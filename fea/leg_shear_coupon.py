"""Actual inclined-leg shear transfer coupon; no gravity and no frame rating."""
import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from fea.contact_shear_coupon import SOURCE as CUBE_SOURCE
from fea.contact_shear_coupon import audit
from fea.contact_shear_coupon import deck as cube_deck
from fea.floor_contact import FACES, SOURCE, node_set
from fea.floor_contact import deck as floor_deck
from fea.foot_contact_repro import extract, geometry_audit

PRELOAD_N = 1200.


def deck(source, formulation, increment):
    nodes, elements, groups, volume = extract(source)
    geometry_audit(nodes, elements, groups)
    if len(elements) != 968 or len(groups["LEFT"]) != 16:
        raise ValueError("Expected original 968-tetrahedron actual left leg")
    top = [n for n, xyz in nodes.items() if xyz[2] > max(p[2] for p in nodes.values())-60]
    foot = sorted({elements[e][i] for e, f in groups["LEFT"] for i in FACES[f-1]})
    base, ground = floor_deck(nodes, elements, groups, top, .3, 10000)
    model = base.split("*STEP,")[0]
    if formulation == "mortar":
        model = model.replace("TYPE=SURFACE TO SURFACE", "TYPE=MORTAR")
    support = [n for n, xyz in ground["LEFT"].items() if xyz[2] == -100.]
    model = model.replace("GROUND_LEFT,1,3,0", "SUPPORT,1,3,0")
    model += "\n".join(node_set("SUPPORT", support)+node_set("WOOD", nodes)+
                       node_set("GROUND", ground["LEFT"])+node_set("FOOT", foot))
    model += "\n*BOUNDARY\nTOP,1,2,0\n"
    # Reuse the tested two-step actuator and output schedule, replacing only
    # cube-specific load rows and contact-pair names with actual-leg targets.
    template, _ = cube_deck(CUBE_SOURCE.read_text(), formulation, increment, True)
    steps = "*STEP,"+template.split("*STEP,", 1)[1]
    load = "*CLOAD,OP=NEW\n"+"".join(f"{n},3,{-PRELOAD_N/len(top)!r}\n" for n in top)
    steps = re.sub(r"\*CLOAD,OP=NEW\n[^*]+", lambda _: load, steps)
    steps = steps.replace("SLAVE=SLAVE,MASTER=MASTER", "SLAVE=SLAVE_LEFT,MASTER=MASTER_LEFT")
    return model+steps, {"nodes": nodes|ground["LEFT"], "wood": list(nodes), "ground": list(ground["LEFT"]),
                         "top": top, "foot": foot, "support": support, "original_volume": volume}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=60.)
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("Positive finite time limit required")
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    if digest(SOURCE) != summary["evidence_sha256"][SOURCE.name]:
        raise ValueError("Frozen frame mesh changed")
    parent = Path("fea/generated")
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="leg-shear-", dir=parent))
    shutil.copyfile(__file__, directory/"leg_shear_coupon.launch.py")
    shutil.copyfile("fea/contact_shear_coupon.py", directory/"contact_shear_coupon.launch.py")
    print(directory, flush=True)
    source = SOURCE.read_text()
    for formulation in ("penalty", "mortar"):
        for increment in (.25, .125):
            text, context = deck(source, formulation, increment)
            name = formulation+"_"+str(increment).replace(".", "p")
            job = directory/name
            job.with_suffix(".inp").write_text(text)
            record = dict(context, formulation=formulation, increment=increment, preload_n=PRELOAD_N,
                          travel_mm=1., mu=.3, normal_penalty_n_mm3=10000., tangent_penalty_n_mm3=100.,
                          max_seconds=args.max_seconds, deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                          source_sha256={str(p): digest(p) for p in (SOURCE, SOURCE.with_suffix(".json"), CUBE_SOURCE, Path(__file__), Path("fea/contact_shear_coupon.py"), Path("fea/foot_contact_repro.py"), Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py"))},
                          status="RUNNING; ACTUAL LEG COUPON ONLY",
                          assumptions="Original968C3D10leg/16floorfaces;1200Nupper60mmnodalpreload,no gravity;upperXYseating then1mmX,Yheld,Zfree;groundC3D8E7000MPa,nu.3,depth100mm,footbbox+100mmonallsides;bottom4SPConly;notfreeboard",
                          local_contact_status="NOT VALIDATED; active/weak-law and actual-gap audits remain required")
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
                    record["endpoints"] = audit(job.with_suffix(".dat").read_text(), context, preload_n=PRELOAD_N)
                    passed = all(s[k] for s in record["endpoints"] for k in ("force_pass", "moment_pass", "aggregate_friction_pass"))
                    record["status"] = "GLOBAL ACTUAL-LEG COUPON CHECKS PASS; LOCAL CONTACT NOT VALIDATED" if passed else "GLOBAL ACTUAL-LEG COUPON AUDIT REJECTED; NOT FRAME FAILURE"
                except (ValueError, FileNotFoundError) as error:
                    record["audit_error"] = str(error)
            record["output_sha256"] = {p.name: digest(p) for p in directory.glob(name+".*") if p.suffix in (".dat", ".frd", ".log", ".sta", ".cvg")}
            job.with_suffix(".json").write_text(json.dumps(record, indent=2, allow_nan=False)+"\n")
            print(name, record["status"], flush=True)


if __name__ == "__main__":
    main()
