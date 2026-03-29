# Container Apps Scaling Troubleshooting

Diagnose and resolve scaling issues with Azure Container Apps.

## Scale-to-Zero Wake-Up Failures

### Symptom: App returns errors on first request after scale-to-zero

**Diagnose:**
```bash
# Check current replica count
az containerapp replica list --name APP -g RG --revision REV -o table

# Check scaling configuration
az containerapp show --name APP -g RG \
  --query "properties.template.scale"

# Check system logs for startup issues
az containerapp logs show --name APP -g RG --type system --tail 50
```

**Common causes:**
- App takes too long to start (exceeds health probe timeout)
- Missing or misconfigured readiness probe
- Heavy initialization (loading models, warming caches)

**Fix:**
- Increase health probe `initialDelaySeconds`
- Set `minReplicas: 1` for latency-sensitive workloads
- Optimize application startup time
- Use startup probes for slow-starting containers

## KEDA Scaler Not Triggering

### Symptom: App does not scale despite queue messages or events

**Diagnose:**
```bash
# Check scale rules
az containerapp show --name APP -g RG \
  --query "properties.template.scale.rules"

# Check if secrets are configured for scaler auth
az containerapp show --name APP -g RG \
  --query "properties.configuration.secrets[].name"

# Check system logs for scaler errors
az containerapp logs show --name APP -g RG --type system --tail 100
```

**Common causes:**
- Missing or incorrect connection string in scaler auth
- Secret name mismatch between scale rule and secrets config
- Wrong queue name or metadata values
- KEDA scaler type not supported on Container Apps

**Supported KEDA scalers include:**
- Azure Queue Storage
- Azure Service Bus
- Azure Event Hubs
- Azure Cosmos DB (change feed)
- HTTP (concurrent requests)
- TCP (concurrent connections)
- Custom (any KEDA-supported scaler)

**Fix:**
```bash
# Verify queue-based scaling
az containerapp show --name APP -g RG \
  --query "properties.template.scale.rules[?name=='queue-scaling']"

# Update scale rule with correct auth
az containerapp update --name APP -g RG \
  --scale-rule-name queue-scaling \
  --scale-rule-type azure-queue \
  --scale-rule-metadata "queueName=myqueue" "queueLength=5" \
  --scale-rule-auth "connection=queue-connection-secret"
```

## Replica Limit Reached

### Symptom: App stops scaling despite load increase

**Diagnose:**
```bash
# Check max replicas setting
az containerapp show --name APP -g RG \
  --query "properties.template.scale.maxReplicas"

# Check current replica count
az containerapp replica list --name APP -g RG --revision REV -o table

# Check environment-level quotas
az containerapp env show --name ENV -g RG \
  --query "properties"
```

**Fix:**
```bash
# Increase max replicas (up to 300)
az containerapp update --name APP -g RG --max-replicas 50
```

## HTTP Scaling Not Responsive

### Symptom: Slow scale-out under HTTP load

**Diagnose:**
```bash
az containerapp show --name APP -g RG \
  --query "properties.template.scale.rules[?http!=null]"
```

**Common causes:**
- `concurrentRequests` threshold set too high
- No HTTP scale rule configured (defaults may not match workload)

**Fix:**
```bash
# Configure appropriate HTTP scaling threshold
az containerapp update --name APP -g RG \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-metadata "concurrentRequests=50"
```

## Scaling Best Practices

| Workload | minReplicas | maxReplicas | Scale Rule |
|----------|------------|-------------|------------|
| Production API | 1-2 | 10-20 | HTTP (50-100 concurrent) |
| Dev/Test API | 0 | 3-5 | HTTP (100 concurrent) |
| Queue Worker | 0 | 30+ | Azure Queue / Service Bus |
| Event Processor | 0 | 20+ | Event Hub / Cosmos DB |

## References

- [Container Apps scaling docs](https://learn.microsoft.com/azure/container-apps/scale-app)
- [KEDA scalers](https://keda.sh/docs/scalers/)
