> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Gate A full mint — operator send sheet

**Prepared:** 2026-10-04 (API paused; live Gate A)  
**Agent does not sign.** Gateway owner signs from `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`.

## Amounts

| Field | Value |
|-------|-------|
| Gate A | **pass** |
| `M_acp_smallest` | `3211738770169793` (~32,117,387.70169793 ACP) |
| `M_wacp_wei` | `321173877016979300000000000` |
| Human wACP | **321,173,877.0169793** |
| `to` | `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4` |
| Gateway | `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b` |
| wACP | `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402` |
| `depositRef` | `0xd91396719192cb120b68389dc44b1150b5d05a188cfc5690590f0f5b007682a7` |
| label | `gate-a-cutover-2026-10-04-full` |

## On-chain checks (pre)

| Check | Value |
|-------|-------|
| `owner()` | `0x396351…B2e4` (matches recipient) |
| gateway `paused()` | `false` |
| `maxSingleMint` now | `30240000000000000000000000` (30.24M wACP) |
| `mintCapPerDay` now | same 30.24M — **must raise** |
| recipient balance | ~15,029,782.92 wACP |
| totalSupply | ~35,685,986.34 wACP |

## Tx 1 — raise caps

BscScan Write Contract → `setCaps`  
- `maxSingle` = `321173877016979300000000000`  
- `perDay` = `321173877016979300000000000`

Calldata:

```
0x212bf31600000000000000000000000000000000000000000109ab36c2a79cb81dbce80000000000000000000000000000000000000000000109ab36c2a79cb81dbce800
```

```bash
cast send 0x57c24FF77B23a82328cb88914D4FD4EEBd93321b \
  'setCaps(uint256,uint256)' \
  321173877016979300000000000 321173877016979300000000000 \
  --rpc-url "$BRIDGE_BSC_RPC_URL" --private-key "$OPERATOR_KEY"
```

Tx hash: `ae6a816d82937d722176de5f24cf84859404e60ff7c5d6824a04b10fb15b7149`

## Tx 2 — mint full headroom

`mintWrapped(to, amount, depositRef)`  
- `to` = `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`  
- `amount` = `321173877016979300000000000`  
- `depositRef` = `0xd91396719192cb120b68389dc44b1150b5d05a188cfc5690590f0f5b007682a7`

Calldata:

```
0x7d8d3ce6000000000000000000000000396351df6420e6089dc67f4cbddc717f34ffb2e400000000000000000000000000000000000000000109ab36c2a79cb81dbce800d91396719192cb120b68389dc44b1150b5d05a188cfc5690590f0f5b007682a7
```

```bash
cast send 0x57c24FF77B23a82328cb88914D4FD4EEBd93321b \
  'mintWrapped(address,uint256,bytes32)' \
  0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4 \
  321173877016979300000000000 \
  0xd91396719192cb120b68389dc44b1150b5d05a188cfc5690590f0f5b007682a7 \
  --rpc-url "$BRIDGE_BSC_RPC_URL" --private-key "$OPERATOR_KEY"
```

Tx hash: `67a66df8c07f5495598f4dcd12219b8cb4664a538cc90ea53deea8579e212416`

**Confirmed after mint:** recipient ≈ **336,203,659.94** wACP; totalSupply ≈ **356,859,863.35** wACP; Gate A headroom = 0.

## Tx 3 — restore prior caps

`setCaps(30240000000000000000000000, 30240000000000000000000000)`

Calldata:

```
0x212bf316000000000000000000000000000000000000000000190391af4eed5994000000000000000000000000000000000000000000000000190391af4eed5994000000
```

Tx hash: `7801157ed480115e15b8b33c4648eefef9549233cc6bfb12dff9b35aa3643dbf`

## After

API unpaused (`BRIDGE_RAIL_PAUSED=false`). Docs updated.

## Notes

- Never mint into a Pancake pool.
- Do not enable `WACP_ORACLE_USE_V3` as part of this mint.
- Reserve snapshot was stale (~277 min) at prep time — re-check proof after mint.
