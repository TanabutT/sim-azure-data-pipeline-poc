import logging
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql import functions as F
from .base import Transformation

logger = logging.getLogger(__name__)


class AggregationTransformation(Transformation):
    """Aggregate data by key columns"""

    def __init__(self, spark: SparkSession, name: str, group_by_cols: list, agg_col: str = None):
        super().__init__(spark, name)
        self.group_by_cols = group_by_cols
        self.agg_col = agg_col

    def execute(self, input_df: DataFrame) -> DataFrame:
        """Aggregate the input dataframe"""

        logger.info(f"[{self.name}] Starting aggregation")
        self.log_stats(input_df, "Input")

        if not self.validate_schema(input_df, self.group_by_cols):
            raise ValueError(f"Missing required columns for aggregation")

        df = input_df.groupBy(*self.group_by_cols)

        if self.agg_col:
            if self.validate_schema(input_df, [self.agg_col]):
                df = df.agg(
                    F.count(F.col(self.agg_col)).alias('count'),
                    F.sum(F.col(self.agg_col)).alias('sum'),
                    F.avg(F.col(self.agg_col)).alias('avg'),
                    F.min(F.col(self.agg_col)).alias('min'),
                    F.max(F.col(self.agg_col)).alias('max')
                )
            else:
                df = df.agg(F.count('*').alias('count'))
        else:
            df = df.agg(F.count('*').alias('count'))

        self.log_stats(df, "Output")
        logger.info(f"[{self.name}] Aggregation completed")

        return df
