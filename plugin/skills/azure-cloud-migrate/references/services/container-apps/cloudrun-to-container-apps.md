# GCP Cloud Run to Azure Container Apps Migration

Migrate serverless container workloads from Google Cloud Run to Azure Container Apps.

## Scope

This guide covers migration from **GCP Cloud Run** services to Azure Container Apps. Both platforms offer serverless container hosting with similar scaling models.

## When to Use

- Cloud Run services being migrated to Azure
- Multi-cloud consolidation onto Azure
- Teams seeking feature parity with Cloud Run on Azure (scale-to-zero, managed TLS, revisions)

## Prerequisites

- `gcloud` CLI access to the source GCP project
- Azure CLI with `containerapp` extension installed
- Azure Container Registry (ACR) for storing container images

## Platform Comparison

| Feature | Cloud Run | Container Apps |
|---------|-----------|---------------|
| Scale to zero | ✅ | ✅ |
| Max instances | 1000 | 300 replicas |
| Max vCPU per instance | 8 | 4 (Consumption) |
| Max memory per instance | 32 GiB | 8 GiB (Consumption) |
| Request timeout | 60 min | 4 min (240s) |
| Revision-based traffic splitting | ✅ | ✅ |
| Managed TLS certificates | ✅ | ✅ |
| Custom domains | ✅ | ✅ |
| VPC connectivity | VPC connector | VNet integration |
| Event-driven | Eventarc / Pub/Sub | KEDA scalers / Dapr |
| Sidecar containers | ✅ (multi-container) | ✅ |
| Jobs (one-off / scheduled) | Cloud Run Jobs | Container Apps Jobs |

## Phase 1: Export Cloud Run Configuration

### List Services

```bash
# List all Cloud Run services
gcloud run services list --platform managed

# Export a specific service
gcloud run services describe SERVICE_NAME \
  --region REGION --format yaml > cloudrun-service.yaml
```

### Key Properties to Extract

```yaml
# From Cloud Run service YAML:
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"     # → minReplicas
        autoscaling.knative.dev/maxScale: "100"    # → maxReplicas
    spec:
      containerConcurrency: 80                     # → concurrentRequests
      containers:
      - image: gcr.io/PROJECT/IMAGE:TAG            # → re-push to ACR
        ports:
        - containerPort: 8080                      # → targetPort
        env:
        - name: VAR_NAME                           # → env mapping
          value: "value"
        resources:
          limits:
            cpu: "1"                               # → resources.cpu
            memory: "512Mi"                        # → resources.memory
  traffic:
  - revisionName: SERVICE-00001                    # → traffic weight
    percent: 100
```

## Phase 2: Assess Compatibility

Load [assessment.md](assessment.md) for the full compatibility matrix.

### Key Mapping: Cloud Run → Container Apps

| Cloud Run Concept | Container Apps Equivalent | Notes |
|------------------|--------------------------|-------|
| Service | Container App | Direct mapping |
| Revision | Revision | Same concept — immutable snapshot |
| Traffic splitting | Traffic weight per revision | Supports percentage-based routing |
| Min/max instances | minReplicas / maxReplicas | Same scaling model |
| Concurrency | HTTP scale rule `concurrentRequests` | Per-replica concurrency |
| Cloud Run Job | Container Apps Job | Manual, scheduled, or event-driven |
| Secrets (Secret Manager) | ACA Secrets / Key Vault refs | Use managed identity for Key Vault |
| VPC connector | VNet integration | Configure during environment setup |
| Eventarc triggers | KEDA scalers | Equivalent event-driven scaling |
| Service account | Managed identity | Azure equivalent for service auth |

### Potential Blockers

| Cloud Run Feature | ACA Limit | Mitigation |
|------------------|-----------|------------|
| >4 vCPU per instance | 4 vCPU max (Consumption) | Use Dedicated workload profiles or optimize |
| >8 GiB memory | 8 GiB max (Consumption) | Use Dedicated workload profiles or optimize |
| >240s request timeout | 240s max | Use async patterns or Container Apps Jobs |
| gRPC streaming >4 min | Ingress timeout limit | Use WebSocket or chunked responses |
| Cloud SQL proxy sidecar | No Cloud SQL | Use Azure SQL with managed identity |

## Phase 3: Migrate Container Images

```bash
# Pull from GCR/Artifact Registry
docker pull gcr.io/PROJECT/IMAGE:TAG

# Tag for ACR
docker tag gcr.io/PROJECT/IMAGE:TAG ACRNAME.azurecr.io/IMAGE:TAG

# Push to ACR
az acr login --name ACRNAME
docker push ACRNAME.azurecr.io/IMAGE:TAG
```

## Phase 4: Generate Bicep

Follow [code-migration.md](code-migration.md) for Bicep template generation.

### Cloud Run → Container App Bicep Mapping

```bicep
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName  // from Cloud Run service name
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    environmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080          // from spec.containers[].ports[].containerPort
        transport: 'auto'
      }
      registries: [{
        server: acr.properties.loginServer
        identity: 'system'
      }]
    }
    template: {
      containers: [{
        name: appName
        image: '${acr.properties.loginServer}/${appName}:latest'
        resources: {
          cpu: json('1.0')       // from resources.limits.cpu
          memory: '512Mi'        // from resources.limits.memory
        }
        env: [
          // Mapped from Cloud Run env vars
          { name: 'PORT', value: '8080' }
        ]
      }]
      scale: {
        minReplicas: 1           // from autoscaling.knative.dev/minScale
        maxReplicas: 100         // from autoscaling.knative.dev/maxScale
        rules: [{
          name: 'http-scale'
          http: {
            metadata: {
              concurrentRequests: '80'  // from containerConcurrency
            }
          }
        }]
      }
    }
  }
}
```

## Phase 5: Deploy and Validate

1. Deploy Bicep templates to Azure
2. Verify ingress endpoints return expected responses
3. Test traffic splitting if migrating multiple revisions
4. Migrate custom domains and DNS records
5. Redirect traffic from Cloud Run to Container Apps

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Image pull failure | ACR auth not configured | `az containerapp registry set --identity system` |
| 502/503 on endpoint | Port mismatch | Ensure `targetPort` matches app listen port |
| Slow cold starts | Scale-to-zero with heavy init | Set `minReplicas: 1` or optimize startup |
| Missing env vars | GCP-specific vars not mapped | Map all Cloud Run env vars to ACA env |
| Timeout errors | Request exceeds 240s | Use async patterns or Container Apps Jobs |

## References

- [Assessment Framework](assessment.md)
- [Code Migration Guide](code-migration.md)
- [ACA Constraints](global-rules.md)
