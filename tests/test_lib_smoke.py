"""Smoke tests for nb_lib_common, imported from the file Fabric wrote to Git (T016, risk R4)."""
import pytest
from pyspark.sql import types as T

from conftest import extract_code_cells, load_notebook


@pytest.fixture()
def paths_df(spark):
    return spark.createDataFrame([("a", "/f/1.csv"), ("b", "/f/2.csv")], ["x", "path"])


def test_real_notebook_file_imports_without_fallback(nb_lib_common):
    # The evidence for R4: the Fabric-written file compiles as-is, so no cell extraction is needed.
    assert nb_lib_common._loaded_by == "plain"
    assert callable(nb_lib_common.add_lineage_columns)


def test_adds_three_lineage_columns_with_contract_types(nb_lib_common, paths_df):
    out = nb_lib_common.add_lineage_columns(paths_df, "path", "run-1")
    assert out.columns == ["x", "path", "_source_file", "_run_id", "_ingest_ts"]
    types = {f.name: f.dataType for f in out.schema.fields}
    assert types["_source_file"] == T.StringType()
    assert types["_run_id"] == T.StringType()
    assert types["_ingest_ts"] == T.TimestampType()


def test_values_follow_the_source_column_and_run_id(nb_lib_common, paths_df):
    rows = nb_lib_common.add_lineage_columns(paths_df, "path", "run-1").collect()
    assert [r["_source_file"] for r in rows] == ["/f/1.csv", "/f/2.csv"]
    assert {r["_run_id"] for r in rows} == {"run-1"}
    assert all(r["_ingest_ts"] is not None for r in rows)


def test_keeps_original_columns_and_row_count(nb_lib_common, paths_df):
    out = nb_lib_common.add_lineage_columns(paths_df, "path", "run-1")
    assert out.count() == paths_df.count() == 2
    assert paths_df.columns == ["x", "path"]  # the input frame is not changed


def test_missing_source_column_raises_a_clear_error(nb_lib_common, paths_df):
    with pytest.raises(ValueError, match="'nope' is not a column"):
        nb_lib_common.add_lineage_columns(paths_df, "nope", "run-1")


def test_loader_falls_back_to_cell_extract_when_a_magic_line_breaks_python(tmp_path):
    # Not the case today (Fabric writes magics as `# MAGIC` comments), but this keeps the
    # fallback from R4 proven for the day a notebook file does not compile as-is.
    nb = tmp_path / "notebook-content.py"
    nb.write_text(
        "# Fabric notebook source\n\n# METADATA ********************\n\n# META {}\n\n"
        "# CELL ********************\n\n%run something\nVALUE = 41 + 1\n\n"
        "# METADATA ********************\n\n# META {}\n",
        encoding="utf-8",
    )
    module = load_notebook("nb_fallback_demo", path=nb, tmp_dir=tmp_path)
    assert module._loaded_by == "cell-extract"
    assert module.VALUE == 42


def test_extract_code_cells_skips_markers_metadata_and_markdown():
    text = (
        "# Fabric notebook source\n# MARKDOWN ********************\n# MAGIC # title\n"
        "# CELL ********************\na = 1\n# METADATA ********************\n# META {}\n"
    )
    assert extract_code_cells(text).strip() == "a = 1"


def test_loader_rejects_a_file_that_is_not_a_fabric_notebook(tmp_path):
    bad = tmp_path / "x.py"
    bad.write_text("print('hi')\n", encoding="utf-8")
    with pytest.raises(ValueError, match="not a Fabric Git notebook file"):
        load_notebook("x", path=bad)
