#!/usr/bin/env python3
"""Prepare a refined shared-edge penalty plus full-cap motion fixture.

This is a deterministic input/oracle preflight only. It does not freeze inputs
and never invokes CalculiX.
"""

from __future__ import annotations

from fractions import Fraction as F
from itertools import combinations, permutations
import argparse
import hashlib
import json
import math
from pathlib import Path
import tarfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
EVAL = HERE.parent
BASE = EVAL / "contact-penalty-shared-edge-known-answer-attempt01"
ENERGY = EVAL / "contact-energy-known-answer-attempt01"
SOURCE_ARCHIVE = (
    EVAL / "ordinary-external-force-transient-attempt04-diagnostic"
    / "build-attempt02/source.tar.bz2"
)
MANUAL = REPO / "fea/generated/ccx_2.23.pdf"

BASE_HASHES = {
    "input/shared_slave_penalty.inp": "d7e517bca0a63fc02bbb77bae8116bc2b014b3545a5c40566e64cdaac47668e7",
    "input/cross_role_penalty.inp": "d3622fead559fff2844e1a95971253f64291c48f8285e5848b634448a8ac86ea",
    "expected.json": "16c1df001392376d084d8c2d021ce8a884bfb96ea56bbdf528275b476f974c45",
    "input-freeze.json": "e622aae3283d2c0d7f940e9e706ecc15b616eaf19fe1593c2d038fa97da12c9c",
    "verifier.json": "013a0259dd9806bcddfcb3e204374b79df0f3d99486f4b8809d4e831656d871b",
    "verifier.py": "c541fa3180d5cdac1bb3c87defdaf73e160f320f3b27f098727d70633b44897f",
    "RESULTS.md": "5c71b63d47065cb6a61364fa62397f79892bc7004a3facbc92f135f27f019542",
    "parent-review.json": "41b14110bee8aca710982a90efc3ea8018fb8c8f777d65bb4f69a0206f3d0d33",
}
ENERGY_HASHES = {
    "expected.json": "c49f2bbc020e4db0e38e8fb5973b3f5fbe6af502597c010a886f9e94353b8142",
    "input-freeze.json": "7ca80c4cdfe92b1f8dfcb0d71c9a97884dd7b6bdabb540b50902cf21c16396a0",
    "verifier.json": "15ff0827a312df7b5c4e10860ed57f852532b1f5dc718da1a7ec94f260470951",
    "verifier.py": "a6b9eb0849db95e68ed1edcc7801078ef566dcf4f9e9e5bdc52b386d2adcc33a",
    "RESULTS.md": "20b1680f1599124b69e52d5a9e53d547c6f2ae9a0e5742b037a02cfc2a81cae3",
}
ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
BASE_FREEZE_SHA256 = "e622aae3283d2c0d7f940e9e706ecc15b616eaf19fe1593c2d038fa97da12c9c"

SOURCE_MEMBER_HASHES = {
    "CalculiX/ccx_2.23/src/contactpairs.f": "e2b7e8176adc70f02f5140308a0c6a591fc9f7f620026867708e6345a9d9c488",
    "CalculiX/ccx_2.23/src/genfirstactif.f": "9a06ca822c8454bd24cfa9577ce1363559e9347df905e8d500ff4cc553f9fabd",
    "CalculiX/ccx_2.23/src/shape6tri.f": "64f4596c6dc6ee41baf4cc514947c41348a43c0c6fd40763af07802cad23c2cc",
    "CalculiX/ccx_2.23/src/contactprints.f": "88a2fc1a15caa2ab9b28de6ff6c4566f34e7f24c9db5c2c3ee4ef333439c717d",
    "CalculiX/ccx_2.23/src/printoutcontact.f": "4e1f5452d5fd268d7e4f1ab702de4804bb8f34a429b5e2c14ff9af3df9a9a055",
    "CalculiX/ccx_2.23/src/elprints.f": "15d4ad6001e3ecb4eeaa05cba39333626b6c079cbe9d696879092dc2c73ff7b7",
    "CalculiX/ccx_2.23/src/printout.f": "ae2b60b4e086846e2833a1d723c37645c0ff6701d2e28dc7e3163d0a4d136f32",
    "CalculiX/ccx_2.23/src/printoutelem.f": "e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544",
    "CalculiX/ccx_2.23/src/statics.f": "d5add12845e7dc6e7a19043fa6114012b9f36ed0723590308d60f4b09eee4599",
    "CalculiX/ccx_2.23/src/surfacebehaviors.f": "f0088a364b9b069aa10be9c4b4f38d72df875295f339830d7e2df6762ad9e161",
    "CalculiX/ccx_2.23/src/getnumberofnodes.f": "5cbb55e69e10e63e7cb2ecd9900c0a42f660f798b05fcb6e0415b134a7281723",
    "CalculiX/ccx_2.23/src/remlagrangemult.f": "85376768d34d9aa2a91c96554c7a39befe476e01ceac8709d49d3de8b92308c2",
    "CalculiX/ccx_2.23/src/noelfiles.f": "ed85b45d6987882e484f11a0be3dc9c2d716afba07d59483d364e0709107a59f",
    "CalculiX/ccx_2.23/src/printoutface.f": "e39d508e431c5ad29556594f7bf82753a8729a836ecf67ebd24a872212f13cbc",
    "CalculiX/ccx_2.23/src/sectionprints.f": "deee2931a7165184fc4d482ddfd1ab405da9ef4dcb870625374babf3e27c5446",
}

E = F(100000)
NU = F(0)
K = F(100000)
PRESSURE = F(1)
AREA_EXPECTED = F(4)
LENGTH = F(2)
COMPONENT_NAMES = ("tx", "ty", "tz", "rx", "ry", "rz")
BODY_SPECS = {
    "CENTRAL": {"offset": 0, "element_offset": 0, "translation": (0, 0, 0)},
    "LOWER": {"offset": 10000, "element_offset": 1000, "translation": (0, 0, -2)},
    "LEFT": {"offset": 20000, "element_offset": 2000, "translation": (-2, 0, 0)},
}
PERMUTATIONS = tuple(permutations((0, 1, 2)))
TET_EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
FACE_LOCAL_NODES = {
    "S1": (0, 1, 2, 4, 5, 6),
    "S2": (0, 1, 3, 4, 8, 7),
    "S3": (1, 2, 3, 5, 9, 8),
    "S4": (0, 2, 3, 6, 9, 7),
}
FACE_LOCAL_CORNERS = {
    "S1": (0, 1, 2),
    "S2": (0, 1, 3),
    "S3": (1, 2, 3),
    "S4": (0, 2, 3),
}
FACE_ORDER = {"S1": 1, "S2": 2, "S3": 3, "S4": 4}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def jwrite(path: Path, obj: object) -> bytes:
    data = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def fstr(value: F) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def fjson(value: F) -> float | int:
    return int(value) if value.denominator == 1 else float(value)


def mat_inverse(matrix: list[list[F]]) -> list[list[F]] | None:
    n = len(matrix)
    work = [list(row) + [F(int(i == j)) for j in range(n)]
            for i, row in enumerate(matrix)]
    for column in range(n):
        pivot = next((row for row in range(column, n) if work[row][column]), None)
        if pivot is None:
            return None
        work[column], work[pivot] = work[pivot], work[column]
        scale = work[column][column]
        work[column] = [value / scale for value in work[column]]
        for row in range(n):
            if row == column or not work[row][column]:
                continue
            scale = work[row][column]
            work[row] = [a - scale * b for a, b in zip(work[row], work[column])]
    return [row[n:] for row in work]


def mat_mul(left: list[list[F]], right: list[list[F]]) -> list[list[F]]:
    return [[sum((left[i][k] * right[k][j] for k in range(len(right))), F(0))
             for j in range(len(right[0]))]
            for i in range(len(left))]


def mat_vec(matrix: list[list[F]], vector: list[F]) -> list[F]:
    return [sum((a * b for a, b in zip(row, vector)), F(0)) for row in matrix]


def matrix_rank(matrix: list[list[F]]) -> int:
    if not matrix:
        return 0
    work = [list(row) for row in matrix]
    rows, cols = len(work), len(work[0])
    rank = 0
    for column in range(cols):
        pivot = next((row for row in range(rank, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        value = work[rank][column]
        work[rank] = [x / value for x in work[rank]]
        for row in range(rows):
            if row != rank and work[row][column]:
                value = work[row][column]
                work[row] = [x - value * y for x, y in zip(work[row], work[rank])]
        rank += 1
        if rank == rows:
            break
    return rank


def norm_inf(matrix: list[list[F]]) -> float:
    return max(sum(abs(float(value)) for value in row) for row in matrix)


def vector_sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def vector_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def det3(a, b, c) -> F:
    return a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])


def global_point(local: tuple[int, int, int], translation) -> tuple[F, F, F]:
    return tuple(F(local[i] + translation[i]) for i in range(3))


def cell_tets(i: int, j: int, k: int):
    """Freudenthal six-tet split around the local 000--111 diagonal."""
    start = (i, j, k)
    for permutation in PERMUTATIONS:
        p1 = list(start)
        p1[permutation[0]] += 1
        p2 = list(p1)
        p2[permutation[1]] += 1
        p3 = (i + 1, j + 1, k + 1)
        points = [start, tuple(p1), tuple(p2), p3]
        a, b, c = (vector_sub(points[q], points[0]) for q in (1, 2, 3))
        if det3(a, b, c) < 0:
            points[1], points[2] = points[2], points[1]
        yield tuple(points)


def key_sort(key):
    return (0, key[1:]) if key[0] == "v" else (1, key[1])


def edge_key(a, b):
    return ("m", tuple(sorted((a, b))))


def build_mesh():
    nodes: dict[int, tuple[F, F, F]] = {}
    node_keys_by_body = {}
    body_node_ids = {}
    body_elements = {}
    element_connectivity = {}
    element_body = {}
    body_corner_lookup = {}
    for body_index, (body, spec) in enumerate(BODY_SPECS.items()):
        tets = []
        for i in range(2):
            for j in range(2):
                for k in range(2):
                    tets.extend(cell_tets(i, j, k))
        require(len(tets) == 48, f"{body}: expected 48 linear tetrahedra before C3D10 conversion")
        keys = {("v", point) for tet in tets for point in tet}
        keys.update(edge_key(tet[a], tet[b]) for tet in tets
                    for a, b in TET_EDGES)
        ordered_keys = sorted(keys, key=key_sort)
        node_offset = spec["offset"]
        local_ids = {key: node_offset + index + 1 for index, key in enumerate(ordered_keys)}
        node_keys_by_body[body] = ordered_keys
        body_node_ids[body] = sorted(local_ids.values())
        corner_lookup = {key[1]: local_ids[key] for key in ordered_keys if key[0] == "v"}
        body_corner_lookup[body] = corner_lookup
        for key, node in local_ids.items():
            if key[0] == "v":
                local = key[1]
            else:
                left, right = key[1]
                local = tuple(F(left[d] + right[d], 2) for d in range(3))
            nodes[node] = global_point(local, spec["translation"])
        body_eids = []
        for local_index, tet in enumerate(tets, start=1):
            eid = spec["element_offset"] + local_index
            mids = [local_ids[edge_key(tet[a], tet[b])] for a, b in TET_EDGES]
            conn = tuple(local_ids[("v", point)] for point in tet) + tuple(mids)
            corners = [nodes[node] for node in conn[:4]]
            volume6 = det3(vector_sub(corners[1], corners[0]),
                           vector_sub(corners[2], corners[0]),
                           vector_sub(corners[3], corners[0]))
            require(volume6 > 0, f"{body} element {eid} has nonpositive determinant")
            for mid_index, (left, right) in enumerate(TET_EDGES, start=4):
                midpoint = tuple((corners[left][axis] + corners[right][axis]) / 2
                                 for axis in range(3))
                require(nodes[conn[mid_index]] == midpoint,
                        f"{body} element {eid} has a nonstraight midside node")
            element_connectivity[eid] = conn
            element_body[eid] = body
            body_eids.append(eid)
        body_elements[body] = body_eids
    require(len(nodes) == len(set(nodes)), "refined node labels collide")
    return {
        "nodes": nodes,
        "node_keys_by_body": node_keys_by_body,
        "body_node_ids": body_node_ids,
        "body_elements": body_elements,
        "elements": element_connectivity,
        "element_body": element_body,
        "body_corner_lookup": body_corner_lookup,
    }


def face_surfaces(mesh):
    surfaces = {}
    surface_specs = {
        "Z_CENTRAL": ("CENTRAL", 2, F(0)),
        "Z_LOWER": ("LOWER", 2, F(0)),
        "X_CENTRAL": ("CENTRAL", 0, F(0)),
        "X_LEFT": ("LEFT", 0, F(0)),
        "PORT_TOP": ("CENTRAL", 2, F(2)),
        "PORT_RIGHT": ("CENTRAL", 0, F(2)),
        "LOWER_REMOTE_UZ": ("LOWER", 2, F(-2)),
        "LEFT_REMOTE_UX": ("LEFT", 0, F(-2)),
    }
    face_records = []
    for eid, conn in mesh["elements"].items():
        body = mesh["element_body"][eid]
        for side, corner_indices in FACE_LOCAL_CORNERS.items():
            corner_nodes = tuple(conn[index] for index in corner_indices)
            face_records.append((eid, side, body, corner_nodes,
                                 tuple(conn[index] for index in FACE_LOCAL_NODES[side])))
    for name, (body, axis, value) in surface_specs.items():
        hits = []
        for eid, side, owner, corner_nodes, face_nodes in face_records:
            if owner != body:
                continue
            if all(mesh["nodes"][node][axis] == value for node in corner_nodes):
                hits.append((eid, side, face_nodes, corner_nodes))
        hits.sort(key=lambda row: (row[0], FACE_ORDER[row[1]]))
        corners_seen = [tuple(sorted(row[3])) for row in hits]
        require(len(corners_seen) == len(set(corners_seen)), f"{name}: duplicate face triangle")
        require(len(hits) == 8, f"{name}: expected eight 2x2 face triangles, found {len(hits)}")
        surfaces[name] = hits
    return surfaces


def perfect_sqrt_fraction(value: F) -> F:
    numerator = math.isqrt(value.numerator)
    denominator = math.isqrt(value.denominator)
    require(numerator * numerator == value.numerator and
            denominator * denominator == value.denominator,
            f"triangle cross-product norm is not a rational square: {value}")
    return F(numerator, denominator)


def triangle_area(mesh, corner_nodes) -> F:
    points = [mesh["nodes"][node] for node in corner_nodes]
    cross = vector_cross(vector_sub(points[1], points[0]),
                         vector_sub(points[2], points[0]))
    norm2 = sum((component * component for component in cross), F(0))
    return perfect_sqrt_fraction(norm2) / 2


def consistent_face_weights(mesh, faces):
    weights: dict[int, F] = {}
    area = F(0)
    for _eid, _side, nodes, corner_nodes in faces:
        face_area = triangle_area(mesh, corner_nodes)
        area += face_area
        for node in nodes[3:]:
            weights[node] = weights.get(node, F(0)) + face_area / 3
    require(sum(weights.values(), F(0)) == area,
            "quadratic face consistent nodal weights do not sum to area")
    return weights, area


def rigid_basis_rows(point, center):
    x, y, z = (point[i] - center[i] for i in range(3))
    return [
        [F(1), F(0), F(0), F(0), z, -y],
        [F(0), F(1), F(0), -z, F(0), x],
        [F(0), F(0), F(1), y, -x, F(0)],
    ]


def build_projection(mesh, weights):
    nodes = sorted(weights)
    area = sum(weights.values(), F(0))
    center = tuple(sum((weights[node] * mesh["nodes"][node][axis]
                        for node in nodes), F(0)) / area
                   for axis in range(3))
    basis = []
    dofs = []
    diagonal_weights = []
    for node in nodes:
        for component, row in enumerate(rigid_basis_rows(mesh["nodes"][node], center), start=1):
            basis.append(row)
            dofs.append((node, component))
            diagonal_weights.append(weights[node])
    gram = [[sum((diagonal_weights[row] * basis[row][i] * basis[row][j]
                  for row in range(len(basis))), F(0))
             for j in range(6)] for i in range(6)]
    gram_inverse = mat_inverse(gram)
    require(gram_inverse is not None, "cap rigid-mode Gram matrix is singular")
    atw = [[basis[row][column] * diagonal_weights[row]
            for row in range(len(basis))] for column in range(6)]
    projection = mat_mul(gram_inverse, atw)
    identity = mat_mul(projection, basis)
    require(identity == [[F(int(i == j)) for j in range(6)] for i in range(6)],
            "cap projection is not an exact rigid-mode left inverse")
    return {
        "nodes": nodes,
        "dofs": dofs,
        "area": area,
        "center": center,
        "basis": basis,
        "weights_diagonal": diagonal_weights,
        "gram": gram,
        "projection": projection,
    }


def cross_area2(a, b, c):
    return sum((value * value for value in vector_cross(vector_sub(b, a),
                                                        vector_sub(c, a))), F(0))


def choose_pivots(mesh, port, forbidden_nodes):
    projection = port["projection"]
    dofs = port["dofs"]
    nodes = [node for node in port["nodes"] if node not in forbidden_nodes]
    require(len(nodes) >= 3, "not enough off-contact, off-other-cap carrier nodes")
    triples = []
    for triple in combinations(nodes, 3):
        score = cross_area2(*(mesh["nodes"][node] for node in triple))
        if score:
            triples.append((score, triple))
    triples.sort(key=lambda item: (-item[0], item[1]))
    require(triples, "eligible cap nodes are collinear; no six-component pivot possible")
    best = None
    best_score = -1.0
    for area2, triple in triples:
        cols = [dofs.index((node, dof)) for node in triple for dof in (1, 2, 3)]
        triple_best = None
        for selected in combinations(cols, 6):
            pivot = [[projection[row][column] for column in selected]
                     for row in range(6)]
            inverse = mat_inverse(pivot)
            if inverse is None:
                continue
            condition = norm_inf(pivot) * norm_inf(inverse)
            if triple_best is None or condition < triple_best[0]:
                triple_best = (condition, selected, pivot, inverse, area2, triple)
        if triple_best is not None:
            # Prefer the most widely spread triple; use its best conditioned six-column minor.
            best = triple_best
            best_score = float(area2)
            break
    require(best is not None, "no exact full-rank six-DOF pivot found on eligible nodes")
    condition, selected, pivot, inverse, _area2, triple = best
    require(matrix_rank(pivot) == 6, "selected physical carrier pivot is not rank six")
    return {
        "selected_columns": list(selected),
        "dependent_dofs": [list(dofs[column]) for column in selected],
        "pivot": pivot,
        "pivot_inverse": inverse,
        "condition_inf": condition,
        "carrier_nodes": list(triple),
        "carrier_node_triangle_area_squared_mm4": best_score,
    }


def affine_displacement(body: str, point):
    x, _y, z = point
    if body == "CENTRAL":
        return (F(-3, 100000) - F(1, 100000) * x,
                F(0),
                F(-3, 100000) - F(1, 100000) * z)
    if body == "LOWER":
        return (F(0), F(0), -F(1, 100000) * (z + 2))
    return (-F(1, 100000) * (x + 2), F(0), F(0))


def target_q(name):
    if name == "PORT_TOP":
        return [F(-4, 100000), F(0), F(-5, 100000), F(0), F(0), F(0)]
    return [F(-5, 100000), F(0), F(-4, 100000), F(0), F(0), F(0)]


def source_hashes():
    checks = []
    for rel, expected in BASE_HASHES.items():
        path = BASE / rel
        actual = sha_file(path)
        require(actual == expected, f"inherited penalty source hash mismatch: {rel}")
        checks.append({"path": str(path.relative_to(REPO)), "sha256": actual})
    for rel, expected in ENERGY_HASHES.items():
        path = ENERGY / rel
        actual = sha_file(path)
        require(actual == expected, f"inherited energy source hash mismatch: {rel}")
        checks.append({"path": str(path.relative_to(REPO)), "sha256": actual})
    require(sha_file(SOURCE_ARCHIVE) == ARCHIVE_SHA256,
            "pinned CalculiX 2.23 archive hash mismatch")
    require(sha_file(MANUAL) == MANUAL_SHA256,
            "pinned CalculiX 2.23 manual hash mismatch")
    member_actual = {}
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        for member, expected in SOURCE_MEMBER_HASHES.items():
            extracted = archive.extractfile("./" + member)
            require(extracted is not None, f"missing pinned source member: {member}")
            actual = sha_bytes(extracted.read())
            require(actual == expected, f"pinned 2.23 source member mismatch: {member}")
            member_actual[member] = actual
    return checks, member_actual


def parse_coarse_nodes(path: Path):
    nodes = {}
    section = None
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            section = "node" if line.upper() == "*NODE" else None
            continue
        if section == "node":
            fields = [x.strip() for x in line.split(",")]
            if len(fields) == 4:
                nodes[int(fields[0])] = tuple(F(x) for x in fields[1:])
    return nodes


def coarse_rank_obstruction():
    source = BASE / "input/shared_slave_penalty.inp"
    coords = parse_coarse_nodes(source)
    weight_sets = {
        "PORT_TOP": {28: F(2, 3), 29: F(2, 3), 31: F(4, 3),
                     32: F(2, 3), 34: F(2, 3)},
        "PORT_RIGHT": {18: F(2, 3), 21: F(4, 3), 22: F(2, 3),
                       34: F(2, 3), 35: F(2, 3)},
    }
    eligible = {"PORT_TOP": (28, 31, 32), "PORT_RIGHT": (21, 22, 35)}
    centers = {"PORT_TOP": (F(1), F(1), F(2)),
               "PORT_RIGHT": (F(2), F(1), F(1))}
    result = {}
    for name, weights in weight_sets.items():
        fake_mesh = {"nodes": coords}
        projection = build_projection(fake_mesh, weights)
        indices = [projection["dofs"].index((node, dof))
                   for node in eligible[name] for dof in (1, 2, 3)]
        candidate = [[projection["projection"][row][col] for col in indices]
                     for row in range(6)]
        rank = matrix_rank(candidate)
        require(rank == 5, f"expected coarse rank-5 obstruction for {name}, got {rank}")
        result[name] = {
            "weights_mm2": {str(node): fstr(weight) for node, weight in weights.items()},
            "projection_center_mm": [fstr(F(x)) for x in centers[name]],
            "eligible_off_contact_off_other_cap_nodes": list(eligible[name]),
            "candidate_physical_dofs": [[node, dof] for node in eligible[name]
                                         for dof in (1, 2, 3)],
            "candidate_projection_submatrix_6x9_exact": [[fstr(x) for x in row]
                                                          for row in candidate],
            "exact_rank": rank,
            "unobservable_rigid_mode": "rotation ry about the collinear carrier-node line",
        }
    return result


def format_float(value: float | F) -> str:
    text = repr(float(value))
    if len(text) > 20:
        raise ValueError(f"Numeric field exceeds pinned f20.0 width: {text}")
    return text


def input_term_rows(terms):
    rows = []
    for start in range(0, len(terms), 4):
        fields = []
        for node, dof, coefficient in terms[start:start + 4]:
            fields.extend((str(node), str(dof), format_float(coefficient)))
        rows.append(",".join(fields))
    return rows


def ids_rows(ids, per_line=16):
    return [",".join(map(str, ids[start:start + per_line]))
            for start in range(0, len(ids), per_line)]


def make_map(mesh, surfaces, port_name, other_port_name, contact_nodes,
             support_nodes, control_ids):
    faces = surfaces[port_name]
    weights, area = consistent_face_weights(mesh, faces)
    projection = build_projection(mesh, weights)
    other_nodes = {node for face in surfaces[other_port_name] for node in face[2]}
    forbidden = set(contact_nodes) | other_nodes | set(support_nodes)
    pivots = choose_pivots(mesh, projection, forbidden)
    selected = pivots["selected_columns"]
    independent = [column for column in range(len(projection["dofs"]))
                   if column not in set(selected)]
    pivot = pivots["pivot"]
    pivot_inverse = pivots["pivot_inverse"]
    indep_matrix = mat_mul(pivot_inverse,
                           [[projection["projection"][row][col] for col in independent]
                            for row in range(6)])
    q_inverse = pivot_inverse
    q = target_q(port_name)
    eqs = []
    for dep_index, dep_col in enumerate(selected):
        dep_node, dep_dof = projection["dofs"][dep_col]
        terms = [(dep_node, dep_dof, F(1))]
        for independent_index, source_col in enumerate(independent):
            coefficient = indep_matrix[dep_index][independent_index]
            if coefficient:
                node, dof = projection["dofs"][source_col]
                terms.append((node, dof, coefficient))
        for q_index, control_node in enumerate(control_ids):
            coefficient = -q_inverse[dep_index][q_index]
            if coefficient:
                terms.append((control_node, 1, coefficient))
        eqs.append(terms)
    body = "CENTRAL"
    full_u = []
    for node in projection["nodes"]:
        full_u.extend(affine_displacement(body, mesh["nodes"][node]))
    projected_q = mat_vec(projection["projection"], full_u)
    require(projected_q == q,
            f"{port_name}: the specified affine oracle does not map to prescribed q")
    # The dual of a uniform pressure translation must recover the exact C3D10
    # consistent nodal traction vector, not merely its resultant.
    force_q = [F(0)] * 6
    if port_name == "PORT_TOP":
        force_q[2] = -PRESSURE * area
        force_component = 3
    else:
        force_q[0] = -PRESSURE * area
        force_component = 1
    dual_nodal = [sum((projection["projection"][qidx][col] * force_q[qidx]
                       for qidx in range(6)), F(0))
                  for col in range(len(projection["dofs"]))]
    target_nodal = [(-PRESSURE * weights[node] if dof == force_component else F(0))
                    for node, dof in projection["dofs"]]
    require(dual_nodal == target_nodal,
            f"{port_name}: full-map force dual differs from consistent face pressure")
    contact_terms = sorted({node for node, _dof, coeff in
                             (term for equation in eqs for term in equation)
                             if node in contact_nodes and coeff})
    require(contact_terms, f"{port_name}: no contact node remains as an independent map term")
    dependent = {tuple(item) for item in pivots["dependent_dofs"]}
    require(not any(node in contact_nodes for node, _dof in dependent),
            f"{port_name}: contact node selected as dependent")
    require(not any(node in other_nodes for node, _dof in dependent),
            f"{port_name}: other-cap node selected as dependent")
    require(not any(node in support_nodes for node, _dof in dependent),
            f"{port_name}: support/gauge node selected as dependent")
    require(len(dependent) == 6, f"{port_name}: expected six unique physical dependent DOFs")
    return {
        "name": port_name,
        "area": area,
        "weights": weights,
        "projection": projection,
        "pivots": pivots,
        "independent_columns": independent,
        "independent_map": indep_matrix,
        "equations": eqs,
        "control_ids": control_ids,
        "prescribed_q": q,
        "projected_affine_q": projected_q,
        "dual_force_vector": force_q,
        "consistent_dual_verified": True,
        "contact_nodes_retained_as_independent_terms": contact_terms,
    }


def vector_node_displacements(mesh):
    values = {}
    for node, point in sorted(mesh["nodes"].items()):
        # Node ranges identify their body without relying on coincident geometry.
        body = "CENTRAL" if node < 10000 else "LOWER" if node < 20000 else "LEFT"
        values[str(node)] = [fjson(value) for value in affine_displacement(body, point)]
    return values


def format_face_surface(name, faces):
    lines = [f"*SURFACE,NAME={name},TYPE=ELEMENT"]
    lines.extend(f"{eid},{side}" for eid, side, _nodes, _corners in faces)
    return lines


def create_deck(mesh, surfaces, maps, case_name):
    controller_nodes = []
    for port_map in maps:
        port_index = 0 if port_map["name"] == "PORT_TOP" else 1
        center = port_map["projection"]["center"]
        for control_id in port_map["control_ids"]:
            controller_nodes.append((control_id, center))

    lines = [
        "*HEADING",
        f"Three-cube refined shared-edge penalty/full-cap-motion known answer ({case_name})",
        "** Units: mm, N, MPa (N/mm2); 3 cubes are unchanged 2 mm geometry.",
        "** Mesh: each cube is a 2x2x2 Freudenthal grid, 48 C3D10 elements/body.",
        "** No CLOAD: full-cap work-dual maps prescribe the affine endpoint.",
        "*NODE",
    ]
    for node, xyz in sorted(mesh["nodes"].items()):
        lines.append(f"{node},{format_float(xyz[0])},{format_float(xyz[1])},{format_float(xyz[2])}")
    for node, xyz in controller_nodes:
        lines.append(f"{node},{format_float(xyz[0])},{format_float(xyz[1])},{format_float(xyz[2])}")
    for body, element_ids in mesh["body_elements"].items():
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={body}")
        for eid in element_ids:
            conn = mesh["elements"][eid]
            lines.append(f"{eid}," + ",".join(map(str, conn)))
    for body, node_ids in mesh["body_node_ids"].items():
        lines.append(f"*NSET,NSET={body}_NODES")
        lines.extend(ids_rows(node_ids))
    physical_nodes = sorted(node for ids in mesh["body_node_ids"].values() for node in ids)
    lines.extend(["*NSET,NSET=ALL_PHYSICAL_NODES", *ids_rows(physical_nodes)])
    control_list = [node for node, _xyz in controller_nodes]
    lines.extend(["*NSET,NSET=PORT_CONTROLS", *ids_rows(control_list)])
    for name in ("Z_CENTRAL", "Z_LOWER", "X_CENTRAL", "X_LEFT",
                 "PORT_TOP", "PORT_RIGHT"):
        lines.extend(format_face_surface(name, surfaces[name]))
    lines.extend([
        "*SURFACE INTERACTION,NAME=NORMAL_LAW",
        "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
        "100000.0",
        "** Frictionless tangential response; no *FRICTION card.",
        "*CONTACT PAIR,INTERACTION=NORMAL_LAW,TYPE=SURFACE TO SURFACE",
        "Z_CENTRAL,Z_LOWER",
    ])
    second_pair = ("X_CENTRAL,X_LEFT" if case_name == "shared_slave_motion"
                   else "X_LEFT,X_CENTRAL")
    lines.extend([
        "*CONTACT PAIR,INTERACTION=NORMAL_LAW,TYPE=SURFACE TO SURFACE",
        second_pair,
        "*MATERIAL,NAME=ELASTIC",
        "*ELASTIC",
        "100000.0,0.0",
        "*SOLID SECTION,ELSET=CENTRAL,MATERIAL=ELASTIC",
        "*SOLID SECTION,ELSET=LOWER,MATERIAL=ELASTIC",
        "*SOLID SECTION,ELSET=LEFT,MATERIAL=ELASTIC",
    ])
    for port_map in maps:
        for equation in port_map["equations"]:
            lines.append("*EQUATION")
            lines.append(str(len(equation)))
            lines.extend(input_term_rows(equation))
    lines.append("*BOUNDARY")
    # Preserve the same three body support planes and the same single out-of-plane gauge.
    support_rows = mesh["support_rows"]
    lines.extend(f"{node},{dof},{dof},0.0" for node, dof in support_rows)
    lines.extend([
        "*AMPLITUDE,NAME=PORT_RAMP",
        "0.,0.,1.,1.",
        "*STEP,NLGEOM,INC=100",
        "*STATIC,DIRECT",
        "1,1",
        "*BOUNDARY,AMPLITUDE=PORT_RAMP",
    ])
    for port_map in maps:
        for index, node in enumerate(port_map["control_ids"]):
            lines.append(f"{node},1,1,{format_float(port_map['prescribed_q'][index])}")
    lines.extend([
        "*NODE PRINT,NSET=ALL_PHYSICAL_NODES,FREQUENCY=1",
        "U,RF",
        "*NODE FILE,NSET=ALL_PHYSICAL_NODES,FREQUENCY=1",
        "U,RF",
        "*NODE PRINT,NSET=PORT_CONTROLS,FREQUENCY=1",
        "U",
        "*EL FILE,FREQUENCY=1",
        "S",
        "*SECTION PRINT,SURFACE=PORT_TOP,NAME=TOP_PORT_WRENCH",
        "SOF",
        "*SECTION PRINT,SURFACE=PORT_RIGHT,NAME=RIGHT_PORT_WRENCH",
        "SOF",
        "*EL PRINT,ELSET=CENTRAL,TOTALS=ONLY,FREQUENCY=1",
        "ELSE",
        "*EL PRINT,ELSET=LOWER,TOTALS=ONLY,FREQUENCY=1",
        "ELSE",
        "*EL PRINT,ELSET=LEFT,TOTALS=ONLY,FREQUENCY=1",
        "ELSE",
        "*CONTACT FILE,FREQUENCY=1",
        "CDIS,CSTR",
        "*CONTACT PRINT,TOTALS=ONLY,FREQUENCY=1",
        "CELS",
        "*CONTACT PRINT,SLAVE=Z_CENTRAL,MASTER=Z_LOWER,FREQUENCY=1",
        "CF,CFN,CFS",
        "*CONTACT PRINT,SLAVE=" + ("X_CENTRAL,MASTER=X_LEFT" if case_name == "shared_slave_motion"
                                   else "X_LEFT,MASTER=X_CENTRAL") + ",FREQUENCY=1",
        "CF,CFN,CFS",
        "*END STEP",
        "",
    ])
    return "\n".join(lines)


def parse_equation_cards(deck_text):
    lines = deck_text.splitlines()
    cards = []
    index = 0
    while index < len(lines):
        if lines[index].strip().upper() != "*EQUATION":
            index += 1
            continue
        index += 1
        require(index < len(lines), "equation card has no term count")
        term_count = int(lines[index].strip())
        index += 1
        fields = []
        while len(fields) < 3 * term_count:
            require(index < len(lines) and not lines[index].strip().startswith("*"),
                    "equation card ended before all terms were serialized")
            fields.extend(field.strip() for field in lines[index].split(",") if field.strip())
            index += 1
        require(len(fields) == 3 * term_count, "equation data row has extra or missing fields")
        cards.append([(int(fields[i]), int(fields[i + 1]), float(fields[i + 2]))
                      for i in range(0, len(fields), 3)])
    return cards


def audit_serialized_equations(deck_text, maps, mesh):
    cards = parse_equation_cards(deck_text)
    expected = [equation for port_map in maps for equation in port_map["equations"]]
    require(len(cards) == len(expected) == 12, "serialized deck does not contain twelve equations")
    physical_u = {}
    for node, point in mesh["nodes"].items():
        body = "CENTRAL" if node < 10000 else "LOWER" if node < 20000 else "LEFT"
        for dof, value in enumerate(affine_displacement(body, point), start=1):
            physical_u[(node, dof)] = float(value)
    control_u = {}
    for port_map in maps:
        for control, value in zip(port_map["control_ids"], port_map["prescribed_q"]):
            control_u[control] = float(value)
    affine_residual = 0.0
    for card_index, (card, exact_terms) in enumerate(zip(cards, expected)):
        exact_serialized = [(node, dof, float(format_float(coefficient)))
                            for node, dof, coefficient in exact_terms]
        require(len(card) == len(exact_serialized),
                f"serialized equation {card_index} term count changed")
        for actual, wanted in zip(card, exact_serialized):
            require(actual[:2] == wanted[:2] and actual[2] == wanted[2],
                    f"serialized equation {card_index} differs from generated coefficients")
        residual = 0.0
        for node, dof, coefficient in card:
            if node in control_u:
                require(dof == 1, "controller equation references a non-scalar DOF")
                value = control_u[node]
            else:
                value = physical_u[(node, dof)]
            residual += coefficient * value
        affine_residual = max(affine_residual, abs(residual))

    per_port = {}
    cursor = 0
    for port_map in maps:
        proj = port_map["projection"]
        selected = port_map["pivots"]["selected_columns"]
        independent = port_map["independent_columns"]
        dofs = proj["dofs"]
        p = [[float(value) for value in row] for row in proj["projection"]]
        p_j = [[p[row][column] for column in selected] for row in range(6)]
        p_r = [[p[row][column] for column in independent] for row in range(6)]
        cards_for_port = cards[cursor:cursor + 6]
        cursor += 6
        require([card[0][:2] for card in cards_for_port] ==
                [tuple(dofs[column]) for column in selected],
                f"{port_map['name']}: serialized dependent DOF order differs")
        control_ids = port_map["control_ids"]
        independent_lookup = {dofs[column]: idx for idx, column in enumerate(independent)}
        n_map = [[0.0 for _ in independent] for _ in range(6)]
        m_map = [[0.0 for _ in range(6)] for _ in range(6)]
        for row_index, card in enumerate(cards_for_port):
            for term_index, (node, dof, coefficient) in enumerate(card):
                if term_index == 0:
                    require(coefficient == 1.0, "dependent equation coefficient is not +1")
                elif node in control_ids:
                    m_map[row_index][control_ids.index(node)] = -coefficient
                else:
                    key = (node, dof)
                    require(key in independent_lookup,
                            f"{port_map['name']}: dependent variable leaked into independent terms")
                    n_map[row_index][independent_lookup[key]] = coefficient
        pjm = [[sum(p_j[i][k] * m_map[k][j] for k in range(6))
                for j in range(6)] for i in range(6)]
        pjn = [[sum(p_j[i][k] * n_map[k][j] for k in range(6))
                for j in range(len(independent))] for i in range(6)]
        identity_error = max(abs(pjm[i][j] - float(i == j))
                             for i in range(6) for j in range(6))
        independent_error = max(abs(pjn[i][j] - p_r[i][j])
                                for i in range(6) for j in range(len(independent)))
        # Deterministic arbitrary state checks the serialized map and its work dual.
        random_u = [0.000013 * (idx + 1) for idx in range(len(independent))]
        random_q = [0.000021 * (idx - 2) for idx in range(6)]
        dependent_u = [sum(m_map[i][j] * random_q[j] for j in range(6))
                       - sum(n_map[i][j] * random_u[j] for j in range(len(independent)))
                       for i in range(6)]
        whole_u = [0.0] * len(dofs)
        for index, column in enumerate(selected):
            whole_u[column] = dependent_u[index]
        for index, column in enumerate(independent):
            whole_u[column] = random_u[index]
        reconstructed_q = [sum(p[row][col] * whole_u[col] for col in range(len(dofs)))
                            for row in range(6)]
        q_reconstruction_error = max(abs(a - b) for a, b in zip(reconstructed_q, random_q))
        force_q = [float(value) for value in port_map["dual_force_vector"]]
        dual = [sum(p[row][col] * force_q[row] for row in range(6))
                for col in range(len(dofs))]
        left_work = sum(force_q[idx] * reconstructed_q[idx] for idx in range(6))
        right_work = sum(dual[idx] * whole_u[idx] for idx in range(len(dofs)))
        virtual_work_error = abs(left_work - right_work)
        per_port[port_map["name"]] = {
            "equation_count": len(cards_for_port),
            "serialized_term_counts": [len(card) for card in cards_for_port],
            "selected_dependent_dofs_first_terms": [list(card[0][:2]) for card in cards_for_port],
            "projection_reconstruction_identity_max_abs_error": identity_error,
            "projection_independent_term_max_abs_error": independent_error,
            "deterministic_state_q_reconstruction_max_abs_error_mm_or_rad": q_reconstruction_error,
            "deterministic_state_virtual_work_error_Nmm": virtual_work_error,
            "contact_nodes_remain_independent": True,
            "no_pivot_term_in_opposite_port_map": True,
        }
    return {
        "equation_count": len(cards),
        "max_affine_field_equation_residual_mm": affine_residual,
        "per_port": per_port,
    }


def source_file_dict(source_checks, source_members):
    return {
        "schema": "shared_edge_penalty_motion_source_snapshot/v1",
        "preparation_script": {
            "path": str((HERE / "prepare.py").relative_to(REPO)),
            "sha256": sha_file(HERE / "prepare.py"),
        },
        "source_packet": str(BASE.relative_to(REPO)),
        "source_input_freeze_sha256": BASE_FREEZE_SHA256,
        "source_artifact_sha256": {row["path"]: row["sha256"] for row in source_checks},
        "source_archive": {
            "path": str(SOURCE_ARCHIVE.relative_to(REPO)),
            "sha256": sha_file(SOURCE_ARCHIVE),
            "pinned_member_sha256": source_members,
        },
        "manual": {
            "path": str(MANUAL.relative_to(REPO)),
            "url": "https://www.dhondt.de/ccx_2.23.pdf",
            "version": "2.23",
            "sha256": sha_file(MANUAL),
            "topics": ["*STATIC,DIRECT", "*EQUATION", "*SURFACE",
                       "*CONTACT PAIR", "*CONTACT PRINT", "*EL PRINT",
                       "*NODE FILE NSET selection", "*EL FILE S and SOF"],
        },
        "pinned_solver": {
            "version": "2.23",
            "base_image_id": "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38",
            "binary_path": "/usr/local/bin/ccx-upstream-2.23",
            "binary_sha256": "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "patched_or_instrumented_binary": False,
        },
        "lineage": {
            "inherited_penalty_known_answer": "contact-penalty-shared-edge-known-answer-attempt01",
            "inherited_energy_known_answer": "contact-energy-known-answer-attempt01",
            "method_difference": "Only this new fixture changes mesh density, replaces the two pressure CLOAD patterns with full six-component off-contact port motion maps, and corrects output requests from pinned 2.23 source evidence; the original three-body geometry, material, penalty law, support topology, contact pair role patterns and affine endpoint are retained.",
            "pinned_2_23_output_correction": "One NODE FILE request preserves ALL_PHYSICAL_NODES for U and RF; PORT_CONTROLS U remains DAT-only because later NODE FILE U sets the shared U NSET selection. EL FILE S is requested for the full mesh so SOF section force integration has nodal stress data.",
            "frozen_authority_copied": False,
            "native_outputs_copied": False,
        },
    }


def build_all():
    source_checks, source_members = source_hashes()
    mesh = build_mesh()
    surfaces = face_surfaces(mesh)
    weights_by_port = {name: consistent_face_weights(mesh, surfaces[name])
                       for name in ("PORT_TOP", "PORT_RIGHT")}
    contact_surface_names = ("Z_CENTRAL", "Z_LOWER", "X_CENTRAL", "X_LEFT")
    all_contact_nodes = {node for name in contact_surface_names
                         for face in surfaces[name] for node in face[2]}
    support_nodes = {node for face in surfaces["LOWER_REMOTE_UZ"] + surfaces["LEFT_REMOTE_UX"]
                     for node in face[2]}
    corner = mesh["body_corner_lookup"]
    lower_anchor_a = corner["LOWER"][(0, 0, 0)]
    lower_anchor_b = corner["LOWER"][(2, 0, 0)]
    left_anchor_a = corner["LEFT"][(0, 0, 0)]
    left_anchor_b = corner["LEFT"][(0, 2, 0)]
    central_gauge = corner["CENTRAL"][(2, 0, 2)]
    support_rows = set()
    for face in surfaces["LOWER_REMOTE_UZ"]:
        for node in face[2]:
            support_rows.add((node, 3))
    support_rows.update({(lower_anchor_a, 1), (lower_anchor_a, 2),
                         (lower_anchor_b, 2)})
    for face in surfaces["LEFT_REMOTE_UX"]:
        for node in face[2]:
            support_rows.add((node, 1))
    support_rows.update({(left_anchor_a, 2), (left_anchor_a, 3),
                         (left_anchor_b, 3), (central_gauge, 2)})
    mesh["support_rows"] = sorted(support_rows)
    mesh["support_nodes"] = {node for node, _dof in support_rows}
    require(not (mesh["support_nodes"] & all_contact_nodes),
            "an explicit remote/gauge support overlaps contact nodes")
    controls_start = max(mesh["nodes"]) + 500
    top_controls = list(range(controls_start + 1, controls_start + 7))
    right_controls = list(range(controls_start + 7, controls_start + 13))
    top_map = make_map(mesh, surfaces, "PORT_TOP", "PORT_RIGHT",
                       all_contact_nodes, mesh["support_nodes"], top_controls)
    right_map = make_map(mesh, surfaces, "PORT_RIGHT", "PORT_TOP",
                         all_contact_nodes, mesh["support_nodes"], right_controls)
    top_deps = {tuple(row) for row in top_map["pivots"]["dependent_dofs"]}
    right_deps = {tuple(row) for row in right_map["pivots"]["dependent_dofs"]}
    require(not (top_deps & right_deps), "port maps have overlapping dependent DOFs")
    # A dependent DOF cannot appear anywhere as a physical term in the other port's equations.
    for port_map, other_map in ((top_map, right_map), (right_map, top_map)):
        other_terms = {(node, dof) for equation in other_map["equations"]
                       for node, dof, _coefficient in equation}
        require(not ({tuple(row) for row in port_map["pivots"]["dependent_dofs"]}
                     & other_terms), "one port's dependent DOF occurs in the other port equations")
    ports = [top_map, right_map]
    mesh["nodes"] = mesh["nodes"]

    # Face matching, area and analytic affine field checks for each physical interface.
    paired = [("Z_CENTRAL", "Z_LOWER"), ("X_CENTRAL", "X_LEFT")]
    interface_checks = {}
    for central_name, outer_name in paired:
        central_coords = sorted(tuple(mesh["nodes"][node] for node in face[2])
                                for face in surfaces[central_name])
        outer_coords = sorted(tuple(mesh["nodes"][node] for node in face[2])
                              for face in surfaces[outer_name])
        # Match all six quadratic face nodes per triangle, independent of face winding.
        canonical = lambda rows: sorted(tuple(sorted(point for point in row)) for row in rows)
        require(canonical(central_coords) == canonical(outer_coords),
                f"contact faces do not have matching quadratic triangles: {central_name}")
        central_area = sum((triangle_area(mesh, face[3]) for face in surfaces[central_name]), F(0))
        outer_area = sum((triangle_area(mesh, face[3]) for face in surfaces[outer_name]), F(0))
        require(central_area == AREA_EXPECTED and outer_area == AREA_EXPECTED,
                f"{central_name}: expected 4 mm2 matching contact areas")
        interface_checks[central_name] = {
            "outer_surface": outer_name,
            "area_central_mm2": fstr(central_area),
            "area_outer_mm2": fstr(outer_area),
            "matching_quadratic_triangles": len(central_coords),
            "matching_six_node_face_sextets": len(central_coords),
            "central_nodes": sorted({node for face in surfaces[central_name] for node in face[2]}),
            "outer_nodes": sorted({node for face in surfaces[outer_name] for node in face[2]}),
        }

    # Prepare equation cards with serialized decimal coefficients and verify affine residuals.
    decks = {}
    for case in ("shared_slave_motion", "cross_role_motion"):
        decks[f"input/{case}.inp"] = create_deck(mesh, surfaces, ports, case).encode()
    equation_audits = {
        case: audit_serialized_equations(data.decode(), ports, mesh)
        for case, data in ((name.removeprefix("input/").removesuffix(".inp"), data)
                           for name, data in decks.items())
    }
    for case, audit in equation_audits.items():
        require(audit["equation_count"] == 12,
                f"{case}: serialized equation audit did not find twelve equations")
        require(audit["max_affine_field_equation_residual_mm"] <= 1e-12,
                f"{case}: serialized equation card does not retain the affine oracle")
        for port_name, port_audit in audit["per_port"].items():
            for key in ("projection_reconstruction_identity_max_abs_error",
                        "projection_independent_term_max_abs_error",
                        "deterministic_state_q_reconstruction_max_abs_error_mm_or_rad",
                        "deterministic_state_virtual_work_error_Nmm"):
                require(port_audit[key] <= 1e-11,
                        f"{case}/{port_name}: serialized equation {key} exceeds preflight tolerance")

    case_specs = {
        "shared_slave_motion": {
            "case_order": 1,
            "contact_pairs": [
                {"slave": "Z_CENTRAL", "master": "Z_LOWER", "axis": "+z resultant on central slave"},
                {"slave": "X_CENTRAL", "master": "X_LEFT", "axis": "+x resultant on central slave"},
            ],
        },
        "cross_role_motion": {
            "case_order": 2,
            "contact_pairs": [
                {"slave": "Z_CENTRAL", "master": "Z_LOWER", "axis": "+z resultant on central slave"},
                {"slave": "X_LEFT", "master": "X_CENTRAL", "axis": "-x resultant on X_LEFT slave"},
            ],
        },
    }
    pair_wrench_oracles = {
        "Z_CENTRAL": {
            "resultant_reference_point_mm": [1.0, 1.0, 0.0],
            "expected_CFN_force_N": [0.0, 0.0, 4.0],
            "expected_CFN_moment_about_origin_Nmm": [4.0, -4.0, 0.0],
        },
        "X_CENTRAL": {
            "resultant_reference_point_mm": [0.0, 1.0, 1.0],
            "expected_CFN_force_N": [4.0, 0.0, 0.0],
            "expected_CFN_moment_about_origin_Nmm": [0.0, 4.0, -4.0],
        },
        "X_LEFT": {
            "resultant_reference_point_mm": [0.0, 1.0, 1.0],
            "expected_CFN_force_N": [-4.0, 0.0, 0.0],
            "expected_CFN_moment_about_origin_Nmm": [0.0, -4.0, 4.0],
        },
    }
    for case, spec in case_specs.items():
        for pair in spec["contact_pairs"]:
            oracle = pair_wrench_oracles[pair["slave"]]
            pair["resultant_reference_point_mm"] = oracle["resultant_reference_point_mm"]
            pair["expected_CFN_vector_N"] = oracle["expected_CFN_force_N"]
            pair["expected_CFN_moment_about_origin_Nmm"] = oracle[
                "expected_CFN_moment_about_origin_Nmm"]
            pair["expected_CF_vector_N"] = oracle["expected_CFN_force_N"]
            pair["expected_CF_moment_about_origin_Nmm"] = oracle[
                "expected_CFN_moment_about_origin_Nmm"]
            pair["expected_projected_normal_force_N_tension_positive"] = -4.0
            pair["expected_CFS_vector_N"] = [0.0, 0.0, 0.0]
            pair["expected_CFS_moment_about_origin_Nmm"] = [0.0, 0.0, 0.0]

    source_snapshot = source_file_dict(source_checks, source_members)
    source_snapshot_bytes = json.dumps(source_snapshot, indent=2, sort_keys=True).encode() + b"\n"
    mesh_node_disp = vector_node_displacements(mesh)
    energy = {
        "body_ELSE_Nmm": {"CENTRAL": 8.0e-5, "LOWER": 4.0e-5, "LEFT": 4.0e-5},
        "ELSE_sum_Nmm": 1.6e-4,
        "penalty_CELS_Nmm": 4.0e-5,
        "ELSE_plus_CELS_total_Nmm": 2.0e-4,
        "tolerance": "abs(observed-reference) <= 0.01*reference + 1e-6 Nmm; inherited unchanged from the pinned penalty energy known-answer packet",
    }
    displacement_tolerance = 1.0e-7
    expected = {
        "schema": "calculix_penalty_shared_edge_motion_known_answer/v1",
        "status": "PREPARED_FOR_PARENT_STATIC_REVIEW_NO_NATIVE_EXECUTION",
        "native_execution_authorized": False,
        "mechanical_or_joint_acceptance": False,
        "geometry": {
            "bodies": {"CENTRAL": "x=[0,2], y=[0,2], z=[0,2]",
                       "LOWER": "x=[0,2], y=[0,2], z=[-2,0]",
                       "LEFT": "x=[-2,0], y=[0,2], z=[0,2]"},
            "element_type": "C3D10",
            "cells_per_body": [2, 2, 2],
            "tets_per_cell": 6,
            "elements_per_body": 48,
            "total_elements": sum(len(v) for v in mesh["body_elements"].values()),
            "nodes_per_body": {body: len(ids) for body, ids in mesh["body_node_ids"].items()},
            "total_physical_nodes": sum(len(ids) for ids in mesh["body_node_ids"].values()),
            "contact_areas_mm2": {"Z": 4.0, "X": 4.0},
            "contact_surface_triangles_per_pair": 8,
            "material": {"E_N_per_mm2": fjson(E), "nu": fjson(NU)},
            "contact": {"law": "frictionless linear pressure-overclosure penalty",
                        "K_N_per_mm3": fjson(K)},
            "supports": "Same physical remote planes and single central out-of-plane y gauge as the coarse penalty oracle; refined support faces constrain the same normal direction at all refined face nodes.",
            "refinement_decision": "One specified regular 2x2x2 grid per original 2 mm cube, each unit cell split into the same six-tet Freudenthal pattern, then converted to straight-sided C3D10. No geometry, material, contact, support or oracle tuning.",
        },
        "mesh_sha256": {name: sha_bytes(data) for name, data in decks.items()},
        "case_order": list(case_specs),
        "cases": case_specs,
        "solver": {
            "version": "2.23",
            "manual_url": "https://www.dhondt.de/ccx_2.23.pdf",
            "manual_sha256": MANUAL_SHA256,
            "source_archive_sha256": sha_file(SOURCE_ARCHIVE),
            "base_image_id": "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38",
            "binary_path": "/usr/local/bin/ccx-upstream-2.23",
            "binary_sha256": "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863",
            "procedure": "*STATIC,DIRECT, one fixed increment 1,1, prescribed endpoint through a linear amplitude",
            "nlgeom": True,
            "patched_or_instrumented_binary": False,
        },
        "motion_map": {
            "definition": "For each cap, q=(A^T W A)^(-1) A^T W u, where A is the 3D rigid translation/rotation basis about the exact area centroid and W repeats each integrated C3D10 quadratic-face midside shape-function weight for U1/U2/U3. The six control DOFs are independent scalar controller-node DOF1 values.",
            "translation_order": ["tx_mm", "ty_mm", "tz_mm"],
            "rotation_order": ["rx_rad", "ry_rad", "rz_rad"],
            "maps": {},
            "equation_policy": "Each of six dependent physical DOFs per port is the first term of one *EQUATION; contact and other-port surface DOFs remain independent terms. No selected dependent DOF is a support/gauge/contact DOF, and no selected dependent DOF appears in the other port's equations.",
            "coarse_rank5_obstruction": coarse_rank_obstruction(),
        },
        "analytical_known_answer": {
            "affine_endpoint_displacement_mm_by_physical_node": mesh_node_disp,
            "affine_field": {
                "CENTRAL": "Ux=-3e-5-1e-5*x; Uy=0; Uz=-3e-5-1e-5*z",
                "LOWER": "Ux=Uy=0; Uz=-1e-5*(z+2)",
                "LEFT": "Ux=-1e-5*(x+2); Uy=Uz=0",
            },
            "port_q_mm_rad": {
                "PORT_TOP_at_centroid_[1,1,2]": [-4e-5, 0.0, -5e-5, 0.0, 0.0, 0.0],
                "PORT_RIGHT_at_centroid_[2,1,1]": [-5e-5, 0.0, -4e-5, 0.0, 0.0, 0.0],
            },
            "normal_force_N_each_pair": 4.0,
            "series_compliance_mm3_per_N": 5.0e-5,
            "approach_mm_each_axis": 5.0e-5,
            "interface_penalty_overclosure_mm_each_pair": 1.0e-5,
            "signed_central_minus_outer_interface_gap_mm_each_pair": -1.0e-5,
            "contact_resultant_output": "CFN is a pair resultant vector, not integrated positive pressure magnitude. The pinned routine labels projection along the printed mean normal tension-positive; expected compression scalar is -4 N. Per-pair force and origin-moment vectors are explicitly listed in cases from r cross F. CF equals CFN here because frictionless CFS is zero.",
            "contact_pairs": interface_checks,
            "energy_Nmm": energy,
            "work_interpretation": "No external work criterion is inferred from ELSE/CELS. This single endpoint motion case does not validate path quadrature across open-gap closure or a current-joint work floor.",
        },
        "output_contract": {
            "physical_node_output": "DAT and FRD U/RF for every physical node in all three bodies; one pinned NODE FILE request selects ALL_PHYSICAL_NODES for both U and RF, with no missing-node allowance.",
            "control_output": "DAT U for 12 scalar control DOFs; compare their scalar DOF1 values with prescribed q and independently reconstruct each q from the physical cap U field. No separate controller FRD rows are required.",
            "element_stress_output": "FRD S requested for the full physical mesh to populate pinned 2.23 nodal stresses used by SOF; exact finite SOF section reports are audited.",
            "port_output": ["TOP_PORT_WRENCH:SOF", "RIGHT_PORT_WRENCH:SOF"],
            "contact_field_output": ["CDIS", "CSTR"],
            "contact_pair_resultants": [
                "CF,CFN,CFS selected by exact slave/master pair for Z_CENTRAL/Z_LOWER",
                "CF,CFN,CFS selected by exact slave/master pair for the case-specific X pair",
            ],
            "body_energy_output": ["CENTRAL ELSE", "LOWER ELSE", "LEFT ELSE"],
            "contact_energy_output": "global CELS (mode-1 penalty only)",
            "trace": "one accepted full increment at time 1; no rejected attempt or cutback; verify .sta/.cvg parity and native exit status",
            "contact_resultant_gate": "Analytical endpoint sign/magnitude and finite output are checked after execution. No zero-resultant/no-bearing inference or first-onset gate is made here.",
        },
        "inherited_numerical_gates": {
            "force_abs_tolerance_N": 0.041,
            "force_formula": "0.01*4 N + 0.001 N per normal support resultant",
            "normal_compliance_relative_tolerance": 0.01,
            "normal_compliance_absolute_tolerance_mm3_per_N": 1e-10,
            "profile_gap_warp_absolute_tolerance_mm": displacement_tolerance,
            "transverse_auxiliary_and_force_closure_tolerance_N": 0.041,
            "moment_closure_tolerance_Nmm": 0.041,
            "pair_resultant_moment_abs_tolerance_Nmm": 0.041,
            "moment_tolerance_formula": "0.01*4 N*1 mm reference length + 0.001 Nmm floor",
            "energy_relative_tolerance": 0.01,
            "energy_absolute_tolerance_Nmm": 1e-6,
            "gate_lineage": "Unchanged from the frozen shared-edge penalty known-answer mechanical gates and the pinned penalty energy known-answer gate; no post-result tuning.",
        },
        "limits": [
            "This is a penalty method fixture, not MORTAR validation.",
            "It tests the combined two-pair shared-node role pattern and six-component work-dual motion maps only in this homogeneous C3D10 cube coupon.",
            "Its per-pair resultants occur at the compressed endpoint; zero/touch/first local contact is not observed. A finite nonzero resultant can establish some bearing, but zero cannot establish absence and a resultant cannot identify the first local bearing point.",
            "No current-joint transfer, joint strength, adopted structural criterion, material qualification or release is established.",
            "Multi-pair ELSE/CELS output is an analytical method check, not a work-balance result or a substitute for current-joint global energy history.",
        ],
        "source_snapshot": "source-snapshot.json",
        "preparation_script_sha256": sha_file(HERE / "prepare.py"),
        "serialized_equation_audits": equation_audits,
    }

    # Build the full map evidence in exact fractions, plus the serialized pivot/equation data.
    motion_maps = {}
    for port_map in ports:
        proj = port_map["projection"]
        motion_maps[port_map["name"]] = {
            "face_area_mm2": fstr(port_map["area"]),
            "area_centroid_mm": [fstr(x) for x in proj["center"]],
            "face_weights_mm2_by_node": {str(node): fstr(weight)
                                           for node, weight in sorted(port_map["weights"].items())},
            "projection_matrix_P_exact": [[fstr(x) for x in row]
                                           for row in proj["projection"]],
            "projection_dof_columns": [list(pair) for pair in proj["dofs"]],
            "projection_gram_matrix_exact": [[fstr(x) for x in row] for row in proj["gram"]],
            "projection_rank": matrix_rank(proj["projection"]),
            "dependent_dofs": port_map["pivots"]["dependent_dofs"],
            "dependent_carrier_nodes": port_map["pivots"]["carrier_nodes"],
            "pivot_matrix_exact": [[fstr(x) for x in row]
                                    for row in port_map["pivots"]["pivot"]],
            "pivot_inverse_exact": [[fstr(x) for x in row]
                                     for row in port_map["pivots"]["pivot_inverse"]],
            "pivot_rank": 6,
            "pivot_condition_inf": port_map["pivots"]["condition_inf"],
            "controller_node_ids": port_map["control_ids"],
            "prescribed_q": [fjson(x) for x in port_map["prescribed_q"]],
            "affine_projection_q_exact": [fstr(x) for x in port_map["projected_affine_q"]],
            "consistent_pressure_dual_check": "exact P^T Q equals the consistent quadratic-face nodal pressure vector",
            "contact_nodes_retained_as_independent_equation_terms": port_map["contact_nodes_retained_as_independent_terms"],
            "equation_term_counts": [len(eq) for eq in port_map["equations"]],
            "serialized_equation_affine_residual_max_mm": max(
                audit["max_affine_field_equation_residual_mm"]
                for audit in equation_audits.values()),
        }
        motion_maps[port_map["name"]]["serialized_equation_checks_by_case"] = {
            case: audit["per_port"][port_map["name"]]
            for case, audit in equation_audits.items()
        }
    expected["motion_map"]["maps"] = motion_maps

    # Run role and input-content checks without invoking a solver.
    deck_reports = {}
    for case, data in decks.items():
        text = data.decode()
        require("*CLOAD" not in text.upper(), f"{case}: unexpected force loading")
        require(text.upper().count("*CONTACT PAIR,") == 2,
                f"{case}: expected exactly two contact pairs")
        require(text.upper().count("*CONTACT PRINT,SLAVE=") == 2,
                f"{case}: expected pair-specific resultants for both pairs")
        require("*STATIC,DIRECT" in text.upper(), f"{case}: missing pinned DIRECT procedure")
        require(text.upper().count("*EQUATION") == 12,
                f"{case}: expected twelve six-component scalar equations")
        require(text.upper().count("*NODE FILE,") == 1,
                f"{case}: one physical-node U/RF NODE FILE card is required")
        require(text.upper().count("*NODE PRINT,NSET=PORT_CONTROLS") == 1 and
                text.upper().count("*EL FILE,FREQUENCY=1") == 1,
                f"{case}: controller DAT or section-stress output request differs")
        deck_reports[data.decode().splitlines()[1].split("(")[-1].rstrip(")")] = {
            "sha256": sha_bytes(data),
            "byte_count": len(data),
            "contact_pair_count": 2,
            "contact_pair_resultant_requests": 2,
            "equation_count": 12,
            "contains_CLOAD": False,
            "node_file_cards": text.upper().count("*NODE FILE,"),
            "controller_node_print_cards": text.upper().count("*NODE PRINT,NSET=PORT_CONTROLS"),
            "element_stress_file_cards": text.upper().count("*EL FILE,FREQUENCY=1"),
        }
    expected_bytes = json.dumps(expected, indent=2, sort_keys=True).encode() + b"\n"
    preflight = {
        "schema": "shared_edge_penalty_motion_static_preflight/v1",
        "status": "PASS_STATIC_ORACLE_AND_INPUT_PREFLIGHT_NO_NATIVE_EXECUTION",
        "native_execution": False,
        "freeze_created": False,
        "source_pins": {"artifact_hashes_checked": len(source_checks),
                        "source_members_checked": len(source_members),
                        "all_match": True,
                        "preparation_script_sha256": sha_file(HERE / "prepare.py")},
        "mesh": {
            "body_element_counts": {body: len(eids) for body, eids in mesh["body_elements"].items()},
            "total_elements": len(mesh["elements"]),
            "physical_node_count": len(mesh["nodes"]),
            "all_element_determinants_positive": True,
            "element_volume_sum_mm3": {body: 8.0 for body in BODY_SPECS},
            "contact_surface_triangle_counts": {name: len(surfaces[name])
                                                  for name in ("Z_CENTRAL", "Z_LOWER", "X_CENTRAL", "X_LEFT")},
            "contact_area_and_matching_mesh_checks": interface_checks,
        },
        "coarse_rank5_obstruction": expected["motion_map"]["coarse_rank5_obstruction"],
        "refined_maps": motion_maps,
        "serialized_equation_audits": equation_audits,
        "supports": {
            "support_scalar_count": len(mesh["support_rows"]),
            "support_contact_node_overlap": 0,
            "central_y_gauge_node": central_gauge,
            "support_nodes_are_only_on_original_remote_planes": True,
        },
        "case_decks": deck_reports,
        "known_answer": {
            "affine_port_q_matches": True,
            "pressure_work_dual_matches_consistent_face_tractions": True,
            "physical_contact_force_each_pair_N": 4.0,
            "contact_pair_origin_wrenches": pair_wrench_oracles,
            "contact_pair_moment_absolute_tolerance_Nmm": 0.041,
            "compliance_mm3_per_N": 5e-5,
            "approach_mm": 5e-5,
            "overclosure_mm": 1e-5,
            "energy_ELSE_CELS": energy,
        },
        "interpretation": "Static preflight of geometry, source lineage, map rank, exact affine oracle, work dual, contact roles, pinned 2.23 output selection, and energy arithmetic only. No native response or readiness/freeze decision is asserted.",
    }
    preflight_bytes = (json.dumps(preflight, indent=2, sort_keys=True) + "\n").encode()
    readiness = {
        "schema": "shared_edge_penalty_motion_readiness/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW",
        "native_execution_authorized": False,
        "input_freeze_created": False,
        "parent_static_review": "PENDING",
        "static_preflight": "PASS; no native execution",
        "preflight_path": "preflight.json",
        "preflight_sha256": sha_bytes(preflight_bytes),
        "input_sha256": {path: sha_bytes(data) for path, data in decks.items()},
        "expected_sha256": sha_bytes(expected_bytes),
        "source_snapshot_sha256": sha_bytes(source_snapshot_bytes),
        "prepare_py_sha256": sha_file(HERE / "prepare.py"),
        "required_parent_review": [
            "review refined mesh conformity and face-side numbering against pinned CalculiX 2.23",
            "review exact full-six pivot disjointness and pressure work-dual result",
            "review pair CFN vector orientation and ELSE/CELS multi-pair tolerances",
            "review endpoint-only scope and no-onset interpretation",
        ],
        "blocked_claims": ["native convergence", "accepted equilibrium", "joint acceptance", "MORTAR applicability", "current-joint transfer", "first-bearing onset"],
    }
    files = {
        "input/shared_slave_motion.inp": decks["input/shared_slave_motion.inp"],
        "input/cross_role_motion.inp": decks["input/cross_role_motion.inp"],
        "expected.json": expected_bytes,
        "source-snapshot.json": source_snapshot_bytes,
        "preflight.json": preflight_bytes,
        "readiness.json": (json.dumps(readiness, indent=2, sort_keys=True) + "\n").encode(),
    }
    return files, preflight


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="regenerate in memory and require all packet outputs byte-identical")
    args = parser.parse_args()
    files, _preflight = build_all()
    if args.check:
        for relative, expected in files.items():
            path = HERE / relative
            require(path.is_file() and path.read_bytes() == expected,
                    f"generated packet file differs: {relative}")
        print("PASS_STATIC_ORACLE_AND_INPUT_PREFLIGHT_NO_NATIVE_EXECUTION")
        return
    existing = [relative for relative in files if (HERE / relative).exists()]
    require(not existing,
            "refusing to overwrite existing preparation artifact(s): " + ", ".join(existing))
    for relative, data in files.items():
        path = HERE / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as output:
            output.write(data)
    print("PASS_STATIC_ORACLE_AND_INPUT_PREFLIGHT_NO_NATIVE_EXECUTION")
    print(f"Wrote {len(files)} preparation artifacts; no freeze or native run created.")


if __name__ == "__main__":
    main()
