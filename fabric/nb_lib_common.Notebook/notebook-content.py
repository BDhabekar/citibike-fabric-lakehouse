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

# CELL ********************

import json
import re
from datetime import datetime

# Sources that land under Files/bronze/<source_id>/ingest_date=YYYY-MM-DD/run_id=<run_id>/
# (docs/data-contracts.md §1). trips is not here: it lands under month=YYYYMM.
LANDING_SOURCES = ("weather_archive", "weather_forecast", "gbfs_station_information", "gbfs_system_regions")

CONFIG_LIBRARY = "vl_citibike"
# Must match fabric/vl_citibike.VariableLibrary/variables.json; a test fails when they drift.
CONFIG_VARIABLES = (
    "env_name", "gbfs_base_url", "weather_archive_url", "weather_forecast_url",
    "weather_latitude", "weather_longitude", "weather_hourly_vars", "trips_base_url",
    "backfill_first_month", "backfill_last_month", "weather_backfill_start", "dq_max_reject_pct",
)

LAKEHOUSES = ("lh_bronze", "lh_silver")
ONELAKE_HOST = "onelake.dfs.fabric.microsoft.com"

# ctl.run_log.details_json is nvarchar(8000); ctl.usp_run_end fails above it (T021).
EXIT_JSON_MAX_CHARS = 8000

# ASCII only: \d would also accept digits from other scripts.
_DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}")
_TABLE_RE = re.compile(r"[a-z][a-z0-9_]{0,127}")
_WORKSPACE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,255}")
# The landing folders, anchored at a path segment so 'xFiles/bronze/...' does not count.
_LANDING_RE = re.compile(r"(?:^|/)Files/bronze/([^/]+)/ingest_date=([^/]+)/run_id=([^/]+)(?=/|$)")


def _preview(value, limit=200):
    """repr() of a value for an error message, cut short so a log never carries a huge string."""
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + "...'"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def _validate_ingest_date(ingest_date):
    if not isinstance(ingest_date, str) or not _DATE_RE.fullmatch(ingest_date):
        raise ValueError(f"ingest_date must be YYYY-MM-DD, got {_preview(ingest_date)}")
    try:
        datetime.strptime(ingest_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"ingest_date is not a real calendar date, got {_preview(ingest_date)}") from None


def _validate_run_id(run_id):
    if not isinstance(run_id, str) or not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            "run_id must be 1-128 letters, digits, '_' or '-', starting with a letter or digit, "
            f"got {_preview(run_id)}"
        )


def _validate_landing_source(source_id):
    if source_id not in LANDING_SOURCES:
        raise ValueError(f"source_id must be one of {LANDING_SOURCES}, got {_preview(source_id)}")


def landing_dir(source_id, ingest_date, run_id):
    """Return 'Files/bronze/<source_id>/ingest_date=<ingest_date>/run_id=<run_id>', no trailing slash.

    The path is relative to the lakehouse root, the form the lakehouse's default mount and
    notebookutils.fs accept. Callers add '/<file name>'.
    ValueError, naming the parameter, when source_id is not in LANDING_SOURCES, ingest_date is not a
    real YYYY-MM-DD date, or run_id has characters a folder name must not carry ('/', '=', spaces, '..').
    """
    _validate_landing_source(source_id)
    _validate_ingest_date(ingest_date)
    _validate_run_id(run_id)
    return f"Files/bronze/{source_id}/ingest_date={ingest_date}/run_id={run_id}"


def parse_landing_path(path):
    """Return (source_id, ingest_date, run_id) from the path of a landed file or folder.

    Accepts a relative path ('Files/bronze/...'), a full abfss:// path and a '/lakehouse/default/...'
    path, with or without a file name or trailing slash. Every part is checked with the same rules
    as landing_dir, so parse_landing_path(landing_dir(s, d, r) + '/f.json') == (s, d, r).
    ValueError when the path has no landing folder, has more than one, or a part fails its check.
    """
    if not isinstance(path, str) or not path:
        raise ValueError(f"path must be a non-empty string, got {_preview(path)}")
    matches = _LANDING_RE.findall(path)
    if not matches:
        raise ValueError(f"not a landing path (no Files/bronze/<source>/ingest_date=/run_id=): {_preview(path)}")
    if len(matches) > 1:
        raise ValueError(f"path holds more than one landing folder: {_preview(path)}")
    source_id, ingest_date, run_id = matches[0]
    _validate_landing_source(source_id)
    _validate_ingest_date(ingest_date)
    _validate_run_id(run_id)
    return (source_id, ingest_date, run_id)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def _validate_count(name, value):
    # bool is a subclass of int in Python, so True would otherwise pass as 1.
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be an int >= 0, got {_preview(value)}")


def exit_payload(notebook, run_id, rows_read, rows_written, rows_rejected, watermark=None, dq=None, message=""):
    """Return the exit JSON of docs/conventions.md §6 as text, keys in contract order.

    A notebook calls notebookutils.notebook.exit(exit_payload(...)) only when it succeeded;
    a failure raises, so status is always "succeeded" here.
    watermark: the new high-water mark as text (an ISO date or YYYYMM), or None.
    dq: a list of rule-result dicts, [] when None. message: short text for the run log.
    ValueError, naming the field, for a wrong type or value; ValueError mentioning the limit when
    the JSON is longer than EXIT_JSON_MAX_CHARS, so the notebook fails, not ctl.usp_run_end.
    Never put secrets or connection strings in message: it is stored in ctl.run_log.
    """
    if not isinstance(notebook, str) or not notebook.strip():
        raise ValueError(f"notebook must be a non-empty string, got {_preview(notebook)}")
    if not isinstance(run_id, str) or not run_id:
        raise ValueError(f"run_id must be a non-empty string, got {_preview(run_id)}")
    _validate_run_id(run_id)
    _validate_count("rows_read", rows_read)
    _validate_count("rows_written", rows_written)
    _validate_count("rows_rejected", rows_rejected)
    if watermark is not None and not isinstance(watermark, str):
        raise ValueError(f"watermark must be text or None, got {_preview(watermark)}")
    if dq is None:
        dq = []
    if not isinstance(dq, (list, tuple)) or not all(isinstance(row, dict) for row in dq):
        raise ValueError(f"dq must be a list of dicts, got {_preview(dq)}")
    if not isinstance(message, str):
        raise ValueError(f"message must be text, got {_preview(message)}")

    payload = {
        "status": "succeeded",
        "notebook": notebook,
        "run_id": run_id,
        "rows_read": rows_read,
        "rows_written": rows_written,
        "rows_rejected": rows_rejected,
        "watermark": watermark,
        "dq": list(dq),
        "message": message,
    }
    try:
        # allow_nan=False: NaN or Infinity in a dq value is not valid JSON and OPENJSON would reject it.
        text = json.dumps(payload, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"dq holds a value that is not plain JSON (str, number, bool, None): {exc}") from None
    if len(text) > EXIT_JSON_MAX_CHARS:
        raise ValueError(
            f"exit payload is {len(text)} characters; ctl.run_log holds {EXIT_JSON_MAX_CHARS}. "
            "Shorten message or log fewer dq rows."
        )
    return text

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

def get_config():
    """Return {name: value} for every name in CONFIG_VARIABLES, read from vl_citibike's active value set.

    Reads the library each call (not at %run time), so a test can stand in for notebookutils.
    RuntimeError listing every variable it could not read; values are never put in the message.
    """
    import notebookutils  # Fabric only; imported here so CI can import this notebook

    config, failed = {}, []
    for name in CONFIG_VARIABLES:
        try:
            config[name] = notebookutils.variableLibrary.get(f"$(/**/{CONFIG_LIBRARY}/{name})")
        except Exception as exc:  # noqa: BLE001 - collect every failure, then raise once
            failed.append(f"{name} ({type(exc).__name__})")
    if failed:
        raise RuntimeError(f"could not read from variable library {CONFIG_LIBRARY}: {', '.join(failed)}")
    return config


def table_path(lakehouse, table):
    """Return abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Tables/<table>.

    The workspace is the one the notebook runs in, so the same code points at dev, test or prod.
    Arguments are checked before Fabric is asked anything. ValueError naming 'lakehouse' or
    'table' for a bad argument; RuntimeError when the workspace name cannot go into a path.
    """
    if lakehouse not in LAKEHOUSES:
        raise ValueError(f"lakehouse must be one of {LAKEHOUSES}, got {_preview(lakehouse)}")
    if not isinstance(table, str) or not _TABLE_RE.fullmatch(table):
        raise ValueError(
            "table must be 1-128 lowercase letters, digits or '_', starting with a letter, "
            f"got {_preview(table)}"
        )
    import notebookutils  # Fabric only

    workspace = notebookutils.runtime.context["currentWorkspaceName"]
    if not isinstance(workspace, str) or not _WORKSPACE_RE.fullmatch(workspace):
        raise RuntimeError(f"workspace name {_preview(workspace)} cannot be used in a OneLake path")
    return f"abfss://{workspace}@{ONELAKE_HOST}/{lakehouse}.Lakehouse/Tables/{table}"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
