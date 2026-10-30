> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Official contract-address and verification index

Status: public-safe reference for the currently documented ACP / wACP / bridge identities.

Use this page as the fast index for the official public contract surfaces, explorer links, and verification pointers.
For deployment-story context, see [bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md).
For source/build verification, see [CONTRACT_VERIFICATION_GUIDE.md](./CONTRACT_VERIFICATION_GUIDE.md).
For operational trust boundaries and bridge risk posture, see [BRIDGE_RISK_DOCUMENTATION.md](./BRIDGE_RISK_DOCUMENTATION.md).

## Critical warning

Treat any token, contract, pool, or social post that does **not** match the addresses on this page as untrusted until verified.

Especially important:
- native **ACP** is **not** an ERC-20/BEP-20 contract;
- the official wrapped BSC asset is **`wACP`**, not an arbitrary token using similar branding;
- verify the full address, not only the symbol, name, or logo;
- cross-check contract source and runtime status before treating a surface as official.
- MetaMask education (add official token / spot fakes): live page `/docs/wacp/metamask` — ANCAP cannot remotely delete tokens from a user’s wallet.

## Official identities

### Native ACP

ACP is the native ANCAP chain asset.
It does **not** have an EVM contract address on the ANCAP chain.

Current public identity surfaces:
- mainnet chain id: `acp-mainnet-1`
- testnet chain id: `acp-testnet-1`
- default numeric chain id in the current ACP docs/tooling: `1001`
- native address format: `acp1...`
- ACP chain landing/status surface: <https://ancap.cloud/acp>
- ACP transaction-view pattern used by the bridge docs/UI: `https://ancap.cloud/acp/tx/<txid>`

Reference docs:
- [ACP crypto-asset whitepaper](./WHITEPAPER_ACP.md)
- [ACP crypto README](../ACP-crypto/README.md)

### BSC mainnet — wrapped ACP contract

Official wrapped token:
- contract: `WACP`
- network: `BSC mainnet`
- bridge ratio: **1 ACP ↔ 10 wACP** (cutover 2026-10-04; see [bridge-spec-v1.md](./bridge-spec-v1.md))
- address: `0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402`
- explorer: <https://bscscan.com/address/0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>
- source: [contracts/bridge-bsc/src/WACP.sol](../contracts/bridge-bsc/src/WACP.sol)
- **BscScan token-update icon (32×32 SVG, direct download URL):** <https://ancap.cloud/wacp-logo-32.svg>
- alias (same file): <https://ancap.cloud/icons/wacp-32.svg>
- PNG fallback (not for the BscScan SVG field): <https://ancap.cloud/wacp-logo.png>
- **Whitepaper (BscScan / public):** <https://ancap.cloud/whitepaper/acp>
- whitepaper aliases: <https://ancap.cloud/whitepaper/wacp>, raw markdown <https://ancap.cloud/whitepaper/acp.md>
- BscScan update form: <https://bscscan.com/tokenupdate/0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402>

### BSC mainnet — bridge gateway contract

Official bridge gateway:
- contract: `BridgeGateway`
- network: `BSC mainnet`
- address: `0x57c24FF77B23a82328cb88914D4FD4EEBd93321b`
- explorer: <https://bscscan.com/address/0x57c24FF77B23a82328cb88914D4FD4EEBd93321b>
- source: [contracts/bridge-bsc/src/BridgeGateway.sol](../contracts/bridge-bsc/src/BridgeGateway.sol)

## Related public trust surfaces

Use these together with the addresses above:
- bridge pilot deployment story: [bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md)
- build/source verification process: [CONTRACT_VERIFICATION_GUIDE.md](./CONTRACT_VERIFICATION_GUIDE.md)
- bridge risk/trust model: [BRIDGE_RISK_DOCUMENTATION.md](./BRIDGE_RISK_DOCUMENTATION.md)
- testnet validation path: [TESTNET_DEPLOYMENT_GUIDE.md](./TESTNET_DEPLOYMENT_GUIDE.md)
- bridge UI/status surface: <https://ancap.cloud/bridge/acp-bsc>
- bridge status API: <https://ancap.cloud/api/v1/bridge/status>
- reserve summary API: <https://ancap.cloud/api/v1/bridge/reserve-summary>
- reserve proof API: <https://ancap.cloud/api/v1/wacp/reserve-proof>

### PancakeSwap markets (wACP / USDT)

- **V2 canonical (thin reference / checkout oracle):** `0xF391ca2bcBaB93Afa23326ebF1e35DB950841601` — [pool UI](https://pancakeswap.finance/liquidity/pool/bsc/0xF391ca2bcBaB93Afa23326ebF1e35DB950841601)
- **V3 bootstrap (shallow, 0.25%):** `0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1` — [pool UI](https://pancakeswap.finance/liquidity/pool/bsc/0xe626bd3ef516c4f784e5d5fb46e297d9c0d7f5e1)
- **Oracle gate:** keep `WACP_ORACLE_USE_V3=false` until quote smoke ($100/$250/$500) is acceptable — playbook [WACP_LIQUIDITY_V3_PLAYBOOK.md](./WACP_LIQUIDITY_V3_PLAYBOOK.md)
- Spend → fee path: [GOLDEN_PATH_ACP_SPEND.md](./GOLDEN_PATH_ACP_SPEND.md)
- wACP on BSC uses **18 decimals** ([WACP.sol](../contracts/bridge-bsc/src/WACP.sol))

## Fast verification flow

1. Confirm the address matches this page exactly.
2. Confirm the same address appears in [bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md).
3. Open the explorer link and compare the verified source/interface with the repo source.
4. Follow [CONTRACT_VERIFICATION_GUIDE.md](./CONTRACT_VERIFICATION_GUIDE.md) to rebuild/test from source.
5. Check runtime truth via bridge status and reserve surfaces.
6. If anything disagrees, treat the surface as suspect until the public docs are reconciled.

## Fake-contract / scam checks

Red flags:
- a token claims to be "ACP" on BSC instead of the wrapped asset name `wACP`;
- a contract uses a similar symbol/logo but a different address;
- a listing links only to chat posts, screenshots, or marketing pages instead of this repo and explorer pages;
- the source code cannot be tied back to the public repo and documented deployment story;
- runtime status or reserve docs do not line up with the contract being promoted.

## Maintenance rule

If the official public contract surfaces change, update all of the following together:
- this page;
- [bridge-pilot-mainnet.md](./bridge-pilot-mainnet.md);
- [CONTRACT_VERIFICATION_GUIDE.md](./CONTRACT_VERIFICATION_GUIDE.md);
- [CHANGELOG_PUBLIC.md](./CHANGELOG_PUBLIC.md) when the change is externally meaningful.
