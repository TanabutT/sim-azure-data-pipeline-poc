import logging
from abc import ABC, abstractmethod
from pyspark.sql import SparkSession, DataFrame

logger = logging.getLogger(__name__)


class Transformation(ABC):
    """Base class for all data transformations"""

    def __init__(self, spark: SparkSession, name: str):
        self.spark = spark
        self.name = name

    @abstractmethod
    def execute(self, input_df: DataFrame) -> DataFrame:
        """Execute the transformation. Subclasses must implement."""
        pass

    def log_stats(self, df: DataFrame, stage: str):
        """Log statistics about a dataframe"""
        try:
            row_count = df.count()
            col_count = len(df.columns)
            logger.info(
                f"[{self.name}] {stage}: "
                f"rows={row_count}, columns={col_count}"
            )
        except Exception as e:
            logger.warning(f"Failed to log stats: {e}")

    def validate_schema(self, df: DataFrame, required_columns: list) -> bool:
        """Validate that all required columns exist"""
        missing = set(required_columns) - set(df.columns)
        if missing:
            logger.error(
                f"[{self.name}] Missing required columns: {missing}"
            )
            return False
        return True
