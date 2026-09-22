"""A shifted outer-base tool path is only a bounded geometry finding."""

from scripts.owner_barrel_outer_base_clearance_probe import probe


def test_both_outer_base_duties_are_screened_without_changing_fixed_inventory():
    report = probe()
    assert report["source_id"] == "owner-barrel-outer-base-clearance-probe-v1"
    assert report["inventory"]["fixed_panel_screws"] == 66
    assert report["inventory"]["retained_frame_bolts"] == 12
    assert report["inventory"]["outer_base_stations"] == 2
    assert report["offsets_inward_mm"] == [0.0, 5.0, 10.0, 15.0]
    assert report["nominal_envelopes_mm"]["washer_od"] == 25.4
    assert set(report["candidates"]) == {"0.0", "5.0", "10.0", "15.0"}
    for candidate in report["candidates"].values():
        assert set(candidate["stations"]) == {
            "clip_angle_base_left",
            "clip_angle_base_right",
        }
        assert all(len(row["rows"]) == 2 for row in candidate["stations"].values())
    assert not report["layout_approved"]
    assert not report["drilling_released"]
    assert not report["structural_released"]


def test_inward_shift_resolves_original_outer_post_access_overlap():
    report = probe()
    baseline = report["candidates"]["0.0"]
    small_shift = report["candidates"]["5.0"]
    shifted = report["candidates"]["10.0"]
    assert not baseline["nominal_geometry_screen_clear"]
    assert not small_shift["nominal_geometry_screen_clear"]
    assert shifted["nominal_geometry_screen_clear"]
    assert report["candidates"]["15.0"]["nominal_geometry_screen_clear"]
    for station in ("clip_angle_base_left", "clip_angle_base_right"):
        assert baseline["stations"][station]["outer_post_bolt_access_hits_mm3"]
        assert not small_shift["stations"][station]["outer_post_bolt_access_hits_mm3"]
        assert not shifted["stations"][station]["outer_post_bolt_access_hits_mm3"]
        assert small_shift["stations"][station]["unrelated_wood_hits_mm3"]
        assert all(
            "washer" in name
            for name in small_shift["stations"][station]["unrelated_wood_hits_mm3"]
        )
        assert not shifted["stations"][station]["unrelated_wood_hits_mm3"]
        assert not shifted["stations"][station]["protected_hits_mm3"]
        assert not shifted["stations"][station]["inter_row_hits_mm3"]
        assert all(
            row["nominal_bore_meets_barrel"]
            for row in shifted["stations"][station]["rows"]
        )
        assert all(
            row["provisional_washer_header_seat_fraction"] >= 0.999
            for row in shifted["stations"][station]["rows"]
        )
    assert not any(shifted["neighbor_hits_mm3"].values())
