"""Focused coverage of the bounded second-bolt tolerance-pose screen."""

from scripts.simple_center_second_bolt_tolerance_probe import OFFSETS, probe


def test_second_bolts_use_tolerance_pose_and_complete_fixed_geometry():
    result = probe()
    assert result["pose_coordinates_mm"] == {
        "rear_y": -190.0,
        "top_z": 348,
        "vertical_y": -139,
        "cross_z": 312.5,
        "upright_y": -135,
        "upright_z": 360,
        "link_x": 133.5,
    }
    assert result["baseline_nominal_geometry"] == "feasible"
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert result["inner_kicker_edges_supported"] == {"left": True, "right": True}
    assert len(result["existing_bores_checked"]) == 8
    assert set(result["interfaces"]) == set(OFFSETS)
    assert result["conditional_markers_only"] is True
    assert result["rating_or_drilling_release"] is False

    for name, interface in result["interfaces"].items():
        assert len(interface["trials"]) == len(OFFSETS[name]) == 4
        for trial in interface["trials"]:
            assert trial["offset_xyz_mm"] == OFFSETS[name][trial["offset"]]
            assert set(trial["checks"]["intended_wood_fraction"]) == set(
                interface["intended_woods"]
            )
            assert set(trial["checks"]["other_bore_hits_mm3"]).issubset(
                {f"second/{bore}" for bore in result["existing_bores_checked"]}
            )
            assert set(trial["checks"]) >= {
                "washer_bearing_fraction",
                "fixed_screw_hits_mm3",
                "hardware_other_hardware_hits_mm3",
                "socket_other_socket_hits_mm3",
                "socket_other_hardware_hits_mm3",
                "insertion_clear_ends",
            }
            assert len(trial["checks"]["washer_bearing_fraction"]) == 2
            assert set(trial["member_edge_end_trial_markers"]) == set(
                interface["intended_woods"]
            )
            assert trial["axis_spacing_mm"] >= 25.4
            assert trial["conditional_4d_pitch_margin_mm"] >= 0

    fits = [
        (name, trial)
        for name, interface in result["interfaces"].items()
        for trial in interface["trials"]
        if trial["collision_fit"]
    ]
    assert [(name, trial["offset"]) for name, trial in fits] == [
        ("post_cleat", "high_z"),
        ("cleat_header", "rear_y"),
    ]
    assert [trial["minimum_measured_marker_margin_mm"] for _, trial in fits] == [
        -10.55,
        -14.7,
    ]
    assert not any(
        interface["any_collision_fit_and_measured_markers"]
        for interface in result["interfaces"].values()
    )
