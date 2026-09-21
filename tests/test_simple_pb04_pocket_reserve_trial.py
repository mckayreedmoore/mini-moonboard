"""Direct geometry-only check of the detached PB04 pocket-depth trial."""

import pytest

from scripts import simple_pb04_pocket_reserve_trial as trial


def test_one_mm_trial_preserves_source_and_clears_geometry():
    result = trial.screen()
    assert result["source_id"] == "pb04-upper-edge-plus-outer-counterbores-v1"
    assert result["inventory"] == {"outer_blocks": 6, "pockets": 12, "panel_axes": 66}
    assert result["pocket_diameter_mm"] == pytest.approx(25.4)
    assert result["original"]["depth_mm"] == pytest.approx(36.9824)
    assert result["deeper"]["depth_mm"] == pytest.approx(37.9824)
    assert result["original"]["nominal_length_margin_mm"] == pytest.approx(0)
    assert result["deeper"]["nominal_length_margin_mm"] == pytest.approx(1)
    assert result["deeper"]["wood_grip_mm"] == pytest.approx(190.6176)
    assert result["deeper"]["axial_wood_beyond_pocket_mm"] == pytest.approx(101.7176)
    assert (
        result["deeper"]["net_block_volume_mm3"]
        < result["original"]["net_block_volume_mm3"]
    )
    assert result["deeper"]["minimum_pocket_to_other_bore_mm"] > 0
    assert result["deeper"]["minimum_pocket_to_other_stack_mm"] > 0
    assert result["deeper"]["minimum_between_pockets_mm"] > 0
    assert result["deeper"]["pocket_to_block_edge_mm"] == pytest.approx(15.875)
    for key, original in result["original"]["stacks"].items():
        deeper = result["deeper"]["stacks"][key]
        for moved in (
            "far_washer_start_from_head_mm",
            "nut_start_from_head_mm",
            "socket_start_from_head_mm",
        ):
            assert deeper[moved] == pytest.approx(original[moved] - 1)
        for fixed in (
            "near_washer_start_from_head_mm",
            "tool_start_from_head_mm",
            "bolt_tip_from_head_mm",
        ):
            assert deeper[fixed] == pytest.approx(original[fixed])
    assert all(result[case]["geometry_clear"] for case in ("original", "deeper"))
    assert result["decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert result["manufacturing_tolerance_verified"] is False
    assert result["structural_released"] is False


def test_nonpositive_or_nonfinite_extra_depth_rejected():
    for extra in (0, -1, float("nan"), float("inf")):
        with pytest.raises(ValueError, match="positive finite"):
            trial.screen(extra_depth_mm=extra)
