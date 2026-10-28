from datetime import date
import json
from pathlib import Path
import pytest
from iris_sig14.models import RawNotice
from iris_sig14.normalize import classify, normalize, parse_date, projected_point
from iris_sig14.pipeline import run_pipeline
from iris_sig14.source import BASE_URL, extract_listing, extract_detail, get_html, list_pages
from iris_sig14.store import SQLiteDemoSink, POSTGRES_UPSERT

F = Path(__file__).parent / "fixtures"


def test_parser_listings_and_pagination():
    rows = extract_listing((F / "listing01.html").read_text(), BASE_URL)
    assert len(rows) == 4
    assert rows[0].source_id == "d1d8a699-1303-46a7-bf89-c2f8a76dc25e"
    assert rows[0].listing_date == date(2025, 2, 21)
    assert rows[0].publication_date is None
    assert rows[0].state == "Saarland"
    pages = list(list_pages(None, BASE_URL, offline_pages=[p.read_text() for p in sorted(F.glob("listing*.html"))]))
    assert len(pages) == 2


def test_detail_provenance_and_no_assumed_publication_date():
    raw = extract_listing((F / "listing01.html").read_text(), BASE_URL)[0]
    raw = extract_detail((F / f"detail_{raw.source_id}.html").read_text(), raw)
    assert raw.decision_date == date(2025, 1, 29)
    assert raw.publication_date is None
    assert raw.latitude is None  # Contact ministry address must not be geocoded.


def test_filtering_and_spatial_validation():
    assert classify("Windpark Saarland", "Genehmigung Windenergieanlage") is None
    assert classify("Umspannwerk Dillingen", "Genehmigungsbescheid") == "power_substation_approval"
    assert classify("GreenSteel EAF Dillingen", "Genehmigungsbescheid") == "heavy_industrial_restructuring_approval"
    assert parse_date("31.02.2026") is None
    assert normalize(RawNotice("x", "Genehmigung Umspannwerk", "https://www.uvp-verbund.de/trefferanzeige?docuuid=x",state="Rheinland-Pfalz")) is None
    p = RawNotice("x", "", "", latitude=49.32, longitude=7.0)
    e, n, warnings = projected_point(p)
    assert 300000 < e < 450000 and 5400000 < n < 5600000 and warnings == []
    assert projected_point(RawNotice("x", "", "", latitude=91, longitude=7))[2] == ["invalid_coordinates"]
    assert projected_point(RawNotice("x", "", "", latitude=float("nan"), longitude=7))[2] == ["invalid_coordinates"]
    assert projected_point(RawNotice("x", "", "", easting=400000, northing=5460000,source_crs="EPSG:4326"))[2] == ["invalid_or_unlabelled_projected_coordinates"]


def test_full_fixture_pipeline_and_idempotent_rerun(tmp_path):
    signals, report = run_pipeline(offline_dir=F)
    assert report["pages"] == 2
    assert report["eligible"] == 4
    assert report["filtered"] == 2  # wind turbine and wrong German state
    assert report["duplicates_in_batch"] == 1
    assert report["quality_flags"]["publication_date_not_verified"] == 4
    s = {r.source_id:r for r in signals}
    assert s["00000000-0000-4000-8000-000000000002"].easting is not None
    assert s["d1d8a699-1303-46a7-bf89-c2f8a76dc25e"].easting is None
    assert "title_description_site_conflict" in s["543d4e12-3a2d-4eb2-a8a5-b0135ca8717c"].quality_flags
    db = SQLiteDemoSink(tmp_path/"demo.db")
    try:
        assert db.load(signals) == {"written": 4, "unchanged": 0}
        assert db.load(signals) == {"written": 0, "unchanged": 4}
        assert db.count() == 4
        s["00000000-0000-4000-8000-000000000002"].title = "Modified fixture"
        s["00000000-0000-4000-8000-000000000002"].finalize()
        assert db.load(signals) == {"written": 1, "unchanged": 3}
        assert db.count() == 4
    finally:
        db.close()


def test_network_errors_rejected(monkeypatch):
    class FakeResp:
        url = "https://www.uvp-verbund.de/freitextsuche"
        headers = {"Content-Type": "text/html"}
        content = b""
        text = ""
        def raise_for_status(self): pass
    class FakeSession:
        def get(self, *args, **kwargs): return FakeResp()
    with pytest.raises(ValueError, match="Empty HTML"):
        get_html(FakeSession(), BASE_URL)
    with pytest.raises(ValueError, match="Refusing URL"):
        get_html(FakeSession(), "https://example.org")
    with pytest.raises(ValueError, match="provider=sl"):
        list(list_pages(None, "https://www.uvp-verbund.de/freitextsuche?provider=by", offline_pages=["<html/>"]))
    assert "ON CONFLICT (source_system, source_id)" in POSTGRES_UPSERT
    assert "IS DISTINCT FROM" in POSTGRES_UPSERT


def test_malformed_empty_listing():
    assert extract_listing("", BASE_URL) == []
    assert list(list_pages(None, BASE_URL, offline_pages=["<html><body>Nothing</body></html>"])) == []
