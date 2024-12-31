metadata description = 'Deploy an app service.'

param planName string
param appName string
param serviceTag string
param location string = resourceGroup().location
param tags object = {}

@description('The SKU of the app service plan.')
param sku string = 'B1'

@description('Database account endpoint.')
param databaseAccountEndpoint string


@description('OpenAI account endpoint.')
param openaiEndpoint string

@description('OpenAI account endpoint2.')
param openaiEndpoint2 string

type openaiOptions = {
  whisperDeploymentName: string
  whisperDeploymentEndpoint: string
  completionDeploymentName: string
  completionDeploymentEndpoint: string
  embeddingDeploymentName: string
  embeddingDeploymentEndpoint: string
}

@description('App settings configuration for OpenAI account options.')
param openaiSettings openaiOptions

type cosmosdbOptions = {
  databaseName: string
  chatContainerName: string
  cacheContainerName: string
  videoAssetsContainerName: string
  videoAssetFramesContainerName: string
}

@description('App settings configuration for CosmosDB account options.')
param cosmosdbSettings cosmosdbOptions

type chatOptions = {
  maxContextWindow: string
  cacheSimilarityScore: string
  productMaxResults: string
}

@description('App settings configuration for Chat options.')
param chatSettings chatOptions

type managedIdentity = {
  resourceId: string
  clientId: string
}

@description('App settings configuration for Managed Identity options.')
param userAssignedManagedIdentity managedIdentity

module appServicePlan '../core/app-service/plan.bicep' = {
  name: 'app-service-plan'
  params: {
    name: planName
    location: location
    tags: tags
    sku: sku
    kind: 'linux'
  }
}

module appServiceWebApp '../core/app-service/site.bicep' = {
  name: 'app-service-web-app'
  params: {
    name: appName
    location: location
    tags: union(tags, { 'azd-service-name': serviceTag })
    appServicePlanName: appServicePlan.outputs.name
    runtimeName: 'python'
    runtimeVersion: '3.11'
    kind: 'app,linux'
    enableSystemAssignedManagedIdentity: false
    userAssignedManagedIdentityIds: [
      userAssignedManagedIdentity.resourceId
    ]
  }
}

module appServiceWebAppConfig '../core/app-service/config.bicep' = {
  name: 'app-service-web-app-config'
  params: {
    parentSiteName: appServiceWebApp.outputs.name
    appSettings: {
      AZURE_OPENAI_ACCOUNT_ENDPOINT_0: openaiEndpoint 
      AZURE_OPENAI_ACCOUNT_ENDPOINT_1: openaiEndpoint2
      AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME: openaiSettings.whisperDeploymentName
      AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT: openaiSettings.whisperDeploymentEndpoint
      AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME: openaiSettings.completionDeploymentName
      AZURE_OPENAI_COMPLETION_DEPLOYMENT_ENDPOINT: openaiSettings.completionDeploymentEndpoint
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: openaiSettings.embeddingDeploymentName
      AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT: openaiSettings.embeddingDeploymentEndpoint
      AZURE_COSMOS_DB_ENDPOINT: databaseAccountEndpoint
      AZURE_COSMOS_DB_DATABASE_NAME: cosmosdbSettings.databaseName
      AZURE_COSMOS_DB_CHAT_CONTAINER_NAME: cosmosdbSettings.chatContainerName
      AZURE_COSMOS_DB_CACHE_CONTAINER_NAME: cosmosdbSettings.cacheContainerName
      AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME: cosmosdbSettings.videoAssetsContainerName
      AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME: cosmosdbSettings.videoAssetFramesContainerName
      AZURE_CHAT_MAX_CONTEXT_WINDOW: chatSettings.maxContextWindow
      AZURE_CHAT_CACHE_SIMILARITY_SCORE: chatSettings.cacheSimilarityScore
      AZURE_CHAT_PRODUCT_MAX_RESULTS: chatSettings.productMaxResults
    }
  }
}

output name string = appServiceWebApp.outputs.name
output endpoint string = appServiceWebApp.outputs.endpoint
