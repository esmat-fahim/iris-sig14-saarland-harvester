"""HTML Pattern B adapter for an observed public UVP-Verbund Saarland search page.

Source markup could not be captured verbatim from the public portal in this environment.
The parser uses semantic URL/heading/text heuristics, with fixture-driven tests.
"""
import logging
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .models import RawNotice
from .normalize import parse_date

log = logging.getLogger(__name__)
BASE_URL = "https://www.uvp-verbund.de/freitextsuche?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&provider=sl&toggle_procedure="
DOMAIN = "www.uvp-verbund.de"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DATE_RE = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")
PUBLISHED_RE = re.compile(r"(?:veröffentlicht\s+am|veröffentlichungsdatum|bekanntmachung\s+vom)\s*:?\s*(\d{2}\.\d{2}\.\d{4})", re.I)
DECISION_RE = re.compile(r"datum\s+der\s+entscheidung\s*:?\s*(\d{2}\.\d{2}\.\d{4})", re.I)
SEED_URLS = [
 "https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=d1d8a699-1303-46a7-bf89-c2f8a76dc25e&provider=sl&toggle_procedure=",
 "https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=543d4e12-3a2d-4eb2-a8a5-b0135ca8717c&provider=sl&toggle_procedure=",
 "https://www.uvp-verbund.de/trefferanzeige?category=chemie%3Banlagen%3Bbauvorhaben%3Benergie%3Bverarbeitung&docuuid=ef8e5ff8-ecc7-4bff-86d6-fa71e80e3db7&provider=sl&toggle_procedure=",
]


def is_allowed_url(url: str, path: str | None = None) -> bool:
    p = urlparse(url)
    return p.scheme == "https" and p.netloc == DOMAIN and (path is None or p.path == path)


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=frozenset(["GET"]), respect_retry_after_header=True)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "IRIS-SIG-14 public-research-harvester/0.1 (+respectful bounded retrieval)", "Accept": "text/html"})
    return s


def get_html(session: requests.Session, url: str, timeout: float = 15) -> str:
    if not is_allowed_url(url):
        raise ValueError("Refusing URL outside approved public UVP host")
    r = session.get(url, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    if not is_allowed_url(r.url):
        raise ValueError("Redirected outside approved public UVP host")
    if "text/html" not in r.headers.get("Content-Type", "").lower():
        raise ValueError("Expected HTML response; refusing non-HTML")
    if not r.content.strip():
        raise ValueError("Empty HTML response")
    return r.text


def _record_node(anchor):
    # Find *local* result card, never a containing list of multiple projects.
    for node in list(anchor.parents)[:9]:
        if node.name in ("html", "body"):
            break
        text = node.get_text(" ", strip=True)
        if DATE_RE.search(text) and "Verfahrensführende Stelle" in text and len(text) <= 4500:
            if len(node.select('a[href*="trefferanzeige"]')) == 1:
                return node
    return None


def _record_area(anchor):
    # Prefer the smallest ancestor; fallback is bounded by the next project link.
    node = _record_node(anchor)
    if node:
        return node.get_text(" ", strip=True)
    # Conservative fallback: only text after link and before next result link.
    tokens = []
    for item in anchor.next_elements:
        if getattr(item, "name", None) == "a" and "trefferanzeige" in item.get("href", ""):
            break
        if isinstance(item, str):
            tokens.append(item.strip())
        if len(" ".join(tokens)) > 3000:
            break
    return " ".join(x for x in tokens if x)


def extract_listing(html: str, base_url: str) -> list[RawNotice]:
    if not is_allowed_url(base_url, "/freitextsuche"):
        raise ValueError("Expected UVP search page")
    soup = BeautifulSoup(html, "html.parser")
    out = []
    seen = set()
    for a in soup.select('a[href*="trefferanzeige"]'):
        href = urljoin(base_url, a.get("href", ""))
        if not is_allowed_url(href, "/trefferanzeige"):
            continue
        qs = parse_qs(urlparse(href).query)
        docuuid = qs.get("docuuid", [""])[0]
        if not UUID_RE.fullmatch(docuuid) or docuuid.lower() in seen:
            continue
        title = a.get_text(" ", strip=True)
        if not title:
            continue
        area = _record_area(a)
        # State check in local result context, not merely the page's global filter panel.
        # Search results often show a Saarland flag img with an alt attribute.
        local_node = _record_node(a) or a.parent
        imgs = local_node.find_all("img")
        stated = [x.get("alt", "").strip() for x in imgs if x.get("alt")]
        if stated:
            # Location marker wins; a state-name in a title is NOT state evidence.
            state = "Saarland" if "Saarland" in stated else None
        else:
            state = "Saarland" if re.search(r"Verfahrensführende Stelle.*?\b(?:des Saarlandes|Saarland)\b", area, re.I) else None
        # Date in result card is listing/update date; not confirmed published date.
        # Use first date near title, not later decision dates in the text.
        listing_match = DATE_RE.search(area)
        listing = parse_date(listing_match.group()) if listing_match else None
        published = PUBLISHED_RE.search(area)
        description = area.replace(title, "", 1).strip()[:2800]
        seen.add(docuuid.lower())
        out.append(RawNotice(
            source_id=docuuid.lower(), title=title, source_url=href,
            description=description, listing_date=listing,
            publication_date=parse_date(published.group(1)) if published else None,
            state=state, source_payload={"listing_excerpt": area[:3500], "retrieval": "HTML_search"}
        ))
    return out


def extract_detail(html: str, notice: RawNotice) -> RawNotice:
    soup = BeautifulSoup(html, "html.parser")
    # Search-result project title is more precise than generic detail-page h1.
    body = soup.get_text(" ", strip=True)
    m = DECISION_RE.search(body)
    if m:
        notice.decision_date = parse_date(m.group(1))
    pub = PUBLISHED_RE.search(body)
    if pub:
        notice.publication_date = parse_date(pub.group(1))
    heading = soup.find(string=re.compile("Allgemeine Vorhabenbeschreibung", re.I))
    if heading:
        header = heading.find_parent(re.compile("h[1-6]"))
        if header:
            pieces = []
            for sib in header.next_siblings:
                if getattr(sib, "name", None) and re.fullmatch("h[1-6]", sib.name):
                    break
                if getattr(sib, "get_text", None):
                    pieces.append(sib.get_text(" ", strip=True))
            desc = " ".join(pieces).strip()
            if desc:
                notice.description = desc[:3000]
    # The 'Ansprechpartner' address is a ministry address, not the project location.
    notice.source_payload["detail_confirmed"] = True
    notice.source_payload["detail_excerpt"] = body[:3500]
    # Accept only data explicitly labelled project/site coordinates.
    meta = soup.select_one('meta[name="project:coordinates"]')
    if meta:
        try:
            lat, lon = meta.get("content", "").split(",")
            notice.latitude, notice.longitude = float(lat), float(lon)
        except (TypeError, ValueError):
            notice.source_payload["coordinate_parse_error"] = True
    return notice


def list_pages(session, source_url: str = BASE_URL, max_pages: int = 10, delay: float = 1.5,
               timeout: float = 15, offline_pages: list[str] | None = None):
    """Yield (page_url, listing notices), fail loudly on live source errors."""
    if not is_allowed_url(source_url, "/freitextsuche") or parse_qs(urlparse(source_url).query).get("provider") != ["sl"]:
        raise ValueError("Search must be UVP provider=sl")
    if not 1 <= max_pages <= 100:
        raise ValueError("max_pages outside safe 1..100")
    seen_ids = set()
    for page in range(1, max_pages + 1):
        p = urlparse(source_url)
        q = parse_qs(p.query, keep_blank_values=True)
        q["page"] = [str(page)]
        page_url = urlunparse(p._replace(query=urlencode(q, doseq=True)))
        if offline_pages is not None:
            if page > len(offline_pages):
                return
            html = offline_pages[page - 1]
        else:
            if page > 1 and delay:
                time.sleep(delay)
            html = get_html(session, page_url, timeout)
        rows = extract_listing(html, page_url)
        if not rows:
            if page == 1:
                log.warning("First search page returned no recognized project records")
            return
        ids = {row.source_id for row in rows}
        if ids.issubset(seen_ids):
            return
        seen_ids |= ids
        yield page_url, rows
        # Pagination signals can be generic; stopping on no new IDs is safe.
