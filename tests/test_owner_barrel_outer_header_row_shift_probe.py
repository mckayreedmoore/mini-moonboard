"""Only the four outer-header rows vary; no result releases construction."""

from functools import lru_cache

import pytest

from scripts import owner_barrel_outer_header_row_shift_probe as screen


@lru_cache(maxsize=1)
def _report():
    return screen.probe()


def test_exact_scope_and_no_release():
    report = _report()
    assert report["inventory"]["outer_header_rows"] == 4
    assert report["inventory"]["fixed_panel_screws"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["source_forward_y_mm"] == -85.0
    assert set(report["options"]) == {"-75", "-80", "-85", "-90"}
    assert all(not flag for flag in report["release_flags"].values())
    assert not any(
        report[key]
        for key in (
            "layout_approved",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        )
    )
    assert "BLOCKED" in report["rim_on_driver"]


def test_row_geometry_cuts_only_three_intended_hosts():
    report = _report()
    for position, option in report["options"].items():
        assert option["rear_y_mm"] == -135.0
        assert option["forward_y_mm"] == float(position)
        assert len(option["rows"]) == 4
        assert len(option["intended_bore_wood_coverage"]) == 12
        assert all(
            value >= 0.999 for value in option["intended_bore_wood_coverage"].values()
        )
        assert set(option["cut_hosts"]) == {
            "base_header",
            "base_post_outer_left",
            "base_post_outer_right",
        }
        assert all(
            member["removed_volume_mm3"] > 0
            and member["cut_is_valid"]
            and member["connected_nominally"]
            for member in option["cut_hosts"].values()
        )
        for name, row in option["rows"].items():
            assert row["counterbore_diameter_mm"] == pytest.approx(25.4)
            assert row["y_mm"] == (-135.0 if name.endswith("_1") else float(position))
            assert row["rim_on_driver_hit_mm3"] > 1.0
            assert row["installed_stack_side_rim_hit_mm3"] == 0
            assert row["counterbore_wood_coverage"] == pytest.approx(1.0)
            assert row["head_in_counterbore_fraction"] == pytest.approx(1.0)
            assert row["washer_in_counterbore_fraction"] == pytest.approx(1.0)
            assert row["barrel_in_cross_bore_fraction"] == pytest.approx(1.0)
            assert row["machine_bore_meets_barrel_bore"]
        assert option["same_side_counterbore_clear_gaps_mm"] == {
            "left": pytest.approx(abs(-135.0 - float(position)) - 25.4),
            "right": pytest.approx(abs(-135.0 - float(position)) - 25.4),
        }


def test_nearest_screw_and_competing_geometry_are_reported_not_approved():
    report = _report()
    expected = {"-75": 2.70625, "-80": 7.70625, "-85": 12.70625, "-90": 17.70625}
    for position, option in report["options"].items():
        nearest = option["nearest_fixed_screw_to_removed_wood"]
        assert nearest["fixed_screw"].startswith("round_kicker_")
        assert nearest["distance_mm"] == pytest.approx(expected[position], abs=0.001)
        assert nearest["cut_path"]
        assert option["protected_fixed_solid_hits_mm3"] == {}
        assert option["other_viewer_hardware_and_path_hits_mm3"] == {}
        assert all(
            not row["unrelated_wood_hits_mm3"] for row in option["rows"].values()
        )
        assert all(
            not row["tool_other_wood_hits_with_rim_removed_mm3"]
            for row in option["rows"].values()
        )
        assert option["disposition"] == "REVISE"
        assert not option["clearance_approved"]


def test_changed_fixed_axis_is_rejected():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    assembly["panel_connections"] = assembly["panel_connections"][:-1]
    with pytest.raises(ValueError, match="Fixed source axes changed"):
        screen.probe(assembly=assembly)


def test_changed_viewer_forward_row_is_rejected():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    assembly["diagnostics"]["producer_diagnostics"]["outer_top8"][
        "viewer_trial_outer_header_forward_y_mm"
    ] = -75.0
    with pytest.raises(ValueError, match="Viewer outer-header forward row changed"):
        screen.probe(assembly=assembly)
