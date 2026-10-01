#!/usr/bin/env python3
"""Reproduce the offline, source-bound one-axis implicit current-map inputs.

This producer only extracts two pinned C3D10 bodies, creates their three input
decks, and records the pinned-quadrature reference. It never invokes CalculiX.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import tarfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE = HERE.parent
SOURCE = BASE / "ordinary-port-motion-attempt09-common-map"
ARCHIVE = (BASE / "ordinary-external-force-transient-attempt04-diagnostic"
           / "build-attempt02" / "source.tar.bz2")
BODY = "M00_A00_BOLT_HEAD_PLUS_SHAFT_UNION"
CARRIER = "M03_A00_NUT"
CONTROL_IDS = (116163, 116164)
PIVOT = (134.5, 1.178456090256, 410.856889078727)
RHO = 7.85e-9
DT = 0.001
TOTAL_TIME = 0.01
STATES = 10
ALPHA_RAMP = 1.2  # rad/s^3
ALPHA_FINAL = ALPHA_RAMP * TOTAL_TIME

PINS = {
    "mesh.inp": "117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803",
    "mesh.json": "1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07",
    "materials.inp": "e0063d0ebc2232b6699f020488944617b1f44f7bfa38f931f47907d08202a3bb",
    "nut-coupling.inp": "af5b36dce4e85b19a6a5b4805dd6b00259da88ccc1a849769642db2ecbf62903",
    "nut-coupling.json": "568ade2437181bc8e9398f64a2818bbf8bd3f46a64dae9639bf363cb68bec960",
    "rigid-carriers.inp": "a15eebb0537a4a3f096531f2c4e48ecd26b6ec53908d61178ead7dfe3bc27815",
}
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
SOURCE_MEMBERS = (
    "e_c3d.f", "gauss.f", "mafillsm.f", "nonlinmpc.f", "rigidbodys.f",
    "rigidmpc.f", "shape10tet.f",
)
CAPTURE_BASELINE_FILES = {
    "DAT": (BASE / "implicit-c3d10-mpc-known-answer-attempt01" / "output"
            / "direct" / "coupon.dat",
            "cf7dc4fbf6e88cbddd7b3799c32ed35d7962a650a9307046673062330549b5b6"),
    "FRD": (BASE / "implicit-c3d10-mpc-known-answer-attempt01" / "output"
            / "direct" / "coupon.frd",
            "d36ba150d42408c3050ad512c0ac0e706ea696d7f994448725de64c6b13c80ad"),
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def source_member_hashes() -> dict[str, str]:
    result = {}
    with tarfile.open(ARCHIVE, "r:bz2") as archive:
        for name in SOURCE_MEMBERS:
            member = archive.extractfile(f"./CalculiX/ccx_2.23/src/{name}")
            if member is None:
                raise ValueError(f"missing pinned source member: {name}")
            result[name] = sha256_bytes(member.read())
    return result


def check_source_pins() -> tuple[dict, dict]:
    if sha256_file(ARCHIVE) != ARCHIVE_SHA256:
        raise ValueError("pinned CalculiX 2.23 source archive hash changed")
    source_hashes = {}
    for name, expected in PINS.items():
        path = SOURCE / name
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"pinned source input changed: {path}: {actual}")
        source_hashes[name] = actual
    for kind, (path, expected) in CAPTURE_BASELINE_FILES.items():
        if sha256_file(path) != expected:
            raise ValueError(f"pinned {kind} output-size baseline changed: {path}")
    return source_hashes, source_member_hashes()


def parse_selected_mesh(mesh_report: dict) -> tuple[dict[int, str], dict[int, str], dict[int, str]]:
    bodies = mesh_report["bodies"]
    main = bodies[BODY]
    carrier = bodies[CARRIER]
    main_node_ids = set(map(int, main["nodes"]))
    carrier_node_ids = set(map(int, carrier["nodes"]))
    main_element_ids = set(map(int, main["elements"]))
    carrier_element_ids = set(map(int, carrier["elements"]))
    if main_node_ids & carrier_node_ids or main_element_ids & carrier_element_ids:
        raise ValueError("pinned body ownership overlaps")

    nodes: dict[int, str] = {}
    main_elements: dict[int, str] = {}
    carrier_elements: dict[int, str] = {}
    mode = None
    for line in (SOURCE / "mesh.inp").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            mode = stripped.split(",", 1)[0].upper()
            continue
        if mode not in ("*NODE", "*ELEMENT"):
            continue
        fields = [field.strip() for field in line.split(",")]
        record_id = int(fields[0])
        if mode == "*NODE" and record_id in main_node_ids | carrier_node_ids:
            if len(fields) != 4 or record_id in nodes:
                raise ValueError(f"invalid or duplicate selected node row: {line}")
            nodes[record_id] = line
        elif mode == "*ELEMENT":
            if record_id in main_element_ids:
                if len(fields) != 11 or record_id in main_elements:
                    raise ValueError(f"invalid or duplicate selected M00 element: {line}")
                main_elements[record_id] = line
            elif record_id in carrier_element_ids:
                if len(fields) != 11 or record_id in carrier_elements:
                    raise ValueError(f"invalid or duplicate selected M03 element: {line}")
                carrier_elements[record_id] = line

    if set(nodes) != main_node_ids | carrier_node_ids:
        raise ValueError("selected node extraction differs from pinned body reports")
    if set(main_elements) != main_element_ids or set(carrier_elements) != carrier_element_ids:
        raise ValueError("selected element extraction differs from pinned body reports")
    main_connectivity = {int(value.strip())
                         for row in main_elements.values()
                         for value in row.split(",")[1:]}
    carrier_connectivity = {int(value.strip())
                            for row in carrier_elements.values()
                            for value in row.split(",")[1:]}
    if main_connectivity != main_node_ids or carrier_connectivity != carrier_node_ids:
        raise ValueError("body node sets do not equal the exact C3D10 connectivity")
    return nodes, main_elements, carrier_elements


def normalize_node_line(line: str) -> tuple[str, tuple[float, float, float], dict]:
    """Emit exactly the coordinate strings the pinned F20.0 reader consumes.

    A few source mesh literals are longer than 20 characters. CalculiX reads
    only characters 1:20 from each coordinate textpart, so retain that exact
    parser-visible prefix and remove only the suffix the original reader
    ignored. This keeps the native coordinate values identical to the pinned
    source input while making the field-width contract explicit.
    """
    fields = [part.strip() for part in line.split(",")]
    if len(fields) != 4 or len(fields[0]) > 10:
        raise ValueError(f"invalid source *NODE row: {line}")
    node_id = int(fields[0])
    emitted = []
    source_values = []
    parsed_values = []
    overwidth = 0
    for literal in fields[1:]:
        parser_text = literal[:20]
        if len(literal) > 20:
            overwidth += 1
        try:
            literal_value = float(literal)
            parsed_value = float(parser_text)
        except ValueError as error:
            raise ValueError(f"coordinate field is not valid within F20.0 width: {line}") from error
        if len(parser_text) > 20 or not math.isfinite(parsed_value):
            raise ValueError(f"coordinate field exceeds or fails F20.0: {line}")
        emitted.append(parser_text)
        source_values.append(literal_value)
        parsed_values.append(parsed_value)
    normalized = f"{node_id},{','.join(emitted)}"
    audit = {
        "source_literal_xyz_mm": source_values,
        "parser_visible_xyz_mm": parsed_values,
        "overwidth_coordinate_field_count": overwidth,
        "max_abs_source_literal_vs_parser_visible_mm": max(
            abs(a - b) for a, b in zip(source_values, parsed_values)),
    }
    return normalized, tuple(parsed_values), audit


def parse_control_nodes() -> dict[int, str]:
    wanted = set(CONTROL_IDS)
    found = {}
    mode = None
    for line in (SOURCE / "nut-coupling.inp").read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("**"):
            continue
        if stripped.startswith("*"):
            mode = stripped.split(",", 1)[0].upper()
            continue
        if mode == "*NODE":
            fields = [field.strip() for field in line.split(",")]
            node_id = int(fields[0])
            if node_id in wanted:
                if len(fields) != 4 or node_id in found:
                    raise ValueError(f"invalid or duplicate control node: {line}")
                found[node_id] = line
    if set(found) != wanted:
        raise ValueError("could not extract both A00 control nodes")
    coords = {node: tuple(map(float, found[node].split(",")[1:])) for node in CONTROL_IDS}
    if any(max(abs(a - b) for a, b in zip(coords[node], PIVOT)) > 2e-13
           for node in CONTROL_IDS):
        raise ValueError("A00 REF/ROT control coordinates differ from pinned pivot")
    return found


def parse_equation_cards(coupling_report: dict,
                         physical_node_ids: set[int]) -> tuple[list[str], list[dict]]:
    lines = (SOURCE / "nut-coupling.inp").read_text().splitlines(keepends=True)
    cards: list[list[str]] = []
    parsed: list[dict] = []
    i = 0
    while i < len(lines):
        if lines[i].strip().upper() != "*EQUATION":
            i += 1
            continue
        card = [lines[i]]
        i += 1
        while i < len(lines) and (not lines[i].strip() or lines[i].lstrip().startswith("**")):
            card.append(lines[i])
            i += 1
        if i == len(lines):
            raise ValueError("truncated *EQUATION card count")
        count_line = lines[i]
        count = int(count_line.strip())
        card.append(count_line)
        i += 1
        tokens: list[str] = []
        data_lines: list[str] = []
        while len(tokens) < 3 * count and i < len(lines):
            raw = lines[i]
            if raw.strip().startswith("*"):
                raise ValueError("truncated *EQUATION term list")
            data_lines.append(raw)
            tokens.extend(part.strip() for part in raw.strip().split(",") if part.strip())
            i += 1
        if len(tokens) != 3 * count:
            raise ValueError("equation term count does not match source row")
        terms = []
        for t in range(count):
            node = int(tokens[3 * t])
            dof = int(tokens[3 * t + 1])
            coefficient = float(tokens[3 * t + 2])
            terms.append((node, dof, coefficient))
        card.extend(data_lines)
        cards.append(card)
        parsed.append({"term_count": count, "terms": terms,
                       "dependent": terms[0][:2]})

    expected = coupling_report["equation_cards"][:6]
    if len(cards) < 6 or len(expected) != 6:
        raise ValueError("A00 current map does not contain six source equations")
    selected = cards[:6]
    selected_parsed = parsed[:6]
    if [row["term_count"] for row in selected_parsed] != [row["term_count"] for row in expected]:
        raise ValueError("A00 equation term counts differ from the pinned report")
    if [row["dependent"] for row in selected_parsed] != [
            (row["dependent_node_id"], row["dependent_dof"]) for row in expected]:
        raise ValueError("A00 source equation dependency order differs from its report")
    dep_dofs = [row["dependent"] for row in selected_parsed]
    if len(set(dep_dofs)) != 6:
        raise ValueError("A00 current map has colliding dependent DOFs")
    allowed_nodes = physical_node_ids | set(CONTROL_IDS)
    all_nodes = {node for row in selected_parsed for node, _, _ in row["terms"]}
    if not all_nodes <= allowed_nodes:
        raise ValueError("A00 map rows reference nodes outside M00 and its controls")
    control_dofs = {(node, dof) for row in selected_parsed
                     for node, dof, _ in row["terms"] if node in CONTROL_IDS}
    expected_control_dofs = {(node, dof) for node in CONTROL_IDS for dof in (1, 2, 3)}
    if control_dofs != expected_control_dofs:
        raise ValueError("A00 map rows do not reference all six free controls")
    return ["".join(card) for card in selected], selected_parsed


def parse_rigid_nset(carrier_node_ids: set[int]) -> tuple[str, str]:
    lines = (SOURCE / "rigid-carriers.inp").read_text().splitlines(keepends=True)
    start = next((i for i, line in enumerate(lines)
                  if line.strip().upper() == "*NSET,NSET=M03_A00_NUT_RIGID_NODES"), None)
    if start is None:
        raise ValueError("pinned M03 rigid carrier NSET not found")
    block = [lines[start]]
    i = start + 1
    ids = []
    while i < len(lines) and not lines[i].strip().startswith("*"):
        block.append(lines[i])
        ids.extend(int(token.strip()) for token in lines[i].split(",") if token.strip())
        i += 1
    if set(ids) != carrier_node_ids or len(ids) != len(carrier_node_ids):
        raise ValueError("pinned rigid carrier NSET differs from M03_A00 node membership")
    rigid_card = "*RIGID BODY,NSET=M03_A00_NUT_RIGID_NODES,REF NODE=116163,ROT NODE=116164\n"
    if rigid_card.strip().upper() not in {
            line.strip().upper() for line in lines}:
        raise ValueError("pinned A00 rigid-body control card not found")
    return "".join(block), rigid_card


def audit_source_equation_widths(equation_cards: list[str], parsed: list[dict]) -> dict:
    max_node_chars = 0
    max_dof_chars = 0
    max_coefficient_chars = 0
    for card, parsed_card in zip(equation_cards, parsed):
        lines = [line.strip() for line in card.splitlines()
                 if line.strip() and not line.lstrip().startswith("**")]
        if lines[0].upper() != "*EQUATION":
            raise ValueError("equation source card header changed during width audit")
        count = int(lines[1])
        tokens = [part.strip() for line in lines[2:]
                  for part in line.split(",") if part.strip()]
        if len(tokens) != 3 * count:
            raise ValueError("equation source card token count changed during width audit")
        for index in range(count):
            node, dof, coefficient = tokens[3 * index:3 * index + 3]
            max_node_chars = max(max_node_chars, len(node))
            max_dof_chars = max(max_dof_chars, len(dof))
            max_coefficient_chars = max(max_coefficient_chars, len(coefficient))
            if len(node) > 10 or len(dof) > 10 or len(coefficient) > 20:
                raise ValueError("pinned current-map equation field exceeds CCX parser width")
            if (int(node), int(dof)) != parsed_card["terms"][index][:2]:
                raise ValueError("equation field changed during width audit")
    return {"node_id_max_chars": max_node_chars,
            "dof_max_chars": max_dof_chars,
            "coefficient_max_chars": max_coefficient_chars,
            "node_id_limit_chars": 10, "dof_limit_chars": 10,
            "coefficient_limit_chars": 20,
            "source_equation_rows_byte_preserved": True}


def cload_text(value: float) -> str:
    text = f"{value:.13e}"
    if len(text) > 20:
        raise ValueError(f"CLOAD value field exceeds F20.0 width: {text}")
    if float(text) == 0.0 and value != 0.0:
        raise ValueError("formatted CLOAD underflowed to zero")
    return text


def audit_deck_numeric_widths(deck: bytes) -> dict:
    maximum_chars = 0
    maximum_field = ""
    maximum_line = ""
    keyword = ""
    for line in deck.decode("ascii").splitlines():
        if not line:
            continue
        if line.lstrip().startswith("*"):
            keyword = line.strip().split(",", 1)[0].upper()
            continue
        if keyword == "*HEADING":
            continue
        for field in line.split(","):
            token = field.strip()
            if len(token) > maximum_chars:
                maximum_chars = len(token)
                maximum_field = token
                maximum_line = line
            if len(token) > 20:
                raise ValueError(f"numeric input field exceeds a 20-character parser field: {line}")
    return {"maximum_comma_field_chars": maximum_chars,
            "maximum_comma_field": maximum_field,
            "maximum_field_line": maximum_line,
            "maximum_numeric_field_chars": 20}


def shape10(xi: float, eta: float, zeta: float) -> tuple[list[float], list[list[float]]]:
    bary = [1.0 - xi - eta - zeta, xi, eta, zeta]
    dbary = [(-1.0, -1.0, -1.0), (1.0, 0.0, 0.0),
             (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    n = [value * (2.0 * value - 1.0) for value in bary]
    dn = [[(4.0 * bary[i] - 1.0) * dbary[i][axis] for axis in range(3)]
          for i in range(4)]
    for first, second in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)):
        n.append(4.0 * bary[first] * bary[second])
        dn.append([4.0 * (dbary[first][axis] * bary[second]
                          + bary[first] * dbary[second][axis]) for axis in range(3)])
    return n, dn


def determinant3(matrix: list[list[float]]) -> float:
    return (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1])
            - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0])
            + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]))


def cross(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def add3(dst: list[float], value: tuple[float, float, float], scale: float) -> None:
    for axis in range(3):
        dst[axis] += scale * value[axis]


def integrate_body(node_coordinates: dict[int, tuple[float, float, float]],
                   element_lines: dict[int, str], density: float = RHO) -> dict:
    low, high = 0.138196601125011, 0.585410196624968
    points = ((low, low, low), (high, low, low), (low, high, low), (low, low, high))
    # Use the pinned source's literal quadrature weight, not mathematical 1/24.
    weight = 0.041666666666667
    local_loads = {node: [0.0, 0.0, 0.0] for node in node_coordinates}
    volume = 0.0
    first_moment = [0.0, 0.0, 0.0]
    inertia = [[0.0] * 3 for _ in range(3)]
    minimum_jacobian = math.inf
    maximum_jacobian = 0.0
    for element_id in sorted(element_lines):
        conn = [int(v.strip()) for v in element_lines[element_id].split(",")[1:]]
        if len(conn) != 10:
            raise ValueError(f"element {element_id} is not C3D10")
        xyz = [node_coordinates[node] for node in conn]
        for q in points:
            n, dn = shape10(*q)
            if abs(sum(n) - 1.0) > 3e-15 or any(abs(sum(dn[i][a] for i in range(10))) > 3e-15
                                                 for a in range(3)):
                raise ValueError("C3D10 shape function partition check failed")
            jac = [[sum(xyz[i][row] * dn[i][col] for i in range(10))
                    for col in range(3)] for row in range(3)]
            det = determinant3(jac)
            if det <= 0.0:
                raise ValueError(f"nonpositive Jacobian in element {element_id}: {det}")
            minimum_jacobian = min(minimum_jacobian, det)
            maximum_jacobian = max(maximum_jacobian, det)
            dvol = det * weight
            xq = tuple(sum(n[i] * xyz[i][a] for i in range(10)) for a in range(3))
            r = tuple(xq[a] - PIVOT[a] for a in range(3))
            direction = cross((0.0, 1.0, 0.0), r)
            volume += dvol
            for a in range(3):
                first_moment[a] += dvol * xq[a]
            r2 = sum(value * value for value in r)
            for a in range(3):
                for b in range(3):
                    inertia[a][b] += density * dvol * ((r2 if a == b else 0.0) - r[a] * r[b])
            accel_per_rad_s2 = direction
            for i, node_id in enumerate(conn):
                add3(local_loads[node_id], accel_per_rad_s2, density * dvol * n[i] * ALPHA_FINAL)

    if volume <= 0 or minimum_jacobian == math.inf:
        raise ValueError("body quadrature produced no positive volume")
    # State all-node geometry bounds on the actual F20.0 coordinates emitted
    # in the deck. The quadrature positions above are not mesh-node extrema.
    radii = [math.sqrt(sum((xyz[a] - PIVOT[a]) ** 2 for a in range(3)))
             for xyz in node_coordinates.values()]
    direction_magnitudes = [math.hypot(xyz[2] - PIVOT[2], xyz[0] - PIVOT[0])
                            for xyz in node_coordinates.values()]
    maximum_radius = max(radii)
    maximum_direction = max(direction_magnitudes)
    mass = density * volume
    centroid = [value / volume for value in first_moment]
    return {"volume_mm3": volume, "mass_tonne": mass, "density_tonne_per_mm3": density,
            "centroid_mm": centroid,
            "inertia_about_pivot_tonne_mm2": inertia,
            "rotation_y_modal_mass_tonne_mm2": inertia[1][1],
            "minimum_jacobian_mm3": minimum_jacobian,
            "maximum_jacobian_mm3": maximum_jacobian,
            "maximum_radius_mm": maximum_radius,
            "maximum_rotation_direction_mm": maximum_direction,
            "load_final_by_node": local_loads}


def cross_matrix_check(body: dict, nodes: dict[int, tuple[float, float, float]]) -> dict:
    loads = body["load_final_by_node"]
    resultant = [sum(loads[n][a] for n in loads) for a in range(3)]
    moment = [0.0, 0.0, 0.0]
    for node_id, xyz in nodes.items():
        r = tuple(xyz[a] - PIVOT[a] for a in range(3))
        m = cross(r, tuple(loads[node_id]))
        for a in range(3):
            moment[a] += m[a]
    expected_resultant = tuple(body["mass_tonne"] * ALPHA_FINAL * value
                               for value in cross((0.0, 1.0, 0.0),
                                                  tuple(body["centroid_mm"][a] - PIVOT[a]
                                                        for a in range(3))))
    expected_moment = [body["inertia_about_pivot_tonne_mm2"][a][1] * ALPHA_FINAL
                       for a in range(3)]
    if max(abs(resultant[a] - expected_resultant[a]) for a in range(3)) > 2e-13:
        raise ValueError("quadrature nodal force resultant does not match the source mass")
    if max(abs(moment[a] - expected_moment[a]) for a in range(3)) > 2e-12:
        raise ValueError("quadrature nodal force moment does not match source inertia")
    return {"resultant_N": resultant, "expected_resultant_N": expected_resultant,
            "moment_about_pivot_Nmm": moment, "expected_moment_about_pivot_Nmm": expected_moment}


def resultant_and_moment(loads: dict[int, list[float]],
                         nodes: dict[int, tuple[float, float, float]]) -> tuple[list[float], list[float]]:
    resultant = [sum(loads[node][axis] for node in loads) for axis in range(3)]
    moment = [0.0, 0.0, 0.0]
    for node_id, xyz in nodes.items():
        r = tuple(xyz[a] - PIVOT[a] for a in range(3))
        m = cross(r, tuple(loads[node_id]))
        for axis in range(3):
            moment[axis] += m[axis]
    return resultant, moment


def vector_digest(loads: dict[int, list[float]]) -> str:
    rows = [f"{node},{loads[node][0]:.17e},{loads[node][1]:.17e},{loads[node][2]:.17e}"
            for node in sorted(loads)]
    return sha256_bytes(("\n".join(rows) + "\n").encode("ascii"))


def audit_load_serialization(body: dict,
                             nodes: dict[int, tuple[float, float, float]]) -> dict:
    exact = body["load_final_by_node"]
    written = body["written_load_by_node"]
    intended_resultant, intended_moment = resultant_and_moment(exact, nodes)
    written_resultant, written_moment = resultant_and_moment(written, nodes)
    abs_errors = []
    rel_errors = []
    raw_rows = []
    max_chars = 0
    for node in sorted(exact):
        for axis in range(3):
            value = exact[node][axis]
            emitted = written[node][axis]
            if value != 0.0:
                field = cload_text(value)
                max_chars = max(max_chars, len(field))
                if len(field) > 20 or float(field[:20]) != emitted:
                    raise ValueError("CLOAD value would be truncated by the pinned F20.0 reader")
                raw_rows.append(f"{node},{axis + 1},{field}")
                abs_errors.append(abs(value - emitted))
                rel_errors.append(abs(value - emitted) / abs(value))
            elif emitted != 0.0:
                raise ValueError("zero load component became nonzero during serialization")
    return {
        "format": "13 digits after decimal in scientific notation; at most 20 characters",
        "solver_parser": "cloads.f reads textpart(3)(1:20) with F20.0",
        "max_field_chars": max_chars,
        "record_count": len(raw_rows),
        "intended_full_precision_vector_sha256_node_fx_fy_fz": vector_digest(exact),
        "emitted_parser_value_vector_sha256_node_fx_fy_fz": vector_digest(written),
        "emitted_cload_rows_sha256": sha256_bytes(("\n".join(raw_rows) + "\n").encode("ascii")),
        "max_component_abs_rounding_error_N": max(abs_errors, default=0.0),
        "max_component_relative_rounding_error": max(rel_errors, default=0.0),
        "intended_resultant_N": intended_resultant,
        "emitted_resultant_N": written_resultant,
        "resultant_delta_N": [written_resultant[a] - intended_resultant[a] for a in range(3)],
        "intended_moment_about_pivot_Nmm": intended_moment,
        "emitted_moment_about_pivot_Nmm": written_moment,
        "moment_delta_Nmm": [written_moment[a] - intended_moment[a] for a in range(3)],
    }


def id_rows(ids: list[int], per_line: int = 16) -> list[str]:
    return [",".join(str(value) for value in ids[start:start + per_line])
            for start in range(0, len(ids), per_line)]


def render_case(name: str, *, include_map: bool, include_carrier: bool,
                node_lines: dict[int, str], main_elements: dict[int, str],
                carrier_elements: dict[int, str], controls: dict[int, str],
                equations: list[str], carrier_nset: str, rigid_card: str,
                body_reference: dict, carrier_reference: dict) -> bytes:
    if include_carrier and (carrier_reference["density_tonne_per_mm3"] != 0.0
                            or carrier_reference["mass_tonne"] != 0.0
                            or carrier_reference["volume_mm3"] <= 0.0):
        raise ValueError("M03 carrier output case must remain positive-volume and zero-density")
    physical_ids = sorted(node_lines_id for node_lines_id in node_lines
                          if node_lines_id in body_reference["physical_node_ids"])
    carrier_ids = sorted(body_reference["carrier_node_ids"] if include_carrier else [])
    control_ids = list(CONTROL_IDS) if include_map else []
    observe_ids = sorted(set(physical_ids) | set(carrier_ids) | set(control_ids))
    selected_nodes = {node: node_lines[node] for node in physical_ids}
    if include_carrier:
        selected_nodes.update({node: node_lines[node] for node in carrier_ids})
    if include_map:
        selected_nodes.update(controls)

    lines = [
        "*HEADING",
        f"Implicit current-map one-axis known-answer fixture; case={name}; no joint acceptance.",
        "*NODE",
        *[selected_nodes[node] for node in sorted(selected_nodes)],
        f"*ELEMENT,TYPE=C3D10,ELSET={BODY}",
        *[main_elements[element] for element in sorted(main_elements)],
    ]
    if include_carrier:
        lines.extend([f"*ELEMENT,TYPE=C3D10,ELSET={CARRIER}",
                      *[carrier_elements[element] for element in sorted(carrier_elements)]])
    lines.extend(["*NSET,NSET=N_PHYSICAL", *id_rows(physical_ids)])
    if include_map:
        lines.extend(["*NSET,NSET=NUT_00_RIGID_CONTROL", *id_rows(control_ids)])
    if include_carrier:
        lines.extend([carrier_nset.rstrip("\n")])
    lines.extend(["*NSET,NSET=N_OBSERVE", *id_rows(observe_ids)])
    if include_map:
        lines.extend(card.rstrip("\n") for card in equations)
    if include_carrier:
        lines.append(rigid_card.rstrip("\n"))
    lines.extend([
        "*MATERIAL,NAME=STEEL_ELASTIC_DIAGNOSTIC",
        "*DENSITY",
        "7.85e-9",
        "*ELASTIC,TYPE=ISO",
        "200000,0.3",
        f"*SOLID SECTION,ELSET={BODY},MATERIAL=STEEL_ELASTIC_DIAGNOSTIC",
    ])
    if include_carrier:
        lines.extend([
            "*MATERIAL,NAME=NUT_ZERO_MASS_RIGID_CARRIER",
            "*DENSITY",
            "0",
            "*ELASTIC",
            "200000,0.3",
            f"*SOLID SECTION,ELSET={CARRIER},MATERIAL=NUT_ZERO_MASS_RIGID_CARRIER",
        ])
    lines.extend([
        "*AMPLITUDE,NAME=ANGULAR_ACCELERATION_RAMP",
        f"0.,0.,{TOTAL_TIME:.12g},1.",
        "*STEP,NLGEOM,INC=10",
        "*DYNAMIC,DIRECT,ALPHA=0.",
        f"{DT:.12g},{TOTAL_TIME:.12g}",
        "*CLOAD,AMPLITUDE=ANGULAR_ACCELERATION_RAMP",
    ])
    load_rows = []
    written_loads = {node_id: [0.0, 0.0, 0.0]
                     for node_id in body_reference["load_final_by_node"]}
    for node_id in sorted(body_reference["load_final_by_node"]):
        force = body_reference["load_final_by_node"][node_id]
        for dof in (1, 3):
            value = force[dof - 1]
            if value != 0.0:
                text = cload_text(value)
                written_loads[node_id][dof - 1] = float(text)
                load_rows.append(f"{node_id},{dof},{text}")
    body_reference["written_load_by_node"] = written_loads
    lines.extend(load_rows)
    lines.extend([
        "*NODE PRINT,NSET=N_OBSERVE,FREQUENCY=1",
        "U,V",
        "*NODE FILE,NSET=N_OBSERVE,FREQUENCY=1",
        "U,V",
        f"*EL PRINT,ELSET={BODY},TOTALS=ONLY,FREQUENCY=1",
        "ELSE,ELKE,EMAS,EVOL",
    ])
    if include_carrier:
        lines.extend([f"*EL PRINT,ELSET={CARRIER},TOTALS=ONLY,FREQUENCY=1",
                      "ELSE,ELKE,EMAS,EVOL"])
    lines.extend(["*END STEP", ""])
    return ("\n".join(lines)).encode("ascii")


def build() -> tuple[dict[str, bytes], dict]:
    source_hashes, member_hashes = check_source_pins()
    mesh_report = json.loads((SOURCE / "mesh.json").read_text())
    coupling_report = json.loads((SOURCE / "nut-coupling.json").read_text())
    main = mesh_report["bodies"][BODY]
    carrier = mesh_report["bodies"][CARRIER]
    nodes_source, main_elements, carrier_elements = parse_selected_mesh(mesh_report)
    controls_source = parse_control_nodes()
    main_node_ids = set(map(int, main["nodes"]))
    carrier_node_ids = set(map(int, carrier["nodes"]))
    equations, parsed_equations = parse_equation_cards(coupling_report, main_node_ids)
    equation_width_audit = audit_source_equation_widths(equations, parsed_equations)
    equation_width_audit["source_equation_rows_sha256"] = sha256_bytes(
        "".join(equations).encode("ascii"))
    carrier_nset, rigid_card = parse_rigid_nset(carrier_node_ids)

    coordinate_lines = {}
    coordinate_audit_rows = {}
    for node_id, raw_line in nodes_source.items():
        emitted_line, _xyz, row_audit = normalize_node_line(raw_line)
        coordinate_lines[node_id] = emitted_line
        coordinate_audit_rows[node_id] = row_audit
    controls = {}
    control_coordinates = {}
    for node_id, raw_line in controls_source.items():
        emitted_line, xyz, row_audit = normalize_node_line(raw_line)
        controls[node_id] = emitted_line
        control_coordinates[node_id] = xyz
        coordinate_audit_rows[node_id] = row_audit
    coordinate_width_audit = {
        "parser": "nodes.f reads coordinate textpart(2:4)(1:20) with F20.0",
        "node_id_limit_chars": 10,
        "coordinate_field_limit_chars": 20,
        "source_M00_node_rows_sha256": sha256_bytes(("\n".join(
            nodes_source[node] for node in sorted(main_node_ids)) + "\n").encode("ascii")),
        "source_M03_node_rows_sha256": sha256_bytes(("\n".join(
            nodes_source[node] for node in sorted(carrier_node_ids)) + "\n").encode("ascii")),
        "source_control_node_rows_sha256": sha256_bytes(("\n".join(
            controls_source[node] for node in sorted(controls_source)) + "\n").encode("ascii")),
        "selected_node_row_count_including_controls": len(coordinate_audit_rows),
        "overwidth_source_coordinate_field_count": sum(
            row["overwidth_coordinate_field_count"] for row in coordinate_audit_rows.values()),
        "max_abs_source_literal_vs_native_parser_coordinate_mm": max(
            row["max_abs_source_literal_vs_parser_visible_mm"]
            for row in coordinate_audit_rows.values()),
        "emitted_coordinate_fields_are_exact_parser_visible_source_prefixes": True,
    }
    physical_xyz = {}
    for node_id in main_node_ids:
        fields = coordinate_lines[node_id].split(",")
        physical_xyz[node_id] = tuple(float(v) for v in fields[1:4])
    carrier_xyz = {}
    for node_id in carrier_node_ids:
        fields = coordinate_lines[node_id].split(",")
        carrier_xyz[node_id] = tuple(float(v) for v in fields[1:4])
    main_elements_ordered = dict(sorted(main_elements.items()))
    reference_body = integrate_body(physical_xyz, main_elements_ordered)
    carrier_reference = integrate_body(carrier_xyz, dict(sorted(carrier_elements.items())), density=0.0)
    reference_body["physical_node_ids"] = sorted(main_node_ids)
    reference_body["carrier_node_ids"] = sorted(carrier_node_ids)
    carrier_reference["physical_node_ids"] = sorted(carrier_node_ids)
    moment_audit = cross_matrix_check(reference_body, physical_xyz)

    decks = {
        "direct": render_case("direct", include_map=False, include_carrier=False,
                              node_lines=coordinate_lines, main_elements=main_elements,
                              carrier_elements=carrier_elements, controls=controls,
                              equations=equations, carrier_nset=carrier_nset,
                              rigid_card=rigid_card, body_reference=reference_body,
                              carrier_reference=carrier_reference),
        "mapped_no_carrier": render_case("mapped_no_carrier", include_map=True, include_carrier=False,
                                          node_lines=coordinate_lines, main_elements=main_elements,
                                          carrier_elements=carrier_elements, controls=controls,
                                          equations=equations, carrier_nset=carrier_nset,
                                          rigid_card=rigid_card, body_reference=reference_body,
                                          carrier_reference=carrier_reference),
        "mapped_carrier": render_case("mapped_carrier", include_map=True, include_carrier=True,
                                      node_lines=coordinate_lines, main_elements=main_elements,
                                      carrier_elements=carrier_elements, controls=controls,
                                      equations=equations, carrier_nset=carrier_nset,
                                      rigid_card=rigid_card, body_reference=reference_body,
                                      carrier_reference=carrier_reference),
    }
    deck_width_audits = {name: audit_deck_numeric_widths(deck)
                         for name, deck in decks.items()}
    source_equation_bytes = "".join(equations).encode("ascii")
    for name, deck in decks.items():
        if name != "direct" and source_equation_bytes not in deck:
            raise ValueError(f"{name} deck did not preserve the exact source map rows")
    input_mapping = {name: {"path": f"input/{name}.inp", "sha256": sha256_bytes(deck)}
                     for name, deck in decks.items()}
    linear_states = []
    for increment in range(1, STATES + 1):
        time = increment * DT
        omega = 0.5 * ALPHA_RAMP * time * time
        theta = ALPHA_RAMP * (time ** 3 / 6.0 + time * DT * DT / 12.0)
        linear_states.append({"increment": increment, "time_s": time,
                              "angular_acceleration_y_rad_s2": ALPHA_RAMP * time,
                              "angular_velocity_y_rad_s": omega,
                              "rotation_vector_y_rad": theta,
                              "linearized_ELKE_Nmm": 0.5 * reference_body[
                                  "rotation_y_modal_mass_tonne_mm2"] * omega * omega})
    force_rows = []
    force_component_counts = {"dof1": 0, "dof2": 0, "dof3": 0}
    for node_id in sorted(reference_body["load_final_by_node"]):
        vector = reference_body["load_final_by_node"][node_id]
        force_rows.append(f"{node_id},{vector[0]:.17e},{vector[1]:.17e},{vector[2]:.17e}")
        for axis, dof in enumerate(("dof1", "dof2", "dof3")):
            if vector[axis] != 0.0:
                force_component_counts[dof] += 1
    load_digest = sha256_bytes(("\n".join(force_rows) + "\n").encode("ascii"))
    load_serialization_audit = audit_load_serialization(reference_body, physical_xyz)
    body_numeric = {key: value for key, value in reference_body.items()
                    if key not in ("load_final_by_node", "physical_node_ids", "carrier_node_ids")}
    body_numeric.update({
        "body_id": BODY,
        "mesh_body_id": main["mesh_body_id"],
        "axis_id": main["axis_id"],
        "component_role": main["component_role"],
        "element_count": len(main_elements),
        "node_count": len(main_node_ids),
        "physical_node_ids_sha256": sha256_bytes(
            ("\n".join(map(str, sorted(main_node_ids))) + "\n").encode("ascii")),
        "carrier_body_id": CARRIER,
        "carrier_element_count": len(carrier_elements),
        "carrier_node_count": len(carrier_node_ids),
        "carrier_node_ids_sha256": sha256_bytes(
            ("\n".join(map(str, sorted(carrier_node_ids))) + "\n").encode("ascii")),
    })
    carrier_numeric = {key: value for key, value in carrier_reference.items()
                       if key not in ("load_final_by_node", "physical_node_ids")}
    carrier_numeric.update({
        "body_id": CARRIER,
        "mesh_body_id": carrier["mesh_body_id"],
        "axis_id": carrier["axis_id"],
        "component_role": carrier["component_role"],
        "element_count": len(carrier_elements),
        "node_count": len(carrier_node_ids),
        "node_ids_sha256": body_numeric["carrier_node_ids_sha256"],
    })
    qnodes = {node: control_coordinates[node] for node in CONTROL_IDS}
    if any(tuple(value) != tuple(PIVOT) for value in qnodes.values()):
        raise ValueError("control nodes do not share the A00 native pivot")
    expected = {
        "schema": "ccx223_implicit_current_map_expected/v1",
        "status": "PREPARED_NOT_FROZEN_NO_NATIVE_RUN",
        "case_order": ["direct", "mapped_no_carrier", "mapped_carrier"],
        "inputs": input_mapping,
        "pinned_source_archive": {
            "path": "ordinary-external-force-transient-attempt04-diagnostic/build-attempt02/source.tar.bz2",
            "sha256": ARCHIVE_SHA256,
            "members_sha256": member_hashes,
        },
        "source_files": {
            name: {"path": f"ordinary-port-motion-attempt09-common-map/{name}",
                  "sha256": digest}
            for name, digest in source_hashes.items()
        },
        "method_sources": {
            "consistent_mass": ["e_c3d.f", "gauss.f", "shape10tet.f", "mafillsm.f"],
            "rigid_current_rotation": ["rigidbodys.f", "rigidmpc.f", "nonlinmpc.f"],
            "mass_quadrature": {
                "rule": "gauss3d5",
                "points_xi_eta_zeta": [[0.138196601125011, 0.138196601125011, 0.138196601125011],
                                         [0.585410196624968, 0.138196601125011, 0.138196601125011],
                                         [0.138196601125011, 0.585410196624968, 0.138196601125011],
                                         [0.138196601125011, 0.138196601125011, 0.585410196624968]],
                "weight_each": 0.041666666666667,
            },
        },
        "procedure": {"type": "DYNAMIC,DIRECT", "nlgeom": True, "alpha": 0.0,
                      "dt_s": DT, "total_time_s": TOTAL_TIME,
                      "accepted_increment_count_expected": STATES,
                      "initial_velocity": "default zero", "boundary_conditions": []},
        "load_definition": {
            "law": "f(t)=M_4point * (alpha_y(t) * (e_y cross (x_reference - p)))",
            "alpha_y(t)": f"{ALPHA_RAMP} * t rad/s^2; c={ALPHA_RAMP} rad/s^3",
            "amplitude": "linear STEP TIME, 0 at t=0 to 1 at t=T; CLOAD values are final-time M*a",
            "load_is_full_physical_nodal_vector": True,
            "load_is_not_lumped_or_mpc_transformed_by_producer": True,
            "same_load_vector_in_all_three_cases": True,
            "intended_full_precision_load_vector_sha256_node_fx_fy_fz": load_digest,
            "serialization_f20_audit": load_serialization_audit,
            "nonzero_final_cload_card_count": force_component_counts["dof1"] + force_component_counts["dof3"],
            "nonzero_final_component_node_counts": force_component_counts,
            "final_force_and_moment_audit": moment_audit,
            "force_y_component_is_zero_by_definition": True,
        },
        "physical_body_reference": body_numeric,
        "zero_density_carrier_reference": carrier_numeric,
        "input_field_width_audit": {
            "CLOAD_field_limit_chars": 20,
            "CLOAD_parser": "cloads.f reads textpart(3)(1:20) with F20.0",
            "coordinate_and_node_fields": coordinate_width_audit,
            "equation_fields": equation_width_audit,
            "all_generated_numeric_comma_fields": deck_width_audits,
            "all_selected_source_map_rows_byte_preserved": True,
        },
        "pivot_and_current_map": {
            "pivot_xyz_mm": list(PIVOT),
            "rotation_axis_global": [0.0, 1.0, 0.0],
            "control_node_ids": list(CONTROL_IDS),
            "control_nodes_coincident_at_pivot": True,
            "equation_row_count": len(equations),
            "equation_term_counts": [row["term_count"] for row in parsed_equations],
            "dependent_node_dofs": [list(row["dependent"]) for row in parsed_equations],
            "all_six_control_dofs_referenced_and_unrestrained": True,
            "reference_control_oracle": "REF node U1-U3=V1-V3=0; ROT node U1=U3=V1=V3=0, U2=theta_y, V2=omega_y. The six REF/ROT values are required in DAT; the controls are unmeshed and omitted from FRD.",
            "map_report_affine_rigid_reproduction_max_abs_error": coupling_report[
                "per_nut"][0]["least_squares_rigid_motion_fit"][
                    "affine_rigid_reproduction_max_abs_error"],
        },
        "linearized_discrete_reference": {
            "newmark_beta": 0.25,
            "newmark_gamma": 0.5,
            "alpha_y": "c*t",
            "omega_y": "c*t^2/2",
            "theta_y": "c*(t^3/6+t*dt^2/12)",
            "direction_per_node_mm": "e_y cross (x_reference-p)=(z-zp,0,-(x-xp))",
            "physical_U": "theta_y * direction_per_node_mm",
            "physical_V": "omega_y * direction_per_node_mm",
            "kinetic_energy": "0.5 * Iyy_about_pivot * omega_y^2 Nmm",
            "states": linear_states,
            "carrier_reference": "For mapped_carrier, exact displacement uses the measured total rotation vector w: x_current=p+R(w)*(x_reference-p). Pinned dynresults.f and nonlinmpc.f establish carrier velocity as REF_velocity + dR/dw * w_dot * (x_reference-p), using the full Rodrigues derivative for a measured three-component ROT vector. For this fixed single global Y axis it specializes to omega_y*e_y cross (R_y(theta_y)*(x_reference-p)). The source convention is established; agreement with native output remains to be tested by this fixture.",
            "zero_components": {
                "physical_U2_V2": 0.0,
                "control_REF_U_V_all_components": 0.0,
                "control_ROT_U1_U3_V1_V3": 0.0,
                "control_ROT_U2": "theta_y",
                "control_ROT_V2": "omega_y",
            },
            "interpretation": "linearized rigid-mode Newmark reference; it is not an exact NLGEOM elastic-body trajectory or a frozen acceptance tolerance",
        },
        "output_contract": {
            "all_physical_node_fields": ["U", "V"],
            "all_physical_nodes_in": ["DAT", "FRD"],
            "node_id_sets": {
                "physical_body": {"node_ids": sorted(main_node_ids),
                                  "count": len(main_node_ids),
                                  "sha256_sorted_decimal_ids": body_numeric["physical_node_ids_sha256"]},
                "mapping_controls": {"node_ids": list(CONTROL_IDS), "count": len(CONTROL_IDS)},
                "zero_density_carrier": {"node_ids": sorted(carrier_node_ids),
                                          "count": len(carrier_node_ids),
                                          "sha256_sorted_decimal_ids": body_numeric["carrier_node_ids_sha256"]},
            },
            "nsets_in_deck": {
                "N_PHYSICAL": "physical_body",
                "NUT_00_RIGID_CONTROL": "mapping_controls, mapped cases only",
                "M03_A00_NUT_RIGID_NODES": "zero_density_carrier, mapped_carrier only; copied from pinned rigid-carriers.inp",
                "N_OBSERVE": "union of the case node groups below",
            },
            "coverage_by_case": {
                "direct": {"DAT_node_groups": ["physical_body"],
                           "FRD_node_groups": ["physical_body"]},
                "mapped_no_carrier": {"DAT_node_groups": ["physical_body", "mapping_controls"],
                                      "FRD_node_groups": ["physical_body"]},
                "mapped_carrier": {"DAT_node_groups": ["physical_body", "mapping_controls", "zero_density_carrier"],
                                   "FRD_node_groups": ["physical_body", "zero_density_carrier"]},
            },
            "coverage_fields": ["U", "V"],
            "control_nodes_FRD_omission": "REF/ROT controls are unmeshed and not attached to elements; FRD omits them even when included in the requested NSET. DAT control-node coverage remains required.",
            "frequency": 1,
            "EL_PRINT_by_case": {
                "direct": {BODY: ["ELSE", "ELKE", "EMAS", "EVOL"]},
                "mapped_no_carrier": {BODY: ["ELSE", "ELKE", "EMAS", "EVOL"]},
                "mapped_carrier": {BODY: ["ELSE", "ELKE", "EMAS", "EVOL"],
                                   CARRIER: ["ELSE", "ELKE", "EMAS", "EVOL"]},
            },
            "zero_density_carrier_expected_totals": {
                "ELSE_Nmm": 0.0,
                "ELKE_Nmm": 0.0,
                "EMAS_tonne": 0.0,
                "EVOL_mm3": carrier_numeric["volume_mm3"],
                "values_are_reference_not_acceptance_thresholds": True,
            },
            "no_ACCEPTANCE_thresholds_assigned": True,
            "proposed_per_case_output_capture_cap_MiB": 64,
            "capture_estimate_basis": {
                "prior_10_node_100_state_DAT_bytes": 204842,
                "prior_10_node_100_state_FRD_bytes": 165328,
                "measured_prior_artifacts": {
                    kind: {"path": f"../{path.relative_to(BASE)}",
                           "sha256": digest, "size_bytes": path.stat().st_size}
                    for kind, (path, digest) in CAPTURE_BASELINE_FILES.items()
                },
                "largest_DAT_node_count": len(main_node_ids) + len(carrier_node_ids) + len(CONTROL_IDS),
                "largest_FRD_node_count": len(main_node_ids) + len(carrier_node_ids),
                "requested_states": STATES,
                "estimated_nodal_DAT_rows_bytes": (len(main_node_ids) + len(carrier_node_ids) + len(CONTROL_IDS)) * STATES * 2 * 52,
                "estimated_nodal_FRD_rows_bytes": (len(main_node_ids) + len(carrier_node_ids)) * STATES * 2 * 49,
                "note": "Adds about 1.4 MiB for model mesh headers and modest solver/log records; estimate is not an observed capture size. 16 MiB would be inadequate; 64 MiB is provisional pending parent runner budget review.",
            },
        },
        "scope_limits": [
            "One source-bound A00 bolt-head/shaft body and its current six-row map only.",
            "The M03 zero-density rigid carrier is passive: no contact, force, or joint interaction is added.",
            "No CAD rebuild, physical nut mass, thread engagement, strength, capacity, or joint acceptance is represented.",
            "The M*a load and linearized Newmark field are based on the pinned four-point C3D10 discrete mass, not continuum-exact curved-body integration.",
            "Finite rotation and nonlinear elastic-body error are not assigned a bound here; parent/reviewer must choose acceptance gates.",
            "No build, native solve, or freeze was performed by this producer.",
        ],
    }
    return decks, expected


def render_expected(expected: dict) -> bytes:
    return (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    decks, expected = build()
    expected_bytes = render_expected(expected)
    targets = {HERE / "input" / f"{name}.inp": data for name, data in decks.items()}
    targets[HERE / "expected.json"] = expected_bytes
    if args.write:
        (HERE / "input").mkdir(exist_ok=True)
        for path, data in targets.items():
            path.write_bytes(data)
    else:
        missing = [str(path.relative_to(HERE)) for path in targets if not path.exists()]
        changed = [str(path.relative_to(HERE)) for path, data in targets.items()
                   if path.exists() and path.read_bytes() != data]
        if missing or changed:
            raise SystemExit(f"reproduction mismatch; missing={missing}, changed={changed}")
    print(json.dumps({"status": "PASS_OFFLINE_PREPARATION" if args.write else "PASS_REPRODUCIBLE_CHECK",
                      "cases": {name: sha256_bytes(data) for name, data in decks.items()},
                      "expected_sha256": sha256_bytes(expected_bytes),
                      "body_mass_tonne": expected["physical_body_reference"]["mass_tonne"],
                      "Iyy_tonne_mm2": expected["physical_body_reference"][
                          "rotation_y_modal_mass_tonne_mm2"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
