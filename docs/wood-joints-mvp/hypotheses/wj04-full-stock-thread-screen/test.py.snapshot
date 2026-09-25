from __future__ import annotations

from copy import deepcopy

import pytest

from scripts import wood_joint_wj04_full_stock_thread_screen as thread_screen


def test_archived_eight_axis_screen_covers_all_independent_corners() -> None:
    report = thread_screen.build_thread_screen_report()

    assert report["physical_bolt_count"] == 8
    assert report["member_screen_count"] == 16
    assert report["total_corner_evaluations"] == 128
    assert report["total_member_corner_fractions"] == 256
    assert report["all_evaluated_member_corners_within_recorded_limit_at_Lb_boundary"]
    assert report["method"]["corner_count_per_bolt"] == 16
    assert report["method"]["head_and_nut_washers_varied_independently"] is True
    assert report["method"]["wood_layers_varied_independently"] is True
    assert report["method"]["Lg_mm_recorded_but_not_used_as_thread_boundary"] == 133.35
    assert report["hardware_and_fit_status"]["actual_NDS_full_body_diameter_exception_established"] is False
    assert report["hardware_and_fit_status"]["full_smooth_shank_through_every_wood_layer_proven"] is False
    assert report["hardware_and_fit_status"]["nut_fit_or_functional_engagement_verified"] is False

    stack_results = {row["stack_spec_id"]: row for row in report["physical_bolts"]}
    assert set(stack_results) == set(thread_screen.EXPECTED_RECEIVERS_BY_STACK)
    for stack in stack_results.values():
        assert stack["independent_washer_and_layer_corner_count"] == 16
        assert len(stack["corner_results"]) == 16
        assert len(stack["member_screens"]) == 2
        for corner in stack["corner_results"]:
            assert len(corner["receiving_member_results"]) == 2
            assert all(
                member["within_recorded_one_quarter_limit_at_Lb_boundary"]
                for member in corner["receiving_member_results"]
            )


def test_worst_member_fractions_follow_actual_ordered_receiver_layers() -> None:
    report = thread_screen.build_thread_screen_report()
    stacks = {row["stack_spec_id"]: row for row in report["physical_bolts"]}

    lower = stacks["lower_rail_1"]["member_screens"]
    assert [row["member_id"] for row in lower] == [
        thread_screen.CLEAT_LOWER,
        "base_rail_service_lower_right",
    ]
    assert lower[0]["maximum_fraction_after_Lb_boundary"] == 0.0
    assert lower[1]["maximum_bearing_length_after_Lb_boundary_mm"] == pytest.approx(3.032)
    assert lower[1]["maximum_fraction_after_Lb_boundary"] == pytest.approx(
        3.032 / 38.6
    )

    upper_rail = stacks["upper_rail_1"]["member_screens"]
    assert [row["member_id"] for row in upper_rail] == [
        "base_rail_service_upper_right",
        thread_screen.CLEAT_UPPER,
    ]
    assert upper_rail[0]["maximum_fraction_after_Lb_boundary"] == 0.0
    assert upper_rail[1]["maximum_bearing_length_after_Lb_boundary_mm"] == pytest.approx(
        3.032
    )
    assert upper_rail[1]["maximum_fraction_after_Lb_boundary"] == pytest.approx(
        3.032 / 89.4
    )


def test_each_wood_layer_and_both_washers_take_independent_catalog_corners() -> None:
    report = thread_screen.build_thread_screen_report()
    stack = next(
        row for row in report["physical_bolts"] if row["stack_spec_id"] == "lower_rail_1"
    )
    corners = stack["corner_results"]

    assert {tuple(row["wood_layer_thicknesses_head_to_nut_mm"]) for row in corners} == {
        (88.4, 37.6),
        (88.4, 38.6),
        (89.4, 37.6),
        (89.4, 38.6),
    }
    assert {
        (row["head_washer_thickness_mm"], row["nut_washer_thickness_mm"])
        for row in corners
    } == {
        (1.2954, 1.2954),
        (1.2954, 2.032),
        (2.032, 1.2954),
        (2.032, 2.032),
    }


def test_archived_source_correction_and_primary_dimension_basis_are_bound() -> None:
    report = thread_screen.build_thread_screen_report()
    method = report["method"]

    assert method["bolt_dimension_basis"]["correction_note"] == (
        "docs/wood-joints-mvp/bolt-dimension-source-correction.md"
    )
    assert method["bolt_dimension_basis"]["lb_min_mm"] == 127.0
    assert method["bolt_dimension_basis"]["lg_max_mm"] == 133.35
    assert "not used as the dimension source" in method["bolt_dimension_basis"][
        "source_attribution_note"
    ]
    assert report["source"]["mechanics_inputs_sha256"] == (
        thread_screen.MECHANICS_INPUTS_SHA256
    )


def test_mechanics_input_rejects_axis_or_order_changes() -> None:
    document, _archive_evidence = thread_screen.load_archived_mechanics_inputs()

    wrong_axis = deepcopy(document)
    wrong_axis["physical_bolts"][0]["physical_bolt_id"] = "foreign/axis"
    with pytest.raises(ValueError, match="physical bolt IDs"):
        thread_screen._validate_mechanics_input(wrong_axis)

    wrong_order = deepcopy(document)
    row = next(
        row
        for row in wrong_order["physical_bolts"]
        if row["stack_spec_id"] == "upper_rail_1"
    )
    row["receivers_head_to_nut"].reverse()
    with pytest.raises(ValueError, match="ordered member receivers"):
        thread_screen._validate_mechanics_input(wrong_order)

    wrong_lg = deepcopy(document)
    wrong_lg["physical_bolts"][0]["hardware"]["bolt"][
        "maximum_grip_gage_Lg_mm"
    ] = 127.0
    with pytest.raises(ValueError, match="dimensional basis changed"):
        thread_screen._validate_mechanics_input(wrong_lg)
