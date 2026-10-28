# ADR-001 — Why I selected UVP-Verbund for approval notices

**Status:** I accepted this approach for my technical demonstration, subject to IRIS confirming any intended native Geoportal feed.  
**Decision date:** 2026-10-28  
**Assigned source:** <https://geoportal.saarland.de>  
**Selected HTML source:** <https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=>  
**Integration pattern:** B — public HTML, without authentication or access-control bypass.

## My decision

I use **UVP-Verbund's public Saarland HTML listings (`provider=sl`)** and individual project-detail pages as the source of legal approval signals. I keep the originally assigned Geoportal as a separately inspected source of **facility inventory and potential location context**.

I do **not** turn existing industrial facilities, mapped substations or grid-capacity figures into approvals. Those sources describe infrastructure, not necessarily newly granted decisions.

This is my **documented alternative-source decision**, not a claim that Geoportal is broken or inaccessible. I recognize that IRIS may expect a specific native Geoportal notice dataset or selector.

## What I verified on the original Geoportal

1. I inspected <https://geoportal.saarland.de/apps/> using my `python -m iris_sig14.geoportal` reconnaissance command. I found **UVP-Verbund (extern)** as an application for environmental proceedings and **Kapazitäten der Umspannanlagen** for substation capacity. I saved the resulting [source-check report](../samples/geoportal_source_check.json).
2. I directly requested HTML OGC API Features pages for `Immissionsschutz:BImsch_Anlagen` and `Immissionsschutz:IED_Anlagen` from <https://geoportal.saarland.de/spatial-objects/237>. Both requests returned **HTTP 200**. Their displayed counts were **632** and **72** facilities, with fields including `NAME`, `INSPIRE_ID`, `NACE_CODE`, `ORT`, `PLZ`, `RWERT`, `HWERT` and `URL`.
3. I treated those records as **facility inventory**, not verified dated approvals. Some URLs lead to government environmental or inspection information, which does not necessarily demonstrate a new approval.
4. I found that the substation map describes physical infrastructure and nonbinding grid-capacity information. I did not infer a new statutory approval from a mapped asset.
5. I did not verify a native Geoportal HTML list containing project-level approval identifiers, approval dates and source links across the limited pages I inspected. **I have not exhaustively examined every dataset or linked application.**
6. I have not inferred EPSG:25832 from Geoportal's `RWERT`/`HWERT` values. I would verify the declared CRS and a reliable facility-to-project identity match before using those coordinates to enrich an approval.

## Why I selected the linked UVP-Verbund source

I inspected UVP-Verbund's public `freitextsuche` results and `trefferanzeige` detail pages. The Saarland filter supplies notice UUIDs, titles, source URLs, listing dates and (where stated) decision dates.

On 2026-10-28, I used my Python harvester on the first results page. I discovered **10 notices**, classified **3 relevant GreenSteel industrial approvals**, and filtered **7**. I inserted the three real records into a local PostgreSQL 16/PostGIS 3.4 database; a repeat run left **all 3 unchanged**. I preserved `publication_date=NULL` and `geom=NULL` where the public source did not support those fields.

I have **not** independently identified a standalone Saarland substation approval. My current substation case is a **synthetic fixture** intended to test the parsing and spatial paths, not evidence of a real permit.

## Alternatives I considered

| Option | My assessment |
|---|---|
| Parse Geoportal's applications catalogue as notices | I rejected this: it lists applications, not decision records |
| Insert Geoportal industrial/IED facilities as approvals | I rejected this: the inspected facility records did not establish individual dated decisions |
| Treat substation-capacity map entries as approved projects | I rejected this: existing assets/capacity do not prove approval |
| Follow Geoportal's official **UVP-Verbund (extern)** application | **I selected this:** it exposes relevant public HTML approval proceedings while retaining Pattern B |
| Enrich approval geometry from Geoportal facility data | I deferred this until the coordinate CRS and the facility/project match can be verified |

## Boundaries and trade-offs

- **Provenance:** I store `source_system=uvp_verbund_sl_html`, the actual UVP `docuuid` and the UVP detail URL. I do not present UVP records as direct Geoportal HTML notices.
- **Database:** I wrote a **local proposed staging schema**, not a verified IRIS production contract.
- **Access:** I use publicly accessible HTTPS HTML with bounded pages, timeouts, retries and delays. I do not bypass access controls.
- **Completeness:** I have not proven exhaustive Saarland approval coverage, PDF coverage or a real standalone substation approval.
- **Spatial data:** I do not fabricate a project point from a ministry address, city name or an unverified Geoportal facility match.

## When I would reconsider this decision

I would prioritize a native Geoportal source if IRIS provides a specific notice layer/selector or I verify a native collection containing the required dated approvals. I would also reassess the adapter if UVP-Verbund stops providing the necessary HTML records.
