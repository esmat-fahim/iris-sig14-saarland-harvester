# Proposal: add-saarland-signal-harvester

## Why
The IRIS-SIG-14 exercise requests public HTML approval notices for heavy-industry transformation and electricity substations in Saarland. The supplied `https://geoportal.saarland.de` is verifiably a GDI catalogue/map portal, not a verified standalone HTML publication list. The UVP-Verbund search provides public HTML project records in Saarland and actual steel-transition approvals.

## What Changes
- Add a configurable and bounded UVP-Verbund Saarland HTML acquisition adapter (Pattern B).
- Parse canonical project UUIDs, titles, listing dates, detail-page decision dates and provenance.
- Strictly filter Saarland and two signal categories; do not conflate publication, update/listing, and approval dates.
- Convert verified *project coordinates* to EPSG:25832; leave unresolved points null with explicit flags.
- Provide deterministic JSONL output and a PostgreSQL/PostGIS staging contract using identity-based upsert.
- Produce fixture tests, SQLite offline demonstration and visible QA report.

## Capabilities
### New Capabilities
- `saarland-signal-ingestion`: verified-source HTML acquisition, normalization, quality-gated spatial staging.

## Impact
Self-contained `iris_sig14` package, local `sql/` DDL, CLI, tests, sample artifacts, README.
No changes to, or rights in, the IRIS reference repository. No production connection is configured.

## Out of Scope
- Web browser bypass, login, CAPTCHA handling, or restricted-source scraping.
- PDF text extraction and municipal gazette/PDF discovery.
- Guessing precise locations from city names or an authority mailing address.
- Mapping onto unknown private IRIS `signal_ingest` schema without a contract.
