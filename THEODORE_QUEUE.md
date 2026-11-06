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

## [x] PR-146 — integration of PRs #142–145

PR #146 (c8bd9142) integrated PRs #142–145 into master. Follow-up PRs #147 and
#148 resolved documentation-wrapper tests that contacted live GitHub. Release
commit is a9395368 (Merge PR #148). CI and deployment for a9395368 succeeded:

- Backend CI Actions 41645358246 — success
- Deploy ancap.cloud Actions 41645358135 — success
- Docs CI 41645358235 — success
- CodeQL 41645358248 — success
- Secret Hygiene 41645358179 — success

Alembic single head is `104_merge_packet_listing` (file
`104_merge_packet_listing_heads.py`). The deploy log proves the production
upgrade `102_cost_evidence_attribution -> 103_packet_templates_rop05`, then
`103_packet_templates_rop05 + 103_robinhood_listing -> 104_merge_packet_listing`.
This integration is **done**.

## [ ] ROP-01 — sources, evidence links and draft packet

Implemented and integrated in a9395368; Backend CI 41645358246 ran the full
`tests/` tree (1384 passed, 47 skipped). Acceptance evidence, including the
test inventory and the deployed migration proof, is recorded in
`docs/ROP01_ACCEPTANCE_2026-11-04.md`.

**Still open** (do not mark done):
- UI acceptance on the deployed build — only local Chromium evidence exists;
  Frontend CI did not run on a9395368 (`frontend-ci.yml` is path-filtered).
- Live customer-source acceptance (permission basis, accuracy, materiality).
- Paid delivery / external payment.

## [ ] ROP-02 — one version-bound reviewed client release

Implemented and integrated in a9395368; the 10 tests in
`tests/api/test_research_packets_api.py` cover exact versions, conflicts,
stale evidence before and after outbox claim, revoked roles, replay and
text-shortening rejection.

**Still open**: explicitly authorized live delivery acceptance against
production. No webhook was sent and no packet was delivered.

## [ ] ROP-03 — bounded recurring collection and quality

Canonical mount and async/admin CRUD fixed in PR #143, integrated via #146
(a9395368). Source quotas `097_source_quotas_rop03_quota_limits` and schedules
`099_source_schedules_rop03_bounded_collection` are in the single-head chain.

**Still open**: bounded recurring-collection acceptance with a paid pilot and
the proposed useful-alert / claim-link / accepted-packet thresholds. These are
pilot targets, not measured results.

## [ ] ROP-04 — actual economics and renewal

Cost-evidence fields and reconciliation are present; COST-03 stays closed.

Renewal tracking API is present (2026-11-06): admin-only `/v1/renewal-events`
with guarded status lifecycle and `/v1/renewal-events/cohort` measurement,
migration `106_renewal_events_rop04`. No real renewal data is recorded yet.

**Still open**: provider/document reconciliation completeness, unknown-expense
recording and due-renewal cohort measurement. Operator/commercial work; do not
report renewals or revenue without evidence.

## [ ] ROP-05 — repeatable onboarding and packet templates

Onboarding templates and packet templates are integrated in a9395368, including
`103_packet_templates_rop05` and the `104_merge_packet_listing` merge.

**Still open**: the proposed 30% onboarding-effort reduction has not been
measured.

There is **no ROP-06** in the pilot roadmap. Onboarding docs labeled ROP-06 are a
Theodore mis-ID of ROP-05 work. Packet templates belong under ROP-05, not a new ID.

## Next step — Theodore, one bounded task (ROP-01 coverage guard)

**ID / criterion**: ROP-01, open box "CI and deployed migration/UI/live-source
acceptance". The migration half is now evidenced; this task prevents silent
loss of that evidence.

**Expected behaviour**: a new offline unit test proves the ROP table migrations
are still in the single-head chain, so a duplicated, renamed or dropped
revision fails CI instead of only failing at deploy time. The duplicate
`093_*` revision created on the stale `fix/p0-release-unblock` branch is the
realistic failure mode.

**Allowed files**: add `tests/unit/test_research_release_contract.py` only.
Do not touch `app/`, migrations, workflows or `docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md`.

**Implementation**: use `alembic.config.Config` + `ScriptDirectory` like
`tests/unit/test_alembic_single_head.py`; assert exactly one head and that
`iterate_revisions(head, "base")` contains at least
`093_research_operations`, `097_source_quotas_rop03_quota_limits`,
`099_source_schedules_rop03_bounded_collection` and
`103_packet_templates_rop05`.

**Verification**: `pytest tests/unit/test_research_release_contract.py
tests/unit/test_alembic_single_head.py -q` (no DB, no network). Report skips.
Negative check: point one assertion at a non-existent revision id in a scratch
copy and confirm the test fails; do not commit that.

**Done when**: test is committed, green locally and in unit CI, and no other
file changed. Do not claim ROP-01 UI/live-source acceptance.

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
