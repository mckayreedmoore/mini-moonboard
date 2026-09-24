"""Focused tests for the bounded WJ-04 paired-joint access plan."""

from __future__ import annotations

import json
import math
from pathlib import Path

import cadquery as cq
import pytest

from scripts import wood_joint_wj04_pair_access as probe

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"


def test_plan_records_panel_off_state_and_fixed_electrical_obstacles():
    plan = probe.trial_plan()
    panel_off = plan["operations"]["panel_off_state"]

    assert panel_off["panels_removed"] == ["main_lower_right", "main_upper_right"]
    assert len(panel_off["attached_tnut_ids_removed"]) == 60
    assert len(panel_off["hold_projection_ids_removed_with_panels"]) == 60
    assert len(panel_off["panel_fastener_axis_ids_removed_for_detachment"]) == 24
    assert panel_off["lights_remain_fixed_count"] == 132
    assert panel_off["wires_remain_fixed_count"] == 131
    assert panel_off["frame_bolt_obligations_retained"] == 12
    assert panel_off["panel_kicker_axis_obligations_retained"] == 66
    assert panel_off["panel_removal_path_verified"] is False


def test_plan_directly_pins_g7_materializer_source():
    plan = probe.trial_plan()
    path = "scripts/wood_joint_wj04_upper_g7_crosscut_probe.py"

    assert plan["source_inputs_sha256"][path] == probe._sha256(ROOT / path)


def test_outer_rail_duties_are_unresolved_prerequisites_not_removed():
    plan = probe.trial_plan()
    outer = plan["operations"]["outer_duty_prerequisites"]

    assert outer["status"] == "unresolved_prerequisite"
    assert outer["removed_from_obstacle_map"] is False
    assert outer["accepted_replacement_count"] == 0
    assert set(outer["duties"]) == {
        "clip_horizontal_lower_right_2",
        "clip_horizontal_upper_right_2",
    }
    assert all(row["legacy_sds_axis_count"] == 6 for row in outer["duties"].values())


def test_local_principal_tool_screen_uses_facom_proxy_and_bounded_sectors():
    plan = probe.trial_plan()
    tool = plan["operations"]["principal_x_bolt_tool_screen"]

    assert tool["environment_state"] == "panel_off_right_upper_and_lower"
    assert tool["candidate_id"] == "facom_34_7_16"
    assert tool["external_proxy_dimensions_mm"] == {
        "head_diameter_and_handle_width": 22.0,
        "head_thickness": 3.0,
        "overall_length": 100.0,
    }
    assert tool["working_stroke_degrees"] == 30.0
    assert tool["one_flat_reindex_degrees"] == 60.0
    assert tool["full_repeatable_nut_removal_proven"] is False
    assert tool["stack_ids"] == [
        "lower_principal_1",
        "lower_principal_2",
        "upper_principal_1",
        "upper_principal_2",
    ]


def test_panel_off_accounting_fails_closed_on_missing_or_duplicate_axis():
    inventory = json.loads(INVENTORY.read_text())
    datums = probe._right_main_tnut_datums()

    missing = dict(inventory)
    missing["fixed_panel_kicker_screws"] = [
        row
        for row in inventory["fixed_panel_kicker_screws"]
        if row["panel_member"] != "main_lower_right"
        or row["axis_id"] != "round_panel_lower_right_rim_1"
    ]
    with pytest.raises(ValueError, match="12 unique panel fastener axes for main_lower_right"):
        probe._panel_off_state(missing, datums)

    duplicate = dict(inventory)
    duplicate["fixed_panel_kicker_screws"] = [
        *inventory["fixed_panel_kicker_screws"],
        next(
            row
            for row in inventory["fixed_panel_kicker_screws"]
            if row["panel_member"] == "main_upper_right"
        ),
    ]
    with pytest.raises(ValueError, match="duplicate panel fastener axis ID"):
        probe._panel_off_state(duplicate, datums)


def test_panel_off_filter_removes_only_named_panel_owned_obstacles():
    plan = probe.trial_plan()
    panel_state = plan["operations"]["panel_off_state"]
    tnut_ids = panel_state["attached_tnut_ids_removed"]
    projection_ids = panel_state["hold_projection_ids_removed_with_panels"]
    panel_axes = panel_state["panel_fastener_axis_ids_removed_for_detachment"]
    frame_ids = [
        row["axis_id"] for row in json.loads(INVENTORY.read_text())["starting_frame_bolts"]
    ]
    frame_roles = ("shaft", "head_washer", "nut_washer", "head", "nut")
    protected = {
        **{f"tnuts/{name}": object() for name in tnut_ids},
        **{f"tnuts/retained_{index}": object() for index in range(82)},
        **{f"hold_hole_and_trial_projection/{name}": object() for name in projection_ids},
        **{
            f"hold_hole_and_trial_projection/retained_{index}": object()
            for index in range(82)
        },
        **{f"panel_screws/{name}": object() for name in panel_axes},
        **{f"panel_screws/retained_{index}": object() for index in range(42)},
        **{f"lights/led_{index}": object() for index in range(132)},
        **{f"wires/wire_{index}": object() for index in range(131)},
        "retained_legacy_connectors/clip_horizontal_lower_right_2": object(),
        **{
            f"frame_bolt_components/{axis_id}/{role}": object()
            for axis_id in frame_ids
            for role in frame_roles
        },
    }
    geometry = type(
        "PanelStateGeometry",
        (),
        {
            "panels": {
                "main_lower_right": object(),
                "main_upper_right": object(),
                "main_lower_left": object(),
            },
            "protected": protected,
        },
    )()

    panels, remaining = probe._panel_off_maps(geometry, plan)

    assert set(panels) == {"main_lower_left"}
    assert len([name for name in remaining if name.startswith("tnuts/")]) == 82
    assert len(
        [name for name in remaining if name.startswith("hold_hole_and_trial_projection/")]
    ) == 82
    assert len([name for name in remaining if name.startswith("lights/")]) == 132
    assert len([name for name in remaining if name.startswith("wires/")]) == 131
    assert len(
        [name for name in remaining if name.startswith("frame_bolt_components/")]
    ) == 60
    assert "retained_legacy_connectors/clip_horizontal_lower_right_2" in remaining


def test_oblique_cylinder_exit_bound_covers_curved_support_between_seam_vertices():
    shape = cq.Solid.makeCylinder(
        10.0,
        30.0,
        cq.Vector(2.0, 3.0, 5.0),
        cq.Vector(1.0, 1.0, 1.0),
    )
    axis = cq.Vector(1.0, -1.0, 0.0).normalized()
    start = cq.Vector(2.0, 3.0, 5.0)
    end = start + cq.Vector(1.0, 1.0, 1.0).normalized() * 30.0
    radial_support = 10.0 * math.sqrt(1.0 - axis.dot(cq.Vector(1, 1, 1).normalized()) ** 2)
    exact_low = min(start.dot(axis), end.dot(axis)) - radial_support
    exact_high = max(start.dot(axis), end.dot(axis)) + radial_support
    vertex_values = [cq.Vector(vertex.Center()).dot(axis) for vertex in shape.Vertices()]

    actual_low, actual_high = probe._projection_bounds(shape, axis)

    assert min(vertex_values) > exact_low
    assert max(vertex_values) < exact_high
    assert actual_low <= exact_low
    assert actual_high >= exact_high
