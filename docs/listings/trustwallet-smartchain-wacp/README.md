> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# Trust Wallet Assets pack — wACP (BSC)

Ready-to-copy folder for a community PR to [`trustwallet/assets`](https://github.com/trustwallet/assets).

## Target path in upstream repo

```text
blockchains/smartchain/assets/0x349797E2f1A4FD722Af2dB181ab1C4ED7606F402/
  info.json
  logo.png
```

## Steps

1. Fork `trustwallet/assets`
2. Copy this directory to the path above (checksum address casing as used by Trust Wallet tooling)
3. Prefer a clean **256×256** PNG for `logo.png` if reviewers reject the current asset
4. Open PR following Trust Wallet contribution guidelines
5. After merge, wallets that use Trust assets will show the wACP logo automatically

This is free and permissionless to *propose*; merge is still at Trust Wallet maintainers’ discretion.
