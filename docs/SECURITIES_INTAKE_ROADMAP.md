> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP — Securities Intake Roadmap

> Status: planned track | Added: 2026-09-06  
> Goal: accept **securities** (ценные бумаги), **promissory notes** (векселя), and **shares/equity** (акции) as collateral, settlement instruments, and org treasury assets — with ACP as the accounting and settlement rail.  
> Source of truth links: `MASTER_ROADMAP.md`, `PRODUCTION_ROADMAP.md`  
> Related: org identity / employee verification, commerce (`docs/ANCAP_COMMERCE_ROADMAP.md`), compliance (`docs/COMPLIANCE_ONRAMP_MATRIX.md`), mobile NFC step-up (planned Biohax implant factor)

## Product thesis

ANCAP already settles ACP workflows, invoices, and bridge rails. The next capital layer is **instrument intake**: companies and verified members can deposit or pledge traditional paper / dematerialized instruments; ANCAP records custody status, valuation, and ACP-denominated settlement intents without becoming a full exchange on day one.

**Non-goals (v1):** public secondary trading venue, retail brokerage license productization, automatic legal enforceability in every jurisdiction.

**Goals (v1–v2):** intake → verify → custody/escrow register → haircut valuation → ACP credit / collateral lock → audit trail.

## Instrument classes

| Class | RU | v1 scope | Notes |
|-------|----|----------|--------|
| Equity / shares | Акции | Private / closely held share certificates + digitized registry entries | ISIN optional; org-issued preferred |
| Promissory notes | Векселя | Simple / transfer notes with issuer, payee, face, maturity, jurisdiction | Paper scan + structured fields |
| Broader securities | Ценные бумаги | Bonds / units as **metadata + custody stub** first | Expand after note+equity MVP |
| Tokenized wrappers | — | Later: wACP-linked receipt NFTs / on-chain attestations | Not required for intake MVP |

## Trust & compliance gates

1. **Org verification** — only verified orgs (owner/admin) can open an intake vault; ties to `org_identity` / employee verification.
2. **KYC/KYB** — issuer and depositor identity snapshots; jurisdiction flags.
3. **Instrument authenticity** — dual control: document hash + human/compliance review (and later registrar APIs).
4. **Custody model** — explicit: *register-only* vs *physical custody partner* vs *dematerialized CSD link*.
5. **Haircut & risk** — instrument-type haircuts, concentration limits, maturity discounts for notes.
6. **Audit** — immutable intake events, status transitions, reviewer IDs (reuse org audit patterns).

## Phased delivery

### Phase S0 — Spec & domain (docs + schemas) `[x]`

- Domain glossary: Instrument, IntakeRequest, CustodyPosition, ValuationSnapshot, Pledge, MaturityEvent.
- Legal/product memo: what ANCAP promises vs third-party custodian.
- Pydantic schemas in `app/schemas/securities.py` (no router-local models).
- Status enum: `draft → submitted → under_review → accepted → pledged → matured/settled → rejected/returned`.

### Phase S1 — Data model & API MVP `[~]`

- Tables (Alembic `058`): `securities_instruments`, `securities_intake_requests`, `securities_custody_positions` (valuations/events deferred).
- Fields (minimum):
  - instrument: `type` (`equity` \| `promissory_note` \| `other_security`), `isin`?, `issuer_name`, `jurisdiction`, `face_amount`, `currency`, `maturity_at`?, `share_count`?, `document_hash`, `metadata_json`
  - intake: `org_id`, `submitted_by`, `status`, `reviewer_id`, `rejection_reason`
  - custody: `location` (`register_only` \| `partner` \| `vault`), `custodian_ref`
- API (auth + org role gated) under `/organizations/{org_id}/securities/*`:
  - `POST/GET .../intake`, `GET .../intake/{id}`, `POST .../intake/{id}/submit`, `POST .../intake/{id}/review`, `GET .../positions`, `GET .../summary`
- Document upload: hash-only store first (object storage path + SHA-256); no public URLs without auth.

### Phase S2 — Ops UI & merchant/treasury UX `[ ]`

- Web: org **Treasury → Securities** desk (list, intake form, status timeline).
- Promissory note form: drawer, payee, amount, currency, issue/maturity dates, place of payment, endorsement chain (JSON).
- Equity form: issuer, class, share count, par/nominal, certificate id / registry id.
- Admin review queue + dual-control approve for amounts above threshold.
- Receipts: PDF/JSON proof of intake acceptance (link into Proof Center patterns).

### Phase S3 — Valuation, haircut, ACP collateral `[ ]`

- Valuation service: manual mark + optional oracle adapter stub.
- Haircut table by instrument type / maturity bucket.
- `POST /v1/securities/positions/{id}/pledge` → lock position → mint **ACP collateral credit** (ledger hold, not free spend) for workflow escrow / invoice guarantee.
- Release / partial release on maturity or admin unwind.
- Risk alerts: concentration, stale valuation, overdue notes.

### Phase S4 — Partner custody & registrars `[ ]`

- Custodian adapter interface (`CustodyProvider`): register, confirm, recall.
- Optional CSD / registrar connectors (jurisdiction-specific; feature-flagged).
- Mobile: read-only positions in wallet (org-linked device); step-up via PIN / biometrics / NFC Biohax for high-value pledge confirmations.

### Phase S5 — Ecosystem (economy + cyber) `[ ]`

- Settlement intents denominated in ACP against pledged instruments.
- Cross-org note discounting marketplace (**invite-only**, compliance-gated) — after S3 stable.
- Attestations: signed custody receipts for auditors; optional on-chain hash anchor.
- Cyber: document malware scan, signed uploads, retention policy, SOC-style access logs.

## Suggested sequencing vs current priorities

| When | Why |
|------|-----|
| After ACP checkout + org identity baseline | Need verified orgs and stable ledger |
| Parallel with Business treasury UI | Same UX surface (`/treasury`) |
| Before public securities marketplace | Intake/custody must be trusted first |

Insert as **Priority R9 / Phase S** in master “Next priorities” — does not block mobile MASVS or commerce days 61–90 completion.

## Acceptance criteria (MVP = S1+S2)

- [ ] Org admin can create intake for **promissory note** and **equity**
- [ ] Document hash stored; raw file not world-readable
- [ ] Status machine enforced server-side
- [ ] Admin can accept/reject with audit event
- [ ] List/filter instruments by org and type
- [ ] Docs + compliance matrix row for “securities intake (register-only)”
- [ ] Targeted pytest coverage for schema + status transitions

## Explicit risks

- Regulatory: may require licenses if offering custody or investment services — keep v1 as **register + escrow orchestration** with clear T&Cs.
- Fraud: forged notes/certificates — mandatory review + dual control.
- Valuation: illiquid private equity — conservative haircuts; no retail LTV marketing.
- Data: PII and corporate secrets in uploads — encryption at rest, org ACL only.

## Open decisions (record when resolved)

1. First jurisdiction focus (EU / CH / other).
2. In-house register-only vs named custody partner for v1.
3. Whether ACP collateral credit is spendable or escrow-only (recommend **escrow-only** first).
