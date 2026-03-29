# Container Apps Networking Troubleshooting

Diagnose and resolve networking issues with Azure Container Apps.

## VNet Integration Issues

### Symptom: App cannot reach VNet resources

**Diagnose:**
```bash
# Check environment VNet configuration
az containerapp env show --name ENV -g RG \
  --query "properties.vnetConfiguration"

# Check infrastructure subnet
az containerapp env show --name ENV -g RG \
  --query "properties.infrastructureResourceGroup"
```

**Common causes:**
- Environment not configured with VNet integration
- Subnet too small (requires /23 or larger for Consumption, /27 for workload profiles)
- NSG rules blocking outbound traffic
- Missing service endpoints or private endpoints

**Fix:**
```bash
# Verify NSG allows required outbound traffic
az network nsg rule list --nsg-name NSG -g RG -o table

# Check subnet delegation
az network vnet subnet show -g RG --vnet-name VNET -n SUBNET \
  --query "delegations"
```

### Symptom: Apps cannot communicate with each other

**Diagnose:**
```bash
# Verify both apps are in the same environment
az containerapp show --name APP1 -g RG --query "properties.environmentId"
az containerapp show --name APP2 -g RG --query "properties.environmentId"

# Check internal ingress
az containerapp show --name APP2 -g RG \
  --query "properties.configuration.ingress.{external:external,fqdn:fqdn}"
```

**Fix:**
- Ensure both apps are in the **same Container Apps environment**
- Backend app must have ingress enabled (even if internal-only)
- Use the internal FQDN: `APP_NAME.internal.ENV_UNIQUE_ID.REGION.azurecontainerapps.io`

## Custom Domain Issues

### Symptom: Custom domain returns certificate error

**Diagnose:**
```bash
# List custom domain bindings
az containerapp hostname list --name APP -g RG -o table

# Check certificate status
az containerapp ssl show --certificate-name CERT -g RG \
  --environment ENV
```

**Common causes:**
- DNS CNAME not pointing to the ACA FQDN
- Certificate not yet issued (managed cert validation pending)
- Certificate expired

**Fix:**
```bash
# Add custom domain with managed certificate
az containerapp hostname bind --name APP -g RG \
  --hostname custom.example.com \
  --environment ENV \
  --validation-method CNAME

# Check DNS resolution
nslookup custom.example.com
```

## Session Affinity Issues

### Symptom: User sessions not sticky across requests

**Diagnose:**
```bash
az containerapp show --name APP -g RG \
  --query "properties.configuration.ingress.stickySessions"
```

**Fix:**
```bash
az containerapp ingress sticky-sessions set --name APP -g RG \
  --affinity sticky
```

## Ingress Timeout

### Symptom: Long-running requests fail with 504

**Diagnose:**
```bash
az containerapp show --name APP -g RG \
  --query "properties.configuration.ingress"
```

**Note:** Default ingress timeout is 240 seconds (configurable up to 3600s via `requestTimeoutDuration`). For operations exceeding the maximum:
- Use asynchronous request patterns (return 202 with status endpoint)
- Use Container Apps Jobs for long-running batch work
- Use WebSocket connections for streaming

## References

- [Container Apps VNet docs](https://learn.microsoft.com/azure/container-apps/vnet-custom)
- [Custom domains](https://learn.microsoft.com/azure/container-apps/custom-domains-managed-certificates)
