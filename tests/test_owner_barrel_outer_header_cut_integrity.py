"""The recessed-header cut screen is detached and cannot approve drilling."""

from functools import lru_cache

import pytest

from scripts import owner_barrel_outer_header_cut_integrity as screen


@lru_cache(maxsize=1)
def _report():
    return screen.probe()


def test_exact_current_viewer_scope_and_no_release():
    report = _report()
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    for side in ("left", "right"):
        station = f"clip_timber_header_outer_{side}"
        assert sorted(
            bolt.start.y
            for name, bolt in assembly["bolts"].items()
            if assembly["bolt_station"][name] == station
        ) == [-135.0, -85.0]
    assert (
        report["source_assembly"] == "export_owner_barrel_scene.build_viewer_assembly"
    )
    assert report["inventory"]["stations"] == 2
    assert report["inventory"]["bolt_rows"] == 4
    assert report["inventory"]["fixed_panel_screws"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert set(report["members"]) == {
        "base_header",
        "base_post_outer_left",
        "base_post_outer_right",
    }
    assert all(not value for value in report["release_flags"].values())
    assert report["disposition"] == "REVISE"
    assert not report["clearance_approved"]
    assert not report["cutting_or_drilling_released"]


def test_only_intended_host_paths_are_subtracted():
    report = _report()
    for name, member in report["members"].items():
        assert member["uncut_volume_mm3"] > member["cut_volume_mm3"] > 0
        assert member["removed_volume_mm3"] > 0
        assert member["cut_solid_count"] == 1
        assert member["cut_is_valid"]
        assert member["uncut_solid_count"] == 1
        paths = member["intended_paths"]
        if name == "base_header":
            assert len(paths) == 8
            assert {path["role"] for path in paths} == {
                "counterbore",
                "machine_bore",
            }
        else:
            assert len(paths) == 4
            assert {path["role"] for path in paths} == {
                "barrel_bore",
                "machine_bore",
            }
            assert all(path["side"] in name for path in paths)
        assert all(path["host_intersection_mm3"] > 0 for path in paths)


def test_nominal_residuals_and_fixed_axes_are_reported_not_accepted():
    report = _report()
    for member in report["members"].values():
        assert member["disposition"] == "REVISE"
        assert not member["clearance_approved"]
        assert member["minimum_modeled_radial_edge_residual_mm"] >= 0
        for path in member["intended_paths"]:
            assert path["radial_edge_residuals_mm"]
            assert all(
                value >= 0 for value in path["radial_edge_residuals_mm"].values()
            )
        for family in ("panel_screws", "frame_bolts"):
            proximity = member["fixed_axis_proximity"][family]
            assert proximity["nearest"]["name"]
            assert proximity["nearest"]["distance_mm"] >= 0
            assert isinstance(proximity["intersections_mm3"], dict)
    assert report["members"]["base_header"]["counterbore_floor_residual_mm"] > 0
    assert report["members"]["base_header"][
        "minimum_modeled_radial_edge_residual_mm"
    ] == pytest.approx(6.35, abs=0.05)
    for side in ("left", "right"):
        post = report["members"][f"base_post_outer_{side}"]
        assert post["fixed_axis_proximity"]["panel_screws"]["nearest"][
            "distance_mm"
        ] == pytest.approx(12.70625, abs=0.05)
    assert report["limits"].lower().find("strength") >= 0


def test_changed_viewer_inventory_is_rejected():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    assembly["drilling_paths"] = dict(assembly["drilling_paths"])
    assembly["drilling_paths"].pop(
        "barrel_trial_clip_timber_header_outer_left_1/counterbore"
    )
    with pytest.raises(ValueError, match="outer-header path inventory"):
        screen.probe(assembly=assembly)
