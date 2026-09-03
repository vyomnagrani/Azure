[CmdletBinding()]
param(
    [switch]$InspectAzure,
    [string]$SubscriptionId,
    [string]$ResourceGroup,
    [string]$ConnectedEnvironment,
    [switch]$InspectKubernetes,
    [string]$KubeContext
)

$ErrorActionPreference = "Stop"

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

Write-Host "Contoso Edge Store local preflight (read-only)"
$failed = $false

if (Test-Command "python") {
    $version = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to query the installed Python version."
    }
    Write-Host "[found] Python $version"
    $supported = & python -c "import sys; print('yes' if sys.version_info >= (3, 11) else 'no')"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to verify the installed Python version."
    }
    if ($supported -ne "yes") {
        Write-Warning "Python 3.11 or later is required."
        $failed = $true
    }
} else {
    Write-Warning "[missing] Python"
    $failed = $true
}

foreach ($tool in @("az", "kubectl", "docker")) {
    $state = if (Test-Command $tool) { "found" } else { "not found (optional for local tests)" }
    Write-Host "[$state] $tool"
}

if ($InspectAzure) {
    if (-not $SubscriptionId) {
        throw "-InspectAzure requires -SubscriptionId."
    }
    if (-not (Test-Command "az")) {
        throw "Azure CLI is not installed."
    }
    Write-Host "Running explicitly requested read-only Azure queries. This script never signs in."
    & az account show --subscription $SubscriptionId --output table
    if ($LASTEXITCODE -ne 0) {
        throw "Azure subscription inspection failed."
    }
    if ($ResourceGroup -and $ConnectedEnvironment) {
        & az containerapp connected-env show `
            --subscription $SubscriptionId `
            --resource-group $ResourceGroup `
            --name $ConnectedEnvironment `
            --output table
        if ($LASTEXITCODE -ne 0) {
            throw "Connected environment inspection failed."
        }
    } elseif ($ResourceGroup -or $ConnectedEnvironment) {
        throw "Provide both -ResourceGroup and -ConnectedEnvironment, or neither."
    }
}

if ($InspectKubernetes) {
    if (-not $KubeContext) {
        throw "-InspectKubernetes requires -KubeContext."
    }
    if (-not (Test-Command "kubectl")) {
        throw "kubectl is not installed."
    }
    Write-Host "Running explicitly requested read-only Kubernetes query."
    & kubectl --context $KubeContext get namespaces
    if ($LASTEXITCODE -ne 0) {
        throw "Kubernetes inspection failed."
    }
}

if ($failed) { exit 1 }
Write-Host "Local preflight complete. No cloud or cluster state was changed."
