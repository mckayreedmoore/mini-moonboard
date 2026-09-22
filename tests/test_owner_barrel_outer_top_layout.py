"""Focused geometry-only contract for the remaining eight owner duties."""

import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import owner_barrel_outer_top_layout as layout
from scripts import owner_layout_protected as protected
from scripts import simple_cross_dowel_continuation as hardware
from scripts import simple_owner_duty_ledger as ledger


def test_eight_duties_use_one_provisional_part_basis_without_release():
    result = layout.screen()
    assert len(result["stations"]) == 8
    assert result["source_axes"] == {"panel": 66, "frame_bolt": 12}
    assert result["provisional_hardware"]["axis_offset_mm"] == 8.001
    assert result["provisional_hardware"]["axis_offset_sensitivity_mm"] == [
        6.0,
        8.001,
        10.0,
    ]
    assert result["direct_count"] >= 2
    assert result["direct_count"] + result["exception_count"] == 8
    for station in result["stations"].values():
        assert station["source_members"]
        assert station["grain"]
        if station["mode"] == "direct":
            assert station["machine_bore_meets_barrel_bore"]
            assert station["source_wood_bore_coverage"] >= 0.999
        else:
            assert station["blocker"]
            assert not station["complete_replacement"]
    assert result["no_legacy_angle_placeholder"]
    assert not result["fit_qualified"]
    assert not result["strength_qualified"]
    assert not result["drilling_released"]


def test_viewer_adapter_has_real_hardware_and_paths_for_eight_duties():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    built = layout.build_layout(wood)
    assert len(built["stations"]) == 8
    assert built["diagnostics"]["disposition"] == "REVISE"
    for row in built["stations"].values():
        assert row["mode"] == "direct"
        assert row["compact_alternate_block"] is None
        assert row["axis_offset_mm"] == 8.001
        assert row["disposition"] == "REVISE"
        assert len(row["bolts"]) == len(row["barrels"]) == 2
        assert set(row["stacks"]) == set(row["bolts"])
        assert len(row["drilling_paths"]) == len(row["access_paths"]) == 4
        assert all(shape.Volume() > 0 for shape in row["barrels"].values())


def test_conditional_recess_only_changes_four_outer_header_viewer_rows():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    original = layout.build_layout(wood)
    previous_viewer = layout.build_revised_layout(wood)
    recessed = layout.build_recessed_viewer_layout(wood)
    assert set(recessed["stations"]) == set(original["stations"])
    assert recessed["diagnostics"]["viewer_trial_outer_header_forward_y_mm"] == -85.0
    for station, row in recessed["stations"].items():
        before = previous_viewer["stations"][station]
        if not station.startswith("clip_timber_header_outer_"):
            assert [b.start.toTuple() for b in row["bolts"].values()] == [
                b.start.toTuple() for b in before["bolts"].values()
            ]
            assert all(set(stack) == {"shaft"} for stack in before["stacks"].values())
            assert all(
                set(stack) == {"shaft", "washer", "head"}
                for stack in row["stacks"].values()
            )
            continue
        assert sorted(
            bolt.start.y for bolt in original["stations"][station]["bolts"].values()
        ) == [
            -135.0,
            -75.0,
        ]
        assert sorted(bolt.start.y for bolt in before["bolts"].values()) == [
            -135.0,
            -75.0,
        ]
        assert sorted(bolt.start.y for bolt in row["bolts"].values()) == [
            -135.0,
            -85.0,
        ]
        for name, bolt in row["bolts"].items():
            assert bolt.start.z == pytest.approx(before["bolts"][name].start.z - 6.651)
            assert set(row["stacks"][name]) == {"shaft", "washer", "head"}
            assert row["stacks"][name]["head"].BoundingBox().zmax == pytest.approx(
                wood["base_header"].BoundingBox().zmax - 1.0
            )
        assert sum("counterbore" in name for name in row["drilling_paths"]) == 2
        assert row["disposition"] == "REVISE"
    assert recessed["diagnostics"]["conditional_rim_removal_required"] is True


def test_recessed_viewer_adds_exactly_twelve_nonheader_stacks_at_bolt_seats():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    default = layout.build_layout(wood)
    revised = layout.build_revised_layout(wood)
    viewer = layout.build_recessed_viewer_layout(wood)
    added = {
        name
        for station, row in viewer["stations"].items()
        if not station.startswith("clip_timber_header_outer_")
        for name in row["stacks"]
    }
    expected_stations = (
        "clip_angle_base_left",
        "clip_angle_base_right",
        "clip_single_top_left_1",
        "clip_single_top_right_2",
        "clip_split_top_center_left",
        "clip_split_top_center_right",
    )
    assert added == {
        f"barrel_trial_{station}_{index}_bolt"
        for station in expected_stations
        for index in (1, 2)
    }
    assert viewer["diagnostics"]["viewer_trial_complete_stack_rows"] == 16
    assert viewer["diagnostics"]["viewer_trial_head_washer_hits_mm3"] == {}
    for station, row in viewer["stations"].items():
        for name, bolt in row["bolts"].items():
            if name not in added:
                continue
            assert set(default["stations"][station]["stacks"][name]) == {"shaft"}
            assert set(revised["stations"][station]["stacks"][name]) == {"shaft"}
            stack = row["stacks"][name]
            seat = (
                bolt.start + bolt.direction * hardware.WASHER_THICKNESS_SENSITIVITY_MM
            )
            washer = stack["washer"]
            head = stack["head"]
            axis = bolt.direction.normalized()
            washer_extent = sorted(
                vertex.Center().dot(axis) for vertex in washer.Vertices()
            )
            head_extent = sorted(
                vertex.Center().dot(axis) for vertex in head.Vertices()
            )
            assert washer_extent[0] == pytest.approx(bolt.start.dot(axis))
            assert washer_extent[-1] == pytest.approx(seat.dot(axis))
            assert head_extent[-1] == pytest.approx(bolt.start.dot(axis))


def test_recessed_viewer_new_heads_and_washers_clear_fixed_and_unrelated_wood():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    viewer = layout.build_recessed_viewer_layout(wood)
    fixed = protected.inventory()
    duties = ledger.selected_duties()
    for station, row in viewer["stations"].items():
        if station.startswith("clip_timber_header_outer_"):
            continue
        unrelated = {
            name: shape
            for name, shape in wood.items()
            if name not in duties[station]["timber"]
        }
        for stack in row["stacks"].values():
            for role in ("head", "washer"):
                shape = stack[role]
                assert not any(protected.hits({role: shape}, fixed).values())
                assert all(
                    protected._volume(shape, target) <= layout.TOL_MM3
                    for target in unrelated.values()
                )


def test_recessed_viewer_reports_exact_unrelated_wood_stack_blocker():
    wood = {part.name: part.shape for part in variant(KERF_RIGHT).uncut_wood_parts()}
    viewer = layout.build_recessed_viewer_layout(wood)
    station = "clip_single_top_left_1"
    bolt_name = next(iter(viewer["stations"][station]["bolts"]))
    wood["unrelated_trial_obstacle"] = viewer["stations"][station]["stacks"][bolt_name][
        "head"
    ]
    with pytest.raises(ValueError, match=f"{bolt_name}.*unrelated_trial_obstacle"):
        layout.build_recessed_viewer_layout(wood)
