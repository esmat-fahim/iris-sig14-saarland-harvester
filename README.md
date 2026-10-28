# IRIS-SIG-14 — Saarland public approval signal harvester

**Submission:** Python HTML Pattern B ETL, OpenSpec requirements, PostgreSQL 16/PostGIS 3.4 staging SQL, tests, and evidence samples. No production secrets or repository mutations.

## Executive summary and source

The specified `https://geoportal.saarland.de` was checked and is a Saarland GDI geodata/metadata service hub. A specific HTML listing of *Bekanntmachungen* there could **not** be confirmed. The public official inter-state UVP-Verbund portal includes Saarland proceedings in HTML, including three verifiable GreenSteel approvals. Therefore this deliverable uses the published **HTML** search at:

https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=

The exact observed search URLs, UUIDs, visible dates and source limitation are documented in [`docs/source_verification.md`](docs/source_verification.md). The site is a justified alternative, *not* a claim that `geoportal.saarland.de` itself exposes these records.

**Reproducibility distinction:** The public listing and three project details were verified through available web retrieval; runtime direct HTTP was unavailable in the execution environment. The test fixtures reconstruct representative HTML structure and must not be presented as downloaded original DOM. Live integration and actual PostgreSQL integration are pending; no unrestricted access is assumed.

## Data flow

```text
UVP Saarland HTML result pages (provider=sl; bounded pages)
  -> project detail HTML -> RawNotice (UUID/title/URL/listing date/decision date)
  -> Saarland + target-industry domain gate
  -> project-coordinate validation -> EPSG:25832 where supported
  -> normalized Signal + content hash + flags
  -> JSONL + quality report -> optional transactional PostGIS upsert
```

## Quick start (offline; no account/database needed)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
pytest -q
iris-sig14 --fixtures tests/fixtures --sqlite-demo demo.sqlite3 \
  --output samples/fixture_output.jsonl --report samples/quality_report.json
# Repeat the command: all unchanged signals => written=0, unchanged=4
```

To run without a SQLite demo file, simply omit `--sqlite-demo`.

## Optional: live HTML retrieval (not tested from this restricted environment)

```bash
iris-sig14 --live --max-pages 2 --delay 2 \
  --output samples/live_output.jsonl --report samples/live_quality.json
# Add --seed-verified-projects if searching the current index omits older GreenSteel examples.
```

Only `https://www.uvp-verbund.de` is permitted. HTTP 429/5xx are retried with backoff; requests use timeouts and a polite delay. 403s are **not** bypassed. No Selenium or protected endpoints are used. The program may need a selector update after a real-source smoke test. If the site is unavailable, use the repeatable offline fixtures and explain the restriction.

## Optional: local PostgreSQL 16 + PostGIS 3.4

The sample IRIS repository **does not publish** `iris_staging.signal_ingest` DDL. The contract in `sql/001_signal_ingest.sql` is a proposed **local** schema, not a verified production table. Inspect with your team before loading into a shared/production database.

```bash
# Optional if Docker is installed; use a LOCAL secret of your choosing:
export POSTGRES_PASSWORD='replace-with-a-strong-local-password'
docker compose up -d db
docker compose exec -T db psql -U iris_demo -d iris_demo < sql/001_signal_ingest.sql

# Supply credentials as an env var; don't commit any .env or URL.
export DATABASE_URL="postgresql+psycopg://iris_demo:${POSTGRES_PASSWORD}@localhost:5434/iris_demo"
# DATABASE_URL is exported: this run loads into the local PostGIS database.
iris-sig14 --fixtures tests/fixtures --output samples/fixture_output.jsonl \
   --report samples/quality_report.json
# Alternatively pass --db-url "$DATABASE_URL" without exporting DATABASE_URL.

docker compose exec -T db psql -U iris_demo -d iris_demo < sql/validation.sql
```

To prevent accidental DB loading during offline testing, make sure `DATABASE_URL` is unset. If you don't have Docker or a real PG server, SQLite demonstration provides a portable idempotency proof but **is not** PostGIS integration coverage. A real production `signal_ingest` table may require its own column mapping/constraints.

## Mapping rules and uncertainty

| Destination column | Source / rule |
|---|---|
| `source_system` | Fixed `uvp_verbund_sl_html` |
| `source_id` | URL `docuuid` (not guessed or title-derived) |
| `title` | Search result's linked title |
| `source_url` | Source detail URL from HTML link |
| `signal_type` | `heavy_industrial_restructuring_approval` or `power_substation_approval`, strict keywords with approval text |
| `listing_date` | Visible search-result date; **not assumed publication** |
| `decision_date` | Explicit detail-page `Datum der Entscheidung` |
| `publication_date` | Only explicit publication date; otherwise NULL + quality flag |
| `location_text` | City mentioned in **project** title/description, not ministry contact |
| `geom` | Point in EPSG:25832 only from explicit project coordinates, validated for Saarland bounds; otherwise NULL |
| `source_payload` | Source HTML textual excerpts and provenance; JSONB |
| `quality_flags` | Publication unverified, point unresolved, malformed coordinates, ambiguous location |
| `content_hash` | SHA256 of canonical normalized content; prevents rewriting unchanged records |

Dates are deliberately separate: e.g., **GreenSteel DRI Dillingen** is listed with `21.02.2025` and its explicit decision is `29.01.2025`; its original publication date is not independently confirmed. The EAF Dillingen listing points to a description of **Völklingen**, which is flagged for review.

**Coordinate QA:** no point is fabricated from a city centroid or the Ministry's Saarbrücken address. A synthetic test case exercises WGS84-to-ETRS89 / UTM zone 32N transformation; actual cited GreenSteel project pages did not supply a verifiable project point in the inspected rendered HTML. If source metadata later provides a valid site coordinate, it will be accepted and projected.

## Error handling / operations

- Requests: bounded retry/backoff for 429/5xx; timeout; HTTPS-only domain allowlist; non-HTML and empty responses rejected.
- Pagination: all fetched pages to configured maximum; stop when empty/duplicate page. No unreliable date-based early stop; changed older records remain discoverable.
- Extraction: UUID validity, geographic state check and signal classification; malformed details logged, listing evidence retained with warning.
- Loading: unique `(source_system, source_id)`, transactional `INSERT ... ON CONFLICT DO UPDATE` guarded by content hash, parameterized queries, no password in repository.
- Reports: outputs include counts, failures and per-field quality flags; SQL validation checks duplicates, SRIDs and missing metadata.

## Directory map

```text
src/iris_sig14/    models.py, source.py, normalize.py, pipeline.py, store.py, cli.py
openspec/          proposal, capability requirements, design and tracked tasks
sql/               local staging DDL and validation queries
tests/             unit/integration-lite tests plus reconstructed HTML fixtures
samples/           public examples, fixture output, concise quality report
docs/              source verification and known coverage limitations
```

## Status and known limitations

1. Unit/fixture tests: runnable offline and intended to be passed; duplicate re-runs proven with SQLite.
2. **Live raw DOM and rate-limit behavior:** not exercised by the authoring environment; selector robustness requires one authorized, throttled local smoke test.
3. **PostGIS integration:** SQL prepared but not executed against an actual database in this environment.
4. **Completeness:** UVP-Verbund covers only proceedings published there, not every industrial planning notification or every substation. Current sample provides real *steel* records but **no independently confirmed public substation approval**; substation path has synthetic test coverage only.
5. **Geolocation:** no guessed project points. Null geometries are expected when source points are unavailable. Geocoding could be added only with authoritative project identifiers/locations and accuracy flags.
6. **Publication dates:** not reconstructed from the decision date, file timestamp, crawl date or search listing date.

## OpenSpec workflow

Spec artifacts are provided in `openspec/changes/add-saarland-signal-harvester/` and follow `proposal -> specs and design -> tasks -> apply`. If OpenSpec CLI is installed locally: `openspec validate add-saarland-signal-harvester` (CLI syntax/version may vary). Installing: `npm install -g @fission-ai/openspec`, then run `openspec init` only if your editor's integration needs initialization; don't overwrite existing specs. The three unchecked tasks in `tasks.md` reflect outstanding live/PostGIS verification, not concealed completions.

## Reviewer reproducibility

Run the offline quick start twice, check `samples/quality_report.json`, inspect `samples/public_verified_examples.jsonl`, then optionally deploy the local DDL and execute `sql/validation.sql`. This demonstrates fail-closed parsing, traceability, idempotency, and explicit uncertainty without requiring IRIS credentials.

## Source-specific check: original Saarland Geoportal (HTML)

The brief names `https://geoportal.saarland.de`. The new **source reconnaissance** command directly inspects its public HTML applications catalogue, with no production credentials or DB writes:

```bash
python -m iris_sig14.geoportal \
  --report samples/geoportal_source_check.json \
  --save-html samples/geoportal_apps_snapshot.html
```

This command checks for **UVP-Verbund (extern)** (the Geoportal-linked official approvals portal) and **Kapazitäten der Umspannanlagen** (its substation/capacity map), and separately inspects the Geoportal-hosted substation application description. It produces a reviewable report. The raw snapshot is for local selector verification; inspect it before publishing or committing. Public accessibility and HTML structure must be rechecked on the candidate's machine.

Offline regression test, with a **synthetic miniature HTML fixture** (not a genuine downloaded DOM):

```bash
python -m iris_sig14.geoportal \
  --html-file tests/fixtures/geoportal_catalogue_sample.html \
  --article-file tests/fixtures/geoportal_substation_article_sample.html \
  --report samples/geoportal_fixture_check.json
pytest -q
```

**Data interpretation:** An existing substation or grid feed-in capacity is **not** an approval. The Geoportal catalogue does not itself supply a verified dated HTML list of the required approval notices. Consequently this check does not insert anything into `iris_staging.signal_ingest`, and the current approval ingestion remains on Geoportal's official external UVP-Verbund destination. Do not replace these provenance fields or label infrastructure entries as approved projects. A direct Geoportal approval adapter should be added only after verifying a genuine public approval listing and its publication dates.
