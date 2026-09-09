"""New straight legs coupled to the unchanged frame by nominal point springs.

Comparison only: fixed XYZ floor, no gravity/contact, isotropic materials and
uncalibrated linear connectors. No transfer of a previous joint force/rating.
"""
import argparse
import copy
import json
import math
import os
import re
import subprocess
import tarfile
import tempfile
from functools import cache
from pathlib import Path

from fea import coupled_gussets as base
from fea.floor_contact import FACES, node_set
from fea.floor_contact_results import blocks, cross
from fea.gusset_connector_trial import point_weights
from fea.leg_connector_map import OUTPUT as LEG_MAP
from fea.prescribed_tet_control import IMAGE
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import mesh_text, unchanged

GATES = {"leg_force_n": .02, "leg_moment_nmm": 10., "constraint_mm": 1e-5,
         "relative_energy_work": .001}
LIMITS = ("Changed straight leg geometry and bolt group; remaining frame mesh unchanged. "
          "Legs/gussets use uncalibrated bilateral point springs, other wood interfaces ideal bonds. "
          "Fixed XYZ floor, no gravity/contact/bolt holes/strength or construction approval. "
          "Isotropic E7000MPa frame; leg E separately recorded, nu0.3. New leg meshes independent. "
          "No inherited compliance bound against a different geometry.")


@cache
def parent_inputs():
    return base.prepare()


def prepare(size, extension=0., mesh_size=40.):
    from fea.lumber_leg_mesh import build
    from mini_moonboard import lumber_leg_frame as model

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
    for path in (str(LEG_MAP), "fea/lumber_leg_response.py", "fea/lumber_leg_mesh.py",
                 "mini_moonboard/lumber_leg_frame.py", "fea/solve_bearing_frame.py", "uv.lock"):
        sources.setdefault(path, digest(path))
    unchanged(sources)
    return nodes, elements, points, cases, sources, legs


def deck(nodes, elements, points, cases, stiffness, legs, leg_modulus=7000.):
    if stiffness not in base.STIFFNESSES or not math.isfinite(leg_modulus) or leg_modulus <= 0:
        raise ValueError("Select declared spring stiffness and a positive finite leg modulus")
    nodes = dict(nodes)
    connections = {}
    for name, p in points.items():
        first, second = max(nodes)+1, max(nodes)+2
        nodes[first] = nodes[second] = p["point_mm"]
        connections[name] = {**p, "parent_point": first, "gusset_point": second}
    leg_elements = {e for leg in legs.values() for e in leg["element_ids"]}
    lines = ["** "+LIMITS, mesh_text(nodes, elements)]
    for name, ids, modulus in (("FRAME", set(elements)-leg_elements, 7000.),
                                ("LEGS", leg_elements, leg_modulus)):
        lines += [line.replace("NSET", "ELSET") for line in node_set(name, sorted(ids))]
        lines += [f"*MATERIAL,NAME={name}", "*ELASTIC", f"{modulus},0.3",
                  f"*SOLID SECTION,ELSET={name},MATERIAL={name}"]
    eid = max(elements)
    for p in connections.values():
        for axis in range(1, 4):
            eid += 1
            lines += [f"*ELEMENT,TYPE=SPRING2,ELSET=SP{eid}",
                      f"{eid},{p['parent_point']},{p['gusset_point']}",
                      f"*SPRING,ELSET=SP{eid}", f"{axis},{axis}", str(stiffness)]
            for virtual, ids, weights in ((p["parent_point"], p["nodes"], p["weights"]),
                    (p["gusset_point"], p["gusset_nodes"], p["other_weights"])):
                if len(ids) != 6 or len(weights) != 6 or abs(sum(weights)-1.) > 1e-9:
                    raise ValueError("Quadratic face coupling required")
                target = [math.fsum(w*nodes[n][i] for n, w in zip(ids, weights, strict=True)) for i in range(3)]
                if math.dist(target, nodes[virtual]) > 1e-6:
                    raise ValueError("Connector interpolation loses rigid-motion consistency")
                terms = [(virtual, axis, 1.)]+[(n, axis, -w) for n, w in zip(ids, weights, strict=True)]
                lines += ["*EQUATION", "7"]+[",".join(f"{n},{a},{w:.15g}" for n, a, w in terms[i:i+4]) for i in (0, 4)]
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    output = set(feet) | {c["node"] for c in cases} | {n for leg in legs.values() for n in leg["nodes"]}
    for p in connections.values():
        output.update(p["nodes"]+p["gusset_nodes"]+[p["parent_point"], p["gusset_point"]])
    lines += node_set("FEET", feet)+node_set("AUDIT", sorted(output))
    for case in cases:
        lines += ["*STEP", "*STATIC", "*BOUNDARY,OP=NEW", "FEET,1,3,0.", "*CLOAD,OP=NEW"]
        lines += [f"{case['node']},{i},{f:.9f}" for i, f in enumerate(case["force_n"], 1) if f]
        lines += ["*NODE PRINT,NSET=AUDIT", "U", "*NODE PRINT,NSET=FEET", "RF",
                  "*EL PRINT,ELSET=TIMBER,TOTALS=ONLY", "ELSE", "*END STEP"]
    return "\n".join(lines)+"\n", {"nodes": nodes, "connections": connections,
                                   "feet": feet, "output": sorted(output)}


def audit(data, context, cases, stiffness, legs):
    # The original bonded geometry is different, hence not a compliance bound.
    checks = [{**case, "bonded_load_work_nmm": 0.} for case in cases]
    subset = {**context, "connections": {n: p for n, p in context["connections"].items()
                                         if n.startswith("timber_base_")}}
    result = base.audit(data, subset, checks, stiffness)
    parsed = blocks(data)
    matches = re.findall(r"total internal energy for set TIMBER and time\s+(\S+)\s+([\d.Ee+\-]+)", data)
    energy = {float(t): float(v) for t, v in matches}
    if len(matches) != len(cases) or set(energy) != set(map(float, range(1, len(cases)+1))):
        raise ValueError("Missing native wood energy endpoints")
    for time, row in enumerate(result, 1):
        u = parsed["displacements", "AUDIT", float(time)]
        rf = parsed["forces", "FEET", float(time)]
        forces, errors, spring_energy = {}, [], 0.
        for name, p in context["connections"].items():
            delta = [u[p["parent_point"]][i]-u[p["gusset_point"]][i] for i in range(3)]
            spring_energy += .5*stiffness*sum(v*v for v in delta)
            if not name.startswith("lumber_leg_bolt_"):
                continue
            forces[name] = [stiffness*v for v in delta]
            for virtual, ids, weights in ((p["parent_point"], p["nodes"], p["weights"]),
                    (p["gusset_point"], p["gusset_nodes"], p["other_weights"])):
                expected = [math.fsum(w*u[n][i] for n, w in zip(ids, weights, strict=True)) for i in range(3)]
                errors.append(math.dist(expected, u[virtual]))
        balances, floors = {}, {}
        for side, leg in legs.items():
            floors[side] = [math.fsum(rf[n][i] for n in leg["floor_nodes"]) for i in range(3)]
            floors[side] += [math.fsum(cross(context["nodes"][n], rf[n])[i]
                                    for n in leg["floor_nodes"]) for i in range(3)]
            names = [n for n in forces if context["connections"][n]["side"] == side]
            transfer = [math.fsum(forces[n][i] for n in names) for i in range(3)]
            transfer += [math.fsum(cross(context["connections"][n]["point_mm"], forces[n])[i]
                                  for n in names) for i in range(3)]
            balances[side] = [a+b for a, b in zip(floors[side], transfer, strict=True)]
        energy_error = abs(2*(energy[float(time)]+spring_energy)/row["load_work_nmm"]-1)
        row.update(leg_connector_force_on_leg_n=forces, leg_floor_wrench_n_nmm=floors,
            leg_residual_n_nmm=balances, maximum_leg_constraint_error_mm=max(errors),
            leg_maximum_basis_displacement_mm={side: max(math.hypot(*u[n]) for n in leg["nodes"])
                                                for side, leg in legs.items()},
            native_wood_energy_nmm=energy[float(time)], spring_energy_nmm=spring_energy,
            relative_energy_work_error=energy_error)
        row["passed"] &= (max(errors) <= GATES["constraint_mm"] and energy[float(time)] > 0
            and energy_error <= GATES["relative_energy_work"]
            and all(max(map(abs, r[:3])) <= GATES["leg_force_n"]
                    and max(map(abs, r[3:])) <= GATES["leg_moment_nmm"] for r in balances.values()))
    return result


def combine(results, cases, nodes):
    rows = base.combine(results, cases, nodes)
    for row in rows:
        basis = [r for r in results if r["hold"] == row["hold"]]
        for field in ("leg_connector_force_on_leg_n", "leg_floor_wrench_n_nmm"):
            row[field] = {name: [math.fsum(c*r[field][name][i]
                for c, r in zip(row["basis_coefficients"], basis, strict=True))
                for i in range(len(basis[0][field][name]))] for name in basis[0][field]}
    return rows


def run(size, extension, mesh_size, output, leg_modulus=7000.):
    if output.exists():
        raise FileExistsError("Refusing to overwrite native evidence")
    nodes, elements, points, cases, sources, legs = prepare(size, extension, mesh_size)
    directory = Path(tempfile.mkdtemp(prefix="lumber-leg-response-", dir="fea/generated")).resolve()
    report = {"stock": size, "extension_mm": extension, "mesh_size_mm": mesh_size,
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
    parser.add_argument("--extension", type=float, choices=(0., 150., 300.), default=0.)
    parser.add_argument("--mesh-size", type=float, default=40.)
    parser.add_argument("--leg-modulus", type=float, default=7000.)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not run(args.size, args.extension, args.mesh_size, args.output, args.leg_modulus):
        raise SystemExit("Native numerical gates failed; do not use scenario results")
