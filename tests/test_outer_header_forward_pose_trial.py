"""Focused invariants for the detached outer-header forward-pose trial."""

from scripts import outer_header_forward_pose_trial as trial


def test_forward_pose_reports_both_mirrors_and_all_gates():
    report = trial.screen()
    assert report["source_inventory"] == {
        "panel_kicker_axes": 66,
        "frame_bolt_axes": 12,
    }
    assert report["center_posts_x_mm"] == [-180.0, 180.0]
    assert set(report["sides"]) == {"left", "right"}
    for row in report["sides"].values():
        assert row["block_y_mm"] == [-120.0, -40.0]
        assert row["local_n_mm"] <= 139.7
        assert row["inside_rear_2x6_envelope"]
        assert row["post_contact_mm2"] > 0
        assert row["header_contact_mm2"] > 0
        assert all(row["host_bore_coverage"].values())
        assert not row["outer_base_stack_hits_mm3"]
        assert not row["outer_base_tool_hits_mm3"]
        assert not row["cross_scene_hits_mm3"]
    assert not report["sides"]["left"]["finite_protected_hits_mm3"]
    assert report["sides"]["right"]["finite_protected_hits_mm3"] == {
        "block": {
            "hold_hole_and_trial_projection": {
                "hold_tnut_kicker_10": 66.429933,
            }
        }
    }
    assert report["decision"] == "REVISE"
    assert report["drilling_released"] is False
    assert report["structural_released"] is False
