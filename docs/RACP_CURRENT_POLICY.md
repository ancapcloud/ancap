# Current token and pricing policy — 2026-10-30

Operator decision: wACP was a test release on BSC. It is retired from public
promotion and the active official token list. Older documents mentioning it are
historical test records, not the current product specification.

- **Internal accounting:** ACP, with original ledger units and native addresses.
- **Primary external token:** rACP on Robinhood Chain, chain ID 4663, contract
  `0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911`.
- **Display:** multiply internal ACP by 10 for a clearly marked rACP equivalent.
  An equivalent is not an ERC-20 balance and does not create or mint tokens.
- **Service pricing:** EUR. Operator-approved rate: 1 EUR = 100 ACP = 1,000 rACP
  equivalents. This is an accounting rate, not a public token market price.
- **Legacy USD catalogue conversion:** immutable ECB reference of 2026-10-29,
  1 EUR = 1.1130 USD; prices round to euro cents. Source:
  https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
- **History:** retain original transaction currency, contracts, evidence and
  recorded obligations. Calling the earlier release a test does not erase
  on-chain balances or transfer reserves. No reserve transfer is part of these
  documentation and display changes.
- **New BSC exposure:** closed under EXTERNAL_TOKEN_RACP_ONLY. Historical
  redemption support remains separate from the active token's public entry points.

Actual rACP supply and reserve figures remain sourced from the existing contract
and ACP reserve. Native ACP balances are not relabelled as minted rACP holdings.
Historical receipts are not rewritten into EUR or rACP.

Implementation and deployment status are recorded separately; an edited file is
not evidence that production has been updated.

## Verified initial trading pool

PancakeSwap V2 rACP/WETH on Robinhood Chain (4663):
https://pancakeswap.finance/liquidity/pool/robinhood/0x7583745440e9e8CBdCaeC3BF97dD02d9872d9c85?chain=robinhood

RPC verification at block 101517870 matched the official rACP contract and
WETH `0x0bd7d308f8e1639fab988df18a8011f41eacad73`. Snapshot reserves:
5,000 rACP and 0.005 WETH. Small bootstrap liquidity; neither deep market
liquidity nor price-tracker listing is claimed. Pool price is separate from
the operator-set EUR service accounting rate.
