# rACP public distribution — 2026-10-30

Scope: public discoverability of the issued rACP contract on Robinhood Chain
4663. The operator explicitly set liquidity budget to zero and deferred liquidity.
No liquidity position, swap, paid directory or market-making transaction was made.

## Published verification

- Blockscout: source verified, exact match, Solidity 0.8.24, MIT, optimizer 200, paris.
- Sourcify: runtime and creation exact matches, match ID 57603340.
- Evidence: `contracts/robinhood-racp/prepared/source-verification.json` and
  `contracts/robinhood-racp/prepared/sourcify-verification.json`.

Blockscout's separate token profile still needs an authenticated account to update
name/logo. The contract verification is complete; a metadata profile approval is not claimed.

## ANCAP website release

- `/tokens/racp`: official token identity, addresses, issuance and reserve transaction links.
- `/docs/racp`: alias to the canonical page.
- Homepage and `/markets`: token card; navigation: permanent rACP link.
- `/tokenlist.json`: rACP on chain 4663, preserving BSC wACP; version 1.1.0.
- `/racp-logo.svg` and `/racp-logo.png`: ANCAP-derived identity, not Robinhood branding.
- `/whitepaper/racp.md`: parameters, custody, redemption and listing limitations.
- `/racp-listings.json`: explicit completed, pending and blocked placements.
- `/llms.txt`: token and metadata resources for machine discovery.
- Native exchange catalog: official page, logo, tokenlist and verification references.

English, Russian, Ukrainian, German and Traditional Chinese copy is included.
Wallet import checks chain 4663 after switching/adding Robinhood Chain and only
then requests `wallet_watchAsset`. It does not sign transactions or approve spending.
Manual import is not a claim of global inclusion in MetaMask or another wallet directory.

## Deferred external listings

- CoinGecko active listing: no active tracked market; not submitted.
- CoinMarketCap tracked market listing: no live market; not submitted.
- DEX pool/price aggregators: no liquidity pool; no market price or trading volume claimed.
- Trust Wallet asset directory: activity/audit eligibility and paid submission requirements
  are not met; no fee paid and no submission made.

Official prerequisites reviewed:
- https://support.coingecko.com/articles/9489827481-how-to-list-a-new-cryptocurrency-on-coingecko?lang=en
- https://support.coinmarketcap.com/hc/en-us/articles/360043659351-Listings-Criteria
- https://developer.trustwallet.com/developer/new-asset/requirements

## Verification

Four focused frontend tests cover wrong-chain refusal, adding an unknown chain,
rejected imports and tokenlist chain/address consistency. Backend catalog regression
passes. Local production compilation and initial remote image build passed. Browser
checks confirmed all five languages; the mobile header was corrected after visual
inspection at a 390px viewport, with no horizontal overflow. The final remote
production build passed and was deployed with build ID `racp-20261030`.
Live checks returned HTTP 200 for the token page, homepage, Markets, whitepaper,
llms.txt, PNG logo and tokenlist 1.1.0; `/docs/racp` resolves to the canonical page.
The deployed API catalog exposes the page/logo/tokenlist/verification references;
the public reserve endpoint returned 1,000,000 ACP. Evidence is archived in
`contracts/robinhood-racp/prepared/publication-verification.json`.

Custody and automated redemption remain separate unfinished services. Source
verification proves matching source, not an audit, endorsement or token listing.
