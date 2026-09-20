"""Regression for the conditional common-post, Y-face HL35 rejection."""

import json
from pathlib import Path

from scripts.hardware_first_center_yface import screen_yface

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "docs/bolted-candidate-prototypes/hardware_first_center_yface.json"


def test_centered_yface_hl35_clashes_with_fixed_kicker_panels():
    result = screen_yface()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["number_of_protected_axes_screened"] == 66
    assert result["all_66_panel_axes_unchanged"] is True
    assert result["front_face_and_kicker_back_y_mm"] == [-36.0, -36.0]
    assert result["original_post_material_missing_mm3"] == {"left": 0.0, "right": 0.0}
    assert result["other_wood_overlap"] == []
    assert len(result["common_post_kicker_receivers"]) == 4
    assert all(r["common_post_intersection_mm3"] > 400
               for r in result["common_post_kicker_receivers"])
    vertical = [r for r in result["panel_flange_clashes"]
                if r["flange"] == "front_vertical"]
    assert {r["panel"] for r in vertical} == {"kicker_left", "kicker_right"}
    assert all(r["overlap_mm3"] > 20_000 for r in vertical)
    assert result["protected_screw_flange_clashes"] == []
    assert json.loads(RESULT.read_text()) == result
