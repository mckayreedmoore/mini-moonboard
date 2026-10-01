#!/usr/bin/env python3
"""Prepare a pinned two-pair, three-body C3D10 shared-edge coupon."""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = HERE.parent
SOURCE_INPUT = EVAL / "contact-mortar-c3d10-fullstep-attempt01/input/mortar_c3d10.inp"
SOURCE_EXPECTED = EVAL / "contact-mortar-c3d10-fullstep-attempt01/expected.json"
ORIGINAL_INPUT = EVAL / "contact-output-known-answer-attempt01/baseline/coupon.inp"
MORTAR_ATTEMPT = EVAL / "contact-mortar-shared-edge-known-answer-attempt02"
MORTAR_FREEZE = MORTAR_ATTEMPT / "input-freeze.json"
INHERITED_DECKS = {
    "shared_slave_penalty": MORTAR_ATTEMPT / "input/shared_slave_penalty.inp",
    "cross_role_penalty": MORTAR_ATTEMPT / "input/cross_role_penalty.inp",
}
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
SOURCE_INPUT_SHA256 = "b24c1f973e3ac9cf94e89c6951c350b9905f80b29220aa001f70c12f051291e4"
SOURCE_EXPECTED_SHA256 = "397e97710cb52d60edb263f36e1c848ee5d7ade02c9d597c636cf70407ba5dec"
ORIGINAL_INPUT_SHA256 = "059c07fb59b500e78578413d0d9538076cabacda7154b035baeee334fdc40404"
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MORTAR_FREEZE_SHA256 = "1a23e2fe3fb5152d12d54b49e3033f4edb0793d699263e17d0a0b7d3b6b0ad6c"
INHERITED_DECK_SHA256 = {
    "shared_slave_penalty": "d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7",
    "cross_role_penalty": "d3622fead559fff2844e1a95971253f64291c48f8285e5848b634448a8ac86ea",
}
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactpairs.f":
        "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488",
    "CalculiX/ccx_2.23/src/genfirstactif.f":
        "9a06ca822c8454bd24cfa9577ce1363559e9347df905e8d500ff4cc553f9fabd",
    "CalculiX/ccx_2.23/src/getnumberofnodes.f":
        "5cbb55e69e10e63e7cb2ecd9900c0a42f660f798b05fcb6e0415b134a7281723",
    "CalculiX/ccx_2.23/src/shape6tri.f":
        "64f4596c6dc6ee41baf4cc514947c41348a43c0c6fd40763af07802cad23c2cc",
    "CalculiX/ccx_2.23/src/stressmortar.c":
        "c62c65de7aba91260320a3c548ebc513a436e4243151ca0441dcc5d309dce621",
    "CalculiX/ccx_2.23/src/remlagrangemult.f":
        "85376768d34d9aa2a91c96554c7a39befe476e01ceac8709d49d3de8b92308c2",
}

MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
CASES = (
    "shared_slave_penalty",
    "cross_role_penalty",
)
E = 100000.0
NU = 0.0
K = 100000.0
PRESSURE = 1.0
LENGTH = 2.0
AREA = 4.0
EXPECTED_FORCE = PRESSURE * AREA
MOMENT_CLOSURE_REFERENCE_LENGTH_MM = 1.0
MOMENT_CLOSURE_ABSOLUTE_FLOOR_NMM = 0.001

# C3D10 connectivity is corners 1..4 then edge nodes (1-2, 2-3, 3-1,
# 1-4, 2-4, 3-4). CalculiX tetra face labels S1 and S3 use these nodes.
MIDPOINT_EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
FACE_LOCAL_NODES = {
    "S1": (0, 1, 2, 4, 5, 6),
    "S3": (1, 2, 3, 5, 9, 8),
}
FACE_LOCAL_CORNERS = {"S1": (0, 1, 2), "S3": (1, 2, 3)}
SURFACE_FACES = {
    "Z_CENTRAL": ((1, "S1"), (2, "S1")),
    "Z_LOWER": ((4, "S3"), (5, "S3")),
    "X_CENTRAL": ((3, "S1"), (4, "S1")),
    "X_LEFT": ((1, "S3"), (6, "S3")),
    "CENTRAL_TOP": ((4, "S3"), (5, "S3")),
    "CENTRAL_RIGHT": ((1, "S3"), (6, "S3")),
}
BODY_SPECS = {
    "CENTRAL": {"node_offset": 0, "element_offset": 0, "translation": (0, 0, 0)},
    "LOWER": {"node_offset": 1000, "element_offset": 100, "translation": (0, 0, -2)},
    "LEFT": {"node_offset": 2000, "element_offset": 200, "translation": (-2, 0, 0)},
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha(path.read_bytes())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def verify_source_pins() -> dict:
    require(sha_file(SOURCE_INPUT) == SOURCE_INPUT_SHA256,
            "pinned full-step source input hash mismatch")
    require(sha_file(SOURCE_EXPECTED) == SOURCE_EXPECTED_SHA256,
            "pinned full-step expected.json hash mismatch")
    require(sha_file(ORIGINAL_INPUT) == ORIGINAL_INPUT_SHA256,
            "pinned original C3D10 coupon hash mismatch")
    require(sha_file(SOURCE_ARCHIVE) == SOURCE_ARCHIVE_SHA256,
            "pinned CalculiX 2.23 source archive hash mismatch")
    require(sha_file(MORTAR_FREEZE) == MORTAR_FREEZE_SHA256,
            "attempt02 frozen input hash mismatch")
    frozen = json.loads(MORTAR_FREEZE.read_text())
    require(frozen["schema"] == "mortar_shared_edge_freeze/v1" and
            frozen["cases"] == ["shared_slave_mortar", "shared_slave_penalty",
                                "cross_role_mortar", "cross_role_penalty"],
            "attempt02 freeze is not the reviewed four-case source")
    for case, source_path in INHERITED_DECKS.items():
        expected_sha = INHERITED_DECK_SHA256[case]
        relative = f"input/{case}.inp"
        require(sha_file(source_path) == expected_sha and
                frozen["files_sha256"].get(relative) == expected_sha,
                f"attempt02 inherited deck is not frozen as expected: {case}")
    member_hashes = {}
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for relative, expected in SOURCE_MEMBERS.items():
            member = archive.getmember("./" + relative)
            extracted = archive.extractfile(member)
            require(extracted is not None, f"missing source member: {relative}")
            actual = sha(extracted.read())
            require(actual == expected, f"pinned source member hash mismatch: {relative}")
            member_hashes[relative] = actual
    return member_hashes


def parse_source_mesh(path: Path) -> tuple[dict[int, tuple[int, int, int]], dict[int, tuple[int, ...]]]:
    nodes: dict[int, tuple[int, int, int]] = {}
    upper_node_ids: set[int] = set()
    upper_elements: dict[int, tuple[int, ...]] = {}
    section = None
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upper_node_ids = upper_node_ids if line.upper() == "*NSET,NSET=N_UPPER" else upper_node_ids
            section = None
            header = line.upper().replace(" ", "")
            if header == "*NODE":
                section = "NODE"
            elif header == "*ELEMENT,TYPE=C3D10,ELSET=UPPER":
                section = "UPPER_ELEMENT"
            elif header == "*NSET,NSET=N_UPPER":
                section = "UPPER_NSET"
            continue
        fields = [field.strip() for field in line.split(",")]
        if section == "NODE":
            require(len(fields) == 4, f"malformed pinned source node: {line}")
            values = tuple(int(Decimal(item)) for item in fields[1:])
            require(all(Decimal(item) == int(Decimal(item)) for item in fields[1:]),
                    f"non-integral source coordinate: {line}")
            nodes[int(fields[0])] = values
        elif section == "UPPER_ELEMENT":
            require(len(fields) == 11, f"malformed pinned C3D10 element: {line}")
            upper_elements[int(fields[0])] = tuple(map(int, fields[1:]))
        elif section == "UPPER_NSET":
            upper_node_ids.update(map(int, fields))
    require(len(upper_node_ids) == 27, "pinned upper template is not 27 nodes")
    require(sorted(upper_elements) == [1, 2, 3, 4, 5, 6],
            "pinned upper template is not six C3D10 tetrahedra")
    referenced = {node for connectivity in upper_elements.values() for node in connectivity}
    require(referenced == upper_node_ids, "pinned upper node group differs from element connectivity")
    require(all(node in nodes for node in upper_node_ids), "pinned upper node coordinate missing")
    return {node: nodes[node] for node in sorted(upper_node_ids)}, upper_elements


def translated_mesh(
    base_nodes: dict[int, tuple[int, int, int]],
    base_elements: dict[int, tuple[int, ...]],
) -> tuple[dict[int, tuple[int, int, int]], dict[int, dict[int, tuple[int, ...]]]]:
    nodes: dict[int, tuple[int, int, int]] = {}
    elements: dict[int, dict[int, tuple[int, ...]]] = {}
    for body, spec in BODY_SPECS.items():
        node_offset = spec["node_offset"]
        element_offset = spec["element_offset"]
        tx, ty, tz = spec["translation"]
        body_nodes = {node + node_offset: (xyz[0] + tx, xyz[1] + ty, xyz[2] + tz)
                      for node, xyz in base_nodes.items()}
        body_elements = {
            element + element_offset: tuple(node + node_offset for node in connectivity)
            for element, connectivity in base_elements.items()
        }
        nodes.update(body_nodes)
        elements[body] = body_elements
    require(len(nodes) == 81 and len(set(nodes)) == 81, "three cube node labels are not disjoint")
    require(sum(map(len, elements.values())) == 18, "three cube element count differs")
    return nodes, elements


def vector_sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vector_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def vector_dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(vector):
    return math.sqrt(vector_dot(vector, vector))


def face_nodes(connectivity: tuple[int, ...], side: str) -> tuple[int, ...]:
    return tuple(connectivity[index] for index in FACE_LOCAL_NODES[side])


def face_corner_nodes(connectivity: tuple[int, ...], side: str) -> tuple[int, ...]:
    return tuple(connectivity[index] for index in FACE_LOCAL_CORNERS[side])


def triangle_area(points) -> float:
    return 0.5 * norm(vector_cross(vector_sub(points[1], points[0]),
                                  vector_sub(points[2], points[0])))


def mesh_checks(nodes, elements):
    signed_determinants = {}
    midpoint_errors = {}
    for body, body_elements in elements.items():
        body_nodes = {node for conn in body_elements.values() for node in conn}
        for element, connectivity in body_elements.items():
            corners = [nodes[node] for node in connectivity[:4]]
            u, v, w = (vector_sub(corners[index], corners[0]) for index in (1, 2, 3))
            determinant = vector_dot(u, vector_cross(v, w))
            signed_determinants[str(element)] = determinant
            require(determinant > 0, f"nonpositive corner Jacobian in element {element}")
            for mid_index, (left, right) in enumerate(MIDPOINT_EDGES, start=4):
                expected = tuple((corners[left][axis] + corners[right][axis]) / 2
                                 for axis in range(3))
                actual = nodes[connectivity[mid_index]]
                error = max(abs(actual[axis] - expected[axis]) for axis in range(3))
                midpoint_errors[f"{element}:{connectivity[mid_index]}"] = error
                require(error <= 1e-12, f"C3D10 midside node is not a straight midpoint: {element}")
        require(len(body_nodes) == 27, f"wrong node count in body {body}")

    exterior_face_counts = {}
    for body, body_elements in elements.items():
        face_owner = Counter()
        for connectivity in body_elements.values():
            for corners in ((0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3)):
                face_owner[tuple(sorted(connectivity[index] for index in corners))] += 1
        exterior_face_counts[body] = sum(count == 1 for count in face_owner.values())
        require(all(count in (1, 2) for count in face_owner.values()),
                f"nonmanifold tetra face ownership in {body}")

    surfaces = {}
    for surface, facets in SURFACE_FACES.items():
        body = "CENTRAL"
        if surface == "Z_LOWER":
            body = "LOWER"
        elif surface == "X_LEFT":
            body = "LEFT"
        facet_nodes = []
        face_triangles = []
        total_area = 0.0
        for local_element, side in facets:
            element = local_element + BODY_SPECS[body]["element_offset"]
            connectivity = elements[body][element]
            all_face_nodes = face_nodes(connectivity, side)
            corner_nodes = face_corner_nodes(connectivity, side)
            facet_nodes.extend(all_face_nodes)
            coords = [nodes[node] for node in corner_nodes]
            area = triangle_area(coords)
            total_area += area
            face_triangles.append({
                "element": element,
                "side": side,
                "corner_nodes": list(corner_nodes),
                "nodes": list(all_face_nodes),
                "area_mm2": area,
            })
            owners = Counter()
            for candidate in elements[body].values():
                for local_corners in ((0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 2, 3)):
                    key = tuple(sorted(candidate[index] for index in local_corners))
                    owners[key] += 1
            require(owners[tuple(sorted(corner_nodes))] == 1,
                    f"selected face is not exterior: {surface} element {element} {side}")
        unique_nodes = sorted(set(facet_nodes))
        require(len(unique_nodes) == 9, f"selected quadratic patch is not nine nodes: {surface}")
        require(abs(total_area - AREA) < 1e-12,
                f"selected patch area is not 4 mm2: {surface}={total_area}")
        surfaces[surface] = {
            "body": body,
            "facets": face_triangles,
            "nodes": unique_nodes,
            "area_mm2": total_area,
        }

    for surface_a, surface_b in (("Z_CENTRAL", "Z_LOWER"), ("X_CENTRAL", "X_LEFT")):
        a = sorted(nodes[node] for node in surfaces[surface_a]["nodes"])
        b = sorted(nodes[node] for node in surfaces[surface_b]["nodes"])
        require(a == b, f"contact surface coordinates do not conform: {surface_a}/{surface_b}")
        tri_a = sorted(tuple(sorted(nodes[node] for node in facet["corner_nodes"]))
                       for facet in surfaces[surface_a]["facets"])
        tri_b = sorted(tuple(sorted(nodes[node] for node in facet["corner_nodes"]))
                       for facet in surfaces[surface_b]["facets"])
        require(tri_a == tri_b, f"contact surface triangulations do not match: {surface_a}/{surface_b}")

    expected_normals = {
        "Z_CENTRAL": [0.0, 0.0, -1.0], "Z_LOWER": [0.0, 0.0, 1.0],
        "X_CENTRAL": [-1.0, 0.0, 0.0], "X_LEFT": [1.0, 0.0, 0.0],
        "CENTRAL_TOP": [0.0, 0.0, 1.0], "CENTRAL_RIGHT": [1.0, 0.0, 0.0],
    }
    for surface, normal_vector in expected_normals.items():
        surfaces[surface]["expected_outward_normal"] = normal_vector
    return surfaces, {
        "all_corner_jacobians_positive": True,
        "signed_corner_determinants_mm3": signed_determinants,
        "all_c3d10_midsides_are_straight_edge_midpoints": True,
        "maximum_midside_coordinate_error_mm": max(midpoint_errors.values()),
        "midside_checks": midpoint_errors,
        "tetra_mesh_exterior_face_count_by_body": exterior_face_counts,
        "selected_faces_are_exterior_and_six_node_quadratic_triangles": True,
        "each_contact_patch_area_mm2": AREA,
        "contact_patch_node_coordinates_match": True,
        "contact_patch_triangle_partitions_match": True,
    }


def create_loads(nodes, elements, surfaces):
    loads = defaultdict(float)
    facets_by_label = {}
    for surface, dof, sign in (("CENTRAL_TOP", 3, -1.0), ("CENTRAL_RIGHT", 1, -1.0)):
        for facet in surfaces[surface]["facets"]:
            node_ids = facet["nodes"]
            area = facet["area_mm2"]
            magnitude = sign * PRESSURE * area / 3.0
            for node in node_ids[3:]:
                loads[(node, dof)] += magnitude
                facets_by_label.setdefault((node, dof), []).append({
                    "surface": surface,
                    "facet_element": facet["element"],
                    "facet_side": facet["side"],
                    "consistent_nodal_force_N": magnitude,
                    "note": "quadratic triangle corner weights 0; each midside gets pressure*area/3",
                })
    entries = []
    for (node, dof), value in sorted(loads.items()):
        entries.append({
            "node": node,
            "dof": dof,
            "force_N": value,
            "coordinate_mm": list(nodes[node]),
            "contributions": facets_by_label[(node, dof)],
        })

    resultant = [0.0, 0.0, 0.0]
    moment = [0.0, 0.0, 0.0]
    by_face = {}
    for label, dof, direction in (("CENTRAL_TOP", 3, "z"), ("CENTRAL_RIGHT", 1, "x")):
        force = [0.0, 0.0, 0.0]
        face_moment = [0.0, 0.0, 0.0]
        for item in entries:
            if item["dof"] != dof or not any(c["surface"] == label for c in item["contributions"]):
                continue
            # A node shared by the loaded top and right patches has separate DOFs;
            # this filter keeps each component on its originating face.
            component_force = sum(c["consistent_nodal_force_N"] for c in item["contributions"]
                                  if c["surface"] == label)
            xyz = item["coordinate_mm"]
            vector = [0.0, 0.0, 0.0]
            vector[dof - 1] = component_force
            cross = [xyz[1] * vector[2] - xyz[2] * vector[1],
                     xyz[2] * vector[0] - xyz[0] * vector[2],
                     xyz[0] * vector[1] - xyz[1] * vector[0]]
            force = [force[i] + vector[i] for i in range(3)]
            face_moment = [face_moment[i] + cross[i] for i in range(3)]
        by_face[label] = {"resultant_N": force, "first_moment_about_global_origin_Nmm": face_moment}
        resultant = [resultant[i] + force[i] for i in range(3)]
        moment = [moment[i] + face_moment[i] for i in range(3)]
    require(all(abs(resultant[i] - target) < 1e-9
                for i, target in enumerate((-EXPECTED_FORCE, 0.0, -EXPECTED_FORCE))),
            f"consistent nodal loads do not sum to expected resultant: {resultant}")
    require(all(abs(moment[i] - target) < 1e-9
                for i, target in enumerate((-EXPECTED_FORCE, 0.0, EXPECTED_FORCE))),
            f"consistent nodal loads do not sum to expected moment: {moment}")
    return entries, {
        "pressure_N_per_mm2": PRESSURE,
        "face_area_mm2_each": AREA,
        "force_magnitude_N_each": EXPECTED_FORCE,
        "consistent_nodal_force_rule": "Quadratic triangle: corner-node integrals are zero; each midside node receives pressure*triangle_area/3 along inward normal.",
        "by_face": by_face,
        "total_resultant_N": resultant,
        "total_first_moment_about_global_origin_Nmm": moment,
        "moment_units": "N mm",
    }


def get_body_nodes(elements):
    return {body: sorted({node for connectivity in body_elements.values() for node in connectivity})
            for body, body_elements in elements.items()}


def nset_card(name: str, node_ids) -> str:
    ordered = sorted(node_ids)
    lines = [f"*NSET,NSET={name}"]
    for start in range(0, len(ordered), 12):
        lines.append(",".join(map(str, ordered[start:start + 12])))
    return "\n".join(lines)


def element_card(body: str, element_rows) -> str:
    lines = [f"*ELEMENT,TYPE=C3D10,ELSET={body}"]
    for label, connectivity in sorted(element_rows.items()):
        lines.append(",".join(map(str, (label, *connectivity))))
    return "\n".join(lines)


def build_deck(case, nodes, elements, surfaces, loads, body_node_groups, spc_groups):
    mortar = case.endswith("_mortar")
    contact_type = "MORTAR" if mortar else "SURFACE TO SURFACE"
    roles = ({
        "PAIR_Z": {"slave": "Z_CENTRAL", "master": "Z_LOWER"},
        "PAIR_X": {"slave": "X_CENTRAL", "master": "X_LEFT"},
    } if case.startswith("shared_slave") else {
        "PAIR_Z": {"slave": "Z_CENTRAL", "master": "Z_LOWER"},
        "PAIR_X": {"slave": "X_LEFT", "master": "X_CENTRAL"},
    })
    lines = [
        "*HEADING",
        "Three-cube orthogonal shared-contact-edge known-answer coupon; not a joint model",
        "** Units: mm, N, MPa (N/mm2); C3D10, E=100000, nu=0; frictionless normal contact",
        "*NODE",
    ]
    for node, xyz in sorted(nodes.items()):
        lines.append(f"{node},{xyz[0]},{xyz[1]},{xyz[2]}")
    for body in ("CENTRAL", "LOWER", "LEFT"):
        lines.extend(["", element_card(body, elements[body])])

    nsets = {
        "CENTRAL_NODES": body_node_groups["CENTRAL"],
        "LOWER_NODES": body_node_groups["LOWER"],
        "LEFT_NODES": body_node_groups["LEFT"],
        "ALLNODES": sorted(nodes),
        **{f"FACE_{name}": data["nodes"] for name, data in surfaces.items()},
    }
    for name, ids in spc_groups.items():
        nsets[name] = ids["nodes"]
    for name, ids in nsets.items():
        lines.extend(["", nset_card(name, ids)])

    lines.extend([
        "",
        "*MATERIAL,NAME=ELASTIC",
        "*ELASTIC",
        f"{E:.1f},{NU:.1f}",
        "*SOLID SECTION,ELSET=CENTRAL,MATERIAL=ELASTIC",
        "*SOLID SECTION,ELSET=LOWER,MATERIAL=ELASTIC",
        "*SOLID SECTION,ELSET=LEFT,MATERIAL=ELASTIC",
        "",
    ])
    for name in ("Z_CENTRAL", "Z_LOWER", "X_CENTRAL", "X_LEFT"):
        body = surfaces[name]["body"]
        element_offset = BODY_SPECS[body]["element_offset"]
        lines.append(f"*SURFACE,NAME={name},TYPE=ELEMENT")
        for local_element, side in SURFACE_FACES[name]:
            lines.append(f"{local_element + element_offset},{side}")
    lines.extend([
        "*SURFACE INTERACTION,NAME=NORMAL_LAW",
        "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
        f"{K:.1f}",
        "** No *FRICTION card; default tangential response is frictionless.",
    ])
    for pair in ("PAIR_Z", "PAIR_X"):
        lines.extend([
            f"*CONTACT PAIR,INTERACTION=NORMAL_LAW,TYPE={contact_type}",
            f"{roles[pair]['slave']},{roles[pair]['master']}",
        ])

    lines.extend(["*BOUNDARY"])
    for group, details in spc_groups.items():
        for dof_start, dof_end, value in details["constraints"]:
            for node in details["nodes"]:
                lines.append(f"{node},{dof_start},{dof_end},{value:.1f}")
    lines.extend([
        "*STEP,NLGEOM,INC=100",
        "*STATIC,DIRECT",
        "1,1",
        "*CLOAD",
    ])
    for item in loads:
        lines.append(f"{item['node']},{item['dof']},{item['force_N']:.12f}")
    lines.extend([
        "*NODE PRINT,NSET=ALLNODES,FREQUENCY=1",
        "U,RF",
        "*NODE FILE,NSET=ALLNODES,FREQUENCY=1",
        "U,RF",
        "*CONTACT FILE,FREQUENCY=1",
        "CDIS,CSTR",
        "*END STEP",
        "",
    ])
    return "\n".join(lines).encode(), roles


def main() -> None:
    for protected in (HERE / "input-freeze.json", HERE / "execution.json", HERE / "output"):
        require(not protected.exists(), f"refusing to regenerate a frozen/executed packet: {protected}")
    pinned_members = verify_source_pins()
    base_nodes, base_elements = parse_source_mesh(SOURCE_INPUT)
    nodes, elements = translated_mesh(base_nodes, base_elements)
    surfaces, geometry_checks = mesh_checks(nodes, elements)
    loads, load_resultants = create_loads(nodes, elements, surfaces)
    body_node_groups = get_body_nodes(elements)

    central_bottom = set(surfaces["Z_CENTRAL"]["nodes"])
    central_left = set(surfaces["X_CENTRAL"]["nodes"])
    shared_nodes = sorted(central_bottom & central_left)
    require(shared_nodes == [1, 4, 24], f"shared central edge differs: {shared_nodes}")
    shared_vertices = [node for node in shared_nodes if node in {1, 4}]
    shared_midsides = [node for node in shared_nodes if node == 24]

    left_offset = BODY_SPECS["LEFT"]["node_offset"]
    lower_offset = BODY_SPECS["LOWER"]["node_offset"]
    base = {node: xyz for node, xyz in base_nodes.items()}
    lower_remote_uz = sorted(node + lower_offset for node, xyz in base.items() if xyz[2] == 0)
    left_remote_ux = sorted(node + left_offset for node, xyz in base.items() if xyz[0] == 0)
    spc_groups = {
        "LOWER_REMOTE_UZ": {
            "nodes": lower_remote_uz,
            "constraints": [(3, 3, 0.0)],
            "meaning": "lower remote z=-2 face normal support",
        },
        "LOWER_REMOTE_XY_ANCHOR_A": {
            "nodes": [1001],
            "constraints": [(1, 1, 0.0), (2, 2, 0.0)],
            "meaning": "lower remote bottom corner removes free tangential translations",
        },
        "LOWER_REMOTE_Y_ANCHOR_B": {
            "nodes": [1002],
            "constraints": [(2, 2, 0.0)],
            "meaning": "second lower remote bottom corner removes rotation about z",
        },
        "LEFT_REMOTE_UX": {
            "nodes": left_remote_ux,
            "constraints": [(1, 1, 0.0)],
            "meaning": "left remote x=-2 face normal support",
        },
        "LEFT_REMOTE_YZ_ANCHOR_A": {
            "nodes": [2001],
            "constraints": [(2, 2, 0.0), (3, 3, 0.0)],
            "meaning": "left remote x=-2 corner removes free tangential translations",
        },
        "LEFT_REMOTE_Z_ANCHOR_B": {
            "nodes": [2004],
            "constraints": [(3, 3, 0.0)],
            "meaning": "second left remote-face corner removes rotation about x",
        },
        "CENTRAL_NODE6_UY": {
            "nodes": [6],
            "constraints": [(2, 2, 0.0)],
            "meaning": "central noncontact node 6=(2,0,2) y gauge anchor",
        },
    }
    all_spc_nodes = {node for group in spc_groups.values() for node in group["nodes"]}
    boundary_constraints = [
        {"group": group, "node": node, "dof_start": dof_start,
         "dof_end": dof_end, "value": value}
        for group, details in spc_groups.items()
        for dof_start, dof_end, value in details["constraints"]
        for node in details["nodes"]
    ]
    all_slave_nodes = {
        case: (set(surfaces["Z_CENTRAL"]["nodes"])
               | set(surfaces["X_CENTRAL"]["nodes"]))
        if case == "shared_slave_penalty"
        else (set(surfaces["Z_CENTRAL"]["nodes"])
              | set(surfaces["X_LEFT"]["nodes"]))
        for case in CASES
    }
    slave_spc_overlap = {case: sorted(ids & all_spc_nodes) for case, ids in all_slave_nodes.items()}
    require(all(not overlap for overlap in slave_spc_overlap.values()),
            f"SPC/slave contact node overlap: {slave_spc_overlap}")

    input_dir = HERE / "input"
    input_dir.mkdir(exist_ok=True)
    inputs = {}
    case_roles = {}
    for case in CASES:
        deck, roles = build_deck(case, nodes, elements, surfaces, loads,
                                 body_node_groups, spc_groups)
        require(sha(deck) == INHERITED_DECK_SHA256[case] and
                sha_file(INHERITED_DECKS[case]) == INHERITED_DECK_SHA256[case],
                f"inherited attempt02 penalty deck changed: {case}")
        target = input_dir / f"{case}.inp"
        target.write_bytes(deck)
        inputs[case] = {"path": f"input/{case}.inp", "sha256": sha(deck)}
        case_roles[case] = roles

    contact_role_checks = {}
    for case, roles in case_roles.items():
        slave_z = set(surfaces[roles["PAIR_Z"]["slave"]]["nodes"])
        master_z = set(surfaces[roles["PAIR_Z"]["master"]]["nodes"])
        slave_x = set(surfaces[roles["PAIR_X"]["slave"]]["nodes"])
        master_x = set(surfaces[roles["PAIR_X"]["master"]]["nodes"])
        contact_role_checks[case] = {
            "pair_count": 2,
            "all_four_surface_names_unique": True,
            "Z_slave_master_node_label_intersection": sorted(slave_z & master_z),
            "X_slave_master_node_label_intersection": sorted(slave_x & master_x),
            "slave_slave_shared_node_labels": sorted(slave_z & slave_x),
            "cross_pair_slave_master_shared_node_labels": sorted((slave_z & master_x) | (slave_x & master_z)),
            "slave_spc_node_label_intersection": slave_spc_overlap[case],
        }

    force_compliance = LENGTH / E + LENGTH / E + 1.0 / K
    single_body = LENGTH / E
    tangent_start = -PRESSURE * (LENGTH / E + 1.0 / K)
    tangent_end = LENGTH - PRESSURE * (2.0 * LENGTH / E + 1.0 / K)
    projected_overlap_width = max(0.0, min(LENGTH, tangent_end) - max(0.0, tangent_start))
    projected_overlap_area = LENGTH * projected_overlap_width
    projected_overlap_loss = 1.0 - projected_overlap_area / AREA
    compression_profiles = {
        "pressure_N_per_mm2": PRESSURE,
        "contact_force_magnitude_N_per_axis": EXPECTED_FORCE,
        "formula": "C_axis = 2 mm/E + 1/K + 2 mm/E; use reference coordinates for this linear endpoint estimate.",
        "axis_compliance_mm3_per_N": force_compliance,
        "interface_contact_law_overclosure_mm": PRESSURE / K,
        "interface_central_minus_outer_signed_gap_mm": -PRESSURE / K,
        "outer_remote_to_central_face_approach_mm": PRESSURE * force_compliance,
        "outer_remote_to_central_face_signed_displacement_mm": -PRESSURE * force_compliance,
        "profiles": {
            "CENTRAL_UX": "-p*((x+2)/E + 1/K), for x in [0,2]; UY and UZ are diagnostic expected zero except numerical residuals.",
            "CENTRAL_UZ": "-p*((z+2)/E + 1/K), for z in [0,2]; UX and UY are diagnostic expected zero except numerical residuals.",
            "LEFT_UX": "-p*(x+2)/E, for x in [-2,0]; UY and UZ are diagnostic expected zero except numerical residuals.",
            "LOWER_UZ": "-p*(z+2)/E, for z in [-2,0]; UX and UY are diagnostic expected zero except numerical residuals.",
            "other_displacement_components": "diagnostic direction checks; not hard displacement-profile gates",
        },
        "expected_node_displacements_mm": {},
        "profile_gate": {
            "normal_profile_max_abs_error_mm": 1e-7,
            "contact_interface_gap_and_face_warp_max_abs_error_mm": 1e-7,
            "relative_to_outer_approach": 0.002,
            "scope": "linear reference-coordinate oracle under NLGEOM; parent review required before freeze",
        },
    }
    for body, node_ids in body_node_groups.items():
        for node in node_ids:
            x, y, z = nodes[node]
            if body == "CENTRAL":
                ux = -PRESSURE * ((x + LENGTH) / E + 1.0 / K)
                uz = -PRESSURE * ((z + LENGTH) / E + 1.0 / K)
            elif body == "LEFT":
                ux = -PRESSURE * (x + LENGTH) / E
                uz = 0.0
            else:
                ux = 0.0
                uz = -PRESSURE * (z + LENGTH) / E
            compression_profiles["expected_node_displacements_mm"][str(node)] = [ux, 0.0, uz]

    applied_and_support = {
        "applied_loads": load_resultants,
        "remote_support_resultants_N": {
            "LEFT_REMOTE_UX": [EXPECTED_FORCE, 0.0, 0.0],
            "LOWER_REMOTE_UZ": [0.0, 0.0, EXPECTED_FORCE],
            "auxiliary_anchor_groups": [0.0, 0.0, 0.0],
            "CENTRAL_NODE6_UY": [0.0, 0.0, 0.0],
        },
        "remote_support_first_moments_about_global_origin_Nmm": {
            "LEFT_REMOTE_UX": [0.0, EXPECTED_FORCE, -EXPECTED_FORCE],
            "LOWER_REMOTE_UZ": [EXPECTED_FORCE, -EXPECTED_FORCE, 0.0],
            "combined": [EXPECTED_FORCE, 0.0, -EXPECTED_FORCE],
        },
        "applied_plus_support_expected_force_closure_N": [0.0, 0.0, 0.0],
        "applied_plus_support_expected_moment_closure_Nmm": [0.0, 0.0, 0.0],
        "normal_support_force_relative_tolerance": 0.01,
        "normal_support_force_absolute_tolerance_N": 0.001,
        "global_force_closure_norm_tolerance_N": 0.01 * EXPECTED_FORCE + 0.001,
        "global_moment_closure_relative_tolerance": 0.01,
        "global_moment_closure_reference_length_mm": MOMENT_CLOSURE_REFERENCE_LENGTH_MM,
        "global_moment_closure_absolute_floor_Nmm": MOMENT_CLOSURE_ABSOLUTE_FLOOR_NMM,
        "global_moment_closure_norm_tolerance_Nmm": (
            0.01 * EXPECTED_FORCE * MOMENT_CLOSURE_REFERENCE_LENGTH_MM
            + MOMENT_CLOSURE_ABSOLUTE_FLOOR_NMM
        ),
        "transverse_and_auxiliary_support_resultant_norm_tolerance_N": 0.01 * EXPECTED_FORCE + 0.001,
        "support_resultant_node_groups": {
            "LEFT_REMOTE_UX": left_remote_ux,
            "LOWER_REMOTE_UZ": lower_remote_uz,
            "auxiliary_anchor_nodes": sorted({
                *spc_groups["LOWER_REMOTE_XY_ANCHOR_A"]["nodes"],
                *spc_groups["LOWER_REMOTE_Y_ANCHOR_B"]["nodes"],
                *spc_groups["LEFT_REMOTE_YZ_ANCHOR_A"]["nodes"],
                *spc_groups["LEFT_REMOTE_Z_ANCHOR_B"]["nodes"],
            }),
            "CENTRAL_NODE6_UY": [6],
        },
        "support_reaction_dof_groups": {
            "LEFT_REMOTE_NORMAL": {"nodes": left_remote_ux, "dof": 1, "expected_sum_N": EXPECTED_FORCE},
            "LOWER_REMOTE_NORMAL": {"nodes": lower_remote_uz, "dof": 3, "expected_sum_N": EXPECTED_FORCE},
            "LOWER_ANCHOR_TANGENTIAL_X": {"nodes": [1001], "dof": 1, "expected_sum_N": 0.0},
            "LOWER_ANCHOR_TANGENTIAL_Y": {"nodes": [1001, 1002], "dof": 2, "expected_sum_N": 0.0},
            "LEFT_ANCHOR_TANGENTIAL_Y": {"nodes": [2001], "dof": 2, "expected_sum_N": 0.0},
            "LEFT_ANCHOR_TANGENTIAL_Z": {"nodes": [2001, 2004], "dof": 3, "expected_sum_N": 0.0},
            "CENTRAL_NODE6_GAUGE_Y": {"nodes": [6], "dof": 2, "expected_sum_N": 0.0},
        },
        "support_node_union_for_global_force_and_moment_closure": sorted(all_spc_nodes),
    }

    expected = {
        "schema": "calculix_penalty_shared_edge_known_answer/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_NO_NATIVE_EXECUTION",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "mechanical_or_joint_acceptance": False,
        "release": False,
        "case_order": list(CASES),
        "cases": {
            case: {
                **inputs[case],
                "contact_type": "MORTAR" if case.endswith("_mortar") else "SURFACE TO SURFACE",
                "pairs": case_roles[case],
                "contact_role_checks": contact_role_checks[case],
                "output_layout": (
                    f"output/{case}/coupon.{{inp,dat,cvg,sta,frd,log}}; "
                    f"output/{case}/coupon.{{stdout,stderr}}; output/{case}/execution.json"
                ),
            }
            for case in CASES
        },
        "solver": {
            "version": "2.23",
            "binary_path": "/usr/local/bin/ccx-upstream-2.23",
            "base_image_id": "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38",
            "binary_sha256": "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "patched_or_instrumented_binary": False,
            "manual_sha256": MANUAL_SHA256,
            "manual_url": "https://www.dhondt.de/ccx_2.23.pdf",
        },
        "source": {
            "prior_input_path": str(SOURCE_INPUT.relative_to(REPO)),
            "prior_input_sha256": SOURCE_INPUT_SHA256,
            "prior_expected_path": str(SOURCE_EXPECTED.relative_to(REPO)),
            "prior_expected_sha256": SOURCE_EXPECTED_SHA256,
            "original_coupon_path": str(ORIGINAL_INPUT.relative_to(REPO)),
            "original_coupon_sha256": ORIGINAL_INPUT_SHA256,
            "source_archive_path": str(SOURCE_ARCHIVE.relative_to(REPO)),
            "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "source_members_sha256": pinned_members,
            "source_snapshot_path": "source-snapshot.json",
            "inherited_penalty_decks": INHERITED_DECK_SHA256,
            "prior_failed_mortar_attempt": {
                "packet": str(MORTAR_ATTEMPT.relative_to(REPO)),
                "input_freeze_sha256": MORTAR_FREEZE_SHA256,
                "execution_sha256": "188e1097ac1f68aa21a025fd9bd0a96c6f7e3c68a5873e986dc853588af0023c",
                "failure_diagnostic_sha256": "40159d1d37047be8070a96553ae706a2192afd8a4a77e5d85db448cc250a67ff",
                "case": "shared_slave_mortar",
                "classification": "FAILED_METHOD_FIXTURE_NO_ACCEPTED_STATE",
                "native_exit_code": 201,
                "accepted_states": 0,
                "unexecuted_cases": ["shared_slave_penalty", "cross_role_mortar",
                                     "cross_role_penalty"],
            },
            "manual": {
                "version": "2.23",
                "section": "*CONTACT PAIR (TYPE=SURFACE TO SURFACE); *SURFACE BEHAVIOR; *STATIC",
                "path": "fea/generated/ccx_2.23.pdf",
                "sha256": MANUAL_SHA256,
            },
            "notes": [
                "The 27-node, six-C3D10 upper cube is parsed from the pinned prior 2 mm coupon; lower and left copies only translate its reference coordinates and node/element labels.",
                "Pinned genfirstactif.f:212-229 uses c0=1e-10 for the initial touch check and marks touching nodes active.",
                "Pinned remlagrangemult.f sets shared-node multiplier activity to -2 for overlapping slave pairs and slave/master cross-role pairs; attempt02 directly observed the warning only in its failed shared-slave MORTAR run.",
                "Each deck has four distinct surface definitions for two pairs and uses one contact type consistently for both pairs.",
                "This packet contains only the two unchanged surface-to-surface penalty decks inherited from the frozen attempt02 inputs; it does not repeat or resolve the MORTAR result.",
            ],
        },
        "fixture": {
            "units": {"length": "mm", "force": "N", "stress": "N/mm2", "moment": "N mm"},
            "geometry": "Three 2x2x2 mm cubes: CENTRAL=[0,2]x[0,2]x[0,2], LOWER=[0,2]x[0,2]x[-2,0], LEFT=[-2,0]x[0,2]x[0,2].",
            "node_coordinates_mm": {str(node): list(xyz) for node, xyz in sorted(nodes.items())},
            "elements": {
                body: {str(label): list(connectivity) for label, connectivity in sorted(rows.items())}
                for body, rows in elements.items()
            },
            "body_node_groups": body_node_groups,
            "contact_face_node_groups": {
                name: surfaces[name]["nodes"]
                for name in ("Z_CENTRAL", "Z_LOWER", "X_CENTRAL", "X_LEFT")
            },
            "contact_faces": surfaces,
            "contact_edge_shared_node_labels": shared_nodes,
            "contact_edge_shared_nodes_by_topology": {
                "vertex_nodes": shared_vertices,
                "midside_nodes": shared_midsides,
            },
            "spc_groups": spc_groups,
            "boundary_constraints": boundary_constraints,
            "slave_spc_overlap_node_labels_by_case": slave_spc_overlap,
            "mesh_checks": geometry_checks,
            "material_and_contact": {
                "youngs_modulus_N_per_mm2": E,
                "poisson_ratio": NU,
                "linear_pressure_overclosure_slope_K_N_per_mm3": K,
                "friction": "none",
                "contact_area_mm2_each_patch": AREA,
                "initial_touch_gap_mm": 0.0,
                "source_initial_touch_threshold_mm": 1e-10,
            },
            "load_entries": loads,
        },
        "load_and_reaction_oracle": applied_and_support,
        "analytical_known_answer": {
            "compression_endpoint": compression_profiles,
            "force_acceptance_inequality": f"abs(F_measured-{EXPECTED_FORCE:g} N) <= 0.01*{EXPECTED_FORCE:g} N + 0.001 N for each remote normal support resultant",
            "normal_compliance_mm3_per_N": force_compliance,
            "normal_compliance_relative_tolerance": 0.01,
            "normal_compliance_absolute_tolerance_mm3_per_N": 1e-10,
            "normal_compliance_acceptance_inequality": "abs(C_measured-C_analytic) <= 0.01*C_analytic + 1e-10 mm3/N",
            "profile_acceptance": "Normal displacement profiles, role-independent interface gap, and face warp each within 1e-7 mm of the frozen linear reference-coordinate estimate.",
            "tangential_support_acceptance": "Each non-axial/auxiliary support resultant <= 0.041 N; global force closure <= 0.041 N; global first-moment closure <= 0.01*4 N*1 mm + 0.001 N mm = 0.041 N mm.",
            "contact_field_acceptance": "CDIS and CSTR are requested. FRD must include one finite CONTACT block with the six expected components and at least one node; additional contact-node coverage is reported diagnostically, without a pointwise pressure gate.",
            "finite_geometry_limit": "At p=1 N/mm2, the small-strain profile estimates move a central contact-face tangential interval to about [-0.00003,1.99995] mm against an adjacent [0,2] mm face, giving a projected overlap area about 3.9999 mm2 (0.0025% below 4 mm2). This is an applicability estimate, not a rigorous worst-case local-error bound or exact pointwise pressure prediction; the 1e-7 mm profile/gap gates require parent review before freeze.",
            "patch_edge_loading_limit": "Consistent quadratic-triangle traction gives zero corner weights and pressure*area/3 at midsides. Some loaded central-face edge nodes also belong to a contact patch; this remains a static review item before freeze.",
            "contact_gap_sign": f"central-interface displacement minus outer-block displacement along global +x or +z; negative means overlap, expected {-PRESSURE / K:.8g} mm.",
            "outer_approach_sign": f"central loaded outer-face mean minus remote-support-face mean along global x or z; expected {-PRESSURE * force_compliance:.8g} mm (approach magnitude {PRESSURE * force_compliance:.8g} mm).",
            "not_qualified": "This two-case surface-to-surface penalty subset only tests shared-slave and cross-role shared-boundary behavior. It does not qualify MORTAR, the complete joint patch, or alter the model.",
        },
        "acceptance": {
            "require_two_pairs_per_deck": True,
            "require_same_contact_type_for_both_pairs_in_each_deck": True,
            "require_zero_explicit_SPC_overlap_with_any_slave_contact_node": True,
            "require_all_81_nodes_U_and_RF_in_DAT_and_FRD": True,
            "require_contact_CDIS_and_CSTR_finite": True,
            "minimum_FRD_contact_blocks_per_case": 1,
            "minimum_finite_FRD_contact_nodes_per_block": 1,
            "FRD_contact_coverage_beyond_minimum_is_diagnostic": True,
            "require_contact_field_sign_or_pointwise_law": False,
            "require_normal_support_force_each_axis": True,
            "require_force_and_moment_resultant_closure": True,
            "require_normal_profiles_interface_gap_and_face_warp": True,
            "require_exactly_one_accepted_increment": True,
            "require_accepted_relative_step_time": 1.0,
            "require_no_rejected_attempt_or_cutback": True,
            "mechanical_or_joint_acceptance": False,
            "native_execution_authorized": False,
        },
        "requested_outputs": {
            "all_nodes": 81,
            "DAT": ["U", "RF", "ALLNODES"],
            "FRD": ["U", "RF", "ALLNODES"],
            "CONTACT_FILE": ["CDIS", "CSTR"],
            "FRD_CONTACT": {
                "field_kind": "CONTACT",
                "component_labels": ["COPEN", "CSLIP1", "CSLIP2", "CPRESS", "CSHEAR1", "CSHEAR2"],
                "minimum_contact_blocks": 1,
                "minimum_finite_nodes_per_block": 1,
                "expected_unique_slave_node_coverage_reference": {
                    "shared_slave_penalty": 15,
                    "cross_role_penalty": 18,
                },
                "coverage_beyond_minimum_is_diagnostic": True,
            },
            "trace_contract": {
                "steps": 1,
                "accepted_increments": {"1": 1},
                "accepted_relative_time": 1.0,
                "accepted_total_time": 1.0,
                "no_rejected_attempts_or_cutbacks": True,
                "cvg_iteration_columns": ["STEP", "INC", "ATT", "ITER"],
                "sta_accepted_columns": ["STEP", "INC", "ATT", "ITRS", "TOTAL_TIME", "STEP_TIME", "INCREMENT_SIZE"],
            },
        },
        "step": {
            "number": 1,
            "procedure": "*STATIC,DIRECT",
            "nlgeom": True,
            "static_data_line": "1,1",
            "meaning": "fixed full-step increment, not alternate matrix solver or dynamic procedure",
            "target": "simultaneous force-controlled compression on CENTRAL_TOP and CENTRAL_RIGHT",
            "cutback_is_acceptance": False,
        },
    }
    expected_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    (HERE / "expected.json").write_bytes(expected_bytes)

    readiness = {
        "schema": "calculix_penalty_shared_edge_readiness/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "native_solver_launched": False,
        "input_freeze_created": False,
        "review_required_before_input_freeze": True,
        "parent_owns": ["static review", "input freeze", "bounded serial execution", "result audit"],
        "source_input_sha256": SOURCE_INPUT_SHA256,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "manual_sha256": MANUAL_SHA256,
        "generated_file_sha256": {
            **{inputs[case]["path"]: inputs[case]["sha256"] for case in CASES},
            "expected.json": sha(expected_bytes),
        },
        "linear_small_strain_applicability_estimate": {
            "pressure_N_per_mm2": PRESSURE,
            "force_N_per_axis": EXPECTED_FORCE,
            "elastic_shortening_mm_per_cube": PRESSURE * single_body,
            "contact_overlap_mm": PRESSURE / K,
            "outer_approach_mm_per_axis": PRESSURE * force_compliance,
            "central_contact_face_tangential_interval_mm": [tangent_start, tangent_end],
            "projected_contact_overlap_area_mm2": projected_overlap_area,
            "projected_area_reduction_fraction": projected_overlap_loss,
            "is_rigorous_worst_case_local_error_bound": False,
            "normal_profile_gap_warp_abs_tolerance_mm": 1e-7,
        },
        "checks": {
            "prior_input_and_expected_hashes_verified": True,
            "original_coupon_hash_verified": True,
            "source_archive_and_member_hashes_verified": True,
            "three_exact_translated_27_node_six_tet_cubes": True,
            "all_positive_corner_jacobians": True,
            "all_quadratic_midsides_are_straight_edge_midpoints": True,
            "selected_faces_exterior_and_quadratic": True,
            "both_contact_face_pairs_match_by_nodes_and_triangles": True,
            "each_contact_patch_area_mm2": AREA,
            "all_four_surface_names_unique_in_each_deck": True,
            "two_pairs_same_contact_type_in_each_deck": True,
            "zero_SPC_overlap_with_any_slave_node_all_cases": True,
            "consistent_quadratic_triangle_CLOAD_resultants_and_moments_verified": True,
            "initial_touch_zero_gap_source_threshold_checked": True,
            "one_static_direct_full_step": True,
            "finite_geometry_and_patch_edge_oracle_caveat_flagged_for_parent_review": True,
        },
        "review_items": [
            "Review the linear small-strain applicability estimate for approximately 0.0025% projected-area overlap reduction under NLGEOM biaxial compression; it is not a rigorous worst-case error bound.",
            "Review the consistent pressure CLOAD contributions at central contact-patch boundary nodes before freeze.",
            "Confirm the 0.041 N force gates and 0.041 N mm moment gate (0.01*4 N*1 mm + 0.001 N mm) against the independent verifier before freeze.",
            "Confirm the two penalty inputs remain byte-identical to their frozen attempt02 decks; MORTAR is excluded after its failed attempt.",
        ],
    }
    (HERE / "readiness.json").write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "cases": {case: inputs[case]["sha256"] for case in CASES},
        "expected_sha256": sha(expected_bytes),
        "readiness": readiness["status"],
        "shared_contact_edge_nodes": shared_nodes,
        "slave_spc_overlap": slave_spc_overlap,
        "applied_resultant_N": load_resultants["total_resultant_N"],
        "applied_moment_Nmm": load_resultants["total_first_moment_about_global_origin_Nmm"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
