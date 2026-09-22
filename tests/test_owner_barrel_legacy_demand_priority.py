"""Legacy actions rank investigation effort, never qualify a barrel joint."""

import copy
import json

import pytest

from scripts.owner_barrel_legacy_demand_priority import SOURCE, analyze


def test_all_six_historical_cases_are_explicitly_nonadopted():
    result = analyze()
    assert result["inventory"] == {
        "cases": 6,
        "stations": 24,
        "station_case_records": 144,
        "flange_case_records": 288,
        "families": 12,
    }
    assert result["force_priority"][0] == "top_outer"
    assert result["families"]["top_outer"]["max_force_n"]["value"] == pytest.approx(
        1186.590488, abs=1e-5
    )
    assert result["families"]["header_outer_post"]["max_force_n"][
        "value"
    ] == pytest.approx(598.660417, abs=1e-5)
    assert result["new_barrel_joint_forces_solved"] is False
    assert result["historical_actions_adopted_for_barrel_design"] is False
    assert result["structural_released"] is False


def test_missing_station_or_bad_reported_norm_is_rejected():
    payload = json.loads(SOURCE.read_text())
    missing = copy.deepcopy(payload)
    del missing["cases"]["a12-left"]["angles"]["clip_single_top_left_1"]
    with pytest.raises(ValueError, match="station set"):
        analyze(missing)
    bad_norm = copy.deepcopy(payload)
    bad_norm["cases"]["a12-left"]["angles"]["clip_single_top_left_1"]["flanges"][
        "beam"
    ]["force_norm_n"] = 0.0
    with pytest.raises(ValueError, match="force norm"):
        analyze(bad_norm)
