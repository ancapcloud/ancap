# Protection against recruitment malware and compromised AI tools

Updated 2026-11-04. Threat: an interview assignment, package, PDF or cloned
repository executes on a credential-bearing workstation, then uses AI/dev tools
to reach deployment identities and signing keys. Background:
[ACSC Contagious Interview advisory](https://www.cyber.gov.au/advisory/north-korean-waterplum-commonly-referred-to-as-contagious-interview-cyber-actor-group-targeting-it-professionals).

## Implemented code controls

- All three backend walletd wrappers use `app/services/walletd_process.py`.
  Signing material travels through a bounded JSON stdin request, not process
  arguments. The child receives only an explicit OS/TLS/RPC environment
  allowlist; provider, GitHub, wallet env secrets, proxy and loader hooks are
  excluded. Helper failures never echo stdout, stderr or the supplied secret.
- Production walletd uses an absolute root-owned executable that is not
  group/world writable. The production default is `/usr/local/bin/walletd`.
  Deploy the Rust helper and Python caller together. Never downgrade only the
  helper: older walletd binaries cannot understand `--request-stdin`.
- Backend CI does not expose a job-wide GitHub token or persisted checkout
  credentials to packages/tests. The protected release gate retains its own
  scoped read token; no release/security check is disabled.
- `scripts/review_untrusted_code.py` stages a filtered copy and runs a Python
  assignment in a disposable, unprivileged, no-network, read-only container.
  It excludes dotfiles, credential/key filenames, secret directories, symlinks,
  junctions and hardlinks. No install hooks, host environment, SSH agent,
  clipboard or Docker socket are forwarded. Source/output/resources/time are
  bounded; terminal controls are escaped. The image must already exist under
  an immutable ID. There is no host execution fallback.
- `scripts/harden_openclaw.py` validates with the installed OpenClaw schema,
  preserves credentials, backs up config privately, and confines tools to
  per-session Docker workspaces. `all` sessions, no host workspace, no network,
  no elevated/host/browser/gateway/node/scheduler controls. Both global and
  configured per-agent overrides are hardened. The gateway still runs on the
  host: this is not isolation of a compromised gateway or trusted plugin.

## Running an external assignment

Use an existing trusted Python image, not an image supplied by the recruiter:

```powershell
$reviewImage = docker image inspect python:3.11-slim --format '{{.Id}}'
python scripts/review_untrusted_code.py C:/Review/assignment main.py --image $reviewImage
```

Review the source as text first. Do not double-click its PDF/scripts, execute
its IDE tasks, enable macros, run `npm install`, accept a fake meeting update,
or load its editor extensions on the host. If it requires additional packages,
review and build a separate trusted image without secrets; do not enable guest
networking as a shortcut. Containers reduce risk, not eliminate kernel/VM risks.
Windows Sandbox or a dedicated disposable VM is preferable for arbitrary GUIs
and non-Python assignments. An antivirus result is not approval to run code.

## Theodore / OpenClaw

```powershell
python scripts/harden_openclaw.py --image $reviewImage              # plan only
python scripts/harden_openclaw.py --image $reviewImage --apply
openclaw gateway restart
openclaw sandbox explain --json
```

On 2026-11-04 the inspected configuration had `tools.profile=full` and
`sandbox.mode=off`, with writable shared host workspace access. A hardened
configuration was applied locally after schema validation. `sandbox explain`
confirmed `sessionIsSandboxed=true` for `agent:main:main`, isolated workspace and
elevated access disabled. Gateway restart could not identify an installed Windows
task; no gateway was listening on configured loopback port 18789 at the check.
No new background service was installed or started. Recheck containment when the
operator next starts the gateway. The agent no longer has general
host execution, arbitrary host files, deployment credentials or outbound tools.
Gateway normal model/chat transport is separate from the guest's disabled network.
The minimal existing Python image supports Python/shell review; Node/Rust builds
need a separately reviewed prebuilt sandbox image, not a return to host execution.
Source transfers into the sandbox must omit secrets and ignored/private files.
Check effective policy after a runtime change; explicit session opt-outs or an
operator overriding host permissions must never be treated as secure containment.

Config backups contain credentials: keep them outside Git and restrict Windows
ACLs to the current operator and SYSTEM. A Docker socket must never be mounted
inside the guest. Sandbox failure must fail closed, not invoke host tools.

## Isolated signer: prepared, not activated in production

`signer/worker.py` is a separate ACP-only worker intended for an independent
clean VM/host. It is deliberately not registered as a public API or MCP tool.
It reads a bounded JSON envelope from stdin under a forced SSH command.

- Accepted operation is exclusively `acp_transfer`: request UUID, policy hash,
  key id, native chain, destination, integer base-unit amount/fee and expiry.
  No arbitrary bytes, EVM transaction, typed-data, permit, delegation, key export
  or caller-selected RPC/keystore path is accepted.
- Policy fixes the RPC, native chain id, source wallet, key file, fee ceiling,
  per-operation and daily limits. walletd checks the RPC chain id and source
  address before signing. An approval signs the complete canonical intent and
  policy hash under a domain-separated Ed25519 message, valid at most five minutes.
- Manual approval is the default. Explicitly enabled automation additionally
  requires an exact destination allowlist and positive caps. The example policy
  has zero caps, so it cannot spend. Real limit values require the owner's policy;
  no accounting/display conversion is used to invent a token market price.
- Private SQLite storage reserves daily budgets transactionally before signing.
  Valid unexpired replays return recorded state, conflicting reuse of a UUID is denied. Pending
  or uncertain sends continue consuming the budget. A crash/timeout does not
  authorize retry or budget release; reconcile on-chain under operator control.
- The caller receives status/txid, not raw signatures or signing keys. SQLite is
  a durable record on the independent host, not an externally tamper-proof log.

Prepare a dedicated operator approval key **on the clean operator device**:

```text
python -m signer.approve_intent --private-key /private/approval.pem --init-key
python -m signer.approve_intent --private-key /private/approval.pem --policy policy.json --intent intent.json --output approved.json
```

The key is encrypted with a prompted password. This is an approval key, not a
wallet key. Review exact destination, native units, fee, policy hash and expiry
on that device. Do not copy its private key to the workstation/API/signer host.
An independent phone/passkey interface is not implemented; the offline tool
requires a clean operator computer. No hardware/HSM assurance is claimed.

On the new host install reviewed code and walletd with a separate deploy identity.
Use a dedicated unprivileged `ancap-signer` user. Keep code/policy/keystore
root-owned, not group/world writable; grant that user read access to its one
keystore and RPC token, and write access only to `/var/lib/ancap-signer/state`.
Do not install LLM tools, browsers, npm projects or general development jobs there.
The API/AI deploy key must not administer the signer host.

Example dedicated SSH authorized key (replace the public key; no private keys):

```text
restrict,command="/opt/ancap-signer/venv/bin/python -m signer.worker --policy /etc/ancap-signer/policy.json --database /var/lib/ancap-signer/state/requests.sqlite3 --walletd /usr/local/bin/walletd" ssh-ed25519 REPLACE_WITH_DEDICATED_CALLER_PUBLIC_KEY
```

Set a fixed working directory containing the installed `signer` package in the
forced-command launcher. Disable password/interactive access for this identity,
all forwarding and PTY; restrict its ingress to the dedicated operations worker.
Do not give the API container that caller key. Test access/rejection before any
firewall change so the operator retains an independent recovery path.

## Remaining deployment gates

The operator confirmed the independent signer host and operator device still
need preparation. No production key has been moved, regenerated or rotated.
The current API still has its legacy `Sicret` mount and local custodial signing.
The new worker therefore is **not yet a live signing boundary**.

1. Prepare the independent host/device, recovery backups and owner-set caps.
2. Verify source address and chain against existing holdings; test fake-key
   requests, concurrency, timeouts and recovery on an isolated chain.
3. Add a narrow authenticated operations-worker adapter; never accept raw
   signing payloads from an LLM/MCP/requester. Add separate typed adapters for
   rACP vouchers, redemption/referrals and historical bridge obligations before
   claiming those keys isolated. Existing voucher/payout types are not covered
   by the ACP worker.
4. Reconcile pending transactions and cut over one rail at a time. Remove its
   raw key/env/mount from the API, LLM jobs and development/CI identities. Keep
   reading, account balances and historical obligations intact. Roll back by
   pausing payouts; do not restore broad key mounts as a routine fallback.
5. With all adapters migrated, remove the broad API secret-directory mount and
   use only per-service read-only secret files. Independently verify denial from
   the API/AI/workstation identities before marking signer isolation complete.
6. Configure production deployment approval on an independent device and
   least-privilege deploy identities. No unattended bypass of branch/environment
   approval is permitted for signer/policy changes.

## Endpoint and incident acceptance

`scripts/security_host_audit.ps1` is read-only. The inspected Windows 11 Pro
host reported Defender disabled and also registered 360 Total Security; this
does not establish that another AV is healthy. This process is not administrator.
Verify the installed product's active protection, updates and tamper protection
in its own UI before changing AV or Windows application-control settings.
Do not disable one product or add code/checkout exclusions to make development work.
WDAC/AppLocker and Windows Sandbox activation require an administrator and remain
separate acceptance gates; no such OS lockdown is claimed by repository changes.

On suspected execution: isolate the endpoint from trusted systems, stop new
signing/automation, revoke the affected account/deploy/provider sessions from a
clean device, preserve logs and independently reconcile outstanding transactions.
Stopping the service does not invalidate already broadcast transactions or EVM
delegations; handle those explicitly with the appropriate independent keys.

Acceptance evidence must distinguish local unit tests, real container isolation,
effective OpenClaw runtime, GitHub CI, production deployment and the independent
host cutover. Green CodeQL alone closes none of the host/custody gates above.
