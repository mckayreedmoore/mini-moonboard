"""Source-bounded tests for the current NDS-2024 Cg evaluator."""

from __future__ import annotations

import copy
from typing import Any

import pytest

from mini_moonboard.nds_2024_group_action import (
    SCHEMA_VERSION,
    SOURCE_ROLES,
    _changed_payload_paths,
    canonical_group_record_sha256,
    canonical_sensitivity_contract_sha256,
    evaluate_group_factor_sensitivity,
)
from mini_moonboard.nds_2024_group_action import (
    evaluate_group_action_factor as _evaluate_group_action_factor,
)


def bindings(
    tag: str = "baseline", *, side_member_ids: tuple[str, ...] = ("side-01",)
) -> dict[str, dict[str, Any]]:
    result = {
        role: {
            "source_id": f"synthetic-fixture/{tag}/{role}",
            "sha256": (hex(index + 1)[2:] * 64)[:64],
        }
        for index, role in enumerate(SOURCE_ROLES)
    }
    result["member_sections"].update(
        main_member_id="main-01",
        side_member_ids=list(side_member_ids),
        shear_planes=len(side_member_ids),
    )
    return result


def payload(*, count: int = 2, diameter: float = 1.0, pitch: float = 4.0) -> dict:
    return {
        "schema": SCHEMA_VERSION,
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "scenario_id": "baseline",
        "source_bindings": bindings(),
        "group_geometry": {
            "row_axis_xyz": [1.0, 0.0, 0.0],
            "fasteners": [
                {
                    "fastener_id": f"b{index + 1}",
                    "center_in": [index * pitch, 0.0, 0.0],
                    "nominal_diameter_in": diameter,
                    "type": "dowel",
                }
                for index in range(count)
            ],
        },
        "load_case": {
            "case_id": "lateral-case-01",
            "lateral_resultant_xyz_lbf": [1000.0, 0.0, 0.0],
        },
        "members": {
            "shear_planes": 1,
            "main": {
                "member_id": "main-01",
                "material": "wood",
                "elastic_modulus_psi": 1_400_000.0,
                "gross_section_area_in2": 10.0,
                "grain_axis_xyz": [1.0, 0.0, 0.0],
            },
            "side_members": [
                {
                    "member_id": "side-01",
                    "material": "wood",
                    "elastic_modulus_psi": 1_400_000.0,
                    "gross_section_area_in2": 5.0,
                    "grain_axis_xyz": [1.0, 0.0, 0.0],
                }
            ],
        },
    }


def evaluate_group_action_factor(payload_record, *, expected_bindings):
    return _evaluate_group_action_factor(
        payload_record,
        expected_bindings=expected_bindings,
        expected_payload_sha256=canonical_group_record_sha256(payload_record),
    )


def bind_sensitivity_contract(contract: dict[str, Any]) -> dict[str, str]:
    contract["sha256"] = canonical_sensitivity_contract_sha256(contract)
    return {
        "contract_id": contract["contract_id"],
        "source_id": contract["source_id"],
        "sha256": contract["sha256"],
        "review_status": "coordinator_reviewed",
    }


def test_published_table_11_3_6a_known_answers_match_rounded_values():
    # AWC NDS-2024 Table 11.3.6A, p. 73: D=1 in, s=4 in,
    # E=1,400,000 psi, As=5 in², As/Am=.5 (thus Am=10 in²).
    # Published Cg values for N=2, 3, 4 are .98, .92, .84.
    expected_table_values = {2: 0.98, 3: 0.92, 4: 0.84}
    independently_computed = {
        2: 0.9766839378238343,
        3: 0.9163482162668576,
        4: 0.8371926373880908,
    }
    for count, rounded_table_value in expected_table_values.items():
        record = payload(count=count)
        result = evaluate_group_action_factor(record, expected_bindings=bindings())
        assert result["status"] == "calculated_method_only"
        assert result["cg"] == pytest.approx(independently_computed[count], rel=1e-13)
        assert round(result["cg"] + 1e-12, 2) == rounded_table_value
        assert result["capacity"] is None
        assert result["criterion_disposition"] == "pending"


def test_equal_ea_two_bolt_row_has_exact_unit_cg_and_subquarter_inch_rule():
    record = payload(count=2, diameter=0.375)
    record["members"]["side_members"][0]["gross_section_area_in2"] = 10.0
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "calculated_method_only"
    assert result["cg"] == pytest.approx(1.0, abs=1e-14)

    small = payload(count=3, diameter=0.249)
    small_result = evaluate_group_action_factor(small, expected_bindings=bindings())
    assert small_result["status"] == "calculated_method_only"
    assert small_result["cg"] == 1.0
    assert small_result["gamma_lbf_per_in"] is None


def test_exact_quarter_inch_uses_equation_not_small_diameter_exception():
    result = evaluate_group_action_factor(
        payload(diameter=0.25, count=3), expected_bindings=bindings()
    )
    assert result["status"] == "calculated_method_only"
    assert result["gamma_lbf_per_in"] == pytest.approx(22500.0)
    assert result["cg"] < 1.0


@pytest.mark.parametrize("diameters", ([0.2499999, 0.25], [0.25, 0.2499999]))
def test_distinct_nominal_diameters_straddling_quarter_inch_are_always_pending(
    diameters,
):
    record = payload(count=2)
    for fastener, diameter in zip(record["group_geometry"]["fasteners"], diameters):
        fastener["nominal_diameter_in"] = diameter
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "pending"
    assert result["cg"] is None
    assert "mixed_fastener_diameters" in result["reason_codes"]


def test_perpendicular_to_grain_uses_nds_11_3_6_3_equivalent_area():
    record = payload(count=3)
    for member in [record["members"]["main"], *record["members"]["side_members"]]:
        member["grain_axis_xyz"] = [0.0, 0.0, 1.0]
        member["thickness_in"] = 1.5
        member["overall_fastener_group_width_in"] = 4.0
        member["group_factor_area_in2"] = 6.0
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "calculated_method_only"
    assert result["main_ea_lbf"] == pytest.approx(1_400_000.0 * 6.0)
    assert result["side_ea_lbf"] == pytest.approx(1_400_000.0 * 6.0)

    for member in [record["members"]["main"], *record["members"]["side_members"]]:
        member["overall_fastener_group_width_in"] = 5.0
        member["group_factor_area_in2"] = 7.5
    width_mismatch = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert width_mismatch["status"] == "pending"
    assert (
        "perpendicular_group_width_does_not_match_single_row_minimum_pitch"
        in width_mismatch["reason_codes"]
    )


def test_multiple_shear_side_members_use_sum_of_gross_side_areas():
    record = payload(count=3)
    record["members"]["shear_planes"] = 2
    record["members"]["side_members"].append(
        {
            "member_id": "side-02",
            "material": "wood",
            "elastic_modulus_psi": 1_400_000.0,
            "gross_section_area_in2": 5.0,
            "grain_axis_xyz": [1.0, 0.0, 0.0],
        }
    )
    multiple_shear_bindings = bindings(side_member_ids=("side-01", "side-02"))
    record["source_bindings"] = multiple_shear_bindings
    result = evaluate_group_action_factor(
        record, expected_bindings=multiple_shear_bindings
    )
    assert result["status"] == "calculated_method_only"
    assert result["side_ea_lbf"] == pytest.approx(1_400_000.0 * 10.0)


@pytest.mark.parametrize("side_count", [3, 4])
def test_four_or_more_total_member_group_action_fails_closed(side_count):
    record = payload(count=3)
    record["members"]["shear_planes"] = side_count
    record["members"]["side_members"] = [
        {
            "member_id": f"side-{index + 1:02d}",
            "material": "wood",
            "elastic_modulus_psi": 1_400_000.0,
            "gross_section_area_in2": 5.0,
            "grain_axis_xyz": [1.0, 0.0, 0.0],
        }
        for index in range(side_count)
    ]
    member_ids = tuple(
        side["member_id"] for side in record["members"]["side_members"]
    )
    expected = bindings(side_member_ids=member_ids)
    record["source_bindings"] = expected

    result = evaluate_group_action_factor(record, expected_bindings=expected)

    assert result["status"] == "pending"
    assert (
        "four_or_more_member_plane_method_not_source_bound"
        in result["reason_codes"]
    )
    assert result["cg"] is None
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"


@pytest.mark.parametrize(
    "row_centres",
    [
        [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [0.0, 0.0, 2.0], [4.0, 0.0, 2.0]],
        [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [1.0, 0.0, 0.1], [5.0, 0.0, 0.1]],
        [
            [0.0, 0.0, 0.0],
            [4.0, 0.0, 0.0],
            [0.0, 0.0, 2.0],
            [4.0, 0.0, 2.0],
            [0.0, 0.0, 4.0],
            [4.0, 0.0, 4.0],
        ],
    ],
)
def test_adjacent_staggered_and_odd_multiple_rows_are_pending(row_centres):
    record = payload(count=2)
    record["group_geometry"]["fasteners"] = [
        {
            "fastener_id": f"b{index + 1}",
            "center_in": center,
            "nominal_diameter_in": 1.0,
            "type": "dowel",
        }
        for index, center in enumerate(row_centres)
    ]
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "pending"
    assert "not_a_single_straight_row" in result["reason_codes"]
    assert result["cg"] is None


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda p: p["load_case"].update(
                lateral_resultant_xyz_lbf=[1000.0, 0.01, 0.0]
            ),
            "load_direction_not_aligned_with_fastener_row",
        ),
        (
            lambda p: p["group_geometry"]["fasteners"][1]["center_in"].__setitem__(
                1, 0.1
            ),
            "not_a_single_straight_row",
        ),
        (
            lambda p: p["group_geometry"]["fasteners"].append(
                {
                    "fastener_id": "b3",
                    "center_in": [9.0, 0.0, 0.0],
                    "nominal_diameter_in": 1.0,
                    "type": "dowel",
                }
            ),
            "nonuniform_pitch_outside_method_scope",
        ),
        (
            lambda p: p["group_geometry"]["fasteners"][1].update(
                nominal_diameter_in=0.5
            ),
            "mixed_fastener_diameters",
        ),
        (
            lambda p: p["group_geometry"]["fasteners"][0].update(
                nominal_diameter_in=1.01
            ),
            "diameter_outside_nds_11_3_6_1_scope",
        ),
        (
            lambda p: p["members"]["side_members"][0].update(material="steel"),
            "unsupported_nonwood_member",
        ),
        (
            lambda p: p["members"]["main"].update(grain_axis_xyz=[1.0, 1.0, 0.0]),
            "oblique_member_grain_loading_outside_method_scope",
        ),
        (
            lambda p: p["members"].update(shear_planes=2),
            "source_binding_mismatch_or_incomplete",
        ),
    ],
)
def test_unsupported_or_inconsistent_evidence_fails_closed(mutation, reason):
    record = payload()
    mutation(record)
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "pending"
    assert reason in result["reason_codes"]
    assert result["cg"] is None
    assert result["capacity"] is None


def test_missing_perpendicular_area_or_unverified_area_product_is_pending():
    record = payload()
    for member in [record["members"]["main"], *record["members"]["side_members"]]:
        member["grain_axis_xyz"] = [0.0, 0.0, 1.0]
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "pending"
    assert "missing_nds_11_3_6_3_perpendicular_area_inputs" in result["reason_codes"]

    for member in [record["members"]["main"], *record["members"]["side_members"]]:
        member.update(
            thickness_in=2.0,
            overall_fastener_group_width_in=4.0,
            group_factor_area_in2=7.0,
        )
    mismatch = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert mismatch["status"] == "pending"
    assert (
        "perpendicular_area_does_not_match_thickness_times_group_width"
        in mismatch["reason_codes"]
    )


def test_independent_binding_is_required_and_producer_hash_changes_do_not_pass():
    record = payload()
    assert (
        evaluate_group_action_factor(record, expected_bindings=None)["status"]
        == "pending"
    )

    expected = bindings()
    changed = copy.deepcopy(record)
    changed["source_bindings"]["geometry"]["sha256"] = "a" * 64
    assert (
        evaluate_group_action_factor(changed, expected_bindings=expected)["status"]
        == "pending"
    )

    expected["geometry"]["sha256"] = "invalid"
    assert (
        evaluate_group_action_factor(record, expected_bindings=expected)["status"]
        == "pending"
    )

    expected = bindings(side_member_ids=("side-01", "side-02"))
    assert (
        evaluate_group_action_factor(record, expected_bindings=expected)["status"]
        == "pending"
    )


def test_factor_inputs_are_bound_by_independent_canonical_record_digest():
    original = payload(count=3)
    expected_digest = canonical_group_record_sha256(original)
    mutations = [
        lambda p: p["group_geometry"]["fasteners"][0].update(nominal_diameter_in=0.5),
        lambda p: p["group_geometry"]["fasteners"][1]["center_in"].__setitem__(0, 3.5),
        lambda p: p["members"]["main"].update(elastic_modulus_psi=1_500_000.0),
        lambda p: p["load_case"].update(lateral_resultant_xyz_lbf=[0.0, 1000.0, 0.0]),
    ]
    for mutate in mutations:
        changed = copy.deepcopy(original)
        mutate(changed)
        result = _evaluate_group_action_factor(
            changed,
            expected_bindings=bindings(),
            expected_payload_sha256=expected_digest,
        )
        assert result["status"] == "pending"
        assert "canonical_payload_digest_mismatch" in result["reason_codes"]
        assert result["cg"] is None

    missing_digest = _evaluate_group_action_factor(
        original, expected_bindings=bindings(), expected_payload_sha256=None
    )
    assert missing_digest["status"] == "pending"
    assert (
        "independent_canonical_payload_digest_required"
        in missing_digest["reason_codes"]
    )


def test_canonical_digest_rejects_non_json_or_nonfinite_payload_values():
    record = payload()
    record["producer_extension"] = ("tuple", "is_not_json")
    assert canonical_group_record_sha256(record) is None

    record = payload()
    record[1] = "non-string object key"
    assert canonical_group_record_sha256(record) is None

    record = payload()
    record["producer_extension"] = float("inf")
    assert canonical_group_record_sha256(record) is None


def test_missing_nonfinite_and_duplicate_fastener_geometry_never_returns_factor():
    record = payload()
    del record["group_geometry"]["fasteners"][1]["center_in"]
    assert (
        evaluate_group_action_factor(record, expected_bindings=bindings())["cg"] is None
    )


def test_whitespace_only_load_case_id_fails_closed():
    record = payload()
    record["load_case"]["case_id"] = "   "

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "pending"
    assert "missing_case_bound_group_action" in result["reason_codes"]
    assert result["cg"] is None


def test_integer_too_large_for_float_conversion_fails_closed():
    record = payload()
    record["members"]["main"]["elastic_modulus_psi"] = 10**1000

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "pending"
    assert "missing_or_invalid_member_modulus" in result["reason_codes"]
    assert result["cg"] is None


def test_extreme_finite_coordinates_with_overflowing_span_fail_closed():
    record = payload(count=2, diameter=0.2)
    record["group_geometry"]["fasteners"][0]["center_in"] = [-1.0e308, 0.0, 0.0]
    record["group_geometry"]["fasteners"][1]["center_in"] = [1.0e308, 0.0, 0.0]

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "pending"
    assert "derived_group_geometry_outside_finite_range" in result["reason_codes"]
    assert result["cg"] is None

    record = payload()
    record["group_geometry"]["fasteners"][1]["center_in"][0] = float("nan")
    assert (
        evaluate_group_action_factor(record, expected_bindings=bindings())["cg"] is None
    )

    record = payload()
    record["group_geometry"]["fasteners"][1]["fastener_id"] = "b1"
    assert (
        evaluate_group_action_factor(record, expected_bindings=bindings())["cg"] is None
    )


def test_finite_load_vector_with_overflowing_norm_keeps_direction_check():
    record = payload()
    record["load_case"]["lateral_resultant_xyz_lbf"] = [1.7e308, 1.7e308, 0.0]

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "pending"
    assert "load_direction_not_aligned_with_fastener_row" in result["reason_codes"]
    assert result["cg"] is None


def test_finite_grain_vector_with_overflowing_norm_keeps_grain_check():
    record = payload()
    record["members"]["main"]["grain_axis_xyz"] = [1.7e308, 0.0, 1.7e308]

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "pending"
    assert "oblique_member_grain_loading_outside_method_scope" in result["reason_codes"]
    assert result["cg"] is None


def test_finite_row_axis_with_overflowing_norm_preserves_valid_row_direction():
    record = payload()
    record["group_geometry"]["row_axis_xyz"] = [1.7e308, 1.7e308, 0.0]
    record["group_geometry"]["fasteners"][1]["center_in"] = [4.0, 4.0, 0.0]
    record["load_case"]["lateral_resultant_xyz_lbf"] = [1000.0, 1000.0, 0.0]
    record["members"]["main"]["grain_axis_xyz"] = [1.7e308, 1.7e308, 0.0]
    record["members"]["side_members"][0]["grain_axis_xyz"] = [
        1.7e308,
        1.7e308,
        0.0,
    ]

    result = evaluate_group_action_factor(record, expected_bindings=bindings())

    assert result["status"] == "calculated_method_only"
    assert result["uniform_pitch_in"] == pytest.approx(4.0 * 2**0.5)
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"


def test_deep_json_payload_returns_none_and_pending_instead_of_recursion_error():
    record = payload()
    nested = None
    for _ in range(600):
        nested = {"items": [nested]}
    record["producer_extension"] = nested

    assert canonical_group_record_sha256(record) is None
    result = _evaluate_group_action_factor(
        record,
        expected_bindings=bindings(),
        expected_payload_sha256="0" * 64,
    )
    assert result["status"] == "pending"
    assert result["cg"] is None
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"


def test_sensitivity_paths_distinguish_json_scalar_types_and_reject_omission():
    baseline = payload(count=3, pitch=4.0)
    variant = payload(count=3, pitch=2.0)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    baseline["producer_extension"] = 1
    variant["producer_extension"] = True
    changed_paths = [
        "group_geometry.fasteners[1].center_in[0]",
        "group_geometry.fasteners[2].center_in[0]",
        "producer_extension",
    ]

    def evaluate_with_paths(paths):
        contract = {
            "contract_id": "synthetic-scalar-type-change",
            "source_id": "synthetic-fixture/scalar-type-change",
            "sha256": "pending-digest",
            "review_status": "coordinator_reviewed",
            "classification": "composite_scenario",
            "candidate_id": "synthetic-only",
            "revision_id": "fixture-v1",
            "group_id": "group-01",
            "baseline_scenario_id": "baseline",
            "sensitivity_scenario_id": "sensitivity",
            "changed_input_paths": paths,
        }
        binding = bind_sensitivity_contract(contract)
        return evaluate_group_factor_sensitivity(
            baseline,
            variant,
            baseline_expected_bindings=bindings(),
            baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
            sensitivity_expected_bindings=bindings("sensitivity"),
            sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
            expected_sensitivity_contract=contract,
            expected_sensitivity_binding=binding,
        )

    result = evaluate_with_paths(changed_paths)
    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["changed_input_paths"] == changed_paths
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"

    omitted_type_change = evaluate_with_paths(changed_paths[:-1])
    assert omitted_type_change["status"] == "pending"
    assert (
        "sensitivity_changed_input_paths_do_not_match_contract"
        in omitted_type_change["reason_codes"]
    )


def test_sensitivity_paths_distinguish_signed_zero_and_reject_omission():
    baseline = payload(count=3, pitch=4.0)
    variant = payload(count=3, pitch=2.0)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    baseline["producer_extension"] = -0.0
    variant["producer_extension"] = 0.0
    changed_paths = [
        "group_geometry.fasteners[1].center_in[0]",
        "group_geometry.fasteners[2].center_in[0]",
        "producer_extension",
    ]

    def evaluate_with_paths(paths):
        contract = {
            "contract_id": "synthetic-signed-zero-change",
            "source_id": "synthetic-fixture/signed-zero-change",
            "sha256": "pending-digest",
            "review_status": "coordinator_reviewed",
            "classification": "composite_scenario",
            "candidate_id": "synthetic-only",
            "revision_id": "fixture-v1",
            "group_id": "group-01",
            "baseline_scenario_id": "baseline",
            "sensitivity_scenario_id": "sensitivity",
            "changed_input_paths": paths,
        }
        binding = bind_sensitivity_contract(contract)
        return evaluate_group_factor_sensitivity(
            baseline,
            variant,
            baseline_expected_bindings=bindings(),
            baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
            sensitivity_expected_bindings=bindings("sensitivity"),
            sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
            expected_sensitivity_contract=contract,
            expected_sensitivity_binding=binding,
        )

    result = evaluate_with_paths(changed_paths)
    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["changed_input_paths"] == changed_paths
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"

    omitted_signed_zero = evaluate_with_paths(changed_paths[:-1])
    assert omitted_signed_zero["status"] == "pending"
    assert (
        "sensitivity_changed_input_paths_do_not_match_contract"
        in omitted_signed_zero["reason_codes"]
    )


def test_extreme_but_finite_ea_inputs_fail_pending_without_arithmetic_exception():
    record = payload(count=4)
    record["members"]["main"]["elastic_modulus_psi"] = 1.0e300
    record["members"]["side_members"][0]["elastic_modulus_psi"] = 1.0e300
    result = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert result["status"] == "pending"
    assert result["cg"] is None
    assert "equation_intermediate_outside_finite_range" in result["reason_codes"]

    record = payload()
    record["members"]["main"]["elastic_modulus_psi"] = 1.0e308
    overflow = evaluate_group_action_factor(record, expected_bindings=bindings())
    assert overflow["status"] == "pending"
    assert overflow["cg"] is None


def test_sensitive_factor_comparison_requires_coordinator_reviewed_contract():
    base = payload(count=3, pitch=4.0)
    variant = payload(count=3, pitch=2.0)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")

    no_contract = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=None,
        expected_sensitivity_binding=None,
    )
    assert no_contract["status"] == "pending"
    assert (
        "sensitivity_case_contract_and_independent_binding_required"
        in no_contract["reason_codes"]
    )

    contract = {
        "contract_id": "synthetic-review-only",
        "source_id": "synthetic-fixture/sensitivity-contract",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": [
            "group_geometry.fasteners[1].center_in[0]",
            "group_geometry.fasteners[2].center_in[0]",
        ],
    }
    contract_binding = bind_sensitivity_contract(contract)
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=contract_binding,
    )
    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["sensitivity_cg"] > result["baseline_cg"]
    assert result["sensitivity_over_baseline_cg"] == pytest.approx(
        result["sensitivity_cg"] / result["baseline_cg"]
    )
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"
    assert result["sensitivity_classification"] == "composite_scenario"
    assert result["changed_input_paths"] == contract["changed_input_paths"]


@pytest.mark.parametrize(
    ("baseline_member_count", "sensitivity_member_count", "pending_prefixes"),
    [
        (4, 4, ("baseline:", "sensitivity:")),
        (3, 4, ("sensitivity:",)),
    ],
)
def test_group_factor_sensitivity_fails_closed_when_either_case_has_four_members(
    baseline_member_count, sensitivity_member_count, pending_prefixes
):
    def scenario(scenario_id, total_members, pitch):
        record = payload(count=3, pitch=pitch)
        record["scenario_id"] = scenario_id
        side_ids = tuple(f"side-{index + 1:02d}" for index in range(total_members - 1))
        record["members"]["shear_planes"] = len(side_ids)
        record["members"]["side_members"] = [
            {
                "member_id": member_id,
                "material": "wood",
                "elastic_modulus_psi": 1_400_000.0,
                "gross_section_area_in2": 5.0,
                "grain_axis_xyz": [1.0, 0.0, 0.0],
            }
            for member_id in side_ids
        ]
        source_bindings = bindings(scenario_id, side_member_ids=side_ids)
        record["source_bindings"] = source_bindings
        return record, source_bindings

    baseline, baseline_bindings = scenario(
        "baseline", baseline_member_count, 4.0
    )
    sensitivity, sensitivity_bindings = scenario(
        "sensitivity", sensitivity_member_count, 2.0
    )
    changed_paths = [
        "group_geometry.fasteners[1].center_in[0]",
        "group_geometry.fasteners[2].center_in[0]",
    ]
    if baseline_member_count != sensitivity_member_count:
        changed_paths.extend(
            ["members.shear_planes", "members.side_members.length"]
        )
    contract = {
        "contract_id": "synthetic-four-member-boundary",
        "source_id": "synthetic-fixture/four-member-boundary",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": sorted(changed_paths),
    }
    contract_binding = bind_sensitivity_contract(contract)

    result = evaluate_group_factor_sensitivity(
        baseline,
        sensitivity,
        baseline_expected_bindings=baseline_bindings,
        baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=sensitivity_bindings,
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(
            sensitivity
        ),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=contract_binding,
    )

    assert result["status"] == "pending"
    assert "baseline_or_sensitivity_case_not_calculated" in result["reason_codes"]
    assert result["cg"] is None
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"
    assert all(
        any(item.startswith(prefix) for item in result["missing_inputs"])
        for prefix in pending_prefixes
    )


def test_sensitivity_contract_mismatch_or_unreviewed_contract_fails_closed():
    base = payload()
    variant = payload()
    variant["scenario_id"] = "sensitivity"
    contract = {
        "contract_id": "synthetic-review-only",
        "source_id": "synthetic-fixture/sensitivity-contract",
        "sha256": "pending-digest",
        "review_status": "draft",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "wrong-baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": [
            "group_geometry.fasteners[1].center_in[0]",
            "group_geometry.fasteners[2].center_in[0]",
        ],
    }
    contract_binding = bind_sensitivity_contract(contract)
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings(),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=contract_binding,
    )
    assert result["status"] == "pending"
    assert (
        "sensitivity_case_contract_not_coordinator_reviewed" in result["reason_codes"]
    )

    contract["review_status"] = "coordinator_reviewed"
    contract_binding = bind_sensitivity_contract(contract)
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings(),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=contract_binding,
    )
    assert result["status"] == "pending"
    assert "baseline_scenario_id_mismatch" in result["reason_codes"]

    contract["baseline_scenario_id"] = "baseline"
    contract_binding = bind_sensitivity_contract(contract)
    bad_binding = dict(contract_binding, sha256="f" * 64)
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings(),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=bad_binding,
    )
    assert result["status"] == "pending"
    assert (
        "sensitivity_contract_does_not_match_independent_review_binding"
        in result["reason_codes"]
    )

    contract["changed_input_paths"] = ["not-the-actual-changed-path"]
    contract_binding = bind_sensitivity_contract(contract)
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings(),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=contract_binding,
    )
    assert result["status"] == "pending"
    assert (
        "sensitivity_changed_input_paths_do_not_match_contract"
        in result["reason_codes"]
    )


def test_mutating_sensitivity_terms_while_retaining_both_hashes_fails_closed():
    base = payload(count=3, pitch=4.0)
    variant = payload(count=3, pitch=2.0)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    contract = {
        "contract_id": "synthetic-review-only",
        "source_id": "synthetic-fixture/sensitivity-contract",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": [
            "group_geometry.fasteners[1].center_in[0]",
            "group_geometry.fasteners[2].center_in[0]",
        ],
    }
    binding = bind_sensitivity_contract(contract)
    declared_contract_digest = contract["sha256"]
    coordinator_digest = binding["sha256"]

    # Adversarial producer changes contract terms but leaves both digest fields
    # untouched. The coordinator digest no longer matches the content.
    contract["changed_input_paths"] = ["group_geometry.fasteners[1].center_in[0]"]
    assert contract["sha256"] == declared_contract_digest
    assert binding["sha256"] == coordinator_digest
    result = evaluate_group_factor_sensitivity(
        base,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(base),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )
    assert result["status"] == "pending"
    assert "sensitivity_contract_content_digest_mismatch" in result["reason_codes"]
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"


def test_sensitivity_paths_sort_numeric_array_indices_consistently():
    baseline = payload(count=12, pitch=4.0)
    variant = payload(count=12, pitch=2.0)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    changed_paths = sorted(
        f"group_geometry.fasteners[{index}].center_in[0]"
        for index in range(1, 12)
    )
    contract = {
        "contract_id": "synthetic-twelve-fastener-pitch-change",
        "source_id": "synthetic-fixture/twelve-fastener-pitch-change",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": changed_paths,
    }
    binding = bind_sensitivity_contract(contract)

    result = evaluate_group_factor_sensitivity(
        baseline,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )

    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["changed_input_paths"] == changed_paths
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"


def test_sensitivity_list_growth_requires_the_added_item_path():
    baseline = payload(count=3)
    variant = copy.deepcopy(baseline)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings(
        "sensitivity", side_member_ids=("side-01", "side-02")
    )
    variant["members"]["shear_planes"] = 2
    variant["members"]["side_members"].append(
        {
            "member_id": "side-02",
            "material": "wood",
            "elastic_modulus_psi": 1_400_000.0,
            "gross_section_area_in2": 5.0,
            "grain_axis_xyz": [1.0, 0.0, 0.0],
        }
    )

    def evaluate_with_paths(paths):
        contract = {
            "contract_id": "synthetic-side-member-growth",
            "source_id": "synthetic-fixture/side-member-growth",
            "sha256": "pending-digest",
            "review_status": "coordinator_reviewed",
            "classification": "composite_scenario",
            "candidate_id": "synthetic-only",
            "revision_id": "fixture-v1",
            "group_id": "group-01",
            "baseline_scenario_id": "baseline",
            "sensitivity_scenario_id": "sensitivity",
            "changed_input_paths": paths,
        }
        binding = bind_sensitivity_contract(contract)
        return evaluate_group_factor_sensitivity(
            baseline,
            variant,
            baseline_expected_bindings=bindings(),
            baseline_expected_payload_sha256=canonical_group_record_sha256(
                baseline
            ),
            sensitivity_expected_bindings=bindings(
                "sensitivity", side_member_ids=("side-01", "side-02")
            ),
            sensitivity_expected_payload_sha256=canonical_group_record_sha256(
                variant
            ),
            expected_sensitivity_contract=contract,
            expected_sensitivity_binding=binding,
        )

    length_only = evaluate_with_paths(
        ["members.shear_planes", "members.side_members.length"]
    )
    assert length_only["status"] == "pending"
    assert (
        "sensitivity_changed_input_paths_do_not_match_contract"
        in length_only["reason_codes"]
    )

    complete = evaluate_with_paths(
        [
            "members.shear_planes",
            "members.side_members.length",
            "members.side_members[1]",
        ]
    )
    assert complete["status"] == "calculated_method_sensitivity_only"
    assert complete["changed_input_paths"] == [
        "members.shear_planes",
        "members.side_members.length",
        "members.side_members[1]",
    ]
    assert complete["capacity"] is None
    assert complete["criterion_disposition"] == "pending"


def test_sensitivity_list_shrink_requires_the_removed_item_path():
    baseline = payload(count=3)
    baseline["source_bindings"] = bindings(
        "baseline", side_member_ids=("side-01", "side-02")
    )
    baseline["members"]["shear_planes"] = 2
    baseline["members"]["side_members"].append(
        {
            "member_id": "side-02",
            "material": "wood",
            "elastic_modulus_psi": 1_400_000.0,
            "gross_section_area_in2": 5.0,
            "grain_axis_xyz": [1.0, 0.0, 0.0],
        }
    )
    variant = payload(count=3)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")

    def evaluate_with_paths(paths):
        contract = {
            "contract_id": "synthetic-side-member-removal",
            "source_id": "synthetic-fixture/side-member-removal",
            "sha256": "pending-digest",
            "review_status": "coordinator_reviewed",
            "classification": "composite_scenario",
            "candidate_id": "synthetic-only",
            "revision_id": "fixture-v1",
            "group_id": "group-01",
            "baseline_scenario_id": "baseline",
            "sensitivity_scenario_id": "sensitivity",
            "changed_input_paths": paths,
        }
        binding = bind_sensitivity_contract(contract)
        return evaluate_group_factor_sensitivity(
            baseline,
            variant,
            baseline_expected_bindings=bindings(
                "baseline", side_member_ids=("side-01", "side-02")
            ),
            baseline_expected_payload_sha256=canonical_group_record_sha256(
                baseline
            ),
            sensitivity_expected_bindings=bindings("sensitivity"),
            sensitivity_expected_payload_sha256=canonical_group_record_sha256(
                variant
            ),
            expected_sensitivity_contract=contract,
            expected_sensitivity_binding=binding,
        )

    length_only = evaluate_with_paths(
        ["members.shear_planes", "members.side_members.length"]
    )
    assert length_only["status"] == "pending"
    assert (
        "sensitivity_changed_input_paths_do_not_match_contract"
        in length_only["reason_codes"]
    )

    complete = evaluate_with_paths(
        [
            "members.shear_planes",
            "members.side_members.length",
            "members.side_members[1]",
        ]
    )
    assert complete["status"] == "calculated_method_sensitivity_only"
    assert complete["changed_input_paths"] == [
        "members.shear_planes",
        "members.side_members.length",
        "members.side_members[1]",
    ]
    assert complete["capacity"] is None
    assert complete["criterion_disposition"] == "pending"


def test_sensitivity_path_escaping_distinguishes_literal_and_nested_keys():
    def calculate(baseline_extension, sensitivity_extension, contract_id):
        baseline = payload(count=3)
        variant = payload(count=3)
        variant["scenario_id"] = "sensitivity"
        variant["source_bindings"] = bindings("sensitivity")
        baseline["producer_extension"] = baseline_extension
        variant["producer_extension"] = sensitivity_extension
        contract = {
            "contract_id": contract_id,
            "source_id": f"synthetic-fixture/{contract_id}",
            "sha256": "pending-digest",
            "review_status": "coordinator_reviewed",
            "classification": "composite_scenario",
            "candidate_id": "synthetic-only",
            "revision_id": "fixture-v1",
            "group_id": "group-01",
            "baseline_scenario_id": "baseline",
            "sensitivity_scenario_id": "sensitivity",
            "changed_input_paths": ["producer_extension.a\\.b"],
        }
        if contract_id.endswith("nested"):
            contract["changed_input_paths"] = ["producer_extension.a.b"]
        binding = bind_sensitivity_contract(contract)
        return evaluate_group_factor_sensitivity(
            baseline,
            variant,
            baseline_expected_bindings=bindings(),
            baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
            sensitivity_expected_bindings=bindings("sensitivity"),
            sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
            expected_sensitivity_contract=contract,
            expected_sensitivity_binding=binding,
        )

    literal_key = calculate({"a.b": 1}, {"a.b": 2}, "literal-key-change")
    nested_keys = calculate(
        {"a": {"b": 1}}, {"a": {"b": 2}}, "nested-key-change-nested"
    )

    assert literal_key["status"] == "calculated_method_sensitivity_only"
    assert nested_keys["status"] == "calculated_method_sensitivity_only"
    assert literal_key["changed_input_paths"] == ["producer_extension.a\\.b"]
    assert nested_keys["changed_input_paths"] == ["producer_extension.a.b"]
    assert literal_key["changed_input_paths"] != nested_keys["changed_input_paths"]


@pytest.mark.parametrize(
    ("key", "encoded_key"),
    [
        ("a.b", r"a\.b"),
        ("a[0]", r"a\[0\]"),
        (r"a\b", r"a\\b"),
        ("", r"\e"),
        (" ", r"\u0020"),
        ("\t", r"\u0009"),
    ],
)
def test_changed_payload_paths_encode_special_object_keys(key, encoded_key):
    actual = _changed_payload_paths(
        {"producer_extension": {key: 1}},
        {"producer_extension": {key: 2}},
    )

    assert actual == [f"producer_extension.{encoded_key}"]


def test_sensitivity_contract_accepts_encoded_whitespace_only_root_key():
    baseline = payload(count=3)
    variant = payload(count=3)
    variant["scenario_id"] = "sensitivity"
    variant["source_bindings"] = bindings("sensitivity")
    baseline[" "] = 1
    variant[" "] = 2
    contract = {
        "contract_id": "synthetic-whitespace-root-key",
        "source_id": "synthetic-fixture/whitespace-root-key",
        "sha256": "pending-digest",
        "review_status": "coordinator_reviewed",
        "classification": "composite_scenario",
        "candidate_id": "synthetic-only",
        "revision_id": "fixture-v1",
        "group_id": "group-01",
        "baseline_scenario_id": "baseline",
        "sensitivity_scenario_id": "sensitivity",
        "changed_input_paths": [r"\u0020"],
    }
    binding = bind_sensitivity_contract(contract)

    result = evaluate_group_factor_sensitivity(
        baseline,
        variant,
        baseline_expected_bindings=bindings(),
        baseline_expected_payload_sha256=canonical_group_record_sha256(baseline),
        sensitivity_expected_bindings=bindings("sensitivity"),
        sensitivity_expected_payload_sha256=canonical_group_record_sha256(variant),
        expected_sensitivity_contract=contract,
        expected_sensitivity_binding=binding,
    )

    assert result["status"] == "calculated_method_sensitivity_only"
    assert result["changed_input_paths"] == [r"\u0020"]
    assert result["capacity"] is None
    assert result["criterion_disposition"] == "pending"
