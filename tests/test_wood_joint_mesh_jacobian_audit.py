"""Focused tests for offline C3D10 Gauss5 Jacobian calculations."""

from __future__ import annotations

import hashlib
import json
import math

import pytest

from fea import wood_joint_mesh_jacobian_audit as audit


def _linear_unit_tetrahedron() -> tuple[tuple[float, float, float], ...]:
    return (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
        (0.5, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (0.0, 0.5, 0.0),
        (0.0, 0.0, 0.5),
        (0.5, 0.0, 0.5),
        (0.0, 0.5, 0.5),
    )


def test_pinned_gmsh_gauss5_rule_has_14_positive_points_and_reference_volume():
    summary = audit.validate_gauss5_rule()

    assert summary["point_count"] == 14
    assert summary["minimum_weight"] == pytest.approx(0.00709100346285)
    assert summary["weight_sum"] == pytest.approx(1 / 6, abs=5e-11)


def test_linear_c3d10_shape_derivatives_sum_to_zero_and_integrate_unit_tetrahedron():
    derivatives = audit.c3d10_shape_derivatives((0.17, 0.21, 0.19))
    assert len(derivatives) == 10
    for natural_axis in range(3):
        assert math.fsum(row[natural_axis] for row in derivatives) == pytest.approx(0.0, abs=1e-14)

    integrated = audit.integrate_c3d10_element(_linear_unit_tetrahedron())

    assert integrated["jacobian_determinant_count"] == 14
    assert integrated["all_jacobians_positive"] is True
    assert integrated["minimum_jacobian_determinant_mm3"] == pytest.approx(1.0)
    assert integrated["integrated_volume_mm3"] == pytest.approx(1 / 6, abs=5e-11)


def test_curved_c3d10_edge_node_changes_jacobian_and_integrated_volume_exactly():
    edge_offset_mm = 0.05
    coordinates = list(_linear_unit_tetrahedron())
    coordinates[4] = (0.5, 0.0, edge_offset_mm)

    integrated = audit.integrate_c3d10_element(tuple(coordinates))
    for row in integrated["determinants"]:
        reference_r = row["reference_point"][0]
        expected = 1 - 4 * edge_offset_mm * reference_r
        assert row["determinant_mm3"] == pytest.approx(expected, abs=1e-13)
        assert row["determinant_mm3"] > 0
    assert integrated["integrated_volume_mm3"] == pytest.approx(
        1 / 6 - edge_offset_mm / 6,
        abs=5e-11,
    )


def test_rule_rejects_duplicate_or_negative_weight_points():
    first = audit.GAUSS5_TETRAHEDRON_14[0]
    duplicate_rule = (first,) * 14
    negative_weight_rule = (*audit.GAUSS5_TETRAHEDRON_14[:-1], (audit.GAUSS5_TETRAHEDRON_14[-1][0], -0.1))

    with pytest.raises(ValueError, match="duplicate"):
        audit.validate_gauss5_rule(duplicate_rule)
    with pytest.raises(ValueError, match="positive"):
        audit.validate_gauss5_rule(negative_weight_rule)


def test_geometry_deck_parser_requires_all_32_expected_c3d10_body_sets(tmp_path):
    nodes = _linear_unit_tetrahedron()
    lines = ["*HEADING", "mesh only", "*NODE"]
    lines.extend(f"{index + 1},{x},{y},{z}" for index, (x, y, z) in enumerate(nodes))
    for index, body_id in enumerate(sorted(audit.EXPECTED_BODY_IDS), 1):
        element_nodes = ",".join(str(value) for value in range(1, 11))
        lines.extend(
            [
                f"*ELEMENT,TYPE=C3D10,ELSET=METAL_{body_id.upper()}",
                f"{index},{element_nodes}",
            ]
        )
    deck = tmp_path / "mesh.inp"
    deck.write_text("\n".join(lines) + "\n")

    parsed_nodes, parsed_bodies = audit.parse_c3d10_deck(deck)

    assert len(parsed_nodes) == 10
    assert set(parsed_bodies) == audit.EXPECTED_BODY_IDS
    assert all(len(elements) == 1 for elements in parsed_bodies.values())


def test_geometry_deck_parser_rejects_non_mesh_mechanics_cards(tmp_path):
    deck = tmp_path / "mesh.inp"
    deck.write_text("*HEADING\nmesh only\n*MATERIAL,NAME=STEEL\n")

    with pytest.raises(ValueError, match="unexpected card"):
        audit.parse_c3d10_deck(deck)


def _minimal_wj24_wood_report():
    return {
        "schema": audit.EXPECTED_WJ24_WOOD_REPORT_SCHEMA,
        "status": audit.EXPECTED_WJ24_WOOD_REPORT_STATUS,
        "body_count": len(audit.EXPECTED_WJ24_WOOD_BODY_IDS),
        "completed_body_ids": list(audit.EXPECTED_WJ24_WOOD_BODY_ID_ORDER),
        "runtime": {"gmsh_version": audit.EXPECTED_GMSH_VERSION},
        "mesh_scope": {
            "WJ24_baseline_only": True,
            "WJ24_finished_wood_bodies": 5,
            "hardware_bodies_meshed": 0,
            "independent_body_models": 5,
        },
        "WJ24_G7_relief_variant_included": False,
        "accepted": False,
        "solved": False,
        "capacity_or_release_claim": False,
        "full_candidate_acceptance_claim": False,
        "contact_or_interface_classification_assigned": False,
        "output_contains_material_contact_tie_load_or_solver_cards": False,
        "bodies": {
            body_id: {
                "WJ24_finished_geometry": {"volume_mm3": 125.0},
                "imported_cad": {"volume_mm3": 125.0},
            }
            for body_id in audit.EXPECTED_WJ24_WOOD_BODY_ID_ORDER
        },
    }


def test_wj24_mesh_contract_selects_exact_wood_body_ids_and_source_volume_field():
    report = _minimal_wj24_wood_report()
    report["bodies"]["base_principal_center_right"]["WJ24_finished_geometry"][
        "volume_mm3"
    ] = 126.5
    report["bodies"]["base_principal_center_right"]["imported_cad"][
        "volume_mm3"
    ] = 126.0

    contract, reported_bodies = audit.validate_mesh_report_contract(report)

    assert contract is audit.WJ24_WOOD_REPORT_CONTRACT
    assert contract.body_ids == audit.EXPECTED_WJ24_WOOD_BODY_IDS
    assert contract.source_volume_field == "WJ24_finished_geometry"
    assert set(reported_bodies) == audit.EXPECTED_WJ24_WOOD_BODY_IDS
    assert audit._source_geometry_volume(
        reported_bodies["base_principal_center_right"],
        contract,
        "base_principal_center_right",
    ) == pytest.approx(126.5)


def test_wj24_mesh_contract_rejects_unknown_report_schema():
    report = _minimal_wj24_wood_report()
    report["schema"] = "wood_joint_unknown_mesh/v1"

    with pytest.raises(ValueError, match="unsupported C3D10 mesh report schema"):
        audit.validate_mesh_report_contract(report)


def test_wj24_mesh_contract_rejects_wrong_completion_status():
    report = _minimal_wj24_wood_report()
    report["status"] = "VERIFIED_C3D10_MESH_ONLY_NO_SOLVER"

    with pytest.raises(ValueError, match="status does not match the wj24_finished_wood contract"):
        audit.validate_mesh_report_contract(report)


def test_wj24_mesh_contract_rejects_wrong_body_inventory():
    report = _minimal_wj24_wood_report()
    report["bodies"]["not_a_wj24_body"] = report["bodies"].pop(
        "base_principal_center_right"
    )

    with pytest.raises(ValueError, match="body inventory differs from the exact five-body contract"):
        audit.validate_mesh_report_contract(report)


@pytest.mark.parametrize("missing", ("record", "volume"))
def test_wj24_mesh_contract_rejects_missing_source_geometry_volume(missing):
    report = _minimal_wj24_wood_report()
    body = report["bodies"]["base_principal_center_right"]
    if missing == "record":
        body.pop("WJ24_finished_geometry")
    else:
        body["WJ24_finished_geometry"].pop("volume_mm3")

    with pytest.raises(ValueError, match="WJ24_finished_geometry"):
        audit.validate_mesh_report_contract(report)


def test_wj24_mesh_deck_parser_accepts_only_the_five_unprefixed_wood_elsets(tmp_path):
    nodes = _linear_unit_tetrahedron()
    lines = ["*HEADING", "WJ24 wood mesh only", "*NODE"]
    lines.extend(f"{index + 1},{x},{y},{z}" for index, (x, y, z) in enumerate(nodes))
    for index, body_id in enumerate(audit.EXPECTED_WJ24_WOOD_BODY_ID_ORDER, 1):
        element_nodes = ",".join(str(value) for value in range(1, 11))
        lines.extend(
            [
                f"*ELEMENT,TYPE=C3D10,ELSET={body_id.upper()}",
                f"{index},{element_nodes}",
            ]
        )
    deck = tmp_path / "wj24-mesh.inp"
    deck.write_text("\n".join(lines) + "\n")

    parsed_nodes, parsed_bodies = audit.parse_c3d10_deck(
        deck,
        expected_body_ids=audit.EXPECTED_WJ24_WOOD_BODY_IDS,
        elset_prefix=audit.EXPECTED_WJ24_CALCULIX_ELSET_PREFIX,
    )

    assert len(parsed_nodes) == 10
    assert set(parsed_bodies) == audit.EXPECTED_WJ24_WOOD_BODY_IDS
    assert all(len(elements) == 1 for elements in parsed_bodies.values())


def test_wj24_audit_uses_finished_geometry_volume_reference(tmp_path):
    nodes = _linear_unit_tetrahedron()
    volume = 1 / 6
    lines = ["*HEADING", "WJ24 synthetic geometry audit", "*NODE"]
    lines.extend(f"{index + 1},{x},{y},{z}" for index, (x, y, z) in enumerate(nodes))
    bodies = {}
    for element_id, body_id in enumerate(audit.EXPECTED_WJ24_WOOD_BODY_ID_ORDER, 1):
        element_nodes = ",".join(str(value) for value in range(1, 11))
        lines.extend(
            [
                f"*ELEMENT,TYPE=C3D10,ELSET={body_id.upper()}",
                f"{element_id},{element_nodes}",
            ]
        )
        bodies[body_id] = {
            "elements": [element_id],
            "nodes": list(range(1, 11)),
            "WJ24_finished_geometry": {"volume_mm3": volume},
            "imported_cad": {
                "volume_mm3": volume,
                "relative_volume_tolerance": 1e-7,
                "relative_volume_error_vs_export": 0.0,
            },
            "integrated_mesh_audit": {
                "cad_volume_mm3": volume,
                "integrated_mesh_volume_mm3": volume,
                "integration_jacobian_count": 14,
                "minimum_integration_jacobian": 1.0,
                "relative_volume_error": 0.0,
                "relative_volume_tolerance": 0.001,
                "sampled_jacobian_count": 1,
            },
            "integration_rule": {
                "minimum_weight": audit.validate_gauss5_rule()["minimum_weight"],
                "weights_per_element": 14,
            },
        }
    deck_path = tmp_path / "mesh.inp"
    deck_bytes = ("\n".join(lines) + "\n").encode()
    deck_path.write_bytes(deck_bytes)
    report = _minimal_wj24_wood_report()
    report["bodies"] = bodies
    report["mesh_input_sha256"] = hashlib.sha256(deck_bytes).hexdigest()
    (tmp_path / "mesh.json").write_text(json.dumps(report))

    result = audit.audit_mesh_directory(tmp_path)

    assert result["audit_scope"]["input_profile"] == "wj24_finished_wood"
    assert result["audit_scope"]["geometry_volume_reference_field"] == (
        "WJ24_finished_geometry.volume_mm3"
    )
    assert result["totals"]["element_count"] == 5
    assert result["totals"][
        "all_5_WJ24_finished_wood_bodies_pass_recorded_relative_volume_tolerance"
    ] is True
    assert all(
        row["relative_volume_error_vs_WJ24_finished_geometry"] == pytest.approx(0.0)
        for row in result["per_body"].values()
    )


def test_hardware_mesh_contract_retains_its_pinned_report_identity():
    report = {
        "schema": audit.EXPECTED_REPORT_SCHEMA,
        "status": audit.EXPECTED_REPORT_STATUS,
        "scenario_id": audit.EXPECTED_SCENARIO_ID,
        "runtime": {"gmsh_version": audit.EXPECTED_GMSH_VERSION},
        "gmsh_to_calculix_quadratic_node_order": [0, 1, 2, 3, 4, 5, 6, 7, 9, 8],
        "bodies": {
            body_id: {"imported_cad": {"volume_mm3": 125.0}}
            for body_id in audit.EXPECTED_HARDWARE_BODY_IDS
        },
    }

    contract, reported_bodies = audit.validate_mesh_report_contract(report)

    assert contract is audit.HARDWARE_REPORT_CONTRACT
    assert contract.body_ids == audit.EXPECTED_HARDWARE_BODY_IDS
    assert contract.source_volume_field == "imported_cad"
    assert set(reported_bodies) == audit.EXPECTED_HARDWARE_BODY_IDS
