metadata description = 'Creates Azure OpenAI Account and deployments.'

param name string
param location string = resourceGroup().location
param tags object = {}

@allowed(['OpenAI', 'ComputerVision', 'TextAnalytics', 'CognitiveServices'])
@description('Sets the kind of Cognitive Services Account.')
param kind string = 'OpenAI'

@allowed([
  'S0'
])
@description('SKU for the account. Defaults to "S0".')
param sku string = 'S0'

@description('Enables access from public networks. Defaults to true.')
param enablePublicNetworkAccess bool = true

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: name
  location: location
  kind: kind
  tags: tags
  sku: {
    name: sku
  }
  properties: {
      customSubDomainName: name
      publicNetworkAccess: enablePublicNetworkAccess ? 'Enabled' : 'Disabled'
    }
 
}

output endpoint string = account.properties.endpoint
output name string = account.name
