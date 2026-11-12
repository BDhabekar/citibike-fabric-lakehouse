# EP08 · CI/CD and release

**Goal.** Every pull request is checked automatically, and releases move from dev to test to prod through the deployment pipeline with per-stage configuration.
**Done when.** The weather slice runs in prod on its schedule as `v0.1.0`, and version 1.0 has gone dev → test → prod the same way as `v1.0.0`.

## FT23 · Continuous integration

### US026 · Every pull request checked
As a reviewer, I want tests and checks to run on every pull request, so that a broken function or a hard-coded value never reaches `main`.
- GitHub Actions runs on pull requests to `dev` and `main`; `main` cannot merge without green checks.

#### T075 · `.github/workflows/ci.yml`
- **Story:** US026
- **ADO:** #133
- **Owner:** Claude builds
- **Estimate:** 60 min
- **Sprint:** 4
- **Depends on:** T016
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/conventions.md §3, §7; docs/risks.md R4; docs/decisions.md ADR-024
**Pass B (ADR-029).** `tests/test_http.py` (T028) arrives with version 1.1; the `tests` job runs whatever is in `tests/`, so nothing here waits for it.
**Do**
1. One workflow, triggers: pull requests to `dev` and `main`, and pushes to `dev`.
2. Jobs: `tests` (Ubuntu, `pyspark` and `pytest` pinned, run `tests/`; Fabric runs Runtime 2.0, so pin `pyspark` to Spark 4.1 and choose Java and Python versions that match it or write down why not; the test Spark session sets `spark.sql.ansi.enabled` to false, because Fabric turns it off where open-source Spark 4.1 turns it on; ADR-024); `lint` (`ruff` on `tests/`, `tools/` and the notebook files); `json` (every `.json` and `.platform` file under `/fabric` parses); `no-hardcoding` (`tools/scan_hardcoded.py`: fails on the URLs and coordinates from `vl_citibike` found outside `vl_citibike`, `docs/`, `tests/`); `backlog` (`python tools/backlog.py check`).
3. Claude writes `tools/scan_hardcoded.py` and its own test.
4. Commit on a branch `ci-setup`; Bharat pushes it and opens a pull request into `dev`; all jobs green; merge.
**Acceptance**
- [ ] Five jobs green on the pull request; link in the Result line.
- [ ] A deliberately bad commit (a URL typed into a test notebook copy) fails `no-hardcoding`, then is reverted.
**Result:** —

#### T076 · Require the checks on `main`
- **Story:** US026
- **ADO:** #134
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 10 min
- **Sprint:** 4
- **Depends on:** T012, T075
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/conventions.md §7
**Do**
1. Ruleset `protect-main` → Require status checks to pass → add the five job names.
**Acceptance**
- [ ] A pull request into `main` shows the five required checks.
**Result:** —

## FT24 · Deployment

### US027 · Promotion with per-stage configuration
As a release manager, I want items promoted dev → test → prod with each stage using its own values, so that prod changes only through a tested path.
- `dp-citibike` has three stages; each stage's variable library value set is right; the test stage passes a smoke run before prod.

#### T077 · Deployment pipeline `dp-citibike`
- **Story:** US027
- **ADO:** #137
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 45 min
- **Sprint:** 4
- **Depends on:** T010, T064
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/environments.md §3–4, docs/decisions.md ADR-014
**Do**
1. Workspaces → Deployment pipelines → New: `dp-citibike`, stages Development, Test, Production; assign the three workspaces.
2. Compare dev with test; deploy all items except `es_station_status` to Test.
3. In `ws-citibike-test`, open `vl_citibike` and set the active value set to `test`.
4. Check each notebook's default lakehouse in test points at test's `lh_bronze`/`lh_silver` (Claude explains auto-binding); add a deployment rule only where it did not bind.
**Acceptance**
- [ ] Test holds every item except the Eventstream; its active value set is `test`.
- [ ] Every notebook in test is bound to test's lakehouses (screenshot of one).
**Result:** —

#### T078 · `pl_post_deploy` and a smoke run in test
- **Story:** US027
- **ADO:** #138
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 60 min
- **Sprint:** 4
- **Depends on:** T077
- **DP-700:** 1.2, 1.4
- **Status:** todo
- **Read first:** docs/decisions.md ADR-014, docs/conventions.md §5
**Do**
1. `pl_post_deploy` (built in dev, deployed to test): `sp_seed_config` (with `weather_backfill_start` from the library), `sp_dim_date`, create the bronze folders if missing (a notebook cell), upload check for the seed file (fail with a clear message if absent).
2. Deploy dev → test again. In test: upload the seed CSV once, run `pl_post_deploy`, then `pl_daily`. (`pl_backfill` for 202604 joins the test run in T080; the `df_weather_codes` refresh joins `pl_post_deploy` in T056, version 1.1.)
3. `dq.usp_run_checks` passes in test.
**Acceptance**
- [ ] Test runs end to end from an empty state using only `pl_post_deploy` and `pl_daily`.
- [ ] Every step that needed a hand action is in `docs/runbooks/release.md` (Claude writes it).
**Result:** —

#### T079 · First release to prod: the weather slice, `v0.1.0`
- **Story:** US027
- **ADO:** #139
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 60 min
- **Sprint:** 4
- **Depends on:** T046, T067, T078, T082
- **DP-700:** 1.2, 1.4
- **Status:** todo
- **Read first:** docs/runbooks/release.md, docs/runbooks/eventstream.md, docs/environments.md
**Pass B (ADR-029).** The first of two releases. It takes the weather path, the checks, the alert, the first report pages and the live poller to prod. Trips, stations, security and the backfill follow in T080 as `v1.0.0`, which is version 1.0.
**Do**
1. Pull request `dev` → `main`, checks green, merge. Claude prepares the tag; Bharat pushes `v0.1.0`.
2. Deploy test → prod. Set `vl_citibike` active value set to `prod`.
3. Follow `docs/runbooks/release.md`: seed file, `pl_post_deploy`, Eventstream from its runbook. Two streams (dev and prod) now poll on the same 4 CU: read the Capacity Metrics app against the number from T047 before leaving both on, and stop the dev one if they do not fit (it is needed again for T048 to T050).
4. Run `pl_daily`.
5. Schedule: `pl_daily` 11:30 IST daily. Note the time zone setting on the schedule.
6. Open `rpt_citibike_ops` in prod and check both pages.
**Acceptance**
- [ ] Prod has weather hours from the backfill start to the archive's last hour; `dq.usp_run_checks` passes.
- [ ] The prod Eventstream is polling; the `pl_daily` schedule shows its next run time.
- [ ] Both report pages render in prod with data; screenshots filed.
- [ ] Tag `v0.1.0` on `main`.
**Result:** —

#### T080 · One change through the whole path
- **Story:** US027
- **ADO:** #140
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 75 min
- **Sprint:** 5
- **Depends on:** T049, T066, T072, T079
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/runbooks/release.md
**Pass C (ADR-029).** The second release, and the one that makes version 1.0: trips, stations, security, the live view and the demand page go to prod through the path T079 used first. The small change of step 1 rides along, so one rule can be followed from dev to prod's `ctl.dq_result`.
**Do**
1. The change: a new warn rule in `nb_silver_trips` (rides with identical start and end coordinates but different station names; Claude explains why it matters).
2. Claude adds `dim.station`, `dim.region` and `fact.trip` to `sm_citibike` with their relationships and the measures Trips, Member share, Avg duration min and Wet-hour trips share, and the trip visuals to the report page **Demand and weather** (moved here from T081 and T082 by ADR-029). Bharat pushes and presses Update all.
3. Commit, pull request `dev` → `main`, green, merge, deploy dev → test. In test: `pl_post_deploy`, `pl_backfill` (202604), `pl_daily`; `dq.usp_run_checks` passes.
4. Deploy test → prod. Follow `docs/runbooks/release.md`: analyst access moved from dev to prod (T071 and T072 grants), then remove the analyst's dev access.
5. Run `pl_backfill` in prod (2026-07 to 2026-09, unattended). Schedule `pl_monthly_trips` 07:00 IST on day 8.
6. Claude prepares the tag; Bharat pushes `v1.0.0`.
**Acceptance**
- [ ] Prod has about 13–14 million trips for Jul–Sep 2026; `dq.usp_run_checks` passes for both scopes.
- [ ] The new rule appears in prod's `ctl.dq_result`.
- [ ] The analyst signs in to prod and sees one region; the dev grant is gone.
- [ ] **Demand and weather** renders in prod with trips; `rtd_citibike_live` shows live data in prod.
- [ ] Tag `v1.0.0` on `main`; pull request, deployment history and tag are linked in the Result line.
**Result:** —
