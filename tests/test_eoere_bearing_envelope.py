import numpy as np
import pytest

from scripts.eoere_bearing_envelope import affine_bearing_upper, utilization


def test_angle_factor_can_put_the_true_maximum_between_endpoints():
    first = np.array([-.3709190287, 1, 0])
    last = np.array([.3709190287, 1, 0])
    grain = [1, 0, 0]
    scale = .99/max(utilization(q, grain, 9.525) for q in (first, last))
    result = affine_bearing_upper(scale*first, scale*last, grain, 9.525)
    assert result["endpoint_maximum"] == pytest.approx(.99)
    assert result["sampled_lower"] > 1.015
    assert result["whole_interval_upper"] >= result["sampled_lower"]
    assert result["absolute_gap"] < 2e-8


@pytest.mark.parametrize("plywood", [False, True])
def test_whole_affine_pressure_bound_encloses_independent_dense_samples(plywood):
    rng = np.random.default_rng(745)
    for _ in range(8):
        first, last = rng.normal(0, 80, (2, 3))
        grain = rng.normal(size=3)
        grain /= np.linalg.norm(grain)
        result = affine_bearing_upper(first, last, grain, 9.525, plywood=plywood)
        samples = [utilization(first+t*(last-first), grain, 9.525, plywood=plywood)
                   for t in np.linspace(0, 1, 2001)]
        assert max(samples) <= result["whole_interval_upper"] + 1e-11


def test_zero_pressure_and_origin_crossing_have_no_singularity():
    assert affine_bearing_upper([0, 0, 0], [0, 0, 0], [1, 0, 0], 9.525)["whole_interval_upper"] == 0
    result = affine_bearing_upper([-4, 0, 0], [4, 0, 0], [1, 0, 0], 9.525)
    assert result["whole_interval_upper"] == pytest.approx(utilization([4, 0, 0], [1, 0, 0], 9.525))


def test_invalid_grain_or_diameter_rejected():
    with pytest.raises(ValueError):
        affine_bearing_upper([1, 0, 0], [1, 0, 0], [2, 0, 0], 9.525)
    with pytest.raises(ValueError):
        affine_bearing_upper([1, 0, 0], [1, 0, 0], [1, 0, 0], 0)
