# Candidate local integration observations — 2026-10-28

These results are transcribed from the candidate's terminal output and are **not** independently executed in the authoring environment. They document actual commands/results on macOS (Python 3.12, Docker PostGIS 16-3.4), distinguish real approvals from synthetic tests, and do not establish source completeness.

## Local tests and idempotency
- Initial `pytest -q`: 6 passed; later regression tests added. The CI runs from the published repository should be checked at the corresponding commit.
- Fixture SQLite run: `discovered=6`, `eligible=4`, `filtered=2`, initial `written=4`, identical second run `written=0`, `unchanged=4`.
- `docker compose ps`: database container `postgis/postgis:16-3.4` was `Up (healthy)`.
- `sql/001_signal_ingest.sql`: local `iris_staging.signal_ingest` table and indexes created.
- PostgreSQL nullable-coordinate bug initially caused `psycopg.errors.AmbiguousParameter`; fixed in `store.py` by explicit typed coordinate parameters. Candidate subsequently reported successful demo database loading.

## Real HTML and live database
- `iris-sig14 --live --max-pages 1 --delay 2` obtained `pages=1`, `discovered=10`, `eligible=3`, `filtered=7`, `duplicates_in_batch=0`.
- Actual records: GreenSteel DRI Dillingen (`d1d8a699-1303-46a7-bf89-c2f8a76dc25e`); GreenSteel EAF Dillingen (`543d4e12-3a2d-4eb2-a8a5-b0135ca8717c`); GreenSteel EAF Völklingen GmbH (`ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7`).
- Live `iris_live` insert: `written=3`, `unchanged=0`; SQL SELECT displayed all 3 UUIDs/titles and listing dates (2025-02-21, 2025-02-21, 2025-01-17). `publication_date` remained NULL due unverified original publication dates.
- All three live geometries were NULL due unavailable verified project coordinates. This is intentional; it does **not** demonstrate real geolocated approved projects.
- Candidate later confirmed successful live Postgres rerun with no new writes; the raw repeat output was not provided in the conversation and therefore is not independently archived. Do not confuse this with a CI integration test.
- Separate `iris_demo` test data includes **synthetic** `Genehmigung Umspannwerk Musterort`, with `ST_SRID(geom)=25832`, `ST_AsText(geom)=POINT(354658.795 5464953.74)`. It is not a real approval.

## Original Geoportal source check
- Candidate ran `python -m iris_sig14.geoportal --report samples/geoportal_source_check.json --save-html samples/geoportal_apps_snapshot.html`.
- Report: `evidence_mode=live_public_html`; official external UVP application and Geoportal substation capacity application listed. No direct Geoportal HTML approval listing verified within inspected pages, and no legal approval record derived from the capacity map.

## Unresolved work
- Capture and review *actual* UVP HTML and run unskipped regression test (`python -m iris_sig14.capture_live`). The original committed fixtures are reconstructed HTML.
- Confirm one **real standalone Saarland substation approval** if available; do not infer it from existing infrastructure capacity.
- Check actual IRIS production staging table contract and independently validate external OpenSpec CLI if applicable.

## Additional native Geoportal HTML OGC API Features check

The candidate ran Python `requests` against the **original** Geoportal's HTML features endpoint for `Immissionsschutz:BImsch_Anlagen` and `Immissionsschutz:IED_Anlagen` with `f=html&limit=5`. Both returned HTTP 200 and `text/html`; the displayed result pages showed 632 and 72 **facility** entries, respectively, with `NAME`, `INSPIRE_ID`, `ORT`, `RWERT`, `HWERT`, and a linked government page. These are not proven to be dated *approval notice* records. The original endpoint was reachable. The follow-on source-purpose decision is recorded at [`source_selection_adr.md`](source_selection_adr.md). No coordinate projection or approval matching is inferred from the unverified Geoportal `RWERT`/`HWERT` CRS.

## Evidence publication state

The two candidate-produced local files `samples/live_output.jsonl` and `samples/live_quality.json` have not yet been observed in the GitHub repository at this documentation update. Once added, the optional `tests/test_live_evidence.py` check becomes active. The authentic HTML capture manifest and snapshots are likewise absent from GitHub and require candidate capture/review.
