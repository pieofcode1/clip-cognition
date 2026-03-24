metadata description = 'App config settings for the app service.'

@description('The name of the app service.')
param parentSiteName string

@secure()
param appSettings object = {}

resource site 'Microsoft.Web/sites@2024-04-01' existing = {
  name: parentSiteName
}

resource config 'Microsoft.Web/sites/config@2024-04-01' = {
  name: 'appsettings'
  parent: site
  kind: 'string'
  properties: appSettings
}
