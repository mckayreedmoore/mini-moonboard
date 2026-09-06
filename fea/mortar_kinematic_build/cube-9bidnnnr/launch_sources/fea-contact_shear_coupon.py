"""Matched penalty/mortar shear coupon; global balance is not local validation."""
import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fea.floor_contact import mesh, node_set
from fea.floor_contact_results import blocks, cross

SOURCE = Path("fea/results/floor_contact/toy_quadratic.inp")
PRELOAD_N = 120.0
TRAVEL_MM = 1.0
MU = .3


def deck(source, formulation, increment, bottom_supported=False):
    if formulation not in ("penalty", "mortar") or increment not in (.25, .125):
        raise ValueError("Only matched penalty/mortar .25/.125 comparisons are defined")
    nodes, elements = mesh(source)
    wood = sorted({n for ids in elements.values() for n in ids})
    ground = sorted(set(nodes)-set(wood))
    support = [n for n in ground if nodes[n][2] == -100.] if bottom_supported else ground
    top = [n for n in wood if nodes[n][2] == 100.]
    foot = [n for n in wood if nodes[n][2] == 0.]
    if len(elements) != 6 or len(ground) != 8 or len(top) != 9 or len(foot) != 9:
        raise ValueError("Expected frozen six-tetrahedron cube topology")
    model = source.split("*STEP,")[0]
    if formulation == "mortar":
        model = model.replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR")
    model = model.replace("GROUND,1,3,0", "SUPPORT,1,3,0")
    model += "\n".join(node_set("TOP", top)+node_set("FOOT", foot)+node_set("SUPPORT", support))
    model += "\n*BOUNDARY\nTOP,1,2,0\n"
    steps = []
    for endpoint in (1, 2):
        lines = ["*STEP,NLGEOM,INC=100", "*STATIC", f"{increment!r},1,1e-6,{increment!r}"]
        if endpoint == 2:
            lines += ["*BOUNDARY", f"TOP,1,1,{TRAVEL_MM!r}"]
        lines += ["*CLOAD,OP=NEW"]+[f"{n},3,{-PRELOAD_N/len(top)!r}" for n in top]
        for name, quantity in (("WOOD", "U"), ("GROUND", "U,RF"), ("TOP", "RF"), ("FOOT", "RF")):
            lines += [f"*NODE PRINT,NSET={name}", quantity]
        lines += ["*NODE FILE", "U,RF", "*CONTACT FILE", "CDIS,CSTR"]
        if formulation == "penalty":
            lines += ["*CONTACT PRINT", "CDIS,CSTR", "*CONTACT PRINT,SLAVE=SLAVE,MASTER=MASTER", "CF,CFN,CFS"]
        lines += ["*END STEP"]
        steps.append("\n".join(lines)+"\n")
    return model+"".join(steps), {"nodes": nodes, "wood": wood, "ground": ground,
                                "top": top, "foot": foot, "support": support}


def audit(data, context, *, preload_n=PRELOAD_N, travel_mm=TRAVEL_MM):
    if any(not math.isfinite(v) or v <= 0 for v in (preload_n, travel_mm)):
        raise ValueError("Positive finite loading context required")
    nodes = {int(n): p for n, p in context["nodes"].items()}
    if not nodes or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in nodes.values()):
        raise ValueError("Invalid coordinates")
    for key in ("wood", "ground", "top", "foot", "support"):
        tags = context[key]
        if not tags or len(tags) != len(set(tags)) or not set(tags) <= nodes.keys():
            raise ValueError("Invalid node context")
    if not set(context["support"]) <= set(context["ground"]):
        raise ValueError("Supports must be ground nodes")
    if (set(context["wood"]) & set(context["ground"]) or
            not (set(context["top"]) | set(context["foot"])) <= set(context["wood"])):
        raise ValueError("Wood, contact, actuator and ground sets are inconsistent")
    parsed, result = blocks(data), []
    for endpoint in (1., 2.):
        u = parsed.get(("displacements", "WOOD", endpoint), {})
        ground = parsed.get(("forces", "GROUND", endpoint), {})
        ground_u = parsed.get(("displacements", "GROUND", endpoint), {})
        top = parsed.get(("forces", "TOP", endpoint), {})
        foot = parsed.get(("forces", "FOOT", endpoint), {})
        for values, key in ((u, "wood"), (ground, "ground"), (ground_u, "ground"), (top, "top"), (foot, "foot")):
            if values.keys() != set(context[key]):
                raise ValueError(f"Incomplete {key} output at {endpoint}")
        positions = {n: tuple(a+b for a, b in zip(nodes[n], v, strict=True)) for n, v in u.items()}
        positions.update({n: tuple(a+b for a, b in zip(nodes[n], v, strict=True)) for n, v in ground_u.items()})
        if not all(math.isfinite(v) for p in positions.values() for v in p):
            raise ValueError("Nonfinite deformed position")
        expected = 0. if endpoint == 1. else travel_mm
        if any(abs(u[n][0]-expected) > 1e-6 or abs(u[n][1]) > 1e-6 for n in top):
            raise ValueError("Actuator displacement does not match prescribed endpoint")
        if any(abs(f[2]+preload_n/len(top)) > 1e-4 for f in top.values()):
            raise ValueError("Free top Z force differs from prescribed CLOAD; output semantics unresolved")
        if any(abs(v) > 1e-9 for n in context["support"] for v in ground_u[n]):
            raise ValueError("Fixed ground support moved")
        forces = [(positions[n], ground[n]) for n in context["support"]]
        # RF includes applied loads: include only constrained actuator X/Y,
        # then count the known free-Z CLOAD once, at its deformed location.
        forces += [(positions[n], (f[0], f[1], -preload_n/len(top))) for n, f in top.items()]
        force = [sum(f[i] for _, f in forces) for i in range(3)]
        moment = [sum(cross(p, f)[i] for p, f in forces) for i in range(3)]
        reaction = [sum(ground[n][i] for n in context["support"]) for i in range(3)]
        if not all(map(math.isfinite, force+moment+reaction)):
            raise ValueError("Nonfinite resultant")
        friction_pass = reaction[2] >= -.1 and math.hypot(*reaction[:2]) <= MU*max(0., reaction[2])+.1
        result.append({"time": endpoint, "force_residual_n": force, "moment_residual_nmm": moment,
                       "ground_reaction_n": reaction, "force_pass": max(map(abs, force)) <= .1,
                       "moment_pass": max(map(abs, moment)) <= 1., "aggregate_friction_pass": friction_pass,
                       "mean_foot_x_displacement_mm": sum(u[n][0] for n in foot)/len(foot),
                       "foot_z_displacement_mm": [min(u[n][2] for n in foot), max(u[n][2] for n in foot)],
                       "ground_top_z_displacement_mm": [ground_u[n][2] for n in ground if nodes[n][2] == 0.],
                       "gap_qualification": "Wood Z displacement is not contact clearance when the ground deforms; local contact geometry remains unaudited",
                       "maximum_free_foot_rf_component_n": max(abs(v) for f in foot.values() for v in f),
                       "top_free_z_rf_n": [f[2] for f in top.values()]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=60.)
    parser.add_argument("--bottom-supported", action="store_true",
                        help="Separate compliant-ground comparison: fix only four bottom ground nodes")
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("Positive finite time limit required")
    parent = Path("fea/generated")
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="contact-shear-", dir=parent))
    shutil.copyfile(__file__, directory/"contact_shear_coupon.launch.py")
    print(directory, flush=True)
    source = SOURCE.read_text()
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for formulation in ("penalty", "mortar"):
        for increment in (.25, .125):
            text, context = deck(source, formulation, increment, args.bottom_supported)
            name = formulation+"_"+str(increment).replace(".", "p")
            job = directory/name
            job.with_suffix(".inp").write_text(text)
            record = dict(context, formulation=formulation, increment=increment, preload_n=PRELOAD_N,
                          travel_mm=TRAVEL_MM, mu=MU, normal_penalty_n_mm3=10000., tangent_penalty_n_mm3=100.,
                          deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                          source_sha256={str(p): digest(p) for p in (SOURCE, Path(__file__), Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py"))},
                          max_seconds=args.max_seconds, status="RUNNING; COUPON ONLY",
                          bottom_supported=args.bottom_supported,
                          assumptions="No gravity; equal nodal top loads total120N; topXY seating guides then1mmX actuator,Y held,Z free; no frame stability inference",
                          local_contact_status="NOT AUDITED; mortar requires separate nodal/weak-law semantics, not penalty DAT assumptions")
            job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
            started = time.monotonic()
            with job.with_suffix(".log").open("w") as log:
                try:
                    run = subprocess.run(["ccx", "-i", name], cwd=directory, stdout=log, stderr=subprocess.STDOUT,
                                         timeout=args.max_seconds, check=False, env=dict(os.environ, OMP_NUM_THREADS="2"))
                    record["exit_code"] = run.returncode
                except subprocess.TimeoutExpired:
                    record["exit_code"] = -999
            record["elapsed_seconds"] = time.monotonic()-started
            record["status"] = "UNRESOLVED SOLVER/OUTPUT; NOT PHYSICAL FAILURE"
            if record["exit_code"] == 0 and "*ERROR" not in job.with_suffix(".log").read_text().upper():
                try:
                    if digest(job.with_suffix(".inp")) != record["deck_sha256"]:
                        raise ValueError("Launched deck changed")
                    record["endpoints"] = audit(job.with_suffix(".dat").read_text(), context)
                    passed = all(s[k] for s in record["endpoints"] for k in ("force_pass", "moment_pass", "aggregate_friction_pass"))
                    record["status"] = "GLOBAL COUPON CHECKS PASS; LOCAL CONTACT NOT VALIDATED" if passed else "GLOBAL COUPON AUDIT REJECTED; NOT FRAME FAILURE"
                    if formulation == "mortar" and not args.bottom_supported:
                        record["status"] = "MORTAR REACTION OUTPUT SEMANTICS UNVERIFIED; NO GLOBAL OR LOCAL PASS"
                        record["reaction_output_note"] = "DAT ground RF may omit mortar forces while free slave RF includes them; reported residuals apply the penalty external-force interpretation and cannot establish mortar equilibrium"
                    elif formulation == "mortar":
                        record["reaction_output_note"] = "Only noncontact bottom SPC reactions and top actuator XY enter external balance; free master/slave RF are excluded. This validates endpoint external balance on this compliant-ground coupon only, not the local mortar law or whole frame"
                except (ValueError, FileNotFoundError) as error:
                    record["audit_error"] = str(error)
            record["output_sha256"] = {p.name: digest(p) for p in directory.glob(name+".*") if p.suffix in (".dat", ".frd", ".log", ".sta", ".cvg")}
            job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
            print(name, record["status"], flush=True)


if __name__ == "__main__":
    main()
