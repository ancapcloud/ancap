# 2026-11-07: inference contention and test-adapter repair

Gateway and model were healthy, but OpenClaw retried timeouts while both roles and their planner/reviewer competed for one Qwen35 runner. Hermes was attempting tests/api/test_wallet_auth.py with --noconftest: four missing-client fixture errors could not be repaired by changing wallet logic.

inference_lane.py now admits managed planner, actor and reviewer phases FIFO. A waiting role publishes waiting-model heartbeats; its execution deadline has not started. The actor holds the lane across its file-tool conversation, preserving prompt-cache locality. Project checks and commits run after releasing the lane, so they can overlap the other agent's model work. This lane coordinates the supervisor's two roles; manual Gateway chats still use Ollama's server queue. It does not claim simultaneous inference on the single GPU.

Automatic backend selection now parses fixture requirements, local fixture dependencies, parametrization and usefixtures/autouse markers; API suites are not eligible for the standalone adapter. Integration/DB work needs an appropriate checker rather than silently bypassing conftest or editing business rules to satisfy broken infrastructure. The same preflight runs again before pytest to catch incompatible newly generated tests.

Normal STOP cancels a queued model phase without quarantine or leaking the lane. Interrupted owned work retains the existing backup/stash safeguards. Previous jobs drained normally under a temporary maintenance STOP; both isolated worktrees were clean, accepted commits retained, and state snapshots saved under runtime/queue-repair-20261107-124645/. No user edits were discarded.

Validation: 30 targeted tests (9 coordinator, 13 continuity, 4 lane, 4 fixture selection) passed. Two actual model JSON requests completed start/end/start/end without overlap; receipt runtime/lane-probe-result.json explicitly identifies a read-only probe, not code completion. Current eligible scopes: 286 frontend units, 15 backend units with standalone checks. Live restart verified: Gateway ready=true; ANCAPParallelAgents Running; Hermes planning and OpenClaw waiting-model with fresh heartbeat; STOP absent. These are scheduling states, not a new feature completion.

# 2026-11-07: DeepSeek/Qwen Q4_K_M runtime

Active model: `ancap-deepseek-qwen:9b-q4km`, from `hf.co/mradermacher/DeepSeek-V4-Pro-Qwen3.5-9B-UNCENSORED-heretic-GGUF:Q4_K_M`; text weights + bundled projector downloaded and SHA256-verified by Ollama. Old models remain installed for rollback. Native model_probe.py passed JSON, native function calling and OpenAI-compatible function calling. Gateway returned READY with actual new-model metadata; main chat reset to the configured new default without clearing history.

Both OpenClaw profiles, Hermes config and planner use the new explicit model and 65536 context (Hermes requires >=64000). Hermes command line pins the configured model. No silent fallback to an old model if configuration is missing. Sample resident model used about 5.9 GB VRAM plus RAM; local inference remains serialized.

Missing worktrees were recreated from their preserved branches. ensure_workspaces.py restores missing registered worktrees, backs up their metadata, recreates the shared bridge junction and per-worktree exclusions, and installs isolated frontend dependencies if missing. Startup fails safely for an existing different branch/root. Main user edits/index are preserved.

Quality corrections: planner must quote exact actual production-source evidence; no financial identifier banners, automatic legal-page changes or formatting/comment churn. Python test definitions are compared by lexical scope and duplicate names rejected before pytest. Native OpenClaw read requests return full small files instead of repeated five-line pagination; no-op edits are rejected with actionable feedback. Short JSON-safe prefix edits were verified for JSX.

Acceptance: OpenClaw 58a91797 (feedback live regions; Vitest + tsc), Hermes ed290871 (Accept header), controller bbd96d47 (removed three shadowing duplicate definitions; all six distinct tests passed). The initial green pytest result had missed shadowing; it is not represented as fully autonomous clean code. Controller provenance is recorded in last-result and the report. 23 coordination/continuity/workspace regressions and native hook checks passed.

The main Gateway's Windows in-process restart stalled. A fresh start through the existing hidden launcher recovered it; root state quick_check was healthy and agent DB admission completed. Do not run two Gateways or edit ownership locks manually. Main-chat model reset result is in runtime/main-session-use-new-default.json; model proof in runtime/gateway-final-model-check.json. No manual Telegram messages, push, merge or deploy were performed.

Backups: runtime/migration-backup-path.txt names the private migration backup; failed drafts and old in-flight state were retained. The older untracked safetensors-conversion installer was not used. Configuration and acceptance details here supersede earlier model/runtime notes below.

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
# 2026-11-09: commit audit and regression proof

See docs/AGENT_INTEGRATION_2026-11-09.md for rejected changes and verification.
Before ordinary green checks, planned tasks prove a new assertion fails on an
isolated baseline whose original tests pass. Related tests are required at task
selection. Exported baseline contains tracked source only, never local secrets.
The new Agent Bridge CI exercises coordination, preservation and scope guards on
Windows. Production publishing/deployment remains outside the agent roles.

