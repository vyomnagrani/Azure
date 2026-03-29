# Container Apps Dapr Troubleshooting

Diagnose and resolve Dapr integration issues with Azure Container Apps.

## Dapr Sidecar Not Starting

### Symptom: App starts but Dapr features don't work

**Diagnose:**
```bash
# Check if Dapr is enabled on the app
az containerapp show --name APP -g RG \
  --query "properties.configuration.dapr"

# Check system logs for Dapr sidecar errors
az containerapp logs show --name APP -g RG --type system --tail 50
```

**Common causes:**
- Dapr not enabled on the container app
- Invalid `appId` (must be unique within the environment)
- `appPort` not matching the port your app listens on

**Fix:**
```bash
# Enable Dapr
az containerapp dapr enable --name APP -g RG \
  --dapr-app-id my-app \
  --dapr-app-port 8080 \
  --dapr-app-protocol http
```

## Service Invocation Failures

### Symptom: Dapr service-to-service calls return errors

**Diagnose:**
```bash
# Verify target app has Dapr enabled with correct appId
az containerapp show --name TARGET_APP -g RG \
  --query "properties.configuration.dapr.{enabled:enabled,appId:appId,appPort:appPort}"

# Check both apps are in the same environment
az containerapp show --name APP1 -g RG --query "properties.environmentId"
az containerapp show --name APP2 -g RG --query "properties.environmentId"
```

**Common causes:**
- Target app does not have Dapr enabled
- Wrong `appId` in the invocation URL
- Apps in different Container Apps environments
- Target app `appPort` doesn't match its listen port

**Fix:**
- Ensure both apps have Dapr enabled in the **same environment**
- Use the correct invocation URL: `http://localhost:3500/v1.0/invoke/TARGET_APP_ID/method/ENDPOINT`
- Verify `appPort` matches the port the target app listens on

## State Store Binding Issues

### Symptom: Dapr state operations fail

**Diagnose:**
```bash
# List Dapr components in the environment
az containerapp env dapr-component list --name ENV -g RG -o table

# Show specific component config
az containerapp env dapr-component show --name ENV -g RG \
  --dapr-component-name statestore
```

**Common causes:**
- Component not created in the environment
- Wrong connection string or access key in component secrets
- Component scoped to different apps (scopes configuration)
- Missing managed identity permissions for the backing store

**Fix:**
```bash
# Create or update a state store component
az containerapp env dapr-component set --name ENV -g RG \
  --dapr-component-name statestore \
  --yaml dapr-statestore.yaml
```

Example component YAML (using Key Vault reference with managed identity):
```yaml
componentType: state.azure.cosmosdb
version: v1
metadata:
  - name: url
    value: "https://ACCOUNT.documents.azure.com:443/"
  - name: database
    value: "mydb"
  - name: collection
    value: "mystate"
  - name: masterKey
    secretRef: cosmos-key
secretStoreComponent: "azurekeyvault"
scopes:
  - my-app
```

> **Security**: Avoid storing secrets directly in component manifests. Use an [Azure Key Vault secret store component](https://learn.microsoft.com/azure/container-apps/dapr-component-connection) with managed identity.

## Pub/Sub Not Delivering Messages

### Symptom: Published messages not received by subscribers

**Diagnose:**
```bash
# Check pub/sub component
az containerapp env dapr-component show --name ENV -g RG \
  --dapr-component-name pubsub

# Check subscriber app logs
az containerapp logs show --name SUBSCRIBER_APP -g RG --tail 100

# Verify subscriber endpoint responds
curl -X POST http://localhost:APP_PORT/TOPIC_ROUTE \
  -H "Content-Type: application/json" \
  -d '{"data": "test"}'
```

**Common causes:**
- Subscriber app not returning subscription list at `/dapr/subscribe`
- Wrong topic name in publisher or subscriber
- Pub/sub component scopes exclude the subscriber app
- Subscriber endpoint returning non-200 status

**Fix:**
- Ensure subscriber app implements `GET /dapr/subscribe` returning topic subscriptions
- Verify topic names match exactly between publisher and subscriber
- Check component scopes include both publisher and subscriber app IDs

## Dapr Component Scoping

Components can be scoped to specific apps. If an app cannot access a component:

```bash
# Check component scopes
az containerapp env dapr-component show --name ENV -g RG \
  --dapr-component-name COMPONENT \
  --query "properties.scopes"
```

If scopes are set, only listed app IDs can use the component. Either add the app or remove scopes for shared access.

## References

- [Dapr on Container Apps](https://learn.microsoft.com/azure/container-apps/dapr-overview)
- [Dapr components](https://learn.microsoft.com/azure/container-apps/dapr-component-connection)
