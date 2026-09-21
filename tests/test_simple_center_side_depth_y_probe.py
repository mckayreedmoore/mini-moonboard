"""Keep the bounded side-cleat co-design result tied to current geometry."""

from scripts.simple_center_side_depth_y_probe import VARIANTS, probe_one


def test_minimum_depth_removes_y_target_but_not_full_cad_conflict():
    result = probe_one(*VARIANTS["minimum_depth_centered"])
    assert result["bore_count"] == 10
    assert result["fixed_screw_count"] == 66
    assert result["inner_kicker_edges_supported"]
    assert result["side_y_conditional_4d_plus_project_5_reserve_mm"] == 0
    assert result["washer_bearing_fraction"]["upright_left"] < 1
    assert not result["nominal_cad_clear"]
    assert not result["whole_center_classification_complete"]
    assert not result["rating_or_drilling_release"]
