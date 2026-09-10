"""Source-bound raw-rim ownership and remote interfaces; no boundary values or solve."""
import argparse
import hashlib
import json
import math
import tarfile
from collections import defaultdict
from pathlib import Path

import cadquery as cq

from fea.floor_contact import FACES
from fea.wide_joint_ownership import mesh_moments
from mini_moonboard import lumber_leg_spread_frame as model
from mini_moonboard.box_exports import exact_bounds

ARCHIVE = Path("fea/results/spread-leg-response/2x6-e0-m40-E7000.tar.gz")
TOL = 1e-5


def authenticate(path):
    with tarfile.open(path) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    report = json.loads(files["report.json"])
    if set(report["artifact_sha256"]) != set(files)-{"report.json"} or any(
            hashlib.sha256(files[n]).hexdigest() != h for n, h in report["artifact_sha256"].items()):
        raise ValueError("Native artifact identity changed")
    if (not report["passed"] or set(report["runs"]) != {"k100", "k1000", "k10000"}
            or (report["geometry"], report["stock"], report["extension_mm"])
            != ("spread-100x50-top150", "2x6", 0)):
        raise ValueError("Require accepted compact spread 2x6 archive")
    for name, sha in report["source_sha256"].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha:
            raise ValueError("Native source identity changed")
    return json.loads(files["input.json"]), report


def select(nodes, elements, shape):
    """Select by CAD interior; reject every selected element with an exterior node."""
    bounds = exact_bounds(shape)
    lo, hi = [[getattr(bounds, a+end) for a in "xyz"] for end in ("min", "max")]
    def inside(p):
        return all(lo[i]-TOL <= p[i] <= hi[i]+TOL for i in range(3)) and shape.isInside(cq.Vector(*p), TOL)
    chosen = {}
    for eid, ids in elements.items():
        if len(ids) != 10 or len(set(ids)) != 10:
            raise ValueError("Require C3D10 connectivity")
        centre = [sum(nodes[n][i] for n in ids[:4])/4 for i in range(3)]
        if inside(centre):
            if not all(inside(nodes[n]) for n in ids):
                raise ValueError(f"Partial rim element ownership: {eid}")
            chosen[eid] = ids
    if not chosen:
        raise ValueError("No rim elements")
    volume, centre, midpoint = mesh_moments(nodes, chosen)
    if abs(volume/shape.Volume()-1) > .001 or math.dist(centre, shape.Center().toTuple()) > 1:
        raise ValueError(f"Raw rim CAD mismatch: mesh volume {volume}, CAD {shape.Volume()}, centroid {centre}")
    return chosen, {"mesh_volume_mm3": volume, "cad_volume_mm3": shape.Volume(),
                    "mesh_centroid_mm": centre, "cad_centroid_mm": shape.Center().toTuple(),
                    "maximum_midpoint_error_mm": midpoint}


def interfaces(nodes, elements, chosen, points, side):
    owned = {n for ids in chosen.values() for n in ids}
    others = {n for e, ids in elements.items() if e not in chosen for n in ids}
    shared = owned & others
    faces = defaultdict(list)
    for e, ids in elements.items():
        if not shared.intersection(ids):
            continue
        for number, indices in enumerate(FACES, 1):
            ns = [ids[i] for i in indices]
            if set(ns) <= shared:
                faces[tuple(sorted(ns))].append({"element": e, "face": number, "nodes": ns})
    boundaries = []
    for rows in faces.values():
        local = [r for r in rows if r["element"] in chosen]
        remote = [r for r in rows if r["element"] not in chosen]
        if local and remote:
            if len(local) != 1 or len(remote) != 1:
                raise ValueError("Nonmanifold rim interface")
            boundaries.append({"rim": local[0], "omitted_wood": remote[0]})
    covered = {n for r in boundaries for n in r["rim"]["nodes"]}
    replaced, retained = {}, {}
    for name, p in points.items():
        hit = owned.intersection(p["nodes"])
        other_hit = owned.intersection(p["gusset_nodes"])
        if not hit and not other_hit:
            continue
        if hit != set(p["nodes"]) or other_hit or p["member"] != f"base_side_{side}":
            raise ValueError("Partial or unexpected rim MPC ownership")
        target = replaced if name.startswith(f"lumber_leg_bolt_{side}_") else retained
        target[name] = p
    if len(replaced) != 4 or set(retained) != {f"timber_base_{side}_{i}" for i in (1, 2)}:
        raise ValueError("Unexpected replaced leg or remote gusset connectors")
    return {"node_ids": sorted(owned), "shared_nodes_with_omitted_wood": sorted(shared),
            "shared_faces": boundaries, "shared_edge_or_vertex_nodes": sorted(shared-covered),
            "remote_gusset_mpcs": retained, "replaced_leg_mpcs": replaced,
            "required_remote_displacement_nodes": sorted(shared | {n for p in retained.values() for n in p["gusset_nodes"]}),
            "retained_rim_mpc_support_nodes": sorted({n for p in retained.values() for n in p["nodes"]}),
            "floor_nodes": sorted(n for n in owned if abs(nodes[n][2]) < TOL)}


def build(path=ARCHIVE):
    path = Path(path)
    data, parent = authenticate(path)
    nodes = {int(n): p for n, p in data["nodes"].items()}
    elements = {int(e): ids for e, ids in data["elements"].items()}
    raw = {p.name: p.shape for p in model.parts("2x6", 0., False)}
    result = {}
    for side in ("left", "right"):
        name = f"base_side_{side}"
        chosen, checks = select(nodes, elements, raw[name])
        result[side] = {"member": name, "element_ids": sorted(chosen), **checks,
                        **interfaces(nodes, elements, chosen, data["points"], side)}
    sources = dict(parent["source_sha256"])
    for name in ("fea/compact_rim_boundary.py", "fea/wide_joint_ownership.py",
                 "fea/solve_bearing_frame.py", "fea/floor_contact.py", "fea/floor_contact_results.py",
                 "mini_moonboard/box_exports.py"):
        sha = hashlib.sha256(Path(name).read_bytes()).hexdigest()
        if name in sources and sources[name] != sha:
            raise ValueError("Conflicting source identity")
        sources[name] = sha
    for name, sha in sources.items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha:
            raise ValueError("Source changed during ownership mapping")
    return {"archive": str(path), "archive_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_sha256": sources, "rims": result, "qualified_for_design": False,
            "boundary_values_assigned": False,
            "limits": "Raw undrilled parent mesh ownership, not drilled joint contact geometry. "
            "Remote node IDs identify mapping targets only; no guessed U, loads or constraints. "
            "Do not apply replaced spring forces with mapped parent displacements. "
            "Future contact-parent fields require their own archive/source and endpoint authentication."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    args = parser.parse_args()
    print(json.dumps(build(args.archive), indent=2, allow_nan=False))
