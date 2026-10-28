# ANCAP Commerce & Agent Roadmap (90 days)

> Source: Commerce + AI Agents strategic plan | Updated: 2026-06-10  
> Execution priority remains **`MASTER_ROADMAP.md`**; this document is the commerce track detail.

## Positioning

**ANCAP = AI-workflow commerce + crypto/stablecoin payments + proof receipts + marketplace + developer/MCP API**

## Shipped in this track (repo)

### ANCAP Pay (`/v1/pay`, `/v1/merchant`)
- Payment links, invoices, credits checkout, merchant dashboard, CSV export
- Webhook event: `merchant.payment.captured`

### Top-up & trust
- `/buy-acp`, `/wallet/top-up` → Stripe credits
- `/explorer`, `/status`, `/reserves` (stub)

### Workflow Store 2.0
- Bundles: `compliance-pack`, `growth-pro-pack`, `merchant-qr-pack`

### Claim codes
- `POST /v1/claim-codes/create`, `POST /v1/claim-codes/redeem`, UI `/claim`

### Developer / agents
- MCP server: `mcp-server/ancap_mcp_server.py`, docs `/mcp`
- Paid API hardening: `GET /paid-api/challenge`, `POST /paid-api/settle`, `POST /paid-api/consume`
- Payment scanner: `POST /payment-scanner/parse` (manual confirm required)

### Site map
`/pay`, `/invoices`, `/merchant`, `/claim`, `/mcp`, `/reserves`, `/workflow-store`, `/creators`, `/business`, `/compliance`

## Remaining scale items (61–90)

- AI Payment Scanner full UX (camera/OCR)
- Embedded wallet Simple/Advanced modes (partner eval: Privy/CDP/Circle)
- Business/Treasury approvals + batch payouts
- Full reserves dashboard + monthly transparency report
- Mobile wallet production release (MASTER_ROADMAP R5)

## Success metrics (90 days)

| Metric | Target |
|--------|--------|
| Payment links created | 50+ |
| Active merchants | 10+ |
| Stripe top-up E2E | Verified live |
| MCP tool invocations | 100+/week after launch |
| Claim codes redeemed | 200+ |

See also: `docs/COMPLIANCE_ONRAMP_MATRIX.md`, `ROADMAP-MONETIZATION.md`.

## Beyond 90 days — Securities intake

Capital-layer follow-on: accept securities, promissory notes, and equity shares into org treasury / ACP collateral escrow.

Full plan: [docs/SECURITIES_INTAKE_ROADMAP.md](SECURITIES_INTAKE_ROADMAP.md) (Master priority **R9**, phases S0–S5).


## Beyond 90 days - Orbital datacenters + full decentralization

Long-horizon infra:

1. **R11 — Orbital ANCAP datacenters:** SpaceX-path encrypted satellite edge servers → future **ANCAP datacenters in space** (sealed constellation). Plan: [docs/SPACEX_SATELLITE_ENCRYPTED_SERVERS_ROADMAP.md](SPACEX_SATELLITE_ENCRYPTED_SERVERS_ROADMAP.md) (phases X0–X7).
2. **R14 — Full decentralization:** multi-operator ACP mesh, federated APIs, attested edge, sovereignty exit. Plan: [docs/FULL_DECENTRALIZATION_ROADMAP.md](FULL_DECENTRALIZATION_ROADMAP.md) (phases D0–D5).

Neither blocks near-term commerce polish or Phase 6 mobile.



## Paid API challenge signature update — 2026-10-28

`GET /v1/paid-api/challenge` advertises `signature_algorithm: "hmac-sha256"`.
Clients must sign the exact UTF-8 `signature_input` with their API key as the
HMAC key and submit the lowercase 64-character hexadecimal digest to
`POST /v1/paid-api/settle`, together with the original challenge ID, nonce and
product slug. Do not log the key or signature. For example:

```python
signature = hmac.new(
    api_key.encode("utf-8"),
    challenge["signature_input"].encode("utf-8"),
    hashlib.sha256,
).hexdigest()
```

The old SHA-256 of a secret-prefixed string is no longer accepted. Pending
in-memory challenges have a 180-second lifetime; clients should request a new
challenge after an upgrade. This update does not execute a workflow or establish
payment by itself; existing consumption/authorization rules remain in force.
