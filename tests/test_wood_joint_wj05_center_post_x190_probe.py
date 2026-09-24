"""Source-independent checks for the isolated WJ-05 ±190 center variant."""

from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj05_center_node_probe as center_probe
from scripts import wood_joint_wj05_center_offset_adapter as adapter
from scripts import wood_joint_wj05_center_post_x190_probe as variant


def _base_axes() -> list[dict]:
    return [
        axis
        for side in center_probe.SIDES
        for axis in (
            center_probe._upper_fastener_axes(side)
            + center_probe._lower_fastener_axes(side)
        )
    ]


def test_adapter_moves_only_the_eight_lower_axes_and_preserves_source_records():
    source = _base_axes()
    original = [dict(axis, origin_global_xyz_mm=list(axis["origin_global_xyz_mm"])) for axis in source]

    moved, records = adapter.shift_lower_axes_outward(source)

    by_id = {axis["axis_id"]: axis for axis in moved}
    source_by_id = {axis["axis_id"]: axis for axis in source}
    record_by_id = {row["axis_id"]: row for row in records}
    assert len(moved) == 16
    assert len(records) == 8
    assert set(record_by_id) == adapter.MOVED_AXIS_IDS
    for axis_id in adapter.MOVED_AXIS_IDS:
        side = "left" if "_left_" in axis_id else "right"
        sign = -1 if side == "left" else 1
        assert by_id[axis_id]["origin_global_xyz_mm"][0] == pytest.approx(
            source_by_id[axis_id]["origin_global_xyz_mm"][0] + sign * 10.0
        )
        assert record_by_id[axis_id]["delta_x_mm"] == sign * 10.0
    for axis_id in adapter.FIXED_AXIS_IDS:
        assert by_id[axis_id] == source_by_id[axis_id]
    assert source == original
    assert adapter.TRIAL_ID == "wj05-center-node-posts-x190-outward-v1"


def test_adapter_fails_closed_when_any_lower_or_upper_axis_is_missing():
    axes = _base_axes()
    axes.pop()

    with pytest.raises(ValueError, match="axis identities changed"):
        adapter.shift_lower_axes_outward(axes)


def test_adapter_moves_two_posts_and_two_lower_cleats_only():
    parts = {
        "base_post_center_right": cq.Solid.makeBox(38.1, 139.7, 238.9, cq.Vector(160.95, -175.7, 0)),
        "base_post_center_left": cq.Solid.makeBox(38.1, 139.7, 238.9, cq.Vector(-199.05, -175.7, 0)),
        "center_post_cleat_right": cq.Solid.makeBox(88.9, 88.9, 128.9, cq.Vector(199.05, -175.7, 110)),
        "center_post_cleat_left": cq.Solid.makeBox(88.9, 88.9, 128.9, cq.Vector(-287.95, -175.7, 110)),
        "center_principal_cleat_right": cq.Solid.makeBox(88.9, 88.9, 82, cq.Vector(89.05, -150, 277)),
        "center_principal_cleat_left": cq.Solid.makeBox(88.9, 88.9, 82, cq.Vector(-177.95, -150, 277)),
        "base_header": cq.Solid.makeBox(600, 139.7, 38.1, cq.Vector(-300, -175.7, 71.9)),
    }
    source_bounds = {name: _bounds(shape) for name, shape in parts.items()}

    moved, records = adapter.shift_lower_members_outward(parts)

    assert len(records) == 4
    assert _center_x(moved["base_post_center_right"]) == pytest.approx(190.0)
    assert _center_x(moved["base_post_center_left"]) == pytest.approx(-190.0)
    assert _bounds(moved["center_post_cleat_right"])[0] == pytest.approx(209.05)
    assert _bounds(moved["center_post_cleat_left"])[1] == pytest.approx(-209.05)
    for name in adapter.FIXED_CLEAT_IDS | {"base_header"}:
        assert _bounds(moved[name]) == source_bounds[name]
    assert _bounds(parts["base_post_center_right"]) == source_bounds[
        "base_post_center_right"
    ]


def test_member_adapter_fails_closed_when_a_fixed_upper_cleat_is_missing():
    parts = {
        name: cq.Solid.makeBox(10, 10, 10, cq.Vector(0, 0, 0))
        for name in adapter.MOVED_MEMBER_IDS | adapter.FIXED_CLEAT_IDS
        if name != "center_principal_cleat_left"
    }

    with pytest.raises(ValueError, match="members missing"):
        adapter.shift_lower_members_outward(parts)


def test_lower_cleat_header_contact_uses_cleat_top_and_header_bottom_faces():
    parts = {
        "base_header": cq.Solid.makeBox(
            600.0, 139.7, 38.1, cq.Vector(-300.0, -175.7, 238.9)
        ),
        "base_post_center_left": cq.Solid.makeBox(
            38.1, 139.7, 238.9, cq.Vector(-209.05, -175.7, 0.0)
        ),
        "base_post_center_right": cq.Solid.makeBox(
            38.1, 139.7, 238.9, cq.Vector(170.95, -175.7, 0.0)
        ),
        "center_post_cleat_left": cq.Solid.makeBox(
            88.9, 88.9, 128.9, cq.Vector(-287.95, -175.7, 110.0)
        ),
        "center_post_cleat_right": cq.Solid.makeBox(
            88.9, 88.9, 128.9, cq.Vector(199.05, -175.7, 110.0)
        ),
        "base_principal_center_left": cq.Solid.makeBox(
            38.1, 139.7, 200.0, cq.Vector(-89.05, -175.7, 238.9)
        ),
        "base_principal_center_right": cq.Solid.makeBox(
            38.1, 139.7, 200.0, cq.Vector(50.95, -175.7, 238.9)
        ),
        "center_principal_cleat_left": cq.Solid.makeBox(
            88.9, 88.9, 82.0, cq.Vector(-177.95, -150.0, 277.0)
        ),
        "center_principal_cleat_right": cq.Solid.makeBox(
            88.9, 88.9, 82.0, cq.Vector(89.05, -150.0, 277.0)
        ),
    }

    contacts = variant._contact_geometry(SimpleNamespace(parts=parts))

    for side in ("left", "right"):
        contact = contacts[side]["lower_cleat_to_header"]
        assert contact["source_face_coordinate_mm"] == pytest.approx(238.9)
        assert contact["mate_face_coordinate_mm"] == pytest.approx(238.9)
        assert contact["faces_coincident"] is True
        assert contact["gross_projected_contact_area_mm2"] > 0.0


def test_mechanics_implications_keep_post_support_and_bolt_group_spacing_distinct():
    implications = adapter.geometry_implications()

    assert implications["post_center_x_mm"]["trial"] == [-190.0, 190.0]
    assert implications["center_post_support_center_spacing_mm"] == {
        "source": 360.0,
        "trial": 380.0,
        "change": 20.0,
    }
    assert implications["lower_header_bolt_group_center_spacing_mm"] == {
        "source": 488.0,
        "trial": 508.0,
        "change": 20.0,
    }
    assert implications["upper_cleat_post_projected_overlap_mm"] == {
        "source": 17.0,
        "trial": 7.0,
        "change": -10.0,
    }


@pytest.mark.parametrize(
    "side,expected_heading,expected_stroke",
    (("left", -1.0, -5.0), ("right", 1.0, 5.0)),
)
def test_tool_route_uses_outward_counterhold_and_backer_avoiding_stroke(
    side, expected_heading, expected_stroke
):
    axis = {
        "axis_id": f"center_principal_header_{side}_2",
        "side": side,
        "origin_global_xyz_mm": [-151.0 if side == "left" else 151.0, -139.4, 238.9],
        "direction_global_xyz": [0.0, 0.0, 1.0],
    }
    nut = cq.Solid.makeCylinder(6.4135, 5.7404, cq.Vector(*axis["origin_global_xyz_mm"]), cq.Vector(0, 0, 1))

    envelope, heading = variant._outward_counterhold(axis, nut)
    bounds = envelope.BoundingBox()
    origin_x = axis["origin_global_xyz_mm"][0]

    assert heading.x == expected_heading
    assert variant.preferred_stroke_degrees(side) == expected_stroke
    if side == "right":
        assert bounds.xmax > origin_x + 70.0
        assert bounds.xmin >= origin_x - 11.0
    else:
        assert bounds.xmin < origin_x - 70.0
        assert bounds.xmax <= origin_x + 11.0
    assert envelope.isValid()


@pytest.mark.parametrize("side,selected,alternate", (("left", -5.0, 5.0), ("right", 5.0, -5.0)))
def test_preferred_route_status_ignores_rejected_alternate_stroke(side, selected, alternate):
    selected_name = f"ratchet_bounded_stroke_{selected:+g}_degrees"
    alternate_name = f"ratchet_bounded_stroke_{alternate:+g}_degrees"
    operations = {
        name: {"external_envelope_clear": True}
        for name in variant.preferred_route_operation_ids(side)
    }
    operations[alternate_name] = {"external_envelope_clear": False}

    status = variant.preferred_route_status(operations, side)

    assert status["clear"] is True
    assert status["alternate_stroke_gates_preferred_route"] is False
    assert selected_name in status["checked_operations"]
    assert "counterhold_vs_static_head_side_tools" in status["checked_operations"]
    assert f"counterhold_vs_ratchet_stroke_{selected:+g}_degrees" in status[
        "checked_operations"
    ]


def test_synthetic_catalog_route_reports_simultaneous_tools_and_selected_sector():
    axes = [
        axis
        for side in center_probe.SIDES
        for axis in (
            center_probe._upper_fastener_axes(side)
            + center_probe._lower_fastener_axes(side)
        )
    ]
    axes, _records = adapter.shift_lower_axes_outward(axes)
    geometry = SimpleNamespace(
        axes=axes,
        fastener_shapes={
            axis["axis_id"]: center_probe._fastener_shapes(axis) for axis in axes
        },
        finished_parts={},
        protected_shapes={},
        fixed_axes={},
        frame_shapes={},
        backer_installed_shapes={},
        retained_legacy_connectors={},
        retained_legacy_sds={},
    )

    routes = variant._build_catalog_tool_route(geometry)

    for side, stroke, heading in (("left", -5.0, -1.0), ("right", 5.0, 1.0)):
        station_id = f"center_principal_header_{side}_2"
        route = routes[station_id]
        operations = route["operations"]
        assert route["tool_pose_and_seating"]["counterhold_heading_xyz"] == [
            heading,
            0.0,
            0.0,
        ]
        assert route["preferred_route_status"]["clear"] is all(
            operations[name]["external_envelope_clear"]
            for name in route["preferred_route_status"]["checked_operations"]
        )
        assert "counterhold_vs_static_head_side_tools" in operations
        assert f"counterhold_vs_ratchet_stroke_{stroke:+g}_degrees" in operations
        assert route["operations"]["selected_backer_avoiding_stroke"][
            "degrees"
        ] == stroke
        alternate = 5.0 if side == "left" else -5.0
        assert f"ratchet_bounded_stroke_{alternate:+g}_degrees" in operations
        assert route["preferred_route_status"][
            "alternate_stroke_gates_preferred_route"
        ] is False


def _bounds(shape: cq.Shape) -> list[float]:
    box = shape.BoundingBox()
    return [box.xmin, box.xmax, box.ymin, box.ymax, box.zmin, box.zmax]


def _center_x(shape: cq.Shape) -> float:
    bounds = shape.BoundingBox()
    return (bounds.xmin + bounds.xmax) / 2
