"""Capture *actual* public UVP HTML for reproducible, offline parser regression tests.

This tool does not write to any database. Its outputs are observations from a
specific retrieval, not reconstructed illustrative HTML. Inspect snapshots for
unnecessary personal information/copyrighted assets before committing them.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from .normalize import classify
from .source import BASE_URL, extract_listing, get_html, make_session


def page_one_url(source_url: str = BASE_URL) -> str:
    """Match the live pipeline's page=1 request exactly."""
    p = urlparse(source_url)
    q = parse_qs(p.query, keep_blank_values=True)
    if q.get("provider") != ["sl"]:
        raise ValueError("Capture restricted to Saarland (provider=sl)")
    q["page"] = ["1"]
    return urlunparse(p._replace(query=urlencode(q, doseq=True)))


def capture(directory: str | Path, *, max_details: int = 3,
            delay: float = 2.0, timeout: float = 15.0) -> dict:
    """Download one real search page and up to N eligible details, or fail closed.

    Files are written only after all requested pages have been downloaded. No
    synthetic HTML, URLs, project identities, or publication dates are added.
    """
    if not 1 <= max_details <= 10:
        raise ValueError("max_details must be between 1 and 10")
    if delay < 1:
        raise ValueError("delay must be >= 1 second for polite access")
    if not 1 <= timeout <= 60:
        raise ValueError("timeout must be 1..60 seconds")
    directory = Path(directory)
    source_url = page_one_url()
    session = make_session()
    try:
        listing_html = get_html(session, source_url, timeout=timeout)
        records = extract_listing(listing_html, source_url)
        if not records:
            raise ValueError("No result records recognized in live HTML: check the source selectors")
        eligible = [r for r in records if r.state == "Saarland" and classify(r.title, r.description)]
        if not eligible:
            raise ValueError("No eligible Saarland records on captured listing; cannot certify target regression")

        details = {}
        for row in eligible[:max_details]:
            time.sleep(delay)
            details[row.source_id] = get_html(session, row.source_url, timeout=timeout)
    finally:
        session.close()

    listing_name = "listing01.html"
    metadata = {
        "evidence_mode": "live_public_html_captured",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_page": source_url,
        "discovered_listing_count": len(records),
        "eligible_listing_count": len(eligible),
        "saved_details_count": len(details),
        "approval_coverage": {
            "heavy_industrial_restructuring": any(
                classify(r.title, r.description) == "heavy_industrial_restructuring_approval" for r in eligible
            ),
            "standalone_substation_approval_verified": False,
            "note": "No claim of independently verified standalone substation approval; review the actual detail pages separately.",
        },
        "files": [],
    }
    payloads = [(listing_name, source_url, listing_html, None)]
    payloads.extend(
        (f"detail_{row.source_id}.html", row.source_url, details[row.source_id], row.source_id)
        for row in eligible[:max_details]
    )
    for name, url, html, source_id in payloads:
        b = html.encode("utf-8")
        metadata["files"].append({
            "filename": name, "url": url, "source_id": source_id,
            "sha256": sha256(b).hexdigest(), "bytes_utf8": len(b),
        })

    directory.mkdir(parents=True, exist_ok=True)
    for name, _, html, _ in payloads:
        (directory / name).write_text(html, encoding="utf-8")
    (directory / "manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Capture real Saarland UVP HTML for regression tests; no DB writes")
    parser.add_argument("--directory", default="tests/fixtures/live_uvp")
    parser.add_argument("--max-details", type=int, default=3)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    try:
        summary = capture(args.directory, max_details=args.max_details,
                          delay=args.delay, timeout=args.timeout)
    except Exception as e:
        parser.exit(2, f"Capture failed (no database writes): {type(e).__name__}: {e}\n")
    print(json.dumps({"captured_at_utc": summary["captured_at_utc"],
                      "discovered_listing_count": summary["discovered_listing_count"],
                      "eligible_listing_count": summary["eligible_listing_count"],
                      "saved_details_count": summary["saved_details_count"],
                      "directory": args.directory}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
