# Sandbox lifecycle operations

Azure Container Apps Sandboxes are a preview, stateful compute option—not
dynamic sessions. A sandbox group is the ARM management boundary; individual
sandboxes, ports, snapshots, files, and lifecycle actions use the data plane.

## Command policy

The preview CLI/SDK surface can change. The authoritative executable operations
for this repository are the scripts checked into `infra/scripts/`, not commands
copied from this guide.

```powershell
# Implemented: inventory the exact wrappers in your revision.
Get-ChildItem .\infra\scripts -File | Sort-Object Name | Select-Object Name

# Implemented: inspect the selected wrapper before running it.
Get-Content .\infra\scripts\<replace-with-an-actual-listed-file>
```

The second line contains a **placeholder** and is intentionally not paste-ready.
Select an actual filename from the first command. Read the script's documented
parameters/help and confirm subscription, tenant, resource group, sandbox group,
and sandbox name before any mutating action.

Do not substitute guessed `az containerapp sandbox` flags. The wrappers exist
to pin the contract and consistently obtain Entra tokens, endpoints, and IDs.

## PowerShell customer journey

The following commands call the **implemented repository wrapper**, not the
preview CLI directly. Values in angle brackets are **placeholders**. Obtain the
Azure context from your provisioned `azd` environment and record the sandbox ID
returned by create.

```powershell
$subscription = "<subscription-id>"
$resourceGroup = "<resource-group>"
$group = "<sandbox-group>"
$region = "<azure-region>"
$registry = "<acr-name>"
$identityResourceId = "<uami-resource-id>"
$diskName = "aca-sandbox-agent-a365"
$diskId = "<private-disk-id-returned-by-image>"
$sandboxId = "<sandbox-id-returned-by-create>"

# Safe capability check; this does not create a sandbox.
.\infra\scripts\sandbox.ps1 -Action preflight `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region

# Build the deployable image in ACR.
.\infra\scripts\sandbox.ps1 -Action build-image `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -Registry $registry -Tag dev -Execute

# Convert the private OCI image to a Sandbox disk and record the returned ID.
.\infra\scripts\sandbox.ps1 -Action image `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region `
  -Image "$registry.azurecr.io/aca-sandbox-agent-a365:dev" `
  -Name $diskName -IdentityResourceId $identityResourceId -Execute

# Create from that private disk. Add only reviewed -AllowHost values and
# non-secret -Environment KEY=VALUE settings. Supply secret settings only
# through an approved operator procedure that does not retain command history.
.\infra\scripts\sandbox.ps1 -Action create `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -DiskId $diskId `
  -Execute

# Expose only FastAPI port 8000. The wrapper warns that this endpoint is anonymous.
.\infra\scripts\sandbox.ps1 -Action port `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId -Port 8000 -Execute

# Rediscover the current endpoint without mutating the sandbox.
.\infra\scripts\sandbox.ps1 -Action endpoint `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId

# Capture a checkpoint while the workload is in a known-good state.
.\infra\scripts\sandbox.ps1 -Action snapshot `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId `
  -Name "<snapshot-name>" -Execute

# Stop the sandbox, and later resume the same sandbox.
.\infra\scripts\sandbox.ps1 -Action stop `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId -Execute
.\infra\scripts\sandbox.ps1 -Action resume `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId -Execute

# Destructive: the second ID is an exact, case-sensitive confirmation.
.\infra\scripts\sandbox.ps1 -Action delete `
  -Subscription $subscription -ResourceGroup $resourceGroup `
  -Group $group -Region $region -SandboxId $sandboxId `
  -ConfirmDelete $sandboxId -Execute
```

Create from an existing snapshot by replacing `-DiskId $diskId` in the create call
with `-Snapshot "<approved-snapshot-name>"`. The create action is the sample's
restore path. Do not set `$sandboxId` until create returns the actual ID.

The `port` action creates an **anonymous public HTTPS endpoint**. “Anonymous”
describes network access to the endpoint; live application APIs must still
validate the bearer token. Do not expose the port until that authentication
gate has been tested, and remove the sandbox when the exercise ends.

For bash, run `./infra/scripts/sandbox.sh --help` and use the corresponding
action. Its mutating guard is `--execute`; delete additionally requires
`--confirm-delete` with the exact ID.

## Provisioning boundary

Infrastructure-as-code creates the sandbox group, identity, registry/image
resources, Foundry resources, monitoring, policy, and role assignments. Data
plane scripts then create and operate the individual sandbox.

Before provisioning:

1. Run offline tests.
2. Review `.azure/deployment-plan.md`, `azure.yaml`, and all `infra/` changes.
3. Verify `az account show` and `azd env get-values` point to the intended
   tenant/subscription/environment. Do not post their output; it can contain
   sensitive configuration.
4. Verify regional Sandbox and selected Foundry model availability/quota.
5. Run the repository's Azure validation step.
6. Obtain a change/cost approval. Provisioning incurs Azure charges.

Use `azd provision`/`azd up` only when the checked-in `azure.yaml` and
infrastructure documentation in your revision define those hooks. These are
standard Azure Developer CLI commands, not sandbox data-plane syntax.

## Lifecycle journey

| Action | Use the repository wrapper that… | Verify before continuing |
| --- | --- | --- |
| **Create** | creates a sandbox from the approved disk image with the configured lifecycle policy. | State is `Running`; expected image/tier/labels; no unexpected secret or public egress. |
| **Expose** | exposes only the application port and returns the assigned endpoint. | TLS endpoint works; `/health` reports expected mode; no shell/debug/admin port is exposed. Treat the URL as sensitive if access is restricted. |
| **Stop** | explicitly suspends the sandbox using the group's Memory or Disk suspend mode. | State is `Stopped`; active requests completed; CPU/memory billing stopped. State-storage charges can continue. |
| **Snapshot** | captures a labeled, point-in-time sandbox snapshot. | Snapshot reaches ready state; labels include workload, owner, purpose, and retention date. A snapshot persists independently of its source. |
| **Resume** | resumes a stopped sandbox (Memory restores RAM+disk; Disk starts processes from preserved disk). | State is `Running`; health succeeds; identity/token clients recover; no request is replayed. |
| **Restore** | creates a new sandbox from an approved snapshot when rollback/clone is intended. | New sandbox inherits captured tier, entrypoint, command, environment, region; endpoint and identity assumptions are revalidated. |
| **Delete** | deletes the named sandbox after confirmation. | Sandbox no longer lists. Snapshots, volumes, group, identity, consent, and Agent 365 registration are checked separately. |

“Stop,” “snapshot,” “resume,” and “restore” are not synonyms:

- **Stop** follows the lifecycle suspend mode.
- **Snapshot** is an immutable independent checkpoint.
- **Resume** continues the same stopped sandbox.
- **Restore** creates another sandbox from a snapshot.

Snapshot restore cannot change the captured tier, entrypoint, command, or
environment. Snapshots are region-scoped and are not garbage-collected
automatically.

## Recommended operating sequence

```text
provision group -> create -> expose -> health check -> test
       -> stop/resume during idle periods
       -> snapshot only for a named checkpoint
       -> delete sandbox -> delete expired snapshots
```

- Start with Memory suspend mode for interactive agent state; consider Disk only
  when cold process restart is acceptable and storage cost matters.
- Configure auto-suspend and auto-delete, but do not rely on them as the sole
  cleanup mechanism.
- Drain or reject requests before stop/snapshot.
- Confirmation tokens are process-local. A suspend can preserve memory, but a
  Disk resume or new restore does not guarantee an outstanding token remains
  valid. Always request a new confirmation after a lifecycle transition.
- Established network connections can become stale despite memory restore.
  Health checks should cause clients to reconnect; never replay a send.

## Port and network safety

- Expose only the FastAPI application port; never SSH, a debugger, token broker
  ports, or a local credential endpoint.
- Use deny-by-default egress and allow only Entra, Work IQ, Foundry, telemetry,
  registry, and other reviewed dependencies.
- Do not expose a token broker or managed-identity endpoint. The current image
  performs direct UAMI-backed exchanges and has no sidecar.
- If a future custom/multi-process image adopts the optional Agent ID sidecar,
  keep it on loopback and add explicit startup, health, and lifecycle controls.
- Use VNet integration/private access where supported by the approved design.
- Run live mode only behind authentication. `/docs` should not expose secrets
  and may be disabled for a production-derived deployment.

## Full cleanup

Perform and verify each plane:

1. **Application:** stop traffic; invalidate external sessions; remove local
   `.env`; remove test drafts/messages according to policy.
2. **Sandbox data plane:** delete sandbox, all sample snapshots, exposed ports,
   volumes, secrets, and converted disk images as appropriate.
3. **Azure control plane:** remove the `azd` environment/resources using the
   repository's documented cleanup path. Confirm resource group deletion only
   if it was dedicated to this sample.
4. **Agent 365:** block/retire or delete the sample registration from the
   registry according to organizational policy.
5. **Entra:** revoke consent and remove the sample agent identity/blueprint,
   credentials/federation, roles, access packages, and sponsor relationship
   when no longer needed.
6. **Security/compliance:** retain or dispose of Defender/Purview/audit records
   according to policy, not merely because compute was deleted.

Never delete a shared blueprint, identity, resource group, snapshot, or
permission grant without checking for other consumers.
