"""Nine linear basis solves on the accepted timber mesh; no insert approval."""
import argparse
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross
from fea.solve_easy_frame import digest, make_deck
from fea.timber_joint_demand import authenticated_inputs
from fea.timber_structural import locations

DIRECTORY = Path("fea/generated/timber-asymmetric")
HOLDS = ("A12", "K12", "F6")
BASIS = ({"name": "X", "force_n": [1000., 0., 0.]},
         {"name": "Y", "force_n": [0., 1000., 0.]},
         {"name": "Z", "force_n": [0., 0., -1000.]})
LIMITS = ("Accepted timber-base-development mesh, not panel-insert geometry. "
          "Linear isotropic ideally bonded frame; fixed XYZ floor; no gravity, "
          "standoff moment, contact, strength or approval. Single mapped face node; "
          "point stress not qualified. Scenario results are linear combinations "
          "of nine solved basis cases, not 216 independently solved cases.")
LIMITS += (" Inherited bonded mesh joins legs to rim AND upper panel edges; "
           "aggregate leg-to-board actions must not be assigned to four rim bolts.")


def save(path, value):
    with path.open("x") as stream:
        stream.write(json.dumps(value, indent=2, allow_nan=False)+"\n")


def unchanged(sources):
    if not sources or any(digest(p) != sha for p, sha in sources.items()):
        raise ValueError("Recorded sources or inputs changed")


def mesh_text(nodes, elements):
    return "\n".join(["*NODE", *[f"{n},"+",".join(map(repr, xyz)) for n, xyz in sorted(nodes.items())],
        "*ELEMENT,TYPE=C3D10,ELSET=TIMBER",
        *[f"{n},"+",".join(map(str, ids)) for n, ids in sorted(elements.items())]])+"\n"


def map_target(nodes, target, normal, feet):
    candidates = [n for n, p in nodes.items() if n not in feet and
                  abs(sum((p[i]-target[i])*normal[i] for i in range(3))) < .01]
    if not candidates:
        raise ValueError("No climbing-face nodes")
    node = min(candidates, key=lambda n: (math.dist(nodes[n], target), n))
    distance = math.dist(nodes[node], target)
    if distance > 20.:
        raise ValueError("Single hold maps beyond 20 mm")
    return {"node": node, "target_mm": list(target), "coordinates_mm": list(nodes[node]), "distance_mm": distance}


def expected_deck(nodes, elements, feet, node):
    return "** "+LIMITS+"\n"+make_deck(mesh_text(nodes, elements), feet, [node], BASIS, 7000.)


def prepare():
    if DIRECTORY.exists():
        raise FileExistsError("Refusing to overwrite asymmetric preparation")
    row, original, _, sources = authenticated_inputs()
    sources["fea/timber_asymmetric.py"] = digest("fea/timber_asymmetric.py")
    nodes, elements = mesh(original)
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    targets = {label: (p, normal) for label, p, normal in locations()}
    mappings = {hold: map_target(nodes, *targets[hold], set(feet)) for hold in HOLDS}
    if len({r["node"] for r in mappings.values()}) != len(HOLDS):
        raise ValueError("Distinct holds map to the same node")
    decks = {hold: expected_deck(nodes, elements, feet, m["node"]) for hold, m in mappings.items()}
    if any(mesh(deck) != (nodes, elements) for deck in decks.values()):
        raise ValueError("Rebuilt deck changes accepted mesh")
    unchanged(sources)
    DIRECTORY.mkdir(parents=True)
    for hold, deck in decks.items():
        with (DIRECTORY/f"{hold}.inp").open("x") as stream:
            stream.write(deck)
    save(DIRECTORY/"input.json", {"candidate": row["candidate"], "limits": LIMITS,
        "source_sha256": sources, "mapping": mappings, "basis": BASIS,
        "accepted_mesh_deck_sha256": row["deck_sha256"],
        "deck_sha256": {h: digest(DIRECTORY/f"{h}.inp") for h in HOLDS}})


def audit(deck, data, node):
    nodes, elements = mesh(deck)
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    if node not in nodes or node in feet or not feet:
        raise ValueError("Invalid single load or support nodes")
    if deck != expected_deck(nodes, elements, feet, node):
        raise ValueError("Deck differs from exact basis loads/material/supports")
    parsed = blocks(data)
    expected = {(kind, name, float(i)) for i in (1, 2, 3)
                for kind, name in (("displacements", "TOP"), ("forces", "FEET"))}
    if set(parsed) != expected:
        raise ValueError("Wrong output endpoints or sets")
    result = []
    for i, case in enumerate(BASIS, 1):
        u, reactions = parsed["displacements", "TOP", float(i)], parsed["forces", "FEET", float(i)]
        if set(u) != {node} or set(reactions) != set(feet):
            raise ValueError("Incomplete single-load or floor reaction output")
        force = [math.fsum(r[a] for r in reactions.values()) for a in range(3)]
        moments = [cross(nodes[n], r) for n, r in reactions.items()]
        moment = [math.fsum(r[a] for r in moments) for a in range(3)]
        residual = [a+b for a, b in zip(force+moment, case["force_n"]+cross(nodes[node], case["force_n"]), strict=True)]
        if max(map(abs, residual[:3])) > .1 or max(map(abs, residual[3:])) > 1.:
            raise ValueError("Basis force/moment equilibrium failed")
        result.append({"name": case["name"], "force_n": case["force_n"], "loaded_displacement_mm": u[node],
                       "reaction_wrench_n_nmm": force+moment, "residual_wrench": residual})
    return result


def solve(hold):
    if hold not in HOLDS:
        raise ValueError("Unknown hold")
    info = json.loads((DIRECTORY/"input.json").read_text())
    unchanged(info["source_sha256"])
    prefix = DIRECTORY/hold
    if any(p != prefix.with_suffix(".inp") for p in DIRECTORY.glob(hold+".*")):
        raise FileExistsError("Refusing to overwrite solver attempt")
    if digest(prefix.with_suffix(".inp")) != info["deck_sha256"][hold]:
        raise ValueError("Prepared deck changed")
    input_sha = digest(DIRECTORY/"input.json")
    save(prefix.with_suffix(".launch.json"), {"input_sha256": input_sha,
        "deck_sha256": info["deck_sha256"][hold], "source_sha256": info["source_sha256"]})
    with prefix.with_suffix(".log").open("x") as stream:
        completed = subprocess.run(["ccx", "-i", hold], cwd=DIRECTORY,
                                   stdout=stream, stderr=subprocess.STDOUT, check=False)
    log = prefix.with_suffix(".log").read_text()
    if completed.returncode or "*ERROR" in log.upper():
        raise ValueError("CalculiX failed; attempt retained")
    unchanged(info["source_sha256"])
    if (digest(prefix.with_suffix(".inp")) != info["deck_sha256"][hold]
            or digest(DIRECTORY/"input.json") != input_sha):
        raise ValueError("Solver deck changed")
    basis = audit(prefix.with_suffix(".inp").read_text(), prefix.with_suffix(".dat").read_text(), info["mapping"][hold]["node"])
    save(prefix.with_suffix(".json"), {"hold": hold, "basis": basis,
        "input_sha256": digest(DIRECTORY/"input.json"),
        "solver_version_banner": [line.strip() for line in log.splitlines() if "version" in line.lower()],
        "artifacts": {p.name: digest(p) for p in DIRECTORY.glob(hold+".*")}})


def scenarios(basis, point):
    for weight in (150, 200, 250, 300):
        for factor in (1, 2):
            for direction in range(-1, 8):
                angle = direction*math.pi/4
                force = [0. if direction < 0 else 300.*math.cos(angle),
                         0. if direction < 0 else 300.*math.sin(angle),
                         -weight*.45359237*9.80665*factor]
                coefficients = [force[0]/1000., force[1]/1000., -force[2]/1000.]
                def combine(key, coefficients=coefficients):
                    return [math.fsum(c*b[key][i] for c, b in zip(coefficients, basis, strict=True))
                            for i in range(len(basis[0][key]))]
                u, reaction = combine("loaded_displacement_mm"), combine("reaction_wrench_n_nmm")
                residual = [a+b for a, b in zip(reaction, force+cross(point, force), strict=True)]
                scale = sum(map(abs, coefficients))
                if (not all(map(math.isfinite, u+reaction)) or max(map(abs, residual[:3])) > .1*scale
                        or max(map(abs, residual[3:])) > scale):
                    raise ValueError("Superposed equilibrium failed")
                yield {"climber_lb": weight, "weight_factor": factor,
                    "horizontal_direction_deg": None if direction < 0 else direction*45,
                    "force_n": force, "basis_coefficients": coefficients,
                    "loaded_displacement_mm": u, "loaded_displacement_magnitude_mm": math.sqrt(sum(v*v for v in u)),
                    "reaction_wrench_n_nmm": reaction, "residual_wrench": residual}


def summarize():
    output = DIRECTORY/"summary.json"
    if output.exists():
        raise FileExistsError("Refusing to overwrite summary")
    info = json.loads((DIRECTORY/"input.json").read_text())
    unchanged(info["source_sha256"])
    rows = []
    hashes = {"input.json": digest(DIRECTORY/"input.json")}
    for hold in HOLDS:
        record = json.loads((DIRECTORY/f"{hold}.json").read_text())
        if record["input_sha256"] != hashes["input.json"]:
            raise ValueError("Basis uses different input")
        unchanged({str(DIRECTORY/p): sha for p, sha in record["artifacts"].items()})
        basis = audit((DIRECTORY/f"{hold}.inp").read_text(), (DIRECTORY/f"{hold}.dat").read_text(), info["mapping"][hold]["node"])
        if json.loads(json.dumps(basis)) != record["basis"]:
            raise ValueError("Basis replay differs")
        rows.extend({"hold": hold, **r} for r in scenarios(basis, info["mapping"][hold]["coordinates_mm"]))
        hashes.update(record["artifacts"])
        hashes[f"{hold}.json"] = digest(DIRECTORY/f"{hold}.json")
    archive = DIRECTORY/"replay"
    archive.mkdir(exist_ok=False)
    for name in hashes:
        with (archive/(name+".gz")).open("xb") as stream:
            stream.write(gzip.compress((DIRECTORY/name).read_bytes(), mtime=0))
    unchanged(info["source_sha256"])
    unchanged({str(DIRECTORY/name): sha for name, sha in hashes.items()})
    save(output, {"limits": LIMITS, "input": info, "basis_solve_count": 9,
        "scenario_count": len(rows), "cases": rows, "uncompressed_artifact_sha256": hashes,
        "archive_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in archive.iterdir()}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "solve", "summarize"))
    parser.add_argument("--hold", choices=HOLDS)
    args = parser.parse_args()
    if args.command == "solve":
        solve(args.hold)
    else:
        {"prepare": prepare, "summarize": summarize}[args.command]()
