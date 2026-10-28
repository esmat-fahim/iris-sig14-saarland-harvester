"""Data contracts: no dates or project coordinates are inferred from agency contacts."""
from dataclasses import asdict, dataclass, field
from datetime import date
from hashlib import sha256
import json


@dataclass
class RawNotice:
    source_id: str
    title: str
    source_url: str
    description: str = ""
    listing_date: date | None = None
    publication_date: date | None = None
    decision_date: date | None = None
    location_text: str | None = None
    state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source_crs: str | None = None
    easting: float | None = None
    northing: float | None = None
    source_payload: dict = field(default_factory=dict)


@dataclass
class Signal:
    source_system: str
    source_id: str
    signal_type: str
    title: str
    source_url: str
    publication_date: date | None
    listing_date: date | None
    decision_date: date | None
    location_text: str | None
    easting: float | None
    northing: float | None
    quality_flags: list[str]
    source_payload: dict
    content_hash: str = ""

    def export(self) -> dict:
        data = asdict(self)
        for key in ("publication_date", "listing_date", "decision_date"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return data

    def finalize(self) -> "Signal":
        data = self.export()
        data.pop("content_hash")
        self.content_hash = sha256(json.dumps(data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return self
