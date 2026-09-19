"""Guard the bounded, non-qualifying connector research outputs."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_ml24z_screen_does_not_transfer_sds_rating() -> None:
    report = read("docs/bolted-candidate-prototypes/ml24z-through-bolt.json")
    assert report["engineering_disposition"] == "unresolved"
    assert report["nominal_screen"]["nominal_shaft_fits"] is True
    assert report["nominal_screen"]["ordinary_bolt_hole_clearance_match"] is False
    assert any("SDS" in item or "stiffness" in item for item in report["required_unresolved_checks"])


def test_alternative_search_is_bounded_and_preserves_stock() -> None:
    report = read("docs/bolted-candidate-prototypes/factory-bolted-alternatives.json")
    assert report["search_budget"]["distinct_families_screened"] <= 3
    assert report["search_budget"]["catalog_exhaustion_claimed"] is False
    assert len(report["alternatives"]) == 3
    assert all(item["disposition"] != "accepted" for item in report["alternatives"])
