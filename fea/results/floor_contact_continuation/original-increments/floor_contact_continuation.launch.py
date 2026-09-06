"""Temporary lateral floor-node preload guides, then two entirely unpinned steps."""
import argparse
import hashlib
import json
import math
import subprocess
import tempfile
import time
from pathlib import Path

from fea.floor_contact import (
    FACES,
    SOURCE,
    deck,
    floor_faces,
    integrated_weights,
    mesh,
    node_set,
)
from fea.floor_contact_recovery import validate_context
from fea.floor_contact_results import blocks, cross


def continuation_deck(base, groups, feet):
    model, gravity, loaded = base.split("*STEP,NLGEOM,INC=200\n")
    model = model.replace("UNPINNED FLOOR CONTACT FEASIBILITY", "TEMPORARY XY GUIDED PRELOAD; FULL RELEASE BEFORE FREE GRAVITY AND LOAD")
    model = model.replace("*BOUNDARY\n", "\n".join(node_set("PRELOAD_GUIDE", feet))+"\n*BOUNDARY\nPRELOAD_GUIDE,1,2,0\n", 1)
    release = "*BOUNDARY,OP=NEW\n"+"".join(f"GROUND_{name},1,3,0\n" for name in groups)
    output = "*NODE PRINT,NSET=PRELOAD_GUIDE\nRF\n*CONTACT PRINT\nCDIS,CSTR\n"
    for name in groups:
        output += f"*CONTACT PRINT,SLAVE=SLAVE_{name},MASTER=MASTER_{name}\nCF,CFN,CFS\n"
    steps = (gravity, release+gravity, loaded)
    return model+"".join("*STEP,NLGEOM,INC=200\n"+step.replace("*END STEP\n", output+"*END STEP\n") for step in steps)


def audit_three(data, nodes, elements, groups, record):
    weights = {int(n): v for n, v in record["nodal_volume_mm3"].items()}
    if weights.keys() != nodes.keys() or not all(map(math.isfinite, weights.values())) or not math.isfinite(sum(weights.values())) or sum(weights.values()) <= 0:
        raise ValueError("Invalid gravity context")
    parsed = blocks(data)
    output = []
    for endpoint, load in ((1., 0.), (2., 0.), (3., 1200.)):
        u = parsed.get(("displacements", "WOODN", endpoint), {})
        guide = parsed.get(("forces", "PRELOAD_GUIDE", endpoint), {})
        if u.keys() != nodes.keys() or guide.keys() != set(record["guide_nodes"]):
            raise ValueError(f"Incomplete accepted endpoint {endpoint}")
        positions = {n: tuple(x+dx for x, dx in zip(xyz, u[n], strict=True)) for n, xyz in nodes.items()}
        forces, patches = [], {}
        for name, xyz in record["ground_nodes"].items():
            xyz = {int(n): p for n, p in xyz.items()}
            reactions = parsed.get(("forces", "GROUND_"+name, endpoint), {})
            if reactions.keys() != xyz.keys():
                raise ValueError(f"Incomplete ground {name} at {endpoint}")
            forces += [(xyz[n], v) for n, v in reactions.items()]
            total = [sum(v[i] for v in reactions.values()) for i in range(3)]
            if total[2] < -.1 or math.hypot(*total[:2]) > .3*max(0, total[2])+.1:
                raise ValueError("Necessary aggregate compression/friction bound failed")
            feet = {elements[e][i] for e, face in groups[name] for i in FACES[face-1]}
            gaps = [positions[n][2] for n in feet]
            patches[name] = {"reaction_n": total, "physical_gap_mm": [min(gaps), max(gaps)]}
        if endpoint == 1:
            forces += [(positions[n], (v[0], v[1], 0.)) for n, v in guide.items()]
        elif max(abs(v[i]) for v in guide.values() for i in (0, 1)) > .001:
            raise ValueError("Released guide nodes report nonzero lateral external force")
        forces += [(positions[n], (0., 0., -v*6e-10*9806.65)) for n, v in weights.items()]
        top = record["load_nodes"]
        forces += [(positions[n], (0., 0., -load/len(top))) for n in top]
        force = [sum(v[i] for _, v in forces) for i in range(3)]
        moment = [sum(cross(p, v)[i] for p, v in forces) for i in range(3)]
        if not all(map(math.isfinite, force+moment)) or max(map(abs, force)) > .1 or max(map(abs, moment)) > 1:
            raise ValueError(f"Deformed equilibrium failed at {endpoint}: {force}, {moment}")
        output.append({"time": endpoint, "temporary_guides_active": endpoint == 1, "load_n": load,
                       "force_residual_n": force, "moment_residual_nmm": moment, "patches": patches,
                       "guide_lateral_resultant_n": [sum(v[i] for v in guide.values()) for i in range(2)]})
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=600)
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("Positive finite runtime required")
    prepared = Path("fea/generated/floor-contact/input.json")
    info = json.loads(prepared.read_text())
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    validate_context(info, summary, digest(SOURCE))
    if any(digest(Path(p)) != h for p, h in info["geometry_source_sha256"].items()):
        raise ValueError("Frozen CAD changed")
    nodes, elements = mesh(SOURCE.read_text())
    groups = floor_faces(nodes, elements)
    weights = integrated_weights(elements, nodes)
    volume = sum(weights.values())
    centre = [sum(v*nodes[n][i] for n, v in weights.items())/volume for i in range(3)]
    if abs(volume/info["cad_volume_mm3"]-1) > .001 or math.dist(centre, info["cad_centre_mm"]) > 1:
        raise ValueError("Integrated mass/CG differs from CAD")
    feet = sorted({elements[e][i] for faces in groups.values() for e, face in faces for i in FACES[face-1]})
    base, ground = deck(nodes, elements, groups, summary["load_nodes"], .3, 10000)
    text = continuation_deck(base, groups, feet)
    directory = Path(tempfile.mkdtemp(prefix="continuation-xy-", dir="fea/generated"))
    job = directory/"continuation"
    job.with_suffix(".inp").write_text(text)
    inputs = (SOURCE, SOURCE.with_suffix(".json"), prepared, Path(__file__), Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py"), Path("fea/floor_contact_recovery.py"))
    record = dict(info, guide_nodes=feet, ground_nodes=ground, nodal_volume_mm3=weights,
                  load_nodes=summary["load_nodes"], mesh_volume_mm3=volume, mesh_centre_mm=centre,
                  mu=.3, normal_penalty_n_mm3=10000, tangent_penalty_n_mm3=100,
                  prelaunch_sha256={str(p): digest(p) for p in inputs},
                  deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  baseline_deck_sha256=hashlib.sha256(base.encode()).hexdigest(),
                  max_seconds=args.max_seconds, status="RUNNING; TEMPORARY GUIDED PRELOAD IS NOT AN ACCEPTED BOARD SOLUTION",
                  assumptions="Step1 actual floor nodes XY fixed,Z free; Step2 OP=NEW retains ground only; Step3 original1200N load; no final guides/pins/springs/damping")
    job.with_suffix(".json").write_text(json.dumps(record, indent=2)+"\n")
    print(f"Evidence: {directory}", flush=True)
    started = time.monotonic()
    with job.with_suffix(".log").open("w") as log:
        try:
            result = subprocess.run(["ccx", "-i", job.name], cwd=directory, stdout=log, stderr=subprocess.STDOUT, timeout=args.max_seconds, check=False)
            record["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            record["exit_code"] = -999
            record["runtime_stop"] = "Bounded timeout; not physical instability evidence"
    record["elapsed_seconds"] = time.monotonic()-started
    log = job.with_suffix(".log").read_text()
    record["status"] = "UNRESOLVED; NO ACCEPTED FREE BOARD SOLUTION"
    if record["exit_code"] == 0 and "*ERROR" not in log.upper():
        try:
            if digest(job.with_suffix(".inp")) != record["deck_sha256"]:
                raise ValueError("Launched deck changed")
            record["audited_steps"] = audit_three(job.with_suffix(".dat").read_text(), nodes, elements, groups, record)
            record["status"] = "THREE EQUILIBRIUM-AUDITED STEPS; LOCAL CONTACT AND HISTORY-SENSITIVITY AUDITS REQUIRED"
        except (ValueError, FileNotFoundError) as error:
            record["audit_error"] = str(error)
    record["output_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.suffix in (".log", ".dat", ".sta", ".cvg", ".frd")}
    job.with_suffix(".json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_seconds", "exit_code")}), flush=True)


if __name__ == "__main__":
    main()
