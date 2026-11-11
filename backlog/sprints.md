# Sprints

One-week sprints, Monday to Sunday. Weekend mornings belong to the cohort (8:00–13:00); SQL 50 runs one question a day until Sat Oct 31.

Estimates on the cards are build minutes. With teaching and the ADE HQ rule that a first-time set-up takes twice the click time, plan about 1.5 times the card total. If a sprint does not finish, its open tasks move to the next sprint and Sprint 6 absorbs the slip. The DP-700 date is fixed (Mon Dec 7), so tasks still open on Sun Dec 6 move to after the exam; the ones that need a live workspace, T089 included, finish by about Thu Dec 17, because the trial ends about Dec 24.

| Sprint | Dates | Goal | Tasks | Card hours (Bharat) |
|---|---|---|---|---|
| 0 | Fri Oct 23 – Sun Oct 25 | repo ready, on GitHub | T001–T002 | 0.2 |
| 1 | Mon Oct 26 – Sun Nov 1 | trial, workspaces, Git, every risk tried | T003–T019 | 8.1 |
| 2 | Mon Nov 2 – Sun Nov 8 | every batch source landing in bronze | T020–T031 | 11.5 |
| 3 | Mon Nov 9 – Sun Nov 15 | silver built and tested; streaming running in dev | T032–T047 | 11.5 |
| 4 | Mon Nov 16 – Sun Nov 22 | hot path, cold path, gold star schema | T048–T063 | 11.5 |
| 5 | Mon Nov 23 – Sun Nov 29 | orchestration, security, CI/CD, release v1.0 to prod | T064–T080 | 13.9 |
| 6 | Mon Nov 30 – Sun Dec 6 | report v1.1, README, public repo, walkthrough; DP-700 practice assessments (schedule: `plan/2026-11-06_dp700-dec7-plan.md` in the private study repo) | T081–T089 | 1.8 |
| — | Mon Dec 7 | **DP-700 exam** (fixed date, booked on the Data Days voucher; practice assessments at 85% before it) | | |
| — | trial end (from T004) minus 7 days | last day for anything that needs a live workspace (T089) | | |

The trial dates are set by T004. If the trial starts on Mon Oct 26 it ends around Thu Dec 24 or Fri Dec 25, which leaves about seventeen days after the exam.

`python3 tools/backlog.py summary` prints the live version of the hour columns.
