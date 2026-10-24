# EP07 · Security and governance

**Goal.** Least-privilege access at workspace, item, row, column and file level, with items endorsed and organised.
**Done when.** The test analyst sees only their region, cannot see exact trip times or ride ids, and cannot open bronze.

## FT22 · Access model

### US025 · Least privilege, proved with a second user
As a data owner, I want analysts to see only what their job needs, so that trip data cannot be used to follow a person and regions see their own numbers.
- Every control is tested signed in as the analyst, not just configured.

#### T071 · Workspace roles and item permissions
- **Story:** US025
- **ADO:** #126
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 5
- **Depends on:** T007, T054
- **DP-700:** 1.3
- **Status:** todo
- **Read first:** docs/environments.md §1, §3; docs/decisions.md ADR-013
**Do**
1. Claude explains the four workspace roles and item sharing, and why the analyst gets item-level Read on the warehouse rather than a workspace role in dev.
2. In `ws-citibike-dev` (security is built and tested in dev, then deployed): share `wh_gold` with the analyst, permission **Read** only (no "Read all data using SQL analytics endpoint" on the lakehouses, no Build).
3. Sign in as the analyst in a private window: `wh_gold` opens; `lh_bronze` and `lh_silver` do not appear.
**Acceptance**
- [ ] The analyst sees the warehouse and nothing else in the workspace; screenshot filed.
- [ ] `docs/environments.md` updated to say dev holds the test grant until T079 moves it to prod.
**Result:** —

#### T072 · GRANTs, row-level security, dynamic data masking and column-level security
- **Story:** US025
- **ADO:** #127
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 75 min
- **Sprint:** 5
- **Depends on:** T059, T060, T071
- **DP-700:** 1.3
- **Status:** todo
- **Read first:** docs/data-contracts.md §5 (sec), docs/decisions.md ADR-013
**Do**
1. Claude teaches RLS (predicate function plus security policy), DDM and column-level `DENY`, each on a 3-row example, before any statement.
2. Bharat writes, with Claude's skeleton: `sec.user_region` rows (analyst → one region); `sec.fn_region_predicate`; security policy `sec.rls_region` on both facts; `ALTER TABLE fact.trip ALTER COLUMN ride_id ADD MASKED WITH (FUNCTION = 'default()')`; `DENY SELECT ON fact.trip (started_at_utc, ended_at_utc) TO [analyst]`; `GRANT SELECT` on `rpt`, `dim` and the allowed fact columns.
3. Test as the analyst: total trips equals their region's count from Bharat's own query; `ride_id` shows masked; selecting `started_at_utc` is refused; `rpt.v_trip_daily_weather` works.
4. Claude saves the statements as `sql/security/001_security.sql`. Commit the workspace.
**Acceptance**
- [ ] Each of the four analyst checks gives the expected result; screenshots filed.
- [ ] Bharat's own account still sees all regions and unmasked values.
**Result:** —

#### T073 · OneLake security: a folder-level role on `lh_bronze`
- **Story:** US025
- **ADO:** #128
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 5
- **Depends on:** T071
- **DP-700:** 1.3
- **Status:** todo
- **Read first:** docs/environments.md §1
**Do**
1. Claude checks Microsoft's current OneLake security page (status, how roles combine with workspace roles) and explains it.
2. If the feature is available in the tenant: on `lh_bronze`, create a role `seed_readers` granting Read on `Files/seed` only; add the analyst; give the analyst Read on `lh_bronze`; sign in as the analyst and confirm only `seed` is visible. Then remove the analyst's access to `lh_bronze`.
3. If it is not available: Claude writes the steps and expected behaviour into the explained notes as theory, and the Result line says so.
**Acceptance**
- [ ] Either a working folder-level test with screenshots, or the theory note and the reason.
- [ ] The analyst has no access to `lh_bronze` at the end.
**Result:** —

#### T074 · Endorsement, descriptions, lineage and the audit log
- **Story:** US025
- **ADO:** #129
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 5
- **Depends on:** T071
- **DP-700:** 1.3
- **Status:** todo
- **Read first:** docs/architecture.md §4
**Do**
1. Mark `wh_gold` (and later `sm_citibike`) as **Promoted**; write a one-line description on every item (Claude supplies the lines).
2. Open the workspace Lineage view; screenshot it (it goes in the README).
3. Admin portal → Audit logs: see where Fabric activities are logged (Microsoft Purview); find one of today's events if the tenant has access; otherwise note what the page says.
4. Sensitivity labels: Claude explains them for the exam; the tenant has no information-protection licence, so nothing is applied (named in the Result line).
**Acceptance**
- [ ] Promoted badge and descriptions visible; lineage screenshot filed.
- [ ] The audit-log finding in the Result line.
**Result:** —
