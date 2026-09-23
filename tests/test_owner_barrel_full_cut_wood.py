"""All diagnostic barrel drilling paths must appear in integrated visual timber."""

from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_visual_wood import build_visual_wood


def test_integrated_visual_timber_represents_all_barrel_paths():
    assembly = build_integrated_viewer_assembly()
    visual = build_visual_wood(
        assembly=assembly,
        candidate_service=True,
        candidate_center_cuts=True,
        candidate_all_cuts=True,
        complete_frame_hosts=True,
    )
    report = visual["report"]
    assert report["candidate_barrel_pairs_with_cut_wood"] == 46
    assert report["replacement_timber_members"] == 20
    assert report["retained_frame_bolt_cuts_in_replacements"] == 24
    assert report["inherited_additional_cuts_in_replacements"] == 2
    assert report["total_host_cutter_records"] == 268
    assert report["all_host_cutters_intersect_raw_wood"] is True
    assert report["all_host_cutters_removed_from_cut_solids"] is True
    assert report["all_twenty_frame_timber_hosts_represented"] is True
    assert set(visual["wood"]) == {
        "base_floor_left",
        "base_floor_right",
        "base_header",
        "base_post_center_left",
        "base_post_center_right",
        "base_post_outer_left",
        "base_post_outer_right",
        "base_principal_center_left",
        "base_principal_center_right",
        "base_rail_bottom_left",
        "base_rail_bottom_right",
        "base_rail_service_lower_left",
        "base_rail_service_lower_right",
        "base_rail_service_upper_left",
        "base_rail_service_upper_right",
        "base_rail_top",
        "base_side_left",
        "base_side_right",
        "lumber_leg_left",
        "lumber_leg_right",
    }
    for side in ("left", "right"):
        floor = report["per_member"][f"base_floor_{side}"]["counts"]
        leg = report["per_member"][f"lumber_leg_{side}"]["counts"]
        assert floor["retained_frame"] == 4
        assert floor["total"] == 4
        assert leg["retained_frame"] == 4
        assert leg["inherited_additional"] == 1
        assert leg["total"] == 5
    assert report["remaining_trial_cuts"] == 108
    assert report["barrel_drilling_paths_without_cut_wood"] == []
    assert report["barrel_path_host_anomalies"] == []
    assert report["unrelated_remaining_pair_cut_intersections"] == []
    assert set(report["barrel_path_hosts"]) == set(assembly["drilling_paths"])
    for path_name, members in report["barrel_path_hosts"].items():
        cutter = assembly["drilling_paths"][path_name]
        assert members
        for member in members:
            assert visual["wood"][member].intersect(cutter).Volume() < 1e-3
    assert report["fixed_panel_receiver_cuts_in_replacements"] == 66
    assert report["excluded_legacy_sds_axes"] == 144
    assert report["release"] is False
