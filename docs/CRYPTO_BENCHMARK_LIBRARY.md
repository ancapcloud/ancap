> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Crypto Benchmark Library (QOBLIB-style)

> Status: active baseline | Added: 2026-09-10  
> Inspiration: [IBM Quantum QOBLIB](https://lnkd.in/p/e7KKfMEA) — open benchmarks, strong classical baselines, no “advantage” claim without measured pass.  
> Public API: `GET /v1/crypto/benchmark` · UI: `/reserves`

## Problem

Crypto rails (ACP / wACP / sACP) invite trust claims: “fully backed,” “live,” “production-ready.” Like quantum optimization, **a claim is only as strong as the baseline behind it**. ANCAP publishes fixed benchmark classes and measures live runtime against them.

**We do not guarantee safety.** We bound risk by measuring vs published baselines.

## Benchmark classes

| ID | Baseline | Source |
|----|----------|--------|
| `reserve_backing` | `backing_ratio >= 1.0` when completed wACP supply > 0 | wACP reserve-proof |
| `snapshot_freshness` | Latest bridge snapshot age ≤ 60 min **or** live proof age ≤ 15 min | `bridge_reserve_snapshots` / proof timestamp |
| `intent_pipeline` | `FAILED == 0`; `PENDING_DEPOSIT` noted (TTL cancel allowed) | Bridge intent counts |
| `dry_run_honesty` | If bridge mint live → `dry_run=false`; dry-run must not claim full production | Settings + public status |
| `sacp_readiness` | sACP contracts configured **or** status openly `not_configured` | sACP settings + reserve-proof |
| `contract_trust` | Official wACP + gateway addresses published; verification flags reported honestly | wACP public status |

## Results

Each class returns: `pass` | `fail` | `pending`.

- **pass** — observed meets baseline  
- **fail** — baseline violated (public note explains why)  
- **pending** — rail disabled, data unavailable, or pre-production posture  

**Overall** = worst class result (fail > pending > pass).

## Related controls

- [`docs/EMBODIED_AI_SECURITY_CONTROLS.md`](EMBODIED_AI_SECURITY_CONTROLS.md) — Physical AI adapters (separate track)  
- [`docs/bridge-next-steps.md`](bridge-next-steps.md) §5 — reserve-proof maturity  
- [`docs/STABLECOIN_SACP_SPEC.md`](STABLECOIN_SACP_SPEC.md) — sACP collateral rules  
- [`docs/OFFICIAL_CONTRACT_ADDRESSES.md`](OFFICIAL_CONTRACT_ADDRESSES.md) — trust addresses  

## QOBLIB mapping

| QOBLIB idea | ANCAP crypto analogue |
|-------------|----------------------|
| Open problem classes | Six fixed benchmark classes above |
| Classical baseline | Published numeric/string baselines in this doc |
| Submitted results | Live API measurement each request |
| No advantage without baseline | No “production-ready” marketing without scorecard pass |

## Next actions

- [x] Public scorecard API + `/reserves` UI  
- [x] Snapshot-backed backing ratio when fresh  
- [x] Stale snapshot + reconciliation mismatch on public proof  
- [ ] sACP mainnet deploy + indexer (S1–S2)  
- [ ] Monthly transparency report export from scorecard history  
