targetScope = 'resourceGroup'

@description('Suffix used for monitoring resource names.')
param name string

@description('Azure region for monitoring resources.')
param location string = resourceGroup().location

@description('Tags applied to monitoring resources.')
param tags object = {}

resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: take('log-${name}', 63)
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
    features: {
      enableLogAccessUsingOnlyResourcePermissions: true
    }
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: take('appi-${name}', 260)
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
    DisableLocalAuth: true
  }
}

output workspaceId string = workspace.id
output workspaceCustomerId string = workspace.properties.customerId
output appInsightsId string = appInsights.id
output appInsightsName string = appInsights.name
output connectionString string = appInsights.properties.ConnectionString
