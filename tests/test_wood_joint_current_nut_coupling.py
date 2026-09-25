"""Focused contracts for the current four-nut stiff-engagement sensitivity."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from fea import wood_joint_current_nut_coupling as coupling


def _cylindrical_nodes():
    nodes = {}
    node_id = 1
    for station in (-2.7, -1.1, 1.2, 2.8):
        for sector in range(16):
            angle = 2.0 * math.pi * sector / 16
            nodes[node_id] = (
                3.175 * math.cos(angle),
                3.175 * math.sin(angle),
                station,
            )
            node_id += 1
    return nodes


def test_weighted_rigid_fit_reproduces_six_motions_and_adjoint_wrench():
    fit = coupling.fit_rigid_motion(_cylindrical_nodes(), (0.0, 0.0, 0.0))

    assert fit["scaled_design_rank"] == 6
    assert fit["coefficient_matrix_rank"] == 6
    assert fit["weighting"] == "equal_weight_per_unique_SHA_bound_TRI6_surface_node"
    assert sum(fit["normalized_weights"]) == pytest.approx(1.0)
    assert all(weight > 0.0 for weight in fit["normalized_weights"])
    assert fit["scaled_design_condition_estimate_inf_norm"] < 100.0
    assert fit["affine_rigid_reproduction_max_abs_error"] < 1e-12
    assert fit["load_adjoint_wrench_audit"]["passed"] is True
    assert fit["load_adjoint_wrench_audit"]["max_scaled_error"] < 1e-12


def test_collinear_short_patch_reports_rank_deficiency():
    nodes = {
        1: (0.0, 0.0, -2.0),
        2: (0.0, 0.0, -1.0),
        3: (0.0, 0.0, 1.0),
        4: (0.0, 0.0, 2.0),
    }

    with pytest.raises(ValueError, match="nut-span shaft patch is rank deficient"):
        coupling.fit_rigid_motion(nodes, (0.0, 0.0, 0.0))


def test_actual_frozen_four_nut_spans_emit_only_control_equations_and_nsets(
    tmp_path: Path,
):
    output = tmp_path / "nut-coupling"
    report = coupling.prepare_current_nut_coupling(output_directory=output)

    assert report["status"] == coupling.STATUS
    assert report["candidate"]["physical_bolt_count"] == 4
    assert (
        report["source_binding"]["inventory_sha256"]
        == coupling.EXPECTED_INVENTORY_SHA256
    )
    assert (
        report["source_binding"]["mesh_report_sha256"]
        == coupling.EXPECTED_MESH_REPORT_SHA256
    )
    assert (
        report["source_binding"]["mesh_deck_sha256"]
        == coupling.EXPECTED_MESH_DECK_SHA256
    )
    assert (
        report["source_binding"]["classification_sha256"]
        == coupling.EXPECTED_CLASSIFICATION_SHA256
    )
    assert report["fresh_control_node_allocation"]["first_control_node_id"] == 116163
    assert report["fresh_control_node_allocation"]["last_control_node_id"] == 116170
    assert report["fresh_control_node_allocation"]["nut_control_nset_count"] == 4
    assert len(report["nsets"]) == 4
    assert len(report["equation_cards"]) == 24
    assert report["audits"]["all_source_and_control_equation_dofs_are_declared"] is True

    expected_patch_sizes = [251, 258, 254, 259]
    dependents = set()
    for axis_index, row in enumerate(report["per_nut"]):
        patch = row["shaft_surface_patch"]
        fit = row["least_squares_rigid_motion_fit"]
        assert patch["strict_span_node_count"] == expected_patch_sizes[axis_index]
        low, high = row["modeled_nut_role_source"][
            "axial_projection_from_underhead_datum_mm"
        ]
        assert all(
            low < item["axial_station_from_underhead_datum_mm"] < high
            for item in patch["selected_nodes"]
        )
        assert patch["endcap_extrapolation_used"] is False
        assert fit["scaled_design_rank"] == fit["coefficient_matrix_rank"] == 6
        assert fit["scaled_design_condition_estimate_inf_norm"] < 100.0
        assert fit["affine_rigid_reproduction_max_abs_error"] < 1e-10
        assert fit["load_adjoint_wrench_audit"]["passed"] is True
        assert (
            row["original_solid_nut_mesh"]["included_in_real_metal_compliance_or_mass"]
            is False
        )
        assert (
            row["original_solid_nut_mesh"]["included_in_coupling_node_support"] is False
        )
        assert row["original_solid_nut_mesh"]["element_elset_name"]
        assert row["original_solid_nut_mesh"]["node_set_name_available"] is False
        for equation in (
            item
            for item in report["equation_cards"]
            if item["physical_bolt_id"] == row["physical_bolt_id"]
        ):
            dependent = (equation["dependent_node_id"], equation["dependent_dof"])
            assert dependent not in dependents
            dependents.add(dependent)
            assert equation["term_count"] > 1

    include_lines = (
        (output / "nut-coupling.inp").read_text(encoding="utf-8").splitlines()
    )
    parsed_equations = []
    line_index = 0
    while line_index < len(include_lines):
        if include_lines[line_index].upper() != "*EQUATION":
            line_index += 1
            continue
        term_count = int(include_lines[line_index + 1])
        terms = []
        line_index += 2
        while len(terms) < term_count:
            cells = include_lines[line_index].split(",")
            assert len(cells) % 3 == 0
            # Native CCX reads coefficient fields as f20.0, not arbitrary
            # Python floats. Preserve the full exponent inside that width.
            assert all(
                len(cells[offset + 2]) <= 20 for offset in range(0, len(cells), 3)
            )
            terms.extend(
                (
                    int(cells[offset]),
                    int(cells[offset + 1]),
                    float(cells[offset + 2]),
                )
                for offset in range(0, len(cells), 3)
            )
            line_index += 1
        assert len(terms) == term_count
        parsed_equations.append(terms)
    assert len(parsed_equations) == 24
    for equation, summary in zip(
        parsed_equations, report["equation_cards"], strict=True
    ):
        assert len(equation) == summary["term_count"]
        assert equation[0][:2] == (
            summary["dependent_node_id"],
            summary["dependent_dof"],
        )
        assert all(dof in (1, 2, 3) for _, dof, _ in equation)

    # Check rigid reproduction after serialization, including the precision
    # actually delivered to the native Fortran reader.
    for nut_index, row in enumerate(report["per_nut"]):
        origin = row["nut_seat_reference"]["global_xyz_mm"]
        positions = {
            item["node_id"]: item["global_xyz_mm"]
            for item in row["shaft_surface_patch"]["selected_nodes"]
        }
        for mode in range(6):
            for component, equation in enumerate(
                parsed_equations[6 * nut_index : 6 * nut_index + 6]
            ):
                residual = float(component == mode)
                for node, dof, coefficient in equation[1:]:
                    x, y, z = [
                        positions[node][axis] - origin[axis] for axis in range(3)
                    ]
                    rigid = (
                        (1, 0, 0, 0, z, -y),
                        (0, 1, 0, -z, 0, x),
                        (0, 0, 1, y, -x, 0),
                    )
                    residual += coefficient * rigid[dof - 1][mode]
                assert abs(residual) < 1e-10

    cards = [line.upper() for line in include_lines if line.startswith("*")]
    assert cards.count("*NODE") == 1
    assert sum(line.startswith("*NSET,NSET=") for line in cards) == 4
    assert cards.count("*EQUATION") == 24
    assert not any(
        line.startswith(
            (
                "*MATERIAL",
                "*SOLID SECTION",
                "*CONTACT",
                "*STEP",
                "*STATIC",
                "*RIGID BODY",
            )
        )
        for line in cards
    )
    index = json.loads((output / "sha256.json").read_text(encoding="utf-8"))
    assert set(index) == {"nut-coupling.inp", "nut-coupling.json"}
    assert report["scope"]["physical_thread_engagement_established"] is False
    assert report["scope"]["native_execution_performed"] is False
