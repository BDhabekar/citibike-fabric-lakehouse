# Data contracts

Every table the project creates, with its grain (what one row is), key, columns and checks. A notebook or procedure that writes a table must produce exactly these columns with these types. Adding, renaming or retyping a column is a change-control decision (`docs/architecture.md` §10).

Type notation: Spark types for lakehouse tables, T-SQL types for the warehouse, KQL types for the Eventhouse. Columns starting with `_` are lineage columns, added by the pipeline rather than taken from the source.

---

## 1. Landing files (`lh_bronze` → Files)

| source_id | Path | Written by |
|---|---|---|
| `weather_archive` | `Files/bronze/weather_archive/ingest_date=YYYY-MM-DD/run_id=<run_id>/weather_archive_<start>_<end>.json` | `pl_ingest_weather_archive` |
| `weather_forecast` | `Files/bronze/weather_forecast/ingest_date=YYYY-MM-DD/run_id=<run_id>/weather_forecast_<yyyyMMddHHmmss>.json` | `nb_ingest_weather_forecast` |
| `gbfs_station_information` | `Files/bronze/gbfs_station_information/ingest_date=YYYY-MM-DD/run_id=<run_id>/station_information.json` | `pl_ingest_gbfs_reference` |
| `gbfs_system_regions` | `Files/bronze/gbfs_system_regions/ingest_date=YYYY-MM-DD/run_id=<run_id>/system_regions.json` | `pl_ingest_gbfs_reference` |
| `trips` | `Files/bronze/trips/month=YYYYMM/` (the CSVs from the zip) | `pl_ingest_trips_month` |
| trips staging | `Files/bronze/_staging/trips/month=YYYYMM/<YYYYMM>-citibike-tripdata.zip` (the zip as downloaded; ADR-027) | `pl_ingest_trips_month` |
| seed | `Files/seed/wmo_weather_codes.csv` | uploaded once from `seed/` in this repo |
| checkpoints | `Files/_checkpoints/<source_id>/` | `nb_bronze_load_json` |

`ingest_date` is the UTC date of the run. `run_id` is the pipeline run id (`@pipeline().RunId`), or `manual-<yyyyMMddHHmmss>` for a hand run. A trip month folder is the only landing path a pipeline may delete, and only its own month, just before re-copying it. The staged zip is never deleted: a rerun overwrites the same file name.

---

## 2. Bronze tables (`lh_bronze` → Tables)

### `bronze_weather`
**Grain:** one row per landed weather file. **Key:** `_source_file`. **Partition:** `_ingest_date`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `source_id` | string | no | `weather_archive` or `weather_forecast` |
| `payload` | string | no | the whole file, untouched |
| `latitude` | double | yes | parsed from payload |
| `longitude` | double | yes | |
| `utc_offset_seconds` | int | yes | must be 0 (requests use `timezone=GMT`) |
| `_source_file` | string | no | full OneLake path |
| `_ingest_date` | date | no | from the folder name |
| `_run_id` | string | no | from the folder name |
| `_ingest_ts` | timestamp | no | when bronze loaded it (UTC) |

### `bronze_gbfs`
**Grain:** one row per landed GBFS file. **Key:** `_source_file`. **Partition:** `_ingest_date`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `source_id` | string | no | `gbfs_station_information` or `gbfs_system_regions` |
| `feed_last_updated` | long | yes | envelope `last_updated` (Unix seconds) |
| `feed_ttl` | int | yes | |
| `feed_version` | string | yes | |
| `payload` | string | no | |
| `_source_file`, `_ingest_date`, `_run_id`, `_ingest_ts` | as above | no | |

### `bronze_trips`
**Grain:** one row per CSV line. **Key:** none enforced in bronze (duplicates are a silver concern). **Partition:** `trip_month`.

| Column | Type | Null | Notes |
|---|---|---|---|
| the 13 source columns (`ride_id` … `member_casual`) | string | yes | read as text, exactly as in the CSV |
| `trip_month` | string | no | `YYYYMM`, from the folder |
| `_source_file` | string | no | |
| `_ingest_ts` | timestamp | no | |
| `_run_id` | string | no | |

Reload rule: `replaceWhere trip_month = '<month>'`.

---

## 3. Silver tables (`lh_silver` → Tables)

### `weather_hourly`
**Grain:** one row per UTC hour. **Key:** `hour_utc`. **Partition:** none (about 9,000 rows a year).

| Column | Type | Null | Notes |
|---|---|---|---|
| `hour_utc` | timestamp | no | |
| `hour_local` | timestamp | no | New York local, from `from_utc_timestamp` |
| `temperature_c` | double | yes | `temperature_2m` |
| `apparent_temperature_c` | double | yes | |
| `relative_humidity_pct` | int | yes | |
| `precipitation_mm` | double | yes | |
| `rain_mm` | double | yes | |
| `snowfall_cm` | double | yes | |
| `cloud_cover_pct` | int | yes | |
| `wind_speed_kmh` | double | yes | |
| `weather_code` | int | yes | WMO code |
| `data_kind` | string | no | `archive` or `forecast` |
| `source_priority` | int | no | 1 archive, 2 forecast (lower wins) |
| `generated_at_utc` | timestamp | no | when the source file was fetched (from `_ingest_ts` of its bronze row) |
| `_source_file` | string | no | |
| `_updated_ts` | timestamp | no | |

**Upsert rule (ADR-018):** match on `hour_utc`. Update when the incoming priority is lower, or the same priority and newer `generated_at_utc`. Archive rows whose measured values are all `null` are dropped before the merge, never merged.
**Checks:** `hour_utc` unique (error); `temperature_c` between -40 and 50 when present (error → quarantine); `precipitation_mm >= 0` (error → quarantine); no gap of more than 2 hours inside the archive range (warn).

### `region`
**Grain:** one row per region. **Key:** `region_id`. Rebuilt from the newest snapshot each run.

| Column | Type | Null |
|---|---|---|
| `region_id` | string | no |
| `region_name` | string | no |
| `feed_last_updated_utc` | timestamp | no |
| `_updated_ts` | timestamp | no |

### `station_scd2`
**Grain:** one row per version of a station. **Key:** `station_version_key`. **Business key:** `station_id` + `valid_from_utc`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `station_version_key` | long | no | `xxhash64(station_id, valid_from_utc)` (ADR-010) |
| `station_id` | string | no | GBFS id |
| `short_name` | string | yes | the id trip files use |
| `station_name` | string | no | |
| `region_id` | string | yes | |
| `capacity` | int | yes | |
| `latitude` | double | no | rounded to 6 decimals |
| `longitude` | double | no | rounded to 6 decimals |
| `attr_hash` | string | no | `sha2` over the six tracked attributes, nulls as empty strings, joined with a separator |
| `valid_from_utc` | timestamp | no | snapshot `last_updated` |
| `valid_to_utc` | timestamp | no | `9999-12-31 00:00:00` while current |
| `is_current` | boolean | no | |
| `_source_file` | string | no | file that opened the version |
| `_updated_ts` | timestamp | no | |

**Rules (ADR-011):** new station → insert a version; changed hash → close the current version at the new snapshot time and insert a version; station missing from a snapshot → close it; re-processing a snapshot already applied changes nothing; snapshots are applied oldest first.
**Checks:** one current row per `station_id` (error); no overlapping validity windows per `station_id` (error); `valid_from_utc < valid_to_utc` (error).

### `trips`
**Grain:** one row per ride. **Key:** `ride_id`. **Partition:** `trip_month`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `ride_id` | string | no | |
| `rideable_type` | string | no | e.g. `classic_bike`, `electric_bike` |
| `member_type` | string | no | `member` or `casual` (from `member_casual`) |
| `started_at_local` | timestamp | no | as in the CSV |
| `ended_at_local` | timestamp | no | |
| `started_at_utc` | timestamp | no | `to_utc_timestamp(started_at_local, 'America/New_York')` |
| `ended_at_utc` | timestamp | no | |
| `start_hour_utc` | timestamp | no | `date_trunc('hour', started_at_utc)`, joins to weather |
| `trip_date_local` | date | no | |
| `start_hour_local` | int | no | 0–23 |
| `duration_sec` | int | no | |
| `start_station_short_name` | string | yes | |
| `end_station_short_name` | string | yes | |
| `start_station_name` | string | yes | |
| `end_station_name` | string | yes | |
| `start_lat`, `start_lng`, `end_lat`, `end_lng` | double | yes | |
| `is_round_trip` | boolean | no | start and end short names equal and not null |
| `has_end_station` | boolean | no | |
| `trip_month` | string | no | `YYYYMM` |
| `_source_file` | string | no | |
| `_updated_ts` | timestamp | no | |

**Dedup:** one row per `ride_id`; if a `ride_id` repeats within a month, keep the row from the lexically last `_source_file` and count the drop.
**Checks → quarantine (error):** `ride_id` null; `started_at` or `ended_at` not parseable; `ended_at < started_at`; `duration_sec` outside 60–86,400; `member_casual` not in (`member`, `casual`). **Warn only:** `rideable_type` not in the known list; start station empty.
**Reload rule:** `replaceWhere trip_month = '<month>'`.

### `station_status_hourly`
**Grain:** one row per station per UTC hour. **Key:** `station_id` + `hour_utc`. **Partition:** `status_date_utc`.

| Column | Type | Null | Notes |
|---|---|---|---|
| `station_id` | string | no | |
| `hour_utc` | timestamp | no | |
| `status_date_utc` | date | no | partition column |
| `hour_local` | timestamp | no | |
| `samples` | int | no | distinct minutes with at least one reading |
| `avg_bikes_available` | double | no | |
| `min_bikes_available` | int | no | |
| `max_bikes_available` | int | no | |
| `avg_ebikes_available` | double | no | |
| `avg_docks_available` | double | no | |
| `minutes_empty` | int | no | distinct minutes with `num_bikes_available = 0` and the station renting |
| `minutes_full` | int | no | distinct minutes with `num_docks_available = 0` and the station returning |
| `minutes_not_renting` | int | no | distinct minutes with `is_renting = false` |
| `_updated_ts` | timestamp | no | |

**Incremental rule:** recompute every hour from (watermark − 2 hours) up to the last complete hour, then MERGE on the key. The 2-hour overlap absorbs late events.
**Checks:** key unique (error); `samples` between 1 and 60 (error); `minutes_empty <= samples` (error).

### `kql_station_status` (OneLake shortcut, read only)
The Eventhouse table `station_status` exposed through OneLake availability (ADR-019). Same columns as §4 below.

### Quarantine tables
`quarantine_trips` and `quarantine_weather`: the columns of the row as it arrived (strings), plus `dq_rule` (string), `dq_reason` (string), `_run_id` (string), `_quarantined_ts` (timestamp). Append only.

---

## 4. Eventhouse `eh_citibike` → KQL database `kqldb_citibike`

### `station_status_raw`
**Grain:** one row per event from the Eventstream (shape fixed by spike T013). Retention 3 days; caching 1 day.

| Column | Type |
|---|---|
| `payload` | dynamic |
| `ingest_time` | datetime (`ingestion_time()` at the update policy) |

### `station_status`
**Grain:** one row per station per poll. Retention 30 days; caching 7 days. Filled by the update policy `fn_parse_station_status()` from `station_status_raw` (with `mv-expand` when one event carries the whole station array).

| Column | Type |
|---|---|
| `station_id` | string |
| `num_bikes_available` | int |
| `num_ebikes_available` | int |
| `num_bikes_disabled` | int |
| `num_docks_available` | int |
| `num_docks_disabled` | int |
| `is_installed` | bool |
| `is_renting` | bool |
| `is_returning` | bool |
| `last_reported` | datetime (from Unix seconds) |
| `poll_time` | datetime (feed `last_updated` when present, else `ingest_time`) |
| `ingest_time` | datetime |

### Other KQL objects
- `mv_station_status_latest`: materialized view, `arg_max(poll_time, *) by station_id`.
- `fn_stations_empty_now()`: stations with zero bikes, renting, in the latest state, with names from the shortcut to silver.
- `fn_rush_hour_empty_15m()`: stations whose last 15 one-minute samples all had zero bikes, between 07:00–10:00 or 16:00–19:00 New York time on weekdays. This is what Activator watches.
- `station_scd2_sc`: OneLake shortcut to `lh_silver.station_scd2` with query acceleration (T048).

---

## 5. Warehouse `wh_gold`

Types follow the Fabric Warehouse rules: `varchar` (no `nvarchar`), `datetime2(6)` (no `datetime`), `int`/`smallint`/`bigint`, `bit`, `decimal`, `float`, `date`. Primary keys are declared `NOT ENFORCED` and are checked by `dq.usp_run_checks`. T054 checks the type list against the Microsoft page before the DDL runs.

### Schema `ctl` (control)
- **`ctl.source_config`**: one row per source. `source_id varchar(50)`, `source_kind varchar(20)` (`rest_pipeline`, `rest_notebook`, `http_file`, `stream`), `base_url_variable varchar(100)` (the name of the variable in `vl_citibike`), `relative_url varchar(400)`, `landing_folder varchar(200)`, `load_pattern varchar(20)` (`incremental`, `snapshot`, `monthly`, `stream`), `is_enabled bit`, `notes varchar(400)`.
- **`ctl.watermark`**: `source_id varchar(50)`, `watermark_value varchar(50)` (ISO date or `YYYYMM`), `updated_at_utc datetime2(6)`, `updated_by_run_id varchar(64)`.
- **`ctl.run_log`**: one row per pipeline step. `run_id varchar(64)`, `parent_run_id varchar(64)`, `pipeline_name varchar(100)`, `step_name varchar(100)`, `environment varchar(10)`, `status varchar(20)` (`started`, `succeeded`, `failed`), `rows_read bigint`, `rows_written bigint`, `rows_rejected bigint`, `started_at_utc datetime2(6)`, `ended_at_utc datetime2(6)`, `error_message varchar(4000)`, `details_json varchar(8000)`.
- **`ctl.dq_result`**: one row per rule per run. `run_id varchar(64)`, `layer varchar(10)`, `table_name varchar(100)`, `rule_name varchar(100)`, `severity varchar(10)` (`error`, `warn`), `rows_checked bigint`, `rows_failed bigint`, `fail_pct decimal(9,4)`, `threshold_pct decimal(9,4)`, `passed bit`, `checked_at_utc datetime2(6)`.

### Schema `dim`
- **`dim.date`**: grain one row per calendar date, 2026-01-01 to 2027-12-31. `date_key int` (yyyymmdd), `date date`, `year smallint`, `quarter smallint`, `month smallint`, `month_name varchar(10)`, `day_of_month smallint`, `day_of_week smallint` (1 = Monday), `day_name varchar(10)`, `iso_week smallint`, `is_weekend bit`, `month_start date`.
- **`dim.weather_code`**: grain one row per WMO code. `weather_code int`, `description varchar(100)`, `category varchar(30)` (`clear`, `cloudy`, `fog`, `drizzle`, `rain`, `snow`, `thunderstorm`). Loaded by Dataflow Gen2 `df_weather_codes`.
- **`dim.weather_hour`**: grain one row per UTC hour. All columns of silver `weather_hourly` except lineage, plus `date_key_local int`, `hour_of_day_local smallint`, `is_wet_hour bit` (`precipitation_mm >= 0.2`).
- **`dim.region`**: `region_id varchar(20)`, `region_name varchar(100)`. Includes the unknown member `('-1', 'Unknown')`.
- **`dim.station`**: grain one row per station version. All columns of silver `station_scd2` except `attr_hash` and lineage. Includes the unknown member `station_version_key = -1`.

### Schema `fact`
- **`fact.trip`**: grain one row per ride. `ride_id varchar(40)`, `trip_date_key int` (local date), `start_hour_utc datetime2(6)`, `start_hour_local smallint`, `start_station_version_key bigint`, `end_station_version_key bigint`, `start_region_id varchar(20)`, `rideable_type varchar(20)`, `member_type varchar(10)`, `duration_sec int`, `is_round_trip bit`, `has_end_station bit`, `started_at_utc datetime2(6)`, `ended_at_utc datetime2(6)`, `trip_month char(6)`, `load_run_id varchar(64)`. Station keys are looked up "as of" `started_at_utc` against the SCD2 validity window, by short name; no match gives `-1`.
- **`fact.station_hour`**: grain one row per station per UTC hour. `station_id varchar(64)`, `station_version_key bigint` (as of the hour), `region_id varchar(20)`, `hour_utc datetime2(6)`, `date_key_local int`, `hour_of_day_local smallint`, `is_weekday bit`, `samples int`, `avg_bikes_available decimal(9,2)`, `min_bikes_available int`, `avg_docks_available decimal(9,2)`, `minutes_empty int`, `minutes_full int`, `minutes_not_renting int`, `load_run_id varchar(64)`.

### Schema `rpt` (views for people and the report)
- `rpt.v_trip_daily_weather`: one row per local date: trips, member trips, casual trips, average duration in minutes, average temperature, total precipitation, wet hours.
- `rpt.v_station_rush_empty`: one row per station: weekday rush-hour minutes empty over the last 14 days of data, rank within region.
- `rpt.v_pipeline_health`: one row per run: duration, status, rows, failed checks.

### Schema `dq`
- `dq.usp_run_checks @run_id, @scope`: runs the gold checks (row reconciliation with silver per month, key uniqueness, orphan keys, unknown-member share), writes `ctl.dq_result`, raises an error when an error-severity check fails.

### Schema `sec`
- `sec.user_region`: `user_principal_name varchar(256)`, `region_id varchar(20)`.
- `sec.fn_region_predicate(@region_id)`: inline table function; Bharat's account sees everything, others see their mapped regions.
- Security policy `sec.rls_region` on `fact.trip` (`start_region_id`) and `fact.station_hour` (`region_id`).

### Procedures (schema `gold` for loads, `ctl` for logging)
`ctl.usp_run_start`, `ctl.usp_run_end`, `ctl.usp_watermark_set`, `ctl.usp_seed_config`; `gold.usp_load_dim_date`, `gold.usp_load_dim_region`, `gold.usp_load_dim_station`, `gold.usp_load_dim_weather_hour @from_utc, @to_utc`, `gold.usp_load_fact_trip @trip_month`, `gold.usp_load_fact_station_hour @from_utc, @to_utc`. Each load deletes its window and inserts it inside one transaction (ADR-017).
