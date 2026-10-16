from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import require_auth
from app.schemas.payment_scanner import PaymentScannerParseRequest, PaymentScannerPreview
from app.services.payment_image_parse import parse_payment_image
from app.services.payment_text_parse import parse_payment_text

router = APIRouter(prefix="/payment-scanner", tags=["Payment Scanner"])


def _to_preview(parsed) -> PaymentScannerPreview:
    return PaymentScannerPreview(
        detected_network=parsed.detected_network,
        address=parsed.address,
        amount=parsed.amount,
        currency=parsed.currency,
        label=parsed.label,
        confidence=parsed.confidence,
        requires_manual_confirm=True,
        parse_notes=parsed.parse_notes,
    )


@router.post("/parse", response_model=PaymentScannerPreview)
async def parse_payment_request(
    body: PaymentScannerParseRequest,
    _user_id: str = Depends(require_auth),
):
    parsed = parse_payment_text(body.raw_text, source=body.source)
    return _to_preview(parsed)


@router.post("/parse-image", response_model=PaymentScannerPreview)
async def parse_payment_image_request(
    file: UploadFile = File(...),
    _user_id: str = Depends(require_auth),
):
    image_bytes = await file.read()
    try:
        parsed = await parse_payment_image(image_bytes=image_bytes, content_type=file.content_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return _to_preview(parsed)
