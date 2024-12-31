metadata description = 'Storage account resource.'

param accountName string
param location string = resourceGroup().location
param tags object = {}

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

output name string = storageAccount.name
output endpoint string = storageAccount.properties.primaryEndpoints.blob
