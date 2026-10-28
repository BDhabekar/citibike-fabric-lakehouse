# Start here (every task chat reads this first)

This repo is the Citi Bike operations lakehouse on Microsoft Fabric, Bharat's second portfolio project after `olist-azure-lakehouse`. The design is locked; the work is a backlog of 89 tasks, and one chat does one task.

## Read in this order, and stop when you have what the task needs

1. This file.
2. `backlog/README.md`: the task-chat protocol (12 steps). Follow it exactly.
3. `python3 tools/backlog.py show T0xx`: your card, with its story and feature.
4. Only the files the card lists under **Read first**.
5. `D:\GitRepositories\portfolio-hq\INSTRUCTIONS.md` (teaching, building, cost and planning rules) the first time in a chat. Its rules apply here unless this repo says otherwise.

Do not read the other epic files, the whole data-contract file or the ADE HQ trackers unless the card says so. That is what keeps a task chat small enough for Sonnet.

## The rules that matter most

- **Build what the card says.** Names, columns, tools and layers come from `docs/architecture.md`, `docs/data-contracts.md` and `docs/conventions.md`. If reality disagrees, follow change control (`docs/architecture.md` §10): set the card `blocked`, write a Proposed decision, ask Bharat.
- **Cost.** Everything runs on the Fabric trial in Bharat's own tenant: ₹0. Anything that would create a paid resource, attach an Azure subscription or ask for a card stops the task.
- **Who does what.** Bharat builds in Fabric (pipelines, notebooks, KQL, T-SQL, deployment) and learns as he goes. Claude teaches, writes the docs, tests, CI, control and DDL scripts, the semantic model and the report, and does every file edit. Bharat never edits repo files.
- **Teach before building.** Every task starts with the full explanation the ADE HQ way (idea, in production, in an interview, steps with the screen each starts from, a small example, what done looks like). Correct any mistake before moving on.
- **Check Microsoft's page** before giving a step where a wrong setting costs time or data, and say where each portal step came from (a named page with its date, or "from memory, unverified").
- **Never push to `main` directly.** Before any commit, check the branch (`git -C D:\GitRepositories\citibike-fabric-lakehouse branch --show-current`); it must be `dev`. `main` changes only through a pull request from `dev`, and a GitHub ruleset enforces it.
- **The repo is public: no personal data.** No email addresses, sign-in names, employer or family names, tenant or workspace ids. Use the placeholders in `docs/environments.md` §1.
- **Secrets never enter a chat or a file.** Tokens and passwords go from Bharat's password manager straight into the Fabric or GitHub screen.
- **Evidence and notes** go to `D:\GitRepositories\portfolio-hq` (`citibike/evidence/`, `citibike/fabric-project-explained.md`), not to this public-bound repo.
- **Commit at the end of the task** on `dev` (`T0xx: ...`); give Bharat the push lines from `docs/conventions.md` §10.
- **Model.** Use the model on the card. If a task turns into an architecture question, say so, write a one-page brief, and let Bharat take it to a separate Opus chat.

## Where things are

| What | Where |
|---|---|
| Design | `docs/architecture.md` (start here), `docs/decisions.md` (ADRs), `docs/data-contracts.md`, `docs/conventions.md` |
| Sources | `docs/sources.md` |
| Environments and who can do what | `docs/environments.md` |
| Cost, trial dates, pay-as-you-go numbers | `docs/cost-and-capacity.md` |
| Risks and their fallbacks | `docs/risks.md` |
| DP-700 skill coverage | `docs/dp700-map.md` |
| Backlog | `backlog/EP*.md`, calendar in `backlog/sprints.md` |
| Fabric items (written by Fabric Git integration only) | `fabric/` |
| SQL and KQL scripts Claude writes | `sql/`, `kql/` |
| Tests and CI | `tests/`, `.github/workflows/` |
| Runbooks for hand-built items and releases | `docs/runbooks/` |

## Current state

*Updated by each task chat in its last step: one line, newest first.*

- Wed Oct 28, 2026 · T014 done: spike R2. Route 1 failed on the screen: the To box of an Activator email rule lists tenant users only and the personal Gmail gave "no match". Route 2 delivered: the tenant admin user's Entra contact Email is set to a plus form of the Gmail address (the plain one belongs to the Gmail guest user already in the tenant), and an Activator email to that user reached the Gmail inbox twice, as a test alert (22:47 IST) and as a live firing (22:49 IST); the events came from the sample stream, so a trigger from job events is not yet proven. ADR-016 decided: the alert rule is built by hand in a workspace without Git (prod, or test while testing), never in dev, because a rule's recipient is stored as plain text in the item definition (R9, option C); T050 and T067 carry a note. Spike items deleted; the Entra edit stays. R2 and R9 stay `open` until T019 and T086. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Wed Oct 28, 2026 · T013 done: spike R1. The Eventstream HTTP source polled `station_status.json` about every 60 s with the JSON pointer `/data/stations` (the box is offered with pagination off). One event is one station with 13 fields and no `last_updated`, `ttl` or `version`, so nothing in an event says which poll it came from. Data insights showed about 2,521 events a minute (about 3.6 million a day), stopping at the deletion and resuming after a restore; the preview shows only a sample, so the three polls are read from the chart, not the preview. `system_regions` has `region_id` and `name` (seven regions). `es_spike_http` deleted; the anonymous connection `conn_spike_gbfs` stays. R1's table status stays `open` until T019 records it in ADR-007. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Wed Oct 28, 2026 · T011 done: `ws-citibike-dev` connected to GitHub (`dev`, folder `fabric`) with a fine-grained token limited to this repo, expiry Jan 26, 2027 (renew before it). The first sync committed the five items on its own (`c6323fb`), so the typed commit message in the card was not used; Source control reads 0 changes and every item is Synced. `fabric/` holds `lh_bronze.Lakehouse`, `lh_silver.Lakehouse`, `wh_gold.Warehouse`, `env_citibike.Environment` and `vl_citibike.VariableLibrary`; `vl_citibike` matches `docs/conventions.md` §3 (the T010 gap is closed). Fabric's default commit message carries the workspace id, accepted once as ADR-026: every Fabric commit from now on is typed `T0xx: ...`. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T010 done: variable library `vl_citibike` created in `ws-citibike-dev` with twelve String variables and four value sets: Default (dev values), `dev` (no overrides, active), `test` and `prod`. Default cannot be renamed, so the `dev` set was added (ADR-025, option b; card and `docs/environments.md` §3 updated). The tails of four long default values were cut off on screen: compare them when the library is first committed to Git. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T009 done: `env_citibike` created and published in `ws-citibike-dev` on Runtime 2.0 (Spark 4.1, Delta 4.2) with the Starter Pool and `spark.sql.session.timeZone` = `UTC`, and set as the workspace default. Microsoft's lifecycle page lists 2.0 as GA and 1.3 as end of support announced (support through March 2027), so the "GA 1.3" in the docs was wrong; ADR-024 records the choice (option A). T075 (CI Spark pins and the ANSI setting) and T044 (read the 2.0 Delta defaults first) carry a note. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T008 done: `lh_bronze` and `lh_silver` (schemas off) and `wh_gold` created in `ws-citibike-dev`; `Files/seed/wmo_weather_codes.csv` uploaded beside `bronze` and `_checkpoints`. All three report collation `Latin1_General_100_BIN2_UTF8` (case-sensitive workspace default), recorded in `docs/conventions.md` §5. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T007 done: test user `analyst.region` (Test Analyst) created in Entra and signed in once at Fabric; free licence, 0 roles, 0 groups, no workspace access until T071. Never press Start trial in that account. See `docs/environments.md` §1. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T006 done: `ws-citibike-dev`, `-test` and `-prod` created on the trial capacity and put in the domain `Mobility`. Workspace defaults read: Starter Pool and Spark runtime 2.0 (recorded then as a preview; Microsoft's lifecycle page lists it as GA, see the T009 line). See `docs/environments.md` §3. Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Tue Oct 27, 2026 · T005 done: Capacity Metrics app installed and showing the trial capacity (F4, Central India). Baseline from the Compute page: average 7.62%, peak 10.04%, no throttling; one practice notebook sitting of about 2 h 21 min used 98% of the CU. See `docs/cost-and-capacity.md` §5, input for ADR-023 option (a). Evidence and notes filed in portfolio-hq. Next: `python3 tools/backlog.py next`.
- Mon Oct 26, 2026 · T004 done: Fabric trial started overnight on its own (Central India, 4 CU, ends about Dec 25; last day for screenshots and publish Dec 18). ADR-022 resolved. ADR-023 (Proposed): the capacity is an F4, not the F64 the docs assumed; Bharat decides. Evidence and notes filed in ADE HQ. Next: T005.
- Sun Oct 25, 2026 · T003 done: signed in with the tenant admin account, free licence active; the Fabric tenant settings the project needs were already on (nothing changed). Next: T004 (start the Fabric trial), Mon Oct 26.
- Sat Oct 24, 2026 · Azure Boards closing moved into the task chat (protocol step 11): `Closed AB#` on a direct push to `dev` links but does not close, tested on T012.
- Sat Oct 24, 2026 · T012 done: rulesets on `main` and `dev` proved (direct push to `main` refused, GH013). Next: Sprint 1 from Mon Oct 26 with T003.
- Sat Oct 24, 2026 · Personal details redacted from the whole history (one-off force push, Bharat's call), repo made public, rulesets on `main` and `dev` (T012). Azure Boards GitHub app connected; task commits end with `AB#<ADO>`.
- Sat Oct 24, 2026 · T002 done: repo on GitHub, main and dev pushed. Backlog mirrored to Azure Boards (dev.azure.com/bdhabekar-citibike, project citibike-fabric-lakehouse) for tracking. Next: Sprint 1 from Mon Oct 26 with T003.
- Fri Oct 23, 2026 · T001 done: repo scaffolded and committed locally. Next: T002 (Bharat creates the GitHub repo and pushes), then Sprint 1 from Mon Oct 26 with T003.
