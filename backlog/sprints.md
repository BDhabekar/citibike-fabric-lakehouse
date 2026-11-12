# Build passes

Re-planned on Thu Nov 12, 2026 (ADR-029). The first plan built one layer at a time for every source: all of bronze, then all of silver, then gold. This one builds one source at a time through every layer, so something complete exists at the end of each pass. No task was deleted and no id changed.

The **Sprint** field on a card is its pass number from this table. `tools/backlog.py check` refuses a card that depends on a card in a later pass, which is what keeps version 1.0 free of version 1.1 work.

| Sprint | What | When | Tasks | Card hours (Bharat) |
|---|---|---|---|---|
| 0 | repo ready, on GitHub (done) | Oct 23 – Oct 25 | T001–T002 | 0.2 |
| 1 | trial, workspaces, Git, six risks tried (done) | Oct 26 – Nov 3 | T003–T019 | 8.1 |
| 2 | control tables, logging procedures, shared notebook library (done) | Nov 3 | T020–T022 | 2.2 |
| 3 | **Pass A: start the stream.** Eventhouse, the live poller, the latest-state view. Built first because station history needs calendar days to collect. | Thu Nov 12 – Sun Nov 15 | T045–T047 | 2.5 |
| 4 | **Pass B: weather, end to end.** One source from the API through bronze, silver, gold, checks, the daily pipeline with its failure alert, CI, the deployment pipeline and the first report pages, released to prod as `v0.1.0`. | to Sun Nov 29 | T023, T024, T029, T032–T036, T054, T055, T058, T061, T062, T064, T067, T075–T079, T081, T082 | 14.4 |
| — | **DP-700 exam, Mon Dec 7** (fixed date, booked on the Data Days voucher). Mon Nov 30 to Sun Dec 6 is for practice assessments (85% before the exam; schedule in `plan/2026-11-06_dp700-dec7-plan.md` in the private study repo). | | | |
| 5 | **Pass C: trips, stations and the live view.** The monthly trip files, station history as SCD Type 2, the trip fact, row-level security, the Real-Time Dashboard and the rush-hour alert, released to prod as `v1.0.0`; then the README, the evidence pack and the walkthrough. | Tue Dec 8 – Thu Dec 17 | T025, T026, T030, T031, T037–T043, T048–T050, T057, T059, T065, T066, T071, T072, T080, T084–T089 | 21.1 |
| 6 | **Version 1.1, only if days are left.** The stream's cold path into gold (T051–T053, T060), the forecast source (T027, T028), the Dataflow Gen2 (T056), table maintenance (T044), and the monitoring, tuning and governance tasks (T063, T068–T070, T073, T074, T083). Released as `v1.1.0`. | after T080, before Fri Dec 18 | the fifteen above | 10.0 |

## What each release holds

| Tag | Closes | In prod afterwards |
|---|---|---|
| `v0.1.0` | pass B (T079) | weather from the API to `dim.weather_hour`, checked and logged every day; the failure alert; the report pages Pipeline health and Demand and weather (weather visuals); the live poller filling the Eventhouse |
| `v1.0.0` | pass C (T080) | 13 to 14 million trips for Jul–Sep 2026, station history, `fact.trip`, row-level security proved with a second user, the trip visuals, the Real-Time Dashboard and the rush-hour alert. Question 1 is answered in the Power BI report, question 2 in KQL on the dashboard. |
| `v1.1.0` | version 1.1 | `fact.station_hour` and the report page Empty at rush hour, the forecast hours, `dim.weather_code` |

## How to read the hours

Estimates on the cards are build minutes. With teaching, and the rule that a first-time set-up takes twice the click time, plan about 1.5 times the card total: about 4 real hours for pass A, 22 for pass B and 32 for pass C. Pass C is the tight one: 32 hours in the ten days between the exam and Thu Dec 17 is more than three hours a day. Two things ease it. Any pass C task whose dependencies are done can be pulled forward when pass B ends early (T026 is ready today). And if the days run out, pass C stops at whatever is finished, `v0.1.0` is already in prod, and the README says what is missing.

The dates are estimates from card hours, not a measured pace: the last task before this re-plan closed on Nov 3.

The trial started on Mon Oct 26 and ends about Fri Dec 25 (`docs/cost-and-capacity.md` §6). Fri Dec 18 is the last day for anything that needs a live workspace, T089 included.

`python3 tools/backlog.py summary` prints the live version of the hour columns, and `python3 tools/backlog.py next` lists what is ready, pass A first.
