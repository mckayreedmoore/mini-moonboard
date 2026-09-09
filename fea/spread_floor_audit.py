"""Independent global endpoint checks; local MORTAR acceptance remains open."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from fea.floor_contact import integrated_weights
from fea.floor_contact_results import blocks, cross

FORCE_TOLERANCE_N = .1
MOMENT_TOLERANCE_NMM = 1.


def source_hashes():
    return {name: hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in (
        "fea/spread_floor_audit.py", "fea/floor_contact.py", "fea/floor_contact_results.py")}


def integrate(record):
    mapped = record["mapped_input"]
    nodes = {int(n): p for n, p in mapped["nodes"].items()}
    elements = {int(e): ids for e, ids in mapped["elements"].items()}
    return integrated_weights(elements, nodes)


def assess(data, record, weights):
    """Only noncontact ground-bottom reactions are external support forces."""
    nodes = {int(n): p for n, p in record["connector_context"]["nodes"].items()}
    physical = {int(n): p for n, p in record["mapped_input"]["nodes"].items()}
    weights = {int(n): v for n, v in weights.items()}
    if weights.keys() != physical.keys() or not all(math.isfinite(v) for v in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("Incomplete or invalid consistent gravity weights")
    parsed, results = blocks(data), []
    for time, loaded in ((1., False), (2., True)):
        u = parsed.get(("displacements", "WOODN", time), {})
        if u.keys() != nodes.keys():
            raise ValueError(f"Missing complete wood/virtual endpoint at time {time}")
        positions = {n: [a+b for a,b in zip(p, u[n], strict=True)] for n,p in nodes.items()}
        forces, moments = [], []
        for name, points in record["ground_nodes"].items():
            points = {int(n): p for n,p in points.items()}
            rf = parsed.get(("forces", "GROUND_"+name, time), {})
            gu = parsed.get(("displacements", "GROUND_"+name, time), {})
            if rf.keys() != points.keys() or gu.keys() != points.keys():
                raise ValueError("Missing complete ground endpoint")
            for n in record["bottom_nodes"][name]:
                forces.append(rf[n])
                moments.append(cross([a+b for a,b in zip(points[n], gu[n], strict=True)], rf[n]))
        for n, volume in weights.items():
            force = [0., 0., -volume*record["density_tonne_mm3"]*9806.65]
            forces.append(force)
            moments.append(cross(positions[n], force))
        if loaded:
            force = record["load"]["force_n"]
            forces.append(force)
            moments.append(cross(positions[record["load"]["node"]], force))
        force = [math.fsum(f[i] for f in forces) for i in range(3)]
        moment = [math.fsum(m[i] for m in moments) for i in range(3)]
        error = 0.
        for p in record["connector_context"]["connections"].values():
            for virtual, ids, terms in ((p["parent_point"], p["nodes"], p["weights"]),
                    (p["gusset_point"], p["gusset_nodes"], p["other_weights"])):
                expected = [math.fsum(w*u[n][i] for n,w in zip(ids, terms, strict=True)) for i in range(3)]
                error = max(error, math.dist(expected, u[virtual]))
        results.append({"time": time, "force_residual_n": force, "moment_residual_nmm": moment,
            "maximum_interpolation_error_mm": error,
            "maximum_wood_displacement_mm": max(math.hypot(*u[n]) for n in physical),
            "global_checks_passed": max(map(abs, force)) <= FORCE_TOLERANCE_N
                and max(map(abs, moment)) <= MOMENT_TOLERANCE_NMM and error <= 1e-5})
    return {"endpoints": results, "global_checks_passed": all(r["global_checks_passed"] for r in results),
        "gates": {"force_n": FORCE_TOLERANCE_N, "moment_nmm": MOMENT_TOLERANCE_NMM,
                  "interpolation_mm": 1e-5},
        "local_contact_audited": False, "qualified_for_design": False,
        "limits": "Global equilibrium and interpolation only. No local traction/gap/friction/"
            "complementarity, mesh sensitivity, connection strength or physical stability approval."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--integrate", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.directory/"input.json"
    record = json.loads(source.read_text())
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    if args.integrate:
        import gmsh
        result = {"input_sha256": sha, "weights": integrate(record),
                  "source_sha256": source_hashes(), "gmsh_version": gmsh.__version__}
    else:
        weights = json.loads((args.directory/"weights.json").read_text())
        if weights["input_sha256"] != sha:
            raise ValueError("Gravity integration belongs to a different input")
        if weights["source_sha256"] != source_hashes():
            raise ValueError("Gravity integration/audit sources changed")
        if hashlib.sha256((args.directory/"contact.inp").read_bytes()).hexdigest() != record["deck_sha256"]:
            raise ValueError("Contact deck differs from preparation")
        result = assess((args.directory/"contact.dat").read_text(), record, weights["weights"])
        result["input_sha256"] = sha
        result["source_sha256"] = source_hashes()
        result["artifact_sha256"] = {name: hashlib.sha256((args.directory/name).read_bytes()).hexdigest()
                                     for name in ("contact.dat", "contact.inp", "weights.json")}
    with args.output.open("x") as output:
        json.dump(result, output, allow_nan=False, indent=2)
        output.write("\n")
