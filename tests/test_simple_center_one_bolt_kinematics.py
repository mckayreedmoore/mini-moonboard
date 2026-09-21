"""Frictionless center-corner point law must expose unresisted face twist."""

from scripts.simple_center_one_bolt_kinematics import screen


def test_each_one_bolt_face_has_free_point_model_twist():
    result = screen()
    assert set(result["interfaces"]) == {
        "post_cleat",
        "cleat_header",
        "header_cleat",
        "cleat_principal",
    }
    for row in result["interfaces"].values():
        assert row["one_bolt_rank_with_axial"] == 5
        assert row["one_bolt_rank_without_axial"] == 5
        assert row["face_normal_twist_null_residual"] < 1e-10
        assert row["two_bolt_rank_with_one_axial"] == 6
    assert result["physical_joint_failure_claimed"] is False
    assert result["rating_or_drilling_release"] is False
