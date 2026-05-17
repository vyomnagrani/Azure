# Samples and Quickstarts

Ready-to-deploy examples for common scenarios on ACA Express.

## Quickstart: Node.js web API

A simple Express.js API that demonstrates environment variables, health checks, and structured logging.

### Application code

```javascript
// server.js
const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API endpoint
app.get('/api/hello', (req, res) => {
  const name = req.query.name || 'World';
  console.log(JSON.stringify({ level: 'info', message: 'Hello requested', name }));
  res.json({ message: `Hello, ${name}!` });
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log(JSON.stringify({ level: 'info', message: 'Shutting down' }));
  process.exit(0);
});

app.listen(port, () => {
  console.log(JSON.stringify({ level: 'info', message: `Server started on port ${port}` }));
});
```

### Dockerfile

```dockerfile
FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --production
COPY server.js .
EXPOSE 3000
CMD ["node", "server.js"]
```

### Deploy

```bash
az acr build --registry myregistry --image node-api:v1 .

az containerapp create \
  --name node-api \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/node-api:v1 \
  --target-port 3000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5
```

---

## Quickstart: Python Flask API

A Flask API with environment-based configuration and health monitoring.

### Application code

```python
# app.py
import os
import json
import signal
import sys
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify(status='healthy')

@app.route('/api/items', methods=['GET'])
def get_items():
    print(json.dumps({'level': 'info', 'message': 'Items requested'}), flush=True)
    return jsonify(items=[
        {'id': 1, 'name': 'Item A'},
        {'id': 2, 'name': 'Item B'},
    ])

def handle_sigterm(signum, frame):
    print(json.dumps({'level': 'info', 'message': 'SIGTERM received'}), flush=True)
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
```

### requirements.txt

```
flask==3.1.0
gunicorn==23.0.0
```

### Deploy

```bash
az acr build --registry myregistry --image flask-api:v1 .

az containerapp create \
  --name flask-api \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/flask-api:v1 \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5
```

---

## Quickstart: .NET 8 minimal API

A minimal .NET API demonstrating configuration and health checks.

### Application code

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/health", () => Results.Ok(new { status = "healthy" }));

app.MapGet("/api/time", () => Results.Ok(new {
    utc = DateTime.UtcNow,
    message = "Hello from ACA Express!"
}));

app.Run();
```

### Dockerfile

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY *.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENV ASPNETCORE_URLS=http://+:8080
ENTRYPOINT ["dotnet", "MyApi.dll"]
```

### Deploy

```bash
az acr build --registry myregistry --image dotnet-api:v1 .

az containerapp create \
  --name dotnet-api \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/dotnet-api:v1 \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 5
```

---

## Quickstart: Static site with Nginx

Serve a static website or SPA using Nginx.

### Dockerfile

```dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### nginx.conf

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Deploy

```bash
az acr build --registry myregistry --image my-site:v1 .

az containerapp create \
  --name my-site \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/my-site:v1 \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3
```

---

## Quickstart: App with authentication

Deploy an API that requires Microsoft Entra ID login.

### Step 1: Deploy the app

```bash
az containerapp create \
  --name secure-api \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/secure-api:v1 \
  --target-port 8080 \
  --ingress external
```

### Step 2: Enable authentication

```bash
az containerapp auth microsoft update \
  --name secure-api \
  --resource-group my-express-rg \
  --yes
```

Now all requests to your app require a valid Microsoft Entra ID token. Unauthenticated requests get redirected to login.

### Step 3: Access user identity in your app

When auth is enabled, user information is passed via headers:

```javascript
app.get('/api/me', (req, res) => {
  res.json({
    name: req.headers['x-ms-client-principal-name'],
    id: req.headers['x-ms-client-principal-id']
  });
});
```

---

## Quickstart: App with custom domain

### Step 1: Deploy

```bash
az containerapp create \
  --name my-app \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/myapp:v1 \
  --target-port 8080 \
  --ingress external
```

### Step 2: Get the default FQDN

```bash
az containerapp show \
  --name my-app \
  --resource-group my-express-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

### Step 3: Configure DNS

Add a CNAME record in your DNS provider:

```
api.example.com → my-app.happyfield-abc123.westus2.azurecontainerapps.io
```

### Step 4: Add the custom domain

```bash
az containerapp hostname add \
  --name my-app \
  --resource-group my-express-rg \
  --hostname api.example.com
```

TLS certificate is provisioned automatically.

---

## Next steps

- [Deploy to ACA Express](deploy-to-aca-express.md)
- [Configure your app](advanced-configuration.md)
- [Set up autoscaling](scaling.md)
- [Monitor with metrics and logs](operations-monitoring.md)
