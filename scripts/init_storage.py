#!/usr/bin/env python3
"""Initialize storage containers and sample data"""

import sys
import logging
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.common import AzuriteStorageClient, Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def wait_for_storage(max_retries=30, retry_delay=2):
    """Wait for Azurite to be available"""
    logger.info("Waiting for Azurite storage to be available...")

    for attempt in range(max_retries):
        try:
            client = AzuriteStorageClient()
            if client.health_check():
                logger.info("✓ Azurite is available")
                return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.info(f"  Attempt {attempt + 1}/{max_retries} - waiting {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                logger.error(f"✗ Azurite not available after {max_retries} attempts")
                return False

    return False


def create_containers():
    """Create required storage containers"""
    logger.info("\nCreating storage containers...")

    client = AzuriteStorageClient()

    containers = ['raw', 'curated', 'output']

    for container in containers:
        try:
            client.create_container(container)
            logger.info(f"✓ Created container: {container}")
        except Exception as e:
            logger.error(f"✗ Failed to create container '{container}': {e}")
            return False

    return True


def create_folder_structure():
    """Create folder structure in containers"""
    logger.info("\nCreating folder structure...")

    client = AzuriteStorageClient()

    folders = {
        'raw': ['inbound/', 'staging/'],
        'curated': ['transformed_data/', 'metadata/'],
        'output': ['reports/', 'archive/']
    }

    for container, paths in folders.items():
        for path in paths:
            try:
                folder_marker = path + '.gitkeep'
                client.upload_blob(container, folder_marker, b'', overwrite=True)
                logger.info(f"✓ Created folder: {container}/{path}")
            except Exception as e:
                logger.warning(f"  Note: {e}")

    return True


def upload_sample_data():
    """Upload sample data files"""
    logger.info("\nUploading sample data...")

    client = AzuriteStorageClient()
    data_dir = Path(__file__).parent.parent / 'data' / 'sample'

    if not data_dir.exists():
        logger.warning(f"  Sample data directory not found: {data_dir}")
        return True

    for file_path in data_dir.glob('*'):
        if file_path.is_file():
            try:
                blob_name = f"inbound/{file_path.name}"
                with open(file_path, 'rb') as f:
                    client.upload_blob('raw', blob_name, f.read(), overwrite=True)
                logger.info(f"✓ Uploaded: {blob_name}")
            except Exception as e:
                logger.error(f"✗ Failed to upload {file_path.name}: {e}")
                return False

    return True


def verify_storage():
    """Verify storage is properly initialized"""
    logger.info("\nVerifying storage setup...")

    client = AzuriteStorageClient()

    try:
        containers = client.list_containers()
        logger.info(f"✓ Found {len(containers)} containers: {', '.join(containers)}")

        for container in containers:
            blobs = client.list_blobs(container)
            if blobs:
                logger.info(f"✓ Container '{container}' has {len(blobs)} items")

        return True
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        return False


def main():
    """Main initialization sequence"""
    logger.info("=" * 60)
    logger.info("Storage Initialization")
    logger.info("=" * 60)

    if not wait_for_storage():
        logger.error("Failed to connect to Azurite storage")
        sys.exit(1)

    if not create_containers():
        logger.error("Failed to create containers")
        sys.exit(1)

    if not create_folder_structure():
        logger.warning("Some folders could not be created")

    if not upload_sample_data():
        logger.warning("Some sample data could not be uploaded")

    if not verify_storage():
        logger.error("Storage verification failed")
        sys.exit(1)

    logger.info("\n" + "=" * 60)
    logger.info("✓ Storage initialization completed successfully!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
