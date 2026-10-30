> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# PancakeSwap wACP liquidity

> **Primary playbook (V3 Stage A/B/C):** [WACP_LIQUIDITY_V3_PLAYBOOK.md](./WACP_LIQUIDITY_V3_PLAYBOOK.md).  
> This page retains **V2 bootstrap context** and historical references.

## Purpose
This document covers the DEX side after the ACP <-> BSC rail is already working live.
It is about how to scale `wACP` liquidity without doing something stupid with reserve-backed inventory.

## Current live bridge context as of 2026-05-07

### Contracts
- `WACP`: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- `BridgeGateway`: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`
- `ACP reserve`: `acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz`

### Runtime
- bridge enabled
- bridge not paused
- `dry_run=false`
- `BRIDGE_ACP_CONFIRMATIONS=1`
- BSC confirmation target from public status: `18`
- reverse `BSC -> ACP` path is live

### Live market references
- pair: `wACP / USDT`
- pair address: `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601`
- pool URL: <https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601>
- swap URL: <https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>
- initial liquidity bootstrap tx: `0x82458ec2b17e5aa58201a625169e493bb5ce8159487d66846906d9de69587503`
- first swap buy tx: `0xe6b867346d6acfdef7e0a34c457dd48c9bf572c7e0aa94224c705dc83c1a504c`
- first swap sell tx: `0x02ff5659d584aabf7bfe19c508c7673ba449ff89c1df07069cc272a6a8ab6795`

### Reserve posture
From live reserve proof on 2026-05-07:
- reserve: about `100999.994999 ACP`
- current total supply: `1 wACP`
- reserve health: `healthy`
- backing ratio: about `100999.994999`

## What the next liquidity step actually means
The bridge can already mint `wACP`, and the pair already exists.
So the next step is not “create a market from zero”.
The next step is to scale inventory and liquidity in a controlled order:
1. reserve stays healthy
2. mint inventory deliberately
3. LP only part of that inventory
4. keep the rest under treasury control

## Required preconditions before meaningful LP expansion
1. Reserve proof is still healthy right before mint and right after mint.
2. The operator wallet has enough `BNB` for gas.
3. The operator wallet has enough `USDT` for the paired side.
4. The chosen LP wallet already holds the minted `wACP` inventory.
5. The initial price target is decided explicitly.
6. Andrew approves the actual mint and LP amounts.

## Recommended operator flow for the `100000 wACP` plan

### 1. Confirm reserve headroom
Check live endpoint:
- <https://ancap.cloud/api/v1/wacp/reserve-proof>

The reserve must remain above the intended redeemable supply after mint.
With current live numbers, a `100000 wACP` mint is feasible in principle.

### 2. Mint to treasury, not directly to LP
Mint `100000 wACP` to the treasury / operator wallet first.
That gives clean separation between:
- supply creation
- reserve verification
- LP sizing

### 3. Re-check supply and reserve immediately
After mint:
- verify `totalSupply`
- verify reserve proof still reads healthy
- verify bridge status still reads enabled / not paused
- verify treasury wallet `balanceOf` is exactly what was intended

### 4. Decide LP depth from price, not from emotion
Do not dump the whole minted stack into liquidity.
Decide in advance:
- starting price in `USDT per wACP`
- how many `wACP` go into LP
- how many `USDT` go into LP
- how much inventory stays outside LP

### 5. Add liquidity on PancakeSwap V2
Operator sequence:
1. connect BSC wallet
2. open the pool URL or Liquidity page
3. import `wACP` if needed
4. choose official BSC `USDT`
5. approve both tokens if prompted
6. add the chosen initial tranche
7. save tx hashes and updated pair references

### 6. Post-LP verification
Run small tests:
- `wACP -> USDT`
- `USDT -> wACP`

Then confirm:
- routing works
- slippage is not insane
- displayed token metadata is acceptable
- pair link remains stable and shareable

## LP policy recommendation
### Bad idea
- mint `100000 wACP`
- LP all `100000`
- hope price discovery figures itself out

### Good idea
- mint `100000 wACP`
- LP a smaller controlled tranche
- keep the majority of inventory outside LP initially
- deepen liquidity only after observing market behavior

## What should be published publicly after execution
At minimum publish:
- official contract address
- official pair address
- reserve proof URL
- pair URL
- swap URL
- note that liquidity is still staged and may remain shallow
- note that bridge operators can pause the system during incidents
- note that redemption depends on reserve and bridge availability

## Operational risks
- shallow LP causes violent price movement
- wrong starting price creates instant distortion
- over-LPing treasury inventory removes flexibility
- stale reserve proof destroys trust fast
- metadata/logo lag on external surfaces can confuse users

## Bottom line
Current infra is good enough to execute the `100000 wACP` plan.
The safe order is:
- reserve
- mint
- verify
- partial LP
- publish

Anything else is asking for avoidable damage.