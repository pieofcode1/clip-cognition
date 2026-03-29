metadata description = 'Deploy the API as an Azure Container Instance with ACR.'

param acrName string
param containerName string
param location string = resourceGroup().location
param tags object = {}

@description('Container image tag.')
param imageTag string = 'latest'

@description('Whether to deploy the container instance. Set to false for initial infra provisioning before an image is pushed.')
param deployContainer bool = false

@description('CPU cores for the container.')
param cpuCores int = 1

@description('Memory in GB for the container.')
param memoryInGb int = 2

type openaiOptions = {
  whisperDeploymentName: string
  whisperDeploymentEndpoint: string
  completionDeploymentName: string
  completionDeploymentEndpoint: string
  embeddingDeploymentName: string
  embeddingDeploymentEndpoint: string
}

@description('OpenAI deployment settings.')
param openaiSettings openaiOptions

type cosmosdbOptions = {
  databaseName: string
  videoAssetsContainerName: string
  videoAssetFramesContainerName: string
}

@description('CosmosDB settings.')
param cosmosdbSettings cosmosdbOptions

@description('Database account endpoint.')
param databaseAccountEndpoint string

@description('Storage account endpoint.')
param storageAccountEndpoint string

@description('Storage container name.')
param storageContainerName string

@description('OpenAI API version.')
param openaiApiVersion string

type managedIdentity = {
  resourceId: string
  clientId: string
}

@description('User-assigned managed identity.')
param userAssignedManagedIdentity managedIdentity

@description('Azure Tenant ID.')
param tenantId string

@description('Azure DocumentDB connection string.')
@secure()
param documentDbConnectionString string = ''

@description('Azure DocumentDB database name.')
param documentDbDatabaseName string = ''

// ACR
module acr '../core/container/registry.bicep' = {
  name: 'container-registry'
  params: {
    name: acrName
    location: location
    tags: tags
  }
}

// ACI — only deploy when an image exists in ACR
module aci '../core/container/instance.bicep' = if (deployContainer) {
  name: 'container-instance'
  params: {
    name: containerName
    location: location
    tags: union(tags, { 'azd-service-name': 'cc-api' })
    containerImage: '${acr.outputs.loginServer}/clip-cognition-api:${imageTag}'
    cpuCores: cpuCores
    memoryInGb: memoryInGb
    acrLoginServer: acr.outputs.loginServer
    acrUsername: acr.outputs.adminUsername
    acrPassword: acr.outputs.adminPassword
    userAssignedIdentityId: userAssignedManagedIdentity.resourceId
    environmentVariables: [
      { name: 'AZURE_TENANT_ID', value: tenantId }
      { name: 'USER_ASSIGNED_ID_CLIENT_ID', value: userAssignedManagedIdentity.clientId }
      { name: 'AZURE_OPENAI_API_VERSION', value: openaiApiVersion }
      { name: 'AZURE_OPENAI_COMPLETION_DEPLOYMENT_ENDPOINT', value: openaiSettings.completionDeploymentEndpoint }
      { name: 'AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME', value: openaiSettings.completionDeploymentName }
      { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT', value: openaiSettings.embeddingDeploymentEndpoint }
      { name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME', value: openaiSettings.embeddingDeploymentName }
      { name: 'AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT', value: openaiSettings.whisperDeploymentEndpoint }
      { name: 'AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME', value: openaiSettings.whisperDeploymentName }
      { name: 'AZURE_COSMOS_DB_ENDPOINT', value: databaseAccountEndpoint }
      { name: 'AZURE_COSMOS_DB_DATABASE_NAME', value: cosmosdbSettings.databaseName }
      { name: 'AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME', value: cosmosdbSettings.videoAssetsContainerName }
      { name: 'AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME', value: cosmosdbSettings.videoAssetFramesContainerName }
      { name: 'AZURE_STORAGE_ACCOUNT_ENDPOINT', value: storageAccountEndpoint }
      { name: 'AZURE_STORAGE_CONTAINER_NAME', value: storageContainerName }
      { name: 'MONGODB_CONNECTION_STRING', secureValue: documentDbConnectionString }
      { name: 'MONGODB_DB_NAME', value: documentDbDatabaseName }
    ]
  }
}

output acrName string = acr.outputs.name
output acrLoginServer string = acr.outputs.loginServer
output containerName string = deployContainer ? aci.?outputs.?name ?? '' : ''
output apiEndpoint string = deployContainer ? 'http://${aci.?outputs.?ipAddress ?? ''}:8000' : ''
