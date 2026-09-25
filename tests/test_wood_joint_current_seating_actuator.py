"""Check the new actuator's MPC direction, duality and dependent-DOF choice."""

import math
from types import SimpleNamespace

import pytest

from fea.wood_joint_current_seating_actuator import (
    DIRECTION_N,
    equation_for_distributions,
)
from fea.wood_joint_patch_unit_cases import PatchNodeWeight, distribute_wrench_to_nodes
from fea.wood_joint_patch_wrench import Wrench, cross


def _distributions():
    points = ((0, -2, -1), (0, 3, -1), (0, 0, 4))
    return tuple(distribute_wrench_to_nodes(
        tuple(PatchNodeWeight(offset + i, point, area)
              for i, (point, area) in enumerate(zip(points, (2, 3, 5), strict=True), 1)),
        (0, 0, 0), Wrench(tuple(sign * value for value in DIRECTION_N), (0, 0, 0)),
        owner_body=f"owner{offset}",
    ) for offset, sign in ((0, 1), (10, -1)))


def test_actuator_reproduces_relative_translation_without_coupling_rigid_rotation():
    distributions = _distributions()
    cards, info = equation_for_distributions(distributions, 100)
    translations = ((0.2, -0.5, 1.2), (-0.4, 0.7, -0.1))
    rotations = ((0.1, -0.2, 0.05), (-0.3, 0.1, 0.2))
    actual = 0.0
    displacements = {}
    for distribution, translation, rotation in zip(distributions, translations, rotations, strict=True):
        for force in distribution.nodal_forces:
            rotational = cross(rotation, force.point_xyz_mm)
            u = tuple(a + b for a, b in zip(translation, rotational, strict=True))
            displacements[force.node_id] = u
            actual += math.fsum(f * v for f, v in zip(force.force_xyz_n, u, strict=True))
    expected = math.fsum(n * (a - b) for n, a, b in zip(DIRECTION_N, *translations, strict=True))
    assert actual == pytest.approx(expected, abs=1e-12)
    assert info["dependent_physical_dof"][0] != 100
    assert info["independent_actuator_dof"] == [100, 1]
    lines = cards.splitlines()
    terms = [cell for line in lines[2:] for cell in line.split(",")]
    assert len(terms) == 3 * int(lines[1])
    residual = 0.0
    for i in range(0, len(terms), 3):
        node, dof, coefficient = int(terms[i]), int(terms[i + 1]), float(terms[i + 2])
        residual += coefficient * (expected if node == 100 else displacements[node][dof - 1])
    assert residual == pytest.approx(0.0, abs=1e-12)
    assert float(terms[2]) == pytest.approx(1.0)
    assert all(len(line.split(",")) <= 12 for line in lines[2:])


def test_actuator_multiplier_work_is_conjugate_to_its_scalar_motion():
    distributions = _distributions()
    _cards, info = equation_for_distributions(distributions, 100)
    u = {(force.node_id, dof): math.sin(force.node_id + 0.3 * dof)
         for distribution in distributions for force in distribution.nodal_forces
         for dof in (1, 2, 3)}
    q = math.fsum(coefficient * u[node, dof]
                  for node, dof, coefficient in info["physical_terms_before_normalization"])
    multiplier = 37.5
    nodal_work = math.fsum(multiplier * coefficient * u[node, dof]
                          for node, dof, coefficient in info["physical_terms_before_normalization"])
    assert nodal_work == pytest.approx(multiplier * q, abs=1e-12)


def test_actuator_rejects_colliding_reference_and_repeated_owner_dofs():
    distributions = _distributions()
    with pytest.raises(ValueError, match="colliding"):
        equation_for_distributions(distributions, 1)
    with pytest.raises(ValueError, match="overlapping"):
        equation_for_distributions((distributions[0], distributions[0]), 100)
    with pytest.raises(ValueError, match="positive integer"):
        equation_for_distributions(distributions, 1.5)


def test_serialized_tiny_signed_coefficients_fit_field_and_reproduce_work():
    forces = (
        SimpleNamespace(
            node_id=10,
            force_xyz_n=(1.0, 1.234567890123456e-24, -9.876543210987654e-25),
        ),
    )
    cards, info = equation_for_distributions(
        (SimpleNamespace(nodal_forces=forces),), 100
    )
    lines = cards.splitlines()
    term_count = int(lines[1])
    tokens = [
        token.strip()
        for line in lines[2:]
        for token in line.split(",")
        if token.strip()
    ]
    assert len(tokens) == 3 * term_count
    parsed = {
        (int(tokens[index]), int(tokens[index + 1])): float(tokens[index + 2])
        for index in range(0, len(tokens), 3)
    }
    assert all(len(tokens[index + 2]) <= 20 for index in range(0, len(tokens), 3))
    assert parsed[(10, 2)] > 0.0
    assert parsed[(10, 3)] < 0.0

    displacements = {(10, 1): 0.0, (10, 2): 1e24, (10, 3): 1e24}
    raw_observation = math.fsum(
        coefficient * displacements[node, dof]
        for node, dof, coefficient in info["physical_terms_before_normalization"]
    )
    scale = info["normalization_coefficient"]
    expected_actuator_motion = raw_observation / scale
    parsed_observation = math.fsum(
        coefficient * displacements[node, dof]
        for (node, dof), coefficient in parsed.items()
        if (node, dof) != (100, 1)
    )
    residual = parsed_observation + parsed[(100, 1)] * expected_actuator_motion
    assert parsed_observation == pytest.approx(
        expected_actuator_motion, rel=1e-13, abs=1e-13
    )
    assert residual == pytest.approx(0.0, abs=1e-13)

    multiplier = 37.5
    parsed_work = multiplier * parsed_observation
    dual_work = multiplier * expected_actuator_motion
    assert parsed_work == pytest.approx(dual_work, rel=5e-13, abs=5e-13)


def test_equation_coefficient_width_overflow_is_rejected():
    distribution = SimpleNamespace(
        nodal_forces=(
            SimpleNamespace(node_id=10, force_xyz_n=(1.0, -1e-308, 0.0)),
        )
    )
    with pytest.raises(ValueError, match="exceeds 20 characters"):
        equation_for_distributions((distribution,), 100)
