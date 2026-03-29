# Kubernetes to Azure Container Apps Migration

Migrate containerized workloads from Kubernetes clusters (on-premises or other cloud providers) to Azure Container Apps.

## Scope

This guide covers migration from **self-hosted Kubernetes** and **third-party managed Kubernetes** (e.g., GKE, EKS) to Azure Container Apps. It does **not** cover migration between Azure services.

## When to Use

- Kubernetes workloads running on-premises or on non-Azure cloud providers
- Teams seeking to reduce Kubernetes operational overhead
- Workloads that do not require custom CRDs, operators, or full Kubernetes API access
- Microservices, APIs, background workers, and event-driven applications

## Prerequisites

- `kubectl` access to the source Kubernetes cluster
- Azure CLI with `containerapp` extension installed
- Azure Container Registry (ACR) for storing container images

## Phase 1: Export Kubernetes Resources

### Identify Target Workloads

```bash
# List deployments in the target namespace
kubectl get deployments -n NAMESPACE -o wide

# List services
kubectl get services -n NAMESPACE -o wide

# List ingress resources
kubectl get ingress -n NAMESPACE
```

### Export Resource Definitions

```bash
# Export a specific deployment
kubectl get deployment DEPLOY_NAME -n NAMESPACE -o yaml > deployment.yaml

# Export associated service
kubectl get service SVC_NAME -n NAMESPACE -o yaml > service.yaml

# Export all resources in a namespace
kubectl get deploy,svc,ingress,configmap,secret -n NAMESPACE -o yaml > namespace-export.yaml
```

## Phase 2: Assess Compatibility

Load [assessment.md](assessment.md) and evaluate each workload against the compatibility matrix.

### Key Mapping: Kubernetes → Container Apps

| Kubernetes Concept | Container Apps Equivalent | Notes |
|-------------------|--------------------------|-------|
| Deployment | Container App | One-to-one mapping for most workloads |
| Service (ClusterIP) | Internal ingress | Set `external: false` |
| Service (LoadBalancer) | External ingress | Set `external: true` |
| Ingress | Built-in ingress with custom domain | Supports TLS, traffic splitting |
| ConfigMap | Environment variables | Inline or from secrets |
| Secret | Secrets (Key Vault refs preferred) | Use managed identity for Key Vault |
| CronJob | Container Apps Job (scheduled) | Cron expression syntax |
| Job | Container Apps Job (manual/event) | One-time or event-triggered |
| HPA | Built-in scaling rules | HTTP, TCP, KEDA-compatible scalers |
| PersistentVolumeClaim | Azure Files mount | Limited persistent storage support |
| DaemonSet | ❌ Not supported | Consider sidecar containers instead |
| StatefulSet | ❌ Not supported | Use external state (Cosmos DB, Redis, SQL) |
| Custom CRDs / Operators | ❌ Not supported | Evaluate if Dapr components can replace |

### Unsupported Patterns

Refer to [global-rules.md](global-rules.md) for the full list. Key blockers:
- DaemonSets, StatefulSets, custom operators
- Privileged containers or host networking
- Workloads needing >4 vCPU or >8 GiB per container
- Direct Kubernetes API access from application code

## Phase 3: Migrate Container Images

```bash
# Login to ACR
az acr login --name ACRNAME

# Tag and push images
docker tag SOURCE_IMAGE ACRNAME.azurecr.io/APPNAME:TAG
docker push ACRNAME.azurecr.io/APPNAME:TAG

# Or import directly from another registry
az acr import --name ACRNAME \
  --source REGISTRY/IMAGE:TAG \
  --image APPNAME:TAG
```

## Phase 4: Generate Bicep

Follow [code-migration.md](code-migration.md) to generate Bicep templates. Map each Kubernetes resource:

### Deployment → Container App

Key properties to translate:
- `spec.containers[].image` → `template.containers[].image`
- `spec.containers[].ports` → `ingress.targetPort`
- `spec.containers[].env` → `template.containers[].env`
- `spec.containers[].resources` → `template.containers[].resources`
- `spec.replicas` → `scale.minReplicas` / `scale.maxReplicas`

### Service Type → Ingress Configuration

| K8s Service Type | ACA Ingress |
|-----------------|-------------|
| ClusterIP | `external: false`, `targetPort: PORT` |
| LoadBalancer | `external: true`, `targetPort: PORT` |
| NodePort | `external: true`, `targetPort: PORT` |

### Environment Variables

```bicep
env: [
  // Direct values (from ConfigMaps)
  { name: 'VAR_NAME', value: 'value' }
  // Secret references (from Secrets)
  { name: 'SECRET_VAR', secretRef: 'secret-name' }
]
```

## Phase 5: Deploy and Validate

1. Deploy using `az deployment group create` or `azd up`
2. Verify endpoints are accessible
3. Run smoke tests against migrated services
4. Compare response behavior with source cluster
5. Migrate DNS and traffic gradually using traffic splitting

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Image pull failure | ACR credentials not configured | `az containerapp registry set --identity system` |
| Port mismatch (502/503) | `targetPort` doesn't match app | Check Dockerfile EXPOSE and app listen port |
| OOM / resource limits | Container exceeds ACA limits | Reduce to ≤4 vCPU and ≤8 GiB per container |
| DNS resolution between apps | Wrong internal ingress name | Use `APP_NAME.internal.ENVIRONMENT.REGION.azurecontainerapps.io` |

## References

- [Assessment Framework](assessment.md)
- [Code Migration Guide](code-migration.md)
- [ACA Constraints](global-rules.md)
