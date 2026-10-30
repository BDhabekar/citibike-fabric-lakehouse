# Sources

Facts below were read from the live endpoints and the publishers' pages on Fri Oct 23, 2026. A line marked **(confirm in T###)** is a fact the named task checks before anything depends on it.

## 1. Open-Meteo historical weather (archive)

| | |
|---|---|
| Endpoint | `https://archive-api.open-meteo.com/v1/archive` |
| Auth | none (no key, no sign-up) |
| Limits | free for non-commercial use; fair use, contact them above 10,000 calls a day; this project makes under 20 calls a day |
| Licence | data under CC BY 4.0; attribution "Weather data by Open-Meteo.com" with a link, required in the README and on the report |
| Lag | the archive runs about 5 days behind today; hours not yet available come back as `null` |

**Request used by `pl_ingest_weather_archive`** (one call per calendar month, or less for the last chunk):

```
?latitude=40.7829&longitude=-73.9654
&start_date=2026-07-01&end_date=2026-07-31
&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,rain,snowfall,cloud_cover,wind_speed_10m,weather_code
&timezone=GMT
```

**Response shape** (parallel arrays, the part that needs real JSON handling):

```json
{
  "latitude": 40.78, "longitude": -73.97, "generationtime_ms": 1.2,
  "utc_offset_seconds": 0, "timezone": "GMT", "timezone_abbreviation": "GMT", "elevation": 39.0,
  "hourly_units": {"time": "iso8601", "temperature_2m": "°C", "precipitation": "mm", "snowfall": "cm", "wind_speed_10m": "km/h"},
  "hourly": {
    "time": ["2026-07-01T00:00", "2026-07-01T01:00", "..."],
    "temperature_2m": [24.1, 23.8, "..."],
    "precipitation": [0.0, 0.2, "..."]
  }
}
```

Element *i* of every array belongs to `time[i]`. Flattening means zipping the arrays, then exploding them into one row per hour (`arrays_zip` + `explode` in PySpark).

## 2. Open-Meteo forecast

| | |
|---|---|
| Endpoint | `https://api.open-meteo.com/v1/forecast` |
| Request | same `latitude`, `longitude`, `hourly` and `timezone` as above, plus `&past_days=3&forecast_days=2` |
| Why | fills the days the archive has not reached yet; ADR-018 says how the two are combined |

Ingested by `nb_ingest_weather_forecast` with `requests`: timeout 30 s, up to 5 attempts, exponential backoff 2, 4, 8, 16 s with jitter, retry only on 429, 5xx and connection errors.

## 3. GBFS feeds (Citi Bike, operated by Lyft)

Discovery file: `https://gbfs.citibikenyc.com/gbfs/2.3/gbfs.json` (`ttl` 60, `version` "2.3"). It points to feeds under `https://gbfs.lyft.com/gbfs/2.3/bkn/en/`. The project uses three:

| Feed | URL suffix | Used for | Frequency |
|---|---|---|---|
| `station_information` | `station_information.json` | station dimension (SCD2) | daily snapshot |
| `system_regions` | `system_regions.json` | region dimension, RLS | daily snapshot |
| `station_status` | `station_status.json` | live availability | every 60 s |

Every GBFS file has the same envelope: `last_updated` (Unix seconds), `ttl` (seconds), `version`, and `data`.

**`station_information` → `data.stations[]`**, fields seen on Oct 23: `station_id` (string; some are long numbers, some UUIDs), `name`, `short_name` (e.g. `"2312.02"`; this is the id that trip files use), `lat`, `lon`, `region_id`, `capacity`, `rental_uris` {`android`, `ios`}, `is_charging`. Example:

```json
{"station_id": "2124037250266884686", "name": "Colonial Rd & 89 St", "short_name": "2312.02",
 "lon": -74.03726, "lat": 40.62254, "region_id": "71", "capacity": 12,
 "rental_uris": {"android": "...", "ios": "..."}, "is_charging": false}
```

**`system_regions` → `data.regions[]`**: `region_id` (string) and `name`, nothing else; envelope `ttl` 60, `version` "2.3". Seven regions read on Oct 28: `70` JC District, `71` NYC District, `158` 8D, `185` Bronx, `189` IC HQ, `190` testzone, `311` Hoboken District. `8D`, `IC HQ` and `testzone` look like operational regions; T037 decides whether the dimension keeps them (read in a browser on Oct 28).

**`station_status` → `data.stations[]`**, fields seen on Oct 23: `station_id`, `num_bikes_available`, `num_ebikes_available`, `num_bikes_disabled`, `num_docks_available`, `num_docks_disabled`, `is_installed`, `is_renting`, `is_returning`, `last_reported` (Unix seconds), `vehicle_types_available[]` {`vehicle_type_id`, `count`}, `num_scooters_available` and `num_scooters_unavailable` (missing on uninstalled placeholder stations). `is_installed`, `is_renting` and `is_returning` may arrive as `0/1` or `true/false`; parsing accepts both. Station count: 2,521 entries in one poll on Oct 28, about 1.08 MB of JSON; every `is_*` flag arrived as `0/1` in that poll.

**Schema drift is expected.** Lyft adds fields without notice. Bronze stores the whole payload as text; silver parses with an explicit schema and ignores unknown fields; a new field is a decision, never a failure.

## 4. Citi Bike trip history

| | |
|---|---|
| Index | `https://s3.amazonaws.com/tripdata/index.html` (an S3 bucket listing) |
| File pattern | `https://s3.amazonaws.com/tripdata/YYYYMM-citibike-tripdata.zip` (files starting `JC-` are Jersey City and are ignored) |
| Publishing | monthly; the last eight files landed between the 4th and the 12th of the next month |
| Format | zip; a month with more than a million trips holds several CSVs, all with the same header |
| Licence | NYCBS Data Use Policy, `https://www.citibikenyc.com/data-sharing-policy`; attribution in the README |

Recent sizes (zipped): 2026-04 165 MB · 2026-05 917 MB · 2026-06 1,051 MB · 2026-07 974 MB · 2026-08 1,024 MB · 2026-09 972 MB (listed Oct 5).

**Columns** (current format): `ride_id`, `rideable_type`, `started_at`, `ended_at`, `start_station_name`, `start_station_id`, `end_station_name`, `end_station_id`, `start_lat`, `start_lng`, `end_lat`, `end_lng`, `member_casual`.

- `started_at` and `ended_at` are New York local time with no offset. Text format confirmed in T015 (Oct 30, 2026) on the top rows of `202604-citibike-tripdata-part1.csv` and `202606-citibike-tripdata_1.csv`: `yyyy-MM-dd HH:mm:ss.SSS`, a space between date and time, three fractional digits, no offset, for example `2026-04-06 18:55:38.804` and `2026-06-02 14:51:58.403`. The preview showed only the top of each file, so whether every row carries three fractional digits was not checked; T041 should test for it.
- The header of both files is the 13-column list above, exactly and in that order. Station ids are text with a decimal part (for example `7293.10`, `6740.01`).
- The CSV names inside the zip differ by month: 2026-04 holds `202604-citibike-tripdata-part1.csv` to `-part4.csv` (4 files, 179 MB each in the lakehouse listing); 2026-06 holds `202606-citibike-tripdata_1.csv` to `_6.csv` (6 files, 185 to 186 MB and one of 71 MB). A month folder is therefore read by `*.csv`, not by name.
- Measured in T015 with Copy on the trial capacity: the 2026-04 zip (164.6 MB) unzipped to 753.5 MB of CSV; the 2026-06 zip (1.051 GB) unzipped to about 1.0 GB. The ratio is not constant, so do not size bronze from the zip size.
- `start_station_id` and `end_station_id` are GBFS `short_name` values, not GBFS `station_id`s. Conformance is measured in T043.
- The publisher removes staff trips, test-station trips and trips under 60 seconds.
- Electric bikes can end away from a dock, so end station fields can be empty.
