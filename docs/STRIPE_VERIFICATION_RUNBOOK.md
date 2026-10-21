# Stripe Verification Runbook

Purpose: close `MASTER_ROADMAP.md` item **4.1 Stripe / fiat payment gateway** honestly.

Use this runbook when the repo-side Stripe adapter is already deployed and you need to verify the remaining external/manual closure work:
- a real Stripe PaymentIntent can be confirmed end-to-end;
- webhook delivery reaches `POST /v1/webhooks/stripe`;
- ANCAP credits are captured into the user's ledger;
- saved-card reuse works against a real/test Stripe customer, not only mocks.

This runbook does **not** replace the repo tests. It covers the manual verification gap that CI and mocked API tests cannot prove.

## Current truth

Already true in repo:
- Stripe intent create / poll / webhook / saved-method surfaces exist;
- unsupported currencies fail closed (`USD` only until a real FX quote exists);
- unconfigured Stripe env fails closed with `503`;
- webhook events are signature-verified and deduplicated;
- polling can sync a succeeded Stripe PaymentIntent into captured ANCAP credits if webhook delivery is delayed.

Still required before roadmap item 4.1 can be marked done:
- verified webhook delivery for a real/test Stripe checkout;
- verified saved-card reuse on a real/test Stripe customer.

Important: **poll fallback is not enough to close the roadmap item**. If `GET /v1/payments/stripe/intents/{id}` captures credits only because polling saw `status=succeeded` while webhook delivery never arrived, treat that as useful resilience proof, not final closure.

## Preconditions

1. Stripe adapter env vars are configured outside git:
   - `STRIPE_SECRET_KEY`
   - `STRIPE_PUBLISHABLE_KEY`
   - `STRIPE_WEBHOOK_SECRET`
   - `STRIPE_API_BASE` must remain `https://api.stripe.com/v1` in production.
     Redirects and alternate hosts are rejected before sending the secret.
     Development/test loopback `/v1` mocks require the explicit
     `STRIPE_ALLOW_LOCAL_TEST_API=true` setting; production ignores that override.

   Production path: put the three values in GitHub repo secrets with those names. Deploy (`Deploy ancap.cloud`) writes them into the host `.env` and recreates `api`. Webhook endpoint to register in Stripe Dashboard / CLI:

   `https://ancap.cloud/api/v1/webhooks/stripe`

   Events: `payment_intent.succeeded`, `payment_intent.payment_failed`, `payment_intent.canceled`.
2. Database migrations are current:
   - `docker compose -f docker-compose.prod.yml exec -T api alembic upgrade head`
3. Target stack is healthy:
   - `GET /api/v1/system/health` -> `200`
4. You have a test user account that can open `/wallet/credits`.
5. You have a webhook delivery path:
   - either a public reachable ANCAP environment;
   - or Stripe CLI forwarding to a local/prod-like endpoint.

## Recommended verification order

Do these in order:
1. New-card checkout with webhook credit capture
2. Saved-card listing / reuse checkout
3. Negative-path spot checks
4. Evidence capture and roadmap truth update

## A. New-card checkout with webhook credit capture

### 1) Confirm Stripe config is really active

Expected behavior before paying:
- `POST /v1/payments/stripe/intent` returns `201`, not `503`
- response contains:
  - ANCAP `item.id`
  - `stripe.payment_intent_id`
  - `stripe.client_secret`
  - supported currency (`USD` only until a real FX quote exists)

Useful surfaces:
- UI: `/wallet/credits`
- API: `POST /v1/payments/stripe/intent`
- API: `GET /v1/payments/stripe/intents/{intent_id}`

### 2) Create a fresh top-up intent

Through UI or API, create a Stripe checkout for a known package such as `launch-credits`.

Record:
- ANCAP payment intent id
- Stripe PaymentIntent id
- package slug
- quoted fiat amount/currency
- user id/email used for the test

### 3) Complete the card payment in Stripe

Use Stripe test-mode cards unless you are intentionally doing a live-money verification.

Minimum recommended test-mode checks:
- successful card payment
- 3DS / authentication-required card if your Stripe setup may trigger it

Do **not** store card numbers in repo docs, tickets, or memory files beyond Stripe's public test-card references.

### 4) Verify webhook delivery reached ANCAP

Success criteria:
- Stripe shows successful delivery for `payment_intent.succeeded`
- `POST /v1/webhooks/stripe` accepts the event
- ANCAP payment intent moves to `captured`
- user ledger balance increases by the expected ACP credit amount

Check all of these:
- Stripe dashboard or Stripe CLI event log shows delivered webhook
- `GET /v1/payments/stripe/intents/{intent_id}` returns:
  - `item.status == "captured"`
  - `credited == true`
- `provider_payload` includes Stripe status/event metadata
  - webhook path should show `stripe_last_event_id` as a real Stripe event id such as `evt_...`
  - webhook path should also include `stripe_last_event_at`
  - poll fallback path will show `stripe_last_event_id == "stripe:poll"`
- wallet UI (`/wallet/credits`) shows the same distinction in the Stripe panel under `Settlement signal`, and now also surfaces a separate `Verification status` line so operators can see at a glance whether the run is `webhook delivery confirmed`, `live webhook verification still open`, or still awaiting terminal evidence
- the same Stripe panel now also surfaces `Payment method evidence` (`saved card` vs `new card`, plus requested saved-method id / save-for-reuse flag when present) so manual runs can prove whether the test exercised saved-card reuse or fresh-card entry without relying only on operator memory
- user ledger balance increased by the package credit amount

### 5) Distinguish webhook success from poll fallback

If credits appear only after manually polling the ANCAP intent and there is no proof that Stripe delivered `payment_intent.succeeded` to the webhook endpoint:
- mark webhook delivery as **not yet verified**
- do not close roadmap item 4.1
- keep the run as partial progress only
- treat UI/API evidence that says `Settlement signal: poll fallback`, `Verification status: live webhook verification still open`, or `stripe_last_event_id == "stripe:poll"` as explicit proof that you still have a webhook-delivery gap

## B. Saved-card reuse verification

After a successful first payment with `save_payment_method=true`:

1. Call `GET /v1/payments/methods` or reopen the wallet credits UI.
2. Confirm a reusable saved card appears for the same authenticated user.
3. Start a second Stripe top-up using that saved payment method.
4. Confirm the second payment reaches terminal success.
5. Confirm ANCAP credits are captured again.

Success criteria:
- saved card is listed through ANCAP
- checkout can reuse it without entering a fresh card
- Stripe/ANCAP status reaches success/captured
- ledger balance increases by the second package credit amount too

## C. Negative-path spot checks

Do at least these quick spot checks while the environment is available:

1. Unsupported currency stays fail-closed
   - creating `GBP` intent returns `400`
2. Webhook secret mismatch stays fail-closed
   - invalid signature is rejected
3. Foreign saved payment method is rejected
   - ANCAP must not let one user charge another customer's saved method

These are already covered by repo tests, but one quick live sanity check helps catch environment drift.

## Evidence to capture

Capture evidence **without storing secrets**.

Use `docs/STRIPE_VERIFICATION_EVIDENCE_TEMPLATE.md` as the copy-ready packet for the current run.

To bootstrap a dated working copy without hand-editing the template header each time, run:
- `python scripts/generate_stripe_verification_packet.py`
- optional Windows launcher-only equivalent: `py -3 scripts/generate_stripe_verification_packet.py`
- optional custom output example: `python scripts/generate_stripe_verification_packet.py --date-label 2026-06-01 --operator ARDO --environment "local prod-like"`

The generator writes a dated markdown packet (default: `docs/stripe-verification-YYYY-MM-DD.md`) from the checked-in template, pre-fills round metadata fields you provide on the command line, appends bootstrap metadata so the packet itself records which template/repo state produced it, and refreshes the stable alias `docs/stripe-verification-latest.md` by default so the newest packet has a fixed handoff path. Pass `--no-write-latest-alias` if you intentionally want to create a dated packet without touching that stable alias.

After the packet is filled, run `python scripts/check_stripe_verification_packet.py docs/stripe-verification-YYYY-MM-DD.md` (or omit the path to check `docs/stripe-verification-latest.md`) so the final closure claim is validated against the packet contract instead of depending only on narrative notes.

Record:
- environment used (local prod-like / staging / production)
- verification date/time
- package slug
- fiat amount/currency
- ACP credit amount
- ANCAP payment intent id
- Stripe PaymentIntent id
- Stripe webhook event id
- whether webhook delivery succeeded
- whether poll fallback was needed
- whether saved-card reuse succeeded
- ledger balance before/after
- any failure mode seen

Acceptable evidence examples:
- redacted screenshots from Stripe dashboard delivery log
- ANCAP API JSON showing `captured` / `credited: true`
- wallet UI screenshot of the Stripe panel showing `Settlement signal: webhook` plus `Verification status: webhook delivery confirmed` for the successful run (or `poll fallback` plus `Verification status: live webhook verification still open` when documenting an incomplete webhook-verification attempt)
- wallet UI/API evidence that also shows `Payment method evidence: saved card` (or `new card`) plus the saved-method id/save-for-reuse flag when you need to prove which path the run exercised
- redacted ledger-balance before/after snapshots
- operator note naming the saved card brand/last4 only

## Done definition for roadmap item 4.1

Only mark **4.1 Stripe / fiat payment gateway** done when both are true:
- new-card checkout was verified end-to-end with confirmed webhook delivery and captured ANCAP credits;
- saved-card reuse was verified end-to-end on the same adapter slice.

If either one is missing, keep status `[~]` and describe the remaining blocker explicitly.

## Troubleshooting

### Intent creation returns 503
- Stripe env vars are missing or not loaded into the API runtime.

### Stripe payment succeeds but ANCAP never captures
- inspect webhook delivery first;
- if Stripe shows no successful webhook delivery, fix reachability/signature/secret mismatch before calling the item done.

### ANCAP captures only after poll
- poll fallback works, but webhook verification is still incomplete.

### No saved cards appear after first payment
- check whether the first intent was created with `save_payment_method=true`;
- inspect Stripe customer/payment-method attachment for the authenticated user.

## Suggested follow-through after a successful run

Once this runbook is completed successfully:
1. save the filled packet as a dated copy of `docs/STRIPE_VERIFICATION_EVIDENCE_TEMPLATE.md` (the generator's default stable alias `docs/stripe-verification-latest.md` can point at the newest filled packet, but keep the dated copy as the evidence-of-record);
2. run `python scripts/check_stripe_verification_packet.py docs/stripe-verification-YYYY-MM-DD.md` and require an exit code `0` / `Closure ready: yes` before claiming roadmap closure;
3. update `MASTER_ROADMAP.md` item 4.1 with the real verification date and evidence summary;
4. update `docs/STATUS_MATRIX.md` so the monetization section no longer lists live Stripe verification as open;
5. keep raw secrets and full client secrets out of docs, memory, tickets, and chat.
