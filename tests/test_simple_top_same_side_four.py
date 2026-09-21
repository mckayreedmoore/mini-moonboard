"""Four top duties need a source-bound, layout-only common block screen."""

import pytest

from scripts import simple_top_same_side_four as trial


def test_four_top_duties_and_fixed_source_are_preserved():
    result = trial.screen()
    assert result["target_stations"] == list(trial.TARGET_STATIONS)
    assert result["inventory"]["candidate_blocks"] == 4
    assert result["inventory"]["candidate_bolts"] == 16
    assert result["inventory"]["removed_target_sds_axes"] == 24
    assert result["inventory"]["fixed_panel_kicker_axes"] == 66
    assert result["source_preserved"]
    assert result["block_local_n_mm"] == 139.7
    assert result["minimum_nominal_block_washer_edge_ligament_mm"] == pytest.approx(
        22.3
    )
    gates = result["protected_3d_gates"]
    assert gates["panel_screw_modeled_shaft_axes"] == "screened_66"
    assert gates["retained_frame_bolt_modeled_shaft_axes"] == "screened_12"
    assert gates["hold_bodies_and_tnuts"] == "unverified_no_solids"
    assert gates["led_bodies_and_wiring"] == "unverified_no_solids"
    assert not result["native_solve"]
    assert not result["drilling_released"]
    assert not result["fabrication_released"]


def test_every_trial_block_contacts_both_actual_members():
    result = trial.screen()
    for row in result["stations"].values():
        assert row["contact_area_mm2"]["upright"] > 0
        assert row["contact_area_mm2"]["rail"] > 0
        assert len(row["complete_bores_by_bolt"]) == 4
        assert all(row["complete_bores_by_bolt"].values())


def test_collision_and_access_are_not_hidden():
    result = trial.screen()
    assert result["decision"] == "ADVANCE_GEOMETRY_ONLY"
    assert not result["obstructions"]
    assert result["smallest_exception"] is None
