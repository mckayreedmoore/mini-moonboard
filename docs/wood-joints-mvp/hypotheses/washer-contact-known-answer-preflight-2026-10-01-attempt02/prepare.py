#!/usr/bin/env python3
"""Prepare a corrected offline CalculiX 2.23 annulus contact-method job.

This file creates the contact mesh, deck, analytic contract, source pins, and
preparation receipt. It never starts a solver or Docker container.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import tarfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PROFILE = ROOT / "fea/calculix_223/solver-profile.json"
MANUAL = ROOT / "fea/generated/ccx_2.23.pdf"
SOURCE_ARCHIVE = Path("/tmp/ccx_2.23.src.tar.bz2")
HTML_ARCHIVE = Path("/tmp/ccx_2.23.htm.tar.bz2")
CONTACT_HISTORY = ROOT / (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "contact-penalty-touch-work-known-answer-attempt01")
CONTACT_OUTPUT = CONTACT_HISTORY / "pair_output.py"
PROFILE_SHA256 = "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c"
MANUAL_SHA256 = "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"
SOURCE_ARCHIVE_SHA256 = "9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7"
HTML_ARCHIVE_SHA256 = "ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736"
SOURCE_MEMBERS = {
    "CalculiX/ccx_2.23/src/contactprints.f":
        "88a2fc1a15caa2ab9b28de6ff6c4566f34e7f24c9db5c2c3ee4ef333439c717d",
    "CalculiX/ccx_2.23/src/dloads.f":
        "10b893e457e390e7b23e4592e6b96c55ba4f222d6cc044347185a94f7d19de58",
    "CalculiX/ccx_2.23/src/printoutcontact.f":
        "4e1f5452d5fd268d7e4f1ab702de4804bb8f34a429b5e2c14ff9af3df9a9a055",
    "CalculiX/ccx_2.23/src/statics.f":
        "d5add12845e7dc6e7a19043fa6114012b9f36ed0723590308d60f4b09eee4599",
    "CalculiX/ccx_2.23/src/e_c3d_rhs.f":
        "d44769de99dddddd89694022ea56a26f3a7a9477c2b63de3dab71daabb1ce4e6",
    "CalculiX/ccx_2.23/src/gauss.f":
        "aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2",
    "CalculiX/ccx_2.23/src/shape6tri.f":
        "64f4596c6dc6ee41baf4cc514947c41348a43c0c6fd40763af07802cad23c2cc",
}
HTML_MEMBERS = {
    "./CalculiX/ccx_2.23/doc/ccx/node34.html":
        "C3D10; §6.2.7, 10-node quadratic tetrahedron",
    "./CalculiX/ccx_2.23/doc/ccx/node147.html":
        "face-to-face penalty contact; §6.7.7",
    "./CalculiX/ccx_2.23/doc/ccx/node249.html":
        "*CONTACT PAIR; §7.22",
    "./CalculiX/ccx_2.23/doc/ccx/node250.html":
        "*CONTACT PRINT; §7.23",
    "./CalculiX/ccx_2.23/doc/ccx/node212.html":
        "RF is total external force, including nodal and distributed loads",
    "./CalculiX/ccx_2.23/doc/ccx/node227.html":
        "*BOUNDARY model definition card and translational DOF definitions",
    "./CalculiX/ccx_2.23/doc/ccx/node272.html":
        "*DSLOAD pressure on element-face surface; §7.45",
    "./CalculiX/ccx_2.23/doc/ccx/node356.html":
        "*SURFACE; §7.129; C3D10 face labels",
    "./CalculiX/ccx_2.23/doc/ccx/node357.html":
        "*SURFACE BEHAVIOR linear pressure-overclosure; §7.130",
    "./CalculiX/ccx_2.23/doc/ccx/node358.html":
        "*SURFACE INTERACTION; §7.131",
}

# Diagnostic-only geometry and material assumptions, not product specifications.
R_IN = 2.5
R_OUT = 5.5
HEIGHT = 1.5
N_RADIAL = 2
N_ANGLE = 16
N_Z = 2
STEEL_E = 200000.0  # MPa, hypothetical elastic value for the software oracle only
SUPPORT_E = 10000.0  # MPa, hypothetical isotropic receiver value; not a wood property
NU = 0.0
EPSILON = 1.0e-4
CONTACT_K = 100000.0  # N/mm^3, numerical penalty used only in the method fixture
PATCH_PRESSURE = 2.0  # MPa, diagnostic traction magnitude
PATCH_SECTORS = 4  # 90 degrees of the 16-sector polygonal annulus
SUPPORT_THICKNESS = 3.0

# Abaqus/CalculiX C3D10 face numbering from the pinned manual §7.129 *SURFACE.
# Tuple entries are zero-based local corner-node indexes.
FACE_LABELS = {
    (0, 1, 2): "S1",  # face 1: local nodes 1-2-3
    (0, 3, 1): "S2",  # face 2: local nodes 1-4-2
    (1, 3, 2): "S3",  # face 3: local nodes 2-4-3
    (2, 3, 0): "S4",  # face 4: local nodes 3-4-1
}
FACE_LOCAL = {
    "S1": (0, 1, 2),
    "S2": (0, 3, 1),
    "S3": (1, 3, 2),
    "S4": (2, 3, 0),
}
EDGE_MID_LOCAL = {
    (0, 1): 4, (1, 2): 5, (0, 2): 6,
    (0, 3): 7, (1, 3): 8, (2, 3): 9,
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def json_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def close(a: float, b: float, tolerance: float = 1e-10) -> bool:
    return abs(a - b) <= tolerance * max(1.0, abs(a), abs(b))


def vec_sub(a, b):
    return tuple(x - y for x, y in zip(a, b))


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def norm(v):
    return math.sqrt(dot(v, v))


def signed_tet_volume(points) -> float:
    a, b, c, d = points
    return dot(vec_sub(b, a), cross(vec_sub(c, a), vec_sub(d, a))) / 6.0


@dataclass
class Mesh:
    nodes: dict[int, tuple[float, float, float]]
    elements: list[tuple[int, tuple[int, ...]]]
    boundary: dict[str, list[tuple[int, str, tuple[int, int, int]]]]
    volume_mm3: float
    top_area_mm2: float
    bottom_area_mm2: float
    top_faces_by_sector: dict[int, list[tuple[int, str, tuple[int, int, int]]]]
    radial_count: int
    angle_count: int
    z_count: int
    z0: float
    z1: float


def make_annulus(*, r_in: float, r_out: float, z0: float, z1: float,
                 n_radial: int, n_angle: int, n_z: int,
                 node_offset: int = 0, element_offset: int = 0) -> Mesh:
    """Create a conforming straight-sided annular prism mesh with C3D10 tets."""
    if not (0.0 < r_in < r_out and z1 > z0 and n_radial >= 2
            and n_angle >= 8 and n_z >= 2):
        raise ValueError("annulus dimensions/resolution are outside the fixture contract")
    xyz: dict[int, tuple[float, float, float]] = {}
    grid: dict[tuple[int, int, int], int] = {}
    next_node = node_offset + 1
    for iz in range(n_z + 1):
        z = z0 + (z1 - z0) * iz / n_z
        for ir in range(n_radial + 1):
            radius = r_in + (r_out - r_in) * ir / n_radial
            for it in range(n_angle):
                theta = 2.0 * math.pi * it / n_angle
                grid[(ir, it, iz)] = next_node
                xyz[next_node] = (radius * math.cos(theta),
                                  radius * math.sin(theta), z)
                next_node += 1

    # A globally consistent six-tetrahedron Freudenthal subdivision of each
    # structured prism cell. Shared hexahedral faces therefore share diagonals.
    tetra4: list[tuple[int, tuple[int, int, int, int], tuple[int, int, int]]] = []
    next_element = element_offset + 1
    cube_tets = (
        (0, 1, 3, 7), (0, 3, 2, 7), (0, 2, 6, 7),
        (0, 6, 4, 7), (0, 4, 5, 7), (0, 5, 1, 7),
    )
    for iz in range(n_z):
        for ir in range(n_radial):
            for it in range(n_angle):
                jt = (it + 1) % n_angle
                # Cube corner order uses radial, angular, axial bit coordinates.
                corners = (
                    grid[(ir, it, iz)], grid[(ir + 1, it, iz)],
                    grid[(ir, jt, iz)], grid[(ir + 1, jt, iz)],
                    grid[(ir, it, iz + 1)], grid[(ir + 1, it, iz + 1)],
                    grid[(ir, jt, iz + 1)], grid[(ir + 1, jt, iz + 1)],
                )
                for pattern in cube_tets:
                    tet = [corners[index] for index in pattern]
                    vol = signed_tet_volume([xyz[node] for node in tet])
                    if abs(vol) <= 1e-12:
                        raise ValueError("degenerate tetrahedron in structured annulus")
                    if vol < 0:
                        tet[0], tet[1] = tet[1], tet[0]
                        vol = -vol
                    tetra4.append((next_element, tuple(tet), (ir, it, iz)))
                    next_element += 1

    # C3D10 midside nodes are shared by edge identity; all are straight-edge
    # midpoints, so each quadratic boundary face has a planar geometry map.
    edges: dict[tuple[int, int], int] = {}
    elements10 = []
    for eid, (a, b, c, d), _cell in tetra4:
        mids = []
        for p, q in ((a, b), (b, c), (c, a), (a, d), (b, d), (c, d)):
            key = tuple(sorted((p, q)))
            if key not in edges:
                edges[key] = next_node
                pa, pb = xyz[p], xyz[q]
                xyz[next_node] = tuple((x + y) / 2.0 for x, y in zip(pa, pb))
                next_node += 1
            mids.append(edges[key])
        elements10.append((eid, (a, b, c, d, *mids)))

    face_counts: dict[tuple[int, int, int], list[tuple[int, str, tuple[int, int, int], tuple[int, int, int]]]] = {}
    sector_top: dict[int, list[tuple[int, str, tuple[int, int, int]]]] = {
        it: [] for it in range(n_angle)
    }
    cells_by_element = {eid: cell for eid, _tet, cell in tetra4}
    for eid, conn in elements10:
        corner_ids = conn[:4]
        for label, local in FACE_LOCAL.items():
            face_nodes = tuple(corner_ids[i] for i in local)
            key = tuple(sorted(face_nodes))
            face_counts.setdefault(key, []).append((eid, label, face_nodes, local))

    def all_at_z(face, z):
        return all(close(xyz[node][2], z, 1e-11) for node in face)

    boundary: dict[str, list[tuple[int, str, tuple[int, int, int]]]] = {
        "top": [], "bottom": [], "exterior": []
    }
    for occ in face_counts.values():
        if len(occ) != 1:
            continue
        eid, label, face_nodes, _local = occ[0]
        boundary["exterior"].append((eid, label, face_nodes))
        if all_at_z(face_nodes, z1):
            row = (eid, label, face_nodes)
            boundary["top"].append(row)
            _ir, it, iz = cells_by_element[eid]
            if iz == n_z - 1:
                sector_top[it].append(row)
        elif all_at_z(face_nodes, z0):
            boundary["bottom"].append((eid, label, face_nodes))

    def area_and_centroid(faces):
        area_sum = 0.0
        first = [0.0, 0.0, 0.0]
        for _eid, _label, nodes in faces:
            p0, p1, p2 = (xyz[n] for n in nodes)
            area = 0.5 * norm(cross(vec_sub(p1, p0), vec_sub(p2, p0)))
            centroid = tuple((a + b + c) / 3.0 for a, b, c in zip(p0, p1, p2))
            area_sum += area
            for k in range(3):
                first[k] += area * centroid[k]
        if area_sum == 0.0:
            raise ValueError("annulus has no boundary area")
        return area_sum, tuple(value / area_sum for value in first)

    top_area, _ = area_and_centroid(boundary["top"])
    bottom_area, _ = area_and_centroid(boundary["bottom"])
    volume = sum(signed_tet_volume([xyz[n] for n in tet])
                 for _eid, tet, _cell in tetra4)
    if volume <= 0 or not close(top_area, bottom_area):
        raise ValueError("annulus volume or opposed planar face areas are invalid")
    return Mesh(xyz, elements10, boundary, volume, top_area, bottom_area,
                sector_top, n_radial, n_angle, n_z, z0, z1)


def c3d10_face_area_centroid(mesh: Mesh, faces):
    """Integrate a planar TRI6 surface using its straight-sided exact geometry."""
    area = 0.0
    first = [0.0, 0.0, 0.0]
    for _eid, _label, corner_nodes in faces:
        p0, p1, p2 = (mesh.nodes[n] for n in corner_nodes)
        da = 0.5 * norm(cross(vec_sub(p1, p0), vec_sub(p2, p0)))
        center = tuple((a + b + c) / 3.0 for a, b, c in zip(p0, p1, p2))
        area += da
        for k in range(3):
            first[k] += da * center[k]
    if area <= 0:
        raise ValueError("empty finite loaded patch")
    return area, tuple(value / area for value in first)


def write_surface_lines(faces):
    return "".join(f"{eid},{label}\n" for eid, label, _nodes in sorted(faces))


def node_set_lines(name: str, ids: list[int]) -> str:
    ids = sorted(set(ids))
    lines = [f"*NSET,NSET={name}\n"]
    for start in range(0, len(ids), 16):
        lines.append(",".join(str(item) for item in ids[start:start + 16]) + "\n")
    return "".join(lines)


def boundary_node_ids(mesh: Mesh) -> dict[str, list[int]]:
    top = sorted({node for face in mesh.boundary["top"] for node in face_nodes6(mesh, face)})
    bottom = sorted({node for face in mesh.boundary["bottom"] for node in face_nodes6(mesh, face)})
    exterior = sorted({node for face in mesh.boundary["exterior"] for node in face_nodes6(mesh, face)})
    return {"top": top, "bottom": bottom, "boundary": exterior}


def face_nodes6(mesh: Mesh, face):
    eid, label, _corner_nodes = face
    conn = dict(mesh.elements)[eid]
    local = FACE_LOCAL[label]
    out = [conn[index] for index in local]
    for i, j in ((local[0], local[1]), (local[1], local[2]), (local[2], local[0])):
        out.append(conn[EDGE_MID_LOCAL[tuple(sorted((i, j)))]] )
    return out


def write_nodes_elements(meshes: list[tuple[str, Mesh]]) -> tuple[str, dict, dict]:
    node_lines = ["*NODE\n"]
    element_lines = []
    element_sets = []
    all_nodes = []
    metadata = {}
    for name, mesh in meshes:
        for node_id, (x, y, z) in sorted(mesh.nodes.items()):
            node_lines.append(f"{node_id},{x:.12g},{y:.12g},{z:.12g}\n")
            all_nodes.append(node_id)
        element_lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={name}\n")
        for element_id, conn in mesh.elements:
            element_lines.append(f"{element_id}," + ",".join(str(n) for n in conn) + "\n")
        metadata[name] = {
            "node_ids": sorted(mesh.nodes),
            "element_ids": [element_id for element_id, _ in mesh.elements],
            "top_area_mm2": mesh.top_area_mm2,
            "bottom_area_mm2": mesh.bottom_area_mm2,
            "volume_mm3": mesh.volume_mm3,
            "top_faces": mesh.boundary["top"],
            "bottom_faces": mesh.boundary["bottom"],
        }
        element_sets.append(name)
    return "".join(node_lines + element_lines), metadata, {"all": sorted(all_nodes)}


def boundary_rows(mesh: Mesh, direction: str) -> list[tuple[int, str, tuple[int, int, int]]]:
    return mesh.boundary[direction]


def job_affine() -> tuple[str, dict]:
    mesh = make_annulus(r_in=R_IN, r_out=R_OUT, z0=0.0, z1=HEIGHT,
                        n_radial=N_RADIAL, n_angle=N_ANGLE, n_z=N_Z)
    boundary = boundary_node_ids(mesh)
    top_ids, bottom_ids = boundary["top"], boundary["bottom"]
    node_cards = ["*BOUNDARY\n"]
    boundary_set = set(boundary["boundary"])
    for node in sorted(boundary_set):
        _x, _y, z = mesh.nodes[node]
        node_cards.append(f"{node},1,1,0.0\n{node},2,2,0.0\n")
        node_cards.append(f"{node},3,3,{-EPSILON * z:.12g}\n")
    deck = (
        "*HEADING\n"
        "Diagnostic affine C3D10 annulus patch; no washer/wood/product claim\n"
        "** Units: mm, N, MPa. Isotropic linear elastic with hypothetical nu=0.\n"
        "** The exterior boundary is prescribed to the exact homogeneous field;\n"
        "** interior nodes remain free. No contact, product stress, or capacity.\n"
        + write_nodes_elements([("ANNULUS", mesh)])[0]
        + node_set_lines("ALLNODES", sorted(mesh.nodes))
        + node_set_lines("TOP_FACE", top_ids)
        + node_set_lines("BOTTOM_FACE", bottom_ids)
        + "*MATERIAL,NAME=DIAGNOSTIC_ELASTIC\n*ELASTIC\n"
        + f"{STEEL_E:.12g},{NU:.12g}\n"
        + "*SOLID SECTION,ELSET=ANNULUS,MATERIAL=DIAGNOSTIC_ELASTIC\n"
        + node_cards[0]
        + "".join(node_cards[1:])
        + "*STEP\n*STATIC,DIRECT\n1.0,1.0\n"
        + "*NODE PRINT,NSET=ALLNODES,FREQUENCY=1\nU,RF\n"
        + "*EL PRINT,ELSET=ANNULUS,FREQUENCY=1\nS\n"
        + "*EL PRINT,ELSET=ANNULUS,TOTALS=ONLY,FREQUENCY=1\nELSE\n"
        + "*END STEP\n"
    )
    area = mesh.top_area_mm2
    volume = mesh.volume_mm3
    force = -STEEL_E * EPSILON * area
    energy = 0.5 * STEEL_E * EPSILON ** 2 * volume
    expected = {
        "job": "affine-annulus",
        "final_time": 1.0,
        "model_coordinates_json": "model_coordinates.json",
        "top_node_ids": top_ids,
        "bottom_node_ids": bottom_ids,
        "boundary_node_ids": sorted(boundary_set),
        "scope": "C3D10 elastic patch and actual FE area/volume only",
        "RF_semantics": "The pinned manual defines RF as total external nodal force; this job has no nodal or distributed loads, so the reported exterior RF is the displacement-constraint reaction.",
        "mesh": {"nodes": len(mesh.nodes), "elements": len(mesh.elements),
                 "node_ids": sorted(mesh.nodes),
                 "element_ids": [eid for eid, _conn in mesh.elements],
                 "tetrahedra_per_hex": 6,
                 "integration_points_per_c3d10": 4,
                 "corner_tet_volume_sum_mm3": volume, "top_FE_area_mm2": area,
                 "bottom_FE_area_mm2": mesh.bottom_area_mm2,
                 "ideal_circle_area_mm2": math.pi * (R_OUT ** 2 - R_IN ** 2),
                 "ideal_circle_comparison_is_not_oracle": True},
        "material_assumption": {"isotropic_E_MPa": STEEL_E, "poisson": NU,
                                "role": "hypothetical linear-elastic diagnostic only"},
        "kinematics": {"epsilon_zz": -EPSILON, "u_x": 0.0, "u_y": 0.0,
                       "u_z_at_top_mm": -EPSILON * HEIGHT},
        "oracle": {"sigma_xx_MPa": 0.0, "sigma_yy_MPa": 0.0,
                   "sigma_zz_MPa": -STEEL_E * EPSILON,
                   "shear_MPa": 0.0,
                   "top_RF3_N": force, "bottom_RF3_N": -force,
                   "top_RF_wrench_N_Nmm": [0.0, 0.0, force, 0.0, 0.0, 0.0],
                   "bottom_RF_wrench_N_Nmm": [0.0, 0.0, -force, 0.0, 0.0, 0.0],
                   "total_elastic_energy_N_mm": energy,
                   "all_boundary_wrench_sum_N_Nmm": [0.0] * 6,
                   "interior_nodes_free": sorted(set(mesh.nodes) - boundary_set)},
        "predeclared_tolerances": {
            "stress_absolute_MPa": 5e-5,
            "stress_relative": 1e-5,
            "displacement_absolute_mm": 1e-8,
            "force_absolute_N": 1e-3,
            "force_relative": 1e-5,
            "moment_absolute_N_mm": 0.02,
            "moment_relative": 1e-5,
            "energy_absolute_N_mm": 1e-9,
            "energy_relative": 1e-5,
            "global_force_absolute_N": 0.02,
            "global_moment_absolute_N_mm": 0.05,
        },
    }
    return deck, expected, mesh.nodes


def merge_mesh_nodes(*meshes: Mesh) -> dict[int, tuple[float, float, float]]:
    out = {}
    for mesh in meshes:
        overlap = set(out).intersection(mesh.nodes)
        if overlap:
            raise ValueError("separate contact bodies must use distinct node identities")
        out.update(mesh.nodes)
    return out


def face_wrench(area: float, centroid, pressure: float):
    # Positive CalculiX pressure P acts inward on the outward-facing top face.
    force = (0.0, 0.0, -pressure * area)
    moment = cross(centroid, force)
    return force, moment


def job_contact() -> tuple[str, dict]:
    upper = make_annulus(r_in=R_IN, r_out=R_OUT, z0=0.0, z1=HEIGHT,
                         n_radial=N_RADIAL, n_angle=N_ANGLE, n_z=N_Z)
    lower = make_annulus(r_in=R_IN, r_out=R_OUT, z0=-SUPPORT_THICKNESS,
                         z1=0.0, n_radial=N_RADIAL, n_angle=N_ANGLE, n_z=N_Z,
                         node_offset=max(upper.nodes),
                         element_offset=max(eid for eid, _ in upper.elements))
    nodes = merge_mesh_nodes(upper, lower)
    # Generate one shared *NODE and two body-specific *ELEMENT blocks.
    node_text = "*NODE\n" + "".join(
        f"{node},{xyz[0]:.12g},{xyz[1]:.12g},{xyz[2]:.12g}\n"
        for node, xyz in sorted(nodes.items()))
    element_text = []
    for name, mesh in (("UPPER", upper), ("SUPPORT", lower)):
        element_text.append(f"*ELEMENT,TYPE=C3D10,ELSET={name}\n")
        element_text.extend(f"{eid}," + ",".join(str(n) for n in conn) + "\n"
                            for eid, conn in mesh.elements)

    slave_faces = upper.boundary["bottom"]
    master_faces = lower.boundary["top"]
    loaded_faces = [face for sector in range(PATCH_SECTORS)
                    for face in upper.top_faces_by_sector[sector]]
    loaded_faces6 = []
    for face in loaded_faces:
        nodes6 = face_nodes6(upper, face)
        p0, p1, p2 = (upper.nodes[node] for node in nodes6[:3])
        normal = cross(vec_sub(p1, p0), vec_sub(p2, p0))
        if abs(normal[2]) <= 1e-12:
            raise ValueError("top pressure face does not have a vertical reference normal")
        loaded_faces6.append({"node_ids": nodes6,
                              "outward_sign": 1 if normal[2] > 0 else -1})
    loaded_patch_node_ids = sorted({node for face in loaded_faces6
                                    for node in face["node_ids"]})
    patch_area, patch_centroid = c3d10_face_area_centroid(upper, loaded_faces)
    if not close(patch_area, c3d10_face_area_centroid(
            upper, [face for sector in range(PATCH_SECTORS)
                    for face in upper.top_faces_by_sector[sector]])[0]):
        raise ValueError("loaded sector area is not deterministic")
    applied_force, applied_moment = face_wrench(patch_area, patch_centroid,
                                                PATCH_PRESSURE)
    contact_force = tuple(-x for x in applied_force)
    contact_moment = tuple(-x for x in applied_moment)

    ground_ids = sorted({node for face in lower.boundary["bottom"]
                         for node in face_nodes6(lower, face)})
    # Frictionless contact leaves in-plane rigid translations and spin free.
    # These gauges remove only those rigid modes; their RF is audited separately.
    gauge_a = next(node for node, xyz in upper.nodes.items()
                   if close(math.hypot(xyz[0], xyz[1]), R_OUT, 1e-10)
                   and close(xyz[1], 0.0, 1e-10) and close(xyz[2], 0.0, 1e-10))
    gauge_b = next(node for node, xyz in upper.nodes.items()
                   if close(math.hypot(xyz[0], xyz[1]), R_OUT, 1e-10)
                   and close(xyz[0], 0.0, 1e-10) and xyz[1] < 0.0
                   and close(xyz[2], 0.0, 1e-10))
    gauge_ids = [gauge_a, gauge_b]
    if set(gauge_ids) & set(loaded_patch_node_ids):
        raise ValueError("upper gauge nodes must not receive the pressure surface load directly")

    # Contact and load surfaces are distinct surface inventories. Surface area,
    # centroid, and pressure wrench are integrated from actual FE triangles.
    surface_text = (
        "*SURFACE,NAME=SLAVE,TYPE=ELEMENT\n" + write_surface_lines(slave_faces)
        + "*SURFACE,NAME=MASTER,TYPE=ELEMENT\n" + write_surface_lines(master_faces)
        + "*SURFACE,NAME=LOAD_PATCH,TYPE=ELEMENT\n" + write_surface_lines(loaded_faces)
    )
    boundary_text = ["*BOUNDARY\n"]
    for node in ground_ids:
        boundary_text.append(f"{node},1,3,0.0\n")
    boundary_text.extend((f"{gauge_a},1,1,0.0\n", f"{gauge_a},2,2,0.0\n",
                          f"{gauge_b},2,2,0.0\n"))

    deck = (
        "*HEADING\n"
        "Diagnostic eccentric finite-patch contact resultant; not a washer/wood/product claim\n"
        "** Units: mm, N, MPa. Bodies use distinct nodes; initial annular faces touch.\n"
        "** Positive P pressure is inward on the top face; no friction or tie.\n"
        + node_text + "".join(element_text)
        + node_set_lines("ALLNODES", sorted(nodes))
        + node_set_lines("GROUND", ground_ids)
        + node_set_lines("UPPER_GAUGES", gauge_ids)
        + node_set_lines("LOAD_PATCH_NODES", loaded_patch_node_ids)
        + "*MATERIAL,NAME=DIAGNOSTIC_STEEL\n*ELASTIC\n"
        + f"{STEEL_E:.12g},{NU:.12g}\n"
        + "*MATERIAL,NAME=DIAGNOSTIC_RECEIVER\n*ELASTIC\n"
        + f"{SUPPORT_E:.12g},{NU:.12g}\n"
        + "*SOLID SECTION,ELSET=UPPER,MATERIAL=DIAGNOSTIC_STEEL\n"
        + "*SOLID SECTION,ELSET=SUPPORT,MATERIAL=DIAGNOSTIC_RECEIVER\n"
        + surface_text
        + "*SURFACE INTERACTION,NAME=DIAGNOSTIC_NORMAL\n"
        + "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR\n"
        + f"{CONTACT_K:.12g}\n"
        + "*CONTACT PAIR,INTERACTION=DIAGNOSTIC_NORMAL,TYPE=SURFACE TO SURFACE\n"
        + "SLAVE,MASTER\n"
        + "".join(boundary_text)
        + "*STEP,NLGEOM,INC=100\n*STATIC,DIRECT\n0.1,1.0,1e-6,0.1\n"
        + "*DSLOAD\nLOAD_PATCH,P," + f"{PATCH_PRESSURE:.12g}\n"
        + "*NODE PRINT,NSET=GROUND,FREQUENCY=1\nU,RF\n"
        + "*NODE PRINT,NSET=UPPER_GAUGES,FREQUENCY=1\nU,RF\n"
        + "*NODE PRINT,NSET=LOAD_PATCH_NODES,FREQUENCY=1\nU\n"
        + "*CONTACT FILE,FREQUENCY=1\nCDIS,CSTR\n"
        + "*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER,FREQUENCY=1\nCF,CFN,CFS\n"
        + "*END STEP\n"
    )
    total_contact_area = upper.bottom_area_mm2
    if not close(total_contact_area, lower.top_area_mm2):
        raise ValueError("contact interfaces are not equal in FE area")
    expected = {
        "job": "finite-sector-contact-resultant",
        "final_time": 1.0,
        "model_coordinates_json": "model_coordinates.json",
        "scope": "contact/resultant extraction and equilibrium only",
        "mesh": {"total_nodes": len(nodes),
                 "total_elements": len(upper.elements) + len(lower.elements),
                 "upper_nodes": len(upper.nodes), "upper_elements": len(upper.elements),
                 "support_nodes": len(lower.nodes), "support_elements": len(lower.elements),
                 "contact_FE_area_mm2": total_contact_area,
                 "upper_FE_volume_mm3": upper.volume_mm3,
                 "support_FE_volume_mm3": lower.volume_mm3,
                 "ideal_circle_contact_area_mm2": math.pi * (R_OUT ** 2 - R_IN ** 2),
                 "ideal_circle_comparison_is_not_oracle": True},
        "material_assumptions": {
            "upper_isotropic_E_MPa": STEEL_E, "receiver_isotropic_E_MPa": SUPPORT_E,
            "poisson_both": NU,
            "role": "hypothetical linear-elastic software diagnostics only; receiver is not a wood model",
        },
        "contact_assumption": {
            "method": "face-to-face penalty, frictionless; normal only",
            "penalty_K_N_mm3": CONTACT_K,
            "initial_state": "exact touch, matched polygonal annular surfaces",
            "penalty_compliance_is_finite": True,
            "penalty_is_not_material_compliance": True,
        },
        "pressure_integration_contract": {
            "solver_discrete_rule": "CalculiX 2.23 gauss2d5; three triangle points, each weight 1/6",
            "solver_discrete_wrench_is_load_balance_oracle": True,
            "continuous_comparison_rule": "independent six-point degree-four TRI6 rule",
            "quadrature_difference_uses_existing_force_gate": 0.02,
            "quadrature_difference_uses_existing_moment_gate_N_mm": 0.05,
            "no_gate_widening": True,
        },
        "loaded_patch": {
            "pressure_MPa": PATCH_PRESSURE,
            "pressure_convention": "positive CalculiX P is inward on outward-facing top surface",
            "sector_count_of_16": PATCH_SECTORS,
            "tri6_face_kinematics": loaded_faces6,
            "pressure_node_ids": loaded_patch_node_ids,
            "tri6_straight_sided_FE_area_mm2": patch_area,
            "FE_area_centroid_mm": list(patch_centroid),
            "initial_applied_force_N": list(applied_force),
            "initial_applied_moment_about_origin_N_mm": list(applied_moment),
            "initial_expected_slave_contact_CF_and_CFN_force_N": list(contact_force),
            "initial_expected_slave_contact_CF_and_CFN_moment_N_mm": list(contact_moment),
            "expected_CFS_force_N": [0.0, 0.0, 0.0],
            "expected_CFS_moment_N_mm": [0.0, 0.0, 0.0],
        },
        "restraints": {
            "ground_node_set": ground_ids,
            "ground_dofs": "1,2,3 fixed on the lower body's bottom annular surface",
            "upper_in_plane_gauge_nodes": gauge_ids,
            "gauge_dofs": {str(gauge_a): [1, 2], str(gauge_b): [2]},
            "gauge_scope": "remove upper-body free in-plane translation/spin only; gauge RF reported separately",
            "gauge_nodes_receive_no_pressure_load": True,
            "gauge_rf_semantics": "CalculiX RF is total external nodal force, including consistent distributed-load contributions; these gauge nodes are disjoint from every pressure-face node, so their fixed x/y RF values are constraint reactions.",
            "free_z_rf_is_reported_not_treated_as_reaction": True,
        },
        "penalty_scale_not_a_response_oracle": {
            "full_contact_linear_normal_stiffness_N_mm": CONTACT_K * total_contact_area,
            "uniform_full_area_displacement_at_total_load_mm":
                norm(contact_force) / (CONTACT_K * total_contact_area),
            "warning": "This is a uniform full-area scale only; the eccentric contact pressure and indentation field are not predicted here.",
        },
        "support_oracle": {
            "ground_RF_initial_wrench_N_Nmm": [0.0, 0.0, -applied_force[2],
                                                 -applied_moment[0], -applied_moment[1],
                                                 -applied_moment[2]],
            "ground_RF_semantics": "The support nodes are on the unpressurized lower body and receive no nodal/distributed external load; RF is therefore support reaction here.",
            "current_deformed_pressure_wrench_used_for_final_balance": True,
            "gauge_reactions_reported_separately": True,
        },
        "predeclared_tolerances": {
            "resultant_absolute_N": 0.02,
            "resultant_relative": 2e-4,
            "moment_absolute_N_mm": 0.05,
            "moment_relative": 2e-4,
            "gauge_force_absolute_N": 0.02,
            "gauge_force_relative_to_load": 1e-4,
            "frictionless_CFS_absolute_N": 0.01,
            "equilibrium_wrench_absolute_N_or_Nmm": 0.1,
            "quadrature_difference_force_absolute_N": 0.02,
            "quadrature_difference_moment_absolute_N_mm": 0.05,
        },
    }
    return deck, expected, nodes


def source_pins() -> dict:
    required_files = {
        "solver_profile": PROFILE,
        "manual_pdf": MANUAL,
        "source_archive": SOURCE_ARCHIVE,
        "manual_html_archive": HTML_ARCHIVE,
        "prior_pair_parser": CONTACT_OUTPUT,
        "prior_exact_touch_deck": CONTACT_HISTORY / "input/penalty_touch_work.inp",
        "prior_exact_touch_readme": CONTACT_HISTORY / "README.md",
        "reduced_native_run_protocol": ROOT / "fea/wood_joint_reduced_native.py",
    }
    for key, path in required_files.items():
        if not path.exists():
            raise FileNotFoundError(f"required pinned source is absent: {key}: {path}")
    hardcoded = {"solver_profile": PROFILE_SHA256, "manual_pdf": MANUAL_SHA256,
                 "source_archive": SOURCE_ARCHIVE_SHA256,
                 "manual_html_archive": HTML_ARCHIVE_SHA256}
    artifact_pins = {}
    for key, path in required_files.items():
        actual = sha_file(path)
        if key in hardcoded and actual != hardcoded[key]:
            raise ValueError(f"pinned source changed: {key}: {actual}")
        artifact_pins[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT)
                      else str(path)] = actual
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        member_pins = {}
        for member, expected_hash in SOURCE_MEMBERS.items():
            actual = sha_bytes(archive.extractfile("./" + member).read())
            if actual != expected_hash:
                raise ValueError(f"pinned 2.23 source member changed: {member}")
            member_pins[member] = actual
    with tarfile.open(HTML_ARCHIVE, "r:bz2") as archive:
        manual_sections = {}
        for member, description in HTML_MEMBERS.items():
            payload = archive.extractfile(member).read()
            lower = payload.lower()
            normalized = b" ".join(re.sub(rb"<[^>]*>", b" ", lower).split())
            if member.endswith("node272.html") and b"load label for pressure is p" not in normalized:
                raise ValueError("pinned manual does not describe *DSLOAD pressure P")
            if member.endswith("node356.html") and b"face 1: 1-2-3" not in lower:
                raise ValueError("pinned manual C3D10 surface face labels changed")
            if member.endswith("node212.html") and b"sum of all external forces in a node" not in normalized:
                raise ValueError("pinned manual RF external-force semantics changed")
            if member.endswith("node227.html") and (
                    b"keyword type: step or model definition" not in normalized
                    or b"1: translation in the local x-direction" not in normalized
                    or b"3: translation in the local z-direction" not in normalized):
                raise ValueError("pinned manual *BOUNDARY model-definition semantics changed")
            manual_sections[description] = {"archive_member": member,
                                            "sha256": sha_bytes(payload)}
    pressure_source = {
        "assembly": "CalculiX/ccx_2.23/src/e_c3d_rhs.f",
        "triangle_rule": "gauss2d5, three integration points with weight 1/6 each",
        "coordinates": "current face coordinates are used for NLGEOM pressure assembly",
        "continuous_comparison": "independent six-point degree-four TRI6 integration",
    }
    if member_pins[pressure_source["assembly"]] != SOURCE_MEMBERS[
            pressure_source["assembly"]]:
        raise ValueError("pinned C3D10 pressure assembly source changed")
    with tarfile.open(SOURCE_ARCHIVE, "r:bz2") as archive:
        rhs = archive.extractfile("./" + pressure_source["assembly"]).read().lower()
        gauss = archive.extractfile("./CalculiX/ccx_2.23/src/gauss.f").read().lower()
        required_rhs = (b"gauss2d5(1,i)", b"gauss2d5(2,i)",
                        b"weight=weight2d5(i)", b"call shape6tri",
                        b"vold(j,konl(ifacet(i,ig)))")
        if any(token not in rhs for token in required_rhs):
            raise ValueError("pinned C3D10 pressure assembly no longer uses gauss2d5 TRI6 rule")
        required_gauss = (b"gauss2d5: tri, 3 integration points",
                          b"0.166666666666667d0", b"0.666666666666667d0",
                          b"weight2d5=(/", b"0.166666666666666d0")
        if any(token not in gauss for token in required_gauss):
            raise ValueError("pinned gauss2d5 points or weights changed")
    packet_code_paths = {}
    for relative in ("README.md", "prepare.py", "verify.py",
                     "verify_preparation_receipt.py", "tests/test_preparation.py"):
        path = HERE / relative
        packet_code_paths[relative] = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha_file(path),
        }
    return {
        "scope": "corrected contact method packet source pins only; no solver/model/product acceptance",
        "artifacts_sha256": artifact_pins,
        "packet_code_paths_sha256": packet_code_paths,
        "official_source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_members_sha256": member_pins,
        "official_manual_pdf_sha256": MANUAL_SHA256,
        "official_manual_html_archive_sha256": HTML_ARCHIVE_SHA256,
        "manual_section_members": manual_sections,
        "solver_pressure_quadrature": pressure_source,
        "pinned_runtime": json.loads(PROFILE.read_text()),
        "contact_history": {
            "exact_touch_fixture_path": str(CONTACT_HISTORY.relative_to(ROOT)),
            "validated_methods_reused": ["open/touch/compress/release states",
                                          "frictionless penalty contact",
                                          "CF/CFN/CFS pair resultants and origin moments"],
            "new_fixture_does_not_rerun_it": True,
        },
        "runner_protocol": {
            "path": "fea/wood_joint_reduced_native.py",
            "sha256": artifact_pins["fea/wood_joint_reduced_native.py"],
            "parent_only_launch": True,
            "each_job_requires_distinct_parent_reserved_run_id": True,
        },
    }


def prepare(output: Path) -> dict:
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty preparation directory: {output}")
    output.mkdir(parents=True, exist_ok=True)
    pins = source_pins()
    (output / "contact_pair_output.py").write_bytes(CONTACT_OUTPUT.read_bytes())
    json_write(output / "source-pins.json", pins)

    contact_deck, contact_expected, contact_nodes = job_contact()
    jobs = {
        "finite-sector-contact": (contact_deck, contact_expected, contact_nodes),
    }
    for name, (deck, expected, coordinates) in jobs.items():
        folder = output / name
        folder.mkdir()
        (folder / "model.inp").write_text(deck)
        json_write(folder / "expected.json", expected)
        json_write(folder / "model_coordinates.json",
                   {str(node): xyz for node, xyz in coordinates.items()})

    artifacts = {}
    for path in sorted(output.rglob("*")):
        if path.is_file() and path.name != "preparation.json":
            artifacts[str(path.relative_to(output))] = sha_file(path)
    supporting_code = {
        relative: sha_file(HERE / relative)
        for relative in ("README.md", "prepare.py", "verify.py",
                         "verify_preparation_receipt.py",
                         "tests/test_preparation.py")
    }
    receipt = {
        "schema": "washer_contact_known_answer_attempt02_preparation/v1",
        "preparation_only": True,
        "native_solve_executed": False,
        "native_readiness": False,
        "input_freeze_created": False,
        "mechanical_acceptance": False,
        "jobs": {name: {"deck": f"{name}/model.inp",
                        "deck_sha256": sha_file(output / name / "model.inp"),
                        "expected": f"{name}/expected.json",
                        "expected_sha256": sha_file(output / name / "expected.json"),
                        "coordinates": f"{name}/model_coordinates.json",
                        "coordinates_sha256": sha_file(output / name / "model_coordinates.json")}
                 for name in jobs},
        "files_sha256": artifacts,
        "supporting_code_sha256": supporting_code,
        "parent_recommended_run_bounds_not_authorization": {
            "timeout_seconds": 60, "memory": "1g", "cpus": 1,
            "serial": True, "contact_job_only": "finite-sector-contact",
        },
    }
    json_write(output / "preparation.json", receipt)
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, nargs="?", default=HERE / "prepared")
    args = parser.parse_args()
    result = prepare(args.output)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
