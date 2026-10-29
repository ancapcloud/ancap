# Robinhood ACP (rACP)

Operator-approved parameters: **10,000,000 rACP** against an exclusive
**1,000,000 ACP** reserve; **1 ACP = 10 rACP**; 18 decimals.
This is a custodial receipt, distinct from BSC wACP. No automatic cross-chain
verification or ACP payout service is implemented in this change.

## Mainnet deployment — 2026-10-30

- Network: Robinhood Chain, chain ID 4663; gas: ETH.
- Contract: `0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911`.
- Deployment transaction: `0x4d7f241ab01eb00d95f68ca6daf3839700b797b685d25df2dedef2a3a7618a53`.
- Block: 101270941; fee: **0.00003171607548 ETH**.
- Issuer/recipient: `0x396351dF6420e6089dC67F4CBdDc717f34fFB2e4`.
- Initial supply: **0**. Issuance has **not** occurred; backing is **not funded**.
- Dedicated reserve: `acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz`.
- Reserve keystore is stored privately on the existing ANCAP server under
  `~/.ancap/racp-reserve/`, directory mode 0700, keystore mode 0600.
  It must be backed up securely before funding. Never commit it or expose it through API.
  A private backup was saved locally under the ignored `Sicret/robinhood-racp/` directory.

The source account's internal platform balance and native ACP wallet balance are
different quantities. The native wallet has sufficient ACP at preflight; the
internal ledger does not have 1,000,000 ACP. No ledger debit, native transfer or
reserve claim was made. Native signing requires the user's wallet password;
the platform recovery flag is disabled. Use the authenticated wallet flow to
transfer 1,000,000 ACP to the dedicated reserve, retaining ACP for the network fee.
Never provide the password in chat or replace this step with an unbacked ledger credit.

## Contract behavior

`issueAgainstReserve(bytes32 evidence)` may be called **once**, only by the
immutable issuer. It issues the entire cap to the immutable recipient. Burning
does not restore mint capacity. Evidence is a nonzero reference attested by the
issuer; Solidity does not verify the native ACP chain. Operators must independently
verify the exclusive reserve and archive the confirmed transfer before calling it.

`requestRedemption(amount, acpAddress)` burns tokens and emits a request. It does
not transfer native ACP. A supervised payout/reconciliation service remains to
be implemented before promoting redemption as available. Amounts must map exactly
to native ACP's 8 decimals (multiples of 10^11 token base units). Destination string
syntax/ownership must be checked by the operator before any payout.

## Build and validation

```powershell
npm ci --ignore-scripts
docker run --rm --entrypoint forge -v C:/Users/drago/Desktop/ANCAP/contracts/robinhood-racp:/work -w /work ghcr.io/foundry-rs/foundry:v1.3.1 test -vv
node verify-runtime.mjs
```

Four contract tests cover zero initial supply, restricted one-time issuance,
cap after redemption, ERC-20 transfers and invalid redemptions. The backend test
`tests/test_racp_catalog.py` ensures rACP cannot enter quote/settlement pairs.
Catalog status remains planned until funding, issuance and redemption readiness.

`prepare-deployment.mjs` only prepares an unsigned creation transaction.
`deploy.mjs --broadcast` checks chain/signer and records an intent before sending;
its journal prevents an accidental second deployment on retry. Mainnet deployment
has already completed: do not remove the journal or deploy another token.
The existing signer env file is accessed only in memory; no private key is in artifacts.

Explorer source verification was attempted but blocked by its Cloudflare challenge.
`prepared/standard-input.json`, compiler 0.8.24, optimizer 200, EVM paris, and
constructor `(issuer, recipient)` are available for manual explorer verification.
Runtime bytecode is checked independently against local compilation by
`verify-runtime.mjs`; that check is distinct from explorer source verification.

## Remaining steps

1. Securely back up the reserve keystore and transfer/confirm the 1,000,000 ACP reserve.
2. Record native reserve transfer hash and confirmed balance; prohibit reuse as wACP backing.
3. Archive evidence, then call `issueAgainstReserve` with its nonzero reference and verify recipient balance.
4. Implement authenticated, idempotent redemption payouts and reserve reconciliation.
5. Deploy the catalog change and enable trading only after the relevant service checks.

Network details: https://docs.robinhood.com/chain/connecting/
Contract: https://robinhoodchain.blockscout.com/address/0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911
