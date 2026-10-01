#!/usr/bin/env python3
"""Parent's independent exact-geometry and one-free-coordinate deck audit."""

import argparse
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "implicit-contact-point-trace-attempt01/input/implicit_point_trace.inp"
SOURCE_SHA = "e9d0ec2252201fdaa249b5e884c9290a128fb31c135afff6e08c566cb504c61b"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value):
    return F(value.replace("D", "E").replace("d", "e"))


def cards(path):
    result = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            fields = [part.strip().upper() for part in line[1:].split(",")]
            opts = {}
            for field in fields[1:]:
                key, _, value = field.partition("=")
                require(key not in opts, "Repeated card option")
                opts[key] = value
            result.append({"name": fields[0], "opts": opts, "rows": []})
        else:
            require(result, "Data before first card")
            result[-1]["rows"].append([part.strip() for part in line.split(",") if part.strip()])
    return result


def geometry(deck):
    nodes, elements, sets = {}, {}, {}
    for card in deck:
        if card["name"] == "NODE":
            for row in card["rows"]:
                require(len(row) == 4, "Node row width differs")
                node = int(row[0])
                require(node not in nodes, "Duplicate node")
                nodes[node] = tuple(number(x) for x in row[1:])
        elif card["name"] == "ELEMENT":
            kind = card["opts"]["TYPE"]
            group = card["opts"].get("ELSET")
            for row in card["rows"]:
                elem = int(row[0])
                require(elem not in elements, "Duplicate element")
                elements[elem] = (kind, tuple(int(x) for x in row[1:]))
                if group:
                    sets.setdefault(group, set()).add(elem)
    return nodes, elements, sets


def determinant(rows):
    a, b, c = rows
    return (a[0] * (b[1]*c[2] - b[2]*c[1])
            - a[1] * (b[0]*c[2] - b[2]*c[0])
            + a[2] * (b[0]*c[1] - b[1]*c[0]))


def audit():
    require(sha(SOURCE) == SOURCE_SHA, "Original coupon source changed")
    path = HERE / "input/coupon.inp"
    deck = cards(path)
    original_nodes, original_elements, _ = geometry(cards(SOURCE))
    nodes, elements, elsets = geometry(deck)
    wanted_elements = {key: value for key, value in original_elements.items() if value[0] == "C3D10"}
    require(elements == wanted_elements and len(elements) == 12, "C3D10 geometry differs from source")
    physical = set().union(*(set(conn) for _, conn in elements.values()))
    require(len(physical) == 54 and set(nodes) == physical | {8001}, "Node roles/counts differ")
    require(all(nodes[n] == original_nodes[n] for n in physical), "Physical node geometry changed")
    require(nodes[8001] == (F(1), F(1), F(1)), "Controller coordinates differ")
    require(set(elsets) == {"UPPER", "LOWER"}, "Element groups differ")
    upper = set().union(*(set(elements[e][1]) for e in elsets["UPPER"]))
    lower = set().union(*(set(elements[e][1]) for e in elsets["LOWER"]))
    require(len(upper) == len(lower) == 27 and not upper & lower, "Body connectivity differs")

    nsets = {}
    for card in deck:
        if card["name"] == "NSET":
            require("GENERATE" not in card["opts"], "Explicit node sets required for this audit")
            label = card["opts"]["NSET"]
            require(label not in nsets, "Repeated node set")
            nsets[label] = [value.upper() for row in card["rows"] for value in row]

    def resolve(target, trail=()):
        if target.isdigit():
            node = int(target)
            require(node in nodes, "Unknown boundary/initial/set node")
            return {node}
        require(target in nsets and target not in trail, "Unknown or cyclic node set")
        return set().union(*(resolve(x, trail + (target,)) for x in nsets[target]))

    require(resolve("N_UPPER") == upper and resolve("N_LOWER") == lower, "Body node sets differ")
    by_name = {}
    for card in deck:
        by_name.setdefault(card["name"], []).append(card)
    allowed = {"HEADING", "NODE", "ELEMENT", "NSET", "EQUATION", "MATERIAL", "DENSITY",
               "ELASTIC", "SOLID SECTION", "SURFACE", "SURFACE INTERACTION", "SURFACE BEHAVIOR",
               "CONTACT PAIR", "INITIAL CONDITIONS", "STEP", "DYNAMIC", "BOUNDARY",
               "NODE PRINT", "NODE FILE", "EL PRINT", "CONTACT PRINT", "END STEP"}
    require(set(by_name) <= allowed, "Unexpected control/loading/material card")
    require(len(by_name.get("STEP", [])) == len(by_name.get("DYNAMIC", [])) == 1, "One dynamic step required")
    step, dynamic = by_name["STEP"][0], by_name["DYNAMIC"][0]
    require(step["opts"] == {"NLGEOM": "", "INC": "70"}, "Step controls differ")
    require(dynamic["opts"] == {"DIRECT": "", "ALPHA": "0"}
            or dynamic["opts"] == {"DIRECT": "", "ALPHA": "0."}, "Dynamic controls differ")
    require([[number(x) for x in row] for row in dynamic["rows"]] == [[F(1, 10000), F(7, 1000)]], "Time schedule differs")

    fixed = {}
    for card in by_name.get("BOUNDARY", []):
        require(not card["opts"], "Boundary options not allowed")
        for target, first, last, value in card["rows"]:
            for node in resolve(target.upper()):
                for dof in range(int(first), int(last) + 1):
                    key = (node, dof)
                    require(key not in fixed and 1 <= dof <= 3, "Duplicate/invalid boundary DOF")
                    fixed[key] = number(value)
    wanted_fixed = {(n, d) for n in lower for d in (1, 2, 3)} | {(n, d) for n in upper | {8001} for d in (1, 2)}
    require(set(fixed) == wanted_fixed and all(v == 0 for v in fixed.values()), "Fixed DOFs differ")
    dependent = set()
    for card in by_name.get("EQUATION", []):
        require(not card["opts"], "Equation options unexpected")
        cursor = 0
        while cursor < len(card["rows"]):
            require(card["rows"][cursor] == ["2"], "Two-term homogeneous equation required")
            cursor += 1
            terms = []
            while len(terms) < 6 and cursor < len(card["rows"]):
                terms.extend(card["rows"][cursor])
                cursor += 1
            require(len(terms) == 6, "Equation term width differs")
            first = (int(terms[0]), int(terms[1]), number(terms[2]))
            second = (int(terms[3]), int(terms[4]), number(terms[5]))
            require(first[0] in upper and first[1:] == (3, F(1)) and second == (8001, 3, F(-1)), "Equation differs")
            require(first[0] not in dependent, "Repeated dependent DOF")
            dependent.add(first[0])
    require(dependent == upper, "Upper translation equations incomplete")
    free = {(n, d) for n in nodes for d in (1, 2, 3)} - set(fixed) - {(n, 3) for n in dependent}
    require(free == {(8001, 3)}, "Unexpected free DOF")
    velocity = {}
    for card in by_name.get("INITIAL CONDITIONS", []):
        require(card["opts"] == {"TYPE": "VELOCITY"}, "Only velocity initial conditions allowed")
        require(deck.index(card) < deck.index(step), "Initial condition must precede step")
        for target, dof, value in card["rows"]:
            for node in resolve(target.upper()):
                key = (node, int(dof))
                require(key not in velocity, "Repeated initial velocity")
                velocity[key] = number(value)
    require(set(velocity) == {(n, 3) for n in upper | {8001}}
            and set(velocity.values()) == {F(-1, 10)}, "Initial velocity field differs")

    require(len(by_name.get("MATERIAL", [])) == len(by_name.get("DENSITY", [])) == len(by_name.get("ELASTIC", [])) == 1, "One explicit material required")
    material = by_name["MATERIAL"][0]["opts"]["NAME"]
    require(by_name["DENSITY"][0]["rows"] and [[number(x) for x in r] for r in by_name["DENSITY"][0]["rows"]] == [[F(1, 8)]], "Density differs")
    require([[number(x) for x in r] for r in by_name["ELASTIC"][0]["rows"]] == [[F(100000), F(0)]], "Elastic data differs")
    sections = {c["opts"]["ELSET"]: c["opts"]["MATERIAL"] for c in by_name.get("SOLID SECTION", [])}
    require(sections == {"UPPER": material, "LOWER": material}, "Solid sections differ")
    volumes = {"UPPER": F(0), "LOWER": F(0)}
    edges = ((0, 1), (1, 2), (0, 2), (0, 3), (1, 3), (2, 3))
    for group, ids in elsets.items():
        for elem in ids:
            conn = elements[elem][1]
            require(len(conn) == 10, "C3D10 connectivity incomplete")
            points = [nodes[n] for n in conn]
            for middle, (i, j) in zip(points[4:], edges):
                require(middle == tuple((points[i][d] + points[j][d]) / 2 for d in range(3)), "Curved or misplaced midside node")
            det = determinant([[points[i][d] - points[0][d] for d in range(3)] for i in (1, 2, 3)])
            require(det > 0, "Nonpositive tetrahedral orientation")
            volumes[group] += det / 6
    require(volumes == {"UPPER": F(8), "LOWER": F(8)}, "Body volumes differ")
    surfaces = {c["opts"]["NAME"]: c["rows"] for c in by_name.get("SURFACE", [])}
    require(len(by_name.get("SURFACE", [])) == 2 and surfaces == {"SLAVE": [["1", "S1"], ["2", "S1"]], "MASTER": [["11", "S3"], ["12", "S3"]]}, "Contact faces differ")
    face_areas, face_vertices = {}, {}
    for label, rows in surfaces.items():
        face_areas[label], face_vertices[label] = F(0), set()
        for element_id, face in rows:
            conn = elements[int(element_id)][1]
            indices = (0, 1, 2) if face == "S1" else (1, 2, 3)
            points = [nodes[conn[i]] for i in indices]
            require(all(point[2] == 0 for point in points), "Interface is not initially coincident at z=0")
            a = [points[1][i] - points[0][i] for i in range(3)]
            b = [points[2][i] - points[0][i] for i in range(3)]
            cross = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
            norm_squared = sum(x*x for x in cross)
            magnitude = F(math.isqrt(norm_squared.numerator), math.isqrt(norm_squared.denominator))
            require(magnitude*magnitude == norm_squared and magnitude > 0, "Face area is not the expected rational area")
            inward = [sum(nodes[n][i] for n in conn[:4])/4 - sum(point[i] for point in points)/3 for i in range(3)]
            if sum(cross[i]*inward[i] for i in range(3)) > 0:
                cross = [-x for x in cross]
            require(tuple(x/magnitude for x in cross) == (0, 0, -1 if label == "SLAVE" else 1), "Outward interface normal differs")
            face_areas[label] += magnitude/2
            face_vertices[label].add(frozenset(points))
        require(face_areas[label] == 4 and len(face_vertices[label]) == 2, "Interface area/triangulation differs")
    require(face_vertices["SLAVE"] == face_vertices["MASTER"], "Interface triangles do not coincide")
    pair = by_name.get("CONTACT PAIR", [])
    require(len(pair) == 1 and pair[0]["rows"] == [["SLAVE", "MASTER"]]
            and pair[0]["opts"]["TYPE"] == "SURFACE TO SURFACE", "Contact pair differs")
    interactions = by_name.get("SURFACE INTERACTION", [])
    require(len(interactions) == 1 and interactions[0]["opts"]["NAME"] == pair[0]["opts"]["INTERACTION"], "Contact interaction is missing or ambiguous")
    law = by_name.get("SURFACE BEHAVIOR", [])
    require(len(law) == 1 and law[0]["opts"] == {"PRESSURE-OVERCLOSURE": "LINEAR"}
            and [[number(x) for x in r] for r in law[0]["rows"]] == [[F(100000)]], "Penalty law differs")
    for name in ("NODE PRINT", "NODE FILE"):
        require(len(by_name.get(name, [])) == 1, "Exactly one nodal output card required")
        card = by_name[name][0]
        require([x.upper() for r in card["rows"] for x in r] == ["U", "V"]
                and card["opts"].get("FREQUENCY") == "1", "Nodal output contract differs")
        if name == "NODE PRINT":
            require(resolve(card["opts"]["NSET"]) == set(nodes), "DAT observation set incomplete")
        elif "NSET" in card["opts"]:
            require(physical <= resolve(card["opts"]["NSET"]), "FRD physical coverage incomplete")
    element_prints = by_name.get("EL PRINT", [])
    require(len(element_prints) == 2 and {c["opts"]["ELSET"] for c in element_prints} == {"UPPER", "LOWER"}, "Element output groups differ")
    for card in element_prints:
        require(card["opts"].get("TOTALS") == "ONLY" and card["opts"].get("FREQUENCY") == "1"
                and [x.upper() for r in card["rows"] for x in r] == ["ELSE", "ELKE", "EMAS", "EVOL"], "Energy/mass output differs")
    contact_prints = by_name.get("CONTACT PRINT", [])
    require(len(contact_prints) == 2, "Two contact output cards required")
    for card in contact_prints:
        fields = [x.upper() for r in card["rows"] for x in r]
        require(card["opts"].get("FREQUENCY") == "1", "Contact output frequency differs")
        if fields == ["CELS"]:
            require(card["opts"].get("TOTALS") == "ONLY", "Contact energy totals missing")
        else:
            require(fields == ["CFN"] and card["opts"].get("SLAVE") == "SLAVE"
                    and card["opts"].get("MASTER") == "MASTER", "Pair force output differs")
    require({tuple(x.upper() for r in c["rows"] for x in r) for c in contact_prints} == {("CFN",), ("CELS",)}, "Contact fields missing")
    return {
        "schema": "parent_free_impact_input_audit/v1", "status": "PASS_PREPARED_INPUT_ALGEBRA_ONLY",
        "input_sha256": sha(path), "source_geometry_input_sha256": SOURCE_SHA,
        "physical_node_count": len(physical), "controller_node": 8001, "element_count": len(elements),
        "fixed_dof_count": len(fixed), "dependent_dof_count": len(dependent), "free_dofs": [[8001, 3]],
        "body_volumes_mm3_exact": {k: str(v) for k, v in volumes.items()},
        "body_masses_tonne_exact": {k: str(v / 8) for k, v in volumes.items()},
        "initial_moving_body_velocity_mm_s_exact": "-1/10", "initial_kinetic_energy_Nmm_exact": "1/200",
        "physical_geometry_equals_original_coupon": True, "all_midside_coordinates_are_exact_midpoints": True,
        "coincident_interface_area_mm2_exact": "4", "slave_outward_normal": [0, 0, -1], "master_outward_normal": [0, 0, 1],
        "uniform_mode_projected_mass_tonne": 1,
        "mass_basis": "Partition of unity on the twelve straight tetrahedra; four-point quadrature exactly integrates the constant uniform-translation integrand. Lower DOFs are fixed.",
        "native_execution": False, "joint_acceptance": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = audit()
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    target = HERE / "parent-input-audit.json"
    if args.write:
        with target.open("x") as stream:
            stream.write(rendered)
    else:
        require(target.read_text() == rendered, "Recorded input audit differs")
    print(json.dumps({"status": result["status"], "input_sha256": result["input_sha256"]}))
