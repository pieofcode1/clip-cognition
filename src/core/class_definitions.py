from enum import Enum
from typing import List, Dict, Any
from core.schema import *
from core.embedding_agent import *
from core.cosmos_util import CosmosUtil
from core.cosmos_mongo_util import CosmosMongoClient


class VectorSearchAgent:
    def __init__(self, vector_store_type: VectorStoreType, container_names: List[str]) -> None:
        self.vector_store_type = vector_store_type
        self.container_names = container_names

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, limit: int) -> VectorSearchResult:
        raise NotImplementedError

    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[Dict[str, Any]]:
        raise NotImplementedError


class CosmosNoSQLVectorSearchAgent(VectorSearchAgent):
    
    def __init__(self) -> None:
        container_names = [
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"], 
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
        ]
        super().__init__(VectorStoreType.CosmosNoSQL, container_names)
        cosmos_sql_agent = CosmosUtil(
            containers=container_names,
            embedding_agent = AzureOpenAIEmbeddingsAgent()
        )
        self.client = cosmos_sql_agent

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> VectorSearchResult:
        response = self.client.perform_vector_search(
            collection_name, prompt=query, 
            content_vector_field=attr_name, projection=projection , limit=limit)
        
        return response
    
    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[Dict[str, Any]]:
        _, items = self.client.query_items(collection_name, filter, limit)
        return items

class CosmosMongoVCoreVectorSearchAgent(VectorSearchAgent):

    def __init__(self) -> None:
        container_names = [
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"], 
            os.environ["AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"]
        ]
        super().__init__(VectorStoreType.CosmosMongoVCore, container_names)
        cosmos_mongo_client = CosmosMongoClient(
            os.environ["MONGODB_CONNECTION_STRING"],
            os.environ["MONGODB_DB_NAME"],
            embedding_agent=AzureOpenAIEmbeddingsAgent()
        )
        self.client = create_cosmos_mongo_vector_search_agent(container_names=container_names)

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> VectorSearchResult:
        response = self.client.perform_vector_search(collection_name, attr_name, prompt=query, projection=projection, limit=limit)
        return response
    
    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[Dict[str, Any]]:
        response = self.client.find(collection_name, filter, limit)
        return response

class AISearchVectorSearchAgent(VectorSearchAgent):

    def __init__(self, index_names: List[str]) -> None:
        self.index_collection_map = {
            "CC_VideoAssets": "cc-video-asset-index",
            "CC_VideoAssetFrames": "cc-video-asset-frames-index"
        }
        super().__init__(VectorStoreType.AISearch, container_names=index_names)
        self.index_client_map = get_ai_search_index_clients(index_names=index_names)

    def perform_vector_search(self, collection_name: str, attr_name: str, query: str, projection: list[str], limit: int) -> VectorSearchResult:
        response = perform_vector_search(
                            self.index_client_map[self.index_collection_map[collection_name]], 
                            attr_name=attr_name,
                            vectorized_query=query, 
                            projection=projection 
            )
        return response
    
    def perform_search(self, collection_name: str, filter: dict, limit: int) -> List[Dict[str, Any]]:
        pass


class VectorSearchAgentFactory:

    @staticmethod
    def create_vector_search_agent(vector_store_type: str) -> VectorSearchAgent:
        print(f"Creating vector search agent for {vector_store_type}")
        if vector_store_type == VectorStoreType.CosmosNoSQL.value:
            return CosmosNoSQLVectorSearchAgent()
        elif vector_store_type == VectorStoreType.CosmosMongoVCore.value:
            return CosmosMongoVCoreVectorSearchAgent()
        elif vector_store_type == VectorStoreType.AISearch.value:
            return AISearchVectorSearchAgent(index_names=["cc-video-asset-index", "cc-video-asset-frames-index"])
        else:
            raise ValueError(f"Invalid vector store type: {vector_store_type}")
