"""Bounded regression for one-piece inner-end rail resection."""

import json
from pathlib import Path

from scripts.hardware_first_center_hybrid_rails import screen_rails

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_hybrid_rails.json"
)


def test_six_rails_keep_all_fixed_panel_receivers_and_clear_new_center_wood():
    result = screen_rails()
    assert result["status"] == "rail_geometry_feasible_only"
    assert result["protected_axis_count"] == 66
    assert result["changed_rail_count"] == 6
    assert all(len(names) == 2 for names in result["rail_assigned_screws"].values())
    assert result["protected_receiver_loss_mm3"] == {}
    assert result["protected_receiver_missing"] == {}
    assert result["rail_panel_clashes_mm3"] == {}
    assert result["rail_principal_clashes_mm3"] == {}
    assert result["rail_plate_clashes_mm3"] == {}
    assert all(result["rail_one_piece_cad_solid"].values())
    assert all(v >= 400 for v in result["rail_screw_receiver_min_mm3"].values())
    assert json.loads(REPORT.read_text()) == result
