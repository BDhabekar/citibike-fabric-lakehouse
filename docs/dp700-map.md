# DP-700 map

Exam DP-700, "Implementing Data Engineering Solutions Using Microsoft Fabric" (credential: Microsoft Certified: Fabric Data Engineer Associate). Skills measured as of **October 19, 2026**, from the [official study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/dp-700). Check the page again before booking: Microsoft updates it when features go GA.

Codes used on task cards: **1.1** workspace settings · **1.2** lifecycle · **1.3** security and governance · **1.4** orchestration · **2.1** loading patterns · **2.2** batch ingest and transform · **2.3** streaming · **3.1** monitoring · **3.2** errors · **3.3** optimisation.

## 1. Implement and manage an analytics solution (30–35%)

| Skill | Built in |
|---|---|
| Configure Spark workspace settings | T006, T009 |
| Configure domain workspace settings | T006 |
| Configure OneLake workspace settings | T006 |
| Configure Apache Airflow workspace settings | **study only** |
| Configure version control | T011, T012, T075, T076 |
| Implement database projects | T054 (the warehouse in Git) |
| Create and configure deployment pipelines | T077, T078, T079, T080 |
| Workspace-level access controls | T071 |
| Item-level access controls | T071 |
| Row-, column-, object- and folder/file-level access controls | T072 (row, column, object), T073 (folder) |
| Dynamic data masking | T072 |
| Apply sensitivity labels to items | **study only** (no information-protection licence in the tenant; T074 notes it) |
| Endorse items | T074, T081 |
| Fabric audit logs | T074 (where they live; depth depends on tenant access) |
| OneLake security | T073 |
| Choose between Dataflow Gen2, a pipeline and a notebook | ADR-006, T056 |
| Schedules and event-based triggers | T079 (schedules); event triggers: **study only** |
| Orchestration with notebooks and pipelines, parameters, dynamic expressions | T024, T025, T064, T065, T066 |

## 2. Ingest and transform data (30–35%)

| Skill | Built in |
|---|---|
| Full and incremental loads | T024 (watermark + overlap), T030 (partition replace), T035 (merge), T052 (incremental with late data), T057 (full) |
| Prepare data for a dimensional model | T038, T039, T054–T060 |
| Loading pattern for streaming data | T045, T046, T051 |
| Choose a data store | ADR-004, ADR-005 |
| Choose between Dataflow Gen2, notebooks, KQL and T-SQL for transformation | ADR-006, ADR-004 |
| OneLake shortcuts | T048, T051 |
| Mirroring | **study only** |
| Ingest with pipelines | T023–T026 |
| Transform with PySpark, SQL and KQL | EP03 (PySpark), EP05 (T-SQL), T045–T048 (KQL) |
| Denormalise | T059, T060 (region on facts) |
| Group and aggregate | T052, T061, T047 |
| Duplicate, missing and late-arriving data | T035, T041, T052 |
| Choose a streaming engine | T046 lesson |
| Native tables vs OneLake shortcuts in Real-Time Intelligence | T048, ADR-019 |
| Query acceleration for OneLake shortcuts vs standard shortcuts | T048 |
| Process data with Eventstream | T013, T046 |
| Process data with Spark Structured Streaming | T017, T029 |
| Process data with KQL | T045, T047, T048 |
| Windowing functions | T047 |

## 3. Monitor and optimise an analytics solution (30–35%)

| Skill | Built in |
|---|---|
| Monitor ingestion and transformation | T068 |
| Monitor semantic model refresh | T083 |
| Configure alerts | T014, T050, T067 |
| Resolve pipeline, Dataflow Gen2, notebook, Eventhouse, Eventstream, T-SQL and shortcut errors | T069 (one planted fault each) |
| Optimise a lakehouse table | T044 |
| Optimise a pipeline | T070 |
| Optimise a warehouse | T063 |
| Optimise Eventstream and Eventhouse | T045 (policies), T047 (materialized view) |
| Optimise Spark | T070 |
| Optimise queries | T063, T048 |

## Study-only list (covered by Microsoft Learn modules and practice questions in the ADE HQ plan)

Apache Airflow jobs and workspace settings · mirroring · sensitivity labels · event-based triggers (storage events, job events) · Copy job · Fabric SQL database · capacity SKUs and smoothing in depth.
