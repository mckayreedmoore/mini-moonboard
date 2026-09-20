"""Regression for the single 15-mm-forward hybrid center trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_hybrid_forward import screen_forward

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_hybrid_forward.json"
)


def test_forward_header_rejected_for_kicker_intersection():
    result = screen_forward()
    assert result["status"] == "rejected_nominal_geometry_trial"
    assert result["upper_shift_mm"] == 15.0
    assert result["header_forward_extension_mm"] == 2.3
    assert set(result["header_extension_panel_clashes_mm3"]) == {
        "kicker_left",
        "kicker_right",
    }
    assert all(v > 0 for v in result["header_extension_panel_clashes_mm3"].values())
    assert result["protected_axis_count"] == 66
    assert result["changed_rail_count"] == 6
    assert len(result["changed_wood_bounds_mm"]) == 10
    assert len(result["plate_bounds_mm"]) == 6
    assert result["changed_wood_adjacent_clashes_mm3"] == {}
    assert result["plate_panel_clashes_mm3"] == {}
    assert result["plate_adjacent_clashes_mm3"] == {}
    assert result["plate_changed_wood_clashes_mm3"] == {}
    assert result["protected_screw_hardware_clashes_mm3"] == {}
    assert result["protected_receiver_loss_mm3"] == {}
    assert result["protected_receiver_missing"] == {}
    assert result["existing_frame_axis_hardware_clashes_mm3"] == {}
    assert all(result["one_piece_cad_solid"].values())
    assert all(v == 0 for v in result["bore_missing_receiver_wood_mm3"].values())
    assert json.loads(REPORT.read_text()) == result
