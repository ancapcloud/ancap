# Native ACP receipt and stale balance index — 2026-10-30

The reported destination was
`acp1qpj54yrltxljjp5rwzd40hpxkwvlq24azuc7xdxd`.
Transaction `ea8c8075ac3df24cf3cc4ed992faf6115131cbbd84558b947b6e68cf620bc7bb`
confirmed in native block 21 for 32,890,484.16372016 ACP. A full scan of
blocks 1–21 found two remaining outputs totalling 32,891,150.16371916 ACP.
The API balance probe still returned height 19 and 665.999999 ACP.
The transfer succeeded; the published balance index lagged behind the node.

Running the dedicated UTXO tick with the database wallet/privacy/binding
watchlist brought the published index to height 21 and the correct amount.
No keys, transfers, reserves, or ledger claims were changed.

The existing UTXO tick comes after unrelated commerce jobs in `/system/jobs/tick`.
An independent systemd timer now runs only the UTXO index every 30 seconds.
Its oneshot service prevents overlapping timer executions, reports failure with
a nonzero exit status, and bounds each run to 180 seconds. This does not claim
that every other ACP subsystem has been audited or repaired.

Install `scripts/refresh-acp-utxo-index.py` as
`/opt/ancap-ops/refresh-acp-utxo-index.py` and the two units from
`deploy/systemd/` into `/etc/systemd/system/`, then run
`systemctl daemon-reload` and `systemctl enable --now ancap-utxo-index.timer`.
The service targets the current production container `current-api-1`; update
the unit if deployment naming changes. Check service journals and the reported
watermark against node height after deployment.
