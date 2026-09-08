import pytest

from fea.dowel_yield import single_shear
from fea.leg_bolt_reference import build


def test_actual_stack_and_conditional_reference():
    result = build()
    assert len(result["rows"]) == 8
    assert len({r["connection"] for r in result["rows"]}) == 8
    for row in result["rows"]:
        assert row["bolt_length_mm"] == pytest.approx(95.25)
        assert row["reference_thread_length_mm"] == pytest.approx(25.4)
        assert [m["bearing_length_mm"] for m in row["members"]] == pytest.approx([38.1, 19.05, 19.05])
        assert [m["threaded_bearing_mm"] for m in row["members"]] == pytest.approx([0, 0, 8.382])
        assert row["members"][2]["threaded_fraction"] == pytest.approx(.44)
        assert not row["members"][2]["nominal_quarter_length_condition"]
        inputs = row["conditional_bonded_laminate_inputs"]
        assert inputs["main_length_in"] == pytest.approx(1.5)
        assert inputs["side_length_in"] == pytest.approx(1.5)
        assert inputs["side_bearing_lb_in"] == pytest.approx(5600*.298)
        assert row["governing_mode"] == "IIIm"
        assert row["conditional_reference_lateral_n"] == pytest.approx(797.6155904451)


def test_steel_strength_alone_reaches_bearing_mode_ceiling():
    # Supplied-input sensitivity, not assignment of a purchased bolt grade.
    inputs = build()["rows"][0]["conditional_bonded_laminate_inputs"]
    baseline = single_shear(**inputs)
    ceiling = baseline["reference_values_lbf"]["II"]
    assert ceiling*4.4482216152605 == pytest.approx(840.7878584403)
    for assumed_fyb in (90000, 120000):
        changed = dict(inputs, main_yield_moment_lb_in=assumed_fyb*.298**3/6,
                       side_yield_moment_lb_in=assumed_fyb*.298**3/6)
        result = single_shear(**changed)
        assert result["governing_mode"] == "II"
        assert result["reference_lateral_lbf"] == pytest.approx(ceiling)
        assert result["reference_values_lbf"]["II"] == baseline["reference_values_lbf"]["II"]
