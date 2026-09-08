import pytest

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
