param(
    [Parameter(Mandatory=$true)][string]$SshTarget,
    [Parameter(Mandatory=$true)][string]$IdentityFile
)
$ErrorActionPreference = 'Continue'
Set-Location (Split-Path $PSScriptRoot -Parent)
# Only a dedicated forwarding key is used; ignore broad identities from ssh config.
while ($true) {
    & docker compose --env-file .env.wevisone -f docker-compose.wevisone.yml up -d wevisone
    if ($LASTEXITCODE -eq 0) {
        & ssh -F none -i $IdentityFile -o BatchMode=yes -o IdentitiesOnly=yes `
            -o StrictHostKeyChecking=yes -o ExitOnForwardFailure=yes `
            -o ServerAliveInterval=30 -o ServerAliveCountMax=3 `
            -N -T -R 127.0.0.1:18097:127.0.0.1:8097 $SshTarget
    }
    Start-Sleep -Seconds 20
}
