"""Isolated unpinned contact-control experiment; convergence is not validation."""
import argparse
import hashlib
import json
import math
import re
import subprocess
import tempfile
import time
from pathlib import Path

from fea.floor_contact import SOURCE, deck, floor_faces, integrated_weights, mesh
from fea.floor_contact_results import audit

CONTROLS = "*CONTROLS,PARAMETERS=CONTACT\n0.001,0.1,100,12\n"


def validate_context(info, summary, source_digest):
    volume, centre = info["cad_volume_mm3"], info["cad_centre_mm"]
    if not math.isfinite(volume) or volume <= 0 or len(centre) != 3 or not all(map(math.isfinite, centre)):
        raise ValueError("Finite positive CAD volume and finite three-coordinate centroid required")
    if source_digest != info["source_sha256"] or source_digest != summary["evidence_sha256"][SOURCE.name]:
        raise ValueError("Frozen mesh provenance differs")
    if info["geometry_source_sha256"] != summary["frozen_geometry"]["geometry_source_sha256"]:
        raise ValueError("Prepared and frozen geometry provenance differ")


def recovery_deck(base, groups):
    output = "*CONTACT PRINT\nCDIS,CSTR\n"
    for name in groups:
        output += f"*CONTACT PRINT,SLAVE=SLAVE_{name},MASTER=MASTER_{name}\nCF,CFN,CFS\n"
    return base.replace("*STATIC\n", CONTROLS + "*STATIC\n").replace("*END STEP\n", output + "*END STEP\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-seconds", type=float, default=600)
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("positive finite runtime required")
    prepared = Path("fea/generated/floor-contact/input.json")
    info = json.loads(prepared.read_text())
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    validate_context(info, summary, digest(SOURCE))
    if any(digest(Path(p)) != h for p, h in info["geometry_source_sha256"].items()):
        raise ValueError("Frozen geometry changed")
    nodes, elements = mesh(SOURCE.read_text())
    groups = floor_faces(nodes, elements)
    weights = integrated_weights(elements, nodes)
    volume = sum(weights.values())
    centre = [sum(v * nodes[n][i] for n, v in weights.items()) / volume for i in range(3)]
    if abs(volume / info["cad_volume_mm3"] - 1) > .001 or math.dist(centre, info["cad_centre_mm"]) > 1:
        raise ValueError("Integrated mass/centroid differs from frozen CAD")
    base, ground = deck(nodes, elements, groups, summary["load_nodes"], .3, 10000)
    text = recovery_deck(base, groups)
    directory = Path(tempfile.mkdtemp(prefix="recovery-it12-", dir="fea/generated"))
    job = directory / "recovery"
    job.with_suffix(".inp").write_text(text)
    inputs = (SOURCE, SOURCE.with_suffix(".json"), prepared, Path(__file__),
              Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py"))
    record = dict(info, mu=.3, normal_penalty_n_mm3=10000, tangent_penalty_n_mm3=100,
                  contact_controls={"delcon": .001, "alea": .1, "kscalemax": 100, "itf2f": 12},
                  ground_nodes=ground, nodal_volume_mm3=weights, load_nodes=summary["load_nodes"],
                  mesh_volume_mm3=volume, mesh_mass_kg=volume * 600 / 1e9, mesh_centre_mm=centre,
                  floor_face_counts={k: len(v) for k, v in groups.items()},
                  prelaunch_sha256={str(p): digest(p) for p in inputs},
                  deck_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  baseline_deck_sha256=hashlib.sha256(base.encode()).hexdigest(),
                  max_seconds=args.max_seconds, status="RUNNING; NOT VALIDATED")
    job.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Evidence: {directory}", flush=True)
    started = time.monotonic()
    with job.with_suffix(".log").open("w") as log:
        try:
            result = subprocess.run(["ccx", "-i", job.name], cwd=directory, stdout=log,
                                    stderr=subprocess.STDOUT, timeout=args.max_seconds, check=False)
            record["exit_code"] = result.returncode
        except subprocess.TimeoutExpired:
            record["exit_code"] = -999
            record["runtime_stop"] = "Bounded timeout; no physical failure conclusion"
    record["elapsed_seconds"] = time.monotonic() - started
    log = job.with_suffix(".log").read_text()
    record["stiffness_reductions"] = len(re.findall("reducing the constant stiffnesses", log))
    record["nominal_stiffness_restoration_messages"] = len(re.findall("restoring the elastic contact stifnesses", log))
    record["status"] = "UNRESOLVED SOLVER/OUTPUT; NOT A STABILITY CONCLUSION"
    if record["exit_code"] == 0 and "*ERROR" not in log.upper():
        try:
            if digest(job.with_suffix(".inp")) != record["deck_sha256"]:
                raise ValueError("Launched deck changed")
            record["audited_steps"] = audit(job.with_suffix(".dat").read_text(), nodes, elements, groups, record)
            record["status"] = "TWO EQUILIBRIUM-AUDITED STEPS; LOCAL CONTACT AND SENSITIVITY AUDITS REQUIRED"
        except (ValueError, FileNotFoundError) as error:
            record["audit_error"] = str(error)
    record["output_sha256"] = {p.name: digest(p) for p in directory.iterdir() if p.suffix in (".log", ".dat", ".sta", ".cvg", ".frd")}
    job.with_suffix(".json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({k: record[k] for k in ("status", "elapsed_seconds", "stiffness_reductions", "nominal_stiffness_restoration_messages")}), flush=True)


if __name__ == "__main__":
    main()
