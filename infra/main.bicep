
targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as a part of the resource names.')
param environment string

@minLength(1)
@allowed([
  'canadaeast'
  'northcentralus'
  'eastus'
  'eastus2'
  'westus3'
  'swedencentral'
])
@description('Primary location for all resources.')
param location string = 'northcentralus'

@description('Secondary location for all resources.')
param location2 string = 'eastus2'

@description('ID of the principal to assig to the database and application roles.')
param principalId string = ''

// Optional parameters
param openAiAccountName string = ''
param cosmosDbAccountName string = ''
param userAssignedIdentityName string = ''
param appServicePlanName string = ''
param appServiceWebAppName string = ''
param containerRegistryName string = ''
param containerInstanceName string = ''
param documentDbClusterName string = ''

@description('Administrator login for Azure DocumentDB cluster.')
param documentDbAdminLogin string = 'pieadmin'

@secure()
@description('Administrator password for Azure DocumentDB cluster. Must be provided via environment.')
#disable-next-line secure-parameter-default
param documentDbAdminPassword string = 'P${uniqueString(newGuid())}!2q${uniqueString(subscription().id, newGuid())}'

@description('Developer public IP to allow through DocumentDB firewall. Empty to skip.')
param developerIpAddress string = ''

@description('Whether to deploy the ACI container instance. Set to true after pushing the image to ACR.')
param deployContainerInstance bool = false

var abbreviations = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, abbreviations.environmentName, location))

var tags = {
  envName: abbreviations.environmentName
  repo: 'pieofcode1/clip-cognition'
}

// serviceName is used as value for the tag (azd-service-name) azd uses to identify deployment host
param serviceName string = 'cc-web'

var chatSettings = {
  maxContextWindow: '3'
  cacheSimilarityScore: '0.95'
  productMaxResults: '10'
}

var openAiSettings = {
  completionModelName: 'gpt-4o'
  completionDeploymentName: 'gpt-4o'
  embeddingModelName: 'text-embedding-3-large'
  embeddingDeploymentName: 'text-embedding-3-large'
  speechModelName: 'whisper'
  speechDeploymentName: 'whisper'
  maxRagTokens: '1500'
  maxContextTokens: '5000'
}


var productDataSourceUri = 'https://cosmosdbcosmicworks.blob.core.windows.net/cosmic-works-vectorized/product-text-3-large-1536-llm-gen-2.json'

var principalType = 'User'


resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-07-01' = {
  name: '${abbreviations.environmentName}-${resourceToken}-rg'
  location: location
  tags: tags
}

module identity 'app/identity.bicep' = {
  name: 'identity'
  scope: resourceGroup
  params: {
    identityName: !empty(userAssignedIdentityName) ? userAssignedIdentityName : '${abbreviations.userAssignedIdentity}-${resourceToken}'
    location: location
    tags: tags
  }
}

module openai 'app/aoai.bicep' = {
  name: 'openai'
  scope: resourceGroup
  params: {
    accountName: !empty(openAiAccountName) ? openAiAccountName : '${abbreviations.openAiAccount}-${resourceToken}'
    location: location
    location2: location2
    tags: tags
    completionModelName: openAiSettings.completionModelName
    completionDeploymentName: openAiSettings.completionDeploymentName
    embeddingModelName: openAiSettings.embeddingModelName
    embeddingDeploymentName: openAiSettings.embeddingDeploymentName
    speechModelName: openAiSettings.speechModelName
    speechDeploymentName: openAiSettings.speechDeploymentName
  }
}

module database 'app/cosmosdb.bicep' = {
  name: 'database'
  scope: resourceGroup
  params: {
    accountName: !empty(cosmosDbAccountName) ? cosmosDbAccountName : '${abbreviations.cosmosDbAccount}-${resourceToken}'
    location: location2
    tags: tags
  }
}

module documentdb 'app/documentdb.bicep' = {
  name: 'documentdb'
  scope: resourceGroup
  params: {
    clusterName: !empty(documentDbClusterName) ? documentDbClusterName : '${abbreviations.documentDbCluster}-${resourceToken}'
    location: location2
    tags: tags
    administratorLogin: documentDbAdminLogin
    administratorLoginPassword: documentDbAdminPassword
    appPrincipalId: identity.outputs.principalId
    userPrincipalId: !empty(principalId) ? principalId : ''
    principalType: principalType
    developerIpAddress: developerIpAddress
  }
}

module storageAccount 'app/storage.bicep' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    accountName: '${abbreviations.storageAccount}${resourceToken}'
    containerName: abbreviations.storageContainer
    developerIpAddress: developerIpAddress
    location: location
    tags: tags
  }
}

module web 'app/web.bicep' = {
  name: 'web'
  scope: resourceGroup
  params: {
    planName: !empty(appServicePlanName) ? appServicePlanName : '${abbreviations.appServicePlan}-${resourceToken}'
    appName: !empty(appServiceWebAppName) ? appServiceWebAppName : '${abbreviations.appServiceWebApp}-${resourceToken}'
    location: location
    tags: tags
    serviceTag: serviceName
    databaseAccountEndpoint: database.outputs.endpoint
    openaiEndpoint: openai.outputs.endpoint_0
    openaiEndpoint2: openai.outputs.endpoint_1
    cosmosdbSettings: {
      databaseName: database.outputs.database.name
      chatContainerName: database.outputs.containers[0].name
      cacheContainerName: database.outputs.containers[1].name
      videoAssetsContainerName: database.outputs.containers[2].name
      videoAssetFramesContainerName: database.outputs.containers[3].name
    }
    openaiSettings: {
      completionDeploymentEndpoint: openai.outputs.deployments[0].endpoint
      completionDeploymentName: openai.outputs.deployments[0].name
      embeddingDeploymentEndpoint: openai.outputs.deployments[1].endpoint
      embeddingDeploymentName: openai.outputs.deployments[1].name
      whisperDeploymentEndpoint: openai.outputs.deployments[2].endpoint
      whisperDeploymentName: openai.outputs.deployments[2].name
    }
    chatSettings: {
      maxContextWindow: chatSettings.maxContextWindow
      cacheSimilarityScore: chatSettings.cacheSimilarityScore
      productMaxResults: chatSettings.productMaxResults
    }
    userAssignedManagedIdentity: {
      resourceId: identity.outputs.resourceId
      clientId: identity.outputs.clientId
    }
  }
}

module container 'app/container.bicep' = {
  name: 'container'
  scope: resourceGroup
  params: {
    deployContainer: deployContainerInstance
    acrName: !empty(containerRegistryName) ? containerRegistryName : '${abbreviations.containerRegistry}${resourceToken}'
    containerName: !empty(containerInstanceName) ? containerInstanceName : '${abbreviations.containerInstance}-${resourceToken}'
    location: location
    tags: tags
    databaseAccountEndpoint: database.outputs.endpoint
    storageAccountEndpoint: storageAccount.outputs.endpoint
    storageContainerName: storageAccount.outputs.containerName
    openaiApiVersion: '2024-10-21'
    openaiSettings: {
      completionDeploymentEndpoint: openai.outputs.deployments[0].endpoint
      completionDeploymentName: openai.outputs.deployments[0].name
      embeddingDeploymentEndpoint: openai.outputs.deployments[1].endpoint
      embeddingDeploymentName: openai.outputs.deployments[1].name
      whisperDeploymentEndpoint: openai.outputs.deployments[2].endpoint
      whisperDeploymentName: openai.outputs.deployments[2].name
    }
    cosmosdbSettings: {
      databaseName: database.outputs.database.name
      videoAssetsContainerName: database.outputs.containers[2].name
      videoAssetFramesContainerName: database.outputs.containers[3].name
    }
    userAssignedManagedIdentity: {
      resourceId: identity.outputs.resourceId
      clientId: identity.outputs.clientId
    }
    tenantId: identity.outputs.tenantId
    documentDbConnectionString: documentdb.outputs.connectionString
    documentDbDatabaseName: documentdb.outputs.databaseName
  }
}

module security 'app/security.bicep' = {
  name: 'security'
  scope: resourceGroup
  params: {
    databaseAccountName: database.outputs.accountName
    storageAccountName: storageAccount.outputs.name
    appPrincipalId: identity.outputs.principalId
    userPrincipalId: !empty(principalId) ? principalId : ''
    principalType: principalType
  }
}

// Outputs
output AZURE_TENANT_ID string = identity.outputs.tenantId
output RESOURCE_GROUP_NAME string = resourceGroup.name
output USER_ASSIGNED_ID_NAME string = identity.outputs.name
output USER_ASSIGNED_ID_CLIENT_ID string = identity.outputs.clientId
output USER_ASSIGNED_ID_PRINCIPAL_ID string = identity.outputs.principalId
output USER_ASSIGNED_ID_RESOURCE_ID string = identity.outputs.resourceId

// Storage Account
output AZURE_STORAGE_ACCOUNT_ENDPOINT string = storageAccount.outputs.endpoint
output AZURE_STORAGE_CONTAINER_NAME string = storageAccount.outputs.containerName

// AI outputs
output AZURE_OPENAI_ACCOUNT_ENDPOINT_0 string = openai.outputs.endpoint_0
output AZURE_OPENAI_ACCOUNT_ENDPOINT_1 string = openai.outputs.endpoint_1
output AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME string = openai.outputs.deployments[0].name
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME string = openai.outputs.deployments[1].name
output AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME string = openai.outputs.deployments[2].name
output AZURE_OPENAI_COMPLETION_DEPLOYMENT_ENDPOINT string = openai.outputs.deployments[0].endpoint
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT string = openai.outputs.deployments[1].endpoint
output AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT string = openai.outputs.deployments[2].endpoint
output AZURE_OPENAI_MAX_RAG_TOKENS string = openAiSettings.maxRagTokens
output AZURE_OPENAI_MAX_CONTEXT_TOKENS string = openAiSettings.maxContextTokens
output AZURE_OPENAI_API_VERSION string = '2024-10-21'

// Database outputs
output AZURE_COSMOS_DB_ENDPOINT string = database.outputs.endpoint
output AZURE_COSMOS_DB_DATABASE_NAME string = database.outputs.database.name
output AZURE_COSMOS_DB_CHAT_CONTAINER_NAME string = database.outputs.containers[0].name
output AZURE_COSMOS_DB_CACHE_CONTAINER_NAME string = database.outputs.containers[1].name
output AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME string = database.outputs.containers[2].name
output AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME string = database.outputs.containers[3].name

// Chat outputs
output AZURE_CHAT_MAX_CONTEXT_WINDOW string = chatSettings.maxContextWindow
output AZURE_CHAT_CACHE_SIMILARITY_SCORE string = chatSettings.cacheSimilarityScore
output AZURE_CHAT_PRODUCT_MAX_RESULTS string = chatSettings.productMaxResults

// DocumentDB outputs
output MONGODB_CONNECTION_STRING string = documentdb.outputs.connectionString
output MONGODB_DB_NAME string = documentdb.outputs.databaseName
output AZURE_DOCUMENTDB_CLUSTER_NAME string = documentdb.outputs.clusterName

// Container outputs
output AZURE_CONTAINER_REGISTRY_NAME string = container.outputs.acrName
output AZURE_CONTAINER_REGISTRY_LOGIN_SERVER string = container.outputs.acrLoginServer
output API_ENDPOINT string = container.outputs.apiEndpoint
