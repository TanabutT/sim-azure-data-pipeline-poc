#!/usr/bin/env python3
"""Verify the entire system setup"""

import sys
import logging
import requests
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.common import AzuriteStorageClient, Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_service(name: str, url: str, timeout: int = 5) -> bool:
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        logger.info(f"✓ {name}: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        logger.error(f"✗ {name}: Connection refused")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ {name}: Request timeout")
        return False
    except Exception as e:
        logger.error(f"✗ {name}: {e}")
        return False


def check_azurite():
    """Check Azurite storage"""
    logger.info("\nChecking Azurite Storage...")

    try:
        client = AzuriteStorageClient()

        if not client.health_check():
            logger.error("✗ Azurite health check failed")
            return False

        containers = client.list_containers()
        logger.info(f"✓ Found containers: {', '.join(containers)}")

        return True
    except Exception as e:
        logger.error(f"✗ Azurite check failed: {e}")
        return False


def check_postgresql():
    """Check PostgreSQL database"""
    logger.info("\nChecking PostgreSQL Database...")

    try:
        import psycopg2
        from services.data_factory.database import DatabaseManager

        db_manager = DatabaseManager(Config.database_url())
        pipelines = db_manager.list_pipelines()

        logger.info(f"✓ Database connected (pipelines: {len(pipelines)})")
        return True
    except ImportError:
        logger.error("✗ psycopg2 not installed")
        return False
    except Exception as e:
        logger.error(f"✗ Database check failed: {e}")
        return False


def check_spark():
    """Check Spark/Jupyter"""
    logger.info("\nChecking Spark/Jupyter...")

    if not check_service("Jupyter Lab", "http://localhost:8888/api", timeout=10):
        return False

    logger.info("✓ Spark/Jupyter is accessible")
    return True


def check_data_factory_api():
    """Check Data Factory API"""
    logger.info("\nChecking Data Factory API...")

    if not check_service("Data Factory API", "http://localhost:5000/health"):
        return False

    try:
        response = requests.get("http://localhost:5000/api/pipelines", timeout=5)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"✓ API responded with {data.get('count', 0)} pipelines")
            return True
        else:
            logger.error(f"✗ API returned status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"✗ API check failed: {e}")
        return False


def print_summary(results: dict):
    """Print verification summary"""
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICATION SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{name:.<40} {status}")

    logger.info("-" * 60)

    if passed == total:
        logger.info(f"✓ All checks passed ({passed}/{total})")
        logger.info("\nSetup is ready for use!")
        logger.info("\nAccess points:")
        logger.info("  - Jupyter Lab: http://localhost:8888")
        logger.info("  - Data Factory API: http://localhost:5000/docs")
        logger.info("  - Azurite Storage: http://localhost:10000")
        logger.info("  - PostgreSQL: localhost:5432")
        return True
    else:
        logger.error(f"✗ {total - passed} check(s) failed ({passed}/{total})")
        return False


def main():
    """Main verification sequence"""
    logger.info("=" * 60)
    logger.info(f"System Verification - {datetime.now().isoformat()}")
    logger.info("=" * 60)

    results = {
        "Azurite Storage": check_azurite(),
        "PostgreSQL Database": check_postgresql(),
        "Spark/Jupyter": check_spark(),
        "Data Factory API": check_data_factory_api(),
    }

    success = print_summary(results)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
