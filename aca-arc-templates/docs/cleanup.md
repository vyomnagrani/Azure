# Safe cleanup

Cleanup is **Deployment scaffold** and has not been executed.

The scripts are dry-run by default:

```powershell
.\scripts\cleanup.ps1
.\scripts\cleanup.ps1 -SubscriptionId "<subscription-id>" `
  -ResourceGroup "<resource-group>"
```

```bash
bash ./scripts/cleanup.sh
bash ./scripts/cleanup.sh --subscription-id "<subscription-id>" \
  --resource-group "<resource-group>"
```

With identifiers, dry-run prints a redacted command but does not invoke Azure.
The scripts reject app names that do not begin with `contoso-edge-store`.

## Later execution gate

Only after a human verifies the subscription, resource group, app name,
ownership, and impact may they add both the execute flag and literal
`DELETE-CONTOSO-EDGE-STORE` confirmation. Review the script immediately before
execution. It deletes only the named Container App.

The scripts never delete:

- an Arc connection or Kubernetes cluster,
- a resource group,
- a container registry or image repository,
- a custom location or connected environment,
- a Log Analytics workspace or other shared logging resource.

Local cleanup is simply stopping Uvicorn and optionally removing `.venv`,
`.env`, and generated caches using normal file management. Never treat the
repository directory itself as disposable.
