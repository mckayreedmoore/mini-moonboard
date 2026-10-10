#!/usr/bin/env python3
"""Build a bounded A09 pair-021 C3D10/TRIA6 curved-contact crop.

Requires this repository's .venv (NumPy and SciPy) for independent curved
TRIA6 closest-point projections. It never launches Code_Aster.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import minimize


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "fea" / "code_aster_trial"))
from a09_topology import FACES  # noqa: E402


OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"
MESH_PATH = SOURCE / "mesh.inp"
CONTACT_PATH = SOURCE / "contact-fragment.inc"
SEED_NODE = 61143
SLAVE_RADIUS_MM = 5.0
MASTER_RADIUS_MM = 10.0
MAX_CROP_TETS = 220

# Pair 021 is extracted unchanged from the source map. It is not a planar
# idealization and not a modification of the candidate's source geometry.
PAIR_SLAVE = "WJCP_021_S"
PAIR_MASTER = "WJCP_021_M"
HISTORY = (
    (0.0, 0.0),
    (1.0, -0.10),
    (2.0, -0.20),
    (3.0, 0.0),
    (4.0, 0.50),
    (5.0, 0.60),
    (6.0, 0.65),
    (7.0, 0.60),
    (8.0, 0.50),
    (9.0, 0.0),
    (10.0, -0.10),
    (11.0, 0.60),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_abaqus_mesh(path: Path):
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    card = ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            card = line.upper()
            continue
        fields = [field.strip() for field in line.split(",")]
        if card.startswith("*NODE"):
            nodes[int(fields[0])] = tuple(map(float, fields[1:4]))
        elif card.startswith("*ELEMENT"):
            if "TYPE=C3D10" not in card:
                raise ValueError(f"unexpected source element card: {card}")
            values = tuple(map(int, fields))
            if len(values) != 11:
                raise ValueError(f"C3D10 row has {len(values)-1} nodes: {line}")
            elements[values[0]] = values[1:]
    if not nodes or not elements:
        raise ValueError("source mesh did not contain nodes and C3D10 elements")
    return nodes, elements


def read_pair_fragment(path: Path):
    surfaces: dict[str, list[tuple[int, int]]] = {}
    node_sets: dict[str, set[int]] = {}
    card = ""
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            card = line.upper()
            if card.startswith("*SURFACE,NAME=WJCP_021_"):
                name = card.split("NAME=", 1)[1].split(",", 1)[0]
                surfaces[name] = []
            elif card.startswith("*NSET,NSET=WJCP_N_021_"):
                name = card.split("NSET=", 1)[1].split(",", 1)[0]
                node_sets[name] = set()
            continue
        fields = [field.strip() for field in line.split(",") if field.strip()]
        if card.startswith("*SURFACE,NAME=WJCP_021_"):
            surfaces[name].append((int(fields[0]), int(fields[1][1:]) - 1))
        elif card.startswith("*NSET,NSET=WJCP_N_021_"):
            node_sets[name].update(map(int, fields))
    for group in (PAIR_SLAVE, PAIR_MASTER):
        if group not in surfaces or not surfaces[group]:
            raise ValueError(f"missing source face group {group}")
    return surfaces, node_sets


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def norm(a):
    return math.sqrt(dot(a, a))


def mean(points):
    return tuple(math.fsum(point[i] for point in points) / len(points)
                 for i in range(3))


def centroid(nodes, face):
    return mean([nodes[nid] for nid in face[:3]])


def element_face(elements, eid, side):
    conn = elements[eid]
    return tuple(conn[index] for index in FACES[side])


def outward_face(nodes, elements, eid, side):
    """Return source face connectivity ordered with its parent tet outward."""
    face = element_face(elements, eid, side)
    tet_center = mean([nodes[nid] for nid in elements[eid][:4]])
    face_center = mean([nodes[nid] for nid in face[:3]])
    raw_normal = cross(sub(nodes[face[1]], nodes[face[0]]),
                       sub(nodes[face[2]], nodes[face[0]]))
    orientation = dot(raw_normal, sub(face_center, tet_center))
    if abs(orientation) < 1.0e-12:
        raise ValueError(f"degenerate source face {eid}/S{side+1}")
    if orientation < 0.0:
        # Reverse three corners and the corresponding quadratic edge nodes.
        face = (face[0], face[2], face[1], face[5], face[4], face[3])
    return face, orientation


def face_edges(face):
    return ((face[0], face[1]), (face[1], face[2]), (face[2], face[0]))


def face_curvature_offsets(nodes, face):
    triples = ((0, 1, 3), (1, 2, 4), (2, 0, 5))
    return [norm(sub(nodes[face[mid]], tuple(
        0.5 * (nodes[face[a]][i] + nodes[face[b]][i]) for i in range(3))))
        for a, b, mid in triples]


def closest_linear_triangle(point, a, b, c):
    """Closest point and barycentric weights on a straight triangle."""
    ab, ac, ap = sub(b, a), sub(c, a), sub(point, a)
    d1, d2 = dot(ab, ap), dot(ac, ap)
    if d1 <= 0.0 and d2 <= 0.0:
        return a, (1.0, 0.0, 0.0)
    bp = sub(point, b)
    d3, d4 = dot(ab, bp), dot(ac, bp)
    if d3 >= 0.0 and d4 <= d3:
        return b, (0.0, 1.0, 0.0)
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return add(a, tuple(v * x for x in ab)), (1.0 - v, v, 0.0)
    cp = sub(point, c)
    d5, d6 = dot(ab, cp), dot(ac, cp)
    if d6 >= 0.0 and d5 <= d6:
        return c, (0.0, 0.0, 1.0)
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return add(a, tuple(w * x for x in ac)), (1.0 - w, 0.0, w)
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return add(b, tuple(w * x for x in sub(c, b))), (0.0, 1.0 - w, w)
    inv = 1.0 / (va + vb + vc)
    v, w = vb * inv, vc * inv
    u = 1.0 - v - w
    q = tuple(u * a[i] + v * b[i] + w * c[i] for i in range(3))
    return q, (u, v, w)


class CurvedFace:
    """Quadratic TRIA6 interpolation and closest-point solve."""

    def __init__(self, source_id, side, node_ids, xyz, parent_direction):
        self.source_id = source_id
        self.side = side
        self.node_ids = node_ids
        self.xyz = np.asarray(xyz, dtype=float)
        self.parent_direction = np.asarray(parent_direction, dtype=float)

    def linear_projection(self, point):
        q, bary = closest_linear_triangle(tuple(point), *self.xyz[:3])
        return norm(sub(tuple(point), tuple(q))), bary

    def bezier_aabb_distance(self, point):
        # A quadratic Lagrange TRIA6 is the triangular Bernstein patch with
        # corner controls P1..P3 and edge controls 2*Pm-0.5*(Pi+Pj). The
        # surface is inside the convex hull of those six controls; distance to
        # their AABB is therefore a rigorous lower bound for global search.
        controls = np.asarray((
            self.xyz[0], self.xyz[1], self.xyz[2],
            2.0 * self.xyz[3] - 0.5 * (self.xyz[0] + self.xyz[1]),
            2.0 * self.xyz[4] - 0.5 * (self.xyz[1] + self.xyz[2]),
            2.0 * self.xyz[5] - 0.5 * (self.xyz[2] + self.xyz[0]),
        ))
        p = np.asarray(point, dtype=float)
        lower = controls.min(axis=0)
        upper = controls.max(axis=0)
        delta = np.maximum(np.maximum(lower - p, p - upper), 0.0)
        return float(np.linalg.norm(delta))

    def position(self, uv):
        u, v = uv
        l1 = 1.0 - u - v
        shape = np.asarray((l1 * (2.0 * l1 - 1.0),
                            u * (2.0 * u - 1.0),
                            v * (2.0 * v - 1.0),
                            4.0 * l1 * u, 4.0 * u * v, 4.0 * v * l1))
        return shape @ self.xyz

    def tangents(self, uv):
        u, v = uv
        l1 = 1.0 - u - v
        du = np.asarray((-(4.0 * l1 - 1.0), 4.0 * u - 1.0, 0.0,
                         4.0 * (l1 - u), 4.0 * v, -4.0 * v))
        dv = np.asarray((-(4.0 * l1 - 1.0), 0.0, 4.0 * v - 1.0,
                         -4.0 * u, 4.0 * u, 4.0 * (l1 - v)))
        return du @ self.xyz, dv @ self.xyz

    def normal_at_barycentric(self, barycentric):
        du, dv = self.tangents((barycentric[1], barycentric[2]))
        normal = np.cross(du, dv)
        jacobian = float(np.linalg.norm(normal))
        normal /= jacobian
        if float(normal @ self.parent_direction) < 0.0:
            normal *= -1.0
        return normal, jacobian

    def project(self, point, start_bary=None):
        point_np = np.asarray(point, dtype=float)
        if start_bary is None:
            _, start_bary = self.linear_projection(point)

        def objective(uv):
            delta = self.position(uv) - point_np
            return 0.5 * float(delta @ delta)

        def gradient(uv):
            delta = self.position(uv) - point_np
            du, dv = self.tangents(uv)
            return np.asarray((float(delta @ du), float(delta @ dv)))

        starts = (np.asarray((start_bary[1], start_bary[2])),
                  np.asarray((1.0 / 3.0, 1.0 / 3.0)),
                  np.asarray((0.0, 0.0)), np.asarray((1.0, 0.0)),
                  np.asarray((0.0, 1.0)), np.asarray((0.5, 0.0)),
                  np.asarray((0.5, 0.5)), np.asarray((0.0, 0.5)))
        results = []
        for start in starts:
            result = minimize(
                objective,
                start,
                method="SLSQP",
                jac=gradient,
                bounds=((0.0, 1.0), (0.0, 1.0)),
                constraints=({"type": "ineq", "fun": lambda uv: 1.0 - uv[0] - uv[1],
                             "jac": lambda uv: np.asarray((-1.0, -1.0))},),
                options={"ftol": 1.0e-14, "maxiter": 80},
            )
            uv = np.asarray(result.x, dtype=float)
            feasible = (np.all(np.isfinite(uv)) and uv[0] >= -1.0e-8 and
                         uv[1] >= -1.0e-8 and uv.sum() <= 1.0 + 1.0e-8)
            if feasible:
                results.append((objective(uv), uv, result.success, result.message))
        if not results:
            raise RuntimeError(f"TRIA6 projection failed on {self.source_id}/S{self.side+1}")
        _, uv, success, message = min(results, key=lambda item: item[0])
        if not success:
            # SLSQP can return a finite edge minimum with a line-search warning.
            # Require convergence for the winning candidate to keep this a
            # defensible independent gap oracle.
            converged = [item for item in results if item[2]]
            if converged:
                _, uv, success, message = min(converged, key=lambda item: item[0])
            else:
                raise RuntimeError(f"TRIA6 projection failed on {self.source_id}/S{self.side+1}: {message}")
        uv = np.maximum(uv, 0.0)
        if uv.sum() > 1.0:
            uv /= uv.sum()
        u, v = uv
        q = self.position((u, v))
        normal, _ = self.normal_at_barycentric((1.0 - u - v, u, v))
        delta = point_np - q
        return {
            "point": q,
            "normal": normal,
            "barycentric": np.asarray((1.0 - u - v, u, v)),
            "distance_mm": float(np.linalg.norm(delta)),
            "signed_gap_mm": float(delta @ normal),
        }


def components(face_rows):
    """Count edge-connected surface components."""
    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for index, row in enumerate(face_rows):
        face = row["node_ids"]
        for a, b in face_edges(face):
            edge_to_faces.setdefault(tuple(sorted((a, b))), []).append(index)
    adjacency = [set() for _ in face_rows]
    for touching in edge_to_faces.values():
        for i in touching:
            adjacency[i].update(j for j in touching if j != i)
    unseen = set(range(len(face_rows)))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            index = stack.pop()
            neighbors = adjacency[index] & unseen
            unseen.difference_update(neighbors)
            stack.extend(neighbors)
    return count


def node_components(element_connectivity):
    """Connected components for retained tets sharing at least one node."""
    node_to_elements: dict[int, list[int]] = {}
    for index, conn in enumerate(element_connectivity):
        for node in conn:
            node_to_elements.setdefault(node, []).append(index)
    adjacency = [set() for _ in element_connectivity]
    for touching in node_to_elements.values():
        for index in touching:
            adjacency[index].update(j for j in touching if j != index)
    unseen = set(range(len(element_connectivity)))
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            index = stack.pop()
            neighbors = adjacency[index] & unseen
            unseen.difference_update(neighbors)
            stack.extend(neighbors)
    return count


def json_float(value):
    return float(value)


def write_aster_mesh(nodes, elements, slave_rows, master_rows,
                     slave_tet_ids, master_tet_ids, slave_surface_nodes,
                     master_surface_nodes, slave_cut_nodes, master_cut_nodes):
    """Write crop immediately, before expensive curved projection audits."""
    retained_node_ids = sorted({node_id for eid in slave_tet_ids + master_tet_ids
                                for node_id in elements[eid]})
    node_label = {source_id: f"N{index:06d}"
                  for index, source_id in enumerate(retained_node_ids, 1)}
    # Code_Aster's IMPR_TABLE NOEUD column contains internal 1-based mesh
    # numbers for this fixture, even though .mail defines named nodes. Preserve
    # the exact COOR_3D order so post-run tables can be mapped back to labels.
    aster_node_number = {source_id: index
                         for index, source_id in enumerate(retained_node_ids, 1)}
    slave_volume_label = {source_id: f"VS{index:04d}"
                          for index, source_id in enumerate(slave_tet_ids, 1)}
    master_volume_label = {source_id: f"VM{index:04d}"
                           for index, source_id in enumerate(master_tet_ids, 1)}
    slave_face_label = {(row["source_element"], row["side"]): f"CS{index:04d}"
                        for index, row in enumerate(slave_rows, 1)}
    master_face_label = {(row["source_element"], row["side"]): f"CM{index:04d}"
                         for index, row in enumerate(master_rows, 1)}

    def group_lines(name, labels, max_per_line=8):
        result = [name]
        result.extend(" ".join(labels[i:i + max_per_line])
                      for i in range(0, len(labels), max_per_line))
        return "\n".join(result)

    lines = ["TITRE", "A09 pair021 quadratic curved contact crop; units mm, N, MPa",
             "FINSF", "COOR_3D"]
    for source_id in retained_node_ids:
        lines.append(f"{node_label[source_id]} " + " ".join(
            f"{v:.17g}" for v in nodes[source_id]))
    lines.extend(("FINSF", "TETRA10"))
    for source_id in slave_tet_ids:
        lines.append(slave_volume_label[source_id] + " " + " ".join(
            node_label[node] for node in elements[source_id]))
    for source_id in master_tet_ids:
        lines.append(master_volume_label[source_id] + " " + " ".join(
            node_label[node] for node in elements[source_id]))
    lines.extend(("FINSF", "TRIA6"))
    for row in slave_rows:
        key = (row["source_element"], row["side"])
        lines.append(slave_face_label[key] + " " + " ".join(
            node_label[node] for node in row["node_ids"]))
    for row in master_rows:
        key = (row["source_element"], row["side"])
        lines.append(master_face_label[key] + " " + " ".join(
            node_label[node] for node in row["node_ids"]))
    lines.append("FINSF")
    groups = (
        ("BOLT", [slave_volume_label[eid] for eid in slave_tet_ids]),
        ("WOOD", [master_volume_label[eid] for eid in master_tet_ids]),
        ("SLAVE", [slave_face_label[(row["source_element"], row["side"])] for row in slave_rows]),
        ("MASTER", [master_face_label[(row["source_element"], row["side"])] for row in master_rows]),
    )
    for group, labels in groups:
        lines.extend(("GROUP_MA", group_lines(group, labels), "FINSF"))
    for group, source_ids in (
        ("SNODE", sorted(slave_surface_nodes)),
        ("MNODE", sorted(master_surface_nodes)),
        ("SCUT", sorted(slave_cut_nodes)),
        ("MCUT", sorted(master_cut_nodes)),
    ):
        lines.extend(("GROUP_NO", group_lines(group, [node_label[nid] for nid in source_ids]), "FINSF"))
    lines.append("FIN")
    mail_path = OUT / "curved_contact.mail"
    mail_path.write_text("\n".join(lines) + "\n")
    return mail_path, node_label, aster_node_number


def generate():
    nodes, elements = read_abaqus_mesh(MESH_PATH)
    surfaces, recorded_sets = read_pair_fragment(CONTACT_PATH)
    seed = nodes[SEED_NODE]

    def source_face_rows(group):
        rows = []
        for eid, side in surfaces[group]:
            oriented, orientation = outward_face(nodes, elements, eid, side)
            center = centroid(nodes, oriented)
            conn = elements[eid]
            tet_center = mean([nodes[nid] for nid in conn[:4]])
            raw_n = cross(sub(nodes[oriented[1]], nodes[oriented[0]]),
                          sub(nodes[oriented[2]], nodes[oriented[0]]))
            outward = sub(center, tet_center)
            rows.append({"source_element": eid, "side": side,
                         "side_name": f"S{side + 1}", "node_ids": oriented,
                         "centroid": center, "orientation_dot": abs(orientation),
                         "raw_dot_outward": dot(raw_n, outward),
                         "parent_direction": outward})
        return rows

    full_slave = source_face_rows(PAIR_SLAVE)
    full_master = source_face_rows(PAIR_MASTER)
    for group, rows in ((PAIR_SLAVE, full_slave), (PAIR_MASTER, full_master)):
        union = {node_id for row in rows for node_id in row["node_ids"]}
        set_name = group.replace("WJCP_", "WJCP_N_", 1)
        if union != recorded_sets[set_name]:
            raise AssertionError(f"source {group} face membership differs from recorded {set_name}")

    slave_rows = [row for row in full_slave
                  if norm(sub(row["centroid"], seed)) <= SLAVE_RADIUS_MM]
    master_rows = [row for row in full_master
                   if norm(sub(row["centroid"], seed)) <= MASTER_RADIUS_MM]
    if not slave_rows or not master_rows:
        raise ValueError("crop selection returned an empty contact surface")

    slave_surface_nodes = {node_id for row in slave_rows for node_id in row["node_ids"]}
    master_surface_nodes = {node_id for row in master_rows for node_id in row["node_ids"]}
    slave_tet_ids = sorted({row["source_element"] for row in slave_rows})
    master_tet_ids = sorted({row["source_element"] for row in master_rows})
    if len(slave_tet_ids) != len(slave_rows) or len(master_tet_ids) != len(master_rows):
        raise AssertionError("source contact group repeats a parent volume cell")
    if set(slave_tet_ids) & set(master_tet_ids):
        raise AssertionError("source bolt and wood crop cells overlap")
    if len(slave_tet_ids) + len(master_tet_ids) > MAX_CROP_TETS:
        raise ValueError(f"crop has {len(slave_tet_ids)+len(master_tet_ids)} tets, cap is {MAX_CROP_TETS}")

    slave_volume_nodes = {node_id for eid in slave_tet_ids for node_id in elements[eid]}
    master_volume_nodes = {node_id for eid in master_tet_ids for node_id in elements[eid]}
    slave_cut_nodes = slave_volume_nodes - slave_surface_nodes
    master_cut_nodes = master_volume_nodes - master_surface_nodes
    if not slave_cut_nodes or not master_cut_nodes:
        raise ValueError("one side has no cut/control support nodes")
    if slave_cut_nodes & slave_surface_nodes or master_cut_nodes & master_surface_nodes:
        raise AssertionError("cut support shares nodes with its contact surface")
    if slave_volume_nodes & master_volume_nodes:
        raise AssertionError("retained body node sets overlap")
    if node_components([elements[eid] for eid in slave_tet_ids]) != 1:
        raise ValueError("retained slave volume cells are disconnected")
    if node_components([elements[eid] for eid in master_tet_ids]) != 1:
        raise ValueError("retained master volume cells are disconnected")
    if components(slave_rows) != 1 or components(master_rows) != 1:
        raise ValueError("selected contact surface patch is disconnected")

    # Keep the expensive projection oracle from blocking first parent review:
    # the immutable crop is emitted as soon as topology and supports pass.
    mail_path, node_label, aster_node_number = write_aster_mesh(
        nodes, elements, slave_rows, master_rows, slave_tet_ids, master_tet_ids,
        slave_surface_nodes, master_surface_nodes, slave_cut_nodes, master_cut_nodes)
    retained_node_ids = sorted(slave_volume_nodes | master_volume_nodes)

    # Ensure the independently closest projection of each retained slave node
    # remains on the retained master surface, not on a cut edge.
    master_projectors = []
    for row in full_master:
        face = row["node_ids"]
        parent_direction = row["parent_direction"]
        master_projectors.append(CurvedFace(
            (row["source_element"], row["side_name"]), row["side"], face,
            [nodes[nid] for nid in face], parent_direction))
    selected_master_face_keys = {(row["source_element"], row["side_name"])
                                 for row in master_rows}

    def project_point(point):
        candidates = [(projector.bezier_aabb_distance(point), projector)
                      for projector in master_projectors]
        candidates.sort(key=lambda item: item[0])
        best = None
        evaluated = 0
        for lower_bound, projector in candidates:
            if best is not None and lower_bound >= best[0]["distance_mm"]:
                break
            evaluated += 1
            try:
                projection = projector.project(point)
            except RuntimeError:
                # A distant face can have a poor local SLSQP direction even
                # though its conservative lower bound remains loose. Do not
                # silently skip a face that could beat the current minimum.
                if best is None or lower_bound < best[0]["distance_mm"]:
                    raise
                continue
            if best is None or projection["distance_mm"] < best[0]["distance_mm"]:
                best = (projection, projector)
        if best is None:
            raise RuntimeError(f"no converged source TRIA6 projection for point {point}")
        best[0]["source_master_faces_evaluated"] = evaluated
        best[0]["source_master_faces_total"] = len(candidates)
        return best

    slave_projectors = {}
    for row in slave_rows:
        face = row["node_ids"]
        slave_projectors.setdefault(row["source_element"], {})[row["side"]] = CurvedFace(
            (row["source_element"], row["side_name"]), row["side"], face,
            [nodes[nid] for nid in face], row["parent_direction"])

    local_barycentric = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                         (0.0, 0.0, 1.0), (0.5, 0.5, 0.0),
                         (0.0, 0.5, 0.5), (0.5, 0.0, 0.5))
    slave_normal_accumulators = {node_id: np.zeros(3) for node_id in slave_surface_nodes}
    for row in slave_rows:
        projector = slave_projectors[row["source_element"]][row["side"]]
        for local_index, node_id in enumerate(row["node_ids"]):
            normal, jacobian = projector.normal_at_barycentric(local_barycentric[local_index])
            slave_normal_accumulators[node_id] += normal * jacobian
    slave_outward_normals = {}
    for node_id, accumulated in slave_normal_accumulators.items():
        length = float(np.linalg.norm(accumulated))
        if length <= 1.0e-14:
            raise ValueError(f"slave outward nodal normal cancels at source node {node_id}")
        slave_outward_normals[node_id] = accumulated / length

    initial_projection = {}
    for node_id in sorted(slave_surface_nodes):
        projection, projector = project_point(nodes[node_id])
        if (projector.source_id[0], projector.source_id[1]) not in selected_master_face_keys:
            raise ValueError(f"slave node {node_id} projects outside retained master patch: {projector.source_id}")
        if projection["signed_gap_mm"] <= 0.0:
            raise ValueError(f"source slave node {node_id} starts penetrated: {projection['signed_gap_mm']} mm")
        initial_projection[node_id] = (projection, projector)

    seed_projection, seed_projector = project_point(nodes[SEED_NODE])
    close = -seed_projection["normal"]
    close /= np.linalg.norm(close)

    # The 0.50 mm approach state must remain separated for every slave node;
    # obtain it by exact TRIA6 projection, not planar-triangle extrapolation.
    motion_checks = {}
    for displacement in (-0.20, -0.10, 0.0, 0.50):
        per_node = []
        for node_id in sorted(slave_surface_nodes):
            moved = np.asarray(nodes[node_id]) + displacement * close
            projection, projector = project_point(moved)
            per_node.append({"source_slave_node": node_id,
                             "source_master_element": projector.source_id[0],
                             "source_master_side": projector.source_id[1],
                             "gap_mm": projection["signed_gap_mm"]})
        gaps = [row["gap_mm"] for row in per_node]
        motion_checks[f"{displacement:+.2f}"] = {
            "control_displacement_mm": displacement,
            "minimum_gap_mm": min(gaps),
            "maximum_gap_mm": max(gaps),
            "all_nodes_open": min(gaps) > 0.0,
            "nodes": per_node,
        }
    if not motion_checks["+0.50"]["all_nodes_open"]:
        raise ValueError("frozen 0.50 mm approach state is not open over the entire patch")
    if motion_checks["+0.50"]["minimum_gap_mm"] <= 0.02:
        raise ValueError("0.50 mm approach state lacks the frozen 0.02 mm opening margin")

    seed_gap = seed_projection["signed_gap_mm"]
    projected_directional_gaps = []
    for node_id, (projection, _) in initial_projection.items():
        n = projection["normal"]
        closing_cosine = -float(n @ close)
        if closing_cosine > 0.0:
            projected_directional_gaps.append(projection["signed_gap_mm"] / closing_cosine)
    activation_estimate = min(projected_directional_gaps)

    source_patch_gaps = [projection["signed_gap_mm"]
                         for projection, _ in initial_projection.values()]
    normal_pair_dots = {
        node_id: float(slave_outward_normals[node_id] @ projection["normal"])
        for node_id, (projection, _) in initial_projection.items()
    }
    all_offsets = [offset for row in slave_rows + master_rows
                   for offset in face_curvature_offsets(nodes, row["node_ids"])]
    meaningful_offsets = [offset for offset in all_offsets if offset > 1.0e-7]
    face_orientation_audit = {
        "slave_min_raw_normal_dot_parent_outward": min(row["raw_dot_outward"] for row in slave_rows),
        "master_min_raw_normal_dot_parent_outward": min(row["raw_dot_outward"] for row in master_rows),
        "output_surface_order_is_outward": True,
    }
    projection_records = []
    for node_id, (projection, projector) in sorted(initial_projection.items()):
        projection_records.append({
            "source_slave_node": node_id,
            "output_slave_node": node_label[node_id],
            "aster_node_number": aster_node_number[node_id],
            "source_master_element": projector.source_id[0],
            "source_master_side": projector.source_id[1],
            "barycentric_on_curved_tria6": [json_float(x) for x in projection["barycentric"]],
            "initial_signed_gap_mm": projection["signed_gap_mm"],
            "euclidean_distance_mm": projection["distance_mm"],
            "source_master_faces_evaluated": projection["source_master_faces_evaluated"],
            "source_master_faces_total": projection["source_master_faces_total"],
            "master_outward_normal": [json_float(x) for x in projection["normal"]],
            "slave_outward_normal": [json_float(x) for x in slave_outward_normals[node_id]],
            "slave_master_outward_normal_dot": normal_pair_dots[node_id],
            "closing_direction_normal_cosine": float(-projection["normal"] @ close),
        })

    manifest = {
        "purpose": "Representative actual quadratic curved-contact method screen for A09 pair 021; no candidate acceptance or property calibration.",
        "source": {
            "mesh": str(MESH_PATH.relative_to(ROOT)),
            "contact_fragment": str(CONTACT_PATH.relative_to(ROOT)),
            "sha256": {"mesh.inp": sha256(MESH_PATH), "contact-fragment.inc": sha256(CONTACT_PATH)},
            "generator_sha256": sha256(Path(__file__)),
            "crop_mail_sha256": sha256(mail_path),
            "topology_mapping": "fea/code_aster_trial/a09_topology.py:FACES; full source pair node memberships revalidated before crop",
            "pair": {"slave": PAIR_SLAVE, "master": PAIR_MASTER},
            "geometry_unchanged": True,
        },
        "crop_rule": {
            "seed_source_slave_node": SEED_NODE,
            "seed_xyz_mm": list(seed),
            "slave_face_corner_centroid_radius_mm": SLAVE_RADIUS_MM,
            "master_face_corner_centroid_radius_mm": MASTER_RADIUS_MM,
            "one_source_C3D10_cell_per_selected_TRIA6_face": True,
            "retained_cell_cap": MAX_CROP_TETS,
            "slave_source_faces": len(slave_rows),
            "master_source_faces": len(master_rows),
            "slave_retained_c3d10": len(slave_tet_ids),
            "master_retained_c3d10": len(master_tet_ids),
            "total_retained_c3d10": len(slave_tet_ids) + len(master_tet_ids),
            "unique_crop_nodes": len(retained_node_ids),
            "slave_contact_nodes": len(slave_surface_nodes),
            "master_contact_nodes": len(master_surface_nodes),
            "slave_cut_control_nodes": len(slave_cut_nodes),
            "master_cut_support_nodes": len(master_cut_nodes),
            "retained_slave_volume_node_connected_components": 1,
            "retained_master_volume_node_connected_components": 1,
            "slave_contact_face_edge_connected_components": 1,
            "master_contact_face_edge_connected_components": 1,
            "cut_groups_are_disjoint_from_contact_nodes": True,
            "bolt_wood_mesh_node_sets_disjoint": True,
        },
        "node_groups": {
            "SNODE": [{"source_node": nid, "output_node": node_label[nid],
                        "aster_node_number": aster_node_number[nid]}
                      for nid in sorted(slave_surface_nodes)],
            "MNODE": [{"source_node": nid, "output_node": node_label[nid],
                        "aster_node_number": aster_node_number[nid]}
                      for nid in sorted(master_surface_nodes)],
            "SCUT": [{"source_node": nid, "output_node": node_label[nid],
                      "aster_node_number": aster_node_number[nid]}
                     for nid in sorted(slave_cut_nodes)],
            "MCUT": [{"source_node": nid, "output_node": node_label[nid],
                      "aster_node_number": aster_node_number[nid]}
                     for nid in sorted(master_cut_nodes)],
        },
        "quadratic_curvature": {
            "slave_tria6_count": len(slave_rows),
            "master_tria6_count": len(master_rows),
            "maximum_midside_offset_from_corner_chord_mm": max(all_offsets),
            "minimum_midside_offset_above_roundoff_floor_mm": min(meaningful_offsets),
            "roundoff_floor_mm": 1.0e-7,
            "edge_midside_offsets_above_roundoff_floor": len(meaningful_offsets),
            "edge_midside_offset_count": len(all_offsets),
            "interpretation": "The retained contact faces are genuinely curved quadratic TRIA6 geometry; the midpoint offsets are geometric diagnostics, not contact error estimates.",
        },
        "orientation": face_orientation_audit,
        "initial_gap": {
        "independent_method": "Global nearest-point projection over every source WJCP_021_M quadratic isoparametric TRIA6. Each surface is represented by its six quadratic Bezier control points; point-to-control-AABB distance is a rigorous lower bound, so faces that cannot beat the current minimum are pruned. Candidate faces use constrained SLSQP from the corner-triangle projection and simplex landmarks. Signed gap is (slave point - projected master point) dot the outward master unit normal.",
            "slave_node_count": len(projection_records),
            "minimum_mm": min(source_patch_gaps),
            "maximum_mm": max(source_patch_gaps),
            "spread_mm": max(source_patch_gaps) - min(source_patch_gaps),
            "seed_node_mm": seed_gap,
            "seed_nearest_master_element": seed_projector.source_id[0],
            "seed_nearest_master_side": seed_projector.source_id[1],
            "seed_master_outward_normal": [json_float(x) for x in seed_projection["normal"]],
            "closing_direction_unit_vector": [json_float(x) for x in close],
            "closing_direction_definition": "negative of exact curved master outward normal at the nearest projection of source slave node 61143",
            "slave_vs_master_outward_normal_dot": {
                "minimum": min(normal_pair_dots.values()),
                "maximum": max(normal_pair_dots.values()),
                "mean": math.fsum(normal_pair_dots.values()) / len(normal_pair_dots),
                "fraction_negative": sum(value < 0.0 for value in normal_pair_dots.values()) / len(normal_pair_dots),
                "interpretation": "Both surfaces are individually oriented out of their parent solids; negative pairwise dots mean their outward normals oppose at the slave-node projection.",
            },
            "minimum_barycentric_coordinate_over_all_projections": min(
                min(record["barycentric_on_curved_tria6"]) for record in projection_records),
            "every_source_nearest_projection_retained_in_crop": True,
            "nodes": projection_records,
        },
        "open_motion_geometry_oracle": {
            "method": "Exact curved TRIA6 projection of every slave contact node after the prescribed rigid translation; both bodies are unloaded while all gap values are positive.",
            "states": motion_checks,
        },
        "frozen_motion": {
            "time_mm_control_displacement": [{"time": t, "control_displacement_mm": d}
                                                for t, d in HISTORY],
            "estimated_first_contact_displacement_mm": activation_estimate,
            "basis": "Minimum source signed gap divided by positive local directional normal cosine; used only to select a small method-screening approach/closure history.",
            "opening_and_separation_states": ["-0.20", "-0.10", "+0.00", "+0.50"],
            "contact_loading_states": ["+0.60", "+0.65"],
            "unloading_reopening_states": ["+0.60", "+0.50", "+0.00", "-0.10"],
            "reclosure_state": "+0.60",
        },
        "frozen_screen_thresholds": {
            "open_state_maximum_absolute_gap_error_mm": 0.02,
            "open_state_minimum_local_gap_mm": 0.0,
            "open_state_maximum_sum_of_local_contact_force_norms_n": 0.05,
            "active_node_maximum_absolute_gap_mm": 0.01,
            "all_slave_nodes_maximum_penetration_mm": 0.01,
            "compression_contact_resultant_minimum_n": 0.05,
            "signed_resultant_contact_force_projection_along_closing_direction": "greater than 0.05 N at compression; report full RN vector and local RN values",
            "prescribed_slave_cut_reaction_consistency": "norm(sum(RN) - sum(FORC_NODA at SCUT)) <= force-balance tolerance",
            "contact_resultant_vs_independent_master_cut_reaction_vector_n": "norm(RN + sum(FORC_NODA at MCUT)) <= max(0.05 N, 0.001 * max(norm(RN), norm(cut reaction)))",
            "force_claim_boundary": "The displacement-controlled load is a solved response, not an analytical pressure oracle. RN-to-cut balance checks action/reaction consistency only; they do not establish pressure accuracy or joint resistance.",
            "absolute_nonlinear_residual_n": 1.0e-9,
            "scope": "Screening proposal frozen before native execution. A fail does not establish broader Code_Aster failure; a pass does not qualify another mesh, interface, joint, or candidate model.",
        },
        "native_execution": "Not run by the generator author; parent owns readiness, frozen inputs and serialized native execution.",
        "software": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "scipy": __import__("scipy").__version__},
    }
    oracle_path = OUT / "geometry-oracle.json"
    oracle_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output_mail": str(mail_path.relative_to(ROOT)),
        "output_mail_sha256": sha256(mail_path),
        "output_geometry_oracle": str(oracle_path.relative_to(ROOT)),
        "source_sha256": manifest["source"]["sha256"],
        "crop": manifest["crop_rule"],
        "quadratic_curvature": manifest["quadratic_curvature"],
        "initial_gap_mm": {key: manifest["initial_gap"][key]
                           for key in ("minimum_mm", "maximum_mm", "spread_mm", "seed_node_mm",
                                       "seed_nearest_master_element", "seed_nearest_master_side")},
        "closing_direction": manifest["initial_gap"]["closing_direction_unit_vector"],
        "open_motion_geometry_oracle": {key: {k: v for k, v in check.items() if k != "nodes"}
                                         for key, check in motion_checks.items()},
        "estimated_first_contact_displacement_mm": activation_estimate,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    generate()
