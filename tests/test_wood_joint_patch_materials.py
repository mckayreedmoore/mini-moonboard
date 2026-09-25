"""Lightweight contract tests for the proposal-only timber material scenario."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from fea import wood_joint_patch_materials as materials


def _frame(grain_axis_local_name="X"):
    return {
        "grain_axis_local_name": grain_axis_local_name,
        "grain_axis_global_xyz": {
            "X": (1.0, 0.0, 0.0),
            "T": (0.0, 1.0, 0.0),
            "N": (0.0, 0.0, 1.0),
        }[grain_axis_local_name],
        "local_axes_global_xyz": {
            "X": (1.0, 0.0, 0.0),
            "T": (0.0, 1.0, 0.0),
            "N": (0.0, 0.0, 1.0),
        },
    }


def test_exact_declared_scenario_is_proposal_only_and_reciprocal():
    scenario = materials.material_scenario()

    assert scenario["schema"] == materials.SCHEMA
    assert scenario["scenario_id"] == materials.SCENARIO_ID
    assert scenario["scenario_id"] == "douglas_fir_orthotropic_elastic_diagnostic_2026-09-24"
    assert scenario["status"] == "proposal_only_unmeasured_unaccepted"
    assert scenario["material_basis"] == "Douglas-fir diagnostic elastic scenario"
    assert scenario["source_document"] == materials.SOURCE_DOCUMENT
    assert scenario["source_document_sha256"] == (
        "f6b723ddfc911284958df7a5348162f6d659396bbc03b83a74fcfbb125b3477f"
    )
    source_path = Path(materials.__file__).resolve().parents[1] / scenario["source_document"]
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == scenario[
        "source_document_sha256"
    ]
    assert scenario["solver_input_format_reference"] == {
        "document": "fea/generated/connection/ccx_2.21.pdf",
        "sha256": "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8",
        "version": "2.21",
        "sections": ("7.46 *ELASTIC", "7.102 *ORIENTATION"),
    }
    manual_path = Path(materials.__file__).resolve().parents[1] / scenario[
        "solver_input_format_reference"
    ]["document"]
    if manual_path.is_file():
        assert hashlib.sha256(manual_path.read_bytes()).hexdigest() == scenario[
            "solver_input_format_reference"
        ]["sha256"]
    assert scenario["calculix_engineering_constants"] == (
        11032.0,
        750.176,
        551.6,
        0.292,
        0.449,
        0.390,
        706.048,
        860.496,
        77.224,
    )
    assert scenario["engineering_constant_order"] == (
        "E_L", "E_R", "E_T", "nu_LR", "nu_LT", "nu_RT", "G_LR", "G_LT", "G_RT"
    )
    assert scenario["derived_reciprocal_poisson_ratios"]["nu_RL"] == pytest.approx(0.019856)
    assert scenario["derived_reciprocal_poisson_ratios"]["nu_TL"] == pytest.approx(0.02245)
    assert scenario["derived_reciprocal_poisson_ratios"]["nu_TR"] == pytest.approx(
        0.286764705882353
    )
    assert scenario["stock_properties_measured"] is False
    assert scenario["grade_specific_measured_properties_claim"] is False
    assert scenario["qualified_for_design"] is False
    assert scenario["resistance_claim"] is False
    fingerprint = dict(scenario)
    scenario_sha256 = fingerprint.pop("scenario_sha256")
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == scenario_sha256
    assert scenario_sha256 == "e4d015ecbf515fd94906bd8d232865402c78f6e4d3d82a8bba59adb321139726"
    assert len(scenario_sha256) == 64


def test_compliance_is_symmetric_reciprocal_and_positive_definite():
    audit = materials.validate_engineering_constants(materials.SCENARIO_CONSTANTS_MPA)
    compliance = audit["compliance_matrix_mpa_inv"]

    assert audit["positive_definite"] is True
    assert all(value > 0.0 for value in audit["compliance_cholesky_diagonal"])
    assert all(
        compliance[row][column] == compliance[column][row]
        for row in range(6)
        for column in range(6)
    )
    # Normal compliance uses reciprocal ratios; shear terms follow engineering
    # shear strain, so their diagonal entries are exactly 1/G_ij.
    assert compliance[0][1] == pytest.approx(-0.292 / 11032.0)
    assert compliance[0][2] == pytest.approx(-0.449 / 11032.0)
    assert compliance[1][2] == pytest.approx(-0.390 / 750.176)
    assert compliance[3][3] == pytest.approx(1.0 / 706.048)
    assert compliance[4][4] == pytest.approx(1.0 / 860.496)
    assert compliance[5][5] == pytest.approx(1.0 / 77.224)
    assert audit["compliance_voigt_order"] == ("11", "22", "33", "12", "13", "23")
    assert audit["shear_strain_convention"] == "engineering shear: gamma_ij = 2 * epsilon_ij"


@pytest.mark.parametrize(
    "constants",
    [
        (1.0, 2.0),
        (1.0,) * 8 + (math.inf,),
        (True,) + (1.0,) * 8,
        (0.0, 750.176, 551.6, 0.292, 0.449, 0.390, 706.048, 860.496, 77.224),
        (11032.0, 750.176, 551.6, 10.0, 10.0, 10.0, 706.048, 860.496, 77.224),
    ],
)
def test_invalid_or_nonpositive_definite_elastic_constants_are_rejected(constants):
    with pytest.raises((TypeError, ValueError)):
        materials.validate_engineering_constants(constants)


def test_both_ring_assignments_keep_a_right_handed_frame_and_transform_vectors():
    first, swapped = materials.material_orientation_cases(_frame())

    assert first["scenario_id"] == "ring_R_on_T"
    assert swapped["scenario_id"] == "ring_R_on_N"
    assert first["material_axes_global_xyz"] == {
        "L": (1.0, 0.0, 0.0),
        "R": (0.0, 1.0, 0.0),
        "T": (0.0, 0.0, 1.0),
    }
    assert swapped["material_axes_global_xyz"] == {
        "L": (1.0, 0.0, 0.0),
        "R": (0.0, 0.0, 1.0),
        "T": (0.0, -1.0, 0.0),
    }
    local = materials.to_material_components((2.0, 3.0, 5.0), swapped)
    assert local == pytest.approx((2.0, 5.0, -3.0))
    assert materials.to_global_components(local, swapped) == pytest.approx((2.0, 3.0, 5.0))
    assert first["calculix_orientation_points_global_xyz"] == (
        1.0, 0.0, 0.0, 0.0, 1.0, 0.0
    )


def test_source_frame_requires_explicit_unit_orthogonal_axes_and_matching_grain():
    frame = _frame("T")
    frame["grain_axis_global_xyz"] = (1.0, 0.0, 0.0)
    with pytest.raises(ValueError, match="align with its named local axis"):
        materials.material_orientation_cases(frame)

    frame = _frame()
    frame["local_axes_global_xyz"]["N"] = (0.0, 1.0, 0.0)
    with pytest.raises(ValueError, match="must be orthogonal"):
        materials.member_orientation(frame, radial_axis_local_name="T")


def test_rendered_cards_preserve_and_revalidate_the_written_constants():
    material_card = materials.render_material_card("wood_proposal")
    assert material_card.startswith(
        "*MATERIAL,NAME=WOOD_PROPOSAL\n*ELASTIC,TYPE=ENGINEERING CONSTANTS\n"
    )
    written_values = tuple(
        float(cell)
        for line in material_card.splitlines()[2:]
        for cell in line.split(",")
    )
    materials.validate_engineering_constants(written_values)
    orientation = materials.material_orientation_cases(_frame())[0]
    orientation_card = materials.render_orientation_card("ori_wood", orientation)
    assert orientation_card.startswith("*ORIENTATION,NAME=ORI_WOOD\n")
    assert tuple(float(value) for value in orientation_card.splitlines()[1].split(",")) == (
        1.0, 0.0, 0.0, 0.0, 1.0, 0.0
    )

    with pytest.raises(ValueError, match="card name"):
        materials.render_material_card("wood;*ELASTIC")
