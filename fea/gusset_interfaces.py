"""Authenticated current-wide gusset face ownership, not traction recovery."""
import json
import math
from collections import defaultdict
from pathlib import Path

import cadquery as cq

from fea.floor_contact import FACES, mesh
from fea.floor_contact_results import cross
from fea.prepare_easy_structural import digest
from fea.wide_asymmetric import authenticated_inputs, unchanged
from fea.wide_joint_ownership import mesh_moments
from mini_moonboard import wide_frame as frame

OUTPUT = Path("fea/results/gusset-interfaces.json")


def build():
    _, deck, _, sources = authenticated_inputs()
    for path in ("fea/gusset_interfaces.py", "fea/wide_joint_ownership.py", "fea/solve_bearing_frame.py"):
        value = digest(path)
        if path in sources and sources[path] != value:
            raise ValueError("Conflicting gusset ownership source")
        sources[path] = value
    nodes, elements = mesh(deck)
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    faces = defaultdict(list)
    for eid, ids in elements.items():
        for number, indices in enumerate(FACES, 1):
            face = tuple(ids[i] for i in indices)
            faces[tuple(sorted(face))].append((eid, number, face))
    if any(len(owners) > 2 for owners in faces.values()):
        raise ValueError("Nonmanifold parent tetrahedron faces")
    result = {}
    for side in ("left", "right"):
        name = "timber_base_gusset_"+side
        shape = raw[name]
        box = shape.BoundingBox()
        chosen = {}
        for eid, ids in elements.items():
            p = [sum(nodes[n][i] for n in ids[:4])/4 for i in range(3)]
            if all(getattr(box, a+"min")-1e-5 <= p[i] <= getattr(box, a+"max")+1e-5
                   for i, a in enumerate("xyz")) and shape.isInside(cq.Vector(*p), 1e-5):
                chosen[eid] = ids
        owned = {n for ids in chosen.values() for n in ids}
        if not chosen or any(not shape.isInside(cq.Vector(*nodes[n]), 1e-5) for n in owned):
            raise ValueError("Incomplete gusset element containment")
        volume, center, midpoint = mesh_moments(nodes, chosen)
        if (abs(volume/shape.Volume()-1) > .001 or math.dist(center, shape.Center().toTuple()) > 1
                or midpoint > 1e-6):
            raise ValueError("Gusset mesh/CAD volume or centroid mismatch")
        shared = owned & {n for eid, ids in elements.items() if eid not in chosen for n in ids}
        contacts = defaultdict(list)
        candidates = {k: raw[k] for k in ("base_side_"+side, "base_post_outer_"+side,
                                         "base_header", "kicker_"+side)}
        for owners in faces.values():
            inside = [f for f in owners if f[0] in chosen]
            if len(owners) != 2 or len(inside) != 1:
                continue
            eid, number, ids = inside[0]
            outside = next(f for f in owners if f[0] not in chosen)
            p = [sum(nodes[n][i] for n in elements[outside[0]][:4])/4 for i in range(3)]
            member = [k for k, s in candidates.items() if s.isInside(cq.Vector(*p), 1e-5)]
            if len(member) != 1 or any(not candidates[member[0]].isInside(cq.Vector(*nodes[n]), 1e-5) for n in ids):
                raise ValueError("Unclassified or ambiguous neighboring face")
            a, b, c = [nodes[n] for n in ids[:3]]
            normal = cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
            area = math.sqrt(sum(v*v for v in normal))/2
            contacts[member[0]].append({"element": eid, "face": number,
                "neighbor_element": outside[0], "neighbor_face": outside[1],
                "nodes": list(ids), "corner_triangle_area_mm2": area})
        face_nodes = {n for rows in contacts.values() for r in rows for n in r["nodes"]}
        result[side] = {"element_ids": sorted(chosen), "node_ids": sorted(owned),
            "mesh_volume_mm3": volume, "cad_volume_mm3": shape.Volume(),
            "maximum_midpoint_error_mm": midpoint,
            "shared_nodes": sorted(shared), "shared_nodes_without_shared_face": sorted(shared-face_nodes),
            "interfaces": dict(contacts)}
    unchanged(sources)
    return {"candidate": frame.KEY, "source_sha256": sources, "gussets": result,
            "limits": "Bonded parent-mesh face/node ownership only; no traction or actual bolt demand. "
            "Interface node sets can overlap at edges; do not double count reactions. "
            "Corner-triangle area does not integrate curved quadratic faces."}


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite interface evidence")
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
