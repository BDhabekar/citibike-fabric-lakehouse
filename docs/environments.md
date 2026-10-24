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

## 2. Capacity

| | |
|---|---|
| Type | Fabric trial, 64 CU |
| Admin | Bharat |
| Region | written in `docs/cost-and-capacity.md` §6 by T004 |
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

## 5. What lives outside Fabric

| What | Where |
|---|---|
| Code, docs, backlog, tests, CI | `D:\GitRepositories\citibike-fabric-lakehouse` = GitHub `BDhabekar/citibike-fabric-lakehouse` |
| Screenshots and proof | `D:\MissionAzureDataEngineer\projects\citibike-fabric-lakehouse\evidence\YYYY-MM-DD\` (private) |
| Teaching notes (what we did, in production, in an interview) | `D:\MissionAzureDataEngineer\notes\fabric-project-explained.md` (private) |
