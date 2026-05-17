# Scaling

ACA Express provides horizontal autoscaling powered by KEDA. Your app automatically scales between a minimum and maximum replica count based on traffic or custom metrics, including scaling to zero when idle.

## How scaling works

ACA Express monitors your app's load and adjusts the number of running replicas:

1. **Scale out**: When load increases (e.g., more concurrent HTTP requests), new replicas are created.
2. **Scale in**: When load decreases, excess replicas are removed.
3. **Scale to zero**: When no traffic arrives for the cooldown period, all replicas terminate — you pay nothing.
4. **Cold start**: When traffic arrives at a zero-replica app, a new replica starts (typically a few seconds).

```
Traffic arrives → Scale from 0 to 1 → More traffic → Scale to N → Traffic drops → Scale to 0
```

## Default scaling behavior

When you create an app without specifying scale rules:

| Setting | Default value |
|---------|--------------|
| Minimum replicas | 0 |
| Maximum replicas | 10 |
| Scale rule | HTTP concurrent requests (10 per replica) |

## Configure scaling via CLI

### Set min/max replicas

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --min-replicas 1 \
  --max-replicas 10
```

Set `--min-replicas 1` to avoid cold starts (your app always has at least one replica running).

### Add an HTTP scale rule

Scale based on concurrent HTTP requests per replica:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --scale-rule-name http-rule \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50
```

This means: when each replica is handling 50 concurrent requests, scale out another replica.

### Add a TCP scale rule

Scale based on concurrent TCP connections:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --scale-rule-name tcp-rule \
  --scale-rule-type tcp \
  --scale-rule-tcp-concurrency 100
```

### Add an Azure Queue scale rule

Scale based on message count in an Azure Storage Queue:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --scale-rule-name queue-rule \
  --scale-rule-type azure-queue \
  --scale-rule-metadata "queueName=my-queue" "queueLength=20" \
  --scale-rule-auth "connection=queue-connection-string"
```

### Add a custom KEDA scale rule

For advanced scenarios, use any KEDA-supported scaler:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --scale-rule-name custom-rule \
  --scale-rule-type <keda-scaler-type> \
  --scale-rule-metadata "key1=value1" "key2=value2"
```

## Configure scaling via Portal

1. Navigate to your container app in the Azure Portal.
2. Select **Scale** in the left menu.
3. Adjust the **Min replicas** and **Max replicas** sliders.
4. Under **Scale rules**, click **Add** to create new rules:
   - Choose rule type (HTTP, TCP, Custom)
   - Configure thresholds
5. Click **Save**.

The portal displays the current replica count and scaling activity in real time.

## Configure scaling via Bicep

```bicep
resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: 'my-app'
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
      }
    }
    template: {
      containers: [
        {
          name: 'my-app'
          image: 'myregistry.azurecr.io/myapp:latest'
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 10
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '30'
              }
            }
          }
        ]
      }
    }
  }
}
```

## Scaling best practices

### Avoid cold starts for production apps

Set `minReplicas: 1` for user-facing production services. This keeps at least one replica warm and eliminates the cold start delay.

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --min-replicas 1
```

### Tune concurrent request thresholds

The HTTP concurrency threshold determines when new replicas are added. Lower values scale out earlier (better latency, higher cost). Higher values pack more requests per replica (lower cost, higher latency under load).

| Workload type | Suggested concurrency |
|--------------|----------------------|
| Lightweight APIs (fast response) | 50–100 |
| Compute-heavy APIs | 10–30 |
| WebSocket connections | 5–20 |

### Use scale to zero for dev/test

For non-production workloads, keep `minReplicas: 0` to eliminate costs when the app isn't in use:

```bash
az containerapp update \
  --name my-dev-app \
  --resource-group my-express-rg \
  --min-replicas 0 \
  --max-replicas 3
```

### Design for stateless operation

Since replicas can be created and destroyed at any time, your app should:

- Store session state externally (Redis, database, etc.)
- Not rely on local file system persistence
- Handle graceful shutdown signals (SIGTERM)
- Start quickly (ideally < 5 seconds)

## Viewing current scale status

### CLI

```bash
az containerapp replica list \
  --name my-app \
  --resource-group my-express-rg \
  --output table
```

### Portal

The **Overview** page shows the current replica count. The **Metrics** page shows scaling activity over time (replica count graph).

## Next steps

- [Monitor with metrics and logs](operations-monitoring.md)
- [Debug with console access](shell-access-troubleshooting.md)
- [Configure your app](advanced-configuration.md)
