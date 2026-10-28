# Design

## Decision 1: source discovery and access
The supplied Geoportal is a geospatial metadata/service hub; an HTML 'Bekanntmachungen' selector at that host could not be verified. Prefer UVP-Verbund (`/freitextsuche`, `provider=sl`) as a documented lawful alternative, with `/trefferanzeige?docuuid=...` public project detail. The observed rendered search returned 20 results for relevant categories on 2026-10-28 and showed GreenSteel cases. This environment cannot capture origin HTML markup or connect directly to that domain over HTTP, so the parser deliberately uses semantic URL patterns and bounded ancestor text rather than claiming stable production CSS selectors. Representative *reconstructed* fixtures test the interface; a live smoke test remains necessary.

## Decision 2: three distinct dates
List-page `21.02.2025` is `listing_date` (the source does not label it as date of publication). Detail-page `Datum der Entscheidung` is `decision_date`. Only a separately explicit `Veröffentlichungsdatum` or `Bekanntmachung vom` is admissible for `publication_date`. Null is better than false precision.

## Decision 3: classified signals and spatial integrity
Only explicit steel-industry transformation or substation activity combined with approval language qualifies. Other infrastructure (including hydrogen pipelines) is not silently accepted. Project city text is preserved; coordinates are accepted only from site/project fields. A federal/ministry contact address is not a project location. Coordinates are validated against conservative Saarland WGS84 bounds, then transformed with pyproj's `always_xy=True` EPSG:4326→25832. Original coordinates are retained in payload when present.

## Decision 4: identity-preserving load
`source_system + docuuid` is a stable conflict key; a SHA-256 hash detects changed normalized payloads. `ON CONFLICT ... DO UPDATE ... WHERE content_hash IS DISTINCT` avoids duplicate rows and unnecessary mutation. PostgreSQL transaction is per batch. A SQLite-only demo sink validates identical semantics offline but does not substitute for actual PostgreSQL integration testing.

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
- Portal markup and pagination might change; URL/structure assumptions must be smoke-tested on actual raw HTML by a network-enabled reviewer.
- Public source may rate-limit/403; never evade restrictions. XML API is *not* substituted because task pattern B explicitly requires HTML.
- Public project descriptions contain ambiguous place names (GreenSteel EAF 'Dillingen' detail says 'Völklingen'). Preserve and flag for manual review.
- Exact IRIS production table schema unknown. Local DDL is proposed, not authoritative. The sink cannot be run against a different schema without adapting fields.
- UVP-Verbund does not cover all approvals, and this implementation does not parse attached PDFs.
