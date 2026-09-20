"""B66/UB66 component screen is geometry evidence, never a rating."""

import json

from scripts.hardware_first_b66_660_component_route import OUTPUT, screen_b66_route


def test_b66_route_reports_factory_requirements_and_protected_geometry():
    report = screen_b66_route()
    assert report["retail_model"] == "UB66"
    assert report["manufacturer_model"] == "B66"
    assert report["rib_spacing_mm"] == 660
    assert report["station"] == "bottom right only"
    assert report["protected_panel_screw_count"] == 66
    assert report["fixed_screw_receiver_loss_mm3"] == {}
    assert report["factory_hole_count"] == 4
    assert report["factory_free_end_offsets_mm"] == [25.4, 126.744]
    assert report["esr_minimum_wood_thickness_mm"] == 76.2
    assert (
        report["esr_bolt_specification"]
        == "3/8-in ASTM A307 Grade A; Fy,b >= 45,000 psi"
    )
    assert (
        report["esr_steel_specification"]
        == "12-ga ASTM A653 SS Grade 40 G90; base t >= 0.099 in"
    )
    assert all(h["receiver_thickness_mm"] >= 76.2 for h in report["holes"])
    assert all(h["receiver_continuous"] for h in report["holes"])
    assert all(h["factory_hole_clear"] for h in report["holes"])
    assert all(h["bolt_wood_overlap_mm3"] > 0 for h in report["holes"])
    assert report["status"] == "nominal_geometry_conflict"
    missing = {h["id"]: h["bore_missing_receiver_mm3"] for h in report["holes"]}
    assert missing["rail_vertical_1"] == 1869.507
    assert all(v == 0 for k, v in missing.items() if k != "rail_vertical_1")
    assert report["protected_screw_hardware_clashes"] == {}
    assert report["panel_hardware_clashes"] == {}
    assert report["other_rail_ends_open"] == 5
    assert report["existing_frame_bolt_axes_resolved"] is False
    assert report["normal_duration_rating_adopted"] is False
    assert report["connected_architecture_verdict"] is False
    assert report["drilling_released"] is False
    assert json.loads(OUTPUT.read_text()) == report


def test_parent_and_access_are_explicitly_screened_not_silently_accepted():
    report = screen_b66_route()
    checks = report["parent_neighbor_checks"]
    assert set(checks) >= {
        "rail_to_parent_wood",
        "rail_to_parent_brackets",
        "bracket_to_parent_wood",
        "bracket_to_parent_brackets",
        "bolt_to_parent_wood",
        "washer_to_parent_wood",
        "tool_to_parent_wood",
        "hardware_to_parent_hardware",
    }
    assert all(not clashes for clashes in checks.values())
    assert report["nominal_access_envelopes_only"] is True
    assert report["actual_hardware_access_verified"] is False
    assert report["full_joint_resistance_verified"] is False
