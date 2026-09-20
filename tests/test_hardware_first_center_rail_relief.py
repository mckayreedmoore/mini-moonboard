"""Regression for the bounded bottom-rail relief trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_rail_relief import screen_rail_relief

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_rail_relief.json"
)


def test_bottom_rail_relief_preserves_fixed_geometry_and_reports_fit():
    result = screen_rail_relief()
    assert result["changed_rail_count"] == 2
    assert result["retained_parent_thick_service_rail_count"] == 4
    assert result["status"] == "geometry_only_unqualified"
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["fixed_panel_outline_count"] == 6
    assert result["original_bottom_rail_wood_loss_mm3"] == {}
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert result["protected_screw_receiver_missing"] == {}
    assert result["rail_other_wood_clashes_mm3"] == {}
    assert result["rail_panel_clashes_mm3"] == {}
    assert result["rail_upper_seat_clashes_mm3"] == {}
    assert result["rail_upper_header_bore_clashes_mm3"] == {}
    assert result["rail_protected_screw_added_occupancy_mm3"] == {}
    assert result["rail_existing_frame_axis_clashes_mm3"] == {}
    assert result["candidate_contact_band_full_section_loss_mm3"] == {
        "base_rail_bottom_left": 0.0,
        "base_rail_bottom_right": 0.0,
    }
    assert set(result["candidate_contact_band_full_section_thickness_mm"].values()) == {
        90.4748
    }
    assert all(result["one_piece_cad_solid"].values())
    assert json.loads(REPORT.read_text()) == result
