import math

import pytest

from scripts.eoere_v9_joint_followup import (
    elastic_steel_index,
    equal_share_row_example,
    nondominated_points,
)


def test_individual_forces_and_equal_share_group_check_agree_without_repeated_reduction():
    example = equal_share_row_example([3, 1], 100, 100)
    assert example["individual_forces"] == [75, 25]
    assert example["distribution_Cg"] == pytest.approx(2/3)
    assert example["individual_index"] == pytest.approx(.75)
    assert example["equal_share_row_index"] == pytest.approx(.75)
    assert example["individual_index_with_repeated_distribution_factor"] == pytest.approx(1.125)


def test_equal_stiffness_row_has_no_distribution_reduction():
    assert equal_share_row_example([1, 1], 100, 100)["distribution_Cg"] == 1.


def test_steel_axial_bending_and_shear_known_answers():
    d, fy = 10., 200.
    area = math.pi*d*d/4
    assert elastic_steel_index(fy*area/2, 0, 0, d, fy) == pytest.approx(1.)
    assert elastic_steel_index(0, fy/2*math.pi*d**3/32, 0, d, fy) == pytest.approx(1.)
    assert elastic_steel_index(0, 0, fy*area/(4*math.sqrt(3)), d, fy) == pytest.approx(1.)


def test_simultaneous_screw_points_do_not_combine_unrelated_case_peaks():
    a, b, c = ({"withdrawal_N": n, "lateral_N": v} for n, v in ((100, 10), (10, 100), (9, 9)))
    assert nondominated_points([a, b, c]) == [a, b]


@pytest.mark.parametrize("values", [(-1, 0, 0, 10, 200), (0, 0, 0, 0, 200), (0, 0, 0, 10, math.nan)])
def test_invalid_material_or_action_is_rejected(values):
    with pytest.raises(ValueError):
        elastic_steel_index(*values)
