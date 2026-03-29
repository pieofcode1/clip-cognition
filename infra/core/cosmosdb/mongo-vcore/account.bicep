metadata description = 'Creates an Azure DocumentDB (Cosmos DB for MongoDB vCore) cluster.'

param name string
param location string = resourceGroup().location
param tags object = {}

@description('Administrator login name.')
@secure()
param administratorLogin string

@description('Administrator login password.')
@secure()
param administratorLoginPassword string

@description('MongoDB server version.')
param serverVersion string = '7.0'

@description('The compute tier and size.')
@allowed(['Free', 'M25', 'M30', 'M40', 'M50', 'M60', 'M80'])
param sku string = 'M40'

@description('Storage size in GB per shard.')
param storageSizeGb int = 128

@description('Number of shards in the cluster.')
param shardCount int = 1

@description('Enable high availability. Defaults to false.')
param enableHa bool = false

resource cluster 'Microsoft.DocumentDB/mongoClusters@2024-07-01' = {
  name: name
  location: location
  tags: tags
  properties: {
    administrator: {
      userName: administratorLogin
      password: administratorLoginPassword
    }
    serverVersion: serverVersion
    compute: {
      tier: sku
    }
    storage: {
      sizeGb: storageSizeGb
    }
    sharding: {
      shardCount: shardCount
    }
    highAvailability: {
      targetMode: enableHa ? 'SameZone' : 'Disabled'
    }
  }
}

output name string = cluster.name
output connectionString string = cluster.properties.connectionString
output id string = cluster.id
