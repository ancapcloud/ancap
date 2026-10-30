> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# wACP -> PancakeSwap Readiness

## Goal
Ship wACP as a credibly reserve-backed wrapped ACP asset on BNB Smart Chain, then scale from a technical bootstrap into a real market launch without breaking reserve discipline.

## Current live state as of 2026-05-07
- PancakeSwap V2 pair is already live: `wACP / USDT`
- pair address: `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601`
- pair URL: <https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601>
- swap URL: <https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>
- wACP contract: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- bridge / gateway contract: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`
- ACP reserve address: `acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz`
- public reserve proof: <https://ancap.cloud/api/v1/wacp/reserve-proof>
- public status endpoint: <https://ancap.cloud/api/v1/wacp/status>
- bridge runtime: enabled, not paused, `dry_run=false`
- ACP confirmations policy: `1`
- BSC confirmations policy: `18`
- reverse `BSC -> ACP` path is live, funded, and automated
- current reserve proof reports approximately `100999.994999 ACP` in reserve
- current wACP total supply is still `1 wACP`
- current backing ratio is approximately `100999.994999`

## Interpretation
The bridge is no longer in a pure pilot-only direction.
The reserve is funded enough for a `100000 wACP` rollout in principle.
What is still missing is the controlled execution sequence for minting, LP sizing, public messaging, and post-launch monitoring.

## Core launch gates
No reserve proof -> no official scale-up.
No clean supply-vs-reserve math -> no official scale-up.
No clear liquidity policy -> no official scale-up.
No published contract and pair references -> no official scale-up.
No rollback / pause posture -> no official scale-up.

## Phase 0 — Constants to freeze

### Token spec
- Native ACP decimals: `8`
- wACP decimals on BSC: `18`
- Conversion rule:
  - `wacp_wei = acp_smallest_unit * 10^10`
  - `acp_smallest_unit = wacp_wei / 10^10`
- `name = Wrapped ACP`
- `symbol = wACP`
- `chainId = 56`

### DEX choice
For the first meaningful market phase:
- Primary venue: **PancakeSwap V2**
- Primary pair: **wACP/USDT**
- Secondary future option: **wACP/ACP**
- Avoid making `wACP/WBNB` the main reference market at launch

Reason:
- V2 is simpler to manage operationally
- USDT pair is easier to communicate publicly
- WBNB adds volatility noise that is not useful for the first real launch

## Phase 1 — Backing and mint envelope

### Canonical invariant
`minted_wACP_on_BSC <= ACP_reserve_smallest_units - operational_buffer`

### Live reserve math snapshot
From `GET /api/v1/wacp/reserve-proof` on 2026-05-07:
- `acp_reserve_balance_smallest = 10099999499900`
- `wacp_total_supply_wei = 1000000000000000000`
- `wacp_total_supply_acp_smallest = 100000000`
- `backing_ratio = 100999.994999`

Equivalent human view:
- reserve: about `100999.994999 ACP`
- minted supply: `1 wACP`
- unused mint headroom before buffer: about `100998.994999 ACP`

### Practical conclusion
A `100000 wACP` mint is **backing-feasible** right now if Andrew wants to consume almost all current reserve headroom.
That does **not** mean all `100000 wACP` should be dropped into liquidity.

## Phase 2 — Safe `100000 wACP` rollout sequence

### Recommended sequence
1. Keep reserve funded above `100000 ACP` first
2. Mint `100000 wACP` to the treasury / operator wallet, not directly into LP
3. Verify total supply and reserve proof immediately after mint
4. Add only a controlled tranche of the minted inventory to PancakeSwap V2 liquidity
5. Keep the rest in treasury for future market-making, OTC, treasury ops, or staged LP adds
6. Publish official reserve-proof and pair links only after post-mint verification is clean

### Why not LP the full 100000?
Because it is strategically dumb.
Full-LP deployment would:
- make price discovery too brittle
- expose too much inventory at once
- leave no treasury-controlled supply for later operations
- increase damage if initial pricing is wrong

## Phase 3 — Liquidity sizing policy

### Minimum operator checklist before adding liquidity
- enough `BNB` for approvals and LP transactions
- enough `USDT` for the paired side
- minted `wACP` balance confirmed in the LP wallet
- reserve proof still healthy after mint
- official pair and swap links prepared
- clear initial price target chosen in advance

### Suggested staged liquidity approach
Instead of LPing all `100000 wACP`, use staged seeding such as:
- Stage A: small discovery liquidity
- Stage B: moderate top-up after swap behavior is observed
- Stage C: deeper liquidity only after market and ops stay stable

The exact tranche sizes should be chosen deliberately from:
- desired start price
- USDT budget available
- target slippage range
- how much treasury inventory should remain off-LP

## Phase 4 — Public trust artifacts
Publish and keep consistent:
- reserve proof endpoint: <https://ancap.cloud/api/v1/wacp/reserve-proof>
- status endpoint: <https://ancap.cloud/api/v1/wacp/status>
- contracts page: <https://ancap.cloud/docs/wacp/contracts>
- PancakeSwap docs page: <https://ancap.cloud/docs/wacp/pancakeswap>
- pair URL: <https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601>
- swap URL: <https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>

## Phase 5 — Launch checklist for the `100000 wACP` step
- [x] reserve is funded above `100000 ACP`
- [x] reserve proof endpoint is live
- [x] pair already exists
- [x] swap URL already exists
- [x] reverse redeem path is live
- [x] wACP contract is verified
- [ ] explicit mint transaction approved by Andrew in active session
- [ ] explicit LP sizing approved by Andrew in active session
- [ ] operator wallet balance checks done immediately before transaction
- [ ] post-mint reserve proof rechecked
- [ ] post-mint total supply rechecked
- [ ] public announcement text prepared with official links

## Red flags
Do **not** proceed with the `100000 wACP` mint if any of these are true:
- reserve proof turns stale or unhealthy
- reserve drops below the intended mint envelope
- LP wallet lacks enough gas or paired USDT
- the mint would consume headroom needed for operational buffer
- the intended LP plan has no explicit start price
- the transaction is being rushed without immediate post-mint verification

## Final recommendation
Current state is good enough to prepare for the `100000 wACP` step.
But the right move is:
- reserve first
- mint to treasury second
- verify third
- add **partial** liquidity fourth
- publish links fifth

That keeps the asset reserve-backed, the launch coherent, and the treasury flexible.