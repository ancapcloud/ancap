# OpenClaw + Hermes на этом ПК

Настроено 2026-11-04. OpenClaw stable 2026.10.10; Hermes установленный v0.14.0.

- OpenClaw: `C:\Users\drago\Desktop\ANCAP-agents\wt-openclaw`, ветка `codex/openclaw-parallel`, профиль `ancap` (`~/.openclaw-ancap`). Сайт, UX, доступность, i18n, публичные AI-страницы.
- Hermes: `C:\Users\drago\Desktop\ANCAP-agents\wt-hermes`, ветка `codex/hermes-parallel`. API, backend-тесты, данные, миграции, mobile, chain, инфраструктура, не-UI документация.
- Общий канал: абсолютный путь `C:\Users\drago\Desktop\ANCAP\agent-bridge`. Inbox — запросы зависимостей; status — результаты и PID. Основная рабочая копия пользователя не используется агентами для разработки.

Оба процесса стартуют одновременно. Инференс сериализован очередью Ollama: лог движка подтверждает, что архитектура qwen35 не поддерживает parallel requests. Проверки и инструменты агентов могут работать параллельно. Один экземпляр супервизора на Windows-сеанс; следующий цикл каждой роли через 60 секунд после собственного завершения. Предел процесса 16 минут. Ошибка одной роли не останавливает другую: повтор через 180 секунд. Только нарушение зоны вызывает общий STOP. Проверка изменённых путей после раунда останавливает следующие циклы при выходе за роль и сохраняет изменения для разбора. Это контроль результата, а не OS-песочница: агенты технически имеют права пользователя. Нельзя обещать абсолютное отсутствие конфликтов.

Одна модель `ancap-qwen:9b`: общие веса Qwen3.5 9B, без дублирования весов на диске; num_ctx=65536, num_thread=6, num_batch=256. Hermes требует минимум 64K; этот размер задан также в Modelfile, чтобы OpenAI-совместимый endpoint действительно использовал его. Ollama: NUM_PARALLEL=1, MAX_LOADED_MODELS=1, FLASH_ATTENTION=1, KV_CACHE_TYPE=q8_0, KEEP_ALIVE=30m. Часть весов/контекста может размещаться в RAM: 8 GB VRAM ограничивают полную выгрузку на GPU. Лимиты потоков сборки — 4 на процесс. Пользовательские переменные Ollama сохранены для следующего входа в Windows.

Автозапуск после входа в Windows пока не подтверждён: созданные .lnk/.vbs исчезают из Startup после записи. Текущий запуск супервизора проверен по живым PID; для ручного старта используйте команду ниже. Причина удаления Startup-файлов не установлена; обход системных ограничений не выполнялся.

Запуск: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File C:\Users\drago\Desktop\ANCAP\agent-bridge\Start-ParallelAgents.ps1`.

Остановка после текущего раунда: создать пустой `agent-bridge/runtime/STOP`. Возобновление: удалить именно этот файл и запустить скрипт. Логи: `runtime/openclaw.log`, `runtime/hermes.log`, `runtime/ollama.err.log`. Проверка без изменений: Python из Hermes venv + `run_parallel.py --smoke`. Один рабочий раунд: `--once`.

Старые ANCAP development cron обоих агентов отключены, настройки сохранены в резервных копиях. Внешние сообщения, push, merge и deploy супервизор не выполняет. Ранее существовавший Telegram-отчёт не активируется новым профилем. Интеграция результатов — отдельная проверка выбранных коммитов обеих веток; автоматического слияния нет.

Рабочие копии созданы от текущего HEAD основной папки, без переноса её незакоммиченных изменений. Зависимости фронтенда устанавливаются отдельно в рабочей копии OpenClaw. При несовпадении API/сайта агенты сначала согласуют зависимость через inbox.

Acceptance 2026-11-04: OpenClaw and Hermes both returned their correct roles and isolated directories using the local model. The scope guard caught a misplaced OpenClaw status during smoke; both worktrees now use a junction to the canonical bridge, verified by write/read roundtrip. Worktree-specific excludes keep that shared channel outside agent commits. Duplicate supervisor invocation was rejected by the mutex. Python/PowerShell syntax checks passed. Sustained development quality is evaluated per subsequent task, not implied by this readiness check.

2026-11-04 worker recovery: run_workers.py supervises independent role loops with 5-second heartbeat and cycle-bound test evidence. Empty acknowledgements return diagnostic exit 126. Hermes is restricted to terminal,file toolsets to reduce prompt size and prevent messaging/scheduling tools. First acceptance cycle must execute verify_worker.py through its own tool. OpenClaw runs the existing racpDisplay Vitest test; Hermes runs the existing ACP RPC headers pytest test with --noconftest, without DB fixtures. These acceptance tests prove tool execution, not completed development. Reports use actual supervisor/worker PID and latest verified receipts, not legacy cron or the main checkout commit.

Hermes Windows fixes: hermes_headless.py supplies a plain-text prompt_toolkit session for CREATE_NO_WINDOW. Workers pin HERMES_GIT_BASH_PATH to C:/Program Files/Git/bin/bash.exe so the system32 WSL shim cannot intercept local terminal calls. No installed Hermes source files were patched. The current worker launcher is hidden; the main Gateway remains a separate service/process. Startup persistence is not confirmed (see above).

Recovery acceptance evidence (2026-11-04): OpenClaw invoked its exec tool and passed 2 existing racpDisplay frontend tests; Hermes invoked its terminal tool with pinned Git Bash and passed the existing backend ACP RPC headers test (1 passed, --noconftest, no DB). Receipts are recorded in status/*-evidence.json with distinct cycle IDs and actual command/exit code; log paths are included in each receipt. Both worktrees remained clean during acceptance. Supervisor/report regressions: 7 passed; existing report helper tests: 4 passed. No Telegram messages were sent manually during repair.

Continuation policy: a zero-exit response without the required cycle receipt triggers up to two continuations of the same conversation, within the original 16-minute budget. Hermes CLI Session IDs are parsed only from that attempt’s local log segment and resumed explicitly. Native agent.tool_use_enforcement is enabled in the local Hermes config (backup retained). A passing acceptance check does not imply a completed development commit; reports distinguish the last verified check from the live cycle.
