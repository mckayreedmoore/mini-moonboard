"""Focused unit checks for WJ-04 catalog tool-envelope geometry."""

import math

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_wj04_tool_access import (
    DEFAULT_PRODUCER_COMMAND,
    DEPENDENCY_PATHS,
    _file_bindings,
    build_catalog_wrench_envelope,
    collision_report,
    full_nut_removal_envelope,
    moving_part_translation_report,
    nut_washer_axial_removal_report,
    rotational_sweep,
    translation_sweep,
    trial_binding,
    wrench_reindex_path,
    write_report,
)


def _tool():
    return WJ04_TRIAL.fasteners.tools[0]


def test_tool_report_hashes_candidate_panel_geometry_dependencies():
    expected = {
        "docs/panel-insert-reference.json",
        "mini_moonboard/base_frame.py",
        "mini_moonboard/floor_flush_width.py",
        "mini_moonboard/insert_frame.py",
        "mini_moonboard/panel_grid.py",
        "mini_moonboard/panel_grid_v2.py",
        "mini_moonboard/wood_joint_panel_machining.py",
    }

    bindings = _file_bindings(WJ04_TRIAL)

    assert expected <= set(DEPENDENCY_PATHS)
    assert set(bindings["dependency_sha256"]) == set(DEPENDENCY_PATHS)
    assert all(len(digest) == 64 for digest in bindings["dependency_sha256"].values())


def test_catalog_wrench_external_envelope_uses_head_width_as_diameter():
    tool = _tool()
    shape = build_catalog_wrench_envelope(
        (0, 0, 0), (0, 0, 1), (1, 0, 0), tool, offset_degrees=0
    )
    bounds = shape.BoundingBox()

    assert bounds.xmax - bounds.xmin == pytest.approx(tool.overall_length_mm)
    assert bounds.ymax - bounds.ymin == pytest.approx(tool.head_width_mm)
    assert bounds.zmax - bounds.zmin == pytest.approx(tool.head_thickness_mm)
    assert bounds.xmin == pytest.approx(-tool.head_width_mm / 2)


def test_turning_sweep_contains_intermediate_wrench_orientation():
    tool = _tool()
    shape = build_catalog_wrench_envelope(
        (0, 0, 0), (0, 0, 1), (1, 0, 0), tool, offset_degrees=15
    )
    sweep = rotational_sweep(shape, (0, 0, 0), (0, 0, 1), 30)

    assert sweep.isValid()
    assert sweep.BoundingBox().ymax > shape.BoundingBox().ymax
    assert sweep.BoundingBox().ymin < shape.BoundingBox().ymin


def test_rotation_bound_respects_nonzero_axis_center():
    block = cq.Solid.makeBox(2, 2, 3, cq.Vector(9, -1, 9))
    sweep = rotational_sweep(block, (10, 0, 5), (0, 0, 1), 30)
    full_turn = rotational_sweep(block, (10, 0, 5), (0, 0, 1), 360)
    bounds = sweep.BoundingBox()

    assert bounds.xmin == pytest.approx(10 - math.sqrt(3) / 2 - 0.5)
    assert bounds.xmax < full_turn.BoundingBox().xmax
    assert bounds.xmax == pytest.approx(10 + math.sqrt(3) / 2 + 0.5)
    assert bounds.zmin == pytest.approx(9)
    assert bounds.zmax == pytest.approx(12)


def test_partial_rotation_enclosure_covers_interior_extremum_analytically():
    phase = math.radians(15)
    center = cq.Vector(math.cos(phase), -math.sin(phase), 0)
    block = cq.Solid.makeBox(
        0.001,
        0.001,
        1,
        center + cq.Vector(-0.0005, -0.0005, -0.5),
    )
    sweep = rotational_sweep(block, (0, 0, 0), (0, 0, 1), 30)
    midpoint = block.rotate((0, 0, 0), (0, 0, 1), 15)
    endpoints = (
        block.BoundingBox(),
        block.rotate((0, 0, 0), (0, 0, 1), 30).BoundingBox(),
    )

    assert sweep.BoundingBox().xmax >= midpoint.BoundingBox().xmax
    assert sweep.BoundingBox().xmax > max(bounds.xmax for bounds in endpoints)


def test_reindex_path_uses_sideways_open_end_motion_and_one_flat_reset():
    tool = _tool()
    shape = build_catalog_wrench_envelope(
        (0, 0, 0), (0, 0, 1), (1, 0, 0), tool, offset_degrees=15
    )
    handle_axis = cq.Vector(math.cos(math.radians(15)), math.sin(math.radians(15)), 0)
    path = wrench_reindex_path(
        shape,
        (0, 0, 0),
        (0, 0, 1),
        handle_axis,
        head_width_mm=tool.head_width_mm,
    )

    assert path["stroke_degrees"] == 30
    assert path["stroke_sweep_rotation_bound_degrees"] == 30
    assert path["stroke_sweep_is_full_rotation_bound"] is False
    assert path["reindex_degrees"] == -60
    assert path["open_end_exit_distance_mm"] == tool.head_width_mm
    assert path["open_end_exit_motion_is_unverified_proxy"] is True
    assert path["lateral_unseat_sweep"].isValid()
    assert path["detached_reindex_sweep"].isValid()
    assert path["lateral_reseat_sweep"].isValid()


def test_full_nut_removal_envelope_uses_whole_tool_length_once():
    tool = _tool()
    shape = full_nut_removal_envelope((2, 3, 4), (0, 0, 1), tool, 12.0)
    bounds = shape.BoundingBox()

    assert bounds.xmax - bounds.xmin == pytest.approx(2 * tool.overall_length_mm)
    assert bounds.ymax - bounds.ymin == pytest.approx(2 * tool.overall_length_mm)
    assert bounds.zmax - bounds.zmin == pytest.approx(12 + tool.head_thickness_mm)


def test_linear_sweep_covers_complete_translation_path():
    block = cq.Solid.makeBox(2, 2, 2, cq.Vector(0, 0, 0))
    sweep = translation_sweep(block, (10, 0, 0))
    midpoint = cq.Solid.makeBox(1, 1, 1, cq.Vector(5, 0.5, 0.5))

    assert sweep.isValid()
    assert sweep.BoundingBox().xmax == pytest.approx(12)
    assert sweep.intersect(midpoint).Volume() == pytest.approx(1)


def test_collision_report_excludes_only_explicit_target_geometry():
    envelope = cq.Solid.makeBox(5, 5, 5, cq.Vector(0, 0, 0))
    obstacles = {
        "target_hex": cq.Solid.makeBox(5, 5, 5, cq.Vector(0, 0, 0)),
        "washer": cq.Solid.makeBox(1, 1, 1, cq.Vector(1, 1, 1)),
    }

    result = collision_report(
        {"wrench": envelope}, obstacles, excluded_target_ids=("target_hex",)
    )

    assert result["excluded_target_obstacle_ids"] == ["target_hex"]
    assert result["external_envelope_clear"] is False
    assert result["external_envelope_hits_mm3"] == {"wrench": {"washer": 1.0}}
    assert result["physical_access_established"] is False
    assert result["real_tool_impossibility_proven"] is False
    assert result["bounds_are_conservative"] is True
    assert result["envelope_clash_proves_physical_blockage"] is False


def test_moving_washer_does_not_collide_with_own_copy_but_hits_other_washer():
    moving = cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0))
    other_washer = cq.Solid.makeBox(1, 1, 1, cq.Vector(3, 0, 0))
    result = moving_part_translation_report(
        "washer_clearance_path",
        "stack/head_washer",
        moving,
        (4, 0, 0),
        {
            "stack/head_washer": moving.copy(),
            "other_stack/nut_washer": other_washer,
        },
        exclusion_scope="The moving washer's installed copy is the same part.",
    )

    assert result["excluded_target_obstacle_ids"] == ["stack/head_washer"]
    assert result["external_envelope_hits_mm3"] == {
        "washer_clearance_path": {"other_stack/nut_washer": 1.0}
    }


def test_nut_washer_axial_slide_excludes_removed_stack_parts_only():
    washer_min_id = WJ04_TRIAL.fasteners.washer.inner_diameter_range_mm[0]
    shaft_max_diameter = WJ04_TRIAL.fasteners.bolts[0].body_diameter_range_mm[1]
    washer = cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0))
    obstacles = {
        "stack/nut_washer": washer.copy(),
        "stack/nut": cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0)),
        "stack/shaft": cq.Solid.makeBox(5, 1, 1, cq.Vector(0, 0, 0)),
        "other_stack/shaft": cq.Solid.makeBox(1, 1, 1, cq.Vector(3, 0, 0)),
        "other_stack/head_washer": cq.Solid.makeBox(1, 1, 1, cq.Vector(4, 0, 0)),
    }
    result = nut_washer_axial_removal_report(
        "stack/nut_washer",
        washer,
        obstacles,
        removed_nut_id="stack/nut",
        shaft_id="stack/shaft",
        outward_axis_xyz=(1, 0, 0),
        travel_mm=4,
        washer_min_inner_diameter_mm=washer_min_id,
        shaft_max_diameter_mm=shaft_max_diameter,
    )

    assert result["excluded_target_obstacle_ids"] == [
        "stack/nut",
        "stack/nut_washer",
        "stack/shaft",
    ]
    assert result["external_envelope_hits_mm3"] == {
        "nut_washer_to_clear_bolt_tip": {
            "other_stack/head_washer": 1.0,
            "other_stack/shaft": 1.0,
        }
    }
    assert result["axial_sliding_clearance"] == {
        "motion_is_along_fastener_axis": True,
        "washer_min_inner_diameter_mm": washer_min_id,
        "shaft_max_diameter_mm": shaft_max_diameter,
        "minimum_radial_clearance_mm": pytest.approx(
            (washer_min_id - shaft_max_diameter) / 2
        ),
        "source_bounds_allow_modeled_axial_slide": True,
        "thread_major_diameter_and_received_clearance_verified": False,
        "delivered_parts_and_assembly_clearance_verified": False,
    }


def test_nut_washer_axial_slide_requires_positive_source_bound_clearance():
    shaft_max_diameter = WJ04_TRIAL.fasteners.bolts[0].body_diameter_range_mm[1]
    washer = cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0))

    with pytest.raises(
        ValueError, match="minimum ID must exceed modeled shaft maximum"
    ):
        nut_washer_axial_removal_report(
            "stack/nut_washer",
            washer,
            {"stack/nut_washer": washer.copy()},
            removed_nut_id="stack/nut",
            shaft_id="stack/shaft",
            outward_axis_xyz=(1, 0, 0),
            travel_mm=4,
            washer_min_inner_diameter_mm=shaft_max_diameter,
            shaft_max_diameter_mm=shaft_max_diameter,
        )


def test_trial_binding_preserves_candidate_and_rejects_access_claim():
    result = trial_binding()

    assert result["trial_id"] == WJ04_TRIAL.trial_id
    assert result["tool_candidate"]["candidate_id"] == _tool().candidate_id
    assert result["tool_candidate"]["modeled_head_diameter_mm"] == 22
    assert result["tool_candidate"]["modeled_head_radius_mm"] == 11
    assert result["tool_candidate"]["catalog_head_offsets_degrees"] == [15, 75]
    assert result["tool_candidate"]["catalog_offset_mapping_verified"] is False
    assert result["operation_screen"]["synthetic_heading_cases_degrees"] == [15, 75]
    fasteners = result["fastener_candidates"]
    assert [row["sku"] for row in fasteners["bolts"]] == [
        "25C375HCS5Z",
        "25C600HCS5Z",
    ]
    assert fasteners["hex_head_bounds"]["height_range_mm"] == [3.81, 4.1402]
    assert fasteners["nut"]["sku"] == "25CNFH5Z"
    assert fasteners["washers_per_stack"] == 2
    assert fasteners["purchase_approved"] is False
    assert result["release_claims"]["physical_access_established"] is False


def test_markdown_and_writer_separate_bound_overlap_from_physical_failure(tmp_path):
    clear = {
        "external_envelope_clear": True,
        "external_envelope_hits_mm3": {},
    }
    overlap = {
        "external_envelope_clear": False,
        "external_envelope_hits_mm3": {
            "wrench": {"protected/wire": 2.5},
        },
    }
    data = {
        **trial_binding(),
        "candidate": WJ04_TRIAL.development_candidate_id,
        "source_commit": WJ04_TRIAL.source_commit,
        "producer_sha256": "abc123",
        "producer_command": DEFAULT_PRODUCER_COMMAND,
        "config_source_sha256": "config123",
        "dependency_sha256": {},
        "input_artifact_sha256": {},
        "envelope_screen_status": "diagnostic_overlap_present",
        "limiting_obstacles": [
            {
                "obstacle_id": "protected/wire",
                "maximum_reported_intersection_mm3": 2.5,
            }
        ],
        "stacks": {
            "rail_1": {
                "heading_cases": [
                    {
                        "head_counterhold": clear,
                        "nut_turn_and_reindex": overlap,
                        "nut_tool_vs_head_counterhold": clear,
                    },
                    {
                        "head_counterhold": clear,
                        "nut_turn_and_reindex": clear,
                        "nut_tool_vs_head_counterhold": clear,
                    },
                ],
                "nut_full_removal": {
                    "wrench_full_turn_and_axial_sweep": clear,
                    "nut_translation_sweep": clear,
                    "nut_washer_translation_sweep": clear,
                },
                "full_bolt_withdrawal": clear,
                "head_washer_removal_after_bolt_withdrawal": clear,
            }
        },
    }

    json_path, markdown_path = write_report(data, tmp_path / "wj04-tool-access.json")
    markdown = markdown_path.read_text()

    assert json_path.read_text().startswith('{\n  "candidate"')
    assert "Overlap in bound" in markdown
    assert "does not prove that an actual open-end wrench cannot pass" in markdown
    assert (
        "purchase, drilling, fabrication, structural, and physical-access approvals are false"
        in markdown
    )
    assert "protected/wire (2.5 mm³)" in markdown
