"""Spread 100x50 mm joint trial using the unchanged native solver/audit kernel."""
import argparse
import copy
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.lumber_leg_response import (
    FACES,
    GATES,
    IMAGE,
    LEG_MAP,
    audit,
    base,
    combine,
    deck,
    digest,
    parent_inputs,
    point_weights,
    unchanged,
)
from fea.lumber_leg_response import (
    LIMITS as ORIGINAL_LIMITS,
)

LIMITS = "Spread 100x50mm group, top150mm past centre. " + ORIGINAL_LIMITS

def prepare(size, extension=0., mesh_size=40.):
    from fea.spread_leg_mesh import build
    from mini_moonboard import lumber_leg_spread_frame as model

    model.geometry(size, extension)
    original_nodes, original_elements, original_points, cases, sources, _ = parent_inputs()
    nodes, elements = dict(original_nodes), dict(original_elements)
    points, sources = copy.deepcopy(original_points), dict(sources)
    mapping = json.loads(LEG_MAP.read_text())
    unchanged(mapping["source_sha256"])
    for path, sha in mapping["source_sha256"].items():
        if path in sources and sources[path] != sha:
            raise ValueError("Conflicting parent source identities")
        sources[path] = sha
    removed = {e for leg in mapping["legs"].values() for e in leg["element_ids"]}
    if not removed <= elements.keys():
        raise ValueError("Parent leg elements missing")
    elements = {e: ids for e, ids in elements.items() if e not in removed}
    used = {n for ids in elements.values() for n in ids}
    nodes = {n: p for n, p in nodes.items() if n in used}
    if not all(case["node"] in nodes for case in cases):
        raise ValueError("Leg replacement removed a climbing load target")
    for p in points.values():
        p["other_weights"] = p["weights"]
    legs = {}
    bolts = model.connections(size, extension)
    for side in ("left", "right"):
        local_nodes, local_elements, metadata = build(size, extension, side, mesh_size)
        for path, sha in metadata["source_sha256"].items():
            if path in sources and sources[path] != sha:
                raise ValueError("Conflicting mesh source identities")
            sources[path] = sha
        first_node, first_element = max(nodes)+1, max(elements)+1
        remap = {n: first_node+i for i, n in enumerate(sorted(local_nodes))}
        element_map = {e: first_element+i for i, e in enumerate(sorted(local_elements))}
        nodes.update({remap[n]: p for n, p in local_nodes.items()})
        elements.update({element_map[e]: tuple(remap[n] for n in ids) for e, ids in local_elements.items()})
        legs[side] = {"nodes": sorted(remap.values()), "element_ids": sorted(element_map.values()),
            "floor_nodes": [remap[n] for n in metadata["floor_nodes"]], "mesh": metadata}
        for bolt in bolts:
            if not bolt.name.startswith(f"lumber_leg_bolt_{side}_"):
                continue
            yz = (bolt.start.y, bolt.start.z)
            rim = f"base_side_{side}"
            retained_faces = [{"element": face["neighbor_element"], "face": face["neighbor_face"],
                "nodes": [elements[face["neighbor_element"]][i]
                          for i in FACES[face["neighbor_face"]-1]]}
                for face in mapping["legs"][side]["interfaces"][rim]]
            parent = point_weights(nodes, retained_faces, yz)
            own = point_weights(local_nodes, metadata["interface_faces"], yz)
            if math.dist(parent["point_mm"], own["point_mm"]) > 1e-6:
                raise ValueError("Connector endpoints do not meet at the actual interface")
            if not set(parent["nodes"]) <= used:
                raise ValueError("Connector references a removed leg node")
            points[bolt.name] = {**parent, "side": side, "member": rim,
                "gusset_nodes": [remap[n] for n in own["nodes"]],
                "other_weights": own["weights"],
                "other_face_element": element_map[own["face_element"]], "other_face": own["face"]}
    if len(points) != 16 or sum(n.startswith("lumber_leg_bolt_") for n in points) != 8:
        raise ValueError("Require eight retained gusset and eight new leg connectors")
    for path in (str(LEG_MAP), "fea/spread_leg_response.py", "fea/spread_leg_mesh.py",
                 "fea/lumber_leg_response.py", "fea/lumber_leg_mesh.py",
                 "mini_moonboard/lumber_leg_spread_frame.py",
                 "mini_moonboard/lumber_leg_frame.py", "fea/solve_bearing_frame.py", "uv.lock"):
        sources.setdefault(path, digest(path))
    unchanged(sources)
    return nodes, elements, points, cases, sources, legs


def run(size, extension, mesh_size, output, leg_modulus=7000.):
    if output.exists():
        raise FileExistsError("Refusing to overwrite native evidence")
    Path("fea/generated").mkdir(parents=True, exist_ok=True)
    nodes, elements, points, cases, sources, legs = prepare(size, extension, mesh_size)
    directory = Path(tempfile.mkdtemp(prefix="spread-leg-response-", dir="fea/generated")).resolve()
    report = {"geometry": "spread-100x50-top150", "stock": size, "extension_mm": extension, "mesh_size_mm": mesh_size,
        "leg_modulus_mpa": leg_modulus, "limits": LIMITS, "gates": GATES, "image": IMAGE,
        "source_sha256": sources, "qualified_for_design": False, "runs": {}}
    print(directory, flush=True)
    # Save the complete mapped input independently of the native deck/output.
    (directory/"input.json").write_text(json.dumps({"nodes": nodes, "elements": elements,
        "points": points, "cases": cases, "legs": legs}, allow_nan=False)+"\n")
    for stiffness in base.STIFFNESSES:
        name = f"k{int(stiffness)}"
        text, context = deck(nodes, elements, points, cases, stiffness, legs, leg_modulus)
        (directory/f"{name}.inp").write_text(text)
        command = ["docker", "run", "--rm", "--network=none", "--cpus=2", "--memory=6g",
            "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", f"{os.getuid()}:{os.getgid()}",
            "-e", "OMP_NUM_THREADS=2", "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", name]
        with (directory/f"{name}.log").open("w") as log:
            done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
        log = (directory/f"{name}.log").read_text()
        if done.returncode or "*ERROR" in log.upper() or "Job finished" not in log:
            raise RuntimeError(f"Failed native solve retained at {directory}")
        rows = audit((directory/f"{name}.dat").read_text(), context, cases, stiffness, legs)
        report["runs"][name] = {"basis": rows,
            "scenarios": combine(rows, cases, nodes) if all(r["passed"] for r in rows) else []}
        print(size, extension, name, "passed", all(r["passed"] for r in rows), flush=True)
        unchanged(sources)
    report["passed"] = all(r["passed"] for run in report["runs"].values() for r in run["basis"])
    report["artifact_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    (directory/"report.json").write_text(json.dumps(report, allow_nan=False)+"\n")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "x:gz") as archive:
        for path in sorted(directory.iterdir()):
            archive.add(path, arcname=path.name)
    return report["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("size", choices=("2x6", "2x8", "2x10", "2x12"))
    parser.add_argument("--extension", type=float, choices=(0., 150., 300.), default=300.)
    parser.add_argument("--mesh-size", type=float, default=40.)
    parser.add_argument("--leg-modulus", type=float, default=7000.)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not run(args.size, args.extension, args.mesh_size, args.output, args.leg_modulus):
        raise SystemExit("Native numerical gates failed; do not use scenario results")
