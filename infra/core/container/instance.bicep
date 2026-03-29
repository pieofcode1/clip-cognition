metadata description = 'Creates an Azure Container Instance.'

param name string
param location string = resourceGroup().location
param tags object = {}

@description('Container image to deploy (e.g. myregistry.azurecr.io/app:latest)')
param containerImage string

@description('CPU cores to allocate.')
param cpuCores int = 1

@description('Memory in GB to allocate.')
param memoryInGb int = 2

@description('Port the container listens on.')
param port int = 8000

@description('Environment variables for the container.')
param environmentVariables array = []

@description('ACR login server (e.g. myregistry.azurecr.io)')
param acrLoginServer string

@description('ACR admin username.')
@secure()
param acrUsername string

@description('ACR admin password.')
@secure()
param acrPassword string

@description('User-assigned managed identity resource ID.')
param userAssignedIdentityId string

resource containerGroup 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: name
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${userAssignedIdentityId}': {}
    }
  }
  properties: {
    osType: 'Linux'
    restartPolicy: 'OnFailure'
    imageRegistryCredentials: [
      {
        server: acrLoginServer
        username: acrUsername
        password: acrPassword
      }
    ]
    containers: [
      {
        name: name
        properties: {
          image: containerImage
          ports: [
            {
              port: port
              protocol: 'TCP'
            }
          ]
          resources: {
            requests: {
              cpu: cpuCores
              memoryInGB: memoryInGb
            }
          }
          environmentVariables: environmentVariables
        }
      }
    ]
    ipAddress: {
      type: 'Public'
      ports: [
        {
          port: port
          protocol: 'TCP'
        }
      ]
    }
  }
}

output name string = containerGroup.name
output fqdn string = containerGroup.properties.ipAddress.fqdn
output ipAddress string = containerGroup.properties.ipAddress.ip
