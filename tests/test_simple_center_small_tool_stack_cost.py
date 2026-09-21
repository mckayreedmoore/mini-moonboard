"""One regression check for the bounded PB-02 stack and price sidecar."""

from scripts.simple_center_small_tool_stack_cost import report


def test_revised_pose_grips_and_basket():
    result = report()
    rows = {row["axis"]: row for row in result["axes"]}
    assert len(rows) == 8
    assert rows["header_cleat"]["wood_grip_mm"] == 99.1
    assert rows["header_cleat"]["trial_bolt_in"] == 5
    assert rows["header_cleat"]["interval_passes"]
    assert rows["cleat_principal"]["projection_margin_in"] == 0.006693
    assert result["trial_bolt_quantities"] == {"5": 3, "6": 3, "8": 2}
    assert result["rejected_pose_141_1_mm_on_6_in"]["passes_assumed_interval"] is False
    assert result["hardware_usd"] == {
        "bolts": "5.87",
        "allocated": "9.17",
        "first_checkout": "9.83",
        "delta_from_published_rejected_pose_basket": "-0.09",
    }
