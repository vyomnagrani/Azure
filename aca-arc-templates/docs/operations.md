# Operations and diagnostics

## Local operation

Run Uvicorn on loopback as shown in the README. Uvicorn emits basic access and
error logs to standard output. The health endpoints are:

- `/health/live`: the process is serving requests.
- `/health/ready`: the local service and deterministic repository are ready.

The initial implementation has no external dependency, so readiness does not
claim database, registry, Arc, or cluster health.

## Basic diagnostic sequence

1. Record the exact image tag, app name, revision, and timestamp.
2. Run the read-only smoke test against the approved URL.
3. Compare `/health/live` and `/health/ready`.
4. Inspect Container App revision/replica status through the current Azure
   Portal or current read-only CLI commands.
5. Inspect application standard output through the environment's approved log
   path.
6. Correlate ingress status, probe failures, and app access logs.

No log query syntax is hard-coded because the connected environment's
configured log destination is a platform decision. Do not assume a Log
Analytics workspace exists or create one from this sample.

## Useful application signals

- HTTP status and path from Uvicorn access logs
- Revision and replica health from the platform
- Probe failures and restart count
- Image pull and startup errors
- Inventory 404, 409, and 422 response rates

Do not log request authorization headers, credentials, kubeconfig content, or
private operator configuration. Current logs are basic diagnostics, not an
audit trail.

