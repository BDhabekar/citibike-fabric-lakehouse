# Backlog

The whole project is planned here before the build starts: epics, features, user stories and tasks. One task is done in one chat.

## Hierarchy and ids

| Level | Id | What it is | Done when |
|---|---|---|---|
| Epic | `EP00`–`EP10` | a large block of the system (one file each) | all its features are done |
| Feature | `FT01`… | a working capability inside an epic | all its stories are done |
| User story | `US001`… | a need written as "As …, I want …, so that …", with acceptance lines | all its tasks are done and its acceptance lines hold |
| Task | `T001`… | 15–90 minutes of work, one chat | its acceptance boxes are ticked and its Result line is written |

Ids are never renumbered or reused. A new task gets the next free number, wherever it sits.

## Card fields

```
#### T013 · Spike R1: Eventstream HTTP source polls the station feed
- **Story:** US006
- **ADO:** #26
- **Owner:** Bharat builds (Claude guides) | Claude builds | Claude writes, Bharat runs
- **Estimate:** 45 min
- **Sprint:** 1
- **Depends on:** T006
- **DP-700:** 2.3
- **Status:** todo | doing | done | blocked
- **Read first:** files the chat reads, and nothing else
**Do**
1. ...
**Acceptance**
- [ ] ...
**Result:** —
```

`DP-700` codes refer to `docs/dp700-map.md`. `ADO` is the task's work item id in Azure Boards (`dev.azure.com/bdhabekar-citibike`, project `citibike-fabric-lakehouse`), fixed once and never changed.

## How a task is run

One task at a time, in this order:

1. Pick the next ready card (`python3 tools/backlog.py next`) and check that its dependencies are done.
2. Set it to `doing`, read the files it lists under **Read first**, and build what the card says.
3. Check every acceptance box against real evidence: a screenshot, a query result or a file in the repo.
4. Write the Result line and close the card (`python3 tools/backlog.py set T0xx done --result "..."`).
5. Update any doc the task changed, run `python3 tools/backlog.py check`, and commit on `dev` as `T0xx: <summary> AB#<ADO>`.
6. Close the work item in Azure Boards, with the Result line as a comment.

A task that cannot be done as written stops: the card goes to `blocked` and a Proposed decision is written (`docs/architecture.md` §10).

The project is built with an AI assistant (Claude) as mentor and pair-programmer, and the **Owner** field on each card says who does what. The working notes of those sessions, the screenshots and the per-task explanations are kept in a private repo.

## Tool

`tools/backlog.py` (standard library only):

| Command | Does |
|---|---|
| `check` | validates ids, parents, dependencies, fields; exits non-zero on a problem (CI runs it) |
| `next` | lists tasks whose dependencies are all done, in sprint order |
| `show T0xx` | prints one card with its story and feature, and warns about unfinished dependencies |
| `set T0xx <status> [--result "..."]` | changes a card's status, writes its Result line |
| `summary` | counts and hours by epic and by sprint |
