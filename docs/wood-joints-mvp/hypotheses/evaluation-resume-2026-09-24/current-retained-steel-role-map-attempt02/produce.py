#!/usr/bin/env python3
"""Build a source-pinned conditional elastic option map for retained hardware.

This producer joins the retained bolt axes in full-frame manifest attempt04 to
the 60 retained hardware mass/component rows in the current topology map. It
reuses only the generic elastic E/nu scenario values and sensitivity policy.
The material option is unselected, but all twelve physical retained frame-bolt
connections remain required obligations. No solver bodies/elements/DOFs are
assigned, no cards are emitted, and no CAD or native solver work is performed.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "retained-steel-elastic-role-map.json"

BASE = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
TOPOLOGY_PATH = BASE + "current-mass-topology-map-attempt03/source-topology-map.json"
TOPOLOGY_PRODUCER_PATH = "scripts/wood_joint_current_mass_topology_map.py"
MANIFEST_PATH = BASE + "current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
MANIFEST_README_PATH = BASE + "current-full-frame-input-manifest-attempt04/README.md"
MANIFEST_PRODUCER_PATH = BASE + "current-full-frame-input-manifest-attempt04/produce.py"
FULL_FRAME_PRODUCER_PATH = "scripts/wood_joint_current_full_frame_manifest.py"
MATERIAL_STATUS_PATH = "docs/wood-joints-mvp/current-material-map-status-2026-09-27.md"
MATERIAL_SCENARIOS_PATH = "docs/wood-joints-mvp/current-material-scenarios.md"
STEEL_SCENARIO_PATH = "docs/wood-joints-mvp/steel-elastic-material-scenario.md"
STEEL_HELPER_PATH = "fea/wood_joint_patch_steel_material.py"
CALCULIX_MANUAL_PATH = "fea/generated/connection/ccx_2.21.pdf"

CANDIDATE_MAP_PATH = BASE + "current-steel-elastic-role-map-attempt01/steel-elastic-role-map.json"
CANDIDATE_MAP_README_PATH = BASE + "current-steel-elastic-role-map-attempt01/README.md"
CANDIDATE_MAP_PRODUCER_PATH = BASE + "current-steel-elastic-role-map-attempt01/produce.py"
ATTEMPT01_MAP_PATH = BASE + "current-retained-steel-role-map-attempt01/retained-steel-elastic-role-map.json"
ATTEMPT01_README_PATH = BASE + "current-retained-steel-role-map-attempt01/README.md"
ATTEMPT01_PRODUCER_PATH = BASE + "current-retained-steel-role-map-attempt01/produce.py"

EXPECTED_SHA256 = {
    TOPOLOGY_PATH: "308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4",
    TOPOLOGY_PRODUCER_PATH: "16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9",
    MANIFEST_PATH: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    MANIFEST_README_PATH: "7e60cb16f2100fe9da50ccc2617eaeb3a5fba35dd5461d4cce49319bbd15bf9f",
    MANIFEST_PRODUCER_PATH: "966e4b5918fefe06741ca828a3b4c3f6d353b735a1fc70df6a98a91b4e98b1f4",
    FULL_FRAME_PRODUCER_PATH: "0774aa06a560a72411d6fd80da00bd82e81320c7b9191dc36c75641f9f8c9df6",
    MATERIAL_STATUS_PATH: "0ad2c85c9fdc6f3cd17a46c57639b4e63c6fd0119d565b45121715f1c1831e6f",
    MATERIAL_SCENARIOS_PATH: "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    STEEL_SCENARIO_PATH: "e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3",
    STEEL_HELPER_PATH: "0cf45f5194231f61500df14ed580adb9742f6b0c7df659382ea658c7598e8d02",
    CALCULIX_MANUAL_PATH: "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8",
    CANDIDATE_MAP_PATH: "13ed1afcfbc9343207b9e8eb498f8fb3762ec2cdbe0719963f26037cc77027cc",
    CANDIDATE_MAP_README_PATH: "a4ca6688d6bece7c4653c421ed52f74f681de10985896d5d4454f89314662222",
    CANDIDATE_MAP_PRODUCER_PATH: "b625579bc032e32a1100c39f31e50cfea65f74b2137394d500e8055436ca1b26",
    ATTEMPT01_MAP_PATH: "063a03819a4ac0ec62cb72495270cb72cce3d4689ed1a7d1828c2a97f59afb85",
    ATTEMPT01_README_PATH: "96cdbe586406f09f1a6976440657eb6cdf35a983605f67a3060429176d4a111e",
    ATTEMPT01_PRODUCER_PATH: "3eded0b72c416c0e9ba9cc7b50526cbe7453eae963b3ce229173d018f90b0f5d",
}

ROLES = ("head", "head_washer", "nut", "nut_washer", "shaft")
RETAINED_AXIS_IDS = (
    "lumber_leg_bolt_left_1",
    "lumber_leg_bolt_left_2",
    "lumber_leg_bolt_right_1",
    "lumber_leg_bolt_right_2",
    "rail_front_bolt_left_1",
    "rail_front_bolt_left_2",
    "rail_front_bolt_right_1",
    "rail_front_bolt_right_2",
    "rail_rear_bolt_left_1",
    "rail_rear_bolt_left_2",
    "rail_rear_bolt_right_1",
    "rail_rear_bolt_right_2",
)
BASELINE_ID = "steel_elastic_diagnostic_baseline_2026-09-24"
SCENARIO_FAMILY_ID = "steel_elastic_diagnostic_family_2026-09-24"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"pinned source is missing: {relative_path}")
    return _sha256_bytes(path.read_bytes())


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path}: expected a JSON object")
    return value


def _load_steel_helper() -> Any:
    path = ROOT / STEEL_HELPER_PATH
    spec = importlib.util.spec_from_file_location("retained_steel_scenario_helper", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load pinned steel scenario helper: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _finite_number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{context}: expected a numeric value")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{context}: expected a finite value")
    return number


def _finite_vector(value: Any, length: int, context: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{context}: expected {length} components")
    return [_finite_number(component, context) for component in value]


def _scenario_family(helper: Any, candidate_map: dict[str, Any]) -> dict[str, Any]:
    scenarios = list(helper.material_scenarios())
    if len(scenarios) != 9:
        raise ValueError(f"steel helper must declare nine sensitivity cases; got {len(scenarios)}")
    by_id = {}
    for scenario in scenarios:
        helper.validate_material_scenario(scenario)
        scenario_id = scenario["scenario_id"]
        if scenario_id in by_id:
            raise ValueError(f"duplicate steel scenario ID: {scenario_id}")
        by_id[scenario_id] = scenario
    if BASELINE_ID not in by_id:
        raise ValueError("declared steel scenario family has no reference case")

    expected_pairs = {
        (youngs, poisson)
        for youngs in (180000.0, 200000.0, 220000.0)
        for poisson in (0.25, 0.30, 0.35)
    }
    actual_pairs = {
        (float(row["youngs_modulus_mpa"]), float(row["poisson_ratio"]))
        for row in scenarios
    }
    if actual_pairs != expected_pairs:
        raise ValueError("steel scenario grid differs from the pinned 3 by 3 policy")

    if candidate_map.get("schema") != "wood_joint_current_steel_elastic_role_map/v1":
        raise ValueError("candidate steel role map schema changed")
    if candidate_map.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("candidate steel role map belongs to another candidate")
    if candidate_map.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("candidate steel role map uses another geometry revision")
    if candidate_map.get("scope_counts", {}).get("candidate_axes") != 92 or candidate_map.get("scope_counts", {}).get("candidate_component_roles") != 460:
        raise ValueError("candidate steel role map scope differs from its reviewed 92/460 inventory")

    candidate_family = candidate_map.get("material_scenario_family", {})
    candidate_rows = candidate_family.get("scenarios", [])
    if len(candidate_rows) != 9:
        raise ValueError("candidate map scenario family is not a complete nine-case grid")
    candidate_by_id = {row.get("scenario_id"): row for row in candidate_rows}
    if set(candidate_by_id) != set(by_id):
        raise ValueError("candidate and retained maps do not reference the same nine cases")

    output_rows = []
    for scenario_id in sorted(by_id):
        item = by_id[scenario_id]
        candidate_item = candidate_by_id[scenario_id]
        reduced = {
            "scenario_id": scenario_id,
            "scenario_sha256": item["scenario_sha256"],
            "role": "reference" if scenario_id == BASELINE_ID else "sensitivity",
            "youngs_modulus_mpa": item["youngs_modulus_mpa"],
            "poisson_ratio": item["poisson_ratio"],
            "derived_shear_modulus_mpa": item["derived_shear_modulus_mpa"],
            "calculix_elastic_type": item["calculix_elastic_type"],
        }
        if any(candidate_item.get(key) != reduced[key] for key in reduced):
            raise ValueError(f"candidate map scenario differs from helper at {scenario_id}")
        if item["calculix_elastic_type"] != "ISO":
            raise ValueError(f"unexpected steel elastic type at {scenario_id}")
        expected_g = item["youngs_modulus_mpa"] / (2.0 * (1.0 + item["poisson_ratio"]))
        if not math.isclose(item["derived_shear_modulus_mpa"], expected_g, rel_tol=1e-14, abs_tol=1e-10):
            raise ValueError(f"derived G does not match E/[2(1+nu)] at {scenario_id}")
        output_rows.append(reduced)

    baseline = by_id[BASELINE_ID]
    if baseline["youngs_modulus_mpa"] != 200000.0 or baseline["poisson_ratio"] != 0.30:
        raise ValueError("reference steel elastic values differ from the declared scenario")
    if candidate_family.get("scenario_family_id") != SCENARIO_FAMILY_ID:
        raise ValueError("candidate map uses an unexpected scenario-family identity")

    return {
        "scenario_family_id": SCENARIO_FAMILY_ID,
        "status": "conditional_generic_elastic_option_only",
        "units": {"elastic_moduli": "MPa", "poisson_ratio": "dimensionless"},
        "reference_scenario_id": BASELINE_ID,
        "scenarios": output_rows,
        "sensitivity_policy": json.loads(json.dumps(helper.SENSITIVITY_POLICY, allow_nan=False)),
        "application_policy": (
            "A single scenario from this nine-case family may be applied uniformly to the 60 "
            "retained component roles in a conditional diagnostic before final resistance or "
            "fit rechecks are closed. This does not waive those rechecks or remove any retained "
            "physical connection obligation. A full-frame native run still requires a defined "
            "connection representation, solver mapping, and bolt/nut engagement assumptions. "
            "This map does not select a scenario or solver run."
        ),
        "basis_and_limits": (
            "The generic E/nu values are reused as conditional elastic input options. The older "
            "helper's 32-body WJ04 identity and scope are not inherited. These values do not "
            "identify delivered alloy, grade, heat treatment, yield strength, plastic response, "
            "preload, fit, or resistance."
        ),
        "solver_card_or_body_assignment_emitted": False,
    }


def _rotation_matrix() -> list[list[float]]:
    """Return a fixed proper rotation used to test isotropic material invariance."""
    ax, ay, az = 0.31, -0.47, 0.83
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    rx = [[1.0, 0.0, 0.0], [0.0, cx, -sx], [0.0, sx, cx]]
    ry = [[cy, 0.0, sy], [0.0, 1.0, 0.0], [-sy, 0.0, cy]]
    rz = [[cz, -sz, 0.0], [sz, cz, 0.0], [0.0, 0.0, 1.0]]

    def multiply(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
        return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    return multiply(multiply(rz, ry), rx)


def _rotation_invariance(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    q = _rotation_matrix()
    orthogonality_error = max(
        abs(sum(q[k][i] * q[k][j] for k in range(3)) - (1.0 if i == j else 0.0))
        for i in range(3)
        for j in range(3)
    )
    determinant = (
        q[0][0] * (q[1][1] * q[2][2] - q[1][2] * q[2][1])
        - q[0][1] * (q[1][0] * q[2][2] - q[1][2] * q[2][0])
        + q[0][2] * (q[1][0] * q[2][1] - q[1][1] * q[2][0])
    )
    if orthogonality_error > 1e-14 or abs(determinant - 1.0) > 1e-14:
        raise ValueError("rotation test matrix is not proper orthogonal")

    worst_abs = 0.0
    worst_rel = 0.0
    for scenario in scenarios:
        youngs = float(scenario["youngs_modulus_mpa"])
        nu = float(scenario["poisson_ratio"])
        shear = youngs / (2.0 * (1.0 + nu))
        lame = youngs * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))

        def c(i: int, j: int, k: int, l: int) -> float:
            return (
                (lame if i == j and k == l else 0.0)
                + shear * ((1.0 if i == k and j == l else 0.0) + (1.0 if i == l and j == k else 0.0))
            )

        for i in range(3):
            for j in range(3):
                for k in range(3):
                    for l in range(3):
                        transformed = sum(
                            q[i][a] * q[j][b] * q[k][cc] * q[l][d] * c(a, b, cc, d)
                            for a in range(3)
                            for b in range(3)
                            for cc in range(3)
                            for d in range(3)
                        )
                        error = abs(transformed - c(i, j, k, l))
                        worst_abs = max(worst_abs, error)
                        worst_rel = max(worst_rel, error / max(abs(c(i, j, k, l)), youngs))
    if worst_rel > 2e-14:
        raise ValueError(f"isotropic stiffness failed rotational invariance: {worst_rel}")
    return {
        "purpose": "verify that each conditional isotropic E/nu option is orientation-independent",
        "rotation_matrix_global_to_test_frame": q,
        "proper_rotation_determinant": determinant,
        "orthogonality_max_abs_error": orthogonality_error,
        "scenario_count_checked": len(scenarios),
        "isotropic_tensor_max_abs_error_mpa": worst_abs,
        "isotropic_tensor_max_relative_error": worst_rel,
        "acceptance_tolerance_relative": 2e-14,
        "result": "pass",
    }


def _mass_role_rows(topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    source_ids: set[str] = set()
    for row in topology.get("physical_mass_rows", []):
        entity = row.get("source_mass_entity", {})
        if entity.get("kind") != "current_retained_frame_hardware_component":
            continue
        name = row.get("inventory_name")
        entity_id = entity.get("id")
        if not isinstance(name, str) or name in rows:
            raise ValueError(f"duplicate or malformed retained inventory name: {name}")
        if not isinstance(entity_id, str) or entity_id in source_ids:
            raise ValueError(f"duplicate or malformed retained source entity ID: {entity_id}")
        rows[name] = row
        source_ids.add(entity_id)
    return rows


def _mass_summary(row: dict[str, Any]) -> dict[str, Any]:
    entity = row["source_mass_entity"]
    mass = _finite_number(row.get("mass_kg"), f"{row['inventory_name']} mass")
    if mass <= 0:
        raise ValueError(f"{row['inventory_name']}: source component mass must be positive")
    center = _finite_vector(row.get("mass_center_global_xyz_mm"), 3, f"{row['inventory_name']} mass center")
    return {
        "source_mass_entity_id": entity["id"],
        "source_mass_entity_kind": entity["kind"],
        "source_geometry_kind": entity["source_geometry_kind"],
        "source_shape_map": row["source_shape_map"],
        "mass_kg": mass,
        "mass_center_global_xyz_mm": center,
        "graph_receiver_member_ids": list(entity["current_graph_member_references"]),
        "solver_dof_id": entity.get("solver_dof_id"),
        "solver_dof_mapping_status": entity.get("solver_dof_mapping_status"),
    }


def _assemble(
    manifest: dict[str, Any], topology: dict[str, Any], scenario_family: dict[str, Any]
) -> dict[str, Any]:
    if topology.get("status") != "GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP":
        raise ValueError("unexpected topology status")
    if topology.get("revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("topology revision differs from reviewed current geometry")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt04":
        raise ValueError("unexpected current full-frame manifest identity")
    if manifest.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("unexpected candidate identity")
    revision = manifest.get("geometry_revision_id")
    if revision != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("manifest revision differs from reviewed current geometry")

    axes = manifest.get("retained_frame_bolt_axes")
    if not isinstance(axes, list) or len(axes) != 12:
        raise ValueError("manifest must contain exactly twelve retained frame-bolt axes")
    axes_by_id = {axis.get("axis_id"): axis for axis in axes if isinstance(axis, dict)}
    if len(axes_by_id) != 12 or set(axes_by_id) != set(RETAINED_AXIS_IDS):
        raise ValueError("retained axis IDs are duplicated or differ from the reviewed inventory")

    all_rows = topology.get("physical_mass_rows", [])
    if len(all_rows) != 778 or topology.get("mass_inventory_row_count") != 778:
        raise ValueError("source topology must preserve all 778 mass rows")
    all_entity_ids = [row.get("source_mass_entity", {}).get("id") for row in all_rows]
    if None in all_entity_ids or len(set(all_entity_ids)) != 778:
        raise ValueError("source topology mass entity IDs are missing or duplicated")
    rows = _mass_role_rows(topology)
    if len(rows) != 60 or topology.get("source_mass_entity_counts", {}).get("current_retained_frame_hardware_component") != 60:
        raise ValueError("topology must contain exactly sixty retained component-role rows")

    readiness = manifest.get("readiness", {})
    if readiness.get("inputs_ready") is not False:
        raise ValueError("manifest readiness changed; this source-bound option map needs a new attempt")
    if readiness.get("retained_frame_steel_role_assignments_complete") is not False:
        raise ValueError("retained-role readiness no longer has the expected false state")
    if readiness.get("solver_body_element_dof_material_mapping_complete") is not False:
        raise ValueError("manifest unexpectedly records implemented solver material mapping")

    retained_axes = []
    component_assignments = []
    all_masses: list[float] = []
    max_axis_center_offset = 0.0
    per_axis_mass: dict[str, float] = {}
    scenario_ids = [row["scenario_id"] for row in scenario_family["scenarios"]]
    if len(scenario_ids) != 9 or len(set(scenario_ids)) != 9:
        raise ValueError("conditional steel scenario IDs are incomplete or duplicated")

    for axis_id in RETAINED_AXIS_IDS:
        axis = axes_by_id[axis_id]
        direction = _finite_vector(axis.get("axis_global_xyz"), 3, f"{axis_id} axis")
        origin = _finite_vector(axis.get("origin_global_xyz_mm"), 3, f"{axis_id} origin")
        direction_norm = math.sqrt(sum(component * component for component in direction))
        if not math.isclose(direction_norm, 1.0, rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"{axis_id}: recorded axis direction is not unit length")
        length = _finite_number(axis.get("source_nominal_length_mm"), f"{axis_id} nominal length")
        occupied = _finite_number(axis.get("source_occupied_length_mm"), f"{axis_id} occupied length")
        diameter = _finite_number(axis.get("source_occupied_diameter_mm"), f"{axis_id} occupied diameter")
        grip = _finite_number(axis.get("source_grip_mm"), f"{axis_id} source grip")
        if min(length, occupied, diameter, grip) <= 0.0:
            raise ValueError(f"{axis_id}: modeled source dimensions must be positive")
        members = axis.get("members_as_recorded")
        if not isinstance(members, list) or len(members) != 2 or len(set(members)) != 2:
            raise ValueError(f"{axis_id}: expected two distinct recorded receiver members")
        associations = axis.get("geometric_member_pair_associations")
        if not isinstance(associations, list) or not associations:
            raise ValueError(f"{axis_id}: missing source member-pair association")
        for association in associations:
            if association.get("physical_head_to_nut_order_established") is not False:
                raise ValueError(f"{axis_id}: source does not permit asserting head-to-nut order")
            if set(association.get("member_pair", [])) != set(members):
                raise ValueError(f"{axis_id}: association receiver pair differs from retained axis")
        if axis.get("candidate_recheck_status") != "required":
            raise ValueError(f"{axis_id}: required current-candidate recheck status changed")

        component_ids = []
        role_records = {}
        stack_mass = 0.0
        for role in ROLES:
            inventory_name = f"{axis_id}/{role}"
            row = rows.get(inventory_name)
            if row is None:
                raise ValueError(f"missing retained role row {inventory_name}")
            entity = row.get("source_mass_entity", {})
            expected_entity_id = f"retained_frame_hardware/{inventory_name}"
            if entity.get("id") != expected_entity_id:
                raise ValueError(f"source entity ID mismatch at {inventory_name}")
            if entity.get("kind") != "current_retained_frame_hardware_component":
                raise ValueError(f"source entity kind mismatch at {inventory_name}")
            if entity.get("axis_id") != axis_id or entity.get("component_role") != role:
                raise ValueError(f"axis/role identity mismatch at {inventory_name}")
            if row.get("source_shape_map") != "protected_retained_frame_components":
                raise ValueError(f"unexpected source shape map at {inventory_name}")
            if row.get("group") != "frame bolts nuts washers":
                raise ValueError(f"unexpected source mass group at {inventory_name}")
            if entity.get("solver_dof_id") is not None:
                raise ValueError(f"unexpected solver DOF assignment at {inventory_name}")
            graph_members = entity.get("current_graph_member_references")
            if not isinstance(graph_members, list) or len(set(graph_members)) != 2 or set(graph_members) != set(members):
                raise ValueError(f"receiver membership mismatch at {inventory_name}")

            mass_summary = _mass_summary(row)
            center = mass_summary["mass_center_global_xyz_mm"]
            offset = [center[i] - origin[i] for i in range(3)]
            along = sum(offset[i] * direction[i] for i in range(3))
            perpendicular = math.sqrt(sum((offset[i] - along * direction[i]) ** 2 for i in range(3)))
            max_axis_center_offset = max(max_axis_center_offset, perpendicular)
            if perpendicular > 1e-8:
                raise ValueError(f"{inventory_name}: source mass center is not on its recorded bolt axis")

            component_bolt_id = f"retained_physical_bolt/{axis_id}" if role in {"head", "shaft"} else None
            assignment = {
                "retained_stack_identity_key": f"retained_stack/{axis_id}",
                "retained_physical_bolt_identity_key": component_bolt_id,
                "axis_id": axis_id,
                "component_role": role,
                "inventory_name": inventory_name,
                "source_mass": mass_summary,
                "conditional_material_option": {
                    "scenario_family_id": SCENARIO_FAMILY_ID,
                    "reference_scenario_id": scenario_family["reference_scenario_id"],
                    "available_scenario_ids": scenario_ids,
                    "status": "conditional_material_option_unselected",
                    "material_option_selected_by_default": False,
                    "solver_material_id": None,
                    "solver_body_id": None,
                    "solver_element_assignment": "not_implemented",
                },
            }
            component_assignments.append(assignment)
            role_records[role] = {
                "source_mass_entity_id": entity["id"],
                "source_mass_kg": mass_summary["mass_kg"],
                "component_role": role,
                "retained_physical_bolt_identity_key": component_bolt_id,
            }
            component_ids.append(entity["id"])
            stack_mass += mass_summary["mass_kg"]
            all_masses.append(mass_summary["mass_kg"])

        if set(role_records) != set(ROLES):
            raise ValueError(f"{axis_id}: role inventory is incomplete")
        if role_records["head"]["retained_physical_bolt_identity_key"] != role_records["shaft"]["retained_physical_bolt_identity_key"]:
            raise ValueError(f"{axis_id}: head and shaft do not share one physical bolt identity")
        if any(role_records[role]["retained_physical_bolt_identity_key"] is not None for role in ("head_washer", "nut", "nut_washer")):
            raise ValueError(f"{axis_id}: washer/nut roles incorrectly folded into bolt identity")

        per_axis_mass[axis_id] = stack_mass
        retained_axes.append(
            {
                "retained_stack_identity_key": f"retained_stack/{axis_id}",
                "retained_physical_bolt_identity_key": f"retained_physical_bolt/{axis_id}",
                "axis_id": axis_id,
                "members_as_recorded": members,
                "source_geometric_member_pair_associations": associations,
                "source_axis_geometry": {
                    "axis_global_xyz_as_recorded": direction,
                    "origin_global_xyz_mm": origin,
                    "source_nominal_length_mm": length,
                    "source_occupied_length_mm": occupied,
                    "source_occupied_diameter_mm": diameter,
                    "source_grip_mm": grip,
                    "physical_head_to_nut_order_established": False,
                },
                "component_role_entity_ids": component_ids,
                "component_roles": role_records,
                "source_role_mass_sum_kg": stack_mass,
                "candidate_recheck_status": "required",
                "physical_connection_obligation_status": "required_in_current_frame_analysis",
                "material_option_selected_by_default": False,
                "physical_identity_limit": (
                    "This key groups the source head and shaft mass/component rows as one modeled bolt. "
                    "All five roles remain separate source components; no fused FE body or delivered part is defined."
                ),
            }
        )

    if len(component_assignments) != 60 or len(all_masses) != 60:
        raise ValueError("retained component role assignment count is not exactly sixty")
    if {row["inventory_name"] for row in component_assignments} != set(rows):
        raise ValueError("retained topology rows do not match the emitted 60-role inventory")
    if max_axis_center_offset > 1e-8:
        raise ValueError("source role centroid-to-axis check exceeds tolerance")

    rotation = _rotation_invariance(scenario_family["scenarios"])
    candidate_family = _read_json(CANDIDATE_MAP_PATH)["material_scenario_family"]
    if candidate_family["sensitivity_policy"] != scenario_family["sensitivity_policy"]:
        raise ValueError("retained material option sensitivity policy differs from candidate map")

    manifest_counts = manifest.get("inventory_counts", {})
    if manifest_counts.get("retained_starting_frame_bolt_axes") != 12:
        raise ValueError("manifest retained frame-bolt axis count differs from 12")
    if manifest_counts.get("retained_frame_modeled_hardware_component_roles") != 60:
        raise ValueError("manifest retained hardware role count differs from 60")

    return {
        "schema": "wood_joint_current_retained_steel_elastic_role_map/v2",
        "attempt_id": "current-retained-steel-role-map-attempt02",
        "status": "conditional_elastic_material_option_unselected_physical_obligations_required",
        "candidate": manifest["candidate"],
        "geometry_revision_id": revision,
        "source_manifest_id": manifest["manifest_id"],
        "source_sha256": EXPECTED_SHA256,
        "producer": {
            "path": (
                "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
                "current-retained-steel-role-map-attempt02/produce.py"
            ),
            "purpose": "read-only conditional role binding from pinned retained-axis, mass-topology, and steel-scenario sources",
        },
        "material_scenario_family": scenario_family,
        "retained_physical_bolt_identities": retained_axes,
        "retained_component_role_options": component_assignments,
        "validation": {
            "physical_connection_obligations": {
                "retained_frame_bolt_axes_required": 12,
                "all_retained_axes_remain_required": True,
                "material_option_selected_by_default": False,
                "physical_connection_omission_authorized": False,
            },
            "axis_role_coverage": {
                "expected_retained_axes": 12,
                "observed_retained_axes": len(retained_axes),
                "expected_roles_per_axis": 5,
                "observed_component_role_options": len(component_assignments),
                "exact_retained_axis_id_set_match": True,
                "unique_source_mass_entity_ids": 60,
            },
            "physical_bolt_identity": {
                "retained_physical_bolt_count": 12,
                "head_and_shaft_share_one_identity_per_axis": True,
                "washer_and_nut_roles_are_separate": True,
                "source_component_mass_rows_accounted_once": True,
            },
            "source_axis_geometry": {
                "all_axis_directions_unit_length": True,
                "max_role_mass_center_perpendicular_offset_mm": max_axis_center_offset,
                "centerline_tolerance_mm": 1e-8,
                "head_to_nut_order_inferred": False,
            },
            "isotropic_rotation_invariance": rotation,
            "retained_role_mass_accounting": {
                "role_row_count": len(all_masses),
                "source_role_mass_total_kg": sum(all_masses),
                "mass_by_axis_kg": per_axis_mass,
                "interpretation": "Source component masses are inventory values; this map allocates no solver density, body mass, or mass carrier.",
            },
        },
        "solver_mapping": {
            "solver_body_ids_assigned": False,
            "solver_dof_mapping_implemented": False,
            "solver_element_material_assignments_written": False,
            "solver_material_cards_emitted": False,
            "source_topology_solver_dof_ids_all_null": True,
        },
        "source_manifest_readiness_unchanged": {
            "inputs_ready": readiness["inputs_ready"],
            "retained_frame_steel_role_assignments_complete": readiness["retained_frame_steel_role_assignments_complete"],
            "solver_body_element_dof_material_mapping_complete": readiness["solver_body_element_dof_material_mapping_complete"],
            "full_frame_inputs_ready_after_this_map": False,
            "retained_material_option_selected_by_default": False,
            "physical_retained_frame_connection_obligations_remain_required": True,
        },
        "claim_limits": [
            "This binds an unselected generic elastic E/nu material option to source role identities only; it does not exclude or remove any required retained physical connection.",
            "Conditional material scenario studies may proceed before final resistance and fit rechecks. A full-frame native run still requires defined physical connection representation, solver mappings, and bolt/nut engagement assumptions; final criterion closure still requires the outstanding rechecks.",
            "The 12 physical-bolt keys group source head and shaft component rows without merging their source masses or defining one solver body.",
            "Washer and nut roles remain separate component identities and are not grouped into the physical-bolt identity.",
            "The axis/receiver records are modeled source geometry; no delivered product, exact purchase specification, fit, engagement, or receiving is established.",
            "No alloy, grade, heat treatment, yield strength, plasticity, preload, resistance, connection acceptance, or release is established.",
            "No solver body, element, DOF, material card, mass allocation, CAD rebuild, or native mechanics result is produced.",
        ],
    }


def _build_record() -> dict[str, Any]:
    for path, expected in EXPECTED_SHA256.items():
        actual = _sha256_file(path)
        if actual != expected:
            raise ValueError(f"source hash changed for {path}: expected {expected}, got {actual}")
    topology = _read_json(TOPOLOGY_PATH)
    manifest = _read_json(MANIFEST_PATH)
    candidate_map = _read_json(CANDIDATE_MAP_PATH)
    helper = _load_steel_helper()
    family = _scenario_family(helper, candidate_map)
    record = _assemble(manifest, topology, family)
    record["record_sha256"] = _sha256_bytes(_canonical(record).encode("utf-8"))
    return record


def _expect_failure(label: str, manifest: dict[str, Any], topology: dict[str, Any], family: dict[str, Any]) -> str:
    try:
        _assemble(manifest, topology, family)
    except (KeyError, TypeError, ValueError) as error:
        return f"{label}: rejected ({type(error).__name__})"
    raise AssertionError(f"negative control unexpectedly passed: {label}")


def self_test() -> dict[str, Any]:
    record = _build_record()
    manifest = _read_json(MANIFEST_PATH)
    topology = _read_json(TOPOLOGY_PATH)
    family = record["material_scenario_family"]
    controls = []

    bad_topology = copy.deepcopy(topology)
    bad_topology["physical_mass_rows"] = [
        row for row in bad_topology["physical_mass_rows"]
        if row.get("inventory_name") != f"{RETAINED_AXIS_IDS[0]}/shaft"
    ]
    controls.append(_expect_failure("missing retained role", copy.deepcopy(manifest), bad_topology, family))

    bad_manifest = copy.deepcopy(manifest)
    bad_manifest["retained_frame_bolt_axes"].append(copy.deepcopy(bad_manifest["retained_frame_bolt_axes"][0]))
    controls.append(_expect_failure("duplicate retained axis", bad_manifest, copy.deepcopy(topology), family))

    bad_topology = copy.deepcopy(topology)
    for row in bad_topology["physical_mass_rows"]:
        if row.get("inventory_name") == f"{RETAINED_AXIS_IDS[0]}/head":
            row["source_mass_entity"]["current_graph_member_references"] = ["wrong_receiver", "lumber_leg_left"]
            break
    controls.append(_expect_failure("receiver mismatch", copy.deepcopy(manifest), bad_topology, family))

    bad_manifest = copy.deepcopy(manifest)
    bad_manifest["retained_frame_bolt_axes"][0]["axis_global_xyz"] = [0.0, 0.0, 0.0]
    controls.append(_expect_failure("zero axis direction", bad_manifest, copy.deepcopy(topology), family))

    return {
        "status": "PASS_RETAINED_STEEL_ROLE_MAP_ATTEMPT02_SELF_TEST",
        "record_sha256": record["record_sha256"],
        "retained_axes": len(record["retained_physical_bolt_identities"]),
        "retained_role_options": len(record["retained_component_role_options"]),
        "elastic_scenarios": len(record["material_scenario_family"]["scenarios"]),
        "negative_controls": controls,
        "rotation_invariance": record["validation"]["isotropic_rotation_invariance"],
        "solver_mapping_implemented": False,
    }


def verify() -> dict[str, Any]:
    expected = _build_record()
    actual = _read_json(OUTPUT.relative_to(ROOT).as_posix())
    supplied_digest = actual.get("record_sha256")
    actual_payload = dict(actual)
    actual_payload.pop("record_sha256", None)
    if supplied_digest != _sha256_bytes(_canonical(actual_payload).encode("utf-8")):
        raise ValueError("role-map canonical record digest mismatch")
    expected_payload = dict(expected)
    expected_payload.pop("record_sha256")
    if supplied_digest != expected["record_sha256"] or actual_payload != expected_payload:
        raise ValueError("retained role map differs from pinned source reconstruction")
    return {
        "status": "verified",
        "record_sha256": expected["record_sha256"],
        "retained_axes": len(expected["retained_physical_bolt_identities"]),
        "retained_role_options": len(expected["retained_component_role_options"]),
        "elastic_scenarios": len(expected["material_scenario_family"]["scenarios"]),
        "solver_mapping_implemented": False,
        "full_frame_inputs_ready": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.write:
        record = _build_record()
        payload = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        result = {
            "status": "written",
            "path": OUTPUT.relative_to(ROOT).as_posix(),
            "record_sha256": record["record_sha256"],
            "retained_axes": len(record["retained_physical_bolt_identities"]),
            "retained_role_options": len(record["retained_component_role_options"]),
            "elastic_scenarios": len(record["material_scenario_family"]["scenarios"]),
            "solver_mapping_implemented": False,
        }
    elif args.verify:
        result = verify()
    else:
        result = self_test()
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
