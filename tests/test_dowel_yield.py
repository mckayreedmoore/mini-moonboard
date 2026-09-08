"""Independent AWC TR12 Example 3.1 benchmark, including every yield mode."""
import pytest

from fea.dowel_yield import single_shear


def example(main=4800., side=4800., gap=0.):
    k = 1. if main == side == 4800 else 1.25
    return {"main_length_in": 1.5, "side_length_in": 1.5,
            "main_bearing_lb_in": main*.5, "side_bearing_lb_in": side*.5,
            "main_yield_moment_lb_in": 45000*.5**3/6,
            "side_yield_moment_lb_in": 45000*.5**3/6, "gap_in": gap,
            "reduction_terms": {"Im": 4*k, "Is": 4*k, "II": 3.6*k,
                                "IIIm": 3.2*k, "IIIs": 3.2*k, "IV": 3.2*k}}


@pytest.mark.parametrize("main,side,gap,expected", [
    (4800, 4800, 0, [900, 900, 414, 550, 550, 663]),
    (4800, 2550, 0, [720, 383, 250, 380, 324, 442]),
    (2550, 2550, 0, [383, 383, 176, 289, 289, 387]),
    (4800, 4800, .25, [900, 900, 370, 482, 482, 576]),
    (4800, 2550, .25, [720, 383, 224, 341, 284, 393]),
    (2550, 2550, .25, [383, 383, 157, 258, 258, 349]),
    (4800, 4800, .5, [900, 900, 333, 426, 426, 501]),
    (4800, 2550, .5, [720, 383, 202, 307, 250, 350]),
    (2550, 2550, .5, [383, 383, 142, 231, 231, 315]),
])
def test_published_example_3_1(main, side, gap, expected):
    result = single_shear(**example(main, side, gap))
    # Published values are rounded to whole pounds-force.
    assert list(result["reference_values_lbf"].values()) == pytest.approx(expected, abs=.51)
    assert result["governing_mode"] == "II"
    assert result["reference_lateral_lbf"] == pytest.approx(min(expected), abs=.51)


@pytest.mark.parametrize("key,value", [("gap_in", -1), ("main_length_in", 0),
    ("side_bearing_lb_in", float("nan")), ("main_yield_moment_lb_in", float("inf")),
    ("reduction_terms", {"Im": 4})])
def test_bad_inputs(key, value):
    inputs = example()
    inputs[key] = value
    with pytest.raises(ValueError):
        single_shear(**inputs)
