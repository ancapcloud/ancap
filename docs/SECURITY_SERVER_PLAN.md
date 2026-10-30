> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ANCAP — Security Audit & Improvement Plan
**Date:** 2026-05-22 | **Auditor:** ARDO

---

## 1. Server Security Issues (CRITICAL)

### 1.1 SSH Bruteforce — No Protection
**Status:** 🔴 CRITICAL
**Finding:** Dozens of failed SSH login attempts logged daily from various IPs (Korea, Indonesia, China, Brazil, etc.)
- IPs: 121.142.87.218, 45.232.73.84, 76.79.213.70, 103.76.84.221, 190.85.41.170, 39.129.90.146, etc.
- `fail2ban` is NOT installed
- `ufw` exists but not configured

**Fix:**
```bash
# Install and configure fail2ban
sudo apt update && sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Create /etc/fail2ban/jail.local:
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = 22
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

# Then: sudo systemctl restart fail2ban
```

### 1.2 UFW Not Configured
**Status:** 🔴 HIGH
**Finding:** Firewall is open. Only 22 (SSH) is "open" implicitly.

**Fix:**
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp comment 'SSH'
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw allow 8083/tcp comment 'HestiaCP'
# Rate limit SSH
sudo ufw limit 22/tcp comment 'SSH rate limit'
sudo ufw --force enable
```

### 1.3 Disk at 87% — 5.1GB Free (40GB Total)
**Status:** 🟡 HIGH
**Finding:**
- Docker images total ~5GB (api 2GB, frontend 1.2GB, acp-node 170MB)
- Multiple old image versions not pruned
- Rust build artifacts in image layers

**Fix:**
```bash
# Prune old images
docker image prune -a -f
# Or selectively:
docker rmi $(docker images --filter "dangling=true" -q) 2>/dev/null
# Prune build cache
docker builder prune -a -f
# Check what's using space
sudo du -sh /var/lib/docker/ 2>/dev/null
# Consider: docker system df
```

### 1.4 Package Updates Pending
**Status:** 🟡 MEDIUM
**Finding:** 20+ packages upgradable including nginx, mariadb, bind9, libpq

**Fix:**
```bash
sudo apt update && sudo apt upgrade -y
# Note: nginx upgrade may restart service — ensure docker-compose stays up
```

### 1.5 `/v1/system/jobs/tick` Unprotected
**Status:** 🔴 CRITICAL
**Finding:** Anyone can trigger background jobs (reputation, ledger invariant, graph metrics, etc.)

**Fix:** Add optional cron secret header check:
```python
# In app/api/routers/system.py
CRON_SECRET = os.getenv("CRON_SECRET")
@router.post("/jobs/tick")
async def tick(request: Request):
    if CRON_SECRET:
        header = request.headers.get("X-Cron-Secret")
        if header != CRON_SECRET:
            raise HTTPException(401, "Unauthorized")
    # ... rest of tick logic
```

### 1.6 Idempotency implementation follow-through
**Status:** 🟡 MEDIUM
**Finding:** the old audit note is stale; current repo now has idempotency key storage and tests, so the remaining work is verification/documentation drift cleanup rather than first implementation.

**Current repo truth:**
- `app/services/idempotency.py` implements request-hash checking and cached response storage
- current tests exercise `Idempotency-Key` usage across mutable order / ledger / run flows

**Fix / follow-through:**
- keep endpoint coverage honest in docs and tests
- add more endpoint-level verification only where a mutable flow still lacks explicit idempotency handling

---

## 2. Mail Server Issues

### 2.1 Port 25 — External Delivery Blocked
**Status:** 🔴 HIGH
**Finding:**
- Port 25 IS open on server (LISTEN 0 20 0.0.0.0:25)
- Dovecot running (IMAP/POP3 OK)
- But `postfix` status returned empty — exim4 binary exists but no config
- `/var/log/mail.log` doesn't exist
- `/etc/postfix/master.cf` doesn't exist

**Diagnosis:** Most VPS providers block port 25 outbound by default. Need either:
1. Ask VPS provider to unblock port 25
2. Use mail relay (SendGrid, Mailgun, AWS SES, etc.)
3. Use SMTP relay through HestiaCP

**Recommended Fix (Mail Relay):**
```bash
# Option A: Exim4 with SMTP relay
sudo apt install exim4-daemon-light
sudo dpkg-reconfigure exim4-config
# Choose: "mail sent by smarthost; no local mail"

# Option B: Install postfix
sudo apt install postfix -y
# Then configure as satellite/relay

# Recommended: Use SendGrid or similar as relay
# In /etc/exim4/update-exim4.conf.conf:
# dc_smarthost='smtp.sendgrid.net::587'
```

### 2.2 SPF/DKIM/DMARC Status
**Status:** 🟡 MEDIUM
**Finding:** SPF present via Cloudflare Email Routing
- MX points to Cloudflare
- SPF: `v=spf1 include:_spf.mx.cloudflare.net ~all`
- But Cloudflare Email Routing is forwarding-only, not a real mailbox

**Current setup:** admin@ancap.cloud IS a real mailbox (HestiaCP), webmail works at webmail.ancap.cloud
- Mail receiving works (IMAP on 993/143)
- Mail SENDING to external fails (port 25 block)

**Fix:** Configure HestiaCP mail to use authenticated SMTP relay

---

## 3. Website Improvements

### 3.1 UX/UI Issues
**Finding:** Based on the site content analysis:
- Landing page is too abstract — needs concrete paid action CTAs
- No "buy workflow" / "start earning" clear entry point
- Missing social proof (no live stats, no team, no activity)
- No clear roadmap link visible on homepage
- No Discord/Telegram join buttons prominently placed
- Missing OG images / social meta tags for key pages

**Priority Fixes:**
- Add floating "Get Started" button with clear first action
- Add Telegram join button (already have @ancap24news)
- Add live metrics: "wACP in circulation", "Bridge transactions", "Total ACP locked"
- Show first 3 workflow products on homepage with pricing

### 3.2 Missing Content (Based on MONETIZATION_EXECUTION_PLAN)
**Status:** 🟡 MEDIUM
**Finding:** Roadmap monetization doc is thorough but site doesn't reflect it yet:

**Add to site:**
1. `/ai/workflows` — AI Workflow Store (P0)
2. `/developers` — as a product page with pricing tiers
3. `/llms.txt` — AI-readable product catalog
4. `/agent-products.json` — machine-readable catalog
5. `/proof` — Proof Center landing page
6. `/pricing` — clear ACP/wACP pricing page

### 3.3 SEO & Discoverability
**Status:** 🟡 MEDIUM
- No sitemap.xml at /sitemap.xml
- No robots.txt or it's basic
- No structured data (JSON-LD) for AI agents
- Missing Twitter/X card meta tags
- Blog/News section would help SEO

**Quick wins:**
- Add `/sitemap.xml` generation
- Add `/robots.txt`
- Add JSON-LD structured data for main pages
- Add OpenGraph meta tags for social sharing

### 3.4 Missing AI Agent Features
**Status:** 🟢 LOW-MEDIUM (but growing importance)
- No MCP server endpoint
- No `/llms.txt` for AI indexing
- No `/agent-products.json` for agent discovery
- These would attract AI agents to use the platform

---

## 4. Security Hardening

### 4.1 API Keys in Docs
**Status:** 🔴 HIGH
**Finding:** provider-specific API key examples were documented in tracked docs
**Fix:** Remove provider-specific key examples from all tracked docs. Store secrets only in `.env` / secret managers.

### 4.2 CORS Wide Open
**Status:** 🟡 MEDIUM
**Finding:** `allow_origins=["*"]` in production
**Fix:** Restrict to known domains in production

### 4.3 Production secret defaults
**Status:** 🟡 MEDIUM
**Finding:** production startup must not rely on dev fallbacks or partially supplied compose env
**Fix:** Ensure a real `DATABASE_URL` (not insecure local bundled-db defaults; if it targets the bundled compose `postgres` service, it must include the real DB password, not a placeholder-like password, and that password must match `POSTGRES_PASSWORD`), a real `POSTGRES_PASSWORD` for that service, plus real random `SECRET_KEY`, `CURSOR_SECRET`, and `CRON_SECRET` values (not placeholder-like strings) are supplied from host env / repo-root `.env` in production and fail fast when missing or inconsistent

### 4.4 No Rate Limiting
**Status:** 🟡 MEDIUM
**Finding:** No rate limiting on public API endpoints
**Fix:** Add nginx rate limiting or FastAPI middleware

---

## 5. Monetization Quick Wins

### 5.1 Landing Page Repositioning
- Change hero from "AI-native capital allocation platform" to **"AI workflows for crypto teams — pay in ACP, get verified results"**
- Add 3 CTA buttons: "Launch a Workflow", "Explore Marketplace", "Read the Docs"
- Show the 5 workflow products with prices immediately

### 5.2 First 5 Sellable Workflows
From ROADMAP-MONETIZATION.md:
1. **Token Listing Pack** — listing requirements, contract checks, docs
2. **Crypto Campaign Builder** — launch checklist, KOL list, airdrop rules
3. **Telegram Growth Kit** — bot setup, channel growth tracking
4. **Airdrop/Bounty Builder** — rules, distribution, anti-sybil
5. **Token Risk Report** — holder analysis, trust score

### 5.3 Proof Center
- Every paid run produces a shareable receipt URL
- Include: workflow slug, price, input hash, status timeline, output
- Make readable by humans AND external AI agents

### 5.4 AI Agent Discovery
```bash
# Create these on the server:
/llms.txt — markdown file listing all public endpoints and products
/agent-products.json — machine-readable catalog of paid API endpoints
```

---

## 6. OpenClaw Integration

### 6.1 Verify OpenClaw Gateway on Server
- Port 18789 is LISTENING on localhost (from ss output: `127.0.0.1:18789`)
- Port 18791 is also listening
- Need to verify: is openclaw gateway actually running?

### 6.2 Deploy OpenClaw Config
- Copy `ancap-openclaw-server.json5` to `~/.openclaw/openclaw.json`
- Set correct TenetaAI API key
- Test with `openclaw status`
- Verify Telegram bot responds

### 6.3 Telegram Bot Testing
- Bot: @ancap47_bot
- Verify DM policy works (currently `allowlist` with user ID 6018675386)
- Verify group policy works (requireMention)

---

## 7. Docker & Infra Cleanup

### 7.1 Image Prune (Free ~3GB)
```bash
docker image prune -a -f
docker builder prune -a -f
docker volume prune -f
```

### 7.2 Check for Unused Containers
- `docker ps -a` shows all containers
- Remove any stopped containers: `docker container prune -f`

### 7.3 Disk Alert
Set up monitoring for disk > 80%:
```bash
# Add to crontab
0 */6 * * * df -h | awk '$5 > 80 {system("echo Disk warning | wall")}'
```

---

## 8. GitHub Actions / CI Check
- Verify `.github/workflows/` pipelines are working
- Check if tests run on PRs
- Consider adding: server deploy workflow, security audit workflow

---

## Summary: Execute Order

| Priority | Task | Owner | Time |
|----------|-------|-------|------|
| P0 | Install fail2ban + UFW | ARDO | 30 min |
| P0 | Fix `/v1/system/jobs/tick` protection | ARDO | 15 min |
| P0 | Remove API keys from docs | ARDO | 5 min |
| P0 | Docker image prune (free disk) | ARDO | 10 min |
| P0 | Fix mail delivery (SMTP relay) | ARDO | 60 min |
| P1 | Update packages | ARDO | 15 min |
| P1 | Add Idempotency-Key | ARDO | 2h |
| P1 | Landing page CTAs | openclaw | 2h |
| P1 | `/ai/workflows` page | openclaw | 3h |
| P1 | OpenClaw server deployment | ARDO+openclaw | 1h |
| P2 | `/llms.txt` + agent catalog | openclaw | 1h |
| P2 | Proof Center page | openclaw | 2h |
| P2 | CORS restriction | ARDO | 15 min |
