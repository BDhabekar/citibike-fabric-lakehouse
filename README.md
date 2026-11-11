# Citi Bike operations lakehouse on Microsoft Fabric

A data platform for New York's Citi Bike system, built end to end in Microsoft Fabric. It answers two questions:

1. **How does weather drive ride demand?** Daily and hourly trips against temperature, rain and snow, for members and casual riders.
2. **Which stations run empty at rush hour?** Minutes with zero bikes per station on weekday mornings and evenings, New York time.

It also has a live view: which stations are empty right now, with an alert when one stays empty for 15 minutes at rush hour.

> **Status: being built.** Started in October 2026; 22 of 89 tasks were done on Nov 11, 2026 (table below). The design was fixed before the build began and is in [`docs/architecture.md`](docs/architecture.md). This page is rewritten in full when version 1.0 reaches prod.

![Architecture](docs/img/architecture.png)

## What it is made of

| Part | In Fabric | What happens there |
|---|---|---|
| Sources | three public feeds | Open-Meteo weather (REST, JSON), Citi Bike station feeds (REST, JSON, one of them polled every 60 seconds) and the monthly trip files (zipped CSV, about 1 GB a month) |
| Bronze | lakehouse `lh_bronze` | every response kept untouched as a file, then loaded as Delta rows with lineage columns |
| Silver | lakehouse `lh_silver` | PySpark: typed, flattened and de-duplicated; station history as SCD Type 2; bad rows go to quarantine tables |
| Gold | warehouse `wh_gold` | a T-SQL star schema, reporting views, control tables, data-quality results, row- and column-level security |
| Live path | Eventstream, Eventhouse (KQL), Activator | station status every minute, the latest state per station, the rush-hour alert |
| Serving | Direct Lake semantic model, Power BI report, Real-Time Dashboard | the two questions, and the live map |
| Delivery | Git, pull requests, a deployment pipeline | dev, test and prod workspaces; `main` always matches prod |

Every load can be run twice and give the same result, every run is logged, and every load is checked. The standards are in [`docs/conventions.md`](docs/conventions.md).

## Where the build stands

| Epic | Done | Tasks |
|---|---|---|
| Program setup | 2 | 2 |
| Platform foundation and risk spikes | 17 | 17 |
| Batch ingestion to bronze | 3 | 12 |
| Silver transformations (PySpark) | 0 | 13 |
| Real-time intelligence | 0 | 9 |
| Gold warehouse (T-SQL star schema) | 0 | 10 |
| Orchestration, monitoring and operations | 0 | 7 |
| Security and governance | 0 | 4 |
| CI/CD and release | 0 | 6 |
| Semantic model and report | 0 | 3 |
| Publish and interview readiness | 0 | 6 |

As of Wed Nov 11, 2026. `python3 tools/backlog.py summary` prints the live numbers.

Before any pipeline was built, six risks were tried on the real service: the Eventstream HTTP source, an alert route that reaches a personal mailbox, unzipping a 1 GB file from HTTP, testing a notebook's code in CI, streaming over a folder of files, and the warehouse reading the lakehouse. The risks and their fallbacks are in [`docs/risks.md`](docs/risks.md); what each trial showed is written into the decisions it touched, and one of them changed the design ([`docs/decisions.md`](docs/decisions.md), ADR-027).

## Where to read

| If you want | Open |
|---|---|
| The design on one page | [`docs/architecture.md`](docs/architecture.md) |
| Why each choice was made, and what was turned down | [`docs/decisions.md`](docs/decisions.md) |
| Every table, column and key | [`docs/data-contracts.md`](docs/data-contracts.md) |
| The sources, their limits and licences | [`docs/sources.md`](docs/sources.md) |
| What exists in each environment and who may do what | [`docs/environments.md`](docs/environments.md) |
| The plan: epics, features, stories and tasks | [`backlog/`](backlog/README.md) |

## How it is built

The work is planned as an agile backlog and mirrored to Azure Boards. A task is done when its acceptance checks hold against real evidence, and it reaches `dev` as one commit linked to its work item.

I am building this with an AI assistant (Claude) as mentor and pair-programmer. I build the Fabric items by hand: pipelines, notebooks, KQL, T-SQL and the deployment. The assistant drafts the docs, tests, CI and control scripts, which I review and run.

## Data and licence

Data: trip data from Citi Bike under the [NYCBS Data Use Policy](https://www.citibikenyc.com/data-sharing-policy); live station data from Citi Bike's public GBFS feed; weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).
