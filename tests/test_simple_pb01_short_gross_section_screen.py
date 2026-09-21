"""The short-block section screen must remain tied to retained case evidence."""

from scripts.simple_pb01_short_gross_section_screen import screen


def test_short_block_reports_both_retained_cases_without_rating():
    result = screen()
    assert set(result["cases"]) == {"a12-left", "k12-right"}
    for case in result["cases"].values():
        assert case["length_mm"] == 152.4
        assert len(case["sections"]) == 20
        assert case["maxima"]["torsion_abs_nmm"]["value"] > 0
        assert case["maxima"]["normal_tension_corner_mpa"]["value"] >= 0
        assert case["maxima"]["transverse_shear_center_mpa"]["value"] >= 0
    assert result["same_topology_full_v4_demand"] is False
    assert result["net_section_stress_mpa"] is None
    assert result["complete_joint_utilization"] is None
    assert result["rating_or_drilling_release"] is False
