"""FastAPI application entry point for the ClipCognition API."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.models import HealthResponse
from api.routes import assets, search, videos

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

app = FastAPI(
    title="ClipCognition API",
    description="Video processing, analysis, and semantic search API powered by Azure OpenAI & Cosmos DB.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(videos.router)
app.include_router(search.router)
app.include_router(assets.router)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health():
    """Health check — runs in a thread pool so blocking DB probes don't stall the event loop."""
    backends = {"cosmosdb_nosql": False, "azure_documentdb": False}

    # Check CosmosDB
    try:
        from api.dependencies import get_search_agent
        get_search_agent("CosmosDB")
        backends["cosmosdb_nosql"] = True
    except Exception:
        pass

    # Check Azure DocumentDB
    try:
        conn_str = os.environ.get("MONGODB_CONNECTION_STRING", "")
        if conn_str and "<user>" not in conn_str and "<password>" not in conn_str:
            from core.az_documentdb_util import AzDocumentDBClient
            client = AzDocumentDBClient(conn_str, os.environ.get("MONGODB_DB_NAME", ""))
            client.ping()
            client.close_connection()
            backends["azure_documentdb"] = True
    except Exception:
        pass

    return HealthResponse(backends=backends)
