# WeVisOne-VL 2B local verification — 2026-10-25

PR #119 remains unmerged and undeployed. This record verifies the local Docker
integration, not payment-grade OCR accuracy or funded settlement.

## Environment and reproducibility

Windows 11, Docker Desktop Linux engine 29.8.2, WSL2; NVIDIA RTX 5050 8151 MiB,
Windows driver 617.42. WSL was configured with 8 GB RAM, 4 CPU and 4 GB swap;
those host settings were not changed. The reported host is Xeon E5-2678 v3 / 64 GB.

Tencent SDK commit `9a6bcd85404505df0d05cfb5d97512ccacf35dee`; checkpoint
`tencent/WeVisOne-VL-2B` revision `798ffc7c87ad6104410812b589e240ba32d92315`.
Python 3.12, PyTorch 2.11.0 CUDA 12.8, BF16, SDPA, native `ocr` task,
802816 maximum image processing pixels, 512 output tokens, one inference at a time.
The worker fails if CUDA is unavailable. No CPU or external-provider fallback.

Verified the GPU inside an NVIDIA CUDA Docker container, built all three images,
then ran `scripts/start-wevisone-local.ps1`. Model and API health checks became
healthy before the website started. All published ports bind to loopback.

## Actual image acceptance

Ran:

```powershell
python scripts/smoke_wevisone_local.py --font C:/Windows/Fonts/msyh.ttc
```

The script creates a disposable local user and five synthetic 1800×550 invoices
with Microsoft YaHei 48 px text, a known checksum-valid ACP address and 12.50 ACP.
Requests use the real authenticated Smart Pay image API and real GPU model.
[Sanitized machine-readable results](evidence/wevisone-2b-local-2026-10-25.json).

- EN: exact address/amount/currency passed; 40.55 seconds (first request).
- RU: exact fields passed; 19.02 seconds.
- UK: exact fields passed; 19.56 seconds.
- DE: exact fields passed; 18.72 seconds.
- zh-Hant: amount/currency passed; address characters were misrecognized. ACP
  checksum rejected the address; `address=null`, `can_pay_acp=false`, 18.42 seconds.
- All five responses required manual confirmation. The strict acceptance command
  exits 1 because the Chinese address case did not pass. Do not relabel it green.

Earlier smaller-font and alternative-layout probes also produced address errors.
This is evidence of sensitivity to document layout, not a broad accuracy
benchmark. Invalid ACP OCR addresses are never corrected by guessing. A user must
paste a verified recipient or use the existing deterministic QR path. Arbitrary
invoices, adversarial documents and payment-grade five-language quality still
need a larger acceptance set. Overall GPU use observed around 7.5 GB includes
Windows desktop applications; it is not an isolated model peak measurement.

## Application and regression checks

- Targeted backend tests passed: 85 cases across scanner API, mobile ACP and
  worker contracts (`tests/api/test_payment_scanner.py`,
  `tests/api/test_mobile_acp.py`, `tests/unit/test_payment_wevisone.py`).
- Frontend API-client tests passed (14 cases); production Next.js Docker build
  passed type checking and prerendering.
- Browser login verified after omitting empty optional Turnstile tokens.
- Scanner controls verified in EN/RU/UK/DE/zh-Hant.
- Before manual review, the ACP draft link is absent. Checking review reveals a
  wallet draft containing the expected payee and amount. This does not submit a
  transaction; the wallet retains its separate confirmation.
- No payment execute, signing, broadcast, merge, production config change or
  deployment was performed. The public website still uses its deployed backend.

The real run uncovered and fixed unsupported freeform field completion, XML
closing tags interpreted as URI addresses, language-dependent amount labels,
OCR address checksum errors, and slow regex paths on untrusted text. Source and
regression cases are included in the PR. See its current CI for the final commit.
