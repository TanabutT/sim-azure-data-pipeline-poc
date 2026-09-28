import logging
from typing import List, Optional
from azure.storage.blob import BlobServiceClient, ContainerClient
from azure.core.exceptions import AzureError
from .config import Config
from .exceptions import StorageException

logger = logging.getLogger(__name__)


class AzuriteStorageClient:
    """Client for interacting with Azurite storage"""

    def __init__(
        self,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None,
        endpoint: Optional[str] = None
    ):
        self.account_name = account_name or Config.azure_storage_account()
        self.account_key = account_key or Config.azure_storage_key()
        self.endpoint = endpoint or Config.azurite_endpoint()

        connection_string = (
            f"DefaultEndpointsProtocol=http;"
            f"AccountName={self.account_name};"
            f"AccountKey={self.account_key};"
            f"BlobEndpoint={self.endpoint}/"
        )

        try:
            self.client = BlobServiceClient.from_connection_string(connection_string)
            logger.info(f"Connected to Azurite at {self.endpoint}")
        except AzureError as e:
            raise StorageException(f"Failed to connect to Azurite: {str(e)}")

    def create_container(self, container_name: str) -> ContainerClient:
        """Create a blob container if it doesn't exist"""
        try:
            container_client = self.client.get_container_client(container_name)
            try:
                container_client.get_container_properties()
                logger.info(f"Container '{container_name}' already exists")
            except AzureError:
                self.client.create_container(name=container_name)
                logger.info(f"Created container '{container_name}'")
            return container_client
        except AzureError as e:
            raise StorageException(f"Failed to create container '{container_name}': {str(e)}")

    def list_containers(self) -> List[str]:
        """List all containers in the account"""
        try:
            return [c['name'] for c in self.client.list_containers()]
        except AzureError as e:
            raise StorageException(f"Failed to list containers: {str(e)}")

    def upload_blob(
        self,
        container_name: str,
        blob_name: str,
        data: bytes,
        overwrite: bool = False
    ) -> None:
        """Upload data to a blob"""
        try:
            container_client = self.client.get_container_client(container_name)
            container_client.upload_blob(name=blob_name, data=data, overwrite=overwrite)
            logger.info(f"Uploaded blob '{blob_name}' to container '{container_name}'")
        except AzureError as e:
            raise StorageException(
                f"Failed to upload blob '{blob_name}' to container '{container_name}': {str(e)}"
            )

    def upload_file(
        self,
        container_name: str,
        blob_name: str,
        file_path: str,
        overwrite: bool = False
    ) -> None:
        """Upload a file to a blob"""
        try:
            with open(file_path, 'rb') as data:
                self.upload_blob(container_name, blob_name, data.read(), overwrite)
            logger.info(f"Uploaded file '{file_path}' to blob '{blob_name}'")
        except (AzureError, IOError) as e:
            raise StorageException(
                f"Failed to upload file '{file_path}': {str(e)}"
            )

    def download_blob(self, container_name: str, blob_name: str) -> bytes:
        """Download a blob"""
        try:
            container_client = self.client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            return blob_client.download_blob().readall()
        except AzureError as e:
            raise StorageException(
                f"Failed to download blob '{blob_name}' from container '{container_name}': {str(e)}"
            )

    def list_blobs(self, container_name: str, prefix: str = '') -> List[str]:
        """List blobs in a container"""
        try:
            container_client = self.client.get_container_client(container_name)
            return [b['name'] for b in container_client.list_blobs(name_starts_with=prefix)]
        except AzureError as e:
            raise StorageException(
                f"Failed to list blobs in container '{container_name}': {str(e)}"
            )

    def delete_blob(self, container_name: str, blob_name: str) -> None:
        """Delete a blob"""
        try:
            container_client = self.client.get_container_client(container_name)
            container_client.delete_blob(blob_name)
            logger.info(f"Deleted blob '{blob_name}' from container '{container_name}'")
        except AzureError as e:
            raise StorageException(
                f"Failed to delete blob '{blob_name}': {str(e)}"
            )

    def blob_exists(self, container_name: str, blob_name: str) -> bool:
        """Check if a blob exists"""
        try:
            container_client = self.client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.get_blob_properties()
            return True
        except AzureError:
            return False

    def get_blob_size(self, container_name: str, blob_name: str) -> int:
        """Get the size of a blob in bytes"""
        try:
            container_client = self.client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            return blob_client.get_blob_properties().size
        except AzureError as e:
            raise StorageException(
                f"Failed to get blob size for '{blob_name}': {str(e)}"
            )

    def health_check(self) -> bool:
        """Check if storage is accessible"""
        try:
            self.client.get_account_information()
            return True
        except AzureError:
            return False
