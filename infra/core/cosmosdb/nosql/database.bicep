metadata description = 'Creates Azure CosmosDB NoSQL Database.'

param name string
param tags object = {}

@description('The name of the CosmosDB account.')
param parentAccountName string

@description('Enables throughput settings at the resource level. Defaults to false.')
param setThroughput bool = false

@description('Enables autoscale settings at the resource level. Defaults to false.')
param autoscale bool = false

@description('The throughput of the database.')
param throughput int = 400


var options = setThroughput 
              ? autoscale ? {
                autoscaleSettings: {
                  maxThroughput: throughput
                }
              } : {
                throughput: throughput
              }
              : {}


resource account 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: parentAccountName
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  name: name
  parent: account
  tags: tags
  properties: {
    options: options
    resource: {
      id: name
    }
  }
}

output name string = database.name
