> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# PancakeSwap listing playbook for wACP

## Important reality first
Getting wACP visible and usable on PancakeSwap is **not** one single button.

There are 3 separate layers:
1. **Token exists on BNB Smart Chain**
2. **Trading pair exists and has liquidity**
3. **Token metadata / logo / discoverability are added in PancakeSwap-related surfaces**

Also:
- being tradable != being featured on the PancakeSwap home page
- the PancakeSwap home page is curated; you do **not** automatically get homepage placement just because a pair exists
- the minimum practical goal is: **wACP contract verified + pair live + liquidity seeded + token metadata submitted**
- CoinGecko listing (separate from PancakeSwap): see [COINGECKO_LISTING_PLAYBOOK.md](./COINGECKO_LISTING_PLAYBOOK.md) — submit as **wACP**, never as ticker `ACP` (already taken)

---

## What must be true before you touch PancakeSwap

Do **not** call it an official market launch before all of this is true:
- wACP mainnet contract deployed on **BSC mainnet**
- wACP contract verified on **BscScan**
- bridge / gateway contracts verified on **BscScan**
- reserve proof endpoint live with real snapshot-backed reserve balance
- reserve docs live
- risk docs live
- multisig admin configured
- pause tested
- mint / burn / redeem tested end-to-end
- duplicate protection tested
- operational runbook written

Current reality: a technical PancakeSwap bootstrap pair already exists. That is useful, but it is **not** the same as full trust maturity.

---

## Recommended market structure (2026+)

**Current state:** V2 bootstrap pair is live (smoke / reference). **New scarce liquidity** goes to **PancakeSwap V3** concentrated `wACP / USDT` per [WACP_LIQUIDITY_V3_PLAYBOOK.md](./WACP_LIQUIDITY_V3_PLAYBOOK.md).

- **Primary venue:** PancakeSwap V3 (Stage A/B/C)
- **Canonical reference:** PancakeSwap V2 pair `0xF391…1601` — keep thin
- **Quote:** `wACP / USDT` (not WBNB first)
- **Infinity:** later, after sustained V3 volume

Avoid:
- pouring scarce USDT into fat V2 full-range LP while V3 is active
- `wACP / WBNB` as the first deep market
- minting wACP directly into any pool

---

## Exact checklist of assets you must prepare

Before submission, prepare this pack:

### Contract data
- wACP contract address
- chainId = `56`
- token name = `Wrapped ACP`
- token symbol = `wACP`
- decimals = `18`
- deploy tx hash
- verification link on BscScan

### Project links
- website: `https://ancap.cloud`
- docs root: `https://ancap.cloud/docs/wacp`
- bridge docs: `https://ancap.cloud/docs/wacp/bridge`
- reserve docs: `https://ancap.cloud/docs/wacp/reserve`
- risk docs: `https://ancap.cloud/docs/wacp/risks`
- contracts docs: `https://ancap.cloud/docs/wacp/contracts`

### Branding pack
- square logo PNG
- transparent background preferred
- at least `200x200`, better `512x512` or `1024x1024`
- ticker exactly `wACP`
- short token description

### Trust / ops pack
- reserve address
- reserve proof endpoint URL
- bridge status endpoint URL
- multisig admin description
- emergency pause policy summary
- public warning that wACP is wrapped and bridge-backed

---

## What you actually do step by step

## Step 1 — Finalize and verify contracts
You need:
- deployed **wACP** contract on BSC mainnet
- verified source on **BscScan**
- if bridge/gateway contracts are user-relevant, verify them too

What to do:
1. Deploy final production wACP contract
2. Verify source code on BscScan
3. Save the contract link
4. Confirm `name`, `symbol`, `decimals`, `totalSupply` read correctly on-chain

Do not continue if verification is missing.

---

## Step 2 — Publish docs pages
Before liquidity, make these pages public on `ancap.cloud`:
- `/docs/wacp`
- `/docs/wacp/bridge`
- `/docs/wacp/reserve`
- `/docs/wacp/risks`
- `/docs/wacp/contracts`

Each page should clearly explain:
- what wACP is
- how ACP backs it
- what risks exist
- how redemption works
- what contract addresses are official

This matters because Pancake users and reviewers will check whether the asset looks real or shady.

---

## Step 3 — Expose reserve proof publicly
Already live:
- `/api/v1/wacp/reserve-proof`

But it still needs maturity work. It should ultimately show:
- reserve address
- ACP reserve balance from snapshot-backed sourcing
- wACP total supply
- backing ratio
- status
- last updated timestamp

Current public state is intentionally `pending`.
Treat that as a blocker for calling the market officially ready, even though a small technical liquidity pair already exists.

---

## Step 4 — Create the first PancakeSwap pair
Open PancakeSwap and connect the treasury / liquidity wallet.

Recommended pair:
- `wACP / USDT`

What to do:
1. Import the wACP token by contract address
2. Select USDT on BSC as the quote asset
3. Create the pair if it does not exist yet
4. Add the first tranche of liquidity
5. Receive LP tokens
6. Decide where LP custody lives:
   - treasury wallet
   - multisig
   - locker (if you later choose to lock LP)

Important:
- start with controlled initial liquidity
- do not use the entire treasury
- document exactly how much wACP and USDT were seeded

---

## Step 5 — Confirm pair is tradable
After liquidity is added:
1. swap a small amount `USDT -> wACP`
2. swap a small amount `wACP -> USDT`
3. check price impact
4. check decimals display is correct
5. check token icon / metadata situation
6. confirm pair URL works and can be shared

Do not announce publicly until both directions succeed.

---

## Step 6 — Submit token metadata / logo support
This is the part many people confuse with “listing on PancakeSwap”.

You usually need to get token metadata into the relevant token list / asset registry used by wallets, UIs, or Pancake-related surfaces.

What to prepare for submission:
- contract address
- chain id
- token name
- symbol
- decimals
- logo file
- website
- docs
- socials if requested

Practical rule:
- find PancakeSwap’s current token list / asset submission instructions
- follow their **current** repository / form process
- submit **only after** the pair is live and contract is verified

Because this process changes over time, always use the current official PancakeSwap docs / GitHub links rather than old tutorials.

---

## Step 7 — Ask for discoverability, not “homepage placement”
If by “add to PancakeSwap home page” you mean “make the project visible to users”, then the realistic asks are:
- token metadata inclusion
- pair discoverability
- logo rendering
- official docs linked from your channels

If you literally mean featured placement on PancakeSwap’s homepage:
- that is editorial / BD / marketing territory
- not automatic
- usually requires traction, credibility, volume, or direct business development contact

So the correct order is:
1. make token safe and real
2. make pair live
3. make metadata discoverable
4. only then try for ecosystem visibility / featuring

---

## Step 8 — Publish your own canonical links
Once live, publish one canonical post/page with:
- official wACP contract address
- official PancakeSwap pair link
- reserve proof link
- risk docs link
- warning against fake tokens

This reduces spoofing risk.

---

## What you personally should do next, in order

### If contracts are NOT final yet
1. Finish wACP production contract
2. Set multisig admin / pause roles
3. Verify on BscScan
4. Finish reserve proof API
5. Publish docs pages
6. Test mint / redeem / pause / duplicate protection
7. Then come back to PancakeSwap

### If contracts ARE final and verified already
1. Prepare logo + metadata pack
2. Publish docs pages publicly
3. Make reserve proof public and snapshot-backed
4. Open PancakeSwap V2
5. Create `wACP / USDT` pair
6. Add initial liquidity
7. Test both swap directions

### What is already done
- pair live: `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601`
- liquidity tx: `0x82458ec2b17e5aa58201a625169e493bb5ce8159487d66846906d9de69587503`
- first buy tx: `0xe6b867346d6acfdef7e0a34c457dd48c9bf572c7e0aa94224c705dc83c1a504c`
- first sell tx: `0x02ff5659d584aabf7bfe19c508c7673ba449ff89c1df07069cc272a6a8ab6795`
- official swap URL: `https://pancakeswap.finance/swap?inputCurrency=0x55d398326f99059fF775485246999027B3197955&outputCurrency=0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
8. Submit token metadata through PancakeSwap’s current official process
9. Publish official contract + pair links on ancap.cloud and Telegram

---

## Minimal submission pack template

Use this as your working draft:

- Project name: ANCAP
- Token name: Wrapped ACP
- Symbol: wACP
- Chain: BNB Smart Chain
- Chain ID: 56
- Contract: `0x...`
- Decimals: 18
- Website: `https://ancap.cloud`
- Docs: `https://ancap.cloud/docs/wacp`
- Reserve proof: `https://ancap.cloud/api/v1/wacp/reserve-proof`
- Risks: `https://ancap.cloud/docs/wacp/risks`
- Logo PNG: `https://ancap.cloud/wacp-logo.png`
- **BscScan 32×32 SVG (required for token update form):** `https://ancap.cloud/wacp-logo-32.svg`
- Pair: `wACP/USDT`

---

## Blunt recommendation
Do **not** optimize for “getting on the PancakeSwap home page”.
Optimize for this instead:
- verified contract
- credible reserve proof
- safe bridge ops
- clean docs
- real liquidity
- clear official links

If those are done, Pancake integration becomes straightforward.
If those are not done, homepage visibility would just amplify risk.
