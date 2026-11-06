# CI/Deployment Evidence — 2026-11-03

## Origin/master HEAD

- SHA: `a9395368d74cea2218b0e7265d373062c07bfef4`
- Merge PR #148 from ancapcloud/codex/fix-bootstrap-utf8-test

## Successful GitHub Actions runs on a9395368

| Check | Actions Run ID | Status |
| --- | --- | --- |
| Backend CI | 41645358246 | success |
| Deploy ancap.cloud | 41645358135 | success |
| Docs CI | 41645358235 | success |
| CodeQL | 41645358248 | success |
| Secret Hygiene | 41645358179 | success |

## Prior integration baseline

- PR #146 (c8bd9142) integrated PRs #142–145
- Alembic single head `104_merge_packet_listing` (file `104_merge_packet_listing_heads.py`; the deploy log shows the production upgrade) — see `docs/ROP01_ACCEPTANCE_2026-11-04.md`
- COST-03 closed with canonical `GET /v1/workflow-store/admin/cost-evidence/{evidence_id}`

## Scope

This evidence confirms engineering CI and deployment success. It does NOT close:

- Commercial/user acceptance (interviews, paid pilots, renewals)
- Live customer-source quality validation
- Paid delivery verification

## Open PRs at time of verification

None before this update. PR #149 (this evidence note) was the only open PR while
it was being verified and merged as `5d5ece2c` on 2026-11-04.
