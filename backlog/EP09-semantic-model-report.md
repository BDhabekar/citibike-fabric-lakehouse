# EP09 · Semantic model and report

**Goal.** A Direct Lake semantic model on `wh_gold` and a three-page report that answer the two business questions. Claude does the modelling and report work (ADE HQ ruling of Oct 17: Power BI formatting is not his focus); Bharat does the clicks only Fabric can take.
**Done when.** The report is in prod through the deployment pipeline as v1.1.0.

## FT25 · Semantic model and report

### US028 · Answers on one page each
As an operations lead, I want one page for demand against weather, one for empty stations and one for pipeline health, so that each question is answered at a glance.
- The model is Direct Lake; the report shows NY time and the Open-Meteo attribution.

#### T081 · `sm_citibike`: Direct Lake model, relationships and measures
- **Story:** US028
- **ADO:** #144
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 60 min
- **Sprint:** 6
- **Depends on:** T061
- **DP-700:** 3.1
- **Status:** todo
- **Read first:** docs/data-contracts.md §5, docs/decisions.md ADR-012, docs/conventions.md §8–9
**Do**
1. Bharat: `wh_gold` → New semantic model → `sm_citibike`, tables `dim.date`, `dim.station`, `dim.region`, `dim.weather_hour`, `dim.weather_code`, `fact.trip`, `fact.station_hour`, `ctl.run_log`, `ctl.dq_result`; commit the workspace.
2. Claude (protocol §9) edits the TMDL: relationships (date to both facts by local date key; station to both facts; weather hour to trips by `start_hour_utc`; region to station; weather code to weather hour), `dim.date` marked as date table, measures (Trips, Member share, Avg duration min, Wet-hour trips share, Minutes empty at rush, Stations empty at rush, Run success rate, Failed checks), formats, hidden technical columns.
3. Bharat pushes and presses Update all; refresh (framing) the model; mark it Promoted.
**Acceptance**
- [ ] The model opens in Direct Lake mode; every measure returns a value on a card.
- [ ] Relationships match the list above.
**Result:** —

#### T082 · `rpt_citibike_ops`: three pages, released as v1.1.0
- **Story:** US028
- **ADO:** #145
- **Owner:** Claude builds
- **Model:** Sonnet
- **Estimate:** 90 min
- **Sprint:** 6
- **Depends on:** T081
- **DP-700:** 1.2
- **Status:** todo
- **Read first:** docs/architecture.md §1, docs/conventions.md §8–9
**Do**
1. Bharat creates an empty report on `sm_citibike` named `rpt_citibike_ops` and commits.
2. Claude writes the PBIR pages: **Demand and weather** (daily trips line with temperature, trips by wet/dry hour, member vs casual); **Empty at rush hour** (top 20 stations by rush-hour minutes empty, region slicer, hour-of-day heat map); **Pipeline health** (runs per day by status, failed checks table, last successful run). Footer: "Weather data by Open-Meteo.com" and "Trip data: Citi Bike (NYCBS Data Use Policy)".
3. Bharat pushes, Update all, checks each page, then releases through the path in T080 as `v1.1.0`.
**Acceptance**
- [ ] Three pages render in prod with data; screenshots filed for the README.
- [ ] Tag `v1.1.0` on `main`.
**Result:** —

#### T083 · Direct Lake framing and fallback, shown
- **Story:** US028
- **ADO:** #146
- **Owner:** Bharat builds (Claude guides)
- **Model:** Sonnet
- **Estimate:** 30 min
- **Sprint:** 6
- **Depends on:** T072, T081
- **DP-700:** 3.1, 3.3
- **Status:** todo
- **Read first:** docs/decisions.md ADR-012, ADR-013
**Do**
1. Claude explains framing (what a refresh does in Direct Lake) and why warehouse RLS sends queries to DirectQuery.
2. Load a new day, see the report unchanged until the model is refreshed, refresh, see it change.
3. With Performance analyzer (or the model's query view), show one visual answered in Direct Lake for Bharat and in DirectQuery when the analyst's RLS applies.
**Acceptance**
- [ ] Both behaviours seen and screenshotted; the explanation is in the explained notes and becomes a README paragraph.
**Result:** —
