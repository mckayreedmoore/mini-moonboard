from __future__ import annotations

import hashlib
import math

import cadquery as cq
import pytest
from OCP.gp import gp_Trsf
from surfaces import (
    SurfaceError,
    _build_stock_frame,
    _to_global_point,
    _to_stock_point,
    _validate_frame,
    canonical_bytes,
    features_for_shape,
    verify_canonical_file,
    verify_pin_document,
)


def rigid_transform(
    x_axis: tuple[float, float, float],
    y_axis: tuple[float, float, float],
    z_axis: tuple[float, float, float],
    origin: tuple[float, float, float],
) -> cq.Matrix:
    transform = gp_Trsf()
    transform.SetValues(
        x_axis[0],
        y_axis[0],
        z_axis[0],
        origin[0],
        x_axis[1],
        y_axis[1],
        z_axis[1],
        origin[1],
        x_axis[2],
        y_axis[2],
        z_axis[2],
        origin[2],
    )
    return cq.Matrix(transform)


def oblique_fixture() -> tuple[cq.Solid, dict[str, object]]:
    g = (math.sqrt(0.5), math.sqrt(0.5), 0.0)
    q = (-math.sqrt(0.5), math.sqrt(0.5), 0.0)
    r = (0.0, 0.0, 1.0)
    origin = (120.0, -40.0, 23.0)
    stock = cq.Solid.makeBox(32.0, 20.0, 12.0)
    bore = cq.Solid.makeCylinder(
        2.1, 32.0, cq.Vector(0.0, 10.0, 5.0), cq.Vector(1.0, 0.0, 0.0)
    )
    seat = cq.Solid.makeBox(10.0, 6.0, 4.0, cq.Vector(8.0, 6.0, 8.0))
    taper = (
        cq.Workplane("XY")
        .polyline([(28.0, 0.0), (32.0, 0.0), (32.0, 4.0)])
        .close()
        .extrude(12.0)
        .val()
    )
    finished = stock.cut(bore).cut(seat).cut(taper)
    assert finished.isValid()
    rotated = finished.transformShape(rigid_transform(g, q, r, origin))
    frame: dict[str, object] = {
        "origin_global_xyz_mm": list(origin),
        "basis_columns_global_xyz": [list(g), list(q), list(r)],
        "original_dimensions_gqr_mm": [32.0, 20.0, 12.0],
    }
    return rotated, frame


def test_translated_rotated_bore_seat_and_taper_are_descriptive_and_bounded() -> None:
    shape, frame = oblique_fixture()
    features = features_for_shape("fixture", shape, frame)

    assert len(features) == len(shape.Faces())
    assert [row["feature_id"] for row in features] == [
        f"fixture/facet{index:03d}" for index in range(1, len(shape.Faces()) + 1)
    ]
    bores = [
        row
        for row in features
        if row["surface_kind"] == "CYLINDER"
        and row["cylinder"]["material_side_geometry"] == "bore_like"
    ]
    assert len(bores) == 1
    assert bores[0]["cylinder"]["radius_mm"] == pytest.approx(2.1)
    assert bores[0]["cylinder"]["axis_unit_stock_gqr"] == pytest.approx([1.0, 0.0, 0.0])
    assert bores[0]["cylinder"]["radial_normal_dot"] < -0.999
    assert bores[0]["cylinder"]["normal_sample_valid_on_trim"] is True
    assert bores[0]["classification"] == "descriptive_cylindrical_patch"

    planes = [row for row in features if row["surface_kind"] == "PLANE"]
    assert planes
    seat_planes = [
        row
        for row in planes
        if row["plane"]["absolute_angle_to_stock_axes_deg"]["r"] < 1e-5
        and row["centroid_stock_gqr_mm"][2] == pytest.approx(8.0, abs=1e-6)
    ]
    assert seat_planes
    assert all(row["classification"] == "descriptive_planar_patch" for row in planes)
    assert any(
        max(row["plane"]["absolute_angle_to_stock_axes_deg"].values()) > 30.0
        for row in planes
    )  # the diagonal taper plane remains geometry, with no inferred cut label
    assert all(row["trim"]["wire_count"] >= 1 for row in features)
    assert all("bounds_stock_gqr_mm" in row and "vertices" in row for row in features)


def test_oriented_outer_cylinder_and_bored_stock_have_opposite_material_side() -> None:
    frame: dict[str, object] = {
        "origin_global_xyz_mm": [0.0, 0.0, 0.0],
        "basis_columns_global_xyz": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "original_dimensions_gqr_mm": [20.0, 20.0, 20.0],
    }
    outer = cq.Solid.makeCylinder(5.0, 20.0, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    outer_features = features_for_shape("outer", outer, frame)
    outer_cylinder = next(
        row for row in outer_features if row["surface_kind"] == "CYLINDER"
    )
    assert outer_cylinder["cylinder"]["material_side_geometry"] == "exterior_like"
    assert outer_cylinder["cylinder"]["radial_normal_dot"] > 0.999
    assert outer_cylinder["cylinder"]["normal_sample_valid_on_trim"] is True
    assert outer_cylinder["cylinder"]["axis_station_interval_mm"] == pytest.approx(
        [0.0, 20.0]
    )

    stock = cq.Solid.makeBox(20.0, 12.0, 12.0)
    bore = cq.Solid.makeCylinder(2.0, 20.0, cq.Vector(0, 6.0, 6.0), cq.Vector(1, 0, 0))
    bored = stock.cut(bore)
    bore_features = features_for_shape("bored", bored, frame)
    bore_face = next(row for row in bore_features if row["surface_kind"] == "CYLINDER")
    assert bore_face["cylinder"]["material_side_geometry"] == "bore_like"
    assert bore_face["cylinder"]["radial_normal_dot"] < -0.999


def test_stock_point_roundtrip_and_frame_orientation_are_validated() -> None:
    origin = (13.0, -7.0, 4.0)
    g = (math.sqrt(0.5), math.sqrt(0.5), 0.0)
    q = (-math.sqrt(0.5), math.sqrt(0.5), 0.0)
    r = (0.0, 0.0, 1.0)
    checked_origin, basis = _validate_frame(origin, [g, q, r])
    point = (100.0, 20.0, -3.0)
    local = _to_stock_point(point, checked_origin, basis)
    restored = _to_global_point(local, checked_origin, basis)
    assert restored == pytest.approx(point, abs=1e-12)
    assert _validate_frame(checked_origin, basis)[1] == basis

    with pytest.raises(SurfaceError, match="orthogonal"):
        _validate_frame(
            (0, 0, 0),
            [(1, 0, 0), (math.sqrt(0.5), math.sqrt(0.5), 0), (0, 0, 1)],
        )
    with pytest.raises(SurfaceError, match="unit length"):
        _validate_frame((0, 0, 0), [(2, 0, 0), (0, 1, 0), (0, 0, 1)])
    with pytest.raises(SurfaceError, match="right-handed"):
        _validate_frame((0, 0, 0), [(1, 0, 0), (0, 1, 0), (0, 0, -1)])


@pytest.mark.parametrize(
    "scaled_field",
    [
        "grain_axis_global_xyz",
        "section_q_axis_global_xyz",
        "section_r_axis_global_xyz",
    ],
)
def test_saved_stock_basis_is_checked_before_normalization(scaled_field) -> None:
    row = {
        "member_id": "fixture",
        "proposed_frame": {
            "status": "CONTAINED",
            "grain_axis_global_xyz": [1.0, 0.0, 0.0],
            "section_q_axis_global_xyz": [0.0, 1.0, 0.0],
            "section_r_axis_global_xyz": [0.0, 0.0, 1.0],
        },
        "original_stock_containment": {
            "proposed_stock_bounds_g_q_r_mm": [[4.0, 12.0], [7.0, 11.0], [1.0, 8.0]]
        },
    }
    frame = _build_stock_frame(row)
    assert frame["origin_global_xyz_mm"] == [4.0, 7.0, 1.0]
    assert frame["original_dimensions_gqr_mm"] == [8.0, 4.0, 7.0]
    row["proposed_frame"][scaled_field] = [
        2.0 * value for value in row["proposed_frame"][scaled_field]
    ]
    with pytest.raises(SurfaceError, match="unit length"):
        _build_stock_frame(row)


def test_unknown_surface_kind_is_fail_closed_but_kept_in_face_coverage() -> None:
    frame: dict[str, object] = {
        "origin_global_xyz_mm": [-4.0, -4.0, -4.0],
        "basis_columns_global_xyz": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        "original_dimensions_gqr_mm": [8.0, 8.0, 8.0],
    }
    torus = cq.Solid.makeTorus(6.0, 2.0)
    features = features_for_shape("unknown", torus, frame)
    assert len(features) == len(torus.Faces())
    assert len(features) == 1
    assert features[0]["surface_kind"] == "TORUS"
    assert features[0]["classification"] == "unsupported_descriptive_only"
    assert "geometry_trace" in features[0]
    assert features[0]["trim"]["wire_count"] >= 1


def test_wrong_pins_and_noncanonical_output_bytes_fail_closed(tmp_path) -> None:
    pinned = tmp_path / "source.bin"
    pinned.write_bytes(b"frozen")
    pins = {
        "pins": {
            "fixture": {
                "path": "source.bin",
                "sha256": hashlib.sha256(b"frozen").hexdigest(),
                "size_bytes": 6,
            }
        }
    }
    verify_pin_document(tmp_path, pins)
    pinned.write_bytes(b"changed")
    with pytest.raises(SurfaceError, match="pinned bytes changed"):
        verify_pin_document(tmp_path, pins)

    output = tmp_path / "canonical.json"
    value = {"z": 1, "a": "fixture"}
    output.write_bytes(canonical_bytes(value))
    verify_canonical_file(output, value, "fixture")
    output.write_text('{ "z": 1, "a": "fixture" }\n', encoding="utf-8")
    with pytest.raises(SurfaceError, match="exact canonical"):
        verify_canonical_file(output, value, "fixture")
