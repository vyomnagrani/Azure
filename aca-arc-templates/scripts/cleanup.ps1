[CmdletBinding()]
param(
    [string]$SubscriptionId,
    [string]$ResourceGroup,
    [string]$AppName = "contoso-edge-store",
    [switch]$Execute,
    [string]$Confirmation
)

$ErrorActionPreference = "Stop"

if (-not $SubscriptionId -or -not $ResourceGroup) {
    Write-Host "Dry run: no Azure command will run."
    Write-Host "Potential sample-only target: Container App '$AppName'."
    Write-Host "Provide -SubscriptionId and -ResourceGroup to print the exact command."
    exit 0
}
if ($AppName -ne "contoso-edge-store") {
    throw "Refusing to delete any target other than the exact sample name 'contoso-edge-store'."
}

$display = "az containerapp delete --subscription <provided> --resource-group '$ResourceGroup' --name '$AppName'"
Write-Host "Sample-only cleanup command: $display"
Write-Host "This script never deletes clusters, resource groups, registries, or Log Analytics workspaces."

if (-not $Execute) {
    Write-Host "Dry run complete. Add -Execute -Confirmation DELETE-CONTOSO-EDGE-STORE to proceed."
    exit 0
}
if ($Confirmation -ne "DELETE-CONTOSO-EDGE-STORE") {
    throw "Execution requires -Confirmation DELETE-CONTOSO-EDGE-STORE."
}
if ($null -eq (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI is not installed."
}

& az containerapp delete `
    --subscription $SubscriptionId `
    --resource-group $ResourceGroup `
    --name $AppName `
    --yes
