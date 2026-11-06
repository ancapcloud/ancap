# Continuous development contract v5 — 2026-11-05

User authorization: OpenClaw and Hermes must continuously write useful ANCAP code. This explicitly replaces the old operator-only queue restriction below.

`continuous.json` enables the loop. Explicit queue tickets retain priority. When they finish, each role independently selects a small unit from current tracked code, reads canonical roadmap/current token policy and its recent outcome journal, asks the local model for one bounded task, executes it in its own worktree, verifies and commits locally, then selects another task. There is no fixed finite queue to exhaust. No-action units are scanned onward; planner/provider errors back off and retry. No fake changes or repetitive commits are required to show activity.

OpenClaw owns frontend source only. Hermes initially selects backend services that have standalone test files; mobile/chain/DB work requires appropriate check adapters before being admitted automatically. Roles never edit the main checkout, agent-bridge control files or each other's paths. The planner has no tools and cannot select shell commands or arbitrary output paths. File scopes remain fixed by the coordinator. Dedicated ancap-profile plugin ancap-scope enforces the exact source/output allowlist in before_tool_call; Hermes uses its registry guard. Unexpected paths are denied before writes in both managed profiles. Existing token ratios and permissions must remain intact.

Acceptance: real production-code diff, unchanged existing Python tests, no unsafe operations in standalone generated tests, task constraints, independent model review for newly planned tickets, then task-specific pytest or frontend Vitest + TypeScript. A model review is a quality gate, not a correctness guarantee. All commits remain local and require normal review/CI before integration or deployment.

Normal task failures receive at most one bounded repair with the actual diagnostic; partial edits are backed up first. After an unsuccessful repair, exact task-owned edits are preserved with a named Git stash and journaled. If HEAD is unchanged and there are no unexpected paths, that role is released to select another task. Out-of-scope/external changes stay quarantined; the other role continues. General STOP remains operator-controlled. A crash cannot start a duplicate writer beside the previous tracked live child.

History: runtime/<role>-history.jsonl. Current generated ticket: runtime/<role>-current-task.json. Planner cursor: status/<role>-planner.json. Manual completed tickets are kept separately and cannot be requeued by automatic results. Cooldown is 30 seconds. Shared local Ollama inference remains serialized for this GPU; file/check work is independent.

Windows Task Scheduler entry `ANCAPParallelAgents` uses current-user interactive logon, no execution time limit and ignores duplicate instances. The launcher retries coordinator crashes. STOP prevents launch. Reboot itself is not performed as part of setup.

---
Historical v4 contract (superseded where it requires operator-only queues):

# Контракт OpenClaw и Hermes — v4, 2026-11-04

Источник действующего запуска: `coordinator.py` и `Start-ParallelAgents.ps1`. `run_parallel.py` — совместимый вход в новый координатор. `run_workers.py` и `tasks/` сохранены как исторический код, для запуска не используются.

## Роли и рабочие копии

- OpenClaw: ветка `codex/openclaw-parallel`, `C:/Users/drago/Desktop/ANCAP-agents/wt-openclaw`. Файловый корень его инструментов — только `frontend-app/`. Только файловые инструменты; shell, process, web и messaging отключены в рабочем профиле `ancap`.
- Hermes: ветка `codex/hermes-parallel`, `C:/Users/drago/Desktop/ANCAP-agents/wt-hermes`. Backend, данные, chain, mobile, инфраструктура и не-UI документация. Для каждого задания файловый guard разрешает только перечисленные источники и выходные файлы; остальные вызовы отклоняются до записи. Ограничение добавляется в отдельном процессе, установленный Hermes не изменяется.
- Основная папка ANCAP остаётся рабочей копией пользователя. Агенты не выполняют push, deploy, merge, rebase, reset или clean.

## Очередь вместо свободного выбора задач

Разрешённые задания задаются оператором в `queue/openclaw.json` и `queue/hermes.json`. Обязательны новый уникальный task_id, enabled=true, sources, allowed_files, instructions, commit_message. Пути относительные, без .., абсолютных адресов, .env, Sicret или файлов ключей. Проверяются также канонические пути, чтобы ссылки не обходили роли.

Завершённый task_id повторно не запускается. Пустая или выполненная очередь означает «готов, ожидает задание», а не поломку. Старые inbox и roadmap не превращаются автоматически в команды. Предложения другому агенту сначала оформляются как ограниченное задание оператором; сами агенты не редактируют очередь и контрольные файлы.

## Проверки и остановки

Координатор публикует heartbeat каждые 5 секунд. До запуска требуется чистая рабочая копия. Во время работы он контролирует изменённые пути. Scope violation, timeout, отсутствие результата или неуспешные проверки блокируют только соответствующую роль через `status/<role>-quarantine.json`. Вторая роль продолжает работу. Никаких бесконечных повторов одного проваленного задания.

`runtime/STOP` — только общая операторская остановка новых заданий. Автоматические ошибки больше не создают общий STOP. Разблокировка роли выполняется после сохранения/разбора её изменений и исправления задания, а не удалением всех файлов состояния.

Результат принимается после появления разрешённых выходных файлов, независимых проверок и локального scoped-коммита. Frontend: существующий racpDisplay Vitest и TypeScript --noEmit; backend: ACP RPC headers pytest --noconftest без БД. Для других видов задач оператор должен настроить соответствующие проверки, до публикации требуется обычный review/CI. Это ограничение инструментов контролируемых профилей, не OS-песочница для любых других запущенных приложений.

## Ресурсы и отчёт

Один локальный Ollama, общая `ancap-qwen:9b`, 64K контекст, одна очередь инференса. Рабочие циклы независимы; после очереди не расходуют GPU на бессодержательные повторы.

Существующий командный отчёт читает `coordinator_report.py`: живой координатор, актуальный heartbeat, состояние задачи и последняя реальная проверка. Даты отображаются по Берлину. Координатор не отправляет внешние сообщения и не меняет получателей ранее настроенной доставки. Главный Gateway и пользовательские интерактивные сессии — отдельные процессы.

## Восстановление 2026-11-04

Незавершённые изменения двух рабочих копий сохранены в проверенной копии `runtime/recovery-20261104-230440/` и Git stash: OpenClaw `150ba7855b2f`, Hermes `e427b4563460`. Основной индекс пользователя проверен и сохранён. Общий STOP старого движка перемещён в ту же копию, история ошибки не удалена.

Новые приёмочные задания реально выполнены файловыми инструментами: OpenClaw `862dae320eca`, Hermes `d6648eebe5e4`; независимые проверки прошли. После них обе роли переходят в готовность, ожидая новых ограниченных заданий.

Старый cron разработки OpenClaw выключен, старый cron полной разработки Hermes `457eff6641e6` приостановлен штатной командой. Это исключает второй автоматический контур вне координатора; интерактивные пользовательские сессии не изменялись.
