targetScope = 'resourceGroup'

@description('ACA Sandbox Group name.')
@minLength(3)
@maxLength(64)
param name string

@description('User-assigned managed identity name.')
param identityName string

@description('Azure region that supports ACA Sandboxes.')
param location string = resourceGroup().location

@description('Tags applied to the sandbox group and identity.')
param tags object = {}

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: tags
}

// ACA Sandboxes is public preview; this API is documented by Microsoft Learn as of 2026-08-27.
#disable-next-line BCP081
resource sandboxGroup 'Microsoft.App/sandboxGroups@2026-02-01-preview' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identity.id}': {}
    }
  }
  properties: {
    defaultCpu: '1'
    defaultMemory: '2Gi'
    defaultDisk: '20Gi'
    maxSandboxCount: 3
    defaultTimeoutSeconds: 300
  }
}

output id string = sandboxGroup.id
output name string = sandboxGroup.name
output identityId string = identity.id
output identityClientId string = identity.properties.clientId
output identityPrincipalId string = identity.properties.principalId
