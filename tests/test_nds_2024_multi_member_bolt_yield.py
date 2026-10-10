"""NDS-2024 multi-member individual-bolt yield method boundary tests."""

import hashlib
import math
from pathlib import Path

import pytest

from mini_moonboard.nds_2024_multi_member_bolt_yield import (
    CURRENT_MANIFEST_FILE_SHA256,
    CURRENT_MANIFEST_PATH,
    NDS_EDITION,
    _reduction_terms,
    calculate_multi_member_bolt_reference,
    inspect_current_candidate_axis,
)


def source_ref(name):
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    return {"path": f"synthetic://{name}", "locator": "fixture-only", "sha256": digest}


def case(member_count=4):
    members = []
    for index in range(member_count):
        if member_count % 2 == 0:
            force = 100.0 if index % 2 == 0 else -100.0
        else:
            force = 100.0 if index % 2 == 0 else -200.0
        members.append({
            "member_id": f"m{index}",
            "material_class": "solid_sawn_lumber",
            "bearing_length_in": 1.5,
            "specific_gravity": 0.43,
            "specific_gravity_source": source_ref(f"wood-G-{index}"),
            "grain_orientation_source": source_ref(f"grain-vector-{index}"),
            "bearing_length_source": source_ref(f"bearing-length-{index}"),
            "load_to_grain_degrees": 0.0,
            "bolt_axis_perpendicular_to_grain": True,
            "thread_bearing_length_in": 0.0,
            "lateral_force_lbf": force,
        })
    result = {
        "standard_edition": NDS_EDITION,
        "geometry_revision_id": "synthetic-mechanics-fixture-only",
        "axis_id": "synthetic-axis-not-a-candidate",
        "geometry_axis_source": source_ref("axis-geometry"),
        "stack_order_source": source_ref("ordered-stack"),
        "members": members,
        "adjacent_face_gaps_in": [0.0] * (member_count - 1),
        "action_source": source_ref("member-actions"),
        "load_normal_to_bolt_axis": True,
        "minimum_spacing_end_edge_verified": True,
        "spacing_end_edge_source": source_ref("spacing-end-edge-review"),
        "bolt": {
            "kind": "bolt",
            "nominal_diameter_in": 0.5,
            "root_diameter_in": 0.4,
            "threaded": True,
            "bending_yield_strength_psi": 45_000.0,
            "product_source": source_ref("bolt-product"),
            "fyb_basis": source_ref("bolt-fyb"),
        },
    }
    result["bolt"]["fyb_basis"]["test_basis"] = "ASTM_F1575"
    if member_count % 2 == 0:
        result["adjacent_pair_roles"] = [
            {"main_member_id": f"m{i + 1}", "side_member_id": f"m{i}"}
            for i in range(member_count - 1)
        ]
    return result


def test_even_four_member_chain_uses_all_six_single_shear_modes_and_nds_multiplier():
    inputs = case(4)
    result = calculate_multi_member_bolt_reference(inputs)

    # AWC TR12 Example 3.1 is the independent zero-gap single-shear answer:
    # lm=ls=1.5 in, D=0.5 in, Fyb=45 ksi, Fe||=4,800 psi. G=0.43 in
    # this fixture resolves to 4,800 psi under NDS Table 12.3.3 rounding.
    expected_modes = {
        "Im": 900.0,
        "Is": 900.0,
        "II": 414.0,
        "IIIm": 550.0,
        "IIIs": 550.0,
        "IV": 663.0,
    }
    assert result["status"] == "conditional_reference_calculated"
    assert result["procedure"] == "NDS-2024-12.3.8.1-even-member-min-pair-times-n-over-2"
    assert result["analysis_count"] == 3
    assert result["nds_member_count_multiplier"] == 2
    for analysis in result["analysis_results"]:
        assert analysis["yield_values_lbf"] == pytest.approx(expected_modes, abs=0.51)
        assert analysis["reference_z_lbf"] == pytest.approx(414.0, abs=0.51)
    assert result["reference_lateral_lbf"] == pytest.approx(828.0, abs=1.02)
    assert result["adjusted_capacity_lbf"] is None
    assert result["criterion_disposition"] == "pending"
    assert result["capacity_or_pass_claim"] is False


def test_two_member_current_interface_uses_all_six_single_shear_modes():
    inputs = case(2)
    result = calculate_multi_member_bolt_reference(inputs)
    assert result["status"] == "conditional_reference_calculated"
    assert result["procedure"] == "NDS-2024-12.3.1A-two-member-single-shear-all-six-modes"
    assert result["analysis_count"] == 1
    assert result["analysis_results"][0]["shear_plane_ids"] == ["m0|m1"]
    assert result["analysis_results"][0]["yield_values_lbf"] == pytest.approx({
        "Im": 900.0, "Is": 900.0, "II": 414.0,
        "IIIm": 550.0, "IIIs": 550.0, "IV": 663.0,
    }, abs=0.51)
    assert result["reference_lateral_lbf"] == pytest.approx(414.0, abs=0.51)
    assert result["criterion_disposition"] == "pending"


def test_three_member_symmetric_double_shear_matches_nds_published_table():
    inputs = case(3)
    for member in inputs["members"]:
        member["specific_gravity"] = 0.50
    result = calculate_multi_member_bolt_reference(inputs)
    assert result["procedure"] == (
        "NDS-2024-12.3.1A-three-member-symmetric-double-shear-all-four-modes"
    )
    assert result["analysis_count"] == 1
    assert set(result["analysis_results"][0]["yield_values_lbf"]) == {
        "Im", "Is", "IIIs", "IV"
    }
    # NDS Table 12F, 1.5-in main/side, 1/2-in bolt, DF-L G=.50, Zll.
    assert result["reference_lateral_lbf"] == pytest.approx(1050.0, abs=0.6)


def test_odd_five_member_chain_uses_every_symmetric_triple_and_published_nds_table_answer():
    inputs = case(5)
    for member in inputs["members"]:
        member["specific_gravity"] = 0.50
    result = calculate_multi_member_bolt_reference(inputs)

    # NDS-2024 Table 12F, first row: three 1-1/2 in solid-sawn members,
    # G=0.50, 1/2 in bolt, Fyb=45 ksi, parallel-to-grain Z = 1,050 lb.
    # NDS 12.3.8.2 applies Z=min(triples)*(n-1)/2 = 1,050*2.
    assert result["procedure"] == "NDS-2024-12.3.8.2-odd-member-min-triple-times-n-minus-1-over-2"
    assert result["analysis_count"] == 3
    assert result["nds_member_count_multiplier"] == 2
    assert [item["reference_z_lbf"] for item in result["analysis_results"]] == pytest.approx(
        [1050.0, 1050.0, 1050.0], abs=0.6
    )
    assert result["reference_lateral_lbf"] == pytest.approx(2100.0, abs=1.2)
    for analysis in result["analysis_results"]:
        assert set(analysis["yield_values_lbf"]) == {"Im", "Is", "IIIs", "IV"}
        assert len(analysis["shear_plane_ids"]) == 2


def test_current_manifest_axis_inventory_is_geometry_only_and_pending():
    root = Path(__file__).resolve().parents[1]
    result = inspect_current_candidate_axis(
        root / CURRENT_MANIFEST_PATH,
        "bottom_center/clip_horizontal_bottom_left_2/principal_1",
    )
    assert result["status"] == "pending"
    assert result["manifest_file_sha256"] == CURRENT_MANIFEST_FILE_SHA256
    assert result["receiver_member_ids"] == [
        "base_principal_center_left", "bottom_center_left_cleat"
    ]
    assert [round(row["modeled_interval_length_mm"], 1)
            for row in result["modeled_receiver_geometry_only"]] == [38.1, 88.9]
    assert all(not row["physical_bearing_length_established"]
               for row in result["modeled_receiver_geometry_only"])
    assert result["member_order_established"] is False
    assert result["reference_lateral_lbf"] is None
    assert result["adjusted_capacity_lbf"] is None
    assert "fresh_current_same-case_demand_and_governing_case" in result["missing_inputs"]
    assert "physical_head_to_nut_stack_order_and_all_member_layers" in result["missing_inputs"]
    assert result["criterion_disposition"] == "pending"


def test_three_receiver_manifest_axis_stays_pending_without_symmetric_physical_stack():
    root = Path(__file__).resolve().parents[1]
    result = inspect_current_candidate_axis(
        root / CURRENT_MANIFEST_PATH,
        "knee_outer_left_side_1",
    )
    assert result["status"] == "pending"
    assert result["receiver_member_ids"] == [
        "base_side_left", "knee_outer_left_inner_frame_block", "knee_outer_left_spine"
    ]
    assert [round(row["modeled_interval_length_mm"], 1)
            for row in result["modeled_receiver_geometry_only"]] == [88.9, 88.9, 38.1]
    assert result["member_order_established"] is False
    assert result["reference_lateral_lbf"] is None
    assert result["criterion_disposition"] == "pending"


def test_manifest_hash_mismatch_fails_closed(tmp_path):
    tampered = tmp_path / "manifest.json"
    tampered.write_text('{"unreviewed": "manifest"}\n')
    result = inspect_current_candidate_axis(tampered, "some-axis")
    assert result["status"] == "pending"
    assert result["reference_lateral_lbf"] is None
    assert result["missing_inputs"] == ["current_full_frame_manifest_hash_rebind_and_review"]


def test_incomplete_actual_case_returns_pending_with_named_inputs():
    result = calculate_multi_member_bolt_reference({"standard_edition": NDS_EDITION})
    assert result["status"] == "pending"
    assert result["reference_lateral_lbf"] is None
    assert "members" in result["missing_inputs"]
    assert "bolt.product_source" in result["missing_inputs"]
    assert "bolt.fyb_basis" in result["missing_inputs"]
    assert "geometry_axis_source" in result["missing_inputs"]
    assert "spacing_end_edge_source" in result["missing_inputs"]
    assert "action_source" in result["missing_inputs"]
    assert result["criterion_disposition"] == "pending"


@pytest.mark.parametrize("changed", [
    {"adjacent_face_gaps_in": [0.0, 0.01, 0.0]},
    {"load_normal_to_bolt_axis": False},
    {"minimum_spacing_end_edge_verified": False},
])
def test_nonapplicable_or_unverified_nds_prerequisites_do_not_calculate(changed):
    with pytest.raises(ValueError):
        calculate_multi_member_bolt_reference(case(4) | changed)


def test_different_standard_edition_is_named_pending_rebind():
    result = calculate_multi_member_bolt_reference(
        case(4) | {"standard_edition": "ANSI/AWC NDS-2018"}
    )
    assert result["status"] == "pending"
    assert result["reference_lateral_lbf"] is None
    assert "standard_edition_mismatch_requires_method_rebind" in result["missing_inputs"]


def test_even_member_direction_must_alternate_at_each_shear_plane():
    inputs = case(4)
    inputs["members"][2]["lateral_force_lbf"] = -100.0
    with pytest.raises(ValueError, match="adjacent members"):
        calculate_multi_member_bolt_reference(inputs)


def test_double_shear_side_geometry_and_actions_must_be_symmetric():
    inputs = case(5)
    inputs["members"][4]["bearing_length_in"] = 1.6
    with pytest.raises(ValueError, match="symmetric side members"):
        calculate_multi_member_bolt_reference(inputs)

    inputs = case(5)
    inputs["members"][2]["lateral_force_lbf"] = -200.0
    with pytest.raises(ValueError, match="same-direction side actions"):
        calculate_multi_member_bolt_reference(inputs)


def test_root_diameter_and_special_subquarter_reduction_apply_to_every_mode():
    inputs = case(4)
    inputs["bolt"]["nominal_diameter_in"] = 0.25
    inputs["bolt"]["root_diameter_in"] = 0.20
    inputs["members"][0]["thread_bearing_length_in"] = 0.376
    for member in inputs["members"]:
        member["load_to_grain_degrees"] = 90.0
    result = calculate_multi_member_bolt_reference(inputs)
    assert result["selected_bearing_and_yield_diameter_in"] == pytest.approx(0.20)
    # January 2025 erratum: KD=10D-0.5=1.5 and the threaded full-body
    # bolt footnote adds Ktheta=1.25 for nominal D>=1/4 in and Dr<1/4 in.
    assert all(value == pytest.approx(1.875)
               for value in result["reduction_terms"].values())
    assert all(set(row["yield_values_lbf"]) == {"Im", "Is", "II", "IIIm", "IIIs", "IV"}
               for row in result["analysis_results"])


def test_corrected_small_diameter_reduction_at_both_interval_boundaries():
    # January 2025 AWC erratum, NDS Table 12.3.1B: D<=.17 uses 2.2;
    # .17<D<.25 uses 10D-.5; D=.25 enters the full-diameter branch.
    at_lower = _reduction_terms(
        diameter_in=0.17, nominal_diameter_in=0.25, angle_max_degrees=0.0
    )
    just_above_lower = _reduction_terms(
        diameter_in=0.170001, nominal_diameter_in=0.25, angle_max_degrees=0.0
    )
    just_below_upper = _reduction_terms(
        diameter_in=0.249999, nominal_diameter_in=0.25, angle_max_degrees=0.0
    )
    at_upper = _reduction_terms(
        diameter_in=0.25, nominal_diameter_in=0.25, angle_max_degrees=0.0
    )
    for terms, expected in (
        (at_lower, 2.2),
        (just_above_lower, 1.20001),
        (just_below_upper, 1.99999),
    ):
        assert list(terms.values()) == pytest.approx([expected] * 6)
    assert at_upper == {
        "Im": 4.0, "Is": 4.0, "II": 3.6,
        "IIIm": 3.2, "IIIs": 3.2, "IV": 3.2,
    }


def test_one_member_thread_boundary_selects_d_or_root_for_the_whole_bolt():
    inputs = case(4)
    inputs["members"][0]["thread_bearing_length_in"] = 1.5 / 4.0
    assert calculate_multi_member_bolt_reference(inputs)[
        "selected_bearing_and_yield_diameter_in"
    ] == pytest.approx(0.5)
    inputs["members"][0]["thread_bearing_length_in"] = 1.5 / 4.0 + 1e-6
    assert calculate_multi_member_bolt_reference(inputs)[
        "selected_bearing_and_yield_diameter_in"
    ] == pytest.approx(0.4)


@pytest.mark.parametrize("field,value", [
    ("specific_gravity", math.nan),
    ("bearing_length_in", math.inf),
    ("load_to_grain_degrees", 91.0),
    ("lateral_force_lbf", 0.0),
    ("lateral_force_lbf", math.nan),
])
def test_member_invalid_inputs_rejected(field, value):
    inputs = case(4)
    inputs["members"][0][field] = value
    with pytest.raises(ValueError):
        calculate_multi_member_bolt_reference(inputs)


def test_member_bolt_axis_must_be_perpendicular_to_grain_and_source_bound():
    inputs = case(4)
    inputs["members"][0]["bolt_axis_perpendicular_to_grain"] = False
    with pytest.raises(ValueError, match="perpendicular"):
        calculate_multi_member_bolt_reference(inputs)

    inputs = case(4)
    inputs["members"][0]["grain_orientation_source"]["sha256"] = "bad"
    with pytest.raises(ValueError, match="grain_orientation_source"):
        calculate_multi_member_bolt_reference(inputs)


def test_invalid_fyb_basis_and_unresolved_pair_role_fail_closed():
    inputs = case(4)
    inputs["bolt"]["fyb_basis"]["test_basis"] = "ASTM_F606_without_Fyb_evaluation"
    with pytest.raises(ValueError, match="Fyb basis"):
        calculate_multi_member_bolt_reference(inputs)

    inputs = case(4)
    del inputs["adjacent_pair_roles"]
    result = calculate_multi_member_bolt_reference(inputs)
    assert result["status"] == "pending"
    assert result["missing_inputs"] == [
        "adjacent_pair_roles:one_main_and_side_binding_per_shear_plane"
    ]


@pytest.mark.parametrize("bad_id", [["member-1"], {"id": "member-1"}])
def test_unhashable_adjacent_pair_member_id_is_reported_as_value_error(bad_id):
    inputs = case(4)
    inputs["adjacent_pair_roles"][0]["main_member_id"] = bad_id
    with pytest.raises(ValueError, match="member IDs must be strings"):
        calculate_multi_member_bolt_reference(inputs)


def test_duplicate_member_ids_and_bad_source_hashes_are_rejected():
    inputs = case(4)
    inputs["members"][1]["member_id"] = inputs["members"][0]["member_id"]
    with pytest.raises(ValueError, match="member IDs"):
        calculate_multi_member_bolt_reference(inputs)

    inputs = case(4)
    inputs["bolt"]["product_source"]["sha256"] = "bad"
    with pytest.raises(ValueError, match="product_source"):
        calculate_multi_member_bolt_reference(inputs)


def test_missing_per_member_grain_property_or_action_returns_pending_not_a_default():
    for path in (
        ("members", 0, "specific_gravity"),
        ("members", 0, "load_to_grain_degrees"),
        ("members", 0, "grain_orientation_source"),
        ("members", 0, "bearing_length_source"),
        ("members", 0, "lateral_force_lbf"),
        ("bolt", "bending_yield_strength_psi"),
    ):
        inputs = case(4)
        if len(path) == 3:
            del inputs[path[0]][path[1]][path[2]]
        else:
            del inputs[path[0]][path[1]]
        result = calculate_multi_member_bolt_reference(inputs)
        assert result["status"] == "pending"
        assert result["reference_lateral_lbf"] is None
