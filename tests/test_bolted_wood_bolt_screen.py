"""Retail bolt availability is not structural-joint approval."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_single_2x_bolt_screen_keeps_orientation_and_rating_separate() -> None:
    record = json.loads(
        (ROOT / "docs/bolted-candidate-prototypes/wood-1p5-bolt-screen.json").read_text()
    )
    assert record["receiver_actual_thickness_mm"] == 38.1
    assert record["preliminary_hex_bolt_diameter_mm"] == 9.525
    assert record["retail_examples"]["lowes"]["url"].startswith("https://www.lowes.com/")
    assert record["retail_examples"]["home_depot"]["url"].startswith("https://www.homedepot.com/")
    assert record["narrow_face_4d_screen"]["best_centered_edge_distance_mm"] == 19.05
    assert record["narrow_face_4d_screen"]["required_loaded_edge_distance_mm"] == 38.1
    assert record["narrow_face_4d_screen"]["passes"] is False
    assert record["bolt_purchase_length_selected"] is False
    assert record["a66_joint_capacity_established"] is False
    assert record["drilling_released"] is False
