"""Standard-library wrench primitives kept importable in the native image."""

from dataclasses import FrozenInstanceError, dataclass

import pytest

from fea.wood_joint_patch_wrench import (
    Wrench,
    equilibrium_residual,
    is_equilibrated,
    shift_wrench,
    to_local,
)


def test_wrench_copies_input_vectors_to_immutable_finite_tuples():
    force = [3, 4, 5]
    moment = [10, 20, 30]
    wrench = Wrench(force, moment)
    force[0] = 999

    assert wrench.force_n == (3.0, 4.0, 5.0)
    assert wrench.moment_nmm == (10.0, 20.0, 30.0)
    with pytest.raises(FrozenInstanceError):
        wrench.force_n = (0.0, 0.0, 0.0)


@pytest.mark.parametrize(
    "bad_vector",
    [
        (1.0, 2.0),
        (1.0, 2.0, float("nan")),
        (1.0, 2.0, float("inf")),
        "123",
    ],
)
def test_wrench_rejects_nonfinite_or_non_vector_components(bad_vector):
    with pytest.raises((TypeError, ValueError), match="finite 3-vector"):
        Wrench(bad_vector, (0.0, 0.0, 0.0))


def test_shift_and_local_projection_keep_all_six_simultaneous_components():
    wrench = Wrench((11.0, -7.0, 6.0), (37.0, 21.0, -31.0))
    shifted = shift_wrench(wrench, (13.0, -18.0, 6.0), (10.0, -20.0, 5.0))
    assert shifted == Wrench((11.0, -7.0, 6.0), (56.0, 14.0, -74.0))

    local = to_local(
        shifted,
        ((0.0, 1.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
    )
    assert local == Wrench((-7.0, -11.0, 6.0), (14.0, -56.0, -74.0))


def test_equilibrium_residual_and_tolerance_check():
    residual = equilibrium_residual(
        Wrench((9.0, 4.0, 2.0), (-12.0, 0.0, -20.0)),
        (
            ((0.0, 2.0, 0.0), (10.0, 0.0, 0.0)),
            ((0.0, 0.0, 3.0), (0.0, 4.0, 0.0)),
        ),
        contact_force=(0.0, 0.0, 2.0),
        other_force=(-1.0, 0.0, 0.0),
    )
    assert is_equilibrated(residual)

    outside_tolerance = Wrench((0.2, 0.0, 0.0), (0.0, 0.0, 0.0))
    assert not is_equilibrated(outside_tolerance, force_tolerance_n=0.1)


def test_wrench_primitives_reject_foreign_wrench_identity():
    @dataclass(frozen=True)
    class ForeignWrench:
        force_n: tuple[float, float, float]
        moment_nmm: tuple[float, float, float]

    with pytest.raises(TypeError, match="patch Wrench"):
        shift_wrench(
            ForeignWrench((1.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 0.0),
        )


def test_local_transform_rejects_non_right_handed_basis():
    with pytest.raises(ValueError, match="right-handed"):
        to_local(
            Wrench((1.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
            ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
        )
