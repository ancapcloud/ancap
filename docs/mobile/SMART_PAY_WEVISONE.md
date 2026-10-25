# Smart Pay: optional WeVisOne-VL photo recognition

Implemented on a review branch, not activated in production. The default
Anthropic provider remains unchanged. No UI strings or language routes change;
EN/RU/UK/DE/zh-Hant use the existing document upload and payment review UI.

WeVisOne-VL is a Tencent visual model with OCR and a documented Python
`predict` API, not a hosted payment API. ANCAP provides its own private worker
using its native OCR task, stripping bounding-box markup and parsing recognized
text deterministically. Accuracy on
ANCAP invoices still requires a real checkpoint evaluation.

Sources: https://tencent.github.io/WeVisOne-VL/ and
https://github.com/Tencent/WeVisOne-VL (SDK `wevisone_vl/engine.py`).
Check upstream code, checkpoint and third-party licenses before deployment.

## Isolated inference host

Install the reviewed Tencent repository and its dependencies in a separate
environment per upstream README; pin the reviewed upstream commit and model
revision in your deployment record. Add FastAPI and uvicorn to that environment. Copy the ANCAP source containing this
worker; do not copy `.env`, wallet/bridge credentials or database credentials.
Pre-download the 2B or 4B weights to a local immutable checkpoint directory and
set `WEVISONE_MODEL` to that directory. No model weights load in the payment API.

Set `WEVISONE_WORKER_API_KEY` to a new random secret with at least 32 characters.
From the ANCAP checkout on the inference host:

```sh
python -m uvicorn scripts.wevisone_payment_worker:app --host 127.0.0.1 --port 8097 --workers 1 --no-access-log
```

For a separate API host, expose this worker through a private HTTPS reverse
proxy, restrict ingress to the API host, and enforce 5 MiB request and 60-second
request limits. Do not use the public Hugging Face demo for customer documents.
The worker accepts raw JPEG/PNG/WebP/GIF at `POST /v1/payment-ocr`, requires a
Bearer token, bounds decoded pixels and serializes inference without a queue.
It does not persist documents or log their bodies. Monitor capacity before use.

Configure the payment API environment:

```dotenv
SMART_PAY_VISION_PROVIDER=wevisone
SMART_PAY_WEVISONE_URL=https://private-inference.example
SMART_PAY_WEVISONE_API_KEY=<same new worker secret>
```

HTTP URLs are accepted only for loopback. Redirects are rejected. An unavailable
worker fails explicitly; documents are never silently sent to another provider.
Set `SMART_PAY_VISION_PROVIDER=anthropic` to restore the existing provider.
No new dependencies belong in the main API image.

## Payment behavior and acceptance

Output enters the existing deterministic payment-text parser with source `ocr`,
its ambiguity checks and confidence cap. The worker cannot sign, broadcast,
settle or confirm a payment. User review remains required, and OCR is not proof
of settlement. QR decoding remains the existing deterministic flow; this model
is not a QR decoder. PDF is explicitly rejected while WeVisOne is selected:
export the payment page as a photo. DOCX and text imports remain deterministic.

Unit checks cover routing, malformed responses, limits, provider failure,
authorization and invalid images using fake inference. Before activation, run
real-checkpoint tests on sample invoices in all five languages, missing and
ambiguous amounts/payees, manipulated documents, provider outages, latency and
GPU memory. Verify existing API manual confirmation and one funded payment
separately. Local GPU inference is recorded in the evidence below; production activation
is not claimed.

## Windows 11 / WSL2 / RTX 5050 8 GB: local Docker launch

Use Docker Desktop with Linux containers, the WSL2 engine and a current NVIDIA
Windows driver. Do not install a Linux display driver inside WSL. Verify GPU
forwarding first:

```powershell
docker run --rm --gpus all nvidia/cuda:12.8.1-base-ubuntu24.04 nvidia-smi
.\scripts\start-wevisone-local.ps1
```

Run from this PR checkout. The script creates a random local credential in the
ignored `.env.wevisone`; it never reads production `.env`. First build downloads
CUDA/PyTorch and first worker startup downloads the pinned Tencent 2B checkpoint
into a named Docker volume. HTTP streaming downloads avoid the Xet parallel
transfer path on memory-constrained WSL setups. Allow several GB of downloads and at least 25 GB of
free disk. A cold start can take several minutes; readiness waits for model load.

Open http://localhost:3001/payment-scanner and create a **local test account**.
Upload a PNG/JPEG invoice, inspect amount/address/currency, select the review
checkbox, and only then open the ACP payment draft. The wallet has its own final
confirmation. Recognition does not send a payment. Never fund the development
wallet: the local API image intentionally omits the production wallet helper.
EN/RU/UK/DE/zh-Hant UI language selection remains available.

The local path is browser → API `localhost:8001/v1/payment-scanner/parse-image`
→ authenticated worker `wevisone:8097` → deterministic parser → manual review.
Worker credentials stay on the backend. All published ports bind to 127.0.0.1;
Postgres/Redis are internal and contain only disposable local data. The worker
receives no database URL, wallet keys or source `.env`. This Compose file is
standalone; do not combine it with the production Compose file.

This uses PyTorch 2.11.0 CUDA 12.8 (Blackwell support), BF16, SDPA, serialized
inference, 802816 maximum processing pixels and 512 output tokens. SDK commit:
`9a6bcd85404505df0d05cfb5d97512ccacf35dee`; model revision:
`798ffc7c87ad6104410812b589e240ba32d92315`. Weights are not baked into images.
Close GPU-heavy applications if available VRAM is too low; do not switch silently
to CPU or a different provider. The model's published benchmarks are not proof of
five-language payment accuracy. Keep the manual review step.

```powershell
# Readiness and logs
Invoke-RestMethod http://localhost:8097/healthz
docker compose --env-file .env.wevisone -f docker-compose.wevisone.yml logs --tail 100 wevisone api
# Stop without deleting model cache or local test accounts
docker compose --env-file .env.wevisone -f docker-compose.wevisone.yml down
# Model only, when running the API on the Windows host
.\scripts\start-wevisone-local.ps1 -WorkerOnly
```

For a host-run API, set `SMART_PAY_VISION_PROVIDER=wevisone`,
`SMART_PAY_WEVISONE_URL=http://127.0.0.1:8097` and use the same secret from
`.env.wevisone`. For the supplied local Docker API the exact internal HTTP
endpoint is enabled explicitly through `SMART_PAY_WEVISONE_ALLOW_LOCAL_HTTP=true`
and `ENVIRONMENT=development`; production still requires private HTTPS.

### Repeatable real-model acceptance

Install Pillow and httpx in your test Python environment. Use a Unicode font
covering Cyrillic and Traditional Chinese (for example Noto Sans CJK). The script
creates five synthetic invoice images and a disposable local user, submits the
images through the real Smart Pay API, asserts amount/address/currency plus
`requires_manual_confirm=true`, and writes sanitized JSON results. It never
calls payment execution or contacts a production API by default.

```powershell
python scripts/smoke_wevisone_local.py --font C:/Windows/Fonts/msyh.ttc
```

Review generated images for missing glyphs before accepting language results.
Artifacts are in ignored `.wevisone-smoke/`. The public ancap.cloud site continues
to use its currently deployed backend. Connecting that production backend to this
computer requires an approved private HTTPS network path and production config
change; this local setup does not expose the GPU worker publicly or deploy the PR.

## Local verification result

Real RTX 5050 inference and browser/API wiring were tested on 2026-10-25.
Four of five synthetic invoice cases pass exact address/amount/currency checks.
The zh-Hant case misrecognizes the address, which is rejected by checksum;
manual verified-address entry is required. The strict smoke command exits 1 for
this remaining quality failure. Do not use OCR as settlement evidence or a
reliable replacement for copying/decoding a payment address. All five UI languages
and manual review remain available. Details and timings:
[local evidence](SMART_PAY_WEVISONE_LOCAL_EVIDENCE_2026-10-25.md).
