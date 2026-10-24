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
- **Model:** Sonnet | Haiku
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

## Running a task (the protocol every task chat follows)

Bharat opens a new chat in the "Mission Azure Data Engineer" project, on the model the card names, and pastes:

> Fabric project: run task T0xx. Read `D:\GitRepositories\citibike-fabric-lakehouse\START-HERE.md` first.

The chat then:

1. Asks for access to `D:\GitRepositories` and, if the card needs evidence or notes, `D:\MissionAzureDataEngineer`.
2. Reads `START-HERE.md`, runs `python3 tools/backlog.py show T0xx`, and reads only the card's **Read first** files.
3. Stops if a dependency is not `done` (the `show` command prints a warning) and says which task comes first.
4. Sets the card to `doing` (`python3 tools/backlog.py set T0xx doing`).
5. Gives Bharat the whole task before he starts, the ADE HQ way: the idea in plain words, why it matters in production and in an interview, the steps with the screen each one starts from, what to send back, a small example of the finished result, and what done looks like. Cost line: "trial capacity, ₹0" (anything else stops the task).
6. Guides the build. Corrects any mistake before moving on.
7. Checks each acceptance box against real evidence (a screenshot, a query result, a file in the repo).
8. Writes the three-part explanation (what we did, in production, in an interview) into `D:\MissionAzureDataEngineer\notes\fabric-project-explained.md`, and files screenshots in `D:\MissionAzureDataEngineer\projects\citibike-fabric-lakehouse\evidence\YYYY-MM-DD\`.
9. Closes the card: `python3 tools/backlog.py set T0xx done --result "<one line: what exists now, any UI difference met>"`.
10. Updates any doc the task changed (for example `docs/environments.md`), runs `python3 tools/backlog.py check`, commits on `dev` with `T0xx: <summary> AB#<ADO>` (the `show` command prints the exact line), and gives Bharat the two push lines from `docs/conventions.md` §10. Once pushed, the Azure Boards GitHub app links the commit to the work item.
11. Closes the work item in Azure Boards. In the browser pane, open `https://dev.azure.com/bdhabekar-citibike/citibike-fabric-lakehouse/_workitems/edit/<ADO>` (Bharat signs in if asked), set State to **Closed**, add the Result line as a comment, save, and confirm the item reads Closed. A `Closed AB#` keyword in the commit does not do this: Azure Boards changes state only when a pull request is merged into the default branch, and task commits go straight to `dev` (tested on T012, Oct 24, 2026).
12. Ends with the next ready task: `python3 tools/backlog.py next`.

If the task cannot be done as written, the chat follows change control (`docs/architecture.md` §10): `blocked`, a Proposed decision, and a question to Bharat.

## Tool

`tools/backlog.py` (standard library only):

| Command | Does |
|---|---|
| `check` | validates ids, parents, dependencies, fields; exits non-zero on a problem (CI runs it) |
| `next` | lists tasks whose dependencies are all done, in sprint order |
| `show T0xx` | prints one card with its story and feature, and warns about unfinished dependencies |
| `set T0xx <status> [--result "..."]` | changes a card's status, writes its Result line |
| `summary` | counts and hours by epic and by sprint |
