"""Focused exact-envelope tests for transverse round-component motion."""

from __future__ import annotations

import math

import cadquery as cq
import pytest

from scripts.wood_joint_transverse_hardware_sweep import (
    exact_transverse_round_component_sweep,
)


def _frame():
    axis = cq.Vector(2.0, -3.0, 6.0).normalized()
    reference = cq.Vector(1.0, 0.0, 0.0)
    travel_axis = (reference - axis * reference.dot(axis)).normalized()
    start = cq.Vector(7.0, -2.0, 4.0)
    return axis, travel_axis, start


def _annular_cylinder(outer_radius, inner_radius, height, start, axis):
    return cq.Solid.makeCylinder(outer_radius, height, start, axis).cut(
        cq.Solid.makeCylinder(inner_radius, height, start, axis)
    )


def _circle_lens_area(radius, distance):
    return (
        2.0 * radius**2 * math.acos(distance / (2.0 * radius))
        - 0.5 * distance * math.sqrt(4.0 * radius**2 - distance**2)
    )


def _assert_dense_poses_are_contained(source, sweep, displacement):
    for sample in range(21):
        pose = source.translate(displacement * (sample / 20.0))
        assert pose.cut(sweep).Volume() < 1e-5


def test_oblique_cylinder_transverse_sweep_has_capsule_volume_and_contains_poses():
    axis, travel_axis, start = _frame()
    radius, height, distance = 4.5, 7.25, 4.0
    source = cq.Solid.makeCylinder(radius, height, start, axis)
    displacement = -travel_axis * distance

    sweep, method = exact_transverse_round_component_sweep(source, displacement.toTuple())

    assert method == "exact_source_brep_transverse_cylinder_sweep"
    assert sweep is not None and sweep.isValid()
    assert sweep.Volume() == pytest.approx(
        (math.pi * radius**2 + 2.0 * radius * distance) * height,
        abs=1e-5,
    )
    _assert_dense_poses_are_contained(source, sweep, displacement)


def test_short_annular_translation_preserves_shared_bore_lens():
    axis, travel_axis, start = _frame()
    outer_radius, inner_radius, height, distance = 8.0, 3.0, 2.5, 2.0
    source = _annular_cylinder(outer_radius, inner_radius, height, start, axis)
    displacement = travel_axis * distance

    sweep, method = exact_transverse_round_component_sweep(source, displacement.toTuple())

    expected_volume = (
        math.pi * outer_radius**2
        + 2.0 * outer_radius * distance
        - _circle_lens_area(inner_radius, distance)
    ) * height
    shared_bore = cq.Solid.makeCylinder(inner_radius, height, start, axis).intersect(
        cq.Solid.makeCylinder(inner_radius, height, start + displacement, axis)
    )
    assert method == "exact_source_brep_transverse_annular_cylinder_sweep"
    assert sweep is not None and sweep.isValid()
    assert sweep.Volume() == pytest.approx(expected_volume, abs=1e-5)
    assert sweep.intersect(shared_bore).Volume() == pytest.approx(0.0, abs=1e-5)
    _assert_dense_poses_are_contained(source, sweep, displacement)


def test_long_annular_translation_fills_bore_when_endpoint_holes_do_not_overlap():
    axis, travel_axis, start = _frame()
    outer_radius, inner_radius, height, distance = 8.0, 3.0, 2.5, 7.0
    source = _annular_cylinder(outer_radius, inner_radius, height, start, axis)
    displacement = travel_axis * distance

    sweep, method = exact_transverse_round_component_sweep(source, displacement.toTuple())

    expected_volume = (math.pi * outer_radius**2 + 2.0 * outer_radius * distance) * height
    midpoint_probe = cq.Solid.makeCylinder(
        0.25, height, start + displacement * 0.5, axis
    )
    assert method == "exact_source_brep_transverse_annular_cylinder_sweep"
    assert sweep is not None and sweep.isValid()
    assert sweep.Volume() == pytest.approx(expected_volume, abs=1e-5)
    assert sweep.intersect(midpoint_probe).Volume() == pytest.approx(
        midpoint_probe.Volume(), abs=1e-5
    )
    _assert_dense_poses_are_contained(source, sweep, displacement)


def test_unsupported_or_nonperpendicular_motion_is_declined():
    axis, travel_axis, start = _frame()
    washer = _annular_cylinder(8.0, 3.0, 2.5, start, axis)
    box = cq.Solid.makeBox(5.0, 6.0, 7.0, start)

    unsupported_sweep, unsupported_method = exact_transverse_round_component_sweep(
        box, (travel_axis * 4.0).toTuple()
    )
    axial_sweep, axial_method = exact_transverse_round_component_sweep(
        washer, (axis * 4.0).toTuple()
    )

    assert (unsupported_sweep, unsupported_method) == (None, None)
    assert (axial_sweep, axial_method) == (None, None)
