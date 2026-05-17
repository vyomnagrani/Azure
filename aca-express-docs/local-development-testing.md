# Local Development and Testing

This guide covers how to develop and test your containerized application locally before deploying to ACA Express.

## Local development workflow

ACA Express runs standard OCI containers, so your local development workflow is straightforward:

```
Code → Build container → Test locally → Push to registry → Deploy to ACA Express
```

No special SDK, CLI, or configuration format is required. If your app runs in a container locally, it runs on ACA Express.

## Building your container image

### Dockerfile basics

Your app needs a Dockerfile that produces a container image listening on an HTTP port:

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

Key requirements:
- Your app must listen on a single HTTP port (the same port you configure as `targetPort` in ACA Express)
- The container should start quickly (ideally < 5 seconds)
- Write logs to stdout/stderr (ACA Express captures these automatically)

### Build the image

```bash
docker build -t myapp:dev .
```

## Testing locally with Docker

### Run your container

```bash
docker run -d \
  -p 8080:3000 \
  -e DATABASE_URL="postgres://localhost:5432/mydb" \
  -e LOG_LEVEL="debug" \
  --name myapp \
  myapp:dev
```

### Verify it works

```bash
curl http://localhost:8080/health
curl http://localhost:8080/
```

### View logs

```bash
docker logs -f myapp
```

### Stop and clean up

```bash
docker stop myapp && docker rm myapp
```

## Environment parity

To match the ACA Express runtime locally, ensure:

| Aspect | Local | ACA Express |
|--------|-------|-------------|
| Port binding | `-p 8080:3000` | `targetPort: 3000` |
| Env vars | `-e KEY=value` | Container app env vars |
| Secrets | `-e SECRET=value` | Container app secrets |
| CPU/memory | Docker resource limits | CPU/memory allocation |

### Simulating resource limits

Match ACA Express resource constraints locally:

```bash
docker run -d \
  --cpus="0.5" \
  --memory="1g" \
  -p 8080:3000 \
  myapp:dev
```

## Testing with Docker Compose

For apps with local dependencies (databases, caches), use Docker Compose:

```yaml
# docker-compose.yml
services:
  app:
    build: .
    ports:
      - "8080:3000"
    environment:
      - DATABASE_URL=postgres://postgres:password@db:5432/mydb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

```bash
docker compose up --build
```

> **Note:** In ACA Express, your external dependencies (databases, caches) must be hosted separately as Azure services or accessible via public endpoints. ACA Express doesn't provide built-in managed databases or caches.

## Pushing to a container registry

Once your image works locally, push it to a registry that ACA Express can pull from.

### Azure Container Registry

```bash
# Log in to ACR
az acr login --name myregistry

# Tag for ACR
docker tag myapp:dev myregistry.azurecr.io/myapp:v1

# Push
docker push myregistry.azurecr.io/myapp:v1
```

### Docker Hub

```bash
docker tag myapp:dev mydockerhub/myapp:v1
docker push mydockerhub/myapp:v1
```

### GitHub Container Registry

```bash
docker tag myapp:dev ghcr.io/myorg/myapp:v1
docker push ghcr.io/myorg/myapp:v1
```

## Testing the deployment

After pushing, deploy to ACA Express and verify:

```bash
# Deploy
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --image myregistry.azurecr.io/myapp:v1

# Get the URL
az containerapp show \
  --name my-app \
  --resource-group my-express-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv

# Test
curl https://<your-app-url>/health
```

## Development tips

### Fast iteration cycle

For rapid development, use ACR Build to build images in the cloud without pulling/pushing locally:

```bash
az acr build \
  --registry myregistry \
  --image myapp:latest \
  .
```

Then update your app:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --image myregistry.azurecr.io/myapp:latest
```

### Logging best practices

Write structured JSON logs to stdout for easier querying in Log Analytics:

```javascript
// Node.js example
console.log(JSON.stringify({
  level: "info",
  message: "Request handled",
  method: "GET",
  path: "/api/users",
  duration_ms: 23,
  status: 200
}));
```

### Graceful shutdown

Handle SIGTERM for clean shutdowns during rolling updates:

```javascript
// Node.js example
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    process.exit(0);
  });
});
```

```python
# Python example
import signal
import sys

def handle_sigterm(signum, frame):
    print("SIGTERM received, shutting down")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)
```

## Next steps

- [Deploy to ACA Express](deploy-to-aca-express.md)
- [Configure your app](advanced-configuration.md)
- [Set up autoscaling](scaling.md)
