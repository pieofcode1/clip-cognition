# Next Steps

## Table of Contents

1. [Deployment](#deployment)
2. [Post-Deployment](#post-deployment)
3. [Local Development](#local-development)
4. [CI/CD](#cicd)
5. [Troubleshooting](#troubleshooting)

## Deployment

### 1. Provision infrastructure

```bash
azd auth login
azd up
```

This deploys all Azure resources **except** the Container Instance (no Docker image yet):

| Resource | Module |
|---|---|
| User-Assigned Managed Identity | `infra/app/identity.bicep` |
| Azure OpenAI (GPT-4o, Whisper, Embeddings) | `infra/app/aoai.bicep` |
| Cosmos DB NoSQL (database + 4 containers) | `infra/app/cosmosdb.bicep` |
| Azure DocumentDB (MongoDB vCore cluster + firewall) | `infra/app/documentdb.bicep` |
| Azure Storage (blob container) | `infra/app/storage.bicep` |
| Azure Container Registry | `infra/app/container.bicep` |
| RBAC role assignments | `infra/app/security.bicep` |

### 2. Set DocumentDB credentials

Before first deployment, set the admin password:

```bash
azd env set AZURE_DOCUMENTDB_ADMIN_PASSWORD "YourStrongPassword123!"
azd env set AZURE_DEVELOPER_IP_ADDRESS "your.public.ip"
```

### 3. Build & deploy the container

```bash
# Build the Docker image
docker build -t clip-cognition-api .

# Push to ACR
az acr login --name $(azd env get-value AZURE_CONTAINER_REGISTRY_NAME)
docker tag clip-cognition-api $(azd env get-value AZURE_CONTAINER_REGISTRY_LOGIN_SERVER)/clip-cognition-api:latest
docker push $(azd env get-value AZURE_CONTAINER_REGISTRY_LOGIN_SERVER)/clip-cognition-api:latest

# Enable ACI deployment & re-provision
azd env set DEPLOY_CONTAINER_INSTANCE true
azd up
```

## Post-Deployment

After `azd up`, environment variables are automatically written to `.azure/dev/.env`. Key outputs:

| Variable | Description |
|---|---|
| `MONGODB_CONNECTION_STRING` | DocumentDB connection string (credentials embedded) |
| `MONGODB_DB_NAME` | DocumentDB database name |
| `AZURE_COSMOS_DB_ENDPOINT` | Cosmos DB NoSQL endpoint |
| `AZURE_DOCUMENTDB_CLUSTER_NAME` | DocumentDB cluster name |
| `AZURE_CONTAINER_REGISTRY_LOGIN_SERVER` | ACR login server |

The API `/health` endpoint reports backend availability:

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "backends": {
    "cosmosdb_nosql": true,
    "azure_documentdb": true
  }
}
```

## Local Development

### Run the API

```bash
cd src
uv run uvicorn api.main:app --reload
```

The API loads environment from `src/api/env/dev/.env`. After `azd up`, copy values from `.azure/dev/.env` or use `azd env get-values` to populate.

### Run the Web App

```bash
cd src/webapp
npm install
npm run dev
```

The webapp will be available at `http://localhost:3000`.

### Environment variable flow

```
azd env (input)  →  main.parameters.json  →  main.bicep  →  .azure/dev/.env (output)
                                                           →  ACI env vars (in Azure)
```

- **Input params**: `AZURE_DOCUMENTDB_ADMIN_LOGIN`, `AZURE_DOCUMENTDB_ADMIN_PASSWORD`, `AZURE_DEVELOPER_IP_ADDRESS`
- **Outputs**: All `AZURE_*`, `MONGODB_*`, `USER_ASSIGNED_*` variables

For local development, `src/api/env/dev/.env` should mirror the relevant values from `.azure/dev/.env`.

## CI/CD

### Configure pipeline

1. Create a workflow pipeline file:
   - [Deploy with GitHub Actions](https://github.com/Azure-Samples/azd-starter-bicep/blob/main/.github/workflows/azure-dev.yml)
   - [Deploy with Azure Pipelines](https://github.com/Azure-Samples/azd-starter-bicep/blob/main/.azdo/pipelines/azure-dev.yml)
2. Run `azd pipeline config` to configure the deployment pipeline to connect securely to Azure.

## Troubleshooting

### DocumentDB connection fails

- Verify your public IP is in the firewall: `azd env set AZURE_DEVELOPER_IP_ADDRESS "your.ip"` then `azd up`
- Confirm `MONGODB_CONNECTION_STRING` does not contain `<user>` or `<password>` placeholders
- Check the cluster exists: `az resource list -g <rg> --resource-type Microsoft.DocumentDB/mongoClusters -o table`

### Cosmos DB returns 403

- Ensure your IP is allowed in Cosmos DB Networking (Azure Portal)
- Verify RBAC role assignments completed: check `infra/app/security.bicep` SQL role definitions

### ACI fails with InaccessibleImage

- The Docker image must be pushed to ACR before enabling ACI
- Set `DEPLOY_CONTAINER_INSTANCE` to `false` (default) for initial infra provisioning
- Push the image, then set to `true` and re-run `azd up`

### MFA token expired

```bash
azd auth logout
az logout
az login --tenant <tenant-id>
azd auth login --tenant-id <tenant-id>
```

### Billing

Visit *Cost Management + Billing* in Azure Portal. Key cost drivers:
- Azure OpenAI (token consumption)
- DocumentDB M40 cluster (compute + storage)
- Cosmos DB NoSQL (RU consumption)
- Azure Container Instances (vCPU + memory hours)
