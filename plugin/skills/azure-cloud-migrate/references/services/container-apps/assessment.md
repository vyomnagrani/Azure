# Container Apps Migration Assessment

Compatibility analysis framework for migrating containerized workloads to Azure Container Apps.

## Assessment Checklist

Evaluate each workload against these criteria before migration.

### Compute Compatibility

| Requirement | ACA Limit | Action if Exceeded |
|------------|-----------|-------------------|
| CPU per container | 4 vCPU max | Split workload or optimize |
| Memory per container | 8 GiB max | Split workload or reduce memory |
| Container image size | No hard limit (recommend <1 GiB) | Optimize image layers |
| Startup time | Health probe timeout (configurable) | Optimize startup, increase timeout |

### Storage Compatibility

| Source Pattern | ACA Support | Migration Path |
|---------------|-------------|----------------|
| EmptyDir (ephemeral) | ✅ Ephemeral storage | Direct mapping |
| Azure Files PVC | ✅ Azure Files mount | Configure volume mount |
| Local SSD / hostPath | ❌ Not supported | Move to Azure Files or external storage |
| Large persistent volumes | ⚠️ Limited | Use Azure Blob, SQL, or Cosmos DB |

### Networking Compatibility

| Source Pattern | ACA Support | Notes |
|---------------|-------------|-------|
| ClusterIP services | ✅ Internal ingress | Apps communicate via internal FQDN |
| LoadBalancer services | ✅ External ingress | Automatic HTTPS with managed certs |
| Ingress with TLS | ✅ Built-in TLS | Managed certs or bring your own |
| Network policies | ⚠️ Limited | VNet integration available |
| Service mesh (Istio) | ⚠️ Partial | Dapr provides similar capabilities |
| Host networking | ❌ Not supported | Redesign required |

### Feature Compatibility

| Source Feature | ACA Equivalent | Compatibility |
|---------------|---------------|---------------|
| Horizontal Pod Autoscaler | Scale rules (HTTP, KEDA) | ✅ Full |
| CronJobs | Container Apps Jobs | ✅ Full |
| ConfigMaps | Environment variables | ✅ Full |
| Secrets | ACA Secrets / Key Vault refs | ✅ Full |
| Init containers | Init containers | ✅ Full |
| Sidecar containers | Additional containers | ✅ Full |
| Liveness / readiness probes | Health probes | ✅ Full |
| DaemonSets | ❌ Not available | ⚠️ Redesign |
| StatefulSets | ❌ Not available | ⚠️ Use external state |
| Custom CRDs | ❌ Not available | ⚠️ Evaluate alternatives |
| Privileged containers | ❌ Not available | ❌ Blocker |

## Assessment Report Template

Generate `assessment.md` in the output directory:

```markdown
# Migration Assessment Report

## Source Environment
- **Platform**: [K8s on-prem / GKE / EKS / Cloud Run]
- **Namespace**: [namespace]
- **Workloads**: [count]

## Compatibility Summary

| Workload | Compatible | Blockers | Effort |
|----------|-----------|----------|--------|
| app-name | ✅ / ⚠️ / ❌ | List blockers | Low/Med/High |

## Blockers
[List any incompatible features that need redesign]

## Recommendations
[Migration order, dependency graph, risk mitigation]
```

## Scoring

- **✅ Compatible**: Direct migration possible
- **⚠️ Partial**: Migration possible with modifications
- **❌ Blocker**: Requires redesign or alternative service
