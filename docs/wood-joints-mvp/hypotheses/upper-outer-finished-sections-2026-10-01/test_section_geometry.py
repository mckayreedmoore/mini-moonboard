from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import section_geometry as sg

cq = pytest.importorskip("cadquery")


def frame(origin=(0.0, 0.0, 0.0)):
    return origin, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)


def section(shape, origin=(5.0, 0.0, 0.0), grain=(1.0, 0.0, 0.0), u=(0.0, 1.0, 0.0), v=(0.0, 0.0, 1.0)):
    return sg.section_properties(shape, origin, grain, u, v)


def test_rectangle_matches_independent_area_and_covariance_integrals():
    shape = cq.Solid.makeBox(10.0, 20.0, 30.0)

    result = section(shape)

    assert result["area_mm2"] == pytest.approx(600.0, abs=1e-8)
    assert result["centroid_global_xyz_mm"] == pytest.approx([5.0, 10.0, 15.0], abs=1e-8)
    assert result["centroid_relative_uv_mm"] == pytest.approx([10.0, 15.0], abs=1e-8)
    assert result["area_covariance_integrals_mm4"] == pytest.approx(
        {"uu": 20_000.0, "uv": 0.0, "vv": 45_000.0}, abs=1e-7
    )
    assert result["component_count"] == 1
    assert result["disconnected_ligaments"] is False
    assert result["components"][0]["wire_count"] == 1
    assert result["kernel"] == {"cadquery": "2.8.0", "ocp": "7.9.3.1.1"}


def test_adjacent_terminal_faces_form_one_component_with_combined_moments():
    # Solid.fuse preserves two adjacent terminal face patches without cleaning.
    first = cq.Solid.makeBox(20.0, 30.0, 8.0)
    second = cq.Solid.makeBox(20.0, 30.0, 8.0, cq.Vector(20.0, 0.0, 0.0))
    shape = first.fuse(second)
    assert len(shape.Solids()) == 1
    assert len(shape.Faces()) == 10

    result = section(
        shape, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0),
        (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
    )

    assert result["area_mm2"] == pytest.approx(40.0 * 30.0, abs=1e-8)
    assert result["centroid_relative_uv_mm"] == pytest.approx([20.0, 15.0], abs=1e-8)
    assert result["area_covariance_integrals_mm4"] == pytest.approx(
        {"uu": 30.0 * 40.0**3 / 12.0, "uv": 0.0, "vv": 40.0 * 30.0**3 / 12.0},
        abs=1e-7,
    )
    assert result["component_count"] == 1
    assert result["disconnected_ligaments"] is False
    component = result["components"][0]
    assert component["wire_count"] == 2
    assert component["area_mm2"] == pytest.approx(result["area_mm2"], abs=1e-8)
    assert component["area_covariance_integrals_mm4"] == pytest.approx(
        result["area_covariance_integrals_mm4"], abs=1e-7
    )


def test_off_center_grain_parallel_hole_matches_subtracted_disk_moments():
    width_u, depth_v, radius = 20.0, 30.0, 2.0
    hole_u, hole_v = 6.0, 12.0
    block = cq.Solid.makeBox(10.0, width_u, depth_v)
    bore = cq.Solid.makeCylinder(radius, 10.0, cq.Vector(0.0, hole_u, hole_v), cq.Vector(1.0, 0.0, 0.0))
    shape = block.cut(bore)

    result = section(shape)

    outer_area = width_u * depth_v
    hole_area = math.pi * radius**2
    area = outer_area - hole_area
    centroid_u = (outer_area * width_u / 2.0 - hole_area * hole_u) / area
    centroid_v = (outer_area * depth_v / 2.0 - hole_area * hole_v) / area
    expected_uu = (
        outer_area * width_u**2 / 12.0
        + outer_area * (width_u / 2.0 - centroid_u) ** 2
        - (math.pi * radius**4 / 4.0 + hole_area * (hole_u - centroid_u) ** 2)
    )
    expected_vv = (
        outer_area * depth_v**2 / 12.0
        + outer_area * (depth_v / 2.0 - centroid_v) ** 2
        - (math.pi * radius**4 / 4.0 + hole_area * (hole_v - centroid_v) ** 2)
    )
    expected_uv = (
        outer_area * (width_u / 2.0 - centroid_u) * (depth_v / 2.0 - centroid_v)
        - hole_area * (hole_u - centroid_u) * (hole_v - centroid_v)
    )

    assert result["area_mm2"] == pytest.approx(area, abs=1e-7)
    assert result["centroid_relative_uv_mm"] == pytest.approx([centroid_u, centroid_v], abs=1e-8)
    assert result["area_covariance_integrals_mm4"] == pytest.approx(
        {"uu": expected_uu, "uv": expected_uv, "vv": expected_vv}, abs=1e-6
    )
    assert result["component_count"] == 1
    assert result["components"][0]["wire_count"] == 2


def test_transverse_bore_returns_two_unequal_disconnected_strip_components():
    width_u, depth_v = 20.0, 30.0
    band_half_height, band_center_v = 4.0, 12.0
    block = cq.Solid.makeBox(10.0, width_u, depth_v)
    bore = cq.Solid.makeCylinder(
        band_half_height,
        width_u + 2.0,
        cq.Vector(5.0, -1.0, band_center_v),
        cq.Vector(0.0, 1.0, 0.0),
    )
    shape = block.cut(bore)

    result = section(shape)

    lower_height = band_center_v - band_half_height
    upper_height = depth_v - band_center_v - band_half_height
    lower_area = width_u * lower_height
    upper_area = width_u * upper_height
    total_area = lower_area + upper_area
    centroid_v = (lower_area * lower_height / 2.0 + upper_area * (band_center_v + band_half_height + upper_height / 2.0)) / total_area
    expected_uu = total_area * width_u**2 / 12.0
    expected_vv = (
        width_u * lower_height**3 / 12.0
        + lower_area * (lower_height / 2.0 - centroid_v) ** 2
        + width_u * upper_height**3 / 12.0
        + upper_area * (band_center_v + band_half_height + upper_height / 2.0 - centroid_v) ** 2
    )
    assert result["area_mm2"] == pytest.approx(total_area, abs=1e-7)
    assert result["component_count"] == 2
    assert result["disconnected_ligaments"] is True
    assert [item["area_mm2"] for item in result["components"]] == pytest.approx([lower_area, upper_area], abs=1e-7)
    expected_component_centroids = [
        [10.0, lower_height / 2.0],
        [10.0, band_center_v + band_half_height + upper_height / 2.0],
    ]
    for item, expected in zip(result["components"], expected_component_centroids, strict=True):
        assert item["centroid_relative_uv_mm"] == pytest.approx(expected, abs=1e-7)
    assert result["centroid_relative_uv_mm"] == pytest.approx([10.0, centroid_v], abs=1e-7)
    assert result["area_covariance_integrals_mm4"] == pytest.approx(
        {"uu": expected_uu, "uv": 0.0, "vv": expected_vv}, abs=1e-6
    )
    assert result["area_covariance_integrals_mm4"]["uv"] == pytest.approx(0.0, abs=1e-7)


def _rotate(vector, axis, angle_radians):
    axis_length = math.sqrt(math.fsum(value * value for value in axis))
    x, y, z = (value / axis_length for value in axis)
    cosine = math.cos(angle_radians)
    sine = math.sin(angle_radians)
    dot = x * vector[0] + y * vector[1] + z * vector[2]
    cross = (
        y * vector[2] - z * vector[1],
        z * vector[0] - x * vector[2],
        x * vector[1] - y * vector[0],
    )
    return tuple(vector[i] * cosine + cross[i] * sine + (1.0 - cosine) * dot * (x, y, z)[i] for i in range(3))


def test_arbitrary_rotation_and_translation_preserve_relative_properties():
    shape = cq.Solid.makeBox(10.0, 20.0, 30.0)
    original_origin = (5.0, 0.0, 0.0)
    original_axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    base = section(shape, original_origin, *original_axes)
    axis = (1.0, -2.0, 3.0)
    angle = math.radians(37.0)
    shift = (123.0, -78.0, 45.0)
    rotated = shape.rotate((0.0, 0.0, 0.0), axis, math.degrees(angle)).translate(shift)
    rotated_origin = tuple(_rotate(original_origin, axis, angle)[i] + shift[i] for i in range(3))
    rotated_axes = tuple(_rotate(vector, axis, angle) for vector in original_axes)

    result = section(rotated, rotated_origin, *rotated_axes)

    assert result["area_mm2"] == pytest.approx(base["area_mm2"], abs=1e-7)
    assert result["centroid_relative_uv_mm"] == pytest.approx(base["centroid_relative_uv_mm"], abs=1e-7)
    assert result["area_covariance_integrals_mm4"] == pytest.approx(
        base["area_covariance_integrals_mm4"], abs=1e-6
    )
    expected_global_center = tuple(_rotate(base["centroid_global_xyz_mm"], axis, angle)[i] + shift[i] for i in range(3))
    assert result["centroid_global_xyz_mm"] == pytest.approx(expected_global_center, abs=1e-7)


@pytest.mark.parametrize("station", [0.0, 10.0])
def test_terminal_one_sided_section_returns_end_profile_once(station):
    shape = cq.Solid.makeBox(10.0, 20.0, 30.0)

    result = section(shape, origin=(station, 0.0, 0.0))

    assert result["area_mm2"] == pytest.approx(600.0, abs=1e-8)
    assert result["component_count"] == 1
    assert result["components"][0]["area_mm2"] == pytest.approx(600.0, abs=1e-8)


@pytest.mark.parametrize(
    ("grain", "u", "v", "message"),
    [
        ((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), "unit"),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 1.0, 0.0), "orthogonal"),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0), "right-handed"),
        ((1.0, 0.0, 0.0), (0.0, math.nan, 0.0), (0.0, 0.0, 1.0), "finite"),
    ],
)
def test_malformed_frame_is_refused_before_geometry_query(grain, u, v, message):
    with pytest.raises(sg.SectionGeometryError, match=message):
        sg.section_properties(object(), (0.0, 0.0, 0.0), grain, u, v)


def test_outside_plane_and_compound_input_are_refused():
    shape = cq.Solid.makeBox(10.0, 20.0, 30.0)
    with pytest.raises(sg.SectionGeometryError, match="outside|no positive-area"):
        section(shape, origin=(11.0, 0.0, 0.0))
    two_solids = cq.Compound.makeCompound([shape, cq.Solid.makeBox(1.0, 1.0, 1.0, cq.Vector(20.0, 0.0, 0.0))])
    with pytest.raises(sg.SectionGeometryError, match="exactly one solid"):
        sg.section_properties(two_solids, *frame())
