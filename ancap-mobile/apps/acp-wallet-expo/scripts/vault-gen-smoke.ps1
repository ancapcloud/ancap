# Legacy entry point; use the encrypted external recovery scenario.
param([switch]$AllowTestWalletReset)
$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "vault-external-restore-smoke.ps1") -AllowTestWalletReset:$AllowTestWalletReset
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
