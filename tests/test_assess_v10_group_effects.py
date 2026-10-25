"""Focused source-contract tests for the current112 group-effects assessor."""

from __future__ import annotations

import pytest

from scripts.assess_v10_group_effects import (
    _build_caltrans_example12_benchmark,
    _row_case_action_refs,
    build_physical_row_roles,
    build_wood_only_geometry_descriptors,
    validate_sha256_map,
)


def _shaft(
    axis_id: str,
    point: list[float],
    *,
    attachments: list[dict] | None = None,
    diameter: float = 9.525,
    surfaces: list[dict] | None = None,
) -> dict:
    return {
        "axis_id": axis_id,
        "body": f"shaft/{axis_id}",
        "point": point,
        "basis": [[0.0, 0.0, 1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        "diameter_mm": diameter,
        "bore_diameter_mm": diameter + 0.8,
        "source_axis": {
            "point_xyz_mm": point,
            "direction_xyz": [0.0, 0.0, 1.0],
            "attachments": attachments or [],
        },
        "surfaces": surfaces
        or [
            {
                "host": "beam",
                "kind": "wood",
                "interval_mm": [0.0, 38.1],
                "bore_diameter_mm": diameter + 0.8,
                "grain_axis_xyz": [1.0, 0.0, 0.0],
                "source_axis_id": axis_id,
            },
            {
                "host": "angle",
                "kind": "steel",
                "interval_mm": [38.1, 44.45],
                "bore_diameter_mm": 10.0,
                "receiver": "beam",
                "source_axis_id": axis_id,
            },
        ],
    }


def _wood_surface(host: str, grain: list[float], axis_id: str) -> dict:
    return {
        "host": host,
        "kind": "wood",
        "interval_mm": [0.0, 38.1],
        "bore_diameter_mm": 10.31875,
        "grain_axis_xyz": grain,
        "source_axis_id": axis_id,
    }


def test_caltrans_example12_benchmark_matches_published_rounding_and_stays_method_only():
    result = _build_caltrans_example12_benchmark()

    assert result["status"] == "PASS_METHOD_BENCHMARK_ONLY"
    assert result["inputs"] == {
        "fastener_count": 3,
        "diameter_in": 0.625,
        "pitch_in": 2.5,
        "main_E_psi": 1_600_000.0,
        "main_A_in2": 144.0,
        "side_E_psi": 1_600_000.0,
        "side_A_in2": 10.88,
        "nominal_gamma_lbf_per_in": pytest.approx(88939.05919223567),
    }
    comparison = result["result"]
    assert comparison["NDS_Cg_method_only"] == pytest.approx(0.9806318451462117)
    assert comparison["distribution_Cg"] == pytest.approx(0.9806318451462125)
    assert comparison["matches_within_tolerance"] is True
    assert comparison["capacity"] is None
    assert comparison["criterion_disposition"] == "pending"


def test_source_pin_mutation_is_rejected():
    validate_sha256_map({"bank": "a" * 64}, {"bank": "a" * 64})

    with pytest.raises(ValueError, match="source pin mismatch"):
        validate_sha256_map({"bank": "b" * 64}, {"bank": "a" * 64})

    with pytest.raises(ValueError, match=r"missing=\['bank'\]"):
        validate_sha256_map({}, {"bank": "a" * 64})


def test_attachment_row_roles_preserve_media_and_leave_cg_unresolved():
    role = {
        "duty_id": "clip-test",
        "angle_id": "angle-test",
        "flange": "beam",
        "row": "far",
        "receiver": "beam",
        "receivers": ["beam"],
    }
    shafts = [
        _shaft("bolt-a", [0.0, 0.0, 0.0], attachments=[role]),
        _shaft("bolt-b", [50.8, 0.0, 0.0], attachments=[role]),
        _shaft(
            "cleat-only",
            [0.0, 25.4, 0.0],
            surfaces=[_wood_surface("cleat", [0.0, 0.0, 1.0], "cleat-only")],
        ),
    ]
    inputs = {
        "shafts": shafts,
        "scenario": {"timber_e_mpa": 11_000.0},
        "timber_rows": [{"name": "beam", "width_mm": 38.1, "depth_mm": 139.7}],
    }
    components = [{"component_id": "component-a", "axis_ids": ["bolt-a", "bolt-b", "cleat-only"]}]

    rows, topology_only = build_physical_row_roles(
        inputs,
        components,
        {"properties": {"EA_N": 14_000_000.0}},
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["row_axis_world_xyz"] == pytest.approx([1.0, 0.0, 0.0])
    assert row["uniform_pitch_mm"] == pytest.approx(50.8)
    assert row["nominal_fastener_diameter_mm"] == pytest.approx(9.525)
    assert row["NDS_shear_plane_count"] is None
    assert row["NDS_effective_member_EA_N"] is None
    assert row["NDS_effective_slip_modulus_N_per_mm"] is None
    assert row["actual_Cg"] is None
    assert row["applicability_status"] == "UNRESOLVED"
    assert {surface["kind"] for shaft in row["fastener_axes"] for surface in shaft["surface_stack"]} == {
        "wood",
        "steel",
    }
    assert [item["axis_id"] for item in topology_only] == ["cleat-only"]
    assert topology_only[0]["row_identity_status"] == "UNRESOLVED_NO_SOURCE_ATTACHMENT_ROW"
    assert topology_only[0]["surface_stack"][0]["host_body_id"] == "cleat"


def test_row_case_action_reference_keeps_signed_resultants_and_receiver_sign():
    row = {
        "fastener_axes": [{"axis_id": "bolt-a"}, {"axis_id": "bolt-b"}],
        "attachment_role": {"receiver": "beam", "receivers": ["beam"]},
    }
    component_case = {
        "case_id": "a12-rear",
        "component_id": "test-component",
        "boundary_port_wrench_totals": [
            {
                "component_body": "shaft/bolt-a",
                "external_body": "beam",
                "source_family": "common_shaft_bearing_actions",
                "action_count": 2,
                "wrench_on_component": {
                    "force_xyz_n": [10.0, -5.0, 0.0],
                    "moment_about_global_origin_xyz_nmm": [1.0, 2.0, 3.0],
                },
                "wrench_on_receiver": {
                    "force_xyz_n": [-10.0, 5.0, 0.0],
                    "moment_about_global_origin_xyz_nmm": [-1.0, -2.0, -3.0],
                },
            }
        ],
        "full_signed_point_action_source": {"path": "frozen.json", "sha256": "c" * 64},
    }

    result = _row_case_action_refs(row, component_case)

    assert result["receiver_wrenches"][0]["force_xyz_N"] == [-10.0, 5.0, 0.0]
    assert result["receiver_wrenches"][0]["moment_about_global_origin_xyz_Nmm"] == [
        -1.0,
        -2.0,
        -3.0,
    ]
    assert result["signed_axis_receiver_wrench_rows"][0]["axis_id"] == "bolt-a"
    assert result["receiver_wrenches"][0]["resultant_direction_xyz"] == pytest.approx(
        [-0.8944271909999159, 0.4472135954999579, 0.0]
    )


def test_six_scope_geometry_descriptors_keep_pairs_singletons_and_current_wrenches():
    shafts = [
        _shaft(
            "front-a",
            [0.0, 0.0, 0.0],
            surfaces=[
                _wood_surface("member-a", [1.0, 0.0, 0.0], "front-a"),
                _wood_surface("member-b", [0.0, 1.0, 0.0], "front-a"),
            ],
        ),
        _shaft(
            "front-b",
            [50.8, 0.0, 0.0],
            surfaces=[
                _wood_surface("member-a", [1.0, 0.0, 0.0], "front-b"),
                _wood_surface("member-b", [0.0, 1.0, 0.0], "front-b"),
            ],
        ),
        _shaft(
            "rear-single",
            [0.0, 100.0, 0.0],
            surfaces=[
                _wood_surface("member-a", [1.0, 0.0, 0.0], "rear-single"),
                _wood_surface("member-b", [0.0, 1.0, 0.0], "rear-single"),
            ],
        ),
    ]
    inputs = {
        "shafts": shafts,
        "timber_rows": [
            {"name": "member-a", "width_mm": 40.0, "depth_mm": 90.0},
            {"name": "member-b", "width_mm": 38.1, "depth_mm": 139.7},
        ],
        "scenario": {"timber_e_mpa": 11_000.0},
    }
    pair_scope = {
        "scope_id": "wood-pair",
        "axis_ids": ["front-a", "front-b"],
        "shaft_body_ids": ["shaft/front-a", "shaft/front-b"],
        "receiver_body_ids": ["member-a", "member-b"],
        "scope_rule": "two receivers remain separate",
    }
    single_scope = {
        "scope_id": "wood-single",
        "axis_ids": ["rear-single"],
        "shaft_body_ids": ["shaft/rear-single"],
        "receiver_body_ids": ["member-a", "member-b"],
        "scope_rule": "single fastener remains unresolved",
    }
    source_actions = [
        {
            "axis_id": "front-a",
            "receiver_body": "member-a",
            "action_on_receiver_body": {
                "body": "member-a",
                "force": [2.0, 0.0, 0.0],
                "point": [0.0, 0.0, 0.0],
                "couple": [0.0, 0.0, 1.0],
            },
        },
        {
            "axis_id": "front-b",
            "receiver_body": "member-a",
            "action_on_receiver_body": {
                "body": "member-a",
                "force": [-1.0, 0.0, 0.0],
                "point": [0.0, 2.0, 0.0],
                "couple": [0.0, 0.0, 0.0],
            },
        },
    ]
    wrench_cases = [
        {
            "case_id": case_id,
            "wood_only_joint_scopes": [
                {"scope_id": "wood-pair", "boundary_actions": source_actions},
                {"scope_id": "wood-single", "boundary_actions": []},
            ],
        }
        for case_id in ("a12-forward", "a12-left", "a12-rear", "k12-right", "k12-rear", "a1-rear")
    ]

    result = build_wood_only_geometry_descriptors(
        inputs,
        [pair_scope, single_scope],
        wrench_cases,
        {"properties": {"EA_N": 14_000_000.0}},
        "wrenches.json",
        "d" * 64,
    )

    pair, single = result
    assert pair["row_axis_world_xyz"] == pytest.approx([1.0, 0.0, 0.0])
    assert pair["row_spacing_mm"] == pytest.approx(50.8)
    assert pair["conditional_geometric_shear_plane_count"] == 1
    assert pair["NDS_shear_plane_count_adopted"] is None
    assert pair["member_ownership"][0]["gross_FE_axial_EA_reference"]["value"] == pytest.approx(
        11_000.0 * 40.0 * 90.0
    )
    assert pair["case_wrenches"][0]["receiver_resultant_wrenches"]["member-a"]["force_xyz_N"] == [
        1.0,
        0.0,
        0.0,
    ]
    assert pair["case_wrenches"][0]["receiver_resultant_wrenches"]["member-a"][
        "moment_about_global_origin_xyz_Nmm"
    ] == [0.0, 0.0, 3.0]
    assert pair["actual_Cg"] is None
    assert single["fastener_count"] == 1
    assert single["row_axis_world_xyz"] is None
    assert single["row_spacing_mm"] is None
    assert single["formula_gamma_sensitivity_only"] is None
    assert single["actual_Cg"] is None


def test_duplicate_axis_ids_and_bad_row_geometry_fail_closed():
    role = {
        "duty_id": "clip-test",
        "angle_id": "angle-test",
        "flange": "beam",
        "row": "far",
        "receiver": "beam",
        "receivers": ["beam"],
    }
    duplicate_inputs = {
        "shafts": [
            _shaft("bolt-a", [0.0, 0.0, 0.0], attachments=[role]),
            _shaft("bolt-a", [50.8, 0.0, 0.0], attachments=[role]),
        ],
        "scenario": {"timber_e_mpa": 11_000.0},
        "timber_rows": [{"name": "beam", "width_mm": 40.0, "depth_mm": 90.0}],
    }
    with pytest.raises(ValueError, match="duplicate prepared shaft axis"):
        build_physical_row_roles(
            duplicate_inputs,
            [{"component_id": "component-a", "axis_ids": ["bolt-a"]}],
            {"properties": {"EA_N": 1.0}},
        )
