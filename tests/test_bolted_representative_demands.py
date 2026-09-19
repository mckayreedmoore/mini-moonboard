"""Archived demands may guide prototypes but may not qualify them."""

from scripts.bolted_candidate_representative_demands import report


def test_representative_archived_demands_are_explicitly_nonadopted() -> None:
    result = report()
    assert result["status"] == "historical_screen_only"
    assert result["capacity_adopted"] is False
    assert result["new_candidate_native_loads_available"] is False
    assert result["case_count"] == 6
    assert len(result["stations"]) == 3
    assert result["stations"]["clip_split_base_center_left"]["geometry_reconciled"] is False
    assert result["stations"]["clip_split_base_center_left"]["archived_to_current_y_shift_mm"] == 10.1
    for station in result["stations"].values():
        for flange in station["flanges"].values():
            assert flange["maximum_force_norm_n"] > 0
            assert flange["maximum_moment_norm_nmm"] > 0
            assert flange["force_case"] in result["case_order"]
            assert flange["moment_case"] in result["case_order"]
