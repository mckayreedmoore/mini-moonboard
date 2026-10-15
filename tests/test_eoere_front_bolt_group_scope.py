import copy
from types import SimpleNamespace

import pytest

from scripts import eoere_front_bolt_group_scope as audit


def fixture():
    shafts = [{"axis_id": str(i), "basis": [[1., 0., 0.]], "point": [0., y, z],
               "diameter_mm": 9.525, "surfaces": [
                   {"host": "post", "kind": "wood", "grain_axis_xyz": [0., 0., 1.], "interval_mm": [0., 38.1]},
                   {"host": "runner", "kind": "wood", "grain_axis_xyz": [0., 1., 0.], "interval_mm": [38.1, 76.2]}]}
              for i, (y, z) in enumerate(((0., 0.), (28., 45.)))]
    helper = SimpleNamespace(THICKNESS=38.1, cross_row_minimum=lambda d: 35.71875)
    return shafts, helper


def test_each_receiver_uses_its_own_grain_and_the_lesser_wood_length():
    shafts, helper = fixture()
    post, runner = audit.pattern(shafts, helper)
    assert post["grain_separation_mm"] == 45.
    assert post["cross_grain_separation_mm"] == 28.
    assert post["perpendicular_marker_grain_margin_mm"] == pytest.approx(9.28125)
    assert post["perpendicular_marker_is_met"] is True
    assert runner["grain_separation_mm"] == 28.
    assert runner["cross_grain_separation_mm"] == 45.
    assert runner["perpendicular_marker_grain_margin_mm"] == pytest.approx(-7.71875)
    assert runner["perpendicular_marker_is_met"] is False
    assert runner["ell_over_D"] == pytest.approx(4.)
    assert post["complete_Cdelta"] is None and runner["complete_Cg"] is None


def test_reversing_both_shaft_directions_and_intervals_preserves_the_pattern():
    shafts, helper = fixture()
    before = audit.pattern(shafts, helper)
    for shaft in shafts:
        shaft["basis"][0] = [-1., 0., 0.]
        for surface in shaft["surfaces"]:
            a, b = surface["interval_mm"]
            surface["interval_mm"] = [-b, -a]
    after = audit.pattern(shafts, helper)
    for original, reversed_row in zip(before, after, strict=True):
        assert reversed_row["cross_grain_axis_xyz"] == [-v for v in original["cross_grain_axis_xyz"]]
        assert {k: v for k, v in reversed_row.items() if k != "cross_grain_axis_xyz"} == {
            k: v for k, v in original.items() if k != "cross_grain_axis_xyz"}


@pytest.mark.parametrize("change", ["duplicate", "different_host", "steel", "wrong_thickness", "nonunit", "nonparallel", "grain_skew", "coincident"])
def test_inapplicable_geometry_is_refused(change):
    shafts, helper = fixture()
    if change == "duplicate": shafts[1]["axis_id"] = shafts[0]["axis_id"]
    elif change == "different_host": shafts[1]["surfaces"][0]["host"] = "other"
    elif change == "steel": shafts[1]["surfaces"][0]["kind"] = "steel"
    elif change == "wrong_thickness": shafts[1]["surfaces"][0]["interval_mm"][1] = 40.
    elif change == "nonunit": shafts[1]["basis"][0] = [2., 0., 0.]
    elif change == "nonparallel": shafts[1]["basis"][0] = [0., 1., 0.]
    elif change == "grain_skew": shafts[1]["surfaces"][0]["grain_axis_xyz"] = [1., 0., 0.]
    elif change == "coincident": shafts[1]["point"] = shafts[0]["point"]
    with pytest.raises(ValueError): audit.pattern(shafts, helper)


def test_signed_actions_and_couples_are_preserved_without_aligning_a_resultant():
    shafts, helper = fixture()
    row = audit.pattern(shafts, helper)[0]
    actions = [{"axis_id": str(i), "receiver": "post", "own_force_xyz_n": [3., 28., 45. if i == 0 else -45.],
                "own_moment_at_aggregate_xyz_nmm": [1., -7., 11.]} for i in range(2)]
    original = copy.deepcopy(actions)
    result = audit.action_scope(row, actions)
    assert result[0]["aligned_with_physical_pair"] is True
    assert result[1]["aligned_with_physical_pair"] is False
    assert result[1]["parallel_grain_signed_n"] == -45.
    assert result[1]["free_couple_at_own_aggregate_xyz_nmm"] == [1., -7., 11.]
    assert actions == original


def test_action_scope_rejects_another_receiver():
    shafts, helper = fixture()
    row = audit.pattern(shafts, helper)[0]
    with pytest.raises(ValueError):
        audit.action_scope(row, [{"axis_id": "0", "receiver": "other"}])


def test_group_uses_original_points_and_free_couples_about_one_origin():
    shafts, helper = fixture()
    row = audit.pattern(shafts, helper)[0]
    actions = [{"axis_id": str(i), "receiver": "post", "own_force_xyz_n": [0., 10., 0.],
                "own_moment_at_aggregate_xyz_nmm": [7., 8., 9.],
                "own_aggregate_point_xyz_mm": [19.05, 28.*i, 45.*i]} for i in range(2)]
    result = audit.group_wrench_scope(row, actions)
    assert result["origin_xyz_mm"] == [19.05, 14., 22.5]
    assert result["force_xyz_n"] == [0., 20., 0.]
    assert result["moment_xyz_nmm"] == [14., 16., 18.]
    assert result["lateral_resultant_aligned_with_physical_pair"] is False
    assert result["complete_Cg"] is None


def test_zero_group_resultant_retains_the_couple_and_has_no_load_direction():
    shafts, helper = fixture()
    row = audit.pattern(shafts, helper)[0]
    actions = [{"axis_id": str(i), "receiver": "post", "own_force_xyz_n": [0., 10.*(1-2*i), 0.],
                "own_moment_at_aggregate_xyz_nmm": [0., 0., 0.],
                "own_aggregate_point_xyz_mm": [19.05, 28.*i, 45.*i]} for i in range(2)]
    result = audit.group_wrench_scope(row, actions)
    assert result["force_xyz_n"] == [0., 0., 0.]
    assert result["moment_xyz_nmm"] == [450., 0., 0.]
    assert result["lateral_resultant_to_physical_pair_sine"] is None
    assert result["lateral_resultant_aligned_with_physical_pair"] is None
