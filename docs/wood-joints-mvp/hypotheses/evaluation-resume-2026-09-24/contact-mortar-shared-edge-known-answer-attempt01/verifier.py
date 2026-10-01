"""Offline provenance, deck, trace, and known-answer audit for the shared-edge coupon."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
CASES = {
    "shared_slave_mortar",
    "shared_slave_penalty",
    "cross_role_mortar",
    "cross_role_penalty",
}
SIDES = {
    "S1": (0, 1, 2, 4, 5, 6),
    "S2": (0, 1, 3, 4, 8, 7),
    "S3": (1, 2, 3, 5, 9, 8),
    "S4": (0, 2, 3, 6, 9, 7),
}
SIDE_CORNERS = {name: indices[:3] for name, indices in SIDES.items()}
MIDPOINT_EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
ALLOWED_CARDS = {
    "HEADING", "NODE", "ELEMENT", "NSET", "MATERIAL", "ELASTIC",
    "SOLID SECTION", "SURFACE", "SURFACE INTERACTION", "SURFACE BEHAVIOR",
    "CONTACT PAIR", "BOUNDARY", "STEP", "STATIC", "CLOAD", "NODE PRINT",
    "NODE FILE", "CONTACT FILE", "END STEP",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    value = str(value)
    match = re.fullmatch(r"\s*([+-]?(?:\d+\.\d*|\.\d+))([+-]\d{3})\s*", value)
    if match and abs(int(match[2])) > 99:
        value = match[1] + "E" + match[2]
    result = float(value.replace("D", "E").replace("d", "e"))
    require(math.isfinite(result), "Nonfinite numeric evidence")
    return result


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, f"Duplicate JSON key: {name}")
            result[name] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Nonfinite JSON number: {value}")

    def finite_float(value):
        result = float(value)
        require(math.isfinite(result), f"Nonfinite JSON number: {value}")
        return result

    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_float=finite_float, parse_constant=reject_constant)


def close(actual, expected, tolerance=1e-10):
    return abs(actual - expected) <= tolerance


def norm(values):
    return math.sqrt(sum(value * value for value in values))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, factor):
    return tuple(x * factor for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def moment(position, force):
    return cross(position, force)


def cards(path):
    result = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            pieces = [part.strip() for part in line[1:].split(",")]
            keyword = pieces[0].upper()
            options, flags = {}, set()
            for part in pieces[1:]:
                if not part:
                    continue
                if "=" in part:
                    key, value = part.split("=", 1)
                    key = key.strip().upper()
                    require(key not in options, f"Duplicate {key} option in {line}")
                    options[key] = value.strip().upper()
                else:
                    flags.add(part.upper())
            result.append({"keyword": keyword, "options": options,
                           "flags": flags, "line": line, "data": []})
        else:
            require(result, f"Data before first input card: {line}")
            result[-1]["data"].append(line)
    return result


def card_data(card):
    return [line for line in card["data"] if line.strip()]


def parse_int(value):
    result = number(value)
    require(result.is_integer(), f"Expected integer, found {value}")
    return int(result)


def node_xyz(nodes, node):
    require(node in nodes, f"Unknown node {node}")
    return nodes[node]


def parse_deck(path):
    parsed = cards(path)
    node_cards = [c for c in parsed if c["keyword"] == "NODE"]
    require(len(node_cards) == 1, "Expected one *NODE card")
    nodes = {}
    for line in card_data(node_cards[0]):
        values = [part.strip() for part in line.split(",")]
        require(len(values) == 4, f"Malformed node row: {line}")
        node = parse_int(values[0])
        require(node not in nodes, f"Duplicate node {node}")
        nodes[node] = tuple(number(value) for value in values[1:])

    elements, body_elements = {}, {}
    for card in parsed:
        if card["keyword"] != "ELEMENT":
            continue
        require(card["options"].get("TYPE") == "C3D10", "Non-C3D10 element card")
        body = card["options"].get("ELSET")
        require(body and body not in body_elements, "Missing/duplicate C3D10 ELSET")
        body_elements[body] = set()
        for line in card_data(card):
            values = [part.strip() for part in line.split(",")]
            require(len(values) == 11, f"Malformed C3D10 row: {line}")
            element = parse_int(values[0])
            require(element not in elements, f"Duplicate element {element}")
            connectivity = tuple(parse_int(value) for value in values[1:])
            require(len(set(connectivity)) == 10, f"Repeated node in element {element}")
            require(set(connectivity) <= set(nodes), f"Unknown element node {element}")
            elements[element] = connectivity
            body_elements[body].add(element)

    nsets = {}
    for card in parsed:
        if card["keyword"] != "NSET":
            continue
        name = card["options"].get("NSET")
        require(name and name not in nsets, "Missing/duplicate NSET")
        values = []
        tokens = [token.strip() for line in card_data(card) for token in line.split(",")]
        tokens = [token for token in tokens if token]
        if "GENERATE" in card["flags"]:
            require(len(tokens) % 3 == 0, f"Malformed generated NSET {name}")
            for start, stop, increment in zip(tokens[::3], tokens[1::3], tokens[2::3]):
                start, stop, increment = map(parse_int, (start, stop, increment))
                require(increment > 0 and stop >= start, f"Bad NSET range {name}")
                values.extend(range(start, stop + 1, increment))
        else:
            values = list(map(parse_int, tokens))
        require(values and len(values) == len(set(values)), f"Empty/duplicate NSET {name}")
        require(set(values) <= set(nodes), f"Unknown node in NSET {name}")
        nsets[name] = set(values)

    surfaces = {}
    for card in parsed:
        if card["keyword"] != "SURFACE":
            continue
        name = card["options"].get("NAME")
        require(name and name not in surfaces, "Missing/duplicate surface")
        require(card["options"].get("TYPE") == "ELEMENT", "Unexpected surface type")
        facets = []
        for line in card_data(card):
            values = [part.strip() for part in line.split(",")]
            require(len(values) == 2, f"Malformed surface facet: {line}")
            facets.append((parse_int(values[0]), values[1].upper()))
        require(facets and len(facets) == len(set(facets)), f"Empty/duplicate surface {name}")
        surfaces[name] = facets

    boundaries = {}
    for card in parsed:
        if card["keyword"] != "BOUNDARY":
            continue
        for line in card_data(card):
            values = [part.strip() for part in line.split(",")]
            require(len(values) in (3, 4), f"Malformed *BOUNDARY row: {line}")
            selector = values[0].upper()
            if selector.isdigit():
                selected_nodes = {parse_int(selector)}
            else:
                require(selector in nsets, f"Unknown boundary NSET {selector}")
                selected_nodes = nsets[selector]
            start, end = parse_int(values[1]), parse_int(values[2])
            value = number(values[3]) if len(values) == 4 else 0.0
            require(1 <= start <= end <= 3, f"Invalid boundary DOF range: {line}")
            for node in selected_nodes:
                for dof in range(start, end + 1):
                    key = (node, dof)
                    require(key not in boundaries, f"Duplicate boundary DOF {key}")
                    boundaries[key] = value

    loads = {}
    for card in parsed:
        if card["keyword"] != "CLOAD":
            continue
        for line in card_data(card):
            values = [part.strip() for part in line.split(",")]
            require(len(values) == 3, f"Malformed *CLOAD row: {line}")
            key = (parse_int(values[0]), parse_int(values[1]))
            require(key not in loads, f"Duplicate CLOAD {key}")
            require(key[0] in nodes and key[1] in (1, 2, 3), f"Invalid CLOAD {key}")
            loads[key] = number(values[2])

    return {"cards": parsed, "nodes": nodes, "elements": elements,
            "body_elements": body_elements, "nsets": nsets,
            "surfaces": surfaces, "boundaries": boundaries, "loads": loads}


def compare_numbers(actual, expected, message, tolerance=1e-10):
    require(close(actual, expected, tolerance),
            f"{message}: got {actual:.12g}, expected {expected:.12g}")


def compare_mapping(actual, expected, message, tolerance=1e-10):
    require(set(actual) == set(expected), f"{message} keys differ")
    for key in expected:
        compare_numbers(actual[key], expected[key], f"{message} {key}", tolerance)


def contact_roles(case, case_spec, fixture):
    slave_surfaces = [pair["slave"] for pair in case_spec["pairs"].values()]
    master_surfaces = [pair["master"] for pair in case_spec["pairs"].values()]
    slave_nodes = set().union(*(set(fixture["contact_faces"][name]["nodes"])
                                for name in slave_surfaces))
    master_nodes = set().union(*(set(fixture["contact_faces"][name]["nodes"])
                                 for name in master_surfaces))
    x_pair = case_spec["pairs"]["PAIR_X"]
    z_pair = case_spec["pairs"]["PAIR_Z"]
    x_intersection = sorted(set(fixture["contact_faces"][x_pair["slave"]]["nodes"]) &
                             set(fixture["contact_faces"][x_pair["master"]]["nodes"]))
    z_intersection = sorted(set(fixture["contact_faces"][z_pair["slave"]]["nodes"]) &
                             set(fixture["contact_faces"][z_pair["master"]]["nodes"]))
    checks = {
        "X_slave_master_node_label_intersection": x_intersection,
        "Z_slave_master_node_label_intersection": z_intersection,
        "all_four_surface_names_unique": len(set(slave_surfaces + master_surfaces)) == 4,
        "cross_pair_slave_master_shared_node_labels": sorted(slave_nodes & master_nodes),
        "pair_count": 2,
        "slave_slave_shared_node_labels": sorted(
            set(fixture["contact_faces"][x_pair["slave"]]["nodes"]) &
            set(fixture["contact_faces"][z_pair["slave"]]["nodes"])),
        "slave_spc_node_label_intersection": [],
    }
    require(checks == case_spec["contact_role_checks"],
            f"{case}: role check metadata is inconsistent")
    return slave_surfaces, master_surfaces, slave_nodes, master_nodes, checks


def audit_deck(case, case_spec, expected, deck_path=None):
    fixture = expected["fixture"]
    parsed = parse_deck(deck_path or HERE / case_spec["path"])
    nodes = parsed["nodes"]
    elements = parsed["elements"]
    require({card["keyword"] for card in parsed["cards"]} <= ALLOWED_CARDS,
            f"{case}: unsupported input card")
    require(set(nodes) == {int(label) for label in fixture["node_coordinates_mm"]},
            f"{case}: node labels differ from fixture")
    for label, coordinate in fixture["node_coordinates_mm"].items():
        for actual, target in zip(nodes[int(label)], coordinate):
            compare_numbers(actual, target, f"{case}: node {label} coordinate", 1e-12)

    expected_elements = {
        int(element): tuple(connectivity)
        for body in fixture["elements"].values()
        for element, connectivity in body.items()
    }
    require(elements == expected_elements, f"{case}: C3D10 connectivity differs")
    require(set(parsed["body_elements"]) == set(fixture["elements"]),
            f"{case}: body ELSET names differ")
    for body, members in fixture["elements"].items():
        require(parsed["body_elements"][body] == {int(label) for label in members},
                f"{case}: body element ownership differs: {body}")
        expected_body_nodes = set(fixture["body_node_groups"][body])
        actual_body_nodes = set().union(*(
            set(elements[element]) for element in parsed["body_elements"][body]))
        require(actual_body_nodes == expected_body_nodes,
                f"{case}: body node membership differs: {body}")

    expected_nsets = {"ALLNODES": set(nodes)}
    expected_nsets.update({f"{body}_NODES": set(labels)
                           for body, labels in fixture["body_node_groups"].items()})
    expected_nsets.update({f"FACE_{name}": set(face["nodes"])
                           for name, face in fixture["contact_faces"].items()})
    expected_nsets.update({name: set(spec["nodes"])
                           for name, spec in fixture["spc_groups"].items()})
    require(parsed["nsets"] == expected_nsets, f"{case}: NSET membership differs")

    require(len(elements) == 18 and len(nodes) == expected["requested_outputs"]["all_nodes"],
            f"{case}: fixture mesh size differs")
    midside_errors, jacobians = {}, {}
    for element, connectivity in elements.items():
        corner = [nodes[node] for node in connectivity[:4]]
        a = tuple(corner[1][d] - corner[0][d] for d in range(3))
        b = tuple(corner[2][d] - corner[0][d] for d in range(3))
        c = tuple(corner[3][d] - corner[0][d] for d in range(3))
        determinant = dot(a, cross(b, c))
        require(determinant > 0, f"{case}: nonpositive corner Jacobian at {element}")
        jacobians[str(element)] = determinant
        for edge_index, (first, second) in enumerate(MIDPOINT_EDGES):
            midside = connectivity[4 + edge_index]
            midpoint = tuple((corner[first][d] + corner[second][d]) / 2
                             for d in range(3))
            error = norm(tuple(nodes[midside][d] - midpoint[d] for d in range(3)))
            midside_errors[f"{element}:{midside}"] = error
    mesh_checks = fixture["mesh_checks"]
    require(max(midside_errors.values()) <=
            max(mesh_checks["maximum_midside_coordinate_error_mm"], 1e-12),
            f"{case}: C3D10 midside nodes are not straight-edge midpoints")
    for element, target in mesh_checks["signed_corner_determinants_mm3"].items():
        compare_numbers(jacobians[element], target, f"{case}: element Jacobian {element}", 1e-12)

    exterior_counts = {body: {} for body in fixture["elements"]}
    for body, body_members in parsed["body_elements"].items():
        for element in body_members:
            connectivity = elements[element]
            for side, corner_indices in SIDE_CORNERS.items():
                face_key = frozenset(connectivity[index] for index in corner_indices)
                exterior_counts[body][face_key] = exterior_counts[body].get(face_key, 0) + 1
    for body, counts in exterior_counts.items():
        exterior_count = sum(value == 1 for value in counts.values())
        require(exterior_count ==
                fixture["mesh_checks"]["tetra_mesh_exterior_face_count_by_body"][body],
                f"{case}: exterior face count differs for {body}")

    contact_surface_names = {
        name for pair in case_spec["pairs"].values()
        for name in (pair["slave"], pair["master"])
    }
    require(set(parsed["surfaces"]) == contact_surface_names,
            f"{case}: contact surface names differ")
    surface_nodes = {}
    for surface, expected_face in fixture["contact_faces"].items():
        expected_facets = {(facet["element"], facet["side"])
                           for facet in expected_face["facets"]}
        if surface in contact_surface_names:
            require(set(parsed["surfaces"][surface]) == expected_facets,
                    f"{case}: selected facets differ for {surface}")
        selected_nodes = set()
        for facet in expected_face["facets"]:
            element, side = facet["element"], facet["side"]
            require(element in parsed["body_elements"][expected_face["body"]],
                    f"{case}: facet {element}/{side} is not on body {expected_face['body']}")
            require(side in SIDES, f"{case}: unknown C3D10 face side {side}")
            connectivity = elements[element]
            local_nodes = tuple(connectivity[index] for index in SIDES[side])
            require(local_nodes == tuple(facet["nodes"]),
                    f"{case}: quadratic face node order differs for {surface}")
            corners = tuple(connectivity[index] for index in SIDE_CORNERS[side])
            require(set(corners) == set(facet["corner_nodes"]),
                    f"{case}: face corners differ for {surface}")
            corner_key = frozenset(corners)
            require(exterior_counts[expected_face["body"]].get(corner_key) == 1,
                    f"{case}: selected face is not exterior: {surface}")
            xyz = [nodes[label] for label in facet["corner_nodes"]]
            raw_normal = cross(tuple(xyz[1][d] - xyz[0][d] for d in range(3)),
                               tuple(xyz[2][d] - xyz[0][d] for d in range(3)))
            # CalculiX reverses S1 and follows the corner order on S3.
            oriented = scale(raw_normal, -1 if side == "S1" else 1)
            magnitude = norm(oriented)
            require(magnitude > 0, f"{case}: degenerate contact facet {surface}")
            unit = scale(oriented, 1 / magnitude)
            require(dot(unit, expected_face["expected_outward_normal"]) > 1 - 1e-10,
                    f"{case}: surface normal differs for {surface}")
            area = magnitude / 2
            compare_numbers(area, facet["area_mm2"], f"{case}: facet area {surface}", 1e-12)
            selected_nodes.update(local_nodes)
        surface_nodes[surface] = selected_nodes
        require(selected_nodes == set(expected_face["nodes"]),
                f"{case}: face node union differs for {surface}")
        compare_numbers(sum(f["area_mm2"] for f in expected_face["facets"]),
                        expected_face["area_mm2"], f"{case}: patch area {surface}", 1e-12)
    for surface, expected_nodes in fixture["contact_face_node_groups"].items():
        require(surface_nodes[surface] == set(expected_nodes),
                f"{case}: declared contact face node group differs for {surface}")

    # Coincident patches must cover the same nine projected coordinates.
    for first, second, axes, fixed_axis, fixed_value in (
        ("X_CENTRAL", "X_LEFT", (1, 2), 0, 0.0),
        ("Z_CENTRAL", "Z_LOWER", (0, 1), 2, 0.0),
    ):
        projected = []
        for name in (first, second):
            face_nodes = surface_nodes[name]
            require(all(close(nodes[node][fixed_axis], fixed_value, 1e-12)
                         for node in face_nodes), f"{case}: {name} is off contact plane")
            projected.append({tuple(nodes[node][axis] for axis in axes) for node in face_nodes})
        require(projected[0] == projected[1] and len(projected[0]) == 9,
                f"{case}: contact patch projection differs for {first}/{second}")

    # The central X/Z pair shares two vertices and one quadratic midside label.
    shared_labels = set(surface_nodes["X_CENTRAL"]) & set(surface_nodes["Z_CENTRAL"])
    require(sorted(shared_labels) == fixture["contact_edge_shared_node_labels"],
            f"{case}: central shared edge labels differ")
    shared_corners = set()
    for facet in fixture["contact_faces"]["X_CENTRAL"]["facets"]:
        shared_corners.update(set(facet["corner_nodes"]) & shared_labels)
    expected_vertices = fixture["contact_edge_shared_nodes_by_topology"]["vertex_nodes"]
    require(sorted(shared_corners) == expected_vertices,
            f"{case}: shared edge vertex labels differ")
    require(sorted(shared_labels - shared_corners) ==
            fixture["contact_edge_shared_nodes_by_topology"]["midside_nodes"],
            f"{case}: shared edge midside labels differ")

    material = fixture["material_and_contact"]
    material_cards = [c for c in parsed["cards"] if c["keyword"] == "MATERIAL"]
    elastic_cards = [c for c in parsed["cards"] if c["keyword"] == "ELASTIC"]
    section_cards = [c for c in parsed["cards"] if c["keyword"] == "SOLID SECTION"]
    require(len(material_cards) == 1 and material_cards[0]["options"].get("NAME") == "ELASTIC",
            f"{case}: material definition differs")
    require(len(elastic_cards) == 1 and len(card_data(elastic_cards[0])) == 1,
            f"{case}: expected one isotropic elastic material")
    elastic = [number(value) for value in card_data(elastic_cards[0])[0].split(",")]
    require(len(elastic) == 2, f"{case}: unexpected elastic constants")
    compare_numbers(elastic[0], material["youngs_modulus_N_per_mm2"], "Young's modulus")
    compare_numbers(elastic[1], material["poisson_ratio"], "Poisson ratio")
    require({(c["options"].get("ELSET"), c["options"].get("MATERIAL"))
             for c in section_cards} == {(body, "ELASTIC") for body in fixture["elements"]},
            f"{case}: solid section ownership differs")

    interaction_cards = [c for c in parsed["cards"]
                         if c["keyword"] == "SURFACE INTERACTION"]
    behavior_cards = [c for c in parsed["cards"] if c["keyword"] == "SURFACE BEHAVIOR"]
    require(len(interaction_cards) == len(behavior_cards) == 1 and
            interaction_cards[0]["options"].get("NAME") == "NORMAL_LAW",
            f"{case}: contact interaction differs")
    require(behavior_cards[0]["options"].get("PRESSURE-OVERCLOSURE") == "LINEAR" and
            len(card_data(behavior_cards[0])) == 1,
            f"{case}: expected linear frictionless pressure-overclosure law")
    compare_numbers(number(card_data(behavior_cards[0])[0]),
                    material["linear_pressure_overclosure_slope_K_N_per_mm3"],
                    f"{case}: normal penalty slope")

    pair_cards = [c for c in parsed["cards"] if c["keyword"] == "CONTACT PAIR"]
    require(len(pair_cards) == len(case_spec["pairs"]) == 2 and
            expected["acceptance"]["require_two_pairs_per_deck"] is True,
            f"{case}: expected two contact pairs")
    pair_by_axis, actual_types = {}, set()
    for card in pair_cards:
        require(card["options"].get("INTERACTION") == "NORMAL_LAW" and
                len(card_data(card)) == 1, f"{case}: malformed contact pair")
        surfaces = [part.strip().upper() for part in card_data(card)[0].split(",")]
        require(len(surfaces) == 2, f"{case}: contact pair must name two surfaces")
        pair_type = card["options"].get("TYPE")
        require(pair_type, f"{case}: contact type is not explicit")
        actual_types.add(pair_type)
        if set(surfaces) == {case_spec["pairs"]["PAIR_X"]["slave"],
                             case_spec["pairs"]["PAIR_X"]["master"]}:
            axis = "PAIR_X"
        elif set(surfaces) == {case_spec["pairs"]["PAIR_Z"]["slave"],
                               case_spec["pairs"]["PAIR_Z"]["master"]}:
            axis = "PAIR_Z"
        else:
            raise ValueError(f"{case}: undeclared contact surface pair {surfaces}")
        require(axis not in pair_by_axis, f"{case}: duplicate {axis}")
        pair_by_axis[axis] = {"slave": surfaces[0], "master": surfaces[1],
                              "type": pair_type}
        require(pair_by_axis[axis]["slave"] == case_spec["pairs"][axis]["slave"] and
                pair_by_axis[axis]["master"] == case_spec["pairs"][axis]["master"],
                f"{case}: slave/master order differs for {axis}")
    require(set(pair_by_axis) == {"PAIR_X", "PAIR_Z"}, f"{case}: X/Z pairs missing")
    require(actual_types == {case_spec["contact_type"]},
            f"{case}: contact formulation differs from expected")

    spc_expected = {}
    for row in fixture["boundary_constraints"]:
        for dof in range(row["dof_start"], row["dof_end"] + 1):
            key = (row["node"], dof)
            require(key not in spc_expected, f"Duplicate expected SPC {key}")
            spc_expected[key] = row["value"]
    require(parsed["boundaries"] == spc_expected, f"{case}: explicit SPC map differs")
    slave_surfaces, master_surfaces, slave_nodes, master_nodes, role_checks = contact_roles(
        case, case_spec, fixture)
    slave_coverage_reference = expected["requested_outputs"]["FRD_CONTACT"][
        "expected_unique_slave_node_coverage_reference"][case]
    require(len(slave_nodes) == slave_coverage_reference,
            f"{case}: distinct slave-node coverage reference is inconsistent")
    spc_nodes = {node for node, _ in parsed["boundaries"]}
    spc_overlap = sorted(slave_nodes & spc_nodes)
    require(spc_overlap == case_spec["contact_role_checks"]["slave_spc_node_label_intersection"],
            f"{case}: slave contact surface overlaps an SPC")
    require(spc_overlap == fixture["slave_spc_overlap_node_labels_by_case"][case],
            f"{case}: SPC overlap differs from fixture table")

    load_expected = {}
    for row in fixture["load_entries"]:
        key = (row["node"], row["dof"])
        require(key not in load_expected, f"Duplicate expected load {key}")
        compare_numbers(norm(tuple(nodes[key[0]][d] - row["coordinate_mm"][d]
                                    for d in range(3))), 0.0,
                        f"{case}: load coordinate {key}", 1e-12)
        contribution_sum = sum(part["consistent_nodal_force_N"]
                               for part in row["contributions"])
        compare_numbers(contribution_sum, row["force_N"],
                        f"{case}: expected load contribution {key}", 1e-12)
        load_expected[key] = row["force_N"]
    compare_mapping(parsed["loads"], load_expected, f"{case}: *CLOAD", 1e-10)
    audit_input_loads(case, fixture, expected)

    steps = [c for c in parsed["cards"] if c["keyword"] == "STEP"]
    end_steps = [c for c in parsed["cards"] if c["keyword"] == "END STEP"]
    statics = [c for c in parsed["cards"] if c["keyword"] == "STATIC"]
    require(len(steps) == len(end_steps) == len(statics) == 1,
            f"{case}: expected one static step")
    require(expected["step"]["number"] == 1 and expected["step"]["nlgeom"] is True and
            expected["step"]["procedure"] == "*STATIC,DIRECT" and
            "NLGEOM" in steps[0]["flags"] and steps[0]["options"].get("INC") == "100",
            f"{case}: NLGEOM/fixed increment control differs")
    require("DIRECT" in statics[0]["flags"] and
            card_data(statics[0]) == [expected["step"]["static_data_line"]],
            f"{case}: static DIRECT schedule differs")
    audit_output_requests(case, parsed["cards"], expected)

    return {**parsed, "surface_nodes": surface_nodes,
            "slave_surfaces": slave_surfaces, "master_surfaces": master_surfaces,
            "slave_nodes": slave_nodes, "master_nodes": master_nodes,
            "boundaries": parsed["boundaries"], "loads": parsed["loads"],
            "pair_types": actual_types, "role_checks": role_checks}


def audit_input_loads(case, fixture, expected):
    node_coords = {int(label): tuple(coord)
                   for label, coord in fixture["node_coordinates_mm"].items()}
    entries = {(row["node"], row["dof"]): row for row in fixture["load_entries"]}
    pressure = expected["analytical_known_answer"]["compression_endpoint"][
        "pressure_N_per_mm2"]
    by_face = {}
    for key, entry in entries.items():
        for part in entry["contributions"]:
            face_name = part["surface"]
            face = fixture["contact_faces"][face_name]
            facets = [facet for facet in face["facets"]
                      if (facet["element"], facet["side"]) ==
                      (part["facet_element"], part["facet_side"])]
            require(len(facets) == 1, f"{case}: load contribution names unknown facet")
            facet = facets[0]
            require(key[0] in facet["nodes"][3:],
                    f"{case}: quadratic face corner received a load")
            compare_numbers(abs(part["consistent_nodal_force_N"]),
                            pressure * facet["area_mm2"] / 3,
                            f"{case}: midside traction weight {face_name}", 1e-10)
            inward = scale(face["expected_outward_normal"], -1)
            vector = [0.0, 0.0, 0.0]
            vector[key[1] - 1] = part["consistent_nodal_force_N"]
            require(norm(tuple(vector[i] - inward[i] * abs(vector[key[1] - 1])
                               for i in range(3))) <= 1e-10,
                    f"{case}: load does not follow inward face normal on {face_name}")
            summary = by_face.setdefault(face_name, {"force": [0.0] * 3,
                                                     "moment": [0.0] * 3})
            for i in range(3):
                summary["force"][i] += vector[i]
            first_moment = moment(node_coords[key[0]], vector)
            for i in range(3):
                summary["moment"][i] += first_moment[i]
    expected_by_face = expected["load_and_reaction_oracle"]["applied_loads"]["by_face"]
    require(set(by_face) == set(expected_by_face), f"{case}: loaded face set differs")
    total_force = [0.0, 0.0, 0.0]
    total_moment = [0.0, 0.0, 0.0]
    for face, values in by_face.items():
        force_delta = tuple(values["force"][i] - expected_by_face[face]["resultant_N"][i]
                            for i in range(3))
        compare_numbers(norm(force_delta), 0.0,
                        f"{case}: applied resultant {face}", 1e-9)
        compare_numbers(norm(tuple(values["moment"][i] -
                                    expected_by_face[face][
                                        "first_moment_about_global_origin_Nmm"][i]
                                    for i in range(3))), 0.0,
                        f"{case}: applied first moment {face}", 1e-9)
        for i in range(3):
            total_force[i] += values["force"][i]
            total_moment[i] += values["moment"][i]
    all_loads = expected["load_and_reaction_oracle"]["applied_loads"]
    compare_numbers(norm(tuple(total_force[i] - all_loads["total_resultant_N"][i]
                                for i in range(3))), 0.0,
                    f"{case}: total applied resultant", 1e-9)
    compare_numbers(norm(tuple(total_moment[i] -
                                all_loads["total_first_moment_about_global_origin_Nmm"][i]
                                for i in range(3))), 0.0,
                    f"{case}: total applied first moment", 1e-9)


def audit_output_requests(case, parsed_cards, expected):
    wanted = expected["requested_outputs"]
    node_print = [c for c in parsed_cards if c["keyword"] == "NODE PRINT"]
    node_file = [c for c in parsed_cards if c["keyword"] == "NODE FILE"]
    contact_file = [c for c in parsed_cards if c["keyword"] == "CONTACT FILE"]
    require(len(node_print) == len(node_file) == len(contact_file) == 1,
            f"{case}: missing/duplicate output request")
    for card, fields in ((node_print[0], wanted["DAT"][:2]),
                         (node_file[0], wanted["FRD"][:2])):
        require(card["options"].get("NSET") == "ALLNODES" and
                card["options"].get("FREQUENCY") == "1",
                f"{case}: output request is not full-frequency ALLNODES")
        actual = [part.strip().upper() for line in card_data(card)
                  for part in line.split(",") if part.strip()]
        require(actual == fields, f"{case}: nodal output fields differ")
    require(contact_file[0]["options"].get("FREQUENCY") == "1" and
            [part.strip().upper() for line in card_data(contact_file[0])
             for part in line.split(",") if part.strip()] == wanted["CONTACT_FILE"],
            f"{case}: CDIS/CSTR contact output request differs")


def numeric_rows(path, width):
    rows = []
    for line in path.read_text().splitlines():
        fields = line.split()
        if not fields or not fields[0].isdigit():
            continue
        require(len(fields) == width, f"Malformed {path.name} row: {line}")
        rows.append(fields)
    require(rows, f"No numeric rows in {path.name}")
    return rows


def convergence(folder, case, expected):
    contract = expected["requested_outputs"]["trace_contract"]
    cvg = numeric_rows(folder / "coupon.cvg",
                       len(contract["cvg_iteration_columns"]) + 5)
    keys = [tuple(map(parse_int, row[:4])) for row in cvg]
    require(len(keys) == len(set(keys)), "Duplicate CVG iteration identity")
    for row in cvg:
        for value in row[4:]:
            number(value)
    groups = {}
    for step, increment, attempt, iteration in keys:
        groups.setdefault((step, increment, attempt), []).append(iteration)
    require(set(groups) == {(1, 1, 1)}, "Unexpected CVG step/increment/attempt")
    for identity, iterations in groups.items():
        require(iterations == list(range(1, len(iterations) + 1)),
                f"Incomplete CVG iteration sequence {identity}")

    transcripts, full_transcript = {}, False
    for name in ("coupon.stdout", "coupon.log"):
        path = folder / name
        if not path.exists():
            continue
        contents = path.read_text(errors="replace")
        require("*ERROR" not in contents.upper(), f"Native error in {name}")
        step = increment = attempt = None
        printed = []
        for line in contents.splitlines():
            if match := re.fullmatch(r"\s*STEP\s+(\d+)\s*", line):
                step = int(match[1])
                increment = attempt = None
            elif match := re.fullmatch(r"\s*increment\s+(\d+)\s+attempt\s+(\d+)\s*", line):
                increment, attempt = map(int, match.groups())
            elif match := re.fullmatch(r"\s*iteration\s+(\d+)\s*", line):
                require(None not in (step, increment, attempt),
                        f"Iteration lacks full identity in {name}")
                printed.append((step, increment, attempt, int(match[1])))
        if printed:
            require(len(printed) == len(set(printed)) and all(k in keys for k in printed),
                    f"{name}/CVG iteration identities differ")
            indices = [keys.index(key) for key in printed]
            require(indices == sorted(indices), f"{name} iteration order differs")
            transcripts[name] = len(printed)
            full_transcript = full_transcript or printed == keys
    require(full_transcript, "Missing full native iteration transcript")
    stderr = folder / "coupon.stderr"
    require(not stderr.exists() or "*ERROR" not in stderr.read_text(errors="replace").upper(),
            "Native error in coupon.stderr")

    mortar = expected["cases"][case]["contact_type"] == "MORTAR"
    max_iteration = max(key[3] for key in keys)
    if mortar:
        limit = expected["requested_outputs"]["trace_contract"][
            "mortar_max_captured_iteration"]
        require(max_iteration <= limit, "MORTAR source override threshold reached")

    sta_rows = numeric_rows(folder / "coupon.sta", len(contract["sta_accepted_columns"]))
    accepted, rejected = [], []
    for row in sta_rows:
        rejected_row = row[2].endswith("U")
        step, increment = parse_int(row[0]), parse_int(row[1])
        attempt = parse_int(row[2].removesuffix("U"))
        iterations = parse_int(row[3])
        require(groups.get((step, increment, attempt), [])[-1:] == [iterations],
                "STA iteration differs from final CVG row")
        total, relative, size = map(number, row[4:])
        if rejected_row:
            rejected.append([step, increment, attempt, iterations])
            continue
        require((step, increment, attempt) == (1, 1, 1) and iterations >= 2,
                "Invalid accepted state identity or mechanical iteration count")
        accepted.append({"step": step, "increment": increment, "attempt": attempt,
                         "iterations": iterations, "total": total,
                         "relative": relative, "increment_size": size})
    require(not rejected, "One-step fixture has a rejected attempt or cutback")
    require(len(accepted) == 1, "Expected exactly one accepted increment")
    state = accepted[0]
    require(state["step"] == contract["steps"] == 1 and
            state["increment"] == contract["accepted_increments"]["1"] == 1 and
            state["attempt"] == 1, "Accepted increment differs from frozen trace contract")
    for value, key in ((state["relative"], "accepted_relative_time"),
                       (state["total"], "accepted_total_time"),
                       (state["increment_size"], "accepted_relative_time")):
        compare_numbers(value, contract[key], f"Accepted time {key}", 2e-6)
    require(set(groups) == {(state["step"], state["increment"], state["attempt"])},
            "CVG contains an unaccepted or extra attempt")
    require(keys[-1] == (state["step"], state["increment"], state["attempt"],
                         state["iterations"]), "Unaccepted terminal CVG tail")
    return state, {"cvg_rows": len(keys), "transcript_iteration_counts": transcripts,
                   "max_iteration": max_iteration, "rejected_attempts": rejected}


def parse_dat(path, node_ids):
    result, active = {}, None
    header = re.compile(
        r"\s*(displacements|forces).*for set (\w+) and time\s+(\S+)", re.IGNORECASE)
    for line in path.read_text().splitlines():
        match = header.match(line)
        if match:
            quantity, nset, time = match.groups()
            require(nset.upper() == "ALLNODES", f"Unexpected DAT set {nset}")
            key = (number(time), quantity.lower())
            require(key not in result, f"Duplicate DAT field {key}")
            active = result[key] = {}
            continue
        fields = line.split()
        if active is not None and len(fields) == 4 and fields[0].isdigit():
            node = parse_int(fields[0])
            require(node in node_ids and node not in active, "Bad/duplicate DAT node")
            active[node] = tuple(number(value) for value in fields[1:])
    require(result, "No nodal DAT evidence")
    require(all(set(values) == node_ids for values in result.values()),
            "Incomplete DAT node coverage")
    return result


def frd_fields(path, state, node_ids, expected, case, deck_audit):
    blocks, time, identity = [], None, None
    active, labels, kind = None, [], None
    for line in path.read_text(errors="replace").splitlines():
        fields = line.split()
        if fields and fields[0] == "1PSTEP":
            require(active is None, "Unterminated FRD dataset")
            require(len(fields) >= 4, "Malformed FRD step identity")
            identity = (parse_int(fields[3]), parse_int(fields[2]))
        elif fields and fields[0] == "100CL":
            require(len(fields) >= 3, "Malformed FRD time record")
            time = number(fields[2])
        elif line.startswith(" -4"):
            require(active is None, "Unterminated FRD field")
            require(len(fields) >= 2, "Malformed FRD field header")
            kind = fields[1]
            require(kind in ("DISP", "FORC", "CONTACT"), f"Unexpected FRD field {kind}")
            active, labels = {}, []
        elif active is not None and line.startswith(" -5"):
            require(len(fields) >= 2, "Malformed FRD component header")
            labels.append(fields[1])
        elif active is not None and line.startswith(" -1"):
            require(len(line) >= 13, "Malformed FRD node record")
            node = parse_int(line[3:13])
            require(node in node_ids and node not in active, "Bad/duplicate FRD node")
            values = [number(line[offset:offset + 12])
                      for offset in range(13, len(line.rstrip()), 12)]
            require(len(values) == (6 if kind == "CONTACT" else 3),
                    f"Malformed FRD {kind} record")
            active[node] = values
        elif active is not None and line.startswith(" -3"):
            require(time is not None and identity is not None and active,
                    "Empty/untimed FRD block")
            require(identity == (state["step"], state["increment"]) and
                    close(time, state["total"], 2e-6),
                    "FRD dataset does not match accepted endpoint")
            require(not any(block["identity"] == identity and block["kind"] == kind
                            for block in blocks), "Duplicate FRD field/state")
            if kind == "CONTACT":
                wanted_labels = expected["requested_outputs"]["FRD_CONTACT"]["component_labels"]
                require(labels == wanted_labels, "Unexpected FRD CONTACT components")
                min_nodes = expected["requested_outputs"]["FRD_CONTACT"][
                    "minimum_finite_nodes_per_block"]
                require(len(active) >= min_nodes, "FRD CONTACT block has too few nodes")
                diagnostics = {
                    "COPEN_min": min(values[0] for values in active.values()),
                    "COPEN_max": max(values[0] for values in active.values()),
                    "CPRESS_min": min(values[3] for values in active.values()),
                    "CPRESS_max": max(values[3] for values in active.values()),
                }
                contact_nodes = set(active)
                slave_nodes = deck_audit["slave_nodes"]
                diagnostics["distinct_slave_node_coverage"] = len(contact_nodes & slave_nodes)
                diagnostics["distinct_slave_node_coverage_reference"] = \
                    expected["requested_outputs"]["FRD_CONTACT"][
                        "expected_unique_slave_node_coverage_reference"][case]
                diagnostics["distinct_slave_node_coverage_fraction"] = (
                    diagnostics["distinct_slave_node_coverage"] /
                    diagnostics["distinct_slave_node_coverage_reference"])
                diagnostics["coverage_is_diagnostic"] = True
            else:
                require(set(active) == node_ids, f"Incomplete FRD {kind} node coverage")
                wanted = ["D1", "D2", "D3", "ALL"] if kind == "DISP" else [
                    "F1", "F2", "F3", "ALL"]
                require(labels == wanted, f"Wrong FRD {kind} components")
                diagnostics = {}
            blocks.append({"time": time, "identity": identity, "kind": kind,
                           "nodes": len(active), **diagnostics})
            active = None
    require(active is None, "Truncated FRD block")
    minimum = expected["requested_outputs"]["FRD_CONTACT"]["minimum_contact_blocks"]
    contact_blocks = [block for block in blocks if block["kind"] == "CONTACT"]
    require(len(contact_blocks) >= minimum, "Missing finite FRD CONTACT field block")
    for kind in ("DISP", "FORC"):
        require(any(block["kind"] == kind and
                    block["identity"] == (state["step"], state["increment"])
                    for block in blocks), f"Missing accepted-state FRD {kind}")
    require(expected["requested_outputs"]["FRD_CONTACT"][
                "coverage_beyond_minimum_is_diagnostic"] is True,
            "Unexpected FRD contact coverage contract")
    return blocks


def audit_known_answer(case, state, parsed_deck, expected, fields):
    fixture = expected["fixture"]
    endpoint = expected["analytical_known_answer"]["compression_endpoint"]
    load_oracle = expected["load_and_reaction_oracle"]
    time_matches = [key for key in fields if key[1] == "displacements" and
                    close(key[0], state["total"], 2e-6)]
    force_matches = [key for key in fields if key[1] == "forces" and
                     close(key[0], state["total"], 2e-6)]
    require(len(time_matches) == len(force_matches) == 1,
            "DAT does not contain exactly one U/RF endpoint")
    require(len(fields) == 2, "Unexpected DAT state or field")
    displacement = fields[time_matches[0]]
    reactions = fields[force_matches[0]]
    nodes = parsed_deck["nodes"]
    node_groups = fixture["body_node_groups"]
    oracle_u = {int(label): tuple(vector)
                for label, vector in endpoint["expected_node_displacements_mm"].items()}
    require(set(oracle_u) == set(nodes), "Analytical node profile does not cover fixture")
    profile_tol = endpoint["profile_gate"]["normal_profile_max_abs_error_mm"]
    gap_tol = endpoint["profile_gate"][
        "contact_interface_gap_and_face_warp_max_abs_error_mm"]
    profile_errors = {"CENTRAL_UX": [], "CENTRAL_UZ": [],
                      "LEFT_UX": [], "LOWER_UZ": []}
    for node in node_groups["CENTRAL"]:
        profile_errors["CENTRAL_UX"].append(abs(displacement[node][0] - oracle_u[node][0]))
        profile_errors["CENTRAL_UZ"].append(abs(displacement[node][2] - oracle_u[node][2]))
    for node in node_groups["LEFT"]:
        profile_errors["LEFT_UX"].append(abs(displacement[node][0] - oracle_u[node][0]))
    for node in node_groups["LOWER"]:
        profile_errors["LOWER_UZ"].append(abs(displacement[node][2] - oracle_u[node][2]))
    max_profile_error = max(max(values) for values in profile_errors.values())
    require(max_profile_error <= profile_tol,
            f"Normal displacement profile exceeds {profile_tol:g} mm")

    face_node_sets = parsed_deck["surface_nodes"]
    all_gaps, face_warp_errors = {}, {}
    for axis, central_name, outer_name, dof, coordinate_indices in (
        ("X", "X_CENTRAL", "X_LEFT", 0, (1, 2)),
        ("Z", "Z_CENTRAL", "Z_LOWER", 2, (0, 1)),
    ):
        central = face_node_sets[central_name]
        outer = face_node_sets[outer_name]
        outer_by_coord = {tuple(nodes[node][index] for index in coordinate_indices): node
                          for node in outer}
        require(len(outer_by_coord) == len(outer), f"Duplicate {axis} face coordinates")
        require(len(central) == len(outer) == 9, f"Incomplete {axis} interface face")
        gaps, gap_warp = [], []
        for node in central:
            key = tuple(nodes[node][index] for index in coordinate_indices)
            require(key in outer_by_coord, f"Unmatched {axis} interface node")
            other = outer_by_coord[key]
            actual_gap = displacement[node][dof] - displacement[other][dof]
            expected_gap = oracle_u[node][dof] - oracle_u[other][dof]
            gaps.append(actual_gap)
            gap_warp.append(abs(actual_gap - expected_gap))
        all_gaps[axis] = gaps
        require(max(gap_warp) <= gap_tol, f"{axis} interface gap exceeds tolerance")
        for face_name, face_nodes in ((central_name, central), (outer_name, outer)):
            actual_values = [displacement[node][dof] for node in face_nodes]
            expected_values = [oracle_u[node][dof] for node in face_nodes]
            actual_warp = max(actual_values) - min(actual_values)
            expected_warp = max(expected_values) - min(expected_values)
            face_warp_errors[face_name] = abs(actual_warp - expected_warp)
    max_face_warp_error = max(face_warp_errors.values())
    require(max_face_warp_error <= gap_tol, "Interface face warp exceeds tolerance")
    target_gap = endpoint["interface_central_minus_outer_signed_gap_mm"]
    max_gap_error = max(abs(gap - target_gap) for gaps in all_gaps.values() for gap in gaps)
    require(max_gap_error <= gap_tol, "Role-independent interface signed gap fails")

    support_groups = load_oracle["support_reaction_dof_groups"]
    force_rel_tol = load_oracle["normal_support_force_relative_tolerance"]
    force_abs_tol = load_oracle["normal_support_force_absolute_tolerance_N"]
    transverse_tol = load_oracle["transverse_and_auxiliary_support_resultant_norm_tolerance_N"]
    reaction_groups = {}
    for name, spec in support_groups.items():
        dof = spec["dof"] - 1
        actual = sum(reactions[node][dof] for node in spec["nodes"])
        target = spec["expected_sum_N"]
        if abs(target) > 0:
            tolerance = force_rel_tol * abs(target) + force_abs_tol
        else:
            tolerance = transverse_tol
        require(abs(actual - target) <= tolerance,
                f"Support reaction group {name} differs: {actual:.8g} vs {target:.8g} N")
        reaction_groups[name] = actual

    x_group = support_groups["LEFT_REMOTE_NORMAL"]
    z_group = support_groups["LOWER_REMOTE_NORMAL"]
    x_force = reaction_groups["LEFT_REMOTE_NORMAL"]
    z_force = reaction_groups["LOWER_REMOTE_NORMAL"]
    expected_force = endpoint["contact_force_magnitude_N_per_axis"]
    force_tolerance = force_rel_tol * expected_force + force_abs_tol
    require(abs(x_force - expected_force) <= force_tolerance and
            abs(z_force - expected_force) <= force_tolerance,
            "Remote normal support forces do not match the analytical endpoint")

    normal_dofs = set()
    for group in (x_group, z_group):
        normal_dofs.update((node, group["dof"] - 1) for node in group["nodes"])
    auxiliary_reaction = [0.0, 0.0, 0.0]
    constrained = parsed_deck["boundaries"]
    for node, dof in constrained:
        if (node, dof - 1) not in normal_dofs:
            auxiliary_reaction[dof - 1] += reactions[node][dof - 1]
    require(norm(auxiliary_reaction) <= transverse_tol,
            "Combined tangential/auxiliary support reaction exceeds tolerance")

    signed_approach = {}
    for axis, center_face, support_name, dof, group_name in (
        ("X", "CENTRAL_RIGHT", "LEFT_REMOTE_UX", 0, "LEFT_REMOTE_UX"),
        ("Z", "CENTRAL_TOP", "LOWER_REMOTE_UZ", 2, "LOWER_REMOTE_UZ"),
    ):
        central_nodes = fixture["contact_faces"][center_face]["nodes"]
        support_nodes = load_oracle["support_resultant_node_groups"][support_name]
        center_mean = sum(displacement[node][dof] for node in central_nodes) / len(central_nodes)
        support_mean = sum(displacement[node][dof] for node in support_nodes) / len(support_nodes)
        signed_approach[axis] = center_mean - support_mean
        target_approach = endpoint["outer_remote_to_central_face_signed_displacement_mm"]
        require(abs(signed_approach[axis] - target_approach) <= profile_tol,
                f"{axis} remote-to-central approach differs")

    # The two remote support DOFs are independent series springs in this oracle.
    analytic_compliance = endpoint["axis_compliance_mm3_per_N"]
    compliance_relative_tol = expected["analytical_known_answer"][
        "normal_compliance_relative_tolerance"]
    compliance_absolute_tol = expected["analytical_known_answer"][
        "normal_compliance_absolute_tolerance_mm3_per_N"]
    compliance = {}
    for axis, approach, force in (("X", signed_approach["X"], x_force),
                                  ("Z", signed_approach["Z"], z_force)):
        measured = abs(approach) / abs(force)
        limit = compliance_relative_tol * analytic_compliance + compliance_absolute_tol
        require(abs(measured - analytic_compliance) <= limit,
                f"{axis} endpoint series compliance differs")
        compliance[axis] = measured

    applied_force = [0.0, 0.0, 0.0]
    applied_moment = [0.0, 0.0, 0.0]
    for (node, dof), value in parsed_deck["loads"].items():
        force = [0.0, 0.0, 0.0]
        force[dof - 1] = value
        position = add(nodes[node], displacement[node])
        for i, item in enumerate(force):
            applied_force[i] += item
        for i, item in enumerate(moment(position, force)):
            applied_moment[i] += item

    support_union = set(load_oracle["support_node_union_for_global_force_and_moment_closure"])
    require(support_union == {node for node, _ in constrained},
            "Frozen support union differs from explicit constrained DOFs")
    constrained_reaction = {}
    for node, dof in constrained:
        if node in support_union:
            constrained_reaction[(node, dof)] = reactions[node][dof - 1]
        else:
            require(abs(reactions[node][dof - 1]) <= transverse_tol,
                    f"Unexpected constrained reaction outside support union: {node}/{dof}")
    support_force = [0.0, 0.0, 0.0]
    support_moment = [0.0, 0.0, 0.0]
    for (node, dof), value in constrained_reaction.items():
        force = [0.0, 0.0, 0.0]
        force[dof - 1] = value
        position = add(nodes[node], displacement[node])
        for i, item in enumerate(force):
            support_force[i] += item
        for i, item in enumerate(moment(position, force)):
            support_moment[i] += item
    force_closure = add(tuple(applied_force), tuple(support_force))
    moment_closure = add(tuple(applied_moment), tuple(support_moment))
    force_target = load_oracle["applied_plus_support_expected_force_closure_N"]
    moment_target = load_oracle["applied_plus_support_expected_moment_closure_Nmm"]
    require(norm(tuple(force_closure[i] - force_target[i] for i in range(3))) <=
            load_oracle["global_force_closure_norm_tolerance_N"],
            "Global applied-plus-support force closure fails")
    require(norm(tuple(moment_closure[i] - moment_target[i] for i in range(3))) <=
            load_oracle["global_moment_closure_norm_tolerance_Nmm"],
            "Global applied-plus-support first-moment closure fails")

    return {
        "max_normal_profile_error_mm": max_profile_error,
        "normal_profile_errors_mm": {key: max(values) for key, values in profile_errors.items()},
        "interface_gap_errors_mm": {axis: max(abs(gap - target_gap) for gap in gaps)
                                     for axis, gaps in all_gaps.items()},
        "max_interface_face_warp_error_mm": max_face_warp_error,
        "interface_face_warp_errors_mm": face_warp_errors,
        "signed_interface_gaps_mm": {axis: [min(gaps), max(gaps)]
                                     for axis, gaps in all_gaps.items()},
        "signed_outer_approach_mm": signed_approach,
        "normal_support_resultants_N": {"X": x_force, "Z": z_force},
        "support_reaction_groups_N": reaction_groups,
        "combined_auxiliary_reaction_N": auxiliary_reaction,
        "series_compliance_mm3_per_N": compliance,
        "global_force_closure_N": force_closure,
        "global_moment_closure_Nmm": moment_closure,
        "non_normal_displacement_diagnostics_mm": {
            "CENTRAL_UY": max(abs(displacement[node][1])
                              for node in node_groups["CENTRAL"]),
            "LEFT_UY_UZ": max(abs(displacement[node][dof])
                               for node in node_groups["LEFT"] for dof in (1, 2)),
            "LOWER_UX_UY": max(abs(displacement[node][dof])
                                for node in node_groups["LOWER"] for dof in (0, 1)),
        },
    }


def audit_case(case, expected, execution):
    case_spec = expected["cases"][case]
    folder = HERE / "output" / case
    require(execution == read_json(folder / "execution.json"),
            f"{case}: root/case execution records differ")
    require(execution["status"] == "completed" and execution["stop_reason"] is None,
            f"{case}: native run did not finish normally")
    state = execution["container_state"]
    require(execution["docker_cli_exit_code"] == state["ExitCode"] == 0 and
            not state["Running"] and not state["OOMKilled"],
            f"{case}: bad terminal container state")
    require(execution["container_image"] == expected["solver"]["base_image_id"],
            f"{case}: wrong container image")
    command = execution["command"]
    container = execution["container"]
    require(re.fullmatch(rf"wj-mortar-fixture-{re.escape(case)}-\d+", container) is not None,
            f"{case}: unexpected container name")
    require("--user" in command, f"{case}: missing explicit container user")
    user_index = command.index("--user")
    require(user_index + 1 < len(command) and
            re.fullmatch(r"\d+:\d+", command[user_index + 1]) is not None,
            f"{case}: malformed container user")
    expected_command = [
        "docker", "run", "--pull=never", "--name", container,
        "--network", "none", "--cpus", "1", "--memory", "1g",
        "--memory-swap", "1g", "--user", command[user_index + 1],
        "--env", "OMP_NUM_THREADS=1", "--env", "CCX_NPROC_EQUATION_SOLVER=1",
        "--mount", f"type=bind,src={folder.resolve()},dst=/work",
        "--workdir", "/work", expected["solver"]["base_image_id"],
        expected["solver"]["binary_path"], "-i", "coupon",
    ]
    require(command == expected_command, f"{case}: invoked command differs from frozen runner")
    limits = read_json(HERE / "input-freeze.json")["limits"]
    require(execution["elapsed_seconds"] <= limits["seconds_per_case"],
            f"{case}: native wall-time limit exceeded")
    require(execution["total_output_bytes"] <= limits["output_bytes_per_case"] and
            execution["max_log_bytes"] <= limits["stdout_or_stderr_bytes"],
            f"{case}: captured output exceeded frozen size limits")
    entries = list(folder.iterdir())
    require(all(path.is_file() for path in entries), f"{case}: unexpected output directory")
    output_files = {path.name for path in entries if path.name != "execution.json"}
    required_files = {"coupon.inp", "coupon.dat", "coupon.cvg", "coupon.sta", "coupon.frd",
                      "coupon.stdout", "coupon.stderr"}
    require(output_files >= required_files, f"{case}: required native output is missing")
    require(output_files == set(execution["outputs_sha256"]),
            f"{case}: output file inventory differs")
    for name, digest in execution["outputs_sha256"].items():
        require(sha(folder / name) == digest, f"{case}: output hash mismatch: {name}")
    require(sha(folder / "coupon.inp") == case_spec["sha256"],
            f"{case}: executed deck differs from expected hash")
    for name in ("coupon.stdout", "coupon.stderr"):
        require((folder / name).stat().st_size <= limits["stdout_or_stderr_bytes"],
                f"{case}: captured stream exceeds frozen bound")

    deck = audit_deck(case, case_spec, expected, folder / "coupon.inp")
    state_row, trace = convergence(folder, case, expected)
    data = parse_dat(folder / "coupon.dat", set(deck["nodes"]))
    known_answer = audit_known_answer(case, state_row, deck, expected, data)
    frd = frd_fields(folder / "coupon.frd", state_row, set(deck["nodes"]),
                     expected, case, deck)
    return {"status": "PASS", "accepted_state": state_row, "trace": trace,
            "known_answer": known_answer, "FRD_field_diagnostics": frd,
            "deck_role_checks": deck["role_checks"]}


def audit_analytic_metadata(expected):
    """Recompute the frozen linear series oracle from geometry and material data."""
    fixture = expected["fixture"]
    endpoint = expected["analytical_known_answer"]["compression_endpoint"]
    coords = {int(label): tuple(value)
              for label, value in fixture["node_coordinates_mm"].items()}
    bodies = fixture["body_node_groups"]
    central = [coords[node] for node in bodies["CENTRAL"]]
    left = [coords[node] for node in bodies["LEFT"]]
    lower = [coords[node] for node in bodies["LOWER"]]
    left_min_x = min(value[0] for value in left)
    lower_min_z = min(value[2] for value in lower)
    span_x = max(value[0] for value in central) - left_min_x
    span_z = max(value[2] for value in central) - lower_min_z
    material = fixture["material_and_contact"]
    modulus = material["youngs_modulus_N_per_mm2"]
    stiffness = material["linear_pressure_overclosure_slope_K_N_per_mm3"]
    pressure = endpoint["pressure_N_per_mm2"]
    require(modulus > 0 and stiffness > 0 and pressure > 0 and
            close(material["poisson_ratio"], 0.0, 1e-12),
            "Analytical coupon requires positive E/K/load and nu=0")
    compliance_x = span_x / modulus + 1 / stiffness
    compliance_z = span_z / modulus + 1 / stiffness
    gap = -pressure / stiffness
    approach_x = -pressure * compliance_x
    approach_z = -pressure * compliance_z
    force_x = pressure * fixture["contact_faces"]["CENTRAL_RIGHT"]["area_mm2"]
    force_z = pressure * fixture["contact_faces"]["CENTRAL_TOP"]["area_mm2"]
    compare_numbers(compliance_x, endpoint["axis_compliance_mm3_per_N"],
                    "Analytical X series compliance", 1e-12)
    compare_numbers(compliance_z, endpoint["axis_compliance_mm3_per_N"],
                    "Analytical Z series compliance", 1e-12)
    compare_numbers(compliance_x, expected["analytical_known_answer"][
        "normal_compliance_mm3_per_N"], "Recorded normal compliance", 1e-12)
    compare_numbers(gap, endpoint["interface_central_minus_outer_signed_gap_mm"],
                    "Analytical interface gap", 1e-12)
    compare_numbers(-gap, endpoint["interface_contact_law_overclosure_mm"],
                    "Analytical contact overclosure", 1e-12)
    compare_numbers(abs(approach_x), endpoint["outer_remote_to_central_face_approach_mm"],
                    "Analytical X approach", 1e-12)
    compare_numbers(abs(approach_z), endpoint["outer_remote_to_central_face_approach_mm"],
                    "Analytical Z approach", 1e-12)
    compare_numbers(approach_x, endpoint["outer_remote_to_central_face_signed_displacement_mm"],
                    "Analytical signed X approach", 1e-12)
    compare_numbers(approach_z, endpoint["outer_remote_to_central_face_signed_displacement_mm"],
                    "Analytical signed Z approach", 1e-12)
    compare_numbers(force_x, endpoint["contact_force_magnitude_N_per_axis"],
                    "Analytical X contact force", 1e-10)
    compare_numbers(force_z, endpoint["contact_force_magnitude_N_per_axis"],
                    "Analytical Z contact force", 1e-10)
    load_oracle = expected["load_and_reaction_oracle"]
    force_tolerance = (load_oracle["normal_support_force_relative_tolerance"] *
                       endpoint["contact_force_magnitude_N_per_axis"] +
                       load_oracle["normal_support_force_absolute_tolerance_N"])
    compare_numbers(force_tolerance, load_oracle["global_force_closure_norm_tolerance_N"],
                    "Declared global force tolerance", 1e-12)
    compare_numbers(force_tolerance,
                    load_oracle["transverse_and_auxiliary_support_resultant_norm_tolerance_N"],
                    "Declared auxiliary reaction tolerance", 1e-12)
    moment_tolerance = (
        load_oracle["global_moment_closure_relative_tolerance"] *
        endpoint["contact_force_magnitude_N_per_axis"] *
        load_oracle["global_moment_closure_reference_length_mm"] +
        load_oracle["global_moment_closure_absolute_floor_Nmm"])
    compare_numbers(moment_tolerance,
                    load_oracle["global_moment_closure_norm_tolerance_Nmm"],
                    "Declared global first-moment tolerance", 1e-12)

    oracle = {int(label): tuple(value) for label, value in
              endpoint["expected_node_displacements_mm"].items()}
    require(set(oracle) == set(coords), "Analytical displacement table node set differs")
    recomputed = {}
    for body, labels in bodies.items():
        for node in labels:
            x, _, z = coords[node]
            if body == "CENTRAL":
                value = (-pressure * ((x - left_min_x) / modulus + 1 / stiffness),
                         0.0,
                         -pressure * ((z - lower_min_z) / modulus + 1 / stiffness))
            elif body == "LEFT":
                value = (-pressure * (x - left_min_x) / modulus, 0.0, 0.0)
            elif body == "LOWER":
                value = (0.0, 0.0, -pressure * (z - lower_min_z) / modulus)
            else:
                raise ValueError(f"Unknown body in displacement oracle: {body}")
            recomputed[node] = value
            for actual, target in zip(oracle[node], value):
                compare_numbers(actual, target, f"Analytical displacement node {node}", 1e-12)
    require(set(recomputed) == set(oracle), "Analytical bodies do not cover all nodes")
    profile_tol = endpoint["profile_gate"]["normal_profile_max_abs_error_mm"]
    compare_numbers(endpoint["profile_gate"]["relative_to_outer_approach"],
                    profile_tol / abs(approach_x),
                    "Profile tolerance fraction of approach", 1e-12)


def audit_root():
    expected = read_json(HERE / "expected.json")
    freeze_path = HERE / "input-freeze.json"
    execution_path = HERE / "execution.json"
    freeze = read_json(freeze_path)
    execution = read_json(execution_path)
    require(expected["schema"] == "calculix_mortar_shared_edge_known_answer/v1",
            "Unexpected expected.json schema")
    require(execution.get("schema") == "mortar_shared_edge_execution/v1",
            "Unexpected root execution schema")
    require(set(expected["cases"]) == CASES and set(expected["case_order"]) == CASES,
            "Expected case set differs")
    require(expected["solver"]["patched_or_instrumented_binary"] is False,
            "Method coupon must use the pinned uninstrumented binary")
    require(expected["mechanical_or_joint_acceptance"] is False and
            expected["release"] is False and expected["native_solver_launched"] is False,
            "Prepared expected artifact must not claim joint/release acceptance")
    acceptance = expected["acceptance"]
    required_gates = (
        "require_all_81_nodes_U_and_RF_in_DAT_and_FRD",
        "require_all_captured_MORTAR_iit_at_or_below",
        "require_contact_CDIS_and_CSTR_finite",
        "require_exactly_one_accepted_increment",
        "require_force_and_moment_resultant_closure",
        "require_no_rejected_attempt_or_cutback",
        "require_normal_profiles_interface_gap_and_face_warp",
        "require_normal_support_force_each_axis",
        "require_same_contact_type_for_both_pairs_in_each_deck",
        "require_two_pairs_per_deck",
        "require_zero_explicit_SPC_overlap_with_any_slave_contact_node",
    )
    require(all(acceptance[key] is True for key in required_gates),
            "Prepared acceptance contract omits a required gate")
    require(acceptance["require_contact_field_sign_or_pointwise_law"] is False and
            acceptance["FRD_contact_coverage_beyond_minimum_is_diagnostic"] is True,
            "Contact-field acceptance exceeds the frozen diagnostic scope")
    require(expected["requested_outputs"]["FRD_CONTACT"]["minimum_contact_blocks"] ==
            acceptance["minimum_FRD_contact_blocks_per_case"] and
            expected["requested_outputs"]["FRD_CONTACT"][
                "minimum_finite_nodes_per_block"] ==
            acceptance["minimum_finite_FRD_contact_nodes_per_block"],
            "FRD contact minima differ between request and acceptance contract")
    audit_analytic_metadata(expected)
    require(execution["input_freeze_sha256"] == sha(freeze_path),
            "Root execution freeze hash differs")
    require(freeze["schema"] == "mortar_shared_edge_freeze/v1",
            "Unexpected input-freeze schema")
    require(execution["image_id"] == freeze["image_id"] ==
            expected["solver"]["base_image_id"], "Root/freeze image pin mismatch")
    require(execution["binary_sha256"] == freeze["binary_sha256"] ==
            expected["solver"]["binary_sha256"], "Root/freeze binary hash mismatch")
    require(freeze["binary_path"] == expected["solver"]["binary_path"],
            "Frozen binary path differs")
    for relative, digest in freeze["files_sha256"].items():
        require(sha(HERE / relative) == digest, f"Frozen artifact differs: {relative}")
    required_frozen = {"README.md", "prepare.py", "expected.json", "readiness.json",
                       "parent-review.json", "verifier.py", "run.py"}
    require(required_frozen <= set(freeze["files_sha256"]),
            "Frozen artifact inventory is incomplete")
    require(execution["status"] == "completed_pending_audit" and
            execution["frozen_inputs_unchanged"] is True,
            "Root execution is incomplete or frozen inputs changed")
    require(execution["mechanical_acceptance"] is False and
            execution["joint_acceptance"] is False and execution["release"] is False,
            "Coupon execution must not claim joint/release acceptance")
    require(len(freeze["cases"]) == len(CASES) and set(freeze["cases"]) == CASES,
            "Frozen run case inventory differs")
    require(freeze["cases"] == expected["case_order"],
            "Frozen run order differs from expected case order")
    runs = execution["runs"]
    require(len(runs) == len(CASES) and [run["case"] for run in runs] ==
            expected["case_order"], "Missing, duplicate, or reordered case execution")
    require(len({run["container"] for run in runs}) == len(CASES),
            "Case container names are not unique")
    for case, spec in expected["cases"].items():
        require(spec["path"] in freeze["files_sha256"] and
                spec["sha256"] == freeze["files_sha256"][spec["path"]],
                f"{case}: expected input digest differs from freeze")
    results = {}
    for run in runs:
        case = run["case"]
        try:
            results[case] = audit_case(case, expected, run)
        except Exception as exc:
            results[case] = {"status": "FAIL", "error": str(exc)}
    if not all(result["status"] == "PASS" for result in results.values()):
        return {"status": "FAIL", "error": "One or more case audits failed",
                "cases": results, "mechanical_acceptance": False,
                "joint_acceptance": False, "release": False}
    return {"status": "PASS_SHARED_EDGE_METHOD_FIXTURE", "cases": results,
            "mechanical_acceptance": False, "joint_acceptance": False, "release": False}


def audit():
    try:
        return audit_root()
    except Exception as exc:
        return {"status": "FAIL", "error": str(exc), "mechanical_acceptance": False,
                "joint_acceptance": False, "release": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    result["verifier_sha256"] = sha(Path(__file__))
    execution_path = HERE / "execution.json"
    result["execution_sha256"] = sha(execution_path) if execution_path.exists() else None
    if args.write:
        with (HERE / "verifier.json").open("x") as stream:
            json.dump(result, stream, indent=2, sort_keys=True)
            stream.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key != "cases"}))
    raise SystemExit(0 if result["status"] == "PASS_SHARED_EDGE_METHOD_FIXTURE" else 1)
