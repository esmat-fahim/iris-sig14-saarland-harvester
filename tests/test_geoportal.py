"""Geoportal site-provenance checks: no capacity maps misclassified as approvals."""
from pathlib import Path
import pytest
from iris_sig14.geoportal import (
    CATALOGUE_URL, SUBSTATION_ARTICLE_URL, allowed_portal_url,
    parse_geoportal_catalogue, inspect_substation_article, assess_geoportal,
    fetch_portal_html, main,
)

F = Path(__file__).parent / "fixtures"


def test_geoportal_catalogue_application_links():
    found = parse_geoportal_catalogue((F / "geoportal_catalogue_sample.html").read_text())
    assert set(found) == {"approval_publications", "substation_capacity_map"}
    assert found["approval_publications"]["catalogue_link"].endswith("id=4169")
    assert found["substation_capacity_map"]["catalogue_link"].endswith("id=7556")


def test_geoportal_source_does_not_fabricate_approvals():
    html = (F / "geoportal_catalogue_sample.html").read_text()
    article = (F / "geoportal_substation_article_sample.html").read_text()
    assessment = assess_geoportal(html, article)
    assert assessment["uvp_external_application_listed"]
    assert assessment["substation_capacity_application_listed"]
    assert assessment["approval_records_extracted_from_geoportal"] == 0
    assert assessment["direct_html_approval_listing_verified"] is False
    assert assessment["substation_article_observations"]["capacity_is_non_binding"]
    assert assessment["substation_article_observations"]["approval_notice_observed"] is False


def test_geoportal_url_guards_and_fetch_errors():
    assert allowed_portal_url(CATALOGUE_URL)
    assert not allowed_portal_url("https://geoportal.saarland.de.evil.org/apps/")
    class FakeResp:
        is_redirect = False
        is_permanent_redirect = False
        headers = {"Content-Type": "text/html"}
        content = b""
        def raise_for_status(self): pass
    class FakeSession:
        def get(self, *args, **kwargs): return FakeResp()
    with pytest.raises(ValueError, match="Empty"):
        fetch_portal_html(FakeSession(), CATALOGUE_URL)
    with pytest.raises(ValueError, match="unapproved"):
        fetch_portal_html(FakeSession(), "https://example.com")


def test_geoportal_offline_cli(tmp_path):
    report = tmp_path / "report.json"
    code = main(["--html-file", str(F / "geoportal_catalogue_sample.html"),
                 "--article-file", str(F / "geoportal_substation_article_sample.html"),
                 "--report", str(report)])
    assert code == 0
    assert report.exists()
