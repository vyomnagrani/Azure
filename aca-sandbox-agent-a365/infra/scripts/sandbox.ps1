[CmdletBinding()]
param(
    [ValidateSet('preflight', 'build-image', 'create', 'image', 'port', 'port-remove', 'endpoint', 'egress', 'stop', 'snapshot', 'resume', 'identity-check', 'delete')]
    [string] $Action = 'preflight',
    [string] $Subscription = $env:AZURE_SUBSCRIPTION_ID,
    [string] $ResourceGroup = $env:AZURE_RESOURCE_GROUP,
    [string] $Group = $env:ACA_SANDBOX_GROUP,
    [string] $Region = $(if ($env:ACA_SANDBOX_REGION) { $env:ACA_SANDBOX_REGION } else { $env:AZURE_LOCATION }),
    [string] $IdentityResourceId = $env:AZURE_MANAGED_IDENTITY_RESOURCE_ID,
    [string] $Registry = $env:AZURE_CONTAINER_REGISTRY_NAME,
    [string] $SandboxId,
    [string] $Disk = 'ubuntu',
    [string] $DiskId,
    [string] $Snapshot,
    [string] $Name,
    [string] $Image,
    [string] $Repository = 'aca-sandbox-agent-a365',
    [string] $Tag = 'dev',
    [string] $ProjectRoot = $(Resolve-Path (Join-Path $PSScriptRoot '..\..')),
    [int] $Port = 8000,
    [string[]] $AllowHost = @(),
    [string[]] $Environment = @(),
    [string] $Entrypoint,
    [switch] $Execute,
    [string] $ConfirmDelete
)

$ErrorActionPreference = 'Stop'

function Write-IdentityGate {
    @'

Agent identity gate:
  Do not enable live Agent 365 mode until identity-check succeeds for a sandbox.
  The group-level UAMI is the intended credential; no secret is emitted here.

This sample does not implement a certificate runtime path. If the identity
probe fails, keep live mode disabled rather than adding a client secret.
'@ | Write-Host
}

function Test-CommandExists([string] $Command) {
    return $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Assert-Azure {
    if (-not (Test-CommandExists 'az')) {
        throw 'Missing prerequisite: az. See https://learn.microsoft.com/cli/azure/install-azure-cli'
    }
    & az account show --output none
    if ($LASTEXITCODE -ne 0) { throw 'Azure CLI is not signed in. Run: az login' }
}

function Assert-Tools {
    Assert-Azure
    if (-not (Test-CommandExists 'aca')) {
        throw 'Missing prerequisite: aca. Install with: irm https://aka.ms/aca-cli-install-ps | iex'
    }
}

function Assert-Context {
    $missing = @()
    if (-not $Subscription) { $missing += 'Subscription/AZURE_SUBSCRIPTION_ID' }
    if (-not $ResourceGroup) { $missing += 'ResourceGroup/AZURE_RESOURCE_GROUP' }
    if (-not $Group) { $missing += 'Group/ACA_SANDBOX_GROUP' }
    if (-not $Region) { $missing += 'Region/ACA_SANDBOX_REGION' }
    if ($missing.Count -gt 0) { throw "Missing context: $($missing -join ', ')" }
}

function Assert-SandboxId {
    if (-not $SandboxId) { throw "SandboxId is required for $Action." }
}

function Assert-Execute {
    if (-not $Execute) { throw "Dry stop: '$Action' changes Azure state. Re-run with -Execute." }
}

function Get-CommonArgs {
    return @('-s', $Subscription, '-g', $ResourceGroup, '--group', $Group, '--region', $Region)
}

switch ($Action) {
    'preflight' {
        Write-Host 'ACA Sandbox infrastructure preflight'
        Write-Host 'Preview assumptions: Microsoft.App/sandboxGroups@2026-02-01-preview; aca CLI command surface is checked at runtime.'
        if (-not (Test-CommandExists 'az')) {
            Write-Warning 'Azure CLI is not installed. See https://learn.microsoft.com/cli/azure/install-azure-cli'
        }
        else {
            & az account show --output none 2>$null
            if ($LASTEXITCODE -eq 0) { Write-Host 'OK: Azure CLI authenticated.' }
            else { Write-Warning 'Azure CLI is installed but not signed in; run az login.' }
        }

        if (-not (Test-CommandExists 'aca')) {
            Write-Warning 'ACA CLI preview is not installed. Install with: irm https://aka.ms/aca-cli-install-ps | iex'
        }
        else {
            Write-Host "OK: $((& aca --version 2>&1 | Select-Object -First 1))"
            $commands = @(
                @('sandbox', 'create'),
                @('sandboxgroup', 'disk', 'create'),
                @('sandbox', 'port', 'add'),
                @('sandbox', 'egress', 'set'),
                @('sandbox', 'stop'),
                @('sandbox', 'snapshot'),
                @('sandbox', 'resume'),
                @('sandbox', 'delete'),
                @('sandboxgroup', 'identity', 'show')
            )
            foreach ($command in $commands) {
                & aca @command --help *> $null
                if ($LASTEXITCODE -eq 0) { Write-Host "OK: aca $($command -join ' ')" }
                else { Write-Warning "Installed preview CLI does not advertise 'aca $($command -join ' ')'." }
            }
        }

        if ($Subscription -and $ResourceGroup -and $Group -and (Test-CommandExists 'az')) {
            $resourceId = "/subscriptions/$Subscription/resourceGroups/$ResourceGroup/providers/Microsoft.App/sandboxGroups/$Group"
            $identityType = & az resource show --ids $resourceId --api-version 2026-02-01-preview --query identity.type -o tsv 2>$null
            if ($LASTEXITCODE -eq 0 -and $identityType -like '*UserAssigned*') {
                Write-Host 'OK: sandbox group has a user-assigned managed identity.'
            }
            else {
                Write-Warning 'Sandbox group was not found or does not report UserAssigned identity.'
            }
            Write-Host 'Operator prerequisite: assign Container Apps SandboxGroup Data Owner to the signed-in user at the group scope.'
            Write-Host "  aca sandboxgroup role create --group '$Group' --role 'Container Apps SandboxGroup Data Owner' --principal-id <SIGNED_IN_USER_OBJECT_ID>"
        }
        else {
            Write-Host 'INFO: Azure context is incomplete; ARM identity verification was skipped.'
        }
        Write-IdentityGate
    }
    'create' {
        Assert-Tools; Assert-Context; Assert-Execute
        $argsList = @('sandbox', 'create') + (Get-CommonArgs) +
            @('--label', 'sample=aca-sandbox-agent-a365', '--egress-default', 'Deny', '--traffic-inspection', 'Full')
        if ($Snapshot) { $argsList += @('--snapshot', $Snapshot) }
        elseif ($DiskId) { $argsList += @('--disk-id', $DiskId) }
        else { $argsList += @('--disk', $Disk) }
        if ($Entrypoint) { $argsList += @('--entrypoint', $Entrypoint) }
        foreach ($setting in $Environment) { $argsList += @('--env', $setting) }
        foreach ($hostName in $AllowHost) { $argsList += @('--egress-rule', "${hostName}:Allow") }
        & aca @argsList
        if ($LASTEXITCODE -ne 0) { throw 'Sandbox creation failed.' }
    }
    'build-image' {
        Assert-Azure; Assert-Context; Assert-Execute
        if (-not $Registry) { throw 'Registry or AZURE_CONTAINER_REGISTRY_NAME is required for build-image.' }
        $dockerfile = Join-Path $ProjectRoot 'Dockerfile'
        if (-not (Test-Path $dockerfile -PathType Leaf)) { throw "Dockerfile not found under ProjectRoot: $ProjectRoot" }
        & az acr build --subscription $Subscription --registry $Registry --image "${Repository}:${Tag}" --file $dockerfile $ProjectRoot
        if ($LASTEXITCODE -ne 0) { throw 'Container image build failed.' }
        Write-Host "OCI image: ${Registry}.azurecr.io/${Repository}:${Tag}"
    }
    'image' {
        Assert-Tools; Assert-Context; Assert-Execute
        if (-not $Image -or -not $Name) { throw 'Image and Name are required for image.' }
        $argsList = @('sandboxgroup', 'disk', 'create') + (Get-CommonArgs) + @('--image', $Image, '--name', $Name)
        if ($Image -like '*.azurecr.io/*') {
            if (-not $IdentityResourceId) { throw 'Private ACR image requires IdentityResourceId.' }
            $helpText = (& aca sandboxgroup disk create --help 2>&1) -join "`n"
            if ($helpText -match '(?m)^\s+--registry-identity(?:\s|<)') { $argsList += @('--registry-identity', $IdentityResourceId) }
            elseif ($helpText -match '(?m)^\s+--identity(?:\s|<)') { $argsList += @('--identity', $IdentityResourceId) }
            else {
                throw 'Installed aca CLI cannot safely express private-registry identity. Use current CLI help or the portal; no credential fallback is attempted.'
            }
        }
        & aca @argsList
        if ($LASTEXITCODE -ne 0) { throw 'Disk image creation failed.' }
    }
    'port' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        Write-Warning 'This creates an anonymous public HTTPS endpoint.'
        $commonArgs = Get-CommonArgs
        & aca sandbox port add @commonArgs --id $SandboxId --port $Port --anonymous -o json
        if ($LASTEXITCODE -ne 0) { throw 'Port exposure failed.' }
    }
    'port-remove' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        $commonArgs = Get-CommonArgs
        & aca sandbox port remove @commonArgs --id $SandboxId --port $Port
        if ($LASTEXITCODE -ne 0) { throw 'Port removal failed.' }
    }
    'endpoint' {
        Assert-Tools; Assert-Context; Assert-SandboxId
        Write-Host 'Inspect the ports/endpoints fields in this response:'
        $commonArgs = Get-CommonArgs
        & aca sandbox get @commonArgs --id $SandboxId -o json
        if ($LASTEXITCODE -ne 0) { throw 'Endpoint discovery failed.' }
    }
    'egress' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        $argsList = @('sandbox', 'egress', 'set') + (Get-CommonArgs) +
            @('--id', $SandboxId, '--default', 'Deny', '--traffic-inspection', 'Full')
        foreach ($hostName in $AllowHost) { $argsList += @('--rule', "${hostName}:Allow") }
        & aca @argsList
        if ($LASTEXITCODE -ne 0) { throw 'Egress policy update failed.' }
    }
    'stop' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        $commonArgs = Get-CommonArgs
        & aca sandbox stop @commonArgs --id $SandboxId
        if ($LASTEXITCODE -ne 0) { throw 'Sandbox stop failed.' }
    }
    'snapshot' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        if (-not $Name) { throw 'Name is required for snapshot.' }
        $commonArgs = Get-CommonArgs
        & aca sandbox snapshot @commonArgs --id $SandboxId --name $Name
        if ($LASTEXITCODE -ne 0) { throw 'Snapshot failed.' }
    }
    'resume' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        Write-Warning 'Resume restarts compute billing.'
        $commonArgs = Get-CommonArgs
        & aca sandbox resume @commonArgs --id $SandboxId
        if ($LASTEXITCODE -ne 0) { throw 'Sandbox resume failed.' }
    }
    'identity-check' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        Write-Host 'Checking only for identity endpoint/header presence; no token is requested or printed.'
        $probe = 'test -n "${IDENTITY_ENDPOINT:-}" && { test -n "${IDENTITY_HEADER:-}" || test -n "${MSI_ENDPOINT:-}"; }'
        $commonArgs = Get-CommonArgs
        & aca sandbox exec @commonArgs --id $SandboxId -c $probe
        if ($LASTEXITCODE -eq 0) {
            Write-Host 'PASS: managed-identity runtime capability is present.'
        }
        else {
            Write-Host 'FAIL: managed-identity runtime capability was not detected.'
            Write-IdentityGate
            throw 'Identity capability gate failed.'
        }
    }
    'delete' {
        Assert-Tools; Assert-Context; Assert-SandboxId; Assert-Execute
        if ($ConfirmDelete -cne $SandboxId) {
            throw 'Deletion refused. Pass ConfirmDelete with the exact SandboxId.'
        }
        $commonArgs = Get-CommonArgs
        & aca sandbox delete @commonArgs --id $SandboxId --yes
        if ($LASTEXITCODE -ne 0) { throw 'Sandbox deletion failed.' }
    }
}
