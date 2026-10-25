"""Fail-closed tests for the aggregate physical-row capacity adapter."""

from __future__ import annotations

import copy

import pytest

from mini_moonboard.nds_2024_group_action import (
    SCHEMA_VERSION as NDS_SCHEMA,
)
from mini_moonboard.nds_2024_group_action import (
    SOURCE_ROLES,
    canonical_group_record_sha256,
)
from mini_moonboard.physical_row_group_capacity import (
    GROUP_FACTOR_SCHEMA_VERSION,
    N_TO_LBF,
    SCHEMA_VERSION,
    canonical_record_sha256,
    evaluate_nds_group_factor_equation,
    evaluate_physical_row_group_capacity,
)
from mini_moonboard.serial_row_benchmark import compare_serial_row_to_nds


def _nds_bindings() -> dict:
    values = {
        role: {
            "source_id": f"fixture/{role}",
            "sha256": f"{index + 1:x}" * 64,
        }
        for index, role in enumerate(SOURCE_ROLES)
    }
    values["member_sections"].update(
        main_member_id="main",
        side_member_ids=["side"],
        shear_planes=1,
    )
    return values


def _nds_record(*, grain=(1.0, 0.0, 0.0), load=(100.0, 0.0, 0.0)) -> dict:
    return {
        "schema": NDS_SCHEMA,
        "candidate_id": "fixture",
        "revision_id": "fixture-v1",
        "group_id": "row-1",
        "scenario_id": "aligned",
        "source_bindings": _nds_bindings(),
        "group_geometry": {
            "row_axis_xyz": [1.0, 0.0, 0.0],
            "fasteners": [
                {
                    "fastener_id": "b1",
                    "center_in": [0.0, 0.0, 0.0],
                    "nominal_diameter_in": 0.5,
                    "type": "dowel",
                },
                {
                    "fastener_id": "b2",
                    "center_in": [4.0, 0.0, 0.0],
                    "nominal_diameter_in": 0.5,
                    "type": "dowel",
                },
            ],
        },
        "load_case": {"case_id": "case-1", "lateral_resultant_xyz_lbf": list(load)},
        "members": {
            "shear_planes": 1,
            "main": {
                "member_id": "main",
                "material": "wood",
                "elastic_modulus_psi": 1_400_000.0,
                "gross_section_area_in2": 10.0,
                "grain_axis_xyz": list(grain),
            },
            "side_members": [
                {
                    "member_id": "side",
                    "material": "wood",
                    "elastic_modulus_psi": 1_400_000.0,
                    "gross_section_area_in2": 10.0,
                    "grain_axis_xyz": list(grain),
                }
            ],
        },
    }


def _row_record(*, couple=(0.0, 0.0, 0.0), status="independently_source_bound") -> dict:
    half_force_n = 50.0 / N_TO_LBF
    return {
        "schema": SCHEMA_VERSION,
        "candidate_id": "fixture",
        "revision_id": "fixture-v1",
        "group_id": "row-1",
        "case_id": "case-1",
        "scenario_id": "aligned",
        "row_axis_xyz": [1.0, 0.0, 0.0],
        "reference_point_xyz_mm": [50.8, 0.0, 0.0],
        "source_bindings": {
            "geometry": {"source_id": "fixture/geometry", "sha256": "a" * 64},
            "actions": {"source_id": "fixture/actions", "sha256": "b" * 64},
            "single_bolt_capacity": {"source_id": "fixture/z", "sha256": "c" * 64},
        },
        "qualification": {
            "status": status,
            "basis": "synthetic test fixture; never candidate acceptance",
            "row_ownership": "two-fastener single shear row",
            "load_path_basis": "fixture source pins",
        },
        "fasteners": [
            {
                "fastener_id": "b1",
                "point_xyz_mm": [0.0, 0.0, 0.0],
                "bolt_axis_xyz": [0.0, 0.0, 1.0],
                "force_xyz_n": [half_force_n, 0.0, 0.0],
                "moment_xyz_nmm_at_point": list(couple),
                "moment_point_xyz_mm": [0.0, 0.0, 0.0],
                "single_bolt_Z_lbf": 100.0,
                "single_bolt_source_id": "fixture/Z/b1",
            },
            {
                "fastener_id": "b2",
                "point_xyz_mm": [101.6, 0.0, 0.0],
                "bolt_axis_xyz": [0.0, 0.0, 1.0],
                "force_xyz_n": [half_force_n, 0.0, 0.0],
                "moment_xyz_nmm_at_point": list(couple),
                "moment_point_xyz_mm": [101.6, 0.0, 0.0],
                "single_bolt_Z_lbf": 120.0,
                "single_bolt_source_id": "fixture/Z/b2",
            },
        ],
    }


def _evaluate(row: dict, nds: dict) -> dict:
    return evaluate_physical_row_group_capacity(
        row,
        expected_row_record_sha256=canonical_record_sha256(row),
        expected_row_sources=row["source_bindings"],
        nds_group_record=nds,
        expected_nds_bindings=nds["source_bindings"],
        expected_nds_record_sha256=canonical_group_record_sha256(nds),
    )


def test_aligned_source_bound_row_uses_cg_once_at_group_capacity():
    result = _evaluate(_row_record(), _nds_record())

    assert result["status"] == "calculated_method_only"
    expected_capacity = 2 * result["nds_group_factor"]["cg"] * 100.0
    assert result["group_lateral_capacity_lbf"] == pytest.approx(expected_capacity)
    assert result["group_lateral_row_demand_sum_abs_lbf"] == pytest.approx(100.0)
    assert result["row_lateral_utilization"] == pytest.approx(100.0 / expected_capacity)
    assert result["minimum_single_bolt_Z_lbf"] == 100.0
    assert result["complete_group_capacity"] is None
    assert result["complete_group_pass"] is None


def test_nonzero_free_couples_are_transported_and_keep_complete_pass_open():
    result = _evaluate(_row_record(couple=(0.0, 0.0, 30.0)), _nds_record())

    assert result["status"] == "calculated_method_only"
    assert result["transported_total_moment_about_reference_xyz_Nmm"] == pytest.approx(
        [0.0, 0.0, 60.0]
    )
    assert result["fasteners"][0]["moment_xyz_Nmm_at_source_point"] == [
        0.0,
        0.0,
        30.0,
    ]
    assert result["complete_group_pass"] is None
    assert "free couples and eccentric group action" in result["unresolved_conditions"]


def test_counteracting_transverse_forces_keep_full_wrench_and_block_row_scalar():
    row = _row_record()
    row["fasteners"][0]["force_xyz_n"][1] = 10.0
    row["fasteners"][1]["force_xyz_n"][1] = -10.0
    nds = _nds_record()
    result = _evaluate(row, nds)

    assert result["status"] == "pending"
    assert result["reason_codes"] == [
        "individual_fastener_lateral_force_not_parallel_to_NDS_row"
    ]
    assert result["misaligned_fastener_ids"] == ["b1", "b2"]
    assert result["lateral_resultant_balance_error_lbf"] == pytest.approx(
        0.0, abs=1e-12
    )
    # Net lateral action is row-parallel even though each fastener has a
    # transverse component. The scalar row criterion must not use cancellation
    # to conceal those individual actions.
    assert result["group_transverse_lateral_resultant_xyz_lbf"] == pytest.approx(
        [0.0, 0.0, 0.0]
    )
    assert result["transported_total_moment_about_reference_xyz_Nmm"] == pytest.approx(
        [0.0, 0.0, -1016.0]
    )
    assert result["max_individual_transverse_lateral_force_lbf"] == pytest.approx(
        10.0 * N_TO_LBF
    )
    assert result["group_lateral_capacity_lbf"] is None
    assert result["fasteners"][0]["moment_xyz_Nmm_at_source_point"] == [
        0.0,
        0.0,
        0.0,
    ]
    assert result["complete_group_pass"] is None


def test_oblique_grain_returns_no_actual_cg_but_preserves_wrench_inventory():
    nds = _nds_record(grain=(0.8660254037844386, 0.5, 0.0))
    row = _row_record(couple=(0.0, 0.0, 7.0))
    result = _evaluate(row, nds)

    assert result["status"] == "pending"
    assert result["cg"] is None
    assert result["group_lateral_capacity_lbf"] is None
    assert result["transported_total_moment_about_reference_xyz_Nmm"] == pytest.approx(
        [0.0, 0.0, 14.0]
    )
    assert result["complete_group_pass"] is None


def test_source_digest_or_binding_mismatch_fails_closed():
    row = _row_record()
    nds = _nds_record()
    row_result = evaluate_physical_row_group_capacity(
        row,
        expected_row_record_sha256="0" * 64,
        expected_row_sources=row["source_bindings"],
        nds_group_record=nds,
        expected_nds_bindings=nds["source_bindings"],
        expected_nds_record_sha256=canonical_group_record_sha256(nds),
    )
    assert row_result["status"] == "pending"
    assert row_result["group_lateral_capacity_lbf"] is None

    bad_sources = copy.deepcopy(row["source_bindings"])
    bad_sources["actions"]["sha256"] = "d" * 64
    source_result = evaluate_physical_row_group_capacity(
        row,
        expected_row_record_sha256=canonical_record_sha256(row),
        expected_row_sources=bad_sources,
        nds_group_record=nds,
        expected_nds_bindings=nds["source_bindings"],
        expected_nds_record_sha256=canonical_group_record_sha256(nds),
    )
    assert source_result["status"] == "pending"
    assert source_result["reason_codes"] == [
        "row_source_binding_mismatch_or_incomplete"
    ]


def test_candidate_scenario_case_identity_mismatch_fails_closed():
    row = _row_record()
    nds = _nds_record()
    nds["candidate_id"] = "different-candidate"
    result = _evaluate(row, nds)
    assert result["status"] == "pending"
    assert result["reason_codes"] == [
        "NDS_and_wrench_candidate_revision_or_group_identity_mismatch"
    ]


def test_missing_explicit_qualification_fails_closed():
    row = _row_record(status="unqualified")
    result = _evaluate(row, _nds_record())
    assert result["status"] == "pending"
    assert result["reason_codes"] == ["row_qualification_not_explicitly_supported"]


def _factor_input(
    *,
    n: int,
    pitch_in: float,
    diameter_in: float,
    ea_main_lbf: float,
    ea_side_lbf: float,
    connection_kind: str,
) -> dict:
    return {
        "schema": GROUP_FACTOR_SCHEMA_VERSION,
        "candidate_id": "synthetic-equation-fixture",
        "revision_id": "fixture-v1",
        "group_id": "group-1",
        "scenario_id": "benchmark-only",
        "case_id": "case-1",
        "fastener_count": n,
        "pitch_in": pitch_in,
        "diameter_in": diameter_in,
        "EA_main_lbf": ea_main_lbf,
        "EA_side_lbf": ea_side_lbf,
        "connection_kind": connection_kind,
        "source_bindings": {
            "primary_equation": {
                "source_id": "NDS-2024-11.3.6.1",
                "sha256": "1" * 64,
            },
            "input_record": {
                "source_id": "synthetic benchmark inputs",
                "sha256": "2" * 64,
            },
        },
    }


def test_equation_engine_matches_maintained_wood_wood_and_caltrans_benchmark():
    record = _factor_input(
        n=3,
        pitch_in=2.5,
        diameter_in=0.625,
        ea_main_lbf=1_600_000.0 * 144.0,
        ea_side_lbf=1_600_000.0 * 10.88,
        connection_kind="wood_wood",
    )
    result = evaluate_nds_group_factor_equation(
        record,
        expected_record_sha256=canonical_record_sha256(record),
        expected_sources=record["source_bindings"],
    )
    serial = compare_serial_row_to_nds(
        fastener_count=3,
        diameter_in=0.625,
        pitch_in=2.5,
        elastic_modulus_main_psi=1_600_000.0,
        area_main_in2=144.0,
        elastic_modulus_side_psi=1_600_000.0,
        area_side_in2=10.88,
    )

    assert result["status"] == "calculated_method_only"
    assert result["cg"] == pytest.approx(0.9806318451462117, abs=1e-12)
    assert result["cg"] == pytest.approx(serial.nds_cg, abs=1e-12)
    assert serial.matches_within_tolerance


def test_equation_engine_reproduces_saved_wood_metal_scenario():
    # Source-linked prior benchmark: header, 41.275 mm row, one gross steel
    # strip; formula verification only, not an actual connection factor.
    n_per_lbf = 4.4482216152605
    record = _factor_input(
        n=2,
        pitch_in=41.275 / 25.4,
        diameter_in=9.525 / 25.4,
        ea_main_lbf=58_716_527.082839996 / n_per_lbf,
        ea_side_lbf=112_903_000.0 / n_per_lbf,
        connection_kind="wood_metal",
    )
    result = evaluate_nds_group_factor_equation(
        record,
        expected_record_sha256=canonical_record_sha256(record),
        expected_sources=record["source_bindings"],
    )

    assert result["status"] == "calculated_method_only"
    assert result["gamma_lbf_per_in"] == pytest.approx(62_002.70911419921)
    assert result["cg"] == pytest.approx(0.9981822123468869, abs=1e-12)
    assert result["physical_applicability"].startswith("caller must establish")


def test_equation_engine_rejects_unpinned_or_unsupported_inputs():
    record = _factor_input(
        n=2,
        pitch_in=2.0,
        diameter_in=0.5,
        ea_main_lbf=1_000_000.0,
        ea_side_lbf=500_000.0,
        connection_kind="wood_steel_wood",
    )
    unsupported = evaluate_nds_group_factor_equation(
        record,
        expected_record_sha256=canonical_record_sha256(record),
        expected_sources=record["source_bindings"],
    )
    assert unsupported["status"] == "pending"
    assert unsupported["cg"] is None

    record["connection_kind"] = "wood_wood"
    unpinned = evaluate_nds_group_factor_equation(
        record,
        expected_record_sha256="0" * 64,
        expected_sources=record["source_bindings"],
    )
    assert unpinned["status"] == "pending"
    assert unpinned["cg"] is None
