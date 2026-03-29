"""Azure Blob Storage helper for upload, download, and SAS token generation."""

import logging
import os
from datetime import datetime, timedelta, timezone

from azure.identity import DefaultAzureCredential
from azure.storage.blob import (
    AccountSasPermissions,
    BlobServiceClient,
    ContentSettings,
    ResourceTypes,
    generate_blob_sas,
)

logger = logging.getLogger(__name__)


class StorageHelper:
    """Wrapper around Azure Blob Storage operations for a single container."""

    def __init__(self, container_name: str) -> None:
        endpoint = os.environ["AZURE_STORAGE_ACCOUNT_ENDPOINT"]
        client_id = os.environ["USER_ASSIGNED_ID_CLIENT_ID"]

        credential = DefaultAzureCredential(managed_identity_client_id=client_id)
        self.blob_service_client = BlobServiceClient(account_url=endpoint, credential=credential)
        self.container_client = self.blob_service_client.get_container_client(container_name)

    def upload_blob(self, file: str, mime_type: str | None = None) -> str:
        content_settings = ContentSettings(content_type=mime_type) if mime_type else None
        with open(file, "rb") as data:
            blob_client = self.container_client.upload_blob(
                name=os.path.basename(file), data=data, overwrite=True, content_settings=content_settings
            )
            return blob_client.url

    def upload_blob_with_key(self, file: str, blob_key: str, mime_type: str | None = None) -> str:
        content_settings = ContentSettings(content_type=mime_type) if mime_type else None
        with open(file, "rb") as data:
            blob_client = self.container_client.upload_blob(
                name=blob_key, data=data, overwrite=True, content_settings=content_settings
            )
            return blob_client.url

    def upload_blob_from_stream(self, stream, blob_key: str, mime_type: str | None = None) -> str:
        content_settings = ContentSettings(content_type=mime_type) if mime_type else None
        blob_client = self.container_client.upload_blob(
            name=blob_key, data=stream, overwrite=True, content_settings=content_settings
        )
        return blob_client.url

    def download_blob(self, blob_key: str, file_path: str) -> None:
        blob_client = self.container_client.get_blob_client(blob_key)
        with open(file_path, "wb") as blob_file:
            download_stream = blob_client.download_blob()
            blob_file.write(download_stream.readall())

    def list_blobs(self):
        return self.container_client.list_blobs()

    def delete_blob(self, blob_key: str) -> None:
        self.container_client.delete_blob(blob_key)
        logger.info("Blob %s deleted.", blob_key)

    def generate_blob_sas_token(self, blob_key: str) -> str:
        blob_client = self.container_client.get_blob_client(blob_key)
        now = datetime.now(timezone.utc)
        sas_token = generate_blob_sas(
            self.blob_service_client.account_name,
            container_name=self.container_client.container_name,
            blob_name=blob_client.blob_name,
            user_delegation_key=self.blob_service_client.get_user_delegation_key(now, now + timedelta(hours=1)),
            account_key=None,
            resource_types=ResourceTypes(object=True),
            permission=AccountSasPermissions(read=True),
            expiry=now + timedelta(hours=1),
        )
        return f"{blob_client.url}?{sas_token}"
