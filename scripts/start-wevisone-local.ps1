param([switch]$WorkerOnly)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path -LiteralPath '.env.wevisone')) {
    $bytes = New-Object byte[] 48
    $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $token = [Convert]::ToBase64String($bytes)
    [IO.File]::WriteAllText((Join-Path $PWD '.env.wevisone'), "SMART_PAY_WEVISONE_API_KEY=$token`n")
}
$services = if ($WorkerOnly) { @('wevisone') } else { @('wevisone', 'api', 'web') }
& docker compose --env-file .env.wevisone -f docker-compose.wevisone.yml up -d --build @services
if ($LASTEXITCODE -ne 0) { throw 'Docker startup failed; inspect Compose logs.' }
Write-Host 'First launch downloads the pinned 2B model. Follow: docker compose --env-file .env.wevisone -f docker-compose.wevisone.yml logs -f wevisone api'
Write-Host 'Local Smart Pay: http://localhost:3001/payment-scanner (register a local test account).'
