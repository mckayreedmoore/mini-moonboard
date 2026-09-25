"""Focused non-materializing tests for the left service geometry hypothesis."""

from __future__ import annotations

import json
from types import SimpleNamespace

import cadquery as cq
import pytest

from mini_moonboard.floor_flush_width import KERF_RIGHT
from scripts import wood_joint_left_rail_integration as left
from scripts import wood_joint_right_rail_integration as right
from scripts import wood_joint_wj06_outer_pair_probe as outer


def _connection(
    name: str,
    start: tuple[float, float, float],
    members: tuple[str, ...],
    *,
    diameter: float = 1.0,
    length: float = 38.1,
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        kind="screw",
        members=members,
        diameter=diameter,
        length=length,
        start=cq.Vector(*start),
        direction=cq.Vector(0.0, 0.0, 1.0),
    )


def test_trial_plan_binds_exact_four_duties_and_24_source_axes():
    inventory = left._canonical_inventory(None)
    plan = left.trial_plan(inventory)

    expected_duties = {
        "clip_horizontal_lower_left_1": [
            left.LOWER_RAIL_LEFT,
            left.SIDE_LEFT,
        ],
        "clip_horizontal_upper_left_1": [
            left.UPPER_RAIL_LEFT,
            left.SIDE_LEFT,
        ],
        "clip_horizontal_lower_left_2": [
            left.LOWER_RAIL_LEFT,
            left.PRINCIPAL_LEFT,
        ],
        "clip_horizontal_upper_left_2": [
            left.UPPER_RAIL_LEFT,
            left.PRINCIPAL_LEFT,
        ],
    }
    assert set(plan["duties"]) == set(expected_duties)
    assert len(plan["duties"]) == 4
    for station_id, hosts in expected_duties.items():
        source_row = next(
            row
            for row in inventory["legacy_duties"]
            if row["legacy_station_id"] == station_id
        )
        assert plan["duties"][station_id]["legacy_host_members"] == hosts
        assert source_row["legacy_host_members"] == hosts
        assert plan["duties"][station_id]["replaced_old_sds_axis_ids"] == [
            axis["axis_id"] for axis in source_row["legacy_sds_axes"]
        ]
        assert len(plan["duties"][station_id]["replaced_old_sds_axis_ids"]) == 6
    assert sum(
        len(row["replaced_old_sds_axis_ids"]) for row in plan["duties"].values()
    ) == 24
    assert plan["counts"]["fixed_panel_screw_axes_retained"] == 66
    assert plan["counts"]["starting_frame_bolt_arrangements_retained"] == 12


def test_stack_map_has_the_exact_16_named_axes_and_reversed_left_ownership():
    plan = left.trial_plan()
    rows = plan["candidate_stack_mapping"]
    expected = set()
    for source_station, target_station, family, stack_ids in (
        (
            "clip_horizontal_lower_right_1",
            "clip_horizontal_lower_left_2",
            "inner",
            ("lower_rail_1", "lower_rail_2", "lower_principal_1", "lower_principal_2"),
        ),
        (
            "clip_horizontal_upper_right_1",
            "clip_horizontal_upper_left_2",
            "inner",
            ("upper_rail_1", "upper_rail_2", "upper_principal_1", "upper_principal_2"),
        ),
        (
            "clip_horizontal_lower_right_2",
            "clip_horizontal_lower_left_1",
            "outer",
            ("lower_rail_1", "lower_rail_2", "lower_side_1", "lower_side_2"),
        ),
        (
            "clip_horizontal_upper_right_2",
            "clip_horizontal_upper_left_1",
            "outer",
            ("upper_rail_1", "upper_rail_2", "upper_side_1", "upper_side_2"),
        ),
    ):
        expected.update(
            (family, stack_id, source_station, target_station)
            for stack_id in stack_ids
        )
    actual = {
        (
            row["source_family"],
            row["source_stack_id"],
            row["source_station_id"],
            row["target_station_id"],
        )
        for row in rows
    }
    assert len(rows) == 16
    assert actual == expected


def test_outer_geometry_undoes_kerf_before_mirroring_points_and_solids():
    right_cleat = cq.Solid.makeBox(
        88.9, 88.9, 119.7, cq.Vector(1038.225, 1353.874134, 229.840968)
    )
    corrected = left.mirror_shape_x(right_cleat, undo_outer_kerf=True)
    naive = left.mirror_shape_x(right_cleat)
    corrected_bounds = corrected.BoundingBox()
    naive_bounds = naive.BoundingBox()

    assert (corrected_bounds.xmin, corrected_bounds.xmax) == pytest.approx(
        left.OUTER_EXPECTED_X_BOUNDS_MM
    )
    assert (naive_bounds.xmin, naive_bounds.xmax) == pytest.approx(
        (-1127.125, -1038.225)
    )
    assert left.mirror_point_x(cq.Vector(1081.675, 0, 0), undo_outer_kerf=True).x == pytest.approx(
        left.OUTER_EXPECTED_RAIL_AXIS_X_MM
    )
    assert left.mirror_point_x(cq.Vector(1038.225, 0, 0), undo_outer_kerf=True).x == pytest.approx(
        left.OUTER_EXPECTED_SIDE_START_X_MM
    )
    assert left.mirror_direction_x(cq.Vector(1, 0, 0)).toTuple() == pytest.approx(
        (-1, 0, 0)
    )


def test_outer_reflected_stacks_keep_exact_hosts_and_reversed_axis_direction():
    source_stack = outer.build_stacks()["lower_side_1"]
    stack = left._mirror_stack(
        source_stack,
        stack_key="left_service/test/clip_horizontal_lower_left_1/lower_side_1",
        member_map={
            outer.LOWER_CLEAT: left.OUTER_LOWER_CLEAT,
            outer.SIDE_HOST: left.SIDE_LEFT,
        },
        undo_outer_kerf=True,
    )

    assert stack.head_seat.center.x == pytest.approx(
        left.OUTER_EXPECTED_SIDE_START_X_MM
    )
    assert stack.direction.toTuple() == pytest.approx((-1, 0, 0))
    assert tuple(layer.body_id for layer in stack.layers) == (
        left.OUTER_LOWER_CLEAT,
        left.SIDE_LEFT,
    )
    assert stack.hardware.under_head_length_mm == pytest.approx(203.2)
    assert outer.SIDE_BOLT_MIN_LENGTH_MM == pytest.approx(198.628)


def test_left_inner_upper_is_full_stock_without_copying_g7_crosscut():
    right_geometry = SimpleNamespace(
        parts={
            outer.LOWER_CLEAT: cq.Solid.makeBox(
                88.9, 88.9, 119.7, cq.Vector(1038.225, 1353.874134, 229.840968)
            ),
            outer.UPPER_CLEAT: cq.Solid.makeBox(
                88.9, 88.9, 119.7, cq.Vector(1038.225, 1497.924134, 229.840968)
            ),
            left.wj04_inner.LOWER_CLEAT: cq.Solid.makeBox(
                88.9, 88.9, 119.7, cq.Vector(89.05, 1353.874134, 229.840968)
            ),
        }
    )
    cleats = left._left_cleat_shapes(right_geometry)
    upper = cleats[left.INNER_UPPER_CLEAT]
    n_axis = cq.Vector(*left.WJ04_TRIAL.frame.n_global)
    n_coordinates = [vertex.Center().dot(n_axis) for vertex in upper.Vertices()]
    x_coordinates = [vertex.Center().x for vertex in upper.Vertices()]

    assert max(n_coordinates) - min(n_coordinates) == pytest.approx(119.7)
    assert (min(x_coordinates), max(x_coordinates)) == pytest.approx(
        (-177.95, -89.05)
    )
    assert left.INNER_UPPER_FULL_ORIGIN_MM[2] == pytest.approx(229.840968)


def test_left_native_source_cutters_keep_left_datum_on_kerf_right_adapter():
    left_axis = _connection(
        "left_axis",
        (-1130.3, 4.0, 8.0),
        ("legacy_left_clip", left.SIDE_LEFT),
    )
    right_axis = _connection(
        "right_axis",
        (1127.125, 4.0, 8.0),
        ("legacy_right_clip", outer.SIDE_HOST),
    )
    native = SimpleNamespace(
        connections=lambda: (left_axis, right_axis),
        service_cutters=lambda: (),
        additional_machining_cutters=lambda: (),
    )
    current_right = _connection(
        "right_axis",
        (1127.125 - 3.175, 4.0, 8.0),
        ("legacy_right_clip", outer.SIDE_HOST),
    )
    source = SimpleNamespace(
        option=KERF_RIGHT,
        source=native,
        connections=lambda: (left_axis, current_right),
    )
    host_ids = frozenset({left.SIDE_LEFT, outer.SIDE_HOST})

    cutters = right.source_native_cutters_by_host(source, host_ids)
    audit = right._source_axis_datum_audit(
        source, frozenset({"left_axis", "right_axis"}), host_ids
    )

    assert cutters[left.SIDE_LEFT]["left_axis"].BoundingBox().xmin == pytest.approx(
        -1130.8
    )
    assert cutters[outer.SIDE_HOST]["right_axis"].BoundingBox().xmin == pytest.approx(
        1123.45
    )
    left_record = audit["left_axis"]
    assert left_record["shared_host_transforms"][left.SIDE_LEFT][
        "native_replay_member_transform"
    ] == "identity"
    assert left_record["shared_host_native_replay_starts_xyz_mm"][left.SIDE_LEFT] == pytest.approx(
        [-1130.3, 4, 8]
    )


def test_panel_purchase_cutters_use_pinned_63p5mm_length_and_left_hosts():
    inventory = left._canonical_inventory(None)
    rows = inventory["fixed_panel_kicker_screws"]
    connections = []
    left_axis_id = None
    left_host = None
    for index, row in enumerate(rows):
        receiver = row["candidate_finished_receiver_member"]
        if receiver in left.SOURCE_HOSTS and left_axis_id is None:
            left_axis_id = row["axis_id"]
            left_host = receiver
        connections.append(
            _connection(
                row["axis_id"],
                (float(index), 2.0, 100.0),
                (row["panel_member"], receiver),
                diameter=row["source_occupied_diameter_mm"],
                length=row["source_occupied_length_mm"],
            )
        )
    assert left_axis_id is not None and left_host is not None
    source = SimpleNamespace(connections=lambda: tuple(connections))

    purchase = right.candidate_panel_purchase_cutters_by_host(
        source, inventory, left.SOURCE_HOSTS
    )

    cutter = purchase[left_host][f"panel_purchase/{left_axis_id}"]
    assert cutter.BoundingBox().zmin == pytest.approx(100.0)
    assert cutter.BoundingBox().zlen == pytest.approx(63.5)
    assert sum(len(cutters) for cutters in purchase.values()) > 0


def test_caller_inventory_must_equal_canonical_pinned_inventory():
    inventory = left._canonical_inventory(None)
    altered = json.loads(json.dumps(inventory))
    altered["legacy_duties"][0]["legacy_host_members"].reverse()

    with pytest.raises(ValueError, match="caller inventory content differs"):
        left._canonical_inventory(altered)


def test_input_fingerprint_covers_all_right_integration_inputs():
    right_inputs = set(right._source_inputs_sha256())
    left_inputs = set(left._source_inputs_sha256())

    assert right_inputs <= left_inputs
    assert "docs/wood-joints-mvp/ordinary-hardware-basis.md" in left_inputs
    assert (
        "docs/wood-joints-mvp/hypotheses/ordinary-hardware-basis.md"
        not in left_inputs
    )
