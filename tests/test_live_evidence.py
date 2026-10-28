"""Validation of candidate-generated live JSONL and report (no network, no DB)."""
from datetime import date
from pathlib import Path
import json
import re
from urllib.parse import parse_qs, urlparse

import pytest

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "samples/live_output.jsonl"
REPORT = ROOT / "samples/live_quality.json"
UUID_PATTERN = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$")
HASH_PATTERN = re.compile(r"[0-9a-f]{64}$")


def test_candidate_live_output_matches_report():
    """Activate once BOTH authentic candidate artifacts are available."""
    if not OUTPUT.exists() and not REPORT.exists():
        pytest.skip("Candidate's genuine live JSONL/report not yet committed")
    assert OUTPUT.exists() and REPORT.exists(), "Commit both genuine live evidence files together"
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in OUTPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert report["mode"] == "live"
    assert report["eligible"] == len(records)
    assert report["discovered"] >= len(records)
    assert report["filtered"] >= 0
    assert report["discovered"] >= report["eligible"] + report["filtered"]
    assert report.get("fetch_failures", []) == []
    assert report.get("malformed", []) == []
    assert urlparse(report["source"]).hostname == "www.uvp-verbund.de"
    assert parse_qs(urlparse(report["source"]).query).get("provider") == ["sl"]
    assert len(records) > 0, "This evidence test expects an actual nonempty candidate live run"

    seen = set()
    issues = {}
    for rec in records:
        assert rec["source_system"] == "uvp_verbund_sl_html"
        assert UUID_PATTERN.fullmatch(rec["source_id"])
        assert rec["source_id"] not in seen
        seen.add(rec["source_id"])
        assert rec["title"].strip()
        assert rec["signal_type"] in {
            "heavy_industrial_restructuring_approval", "power_substation_approval"
        }
        assert HASH_PATTERN.fullmatch(rec["content_hash"])
        assert rec.get("source_payload") and isinstance(rec["source_payload"], dict)
        link = urlparse(rec["source_url"])
        assert link.scheme == "https" and link.hostname == "www.uvp-verbund.de"
        assert link.path == "/trefferanzeige"
        assert parse_qs(link.query).get("docuuid") == [rec["source_id"]]
        for field in ("publication_date", "listing_date", "decision_date"):
            if rec.get(field) is not None:
                assert date.fromisoformat(rec[field])
        if rec.get("easting") is None or rec.get("northing") is None:
            assert rec.get("easting") is None and rec.get("northing") is None
            assert "unresolved_project_point" in rec["quality_flags"] or any(
                flag in rec["quality_flags"] for flag in (
                    "invalid_coordinates", "coordinate_pair_incomplete",
                    "invalid_or_unlabelled_projected_coordinates",
                )
            )
        for flag in rec["quality_flags"]:
            issues[flag] = issues.get(flag, 0) + 1
    assert report.get("quality_flags", {}) == issues
