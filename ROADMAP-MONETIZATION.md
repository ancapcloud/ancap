> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Monetization-First Roadmap

> Status: supporting strategy note | Updated: 2026-05-25
> Last verified: 2026-05-28
> Source of truth for execution priority: `MASTER_ROADMAP.md`
> This file now serves as monetization strategy context. The first ACP-first revenue loop exists; the remaining work is monetization depth, not a greenfield monetization thesis.
> Fast status index: `docs/STATUS_MATRIX.md`

## Thesis

ANCAP should stop presenting itself mainly as an abstract AI/Web3 showcase and move toward a product that directly sells useful AI-driven crypto workflows, machine-readable proofs, and agent-to-agent paid execution.

Core formula:

**AI task -> crypto payment -> verified result -> receipt/proof -> repeat run / subscription / marketplace fee**

This keeps ANCAP in the safer zone of selling software and AI services for crypto teams and agents, instead of drifting into promises of investment returns or regulated financial products.

---

## Primary Goal

The first ACP-first revenue loop is already in place in baseline form. The current monetization goal is to deepen and de-risk it:

1. improve payment quality and conversion
2. add creator withdrawal and earnings visibility
3. add subscription and referral payout mechanics
4. deepen paid API monetization and reporting
5. add marketplace discovery and dispute/refund flows
6. keep ACP-first as the core unit while adding lower-friction adapters later where needed

---

## May 2026 Execution Plan: What To Keep, Add, And Defer

The broad product-improvement research is useful, but ANCAP should not implement every generic recommendation. The immediate monetization path is narrower:

**North Star:** weekly paid workflow GMV in ACP.

### Keep in the active roadmap

1. **Conversion and checkout clarity**
   - Make `home -> workflow -> checkout -> receipt` obvious.
   - Show price, expected output, sample report, execution time, and proof expectation before payment.
   - Track workflow view, checkout start, paid run, completion, and repeat run.

2. **ACP-first payment quality**
   - Keep ACP as the primary accounting unit.
   - Improve payment intent states: invoice, pending, confirmed, failed, receipt.
   - Avoid adding broad multi-currency support until ACP checkout is stable.

3. **Creator and seller economy**
   - Let AI agents and workflow creators define, publish, and monetize paid workflows.
   - Prioritize seller dashboard metrics: published workflows, paid runs, revenue in ACP, conversion, receipt completion.
   - ANCAP earns from marketplace take rate, premium placement, and execution fees.

4. **Proof Center as the trust layer**
   - Every paid run should produce a shareable receipt URL.
   - Receipts should include workflow slug, price snapshot, input hash, status timeline, output items, and ledger/proof metadata.
   - Make receipts readable by humans and external AI agents.

5. **Agent/API monetization**
   - Treat `/developers` as a product page, not only documentation.
   - Expose paid API endpoints, spend caps, 402-compatible payment terms, and machine-readable receipts.
   - Maintain AI-readable catalog surfaces such as `/llms.txt` and `/agent-products.json`.

6. **Telegram and X acquisition loop**
   - Use free token snapshots as the cold-traffic entry point.
   - Upsell to Token Risk Report Pro, Launch Pack, and premium workflow bundles.
   - Reward referrals after first captured paid run, not after registration.

### Add now

- AI-readable product catalog for agents.
- Sample reports for premium workflow SKUs.
- Creator workflow publishing flow.
- Seller dashboard revenue attribution.
- Public receipt/proof pages for paid runs.
- Basic funnel and revenue analytics by SKU, bundle, creator, and API endpoint.

### Defer

- Native mobile app.
- Physical product after-sales features.
- Large integration marketplace.
- Heavy A/B testing platform before traffic volume justifies it.
- Complex personalization before basic role-based journeys are polished.
- Broad multi-currency checkout before ACP payment quality is strong.

### Six-week implementation sequence

1. **Week 1: Conversion and trust**
   - Workflow cards, sample reports, checkout state, receipt expectation, public AI-readable catalog.
2. **Week 2: Creator economy MVP**
   - Create workflow, define schema, set price, publish/unpublish, seller dashboard basics.
3. **Week 3: Proof receipts**
   - Shareable receipt page, proof center indexing, machine-readable receipt schema.
4. **Week 4: Developer/API monetization**
   - Paid endpoint packaging, API key CTA, spend caps, 402-compatible response shape.
5. **Week 5: Acquisition**
   - Free token snapshot, paid report upsell, Telegram/X referral links, first-paid-run referral reward.
6. **Week 6: Scale**
   - Premium workflow ranking, creator payouts, Telegram bot-lite, revenue dashboards.

---

## Product Positioning Shift

### Move away from
- generic "AI-native capital allocation" landing language
- vague ecosystem/vision-first messaging
- marketplace abstraction before monetization exists
- low-conversion crypto ideology without concrete paid actions

### Move toward
- paid AI workflows for crypto projects
- treasury / payout / proof tooling
- listing and launch support
- agent wallet + spend controls
- paid API / MCP tooling for other agents
- proof center as trust layer

---

## Revenue Lines

### 1) Paid Workflow Runs
Examples:
- Token Listing Pack
- Crypto Launch Campaign Builder
- Telegram Growth Kit
- Airdrop / Bounty Builder
- Token Risk / Trust Report

Model:
- pay-per-run
- repeat-run discount
- subscription bundles
- enterprise packages

### 2) Campaign / Service Packages
Examples:
- 14-day launch campaign
- listing readiness package
- KOL outreach pack
- bounty campaign management

Model:
- setup fee
- campaign fee
- verification fee
- payout fee

### 3) Paid API / MCP / x402-style Agent Access
Examples:
- token risk check
- wallet risk score
- listing readiness
- campaign score
- bridge proof
- reserve status

Model:
- pay-per-call
- monthly pro plan
- enterprise limits
- marketplace/provider fee

### 4) Treasury / Payout B2B
Examples:
- payout review
- duplicate detection
- suspicious wallet detection
- approval logs
- monthly statements

Model:
- monthly plan
- per-payout fee
- premium audit logs
- custom policies

---

## MVP Scope (2-4 weeks)

## Week 1 - Money Rails + Paid Runs Foundation

### Frontend pages
- `/ai/workflows`
- `/ai/run/[template]`
- `/billing`
- `/wallet/credits`
- `/dashboard/runs`

### Backend capabilities
- workflow template registry
- create run endpoint
- cost calculation
- balance lock / reservation
- execute workflow run
- save result
- save receipt
- refund on failed run

### Data model
Create or extend entities for:
- `workflows`
- `workflow_runs`
- `run_costs`
- `credits_ledger`
- `payment_intents`
- `receipts`
- `audit_events`

### Deliverable
A signed-in user can buy and run a priced workflow and see status, result preview, and receipt.

---

## Week 2 - First 5 Sellable Workflows

### First workflow products
1. Token Listing Pack
2. Crypto Campaign Builder
3. Telegram Growth Kit
4. Airdrop / Bounty Builder
5. Token Risk Report

### Each workflow must include
- landing copy
- input form
- price
- estimated completion time
- output preview
- full result unlock
- receipt
- repeat run button

### Deliverable
ANCAP has at least 5 concrete monetizable workflow templates on the site.

---

## Week 3 - Earn / Bounty / Referral Loop

### Frontend pages
- `/earn`
- `/campaigns`
- `/referrals`
- `/partners`

### Capabilities
- proof upload / proof links
- reward pools
- payout queue
- manual approval
- suspicious user flags
- referral tracking

### Monetization
- campaign setup fee
- reward pool fee
- payout fee
- verification fee
- featured placement

### Deliverable
ANCAP can attract traffic through bounty/referral loops while taking campaign and verification fees.

---

## Week 4 - Agent / API Monetization

### Frontend pages
- `/developers`
- `/developers/pricing`
- `/developers/mcp`
- `/developers/receipts`

### Capabilities
- API keys
- paid endpoints
- MCP tool descriptions
- machine-readable receipts
- webhook callbacks
- x402-compatible architecture prep

### First paid API set
- `/token-risk-report`
- `/listing-readiness`
- `/bridge-proof`
- `/campaign-score`
- `/wallet-risk`
- `/market-report`

### Deliverable
Other agents and external systems can pay ANCAP for machine-readable checks and reports.

---

## Top Priority Features (P0 -> P2)

## P0
- Paid AI Workflow Store
- Billing / Credits / ACP / wACP support
- Run history + result + cost
- Token Listing Pack Generator
- Crypto Campaign Builder
- AI Bounty Builder
- Referral cabinet
- Treasury payout approvals
- Audit receipts
- Admin margin dashboard

## P1
- MCP server for ANCAP tools
- paid API endpoints
- agent wallet limits
- curated agent marketplace
- partner / KOL CRM
- proof of reserve page
- campaign payout verification
- provider dashboard

## P2
- enterprise workspace
- private workflows
- dedicated internal deployments

---

## Recommended First Product

## ANCAP AI Crypto Launch Suite

Initial bundle:
- Token Listing Pack
- Campaign Builder
- Telegram Growth Kit
- Bounty Builder
- KOL Outreach Pack
- Token Risk Report
- Proof / Receipt Center
- Referral / Partner Cabinet
- Treasury Payouts

Why this first:
- clear buyer profile: crypto teams
- immediate perceived value
- no GPU dependency required
- can be delivered with templates, rules, APIs, and proof artifacts
- naturally monetizes via runs, packages, and B2B tools

---

## Compliance / Positioning Constraints

Avoid for now:
- promises of yield or investment returns
- staking/yield products without legal basis
- trading signals framed as guaranteed profit
- open permissionless marketplace full of junk
- launchpad securities behavior
- casino / gambling mechanics
- pump tooling

Safer early positioning:
- software tools for crypto teams
- AI workflow execution
- marketing / launch / compliance-draft / listing support
- treasury / payout review / proof / reconciliation
- agent payments and spend controls

---

## Immediate Build Order Inside Current Repo

### Phase A - Landing and navigation shift
- update homepage copy toward paid workflows and proof-based execution
- add direct CTA to workflow catalog
- add monetization roadmap doc to repo

### Phase B - Frontend workflow store shell
- add `/ai/workflows`
- add workflow cards for the first 5 products
- add pricing and proof messaging

### Phase C - Backend monetization shell
- add workflow templates API
- add create-run API
- add run receipt response shape
- connect to existing runs / tasks / listings / referrals / wallet primitives where possible

### Phase D - Billing and execution primitives
- reserve credits
- record pricing and receipts
- add run status timeline

---

## Working Principle

Do not build another vague crypto front page.
Build revenue loops first, then deepen the protocol and agent economy behind them.

If a feature does not clearly support one of these loops, it is probably not first-priority:
- pay-per-run
- campaign/service package
- agent API payment
- treasury/payout fee

---

## Current Session Execution Plan

1. Write this roadmap into the repo.
2. Reposition the homepage toward paid AI workflows and proof-backed results.
3. Add a first workflow catalog page in the frontend.
4. Then wire the page into navigation and CTA flow.
5. After that, move to backend workflow-template endpoints.
