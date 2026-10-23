# EP08 · CI/CD and release

**Goal.** Every pull request is checked automatically, and releases move from dev to test to prod through the deployment pipeline with per-stage configuration.
**Done when.** v1.0.0 runs in prod on its schedules, and one later change has gone dev → test → prod the same way.

## FT23 · Continuous integration

### US026 · Every pull request checked
As a reviewer, I want tests and checks to run on every pull request, so that a broken function or a hard-coded value never reaches `main`.
- GitHub Actions runs on pull requests to `dev` and `main`; `main` cannot merge without green checks.

#### T075 · `.github/workflows/ci.yml`
- **Story:** US026
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T016, T028
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/conventions.md §3, §7; docs/risks.md R4
**Do**
1. One workflow, triggers: pull requests to `dev` and `main`, and pushes to `dev`.
2. Jobs: `tests` (Ubuntu, Java 17, Python 3.11, `pyspark` and `pytest` pinned, run `tests/`); `lint` (`ruff` on `tests/`, `tools/` and the notebook files); `json` (every `.json` and `.platform` file under `/fabric` parses); `no-hardcoding` (`tools/scan_hardcoded.py`: fails on the URLs and coordinates from `vl_citibike` found outside `vl_citibike`, `docs/`, `tests/`); `backlog` (`python tools/backlog.py check`).
3. Claude writes `tools/scan_hardcoded.py` and its own test.
4. Commit on a branch `ci-setup`; Bharat pushes it and opens a pull request into `dev`; all jobs green; merge.
**Acceptance**
- [ ] Five jobs green on the pull request; link in the Result line.
- [ ] A deliberately bad commit (a URL typed into a test notebook copy) fails `no-hardcoding`, then is reverted.
**Result:** —

#### T076 · Require the checks on `main`
- **Story:** US026
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 10 min
- **Sprint:** 5
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
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 5
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
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 5
- **Depends on:** T077
- **DP-700:** 1.2, 1.4
- **Status:** todo
- **Read first:** docs/decisions.md ADR-014, docs/conventions.md §5
**Do**
1. `pl_post_deploy` (built in dev, deployed to test): `sp_seed_config` (with `weather_backfill_start` from the library), `sp_dim_date`, refresh `df_weather_codes`, create the bronze folders if missing (a notebook cell), upload check for the seed file (fail with a clear message if absent).
2. Deploy dev → test again. In test: upload the seed CSV once, run `pl_post_deploy`, then `pl_backfill` (202604) and `pl_daily`.
3. `dq.usp_run_checks` passes in test.
**Acceptance**
- [ ] Test runs end to end from an empty state using only `pl_post_deploy`, `pl_backfill` and `pl_daily`.
- [ ] Every step that needed a hand action is in `docs/runbooks/release.md` (Claude writes it).
**Result:** —

#### T079 · Release v1.0.0 to prod
- **Story:** US027
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 5
- **Depends on:** T046, T066, T067, T072, T078
- **DP-700:** 1.2, 1.4
- **Status:** todo
- **Read first:** docs/runbooks/release.md, docs/runbooks/eventstream.md, docs/environments.md
**Do**
1. Pull request `dev` → `main`, checks green, merge. Claude prepares the tag; Bharat pushes `v1.0.0`.
2. Deploy test → prod. Set `vl_citibike` active value set to `prod`.
3. Follow `docs/runbooks/release.md`: seed file, `pl_post_deploy`, Eventstream from its runbook, OneLake availability and the `kql_station_status` shortcut, analyst access moved from dev to prod (T071 grants).
4. Run `pl_backfill` (2026-07 to 2026-09, unattended) and `pl_daily`.
5. Schedules: `pl_daily` 11:30 IST daily; `pl_monthly_trips` 07:00 IST on day 8. Note the time zone setting on the schedule.
6. Remove the analyst's dev access.
**Acceptance**
- [ ] Prod has about 13–14 million trips for Jul–Sep 2026; `dq.usp_run_checks` passes.
- [ ] The prod Eventstream is polling; schedules show their next run time.
- [ ] Tag `v1.0.0` on `main`.
**Result:** —

#### T080 · One change through the whole path
- **Story:** US027
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 5
- **Depends on:** T079
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/runbooks/release.md
**Do**
1. The change: a new warn rule in `nb_silver_trips` (rides with identical start and end coordinates but different station names; Claude explains why it matters).
2. Build in dev, commit, pull request `dev` → `main`, green, merge, deploy dev → test → prod, tag `v1.0.1`.
3. The next prod `pl_monthly_trips` (or a hand run for one month) records the new rule in `ctl.dq_result`.
**Acceptance**
- [ ] The rule appears in prod's `ctl.dq_result`; pull request, deployment history and tag are linked in the Result line.
**Result:** —
