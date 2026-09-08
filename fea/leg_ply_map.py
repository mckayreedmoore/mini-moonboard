"""Individual leg-ply ownership and stitch axes on the existing bonded mesh."""
import json
import math
from collections import defaultdict
from pathlib import Path

from fea.floor_contact import FACES, mesh
from fea.gusset_connector_trial import point_weights
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import unchanged
from fea.wide_asymmetric import authenticated_inputs
from fea.wide_joint_ownership import mesh_moments
from mini_moonboard import wide_frame as frame

MAP = Path("fea/results/leg-connector-map.json")
OUTPUT = Path("fea/results/leg-ply-map.json")


def build():
    import cadquery as cq

    _, deck, _, sources = authenticated_inputs()
    parent = json.loads(MAP.read_text())
    unchanged(parent["source_sha256"])
    sources.update(parent["source_sha256"])
    sources[str(MAP)] = digest(MAP)
    sources["fea/leg_ply_map.py"] = digest("fea/leg_ply_map.py")
    nodes, elements = mesh(deck)
    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    bolts = frame.connections()
    result = {}
    for side, leg in parent["legs"].items():
        inner, outer = (f"leg_{side}_{layer}" for layer in ("inner", "outer"))
        # Derive split plane from CAD, not a nominal plywood thickness.
        bb = raw[inner].BoundingBox()
        sign = -1 if side == "left" else 1
        plane = bb.xmin if sign < 0 else bb.xmax
        groups = {inner: {}, outer: {}}
        for eid in leg["element_ids"]:
            ids = elements[eid]
            distances = [sign*(nodes[n][0]-plane) for n in ids]
            if max(distances) <= 1e-5:
                groups[inner][eid] = ids
            elif min(distances) >= -1e-5:
                groups[outer][eid] = ids
            else:
                raise ValueError("Element crosses ply boundary; cannot release without remeshing")
        members = {}
        for name, chosen in groups.items():
            owned = {n for ids in chosen.values() for n in ids}
            if not chosen or any(not raw[name].isInside(cq.Vector(*nodes[n]), 1e-5) for n in owned):
                raise ValueError("Ply selection leaves CAD or is empty")
            volume, centre, midpoint = mesh_moments(nodes, chosen)
            if abs(volume/raw[name].Volume()-1) > .001 or math.dist(centre, raw[name].Center().toTuple()) > 1.:
                raise ValueError("Individual ply volume or centroid differs from CAD")
            members[name] = {"element_ids": sorted(chosen), "node_ids": sorted(owned),
                             "floor_nodes": sorted(n for n in owned if abs(nodes[n][2]) < 1e-5),
                             "mesh_volume_mm3": volume, "cad_volume_mm3": raw[name].Volume(),
                             "mesh_centroid_mm": centre, "cad_centroid_mm": raw[name].Center().toTuple(),
                             "maximum_midpoint_error_mm": midpoint}
        faces = defaultdict(list)
        for name, chosen in groups.items():
            for eid, ids in chosen.items():
                for number, indices in enumerate(FACES, 1):
                    face = [ids[i] for i in indices]
                    if all(abs(nodes[n][0]-plane) < 1e-5 for n in face):
                        faces[tuple(sorted(face))].append({"member": name, "element": eid,
                                                          "face": number, "nodes": face})
        if not faces or any(len(rows) != 2 or {r["member"] for r in rows} != set(groups) for rows in faces.values()):
            raise ValueError("Ply interface is not conforming and two-sided")
        shared = set(members[inner]["node_ids"]) & set(members[outer]["node_ids"])
        if {n for face in faces for n in face} != shared:
            raise ValueError("Shared ply nodes lack complete interface faces")
        interface = [next(r for r in rows if r["member"] == inner) for rows in faces.values()]
        stitches = [c for c in bolts if c.name.startswith(f"leg_stitch_{side}_")]
        if len(stitches) != 3 or any(set(c.members) != set(groups) for c in stitches):
            raise ValueError("Require three intended stitch bolts per leg")
        points = {c.name: point_weights(nodes, interface, (c.start.y, c.start.z)) for c in stitches}
        result[side] = {"plane_x_mm": plane, "members": members, "shared_nodes": sorted(shared),
                        "interface_faces": list(faces.values()), "stitch_points": points}
    unchanged(sources)
    return json.loads(json.dumps({"candidate": frame.KEY, "source_sha256": sources,
        "limits": "Ownership and stitch mapping only. No node release, solve, contact, bolt stiffness, "
        "individual-ply load sharing or resistance established.", "legs": result}))


if __name__ == "__main__":
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite ply-map evidence")
    OUTPUT.write_text(json.dumps(build(), indent=2)+"\n")
