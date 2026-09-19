"""Representative-joint records stay diagnostic until G1 is resolved."""

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]


def report(name: str) -> dict:
    return json.loads((ROOT / "docs/bolted-candidate-prototypes" / name).read_text())


def test_three_representative_joints_name_real_current_stations() -> None:
    narrow = report("narrow-opposing.json")
    center = report("center-header.json")
    outer = report("outer-base.json")
    assert narrow["station"] == "clip_horizontal_bottom_left_2"
    assert center["stations"] == ["clip_split_base_center_left", "clip_split_base_center_right"]
    assert outer["stations"] == ["clip_angle_base_left", "clip_angle_base_right"]
    assert center["current_clip_y_mm"] == -124.9
    assert center["archived_clip_y_mm"] == -135.0


def test_representative_records_cannot_be_misread_as_acceptance() -> None:
    for name in ("narrow-opposing.json", "center-header.json", "outer-base.json"):
        item = report(name)
        assert item["status"] == "complete"
        assert item["engineering_disposition"] != "accepted"
        assert "geometry" in item["engineering_disposition"] or "unresolved" in item["engineering_disposition"]


def test_narrow_face_screen_exposes_the_negative_reserve() -> None:
    item = report("narrow-opposing.json")
    assert item["screen"]["four_d_edge_reserve_on_38_1_mm_face"] < 0
