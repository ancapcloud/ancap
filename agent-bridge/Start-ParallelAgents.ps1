$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $env:LOCALAPPDATA 'hermes\hermes-agent\venv\Scripts\python.exe'
$taskOllama = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
$taskVars = @{
    OLLAMA_NUM_PARALLEL = '1'
    OLLAMA_MAX_LOADED_MODELS = '1'
    OLLAMA_CONTEXT_LENGTH = '65536'
    OLLAMA_FLASH_ATTENTION = '1'
    OLLAMA_KV_CACHE_TYPE = 'q8_0'
    OLLAMA_KEEP_ALIVE = '30m'
}
foreach ($taskPair in $taskVars.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($taskPair.Key, $taskPair.Value, 'Process')
}
New-Item -ItemType Directory -Force -Path "$taskRoot\runtime" | Out-Null
if (Test-Path "$taskRoot\runtime\STOP") { exit 0 }
try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 3 | Out-Null }
catch {
    Start-Process -FilePath $taskOllama -ArgumentList 'serve' -WindowStyle Hidden `
        -RedirectStandardOutput "$taskRoot\runtime\ollama.log" `
        -RedirectStandardError "$taskRoot\runtime\ollama.err.log" | Out-Null
    $taskReady = $false
    for ($taskTry = 0; $taskTry -lt 30; $taskTry++) {
        Start-Sleep -Seconds 2
        try { Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2 | Out-Null; $taskReady = $true; break } catch {}
    }
    if (-not $taskReady) { throw 'Ollama did not become ready.' }
}
& $taskPython "$taskRoot\coordinator.py"
exit $LASTEXITCODE
