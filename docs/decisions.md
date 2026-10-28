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

## ADR-016 · Failure alert route: an Activator email to the tenant user, recipient kept out of Git (Decided: option C, found in T014)
**Status.** Decided Wed Oct 28, 2026, about 22:58 IST. The route came out of the spike; the Git question (R9) was Bharat's call, option C. His reply was "Option C it is then".
**Order tried** (unchanged from the plan). (1) Activator email to an external address. (2) Activator email to the tenant user, with that user's contact email set to his Gmail. (3) Pipeline failure path calling a Web activity to a phone push service.
**What the spike showed** (Oct 28, 2026, in `ws-citibike-test`, on Activator's sample stream, rule condition "On every value").
- Route 1 failed on the screen. The To box of the email action is a picker of tenant users. Bharat's personal Gmail gave "no match in the list", so it could not be chosen (his report, no screenshot). That matches Microsoft's Activator limitations page, which was read only as a search snippet: a recipient must be in the creator's domain or a verified domain of the tenant, and external and guest addresses are not allowed.
- Route 2 delivered. The admin user's Contact information Email in Entra was set to a plus form of the Gmail address (evidence T014-3). The plus form is deliberate: the plain address already belongs to the Gmail guest user in the tenant, and Microsoft's troubleshooting page lists an error for two users sharing one address. Whether the plain address would have failed was not tested. The picker showed one chip for the admin user, and its hover read the plus address (T014-5). "Send me a test alert" at 22:47 IST and a live firing at 22:49 IST (activation 17:19:02 UTC) both reached the Gmail inbox, not spam, from `microsoft-noreply@microsoft.com` (T014-6, T014-7).
- Route 3 was not needed; `pl_spike_alert` was not built.
**Decision.** (1) The route is an Activator email action whose recipient is the tenant admin user, picked from the list. Its Entra Email stays set to the plus form (`docs/environments.md` §1). (2) R9, option C: an alert rule is built by hand in a workspace with no Git link (`ws-citibike-prod`, or `ws-citibike-test` while testing) and never in `ws-citibike-dev`. The repo holds a runbook of the rule's settings with `<alert-recipient>` as the recipient. Reason: a rule's recipient is stored as plain text in the item's `ReflexEntities.json` (Microsoft's Reflex definition page, updated Mar 4, 2026), and the tenant sign-in name ends in a domain that carries his Gmail handle. What a route 2 rule stores there was not looked at.
**Turned down.** (A) Commit the rule with his real recipient: puts the handle into public history and breaks START-HERE. (B) A neutral alert user as the recipient: the tenant domain still ends up in the file. (D) A placeholder swapped at deploy: no Fabric setting known, unverified.
**Consequence.** The rule is not versioned code, a named exception; the README's "what I would do at scale" says the rule lives in Git with a shared mailbox as recipient. T050 and T067 carry a note: no Activator rule with a recipient is built in dev. T086 scans the repo for `ReflexEntities.json`. Email is capped at 30 per rule per recipient per hour (Microsoft), so a rule fires on a condition, never on every value. **Not proven:** the spike used the sample stream, so a trigger from Fabric job events or from a pipeline failure path is still untested; delivery is the part that is proven. The test alert always goes to the rule's creator.

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

## ADR-022 · Fabric trial refused in the new tenant (Proposed, found in T004)
**Status.** Resolved Oct 26, 2026. The trial started on its own overnight (capacity created about 02:21 IST, after the refusal at 00:37 and with no change to any setting). Bharat's own account of what he did is not recorded here.
**Context.** On Mon Oct 26, 2026 the trial would not start in the tenant `bharat-ade` (created Sep 10, 2026, 46 days old). "Start trial" with "Fabric and Power BI" starts only a Power BI trial and says a Fabric trial isn't available for the account. "Start Fabric trial" afterwards, and creating a Fabric item in My workspace, fail with "unable to start trial at this time" (status code 200; the tracking IDs are held in ADE HQ evidence, not in this repo). Checked and ruled out: Fabric tenant settings "Users can create Fabric items" and "Users can try Microsoft Fabric paid features" are on for the entire organization; the Trial capacities list is empty; the home region is Central India, a region where trials are offered; the Fabric, Fabric Trial and Power BI Premium workspace types are all disabled. No Azure subscription or payment method was asked for.
**Cause.** Not confirmed by Microsoft. The tenant-age idea below did not hold: the tenant was 46 days old when the trial started. The two community reports were about a recently created tenant; a provisioning delay fits better. Earlier note on the reports: Two community threads on newly created tenants report the same refusal. One says the tenant or account must be 90 days old (which would be Dec 9, 2026 here), another says provisioning can take 24 to 48 hours. Neither is Microsoft documentation. Microsoft's own trial page does not name a tenant-age rule.
**Support.** The Fabric support ticket form needs a paid support plan, which breaks the ₹0 rule. Route instead: a post in the Microsoft Fabric Community forum with the error details.
**Options.** (a) Retry "Start Fabric trial" daily and post to the community forum; work on nothing that needs a live workspace until it starts. (b) If the tenant-age rule is real, reorder the backlog so Fabric-free work (SQL, KQL and Python written locally, tests, CI, docs) comes first, and move the DP-700 date. (c) Use a different, older tenant. Rejected so far by `docs/environments.md` (employer, relative and student tenants are never used). (d) A pay-as-you-go F2 capacity. Breaks the ₹0 rule; only by written decision (`docs/cost-and-capacity.md` §3–4).
**Recommendation.** (a) now, with (b) prepared. Decide on (c) or (d) only if the trial has not started by about Nov 2.
**Consequence if the 90-day rule holds.** The trial would start about Dec 9 and end about Feb 7, 2027, after the planned DP-700 window of Dec 7–12.

## ADR-023 · The trial capacity is an F4, not an F64 (Proposed, found in T004)
**Status.** Proposed. Bharat decides. Does not block T004.
**Context.** The Admin portal (Capacity settings, Trial) shows one trial capacity in Central India with 4 capacity units, "the equivalent to an F4", and says its size cannot be changed. The docs assumed 64 CU (an F64) when they said capacity was "plenty" (`docs/cost-and-capacity.md` §1, §2, §5). Microsoft's trial page describes sizes from 4 to 64 CU, so 4 is the low end of that range.
**Why it matters.** The design includes a continuous Eventstream, a Kusto Eventhouse, a warehouse, Spark notebooks and a semantic model, all in the same capacity across dev, test and prod. On 4 CU, concurrent jobs can throttle, and the fix recorded in §5 ("fewer concurrent jobs, not a bigger capacity") may become the normal way of working.
**Options.** (a) Carry on and measure: T005 installs the Capacity Metrics app, and the first heavy spikes (T013, T015) show real load against 4 CU before anything is decided. (b) Ask whether a larger size is possible through the Fabric Community forum. (c) Cut the load: one workspace on the capacity at a time, Eventstream stopped outside prod, smaller months in dev and test (already planned in ADR-021). (d) A paid F-size capacity. Breaks the ₹0 rule; only by written decision.
**Recommendation.** (a), with (c) as the working habit. Revisit at T015 if jobs throttle.

## ADR-024 · Spark runtime for `env_citibike`: 2.0 (GA) or 1.3 (support ending) (Decided: 2.0, found in T009)
**Status.** Decided Tue Oct 27, 2026, 21:45 IST: option (a), Runtime 2.0. Bharat's reply was "A". T009 builds `env_citibike` on 2.0.
**Context.** `docs/environments.md` §3 and the T006 Result say Runtime 2.0 is a preview and that T009 must set "GA 1.3". Microsoft's pages read on Oct 27, 2026 say otherwise. The lifecycle page (last updated Jul 29, 2026) lists Runtime 2.0 (Spark 4.1) as GA with end of support Aug 31, 2028, and Runtime 1.3 (Spark 3.5) as "end of support announced": it enters Long Term Support on Oct 1, 2026 and is supported through March 2027. The Runtime 2.0 page (updated Oct 22, 2026) calls it the latest GA and the default for new workspaces and environments, which matches the workspace default seen in T006. The older reading most likely came from a stale copy of the lifecycle page (copies in other locales still show 1.3 as GA); not confirmed. After end of support, Microsoft removes the runtime from environments and existing environments on it stop running. The card's own rule is "the newest GA runtime offered", so the card is met by either reading of the facts; what changes is the value the docs promised.
**What 2.0 changes for this project** (Microsoft's migration guide, updated Oct 23, 2026; Delta interoperability page, updated Oct 7, 2026). Spark 4.1.1, Delta 4.2, Python 3.13, Java 21. New Delta tables default to reader 3 / writer 7 with deletion vectors on; the SQL analytics endpoint, Direct Lake models and Fabric Spark read deletion vectors, while pipeline Copy and Lookup activities and Eventstreams do not. This project's pipelines copy files into `Files/`, not Delta tables, so no planned path reads a Delta table with a pipeline activity (checked against EP02 to EP08 on Oct 27). `spark.sql.ansi.enabled` stays false in Fabric. The Event Hubs connector is gone; the project does not use it. Runtime 2.0 removes many preinstalled Python packages; `requests` is not on the removed list, and no library is installed in this project.
**Options.** (a) Runtime 2.0, the GA default, supported to Aug 2028. A production team builds on the GA runtime that is not about to leave support. Cost: CI test pins (T075 says Java 17, Python 3.11, a pinned `pyspark`) must be set to match Spark 4.1 instead of 3.5, and table-feature settings in T044 and the maintenance task EP03 are chosen against Delta 4.2 defaults. (b) Runtime 1.3, as the docs said. Simpler Delta defaults (reader 1 / writer 2), but its support ends in March 2027 and an environment still on it stops running after that, so the portfolio would need a rebuild on 2.0 anyway. (c) 1.3 now and move to 2.0 later. Same cost as (b) plus a migration the project has no room for.
**Recommendation.** (a). Production-grade choice, and the default Microsoft ships.
**Consequence if (a).** T009 selects 2.0 and writes the exact label seen. `docs/environments.md` §3 and the START-HERE line for T006 are corrected. T075's pins are aligned to Spark 4.1 when T075 is done (note added to its card). The table-feature choices in T044 and EP03 check the 2.0 defaults first.
**Consequence if (b) or (c).** T009 selects 1.3; a task is added before Mar 2027 to move the environment to 2.0; the README names the support end date as a known limit.


## ADR-025 · The dev workspace has no value set called `dev` (Decided: option b, found in T010)
**Status.** Decided Tue Oct 27, 2026, about 22:25 IST: option (b). Bharat added the `dev` value set and made it active (screenshot T010-2) after reading the options; the card's "three value sets" now reads four.
**Context.** The card says to put the dev values in the default value set and then "make `dev` the active value set", with the acceptance line "Active value set in dev is `dev`". `docs/environments.md` §3 lists `dev`, `test` and `prod` as the active set per stage. Microsoft's pages describe a Default value set that is always present plus alternative sets you add. Bharat's screen of Oct 27, 22:18 IST shows exactly that: the set is labelled "Default value set" with the Active badge, and its three-dots menu offers only "Set as active", so it cannot be renamed. `test` and `prod` exist and are built as the conventions table says. No set named `dev` exists.
**Why it matters.** Microsoft says the active choice is workspace state and that a workspace created by a deployment starts on Default, so a stage that is not switched silently reads the dev values (the three backfill variables and `env_name` would be wrong in prod). EP08 already sets and checks the active set per stage by hand (T077 and the two cards after it), which covers this either way. The open point is only how dev's own set is named.
**Options.** (a) Keep it as built: the Default value set holds the dev values and is dev's active set. Nothing to add. The acceptance line is reworded to "active value set in dev is Default", and `docs/environments.md` §3 row is reworded the same way. Cost: dev is the only stage whose active set is not named after its stage, so a check of the form "active set equals stage name" does not work. (b) Add a fourth value set `dev` that overrides nothing (every cell points at the default) and make it active in dev. Every stage then names its own set, the §3 table holds as written, and a stage that still shows Default is visibly wrong. Cost: the library has four value sets, so the acceptance line "three value sets" becomes four, and one more set exists that must stay empty. (c) Put neutral values in the default and give dev its own full set. Rejected for now: it changes what the conventions table says the default holds.
**Recommendation.** (b). A production team names every stage's set explicitly so that "active set = stage" can be checked everywhere, and (b) changes the fewest documents (only the card's "three"). (a) is the pattern in Microsoft's own tutorial and is acceptable if you prefer no empty set.
**Consequence if (b).** Bharat adds `dev` (Add value set, tick "Set as active", Save) and sends one screenshot; the card's acceptance reads "four value sets (Default, `dev`, `test`, `prod`)"; nothing else changes.
**Consequence if (a).** The card and `docs/environments.md` §3 are reworded; T010 can be closed on the screen already filed.

## ADR-026 · Fabric's first commit put the workspace id in the public history (Decided: option A, found in T011)
**Status.** Decided Wed Oct 28, 2026, 19:49 IST: option (A). Bharat's reply was "A is fine for me if it is not a credential and if it does not harm anything"; the answer to those two conditions is under Context.
**Context.** Connecting `ws-citibike-dev` to `dev`/`fabric` made Fabric copy the workspace into the empty folder and commit it by itself (commit `c6323fb`, Oct 28, 2026, 19:41 IST), with its default message "Committing 5 items from workspace" followed by the workspace's id. The repo is public, and the rule in START-HERE says no tenant or workspace ids. Checked on GitHub: the author and committer are the repo's noreply address, and the files hold no email address and no tenant name, only each item's own `logicalId`. So the id sits in one commit message only. It is an identifier, not a credential: it signs nothing in and authorises nothing by itself; Fabric actions need a Microsoft Entra sign-in and a role in the workspace (taken from how Fabric access works, not checked against a Microsoft page in this task). What it can do is tell a reader that this workspace exists and what an id looks like. No cost, no data and no access is affected.
**Options.** (A) Leave the commit and name it as an exception here. (B) Reword `c6323fb` and force-push `dev`: the `protect-dev` ruleset has to be lifted, the workspace's last-synced commit disappears so the connection may need a disconnect and reconnect, and GitHub keeps the old commit reachable by its hash for a while, so the id would not be fully gone.
**Decision and reason.** (A). A production team does not rewrite a shared branch for an identifier that is not a credential, and (B) risks the connection for a partial result. The prevention is the part that matters.
**Consequence.** Every Fabric commit from the Source control pane gets a typed message of the form `T0xx: <what changed>` (`docs/conventions.md` §7, which already says so); the default message is never accepted. The first sync of a connection commits by itself with the default message, so a new connection (a new workspace, or a reconnect after a Git configuration change) is made only when the branch already holds the items, or the exception is named again. The id is not written in any file of this repo; it stays in the private evidence notes only as "the workspace id".
