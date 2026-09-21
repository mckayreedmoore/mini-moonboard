"""Integrated PB02 ten-bolt stack sensitivity, with no hardware release."""

import pytest

from scripts.simple_center_pb02_integrated_stack_screen import screen


@pytest.fixture(scope="module")
def result():
    return screen()


def test_working_pose_changes_only_the_two_documented_grips(result):
    assert result["source_commit"] == "e9e4e42"
    rows = result["scenarios"]["current_lengths"]["rows"]
    assert len(rows) == 10
    assert rows["header_cleat"]["wood_grip_mm"] == 105.1
    assert rows["cleat_link"]["wood_grip_mm"] == 99.7
    assert rows["cleat_principal"]["wood_grip_mm"] == 109.05
    assert rows["post_cleat_2"]["wood_grip_mm"] == 177.8
    assert result["grip_changes_from_maintained_pose_mm"] == {
        "header_cleat": -4.0,
        "cleat_link": 4.8,
    }
    assert not result["procurement_or_drilling_released"]
    assert all(not row["actual_thread_nut_washer_verified"] for row in rows.values())


def test_length_scenarios_keep_orientation_collisions_visible(result):
    scenarios = result["scenarios"]
    assert set(scenarios) == {
        "current_lengths",
        "principal_pair_5_5in",
        "principal_pair_6in",
        "link_5_5in",
    }
    assert (
        scenarios["current_lengths"]["rows"]["cleat_link"][
            "minimum_projection_margin_in"
        ]
        > 0
    )
    assert (
        scenarios["principal_pair_5_5in"]["rows"]["header_cleat"]["trial_length_in"]
        == 5.5
    )
    assert (
        scenarios["principal_pair_6in"]["rows"]["cleat_principal"]["trial_length_in"]
        == 6
    )
    assert scenarios["link_5_5in"]["rows"]["cleat_link"]["trial_length_in"] == 5.5
    assert all(len(case["rows"]) == 10 for case in scenarios.values())
    assert scenarios["current_lengths"]["wood_or_fixed_screw_hits_mm3"] == {}
    assert scenarios["principal_pair_5_5in"]["wood_or_fixed_screw_hits_mm3"] == {}
    six_in_hits = scenarios["principal_pair_6in"]["wood_or_fixed_screw_hits_mm3"]
    assert six_in_hits["cleat_principal:principal_cleat_left:tip"]["wood_hits_mm3"] == {
        "cleat_principal:principal_cleat_left:tip/base_principal_center_left": pytest.approx(
            518.98796
        )
    }
    assert all(
        case["modeled_wood_and_fixed_screws_clear_both_orientations"]
        != bool(case["wood_or_fixed_screw_hits_mm3"])
        for case in scenarios.values()
    )


def test_retail_leads_are_exact_documented_skus_and_remain_unselected(result):
    assert set(result["ordinary_store_leads"]) == {
        "800676",
        "9058745",
        "190059",
        "805336",
        "805330",
        "190062",
        "805436",
        "800696",
        "9058821",
    }
    assert result["ordinary_store_leads"]["800696"]["nominal_length_in"] == 8
    assert (
        result["ordinary_store_leads"]["800676"]["product_facts"]["thread_description"]
        == "fully threaded"
    )
    assert all(
        lead["usable_thread_interval_verified"] is False
        for lead in result["ordinary_store_leads"].values()
    )
    assert result["invented_bounds_are_not_product_facts"]
