import copy
from fractions import Fraction

import pytest

from scripts import eoere_two_member_group_bound as audit


def shafts():
    return [{"axis_id": str(i), "basis": [[1., 0., 0.]], "point": [0., float(i)*40., 0.],
             "diameter_mm": 9.525, "surfaces": [
                 {"kind": "wood", "host": "main", "interval_mm": [0., 38.1]},
                 {"kind": "steel", "host": "plate", "interval_mm": [-6.35, 0.]}]} for i in range(2)]


def test_complete_pair_and_wood_wood_variant_are_bound_without_guessing_EA():
    data = shafts(); before = copy.deepcopy(data)
    row = audit.ordinary_groups(data)[0]
    assert row["Cg_equation_lower_bound"] == .5 and row["actual_Cg"] is None
    assert row["physical_axis_ids"] == ["0", "1"] and data == before
    for shaft in data: shaft["surfaces"][1]["kind"] = "wood"
    assert audit.ordinary_groups(data)[0]["Cg_equation_lower_bound"] == .5


@pytest.mark.parametrize("change", ["omitted", "third", "mixed", "coincident", "different_diameter", "nonparallel", "empty_bearing"])
def test_unproved_pair_premises_fail_closed(change):
    data = shafts()
    if change == "omitted": data.pop()
    elif change == "third": data.append({**copy.deepcopy(data[0]), "axis_id": "2", "point": [0., 80., 0.]})
    elif change == "mixed":
        other = {**copy.deepcopy(data[0]), "axis_id": "2", "point": [0., 80., 0.]}
        other["surfaces"].append({"kind": "steel", "host": "other_plate", "interval_mm": [-12.7, -6.35]})
        data.append(other)
    elif change == "coincident": data[1]["point"] = [20., 0., 0.]
    elif change == "different_diameter": data[1]["diameter_mm"] = 12.7
    elif change == "nonparallel": data[1]["basis"][0] = [0., 1., 0.]
    elif change == "empty_bearing": data[1]["surfaces"][0]["interval_mm"] = [0., 0.]
    with pytest.raises(ValueError): audit.ordinary_groups(data)


def test_separate_fittings_are_not_merged_into_a_four_fastener_row():
    first, second = shafts(), shafts()
    for s in second:
        s["axis_id"] += "b"
        s["surfaces"][1]["host"] = "independent_plate"
    assert len(audit.ordinary_groups([*first, *second])) == 2


@pytest.mark.parametrize("m", [Fraction(1, 100), Fraction(1, 2), Fraction(99, 100)])
@pytest.mark.parametrize("r", [Fraction(1, 100), Fraction(1, 2), Fraction(1)])
def test_exact_original_NDS_algebra_and_both_bound_certificates(m, r):
    original = m*(1-m**4)/(2*((1+r*m**2)*(1+m)-1+m**4))*(1+r)/(1-m)
    denominator = 2*(1+(r-1)*m+m*m)
    reduced = (1+r)*(1+m*m)/denominator
    assert original == reduced
    assert reduced-Fraction(1, 2) == (r*(1+m*m)+(1-r)*m)/denominator >= 0
    assert 1-reduced == (1-r)*(1-m)*(1-m)/denominator >= 0


def test_component_comparison_preserves_demand_and_records_conservative_exceedance():
    source = {"lateral_demand_n": 6., "unadjusted_component_Z_n": 10., "V_over_unadjusted_component_Z": .6}
    result = audit.component_comparison(source, .5)
    assert result["lateral_demand_n"] == 6.
    assert result["Cg_bound_only_reference_index"] == 1.2
    assert result["Cg_bound_only_reference_exceeded"] is True
    assert result["complete_adjusted_joint_reference_n"] is None


def test_changed_original_ratio_is_not_reinterpreted_as_a_new_result():
    with pytest.raises(ValueError):
        audit.component_comparison({"lateral_demand_n": 6., "unadjusted_component_Z_n": 10.,
                                    "V_over_unadjusted_component_Z": .4}, .5)
