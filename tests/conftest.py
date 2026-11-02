"""Shared test setup: load a Fabric notebook's Git file as a module, and a local Spark session.

Fabric Git integration stores a notebook as `fabric/<name>.Notebook/notebook-content.py`.
Every cell boundary and metadata block in that file is a comment (`# CELL ****`, `# META ...`,
`# MAGIC ...`), so the file is valid Python and a plain import works (risk R4, task T016).

`load_notebook` tries the plain import first. If Python cannot compile the file (for example a
bare `%run` line), it falls back to extracting the code cells into a temporary module. The module
gets `_loaded_by` set to "plain" or "cell-extract" so a test can say which route was used.
"""
import importlib.util
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HEADER = "# Fabric notebook source"
CELL_MARK = re.compile(r"^# CELL \*+\s*$")
BLOCK_MARK = re.compile(r"^# (METADATA|MARKDOWN|CELL) \*+\s*$")


def notebook_file(name: str) -> Path:
    return REPO_ROOT / "fabric" / f"{name}.Notebook" / "notebook-content.py"


def _import_file(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def extract_code_cells(text: str) -> str:
    """Return the code cells of a notebook-content.py as plain Python source.

    Keeps only lines between a `# CELL ****` marker and the next block marker, and drops
    lines that start with `%` or `!` (Jupyter magics that are not valid Python).
    """
    out, in_cell = [], False
    for line in text.splitlines():
        if CELL_MARK.match(line):
            in_cell = True
            continue
        if BLOCK_MARK.match(line):
            in_cell = False
            continue
        if in_cell and not line.lstrip().startswith(("%", "!")):
            out.append(line)
    return "\n".join(out) + "\n"


def load_notebook(name: str, path: Path | None = None, tmp_dir: Path | None = None):
    path = path or notebook_file(name)
    text = path.read_text(encoding="utf-8")
    if not text.startswith(HEADER):
        raise ValueError(f"{path} does not start with '{HEADER}'; not a Fabric Git notebook file")
    try:
        module = _import_file(name, path)
        module._loaded_by = "plain"
        return module
    except SyntaxError:
        if tmp_dir is None:
            raise
        extracted = tmp_dir / f"{name}.py"
        extracted.write_text(extract_code_cells(text), encoding="utf-8")
        module = _import_file(name, extracted)
        module._loaded_by = "cell-extract"
        return module


@pytest.fixture(scope="session")
def spark():
    from pyspark.sql import SparkSession

    session = (
        SparkSession.builder.master("local[1]")
        .appName("citibike-unit-tests")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.sql.session.timeZone", "UTC")  # same as env_citibike (T009)
        .getOrCreate()
    )
    yield session
    session.stop()


@pytest.fixture(scope="session")
def nb_lib_common():
    return load_notebook("nb_lib_common")
