"""Independent mass-coordinate calculation; no native execution or acceptance."""

from fractions import Fraction
import json
import numpy as np


def calculate():
    alpha = Fraction(1203, 10000)
    corner = alpha / (1 + alpha) / 4
    midside = 1 / (1 + alpha) / 6
    exact_masses = [corner] * 4 + [midside] * 6
    assert sum(exact_masses) == 1
    mass = np.diag([float(value) for value in exact_masses])
    # Independent coordinates are physical nodes 2..10, followed by q11.
    # u1 = 4*q11 - u2 - u3 - u4; every physical motion remains representable.
    transform = np.zeros((10, 10))
    transform[0, :3] = -1
    transform[0, 9] = 4
    transform[1:, :9] = np.eye(9)
    assert np.linalg.matrix_rank(transform) == 10
    applied = mass @ np.ones(10)
    reduced_mass = transform.T @ mass @ transform
    reduced_force = transform.T @ applied
    full_acceleration = transform @ np.linalg.solve(reduced_mass, reduced_force)
    diagonal_acceleration = transform @ (reduced_force / np.diag(reduced_mass))
    assert np.max(np.abs(full_acceleration - 1)) < 1e-12
    assert np.max(np.abs(diagonal_acceleration - np.array([1, 0, 0, 0] + [1] * 6))) < 1e-12
    return {
        "status": "PASS_INDEPENDENT_COORDINATE_INVARIANCE_ORACLE",
        "mass_tonne_exact": [str(value) for value in exact_masses],
        "total_mass_tonne": 1,
        "physical_force_N": applied.tolist(),
        "coordinate_transform_rank": 10,
        "reduced_mass_tonne": reduced_mass.tolist(),
        "full_reduced_mass_physical_acceleration_mm_s2": full_acceleration.tolist(),
        "diagonal_only_hypothesis_initial_acceleration_mm_s2": diagonal_acceleration.tolist(),
        "diagonal_only_hypothesis_initial_momentum_rate_N": float(applied @ diagonal_acceleration),
        "initial_external_force_N": float(np.sum(applied)),
        "analytical_trajectory": "All physical U1=t^2/2 mm and V1=t mm/s; q11 has the same motion. Physical ELSE=0, ELKE=t^2/2 N mm. This tests the declared lumped discrete mass, not consistent-mass equivalence.",
        "hypothesis_limit": "The diagonal-only acceleration is a source-derived initial-state prediction, not a native result or full-history prediction; later internal forces may differ.",
        "native_execution": False,
        "joint_acceptance": False,
        "release": False,
    }


if __name__ == "__main__":
    print(json.dumps(calculate(), indent=2, sort_keys=True, allow_nan=False))
