> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# sACP — Stable ACP (ACP-backed stablecoin)

Status: **foundation (S0)** — contract + public API + exchange catalog + docs.  
Mint/redeem orchestration and mainnet deploy are **not** live.

## Product

| Symbol | Name | Network | Decimals |
|--------|------|---------|----------|
| **sACP** | Stable ACP | BNB Smart Chain (BEP-20) | 18 |

**sACP** is ANCAP’s commerce-oriented stablecoin. It is **distinct** from:

- **ACP** — platform accounting unit / native coin (not a fiat peg)
- **wACP** — 1:1 wrap of ACP on BSC (reserve-backed wrap, not USD-targeted)
- Partner **USDC/USDT** — third-party ramps (`/pay-with-stablecoin` waitlist)

## Peg model

- **Target:** `1 sACP ≈ 1 USD` (soft target for commerce pricing)
- **Backing:** ACP collateral held in a dedicated reserve (overcollateralized)
- **Not a promise:** no guaranteed USD redemption; operator-mediated rail (same honesty bar as wACP bridge docs)
- **Invariant (target):**  
  `collateral_value_usd(ACP_reserve) >= min_collateral_ratio * circulating_sACP`  
  Default min ratio: **1.50** (150%)

## Conversion (foundation config)

Config keys (backend):

- `FF_SACP` / `ff_sacp` — feature flag (default on for catalog/API visibility)
- `sacp_contract` — BEP-20 address (empty until deploy)
- `sacp_gateway_contract` — mint/burn gateway (empty until deploy)
- `sacp_reserve_acp_address` — ACP collateral address
- `sacp_acp_per_usd` — indicative ACP amount required per 1 USD of peg target (default `"4"` ≈ $0.25/ACP soft quote)
- `sacp_min_collateral_ratio` — default `"1.50"`

Indicative mint (user locks ACP → receives sACP):

```
sacp_out = acp_in / (sacp_acp_per_usd * sacp_min_collateral_ratio)
```

Indicative redeem (burn sACP → unlock ACP): reverse with protocol fee (TBD).

## On-chain

- `contracts/bridge-bsc/src/SACP.sol` — BEP-20; mint/burn only via gateway
- Gateway mint/burn mirrors wACP pattern (`mintByGateway` / `burnByGateway`)
- Deploy scripts: follow-up (S1); do not reuse `WACP.sol` or rename wACP

## Public API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/v1/sacp/status` | Enabled/paused, contracts, peg notes |
| GET | `/v1/sacp/reserve-proof` | Collateral vs circulating (snapshots when recorded) |
| POST | `/v1/sacp/intents/mint` | Create mint intent (ACP collateral → sACP) |
| POST | `/v1/sacp/intents/redeem` | Create redeem intent (burn sACP → ACP) |
| GET | `/v1/sacp/intents/{id}` | Intent status |
| POST | `/v1/sacp/admin/intents/{id}/bind` | Operator bind tx hashes (`X-Bridge-Operator-Secret`) |
| POST | `/v1/sacp/admin/snapshots` | Operator reserve snapshot |

## Exchange office

Asset id: `sacp_bsc`  
Rail: `stablecoin`  
Quote mode: `stable_peg`  
Directions: both (ACP ↔ sACP indicative quotes when `ff_sacp`)

## Roadmap slices

| ID | Scope | Status |
|----|--------|--------|
| S0 | Spec, contract source, public status API, catalog, docs | done |
| S1 | Gateway + DeploySacp script + forge tests; env wiring | done (broadcast addresses = ops) |
| S2 | Mint/redeem intents + reserve snapshots table/API | done |
| S3 | Smart Pay sACP asset + ACP→sACP route | done (merchant UX polish later) |
| S4 | Compliance checklist before public mint | checklist landed; legal sign-off pending |

## Compliance note

Treat sACP as a **utility commerce settlement token** with a USD *target*, not as a licensed e-money product, until legal review completes. See `docs/SACP_COMPLIANCE_CHECKLIST.md`. Public copy must not claim “guaranteed USD peg” or “bank deposit equivalent.”
