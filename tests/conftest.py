import pytest
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.common import AzuriteStorageClient
from services.data_factory.database import DatabaseManager


@pytest.fixture(scope='session')
def storage_client():
    """Fixture for storage client (session scope)"""
    return AzuriteStorageClient()


@pytest.fixture(scope='session')
def database_manager():
    """Fixture for database manager (session scope)"""
    db_url = os.getenv(
        'DATABASE_URL',
        'postgresql://df_user:postgres@postgres:5432/data_factory'
    )
    return DatabaseManager(db_url)


@pytest.fixture
def clean_test_container(storage_client):
    """Fixture that provides a clean test container"""
    container_name = 'test-container'
    storage_client.create_container(container_name)

    yield container_name

    try:
        blobs = storage_client.list_blobs(container_name)
        for blob in blobs:
            storage_client.delete_blob(container_name, blob)
        storage_client.client.delete_container(container_name)
    except Exception:
        pass


@pytest.fixture
def sample_data():
    """Fixture that provides sample test data"""
    return {
        'csv_data': b'id,name,value\n1,test,100\n2,test2,200\n',
        'json_data': b'{"id": 1, "name": "test"}',
        'text_data': b'Hello, World!'
    }
