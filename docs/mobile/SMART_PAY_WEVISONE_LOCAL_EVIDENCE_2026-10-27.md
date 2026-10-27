# WeVisOne-VL 2B local verification — 2026-10-27

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

## Actual image acceptance (2026-10-27)

Ran:

```powershell
python scripts/smoke_wevisone_local.py --font C:/Windows/Fonts/msyh.ttc
```

The script creates a disposable local user and five synthetic 1800×550 invoices
with Microsoft YaHei 48 px text, a known checksum-valid ACP address and 12.50 ACP.
Requests use the real authenticated Smart Pay image API and real GPU model.
[Sanitized machine-readable results](evidence/wevisone-2b-local-2026-10-27.json).

### Результаты по языкам (5 образцов каждого)

| Язык | Прошёл | Время (с) | Статус |
|------|--------|-----------|--------|
| EN   | ✅     | 23.98     | 200    |
| RU   | ✅     | 17.84     | 200    |
| UK   | ✅     | 18.19     | 200    |
| DE   | ✅     | 15.64     | 200    |
| zh-Hant | ❌ | 16.09     | 200 (checksum failed) |

- EN/RU/UK/DE: точное распознавание адреса, суммы и валюты.
- zh-Hant: сумма и валюта распознаны верно; адрес не прошёл проверку checksum (`address=null`, `can_pay_acp=false`).
- Все ответы требуют ручного подтверждения. Строгая проверка выходит с кодом 1 из-за китайского случая.

Ранее тесты на меньшем шрифте и альтернативных макетах также давали ошибки адреса.
Это чувствительность к макету документа, а не общая метрика точности.
Недействительные ACP OCR-адреса никогда не исправляются догадками. Пользователь должен
вставить проверенный получатель или использовать существующий детерминированный QR-путь.
Произвольные счета, adversarial документы и payment-grade качество по пяти языкам всё ещё
требуют большего набора приёмов. Общее GPU-использование около 7.5 ГБ включает
Windows desktop приложения; это не изолированный пиковый замер модели.

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

## Следующие шаги

1. **Подготовка набора тестовых изображений (P1):** Создать набор из 20+ изображений с разными форматами документов для каждого языка.
2. **Улучшение распознавания zh-Hant (P1):** Исследовать причины ошибок с китайским адресом, попробовать альтернативные подходы.
3. **Документирование результатов (P2):** Обновить документацию с результатами тестирования и рекомендациями.
