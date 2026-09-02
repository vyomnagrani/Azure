targetScope = 'resourceGroup'

@description('Short azd environment name used in resource names and tags.')
@minLength(2)
@maxLength(32)
param environmentName string

@description('Azure region. It must support ACA Sandboxes and the selected model.')
param location string = resourceGroup().location

@description('Provision the optional pay-per-token Foundry model deployment.')
param enableFoundry bool = true

@description('Foundry model deployment name.')
param modelDeploymentName string = 'gpt-4.1-mini'

@description('GlobalStandard quota capacity assigned to the development deployment.')
@minValue(1)
param modelCapacity int = 10

@description('Optional signed-in user object ID to grant sandbox data-plane access at group scope.')
param sandboxOperatorPrincipalId string = ''

@description('Tags applied to every resource.')
param tags object = {
  'azd-env-name': environmentName
  environment: 'development'
  sample: 'aca-sandbox-agent-a365'
}

var token = take(uniqueString(subscription().id, resourceGroup().id, environmentName, location), 8)
var sandboxGroupName = take('sbg-${environmentName}-${token}', 64)
var identityName = take('id-${environmentName}-${token}', 128)
var registryName = take('acr${token}${uniqueString(resourceGroup().id)}', 50)
var monitoringName = take('${environmentName}-${token}', 40)
var appInsightsName = take('appi-${monitoringName}', 260)
var foundryName = take('aif-${environmentName}-${token}', 64)
var foundryProjectName = 'inbox-agent'

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    name: monitoringName
    location: location
    tags: tags
  }
}

module registry 'modules/registry.bicep' = {
  name: 'registry'
  params: {
    name: registryName
    location: location
    tags: tags
  }
}

module sandbox 'modules/sandbox-group.bicep' = {
  name: 'sandbox-group'
  params: {
    name: sandboxGroupName
    identityName: identityName
    location: location
    tags: tags
  }
}

module foundry 'modules/foundry.bicep' = if (enableFoundry) {
  name: 'foundry'
  params: {
    name: foundryName
    location: location
    tags: tags
    deploymentName: modelDeploymentName
    projectName: foundryProjectName
    capacity: modelCapacity
  }
}

resource registryResource 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: registryName
}

// ACA Sandboxes is public preview; this reference is used for optional operator RBAC.
#disable-next-line BCP081
resource sandboxGroupResource 'Microsoft.App/sandboxGroups@2026-02-01-preview' existing = {
  name: sandboxGroupName
}

resource foundryResource 'Microsoft.CognitiveServices/accounts@2026-05-01' existing = if (enableFoundry) {
  name: foundryName
}

resource foundryProjectResource 'Microsoft.CognitiveServices/accounts/projects@2026-05-01' existing = if (enableFoundry) {
  parent: foundryResource
  name: foundryProjectName
}

resource appInsightsResource 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

var acrPullRoleId = '7f951dda-4ed3-4680-a7ca-43fe172d538d'
resource identityAcrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(registryResource.id, identityName, acrPullRoleId)
  scope: registryResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', acrPullRoleId)
    principalId: sandbox.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    registry
  ]
}

var monitoringMetricsPublisherRoleId = '3913510d-42f4-4e42-8a64-420c390055eb'
resource identityMonitoringPublisher 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appInsightsResource.id, identityName, monitoringMetricsPublisherRoleId)
  scope: appInsightsResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', monitoringMetricsPublisherRoleId)
    principalId: sandbox.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    monitoring
  ]
}

var sandboxDataOwnerRoleId = 'c24cf47c-5077-412d-a19c-45202126392c'
resource operatorSandboxDataOwner 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(sandboxOperatorPrincipalId)) {
  name: guid(sandboxGroupResource.id, sandboxOperatorPrincipalId, sandboxDataOwnerRoleId)
  scope: sandboxGroupResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', sandboxDataOwnerRoleId)
    principalId: sandboxOperatorPrincipalId
    principalType: 'User'
  }
  dependsOn: [
    sandbox
  ]
}

var foundryUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'
resource identityFoundryUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (enableFoundry) {
  name: guid(foundryProjectResource.id, identityName, foundryUserRoleId)
  scope: foundryProjectResource
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', foundryUserRoleId)
    principalId: sandbox.outputs.identityPrincipalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    foundry
  ]
}

output AZURE_RESOURCE_GROUP string = resourceGroup().name
output AZURE_LOCATION string = location
output AZURE_CONTAINER_REGISTRY_NAME string = registry.outputs.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = registry.outputs.loginServer
output AZURE_LOG_ANALYTICS_WORKSPACE_ID string = monitoring.outputs.workspaceId
output APPLICATIONINSIGHTS_CONNECTION_STRING string = monitoring.outputs.connectionString
output APPLICATIONINSIGHTS_AUTHENTICATION_STRING string = 'Authorization=AAD;ClientId=${sandbox.outputs.identityClientId}'
output ACA_SANDBOX_GROUP string = sandbox.outputs.name
output ACA_SANDBOX_GROUP_ID string = sandbox.outputs.id
output ACA_SANDBOX_REGION string = location
output AZURE_CLIENT_ID string = sandbox.outputs.identityClientId
output AZURE_MANAGED_IDENTITY_RESOURCE_ID string = sandbox.outputs.identityId
output FOUNDRY_ENDPOINT string = enableFoundry ? foundry!.outputs.endpoint : ''
output FOUNDRY_MODEL_DEPLOYMENT string = enableFoundry ? foundry!.outputs.deploymentName : ''
