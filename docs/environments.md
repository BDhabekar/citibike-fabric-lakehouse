# Environments

The map of what exists where and who may do what (ADE HQ rule 24). Update it the same turn something is created.

## 1. Identities

| Who | Account | Where | Rights |
|---|---|---|---|
| Bharat | `<tenant-admin-upn>` | tenant `bharat-ade` | Global Administrator; Fabric admin; trial capacity admin; Admin on all three workspaces |
| Test analyst (for security tests only) | `analyst.region@<tenant-domain>` (created in T007) | tenant `bharat-ade` | Fabric free licence; Viewer on `ws-citibike-prod`; Read on `wh_gold` only; mapped to one region in `sec.user_region` |
| GitHub | `BDhabekar` | github.com | owner of `BDhabekar/citibike-fabric-lakehouse` |

Placeholders: `<tenant-admin-upn>` is Bharat's admin sign-in in `bharat-ade`, `<tenant-domain>` that tenant's `onmicrosoft.com` domain, `<alert-email>` his personal email. The repo is public, so the real values are never written here; ask Bharat for them in the chat when a step needs one.

Never used for this project: the employer work account, a relative's tenant or his Azure for Students subscription, the Gmail address as a sign-in.

Seen in T003 (Oct 25, 2026): the tenant also holds his Gmail address as an external user, which is never used to sign in to Fabric. The Fabric tenant settings for creating items, trials, Git and GitHub sync and workspace creation were already enabled for the entire organization; there is no variable-library or Eventhouse switch. Service principals creating workspaces and deployment pipelines is Disabled (see EP08).

Seen in T007 (Oct 27, 2026): `analyst.region` exists in Entra as a Member of the tenant's own `onmicrosoft.com` domain (display name Test Analyst), created by the tenant admin account and signed in once at `app.fabric.microsoft.com`; its Account manager reads Free account. It holds 0 roles and 0 groups and has no workspace access; the grants in the table row above are made in T071. Never press Start trial in that account's session.

## 2. Capacity

| | |
|---|---|
| Type | Fabric trial, 4 CU (F4), started Oct 26, 2026 |
| Admin | Bharat |
| Region | Central India; dates in `docs/cost-and-capacity.md` §6 |
| Azure subscription | none during the build |

## 3. Workspaces

| | `ws-citibike-dev` | `ws-citibike-test` | `ws-citibike-prod` |
|---|---|---|---|
| Capacity | trial | trial | trial |
| Domain | Mobility | Mobility | Mobility |
| Git | GitHub `BDhabekar/citibike-fabric-lakehouse`, branch `dev`, folder `/fabric` | none | none |
| Deployment stage | Development | Test | Production |
| `vl_citibike` active value set | `dev` | `test` | `prod` |
| Roles | Bharat Admin | Bharat Admin | Bharat Admin; analyst Viewer |
| Trip months loaded | 2026-04 | 2026-04 | 2026-07 onwards |
| Eventstream | built by hand (runbook), stopped after T050 | none | built by hand (runbook), running |
| Schedules | off | off | `pl_daily` 11:30 IST daily; `pl_monthly_trips` 07:00 IST on the 8th |

Seen in T006 (Oct 27, 2026): the three workspaces exist on the trial capacity (workspace type Fabric Trial, SKU FTL4, Central India) and sit in the domain `Mobility`. Workspace defaults read in dev (test and prod reported the same): Spark pool Starter Pool (memory optimized, medium nodes, 1 to 10 nodes), "Customize compute configurations for items" on, no default environment, Spark runtime 2.0 (Spark 4.1, Delta 4.2), which T006 recorded as a preview. Microsoft's lifecycle page, read on Oct 27 and last updated Jul 29, 2026, lists 2.0 as GA and 1.3 as end of support announced, so `env_citibike` (T009) uses 2.0 (ADR-024). OneLake settings: cache for shortcuts off, diagnostic events off, no lifecycle rules. Git, roles for the analyst and the other rows of the table are still to do in their own tasks.

Seen in T010 (Oct 27, 2026): `vl_citibike` in dev has twelve String variables and four value sets: Default (the dev values, cannot be renamed), `dev` (no overrides, active), `test` (overrides `env_name`) and `prod` (overrides `env_name` and the three backfill variables). Microsoft says a workspace created by a deployment starts on Default, so the stage's own set is chosen by hand in T077 (ADR-025).

## 4. Items per workspace

Created in dev, promoted to test and prod by `dp-citibike`, except where marked.

| Item | Created in | Reaches test and prod by |
|---|---|---|
| `lh_bronze`, `lh_silver` | T008 | deployment (empty; each stage loads its own data) |
| `wh_gold` | T008 | deployment (objects only); `pl_post_deploy` seeds config |
| `env_citibike` | T009 | deployment |
| `vl_citibike` | T010 | deployment; active value set chosen per stage in T077 |
| notebooks, pipelines, `df_weather_codes` | EP02 to EP06 | deployment |
| `eh_citibike`, `kqldb_citibike`, `kqs_citibike`, `rtd_citibike_live`, `act_citibike_alerts` | EP04 | deployment (prod only receives streaming data) |
| `es_station_status` | T046 | **by hand** from `docs/runbooks/eventstream.md` (ADR-007) |
| shortcut `kql_station_status` in `lh_silver` | T051 | recreated after deployment by the runbook step in T079 |
| `sm_citibike`, `rpt_citibike_ops` | EP09 | deployment |

Seen in T008 (Oct 27, 2026): `lh_bronze`, `lh_silver` and `wh_gold` exist in `ws-citibike-dev`; both lakehouses were created with "Lakehouse schemas" cleared (the box is ticked by default) and each shows a SQL analytics endpoint beside it in the item list, with no default semantic model listed. `lh_bronze` → Files holds `_checkpoints`, `bronze` and `seed`; `Files/seed/wmo_weather_codes.csv` is in `seed` (770 B, the same size as the repo file). The warehouse Create dialog has an Advanced pane (description and collation, collation set to Workspace default); nothing was changed there. Collation of all three items: see `docs/conventions.md` §5.

Seen in T009 (Oct 27, 2026): `env_citibike` exists in `ws-citibike-dev` and is published on Runtime 2.0 (Spark 4.1, Delta 4.2), the choice recorded in ADR-024. A new environment opens with 2.0 already selected; the runtime list also offers 1.3 and 1.2, and 1.2 carries a warning icon. Pool: Starter Pool (memory optimized, medium nodes, 1 to 10 nodes) with the compute values left at their defaults: driver and executor 8 cores and 56 GB, dynamic allocation on with 1 to 9 executors, live pool off. One Spark property, `spark.sql.session.timeZone` = `UTC`, set on the environment's own Spark properties page under Spark compute (the property is picked from a dropdown). No libraries, no resources, and the Acceleration page was not changed. Publish and Save are greyed with no pending-changes banner afterwards; no "Published" message was captured. Default: Workspace settings, Data Engineering/Science, Spark settings, Environment tab, Set default environment On with `env_citibike` selected; its Preview shows Runtime 2.0 and the time zone property. The default was set before the publish and read again after it, still On. Once an environment is the workspace default, only workspace admins can edit it (Microsoft, "Create, configure, and use an environment in Fabric", last updated Mar 31, 2026).

## 5. What lives outside Fabric

| What | Where |
|---|---|
| Code, docs, backlog, tests, CI | `D:\GitRepositories\citibike-fabric-lakehouse` = GitHub `BDhabekar/citibike-fabric-lakehouse` |
| Screenshots and proof | `D:\GitRepositories\portfolio-hq\citibike\evidence\YYYY-MM-DD\` (private) |
| Teaching notes (what we did, in production, in an interview) | `D:\GitRepositories\portfolio-hq\citibike\fabric-project-explained.md` (private) |
