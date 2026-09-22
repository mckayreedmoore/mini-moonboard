"""Outer/top finite-screen evidence cannot silently become a layout release."""

from scripts.owner_barrel_outer_top_protected_probe import probe


def test_exact_owner_assembly_outer_top_screen_keeps_known_wood_conflicts():
    result = probe()
    assert result["source_id"] == "owner-barrel-outer-top-protected-probe-v1"
    assert result["inventory"]["stations"] == 8
    assert result["inventory"]["fixed_panel_screws"] == 66
    assert result["inventory"]["retained_frame_bolts"] == 12
    assert len(result["stations"]) == 8
    assert all(
        not row["fixed_protected_hits_mm3"] for row in result["stations"].values()
    )
    assert all(
        result["stations"][station]["unrelated_wood_hits_mm3"]
        for station in (
            "clip_timber_header_outer_left",
            "clip_timber_header_outer_right",
            "clip_angle_base_left",
            "clip_angle_base_right",
        )
    )
    assert not result["same_family_physical_hits_mm3"]
    assert not result["same_family_path_to_physical_hits_mm3"]
    assert not result["layout_approved"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]
    assert not result["structural_released"]
