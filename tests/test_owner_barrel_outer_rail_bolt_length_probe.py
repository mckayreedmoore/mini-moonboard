"""Preserved length sensitivity on the historical 70-mm outer-rail axes."""

from copy import copy

import pytest

from scripts.owner_barrel_outer_rail_bolt_length_probe import historical_assembly, probe
from scripts.simple_owner_duty_ledger import selected_duties


@pytest.fixture(scope="module")
def result():
    return probe()


def test_historical_70mm_ownership_and_fixed_inventory(result):
    expected = {
        name
        for name, duty in selected_duties().items()
        if duty["family"] in {"bottom_outer", "lower_outer", "upper_outer"}
    }
    assert len(expected) == 6
    assert set(result["stations"]) == expected
    assert len(result["bolts"]) == 12
    assert result["viewer_pose"]["outer_header_forward_y_mm"] == -85.0
    assert result["fixed_inventory"]["panel_screws"] == 66
    assert result["fixed_inventory"]["frame_bolts"] == 12
    assert result["fixed_inventory"]["tnuts"] == 142
    assert result["fixed_inventory"]["lights"] == 132
    assert result["fixed_inventory"]["wires"] == 131
    assert all(len(row["bolt_names"]) == 2 for row in result["stations"].values())
    assert result["selected_hardware"] is False
    assert result["drilling_released"] is False


def test_length_reach_far_side_and_bore_extension(result):
    for bolt in result["bolts"].values():
        assert bolt["modeled_5in_shortfall_mm"] == pytest.approx(33.551, abs=0.01)
        six, seven = bolt["alternatives"]["6_in"], bolt["alternatives"]["7_in"]
        assert six["nominal_length_mm"] == pytest.approx(152.4)
        assert seven["nominal_length_mm"] == pytest.approx(177.8)
        assert six["tip_past_assumed_barrel_axis_mm"] == pytest.approx(-8.151, abs=0.01)
        assert seven["tip_past_assumed_barrel_axis_mm"] == pytest.approx(
            17.249, abs=0.01
        )
        assert bolt["modeled_barrel_far_wall_from_start_mm"] == pytest.approx(
            165.5548, abs=0.001
        )
        assert six["tip_past_modeled_barrel_far_wall_mm"] == pytest.approx(
            -13.1548, abs=0.001
        )
        assert seven["tip_past_modeled_barrel_far_wall_mm"] == pytest.approx(
            12.2452, abs=0.001
        )
        assert seven["nominal_tip_beyond_modeled_barrel_body"] is True
        assert six["reaches_assumed_barrel_axis"] is False
        assert seven["reaches_assumed_barrel_axis"] is True
        assert six["required_machine_bore_extension_mm"] == 0
        assert seven["required_machine_bore_extension_mm"] == pytest.approx(
            10.2452, abs=0.001
        )
        assert seven["modeled_bore_depth_past_nominal_tip_mm"] == 0
        assert seven["remaining_receiving_wood_to_far_side_mm"] == pytest.approx(
            954.001 if bolt["station"].endswith("left_1") else 950.826,
            abs=0.001,
        )
        assert (
            seven["remaining_receiving_wood_to_far_side_mm"]
            < six["remaining_receiving_wood_to_far_side_mm"]
        )
        assert six["tip_inside_receiving_wood"]
        assert seven["tip_inside_receiving_wood"]


def test_screen_records_all_envelope_families_without_release(result):
    for bolt in result["bolts"].values():
        for alternative in bolt["alternatives"].values():
            assert set(alternative["shaft_hits_mm3"]) == {
                "unrelated_wood",
                "fixed_protected",
                "neighbor_viewer_hardware",
            }
            assert set(alternative["bore_extension_hits_mm3"]) == {
                "unrelated_wood",
                "fixed_protected",
                "neighbor_viewer_hardware",
            }
            assert all(not hits for hits in alternative["shaft_hits_mm3"].values())
            assert all(
                not hits for hits in alternative["bore_extension_hits_mm3"].values()
            )
            assert alternative["bore_extension_outside_receiving_wood_mm3"] == 0
    assert result["retail_lead"]["model"] == "807396"
    assert result["modeled_bore_diameter_mm"] == pytest.approx(7.5)
    assert result["modeled_shaft_diameter_mm"] == pytest.approx(6.35)
    assert result["modeled_radial_bore_clearance_mm"] == pytest.approx(0.575)
    assert result["thread_engagement_verified"] is False
    assert result["delivered_length_verified"] is False


def test_probe_rejects_missing_exact_station_owner(result):
    assembly = historical_assembly()
    changed = {**assembly, "bolt_station": copy(assembly["bolt_station"])}
    name = next(iter(result["bolts"]))
    changed["bolt_station"][name] = "clip_horizontal_lower_center_1"
    with pytest.raises(ValueError, match="ownership"):
        probe(assembly=changed)
