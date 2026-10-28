# IRIS-SIG-14 — Saarland public approval signal harvester

**Submission:** Python HTML Pattern B ETL, OpenSpec requirements, PostgreSQL 16/PostGIS 3.4 staging SQL, tests, and evidence samples. No production secrets or repository mutations.

## Executive summary and source

The specified `https://geoportal.saarland.de` was checked and is a Saarland GDI geodata/metadata service hub. A specific HTML listing of *Bekanntmachungen* there could **not** be confirmed. The public official inter-state UVP-Verbund portal includes Saarland proceedings in HTML, including three verifiable GreenSteel approvals. Therefore this deliverable uses the published **HTML** search at:

https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=

The exact observed search URLs, UUIDs, visible dates and source limitation are documented in [`docs/source_verification.md`](docs/source_verification.md). The site is a justified alternative, *not* a claim that `geoportal.saarland.de` itself exposes these records.

**Why an alternative host?** The original Geoportal is accessible and exposes HTML industrial/IED facility features and a substation-capacity application, but no individual dated approval-notice stream was verified in the inspected pages. Crucially, its catalogue lists **UVP-Verbund (extern)** for approval proceedings. We chose that official *linked* HTML publication source for legal approval signals, while keeping Geoportal facility inventory separate from approvals. See **[ADR-001: approval source selection](docs/source_selection_adr.md)** for observed endpoints, alternatives rejected, risks and the condition for revisiting this decision. This is a justified choice under the assignment's alternative-source clause, but still needs IRIS reviewer confirmation if a particular native Geoportal feed was intended.

**Reproducibility distinction:** The public listing and three project details were verified through available web retrieval; runtime direct HTTP was unavailable in the execution environment. The test fixtures reconstruct representative HTML structure and must not be presented as downloaded original DOM. The candidate subsequently executed a live Saarland HTML search and local PostgreSQL/PostGIS ingestion on their Mac on 2026-10-28; see [`docs/local_execution_evidence.md`](docs/local_execution_evidence.md). Actual raw HTML snapshot capture is still pending and is not included in the reconstructed fixtures.

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

## Optional: live HTML retrieval (candidate-tested on macOS, 2026-10-28)

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
2. **Genuine HTML regression fixture:** candidate successfully retrieved a live HTML page, but the actual raw DOM has not yet been saved as a reviewed, reproducible fixture. Live 429 behavior is not demonstrated.
3. **PostGIS integration:** candidate reported successful local PostgreSQL 16/PostGIS 3.4 loads, SQL verification, null geometries for public records, synthetic EPSG:25832 point, and an unchanged rerun. These observations are candidate-supplied, not independently reproduced in the authoring environment.
4. **Completeness:** UVP-Verbund covers only proceedings published there, not every industrial planning notification or every substation. Current sample provides real *steel* records but **no independently confirmed public substation approval**; substation path has synthetic test coverage only.
5. **Geolocation:** no guessed project points. Null geometries are expected when source points are unavailable. Geocoding could be added only with authoritative project identifiers/locations and accuracy flags.
6. **Publication dates:** not reconstructed from the decision date, file timestamp, crawl date or search listing date.

## OpenSpec workflow

Spec artifacts are provided in `openspec/changes/add-saarland-signal-harvester/` and follow `proposal -> specs and design -> tasks -> apply`. If OpenSpec CLI is installed locally: `openspec validate add-saarland-signal-harvester` (CLI syntax/version may vary). Installing: `npm install -g @fission-ai/openspec`, then run `openspec init` only if your editor's integration needs initialization; don't overwrite existing specs. See `tasks.md` for explicit remaining source-fixture, standalone substation, and production-schema verification tasks.

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


## Genuine live HTML regression capture (next step)

Previously committed `tests/fixtures/listing*.html` files are **reconstructed**, not verbatim downloaded pages. The candidate successfully ran the following capture on 2026-10-28, saving one genuine search page plus three details locally (10 discovered, 3 eligible), without modifying either PostGIS database:

```bash
unset DATABASE_URL
python -m iris_sig14.capture_live \
  --directory tests/fixtures/live_uvp \
  --max-details 3 --delay 2
pytest -q -rs
```

The capture requests exactly **one Saarland search page** and at most **three eligible project detail pages**, with a delay between detail requests and the existing HTTPS host allowlist. It saves a first-page snapshot, individual detail-page snapshots, and `manifest.json` with the actual captured URLs, timestamp (UTC), byte lengths, and SHA-256 checksums. No HTML is fabricated. If no records can be parsed, the capture fails rather than passing silently. No credentials are required.

The `test_real_live_html_selector_regression` test is **skipped on a checkout lacking** `tests/fixtures/live_uvp/manifest.json` (including clean CI). On the candidate Mac, that manifest was generated and the candidate reported `pytest -q -rs` **16 passed** on 2026-10-28. This is local candidate evidence, not independently replayed from published raw HTML. The regression verifies file checksums, parses the saved DOM, checks listing counts and detail normalization. Genuine captured HTML is still local-only pending review.

**Before publishing the captured snapshot**, inspect the downloaded HTML and ensure redistribution is appropriate, including reviewing public personal/contact data. If sharing full source HTML is not appropriate, keep it local and document it as candidate-held test evidence rather than silently replacing it with a reconstructed example. The command does not claim any standalone substation approval was found; real electrical substation approval coverage is still outstanding.

## Candidate live evidence: review and commit (not yet uploaded)

The successful candidate-run sample and quality report exist **only on the candidate's Mac until committed**. Do not substitute the hand-transcribed examples for these genuine files. In the repository root:

```bash
# Review the actual output for unexpected sensitive material before publication.
python -m json.tool samples/live_quality.json
head -n 1 samples/live_output.jsonl
# Confirm both belong to your successful live run; then explicitly stage only these:
git add samples/live_output.jsonl samples/live_quality.json
git commit -m "Add candidate live UVP ingestion output and quality report"
git push origin main
pytest -q -rs
```

`tests/test_live_evidence.py` automatically checks consistency of those two files *when present*, but skips in CI until they have been committed. If one is present without the other, the test fails. Re-running the live harvester after output capture may overwrite the report, so review the final pair together. Neither file should contain database credentials; verify before committing.

To complete **real HTML regression coverage**, run the capture documented above on the candidate Mac and ensure `pytest -q -rs` reports that `test_real_live_html_selector_regression` is no longer skipped. Captured HTML may include public personal/contact information; review it before deciding whether to check the snapshots into a public repository. An uncommitted local capture is evidence of the candidate's test but is not reproducible by a remote reviewer.

## Verified live output evidence

The actual candidate-produced `samples/live_output.jsonl` and `samples/live_quality.json` were committed on 2026-10-28 (commit `1f04f6e`). The report describes a re-run with `written=0, unchanged=3`; initial inserts and source checks are recorded separately in `docs/local_execution_evidence.md`. The engineering justification for using Geoportal's officially linked UVP-Verbund approval application rather than treating Geoportal infrastructure features as dated approvals is maintained in [ADR-001](docs/source_selection_adr.md).
