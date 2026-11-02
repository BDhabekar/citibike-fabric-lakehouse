# Risks

Each risk is retired by a named task before any other task depends on it, and each has its fallback decided now, so a failed check changes a known line instead of starting a redesign. Spikes run in Sprint 1 (T013–T018); T019 writes the outcomes here and in `docs/decisions.md`.

| Id | Risk | Retired by | If it fails (decided now) | Status |
|---|---|---|---|---|
| R1 | The Eventstream HTTP source (preview) does not poll the GBFS feed reliably, or its event shape is unexpected | T013 | Fall back to `pl_poll_station_status` every 5 minutes landing JSON in `lh_bronze`, with Eventhouse ingestion from OneLake; ADR-007 updated to option (c) | closed (T019): option (a) works, fallback not taken; ADR-007 |
| R2 | No alert route reaches Bharat (the tenant user has no mailbox) | T014 | Try in order: Activator email to Gmail; Activator email to the tenant user with its contact email set to Gmail; pipeline Web activity to a phone push service | closed (T019): route 2 of the order delivered; ADR-016 |
| R3 | Copy activity cannot decompress the 1 GB trip zip from HTTP into Files | T015 | Copy the zip as binary, then unzip in a notebook with Python `zipfile` through the lakehouse file mount | fallback taken (T019), a different one: ADR-027, two Copy activities; the notebook fallback in this row is not used |
| R4 | CI cannot import `nb_lib_common` from its Git file (`notebook-content.py`) | T016 | CI extracts the code cells between the cell markers into a temporary module before importing | closed (T019): plain import works, fallback not taken |
| R5 | Structured Streaming with the text source and `availableNow` misbehaves in Fabric | T017 | Batch read anti-joined on `_source_file` (ADR-008 fallback) | closed (T019): works, ADR-008 fallback not taken |
| R6 | Warehouse cross-database query to `lh_silver`, the Stored procedure activity, or the variable library in pipelines and notebooks does not work as documented | T018 | Cross-database: Script activity against the warehouse reading the silver SQL endpoint. Variable library: pipeline parameters with defaults plus deployment rules | closed (T019): all three work in dev, fallbacks not taken; the test and prod value sets are not yet tried |
| R7 | The tenant blocks the trial or a needed setting | T003 | Bharat is Global Administrator; the setting is switched on in the Admin portal | open |
| R8 | The trial ends before the project, the publish or the exam | T004 sets the dates; sprints end 7 days before trial end | Publish from Git and screenshots; a short paid F2 session only by written decision (`docs/cost-and-capacity.md` §3–4) | open |
| R9 | An email address or other personal detail ends up in the public repo through item definitions in Git | T014, T086 | Use an address Bharat is happy to publish, or keep that value out of Git; T086 scans the repo before it goes public | open |
| R10 | Fabric screens change during the build | every task | Small UI differences are noted in the Result line; anything that changes the design goes through change control | standing |
| R11 | Lyft adds or changes GBFS fields | design | Bronze keeps raw text; silver parses with an explicit schema and ignores extras | designed out |
| R12 | Daylight saving ends on Sun Nov 1, 2026, during streaming | design | Everything stored in UTC (ADR-009); the unit tests in T042 and T053 cover that day | designed out |
| R13 | A monthly trip file is late or renamed | T026 | The pipeline checks the file exists first and fails with a clear message; the next day's run retries | open |
| R14 | Open-Meteo rate limits | design | Under 20 calls a day; retries with backoff | designed out |

## R1 spike result (T013, Oct 28, 2026): shape known, polling repeats

The HTTP source called `station_status.json` and keeps calling it. The result below comes from Bharat's screenshots of Oct 28 and Microsoft's definition of the metrics. T019 (Nov 3, 2026) closed R1 and recorded the outcome in ADR-007: option (a) holds and fallback (c) is not taken.

**Settings that worked.** Method GET, Anonymous connection, request interval 60 s, Pagination method "No pagination", Response data JSON pointer `/data/stations` (the box is offered without pagination). Fabric's defaults for the rest: 10 retries, 3 s backoff, retry on 500, 502, 503 and 504. A run without the pointer was not tried.

**Event shape: one event is one station**, not one poll. The `data.stations[]` entry arrives with 13 fields: `station_id`, `num_bikes_available`, `num_bikes_disabled`, `num_docks_available`, `num_docks_disabled`, `is_installed`, `is_renting`, `is_returning`, `last_reported`, `vehicle_types_available` (an array of `vehicle_type_id` and `count`, shown as one JSON cell), `num_ebikes_available`, `num_scooters_available`, `num_scooters_unavailable` (the two scooter fields are empty on placeholder stations). The envelope fields `last_updated`, `ttl` and `version` do not appear, so no field says which poll an event came from; the arrival time has to be stamped downstream. Flags arrived as `0/1`.

**Polling evidence.** Microsoft defines IncomingMessages and IncomingBytes on the Data insights tab as values over a period, not cumulative totals (Learn, "Monitor status and performance of an eventstream", updated Mar 19, 2026). On the one-hour chart the value sits at 2.52K messages and 2.2 MB from about 20:27 to 20:40 IST, falls to 0 when the eventstream is deleted at 20:40, and returns to about 2.5K from 20:53 after it is restored at about 20:51 and runs again. One poll is about 2,521 events (the station count read on Oct 28), so about one poll in each one-minute point of the chart, which matches the 60 s interval and works out to about 3.6 million events a day. The chart's point spacing of one minute is read off the screenshots, not from a Microsoft page, which gives no granularity.

**What is not proven.** The preview does not separate polls: the eight rows seen at 20:29:40 IST all had `last_reported` around 20:25, so it shows a sample, not the newest rows. Why the chart climbs over three minutes at each start instead of jumping to 2.5K is not explained. Why the chart shows 2.2 MB for 2.52K messages (about 870 bytes an event against about 428 in the raw file) is not explained. Whether a repeated station (same `last_reported`) arrives again is not checked; a dedup key is a silver-layer decision.

## R2 and R9 spike result (T014, Oct 28, 2026): route found, recipient kept out of Git

R2: an Activator email to the tenant admin user, whose Entra contact Email is set to a plus form of the Gmail address, reached the Gmail inbox twice (a test alert and a live firing). The external Gmail address could not be picked as a recipient. Full account in ADR-016. T019 (Nov 3, 2026) closed R2 on route 2 of the order decided in advance.

R9: option C, decided by Bharat. An alert rule is built by hand in a workspace without a Git link, never in dev; the repo holds a runbook with a placeholder recipient. R9 stays `open` until T086 scans the repo.

## R3 spike result (T015, Oct 30, 2026): met, and resolved by a different fallback

R3 came true. One Copy from the HTTP source with Binary and ZipDeflate failed with `UserErrorSourceNotSeekable`: the HTTP source does not support random read, and unzipping needs it. The notebook fallback in the R3 row is not used. Bharat chose the workaround that Microsoft's own error message names, ADR-027 option (a): `cp_trips_stage` copies the zip as plain Binary to `Files/bronze/_staging/trips/month=YYYYMM/`, then `cp_trips_unzip` unzips it into `Files/bronze/trips/month=YYYYMM/` with the preserve-name tick off. Both are pipeline Copy activities, so no Spark session sits in the trip path. T019 recorded R3 as resolved by ADR-027.

Two months ran. 2026-04 (164.6 MB zip): 23 s and 25 s, 4 CSVs, 753.5 MB written. 2026-06 (1.051 GB zip): 63 s and 31 s, 6 CSVs, about 1.0 GB. The zip-to-CSV ratio is not constant and the cause is not established. The connection address needs its trailing slash (a 404 without it), which T026 carries. ADR-006, T026 and `docs/data-contracts.md` section 1 were edited in T015 to match.

## R4 spike result (T016, Nov 3, 2026): a plain import of the Git file works

The loader in `tests/conftest.py` imports `fabric/nb_lib_common.Notebook/notebook-content.py` as a module with `importlib.util.spec_from_file_location`, and the 8 tests in `tests/test_lib_smoke.py` pass against it. T019 (Nov 3, 2026) closed R4. The cell-extract fallback is not taken; it stays in the loader as a guard.

**What the file looks like.** Fabric wrote it on the commit of Nov 3 (`de9e688`): the line `# Fabric notebook source`, a `# METADATA ****` block holding `kernel_info` (`synapse_pyspark`) and empty `dependencies`, then `# CELL ****`, the cell's code, and a second `# METADATA ****` block with `language` and `language_group`. Every marker is a comment, so Python compiles the file as it is. No lakehouse id or workspace id is in the file because the notebook had no default lakehouse attached. The file arrived with Windows line endings (CRLF) in Bharat's clone; Python reads them without trouble.

**Loader approach: plain import first, cell-extract only as a fallback.** `load_notebook(name)` checks the header line, then imports the file under the notebook's own name (the file name `notebook-content.py` has a hyphen, so a normal `import` statement cannot name it). If compiling fails with a `SyntaxError`, it writes the code cells (text between `# CELL ****` and the next marker, minus lines starting with `%` or `!`) to a temporary module and imports that instead. The loaded module carries `_loaded_by`, and one test asserts it is `"plain"` for the real file, so a future notebook that needs the fallback shows up in CI instead of passing quietly. The fallback is proven only on a made-up file with a bare `%run` line. How Fabric writes magic and markdown cells in the Git file (I expect `# MAGIC` comment lines, so they would not break a plain import) was not seen in this spike and is unverified until a notebook with a `%run` cell is committed.

**Run.** In my cloud workspace, in a scratch virtual environment: pyspark 4.1.4, Java 21, Python 3.13.18, a local Spark session with the time zone set to UTC as in `env_citibike`. 8 passed. Nothing was installed on the laptop or in the repo. Fabric Runtime 2.0 is Spark 4.1 (ADR-024), so the pyspark line matches in major and minor version; Fabric's own Python version on that runtime was not checked, and T075 pins the CI versions.

**Not proven.** The function was never run inside Fabric (the notebook was not connected to a session), only locally. The tests cover one function, so they show the import route and the Spark session work, not that every later function in `nb_lib_common` will import the same way.

**Side finding, for ADR-026.** Bharat committed from Source control without typing a message, so Fabric's default `Committing 1 item from workspace <workspace id>` went to `origin/dev` of the public repo a second time (first time: T011).

## R5 spike result (T017, Nov 3, 2026): `availableNow` over a Files folder works as ADR-008 expects

R5 did not come true, so ADR-008's batch anti-join fallback is not taken. T019 (Nov 3, 2026) closed R5.

**What ran.** In `nb_spike_stream` (PySpark, Workspace default environment, `lh_bronze` attached as the default lakehouse), `spark.readStream.format("text").option("wholetext", True).load("Files/spike/in/")` selected `value` as `raw_json` and `_metadata.file_path` as `_source_file`, and wrote to the Delta table `spike_stream` with `checkpointLocation` `Files/_checkpoints/spike/`, `trigger(availableNow=True)` and `awaitTermination()`. The count and a count per file name were read back in a second cell.

**Counts.** Run 1 with two files (`spike_a.json`, `spike_b.json`, 8 lines each): 2 rows, one per file, so `wholetext` gave one row per file and not per line. After `spike_c.json` was added, run 2: 3 rows, one new, the other two not read again. Run 3 with no new file: 3 rows, still one per file. The streaming cell took 37 s on the first run (11 s of that was the session starting), 4 s on the second and 2 s on the third.

**What this shows.** The text source, `_metadata.file_path`, a checkpoint under `Files/_checkpoints/` and `availableNow` all work together in a Fabric notebook on Runtime 2.0, and a run with nothing new ends on its own and adds nothing. `nb_bronze_load_json` (ADR-008) can be written this way.

**Not proven.** Only three small files were used, so nothing is known about the speed of listing a large folder. A failure half way through a batch was not tried, so exactly-once behaviour after a crash is as Spark documents it, not something seen here. Whether `_metadata.file_path` is a full OneLake path or a relative one was not looked at (only the file name was shown, to keep the workspace id off the screen); `nb_bronze_load_json` should check this before it builds `_source_file` from it. Files re-uploaded under the same name were not tried. Nothing was run as a pipeline Notebook activity.

## R6 spike result (T018, Nov 3, 2026): all three reads work in dev

R6 did not come true, so none of its fallbacks (a Script activity for the cross-database read, pipeline parameters with deployment rules for the variables) is taken. T019 (Nov 3, 2026) closed R6.

**What ran.** In `ws-citibike-dev`: a notebook attached to `lh_silver` wrote the Delta table `spike_t` (3 rows). In `wh_gold`, with the `lh_silver` SQL analytics endpoint added to the Explorer through + Warehouses, `SELECT COUNT(*) AS n FROM lh_silver.dbo.spike_t;` returned 3. The warehouse got the table `dbo.spike_log (n int, logged_at datetime2(6))` and the procedure `dbo.usp_spike @n int`, which inserts `@n` and `SYSUTCDATETIME()`. The pipeline `pl_spike_sp` has one Stored procedure activity, `sp_log`, on the Warehouse connection `wh_gold (ws-citibike-dev)`. Run 1 passed the literal 7 and added one row. Run 2 passed `@length(pipeline().libraryVariables.vl_citibike_env_name)` as an Int32 parameter (12 s, Succeeded) and added a row with n = 3, which only the library value `dev` can produce. In the notebook, `notebookutils.variableLibrary.getLibrary("vl_citibike").env_name` and `notebookutils.variableLibrary.get("$(/**/vl_citibike/env_name)")` both printed `dev`. The syntax is in `docs/conventions.md` §3.

**One finding.** A pipeline names a variable added on its Library variables tab `<library>_<variable>`, so the expression is `libraryVariables.vl_citibike_env_name`. The first attempt used the plain name `env_name` and the editor refused it ("Parameter env_name was not found under pl_spike_sp"). The notebook uses the plain name. T026 and later pipelines should expect the prefixed form.

**Not proven.** Only the dev value set was read, so the `test` and `prod` sets are untested here (T077 chooses them by hand). The notebook ran interactively as Bharat; Microsoft's page says a service principal is not supported for the notebook utilities, so a scheduled notebook under another identity is open. Nothing ran as a pipeline Notebook activity. How long the SQL analytics endpoint takes to show a new lakehouse table was not measured: the count query ran about six minutes after the table was written and worked at once. A permissions banner ("limited functionality ... permissions are restricted") showed in the notebook and did not stop any cell.
