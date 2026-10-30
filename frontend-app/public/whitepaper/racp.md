# Robinhood ACP (rACP)

rACP is an ACP receipt issued by ANCAP on Robinhood Chain (chain ID 4663).
It is not issued by Robinhood. Name and ticker match the deployed contract.

- Contract: `0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911`
- Decimals: 18. Lifetime issuance cap: 10,000,000 rACP.
- Issued: 10,000,000 rACP. 1 ACP corresponds to 10 rACP.
- Initial dedicated reserve: 1,000,000 native ACP, confirmed at ACP block 19.
- Reserve address: `acp1qqqsdr00nem230z3e84stqkx7drh2xwncupts2lz`
- Funding transaction: `1b369ac2dc6c21c84e1ca798bd5f4059a5c45ea4ca25ef5068042533a77cd0c2`
- Issuance transaction: `0xe9b437c7e2260ae284ae011fdae4699b9bca63e3712997ffad28be8d105334e8`

The immutable issuer attested to native reserve funding. The EVM contract does
not verify ACP consensus or maintain cross-chain reserves automatically.
Transfers use ERC-20. No transfer tax, mutable owner, additional mint capacity,
or upgrade mechanism is present. Burns do not restore issuance capacity.

`requestRedemption` burns rACP and emits `RedemptionRequested`. Native ACP is
paid by the ANCAP supervised redeem service from the exclusive reserve when
`RACP_REDEEM_ENABLED=true`. Destination is the `acp1` string in the event.
Do not treat an emitted request alone as a completed payout until status is
`COMPLETED` at `/v1/racp/redeem/by-tx/{tx}` or `/tokens/racp/redeem`.

No trading pool or market price has been established. Liquidity budget is zero
until the operator provides new parameters. No CoinGecko, CoinMarketCap,
Trust Wallet directory, exchange listing, Robinhood endorsement, or security
audit is claimed. Source verification is not an audit or listing approval.

Official page: https://ancap.cloud/tokens/racp
Redeem: https://ancap.cloud/tokens/racp/redeem
Token list: https://ancap.cloud/tokenlist.json
Placement status: https://ancap.cloud/racp-listings.json
Source verification: https://robinhoodchain.blockscout.com/address/0xD53f91A63f95beAc61Ec8417c40C5e620FE3a911?tab=contract
