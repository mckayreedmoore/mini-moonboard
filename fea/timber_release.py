"""K12 panel-edge release sensitivity; fixed floor and ideal rim, not capacity."""
import argparse
import gzip
import hashlib
import json
import math
import subprocess
from pathlib import Path

from fea import timber_asymmetric as basis_run
from fea.floor_contact import mesh, node_set
from fea.floor_contact_results import blocks, cross
from fea.panel_edge_release import release
from fea.prove_panel_edge_release import REPORT, recover
from fea.publish_timber_asymmetric import compliance
from fea.timber_joint_demand import authenticated_inputs

DIRECTORY = Path("fea/generated/timber-release")
BASELINE = Path("fea/results/timber-asymmetric")
LIMITS = (
    "K12 linear release sensitivity on accepted timber mesh, not insert/wide geometry. "
    "Fixed XYZ floor, no gravity; ideal rim bond, common N=0 edge and bonded leg plies retained. "
    "Released coincident panel surfaces are traction-free, not unilateral contact; "
    "negative signed X gap means interpenetration. Not a conservative bound, "
    "joint/bolt demand or resistance qualification. Three basis solves and one "
    "linear scenario combination; point stresses unqualified."
)
SOURCE_FILES = ("fea/timber_release.py", "fea/panel_edge_release.py",
                "fea/prove_panel_edge_release.py", "fea/timber_asymmetric.py",
                "fea/publish_timber_asymmetric.py", "uv.lock")


def pair_ids(mapping):
    if set(mapping) != {"left", "right"} or any(not values for values in mapping.values()):
        raise ValueError("Both leg node maps required")
    ids = [int(n) for values in mapping.values() for pair in values.items() for n in pair]
    if len(ids) != len(set(ids)):
        raise ValueError("Released node pair IDs overlap")
    return sorted(ids)


def expected_deck(nodes, elements, feet, load, mapping):
    pairs = pair_ids(mapping)
    if set(pairs) & (set(feet) | {load}) or not set(pairs) <= nodes.keys():
        raise ValueError("Released pairs overlap protected or missing nodes")
    for values in mapping.values():
        for old, new in values.items():
            if tuple(nodes[int(old)]) != tuple(nodes[int(new)]):
                raise ValueError("Release pairs must initially coincide")
    text = basis_run.make_deck(basis_run.mesh_text(nodes, elements), feet, [load], basis_run.BASIS, 7000.)
    text = text.replace("*MATERIAL,NAME=WOOD_SCREEN", "\n".join(node_set("PAIRS", pairs))+"\n*MATERIAL,NAME=WOOD_SCREEN")
    return "** "+LIMITS+"\n"+text.replace("*END STEP", "*NODE PRINT,NSET=PAIRS\nU\n*END STEP")


def gap_summary(displacements, mapping):
    if set(displacements) != set(pair_ids(mapping)):
        raise ValueError("Incomplete released-pair displacements")
    if any(len(v) != 3 or not all(map(math.isfinite, v)) for v in displacements.values()):
        raise ValueError("Invalid released-pair displacement")
    result = {}
    for side, sign in (("left", -1), ("right", 1)):
        values = [{"board_node": int(old), "leg_node": int(new),
                   "signed_gap_mm": sign*(displacements[int(new)][0]-displacements[int(old)][0])}
                  for old, new in mapping[side].items()]
        result[side] = {"pairs": values, "minimum_signed_gap_mm": min(v["signed_gap_mm"] for v in values),
            "maximum_signed_gap_mm": max(v["signed_gap_mm"] for v in values),
            "interpenetrating_pair_count": sum(v["signed_gap_mm"] < -1e-5 for v in values),
            "classification_tolerance_mm": 1e-5}
    return result


def audit(deck, data, info):
    nodes, elements = mesh(deck)
    feet, load, mapping = info["floor_nodes"], info["mapping"]["node"], info["node_map"]
    if deck != expected_deck(nodes, elements, feet, load, mapping):
        raise ValueError("Deck differs from prescribed release basis")
    if set(feet) != {n for n, p in nodes.items() if abs(p[2]) < 1e-5} or load in feet:
        raise ValueError("Changed floor or applied-load ownership")
    parsed = blocks(data)
    expected = {(kind, name, float(i)) for i in (1, 2, 3) for kind, name in
                (("displacements", "TOP"), ("forces", "FEET"), ("displacements", "PAIRS"))}
    if set(parsed) != expected:
        raise ValueError("Wrong release output endpoints")
    basis, pairs = [], []
    for step, case in enumerate(basis_run.BASIS, 1):
        u = parsed["displacements", "TOP", float(step)]
        reactions = parsed["forces", "FEET", float(step)]
        pair_u = parsed["displacements", "PAIRS", float(step)]
        if set(u) != {load} or set(reactions) != set(feet):
            raise ValueError("Incomplete release load/support outputs")
        reaction = [math.fsum(r[i] for r in reactions.values()) for i in range(3)]
        moments = [cross(nodes[n], r) for n, r in reactions.items()]
        reaction += [math.fsum(r[i] for r in moments) for i in range(3)]
        external = case["force_n"]+cross(nodes[load], case["force_n"])
        residual = [a+b for a, b in zip(reaction, external, strict=True)]
        if max(map(abs, residual[:3])) > .1 or max(map(abs, residual[3:])) > 1.:
            raise ValueError("Release force/moment equilibrium failed")
        basis.append({"name": case["name"], "force_n": case["force_n"],
            "loaded_displacement_mm": u[load], "reaction_wrench_n_nmm": reaction,
            "residual_wrench": residual, "gap": gap_summary(pair_u, mapping)})
        pairs.append(pair_u)
    scenario = next(r for r in basis_run.scenarios(basis, nodes[load])
                    if r["climber_lb"] == 300 and r["weight_factor"] == 2
                    and r["horizontal_direction_deg"] == 90)
    combined = {n: [math.fsum(c*values[n][i] for c, values in
                    zip(scenario["basis_coefficients"], pairs, strict=True)) for i in range(3)] for n in pair_ids(mapping)}
    scenario["gap"] = gap_summary(combined, mapping)
    baseline = info["bonded_basis"]
    comparison = {"bonded_compliance": compliance(baseline), "released_compliance": compliance(basis)}
    original_scenario = next(r for r in basis_run.scenarios(baseline, nodes[load])
                            if r["climber_lb"] == 300 and r["weight_factor"] == 2
                            and r["horizontal_direction_deg"] == 90)
    comparison["bonded_300lb_2x_outward300"] = original_scenario
    return {"basis": basis, "scenario_300lb_2x_outward300": scenario, "comparison": comparison}


def prepare():
    if DIRECTORY.exists():
        raise FileExistsError("Refusing to overwrite release preparation")
    accepted, original, _, sources = authenticated_inputs()
    joint = json.loads(REPORT.read_text())
    summary_path = BASELINE/"summary.json"
    baseline = json.loads(summary_path.read_text())
    for closure in (joint["source_sha256"], baseline["source_sha256"]):
        if any(p in sources and sources[p] != sha for p, sha in closure.items()):
            raise ValueError("Conflicting source identities")
        sources.update(closure)
    basis_run.unchanged(sources)
    for path in (*SOURCE_FILES, str(REPORT), str(summary_path)):
        sources[path] = basis_run.digest(path)
    if baseline["candidate"] != accepted["candidate"] or joint["candidate"] != accepted["candidate"]:
        raise ValueError("Different release/baseline geometry")
    decoded = {}
    for name in ("K12.inp.gz", "K12.dat.gz"):
        path = BASELINE/name
        payload = path.read_bytes()
        data = gzip.decompress(payload)
        hashes = baseline["replay_archives"][name]
        if (hashlib.sha256(payload).hexdigest() != hashes["gzip_sha256"] or
                hashlib.sha256(data).hexdigest() != hashes["uncompressed_sha256"]):
            raise ValueError("Bonded baseline archive changed")
        decoded[name] = data.decode()
        sources[str(path)] = basis_run.digest(path)
    nodes, elements = mesh(original)
    if mesh(decoded["K12.inp.gz"]) != (nodes, elements):
        raise ValueError("Bonded K12 mesh differs")
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    target, normal = next((p, n) for label, p, n in basis_run.locations() if label == "K12")
    mapping = basis_run.map_target(nodes, target, normal, set(feet))
    if mapping != baseline["input"]["mapping"]["K12"]:
        raise ValueError("Bonded/released load mapping differs")
    bonded = basis_run.audit(decoded["K12.inp.gz"], decoded["K12.dat.gz"], mapping["node"])
    if json.loads(json.dumps(bonded)) != baseline["basis_results"]["K12"]["basis"]:
        raise ValueError("Bonded K12 replay differs")
    legs = {side: recover(nodes, elements, leg) for side, leg in joint["legs"].items()}
    from mini_moonboard import box_frame as b

    revised_nodes, revised_elements, proof = release(nodes, elements, legs,
        {"left": -b.HALF, "right": b.HALF}, b.point(0, 0, 0).toTuple(), b.normal().toTuple(),
        floor_nodes=feet, load_nodes={mapping["node"], *accepted["load_nodes"]})
    node_map = {side: values["node_map"] for side, values in proof["legs"].items()}
    deck = expected_deck(revised_nodes, revised_elements, feet, mapping["node"], node_map)
    info = {"candidate": accepted["candidate"], "limits": LIMITS, "source_sha256": sources,
        "accepted_mesh_deck_sha256": accepted["deck_sha256"], "mapping": mapping,
        "floor_nodes": feet, "node_map": node_map, "release_proof": proof, "bonded_basis": bonded,
        "deck_sha256": hashlib.sha256(deck.encode()).hexdigest()}
    basis_run.unchanged(sources)
    DIRECTORY.mkdir(parents=True)
    with (DIRECTORY/"K12.inp").open("x") as stream:
        stream.write(deck)
    basis_run.save(DIRECTORY/"input.json", info)


def solve():
    info_path, prefix = DIRECTORY/"input.json", DIRECTORY/"K12"
    info = json.loads(info_path.read_text())
    basis_run.unchanged(info["source_sha256"])
    if any(p != prefix.with_suffix(".inp") for p in DIRECTORY.glob("K12.*")):
        raise FileExistsError("Refusing to overwrite release solver attempt")
    input_sha = basis_run.digest(info_path)
    if basis_run.digest(prefix.with_suffix(".inp")) != info["deck_sha256"]:
        raise ValueError("Prepared release deck changed")
    basis_run.save(prefix.with_suffix(".launch.json"), {"input_sha256": input_sha,
        "deck_sha256": info["deck_sha256"], "source_sha256": info["source_sha256"]})
    with prefix.with_suffix(".log").open("x") as stream:
        completed = subprocess.run(["ccx", "-i", "K12"], cwd=DIRECTORY,
                                   stdout=stream, stderr=subprocess.STDOUT, check=False)
    if completed.returncode or "*ERROR" in prefix.with_suffix(".log").read_text().upper():
        raise ValueError("CalculiX release solve failed; attempt retained")
    basis_run.unchanged(info["source_sha256"])
    if basis_run.digest(info_path) != input_sha or basis_run.digest(prefix.with_suffix(".inp")) != info["deck_sha256"]:
        raise ValueError("Release inputs changed during solve")
    result = audit(prefix.with_suffix(".inp").read_text(), prefix.with_suffix(".dat").read_text(), info)
    basis_run.save(prefix.with_suffix(".json"), {"candidate": info["candidate"], "limits": LIMITS,
        "input_sha256": input_sha, **result,
        "artifacts": {p.name: basis_run.digest(p) for p in DIRECTORY.glob("K12.*")}})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "solve"))
    {"prepare": prepare, "solve": solve}[parser.parse_args().command]()
