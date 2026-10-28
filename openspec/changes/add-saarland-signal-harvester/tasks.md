# Implementation Tasks

## Source reconnaissance
- [x] Verify supplied Geoportal is a GDI catalogue and not a confirmed HTML Bekanntmachungen listing.
- [x] Locate and manually inspect public UVP-Verbund Saarland HTML search and 3 real GreenSteel approval detail pages.
- [x] Record distinct listing and decision dates, and explicitly mark publication dates unverified.
- [x] Implement bounded live raw-HTML capture command, capture provenance manifest and conditional regression test.
- [x] Run real public HTML capture on candidate Mac and locally pass the unskipped real-DOM regression test (candidate-reported `16 passed`; snapshots are local-only).
- [ ] Review captured HTML for personal data and redistribution conditions; decide whether to commit a permissible minimized fixture or retain full pages privately.

## Ingestion
- [x] Add config/CLI, HTTP host restrictions, retries, timeout and bounded pagination.
- [x] Extract listing UUID/title/URL/date and detail decision date.
- [x] Implement strict domain, state, date and coordinate transformation rules.
- [x] Track duplicates and reviewable quality flags.

## Persistence and testing
- [x] Provide local PostgreSQL 16 + PostGIS 3.4 DDL and parameterized upsert.
- [x] Provide SQLite demo and assert duplicate-free identical reruns.
- [x] Add mock/fixture tests for missing HTML, date provenance and invalid coordinates.
- [x] Generate representative public-source and fixture-only sample outputs and QA report.
- [x] Candidate executed PostgreSQL 16/PostGIS 3.4 integration on a Mac: 3 real records loaded, repeated run unchanged, and EPSG:25832 synthetic point verified (see docs/local_execution_evidence.md).
- [ ] Reconcile local table contract with real IRIS production staging schema when provided.

## Direct Geoportal source verification
- [x] Inspect Geoportal public HTML applications listing, identify the UVP-Verbund external application and the substation capacity map.
- [x] Add a no-database, safe direct-Geoportal HTML discovery command and reconstructed-fixture tests; prevent map inventory from being misclassified as approvals.
- [x] Candidate executed discovery on live Geoportal HTML; report found the official UVP external app and the substation capacity app, no direct approval listing (see candidate logs).
- [x] Candidate committed the Geoportal source-check report to the repository on 2026-10-28.
- [ ] Confirm whether any native Geoportal page actually carries required dated approvals before designing a direct approval adapter.

## Scope completeness
- [ ] Find and verify a real, standalone Saarland power-substation approval from an authoritative dated publication; current substation fixture is synthetic.
- [ ] Validate OpenSpec against the installed CLI/version and record the outcome.

## Reviewer evidence and architecture decision
- [x] Document why original Geoportal facility HTML cannot automatically be treated as approval notices; record the UVP-Verbund external-link decision and risks in ADR-001.
- [x] Record candidate's direct HTTP 200 checks of Geoportal OGC API Features industrial-installation lists without inventing approval dates.
- [x] Update quality handoff documentation to reflect candidate's successful live HTML/PostGIS runs rather than obsolete inaccessible-runtime wording.
- [x] Add optional automated consistency validation for the two candidate-generated live JSONL/report artifacts.
- [x] Review and commit candidate-generated `samples/live_output.jsonl` and `samples/live_quality.json` from the Mac (commit `1f04f6e`).
- [x] Capture actual UVP HTML on the Mac and pass non-skipped HTML regression test locally (candidate-reported 16 passed).
- [ ] Inspect captured HTML and document the redistribution decision; do not automatically commit full source pages.
