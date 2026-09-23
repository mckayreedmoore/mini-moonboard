"""The selected qualification articles stay complete and fail closed."""

import copy

import pytest

from scripts import owner_barrel_selected_hardware as selected


def test_selected_stack_covers_all_barrel_pairs_and_records_strength():
    result = selected.report()
    assert result["selected_bolt_count"] == 48
    assert result["selected_washer_count"] == 48
    assert result["bolt_minimum_proof_load_lbf"] == pytest.approx(2703.0)
    assert result["bolt_minimum_tensile_load_lbf"] == pytest.approx(3816.0)
    assert result["washer_minimum_annular_area_mm2"] == pytest.approx(213.63, 0.01)


def test_current_six_inch_stack_is_rejected_and_design_stays_blocked():
    data = selected.load_selection()
    result = selected.report(data)
    assert result["as_drawn_six_inch_stack"] == "FAIL_CLOSED_NOT_QUALIFIED"
    assert result["complete_design"] == "EVIDENCE_BLOCKED"
    assert data["stack_screen"]["stafast_shifted_bodies_checked"] == 46
    assert data["stack_screen"]["stafast_shifted_body_unrelated_collisions"] == 0
    assert data["stack_screen"][
        "six_and_half_minimum_added_bore_depth_to_zero_clearance_mm"
    ] == pytest.approx(10.4408)
    assert data["stack_screen"][
        "six_and_half_provisional_2mm_clearance_added_bore_depth_mm"
    ] == pytest.approx(12.4408)
    assert data["stack_screen"]["six_and_half_corrected_cad_probe_pair_count"] == 12
    assert (
        data["stack_screen"][
            "six_and_half_corrected_cad_probe_unrelated_or_protected_hits"
        ]
        == 0
    )
    assert data["stack_screen"][
        "five_in_minimum_adverse_clearance_before_machining_error_mm"
    ] == pytest.approx(0.1204)
    assert (
        "complete-joint stiffness and strength qualification"
        in result["blocking_gates"]
    )


def test_missing_barrel_strength_cannot_be_silently_filled():
    data = selected.load_selection()
    changed = copy.deepcopy(data)
    changed["barrel"]["controlled_strength_n"] = 1000
    with pytest.raises(ValueError, match="not controlled"):
        selected.validate_selection(changed)


def test_release_and_inventory_drift_fail_closed():
    data = selected.load_selection()
    changed = copy.deepcopy(data)
    changed["decision"]["diy_ready"] = True
    with pytest.raises(ValueError, match="cannot release"):
        selected.validate_selection(changed)

    changed = copy.deepcopy(data)
    changed["bolts"][0]["quantity"] -= 1
    with pytest.raises(ValueError, match="48 barrel pairs"):
        selected.validate_selection(changed)


def _filled_measurements():
    payload = selected.measurement_template()
    for row in payload["pairs"]:
        row["actual"].update(
            {
                "bolt_length_mm": row["selected_bolt_nominal_length_mm"],
                "male_complete_start_mm": 50.0,
                "male_complete_end_mm": 170.0,
                "installed_thread_axis_from_head_mm": 100.0,
                "female_complete_start_from_axis_mm": -5.0,
                "female_complete_end_from_axis_mm": 5.0,
                "bore_cap_from_head_mm": 180.0,
                "barrel_od_min_mm": 9.98,
                "barrel_od_max_mm": 10.02,
                "finished_bore_min_mm": 10.12,
                "finished_bore_max_mm": 10.18,
                "axis_offset_mm": 0.1,
            }
        )
        row["acceptance"].update(
            {
                "required_engagement_mm": 8.0,
                "minimum_tip_clearance_mm": 2.0,
                "minimum_insertion_clearance_mm": 0.05,
                "maximum_insertion_clearance_mm": 0.25,
                "maximum_axis_offset_mm": 0.2,
            }
        )
    return payload


def test_measurement_template_binds_all_selected_products():
    payload = selected.measurement_template()
    products = {}
    for row in payload["pairs"]:
        products[row["selected_bolt_product"]] = (
            products.get(row["selected_bolt_product"], 0) + 1
        )
    assert products == {
        "1456BHT5": 8,
        "1472BHT5": 24,
        "1480BHT5": 4,
        "14104BHT5": 12,
    }
    pair_ids = {row["pair_id"] for row in payload["pairs"]}
    assert not selected.REPLACED_PRINCIPAL_PAIRS & pair_ids
    assert {row["pair_id"] for row in selected.VERTICAL_PRINCIPAL_PAIRS} <= pair_ids
    result = selected.evaluate_measurements(payload)
    assert result["status"] == "EVIDENCE_BLOCKED"
    assert all(row["missing"] for row in result["results"])


def test_complete_measurements_pass_geometry_only_without_release():
    result = selected.evaluate_measurements(_filled_measurements())
    assert result["status"] == "PASS_GEOMETRY_ONLY"
    assert result["structural_released"] is False
    assert result["diy_ready"] is False
    assert all(not row["failures"] for row in result["results"])


def test_any_measured_fit_failure_forces_no_go():
    payload = _filled_measurements()
    payload["pairs"][0]["actual"]["axis_offset_mm"] = 0.3
    result = selected.evaluate_measurements(payload)
    assert result["status"] == "NO_GO_MEASURED_FIT"
    assert result["results"][0]["failures"] == ["AXIS_MISALIGNMENT_EXCEEDS_LIMIT"]


def test_impossible_measurement_is_rejected():
    payload = _filled_measurements()
    payload["pairs"][0]["actual"]["finished_bore_min_mm"] = -1
    with pytest.raises(ValueError, match="physical dimensions"):
        selected.evaluate_measurements(payload)
