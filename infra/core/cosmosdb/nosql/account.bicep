metadata description = 'Creates Azure CosmosDB NoSQL Account.'

param name string
param location string = resourceGroup().location
param tags object = {}

@description('Enables serverless account. Defaults to false.')
param enableServerless bool = false

@description('Enables multiple write locations. Defaults to false.')
param disableKeyBasedAuth bool = false

@description('Enables Vector search for this account. Defaults to false.')
param enableNoSQLVectorSearch bool = false

@description('Enables NoSQL Full Text Search for this account. Defaults to false.')
param enableNoSQLFullTextSearch bool = false


module account '../account.bicep' = {
  name: 'account'
  params: {
    name: name
    location: location
    tags: tags
    kind: 'GlobalDocumentDB'
    enableServerless: enableServerless
    disableKeyBasedAuth: disableKeyBasedAuth
    enableNoSQLVectorSearch: enableNoSQLVectorSearch
    enableNoSQLFullTextSearch: enableNoSQLFullTextSearch
  }
}

output endpoint string = account.outputs.endpoint
output name string = account.outputs.name
