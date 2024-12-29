metadata description = 'Creates an Azure CosmosDB NoSQL container.'

param name string
param tags object = {}

@description('The name of the CosmosDB account.')
param parentAccountName string

@description('The name of the CosmosDB database.')
param parentDatabaseName string

@description('Enables throughput settings at the resource level. Defaults to false.')
param setThroughput bool = false


@description('Enables autoscale settings at the resource level. Defaults to false.')
param autoscale bool = false

@description('The throughput of the container.')
param throughput int = 400

@description('The partition key path of the container.')
param partitionKeyPath string[] = [
  '/id'
]

@description('The indexing policy of the container.')
param indexingPolicy object = {}

@description('Optional vector embedding policy for the container.')
param vectorEmbeddingPolicy object = {}

@description('Optional full text policy for the container')
param fullTextPolicy object = {}


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

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' existing = {
  parent: account
  name: parentDatabaseName
}

resource container 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = {
  name: name
  parent: database
  tags: tags
  properties: {
    options: options
    resource: union(
      {
        id: name
        partitionKey: {
          paths: partitionKeyPath
          kind: 'MultiHash'
          version: 2
        }
      },
      !empty(indexingPolicy)
        ? {
            indexingPolicy: indexingPolicy
          }
        : {},
      !empty(fullTextPolicy)
        ? {
            fullTextPolicy: fullTextPolicy
          }
        : {},
      !empty(vectorEmbeddingPolicy)
        ? {
            vectorEmbeddingPolicy: vectorEmbeddingPolicy
          }
        : {}
    )
  }
}

output name string = container.name
