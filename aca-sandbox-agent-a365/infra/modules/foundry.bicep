targetScope = 'resourceGroup'

@description('Globally unique Foundry account name.')
@minLength(2)
@maxLength(64)
param name string

@description('Azure region that supports the selected model and deployment SKU.')
param location string = resourceGroup().location

@description('Tags applied to Foundry resources.')
param tags object = {}

@description('Model deployment name.')
param deploymentName string

@description('Foundry project name.')
param projectName string = 'inbox-agent'

@description('GlobalStandard quota capacity.')
@minValue(1)
param capacity int

resource account 'Microsoft.CognitiveServices/accounts@2026-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: name
    disableLocalAuth: true
    dynamicThrottlingEnabled: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
}

resource model 'Microsoft.CognitiveServices/accounts/deployments@2026-05-01' = {
  parent: account
  name: deploymentName
  sku: {
    name: 'GlobalStandard'
    capacity: capacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: 'gpt-4.1-mini'
      version: '2025-04-14'
    }
    raiPolicyName: 'Microsoft.Default'
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-05-01' = {
  parent: account
  name: projectName
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    displayName: 'ACA Sandbox Inbox Agent'
    description: 'Microsoft Agent 365 inbox sample hosted in an ACA Sandbox.'
  }
}

output id string = account.id
output name string = account.name
output endpoint string = 'https://${account.name}.services.ai.azure.com/api/projects/${project.name}'
output deploymentName string = model.name
