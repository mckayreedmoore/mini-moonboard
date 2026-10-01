#!/usr/bin/env python3
"""Check parent-exported Code_Aster A09 actual-map nodal histories.

This checker performs no solver calls. It validates the frozen source and
generated inputs, maps MED nodes by exact source coordinates while resolving
the coincident controls through MED node groups, then checks every physical
node/state against the small-motion Newmark oracle. Physical kinetic energy is
recomputed from the pinned 17.4 TETRA10 FPG15 scalar mass matrices.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Any, Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "fea/code_aster_trial/mass_reference"))
from aster_tetra10_mass import FPG15_POINTS, FPG15_WEIGHTS, tetra10_mass_matrix  # noqa: E402

EVIDENCE = ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27"
READINESS_PATH = EVIDENCE / "actual-map-readiness.json"
CASE_NAMES = ("direct", "mapped_no_carrier", "mapped_carrier")
QUANTITIES = ("DEPL", "VITE", "ACCE")
VECTORS = ("DX", "DY", "DZ")
SOURCE_DOFS = {1: "DX", 2: "DY", 3: "DZ"}
CASE_PREFIX = {"direct": "D", "mapped_no_carrier": "M", "mapped_carrier": "C"}
PIVOT = np.array((134.5, 1.178456090256, 410.856889078727), dtype=float)
DENSITY = 7.85e-9
MASS_REVIEW_REFERENCE_TONNE = 4.208482861852778e-05
IYY_REVIEW_REFERENCE_TONNE_MM2 = 0.1538313026661648
# MED serializes the exact source ASCII coordinates through Code_Aster's
# floating-point mesh representation. This is an output-serialization bound;
# source .mail coordinates remain pinned and exact, and it does not alter the
# parent-frozen mechanical acceptance bounds.
MED_COORD_SERIALIZATION_ATOL_MM = 1.0e-10


class CheckError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckError(f"cannot read JSON {path}: {exc}") from exc


def sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise CheckError(f"cannot read {path}: {exc}") from exc


def number(value: Any, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise CheckError(f"{label} is not numeric: {value!r}") from exc
    require(math.isfinite(result), f"{label} is not finite")
    return result


def source_equations(path: Path) -> tuple[tuple[tuple[int, int, str], ...], ...]:
    lines = path.read_text().splitlines()
    equations = []
    index = 0
    while index < len(lines):
        if lines[index].strip().upper() != "*EQUATION":
            index += 1
            continue
        index += 1
        require(index < len(lines), "truncated *EQUATION header")
        nterms = int(lines[index].strip())
        index += 1
        fields: list[str] = []
        while len(fields) < 3 * nterms:
            require(index < len(lines), "truncated *EQUATION row")
            row = lines[index].strip()
            require(not row.startswith("*"), "Abaqus keyword inside equation row")
            fields.extend(item.strip() for item in row.split(",") if item.strip())
            index += 1
        require(len(fields) == 3 * nterms, "unexpected extra equation fields")
        equations.append(tuple((int(fields[i]), int(fields[i + 1]), fields[i + 2])
                               for i in range(0, len(fields), 3)))
    require(len(equations) >= 6, f"expected six source rows, found {len(equations)}")
    return tuple(equations[:6])


def equation_digest(equations: Iterable[Iterable[tuple[int, int, str]]]) -> str:
    serialized = "\n".join(";".join(f"{node},{dof},{coefficient}"
                                     for node, dof, coefficient in row)
                            for row in equations)
    return hashlib.sha256(serialized.encode()).hexdigest()


def parse_aster_groups(mail_path: Path, section_name: str) -> dict[str, tuple[str, ...]]:
    lines = mail_path.read_text().splitlines()
    groups: dict[str, tuple[str, ...]] = {}
    in_section = False
    current: list[str] = []

    def finish() -> None:
        nonlocal current
        if current:
            name, *members = current[0].split()
            require(name not in groups, f"duplicate {section_name} group {name} in {mail_path}")
            groups[name] = tuple(members + [item for row in current[1:] for item in row.split()])
        current = []

    for raw in lines:
        line = raw.strip()
        if line == "FINSF":
            if in_section:
                finish()
            in_section = False
            continue
        if line in ("GROUP_MA", "GROUP_NO"):
            if in_section:
                finish()
            in_section = line == section_name
            continue
        if in_section and line:
            current.append(line)
    if in_section:
        finish()
    return groups


def get_map_ast(comm_path: Path) -> tuple[list[ast.Call], str]:
    text = comm_path.read_text()
    try:
        tree = ast.parse(text, filename=str(comm_path))
    except SyntaxError as exc:
        raise CheckError(f"generated command file is not valid Python: {comm_path}: {exc}") from exc
    found = None
    for statement in tree.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "map_equations"
            for target in statement.targets
        ):
            found = statement.value
            break
    require(isinstance(found, (ast.Tuple, ast.List)), f"map_equations missing/invalid in {comm_path}")
    rows = []
    for row in found.elts:
        require(isinstance(row, ast.Call), f"map row is not an _F call in {comm_path}")
        rows.append(row)
    return rows, text


def keyword_value(call: ast.Call, key: str) -> ast.expr:
    for item in call.keywords:
        if item.arg == key:
            return item.value
    raise CheckError(f"map equation lacks {key}")


def tuple_values(value: ast.expr, label: str) -> list[Any]:
    require(isinstance(value, (ast.Tuple, ast.List)), f"{label} is not a tuple/list")
    result = []
    for item in value.elts:
        try:
            result.append(ast.literal_eval(item))
        except (ValueError, TypeError) as exc:
            raise CheckError(f"{label} has a nonliteral item") from exc
    return result


def verify_source_map_and_comm(oracle: dict[str, Any], input_root: Path,
                               input_manifest: dict[str, Any]) -> dict[str, Any]:
    source_files = oracle["source_files"]
    for name, record in source_files.items():
        path = Path(record["path"])
        require(sha256(path) == record["sha256"], f"pinned source hash changed: {name}")
    coupling = Path(source_files["nut-coupling.inp"]["path"])
    rows = source_equations(coupling)
    require([len(row) for row in rows] == [754] * 6, "source A00 first six rows are not 754 terms each")
    digest = equation_digest(rows)
    require(digest == oracle["source_map"]["exact_ordered_term_digest_sha256"],
            "oracle source-map term digest differs from pinned A09 source")

    mapped_audits = {}
    export_overlays = {}
    mail_geometry = {}
    artifacts = input_manifest["generated_artifacts"]
    source_nodes = set()
    source_force_rows = oracle["mass_reference"]["load_vector_final_tonne_mm_s2"]
    expected_force_data = [(f"N{int(row[0])}", *(float(value) for value in row[1:4]))
                           for row in source_force_rows]
    for case in CASE_NAMES:
        folder = input_root / case
        comm_path = folder / f"{case}.comm"
        mail_path = folder / f"{case}.mail"
        export_path = folder / f"{case}.export"
        for suffix, path in (("comm", comm_path), ("mail", mail_path)):
            require(sha256(path) == artifacts[case][suffix],
                    f"generated {case}.{suffix} differs from the input manifest")
        base_export = HERE / "input" / case / f"{case}.export"
        base_export_lines = [line.strip() for line in base_export.read_text().splitlines() if line.strip()]
        actual_export_lines = [line.strip() for line in export_path.read_text().splitlines() if line.strip()]
        require(all(line.split()[0] in {"P", "A", "F"} for line in actual_export_lines),
                f"{case}.export contains a non-P/A/F line")
        if sha256(export_path) == artifacts[case]["export"]:
            export_overlays[case] = {"exact_manifest_match": True, "time_limit": None}
        else:
            require(len(actual_export_lines) == len(base_export_lines),
                    f"{case}.export resource overlay changed line count")
            changed = []
            for before, after in zip(base_export_lines, actual_export_lines):
                if before == after:
                    continue
                b, a = before.split(), after.split()
                require(len(b) == 3 and len(a) == 3 and b[:2] == ["P", "time_limit"] and
                        a[:2] == ["P", "time_limit"],
                        f"{case}.export changed a line other than P time_limit")
                require(int(a[2]) >= int(b[2]), f"{case}.export lowered its time limit")
                changed.append((int(b[2]), int(a[2])))
            require(len(changed) == 1, f"{case}.export overlay must change exactly one time limit")
            export_overlays[case] = {"exact_manifest_match": False,
                                     "base_time_limit_seconds": changed[0][0],
                                     "runtime_time_limit_seconds": changed[0][1],
                                     "only_allowed_resource_line_changed": True}
        mail_geometry[case] = audit_mail_geometry(mail_path, oracle["cases"][case], oracle)
        try:
            comm_tree = ast.parse(comm_path.read_text(), filename=str(comm_path))
        except SyntaxError as exc:
            raise CheckError(f"generated command file is not valid Python: {comm_path}: {exc}") from exc
        force_assignment = next((statement for statement in comm_tree.body
                                 if isinstance(statement, ast.Assign) and any(
                                     isinstance(target, ast.Name) and target.id == "force_data"
                                     for target in statement.targets)), None)
        require(force_assignment is not None and isinstance(force_assignment.value, (ast.Tuple, ast.List)),
                f"{case} does not contain literal physical force_data")
        actual_force_data = []
        for force_row in force_assignment.value.elts:
            values = tuple_values(force_row, f"{case} force_data row")
            require(len(values) == 4, f"{case} force_data row does not have node+xyz values")
            actual_force_data.append((str(values[0]), *(float(value) for value in values[1:])))
        require(actual_force_data == expected_force_data,
                f"{case} physical force vector differs from shared pinned FPG15 M*a input")
        source_group_map = parse_aster_groups(mail_path, "GROUP_NO")
        if case == "direct":
            continue
        calls, text = get_map_ast(comm_path)
        require(len(calls) == 6, f"{case} does not contain exactly six actual A00 map rows")
        comm_tree = ast.parse(text, filename=str(comm_path))
        kin_statement = next((statement for statement in comm_tree.body
                              if isinstance(statement, ast.Assign) and any(
                                  isinstance(target, ast.Name) and target.id == "KIN"
                                  for target in statement.targets)), None)
        require(kin_statement is not None and isinstance(kin_statement.value, ast.Call),
                f"{case} has no KIN mechanical load assignment")
        liaison = next((item.value for item in kin_statement.value.keywords if item.arg == "LIAISON_DDL"), None)
        require(liaison is not None, f"{case} KIN does not attach LIAISON_DDL")
        liaison_names = {node.id for node in ast.walk(liaison) if isinstance(node, ast.Name)}
        require("map_equations" in liaison_names,
                f"{case} KIN does not use the preserved actual A00 map equations")
        require(("carrier_equations" in liaison_names) == (case == "mapped_carrier"),
                f"{case} KIN has incorrect carrier-equation inclusion")
        row_reports = []
        for row_index, (call, source_row) in enumerate(zip(calls, rows)):
            if any(item.arg == "GROUP_NO" for item in call.keywords):
                group_names = tuple_values(keyword_value(call, "GROUP_NO"), f"{case} row {row_index} GROUP_NO")
                names = []
                for group in group_names:
                    require(group in source_group_map, f"{case} map references unknown singleton group {group}")
                    members = source_group_map[group]
                    require(len(members) == 1, f"{case} map group {group} is not a singleton node group")
                    names.append(members[0])
                generated_nodes = names
            else:
                generated_nodes = tuple_values(keyword_value(call, "NOEUD"), f"{case} row {row_index} NOEUD")
            generated_ddls = tuple_values(keyword_value(call, "DDL"), f"{case} row {row_index} DDL")
            generated_coeffs = tuple_values(keyword_value(call, "COEF_MULT"), f"{case} row {row_index} COEF_MULT")
            expected_nodes = [f"N{node}" for node, _, _ in source_row]
            expected_ddls = [SOURCE_DOFS[dof] for _, dof, _ in source_row]
            require(generated_nodes == expected_nodes,
                    f"{case} row {row_index} changes ordered source node terms")
            require(generated_ddls == expected_ddls,
                    f"{case} row {row_index} changes ordered source DOF terms")
            require(len(generated_coeffs) == len(source_row),
                    f"{case} row {row_index} coefficient count changed")
            coefficient_segments = [
                ast.get_source_segment(text, item).strip()
                for item in keyword_value(call, "COEF_MULT").elts
            ]
            require(coefficient_segments == [coefficient for _, _, coefficient in source_row],
                    f"{case} row {row_index} does not preserve coefficient tokens exactly")
            co_imp = ast.literal_eval(keyword_value(call, "COEF_IMPO"))
            require(float(co_imp) == 0.0, f"{case} row {row_index} changes the zero right-hand side")
            row_reports.append({"source_terms": len(source_row), "node_order_exact": True,
                               "dof_order_exact": True, "coefficient_tokens_exact": True,
                               "zero_rhs_exact": True})
        mapped_audits[case] = row_reports
    return {"source_sha256_verified": True, "source_term_digest_sha256": digest,
            "source_rows": [len(row) for row in rows], "generated_rows": mapped_audits,
            "source_mesh_geometry_audit": mail_geometry,
            "export_resource_overlays": export_overlays}


def parse_source_mesh(mesh_path: Path) -> tuple[dict[int, tuple[float, float, float]],
                                                dict[int, tuple[int, ...]]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    section = ""
    pending: list[str] = []

    def finish_element() -> None:
        nonlocal pending
        if pending:
            require(len(pending) == 11, f"unexpected C3D10 field count {len(pending)}")
            elem, *connectivity = (int(value) for value in pending)
            elements[elem] = tuple(connectivity)
            pending = []

    for raw in mesh_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if section == "ELEMENT":
                finish_element()
            upper = line.upper().replace(" ", "")
            if upper == "*NODE":
                section = "NODE"
            elif upper.startswith("*ELEMENT,TYPE=C3D10"):
                section = "ELEMENT"
            else:
                section = ""
            continue
        if section == "NODE":
            fields = [part.strip() for part in line.split(",")]
            require(len(fields) == 4, "malformed pinned source node row")
            nodes[int(fields[0])] = tuple(float(x) for x in fields[1:4])
        elif section == "ELEMENT":
            pending.extend(part.strip() for part in line.split(",") if part.strip())
            if len(pending) >= 11:
                finish_element()
    if section == "ELEMENT":
        finish_element()
    require(nodes and elements, "no TETRA10 nodes/elements parsed from pinned source")
    return nodes, elements


def source_node_tokens(path: Path, wanted: set[int]) -> dict[int, tuple[str, str, str]]:
    result: dict[int, tuple[str, str, str]] = {}
    in_nodes = False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            in_nodes = line.upper() == "*NODE"
            continue
        if in_nodes:
            fields = [part.strip() for part in line.split(",")]
            if len(fields) == 4 and int(fields[0]) in wanted:
                result[int(fields[0])] = (fields[1], fields[2], fields[3])
    return result


def audit_mail_geometry(mail_path: Path, case_record: dict[str, Any], oracle: dict[str, Any]) -> dict[str, Any]:
    """Check ASTER mesh coordinates/connectivity against pinned Abaqus source text."""
    source_files = oracle["source_files"]
    source_mesh_path = Path(source_files["mesh.inp"]["path"])
    coupling_path = Path(source_files["nut-coupling.inp"]["path"])
    control_ids = set(int(value) for value in case_record["control_node_ids"])
    body_ids = set(int(value) for value in case_record["physical_node_ids"] + case_record["carrier_node_ids"])
    required_ids = body_ids | control_ids
    node_text = source_node_tokens(source_mesh_path, body_ids)
    node_text.update(source_node_tokens(coupling_path, control_ids))
    require(set(node_text) == required_ids, f"{mail_path} source node text does not cover all input nodes")

    coords: dict[str, tuple[str, str, str]] = {}
    elements: dict[str, tuple[str, ...]] = {}
    point_elements: dict[str, str] = {}
    section = ""
    for raw in mail_path.read_text().splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == "FINSF":
            section = ""
            continue
        if line in {"COOR_3D", "TETRA10", "POI1"}:
            section = line
            continue
        if line.startswith("*") or line in {"TITRE", "FIN"}:
            section = ""
            continue
        fields = line.split()
        if section == "COOR_3D":
            require(len(fields) == 4, f"malformed COOR_3D row in {mail_path}")
            coords[fields[0]] = tuple(fields[1:4])
        elif section == "TETRA10":
            require(len(fields) == 11, f"malformed TETRA10 row in {mail_path}")
            elements[fields[0]] = tuple(fields[1:])
        elif section == "POI1":
            require(len(fields) == 2, f"malformed POI1 row in {mail_path}")
            point_elements[fields[0]] = fields[1]
    expected_names = {f"N{node}" for node in required_ids}
    require(set(coords) == expected_names, f"{mail_path} source node names/count changed")
    for node, source_tokens in node_text.items():
        require(coords[f"N{node}"] == source_tokens,
                f"{mail_path} coordinate text changed for source node N{node}")

    source_nodes, source_elements = parse_source_mesh(source_mesh_path)
    del source_nodes
    expected_element_ids = [int(value) for value in case_record["mesh_element_order_source_ids"]]
    require(set(elements) == {f"M{element}" for element in expected_element_ids},
            f"{mail_path} element names/count changed")
    for element in expected_element_ids:
        expected_connectivity = tuple(f"N{node}" for node in source_elements[element])
        require(elements[f"M{element}"] == expected_connectivity,
                f"{mail_path} TETRA10 source connectivity/order changed for M{element}")
    expected_points = {f"P{node}": f"N{node}" for node in control_ids}
    require(point_elements == expected_points, f"{mail_path} POI1 control nodes changed")

    groups_no = parse_aster_groups(mail_path, "GROUP_NO")
    expected_physical = {f"N{node}" for node in case_record["physical_node_ids"]}
    require(set(groups_no.get("PHYS_NODES", ())) == expected_physical,
            f"{mail_path} PHYS_NODES membership differs from source body")
    carrier_ids = case_record["carrier_node_ids"]
    if carrier_ids:
        require(set(groups_no.get("CARRIER_NODES", ())) == {f"N{node}" for node in carrier_ids},
                f"{mail_path} CARRIER_NODES membership differs from source carrier")
    if control_ids:
        require(groups_no.get("NREF") == ("N116163",) and groups_no.get("NROT") == ("N116164",),
                f"{mail_path} NREF/NROT group identity changed")
    groups_ma = parse_aster_groups(mail_path, "GROUP_MA")
    require(set(groups_ma.get("PHYS", ())) == {f"M{elem}" for elem in case_record["physical_element_ids"]},
            f"{mail_path} PHYS element group differs from source body")
    if case_record["carrier_element_ids"]:
        require(set(groups_ma.get("CARR", ())) == {f"M{elem}" for elem in case_record["carrier_element_ids"]},
                f"{mail_path} CARR element group differs from source carrier")
    return {"input_nodes_exact": len(coords), "input_tetra10_connectivity_exact": len(elements),
            "input_coordinate_tokens_exact": True, "source_node_and_element_order_exact": True}


def source_mass_data(oracle: dict[str, Any]) -> dict[str, Any]:
    source_files = oracle["source_files"]
    mesh_record = read_json(Path(source_files["mesh.json"]["path"]))
    node_coords, element_connectivity = parse_source_mesh(Path(source_files["mesh.inp"]["path"]))
    body_name = oracle["source_bodies"]["physical"]
    physical_ids = tuple(sorted(int(node) for node in mesh_record["bodies"][body_name]["nodes"]))
    physical_elements = tuple(sorted(int(elem) for elem in mesh_record["bodies"][body_name]["elements"]))
    require(len(physical_ids) == oracle["source_bodies"]["physical_nodes"], "physical source node count mismatch")
    require(len(physical_elements) == oracle["source_bodies"]["physical_elements"], "physical source element count mismatch")
    node_position = {node: i for i, node in enumerate(physical_ids)}
    xyz = np.array([node_coords[node] for node in physical_ids], dtype=float)
    connectivity = np.array([[node_position[node] for node in element_connectivity[elem]]
                             for elem in physical_elements], dtype=np.int64)
    blocks = np.empty((len(connectivity), 10, 10), dtype=float)
    for index, elem in enumerate(connectivity):
        blocks[index] = tetra10_mass_matrix(xyz[elem], DENSITY, "fpg15")
    mass = float(blocks.sum())
    radius = xyz - PIVOT
    direction = np.cross(np.array((0.0, 1.0, 0.0)), radius)
    inertia = np.zeros((3, 3), dtype=float)
    for elem in connectivity:
        xyz_e = xyz[elem]
        for point, weight in zip(FPG15_POINTS, FPG15_WEIGHTS):
            bary = np.array((point[1], point[2], 1.0 - point.sum(), point[0]))
            dlam = np.array(((0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                             (-1.0, -1.0, -1.0), (1.0, 0.0, 0.0)))
            dn = np.empty((10, 3), dtype=float)
            for i in range(4):
                dn[i] = (4.0 * bary[i] - 1.0) * dlam[i]
            for k, (i, j) in enumerate(((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)), 4):
                dn[k] = 4.0 * (bary[i] * dlam[j] + bary[j] * dlam[i])
            det_j = float(np.linalg.det(xyz_e.T @ dn))
            require(det_j > 0 and math.isfinite(det_j), "nonpositive FPG15 Jacobian in physical mesh")
            shape = np.array([bary[i] * (2 * bary[i] - 1) for i in range(4)] +
                             [4 * bary[i] * bary[j] for i, j in
                              ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))])
            rel = shape @ xyz_e - PIVOT
            inertia += DENSITY * weight * det_j * (float(rel @ rel) * np.eye(3) - np.outer(rel, rel))

    slope = number(oracle["time_integration"]["angular_acceleration_slope_rad_s3"], "ramp slope") \
        if "angular_acceleration_slope_rad_s3" in oracle["time_integration"] else None
    if slope is None:
        match = oracle["time_integration"]["angular_acceleration_law"]
        try:
            slope = float(match.split("c=")[1].split()[0])
        except (IndexError, ValueError) as exc:
            raise CheckError("cannot parse angular-acceleration slope from oracle") from exc
    end_time = number(oracle["time_integration"]["time_end_s"], "end time")
    alpha_end = slope * end_time
    accel = alpha_end * direction
    loads = np.zeros_like(xyz)
    for elem, block in zip(connectivity, blocks):
        loads[elem] += block @ accel[elem]
    payload = b"".join(struct.pack("<q3d", node, *values)
                       for node, values in zip(physical_ids, loads))
    load_digest = hashlib.sha256(payload).hexdigest()
    mref = oracle["mass_reference"]
    oracle_loads = [(int(row[0]), *(float(x) for x in row[1:4]))
                    for row in mref["load_vector_final_tonne_mm_s2"]]
    require([row[0] for row in oracle_loads] == list(physical_ids), "oracle load node order differs from source")
    oracle_payload = b"".join(struct.pack("<q3d", node, fx, fy, fz)
                               for node, fx, fy, fz in oracle_loads)
    require(hashlib.sha256(oracle_payload).hexdigest() == mref["load_vector_final_sha256_le_nodeid_fx_fy_fz"],
            "oracle load-vector payload digest mismatch")
    require(np.allclose(np.array([row[1:] for row in oracle_loads]), loads,
                        rtol=2e-12, atol=2e-18), "oracle final nodal load vector is not FPG15 M*a")
    require(load_digest == mref["load_vector_final_sha256_le_nodeid_fx_fy_fz"],
            "independently rebuilt final nodal load digest differs from oracle")
    require(math.isclose(mass, MASS_REVIEW_REFERENCE_TONNE, rel_tol=5e-11, abs_tol=1e-16),
            "independently rebuilt FPG15 mass differs from review reference")
    require(math.isclose(inertia[1, 1], IYY_REVIEW_REFERENCE_TONNE_MM2,
                         rel_tol=5e-11, abs_tol=1e-13),
            "independently rebuilt FPG15 Iyy differs from review reference")
    require(math.isclose(mass, number(mref["physical_mass_tonne"], "oracle mass"),
                         rel_tol=2e-12, abs_tol=1e-16), "oracle total mass mismatch")
    require(math.isclose(inertia[1, 1], number(mref["rotation_y_modal_mass_tonne_mm2"], "oracle Iyy"),
                         rel_tol=2e-12, abs_tol=1e-13), "oracle Iyy mismatch")
    expected_energy = 0.5 * inertia[1, 1] * np.array(
        [number(row["omega_rad_s"], "omega") for row in oracle["time_integration"]["rotation_history"]]
    ) ** 2
    oracle_energy = np.array(mref["kinetic_energy_expected_by_state_N_mm"], dtype=float)
    require(expected_energy.shape == oracle_energy.shape and
            np.allclose(expected_energy, oracle_energy, rtol=2e-12, atol=1e-25),
            "Newmark analytical energy history disagrees with rebuilt FPG15 Iyy")
    return {"physical_node_ids": physical_ids, "physical_element_ids": physical_elements,
            "coordinates_mm": xyz, "connectivity": connectivity, "mass_blocks": blocks,
            "total_mass_tonne": mass, "inertia_about_pivot_tonne_mm2": inertia,
            "expected_energy_N_mm": expected_energy, "final_load_digest": load_digest}


def expected_history(oracle: dict[str, Any]) -> list[tuple[float, float, float, float]]:
    time = oracle["time_integration"]
    dt = number(time["dt_s"], "dt")
    n = int(time["increments"])
    beta, gamma = number(time["beta"], "beta"), number(time["gamma"], "gamma")
    law = time["angular_acceleration_law"]
    try:
        slope = float(law.split("c=")[1].split()[0])
    except (IndexError, ValueError) as exc:
        raise CheckError("cannot parse ramp slope") from exc
    state = [(0.0, 0.0, 0.0, 0.0)]
    q = qdot = qddot = 0.0
    for index in range(1, n + 1):
        t = index * dt
        a = slope * t
        qnew = q + dt * qdot + dt * dt * (0.5 - beta) * qddot + beta * dt * dt * a
        vnew = qdot + dt * (1.0 - gamma) * qddot + dt * gamma * a
        q, qdot, qddot = qnew, vnew, a
        state.append((t, q, qdot, qddot))
    require(len(state) == len(time["rotation_history"]), "rotation history state count mismatch")
    for i, (actual, recorded) in enumerate(zip(state, time["rotation_history"])):
        for key, value in zip(("time_s", "theta_rad", "omega_rad_s", "alpha_rad_s2"), actual):
            require(math.isclose(value, number(recorded[key], f"rotation_history[{i}].{key}"),
                                 rel_tol=2e-13, abs_tol=1e-20),
                    f"stored Newmark history differs at state {i}, {key}")
    return state


def coord_key(row: Iterable[Any]) -> tuple[float, float, float]:
    vals = tuple(number(value, "coordinate") for value in row)
    require(len(vals) == 3, "coordinate must contain exactly three components")
    return vals  # type: ignore[return-value]


def physical_indices(extracted: dict[str, Any], case_record: dict[str, Any], label: str) -> tuple[list[int], list[int], list[int]]:
    coords = extracted.get("coordinates")
    require(isinstance(coords, list), f"{label} extraction has no coordinates")
    keys = [coord_key(row) for row in coords]
    expected_coords = case_record.get("mesh_order_coordinates_mm")
    expected_ids = case_record.get("mesh_node_order_source_ids")
    require(isinstance(expected_coords, list) and isinstance(expected_ids, list) and
            len(expected_coords) == len(expected_ids), f"{label} oracle has no ordered source mesh coordinates")
    expected_keys = [coord_key(row) for row in expected_coords]
    require(len(keys) == len(expected_keys), f"{label} MED node count differs from the frozen mesh")
    groups = extracted.get("node_groups", {})
    require(isinstance(groups, dict), f"{label} extraction must include named node_groups")
    node_index: dict[int, int] = {}
    used_indices: set[int] = set()
    coordinate_max_error = 0.0
    for node_id, expected in zip((int(node) for node in expected_ids), expected_keys):
        singleton_name = f"N{node_id}"
        require(singleton_name in groups,
                f"{label} extraction lacks singleton node group {singleton_name}; use --all-singleton-groups")
        values = [int(value) for value in groups[singleton_name]]
        require(len(values) == 1, f"{label} singleton {singleton_name} does not resolve to one MED node")
        index = values[0]
        require(0 <= index < len(keys), f"{label} singleton {singleton_name} has an invalid MED node index")
        require(node_id not in node_index and index not in used_indices,
                f"{label} source-node singleton groups are not one-to-one")
        node_index[node_id] = index
        used_indices.add(index)
        component_error = max(abs(a - b) for a, b in zip(keys[index], expected))
        coordinate_max_error = max(coordinate_max_error, component_error)
        require(component_error <= MED_COORD_SERIALIZATION_ATOL_MM,
                f"{label} {singleton_name} coordinate serialization error {component_error:.6g} mm "
                f"exceeds {MED_COORD_SERIALIZATION_ATOL_MM:.3g} mm")
    require(used_indices == set(range(len(keys))),
            f"{label} source singleton groups do not cover all MED nodes exactly once")
    physical_ids = [int(node) for node in case_record["physical_node_ids"]]
    carrier_ids = [int(node) for node in case_record.get("carrier_node_ids", [])]
    pidx = [node_index[node] for node in physical_ids]
    cidx = [node_index[node] for node in carrier_ids]
    require("PHYS_NODES" in groups, f"{label} extraction omitted PHYS_NODES; pass --node-group PHYS_NODES")
    phys_group = [int(value) for value in groups["PHYS_NODES"]]
    require(len(phys_group) == len(pidx) and set(phys_group) == set(pidx),
            f"{label} PHYS_NODES group does not match exact coordinate mapping")
    if carrier_ids:
        require("CARRIER_NODES" in groups, f"{label} extraction omitted CARRIER_NODES")
        carrier_group = [int(value) for value in groups["CARRIER_NODES"]]
        require(len(carrier_group) == len(cidx) and set(carrier_group) == set(cidx),
                f"{label} CARRIER_NODES group does not match exact coordinate mapping")
    controls = []
    if case_record["include_map"]:
        for group_name in ("NREF", "NROT"):
            require(group_name in groups, f"{label} extraction omitted {group_name}; pass --node-group {group_name}")
            group_values = [int(value) for value in groups[group_name]]
            require(len(group_values) == 1, f"{label} {group_name} must resolve to exactly one node")
            controls.append(group_values[0])
        require(controls[0] != controls[1], f"{label} control groups resolve to same MED node index")
        require(np.allclose(np.array([keys[i] for i in controls]), np.vstack((PIVOT, PIVOT)),
                            rtol=0.0, atol=MED_COORD_SERIALIZATION_ATOL_MM),
                f"{label} coincident controls moved from the pinned pivot")
        require(controls[0] == node_index[116163] and controls[1] == node_index[116164],
                f"{label} NREF/NROT groups do not resolve to their exact source node identities")
    # Save output-serialization diagnostics for the parent report, keeping them
    # separate from the immutable source-geometry assertion and mechanical gates.
    extracted.setdefault("_checker_metadata", {})["max_med_coordinate_serialization_error_mm"] = coordinate_max_error
    return pidx, cidx, controls


def index_fields(extracted: dict[str, Any], case: str, expected_states: list[tuple[float, float, float, float]],
                 label: str) -> dict[str, list[dict[str, Any]]]:
    fields = extracted.get("fields")
    require(isinstance(fields, dict), f"{label} extraction has no fields object")
    names = oracle_names(case)
    indexed = {}
    for quantity in QUANTITIES:
        field_name = names[quantity]
        require(field_name in fields, f"{label} history missing {field_name}")
        states = fields[field_name]
        require(isinstance(states, list) and len(states) == len(expected_states),
                f"{label} {field_name} has wrong number of states")
        for i, (state, expected) in enumerate(zip(states, expected_states)):
            require(int(state.get("iteration", -1)) == i and int(state.get("order", -1)) == i,
                    f"{label} {field_name} iteration/order mismatch at state {i}")
            t = number(state.get("time"), f"{label} {field_name}[{i}].time")
            require(abs(t - expected[0]) <= ACCEPTANCE["time_absolute_seconds"],
                    f"{label} {field_name} time mismatch at state {i}: {t} vs {expected[0]}")
            components = state.get("components")
            require(isinstance(components, list) and len(components) == len(set(components)),
                    f"{label} {field_name}[{i}] component list invalid")
            require(set(VECTORS).issubset(components), f"{label} {field_name} omits DX/DY/DZ")
            values = state.get("values")
            require(isinstance(values, list) and len(values) == len(extracted["coordinates"]),
                    f"{label} {field_name}[{i}] node count mismatch")
            for node, row in enumerate(values):
                require(isinstance(row, list) and len(row) == len(components),
                        f"{label} {field_name}[{i}] malformed value row {node}")
                for component, item in zip(components, row):
                    number(item, f"{label} {field_name}[{i}][{node}].{component}")
        indexed[quantity] = states
    return indexed


def field_row(state: dict[str, Any], node_index: int, names: tuple[str, ...] = VECTORS) -> np.ndarray:
    component_position = {name: state["components"].index(name) for name in names}
    return np.array([number(state["values"][node_index][component_position[name]], name) for name in names])


def rigid_field(xyz: np.ndarray, scalar: float) -> np.ndarray:
    relative = xyz - PIVOT
    direction = np.cross(np.array((0.0, 1.0, 0.0)), relative)
    return scalar * direction


def field_abs_floor(quantity: str, tolerances: dict[str, Any]) -> float:
    return number(tolerances[{"DEPL": "displacement_absolute_floor_mm",
                             "VITE": "velocity_absolute_floor_mm_per_s",
                             "ACCE": "acceleration_absolute_floor_mm_per_s2"}[quantity]],
                  f"{quantity} abs floor")


def compare_array(actual: np.ndarray, expected: np.ndarray, peak: float, atol: float, rtol: float,
                  label: str) -> dict[str, Any]:
    errors = np.abs(actual - expected)
    bound = atol + rtol * peak
    fail_mask = errors > bound
    if np.any(fail_mask):
        loc = np.unravel_index(int(np.argmax(errors - bound)), errors.shape)
        raise CheckError(f"{label} exceeds frozen bound at {loc}: error={errors[loc]:.6g}, bound={bound:.6g}")
    zero_mask = expected == 0.0
    return {"max_absolute_error": float(errors.max(initial=0.0)),
            "max_error_over_bound": float(np.max(errors / bound)) if bound else 0.0,
            "max_absolute_error_where_expected_zero": float(errors[zero_mask].max(initial=0.0)) if np.any(zero_mask) else 0.0,
            "bound": bound, "mode_peak": peak, "passed": True}


def energy_from_velocity(velocity: np.ndarray, connectivity: np.ndarray, blocks: np.ndarray) -> float:
    # Local TETRA10 matrices are scalar; each applies independently to x/y/z.
    local = velocity[connectivity]
    return 0.5 * float(np.einsum("eic,eij,ejc->", local, blocks, local, optimize=True))


def check_histories(oracle: dict[str, Any], readiness: dict[str, Any], extracted_by_case: dict[str, dict[str, Any]],
                    mass_data: dict[str, Any]) -> dict[str, Any]:
    global ACCEPTANCE
    ACCEPTANCE = readiness["acceptance"]
    rtol = number(ACCEPTANCE["field_error_mode_peak_relative"], "field relative tolerance")
    energy_rtol = number(ACCEPTANCE["kinetic_energy_relative"], "energy relative tolerance")
    history = expected_history(oracle)
    xyz = mass_data["coordinates_mm"]
    physical_ids = list(mass_data["physical_node_ids"])
    require(list(oracle["cases"]["direct"]["physical_node_ids"]) == physical_ids,
            "oracle direct physical node order differs from pinned source order")
    quantities_indexed = {}
    role_indices = {}
    med_coordinate_errors = {}
    for case in CASE_NAMES:
        pidx, cidx, controls = physical_indices(extracted_by_case[case], oracle["cases"][case], case)
        require(len(pidx) == len(xyz), f"{case} physical node count mismatch")
        physical_med_xyz = np.array([coord_key(extracted_by_case[case]["coordinates"][i]) for i in pidx])
        physical_coordinate_error = float(np.max(np.abs(physical_med_xyz - xyz), initial=0.0))
        require(physical_coordinate_error <= MED_COORD_SERIALIZATION_ATOL_MM,
                f"{case} physical node coordinate serialization exceeds allowed metadata bound")
        med_coordinate_errors[case] = extracted_by_case[case]["_checker_metadata"][
            "max_med_coordinate_serialization_error_mm"]
        quantities_indexed[case] = index_fields(extracted_by_case[case], case, history, case)
        role_indices[case] = (pidx, cidx, controls)

    field_summary: dict[str, Any] = {}
    pairwise_summary: dict[str, Any] = {}
    carrier_summary: dict[str, Any] = {}
    carrier_from_controls_summary: dict[str, Any] = {}
    control_summary: dict[str, Any] = {}
    expected_energy = mass_data["expected_energy_N_mm"]
    actual_energy: dict[str, list[float]] = {case: [] for case in CASE_NAMES}
    for qindex, quantity in enumerate(QUANTITIES):
        scalar_index = {"DEPL": 1, "VITE": 2, "ACCE": 3}[quantity]
        case_values: dict[str, list[np.ndarray]] = {}
        q_reports = {}
        for case in CASE_NAMES:
            pidx, cidx, controls = role_indices[case]
            states = quantities_indexed[case][quantity]
            case_values[case] = []
            expected_list = []
            errors_by_state = []
            for step, (state, qstate) in enumerate(zip(states, history)):
                expected = rigid_field(xyz, qstate[scalar_index])
                actual = np.array([field_row(state, index) for index in pidx])
                peak = float(np.max(np.abs(expected), initial=0.0))
                errors_by_state.append(compare_array(actual, expected, peak, field_abs_floor(quantity, ACCEPTANCE),
                                                     rtol, f"{case}.{quantity}[{step}]"))
                case_values[case].append(actual)
                expected_list.append(expected)
                if cidx:
                    carrier_xyz = np.array([coord_key(extracted_by_case[case]["coordinates"][i]) for i in cidx])
                    carrier_expected = rigid_field(carrier_xyz, qstate[scalar_index])
                    carrier_actual = np.array([field_row(state, index) for index in cidx])
                    csummary = compare_array(carrier_actual, carrier_expected, peak,
                                             field_abs_floor(quantity, ACCEPTANCE), rtol,
                                             f"{case}.carrier.{quantity}[{step}]")
                    carrier_summary.setdefault(quantity, []).append(csummary)
                if controls:
                    ref_index, rot_index = controls
                    cindex = {name: state["components"].index(name) for name in state["components"]}
                    # DIS_TR controls carry translations (DX/DY/DZ); their unused rotation DOFs are fixed zero.
                    for control_label, node_index, expected_translation in (
                        ("NREF", ref_index, np.zeros(3)),
                        ("NROT", rot_index, np.array((0.0, qstate[scalar_index], 0.0))),
                    ):
                        actual_translation = field_row(state, node_index)
                        normalization_peak = (abs(qstate[scalar_index]) if control_label == "NROT" else peak)
                        csummary = compare_array(actual_translation, expected_translation, normalization_peak,
                                                 field_abs_floor(quantity, ACCEPTANCE), rtol,
                                                 f"{case}.{control_label}.{quantity}[{step}]")
                        control_summary.setdefault(f"{control_label}.{quantity}", []).append(csummary)
                        for rotational in ("DRX", "DRY", "DRZ"):
                            if rotational in cindex:
                                actual_rot = number(state["values"][node_index][cindex[rotational]], rotational)
                                require(abs(actual_rot) <= field_abs_floor(quantity, ACCEPTANCE) + rtol * normalization_peak,
                                        f"{case}.{control_label}.{quantity}[{step}].{rotational} is nonzero")
                    if cidx:
                        measured_translation = field_row(state, ref_index)
                        measured_rotation = field_row(state, rot_index)
                        carrier_relative = carrier_xyz - PIVOT
                        expected_from_measured_controls = measured_translation + np.cross(
                            np.broadcast_to(measured_rotation, carrier_relative.shape), carrier_relative
                        )
                        carrier_from_controls = np.array([field_row(state, index) for index in cidx])
                        measured_summary = compare_array(
                            carrier_from_controls, expected_from_measured_controls, peak,
                            field_abs_floor(quantity, ACCEPTANCE), rtol,
                            f"{case}.carrier_from_measured_controls.{quantity}[{step}]")
                        carrier_from_controls_summary.setdefault(quantity, []).append(measured_summary)
            q_reports[case] = {
                "states": len(states),
                "max_error_over_frozen_bound": max(item["max_error_over_bound"] for item in errors_by_state),
                "max_absolute_error": max(item["max_absolute_error"] for item in errors_by_state),
                "max_error_where_expected_zero": max(item["max_absolute_error_where_expected_zero"] for item in errors_by_state),
                "relative_tolerance": rtol,
                "absolute_floor": field_abs_floor(quantity, ACCEPTANCE),
                "normalization": "analytical physical-body component maximum for this field and state",
            }
        field_summary[quantity] = q_reports
        for left, right in (("direct", "mapped_no_carrier"), ("direct", "mapped_carrier"),
                            ("mapped_no_carrier", "mapped_carrier")):
            pair_key = f"{left}__vs__{right}"
            pair_reports = []
            for step, qstate in enumerate(history):
                expected = rigid_field(xyz, qstate[scalar_index])
                peak = float(np.max(np.abs(expected), initial=0.0))
                report = compare_array(case_values[left][step], case_values[right][step], peak,
                                       field_abs_floor(quantity, ACCEPTANCE), rtol,
                                       f"{quantity}.{pair_key}[{step}]")
                pair_reports.append(report)
            pairwise_summary.setdefault(quantity, {})[pair_key] = {
                "states": len(pair_reports),
                "max_error_over_frozen_bound": max(r["max_error_over_bound"] for r in pair_reports),
                "max_absolute_difference": max(r["max_absolute_error"] for r in pair_reports),
                "max_difference_where_analytical_component_zero": max(
                    r["max_absolute_error_where_expected_zero"] for r in pair_reports),
                "passed": True,
            }
        if quantity == "VITE":
            for case in CASE_NAMES:
                pidx = role_indices[case][0]
                states = quantities_indexed[case][quantity]
                case_energy = []
                for state_index, state in enumerate(states):
                    velocities = np.zeros_like(xyz)
                    velocities[:] = np.array([field_row(state, index) for index in pidx])
                    measured = energy_from_velocity(velocities, mass_data["connectivity"], mass_data["mass_blocks"])
                    case_energy.append(measured)
                    ref = float(expected_energy[state_index])
                    if ref == 0.0:
                        err = abs(measured - ref)
                        require(err <= number(ACCEPTANCE["zero_energy_absolute_floor_tonne_mm2_per_s2"], "zero-energy floor"),
                                f"{case} initial kinetic energy exceeds frozen zero-energy floor")
                    else:
                        rel = abs(measured - ref) / abs(ref)
                        require(rel <= energy_rtol,
                                f"{case} kinetic energy relative error at state {state_index}: {rel:.6g} > {energy_rtol:.6g}")
                actual_energy[case] = case_energy

    energy_summary = {}
    for case in CASE_NAMES:
        errors = [abs(a - b) for a, b in zip(actual_energy[case], expected_energy)]
        relatives = [abs(a - b) / abs(b) for a, b in zip(actual_energy[case], expected_energy) if b != 0.0]
        energy_summary[case] = {"states": len(actual_energy[case]),
                                "terminal_N_mm": actual_energy[case][-1],
                                "terminal_expected_N_mm": float(expected_energy[-1]),
                                "max_absolute_error_N_mm": max(errors),
                                "max_relative_error_nonzero": max(relatives, default=0.0),
                                "zero_state_absolute_floor": ACCEPTANCE["zero_energy_absolute_floor_tonne_mm2_per_s2"],
                                "relative_tolerance": energy_rtol,
                                "passed": True}
    for left, right in (("direct", "mapped_no_carrier"), ("direct", "mapped_carrier"),
                        ("mapped_no_carrier", "mapped_carrier")):
        pair_errors = [abs(a - b) for a, b in zip(actual_energy[left], actual_energy[right])]
        for i, (error, ref) in enumerate(zip(pair_errors, expected_energy)):
            if ref == 0.0:
                require(error <= number(ACCEPTANCE["zero_energy_absolute_floor_tonne_mm2_per_s2"], "zero-energy floor"),
                        f"pairwise energy {left}/{right} exceeds zero floor at state {i}")
            else:
                require(error / abs(ref) <= energy_rtol,
                        f"pairwise energy {left}/{right} exceeds relative tolerance at state {i}")
        energy_summary[f"{left}__vs__{right}"] = {
            "max_absolute_difference_N_mm": max(pair_errors),
            "max_relative_difference_nonzero": max((e / abs(x) for e, x in zip(pair_errors, expected_energy) if x != 0.0), default=0.0),
            "passed": True,
        }
    require(number(oracle["source_bodies"]["carrier_material"]["density_tonne_per_mm3"], "carrier density") == 0.0,
            "carrier density is not zero")
    return {"status": "PASS", "state_count": len(history), "physical_node_count": len(xyz),
            "med_coordinate_serialization": {
                "separate_metadata_bound_mm": MED_COORD_SERIALIZATION_ATOL_MM,
                "maximum_component_error_by_case_mm": med_coordinate_errors,
                "source_ASCII_and_generated_mesh_identity_are_checked_separately": True,
            },
            "field_vs_analytical": field_summary, "pairwise_physical_fields": pairwise_summary,
            "carrier_linear_small_motion": {"all_carrier_nodes_checked": len(role_indices["mapped_carrier"][1]),
                                             "field_summaries": carrier_summary,
                                             "measured_control_consistency": carrier_from_controls_summary,
                                             "mass_tonne": 0.0,
                                             "kinetic_energy_N_mm": 0.0,
                                             "zero_inertia_basis": "source carrier density RHO=0; no carrier nodal loads",
                                             "finite_rotation_claim": False},
            "control_translation_histories": {
                "checks": control_summary,
                "rotation_normalization": "NROT translation-coded angle/angle-rate/angle-acceleration uses its own expected absolute peak; the same numerical absolute floors apply in those encoded units",
            },
            "physical_kinetic_energy_N_mm": energy_summary}


def oracle_names(case: str) -> dict[str, str]:
    return _ACTIVE_ORACLE["cases"][case]["expected_field_names"]


def run(args: argparse.Namespace) -> dict[str, Any]:
    global _ACTIVE_ORACLE
    oracle = read_json(args.oracle)
    _ACTIVE_ORACLE = oracle
    readiness = read_json(args.readiness)
    require(readiness.get("frozen_before_native") is True, "parent readiness tolerances are not frozen")
    input_manifest = read_json(args.manifest)
    require(input_manifest["oracle_sha256"] == sha256(args.oracle), "oracle hash differs from input manifest")
    source_audit = verify_source_map_and_comm(oracle, args.input_root, input_manifest)
    mass_data = source_mass_data(oracle)
    extracted = {case: read_json(getattr(args, case)) for case in CASE_NAMES}
    histories = check_histories(oracle, readiness, extracted, mass_data)
    return {
        "schema": "code_aster_actual_a09_first_map_history_check/v1",
        "status": "PASS",
        "scope": oracle["scope"],
        "solver_execution_by_checker": False,
        "oracle": str(args.oracle),
        "readiness": str(args.readiness),
        "input_manifest": str(args.manifest),
        "source_and_equation_audit": source_audit,
        "mass_oracle_rebuild": {
            "method": "Code_Aster 17.4 ordinary 3D MECA_TETRA10 FPG15; curved det(J) at each point",
            "fpg15_weight_sum": float(FPG15_WEIGHTS.sum()),
            "physical_mass_tonne": mass_data["total_mass_tonne"],
            "review_reference_mass_tonne": MASS_REVIEW_REFERENCE_TONNE,
            "inertia_about_pivot_tonne_mm2": mass_data["inertia_about_pivot_tonne_mm2"].tolist(),
            "review_reference_Iyy_tonne_mm2": IYY_REVIEW_REFERENCE_TONNE_MM2,
            "final_nodal_load_sha256": mass_data["final_load_digest"],
            "all_loads_recomputed_as_FPG15_Ma": True,
        },
        "frozen_tolerances": readiness["acceptance"],
        "history_checks": histories,
        "claim_limit": "one actual A00 first-bolt/nut weighted map and one zero-density carrier under one infinitesimal global-Y angular-acceleration mode; no finite-rotation, contact, thread, strength, or joint acceptance",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--direct", required=True, type=Path, help="extracted direct nodal-history JSON")
    parser.add_argument("--mapped-no-carrier", dest="mapped_no_carrier", required=True, type=Path,
                        help="extracted actual-map nodal-history JSON")
    parser.add_argument("--mapped-carrier", dest="mapped_carrier", required=True, type=Path,
                        help="extracted actual-map plus zero-density carrier history JSON")
    parser.add_argument("--oracle", type=Path, default=HERE / "oracle.json")
    parser.add_argument("--manifest", type=Path, default=HERE / "input-manifest.json")
    parser.add_argument("--input-root", type=Path, default=HERE / "input")
    parser.add_argument("--readiness", type=Path, default=READINESS_PATH)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        report = run(args)
    except (CheckError, KeyError, TypeError, ValueError, IndexError) as exc:
        report = {"schema": "code_aster_actual_a09_first_map_history_check/v1",
                  "status": "FAIL", "error": str(exc), "solver_execution_by_checker": False}
    rendered = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered)
    print(rendered, end="")
    return 0 if report.get("status") == "PASS" else 1


_ACTIVE_ORACLE: dict[str, Any] = {}
ACCEPTANCE: dict[str, Any] = {}


if __name__ == "__main__":
    raise SystemExit(main())
