metadata description = 'Storage account resource.'

param accountName string
param location string = resourceGroup().location
param tags object = {}

@description('The name of the storage account container.')
param containerName string

module storageAccount '../core/storage/account.bicep' = {
  name: 'storageAccount'
  params: {
    accountName: accountName
    containerName: containerName
    location: location
    tags: tags
  }
}

output name string = storageAccount.outputs.name
output endpoint string = storageAccount.outputs.endpoint
output id string = storageAccount.outputs.id
output containerName string = storageAccount.outputs.containerName
