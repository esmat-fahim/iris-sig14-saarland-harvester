"""Bounded ETL orchestration with transparent record-level and fetch quality metrics."""
import json
import logging
import time
from collections import Counter
from pathlib import Path
from .models import RawNotice
from .normalize import normalize, classify, parse_date
from .source import BASE_URL, SEED_URLS, extract_detail, get_html, list_pages, make_session

log = logging.getLogger(__name__)


def run_pipeline(*, offline_dir: str | Path | None = None, source_url: str = BASE_URL,
                 seed_urls: bool = False, max_pages: int = 10, timeout: float = 15,
                 delay: float = 1.5) -> tuple[list, dict]:
    session = make_session()
    report = {"mode": "fixture" if offline_dir else "live", "source": source_url,
              "pages": 0, "discovered": 0, "eligible": 0, "filtered": 0,
              "fetch_failures": [], "malformed": [], "quality_flags": {}, "duplicates_in_batch": 0}
    if offline_dir:
        report["fixture_notice"] = ("Search result HTML is reconstructed from verified rendered public text; "
            "one substation case is wholly synthetic and is NOT an observed public permit.")
    discovered = {}
    if offline_dir:
        folder = Path(offline_dir)
        pages = [p.read_text(encoding="utf-8") for p in sorted(folder.glob("listing*.html"))]
        if not pages:
            raise FileNotFoundError(f"No listing*.html in {folder}")
    else:
        pages = None
    try:
        for url, rows in list_pages(session, source_url, max_pages, delay, timeout, offline_pages=pages):
            report["pages"] += 1
            for row in rows:
                if row.source_id in discovered:
                    report["duplicates_in_batch"] += 1
                else:
                    discovered[row.source_id] = row
        if seed_urls and not offline_dir:
            from urllib.parse import parse_qs, urlparse
            from .source import UUID_RE, is_allowed_url
            seeded = [
                ("GreenSteel DRI Dillingen", "Genehmigungsbescheid zur Errichtung und zum Betrieb einer Schachtofen-Direktreduktionsanlage am Standort Dillingen", "21.02.2025"),
                ("GreenSteel EAF Dillingen", "Genehmigungsbescheid zur Errichtung und zum Betrieb eines Elektrolichtbogenofens am Hüttenstandort Völklingen", "21.02.2025"),
                ("GreenSteel EAF Völklingen GmbH", "Genehmigungsbescheid zur Errichtung und zum Betrieb eines Elektrolichtbogenofens am Hüttenstandort Völklingen", "17.01.2025"),
            ]
            for url, (title, desc, listing_date) in zip(SEED_URLS, seeded):
                if not is_allowed_url(url, "/trefferanzeige"):
                    continue
                ident = parse_qs(urlparse(url).query).get("docuuid", [""])[0]
                if UUID_RE.fullmatch(ident) and ident not in discovered:
                    discovered[ident] = RawNotice(source_id=ident, title=title, description=desc,
                        listing_date=parse_date(listing_date), source_url=url, state="Saarland",
                        source_payload={"retrieval": "previously_verified_public_listing_seed", "observed_on": "2026-10-28"})
        report["discovered"] = len(discovered)
        if not discovered:
            report["source_warning"] = "empty_result_or_parser_selector_mismatch; verify source before considering a zero-signal run complete"
        output = []
        for raw in discovered.values():
            # Reject clearly irrelevant/non-Saarland listings before touching details.
            # This minimizes source requests; detail evidence can still refine accepted records.
            if raw.state != "Saarland" or classify(raw.title, raw.description) is None:
                report["filtered"] += 1
                continue
            try:
                if offline_dir:
                    path = Path(offline_dir) / f"detail_{raw.source_id}.html"
                    detail_html = path.read_text(encoding="utf-8") if path.exists() else None
                else:
                    if delay:
                        time.sleep(delay)
                    detail_html = get_html(session, raw.source_url, timeout)
                if detail_html:
                    extract_detail(detail_html, raw)
                else:
                    report["malformed"].append({"source_id": raw.source_id, "issue": "detail_html_missing"})
            except Exception as exc:
                report["fetch_failures"].append({"url": raw.source_url, "issue": f"{type(exc).__name__}: {exc}"})
                # Keep listing evidence; never invent dates/coordinates when details fail.
            try:
                s = normalize(raw)
                if s is None:
                    report["filtered"] += 1
                    continue
                output.append(s)
            except Exception as exc:
                report["malformed"].append({"source_id": raw.source_id, "issue": f"{type(exc).__name__}: {exc}"})
        report["eligible"] = len(output)
        report["quality_flags"] = dict(Counter(flag for s in output for flag in s.quality_flags))
        return output, report
    finally:
        session.close()


def write_artifacts(signals, report, output_path, report_path):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with Path(output_path).open("w", encoding="utf-8") as f:
        for s in signals:
            f.write(json.dumps(s.export(), ensure_ascii=False, sort_keys=True) + "\n")
    Path(report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
