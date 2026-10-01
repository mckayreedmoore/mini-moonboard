#!/usr/bin/env python3
"""Build a source-pinned conditional steel-elastic role map for current WJ24.

The producer joins the frozen current mass/topology rows to the current full-
frame manifest and the already-declared generic steel elastic scenario. It
does not select delivered hardware, assign solver bodies/elements, build a
deck, rebuild CAD, or run a solver.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "steel-elastic-role-map.json"

TOPOLOGY_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-topology-map-attempt03/source-topology-map.json"
)
MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt03/current-full-frame-input-manifest.json"
)
MATERIAL_SCENARIOS_PATH = "docs/wood-joints-mvp/current-material-scenarios.md"
STEEL_SCENARIO_PATH = "docs/wood-joints-mvp/steel-elastic-material-scenario.md"
STEEL_HELPER_PATH = "fea/wood_joint_patch_steel_material.py"
CALCULIX_MANUAL_PATH = "fea/generated/connection/ccx_2.21.pdf"
TOPOLOGY_PRODUCER_PATH = "scripts/wood_joint_current_mass_topology_map.py"
MANIFEST_PRODUCER_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt03/produce.py"
)

EXPECTED_SHA256 = {
    TOPOLOGY_PATH: "308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4",
    MANIFEST_PATH: "2f5eed3e4fa01e62e776d8fc0e4fae12182f86e1d84c63c956dbe7b44fbb5896",
    MATERIAL_SCENARIOS_PATH: "dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4",
    STEEL_SCENARIO_PATH: "e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3",
    STEEL_HELPER_PATH: "0cf45f5194231f61500df14ed580adb9742f6b0c7df659382ea658c7598e8d02",
    CALCULIX_MANUAL_PATH: "16b6bab5a3f1a40a21fff62379f95c804a58d93758ab2e9a489b18d911dc20c8",
    TOPOLOGY_PRODUCER_PATH: "16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9",
    MANIFEST_PRODUCER_PATH: "1d9f1417b33d6d6ef2626c6f1b3957579361c960f59f963e3b8157df5fbf35f2",
}

CANDIDATE_ROLES = ("head", "head_washer", "nut", "nut_washer", "shaft")
RETAINED_ROLES = CANDIDATE_ROLES
BASELINE_SCENARIO_ID = "steel_elastic_diagnostic_baseline_2026-09-24"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"pinned source is missing: {relative_path}")
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path}: expected a JSON object")
    return value


def load_steel_helper() -> Any:
    module_path = ROOT / STEEL_HELPER_PATH
    spec = importlib.util.spec_from_file_location("pinned_steel_scenario_helper", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load pinned steel scenario helper: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def require_close(actual: Any, expected: float, context: str, *, atol: float = 1e-10) -> None:
    if isinstance(actual, bool) or not isinstance(actual, (int, float)):
        raise TypeError(f"{context}: expected a numeric value")
    if not math.isfinite(float(actual)) or not math.isclose(
        float(actual), expected, rel_tol=0.0, abs_tol=atol
    ):
        raise ValueError(f"{context}: expected {expected}, got {actual}")


def _scenario_family(helper: Any) -> dict[str, Any]:
    scenarios = list(helper.material_scenarios())
    if len(scenarios) != 9:
        raise ValueError(f"steel helper must declare nine cases; got {len(scenarios)}")
    for scenario in scenarios:
        helper.validate_material_scenario(scenario)
    by_id = {scenario["scenario_id"]: scenario for scenario in scenarios}
    if len(by_id) != 9 or BASELINE_SCENARIO_ID not in by_id:
        raise ValueError("steel scenario IDs are duplicated or lack the declared baseline")

    baseline = by_id[BASELINE_SCENARIO_ID]
    require_close(baseline["youngs_modulus_mpa"], 200000.0, "baseline E")
    require_close(baseline["poisson_ratio"], 0.30, "baseline nu")
    require_close(baseline["derived_shear_modulus_mpa"], 76923.07692307692, "baseline G", atol=1e-8)

    grid = {
        (float(item["youngs_modulus_mpa"]), float(item["poisson_ratio"]))
        for item in scenarios
    }
    expected_grid = {
        (youngs, poisson)
        for youngs in (180000.0, 200000.0, 220000.0)
        for poisson in (0.25, 0.30, 0.35)
    }
    if grid != expected_grid:
        raise ValueError("steel helper sensitivity scenarios differ from the declared 3x3 grid")

    scenario_rows = []
    for item in sorted(
        scenarios,
        key=lambda record: (record["youngs_modulus_mpa"], record["poisson_ratio"]),
    ):
        scenario_rows.append(
            {
                "scenario_id": item["scenario_id"],
                "scenario_sha256": item["scenario_sha256"],
                "role": "reference" if item["scenario_id"] == BASELINE_SCENARIO_ID else "sensitivity",
                "youngs_modulus_mpa": item["youngs_modulus_mpa"],
                "poisson_ratio": item["poisson_ratio"],
                "derived_shear_modulus_mpa": item["derived_shear_modulus_mpa"],
                "calculix_elastic_type": item["calculix_elastic_type"],
            }
        )

    return {
        "scenario_family_id": "steel_elastic_diagnostic_family_2026-09-24",
        "status": "conditional_generic_elastic_scenario_only",
        "units": {"elastic_moduli": "MPa", "poisson_ratio": "dimensionless"},
        "reference_scenario_id": BASELINE_SCENARIO_ID,
        "scenarios": scenario_rows,
        "sensitivity_policy": json.loads(
            json.dumps(helper.SENSITIVITY_POLICY, allow_nan=False)
        ),
        "application_policy": (
            "For a future diagnostic comparison, one scenario from this family is applied "
            "uniformly to the 460 candidate component roles. The role map does not select "
            "a solver run or assert per-role physical material variation."
        ),
        "basis_and_limits": (
            "The existing generic E/nu proposal is reused only as a conditional elastic "
            "input family. It does not identify delivered alloy, grade, heat treatment, "
            "yield strength, plastic response, preload, or resistance. The old 32-body "
            "WJ04 hardware scope is not inherited."
        ),
        "solver_card_or_body_assignment_emitted": False,
    }


def _mass_role_rows(topology: dict[str, Any], kind: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in topology["physical_mass_rows"]:
        entity = row["source_mass_entity"]
        if entity.get("kind") != kind:
            continue
        name = row.get("inventory_name")
        if not isinstance(name, str) or name in rows:
            raise ValueError(f"duplicate or malformed mass inventory role: {name}")
        rows[name] = row
    return rows


def _source_mass_summary(row: dict[str, Any]) -> dict[str, Any]:
    entity = row["source_mass_entity"]
    return {
        "source_mass_entity_id": entity["id"],
        "source_mass_entity_kind": entity["kind"],
        "source_geometry_kind": entity["source_geometry_kind"],
        "source_shape_map": row["source_shape_map"],
        "mass_kg": row["mass_kg"],
        "mass_center_global_xyz_mm": row["mass_center_global_xyz_mm"],
        "graph_receiver_member_ids": entity["current_graph_member_references"],
        "solver_dof_id": entity["solver_dof_id"],
        "solver_dof_mapping_status": entity["solver_dof_mapping_status"],
    }


def _candidate_axis_geometry(axis: dict[str, Any]) -> dict[str, Any]:
    geometry = axis.get("geometry")
    if not isinstance(geometry, dict):
        raise ValueError(f"{axis.get('axis_id')}: missing candidate axis geometry record")
    required = (
        "modeled_shaft_diameter_mm",
        "modeled_shaft_occupied_length_mm",
        "modeled_underhead_to_tip_mm",
        "shaft_center_global_xyz_mm",
        "wood_grip_material_length_mm",
    )
    if any(key not in geometry for key in required):
        raise ValueError(f"{axis.get('axis_id')}: incomplete modeled geometry record")
    return {key: geometry[key] for key in required}


def build_record() -> dict[str, Any]:
    for path, expected in EXPECTED_SHA256.items():
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"source hash changed for {path}: expected {expected}, got {actual}")

    topology = read_json(TOPOLOGY_PATH)
    manifest = read_json(MANIFEST_PATH)
    helper = load_steel_helper()
    scenario_family = _scenario_family(helper)

    if topology.get("status") != "GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP":
        raise ValueError("unexpected source topology status")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt03":
        raise ValueError("unexpected current full-frame manifest identity")
    if manifest.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("unexpected development candidate")
    if manifest.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise ValueError("unexpected reviewed geometry revision")

    candidate_axes = manifest.get("candidate_bolt_axes")
    retained_axes = manifest.get("retained_frame_bolt_axes")
    if not isinstance(candidate_axes, list) or len(candidate_axes) != 92:
        raise ValueError("current manifest must contain exactly 92 candidate bolt axes")
    if not isinstance(retained_axes, list) or len(retained_axes) != 12:
        raise ValueError("current manifest must contain exactly 12 retained frame-bolt axes")

    candidate_mass_rows = _mass_role_rows(topology, "current_candidate_hardware_component")
    retained_mass_rows = _mass_role_rows(topology, "current_retained_frame_hardware_component")
    if len(candidate_mass_rows) != 460 or len(retained_mass_rows) != 60:
        raise ValueError(
            "topology role counts changed: expected 460 candidate and 60 retained rows"
        )
    topology_rows = topology.get("physical_mass_rows", [])
    if (
        len(topology_rows) != 778
        or topology.get("mass_inventory_row_count") != 778
        or topology.get("unique_source_mass_entity_count") != 778
    ):
        raise ValueError("source topology inventory must retain all 778 mass rows")
    entity_counts = topology.get("source_mass_entity_counts", {})
    if (
        entity_counts.get("current_candidate_hardware_component") != 460
        or entity_counts.get("current_retained_frame_hardware_component") != 60
    ):
        raise ValueError("source topology candidate/retained role counts differ from 460/60")
    if any(row["source_mass_entity"].get("solver_dof_id") is not None for row in topology_rows):
        raise ValueError("source topology unexpectedly contains an implemented solver DOF")
    source_entity_ids = [row["source_mass_entity"]["id"] for row in topology_rows]
    if len(source_entity_ids) != len(set(source_entity_ids)):
        raise ValueError("source topology entity IDs are not unique")

    candidate_axes_by_id = {axis["axis_id"]: axis for axis in candidate_axes}
    retained_axes_by_id = {axis["axis_id"]: axis for axis in retained_axes}
    if len(candidate_axes_by_id) != 92 or len(retained_axes_by_id) != 12:
        raise ValueError("duplicate current candidate or retained axis ID")

    candidate_roles_by_axis: dict[str, dict[str, dict[str, Any]]] = {}
    for name, row in candidate_mass_rows.items():
        entity = row["source_mass_entity"]
        axis_id = entity.get("axis_id")
        role = entity.get("component_role")
        if not isinstance(axis_id, str) or role not in CANDIDATE_ROLES:
            raise ValueError(f"malformed candidate component identity: {name}")
        if row.get("group") != "block bolts nuts washers":
            raise ValueError(f"unexpected candidate role inventory group: {name}")
        if row.get("source_shape_map") != "candidate_installed_hardware":
            raise ValueError(f"unexpected candidate source shape map: {name}")
        if name != f"{axis_id}/{role}" or entity.get("id") != f"candidate_installed_hardware/{name}":
            raise ValueError(f"candidate inventory/entity identity mismatch: {name}")
        if role in candidate_roles_by_axis.setdefault(axis_id, {}):
            raise ValueError(f"duplicate candidate component role: {axis_id}/{role}")
        candidate_roles_by_axis[axis_id][role] = row

    if set(candidate_roles_by_axis) != set(candidate_axes_by_id):
        raise ValueError("candidate axis IDs differ between mass topology and geometry manifest")

    baseline_id = scenario_family["reference_scenario_id"]
    scenario_ids = [item["scenario_id"] for item in scenario_family["scenarios"]]
    candidate_component_roles: list[dict[str, Any]] = []
    candidate_bolt_identities: list[dict[str, Any]] = []
    for axis_id in sorted(candidate_axes_by_id):
        axis = candidate_axes_by_id[axis_id]
        roles = candidate_roles_by_axis[axis_id]
        if set(roles) != set(CANDIDATE_ROLES):
            raise ValueError(f"candidate axis {axis_id} does not have exactly five component roles")
        if set(axis.get("scene_modeled_component_role_ids", [])) != set(CANDIDATE_ROLES):
            raise ValueError(f"manifest modeled role set differs at {axis_id}")
        receivers = axis.get("receiver_member_ids")
        if not isinstance(receivers, list) or len(receivers) < 2 or len(set(receivers)) != len(receivers):
            raise ValueError(f"candidate axis {axis_id} has malformed recorded receiver membership")

        role_entity_ids = []
        for role in CANDIDATE_ROLES:
            row = roles[role]
            entity = row["source_mass_entity"]
            graph_receivers = entity.get("current_graph_member_references")
            if not isinstance(graph_receivers, list) or set(graph_receivers) != set(receivers):
                raise ValueError(f"mass-topology receiver set differs from manifest at {axis_id}/{role}")
            if entity.get("solver_dof_id") is not None:
                raise ValueError(f"unexpected implemented solver DOF for {axis_id}/{role}")
            role_entity_ids.append(entity["id"])

            bolt_identity = f"candidate_physical_bolt/{axis_id}" if role in {"head", "shaft"} else None
            candidate_component_roles.append(
                {
                    "candidate_stack_identity_key": f"candidate_stack/{axis_id}",
                    "candidate_physical_bolt_identity_key": bolt_identity,
                    "axis_id": axis_id,
                    "component_role": role,
                    "inventory_name": row["inventory_name"],
                    "source_mass": _source_mass_summary(row),
                    "conditional_material_binding": {
                        "scenario_family_id": scenario_family["scenario_family_id"],
                        "reference_scenario_id": baseline_id,
                        "available_scenario_ids": scenario_ids,
                        "scope": "conditional source component-role binding; one scenario applied uniformly per diagnostic comparison",
                        "solver_material_id": None,
                        "solver_body_id": None,
                        "solver_element_assignment": "not_implemented",
                    },
                }
            )

        associations = axis.get("geometric_member_pair_associations", [])
        if any(item.get("physical_head_to_nut_order_established") is not False for item in associations):
            raise ValueError(f"unexpected physical head-to-nut ordering claim at {axis_id}")
        candidate_bolt_identities.append(
            {
                "candidate_physical_bolt_identity_key": f"candidate_physical_bolt/{axis_id}",
                "candidate_stack_identity_key": f"candidate_stack/{axis_id}",
                "axis_id": axis_id,
                "receiver_member_ids_as_recorded": receivers,
                "source_geometric_member_pair_associations": associations,
                "source_modeled_axis_geometry": _candidate_axis_geometry(axis),
                "component_role_entity_ids": role_entity_ids,
                "head_and_shaft_identity_rule": (
                    "The source head and shaft role rows share this candidate bolt identity; "
                    "they remain separate mass/component roles and are not asserted to be one FE body."
                ),
                "geometry_limit": (
                    "Manifest axis and shaft dimensions are candidate modeled geometry, not delivered "
                    "hardware, purchase length, thread engagement, or physical head-to-nut ordering."
                ),
            }
        )

    retained_roles_by_axis: dict[str, dict[str, dict[str, Any]]] = {}
    for name, row in retained_mass_rows.items():
        entity = row["source_mass_entity"]
        axis_id = entity.get("axis_id")
        role = entity.get("component_role")
        if not isinstance(axis_id, str) or role not in RETAINED_ROLES:
            raise ValueError(f"malformed retained component identity: {name}")
        if row.get("source_shape_map") != "protected_retained_frame_components":
            raise ValueError(f"unexpected retained source shape map: {name}")
        if name != f"{axis_id}/{role}" or entity.get("id") != f"retained_frame_hardware/{name}":
            raise ValueError(f"retained inventory/entity identity mismatch: {name}")
        if role in retained_roles_by_axis.setdefault(axis_id, {}):
            raise ValueError(f"duplicate retained component role: {axis_id}/{role}")
        retained_roles_by_axis[axis_id][role] = row

    if set(retained_roles_by_axis) != set(retained_axes_by_id):
        raise ValueError("retained axis IDs differ between mass topology and geometry manifest")

    retained_component_inventory: list[dict[str, Any]] = []
    retained_axis_inventory: list[dict[str, Any]] = []
    for axis_id in sorted(retained_axes_by_id):
        axis = retained_axes_by_id[axis_id]
        roles = retained_roles_by_axis[axis_id]
        if set(roles) != set(RETAINED_ROLES):
            raise ValueError(f"retained axis {axis_id} does not have exactly five role rows")
        receivers = axis.get("members_as_recorded")
        if not isinstance(receivers, list) or len(receivers) != 2 or len(set(receivers)) != 2:
            raise ValueError(f"retained axis {axis_id} does not have two recorded members")

        entity_ids = []
        for role in RETAINED_ROLES:
            row = roles[role]
            entity = row["source_mass_entity"]
            graph_receivers = entity.get("current_graph_member_references")
            if not isinstance(graph_receivers, list) or set(graph_receivers) != set(receivers):
                raise ValueError(f"retained topology receiver set differs at {axis_id}/{role}")
            entity_ids.append(entity["id"])
            retained_component_inventory.append(
                {
                    "axis_id": axis_id,
                    "component_role": role,
                    "inventory_name": row["inventory_name"],
                    "source_mass": _source_mass_summary(row),
                    "material_assignment": None,
                    "assignment_status": "unassigned_by_default_outside_candidate_steel_role_map",
                }
            )
        if axis.get("candidate_recheck_status") != "required":
            raise ValueError(f"retained axis {axis_id} lost its current-candidate recheck status")
        retained_axis_inventory.append(
            {
                "axis_id": axis_id,
                "members_as_recorded": receivers,
                "component_role_entity_ids": entity_ids,
                "candidate_recheck_status": axis["candidate_recheck_status"],
                "source_nominal_length_mm": axis["source_nominal_length_mm"],
                "source_occupied_length_mm": axis["source_occupied_length_mm"],
                "source_occupied_diameter_mm": axis["source_occupied_diameter_mm"],
                "material_assignment": None,
                "assignment_status": "unassigned_by_default_pending_scope_inclusion_and_candidate_recheck",
            }
        )

    input_readiness = manifest.get("readiness", {})
    inventory_counts = manifest.get("inventory_counts", {})
    if input_readiness.get("inputs_ready") is not False:
        raise ValueError("source manifest no longer records full-frame inputs as not ready")
    if input_readiness.get("per_member_material_mapping_ready") is not False:
        raise ValueError("source manifest readiness changed; create a new reviewed attempt")
    if inventory_counts.get("candidate_modeled_hardware_component_roles") != 460:
        raise ValueError("manifest candidate hardware role count is not 460")
    if inventory_counts.get("retained_frame_modeled_hardware_component_roles") != 60:
        raise ValueError("manifest retained hardware role count is not 60")

    record: dict[str, Any] = {
        "schema": "wood_joint_current_steel_elastic_role_map/v1",
        "attempt_id": "current-steel-elastic-role-map-attempt01",
        "status": "conditional_elastic_role_data_binding_only",
        "candidate": manifest["candidate"],
        "geometry_revision_id": manifest["geometry_revision_id"],
        "source_manifest_id": manifest["manifest_id"],
        "source_sha256": EXPECTED_SHA256,
        "producer": {
            "path": (
                "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
                "current-steel-elastic-role-map-attempt01/produce.py"
            ),
            "purpose": "read-only role binding from pinned topology, geometry manifest, and elastic scenario sources",
        },
        "material_scenario_family": scenario_family,
        "candidate_physical_bolt_identities": candidate_bolt_identities,
        "candidate_component_role_assignments": candidate_component_roles,
        "retained_frame_bolt_axes_inventory_only": retained_axis_inventory,
        "retained_frame_component_roles_unassigned": retained_component_inventory,
        "scope_counts": {
            "candidate_physical_bolt_identities": len(candidate_bolt_identities),
            "candidate_axes": len(candidate_axes_by_id),
            "candidate_component_roles": len(candidate_component_roles),
            "candidate_roles_per_axis": 5,
            "retained_frame_axes_in_inventory_only": len(retained_axis_inventory),
            "retained_frame_component_roles_unassigned": len(retained_component_inventory),
            "scenario_family_cases": len(scenario_ids),
        },
        "solver_mapping": {
            "solver_body_ids_assigned": False,
            "solver_dof_mapping_implemented": False,
            "solver_element_material_assignments_written": False,
            "solver_material_cards_emitted": False,
            "source_topology_solver_dof_ids_all_null": True,
        },
        "source_manifest_readiness_unchanged": {
            "inputs_ready": input_readiness["inputs_ready"],
            "per_member_material_mapping_ready": input_readiness["per_member_material_mapping_ready"],
            "full_frame_inputs_ready_after_this_map": False,
        },
        "claim_limits": [
            "The elastic E/nu values are a generic conditional diagnostic scenario, not delivered hardware properties or alloy/grade identification.",
            "The sensitivity grid is analyst-declared numerical perturbation, not a physical bound, tolerance, or statistical interval.",
            "Head and shaft remain separate source mass/component roles with one candidate physical-bolt identity; no fused solver body is defined.",
            "The 60 retained frame-hardware roles are inventoried separately and remain unassigned by default.",
            "No yield strength, plasticity, preload, resistance, connection acceptance, physical receiving, or release is established.",
            "No solver body, element, DOF, material card, CAD rebuild, or native mechanics result is produced.",
        ],
    }
    record["record_sha256"] = sha256_bytes(canonical_json(record).encode("utf-8"))
    return record


def verify() -> dict[str, Any]:
    expected = build_record()
    actual = read_json(OUTPUT.relative_to(ROOT).as_posix())
    actual_digest = actual.pop("record_sha256", None)
    if actual_digest != sha256_bytes(canonical_json(actual).encode("utf-8")):
        raise ValueError("role map canonical record digest mismatch")
    expected_payload = dict(expected)
    expected_digest = expected_payload.pop("record_sha256")
    if actual_digest != expected_digest or actual != expected_payload:
        raise ValueError("role map differs from its pinned source reconstruction")
    return {
        "status": "verified",
        "candidate": expected["candidate"],
        "geometry_revision_id": expected["geometry_revision_id"],
        "candidate_axes": expected["scope_counts"]["candidate_axes"],
        "candidate_component_roles": expected["scope_counts"]["candidate_component_roles"],
        "retained_roles_unassigned": expected["scope_counts"]["retained_frame_component_roles_unassigned"],
        "solver_mapping_implemented": False,
        "record_sha256": expected_digest,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.write:
        record = build_record()
        payload = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
        with OUTPUT.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
        print(
            json.dumps(
                {
                    "status": "written",
                    "path": OUTPUT.relative_to(ROOT).as_posix(),
                    "record_sha256": record["record_sha256"],
                    "candidate_axes": record["scope_counts"]["candidate_axes"],
                    "candidate_component_roles": record["scope_counts"]["candidate_component_roles"],
                },
                sort_keys=True,
            )
        )
    else:
        print(json.dumps(verify(), sort_keys=True))


if __name__ == "__main__":
    main()
