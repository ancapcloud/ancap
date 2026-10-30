> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

---
name: ANCAP device-ready wallet and product reliability
overview: Завершить существующий vault/FFI, доказать external restore и local sign на Android, пройти physical и store gates; затем улучшать paid-run и автоматизацию депозитов. Сохранять независимость wallet, bridge, consensus и sACP.
todos:
  - id: baseline-scope
    content: Зафиксировать HEAD, dirty paths и проверяемую исходную точку; составить allowlist wallet/FFI
    status: completed
  - id: vault-integrity
    content: Проверить и завершить byte-safe chunking, crash consistency, migration, wipe и конкурентные операции
    status: completed
  - id: external-recovery
    content: Завершить безопасный encrypted keystore export/import и external restore без mnemonic
    status: in_progress
  - id: android-evidence
    content: Pixel_10_Pro — create, export, fresh-state restore, restart, send и independent local-sign verification
    status: in_progress
  - id: android-store-compatibility
    content: Проверенная миграция Expo/RN/toolchain на target API 36+, release signing и 16 KB full-artifact evidence
    status: pending
  - id: physical-release
    content: Physical PIN/biometrics/MASVS; Android release candidate и Play Internal; отдельная macOS/iOS/TestFlight ветка
    status: pending
  - id: side-tracks
    content: Изолированные fee-recycle, CodeQL/dependencies и capacity/recovery ops по evidence
    status: pending
  - id: product-reliability
    content: После mobile gates — paid-run reliability, conversion baseline, deposit watcher, затем Smart Pay broadcast
    status: pending
isProject: false
---

# ANCAP: исполнимый план для Cursor

Дата: 17 октября 2026. Обновлён после инженерного аудита четырёх исходных коммитов. Проверки, исправления и ограничения записаны в docs/mobile/ENGINEERING_AUDIT_2026-10-17.md; этот отчёт имеет приоритет над описанием исходного состояния ниже. Production и store release не проверены. Зашифрованный recovery через host transport прошёл, native local-sign fixture с синтетическими UTXO прошёл; системный picker/SAF, funded emulator и physical evidence остаются открыты.

Следующий отдельный инженерный этап перед Play: инвентаризация Expo/RN/native зависимостей и совместимого toolchain, выбор поддерживаемого стека с API 36+, последовательная миграция с regeneration/bindings diff, повтор unit/typecheck/native recovery/sign и проверка release AAB на 16 KB. Текущая APK target API 34. Не закрывать этап одним изменением targetSdk. Release должен пройти :app:verifyReleaseSigning с operator upload key; секреты не сохранять в git. Критерии и официальные ссылки — docs/mobile/RELEASE_CHECKLIST.md.

## Цель и порядок

Главный результат — пользователь может создать кошелёк, самостоятельно сохранить зашифрованную резервную копию, восстановить тот же адрес в чистом состоянии приложения и локально подписать корректную транзакцию. Далее — проверка защиты на физическом устройстве и воспроизводимый внутренний store release.

Порядок: baseline → vault integrity → external recovery → Android evidence → physical Android/release candidate → Play Internal. iOS native/physical/TestFlight выполнять отдельной веткой на macOS после стабилизации общего формата keystore; iOS не должен искусственно блокировать готовый Android Internal release. Общую mobile release readiness не объявлять до прохождения обеих заявленных платформ.

P0 security triage и сбор продуктовой baseline могут идти независимо. Расширение продукта и автоматическое движение средств — после соответствующих gates. Календарные обещания давать после baseline; отсутствие устройства или credentials блокирует конкретный gate, а не всю разработку.

## 0. Контракт выполнения и baseline

1. Прочитать применимые AGENTS.md, MASTER_ROADMAP.md, PRODUCTION_ROADMAP.md, docs/PROJECT_STABILIZATION_2026-10-16.md и docs/mobile/{ROADMAP,ANDROID_TEST_ENV,MASVS_L1_CHECKLIST,DEVICE_MATRIX,RELEASE_CHECKLIST,RELEASE_RUNBOOK}.md. При конфликте статуса приоритет у MASTER_ROADMAP.md; расхождение записать.
2. Снять HEAD, git status и diff по затронутым областям. Проверить вложенные репозитории/submodules и их собственные инструкции. Сохранить перечень исходных WIP, не секретные payload.
3. Создать явный allowlist файлов и hunks для wallet/FFI. Особо проверить Cargo.lock, package-lock.json, Gradle и generated bindings: они могут содержать изменения нескольких треков. Не применять git add . и не коммитить смешанный lockfile целиком без разбора.
4. Не делать reset/clean/stash и не отменять исходные изменения ради чистого дерева. Требование чистоты означает: собственная работа завершена, исходный чужой WIP сохранён и перечислен. Если код зависит от исключённого WIP, сначала разобрать зависимость и проверить чистое воспроизведение выбранного набора коммитов.
5. Выяснить реальные команды из manifests/scripts, не выдумывать команды сборки. Выполнить targeted baseline; существующие failures отделить от новых.

Выход: краткий baseline с SHA, границами изменений, командами, результатами и внешними зависимостями. Работу вести последовательно; отдельные commits сами по себе не требуют параллельных агентов.

## 1. Завершить vault integrity

Опорные файлы: ancap-mobile/apps/acp-wallet-expo/lib/{vault-chunk.ts,vault.ts,secure-vault-adapter.ts}, vault*.test.ts и ACP-crypto/acp-mobile-ffi/.

Существующая реализация уже имеет generations, active pointer и pending generations. Сначала проверить её свойства, затем вносить минимальные исправления; не переписывать механизм без выявленной причины.

- Проверить UTF-8 byte length каждого записываемого значения. Сейчас chunkSecret использует string.length/slice. Либо доказать и валидировать ASCII-only сериализацию, либо сделать byte-safe разбиение с корректным Unicode roundtrip. Проверять положительный целочисленный размер chunk. Значение 1800 — внутренний бюджет; комментарий про 2048 не считать универсальной гарантией SecureStore на всех платформах.
- Валидировать metadata: строгий count, верхняя граница числа chunks и общего payload, версия формата. Отсутствующий, перемешанный или повреждённый chunk должен давать контролируемую ошибку. Использовать существующую криптографическую проверку keystore; checksum, если нужен для диагностики целостности записи, не является аутентификацией.
- Доказать атомарность: write → read-back/validation → active pointer → cleanup. При сбое до commit старое поколение доступно; сбой cleanup после commit не уничтожает новое. Обрабатывать ошибки pointer write и чтения pending metadata.
- Проверить crash после записи chunk до обновления count: cleanup должен знать, какие ключи удалять. Ограничить рост pending generations; не хранить неограниченный список в одном SecureStore value.
- Проверить save/save, save/wipe и migration/save. Сериализовать мутации, если текущая архитектура допускает гонки. После успешного wipe запоздалый save не должен воскресить кошелёк.
- Legacy migration: читать прежний формат, записывать и проверять новый, только затем удалять legacy. Ошибка миграции не должна портить единственную рабочую копию.
- PIN, biometric cancel/lockout и недоступный keychain не должны приводить к скрытому ослаблению защиты. Проверить смену биометрии, background lock и повторный запуск.
- Wipe: active/pending/legacy secrets, app-owned export, session state. Ошибки cleanup фиксировать без секретов; не показывать полное успешное удаление, если часть app-owned данных осталась. Не обещать физическое стирание flash или удаление внешней копии пользователя.

Приёмка: targeted unit tests и fault injection покрывают эти инварианты; typecheck и FFI tests зелёные. Наличие этих сценариев сначала сверить с существующими тестами, не создавать дубликаты.

## 2. Сделать recovery самостоятельным пользовательским сценарием

Сейчас keystore-export.ts пишет acp-keystore-export.json в documentDirectory и может молча завершиться, если директория недоступна. Проверить callers и исправить статус успеха, если пользователь не получил реальный backup.

- Экспортировать только зашифрованный keystore. Проверить формат, version, KDF/encryption parameters, проверку пароля и соответствие восстановленного public address. Не вводить собственную криптосхему.
- Добавить явное сохранение/передачу файла вне sandbox через подходящий существующему Expo stack системный механизм. Cancel, unavailable directory и I/O error должны быть различимы; сообщение «сохранено» показывать только по подтверждённому результату доступного API.
- Разделить Copy, Export file и Restore. Объяснить пользователю, что для восстановления нужны файл и пароль; clipboard не считать надёжным backup.
- Определить срок жизни промежуточного app-owned файла, правила удаления и доступность backup в OS backup. Проверить, что логи, screenshots, crash reports и evidence не содержат keystore, mnemonic, private key или пароль.
- Импортировать файл через явное действие пользователя, с ограничением размера, валидацией версии/формата и безопасным отказом на malformed/unsupported keystore. Не затирать текущий vault до полной проверки импортируемого.
- Подтвердить FFI → Expo restore и Expo → FFI restore, если оба направления заявлены поддерживаемыми. Использовать export_keystore_smoke и существующие vault-gen-smoke.ps1 / vault-external-restore-smoke.ps1 после проверки их расположения и предпосылок.

Приёмка: create → external export → очистка состояния тестового приложения → import без mnemonic → тот же address → local sign. Отдельно проверить wrong password, damaged/truncated file и unsupported version. Очистку проводить только на выделенном тестовом wallet/AVD с подготовленной копией.

## 3. Android: доказать полный local-sign путь

1. Pixel_10_Pro: собрать native dev client по ANDROID_TEST_ENV.md; Expo Go не засчитывать как проверку native FFI.
2. Пройти create → export → restart → unlock → fresh-state restore → send preview → Sign locally. Проверить сохранение адреса после повторного запуска и миграции.
3. Проверить подпись независимым verifier или chain validation: signer/address, network/chain, recipient, amount, fee и сериализованные bytes совпадают с подтверждённым preview. При изменении данных требовать новое подтверждение.
4. Проверить offline sign, RPC timeout и двойное нажатие. Неподписанный/неподтверждённый запрос не должен отправляться; timeout broadcast не должен автоматически создавать новую оплату.
5. Funded broadcast — отдельный сценарий с предоставленным operator test ACP, зафиксированными сетью и получателем. Подтвердить txid и включение/балансы по правилам ACP. Нет funds — local sign может быть passed, broadcast остаётся pending.
6. Повторить critical smoke на release candidate: debug native build не доказывает готовность release variant.

Evidence packet: commit SHA, версия build, OS/AVD, дата, точные команды и exit codes, сценарии expected/actual, обезличенные screenshots/logs, причины skipped. Artifact signatures и секреты не публиковать без необходимости. Маркеры P4-3/P4-9/P4-11/P2-3 обновлять только после сверки формулировок в текущем ROADMAP.md и соответствующего evidence.

## 4. Physical и store release

- На физическом Android проверить PIN retry/lock, biometrics success/cancel/lockout, background/resume, process death, смену biometric enrollment, external restore и wipe. Дополнить применимые проверки существующего MASVS checklist; перечислить непроверенные пункты отдельно.
- Проверить privacy controls, secret redaction, recovery UX и отсутствие незаявленного fallback с native local signing на удалённый walletd. Пользователь должен понимать фактический режим хранения и подписи.
- Собрать подписанный release candidate с build ID, SHA, dependency lock и проверяемой конфигурацией endpoints. Сверить разрешения, privacy/store declarations и supported platforms с реальным поведением и текущими release docs.
- Play Internal: upload → установка именно store artifact → critical recovery/sign smoke → зафиксированные versionCode и evidence. До расширения rollout определить критерии остановки и recovery/update path; для vault migration не считать downgrade заведомо безопасным rollback.
- iOS: macOS native build, физические Keychain/biometrics проверки и TestFlight installation smoke. Android evidence не переносить автоматически на iOS.
- Если нет macOS, physical device, signing credentials или store access: подготовить всё доступное, записать конкретный внешний шаг и оставить соответствующий gate открытым. Не объявлять релиз завершённым по emulator smoke.

## 5. Независимые треки без смешивания с wallet

**Fee-recycle:** отдельный commit для app/services/wacp_fee_recycle.py, scripts/wacp/fee_recycle_check.py и релевантных tests. Проверить boundary threshold, stale/missing inputs, decimal precision, повторный запуск и ошибки RPC. Результат — eligibility report для human wrap+LP; отсутствие автоматического перевода средств подтвердить по коду. Сохранять 1 ACP ↔ 10 wACP.

**Security:** triage CodeQL по реальному data flow, severity и runtime exposure; у каждого решения evidence и remediation/accepted-risk rationale. Проверить, что hashed Linux Python lock и dependency follow-up из stabilization документа действительно завершены: не повторять уже выполненное. Exploitable release-path issue блокирует затронутый релиз. Major Expo/RN/tooling upgrade — отдельная совместимость и regression scope.

**Ops:** заново измерить disk usage; 81% — историческое наблюдение. Retention только после проверки backup/restore evidence и владельца данных; не удалять node/DB state ради headroom. После node release — check_acp_peers.py; после web deploy — deployed SHA, migrations по runbook и health. Для растущей сети приёмка peers должна учитывать допустимый lag и согласованный chain point, а не случайную гонку чтений tip.

Запреты: не менять consensus/miner в wallet commit; не flip WACP_ORACLE_USE_V3 до Stage A–C и quote smoke; не включать Infinity/auto-LP; не делать sACP mint до legal S4; R9–R14 и FF_PROJECT_ECONOMY не расширять в рамках этого плана. Любые изменения внешних систем выполнять только в пределах отдельной авторизации оператора.

## 6. После gates: улучшать основной продукт измеримо

1. Уже во время mobile работы подготовить контракт событий discovery → preview → funded run → receipt → repeat run. События без wallet secrets и payment payload; определить session/run identifiers, denominators, окно измерения и baseline. Числовые KPI назначить после измерения, не выдумывать целевой conversion.
2. Первый продуктовый срез — один реальный ACP-paid workflow до проверяемого receipt. Устранить непонятные pending/failure состояния, добавить безопасный retry и защиту от повторного списания. Приёмка включает timeout после фактической оплаты, restart и получение уже существующего receipt.
3. Deposit watcher: сначала read-only/shadow reconciliation с текущим desk-assisted процессом. Затем duplicate/out-of-order events, cursor restart, backfill, concurrent workers, confirmation/reorg policy для каждой сети, atomic credit + idempotency, audit trail и manual exception queue. Автоматизацию включать ограниченно после совпадения результатов; desk fallback сохранять до доказанной устойчивости.
4. Smart Pay SQ-7 — после local-sign gate и готовности routePlan contract: preview/confirmation binding, expiry, изменившаяся fee/slippage, отказ отдельного leg, persisted state, reconcile-before-retry. Приёмка — подтверждённый маршрут без повторной оплаты при перезапуске.
5. React Flow — только после стабильного builder API и спроса по событиям/обратной связи. Community payouts — после acceptance/dispute/settlement controls. Остальные расширения сохранять staged backlog.

## Коммиты, evidence и итоговый отчёт Cursor

Рекомендуемые границы: vault integrity/tests → FFI keystore roundtrip → export/import UX → Android/release fixes → evidence/docs. Допустимо менять порядок FFI/UI по реальным зависимостям; каждый commit должен собираться с объявленными зависимостями. Fee-recycle/security/ops — отдельные changesets. Не включать unrelated WIP.

Для каждого gate записывать: status (pending/in_progress/passed/failed/blocked_external), commit, команда или ручной сценарий, результат, ссылка на evidence, оставшийся риск. Evidence хранить в docs/mobile/evidence/2026-10-17/ или принятом в репозитории месте; большие/чувствительные артефакты — в предназначенном для них закрытом хранилище.

Во время реализации запускать targeted tests; перед push — обязательные repository checks и полный suite, если этого требуют AGENTS.md/CI. Не считать interrupted runs успешными. Проверить воспроизведение выбранных commits без excluded WIP. Обновить roadmap сразу после доказанной приёмки.

Итоговый ответ Cursor: что изменено; SHA и границы commits; выполненные проверки и ссылки; какие gates открыты и почему; какие исходные dirty paths сохранены; следующий конкретный шаг. Не писать «всё готово», если external restore, release artifact, physical evidence или store installation не проверены.

## Стартовая инструкция для Cursor

Продолжи по актуальному ENGINEERING_AUDIT_2026-10-17.md: обнови baseline и проверь, что HEAD содержит перечисленные исправления. Completed-этапы повторно не реализовывай. Следующий отдельный changeset — совместимый API 36+ Android stack, полное 16 KB evidence и release signing; параллельно закрывай доступные system-picker/SAF сценарии. Сначала проверь актуальное состояние репозитория и существующих тестов. Заверши доступные локальные изменения и evidence, сохраняя исходный WIP. Не расширяй scope на bridge/consensus/sACP и не отмечай external gates закрытыми без проверки. При внешней зависимости продолжай независимую локальную работу и укажи точно, что требуется от оператора. Этот план сам по себе не авторизует production deploy, движение средств, store upload или внешнюю публикацию. Закоммить только относящиеся к выполняемой задаче проверенные изменения, если запуск плана оператором включает разрешение на коммиты; push и внешние действия выполняй по отдельной авторизации.
