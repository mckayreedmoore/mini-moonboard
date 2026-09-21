"""Bounded second-bolt geometry screen for the revised PB-02 pose."""

from scripts.simple_center_second_bolt_probe import OFFSETS, probe


def test_second_bolt_screen_keeps_fixed_axes_and_checks_every_interface():
    result = probe()
    assert result["fixed_axes"] == {"panel": 48, "kicker": 18}
    assert result["fixed_screw_axes_checked"] == 66
    assert set(result["interfaces"]) == {
        "post_cleat",
        "cleat_header",
        "header_cleat",
        "cleat_principal",
    }
    assert all(0 < len(trials) <= 4 for trials in OFFSETS.values())
    assert result["conditional_markers_only"] is True
    assert result["rating_or_drilling_release"] is False
    for name, data in result["interfaces"].items():
        assert len(data["trials"]) == len(OFFSETS[name])
        for trial in data["trials"]:
            assert trial["axis_spacing_mm"] > 0
            assert set(trial["checks"]) == {
                "intended_wood_fraction",
                "washer_bearing_fraction",
                "unintended_wood_hits_mm3",
                "other_bore_hits_mm3",
                "fixed_screw_hits_mm3",
                "hardware_wood_hits_mm3",
                "hardware_screw_hits_mm3",
                "hardware_other_hardware_hits_mm3",
                "socket_wood_hits_mm3",
                "socket_screw_hits_mm3",
                "socket_other_hardware_hits_mm3",
                "socket_other_socket_hits_mm3",
            }
            assert set(trial["member_edge_end_trial_markers"]) == set(
                ("shifted_right_post", "header_post_side_cleat")
                if name == "post_cleat"
                else ("header_post_side_cleat", "base_header")
                if name == "cleat_header"
                else ("base_header", "header_side_cleat")
                if name == "header_cleat"
                else ("header_side_cleat", "base_principal_center_right")
            )
            assert trial["trial_marker_status"] in {
                "fails measured trial marker",
                "incomplete: oblique member unclassified",
                "passes measured trial markers only",
            }
            if trial["collision_fit"]:
                assert all(
                    value > 0
                    for value in trial["checks"]["intended_wood_fraction"].values()
                )
                assert (
                    abs(sum(trial["checks"]["intended_wood_fraction"].values()) - 1)
                    < 1e-6
                )
                assert all(
                    value == 1
                    for value in trial["checks"]["washer_bearing_fraction"].values()
                )
                assert not any(
                    value
                    for key, value in trial["checks"].items()
                    if key.endswith("hits_mm3")
                )
    assert result["interfaces"]["post_cleat"]["any_collision_fit"] is True
    assert result["interfaces"]["cleat_header"]["any_collision_fit"] is True
    assert all(
        not data["any_collision_fit_and_measured_markers"]
        for data in result["interfaces"].values()
    )
    post_high = result["interfaces"]["post_cleat"]["trials"][3]
    assert post_high["collision_fit"] is True
    assert (
        post_high["member_edge_end_trial_markers"]["header_post_side_cleat"][
            "distances"
        ]["z"]["minimum_margin_mm"]
        == -10.55
    )
    header_rear = result["interfaces"]["cleat_header"]["trials"][2]
    assert header_rear["collision_fit"] is True
    assert (
        header_rear["member_edge_end_trial_markers"]["header_post_side_cleat"][
            "distances"
        ]["y"]["minimum_margin_mm"]
        == -14.7
    )
