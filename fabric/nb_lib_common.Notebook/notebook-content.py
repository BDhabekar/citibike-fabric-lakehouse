# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

from pyspark.sql import DataFrame, functions as F


def add_lineage_columns(df: DataFrame, source_file_col: str, run_id: str) -> DataFrame:
    """Add the three lineage columns of docs/data-contracts.md to a DataFrame.

    source_file_col: name of the column that already holds the file path.
    Returns df plus _source_file (string), _run_id (string), _ingest_ts (timestamp).
    """
    if source_file_col not in df.columns:
        raise ValueError(f"source_file_col '{source_file_col}' is not a column of the DataFrame")
    return (
        df.withColumn("_source_file", F.col(source_file_col).cast("string"))
        .withColumn("_run_id", F.lit(run_id).cast("string"))
        .withColumn("_ingest_ts", F.current_timestamp())
    )

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
