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
- **Estimate:** 60 min
- **Sprint:** 4
- **Depends on:** T024, T029, T035, T058, T062
- **DP-700:** 1.4
- **Status:** todo
- **Read first:** docs/architecture.md §5, docs/conventions.md §1, §6, docs/decisions.md ADR-015
**Pass B (ADR-029).** `pl_daily` is built here with the weather branch only, and it keeps the five stages so a later branch drops into its stage without the pipeline being redrawn. T057 (pass C) adds `ex_gbfs_reference`, `nb_silver_region`, `nb_silver_station`, `sp_dim_region` and `sp_dim_station`. In version 1.1, T027 adds `nb_weather_forecast`, T052 adds `nb_silver_status_hourly` and T060 adds `sp_fact_station_hour`.
**Do**
1. Parameters `run_id` defaults to `@pipeline().RunId`. `sp_run_start`.
2. Stage 1: `ex_weather_archive` (Invoke pipeline).
3. Stage 2: `nb_bronze_json`.
4. Stage 3: `nb_silver_weather`.
5. Stage 4: `sp_dim_weather_hour` (last 10 days to tomorrow + 1).
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
- **Estimate:** 90 min
- **Sprint:** 5
- **Depends on:** T026, T030, T041, T043, T059, T062, T067
- **DP-700:** 1.4, 2.1
- **Status:** todo
- **Read first:** docs/architecture.md §5
**Do**
1. Claude adds the `monthly` scope and the station checks to `sql/gold/003_dq_checks.sql` (moved here from T062 by ADR-029): silver vs gold row reconciliation per trip month, key uniqueness on `fact.trip` and `dim.station`, orphan keys (no key outside `dim.station`), unknown-member share (warn, threshold from T043), one current station version per id. Bharat runs it.
2. Parameter `trip_month`, default empty meaning "previous month" (expression built by Bharat from Claude's building blocks).
3. `ex_trips_month` → `nb_bronze_trips` → `nb_silver_trips` → `sp_fact_trip` → `sp_dq_monthly` → `sp_watermark_set` (`trips`) → `sp_run_end`, with the failure path built as in T067 (`sp_run_end_failed`, the alert, `fail_pipeline`).
4. Run for `202604` twice.
5. Force a failure: run with `trip_month = 209901`; check the log row, the alert and the run status.
**Acceptance**
- [ ] Green twice with identical counts at every step; `ctl.dq_result` all passed for the `monthly` scope.
- [ ] The forced failure shows Failed, logs its message in `ctl.run_log` and sends the alert.
**Result:** —

#### T066 · `pl_backfill`
- **Story:** US023
- **ADO:** #116
- **Owner:** Bharat builds (Claude guides)
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
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T014, T064
- **DP-700:** 3.1, 3.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-016
**Do**
1. In `pl_daily`: an on-failure path from each stage to `sp_run_end_failed` (status `failed`, the failed activity's error message) and the alert (route from ADR-016), ending in a `fail_pipeline` Fail activity so the run still shows as failed.
2. Force a failure: Claude gives one statement that plants a duplicate hour in `dim.weather_hour`, in a day older than the 10-day reload window so the load does not wipe it. Run `pl_daily`: `sp_dq_daily` fails. Afterwards delete the planted row and run green.
3. Check the log row, the alert and the run status.
**Note (T014, ADR-016).** The alert is an Activator email to the tenant admin user (route 2). Build the rule in `ws-citibike-prod` or `ws-citibike-test`, never in dev, and Claude writes `docs/runbooks/alert-rule.md` here, with the rule's settings and `<alert-recipient>`; T050 (pass C) adds its rule to the same runbook. `pl_monthly_trips` gets the same failure path when it is built in T065. A trigger from job events or the pipeline failure path has not been proven yet; prove it here before relying on it.
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
- **Estimate:** 45 min
- **Sprint:** 6
- **Depends on:** T064
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/cost-and-capacity.md §5
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left.
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
- **Estimate:** 60 min
- **Sprint:** 6
- **Depends on:** T047, T051, T056, T064
- **DP-700:** 3.2
- **Status:** todo
- **Read first:** docs/runbooks/eventstream.md
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left.
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
- **Estimate:** 60 min
- **Sprint:** 6
- **Depends on:** T068
- **DP-700:** 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §3
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left.
**Do**
1. From T068, pick the slowest notebook and the slowest pipeline step.
2. Claude lays out options (broadcast join for small dimensions, partition count, caching a reused DataFrame; for the pipeline, parallelism and batch counts) and recommends one each.
3. Apply, re-run, compare.
**Acceptance**
- [ ] Before/after durations in the Result line; reasons in the explained notes.
**Result:** —
