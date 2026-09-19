"""LB-10 wrench, contact, and clearance semantics."""

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
    shifted = shift_wrench(Wrench((10.0, 0.0, 0.0), (0.0, 0.0, 0.0)), (0.0, 20.0, 0.0), (0.0, 0.0, 0.0))
    assert shifted.force_n == (10.0, 0.0, 0.0)
    assert shifted.moment_nmm == (0.0, 0.0, -200.0)


def test_local_wrench_transform_and_equilibrium() -> None:
    wrench = Wrench((3.0, 4.0, 0.0), (0.0, 0.0, 10.0))
    local = to_local(wrench, ((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)))
    assert local == Wrench((4.0, 3.0, 0.0), (0.0, 0.0, 10.0))
    residual = equilibrium_residual(Wrench((10.0, 0.0, 0.0), (0.0, 0.0, -20.0)), (((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),))
    assert is_equilibrated(residual)


def test_contact_does_not_carry_opening_tension() -> None:
    assert compression_only_contact((-4.0, 0.0, 0.0), (1.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)
    assert compression_only_contact((4.0, 0.0, 0.0), (1.0, 0.0, 0.0)) == (4.0, 0.0, 0.0)


def test_clearance_is_explicit_and_duplicate_load_paths_fail() -> None:
    assert clearance_response(20.0, 10.0, 1.0) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="duplicated"):
        require_unique_physical_fasteners(("bolt-1", "bolt-1"))
