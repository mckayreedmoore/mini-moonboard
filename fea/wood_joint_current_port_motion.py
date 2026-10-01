"""Build a source-bound port-motion diagnostic with the cleat unconstrained.

The port coordinates are section projections only.  The equations do not make
either section rigid; they impose six work-conjugate section coordinates at the
two actual full-stock ends and leave all other port and cleat motions free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from fea.floor_contact import FACES
from fea.wood_joint_current_external_ports import BASE, ROTATION_LENGTH_MM, sha, skew
from fea.wood_joint_patch_contact_contract import parse_c3d10_deck


def _term_rows(terms: list[tuple[int, int, float]]) -> list[str]:
    lines = []
    for start in range(0, len(terms), 4):
        group = terms[start:start + 4]
        lines.append(",".join(cell for node, dof, value in group
                               for cell in (str(node), str(dof), f"{value:.12e}")))
    return lines


def _id_rows(node_ids: list[int]) -> list[str]:
    return [",".join(map(str, node_ids[start:start + 16]))
            for start in range(0, len(node_ids), 16)]


def _dependency_variables(nut_include: Path) -> set[tuple[int, int]]:
    lines = nut_include.read_text().splitlines()
    dependent: set[tuple[int, int]] = set()
    i = 0
    while i < len(lines):
        if not lines[i].strip().upper().startswith("*EQUATION"):
            i += 1
            continue
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("**")):
            i += 1
        term_count = int(lines[i].strip())
        i += 1
        tokens: list[str] = []
        while i < len(lines) and len(tokens) < term_count * 3:
            row = lines[i].strip()
            i += 1
            if not row or row.startswith("**") or row.startswith("*"):
                continue
            tokens.extend(cell.strip() for cell in row.split(",") if cell.strip())
        if len(tokens) < term_count * 3:
            raise ValueError("truncated equation in the frozen nut-coupling input")
        dependent.add((int(tokens[0]), int(tokens[1])))
    return dependent


def _contact_surface_nodes(bundle: Path) -> set[int]:
    nodes, elements, _ = parse_c3d10_deck(
        (bundle / "mesh.inp").read_text(), context="port-motion frozen mesh")
    del nodes
    lines = (bundle / "contact-fragment.inc").read_text().splitlines()
    active = False
    found: set[int] = set()
    for raw in lines:
        line = raw.strip()
        if line.startswith("*"):
            active = line.upper().startswith("*SURFACE,") and "TYPE=ELEMENT" in line.upper()
            continue
        if not active or not line or line.startswith("**"):
            continue
        element_token, side_token = (cell.strip() for cell in line.split(",", 1))
        element = int(element_token)
        side = int(side_token.upper().removeprefix("S"))
        found.update(elements[element][local_id] for local_id in FACES[side - 1])
    return found


def _choose_dependencies(cmat: np.ndarray, node_ids: list[int],
                         reserved: set[tuple[int, int]]) -> list[int]:
    """Choose six independent physical DOFs with pivoted Gram-Schmidt."""
    candidates = [column for column in range(cmat.shape[1])
                  if (node_ids[column // 3], column % 3 + 1) not in reserved]
    orthogonal: list[np.ndarray] = []
    selected: list[int] = []
    for _ in range(6):
        best_column = -1
        best_residual: np.ndarray | None = None
        best_norm = 0.0
        for column in candidates:
            if column in selected:
                continue
            residual = cmat[:, column].copy()
            for direction in orthogonal:
                residual -= direction * float(direction @ residual)
            norm = float(np.linalg.norm(residual))
            if norm > best_norm:
                best_column, best_residual, best_norm = column, residual, norm
        if best_column < 0 or best_residual is None or best_norm < 1e-8:
            raise ValueError("section map cannot provide six stable dependent variables")
        selected.append(best_column)
        orthogonal.append(best_residual / best_norm)
    pivot = cmat[:, selected]
    condition = float(np.linalg.cond(pivot))
    if not np.isfinite(condition) or condition > 1e8:
        raise ValueError(f"port equation pivot block is poorly conditioned: {condition}")
    return selected


def _motion_transform(port_origin: np.ndarray, joint_origin: np.ndarray,
                      basis: np.ndarray) -> np.ndarray:
    offset_local = basis.T @ (port_origin - joint_origin)
    transform = np.eye(6)
    transform[:3, 3:] = -skew(offset_local) / ROTATION_LENGTH_MM
    return transform


def prepare(bundle: Path, case: str = "n_plus", generalized_motion_mm: float = 1.0,
            initial_increment: float = 0.01, maximum_increment: float = 0.05,
            step_total_time: float = 1.0,
            step_endpoint_amplitude: float = 1.0) -> dict[str, Any]:
    bundle = bundle.resolve()
    lock_path = bundle / "bundle-lock.json"
    if not lock_path.is_file():
        raise ValueError("external-port bundle lock is required")
    lock = json.loads(lock_path.read_text())
    if lock.get("status") != "FROZEN_SUPPLEMENTAL_EXTERNAL_PORT_CASES":
        raise ValueError("external-port source bundle is not frozen")
    port_path = bundle / "external-ports.json"
    ports_report = json.loads(port_path.read_text())
    for file_name, expected in lock["supplemental_case_artifacts_sha256"].items():
        if sha(bundle / file_name) != expected:
            raise ValueError(f"locked supplemental file changed: {file_name}")
    if sha(port_path) != lock["supplemental_case_artifacts_sha256"]["external-ports.json"]:
        raise ValueError("external port map differs from its frozen bundle lock")
    if generalized_motion_mm <= 0 or not np.isfinite(generalized_motion_mm):
        raise ValueError("generalized motion magnitude must be finite and positive")
    if initial_increment <= 0 or maximum_increment <= 0 or initial_increment > maximum_increment:
        raise ValueError("invalid static increment controls")
    if not np.isfinite(step_total_time) or step_total_time <= 0:
        raise ValueError("invalid static step total time")
    if (not np.isfinite(step_endpoint_amplitude)
            or not 0 < step_endpoint_amplitude <= 1):
        raise ValueError("step endpoint amplitude must be in (0, 1]")
    axis_token, sign_token = case.rsplit("_", 1)
    axis_index = {"x": 0, "t": 1, "n": 2, "rx": 3, "rt": 4, "rn": 5}[axis_token]
    sign = 1.0 if sign_token == "plus" else -1.0 if sign_token == "minus" else None
    if sign is None:
        raise ValueError("case sign must be plus or minus")
    frame = ports_report["frame"]
    joint_origin = np.asarray(frame["origin_global_xyz_mm"], dtype=float)
    basis = np.asarray(frame["basis_columns_global_xyz"], dtype=float)
    target = np.zeros(6)
    target[axis_index] = sign * generalized_motion_mm

    nut_json = json.loads((bundle / "nut-coupling.json").read_text())
    control_start = int(nut_json["fresh_control_node_allocation"]["last_control_node_id"]) + 1
    nut_dependent = _dependency_variables(bundle / "nut-coupling.inp")
    contact_nodes = _contact_surface_nodes(bundle)
    reserved = nut_dependent | {(node, dof) for node in contact_nodes for dof in (1, 2, 3)}
    port_controls: dict[str, list[int]] = {}
    all_port_dependencies: set[tuple[int, int]] = set()
    node_rows: list[str] = []
    equation_rows: list[str] = []
    equations: list[str] = [
        "** Six linear section-coordinate constraints per actual external member port.",
        "** These are projection equations, not rigid port ties; cleat remains free.",
    ]
    nset_nodes: list[int] = []
    per_port: dict[str, Any] = {}
    for port_index, name in enumerate(("rail", "principal")):
        port = ports_report["ports"][name]
        full_ids = list(map(int, port["node_ids"]))
        ids = full_ids
        xyz = np.asarray(port["global_xyz_mm"], dtype=float)
        weights = np.asarray(port["positive_area_weights_normalized"], dtype=float)
        if len(ids) != 43 or xyz.shape != (len(ids), 3) or weights.shape != (len(ids),):
            raise ValueError(f"{name}: source-bound force map must cover all 43 cap nodes")
        if abs(float(np.sum(weights)) - 1.0) > 2e-12:
            raise ValueError(f"{name}: full-cap force-map weights do not sum to one")
        port_origin = np.asarray(port["port_origin_global_xyz_mm"], dtype=float)
        bmat = np.vstack([
            np.column_stack((basis, -skew(point - port_origin) @ basis / ROTATION_LENGTH_MM))
            for point in xyz
        ])
        weighted = np.repeat(weights, 3)
        gram = bmat.T @ (weighted[:, None] * bmat)
        gram_singular = np.linalg.svd(gram, compute_uv=False)
        if gram_singular[-1] <= gram_singular[0] * 1e-12:
            raise ValueError(f"{name}: contact-free cap nodes do not span six section modes")
        cmat = np.linalg.solve(gram, bmat.T * weighted[None, :])
        identity_error = float(np.max(np.abs(cmat @ bmat - np.eye(6))))
        if identity_error > 2e-11:
            raise ValueError(f"{name}: port projection is not a verified left inverse")
        source_cmat = np.asarray(port["displacement_map_C"], dtype=float)
        if source_cmat.shape != cmat.shape or np.max(np.abs(cmat - source_cmat)) > 2e-11:
            raise ValueError(f"{name}: motion projection differs from the frozen force-dual map")
        transform = _motion_transform(port_origin, joint_origin, basis)
        joint_motion = (0.5 * target) if name == "rail" else (-0.5 * target)
        requested_port_motion = transform @ joint_motion
        dep_columns = _choose_dependencies(cmat, ids, reserved)
        deps = [(ids[column // 3], column % 3 + 1) for column in dep_columns]
        if len(set(deps)) != 6:
            raise ValueError(f"{name}: dependent physical port DOFs are not unique")
        if all_port_dependencies.intersection(deps) or set(deps).intersection(reserved):
            raise ValueError(f"{name}: port equation dependent-DOF collision")
        all_port_dependencies.update(deps)
        controls = list(range(control_start + port_index * 6,
                              control_start + (port_index + 1) * 6))
        port_controls[name] = controls
        nset_nodes.extend(controls)
        equation_term_counts: list[int] = []
        for q_index, control_id in enumerate(controls):
            xyz = port_origin
            node_rows.append(f"{control_id},{xyz[0]:.12f},{xyz[1]:.12f},{xyz[2]:.12f}")
        independent_columns = [column for column in range(cmat.shape[1])
                               if column not in set(dep_columns)]
        pivot = cmat[:, dep_columns]
        pivot_inverse = np.linalg.inv(pivot)
        independent_map = pivot_inverse @ cmat[:, independent_columns]
        if np.max(np.abs(pivot @ independent_map - cmat[:, independent_columns])) > 2e-10:
            raise ValueError(f"{name}: port equation elimination failed its reconstruction audit")
        if np.max(np.abs(pivot @ pivot_inverse - np.eye(6))) > 2e-10:
            raise ValueError(f"{name}: port equation pivot inverse failed its identity audit")
        for dep_index, dep in enumerate(deps):
            terms = [(dep[0], dep[1], 1.0)]
            for matrix_column, source_column in enumerate(independent_columns):
                coefficient = float(independent_map[dep_index, matrix_column])
                if coefficient != 0.0:
                    terms.append((ids[source_column // 3], source_column % 3 + 1,
                                  coefficient))
            for q_index, control_id in enumerate(controls):
                coefficient = -float(pivot_inverse[dep_index, q_index])
                if coefficient != 0.0:
                    terms.append((control_id, 1, coefficient))
            equation_term_counts.append(len(terms))
            equation_rows.extend(["*EQUATION", str(len(terms)), *_term_rows(terms)])
        per_port[name] = {
            "member_body": port["body_id"],
            "source_port_face_refs": port["face_refs_element_side"],
            "projection_matrix_sha256": hashlib.sha256(cmat.astype("<f8").tobytes()).hexdigest(),
            "projection_left_inverse_max_abs_error": identity_error,
            "projection_gram_singular_values": gram_singular.tolist(),
            "projection_condition_number": float(gram_singular[0] / gram_singular[-1]),
            "equation_pivot_condition_number": float(np.linalg.cond(pivot)),
            "equation_pivot_matrix": pivot.tolist(),
            "equation_pivot_inverse": pivot_inverse.tolist(),
            "equation_dependent_columns": dep_columns,
            "port_fit_node_ids": ids,
            "port_coordinate_definition": "source-bound full 43-node cap projection; identical to external-port force dual",
            "contact_port_node_ids_retained_as_independent_equation_terms": [
                node for node in full_ids if node in contact_nodes
            ],
            "positive_area_weights_normalized_on_fit_nodes": weights.tolist(),
            "control_displacement_map_C": cmat.tolist(),
            "control_weighted_rigid_basis": bmat.tolist(),
            "port_transform_from_joint_datum": transform.tolist(),
            "control_node_ids": controls,
            "controlled_q_port_local_mm": requested_port_motion.tolist(),
            "dependent_physical_dofs": [list(item) for item in deps],
            "equation_term_counts": equation_term_counts,
        }
    equations.extend(["*NODE", *node_rows, *equation_rows,
                      "*NSET,NSET=WJ_PORT_MOTION_CONTROLS"])
    equations.extend(_id_rows(nset_nodes))
    cleat_node_ids = list(map(int, json.loads((bundle / "mesh.json").read_text())
                              ["bodies"]["W00_BOTTOM_CENTER_RIGHT_CLEAT"]["nodes"]))
    if len(cleat_node_ids) != 9369 or len(set(cleat_node_ids)) != len(cleat_node_ids):
        raise ValueError("the source-bound current cleat node set changed")
    equations.extend(["*NSET,NSET=WJ_PORT_MOTION_MONITOR"])
    monitor_nodes = sorted({
        *nset_nodes,
        *map(int, ports_report["ports"]["rail"]["node_ids"]),
        *map(int, ports_report["ports"]["principal"]["node_ids"]),
        *map(int, ports_report.get("nut_control_node_monitor_ids", [])),
    })
    equations.extend(_id_rows(monitor_nodes))
    equations.extend(["*NSET,NSET=WJ_CLEAT_POSE_NODES"])
    equations.extend(_id_rows(cleat_node_ids))
    for name in ("rail", "principal"):
        equations.append(f"*SURFACE,NAME=WJ_{name.upper()}_SECTION")
        equations.extend(
            f"{int(element)},S{int(side)}"
            for element, side in ports_report["ports"][name]["face_refs_element_side"]
        )
    control_include = bundle / "port-motion-controls.inp"
    deck_path = bundle / f"port_motion_{case}.inp"
    report_path = bundle / f"port-motion_{case}.json"
    source_snapshot_path = bundle / "port-motion-producer.py.snapshot"
    lock_output_path = bundle / f"port-motion-{case}-lock.json"
    if any(path.exists() for path in
           (control_include, deck_path, report_path, source_snapshot_path, lock_output_path)):
        raise FileExistsError("port-motion artifacts are immutable; use a new attempt directory")
    control_include.write_text("\n".join(equations) + "\n")
    deck = [
        "** Controlled external member response; both timber ends move symmetrically.",
        "** No cleat boundary, global support gauge, CLOAD, tie, or port rigidization.",
        "*INCLUDE,INPUT=mesh.inp",
        "*INCLUDE,INPUT=materials.inp",
        "*INCLUDE,INPUT=nut-coupling.inp",
        "*INCLUDE,INPUT=rigid-carriers.inp",
        "*INCLUDE,INPUT=contact-fragment.inc",
        "*INCLUDE,INPUT=output-sets.inp",
        "*INCLUDE,INPUT=port-motion-controls.inp",
        "*AMPLITUDE,NAME=WJ_PORT_MOTION_RAMP",
        f"0.,0.,{step_total_time:.12g},{step_endpoint_amplitude:.12g}",
        f"** SIGNED CASE {case}; scaled relative joint coordinate {target.tolist()} mm",
        "*STEP,NLGEOM,INC=100",
        "*STATIC",
        f"{initial_increment:.8g},{step_total_time:.8g},1.e-6,{maximum_increment:.8g}",
        "*BOUNDARY,AMPLITUDE=WJ_PORT_MOTION_RAMP",
    ]
    for port_name in ("rail", "principal"):
        values = per_port[port_name]["controlled_q_port_local_mm"]
        for control_id, value in zip(port_controls[port_name], values, strict=True):
            deck.append(f"{control_id},1,1,{float(value):.13e}")
    deck.extend([
        "*NODE PRINT,NSET=WJ_PORT_MOTION_MONITOR,FREQUENCY=1",
        "U,RF",
        "*NODE FILE,NSET=WJ_PORT_MOTION_MONITOR,FREQUENCY=1",
        "U,RF",
        "*NODE PRINT,NSET=WJ_CLEAT_POSE_NODES,FREQUENCY=1",
        "U",
        "*NODE FILE,NSET=WJ_CLEAT_POSE_NODES,FREQUENCY=1",
        "U",
        "*SECTION PRINT,SURFACE=WJ_RAIL_SECTION,NAME=WJ_RAIL_PORT",
        "SOF",
        "*SECTION PRINT,SURFACE=WJ_PRINCIPAL_SECTION,NAME=WJ_PRINCIPAL_PORT",
        "SOF",
        "*EL FILE,FREQUENCY=1",
        "S,E",
        "*EL PRINT,ELSET=CURRENT_ALL_ELEMENTS,TOTALS=ONLY,FREQUENCY=1",
        "ELSE,ELKE,EMAS,EVOL",
        "*CONTACT PRINT,FREQUENCY=1",
        "CDIS,CSTR,CELS,CNUM",
    ])
    contact_text = (bundle / "contact-fragment.inc").read_text().splitlines()
    pairs = []
    for i, line in enumerate(contact_text):
        if line.upper().startswith("*CONTACT PAIR,"):
            data = next(row.strip() for row in contact_text[i + 1:]
                        if row.strip() and not row.strip().startswith("**"))
            pairs.append(tuple(cell.strip() for cell in data.split(",")))
    if len(pairs) != 35:
        raise ValueError("the frozen contact manifest no longer has 35 contact pairs")
    for slave, master in pairs:
        deck.extend([f"*CONTACT PRINT,SLAVE={slave},MASTER={master},FREQUENCY=1",
                     "CF,CFN,CFS"])
    deck.append("*END STEP")
    deck_path.write_text("\n".join(deck) + "\n")
    case_report = {
        "schema": "wood_joint_current_port_motion_case/v2",
        "status": "FROZEN_CONTROLLED_PORT_MOTION_INPUT_NOT_EXECUTED",
        "case": case,
        "relative_joint_coordinate_mm": target.tolist(),
        "motion_rule": "rail and principal receive symmetric half motions about common joint datum; local port translations include rigid offset theta-cross-r; the six full-cap force-dual projections are controlled and all remaining cap deformation is free",
        "scale": {"translation_mm": generalized_motion_mm,
                  "rotation_rad": generalized_motion_mm / ROTATION_LENGTH_MM,
                  "interpretation": "numerical characterization input, not a measured demand"},
        "step_control": {
            "initial_increment": initial_increment,
            "total_time": step_total_time,
            "minimum_increment": 1e-6,
            "maximum_increment": maximum_increment,
            "amplitude_start_time_value": [0.0, 0.0],
            "amplitude_end_time_value": [step_total_time, step_endpoint_amplitude],
            "endpoint_relative_joint_coordinate_mm":
                (target * step_endpoint_amplitude).tolist(),
        },
        "ports": per_port,
        "cleat_boundary_or_constraint": False,
        "global_gauge_included": False,
        "boundary_conditions_only_on_port_control_nodes": True,
        "source_bundle_lock_sha256": sha(lock_path),
        "external_ports_sha256": sha(port_path),
        "nut_equation_dependent_set_intersection": bool(set(all_port_dependencies) & nut_dependent),
        "contact_surface_node_dependent_set_intersection": bool(
            {node for node, _dof in all_port_dependencies} & contact_nodes),
        "contact_surface_node_count_in_port_coordinate": sum(
            node in contact_nodes for port in per_port.values()
            for node in port["port_fit_node_ids"]),
        "cleat_pose_node_count": len(cleat_node_ids),
        "cleat_boundary_or_constraint": False,
        "port_section_output_names": ["WJ_RAIL_PORT", "WJ_PRINCIPAL_PORT"],
        "dependent_dof_collision_check": "six distinct physical variables per port; none reused from nut-coupling dependent terms",
        "limits": [
            "This is a prescribed relative section-motion experiment, not force-controlled service demand.",
            "The section equations control only the six full-cap projected coordinates; contact nodes remain independent and port nodes are not tied together.",
            "A static nonlinear run must accept equilibrium and pass reactions, contact and balance audits before any response interpretation.",
            "Current member end sections are remote analysis ports; transfer to complete frame demand remains unverified.",
        ],
    }
    source_snapshot_path.write_bytes(Path(__file__).read_bytes())
    case_report["artifacts_sha256"] = {
        "port-motion-controls.inp": sha(control_include),
        deck_path.name: sha(deck_path),
        source_snapshot_path.name: sha(source_snapshot_path),
    }
    report_path.write_text(json.dumps(case_report, indent=2) + "\n")
    frozen_inputs = {**lock["frozen_common_artifacts_sha256"],
                     **lock["supplemental_case_artifacts_sha256"]}
    frozen_inputs["input-freeze.json"] = lock["input_freeze_sha256"]
    frozen_inputs["bundle-lock.json"] = sha(lock_path)
    frozen_inputs.update(case_report["artifacts_sha256"])
    frozen_inputs[report_path.name] = sha(report_path)
    if frozen_inputs != {name: sha(bundle / name) for name in frozen_inputs}:
        raise ValueError("port-motion bundle input bytes changed while freezing")
    motion_lock = {
        "schema": "wood_joint_current_port_motion_lock/v2",
        "status": "FROZEN_CONTROLLED_PORT_MOTION_INPUTS",
        "case": case,
        "solver_image": lock["source_solver_image"],
        "source_solver_binary_sha256": lock["source_solver_binary_sha256"],
        "external_port_bundle_lock_sha256": sha(lock_path),
        "input_sha256": frozen_inputs,
        "native_execution": False,
        "mechanical_acceptance": False,
        "cleat_boundary_or_constraint": False,
        "global_gauge_included": False,
    }
    lock_output_path.write_text(json.dumps(motion_lock, indent=2) + "\n")
    return case_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--case", default="n_plus")
    parser.add_argument("--motion-mm", type=float, default=1.0)
    parser.add_argument("--initial-increment", type=float, default=0.01)
    parser.add_argument("--maximum-increment", type=float, default=0.05)
    parser.add_argument("--step-total-time", type=float, default=1.0)
    parser.add_argument("--step-endpoint-amplitude", type=float, default=1.0)
    args = parser.parse_args()
    result = prepare(args.bundle, args.case, args.motion_mm,
                     args.initial_increment, args.maximum_increment,
                     args.step_total_time, args.step_endpoint_amplitude)
    print(json.dumps({"status": result["status"], "case": result["case"],
                      "artifacts_sha256": result["artifacts_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
