# EP02 · Batch ingestion to bronze (REST, JSON and files)

**Goal.** Every batch source lands untouched in `lh_bronze` Files and becomes a bronze Delta table, driven by control tables and logged per run.
**Done when.** A second run of every ingestion for the same window changes no bronze counts (T031).

## FT06 · Control framework

### US007 · Metadata-driven, logged ingestion
As an operator, I want sources, watermarks and run results in control tables, so that adding a source is a row, not a new pipeline, and every run can be traced.
- `ctl` tables and procedures exist; `nb_lib_common` gives every notebook the same config, paths and exit payload.

#### T020 · Create the `ctl` schema, tables and seed procedure in `wh_gold`
- **Story:** US007
- **ADO:** #36
- **Owner:** Claude writes, Bharat runs
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 2
- **Depends on:** T019
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (ctl), docs/conventions.md §5
**Do**
1. Claude checks the Fabric Warehouse supported-types page and the `CREATE OR ALTER`/`DROP IF EXISTS` support, then writes `sql/ctl/001_ctl_tables.sql` (schema `ctl`, the four tables) and `sql/ctl/002_usp_seed_config.sql` (`ctl.usp_seed_config` inserting the five sources if absent: `weather_archive`, `weather_forecast`, `gbfs_station_information`, `gbfs_system_regions`, `trips`; and a watermark row for `weather_archive` set from a parameter).
2. Bharat runs both in `wh_gold` (New SQL query, paste, Run), then `EXEC ctl.usp_seed_config @weather_start = '2026-04-01';`.
3. Run both scripts a second time: no error, no duplicate rows (idempotency).
4. Commit the workspace (`T020: ctl schema`).
**Acceptance**
- [ ] Four `ctl` tables with the contract's columns and types.
- [ ] `SELECT * FROM ctl.source_config` returns five rows after two runs of the seed.
- [ ] `sql/ctl/*.sql` committed in the repo; the warehouse change committed from the workspace.
**Result:** —

#### T021 · Logging, watermark and window procedures
- **Story:** US007
- **ADO:** #37
- **Owner:** Claude writes, Bharat runs
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 2
- **Depends on:** T020
- **DP-700:** 1.4, 2.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (ctl), docs/conventions.md §5, §6
**Do**
1. Claude writes `sql/ctl/003_logging_procs.sql`:
   - `ctl.usp_run_start @run_id, @parent_run_id, @pipeline_name, @step_name, @environment` (inserts a `started` row)
   - `ctl.usp_run_end @run_id, @step_name, @status, @details_json, @error_message` (updates the row; reads `rows_read`, `rows_written`, `rows_rejected` from `@details_json` with `JSON_VALUE`)
   - `ctl.usp_watermark_set @source_id, @value, @run_id`
   - `ctl.usp_weather_windows @from_date, @to_date` returning one row per calendar-month chunk (`start_date`, `end_date`), built from a numbers list (no recursive CTE)
   - `ctl.usp_month_list @first_month, @last_month` returning one row per `YYYYMM` month in the range (for `pl_backfill`)
2. Bharat runs it, then the three test calls Claude gives (start, end with a sample exit JSON, windows for 2026-04-01 to 2026-07-15).
3. Commit the workspace.
**Acceptance**
- [ ] A started-then-ended test row in `ctl.run_log` with the counts parsed from the JSON.
- [ ] `usp_weather_windows` returns 4 rows for the test range, the last ending 2026-07-15.
- [ ] `usp_month_list '202607', '202609'` returns 3 rows.
- [ ] Test rows deleted afterwards.
**Result:** —

#### T022 · `nb_lib_common` version 1: config, paths, lineage and the exit payload
- **Story:** US007
- **ADO:** #38
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 2
- **Depends on:** T016, T019
- **DP-700:** 1.4
- **Status:** todo
- **Read first:** docs/conventions.md §2, §4, §6; docs/data-contracts.md §1
**Do**
1. Claude gives the function list and their signatures; Bharat writes the bodies in `nb_lib_common` (the notebook from T016):
   - `get_config()` → dict of every `vl_citibike` variable (Fabric-only; uses the syntax proved in T018)
   - `landing_dir(source_id, ingest_date, run_id)` → the contract path
   - `parse_landing_path(path)` → `(source_id, ingest_date, run_id)`
   - `add_lineage_columns(df, run_id)` → adds `_source_file`, `_ingest_ts`, `_run_id`
   - `exit_payload(notebook, run_id, rows_read, rows_written, rows_rejected, watermark=None, dq=None, message="")` → JSON string in the contract shape
   - `table_path(lakehouse, table)` → the table's OneLake path in the current workspace (Fabric-only)
2. Fabric-only imports (`notebookutils`) sit inside the functions that need them, so CI can import the notebook.
3. Claude writes `tests/test_lib_paths.py` for the three pure functions.
4. Commit the workspace; Claude pulls and runs the tests.
**Acceptance**
- [ ] The six functions exist with the given signatures.
- [ ] Path and payload tests pass.
- [ ] `get_config()["env_name"]` returns `dev` in a test cell (cell removed before commit).
**Result:** —

## FT07 · REST and JSON ingestion with pipelines

### US008 · Hourly weather history in bronze
As an analyst, I want every hour of weather since the backfill start, so that demand can be compared with the conditions riders faced.
- Weather JSON lands per run in the contract path; a re-run re-fetches a 7-day overlap and never leaves a gap.

#### T023 · `pl_ingest_weather_archive` with fixed values, one month
- **Story:** US008
- **ADO:** #41
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 2
- **Depends on:** T022
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/sources.md §1, docs/data-contracts.md §1
**Do**
1. New connection: REST, base URL `https://archive-api.open-meteo.com`, authentication Anonymous. Name it `conn_open_meteo_archive`.
2. New pipeline `pl_ingest_weather_archive`. Copy activity `cp_weather_archive`: source REST, relative URL with the April 2026 query from `docs/sources.md` §1 typed in full; sink `lh_bronze` Files, folder `bronze/weather_archive/ingest_date=<today>/run_id=manual-<stamp>/`, file `weather_archive_2026-04-01_2026-04-30.json`, format JSON.
3. Run. Open the file: the `hourly.time` array has 720 entries.
**Acceptance**
- [ ] The file exists in the contract path with 720 hours.
- [ ] The run is green; its duration is in the Result line.
**Result:** —

#### T024 · Parameterise the weather pipeline: watermark, overlap window, monthly chunks, logging
- **Story:** US008
- **ADO:** #42
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 2
- **Depends on:** T021, T023
- **DP-700:** 1.4, 2.1
- **Status:** todo
- **Read first:** docs/conventions.md §1, §3, §6; docs/decisions.md ADR-018
**Do**
1. Parameters: `run_id` (default `manual`), `parent_run_id` (default empty). Library variables: `vl_citibike` (`weather_latitude`, `weather_longitude`, `weather_hourly_vars`, `env_name`).
2. `sp_run_start` → `lkp_watermark` (`SELECT watermark_value FROM ctl.watermark WHERE source_id = 'weather_archive'`).
3. `set_v_from`: watermark minus 7 days (the overlap that catches the archive's late days); `set_v_to`: yesterday (UTC). Claude gives the expression building blocks; Bharat writes the expressions.
4. `lkp_windows`: `EXEC ctl.usp_weather_windows @from_date, @to_date`.
5. `fe_windows` (sequential) → `cp_weather_archive` with the relative URL built from the window and the library variables, and the sink path from `run_id` and the window.
6. `sp_watermark_set` to `v_to` after the loop; `sp_run_end` with a JSON built from the loop count.
7. Run twice. Second run: same windows re-fetched, new files in a new `run_id` folder, watermark unchanged.
**Acceptance**
- [ ] No URL, latitude or date is typed anywhere in the pipeline (all from parameters, the library or lookups).
- [ ] Watermark moved to yesterday; `ctl.run_log` has two started/succeeded pairs.
- [ ] A second run is green and lands files under its own `run_id`.
**Result:** —

### US009 · Station reference data every day
As an analyst, I want a daily snapshot of the station list and regions, so that station history can be built from it.
- Both feeds land daily from one generic copy, driven by `ctl.source_config`.

#### T025 · `pl_ingest_gbfs_reference`, driven by `ctl.source_config`
- **Story:** US009
- **ADO:** #44
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 2
- **Depends on:** T024
- **DP-700:** 1.4, 2.2
- **Status:** todo
- **Read first:** docs/sources.md §3, docs/data-contracts.md §1, §5 (ctl.source_config)
**Do**
1. Connection: HTTP, base URL `https://gbfs.lyft.com`, anonymous: `conn_gbfs`.
2. Pipeline: `sp_run_start` → `lkp_sources` (`SELECT source_id, relative_url, landing_folder FROM ctl.source_config WHERE load_pattern = 'snapshot' AND is_enabled = 1`) → `fe_sources` (parallel, batch count 2) → `cp_gbfs_feed`: HTTP source, relative URL from the item; format **Binary** both sides, so the file lands byte for byte; sink path from `landing_folder`, today and `run_id`.
3. `sp_run_end` with the item count.
4. Turn `gbfs_system_regions` off in `ctl.source_config` and run: only one feed lands. Turn it back on.
**Acceptance**
- [ ] Two files land per run in the contract paths.
- [ ] Disabling a source row stops that copy without editing the pipeline.
- [ ] The landed files are byte-identical to a browser download (size matches).
**Result:** —

### US010 · Monthly trip files in bronze
As an analyst, I want each month's trip file landed and unzipped, so that Spark can read millions of trips from OneLake.
- One parameterised pipeline lands any month; re-running a month replaces it exactly.

#### T026 · `pl_ingest_trips_month`
- **Story:** US010
- **ADO:** #46
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 2
- **Depends on:** T015, T021
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/sources.md §4, docs/data-contracts.md §1, docs/risks.md R3, R13
**Do**
1. Parameters `trip_month` (`YYYYMM`), `run_id`, `parent_run_id`. Library variable `trips_base_url`.
2. `sp_run_start` → `del_month_folder`: Delete activity on `lh_bronze` Files `bronze/trips/month=<trip_month>/` (the only delete a pipeline may do; ignore "not found").
3. Two Copy activities, as proved in T015 (ADR-027): `cp_trips_stage` (HTTP to the staging path, Binary, no compression, URL built from `trips_base_url` and `trip_month`), then `cp_trips_unzip` (the staged zip, ZipDeflate, preserve-name tick off, into `bronze/trips/month=<trip_month>/`).
4. `gm_month_folder`: Get Metadata child items; `if_has_files`: fail with "no CSV extracted for <month>" if the count is 0.
5. Failure path on `cp_trips_stage` and on `cp_trips_unzip`: `sp_run_end` with status `failed` and the activity's error message (a 404 means "file not published yet").
6. Run for `202604` twice; then once for `209901` to see the clean failure.
**Note (T015, ADR-027).** The connection is `conn_tripdata bharat` (Fabric adds ` bharat` to the name typed) with the data source path `https://s3.amazonaws.com/tripdata/`. The trailing slash matters: without it Fabric requests the wrong path and returns a 404. A Copy activity takes its base address from the connection, so settle here whether `trips_base_url` can feed it or the connection stays the one place for the address; the relative URL is `<trip_month>-citibike-tripdata.zip`. CSV names differ by month (`-partN.csv` in 2026-04, `_N.csv` in 2026-06): read a month folder by `*.csv`. Measured in T015: 2026-04 took 23 s and 25 s, 2026-06 (1.051 GB) 63 s and 31 s. The staged zip is overwritten on a rerun, never deleted.
**Acceptance**
- [ ] `202604` lands its CSVs; the second run leaves the same file names and sizes.
- [ ] The `209901` run fails with a logged, readable message in `ctl.run_log`.
**Result:** —

## FT08 · Code-based REST ingestion

### US011 · An API ingested in code, with retries
As a data engineer, I want one source ingested in Python with retries and backoff, so that I can explain and show resilient API code, not only connectors.
- `nb_ingest_weather_forecast` survives a transient failure and lands one file per run.

#### T027 · `nb_ingest_weather_forecast`
- **Story:** US011
- **ADO:** #49
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 2
- **Depends on:** T022
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/sources.md §2, docs/conventions.md §4, §6
**Do**
1. Add to `nb_lib_common`: `http_get_json(session, url, params, timeout=30, max_attempts=5, backoff_base=2)` retrying only on 429, 5xx and connection errors, with jitter; returns the parsed JSON and the attempt count.
2. Notebook `nb_ingest_weather_forecast` (default lakehouse `lh_bronze`), parameters `run_id`. Build the request from `get_config()`, call `http_get_json`, write the raw response text to the landing path with `notebookutils.fs.put` (overwrite false).
3. Exit payload: `rows_written` = hours in the response, `message` = attempts used.
4. Run once from the notebook, once from a test pipeline `Notebook` activity passing `run_id = @pipeline().RunId`.
**Acceptance**
- [ ] One file per run in the contract path, 120 hours each (3 past + 2 future days).
- [ ] The pipeline's activity output shows the exit JSON.
- [ ] No URL is typed in the notebook.
**Result:** —

#### T028 · Unit tests for the HTTP helper and the path builders
- **Story:** US011
- **ADO:** #50
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 2
- **Depends on:** T016, T027
- **DP-700:** 3.2
- **Status:** todo
- **Read first:** docs/conventions.md §4
**Do**
1. `tests/test_http.py` with a fake session: success first time; 503 then success (2 attempts); 404 (no retry, raises); five 503s (raises after 5); timeout then success. Backoff sleeps patched to zero.
2. Run locally (Claude's workspace).
**Acceptance**
- [ ] Five tests pass; none makes a real network call.
**Result:** —

## FT09 · Bronze tables

### US012 · Raw files become queryable bronze tables with lineage
As a data engineer, I want every landed file turned into bronze rows exactly once, so that silver reads tables, not folders, and every row says where it came from.
- Bronze tables match the contract; re-runs add nothing.

#### T029 · `nb_bronze_load_json` with Structured Streaming `availableNow`
- **Story:** US012
- **ADO:** #53
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 2
- **Depends on:** T017, T024, T025, T027
- **DP-700:** 2.1, 2.3
- **Status:** todo
- **Read first:** docs/decisions.md ADR-008, docs/data-contracts.md §1–2, docs/risks.md R5
**Do**
1. Parameter `source_ids` (comma list, default all four JSON sources), `run_id`.
2. For each source: `readStream` text, `wholetext`, path `Files/bronze/<source_id>/*/*/*.json`, add `_metadata.file_path` as `_source_file`; in `foreachBatch`, parse `_ingest_date` and `_run_id` from the path with `parse_landing_path`, pull the envelope fields with `get_json_object`, append to `bronze_weather` or `bronze_gbfs`.
3. Checkpoint `Files/_checkpoints/<source_id>/`; `trigger(availableNow=True)`; `awaitTermination()`.
4. Exit payload with rows written per source.
5. Run, then run again with no new files.
**Acceptance**
- [ ] Both tables match the contract's columns and types.
- [ ] Second run writes 0 rows.
- [ ] Row count equals the number of landed files per source.
**Result:** —

#### T030 · `nb_bronze_load_trips`
- **Story:** US012
- **ADO:** #54
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 2
- **Depends on:** T026
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §2 (bronze_trips), docs/sources.md §4
**Do**
1. Parameters `trip_month`, `run_id`.
2. Read all CSVs under `Files/bronze/trips/month=<trip_month>/` (recursive) with an explicit all-string schema of the 13 columns, `header=true`; add `trip_month`, lineage columns.
3. Write `bronze_trips` partitioned by `trip_month` with `mode("overwrite").option("replaceWhere", "trip_month = '<m>'")`.
4. Exit payload with rows written.
**Acceptance**
- [ ] `bronze_trips` has the 2026-04 rows; the count equals the sum of CSV lines minus headers (checked once with a file-level count).
- [ ] Re-running gives the same count; `DESCRIBE HISTORY` shows an overwrite of one partition only.
**Result:** —

#### T031 · Prove bronze is idempotent
- **Story:** US012
- **ADO:** #55
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 2
- **Depends on:** T029, T030
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/architecture.md §7
**Do**
1. Note bronze counts per table and source.
2. Run `pl_ingest_gbfs_reference`, `nb_bronze_load_json` (twice), `nb_bronze_load_trips` for 202604.
3. Note counts again: JSON tables grow by exactly the new files; trips unchanged.
4. Claude writes the before/after table into the Result line and the explained notes.
**Acceptance**
- [ ] The counts behave exactly as step 3 says.
**Result:** —
