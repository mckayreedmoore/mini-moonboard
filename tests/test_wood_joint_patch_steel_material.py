"""Lightweight contract tests for proposal-only diagnostic steel inputs."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

from fea import wood_joint_patch_steel_material as materials


def test_exact_baseline_identity_sources_and_local_solver_manual():
    scenario = materials.material_scenario()

    assert scenario["schema"] == materials.SCHEMA
    assert scenario["scenario_id"] == "steel_elastic_diagnostic_baseline_2026-09-24"
    assert scenario["status"] == "proposal_only_unmeasured_unaccepted"
    assert scenario["source_document"] == materials.SOURCE_DOCUMENT
    assert scenario["source_document_sha256"] == (
        "e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3"
    )
    source_path = Path(materials.__file__).resolve().parents[1] / materials.SOURCE_DOCUMENT
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
        materials.SOURCE_DOCUMENT_SHA256
    )
    assert scenario["source_references"] == materials.SOURCE_REFERENCES
    assert scenario["source_references"][0]["sha256"] == (
        "c31583aaa194f454c50d822db417e9493fd39edf804de10e5d6eecc143c62f36"
    )
    assert scenario["solver_input_format_reference"] == {
        "document": "fea/generated/connection/ccx_2.21.pdf",
        "sha256": "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8",
        "version": "2.21",
        "section": "7.46 *ELASTIC",
    }
    manual_path = Path(materials.__file__).resolve().parents[1] / (
        scenario["solver_input_format_reference"]["document"]
    )
    assert hashlib.sha256(manual_path.read_bytes()).hexdigest() == (
        scenario["solver_input_format_reference"]["sha256"]
    )

    assert scenario["youngs_modulus_mpa"] == 200000.0
    assert scenario["poisson_ratio"] == 0.30
    assert scenario["derived_shear_modulus_mpa"] == pytest.approx(76923.07692307692)
    assert scenario["calculix_elastic_type"] == "ISO"
    assert scenario["calculix_elastic_data_order"] == (
        "youngs_modulus_mpa",
        "poisson_ratio",
    )
    assert scenario["hardware_scope"]["body_role_counts"] == {
        "continuous_bolt": 8,
        "washer": 16,
        "nut": 8,
    }
    assert scenario["hardware_scope"]["body_count_per_profile"] == 32
    assert scenario["delivered_material_properties_verified"] is False
    assert scenario["steel_grade_assigned"] is False
    assert scenario["plasticity_defined"] is False
    assert scenario["strength_or_resistance_claim"] is False
    assert scenario["qualified_for_design"] is False

    fingerprint = dict(scenario)
    scenario_sha256 = fingerprint.pop("scenario_sha256")
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert hashlib.sha256(canonical.encode("utf-8")).hexdigest() == scenario_sha256
    assert scenario_sha256 == "596a2abf25d9bd211f3e2697716e74ac4fd8928218a108358f4199c77cc4d53a"


def test_sensitivity_cases_are_the_complete_declared_cartesian_grid():
    scenarios = materials.material_scenarios()

    assert len(scenarios) == 9
    assert {
        scenario["youngs_modulus_mpa"] for scenario in scenarios
    } == {180000.0, 200000.0, 220000.0}
    assert {scenario["poisson_ratio"] for scenario in scenarios} == {
        0.25,
        0.30,
        0.35,
    }
    assert len({scenario["scenario_id"] for scenario in scenarios}) == 9
    assert len({scenario["scenario_sha256"] for scenario in scenarios}) == 9
    assert {
        scenario["scenario_id"]: scenario["scenario_sha256"] for scenario in scenarios
    } == {
        "steel_elastic_diagnostic_E180000_nu025_2026-09-24": (
            "a49a64194a80eba30a46bb850cca83e9885d4b1204eeab66bdb9599d70fdc214"
        ),
        "steel_elastic_diagnostic_E180000_nu030_2026-09-24": (
            "45752a0accb2096468c6f71d4e5fdf5135116aeb88e0cd934dadeaae25687fba"
        ),
        "steel_elastic_diagnostic_E180000_nu035_2026-09-24": (
            "c690707e55cc83ebfc8a44979a12f593ac1e5b433510dc801fd7faff398f3e0b"
        ),
        "steel_elastic_diagnostic_E200000_nu025_2026-09-24": (
            "401f48b100a3e867239dcfc71e968ccc43089dbf018070b46accbba6c98b7078"
        ),
        "steel_elastic_diagnostic_baseline_2026-09-24": (
            "596a2abf25d9bd211f3e2697716e74ac4fd8928218a108358f4199c77cc4d53a"
        ),
        "steel_elastic_diagnostic_E200000_nu035_2026-09-24": (
            "109d24faf26ca9c34750c58e2e61d1abc0cd71fb910a8f254181340f83d879dc"
        ),
        "steel_elastic_diagnostic_E220000_nu025_2026-09-24": (
            "b3c9c1d435b74f4f012fb5ec63af14e2f76cfa6e35301100ae000f9883306089"
        ),
        "steel_elastic_diagnostic_E220000_nu030_2026-09-24": (
            "35dc1583293e1d53601198c189d159d799b981734109ffe6fd121dbd009d1392"
        ),
        "steel_elastic_diagnostic_E220000_nu035_2026-09-24": (
            "9a8b5d1ddfffabb03a92dd6122f44bc970695c989cfba02f0b8b09123ced10d7"
        ),
    }
    assert all(
        scenario["derived_shear_modulus_mpa"]
        == pytest.approx(
            scenario["youngs_modulus_mpa"]
            / (2.0 * (1.0 + scenario["poisson_ratio"]))
        )
        for scenario in scenarios
    )
    assert materials.SENSITIVITY_POLICY["method"] == "full_cartesian_grid"
    assert materials.SENSITIVITY_POLICY["relative_youngs_modulus_perturbation"] == 0.10
    assert materials.SENSITIVITY_POLICY["absolute_poisson_ratio_perturbation"] == 0.05
    assert "not statistical intervals" in materials.SENSITIVITY_POLICY["interpretation"]
    assert all(
        scenario["sensitivity_policy"] == materials.SENSITIVITY_POLICY
        for scenario in scenarios
    )


@pytest.mark.parametrize(
    ("youngs_modulus_mpa", "poisson_ratio", "expected"),
    [
        (200000.0, 0.30, 76923.07692307692),
        (180000.0, 0.25, 72000.0),
        (220000.0, 0.35, 81481.48148148148),
    ],
)
def test_isotropic_shear_modulus_is_derived_from_valid_stable_constants(
    youngs_modulus_mpa, poisson_ratio, expected
):
    assert materials.shear_modulus_mpa(youngs_modulus_mpa, poisson_ratio) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    ("youngs_modulus_mpa", "poisson_ratio"),
    [
        (0.0, 0.30),
        (-1.0, 0.30),
        (math.inf, 0.30),
        (True, 0.30),
        (200000.0, math.nan),
        (200000.0, -1.0),
        (200000.0, 0.5),
        (200000.0, True),
    ],
)
def test_unstable_or_nonfinite_isotropic_constants_are_rejected(
    youngs_modulus_mpa, poisson_ratio
):
    with pytest.raises((TypeError, ValueError)):
        materials.shear_modulus_mpa(youngs_modulus_mpa, poisson_ratio)


def test_material_card_emits_and_revalidates_exact_isotropic_values():
    scenario = materials.material_scenario()
    card = materials.render_material_card("steel_diagnostic", scenario)

    assert card == (
        "*MATERIAL,NAME=STEEL_DIAGNOSTIC\n"
        "*ELASTIC,TYPE=ISO\n"
        "200000,0.3\n"
    )
    written_youngs, written_poisson = map(float, card.splitlines()[2].split(","))
    assert written_youngs == scenario["youngs_modulus_mpa"]
    assert written_poisson == scenario["poisson_ratio"]
    assert materials.shear_modulus_mpa(written_youngs, written_poisson) == pytest.approx(
        scenario["derived_shear_modulus_mpa"]
    )


def test_material_card_rejects_unbound_values_hashes_and_names():
    scenario = materials.material_scenario()
    changed = dict(scenario)
    changed["youngs_modulus_mpa"] = 210000.0
    with pytest.raises(ValueError, match="scenario_sha256"):
        materials.render_material_card("STEEL", changed)

    fingerprint = dict(changed)
    fingerprint.pop("scenario_sha256")
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), allow_nan=False)
    changed["scenario_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    with pytest.raises(ValueError, match="exact declared"):
        materials.validate_material_scenario(changed)
    with pytest.raises(ValueError, match="material name"):
        materials.render_material_card("steel;*PLASTIC", scenario)
