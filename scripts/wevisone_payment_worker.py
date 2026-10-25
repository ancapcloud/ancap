"""Run on an isolated inference host, without wallet keys or database access."""
from __future__ import annotations

import hmac
import io
import os
import threading
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from PIL import Image, UnidentifiedImageError
from starlette.concurrency import run_in_threadpool

from app.services.payment_vision_prompt import _VISION_PROMPT

MAX_BYTES = 5_242_880
MAX_PIXELS = 16_000_000
_lock = threading.Lock()


@asynccontextmanager
async def lifespan(app: FastAPI):
    token = os.environ.get("WEVISONE_WORKER_API_KEY", "")
    if len(token) < 32:
        raise RuntimeError("WEVISONE_WORKER_API_KEY must contain at least 32 characters")
    from wevisone_vl import WeVisOneVL

    checkpoint = os.environ.get("WEVISONE_MODEL", "tencent/WeVisOne-VL-2B")
    app.state.token = token
    import torch
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU required; check Docker Desktop WSL2 GPU support")
    app.state.model = WeVisOneVL(
        checkpoint, backend="transformers", device="cuda:0", dtype="bfloat16",
        revision=os.environ.get("WEVISONE_MODEL_REVISION") or None,
        max_pixels=int(os.environ.get("WEVISONE_MAX_PIXELS", "802816")),
        attention_implementation="sdpa",
    )
    yield
    del app.state.model


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


def recognize(data: bytes, model) -> str:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as source:
                if source.format not in {"JPEG", "PNG", "WEBP", "GIF"}:
                    raise ValueError("Unsupported image format")
                if source.width * source.height > MAX_PIXELS:
                    raise ValueError("Image dimensions exceed limit")
                image = source.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError,
            Image.DecompressionBombWarning) as exc:
        raise HTTPException(status_code=422, detail="Invalid or oversized image") from exc
    # Public SDK supports custom freeform prompts; no dense decoder is needed for OCR.
    result = model.predict(image, task="freeform", prompt=_VISION_PROMPT,
                           decode_matting=False, temperature=0, max_new_tokens=int(os.environ.get("WEVISONE_MAX_NEW_TOKENS", "512")))
    text = result.response.strip()
    if len(text) > 32000:
        raise HTTPException(status_code=502, detail="OCR output exceeds limit")
    return "" if text.upper() in {"EMPTY", "NONE"} else text


@app.post("/v1/payment-ocr")
async def payment_ocr(request: Request):
    if not hmac.compare_digest(request.headers.get("authorization", ""), f"Bearer {request.app.state.token}"):
        raise HTTPException(status_code=401, detail="Unauthorized")
    media = request.headers.get("content-type", "").split(";", 1)[0].lower().strip()
    if media not in {"image/jpeg", "image/png", "image/webp", "image/gif"}:
        raise HTTPException(status_code=415, detail="Upload a supported photo")
    if not _lock.acquire(blocking=False):
        raise HTTPException(status_code=503, detail="OCR worker busy; retry later")
    try:
        data = bytearray()
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > MAX_BYTES:
                raise HTTPException(status_code=413, detail="Image exceeds limit")
        if not data:
            raise HTTPException(status_code=422, detail="Empty image")
        text = await run_in_threadpool(recognize, bytes(data), request.app.state.model)
        return {"text": text}
    finally:
        _lock.release()


@app.get("/healthz")
async def healthz():
    return {"status": "ready", "model": "WeVisOne-VL-2B", "device": "cuda:0"}
