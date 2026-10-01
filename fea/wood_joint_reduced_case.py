"""Assemble one source-bound reduced wood-joint static case.

The default case is the zero-gap a12-rear diagnostic seed with no 25 kg
accessory allowance. It assembles geometry, conditional connections, source
gravity and one climbing patch; it does not run a native solve or qualify the
candidate. The returned physical nodal ownership/load maps support a separate
equilibrium audit and response runner.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

REPOSITORY = Path(__file__).resolve().parents[1]
if str(REPOSITORY) not in sys.path:
    sys.path.insert(0, str(REPOSITORY))

from fea import wood_joint_reduced_body_loads as body_loads
from fea import wood_joint_reduced_geometry as reduced_geometry
from fea import wood_joint_reduced_gravity as hardware_gravity
from fea import wood_joint_reduced_loads as gravity_loads
from fea import wood_joint_reduced_model as reduced_model
from fea import wood_joint_reduced_panels as panel_api
from fea import wood_joint_reduced_properties as connector_properties

ROOT = REPOSITORY
MODEL_INPUTS_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
CHECK_PATH = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/case-assembly-check.json"
SCHEMA = "wood_joint_reduced_case_assembly/v1"
GRAVITY_M_S2 = 9.80665
WRENCH_TOL = 2.0e-6


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _v3(value: Any) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    if result.shape != (3,) or not np.isfinite(result).all():
        raise ValueError("Expected a finite global XYZ triplet")
    return result


def _cross(first: Any, second: Any) -> list[float]:
    return np.cross(_v3(first), _v3(second)).tolist()


def _moment_global(point: Any, force: Any, couple: Any = (0., 0., 0.)) -> list[float]:
    return (np.cross(_v3(point), _v3(force)) + _v3(couple)).tolist()


def _close(actual: Any, expected: Any, *, tol: float = WRENCH_TOL, label: str) -> None:
    first, second = _v3(actual), _v3(expected)
    error = np.max(np.abs(first - second))
    if error > tol * max(1.0, float(np.max(np.abs(second)))):
        raise AssertionError(f"{label}: {first.tolist()} != {second.tolist()} (max residual {error:g})")


def _accumulate(target: dict[Any, list[float]], key: Any, value: Any) -> None:
    target[key] = (np.asarray(target.get(key, [0., 0., 0.]), dtype=float)
                   + _v3(value)).tolist()


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return sorted(_json_safe(item) for item in value)
    return value


def _physical_body_topology(structure) -> tuple[dict[str, list[int]], dict[str, list[int]], dict[int, str]]:
    body_elements: dict[str, list[int]] = {}
    body_nodes: dict[str, list[int]] = {}
    node_owner: dict[int, str] = {}
    body_ids = sorted((*structure.members.keys(), *structure.panels.keys()))
    if len(body_ids) != 50 or len(set(body_ids)) != 50:
        raise AssertionError(f"Expected 50 unique physical source bodies, got {len(body_ids)}")
    for body in body_ids:
        groups = ([body] if body in structure.members
                  else list(structure.panel_layer_groups[body]))
        element_ids = [eid for group in groups for eid in structure.groups.get(group, [])]
        if not element_ids:
            raise AssertionError(f"Physical body has no solid elements: {body}")
        node_ids = sorted({int(node) for eid in element_ids
                           for node in structure.elements[eid][1]})
        if not node_ids:
            raise AssertionError(f"Physical body has no element-owned nodes: {body}")
        body_elements[body] = sorted(int(eid) for eid in element_ids)
        body_nodes[body] = node_ids
        for node in node_ids:
            previous = node_owner.setdefault(node, body)
            if previous != body:
                raise AssertionError(
                    f"Physical solid node {node} has multiple owners: {previous}, {body}"
                )
    return body_elements, body_nodes, node_owner


def _equation_load_expander(structure) -> dict[int, dict[int, list[tuple[int, float]]]]:
    """Map translational slave loads to physical master nodes by virtual work."""
    expanded: dict[int, dict[int, list[tuple[int, float]]]] = defaultdict(dict)
    for equation in structure.equations:
        if not equation:
            continue
        slave, dof, coefficient = equation[0]
        if int(dof) not in (1, 2, 3) or abs(float(coefficient) - 1.0) > 1.0e-12:
            continue
        # Panel point loads use affine surface attachment equations.  Rigid
        # connector point equations also start with a unit translational
        # slave, but contain rotational master DOFs and are not load
        # interpolation weights.
        if any(int(master_dof) != int(dof) for _, master_dof, _ in equation[1:]):
            continue
        masters = [(int(node), -float(weight)) for node, _, weight in equation[1:]
                   if abs(float(weight)) > 1.0e-13]
        total = sum(weight for _, weight in masters)
        if not masters or abs(total - 1.0) > 1.0e-8:
            continue
        if int(dof) in expanded[int(slave)]:
            raise AssertionError(f"Duplicate translational attachment equation: node {slave}, DOF {dof}")
        expanded[int(slave)][int(dof)] = masters
    return expanded


def _record_panel_loads(structure, body: str, nodal_rows: list[Any], *,
                        owner_by_node: dict[int, str], expander: dict[int, dict[int, list[tuple[int, float]]]],
                        body_loads_by_node: dict[str, dict[int, list[float]]],
                        source_label: str) -> list[dict[str, Any]]:
    """Expand panel point-slave forces to physical C3D20 nodes for balance."""
    normalized: list[dict[str, Any]] = []
    for row in nodal_rows:
        if isinstance(row, dict):
            node, force = int(row["node"]), _v3(row["force_xyz_n"])
        else:
            node, force = int(row[0]), _v3(row[1])
        if owner_by_node.get(node) == body:
            _accumulate(body_loads_by_node[body], node, force)
            normalized.append({"node": node, "force_xyz_n": force.tolist(), "load_source_node": node})
            continue
        if node not in expander:
            raise AssertionError(f"{source_label}: loaded node {node} is not owned by {body} or an attachment")
        for dof in (1, 2, 3):
            masters = expander[node].get(dof)
            if masters is None:
                raise AssertionError(f"{source_label}: attachment node {node} lacks DOF {dof} map")
            for master, weight in masters:
                if owner_by_node.get(master) != body:
                    raise AssertionError(f"{source_label}: attachment master {master} is outside panel {body}")
                component = np.zeros(3)
                component[dof - 1] = force[dof - 1] * weight
                _accumulate(body_loads_by_node[body], master, component)
                normalized.append({"node": master, "force_xyz_n": component.tolist(),
                                   "load_source_node": node, "attachment_weight": weight})
    return normalized


def _nodal_wrench(structure, nodal_map: dict[int, list[float]]) -> tuple[list[float], list[float]]:
    force = np.zeros(3)
    moment = np.zeros(3)
    for node, value in nodal_map.items():
        point = _v3(structure.nodes[int(node)])
        nodal_force = _v3(value)
        force += nodal_force
        moment += np.cross(point, nodal_force)
    return force.tolist(), moment.tolist()


def _add_expected_body_wrench(expected: dict[str, dict[str, list[float]]], body: str,
                              point: Any, force: Any, couple: Any, source_name: str,
                              source_ledger: list[dict[str, Any]]) -> None:
    force_v, couple_v = _v3(force), _v3(couple)
    global_moment = np.cross(_v3(point), force_v) + couple_v
    if body not in expected:
        expected[body] = {"force_xyz_n": [0., 0., 0.], "moment_about_global_origin_xyz_nmm": [0., 0., 0.]}
    expected[body]["force_xyz_n"] = (np.asarray(expected[body]["force_xyz_n"]) + force_v).tolist()
    expected[body]["moment_about_global_origin_xyz_nmm"] = (
        np.asarray(expected[body]["moment_about_global_origin_xyz_nmm"]) + global_moment
    ).tolist()
    source_ledger.append({
        "source_name": source_name,
        "receiver_body": body,
        "application_point_xyz_mm": _v3(point).tolist(),
        "force_xyz_n": force_v.tolist(),
        "couple_xyz_nmm_about_application_point": couple_v.tolist(),
        "global_moment_xyz_nmm": global_moment.tolist(),
    })


def _merge_hashes(*maps: dict[str, str]) -> dict[str, str]:
    combined: dict[str, str] = {}
    for source_map in maps:
        for path, digest in source_map.items():
            previous = combined.setdefault(str(path), str(digest))
            if previous != str(digest):
                raise ValueError(f"Conflicting source hashes for {path}")
    return dict(sorted(combined.items()))


def build_case(
    case_id: str = "a12-rear",
    *,
    accessory_scenario_id: str | None = None,
    mesh_size_mm: float = 150.0,
    ring_case: str = "A",
    panel_group_factor: float = 1.0,
    hillman_axial_ratio: float | None = 1.0,
    bolt_gap_factor: float = 0.0,
    contact_penalty_n_per_mm3: float = 100.0,
) -> tuple[Any, Any, dict[str, Any]]:
    """Build one audited case and return ``(structure, panels, metadata)``.

    ``accessory_scenario_id`` deliberately defaults to ``None`` and only that
    value is accepted for this first-response seed; the 25 kg alternatives
    remain a separately staged sensitivity.  Material and connector kwargs
    are explicit so the diagnostic assumptions appear in the record.
    """
    if accessory_scenario_id is not None:
        raise ValueError("The first assembled response seed excludes 25 kg accessories; pass None")
    model_inputs = json.loads(MODEL_INPUTS_PATH.read_text(encoding="utf-8"))
    cases = {row["case_id"]: row for row in model_inputs["cases"]}
    if case_id not in cases:
        raise ValueError(f"Unknown frozen climbing case {case_id!r}; choose one of {sorted(cases)}")
    case = cases[case_id]

    structure, panels, geometry_metadata = reduced_geometry.build_geometry(
        mesh_size_mm, ring_case=ring_case, panel_group_factor=panel_group_factor
    )
    geometry_audit = reduced_geometry.audit_geometry(structure, panels, geometry_metadata)
    if not geometry_audit["all_passed"]:
        raise ValueError("Current reduced geometry attachment audit failed")
    geometry_metadata["attachment_audit"] = geometry_audit
    if geometry_audit["native_solve_executed"] or geometry_audit["loads_added"]:
        raise AssertionError("Geometry audit must finish before any loads or native solve")

    property_data = connector_properties.build(
        hillman_axial_ratio_grid=None if hillman_axial_ratio is None else [hillman_axial_ratio]
    )
    if property_data["revision_id"] != model_inputs["revision_id"]:
        raise AssertionError("Connector properties and case inputs have different revisions")
    contact_geometry = json.loads(reduced_geometry.CONTACT_GEOMETRY.read_text(encoding="utf-8"))
    connection_metadata = reduced_model.add_connections(
        structure, panels, geometry_metadata, property_data, model_inputs,
        contact_geometry, hillman_axial_ratio=hillman_axial_ratio,
        bolt_gap_factor=bolt_gap_factor,
        contact_penalty_n_per_mm3=contact_penalty_n_per_mm3,
    )

    load_data = gravity_loads.compile_loads()
    hardware_data = hardware_gravity.compile_body_gravity()
    if load_data["revision_id"] != model_inputs["revision_id"] or hardware_data["revision_id"] != model_inputs["revision_id"]:
        raise AssertionError("Gravity carriers and current case inputs have different revisions")
    _close(load_data["base_mass_accounting"]["gravity_force_global_xyz_n"],
           hardware_data["equilibrium"]["all_778_source_force_xyz_n"],
           label="independent gravity compiler global force")
    _close(load_data["base_mass_accounting"]["gravity_moment_about_global_origin_xyz_nmm"],
           hardware_data["equilibrium"]["all_778_source_moment_about_global_origin_xyz_nmm"],
           label="independent gravity compiler global moment")

    body_elements, body_nodes, owner_by_node = _physical_body_topology(structure)
    member_node_loads: dict[str, dict[int, list[float]]] = {body: {} for body in body_nodes}
    expected_body: dict[str, dict[str, list[float]]] = {}
    source_ledger: list[dict[str, Any]] = []
    load_source_owner: dict[str, list[str]] = defaultdict(list)
    own_weight_audits = []

    source_rows = {row["source_name"]: row for row in load_data["source_rows"]}
    if len(source_rows) != 778:
        raise AssertionError("Expected all 778 unique source mass rows in the gravity inventory")
    kind_counts = load_data["base_mass_accounting"]["source_entity_kind_counts"]
    if kind_counts.get("current_physical_member_solid") != 50 or kind_counts.get("current_physical_tnut_component") != 142:
        raise AssertionError("Member/T-nut source partition changed")
    hardware_rows = {row["name"]: row for row in hardware_data["source_rows"]}
    expected_hardware_names = {
        name for name, row in source_rows.items()
        if row["source_entity_kind"] in (
            "current_candidate_hardware_component",
            "current_retained_frame_hardware_component",
            "current_panel_screw_axis_envelope_proxy",
        )
    }
    if len(hardware_rows) != 586 or set(hardware_rows) != expected_hardware_names:
        raise AssertionError("Hardware source rows do not exactly partition the 586 omitted components")

    # Member self-weight is applied as distributed consistent body gravity.
    member_names: set[str] = set()
    for name, row in source_rows.items():
        if row["source_entity_kind"] != "current_physical_member_solid":
            continue
        body = row["source_receiver_member_ids"][0]
        if body != name or body not in body_nodes or body in member_names:
            raise AssertionError(f"Member source body does not map uniquely to its physical body: {name}")
        member_names.add(body)
        contribution = row["contributions"][0]
        result = body_loads.add_body_self_weight(
            structure, body, row["mass_kg"], row["source_centroid_xyz_mm"]
        )
        own_weight_audits.append({
            "source_name": name,
            "body": body,
            "source_mass_kg": row["mass_kg"],
            "source_centroid_xyz_mm": row["source_centroid_xyz_mm"],
            "mesh_centroid_xyz_mm": result["mesh_centroid_xyz_mm"],
            "mesh_volume_mm3": result["mesh_volume_mm3"],
            "gravity_force_xyz_n": contribution["force_xyz_n"],
            "gravity_moment_about_global_origin_xyz_nmm": row["source_moment_about_global_origin_xyz_nmm"],
            "centroid_correction_total_absolute_nodal_force_n": result["centroid_correction_total_absolute_nodal_force_n"],
        })
        for load in result["loads"]:
            node = int(load["node"])
            if owner_by_node.get(node) != body:
                raise AssertionError(f"Self-weight node {node} is not owned by source body {body}")
            _accumulate(member_node_loads[body], node, load["force_xyz_n"])
        _add_expected_body_wrench(
            expected_body, body, row["source_centroid_xyz_mm"], contribution["force_xyz_n"],
            [0., 0., 0.], name, source_ledger,
        )
        load_source_owner[name].append(body)
    if len(member_names) != 50:
        raise AssertionError(f"Expected 50 distributed member/panel self weights, got {len(member_names)}")

    # T-nuts use their exact mapped climbing-face panel point and source couple.
    tnut_rows = [row for row in load_data["source_rows"]
                 if row["source_entity_kind"] == "current_physical_tnut_component"]
    tnut_names: set[str] = set()
    equation_expander = _equation_load_expander(structure)
    panel_load_records: list[dict[str, Any]] = []
    tnut_load_audits = []
    for row in tnut_rows:
        name = row["source_name"]
        if name in tnut_names or len(row["contributions"]) != 1:
            raise AssertionError(f"T-nut source should have exactly one current panel carrier: {name}")
        tnut_names.add(name)
        load = row["contributions"][0]
        receivers = row["source_receiver_member_ids"]
        panel_id = receivers[0]
        if len(receivers) != 1 or panel_id not in structure.panels:
            raise AssertionError(f"T-nut carrier is not its current panel: {name}")
        point = load["reference_point_xyz_mm"]
        label = "gravity/tnut/" + name
        record = panels.add_point_wrench(
            panel_id, point, load["force_xyz_n"], load["couple_xyz_nmm_about_reference"],
            moment_reference_xyz_mm=point, label=label, allow_source_hole=True,
        )
        # add_point_wrench creates this carrier's affine panel attachment.
        # Refresh the map after that mutation so its slave force can be
        # expanded to physical solid nodes for the independent balance audit.
        equation_expander = _equation_load_expander(structure)
        record["source_name"] = name
        record["source_component_mass_kg"] = row["mass_kg"]
        normalized = _record_panel_loads(
            structure, panel_id, record["nodal_forces"], owner_by_node=owner_by_node,
            expander=equation_expander, body_loads_by_node=member_node_loads,
            source_label=name,
        )
        _add_expected_body_wrench(
            expected_body, panel_id, point, load["force_xyz_n"],
            load["couple_xyz_nmm_about_reference"], name, source_ledger,
        )
        record["physical_body_nodal_forces"] = normalized
        panel_load_records.append(record)
        tnut_load_audits.append({
            "source_name": name, "panel_id": panel_id, "mass_kg": row["mass_kg"],
            "point_xyz_mm": point, "force_xyz_n": load["force_xyz_n"],
            "couple_xyz_nmm_about_reference": load["couple_xyz_nmm_about_reference"],
        })
        load_source_owner[name].append(panel_id)
    if len(tnut_names) != 142:
        raise AssertionError(f"Expected 142 individually applied T-nuts, got {len(tnut_names)}")

    # The 586 omitted hardware sources apply at source-axis receiver locations.
    hardware_load_audits = []
    applied_hardware_names: set[str] = set()
    for row in hardware_data["source_rows"]:
        name = row["name"]
        if name in applied_hardware_names:
            raise AssertionError(f"Omitted hardware mass duplicated: {name}")
        applied_hardware_names.add(name)
        source_row = source_rows[name]
        if abs(source_row["mass_kg"] - row["mass_kg"]) > 1.0e-10:
            raise AssertionError(f"Hardware source mass mismatch: {name}")
        for contribution in row["body_load_contributions"]:
            body = contribution["receiver_member_id"]
            if body not in body_nodes:
                raise AssertionError(f"Hardware receiver is not one of the 50 physical bodies: {body}")
            applied = body_loads.add_body_point_wrench(
                structure, body, contribution["application_point_xyz_mm"],
                contribution["force_xyz_n"],
                contribution["couple_xyz_nmm_about_application_point"],
            )
            if applied["body"] != body:
                raise AssertionError(f"Hardware point-wrench receiver changed: {name}")
            for nodal in applied["nodal_forces"]:
                node = int(nodal["node"])
                if owner_by_node.get(node) != body:
                    raise AssertionError(f"Hardware load node {node} is not owned by receiver {body}")
                _accumulate(member_node_loads[body], node, nodal["force_xyz_n"])
            _add_expected_body_wrench(
                expected_body, body, contribution["application_point_xyz_mm"],
                contribution["force_xyz_n"],
                contribution["couple_xyz_nmm_about_application_point"], name, source_ledger,
            )
            hardware_load_audits.append({
                "source_name": name,
                "receiver_body": body,
                "mass_share_kg": contribution["mass_share_kg"],
                "application_point_xyz_mm": contribution["application_point_xyz_mm"],
                "force_xyz_n": contribution["force_xyz_n"],
                "couple_xyz_nmm_about_application_point": contribution["couple_xyz_nmm_about_application_point"],
                "applied_element": applied["element"],
            })
            load_source_owner[name].append(body)
    if applied_hardware_names != expected_hardware_names:
        raise AssertionError("Applied hardware sources differ from the omitted source inventory")

    # Exactly one source-bound climbing patch is added to the selected panel.
    case_panel = case["loaded_panel"]
    if case_panel not in structure.panels:
        raise AssertionError(f"Climbing load target is not a current panel: {case_panel}")
    case_record = panels.add_case_patch_wrench(case)
    if case_record["label"] != case_id or case_record["panel_id"] != case_panel:
        raise AssertionError("Panel adapter returned an unexpected case-patch owner")
    normalized_case = _record_panel_loads(
        structure, case_panel, case_record["nodal_forces"], owner_by_node=owner_by_node,
        expander=equation_expander, body_loads_by_node=member_node_loads,
        source_label="climbing_case/" + case_id,
    )
    case_record["physical_body_nodal_forces"] = normalized_case
    panel_load_records.append(case_record)
    source_applied = case["source_applied_load"]
    case_ref = source_applied["wrench_reference_point_global_xyz_mm"]
    case_force = source_applied["applied_force_global_xyz_n"]
    case_couple = source_applied["moment_global_xyz_nmm"]
    _add_expected_body_wrench(
        expected_body, case_panel, case_ref, case_force, case_couple,
        "climbing_case/" + case_id, source_ledger,
    )
    load_source_owner["climbing_case/" + case_id].append(case_panel)
    if sum(record.get("load_kind") == "uniform_square_patch_wrench" for record in panel_load_records) != 1:
        raise AssertionError("Expected exactly one panel climbing patch load")

    actual_body_wrenches: dict[str, dict[str, list[float]]] = {}
    max_body_force_residual = max_body_moment_residual = 0.0
    body_wrench_rows = []
    for body in sorted(body_nodes):
        force, moment = _nodal_wrench(structure, member_node_loads[body])
        expected = expected_body.get(body, {"force_xyz_n": [0., 0., 0.],
                                            "moment_about_global_origin_xyz_nmm": [0., 0., 0.]})
        force_error = _v3(force) - _v3(expected["force_xyz_n"])
        moment_error = _v3(moment) - _v3(expected["moment_about_global_origin_xyz_nmm"])
        max_body_force_residual = max(max_body_force_residual, float(np.max(np.abs(force_error))))
        max_body_moment_residual = max(max_body_moment_residual, float(np.max(np.abs(moment_error))))
        _close(force, expected["force_xyz_n"], label=f"{body} body force")
        _close(moment, expected["moment_about_global_origin_xyz_nmm"],
               label=f"{body} body moment")
        actual_body_wrenches[body] = {
            "force_xyz_n": force,
            "moment_about_global_origin_xyz_nmm": moment,
        }
        body_wrench_rows.append({
            "body": body, "node_count": len(body_nodes[body]),
            "loaded_node_count": len(member_node_loads[body]),
            "force_xyz_n": force,
            "moment_about_global_origin_xyz_nmm": moment,
            "force_residual_xyz_n": force_error.tolist(),
            "moment_residual_xyz_nmm": moment_error.tolist(),
        })

    physical_external_loads: dict[int, list[float]] = {}
    for body, nodal_map in member_node_loads.items():
        for node, force in nodal_map.items():
            if owner_by_node.get(int(node)) != body:
                raise AssertionError(f"Physical external load is outside its owner body: {body}/{node}")
            _accumulate(physical_external_loads, int(node), force)
    total_actual_force = np.zeros(3)
    total_actual_moment = np.zeros(3)
    for node, force in physical_external_loads.items():
        point = _v3(structure.nodes[int(node)])
        vector = _v3(force)
        total_actual_force += vector
        total_actual_moment += np.cross(point, vector)

    gravity_force = _v3(load_data["base_mass_accounting"]["gravity_force_global_xyz_n"])
    gravity_moment = _v3(load_data["base_mass_accounting"]["gravity_moment_about_global_origin_xyz_nmm"])
    case_global_moment = _v3(_moment_global(case_ref, case_force, case_couple))
    expected_total_force = gravity_force + _v3(case_force)
    expected_total_moment = gravity_moment + case_global_moment
    _close(total_actual_force, expected_total_force, label="assembled case global force")
    _close(total_actual_moment, expected_total_moment, label="assembled case global moment")
    panel_load_audit = panels.audit_wrenches()
    if not panel_load_audit["all_passed"] or panel_load_audit["load_count"] != 143:
        raise AssertionError("The 142 T-nut and one climbing patch panel wrenches did not audit")

    source_names_applied = set(member_names) | tnut_names | applied_hardware_names
    if len(source_names_applied) != 778 or source_names_applied != set(source_rows):
        raise AssertionError("Every base source mass must be applied exactly once")
    expected_hardware_contributions = hardware_data["inventory_summary"]["body_receiver_contribution_count"]
    expected_ledger_rows = 50 + 142 + expected_hardware_contributions + 1
    if len(source_ledger) != expected_ledger_rows:
        raise AssertionError(
            f"Expected one body-resolved row per member/T-nut/hardware receiver contribution plus case; "
            f"got {len(source_ledger)} vs {expected_ledger_rows}"
        )
    if len(structure.loads) == 0:
        raise AssertionError("No physical source nodal loads were assembled")
    if bolt_gap_factor == 0.0 and any(
        float(spring.get("radial_clearance_mm", 0.0)) > 0.0 for spring in structure.springs
    ):
        raise AssertionError("Zero-gap seed contains a positive radial spring gap")

    # Keep a root-relative, live-verifiable inventory of all inputs used by
    # the source-bound adapters, including member and panel STEP files.
    def root_relative_hashes(source_map: dict[str, str]) -> dict[str, str]:
        result = {}
        for source_path, digest in source_map.items():
            path = Path(source_path)
            if path.is_absolute():
                try:
                    path = path.resolve().relative_to(ROOT)
                except ValueError as exc:
                    raise ValueError(f"Pinned source is outside the repository: {source_path}") from exc
            relative = path.as_posix()
            live_path = ROOT / path
            if not live_path.is_file() or _sha256(live_path) != str(digest):
                raise ValueError(f"Pinned source does not match live repository data: {relative}")
            result[relative] = str(digest)
        return result

    source_maps = [
        root_relative_hashes(property_data["source_sha256"]),
        root_relative_hashes(load_data["source_sha256"]),
        root_relative_hashes(hardware_data["source_sha256"]),
        root_relative_hashes({row["path"]: row["sha256"]
                              for row in geometry_metadata["source_documents"].values()}),
    ]
    for descriptor in model_inputs["members"]:
        binding = descriptor["current_finished_step_binding"]
        source_maps.append(root_relative_hashes({binding["path"]: binding["file_sha256"]}))
    for descriptor in geometry_metadata["panel_mesh_metadata"].values():
        source_maps.append(root_relative_hashes({descriptor["step_path"]: descriptor["step_sha256"]}))
    # The material binder records nested path/hash pairs for its timber and
    # block material maps, helper code and selected material table.
    def collect_material_hashes(value: Any) -> dict[str, str]:
        found: dict[str, str] = {}
        if isinstance(value, dict):
            path = value.get("path")
            digest = value.get("sha256")
            if isinstance(path, str) and isinstance(digest, str):
                found[path] = digest
            for child in value.values():
                found.update(collect_material_hashes(child))
        elif isinstance(value, list):
            for child in value:
                found.update(collect_material_hashes(child))
        return found

    source_maps.append(root_relative_hashes(collect_material_hashes(geometry_metadata["material_binding"])))
    input_hashes = _merge_hashes(*source_maps)
    model_inputs_sha256 = input_hashes[str(MODEL_INPUTS_PATH.relative_to(ROOT))]

    # Explicit source-module hashes make the returned assembler record stand alone.
    module_paths = [
        Path(__file__).resolve(), Path(reduced_geometry.__file__).resolve(),
        Path(connector_properties.__file__).resolve(), Path(reduced_model.__file__).resolve(),
        Path(body_loads.__file__).resolve(), Path(gravity_loads.__file__).resolve(),
        Path(hardware_gravity.__file__).resolve(), Path(panel_api.__file__).resolve(),
    ]
    module_hashes = {str(path.relative_to(ROOT)): _sha256(path)
                     for path in module_paths if path.is_file() and path.is_relative_to(ROOT)}
    input_hashes = _merge_hashes(input_hashes, module_hashes)

    body_geometry = {}
    for body in sorted(body_nodes):
        if body in structure.members:
            member = structure.members[body]
            record = _json_safe(member["record"])
            kind = "member"
        else:
            record = panels.panel_metadata(body)
            kind = "panel"
        body_geometry[body] = {
            "kind": kind,
            "element_count": len(body_elements[body]),
            "node_count": len(body_nodes[body]),
            "geometry_record": record,
        }
    expected_physical_body_names = sorted(row["member_id"] for row in model_inputs["members"])
    if expected_physical_body_names != sorted(body_nodes):
        raise AssertionError("Physical body inventory differs from the pinned member and panel source inventory")

    hardware_axis_audits: dict[str, dict[str, Any]] = {}
    for row in hardware_data["source_rows"]:
        axis_id = str(row["source_axis_id"])
        audit = hardware_axis_audits.setdefault(axis_id, {
            "source_axis_id": axis_id,
            "source_entity_kind": row["source_entity_kind"],
            "current_receiver_member_ids": row["current_receiver_member_ids"],
            "receiver_intervals": row["receiver_intervals"],
            "source_axis_center_xyz_mm": row["body_load_contributions"][0]["source_axis_center_xyz_mm"],
            "source_axis_unit_direction_global": row["body_load_contributions"][0]["source_axis_unit_direction_global"],
            "axis_interval_basis": sorted({
                str(interval["interval_basis"])
                for interval in row["receiver_intervals"]
            }),
            "source_names": [],
        })
        audit["source_names"].append(row["name"])

    metadata = {
        "schema": SCHEMA,
        "scope": "conditional_reduced_wood_joint_static_case",
        "candidate": model_inputs["candidate"],
        "geometry_revision_id": model_inputs["revision_id"],
        "source_model_inputs_sha256": model_inputs_sha256,
        "case_id": case_id,
        "case_input": case,
        "scenario": {
            "mesh_size_mm": float(mesh_size_mm),
            "ring_case": ring_case,
            "panel_group_factor": float(panel_group_factor),
            "hillman_axial_to_lateral_ratio": hillman_axial_ratio,
            "hillman_ratio_status": "non-qualifying diagnostic only" if hillman_axial_ratio is not None else "known omission case",
            "bolt_gap_factor": float(bolt_gap_factor),
            "contact_penalty_n_per_mm3": float(contact_penalty_n_per_mm3),
            "accessory_scenario_id": None,
            "accessory_budget_kg": 0.0,
            "floor": "unverified no-slip assumption only while each floor cell bears",
            "zero_gap_seed_is_diagnostic_only": bolt_gap_factor == 0.0,
        },
        "material_binding": geometry_metadata["material_binding"],
        "source_sha256": input_hashes,
        "geometry_source_documents": geometry_metadata["source_documents"],
        "geometry_audit": {
            key: geometry_audit[key] for key in (
                "contact_patch_count", "contact_area_cell_count", "floor_cell_count",
                "attachment_attempt_count", "attachment_success_count", "attachment_failure_count",
                "source_bore_abstraction_count", "affine_motion_audit_failure_count",
                "all_passed", "native_solve_executed",
            )
        },
        "body_geometry": body_geometry,
        "physical_body_elements": body_elements,
        "physical_body_nodes": body_nodes,
        "expected_physical_body_names": expected_physical_body_names,
        "physical_body_loads": {
            body: {node: force for node, force in sorted(nodal_map.items())}
            for body, nodal_map in sorted(member_node_loads.items())
        },
        "physical_external_loads": physical_external_loads,
        "physical_body_wrenches": actual_body_wrenches,
        "expected_physical_body_wrenches": expected_body,
        "source_wrench_ledger": source_ledger,
        "connection_ownership": connection_metadata["connection_ownership"],
        "connection_attachment_rows": connection_metadata["connection_attachment_rows"],
        "connection_counts": connection_metadata["counts"],
        "connection_scenario": connection_metadata["scenario"],
        "contact_cell_ownership": geometry_audit["sample_geometry_records"],
        "floor_support_nodes": sorted(int(node) for node in structure.fixed),
        "gravity_load_audits": {
            "member_self_weight_rows": own_weight_audits,
            "tnut_point_loads": tnut_load_audits,
            "hardware_receiver_point_loads": hardware_load_audits,
            "hardware_gravity_inventory": hardware_data["inventory_summary"],
            "hardware_axis_interval_audits": hardware_axis_audits,
            "hardware_gross_fill_scope": (
                "Only the declared fastener-bore abstraction is used for gross section receiver intervals. "
                "Current source-axis ids, receiver identities, signed intervals, and interval bases are listed "
                "above. Central declared bores are omitted from gross support; other non-coaxial cavities are "
                "not classified by this bounded audit."
            ),
            "base_mass_accounting": load_data["base_mass_accounting"],
            "hardware_equilibrium": hardware_data["equilibrium"],
            "panel_load_wrench_audit": panel_load_audit,
        },
        "panel_load_records": [
            {key: value for key, value in row.items() if key != "nodal_forces"}
            for row in panel_load_records
        ],
        "case_assembly_audit": {
            "source_mass_rows_applied_once": len(source_names_applied),
            "member_self_weight_row_count": len(own_weight_audits),
            "tnut_row_count": len(tnut_load_audits),
            "omitted_hardware_row_count": len(applied_hardware_names),
            "hardware_receiver_contribution_count": len(hardware_load_audits),
            "physical_body_count": len(body_nodes),
            "physical_body_node_count": len(owner_by_node),
            "physical_element_count": sum(len(eids) for eids in body_elements.values()),
            "unique_physical_node_ownership": True,
            "max_body_force_residual_n": max_body_force_residual,
            "max_body_moment_residual_nmm": max_body_moment_residual,
            "global_force_xyz_n": total_actual_force.tolist(),
            "global_moment_about_origin_xyz_nmm": total_actual_moment.tolist(),
            "expected_global_force_xyz_n": expected_total_force.tolist(),
            "expected_global_moment_about_origin_xyz_nmm": expected_total_moment.tolist(),
            "no_unreported_gap_reference_loads": True,
            "physical_nodal_loads_captured_before_auxiliary_gap_offsets": True,
            "native_solve_executed": False,
            "mechanical_acceptance": False,
        },
        "physical_load_sources_by_body": {
            body: sorted({name for name, receivers in load_source_owner.items() if body in receivers})
            for body in sorted(body_nodes)
        },
        "body_wrench_audit_rows": body_wrench_rows,
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "scope_limit": "One source-bound static diagnostic seed only. Solver response, active-set consistency, capacities, physical fastener properties, delivered materials, accessories, and design acceptance are not established.",
    }
    return structure, panels, metadata


def case_assembly_check(
    case_id: str = "a12-rear",
    *,
    accessory_scenario_id: str | None = None,
    mesh_size_mm: float = 150.0,
    ring_case: str = "A",
    panel_group_factor: float = 1.0,
    hillman_axial_ratio: float | None = 1.0,
    bolt_gap_factor: float = 0.0,
) -> dict[str, Any]:
    _, _, metadata = build_case(
        case_id, accessory_scenario_id=accessory_scenario_id,
        mesh_size_mm=mesh_size_mm, ring_case=ring_case,
        panel_group_factor=panel_group_factor,
        hillman_axial_ratio=hillman_axial_ratio,
        bolt_gap_factor=bolt_gap_factor,
    )
    audit = metadata["case_assembly_audit"]
    serialized_metadata = json.dumps(metadata, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return {
        "schema": "wood_joint_reduced_case_assembly_check/v1",
        "status": "PASS_SOURCE_CASE_LOAD_WRENCH_CONSERVATION",
        "candidate": metadata["candidate"],
        "geometry_revision_id": metadata["geometry_revision_id"],
        "case_id": case_id,
        "scenario": metadata["scenario"],
        "case_metadata_sha256": hashlib.sha256(serialized_metadata.encode("utf-8")).hexdigest(),
        "source_sha256": metadata["source_sha256"],
        "geometry_audit": metadata["geometry_audit"],
        "connection_counts": metadata["connection_counts"],
        "source_inventory": {
            "unique_base_mass_sources_applied_once": audit["source_mass_rows_applied_once"],
            "distributed_body_self_weight_rows": audit["member_self_weight_row_count"],
            "tnut_panel_point_load_rows": audit["tnut_row_count"],
            "omitted_hardware_rows": audit["omitted_hardware_row_count"],
            "omitted_hardware_receiver_contributions": audit["hardware_receiver_contribution_count"],
            "omitted_hardware_mass_kg": metadata["gravity_load_audits"]["hardware_gravity_inventory"]["omitted_hardware_condensed_mass_kg"],
            "accessory_budget_kg": 0.0,
        },
        "physical_mesh": {
            "body_count": audit["physical_body_count"],
            "unique_solid_node_count": audit["physical_body_node_count"],
            "solid_element_count": audit["physical_element_count"],
        },
        "body_load_wrench_conservation": {
            "max_force_residual_n": audit["max_body_force_residual_n"],
            "max_moment_residual_nmm": audit["max_body_moment_residual_nmm"],
            "body_count": len(metadata["physical_body_wrenches"]),
        },
        "global_equilibrium": {
            "force_xyz_n": audit["global_force_xyz_n"],
            "moment_about_origin_xyz_nmm": audit["global_moment_about_origin_xyz_nmm"],
            "expected_force_xyz_n": audit["expected_global_force_xyz_n"],
            "expected_moment_about_origin_xyz_nmm": audit["expected_global_moment_about_origin_xyz_nmm"],
        },
        "panel_load_audit": {
            "load_count": metadata["gravity_load_audits"]["panel_load_wrench_audit"]["load_count"],
            "all_passed": metadata["gravity_load_audits"]["panel_load_wrench_audit"]["all_passed"],
            "case_patch_count": 1,
        },
        "unique_physical_node_ownership": audit["unique_physical_node_ownership"],
        "physical_nodal_loads_captured_before_gap_offsets": audit["physical_nodal_loads_captured_before_auxiliary_gap_offsets"],
        "native_solve_executed": False,
        "mechanical_acceptance": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-id", default="a12-rear")
    parser.add_argument("--accessory-scenario-id", default=None)
    parser.add_argument("--mesh-size-mm", type=float, default=150.0)
    parser.add_argument("--ring-case", choices=("A", "B"), default="A")
    parser.add_argument("--panel-group-factor", type=float, default=1.0)
    parser.add_argument("--hillman-axial-ratio", type=float, default=1.0)
    parser.add_argument("--bolt-gap-factor", type=float, default=0.0)
    parser.add_argument("--check-output", type=Path, default=CHECK_PATH)
    args = parser.parse_args()
    result = case_assembly_check(
        args.case_id, accessory_scenario_id=args.accessory_scenario_id,
        mesh_size_mm=args.mesh_size_mm, ring_case=args.ring_case,
        panel_group_factor=args.panel_group_factor,
        hillman_axial_ratio=args.hillman_axial_ratio,
        bolt_gap_factor=args.bolt_gap_factor,
    )
    args.check_output.parent.mkdir(parents=True, exist_ok=True)
    args.check_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
