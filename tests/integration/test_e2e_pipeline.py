import pytest
from services.common import AzuriteStorageClient


class TestEndToEndPipeline:
    """End-to-end pipeline tests"""

    def test_data_flow_raw_to_curated(self, clean_test_container, sample_data):
        """Test data flow from raw to curated zone"""
        client = AzuriteStorageClient()

        client.create_container('raw')
        client.create_container('curated')

        client.upload_blob('raw', 'inbound/input.csv', sample_data['csv_data'])

        data = client.download_blob('raw', 'inbound/input.csv')
        assert data == sample_data['csv_data']

        client.upload_blob('curated', 'transformed/output.csv', data, overwrite=True)

        output = client.download_blob('curated', 'transformed/output.csv')
        assert output == sample_data['csv_data']

        client.client.delete_container('raw')
        client.client.delete_container('curated')

    def test_copy_activity_simulation(self, sample_data):
        """Test copy activity simulation"""
        client = AzuriteStorageClient()

        source_container = 'source'
        sink_container = 'sink'
        blob_name = 'data.txt'

        client.create_container(source_container)
        client.create_container(sink_container)

        client.upload_blob(source_container, blob_name, sample_data['text_data'])

        source_data = client.download_blob(source_container, blob_name)
        client.upload_blob(sink_container, blob_name, source_data, overwrite=True)

        sink_data = client.download_blob(sink_container, blob_name)

        assert sink_data == sample_data['text_data']

        client.client.delete_container(source_container)
        client.client.delete_container(sink_container)

    def test_multiple_file_transfer(self, sample_data):
        """Test transferring multiple files"""
        client = AzuriteStorageClient()

        source_container = 'multi_source'
        sink_container = 'multi_sink'

        client.create_container(source_container)
        client.create_container(sink_container)

        files = {
            'file1.txt': sample_data['text_data'],
            'file2.csv': sample_data['csv_data'],
            'file3.json': sample_data['json_data']
        }

        for filename, data in files.items():
            client.upload_blob(source_container, filename, data)

        source_files = client.list_blobs(source_container)
        assert len(source_files) == 3

        for filename in source_files:
            data = client.download_blob(source_container, filename)
            client.upload_blob(sink_container, filename, data, overwrite=True)

        sink_files = client.list_blobs(sink_container)
        assert len(sink_files) == 3

        client.client.delete_container(source_container)
        client.client.delete_container(sink_container)
