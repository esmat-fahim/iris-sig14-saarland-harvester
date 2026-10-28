# ADR-001 — Approval notice source selection for IRIS-SIG-14

**Status:** Accepted for the current demonstration, subject to IRIS reviewer confirmation of source expectations and the private production table contract.  
**Decision date:** 2026-10-28  
**Original assigned endpoint:** <https://geoportal.saarland.de>  
**Implemented approval-record source:** <https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=>  
**Pattern:** B (public HTML), no authentication or bypass.

## Decision

Use **UVP-Verbund's Saarland (`provider=sl`) public HTML search and per-project detail pages** as the primary source of *approval signals*, while retaining the assigned Saarland Geoportal as a **separate, verified source-discovery and optional facility-location context source**. Do **not** load the Geoportal's industrial-facility inventory or substation-capacity records into the approval staging table as if they were approvals.

The assignment explicitly allows a documented alternative when an advertised endpoint or HTML selector is not usable for the required notice stream. This is a **source-purpose mismatch**, not a claim that the original Geoportal is inaccessible or obsolete. The alternative remains a departure from the literal host in the brief, and IRIS may prefer another officially designated notice feed.

## Evidence gathered on the *original* domain

1. The public applications catalogue <https://geoportal.saarland.de/apps/> lists **UVP-Verbund (extern)** as an application for environmental proceedings, and **Kapazitäten der Umspannanlagen** for substation/capacity context. The candidate executed `python -m iris_sig14.geoportal` against live public HTML and saved `samples/geoportal_source_check.json`.
2. The candidate independently queried *native Geoportal HTML features* for the `Immissionsschutz:BImsch_Anlagen` and `Immissionsschutz:IED_Anlagen` collections via the OGC API Features page at <https://geoportal.saarland.de/spatial-objects/237>. Both returned HTTP 200 and HTML. The displayed lists showed **632 and 72 facilities, respectively**, at the time of inspection. Visible fields included `NAME`, `INSPIRE_ID`, `NACE_CODE`, `ORT`, `PLZ`, `RWERT`, `HWERT`, and `URL`. These are **facility records**, not necessarily dated individual approval decisions. The `URL` may link to an agency's environmental publication or inspection page, which itself must be evaluated before being treated as an approval.
3. The mapped substation information is about location/grid capacity, with nonbinding capacity statements. An existing or mapped facility must **not** be treated as a newly approved infrastructure project.
4. The limited inspected Geoportal surfaces did **not** demonstrate a native HTML notice list with project-specific approval identifiers, decision/publication dates, and source URLs meeting the requested event contract. This is **not an exhaustive search of every Geoportal layer, dataset, or linked application**. If a suitable native notice collection is established, reassess this decision.
5. The Geoportal `RWERT`/`HWERT` coordinates must not be assumed to be EPSG:25832. For example a displayed `RWERT` starting with `32` suggests a zone-prefixed coordinate representation; the **declared CRS must first be verified** before any coordinate transform or facility-to-approval match. No Geoportal point has been assigned to a UVP approval on the basis of city/name similarity alone.

## Evidence for the chosen official linked source

- UVP-Verbund's public `freitextsuche` HTML with `provider=sl` exposes project links containing a `docuuid`, titles, listing dates, and links to project detail pages. Source detail content supplies separate decision dates where explicitly identified.
- The candidate's local live run on 2026-10-28 returned **10 discovered / 3 eligible / 7 filtered** for the first search page. Three public GreenSteel project UUIDs were loaded into PostgreSQL 16/PostGIS 3.4; a repeated run left them unchanged. See `docs/local_execution_evidence.md`.
- No independently verified original *publication date* or exact project point was supplied for these three cases. Accordingly `publication_date` and `geom` remain `NULL`, with review flags.
- A **standalone power substation approval has not yet been independently confirmed**. A synthetic substation fixture tests the classifier and coordinate handling but is not a public approval signal.

## Alternatives considered

| Option | Assessment |
|---|---|
| Parse Geoportal's application catalogue as approvals | Rejected: it lists applications, not notice decisions |
| Parse Geoportal industrial/IED facilities directly into `signal_ingest` | Rejected: existing installations lack demonstrated event/approval identity and decision dates |
| Treat the Geoportal substation capacity map as approval notices | Rejected: facility/capacity data does not prove an approval |
| Follow Geoportal's **official external UVP-Verbund link** and parse its HTML | **Chosen**: supplies identifiable approval proceeding records and remains Pattern B |
| Link Geoportal facilities to approvals for geometry enrichment | Deferred until authoritative CRS and facility/site match are independently verified |

## Implementation boundaries and consequences

- **Provenance:** `source_system = uvp_verbund_sl_html`; `source_id` is the actual UVP `docuuid`; `source_url` points to the actual UVP detail page. Never label UVP content as directly scraped from Geoportal.
- **Schema:** the checked-in `iris_staging.signal_ingest` DDL is a **proposed local demonstration contract**, not confirmed IRIS production DDL.
- **Compliance:** HTTPS public HTML requests, bounded pages, timeout/retries and polite delay; no access-control bypass and no PDF download required for the current extraction.
- **Completeness:** neither first-page UVP results nor the selected HTML category filters establish complete coverage of Saarland's heavy-industry and standalone substation approvals.
- **Open questions:** Identify a confirmed standalone substation approval; validate authentic HTML regression snapshots; reconcile actual IRIS schema; evaluate native Geoportal sources if IRIS supplies a specific notice-layer ID.

## Revisit this decision when

IRIS supplies a precise Geoportal notice service/selector, a verified native Geoportal approval collection is found, or the chosen UVP source stops exposing the required dated approval events.
