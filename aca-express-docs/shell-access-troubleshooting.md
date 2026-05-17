# Console Access and Troubleshooting

ACA Express provides interactive shell access to running containers directly from the Azure Portal or CLI. This lets you inspect file systems, check running processes, test network connectivity, and debug issues in real time.

## Console access via Portal

1. Navigate to your container app in the Azure Portal.
2. Select **Console** in the left menu.
3. Choose a startup command:
   - `/bin/bash` — Bash shell (if available in your image)
   - `/bin/sh` — POSIX shell (available in most images)
   - Custom command — specify any executable
4. Click **Connect**.
5. An interactive terminal opens in the browser.

### What you can do in the console

- Inspect configuration files and environment variables
- Check running processes (`ps aux`)
- Test outbound network connectivity (`curl`, `wget`, `nslookup`)
- View application files and logs on disk
- Run diagnostic commands specific to your application runtime

### Console limitations

- The console connects to a single running replica. If you have multiple replicas, you may need to identify which one to connect to.
- Console sessions are ephemeral — any changes you make inside the container are lost when the replica restarts.
- If your container image doesn't include a shell (e.g., distroless images), console access won't work.
- The session times out after a period of inactivity.

## Console access via CLI

```bash
az containerapp exec \
  --name my-app \
  --resource-group my-express-rg \
  --command "/bin/sh"
```

This opens an interactive shell session in your terminal.

---

## Troubleshooting common issues

### App won't start

**Symptoms:** Replica count stays at 0, or replicas crash immediately.

**Diagnosis steps:**

1. Check system logs for startup errors:

   ```bash
   az containerapp logs show \
     --name my-app \
     --resource-group my-express-rg \
     --type system \
     --tail 50
   ```

2. Check application logs for crash output:

   ```bash
   az containerapp logs show \
     --name my-app \
     --resource-group my-express-rg \
     --type console \
     --tail 50
   ```

3. Common causes:
   - **Wrong target port** — Ensure `--target-port` matches the port your app actually listens on.
   - **Missing environment variables** — App crashes because required config isn't set.
   - **Image pull failure** — Registry credentials are wrong or image doesn't exist.
   - **Insufficient memory** — App runs out of memory during startup. Try a larger memory allocation.
   - **Startup command error** — Command override has a typo or missing dependency.

**Fix:** Update the container configuration:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --target-port 3000 \
  --cpu 0.5 \
  --memory 1.0Gi
```

---

### App is slow or timing out

**Symptoms:** High response times, 504 gateway timeouts.

**Diagnosis steps:**

1. Check metrics for CPU and memory saturation:
   - Navigate to **Metrics** → select **CPU Usage** and **Memory Usage**.
   - If either is near 100%, your container is resource-constrained.

2. Check replica count:
   - If at max replicas, your scale ceiling may be too low.
   - If at 1 replica and CPU is high, increase max replicas.

3. Check request duration metrics for percentile spikes.

**Fixes:**

- Increase CPU/memory: `az containerapp update --cpu 1.0 --memory 2.0Gi`
- Increase max replicas: `az containerapp update --max-replicas 10`
- Lower the HTTP concurrency threshold to scale out earlier

---

### Image pull errors

**Symptoms:** App shows "ImagePullBackOff" or "ErrImagePull" in system logs.

**Diagnosis:**

```bash
az containerapp logs show \
  --name my-app \
  --resource-group my-express-rg \
  --type system \
  --tail 20
```

**Common causes and fixes:**

| Cause | Fix |
|-------|-----|
| Image tag doesn't exist | Verify the image:tag exists in your registry |
| Wrong registry server | Check `--registry-server` is correct |
| Auth failure (private registry) | Update registry credentials |
| ACR not accessible | Ensure managed identity has AcrPull role |

---

### Custom domain not working

**Symptoms:** Domain shows SSL error or doesn't resolve.

**Diagnosis steps:**

1. Verify DNS resolution:

   ```bash
   nslookup www.example.com
   ```

2. Check if it points to your app's FQDN.

3. In the Portal, check **Custom domains** for certificate provisioning status.

**Common causes:**

- DNS propagation hasn't completed (wait up to 48 hours for global propagation)
- CNAME record points to wrong target
- Domain validation not completed

---

### App returns 401/403 after enabling auth

**Symptoms:** All requests get unauthorized errors.

**Diagnosis:**

1. Verify the auth configuration in **Authentication** settings.
2. Check if the Entra ID app registration was created successfully.
3. Test with a browser to see if the login redirect works.

**Common causes:**

- App expects auth tokens in a specific format — check Easy Auth header configuration.
- Redirect URI mismatch — the automatically configured URI doesn't match your client.
- Token audience mismatch — your app validates a different audience than what's configured.

---

### Scaling issues

**Symptoms:** App doesn't scale out under load, or doesn't scale to zero.

**Diagnosis:**

1. Check current scale rules:

   ```bash
   az containerapp show \
     --name my-app \
     --resource-group my-express-rg \
     --query properties.template.scale
   ```

2. Check scaling events in system logs:

   ```bash
   az containerapp logs show \
     --name my-app \
     --resource-group my-express-rg \
     --type system \
     --tail 50
   ```

**Common causes:**

- No scale rules defined — add an HTTP or custom rule
- `minReplicas` set too high — app can't scale to zero
- `maxReplicas` set too low — app hits ceiling under load
- Health check failing — unhealthy replicas get restarted instead of staying available

---

## Health checks and readiness

ACA Express automatically health-checks your replicas during deployments. Ensure your app:

1. **Starts quickly** — respond to requests within the startup timeout.
2. **Responds on the target port** — the platform sends HTTP requests to verify readiness.
3. **Returns 2xx on the root path** — or configure a specific health endpoint.

If health checks fail, the deployment rolls back and the previous version remains active.

---

## Getting help

- **Azure Portal** — Check the **Notifications** panel for deployment error details.
- **Activity Log** — View ARM operations and their status codes in the resource group's Activity Log.
- **Azure Support** — File a support ticket for platform-level issues.

## Next steps

- [Monitor with metrics and logs](operations-monitoring.md)
- [Configure your app](advanced-configuration.md)
- [Set up autoscaling](scaling.md)
