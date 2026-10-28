# Implementation Tasks

## Source reconnaissance
- [x] Verify supplied Geoportal is a GDI catalogue and not a confirmed HTML Bekanntmachungen listing.
- [x] Locate and manually inspect public UVP-Verbund Saarland HTML search and 3 real GreenSteel approval detail pages.
- [x] Record distinct listing and decision dates, and explicitly mark publication dates unverified.
- [ ] Capture and test actual raw HTML markup from a network-enabled local environment.

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
- [ ] Execute integration test against an actual PostgreSQL 16/PostGIS 3.4 instance (not installed in execution environment).
- [ ] Reconcile local table contract with real IRIS production staging schema when provided.

## Direct Geoportal source verification
- [x] Inspect Geoportal public HTML applications listing, identify the UVP-Verbund external application and the substation capacity map.
- [x] Add a no-database, safe direct-Geoportal HTML discovery command and reconstructed-fixture tests; prevent map inventory from being misclassified as approvals.
- [ ] Execute the discovery command locally against real Geoportal HTML and archive a reviewed DOM/quality report.
- [ ] Confirm whether any native Geoportal page actually carries required dated approvals before designing a direct approval adapter.
