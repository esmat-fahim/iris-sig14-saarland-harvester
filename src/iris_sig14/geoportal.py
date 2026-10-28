"""Source reconnaissance on the *specified* Geoportal Saarland HTML catalogue.

This module does NOT treat map layers or substation capacity maps as approval
notices. The UVP application is listed as external in the Geoportal catalogue.
It is not an approval harvester and deliberately never writes to signal_ingest.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

CATALOGUE_URL = "https://geoportal.saarland.de/apps/"
SUBSTATION_ARTICLE_URL = "https://geoportal.saarland.de/article/Umspannanlagen_Kapazitaeten/"
PORTAL_HOST = "geoportal.saarland.de"
TARGET_APPLICATIONS = {
    "approval_publications": "UVP-Verbund (extern)",
    "substation_capacity_map": "Kapazitäten der Umspannanlagen",
}


def allowed_portal_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc == PORTAL_HOST


def portal_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset({"GET"}), respect_retry_after_header=True)
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "IRIS-SIG-14-source-recon/0.2 (public HTML only)",
                            "Accept": "text/html"})
    return session


def fetch_portal_html(session: requests.Session, url: str, timeout: float = 15) -> str:
    if not allowed_portal_url(url) or url not in (CATALOGUE_URL, SUBSTATION_ARTICLE_URL):
        raise ValueError("Refusing unapproved Geoportal URL")
    response = session.get(url, timeout=timeout, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect or response.is_permanent_redirect:
        raise ValueError("Geoportal redirect requires manual review")
    if "text/html" not in response.headers.get("Content-Type", "").lower():
        raise ValueError("Geoportal did not return HTML")
    if not response.content.strip():
        raise ValueError("Empty Geoportal HTML response")
    return response.text


def parse_geoportal_catalogue(html: str) -> dict:
    """Look for documented official applications, never infer approvals from a map."""
    soup = BeautifulSoup(html, "html.parser")
    links = {}
    for anchor in soup.select("a[href]"):
        label = " ".join(anchor.get_text(" ", strip=True).split())
        for kind, target in TARGET_APPLICATIONS.items():
            if re.sub(r"\s+", " ", label.casefold()) != re.sub(r"\s+", " ", target.casefold()):
                continue
            url = urljoin(CATALOGUE_URL, anchor["href"])
            if not allowed_portal_url(url):
                continue
            links[kind] = {"label": label, "catalogue_link": url, "catalogue": CATALOGUE_URL}
    return links


def inspect_substation_article(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    body = soup.get_text(" ", strip=True).casefold()
    return {
        "substation_topic_found": "umspannanlagen" in body,
        "capacity_context_found": "einspeisekapazitäten" in body or "trafoleistung" in body,
        "capacity_is_non_binding": "unverbindlich" in body,
        "approval_notice_observed": False,  # An infrastructure capacity description is NOT an approval.
    }


def assess_geoportal(catalogue_html: str, article_html: str | None = None) -> dict:
    found = parse_geoportal_catalogue(catalogue_html)
    result = {
        "source": CATALOGUE_URL,
        "mode": "geoportal_source_reconnaissance",
        "applications_found": found,
        "uvp_external_application_listed": "approval_publications" in found,
        "substation_capacity_application_listed": "substation_capacity_map" in found,
        "substation_article_url": SUBSTATION_ARTICLE_URL,
        "substation_article_observations": inspect_substation_article(article_html) if article_html is not None else None,
        "approval_records_extracted_from_geoportal": 0,
        "direct_html_approval_listing_verified": False,
        "mapping_decision": (
            "Do NOT load Geoportal map/application entries into iris_staging.signal_ingest. "
            "A mapped substation or capacity does not establish a new legal approval. "
            "UVP-Verbund is an external approval-publications application listed by Geoportal; "
            "retain separate source provenance when harvesting approvals there."
        ),
        "limitations": [
            "Only the Geoportal applications catalogue and named substation article are checked.",
            "No direct HTML approval-notice listing on geoportal.saarland.de has been verified.",
            "The portal map viewer and potential WMS/WFS layer content are not harvested here.",
        ],
    }
    if not found:
        result["warning"] = "No named applications found; check real HTML markup or website changes"
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Inspect the original Saarland Geoportal public HTML")
    parser.add_argument("--html-file", type=Path, help="Offline catalogue HTML fixture (no network)")
    parser.add_argument("--article-file", type=Path, help="Offline substation article fixture")
    parser.add_argument("--report", type=Path, default=Path("samples/geoportal_source_check.json"))
    parser.add_argument("--save-html", type=Path, help="Save fetched public catalogue HTML for local inspection")
    parser.add_argument("--timeout", type=float, default=15)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    try:
        if args.html_file:
            catalogue = args.html_file.read_text(encoding="utf-8")
            article = args.article_file.read_text(encoding="utf-8") if args.article_file else None
        else:
            with portal_session() as session:
                catalogue = fetch_portal_html(session, CATALOGUE_URL, args.timeout)
                try:
                    article = fetch_portal_html(session, SUBSTATION_ARTICLE_URL, args.timeout)
                except (requests.RequestException, ValueError) as exc:
                    article = None
                    article_issue = f"{type(exc).__name__}: {exc}"
                else:
                    article_issue = None
        result = assess_geoportal(catalogue, article)
        result["evidence_mode"] = "offline_html_fixture" if args.html_file else "live_public_html"
        if not args.html_file and article_issue:
            result["substation_article_fetch_issue"] = article_issue
        if args.save_html and not args.html_file:
            args.save_html.parent.mkdir(parents=True, exist_ok=True)
            args.save_html.write_text(catalogue, encoding="utf-8")
    except (OSError, requests.RequestException, ValueError) as exc:
        result = {"source": CATALOGUE_URL, "fatal_error": f"{type(exc).__name__}: {exc}"}
        code = 2
    else:
        code = 0 if result["uvp_external_application_listed"] and result["substation_capacity_application_listed"] else 2
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
