# ROP-01 acceptance evidence — release a9395368

Scope: the only open ROP-01 checkbox in
`docs/RESEARCH_OPERATIONS_PILOT_ROADMAP.md` —
"CI and deployed migration/UI/live-source acceptance on a fixed release".

This file records what is proven for one fixed release, what is not, and how to
re-verify it. It does not declare ROP-01 commercially accepted, does not claim
customer-source quality and does not close any ROP-02..05 gate.

## Fixed release

- Commit: `a9395368d74cea2218b0e7265d373062c07bfef4` ("Merge pull request #148").
- Production build id: `a939536` (`GET https://ancap.cloud/internal/frontend-build`,
  checked 2026-11-04). Build id matches the release commit prefix.
- `master` has since advanced to `5d5ece2c` (docs-only PR #149: roadmap/queue
  status reconciliation). That commit changed no runtime code, so the deployed
  build remains the release under test.

## CI on the release SHA

Check runs reported for `a9395368` (GitHub Actions, 2026-11-03):

| Check | Run | Result |
| --- | --- | --- |
| Backend CI | 41645358246 | success |
| Deploy ancap.cloud | 41645358135 | success |
| Docs CI | 41645358235 | success |
| CodeQL (Python, JS/TS, Actions) | 41645358248 | success |
| Secret Hygiene | 41645358179 | success |

Counts from the Backend CI log on that run:

- backend: **1384 passed, 47 skipped** (`pytest -q`, `backend-ci.yml:168`);
- unit job: **277 passed, 7 skipped**;
- documentation block: **60 passed, 5 skipped**;
- coverage line for the research modules: router `research_ops.py` 100%,
  schemas 94%, service 52%.

Because Backend CI runs the whole `tests/` tree, the four research modules below
are inside the tested set. A skipped test is not counted as passed; the 47/7
skips are reported as-is.

**Frontend CI did not run on `a9395368`** — `frontend-ci.yml` is path-filtered and
the release commit changed documentation only. The last green Frontend CI run is
41639480462 on `c8bd9142`, not on the release SHA. No browser acceptance for the
deployed build is therefore claimed.

## ROP-01 test inventory (26 test functions)

| Module | Test functions | Covers |
| --- | --- | --- |
| `tests/api/test_research_operations_api.py` | 5 | cross-project/member isolation, guest denial, read-only member, 10-source / 20-version / 50-claim limits, retention and purge, project/source deletion, text-change and unavailable states, concurrent check serialization, absence of payment intents |
| `tests/unit/test_research_fetch.py` | 4 | URL policy (HTTP, loopback/link-local/private, credentials, non-443 port, query, fragment), DNS pinning + Host/SNI, redirect/status/content-type/encoding/size rejection, text-vs-technical change classification, private-address rebinding block |
| `tests/api/test_research_ops.py` | 7 | route-level source/claim/packet happy paths, brief and snapshot reads |
| `tests/api/test_research_packets_api.py` | 10 | ROP-02 evidence: exact packet/review versions, stale evidence before/after outbox claim, revoked roles, replay, text-shortening rejection |

`SourceCreate` rejects query strings and fragments at the schema boundary, so the
"no query/fragment" rule is enforced, not only documented.

Local re-run on 2026-11-04 (repository test configuration, no live network):

- `pytest tests/unit/test_research_fetch.py -q` — 18 passed (parametrized URL and
  response cases);
- `pytest tests/api/test_research_operations_api.py -q` — 5 passed;
- `pytest tests/unit/test_theodore_queue_guard.py tests/unit/test_alembic_single_head.py -q`
  — 8 passed.

CI itself ran the whole suite against PostgreSQL (41645358246); these local runs
re-check the same modules but are not a substitute for the CI result.

## Deployed migration

Repository state (checked 2026-11-04):

- single Alembic head: `104_merge_packet_listing` (file
  `alembic/versions/104_merge_packet_listing_heads.py`);
- `tests/unit/test_alembic_single_head.py` guards against a branched graph;
- research retention tables come from `093_research_operations`
  (down_revision `092_workflow_cost_evidence`), quotas from
  `097_source_quotas_rop03_quota_limits`, schedules from
  `099_source_schedules_rop03_bounded_collection`, packet templates from
  `103_packet_templates_rop05`.

Production migration evidence from the Deploy 41645358135 log
(`Deploy over SSH`, 2026-11-03):

```
13:49:21.795  INFO [alembic.runtime.migration] Context impl PostgresqlImpl.
13:49:22.006  INFO [alembic.runtime.migration] Running upgrade 102_cost_evidence_attribution -> 103_packet_templates_rop05, ROP-05: reusable packet templates (categories/structure only).
13:49:22.083  INFO [alembic.runtime.migration] Running upgrade 103_packet_templates_rop05, 103_robinhood_listing -> 104_merge_packet_listing, Merge packet-template and Robinhood-listing migration branches.
```

So the production database was at `102_cost_evidence_attribution` before this
deploy and reached `104_merge_packet_listing` during it. `093_research_operations`
predates that sequence (it is an ancestor of 102); this log does not re-prove the
093 application, only the final head.

Post-deploy smoke in the same run: `/api/v1/system/health` ok,
`/api/v1/system/ready` ready, `/internal/frontend-build` = `a939536`.

## Live production probes (read-only, 2026-11-04)

| Probe | Response |
| --- | --- |
| `GET /internal/frontend-build` | `{"NEXT_PUBLIC_APP_BUILD_ID":"a939536", ...}` |
| `GET /api/v1/system/health` | `{"status":"ok"}` |
| `GET /api/v1/system/ready` | `{"status":"ready","checks":{"database":true,"redis":true}}` |

Scheduled job run 41760068231 (2026-11-04, same release SHA) succeeded. It only
enqueues the background tick (`{"status":"queued", ...}`); it proves the scheduler
fired, not that the research purge iteration executed. `purge_expired` is wired
into `workflow_ops_tick`, which `_run_all_jobs` calls in-process.

## Not proven — remains open

- **UI acceptance on the deployed build.** The roadmap cites 5 local Chromium
  scenarios (EN/RU/UK/DE/zh-Hant, 390 px); no browser test runs in CI and none was
  run against production in this cycle. An authenticated production account was
  not available.
- **Live customer-source acceptance.** No real client source was collected;
  permission basis, accuracy and materiality review remain operator work.
- **Paid delivery / external payment.** No ROP-02 webhook was sent and no
  research packet was delivered to a customer.
- **ROP-03/04/05 measurement thresholds** (useful-alert, claim-link,
  accepted-packet, 30% onboarding effort, renewal cohorts) are untouched here.

## How to re-verify

```bash
# single migration head and research lineage
python -m alembic heads
python -m alembic history | grep -E "093_research|103_packet|104_merge"

# targeted ROP-01 tests (needs the test PostgreSQL used by conftest)
pytest tests/unit/test_research_fetch.py tests/api/test_research_operations_api.py -q
pytest tests/unit/test_theodore_queue_guard.py -q

# production read-only probes
curl -s https://ancap.cloud/api/v1/system/health
curl -s https://ancap.cloud/api/v1/system/ready
curl -s https://ancap.cloud/internal/frontend-build
```
