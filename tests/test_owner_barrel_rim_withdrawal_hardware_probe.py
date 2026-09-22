"""The detached rim screen reports nominal collisions without releasing work."""

from functools import lru_cache

import cadquery as cq
import pytest

from scripts import owner_barrel_rim_withdrawal_hardware_probe as screen


@lru_cache(maxsize=1)
def _report():
    return screen.probe()


def test_current_viewer_inventory_and_temporary_removal():
    report = _report()
    assert report["schema"] == "owner_barrel_rim_withdrawal_hardware_probe/v1"
    assert report["source_forward_row_y_mm"] == -85.0
    assert report["fixed_axis_inventory"] == {
        "panel_kicker_screws": 66,
        "frame_bolts": 12,
    }
    assert report["fixed_axis_coordinates_changed"] is False
    assert all(flag is False for flag in report["source_release_flags"].values())
    assert all(
        report[key] is False
        for key in ("drilling_released", "fabrication_released", "structural_released")
    )
    for side in ("left", "right"):
        row = report["sides"][side]
        removed = row["temporary_removal"]
        assert len(removed["rim_attached_stations"]) == 5
        assert len(removed["station_barrels"]) == 10
        assert len(removed["station_bolt_stacks"]) == 10
        assert len(removed["fixed_panel_screws"]) == 8
        assert len(removed["fixed_frame_bolts"]) == 2
        assert row["geometry_altered"] is False
        assert row["retained_outer_header_rows"] == 2
        assert len(row["retained_outer_header_stacks"]) == 2
        assert all(
            stack.endswith("_bolt") and f"header_outer_{side}" in stack
            for stack in row["retained_outer_header_stacks"]
        )
        assert row["viewer_supplemental_heads_washers_absent_for"] == []
        assert not set(row["retained_outer_header_stacks"]) & set(
            row["viewer_supplemental_heads_washers_absent_for"]
        )
        assert row["retained_inventory"]["barrels"] > 0
        assert row["retained_inventory"]["bolt_stack_solids"] == 114
        assert row["retained_inventory"]["protected_panel_screws"] == 58
        assert row["retained_inventory"]["protected_frame_bolts"] == 10


def test_every_sample_reports_all_representable_categories():
    for row in _report()["sides"].values():
        path = row["withdrawal"]
        assert path["direction_xyz"] == pytest.approx([0, *screen.coordinates.N])
        assert path["rim_normal_depth_mm"] == pytest.approx(139.7)
        assert [sample["withdrawal_mm"] for sample in path["samples"]] == list(
            range(0, 161, 5)
        )
        assert path["sampled_clear"] is True
        for sample in path["samples"]:
            assert set(sample["positive_volume_hits_mm3"]) == {
                "other_uncut_wood",
                "retained_barrels",
                "retained_bolt_stacks",
                "protected_envelopes",
            }
            assert all(
                volume > screen.HIT_TOL_MM3
                for family in sample["positive_volume_hits_mm3"].values()
                for volume in family.values()
            )
            assert all(
                not family for family in sample["positive_volume_hits_mm3"].values()
            )
        assert path["continuous_sweep_verified"] is False
        assert path["real_hardware_and_service_verified"] is False


def test_a_retained_hardware_collision_is_recorded_at_its_sample():
    rim = cq.Solid.makeBox(10, 10, 10)
    overlap = cq.Solid.makeBox(3, 3, 3, cq.Vector(2, 2, 2))
    path = screen._sample_withdrawal(
        rim,
        (0, 20),
        {
            "other_uncut_wood": {},
            "retained_barrels": {"trial": overlap},
            "retained_bolt_stacks": {},
            "protected_envelopes": {},
        },
    )
    assert path["samples"][0]["positive_volume_hits_mm3"]["retained_barrels"] == {
        "trial": pytest.approx(27.0)
    }
    assert path["samples"][1]["positive_volume_hits_mm3"]["retained_barrels"] == {}
    assert path["sampled_clear"] is False


def test_changed_fixed_axis_or_forward_row_is_rejected():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    assembly["panel_connections"] = assembly["panel_connections"][:-1]
    with pytest.raises(ValueError, match="Fixed source axes changed"):
        screen.probe(assembly=assembly)

    assembly = build_viewer_assembly()
    assembly["diagnostics"]["producer_diagnostics"]["outer_top8"] = {
        **assembly["diagnostics"]["producer_diagnostics"]["outer_top8"],
        "viewer_trial_outer_header_forward_y_mm": -75.0,
    }
    with pytest.raises(ValueError, match="Viewer outer-header forward row changed"):
        screen.probe(assembly=assembly)


def test_missing_outer_header_supplemental_solid_is_rejected():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    name = "barrel_trial_clip_timber_header_outer_left_1_bolt"
    assembly["stacks"] = {
        **assembly["stacks"],
        name: {"shaft": assembly["stacks"][name]["shaft"]},
    }
    with pytest.raises(
        ValueError, match="Viewer outer-header row changed|Viewer bolt stack changed"
    ):
        screen.probe(assembly=assembly)
