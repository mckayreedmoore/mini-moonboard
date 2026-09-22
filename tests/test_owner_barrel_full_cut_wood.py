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
    )
    report = visual["report"]
    assert report["candidate_barrel_pairs_with_cut_wood"] == 46
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
