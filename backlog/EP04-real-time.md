# EP04 · Real-time intelligence

**Goal.** Live station status every minute in an Eventhouse, a live dashboard, a rush-hour alert, and the same data reused in silver for history.
**Done when.** The dashboard shows stations empty now, Activator has fired a real rush-hour alert, and `station_status_hourly` fills from the stream.

## FT15 · Stream ingestion

### US018 · Live station status in the Eventhouse
As an operations lead, I want every station's status landed every minute, so that empty stations are seen while they are empty.
- `station_status` fills from the Eventstream through an update policy; retention and caching are set.

#### T045 · Eventhouse, KQL database, tables, policies and the update policy
- **Story:** US018
- **ADO:** #83
- **Owner:** Claude writes, Bharat runs
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T019
- **DP-700:** 2.3, 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §4, docs/risks.md R1 (the event shape from T013)
**Do**
1. Bharat: `ws-citibike-dev` → New item → Eventhouse → `eh_citibike`; rename its database to `kqldb_citibike`. Leave minimum consumption off.
2. Claude writes `kql/001_tables_and_policies.kql`: both tables; retention (raw 3 days, typed 30 days) and caching (raw 1 day, typed 7 days); `fn_parse_station_status()` (with `mv-expand` if T013 found one event per poll); the update policy on `station_status`.
3. Bharat runs the script in a KQL queryset as one batch; then `.show table station_status policy update` to confirm.
4. Claude tests the function by ingesting one sample payload inline (`.ingest inline`) and reading `station_status`.
5. Commit the workspace.
**Acceptance**
- [ ] Both tables and the update policy exist; the inline sample produces typed rows.
- [ ] `kql/001_tables_and_policies.kql` committed.
**Result:** —

#### T046 · `es_station_status`: the live poller, built from the runbook
- **Story:** US018
- **ADO:** #84
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 3
- **Depends on:** T013, T045
- **DP-700:** 2.3
- **Status:** todo
- **Read first:** docs/decisions.md ADR-007, docs/risks.md R1
**Do**
1. Claude first writes `docs/runbooks/eventstream.md`: every setting of the source (from T013), the destination (Eventhouse `kqldb_citibike`, table `station_status_raw`, direct ingestion, JSON), and how to stop and start it.
2. Bharat builds `es_station_status` by following the runbook word for word, then publishes.
3. After 5 minutes: `station_status_raw | count` and `station_status | summarize dcount(station_id), max(ingest_time)`.
4. Source control will show the Eventstream as not supported or failing to commit; leave it uncommitted (ADR-007) and note what the pane says.
**Acceptance**
- [ ] `station_status` grows every minute with about two thousand stations per poll.
- [ ] The runbook is enough to rebuild the item with no other help (Bharat says so).
**Result:** —

#### T047 · Latest-state view and the KQL queryset with windowing
- **Story:** US018
- **ADO:** #85
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 3
- **Depends on:** T046
- **DP-700:** 2.3, 3.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §4
**Do**
1. Claude teaches `summarize ... by bin()`, `arg_max`, tumbling and sliding windows, and materialized views on the live table first.
2. Bharat writes `mv_station_status_latest` (`.create materialized-view ... arg_max(poll_time, *) by station_id`) and checks it.
3. Queryset `kqs_citibike` with six saved queries Bharat writes: stations empty now; bikes available city-wide per 5 minutes (tumbling); per-station 15-minute sliding minimum; stations whose `last_reported` is older than 30 minutes (stale); top 10 stations by emptiness today; polls per minute (ingestion health).
4. Commit the workspace.
**Acceptance**
- [ ] The materialized view returns one row per station.
- [ ] Six saved queries run and are committed.
**Result:** —

## FT16 · Hot path for operations

### US019 · A live view and an alert
As an operations lead, I want a live dashboard and an alert when a station stays empty at rush hour, so that a rebalancing van can be sent.
- The dashboard shows names, not ids; the alert fires on real data.

#### T048 · Station names in KQL through a shortcut with query acceleration
- **Story:** US019
- **ADO:** #88
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T039, T047
- **DP-700:** 2.3, 2.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-019, docs/data-contracts.md §4
**Do**
1. Claude explains native tables, OneLake shortcuts and query acceleration in Real-Time Intelligence, and when each fits.
2. In `kqldb_citibike`: New → OneLake shortcut → `lh_silver` → table `station_scd2`, name `station_scd2_sc`, query acceleration **on**.
3. Bharat writes `fn_stations_empty_now()` joining `mv_station_status_latest` to current versions from the shortcut, and `fn_rush_hour_empty_15m()` as defined in the contract.
4. Compare one query's time with acceleration on vs a second shortcut without it (then delete the second).
**Acceptance**
- [ ] Both functions return station names.
- [ ] The accelerated vs plain timing is in the Result line.
**Result:** —

#### T049 · `rtd_citibike_live` Real-Time Dashboard
- **Story:** US019
- **ADO:** #89
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T048
- **DP-700:** 2.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §4
**Do**
1. New item → Real-Time Dashboard → `rtd_citibike_live`, data source `kqldb_citibike`, auto refresh 1 minute.
2. Tiles (Claude gives the exact query for each): stations empty now (count); map of empty stations (latitude/longitude); bikes available city-wide, last 6 hours (time chart); top 10 empty stations today (table); ingestion health (polls per minute).
3. Commit the workspace.
**Acceptance**
- [ ] Five tiles render with live data; screenshot filed.
**Result:** —

#### T050 · Activator: rush-hour empty-station alert
- **Story:** US019
- **ADO:** #90
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T014, T048
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/decisions.md ADR-016 (route from T014)
**Do**
1. Activator `act_citibike_alerts`, source: the `fn_rush_hour_empty_15m()` query on a 5-minute schedule.
2. Rule `rush_hour_empty`: fire when the query returns rows; action through the route ADR-016 records; message lists station names.
3. Test outside rush hour by a temporary copy of the function with the hour filter removed; restore it after the alert arrives.
4. Stop the dev Eventstream after this task (`docs/runbooks/eventstream.md`, Stop section); it runs only in prod from T079.
**Note (T014, ADR-016).** Build `act_citibike_alerts` in a workspace with no Git link (`ws-citibike-prod`, or `ws-citibike-test` while testing), never in `ws-citibike-dev`: a rule's recipient is stored in the item definition and Git would carry it into the public repo. Pick the tenant admin user in the To box, never type an address. Write `docs/runbooks/alert-rule.md` with the rule's settings and `<alert-recipient>`. Settle in this task whether the source query can be read from another workspace.
**Acceptance**
- [ ] A real alert, with station names, reached Bharat; screenshot filed.
- [ ] The temporary function is removed; the dev Eventstream is stopped.
**Result:** —

## FT17 · Cold path for history

### US020 · Hourly availability history in silver
As an analyst, I want hourly availability per station kept in the lakehouse, so that gold can rank stations by rush-hour emptiness over weeks.
- `station_status_hourly` is built from the same stream, incrementally, with a late-data overlap.

#### T051 · OneLake availability for `station_status` and the shortcut in `lh_silver`
- **Story:** US020
- **ADO:** #93
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 4
- **Depends on:** T046
- **DP-700:** 2.2, 2.3
- **Status:** todo
- **Read first:** docs/decisions.md ADR-019
**Do**
1. `kqldb_citibike` → table `station_status` → OneLake availability **on**. Note the latency Microsoft states.
2. `lh_silver` → Tables → New shortcut → Microsoft OneLake → `kqldb_citibike` → `station_status`, name `kql_station_status`.
3. From a notebook: count rows and max `ingest_time` through the shortcut; compare with KQL.
**Acceptance**
- [ ] The shortcut is readable from Spark; the lag against KQL is written in the Result line.
**Result:** —

#### T052 · `nb_silver_station_status_hourly`
- **Story:** US020
- **ADO:** #94
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 4
- **Depends on:** T032, T051
- **DP-700:** 2.1, 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (station_status_hourly), docs/decisions.md ADR-009
**Do**
1. Watermark = max `hour_utc` in the target (or the first data hour); window = watermark − 2 hours up to the last complete hour.
2. Minute buckets from `poll_time`; aggregate per station-hour as the contract defines (distinct minutes); `hour_local` from UTC.
3. Checks; `MERGE` on `station_id` + `hour_utc`.
4. Exit payload with `watermark`.
5. Run twice: the second run rewrites only the overlap hours with the same values.
**Acceptance**
- [ ] Table matches the contract; key unique; `minutes_empty <= samples` everywhere.
- [ ] `hour_local` is right on both sides of a clock change (streaming starts after Nov 1, 2026, so this is proved by the unit test in T053).
**Result:** —

#### T053 · Tests for the hourly aggregation
- **Story:** US020
- **ADO:** #95
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 4
- **Depends on:** T052
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/data-contracts.md §3 (station_status_hourly)
**Do**
1. Move the aggregation into `nb_lib_common.aggregate_station_hour(df)` if not already (protocol §9).
2. `tests/test_station_hour.py`: two polls in one minute count once; empty only while renting; full only while returning; late event inside the overlap updates the hour; on a made-up Sun Nov 1, 2026 the local day has 25 distinct UTC hours.
**Acceptance**
- [ ] Five tests pass.
**Result:** —
