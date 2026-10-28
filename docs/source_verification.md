# Source verification and provenance — 2026-10-28

## Assigned entrypoint
- https://geoportal.saarland.de — verified public GIS metadata, map layer and geodata-service portal (no identified dedicated HTML Bekanntmachungen record list).
- LVGL description: https://www.saarland.de/lvgl/DE/GeoportalSaarland/geoportalsaarland_node

## Selected Pattern-B alternative
- Public UVP-Verbund search: https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=
- Public second results page: https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&page=2&provider=sl&toggle_procedure=
- Source visually verified as HTML using public indexed/crawled text results, with 20 Saarland results across two pages for the specified category subset on 2026-10-28.

## Public records inspected

| UVP project UUID | Project title | Search result date | Explicit decision date | Confirmed publication date |
|---|---|---|---|---|
| d1d8a699-1303-46a7-bf89-c2f8a76dc25e | GreenSteel DRI Dillingen | 21.02.2025 | 29.01.2025 | Not identified |
| 543d4e12-3a2d-4eb2-a8a5-b0135ca8717c | GreenSteel EAF Dillingen | 21.02.2025 | 29.01.2025 | Not identified |
| ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7 | GreenSteel EAF Völklingen GmbH | 17.01.2025 | 10.12.2024 | Not identified |

Links:
- https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=d1d8a699-1303-46a7-bf89-c2f8a76dc25e&provider=sl&toggle_procedure=
- https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=543d4e12-3a2d-4eb2-a8a5-b0135ca8717c&provider=sl&toggle_procedure=
- https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7&provider=sl&toggle_procedure=

## Verified ambiguity
The UVP record titled **GreenSteel EAF Dillingen** describes an electric arc furnace at **Hüttenstandort Völklingen**. The source title and description conflict; the output includes `title_description_site_conflict`. Do not invent another project location. UVP detail pages prominently show a Saarbrücken ministry contact address, which is not automatically the project point.

## Accessibility and test qualification
The public source was readable through a web retrieval service, but direct container HTTP requests failed due disabled DNS/network. The candidate has since run a live, code-executed scrape on macOS (see `docs/local_execution_evidence.md`), but a checked-in raw-HTML DOM snapshot is NOT yet verified. Search-result HTML fixtures are structurally reconstructed from visible public content, not downloaded page-source captures. Additional synthetic substation test is plainly labelled. The UVP portal may also return 429 responses under repeated access; do not bypass. There is no evidence that published UVP coverage is exhaustive of all relevant industrial/substation permits.

## Original Geoportal HTML reconnaissance (2026-10-28)

- Public Geoportal applications listing: <https://geoportal.saarland.de/apps/>
- Listed application **UVP-Verbund (extern)** links to approval proceedings (Geoportal catalogue application invocation ID 4169). This explains why an official approval-record harvester follows the portal's external link.
- Listed application **Kapazitäten der Umspannanlagen** (invocation ID 7556), with direct Geoportal information page: <https://geoportal.saarland.de/article/Umspannanlagen_Kapazitaeten/>. The page describes mapped substations, operators and non-binding feed-in capacity metrics, **not new statutory approvals**.
- The catalogue alone does *not* establish a native dated HTML list of industrial/substation approval notices on `geoportal.saarland.de`. No direct approved-project signal is manufactured from map layers or application metadata.
- `python -m iris_sig14.geoportal` implements a direct **public-HTML source check** for these applications. Unit tests use **minimal reconstructed fixtures**, not authentic HTML downloads. The candidate ran the live check on macOS and observed both application links; see `docs/local_execution_evidence.md`. The reviewed source snapshot/report may be committed separately.
- Source reconnaissance is separate from the `uvp_verbund_sl_html` approval adapter and intentionally performs no staging writes.
