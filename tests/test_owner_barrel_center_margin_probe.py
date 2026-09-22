"""Nominal two-duty center-principal/header washer and row sensitivity."""

import pytest

from scripts import owner_barrel_center_margin_probe as probe


@pytest.fixture(scope="module")
def report():
    return probe.build()


def test_fixed_assembly_inventory_and_unchanged_post_pose(report):
    assert report["post_centers_x_mm"] == [-180.0, 180.0]
    assert report["fixed_panel_screw_axes"] == 66
    assert report["retained_old_frame_bolt_axes"] == 12
    assert report["protected_counts"] == {
        "tnuts": 142,
        "hold_hole_and_trial_projection": 142,
        "lights": 132,
        "wires": 131,
        "panel_screws": 66,
        "frame_bolts": 12,
    }
    assert report["header_rear_y_mm"] == pytest.approx(-175.7)
    assert report["backer_rear_y_mm"] == pytest.approx(-124.9)
    assert not report["structural_fit_verified"]
    assert not report["delivered_hardware_fit_verified"]
    assert not report["drilling_released"]
    bound = report["bounded_full_bolt_tip_proof"]
    assert bound["most_forward_rear_row_y_mm"] == pytest.approx(-157.9)
    assert bound["minimum_principal_y_at_tip_z_mm"] == pytest.approx(-150.652126)
    assert bound["tip_y_shortfall_at_most_favorable_row_mm"] == pytest.approx(7.247874)
    assert bound["full_nominal_rear_bolt_tip_misses_principal_for_all_seat_rows"]


def test_positive_reserve_point_and_bounded_row_window(report):
    window = report["washer_22mm_one_mm_reserve_window"]
    assert window["nonempty"]
    assert window["rear_row_y_mm"] == pytest.approx([-163.7, -159.9])
    assert window["forward_row_y_max_mm"] == pytest.approx(-136.9)
    assert window["minimum_row_spacing_mm"] == pytest.approx(23.0)
    trial = report["trials"][0]
    assert trial["washer_od_mm"] == 22.0
    assert "forward_backer_rear_mm" in trial["reserves_mm"]
    assert trial["rows_y_mm"] == pytest.approx([-162.4333333333, -138.1666666667])
    assert trial["washer_seat_cad_opportunity"]
    assert not trial["full_nominal_bolt_bore_contained"]
    assert set(trial["reserves_mm"].values()) == {2.266667}
    assert all(not hits for hits in trial["pair_hits_mm3"].values())
    assert len(trial["bolts"]) == 4
    for bolt in trial["bolts"].values():
        assert bolt["minimum_intended_core_fraction"] == pytest.approx(1.0)
        assert bolt["bolt_barrel_intersection_mm3"] > 400
        assert bolt["washer_to_header_x_edge_mm"] > 0
        assert bolt["washer_to_header_front_edge_mm"] > 0
        assert not bolt["protected_hits_mm3"]
        assert not bolt["unrelated_wood_hits_mm3"]
    rear = [bolt for name, bolt in trial["bolts"].items() if name.endswith("_1")]
    forward = [bolt for name, bolt in trial["bolts"].items() if name.endswith("_2")]
    assert [
        bolt["full_nominal_bore_uncontained_mm3"] for bolt in rear
    ] == pytest.approx([620.281293, 620.281293])
    assert all(not bolt["nominal_bolt_tip_center_in_principal"] for bolt in rear)
    assert all(bolt["full_nominal_bore_uncontained_mm3"] == 0 for bolt in forward)
    assert all(bolt["nominal_bolt_tip_center_in_principal"] for bolt in forward)


def test_larger_washers_reduce_reserve_and_original_has_none(report):
    assert [row["washer_od_mm"] for row in report["trials"]] == [22.0, 23.0, 24.0, 25.4]
    assert [row["balanced_reserve_mm"] for row in report["trials"]] == pytest.approx(
        [2.266667, 1.6, 0.933333, 0.0]
    )
    assert [row["washer_seat_cad_opportunity"] for row in report["trials"]] == [
        True,
        True,
        True,
        False,
    ]
    assert not any(row["full_nominal_bolt_bore_contained"] for row in report["trials"])
    assert report["trials"][-1]["rows_y_mm"] == pytest.approx([-163.0, -137.6])
    assert not probe.row_window(25.4, 0.1)["nonempty"]


def test_ordinary_nominal_length_sensitivity_at_22mm_seat(report):
    sensitivity = report["bolt_length_sensitivity_22mm"]
    assert sensitivity["provisional_required_tip_past_thread_axis_mm"] == 10.0
    assert sensitivity["selected_length"] is None
    assert not sensitivity["retail_qualified"]
    window = sensitivity["necessary_length_window"]
    assert window["minimum_nominal_length_for_provisional_overrun_mm"] == pytest.approx(
        77.751
    )
    assert window["maximum_nominal_length_from_rear_bore_edge_mm"] == pytest.approx(
        108.490628
    )
    trials = sensitivity["trials"]
    assert [trial["bolt_nominal_length_in"] for trial in trials] == [4.0, 4.5, 5.0]
    assert [trial["bolt_nominal_length_mm"] for trial in trials] == pytest.approx(
        [101.6, 114.3, 127.0]
    )
    assert [trial["nominal_geometry_plausible"] for trial in trials] == [
        True,
        False,
        False,
    ]
    assert all(trial["washer_seat_cad_opportunity"] for trial in trials)
    assert all(trial["provisional_axis_overrun_met"] for trial in trials)
    assert [trial["full_nominal_bolt_bore_contained"] for trial in trials] == [
        True,
        False,
        False,
    ]
    for trial, overrun, rear_bore, rear_shaft in zip(
        trials,
        (33.849, 46.549, 59.249),
        (0.0, 77.113647, 620.281293),
        (0.0, 51.387059, 444.645199),
        strict=True,
    ):
        assert len(trial["bolts"]) == 4
        assert all(not hits for hits in trial["pair_hits_mm3"].values())
        for name, bolt in trial["bolts"].items():
            assert bolt["nominal_tip_beyond_thread_axis_mm"] == pytest.approx(overrun)
            assert bolt["provisional_tip_past_axis_allowance_met"]
            assert bolt["bolt_barrel_intersection_mm3"] > 400
            assert not bolt["protected_hits_mm3"]
            assert not bolt["unrelated_wood_hits_mm3"]
            if name.endswith("_1"):
                assert bolt["full_nominal_bore_uncontained_mm3"] == pytest.approx(
                    rear_bore
                )
                assert bolt["embedded_nominal_shaft_uncontained_mm3"] == pytest.approx(
                    rear_shaft
                )
            else:
                assert bolt["full_nominal_bore_uncontained_mm3"] == 0
                assert bolt["embedded_nominal_shaft_uncontained_mm3"] == 0


def test_conflicted_19mm_listing_is_only_nominal_geometry_trial(report):
    lead = report["retail_washer_od_lead_19_05mm"]
    assert lead["retail_dimensions_conflicted"]
    assert "0.868-0.905-in OD" in lead["same_page_hillman_answer"]
    assert not lead["bearing_qualified"]
    assert not lead["delivered_dimensions_verified"]
    trial = lead["trial"]
    assert trial["washer_od_mm"] == pytest.approx(19.05)
    assert trial["washer_thickness_mm"] == pytest.approx(1.5875)
    assert trial["bolt_nominal_length_mm"] == pytest.approx(101.6)
    assert trial["rows_y_mm"] == pytest.approx([-161.9416667, -138.6583333])
    assert set(trial["reserves_mm"].values()) == {4.233333}
    assert trial["nominal_geometry_plausible"]
    assert trial["full_nominal_bolt_bore_contained"]
    assert trial["provisional_axis_overrun_met"]
    assert all(not hits for hits in trial["pair_hits_mm3"].values())
    for bolt in trial["bolts"].values():
        assert bolt["full_nominal_bore_uncontained_mm3"] == 0
        assert bolt["embedded_nominal_shaft_uncontained_mm3"] == 0
        assert not bolt["protected_hits_mm3"]
        assert not bolt["unrelated_wood_hits_mm3"]
