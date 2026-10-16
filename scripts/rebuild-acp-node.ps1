#!/usr/bin/env pwsh
# Rebuild acp-node only (use when you see "access denied" -> stop the node first, then run this).
# Default: `cargo build --release` — NO on-chain creator vesting (see ACP-crypto/acp-node/src/vesting.rs).
#
#   .\scripts\rebuild-acp-node.ps1
#   .\scripts\rebuild-acp-node.ps1 -MainnetVesting   # `cargo build --release --features enforced-creator-vesting`

[CmdletBinding()]
param(
    [switch]$MainnetVesting
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$crateDir = Join-Path $repoRoot "ACP-crypto\acp-node"
$exe = Join-Path $crateDir "target\release\acp-node.exe"

Write-Host "acp-node rebuild in: $crateDir" -ForegroundColor Cyan
Push-Location $crateDir
try {
    if ($MainnetVesting) {
        Write-Host "Building with --features enforced-creator-vesting" -ForegroundColor Yellow
        cargo build --release -p acp-node --target-dir (Join-Path $crateDir "target") --features enforced-creator-vesting
    } else {
        cargo build --release -p acp-node --target-dir (Join-Path $crateDir "target")
    }
    if ($LASTEXITCODE -ne 0) { throw "acp-node build failed (exit $LASTEXITCODE)" }
} finally {
    Pop-Location
}
if (Test-Path -LiteralPath $exe) {
    Write-Host "OK: $exe" -ForegroundColor Green
} else {
    throw "Build did not produce $exe (if access denied, stop acp-node.exe and retry)"
}
