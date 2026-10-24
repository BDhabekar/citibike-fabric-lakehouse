# Start here (every task chat reads this first)

This repo is the Citi Bike operations lakehouse on Microsoft Fabric, Bharat's second portfolio project after `olist-azure-lakehouse`. The design is locked; the work is a backlog of 89 tasks, and one chat does one task.

## Read in this order, and stop when you have what the task needs

1. This file.
2. `backlog/README.md`: the task-chat protocol (11 steps). Follow it exactly.
3. `python3 tools/backlog.py show T0xx`: your card, with its story and feature.
4. Only the files the card lists under **Read first**.
5. `D:\MissionAzureDataEngineer\INSTRUCTIONS.md` §5.5, §6 (teaching and building rules) the first time in a chat. Its rules apply here unless this repo says otherwise.

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
- **Evidence and notes** go to ADE HQ (`projects/citibike-fabric-lakehouse/evidence/`, `notes/fabric-project-explained.md`), not to this public-bound repo.
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

- Sat Oct 24, 2026 · Personal details redacted from the whole history (one-off force push, Bharat's call), repo made public, rulesets on `main` and `dev` (T012). Azure Boards GitHub app connected; closing commits end with `Closed AB#<ADO>`.
- Sat Oct 24, 2026 · T002 done: repo on GitHub, main and dev pushed. Backlog mirrored to Azure Boards (dev.azure.com/bdhabekar-citibike, project citibike-fabric-lakehouse) for tracking. Next: Sprint 1 from Mon Oct 26 with T003.
- Fri Oct 23, 2026 · T001 done: repo scaffolded and committed locally. Next: T002 (Bharat creates the GitHub repo and pushes), then Sprint 1 from Mon Oct 26 with T003.
