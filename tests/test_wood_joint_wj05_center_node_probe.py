"""Focused, source-independent checks for the WJ-05 center-node trial."""

import json

import cadquery as cq
import pytest

from scripts import wood_joint_wj05_center_node_probe as probe


def test_l82_upper_cleat_is_full_4x4_with_open_wire_relief_and_partial_seat():
    parts = probe._candidate_parts({})
    right_lower = parts["center_post_cleat_right"]
    left_lower = parts["center_post_cleat_left"]
    right_upper = parts["center_principal_cleat_right"]
    left_upper = parts["center_principal_cleat_left"]

    assert probe._bounds(right_lower) == [
        199.05,
        287.95,
        -175.7,
        -86.8,
        110.0,
        238.9,
    ]
    assert probe._bounds(left_lower) == [
        -287.95,
        -199.05,
        -175.7,
        -86.8,
        110.0,
        238.9,
    ]
    assert probe._bounds(right_upper) == pytest.approx(
        [89.05, 177.95, -223.86273, -61.12876, 277.0, 339.81564],
        abs=1e-5,
    )
    assert probe._bounds(left_upper) == pytest.approx(
        [-177.95, -89.05, -223.86273, -61.12876, 277.0, 339.81564],
        abs=1e-5,
    )
    assert probe.UPPER_CLEAT_N_MM == (50.8, 139.7)
    assert probe.UPPER_CLEAT_GRAIN_LENGTH_MM == 82.0
    assert probe.UPPER_CLEAT_RAW_GRAIN_LENGTH_MM == pytest.approx(156.596, abs=0.001)

    unrelieved = probe._upper_cleat_right(apply_wire_relief=False)
    relief = probe._upper_cleat_wire_relief()
    assert unrelieved.isValid()
    assert right_upper.isValid()
    assert unrelieved.Volume() == pytest.approx(88.9 * 88.9 * 82.0, rel=1e-8)
    assert unrelieved.Volume() - right_upper.Volume() == pytest.approx(
        4654.617, abs=0.01
    )
    assert relief.Volume() == pytest.approx(4654.617, abs=0.01)
    assert probe.UPPER_WIRE_RELIEF_N_MAX_MM == pytest.approx(61.971187, abs=1e-6)


def test_sixteen_axes_have_expected_rows_grips_and_geometry_only_screens():
    axes = [
        axis
        for side in probe.SIDES
        for axis in probe._upper_fastener_axes(side) + probe._lower_fastener_axes(side)
    ]
    assert len(axes) == 16
    assert len({axis["axis_id"] for axis in axes}) == 16
    assert {axis["candidate_sku"] for axis in axes} == {None}
    assert all(axis["capacity_assigned"] is False for axis in axes)
    assert {
        axis["interface_id"] for axis in axes
    } == {
        "clip_split_base_center_left",
        "clip_split_base_center_right",
        "clip_split_header_center_left",
        "clip_split_header_center_right",
    }

    by_id = {axis["axis_id"]: axis for axis in axes}
    assert by_id["center_principal_right_1"]["wood_grip_mm"] == 127.0
    assert by_id["center_principal_right_1"]["origin_global_xyz_mm"] == pytest.approx(
        [50.95, -150.089079, 295.768089], abs=1e-6
    )
    assert by_id["center_principal_right_2"]["origin_global_xyz_mm"] == pytest.approx(
        [50.95, -128.877088, 321.047555], abs=1e-6
    )
    assert by_id["center_principal_header_right_1"]["wood_grip_mm"] == pytest.approx(
        100.915644
    )
    assert by_id["center_post_header_right_1"]["wood_grip_mm"] == 167.0

    principal_screen = probe._axis_screen_metadata(
        by_id["center_principal_right_1"]
    )
    assert principal_screen["grain_end_distances_mm"] == [24.5, 57.5]
    assert principal_screen["nearest_grain_end_conditional_3p5D_margin_mm"] == pytest.approx(
        2.275
    )
    assert principal_screen["nearest_grain_end_conditional_7D_margin_mm"] == pytest.approx(
        -19.95
    )
    assert principal_screen["cleat_cross_grain_edge_distances_mm"] == pytest.approx(
        [44.45, 44.45]
    )
    assert principal_screen["crossgrain_ray_to_horizontal_seat_geometry_only_mm"] == pytest.approx(
        29.197963, abs=1e-6
    )
    assert principal_screen["principal_row_pitch_mm"] == 33.0
    assert principal_screen["principal_row_pitch_minus_5D_mm"] == pytest.approx(1.25)
    assert principal_screen["conditional_screens_mm"]["5D_pair_spacing"] == 31.75
    assert "oblique" in principal_screen["note"]

    header_screen = probe._axis_screen_metadata(
        by_id["center_principal_header_right_1"]
    )
    assert min(header_screen["cleat_x_edge_distances_mm"]) == pytest.approx(26.95)
    assert min(header_screen["cleat_entry_local_N_edge_distances_mm"]) == pytest.approx(
        24.197795, abs=1e-6
    )
    assert min(header_screen["cleat_exit_local_N_edge_distances_mm"]) == pytest.approx(
        24.325, abs=0.01
    )

    lower_screen = probe._axis_screen_metadata(by_id["center_post_header_right_1"])
    assert min(lower_screen["cleat_y_edge_distances_mm"]) == pytest.approx(26.95)


def test_installed_stack_stays_separate_from_tool_proxies_and_relief_clearance():
    axes = probe._upper_fastener_axes("right")
    axis = axes[0]
    shapes = probe._fastener_shapes(axis)
    assert set(shapes) == {
        "bore",
        "shaft",
        "head_washer",
        "head",
        "nut_washer",
        "nut",
        "head_tool",
        "nut_tool",
    }
    assert all(shapes[name].Volume() > 0 for name in shapes)
    assert (
        axis["wood_grip_mm"]
        + 2 * probe.WASHER_THICKNESS_MM
        + probe.NUT_HEIGHT_MM
        + probe.THREAD_PAST_NUT_MM
    ) == pytest.approx(139.2174)

    records = probe._axis_relief_distance_records(
        axes, probe._upper_cleat_wire_relief()
    )
    assert records[0]["axis_id"] == "center_principal_right_1"
    assert records[0]["axis_centerline_min_distance_to_removed_wedge_mm"] > 90.0
    assert records[0]["installed_component_min_distance_to_removed_wedge_mm"][
        "nut_washer"
    ] > 80.0
    assert records[1]["axis_centerline_min_distance_to_removed_wedge_mm"] > 60.0
    assert records[1]["installed_component_min_distance_to_removed_wedge_mm"][
        "nut_washer"
    ] > 50.0
    assert all(record["tool_envelopes_included"] is False for record in records)

    left_records = probe._axis_relief_distance_records(
        probe._upper_fastener_axes("left"), probe._upper_cleat_wire_relief()
    )
    assert [
        record["axis_centerline_min_distance_to_removed_wedge_mm"]
        for record in left_records
    ] == pytest.approx(
        [record["axis_centerline_min_distance_to_removed_wedge_mm"] for record in records]
    )


@pytest.mark.parametrize(
    "direction,axis_index",
    [
        ((1.0, 0.0, 0.0), 0),
        ((-1.0, 0.0, 0.0), 0),
        ((0.0, 0.0, 1.0), 2),
        ((0.0, 0.0, -1.0), 2),
    ],
)
def test_head_tool_proxy_seats_at_head_and_extends_outward_only(direction, axis_index):
    axis = {
        "origin_global_xyz_mm": [10.0, 20.0, 30.0],
        "direction_global_xyz": direction,
        "wood_grip_mm": 100.0,
    }

    shapes = probe._fastener_shapes(axis)
    tool = shapes["head_tool"].BoundingBox()
    head = shapes["head"].BoundingBox()
    bounds = [
        (tool.xmin, tool.xmax),
        (tool.ymin, tool.ymax),
        (tool.zmin, tool.zmax),
    ][axis_index]
    head_bounds = [
        (head.xmin, head.xmax),
        (head.ymin, head.ymax),
        (head.zmin, head.zmax),
    ][axis_index]
    head_outer = (
        axis["origin_global_xyz_mm"][axis_index]
        - direction[axis_index]
        * (probe.WASHER_THICKNESS_MM + probe.HEAD_HEIGHT_MM)
    )
    outward_endpoint = head_outer - direction[axis_index] * probe.TOOL_LENGTH_MM

    assert bounds == pytest.approx(
        (min(head_outer, outward_endpoint), max(head_outer, outward_endpoint))
    )
    seated_head_face = head_bounds[0] if direction[axis_index] > 0 else head_bounds[1]
    assert seated_head_face == pytest.approx(head_outer)


def test_wire_clearance_gate_fails_closed_below_2mm():
    candidate = cq.Solid.makeBox(10, 10, 10, cq.Vector(0, 0, 0))
    clear_wire = cq.Solid.makeBox(1, 1, 1, cq.Vector(12, 0, 0))
    close_wire = cq.Solid.makeBox(1, 1, 1, cq.Vector(11.9, 0, 0))

    clear = probe._source_wire_clearance({"upper": candidate}, {"wire": clear_wire})[
        "upper"
    ]
    close = probe._source_wire_clearance({"upper": candidate}, {"wire": close_wire})[
        "upper"
    ]
    absent = probe._source_wire_clearance({"upper": candidate}, {})["upper"]

    assert clear["distance_gate_passed"] is True
    assert clear["minimum_proven_clearance_lower_bound_mm"] == pytest.approx(2.0)
    assert close["distance_gate_passed"] is False
    assert close["below_required_clearance_mm"] == {"wire": pytest.approx(1.9)}
    assert absent["distance_gate_passed"] is False


def test_source_fingerprint_covers_active_wire_and_protected_inputs():
    bindings = probe._source_bindings()

    assert {
        "mini_moonboard/round_service_wiring.py",
        "mini_moonboard/hold_tnut_reinforcement.py",
        "docs/round-service-wiring-reference.json",
        "docs/led-wiring-reference.json",
        "scripts/owner_layout_protected.py",
    } <= set(bindings)
    assert all(len(digest) == 64 for digest in bindings.values())


def test_fixed_axis_subcounts_cover_actual_source_members_and_reject_unknowns():
    inventory = json.loads(probe.SOURCE_INVENTORY.read_text())
    rows = inventory["fixed_panel_kicker_screws"]
    counts = probe._fixed_axis_member_counts(rows)

    assert counts == {"panel_axes": 48, "kicker_axes": 18}
    assert sum(counts.values()) == len(rows) == 66
    with pytest.raises(ValueError, match="Unrecognized fixed panel/kicker member"):
        probe._fixed_axis_member_counts([{"panel_member": "unexpected_panel"}])


def test_trial_cannot_assign_capacity_or_release_drilling():
    assert probe.RELEASE_FLAGS == {
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "rating_claimed": False,
    }
    assert probe.TRIAL_ID == "wj05-center-node-rear-4x4-upper-l82-wire-relief-v2"
