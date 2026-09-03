# 01 - Read-only preflight

**Implemented:** local prerequisite inspection.  
**Deployment scaffold:** opt-in read-only Azure and Kubernetes inspection.  
**Deferred validation:** running those live queries against the reserved cluster.

## Default local check

```powershell
.\scripts\preflight.ps1
```

```bash
bash ./scripts/preflight.sh
```

The default checks Python 3.11+ and reports whether optional `az`, `kubectl`,
and Docker commands exist. Their absence does not block Python tests. The
script does not authenticate, select a subscription, read a kubeconfig, or
contact a cluster by default.

## Explicit read-only inspection for later

After an operator has separately authenticated and approved the target:

```powershell
.\scripts\preflight.ps1 -InspectAzure `
  -SubscriptionId "<subscription-id>" `
  -ResourceGroup "<resource-group>" `
  -ConnectedEnvironment "<connected-environment>"

.\scripts\preflight.ps1 -InspectKubernetes -KubeContext "<context>"
```

```bash
bash ./scripts/preflight.sh --inspect-azure \
  --subscription-id "<subscription-id>" \
  --resource-group "<resource-group>" \
  --connected-environment "<connected-environment>"

bash ./scripts/preflight.sh --inspect-kubernetes --kube-context "<context>"
```

Angle-bracket values are placeholders and must never be pasted literally.
These modes only invoke show/get operations and never sign in. Review the
commands in the scripts before use; installed CLI versions and permissions can
change. Keep subscription IDs and resource names in local operator input, not
checked-in files.

## Preflight acceptance criteria

- Local tests pass without Docker, Azure, or Kubernetes.
- The operator verifies the selected Azure account separately.
- The named connected environment can be read.
- The explicitly selected Kubernetes context can list namespaces.
- No command in the preflight changes cloud or cluster state.
