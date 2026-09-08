"""Coupled leg/rim and gusset point-connector sensitivity, fixed floor retained."""
import json
import math
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path

from fea import coupled_gussets as base
from fea.floor_contact_results import blocks, cross
from fea.prescribed_tet_control import IMAGE
from fea.solve_easy_frame import digest
from fea.timber_asymmetric import unchanged

MAP = Path("fea/results/leg-connector-map.json")
OUTPUT = Path("fea/results/coupled-leg-release.tar.gz")
GATES = {"leg_force_n": .02, "leg_moment_nmm": 10., "leg_constraint_mm": 1e-5}
LIMITS = ("Leg-to-rim/panel and gusset bonds released; paired leg plies and other frame bonds remain. "
          "XYZ-fixed floor, no gravity/contact, isotropic wood, uncalibrated bilateral point springs. "
          "Conditional sensitivity, NOT physical connection qualification.")


def prepare():
    nodes, elements, points, cases, sources, _ = base.prepare()
    mapping = json.loads(MAP.read_text())
    unchanged(mapping["source_sha256"])
    for name, value in mapping["source_sha256"].items():
        if name in sources and sources[name] != value:
            raise ValueError("Conflicting leg source")
        sources[name] = value
    sources[str(MAP)] = digest(MAP)
    sources["fea/coupled_leg_release.py"] = digest("fea/coupled_leg_release.py")
    remaps = {}
    for side, leg in mapping["legs"].items():
        selected = set(leg["element_ids"])
        owned = {n for e in selected for n in elements[e]}
        shared = owned & {n for e, ids in elements.items() if e not in selected for n in ids}
        if shared != set(leg["shared_nodes"]) or shared & set(leg["floor_nodes"]):
            raise ValueError("Leg release interface differs or reaches floor")
        first = max(nodes)+1
        remap = {n: first+i for i, n in enumerate(sorted(shared))}
        nodes.update({new: nodes[old] for old, new in remap.items()})
        for e in selected:
            elements[e] = tuple(remap.get(n, n) for n in elements[e])
        owned = {n for e in selected for n in elements[e]}
        if owned & {n for e, ids in elements.items() if e not in selected for n in ids}:
            raise ValueError("Leg remains bonded outside its paired plies")
        for name, point in leg["points"].items():
            # Reuse the verified two-sided connector deck's internal field name;
            # these released-side nodes belong to a LEG, not a gusset.
            points[name] = {**point, "gusset_nodes": [remap[n] for n in point["nodes"]]}
        remaps[side] = remap
    unchanged(sources)
    return nodes, elements, points, cases, sources, mapping["legs"], remaps


def audit(data, context, cases, stiffness, legs):
    gusset_context = {**context, "connections": {n: p for n, p in context["connections"].items() if n.startswith("timber_base_")}}
    results = base.audit(data, gusset_context, cases, stiffness)
    parsed = blocks(data)
    for time, row in enumerate(results, 1):
        u, rf = parsed["displacements", "AUDIT", float(time)], parsed["forces", "FEET", float(time)]
        forces, errors, balances, floor_wrenches = {}, [], {}, {}
        for name, p in context["connections"].items():
            if not name.startswith("analysis_leg_wall_bolt_"):
                continue
            for virtual, ids in ((p["parent_point"], p["nodes"]), (p["gusset_point"], p["gusset_nodes"])):
                expected = [math.fsum(w*u[n][i] for n, w in zip(ids, p["weights"], strict=True)) for i in range(3)]
                errors.append(math.dist(expected, u[virtual]))
            forces[name] = [stiffness*(u[p["parent_point"]][i]-u[p["gusset_point"]][i]) for i in range(3)]
        for side, leg in legs.items():
            feet = leg["floor_nodes"]
            moments = [cross(context["nodes"][n], rf[n]) for n in feet]
            floor = [math.fsum(rf[n][i] for n in feet) for i in range(3)]+[math.fsum(m[i] for m in moments) for i in range(3)]
            names = [n for n in forces if context["connections"][n]["side"] == side]
            moments = [cross(context["connections"][n]["point_mm"], forces[n]) for n in names]
            transfer = [math.fsum(forces[n][i] for n in names) for i in range(3)]+[math.fsum(m[i] for m in moments) for i in range(3)]
            balances[side] = [a+b for a, b in zip(floor, transfer, strict=True)]
            floor_wrenches[side] = floor
        row.update(leg_connector_force_on_leg_n=forces, leg_floor_wrench_n_nmm=floor_wrenches,
                   leg_residual_n_nmm=balances, maximum_leg_constraint_error_mm=max(errors))
        row["passed"] &= (max(errors) <= GATES["leg_constraint_mm"] and
                          all(max(map(abs, r[:3])) <= GATES["leg_force_n"] and max(map(abs, r[3:])) <= GATES["leg_moment_nmm"] for r in balances.values()))
    return results


def combine(results, cases, nodes):
    rows = base.combine(results, cases, nodes)
    for row in rows:
        basis = [r for r in results if r["hold"] == row["hold"]]
        row["leg_connector_force_on_leg_n"] = {
            name: [math.fsum(c*r["leg_connector_force_on_leg_n"][name][i] for c, r in zip(row["basis_coefficients"], basis, strict=True))
                   for i in range(3)] for name in basis[0]["leg_connector_force_on_leg_n"]}
    return rows


def run():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite leg-release evidence")
    nodes, elements, points, cases, sources, legs, remaps = prepare()
    directory = Path(tempfile.mkdtemp(prefix="coupled-legs-", dir="fea/generated")).resolve()
    report = {"limits": LIMITS, "gates": GATES, "inherited_gates": base.GATES, "image": IMAGE,
              "source_sha256": sources, "leg_duplicate_nodes": remaps, "runs": {}}
    print(directory, flush=True)
    for stiffness in base.STIFFNESSES:
        name = f"k{int(stiffness)}"
        text, context = base.deck(nodes, elements, points, cases, stiffness)
        text = text.replace("** "+base.LIMITS, "** "+LIMITS, 1)
        (directory/f"{name}.inp").write_text(text)
        command = ["docker", "run", "--rm", "--network=none", "--cpus=2", "--memory=6g",
                   "--read-only", "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m", "--user", f"{os.getuid()}:{os.getgid()}",
                   "-e", "OMP_NUM_THREADS=2", "-v", f"{directory}:/work", "-w", "/work", IMAGE, "ccx", "-i", name]
        with (directory/f"{name}.log").open("w") as log:
            done = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=False)
        if done.returncode or "*ERROR" in (directory/f"{name}.log").read_text().upper():
            raise RuntimeError(f"Failed leg trial retained at {directory}")
        results = audit((directory/f"{name}.dat").read_text(), context, cases, stiffness, legs)
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
