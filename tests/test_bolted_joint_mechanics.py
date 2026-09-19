"""LB-10 wrench, contact, and clearance semantics."""

import math

import pytest

from mini_moonboard.bolted_joint_mechanics import (
    Wrench,
    clearance_response,
    compression_only_contact,
    equilibrium_residual,
    is_equilibrated,
    require_unique_physical_fasteners,
    shift_wrench,
    to_local,
)


def test_wrench_shift_preserves_force_and_adds_eccentric_moment() -> None:
    shifted = shift_wrench(
        Wrench((10.0, 0.0, 0.0), (0.0, 0.0, 0.0)), (0.0, 20.0, 0.0), (0.0, 0.0, 0.0)
    )
    assert shifted.force_n == (10.0, 0.0, 0.0)
    assert shifted.moment_nmm == (0.0, 0.0, -200.0)


def test_local_wrench_transform_and_equilibrium() -> None:
    wrench = Wrench((3.0, 4.0, 0.0), (0.0, 0.0, 10.0))
    local = to_local(wrench, ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
    assert local == Wrench((4.0, -3.0, 0.0), (0.0, 0.0, 10.0))
    residual = equilibrium_residual(
        Wrench((10.0, 0.0, 0.0), (0.0, 0.0, -20.0)),
        (((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),),
    )
    assert is_equilibrated(residual)


def test_local_transform_preserves_composed_moment_equilibrium() -> None:
    basis = ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    joint = Wrench((9.0, 4.0, 2.0), (-12.0, 0.0, -20.0))
    fasteners = (
        ((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),
        ((0.0, 0.0, 3.0), (0.0, 4.0, 0.0)),
    )
    contact = (0.0, 0.0, 2.0)
    other = (-1.0, 0.0, 0.0)
    assert is_equilibrated(equilibrium_residual(joint, fasteners, contact, other))

    def project(vector: tuple[float, float, float]) -> tuple[float, float, float]:
        return to_local(Wrench(vector, (0.0, 0.0, 0.0)), basis).force_n

    local_fasteners = tuple(
        (project(offset), project(force)) for offset, force in fasteners
    )
    local_residual = equilibrium_residual(
        to_local(joint, basis), local_fasteners, project(contact), project(other)
    )
    assert is_equilibrated(local_residual)


@pytest.mark.parametrize(
    "basis",
    [
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        ((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        ((2.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.1, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        ((math.nan, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.0, math.inf, 0.0), (0.0, 0.0, 1.0)),
    ],
)
def test_local_transform_rejects_invalid_basis(
    basis: tuple[tuple[float, float, float], ...],
) -> None:
    with pytest.raises(ValueError, match="basis"):
        to_local(Wrench((1.0, 2.0, 3.0), (0.0, 0.0, 0.0)), basis)


def test_local_transform_accepts_roundoff_in_rotation() -> None:
    basis = ((1.0, 1e-11, 0.0), (-1e-11, 1.0, 0.0), (0.0, 0.0, 1.0))
    assert to_local(
        Wrench((1.0, 2.0, 3.0), (0.0, 0.0, 0.0)), basis
    ).force_n == pytest.approx((1.0, 2.0, 3.0))


def test_contact_does_not_carry_opening_tension() -> None:
    assert compression_only_contact((-4.0, 0.0, 0.0), (1.0, 0.0, 0.0)) == (
        0.0,
        0.0,
        0.0,
    )
    assert compression_only_contact((4.0, 0.0, 0.0), (1.0, 0.0, 0.0)) == (4.0, 0.0, 0.0)


def test_clearance_is_explicit_and_duplicate_load_paths_fail() -> None:
    assert clearance_response(20.0, 10.0, 1.0) == pytest.approx(3.0)
    with pytest.raises(ValueError, match="duplicated"):
        require_unique_physical_fasteners(("bolt-1", "bolt-1"))


@pytest.mark.parametrize("force", [20.0, -20.0])
def test_clearance_total_slip_is_monotonic_and_matches_bearing_force(
    force: float,
) -> None:
    slips = [clearance_response(force, 10.0, gap) for gap in (0.0, 1.0, 2.0, 3.0)]
    assert [abs(slip) for slip in slips] == pytest.approx((2.0, 3.0, 4.0, 5.0))
    assert all(math.copysign(1.0, slip) == math.copysign(1.0, force) for slip in slips)
    for gap, slip in zip((0.0, 1.0, 2.0, 3.0), slips, strict=True):
        assert 10.0 * max(0.0, abs(slip) - gap) == pytest.approx(abs(force))


@pytest.mark.parametrize("gap", [0.0, 1.0, 3.0])
def test_zero_force_clearance_convention(gap: float) -> None:
    assert clearance_response(0.0, 10.0, gap) == 0.0


@pytest.mark.parametrize(
    ("force", "stiffness", "gap"),
    [
        (math.nan, 10.0, 1.0),
        (math.inf, 10.0, 1.0),
        (-math.inf, 10.0, 1.0),
        (20.0, math.nan, 1.0),
        (20.0, math.inf, 1.0),
        (20.0, -math.inf, 1.0),
        (20.0, 0.0, 1.0),
        (20.0, -1.0, 1.0),
        (20.0, 10.0, math.nan),
        (20.0, 10.0, math.inf),
        (20.0, 10.0, -math.inf),
        (20.0, 10.0, -1.0),
    ],
)
def test_clearance_rejects_invalid_inputs(
    force: float, stiffness: float, gap: float
) -> None:
    with pytest.raises(ValueError, match="clearance/stiffness"):
        clearance_response(force, stiffness, gap)
