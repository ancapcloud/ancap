> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# wACP 100000 rollout plan

> Superseded for **new liquidity deployment** by [WACP_LIQUIDITY_V3_PLAYBOOK.md](./WACP_LIQUIDITY_V3_PLAYBOOK.md) (V3 primary, V2 thin reference).  
> Keep this doc for historical 100k mint envelope planning.

## Objective
Execute a controlled scale-up from the current live state to:
- reserve-backed supply of `100000 wACP`
- staged liquidity on `wACP/USDT` (V3 concentrated + thin V2 reference)
- public trust links for reserve proof and pair discovery

## Live starting point on 2026-05-07
- reserve proof URL: <https://ancap.cloud/api/v1/wacp/reserve-proof>
- status URL: <https://ancap.cloud/api/v1/wacp/status>
- pair URL: <https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601>
- swap URL: <https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>
- reserve: about `100999.994999 ACP`
- current supply: `1 wACP`
- backing status: `healthy`
- reverse redeem path: live

## Non-goals
This rollout is **not**:
- a promise to LP the full minted amount
- a promise of deep liquidity on day one
- a reason to bypass post-mint verification

## Canonical policy
Minted supply must never exceed reserve-backed capacity.
Treasury inventory and LP inventory are not the same thing.
LP only the amount that matches the chosen launch depth.

## Execution order

### Step 1 — Pre-flight checks
Verify live right before action:
- reserve proof still healthy
- reserve still above `100000 ACP`
- bridge enabled and not paused
- treasury / operator wallet has enough gas BNB
- treasury / operator wallet has enough USDT for planned LP

### Step 2 — Mint
Mint `100000 wACP` to treasury / operator wallet.
Do **not** mint directly into a pool.

### Step 3 — Immediate verification
Right after mint:
- verify `totalSupply`
- verify treasury `balanceOf`
- verify reserve proof endpoint still reports healthy backing
- verify bridge status endpoint still reports live state

### Step 4 — Choose LP tranche
Pick a deliberate tranche for PancakeSwap V2.
Example logic:
- small tranche if price discovery is the priority
- larger tranche only if treasury accepts tighter inventory commitment

The tranche must be chosen from:
- desired starting price
- USDT budget
- acceptable slippage
- amount of wACP to keep off-market

### Step 5 — Add liquidity
Use PancakeSwap V2 `wACP/USDT`.
Record:
- LP tx hash
- resulting reserves
- any approval tx hashes
- updated pair URL if needed

### Step 6 — Smoke tests
Perform at least:
- one small buy
- one small sell

Confirm:
- routing works
- quotes are sane
- token metadata is acceptable
- pair page is shareable

### Step 7 — Publish official references
After post-mint and post-LP checks are clean, publish:
- reserve proof URL
- status URL
- contract address
- pair URL
- swap URL

## Operator checklist
- [x] pair already exists
- [x] reserve proof already exists
- [x] reverse redeem path is live
- [x] reserve currently covers the planned 100000 envelope
- [ ] mint tx approved by Andrew
- [ ] LP tranche approved by Andrew
- [ ] pre-flight wallet balances checked immediately before action
- [ ] post-mint verification completed
- [ ] post-LP smoke tests completed
- [ ] public message prepared with official links

## Recommended public wording points
- wACP is reserve-backed by ACP
- reserve proof is public
- PancakeSwap pair is official
- liquidity is staged, not infinite
- bridge/redemption availability depends on live system health

## Red lines
Abort or pause if:
- reserve proof becomes stale or unhealthy
- reserve falls below planned supply envelope
- price target has not been agreed
- LP wallet is missing gas or paired stablecoin
- post-mint verification fails

## Final stance
The reserve is there.
The pair is there.
The bridge is there.
What matters now is discipline: mint cleanly, LP partially, verify everything, then publish.