# ANCAP Theodore Queue — 2026-11-03

## [~] COST-03 — просмотр первичной записи затрат

Canonical admin GET is verified on PR #142 (`codex/theodore-integrate-20261103`).
Do not re-implement here. Mark `[x]` only after that PR reaches `master`.

## Active — Research Operations gaps

Queue follows `MASTER_ROADMAP.md` and `docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md`.
Copies under Theodore/ or the OpenClaw workspace are stale. Pilot IDs are only
ROP-01 … ROP-05. There is **no ROP-06 / ROP-07**.

- ROP-01 sources/claims/draft — implemented; CI/live acceptance still open.
- ROP-02 reviewed packet release — implemented; CI/live acceptance still open.
- ROP-03 bounded schedules/fixtures — code present; mount/async repair on PR #143.
- ROP-04 evidenced economics — cost-evidence fields/reconcile present; commercial
  renewal measurement remains operator work.
- ROP-05 onboarding templates — already on `master`. Packet templates admin API +
  migration `103_packet_templates_rop05` land in this branch (behavior from
  Theodore `8a42905f`/`b1440775`, retargeted under ROP-05, async/admin-auth fixed).
  Do not merge packet templates with onboarding templates. Effort-reduction
  validation (30%) remains open.

Next engineer step after merge: CI/live acceptance for ROP-01/02 and source-schedules
fix; do not invent new ROP IDs. Smart Pay OCR remains archived below.
Run `scripts/theodore_queue_guard.py` when present before rewriting a receipt.

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
