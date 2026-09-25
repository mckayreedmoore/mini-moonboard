import copy

import pytest

from scripts.wood_joint_current_patch_resistance_preflight import (
    EXPECTED_INPUT_SHA256,
    InputContractError,
    build_report,
    load_frozen_inputs,
)


def _report():
    inputs, hashes = load_frozen_inputs()
    return build_report(
        inventory=inputs["inventory"],
        classification=inputs["contact_classification"],
        material_map=inputs["material_map"],
        input_hashes=hashes,
    )


def test_current_patch_reports_only_per_seat_wood_bearing_reference():
    report = _report()
    bearing = report["wood_washer_bearing"]

    assert report["candidate"]["wood_member_count"] == 3
    assert report["candidate"]["physical_bolt_count"] == 4
    assert bearing["seat_count"] == 8
    assert bearing["status"] == "conditional_per_seat_wood_reference_only"
    assert bearing["lower_per_seat"]["reference_N"] == pytest.approx(
        920.570210427, rel=1e-10
    )
    assert bearing["upper_per_seat"]["reference_N"] == pytest.approx(
        1019.160310383, rel=1e-10
    )
    assert len(bearing["seats"]) == 8
    assert all(
        row["result_state"] == "CONDITIONAL_WOOD_BEARING_REFERENCE_ONLY"
        and row["pressure_or_preload_established"] is False
        for row in bearing["seats"]
    )
    assert "total_reference" not in bearing


def test_group_pitch_is_reported_as_geometry_without_nds_disposition():
    groups = _report()["two_bolt_group_geometry"]

    assert len(groups) == 2
    expected_pitch_angles = {
        "bottom_center_right_cleat_to_base_rail_bottom_right": {
            "bottom_center_right_cleat": 0.0,
            "base_rail_bottom_right": 90.0,
        },
        "bottom_center_right_cleat_to_base_principal_center_right": {
            "bottom_center_right_cleat": 90.0,
            "base_principal_center_right": 0.0,
        },
    }
    for group in groups:
        assert group["bolt_center_pitch_mm"] == pytest.approx(33.0, abs=1e-6)
        assert group["pitch_over_modeled_shaft_diameter"] == pytest.approx(
            33 / 6.35, rel=1e-8
        )
        assert group["classification"] == "GEOMETRY_ONLY_NO_NDS_SPACING_OR_GROUP_PASS"
        assert all(
            receiver["bolt_axis_to_declared_grain_angle_degrees"]
            == pytest.approx(90.0, abs=1e-6)
            for receiver in group["receiver_axis_grain_geometry"]
        )
        for receiver in group["receiver_axis_grain_geometry"]:
            assert receiver[
                "bolt_group_pitch_to_declared_grain_angle_degrees"
            ] == pytest.approx(
                expected_pitch_angles[group["interface_id"]][
                    receiver["wood_member_id"]
                ],
                abs=1e-6,
            )


def test_dowel_yield_and_joint_acceptance_remain_open():
    report = _report()

    dowel = report["resistance_gates"]["NDS_dowel_yield_and_member_bearing"]
    assert dowel["status"] == "unresolved"
    assert any("Dr" in item for item in dowel["missing_resistance_inputs"])
    assert any("ASTM F1575" in item for item in dowel["missing_resistance_inputs"])
    assert any(
        "fresh per-bolt" in item for item in dowel["later_demand_and_response_inputs"]
    )
    thread_screen = dowel["member_thread_fraction_limits"]
    assert (
        thread_screen["status"]
        == "NDS_THREAD_FRACTION_LIMITS_COMPUTED_OCCUPANCY_UNVERIFIED"
    )
    assert len(thread_screen["per_bolt_member_limits"]) == 4
    for bolt in thread_screen["per_bolt_member_limits"]:
        limits = {
            row["wood_member_id"]: row[
                "maximum_thread_bearing_length_for_full_body_D_mm"
            ]
            for row in bolt["members"]
        }
        assert limits["bottom_center_right_cleat"] == pytest.approx(22.225)
        assert sorted(limits.values()) == pytest.approx([9.525, 22.225])
    assert report["demand_and_acceptance"]["joint_adequacy_claim"] is False
    assert report["demand_and_acceptance"]["criteria_passed"] == []
    assert (
        report["demand_and_acceptance"]["historical_demands_or_capacities_imported"]
        is False
    )


def test_missing_wood_washer_seat_fails_closed():
    inputs, hashes = load_frozen_inputs()
    classification = copy.deepcopy(inputs["contact_classification"])
    classification["hardware_seats"] = [
        row
        for row in classification["hardware_seats"]
        if row.get("seat_kind") != "nut_washer_to_last_receiver"
        or row.get("physical_bolt_id", "").endswith("rail_2")
    ]

    with pytest.raises(InputContractError, match="expected eight"):
        build_report(
            inventory=inputs["inventory"],
            classification=classification,
            material_map=inputs["material_map"],
            input_hashes=hashes,
        )


def test_nonfrozen_input_hashes_are_rejected():
    inputs, hashes = load_frozen_inputs()
    hashes["inventory"] = "0" * 64

    with pytest.raises(InputContractError, match="unexpected hash for inventory"):
        build_report(
            inventory=inputs["inventory"],
            classification=inputs["contact_classification"],
            material_map=inputs["material_map"],
            input_hashes=hashes,
        )


def test_expected_hash_binding_is_explicit_for_all_manifests():
    _, hashes = load_frozen_inputs()

    assert hashes == EXPECTED_INPUT_SHA256
