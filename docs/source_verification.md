# My source verification and provenance — 2026-10-28

## Assigned Geoportal and chosen alternative

I started with the assigned <https://geoportal.saarland.de>. I verified that its public HTML exposes a GIS data/application catalogue, substation capacity information and industrial-facility features. I did **not** verify an individual dated approval-notice listing in the surfaces I examined. I do **not** claim the site is inaccessible or that no such source could exist elsewhere on the portal.

I selected the official, Geoportal-linked **UVP-Verbund (extern)** application as my **Pattern B HTML approval source**:

- [UVP-Verbund Saarland search](https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure=)
- [UVP-Verbund example second page](https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&page=2&provider=sl&toggle_procedure=)
- [Geoportal's applications catalogue](https://geoportal.saarland.de/apps/)
- [Geoportal substation capacity article](https://geoportal.saarland.de/article/Umspannanlagen_Kapazitaeten/)
- [LVGL Geoportal description](https://www.saarland.de/lvgl/DE/GeoportalSaarland/geoportalsaarland_node)

I initially compared public rendered search results, including 20 listings observed across two results pages for selected categories. I subsequently **ran my own live Python extraction of the first page** on my Mac: **10 discovered**, **3 eligible**, **7 filtered**. I do not claim that my local run harvested every page or every relevant Saarland permit.

## Public approvals I inspected

| UVP project UUID | Project | Listing date | Explicit decision date | Verified publication date |
|---|---|---|---|---|
| `d1d8a699-1303-46a7-bf89-c2f8a76dc25e` | GreenSteel DRI Dillingen | 2025-02-21 | 2025-01-29 | Not verified |
| `543d4e12-3a2d-4eb2-a8a5-b0135ca8717c` | GreenSteel EAF Dillingen | 2025-02-21 | 2025-01-29 | Not verified |
| `ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7` | GreenSteel EAF Völklingen GmbH | 2025-01-17 | 2024-12-10 | Not verified |

I retain the original identifiers and source URLs in [my live JSONL output](../samples/live_output.jsonl). I distinguish **listing dates** from **decision dates** and do not substitute either for missing publication dates.

### Location ambiguity

I flagged **GreenSteel EAF Dillingen** because its detail description refers to **Hüttenstandort Völklingen**. I preserve this conflict as `title_description_site_conflict` rather than assign an unsupported project location. I also avoid using the ministry's Saarbrücken contact address as a project coordinate.

## Live HTML and regression evidence

I retrieved actual public HTML from my Mac with `python -m iris_sig14.capture_live`. On 2026-10-28, I saved **one search page and three detail pages** and reported **16 passing local tests** with that real-DOM regression enabled.

I deliberately keep those downloaded HTML snapshots **outside public Git** pending complete privacy and redistribution review; my representative public `tests/fixtures/*.html` files are **reconstructed fixtures**, not a verbatim source capture. Clean CI therefore skips the optional genuine-DOM test.

I use only public HTTPS responses, with request limits and retries; I do not bypass access restrictions. I have not demonstrated complete coverage of all relevant decisions or every possible live rate-limiting scenario.

## Additional Geoportal verification

I ran `python -m iris_sig14.geoportal` against the live public applications catalogue, found **UVP-Verbund (extern)** and **Kapazitäten der Umspannanlagen**, and committed my [Geoportal source-check report](../samples/geoportal_source_check.json). This reconnaissance does **not** insert records into the approval staging table.

I also requested the original Geoportal's HTML OGC API Features collections `Immissionsschutz:BImsch_Anlagen` and `Immissionsschutz:IED_Anlagen`. Both returned HTTP 200 and displayed **632** and **72** facilities. These features contain facility identifiers and locations but were **not** demonstrated to be individual dated approvals. I have not treated their `RWERT`/`HWERT` fields as EPSG:25832 without verifying the CRS.

For the full alternatives analysis, risks and criteria for changing sources, I refer to [ADR-001](source_selection_adr.md).
