# Read-only endpoint inventory. Never print credentials or disable another AV.
$ErrorActionPreference = 'Stop'
$products = @(Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct -ErrorAction SilentlyContinue |
    Select-Object displayName, productState)
$defender = Get-MpComputerStatus -ErrorAction SilentlyContinue
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
[pscustomobject]@{
    IsAdministrator = $admin
    AntivirusProducts = $products
    DefenderRealtime = $defender.RealTimeProtectionEnabled
    DefenderTamperProtection = $defender.IsTamperProtected
    DockerAvailable = [bool](Get-Command docker -ErrorAction SilentlyContinue)
    WindowsSandboxAvailable = [bool](Get-Command WindowsSandbox.exe -ErrorAction SilentlyContinue)
    Note = 'Registered antivirus is not proof of active protection. Verify the installed product dashboard. Never run an external assignment on the credential-bearing host.'
} | ConvertTo-Json -Depth 4
