import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from .base import Transformation

logger = logging.getLogger(__name__)


class DataCleaner(Transformation):
    """Clean and prepare data for analysis"""

    def execute(self, input_df: DataFrame) -> DataFrame:
        """Clean the input dataframe"""

        logger.info(f"[{self.name}] Starting data cleaning")
        self.log_stats(input_df, "Input")

        df = input_df

        df = df.dropna(how='all')
        logger.info(f"[{self.name}] Dropped empty rows")

        df = df.dropDuplicates()
        logger.info(f"[{self.name}] Removed duplicates")

        for col in df.columns:
            df = df.withColumn(col, F.trim(F.col(col)))
        logger.info(f"[{self.name}] Trimmed whitespace from all columns")

        self.log_stats(df, "Output")
        logger.info(f"[{self.name}] Data cleaning completed")

        return df
