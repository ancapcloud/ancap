# ANCAP Theodore Queue — 2026-11-03

## [x] COST-03 — просмотр первичной записи затрат

Verified on branch work for integration into `master`.

Canonical admin-only
`GET /v1/workflow-store/admin/cost-evidence/{evidence_id}` lives in
`app/api/routers/workflow_value.py` and calls `app.services.workflow_costs.get_cost_evidence`.
Response includes source, document_sha256, review_note, allocations with exact amounts,
`verification_basis=operator_attested`, and `Cache-Control: private, no-store`.
Guest 401, ordinary user 403, unknown id 404. GET does not mutate rows and does not
fetch documents over the network. The non-canonical alias
`GET /v1/workflow-store/cost-evidence/{evidence_id}` was removed so only one GET remains.

Do not reopen COST-03. Reconcile/attribute mutations stay under
`/v1/workflow-store/admin/cost-evidence/{id}/…` (COST-04 / COST-05).

## Active next — Research Operations gaps

Queue follows `MASTER_ROADMAP.md` and `docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md`.
Copies under Theodore/ or the OpenClaw workspace are stale.

ROP numbering in the pilot roadmap:

- ROP-01 sources/claims/draft — implemented; CI/live acceptance still open.
- ROP-02 reviewed packet release — implemented; CI/live acceptance still open.
- ROP-03 bounded schedules/fixtures — canonical mount and async/admin CRUD fixed
  in PR #143 and integrated into #146; CI/live acceptance remains separate.
- ROP-04 evidenced economics — cost-evidence fields/reconcile present; commercial
  renewal measurement remains operator work.
- ROP-05 repeatable onboarding + packet templates — onboarding templates are in
  `master`; packet templates are integrated into #146, including the 103 table
  migration and 104 merge of listing/template heads. CI/live and 30% effort
  reduction acceptance remain open.
- There is **no ROP-06** in the pilot roadmap. Onboarding docs labeled ROP-06 are a
  Theodore mis-ID of ROP-05 work. Packet templates belong under ROP-05, not a new ID.

Next engineer step: review and integrate PR #146, then verify live acceptance
for ROP-01/02/03/05. Do not re-implement COST-03 or invent ROP-06/07.
Smart Pay OCR remains archived below.

## Архив OCR — отложено за активными P0

Ниже историческая очередь. Не выполнять в фоновом цикле, пока активный роадмап
или отдельное поручение Андрея не вернёт ей приоритет. Отчёты по языкам уже
есть в Git; не выдавай их за новую проверку или закрытие качества распознавания.

## Smart Pay WeVisOne-VL: Five-language payment-grade recognition quality

### Задача 1: Анализ качества распознавания адресов по языкам (P0)
**Описание:** Протестировать распознавание на реальных образцах для всех 5 языков, выявить проблемы с zh-Hant и другими.
**Файлы:** `docs/mobile/SMART_PAY_WEVISONE_LOCAL_EVIDENCE_2026-10-25.md`, `evidence/wevisone-2b-local-2026-10-25.json`
**Критерий готовности:** Отчёт с результатами тестирования на 10+ образцах каждого языка.
**Проверка:** Сравнить точность распознавания адресов и сумм.

### Задача 2: Подготовка набора тестовых изображений (P1)
**Описание:** Создать набор из 20+ изображений с разными форматами документов для каждого языка.
**Файлы:** `scripts/generate_test_invoices.py` (или аналогичный скрипт)
**Критерий готовности:** Скрипт генерирует тестовые изображения, результаты сохранены в JSON.
**Проверка:** Запустить скрипт и проверить выходной файл.

### Задача 3: Улучшение распознавания zh-Hant (P1)
**Описание:** Исследовать причины ошибок с китайским адресом, попробовать альтернативные подходы.
**Файлы:** Модели WeVisOne-VL, конфигурация OCR
**Критерий готовности:** Точность распознавания адресов zh-Hant ≥ 90% на тестовом наборе.
**Проверка:** Запустить тесты и проверить результаты в JSON.

### Задача 4: Документирование результатов (P2)
**Описание:** Обновить документацию с результатами тестирования и рекомендациями.
**Файлы:** `docs/mobile/SMART_PAY_WEVISONE_LOCAL_EVIDENCE_2026-10-25.md`
**Критерий готовности:** Документация обновлена, отмечены выполненные и оставшиеся задачи.
**Проверка:** Проверить содержимое файла.
