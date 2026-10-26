# EP10 · Publish and interview readiness

**Goal.** A public repository that explains the project in ten minutes, a rehearsed walkthrough, and the project's questions in the interview bank, all before the trial ends.
**Done when.** The repo is public and pinned, the walkthrough has been given out loud under ten minutes, and the trial-end checklist is done.

## FT26 · Publish

### US029 · A repo that sells the project
As a candidate, I want a README an interviewer can read in five minutes, so that the project gets me to the technical round.
- Architecture, run flow, decisions with rejected options, numbers, cost, known gaps, scale paragraph and attributions are in the README.

#### T084 · README in full
- **Story:** US029
- **ADO:** #150
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 6
- **Depends on:** T079, T082
- **DP-700:** —
- **Status:** todo
- **Read first:** docs/architecture.md, docs/decisions.md, the Result lines of every done task (`tools/backlog.py summary` and the epic files)
**Do**
1. Sections: what it answers; the picture; one run, step by step; design decisions with what was rejected (from the ADRs); numbers (rows per layer, run times, rejects, CU of a daily run); cost (₹0 on the trial, what an F2 would cost); security; CI/CD; Fabric vs Databricks (a short table drawn from the Olist project); known gaps; "at 100 times the scale"; how it was built (one line: built with an AI assistant, Claude, as in the Olist repo); attributions.
2. Screenshots from the evidence folder, renamed, into `docs/img/`.
3. Humanised writing, Bharat's voice, no AI tells.
**Acceptance**
- [ ] Every number in the README traces to a Result line or a query.
- [ ] Bharat has read it and approved it.
**Result:** —

#### T085 · Evidence pack
- **Story:** US029
- **ADO:** #151
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 6
- **Depends on:** T079
- **DP-700:** —
- **Status:** todo
- **Read first:** docs/environments.md §5
**Do**
1. Index the evidence folders in ADE HQ by task; list any acceptance box whose proof is missing.
2. Bharat takes the missing screenshots (Claude names each screen and what to capture).
**Acceptance**
- [ ] Every done task has its proof filed and indexed.
**Result:** —

#### T086 · Make the repo public
- **Story:** US029
- **ADO:** #152
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 20 min
- **Sprint:** 6
- **Depends on:** T084, T085
- **DP-700:** —
- **Status:** todo
- **Read first:** docs/risks.md R9
**Do**
1. Claude scans the whole repo and its history for secrets, tokens, the alert address (unless R9 decided it may be public), workspace or tenant ids worth hiding, and personal details; reports findings before anything changes.
2. Claude adds the MIT `LICENSE` (as in the Olist repo).
3. Bharat: Settings → Change visibility → Public; About box (description and topics Claude supplies); pin the repo on his profile next to `olist-azure-lakehouse`.
**Acceptance**
- [ ] The scan found nothing that should stay private (or it was removed first).
- [ ] Repo public, licensed, pinned.
**Result:** —

### US030 · Ready to talk about it
As a candidate, I want to explain the project fluently and answer its likely questions, so that the interview is a conversation about work I did.
- The walkthrough is timed; the questions are in the bank.

#### T087 · Twenty-five Fabric questions into the interview bank
- **Story:** US030
- **ADO:** #154
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 45 min
- **Sprint:** 6
- **Depends on:** T084
- **DP-700:** —
- **Status:** todo
- **Read first:** D:\GitRepositories\interview-prep\interview-bank-plan.md
**Do**
1. Add 25 `Q-###` blocks to `interview-bank.md` in `D:\GitRepositories\interview-prep`, each answered from this project's own decisions and numbers (lakehouse vs warehouse, Direct Lake and fallback, SCD2 with deletes, idempotency, streaming design, CI/CD path, security, cost, troubleshooting).
2. Rebuild the Career HQ Interview tab as the bank plan says.
**Acceptance**
- [ ] 25 new blocks, each tied to a decision or a number in this repo.
**Result:** —

#### T088 · Ten-minute walkthrough, out loud
- **Story:** US030
- **ADO:** #155
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 6
- **Depends on:** T086
- **DP-700:** —
- **Status:** todo
- **Read first:** README.md
**Do**
1. Claude gives the running order (problem, picture, one run, three decisions, security, CI/CD, numbers, gaps) with a time for each.
2. Bharat gives it out loud, timed, sharing the README; Claude asks five follow-up questions as an interviewer would.
**Acceptance**
- [ ] Under ten minutes; the five follow-ups answered; weak answers written into ADE HQ weak points.
**Result:** —

#### T089 · Trial-end checklist
- **Story:** US030
- **ADO:** #156
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 6
- **Depends on:** T086
- **DP-700:** —
- **Status:** todo
- **Read first:** docs/cost-and-capacity.md §2–4, §6
**Do**
1. Seven days before the trial ends: confirm every item that Git supports is committed and on `main`; export the Eventstream settings into its runbook (already there); final Capacity Metrics screenshot; stop the prod Eventstream and schedules on the last day.
2. Write the decision for Bharat: let the workspaces lapse (the default), or a paid F2 for demos with the guardrails in `docs/cost-and-capacity.md` §4 (only with his written yes).
**Acceptance**
- [ ] Checklist done; Bharat's decision written in `docs/decisions.md` as ADR-023.
**Result:** —
