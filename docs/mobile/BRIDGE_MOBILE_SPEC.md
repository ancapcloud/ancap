> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge — Mobile UX Specification

Normative protocol: `docs/bridge-spec-v1.md`
Backend: `app/api/routers/bridge_rail.py`

## User-facing language

| Internal | UI label |
|----------|----------|
| Mint ACP → wACP | **Convert ACP to wACP** |
| Burn wACP → ACP | **Convert wACP to ACP** |

Always show disclaimer (custodial clearing rail, reserve risk).

## Decimal conversion

```
wacp_wei = acp_smallest * 10^10
acp_smallest_floor = wacp_wei / 10^10   (integer division on redeem)
remainder_wacp_wei = wacp_wei % 10^10   (not paid as ACP in v1)
```

Use `POST /bridge/quote/bsc-to-acp` for redeem quotes with remainder transparency.

## ACP → wACP flow (mobile)

1. User enters amount + BSC address (`0x...`).
2. App calls `POST /bridge/intents/acp-to-bsc` (auth optional per deployment).
3. UI shows deposit instructions (address / memo per rail config).
4. User signs ACP transfer **locally** to deposit target.
5. App polls intent status → stepper:
   - Created → Waiting for deposit → Deposit detected → Confirming → Minting → Completed

## wACP → ACP flow

**Only when `bridgeReverseEnabled: true` in mobile config.**

1. Quote via `POST /bridge/quote/bsc-to-acp`.
2. Create intent `POST /bridge/intents/bsc-to-acp`.
3. User burns wACP on BSC (external wallet or in-app BSC key — v1.2).
4. Submit burn tx hash when API supports it.
5. Poll until `COMPLETED` or `FAILED`.

Current backend note (2026-05-23): reverse rail is live in runtime, but mobile should still gate exposure from config until the app product/security/recovery posture is explicitly approved for release.

## Reserve proof screen

- `GET /bridge/wacp/reserve-proof`
- Read-only display for trust; link to `docs/wacp/reserve`

## PancakeSwap

Deep links from config / constants in `bridge_rail.py` (`WACP_SWAP_URL`) — open in browser, not in-app exchange.

## What mobile must not claim

- Guaranteed peg price
- Investment returns
- Instant guaranteed completion (show ETA + support)
