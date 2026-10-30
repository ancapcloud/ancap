> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ACP Wallet — Product Requirements (MVP)

## Product

**ANCAP ACP Wallet** — official non-custodial mobile wallet for ACP and wACP.

**Tagline:** Store, send, receive and bridge ACP securely. Your keys. Your ACP.

## Goals

1. Give ACP a native mobile surface (not only web custodial wallet).
2. Link ACP chain ↔ wACP on BSC via existing clearing rail.
3. Pass App Store / Google Play as **software wallet, non-custodial**.

## MVP scope (v1.0.0)

| Feature | Included |
|---------|----------|
| Create wallet (BIP39 12 words) | Yes |
| Import wallet | Yes |
| Watch-only address | Yes |
| Backup + confirm seed | Yes |
| PIN + biometrics | Yes |
| ACP balance | Yes |
| Send / receive ACP | Yes (local sign) |
| Transaction history | Yes |
| wACP balance (BSC) | Yes (read-only, user supplies `0x` address) |
| Bridge status ACP ↔ wACP | Yes |
| Risk disclaimer + legal links | Yes |
| Languages EN / RU / UK / DE | Yes |

## Out of scope (v1.0)

- Fiat buy/sell, in-app exchange
- ICO, investment copy, task rewards for install/share
- Custodial balances
- Staking, governance, WalletConnect
- ANCAP Cloud login (optional v1.1)

## Users

- ACP holders who want self-custody on phone
- Users bridging to BSC / PancakeSwap liquidity
- ANCAP ecosystem participants (future: optional account link)

## Success metrics

- Crash-free sessions > 99%
- Send success rate > 98% (testnet + mainnet)
- Bridge intent completion visible end-to-end
- Store approval on first or second submission

## Store positioning

- **Category:** Finance → Cryptocurrency wallet (non-custodial)
- **Not:** exchange, investment app, play-to-earn

See `SECURITY_MODEL.md` and `BRIDGE_MOBILE_SPEC.md` for compliance copy.
