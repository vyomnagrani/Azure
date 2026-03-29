# Container Apps Global Rules

Constraints, limits, and unsupported features for Azure Container Apps migrations.

## Resource Limits

| Resource | Limit | Notes |
|----------|-------|-------|
| vCPU per container | 4 max | Consumption plan |
| Memory per container | 8 GiB max | Consumption plan |
| Replicas per app | 300 max | Across all revisions |
| Apps per environment | 100 max | Soft limit, can request increase |
| Containers per app | 10 max | Including init and sidecar containers |
| Ingress timeout | 240 seconds max | For long-running requests |

## Unsupported Kubernetes Features

These Kubernetes features have **no direct equivalent** in Container Apps:

| Feature | Why Not Supported | Alternative |
|---------|------------------|-------------|
| DaemonSets | No node-level access | Use sidecar containers or external agents |
| StatefulSets | No stable network IDs or ordered deployment | Use external state stores (Cosmos DB, Redis, SQL) |
| Custom CRDs / Operators | No Kubernetes API | Evaluate Dapr components or Azure-native services |
| Privileged containers | Security boundary | Redesign without host access |
| Host networking | Managed networking | Use VNet integration for network control |
| hostPath volumes | No node filesystem | Use Azure Files or ephemeral storage |
| Pod affinity / anti-affinity | Managed scheduling | Rely on ACA's built-in distribution |

## Networking Rules

- Internal apps communicate via `APP_NAME.internal.ENV_UNIQUE_ID.REGION.azurecontainerapps.io`
- External apps get automatic HTTPS with managed certificates
- Custom domains require DNS validation and certificate configuration
- VNet integration available for private networking scenarios
- No direct pod-to-pod communication by IP — use service names

## Security Rules

- All containers run as non-root by default
- No privileged mode or host namespace access
- Secrets stored in ACA secrets or Azure Key Vault (preferred)
- Use managed identity for all Azure service authentication
- Never hardcode credentials in Bicep templates or environment variables

## Migration Rules

- Never modify the source directory — all output goes to `<source-folder>-azure/`
- Generate assessment before any code migration
- Confirm target subscription and region with the user
- Destructive actions (deleting source resources) require explicit user approval
- Document all assumptions and decisions in the migration report
