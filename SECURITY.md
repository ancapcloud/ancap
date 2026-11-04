# Security Policy

Developer/recruitment malware, AI tool isolation and custody cutover:
[operational controls and remaining gates](docs/DEVELOPER_SOCIAL_ENGINEERING_DEFENSE.md).

## Security boundary

ANCAP aims to be open-source where transparency increases trust, integration, and adoption.

However, the following remain private and must never be published in public issues, PRs, docs, or examples:
- private keys
- seed phrases / mnemonics
- bridge signer logic and operational controls
- admin wallets
- production `.env` values
- deploy secrets and tokens
- real RPC / API credentials
- hot-wallet operational internals
- sensitive anti-fraud thresholds that would materially help abuse

## Reporting a vulnerability

Please report security issues responsibly.

Preferred report contents:
- affected component
- impact
- reproduction steps
- proof-of-concept if safe
- suggested mitigation if known

Private vulnerability reporting is enabled for this repository. Use GitHub's
[Report a vulnerability](https://github.com/ancapcloud/ancap/security/advisories/new)
to share a report privately with the maintainers. Do not include reproduction
details, credentials or sensitive production data in a public issue or PR.

## Disclosure policy

- Do not publish exploit details before the issue is triaged and mitigated.
- Give maintainers time to reproduce and patch.
- If a secret may have leaked, assume compromise and rotate/revoke it immediately.

## Scope examples

In scope:
- auth bypass
- privilege escalation
- secret exposure
- insecure defaults in production paths
- unsafe wallet / bridge / receipt handling
- chain settlement integrity issues
- injection / SSRF / unsafe deserialization / RCE risks

Out of scope unless there is a concrete exploitable path:
- generic best-practice suggestions without a demonstrated project-specific weakness
- purely theoretical attacks with no plausible exploit chain

## Hard rule

Never commit real secrets to the repository. If you discover one, stop and rotate/revoke it first.

Operator follow-through checklist: [docs/SECRET_ROTATION_RUNBOOK.md](docs/SECRET_ROTATION_RUNBOOK.md)

## External dependency advisories (operator)

- **2026-09-11 — GitLab CVE-2026-85706 (CVSS 10):** self-managed GitLab path traversal / unauthenticated file read when a public project exists. **ANCAP stack (GitHub + SourceCraft) is not affected.** Operator note: [docs/GITLAB_CVE_2026_85706.md](docs/GITLAB_CVE_2026_85706.md).
