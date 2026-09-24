"""Regression coverage for WJ-05 seated Ko-ken socket datums."""

import pytest

from mini_moonboard.wood_joint_wj05_socket import (
    KOKEN_SOCKET_H1_MM,
    KOKEN_SOCKET_LENGTH_MM,
    KOKEN_SOCKET_OUTSIDE_DIAMETER_MM,
    KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM,
    KOKEN_SOCKET_WORKING_END_DIAMETER_MM,
    seated_koken_3305a_7_16_envelope,
    wj05_socket_occupancy_intent,
)
from scripts.wood_joint_wj05_receiver_audit import _backer_station_shapes
from scripts.wood_joints_wj05_center_backer_transfer_probe import (
    BACKER_BOLT_STATIONS,
    _source_and_candidate,
)

STATIONS_XY_MM = (
    (-35.0, -97.0),
    (-35.0, -63.0),
    (41.0, -98.0),
    (25.0, -76.0),
)
TOP_NUT_BEARING_FACE_Z_MM = 283.096
TOP_NUT_OUTER_FACE_Z_MM = 288.8364
BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM = 4.968
BOTTOM_HEAD_OUTER_FACE_Z_MM = 0.1928
HEAD_MAX_CORNER_DIAMETER_MM = 12.827


def test_catalog_envelope_uses_official_koken_dimensions():
    assert KOKEN_SOCKET_LENGTH_MM == pytest.approx(55.0)
    assert KOKEN_SOCKET_OUTSIDE_DIAMETER_MM == pytest.approx(17.2)
    assert KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM == pytest.approx(41.5)
    assert KOKEN_SOCKET_H1_MM == pytest.approx(12.0)
    assert KOKEN_SOCKET_WORKING_END_DIAMETER_MM == pytest.approx(16.0)


@pytest.mark.parametrize("center_xy_mm", STATIONS_XY_MM)
def test_top_socket_starts_at_nut_bearing_face_and_surrounds_full_hex_height(
    center_xy_mm,
):
    socket = seated_koken_3305a_7_16_envelope(
        center_xy_mm,
        TOP_NUT_BEARING_FACE_Z_MM,
        outward_z=1,
        target_bounds_z_mm=(
            TOP_NUT_BEARING_FACE_Z_MM,
            TOP_NUT_OUTER_FACE_Z_MM,
        ),
    )

    assert socket.center_xy_mm == center_xy_mm
    assert socket.axial_bounds_mm == pytest.approx(
        (TOP_NUT_BEARING_FACE_Z_MM, TOP_NUT_BEARING_FACE_Z_MM + 55.0)
    )
    assert socket.approach_endpoint_bounds_mm == pytest.approx(
        (TOP_NUT_OUTER_FACE_Z_MM, TOP_NUT_OUTER_FACE_Z_MM + 55.0)
    )
    assert socket.approach_sweep_bounds_mm == pytest.approx(
        (TOP_NUT_BEARING_FACE_Z_MM, TOP_NUT_OUTER_FACE_Z_MM + 55.0)
    )
    assert socket.length_mm == pytest.approx(KOKEN_SOCKET_LENGTH_MM)
    assert socket.outside_diameter_mm == pytest.approx(
        KOKEN_SOCKET_OUTSIDE_DIAMETER_MM
    )
    assert socket.stud_clearance_depth_mm == pytest.approx(
        KOKEN_SOCKET_STUD_CLEARANCE_DEPTH_MM
    )
    assert socket.stud_clearance_depth_mm == pytest.approx(41.5)
    engagement_overlap = min(
        socket.axial_bounds_mm[1], TOP_NUT_OUTER_FACE_Z_MM
    ) - max(socket.axial_bounds_mm[0], TOP_NUT_BEARING_FACE_Z_MM)
    assert engagement_overlap == pytest.approx(
        TOP_NUT_OUTER_FACE_Z_MM - TOP_NUT_BEARING_FACE_Z_MM
    )
    assert socket.outside_diameter_mm > HEAD_MAX_CORNER_DIAMETER_MM
    intent = wj05_socket_occupancy_intent(
        socket,
        target_component="top_nut",
        target_bounds_z_mm=(TOP_NUT_BEARING_FACE_Z_MM, TOP_NUT_OUTER_FACE_Z_MM),
        target_max_corner_diameter_mm=HEAD_MAX_CORNER_DIAMETER_MM,
    )
    assert intent["classification"] == (
        "intentional_socket_fastener_occupancy_not_obstacle_clash"
    )
    assert intent["external_envelope_axial_overlap_mm"] == pytest.approx(
        TOP_NUT_OUTER_FACE_Z_MM - TOP_NUT_BEARING_FACE_Z_MM
    )
    assert intent["socket_outer_envelope_spans_full_target_hex_height"] is True
    assert intent["internal_12_point_profile_and_engagement_fit"] == (
        "not_modeled_or_assessed"
    )


@pytest.mark.parametrize("center_xy_mm", STATIONS_XY_MM)
def test_bottom_socket_starts_at_underhead_face_and_surrounds_full_hex_height(
    center_xy_mm,
):
    socket = seated_koken_3305a_7_16_envelope(
        center_xy_mm,
        BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM,
        outward_z=-1,
        target_bounds_z_mm=(
            BOTTOM_HEAD_OUTER_FACE_Z_MM,
            BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM,
        ),
    )

    assert socket.center_xy_mm == center_xy_mm
    assert socket.axial_bounds_mm == pytest.approx(
        (BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM - 55.0, BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM)
    )
    assert socket.approach_endpoint_bounds_mm == pytest.approx(
        (BOTTOM_HEAD_OUTER_FACE_Z_MM - 55.0, BOTTOM_HEAD_OUTER_FACE_Z_MM)
    )
    assert socket.approach_sweep_bounds_mm == pytest.approx(
        (BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM - 55.0 - (
            BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM - BOTTOM_HEAD_OUTER_FACE_Z_MM
        ), BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM)
    )
    engagement_overlap = min(
        socket.axial_bounds_mm[1], BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM
    ) - max(socket.axial_bounds_mm[0], BOTTOM_HEAD_OUTER_FACE_Z_MM)
    assert engagement_overlap == pytest.approx(
        BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM - BOTTOM_HEAD_OUTER_FACE_Z_MM
    )
    assert socket.outside_diameter_mm > HEAD_MAX_CORNER_DIAMETER_MM
    intent = wj05_socket_occupancy_intent(
        socket,
        target_component="bottom_bolt_head",
        target_bounds_z_mm=(
            BOTTOM_HEAD_OUTER_FACE_Z_MM,
            BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM,
        ),
        target_max_corner_diameter_mm=HEAD_MAX_CORNER_DIAMETER_MM,
    )
    assert intent["external_envelope_axial_overlap_mm"] == pytest.approx(
        BOTTOM_HEAD_UNDERHEAD_FACE_Z_MM - BOTTOM_HEAD_OUTER_FACE_Z_MM
    )
    assert intent["socket_outer_envelope_spans_full_target_hex_height"] is True


def test_socket_requires_outward_axial_direction():
    with pytest.raises(ValueError, match="outward_z must be -1 or 1"):
        seated_koken_3305a_7_16_envelope(
            (0.0, 0.0),
            0.0,
            outward_z=0,
            target_bounds_z_mm=(0.0, 1.0),
        )


@pytest.fixture(scope="module")
def producer_station_shapes():
    probe_tools = _source_and_candidate()[7]
    audit_tools = {}
    for side, stations in BACKER_BOLT_STATIONS.items():
        for index, (x_mm, y_mm) in enumerate(stations, start=1):
            station_id = f"backer_header_{side}_{index}"
            audit_tools[station_id] = _backer_station_shapes(x_mm, y_mm)
    return probe_tools, audit_tools


def _z_bounds(shape):
    box = shape.BoundingBox()
    return box.zmin, box.zmax


def _xy_bounds(shape):
    box = shape.BoundingBox()
    return box.xmin, box.xmax, box.ymin, box.ymax


def test_both_wj05_producers_use_seated_and_complete_approach_sweep(
    producer_station_shapes,
):
    probe_tools, audit_tools = producer_station_shapes
    expected_top = {
        "approach_endpoint": (288.8364, 343.8364),
        "seated": (283.096, 338.096),
        "approach_sweep": (283.096, 343.8364),
    }
    expected_bottom = {
        "approach_endpoint": (-54.8072, 0.1928),
        "seated": (-50.032, 4.968),
        "approach_sweep": (-54.8072, 4.968),
    }

    for side, stations in BACKER_BOLT_STATIONS.items():
        for index, (x_mm, y_mm) in enumerate(stations, start=1):
            station_id = f"backer_header_{side}_{index}"
            probe = probe_tools[station_id]
            audit = audit_tools[station_id]
            top_shapes = (
                (probe["top"], audit["top_tool"], "approach_endpoint"),
                (probe["top_seated"], audit["top_tool_seated"], "seated"),
                (
                    probe["top_approach_sweep"],
                    audit["top_tool_approach_sweep"],
                    "approach_sweep",
                ),
            )
            bottom_shapes = (
                (probe["bottom"], audit["bottom_tool"], "approach_endpoint"),
                (probe["bottom_seated"], audit["bottom_tool_seated"], "seated"),
                (
                    probe["bottom_approach_sweep"],
                    audit["bottom_tool_approach_sweep"],
                    "approach_sweep",
                ),
            )
            for shapes, expected_positions in (
                (top_shapes, expected_top),
                (bottom_shapes, expected_bottom),
            ):
                for probe_shape, audit_shape, position in shapes:
                    expected_z = expected_positions[position]
                    expected_xy = (
                        x_mm - KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2,
                        x_mm + KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2,
                        y_mm - KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2,
                        y_mm + KOKEN_SOCKET_OUTSIDE_DIAMETER_MM / 2,
                    )
                    assert _z_bounds(probe_shape) == pytest.approx(expected_z)
                    assert _z_bounds(audit_shape) == pytest.approx(expected_z)
                    assert _xy_bounds(probe_shape) == pytest.approx(expected_xy)
                    assert _xy_bounds(audit_shape) == pytest.approx(expected_xy)
