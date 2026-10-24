import math
import runpy
from pathlib import Path

import numpy as np
import pytest

from scripts.timber_vector_shear_bound import box_disk_sum_upper, region_bound


def test_orthogonal_direct_and_torsion_vectors():
    assert box_disk_sum_upper(0, 1, 1, 0, 1) == pytest.approx(math.sqrt(2))


def test_unrestricted_alignment_and_box_corner():
    assert box_disk_sum_upper(3, 4, 1, 1, 1) == pytest.approx(6)
    assert box_disk_sum_upper(0, 0, .3, .4, 1) == pytest.approx(.5)
    assert box_disk_sum_upper(3, 4, 0, 0, 0) == pytest.approx(5)


def test_dense_primal_points_are_bounded_and_old_peak_addition_is_upper():
    rng = np.random.default_rng(317)
    for _ in range(60):
        du, dv, a, b, radius = rng.uniform(0, 5, 5)
        upper = box_disk_sum_upper(du, dv, a, b, radius)
        angle = np.linspace(0, math.pi / 2, 4001)
        length = np.minimum(radius, np.minimum(
            a / np.maximum(np.cos(angle), 1e-300), b / np.maximum(np.sin(angle), 1e-300)))
        actual = np.hypot(du + length * np.cos(angle), dv + length * np.sin(angle))
        assert max(actual) <= upper + 1e-12
        assert upper <= min(math.hypot(du, dv) + radius, math.hypot(du+a, dv+b)) + 1e-12
        assert upper == pytest.approx(box_disk_sum_upper(dv, du, b, a, radius))


@pytest.mark.parametrize("bad", [math.nan, math.inf, -1])
def test_invalid_bounds_rejected(bad):
    with pytest.raises(ValueError):
        box_disk_sum_upper(0, 1, 1, bad, 1)


def region(wrench):
    return {"area_mm2": 3., "wrench_at_regional_centroid_n_nmm": wrench,
            "rectangle_torsion": {"J_mm4": 100., "J_series_absolute_tail_bound_mm4": .01,
                                  "face_shear_coefficients_u_v_per_mm3": [.7, 1.]}}


def test_complete_wrench_convexity_for_bernstein_controls():
    rng = np.random.default_rng(918)
    for _ in range(120):
        controls = rng.normal(0, 8, (4, 6))
        weights = rng.dirichlet(np.ones(4))
        index = region_bound(region(weights @ controls), 1.2)["upper_index"]
        control_indices = [region_bound(region(q), 1.2)["upper_index"] for q in controls]
        assert index <= weights @ control_indices + 1e-11


def test_signed_wrench_and_series_tail_kept():
    q = [9, 3, -4, 8, 20, -11]
    bound = region_bound(region(q), 1.2)
    assert bound == region_bound(region([-v for v in q]), 1.2)
    assert bound["J_tail_multiplier"] > 1
    assert bound["vector_shear_torsion_upper_mpa"] <= bound["separate_peak_sum_with_same_tail_mpa"] + 1e-12
    with pytest.raises(ValueError):
        region_bound(region(q[:5]), 1.2)
    with pytest.raises(ValueError):
        region_bound(region(q), 0)


def test_issued_rectangle_math_supplies_the_full_region_contract():
    root = Path(__file__).resolve().parents[1]
    path = root / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/corner-net-section.py"
    method = runpy.run_path(str(path), run_name="rectangle_vector_bound_control")
    comparison = method["nominal_section"](
        [100., 600., -240., 12000., 3200., -1800.],
        [{"bounds_uv_mm": [[0., 88.9], [0., 139.7]]}],
        {"Fv_parallel": 1.2, "Fb": 6., "Ft_parallel": 4., "Fc_parallel": 9.})
    current = comparison["regions"][0]
    result = region_bound(current, 1.2)
    assert result["upper_index"] <= current["same_state_shear_bound_over_Fv"] + 1e-7
    assert result["upper_index"] > 0
