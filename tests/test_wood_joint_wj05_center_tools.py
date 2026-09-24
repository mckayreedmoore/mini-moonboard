"""Focused geometry checks for the WJ-05 upper-center tool adapter."""

from __future__ import annotations

from types import SimpleNamespace

import cadquery as cq
import pytest

from scripts import wood_joint_wj05_center_tools as center_tools


def _station(side: str) -> tuple[dict, dict[str, cq.Shape]]:
    sign = -1 if side == "left" else 1
    station_id = f"center_principal_header_{side}_2"
    axis = {
        "axis_id": station_id,
        "side": side,
        "origin_global_xyz_mm": [sign * 151.0, -139.4, 238.9],
        "direction_global_xyz": [0.0, 0.0, 1.0],
    }
    head_outer_z = 238.9 - 1.651 - center_tools.center_probe.HEAD_HEIGHT_MM
    head_bearing_z = head_outer_z + center_tools.center_probe.HEAD_HEIGHT_MM
    head = cq.Solid.makeCylinder(
        center_tools.center_probe.HEAD_DIAMETER_MM / 2,
        center_tools.center_probe.HEAD_HEIGHT_MM,
        cq.Vector(sign * 151.0, -139.4, head_outer_z),
        cq.Vector(0, 0, 1),
    )
    shaft = cq.Solid.makeCylinder(
        center_tools.center_probe.BOLT_DIAMETER_MM / 2,
        112.0,
        cq.Vector(sign * 151.0, -139.4, head_bearing_z),
        cq.Vector(0, 0, 1),
    )
    far = 339.8156
    nut_washer = cq.Solid.makeCylinder(
        center_tools.center_probe.WASHER_DIAMETER_MM / 2,
        center_tools.center_probe.WASHER_THICKNESS_MM,
        cq.Vector(sign * 151.0, -139.4, far),
        cq.Vector(0, 0, 1),
    )
    nut = cq.Solid.makeCylinder(
        center_tools.center_probe.NUT_DIAMETER_MM / 2,
        center_tools.center_probe.NUT_HEIGHT_MM,
        cq.Vector(
            sign * 151.0,
            -139.4,
            far + center_tools.center_probe.WASHER_THICKNESS_MM,
        ),
        cq.Vector(0, 0, 1),
    )
    head_washer = cq.Solid.makeCylinder(
        center_tools.center_probe.WASHER_DIAMETER_MM / 2,
        center_tools.center_probe.WASHER_THICKNESS_MM,
        cq.Vector(sign * 151.0, -139.4, head_bearing_z),
        cq.Vector(0, 0, 1),
    )
    return axis, {
        "head": head,
        "shaft": shaft,
        "head_washer": head_washer,
        "nut_washer": nut_washer,
        "nut": nut,
    }


@pytest.mark.parametrize("side,heading_x", (("right", -1), ("left", 1)))
def test_socket_bearing_plane_extension_stack_and_mirrored_heading(side, heading_x):
    axis, installed = _station(side)
    shapes, datum = center_tools._station_tool_shapes(
        axis, installed["head"], installed["nut"]
    )

    bearing = datum["head_bearing_face_xyz_mm"][2]
    outer = datum["head_outer_face_xyz_mm"][2]
    socket = shapes["socket_bearing_face_seated_occupancy"].BoundingBox()
    socket_body = shapes["socket_product_body"].BoundingBox()
    socket_barrel = shapes["socket_barrel_beyond_head"].BoundingBox()
    extension = shapes["extension_body"].BoundingBox()
    ratchet = shapes["ratchet_inline_body"].BoundingBox()

    assert datum["inward_handle_heading_xyz"] == [heading_x, 0, 0]
    assert bearing == pytest.approx(237.249)
    assert outer == pytest.approx(232.4738)
    assert socket.zmax == pytest.approx(bearing)
    assert socket.zmin == pytest.approx(bearing - center_tools.SOCKET_LENGTH_MM)
    assert socket_body.zmax == pytest.approx(bearing)
    assert socket_body.zmin == pytest.approx(bearing - center_tools.SOCKET_LENGTH_MM)
    assert socket_barrel.zmax == pytest.approx(outer)
    assert socket_barrel.zmin == pytest.approx(bearing - center_tools.SOCKET_LENGTH_MM)
    assert extension.zmax == pytest.approx(socket_body.zmin)
    assert extension.zmin == pytest.approx(
        extension.zmax - center_tools.EXTENSION_LENGTH_MM
    )
    assert ratchet.zmax == pytest.approx(extension.zmin)
    assert ratchet.zmin == pytest.approx(
        ratchet.zmax - center_tools.RATCHET_HEAD_THICKNESS_MM
    )
    assert (ratchet.xmax - ratchet.xmin) == pytest.approx(
        center_tools.RATCHET_OVERALL_LENGTH_MM
    )
    assert datum["socket_external_occupancy"][
        "catalog_oal_already_includes_head_depth"
    ] is True
    assert datum["extension_external_envelope"][
        "socket_to_extension_square_drive_engagement_mm"
    ] is None
    assert datum["extension_external_envelope"][
        "extension_to_ratchet_square_drive_engagement_mm"
    ] is None
    assert shapes["socket_bearing_face_seated_occupancy"].isValid()
    assert shapes["extension_body"].isValid()
    assert shapes["ratchet_inline_body"].isValid()


def test_counterhold_is_slab_centered_within_the_installed_nut_hex_height():
    axis, installed = _station("right")
    _shapes, datum = center_tools._station_tool_shapes(
        axis, installed["head"], installed["nut"]
    )

    seating = datum["counterhold_seating"]
    target_low, target_high = seating["target_hex_axial_bounds_mm"]
    wrench_low, wrench_high = seating["wrench_slab_axial_bounds_mm"]
    assert seating["slab_centered_within_target_hex_height"] is True
    assert wrench_low > target_low
    assert wrench_high < target_high
    assert wrench_high - wrench_low == pytest.approx(3.0)
    assert (wrench_low + wrench_high) / 2 == pytest.approx(
        (target_low + target_high) / 2
    )


def _synthetic_legacy_inventory_and_model():
    target_duties = {
        "clip_split_header_center_left": "header_center",
        "clip_split_header_center_right": "header_center",
        "clip_split_base_center_left": "base_center",
        "clip_split_base_center_right": "base_center",
    }
    duty_rows = []
    connector_parts = []
    screw_connections = []
    names = list(target_duties)
    names.extend(f"clip_retained_{index:02d}" for index in range(20))
    for duty_index, duty_id in enumerate(names):
        family = target_duties.get(duty_id, "top_outer")
        axes = []
        for axis_index in range(6):
            axis_id = f"{duty_id}_sds_{axis_index + 1}"
            origin = cq.Vector(duty_index * 100.0, axis_index * 20.0, 0.0)
            direction = cq.Vector(0, 0, 1)
            members = [duty_id, f"host_{duty_index:02d}"]
            axes.append(
                {
                    "axis_id": axis_id,
                    "members": members,
                    "origin_global_xyz_mm": list(origin.toTuple()),
                    "axis_global_xyz": list(direction.toTuple()),
                    "source_occupied_length_mm": 38.1,
                    "source_occupied_diameter_mm": 6.35,
                }
            )
            screw_connections.append(
                SimpleNamespace(
                    name=axis_id,
                    kind="screw",
                    start=origin,
                    direction=direction,
                    length=38.1,
                    diameter=6.35,
                )
            )
        duty_rows.append(
            {
                "legacy_station_id": duty_id,
                "legacy_family": family,
                "legacy_sds_axes": axes,
            }
        )
        connector_parts.append(
            SimpleNamespace(
                name=duty_id,
                shape=cq.Solid.makeBox(
                    20.0,
                    20.0,
                    4.0,
                    cq.Vector(duty_index * 100.0, 0, 50),
                ),
            )
        )
    inventory = {"legacy_duties": duty_rows}
    model = SimpleNamespace(
        parts=lambda: connector_parts,
        connections=lambda: screw_connections,
    )
    return inventory, model


def test_retained_legacy_inventory_excludes_only_four_center_duties():
    inventory, model = _synthetic_legacy_inventory_and_model()

    connectors, sds_axes, summary = center_tools._retained_legacy_hardware(
        model, inventory
    )

    assert len(connectors) == 20
    assert len(sds_axes) == 120
    assert not center_tools.REPLACED_CENTER_LEGACY_DUTIES.intersection(connectors)
    assert summary["excluded_replaced_center_sds_axis_count"] == 24
    assert summary["retained_connector_body_count"] == 20
    assert summary["retained_sds_axis_count"] == 120
    assert all(shape.isValid() for shape in connectors.values())
    assert all(shape.isValid() for shape in sds_axes.values())


def test_retained_legacy_inventory_fails_closed_on_missing_source_axis():
    inventory, model = _synthetic_legacy_inventory_and_model()
    connections = model.connections()
    model.connections = lambda: connections[:-1]

    with pytest.raises(ValueError, match="legacy SDS axis identities changed"):
        center_tools._retained_legacy_hardware(model, inventory)


def test_report_screens_obstacles_keeps_target_exclusions_narrow_and_bounds_claims():
    axes = {}
    installed = {}
    candidate_hardware = {}
    for side in ("left", "right"):
        axis, roles = _station(side)
        axes[axis["axis_id"]] = axis
        installed[axis["axis_id"]] = roles
        candidate_hardware.update(
            {
                f"{axis['axis_id']}/{role}": shape
                for role, shape in roles.items()
            }
        )
    protected_blocker = cq.Solid.makeBox(
        12.0,
        12.0,
        8.0,
        cq.Vector(40.0, -145.4, 122.0),
    )
    geometry = center_tools.MaterializedCenterToolGeometry(
        trial_id=center_tools.center_probe.TRIAL_ID,
        source_fingerprints_sha256={"synthetic": "source"},
        tool_source_fingerprints_sha256={"synthetic": "tool"},
        station_axes=axes,
        installed_by_axis=installed,
        obstacle_groups={
            "center_trial_timber_conservative": {},
            "protected": {"test_wire": protected_blocker},
            "fixed_66_panel_kicker_axes": {},
            "retained_frame_bolt_components_and_axes": {},
            "active_wj05_backer_installed_hardware": {},
            "retained_legacy_connector_bodies": {},
            "retained_legacy_sds_axes": {},
            "candidate_installed_hardware": candidate_hardware,
        },
        retained_legacy_inventory={"synthetic": True},
        floor_z_mm=0.0,
    )

    result = center_tools.build_tool_report(geometry)
    right = result["stations"]["center_principal_header_right_2"]
    assembly = right["operations"]["seated_socket_extension_and_inline_ratchet"]
    counterhold = right["operations"][
        "nut_side_counterhold_seated_within_hex_height"
    ]

    assert "protected/test_wire" in assembly["external_envelope_hits_mm3"][
        "ratchet_inline_body"
    ]
    assert assembly["excluded_target_obstacle_ids"] == [
        "candidate_installed_hardware/center_principal_header_right_2/head",
        "candidate_installed_hardware/center_principal_header_right_2/shaft",
    ]
    assert counterhold["excluded_target_obstacle_ids"] == [
        "candidate_installed_hardware/center_principal_header_right_2/nut",
        "candidate_installed_hardware/center_principal_header_right_2/shaft",
    ]
    assert assembly["physical_access_established"] is False
    assert result["claims"]["tool_selected"] is False
    assert result["release_flags"]["fabrication_released"] is False
    assert set(result["stations"]) == set(center_tools.STATION_IDS)
    assert result["tool_candidates"]["ratchet"]["stroke_cases_degrees"] == [-5.0, 5.0]
    assert result["screen_basis"]["socket_ratchet_drive_engagement"].startswith(
        "Catalog parts have nominally matching 1/4-in square drives."
    )
    assert "Raw source-derived frame timber" in result["screen_basis"][
        "timber_obstacle_status"
    ]
    for station in result["stations"].values():
        operations = station["operations"]
        assert "ratchet_bounded_stroke_-5_degrees" in operations
        assert "ratchet_bounded_stroke_+5_degrees" in operations
        assert operations["seated_socket_extension_and_inline_ratchet"][
            "floor_screen"
        ]["ratchet_inline_body"]["below_analytical_floor"] is False
