"""Regression capture tests. Live snapshot test activates only after real capture."""
from hashlib import sha256
import json
from pathlib import Path

import pytest

from iris_sig14 import capture_live
from iris_sig14.normalize import classify, normalize
from iris_sig14.source import extract_detail, extract_listing

F = Path(__file__).parent / "fixtures"
LIVE = F / "live_uvp"


def test_capture_downloads_genuine_returned_html_without_db(monkeypatch, tmp_path):
    listing = (F / "listing01.html").read_text(encoding="utf-8")
    first_id = "d1d8a699-1303-46a7-bf89-c2f8a76dc25e"
    detail = (F / f"detail_{first_id}.html").read_text(encoding="utf-8")
    calls = []

    class Session:
        def close(self):
            pass

    monkeypatch.setattr(capture_live, "make_session", Session)
    monkeypatch.setattr(capture_live.time, "sleep", lambda s: None)

    def fake_get_html(session, url, timeout):
        calls.append(url)
        return detail if "/trefferanzeige?" in url else listing

    monkeypatch.setattr(capture_live, "get_html", fake_get_html)
    result = capture_live.capture(tmp_path, max_details=1)
    assert result["discovered_listing_count"] == 4
    assert result["saved_details_count"] == 1
    assert len(calls) == 2
    assert (tmp_path / "listing01.html").read_text(encoding="utf-8") == listing
    assert (tmp_path / f"detail_{first_id}.html").read_text(encoding="utf-8") == detail
    assert result["files"][0]["sha256"] == sha256(listing.encode()).hexdigest()
    assert result["approval_coverage"]["standalone_substation_approval_verified"] is False


def test_capture_rejects_unparseable_html_without_writing(monkeypatch, tmp_path):
    class Session:
        def close(self):
            pass

    monkeypatch.setattr(capture_live, "make_session", Session)
    monkeypatch.setattr(capture_live, "get_html", lambda *_args, **_kwargs: "<html><body>Changed layout</body></html>")
    with pytest.raises(ValueError, match="No result records"):
        capture_live.capture(tmp_path)
    assert not (tmp_path / "manifest.json").exists()


def test_capture_rejects_bad_limits():
    with pytest.raises(ValueError, match="delay"):
        capture_live.capture("does_not_matter", delay=0)
    with pytest.raises(ValueError, match="max_details"):
        capture_live.capture("does_not_matter", max_details=0)


@pytest.mark.skipif(not (LIVE / "manifest.json").exists(),
                    reason="Genuine HTML not captured yet: run python -m iris_sig14.capture_live")
def test_real_live_html_selector_regression():
    """When captured by candidate on Mac, validate the actual saved DOM offline."""
    manifest = json.loads((LIVE / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["evidence_mode"] == "live_public_html_captured"
    assert manifest["saved_details_count"] >= 1
    assert manifest["source_page"].startswith("https://www.uvp-verbund.de/freitextsuche?")
    for item in manifest["files"]:
        name = item["filename"]
        assert name == Path(name).name  # Do not trust paths in metadata.
        assert sha256((LIVE / name).read_bytes()).hexdigest() == item["sha256"]
    listing = (LIVE / "listing01.html").read_text(encoding="utf-8")
    rows = extract_listing(listing, manifest["source_page"])
    assert len(rows) == manifest["discovered_listing_count"]
    eligible = {r.source_id: r for r in rows
                if r.state == "Saarland" and classify(r.title, r.description)}
    assert len(eligible) == manifest["eligible_listing_count"]
    for item in manifest["files"]:
        if item["source_id"]:
            assert item["source_id"] in eligible
            raw = extract_detail((LIVE / item["filename"]).read_text(encoding="utf-8"),
                                 eligible[item["source_id"]])
            signal = normalize(raw)
            assert signal is not None
            assert signal.source_id == item["source_id"]
            assert signal.source_url.startswith("https://www.uvp-verbund.de/trefferanzeige?")
