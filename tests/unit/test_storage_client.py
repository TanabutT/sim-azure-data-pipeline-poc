import pytest
from services.common import AzuriteStorageClient, StorageException


@pytest.fixture
def storage_client():
    """Fixture for storage client"""
    return AzuriteStorageClient()


class TestAzuriteStorageClient:
    """Test cases for AzuriteStorageClient"""

    def test_health_check(self, storage_client):
        """Test health check"""
        assert storage_client.health_check() is True

    def test_create_container(self, storage_client):
        """Test container creation"""
        container = storage_client.create_container('test-container')
        assert container is not None
        storage_client.client.delete_container('test-container')

    def test_list_containers(self, storage_client):
        """Test listing containers"""
        containers = storage_client.list_containers()
        assert isinstance(containers, list)

    def test_upload_and_download_blob(self, storage_client):
        """Test blob upload and download"""
        container_name = 'test-container'
        blob_name = 'test-blob.txt'
        test_data = b'Hello, World!'

        storage_client.create_container(container_name)

        storage_client.upload_blob(container_name, blob_name, test_data)

        downloaded = storage_client.download_blob(container_name, blob_name)
        assert downloaded == test_data

        storage_client.delete_blob(container_name, blob_name)
        storage_client.client.delete_container(container_name)

    def test_blob_exists(self, storage_client):
        """Test blob existence check"""
        container_name = 'test-container'
        blob_name = 'test-blob.txt'
        test_data = b'Test'

        storage_client.create_container(container_name)
        storage_client.upload_blob(container_name, blob_name, test_data)

        assert storage_client.blob_exists(container_name, blob_name) is True
        assert storage_client.blob_exists(container_name, 'nonexistent') is False

        storage_client.delete_blob(container_name, blob_name)
        storage_client.client.delete_container(container_name)

    def test_list_blobs(self, storage_client):
        """Test listing blobs in a container"""
        container_name = 'test-container'

        storage_client.create_container(container_name)
        storage_client.upload_blob(container_name, 'blob1.txt', b'Data1')
        storage_client.upload_blob(container_name, 'blob2.txt', b'Data2')

        blobs = storage_client.list_blobs(container_name)
        assert len(blobs) == 2

        storage_client.delete_blob(container_name, 'blob1.txt')
        storage_client.delete_blob(container_name, 'blob2.txt')
        storage_client.client.delete_container(container_name)
