# EP03 · Silver transformations (PySpark)

**Goal.** Typed, flattened, deduplicated and conformed silver tables, with data-quality results recorded and bad rows quarantined, never silently dropped.
**Done when.** All silver tables in `docs/data-contracts.md` §3 (except `station_status_hourly`, built in EP04) exist, pass their checks, and their shared functions have unit tests.

## FT10 · Data-quality framework

### US013 · Checks as data, results recorded
As an operator, I want every silver load to record which checks ran and how many rows failed, so that quality is visible over time and a bad load stops the pipeline.
- One rule runner, used by every silver notebook, producing the `dq` list of the exit contract.

#### T032 · DQ runner and quarantine writer in `nb_lib_common`
- **Story:** US013
- **ADO:** #59
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 3
- **Depends on:** T029
- **DP-700:** 2.2, 3.2
- **Status:** todo
- **Read first:** docs/conventions.md §6, docs/data-contracts.md §3 (quarantine)
**Do**
1. A rule is a dict: `name`, `severity` (`error`/`warn`), `condition` (a Spark SQL expression that is true for a *good* row), `threshold_pct`.
2. `apply_rules(df, rules)` → `(good_df, bad_df, results)`: `bad_df` carries `dq_rule` and `dq_reason` for the first error rule a row fails; warn rules only count. `results` is the list for the exit payload.
3. `write_quarantine(bad_df, table, run_id)` appends to `quarantine_<table>` in `lh_silver`.
4. `raise_if_failed(results)` raises with a readable message when any error rule exceeds its threshold.
**Acceptance**
- [ ] The three functions exist; `apply_rules` never reads storage (testable in CI).
- [ ] A scratch run on 10 made-up rows routes the 2 bad rows to quarantine with the right reasons.
**Result:** —

#### T033 · Tests for the DQ runner
- **Story:** US013
- **ADO:** #60
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 3
- **Depends on:** T032
- **DP-700:** 3.2
- **Status:** todo
- **Read first:** docs/conventions.md §4
**Do**
1. `tests/test_dq.py`: good rows pass; one error rule; two error rules (first one wins in `dq_rule`); warn rule counted not quarantined; threshold exceeded raises; nulls in the checked column count as failures.
**Acceptance**
- [ ] All tests pass locally.
**Result:** —

## FT11 · Weather silver

### US014 · One row per hour of weather
As an analyst, I want one weather row per UTC hour, preferring measured archive values over forecasts, so that joins with trips are exact and recent days improve automatically.
- `weather_hourly` matches the contract and the upsert rule in ADR-018.

#### T034 · Flatten Open-Meteo's parallel arrays
- **Story:** US014
- **ADO:** #63
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 3
- **Depends on:** T032
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/sources.md §1, docs/data-contracts.md §3 (weather_hourly)
**Do**
1. In `nb_lib_common`: `explode_open_meteo_hourly(df_payload)` takes rows with a `payload` string, parses it with an explicit schema (`hourly` as a struct of arrays), `arrays_zip`s the arrays, `explode`s, and returns one row per hour with the contract's column names (UTC `hour_utc` from `time`, which is GMT).
2. Claude adds `tests/test_weather_explode.py` with a 3-hour payload, including a `null` value and a missing variable.
**Acceptance**
- [ ] The function returns 3 rows for the test payload, columns named as in the contract.
- [ ] The test passes.
**Result:** —

#### T035 · `nb_silver_weather_hourly` with source-priority upsert
- **Story:** US014
- **ADO:** #64
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 3
- **Depends on:** T034
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-018, docs/data-contracts.md §3 (weather_hourly)
**Do**
1. Read `bronze_weather` rows newer than the silver table's last `_source_file` set (Claude explains the choice: anti-join on `_source_file` against a small processed list, or a `_ingest_ts` watermark).
2. Explode; set `data_kind`, `source_priority`, `generated_at_utc`; drop archive rows whose measured values are all null; deduplicate within the batch (best priority, then newest).
3. `apply_rules` (hour unique, temperature range, precipitation ≥ 0); quarantine bad rows.
4. `MERGE` into `weather_hourly` with the ADR-018 conditions.
5. Exit payload with counts and `dq`.
6. Run, run again (no change), then load a new forecast file and run (only forecast hours change).
**Acceptance**
- [ ] One row per hour from 2026-04-01 to tomorrow + 1.
- [ ] An archive row is never replaced by a forecast row (Claude's check query returns 0).
- [ ] Second run reports 0 rows written.
**Result:** —

#### T036 · Tests for the weather priority rule
- **Story:** US014
- **ADO:** #65
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 3
- **Depends on:** T035
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/decisions.md ADR-018
**Do**
1. Move the batch dedup logic into a pure function in `nb_lib_common` (Bharat commits; Claude edits per conventions §9 if needed) and test: archive beats forecast; newer forecast beats older; forecast never beats archive; all-null archive row dropped.
**Acceptance**
- [ ] Four tests pass.
**Result:** —

## FT12 · Station silver

### US015 · Station history that survives renames and removals
As an analyst, I want every version of every station kept, so that a trip is matched to the station as it was on the day of the trip.
- `region` and `station_scd2` match the contract and ADR-011.

#### T037 · `nb_silver_region`
- **Story:** US015
- **ADO:** #68
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 3
- **Depends on:** T029, T032
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (region), docs/sources.md §3
**Do**
1. Take the newest `gbfs_system_regions` row from `bronze_gbfs`, parse `data.regions[]` with an explicit schema, explode, overwrite `region`.
2. Check: `region_id` unique, `region_name` not null.
**Acceptance**
- [ ] `region` has one row per region in the latest file.
**Result:** —

#### T038 · SCD Type 2 function with deterministic keys
- **Story:** US015
- **ADO:** #69
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 3
- **Depends on:** T032
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-010, ADR-011; docs/data-contracts.md §3 (station_scd2)
**Do**
1. Claude teaches SCD2 on a 3-station made-up example first (new, changed, missing) before any code.
2. In `nb_lib_common`: `scd2_changes(current_df, snapshot_df, snapshot_ts)` → a DataFrame of actions (`insert_new`, `close`, `insert_version`, `close_missing`) with the new rows' `station_version_key = xxhash64(station_id, valid_from_utc)` and `attr_hash`.
3. Pure function: DataFrames in, DataFrame out; the MERGE is done by the notebook (T039).
**Acceptance**
- [ ] On the made-up example the function returns exactly the actions Claude predicted in the lesson.
**Result:** —

#### T039 · `nb_silver_station_scd2`
- **Story:** US015
- **ADO:** #70
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 3
- **Depends on:** T038
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (station_scd2), docs/decisions.md ADR-011
**Do**
1. Read unprocessed `gbfs_station_information` snapshots from `bronze_gbfs`, oldest first.
2. For each snapshot: parse `data.stations[]`, round coordinates, compute actions with `scd2_changes`, apply them with one `MERGE` (closes and inserts together).
3. Checks: one current row per station, no overlapping windows; quarantine none (a failure here raises).
4. Exit payload.
5. Run on the snapshots so far; run again (no change).
**Acceptance**
- [ ] One current version per station id.
- [ ] Re-run writes 0 rows.
- [ ] Claude's overlap check query returns 0.
**Result:** —

#### T040 · Tests for SCD2
- **Story:** US015
- **ADO:** #71
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T038
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/decisions.md ADR-011
**Do**
1. `tests/test_scd2.py`: new station; unchanged station (no action); capacity change (close + insert); station missing (close); same snapshot twice (no action); coordinates differing only after the 6th decimal (no action); keys stable across two runs.
**Acceptance**
- [ ] Seven tests pass.
**Result:** —

## FT13 · Trips silver

### US016 · Clean trips in UTC with quality flags
As an analyst, I want one clean row per ride with UTC and local times, so that trips join exactly to weather and station history.
- `trips` matches the contract; rejected rides are in quarantine with a reason.

#### T041 · `nb_silver_trips`
- **Story:** US016
- **ADO:** #74
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 3
- **Depends on:** T030, T032
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (trips), docs/decisions.md ADR-009, docs/sources.md §4
**Do**
1. Parameters `trip_month`, `run_id`. Read the month from `bronze_trips`.
2. Parse timestamps with the format recorded in T015; convert to UTC with `to_utc_timestamp(..., 'America/New_York')`; compute `duration_sec`, `start_hour_utc`, `trip_date_local`, `start_hour_local`, flags.
3. Deduplicate on `ride_id` (keep the lexically last `_source_file`), count drops.
4. `apply_rules` with the contract's error and warn rules; quarantine.
5. Write with `replaceWhere trip_month = '<m>'`.
6. Exit payload with counts and `dq`.
**Acceptance**
- [ ] `trips` for 2026-04 matches the contract; `ride_id` unique.
- [ ] Quarantine rows have reasons; the reject share is under `dq_max_reject_pct` (or the run fails, as designed).
- [ ] A ride starting at 2026-04-15 08:00 local shows 12:00 UTC (daylight time, UTC-4).
**Result:** —

#### T042 · Tests for the trip rules
- **Story:** US016
- **ADO:** #75
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T041
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (trips)
**Do**
1. Move the row-shaping logic into `nb_lib_common.shape_trips(df)` if it is not already there (protocol §9).
2. `tests/test_trips.py`: normal ride; end before start; 59 s; 25 h; unknown member type; empty end station (kept, flagged); a ride across the Nov 1 clock change (UTC duration correct); duplicate `ride_id`.
**Acceptance**
- [ ] Eight tests pass.
**Result:** —

#### T043 · Station-id conformance check between trips and stations
- **Story:** US016
- **ADO:** #76
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T039, T041
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/sources.md §4
**Do**
1. Query: share of `trips.start_station_short_name` values (non-null) that match a `station_scd2.short_name` valid at the trip's start time; list the top 20 unmatched names with counts.
2. Claude explains the result and what gold does with unmatched rides (unknown member `-1`).
3. The share becomes a warn rule in `dq.usp_run_checks` (T062) with the threshold Claude proposes from this number.
**Acceptance**
- [ ] Match share and top unmatched list in the Result line and the explained notes.
**Result:** —

## FT14 · Lakehouse table optimisation

### US017 · Silver tables stay fast as they grow
As an operator, I want partitioning, file sizes and old versions managed, so that queries stay fast and storage does not grow without limit.
- Choices are written down with their reason; a maintenance notebook runs weekly.

#### T044 · Table layout and `nb_ops_table_maintenance`
- **Story:** US017
- **ADO:** #79
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T041
- **DP-700:** 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §2–3 (partitions); docs/decisions.md ADR-024
**Do**
1. Claude lays out the options (partitioning, V-Order, optimize-write, Z-order, VACUUM retention) with their cost, checks Microsoft's current property names, and recommends. The environment runs Runtime 2.0 (ADR-024): read its defaults first (deletion vectors on for new tables, adaptive target file size, `OPTIMIZE` fast mode, optimize-write no longer set) so no setting is chosen against 1.3 behaviour.
2. Apply the chosen table properties to the silver tables.
3. `nb_ops_table_maintenance`: for each bronze and silver table, `OPTIMIZE` (with Z-order where chosen) and `VACUUM` with 7-day retention; exit payload with files before/after.
4. Run once; note the file counts.
**Acceptance**
- [ ] Settings and reasons written in the Result line and ADR log (Claude adds the next free ADR number; ADR-022 to ADR-024 are taken).
- [ ] The notebook runs green; file counts before/after recorded.
**Result:** —
