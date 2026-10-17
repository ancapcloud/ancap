# Build libacp_mobile_ffi.so for Android ABIs and copy into expo-acp-core/jniLibs.
# Requires: rustup, Android SDK + NDK, cargo-ndk (`cargo install cargo-ndk`)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$crypto = Join-Path $root "ACP-crypto"
$jniRoot = Join-Path $root "ancap-mobile\modules\expo-acp-core\android\src\main\jniLibs"

function Resolve-AndroidSdkPath {
  $candidates = @(
    $env:ANDROID_HOME,
    $env:ANDROID_SDK_ROOT,
    (Join-Path $env:LOCALAPPDATA "Android\Sdk"),
    (Join-Path $env:USERPROFILE "AppData\Local\Android\Sdk")
  ) | Where-Object { $_ }

  foreach ($path in $candidates) {
    if (Test-Path $path) {
      return (Resolve-Path $path).Path
    }
  }

  return $null
}

function Resolve-AndroidNdkPath([string]$sdkPath) {
  if ($env:ANDROID_NDK_HOME -and (Test-Path $env:ANDROID_NDK_HOME)) {
    return (Resolve-Path $env:ANDROID_NDK_HOME).Path
  }

  $ndkRoot = if ($sdkPath) { Join-Path $sdkPath "ndk" } else { $null }
  if ($ndkRoot -and (Test-Path $ndkRoot)) {
    $versionDirs = Get-ChildItem $ndkRoot -Directory | Sort-Object Name -Descending
    $preferred = $versionDirs | Where-Object { $_.Name -match '^28\.' } | Select-Object -First 1
    if ($preferred) {
      return $preferred.FullName
    }
    $fallback = $versionDirs | Select-Object -First 1
    if ($fallback) {
      return $fallback.FullName
    }
  }

  $legacy = if ($sdkPath) { Join-Path $sdkPath "ndk-bundle" } else { $null }
  if ($legacy -and (Test-Path $legacy)) {
    return (Resolve-Path $legacy).Path
  }

  return $null
}

$env:ANDROID_HOME = Resolve-AndroidSdkPath
if (-not $env:ANDROID_HOME) {
  Write-Error "Android SDK not found. Install Android Studio SDK or set ANDROID_HOME / ANDROID_SDK_ROOT."
}

$env:ANDROID_NDK_HOME = Resolve-AndroidNdkPath $env:ANDROID_HOME
if (-not $env:ANDROID_NDK_HOME) {
  $sdkManagerHint = Join-Path $env:ANDROID_HOME "cmdline-tools\latest\bin\sdkmanager.bat"
  $hint = if (Test-Path $sdkManagerHint) {
    "Install NDK r28+, e.g. `"$sdkManagerHint`" `"ndk;28.0.13004108`""
  } else {
    "Install NDK r28+ from Android Studio → SDK Manager → SDK Tools (NDK 28.0.13004108 or newer)."
  }
  Write-Error "Android NDK not found under '$($env:ANDROID_HOME)'. $hint"
}

New-Item -ItemType Directory -Force -Path $jniRoot | Out-Null

Write-Host "Using Android SDK: $($env:ANDROID_HOME)"
Write-Host "Using Android NDK: $($env:ANDROID_NDK_HOME)"

Set-Location $crypto

$targetsToEnsure = @("aarch64-linux-android", "x86_64-linux-android", "armv7-linux-androideabi")
$installedTargets = @((& rustup target list --installed 2>$null) | ForEach-Object { $_.Trim() })
$missingTargets = $targetsToEnsure | Where-Object { $_ -notin $installedTargets }
if ($missingTargets.Count -gt 0) {
  Write-Host "Installing missing Rust Android targets: $($missingTargets -join ', ')"
  & rustup target add @missingTargets
  if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install Rust Android targets: $($missingTargets -join ', ')"
  }
} else {
  Write-Host "Rust Android targets already installed"
}

if (-not (Get-Command cargo-ndk -ErrorAction SilentlyContinue)) {
  Write-Host "Installing cargo-ndk (needs network)..."
  cargo install cargo-ndk
  if ($LASTEXITCODE -ne 0) { throw "cargo-ndk installation failed" }
}

$targets = @(
  @{ abi = "arm64-v8a"; triple = "aarch64-linux-android" },
  @{ abi = "x86_64"; triple = "x86_64-linux-android" },
  @{ abi = "armeabi-v7a"; triple = "armv7-linux-androideabi" }
)

foreach ($t in $targets) {
  Write-Host "Building $($t.triple)..."
  cargo ndk -t $t.abi -o $jniRoot build -p acp-mobile-ffi --release --locked
  if ($LASTEXITCODE -ne 0) { throw "Native build failed for $($t.triple); do not use older libraries" }
}

Write-Host "Native libs installed under expo-acp-core/android/src/main/jniLibs"
