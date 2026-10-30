# WebID KYC and future card issuing path

> Status: P0 shipped · P1 sandbox adapter shipped (fail-closed) | Updated: 2026-10-30  
> Partner site: [webid-solutions.com](https://webid-solutions.com/en/)

## Honest split

| Layer | Who | What it does |
|-------|-----|----------------|
| KYC / KYB | WebID (or equivalent) | Verify person / company (VideoID, CorporateID, ePassID, …) |
| Card issuing | Licensed BaaS / EMI | BIN, plastic/virtual cards, settlement |
| Apple Pay | Issuer + card network | Tokenize issued cards into Apple Wallet |

**WebID does not issue physical cards and does not enable Apple Pay by itself.**  
ANCAP soulbound `/passport` and org NFC are **not** regulated identity verification.

ANCAP remains **not a VASP** until counsel and a licensed card issuer change that posture. See [COMPLIANCE_ONRAMP_MATRIX.md](./COMPLIANCE_ONRAMP_MATRIX.md).

## Phases

### P0 — shipped

- Public waitlist: `/cards` → `POST /v1/commerce/ramp-waitlist` with `interest=physical_card_apple_pay`
- Fail-closed: `GET /v1/commerce/webid/status` → `configured=false`, `issues_cards=false`
- Env placeholders only (`WEBID_ENABLED=false`, empty credentials)

### P1 — sandbox API (repo ready, live after commercial account)

- Env: `WEBID_ENABLED`, `WEBID_API_BASE`, `WEBID_CLIENT_ID`, `WEBID_CLIENT_SECRET`, optional
  `WEBID_CREATE_PATH`, `WEBID_LIGHT_REDIRECT_BASE`, `WEBID_RETURN_URL`, `WEBID_WEBHOOK_SECRET`,
  `WEBID_PRODUCT`
- Authenticated `POST /v1/commerce/webid/session` starts an identification process (503 until configured)
- Signed `POST /v1/commerce/webid/webhook` acks status callbacks (HMAC-SHA256; 401 without secret)
- `/cards` shows live partner status via `GET /v1/commerce/webid/status`
- CorporateID path: set `WEBID_PRODUCT=CorporateID` when Gewerbe / UBO KYB is required

Without a commercial WebID account, all session/webhook paths stay fail-closed. Do not invent live KYC.

### P2 — licensed card path (counsel gate)

- Contract a European EMI / BaaS (not WebID) for plastic + Apple Pay tokenization
- Revisit “not a VASP” messaging before any “get your ANCAP card” CTA
- Link ACP spend only after issuer settlement rules are clear

## Operator checklist (outside repo)

1. Contact WebID business sales (Crypto/Web3 + CorporateID if company KYB) via [webid-solutions.com](https://webid-solutions.com/en/)
2. Receive sandbox base URL, customer id, API key / secret, webhook signing secret, light-redirect base
3. Set host env (`WEBID_ENABLED=true` + credentials); never commit secrets
4. Smoke: `GET /v1/commerce/webid/status` → `sessions_ready=true`; signed-in `POST /v1/commerce/webid/session`
5. Shortlist card issuer / BaaS separately
6. Counsel review before claiming card issuance or Apple Pay on product surfaces

## Public surfaces

| Surface | Role |
|---------|------|
| `/cards` | Waitlist + live WebID status + honesty copy |
| `GET /v1/commerce/webid/status` | Partner slot status (no secrets) |
| `POST /v1/commerce/webid/session` | Start KYC session (auth; fail-closed) |
| `POST /v1/commerce/webid/webhook` | Identification status ack (HMAC) |
| `/compliance` | Link to card waitlist |
| `/buy-acp` | Quiet link to `/cards` |
