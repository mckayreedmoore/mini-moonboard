"""Separate climber masses and retain simultaneous leg-bolt force components."""
import hashlib
import json
import math
import tarfile

from fea.coupled_leg_release import OUTPUT
from fea.leg_bolt_reference import build as references
from fea.timber_asymmetric import unchanged


def build():
    with tarfile.open(OUTPUT) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive.getmembers()}
    report = json.loads(files["report.json"])
    unchanged(report["source_sha256"])
    if not report["passed"] or set(files)-{"report.json"} != set(report["artifact_sha256"]):
        raise ValueError("Require complete passing coupled-leg archive")
    if any(hashlib.sha256(files[n]).hexdigest() != h for n, h in report["artifact_sha256"].items()):
        raise ValueError("Coupled-leg artifacts changed")
    reference = {r["connection"]: r["conditional_reference_lateral_n"] for r in references()["rows"]}
    rows = []
    for stiffness, run in report["runs"].items():
        for weight in (150, 200, 250, 300):
            cases = [s for s in run["scenarios"] if s["climber_lb"] == weight]
            if len(cases) != 54:
                raise ValueError("Expected 54 scenarios per climber mass and stiffness")
            candidates = []
            for case in cases:
                forces = case["leg_connector_force_on_leg_n"]
                if set(forces) != set(reference):
                    raise ValueError("Leg bolt inventory differs")
                for name, force in forces.items():
                    if len(force) != 3 or not all(map(math.isfinite, force)):
                        raise ValueError("Require finite signed three-component forces")
                    candidates.append({"connection": name,
                        "case": {k: case[k] for k in ("hold", "climber_lb", "weight_factor", "horizontal_direction_deg", "force_n")},
                        "force_on_leg_n": force, "lateral_n": math.hypot(*force[1:]),
                        "simultaneous_signed_axial_n": force[0],
                        "conditional_reference_n": reference[name]})
            peak = max(candidates, key=lambda r: r["lateral_n"])
            rows.append({"stiffness": stiffness, "climber_lb": weight, **peak,
                         "numerical_reference_ratio": peak["lateral_n"]/peak["conditional_reference_n"]})
    return {"archive_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
            "limits": "Archived assumed-stiffness trial and conditional bonded-laminate reference only. "
            "Not physical demand bounds, allowable ratios, safety factors or climber ratings.", "rows": rows}


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
