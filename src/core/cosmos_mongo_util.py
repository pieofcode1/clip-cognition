"""Azure DocumentDB utility for CRUD and vector search operations."""

import json
import logging
from typing import Any

from bson import json_util
from pymongo import MongoClient

logger = logging.getLogger(__name__)


class CosmosDocumentDBClient:
    """Client wrapper for Azure DocumentDB with vector search support."""

    def __init__(self, connection_uri: str, db_name: str, embedding_agent=None) -> None:
        self.mongodb_client = MongoClient(connection_uri)
        self.database = self.mongodb_client[db_name]
        self.embedding_agent = embedding_agent

    def ping(self) -> None:
        self.mongodb_client.admin.command("ping")

    def create_collection(self, collection_name: str) -> None:
        self.database.create_collection(collection_name)

    def get_collection(self, collection_name: str):
        return self.database[collection_name]

    def create_vector_index(
        self,
        collection_name: str,
        attr_name: str,
        index_name: str,
        index_type: str = "vector-hnsw",
        num_lists: int = 1,
        similarity: str = "COS",
        dimensions: int = 1536,
    ) -> None:
        if index_type == "vector-ivf":
            search_options = {
                "kind": index_type,
                "numLists": num_lists,
                "similarity": similarity,
                "dimensions": dimensions,
            }
        elif index_type == "vector-hnsw":
            search_options = {
                "kind": index_type,
                "m": 64,
                "efConstruction": 256,
                "similarity": similarity,
                "dimensions": dimensions,
            }
        else:
            raise ValueError(f"Invalid index type '{index_type}'. Supported: 'vector-ivf', 'vector-hnsw'")

        self.database.command({
            "createIndexes": collection_name,
            "indexes": [{
                "name": index_name,
                "key": {attr_name: "cosmosSearch"},
                "cosmosSearchOptions": search_options,
            }],
        })
        logger.info("Created %s index '%s' on %s.%s", index_type, index_name, collection_name, attr_name)

    def insert(self, collection_name: str, data) -> None:
        collection = self.database[collection_name]
        if isinstance(data, dict):
            items = [json.loads(json_util.dumps(data))]
        else:
            items = [json.loads(json_util.dumps(item)) for item in data]
        collection.insert_many(items)

    def find(self, collection_name: str, filter: dict | None = None, limit: int = 100) -> list[dict[str, Any]]:
        collection = self.database[collection_name]
        result = collection.find(filter=filter or {}, limit=limit)
        return list(result)

    def perform_vector_search(
        self,
        collection_name: str,
        attr_name: str,
        prompt: str,
        projection: list[str] | None = None,
        limit: int = 3,
    ) -> list[dict]:
        collection = self.database[collection_name]
        embedding_vector = self.embedding_agent.get_text_embeddings(prompt)

        projected_fields: dict = {"similarityScore": {"$meta": "searchScore"}}
        if projection:
            for field in projection:
                projected_fields[field] = 1
        else:
            projected_fields["document"] = "$$ROOT"

        pipeline = [
            {
                "$search": {
                    "cosmosSearch": {
                        "vector": embedding_vector,
                        "path": attr_name,
                        "k": limit,
                        "efsearch": 40,
                    },
                    "returnStoredSource": True,
                }
            },
            {"$project": projected_fields},
        ]
        results = collection.aggregate(pipeline)
        return list(results)

    def close_connection(self) -> None:
        self.mongodb_client.close()
