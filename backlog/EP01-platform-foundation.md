# EP01 · Platform foundation and risk spikes

**Goal.** A Fabric trial capacity in Bharat's own tenant, three workspaces, the shared items, Git, and every risky feature proven before anything depends on it.
**Done when.** `ws-citibike-dev` is synced to GitHub, and every risk R1–R6 in `docs/risks.md` is closed or has its fallback recorded.

## FT02 · Tenant and capacity

### US002 · A free capacity I control
As the platform owner, I want a Fabric trial capacity in my own tenant, so that the whole build runs at ₹0 and I can change any tenant setting.
- The trial is active, its dates are written down, and the Capacity Metrics app reads it.

#### T003 · Sign in with the tenant account and switch on the tenant settings
- **Story:** US002
- **ADO:** #9
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** —
- **DP-700:** 1.1
- **Status:** done
- **Read first:** docs/environments.md §1, docs/decisions.md ADR-002
**Do**
1. In a private browser window, go to `https://app.fabric.microsoft.com` and sign in as `<tenant-admin-upn>` (never the Gmail address). Accept the free Fabric licence if offered.
2. Settings (gear) → Admin portal → Tenant settings. Check each setting below against Microsoft's current wording before changing it (ADE HQ rule 22), and set it to **Enabled for the entire organization**:
   - Users can create Fabric items
   - Users can try Microsoft Fabric paid features
   - Users can synchronize workspace items with their Git repositories
   - Users can sync workspace items with GitHub repositories
   - Users can create and use variable libraries (if listed)
   - Eventhouse and Real-Time Intelligence settings (if listed as off)
3. Leave every setting that sends data outside the tenant or turns on paid features (Copilot, Azure OpenAI) as it is.
4. Screenshot each changed setting.
**Acceptance**
- [x] Signed in as the tenant account; the free licence shows under Account manager.
- [x] Each setting above is enabled, with a screenshot filed in ADE HQ evidence.
- [x] `docs/environments.md` §1 still matches what was seen (fix it if not).
**Result:** Signed in with the tenant admin account, free licence active; creating items, trial, Git and GitHub sync and workspace creation already enabled org-wide (nothing changed); no variable-library or Eventhouse switch exists; service-principal workspace creation is Disabled (note for EP08)

#### T004 · Start the 60-day trial and record its dates
- **Story:** US002
- **ADO:** #10
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 15 min
- **Sprint:** 1
- **Depends on:** T003
- **DP-700:** 1.1
- **Status:** done
- **Read first:** docs/cost-and-capacity.md §1, §2, §6
**Do**
1. Account manager (the profile picture, top right) → **Start trial** (or Free trial).
2. In the region list choose **Central India** if it is offered; otherwise keep the default region. Write down which one.
3. Agree and start. Read the end date from Account manager.
4. Claude writes the start date, end date and region into `docs/cost-and-capacity.md` §6 and `docs/environments.md` §2, and works out the date seven days before the end (the last day for screenshots and publish).
**Acceptance**
- [x] Account manager shows the trial with days remaining.
- [x] §6 of the cost doc has the start date, end date and region.
- [x] No Azure subscription or payment method was asked for or attached (if one is asked for, stop: that is not the trial).
**Result:** Fabric trial active in Central India from Oct 26, 2026 (ends about Dec 25; last day for screenshots Dec 18). Met a refusal first (ADR-022, resolved by itself) and found the capacity is an F4, not F64 (ADR-023, Proposed)

#### T005 · Install the Capacity Metrics app and read a baseline
- **Story:** US002
- **ADO:** #11
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T004
- **DP-700:** 3.1
- **Status:** done
- **Read first:** docs/cost-and-capacity.md §5
**Do**
1. Install the Microsoft Fabric Capacity Metrics app from the Power BI apps marketplace (Apps → Get apps). Connect it to the trial capacity (the capacity id comes from Admin portal → Capacity settings → Trial).
2. Open the Compute page; note the CU % for the last day (it should be close to zero).
3. Screenshot the page.
**Acceptance**
- [x] The app opens and shows the trial capacity.
- [x] Baseline screenshot filed; the CU % is written in the Result line.
**Result:** Capacity Metrics app installed, trial capacity visible (F4, Central India); Compute page average 7.62%, peak 10.04%, no throttling. One practice notebook sitting used 33,937 of 34,705 CU-s, so the baseline is a sitting, not idle. The app loaded its data on its own after an initial credentials error.

## FT03 · Workspaces and shared items

### US003 · Isolated environments
As a developer, I want separate dev, test and prod workspaces with the same items, so that a change is proven before it reaches prod.
- Three workspaces exist on the trial capacity, in the domain Mobility, with the roles in `docs/environments.md`.

#### T006 · Create the three workspaces, their settings and the domain
- **Story:** US003
- **ADO:** #14
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T004
- **DP-700:** 1.1
- **Status:** done
- **Read first:** docs/environments.md §3, docs/conventions.md §1
**Do**
1. Workspaces → New workspace → `ws-citibike-dev`. Advanced → License mode **Trial**. Repeat for `ws-citibike-test` and `ws-citibike-prod`.
2. Admin portal → Domains → Create domain `Mobility`, then assign the three workspaces to it.
3. In `ws-citibike-dev` → Workspace settings → Data Engineering/Science → Spark settings: note the default pool (Starter pool) and runtime version, and leave them; the environment item (T009) sets what the project needs.
4. Workspace settings → OneLake: note the options shown (for DP-700), change nothing.
5. Repeat steps 3–4 reading only, in test and prod, to confirm the same defaults.
**Acceptance**
- [x] Three workspaces on the trial capacity, named exactly as in `docs/environments.md`.
- [x] Domain `Mobility` exists with the three workspaces in it.
- [x] The Spark and OneLake defaults seen are written in the Result line.
**Result:** Three workspaces (type Fabric Trial, F4 trial capacity, Central India) are in domain Mobility. Dev defaults seen, test and prod reported the same: Starter Pool (memory optimized, medium, 1-10 nodes), no default environment, Spark runtime 2.0 (Spark 4.1, Delta 4.2), which was recorded as a preview (corrected in T009: Microsoft's lifecycle page lists 2.0 as GA, see ADR-024); OneLake cache for shortcuts off, diagnostics off, no lifecycle rules. UI difference: 'License mode' is now 'Workspace type'; OneLake settings has General, Storage report and Lifecycle management pages.

#### T007 · Create the test analyst user and confirm the role map
- **Story:** US003
- **ADO:** #15
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 20 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 1.3
- **Status:** done
- **Read first:** docs/environments.md §1
**Do**
1. Microsoft Entra admin center (entra.microsoft.com, signed in as the tenant account) → Users → New user → Create new user: `analyst.region`, display name "Test Analyst", auto-generated password. Bharat keeps the password in his own password manager; it never goes into a chat or a file.
2. Sign in once as the analyst in a separate private window at `app.fabric.microsoft.com`, change the password, accept the free licence, sign out.
3. Give no workspace access yet (T071 does that).
**Acceptance**
- [x] The analyst user exists and has signed in once.
- [x] No password or token appears in any chat, file or screenshot.
**Result:** The test analyst user analyst.region (display name Test Analyst) exists as an enabled Member with 0 roles, 0 groups and no workspace access, and has signed in once at app.fabric.microsoft.com; its Account manager reads Free account and Start trial was not pressed. UI difference: the Entra menu path is Entra ID > Users > All users.

#### T008 · Create the lakehouses and the warehouse in dev, and upload the seed file
- **Story:** US003
- **ADO:** #16
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 20 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 2.2
- **Status:** done
- **Read first:** docs/decisions.md ADR-004, ADR-005; docs/data-contracts.md §1
**Do**
1. In `ws-citibike-dev`: New item → Lakehouse → `lh_bronze`. Leave "Lakehouse schemas" **unticked** (ADR-005). Repeat for `lh_silver`.
2. New item → Warehouse → `wh_gold`.
3. In `lh_bronze` → Files: create folders `bronze`, `seed`, `_checkpoints`. Upload `seed/wmo_weather_codes.csv` from the repo into `Files/seed/`.
**Acceptance**
- [x] `lh_bronze`, `lh_silver`, `wh_gold` exist in dev, lakehouses without schemas.
- [x] `Files/seed/wmo_weather_codes.csv` is in `lh_bronze`.
**Result:** lh_bronze and lh_silver (schemas off) and wh_gold exist in ws-citibike-dev; Files/seed/wmo_weather_codes.csv (770 B) is in lh_bronze beside bronze and _checkpoints; all three report collation Latin1_General_100_BIN2_UTF8 (workspace default, seen on the warehouse Advanced pane); no default semantic model is listed. Evidence in portfolio-hq.

### US004 · Versioned configuration
As a developer, I want Spark settings and environment values stored as items, so that they travel with deployment instead of living in people's heads.
- `env_citibike` and `vl_citibike` exist in dev with the values in `docs/conventions.md` §3.

#### T009 · Create the environment `env_citibike`
- **Story:** US004
- **ADO:** #18
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 1.1, 3.3
- **Status:** done
- **Read first:** docs/conventions.md §4
**Do**
1. `ws-citibike-dev` → New item → Environment → `env_citibike`.
2. Spark compute: runtime = the newest GA runtime offered (write the version down); pool = Starter pool.
3. Spark properties: add `spark.sql.session.timeZone = UTC`. No other properties yet (T044 adds table-level settings in code).
4. Public libraries: none (the standard runtime has `requests`).
5. Save and **Publish** (an environment is not used until published).
6. Workspace settings → Data Engineering/Science → Environment → set `env_citibike` as the workspace default.
**Acceptance**
- [x] `env_citibike` is published with runtime, pool and the time-zone property.
- [x] It is the default environment of `ws-citibike-dev`.
**Result:** env_citibike is published in ws-citibike-dev on Runtime 2.0 (Spark 4.1, Delta 4.2), chosen in ADR-024 because Microsoft lists 2.0 as GA and 1.3 as end of support announced, with the Starter Pool at default compute values, spark.sql.session.timeZone = UTC and no libraries, and it is the workspace default environment. UI differences: a new environment opens with 2.0 preselected; Spark properties is its own page under Spark compute (property chosen from a dropdown); the default switch is under Workspace settings, Data Engineering/Science, Spark settings, Environment tab; no Published message was captured (Publish greyed, no pending banner).

#### T010 · Create the variable library `vl_citibike` with its value sets
- **Story:** US004
- **ADO:** #19
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 40 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 1.2, 1.4
- **Status:** done
- **Read first:** docs/conventions.md §3
**Do**
1. `ws-citibike-dev` → New item → Variable library → `vl_citibike`.
2. Add each variable in `docs/conventions.md` §3 as type String, with the dev value as the default value set.
3. Add value sets `test` and `prod` with their values (only the variables that differ need overriding).
4. The Default value set cannot be renamed, so add a fourth value set `dev` with no overrides and make it the active one in this workspace (ADR-025). Save.
**Acceptance**
- [x] Twelve variables, four value sets (Default, `dev`, `test`, `prod`), values exactly as in the conventions table.
- [x] Active value set in dev is `dev`.
**Result:** vl_citibike in ws-citibike-dev: 12 String variables, value sets Default (dev values), dev (no overrides, active), test, prod; Default cannot be renamed so dev was added (ADR-025 b); tails of four long default URLs and the hourly list to be compared when the library is first committed to Git.

## FT04 · Source control

### US005 · Every Fabric item in Git
As a developer, I want the dev workspace synced to GitHub, so that every change has history and can be reviewed.
- `ws-citibike-dev` is connected to branch `dev`, folder `/fabric`, and its items are committed.

#### T011 · Connect `ws-citibike-dev` to GitHub and make the first workspace commit
- **Story:** US005
- **ADO:** #22
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T002, T008, T009, T010
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/decisions.md ADR-014, ADR-020; docs/conventions.md §7, §9
**Do**
1. GitHub → Settings (account) → Developer settings → Fine-grained tokens → Generate: repository access **only** `citibike-fabric-lakehouse`; permission Contents **Read and write**; expiry 90 days. Bharat copies it straight into Fabric in the next step; it is never pasted into a chat or a file.
2. `ws-citibike-dev` → Workspace settings → Git integration → GitHub → Add account (display name, the token, the repo URL) → Connect → branch `dev`, Git folder `fabric` → Connect and sync.
3. Source control pane → commit everything with the message `T011: first workspace commit`.
4. Claude reads the repo after Bharat runs `git -C D:\GitRepositories\citibike-fabric-lakehouse pull` and lists what Fabric wrote under `/fabric`.
**Acceptance**
- [ ] The workspace shows "Synced" with branch `dev`.
- [ ] `/fabric` on GitHub has folders for `lh_bronze`, `lh_silver`, `wh_gold`, `env_citibike`, `vl_citibike`.
- [ ] The token expiry date is in the Result line (renew before it).
**Result:** —

#### T012 · Protect `main` and `dev` on GitHub
- **Story:** US005
- **ADO:** #23
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 15 min
- **Sprint:** 1
- **Depends on:** T011
- **DP-700:** 1.2
- **Status:** done
- **Read first:** docs/conventions.md §7
**Do**
1. GitHub repo → Settings → Rules → Rulesets → New branch ruleset `protect-main`, target `main`: require a pull request before merging (0 approvals needed, since he is the only person), block force pushes, restrict deletions. Status checks are added in T076.
2. Ruleset `protect-dev`, target `dev`: block force pushes, restrict deletions. No pull request rule (Fabric commits straight to `dev`).
**Acceptance**
- [x] Both rulesets active.
- [x] A direct push to `main` is refused (Claude prepares an empty test commit on a throwaway branch; Bharat tries the push and pastes the refusal).
**Result:** Oct 24: repo made public (rulesets are not enforced on free private repos); protect-main (PR required, 0 approvals, no force push, no deletion) and protect-dev (no force push, no deletion) Active. A direct push of a test commit to main was refused with GH013 'Changes must be made through a pull request'. Done before T011, on Bharat's call.

## FT05 · Risk spikes

### US006 · Proven features before building on them
As the architect, I want each risky feature tried on a small case first, so that no build task is left half-done by a feature that does not work.
- Each spike records a pass or the fallback taken in `docs/risks.md` and `docs/decisions.md`.

#### T013 · Spike R1: the Eventstream HTTP source polls the station feed
- **Story:** US006
- **ADO:** #26
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 2.3
- **Status:** todo
- **Read first:** docs/risks.md R1, docs/sources.md §3, docs/decisions.md ADR-007
**Do**
1. In `ws-citibike-dev`: New item → Eventstream → `es_spike_http`.
2. Add source → HTTP (preview). Base URL `https://gbfs.lyft.com/gbfs/2.3/bkn/en/station_status.json`, authentication Anonymous, method GET, request interval 60 s, no pagination. If a "response data JSON pointer" option is offered without pagination, try `/data/stations` first.
3. Publish. Open the live data preview, wait three polls.
4. Record: is one event one poll (the whole file) or one station? Which fields does an event carry? How many events per poll?
5. Also open `system_regions.json` in a browser and note its fields (for T037).
6. Delete `es_spike_http` after the notes are taken (it must not stay polling).
**Acceptance**
- [ ] At least three polls seen in the preview, screenshot filed.
- [ ] Event shape written in `docs/risks.md` R1 (Claude writes it): per poll or per station, and the field list.
- [ ] `system_regions` fields written in `docs/sources.md` §3.
- [ ] The spike eventstream is deleted.
**Result:** —

#### T014 · Spike R2: find an alert route that reaches Bharat
- **Story:** US006
- **ADO:** #27
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/risks.md R2, R9; docs/decisions.md ADR-016
**Do**
1. Option 1: New item → Activator → `act_spike`. Source: Real-Time hub → Fabric events → Job events (or the sample data source if job events are not offered). Make a rule that fires on any event; action Email to `<alert-email>`. Start it and wait for a mail.
2. If the mail does not arrive in 10 minutes or the action is refused (for example "InvalidRecipientDomain"): Option 2: in Entra, set the tenant user's Contact information → Email to the Gmail address; change the action's recipient to the tenant user; test again.
3. If that fails too: Option 3: Claude writes a tiny pipeline `pl_spike_alert` with one Web activity that POSTs a message to a push-notification topic Bharat creates in a phone app; run it.
4. Stop and delete `act_spike` (and `pl_spike_alert` if made).
5. Decide with Bharat whether the alert address may appear in a public repo (R9).
**Acceptance**
- [ ] One route delivered a test alert to Bharat's phone or Gmail; screenshot of the received message filed.
- [ ] The working route and the publish decision for the address are written in ADR-016 by Claude.
- [ ] Spike items deleted.
**Result:** —

#### T015 · Spike R3: copy a zipped trip file from HTTP and unzip it into Files
- **Story:** US006
- **ADO:** #28
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T008
- **DP-700:** 2.2
- **Status:** todo
- **Read first:** docs/risks.md R3, docs/sources.md §4
**Do**
1. `ws-citibike-dev` → New item → Data pipeline → `pl_spike_zip`.
2. Copy activity. Source: connection type HTTP, URL `https://s3.amazonaws.com/tripdata/202604-citibike-tripdata.zip`, anonymous; file format **Binary**; compression type **ZipDeflate**. Destination: `lh_bronze` → Files → folder `bronze/trips/month=202604`; file format Binary; tick "preserve zip file name as folder" **off**.
3. Run. Note duration and bytes read.
4. Browse the folder: list the CSV names. Open one in the preview: note the header and two `started_at` values exactly as written (for T041).
5. Leave the files (T026 replaces them); delete `pl_spike_zip`.
**Acceptance**
- [ ] CSVs for 2026-04 sit in `Files/bronze/trips/month=202604/`, screenshot filed.
- [ ] The header and the timestamp text format are written in `docs/sources.md` §4 by Claude.
- [ ] Duration and size in the Result line.
**Result:** —

#### T016 · Spike R4: CI can import a notebook's Git file and test it
- **Story:** US006
- **ADO:** #29
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T011
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/risks.md R4, docs/conventions.md §4
**Do**
1. Bharat creates notebook `nb_lib_common` in dev with one code cell: a function `add_lineage_columns(df, source_file_col, run_id)` that Claude supplies, and commits it from Source control.
2. After `git pull`, Claude reads `fabric/nb_lib_common.Notebook/notebook-content.py` and writes `tests/conftest.py` with a loader that imports the notebook file as a module (and strips any magic lines if needed), plus `tests/test_lib_smoke.py` that builds a local Spark session and tests the function.
3. Claude copies the repo's `fabric/` and `tests/` into its own cloud workspace and runs the tests there (Java, `pyspark` and `pytest` installed in that workspace, never on the laptop or into the repo). CI (T075) runs the same tests on GitHub.
**Acceptance**
- [ ] `pytest` passes locally against the file Fabric wrote.
- [ ] The loader approach is written in `docs/risks.md` R4 (plain import, or the cell-extract fallback).
**Result:** —

#### T017 · Spike R5: Structured Streaming `availableNow` over a Files folder
- **Story:** US006
- **ADO:** #30
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T008, T009
- **DP-700:** 2.3
- **Status:** todo
- **Read first:** docs/risks.md R5, docs/decisions.md ADR-008
**Do**
1. Upload two small JSON files (Claude provides them) into `lh_bronze/Files/spike/in/`.
2. Notebook `nb_spike_stream` (attached to `lh_bronze`): `spark.readStream.format("text").option("wholetext", True).load("Files/spike/in/")` with `_metadata.file_path`, write to Delta table `spike_stream` with checkpoint `Files/_checkpoints/spike/` and `trigger(availableNow=True)`. Run: 2 rows.
3. Upload a third file, run again: exactly 1 new row. Run a third time with no new file: 0 new rows.
4. Drop the table, delete the spike folder and checkpoint, delete the notebook.
**Acceptance**
- [ ] Row counts 2 → 3 → 3 across the three runs, screenshot filed.
- [ ] Result recorded in R5; if it failed, ADR-008's fallback is marked as taken.
**Result:** —

#### T018 · Spike R6: warehouse reads silver, a pipeline runs a procedure, and the variable library resolves
- **Story:** US006
- **ADO:** #31
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T008, T010
- **DP-700:** 1.4, 2.2
- **Status:** todo
- **Read first:** docs/risks.md R6
**Do**
1. Notebook (attached to `lh_silver`): create a tiny Delta table `spike_t` with three rows.
2. `wh_gold` → New SQL query: `SELECT COUNT(*) FROM lh_silver.dbo.spike_t;` (cross-database query). Create `dbo.usp_spike @n int` that inserts into a table `dbo.spike_log`.
3. Pipeline `pl_spike_sp`: Stored procedure activity on `wh_gold` calling `dbo.usp_spike` with `@n` taken from the variable library (`env_name` length, or any value): add `vl_citibike` under the pipeline's Library variables and reference it in the parameter.
4. Notebook cell: read `env_name` from `vl_citibike` with `notebookutils` (Claude gives the call after checking Microsoft's page) and print it.
5. Clean up: drop `spike_t`, `spike_log`, `usp_spike`; delete the pipeline and notebook.
**Acceptance**
- [ ] The cross-database query returns 3.
- [ ] The pipeline run is green and `spike_log` got its row.
- [ ] The notebook printed `dev` from the variable library.
- [ ] The exact syntax that worked for both variable-library reads is written in `docs/conventions.md` §3 by Claude.
**Result:** —

#### T019 · Close the spikes: record outcomes and adjust affected cards
- **Story:** US006
- **ADO:** #32
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 1
- **Depends on:** T013, T014, T015, T016, T017, T018
- **DP-700:** —
- **Status:** todo
- **Read first:** docs/risks.md, docs/decisions.md
**Do**
1. Mark R1–R6 closed or "fallback taken" in `docs/risks.md`.
2. Write the outcomes into ADR-007, ADR-008, ADR-016.
3. If any fallback was taken, edit only the cards it affects (named in the risk row) and list the edits in the Result line. A fallback that changes the architecture goes to Bharat first.
4. `tools/backlog.py check`, commit.
**Acceptance**
- [ ] No R1–R6 row says "open".
- [ ] Every affected card is updated and named in the Result line.
**Result:** —
