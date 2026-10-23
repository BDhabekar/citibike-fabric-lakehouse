# EP00 · Program setup

**Goal.** One repository holds the locked design and the full backlog, so every task chat starts from the same truth.
**Done when.** The repo is on GitHub (private) with branches `main` and `dev`.

## FT01 · Repository and working method

### US001 · One source of truth for every task chat
As Bharat, I want the design, conventions and backlog in one repo, so that any chat on any model builds the same thing.
- The repo has the architecture, decisions, contracts, conventions, risks, cost and environment docs.
- `tools/backlog.py check` passes.

#### T001 · Scaffold the repo, the design docs and the backlog
- **Story:** US001
- **Owner:** Claude builds
- **Model:** Opus
- **Estimate:** 120 min
- **Sprint:** 0
- **Depends on:** —
- **DP-700:** —
- **Status:** done
- **Read first:** —
**Do**
1. Create `D:\GitRepositories\citibike-fabric-lakehouse` with `docs/`, `backlog/`, `tools/`, `seed/`, `fabric/`.
2. Write the architecture, decisions, data contracts, sources, conventions, environments, risks, cost and DP-700 map.
3. Write the backlog, the sprint calendar and `tools/backlog.py`; run `check`.
4. `git init -b main`, set the identity, first commit, create branch `dev`.
**Acceptance**
- [x] All docs exist and `tools/backlog.py check` passes.
- [x] First commit on `main`; branch `dev` exists.
**Result:** Oct 23: repo scaffolded, 89 tasks across 11 epics, first commit made locally.

#### T002 · Create the GitHub repository and push both branches
- **Story:** US001
- **Owner:** Bharat builds (Claude guides)
- **Model:** Haiku
- **Estimate:** 15 min
- **Sprint:** 0
- **Depends on:** T001
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/conventions.md §7
**Do**
1. On github.com, signed in as `BDhabekar`: New repository → name `citibike-fabric-lakehouse` → **Private** → no README, no .gitignore, no licence (the repo already has its files).
2. On Windows, in a terminal:
   ```
   git -C D:\GitRepositories\citibike-fabric-lakehouse remote add origin https://github.com/BDhabekar/citibike-fabric-lakehouse.git
   git -C D:\GitRepositories\citibike-fabric-lakehouse push -u origin main
   git -C D:\GitRepositories\citibike-fabric-lakehouse push -u origin dev
   ```
3. On GitHub: Settings → General → Default branch → switch to `dev` (Fabric commits there; `main` stays the release branch).
**Acceptance**
- [ ] The repo exists, private, with branches `main` and `dev`, same commit on both.
- [ ] Default branch is `dev`.
**Result:** —
