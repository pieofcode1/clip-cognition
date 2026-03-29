# ClipCognition

Intelligent media processing and video RAG using Azure OpenAI & Cosmos DB.

ClipCognition is a two-tier application:

- **FastAPI backend** — runs the video processing, embedding, and search logic in a Docker container (Azure Container Instances)
- **Next.js React frontend** — modern web UI that calls the API

Capabilities:

- **Extracts frames** from uploaded videos at configurable intervals
- **Transcribes audio** using Azure OpenAI Whisper
- **Summarizes** each frame and audio using GPT-4o
- **Generates vector embeddings** and stores them in Azure Cosmos DB or Azure DocumentDB
- **Enables semantic search** across video content via vector similarity
- **Dual vector-store support** — switch between Cosmos DB NoSQL and Azure DocumentDB at query time

## Architecture

| Component | Azure Service |
|---|---|
| API runtime | Azure Container Instances (Docker) |
| Container registry | Azure Container Registry |
| LLM (vision + text) | Azure OpenAI GPT-4o |
| Audio transcription | Azure OpenAI Whisper |
| Embeddings | Azure OpenAI text-embedding-3-large |
| Vector store (NoSQL) | Azure Cosmos DB NoSQL (native vector search) |
| Vector store (MongoDB) | Azure DocumentDB (MongoDB vCore — HNSW/IVF vector search) |
| Blob storage | Azure Storage |
| Identity | Managed Identity (User-Assigned) |
| IaC | Bicep + Azure Developer CLI (azd) |

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://docs.docker.com/get-docker/) (for building the API container)
- [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/)
- Azure subscription with the services above provisioned
- User-assigned managed identity with appropriate RBAC roles

## Getting Started

### 1. Clone & install

```bash
git clone https://github.com/pieofcode1/clip-cognition.git
cd clip-cognition
uv sync
```

### 2. Provision infrastructure

```bash
azd auth login
azd up
```

This provisions all Azure resources (Cosmos DB, DocumentDB, OpenAI, Storage, ACR, Managed Identity, RBAC) **except** the Container Instance — that requires a Docker image.

To also deploy the container instance after pushing an image:

```bash
azd env set DEPLOY_CONTAINER_INSTANCE true
azd up
```

### 3. Configure environment

After `azd up`, environment variables are written to `.azure/dev/.env` and `src/api/env/dev/.env` automatically.

For manual setup, copy the templates:

```bash
# API — all Azure service credentials
cp src/api/env/dev/.env.example src/api/env/dev/.env
```

See [src/api/env/dev/.env.example](src/api/env/dev/.env.example) for all required Azure variables.
The webapp reads the API URL from `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

### 4. Run the API locally

```bash
cd src
uv run uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 5. Run the Web App

In a separate terminal:

```bash
cd src/webapp
npm install
npm run dev
```

The webapp will be available at `http://localhost:3000`.

### 6. Build & push the Docker image

```bash
# Build
docker build -t clip-cognition-api .

# Tag & push to ACR
az acr login --name <your-acr-name>
docker tag clip-cognition-api <your-acr-name>.azurecr.io/clip-cognition-api:latest
docker push <your-acr-name>.azurecr.io/clip-cognition-api:latest
```

## Project Structure

```
src/
├── api/                         # FastAPI backend
│   ├── main.py                  # App entry point & health endpoint
│   ├── dependencies.py          # Dependency injection (config, agents)
│   ├── models.py                # Request/response Pydantic models
│   ├── env/dev/.env.example     # API environment variable template
│   └── routes/
│       ├── videos.py            # Video upload & analysis endpoints
│       ├── search.py            # Semantic search endpoint
│       └── assets.py            # Video assets, frames & blob listing
├── webapp/                      # Next.js React frontend
│   ├── src/app/                 # App Router pages (/, /dashboard, /analyze, /search, /assets/[id])
│   ├── src/components/          # Reusable React components (navbar, frame gallery)
│   ├── src/lib/                 # API client, types, settings context
│   └── package.json             # Node.js dependencies
├── core/                        # Shared business logic
│   ├── config.py                # Centralized config & env validation
│   ├── schema.py                # Pydantic data models & enums
│   ├── prompts.py               # LLM prompt templates
│   ├── video_processor.py       # Video processing pipeline
│   ├── agent_factory.py         # Vector search agent factory (dual-backend)
│   ├── embedding_agent.py       # Text/image embedding agents
│   ├── cosmos_util.py           # Cosmos DB NoSQL client
│   ├── az_documentdb_util.py    # Azure DocumentDB (MongoDB vCore) client
│   ├── storage_helper.py        # Azure Blob Storage helper
│   └── utilities.py             # Shared utilities (timer decorator)
infra/                           # Azure Bicep IaC
├── main.bicep                   # Subscription-level orchestration
├── main.parameters.json         # Parameter file for azd
├── app/                         # Application-level modules
│   ├── aoai.bicep               # Azure OpenAI accounts & deployments
│   ├── cosmosdb.bicep           # Cosmos DB NoSQL (database + containers)
│   ├── documentdb.bicep         # Azure DocumentDB cluster + firewall + RBAC
│   ├── container.bicep          # ACR + ACI (conditional)
│   ├── identity.bicep           # User-assigned managed identity
│   ├── security.bicep           # RBAC role assignments
│   ├── storage.bicep            # Storage account + blob container
│   └── web.bicep                # App Service (optional)
├── core/                        # Reusable Bicep modules
│   ├── aoai/                    # OpenAI account & deployment
│   ├── app-service/             # App Service plan, site, config
│   ├── container/               # ACR registry & ACI instance
│   ├── cosmosdb/
│   │   ├── nosql/               # Cosmos DB NoSQL account, database, container, roles
│   │   └── mongo-vcore/         # DocumentDB cluster, firewall rules, role assignments
│   ├── security/                # Generic RBAC role assignment & definition
│   └── storage/                 # Storage account & role assignment
Dockerfile                       # API container image
azure.yaml                       # azd project configuration
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check with backend status (`cosmosdb_nosql`, `azure_documentdb`) |
| `POST` | `/videos/upload` | Upload video to blob storage (returns preview URL) |
| `POST` | `/videos/analyze` | Analyze a previously uploaded video (by blob key) |
| `POST` | `/search` | Semantic vector search across video frames |
| `GET` | `/assets/videos` | List all processed video assets |
| `GET` | `/assets/videos/{id}` | Get a single video asset with playback URL |
| `GET` | `/assets/videos/{id}/frames` | List frames for a video asset |
| `GET` | `/assets/frames/{blob_key}/url` | Generate SAS URL for a frame image |
| `GET` | `/assets/blobs` | List all blobs in the storage container |

All endpoints that query the database accept a `vector_store_type` parameter (`CosmosDB NoSQL` or `Azure DocumentDB`) to choose the backend.

## Vector Store Backends

### Cosmos DB NoSQL
- Uses native [vector search](https://learn.microsoft.com/azure/cosmos-db/nosql/vector-search) with `quantizedFlat` indexes
- Authentication via managed identity (RBAC, no keys)
- Data plane access through the Cosmos DB SDK

### Azure DocumentDB (MongoDB vCore)
- Uses [HNSW or IVF vector indexes](https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/vector-search) via the MongoDB wire protocol
- Authentication via connection string (username/password)
- Control plane RBAC via managed identity (Contributor role)
- Firewall rules for Azure services and developer IP

## Infrastructure

Azure resources are provisioned using Bicep templates in `infra/` with [Azure Developer CLI (azd)](https://learn.microsoft.com/azure/developer/azure-developer-cli/).

Key parameters in `main.parameters.json`:

| Parameter | Source env var | Description |
|---|---|---|
| `documentDbAdminLogin` | `AZURE_DOCUMENTDB_ADMIN_LOGIN` | DocumentDB admin username (default: `pieadmin`) |
| `documentDbAdminPassword` | `AZURE_DOCUMENTDB_ADMIN_PASSWORD` | DocumentDB admin password |
| `developerIpAddress` | `AZURE_DEVELOPER_IP_ADDRESS` | Developer IP for DocumentDB firewall |
| `deployContainerInstance` | — | Set to `true` after pushing Docker image to ACR |

The ACI deployment is conditional (`deployContainer = false` by default) to allow infrastructure provisioning before the Docker image exists.

## License

See [LICENSE](LICENSE) for details.
