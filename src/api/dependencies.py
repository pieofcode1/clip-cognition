"""Shared FastAPI dependencies for configuration and service singletons."""

import logging
import os
from functools import lru_cache

from core.agent_factory import VectorSearchAgentFactory, VectorSearchAgent
from core.config import load_environment, load_config, AppConfig
from core.storage_helper import StorageHelper

logger = logging.getLogger(__name__)

# Load environment once at module import
load_environment()


@lru_cache
def get_config() -> AppConfig:
    return load_config()


@lru_cache
def get_storage_helper() -> StorageHelper:
    return StorageHelper(container_name=os.environ["AZURE_STORAGE_CONTAINER_NAME"])


_search_agents: dict[str, VectorSearchAgent] = {}


def get_search_agent(vector_store_type: str) -> VectorSearchAgent:
    """Return a cached search agent for the given vector store type."""
    if vector_store_type not in _search_agents:
        _search_agents[vector_store_type] = VectorSearchAgentFactory.create_vector_search_agent(vector_store_type)
        logger.info("Created search agent for %s", vector_store_type)
    return _search_agents[vector_store_type]
