import json

import pytest

from fea.compare_rim_sections import DIRECTORY, compare, section


def test_rectangle_properties_and_axis_scaling():
    assert section(2,6)=={"area_mm2":12,"I_normal_mm4":36,
                         "I_lateral_mm4":4,"Z_normal_mm3":12,"Z_lateral_mm3":4}
    a,b=section(2,6),section(2,12)
    assert b["I_normal_mm4"]==8*a["I_normal_mm4"]
    assert b["I_lateral_mm4"]==2*a["I_lateral_mm4"]
    assert b["Z_normal_mm3"]==4*a["Z_normal_mm3"]


@pytest.mark.parametrize("value",[0,-1,float("nan"),float("inf")])
def test_reject_invalid_section(value):
    with pytest.raises(ValueError):
        section(value,10)
    with pytest.raises(ValueError):
        section(10,value)


def test_comparison_matches_cad_depths_and_frozen_results():
    result=compare()
    assert result==json.loads((DIRECTORY/"hybrid_rim_sections.json").read_text())
    assert result["baseline_assumed_E_mpa"]==7000
    ply,ten,twelve=result["sections"]
    assert [p["depth_mm"] for p in (ply,ten,twelve)]==pytest.approx([322.8,234.95,285.75])
    for p in (ply,ten,twelve):
        ratio=p["equal_E_normal_EI_ratio"]
        assert ratio==pytest.approx((p["depth_mm"]/322.8)**3)
        assert p["E_to_match_baseline_normal_EI_mpa"]*ratio==pytest.approx(7000)
        assert p["same_normal_moment_stress_ratio"]==pytest.approx((322.8/p["depth_mm"])**2)
        assert [s["EI_ratio_to_plywood"] for s in p["normal_EI_sensitivity"]]==pytest.approx(
            [ratio*f for f in (.5,1,1.5,2)])
    assert 0<ten["equal_E_normal_EI_ratio"]<twelve["equal_E_normal_EI_ratio"]<1
