> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Bridge risk documentation

Public-safe risk model for the custodial `ACP -> BSC -> wACP` rail.

This document is intentionally transparent about system risk without exposing private operator secrets, signer material, or internal response playbooks.

Related documents:
- [Bridge spec v1](./bridge-spec-v1.md)
- [Bridge pilot mainnet status](./bridge-pilot-mainnet.md)
- [Official contract-address index](./OFFICIAL_CONTRACT_ADDRESSES.md)
- [Bridge launch checklist](./bridge-launch-checklist.md)
- [contracts/bridge-bsc/README.md](../contracts/bridge-bsc/README.md)

## Trust model

Current bridge model is **operator-mediated and reserve-backed**, not trustless.

What users can trust today:
- public contract source for `WACP.sol` and `BridgeGateway.sol`
- public runtime/API status surfaces
- public reserve and reconciliation surfaces
- on-chain BSC mint / burn events
- documented operator truth rules

What users must still trust operationally:
- operator custody of reserve assets
- operator key management and payout discipline
- off-chain watchers/orchestrator correctness
- incident response during chain/API/provider failures

## Main risk categories

### 1. Custodial reserve risk

**Risk:** reserve assets backing minted `wACP` are mismanaged, underfunded, or operationally unavailable.

**Impact:** users may hold `wACP` that cannot be redeemed promptly or fully.

**Current mitigations:**
- reserve summary and reconciliation endpoints
- conservative pilot caps
- operator truth rule: docs/runtime/public status must not pretend availability that does not exist
- explicit pause capability on the bridge contract / runtime

**Still open:** stronger proof freshness, stale-data alarms, and broader operator drill coverage.

### 2. Signer compromise / privileged-key abuse

**Risk:** BSC mint signer, ACP payout signer, or bridge admin secret is compromised.

**Impact:** unauthorized minting, false admin actions, or malicious payouts.

**Current mitigations:**
- keep secrets outside git and only in operator-controlled secret storage
- minimal operator surface area
- admin endpoints require both platform-admin auth and operator secret
- pause controls and daily/single-mint caps in the bridge path

**Still open:** stricter signer separation, stronger key rotation drills, and hardened recovery playbooks.

### 3. Chain / watcher desync

**Risk:** ACP or BSC watchers miss, double-process, or misclassify transactions/events.

**Impact:** duplicate mint attempts, delayed completion, or stuck intents.

**Current mitigations:**
- explicit bridge FSM in the spec
- idempotent intent/result tracking
- reconciliation endpoints
- runtime state surfaces for operator verification

**Still open:** deeper replay/recovery validation and more failure-mode drills.

### 4. Reorg / finality mismatch

**Risk:** transactions treated as final too early or under inconsistent confirmation assumptions.

**Impact:** false completed status, accounting drift, or unsafe downstream actions.

**Current mitigations:**
- documented confirmation handling in runtime status
- explicit ACP/BSC confirmation-aware flow
- conservative operator review during pilot state

**Still open:** broader multi-environment validation and stronger rollback/reorg drills.

### 5. Public-status / runtime truth drift

**Risk:** docs, UI, or API claim a safer or more complete status than runtime reality.

**Impact:** users and integrators make decisions on false assumptions.

**Current mitigations:**
- explicit truth rule in bridge docs
- runtime/API/public-status review as a launch criterion
- roadmap requirement to keep one real deployment story, not parallel contradictory ones

**Still open:** routine status-matrix hygiene and tighter release gating around public docs.

### 6. User input / address / amount mistakes

**Risk:** wrong ACP address, wrong chain expectations, or misunderstanding redeem remainder/floor rules.

**Impact:** failed release, delayed manual handling, or support burden.

**Current mitigations:**
- public UI/API quote surfaces
- documented reverse-rail remainder/floor semantics
- explicit release request flow in spec/docs

**Still open:** better UX copy, clearer risk copy for reverse rail, and more polished end-user safeguards.

### 7. Availability / provider dependency risk

**Risk:** ACP RPC, BSC RPC, database, queue, or proxy outages disrupt the rail.

**Impact:** delayed deposit detection, minting, status sync, or payouts.

**Current mitigations:**
- health/readiness checks
- compose-based runtime verification
- operator reconciliation path
- explicit bridge status endpoints

**Still open:** better redundancy and broader failover drills.

## Public user-facing posture

Current truthful posture should be:
- the bridge is real and operationally live enough to process pilot traffic;
- the rail is **not** equivalent to a fully trustless bridge;
- reverse payout flow is live in runtime truth, but still needs hardening and repeated validation;
- users should treat current operation as a conservative, operator-managed rail with published status and documented limits.

## Operator truth rules

Never claim all of the following unless they are actually true in runtime:
- reserve health is current and verified
- redeem is fully available
- reconciliation is clean
- confirmations/finality thresholds are satisfied
- incident status is resolved

If runtime must degrade, public status and docs must degrade with it.

## Minimum public evidence expected before calling the bridge "healthy"

- latest runtime health checks pass
- reserve/reconciliation status is available and clean
- at least one recent end-to-end operation can be traced across API + chain state
- docs match runtime truth
- no known unresolved critical signer/reserve incident
