"""The bounded PB-02 purchase screen keeps quantities and checkout distinct."""

from scripts.simple_center_combined_cost_screen import report


def test_combined_pose_counts_cuts_and_illustrative_hardware():
    result = report()
    assert result["members"]["4x4"]["cut_lengths_mm"] == [238.9, 183.0, 128.9]
    assert result["members"]["4x4"]["remainder_mm"] == 1878.0
    assert result["members"]["2x4"]["remainder_mm"] == 1975.2
    assert result["members"]["4x6"]["cut_lengths_mm"] == [238.9, 145.0]
    assert result["members"]["4x6"]["remainder_mm"] == 2048.1
    assert result["hardware_counts"] == {
        "inherited_post": 2,
        "inherited_link": 1,
        "inherited_upright": 1,
        "new_post_to_header_side_cleat": 1,
        "new_side_cleat_to_header": 1,
        "new_header_to_principal_side_cleat": 1,
        "new_principal_side_cleat_to_principal": 1,
        "total_1_4_bolts": 8,
        "nuts": 8,
        "washers": 16,
    }
    assert result["illustrative_bolt_lengths_qty"] == {
        "5_in": 2,
        "6_in": 4,
        "8_in": 2,
    }
    assert result["example_hardware_usd"]["allocated"] == "9.26"
    assert result["example_hardware_usd"]["first_checkout"] == "9.92"
    assert result["principal_cleat_rips"]["x_offcut_mm"] == 14.75
    assert result["principal_cleat_rips"]["z_offcut_mm"] == 33.5
