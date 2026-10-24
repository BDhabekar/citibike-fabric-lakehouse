# EP06 · Orchestration, monitoring and operations

**Goal.** One daily and one monthly pipeline run everything in order, safely re-runnable, with a failure path that logs and alerts; the operator can monitor, troubleshoot and tune it.
**Done when.** A forced failure produces a logged error and an alert, and the error drills are written up.

## FT20 · Master pipelines

### US023 · One run does everything, in order
As an operator, I want one daily run and one monthly run, so that nobody has to remember the order of twenty steps.
- `pl_daily` and `pl_monthly_trips` are green end to end; `pl_backfill` loads any range of months.

#### T064 · `pl_daily`
- **Story:** US023
- **ADO:** #114
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 5
- **Depends on:** T024, T025, T027, T029, T035, T037, T039, T052, T057, T058, T060, T062
- **DP-700:** 1.4
- **Status:** todo
- **Read first:** docs/architecture.md §5, docs/conventions.md §1, §6, docs/decisions.md ADR-015
**Do**
1. Parameters `run_id` defaults to `@pipeline().RunId`. `sp_run_start`.
2. Stage 1 (parallel): `ex_weather_archive` (Invoke pipeline), `nb_weather_forecast`, `ex_gbfs_reference`.
3. Stage 2: `nb_bronze_json`.
4. Stage 3 (parallel): `nb_silver_weather`, `nb_silver_region`, `nb_silver_station`, `nb_silver_status_hourly`.
5. Stage 4: `sp_dim_region`, `sp_dim_station`, then (parallel) `sp_dim_weather_hour` (last 10 days to tomorrow + 1) and `sp_fact_station_hour` (window from the status notebook's exit `watermark`).
6. Stage 5: `sp_dq_daily`. Then `sp_run_end`.
7. Every notebook activity: timeout 30 minutes, retry 1 after 60 seconds. Every notebook's exit JSON is passed to `ctl.usp_run_end` as one step row.
8. Run twice.
**Acceptance**
- [ ] Two green runs; `ctl.run_log` shows every step for both; `ctl.dq_result` all passed.
- [ ] No step is typed with a date or URL.
**Result:** —

#### T065 · `pl_monthly_trips`
- **Story:** US023
- **ADO:** #115
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T026, T030, T041, T059, T062
- **DP-700:** 1.4, 2.1
- **Status:** todo
- **Read first:** docs/architecture.md §5
**Do**
1. Parameter `trip_month`, default empty meaning "previous month" (expression built by Bharat from Claude's building blocks).
2. `ex_trips_month` → `nb_bronze_trips` → `nb_silver_trips` → `sp_fact_trip` → `sp_dq_monthly` → `sp_watermark_set` (`trips`) → `sp_run_end`.
3. Run for `202604` twice.
**Acceptance**
- [ ] Green twice with identical counts at every step.
**Result:** —

#### T066 · `pl_backfill`
- **Story:** US023
- **ADO:** #116
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 5
- **Depends on:** T065
- **DP-700:** 1.4
- **Status:** todo
- **Read first:** docs/conventions.md §3
**Do**
1. `lkp_months`: `EXEC ctl.usp_month_list` with `backfill_first_month` and `backfill_last_month` from the library.
2. `fe_months` **sequential** → `ex_monthly_trips` with `trip_month` from the current item.
3. Run in dev (one month: 202604).
**Acceptance**
- [ ] Green; one `pl_monthly_trips` child run per month in the Monitoring hub.
**Result:** —

#### T067 · Failure path, alert and a forced failure
- **Story:** US023
- **ADO:** #117
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T014, T064
- **DP-700:** 3.1, 3.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-016
**Do**
1. In `pl_daily` and `pl_monthly_trips`: an on-failure path from each stage to `sp_run_end_failed` (status `failed`, the failed activity's error message) and the alert (route from ADR-016), ending in a `fail_pipeline` Fail activity so the run still shows as failed.
2. Force a failure: run `pl_monthly_trips` with `trip_month = 209901`.
3. Check the log row, the alert and the run status.
**Acceptance**
- [ ] The alert arrived; `ctl.run_log` has the failed step with its message; the run shows Failed.
**Result:** —

## FT21 · Monitoring and troubleshooting

### US024 · Health and capacity visible, errors diagnosable
As an operator, I want to see what ran, what it cost in capacity, and why something failed, so that I can fix problems without guessing.
- The operator knows where every kind of error shows up and has tuned the slowest steps.

#### T068 · Monitoring hub, Spark monitoring and capacity use of a daily run
- **Story:** US024
- **ADO:** #120
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 5
- **Depends on:** T064
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/cost-and-capacity.md §5
**Do**
1. Monitoring hub: filter to `pl_daily`, open the last run, read each activity's duration and input/output.
2. Open one notebook run's Spark monitoring: jobs, stages, the slowest stage, shuffle size.
3. Capacity Metrics app: find the CU used by that run (by item).
4. Claude writes the numbers into the explained notes as "what a daily run costs in capacity on the trial, and what that would mean on an F2".
**Acceptance**
- [ ] Durations, slowest Spark stage and CU per item in the Result line.
**Result:** —

#### T069 · Error drills: break it on purpose, find it, fix it
- **Story:** US024
- **ADO:** #121
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T047, T051, T056, T064
- **DP-700:** 3.2
- **Status:** todo
- **Read first:** docs/runbooks/eventstream.md
**Do**
1. Claude plants one fault at a time in dev (each with its undo written first): a pipeline parameter with a bad date; a notebook reading a misspelled column; a T-SQL procedure with a divide by zero; a KQL update policy pointing at a renamed column; a shortcut whose target table was renamed; the Eventstream paused; a Dataflow Gen2 refresh failing on a type mismatch in `df_weather_codes`.
2. Bharat finds each from the screen where it surfaces (Monitoring hub, notebook output, query editor, `.show ingestion failures`, shortcut error, Eventstream status, dataflow refresh history), names the cause, fixes it.
3. Claude records where each error type shows up into a troubleshooting table in the explained notes.
**Acceptance**
- [ ] Seven faults found and fixed; every planted change undone (Source control shows nothing pending afterwards).
**Result:** —

#### T070 · Optimisation pass with before and after numbers
- **Story:** US024
- **ADO:** #122
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T068
- **DP-700:** 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §3
**Do**
1. From T068, pick the slowest notebook and the slowest pipeline step.
2. Claude lays out options (broadcast join for small dimensions, partition count, caching a reused DataFrame; for the pipeline, parallelism and batch counts) and recommends one each.
3. Apply, re-run, compare.
**Acceptance**
- [ ] Before/after durations in the Result line; reasons in the explained notes.
**Result:** —
