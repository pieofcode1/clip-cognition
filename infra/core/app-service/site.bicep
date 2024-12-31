metadata description = 'Create the app service resource.'

param name string
param location string = resourceGroup().location
param tags object = {}

@description('The name of the app service plan.')
param appServicePlanName string

@description('The name of the app service plan resource group.')
@allowed([
  'python'
  'node'
  'java'
  'dotnet'
  'dotnetcore'
  'dotnet-isolated'
  'powershell'
  'custom'
])
param runtimeName string

@description('The version of the runtime.')
param runtimeVersion string

@description('The os settings for the app service.')
param kind string = 'app,linux'

@description('If the website should always be on. Default is true.')
param alwaysOn bool = true

@description('Allowed CORS origins for the app service.')
param allowedCorsOrigins string[] = []

@description('Whether to enable system assigned managed identity. Default is false.')
param enableSystemAssignedManagedIdentity bool = false

@description('User assigned managed identity ids.')
param userAssignedManagedIdentityIds string[] = []

var linuxFxVersion = '${runtimeName}|${runtimeVersion}'

resource plan 'Microsoft.Web/serverfarms@2024-04-01' existing = {
  name: appServicePlanName
}

resource site 'Microsoft.Web/sites@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: kind
  identity: {
    type: enableSystemAssignedManagedIdentity
              ? (!empty(userAssignedManagedIdentityIds) ? 'SystemAssigned, UserAssigned' : 'SystemAssigned')
              : (!empty(userAssignedManagedIdentityIds) ? 'UserAssigned' : null)
    userAssignedIdentities: !empty(userAssignedManagedIdentityIds) ? toObject(userAssignedManagedIdentityIds, uaId => uaId, uaId => {}) : null
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      alwaysOn: alwaysOn
      http20Enabled: true
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: union(['https://portal.azure.com', 'https://ms.portal.azure.com'], allowedCorsOrigins)
      }
      linuxFxVersion: linuxFxVersion
    }
  }
}

output endpoint string = 'https://${site.properties.defaultHostName}'
output name string = site.name
output managedIdentityPrincipalId string = enableSystemAssignedManagedIdentity ? site.identity.principalId : ''
