# Container Apps KQL Queries

KQL queries for diagnosing Azure Container Apps issues using Log Analytics.

## Prerequisites

- Container Apps environment connected to a Log Analytics workspace
- Diagnostic settings enabled on the Container Apps environment

## Console Logs (Application Output)

```kql
// Recent application logs
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| where ContainerAppName_s == "APP_NAME"
| project TimeGenerated, Log_s, RevisionName_s, ReplicaName_s
| order by TimeGenerated desc
| take 50
```

```kql
// Application errors (stderr)
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| where ContainerAppName_s == "APP_NAME"
| where Log_s contains "error" or Log_s contains "exception" or Log_s contains "fatal"
| project TimeGenerated, Log_s, RevisionName_s, ReplicaName_s
| order by TimeGenerated desc
| take 50
```

## System Logs (Platform Events)

```kql
// Container lifecycle events (start, stop, crash)
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(1h)
| where ContainerAppName_s == "APP_NAME"
| project TimeGenerated, EventSource_s, Reason_s, Log_s, RevisionName_s
| order by TimeGenerated desc
| take 50
```

```kql
// Image pull failures
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(1h)
| where Reason_s == "ImagePullBackOff" or Reason_s == "ErrImagePull"
| project TimeGenerated, ContainerAppName_s, Log_s, RevisionName_s
| order by TimeGenerated desc
```

```kql
// Container crashes and restarts
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(4h)
| where Reason_s in ("BackOff", "CrashLoopBackOff", "OOMKilled")
| summarize CrashCount=count() by ContainerAppName_s, Reason_s, bin(TimeGenerated, 15m)
| order by TimeGenerated desc
```

## Scaling Events

```kql
// Replica scaling events
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(4h)
| where EventSource_s == "KEDA" or Log_s contains "scaling" or Log_s contains "replica"
| project TimeGenerated, ContainerAppName_s, Log_s, Reason_s
| order by TimeGenerated desc
| take 50
```

## Ingress and HTTP Logs

```kql
// HTTP request logs (if enabled)
ContainerAppConsoleLogs_CL
| where TimeGenerated > ago(1h)
| where ContainerAppName_s == "APP_NAME"
| where Log_s matches regex "\\d{3}"  // contains HTTP status codes
| project TimeGenerated, Log_s, RevisionName_s
| order by TimeGenerated desc
| take 50
```

## Revision Health

```kql
// Revision provisioning events
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(24h)
| where ContainerAppName_s == "APP_NAME"
| where EventSource_s == "ContainerApp" or EventSource_s == "Revision"
| project TimeGenerated, EventSource_s, Reason_s, Log_s, RevisionName_s
| order by TimeGenerated desc
```

## Cross-App Diagnostics

```kql
// All errors across all apps in the environment
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(1h)
| where Reason_s in ("BackOff", "CrashLoopBackOff", "Failed", "ErrImagePull", "OOMKilled")
| summarize ErrorCount=count() by ContainerAppName_s, Reason_s
| order by ErrorCount desc
```

```kql
// Apps with most restarts (last 24h)
ContainerAppSystemLogs_CL
| where TimeGenerated > ago(24h)
| where Reason_s in ("BackOff", "CrashLoopBackOff")
| summarize Restarts=count() by ContainerAppName_s
| order by Restarts desc
| take 10
```

## Tips

- Always include a time filter (`TimeGenerated > ago(Xh)`)
- Use `take 50` to limit large result sets
- `ContainerAppConsoleLogs_CL` = application stdout/stderr
- `ContainerAppSystemLogs_CL` = platform events (startup, scaling, health)
- Replace `APP_NAME` with the actual container app name

## References

- [Container Apps monitoring](https://learn.microsoft.com/azure/container-apps/log-monitoring)
- [Log Analytics queries](https://learn.microsoft.com/azure/container-apps/log-monitoring#log-analytics)
