# Smart Pay: optional WeVisOne-VL photo recognition

Implemented on a review branch, not activated in production. The default
Anthropic provider remains unchanged. No UI strings or language routes change;
EN/RU/UK/DE/zh-Hant use the existing document upload and payment review UI.

WeVisOne-VL is a Tencent visual model with OCR and a documented Python
`predict` API, not a hosted payment API. ANCAP provides its own private worker
using the supported freeform prompt to extract payment fields. Accuracy on
ANCAP invoices still requires a real checkpoint evaluation.

Sources: https://tencent.github.io/WeVisOne-VL/ and
https://github.com/Tencent/WeVisOne-VL (SDK `wevisone_vl/engine.py`).
Check upstream code, checkpoint and third-party licenses before deployment.

## Isolated inference host

Install the reviewed Tencent repository and its dependencies in a separate
environment per upstream README; pin the reviewed upstream commit and model
revision in your deployment record. Add FastAPI, uvicorn, httpx and
pydantic-settings to that environment. Copy the ANCAP source containing this
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
separately. Neither real GPU inference nor production activation is claimed.
