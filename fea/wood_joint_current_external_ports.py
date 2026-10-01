"""Freeze work-conjugate rail/principal ports for the current ordinary patch.

The ports are observations and distributed load patches on the source-defined
remote end sections. They do not tie or restrain the cleat. This module creates
input evidence only; a nonlinear solve and its mechanical interpretation are
separate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from fea.floor_contact import FACES
from fea.wood_joint_patch_contact_contract import parse_c3d10_deck

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
MESH_DECK = BASE / "ordinary-patch-mesh-attempt02/mesh/mesh.inp"
MESH_REPORT = BASE / "ordinary-patch-mesh-attempt02/mesh/mesh.json"
PATCH_INVENTORY = BASE / "ordinary-patch-inputs-attempt01/inventory.json"

PINS = {
    "mesh_deck": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh_report": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "patch_inventory": "70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3",
}
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
PORTS = {
    "rail": ("W01_BASE_RAIL_BOTTOM_RIGHT", "12"),
    "principal": ("W02_BASE_PRINCIPAL_CENTER_RIGHT", "16"),
}
ROTATION_LENGTH_MM = 1000.0
PLANE_TOL_MM = 1e-5
MAP_TOL = 2e-11
GAUGE_NODE_DOFS = ((33985, (1, 2, 3)), (56117, (2, 3)), (32577, (3,)))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skew(v: np.ndarray) -> np.ndarray:
    x, y, z = map(float, v)
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def _tri6_chord_area(nodes: dict[int, tuple[float, float, float]],
                     conn: tuple[int, ...], side: int) -> float:
    pts = [np.asarray(nodes[conn[i]], dtype=float) for i in FACES[side - 1]]
    a, b, c, d, e, f = pts
    triangles = ((a, d, f), (d, b, e), (f, e, c), (d, e, f))
    return math.fsum(float(np.linalg.norm(np.cross(y - x, z - x)) / 2)
                     for x, y, z in triangles)


def _read_sources() -> tuple[dict[str, Any], dict[int, tuple[float, float, float]],
                              dict[int, tuple[int, ...]]]:
    paths = {"mesh_deck": MESH_DECK, "mesh_report": MESH_REPORT,
             "patch_inventory": PATCH_INVENTORY}
    actual = {name: sha(path) for name, path in paths.items()}
    if actual != PINS:
        raise ValueError(f"ordinary-patch source pin mismatch: {actual}")
    report = json.loads(MESH_REPORT.read_text())
    inventory = json.loads(PATCH_INVENTORY.read_text())
    nodes, elements, _elsets = parse_c3d10_deck(MESH_DECK.read_text(), context=str(MESH_DECK))
    if len(nodes) != 116_162 or len(elements) != 57_643:
        raise ValueError("frozen mesh count differs from the authenticated WJ24 mesh")
    return {"report": report, "inventory": inventory, "source_sha256": actual}, nodes, elements


def prepare_remote_gauge(destination: Path) -> dict[str, Any]:
    """Freeze a new six-scalar global gauge away from both external load ports."""
    sources, nodes, _elements = _read_sources()
    report = sources["report"]
    principal = report["bodies"]["W02_BASE_PRINCIPAL_CENTER_RIGHT"]
    owner_nodes = set(map(int, principal["nodes"]))
    port_nodes = set(map(int, principal["surface_inventory"]["16"]["tri6_node_ids"]))
    other_port = report["bodies"]["W01_BASE_RAIL_BOTTOM_RIGHT"]["surface_inventory"]["12"]
    port_nodes |= set(map(int, other_port["tri6_node_ids"]))

    contact_nodes: set[int] = set()
    active = False
    contact_path = BASE / "ordinary-patch-contact-deck-attempt01/contact-fragment.inc"
    for raw in contact_path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("*"):
            active = line.upper().startswith("*NSET,NSET=WJCP_N_")
            continue
        if active and line and not line.startswith("**"):
            contact_nodes.update(int(cell.strip()) for cell in line.split(",") if cell.strip())

    gauge_ids = [node for node, _dofs in GAUGE_NODE_DOFS]
    if not set(gauge_ids) <= owner_nodes or set(gauge_ids) & (port_nodes | contact_nodes):
        raise ValueError("remote global gauge overlaps a port, contact patch, or wrong owner")
    a = np.asarray(nodes[gauge_ids[0]], dtype=float)
    rows = []
    for node_id, dofs in GAUGE_NODE_DOFS:
        relative = np.asarray(nodes[node_id], dtype=float) - a
        rigid = np.column_stack((np.eye(3), -skew(relative) / ROTATION_LENGTH_MM))
        for dof in dofs:
            rows.append(rigid[dof - 1])
    matrix = np.asarray(rows)
    singular = np.linalg.svd(matrix, compute_uv=False)
    rank = int(np.linalg.matrix_rank(matrix, tol=singular[0] * 1e-10))
    if rank != 6 or singular[-1] / singular[0] < 1e-4:
        raise ValueError("remote 3-2-1 global gauge does not robustly remove six rigid modes")
    rows_inp = ["** Six-scalar global rigid-motion gauge; no cleat restraint or local spring.",
                "*BOUNDARY"]
    for node_id, dofs in GAUGE_NODE_DOFS:
        for dof in dofs:
            rows_inp.append(f"{node_id},{dof},{dof},0.")
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    deck_path = destination / "gauge.inp"
    deck_path.write_text("\n".join(rows_inp) + "\n")
    gauge = {
        "schema": "wood_joint_current_external_port_gauge/v1",
        "status": "FROZEN_SIX_GLOBAL_RIGID_GAUGES_ONLY",
        "source_sha256": sources["source_sha256"],
        "contact_fragment_sha256": sha(contact_path),
        "nodes": [
            {"node_id": node_id, "global_xyz_mm": list(nodes[node_id]),
             "fixed_global_dofs": list(dofs),
             "owner": "W02_BASE_PRINCIPAL_CENTER_RIGHT"}
            for node_id, dofs in GAUGE_NODE_DOFS
        ],
        "port_node_overlap": False,
        "contact_node_overlap": False,
        "rigid_matrix_origin": "node 33985; rigid rotations scaled by 1000 mm",
        "rigid_body_matrix": matrix.tolist(),
        "singular_values": singular.tolist(),
        "rank": rank,
        "rank_threshold_relative": 1e-10,
        "distance_to_principal_external_port_plane_mm": [
            float(np.dot(np.asarray(principal["surface_inventory"]["16"]["cad_centroid_global_xyz_mm"])
                         - np.asarray(nodes[node_id]),
                         np.asarray([0., .6427876096867989, .7660444431187603])))
            for node_id in gauge_ids
        ],
        "deck_sha256": sha(deck_path),
        "limits": [
            "Gauge removes six whole-model rigid motions only; it is not a physical support.",
            "Gauge reactions must be checked against the self-equilibrated port loading.",
            "Cleat and all bolt, washer, and nut-related internal motions remain unconstrained by this gauge.",
        ],
    }
    report_path = destination / "gauge.json"
    report_path.write_text(json.dumps(gauge, indent=2) + "\n")
    return gauge


def _origin_and_basis(inventory: dict[str, Any]) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    interfaces = inventory["wood_interfaces"]
    reference = {
        "bottom_center_right_cleat_to_base_rail_bottom_right",
        "bottom_center_right_cleat_to_base_principal_center_right",
        "base_rail_bottom_right_to_base_principal_center_right",
    }
    selected = [row for row in interfaces if row["interface_id"] in reference]
    if {row["interface_id"] for row in selected} != reference:
        raise ValueError("the three ordinary-patch interfaces are not all present")
    total_area = math.fsum(float(row["finite_overlap_area_mm2"]) for row in selected)
    origin = sum(
        float(row["finite_overlap_area_mm2"])
        * np.asarray(row["finite_overlap_area_centroid_global_xyz_mm"], dtype=float)
        for row in selected
    ) / total_area
    x = np.array([1.0, 0.0, 0.0])
    t = np.array([0.0, 0.6427876096867989, 0.7660444431187603])
    n = np.cross(x, t)
    basis = np.column_stack((x, t, n))
    if not np.allclose(basis.T @ basis, np.eye(3), rtol=0, atol=2e-15):
        raise ValueError("response frame is not orthonormal")
    return origin, basis, {
        "origin_rule": "finite-common-area-weighted centroid of all three ordinary wood interfaces",
        "origin_global_xyz_mm": origin.tolist(),
        "basis_columns_global_xyz": basis.tolist(),
        "basis_labels": ["X", "T", "N"],
        "basis_basis": "X is the rail grain; T and N are source-frame principal/cleat directions",
        "rotation_length_mm": ROTATION_LENGTH_MM,
        "interface_area_sum_mm2": total_area,
    }


def _make_port(name: str, body_id: str, surface_tag: str,
               report: dict[str, Any], nodes: dict[int, tuple[float, float, float]],
               elements: dict[int, tuple[int, ...]], basis: np.ndarray,
               inventory: dict[str, Any]) -> dict[str, Any]:
    body = report["bodies"][body_id]
    surface = body["surface_inventory"][surface_tag]
    expected_axis = {
        "rail": np.array([1.0, 0.0, 0.0]),
        "principal": np.array([0.0, 0.6427876096867989, 0.7660444431187603]),
    }[name]
    source_key = body["source_step_artifact_key"]
    source_record = inventory["step_artifacts"][source_key]
    source_bounds = source_record["source_solid"]["bounds_xyz_mm"]
    if source_record["file_sha256"] != body["source_step_sha256"]:
        raise ValueError(f"{name}: mesh body and source STEP hashes differ")
    checks = source_record["identity_checks"]
    if not all(checks.get(key) is True for key in ("bounds", "centroid", "solid_count", "volume")):
        raise ValueError(f"{name}: source STEP identity checks are incomplete")
    if not checks.get("symmetric_difference", {}).get("passed"):
        raise ValueError(f"{name}: source STEP geometry readback is not identical")
    # Bind the external section by its physical meaning: the full-stock cap at
    # the distal end along the member axis, not by a transient CAD surface tag.
    projections = []
    for tag, candidate in body["surface_inventory"].items():
        centroid = np.asarray(candidate["cad_centroid_global_xyz_mm"], dtype=float)
        projections.append((float(centroid @ expected_axis), tag, candidate))
    projections.sort(reverse=True, key=lambda row: row[0])
    selected_projection = float(np.dot(
        np.asarray(surface["cad_centroid_global_xyz_mm"], dtype=float), expected_axis))
    if projections[0][1] != surface_tag or projections[0][0] - projections[1][0] < 1e-3:
        raise ValueError(f"{name}: selected section is not the unique distal source surface")
    normal_cosine = float(np.dot(
        np.asarray(surface["analytic_surface_data"]["sample_normal_global"], dtype=float),
        expected_axis))
    expected_section_area = 139.7 * 38.1
    if abs(normal_cosine - 1.0) > 1e-10 or abs(float(surface["cad_area_mm2"]) - expected_section_area) > 1e-5:
        raise ValueError(f"{name}: source section is not the outward full 2x6 end cap")
    refs = [tuple(map(int, row)) for row in surface["tri6_exterior_face_refs"]]
    if len(refs) != 16:
        raise ValueError(f"{name}: expected the source-defined 16-face external section")
    nodal_area: dict[int, float] = {}
    chord_area = 0.0
    for element, side in refs:
        conn = elements[element]
        face_nodes = [conn[i] for i in FACES[side - 1]]
        if len(set(face_nodes)) != 6:
            raise ValueError(f"{name}: degenerate TRI6 source face")
        area = _tri6_chord_area(nodes, conn, side)
        if not math.isfinite(area) or area <= 0:
            raise ValueError(f"{name}: invalid TRI6 area")
        chord_area += area
        for node in face_nodes:
            nodal_area[node] = nodal_area.get(node, 0.0) + area / 6.0
    ids = sorted(nodal_area)
    if len(ids) != 43 or set(ids) != set(map(int, surface["tri6_node_ids"])):
        raise ValueError(f"{name}: CAD section nodes differ from the exact face references")
    target_area = float(surface["cad_area_mm2"])
    area_error = abs(chord_area - target_area) / target_area
    if area_error > 5e-8:
        raise ValueError(f"{name}: TRI6 chord area does not reproduce source CAD area")
    origin = np.asarray(surface["cad_centroid_global_xyz_mm"], dtype=float)
    normal = np.asarray(surface["analytic_surface_data"]["sample_normal_global"], dtype=float)
    normal /= np.linalg.norm(normal)
    xyz = np.asarray([nodes[i] for i in ids], dtype=float)
    plane_residual = np.max(np.abs((xyz - origin) @ normal))
    if plane_residual > PLANE_TOL_MM:
        raise ValueError(f"{name}: external port nodes leave the source CAD plane")
    w = np.asarray([nodal_area[i] for i in ids], dtype=float)
    w /= np.sum(w)

    # B maps local [uX,uT,uN,L thetaX,L thetaT,L thetaN] to global nodal u.
    blocks = [np.column_stack((basis, -skew(point - origin) @ basis / ROTATION_LENGTH_MM))
              for point in xyz]
    bmat = np.vstack(blocks)
    weights = np.repeat(w, 3)
    gram = bmat.T @ (weights[:, None] * bmat)
    singular = np.linalg.svd(gram, compute_uv=False)
    if singular[-1] <= singular[0] * 1e-12:
        raise ValueError(f"{name}: the port does not span six rigid-section modes")
    cmat = np.linalg.solve(gram, bmat.T * weights[None, :])
    identity_error = float(np.max(np.abs(cmat @ bmat - np.eye(6))))
    if identity_error > MAP_TOL:
        raise ValueError(f"{name}: displacement map is not a left inverse")
    return {
        "name": name,
        "body_id": body_id,
        "surface_tag": surface_tag,
        "surface_semantic_status": "SOURCE_BOUND_DISTAL_FULL_STOCK_END_SECTION",
        "semantic_binding": {
            "source_step_artifact_key": source_key,
            "source_step_file": source_record["file"],
            "source_step_sha256": source_record["file_sha256"],
            "source_step_readback_identity_checks": checks,
            "source_solid_global_bounds_xyz_mm": source_bounds,
            "member_axis_unit_global": expected_axis.tolist(),
            "selection_rule": "unique planar full 2x6 section with outward normal along the member axis and maximum centroid projection among this exact source solid's exterior surfaces",
            "selected_centroid_axis_projection_mm": selected_projection,
            "next_exterior_surface_centroid_projection_mm": projections[1][0],
            "projection_separation_to_next_surface_mm": projections[0][0] - projections[1][0],
            "outward_normal_dot_member_axis": normal_cosine,
            "full_section_area_mm2": expected_section_area,
            "tag_status": "transient mesh source tag retained only as a hash-bound locator; semantic selection does not depend on tag permanence or face ordinal",
        },
        "face_refs_element_side": [list(row) for row in refs],
        "node_ids": ids,
        "global_xyz_mm": xyz.tolist(),
        "positive_area_weights_normalized": w.tolist(),
        "source_surface_normal_global": normal.tolist(),
        "port_origin_global_xyz_mm": origin.tolist(),
        "cad_area_mm2": target_area,
        "tri6_chord_area_mm2": chord_area,
        "relative_area_error": area_error,
        "plane_max_residual_mm": float(plane_residual),
        "weighted_rigid_basis": bmat.tolist(),
        "displacement_map_C": cmat.tolist(),
        "gram_singular_values": singular.tolist(),
        "left_inverse_max_abs_error": identity_error,
        "weight_rule": "each exact TRI6 face chord area is split positively and equally among its six nodes",
    }


def _nodal_forces(port: dict[str, Any], basis: np.ndarray, force_global: np.ndarray,
                  moment_at_port_global: np.ndarray) -> np.ndarray:
    cmat = np.asarray(port["displacement_map_C"], dtype=float)
    scaled_local_wrench = np.r_[basis.T @ force_global,
                                basis.T @ moment_at_port_global / ROTATION_LENGTH_MM]
    return (cmat.T @ scaled_local_wrench).reshape((-1, 3))


def _wrench_about(points: np.ndarray, forces: np.ndarray, datum: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    total_f = np.sum(forces, axis=0)
    total_m = np.sum(np.cross(points - datum, forces), axis=0)
    return total_f, total_m


def _format(value: float) -> str:
    if abs(value) < 5e-15:
        return "0.0"
    result = f"{value:.13e}"
    if len(result) > 20:
        raise ValueError("CLOAD coefficient exceeds CalculiX fixed-width field")
    return result


def _case_loads(ports: dict[str, Any], origin: np.ndarray, basis: np.ndarray,
                case: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    axis_token, sign_token = case.rsplit("_", 1)
    sign = 1.0 if sign_token == "plus" else -1.0
    direction = np.zeros(6)
    axis_index = {"x": 0, "t": 1, "n": 2, "rx": 3, "rt": 4, "rn": 5}[axis_token]
    generalized = 1.0 if axis_index < 3 else ROTATION_LENGTH_MM
    direction[axis_index] = sign * generalized
    force_local, moment_local = direction[:3], direction[3:]
    force_global = basis @ force_local
    moment_global = basis @ moment_local
    rows: list[dict[str, Any]] = []
    audit = {}
    for name, multiplier in (("rail", 1.0), ("principal", -1.0)):
        port = ports[name]
        rport = np.asarray(port["port_origin_global_xyz_mm"], dtype=float)
        f = multiplier * force_global
        m_at_joint = multiplier * moment_global
        m_at_port = m_at_joint - np.cross(rport - origin, f)
        xyz = np.asarray(port["global_xyz_mm"], dtype=float)
        nodal = _nodal_forces(port, basis, f, m_at_port)
        resultant_f, resultant_m = _wrench_about(xyz, nodal, origin)
        force_scale = max(1.0, float(np.linalg.norm(f)))
        moment_scale = max(ROTATION_LENGTH_MM, float(np.linalg.norm(m_at_joint)),
                           float(np.linalg.norm(rport - origin)) * force_scale)
        if np.linalg.norm(resultant_f - f) > 1e-10 * force_scale:
            raise ValueError(f"{case}/{name}: nodal port force does not recover the target")
        if np.linalg.norm(resultant_m - m_at_joint) > 2e-10 * moment_scale:
            raise ValueError(f"{case}/{name}: nodal port moment does not recover the target")
        audit[name] = {
            "target_force_global_n": f.tolist(),
            "target_moment_at_joint_global_nmm": m_at_joint.tolist(),
            "target_moment_at_port_global_nmm": m_at_port.tolist(),
            "recovered_force_global_n": resultant_f.tolist(),
            "recovered_moment_at_joint_global_nmm": resultant_m.tolist(),
            "force_error_n": float(np.linalg.norm(resultant_f - f)),
            "moment_error_nmm": float(np.linalg.norm(resultant_m - m_at_joint)),
        }
        for node, force in zip(port["node_ids"], nodal, strict=True):
            for dof, value in enumerate(force, 1):
                if abs(value) > 5e-15:
                    rows.append({"owner": port["body_id"], "port": name,
                                 "node_id": node, "dof": dof,
                                 "force_n": float(value)})
    pair_force = np.sum([row["target_force_global_n"] for row in audit.values()], axis=0)
    pair_moment = np.sum([row["target_moment_at_joint_global_nmm"] for row in audit.values()], axis=0)
    if np.linalg.norm(pair_force) > 1e-10 or np.linalg.norm(pair_moment) > 1e-7:
        raise ValueError(f"{case}: rail/principal pair is not self-equilibrated")
    return rows, {"case": case, "generalized_wrench_local": direction.tolist(),
                  "rail_and_principal_audits": audit,
                  "pair_force_global_n": pair_force.tolist(),
                  "pair_moment_at_joint_global_nmm": pair_moment.tolist(),
                  "load_rule": "equal and opposite work-conjugate wrenches at one joint datum, translated to each remote port and dual-mapped to its TRI6 nodes"}


def _render_deck(case: str, load_rows: list[dict[str, Any]],
                 monitor_ids: list[int]) -> str:
    lines = [
        "** Reconstructed ordinary patch external-port diagnostic; cleat remains free.",
        "*INCLUDE,INPUT=mesh.inp",
        "*INCLUDE,INPUT=materials.inp",
        "*INCLUDE,INPUT=nut-coupling.inp",
        "*INCLUDE,INPUT=rigid-carriers.inp",
        "*INCLUDE,INPUT=contact-fragment.inc",
        "*INCLUDE,INPUT=output-sets.inp",
        "*INCLUDE,INPUT=gauge.inp",
        "*NSET,NSET=WJ_EXTERNAL_PORT_MONITOR",
    ]
    lines.extend(",".join(map(str, monitor_ids[i:i + 16]))
                 for i in range(0, len(monitor_ids), 16))
    lines.extend([
        "*AMPLITUDE,NAME=WJ_RAMP",
        "0.,0.,1.,1.",
        f"** CASE {case}",
        "*STEP,NLGEOM,INC=100",
        "*STATIC",
        "0.001,1.,1.e-8,0.05",
        "*CLOAD,AMPLITUDE=WJ_RAMP",
    ])
    for row in load_rows:
        lines.append(f"{row['node_id']},{row['dof']},{_format(row['force_n'])}")
    lines.extend([
        "*NODE PRINT,NSET=WJ_EXTERNAL_PORT_MONITOR,FREQUENCY=1",
        "U,RF",
        "*NODE FILE,NSET=WJ_EXTERNAL_PORT_MONITOR,FREQUENCY=1",
        "U,RF",
        "*EL FILE,FREQUENCY=1",
        "S,E",
        "*EL PRINT,ELSET=CURRENT_ALL_ELEMENTS,TOTALS=ONLY,FREQUENCY=1",
        "ELSE,ELKE,EMAS,EVOL",
        "*CONTACT PRINT,FREQUENCY=1",
        "CDIS,CSTR,CELS,CNUM",
    ])
    contact_path = BASE / "ordinary-patch-contact-deck-attempt01/contact-fragment.inc"
    text = contact_path.read_text()
    pairs = []
    raw = text.splitlines()
    for i, line in enumerate(raw):
        if line.upper().startswith("*CONTACT PAIR,"):
            data = next(x.strip() for x in raw[i + 1:] if x.strip() and not x.strip().startswith("**"))
            pairs.append(tuple(x.strip() for x in data.split(",")))
    if len(pairs) != 35 or len(set(pairs)) != 35:
        raise ValueError("the frozen 35-pair contact manifest changed")
    for slave, master in pairs:
        lines.extend([f"*CONTACT PRINT,SLAVE={slave},MASTER={master},FREQUENCY=1", "CF,CFN,CFS"])
    lines.append("*END STEP")
    return "\n".join(lines) + "\n"


def prepare(bundle: Path) -> dict[str, Any]:
    bundle = bundle.resolve()
    if not (bundle / "input-freeze.json").is_file():
        raise ValueError("build the source-bound zero-load model in this bundle first")
    model_freeze = json.loads((bundle / "input-freeze.json").read_text())
    if model_freeze.get("revision") != REVISION:
        raise ValueError("model revision differs from the current owner-reviewed joint")
    sources, node_coords, elements = _read_sources()
    origin, basis, frame = _origin_and_basis(sources["inventory"])
    port_data = {
        name: _make_port(name, body_id, tag, sources["report"], node_coords,
                         elements, basis, sources["inventory"])
        for name, (body_id, tag) in PORTS.items()
    }
    nut_coupling = json.loads((bundle / "nut-coupling.json").read_text())
    nut_control_ids = sorted({
        int(per_nut["control_node_ids"][key])
        for per_nut in nut_coupling["per_nut"]
        for key in ("translation_reference_node_id", "rotation_control_node_id")
    })
    monitor_ids = sorted({*port_data["rail"]["node_ids"],
                          *port_data["principal"]["node_ids"],
                          *(node for node, _dofs in GAUGE_NODE_DOFS),
                          *nut_control_ids})
    cases = {}
    for axis in ("x", "t", "n", "rx", "rt", "rn"):
        for sign in ("plus", "minus"):
            name = f"{axis}_{sign}"
            loads, audit = _case_loads(port_data, origin, basis, name)
            cases[name] = {"loads": loads, "audit": audit}
            (bundle / f"response_{name}.inp").write_text(
                _render_deck(name, loads, monitor_ids))
    report = {
        "schema": "wood_joint_current_external_ports/v1",
        "status": "FROZEN_INPUT_ONLY_NO_RESPONSE_ACCEPTANCE",
        "revision": REVISION,
        "source_sha256": sources["source_sha256"],
        "producer_sha256": sha(Path(__file__)),
        "case_deck_sha256": {
            name: sha(bundle / f"response_{name}.inp") for name in cases
        },
        "frame": frame,
        "ports": port_data,
        "signed_cases": {name: case["audit"] for name, case in cases.items()},
        "cleat_boundary_or_constraint": False,
        "port_application": "nodal CLOAD dual distribution; no port coupling, tie, or boundary condition",
        "only_global_gauge": "six source-frozen remote principal-member scalar gauges from gauge.inp",
        "nut_control_node_monitor_ids": nut_control_ids,
        "control_state_output": "all eight pseudo-node control IDs are included in WJ_EXTERNAL_PORT_MONITOR NODE PRINT and NODE FILE requests",
        "case_scale": {"translation_force_n": 1.0,
                       "rotation_couple_nmm": ROTATION_LENGTH_MM,
                       "interpretation": "unit scaled generalized wrench; numerical diagnostic only"},
        "physical_limits": [
            "The model is reconstructed from preserved source artifacts and is not attempt03-identical.",
            "The six-DOF shaft-to-nut fit, boreless rigid nut seat carriers and elastic timber are explicit assumptions.",
            "Nominal hole/shaft clearance is geometry from CAD occupancy, not a measurement of delivered holes or bolts.",
            "No friction, preload, physical thread law, failure law, or capacity is represented.",
            "No station result is transferred by this input freeze.",
        ],
    }
    report_path = bundle / "external-ports.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    source_snapshot = Path(__file__)
    (bundle / "external-ports-producer.py.snapshot").write_bytes(source_snapshot.read_bytes())
    common_hashes = model_freeze["artifacts_sha256"]
    if common_hashes != {name: sha(bundle / name) for name in common_hashes}:
        raise ValueError("common model artifacts changed while freezing external ports")
    supplementary_names = [
        "external-ports.json",
        "external-ports-producer.py.snapshot",
        *(f"response_{axis}_{sign}.inp"
          for axis in ("x", "t", "n", "rx", "rt", "rn")
          for sign in ("plus", "minus")),
    ]
    step_hashes = {}
    for port in port_data.values():
        semantic = port["semantic_binding"]
        step_path = BASE / "ordinary-patch-inputs-attempt01/wood" / semantic["source_step_file"]
        actual_step_hash = sha(step_path)
        if actual_step_hash != semantic["source_step_sha256"]:
            raise ValueError(f"source STEP hash changed: {step_path}")
        step_hashes[semantic["source_step_file"]] = actual_step_hash
    lock = {
        "schema": "wood_joint_current_external_port_bundle_lock/v1",
        "status": "FROZEN_SUPPLEMENTAL_EXTERNAL_PORT_CASES",
        "revision": REVISION,
        "input_freeze_sha256": sha(bundle / "input-freeze.json"),
        "source_solver_image": model_freeze["solver_image"],
        "source_solver_binary_sha256": "6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b",
        "frozen_common_artifacts_sha256": common_hashes,
        "external_port_source_sha256": sources["source_sha256"],
        "semantic_source_step_sha256": step_hashes,
        "supplemental_case_artifacts_sha256": {
            name: sha(bundle / name) for name in supplementary_names
        },
        "case_names": list(cases),
        "limits": [
            "Bundle is a reconstructed, source-bound replacement and is not attempt03-identical.",
            "Hashes freeze input bytes; they do not establish physical adequacy or response acceptance.",
            "Cleat has no boundary condition; only the six scalars in gauge.inp remove whole-model rigid modes.",
        ],
    }
    (bundle / "bundle-lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    if sha(report_path) == "":
        raise AssertionError("unreachable digest check")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path, nargs="?")
    parser.add_argument("--write-gauge", type=Path)
    args = parser.parse_args()
    if args.write_gauge is not None:
        result = prepare_remote_gauge(args.write_gauge)
        print(json.dumps({"status": result["status"], "rank": result["rank"],
                          "gauge": str(args.write_gauge.resolve())}, indent=2))
        return
    if args.bundle is None:
        parser.error("bundle is required unless --write-gauge is supplied")
    result = prepare(args.bundle)
    print(json.dumps({"status": result["status"],
                      "ports": {name: {"nodes": len(row["node_ids"]),
                                       "area_mm2": row["cad_area_mm2"],
                                       "left_inverse_error": row["left_inverse_max_abs_error"]}
                                for name, row in result["ports"].items()},
                      "signed_case_count": len(result["signed_cases"]),
                      "bundle": str(args.bundle.resolve())}, indent=2))


if __name__ == "__main__":
    main()
