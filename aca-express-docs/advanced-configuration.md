# Configuration

This guide covers how to configure your ACA Express app: environment variables, secrets, networking, custom domains, authentication, and resource allocation.

## Environment variables

Environment variables let you pass configuration values to your container at runtime.

### Set via CLI

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --set-env-vars "DATABASE_URL=postgres://..." "LOG_LEVEL=info" "APP_ENV=production"
```

### Set via Portal

1. Navigate to your container app in the Azure Portal.
2. Select **Containers** in the left menu.
3. Click **Edit and deploy**.
4. Under **Environment variables**, add your key-value pairs.
5. Click **Save**.

### Using secret references in environment variables

You can reference secrets in environment variables to avoid exposing sensitive values:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --set-env-vars "DB_PASSWORD=secretref:my-db-password"
```

---

## Secrets

Secrets store sensitive configuration values (passwords, API keys, connection strings) separately from environment variables.

### Create a secret

```bash
az containerapp secret set \
  --name my-app \
  --resource-group my-express-rg \
  --secrets "my-db-password=SuperSecret123" "api-key=abc123xyz"
```

### List secrets

```bash
az containerapp secret list \
  --name my-app \
  --resource-group my-express-rg \
  --output table
```

### Remove a secret

```bash
az containerapp secret remove \
  --name my-app \
  --resource-group my-express-rg \
  --secret-names my-db-password
```

> **Note:** Secrets are stored encrypted and never exposed in API responses. Updating a secret triggers a new revision deployment.

---

## Ingress and networking

ACA Express provides external HTTP ingress by default. You can configure additional networking options.

### Transport protocol

Set the transport protocol for your ingress:

```bash
az containerapp ingress update \
  --name my-app \
  --resource-group my-express-rg \
  --transport http2
```

Supported values: `http` (HTTP/1.1), `http2`

### Session affinity (sticky sessions)

Enable session affinity to route requests from the same client to the same replica:

```bash
az containerapp ingress sticky-sessions set \
  --name my-app \
  --resource-group my-express-rg \
  --affinity sticky
```

### IP restrictions

Restrict access to your app by IP address:

```bash
az containerapp ingress access-restriction set \
  --name my-app \
  --resource-group my-express-rg \
  --rule-name "allow-office" \
  --ip-address 203.0.113.0/24 \
  --action Allow
```

### CORS policy

Configure Cross-Origin Resource Sharing for browser clients:

```bash
az containerapp ingress cors update \
  --name my-app \
  --resource-group my-express-rg \
  --allowed-origins "https://mysite.com" "https://app.mysite.com" \
  --allowed-methods "GET" "POST" "PUT" \
  --allowed-headers "Content-Type" "Authorization" \
  --max-age 3600
```

---

## Custom domains

Bring your own domain with automatic TLS certificate management.

### Add a custom domain

1. Create a CNAME record pointing your domain to the app's auto-generated FQDN:

   ```
   www.example.com  CNAME  my-app.happyfield-abc123.westus2.azurecontainerapps.io
   ```

2. Add the custom domain:

   ```bash
   az containerapp hostname add \
     --name my-app \
     --resource-group my-express-rg \
     --hostname www.example.com
   ```

3. The platform automatically provisions and manages a TLS certificate.

### Via Portal

1. Navigate to your container app.
2. Select **Custom domains** in the left menu.
3. Click **Add custom domain**.
4. Follow the DNS validation steps.
5. The certificate is provisioned automatically.

---

## Authentication

ACA Express provides simplified one-click authentication that automatically sets up an Entra ID app registration.

### Enable Microsoft Entra ID auth

Via Portal:

1. Navigate to your container app.
2. Select **Authentication** in the left menu.
3. Click **Add identity provider**.
4. Select **Microsoft**.
5. The platform automatically:
   - Creates an Entra ID app registration
   - Configures redirect URIs
   - Sets up Easy Auth middleware
6. Choose whether to require authentication or allow anonymous access.

Via CLI:

```bash
az containerapp auth microsoft update \
  --name my-app \
  --resource-group my-express-rg \
  --yes
```

### Enable GitHub auth

1. In the Portal, select **Authentication** → **Add identity provider** → **GitHub**.
2. Provide your GitHub OAuth App credentials (Client ID and Client Secret).
3. Configure allowed redirect URLs.

### Auth behavior

When authentication is enabled:

- Unauthenticated requests receive a `401` response (or redirect to login, depending on configuration).
- Authenticated requests include user identity headers passed to your container.
- Token refresh is handled automatically by the platform.

---

## Resource allocation

Configure CPU and memory for your container:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --cpu 1.0 \
  --memory 2.0Gi
```

### Available CPU/memory combinations

| CPU (vCPU) | Memory (GiB) |
|-----------|-------------|
| 0.25 | 0.5 |
| 0.5 | 1.0 |
| 1.0 | 2.0 |
| 2.0 | 4.0 |
| 4.0 | 8.0 |

---

## Startup command override

Override the container's default entrypoint command:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --command "node" \
  --args "server.js" "--port" "8080"
```

---

## Managed identity

Assign a managed identity to your app for secure access to other Azure resources (Key Vault, Storage, databases) without storing credentials.

### Enable system-assigned identity

```bash
az containerapp identity assign \
  --name my-app \
  --resource-group my-express-rg \
  --system-assigned
```

### Use with Azure Key Vault

Once identity is assigned, grant it access to your Key Vault and reference secrets directly—no connection strings needed in your app configuration.

---

## Next steps

- [Set up autoscaling](scaling.md)
- [Monitor with metrics and logs](operations-monitoring.md)
- [Debug with console access](shell-access-troubleshooting.md)
