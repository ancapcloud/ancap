# Emulator smoke: create → clipboard export → pm clear → paste import (no mnemonic) → restart → same address
# Requires: adb, running emulator, installed cloud.ancap.acpwallet with embedded JS (no Metro stash).
# Does NOT broadcast transactions.

$ErrorActionPreference = "Stop"
$env:ANDROID_HOME = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$env:Path = "$env:ANDROID_HOME\platform-tools;$env:Path"

$Package = "cloud.ancap.acpwallet"
$ExportPath = Join-Path $env:TEMP "ancap-keystore-smoke.json"

function Dump {
  adb shell uiautomator dump /sdcard/ui.xml 2>$null | Out-Null
  cmd /c "adb pull /sdcard/ui.xml %TEMP%\u.xml >nul 2>&1"
  Get-Content "$env:TEMP\u.xml" -Raw -Encoding UTF8
}

function Labels([string]$xml) {
  ([regex]::Matches($xml, 'text="([^"]{3,70})"') | ForEach-Object { $_.Groups[1].Value } |
    Where-Object { $_.Length -lt 70 -and $_ -notmatch '^[\{\[]' } |
    Select-Object -First 16) -join " || "
}

function Tap-Text([string]$t) {
  $xml = Dump
  $esc = [regex]::Escape($t)
  $m = [regex]::Match($xml, "text=`"$esc`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  if (-not $m.Success) {
    $m = [regex]::Match($xml, "bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"[^>]*text=`"$esc`"")
  }
  if (-not $m.Success) { throw "no:$t $(Labels $xml)" }
  adb shell input tap ([int]((([int]$m.Groups[1].Value) + ([int]$m.Groups[3].Value)) / 2)) ([int]((([int]$m.Groups[2].Value) + ([int]$m.Groups[4].Value)) / 2))
  Write-Host "tap:$t"
  Start-Sleep -Seconds 1
}

function Tap-Contains([string]$sub) {
  $xml = Dump
  $m = [regex]::Match($xml, "text=`"([^`"]*$([regex]::Escape($sub))[^`"]*)`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  if (-not $m.Success) { throw "no:$sub $(Labels $xml)" }
  adb shell input tap ([int]((([int]$m.Groups[2].Value) + ([int]$m.Groups[4].Value)) / 2)) ([int]((([int]$m.Groups[3].Value) + ([int]$m.Groups[5].Value)) / 2))
  Write-Host "tap:$($m.Groups[1].Value)"
  Start-Sleep -Seconds 1
}

function Launch-App {
  adb shell am force-stop $Package
  Start-Sleep -Seconds 2
  adb shell monkey -p $Package -c android.intent.category.LAUNCHER 1 | Out-Null
  Start-Sleep -Seconds 12
}

function Scroll-Tap-Save-Create {
  for ($i = 0; $i -lt 20; $i++) {
    $xml = Dump
    $m = [regex]::Match($xml, 'text="([^"]*save wallet[^"]*)"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
    if ($m.Success) {
      adb shell input tap ([int]((([int]$m.Groups[2].Value) + ([int]$m.Groups[4].Value)) / 2)) ([int]((([int]$m.Groups[3].Value) + ([int]$m.Groups[5].Value)) / 2))
      Write-Host "tap:$($m.Groups[1].Value)"
      return
    }
    adb shell input swipe 640 2200 640 900 350
    Start-Sleep -Milliseconds 500
  }
  throw "create save missing"
}

# --- create + external export (clipboard) ---
Launch-App
$xml = Dump
Write-Host "START $(Labels $xml)"
if ($xml -notmatch "Create new wallet") {
  # wipe if a wallet is present
  $m = [regex]::Match($xml, 'content-desc="[^"]*Settings"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
  if ($m.Success) {
    adb shell input tap ([int]((([int]$m.Groups[1].Value) + ([int]$m.Groups[3].Value)) / 2)) ([int]((([int]$m.Groups[2].Value) + ([int]$m.Groups[4].Value)) / 2))
    Start-Sleep -Seconds 2
    for ($i = 0; $i -lt 14; $i++) {
      if ((Dump) -match "Remove wallet from this device") { break }
      adb shell input swipe 640 2200 640 800 300
      Start-Sleep -Milliseconds 400
    }
    Tap-Contains "Remove wallet from this device"
    Start-Sleep -Seconds 1
    if ((Dump) -match 'text="REMOVE"') { Tap-Text "REMOVE" } else { Tap-Text "Remove" }
    Start-Sleep -Seconds 5
    Launch-App
  }
}
if ((Dump) -notmatch "Create new wallet") { throw "expected welcome" }

Tap-Text "Create new wallet"
Start-Sleep -Seconds 2
Tap-Text "Generate wallet"
Start-Sleep -Seconds 20
$xml = Dump
$ADDR = [regex]::Match($xml, 'text="(acp1[a-z0-9]+)"').Groups[1].Value
Write-Host "CREATED=$ADDR"
if (-not $ADDR) { throw "no address" }

for ($i = 0; $i -lt 8; $i++) {
  if ((Dump) -match "Copy keystore JSON") { break }
  adb shell input swipe 640 2300 640 700 350
  Start-Sleep -Milliseconds 400
}
Tap-Text "Copy keystore JSON"
Start-Sleep -Seconds 1
if ((Dump) -match 'text="OK"') { Tap-Text "OK" }

# Capture external backup from clipboard to host file before wiping app data.
# Native ACP keystore uses "v":3; older fixtures may use "version":3.
$clip = adb shell cmd clipboard get-clip 2>$null | Out-String
if ($clip -notmatch '\{.*"(?:v|version)"') {
  # Fallback: some images wrap clip output; try service
  $clip = adb exec-out cmd clipboard get-clip 2>$null | Out-String
}
# Extract JSON object from clipboard dump
$ksMatch = [regex]::Match($clip, '(\{[\s\S]*"(?:v|version)"\s*:\s*3[\s\S]*\})')
if (-not $ksMatch.Success) {
  # Last resort: read via app FileSystem if Copy also left nothing parseable — fail clearly
  throw "clipboard export missing keystore JSON (capture failed)"
}
$ksJson = $ksMatch.Groups[1].Value.Trim()
# Trim trailing non-JSON if clipboard meta appended
$end = $ksJson.LastIndexOf("}")
if ($end -ge 0) { $ksJson = $ksJson.Substring(0, $end + 1) }
Set-Content -Path $ExportPath -Value $ksJson -Encoding utf8NoBOM
Write-Host "EXPORT_BYTES=$((Get-Item $ExportPath).Length) path=$ExportPath"

Scroll-Tap-Save-Create
Start-Sleep -Seconds 2
if ((Dump) -match "CONTINUE") { Tap-Text "CONTINUE" }
elseif ((Dump) -match "Continue") { Tap-Text "Continue" }
Start-Sleep -Seconds 6
$xml = Dump
$h1 = [regex]::Match($xml, 'text="(acp1[a-z0-9]+)"').Groups[1].Value
Write-Host "HOME1=$h1"
if ($h1 -ne $ADDR) { throw "save mismatch" }

# --- delete app data (true wipe, including any residual SecureStore) ---
adb shell am force-stop $Package
adb shell pm clear $Package | Out-Null
Start-Sleep -Seconds 2
Launch-App
$xml = Dump
Write-Host "AFTER_CLEAR $(Labels $xml)"
if ($xml -notmatch "Create new wallet") { throw "expected welcome after pm clear" }

# Restore clipboard from host export, then paste in import UI
$raw = Get-Content $ExportPath -Raw -Encoding UTF8
# Push via temp + run-as is unreliable for clipboard; use content intent / clip set
$tmpDevice = "/data/local/tmp/ancap-ks-smoke.json"
adb push $ExportPath $tmpDevice | Out-Null
# Set clipboard from file using app process helper: broadcast not available — use cmd if supported
adb shell "cmd clipboard set-clip --type text \"`$(cat $tmpDevice)\"" 2>$null | Out-Null
# Alternative: many emulators accept:
adb shell "am broadcast -a clipper.set -e text \"$(Get-Content $ExportPath -Raw)\"" 2>$null | Out-Null

# Prefer reading file into clipboard via a short shell that avoids cmd length limits:
adb shell "run-as $Package sh -c 'cp $tmpDevice files/ks-import.json'" 2>$null | Out-Null

Tap-Text "Import wallet"
Start-Sleep -Seconds 2

# Paste from clipboard — if clipboard set failed, type is impossible for 40KB;
# instead push JSON into the focused field via Expo Clipboard by launching with the file
# copied into a world-readable path and using `adb shell cmd clipboard set-text` when available.
$clipSet = $false
try {
  # Android 13+ sometimes: service call; try writing clip via `cmd clipboard`
  $escaped = ($raw -replace '\\', '\\\\' -replace '"', '\"')
  # Use base64 pipe to avoid shell escaping hell
  $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($raw))
  Set-Content -Path "$env:TEMP\ancap-ks.b64" -Value $b64 -Encoding ascii
  adb push "$env:TEMP\ancap-ks.b64" /data/local/tmp/ancap-ks.b64 | Out-Null
  adb shell "base64 -d /data/local/tmp/ancap-ks.b64 > /data/local/tmp/ancap-ks.json"
  # toybox `cmd clipboard` set may not take files; use clipper-like approach via settings
  # Fall back: inject via `input` is too small — use react-native by pasting after
  # `adb shell service call clipboard 2 i32 1` ...
  # Practical path: use `am start` with EXTRA truncated — instead write KeyStore into SecureStore is forbidden.
  #
  # Use `uiautomator` + clipboard manager app — if get-clip worked, set-clip via same cmd:
  adb shell "cat /data/local/tmp/ancap-ks.json | cmd clipboard set-clip" 2>$null
  if ($LASTEXITCODE -eq 0) { $clipSet = $true }
} catch {}

if (-not $clipSet) {
  # Host-side: open import, use Clipboard via Expo by setting PRIMARY clip through content provider
  # Final fallback — use `adb shell cmd clipboard set-text @/data/local/tmp/ancap-ks.json` (API 34+)
  adb shell "cmd clipboard set-text --file /data/local/tmp/ancap-ks.json" 2>$null
  if ($LASTEXITCODE -eq 0) { $clipSet = $true }
}

if (-not $clipSet) {
  Write-Host "WARN: cmd clipboard set failed; trying Paste anyway (clipboard may still hold create export if pm clear kept it)"
}

Tap-Contains "Paste keystore"
Start-Sleep -Seconds 2
$imp = $null
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 2
  $xml = Dump
  $imp = [regex]::Match($xml, 'text="(acp1[a-z0-9]{20,})"').Groups[1].Value
  Write-Host "p$i imp=$imp $(Labels $xml)"
  if ($imp) { break }
  if ((Labels $xml) -match "(?i)empty|fail|error|required") {
    # re-try paste
    if ($i -in 2, 8, 15) { Tap-Contains "Paste keystore" }
  }
}
if ($imp -ne $ADDR) { throw "import mismatch got=$imp want=$ADDR" }

Tap-Contains "Save on device"
$h2 = $null
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep -Seconds 3
  $xml = Dump
  if ($xml -match 'text="CONTINUE"') { Tap-Text "CONTINUE"; continue }
  if ($xml -match 'text="Continue"') { Tap-Text "Continue"; continue }
  Write-Host "s$i $(Labels $xml)"
  if (($xml -match "Receive") -and ($xml -match [regex]::Escape($ADDR))) { $h2 = $ADDR; break }
  if ($i -in 4, 12 -and $xml -match "Save on device") { Tap-Contains "Save on device" }
}
if ($h2 -ne $ADDR) { throw "home after import fail" }

Launch-App
$xml = Dump
$h3 = [regex]::Match($xml, 'text="(acp1[a-z0-9]{20,})"').Groups[1].Value
Write-Host "HOME3=$h3"
if ($h3 -ne $ADDR) { throw "restart mismatch" }

Write-Host "SMOKE_OK=True ADDR=$ADDR"
Remove-Item $ExportPath -Force -ErrorAction SilentlyContinue
