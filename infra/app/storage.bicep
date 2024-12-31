metadata description = 'Storage account resource.'

param accountName string
param location string = resourceGroup().location
param tags object = {}


module storageAccount '../core/storage/account.bicep' = {
  name: 'storageAccount'
  params: {
    accountName: accountName
    location: location
    tags: tags
  }
}

output name string = storageAccount.outputs.name
output endpoint string = storageAccount.outputs.endpoint
