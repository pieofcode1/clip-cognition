"""Factory for creating vector search agents backed by different stores."""

import logging
import os
from typing import Any, List

from core.az_documentdb_util import AzDocumentDBClient
from core.cosmos_util import CosmosUtil
from core.embedding_agent import AzureOpenAIEmbeddingsAgent
from core.schema import VectorStoreType

logger = logging.getLogger(__name__)


class VectorSearchAgent:
    """Base class for vector search operations."""

    def __init__(self, vector_store_type: VectorStoreType, container_names: List[str]) -> None:
        self.vector_store_type = vector_store_type
        self.container_names = container_names

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> list[dict]:
        raise NotImplementedError

    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[dict[str, Any]]:
        raise NotImplementedError


class CosmosNoSQLVectorSearchAgent(VectorSearchAgent):

    def __init__(self) -> None:
        container_names = [
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"],
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"],
        ]
        database_name = os.environ["AZURE_COSMOS_DB_DATABASE_NAME"]
        super().__init__(VectorStoreType.CosmosNoSQL, container_names)
        self.client = CosmosUtil(
            database=database_name,
            containers=container_names,
            embedding_agent=AzureOpenAIEmbeddingsAgent(),
        )

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> list[dict]:
        return self.client.perform_vector_search(
            collection_name, prompt=query, content_vector_field=attr_name, projection=projection, limit=limit,
        )

    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[dict[str, Any]]:
        _, items = self.client.query_items(collection_name, filter, limit)
        return items


class AzDocumentDBVectorSearchAgent(VectorSearchAgent):

    def __init__(self) -> None:
        container_names = [
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"],
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"],
        ]
        super().__init__(VectorStoreType.AzureDocumentDB, container_names)

        conn_str = os.environ.get("MONGODB_CONNECTION_STRING", "")
        if not conn_str or "<user>" in conn_str or "<password>" in conn_str:
            raise ValueError(
                "MONGODB_CONNECTION_STRING is not configured or still contains placeholders. "
                "Run 'azd up' to provision DocumentDB and populate the connection string."
            )

        self.client = AzDocumentDBClient(
            conn_str,
            os.environ["MONGODB_DB_NAME"],
            embedding_agent=AzureOpenAIEmbeddingsAgent(),
        )

        # Ensure vector indexes exist on DocumentDB collections
        frames_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
        self.client.ensure_vector_index(frames_container, "summary_vector", "idx_summary_vector", dimensions=1536)

        assets_container = os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"]
        self.client.ensure_vector_index(assets_container, "video_summary_vector", "idx_video_summary_vector", dimensions=1536)
        self.client.ensure_vector_index(assets_container, "audio_summary_vector", "idx_audio_summary_vector", dimensions=1536)

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> list[dict]:
        return self.client.perform_vector_search(collection_name, attr_name, prompt=query, projection=projection, limit=limit)

    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[dict[str, Any]]:
        return self.client.find(collection_name, filter, limit)


class VectorSearchAgentFactory:

    @staticmethod
    def create_vector_search_agent(vector_store_type: str) -> VectorSearchAgent:
        logger.info("Creating vector search agent for %s", vector_store_type)
        if vector_store_type == VectorStoreType.CosmosNoSQL.value:
            return CosmosNoSQLVectorSearchAgent()
        elif vector_store_type == VectorStoreType.AzureDocumentDB.value:
            return AzDocumentDBVectorSearchAgent()
        else:
            raise ValueError(f"Unsupported vector store type: {vector_store_type}")
