> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Mobile — Smart QR Security Model

> Status: proposed security model | Updated: 2026-05-25
> Scope: Smart QR scan, parse, auto-swap, and pay flows on iOS + Android
> Related: `SECURITY_MODEL.md`, `SMART_QR_PAYMENT_INTENT_SCHEMA.md`, `SMART_QR_API_SPEC.md`

---

## 1. Security objective

Smart QR Pay must feel simple to users without becoming a phishing machine.

Primary security goal:
- **make scan -> parse -> pay safe enough for real money**

That means:
- no blind trust in QR payloads
- no blind trust in AI classification
- no hidden asset substitution
- no invisible fee charging
- no untracked partial execution

---

## 2. Threat model

### 2.1 Attacker goals
- trick user into paying the wrong address
- substitute token or chain
- exploit ambiguous QR payload formats
- abuse auto-swap to extract extra value via slippage/fee manipulation
- poison routing or contract metadata
- steal sensitive scan/image data
- trigger inconsistent partial payment states

### 2.2 Trust boundaries

| Zone | Trust | Notes |
|---|---|---|
| Device secure storage | High | keys remain local |
| App process after unlock | Medium | user present but UI can still be tricked |
| QR payload content | Low | fully untrusted |
| AI classifier output | Low-Medium | useful hint, never final authority |
| Routing / quote backend | Medium | must be auditable, fee-transparent |
| Public RPC / indexers / DEX data | Low-Medium | external dependencies |

---

## 3. Core security rules

1. **QR payload is untrusted input**
2. **AI output is advisory, not authoritative**
3. **User confirmation is mandatory before execution**
4. **Recipient, asset, amount, and fee must be shown explicitly**
5. **Local signing only for non-custodial path**
6. **Every step must be resumable and auditable**

---

## 4. High-risk cases to defend against

### 4.1 Address poisoning / substitution
Controls:
- validate chain-specific address format
- checksum validation for EVM
- show compact but recognizable address preview
- warn when address resembles previously seen address but differs
- never auto-replace recipient from contacts/aliases without user action

### 4.2 Token spoofing
Controls:
- allowlist supported token contracts per network
- show token symbol + contract verification badge
- unsupported/unverified contract => warning or block depending on release mode

### 4.3 Non-standard QR payload traps
Controls:
- parse known standards first
- ambiguous freeform payload => `needs_review`
- AI classified payload => force stronger warning banner
- low confidence => block auto-route generation

### 4.4 Fee manipulation
Controls:
- display ACP service fee separately
- display network gas separately
- show total source spend and delivered target amount
- signed quote with TTL
- refresh quote on expiry

### 4.5 Slippage exploitation
Controls:
- user-set max slippage
- route invalid if slippage exceeds limit
- warn on volatile route / illiquid pair
- strict quote expiry

### 4.6 Partial execution failure
Controls:
- explicit execution session states
- recovery endpoint
- tx reference persistence
- clear distinction between swap submitted vs merchant paid

---

## 5. AI-specific security constraints

### AI must never:
- sign transactions
- choose a hidden recipient
- silently infer missing destination from weak signals
- execute payment without explicit confirmation
- override deterministic parser result with weaker evidence

### AI may:
- classify freeform payloads
- extract likely network / asset / amount candidates
- extract merchant label hints from screenshot text if user consented
- propose parse candidates with confidence score

### AI output handling rules
- must be converted into canonical `PaymentIntent`
- must be schema-validated
- must carry `parseMethod = ai`
- must set `riskFlags` including `ai_classified`
- if confidence below threshold -> no quote, no payment prep

---

## 6. Privacy model

### Local-first principle
Preferred flow:
- QR decode on device
- deterministic parse on device where possible
- server only receives normalized payload text for quote/route when needed

### Photo import handling
If user scans from gallery/photo:
- decode locally first
- do not upload full image unless user explicitly consented and local decode failed
- if image upload exists later, apply:
  - size limit
  - short retention
  - no permanent storage by default
  - no training-data reuse

### Logging
Never log:
- mnemonic / seed / secrets
- full raw photo contents
- full raw private invoice images unless explicit debug mode for internal beta only
- decrypted signing material

Prefer logging:
- payload hash
- parse method
- route id
- risk flags
- anonymized failure code

---

## 7. Transaction security controls

### Confirmation screen must show
- destination address
- destination network
- destination asset
- amount to recipient
- source asset being spent
- ACP service fee
- network fee(s)
- route summary
- warnings / risk flags

### Confirmation screen must not
- hide fees inside source amount
- collapse chain/asset identity into vague labels
- skip display because parser confidence is high

---

## 8. Supported-asset release policy

### Initial release recommendation
Allow only:
- ACP
- wACP
- a very small allowlist of EVM tokens (e.g. USDT / USDC on BSC only if fully tested)

Block by default:
- arbitrary ERC-20 contracts
- unsupported chains
- cross-chain magic routes without explicit product approval

Reason:
- reduces spoofing surface
- simplifies route safety
- lowers App Store / Play review risk

---

## 9. Quote and route integrity

Every quote should include:
- quote id
- expiry timestamp
- source asset amount
- target asset amount
- ACP service fee
- gas estimate(s)
- route steps
- slippage bound

Recommended backend protections:
- sign quote payload or store immutable quote snapshot server-side
- reject execute if quote expired or altered
- attach route provenance (`dexOrRail`, source liquidity, timestamp)

---

## 10. Recovery and idempotency

Must support:
- app closed during payment
- network outage after local sign
- duplicate execute tap
- backend receipt lag

Controls:
- idempotency key for execute
- session recovery endpoint
- tx hash reconciliation
- receipt reconstruction from known txs

---

## 11. Mobile-specific controls

### iOS / Android scan safety
- require camera permission only on scanner entry
- sanitize shared/imported content
- block screenshots on sensitive confirmation states if necessary
- do not expose hidden debug parser output in production UI

### Local vault
Smart QR feature must reuse the existing wallet vault rules:
- device-only secure storage
- biometric-gated read for signing material when enabled
- no server custody of seed

---

## 12. Abuse and fraud controls

Backend should detect:
- repeated malformed payload floods
- suspicious high-frequency quote spam
- repeated execution failures on same contract / address
- contract addresses outside supported allowlist
- unusual fee/gas deviations

Optional future controls:
- known-merchant registry
- scam-address denylist
- suspicious merchant pattern scoring

---

## 13. Store / compliance positioning

To reduce review risk:
- describe feature as **non-custodial crypto wallet smart payment assistant**
- avoid “investment”, “guaranteed savings”, or misleading exchange claims
- clearly disclose third-party liquidity / bridge / swap risk
- clearly disclose custodial rails if any beta route uses operator execution

---

## 14. Security release gates

Do not ship Smart Auto-Swap Pay until all are true:

1. deterministic parser test suite is in place
2. supported assets are allowlisted
3. confirmation UI shows all required values
4. execute path is idempotent
5. recovery path is tested
6. no secrets / images leak into logs
7. quote expiry and slippage limits are enforced
8. mobile signing path is stable on real iOS and Android devices

---

## 15. Bottom line

The feature is powerful only if it is strict.

The safe version of Smart QR Pay is:
- **scan locally**
- **parse deterministically where possible**
- **use AI only as guarded fallback**
- **show everything before pay**
- **track every execution state**
- **never trust unvalidated QR data with money**
