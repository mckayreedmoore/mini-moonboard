"""Independent reciprocal-compliance calculation, separate from the producer."""

import importlib.util
import json
import math
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "frame_prepare", Path(__file__).with_name("prepare.py")
)
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)


def solve_normal(compliance, strain):
    """Small independent Gaussian elimination; no source matrix or FE operator."""
    rows = [list(row) + [value] for row, value in zip(compliance, strain, strict=True)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(rows[row][column]))
        rows[column], rows[pivot] = rows[pivot], rows[column]
        divisor = rows[column][column]
        assert divisor != 0
        rows[column] = [value / divisor for value in rows[column]]
        for row in range(3):
            if row != column:
                factor = rows[row][column]
                rows[row] = [
                    a - factor * b for a, b in zip(rows[row], rows[column], strict=True)
                ]
    return [row[3] for row in rows]


def independent_answers():
    # These are the stated method inputs, not values copied from producer output.
    e_l, e_r, e_t = 11032.0, 750.176, 551.6
    nu_lr, nu_lt, nu_rt = 0.292, 0.449, 0.390
    shear_lr, shear_lt, shear_rt = 706.048, 860.496, 77.224
    sine, cosine = math.sin(math.radians(40)), math.cos(math.radians(40))
    q = ((0, 1, 0), (sine, 0, cosine), (cosine, 0, -sine))
    global_strain = ((2e-5, 5e-6, 7e-6), (5e-6, -3e-5, -2e-6), (7e-6, -2e-6, -1e-4))
    local_strain = [
        [
            math.fsum(
                q[i][a] * global_strain[i][j] * q[j][b]
                for i in range(3)
                for j in range(3)
            )
            for b in range(3)
        ]
        for a in range(3)
    ]
    compliance = (
        (1 / e_l, -nu_lr / e_l, -nu_lt / e_l),
        (-nu_lr / e_l, 1 / e_r, -nu_rt / e_r),
        (-nu_lt / e_l, -nu_rt / e_r, 1 / e_t),
    )
    normal = solve_normal(compliance, [local_strain[i][i] for i in range(3)])
    local_stress = [[0.0] * 3 for _ in range(3)]
    for i in range(3):
        local_stress[i][i] = normal[i]
    for i, j, modulus in ((0, 1, shear_lr), (0, 2, shear_lt), (1, 2, shear_rt)):
        local_stress[i][j] = local_stress[j][i] = 2 * modulus * local_strain[i][j]
    global_stress = [
        [
            math.fsum(
                q[i][a] * local_stress[a][b] * q[j][b]
                for a in range(3)
                for b in range(3)
            )
            for j in range(3)
        ]
        for i in range(3)
    ]
    local_energy = 0.5 * math.fsum(
        local_stress[i][j] * local_strain[i][j] for i in range(3) for j in range(3)
    )
    global_energy = 0.5 * math.fsum(
        global_stress[i][j] * global_strain[i][j] for i in range(3) for j in range(3)
    )
    return local_stress, global_stress, local_energy, global_energy


def test_pinned_tensor_and_energy_match_independent_reciprocal_compliance():
    local_stress, global_stress, local_energy, global_energy = independent_answers()
    oracle = json.loads(prepare.ORACLE.read_text())
    for computed, key in (
        (local_stress, "local_stress_tensor_MPa"),
        (global_stress, "global_stress_tensor_MPa"),
    ):
        for actual, expected in zip(computed, oracle[key], strict=True):
            assert actual == pytest.approx(expected, abs=1e-14, rel=1e-11)
    assert local_energy == pytest.approx(global_energy, abs=1e-16)
    assert global_energy == pytest.approx(oracle["energy_density_N_per_mm3"], abs=1e-16)
    assert global_energy > 0
