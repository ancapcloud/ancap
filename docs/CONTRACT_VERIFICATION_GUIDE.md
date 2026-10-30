> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Contract verification guide

Public-safe process for verifying the published `wACP` and `BridgeGateway` contract sources against ANCAP bridge deployments.

Related files:
- [OFFICIAL_CONTRACT_ADDRESSES.md](./OFFICIAL_CONTRACT_ADDRESSES.md)
- [contracts/bridge-bsc/src/WACP.sol](../contracts/bridge-bsc/src/WACP.sol)
- [contracts/bridge-bsc/src/BridgeGateway.sol](../contracts/bridge-bsc/src/BridgeGateway.sol)
- [contracts/bridge-bsc/README.md](../contracts/bridge-bsc/README.md)
- [bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md)
- [bridge-github-workflow.md](./bridge-github-workflow.md)

## Goal

Anyone reviewing ANCAP should be able to confirm that:
- the published Solidity source matches the intended bridge contracts;
- the build artifacts are reproducible from the repo;
- deployed addresses can be tied to a documented release/tag and runtime state.

## What to verify

Minimum verification set:
- source files:
  - `contracts/bridge-bsc/src/WACP.sol`
  - `contracts/bridge-bsc/src/BridgeGateway.sol`
- deployment script:
  - `contracts/bridge-bsc/script/Deploy.s.sol`
- tests:
  - `contracts/bridge-bsc/test/BridgeGateway.t.sol`
  - `contracts/bridge-bsc/test/DeployPrediction.t.sol`
- deployment/runtime docs:
  - `contracts/bridge-bsc/README.md`
  - `docs/bridge-pilot-mainnet.md`

## Rebuild locally

From repo root:

```bash
cd contracts/bridge-bsc
forge install foundry-rs/forge-std@v1.9.4
forge test -vvv
forge build
```

Docker alternative:

```bash
docker run --rm -v "$(pwd):/repo" -w /repo/contracts/bridge-bsc ghcr.io/foundry-rs/foundry:latest /bin/bash -lc "git config --global --add safe.directory /repo && forge install foundry-rs/forge-std@v1.9.4 && forge test -vvv && forge build"
```

Expected result:
- tests pass;
- build artifacts are generated under `contracts/bridge-bsc/out/`.

## Compare deployed contracts

For each declared deployment address:
1. confirm the address appears in a public ANCAP bridge doc or release note;
2. inspect contract bytecode / verified source on the relevant block explorer;
3. compare ABI-relevant functions/events with repo source;
4. confirm the deployment story matches the documented runtime state.

At minimum compare:
- token metadata and gateway wiring for `WACP`
- pause/admin/mint-cap/release surfaces for `BridgeGateway`
- `ReleaseRequested` event semantics
- the addresses in [OFFICIAL_CONTRACT_ADDRESSES.md](./OFFICIAL_CONTRACT_ADDRESSES.md) against both the explorer pages and the documented pilot deployment story

## Release evidence to preserve

Each public bridge release or pilot checkpoint should preserve:
- release tag name
- deployed contract addresses
- relevant Alembic head revision
- API/frontend revision or commit hash
- BSC network identifier (testnet/mainnet)
- date of verification

Recommended tag examples:
- `bridge-v1.0.0-testnet`
- `bridge-v1.0.0-mainnet`

## Mainnet pilot references

Current documented pilot addresses live in:
- [docs/bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md)

Treat that file as the public pointer to the latest documented bridge deployment story unless a newer release note supersedes it.

## Things that must stay private

Do **not** publish any of the following in verification materials:
- deployer private keys
- operator secrets
- mnemonic phrases
- raw secret-store exports
- privileged internal RPC credentials

## Review verdict template

A minimal public verification note should answer:
- Which repo commit/tag was reviewed?
- Which addresses were checked?
- Did local Foundry build/tests pass?
- Do the published sources match the deployed contract interfaces/behavior?
- Which open risks remain operational rather than source-level?
