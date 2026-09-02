targetScope = 'resourceGroup'

@description('Globally unique, alphanumeric Azure Container Registry name.')
@minLength(5)
@maxLength(50)
param name string

@description('Azure region for the registry.')
param location string = resourceGroup().location

@description('Tags applied to the registry.')
param tags object = {}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    dataEndpointEnabled: false
    publicNetworkAccess: 'Enabled'
  }
}

output id string = registry.id
output name string = registry.name
output loginServer string = registry.properties.loginServer
