> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Operator checklist — mint + send wACP to hot wallet

**Recipient (locked):** `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`  
**Ratio:** 1 ACP ↔ 10 wACP (cutover 2026-10-04)

## Preconditions

- [x] Bridge paused during API deploy of ratio cutover
- [x] Gate A pass (full headroom mint)
- [x] Recipient address verified character-by-character

## A — Mint (full Gate A)

- [x] setCaps raise: `ae6a816d82937d722176de5f24cf84859404e60ff7c5d6824a04b10fb15b7149`
- [x] mintWrapped ~321,173,877.02 wACP: `67a66df8c07f5495598f4dcd12219b8cb4664a538cc90ea53deea8579e212416`
- [x] setCaps restore (30.24M): `7801157ed480115e15b8b33c4648eefef9549233cc6bfb12dff9b35aa3643dbf`
- [x] Post balance on recipient ~**336,203,659.94** wACP; Gate A headroom = 0

## B — Transfer

- [x] n/a — mint-to-self (bridge_signer == recipient)

## After

- [x] Unpause bridge — `BRIDGE_RAIL_PAUSED=false`
- [x] Fill tx table in `docs/BRIDGE_RATIO_CUTOVER_2026-10-04.md`
- [x] Do **not** enable `WACP_ORACLE_USE_V3` unless quote smoke passed separately
