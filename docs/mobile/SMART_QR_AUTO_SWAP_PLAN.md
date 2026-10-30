> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP Mobile — Smart QR Pay + Auto-Swap Plan

> Status: proposed feature plan | Updated: 2026-05-25
> Depends on: `ACP_WALLET_PRD.md`, `API_MOBILE.md`, `SECURITY_MODEL.md`, `BRIDGE_MOBILE_SPEC.md`
> Scope: iOS + Android, React Native / Expo app with native modules where needed
> Related technical specs: `SMART_QR_PAYMENT_INTENT_SCHEMA.md`, `SMART_QR_API_SPEC.md`, `SMART_QR_SECURITY.md`

---

## 1. Product goal

Turn the wallet into a **smart crypto payment app**:

1. User scans a QR code from **camera or photo gallery**.
2. App auto-detects what is encoded:
   - destination address
   - chain / network
   - asset / token
   - amount
   - memo / tag / payment reference
   - merchant label if present
3. If the invoice asset differs from the user's preferred spend asset, the app offers **auto-swap + pay**.
4. The app swaps from the selected source asset into the required payment asset and pays the invoice.
5. The **swap fee is charged in ACP**.
6. User can choose in Settings which crypto balance should be used first for auto-swap.

This should become a flagship UX feature: **scan -> understand -> convert -> pay**.

---

## 2. Critical reality check

This feature is strategically strong, but it is **not a small wallet patch**. It requires new product layers:

1. **Smart QR parsing / classification**
2. **Multi-asset payment intent model**
3. **Swap routing / quote engine**
4. **EVM wallet support inside mobile** (or a custodial/relay fallback)
5. **ACP-denominated fee engine**
6. **Payment orchestration / status tracking**
7. **Security and compliance review**

Also important: current mobile scope explicitly says **"Fiat buy/sell, in-app exchange" is out of scope for v1.0** and current wACP support is still weaker than full in-app EVM signing. So this plan should be treated as a **v1.1 / v2 product track**, not as part of the remaining v1.0 release-closure work.

---

## 3. Recommended product scope by release

### Phase A — Smart QR Pay MVP (recommended first ship)

Support only:
- ACP native payments
- EVM/BSC payments where asset + receiver can be handled by the app
- QR from camera
- QR from gallery/photo
- deterministic parsing for known standards
- user confirmation before final send
- preferred spend asset in Settings
- ACP swap fee charging

### Phase B — Smart Auto-Swap Pay

Add:
- auto-swap from user-selected source asset
- quote preview, slippage controls, route display
- payment session + execution tracking
- receipts and failure recovery
- more token support on EVM/BSC

### Phase C — AI / ambiguous QR intelligence

Add:
- AI fallback for non-standard or ambiguous QR payloads
- contextual classification of raw payloads / invoice strings / surrounding text from screenshots
- merchant-pattern recognition and confidence scoring

### Phase D — Multi-chain expansion

Later support:
- Base / Ethereum mainnet / Polygon
- TRON / Solana / Bitcoin-style invoices only if explicitly justified
- chain-specific memo/tag support beyond EVM

Recommendation: **do not start with “all chains”**. Start with **ACP + BSC/EVM** first.

---

## 4. Product principles

1. **Deterministic parser first, AI second**
   - Never rely on LLM/AI as the only parser for a payment request.
   - Known QR formats should be decoded by schema-based parsers.
   - AI is a fallback classifier for unknown/ambiguous content only.

2. **User confirmation is mandatory**
   - Even if the system auto-detects everything, the final confirmation screen must show:
     - what asset will be spent
     - what asset will be delivered
     - destination
     - amount
     - swap fee in ACP
     - network fee
     - slippage / route

3. **Non-custodial if possible**
   - Keys stay on device.
   - Mobile signs locally.
   - Backend may quote / route / relay, but should not hold user funds.

4. **Settings-driven source asset**
   - User can set preferred source asset for auto-pay.
   - Example: ACP / wACP / USDT / USDC / BNB (once supported).

5. **ACP captures platform fee**
   - Swap/service fee is denominated and charged in ACP.
   - If user lacks ACP fee reserve, the flow must warn or block.

---

## 5. Smart QR input types

### 5.1 Input modes

The app should support:
- live camera scan
- photo gallery import
- share-from-other-apps (future)
- paste raw invoice text / URI (future)

### 5.2 QR / invoice formats to support first

#### Deterministic parsers (must-have)
- raw ACP address
- raw EVM address (`0x...`)
- EIP-681 / EIP-831 style URIs
- BIP21-like amount/address patterns where relevant
- simple merchant payloads with address + amount
- bridge-related ANCAP internal QR formats if introduced later

#### Heuristic parsers
- raw string with known chain prefix
- address + amount separated by delimiters
- token contract + recipient + amount payloads

#### AI fallback
Use only when deterministic + heuristic parsing fail.

AI output must be validated into a canonical schema:

```json
{
  "network": "bsc",
  "asset": "USDT",
  "tokenAddress": "0x...",
  "recipient": "0x...",
  "amount": "25.50",
  "memo": null,
  "merchantLabel": "Example Store",
  "confidence": 0.91
}
```

If confidence is low or schema validation fails -> do not auto-pay.

---

## 6. What the “AI service” should actually do

The right implementation is **three-layer intelligence**, not “LLM scans QR image and guesses”.

### Layer 1 — QR decode
Native barcode/QR detection from camera or photo.

### Layer 2 — Structured parser
Rules for known standards:
- URI parsing
- chain recognition
- asset mapping
- amount extraction
- memo/tag extraction

### Layer 3 — AI fallback classifier
Only for unknown or weird merchant payloads:
- classify chain / asset / amount from raw payload
- extract merchant hints from screenshot text if present
- map strange invoice formats into canonical payment intent

### Why this matters
- safer
- cheaper
- faster
- easier to pass security review
- easier to explain to App Store / Play review

---

## 7. Main technical prerequisite: full mobile spend support for target chains

Today the wallet is strongest on **ACP native** and still incomplete on mobile native release closure. For smart auto-pay to work well, the app needs signing support for the payment target chain.

### Recommended architecture

#### Option A — Full non-custodial multi-chain wallet (recommended)
- derive and store EVM account locally from the same mnemonic
- support local signing for BSC/EVM transactions
- app performs approvals / swaps / transfers locally
- backend provides quotes, metadata, and optional relay services only

#### Option B — Operator swap relay (faster but weaker trust)
- user sends ACP to an operator-controlled payment rail
- backend executes swap + merchant payout
- app tracks payment session status

This is easier for MVP, but it is more custodial and weaker as a flagship wallet story.

**Recommendation:**
- use **Option A** as the final target
- if needed, use **Option B** only as a narrowly labeled beta/payment rail for supported merchants

---

## 8. Settings model

Add a new Settings section: **Smart Pay**

Fields:
- Preferred spend asset
- Allowed source assets (multi-select)
- Max slippage (%)
- Require confirmation for every payment (default: on)
- Auto-swap enabled (default: off at first)
- Minimum ACP fee reserve
- Preferred network priority
- Allowed merchant/invoice types
- Save scan history (on/off)

Example source assets after multi-asset support exists:
- ACP
- wACP
- USDT (BSC)
- USDC (BSC/Base later)
- BNB

---

## 9. Payment flow design

### 9.1 Direct pay flow

If scanned QR matches an asset the user already holds on the correct network:
1. Scan
2. Parse
3. Show confirmation
4. Sign locally
5. Broadcast
6. Save receipt

### 9.2 Auto-swap pay flow

If QR requests a different asset:
1. Scan QR / import photo
2. Parse into canonical `PaymentIntent`
3. Determine target network + target asset + amount
4. Pick source asset based on Settings
5. Request quotes from routing backend / DEX aggregator
6. Compute:
   - required source amount
   - ACP service fee
   - network gas
   - slippage bounds
7. Show confirmation screen
8. Execute swap
9. Execute payout transfer to merchant
10. Save receipt + route metadata + payment status

### 9.3 Failure-safe states

Need explicit statuses:
- SCANNED
- PARSED
- QUOTED
- AWAITING_CONFIRMATION
- SWAP_SUBMITTED
- SWAP_CONFIRMED
- PAYOUT_SUBMITTED
- COMPLETED
- FAILED_PARSE
- FAILED_QUOTE
- FAILED_SWAP
- FAILED_PAYOUT
- NEEDS_RECOVERY

This flow needs resumability if the app closes mid-payment.

---

## 10. Backend services to add

### 10.1 QR Intelligence API

New endpoints (example):
- `POST /v1/mobile/scan/decode` — optional server-side decode/classify fallback
- `POST /v1/mobile/payment-intents/parse` — parse QR payload into canonical intent
- `POST /v1/mobile/payment-intents/classify` — AI fallback for ambiguous payloads

### 10.2 Payment Routing API

- `POST /v1/mobile/payments/quote`
- `POST /v1/mobile/payments/execute`
- `GET /v1/mobile/payments/{id}`
- `POST /v1/mobile/payments/{id}/recover`

### 10.3 Supported assets / route discovery

- `GET /v1/mobile/smart-pay/assets`
- `GET /v1/mobile/smart-pay/networks`
- `GET /v1/mobile/smart-pay/settings/defaults`

### 10.4 ACP fee engine

- `POST /v1/mobile/smart-pay/fee-quote`
- charge platform/service fee in ACP
- validate minimum ACP reserve before execution

---

## 11. Mobile app implementation plan

## 11.1 Stage 0 — Product/spec groundwork

Deliverables:
- final supported-chain matrix
- payment-intent schema
- QR parser spec
- auto-swap UX spec
- ACP fee policy
- compliance notes for App Store / Play

Exit criteria:
- one approved spec for iOS + Android
- clear first-release chain scope

## 11.2 Stage 1 — Smart QR scanner

Features:
- camera scan
- gallery/photo scan
- native QR detection
- scan history (optional)
- local canonical parser for known formats

Recommended native stack:
- **iOS:** Apple Vision / VisionKit barcode detection
- **Android:** Google ML Kit Barcode Scanning
- React Native bridge/custom module if Expo layer is insufficient

Exit criteria:
- parse known ACP and EVM/BSC payment QRs reliably from camera + photo

## 11.3 Stage 2 — Canonical payment intent layer

Add a common model:

```ts
interface PaymentIntent {
  id: string;
  source: "camera" | "photo" | "paste";
  rawPayload: string;
  network: "acp" | "bsc" | "base" | "ethereum" | "unknown";
  assetSymbol: string | null;
  tokenAddress?: string | null;
  recipient: string;
  amount?: string | null;
  memo?: string | null;
  merchantLabel?: string | null;
  parseMethod: "deterministic" | "heuristic" | "ai";
  confidence: number;
}
```

Exit criteria:
- every scan becomes a validated `PaymentIntent` or explicit error state

## 11.4 Stage 3 — EVM spend support in wallet

Needed for true auto-swap + pay on BSC/EVM:
- derive EVM account from mnemonic
- secure local storage for EVM key material
- balances for BNB / USDT / USDC / wACP
- ERC-20 approvals + transfer support
- local signing + broadcast support

Exit criteria:
- app can spend supported EVM assets non-custodially

## 11.5 Stage 4 — Quote and route engine

Add routing layer for:
- direct payment
- ACP -> wACP -> target asset path
- source asset -> target asset path on supported chain
- slippage, deadline, gas estimation

Needs:
- on-chain router integration or aggregator partner
- route scoring: output, gas, reliability, latency

Exit criteria:
- app can get stable quotes for supported payment routes

## 11.6 Stage 5 — Auto-swap execution

Execution modes:
- direct send
- swap then send
- bridge then swap then send (later)

Must include:
- final quote confirmation
- failure rollback/recovery UX
- payment receipt storage
- status timeline

Exit criteria:
- supported QR invoice can be fully paid from non-matching source asset

## 11.7 Stage 6 — ACP fee charging

Rules:
- service fee denominated in ACP
- show fee separately from network gas
- block if ACP reserve below minimum
- allow fee quote refresh

Possible models:
- fixed ACP fee by payment class
- percentage fee with ACP min/max caps
- dynamic route-based ACP fee

Recommendation:
- start with a **simple transparent fee schedule**
- avoid too many dynamic variables in the first release

## 11.8 Stage 7 — AI fallback service

Add only after deterministic system works.

Use cases:
- strange merchant QR formats
- screenshot includes extra invoice text
- raw payload not matching supported standards

Rules:
- AI never signs
- AI never executes payment automatically
- AI output must be validated into canonical schema
- low confidence -> ask user, do not auto-route

Exit criteria:
- ambiguous QR payloads are classified better without unsafe automation

## 11.9 Stage 8 — Security, abuse, and store review hardening

Must cover:
- address poisoning / replacement detection
- malicious QR payload warnings
- contract allowlists / risk labels
- fee transparency
- anti-phishing confirmations
- no secrets in logs / screenshots
- route timeout and slippage protections
- safe recovery after crash/app restart

Store/compliance notes:
- avoid “investment” language
- present as non-custodial wallet + payment routing
- document swap risks and third-party liquidity risk

## 11.10 Stage 9 — Beta rollout

Beta order:
1. internal dogfood
2. closed beta with known merchants / known QR types
3. TestFlight + Play Internal
4. production rollout behind feature flag

Recommendation:
- launch first with **whitelisted QR/payment types**
- expand after real telemetry and failure analysis

---

## 12. UI / UX surfaces to add

### Main entry points
- Home screen CTA: **Scan & Pay**
- Send tab shortcut: **Smart QR Pay**
- Photo import button in scanner

### New screens
- Scanner screen
- Scan result / decoded invoice screen
- Quote comparison screen
- Confirm swap & pay screen
- Payment progress screen
- Receipt screen
- Smart Pay settings screen
- Recovery / failed payment screen

### New history items
Each smart payment should store:
- scanned payload hash
- parse method (deterministic/heuristic/ai)
- target invoice asset
- source spend asset
- swap route
- ACP fee
- network fee
- payment receipt(s)

---

## 13. Core risks

### Product risks
- too broad chain support too early
- user confusion around swap vs pay vs bridge
- poor failure recovery after swap but before payout

### Technical risks
- QR standards are messy and inconsistent
- true multi-chain non-custodial support is real engineering work
- quote volatility and slippage
- partial success states

### Security risks
- malicious QR payloads
- poisoned token contracts
- spoofed merchant requests
- signing wrong network/asset due to bad parser

### Compliance / store risks
- in-app swap can trigger additional review scrutiny
- wording must avoid custodial/investment implications
- some routes/partners may create regulatory burden by jurisdiction

---

## 14. Recommended rollout path

### Track 1 — Finish current wallet v1.0 release closure
Do first:
- native build closure
- device verification
- MASVS checklist
- TestFlight / Play Internal
- production release

### Track 2 — Build Smart QR Pay foundation
Then:
- scanner + gallery support
- canonical parser
- direct pay for supported QR formats

### Track 3 — Add non-custodial EVM spend support
Then:
- local EVM wallet support
- token balances
- ERC-20 transfers / approvals

### Track 4 — Add auto-swap pay
Then:
- quote engine
- route engine
- ACP service fee
- receipts and recovery

### Track 5 — Add AI fallback intelligence
Finally:
- ambiguous QR classification
- weird merchant/invoice support
- confidence scoring and guarded automation

---

## 15. Recommended first-release scope for this feature

If the goal is to ship something valuable fast without blowing up complexity, the first production scope should be:

1. ACP + BSC only
2. camera + gallery scan
3. deterministic QR parsing first
4. direct pay first
5. auto-swap only for a small supported asset list
6. user confirmation always required
7. ACP fee charged explicitly and separately
8. feature-flagged rollout

This gets the product to a strong “wow” moment without pretending universal crypto invoice support is easy.

---

## 16. Bottom-line recommendation

Yes — this can become the main differentiator of the wallet.

But the right sequence is:
1. finish the wallet release baseline
2. build smart scan + parse
3. add real multi-asset spend support
4. add route/quote/auto-pay
5. only then add AI fallback for strange QR payloads

The winning version is **not** “AI guesses from a QR image”.
The winning version is **structured payment intelligence + safe non-custodial execution + ACP fee capture**.
