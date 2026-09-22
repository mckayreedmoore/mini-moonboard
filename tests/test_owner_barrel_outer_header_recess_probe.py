"""A recessed outer-header bolt is only a conditional geometry lead."""

from scripts.owner_barrel_outer_header_recess_probe import probe


def test_recessed_head_removes_installed_rim_clash_but_not_release():
    result = probe()
    assert result["inventory"]["rows"] == 4
    assert result["inventory"]["fixed_panel_screws"] == 66
    assert result["inventory"]["retained_frame_bolts"] == 12
    assert result["trial"]["head_below_header_top_mm"] > 0
    assert result["trial"]["counterbore_diameter_mm"] >= result["trial"]["washer_od_mm"]
    for row in result["rows"].values():
        assert row["original_shaft_side_rim_hit_mm3"] > 1
        assert row["recessed_stack_side_rim_hit_mm3"] == 0
        assert row["counterbore_side_rim_hit_mm3"] == 0
        assert row["machine_bore_meets_barrel"]
        assert row["tip_beyond_barrel_axis_mm"] > 0
        assert row["counterbore_header_coverage"] > 0.999
        assert row["tool_side_rim_hit_when_assembled_mm3"] > 1
        assert not row["tool_other_wood_hits_with_rim_removed_mm3"]
        assert not row["fixed_protected_hits_mm3"]
        assert not row["unrelated_wood_hits_mm3"]
        assert not row["neighbor_hardware_hits_mm3"]
        assert row["counterbore_header_side_margin_mm"] > 0
    assert not result["drilling_released"]
    assert not result["fabrication_released"]
    assert not result["structural_released"]
