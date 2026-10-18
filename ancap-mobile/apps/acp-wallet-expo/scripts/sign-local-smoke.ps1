# Emulator smoke: open Send → Sign locally (no broadcast).
# Expects an unlocked wallet already on home (after vault-external-restore-smoke).
# Exit 0: signed result observed; exit 2: funding blocked; exit 1: failed/unobserved.
# An error mentioning native/module/failure is NEVER evidence of successful linkage.

$ErrorActionPreference = "Stop"
$env:ANDROID_HOME = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$env:Path = "$env:ANDROID_HOME\platform-tools;$env:Path"
$Package = "cloud.ancap.acpwallet"
$Amount = "0.00000001"
$UiDumpPath = Join-Path $env:TEMP ("ancap-sign-ui-" + [guid]::NewGuid().ToString("N") + ".xml")
$DeviceUiPath = "/sdcard/ancap-sign-ui.xml"
$qemu = (& adb shell getprop ro.kernel.qemu 2>$null | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or $qemu -ne "1") { throw "Expected one Android emulator." }
$avd = (& adb emu avd name 2>$null | Select-Object -First 1).Trim()
if ($LASTEXITCODE -ne 0 -or $avd -ne "Pixel_10_Pro") { throw "Expected Pixel_10_Pro." }

function Dump {
  adb shell uiautomator dump $DeviceUiPath 2>$null | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "UI dump failed; no signing evidence." }
  # Windows PowerShell treats adb's successful stderr progress as an error.
  $previousPreference = $ErrorActionPreference
  try {
    $ErrorActionPreference = "Continue"
    & adb pull $DeviceUiPath $UiDumpPath 2>$null | Out-Null
    $pullExitCode = $LASTEXITCODE
  } finally { $ErrorActionPreference = $previousPreference }
  if ($pullExitCode -ne 0) { throw "UI pull failed; no signing evidence." }
  Get-Content -LiteralPath $UiDumpPath -Raw -Encoding UTF8
}
function Labels([string]$xml) {
  ([regex]::Matches($xml, 'text="([^"]{3,70})"') | ForEach-Object { $_.Groups[1].Value } |
    Where-Object { $_.Length -lt 70 -and $_ -notmatch '^[\{\[]' } |
    Select-Object -First 14) -join " || "
}
function Tap-Contains([string]$sub) {
  $xml = Dump
  $m = [regex]::Match($xml, "text=`"([^`"]*$([regex]::Escape($sub))[^`"]*)`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  if (-not $m.Success) {
    $m = [regex]::Match($xml, "content-desc=`"([^`"]*$([regex]::Escape($sub))[^`"]*)`"[^>]*bounds=`"\[(\d+),(\d+)\]\[(\d+),(\d+)\]`"")
  }
  if (-not $m.Success) { throw "no:$sub $(Labels $xml)" }
  adb shell input tap ([int]((([int]$m.Groups[2].Value)+([int]$m.Groups[4].Value))/2)) ([int]((([int]$m.Groups[3].Value)+([int]$m.Groups[5].Value))/2))
  Write-Host "tap:$($m.Groups[1].Value)"; Start-Sleep 1
}

try {
adb shell am force-stop $Package
Start-Sleep 2
adb shell monkey -p $Package -c android.intent.category.LAUNCHER 1 | Out-Null
Start-Sleep 12
$xml = Dump
Write-Host "HOME $(Labels $xml)"
$addr = [regex]::Match($xml, 'text="(acp1[a-z0-9]{20,})"').Groups[1].Value
if (-not $addr) { throw "expected wallet on home" }
# Self-send target — still no broadcast; empty UTXO set should fail inside FFI with a clear error.
$To = $addr

Tap-Contains "Send"
Start-Sleep 2

# Focus first text field (To) and type address
$xml = Dump
$fields = [regex]::Matches($xml, 'class="android.widget.EditText"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
if ($fields.Count -lt 2) { throw "send fields missing $(Labels $xml)" }
$toBounds = $fields[0]
adb shell input tap ([int]((([int]$toBounds.Groups[1].Value)+([int]$toBounds.Groups[3].Value))/2)) ([int]((([int]$toBounds.Groups[2].Value)+([int]$toBounds.Groups[4].Value))/2))
Start-Sleep 1
# bech32 is alphanumeric — adb input text is enough (no special chars)
adb shell input text $To
Start-Sleep 1
$amtBounds = $fields[1]
adb shell input tap ([int]((([int]$amtBounds.Groups[1].Value)+([int]$amtBounds.Groups[3].Value))/2)) ([int]((([int]$amtBounds.Groups[2].Value)+([int]$amtBounds.Groups[4].Value))/2))
Start-Sleep 1
adb shell input text $Amount
Start-Sleep 1
adb shell input keyevent 4
Start-Sleep 1

Tap-Contains "Sign locally"
$seen = $null
for ($i = 0; $i -lt 20; $i++) {
  Start-Sleep 2
  $xml = Dump
  Write-Host "sign_$i $(Labels $xml)"
  if ($xml -match "Signed locally|Local signature ready") {
    Write-Host "SIGN_LOCAL_OK=True ADDR=$addr"
    exit 0
  }
  if ($xml -match "(?i)insufficient funds|no spendable|no utxo") {
    Write-Host "SIGN_LOCAL_BLOCKED=funding_required ADDR=$addr"
    exit 2
  }
  if ($xml -match "(?i)native module|not linked|Sign failed|could not sign") {
    Write-Host "SIGN_LOCAL_FAILED=True ADDR=$addr"
    exit 1
  }

}
Write-Host "SIGN_LOCAL_UNVERIFIED=True ADDR=$addr"
Write-Host "NOTE=No definite signing outcome observed; do not count this run as passed"
exit 1
} finally {
  Remove-Item -LiteralPath $UiDumpPath -Force -ErrorAction SilentlyContinue
  & adb shell rm -f $DeviceUiPath 2>$null | Out-Null
}
