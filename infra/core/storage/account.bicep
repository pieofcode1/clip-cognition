metadata description = 'Storage account resource.'

param accountName string
param location string = resourceGroup().location
param tags object = {}

@description('The name of the storage account container.')
param containerName string = ''

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' existing = {
  name: 'default'
  parent: storageAccount
}

resource blobContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: containerName
  parent: blobService
  properties: {
    publicAccess: 'None'
  }
}

output name string = storageAccount.name
output endpoint string = storageAccount.properties.primaryEndpoints.blob
output id string = storageAccount.id
output containerName string = blobContainer.name
