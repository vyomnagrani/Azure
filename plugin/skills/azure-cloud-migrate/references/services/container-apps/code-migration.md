# Container Apps Code Migration

Bicep templates, output structure, and deployment guidance for Container Apps migrations.

## Output Structure

All migration artifacts go to `<source-folder>-azure/` at workspace root:

```
<source-folder>-azure/
├── assessment.md          # Assessment report
├── code-migration.md      # Migration notes and decisions
├── migration-status.md    # Progress tracking
└── infra/
    ├── main.bicep         # Main deployment template
    ├── main.parameters.json
    ├── modules/
    │   ├── environment.bicep   # Container Apps environment
    │   ├── registry.bicep      # Container Registry
    │   └── apps/
    │       ├── app-name.bicep  # One per migrated workload
    │       └── ...
    └── monitoring/
        ├── log-analytics.bicep
        └── app-insights.bicep
```

## Bicep Template Patterns

### Container Apps Environment

```bicep
resource env 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: envName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}
```

### Container App (from Deployment)

```bicep
resource app 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    environmentId: env.id
    configuration: {
      ingress: {
        external: true    // false for internal services
        targetPort: 8080  // from K8s containerPort / Cloud Run PORT
        transport: 'auto'
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: appName
          image: '${acr.properties.loginServer}/${appName}:latest'
          resources: {
            cpu: json('0.5')   // from K8s resources.requests.cpu
            memory: '1Gi'      // from K8s resources.requests.memory
          }
          env: [
            // Mapped from ConfigMaps / env vars
            { name: 'PORT', value: '8080' }
          ]
        }
      ]
      scale: {
        minReplicas: 1   // from K8s replicas / Cloud Run min-instances
        maxReplicas: 10  // from HPA maxReplicas / Cloud Run max-instances
        rules: [
          {
            name: 'http-scale'
            http: {
              metadata: {
                concurrentRequests: '100'
              }
            }
          }
        ]
      }
    }
  }
}
```

### Container Apps Job (from CronJob)

```bicep
resource job 'Microsoft.App/jobs@2024-03-01' = {
  name: jobName
  location: location
  properties: {
    environmentId: env.id
    configuration: {
      triggerType: 'Schedule'
      replicaTimeout: 1800
      replicaRetryLimit: 1
      scheduleTriggerConfig: {
        cronExpression: '0 */6 * * *'  // from K8s schedule
      }
      registries: [
        {
          server: acr.properties.loginServer
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: jobName
          image: '${acr.properties.loginServer}/${jobName}:latest'
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
    }
  }
}
```

## Deployment

After generating Bicep templates:

1. **Validate**: `az bicep build --file infra/main.bicep`
2. **Preview**: `az deployment group what-if -g RG --template-file infra/main.bicep`
3. **Deploy**: `az deployment group create -g RG --template-file infra/main.bicep`
4. **Verify**: Check endpoints and logs

Or hand off to `azure-prepare` → `azure-validate` → `azure-deploy` for the full deployment workflow.
