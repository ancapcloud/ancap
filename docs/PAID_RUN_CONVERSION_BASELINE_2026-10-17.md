# Paid-run conversion baseline — 2026-10-17

Stabilization P2 item: measure discovery → preview → funded run → receipt → repeat-run.

## Funnel definition

| Step | Signal | Source |
|------|--------|--------|
| Discovery | workflow catalog / discovery shortlist view | frontend `/ai/workflows`, discovery APIs |
| Preview | quote or estimated ACP cost shown | workflow preview / store templates |
| Funded run | confirmed ACP ledger debit linked to run_id (including later failed runs) | `llm_usage_events`, workflow run rows |
| Receipt | proof / receipt id returned to user | workflow ops receipt / payment receipt |
| Repeat-run | second funded run by same user within 7d | run table grouped by user_id |

## How to measure (ops)

1. Export last 14 days of workflow runs with payment status from admin/analytics (or SQL against run + ledger tables).
2. Compute step conversion rates; record in this file under “Snapshot”.
3. Acceptance for product work: at least one end-to-end ACP-funded run with verifiable receipt in production (already demonstrated historically; keep measuring weekly).

## Snapshot

- Date: 2026-10-17
- Environment: production measurement not re-pulled this session
- Baseline method locked as above
- Next engineering focus after mobile store gates: failure/retry UX copy from real support tickets, then deposit-watcher soak (`FF_SWAP_DEPOSIT_WATCHER`)

## Related

- Deposit watcher shadow mode: `app/services/swap_tron_deposit_watcher.py` (default off)
- Smart Pay ACP route broadcast helper: `ancap-mobile/.../lib/smart-pay-route-broadcast.ts`

## Measurement corrections from engineering audit

This is a proposed event/source mapping, not a measured production baseline.
Keep `funded`, `started`, `succeeded`, `receipt available`, `receipt viewed` and
`repeat funded` separate. A paid run that fails still belongs in the funded
cohort; filtering it out inflates conversion. Receipt availability does not prove
that a user viewed it. Define run/user identity, dedupe keys, denominators and
conversion windows before aggregation. A seven-day repeat cohort must have a
full seven days of follow-up; exclude immature cohorts or mark them censored.
No production conversion percentages or performance improvement are claimed.
