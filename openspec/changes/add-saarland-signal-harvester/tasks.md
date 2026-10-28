# Implementation Tasks

## Source reconnaissance
- [x] I verified the supplied Geoportal is a GDI catalogue and not a confirmed HTML Bekanntmachungen listing.
- [x] I located and manually inspect public UVP-Verbund Saarland HTML search and 3 real GreenSteel approval detail pages.
- [x] I recorded distinct listing and decision dates, and explicitly mark publication dates unverified.
- [x] I implemented bounded live raw-HTML capture command, capture provenance manifest and conditional regression test.
- [x] I ran real public HTML capture on my Mac and locally pass the unskipped real-DOM regression test (I reported `16 passed`; snapshots are local-only).
- [x] I decided evidence packaging: retain full raw HTML locally after limited contact-link scan; exclude snapshots from public Git because no comprehensive content/redistribution audit was performed.

## Ingestion
- [x] I added config/CLI, HTTP host restrictions, retries, timeout and bounded pagination.
- [x] I extract listing UUID/title/URL/date and detail decision date.
- [x] Implement strict domain, state, date and coordinate transformation rules.
- [x] I track duplicates and reviewable quality flags.

## Persistence and testing
- [x] I provided local PostgreSQL 16 + PostGIS 3.4 DDL and parameterized upsert.
- [x] Provide SQLite demo and assert duplicate-free identical reruns.
- [x] Add mock/fixture tests for missing HTML, date provenance and invalid coordinates.
- [x] I generated representative public-source and fixture-only sample outputs and QA report.
- [x] I executed PostgreSQL 16/PostGIS 3.4 integration on a Mac: 3 real records loaded, repeated run unchanged, and EPSG:25832 synthetic point verified (see docs/local_execution_evidence.md).
- [ ] I still need to reconcile local table contract with real IRIS production staging schema when provided.

## Direct Geoportal source verification
- [x] I inspected Geoportal public HTML applications listing, identify the UVP-Verbund external application and the substation capacity map.
- [x] Add a no-database, safe direct-Geoportal HTML discovery command and reconstructed-fixture tests; prevent map inventory from being misclassified as approvals.
- [x] I executed discovery on live Geoportal HTML; report found the official UVP external app and the substation capacity app, no direct approval listing (see I logs).
- [x] I committed the Geoportal source-check report to the repository on 2026-10-28.
- [ ] I still need to confirm whether any native Geoportal page actually carries required dated approvals before designing a direct approval adapter.

## Scope completeness
- [ ] I still need to find and verify a real, standalone Saarland power-substation approval from an authoritative dated publication; current substation fixture is synthetic.
- [ ] I still need to validate OpenSpec against the installed CLI/version and record the outcome.

## Reviewer evidence and architecture decision
- [x] I documented why original Geoportal facility HTML cannot automatically be treated as approval notices; record the UVP-Verbund external-link decision and risks in ADR-001.
- [x] Record my direct HTTP 200 checks of Geoportal OGC API Features industrial-installation lists without inventing approval dates.
- [x] I updated quality handoff documentation to reflect my successful live HTML/PostGIS runs rather than obsolete inaccessible-runtime wording.
- [x] Add optional automated consistency validation for the two my generated live JSONL/report artifacts.
- [x] I reviewed and commit my generated `samples/live_output.jsonl` and `samples/live_quality.json` from the Mac (commit `1f04f6e`).
- [x] I captured actual UVP HTML on the Mac and pass non-skipped HTML regression test locally (I reported 16 passed).
- [x] Document limited HTML contact scan and the decision to exclude raw downloaded pages from public Git. Representative reconstructed fixtures remain public.
