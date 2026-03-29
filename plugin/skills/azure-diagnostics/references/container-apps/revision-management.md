# Container Apps Revision Management Troubleshooting

Diagnose and resolve revision-related issues with Azure Container Apps.

## Stuck Revisions

### Symptom: Revision stuck in "Provisioning" or "Failed" state

**Diagnose:**
```bash
# List all revisions with status
az containerapp revision list --name APP -g RG -o table

# Show details of the stuck revision
az containerapp revision show --name APP -g RG --revision REV_NAME \
  --query "{name:name,active:properties.active,healthState:properties.healthState,provisioningState:properties.provisioningState,createdTime:properties.createdTime}"

# Check system logs for provisioning errors
az containerapp logs show --name APP -g RG --type system --tail 100
```

**Common causes:**
- Image pull failure on the new revision
- Health probe failing during provisioning
- Resource limit exceeded (CPU/memory)
- Invalid configuration (wrong port, missing secrets)

**Fix:**
```bash
# Deactivate the failed revision
az containerapp revision deactivate --name APP -g RG --revision REV_NAME

# Activate a known-good revision
az containerapp revision activate --name APP -g RG --revision GOOD_REV
```

## Traffic Splitting Issues

### Symptom: Traffic not routing to expected revision

**Diagnose:**
```bash
# Check traffic distribution
az containerapp ingress traffic show --name APP -g RG

# List active revisions
az containerapp revision list --name APP -g RG \
  --query "[?properties.active==\`true\`].{name:name,trafficWeight:properties.trafficWeight}" -o table
```

**Common causes:**
- Target revision is not active
- Traffic weights do not sum to 100
- Revision health state is "Unhealthy"

**Fix:**
```bash
# Set traffic split between revisions
az containerapp ingress traffic set --name APP -g RG \
  --revision-weight REV1=80 REV2=20

# Route all traffic to latest revision
az containerapp ingress traffic set --name APP -g RG \
  --revision-weight latest=100
```

## Revision Mode Issues

### Single vs Multi-Revision Mode

**Check current mode:**
```bash
az containerapp show --name APP -g RG \
  --query "properties.configuration.activeRevisionsMode"
```

| Mode | Behavior |
|------|----------|
| `Single` | Only the latest revision is active. Previous revisions are deactivated automatically. |
| `Multiple` | Multiple revisions can be active simultaneously. Supports traffic splitting. |

**Switch to multi-revision mode:**
```bash
az containerapp revision set-mode --name APP -g RG --mode multiple
```

**Switch to single-revision mode:**
```bash
# Warning: this deactivates all revisions except the latest
az containerapp revision set-mode --name APP -g RG --mode single
```

## Old Revisions Not Cleaning Up

### Symptom: Too many inactive revisions

Container Apps retains up to 100 inactive revisions. To clean up:

```bash
# List inactive revisions sorted by date
az containerapp revision list --name APP -g RG \
  --query "[?properties.active==\`false\`].{name:name,created:properties.createdTime}" \
  --output table

# Revisions are automatically cleaned up when the limit is reached
# (oldest inactive revisions are removed first)
```

## Rolling Back to a Previous Revision

```bash
# 1. List available revisions
az containerapp revision list --name APP -g RG -o table

# 2. Activate the target revision
az containerapp revision activate --name APP -g RG --revision TARGET_REV

# 3. Route traffic to it
az containerapp ingress traffic set --name APP -g RG \
  --revision-weight TARGET_REV=100

# 4. Deactivate the problematic revision
az containerapp revision deactivate --name APP -g RG --revision BAD_REV
```

## References

- [Container Apps revisions](https://learn.microsoft.com/azure/container-apps/revisions)
- [Traffic splitting](https://learn.microsoft.com/azure/container-apps/traffic-splitting)
