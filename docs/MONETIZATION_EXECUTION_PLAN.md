> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Monetization Execution Plan

## Goal

Turn ANCAP into a revenue-first AI workflow product for crypto teams:

`workflow quote -> credits/payment intent -> reserved funds -> execution -> proof bundle -> repeat/package/API upsell`

The project already has the right primitives: workflow runs, ledger accounts, receipts, proof bundles, referrals, marketplace listings, contracts, ACP wallets, and wACP bridge surfaces. The next work should tighten those primitives into paid loops instead of adding unrelated product surfaces.

## P0 Revenue Path

1. Paid Workflow Store
   - Keep the first five workflow SKUs: Token Listing Pack, Crypto Campaign Builder, Telegram Growth Kit, Airdrop/Bounty Builder, Token Risk Report.
   - Every SKU must expose a quote, input form, run status, result, receipt, and repeat action.

2. Billing Safety
   - Use `payment_intents` as the source of truth for workflow payments.
   - A ledger-credit payment reserves user credits into the workflow-run escrow account before execution.
   - A completed run captures reserved funds into the platform fee account.
   - A failed or cancelled run refunds reserved funds back to the user account.

3. Admin Revenue View
   - Track paid runs, captured revenue, refunded amount, failed payment attempts, and workflow SKU conversion.
   - Keep margin metadata on each run once external AI/provider costs are integrated.

4. Packages
   - Launch Pack: all five workflow SKUs at a bundle price.
   - Growth Pack: repeated campaign/growth runs plus proof exports.
   - Concierge Pack: manual review and custom delivery on top of generated artifacts.

5. Growth Loop
   - Referrals should reward first paid purchase, not only signup.
   - Partner codes should report clicks, attributed paid runs, captured revenue, and payable commission.

6. API Monetization
   - Meter API keys by paid endpoint usage.
   - Start with token risk, listing readiness, wallet risk, bridge proof, and campaign score endpoints.

## Implemented MVP

The current implementation now covers the full first revenue loop:

- paid workflow catalog with five crypto workflow SKUs.
- workflow runs with quotes, status, previews, result shells, receipts, repeat runs, receipt trails, and proof bundles.
- `payment_intents` as the source of truth for workflow payments and wallet credit top-ups.
- ledger-credit reservation into workflow escrow before execution.
- automatic capture into the platform fee account when a workflow completes.
- automatic refund when a reserved workflow fails or is cancelled.
- proof metadata for payment intent, reservation, capture, refund, settlement, and referral reward state.
- admin revenue summary by currency, payment status, run status, and workflow SKU.
- Launch Pack, Growth Pack, and Concierge Pack checkout with proportional allocation across workflow runs.
- wallet credit packages for prepaid workflow spend: Starter Credits, Launch Credits, and Growth Credits.
- admin top-up approval queue so users can create invoices but cannot self-credit balances.
- first-paid-workflow referral reward trigger, reusing the existing referral reward ledger and idempotency model.
- paid API catalog and `api_usage_events` metering for token risk, listing readiness, wallet risk, bridge proof, and campaign score endpoints.
- prepaid credit debits for paid API calls authenticated by `X-API-Key`.
- Billing UI now shows paid API products and recent usage; Admin overview shows pending top-up approvals.

## Remaining Production Hardening Queue

1. Payment provider integration
   - Replace admin-approved manual top-ups with processor webhooks once provider credentials are chosen.
   - Keep `payment_intents` as the same stable contract for manual, webhook, and dispute flows.

2. Admin security
   - Set `PLATFORM_ADMIN_USER_IDS` in production.
   - Add a persistent user role table if the team wants role management inside the app instead of environment allowlists.

3. API monetization depth
   - Add monthly usage exports and per-agent spend caps.
   - Add idempotency keys for expensive paid API calls where clients may retry.
   - Route paid API outputs to stronger analyzers when external provider costs are wired.

4. Revenue quality
   - Add provider cost fields to payment intents or workflow receipts.
   - Report gross revenue, estimated cost, margin, refunds, open reserved funds, and referral commission per SKU.
