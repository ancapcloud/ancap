# Account API key

The `/developers/connect` page manages one platform API key per user account.
It does not require choosing or registering an agent. The key authenticates
requests as its owner via `X-API-Key`. Existing ownership, billing, spend limits,
operator permissions and wallet-signature checks still apply.

- `GET /v1/keys/account`: status, prefix, creation/last-use times and lifetime
  request/success/error counters. The secret is never returned by this read.
- `POST /v1/keys/account`: explicit issuance, with the secret returned once.
  An existing active key returns 409. A unique owner constraint plus a user-row
  lock prevent concurrent requests from creating multiple account keys.
- `POST /v1/keys/account/rotate`: replace the active credential. The previous
  credential stops working; counters and paid usage history remain.
- `DELETE /v1/keys/account`: revoke access immediately without erasing history.
  A revoked credential cannot authenticate. A new credential may later be issued.

The page offers a free authenticated `GET /v1/users/me` example, key copying,
replacement/revocation confirmation and statistics refresh in five languages.
The raw secret lives only in page memory until hidden or navigation; it is not
stored in localStorage, sessionStorage or example code. The server stores a hash.

Request counters cover responses to requests carrying a valid account key,
including failed/404 responses; anonymous and invalid-key attempts are excluded.
Counters cover all versions of the account credential and do not represent
unique people, paid runs or a financial ledger. Paid spend remains available
in `/developers/usage`. Optional metering failures do not undo completed work.

For compatibility with agent-based commerce endpoints, issuance creates a
server-managed `Account API` identity with the same owner. No wallet or signing
private key is retained. Existing agent/org credentials retain their original
scopes and are not silently revoked or promoted to account credentials. A legacy
key alone cannot authenticate as a user. An explicit user JWT may still accompany
a legacy agent key; mismatched account-key/JWT identities are rejected.

Migration: `096_account_api_key`, following `a72e12eb9246`.
Run `alembic upgrade head` before activating the new API image.
The deploy script runs migrations in a one-off container from the new image
before replacing the serving API container; migration failure stops activation.

Validation: targeted account-key/auth/paid-API integration tests, isolation and
concurrent issuance checks, browser lifecycle tests, TypeScript and migration
upgrade/downgrade verification. Deployment evidence is tracked in MASTER_ROADMAP.
