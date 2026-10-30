> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Theodore operator security

Updated: 2026-09-28

## What Theodore is

Theodore is a **visible** promo / ops helper that posts paid SKU copy to an allowlisted Telegram channel via `scripts/theodore-earn-promo.ps1`.

It is **not**:
- a hidden Windows persistence agent
- a wallet / bridge signer
- an autonomous spender of ACP / wACP / fiat

## Required run mode

- Set `ANCAP_REPO_ROOT` or run from the repo so paths resolve without machine-specific hardcoding.
- Load secrets only from `.env.telegram` / `.env` in the repo root.
- Schedule with a **visible** interactive task (do **not** use `-WindowStyle Hidden` / stealth launch).
- Logs: `memory/theodore-earn.log` and `memory/theodore-earn-state.json`.

## Money controls

- Script refuses to start if wallet/signer env vars are present (`ACP_HOT_MNEMONIC*`, `PRIVATE_KEY`, `MNEMONIC`, `BRIDGE_SIGNER_KEY`).
- On-chain mint, LP, bridge, and payouts require a **separate human-confirmed** operator path (reserve-proof gate + treasury/multisig).
- Paid-API spend caps in the product remain independent of Theodore.

## Related controls

- Embodied / tool deny list: `docs/EMBODIED_AI_SECURITY_CONTROLS.md`
- Host hardening: `docs/SECURITY_SERVER_PLAN.md`
- Public audit checklist: `docs/AUDIT_CHECKLIST.md`
- Cisco / enterprise segmentation notes (operator appendix): `docs/CISCO_SECURITY_APPENDIX.md`
