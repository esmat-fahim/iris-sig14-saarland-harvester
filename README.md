# IRIS-SIG-14 — Saarland approval signal harvester

I built this Python **Pattern B (HTML) ETL pipeline** for the IRIS-SIG-14 technical assignment. My implementation discovers relevant Saarland approval notices, normalizes their attributes, generates public-source JSONL and quality reports, and can load records idempotently into a local PostgreSQL 16/PostGIS 3.4 staging table.

I have included installation and configuration instructions, automated tests, reconstructed test fixtures, real public-source examples, validation SQL, OpenSpec artifacts, and an engineering decision record. I do not include database credentials or claim access to the private IRIS production schema.

## Why I selected UVP-Verbund rather than scraping approvals directly from Geoportal Saarland

I began with the endpoint specified in the brief, [Geoportal Saarland](https://geoportal.saarland.de). I inspected its public HTML application catalogue and substation-capacity application, then queried its own OGC API Features HTML listings for industrial facilities. Those direct requests succeeded: the observed pages advertised **632 BImSchG facilities** and **72 IED facilities**. They provided facility names, identifiers, addresses, coordinates and links to government information, but I did not verify a dated stream of individual restructuring or substation **approval decisions** in the surfaces I inspected.

I did **not** conclude that the original website is unavailable or that no other suitable dataset can exist on it. Rather, I distinguished *facility inventory* from *approval events*: a mapped industrial plant or substation is not evidence of a newly issued permit.

The Geoportal application catalogue explicitly lists **UVP-Verbund (extern)** as a linked environmental-proceedings application. I therefore chose the official UVP-Verbund **HTML** Saarland search as the source of approval notices:

https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=

I restrict the search to Saarland using `provider=sl` and preserve each notice's original URL and source identifier. I successfully ingested three public GreenSteel approval records from that source. This is my documented alternative-source decision under the assignment's allowance for justified alternatives; I would confirm with IRIS whether a specific native Geoportal approval feed was intended.

**Detailed rationale:** [ADR-001 — Approval source selection](docs/source_selection_adr.md). My source evidence and observed URLs are in [source verification](docs/source_verification.md).

## How my pipeline works

```text
UVP-Verbund Saarland public HTML search (provider=sl)
    -> bounded pagination and project detail HTML
    -> extraction: source UUID, title, URL, dates and description
    -> Saarland + target-approval classification
    -> validation and normalization
    -> project coordinate transformation only when supported
    -> JSONL + concise quality report
    -> optional PostgreSQL/PostGIS transactional, idempotent upsert
```

I separated the implementation into focused modules:

| Path | What it does |
|---|---|
| `src/iris_sig14/source.py` | Retrieves and parses public listing/detail HTML, applies request limits, retry rules and pagination |
| `src/iris_sig14/normalize.py` | Classifies notices, validates dates and coordinates, and assigns quality flags |
| `src/iris_sig14/pipeline.py` | Runs the ETL and prepares reports |
| `src/iris_sig14/store.py` | Writes to SQLite demonstration storage or PostgreSQL/PostGIS with conflict-safe upserts |
| `src/iris_sig14/cli.py` | Provides the `iris-sig14` command |
| `src/iris_sig14/geoportal.py` | Inspects the **original** Geoportal's public HTML applications catalogue without writing approval records |
| `src/iris_sig14/capture_live.py` | Saves authentic UVP HTML snapshots and a checksum manifest for offline selector regression testing |
| `sql/001_signal_ingest.sql` | Defines my **proposed local** staging schema |
| `sql/validation.sql` | Checks duplicates, missing metadata, quality flags and geometry SRIDs |
| `openspec/` | Contains my proposal, specification, design and tracked tasks |

## Installation and configuration

I used **Python 3.12** locally; the package requires Python 3.11 or newer. To create a fresh environment, I use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q -rs
```

On Windows PowerShell, the activation command is `.venv\Scripts\Activate.ps1`. My dependencies are declared in `pyproject.toml`, and configurable example values are in `.env.example`. I keep local credentials outside version control; `.env` and generated package metadata are ignored.

### Reproduce my fixture-based demonstration

I can run the offline ETL without network access or a PostgreSQL server:

```bash
unset DATABASE_URL
iris-sig14 --fixtures tests/fixtures --sqlite-demo demo.sqlite3 \
  --output /tmp/iris-sig14-fixture-output.jsonl \
  --report /tmp/iris-sig14-fixture-quality.json
```

On an initially empty SQLite demonstration database, I observed **four eligible unique records written**. Repeating the same run produced **zero writes and four unchanged records**, demonstrating duplicate-safe re-execution. One of those fixture records is an **explicitly synthetic** substation example; it is not a public permit.

### Run a bounded live HTML search

I use the following command to retrieve real notices without connecting to a database:

```bash
unset DATABASE_URL
iris-sig14 --live --max-pages 1 --delay 2 \
  --output /tmp/iris-sig14-live-output.jsonl \
  --report /tmp/iris-sig14-live-quality.json
```

I intentionally write ad hoc re-runs to `/tmp` so I do not overwrite the committed evidence in `samples/live_output.jsonl` and `samples/live_quality.json`. The source is restricted to `www.uvp-verbund.de`, with request timeouts, a delay, and bounded retry/backoff for 429/5xx. I do not bypass 403 responses or scrape protected endpoints. The parser may require maintenance if the source changes its HTML.

### Reproduce my local PostgreSQL/PostGIS setup

I tested against **PostgreSQL 16 + PostGIS 3.4** using Docker. I use a locally chosen password, not a credential committed to this repository:

```bash
export POSTGRES_PASSWORD='choose-your-own-local-password'
docker compose up -d db
docker compose exec -T db psql -U iris_demo -d iris_demo < sql/001_signal_ingest.sql

export DATABASE_URL="postgresql+psycopg://iris_demo:$POSTGRES_PASSWORD@localhost:5434/iris_demo"
iris-sig14 --fixtures tests/fixtures \
  --output /tmp/iris-sig14-pg-output.jsonl \
  --report /tmp/iris-sig14-pg-quality.json

docker compose exec -T db psql -U iris_demo -d iris_demo < sql/validation.sql
```

I also used a separate local `iris_live` database for actual UVP records, so I did not mix those records with synthetic fixtures. **I have not verified the private IRIS production table definition**: `sql/001_signal_ingest.sql` is my proposed local contract, not an authorized replacement for a production schema. I would reconcile it before loading into any shared database.

## Field mapping and data quality

I apply the following rules rather than inferring missing facts:

| Destination field | My mapping rule |
|---|---|
| `source_system` | `uvp_verbund_sl_html` |
| `source_id` | The original UVP `docuuid` |
| `title` | The linked project title |
| `source_url` | The public detail-page URL |
| `signal_type` | Classified as heavy-industrial restructuring approval or power-substation approval when supported by the notice |
| `listing_date` | Date shown in the search listing; **not automatically a publication date** |
| `decision_date` | Explicit decision date from the detail page |
| `publication_date` | Explicit publication date if available; otherwise `NULL` with a quality flag |
| `location_text` | Project-place text, not the authority's contact address |
| `geom` | Verified project point transformed to EPSG:25832 when sufficient source coordinates exist; otherwise `NULL` |
| `source_payload` | Source context and provenance |
| `quality_flags` | Missing or conflicting metadata requiring review |
| `content_hash` | SHA-256 of normalized content to avoid rewriting unchanged records |

I preserve listing, decision and publication dates separately. For example, **GreenSteel DRI Dillingen** has a search-listing date of 2025-02-21 and a decision date of 2025-01-29; I did not manufacture a publication date. I also flag the **GreenSteel EAF Dillingen** record because the detail text refers to **Völklingen**.

I do not fabricate coordinates from municipality centroids or the ministry's Saarbrücken contact address. My synthetic spatial test exercises conversion from WGS84 to EPSG:25832; the three verified live GreenSteel records have `NULL` geometry because I could not verify project-specific point coordinates.

## Actual live results and quality report

I ran the live harvester from my Mac on **2026-10-28**, then inserted three relevant GreenSteel records into local PostGIS. I tested a repeated load and saw **`written=0, unchanged=3`**.

The real, generated outputs are committed here:

- [Live JSONL output](samples/live_output.jsonl) — three observed public approval signals.
- [Live quality report](samples/live_quality.json) — one page, ten discovered results, three eligible, seven filtered, no reported fetch or malformed-record failures.
- [Public verified examples](samples/public_verified_examples.jsonl) — separate **hand-transcribed** public-source examples, not a raw harvester run.
- [Fixture quality report](samples/quality_report.json) and [fixture output](samples/fixture_output.jsonl) — reconstructed/synthetic test evidence, not real approval coverage.

My live quality report identifies **three unresolved project points**, **three unverified publication dates**, **one title/description site conflict**, and **zero within-batch duplicates**. These are explicit data-quality findings, not silent substitutions. I describe the local execution in [local execution evidence](docs/local_execution_evidence.md) and the limitations in [quality notes](docs/quality_notes.md).

## Testing and reproducibility

I reported **16 passing tests locally** on 2026-10-28, after downloading genuine UVP HTML consisting of one listing page and three eligible detail pages. The live capture discovered ten listings and three eligible records. I tested the saved DOM using:

```bash
unset DATABASE_URL
python -m iris_sig14.capture_live \
  --directory tests/fixtures/live_uvp \
  --max-details 3 --delay 2
pytest -q -rs
```

The capture creates a `manifest.json` with URLs, retrieval time and SHA-256 checksums. I keep the full downloaded HTML in `tests/fixtures/live_uvp/` **only on my Mac**, rather than redistributing whole pages. A limited contact-detail scan found email/contact links in the detail pages; that scan is not a complete privacy or licensing audit. The directory is excluded by `.gitignore`.

As a result, **a fresh checkout/CI run may skip the genuine-DOM regression test** because the local snapshots are absent. The representative reconstructed HTML tests and the committed live-output consistency check still run. Reviewers can capture fresh public HTML themselves with the command above, subject to site access and source changes. I do not present my reconstructed fixture HTML as an original downloaded copy.

I also checked the assigned original Geoportal directly:

```bash
python -m iris_sig14.geoportal \
  --report samples/geoportal_source_check.json \
  --save-html samples/geoportal_apps_snapshot.html
```

I committed the resulting [Geoportal source check](samples/geoportal_source_check.json). The HTML snapshot itself stays local. That inspection confirmed the official external UVP application and the Geoportal's substation-capacity application; it did not verify a native dated approval-notice listing in the inspected pages.

## OpenSpec workflow

I documented the design decisions and acceptance tasks in `openspec/changes/add-saarland-signal-harvester/`. To validate them with a compatible locally installed OpenSpec CLI, I would run:

```bash
openspec validate add-saarland-signal-harvester
```

I have not recorded an independent successful OpenSpec CLI validation yet; this remains an open checklist item. The [OpenSpec task list](openspec/changes/add-saarland-signal-harvester/tasks.md) distinguishes completed work from remaining gaps.

## Known limitations and follow-up work

1. **Source scope:** My chosen UVP-Verbund HTML search is a justified, Geoportal-linked alternative, not a direct approval-notice feed on `geoportal.saarland.de`. I have not established exhaustive coverage of Saarland approvals or parsed all referenced PDFs.
2. **Substation approval coverage:** The public live sample contains three steel-industry approvals, but I have **not yet independently verified a standalone Saarland power-substation approval**. The substation test case is synthetic.
3. **Exact project geometry:** The three live records have no source-verified project points. I deliberately keep their geometry `NULL`.
4. **Publication date provenance:** I do not substitute listing dates, decision dates or crawl timestamps for unverified publication dates.
5. **Source resilience:** I have implemented bounded pagination and retry logic, but have not demonstrated exhaustive multi-page coverage or every live server-side failure condition.
6. **Production integration:** My staging DDL and local PostGIS demonstration have not been checked against IRIS's private production schema.

I consider the Python implementation, configuration, README, automated tests, sample output, validation queries, quality reporting and source-selection rationale part of this submission. I keep the unresolved source-coverage questions explicit rather than claiming that every acceptance criterion has been demonstrated.
