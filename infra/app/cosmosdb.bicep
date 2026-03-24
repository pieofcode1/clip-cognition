metadata description = 'Creates Azure CosmosDB NoSQL Account, Database and Containers.'

param accountName string
param location string = resourceGroup().location
param tags object = {}

var databaseName = 'clip-cognition-db'

var containers = [
  {
    name: 'chat' // Container for chat sessions and messages
    partitionKeyPaths: [
      '/tenantId'  // Partition on the tenant identifier, l1 of HPK
      '/userId'    // Partition on the user identifier, l2 of HPK
      '/sessionId' // Partition on the session identifier, l3 of HPK
    ]
    indexingPolicy: {
      automatic: true
      indexingMode: 'consistent'
      includedPaths: [
        {
          path: '/tenantId/?'
        }
        {
          path: '/userId/?'
        }
        {
          path: '/sessionId/?'
        }
        {
          path: '/timeStamp/?'
        }
      ]
      excludedPaths: [
        {
          path: '/*'
        }
      ]
    }
    vectorEmbeddingPolicy: {
      vectorEmbeddings: []
    }
    fullTextPolicy: {
      fullTextPaths: []
    }
  }
  {
    name: 'cache' // Container for cached messages
    partitionKeyPaths: [
      '/id' // Partition on cache identifier
    ]
    indexingPolicy: {
      automatic: true
      indexingMode: 'consistent'
      includedPaths: [
        {
          path: '/*'
        }
      ]
      excludedPaths: [
        {
          path: '/vectors/?'
        }
      ]
      vectorIndexes: [
        {
          path: '/vectors'
          type: 'diskANN'
        }
      ]
    }
    vectorEmbeddingPolicy: {
      vectorEmbeddings: [
        {
          path: '/vectors'
          dataType: 'float32'
          dimensions: 1536
          distanceFunction: 'cosine'
        }
      ]
    }
    fullTextPolicy: {
      fullTextPaths: []
    }
  }
  {
    name: 'video-assets' // Container for products
    partitionKeyPaths: [
      '/asset_name' // Partition for product data
    ]
    indexingPolicy: {
      automatic: true
      indexingMode: 'consistent'
      includedPaths: [
        {
          path: '/*'
        }
      ]
      excludedPaths: [
        {
          path: '/audio_summary_vector/*'
        }
        {
          path: '/video_summary_vector/*'
        }
      ]
      vectorIndexes: [
        {
          path: '/audio_summary_vector'
          type: 'quantizedFlat'
        }
        {
          path: '/video_summary_vector'
          type: 'diskANN'
        }
      ]
      fullTextIndexes: [
        {
          path: '/audio_summary'
        }
        {
          path: '/video_summary'
        }
      ]
    }
    vectorEmbeddingPolicy: {
      vectorEmbeddings: [
        {
          path: '/audio_summary_vector'
          dataType: 'float32'
          dimensions: 1536
          distanceFunction: 'cosine'
        }
        {
          path: '/video_summary_vector'
          dataType: 'float32'
          dimensions: 1536
          distanceFunction: 'cosine'
        }
      ]
    }
    fullTextPolicy: {
      defaultLanguage: 'en-US'
      fullTextPaths: [
        {
          path: '/audio_summary'
          language: 'en-US'
        }
        {
          path: '/video_summary'
          language: 'en-US'
        }
      ]
    }
  }
  {
    name: 'video-asset-frames' // Container for products
    partitionKeyPaths: [
      '/asset_name' // Partition for product data
    ]
    indexingPolicy: {
      automatic: true
      indexingMode: 'consistent'
      includedPaths: [
        {
          path: '/*'
        }
      ]
      excludedPaths: [
        {
          path: '/summary_vector/*'
        }
      ]
      vectorIndexes: [
        {
          path: '/summary_vector'
          type: 'diskANN'
        }
      ]
      fullTextIndexes: [
        {
          path: '/summary'
        }
      ]
    }
    vectorEmbeddingPolicy: {
      vectorEmbeddings: [
        {
          path: '/summary_vector'
          dataType: 'float32'
          dimensions: 1536
          distanceFunction: 'cosine'
        }
      ]
    }
    fullTextPolicy: {
      defaultLanguage: 'en-US'
      fullTextPaths: [
        {
          path: '/summary'
          language: 'en-US'
        }
      ]
    }
  }
]

module cosmosdbAccount '../core/cosmosdb/nosql/account.bicep' = {
  name: 'cosmosdb-account'
  params: {
    name: accountName
    location: location
    tags: tags
    enableServerless: true
    enableNoSQLVectorSearch: true
    enableNoSQLFullTextSearch: true
    disableKeyBasedAuth: true
  }
}

module cosmosdbDatabase '../core/cosmosdb/nosql/database.bicep' = {
  name: 'cosmosdb-database-${databaseName}'
  params: {
    name: databaseName
    parentAccountName: cosmosdbAccount.outputs.name
    tags: tags
    setThroughput: false
  }
}

module cosmosDbContainers '../core/cosmosdb/nosql/container.bicep' = [
  for (container, _) in containers: {
    name: 'cosmosdb-container-${container.name}'
    params: {
      name: container.name
      parentAccountName: cosmosdbAccount.outputs.name
      parentDatabaseName: cosmosdbDatabase.outputs.name
      tags: tags
      setThroughput: false
      partitionKeyPath: container.partitionKeyPaths
      indexingPolicy: container.indexingPolicy
      vectorEmbeddingPolicy: container.vectorEmbeddingPolicy
      fullTextPolicy: container.fullTextPolicy
    }
  }
]

output endpoint string = cosmosdbAccount.outputs.endpoint
output accountName string = cosmosdbAccount.outputs.name

output database object = {
  name: cosmosdbDatabase.outputs.name
}

output containers array = [
  for (container, index) in containers: {
    name: cosmosDbContainers[index].outputs.name
  }
]
