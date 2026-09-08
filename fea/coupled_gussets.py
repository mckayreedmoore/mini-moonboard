"""Coupled wide-frame gusset-release sensitivity; other bonds/fixed floor remain."""
import gzip
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea.floor_contact import mesh, node_set
from fea.floor_contact_results import blocks, cross
from fea.gusset_connector_trial import STIFFNESSES
from fea.gusset_connector_trial import prepare as point_inputs
from fea.gusset_recovery import MAP
from fea.prescribed_tet_control import IMAGE
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import BASIS, HOLDS, mesh_text, scenarios, unchanged
from fea.wide_asymmetric import preparation

OUTPUT = Path("fea/results/coupled-gussets.tar.gz")
GATES = {"global_force_n": .1, "global_moment_nmm": 1., "gusset_force_n": .02,
         "gusset_moment_nmm": 5., "constraint_mm": 1e-6, "bonded_compliance_tolerance_mm_n": .01}
LIMITS = ("Only gusset shared nodes released; other ideal wood bonds and XYZ-fixed floor remain. "
          "No gravity, header contact, holes, anisotropy or physical bolt stiffness. "
          "Point-connector sensitivity only, not actual demand or resistance qualification.")


def prepare():
    info, parents = preparation()
    nodes, elements = mesh(parents["A12"])
    _, _, points, _, point_sources = point_inputs()
    mapping = json.loads(MAP.read_text())
    sources = dict(info["source_sha256"])
    for name, value in point_sources.items():
        if name in sources and sources[name] != value:
            raise ValueError("Conflicting source provenance")
        sources[name] = value
    sources["fea/coupled_gussets.py"] = digest("fea/coupled_gussets.py")
    remaps = {}
    for side, gusset in mapping["gussets"].items():
        selected = set(gusset["element_ids"])
        actual_shared = {n for e in selected for n in elements[e]} & {n for e, ids in elements.items() if e not in selected for n in ids}
        if actual_shared != set(gusset["shared_nodes"]):
            raise ValueError("Shared interface topology changed")
        first = max(nodes)+1
        remap = {n: first+i for i, n in enumerate(sorted(actual_shared))}
        nodes.update({new: nodes[old] for old, new in remap.items()})
        for e in selected:
            elements[e] = tuple(remap.get(n, n) for n in elements[e])
        owned = {n for e in selected for n in elements[e]}
        if owned & {n for e, ids in elements.items() if e not in selected for n in ids}:
            raise ValueError("Gusset remains bonded to another member")
        remaps[side] = remap
    for p in points.values():
        p["gusset_nodes"] = [remaps[p["side"]][n] for n in p["nodes"]]
        if any(nodes[a] != nodes[b] for a, b in zip(p["nodes"], p["gusset_nodes"], strict=True)):
            raise ValueError("Release changes coordinates")
    cases = []
    for hold in HOLDS:
        path = Path(f"fea/results/wide-asymmetric/{hold}.json.gz")
        parent = json.loads(gzip.decompress(path.read_bytes()))
        sources[str(path)] = digest(path)
        for index, basis in enumerate(BASIS):
            original = parent["basis"][index]
            if original["force_n"] != basis["force_n"]:
                raise ValueError("Parent basis differs")
            force = basis["force_n"]
            cases.append({"hold": hold, "axis": basis["name"], "node": info["mapping"][hold]["node"],
                          "force_n": force, "bonded_load_work_nmm": sum(f*u for f, u in zip(force, original["loaded_displacement_mm"], strict=True))})
    unchanged(sources)
    return nodes, elements, points, cases, sources, remaps


def deck(nodes, elements, points, cases, stiffness):
    if stiffness not in STIFFNESSES:
        raise ValueError("Unplanned stiffness")
    nodes = dict(nodes)
    connections = {}
    for name, p in points.items():
        parent, gusset = max(nodes)+1, max(nodes)+2
        nodes[parent] = nodes[gusset] = p["point_mm"]
        connections[name] = {**p, "parent_point": parent, "gusset_point": gusset}
    lines = ["** "+LIMITS, mesh_text(nodes, elements), "*MATERIAL,NAME=MAT", "*ELASTIC", "7000.,0.3",
             "*SOLID SECTION,ELSET=TIMBER,MATERIAL=MAT"]
    eid = max(elements)
    for p in connections.values():
        for axis in range(1, 4):
            eid += 1
            lines += [f"*ELEMENT,TYPE=SPRING2,ELSET=SP{eid}", f"{eid},{p['parent_point']},{p['gusset_point']}",
                      f"*SPRING,ELSET=SP{eid}", f"{axis},{axis}", f"{stiffness:.1f}"]
            for virtual, ids in ((p["parent_point"], p["nodes"]), (p["gusset_point"], p["gusset_nodes"])):
                terms = [(virtual, axis, 1.)]+[(n, axis, -w) for n, w in zip(ids, p["weights"], strict=True)]
                lines += ["*EQUATION", "7"]+[",".join(f"{n},{a},{w:.15g}" for n, a, w in terms[i:i+4]) for i in (0, 4)]
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    output = set(feet) | {c["node"] for c in cases}
    for p in connections.values():
        output.update(p["nodes"]+p["gusset_nodes"]+[p["parent_point"], p["gusset_point"]])
    lines += node_set("FEET", feet)+node_set("AUDIT", sorted(output))
    for case in cases:
        lines += ["*STEP", "*STATIC", "*BOUNDARY,OP=NEW", "FEET,1,3,0.", "*CLOAD,OP=NEW"]
        lines += [f"{case['node']},{i},{f:.9f}" for i, f in enumerate(case["force_n"], 1) if f]
        lines += ["*NODE PRINT,NSET=AUDIT", "U", "*NODE PRINT,NSET=FEET", "RF", "*END STEP"]
    return "\n".join(lines)+"\n", {"nodes": nodes, "connections": connections, "feet": feet, "output": sorted(output)}


def audit(data, context, cases, stiffness):
    nodes, connections = context["nodes"], context["connections"]
    parsed = blocks(data)
    if set(parsed) != {(kind, name, float(t)) for t in range(1, len(cases)+1)
                       for kind, name in (("displacements", "AUDIT"), ("forces", "FEET"))}:
        raise ValueError("Incomplete coupled endpoints")
    results = []
    for time, case in enumerate(cases, 1):
        u, rf = parsed["displacements", "AUDIT", float(time)], parsed["forces", "FEET", float(time)]
        if set(u) != set(context["output"]) or set(rf) != set(context["feet"]):
            raise ValueError("Incomplete coupled node output")
        force = [math.fsum(v[i] for v in rf.values()) for i in range(3)]
        moments = [cross(nodes[n], v) for n, v in rf.items()]
        reaction = force+[math.fsum(v[i] for v in moments) for i in range(3)]
        applied = case["force_n"]+cross(nodes[case["node"]], case["force_n"])
        residual = [a+b for a, b in zip(reaction, applied, strict=True)]
        errors = [math.hypot(*u[n]) for n in context["feet"]]
        forces = {}
        for name, p in connections.items():
            for virtual, ids in ((p["parent_point"], p["nodes"]), (p["gusset_point"], p["gusset_nodes"])):
                expected = [math.fsum(w*u[n][i] for n, w in zip(ids, p["weights"], strict=True)) for i in range(3)]
                errors.append(math.dist(expected, u[virtual]))
            forces[name] = [stiffness*(u[p["parent_point"]][i]-u[p["gusset_point"]][i]) for i in range(3)]
        gusset_residuals = {}
        for side in ("left", "right"):
            names = [n for n, p in connections.items() if p["side"] == side]
            torques = [cross(connections[n]["point_mm"], forces[n]) for n in names]
            gusset_residuals[side] = [math.fsum(forces[n][i] for n in names) for i in range(3)]+[math.fsum(v[i] for v in torques) for i in range(3)]
        work = sum(f*v for f, v in zip(case["force_n"], u[case["node"]], strict=True))
        passed = (max(map(abs, residual[:3])) <= GATES["global_force_n"]
                  and max(map(abs, residual[3:])) <= GATES["global_moment_nmm"]
                  and max(errors) <= GATES["constraint_mm"] and work > 0
                  and work >= case["bonded_load_work_nmm"]-GATES["bonded_compliance_tolerance_mm_n"]
                  and all(max(map(abs, r[:3])) <= GATES["gusset_force_n"]
                          and max(map(abs, r[3:])) <= GATES["gusset_moment_nmm"] for r in gusset_residuals.values()))
        results.append({"hold": case["hold"], "axis": case["axis"], "loaded_displacement_mm": list(u[case["node"]]),
                        "load_work_nmm": work, "reaction_wrench_n_nmm": reaction, "residual_wrench": residual,
                        "connector_force_on_gusset_n": forces, "gusset_residual_n_nmm": gusset_residuals,
                        "maximum_constraint_error_mm": max(errors), "passed": bool(passed)})
    return results


def combine(results, cases, nodes):
    rows = []
    for hold in HOLDS:
        basis = [r for r in results if r["hold"] == hold]
        point = nodes[next(c["node"] for c in cases if c["hold"] == hold)]
        for scenario in scenarios(basis, point):
            forces = {name: [math.fsum(c*r["connector_force_on_gusset_n"][name][i]
                                      for c, r in zip(scenario["basis_coefficients"], basis, strict=True))
                             for i in range(3)] for name in basis[0]["connector_force_on_gusset_n"]}
            rows.append({"hold": hold, **scenario, "connector_force_on_gusset_n": forces})
    return rows


def run():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite coupled evidence")
    nodes, elements, points, cases, sources, remaps = prepare()
    directory = Path(tempfile.mkdtemp(prefix="coupled-gussets-", dir="fea/generated")).resolve()
    report = {"limits": LIMITS, "gates": GATES, "image": IMAGE, "source_sha256": sources,
              "duplicate_nodes": remaps, "points": points, "cases": cases, "runs": {}}
    print(directory, flush=True)
    for stiffness in STIFFNESSES:
        name = f"k{int(stiffness)}"
        text, context = deck(nodes, elements, points, cases, stiffness)
        (directory/f"{name}.inp").write_text(text)
        command = ["docker", "run", "--rm", "--network=none", "--cpus=2", "--memory=6g",
                   "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", f"{os.getuid()}:{os.getgid()}",
                   "-e", "OMP_NUM_THREADS=2", "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", name]
        with (directory/f"{name}.log").open("w") as log:
            done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
        if done.returncode or "*ERROR" in (directory/f"{name}.log").read_text().upper():
            raise RuntimeError(f"Failed coupled run retained at {directory}")
        results = audit((directory/f"{name}.dat").read_text(), context, cases, stiffness)
        report["runs"][name] = {"basis": results, "scenarios": combine(results, cases, nodes) if all(r["passed"] for r in results) else []}
        print(name, "passed", all(r["passed"] for r in results), flush=True)
        unchanged(sources)
    report["passed"] = all(r["passed"] for run in report["runs"].values() for r in run["basis"])
    report["artifact_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.is_file()}
    (directory/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    with tarfile.open(OUTPUT, "x:gz") as archive:
        for p in sorted(directory.iterdir()):
            archive.add(p, arcname=p.name)


if __name__ == "__main__":
    run()
