"""One bounded HL33 installed-geometry regression."""

import json
from pathlib import Path

from scripts.hardware_first_center_hl33 import screen_hl33

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes"
    / "hardware_first_center_hl33.json"
)


def test_hl33_trial_reports_every_protected_axis_and_installed_clash():
    result = screen_hl33()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["protected_axis_count"] == 66
    assert result["existing_frame_axis_count"] == 12
    assert result["catalog_mm"]["bend_length"] == 63.5
    assert result["catalog_mm"]["leg_reach"] == 82.55
    assert all(result["one_piece_cad_solid"].values())
    assert all(result["ordinary_stock_example_dimension_fit"].values())
    assert result["kicker_seam_supported"] is True
    assert result["protected_screw_receiver_loss_mm3"] == {}
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert result["bore_missing_receiver_wood_mm3"] == {}
    assert result["independent_bore_crossings_mm3"] == {}
    assert result["bore_panel_clashes_mm3"] == {}
    assert result["bore_other_new_wood_clashes_mm3"] == {}
    assert set(result["bore_adjacent_wood_clashes_mm3"]) == {
        "upper_left_principal",
        "upper_right_principal",
    }
    assert result["plate_pair_clashes_mm3"] == {}
    assert result["protected_screw_plate_clashes_mm3"] == {}
    assert result["protected_screw_bore_clashes_mm3"] == {}
    assert result["new_wood_adjacent_clashes_mm3"]
    assert "new wood collision" in result["failures"]
    assert "bore collision with other material" in result["failures"]
    assert json.loads(REPORT.read_text()) == result
