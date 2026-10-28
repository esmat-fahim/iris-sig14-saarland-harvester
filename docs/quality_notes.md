# Quality and error report — reviewer handoff

**Evidence date:** 2026-10-28. Separate **candidate-run local observations** from **committed fixture examples**. No connection to an IRIS production database is claimed.

## Live source, local PostgreSQL and results

On the candidate's Mac, Python 3.12 retrieved the UVP-Verbund Saarland first results page via public HTML (`provider=sl`). Terminal output showed `pages=1`, `discovered=10`, `eligible=3`, `filtered=7`, `duplicates_in_batch=0`, and no reported fetch failures in the displayed summary. The three eligible records were GreenSteel DRI Dillingen, GreenSteel EAF Dillingen and GreenSteel EAF Völklingen GmbH. Their candidate-run local `iris_live` database reported `written=3, unchanged=0` on first insertion and the candidate confirmed unchanged records on rerun. A SQL query displayed the three UUIDs and listing dates. This is local **PostgreSQL 16/PostGIS 3.4** evidence, not an assertion that the IRIS production schema was tested.

The candidate also tested a **synthetic** substation fixture in local PostGIS, yielding `POINT(354658.795 5464953.74)` at SRID `25832`; it must not be presented as a real approval.

## Quality exceptions surfaced by the live run

| Issue | Count | Handling |
|---|---:|---|
| `publication_date_not_verified` | 3 | Preserve `NULL`; never confuse listing/decision date with publication date |
| `unresolved_project_point` | 3 | Preserve `NULL` PostGIS geometry; no city-centroid or authority-address guess |
| `title_description_site_conflict` | 1 | Flag ambiguous Dillingen/Völklingen text for manual review |
| `duplicates_in_batch` | 0 | None found on the first live page; primary-key/upsert rerun checks remain applicable |

The first-page live result was a successful source/loader smoke test; it does **not** demonstrate full pagination, complete substation coverage or a reliable official project-level coordinate.

## Distinguish committed evidence

- `samples/public_verified_examples.jsonl` is **hand-transcribed public-source evidence**, NOT a recording of the Python live output.
- `samples/fixture_output.jsonl` and `samples/quality_report.json` are derived from **reconstructed/synthetic** test inputs; their count is four, including one synthetic substation.
- The candidate's actual `samples/live_output.jsonl` and `samples/live_quality.json` were generated locally but **are not yet checked into GitHub**. Commit them together after inspecting them for unexpected personal information; the repository's optional evidence regression test will then check their consistency.
- `tests/fixtures/live_uvp/` is intentionally absent until the candidate runs the live capture command. Until the manifest exists, `test_real_live_html_selector_regression` is **skipped**, not passed.

## Remaining risk register

1. **Original endpoint versus approval event source:** We inspected direct Geoportal HTML/catalogue/facility features; no native dated approval list was confirmed in those surfaces. The rationale is recorded in [`source_selection_adr.md`](source_selection_adr.md). UVP-Verbund is the Geoportal-listed official **external** approval source, not the same host.
2. **Standalone power substation:** only synthetic test coverage; find a real dated approval or explicitly report this gap to IRIS.
3. **True raw-HTML parsing:** candidate should capture and test the actual DOM using `python -m iris_sig14.capture_live` and `pytest -q -rs`; do not publish full snapshots without content review.
4. **Publication dates and project points:** quality flags are expected for the three observed GreenSteel cases.
5. **IRIS production compatibility:** `sql/001_signal_ingest.sql` is a proposed staging contract and requires reconciliation with the real schema.
6. **Live operational resilience:** bounded HTTP retries are implemented, but site-side 429/500 scenarios and exhaustive pagination have not been demonstrated end-to-end.

## Reviewer checks

Use `sql/validation.sql` against the candidate's local demonstration database, including duplicate-key, missing-field and SRID checks. Re-run `iris-sig14 --live --max-pages 1 --delay 2` **only with explicit local DB targeting** if the reviewer wants to repeat the successful first-page ingestion. Never bypass a 403 or other access restriction.
