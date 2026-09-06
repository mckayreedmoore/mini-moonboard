"""Actual frozen left-leg coupon: conditional upper guide, never a free-board result."""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path

from fea.floor_contact import FACES, SOURCE, deck, floor_faces, integrated_weights, mesh
from fea.floor_contact_results import blocks, cross

DIRECTORY = Path("fea/generated/foot-contact-diagnosis")
EDGES = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))


def extract(text):
    """Find the complete original volume owning the actual left floor patch."""
    nodes, elements = mesh(text)
    floor = floor_faces(nodes, elements)["LEFT"]
    owners = {}
    volume = None
    for line in text.splitlines():
        if line.startswith("*"):
            volume = line.upper().split("ELSET=")[-1].strip() if line.upper().startswith("*ELEMENT") else None
        elif volume and line.strip():
            owners[int(line.split(",")[0])] = volume
    selected = {owners[e] for e, _ in floor}
    if len(selected) != 1 or "VOLUME" not in next(iter(selected)):
        raise ValueError("Actual left floor must belong to one original volume")
    elements = {e: ids for e, ids in elements.items() if owners[e] in selected}
    used = {n for ids in elements.values() for n in ids}
    return {n: xyz for n, xyz in nodes.items() if n in used}, elements, {"LEFT": floor}, next(iter(selected))


def geometry_audit(nodes, elements, groups):
    offsets = []
    for ids in elements.values():
        for mid, (a, b) in zip(ids[4:], EDGES, strict=True):
            offsets.append(math.dist(nodes[mid], tuple((nodes[ids[a]][i]+nodes[ids[b]][i])/2 for i in range(3))))
    cosines = []
    for element, face in groups["LEFT"]:
        ids = elements[element]
        corners = FACES[face-1][:3]
        a, b, c = (nodes[ids[i]] for i in corners)
        normal = cross([b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)])
        opposite = nodes[ids[next(i for i in range(4) if i not in corners)]]
        if sum(normal[i]*(opposite[i]-a[i]) for i in range(3)) > 0:
            normal = [-v for v in normal]
        norm = math.hypot(*normal)
        if norm == 0:
            raise ValueError("Degenerate floor face")
        cosines.append(-normal[2]/norm)
    if not cosines or min(cosines) < .999999:
        raise ValueError("Floor face outward normal does not oppose upward ground")
    return {"max_midside_offset_mm": max(offsets), "minimum_outward_down_cosine": min(cosines)}


def coupon_deck(nodes, elements, groups):
    top = [n for n, xyz in nodes.items() if xyz[2] > max(p[2] for p in nodes.values())-60]
    if len(top) < 3:
        raise ValueError("Missing upper restraint/load patch")
    text, ground = deck(nodes, elements, groups, top, .3, 10000)
    text = text.replace("UNPINNED FLOOR CONTACT FEASIBILITY", "CONDITIONAL ACTUAL LEG COUPON; UPPER X/Y GUIDE; NOT FREE BOARD")
    text = text.replace("*BOUNDARY\n", "*BOUNDARY\nTOP,1,2,0\n", 1)
    text = text.replace("*NODE PRINT,NSET=WOODN", "*NODE PRINT,NSET=TOP\nRF\n*NODE PRINT,NSET=WOODN")
    return text, ground, top


def audit(data, nodes, ground, top, weights):
    parsed = blocks(data)
    results = []
    for time, load in ((1., 0.), (2., 1200.)):
        u = parsed.get(("displacements", "WOODN", time), {})
        support = parsed.get(("forces", "TOP", time), {})
        reaction = parsed.get(("forces", "GROUND_LEFT", time), {})
        if u.keys() != nodes.keys() or support.keys() != set(top) or reaction.keys() != ground["LEFT"].keys():
            raise ValueError(f"Incomplete accepted final output at time {time}")
        positions = {n: tuple(x+dx for x, dx in zip(xyz, u[n], strict=True)) for n, xyz in nodes.items()}
        # RF output at unconstrained z includes applied load: only x/y are support reactions.
        applied = [(positions[n], (v[0], v[1], 0.)) for n, v in support.items()]
        applied += [(ground["LEFT"][n], v) for n, v in reaction.items()]
        applied += [(positions[n], (0., 0., -v*6e-10*9806.65)) for n, v in weights.items()]
        applied += [(positions[n], (0., 0., -load/len(top))) for n in top]
        force = [sum(v[i] for _, v in applied) for i in range(3)]
        moment = [sum(cross(p, v)[i] for p, v in applied) for i in range(3)]
        total = [sum(v[i] for v in reaction.values()) for i in range(3)]
        if max(map(abs, force)) > .1 or max(map(abs, moment)) > 2:
            raise ValueError(f"Equilibrium residual at {time}: {force}, {moment}")
        if total[2] <= 0 or math.hypot(*total[:2]) > .3*total[2]+.1:
            raise ValueError("Necessary aggregate floor friction/compression bound failed")
        results.append({"time": time, "downward_upper_load_n": load, "force_residual_n": force,
                        "moment_residual_nmm": moment, "floor_resultant_n": total,
                        "upper_guide_resultant_n": [sum(v[i] for v in support.values()) for i in range(2)]+[0.],
                        "max_displacement_mm": max(math.hypot(*v) for v in u.values())})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--straight-midsides", action="store_true")
    parser.add_argument("--max-seconds", type=float, default=120)
    args = parser.parse_args()
    if not math.isfinite(args.max_seconds) or args.max_seconds <= 0:
        parser.error("Positive finite runtime required")
    source = SOURCE.read_text()
    summary = json.loads(SOURCE.with_suffix(".json").read_text())
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if summary["evidence_sha256"][SOURCE.name] != digest:
        raise ValueError("Frozen mesh digest mismatch")
    for path, expected in summary["frozen_geometry"]["geometry_source_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Frozen CAD digest mismatch")
    cad_path = DIRECTORY/"actual_leg_cad.json"
    if args.prepare:
        from mini_moonboard.footprint_frame import parts
        leg = next(p.shape for p in parts(100, False) if p.name == "leg_left")
        bounds = leg.BoundingBox()
        record = {"source_sha256": digest, "volume_mm3": leg.Volume(), "centre_mm": leg.Center().toTuple(),
                  "bounds_mm": [[getattr(bounds, axis+"min"), getattr(bounds, axis+"max")] for axis in "xyz"],
                  "geometry_source_sha256": summary["frozen_geometry"]["geometry_source_sha256"]}
        DIRECTORY.mkdir(parents=True, exist_ok=True)
        if cad_path.exists():
            raise ValueError("Existing CAD reference is immutable")
        cad_path.write_text(json.dumps(record, indent=2)+"\n")
        return
    nodes, elements, groups, volume = extract(source)
    geometry = geometry_audit(nodes, elements, groups)
    if args.straight_midsides:
        for ids in elements.values():
            for mid, (a, b) in zip(ids[4:], EDGES, strict=True):
                nodes[mid] = tuple((nodes[ids[a]][i]+nodes[ids[b]][i])/2 for i in range(3))
    weights = integrated_weights(elements, nodes)
    cad = json.loads(cad_path.read_text())
    centre = [sum(nodes[n][i]*w for n, w in weights.items())/sum(weights.values()) for i in range(3)]
    bounds = [[min(p[i] for p in nodes.values()), max(p[i] for p in nodes.values())] for i in range(3)]
    if cad["source_sha256"] != digest or abs(sum(weights.values())/cad["volume_mm3"]-1) > .001 or math.dist(centre, cad["centre_mm"]) > 1 or any(abs(a-b) > 1 for aa, bb in zip(bounds, cad["bounds_mm"], strict=True) for a, b in zip(aa, bb, strict=True)):
        raise ValueError("Extracted volume does not match actual CAD left leg mass/CG/bounds")
    text, ground, top = coupon_deck(nodes, elements, groups)
    name = "actual_leg_straight" if args.straight_midsides else "actual_leg"
    directory = DIRECTORY/name
    directory.mkdir(parents=True, exist_ok=True)
    job = directory/name
    if job.with_suffix(".json").exists():
        raise ValueError("Existing result is immutable; use a fresh output location")
    job.with_suffix(".inp").write_text(text)
    record = {"source": str(SOURCE), "source_sha256": digest, "original_volume": volume,
              "node_count": len(nodes), "element_count": len(elements), "floor_face_count": len(groups["LEFT"]),
              "original_geometry_audit": geometry, "straight_midsides": args.straight_midsides,
              "mass_kg": sum(weights.values())*6e-7, "upper_node_count": len(top),
              "mesh_centre_mm": centre, "mesh_bounds_mm": bounds, "cad_reference": cad,
              "assumptions": "Permanent upper 60 mm x/y guide; z free; gravity then 1200 N downward upper patch; conditional leg coupon, never free board",
              "deck_sha256": hashlib.sha256(text.encode()).hexdigest(),
              "run_source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path("fea/floor_contact.py"), Path("fea/floor_contact_results.py"))}}
    job.with_suffix(".json").write_text(json.dumps(dict(record, status="INPUTS FROZEN; NOT RUN"), indent=2)+"\n")
    try:
        result = subprocess.run(["ccx", "-i", name], cwd=directory, capture_output=True, text=True, timeout=args.max_seconds, check=False)
        output = result.stdout+result.stderr
        record["exit_code"] = result.returncode
    except subprocess.TimeoutExpired as error:
        output = (error.stdout or b"").decode()+(error.stderr or b"").decode()
        record["exit_code"] = -999
    job.with_suffix(".log").write_text(output)
    record["status"] = "UNRESOLVED NUMERICAL RESULT; NO PHYSICAL STABILITY CONCLUSION"
    if record["exit_code"] == 0 and "*ERROR" not in output.upper():
        try:
            record["audited_steps"] = audit(job.with_suffix(".dat").read_text(), nodes, ground, top, weights)
            record["status"] = "TWO COMPLETE EQUILIBRIUM-AUDITED CONDITIONAL COUPON STEPS; LOCAL CONTACT AUDIT STILL REQUIRED"
        except ValueError as error:
            record["audit_error"] = str(error)
    record["evidence_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.glob(name+".*") if p.suffix in (".inp", ".dat", ".sta", ".cvg", ".log")}
    job.with_suffix(".json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
