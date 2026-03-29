"""Embedding agents for generating text and image vector embeddings."""

import logging
import os
from abc import ABC, abstractmethod

import requests
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

logger = logging.getLogger(__name__)


class BaseEmbeddingAgent(ABC):
    """Base class for embedding agents."""

    @abstractmethod
    def get_text_embeddings(self, text: str) -> list[float]:
        ...

    @abstractmethod
    def get_image_embeddings(self, blob_image_path: str) -> list[float]:
        ...


class AzureOpenAIEmbeddingsAgent(BaseEmbeddingAgent):
    """Generates text embeddings using Azure OpenAI."""

    def __init__(self) -> None:
        client_id = os.environ["USER_ASSIGNED_ID_CLIENT_ID"]
        credential = DefaultAzureCredential(managed_identity_client_id=client_id)
        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        self._client = AzureOpenAI(
            azure_ad_token_provider=token_provider,
            azure_endpoint=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT"],
            api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        )
        self._deployment_name = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME"]
        self._dimensions = 1536

    def get_text_embeddings(self, text: str) -> list[float]:
        response = self._client.embeddings.create(input=text, model=self._deployment_name, dimensions=self._dimensions)
        return response.data[0].embedding

    def get_image_embeddings(self, blob_image_path: str) -> list[float]:
        raise NotImplementedError("Image embeddings are not supported by Azure OpenAI embedding models.")


class AIVisionEmbeddingsAgent(BaseEmbeddingAgent):
    """Generates text and image embeddings using Azure AI Vision."""

    def __init__(self) -> None:
        self._endpoint = os.environ["COGNITIVE_MULTISVC_ENDPOINT"]
        self._api_key = os.environ["COGNITIVE_MULTISVC_API_KEY"]

    def _call_vision_api(self, operation: str, payload: dict) -> list[float]:
        url = (
            f"{self._endpoint}/computervision/retrieval:{operation}"
            "?api-version=2024-02-01&model-version=2023-04-15"
        )
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": self._api_key,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["vector"]

    def get_text_embeddings(self, text: str) -> list[float]:
        return self._call_vision_api("vectorizeText", {"text": text})

    def get_image_embeddings(self, blob_image_path: str) -> list[float]:
        return self._call_vision_api("vectorizeImage", {"url": blob_image_path})
