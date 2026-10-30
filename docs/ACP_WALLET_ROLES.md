> **2026-10-30 status:** wACP was an ANCAP test release on BSC and is retired from public promotion. This document contains historical test material or technical identifiers. Current policy: rACP is the primary external token; ACP remains internal; display 1 ACP = 10 rACP equivalents; service prices use EUR (1 EUR = 100 ACP). Historical balances and obligations are not erased. See `docs/RACP_CURRENT_POLICY.md` in the repository root.

# ACP wallet roles and tokenomics (operator reference)

Last updated: 2026-10-02.

## Official tokenomics (210M ACP, protocol)

| Bucket | Share | ACP | On-chain form |
|---|---:|---:|---|
| Creator vesting | 33% | 69,300,000 | Vesting contract / dedicated wallet |
| Validator emission reserve | 50% | 105,000,000 | Locked genesis UTXO; released by signed spends |
| Public & liquidity | 12% | 25,200,000 | Treasury / LP wallets |
| Ecosystem grants | 5% | 10,500,000 | Grants wallet |

Source: `ACP-crypto/acp-crypto/src/protocol_params.rs`, `docs/FINANCE_MODEL.md`.

Annual validator payout: **10.5M ACP/year** from the 105M reserve (not new mint).

## Production operator wallets (must stay separate)

| Role | Address | Keystore | Never use for |
|---|---|---|---|
| **Bridge reserve** | `acp1qrz3ksr8gpv4ah208t5qvzxx0f4vc7a7ws7uqluz` | `Sicret/bridge-bsc/acp-reserve-keystore.json` | Custodial sweep, genesis dumps |
| **Custodial hot** | `acp1qzfdkqxfgyw9ysk99qsd79yxdfe338yd85vrqnp9` | `Sicret/custodial-hot.keystore.json` → `/run/secrets/custodial-hot.keystore.json` (`ACP_CUSTODIAL_HOT_KEYSTORE_FILE`) | wACP backing / bridge reserve spends |
| **Public & Liquidity** | `acp1qqla8waukrudkleau9n6gzj9c58ufyfxaulvwumm` | `Sicret/public-liquidity.keystore.json` | Untracked issuance |
| **Project treasury** | `acp1qpw9nstpx5vtmqxdxmmud25dk0ae4s6a7cs7n902` | `Sicret/project-treasury-keystore.json` | Bridge reserve |
| **Bridge release hot** | `acp1qq805ke8uggeszjcnyeru8wcjded7qt7g5sescpc` | `Sicret/bridge-bsc/acp-release-hot-mnemonic.txt` | wACP backing |

### Env naming bug (fixed intent)

On production, `ACP_HOT_*` in `docker-compose.prod.yml` points at **bridge reserve** signer material
for reverse-rail payouts. That is correct for bridge orchestrator, but must **not** be confused with
**custodial hot** `acp1qzfdkq...`.

Recommended env split:

- `ACP_BRIDGE_RESERVE_KEYSTORE_FILE` — bridge reserve (`acp1qrz3...`)
- `ACP_CUSTODIAL_HOT_KEYSTORE_FILE` — custodial hot (`acp1qzfdkq...`)
- `ACP_RELEASE_HOT_MNEMONIC_FILE` — BSC→ACP release wallet

## Supply incident and v3 recovery (2026-10-02)

The v2 node did not resolve transaction inputs against live UTXOs. Three
double-spends plus synthetic validator outputs raised actual unspent supply to
`832,187,477.05255227 ACP`. A stale cross-regenesis API index separately showed
the incorrect `2,538,291,192.32 ACP` figure.

Recovery v3 restores the official four-output 210M genesis, archives the old
RocksDB, funds operational wallets from Public & Liquidity and Ecosystem, and activates
stateful input/ownership/double-spend/cap checks. See
[`ACP_SUPPLY_INCIDENT_2026-10-02.md`](ACP_SUPPLY_INCIDENT_2026-10-02.md).

## Invariants (enforce in scripts and CI)

```
bridge_reserve_acp >= wacp_total_supply_acp   # backing ratio >= 1
bridge_reserve_units >= ceil(wacp_totalSupply_wei / 10^10) + 99_900_000_000
issued_supply_units == 21_000_000_000_000_000
utxo_supply_units <= issued_supply_units
post_genesis_issuance_units == 0
```

The `99_900_000_000`-unit bridge margin is the 999 ACP reverse-payout fee
buffer. The liability source is the wACP contract's live BSC `totalSupply()`,
not only the platform's bridge-operation rows.

Before any transfer **from** bridge reserve:

```bash
curl -s -H 'User-Agent: ancap-backend/1.0' https://ancap.cloud/api/v1/bridge/wacp/reserve-proof
```

Never run `scripts/sweep-acp-to-hot.sh` against bridge reserve when
`backing_ratio < 1` would result.

## Canonical v3 bucket keys

| Bucket | Keystore |
|---|---|
| Creator | `creator.keystore.json` → `acp1qrfw3d50jd4864vxhatuknhw65jwv463ccr6flsl` |
| Validator reserve | `validator-reserve.keystore.json` |
| Public & liquidity | `public-liquidity.keystore.json` |
| Ecosystem | `ecosystem-grants.keystore.json` → `acp1qq9t4lf4z7lprt7a6nr682cl02f5tcyh45stakdf` |

Operational hot, project, and bridge balances are ordinary outputs funded from
Public & Liquidity or Ecosystem. They must never be added to the four genesis
allocations when calculating total supply.
