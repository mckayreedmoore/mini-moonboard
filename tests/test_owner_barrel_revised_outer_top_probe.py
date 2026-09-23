"""The revised-viewer collision screen must never imply a drilling release."""

from scripts.owner_barrel_revised_outer_top_probe import probe


def test_revised_viewer_inventory_and_provisional_stack_are_explicit():
    result = probe()
    assert result["source_id"] == "owner-barrel-revised-outer-top-probe-v1"
    assert (
        result["source_assembly"] == "export_owner_barrel_scene.build_viewer_assembly"
    )
    assert result["inventory"]["stations"] == 8
    assert result["inventory"]["rows"] == 16
    assert result["inventory"]["fixed_panel_screws"] == 66
    assert result["inventory"]["retained_frame_bolts"] == 12
    assert result["inventory"]["viewer_head_washer_rows"] == 16
    assert result["inventory"]["supplemental_provisional_head_washer_rows"] == 0
    assert result["trial_basis"]["hold_rear_projection_is_provisional"]
    assert result["trial_basis"]["delivered_hardware_verified"] is False
    for station in result["stations"].values():
        assert station["disposition"] == "REVISE"
        assert len(station["rows"]) == 2
        for row in station["rows"].values():
            assert {"shaft", "head", "washer", "barrel"} <= set(row["physical_roles"])
            assert {
                "machine_bore",
                "barrel_bore",
                "bolt_access",
                "barrel_access",
            } <= set(row["path_roles"])
            assert row["head_washer_source"] in (
                "viewer",
                "supplemental_provisional_envelope_not_in_viewer",
            )


def test_outer_header_driver_has_two_conditional_rim_states():
    result = probe()
    for side in ("left", "right"):
        station = result["stations"][f"clip_timber_header_outer_{side}"]
        for row in station["rows"].values():
            access = row["outer_header_bolt_driver"]
            assert access["installed_side_rim_hit_mm3"] > 1
            assert access["installed_state"] == "blocked_by_side_rim"
            assert access["rim_removed_state"] == "conditional_unverified"
            assert access["rim_removed_side_rim_excluded"] is True
            assert access["rim_removal_verified"] is False
            assert access["rim_removed_unrelated_wood_hits_mm3"] == {}
            assert row["head_washer_source"] == "viewer"


def test_all_collision_families_are_reported_without_clear_or_release():
    result = probe()
    assert set(result["collision_scope"]) == {
        "fixed_protected",
        "unrelated_wood",
        "same_family_neighbor",
        "cross_family",
    }
    for station in result["stations"].values():
        assert "fixed_protected_hits_mm3" in station
        assert "unrelated_wood_hits_mm3" in station
        assert "same_family_neighbor_hits_mm3" in station
        assert "cross_family_hits_mm3" in station
    assert (
        sum(
            len(hits)
            for station in result["stations"].values()
            for hits in station["unrelated_wood_hits_mm3"].values()
        )
        == 4
    )
    assert all(
        not station["fixed_protected_hits_mm3"]
        and not any(station["same_family_neighbor_hits_mm3"].values())
        and not any(station["cross_family_hits_mm3"].values())
        for station in result["stations"].values()
    )
    assert result["layout_approved"] is False
    assert result["drilling_released"] is False
    assert result["fabrication_released"] is False
    assert result["structural_released"] is False
    assert "clear" not in str(result).lower()
