# EP05 · Gold warehouse (T-SQL star schema)

**Goal.** A star schema in `wh_gold` loaded by idempotent procedures, with reporting views and gold-level checks.
**Done when.** All `dim`, `fact` and `rpt` objects in `docs/data-contracts.md` §5 exist, loads re-run cleanly, and `dq.usp_run_checks` passes.

## FT18 · Star schema

### US021 · A model analysts can query
As an analyst, I want trips and station-hours in a star schema with conformed dimensions, so that any BI tool or SQL user gets the same answers.
- Facts and dimensions match the contract; every load can be re-run for its window.

#### T054 · DDL for `dim`, `fact`, `rpt`, `dq`, `sec` and `gold`
- **Story:** US021
- **ADO:** #99
- **Owner:** Claude writes, Bharat runs
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T018, T020
- **DP-700:** 2.1, 1.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §5, docs/conventions.md §5
**Do**
1. Claude checks the supported data types and `PRIMARY KEY NONCLUSTERED NOT ENFORCED` syntax on Microsoft's Fabric Warehouse pages, then writes `sql/gold/001_schemas_and_tables.sql`.
2. Bharat runs it twice (second run: no error).
3. Commit the workspace. Claude reads the warehouse folder Fabric wrote under `/fabric` and confirms each table is there as a database-project file.
**Acceptance**
- [ ] Every table in the contract exists with its types.
- [ ] The warehouse item in Git lists the tables (database project).
**Result:** —

#### T055 · `gold.usp_load_dim_date`
- **Story:** US021
- **ADO:** #100
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 30 min
- **Sprint:** 4
- **Depends on:** T054
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (dim.date)
**Do**
1. Claude gives the skeleton (a numbers list from `VALUES` cross joins, no recursive CTE); Bharat writes the column expressions.
2. Run it; then run it again.
**Acceptance**
- [ ] 730 rows (2026-01-01 to 2027-12-31); `day_of_week` 1 = Monday; Sat and Sun flagged weekend.
- [ ] Second run leaves 730 rows.
**Result:** —

#### T056 · Dataflow Gen2 `df_weather_codes` into `dim.weather_code`
- **Story:** US021
- **ADO:** #101
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 45 min
- **Sprint:** 6
- **Depends on:** T008, T054
- **DP-700:** 1.4, 2.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-006
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left. When it is built, `pl_post_deploy` gains the `df_weather_codes` refresh (it was a step of T078) and `dim.weather_code` joins `sm_citibike`.
**Do**
1. Claude explains when a Dataflow Gen2 is the right tool (a small reference table maintained by business users, Power Query skills) and when it is not.
2. New item → Dataflow Gen2 → `df_weather_codes`. Source: `lh_bronze` → Files → `seed/wmo_weather_codes.csv`. Types: `weather_code` whole number, others text. Trim text.
3. Destination: `wh_gold`, table `dim.weather_code`, update method **Replace**.
4. Publish; refresh; refresh again.
**Acceptance**
- [ ] `dim.weather_code` has the seed's row count, once, after two refreshes.
**Result:** —

#### T057 · `gold.usp_load_dim_region` and `gold.usp_load_dim_station`
- **Story:** US021
- **ADO:** #102
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 75 min
- **Sprint:** 5
- **Depends on:** T037, T039, T054, T064
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (dim.region, dim.station), docs/decisions.md ADR-017
**Do**
1. Both procedures: in one transaction, delete all rows, insert from `lh_silver.dbo.region` / `lh_silver.dbo.station_scd2`, then insert the unknown member.
2. Run each twice.
3. Add the station branch to `pl_daily` (moved here from T064 by ADR-029): `ex_gbfs_reference` in stage 1, `nb_silver_region` and `nb_silver_station` in stage 3, `sp_dim_region` then `sp_dim_station` at the start of stage 4. Run `pl_daily` twice.
**Acceptance**
- [ ] Row counts equal silver + 1 (unknown member); unchanged after the second run.
- [ ] Two green `pl_daily` runs with the five new steps in `ctl.run_log`.
**Result:** —

#### T058 · `gold.usp_load_dim_weather_hour @from_utc, @to_utc`
- **Story:** US021
- **ADO:** #103
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T035, T054
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (dim.weather_hour), docs/decisions.md ADR-017
**Do**
1. Delete the window, insert from `lh_silver.dbo.weather_hourly` with `date_key_local`, `hour_of_day_local` (from `hour_local`) and `is_wet_hour`.
2. Load 2026-04-01 to today + 2 days; reload the last 10 days.
**Acceptance**
- [ ] One row per hour that silver holds in the window; the reload leaves the same count.
**Result:** —

#### T059 · `gold.usp_load_fact_trip @trip_month`
- **Story:** US021
- **ADO:** #104
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 105 min
- **Sprint:** 5
- **Depends on:** T041, T057, T061
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (fact.trip), docs/decisions.md ADR-010, ADR-013, ADR-017
**Do**
1. Claude teaches the "as of" lookup on an SCD2 dimension with a 2-station, 3-trip made-up example before any SQL.
2. Delete the month; insert from `lh_silver.dbo.trips` with `LEFT JOIN dim.station` on `short_name` and `started_at_utc` inside the validity window (start and end separately), `COALESCE(key, -1)`, `start_region_id` from the start station's version, `trip_date_key` from the local date.
3. Run for 202604 twice.
4. Claude adds `rpt.v_trip_daily_weather` to `sql/gold/002_rpt_views.sql` (moved here from T061 by ADR-029); Bharat runs it and `SELECT TOP 10`.
**Acceptance**
- [ ] Row count equals silver valid trips for 202604; `ride_id` unique.
- [ ] Unknown-key share matches the conformance number from T043 (within rounding).
- [ ] `rpt.v_trip_daily_weather` has one row per local date with trips.
**Result:** —

#### T060 · `gold.usp_load_fact_station_hour @from_utc, @to_utc`
- **Story:** US021
- **ADO:** #105
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 45 min
- **Sprint:** 6
- **Depends on:** T052, T057
- **DP-700:** 2.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (fact.station_hour)
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left. When it is built it carries everything that hangs on `fact.station_hour`: `sp_fact_station_hour` in stage 4 of `pl_daily`, `rpt.v_station_rush_empty` in `sql/gold/002_rpt_views.sql`, the station-hour checks in `dq.usp_run_checks`, `fact.station_hour` in the policy `sec.rls_region`, the table and the two rush-hour measures in `sm_citibike`, and the report page **Empty at rush hour**. That release is tagged `v1.1.0`.
**Do**
1. Delete the window; insert from `lh_silver.dbo.station_status_hourly` joined to `dim.station` by `station_id` as of `hour_utc`; `region_id`, `is_weekday` from `dim.date`.
2. Load everything so far; reload the last day.
**Acceptance**
- [ ] Row count equals silver for the window; key unique; reload leaves the same count.
**Result:** —

#### T061 · Reporting views in `rpt`
- **Story:** US021
- **ADO:** #106
- **Owner:** Claude writes, Bharat runs
- **Estimate:** 15 min
- **Sprint:** 4
- **Depends on:** T058
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (rpt)
**Do**
1. Claude writes `sql/gold/002_rpt_views.sql` with `rpt.v_pipeline_health`. The other two views need facts that are loaded later: `rpt.v_trip_daily_weather` is added to the same file in T059 (pass C) and `rpt.v_station_rush_empty` in T060 (version 1.1).
2. Bharat runs it and runs `SELECT TOP 10` on the view.
**Acceptance**
- [ ] `rpt.v_pipeline_health` returns one row per run.
**Result:** —

## FT19 · Gold quality and performance

### US022 · Gold that reconciles and stays fast
As an analyst, I want gold to reconcile with silver and to answer quickly, so that I trust the numbers and the report stays responsive.
- Checks run after every load; slow queries are found and explained.

#### T062 · `dq.usp_run_checks @run_id, @scope`
- **Story:** US022
- **ADO:** #109
- **Owner:** Claude writes, Bharat runs
- **Estimate:** 30 min
- **Sprint:** 4
- **Depends on:** T058
- **DP-700:** 3.1, 3.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (dq, ctl.dq_result)
**Do**
1. Claude writes `sql/gold/003_dq_checks.sql` with the `daily` scope as pass B needs it: silver vs gold row reconciliation for `dim.weather_hour` over the loaded window, and key uniqueness on `dim.weather_hour` and `dim.date`. The `monthly` scope and the station checks (trip reconciliation per month, key uniqueness on `fact.trip` and `dim.station`, orphan keys, unknown-member share, one current station version per id) are added in T065 (pass C); the station-hour checks in T060 (version 1.1).
2. Each check writes a `ctl.dq_result` row; any failed error check ends with `THROW`.
3. Bharat runs it; then breaks one thing on purpose (a duplicate hour in a scratch copy of `dim.weather_hour`, per Claude's script), runs again, sees the failure, cleans up.
**Acceptance**
- [ ] A clean run writes all-passed rows.
- [ ] The planted duplicate makes the procedure fail with a readable message.
**Result:** —

#### T063 · Warehouse performance review
- **Story:** US022
- **ADO:** #110
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 30 min
- **Sprint:** 6
- **Depends on:** T061
- **DP-700:** 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §5
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left.
**Do**
1. Run the three `rpt` views twice each; read Query insights (`queryinsights.exec_requests_history`, `long_running_queries`) for their times.
2. Claude explains statistics, result-set caching and data clustering options that exist at the time (checked on Microsoft's pages), recommends at most one change, and Bharat applies it.
3. Re-run and compare.
**Acceptance**
- [ ] Before/after times in the Result line; the reason for the change (or for no change) in the explained notes.
**Result:** —
