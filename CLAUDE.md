# ANCAP — Claude Code Memory

## Project Identity

ANCAP is an ACP-first AI workflow platform. Users, crypto teams, creators, and AI agents buy, create, and sell paid AI workflows for ACP. Primary LLM is Teneta/Claude-compatible Anthropic API. Payments are ACP-first — Stripe/fiat is a later adapter.

Key identities:
- ACP = platform accounting unit (1:1 with itself)
- wACP = wrapped ACP on BSC (**1 ACP ↔ 10 wACP** as of 2026-10-04; `app/services/bridge_decimal.py`)
- sACP = Stable ACP — USD-targeted, ACP-collateralized commerce stablecoin on BSC (`docs/STABLECOIN_SACP_SPEC.md`); distinct from wACP and partner USDC/USDT
- ACP-crypto/ = Rust chain/wallet source of truth (sibling to this repo)
- ancap-mobile/ = React Native Expo wallet (sibling or submodule)
- `app/` = FastAPI backend
- `frontend-app/` = Next.js frontend

## Key Decisions (do not re-evaluate — resolved)

- **Pydantic schemas**: Always define request/response models in `app/schemas/*.py`, never locally inside router files. FastAPI evaluates Pydantic types at import time; locally-defined models cause `TypeError: Annotated[...] is not fully defined` at startup.
- **Org API key deletion**: Use a direct `delete(ApiKey).where().where()` with `result.rowcount` check — NOT `session.get()` or `scalar_one_or_none()`. Async SQLAlchemy sessions can return None from ORM reads in some transaction isolation cases.
- **agent_id nullable for org-owned keys**: `ApiKey.agent_id` is nullable. Org-owned keys have `agent_id=None`, `org_id=<uuid>`. Agent-owned keys have `org_id=None`, `agent_id=<uuid>`.
- **expo module imports**: Use static module-level imports, NOT `await import("expo-module")`. Dynamic imports cause TS1323 errors in expo modules.
- **Linking import in React Native**: Always `import { Linking } from "react-native"`, never from `expo-router`.
- **bscRpcUrl TypeScript chain**: When adding fields to the mobile config, update three places: `app/schemas/mobile_acp.py`, `app/api/routers/mobile_acp.py` (backend), AND `ancap-mobile/packages/acp-api-client/src/types.ts` AND run `npm run build` in that package. The SDK uses compiled `dist/` output, not source `.ts` files.
- **ACL line ending normalization**: CRLF auto-conversion happens on Windows git checkouts. The Kotlin and Swift FFI binding files (`acp_mobile_ffi.kt`, `acp_mobile_ffi.swift`) trigger this on every git operation. Discard whitespace-only changes with `git checkout -- <file>` before committing.

## Known Workarounds

- **Backend test runtime**: `pytest tests/ -q` takes ~6-8 min for the full suite (258+ tests). For faster feedback, run targeted subsets: `pytest tests/api/test_organizations.py tests/api/test_bridge_rail.py tests/api/test_workflow_store.py -q`.
- **Pycache stale bytecode**: After updating Python code, sometimes old error messages persist. Fix: `find . -path "*/__pycache__/*.pyc" -delete`.
- **FastAPI route verification**: To check if a route exists without starting the server: `python -c "from app.main import app; print([r.path for r in app.routes if 'keyword' in r.path])"`.
- **`/internal/frontend-build`**: This is a Next.js route in `frontend-app/src/app/internal/frontend-build/route.ts` — NOT a FastAPI route. It reads `.next/BUILD_ID` or `NEXT_PUBLIC_APP_BUILD_ID` env var.
- **Alembic migration run**: After pulling on any deploy target, always run `alembic upgrade head` before starting services. Recent migrations: 051 (mobile ACP indexer), 052 (bridge reserve snapshots), 053 (api_keys org_id), 054 (api_keys agent_id nullable), 057 (org NFC identity), 058 (securities + watch fleet + orbital edge), 059 (AETERNA DNA vault + intents + partners), 069 (sACP stablecoin ops + reserve snapshots), 070 (lunar land), 071 (mail IMAP/SMTP provider accounts), 072 (passport education docs ChaCha20-Poly1305), 073 (DNA/RNA bank AES-256-GCM HKDF-SHA384), 074 (perimeter cleanup Abrams Suite-B vault), 075 (literary auction + reviews.rating), 076 (Nexus social_posts people+robots), 077 (auction-deal X-Wing draft-10 PQC envelopes), 078 (FLORA flower auction), 079 (dark matter auction).

## Preferences

- **Commit style**: Small, atomic commits as I go. Message format: `type(scope): description` (e.g., `fix(orgs): resolve delete 404 with direct DELETE statement`).
- **Working tree**: Keep clean before stopping a session. `git status --short` should return nothing.
- **Roadmap discipline**: When fixing something, check the roadmap files immediately after — correct the status markers. Stale docs are the enemy of reliable execution.
- **Test before push**: Always run the targeted test subset for the area being changed before pushing.
- **Docs vs code**: If a route is documented in the smoke targets but doesn't exist in code — implement it or remove it from docs. Don't let docs drift from code.

## Recurring Mistakes to Avoid

- **Do NOT commit `.pyc` files or `__pycache__/`** — they are in `.gitignore` but can slip through with `git add .`.
- **Do NOT use `session.commit()` before making additional changes in the same session handler** — if you need to modify a row you just created in the same request, `flush()` after each modification. `commit()` ends the transaction boundary.
- **Do NOT assume Projects persist conversation history** — Projects only persist custom instructions. This session started with no memory of previous sessions. Read `CLAUDE.md`, `MASTER_ROADMAP.md`, and `PRODUCTION_ROADMAP.md` at session start.
- **Do NOT import Pydantic models from router files into other routers** — always import from `app.schemas.*`.
- **Do NOT run the full test suite during active development** — it takes 6-8 min. Use targeted tests. Run the full suite only before pushing or when auditing.

## Architecture Decisions Worth Preserving

- `app/db/models.py` — single source of truth for all SQLAlchemy models. Add new models here, not inline.
- `app/services/` — business logic layer. Routers call services; services handle DB operations.
- `app/schemas/` — one file per domain (e.g., `keys.py`, `mobile_acp.py`, `bridge_rail.py`).
- Bridge reconciliation runs via `POST /v1/system/jobs/tick`. Snapshots are persisted to `bridge_reserve_snapshots`. Alerts checked via `GET /v1/bridge/admin/alerts`.
- Mobile ACP indexer ticks via `POST /v1/system/jobs/tick` (same job scheduler).
- LLM execution with reliability: `app/services/llm.py` handles retry/backoff, degraded fallback, and usage event recording. Provider health surfaced in `/system/health/full`.

## Current Phase

Phase 6 — ACP Mobile Wallet MVP (in progress). Active items:
- `[~]` PIN + biometrics (`expo-local-authentication`) — code wired; physical-device sign-off open
- `[~]` SecureVault wiring (walletd fallback until native FFI ready) — code wired; physical sign-off open
- `[x]` i18n EN/RU/UK/DE (`i18next`)
- `[~]` MASVS L1 checklist — repo baseline closed; physical sign-off open
- `[x]` Exchange office foundation — ACP-hub multi-asset catalog/quote/tickets + Expo Exchange tab (`docs/mobile/EXCHANGE_OFFICE_FOUNDATION.md`); **ticket auth-settle/sync + USDT→ACP swap link shipped**; full auto deposit watcher still desk-assisted
- `[x]` OTC commodities rail (oil/gas/uranium/timber/sand/stone/ores) + Markets AI prediction workflows (`/ai/workflows`)
- `[ ]` React Flow strategy canvas (Phase 7, after builder API stable)

**Monetization:** not a work-stop blocker. ACP-first loop live; `/buy-acp` crypto-first; Stripe 4.1 = operator live verification only.

**Public repo Phase 1:** root `README.md` exists. Theodore / progress bots must not report missing README or “monetization after first ACP cycle” as blockers.

Local Android test env (**blocker cleared 2026-09-11**):
- AVD `Pixel_10_Pro` + `ancap-mobile/scripts/start-android-test-env.ps1`
- Docs: `docs/mobile/ANDROID_TEST_ENV.md`
- Do **not** report “no device / no test environment” as a work-stop blocker

Still open (operator follow-up, not freeze):
- Create/send/sign smoke on emulator via `npx expo run:android`
- Play Internal / TestFlight uploads
- iOS native build (`build-ios-native.ps1` on macOS)

Phase 7 CI: Playwright smoke in CI (needs separate job with backend service).

Planned capital track (not blocking Phase 6): Securities intake R9 — promissory notes, shares, securities register/pledge (`docs/SECURITIES_INTAKE_ROADMAP.md`). Foundation: S0 done, S1 API/tables in `058_r9_r10_r11`.

Planned workplace wearables track (not blocking Phase 6): Apple Watch HR fleet R10 / mobile Phase 5.6 — 3 watches per employee, band rotation for charging, heart-rate sync (`docs/mobile/APPLE_WATCH_EMPLOYEE_FLEET.md`). Foundation: W0 done, W1 inventory/rotation/HR ingest API in migration `058`.

Planned orbital infra track (not blocking Phase 6): Orbital ANCAP datacenters R11 — SpaceX sealed edge payloads → future datacenters in space; phases X0–X7 (`docs/SPACEX_SATELLITE_ENCRYPTED_SERVERS_ROADMAP.md`). Foundation: control-plane registry + `FF_ORBITAL_EDGE` (migration `058`).

Planned decentralization track (not blocking Phase 6): Full decentralization R14 — multi-operator ACP mesh, federated API/read plane, attested edge, operator exit; phases D0–D5 (`docs/FULL_DECENTRALIZATION_ROADMAP.md`). Complements R11 space tier.

Planned longevity track (not blocking Phase 6): AETERNA R12 — DNA vault, Sequencing.com-style import, ACP-paid genomic/longevity consult workflows (1,000,000 ACP), partial mRNA-reprogramming consult (eTurna/USPTO allowance literacy as of 11 Sep 2026), stem-cell organ print (250,000 ACP / organ, wisdom-tooth DPSC fallback, licensed bioreactor partner only), veterinary organ rails (feline tissue cryoconservator-restorer 75,000 ACP; canine VET REGEN POD 180,000 ACP; conceptual partner architecture, licensed veterinarian only; `/legal/vet-regen`), Vinci light chamber (48,000 ACP photobiomodulation / LED session protocol; Leonardo sunlight-health literacy; licensed phototherapy partner only; `/legal/light-chamber`), microwave body contouring (52,000 ACP contact-cooled 2.45 / 5.8 GHz applicator; licensed aesthetic/dermatology partner only; `/legal/body-contouring`), BioFusion micromanipulation chamber (88,000 ACP IVF/ICSI / plant / BSL-lab partner brief; `/legal/biofusion`), wisdom-tooth DPSC biomaterial (65,000 ACP licensed bioreactor construct, not a full organ; `/legal/dpsc`), Vascular Care+ (54,000 ACP anhydrous N2+O2 + light-wave; licensed phlebology/aesthetic partner only; `/legal/vascular-care-plus`), Vascular Care (58,000 ACP ultrasound/RF/thermal; `/legal/vascular-care`), needle-free transdermal pistol (46,000 ACP aerosol + carrier gas; licensed clinic partner only; `/legal/transdermal`), M-receptor delivery subscription (12,000 ACP / month; licensed clinic retainer for patch / iontophoresis / inhaler / vagus-adjacent neuromodulation; `/legal/m-receptor`), artificial oxygen carrier (92,000 ACP hemoglobin-vesicle / PFC-emulsion architecture literacy; licensed bioreactor / transfusion-medicine partner only; `/legal/oxygen-carrier`), synthetic blood / Black Mamba architecture (98,000 ACP multi-layer HBOC/PFC + modified peptide literacy; licensed bioreactor partner only; `/legal/synthetic-blood-mamba`), ADHD / СДВГ support brief (42,000 ACP licensed clinician / child psychiatry–neurology partner literacy; not a diagnosis, prescription, stimulant compounding, or guaranteed academic/financial outcome; `/legal/adhd-support`), PulmoPure lung-care subscription (14,000 ACP / month; licensed pulmonology partner literacy; not a CE/FDA device, ozone therapy, medical-gas compounding, or guaranteed clean-lungs outcome; `/legal/pulmopure`). , Project Barsuk quantum-pen brief (36,000 ACP secure-comms literacy; not Parker/weapon; `/legal/barsuk`), teleport-earphones medevac fiction brief (58,000 ACP; not Apple/real teleport/weapon; `/legal/teleport-earphones`), Installation Project / Проект Установки (72,000 ACP high-protein infant milk-line + neonatal hyperbaric literacy; licensed neonatology/nutrition partner only; not formula sold by ANCAP; not CE/FDA HBO; not home HBO; not a guaranteed rickets/anemia/infection outcome; `/legal/installation-project`; insurance `neonatal_install`). Track: `docs/AETERNA_LONGEVITY_MARKETPLACE_ROADMAP.md`. Foundation: A0 done, A1 API/tables in `059_aeterna` + `FF_AETERNA`; organ-print SKU + mRNA-reprogramming consult + vet rails + Vinci light chamber + microwave body contouring + BioFusion + DPSC biomaterial + vascular / transdermal / M-receptor / oxygen-carrier / synthetic-blood / ADHD-support / PulmoPure / Barsuk / teleport-earphones / Installation Project rails wired in catalog/intents/frontend; DNA-matched pheromone perfume (8,900 ACP / bottle, /legal/dna-pheromone-perfume). Antique fire restore after total fire (42,000 ACP reverse-combustion / metallurgy conservation literacy; six-stage protocol is artifact analogy not medical burn care; /antique-fire-restore, /legal/antique-fire-restore; insurance ntique_fire_restore). Antique fire restore after total fire (42,000 ACP reverse-combustion / metallurgy conservation literacy; six-stage protocol is artifact analogy not medical burn care; `/antique-fire-restore`, `/legal/antique-fire-restore`; insurance `antique_fire_restore`).

Planned lunar track (not blocking Phase 6): Lunar land trading R13 — science-tagged parcel registry + ACP interest desk (NASA–IBM LFM themes). Track: `docs/LUNAR_LAND_TRADING_ROADMAP.md`. Foundation: L0/L1 in `070_lunar_land` + `FF_LUNAR_LAND` + `/lunar`.

Embodied / humanoid model adapters (Unitree UnifoLM etc.): **off by default** — `FF_EMBODIED_ADAPTER=false`, register at `GET /v1/embodied-ai/security`, policy in `docs/EMBODIED_AI_SECURITY_CONTROLS.md`. Never host weights on the API host; never share process space with ACP/bridge keys.

Crypto Benchmark Library (QOBLIB-style): public scorecard at `GET /v1/crypto/benchmark` + `/reserves`; baselines in `docs/CRYPTO_BENCHMARK_LIBRARY.md`. No “production-ready” claim without measured pass vs published baselines.
