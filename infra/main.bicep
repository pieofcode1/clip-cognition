
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

var abbreviations = loadJsonContent('./abbreviations.json')
var resourceToken = toLower(uniqueString(subscription().id, abbreviations.environmentName, location))

var tags = {
  envName: abbreviations.environmentName
  repo: 'pieofcode1/clip-cognition'
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

module security 'app/security.bicep' = {
  name: 'security'
  scope: resourceGroup
  params: {
    databaseAccountName: database.outputs.accountName
    appPrincipalId: identity.outputs.principalId
    userPrincipalId: !empty(principalId) ? principalId : ''
    principalType: principalType
  }
}

// Outputs
output RESOURCE_GROUP_NAME string = resourceGroup.name
output USER_ASSIGNED_ID_NAME string = identity.outputs.name
output AZURE_TENANT_ID string = identity.outputs.tenantId

// AI outputs
output AZURE_OPENAI_ACCOUNT_ENDPOINT_0 string = openai.outputs.endpoint_0
output AZURE_OPENAI_ACCOUNT_ENDPOINT_1 string = openai.outputs.endpoint_1
output AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME string = openai.outputs.deployments[0].name
output AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME string = openai.outputs.deployments[1].name
output AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME string = openai.outputs.deployments[2].name
output AZURE_OPENAI_MAX_RAG_TOKENS string = openAiSettings.maxRagTokens
output AZURE_OPENAI_MAX_CONTEXT_TOKENS string = openAiSettings.maxContextTokens

// Database outputs
output AZURE_COSMOS_DB_ENDPOINT string = database.outputs.endpoint
output AZURE_COSMOS_DB_DATABASE_NAME string = database.outputs.database.name
output AZURE_COSMOS_DB_CHAT_CONTAINER_NAME string = database.outputs.containers[0].name
output AZURE_COSMOS_DB_CACHE_CONTAINER_NAME string = database.outputs.containers[1].name
output AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME string = database.outputs.containers[2].name
output AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME string = database.outputs.containers[3].name
