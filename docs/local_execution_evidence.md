# My local integration and reproducibility evidence — 2026-10-28

I recorded the following results from commands I ran on my Mac (Python 3.12 and a local Docker PostgreSQL 16/PostGIS 3.4 container). These are **my local observations**, not claims that I accessed IRIS's production environment or that the full run was independently reproduced in CI. My published samples and the automated workflow provide additional reviewable evidence.

## Offline tests and database re-runs

- I initially ran `pytest -q` with 6 passing tests; I added more regression tests as development progressed. The [GitHub Actions workflow](../.github/workflows/tests.yml) runs the published test suite on Linux with Python 3.11 and 3.12.
- I ran the fixture pipeline in SQLite: 6 discovered, 4 eligible, 2 filtered; the first execution wrote 4 records, and the second wrote **0** with **4 unchanged**.
- I started a local `postgis/postgis:16-3.4` Docker container and verified that it was healthy.
- I created my demonstration `iris_staging.signal_ingest` table and indexes using `sql/001_signal_ingest.sql`.
- I encountered `psycopg.errors.AmbiguousParameter` when loading null coordinates, corrected the SQL by explicitly typing the coordinate parameters, and subsequently loaded data successfully.

## Live approval ingestion into PostGIS

I ran `iris-sig14 --live --max-pages 1 --delay 2` against the public Saarland-filtered UVP HTML search. It returned **1 page, 10 discovered, 3 eligible, 7 filtered**, with no within-batch duplicates.

I ingested three actual public industrial approval notices:

| Source UUID | Project | Listing date |
|---|---|---|
| `d1d8a699-1303-46a7-bf89-c2f8a76dc25e` | GreenSteel DRI Dillingen | 2025-02-21 |
| `543d4e12-3a2d-4eb2-a8a5-b0135ca8717c` | GreenSteel EAF Dillingen | 2025-02-21 |
| `ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7` | GreenSteel EAF Völklingen GmbH | 2025-01-17 |

I loaded these records into a separate local `iris_live` database to avoid mixing real records with synthetic fixtures. My initial run wrote **3 records**. My repeated live report records **0 written / 3 unchanged**, as preserved in [live_quality.json](../samples/live_quality.json). I left `publication_date` and `geom` as `NULL` where I could not independently verify a publication date or project point.

I separately checked a **synthetic** substation fixture in `iris_demo`. Its geometry produced `ST_SRID(geom)=25832` and `POINT(354658.795 5464953.74)`. I do **not** represent this as a real substation approval.

## Direct investigation of the assigned Geoportal

I ran the public HTML reconnaissance tool:

```bash
python -m iris_sig14.geoportal \
  --report samples/geoportal_source_check.json \
  --save-html samples/geoportal_apps_snapshot.html
```

My [source-check report](../samples/geoportal_source_check.json) confirmed Geoportal's official **UVP-Verbund (extern)** application and a **substation capacity** application. Neither inspected page was a verified native list of approval decisions.

I also queried **the original Geoportal domain** for the `Immissionsschutz:BImsch_Anlagen` and `Immissionsschutz:IED_Anlagen` OGC API Features collections using HTML responses (`f=html&limit=5`). Both returned HTTP 200. Their displayed listings showed **632** and **72** industrial *facilities*, respectively, with IDs, locations, coordinate fields and external URLs. I did **not** assume these were individual dated approval events or that their `RWERT`/`HWERT` coordinate system had been verified. I explain my source choice in [ADR-001](source_selection_adr.md).

## Genuine HTML capture and local regression

On 2026-10-28 I ran:

```bash
python -m iris_sig14.capture_live \
  --directory tests/fixtures/live_uvp \
  --max-details 3 --delay 2
pytest -q -rs
```

The capture summary recorded `captured_at_utc=2026-10-28T15:48:03.312204+00:00`, **10 discovered listing records, 3 eligible, and 3 saved detail pages**. I reported **16 passing tests** with the genuine HTML snapshot available locally. The actual snapshot files and the detailed local terminal log have **not** been independently inspected from the public GitHub repository.

I ran a limited local contact scan: each of the three detail pages contained one email address and two `mailto:` links, and the listing page contained one `mailto:` link. Because I have **not** completed a full privacy/rights audit, I retain these downloaded pages **locally** rather than committing complete third-party HTML to GitHub. The published reconstructed fixtures are separate from this genuine HTML; clean CI skips the real-DOM test until a fresh snapshot is captured.

## Fresh-clone reproducibility

I also cloned the public repository into a **new folder and Python 3.12 virtual environment** on my Mac, installed the project from `pyproject.toml`, and ran `pytest -q -rs`. The fresh checkout reported **15 passed, 1 expected skip** because the private HTML snapshots were absent.

I ran the offline fixture ETL twice against a newly created SQLite demonstration database: the first run reported **4 written / 0 unchanged**; the second reported **0 written / 4 unchanged**. This supports reproducibility without my original project directory, credentials or a PostgreSQL server.

## What I have not established

- I have **not** confirmed an actual, standalone Saarland substation approval from an authoritative dated publication; my substation fixture is synthetic.
- I have not mapped the local demonstration schema to IRIS's private production table.
- I have not claimed exhaustive approval coverage or live testing of every possible network failure.
- I have not recorded an independent successful OpenSpec CLI validation.

I keep those gaps in my [OpenSpec checklist](../openspec/changes/add-saarland-signal-harvester/tasks.md).
