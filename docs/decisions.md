# Decisions

Each decision has the options that were turned down, because "why not X?" is the question interviews ask. Status is **Accepted** unless marked otherwise. New entries go at the end with the next number. A task chat that hits a conflict writes a **Proposed** entry and stops (see `docs/architecture.md` §10).

---

## ADR-001 · Dataset: Citi Bike trips, GBFS station feeds and Open-Meteo weather
**Context.** The Olist project already covers batch SQL ingestion from a database. This one needs REST APIs, nested JSON, a live stream and real volume for Spark.
**Decision.** Citi Bike monthly trips (about 4–5 million rows a month), GBFS station feeds (live and reference), Open-Meteo weather (history and forecast).
**Turned down.** Olist on Fabric (no REST, no stream, no comparison value left); a paid or keyed API (secrets and quotas for no learning gain); synthetic data (interviewers discount it).
**Consequence.** Attribution is owed: Open-Meteo data is CC BY 4.0, Citi Bike data is under the NYCBS Data Use Policy. Both go in the README.

## ADR-002 · Identity: Bharat's own tenant, not an employer or family tenant
**Context.** Fabric needs a work or school (Microsoft Entra) account. A Gmail address cannot hold a Fabric licence.
**Decision.** `<tenant-admin-upn>` in his own tenant `bharat-ade`, where he is Global Administrator (created Sep 10, 2026).
**Turned down.** The employer work account: company policy, IT can block trials, and the work disappears when he changes jobs. A relative's Azure for Students tenant: Bharat is not a tenant admin there, so he could not change Fabric tenant settings (trials, service principals, Git), and the project would sit in someone else's directory.
**Consequence.** He controls every tenant setting. The test analyst user for security work is created in the same tenant at no cost.

## ADR-003 · Capacity: the 60-day trial for the whole build; pay-as-you-go F2 only for short demos afterwards
**Context.** The last project's plan was skewed by an unexpected Serverless bill. This one must have a cost that cannot surprise.
**Decision.** Build, publish and sit DP-700 inside the trial. No Azure subscription is linked during the build, so nothing can bill. After the trial, a pay-as-you-go F2 is created only if a live demo is needed, paused by default, with a budget alert and a nightly automatic pause.
**Turned down.** Buying an F2 from day one (about ₹28,000 a month if left running). A reservation (billed for a year whether used or not). Running the build on the Azure for Students credit (wrong tenant, and the credit is not his).
**Consequence.** The trial end date is a hard deadline. Prices and guardrails: `docs/cost-and-capacity.md`.

## ADR-004 · Layers: lakehouses for bronze and silver, a warehouse for gold
**Decision.** `lh_bronze` and `lh_silver` hold files and Delta tables processed by Spark. `wh_gold` holds the star schema, control tables and security objects, built with T-SQL.
**Turned down.** All lakehouse (gold through the SQL analytics endpoint, which is read-only, so no stored procedures, no multi-table transactions, no RLS written in T-SQL on gold tables). All warehouse (T-SQL is a poor fit for exploding JSON arrays and SCD2 history on large CSVs).
**Consequence.** Gold procedures read silver through cross-database queries in the same workspace (proved by spike T018).

## ADR-005 · Two lakehouses rather than one lakehouse with schemas
**Decision.** Separate `lh_bronze` and `lh_silver`, no schema-enabled lakehouses.
**Turned down.** One schema-enabled lakehouse: fewer items, but it adds feature limits to check for no benefit at this size.
**Consequence.** Permissions can differ per layer (analysts never see bronze).

## ADR-006 · Four ingestion styles, each chosen for its source
**Decision.** Pipeline Copy (REST connector) for weather history; pipeline Copy (HTTP connector) for GBFS reference feeds, driven by `ctl.source_config`; pipeline Copy (HTTP, binary, zip decompression) for trip files; a notebook with `requests` for the forecast; Eventstream for live status. Dataflow Gen2 is used once, for the small WMO weather-code lookup, as a business-maintained reference table.
**Turned down.** Everything in notebooks (loses the no-code monitoring, retries and connectors that most teams use); everything in pipelines (no place to show retry and backoff written in code, which interviews ask about).
**Consequence.** Covers the DP-700 point "choose between Dataflow Gen2, a pipeline and a notebook" with a real reason for each.

## ADR-007 · Live status through the Eventstream HTTP source (named preview exception)
**Context.** The station feed has to be polled; it does not push.
**Options.** (a) Eventstream HTTP source polling every 60 seconds. (b) A notebook that polls and sends to an Eventstream custom endpoint, which needs a connection string and a secret store; Azure Key Vault needs a paid Azure subscription. (c) A pipeline every 5 minutes copying JSON files, which is not streaming.
**Decision.** (a). Microsoft documents it as preview, without Git or deployment-pipeline support.
**Consequence.** The Eventstream is the one item created by hand in dev and prod, from `docs/runbooks/eventstream.md`. Everything downstream (KQL tables, update policy, views, functions) is in Git. Spike T013 confirms the event shape before anything depends on it. If (a) fails, (c) is the fallback, and the change is recorded here first.

## ADR-008 · Bronze picks up new files with Structured Streaming `availableNow`
**Decision.** `nb_bronze_load_json` reads landing folders with `spark.readStream` (text, whole file per row) and `trigger(availableNow=True)`, with one checkpoint folder per source under `Files/_checkpoints/`. Each run processes exactly the files not yet seen, then stops.
**Turned down.** Re-reading whole folders (cost grows every day); hand-written "processed files" tables (more code that can go wrong).
**Fallback (decided now).** If the streaming text source misbehaves in spike T017, use a batch read anti-joined on `_source_file` against the bronze table.
**Consequence.** Covers the DP-700 point "process data by using Spark structured streaming" with a real use.

## ADR-009 · Time: UTC in storage, New York local time computed once in Spark
**Decision.** All stored timestamps are UTC. Silver adds local columns with `from_utc_timestamp(..., 'America/New_York')` or converts the other way for trips (whose CSV times are local). Weather is requested with `timezone=GMT`.
**Turned down.** Local time everywhere (the hour 01:00–02:00 repeats on Sun Nov 1, 2026, when clocks go back, which silently doubles rows in hourly joins).
**Consequence.** Joins between trips, weather and station status are on `hour_utc`. Reports show local hours from the columns built in Spark.

## ADR-010 · Deterministic surrogate keys built in silver
**Decision.** `station_version_key = xxhash64(station_id, valid_from_utc)`. Unknown members are `-1`.
**Turned down.** Warehouse identity columns or `ROW_NUMBER()` at load time (keys change on a rebuild, so facts and dimensions drift apart after a re-run).
**Consequence.** A full rebuild gives the same keys, so reloads are safe.

## ADR-011 · Stations are SCD Type 2, and a station that disappears is closed
**Decision.** Tracked attributes: short name, name, region, capacity, latitude, longitude (rounded to 6 decimals). A changed hash closes the old version and opens a new one at the snapshot's `last_updated` time. A station missing from a snapshot is closed with `is_current = false`.
**Consequence.** Handles deletes at the source, the gap left open in the Olist project (its backlog item B38).

## ADR-012 · Semantic model in Direct Lake on the warehouse; Power BI items in Git (named preview exception)
**Decision.** `sm_citibike` uses Direct Lake on `wh_gold`. The model and report are stored in Git as TMDL and PBIR, which Microsoft marks as preview for Git. Claude writes the model and report definitions; Bharat creates the items and syncs.
**Consequence.** Warehouse RLS makes Direct Lake fall back to DirectQuery for those queries. Task T083 shows it and the README explains it.

## ADR-013 · Security model
**Decision.** Workspace roles (Bharat Admin; test analyst Viewer on prod only); item permission Read on `wh_gold` only; T-SQL `GRANT SELECT` on `rpt` and `dim`/`fact` for the analyst role; RLS by region; dynamic data masking on `fact.trip.ride_id`; column-level `DENY` on exact trip timestamps for analysts. `region_id` is copied onto both fact tables so the RLS predicate needs no join.
**Why mask ride_id and hide exact times.** A single trip with its exact start time and two station locations can identify a person. Analysts need counts by hour, not exact seconds.

## ADR-014 · CI/CD: Fabric Git integration and deployment pipelines, checks in GitHub Actions
**Decision.** `ws-citibike-dev` is connected to GitHub repo `BDhabekar/citibike-fabric-lakehouse`, branch `dev`, folder `/fabric`. A pull request `dev` → `main` with green checks is the release approval. Deployment pipeline `dp-citibike` (Development → Test → Production) promotes items. Variable library `vl_citibike` holds per-stage values. GitHub Actions runs unit tests, lint, JSON checks, a hard-coded-value scan and the backlog check on every pull request.
**Turned down.** The `fabric-cicd` Python library run from Actions with a service principal (production-grade too, but needs a client secret stored in GitHub and more tenant settings, for no DP-700 benefit). One Git branch per stage (more merges, more to explain).
**Consequence.** Lakehouse and warehouse data never travel through deployment; each stage loads its own data. Config rows are seeded after each deployment by `pl_post_deploy`.

## ADR-015 · Orchestration: pipelines run things, notebooks report back in one JSON shape
**Decision.** Pipelines own order, retries, timeouts and logging. Every notebook ends with `notebookutils.notebook.exit(json.dumps(...))` using the exit contract in `docs/conventions.md` §6. The pipeline logs it with `ctl.usp_run_end`.
**Turned down.** Notebooks writing to the warehouse themselves (a second connector and credential path to maintain).

## ADR-016 · Failure alert route: decided by spike T014
**Order tried.** (1) Activator email to an external address, from Fabric job events. (2) Activator email to the tenant user, with that user's contact email set to his Gmail. (3) Pipeline failure path calling a Web activity to a phone push service.
**Status.** Accepted order. The working route is written here by T019.

## ADR-017 · Gold loads by delete-and-insert per window inside a transaction
**Decision.** Each procedure takes a window (month or date range), deletes that window from the target and inserts it from silver, inside `BEGIN TRAN ... COMMIT`.
**Turned down.** Depending on `MERGE` in the Warehouse (check its status at build time rather than build on it); full reloads every day (cost grows with history).

## ADR-018 · Weather: one point, archive beats forecast
**Decision.** Central Park (40.7829, -73.9654). Archive rows always win over forecast rows for the same hour; a newer forecast replaces an older forecast; a forecast never replaces an archive row.
**Consequence.** Recent days use forecast-model values until the archive catches up (about 5 days behind), then are corrected automatically by the next run.

## ADR-019 · One stream, two uses: OneLake availability for station status
**Decision.** Turn on OneLake availability for the KQL table `station_status`, then shortcut it into `lh_silver` as `kql_station_status`. The hourly silver table is built from that.
**Turned down.** A second poller for the batch side (two copies of the same truth, which drift).
**Consequence.** Covers "native tables vs OneLake shortcuts" in Real-Time Intelligence. The reverse direction is also used: an Eventhouse shortcut to the silver station table (with query acceleration) so KQL can show station names (T048).

## ADR-020 · Who edits what in the repo
**Decision.** The Fabric workspace owns `/fabric`. Claude owns everything else (docs, backlog, tests, CI, tools, seed files). Claude edits a file under `/fabric` only with the protocol in `docs/conventions.md` §9 (Bharat commits pending workspace changes first, pulls, Claude edits and commits, Bharat pushes, then presses Update in Fabric).

## ADR-021 · Data volume per environment
**Decision.** Prod loads trip months 2026-07, 2026-08 and 2026-09 (about 3 GB zipped, roughly 13–14 million rows) and then each new month. Dev and test load 2026-04 only (165 MB, the smallest recent month).
**Consequence.** Enough volume to make Spark choices visible, small enough to keep test runs short.
