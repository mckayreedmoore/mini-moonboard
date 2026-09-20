"""Regression for the single thick-header outer-post nominal trial."""

import json
from pathlib import Path

from scripts.hardware_first_center_thick_outer import screen_thick_outer

REPORT = (
    Path(__file__).resolve().parents[1]
    / "docs/bolted-candidate-prototypes/hardware_first_center_thick_outer.json"
)


def test_full_center_nominal_pose_preserves_frozen_axes_and_catalog_wood():
    result = screen_thick_outer()
    assert result["status"] == "rejected_installed_geometry_trial"
    assert result["failures"] == ["missing kicker seam support"]
    assert result["protected_axis_count"] == 66
    assert result["retained_frame_axis_count"] == 12
    assert result["changed_rail_count"] == 6
    assert len(result["bracketed_header_receiver_thickness_mm"]) == 6
    assert set(result["bracketed_header_receiver_thickness_mm"].values()) == {88.9}
    assert result["lower_post_receiver_thickness_mm"] >= 88.9
    assert result["minimum_upper_lower_header_bore_axis_spacing_x_mm"] > 14.2875
    assert result["shared_post_through_bolt_axes"] == 2
    assert result["post_bores_shared_between_lower_plates"] is True
    assert result["kicker_seam_supported"] is False
    assert result["kicker_seam_vertical_support_gap_mm"] == 4.55
    assert result["lower_seat_center_x_gap_mm"] == 19.05
    assert result["independent_bore_crossings_mm3"] == {}
    assert all(v == 0 for v in result["bore_missing_receiver_wood_mm3"].values())
    for field in (
        "plate_pair_clashes_mm3",
        "plate_wood_clashes_mm3",
        "plate_panel_clashes_mm3",
        "plate_adjacent_wood_clashes_mm3",
        "changed_wood_pair_clashes_mm3",
        "wood_panel_clashes_mm3",
        "wood_adjacent_clashes_mm3",
        "bore_other_wood_clashes_mm3",
        "bore_panel_clashes_mm3",
        "bore_adjacent_wood_clashes_mm3",
        "protected_screw_hardware_clashes_mm3",
        "protected_screw_receiver_loss_mm3",
        "protected_screw_receiver_missing",
        "existing_frame_axis_hardware_clashes_mm3",
        "existing_frame_axis_changed_wood_clashes_mm3",
    ):
        assert result[field] == {}, field
    assert len(result["kicker_center_receivers_mm3"]) == 4
    assert all(v > 0 for v in result["kicker_center_receivers_mm3"].values())
    assert all(result["one_piece_cad_solid"].values())
    assert all(result["ordinary_stock_example_dimension_fit"].values())
    assert len(result["original_rail_principal_clashes_mm3"]) == 6
    assert "unestablished" in result["reversible_F1_coverage"]
    assert "absent" in result["rail_to_center_attachment"]
    assert json.loads(REPORT.read_text()) == result
