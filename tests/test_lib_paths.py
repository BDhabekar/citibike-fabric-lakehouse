"""Tests for nb_lib_common version 1 (T022): paths, exit payload and the two Fabric-only functions.

The pure functions (`landing_dir`, `parse_landing_path`, `exit_payload`) are tested directly.
`get_config` and `table_path` need `notebookutils`, which exists only inside Fabric, so they are
tested against a small stand-in module put into `sys.modules`. That proves the function reads the
right names and builds the right path; it does not prove Fabric's behaviour (that is the test cell
Bharat runs in the workspace).

The contracts under test: `docs/data-contracts.md` §1 (landing paths), `docs/conventions.md` §3
(variable library) and §6 (exit payload).
"""
import json
import re
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
LANDING_SOURCES = [
    "weather_archive",
    "weather_forecast",
    "gbfs_station_information",
    "gbfs_system_regions",
]


# --------------------------------------------------------------------------- landing_dir


@pytest.mark.parametrize("source_id", LANDING_SOURCES)
def test_landing_dir_builds_the_contract_path(nb_lib_common, source_id):
    out = nb_lib_common.landing_dir(source_id, "2026-04-01", "run-1")
    assert out == f"Files/bronze/{source_id}/ingest_date=2026-04-01/run_id=run-1"


@pytest.mark.parametrize(
    "run_id",
    ["manual", "manual-20261103114600", "3f2a9c1e-7b64-4d0a-9a55-0c1d2e3f4a5b", "seed"],
)
def test_landing_dir_accepts_the_run_ids_the_project_uses(nb_lib_common, run_id):
    out = nb_lib_common.landing_dir("weather_archive", "2026-04-01", run_id)
    assert out.endswith(f"/run_id={run_id}")


def test_landing_dir_has_no_trailing_slash_so_callers_add_the_file_name(nb_lib_common):
    assert not nb_lib_common.landing_dir("weather_archive", "2026-04-01", "r1").endswith("/")


@pytest.mark.parametrize("source_id", ["trips", "_staging", "seed", "", "Weather_Archive", "weather archive"])
def test_landing_dir_rejects_a_source_without_the_ingest_date_layout(nb_lib_common, source_id):
    # `trips` lands under month=YYYYMM, so it has no landing_dir; the others are not sources at all.
    with pytest.raises(ValueError, match="source_id"):
        nb_lib_common.landing_dir(source_id, "2026-04-01", "r1")


@pytest.mark.parametrize(
    "ingest_date",
    ["2026-4-1", "20260401", "2026-02-30", "2026-13-01", "", "2026-04-01T00:00:00", "01-04-2026"],
)
def test_landing_dir_rejects_a_date_that_is_not_a_real_yyyy_mm_dd(nb_lib_common, ingest_date):
    with pytest.raises(ValueError, match="ingest_date"):
        nb_lib_common.landing_dir("weather_archive", ingest_date, "r1")


@pytest.mark.parametrize("run_id", ["", "a/b", "run id", "run_id=x", "a=b", "-x", "../x"])
def test_landing_dir_rejects_a_run_id_that_would_break_the_path(nb_lib_common, run_id):
    with pytest.raises(ValueError, match="run_id"):
        nb_lib_common.landing_dir("weather_archive", "2026-04-01", run_id)


# --------------------------------------------------------------------------- parse_landing_path

FULL_PATH = (
    "abfss://ws-citibike-dev@onelake.dfs.fabric.microsoft.com/lh_bronze.Lakehouse/"
    "Files/bronze/gbfs_system_regions/ingest_date=2026-11-03/"
    "run_id=3f2a9c1e-7b64-4d0a-9a55-0c1d2e3f4a5b/system_regions.json"
)


def test_parse_reads_source_date_and_run_id_from_a_relative_file_path(nb_lib_common):
    path = "Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=run-1/weather_archive_2026-04-01_2026-04-30.json"
    assert nb_lib_common.parse_landing_path(path) == ("weather_archive", "2026-04-01", "run-1")


def test_parse_reads_a_full_onelake_path(nb_lib_common):
    # `_metadata.file_path` may be full or relative (open question for T029), so both must work.
    assert nb_lib_common.parse_landing_path(FULL_PATH) == (
        "gbfs_system_regions",
        "2026-11-03",
        "3f2a9c1e-7b64-4d0a-9a55-0c1d2e3f4a5b",
    )


def test_parse_reads_the_local_mount_form_of_a_path(nb_lib_common):
    path = "/lakehouse/default/Files/bronze/weather_forecast/ingest_date=2026-11-03/run_id=manual/weather_forecast_20261103114500.json"
    assert nb_lib_common.parse_landing_path(path) == ("weather_forecast", "2026-11-03", "manual")


@pytest.mark.parametrize("suffix", ["", "/"])
def test_parse_accepts_a_folder_path_with_no_file_name(nb_lib_common, suffix):
    path = "Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=r1" + suffix
    assert nb_lib_common.parse_landing_path(path) == ("weather_archive", "2026-04-01", "r1")


def test_parse_returns_a_tuple_of_three_strings(nb_lib_common):
    out = nb_lib_common.parse_landing_path(FULL_PATH)
    assert isinstance(out, tuple) and len(out) == 3
    assert all(isinstance(part, str) for part in out)


@pytest.mark.parametrize("source_id", LANDING_SOURCES)
@pytest.mark.parametrize("run_id", ["manual-20261103114600", "3f2a9c1e-7b64-4d0a-9a55-0c1d2e3f4a5b"])
def test_parse_undoes_landing_dir(nb_lib_common, source_id, run_id):
    folder = nb_lib_common.landing_dir(source_id, "2026-11-03", run_id)
    assert nb_lib_common.parse_landing_path(folder + "/some_file.json") == (source_id, "2026-11-03", run_id)


@pytest.mark.parametrize(
    "path",
    [
        "",
        "Files/bronze/trips/month=202604/202604-citibike-tripdata.csv",
        "Files/bronze/_staging/trips/month=202604/202604-citibike-tripdata.zip",
        "Files/seed/wmo_weather_codes.csv",
        "Files/bronze/weather_archive/run_id=r1/x.json",
        "Files/bronze/weather_archive/ingest_date=2026-04-01/x.json",
        "Files/bronze/weather_archive/ingest_date=2026-02-30/run_id=r1/x.json",
        "Files/bronze/weather_archive/ingest_date=26-04-01/run_id=r1/x.json",
    ],
)
def test_parse_rejects_a_path_that_is_not_a_landing_path(nb_lib_common, path):
    with pytest.raises(ValueError):
        nb_lib_common.parse_landing_path(path)


# --------------------------------------------------------------------------- exit_payload

CONTRACT_KEYS = [
    "status", "notebook", "run_id", "rows_read", "rows_written", "rows_rejected", "watermark", "dq", "message",
]
DQ_ROW = {
    "table": "trips", "rule": "duration_in_range", "severity": "error",
    "rows_checked": 4512345, "rows_failed": 2401, "threshold_pct": 1.0, "passed": True,
}


def contract_example(nb_lib_common):
    return nb_lib_common.exit_payload(
        notebook="nb_silver_trips", run_id="r1",
        rows_read=4512345, rows_written=4509876, rows_rejected=2469,
        watermark="202609", dq=[DQ_ROW], message="",
    )


def test_exit_payload_returns_a_json_string(nb_lib_common):
    out = contract_example(nb_lib_common)
    assert isinstance(out, str)
    json.loads(out)


def test_exit_payload_matches_the_contract_example(nb_lib_common):
    # docs/conventions.md §6, the example block.
    assert json.loads(contract_example(nb_lib_common)) == {
        "status": "succeeded",
        "notebook": "nb_silver_trips",
        "run_id": "r1",
        "rows_read": 4512345,
        "rows_written": 4509876,
        "rows_rejected": 2469,
        "watermark": "202609",
        "dq": [DQ_ROW],
        "message": "",
    }


def test_exit_payload_keys_come_in_the_contract_order(nb_lib_common):
    assert list(json.loads(contract_example(nb_lib_common))) == CONTRACT_KEYS


def test_exit_payload_defaults_are_null_watermark_empty_dq_empty_message(nb_lib_common):
    out = json.loads(nb_lib_common.exit_payload("nb_x", "r1", 10, 9, 1))
    assert out["watermark"] is None
    assert out["dq"] == []
    assert out["message"] == ""
    assert out["status"] == "succeeded"


def test_exit_payload_takes_its_arguments_in_the_documented_order(nb_lib_common):
    out = json.loads(nb_lib_common.exit_payload("nb_x", "r1", 10, 9, 1, "202604", [DQ_ROW], "ok"))
    assert (out["notebook"], out["run_id"]) == ("nb_x", "r1")
    assert (out["rows_read"], out["rows_written"], out["rows_rejected"]) == (10, 9, 1)
    assert (out["watermark"], out["dq"], out["message"]) == ("202604", [DQ_ROW], "ok")


def test_exit_payload_keeps_counts_as_json_numbers(nb_lib_common):
    out = json.loads(contract_example(nb_lib_common))
    assert all(type(out[k]) is int for k in ("rows_read", "rows_written", "rows_rejected"))


@pytest.mark.parametrize("bad", [-1, 1.5, "5", None, True])
@pytest.mark.parametrize("which", ["rows_read", "rows_written", "rows_rejected"])
def test_exit_payload_rejects_a_count_that_is_not_a_non_negative_int(nb_lib_common, which, bad):
    counts = {"rows_read": 1, "rows_written": 1, "rows_rejected": 0}
    counts[which] = bad
    with pytest.raises(ValueError, match=which):
        nb_lib_common.exit_payload("nb_x", "r1", **counts)


@pytest.mark.parametrize("field", ["notebook", "run_id"])
def test_exit_payload_rejects_an_empty_name_or_run_id(nb_lib_common, field):
    args = {"notebook": "nb_x", "run_id": "r1"}
    args[field] = ""
    with pytest.raises(ValueError, match=field):
        nb_lib_common.exit_payload(rows_read=1, rows_written=1, rows_rejected=0, **args)


def test_exit_payload_rejects_a_watermark_that_is_not_text(nb_lib_common):
    # ctl.watermark stores text (an ISO date or YYYYMM), so 202609 as a number is a bug.
    with pytest.raises(ValueError, match="watermark"):
        nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, watermark=202609)


def test_exit_payload_refuses_json_longer_than_run_log_can_hold(nb_lib_common):
    # ctl.usp_run_end fails when details_json is over 8,000 characters (T021), so fail in the notebook.
    assert len(contract_example(nb_lib_common)) <= 8000
    with pytest.raises(ValueError, match="8000"):
        nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, dq=[DQ_ROW] * 80)


# --------------------------------------------------------------------------- Fabric-only functions

VARIABLES_JSON = REPO_ROOT / "fabric" / "vl_citibike.VariableLibrary" / "variables.json"


class FakeLibrary:
    """Stands in for the object `getLibrary` returns: property, bracket and getVariable access."""

    def __init__(self, values):
        self.__dict__["_values"] = dict(values)

    def __getattr__(self, name):
        try:
            return self.__dict__["_values"][name]
        except KeyError:
            raise AttributeError(name) from None

    def __getitem__(self, name):
        return self._values[name]

    def getVariable(self, name):
        return self._values[name]


def make_fake_notebookutils(values, workspace_name="ws-citibike-test"):
    reference = re.compile(r"^\$\(/\*\*/vl_citibike/([A-Za-z0-9_]+)\)$")

    def get(ref):
        match = reference.match(ref)
        if not match:
            raise KeyError(ref)
        return values[match.group(1)]

    def get_library(name):
        assert name == "vl_citibike", f"unexpected library {name!r}"
        return FakeLibrary(values)

    return types.SimpleNamespace(
        variableLibrary=types.SimpleNamespace(get=get, getLibrary=get_library),
        runtime=types.SimpleNamespace(context={
            "currentWorkspaceName": workspace_name,
            "currentWorkspaceId": "00000000-0000-0000-0000-000000000000",
            "defaultLakehouseName": None,
        }),
    )


def test_config_variable_names_match_the_library_definition_in_git(nb_lib_common):
    # Catches drift: a variable added to vl_citibike but not to the library's list (or the reverse).
    in_git = [v["name"] for v in json.loads(VARIABLES_JSON.read_text(encoding="utf-8"))["variables"]]
    assert sorted(nb_lib_common.CONFIG_VARIABLES) == sorted(in_git)
    assert len(in_git) == 12


def test_get_config_returns_every_variable_by_name(nb_lib_common, monkeypatch):
    values = {name: f"value-of-{name}" for name in nb_lib_common.CONFIG_VARIABLES}
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils(values))
    cfg = nb_lib_common.get_config()
    assert isinstance(cfg, dict)
    assert cfg == values


def test_get_config_reads_the_library_when_called_not_when_imported(nb_lib_common, monkeypatch):
    first = {name: "a" for name in nb_lib_common.CONFIG_VARIABLES}
    second = {name: "b" for name in nb_lib_common.CONFIG_VARIABLES}
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils(first))
    assert set(nb_lib_common.get_config().values()) == {"a"}
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils(second))
    assert set(nb_lib_common.get_config().values()) == {"b"}


@pytest.mark.parametrize("lakehouse", ["lh_bronze", "lh_silver"])
def test_table_path_builds_the_onelake_path_in_the_current_workspace(nb_lib_common, monkeypatch, lakehouse):
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils({}, "ws-citibike-test"))
    assert nb_lib_common.table_path(lakehouse, "trips") == (
        f"abfss://ws-citibike-test@onelake.dfs.fabric.microsoft.com/{lakehouse}.Lakehouse/Tables/trips"
    )


def test_table_path_follows_the_workspace_it_runs_in(nb_lib_common, monkeypatch):
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils({}, "ws-citibike-prod"))
    assert "@onelake" in nb_lib_common.table_path("lh_silver", "weather_hourly")
    assert nb_lib_common.table_path("lh_silver", "weather_hourly").startswith("abfss://ws-citibike-prod@")


@pytest.mark.parametrize("lakehouse", ["wh_gold", "lh_gold", "", "lh_bronze.Lakehouse"])
def test_table_path_rejects_a_lakehouse_that_is_not_bronze_or_silver(nb_lib_common, monkeypatch, lakehouse):
    # A bare module has no `runtime`, so touching it would raise AttributeError and fail this test:
    # the arguments must be checked before Fabric is asked anything.
    monkeypatch.setitem(sys.modules, "notebookutils", types.ModuleType("notebookutils"))
    with pytest.raises(ValueError, match="lakehouse"):
        nb_lib_common.table_path(lakehouse, "trips")


@pytest.mark.parametrize("table", ["", "Trips", "a/b", "../x", "my table", "1trips", "trips.delta"])
def test_table_path_rejects_a_table_name_that_would_leave_the_tables_folder(nb_lib_common, monkeypatch, table):
    monkeypatch.setitem(sys.modules, "notebookutils", types.ModuleType("notebookutils"))
    with pytest.raises(ValueError, match="table"):
        nb_lib_common.table_path("lh_bronze", table)


# --------------------------------------------------------------------------- edge and security cases
def test_import_does_not_touch_notebookutils(nb_lib_common):
    assert "notebookutils" not in sys.modules

@pytest.mark.parametrize("path", [
    "xFiles/bronze/weather_archive/ingest_date=2026-04-01/run_id=r1/f.json",
    "Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=r1/Files/bronze/weather_forecast/ingest_date=2026-04-02/run_id=r2/f.json",
    "Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=../f.json",
    "Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=r1x\n",
    "Files/bronze/weather_archive/ingest_date=٢٠٢٦-٠٤-٠١/run_id=r1/f.json",
    "Files/bronze/trips/ingest_date=2026-04-01/run_id=r1/f.json",
    None, 42, b"Files/bronze/weather_archive/ingest_date=2026-04-01/run_id=r1",
])
def test_parse_refuses_tricky_paths(nb_lib_common, path):
    with pytest.raises(ValueError):
        nb_lib_common.parse_landing_path(path)

def test_parse_error_message_is_cut_short(nb_lib_common):
    try: nb_lib_common.parse_landing_path("x" * 10000)
    except ValueError as e: assert len(str(e)) < 400

@pytest.mark.parametrize("run_id", ["r" * 129, "ok\n", " r1", "r1 ", "ру1"])
def test_landing_dir_refuses_more_run_ids(nb_lib_common, run_id):
    with pytest.raises(ValueError, match="run_id"):
        nb_lib_common.landing_dir("weather_archive", "2026-04-01", run_id)

def test_landing_dir_accepts_128_char_run_id(nb_lib_common):
    nb_lib_common.landing_dir("weather_archive", "2026-04-01", "r" * 128)

@pytest.mark.parametrize("ingest_date", ["٢٠٢٦-٠٤-٠١", None, 20260401, "2026-04-01\n", "0000-01-01"])
def test_landing_dir_refuses_more_dates(nb_lib_common, ingest_date):
    with pytest.raises(ValueError, match="ingest_date"):
        nb_lib_common.landing_dir("weather_archive", ingest_date, "r1")

def test_leap_day_is_real(nb_lib_common):
    assert nb_lib_common.landing_dir("weather_archive", "2028-02-29", "r1").endswith("run_id=r1")
    with pytest.raises(ValueError, match="ingest_date"):
        nb_lib_common.landing_dir("weather_archive", "2026-02-29", "r1")

@pytest.mark.parametrize("dq", [
    [{"threshold_pct": float("nan")}], [{"x": float("inf")}], [{"x": object()}],
    "not a list", [1, 2], {"rule": "x"},
])
def test_exit_payload_refuses_bad_dq(nb_lib_common, dq):
    with pytest.raises(ValueError, match="dq"):
        nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, dq=dq)

def test_exit_payload_accepts_a_tuple_of_dq_rows(nb_lib_common):
    assert json.loads(nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, dq=(DQ_ROW,)))["dq"] == [DQ_ROW]

@pytest.mark.parametrize("bad", [{"message": 5}, {"notebook": "   "}, {"notebook": None}, {"run_id": "a/b"}, {"run_id": None}])
def test_exit_payload_refuses_more_bad_fields(nb_lib_common, bad):
    args = dict(notebook="nb_x", run_id="r1", rows_read=1, rows_written=1, rows_rejected=0)
    args.update(bad)
    with pytest.raises(ValueError, match=next(iter(bad))):
        nb_lib_common.exit_payload(**args)

def test_exit_payload_message_injection_stays_inside_the_string(nb_lib_common):
    msg = '", "status": "failed", "x": "'
    out = json.loads(nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, message=msg))
    assert out["status"] == "succeeded" and out["message"] == msg

def test_exit_payload_just_under_the_limit_passes(nb_lib_common):
    base = len(nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0))
    nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, message="a" * (8000 - base))
    with pytest.raises(ValueError, match="8000"):
        nb_lib_common.exit_payload("nb_x", "r1", 1, 1, 0, message="a" * (8001 - base))

def test_get_config_reports_every_missing_variable_without_values(nb_lib_common, monkeypatch):
    values = {n: "SECRET-VALUE" for n in nb_lib_common.CONFIG_VARIABLES[:10]}
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils(values))
    with pytest.raises(RuntimeError) as info:
        nb_lib_common.get_config()
    text = str(info.value)
    assert "weather_backfill_start" in text and "dq_max_reject_pct" in text
    assert "SECRET-VALUE" not in text

@pytest.mark.parametrize("ws", ["ws citibike", "ws/../other", "a@b", "", None])
def test_table_path_refuses_a_workspace_name_that_breaks_the_url(nb_lib_common, monkeypatch, ws):
    monkeypatch.setitem(sys.modules, "notebookutils", make_fake_notebookutils({}, ws))
    with pytest.raises(RuntimeError, match="workspace"):
        nb_lib_common.table_path("lh_bronze", "trips")

@pytest.mark.parametrize("table", ["t" * 129, None, "trips\n", "tr-ips"])
def test_table_path_refuses_more_tables(nb_lib_common, monkeypatch, table):
    monkeypatch.setitem(sys.modules, "notebookutils", types.ModuleType("notebookutils"))
    with pytest.raises(ValueError, match="table"):
        nb_lib_common.table_path("lh_bronze", table)

@pytest.mark.parametrize("lh", [None, ["lh_bronze"], "LH_BRONZE"])
def test_table_path_refuses_more_lakehouses(nb_lib_common, monkeypatch, lh):
    monkeypatch.setitem(sys.modules, "notebookutils", types.ModuleType("notebookutils"))
    with pytest.raises(ValueError, match="lakehouse"):
        nb_lib_common.table_path(lh, "trips")
