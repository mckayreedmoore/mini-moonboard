"""Nominal 6-in/60-mm setback trial on the independent barrel viewer."""

from copy import copy

import pytest

from scripts.owner_barrel_outer_rail_setback_probe import probe
from scripts.simple_owner_duty_ledger import selected_duties


@pytest.fixture(scope="module")
def report():
    return probe()


def test_exact_six_stations_and_fixed_inventory(report):
    expected = {
        name
        for name, duty in selected_duties().items()
        if duty["family"] in {"bottom_outer", "lower_outer", "upper_outer"}
    }
    assert set(report["stations"]) == expected
    assert report["trial_bolt_count"] == 12
    assert report["trial_barrel_setback_from_butt_mm"] == 60
    assert report["trial_bolt_length_mm"] == pytest.approx(152.4)
    assert report["fixed_inventory"]["panel_screws"] == 66
    assert report["fixed_inventory"]["frame_bolts"] == 12


def test_six_in_nominal_tip_inside_barrel_and_bore(report):
    assert report["nominal_geometry_clear"] is True
    assert report["peer_hardware_hits_mm3"] == {}
    for station in report["stations"].values():
        assert station["source_status"] == "DIRECT_TRIAL_GEOMETRY_ONLY"
        assert station["direct_butt_available"]
        assert station["barrels_contained_in_rail"]
        assert station["machine_bore_meets_barrel_bore"]
        assert station["protected_hits_mm3"] == {}
        assert station["unrelated_wood_hits_mm3"] == {}
        assert len(station["rows"]) == 2
        for bolt in station["rows"].values():
            assert bolt["nominal_tip_past_axis_mm"] == pytest.approx(1.849, abs=0.01)
            assert bolt["nominal_tip_to_barrel_far_wall_mm"] == pytest.approx(
                3.1548, abs=0.01
            )
            assert bolt["nominal_tip_to_machine_bore_end_mm"] > 0
            assert bolt[
                "nominal_length_window_for_axis_to_far_wall_mm"
            ] == pytest.approx([150.551, 155.5548], abs=0.01)
            assert bolt["smallest_nominal_longitudinal_margin_mm"] == pytest.approx(
                1.849, abs=0.01
            )


def test_geometry_is_not_hardware_or_drilling_release(report):
    assert report["retail_lead"]["model"] == "805436"
    assert report["selected_hardware"] is False
    assert report["thread_engagement_verified"] is False
    assert report["capacity_verified"] is False
    assert report["drilling_released"] is False
    assert report["fabrication_released"] is False


def test_rejects_changed_viewer_station_inventory():
    from scripts.export_owner_barrel_scene import build_viewer_assembly

    assembly = build_viewer_assembly()
    changed = {**assembly, "station_modes": copy(assembly["station_modes"])}
    station = next(
        name
        for name, duty in selected_duties().items()
        if duty["family"] in {"bottom_outer", "lower_outer", "upper_outer"}
    )
    changed["station_modes"][station] = "not_direct"
    with pytest.raises(ValueError, match="inventory changed"):
        probe(assembly=changed)
