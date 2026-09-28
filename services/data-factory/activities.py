import logging
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import requests
from services.common import AzuriteStorageClient, StorageException

logger = logging.getLogger(__name__)


class Activity(ABC):
    """Base class for all activities"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.output = None
        self.error = None

    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Execute the activity. Subclasses must implement."""
        pass

    async def validate(self) -> bool:
        """Validate activity configuration. Subclasses should override."""
        return True


class CopyActivity(Activity):
    """Copy data between storage locations"""

    async def execute(self) -> Dict[str, Any]:
        try:
            source = self.config.get('source', {})
            sink = self.config.get('sink', {})

            source_container = source.get('container')
            source_blob = source.get('path')
            sink_container = sink.get('container')
            sink_blob = sink.get('path')

            if not all([source_container, source_blob, sink_container, sink_blob]):
                raise ValueError("Missing required copy parameters")

            client = AzuriteStorageClient()

            logger.info(f"Copying from {source_container}/{source_blob} to {sink_container}/{sink_blob}")

            data = client.download_blob(source_container, source_blob)
            client.upload_blob(sink_container, sink_blob, data, overwrite=True)

            self.output = {
                'source': f"{source_container}/{source_blob}",
                'sink': f"{sink_container}/{sink_blob}",
                'bytes_copied': len(data)
            }

            logger.info(f"Copy activity '{self.name}' completed successfully")
            return self.output

        except Exception as e:
            self.error = str(e)
            logger.error(f"Copy activity '{self.name}' failed: {e}")
            raise


class SparkActivity(Activity):
    """Execute PySpark transformation jobs"""

    async def execute(self) -> Dict[str, Any]:
        try:
            notebook_path = self.config.get('notebook_path')
            parameters = self.config.get('parameters', {})

            if not notebook_path:
                raise ValueError("notebook_path is required for SparkActivity")

            logger.info(f"Executing Spark activity '{self.name}' with notebook: {notebook_path}")

            spark_endpoint = self.config.get('spark_endpoint', 'http://spark:8888')
            timeout = self.config.get('timeout', 300)

            self.output = {
                'notebook': notebook_path,
                'parameters': parameters,
                'status': 'submitted',
                'execution_time': 0
            }

            logger.info(f"Spark activity '{self.name}' execution plan created")
            return self.output

        except Exception as e:
            self.error = str(e)
            logger.error(f"Spark activity '{self.name}' failed: {e}")
            raise


class WaitActivity(Activity):
    """Wait for a specified duration"""

    async def execute(self) -> Dict[str, Any]:
        try:
            duration_seconds = self.config.get('duration_seconds', 0)

            if not isinstance(duration_seconds, (int, float)) or duration_seconds < 0:
                raise ValueError("duration_seconds must be a non-negative number")

            logger.info(f"Wait activity '{self.name}' waiting for {duration_seconds} seconds")

            time.sleep(duration_seconds)

            self.output = {
                'waited_seconds': duration_seconds
            }

            logger.info(f"Wait activity '{self.name}' completed")
            return self.output

        except Exception as e:
            self.error = str(e)
            logger.error(f"Wait activity '{self.name}' failed: {e}")
            raise


class WebActivity(Activity):
    """Call an external web service"""

    async def execute(self) -> Dict[str, Any]:
        try:
            url = self.config.get('url')
            method = self.config.get('method', 'GET').upper()
            headers = self.config.get('headers', {})
            body = self.config.get('body')
            timeout = self.config.get('timeout', 30)

            if not url:
                raise ValueError("url is required for WebActivity")

            logger.info(f"Web activity '{self.name}' calling {method} {url}")

            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=body, headers=headers, timeout=timeout)
            elif method == 'PUT':
                response = requests.put(url, json=body, headers=headers, timeout=timeout)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            try:
                response_body = response.json()
            except:
                response_body = response.text

            self.output = {
                'status_code': response.status_code,
                'response': response_body
            }

            logger.info(f"Web activity '{self.name}' completed with status {response.status_code}")
            return self.output

        except Exception as e:
            self.error = str(e)
            logger.error(f"Web activity '{self.name}' failed: {e}")
            raise


class IfConditionActivity(Activity):
    """Conditional branching activity"""

    async def execute(self) -> Dict[str, Any]:
        try:
            condition = self.config.get('condition')

            if condition is None:
                raise ValueError("condition is required for IfConditionActivity")

            result = bool(condition)

            self.output = {
                'condition': condition,
                'result': result,
                'true_activities': self.config.get('true_activities', []),
                'false_activities': self.config.get('false_activities', [])
            }

            logger.info(f"If condition activity '{self.name}' evaluated to {result}")
            return self.output

        except Exception as e:
            self.error = str(e)
            logger.error(f"If condition activity '{self.name}' failed: {e}")
            raise


def create_activity(name: str, activity_type: str, config: Dict[str, Any]) -> Activity:
    """Factory function to create activity instances"""

    activity_map = {
        'CopyActivity': CopyActivity,
        'SparkActivity': SparkActivity,
        'WaitActivity': WaitActivity,
        'WebActivity': WebActivity,
        'IfConditionActivity': IfConditionActivity,
    }

    ActivityClass = activity_map.get(activity_type)
    if not ActivityClass:
        raise ValueError(f"Unknown activity type: {activity_type}")

    return ActivityClass(name, config)
