# Generate Kotlin + Swift bindings for acp-mobile-ffi (run from ACP-crypto/)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

cargo build -p acp-mobile-ffi --release
if ($LASTEXITCODE -ne 0) { throw "Host FFI build failed; do not generate from an older library." }
$lib = Join-Path $root "target\release\acp_mobile_ffi.dll"
if (-not (Test-Path $lib)) { throw "Fresh host FFI library missing: $lib" }

$outKotlin = Join-Path $root "acp-mobile-ffi\bindings\kotlin"
$outSwift = Join-Path $root "acp-mobile-ffi\bindings\swift"
New-Item -ItemType Directory -Force -Path $outKotlin | Out-Null
New-Item -ItemType Directory -Force -Path $outSwift | Out-Null

cargo run -p acp-mobile-ffi --bin uniffi-bindgen -- generate `
  --library $lib `
  --language kotlin `
  --out-dir $outKotlin
if ($LASTEXITCODE -ne 0) { throw "Kotlin binding generation failed." }
$kotlinFile = Join-Path $outKotlin "uniffi\acp_mobile_ffi\acp_mobile_ffi.kt"
& (Join-Path $PSScriptRoot "fix-uniffi-kotlin.ps1") -SourcePath $kotlinFile
$stagedKotlin = Join-Path (Split-Path -Parent $root) "ancap-mobile\modules\expo-acp-core\android\src\main\java\uniffi\acp_mobile_ffi\acp_mobile_ffi.kt"
if (Test-Path -LiteralPath (Split-Path -Parent $stagedKotlin)) {
    Copy-Item -LiteralPath $kotlinFile -Destination $stagedKotlin
}

cargo run -p acp-mobile-ffi --bin uniffi-bindgen -- generate `
  --library $lib `
  --language swift `
  --out-dir $outSwift
if ($LASTEXITCODE -ne 0) { throw "Swift binding generation failed." }

Write-Host "Bindings written to acp-mobile-ffi/bindings/"
