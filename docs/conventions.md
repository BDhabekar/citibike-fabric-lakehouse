# Conventions

## 1. Item names

Lower snake case, with a type prefix. One name per item in every environment: the workspace tells you which environment you are in, so the item name never carries it.

| Prefix | Item type | Names in this project |
|---|---|---|
| `ws-` | workspace (the one exception: kebab case, as Fabric shows workspaces in lists) | `ws-citibike-dev`, `ws-citibike-test`, `ws-citibike-prod` |
| `lh_` | lakehouse | `lh_bronze`, `lh_silver` |
| `wh_` | warehouse | `wh_gold` |
| `nb_` | notebook | `nb_lib_common`, `nb_ingest_weather_forecast`, `nb_bronze_load_json`, `nb_bronze_load_trips`, `nb_silver_weather_hourly`, `nb_silver_region`, `nb_silver_station_scd2`, `nb_silver_trips`, `nb_silver_station_status_hourly`, `nb_ops_table_maintenance` |
| `pl_` | pipeline | `pl_ingest_weather_archive`, `pl_ingest_gbfs_reference`, `pl_ingest_trips_month`, `pl_daily`, `pl_monthly_trips`, `pl_backfill`, `pl_post_deploy` |
| `df_` | Dataflow Gen2 | `df_weather_codes` |
| `env_` | environment | `env_citibike` |
| `vl_` | variable library | `vl_citibike` |
| `eh_` | eventhouse | `eh_citibike` (database `kqldb_citibike`) |
| `es_` | eventstream | `es_station_status` |
| `kqs_` | KQL queryset | `kqs_citibike` |
| `rtd_` | Real-Time Dashboard | `rtd_citibike_live` |
| `act_` | Activator | `act_citibike_alerts` |
| `sm_` | semantic model | `sm_citibike` |
| `rpt_` | report | `rpt_citibike_ops` |
| `dp-` | deployment pipeline | `dp-citibike` |

Pipeline activities: `<verb>_<object>` in lower snake case, e.g. `lkp_watermark`, `cp_weather_archive`, `fe_months`, `nb_bronze_weather`, `sp_run_start`, `if_has_rows`. Verb prefixes: `lkp` Lookup, `cp` Copy, `fe` ForEach, `nb` Notebook, `sp` Stored procedure, `scr` Script, `if` If condition, `sw` Switch, `wb` Web, `set` Set variable, `ex` Invoke pipeline, `fail` Fail.

Pipeline parameters: `run_id`, `parent_run_id`, `start_date`, `end_date` (ISO `YYYY-MM-DD`), `trip_month` (`YYYYMM`), `source_id`. Pipeline variables: `v_<name>`.

## 2. OneLake folders

Exactly as in `docs/data-contracts.md` §1. Never write outside `Files/bronze/`, `Files/seed/` and `Files/_checkpoints/` in `lh_bronze`. `lh_silver` has no Files content apart from the shortcut.

## 3. Variable library `vl_citibike`

| Variable | dev | test | prod |
|---|---|---|---|
| `env_name` | `dev` | `test` | `prod` |
| `gbfs_base_url` | `https://gbfs.lyft.com/gbfs/2.3/bkn/en` | same | same |
| `weather_archive_url` | `https://archive-api.open-meteo.com/v1/archive` | same | same |
| `weather_forecast_url` | `https://api.open-meteo.com/v1/forecast` | same | same |
| `weather_latitude` | `40.7829` | same | same |
| `weather_longitude` | `-73.9654` | same | same |
| `weather_hourly_vars` | `temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,snowfall,cloud_cover,wind_speed_10m,weather_code` | same | same |
| `trips_base_url` | `https://s3.amazonaws.com/tripdata` | same | same |
| `backfill_first_month` | `202604` | `202604` | `202607` |
| `backfill_last_month` | `202604` | `202604` | `202609` |
| `weather_backfill_start` | `2026-04-01` | `2026-04-01` | `2026-07-01` |
| `dq_max_reject_pct` | `1.0` | `1.0` | `1.0` |

Nothing environment-specific is typed into a pipeline, notebook or procedure. The CI scan (T075) fails a pull request that contains any of these URLs outside `vl_citibike`, `docs/` or `tests/`.

## 4. Notebook layout

Every notebook has these cells, in this order:

1. **Header** (markdown): purpose, inputs, outputs, the contract tables it writes, the task id that built it.
2. **Parameters** (a parameter cell): `run_id = "manual"` plus the notebook's own parameters, all with defaults that work in dev.
3. **Imports and `%run nb_lib_common`.**
4. **Config**: read `vl_citibike` through `nb_lib_common.get_config()`.
5. **Logic**: small functions first, then one `main()` call.
6. **Exit**: `notebookutils.notebook.exit(exit_payload(...))`.

Rules:

- Explicit schemas for every `from_json` and CSV read. No `inferSchema` outside a one-off investigation.
- No `display()`, `print()` of data or `.collect()` on large frames in committed code. Row counts come from Delta history or the write metrics.
- No `.toPandas()` on anything but tiny frames.
- Reusable functions go in `nb_lib_common` and get a unit test. A function in `nb_lib_common` takes and returns DataFrames or plain values, and never reads config or touches storage, so CI can test it without Fabric.
- Default lakehouse: bronze notebooks attach `lh_bronze`; silver notebooks attach `lh_silver` and read bronze through its OneLake path built by `nb_lib_common.table_path()`.

## 5. T-SQL in `wh_gold`

- Every object is schema-qualified. Procedure names start `usp_`, views `v_`, functions `fn_`.
- Every load procedure: parameters for its window, `SET NOCOUNT ON`, `BEGIN TRAN`, delete the window, insert the window, `COMMIT`, then `SELECT @@ROWCOUNT AS rows_written`-style output for the pipeline. On error: `ROLLBACK` and `THROW`.
- Scripts that create objects use `CREATE OR ALTER` where Fabric supports it, otherwise `DROP ... IF EXISTS` then `CREATE`. Re-running a script is always safe.
- Seed data is inserted by procedures (`ctl.usp_seed_config`), never by hand, because deployment moves objects but not data.

## 6. Notebook exit contract

Every notebook returns this JSON as its exit value. The pipeline passes it to `ctl.usp_run_end` as `details_json` and reads the counts from it.

```json
{
  "status": "succeeded",
  "notebook": "nb_silver_trips",
  "run_id": "<run_id>",
  "rows_read": 4512345,
  "rows_written": 4509876,
  "rows_rejected": 2469,
  "watermark": "202609",
  "dq": [
    {"table": "trips", "rule": "duration_in_range", "severity": "error",
     "rows_checked": 4512345, "rows_failed": 2401, "threshold_pct": 1.0, "passed": true}
  ],
  "message": ""
}
```

A notebook that finds an error-severity check above its threshold raises an exception after writing quarantine rows, so the pipeline's failure path runs. `status` is then never returned; the pipeline logs the error text instead.

## 7. Git

- Branches: `dev` (connected to `ws-citibike-dev`), `main` (what is in prod). `main` takes changes only through a pull request from `dev` with green checks.
- Commit messages: `T0xx: <what changed>` for task work; Fabric commits from the workspace use the same pattern, typed in the Source control pane.
- Tags: `vMAJOR.MINOR.PATCH` on `main` after each release to prod.
- Identity in this repo: `user.email = 166133418+BDhabekar@users.noreply.github.com`, `user.name = BDhabekar`.
- Never committed: secrets, tokens, `.pbix` files, data files other than `seed/`, anything under `evidence/` (screenshots live in ADE HQ).

## 8. Units, rounding, names in reports

Celsius, millimetres, centimetres for snow, km/h. Durations stored in seconds, shown in minutes with one decimal. Times shown in New York local time with the label "NY time".

## 9. Editing files under `/fabric` from outside Fabric (ADR-020)

Only for `nb_lib_common`, semantic model TMDL and report PBIR files, and only in this order:

1. Bharat opens Source control in `ws-citibike-dev` and commits anything pending.
2. Bharat runs `git -C D:\GitRepositories\citibike-fabric-lakehouse pull`.
3. Claude edits the file and commits on `dev` (`T0xx: ...`).
4. Bharat runs `git -C D:\GitRepositories\citibike-fabric-lakehouse push`. Nothing can have reached `dev` between steps 2 and 4 because the workspace had nothing pending.
5. Bharat opens Source control in the workspace and presses **Update all**.

## 10. Task chats and commits

Each task chat commits its own repo changes at the end of the task, on `dev`, with the message `T0xx: <summary>`, and ends with the two lines Bharat runs on Windows:

```
git -C D:\GitRepositories\citibike-fabric-lakehouse pull --rebase origin dev
git -C D:\GitRepositories\citibike-fabric-lakehouse push origin dev
```

The rebase is needed because Fabric commits to `dev` on GitHub directly. Claude never touches `/fabric` outside §9, so the rebase cannot conflict. Git in the device folder leaves lock files unless deletion is allowed, so the chat asks once for delete permission on `D:\GitRepositories` (git housekeeping only).
