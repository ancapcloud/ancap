> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Public integration examples

Contributor-friendly index for the current public-safe ANCAP example surfaces.

Use this page when you want one place to inspect the first publishable payment, wallet, and bridge-facing references without browsing the whole monorepo tree.

## Payment example

- [Examples landing page](../examples/README.md)
- [Stripe credit top-up example](../examples/payment-integration/python_credit_topup.py)
- [Payment example README](../examples/payment-integration/README.md)

What it demonstrates:
- authenticate with an ANCAP bearer token;
- list available credit packages;
- create a Stripe-backed top-up intent;
- poll the intent until it reaches a terminal state.

## Wallet / auth example

- [Wallet connection example](../examples/wallet-connection/python_wallet_login.py)
- [Wallet connection README](../examples/wallet-connection/README.md)

What it demonstrates:
- request a wallet auth challenge;
- sign the message locally with an EVM key;
- verify the signature;
- confirm the authenticated session with `/v1/users/me`.

## Bridge / contract-facing public references

These are not private operator runbooks. They are the public-safe contract and verification surfaces that integrators and reviewers can inspect alongside the examples.

- [Bridge contract docs](../contracts/bridge-bsc/README.md)
- [wACP contract source](../contracts/bridge-bsc/src/WACP.sol)
- [Bridge gateway contract source](../contracts/bridge-bsc/src/BridgeGateway.sol)
- [Official contract-address index](OFFICIAL_CONTRACT_ADDRESSES.md)
- [Contract verification guide](CONTRACT_VERIFICATION_GUIDE.md)
- [Bridge risk documentation](BRIDGE_RISK_DOCUMENTATION.md)
- [Testnet deployment guide](TESTNET_DEPLOYMENT_GUIDE.md)

## Scope boundary

Public-safe examples belong here.

Do **not** treat this page as approval to publish:
- private keys, bearer tokens, or production `.env` values;
- bridge signer internals or hot-wallet operating procedures;
- private infrastructure/admin runbooks;
- abuse-sensitive controls or operator-only fraud logic.
