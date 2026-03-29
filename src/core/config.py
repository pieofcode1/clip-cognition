"""Centralized configuration loaded from environment variables with validation."""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

import dotenv

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AzureOpenAIConfig:
    completion_endpoint: str
    completion_deployment_name: str
    embedding_endpoint: str
    embedding_deployment_name: str
    whisper_endpoint: str
    whisper_deployment_name: str
    api_version: str


@dataclass(frozen=True)
class AzureCosmosConfig:
    endpoint: str
    database_name: str
    video_assets_container: str
    video_asset_frames_container: str


@dataclass(frozen=True)
class AzureStorageConfig:
    account_endpoint: str
    container_name: str


@dataclass(frozen=True)
class AzureIdentityConfig:
    tenant_id: str
    client_id: str


@dataclass(frozen=True)
class DocumentDBConfig:
    connection_string: str
    db_name: str


@dataclass(frozen=True)
class AppConfig:
    identity: AzureIdentityConfig
    openai: AzureOpenAIConfig
    cosmos: AzureCosmosConfig
    storage: AzureStorageConfig
    documentdb: DocumentDBConfig | None = None


def _require_env(key: str) -> str:
    """Return the value of an environment variable or raise with a clear message."""
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


def _optional_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def load_environment() -> None:
    """Load .env file based on AZURE_ENV_NAME (defaults to 'dev')."""
    env_name = os.environ.get("AZURE_ENV_NAME", "dev")
    env_file_path = Path(f"./api/env/{env_name}/.env")
    if env_file_path.exists():
        dotenv.load_dotenv(dotenv_path=env_file_path)
        logger.info("Loaded environment from %s", env_file_path)
    else:
        logger.warning("Environment file not found at %s — using existing env vars", env_file_path)


def load_config() -> AppConfig:
    """Build and validate the full application config from environment variables."""
    identity = AzureIdentityConfig(
        tenant_id=_require_env("AZURE_TENANT_ID"),
        client_id=_require_env("USER_ASSIGNED_ID_CLIENT_ID"),
    )
    openai_cfg = AzureOpenAIConfig(
        completion_endpoint=_require_env("AZURE_OPENAI_COMPLETION_DEPLOYMENT_ENDPOINT"),
        completion_deployment_name=_require_env("AZURE_OPENAI_COMPLETION_DEPLOYMENT_NAME"),
        embedding_endpoint=_require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT"),
        embedding_deployment_name=_require_env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"),
        whisper_endpoint=_require_env("AZURE_OPENAI_WHISPER_DEPLOYMENT_ENDPOINT"),
        whisper_deployment_name=_require_env("AZURE_OPENAI_WHISPER_DEPLOYMENT_NAME"),
        api_version=_require_env("AZURE_OPENAI_API_VERSION"),
    )
    cosmos = AzureCosmosConfig(
        endpoint=_require_env("AZURE_COSMOS_DB_ENDPOINT"),
        database_name=_require_env("AZURE_COSMOS_DB_DATABASE_NAME"),
        video_assets_container=_require_env("AZURE_COSMOS_DB_VIDEO_ASSETS_CONTAINER_NAME"),
        video_asset_frames_container=_require_env("AZURE_COSMOS_DB_VIDEO_ASSET_FRAMES_CONTAINER_NAME"),
    )
    storage = AzureStorageConfig(
        account_endpoint=_require_env("AZURE_STORAGE_ACCOUNT_ENDPOINT"),
        container_name=_require_env("AZURE_STORAGE_CONTAINER_NAME"),
    )

    # DocumentDB is optional — only required for Azure DocumentDB vector store
    documentdb = None
    mongo_conn = _optional_env("MONGODB_CONNECTION_STRING")
    mongo_db = _optional_env("MONGODB_DB_NAME")
    if mongo_conn and mongo_db:
        documentdb = DocumentDBConfig(connection_string=mongo_conn, db_name=mongo_db)

    return AppConfig(
        identity=identity,
        openai=openai_cfg,
        cosmos=cosmos,
        storage=storage,
        documentdb=documentdb,
    )
