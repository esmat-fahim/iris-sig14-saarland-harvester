# IRIS-SIG-14 — Saarland Approval Signal Harvester

I built a Python **Pattern B (HTML) ETL pipeline** to discover Saarland approval notices, normalize and validate them, generate JSONL/quality reports, and load records idempotently into PostgreSQL 16/PostGIS 3.4.

## Source and engineering decision

The brief specifies [Saarland Geoportal](https://geoportal.saarland.de). I tested its HTML application catalogue and industrial-installation datasets; they were accessible, but I did not verify an HTML listing of individual dated **approval decisions** in the pages inspected. Existing facilities and substation capacity are not, by themselves, evidence of new approvals.

Because Geoportal officially lists **UVP-Verbund (extern)** for environmental proceedings, I selected its public [Saarland-filtered HTML search](https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=), with `provider=sl`. I retain each notice's original ID and URL and do not claim to scrape approval events directly from Geoportal. I would confirm with IRIS if a specific native Geoportal approval feed was intended.

**Full rationale:** [ADR-001](docs/source_selection_adr.md) · [Source verification](docs/source_verification.md) · [Direct Geoportal check](samples/geoportal_source_check.json)

## Setup and run

I used Python 3.12; **Python 3.11+** is required. Dependencies are in `pyproject.toml` and optional settings are described in `.env.example`. No credentials are committed.

```bash
python3 -m venv .venv
source .venv/bin/activate                 # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
pytest -q -rs
```

To run a **complete offline ETL** without network access or PostgreSQL:

```bash
unset DATABASE_URL
iris-sig14 --fixtures tests/fixtures --sqlite-demo demo.sqlite3 \
  --output /tmp/iris-fixture-output.jsonl \
  --report /tmp/iris-fixture-report.json
```

Run that command twice against a **fresh** `demo.sqlite3` database. I observed **4 records written** initially, then **0 written / 4 unchanged**, demonstrating idempotency. The fixtures include one explicitly **synthetic substation** case.

To collect **live notices** without database writes:

```bash
unset DATABASE_URL
iris-sig14 --live --max-pages 1 --delay 2 \
  --output /tmp/iris-live-output.jsonl \
  --report /tmp/iris-live-report.json
```

Live output varies as the source changes. HTTP requests use a domain allowlist, timeouts, bounded retries, and polite delays; access controls are not bypassed. Temporary output paths avoid overwriting committed evidence.

### Optional PostgreSQL/PostGIS demonstration

With Docker, I used the following **local-only** PostgreSQL 16/PostGIS 3.4 setup:

```bash
export POSTGRES_PASSWORD='choose-a-local-password'
docker compose up -d db
docker compose exec -T db psql -U iris_demo -d iris_demo < sql/001_signal_ingest.sql

export DATABASE_URL="postgresql+psycopg://iris_demo:${POSTGRES_PASSWORD}@localhost:5434/iris_demo"
iris-sig14 --fixtures tests/fixtures \
  --output /tmp/iris-pg-output.jsonl \
  --report /tmp/iris-pg-report.json

docker compose exec -T db psql -U iris_demo -d iris_demo < sql/validation.sql
```

If the password contains URL-special characters, URL-encode it in `DATABASE_URL`. The DDL is a **proposed local** `iris_staging.signal_ingest` schema, not a verified IRIS production contract.

## Field mapping and quality rules

- **Identity:** original UVP `docuuid`, source URL and `source_system`; content-hash-guarded transactional upsert prevents repeated writes.
- **Dates:** listing, decision, and publication dates are distinct. I leave unverified `publication_date` as `NULL` with a quality flag.
- **Geometry:** only verified project coordinates are converted to **EPSG:25832**; otherwise geometry remains `NULL`. I do not infer site points from ministry addresses or municipality centroids.
- **Scope:** I filter for Saarland heavy-industrial restructuring and substation approval signals, preserving source context and flagging ambiguity.

Detailed behavior is in the [OpenSpec requirements](openspec/changes/add-saarland-signal-harvester/specs/saarland-signal-ingestion/spec.md) and [design](openspec/changes/add-saarland-signal-harvester/design.md).

## Evidence and tests

On **28 October 2026**, I retrieved **10 live notices**, selected **3 GreenSteel industrial approvals**, and ingested those into local PostgreSQL/PostGIS. A repeated load reported **0 written / 3 unchanged**.

- [Actual live JSONL (3 approvals)](samples/live_output.jsonl) · [Live quality report](samples/live_quality.json)
- [Fixture output](samples/fixture_output.jsonl) · [Fixture quality report](samples/quality_report.json)
- [Validation SQL](sql/validation.sql) · [Execution evidence](docs/local_execution_evidence.md) · [QA notes](docs/quality_notes.md)

The live report records **3 unverified publication dates, 3 unresolved project points, and 1 site-description conflict**.

I passed **16 automated tests locally**, including a regression test with genuinely captured public HTML. I also tested a **fresh GitHub clone**: installation succeeded, **15 tests passed and 1 was expectedly skipped**, and the full offline ETL ran idempotently. GitHub Actions tests the published project on Ubuntu/Python 3.11 and 3.12.

I keep genuine downloaded HTML snapshots **local only** because redistribution has not been cleared. Thus the real-DOM regression test is skipped in a clean clone, while the published reconstructed fixtures and live-output consistency tests remain runnable.

## Known limitations

- The live sample demonstrates **industrial approvals**, not a verified **standalone substation approval**; that case is covered only by a synthetic fixture.
- Verified project-point coordinates and explicit publication dates were unavailable for the three live records; missing values remain `NULL`.
- I have not demonstrated exhaustive Saarland approval coverage, parsed all linked PDFs, or tested against IRIS's private production schema.
- The selected source is the Geoportal's **linked UVP-Verbund application**, not a native Geoportal approval feed; see [ADR-001](docs/source_selection_adr.md).

## License

I license my original code and documentation under [MIT](LICENSE). This does not license third-party website content, datasets, or downloaded HTML.
