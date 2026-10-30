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
- Issued supply: **10,000,000 rACP**. After campaign funding, treasury holds
  **9,000,000 rACP** and the claim pool holds **1,000,000 rACP** before claims.
- Issuance transaction: `0xe9b437c7e2260ae284ae011fdae4699b9bca63e3712997ffad28be8d105334e8`.
- Issuance block: 101282581; fee: **0.000002401664904 ETH**.
- Reserve funded with **1,000,000 ACP**, confirmed in native block 19 (one confirmation at issuance).
- Native funding transaction: `1b369ac2dc6c21c84e1ca798bd5f4059a5c45ea4ca25ef5068042533a77cd0c2`.
- Issuer evidence commitment: `0x9eb3773d3937092df7b67e12c6443d16c7d778e4ed49dd4807ffd94d9642302b`.
- Dedicated reserve: `acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz`.
- Reserve keystore is stored privately on the existing ANCAP server under
  `~/.ancap/racp-reserve/`, directory mode 0700, keystore mode 0600.
  Never commit it or expose it through API.
  A private backup was saved locally under the ignored `Sicret/robinhood-racp/` directory.

The source account's internal platform claims and native ACP wallet balance
are different quantities. A follow-up production audit on 2026-10-30 found that
the personal wallet was incorrectly capped to shared custodial ledger entitlement.
That calculation is now fixed and live-checked: personal total is its native balance,
and available is native balance minus active stake/platform reservations. Custodial
hot entitlement checks remain unchanged. Nine targeted tests passed. The operator
then explicitly approved releasing the shortfall from platform balances/staking.
Three 50,000 ACP stakes were released through the existing staking service; three
200 ACP stakes remain. Ledger withdrawals totalled 259,027.96904192 ACP, leaving
65.999999 ACP liquid platform credits. The native transfer used 0.000001 ACP in fees;
665.999999 ACP remain at the source. A database operation journal and withdrawal
references prevent repeating the release on retry. No funds were minted in the ledger.

`fund-reserve.py` requires the funding user's ID in `RACP_FUNDING_USER_ID` and the
wallet password on stdin, never in files or argv. Default mode is read-only.
The completed funding operation must not be repeated. The reserve proof in
`prepared/reserve-funding.json` is preserved byte-for-byte by `.gitattributes`:
the issuer evidence is its UTF-8 Keccak-256 digest, after removing any BOM.

The partial UTXO index previously returned a false zero for unwatched addresses.
The API now falls back to a live walletd probe for those addresses. Five index tests
passed and the public reserve endpoint was checked against the native node.

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
Catalog status is beta, with no quote/settlement pairs until redemption readiness.
The updated catalog is deployed to the existing production API and was checked at
`/v1/mobile/exchange/catalog`; the public native reserve balance endpoint returns
1,000,000 ACP. Deployment used targeted source/container patches on the existing
server, preserving its other changes; these patches must be retained in subsequent
image builds. Token deployment/issuance are independent on-chain state.

`prepare-deployment.mjs` only prepares an unsigned creation transaction.
`deploy.mjs --broadcast` checks chain/signer and records an intent before sending;
its journal prevents an accidental second deployment on retry. Mainnet deployment
has already completed: do not remove the journal or deploy another token.
The existing signer env file is accessed only in memory; no private key is in artifacts.
`issue.mjs --broadcast` checks the archived proof, current public reserve balance,
issuer/recipient, cap and zero prior issuance, and journals before signing/sending.
Issuance has already completed. Do not remove its journal or attempt another issuance.

Blockscout source verification completed on 2026-10-30 through its standard JSON
form: exact match, Solidity 0.8.24, optimizer 200, EVM paris, MIT. Sourcify also
reports creation/runtime exact matches, match ID 57603340. Archived responses:
`prepared/source-verification.json` and `prepared/sourcify-verification.json`.
The token's separate Blockscout name/logo profile requires account login and has
not been updated; source verification does not imply a profile/listing approval.
Runtime bytecode is independently checked against local compilation by
`verify-runtime.mjs`.

## Remaining steps

1. Preserve the exclusive reserve; prohibit reuse as wACP backing.
2. Implement authenticated, idempotent redemption payouts and continuous reserve reconciliation.
3. Enable trading only after the relevant service checks and a new operator liquidity budget.

## Public distribution — 2026-10-30

Operator liquidity budget: **0**; no pool, LP position or paid listing was created.
The official page `/tokens/racp`, homepage/Markets cards, navigation link, five-language
wallet-import flow, PNG/SVG identity, tokenlist, whitepaper and machine-readable
`/racp-listings.json` are included in the website release. The native ACP wallet
and Robinhood EVM wallet remain distinct; this does not add an automated bridge.

CoinGecko active listing prerequisites require an active market on a tracked venue.
CoinMarketCap tracked listing is deferred until market readiness. Trust Wallet's
directory requires eligibility checks, established activity/audit and a fee; no
fee or approval is claimed. These applications have not been submitted.
Use the status JSON to distinguish live public resources from pending applications.

Official requirements reviewed:
- https://support.coingecko.com/articles/9489827481-how-to-list-a-new-cryptocurrency-on-coingecko?lang=en
- https://support.coinmarketcap.com/hc/en-us/articles/360043659351-Listings-Criteria
- https://developer.trustwallet.com/developer/new-asset/requirements

Network details: https://docs.robinhood.com/chain/connecting/
Contract: https://robinhoodchain.blockscout.com/address/0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911

## Funded opt-in airdrop — 2026-10-30

The operator authorized 1,000,000 existing rACP for free distribution, at most
1,000 per recipient. The chosen fixed allocation is **500 rACP**, up to **2,000**
claims. This allocates existing tokens; it does not mint tokens or move native ACP.
Funding a pool is not a completed transfer to recipients. Live claimed amounts:
https://api.ancap.cloud/v1/racp/airdrop/status

- Claim page: https://ancap.cloud/tokens/racp/airdrop
- Pool: `0x2867D10560b35616370cF5C7A21Ab1532698FD0F`.
- Funding transaction: `0x21dd02d49eba0c48eecf25377144cb93128187983ecb2d05baeccd3a13cc42db`.
- Dedicated voucher signer: `0x5a40eb5b084F24e3d545987403E36cCDf155bdD8`.
- Sourcify creation/runtime exact match: **57606968**.

The recipient authenticates or links their EVM wallet with the existing signed
ANCAP challenge, passes Turnstile, obtains a ten-minute EIP-712 voucher, and submits
the claim. Recipients pay network ETH gas; no token purchase, approval or payment
to ANCAP is required. A relayer cannot redirect a signed allocation. Both account
identity and recipient wallet can claim only once. These restrictions are not
proof of unique humans; multiple accounts/wallets remain a Sybil limitation.

The contract fixes the cumulative budget and amount per claim. The treasury owner
may pause and recover undistributed tokens while paused. A dedicated signer can
only authorize campaign claims; the API never receives the treasury spending key.
No private identity, email address or wallet credential is included in vouchers.
Server paths default to `/run/secrets/racp-airdrop.json` and
`/run/secrets/racp-airdrop-voucher.key` (0600); absent configuration disables issuance.
Never commit either secret file. Preserve `prepared/airdrop-deployment.json` and do
not repeat deployment or funding. Source and funding journals are public artifacts.

Validation includes fixed grants, replay, recipient redirection, account reuse,
contract domain, expired signatures, paused/unfunded rollback, and the full 2,000
claim budget even when overfunded. Python EIP-712 digests match the deployed
contract's read-only `claimDigest`; frontend calldata is restricted to this pool's
claim function with zero ETH value. Real-user claims require the user's wallet.
