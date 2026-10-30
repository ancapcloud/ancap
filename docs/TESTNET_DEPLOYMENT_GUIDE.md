> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Testnet deployment guide

Public-safe deployment guide for validating the ANCAP BSC bridge path on testnet before or alongside mainnet/pilot work.

Related files:
- [contracts/bridge-bsc/README.md](../contracts/bridge-bsc/README.md)
- [docs/bridge-github-workflow.md](./bridge-github-workflow.md)
- [docs/OFFICIAL_CONTRACT_ADDRESSES.md](./OFFICIAL_CONTRACT_ADDRESSES.md)
- [docs/CONTRACT_VERIFICATION_GUIDE.md](./CONTRACT_VERIFICATION_GUIDE.md)

## Goal

Produce a repeatable testnet checkpoint that proves:
- bridge contracts can be built and deployed from repo source;
- ANCAP API/runtime can target those addresses safely;
- at least one small end-to-end bridge flow works on a non-mainnet chain.

## Scope

This is a **public-safe** guide. It explains the flow, required artifacts, and verification expectations without exposing private keys or internal operator secrets.

## Recommended prerequisites

- Foundry installed locally, or Docker access for Foundry container builds
- BSC testnet RPC URL
- funded testnet deployer wallet
- isolated non-production operator secrets
- ANCAP API/runtime environment prepared for testnet addresses

## Step 1 — build and test contracts

```bash
cd contracts/bridge-bsc
forge install foundry-rs/forge-std@v1.9.4
forge test -vvv
forge build
```

Expected result:
- tests pass;
- fresh artifacts exist in `contracts/bridge-bsc/out/`.

## Step 2 — deploy to BSC testnet

From repo root or `contracts/bridge-bsc` environment:

```bash
export PRIVATE_KEY=...   # testnet-only deployer key
export BSC_RPC_URL=...   # BSC testnet RPC
forge script script/Deploy.s.sol:DeployScript \
  --rpc-url "$BSC_RPC_URL" \
  --broadcast -vvv
```

Record at minimum:
- deployment date
- git commit / tag
- `WACP` address
- `BridgeGateway` address
- network name + chain id

## Step 3 — wire runtime to testnet contracts

Prepare a non-production runtime config with:
- testnet RPC URL
- deployed `WACP` address
- deployed `BridgeGateway` address
- isolated bridge operator secret
- isolated BSC private key
- explicit dry-run / enabled / pause settings appropriate for the test phase

Do not reuse production secrets for testnet validation.

## Step 4 — smoke-check runtime surfaces

Verify at minimum:
- `GET /api/v1/system/health`
- `GET /api/v1/bridge/status`
- `GET /api/v1/bridge/reserve-summary`
- `POST /api/v1/system/jobs/tick`
- bridge UI route loads if frontend is part of the test checkpoint

Expected result:
- runtime reports the intended testnet addresses/config;
- bridge is either safely paused for setup or explicitly enabled for the test window;
- no stale mainnet addresses remain in the test environment.

## Step 5 — run a small end-to-end test

Recommended minimal test:
1. create a fresh bridge intent;
2. perform the ACP-side action required by the current test setup;
3. let orchestrator/watchers advance the flow;
4. confirm BSC mint or release event on testnet explorer;
5. verify API/UI status matches chain outcome.

## Step 6 — preserve public evidence

For a valid documented testnet checkpoint, publish or retain:
- commit hash or release tag
- deployed testnet addresses
- explorer links
- confirmation that Foundry tests/build passed
- runtime/API revision used
- short verdict: success, partial, or blocked

Recommended release tag pattern:
- `bridge-v1.0.0-testnet`

## Exit criteria

Treat the testnet deployment guide as satisfied when a reviewer can reproduce the intent of the process and inspect public evidence of:
- buildable contracts
- declared addresses
- documented runtime wiring
- at least one validated testnet checkpoint
