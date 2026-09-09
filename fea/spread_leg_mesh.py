"""Independent spread-leg C3D10 mesh; 100x50 group, top150mm, not qualified.

Frozen worker/parser/integration helpers are reused. The explicit CAD audit is
kept here so archived original geometry sources remain unchanged.
"""
import hashlib
import json
import math
import os
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import cadquery as cq
import numpy as np

from fea.floor_contact import FACES, mesh
from fea.lumber_leg_mesh import WORKER
from fea.prescribed_tet_control import IMAGE
from fea.solve_bearing_frame import straight_mesh_volume
from fea.solve_easy_frame import digest
from mini_moonboard import lumber_leg_spread_frame as frame


def build(size, extension, side, mesh_size=40.):
    """Return local node/element IDs and audited floor/inner-face metadata.

    Inner-face records have element/face/nodes keys for point_weights. IDs
    must be remapped by a whole-frame caller. No holes or material model.
    """
    if side not in ("left", "right") or isinstance(mesh_size, bool) or not (
            math.isfinite(mesh_size) and 0 < mesh_size <= 80):
        raise ValueError("Require left/right and finite mesh size in (0,80] mm")
    manifest_path = Path("exports/wide-principal-development/manifest.json")
    sources = dict(json.loads(manifest_path.read_text())["sources"])
    for path in (str(manifest_path), "mini_moonboard/lumber_leg_frame.py", "mini_moonboard/lumber_leg_spread_frame.py",
                 "fea/lumber_leg_mesh.py", "fea/spread_leg_mesh.py", "fea/floor_contact.py",
                 "fea/solve_bearing_frame.py", "fea/prescribed_tet_control.py", "uv.lock"):
        sources.setdefault(path, digest(path))
    if not sources or any(digest(p) != value for p, value in sources.items()):
        raise ValueError("Current geometry source differs")
    part = frame.leg(size, extension, side)
    shape = part.shape
    settings = {"General.NumThreads": 1, "Mesh.MeshSizeMax": mesh_size,
                "Mesh.MeshSizeMin": mesh_size/5, "Mesh.MeshSizeFromCurvature": 0,
                "Mesh.ElementOrder": 2, "Mesh.SecondOrderLinear": 1}
    with tempfile.TemporaryDirectory(prefix="spread-leg-mesh-") as temporary:
        step, inp = Path(temporary)/"leg.step", Path(temporary)/"leg.inp"
        cq.exporters.export(shape, str(step))
        step_sha = digest(step)
        (Path(temporary)/"settings.json").write_text(json.dumps(settings))
        subprocess.run(["docker", "run", "--rm", "--network=none", "--cpus=1", "--memory=1g",
                        "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                        "--user", f"{os.getuid()}:{os.getgid()}", "-v", f"{temporary}:/work",
                        "-w", "/work", IMAGE, "timeout", "110", "python3", "-c", WORKER],
                       check=True, capture_output=True, text=True, timeout=120)
        text = inp.read_text()
        version = json.loads((Path(temporary)/"gmsh-version.json").read_text())
    nodes, elements = mesh(text)
    if {n for ids in elements.values() for n in ids} != set(nodes):
        raise ValueError("Incomplete mesh node ownership")
    volume, midpoint = straight_mesh_volume(nodes, elements)
    corners = np.array([[nodes[n] for n in ids[:4]] for ids in elements.values()])
    volumes = np.linalg.det(corners[:, 1:]-corners[:, :1])/6
    centre = np.sum(volumes[:, None]*corners.mean(axis=1), axis=0)/volume
    cad_centre = shape.Center().toTuple()
    if abs(volume/shape.Volume()-1) > 1e-6 or math.dist(centre, cad_centre) > 1e-5:
        raise ValueError("Leg mesh volume/centroid differs from CAD")
    if any(not shape.isInside(cq.Vector(*p), 1e-5) for p in nodes.values()):
        raise ValueError("Leg mesh leaves CAD solid")
    owners = defaultdict(list)
    for eid, ids in elements.items():
        for number, indices in enumerate(FACES, 1):
            face = [ids[i] for i in indices]
            owners[tuple(sorted(face))].append({"element": eid, "face": number, "nodes": face})
    if any(len(rows) > 2 for rows in owners.values()):
        raise ValueError("Nonmanifold leg mesh")
    boundary = [rows[0] for rows in owners.values() if len(rows) == 1]
    surfaces = {}
    for name, axis, coordinate in (("floor", 2, 0.),
                                    ("inner_interface", 0, frame.original.b.HALF if side == "right" else -frame.original.b.HALF)):
        faces = [f for f in boundary if all(abs(nodes[n][axis]-coordinate) < 1e-5 for n in f["nodes"])]
        owned = {n for f in faces for n in f["nodes"]}
        if not faces or owned != {n for n, p in nodes.items() if abs(p[axis]-coordinate) < 1e-5}:
            raise ValueError("Incomplete floor/interface node coverage")
        triangles = np.array([[nodes[n] for n in f["nodes"][:3]] for f in faces])
        areas = np.linalg.norm(np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0]), axis=1)/2
        area = float(areas.sum())
        centroid = np.sum(areas[:, None]*triangles.mean(axis=1), axis=0)/area
        cad = [f for f in shape.Faces() if all(abs(v.Center().toTuple()[axis]-coordinate) < 1e-5 for v in f.Vertices())]
        if len(cad) != 1 or abs(area/cad[0].Area()-1) > 1e-6 or math.dist(centroid, cad[0].Center().toTuple()) > 1e-5:
            raise ValueError("Floor/interface area or centroid differs from CAD")
        surfaces[name] = {"nodes": sorted(owned), "faces": faces, "area_mm2": area,
                          "centroid_mm": centroid.tolist(), "cad_area_mm2": cad[0].Area(),
                          "cad_centroid_mm": cad[0].Center().toTuple()}
    if any(digest(p) != value for p, value in sources.items()):
        raise ValueError("Source changed during leg meshing")
    return nodes, elements, {"stock": size, "extension_mm": extension, "side": side,
        "mesh_size_mm": mesh_size, "settings": settings,
        "along_leg_pitch_mm": frame.ALONG_LEG_PITCH,
        "along_rim_pitch_mm": frame.ALONG_RIM_PITCH,
        "top_extension_mm": frame.TOP_EXTENSION, "gmsh_version": version, "image": IMAGE,
        "node_count": len(nodes), "element_count": len(elements),
        "mesh_volume_mm3": volume, "cad_volume_mm3": shape.Volume(),
        "mesh_centroid_mm": centre.tolist(), "cad_centroid_mm": cad_centre,
        "maximum_midpoint_error_mm": midpoint,
        "minimum_corner_determinant_mm3": float(6*volumes.min()), "floor": surfaces["floor"],
        "floor_nodes": surfaces["floor"]["nodes"],
        "interface_faces": surfaces["inner_interface"]["faces"],
        "inner_interface": surfaces["inner_interface"], "source_sha256": sources,
        "step_sha256": step_sha, "mesh_inp_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "limits": "Undrilled independent leg mesh only; no hardware holes, joint law, local stress or strength qualification."}
