Acceptance 2026-11-05: frontend continuous cycle committed 37494589 and automatically planned/started the next actual task without a new manual ticket. Hermes first draft failed tests, was preserved as stash 693c5a375c24, and a scoped repair is active. 19 Python coordination/continuity regressions passed. Native OpenClaw before_tool_call scope plugin passed delegation/denial checks; work-profile configuration validated. Windows ANCAPParallelAgents task is Running; reboot not performed.

# Continuous development enabled — 2026-11-05

Active contract v5. `continuous.json` enabled=true; after manual tickets, the coordinator automatically plans scoped code tasks and continues after each accepted commit. No finite queue exhaustion. One independent role loop per agent; local model inference is shared.

To pause new cycles create `runtime/STOP`; an already executing bounded task may finish. To resume remove that operator marker and start scheduled task `ANCAPParallelAgents` or Start-ParallelAgents.ps1. For task progress use coordinator_report.py. Logs and journals in runtime/; actual acceptance in status/*-last-result.json. Do not interpret planning, review or recovery as a completed code result.

Normal in-scope failed attempts receive one diagnostic-driven repair with a verified file backup; a second failure is preserved in a named stash, recorded, then another task selected. Unexpected paths/HEAD changes remain quarantined for review. Preserve user edits. No push/merge/deploy. Logon task registration is configured; reboot is not tested.

Verified 2026-11-05: OpenClaw completed flows preview commit d9f667935e55 (Vitest + TypeScript); Hermes completed missing-token regression commit 9dd881eacc47 (4 pytest tests, no DB). First Hermes draft was rejected and preserved in runtime/recovery-20261105; no out-of-role changes accepted. Coordinator now checks ticket required/forbidden content before tests and rejects unchanged artifacts as new development. Nine coordinator regressions passed. Both finite tickets are complete; no autonomous roadmap planner or unlimited development loop is configured.

# 2026-11-05: queue exhaustion

A live coordinator alone does not mean development is progressing. The two recovery notes completed on 2026-11-04 and no further tickets were queued. Actual development tickets now target the operator-only flows preview and RPC header isolation. Idle reports explicitly identify an exhausted queue and the ticket path. Never rerun the same completed ticket ID merely to fabricate activity; add a new bounded task with real acceptance criteria.

# Действующий режим: scoped queue v3 (2026-11-04, 23:15 Берлин)

Запуск: `Start-ParallelAgents.ps1` → `coordinator.py`. Действующий контракт — `CONTRACT.md` v4. Старые описания run_workers/tasks ниже — история, не текущая конфигурация.

Старое дублирующее cron-задание Hermes `457eff6641e6` приостановлено через штатный `hermes cron pause`; его настройки сохранены в recovery-копии. Старое задание разработки OpenClaw уже выключено. Командный отчёт оставлен включённым.

Новые задания: `queue/openclaw.json` и `queue/hermes.json`; новый уникальный task_id и точные sources/allowed_files обязательны. Выполненная очередь переводит роль в idle/готовность. Самостоятельный выбор из старого inbox выключен. Ошибка одной роли создаёт только её quarantine, вторая продолжает работать. Общий runtime/STOP используется только для операторской остановки.

Отчёт: `coordinator_report.py`, вызываемый существующим theodore_status.py. «Готов» без PID модели — нормальное состояние между заданиями. Завершение подтверждают независимые проверки и новый локальный коммит.

Восстановленные задания завершены: frontend `862dae320eca` (Vitest + TypeScript), backend `d6648eebe5e4` (3 pytest без БД). Семь регрессионных тестов нового координатора прошли. В реальном реестре Hermes проверено, что запрещённая запись отклоняется до создания файла.

WIP сохранён в runtime/recovery-20261104-230440/ (хеши файлов в manifest.json) и двух именованных stash; см. CONTRACT.md. Автозапуск после перезагрузки, как и ранее, не подтверждён; это восстановление проверяет текущий работающий координатор и ручной запуск.

---

История предыдущих конфигураций:

# OpenClaw + Hermes на этом ПК

Настроено 2026-11-04. OpenClaw stable 2026.10.10; Hermes установленный v0.14.0.

- OpenClaw: `C:\Users\drago\Desktop\ANCAP-agents\wt-openclaw`, ветка `codex/openclaw-parallel`, профиль `ancap` (`~/.openclaw-ancap`). Сайт, UX, доступность, i18n, публичные AI-страницы.
- Hermes: `C:\Users\drago\Desktop\ANCAP-agents\wt-hermes`, ветка `codex/hermes-parallel`. API, backend-тесты, данные, миграции, mobile, chain, инфраструктура, не-UI документация.
- Общий канал: абсолютный путь `C:\Users\drago\Desktop\ANCAP\agent-bridge`. Inbox — запросы зависимостей; status — результаты и PID. Основная рабочая копия пользователя не используется агентами для разработки.

Оба процесса стартуют одновременно. Инференс сериализован очередью Ollama: лог движка подтверждает, что архитектура qwen35 не поддерживает parallel requests. Проверки и инструменты агентов могут работать параллельно. Один экземпляр супервизора на Windows-сеанс; следующий цикл каждой роли через 60 секунд после собственного завершения. Предел цикла 30 минут, включая медленную загрузку и очередь общей локальной модели. Ошибка одной роли не останавливает другую: повтор через 180 секунд. Только нарушение зоны вызывает общий STOP. Проверка изменённых путей после раунда останавливает следующие циклы при выходе за роль и сохраняет изменения для разбора. Это контроль результата, а не OS-песочница: агенты технически имеют права пользователя. Нельзя обещать абсолютное отсутствие конфликтов.

Одна модель `ancap-qwen:9b`: общие веса Qwen3.5 9B, без дублирования весов на диске; num_ctx=65536, num_thread=6, num_batch=256. Hermes требует минимум 64K; этот размер задан также в Modelfile, чтобы OpenAI-совместимый endpoint действительно использовал его. Ollama: NUM_PARALLEL=1, MAX_LOADED_MODELS=1, FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0, KEEP_ALIVE=30m. Часть весов/контекста может размещаться в RAM: 8 GB VRAM ограничивают полную выгрузку на GPU. Лимиты потоков сборки — 4 на процесс. Пользовательские переменные Ollama сохранены для следующего входа в Windows.

Автозапуск после входа в Windows пока не подтверждён: созданные .lnk/.vbs исчезают из Startup после записи. Текущий запуск супервизора проверен по живым PID; для ручного старта используйте команду ниже. Причина удаления Startup-файлов не установлена; обход системных ограничений не выполнялся.

Запуск: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\drago\Desktop\ANCAP\agent-bridge\Start-ParallelAgents.ps1`.

Остановка после текущего раунда: создать пустой `agent-bridge/runtime/STOP`. Возобновление: удалить именно этот файл и запустить скрипт. Логи: `runtime/openclaw.log`, `runtime/hermes.log`, `runtime/ollama.err.log`. Проверка без изменений: Python из Hermes venv + `run_parallel.py --smoke`. Один рабочий раунд: `--once`.

Старые ANCAP development cron обоих агентов отключены, настройки сохранены в резервных копиях. Внешние сообщения, push, merge и deploy супервизор не выполняет. Ранее существовавший Telegram-отчёт не активируется новым профилем. Интеграция результатов — отдельная проверка выбранных коммитов обеих веток; автоматического слияния нет.

Рабочие копии созданы от текущего HEAD основной папки, без переноса её незакоммиченных изменений. Зависимости фронтенда устанавливаются отдельно в рабочей копии OpenClaw. При несовпадении API/сайта агенты сначала согласуют зависимость через inbox.

Acceptance 2026-11-04: OpenClaw and Hermes both returned their correct roles and isolated directories using the local model. The scope guard caught a misplaced OpenClaw status during smoke; both worktrees now use a junction to the canonical bridge, verified by write/read roundtrip. Worktree-specific excludes keep that shared channel outside agent commits. Duplicate supervisor invocation was rejected by the mutex. Python/PowerShell syntax checks passed. Sustained development quality is evaluated per subsequent task, not implied by this readiness check.

2026-11-04 worker recovery: run_workers.py supervises independent role loops with 5-second heartbeat and cycle-bound test evidence. Empty acknowledgements return diagnostic exit 126. Hermes is restricted to terminal,file toolsets to reduce prompt size and prevent messaging/scheduling tools. First acceptance cycle must execute verify_worker.py through its own tool. OpenClaw runs the existing racpDisplay Vitest test; Hermes runs the existing ACP RPC headers pytest test with --noconftest, without DB fixtures. These acceptance tests prove tool execution, not completed development. Reports use actual supervisor/worker PID and latest verified receipts, not legacy cron or the main checkout commit.

Hermes Windows fixes: hermes_headless.py supplies a plain-text prompt_toolkit session for CREATE_NO_WINDOW. Workers pin HERMES_GIT_BASH_PATH to C:/Program Files/Git/bin/bash.exe so the system32 WSL shim cannot intercept local terminal calls. No installed Hermes source files were patched. The current worker launcher is hidden; the main Gateway remains a separate service/process. Startup persistence is not confirmed (see above).

Recovery acceptance evidence (2026-11-04): OpenClaw invoked its exec tool and passed 2 existing racpDisplay frontend tests; Hermes invoked its terminal tool with pinned Git Bash and passed the existing backend ACP RPC headers test (1 passed, --noconftest, no DB). Receipts are recorded in status/*-evidence.json with distinct cycle IDs and actual command/exit code; log paths are included in each receipt. Both worktrees remained clean during acceptance. Supervisor/report regressions: 9 passed; existing report helper tests: 4 passed. No Telegram messages were sent manually during repair.

Continuation policy: a zero-exit response without the required cycle receipt triggers up to two continuations of the same conversation, within the 30-minute local execution budget. Hermes CLI Session IDs are parsed only from that attempt’s local log segment and resumed explicitly. Native agent.tool_use_enforcement is enabled in the local Hermes config (backup retained). A passing acceptance check does not imply a completed development commit; reports distinguish the last verified check from the live cycle.

2026-11-04 execution repair: fixed a double-absolute-path prompt substitution that had produced invalid paths. Current bootstrap tasks are explicit JSON tickets with exact source context and allowed file lists. A ticket is complete only with a passing cycle receipt AND a new scoped commit; task results are stored separately. OpenClaw verification now runs Vitest plus TypeScript --noEmit. Hermes is limited to 12 turns per invocation; total cycle budget is 30 minutes to account for local inference contention. Current worker PID is reported separately from task completion.
