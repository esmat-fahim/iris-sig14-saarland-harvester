# Proposal: add-saarland-signal-harvester

## Why
I am addressing the IRIS-SIG-14 request for public HTML approval notices for heavy-industry transformation and electricity substations in Saarland. I inspected the supplied `https://geoportal.saarland.de`, including its HTML facility collections, but did not verify a native dated approval-notice list in those pages. I selected its officially linked UVP-Verbund HTML search for identifiable Saarland proceedings and steel-transition approvals.

## What I implemented
- I added a configurable and bounded UVP-Verbund Saarland HTML acquisition adapter (Pattern B).
- I parse canonical project UUIDs, titles, listing dates, detail-page decision dates and provenance.
- I filter Saarland and two signal categories; do not conflate publication, update/listing, and approval dates.
- I convert verified *project coordinates* to EPSG:25832; leave unresolved points null with explicit flags.
- I provide deterministic JSONL output and a PostgreSQL/PostGIS staging contract using identity-based upsert.
- I produce fixture tests, SQLite offline demonstration and visible QA report.

## Capabilities
### New Capabilities
- `saarland-signal-ingestion`: verified-source HTML acquisition, normalization, quality-gated spatial staging.

## Impact
I provide a self-contained `iris_sig14` package, local `sql/` DDL, CLI, tests, sample artifacts and README. I have not changed the IRIS reference repository, claimed rights over its contents, or configured a production connection.

## What I excluded
- I do not bypass browser restrictions, login, CAPTCHAs or access controls.
- I have not implemented PDF extraction or comprehensive municipal-gazette discovery.
- I do not guess project coordinates from municipality names or an agency address.
- I do not load data into an unknown private IRIS `signal_ingest` table without a schema contract.
