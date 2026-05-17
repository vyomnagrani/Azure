# Monitoring: Metrics and Logs

ACA Express provides built-in observability through metrics dashboards, real-time log streaming, and Log Analytics integration. No additional instrumentation is required for basic monitoring.

## Metrics dashboard

The metrics dashboard in the Azure Portal provides real-time and historical performance data.

### Accessing metrics

1. Navigate to your container app in the Azure Portal.
2. Select **Metrics** in the left menu.
3. Choose a metric from the dropdown.
4. Set the time range and granularity.

### Available metrics

| Metric | Description | Unit |
|--------|-------------|------|
| **CPU Usage** | CPU consumed by all replicas | Millicores |
| **Memory Usage** | Memory consumed by all replicas | Bytes |
| **Request Count** | Total HTTP requests received | Count |
| **Request Duration** | Average response time for requests | Milliseconds |
| **Replica Count** | Number of running replicas | Count |
| **Network In** | Bytes received | Bytes |
| **Network Out** | Bytes sent | Bytes |

### Creating metric charts

You can pin metric charts to an Azure Dashboard for quick access:

1. Configure the metric view (metric type, aggregation, time range).
2. Click **Pin to dashboard**.
3. Select or create a dashboard.

### Setting up alerts

Create alerts to be notified when metrics exceed thresholds:

1. In the **Metrics** view, click **New alert rule**.
2. Configure the condition (e.g., CPU > 80%, Request Duration > 2000ms).
3. Add an action group (email, SMS, webhook, etc.).
4. Set the alert name and severity.

---

## Real-time log streaming

Stream container logs in real time directly from the portal or CLI — useful for debugging startup issues or monitoring live behavior.

### Stream logs via Portal

1. Navigate to your container app.
2. Select **Log stream** in the left menu.
3. Logs appear in real time as your container writes to stdout/stderr.
4. Use the **pause** button to freeze the stream for inspection.
5. Use the **filter** field to search within the log output.

### Stream logs via CLI

```bash
az containerapp logs show \
  --name my-app \
  --resource-group my-express-rg \
  --type console \
  --follow
```

Options:
- `--follow` — Stream logs continuously (Ctrl+C to stop)
- `--tail 100` — Show the last 100 lines
- `--type console` — Application stdout/stderr logs
- `--type system` — Platform system logs (scaling events, health checks)

---

## Log Analytics (KQL queries)

For historical log analysis, ACA Express routes app logs to a Log Analytics workspace where you can query using KQL (Kusto Query Language).

### Accessing Log Analytics

1. Navigate to your container app.
2. Select **Logs** in the left menu.
3. The query editor opens with your app's Log Analytics workspace pre-selected.

### Common queries

#### Recent application logs

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "my-app"
| where TimeGenerated > ago(1h)
| project TimeGenerated, Log_s
| order by TimeGenerated desc
| take 100
```

#### Error logs

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "my-app"
| where Log_s contains "error" or Log_s contains "exception"
| where TimeGenerated > ago(24h)
| project TimeGenerated, Log_s
| order by TimeGenerated desc
```

#### Request patterns over time

```kql
ContainerAppConsoleLogs_CL
| where ContainerAppName_s == "my-app"
| where TimeGenerated > ago(6h)
| summarize count() by bin(TimeGenerated, 5m)
| render timechart
```

#### Scaling events

```kql
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "my-app"
| where Reason_s == "ScalingReplica"
| where TimeGenerated > ago(24h)
| project TimeGenerated, Reason_s, Log_s
| order by TimeGenerated desc
```

### Configuring log destination

When creating your Express environment, you can specify the Log Analytics workspace:

```bash
az containerapp env create \
  --name my-express-env \
  --resource-group my-express-rg \
  --location westus2 \
  --environment-type Express \
  --logs-workspace-id <workspace-id> \
  --logs-workspace-key <workspace-key>
```

---

## Application Insights integration (optional)

For deeper application performance monitoring (APM), connect your app to Application Insights:

1. Navigate to your container app.
2. Select **Application Insights** in the environment settings.
3. Provide the Application Insights connection string.
4. Or set it as an environment variable in your container:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --set-env-vars "APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=..."
```

This enables distributed tracing, dependency tracking, and custom telemetry if your app includes the App Insights SDK.

---

## Monitoring best practices

### Set up alerts for production apps

At minimum, configure alerts for:

- **CPU > 80%** — may indicate undersized containers or need for more replicas
- **Request Duration > threshold** — latency degradation
- **5xx error rate > 0** — application errors
- **Replica Count = Max** — scaling ceiling reached

### Use structured logging

Write logs as structured JSON for easier querying in Log Analytics:

```json
{"level": "info", "message": "Request processed", "duration_ms": 45, "status": 200}
```

Then query with:

```kql
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| extend parsed = parse_json(Log_s)
| where toint(parsed.status) >= 500
| project TimeGenerated, parsed.message, parsed.duration_ms, parsed.status
```

### Monitor scaling behavior

Track replica count over time to understand your app's load patterns and optimize min/max settings:

```kql
ContainerAppSystemLogs_CL
| where ContainerAppName_s == "my-app"
| where TimeGenerated > ago(7d)
| summarize max(ReplicaCount_d) by bin(TimeGenerated, 1h)
| render timechart
```

---

## Next steps

- [Debug with console access](shell-access-troubleshooting.md)
- [Set up autoscaling](scaling.md)
- [Configure your app](advanced-configuration.md)
