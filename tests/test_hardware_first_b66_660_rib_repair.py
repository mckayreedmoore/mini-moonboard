"""Bounded B66 bore repair trial; geometry only."""

import json

from scripts.hardware_first_b66_660_rib_repair import OUTPUT, screen_repairs


def test_two_repairs_check_all_four_bores_and_fixed_receivers():
    report = screen_repairs()
    assert len(report["variants"]) == 2
    assert report["original_bore_missing_mm3"] > 0
    for trial in report["variants"]:
        assert len(trial["holes"]) == 4
        assert all(h["receiver_thickness_mm"] >= 76.2 for h in trial["holes"])
        assert all(h["receiver_continuous"] for h in trial["holes"])
        assert trial["fixed_screw_receiver_loss_mm3"] == {}
        assert trial["parent_header_bracket_count"] == 8
        assert trial["protected_panel_screw_count"] == 66
        assert len(trial["old_frame_axis_diagnostic"]) == 12
        assert all(not hits for hits in trial["old_frame_axis_diagnostic"].values())
        assert trial["all_four_full_bores_in_wood"] is True
        assert trial["nominal_local_checks_clear"] is True
        assert trial["repair_diagnostic"]["rail_seat_contact_fraction"] == 1.0
        assert trial["repair_diagnostic"]["rib_extension_to_parent_wood"] == {}
        assert trial["repair_diagnostic"]["rib_extension_to_parent_hardware"] == {}
        assert all(not clashes for clashes in trial["parent_neighbor_checks"].values())
        assert trial["protected_screw_hardware_clashes"] == {}
        assert trial["panel_hardware_clashes"] == {}
        assert trial["old_frame_axes_approved"] is False
        assert trial["normal_duration_rating_adopted"] is False
        assert trial["drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == report
