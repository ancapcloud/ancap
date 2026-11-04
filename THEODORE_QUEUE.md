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

## [x] PR #146 integration — 2026-11-03

PR #146 (c8bd9142) integrated PRs #142–145 into master. Follow-up PRs #147 and
#148 resolved documentation-wrapper tests that contacted live GitHub. Origin/master
HEAD is now a9395368 (Merge PR #148). CI and deployment for a9395368 succeeded:

- Backend CI Actions 41645358246 — success
- Deploy ancap.cloud Actions 41645358135 — success
- Docs CI 41645358235 — success
- CodeQL 41645358248 — success
- Secret Hygiene 41645358179 — success

Alembic through 104_merge_packet_listing_heads. This integration is **done**.

## Active next — ROP-01 CI/deployed acceptance

Queue follows `MASTER_ROADMAP.md` and `docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md`.
Copies under Theodore/ or the OpenClaw workspace are stale.

ROP numbering in the pilot roadmap:

- ROP-01 sources/claims/draft — implemented and integrated (a9395368); CI passed.
  **Open criterion**: record the specific green test runs on a9395368 and which
  evidence file/checklist confirms deployed migration/UI/live-source acceptance.
- ROP-02 reviewed packet release — implemented and integrated (a9395368); CI passed.
  Deployed acceptance checklist remains open.
- ROP-03 bounded schedules/fixtures — canonical mount and async/admin CRUD fixed
  in PR #143, integrated via #146 (a9395368); CI passed. Live acceptance separate.
- ROP-04 evidenced economics — cost-evidence fields/reconcile present; commercial
  renewal measurement remains operator work.
- ROP-05 repeatable onboarding + packet templates — onboarding templates integrated
  (a9395368) including the 103 table migration and 104 merge of listing/template
  heads. CI passed. 30% effort reduction acceptance remains open.
- There is **no ROP-06** in the pilot roadmap. Onboarding docs labeled ROP-06 are a
  Theodore mis-ID of ROP-05 work. Packet templates belong under ROP-05, not a new ID.

**Next engineer/Theodore step**: close ROP-01 CI/deployed acceptance on a9395368
by documenting which backend tests cover migration 093/sources/claims/draft
(already green on Actions 41645358246) and confirming the deployed migration
runs on ancap.cloud. Record this in an evidence file or the ROP-01 checklist.
Do not claim live customer-source quality or paid delivery.

Do not re-implement COST-03 or invent ROP-06/07.
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
