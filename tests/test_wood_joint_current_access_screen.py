"""Lightweight contracts for the live current-revision access collector."""

from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.wood_joint_wj04_config import WJ04_TRIAL
from scripts.wood_joint_current_access_screen import (
    CURRENT_REVISION_ID,
    ORDINARY_ROLES,
    _detached_role_motion,
    _motion_collision,
    _operation_order_summary,
    _priority_axis_groups,
    _withdrawal_and_insertion,
    _wrench_operation,
    build_current_access_report,
)


def _live_axis_maps():
    candidate_bores = {}
    candidate_hardware = {}
    stock_envelope = cq.Solid.makeBox(2, 2, 2, cq.Vector(1000, 1000, 1000))
    for index in range(92):
        if index < 8:
            axis_id = f"exterior_{index}"
            receivers = (
                ("knee_outer_left_spine", "base_post_outer_left", "outer_rim_left")
                if index == 0
                else ("knee_outer_left_spine", "base_post_outer_left")
            )
        elif index < 16:
            axis_id = f"tall_{index}"
            receivers = ("center_principal_cleat_left", "base_header")
        else:
            axis_id = f"other_{index}"
            receivers = ("other_receiver_a", "other_receiver_b")
        candidate_bores[axis_id] = SimpleNamespace(receiver_ids=receivers)
        candidate_hardware[axis_id] = {
            role: stock_envelope for role in ORDINARY_ROLES
        }
    return candidate_bores, candidate_hardware


def test_priority_selection_uses_live_receiver_ids_and_limits_to_sixteen_axes():
    bores, hardware = _live_axis_maps()

    groups = _priority_axis_groups(bores, hardware)

    assert len(groups["exterior_2x6"]) == 8
    assert len(groups["trimmed_tall_center"]) == 8
    assert not set(groups["exterior_2x6"]) & set(groups["trimmed_tall_center"])
    assert set().union(*map(set, groups.values())) == {
        *(f"exterior_{index}" for index in range(8)),
        *(f"tall_{index}" for index in range(8, 16)),
    }
    assert len(bores["exterior_0"].receiver_ids) == 3


def test_three_receiver_sandwich_uses_all_timbers_for_shaft_travel():
    receivers = {
        "head_member": cq.Solid.makeBox(6, 30, 30, cq.Vector(-6, -15, -15)),
        "middle_member": cq.Solid.makeBox(12, 30, 30, cq.Vector(-18, -15, -15)),
        "far_member": cq.Solid.makeBox(12, 30, 30, cq.Vector(-30, -15, -15)),
    }
    roles = {
        "head": cq.Solid.makeBox(4, 12, 12, cq.Vector(1, -6, -6)),
        "head_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(-1, -8, -8)),
        "shaft": cq.Solid.makeCylinder(3, 34, cq.Vector(-31, 0, 0), cq.Vector(1, 0, 0)),
        "nut": cq.Solid.makeBox(6, 12, 12, cq.Vector(-37, -6, -6)),
        "nut_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(-39, -8, -8)),
    }
    obstacles = {f"wood/{name}": shape for name, shape in receivers.items()}
    obstacles.update(
        {f"candidate_stack/axis/{role}": shape for role, shape in roles.items()}
    )

    report = _withdrawal_and_insertion(
        "axis",
        ("head_member", "middle_member", "far_member"),
        roles,
        receivers,
        obstacles,
    )

    assert report["head_side_receiver_id_by_live_centroid"] == "head_member"
    assert report["derived_travel_mm"] == 31.0
    assert report["reverse_assembly"]["swept_occupancy_is_direction_symmetric"] is True


def test_priority_selection_rejects_wrong_current_axis_coverage():
    bores, hardware = _live_axis_maps()
    hardware.pop("other_91")

    with pytest.raises(ValueError, match="axis IDs differ"):
        _priority_axis_groups(bores, hardware)


def test_motion_report_keeps_other_live_geometry_as_blockers():
    moving = cq.Solid.makeBox(4, 4, 4, cq.Vector(0, 0, 0))
    target = cq.Solid.makeBox(1, 1, 1, cq.Vector(0, 0, 0))
    blocker = cq.Solid.makeBox(1, 1, 1, cq.Vector(2, 2, 2))
    obstacles = {
        "candidate_stack/target/head": target,
        "candidate_stack/other/nut": blocker,
    }

    report = _motion_collision(
        "target",
        {"shaft_motion": moving},
        obstacles,
        excluded_roles=("head",),
        phase="test phase",
        direction_text="test translation",
    )

    assert report["potential_blocker_ids"] == ["candidate_stack/other/nut"]
    assert report["collision_screen"]["excluded_target_obstacle_ids"] == [
        "candidate_stack/target/head"
    ]
    assert report["physical_motion_established"] is False


def test_detached_nut_slide_is_separate_from_unthreading_and_reversed_for_assembly():
    roles = {
        "nut": cq.Solid.makeBox(6, 12, 12, cq.Vector(-56, -6, -6)),
        "nut_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(-50, -8, -8)),
        "shaft": cq.Solid.makeCylinder(3, 60, cq.Vector(-59, 0, 0), cq.Vector(1, 0, 0)),
        "head": cq.Solid.makeBox(4, 12, 12, cq.Vector(1, -6, -6)),
        "head_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(-1, -8, -8)),
    }
    obstacles = {
        f"candidate_stack/axis/{role}": shape for role, shape in roles.items()
    }

    report = _detached_role_motion(
        "axis",
        "nut",
        roles["nut"],
        roles["shaft"],
        cq.Vector(-1, 0, 0),
        obstacles,
    )

    assert report["derived_axial_travel_mm"] == 9.0
    assert report["threaded_disengagement_or_part_capture_established"] is False
    assert report["reverse_assembly"]["swept_occupancy_is_direction_symmetric"] is True


def test_wrench_screen_reports_both_turn_directions_and_limited_samples():
    roles = {
        "head": cq.Solid.makeBox(4, 12, 12, cq.Vector(3, -6, -6)),
        "head_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(1, -8, -8)),
        "shaft": cq.Solid.makeCylinder(3, 60, cq.Vector(-59, 0, 0), cq.Vector(1, 0, 0)),
        "nut": cq.Solid.makeBox(6, 12, 12, cq.Vector(-56, -6, -6)),
        "nut_washer": cq.Solid.makeBox(2, 16, 16, cq.Vector(-50, -8, -8)),
    }
    obstacles = {
        f"candidate_stack/axis/{role}": shape for role, shape in roles.items()
    }

    report = _wrench_operation(
        "axis",
        roles,
        obstacles,
        WJ04_TRIAL.fasteners.tools[0],
        target_role="head",
        side_axis=cq.Vector(1, 0, 0),
    )

    assert report["actual_tool_access_established"] is False
    assert len(report["pose_rows"]) == 2
    for pose in report["pose_rows"]:
        assert [
            row["turn_sample_degrees"]
            for row in pose["discrete_turn_pose_samples"]
        ] == [0.0, -15.0, 15.0, -30.0, 30.0]
        assert {
            row["stroke_direction"]
            for row in pose["continuous_30_degree_AABB_enclosures"]
        } == {"loosening", "tightening"}


def test_sequence_summary_reports_conditional_assembly_and_removal_cycles():
    def operation(*blockers):
        return {"potential_blocker_ids": list(blockers)}

    rows = [
        {
            "axis_id": "axis_a",
            "operations": {
                "head_side_bolt": {
                    "reverse_assembly": operation("candidate_stack/axis_b/head"),
                    "withdrawal": operation("candidate_stack/axis_b/nut"),
                },
                "nut_washer": {"reverse_assembly": operation(), "removal": operation()},
                "nut": {"reverse_assembly": operation(), "removal": operation()},
            },
        },
        {
            "axis_id": "axis_b",
            "operations": {
                "head_side_bolt": {
                    "reverse_assembly": operation("candidate_stack/axis_a/nut"),
                    "withdrawal": operation("candidate_stack/axis_a/head"),
                },
                "nut_washer": {"reverse_assembly": operation(), "removal": operation()},
                "nut": {"reverse_assembly": operation(), "removal": operation()},
            },
        },
    ]

    summary = _operation_order_summary(rows)

    assert summary["assembly_cycles_within_screened_subset"] == [["axis_a", "axis_b"]]
    assert summary["removal_cycles_within_screened_subset"] == [["axis_a", "axis_b"]]
    assert summary["graph_complete_for_all_92_axes_or_all_build_states"] is False


def test_collector_rejects_archived_or_other_revision_geometry_before_reading_it():
    geometry = SimpleNamespace(layout_id="wj24-twenty-four-duty-integrated-static-v1")

    with pytest.raises(ValueError, match=CURRENT_REVISION_ID):
        build_current_access_report(geometry)
