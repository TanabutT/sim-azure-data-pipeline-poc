import logging
import os
from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

logger = logging.getLogger(__name__)


class SparkSessionFactory:
    """Factory for creating and configuring Spark sessions"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.session = None

    @staticmethod
    def create_session(app_name: str = "DataPipeline") -> SparkSession:
        """Create and configure a Spark session with Delta Lake support"""

        azurite_endpoint = os.getenv('AZURITE_ENDPOINT', 'http://azurite:10000')
        azure_account = os.getenv('AZURE_STORAGE_ACCOUNT', 'devstoreaccount1')
        azure_key = os.getenv('AZURE_STORAGE_KEY', 'sharedsecretkey1')

        builder = (
            SparkSession.builder
            .appName(app_name)
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .config("spark.sql.warehouse.dir", "/home/jovyan/spark_warehouse")
            .config("fs.azure.storage.type", "block")
            .config(f"fs.azure.account.auth.type.{azure_account}.dfs.core.windows.net", "SharedKey")
            .config(f"fs.azure.account.key.{azure_account}.dfs.core.windows.net", azure_key)
        )

        try:
            builder = configure_spark_with_delta_pip(builder)
        except Exception as e:
            logger.warning(f"Delta Lake configuration failed: {e}")

        spark = builder.getOrCreate()
        spark.sparkContext.setLogLevel("INFO")

        logger.info(f"Created Spark session: {app_name}")
        logger.info(f"Spark version: {spark.version}")
        logger.info(f"Azurite endpoint: {azurite_endpoint}")

        return spark

    def get_session(self, app_name: str = "DataPipeline") -> SparkSession:
        """Get or create a Spark session"""
        if self.session is None:
            self.session = self.create_session(app_name)
        return self.session

    def stop_session(self) -> None:
        """Stop the Spark session"""
        if self.session:
            self.session.stop()
            self.session = None
            logger.info("Stopped Spark session")
