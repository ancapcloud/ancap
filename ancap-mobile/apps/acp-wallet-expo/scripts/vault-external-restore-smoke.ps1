param([switch]$AllowTestWalletReset)

# Independent restore smoke (no SecureStore stash):
# create → password-encrypted Copy export → host pull via run-as →
# pm clear → restore export file → Load export file import (no mnemonic) → restart → same address
# No transaction broadcast.

$ErrorActionPreference = "Stop"
$env:ANDROID_HOME = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$env:Path = "$env:ANDROID_HOME\platform-tools;$env:Path"
$Package = "cloud.ancap.acpwallet"

if (-not $AllowTestWalletReset) { throw "This smoke resets the test wallet. Pass -AllowTestWalletReset for a disposable Pixel_10_Pro wallet only." }
$qemu = (& adb shell getprop ro.kernel.qemu 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $qemu -ne "1") { throw "Refusing wallet reset: expected one Android emulator." }
$avd = (& adb emu avd name 2>$null | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0 -or $avd -ne "Pixel_10_Pro") { throw "Refusing wallet reset outside Pixel_10_Pro." }

$ExportFilename = "acp-keystore-export.json"
$ExportPath = Join-Path $env:TEMP ("ancap-keystore-external-" + [guid]::NewGuid().ToString("N") + ".json")
$UiDumpPath = Join-Path $env:TEMP ("ancap-smoke-ui-" + [guid]::NewGuid().ToString("N") + ".xml")
# Ephemeral credential for this disposable-wallet run only. Never log or persist it.
$passwordBytes = New-Object byte[] 24
$passwordRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
  $passwordRng.GetBytes($passwordBytes)
  $TestBackupPassword = [Convert]::ToBase64String($passwordBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
} finally {
  $passwordRng.Dispose()
  [Array]::Clear($passwordBytes, 0, $passwordBytes.Length)
}
$DeviceTmp = "/data/local/tmp/ancap-ks-external.json"

function Dump {
  adb shell uiautomator dump /sdcard/ui.xml 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "UI hierarchy dump failed; do not reuse stale evidence." }
  $previousPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & adb pull /sdcard/ui.xml $UiDumpPath 2>$null | Out-Null
    $pullExitCode = $LASTEXITCODE
  } finally { $ErrorActionPreference = $previousPreference }
  if ($pullExitCode -ne 0) { throw "UI hierarchy pull failed; do not reuse stale evidence." }
  try { Get-Content -LiteralPath $UiDumpPath -Raw -Encoding UTF8 }
  finally { & adb shell rm -f /sdcard/ui.xml 2>$null | Out-Null }
}
function Labels([string]$xml) {
  ([regex]::Matches($xml, 'text="([^"]{3,70})"') | ForEach-Object { $_.Groups[1].Value } |
    Where-Object { $_.Length -lt 70 -and $_ -notmatch '^[\{\[]|^\d+\.\s' } |
    Select-Object -First 14) -join " || "
}
function Tap-Text([string]$t) {
  $xml = Dump; $esc = "(?i)" + [regex]::Escape($t)
  $m = [regex]::Match($xml, "text=`"$esc`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  if (-not $m.Success) { $m = [regex]::Match($xml, "bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"[^>]*text=`"$esc`"") }
  if (-not $m.Success) { throw "no:$t $(Labels $xml)" }
  adb shell input tap ([int]((([int]$m.Groups[1].Value)+([int]$m.Groups[3].Value))/2)) ([int]((([int]$m.Groups[2].Value)+([int]$m.Groups[4].Value))/2))
  Write-Host "tap:$t"; Start-Sleep 1
}
function Tap-Contains([string]$sub) {
  $xml = Dump
  $m = [regex]::Match($xml, "text=`"([^`"]*$([regex]::Escape($sub))[^`"]*)`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  if (-not $m.Success) { throw "no:$sub $(Labels $xml)" }
  adb shell input tap ([int]((([int]$m.Groups[2].Value)+([int]$m.Groups[4].Value))/2)) ([int]((([int]$m.Groups[3].Value)+([int]$m.Groups[5].Value))/2))
  Write-Host "tap:$($m.Groups[1].Value)"; Start-Sleep 1
}
function Set-BackupPassword([string]$Label) {
  for ($attempt = 0; $attempt -lt 10; $attempt++) {
    $xml = Dump
    $match = [regex]::Match($xml, "content-desc=`"$Label`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
    if ($match.Success) {
      & adb shell input tap ([int]((([int]$match.Groups[1].Value)+([int]$match.Groups[3].Value))/2)) ([int]((([int]$match.Groups[2].Value)+([int]$match.Groups[4].Value))/2))
      & adb shell input text $TestBackupPassword
      & adb shell input keyevent 4
      Start-Sleep 1
      return
    }
    & adb shell input swipe 640 2200 640 900 350
    Start-Sleep -Milliseconds 500
  }
  throw "Password field missing: $Label"
}
function Launch-App {
  adb shell am force-stop $Package
  Start-Sleep 2
  adb shell monkey -p $Package -c android.intent.category.LAUNCHER 1 | Out-Null
  Start-Sleep 12
}
function Dismiss-CompatDialog {
  $xml = Dump
  if ($xml -notmatch "Android App Compatibility") { return $false }
  # Checkbox first, then OK — OK may already be gone if the dialog auto-closed.
  if ($xml -match "Don't Show Again") {
    try { Tap-Contains "Don't Show Again"; Start-Sleep 1 } catch { }
  }
  $xml = Dump
  if ($xml -match "Android App Compatibility" -and $xml -match 'text="OK"') {
    Tap-Text "OK"; Start-Sleep 2
  }
  return $true
}
function Wait-Welcome([string]$label = "welcome") {
  for ($i = 0; $i -lt 24; $i++) {
    $xml = Dump
    Write-Host "${label}_$i $(Labels $xml)"
    if ($xml -match 'System UI.+responding|Pixel Launcher.+responding') {
      throw "Android system/launcher ANR; reboot the emulator without wiping its data and retry."
    }
    if ($xml -match "Create new wallet") { return $xml }
    if ($xml -match "Android App Compatibility") {
      Dismiss-CompatDialog | Out-Null
      continue
    }
    # Expo embedded-bundle / dev-client interstitial
    if ($xml -match 'text="Continue"') { Tap-Text "Continue"; Start-Sleep 3; continue }
    if ($xml -match 'Toggle performance monitor|Remote JS debugger') {
      adb shell input keyevent 4
      Start-Sleep 2
      continue
    }
    if ($xml -match 'text="OK"' -and $xml -notmatch "Create new wallet") {
      try { Tap-Text "OK"; Start-Sleep 2 } catch { }
      continue
    }
    Start-Sleep 2
    if ($i -in 6, 12, 18) { Launch-App }
  }
  throw "expected $label"
}
function Scroll-Tap-Save-Create {
  for ($i = 0; $i -lt 20; $i++) {
    $xml = Dump
    $m = [regex]::Match($xml, 'text="([^"]*save wallet[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
    if ($m.Success) {
      adb shell input tap ([int]((([int]$m.Groups[2].Value)+([int]$m.Groups[4].Value))/2)) ([int]((([int]$m.Groups[3].Value)+([int]$m.Groups[5].Value))/2))
      Write-Host "tap:$($m.Groups[1].Value)"; return
    }
    adb shell input swipe 640 2200 640 900 350; Start-Sleep -Milliseconds 500
  }
  throw "create save missing"
}

function Scroll-Tap-Save-Import {
  for ($i = 0; $i -lt 16; $i++) {
    $xml = Dump
    if ($xml -match 'text="Save on device"') {
      Tap-Contains "Save on device"
      return
    }
    adb shell input swipe 640 2200 640 900 350
    Start-Sleep -Milliseconds 500
  }
  throw "import Save on device not visible"
}

function Pull-ExportFile {
  # Prefer files/ documentDirectory path written on Copy.
  $candidates = @(
    "files/$ExportFilename",
    "files/Documents/$ExportFilename"
  )
  foreach ($rel in $candidates) {
    $probe = adb shell "run-as $Package ls $rel" 2>$null | Out-String
    if ($probe -match [regex]::Escape($ExportFilename)) {
      cmd /c "adb exec-out run-as $Package cat $rel > `"$ExportPath`""
      if ((Test-Path $ExportPath) -and (Get-Item $ExportPath).Length -gt 100) {
        Write-Host "PULLED_EXPORT=$rel bytes=$((Get-Item $ExportPath).Length)"
        return
      }
    }
  }
  $found = adb shell "run-as $Package find . -name $ExportFilename 2>/dev/null" 2>$null | Select-Object -First 1
  if ($found) {
    $rel = ($found -replace '^\./', '').Trim()
    cmd /c "adb exec-out run-as $Package cat $rel > `"$ExportPath`""
    if ((Test-Path $ExportPath) -and (Get-Item $ExportPath).Length -gt 100) {
      Write-Host "PULLED_EXPORT=$rel bytes=$((Get-Item $ExportPath).Length)"
      return
    }
  }
  throw "export file missing after Copy (expected $ExportFilename under run-as)"
}

function Restore-ExportFileToApp {
  # Debuggable app: pipe host export into sandbox via run-as (no adb root; cannot read /sdcard from run-as).
  $prevEap = $ErrorActionPreference
  $ErrorActionPreference = "Continue"
  adb shell "run-as $Package mkdir -p files" 2>$null | Out-Null
  $json = [IO.File]::ReadAllText($ExportPath)
  $json | & adb shell "run-as $Package sh -c 'cat > files/$ExportFilename'" 2>$null | Out-Null
  $probe = (cmd /c "adb shell run-as $Package ls -l files/$ExportFilename 2>nul") | Out-String
  $ErrorActionPreference = $prevEap
  if ($probe -notmatch $ExportFilename) {
    throw "failed to restore export file into app files/: $probe"
  }
  Write-Host "RESTORED_EXPORT $($probe.Trim())"
}

try {

Launch-App
$xml = Dump
Write-Host "START $(Labels $xml)"
if ($xml -match 'System UI.+responding|Pixel Launcher.+responding') {
  throw "Android system/launcher ANR; reboot the emulator without wiping its data and retry."
}
# Existing wallet blocks welcome — wipe via Settings tab or hard clear app data.
if ($xml -notmatch "Create new wallet") {
  $m = [regex]::Match($xml, 'content-desc="[^"]*Settings"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
  if (-not $m.Success) {
    $m = [regex]::Match($xml, 'text="Settings"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
  }
  if ($m.Success) {
    adb shell input tap ([int]((([int]$m.Groups[1].Value)+([int]$m.Groups[3].Value))/2)) ([int]((([int]$m.Groups[2].Value)+([int]$m.Groups[4].Value))/2))
    Start-Sleep 2
    for ($i = 0; $i -lt 14; $i++) {
      if ((Dump) -match "Remove wallet from this device") { break }
      adb shell input swipe 640 2200 640 800 300; Start-Sleep -Milliseconds 400
    }
    try {
      Tap-Contains "Remove wallet from this device"; Start-Sleep 1
      if ((Dump) -match 'text="REMOVE"') { Tap-Text "REMOVE" } else { Tap-Text "Remove" }
      Start-Sleep 5
    } catch {
      Write-Host "UI wipe failed; pm clear fallback"
      adb shell am force-stop $Package
      adb shell pm clear $Package | Out-Null
      Start-Sleep 2
    }
  } else {
    Write-Host "Settings tab not found; pm clear fallback"
    adb shell am force-stop $Package
    adb shell pm clear $Package | Out-Null
    Start-Sleep 2
  }
  Launch-App
}
Wait-Welcome "START" | Out-Null
if ((Dump) -notmatch "Create new wallet") { throw "expected welcome" }

Tap-Text "Create new wallet"; Start-Sleep 2
Tap-Text "Generate wallet"; Start-Sleep 20
$xml = Dump
$ADDR = [regex]::Match($xml, 'text="(acp1[a-z0-9]+)"').Groups[1].Value
Write-Host "CREATED=$ADDR"
if (-not $ADDR) { throw "no address" }

for ($i = 0; $i -lt 8; $i++) {
  if ((Dump) -match "Copy keystore JSON") { break }
  adb shell input swipe 640 2300 640 700 350; Start-Sleep -Milliseconds 400
}
Set-BackupPassword "backup-password"
Set-BackupPassword "backup-password-confirm"
Tap-Text "Copy keystore JSON"; Start-Sleep 15
if ((Dump) -match 'text="OK"') { Tap-Text "OK" }

Pull-ExportFile
$ksJson = [IO.File]::ReadAllText($ExportPath)
# The encrypted envelope is v2; the authenticated inner wallet identity is v3.
$backup = $ksJson | ConvertFrom-Json
if ($backup.v -ne 2 -or $backup.crypto.kdf -ne "argon2id") { throw "encrypted envelope missing" }
if ($ksJson -match 'spend_ed25519_seed32|spend_dilithium_sk') { throw "plaintext keys in backup" }
Write-Host "EXPORT_BYTES=$((Get-Item $ExportPath).Length)"

Scroll-Tap-Save-Create; Start-Sleep 2
if ((Dump) -match "CONTINUE") { Tap-Text "CONTINUE" }
elseif ((Dump) -match "Continue") { Tap-Text "Continue" }
Start-Sleep 6
$h1 = [regex]::Match((Dump), 'text="(acp1[a-z0-9]+)"').Groups[1].Value
Write-Host "HOME1=$h1"
if ($h1 -ne $ADDR) { throw "save mismatch" }

# Delete application data (full wipe of SecureStore / generations / leftovers)
adb shell am force-stop $Package
adb shell pm clear $Package | Out-Null
Start-Sleep 2

# Cold start so run-as / files dir exist, then restore the external export artifact.
Launch-App
Wait-Welcome "AFTER_CLEAR" | Out-Null

# Probe SecureStore leftovers without aborting on missing prefs (pm clear → empty).
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$ss = (cmd /c "adb shell run-as $Package cat shared_prefs/SecureStore.xml 2>nul") | Out-String
$ErrorActionPreference = $prevEap
Write-Host "SS_HAS_ACTIVE=$($ss -match 'active_gen') SS_HAS_STASH=$($ss -match 'backup_ks')"

Restore-ExportFileToApp

Tap-Text "Import wallet"; Start-Sleep 2
Write-Host "IMP $(Labels (Dump))"
if ((Dump) -match "Load last keystore") { throw "stash UI must be removed" }
if ((Dump) -notmatch "Load keystore export file") { throw "missing Load keystore export file button" }

Set-BackupPassword "backup-password"
Tap-Contains "Load keystore export file"
$imp = $null
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep 2
  $xml = Dump
  $imp = [regex]::Match($xml, 'text="(acp1[a-z0-9]{20,})"').Groups[1].Value
  Write-Host "p$i imp=$imp $(Labels $xml)"
  if ($imp) { break }
  if ($i -in 3, 10, 18) {
    Restore-ExportFileToApp
    Tap-Contains "Load keystore export file"
  }
}
if ($imp -ne $ADDR) { throw "import mismatch got=$imp want=$ADDR" }

Scroll-Tap-Save-Import
$h2 = $null
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep 3
  $xml = Dump
  if ($xml -match 'text="CONTINUE"') { Tap-Text "CONTINUE"; continue }
  if ($xml -match 'text="Continue"') { Tap-Text "Continue"; continue }
  Write-Host "s$i $(Labels $xml)"
  if (($xml -match "Receive") -and ($xml -match [regex]::Escape($ADDR))) { $h2 = $ADDR; break }
  if ($i -in 5, 15 -and $xml -match "Save on device") { Tap-Contains "Save on device" }
}
if ($h2 -ne $ADDR) { throw "home2 fail" }

Launch-App
$h3 = [regex]::Match((Dump), 'text="(acp1[a-z0-9]{20,})"').Groups[1].Value
Write-Host "HOME3=$h3"
if ($h3 -ne $ADDR) { throw "restart mismatch" }

Write-Host "SMOKE_OK=True ADDR=$ADDR"
} finally {
  $TestBackupPassword = $null
  Remove-Item -LiteralPath $ExportPath -Force -ErrorAction SilentlyContinue
  Remove-Item -LiteralPath $UiDumpPath -Force -ErrorAction SilentlyContinue
  & adb shell rm -f $DeviceTmp /sdcard/ui.xml 2>$null | Out-Null
}
