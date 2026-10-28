# Design

## Decision 1: source discovery and access
I found that the supplied Geoportal serves geospatial metadata and facility data; I could not verify a native HTML 'Bekanntmachungen' notice stream on the pages inspected. I selected UVP-Verbund (`/freitextsuche`, `provider=sl`) as a documented lawful alternative, with `/trefferanzeige?docuuid=...` public project detail. I initially inspected 20 rendered results across two pages and later executed a first-page live extraction on my Mac (10 discovered, 3 eligible). I use URL patterns and contextual text rather than assuming permanent CSS selectors. I also captured genuine HTML locally and passed the real-DOM regression test; the published fixtures are reconstructed to avoid redistributing full pages.

## Decision 2: three distinct dates
I record list-page `21.02.2025` as `listing_date` (the source does not label it as date of publication). I record explicit detail-page `Datum der Entscheidung` as `decision_date`. I accept only a separately explicit `Veröffentlichungsdatum` or `Bekanntmachung vom` for `publication_date`; I prefer NULL to invented precision.

## Decision 3: classified signals and spatial integrity
I classify only steel-industry transformation or substation activity accompanied by approval language. I exclude unrelated infrastructure (including hydrogen pipelines). I preserve project-city text and accept coordinates only from project/site fields. A federal/ministry contact address is not a project location. I validate coordinates against conservative Saarland WGS84 bounds, then transform them with pyproj's `always_xy=True` EPSG:4326→25832. I retain original source coordinates in the payload when present.

## Decision 4: identity-preserving load
I use `source_system + docuuid` as a stable conflict key and SHA-256 to detect changed normalized payloads. `ON CONFLICT ... DO UPDATE ... WHERE content_hash IS DISTINCT` avoids duplicate rows and unnecessary mutation. I use a transaction per PostgreSQL batch. I also provide a SQLite demo sink for offline checks, while separately testing local PostgreSQL/PostGIS.

## Data flow
```text
UVP HTML search (provider=sl, bounded pages)
    -> detail pages (docuuid)
    -> RawNotice (source evidence and distinct dates)
    -> Saarland + industry/substation classifier
    -> strict project-coordinate validation / EPSG:25832
    -> Signal + quality_flags + content_hash
    -> JSONL + QA report
    -> optional PostgreSQL/PostGIS upsert
```

## Risks and trade-offs
- I recognize that portal markup/pagination may change; I have locally smoke-tested real HTML but future reviews may need renewed captures.
- I do not bypass restrictions if the source rate-limits or returns 403. XML API is *not* substituted because task pattern B explicitly requires HTML.
- I flag ambiguous source locations (GreenSteel EAF 'Dillingen' detail says 'Völklingen'). and preserve them for manual review.
- I do not know IRIS's production table contract; my local DDL is proposed, not authoritative, and I would adapt the loader before using a different schema.
- I do not claim full UVP/Saarland permit coverage or parse linked PDFs.

## Decision refinement: original Geoportal is reachable but its checked HTML datasets are inventories

I accessed the original `geoportal.saarland.de` OGC API Features HTML collections (BImSchG installations and IED installations). Those collections expose identifiable facilities and geographic attributes, but a notice-level approval date/decision is not established for those features. The Geoportal applications catalogue separately links an **external UVP-Verbund** approval application. I retain Pattern B by scraping the officially linked UVP HTML rather than treating facility inventory as a legal approval. I document the decision more comprehensively in `docs/source_selection_adr.md`. I would reconsider this decision if IRIS identifies a specific native Geoportal notice selector/collection.

I executed live UVP HTML ingestion and local PostgreSQL 16/PostGIS 3.4 loading. I also captured and regression-tested genuine HTML locally; I have not verified a real standalone substation approval.
