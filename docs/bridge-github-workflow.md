> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# GitHub / production workflow — bridge rail

Aligned with the custodial wACP plan: all durable changes go through **GitHub**; production is the target runtime.

## Branch naming (suggested)

| Topic | Branch prefix |
|-------|----------------|
| Specification / docs | `spec/bridge-v1` |
| Solidity (Foundry) | `contracts/bsc-wacp` |
| API / orchestrator / jobs | `backend/bridge-orchestrator` |
| Frontend `/bridge/*` | `frontend/bridge-ui` |

Flow: branch off `main` → PR → review → CI green → merge.

## Release tags

- `bridge-v1.0.0-testnet` — contract addresses + API revision verified on BSC testnet.
- `bridge-v1.0.0-mainnet` — production contract addresses + deployed API/frontend revision.

Tag message should list: wACP address, gateway address, Alembic head revision, Docker image digest (if applicable).

## Secrets

Never commit mnemonics, operator keys, or `BRIDGE_OPERATOR_SECRET`. Use the same patterns as other ANCAP secrets (e.g. `Sicret/` volume in [docker-compose.prod.yml](../docker-compose.prod.yml)).

## CI

- Python: run existing test suite + `pytest tests/test_bridge_decimal.py`.
- Solidity: from `contracts/bridge-bsc`, after `forge install foundry-rs/forge-std@v1.9.4`, run `forge test` (Docker example in [contracts/bridge-bsc/README.md](../contracts/bridge-bsc/README.md)).

## Docker / Foundry note

When the mounted project is a Git repo, run `git config --global --add safe.directory /repo` inside the container before `forge install` if Git reports “dubious ownership”.
