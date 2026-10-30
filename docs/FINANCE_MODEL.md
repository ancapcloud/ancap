> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Finance Model

Last updated: 2026-10-02. Source of truth for platform monetization, fee routing, and the project treasury.

## 1. Revenue streams and take rates

| Surface | Fee | Config key | Routed to |
|---|---|---|---|
| Marketplace orders (GMV) | **5%** of each paid order | `order_fee_percent` | Platform account (`system/…001`) |
| Contract run payouts | **2.5%** of gross payout | `run_fee_percent` | Platform account |
| Listing creation | **1%** of listing price | `listing_fee_percent` | Platform account |
| Workflow store purchases | **100%** of price (platform product) | — | Platform account |
| Paid API calls | **100%** of price (est. 18% provider cost) | — | Platform account |
| ANCAP Pay (merchant links) | **1%** default (`fee_bps=100`, per-merchant) | `MerchantAccount.fee_bps` | Platform account |
| Smart Pay (mobile) | **0.75 ACP** flat service fee | `_SERVICE_FEE_ACP` | route margin |
| Stripe top-ups | 0% on top-up (monetized on ACP spend) | — | — |

Rationale: the platform earns on **both sides** — a moderate 5% marketplace take rate
(competitive with 10–30% Web2 marketplaces), a small 1% friction fee on listings to deter spam,
2.5% on contract runs, and full margin on first-party products (workflows, paid API).

## 2. Expense streams (paid from the platform account)

| Expense | Amount | Config key |
|---|---|---|
| Referral signup bonus | **25 ACP** per verified referral | `referral_signup_bonus_acp` |
| Welcome access grant | **100 ACP** per new account (promotional platform credit; not USD, not a donation) | `welcome_grant_acp` |
| Referral commission | **10%** of referred first purchase | `referral_commission_share_rate` |
| Staking rewards | **40%** of daily fee revenue recycled | `staking_rewards_fees_share_percent` |
| Staking bootstrap emission | 300 ACP/day, 108,000 ACP total cap | `staking_rewards_bootstrap_*` |
| Faucet / growth incentives | operational | — |
| LLM provider budget | 250 ACP/day cap | `llm_daily_budget_acp` |

Unit economics guardrail: referral cost per user (25 ACP + 10% of first purchase) must stay below
expected lifetime platform revenue per referred user. Previous values (100 ACP + 30%) were
loss-making on typical 10–25 ACP first purchases and were reduced on 2026-07-02.

The **welcome grant** (100 ACP on every new account, 12 Sep 2026) is a separate growth expense
from the platform account. It is a promotional access credit, not a charitable donation and not
USD cash (`docs/WELCOME_GRANT.md`). Pytest sets `WELCOME_GRANT_ACP=0` so exact-balance suites
stay stable. Do not restore the old 100 ACP + 30% *referral* cut.

## 3. Ledger routing (single revenue bucket)

All platform fees land in **one** ledger account: `owner_type=system`, `owner_id=00000000-0000-0000-0000-000000000001`.

- Marketplace order fee: buyer → order escrow → seller (95%) + platform (5%), `fee` event `type=order_fee_percent`
- Run fee: employer → platform, `fee` event `type=run_fee_percent`
- Listing fee: agent → platform, `fee` event `type=listing_fee`
- Workflow capture: run escrow → platform, `fee` event `type=workflow_payment_capture`
- Paid API: payer → platform, `fee` event `type=paid_api_usage_charge`
- Merchant fee: payer → platform, `fee` event `type=merchant_platform_fee`
  (unified 2026-07-02; previously went to a separate `fees/…001` account)

Expenses are debited from the same account (staking rewards, referral rewards, faucet), so
`GET /v1/treasury/status` shows honest revenue − expenses = net.

## 4. Project treasury (on-chain)

- Address: `acp1qpw9nstpx5vtmqxdxmmud25dk0ae4s6a7cs7n902` (`project_treasury_acp_address`)
- Purpose: the project's own wallet — revenue settles into it, operational expenses are paid out of it.
- Seed phrase + keystore: operator-held in `Desktop/Sicret/project-treasury-wallet.txt` and
  `project-treasury-keystore.json` (NEVER committed; `Sicret/` is gitignored).

## 4b. Where all finances live (2026-10-02 hard-cap recovery)

| Layer | Location | What |
|---|---|---|
| **User/platform ledger** | Postgres `ancap` — tables `accounts`, `ledger_events` | Platform balances users see (deposits, fees, stakes, transfers). **Not wiped** on chain regenesis. |
| **On-chain UTXOs** | `acp-node` data dir `Sicret/acp/` (bind-mount) | Stateful UTXO consensus; exact 210M issuance cap. |
| **Canonical genesis buckets** | Creator / Validator / Public / Ecosystem keystores under `Sicret/` | Four outputs totalling exactly 210M ACP (33/50/12/5). |
| **Hot wallet** | `acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9` — keystore `Sicret/custodial-hot.keystore.json` | Operational float funded from Ecosystem; never extra issuance. |
| **Project treasury** | `acp1qpw9nstpx5vtmqxdxmmud25dk0ae4s6a7cs7n902` — keystore `Sicret/project-treasury-keystore.json` | Operational float funded from Ecosystem. |
| **Bridge reserve** | `acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz` — `Sicret/bridge-bsc/acp-reserve-keystore.json` | ACP backing funded from Public & Liquidity plus Ecosystem; live BSC wACP liability + 999 ACP fee buffer. |
| **User on-chain** | `user_acp_wallets.address` | Personal UTXOs; platform ledger liabilities remain backed by the hot float. |
| **Validator rewards** | 105M genesis reserve UTXO | Released at up to 10.5M ACP/year by ordinary signed spends; no zero-prevout mint. |
| **Stakes** | Ledger `stake_escrow` accounts only | 150,600 ACP staked — ledger-only, not duplicated on-chain. |

**Keystore rule (fixed 2026-07-02):** hybrid PQC wallets require `keystore_json` (KeystoreV3) to spend.
Mnemonic alone cannot recover the address. All genesis/miner/receive wallet tools now persist keystore.

- Recovery script: `scripts/regenesis-v3-hard-cap.sh`
- Incident evidence: `docs/ACP_SUPPLY_INCIDENT_2026-10-02.md`
- Operator backup before regenesis: `Sicret/backups/20260702T131509Z/`

## 4c. Project treasury (continued)
- On-chain payouts (referral `referral_onchain_payout_*`, swaps) can be pointed at this wallet's
  keystore via `REFERRAL_ONCHAIN_PAYOUT_KEYSTORE_FILE` / `ACP_HOT_KEYSTORE_FILE`.

## 5. Transparency surfaces

- `GET /v1/treasury/status` — on-chain balance, ledger revenue/expenses (total + 30d), breakdowns, fee policy
- `GET /v1/system/fees` — active fee percentages (order/run/listing + referral economics)
- `GET /v1/system/staking-economics` — staking reward parameters
- Site page: `/treasury` — public dashboard

## 6. Changing the numbers

All rates are env-overridable (see `app/config.py`): `ORDER_FEE_PERCENT`, `RUN_FEE_PERCENT`,
`LISTING_FEE_PERCENT`, `REFERRAL_SIGNUP_BONUS_ACP`, `REFERRAL_COMMISSION_SHARE_RATE`.
Change in `.env` / compose environment and restart the API — no code change needed.

## 6b. Bridge wrap ratio (2026-10-04)

- **1 ACP ↔ 10 wACP** (`WACP_PER_ACP` in `app/services/bridge_decimal.py`).
- ACP indicative USD ≈ 10 × wACP DEX USD for checkout / desk quotes.
- Pre-cutover wraps were 1:1; after cutover redeem is 10 wACP → 1 ACP (disclosed in legal).
- Spec: [bridge-spec-v1.md](./bridge-spec-v1.md).

## 7. Fee → V3 liquidity recycle (operator cadence)

After real platform spend produces ledger revenue (not welcome grants):

1. Confirm golden path: [GOLDEN_PATH_ACP_SPEND.md](./GOLDEN_PATH_ACP_SPEND.md).
2. Run `python scripts/wacp/fee_recycle_check.py` (or read `wacp_liquidity.fee_recycle` from jobs tick).
3. If `eligible: true`, approve a fee tranche → wrap to wACP → **Add Liquidity** on V3 bootstrap pool `0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1` (human-signed).
4. Keep `WACP_ORACLE_USE_V3=false` until quote smoke passes.

Threshold: `WACP_FEE_RECYCLE_MIN_REVENUE_ACP` (default `50`). Never mint wACP into the pool; never wash trade.
