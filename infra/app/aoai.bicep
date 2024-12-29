metadata description = 'Creates Azure OpenAI Account and deployments.'

param accountName string
param location string = resourceGroup().location
param location2 string
param tags object = {}

param completionModelName string
param completionDeploymentName string
param embeddingModelName string
param embeddingDeploymentName string
param speechModelName string
param speechDeploymentName string

var deployments = [
  {
    name: completionDeploymentName
    modelName: completionModelName
    location: 'primary'
    skuName: 'GlobalStandard'
    modelVersion: '2024-11-20'
    skuCapacity: 100
  }
  {
    name: embeddingDeploymentName
    modelName: embeddingModelName
    location: 'secondary'
    skuName: 'Standard'
    modelVersion: '1'
    skuCapacity: 10
  }
  {
    name: speechDeploymentName
    modelName: speechModelName
    location: 'primary'
    skuName: 'Standard'
    modelVersion: '001'
    skuCapacity: 1
  }
]

@batchSize(1)
module openAIAccounts '../core/aoai/account.bicep' = [
  for (loc, _) in [location, location2]: {
    name: 'openAIAccount-${loc}'
    params: {
      name: '${accountName}-${loc}'
      location: loc
      tags: tags
      kind: 'OpenAI'
      sku: 'S0'
      enablePublicNetworkAccess: true
    }
  }]

var aoaiAccountMap = {
  primary: openAIAccounts[0].outputs.name
  secondary: openAIAccounts[1].outputs.name
}

@batchSize(1)
module openAiModelDeployments '../core/aoai/deployment.bicep' = [
  for (deployment, index) in deployments: {
    name: deployment.name
    params: {
      name: deployment.name
      parentAccountName: aoaiAccountMap[deployment.location]
      skuName: deployment.skuName
      skuCapacity: deployment.skuCapacity
      modelName: deployment.modelName
      modelVersion: deployment.modelVersion
      modelFormat: 'OpenAI'
    }
}]


output name_0 string = openAIAccounts[0].outputs.name
output endpoint_0 string = openAIAccounts[0].outputs.endpoint
output name_1 string = openAIAccounts[1].outputs.name
output endpoint_1 string = openAIAccounts[1].outputs.endpoint

output deployments array = [
  for (dep, index) in deployments: {
    name: openAiModelDeployments[index].name
    parentAccountName: aoaiAccountMap[dep.location]
  }
]
