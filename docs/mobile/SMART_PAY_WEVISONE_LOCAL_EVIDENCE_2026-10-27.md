# WeVisOne-VL 2B local verification — 2026-10-27

## Summary

Five-language payment-grade recognition quality verified on synthetic samples using WeVisOne-VL 2B. Four of five languages passed acceptance; zh-Hant requires optimization.

**Status:** P0 task completed, P1 test set generated (25 images), P2 documentation updated.

## New Test Set (P1)

Generated 25 invoice images with varied amounts and layouts:
- EN: 5 samples (invoice_en_0001.png - invoice_en_0005.png)
- RU: 5 samples (invoice_ru_0001.png - invoice_ru_0005.png)
- UK: 5 samples (invoice_uk_0001.png - invoice_uk_0005.png)
- DE: 5 samples (invoice_de_0001.png - invoice_de_0005.png)
- zh-Hant: 5 samples (invoice_zh-Hant_0001.png - invoice_zh-Hant_0005.png)

Results saved to: `evidence/wevisone-test-invoices.json`

**Note:** All images use the same base layout with different amounts. Additional format variations (different layouts, fonts, orientations) should be generated for comprehensive testing.

## Environment and reproducibility

Windows 11, Docker Desktop Linux engine 29.8.2, WSL2; NVIDIA RTX 5050 8151 MiB,
Windows driver 617.42. Python 3.12, PyTorch 2.11.0 CUDA 12.8, BF16, SDPA, native `ocr` task,
802816 maximum image processing pixels, 512 output tokens, one inference at a time.

Verified the GPU inside an NVIDIA CUDA Docker container. Model and API health checks became healthy.

## Actual image acceptance

Ran:

```powershell
python scripts/smoke_wevisone_local.py --font C:/Windows/Fonts/msyh.ttc
```

The script creates five synthetic 1800×550 invoices with Microsoft YaHei 48 px text, a known checksum-valid ACP address and 12.50 ACP. Requests use the real authenticated Smart Pay image API and real GPU model.

**Results:**

| Language | Status | Time | Notes |
|----------|--------|------|-------|
| EN | ✅ passed | 20.66s | address/amount/currency recognized correctly |
| RU | ✅ passed | 17.42s | all fields exact |
| UK | ✅ passed | 17.98s | all fields exact |
| DE | ✅ passed | 16.22s | all fields exact |
| zh-Hant | ❌ failed | 16.0s | address=null, checksum rejected (address not recognized) |

**Conclusion:** Model works on 4 of 5 languages. Chinese (zh-Hant) requires separate optimization — likely a font or data preparation issue for traditional Chinese.

## Application and regression checks

- Targeted backend tests passed: scanner API, mobile ACP and worker contracts.
- Frontend API-client tests passed; production Next.js Docker build passed type checking and prerendering.
- Browser login verified after omitting empty optional Turnstile tokens.
- Scanner controls verified in EN/RU/UK/DE/zh-Hant.

**Limitations:** All five responses required manual confirmation. The strict acceptance command exits 1 because the Chinese address case did not pass. Do not relabel it green.

## Recommendations for zh-Hant optimization

1. **Font substitution:** Try alternative fonts with better Traditional Chinese support (e.g., `msyh.ttc` vs `SimSun`, or system-installed `NotoSansTC`).
2. **Data preparation:** Verify that the model training data includes sufficient Traditional Chinese samples.
3. **Layout sensitivity:** Earlier smaller-font and alternative-layout probes also produced address errors — this indicates sensitivity to document layout, not just character recognition.
4. **Fallback path:** Invalid ACP OCR addresses are never corrected by guessing. Users must paste a verified recipient or use the existing deterministic QR path.

## Next steps (P1 → P2)

- ✅ P1: Generated expanded test set of 25 images with varied amounts.
- 🔄 P2: Investigate zh-Hant failure root cause and implement fixes.
- ⏳ Re-run acceptance tests after optimization.

**Current status:** zh-Hant still fails address recognition (address=null, checksum rejected). Need to investigate font/data/layout causes before proceeding.

## Evidence files

- `docs/mobile/SMART_PAY_WEVISONE_LOCAL_EVIDENCE_2026-10-27.md` — this report
- `evidence/wevisone-2b-local-2026-10-25.json` — sanitized machine-readable results (from prior run)
