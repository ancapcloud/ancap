# ANCAP — Orbital Datacenters / SpaceX Encrypted Servers Roadmap

> Status: planned track | Added: 2026-09-06 · Updated: 2026-10-16  
> Goal: launch **ANCAP edge nodes** as satellite payloads with **encrypted servers**, then scale toward **ANCAP datacenters in space** (sealed multi-node orbital compute/storage), using **SpaceX** (rideshare / Transporter / custom manifests as available) as the primary launch path.  
> Source of truth links: `MASTER_ROADMAP.md` (priority **R11**), `PRODUCTION_ROADMAP.md`  
> Related: full decentralization **R14** (`docs/FULL_DECENTRALIZATION_ROADMAP.md`), ACP node ops, bridge/custody hardening, compliance matrix, mobile/org identity (ground ops only)

## Product thesis

ANCAP’s long-horizon infra layer is **sovereign, hard-to-seize compute**:

1. **v1–v2 (edge sats):** small satellites hosting encrypted ACP-adjacent services (attestation relays, sealed workflow runners, encrypted object stores, and/or key-ceremony helpers) with **zero cleartext at rest** and **ground-authorized** session keys only.
2. **v3+ (orbital datacenters):** place **ANCAP datacenters in space** — higher-capacity sealed modules (power/thermal/storage class beyond demo edge), constellation redundancy, and optical/RF backhaul so critical capacity is not confined to terrestrial jurisdictions.

Together with **R14 full decentralization**, space capacity is the outer tier of a ground + orbital peer mesh — not a marketing claim of “ANCAP lives only in space” before flight hardware exists.

**Non-goals (v1):** consumer broadband constellation, Starlink reseller product, weapons/dual-use payloads, claiming regulatory approval before counsel review, claiming live orbital datacenters before X4/X6 evidence.

**Goals (v1–v3):** feasibility → payload architecture → crypto/ops model → SpaceX launch path → ground segment → first flight → ACP edge integration → datacenter-class modules → constellation ops.

## Why SpaceX

| Option | Role |
|--------|------|
| SpaceX rideshare (e.g. Transporter / Bandwagon-class) | Primary: lowest cost path for cubesat / ESPA-class encrypted server demos |
| SpaceX dedicated / multi-manifest | Later: if mass/power/orbit requirements exceed rideshare envelopes |
| Alternate LV | Contingency only; keep ICD and radiation plan launcher-agnostic |

Procurement is **commercial launch services + licensed payload** — not an ITAR/export or spectrum shortcut. Export control, ITU/national filings, and insurance sit on the critical path.

## Security model (encrypted servers)

1. **At rest:** full-disk / volume encryption; keys never stored in clear on-orbit; boot sealed with measured firmware.
2. **In transit:** mutual TLS or Noise-based links over TT&C / optical / RF ground; rotate session keys via ground HSM.
3. **Control plane:** dual-control ground ops; signed command uplink; deny-by-default.
4. **Workload:** sealed ACP edge jobs (attestation, encrypted blob relay, optional TEE if radiation-tolerant hardware allows).
5. **Compromise assumption:** physical capture of bus ≠ plaintext customer data (keys require ground ceremony + time-bound unwrap).

## Phased delivery

### Phase X0 — Feasibility & constraints `[~]`

- Orbit class (LEO preferred), mass/power/thermal envelope, radiation budget.
- Legal/export memo: jurisdiction of operator, payload classification, data residency claims that are *honest*.
- Decision record: cubesat vs ESPA; single demo sat vs 3-sat path redundancy.
- In-repo control-plane stub: `app/schemas/orbital_edge.py`, `/orbital-edge/status`, org node registry (feature-flagged writes via `FF_ORBITAL_EDGE`).

### Phase X1 — Payload & encrypted server architecture `[~]`

- Block diagram: compute, storage, crypto module, radio, power, ADCS interfaces.
- Software: hardened OS, encrypted volumes, remote attested boot story.
- Threat model: RF spoofing, jamming, supply-chain, ground insider, debris/EOL.
- Attestation registry tables (`orbital_edge_nodes`, `orbital_attestations`) + API for sealed_boot / encrypted_volume / command_path / health_ping digests.

### Phase X2 — Ground segment & key ceremony `[ ]`

- Ground station plan (owned + partner NOC).
- HSM-backed key ceremony; dual-control unlock; emergency wipe policy.
- Runbooks: launch, LEOP, nominal ops, anomaly, deorbit.

### Phase X3 — SpaceX path & program management `[ ]`

- Rideshare ICD fit check; interface docs; environmental test plan (vibe/TVAC).
- Commercial engagement checklist with SpaceX (or integrator) for manifest slot.
- Insurance, launch license coordination with counsel; schedule buffer for slips.

### Phase X4 — Integration, test, first flight `[ ]`

- FlatSat → environmental → ship → launch.
- On-orbit checkout: encrypted volume unlock via ground, health telemetry, sealed ping to ACP control plane.
- Success criteria: encrypted store round-trip + authenticated command path for ≥ N days.

### Phase X5 — ACP / ANCAP product edge `[ ]`

- Productize as **ANCAP Orbital Edge** (feature-flagged): attestation relay, sealed workflow offload, disaster-recovery sealed backup shard.
- Billing/ops: ACP-denominated capacity reservation (treasury UX later).
- Fleet ops: 2nd/3rd bird for redundancy; EOL and replacement cadence.

### Phase X6 — Orbital datacenter class `[ ]`

- Scale payload class beyond demo edge: power budget, thermal rejection, radiation-tolerant storage density, and sealed rack-equivalent modules.
- Architecture decision: few larger birds vs many smaller nodes for “datacenter in space” capacity.
- Backhaul plan: RF + optical crosslink options; latency/bandwidth honest limits for product UX.
- Legal/ops memo: what residency / seizure-resistance claims are allowed after counsel review.

### Phase X7 — Constellation & mesh ops `[ ]`

- Multi-bird redundancy with attested health in `/orbital-edge` (or successor control plane).
- Inter-sat mesh for sealed shard sync; ground federated operators (ties to **R14** D3–D5).
- EOL, replacement cadence, debris/compliance runbooks; ACP capacity reservation for reserved orbital slots.

## Dependencies

- Stable ACP ledger + org identity (for who may authorize orbital workloads).
- Compliance matrix update before any public marketing of “satellite servers” or “datacenters in space”.
- **R14** for ground federation so orbital tier is not the only decentralization path.
- Does **not** block: Phase 6 mobile MVP, R9 securities, R10 Apple Watch fleet.

## Success metrics

| Metric | Target (first flight) |
|--------|------------------------|
| Cleartext at rest on bus | None (keys unwrap only for active session) |
| Authenticated uplink | 100% of commands signed + dual-control for destructive ops |
| Encrypted store round-trip | Demonstrated from ground within LEOP+30d |
| SpaceX (or approved LV) slot | Manifest secured before PDR exit |

## Open questions

- TEE availability under LEO radiation vs software-only sealed boxes.
- Optical vs RF primary for high-rate encrypted sync.
- Whether first payload is **relay-only** (safer) vs **general compute**.
