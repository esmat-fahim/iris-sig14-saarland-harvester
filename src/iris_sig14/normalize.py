"""Strict Saarland/domain gates, explicit provenance and safe point handling."""
from datetime import datetime
import math
import re
from pyproj import Transformer
from .models import RawNotice, Signal

STEEL = re.compile(r"\b(?:elektrolichtbogenofe\w*|schachtofen|direktreduktionsanlage|greensteel|stahlwerk|stahlindustrie|hüttenwerk|eaf|dri|hochofenum\w*|dekarbonisier\w*|transformationsprozess)\b", re.I)
SUBSTATION = re.compile(r"\b(?:umspannwerk\w*|umspannanlage\w*|transformatorenstation\w*|schaltanlage\w*|schaltwerk\w*|netzstation\w*)\b", re.I)
APPROVAL = re.compile(r"\b(?:genehmig\w*|bescheid\w*|planfeststellung\w*|zulassung\w*|bekanntmachung\w*|uvp|bimschg|antrag\w*)\b", re.I)
STOP = re.compile(r"\b(?:windpark\w*|windenergieanlage\w*|gasleitung\w*|wasserstoffleitung\w*|trassenverlauf\w*)\b", re.I)
CITY = re.compile(r"\b(Dillingen|Völklingen|Saarlouis|Saarbrücken|Neunkirchen|Homburg|St\.\s*Ingbert|Sankt Ingbert|Merzig|Bous|Wadern)\b", re.I)
WGS84_TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:25832", always_xy=True)
# Conservative state bounding box: only validation, never a location estimate.
SAARLAND_BOUNDS = (6.25, 49.05, 7.45, 49.68)


def parse_date(s: str | None):
    if not s:
        return None
    value = s.strip()
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
        return None
    try:
        return datetime.strptime(value, "%d.%m.%Y").date()
    except ValueError:
        return None


def classify(title: str, description: str) -> str | None:
    text = f"{title} {description}"
    if SUBSTATION.search(text) and APPROVAL.search(text):
        return "power_substation_approval"
    if STEEL.search(text) and APPROVAL.search(text) and not (STOP.search(title) and not STEEL.search(title)):
        return "heavy_industrial_restructuring_approval"
    return None


def location_from_text(title: str, description: str) -> str | None:
    # Never derive a project point from the authority's Saarbrücken mailing address.
    m = CITY.search(f"{title} {description}")
    return m.group(1) if m else None


def projected_point(raw: RawNotice) -> tuple[float | None, float | None, list[str]]:
    flags = []
    if raw.latitude is not None or raw.longitude is not None:
        if raw.latitude is None or raw.longitude is None:
            return None, None, ["coordinate_pair_incomplete"]
        try:
            lon, lat = float(raw.longitude), float(raw.latitude)
            if not math.isfinite(lon) or not math.isfinite(lat):
                raise ValueError("non-finite")
            xmin, ymin, xmax, ymax = SAARLAND_BOUNDS
            if not (xmin <= lon <= xmax and ymin <= lat <= ymax):
                raise ValueError("outside Saarland bbox")
            e, n = WGS84_TO_UTM.transform(lon, lat)
            return round(e, 3), round(n, 3), flags
        except (TypeError, ValueError, OverflowError):
            return None, None, ["invalid_coordinates"]
    if raw.easting is not None or raw.northing is not None:
        if raw.easting is None or raw.northing is None or raw.source_crs != "EPSG:25832":
            return None, None, ["invalid_or_unlabelled_projected_coordinates"]
        try:
            e, n = float(raw.easting), float(raw.northing)
            if not math.isfinite(e) or not math.isfinite(n):
                raise ValueError
            lon, lat = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True).transform(e, n)
            xmin, ymin, xmax, ymax = SAARLAND_BOUNDS
            if not (xmin <= lon <= xmax and ymin <= lat <= ymax):
                raise ValueError
            return round(e, 3), round(n, 3), flags
        except (ValueError, TypeError):
            return None, None, ["invalid_coordinates"]
    return None, None, ["unresolved_project_point"]


def normalize(raw: RawNotice) -> Signal | None:
    # This specific adapter is Saarland-only; missing state is not evidence of Saarland.
    if raw.state != "Saarland":
        return None
    signal_type = classify(raw.title, raw.description)
    if not signal_type:
        return None
    if not raw.source_id or not raw.title or not raw.source_url.startswith("https://www.uvp-verbund.de/trefferanzeige?"):
        return None
    easting, northing, flags = projected_point(raw)
    location = raw.location_text or location_from_text(raw.title, raw.description)
    if raw.publication_date is None:
        flags.append("publication_date_not_verified")
    if not location:
        flags.append("location_text_missing")
    if raw.title.lower().find("dillingen") >= 0 and re.search(r"hüttenstandort\s+völklingen", raw.description, re.I):
        flags.append("title_description_site_conflict")
    return Signal(
        source_system="uvp_verbund_sl_html", source_id=raw.source_id,
        signal_type=signal_type, title=raw.title.strip(), source_url=raw.source_url,
        publication_date=raw.publication_date, listing_date=raw.listing_date,
        decision_date=raw.decision_date, location_text=location,
        easting=easting, northing=northing, quality_flags=flags,
        source_payload=raw.source_payload,
    ).finalize()
