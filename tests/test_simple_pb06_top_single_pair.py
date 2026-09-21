from scripts import simple_pb06_top_single_pair as trial


def test_top_single_pair_is_source_bound_and_never_released():
    result = trial.screen()
    assert result["target_stations"] == list(trial.TARGET_STATIONS)
    assert result["inventory"] == {
        "existing_blocks": 10,
        "candidate_blocks": 2,
        "candidate_bolts": 8,
        "target_sds_axes_retained": 12,
        "other_sds_axes_retained": 60,
        "frame_axes": 12,
        "panel_kicker_axes": 66,
    }
    assert result["decision"] == "REVISE"
    assert result["minimum_signed_margin_mm"] == -28.575
    for local in result["local"].values():
        assert local["contact_area_mm2"]["upright"] == 0.0
        assert not local["complete_bores"]
        assert local["collision_clear"] and local["access_clear"]
    assert not result["strength_checked"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]
    assert len(result["full_nominal_shaft_lengths_mm"]) == 8
    assert set(result["full_nominal_shaft_lengths_mm"].values()) == {127.0, 203.2}
    assert all(len(row) == 4 for row in result["receiving_member_margins_mm"].values())
