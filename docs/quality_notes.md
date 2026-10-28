# My quality and error report — IRIS-SIG-14

**Evidence date:** 2026-10-28. I separate actual live ingestion, reconstructed test fixtures, and synthetic data. I did **not** connect to IRIS's production database.

## Live ingestion and quality results

I retrieved one Saarland-filtered UVP-Verbund HTML results page (`provider=sl`), discovering **10 notices**. My classifier accepted **3 industrial approvals** and filtered **7**. I did not observe any fetch failures or malformed records in the captured quality report.

I loaded the three GreenSteel records into my local **PostgreSQL 16/PostGIS 3.4** `iris_live` database. The initial load wrote 3 records; the repeated load recorded **0 written / 3 unchanged**, as shown in [live_quality.json](../samples/live_quality.json).

| Quality issue | Count | How I handled it |
|---|---:|---|
| `publication_date_not_verified` | 3 | I preserved `NULL` rather than using a listing or decision date |
| `unresolved_project_point` | 3 | I preserved `NULL` geometry rather than inventing coordinates |
| `title_description_site_conflict` | 1 | I flagged the Dillingen/Völklingen discrepancy for manual review |
| `duplicates_in_batch` | 0 | No duplicate IDs occurred within the first-page live batch |

I validated an EPSG:25832 point using a **synthetic** substation fixture in local PostGIS; I do **not** treat it as a real approved project. My first-page live run is a smoke test, not a claim of complete Saarland coverage.

## Evidence available in the repository

- I committed the **actual pipeline-generated** [live JSONL](../samples/live_output.jsonl) and [live quality report](../samples/live_quality.json), not manually substituted examples.
- I retain [hand-transcribed verified examples](../samples/public_verified_examples.jsonl) separately; they are **not** a raw live-run capture.
- I label [fixture output](../samples/fixture_output.jsonl) and [fixture quality report](../samples/quality_report.json) as reconstructed/synthetic test evidence. This fixture set contains a synthetic substation.
- I recorded the detailed commands and results in [my execution evidence](local_execution_evidence.md).

I captured genuine public HTML on my Mac (one listing and three details) and reported **16 locally passing tests**. A limited scan found email/contact links in the downloaded detail pages. I therefore keep the complete HTML **local only** pending fuller privacy and redistribution review. A clean GitHub checkout does not contain those original HTML snapshots and skips that single real-DOM regression test; the published representative fixtures and other tests remain available.

## Risks and remaining work

1. **Source choice:** I investigated Geoportal's own industrial and substation data and selected the officially linked UVP-Verbund approval listing because facility inventory is not an approval event. I document the trade-off in [ADR-001](source_selection_adr.md).
2. **Standalone substation approval:** I have synthetic test coverage but have not verified an actual public substation approval.
3. **Missing source fields:** I leave unverified publication dates and project points `NULL`, with flags, instead of inventing metadata.
4. **Production compatibility:** My `sql/001_signal_ingest.sql` is a proposed local staging contract, not confirmed IRIS production DDL.
5. **Operational coverage:** I implemented bounded retries and pagination but have not proven exhaustive multi-page harvesting or tested every live HTTP 429/500 failure mode.
6. **Reproducibility scope:** I passed 15 tests with one expected skip in a fresh clone, and the published GitHub Actions workflow tests the package on Ubuntu. Those checks are not a substitute for production PostGIS integration.

## How I recommend validating the results

I include [`sql/validation.sql`](../sql/validation.sql) to inspect duplicates, missing metadata, geometry SRIDs and quality flags. I recommend running the offline fixture mode first. For a local database test, a reviewer should point `DATABASE_URL` at **their own** instance—not a shared or production database—and never bypass an HTTP access restriction.
