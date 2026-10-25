# Production Secret Baseline

Purpose: operator checklist and evidence format for Priority 0.2 production-secret hardening. The current host/runtime baseline is already verified; this file exists to preserve that proof standard for future staging/production deploys.

Use this when:
- preparing a staging or production deploy with `docker-compose.prod.yml`
- moving secrets from local testing into CI / host env management
- re-verifying that prod-like secret guardrails are backed by real operator provisioning, not only repo-side checks
- recording refreshed evidence after any secret rotation, host migration, or deploy-environment change

## Required secret set

Before treating a production deploy as valid, provision all of the following outside the repo:
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `SECRET_KEY`
- `CURSOR_SECRET`
- `CRON_SECRET`

Optional but production-relevant values that should also be reviewed when used:
- `ACP_WALLET_RECOVERY_MASTER_KEY`
- `TURNSTILE_SECRET_KEY`
- `SMTP_PASSWORD`
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`
- `OPENROUTER_API_KEY` (homepage dialog; free models only; never send this to the browser)
- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`
- any bridge / wallet operator secrets sourced from private env files

## Rules

1. **Store real values only in env / CI / secret-manager locations.** Never commit them to git, paste them into docs, or leave them in screenshots/chat.
2. **If `docker-compose.prod.yml` uses the bundled `postgres` service, `DATABASE_URL` and `POSTGRES_PASSWORD` must match exactly.**
3. **Do not use placeholder-like or default values** for `SECRET_KEY`, `CURSOR_SECRET`, `CRON_SECRET`, or the bundled-postgres password.
4. **Run quiet compose validation before any deploy** so interpolation failures stop early without dumping resolved secrets.
5. **Capture evidence of provisioning without recording the secret values themselves.**

## Provisioning checklist

1. Put the real values into the host env, CI secret store, or repo-root `.env` kept outside version control.
2. Confirm the deploy helpers can see them:
   - PowerShell: `./scripts/deploy-ancap-cloud.ps1` or `./scripts/rebuild-prod.ps1`
   - Linux: `bash scripts/deploy-ancap-cloud.sh`
3. Run:
   - `docker compose -f docker-compose.prod.yml config --quiet`
4. If using the bundled compose postgres service, confirm the `DATABASE_URL` password and `POSTGRES_PASSWORD` are still in sync.
5. Start or verify the prod-like stack and confirm:
   - `http://127.0.0.1:8080/api/v1/system/health` returns `200` / `{"status":"ok"}`
   - `http://127.0.0.1:8080/api/v1/system/ready` returns ready with database/redis true
6. If wallet recovery is expected in production, verify `ACP_WALLET_RECOVERY_MASTER_KEY` is present before user migration begins.

## Evidence to capture

Record the following without storing the secret values:
- environment(s) provisioned: staging / production
- which secret store or host env location now holds the values
- time of last successful `docker compose -f docker-compose.prod.yml config --quiet`
- time of last successful health / ready verification on the prod-like path
- whether bundled-postgres parity (`DATABASE_URL` == `POSTGRES_PASSWORD`) was checked
- any remaining secrets intentionally unset because the feature stays disabled (for example Stripe)

## Done definition

Treat Priority 0.2 as closed for a given host/runtime only when all of the following are true:
- required production secrets are provisioned outside the repo
- `docker compose -f docker-compose.prod.yml config --quiet` succeeds in the real target environment
- prod-like or real deploy health checks succeed
- no placeholder/default production secrets remain in active env/CI locations
- roadmap/status docs no longer need to say that env/CI follow-through is still pending for that verified environment

Current verified note:
- as of 2026-05-28 on the current host/runtime, this baseline is satisfied: required secrets are present from repo-root `.env`, bundled-postgres parity holds, `docker compose -f docker-compose.prod.yml config --quiet` succeeds, and `http://127.0.0.1:8080/api/v1/system/health` plus `/api/v1/system/ready` return healthy responses

## Notes

- This checklist complements the repo-side guards already covered by tests; it does not replace them.
- Stripe secrets may remain intentionally unset until the Stripe adapter is being actively verified; in that case the feature should stay fail-closed.
- Secret rotation incidents belong in `docs/SECRET_ROTATION_RUNBOOK.md`; this file is for baseline provisioning and evidence, not incident response.
