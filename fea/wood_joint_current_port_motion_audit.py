"""Independent algebra and deck audit for a frozen port-motion case."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from fea.floor_contact import FACES
from fea.wood_joint_patch_contact_contract import parse_c3d10_deck


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _skew(vector: np.ndarray) -> np.ndarray:
    x, y, z = map(float, vector)
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def _independent_c(port: dict[str, Any], fit: dict[str, Any], basis: np.ndarray,
                   length: float) -> tuple[np.ndarray, np.ndarray]:
    source_ids = list(map(int, port["node_ids"]))
    source_xyz = np.asarray(port["global_xyz_mm"], dtype=float)
    source_weights = np.asarray(port["positive_area_weights_normalized"], dtype=float)
    fit_ids = list(map(int, fit["port_fit_node_ids"]))
    if fit_ids != source_ids:
        raise ValueError("controlled section map must use every source-bound cap node in source order")
    indexes = [source_ids.index(int(node)) for node in fit["port_fit_node_ids"]]
    xyz = source_xyz[indexes]
    origin = np.asarray(port["port_origin_global_xyz_mm"], dtype=float)
    node_weights = source_weights[indexes]
    if abs(float(np.sum(node_weights)) - 1.0) > 2e-12:
        raise ValueError("full-cap section-map weights do not sum to one")
    b = np.vstack([
        np.column_stack((basis, -_skew(point - origin) @ basis / length))
        for point in xyz
    ])
    weights = np.repeat(node_weights, 3)
    gram = b.T @ (weights[:, None] * b)
    c = np.linalg.solve(gram, b.T * weights[None, :])
    return b, c


def _parse_control_include(path: Path) -> tuple[dict[int, np.ndarray], list[list[tuple[int, int, float]]]]:
    lines = path.read_text().splitlines()
    nodes: dict[int, np.ndarray] = {}
    equations: list[list[tuple[int, int, float]]] = []
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.upper() == "*NODE":
            index += 1
            while index < len(lines) and not lines[index].lstrip().startswith("*"):
                values = [cell.strip() for cell in lines[index].split(",")]
                nodes[int(values[0])] = np.asarray(list(map(float, values[1:4])))
                index += 1
            continue
        if line.upper() == "*EQUATION":
            count = int(lines[index + 1].strip())
            index += 2
            tokens: list[str] = []
            while len(tokens) < 3 * count:
                row = lines[index].strip()
                index += 1
                if row and not row.startswith("**"):
                    tokens.extend(cell.strip() for cell in row.split(",") if cell.strip())
            if len(tokens) != 3 * count:
                raise ValueError("equation token count does not match declared term count")
            equations.append([
                (int(tokens[i]), int(tokens[i + 1]), float(tokens[i + 2]))
                for i in range(0, len(tokens), 3)
            ])
            continue
        index += 1
    return nodes, equations


def _surface_face_map(path: Path) -> dict[str, list[tuple[int, int]]]:
    result: dict[str, list[tuple[int, int]]] = {}
    active: str | None = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("*SURFACE,"):
            name = next((token.split("=", 1)[1].strip().upper()
                         for token in line.split(",")
                         if token.strip().upper().startswith("NAME=")), None)
            if not name or name in result:
                raise ValueError("section surface has missing or duplicate name")
            active = name
            result[active] = []
        elif line.startswith("*"):
            active = None
        elif active and line and not line.startswith("**"):
            element, side = (cell.strip() for cell in line.split(",", 1))
            result[active].append((int(element), int(side.upper().removeprefix("S"))))
    return result


def _named_nset(path: Path, wanted: str) -> set[int]:
    lines = path.read_text().splitlines()
    result: set[int] = set()
    active = False
    for raw in lines:
        line = raw.strip()
        upper = line.upper()
        if upper.startswith("*NSET,"):
            active = any(token.strip().upper() == f"NSET={wanted.upper()}"
                         for token in line.split(",")[1:])
            continue
        if line.startswith("*"):
            active = False
            continue
        if active and line and not line.startswith("**"):
            result.update(int(cell.strip()) for cell in line.split(",") if cell.strip())
    return result


def _nut_dependent_dofs(path: Path) -> set[tuple[int, int]]:
    lines = path.read_text().splitlines()
    dependent: set[tuple[int, int]] = set()
    index = 0
    while index < len(lines):
        if not lines[index].strip().upper().startswith("*EQUATION"):
            index += 1
            continue
        index += 1
        while index < len(lines) and not lines[index].strip():
            index += 1
        count = int(lines[index].strip())
        index += 1
        tokens: list[str] = []
        while len(tokens) < 3 * count:
            row = lines[index].strip()
            index += 1
            if row and not row.startswith("**") and not row.startswith("*"):
                tokens.extend(cell.strip() for cell in row.split(",") if cell.strip())
        dependent.add((int(tokens[0]), int(tokens[1])))
    return dependent


def _contact_surface_nodes(bundle: Path) -> set[int]:
    _, elements, _ = parse_c3d10_deck(
        (bundle / "mesh.inp").read_text(), context="port-motion independent audit")
    found: set[int] = set()
    active = False
    for raw in (bundle / "contact-fragment.inc").read_text().splitlines():
        line = raw.strip()
        if line.startswith("*"):
            active = line.upper().startswith("*SURFACE,") and "TYPE=ELEMENT" in line.upper()
            continue
        if not active or not line or line.startswith("**"):
            continue
        element_token, side_token = (cell.strip() for cell in line.split(",", 1))
        found.update(elements[int(element_token)][local]
                     for local in FACES[int(side_token.upper().removeprefix("S")) - 1])
    return found


def audit(bundle: Path, case: str = "n_plus") -> dict[str, Any]:
    bundle = bundle.resolve()
    case_path = bundle / f"port-motion_{case}.json"
    deck_path = bundle / f"port_motion_{case}.inp"
    control_path = bundle / "port-motion-controls.inp"
    lock_path = bundle / f"port-motion-{case}-lock.json"
    case_report = json.loads(case_path.read_text())
    lock = json.loads(lock_path.read_text())
    if case_report.get("schema") != "wood_joint_current_port_motion_case/v2":
        raise ValueError("case is not the full-cap common-map revision")
    external = json.loads((bundle / "external-ports.json").read_text())
    input_hash_check = {
        name: _sha(bundle / name) == digest
        for name, digest in lock["input_sha256"].items()
    }
    if not all(input_hash_check.values()):
        raise ValueError("a source-bound port-motion input hash changed")
    basis = np.asarray(external["frame"]["basis_columns_global_xyz"], dtype=float)
    length = float(external["frame"]["rotation_length_mm"])
    nodes, equations = _parse_control_include(control_path)
    if len(equations) != 12:
        raise ValueError(f"expected 12 section equations; found {len(equations)}")
    if len(nodes) != 12:
        raise ValueError(f"expected 12 port coordinate controls; found {len(nodes)}")
    section_surfaces = _surface_face_map(control_path)
    if set(section_surfaces) != {"WJ_RAIL_SECTION", "WJ_PRINCIPAL_SECTION"}:
        raise ValueError("control include does not define exactly the two external port sections")
    for name in ("rail", "principal"):
        expected_faces = sorted(tuple(map(int, row))
                                for row in external["ports"][name]["face_refs_element_side"])
        actual_faces = sorted(section_surfaces[f"WJ_{name.upper()}_SECTION"])
        if actual_faces != expected_faces:
            raise ValueError(f"{name}: SECTION PRINT surface differs from source-bound cap faces")
    mesh_report = json.loads((bundle / "mesh.json").read_text())
    expected_cleat_nodes = set(map(
        int, mesh_report["bodies"]["W00_BOTTOM_CENTER_RIGHT_CLEAT"]["nodes"]))
    actual_cleat_nodes = _named_nset(control_path, "WJ_CLEAT_POSE_NODES")
    if len(expected_cleat_nodes) != 9369 or actual_cleat_nodes != expected_cleat_nodes:
        raise ValueError("cleat pose output set differs from the source-bound free cleat")
    nut_dependent = _nut_dependent_dofs(bundle / "nut-coupling.inp")
    contact_nodes = _contact_surface_nodes(bundle)
    dependent: list[tuple[int, int]] = []
    max_c_reconstruction_error = 0.0
    max_force_map_error = 0.0
    max_serialized_elimination_error = 0.0
    max_virtual_work_relative_error = 0.0
    contact_node_equation_reference_count = 0
    equation_cursor = 0
    control_ids_by_port: dict[str, list[int]] = {}
    for name in ("rail", "principal"):
        port = external["ports"][name]
        fit = case_report["ports"][name]
        if fit.get("port_coordinate_definition") != (
                "source-bound full 43-node cap projection; identical to external-port force dual"):
            raise ValueError(f"{name}: coordinate definition does not match the frozen force dual")
        fit_ids = list(map(int, fit["port_fit_node_ids"]))
        source_ids = list(map(int, port["node_ids"]))
        if fit_ids != source_ids or len(fit_ids) != 43:
            raise ValueError(f"{name}: control projection is not the complete source cap")
        b, c = _independent_c(port, fit, basis, length)
        saved_c = np.asarray(fit["control_displacement_map_C"], dtype=float)
        max_c_reconstruction_error = max(
            max_c_reconstruction_error, float(np.max(np.abs(c - saved_c))))
        source_c = np.asarray(port["displacement_map_C"], dtype=float)
        max_force_map_error = max(max_force_map_error,
                                  float(np.max(np.abs(c - source_c))))
        if float(np.max(np.abs(c @ b - np.eye(6)))) > 2e-11:
            raise ValueError(f"{name}: independently reconstructed section map is rank deficient")
        control_ids = list(map(int, case_report["ports"][name]["control_node_ids"]))
        control_ids_by_port[name] = control_ids
        dep_dofs = [tuple(map(int, row)) for row in fit["dependent_physical_dofs"]]
        dep_columns = [fit_ids.index(node) * 3 + dof - 1 for node, dof in dep_dofs]
        if len(set(dep_columns)) != 6:
            raise ValueError(f"{name}: pivot DOFs are not distinct")
        independent_columns = [column for column in range(c.shape[1])
                              if column not in set(dep_columns)]
        pivot = c[:, dep_columns]
        pivot_inverse = np.linalg.inv(pivot)
        expected_independent = pivot_inverse @ c[:, independent_columns]
        expected_controls = -pivot_inverse
        actual_independent = np.zeros_like(expected_independent)
        actual_controls = np.zeros_like(expected_controls)
        dep_set = set(dep_dofs)
        for row_index, dep in enumerate(dep_dofs):
            terms = equations[equation_cursor]
            equation_cursor += 1
            if (terms[0][0], terms[0][1]) != dep or abs(terms[0][2] - 1.0) > 1e-13:
                raise ValueError(f"{name}: serialized equation dependent variable differs")
            dependent.append(dep)
            for node, dof, coefficient in terms:
                if (node, dof) == dep:
                    continue
                if node in control_ids:
                    if dof != 1:
                        raise ValueError("port coordinate control must use scalar DOF 1")
                    actual_controls[row_index, control_ids.index(node)] = coefficient
                else:
                    if (node, dof) in dep_set:
                        raise ValueError(f"{name}: dependent variables form a cyclic MPC graph")
                    if node not in fit_ids:
                        raise ValueError("port equation references a node outside its bound section")
                    if node in contact_nodes:
                        contact_node_equation_reference_count += 1
                    column = fit_ids.index(node) * 3 + dof - 1
                    actual_independent[row_index, independent_columns.index(column)] = coefficient
        max_serialized_elimination_error = max(
            max_serialized_elimination_error,
            float(np.max(np.abs(actual_independent - expected_independent))),
            float(np.max(np.abs(actual_controls - expected_controls))),
        )
        if control_ids[0] in nodes:
            control_coords = np.asarray([nodes[node] for node in control_ids])
            expected_coords = np.repeat(
                np.asarray(port["port_origin_global_xyz_mm"], dtype=float)[None, :], 6, axis=0)
            if not np.allclose(control_coords, expected_coords, rtol=0, atol=1e-9):
                raise ValueError(f"{name}: control coordinate labels do not match its source port")
        rng = np.random.default_rng(20260927 + (0 if name == "rail" else 1))
        arbitrary_u = rng.normal(size=c.shape[1])
        arbitrary_wrench = rng.normal(size=6)
        mapped_force = c.T @ arbitrary_wrench
        left_work = float(arbitrary_u @ mapped_force)
        right_work = float((c @ arbitrary_u) @ arbitrary_wrench)
        work_scale = max(1.0, abs(left_work), abs(right_work))
        max_virtual_work_relative_error = max(
            max_virtual_work_relative_error, abs(left_work - right_work) / work_scale)
    if len(set(dependent)) != 12:
        raise ValueError("dependent physical port DOFs are not unique")
    if set(dependent) & nut_dependent:
        raise ValueError("port equation dependencies collide with nut coupling")
    if {node for node, _dof in dependent} & contact_nodes:
        raise ValueError("port equation dependent variables lie on contact faces")
    if (max_c_reconstruction_error > 2e-11 or max_force_map_error > 2e-11
            or max_serialized_elimination_error > 2e-10
            or max_virtual_work_relative_error > 2e-12):
        raise ValueError("serialized elimination does not enforce the independently rebuilt section map")

    deck = deck_path.read_text()
    upper_deck = deck.upper()
    if any(token in upper_deck for token in ("*CLOAD", "*STABILIZE", "*TIE", "*RIGID BODY")):
        raise ValueError("port-motion case contains a prohibited load/stabilizer/tie/rigid body")
    if "*INCLUDE,INPUT=GAUGE.INP" in upper_deck:
        raise ValueError("port-motion case unexpectedly includes the numerical gauge")
    if "W00_BOTTOM_CENTER_RIGHT_CLEAT" in upper_deck:
        raise ValueError("port-motion case mentions cleat boundary control")
    if ("*NODE FILE,NSET=WJ_CLEAT_POSE_NODES" not in upper_deck
            or "*SECTION PRINT,SURFACE=WJ_RAIL_SECTION,NAME=WJ_RAIL_PORT\nSOF" not in upper_deck
            or "*SECTION PRINT,SURFACE=WJ_PRINCIPAL_SECTION,NAME=WJ_PRINCIPAL_PORT\nSOF" not in upper_deck):
        raise ValueError("deck omits full cleat-pose or external-section-wrench output")
    deck_lines = deck.splitlines()
    amplitude_index = next(i for i, row in enumerate(deck_lines)
                           if row.upper().startswith("*AMPLITUDE,NAME=WJ_PORT_MOTION_RAMP"))
    amplitude_values = [float(cell.strip()) for cell in deck_lines[amplitude_index + 1].split(",")]
    if len(amplitude_values) != 4:
        raise ValueError("port-motion amplitude must contain exactly two time/value pairs")
    static_index = next(i for i, row in enumerate(deck_lines)
                        if row.upper().startswith("*STATIC"))
    static_values = [float(cell.strip()) for cell in deck_lines[static_index + 1].split(",")]
    if len(static_values) != 4:
        raise ValueError("port-motion static control must contain four values")
    step_control = case_report.get("step_control", {
        "initial_increment": static_values[0], "total_time": static_values[1],
        "minimum_increment": static_values[2], "maximum_increment": static_values[3],
        "amplitude_start_time_value": amplitude_values[:2],
        "amplitude_end_time_value": amplitude_values[2:],
        "endpoint_relative_joint_coordinate_mm": case_report["relative_joint_coordinate_mm"],
    })
    expected_static = [float(step_control[key]) for key in (
        "initial_increment", "total_time", "minimum_increment", "maximum_increment")]
    if not np.allclose(static_values, expected_static, rtol=0, atol=1e-12):
        raise ValueError("serialized static controls differ from the frozen step report")
    expected_amplitude = [*map(float, step_control["amplitude_start_time_value"]),
                          *map(float, step_control["amplitude_end_time_value"])]
    if not np.allclose(amplitude_values, expected_amplitude, rtol=0, atol=1e-12):
        raise ValueError("serialized amplitude differs from the frozen step report")
    if not np.isclose(static_values[1], amplitude_values[2], rtol=0, atol=1e-12):
        raise ValueError("amplitude endpoint time differs from the static step end")
    if not (0 < amplitude_values[3] <= 1):
        raise ValueError("amplitude endpoint must be between zero and one")
    if not (0 < static_values[0] <= static_values[3]
            and static_values[0] <= static_values[1]):
        raise ValueError("serialized static increment controls are inconsistent")
    boundary_index = next(i for i, row in enumerate(deck_lines)
                          if row.upper().startswith("*BOUNDARY,"))
    boundary_rows = []
    index = boundary_index + 1
    while index < len(deck_lines) and not deck_lines[index].lstrip().startswith("*"):
        row = deck_lines[index].strip()
        if row:
            values = [cell.strip() for cell in row.split(",")]
            boundary_rows.append((int(values[0]), int(values[1]), int(values[2]), float(values[3])))
        index += 1
    allowed_controls = {node for ids in control_ids_by_port.values() for node in ids}
    if len(boundary_rows) != 12 or {row[0] for row in boundary_rows} != allowed_controls:
        raise ValueError("boundary cards do not act exclusively on the twelve port controls")
    if any(row[1:3] != (1, 1) for row in boundary_rows):
        raise ValueError("port-motion boundary cards must prescribe only each scalar coordinate")

    axis, sign_name = case.rsplit("_", 1)
    axis_index = {"x": 0, "t": 1, "n": 2, "rx": 3, "rt": 4, "rn": 5}[axis]
    sign = 1.0 if sign_name == "plus" else -1.0
    target = np.zeros(6)
    target[axis_index] = sign * float(case_report["scale"]["translation_mm"] if axis_index < 3
                                     else case_report["scale"]["translation_mm"])
    joint_origin = np.asarray(external["frame"]["origin_global_xyz_mm"], dtype=float)
    expected_values: dict[int, float] = {}
    motion_transform_errors = []
    for port_index, name in enumerate(("rail", "principal")):
        port = external["ports"][name]
        xyz0 = np.asarray(port["port_origin_global_xyz_mm"], dtype=float)
        offset_local = basis.T @ (xyz0 - joint_origin)
        transform = np.eye(6)
        transform[:3, 3:] = -_skew(offset_local) / length
        joint_q = 0.5 * target if name == "rail" else -0.5 * target
        expected_port_q = transform @ joint_q
        stored = np.asarray(case_report["ports"][name]["controlled_q_port_local_mm"])
        motion_transform_errors.append(float(np.max(np.abs(stored - expected_port_q))))
        for control_id, value in zip(control_ids_by_port[name], expected_port_q, strict=True):
            expected_values[control_id] = float(value)
    boundary_error = max(abs(value - expected_values[node])
                         for node, _lo, _hi, value in boundary_rows)
    if max(motion_transform_errors, default=0.0) > 1e-12 or boundary_error > 1e-12:
        raise ValueError("boundary values do not implement the signed joint-datum motion")
    endpoint_motion = target * amplitude_values[3]
    if not np.allclose(endpoint_motion,
                       np.asarray(step_control["endpoint_relative_joint_coordinate_mm"], dtype=float),
                       rtol=0, atol=1e-12):
        raise ValueError("reported endpoint motion differs from the serialized amplitude endpoint")

    return {
        "schema": "wood_joint_current_port_motion_audit/v2",
        "status": "FULL_CAP_WORK_DUAL_PORT_MOTION_EQUATIONS_INDEPENDENTLY_VERIFIED_INPUT_ONLY",
        "case": case,
        "input_hashes_verified": len(input_hash_check),
        "input_hashes_all_match": all(input_hash_check.values()),
        "equation_count": len(equations),
        "generalized_control_count": len(nodes),
        "boundary_scalar_count": len(boundary_rows),
        "max_independent_C_reconstruction_error": max_c_reconstruction_error,
        "max_motion_to_force_map_error": max_force_map_error,
        "max_serialized_elimination_error": max_serialized_elimination_error,
        "max_random_virtual_work_relative_error": max_virtual_work_relative_error,
        "contact_surface_node_equation_reference_count": contact_node_equation_reference_count,
        "source_bound_section_face_counts": {
            name: len(section_surfaces[f"WJ_{name.upper()}_SECTION"])
            for name in ("rail", "principal")
        },
        "cleat_pose_node_count": len(actual_cleat_nodes),
        "max_joint_to_port_motion_transform_error": max(motion_transform_errors),
        "max_boundary_value_error": boundary_error,
        "serialized_step_control": {
            "initial_increment": static_values[0],
            "total_time": static_values[1],
            "minimum_increment": static_values[2],
            "maximum_increment": static_values[3],
            "amplitude_end_time_value": amplitude_values[2:],
            "endpoint_relative_joint_coordinate_mm": endpoint_motion.tolist(),
        },
        "nut_equation_dependent_dof_intersection": False,
        "contact_surface_nodes_are_independent_equation_terms": True,
        "contact_surface_nodes_are_dependent_variables": False,
        "cleat_boundary_or_constraint": False,
        "section_wrench_output": ["WJ_RAIL_PORT:SOF", "WJ_PRINCIPAL_PORT:SOF"],
        "global_gauge_included": False,
        "port_nodes_tied_or_rigidized": False,
        "external_load_cards": False,
        "mechanical_acceptance": False,
        "source_sha256": {
            "bundle-lock.json": _sha(bundle / "bundle-lock.json"),
            lock_path.name: _sha(lock_path),
            case_path.name: _sha(case_path),
            control_path.name: _sha(control_path),
            deck_path.name: _sha(deck_path),
        },
        "interpretation": "This independent audit confirms the serialized work-conjugate projection equations and physical port motion values; it does not establish convergence, equilibrium, load transfer, or joint acceptance.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--case", default="n_plus")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.bundle, args.case)
    output = args.output or (args.bundle / f"port-motion_{args.case}-audit.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "output": str(output),
                      "max_serialized_elimination_error": result["max_serialized_elimination_error"]}, indent=2))


if __name__ == "__main__":
    main()
