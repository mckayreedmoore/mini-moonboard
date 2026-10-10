#!/usr/bin/env python3
"""Generate an offline Code_Aster 17.4 A09 first-axis map fixture.

This script reads the frozen source C3D10 mesh, source material cards, source
M03 rigid-node set, and the first six A00 *EQUATION rows. It emits three
small-motion free-response decks and a discrete FPG15 mass/load oracle. It
never starts Code_Aster or changes the source geometry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"
MASS_MODULE_DIR = ROOT / "fea/code_aster_trial/mass_reference"
sys.path.insert(0, str(MASS_MODULE_DIR))
from aster_tetra10_mass import FPG15_POINTS, FPG15_WEIGHTS, tetra10_mass_matrix  # noqa: E402


PINS = {
    "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "nut-coupling.inp": "af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903",
    "rigid-carriers.inp": "a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815",
    "materials.inp": "e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb",
}
BODY = "M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION"
CARRIER = "M03_A00_NUT"
CONTROL_IDS = (116163, 116164)  # REF and ROT; both are at the native pivot.
PIVOT = np.array((134.5, 1.178456090256, 410.856889078727), dtype=float)
DENSITY_PHYS = 7.85e-9  # tonne / mm^3, as in materials.inp
DENSITY_CARRIER = 0.0
E_STEEL = 200000.0  # MPa, as in materials.inp
NU_STEEL = 0.3
T_END = 1.0e-4  # s
N_STEPS = 10
DT = T_END / N_STEPS
BETA = 0.25
GAMMA = 0.5
THETA_END_TARGET = 2.01e-7  # rad; gives c=1.2e6 rad/s^3 for these steps.
ACCEL_RAMP_SLOPE = THETA_END_TARGET / (T_END**3 / 6.0 + T_END * DT**2 / 12.0)
CONTROL_IDS_SOURCE_TEXT = {"116163": "NREF", "116164": "NROT"}
DOF_TO_ASTER = {1: "DX", 2: "DY", 3: "DZ"}


class FixtureError(RuntimeError):
    pass


@dataclass(frozen=True)
class EquationTerm:
    node: int
    dof: int
    coefficient: str


@dataclass(frozen=True)
class SourceData:
    node_tokens: dict[int, tuple[str, str, str]]
    element_nodes: dict[int, tuple[int, ...]]
    physical_nodes: tuple[int, ...]
    physical_elements: tuple[int, ...]
    carrier_nodes: tuple[int, ...]
    carrier_elements: tuple[int, ...]
    control_tokens: dict[int, tuple[str, str, str]]
    equations: tuple[tuple[EquationTerm, ...], ...]
    dependent_dofs: tuple[tuple[int, int], ...]
    source_hashes: dict[str, str]
    source_materials: dict[str, dict[str, float]]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise FixtureError(message)


def parse_abaqus_mesh(path: Path) -> tuple[dict[int, tuple[str, str, str]], dict[int, tuple[int, ...]]]:
    node_tokens: dict[int, tuple[str, str, str]] = {}
    element_nodes: dict[int, tuple[int, ...]] = {}
    section = ""
    pending: list[str] = []

    def finish_element() -> None:
        nonlocal pending
        if not pending:
            return
        require(len(pending) == 11, f"C3D10 record has {len(pending)} fields, expected 11")
        elem_id, *connectivity = (int(v) for v in pending)
        require(elem_id not in element_nodes, f"duplicate C3D10 element ID {elem_id}")
        element_nodes[elem_id] = tuple(connectivity)
        pending = []

    for line_number, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if section == "ELEMENT_C3D10":
                finish_element()
            upper = line.upper().replace(" ", "")
            if upper == "*NODE":
                section = "NODE"
            elif upper.startswith("*ELEMENT,TYPE=C3D10"):
                section = "ELEMENT_C3D10"
            else:
                section = ""
            continue
        if section == "NODE":
            fields = [item.strip() for item in line.split(",")]
            require(len(fields) == 4, f"node row at line {line_number} does not have ID+xyz")
            node_id = int(fields[0])
            require(node_id not in node_tokens, f"duplicate source node ID {node_id}")
            node_tokens[node_id] = tuple(fields[1:4])
        elif section == "ELEMENT_C3D10":
            pending.extend(item.strip() for item in line.split(",") if item.strip())
            if len(pending) >= 11:
                finish_element()
    if section == "ELEMENT_C3D10":
        finish_element()
    require(node_tokens and element_nodes, "source mesh parser found no nodes or C3D10 elements")
    return node_tokens, element_nodes


def parse_equations(path: Path) -> tuple[tuple[EquationTerm, ...], ...]:
    lines = path.read_text().splitlines()
    sections: list[tuple[EquationTerm, ...]] = []
    index = 0
    while index < len(lines):
        if lines[index].strip().upper() != "*EQUATION":
            index += 1
            continue
        index += 1
        require(index < len(lines), "truncated *EQUATION section")
        term_count = int(lines[index].strip())
        index += 1
        fields: list[str] = []
        while len(fields) < 3 * term_count:
            require(index < len(lines), "truncated *EQUATION data")
            raw = lines[index].strip()
            require(not raw.startswith("*"), "new Abaqus keyword before equation row completed")
            fields.extend(field.strip() for field in raw.split(",") if field.strip())
            index += 1
        require(len(fields) == 3 * term_count, "equation has trailing or missing fields")
        terms = tuple(
            EquationTerm(int(fields[offset]), int(fields[offset + 1]), fields[offset + 2])
            for offset in range(0, len(fields), 3)
        )
        sections.append(terms)
    require(len(sections) >= 6, f"expected at least 6 source equations, found {len(sections)}")
    return tuple(sections[:6])


def parse_nset(path: Path, set_name: str) -> tuple[int, ...]:
    lines = path.read_text().splitlines()
    inside = False
    ids: list[int] = []
    target = f"*NSET,NSET={set_name}".upper()
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            inside = line.upper().replace(" ", "") == target
            continue
        if inside:
            ids.extend(int(item.strip()) for item in line.split(",") if item.strip())
    require(bool(ids), f"NSET {set_name} has no nodes")
    require(len(ids) == len(set(ids)), f"NSET {set_name} contains duplicate nodes")
    return tuple(sorted(ids))


def parse_control_nodes(path: Path, ids: tuple[int, int]) -> dict[int, tuple[str, str, str]]:
    lines = path.read_text().splitlines()
    selected: dict[int, tuple[str, str, str]] = {}
    section = ""
    for line_number, raw in enumerate(lines, start=1):
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            section = "NODE" if line.upper() == "*NODE" else ""
            continue
        if section == "NODE":
            fields = [item.strip() for item in line.split(",")]
            if len(fields) == 4 and int(fields[0]) in ids:
                node_id = int(fields[0])
                selected[node_id] = tuple(fields[1:4])
    require(set(selected) == set(ids), f"control nodes missing from source map: {set(ids)-set(selected)}")
    return selected


def parse_materials(path: Path) -> dict[str, dict[str, float]]:
    lines = path.read_text().splitlines()
    result: dict[str, dict[str, float]] = {}
    current = ""
    density = None
    elastic = None
    in_density = False
    in_elastic = False
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            if line.upper().startswith("*MATERIAL,"):
                if current and density is not None and elastic is not None:
                    result[current] = {"density_tonne_per_mm3": density, "E_MPa": elastic[0], "nu": elastic[1]}
                match = re.search(r"NAME=([^,]+)", line, re.IGNORECASE)
                current = match.group(1) if match else ""
                density = None
                elastic = None
                in_density = False
                in_elastic = False
            else:
                in_density = line.upper() == "*DENSITY"
                in_elastic = line.upper().startswith("*ELASTIC")
            continue
        if in_density:
            density = float(line.split(",")[0].strip())
            in_density = False
        elif in_elastic and current == "STEEL_ELASTIC_DIAGNOSTIC":
            values = [float(value.strip()) for value in line.split(",")]
            elastic = (values[0], values[1])
            in_elastic = False
        elif in_elastic and current == "NUT_ZERO_MASS_RIGID_CARRIER":
            values = [float(value.strip()) for value in line.split(",")]
            elastic = (values[0], values[1])
            in_elastic = False
    if current and density is not None and elastic is not None:
        result[current] = {"density_tonne_per_mm3": density, "E_MPa": elastic[0], "nu": elastic[1]}
    require("STEEL_ELASTIC_DIAGNOSTIC" in result, "steel diagnostic material not found")
    require("NUT_ZERO_MASS_RIGID_CARRIER" in result, "zero-mass carrier material not found")
    return result


def load_source() -> SourceData:
    source_hashes = {name: sha256(SOURCE / name) for name in PINS}
    for name, expected in PINS.items():
        require(source_hashes[name] == expected, f"source hash mismatch for {name}: {source_hashes[name]}")
    mesh_record = json.loads((SOURCE / "mesh.json").read_text())
    physical_nodes = tuple(sorted(int(n) for n in mesh_record["bodies"][BODY]["nodes"]))
    physical_elements = tuple(sorted(int(e) for e in mesh_record["bodies"][BODY]["elements"]))
    carrier_nodes_from_record = tuple(sorted(int(n) for n in mesh_record["bodies"][CARRIER]["nodes"]))
    carrier_elements = tuple(sorted(int(e) for e in mesh_record["bodies"][CARRIER]["elements"]))
    node_tokens, element_nodes = parse_abaqus_mesh(SOURCE / "mesh.inp")
    require(set(physical_nodes).issubset(node_tokens), "physical source nodes missing from mesh.inp")
    require(set(carrier_nodes_from_record).issubset(node_tokens), "carrier source nodes missing from mesh.inp")
    require(set(physical_elements).issubset(element_nodes), "physical source elements missing from mesh.inp")
    require(set(carrier_elements).issubset(element_nodes), "carrier source elements missing from mesh.inp")
    for elem_set, nodes in ((physical_elements, physical_nodes), (carrier_elements, carrier_nodes_from_record)):
        actual = {node for elem in elem_set for node in element_nodes[elem]}
        require(actual == set(nodes), f"mesh.json node ownership does not match connectivity for {elem_set}")
    carrier_nodes = parse_nset(SOURCE / "rigid-carriers.inp", "M03_A00_NUT_RIGID_NODES")
    require(carrier_nodes == carrier_nodes_from_record, "source M03 rigid-node NSET differs from mesh.json body nodes")
    require(set(physical_nodes).isdisjoint(carrier_nodes), "physical and carrier source node IDs overlap")
    control_tokens = parse_control_nodes(SOURCE / "nut-coupling.inp", CONTROL_IDS)
    require(not (set(CONTROL_IDS) & set(node_tokens)), "control node ID unexpectedly occurs in volume mesh")
    node_tokens.update(control_tokens)
    equations = parse_equations(SOURCE / "nut-coupling.inp")
    dependent = tuple((row[0].node, row[0].dof) for row in equations)
    require(all(node in physical_nodes for node, _ in dependent), "an A00 dependent DOF is outside the physical body")
    require(len(set(dependent)) == 6, "the six source A00 dependent DOFs are not unique")
    require(all(len(row) == 754 for row in equations), "A00 equation term count changed")
    require(all(term.dof in (1, 2, 3) for row in equations for term in row), "unexpected source equation DOF")
    require(all(term.node in set(physical_nodes) | set(CONTROL_IDS) for row in equations for term in row),
            "source A00 equation references an unexpected node")
    materials = parse_materials(SOURCE / "materials.inp")
    require(materials["STEEL_ELASTIC_DIAGNOSTIC"]["density_tonne_per_mm3"] == DENSITY_PHYS,
            "physical density differs from source material card")
    require(materials["NUT_ZERO_MASS_RIGID_CARRIER"]["density_tonne_per_mm3"] == DENSITY_CARRIER,
            "carrier density differs from source material card")
    require(materials["STEEL_ELASTIC_DIAGNOSTIC"]["E_MPa"] == E_STEEL, "physical E differs from source")
    require(materials["NUT_ZERO_MASS_RIGID_CARRIER"]["E_MPa"] == E_STEEL, "carrier E differs from source")
    return SourceData(node_tokens, element_nodes, physical_nodes, physical_elements, carrier_nodes,
                      carrier_elements, control_tokens, equations, dependent, source_hashes, materials)


def coords_for_ids(data: SourceData, ids: Iterable[int]) -> np.ndarray:
    return np.array([[float(value) for value in data.node_tokens[node]] for node in ids], dtype=float)


def body_arrays(data: SourceData) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    physical_ids = list(data.physical_nodes)
    physical_position = {node: idx for idx, node in enumerate(physical_ids)}
    physical_xyz = coords_for_ids(data, physical_ids)
    physical_elem_ids = list(data.physical_elements)
    physical_connectivity = np.array([
        [physical_position[node] for node in data.element_nodes[elem]]
        for elem in physical_elem_ids
    ], dtype=np.int64)
    carrier_ids = list(data.carrier_nodes)
    carrier_position = {node: idx for idx, node in enumerate(carrier_ids)}
    carrier_xyz = coords_for_ids(data, carrier_ids)
    carrier_elem_ids = list(data.carrier_elements)
    carrier_connectivity = np.array([
        [carrier_position[node] for node in data.element_nodes[elem]]
        for elem in carrier_elem_ids
    ], dtype=np.int64)
    return physical_xyz, physical_connectivity, carrier_xyz, carrier_connectivity


def newmark_rotation_history() -> list[dict[str, float]]:
    q = qdot = qddot = 0.0
    rows = [{"step": 0, "time_s": 0.0, "theta_rad": 0.0, "omega_rad_s": 0.0, "alpha_rad_s2": 0.0}]
    for step in range(1, N_STEPS + 1):
        time = step * DT
        next_accel = ACCEL_RAMP_SLOPE * time
        next_q = q + DT * qdot + DT * DT * (0.5 - BETA) * qddot + BETA * DT * DT * next_accel
        next_qdot = qdot + DT * (1.0 - GAMMA) * qddot + DT * GAMMA * next_accel
        q, qdot, qddot = next_q, next_qdot, next_accel
        rows.append({"step": step, "time_s": time, "theta_rad": q, "omega_rad_s": qdot,
                     "alpha_rad_s2": qddot})
    return rows


def compute_mass_and_load(data: SourceData) -> dict[str, Any]:
    physical_xyz, connectivity, _, _ = body_arrays(data)
    mass_blocks = np.empty((len(connectivity), 10, 10), dtype=float)
    for index, element_nodes in enumerate(connectivity):
        mass_blocks[index] = tetra10_mass_matrix(physical_xyz[element_nodes], DENSITY_PHYS, "fpg15")
    element_volumes = mass_blocks.sum(axis=(1, 2)) / DENSITY_PHYS
    total_mass = float(element_volumes.sum() * DENSITY_PHYS)
    require(total_mass > 0.0 and math.isfinite(total_mass), "FPG15 physical mass is nonpositive or nonfinite")
    node_mass = np.zeros((len(physical_xyz),), dtype=float)
    for elem, block in zip(connectivity, mass_blocks):
        node_mass[elem] += block.sum(axis=1)
    centroid = node_mass @ physical_xyz / total_mass
    relative = physical_xyz - PIVOT
    direction = np.cross(np.array((0.0, 1.0, 0.0)), relative)
    inertia = np.zeros((3, 3), dtype=float)
    final_accel = ACCEL_RAMP_SLOPE * T_END * direction
    final_load = np.zeros_like(physical_xyz)
    energy_mode_mass = 0.0
    for elem, block in zip(connectivity, mass_blocks):
        xyz_e = physical_xyz[elem]
        r_q = FPG15_POINTS
        # N(q) and det(J(q)) are the same FPG15 quadrature used in each mass block.
        # The load action is computed from the consistent nodal matrix, M_e a_e.
        final_load[elem] += block @ final_accel[elem]
        d_e = direction[elem]
        energy_mode_mass += float(np.einsum("ia,ij,ja->", d_e, block, d_e))
    resultant = final_load.sum(axis=0)
    moment = np.cross(relative, final_load).sum(axis=0)
    # Integral-based inertia uses the same FPG15 rule, curved geometry, and material density.
    for elem in connectivity:
        xyz_e = physical_xyz[elem]
        for point, weight in zip(FPG15_POINTS, FPG15_WEIGHTS):
            bary = np.array((point[1], point[2], 1.0 - point.sum(), point[0]))
            dlam = np.array(((0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                             (-1.0, -1.0, -1.0), (1.0, 0.0, 0.0)))
            dn = np.empty((10, 3), dtype=float)
            for i in range(4):
                dn[i] = (4.0 * bary[i] - 1.0) * dlam[i]
            for k, (i, j) in enumerate(((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)), 4):
                dn[k] = 4.0 * (bary[i] * dlam[j] + bary[j] * dlam[i])
            detj = float(np.linalg.det(xyz_e.T @ dn))
            n = np.array([bary[i] * (2.0 * bary[i] - 1.0) for i in range(4)] +
                         [4.0 * bary[i] * bary[j] for i, j in
                          ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))])
            position = n @ xyz_e
            r = position - PIVOT
            inertia += DENSITY_PHYS * weight * detj * (float(r @ r) * np.eye(3) - np.outer(r, r))
    alpha_end = ACCEL_RAMP_SLOPE * T_END
    expected_resultant = total_mass * np.cross((0.0, alpha_end, 0.0), centroid - PIVOT)
    expected_moment = inertia @ np.array((0.0, alpha_end, 0.0))
    require(np.max(np.abs(resultant - expected_resultant)) <= 2e-10 * max(1.0, np.max(np.abs(expected_resultant))),
            "FPG15 load resultant does not match mass-center acceleration")
    require(np.max(np.abs(moment - expected_moment)) <= 2e-10 * max(1.0, np.max(np.abs(expected_moment))),
            "FPG15 load moment does not match pivot inertia")
    require(abs(energy_mode_mass - inertia[1, 1]) <= 2e-9 * max(1.0, abs(inertia[1, 1])),
            "FPG15 modal mass does not match independently integrated Iyy")
    load_rows = [(int(node), *[float(value) for value in values])
                 for node, values in zip(data.physical_nodes, final_load)]
    payload = b"".join(struct.pack("<q3d", node, fx, fy, fz) for node, fx, fy, fz in load_rows)
    times = newmark_rotation_history()
    energy_states = [0.5 * energy_mode_mass * state["omega_rad_s"] ** 2 for state in times]
    return {
        "method": "Code_Aster v17.4 ordinary 3D MECA_TETRA10 MASS=FPG15 consistent mass; pointwise curved det(J)",
        "rule_points_reference_xyz": FPG15_POINTS.tolist(),
        "rule_weights_reference_volume_1_over_6": FPG15_WEIGHTS.tolist(),
        "rule_weight_sum": float(FPG15_WEIGHTS.sum()),
        "physical_mass_tonne": total_mass,
        "physical_volume_mm3": total_mass / DENSITY_PHYS,
        "physical_centroid_mm": centroid.tolist(),
        "inertia_about_pivot_tonne_mm2": inertia.tolist(),
        "rotation_y_modal_mass_tonne_mm2": energy_mode_mass,
        "load_vector_final_tonne_mm_s2": load_rows,
        "load_vector_final_sha256_le_nodeid_fx_fy_fz": hashlib.sha256(payload).hexdigest(),
        "final_resultant_N": resultant.tolist(),
        "expected_resultant_N": expected_resultant.tolist(),
        "final_moment_about_pivot_N_mm": moment.tolist(),
        "expected_moment_about_pivot_N_mm": expected_moment.tolist(),
        "kinetic_energy_expected_by_state_N_mm": energy_states,
        "maximum_radius_mm": float(np.linalg.norm(physical_xyz - PIVOT, axis=1).max()),
        "maximum_rotation_displacement_direction_mm": float(np.linalg.norm(direction, axis=1).max()),
        "independent_checks": {
            "total_load_resultant_matches_centroid_acceleration": True,
            "total_load_moment_matches_pivot_inertia": True,
            "modal_mass_matches_pivot_Iyy": True,
            "fpg4_not_used": True,
        },
    }


def _rows_for_comm(rows: Iterable[Iterable[str]], indent: str, limit: int = 7) -> str:
    values = [list(row) for row in rows]
    chunks = [values[i:i + limit] for i in range(0, len(values), limit)]
    return "\n".join(indent + ", ".join(row) + ("," if index + 1 < len(chunks) else "")
                     for index, chunk in enumerate(chunks) for row in chunk)


def _format_tuple(values: Iterable[str], indent: str = "        ", limit: int = 8) -> str:
    vals = list(values)
    chunks = [vals[i:i + limit] for i in range(0, len(vals), limit)]
    lines = [indent + ", ".join(chunk) + ("," if index + 1 < len(chunks) else "")
             for index, chunk in enumerate(chunks)]
    return "(\n" + "\n".join(lines) + "\n    )"


def aster_node(node_id: int) -> str:
    return f"'N{node_id}'"


def write_mail(path: Path, data: SourceData, case: str) -> dict[str, Any]:
    include_carrier = case == "mapped_carrier"
    include_controls = case != "direct"
    nodes = set(data.physical_nodes)
    if include_carrier:
        nodes.update(data.carrier_nodes)
    if include_controls:
        nodes.update(CONTROL_IDS)
    ordered_nodes = tuple(sorted(nodes))
    ordered_elements = tuple(sorted(data.physical_elements + (data.carrier_elements if include_carrier else ())))
    ctrl_element_names = ("P116163", "P116164") if include_controls else ()
    lines = [
        "TITRE",
        f"A09 first A00 weighted map small-motion fixture: {case}",
        "FINSF",
        "COOR_3D",
    ]
    for node in ordered_nodes:
        tokens = data.node_tokens[node]
        lines.append(f"N{node} {tokens[0]} {tokens[1]} {tokens[2]}")
    lines.append("FINSF")
    lines.append("TETRA10")
    for elem in ordered_elements:
        lines.append(f"M{elem} " + " ".join(f"N{node}" for node in data.element_nodes[elem]))
    lines.append("FINSF")
    if include_controls:
        lines.append("POI1")
        lines.extend((f"{ctrl_element_names[0]} N116163", f"{ctrl_element_names[1]} N116164", "FINSF"))
    for group_name, elem_ids in (("PHYS", data.physical_elements),
                                 ("CARR", data.carrier_elements if include_carrier else ())):
        if not elem_ids:
            continue
        lines.extend(("GROUP_MA", group_name))
        lines.extend(f"M{elem}" for elem in elem_ids)
        lines.append("FINSF")
    if include_controls:
        lines.extend(("GROUP_MA", "CTRL", *ctrl_element_names, "FINSF"))
    groups = [
        ("PHYS_NODES", data.physical_nodes),
        ("MAPPED_DEPENDENTS", tuple(sorted({node for node, _ in data.dependent_dofs}))),
    ]
    if include_controls:
        groups.extend((("NREF", (116163,)), ("NROT", (116164,))))
    if include_carrier:
        groups.append(("CARRIER_NODES", data.carrier_nodes))
    for name, members in groups:
        if not members:
            continue
        lines.extend(("GROUP_NO", name))
        lines.extend(f"N{node}" for node in members)
        lines.append("FINSF")
    for node in ordered_nodes:
        lines.extend(("GROUP_NO", f"N{node}", f"N{node}", "FINSF"))
    lines.append("FIN")
    path.write_text("\n".join(lines) + "\n")
    return {
        "mesh_node_order_source_ids": list(ordered_nodes),
        "physical_node_ids": list(data.physical_nodes),
        "carrier_node_ids": list(data.carrier_nodes) if include_carrier else [],
        "control_node_ids": list(CONTROL_IDS) if include_controls else [],
        "mesh_element_order_source_ids": list(ordered_elements),
        "physical_element_ids": list(data.physical_elements),
        "carrier_element_ids": list(data.carrier_elements) if include_carrier else [],
        "control_element_names": list(ctrl_element_names),
        "mesh_order_coordinates_mm": [[float(value) for value in data.node_tokens[node]] for node in ordered_nodes],
        "role_by_node_id": {str(node): ("physical" if node in data.physical_nodes else
                                        "carrier" if node in data.carrier_nodes else
                                        "reference_control" if node == 116163 else "rotation_control")
                            for node in ordered_nodes},
    }


def _equation_code(equations: tuple[tuple[EquationTerm, ...], ...]) -> str:
    chunks = ["map_equations = ("]
    for row in equations:
        nodes = [aster_node(term.node) for term in row]
        ddls = [f"'{DOF_TO_ASTER[term.dof]}'" for term in row]
        coefs = [term.coefficient for term in row]
        chunks.append("    _F(")
        chunks.append("        GROUP_NO=" + _format_tuple(nodes, "            "))
        chunks[-1] += ","
        chunks.append("        DDL=" + _format_tuple(ddls, "            "))
        chunks[-1] += ","
        chunks.append("        COEF_MULT=" + _format_tuple(coefs, "            "))
        chunks[-1] += ", COEF_IMPO=0.0,"
        chunks.append("    ),")
    chunks.append(")")
    return "\n".join(chunks)


def _load_code(load_rows: list[list[Any]]) -> str:
    data_rows = []
    for node, fx, fy, fz in load_rows:
        data_rows.append(f"    ({aster_node(int(node))}, {float(fx):.17g}, {float(fy):.17g}, {float(fz):.17g}),")
    return "force_data = (\n" + "\n".join(data_rows) + "\n)\n" + \
        "LOAD = AFFE_CHAR_MECA(\n    MODELE=MODEL,\n    FORCE_NODALE=tuple(\n" + \
        "        _F(GROUP_NO=node, FX=fx, FY=fy, FZ=fz) for node, fx, fy, fz in force_data\n" + \
        "    ),\n);"


def _carrier_code(data: SourceData) -> str:
    out = ["carrier_points = ("]
    for node in data.carrier_nodes:
        xyz = [float(token) for token in data.node_tokens[node]]
        x, y, z = xyz - PIVOT
        out.append(f"    ({aster_node(node)}, {x:.17g}, {y:.17g}, {z:.17g}),")
    out.extend((")", "carrier_equations = []", "for node, x, y, z in carrier_points:",
                "    carrier_equations.extend((",
                "        _F(GROUP_NO=(node, 'N116163', 'N116164', 'N116164'), DDL=('DX', 'DX', 'DY', 'DZ'), COEF_MULT=(1.0, -1.0, -z, y), COEF_IMPO=0.0),",
                "        _F(GROUP_NO=(node, 'N116163', 'N116164', 'N116164'), DDL=('DY', 'DY', 'DX', 'DZ'), COEF_MULT=(1.0, -1.0, z, -x), COEF_IMPO=0.0),",
                "        _F(GROUP_NO=(node, 'N116163', 'N116164', 'N116164'), DDL=('DZ', 'DZ', 'DX', 'DY'), COEF_MULT=(1.0, -1.0, -y, x), COEF_IMPO=0.0),",
                "    ))"))
    return "\n".join(out)


def write_comm(path: Path, data: SourceData, case: str, mass: dict[str, Any]) -> None:
    label = {"direct": "D", "mapped_no_carrier": "M", "mapped_carrier": "C"}[case]
    include_carrier = case == "mapped_carrier"
    include_map = case != "direct"
    model_parts = ["_F(GROUP_MA='PHYS', PHENOMENE='MECANIQUE', MODELISATION='3D')"]
    if include_carrier:
        model_parts.append("_F(GROUP_MA='CARR', PHENOMENE='MECANIQUE', MODELISATION='3D')")
    if include_map:
        model_parts.append("_F(GROUP_MA='CTRL', PHENOMENE='MECANIQUE', MODELISATION='DIS_TR')")
    material_parts = ["_F(GROUP_MA='PHYS', MATER=MAT_PHYS)"]
    if include_carrier:
        material_parts.append("_F(GROUP_MA='CARR', MATER=MAT_CARR)")
    dynamics = newmark_rotation_history()
    t_values = ", ".join(f"{row['time_s']:.17g}" for row in dynamics)
    kinematics = ""
    if include_map:
        kinematics += _equation_code(data.equations) + "\n\n"
        if include_carrier:
            kinematics += _carrier_code(data) + "\n\n"
        map_terms = "tuple(map_equations) + tuple(carrier_equations)" if include_carrier else "map_equations"
        kinematics += (
            "KIN = AFFE_CHAR_MECA(\n"
            "    MODELE=MODEL,\n"
            f"    LIAISON_DDL=tuple({map_terms}),\n"
            "    DDL_IMPO=_F(GROUP_NO=('NREF', 'NROT'), DRX=0.0, DRY=0.0, DRZ=0.0),\n"
            ");\n\n"
            "CARA = AFFE_CARA_ELEM(\n"
            "    MODELE=MODEL,\n"
            "    DISCRET=_F(GROUP_MA='CTRL', CARA='K_TR_D_N', VALE=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),\n"
            ");\n\n"
        )
    time_load = (
        "TIME_FUNCTION = DEFI_FONCTION(\n"
        "    NOM_PARA='INST',\n"
        f"    VALE=(0.0, 0.0, {T_END:.17g}, 1.0),\n"
        "    PROL_GAUCHE='CONSTANT',\n"
        "    PROL_DROITE='CONSTANT',\n"
        ");\n\n"
    )
    load_code = _load_code(mass["load_vector_final_tonne_mm_s2"])
    excit = "EXCIT=(_F(CHARGE=LOAD, FONC_MULT=TIME_FUNCTION),),"
    if include_map:
        excit = "EXCIT=(_F(CHARGE=KIN), _F(CHARGE=LOAD, FONC_MULT=TIME_FUNCTION)),"
    cara = "CARA_ELEM=CARA,\n    " if include_map else ""
    joined_models = ",\n        ".join(model_parts)
    material_groups = "('PHYS', 'CARR')" if include_carrier else "'PHYS'"
    comm = f"""# Generated by {Path(__file__).name}; source files are read-only.
# Case {case}; same physical load vector for direct and mapped representations.
# All lengths are mm, density tonne/mm^3, time s, force N.
DEBUT();

MAIL = LIRE_MAILLAGE(UNITE=20, FORMAT='ASTER');
MODEL = AFFE_MODELE(\n    MAILLAGE=MAIL,\n    AFFE=(\n        {joined_models},\n    ),\n);

MAT_PHYS = DEFI_MATERIAU(ELAS=_F(E={E_STEEL:.17g}, NU={NU_STEEL:.17g}, RHO={DENSITY_PHYS:.17g}));
MAT_CARR = DEFI_MATERIAU(ELAS=_F(E={E_STEEL:.17g}, NU={NU_STEEL:.17g}, RHO={DENSITY_CARRIER:.1f}));
CHMAT = AFFE_MATERIAU(MAILLAGE=MAIL, AFFE=({', '.join(material_parts)},));

{kinematics}{time_load}{load_code}

TSTEPS = DEFI_LIST_REEL(VALE=({t_values},));
RESULT_{label} = DYNA_NON_LINE(\n    MODELE=MODEL,\n    CHAM_MATER=CHMAT,\n    {cara}COMPORTEMENT=_F(GROUP_MA={material_groups}, RELATION='ELAS', DEFORMATION='PETIT'),\n    {excit}\n    INCREMENT=_F(LIST_INST=TSTEPS),\n    SCHEMA_TEMPS=_F(SCHEMA='NEWMARK', FORMULATION='DEPLACEMENT', BETA={BETA}, GAMMA={GAMMA}),\n    MASS_DIAG='NON',\n    NEWTON=_F(MATRICE='TANGENTE', REAC_ITER=1),\n    CONVERGENCE=_F(RESI_GLOB_RELA=1.0e-9, ITER_GLOB_MAXI=20),\n    ARCHIVAGE=_F(PAS_ARCH=1),\n    TITRE='A09 A00 first map small-motion inertia: {case}',\n);

IMPR_RESU(\n    FORMAT='MED',\n    UNITE=80,\n    RESU=_F(RESULTAT=RESULT_{label}, NOM_CHAM=('DEPL', 'VITE', 'ACCE')),\n);
"""
    comm += "\nFIN();\n"
    compile(comm, str(path), "exec")
    path.write_text(comm)


def write_export(path: Path, case: str) -> None:
    stem = case
    rows = [
        "P actions make_etude",
        "P mode interactif",
        "P ncpus 1",
        "P mpi_nbcpu 1",
        "P mpi_nbnoeud 1",
        "P time_limit 180",
        "P memory_limit 4096",
        f"F comm {stem}.comm D 1",
        f"F mail {stem}.mail D 20",
        f"F mess {stem}.mess R 6",
        f"F rmed {stem}.rmed R 80",
    ]
    path.write_text("\n".join(rows) + "\n")


def map_equation_digest(equations: tuple[tuple[EquationTerm, ...], ...]) -> str:
    serial = "\n".join(";".join(f"{term.node},{term.dof},{term.coefficient}" for term in row)
                       for row in equations).encode()
    return hashlib.sha256(serial).hexdigest()


def generate(output_root: Path) -> dict[str, Any]:
    data = load_source()
    mass = compute_mass_and_load(data)
    histories = newmark_rotation_history()
    xyz_body, _, xyz_carrier, _ = body_arrays(data)
    all_body_xyz = np.vstack((xyz_body, xyz_carrier))
    coord_keys = [tuple(float(x) for x in row) for row in all_body_xyz]
    require(len(coord_keys) == len(set(coord_keys)), "A00 physical/carrier coordinates are not unique")
    require(tuple(float(x) for x in PIVOT) not in set(coord_keys), "a body node coincides with the duplicate pivot controls")
    paths: dict[str, dict[str, str]] = {}
    cases: dict[str, Any] = {}
    for case in ("direct", "mapped_no_carrier", "mapped_carrier"):
        folder = output_root / case
        folder.mkdir(parents=True, exist_ok=True)
        mesh_info = write_mail(folder / f"{case}.mail", data, case)
        write_comm(folder / f"{case}.comm", data, case, mass)
        write_export(folder / f"{case}.export", case)
        cases[case] = {
            **mesh_info,
            "include_map": case != "direct",
            "include_carrier": case == "mapped_carrier",
            "expected_field_names": {
                "DEPL": f"RESULT_{ {'direct':'D','mapped_no_carrier':'M','mapped_carrier':'C'}[case] }DEPL".replace(" ", ""),
                "VITE": f"RESULT_{ {'direct':'D','mapped_no_carrier':'M','mapped_carrier':'C'}[case] }VITE".replace(" ", ""),
                "ACCE": f"RESULT_{ {'direct':'D','mapped_no_carrier':'M','mapped_carrier':'C'}[case] }ACCE".replace(" ", ""),
            },
        }
        paths[case] = {}
        for suffix in ("mail", "comm", "export"):
            artifact = folder / f"{case}.{suffix}"
            paths[case][suffix] = hashlib.sha256(artifact.read_bytes()).hexdigest()
    oracle = {
        "schema": "code_aster_actual_a09_first_map_fpg15_inertia_fixture/v1",
        "status": "PREPARED_OFFLINE_NOT_FROZEN_NOT_NATIVE_RUN",
        "solver_execution": False,
        "units": "mm, tonne, s, N; angles are dimensionless radians in the ROT node's translational DOFs",
        "scope": "one A00 first bolt/nut actual weighted-map small-motion Y-rotation check; no contact, wood, thread, strength, or joint acceptance",
        "runtime_target": {
            "container": "simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5",
            "version": "Code_Aster 17.4.0",
            "native_calls_by_fixture_author": False,
        },
        "source_files": {name: {"path": str(SOURCE / name), "sha256": data.source_hashes[name]} for name in PINS},
        "source_bodies": {
            "physical": BODY,
            "carrier": CARRIER,
            "physical_elements": len(data.physical_elements),
            "physical_nodes": len(data.physical_nodes),
            "carrier_elements": len(data.carrier_elements),
            "carrier_nodes": len(data.carrier_nodes),
            "physical_material": data.source_materials["STEEL_ELASTIC_DIAGNOSTIC"],
            "carrier_material": data.source_materials["NUT_ZERO_MASS_RIGID_CARRIER"],
        },
        "controls": {
            "reference_node": 116163,
            "rotation_node": 116164,
            "both_source_coordinates_mm": [float(x) for x in PIVOT],
            "coincident_control_coordinate_requires_group_aware_or_unique_body_node_mapping": True,
            "expected_reference_translation": [0.0, 0.0, 0.0],
            "expected_rotation_translation_axis": "DY",
            "rotation_node_DEPL_VITE_ACCE_expected_from_rotation_history": True,
            "rotation_control_units_note": "The unchanged source equations use translations 1..3 on both control nodes; NROT DX/DY/DZ encode theta_x/theta_y/theta_z in radians.",
        },
        "source_map": {
            "source_path": str(SOURCE / "nut-coupling.inp"),
            "source_sha256": data.source_hashes["nut-coupling.inp"],
            "first_six_a00_rows_term_counts": [len(row) for row in data.equations],
            "dependent_dofs_node_and_abaqus_dof": [list(row) for row in data.dependent_dofs],
            "exact_ordered_term_digest_sha256": map_equation_digest(data.equations),
            "preserved_coefficients": True,
            "Code_Aster_translation": "each source node/DOF/coefficient term is emitted in the same order to LIAISON_DDL singleton GROUP_NO/DDL/COEF_MULT; source DOF 1/2/3 maps to DX/DY/DZ",
            "source_affine_audit": str(ROOT / "docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/source-map-affine-audit.json"),
        },
        "carrier_map": {
            "source_rigid_node_set": "M03_A00_NUT_RIGID_NODES",
            "source_rigid_carrier_sha256": data.source_hashes["rigid-carriers.inp"],
            "formulation": "explicit linear small-motion rigid field about the exact source pivot, controlled by NREF translations and NROT translations; no finite-rotation claim",
            "source_controls_are_not_merged_or_moved": True,
        },
        "time_integration": {
            "scheme": "Code_Aster DYNA_NON_LINE implicit Newmark average acceleration",
            "beta": BETA,
            "gamma": GAMMA,
            "consistent_mass": True,
            "MASS_DIAG": "NON",
            "time_end_s": T_END,
            "increments": N_STEPS,
            "dt_s": DT,
            "angular_acceleration_law": f"alpha_y(t)=c*t, c={ACCEL_RAMP_SLOPE:.17g} rad/s^3",
            "target_end_angle_rad": THETA_END_TARGET,
            "rotation_history": histories,
        },
        "mass_reference": mass,
        "cases": cases,
        "input_file_sha256": paths,
        "historical_author_tolerance_proposal_not_adopted": {
            "field_comparison": "propose per-value |actual-expected| <= absolute_floor + relative_tolerance*|expected|; floor based on output resolution and global state scale; parent must freeze per-field floors/tolerances before any native run",
            "direct_to_oracle_and_mapped_to_oracle": "initial proposal rel=2e-4 on nonzero fields with DAT/MED precision-derived abs floor; inspect output precision and parent freeze before run",
            "mapped_to_mapped_plus_carrier": "initial proposal rel=2e-4 on nonzero physical fields with absolute floor; compare all physical nodes/states",
            "carrier_rigid_field": "initial proposal rel=2e-4 on nonzero components with zero-component absolute floor; no finite-rotation response test",
            "mass_energy": "initial proposal rel=2e-4 for nonzero physical energy; direct FPG15 local-mass quadratic form from actual VITE fields",
            "status": "proposal only; no tolerance is frozen by this fixture author",
        },
        "limitations": [
            "One actual A00 six-row map and one A00 nut carrier only.",
            "Small-angle Y rotation and implicit inertia mapping only; the carrier equations are linear PETIT relations.",
            "FPG15 is the pinned Code_Aster 17.4 ordinary 3D TETRA10 mass rule; this does not establish other elements or modes.",
            "The fixture does not model contact, preload, thread engagement, joint load path, resistance, timber, or candidate acceptance.",
            "The solver authoring environment did not launch Code_Aster; parent owns readiness, freeze, serialized runs, extraction, and interpretation.",
        ],
    }
    oracle_path = HERE / "oracle.json"
    oracle_path.write_text(json.dumps(oracle, indent=2, sort_keys=True, allow_nan=False) + "\n")
    manifest = {
        "schema": "code_aster_actual_a09_first_map_input_manifest/v1",
        "generator": str(Path(__file__).resolve()),
        "generated_artifacts": {
            case: {suffix: digest for suffix, digest in case_hashes.items()}
            for case, case_hashes in paths.items()
        },
        "oracle_sha256": sha256(oracle_path),
        "source_sha256": data.source_hashes,
        "solver_execution": False,
        "mesh_order_rule": "Source node IDs ascending within selected bodies, then all included controls; the oracle records the exact order and coordinates. MED postprocessing must map body nodes by unique coordinates, treating the two coincident controls as ambiguous and reading them through NREF/NROT groups if used.",
    }
    (HERE / "input-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return oracle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=HERE / "input",
                        help="owned output directory for generated case decks")
    args = parser.parse_args()
    oracle = generate(args.output_root)
    print(json.dumps({
        "status": oracle["status"],
        "output_root": str(args.output_root),
        "physical_nodes": oracle["source_bodies"]["physical_nodes"],
        "carrier_nodes": oracle["source_bodies"]["carrier_nodes"],
        "elements": [oracle["source_bodies"]["physical_elements"], oracle["source_bodies"]["carrier_elements"]],
        "fpg15_mass_tonne": oracle["mass_reference"]["physical_mass_tonne"],
        "fpg15_modal_mass_tonne_mm2": oracle["mass_reference"]["rotation_y_modal_mass_tonne_mm2"],
        "load_sha256": oracle["mass_reference"]["load_vector_final_sha256_le_nodeid_fx_fy_fz"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
