"""The four fixed kicker screws must land in attached integrated posts."""

from scripts.export_owner_barrel_scene import build_integrated_viewer_assembly
from scripts.owner_barrel_integrated_backing import report


def test_backing_duty_transfers_to_posts_but_is_not_strength_qualified():
    result = report(build_integrated_viewer_assembly())
    assert result["status"] == "geometric_receiver_and_post_header_path_only"
    assert result["separate_backer_count"] == 0
    assert result["fixed_center_kicker_screw_count"] == 4
    assert result["post_header_barrel_pair_count"] == 4
    assert set(result["posts"]) == {
        "base_post_center_left",
        "base_post_center_right",
    }
    for post in result["posts"].values():
        assert len(post["kicker_screws"]) == 2
        assert len(post["post_header_bolts"]) == 2
        assert all(row["full_purchased_shaft_in_post"] for row in post["kicker_screws"])
        assert all(row["wood_embed_length_mm"] > 0 for row in post["kicker_screws"])
    assert result["panel_screw_resistance_verified"] is False
    assert result["post_header_joint_resistance_verified"] is False
    assert result["complete_backing_load_path_verified"] is False
