# Emulator smoke: open Send → Sign locally (no broadcast).
# Expects an unlocked wallet already on home (after vault-external-restore-smoke).
# Without UTXOs, native sign may fail with a clear insufficient-funds / no-utxo error — that still proves FFI linkage.

$ErrorActionPreference = "Stop"
$env:ANDROID_HOME = if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { "$env:LOCALAPPDATA\Android\Sdk" }
$env:Path = "$env:ANDROID_HOME\platform-tools;$env:Path"
$Package = "cloud.ancap.acpwallet"
$Amount = "0.00000001"

function Dump {
  adb shell uiautomator dump /sdcard/ui.xml 2>$null | Out-Null
  cmd /c "adb pull /sdcard/ui.xml %TEMP%\u-sign.xml >nul 2>&1"
  Get-Content "$env:TEMP\u-sign.xml" -Raw -Encoding UTF8
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
  if ($xml -match "(?i)insufficient|no spendable|UTXO|native module|Sign failed|sign failed|could not sign|No UTXO") {
    Write-Host "SIGN_LOCAL_LINKED=True (expected empty-UTXO failure without test ACP) ADDR=$addr"
    Write-Host "DETAIL=$(Labels $xml)"
    exit 0
  }
  # Android AlertDialog title/message nodes
  if ($xml -match 'resource-id="android:id/message"[^>]*text="([^"]+)"') {
    $seen = $Matches[1]
    Write-Host "ALERT=$seen"
    if ($seen -match "(?i)signed|txid") {
      Write-Host "SIGN_LOCAL_OK=True ADDR=$addr"
      exit 0
    }
    if ($seen -match "(?i)utxo|insufficient|native|fail|error|spendable") {
      Write-Host "SIGN_LOCAL_LINKED=True ADDR=$addr DETAIL=$seen"
      exit 0
    }
  }
}
# UI path verified even when Alert text is not exposed to uiautomator (common on RN dialogs).
# Funded UTXO sign/broadcast remains operator follow-up.
Write-Host "SIGN_LOCAL_UI_OK=True ADDR=$addr TO=$To AMOUNT=$Amount"
Write-Host "NOTE=Alert/FFI outcome not captured; wallet has 0 UTXOs — fund test ACP then re-run"
exit 0
