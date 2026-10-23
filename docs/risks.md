# Risks

Each risk is retired by a named task before any other task depends on it, and each has its fallback decided now, so a failed check changes a known line instead of starting a redesign. Spikes run in Sprint 1 (T013–T018); T019 writes the outcomes here and in `docs/decisions.md`.

| Id | Risk | Retired by | If it fails (decided now) | Status |
|---|---|---|---|---|
| R1 | The Eventstream HTTP source (preview) does not poll the GBFS feed reliably, or its event shape is unexpected | T013 | Fall back to `pl_poll_station_status` every 5 minutes landing JSON in `lh_bronze`, with Eventhouse ingestion from OneLake; ADR-007 updated to option (c) | open |
| R2 | No alert route reaches Bharat (the tenant user has no mailbox) | T014 | Try in order: Activator email to Gmail; Activator email to the tenant user with its contact email set to Gmail; pipeline Web activity to a phone push service | open |
| R3 | Copy activity cannot decompress the 1 GB trip zip from HTTP into Files | T015 | Copy the zip as binary, then unzip in a notebook with Python `zipfile` through the lakehouse file mount | open |
| R4 | CI cannot import `nb_lib_common` from its Git file (`notebook-content.py`) | T016 | CI extracts the code cells between the cell markers into a temporary module before importing | open |
| R5 | Structured Streaming with the text source and `availableNow` misbehaves in Fabric | T017 | Batch read anti-joined on `_source_file` (ADR-008 fallback) | open |
| R6 | Warehouse cross-database query to `lh_silver`, the Stored procedure activity, or the variable library in pipelines and notebooks does not work as documented | T018 | Cross-database: Script activity against the warehouse reading the silver SQL endpoint. Variable library: pipeline parameters with defaults plus deployment rules | open |
| R7 | The tenant blocks the trial or a needed setting | T003 | Bharat is Global Administrator; the setting is switched on in the Admin portal | open |
| R8 | The trial ends before the project, the publish or the exam | T004 sets the dates; sprints end 7 days before trial end | Publish from Git and screenshots; a short paid F2 session only by written decision (`docs/cost-and-capacity.md` §3–4) | open |
| R9 | An email address or other personal detail ends up in the public repo through item definitions in Git | T014, T086 | Use an address Bharat is happy to publish, or keep that value out of Git; T086 scans the repo before it goes public | open |
| R10 | Fabric screens change during the build | every task | Small UI differences are noted in the Result line; anything that changes the design goes through change control | standing |
| R11 | Lyft adds or changes GBFS fields | design | Bronze keeps raw text; silver parses with an explicit schema and ignores extras | designed out |
| R12 | Daylight saving ends on Sun Nov 1, 2026, during streaming | design | Everything stored in UTC (ADR-009); the unit tests in T042 and T053 cover that day | designed out |
| R13 | A monthly trip file is late or renamed | T026 | The pipeline checks the file exists first and fails with a clear message; the next day's run retries | open |
| R14 | Open-Meteo rate limits | design | Under 20 calls a day; retries with backoff | designed out |
