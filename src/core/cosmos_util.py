"""Azure Cosmos DB NoSQL API utility for CRUD and vector search operations."""

import logging
import os
from datetime import datetime
from typing import Any, List

import azure.cosmos.exceptions as exceptions
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.diagnostics import RecordDiagnostics
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


class CosmosUtil:
    """Manages Azure Cosmos DB NoSQL containers and provides vector search."""

    def __init__(self, auth_type: str = "mi", database: str = "", containers: list | None = None, embedding_agent=None) -> None:
        self.database_name = database or os.environ["AZURE_COSMOS_DB_DATABASE_NAME"]
        self.embedding_agent = embedding_agent

        container_names: list[str] = []
        if containers is not None:
            container_names = containers if isinstance(containers, list) else [containers]

        self.container_map: dict[str, Any] = {}

        if auth_type == "conn_str":
            connection_string = os.environ["AZURE_COSMOS_CONNECTION_STRING"]
            self.cosmos_client = CosmosClient.from_connection_string(connection_string)
        elif auth_type == "mi":
            endpoint = os.environ["AZURE_COSMOS_DB_ENDPOINT"]
            client_id = os.environ["USER_ASSIGNED_ID_CLIENT_ID"]
            credential = DefaultAzureCredential(managed_identity_client_id=client_id)
            self.cosmos_client = CosmosClient(endpoint, credential=credential)
        else:
            raise ValueError(f"Invalid authentication type: {auth_type}")

        self.database_client = self.cosmos_client.create_database_if_not_exists(self.database_name)
        logger.info("Initialized Cosmos DB database: %s with containers: %s", self.database_name, container_names)

        for name in container_names:
            self.container_map[name] = self.database_client.get_container_client(name)

    def add_containers(self, container_names: list[str]) -> None:
        for name in container_names:
            self.container_map[name] = self.database_client.get_container_client(name)

    def upsert_items(self, container: str, items) -> None:
        documents = items if isinstance(items, list) else [items]
        container_client = self.container_map[container]

        for item in documents:
            container_client.upsert_item(body=item)
            request_charge = container_client.client_connection.last_response_headers.get("x-ms-request-charge", "N/A")
            logger.debug("Upserted item — RU charge: %s", request_charge)

    def query_items(self, container: str, predicate, limit: int | None = None):
        container_client = self.container_map[container]
        top_clause = f"TOP {limit}" if limit else ""

        if not predicate:
            query = f"SELECT {top_clause} * FROM r"
        elif isinstance(predicate, dict):
            conditions = " AND ".join(f"r.{k} = '{v}'" for k, v in predicate.items())
            query = f"SELECT {top_clause} * FROM r WHERE {conditions}"
        else:
            query = f"SELECT {top_clause} * FROM r WHERE r.{predicate}"

        logger.debug("Cosmos query: %s", query)

        diagnostics = RecordDiagnostics()
        items = list(container_client.query_items(
            query=query,
            enable_cross_partition_query=True,
            response_hook=diagnostics,
        ))
        ru_consumption = (
            datetime.now().isoformat(),
            diagnostics.request_charge,
            float(diagnostics.headers.get("x-ms-request-duration-ms", 0)),
        )
        return ru_consumption, items

    def create_vector_embedding_policy(self, field_paths: List[str]) -> dict:
        return {
            "vectorEmbeddings": [
                {"path": field, "dataType": "float32", "distanceFunction": "cosine", "dimensions": 1536}
                for field in field_paths
            ]
        }

    def create_indexing_policy(self, field_paths: List[str]) -> dict:
        excluded_paths = [{"path": "/\"_etag\"/?"}]
        vector_indexes = []
        for field in field_paths:
            excluded_paths.append({"path": f"{field}/*"})
            vector_indexes.append({"path": field, "type": "quantizedFlat"})

        return {
            "includedPaths": [{"path": "/*"}],
            "excludedPaths": excluded_paths,
            "vectorIndexes": vector_indexes,
        }

    def create_container_with_vectors(self, container_name: str, partition_key: str, vector_fields: List[str]):
        try:
            container = self.database_client.create_container_if_not_exists(
                id=container_name,
                partition_key=PartitionKey(path=partition_key),
                vector_embedding_policy=self.create_vector_embedding_policy(vector_fields),
                indexing_policy=self.create_indexing_policy(vector_fields),
            )
            self.container_map[container_name] = container
            return container
        except exceptions.CosmosResourceExistsError:
            container = self.database_client.get_container_client(container_name)
            self.container_map[container_name] = container
            return container

    def perform_vector_search(self, container_name: str, prompt: str, content_vector_field: str = "summary_vector", projection: list | None = None, limit: int = 3):
        container_client = self.container_map[container_name]
        prompt_vector = self.embedding_agent.get_text_embeddings(prompt)

        if projection:
            projected_fields = ", ".join(f"c.{p}" for p in projection)
        else:
            projected_fields = "*"

        items = list(container_client.query_items(
            query=(
                f"SELECT TOP @limit {projected_fields}, "
                f"VectorDistance(c.{content_vector_field}, @prompt_vector) AS similarity_score "
                f"FROM c ORDER BY VectorDistance(c.{content_vector_field}, @prompt_vector)"
            ),
            parameters=[
                {"name": "@limit", "value": limit},
                {"name": "@prompt_vector", "value": prompt_vector},
            ],
            enable_cross_partition_query=True,
        ))
        logger.debug("Vector search returned %d results.", len(items))
        return items
