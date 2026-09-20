"""Bounded regression for thickening the six tongue-concept cut rails."""

import json
from pathlib import Path

from scripts.hardware_first_center_thick_rails import screen_thick_rails

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_thick_rails.json"
)


def test_thick_rail_feasibility_screen():
    result = screen_thick_rails()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert "rail collision with wood" in result["failures"]
    assert "rail collision with tongue-concept plate or bore" in result["failures"]
    assert "cut end face blocked" in result["failures"]
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["changed_rail_count"] == 6
    assert set(result["rail_receiver_thickness_mm"].values()) == {90.4748}
    for name, bounds in result["rail_bounds_mm"].items():
        assert bounds[1 if name.endswith("left") else 0] == (
            -120.0 if name.endswith("left") else 120.0
        )
    assert all(result["one_piece_cad_solid"].values())
    assert all(result["listed_4x6_dimension_fit"].values())
    assert set(result["rail_end_face_1mm_blockers_mm3"]) == {
        "base_rail_bottom_left",
        "base_rail_bottom_right",
    }
    assert result["rail_panel_clashes_mm3"] == {}
    assert result["rail_existing_frame_axis_clashes_mm3"] == {}
    assert result["rail_protected_screw_clashes_mm3"] == {}
    assert result["original_rail_wood_loss_mm3"] == {}
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert json.loads(REPORT.read_text()) == result
