# EP09 · Semantic model and report

**Goal.** A Direct Lake semantic model on `wh_gold` and a three-page report that answer the two business questions. Claude does the modelling and report work (ADE HQ ruling of Oct 17: Power BI formatting is not his focus); Bharat does the clicks only Fabric can take.
**Done when.** The report is in prod through the deployment pipeline: Pipeline health and the weather visuals with `v0.1.0`, the trip visuals with `v1.0.0`, and the page Empty at rush hour with `v1.1.0`.

## FT25 · Semantic model and report

### US028 · Answers on one page each
As an operations lead, I want one page for demand against weather, one for empty stations and one for pipeline health, so that each question is answered at a glance.
- The model is Direct Lake; the report shows NY time and the Open-Meteo attribution.

#### T081 · `sm_citibike`: Direct Lake model, relationships and measures
- **Story:** US028
- **ADO:** #144
- **Owner:** Claude builds
- **Estimate:** 60 min
- **Sprint:** 4
- **Depends on:** T061
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5, docs/decisions.md ADR-012, docs/conventions.md §8–9
**Do**
1. Bharat: `wh_gold` → New semantic model → `sm_citibike`, tables `dim.date`, `dim.weather_hour`, `ctl.run_log`, `ctl.dq_result`; commit the workspace. These are the tables pass B loads. `dim.station`, `dim.region` and `fact.trip` join in T080 (pass C); `fact.station_hour` in T060 and `dim.weather_code` in T056 (version 1.1).
2. Claude (protocol §9) edits the TMDL: the relationship date to weather hour by local date key, `dim.date` marked as date table, measures (Run success rate, Failed checks, Avg temperature, Wet hours; names and units by `docs/conventions.md` §8), formats, hidden technical columns. Added with their tables later: date and station to `fact.trip`, weather hour to trips by `start_hour_utc`, region to station, and the measures Trips, Member share, Avg duration min and Wet-hour trips share (T080); the station-hour relationships and Minutes empty at rush, Stations empty at rush (T060); weather code to weather hour (T056).
3. Bharat pushes and presses Update all; refresh (framing) the model; mark it Promoted.
**Acceptance**
- [ ] The model opens in Direct Lake mode; every measure returns a value on a card.
- [ ] The relationship and the four measures match step 2.
**Result:** —

#### T082 · `rpt_citibike_ops`: the report, built page by page
- **Story:** US028
- **ADO:** #145
- **Owner:** Claude builds
- **Estimate:** 90 min
- **Sprint:** 4
- **Depends on:** T081
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/architecture.md §1, docs/conventions.md §8–9
**Do**
1. Bharat creates an empty report on `sm_citibike` named `rpt_citibike_ops` and commits.
2. Claude writes the PBIR pages that pass B has data for: **Pipeline health** in full (runs per day by status, failed checks table, last successful run) and **Demand and weather** with its weather visuals (daily temperature line, wet hours per day). Footer: "Weather data by Open-Meteo.com" and "Trip data: Citi Bike (NYCBS Data Use Policy)".
3. Bharat pushes, Update all, checks both pages in dev. They reach prod with the first release (T079).
4. Later, with their data: the trip visuals of **Demand and weather** (daily trips line with temperature, trips by wet/dry hour, member vs casual) in T080; the page **Empty at rush hour** (top 20 stations by rush-hour minutes empty, region slicer, hour-of-day heat map) in T060, version 1.1.
**Acceptance**
- [ ] Both pages render in dev with data; screenshots filed for the README.
**Result:** —

#### T083 · Direct Lake framing and fallback, shown
- **Story:** US028
- **ADO:** #146
- **Owner:** Bharat builds (Claude guides)
- **Estimate:** 30 min
- **Sprint:** 6
- **Depends on:** T072, T081
- **DP-700:** 3.1, 3.3
- **Status:** todo
- **Read first:** docs/decisions.md ADR-012, ADR-013
**Version 1.1 (ADR-029).** Not in version 1.0; built after T080, and only if the trial still has days left.
**Do**
1. Claude explains framing (what a refresh does in Direct Lake) and why warehouse RLS sends queries to DirectQuery.
2. Load a new day, see the report unchanged until the model is refreshed, refresh, see it change.
3. With Performance analyzer (or the model's query view), show one visual answered in Direct Lake for Bharat and in DirectQuery when the analyst's RLS applies.
**Acceptance**
- [ ] Both behaviours seen and screenshotted; the explanation is in the explained notes and becomes a README paragraph.
**Result:** —
