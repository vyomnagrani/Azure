# Deploy to Azure Container Apps Express

This guide walks you through deploying your first container app to ACA Express using the Azure Portal, Azure CLI, or Bicep.

## Prerequisites

- An Azure subscription with Contributor access
- A container image in a registry (Azure Container Registry, Docker Hub, GitHub Container Registry, etc.)
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) 2.70+ (for CLI deployments)

## Option 1: Deploy via Azure Portal

### Step 1: Create an Express environment

1. In the Azure Portal, search for **Container Apps** and select **Create**.
2. Under **Basics**, select your subscription and resource group.
3. For **Environment**, click **Create new**.
4. Set **Environment mode** to **Express**.
5. Give the environment a name (e.g., `my-express-env`).
6. Select your preferred region.
7. Click **Create**.

### Step 2: Configure your container

1. Under **Container**, provide:
   - **Image source**: Select your registry type (Azure Container Registry, Docker Hub, or other)
   - **Image**: Enter the full image reference (e.g., `myregistry.azurecr.io/myapp:latest`)
   - **Target port**: The port your app listens on (e.g., `8080`)
   - **CPU and Memory**: Choose a resource allocation (e.g., 0.5 vCPU / 1 GiB)

2. Optionally add environment variables or secrets.

### Step 3: Configure ingress

1. Under **Ingress**, ensure **External** is enabled (this is the default for Express).
2. The platform automatically provisions a public URL with TLS.

### Step 4: Review and create

1. Click **Review + Create**.
2. Verify your settings and click **Create**.
3. Deployment completes in approximately 30 seconds.
4. Once deployed, your app URL appears on the overview page.

---

## Option 2: Deploy via Azure CLI

### Step 1: Log in and set defaults

```bash
az login
az account set --subscription <your-subscription-id>
```

### Step 2: Create a resource group

```bash
az group create \
  --name my-express-rg \
  --location westus2
```

### Step 3: Create an Express environment

```bash
az containerapp env create \
  --name my-express-env \
  --resource-group my-express-rg \
  --location westus2 \
  --environment-type Express
```

### Step 4: Deploy your container app

```bash
az containerapp create \
  --name my-app \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image docker.io/library/nginx:latest \
  --target-port 80 \
  --ingress external \
  --cpu 0.5 \
  --memory 1.0Gi \
  --min-replicas 0 \
  --max-replicas 5
```

### Step 5: Get your app URL

```bash
az containerapp show \
  --name my-app \
  --resource-group my-express-rg \
  --query properties.configuration.ingress.fqdn \
  --output tsv
```

---

## Option 3: Deploy via Bicep

### Express environment and app template

```bicep
param location string = resourceGroup().location
param appName string = 'my-app'
param environmentName string = 'my-express-env'
param containerImage string = 'docker.io/library/nginx:latest'
param targetPort int = 80

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    environmentMode: 'Express'
  }
}

resource containerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'http'
      }
    }
    template: {
      containers: [
        {
          name: appName
          image: containerImage
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 5
      }
    }
  }
}

output appUrl string = containerApp.properties.configuration.ingress.fqdn
```

Deploy with:

```bash
az deployment group create \
  --resource-group my-express-rg \
  --template-file main.bicep
```

---

## Using a private container registry

If your image is in a private registry, provide credentials:

### Azure Container Registry (with managed identity)

```bash
az containerapp create \
  --name my-app \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image myregistry.azurecr.io/myapp:v1 \
  --registry-server myregistry.azurecr.io \
  --target-port 8080 \
  --ingress external
```

### Other registries (with username/password)

```bash
az containerapp create \
  --name my-app \
  --resource-group my-express-rg \
  --environment my-express-env \
  --image ghcr.io/myorg/myapp:latest \
  --registry-server ghcr.io \
  --registry-username <username> \
  --registry-password <password> \
  --target-port 8080 \
  --ingress external
```

---

## Updating your app

To deploy a new version of your container image:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --image myregistry.azurecr.io/myapp:v2
```

This triggers a rolling update:
1. New replicas are created with the updated image.
2. Health checks confirm the new replicas are ready.
3. Traffic shifts to the new replicas.
4. Old replicas are terminated.

The update typically completes in ~30 seconds with zero downtime.

---

## Rolling back

If a deployment introduces issues, roll back to a previous revision:

```bash
az containerapp revision list \
  --name my-app \
  --resource-group my-express-rg \
  --output table
```

Then activate a previous revision's image:

```bash
az containerapp update \
  --name my-app \
  --resource-group my-express-rg \
  --image myregistry.azurecr.io/myapp:v1
```

---

## CI/CD integration

You can trigger ACA Express deployments from any CI/CD system by calling the Azure CLI or ARM API.

### GitHub Actions example

```yaml
name: Deploy to ACA Express

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build and push image
        run: |
          az acr build \
            --registry myregistry \
            --image myapp:${{ github.sha }} .

      - name: Deploy to ACA Express
        run: |
          az containerapp update \
            --name my-app \
            --resource-group my-express-rg \
            --image myregistry.azurecr.io/myapp:${{ github.sha }}
```

---

## Next steps

- [Configure environment variables, secrets, and networking](advanced-configuration.md)
- [Set up autoscaling](scaling.md)
- [Monitor your app](operations-monitoring.md)
