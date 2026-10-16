# ANCAP — Full Decentralization Roadmap

> Status: planned track | Added: 2026-10-16  
> Goal: **full decentralization of the ANCAP project** — no single host, company, or region as a lasting single point of failure for ACP consensus peers, public APIs, sealed edge capacity, and operator exit.  
> Source of truth links: `MASTER_ROADMAP.md` (priority **R14**), `PRODUCTION_ROADMAP.md`  
> Related: open-source transparency track in Master, multi-node ACP tip family (`docs/ORACLE_CLOUD_ACP_NODE_PLAN.md`), orbital datacenters **R11** (`docs/SPACEX_SATELLITE_ENCRYPTED_SERVERS_ROADMAP.md`)

## Product thesis

ANCAP starts as an operator-hosted product with an ACP Lean chain and growing peer mesh. The long-horizon target is a **federated, multi-operator system**:

- **ACP:** many independent peers on one tip family; public RPC diversity; no sole miner/assembler monopoly narrative without measured reality.
- **Product plane:** multi-region / multi-operator API and data planes with signed mirrors and honest failover.
- **Edge:** attested ground (then **orbital**) nodes can run sealed jobs under policy — including future **ANCAP datacenters in space** (R11 X6–X7).
- **Exit:** users and orgs can leave a given operator with portable identity proofs and ledger receipts.

**Non-goals (near term):** pretending the live stack is already fully decentralized; removing all operator accountability; unlicensed spectrum or weapons-adjacent orbital claims.

## Phased delivery

### Phase D0 — Threat model & honest boundaries `[ ]`

- Map SPOFs today (API host, Postgres, single RPC, bridge keys, DNS).
- Define what “fully decentralized” means for ANCAP in public copy (ledger vs product UX vs custody).
- Update compliance / trust docs before marketing decentralization milestones.

### Phase D1 — Multi-operator ACP mesh `[ ]`

- Harden peer join docs and tip-family health monitoring beyond the current three-peer tip family.
- Public explorer/status surfaces that show multi-peer agreement (not a single RPC as truth).
- Operator runbooks for new peers (Oracle Cloud plan and successors).

### Phase D2 — Federated API / read plane `[ ]`

- Multi-region deploy pattern for API + DB (primary/replica or active-active with conflict rules).
- Signed public mirrors for trust docs and reserve/benchmark snapshots.
- Failover drills without silent ledger or receipt forks.

### Phase D3 — Permissionless / attested edge participation `[ ]`

- Ground attested edge adapters for sealed offload (feature-flagged).
- Bridge to R11 orbital edge attestation registry (`FF_ORBITAL_EDGE` and successors).
- Policy: who may run edge capacity; dual-control for destructive ops.

### Phase D4 — Governance & keys `[ ]`

- Threshold / dual-control for bridge, orbital unlock, and destructive infra actions.
- Open contribution path for infra adapters (align with Master open-source phases).
- Transparent incident and tip-disagreement disclosure.

### Phase D5 — Sovereignty exit `[ ]`

- Portable org/user identity export + ledger proof bundles.
- Self-host / third-party operator handoff checklist.
- Documented “exit to another operator or self-host” path on trust surfaces.

## Dependencies

- Stable ACP Lean chain and public explorer honesty.
- Open-source / GitHub transparency track (Master Phase 1–8).
- R11 for space datacenter tier (optional outer mesh, not a prerequisite for D0–D2).
- Does **not** block: Phase 6 mobile MVP, near-term commerce, R9–R13 product tracks.

## Success metrics (long-horizon)

| Metric | Target |
|--------|--------|
| Independent ACP peers on tip family | ≥ 3 operators / regions before claiming “mesh” |
| API SPOF | Documented multi-region failover drill passed |
| Edge participation | ≥ 1 non-primary attested edge path (ground or orbital) |
| Operator exit | Published portable export path exercised in staging |
| Public claims | No “fully decentralized” marketing until D4 evidence checklist green |

## Open questions

- How much of Workflow Store / LLM execution stays BYOK vs network-hosted.
- Bridge custody model under multi-operator control (threshold vs federation of bridges).
- Whether orbital capacity (R11) is required for D5 marketing or only for seizure-resistance tier.
