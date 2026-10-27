# Cost and capacity

## 1. The build costs ₹0, and nothing can bill by accident

- The project runs on the **Fabric trial capacity**: 60 days, no credit card. The capacity Fabric actually gave is **4 capacity units (an F4)**, not 64 (see ADR-023). [Microsoft Learn: Fabric trial capacity](https://learn.microsoft.com/en-us/fabric/fundamentals/fabric-trial) and [Get started with Microsoft Fabric](https://microsoft.com/microsoft-fabric/getting-started), read Oct 23, 2026.
- The trial lives in Bharat's own tenant (`bharat-ade`). **No Azure subscription is attached to Fabric during the build.** The tenant's own Azure subscription is expired, so there is no payment method anywhere in the path. A bill is impossible, not just unlikely.
- GitHub Actions is free for public repositories, and private repositories on GitHub Free get 2,000 minutes a month. CI here uses a few minutes a day.
- The only money in the plan is the DP-700 exam fee (₹4,865 in the ADE plan; check the price, and any free-voucher offer, at booking).

## 2. Trial facts that shape the plan

| Fact | What it means here |
|---|---|
| 60 days from the day it starts | Started in T004. The start and end dates are written in §6 below the same day. |
| 4 CU, the size of an F4 (read in the Admin portal on Oct 26, 2026; the size cannot be changed) | An F4 is twice an F2 and 1/16 of the F64 first assumed. Whether it is enough is ADR-023 (Proposed). Timings seen on the trial are **not** what a larger capacity would give. Say so in interviews. |
| Needs a per-user Power BI licence | The free Fabric licence, taken in T003. The trial includes a Power BI individual trial. |
| When it ends | Workspaces drop off the capacity. Content is kept for 7 days and can be reattached to a paid capacity in that window, then it is gone. |
| Cannot be restarted once cancelled | Never press Cancel trial. |

**Durable record.** Everything that matters is in Git from T011 onwards (items as code, docs, tests, screenshots in ADE HQ). When the trial ends, the repo still shows the whole project. A live demo after that is the only thing that would need money (§3).

## 3. If a live workspace is ever needed after the trial (pay-as-you-go F2)

Do not do this without a written decision. These are the numbers to decide with.

**Rates.**

| Item | Rate | Source and confidence |
|---|---|---|
| F2 capacity, US regions (East US, West US 2) | $0.18 per CU-hour → **$0.36 an hour** for F2 | several pricing guides dated Oct 2026; consistent with each other |
| F2 capacity, Central India | $0.20 per CU-hour → **$0.40 an hour** | one pricing guide, Oct 2026: **unverified**. The Azure portal shows the exact INR price when the capacity is created; read it there first |
| Billing granularity | per second, 1-minute minimum | Microsoft pricing page |
| Paused capacity | no compute charge; storage still billed | Microsoft Learn, OneLake consumption |
| Pausing after a burst | any smoothed usage above the F2 size is billed at once when you pause | Fabric community, accepted answer |
| OneLake storage | about $0.023 per GB a month; soft-deleted data billed the same | community answer: **unverified**; check the pricing page for the region |
| Power BI Pro (needed to share reports on a capacity smaller than F64) | about $14 per user a month list | **check the India price at purchase** |
| Exchange rate used below | 1 USD = ₹94.81 | mid-market, Oct 23, 2026 |
| GST | 18% added on Indian invoices | **assumption**; confirm on the first invoice |

**What an F2 in Central India would cost** (at the unverified $0.40 an hour):

| Use | Hours a month | Before GST | With 18% GST |
|---|---|---|---|
| One hour | 1 | ₹38 | ₹45 |
| A few demos and interview screen-shares | 10 | ₹379 | ₹447 |
| Two hours every day | 60 | ₹2,275 | ₹2,685 |
| **Left running by mistake for a month** | 730 | **₹27,684** | **₹32,667** |
| Storage for about 20 GB, every month, even paused | | ₹44 | ₹51 |

The last capacity row is the trap. Every guardrail below exists to stop it.

## 4. Guardrails, if a paid capacity is ever created

1. **F2 only.** Never a larger SKU, never a reservation (a reservation bills every hour for a year whether used or not).
2. **Budget first.** Before the capacity exists, a ₹500 monthly budget on the subscription, alerts at 50%, 90% and 100% to Gmail, and the same mail checks ADE HQ already runs.
3. **Paused by default.** Resume for a session, pause at the end of it. Write the resume and pause times in the ADE HQ log.
4. **A nightly automatic pause.** An Azure Automation runbook (or a Logic App) suspends the capacity at 23:00 IST every night, so a forgotten resume costs one evening, not a month. Built and tested before the first resume.
5. **No always-on streaming.** The Eventstream is stopped and the Eventhouse has no minimum consumption set. The live path is a trial-only feature unless a decision says otherwise.
6. **No extra billing switches.** Autoscale Billing for Spark off. Capacity overage (preview, billed at three times the pay-as-you-go rate) off. OneLake disaster-recovery storage off.
7. **Read the cost by meter** the day after every use (the habit from the Olist project).

## 5. Capacity use during the trial

The trial has no price, but it has a size. Watch it in the Capacity Metrics app (installed in T005):

- Run notebooks on the starter pool, and never leave a session running: stop it from the notebook toolbar when a sitting ends.
- The live Eventstream polls every 60 seconds, all day. In dev it is stopped after T050; it runs continuously only in prod.
- If the metrics app shows throttling, the fix is fewer concurrent jobs, not a bigger capacity.

**Baseline read in T005 (Tue Oct 27, 2026; Compute page, 14-day view, data from Oct 26).** SKU F4 (the app labels it FTL4), average utilization 7.62%, peak 10.04%, no throttling, nothing rejected. Almost all of it came from one practice notebook session of about 2 h 21 min: 33,937 of the 34,705 CU-seconds in total. The lakehouse and its SQL endpoint spent the rest. With no work running, usage is near zero, so read 7.62% as the cost of one sitting, not an idle level. An F4 holds 4 x 86,400 = 345,600 CU-seconds a day, and 34,705 / 345,600 = 10.04%, which is exactly the peak: background work is spread over about 24 hours (from memory, unverified), so the peak is the sitting's total divided by a day's capacity. Rough budget: about ten sittings of that size a day before 100%, fewer when sittings overlap. This is the measured input for ADR-023 option (a). The app's own workspace is of type Power BI Pro (Workspace settings → Workspace type, Oct 27, 2026), so it is not assigned to the trial capacity and its refreshes do not spend F4 CU (my reading of the workspace type; Microsoft advises a Pro workspace for this reason). Source: Microsoft Fabric Capacity Metrics app, Compute page, read Oct 27, 2026.

## 6. Trial dates (filled in by T004)

| | |
|---|---|
| Trial started | Mon Oct 26, 2026, about 02:21 IST (the capacity's own name carries 2026-10-25 20:51 UTC) |
| Trial ends | about Fri Dec 25, 2026 (60 days from the start; the Admin portal showed 59 days left at 09:15 IST on Oct 26) |
| Region chosen | Central India (the default offered; no choice was needed) |
| Capacity size | 4 CU (F4), cannot be resized |
| Last day to finish screenshots, publish and DP-700 practice on live items | Fri Dec 18, 2026 (trial end minus 7 days) |
