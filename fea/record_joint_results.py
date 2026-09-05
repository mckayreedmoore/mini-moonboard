"""Reparse completed DAT/INP pairs and publish small, hash-linked summaries."""
import hashlib
import json
import math
from pathlib import Path

from .joint_math import parse_joint_results


def read_deck(text):
    nodes, forces, elements = {}, {}, set()
    section = ""
    quadratic = False
    for line in text.splitlines():
        if line.startswith("**"):
            continue
        if line.startswith("*"):
            section = line.upper().split(",")[0]
            quadratic = section=="*ELEMENT" and "TYPE=C3D10" in line.upper()
        elif line.strip() and quadratic:
            elements.add(int(line.split(",")[0]))
        elif line.strip() and section in ("*NODE", "*CLOAD"):
            cells = line.split(",")
            tag = int(cells[0])
            if section == "*NODE":
                nodes[tag] = tuple(float(v) for v in cells[1:4])
            else:
                forces.setdefault(tag,[0.,0.,0.])[int(cells[1])-1] += float(cells[2])
    if not nodes or not forces or not elements:
        raise ValueError("Missing input nodes, loads or quadratic elements")
    force = [sum(v[i] for v in forces.values()) for i in range(3)]
    moment = [sum(nodes[t][(i+1)%3]*v[(i+2)%3]-nodes[t][(i+2)%3]*v[(i+1)%3] for t,v in forces.items()) for i in range(3)]
    return nodes, force, moment, elements


def main():
    directory = Path("fea/generated")
    output = Path("fea/results")
    output.mkdir(exist_ok=True)
    for size in (12,8):
        records = json.loads((directory/f"joint_results_{size}_7000.json").read_text())
        if len(records)!=12 or len({(r["part"],r["case"]) for r in records})!=12:
            raise ValueError("Expected twelve distinct joint cases")
        for r in records:
            stem = directory/f"joint_{r['part']}_{size}_7000_{r['case']}"
            deck, dat = stem.with_suffix(".inp"), stem.with_suffix(".dat")
            nodes, force, moment, elements = read_deck(deck.read_text())
            actual = parse_joint_results(dat.read_text(),force,nodes,moment,elements)
            for key in ("max_displacement_mm", "peak_equivalent_stress_mpa", "p95_equivalent_stress_mpa"):
                if not math.isclose(actual[key],r[key],rel_tol=1e-10):
                    raise ValueError("Summary does not match raw solver evidence")
            r.update(actual)
            r["applied_global_moment_nmm"] = moment
            r["evidence_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (deck,dat)}
            # These identify the re-audit context, not immutable execution
            # provenance. The INP and DAT above are the actual solve evidence.
            r["audit_context_sha256"] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                (directory/f"joint_{r['part']}.step",directory/"joints.json",
                 Path("fea/solve_joints.py"),Path("fea/prepare_joints.py"),Path("fea/joint_math.py"))}
        (output/f"joint_bearing_{size}_7000.json").write_text(json.dumps(records,indent=2)+"\n")
    (output/"joint_geometry.json").write_text((directory/"joints.json").read_text())


if __name__ == "__main__":
    main()
