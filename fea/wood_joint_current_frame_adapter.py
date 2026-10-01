"""Offline, source-bound audit for the current wood-joint frame inputs.

This module joins the exact current STEP inventory to the attempt03 mass
topology inventory and the six-case load/datum contract. It deliberately does
not create a mesh, material card, solver body, load target, or response model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CANDIDATE = "compact-floor-flush-wood-joints-development"
ATTEMPT_REL = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-adapter-attempt01"
)
MASS_GRAVITY_M_S2 = 9.80665
VECTOR_TOL = 1e-6
SCALAR_TOL = 1e-8


class AdapterError(ValueError):
    """Raised when an input is tampered, ambiguous, or analytically inconsistent."""


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except OSError as exc:
        raise AdapterError(f"cannot read pinned source {path}: {exc}") from exc


def _safe_source_path(root: Path, relative_path: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise AdapterError(
            f"source path escapes repository root: {relative_path}"
        ) from exc
    return candidate


def _load_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_source_path(root, relative_path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AdapterError(f"cannot load JSON source {relative_path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AdapterError(f"expected a JSON object at {relative_path}")
    return value


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AdapterError(message)


def _close(actual: float, expected: float, *, abs_tol: float = SCALAR_TOL) -> bool:
    return math.isclose(float(actual), float(expected), rel_tol=1e-10, abs_tol=abs_tol)


def _same_vector(
    actual: Sequence[float], expected: Sequence[float], *, abs_tol: float = VECTOR_TOL
) -> bool:
    return len(actual) == len(expected) and all(
        _close(a, e, abs_tol=abs_tol) for a, e in zip(actual, expected, strict=True)
    )


def _cross(a: Sequence[float], b: Sequence[float]) -> list[float]:
    return [
        float(a[1]) * float(b[2]) - float(a[2]) * float(b[1]),
        float(a[2]) * float(b[0]) - float(a[0]) * float(b[2]),
        float(a[0]) * float(b[1]) - float(a[1]) * float(b[0]),
    ]


def _add(a: Sequence[float], b: Sequence[float]) -> list[float]:
    return [float(x) + float(y) for x, y in zip(a, b, strict=True)]


def _scale(a: Sequence[float], scalar: float) -> list[float]:
    return [float(x) * scalar for x in a]


def _unique_index(
    records: Iterable[Mapping[str, Any]], key: str, label: str
) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for record in records:
        value = record.get(key)
        _require(isinstance(value, str) and bool(value), f"{label} has a missing {key}")
        _require(value not in index, f"{label} has duplicate {key}: {value}")
        index[value] = record
    return index


def verify_file_pin(root: Path, pin: Mapping[str, Any]) -> str:
    relative_path = pin.get("path")
    expected = pin.get("sha256")
    _require(
        isinstance(relative_path, str),
        "file pin path must be a repository-relative string",
    )
    _require(
        isinstance(expected, str) and len(expected) == 64,
        f"file pin for {relative_path} has no SHA-256",
    )
    actual = _sha256_file(_safe_source_path(root, relative_path))
    _require(
        actual == expected,
        f"source hash mismatch for {relative_path}: expected {expected}, got {actual}",
    )
    return actual


def verify_hash_map(root: Path, expected_by_path: Mapping[str, str]) -> dict[str, str]:
    """Verify a source manifest's path-to-hash map and return observed hashes."""
    observed: dict[str, str] = {}
    for relative_path, expected in sorted(expected_by_path.items()):
        observed[relative_path] = verify_file_pin(
            root, {"path": relative_path, "sha256": expected}
        )
    return observed


def validate_body_id_set(
    body_ids: Iterable[str], expected_body_ids: Iterable[str]
) -> list[str]:
    """Reject duplicate or unknown/missing body identities; preserve sorted IDs."""
    values = list(body_ids)
    _require(
        all(isinstance(item, str) and item for item in values),
        "body identity is empty or invalid",
    )
    duplicates = sorted(item for item, count in Counter(values).items() if count != 1)
    _require(not duplicates, f"duplicate body mapping IDs: {duplicates}")
    observed = set(values)
    expected = set(expected_body_ids)
    _require(
        observed == expected,
        "body mapping identity mismatch: "
        f"unknown={sorted(observed - expected)} missing={sorted(expected - observed)}",
    )
    return sorted(values)


def validate_mass_identity_rows(
    mass_rows: Sequence[Mapping[str, Any]],
    centroid_rows: Sequence[Mapping[str, Any]],
    *,
    expected_kind_counts: Mapping[str, int] | None = None,
) -> dict[str, Mapping[str, Any]]:
    """Require each source mass name and entity role to occur exactly once."""
    mass_by_name = _unique_index(mass_rows, "inventory_name", "mass topology rows")
    centroid_by_name = _unique_index(centroid_rows, "name", "mass centroid rows")
    _require(
        set(mass_by_name) == set(centroid_by_name),
        "mass inventory name mismatch: "
        f"missing_topology={sorted(set(centroid_by_name) - set(mass_by_name))} "
        f"missing_centroid={sorted(set(mass_by_name) - set(centroid_by_name))}",
    )

    entity_ids: list[str] = []
    kind_counts: Counter[str] = Counter()
    for inventory_name, row in mass_by_name.items():
        source_entity = row.get("source_mass_entity")
        _require(
            isinstance(source_entity, dict),
            f"mass row {inventory_name} has no source entity",
        )
        entity_id = source_entity.get("id")
        kind = source_entity.get("kind")
        _require(
            isinstance(entity_id, str) and entity_id,
            f"mass row {inventory_name} has no entity ID",
        )
        _require(
            isinstance(kind, str) and kind,
            f"mass row {inventory_name} has no entity kind",
        )
        entity_ids.append(entity_id)
        kind_counts[kind] += 1

        centroid = centroid_by_name[inventory_name]
        for field in (
            "mass_kg",
            "mass_center_global_xyz_mm",
            "gravity_force_global_xyz_n",
            "gravity_moment_about_global_origin_nmm",
        ):
            _require(
                field in row and field in centroid,
                f"mass row {inventory_name} is missing {field}",
            )
            actual = row[field]
            expected = centroid[field]
            if isinstance(actual, list):
                _require(
                    _same_vector(actual, expected),
                    f"mass row {inventory_name} disagrees with centroid source at {field}",
                )
            else:
                _require(
                    _close(actual, expected),
                    f"mass row {inventory_name} disagrees with centroid source at {field}",
                )
        _require(
            row.get("group") == centroid.get("group"),
            f"mass row {inventory_name} group mismatch",
        )

    duplicates = sorted(
        item for item, count in Counter(entity_ids).items() if count != 1
    )
    _require(not duplicates, f"mass source role is duplicated: {duplicates[:5]}")
    if expected_kind_counts is not None:
        _require(
            dict(kind_counts) == dict(expected_kind_counts),
            f"mass role category count mismatch: observed={dict(kind_counts)} expected={dict(expected_kind_counts)}",
        )
    return mass_by_name


def validate_mass_resultants(
    mass_rows: Sequence[Mapping[str, Any]],
    mass_map: Mapping[str, Any],
    centroids: Mapping[str, Any],
) -> dict[str, Any]:
    """Recompute mass, center, gravity, and origin moment from all source rows."""
    total_mass = 0.0
    weighted_center = [0.0, 0.0, 0.0]
    total_force = [0.0, 0.0, 0.0]
    total_moment = [0.0, 0.0, 0.0]
    for row in mass_rows:
        mass = float(row["mass_kg"])
        center = [float(value) for value in row["mass_center_global_xyz_mm"]]
        force = [float(value) for value in row["gravity_force_global_xyz_n"]]
        moment = [
            float(value) for value in row["gravity_moment_about_global_origin_nmm"]
        ]
        expected_force = [0.0, 0.0, -mass * MASS_GRAVITY_M_S2]
        expected_moment = _cross(center, force)
        _require(
            _same_vector(force, expected_force),
            f"mass row {row['inventory_name']} gravity-force mismatch",
        )
        _require(
            _same_vector(moment, expected_moment),
            f"mass row {row['inventory_name']} origin-moment mismatch",
        )
        total_mass += mass
        weighted_center = _add(weighted_center, _scale(center, mass))
        total_force = _add(total_force, force)
        total_moment = _add(total_moment, moment)

    center = _scale(weighted_center, 1.0 / total_mass)
    _require(
        _close(total_mass, mass_map["modeled_mass_kg"]),
        "mass topology total mass mismatch",
    )
    _require(
        _close(total_mass, centroids["modeled_mass_kg"]),
        "mass centroid total mass mismatch",
    )
    _require(
        _same_vector(center, mass_map["modeled_mass_center_global_xyz_mm"]),
        "mass topology aggregate center mismatch",
    )
    _require(
        _same_vector(center, centroids["modeled_mass_center_global_xyz_mm"]),
        "mass centroid aggregate center mismatch",
    )
    _require(
        _same_vector(total_force, mass_map["gravity_force_global_xyz_n"]),
        "mass topology gravity mismatch",
    )
    _require(
        _same_vector(total_force, centroids["gravity_force_global_xyz_n"]),
        "mass centroid gravity mismatch",
    )
    _require(
        _same_vector(total_moment, mass_map["gravity_moment_about_global_origin_nmm"]),
        "mass topology origin moment mismatch",
    )
    _require(
        _same_vector(total_moment, centroids["gravity_moment_about_global_origin_nmm"]),
        "mass centroid origin moment mismatch",
    )
    return {
        "mass_rows": len(mass_rows),
        "modeled_mass_kg": total_mass,
        "modeled_mass_center_global_xyz_mm": center,
        "gravity_force_global_xyz_n": total_force,
        "gravity_moment_about_global_origin_nmm": total_moment,
        "equipment_allowance_kg_excluded": mass_map["equipment_allowance"]["mass_kg"],
    }


def validate_mass_role_joins(
    mass_rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    body_ids: Iterable[str],
) -> dict[str, int]:
    """Join mass entities to exact member, bolt-axis, screw-axis, and graph IDs."""
    body_set = set(body_ids)
    entity_by_kind: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in mass_rows:
        entity = row["source_mass_entity"]
        entity_by_kind[entity["kind"]].append(row)
        refs = entity.get("current_graph_member_references")
        _require(
            isinstance(refs, list) and refs,
            f"mass role {entity['id']} has no graph-member reference",
        )
        _require(
            set(refs) <= body_set,
            f"mass role {entity['id']} references unknown body IDs {sorted(set(refs) - body_set)}",
        )
        _require(
            entity.get("solver_dof_id") is None,
            f"mass role {entity['id']} has an unsupported solver DOF mapping",
        )

    members = entity_by_kind["current_physical_member_solid"]
    member_ids = [
        row["source_mass_entity"]["id"].removeprefix("physical_member/")
        for row in members
    ]
    validate_body_id_set(member_ids, body_set)
    for row in members:
        entity = row["source_mass_entity"]
        _require(
            entity["id"] == f"physical_member/{row['inventory_name']}",
            "physical-member mass ID/name mismatch",
        )

    candidate_axes = manifest["candidate_bolt_axes"]
    expected_candidate_roles: list[str] = []
    candidate_axis_ids = validate_body_id_set(
        [axis["axis_id"] for axis in candidate_axes],
        [axis["axis_id"] for axis in candidate_axes],
    )
    for axis in candidate_axes:
        roles = axis.get("scene_modeled_component_role_ids")
        _require(
            isinstance(roles, list),
            f"candidate axis {axis['axis_id']} lacks source role IDs",
        )
        _require(
            len(roles) == len(set(roles)),
            f"candidate axis {axis['axis_id']} repeats a component role",
        )
        expected_candidate_roles.extend(
            f"candidate_installed_hardware/{axis['axis_id']}/{role}" for role in roles
        )
    candidate_rows = entity_by_kind["current_candidate_hardware_component"]
    actual_candidate_roles = [row["source_mass_entity"]["id"] for row in candidate_rows]
    validate_body_id_set(actual_candidate_roles, expected_candidate_roles)
    expected_axis_role_pairs = {
        (axis["axis_id"], role)
        for axis in candidate_axes
        for role in axis["scene_modeled_component_role_ids"]
    }
    observed_axis_role_pairs = {
        (
            row["source_mass_entity"].get("axis_id"),
            row["source_mass_entity"].get("component_role"),
        )
        for row in candidate_rows
    }
    _require(
        observed_axis_role_pairs == expected_axis_role_pairs,
        "candidate bolt axis/role fields mismatch their source IDs",
    )
    _require(
        len(candidate_axis_ids) == 92 and len(expected_candidate_roles) == 460,
        "candidate bolt role count mismatch",
    )

    retained_axes = manifest["retained_frame_bolt_axes"]
    retained_axis_index = _unique_index(
        retained_axes, "axis_id", "retained frame-bolt axes"
    )
    retained_rows = entity_by_kind["current_retained_frame_hardware_component"]
    retained_by_axis: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in retained_rows:
        entity = row["source_mass_entity"]
        axis_id = entity.get("axis_id")
        _require(
            axis_id in retained_axis_index,
            f"retained mass role has unknown axis ID: {axis_id}",
        )
        _require(
            entity["id"]
            == f"retained_frame_hardware/{axis_id}/{entity.get('component_role')}",
            f"retained mass role ID/axis mismatch: {entity['id']}",
        )
        retained_by_axis[axis_id].append(row)
    _require(
        set(retained_by_axis) == set(retained_axis_index),
        "retained hardware roles omit a frame-bolt axis",
    )
    for axis_id, axis_rows in retained_by_axis.items():
        role_names = [
            row["source_mass_entity"].get("component_role") for row in axis_rows
        ]
        _require(
            len(axis_rows) == retained_axis_index[axis_id]["modeled_component_count"]
            and len(set(role_names)) == len(role_names),
            f"retained frame-bolt role count/uniqueness mismatch at {axis_id}",
        )

    screw_axes = manifest["panel_kicker_screw_axes"]
    screw_axis_ids = validate_body_id_set(
        [axis["axis_id"] for axis in screw_axes],
        [axis["axis_id"] for axis in screw_axes],
    )
    screw_rows = entity_by_kind["current_panel_screw_axis_envelope_proxy"]
    screw_mass_axes = [row["source_mass_entity"].get("axis_id") for row in screw_rows]
    validate_body_id_set(screw_mass_axes, screw_axis_ids)
    for row in screw_rows:
        entity = row["source_mass_entity"]
        _require(
            entity["id"] == f"panel_screw_axis_envelope/{entity['axis_id']}",
            f"panel-screw mass proxy ID/axis mismatch: {entity['id']}",
        )

    tnuts = entity_by_kind["current_physical_tnut_component"]
    for row in tnuts:
        entity = row["source_mass_entity"]
        _require(
            entity["id"] == f"protected_tnuts/{row['inventory_name']}",
            f"T-nut mass role ID/name mismatch: {entity['id']}",
        )
    return {
        "physical_member_bodies": len(members),
        "candidate_bolt_axes": len(candidate_axes),
        "candidate_hardware_roles": len(candidate_rows),
        "retained_frame_bolt_axes": len(retained_axes),
        "retained_hardware_roles": len(retained_rows),
        "panel_kicker_screw_axes": len(screw_axes),
        "screw_mass_proxy_roles": len(screw_rows),
        "physical_tnut_roles": len(tnuts),
    }


def validate_load_contract(
    load_contract: Mapping[str, Any], datum_contract: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """Check six case identities, explicit datums, force vectors, and wrench moments."""
    _require(
        load_contract.get("candidate") == CANDIDATE, "load contract candidate mismatch"
    )
    _require(
        load_contract.get("geometry_revision_id") == REVISION,
        "load contract revision mismatch",
    )
    _require(
        datum_contract.get("revision_id") == REVISION, "load datum revision mismatch"
    )
    geometry = load_contract["current_geometry_inputs"]
    normal = geometry["panel_outward_normal_global_xyz"]
    datums = datum_contract["holds"]
    _require(
        set(datums) == {"A12", "K12", "A1"}, "current load datum hold IDs mismatch"
    )
    for hold_id, hold in datums.items():
        _require(
            _same_vector(
                geometry["hold_face_datums_global_xyz_mm"][hold_id],
                hold["face_datum_global_mm"],
            ),
            f"load contract and datum record disagree on {hold_id} face datum",
        )
        _require(
            _same_vector(
                geometry["panel_midplane_applicationpoints_global_xyz_mm"][hold_id],
                hold["panel_midplane_reference_global_mm"],
            ),
            f"load contract and datum record disagree on {hold_id} panel reference datum",
        )
        _require(
            _same_vector(hold["outward_normal_global"], normal),
            f"load contract and datum record disagree on {hold_id} outward normal",
        )
    cases = load_contract["cases"]
    case_by_id = _unique_index(cases, "case_id", "current load cases")
    expected_ids = [
        "a12-rear",
        "a12-forward",
        "a12-left",
        "k12-right",
        "k12-rear",
        "a1-rear",
    ]
    _require(set(case_by_id) == set(expected_ids), "six current load case IDs mismatch")
    adapted_cases: list[dict[str, Any]] = []
    for case_id in expected_ids:
        case = case_by_id[case_id]
        hold_id = case.get("hold_id")
        _require(hold_id in datums, f"load case {case_id} has an unknown hold datum")
        hold = datums[hold_id]
        face = hold["face_datum_global_mm"]
        panel_midplane = hold["panel_midplane_reference_global_mm"]
        _require(
            _same_vector(case["panel_patch"]["center_global_xyz_mm"], face),
            f"load case {case_id} patch center does not match its hold-face datum",
        )
        _require(
            _same_vector(
                case["panel_midplane_applicationpoint_global_xyz_mm"], panel_midplane
            ),
            f"load case {case_id} panel reference datum mismatch",
        )
        _require(
            _same_vector(
                case["applied_wrench"]["reference_point_global_xyz_mm"], panel_midplane
            ),
            f"load case {case_id} wrench reference point does not match the panel datum",
        )
        _require(
            _same_vector(case["standoff"]["direction_global_xyz"], normal),
            f"load case {case_id} standoff direction mismatch",
        )
        distance = float(case["standoff"]["distance_mm"])
        app_point = _add(face, _scale(normal, distance))
        _require(
            _same_vector(
                case["standoff"]["force_application_point_global_xyz_mm"], app_point
            ),
            f"load case {case_id} standoff application point mismatch",
        )
        force = case["applied_force_global_xyz_n"]
        horizontal = case["case_inputs"]["horizontal_force_global_xy_n"]
        expected_force = [
            float(horizontal[0]),
            float(horizontal[1]),
            float(load_contract["load_basis"]["vertical_force_global_z_n"]),
        ]
        _require(
            _same_vector(force, expected_force),
            f"load case {case_id} force disagrees with its frozen components",
        )
        _require(
            _close(case["case_inputs"]["pounds"], load_contract["load_basis"]["pounds"])
            and _close(
                case["case_inputs"]["dynamic_factor"],
                load_contract["load_basis"]["dynamic_factor"],
            ),
            f"load case {case_id} scalar basis mismatch",
        )
        _require(
            _close(
                case["panel_patch"]["size_mm"],
                load_contract["load_basis"]["patch_size_mm"],
            ),
            f"load case {case_id} patch size mismatch",
        )
        _require(
            _close(
                case["standoff"]["distance_mm"],
                load_contract["load_basis"]["standoff_mm"],
            ),
            f"load case {case_id} standoff length mismatch",
        )
        _require(
            _same_vector(case["applied_wrench"]["force_global_xyz_n"], force),
            f"load case {case_id} wrench force mismatch",
        )
        moment = _cross(
            [float(app_point[i]) - float(panel_midplane[i]) for i in range(3)], force
        )
        _require(
            _same_vector(
                case["moment_about_panel_midplane_applicationpoint_global_xyz_nmm"],
                moment,
            ),
            f"load case {case_id} moment field does not match its force/datum",
        )
        _require(
            _same_vector(case["applied_wrench"]["moment_global_xyz_nmm"], moment),
            f"load case {case_id} wrench moment/datum mismatch",
        )
        _require(
            _same_vector(
                case["standoff"]["force_application_point_global_xyz_mm"], app_point
            ),
            f"load case {case_id} force point mismatch",
        )
        adapted_cases.append(
            {
                "case_id": case_id,
                "hold_id": hold_id,
                "panel_body_source_id": hold["panel_id"],
                "patch_center_global_xyz_mm": list(face),
                "wrench_reference_global_xyz_mm": list(panel_midplane),
                "applied_force_global_xyz_n": list(force),
                "applied_moment_global_xyz_nmm": list(moment),
                "solver_load_id": None,
                "solver_target_set_id": None,
                "solver_patch_element_ids": None,
            }
        )
    return adapted_cases


def _validate_solver_mappings_null(mass_rows: Sequence[Mapping[str, Any]]) -> None:
    for row in mass_rows:
        entity = row["source_mass_entity"]
        _require(
            entity.get("solver_dof_id") is None,
            f"solver DOF unexpectedly assigned for {entity['id']}",
        )


def _blocker_category(text: str) -> str:
    lower = text.lower()
    if "solver mesh" in lower or "element/node" in lower or "body/element/dof" in lower:
        return "solver_identity_and_material_assignment"
    if (
        "plywood" in lower
        or "layup" in lower
        or "orientation" in lower
        or "properties" in lower
    ):
        return "source_backed_material_properties"
    if "bolt" in lower or "hardware" in lower or "hillman" in lower or "screw" in lower:
        return "hardware_and_attachment_laws"
    if "contact graph" in lower or "mechanical" in lower or "duties" in lower:
        return "connection_mechanics"
    if "gravity" in lower or "mass-to-mesh" in lower:
        return "mass_transfer_to_model"
    if "boundary-condition" in lower or "floor support" in lower:
        return "support_model"
    if "cases are applied" in lower or "reactions" in lower or "stability" in lower:
        return "response_and_demand"
    if "histories" in lower or "time basis" in lower:
        return "ordinary_joint_history"
    return "upstream_manifest_blocker"


def _make_adapter_contract(
    manifest: Mapping[str, Any],
    bundle: Mapping[str, Any],
    mass_map: Mapping[str, Any],
    load_cases: Sequence[Mapping[str, Any]],
    source_hashes: Mapping[str, str],
) -> dict[str, Any]:
    bundle_members = _unique_index(bundle["members"], "member_id", "exact STEP bundle")
    body_bindings = []
    for binding in sorted(
        manifest["finished_member_step_bindings"], key=lambda item: item["member_id"]
    ):
        member_id = binding["member_id"]
        bundle_member = bundle_members[member_id]
        body_bindings.append(
            {
                "source_member_id": member_id,
                "source_member_kind": binding["member_kind"],
                "step_path": binding["path"],
                "step_sha256": binding["file_sha256"],
                "step_size_bytes": binding["size_bytes"],
                "shape_summary_sha256": binding["shape_summary_sha256"],
                "bundle_step_relative_path": bundle_member["step_file"],
                "solver_body_id": None,
                "solver_element_ids": None,
                "solver_node_ids": None,
                "solver_dof_ids": None,
                "solver_material_id": None,
                "material_assignment_status": "unassigned",
            }
        )

    mass_bindings = []
    for row in mass_map["physical_mass_rows"]:
        entity = row["source_mass_entity"]
        mass_bindings.append(
            {
                "source_mass_entity_id": entity["id"],
                "source_mass_entity_kind": entity["kind"],
                "source_inventory_name": row["inventory_name"],
                "solver_body_id": None,
                "solver_element_ids": None,
                "solver_dof_id": None,
                "solver_mass_set_id": None,
                "mass_transfer_status": "not_implemented",
            }
        )
    mass_bindings.sort(key=lambda item: item["source_mass_entity_id"])

    material_assignments = {
        "frame_timber_properties": None,
        "candidate_block_properties": None,
        "plywood_layups_axes_and_properties": None,
        "candidate_hardware_product_and_material_cards": None,
        "retained_frame_hardware_product_and_material_cards": None,
        "hillman_screw_material_and_connection_properties": None,
        "solver_material_ids": None,
    }
    return {
        "schema": "wood_joint_current_frame_adapter_contract/v1",
        "candidate": manifest["candidate"],
        "geometry_revision_id": manifest["geometry_revision_id"],
        "reviewed_repository_commit": manifest["reviewed_repository_commit"],
        "source_manifest_attempt03_sha256": source_hashes["attempt03_manifest"],
        "source_manifest_attempt04_sha256": source_hashes["attempt04_manifest"],
        "exact_step_bundle_descriptor_sha256": source_hashes[
            "member_bundle_descriptor"
        ],
        "body_bindings": body_bindings,
        "mass_bindings": mass_bindings,
        "mass_transfer": {
            "source_map_path": manifest["evidence_bindings"]["source_to_mass_topology"][
                "path"
            ],
            "source_map_sha256": source_hashes["mass_topology_map"],
            "source_inventory_row_count": mass_map["mass_inventory_row_count"],
            "source_entity_count": mass_map["unique_source_mass_entity_count"],
            "mass_values_and_graph_references": "remain in the pinned source map; not copied into this adapter",
            "solver_dof_mapping_implemented": False,
            "solver_dof_id": None,
            "reduced_model_mass_transfer_implemented": False,
            "equipment_allowance_kg_excluded_from_778_rows": mass_map[
                "equipment_allowance"
            ]["mass_kg"],
        },
        "load_cases": list(load_cases),
        "support_mapping": {
            "solver_boundary_condition_ids": None,
            "solver_contact_ids": None,
            "floor_support_assumption": "no-slip analytical assumption; unverified",
        },
        "material_assignments": material_assignments,
        "solver_mappings": {
            "mesh_id": None,
            "body_ids": None,
            "element_ids": None,
            "node_ids": None,
            "dof_ids": None,
            "load_ids": None,
            "boundary_condition_ids": None,
            "contact_ids": None,
        },
        "contract_limit": (
            "Offline identity and analytical consistency adapter only. It does not define a launch-ready "
            "finite-element model, load path, capacity, reaction, connection demand, or acceptance result."
        ),
    }


def audit_current_frame(
    root: Path, pins: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Verify pinned source identity and emit deterministic audit/adapter records."""
    root = root.resolve()
    _require(
        pins.get("schema") == "wood_joint_current_frame_adapter_source_pins/v1",
        "source-pins schema mismatch",
    )
    pin_records = pins.get("pinned_inputs")
    _require(isinstance(pin_records, list), "source-pins pinned_inputs must be a list")
    pins_by_id = _unique_index(pin_records, "id", "source pins")
    required_pin_ids = {
        "attempt03_manifest",
        "attempt04_manifest",
        "attempt03_producer",
        "attempt03_readme",
        "attempt04_producer",
        "attempt04_readme",
        "member_bundle_descriptor",
        "mass_topology_map",
        "mass_centroid_export",
        "load_case_contract",
        "load_datum_contract",
    }
    _require(
        set(pins_by_id) == required_pin_ids,
        "source-pins IDs are incomplete or contain unexpected entries",
    )

    source_hashes: dict[str, str] = {}
    authenticated: dict[str, str] = {}
    for pin_id in sorted(pins_by_id):
        pin = pins_by_id[pin_id]
        actual = verify_file_pin(root, pin)
        source_hashes[pin_id] = actual
        authenticated[pin["path"]] = actual

    paths = {pin_id: pins_by_id[pin_id]["path"] for pin_id in pins_by_id}
    attempt03 = _load_json(root, paths["attempt03_manifest"])
    manifest = _load_json(root, paths["attempt04_manifest"])
    bundle = _load_json(root, paths["member_bundle_descriptor"])
    mass_map = _load_json(root, paths["mass_topology_map"])
    centroids = _load_json(root, paths["mass_centroid_export"])
    load_contract = _load_json(root, paths["load_case_contract"])
    datum_contract = _load_json(root, paths["load_datum_contract"])

    _require(manifest.get("candidate") == CANDIDATE, "attempt04 candidate mismatch")
    _require(
        manifest.get("geometry_revision_id") == REVISION, "attempt04 revision mismatch"
    )
    _require(attempt03.get("candidate") == CANDIDATE, "attempt03 candidate mismatch")
    _require(
        attempt03.get("geometry_revision_id") == REVISION, "attempt03 revision mismatch"
    )
    _require(
        manifest.get("reviewed_repository_commit")
        == attempt03.get("reviewed_repository_commit"),
        "attempt03/04 commit mismatch",
    )

    attempt03_snapshot = manifest["evidence_bindings"][
        "attempt03_preserved_manifest_snapshot"
    ]
    attempt03_pin = attempt03_snapshot["manifest"]
    _require(
        attempt03_pin.get("file_sha256") == source_hashes["attempt03_manifest"],
        "attempt04 does not bind the pinned attempt03 manifest bytes",
    )
    _require(
        attempt03_snapshot["producer_file"].get("file_sha256")
        == source_hashes["attempt03_producer"],
        "attempt04 does not bind the pinned attempt03 producer bytes",
    )
    _require(
        attempt03_snapshot["producer_file"].get("path")
        == pins_by_id["attempt03_producer"]["path"],
        "attempt04 attempt03 producer path mismatch",
    )
    _require(
        attempt03_snapshot["readme_file"].get("file_sha256")
        == source_hashes["attempt03_readme"],
        "attempt04 does not bind the pinned attempt03 README bytes",
    )
    _require(
        attempt03_snapshot["readme_file"].get("path")
        == pins_by_id["attempt03_readme"]["path"],
        "attempt04 attempt03 README path mismatch",
    )
    for attempt_key, manifest_data in (
        ("attempt03", attempt03),
        ("attempt04", manifest),
    ):
        producer_ref = manifest_data.get("producer", {}).get("path")
        producer_sha = manifest_data.get("producer", {}).get("sha256")
        producer_pin = pins_by_id[f"{attempt_key}_producer"]
        _require(
            producer_ref == producer_pin["path"]
            and producer_sha == producer_pin["sha256"],
            f"{attempt_key} producer pin mismatch",
        )
    for attempt_key, manifest_data in (
        ("attempt03", attempt03),
        ("attempt04", manifest),
    ):
        readme_pin = pins_by_id[f"{attempt_key}_readme"]
        _require(
            readme_pin.get("role") == f"{attempt_key} manifest README",
            f"{attempt_key} README pin role mismatch",
        )

    inherited_keys = (
        "finished_member_step_bindings",
        "physical_members",
        "applied_load_cases",
        "inventory_counts",
        "candidate_blocks",
        "candidate_bolt_axes",
        "panel_kicker_screw_axes",
        "retained_frame_bolt_axes",
        "target_duties",
        "release",
    )
    for key in inherited_keys:
        _require(
            manifest.get(key) == attempt03.get(key),
            f"attempt04 changed inherited attempt03 source record {key}",
        )

    geometry_binding = manifest["evidence_bindings"]["finished_member_geometry"]
    _require(
        geometry_binding.get("path") == paths["member_bundle_descriptor"],
        "attempt04 STEP descriptor path mismatch",
    )
    _require(
        geometry_binding.get("file_sha256")
        == source_hashes["member_bundle_descriptor"],
        "attempt04 STEP descriptor hash mismatch",
    )
    _require(
        bundle.get("candidate") == CANDIDATE
        and bundle.get("geometry_revision_id") == REVISION,
        "STEP bundle authority mismatch",
    )
    bindings = manifest["finished_member_step_bindings"]
    bundle_members = bundle["members"]
    binding_by_id = _unique_index(bindings, "member_id", "attempt04 body bindings")
    bundle_by_id = _unique_index(bundle_members, "member_id", "exact STEP bundle")
    _require(
        len(bindings) == 50 and len(bundle_members) == 50,
        "exact STEP member count is not 50",
    )
    body_ids = validate_body_id_set(binding_by_id, bundle_by_id)
    expected_kind_counts = {"timber": 20, "plywood_panel": 6, "candidate_block": 24}
    observed_kind_counts = dict(Counter(binding["member_kind"] for binding in bindings))
    _require(
        observed_kind_counts == expected_kind_counts,
        f"STEP body kind counts mismatch: {observed_kind_counts}",
    )

    for member_id in body_ids:
        binding = binding_by_id[member_id]
        bundle_member = bundle_by_id[member_id]
        _require(
            binding["member_kind"] == bundle_member["member_kind"],
            f"STEP body kind mismatch for {member_id}",
        )
        _require(
            binding["file_sha256"] == bundle_member["step_sha256"],
            f"STEP body source hash mismatch for {member_id}",
        )
        _require(
            binding["size_bytes"] == bundle_member["step_size_bytes"],
            f"STEP body byte count mismatch for {member_id}",
        )
        expected_path = (
            Path(geometry_binding["path"]).parent.parent / bundle_member["step_file"]
        ).as_posix()
        _require(
            binding["path"] == expected_path, f"STEP body path mismatch for {member_id}"
        )
        step_path = _safe_source_path(root, binding["path"])
        _require(
            _sha256_file(step_path) == binding["file_sha256"],
            f"STEP body tampered: {member_id}",
        )
        _require(
            step_path.stat().st_size == binding["size_bytes"],
            f"STEP body size mismatch: {member_id}",
        )
        _require(
            bundle_member.get("step_roundtrip_summary", {}).get("valid") is True,
            f"STEP round-trip is not valid for {member_id}",
        )
        authenticated[binding["path"]] = binding["file_sha256"]

    mass_binding = manifest["evidence_bindings"]["source_to_mass_topology"]
    _require(
        mass_binding.get("path") == paths["mass_topology_map"],
        "attempt04 mass topology path mismatch",
    )
    _require(
        mass_binding.get("file_sha256") == source_hashes["mass_topology_map"],
        "attempt04 mass topology hash mismatch",
    )
    centroid_binding = manifest["evidence_bindings"]["source_mass_centroids"]
    _require(
        centroid_binding.get("path") == paths["mass_centroid_export"],
        "attempt04 mass-centroid path mismatch",
    )
    _require(
        centroid_binding.get("file_sha256") == source_hashes["mass_centroid_export"],
        "attempt04 mass-centroid hash mismatch",
    )
    _require(
        mass_map.get("revision_id") == REVISION
        and centroids.get("revision_id") == REVISION,
        "mass source revision mismatch",
    )
    _require(
        mass_map.get("native_solve_run") is False
        and mass_map.get("mechanical_acceptance") is False,
        "mass topology map carries an out-of-scope acceptance flag",
    )
    _require(
        mass_map.get("cad_rebuilt_or_modified") is False,
        "mass topology map reports CAD changes",
    )
    integration = mass_map.get("global_model_integration", {})
    _require(
        integration.get("solver_dof_mapping_implemented") is False,
        "mass topology map reports an implemented DOF mapping",
    )
    _require(
        integration.get("solver_dof_mapping_count") == 0,
        "mass topology map reports solver DOF records",
    )
    _require(
        integration.get("reduced_model_mass_transfer_implemented") is False,
        "mass topology map reports implemented mass transfer",
    )
    _require(
        integration.get("implemented_mass_carrier_count") == 0,
        "mass topology map reports implemented mass carriers",
    )

    nested_mass_hashes = mass_map.get("source_sha256")
    _require(
        isinstance(nested_mass_hashes, dict), "mass topology source hashes are missing"
    )
    authenticated.update(verify_hash_map(root, nested_mass_hashes))
    nested_load_hashes = {
        path: record["sha256"]
        for path, record in load_contract["source_provenance"]["files"].items()
    }
    authenticated.update(verify_hash_map(root, nested_load_hashes))
    load_datum_source = load_contract["source_provenance"]["current_transform_source"]
    _require(
        load_datum_source["source_path"] == paths["load_datum_contract"],
        "load datum source path mismatch",
    )
    _require(
        load_datum_source["sha256"] == source_hashes["load_datum_contract"],
        "load datum source hash mismatch",
    )
    _require(
        load_contract.get("contract_sha256")
        == manifest["evidence_bindings"]["six_current_applied_load_cases"][
            "content_digest"
        ],
        "load contract content digest binding mismatch",
    )
    _require(
        load_contract.get("contract_sha256")
        == "19fe8aa9b370f2f82758610b8e0231bf0d3972036cf849ef2ffea16e5bf05776",
        "load contract digest differs from attempt04 record",
    )
    applied_loads = manifest["applied_load_cases"]
    _require(
        applied_loads["source_path"] == paths["load_case_contract"],
        "attempt04 load contract path mismatch",
    )
    _require(
        applied_loads["source_file_sha256"] == source_hashes["load_case_contract"],
        "attempt04 load contract hash mismatch",
    )
    _require(
        applied_loads["contract_sha256"] == load_contract["contract_sha256"],
        "attempt04 load content digest mismatch",
    )
    _require(
        applied_loads["basis"] == load_contract["load_basis"],
        "attempt04 and six-case load contract basis mismatch",
    )
    _require(
        applied_loads["current_geometry_input_sha256"]
        == load_contract["current_geometry_input_sha256"],
        "attempt04 and six-case load geometry input hash mismatch",
    )
    manifest_load_cases = _unique_index(
        applied_loads["cases"], "case_id", "attempt04 applied load cases"
    )
    contract_load_cases = _unique_index(
        load_contract["cases"], "case_id", "six-case load contract"
    )
    _require(
        set(manifest_load_cases) == set(contract_load_cases),
        "attempt04 load-case identity set differs from the six-case contract",
    )
    for case_id, contract_case in contract_load_cases.items():
        manifest_case = manifest_load_cases[case_id]
        _require(
            manifest_case["input_type"] == "source_bound_applied_force_and_wrench_only"
            and manifest_case["reactions_or_joint_demands"] is False,
            f"attempt04 load case {case_id} exceeds the applied-wrench-only boundary",
        )
        _require(
            manifest_case["hold_id"] == contract_case["hold_id"]
            and manifest_case["case_inputs"] == contract_case["case_inputs"],
            f"attempt04 load case {case_id} identity/input fields mismatch",
        )
        field_pairs = (
            ("applied_force_global_xyz_n", "applied_force_global_xyz_n"),
            (
                "force_application_point_global_xyz_mm",
                "standoff.force_application_point_global_xyz_mm",
            ),
            (
                "wrench_reference_point_global_xyz_mm",
                "applied_wrench.reference_point_global_xyz_mm",
            ),
            ("moment_global_xyz_nmm", "applied_wrench.moment_global_xyz_nmm"),
            ("patch_center_global_xyz_mm", "panel_patch.center_global_xyz_mm"),
            ("patch_size_mm", "panel_patch.size_mm"),
        )
        for manifest_field, contract_path in field_pairs:
            value: Any = contract_case
            for path_component in contract_path.split("."):
                value = value[path_component]
            if isinstance(value, list):
                _require(
                    _same_vector(manifest_case[manifest_field], value),
                    f"attempt04 load case {case_id} differs from contract at {manifest_field}",
                )
            else:
                _require(
                    _close(manifest_case[manifest_field], value),
                    f"attempt04 load case {case_id} differs from contract at {manifest_field}",
                )

    mass_rows = mass_map["physical_mass_rows"]
    centroids_rows = centroids["rows"]
    kind_counts = mass_map["source_mass_entity_counts"]
    _require(
        mass_map["mass_inventory_row_count"] == 778,
        "mass map inventory row count mismatch",
    )
    _require(
        mass_map["unique_source_mass_entity_count"] == 778,
        "mass map unique source entity count mismatch",
    )
    mass_by_name = validate_mass_identity_rows(
        mass_rows,
        centroids_rows,
        expected_kind_counts=kind_counts,
    )
    _require(
        len(mass_by_name) == 778,
        "source mass inventory does not contain 778 unique roles",
    )
    _require(
        dict(kind_counts)
        == {
            "current_candidate_hardware_component": 460,
            "current_physical_tnut_component": 142,
            "current_panel_screw_axis_envelope_proxy": 66,
            "current_retained_frame_hardware_component": 60,
            "current_physical_member_solid": 50,
        },
        "source mass role-category inventory differs from the frozen 778-row contract",
    )
    role_joins = validate_mass_role_joins(mass_rows, manifest, body_ids)
    mass_resultants = validate_mass_resultants(mass_rows, mass_map, centroids)
    _validate_solver_mappings_null(mass_rows)
    allowance = mass_map["equipment_allowance"]
    _require(
        allowance.get("included_in_mass_rows") is False,
        "25 kg equipment allowance must remain outside the 778 mass rows",
    )
    _require(
        _close(allowance.get("mass_kg"), 25.0),
        "separate equipment allowance mass mismatch",
    )

    adapted_cases = validate_load_contract(load_contract, datum_contract)
    load_ids = [case["case_id"] for case in adapted_cases]
    _require(
        load_ids
        == ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"],
        "adapter load case order mismatch",
    )
    body_kind_by_id = {
        binding["member_id"]: binding["member_kind"] for binding in bindings
    }
    for case in adapted_cases:
        panel_id = case["panel_body_source_id"]
        _require(
            panel_id in body_kind_by_id,
            f"load case {case['case_id']} datum names an unknown panel body",
        )
        _require(
            body_kind_by_id[panel_id] == "plywood_panel",
            f"load case {case['case_id']} datum does not name a plywood panel",
        )

    unresolved = manifest["readiness"].get("unresolved_inputs", [])
    _require(
        isinstance(unresolved, list) and unresolved,
        "attempt04 unresolved input list is empty",
    )
    blockers = [
        {
            "category": _blocker_category(text),
            "source": "current-full-frame-input-manifest-attempt04",
            "detail": text,
        }
        for text in unresolved
    ]
    blocker_categories = [blocker["category"] for blocker in blockers]
    readiness = {
        "inputs_ready": False,
        "launch_ready": False,
        "complete_mechanical_model_ready": False,
        "solver_body_element_dof_material_mapping_ready": False,
        "per_member_material_mapping_ready": False,
        "six_panel_layups_assigned": False,
        "candidate_structural_hardware_ready": False,
        "retained_frame_hardware_assignments_complete": False,
        "complete_mechanical_contact_attachment_model_ready": False,
        "current_full_frame_demands_available": False,
        "criterion_resolved": False,
        "all_47_criteria_resolved": False,
        "candidate_accepted": False,
        "engineering_mvp_complete": False,
        "structural_released": False,
        "fabrication_released": False,
        "drilling_released": False,
        "climbing_released": False,
        "blocker_count": len(blockers),
        "blocker_categories": sorted(set(blocker_categories)),
        "blockers": blockers,
    }
    contract = _make_adapter_contract(
        manifest, bundle, mass_map, adapted_cases, source_hashes
    )
    audit = {
        "schema": "wood_joint_current_frame_adapter_audit/v1",
        "candidate": CANDIDATE,
        "geometry_revision_id": REVISION,
        "adapter_scope": "offline source-bound identity and analytical consistency audit",
        "result": "source_audit_passed_readiness_blocked",
        "source_authentication": {
            "status": "PASS",
            "authenticated_file_count": len(authenticated),
            "sha256_by_path": dict(sorted(authenticated.items())),
        },
        "checks": {
            "attempt03_attempt04_lineage": "PASS",
            "exact_step_body_identity_and_bytes": "PASS",
            "body_to_mass_topology_identity": "PASS",
            "mass_entity_role_counts_and_unique_joins": "PASS",
            "mass_centroid_and_resultant_reconstruction": "PASS",
            "six_case_load_and_datum_wrench_consistency": "PASS",
            "solver_mapping_evidence_boundary": "NULL_AND_UNASSIGNED",
        },
        "verified_counts": {
            "step_bodies": len(body_ids),
            "step_kind_counts": observed_kind_counts,
            "mass_inventory_rows": len(mass_rows),
            "unique_mass_entities": len(mass_map["physical_mass_rows"]),
            "mass_source_kind_counts": dict(sorted(kind_counts.items())),
            "candidate_and_retained_axis_role_joins": role_joins,
            "load_cases": len(adapted_cases),
        },
        "mass_resultants": mass_resultants,
        "readiness": readiness,
        "limits": [
            "Exact STEP body identity and file bytes do not establish a solver mesh or element/node mapping.",
            "The source topology map is an inventory join; it has no solver DOF or mass-transfer implementation.",
            "The six current load cases are applied force/wrench inputs only; they provide no reactions, joint demands, load sharing, or stability result.",
            "No material assignment, attachment law, boundary condition, solver load target, or response is created by this adapter.",
        ],
    }
    _require(
        all(
            value is False
            for key, value in readiness.items()
            if isinstance(value, bool)
        ),
        "adapter raised a readiness or release flag",
    )
    _require(
        all(value is False for value in manifest["release"].values()),
        "attempt04 release gate is not fully false",
    )
    return audit, contract


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(payload)
    except FileExistsError as exc:
        raise AdapterError(
            f"refusing to replace append-only attempt artifact: {path}"
        ) from exc


def write_attempt_outputs(
    root: Path, attempt_dir: Path, audit: Mapping[str, Any], contract: Mapping[str, Any]
) -> None:
    root = root.resolve()
    attempt_dir = attempt_dir.resolve()
    try:
        attempt_rel = attempt_dir.relative_to(root)
    except ValueError as exc:
        raise AdapterError(
            "attempt output directory must be inside the repository"
        ) from exc
    audit_path = attempt_dir / "adapter-audit.json"
    contract_path = attempt_dir / "current-frame-adapter-contract.json"
    terminal_path = attempt_dir / "terminal-hashes.json"
    existing = [
        path.name
        for path in (audit_path, contract_path, terminal_path)
        if path.exists()
    ]
    _require(not existing, f"refusing to replace existing attempt outputs: {existing}")
    _write_json(audit_path, audit)
    _write_json(contract_path, contract)

    artifact_paths = [
        "fea/wood_joint_current_frame_adapter.py",
        "tests/test_wood_joint_current_frame_adapter.py",
        (attempt_rel / "README.md").as_posix(),
        (attempt_rel / "source-pins.json").as_posix(),
        (attempt_rel / "adapter-audit.json").as_posix(),
        (attempt_rel / "current-frame-adapter-contract.json").as_posix(),
    ]
    hash_records = []
    for relative_path in sorted(artifact_paths):
        file_path = _safe_source_path(root, relative_path)
        hash_records.append(
            {
                "path": relative_path,
                "sha256": _sha256_file(file_path),
                "size_bytes": file_path.stat().st_size,
            }
        )
    terminal_hashes = {
        "schema": "wood_joint_current_frame_adapter_terminal_hashes/v1",
        "scope": "Terminal hashes for adapter source, tests, source pins, README, and deterministic generated outputs; this hash file is self-excluded.",
        "artifacts": hash_records,
    }
    _write_json(terminal_path, terminal_hashes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--attempt-dir", type=Path, default=ATTEMPT_REL)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write deterministic audit and adapter outputs",
    )
    args = parser.parse_args()
    root = args.repo_root.resolve()
    attempt_dir = (
        args.attempt_dir if args.attempt_dir.is_absolute() else root / args.attempt_dir
    )
    pins_path = attempt_dir / "source-pins.json"
    try:
        pins = _load_json(root, pins_path.relative_to(root).as_posix())
        audit, contract = audit_current_frame(root, pins)
        if args.write:
            write_attempt_outputs(root, attempt_dir, audit, contract)
        print(
            json.dumps(
                {
                    "result": audit["result"],
                    "checks": audit["checks"],
                    "verified_counts": audit["verified_counts"],
                    "readiness": audit["readiness"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    except (AdapterError, OSError, ValueError) as exc:
        parser.exit(2, f"current-frame adapter audit failed closed: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
