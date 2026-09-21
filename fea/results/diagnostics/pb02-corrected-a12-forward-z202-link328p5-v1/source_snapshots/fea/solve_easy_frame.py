"""Isolated A/B ideal-bonded stiffness screen, not joint or use approval."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from fea.box_results import parse_results
from fea.floor_contact import FACES, floor_faces, mesh, node_set
from fea.floor_contact_results import blocks, cross
from fea.hybrid_results import deck_geometry, support_moments

KEYS = ("square-cut-bracket", "square-cut-wood-blocks")
LIMITS = (
    "Optimistic ideal-bonded stiffness diagnostic only: every touching wood interface, "
    "including independent leg plies, is artificially bonded. Actual floor nodes "
    "are fixed XYZ; no gravity, contact separation, sliding, bolt/screw/connector "
    "compliance, material strength, buckling or use approval. Isotropic wood. "
    "B blocks change the bonded load path; A/B difference is not a joint ranking."
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_deck(mesh_text, feet, top, cases, modulus):
    lines = ["** " + LIMITS, mesh_text, *node_set("FEET", feet),
             *node_set("TOP", top), "*MATERIAL,NAME=WOOD_SCREEN", "*ELASTIC",
             f"{modulus:g},0.3", "*SOLID SECTION,ELSET=TIMBER,MATERIAL=WOOD_SCREEN"]
    for case in cases:
        lines += ["** CASE " + case["name"], "*STEP", "*STATIC", "*BOUNDARY",
                  "FEET,1,3,0", "*CLOAD,OP=NEW"]
        lines += [f"{n},{i},{force/len(top):.9f}" for n in top
                  for i, force in enumerate(case["force_n"], 1) if force]
        lines += ["*NODE PRINT,NSET=TOP", "U", "*NODE PRINT,NSET=FEET,TOTALS=YES",
                  "RF", "*NODE FILE", "U", "*END STEP"]
    return "\n".join(lines) + "\n"


def audit(text, data, info):
    cases = [(c["name"], tuple(v/1200 for v in c["force_n"]))
             for c in info["audited_cases"]]
    nodes, feet, top = deck_geometry(text, cases)
    _, elements = mesh(text)
    groups = floor_faces(nodes, elements)
    group_nodes = {name: sorted({elements[e][i] for e, face in faces
                                for i in FACES[face-1]}) for name, faces in groups.items()}
    if sum(map(len, group_nodes.values())) != len({n for ids in group_nodes.values() for n in ids}):
        raise ValueError("Floor patches share reaction nodes")
    if set(feet) != {n for ids in group_nodes.values() for n in ids}:
        raise ValueError("Fixed nodes do not equal complete actual floor patches")
    maxima, reactions = parse_results(data, cases)
    moments = support_moments(data, nodes, feet, top, cases)
    parsed, patches = blocks(data), []
    for endpoint, (name, _) in enumerate(cases, 1):
        u = parsed.get(("displacements", "TOP", float(endpoint)), {})
        rf = parsed.get(("forces", "FEET", float(endpoint)), {})
        if set(u) != set(top) or set(rf) != set(feet):
            raise ValueError("Missing exact load/support endpoint nodes")
        for group, ids in group_nodes.items():
            patches.append({"case": name, "group": group,
                            "reaction_n": [sum(rf[n][i] for n in ids) for i in range(3)],
                            "moment_about_origin_nmm": [sum(cross(nodes[n], rf[n])[i]
                                                            for n in ids) for i in range(3)]})
    return {"max_top_displacement_mm": maxima, "reaction_totals_n": reactions,
            "reaction_moment_nmm": moments, "floor_patch_reactions": patches}


def target_mapping(nodes, targets, size):
    if len(targets) != 5 or not all(math.isfinite(v) for p in targets for v in p):
        raise ValueError("Five finite load targets required")
    result = [{"target_mm": p, "node": min(nodes, key=lambda n: math.dist(nodes[n], p))}
              for p in targets]
    for row in result:
        row["coordinates_mm"] = nodes[row["node"]]
        row["distance_mm"] = math.dist(row["coordinates_mm"], row["target_mm"])
    if len({r["node"] for r in result}) != 5 or any(r["distance_mm"] > size/2 for r in result):
        raise ValueError("Load targets map to duplicate or distant nodes")
    return result


def run(candidate, size, modulus):
    import gmsh

    directory = Path("fea/generated/square-cut") / candidate
    info_path = directory / "box_frame_bulk.json"
    info = json.loads(info_path.read_text())
    step = directory / "box_frame_bulk.step"
    if info["candidate"] != candidate or digest(step) != info["step_sha256"]:
        raise ValueError("Frozen candidate/STEP identity differs")
    sources = dict(info["geometry_source_sha256"])
    for name in ("fea/solve_easy_frame.py", "fea/box_results.py", "fea/floor_contact.py",
                 "fea/floor_contact_results.py", "fea/hybrid_results.py"):
        sources.setdefault(name, digest(name))
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError("Frozen source differs")
    prefix = directory / f"box_audited_{size:g}_{modulus:g}".replace(".", "p")
    context = prefix.with_suffix(".context.json")
    with context.open("x") as stream:
        json.dump({"input_sha256": digest(info_path), "source_sha256": sources,
                   "limits": LIMITS, "candidate": candidate, "size_mm": size,
                   "modulus_mpa": modulus}, stream, indent=2)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Verbosity", 2)
        gmsh.model.add(candidate)
        shapes = gmsh.model.occ.importShapes(str(step))
        if len(shapes) < 2 or any(dim != 3 for dim, _ in shapes):
            raise ValueError("Expected multi-solid timber STEP")
        gmsh.model.occ.fragment(shapes[:1], shapes[1:])
        gmsh.model.occ.synchronize()
        volumes = [tag for _, tag in gmsh.model.getEntities(3)]
        gmsh.model.addPhysicalGroup(3, volumes, 1)
        gmsh.model.setPhysicalName(3, 1, "TIMBER")
        for key, value in (("Mesh.MeshSizeMax", size), ("Mesh.MeshSizeMin", size/5),
                           ("Mesh.MeshSizeFromCurvature", 0), ("Mesh.ElementOrder", 2)):
            gmsh.option.setNumber(key, value)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        qualities = [float(q) for tags in gmsh.model.mesh.getElements(3)[1]
                     for q in gmsh.model.mesh.getElementQualities(tags, "minDetJac")]
        if not qualities or not all(map(math.isfinite, qualities)) or min(qualities) <= 0:
            raise ValueError("Invalid quadratic Jacobian")
        gmsh.write(str(prefix.with_suffix(".inp")))
        version = gmsh.__version__
    finally:
        gmsh.finalize()
    mesh_text = prefix.with_suffix(".inp").read_text()
    nodes, elements = mesh(mesh_text)
    parent = {n: n for n in nodes}

    def root(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for ids in elements.values():
        for n in ids[1:]:
            parent[root(n)] = root(ids[0])
    if len({root(n) for n in nodes}) != 1:
        raise ValueError("Ideal-bonded timber mesh is disconnected")
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    targets = info["audited_load_targets_mm"]
    mapping = target_mapping(nodes, targets, size)
    top = sorted(r["node"] for r in mapping)
    if len(targets) != 5 or len(top) != 5 or not feet or set(top) & set(feet):
        raise ValueError("Invalid load/support selection")
    text = make_deck(mesh_text, feet, top, info["audited_cases"], modulus)
    prefix.with_suffix(".inp").write_text(text)
    deck_sha = digest(prefix.with_suffix(".inp"))
    launch = json.loads(context.read_text())
    launch.update(deck_sha256=deck_sha, load_nodes=top, floor_node_count=len(feet),
                  gmsh_version=version, min_jacobian=min(qualities))
    context.write_text(json.dumps(launch, indent=2, allow_nan=False) + "\n")
    with prefix.with_suffix(".log").open("w") as stream:
        result = subprocess.run(["ccx", "-i", prefix.name], cwd=directory,
                                stdout=stream, stderr=subprocess.STDOUT, check=False)
    if result.returncode or "*ERROR" in prefix.with_suffix(".log").read_text().upper():
        raise ValueError("CalculiX failed; outputs retained")
    if (digest(prefix.with_suffix(".inp")) != deck_sha or digest(step) != info["step_sha256"]
            or digest(info_path) != launch["input_sha256"]):
        raise ValueError("Frozen solver input changed")
    if any(digest(name) != sha for name, sha in sources.items()):
        raise ValueError("Source changed during run")
    summary = {"candidate": candidate, "mesh_size_mm": size, "modulus_mpa": modulus,
               "nodes": len(nodes), "elements": len(elements), "min_jacobian": min(qualities),
               "gmsh_version": version, "geometry_commit": info["geometry_commit"],
               "load_nodes": top, "load_target_mapping": mapping,
               "floor_nodes": len(feet), "limits": LIMITS,
               "frozen_geometry": info, "source_sha256": sources,
               "load_target_distances_mm": [min(math.dist(nodes[n], t) for n in top) for t in targets],
               **audit(text, prefix.with_suffix(".dat").read_text(), info)}
    summary["evidence_sha256"] = {p.name: digest(p) for p in directory.glob(prefix.name + ".*")}
    prefix.with_suffix(".json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("candidate", "nodes", "max_top_displacement_mm")}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", choices=KEYS, required=True)
    parser.add_argument("--size", type=float, choices=(60., 40.), required=True)
    parser.add_argument("--modulus", type=float, default=7000.)
    args = parser.parse_args()
    if not math.isfinite(args.modulus) or args.modulus <= 0:
        parser.error("Modulus must be positive finite")
    run(args.candidate, args.size, args.modulus)


if __name__ == "__main__":
    main()
