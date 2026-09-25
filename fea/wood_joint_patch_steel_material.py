"""Proposal-only isotropic elastic inputs for WJ04 hardware diagnostics.

These scenario values are a generic linear-elastic reference for sensitivity
work on the response-only hardware bodies. They do not identify the material
or grade of any delivered bolt, washer, or nut.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

SCHEMA = "wood_joint_patch_steel_material_scenario/v1"
SCENARIO_DATE = "2026-09-24"
STATUS = "proposal_only_unmeasured_unaccepted"
SOURCE_DOCUMENT = "docs/wood-joints-mvp/steel-elastic-material-scenario.md"
SOURCE_DOCUMENT_SHA256 = "e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3"
CALCULIX_MANUAL_PATH = "fea/generated/connection/ccx_2.21.pdf"
CALCULIX_MANUAL_SHA256 = "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8"
CALCULIX_MANUAL_VERSION = "2.21"
CALCULIX_MANUAL_SECTION = "7.46 *ELASTIC"

BASELINE_YOUNGS_MODULUS_MPA = 200000.0
BASELINE_POISSON_RATIO = 0.30
YOUNGS_MODULUS_SENSITIVITY_MPA = (180000.0, 200000.0, 220000.0)
POISSON_RATIO_SENSITIVITY = (0.25, 0.30, 0.35)
HARDWARE_BODY_ROLE_COUNTS = {"continuous_bolt": 8, "washer": 16, "nut": 8}

SOURCE_REFERENCES = (
    {
        "title": "Experimental Evaluation of a Procedure for SMF Continuity Plate and Weld Design",
        "authors": "Adel Mashayekh and Chia-Ming Uang",
        "publication": "AISC Engineering Journal, Second Quarter 2018, pp. 109–122",
        "url": "https://ej.aisc.org/index.php/engj/article/download/1127/1126/1126",
        "sha256": "c31583aaa194f454c50d822db417e9493fd39edf804de10e5d6eecc143c62f36",
        "use": "Primary published FE study reporting typical steel model values E=29,000 ksi and nu=0.3.",
    },
    {
        "title": "ANSI/AISC 360-22, Specification for Structural Steel Buildings",
        "authors": "American Institute of Steel Construction",
        "publication": "2022, Table B4.1a",
        "url": "https://www.aisc.org/aisc/publications/current-standards/aisc-360/",
        "sha256": None,
        "use": "Primary standard source for the stated steel elastic modulus E=29,000 ksi (200,000 MPa).",
    },
)

SENSITIVITY_POLICY = {
    "method": "full_cartesian_grid",
    "youngs_modulus_mpa": YOUNGS_MODULUS_SENSITIVITY_MPA,
    "poisson_ratio": POISSON_RATIO_SENSITIVITY,
    "relative_youngs_modulus_perturbation": 0.10,
    "absolute_poisson_ratio_perturbation": 0.05,
    "interpretation": (
        "Analyst-declared numerical perturbations around the elastic reference; "
        "not statistical intervals, material bounds, lot variation, or tolerances."
    ),
}

LIMITATIONS = (
    "Generic isotropic steel elastic diagnostic; no steel grade is assigned.",
    "Values are not measured or verified properties of delivered bolts, washers, or nuts.",
    "The common material card across 32 hardware bodies is a diagnostic simplification only.",
    "No yield stress, plasticity, strength, resistance, or design qualification is supplied.",
    "Body geometry is response-only idealized hardware and is not a delivered-part inspection.",
)


def _finite_positive(value: Any, name: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{name} must be a finite positive number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite positive number") from error
    if not math.isfinite(result) or result <= 0.0:
        raise ValueError(f"{name} must be a finite positive number")
    return result


def shear_modulus_mpa(youngs_modulus_mpa: float, poisson_ratio: float) -> float:
    """Return isotropic G derived from E and nu after checking stability."""

    youngs = _finite_positive(youngs_modulus_mpa, "Young's modulus")
    if isinstance(poisson_ratio, bool):
        raise TypeError("Poisson's ratio must be finite and between -1 and 0.5")
    try:
        poisson = float(poisson_ratio)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Poisson's ratio must be finite and between -1 and 0.5") from error
    if not math.isfinite(poisson) or not -1.0 < poisson < 0.5:
        raise ValueError("Poisson's ratio must be finite and between -1 and 0.5")
    return youngs / (2.0 * (1.0 + poisson))


def _canonical_sha256(record: Mapping[str, Any]) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _scenario_id(youngs_modulus_mpa: float, poisson_ratio: float) -> str:
    if (
        youngs_modulus_mpa == BASELINE_YOUNGS_MODULUS_MPA
        and poisson_ratio == BASELINE_POISSON_RATIO
    ):
        return f"steel_elastic_diagnostic_baseline_{SCENARIO_DATE}"
    e_token = str(int(youngs_modulus_mpa))
    nu_token = f"{round(poisson_ratio * 100):03d}"
    return f"steel_elastic_diagnostic_E{e_token}_nu{nu_token}_{SCENARIO_DATE}"


def _make_scenarios() -> tuple[dict[str, Any], ...]:
    scenarios = []
    for youngs_modulus_mpa in YOUNGS_MODULUS_SENSITIVITY_MPA:
        for poisson_ratio in POISSON_RATIO_SENSITIVITY:
            record = {
                "schema": SCHEMA,
                "scenario_id": _scenario_id(youngs_modulus_mpa, poisson_ratio),
                "status": STATUS,
                "material_basis": "generic isotropic steel elastic reference for diagnostics",
                "source_document": SOURCE_DOCUMENT,
                "source_document_sha256": SOURCE_DOCUMENT_SHA256,
                "source_references": deepcopy(SOURCE_REFERENCES),
                "baseline_reference": {
                    "youngs_modulus_mpa": BASELINE_YOUNGS_MODULUS_MPA,
                    "poisson_ratio": BASELINE_POISSON_RATIO,
                },
                "sensitivity_policy": deepcopy(SENSITIVITY_POLICY),
                "units": {"elastic_moduli": "MPa", "poisson_ratio": "dimensionless"},
                "calculix_elastic_type": "ISO",
                "calculix_elastic_data_order": ("youngs_modulus_mpa", "poisson_ratio"),
                "youngs_modulus_mpa": youngs_modulus_mpa,
                "poisson_ratio": poisson_ratio,
                "derived_shear_modulus_mpa": shear_modulus_mpa(
                    youngs_modulus_mpa, poisson_ratio
                ),
                "hardware_scope": {
                    "body_count_per_profile": sum(HARDWARE_BODY_ROLE_COUNTS.values()),
                    "body_role_counts": deepcopy(HARDWARE_BODY_ROLE_COUNTS),
                    "assignment_scope": (
                        "one common isotropic reference card across the 32 response-only "
                        "hardware bodies in one selected profile"
                    ),
                },
                "solver_input_format_reference": {
                    "document": CALCULIX_MANUAL_PATH,
                    "sha256": CALCULIX_MANUAL_SHA256,
                    "version": CALCULIX_MANUAL_VERSION,
                    "section": CALCULIX_MANUAL_SECTION,
                },
                "delivered_material_properties_verified": False,
                "steel_grade_assigned": False,
                "plasticity_defined": False,
                "strength_or_resistance_claim": False,
                "qualified_for_design": False,
                "limitations": LIMITATIONS,
            }
            record["scenario_sha256"] = _canonical_sha256(record)
            scenarios.append(record)
    return tuple(scenarios)


def material_scenarios() -> tuple[dict[str, Any], ...]:
    """Return the explicit baseline and all declared elastic sensitivity cases."""

    return _make_scenarios()


def material_scenario() -> dict[str, Any]:
    """Return the baseline E=200000 MPa, nu=0.30 diagnostic scenario."""

    return next(
        scenario
        for scenario in material_scenarios()
        if scenario["scenario_id"] == f"steel_elastic_diagnostic_baseline_{SCENARIO_DATE}"
    )


def validate_material_scenario(scenario: Mapping[str, Any]) -> dict[str, Any]:
    """Require an unchanged member of the declared scenario set."""

    if not isinstance(scenario, Mapping):
        raise TypeError("scenario must be a mapping")
    declared = {item["scenario_id"]: item for item in material_scenarios()}
    scenario_id = scenario.get("scenario_id")
    if not isinstance(scenario_id, str) or scenario_id not in declared:
        raise ValueError("scenario_id is not a declared steel diagnostic scenario")
    selected = dict(scenario)
    supplied_sha256 = selected.pop("scenario_sha256", None)
    if not isinstance(supplied_sha256, str) or _canonical_sha256(selected) != supplied_sha256:
        raise ValueError("scenario_sha256 does not match the supplied scenario")
    if dict(scenario) != declared[scenario_id]:
        raise ValueError("scenario differs from the exact declared diagnostic values")
    return declared[scenario_id]


def render_material_card(material_name: str, scenario: Mapping[str, Any]) -> str:
    """Render one source-pinned CalculiX isotropic elastic material card."""

    if not isinstance(material_name, str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_]{0,79}", material_name
    ):
        raise ValueError("material name must start with a letter and contain only letters, digits, or _")
    record = validate_material_scenario(scenario)
    card_name = material_name.upper()
    youngs = record["youngs_modulus_mpa"]
    poisson = record["poisson_ratio"]
    emitted_youngs = float(format(youngs, ".15g"))
    emitted_poisson = float(format(poisson, ".15g"))
    emitted_shear = shear_modulus_mpa(emitted_youngs, emitted_poisson)
    if not math.isclose(
        emitted_shear,
        record["derived_shear_modulus_mpa"],
        rel_tol=1e-14,
        abs_tol=1e-12,
    ):
        raise ValueError("emitted elastic values do not preserve the declared isotropic scenario")
    return (
        f"*MATERIAL,NAME={card_name}\n"
        "*ELASTIC,TYPE=ISO\n"
        f"{format(emitted_youngs, '.15g')},{format(emitted_poisson, '.15g')}\n"
    )
