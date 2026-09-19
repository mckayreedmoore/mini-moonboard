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
        assert item["status"] == "incomplete_representative_prototype"
        assert item["engineering_disposition"] != "accepted"
        assert "geometry" in item["engineering_disposition"] or "unresolved" in item["engineering_disposition"]


def test_narrow_face_screen_exposes_the_negative_reserve() -> None:
    item = report("narrow-opposing.json")
    assert item["screen"]["four_d_edge_reserve_on_38_1_mm_face"] < 0


def test_a66_face_options_are_station_specific_and_not_selected() -> None:
    narrow = report("narrow-opposing.json")["a66_face_option"]
    center = report("center-header.json")["a66_face_option"]
    outer = report("outer-base.json")["a66_face_option"]
    assert narrow["narrow_face_four_d_reserve_mm"] == -19.05
    assert all(option["wide_face_four_d_best_case_reserve_mm"] == 31.75
               for option in (narrow, center, outer))
    assert all(option["status"] == "unverified_geometry_only"
               for option in (narrow, center, outer))
    assert all(option["factory_hole_coordinates_known"] is False
               for option in (narrow, center, outer))
    assert center["neighbor_center_clip_stations"] >= 6
    assert outer["retained_front_runner_bolts_nearby"] == 2
