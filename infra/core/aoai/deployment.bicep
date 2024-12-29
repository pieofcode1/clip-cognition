metadata description = 'Creates Azure OpenAI deployments for the parent account.'

param name string

@description('Name of the parent Azure OpenAI Account.')
param parentAccountName string

@description('Name of the SKU for the deployment. Defaults to "Standard".')
param skuName string = 'Standard'

@description('Capacity of the SKU. Defaults to 100.')
param skuCapacity int = 100

@description('Name of the model to deploy.')
param modelName string

@description('Version of the model to deploy.')
param modelVersion string

@description('Format of the model to deploy.')
param modelFormat string


resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: parentAccountName
}

resource deployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: name
  parent: account
  sku: {
    name: skuName
    capacity: skuCapacity
  }
  properties: {
    model: {
      name: modelName
      version: modelVersion
      format: modelFormat
    }
  }
} 
