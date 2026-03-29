# Container Apps Jobs

Azure Container Apps Jobs run containerized tasks that execute to completion. Unlike Container Apps (which run continuously), Jobs start, execute, and terminate.

## When to Use Jobs vs Container Apps

| Scenario | Use Jobs | Use Container Apps |
|----------|----------|-------------------|
| Batch data processing | ✅ | |
| Scheduled cleanup tasks | ✅ | |
| Event-driven one-off processing | ✅ | |
| Database migrations | ✅ | |
| Long-running APIs | | ✅ |
| Continuously running workers | | ✅ |
| Web applications | | ✅ |

## Trigger Types

### Manual Trigger

Jobs started on-demand via API or CLI:

```bicep
resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: '${resourcePrefix}-manual-job'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    environmentId: env.id
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 1800        // 30 min max execution time
      replicaRetryLimit: 1        // retry once on failure
      manualTriggerConfig: {
        parallelism: 1            // run 1 replica at a time
        replicaCompletionCount: 1 // 1 replica must complete
      }
      registries: [{
        server: acr.properties.loginServer
        identity: 'system'
      }]
    }
    template: {
      containers: [{
        name: 'job-runner'
        image: '${acr.properties.loginServer}/myjob:latest'
        resources: {
          cpu: json('0.5')
          memory: '1Gi'
        }
        env: [
          { name: 'TASK_TYPE', value: 'manual' }
        ]
      }]
    }
  }
}
```

**Start a manual job:**
```bash
az containerapp job start --name JOB -g RG
```

### Schedule Trigger

Jobs run on a cron schedule:

```bicep
resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: '${resourcePrefix}-scheduled-job'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    environmentId: env.id
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: 3600
      replicaRetryLimit: 1
      scheduleTriggerConfig: {
        cronExpression: '0 */6 * * *'  // every 6 hours
        parallelism: 1
        replicaCompletionCount: 1
      }
      registries: [{
        server: acr.properties.loginServer
        identity: 'system'
      }]
    }
    template: {
      containers: [{
        name: 'cleanup'
        image: '${acr.properties.loginServer}/cleanup:latest'
        resources: {
          cpu: json('0.25')
          memory: '0.5Gi'
        }
      }]
    }
  }
}
```

**Cron expression examples:**

| Expression | Schedule |
|-----------|----------|
| `0 0 * * *` | Daily at midnight |
| `0 */6 * * *` | Every 6 hours |
| `*/15 * * * *` | Every 15 minutes |
| `0 9 * * 1-5` | Weekdays at 9 AM |
| `0 0 1 * *` | First of each month |

### Event Trigger

Jobs triggered by external events (KEDA scalers):

```bicep
resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: '${resourcePrefix}-event-job'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    environmentId: env.id
    configuration: {
      triggerType: 'Event'
      replicaTimeout: 1800
      replicaRetryLimit: 2
      eventTriggerConfig: {
        parallelism: 5            // process up to 5 in parallel
        replicaCompletionCount: 5
        scale: {
          minExecutions: 0
          maxExecutions: 20
          pollingInterval: 30     // check every 30 seconds
          rules: [{
            name: 'queue-trigger'
            type: 'azure-queue'
            metadata: {
              queueName: 'work-items'
              queueLength: '1'
            }
            auth: [{
              secretRef: 'storage-connection'
              triggerParameter: 'connection'
            }]
          }]
        }
      }
      secrets: [{
        name: 'storage-connection'
        value: storageConnectionString
      }]
      registries: [{
        server: acr.properties.loginServer
        identity: 'system'
      }]
    }
    template: {
      containers: [{
        name: 'processor'
        image: '${acr.properties.loginServer}/processor:latest'
        resources: {
          cpu: json('1.0')
          memory: '2Gi'
        }
      }]
    }
  }
}
```

## Job Execution Management

```bash
# List job executions
az containerapp job execution list --name JOB -g RG -o table

# Show specific execution
az containerapp job execution show --name JOB -g RG --job-execution-name EXEC_NAME

# Start a manual job
az containerapp job start --name JOB -g RG

# View execution logs
az containerapp logs show --name JOB -g RG --type system --tail 50
```

## Resource Limits

| Resource | Limit |
|----------|-------|
| Max execution time | 24 hours (`replicaTimeout` in seconds) |
| Max parallel replicas | 100 (`parallelism`) |
| Max retry attempts | 3 (`replicaRetryLimit`) |
| CPU per container | 4 vCPU max (Consumption) |
| Memory per container | 8 GiB max (Consumption) |

## Deployment Verification

Unlike Container Apps (which verify via endpoint health), Jobs verify by checking execution history:

```bash
# Check job exists and is configured
az containerapp job show --name JOB -g RG \
  --query "{name:name,triggerType:properties.configuration.triggerType,provisioningState:properties.provisioningState}"

# For scheduled jobs, verify next execution
az containerapp job execution list --name JOB -g RG -o table

# For manual jobs, trigger a test execution
az containerapp job start --name JOB -g RG
az containerapp job execution list --name JOB -g RG -o table
```

## References

- [Container Apps Jobs docs](https://learn.microsoft.com/azure/container-apps/jobs)
- [KEDA scalers](https://keda.sh/docs/scalers/)
