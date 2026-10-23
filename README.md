# Citi Bike operations lakehouse on Microsoft Fabric

A production-style data platform for New York's Citi Bike system, built end to end in Microsoft Fabric: REST and JSON ingestion, monthly bulk files, a live stream, a medallion lakehouse, a warehouse star schema, real-time alerts, and CI/CD across dev, test and prod.

It answers two questions: **how weather drives ride demand**, and **which stations run empty at rush hour**.

**Status:** being built (started October 2026). The design is in [`docs/architecture.md`](docs/architecture.md) and the decisions behind it in [`docs/decisions.md`](docs/decisions.md). This README is rewritten in full when the project is published.

Data: trip data from Citi Bike under the [NYCBS Data Use Policy](https://www.citibikenyc.com/data-sharing-policy); live station data from Citi Bike's public GBFS feed; weather data by [Open-Meteo.com](https://open-meteo.com/) (CC BY 4.0).
