> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP — Embodied AI / Humanoid Model Security Controls

> Status: active baseline | Added: 2026-09-10  
> Context: open-source humanoid foundation models (e.g. Unitree **UnifoLM-WLA-1.0**) will show up next to DeFi / RWA rails. Open weights ≠ safe deployment.  
> Related: `docs/SECURITY_SERVER_PLAN.md`, OpenClaw Theodore hardening, orbital-edge attestations (R11)

## Problem (DeFi analogy)

Open protocols (DeFi) and open embodied models share failure modes:

| DeFi failure | Embodied / Physical AI analogue |
|--------------|----------------------------------|
| Fork fragmentation | Unverified fine-tunes / weight swaps |
| Oracle spoofing (Chainlink-class risk) | Sensor / teleop / world-model input spoofing |
| Rug / malicious upgrade | Silent policy replacement on the robot |
| Unaudited composability | Chaining VLA → actuator without gates |
| Key leakage | Telemetry, keys, or ACP wallets on the edge |

**Guarantee language:** no open model can be “guaranteed safe” after wide adoption. ANCAP’s job is **defense in depth + attestation + least privilege + kill switches**, same posture we use for bridge/ACP rails.

## Non-goals

- Hosting UnifoLM / Unitree weights on the ANCAP API host.
- Claiming ANCAP certifies Unitree safety for industrial deployment.
- Allowing agents (Theodore / OpenClaw) to `exec` robot control stacks by default.

## Control plane (must hold)

### C1 — Provenance & supply chain
1. Pin **vendor release digest** (git tag + Hugging Face revision / checksum) before any integration experiment.
2. Prefer read-only catalog references; never auto-pull “latest” into production.
3. Treat third-party fine-tunes as untrusted until hashed and reviewed.

### C2 — Separation of brains and money
1. Embodied inference runs **off** the ACP settlement host.
2. ACP / wACP / bridge keys never share process space with robot inference.
3. Agents that discuss robotics (Theodore) stay on **minimal tool profile**: no `exec`, `write`, `browser`, messaging blast.

### C3 — Capability allowlists (robot side)
1. Task allowlist (desktop vs whole-body) — no open-ended “do anything” in live settings.
2. End-effector / force / speed caps enforced in firmware / middleware, not only in the model.
3. Human-in-the-loop for first N runs of any new policy checksum.

### C4 — Attestation & audit
1. Record policy digest + dataset/model card URI in ANCAP audit events when a workflow references embodied AI.
2. Reuse patterns from orbital-edge attestations (`digest_sha256`, verified flag) for sealed edge payloads.
3. Public status surfaces must say **vendor claim** vs **ANCAP-verified**.

### C5 — Runtime isolation
1. Sandbox inference (container / VM / air-gapped lab) with egress allowlist.
2. No raw privileged shell from model tool-calling into production.
3. Network default-deny for robot controllers; explicit peer map.

### C6 — Kill switches & rollback
1. Hardware e-stop and software kill independent of the foundation model.
2. Instant rollback to last known-good policy digest.
3. Feature flags for any ANCAP vertical that wires embodied adapters (`FF_*` off by default until review).

### C7 — Data / privacy
1. No customer DNA / health / wallet secrets in robot training loops (AETERNA already hash-only).
2. Telemetry retention limits; no silent cloud upload of home/lab video without consent.

### C8 — Governance (anti-fragmentation)
1. Publish an ANCAP **approved model register** (name, digest, license, threat notes) before production adapters.
2. Security review ticket required for each new UnifoLM / VLA / WMA revision.
3. Prefer one pinned revision per environment (dev / staging / prod).

## ANCAP concrete baseline (today)

| Surface | Control |
|---------|---------|
| OpenClaw Theodore | Tool deny: `exec`, `write`, `browser`, messaging groups; Telegram allowlist-only |
| API host | No Unitree weights on disk; lunar LFM is metadata themes only |
| Bridge / ACP | Operator secrets, dry-run gates, confirmations, bind-deposit admin recovery |
| Orbital edge | Attestation digests + `FF_ORBITAL_EDGE` |
| Lunar R13 | Speculative registry + Outer Space Treaty disclaimer; no sovereign title claim |
| Embodied adapters | `FF_EMBODIED_ADAPTER=false`; `GET /v1/embodied-ai/security` register (UnifoLM pending digest) |

## Answer to “how do we guarantee safety?”

We don’t guarantee. We **bound risk**:

1. **Pin + hash** open models (stop silent drift).  
2. **Isolate** inference from capital rails.  
3. **Cap actuators** outside the neural net.  
4. **Attest** what ran.  
5. **Kill** independently of the model.  
6. **Flag** adapters until reviewed.  
7. **Refuse** unverified fine-tunes in production catalogs.

That is the Chainlink lesson applied to Physical AI: open connectivity is valuable; **unguarded trust of any single feed or weight file is not**.

## Next actions

- [x] Approved-model register (`GET /v1/embodied-ai/security` — UnifoLM-WLA-1.0 `pending_digest`)
- [x] `FF_EMBODIED_ADAPTER` stub (default false; `require_adapter_enabled()` gate)
- [x] Heartbeat check: Theodore tool deny list still intact (2026-09-10)
- [x] Public post / Moltbook reply pointing here for DeFi/RWA readers
- [ ] Pin official UnifoLM weight digest when vendor publishes checksum
- [ ] Production adapter only after security review ticket + firmware cap attestation
