"""Bounded old-timber K12 panel/leg contact diagnostic, not frame approval."""
import argparse
import gzip
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from fea import timber_asymmetric as common
from fea import timber_release as released
from fea.floor_contact import FACES, mesh, node_set
from fea.publish_timber_release import validate_replay
from fea.timber_contact_faces import reconstruct
from fea.timber_joint_demand import authenticated_inputs

DIRECTORY = Path("fea/generated/timber-panel-contact")
ARCHIVE = Path("fea/results/timber-release")
FORCE = [0., 300., -300.*.45359237*9.80665*2]
TIMEOUT = 600
LIMITS = (
    "Nonlinear single K12 combined-load diagnostic on preserved timber-base-development, "
    "not current wide or insert geometry. Frictionless panel/leg contact only; ideal "
    "rim bond, N=0 common edge and bonded leg plies retained. Fixed XYZ floor includes "
    "kicker bottom; no gravity, calibrated contact stiffness, joint capacity or approval. "
    "Direct 300lb x2 downward plus300N outward force ramp; no superposition."
)


def expected_deck(info):
    nodes = {int(n): tuple(p) for n, p in info["nodes"].items()}
    elements = {int(e): tuple(ids) for e, ids in info["elements"].items()}
    if not nodes or any(len(p) != 3 or not all(map(math.isfinite, p)) for p in nodes.values()):
        raise ValueError("Invalid mesh coordinates")
    feet, load = info["floor_nodes"], info["load_node"]
    pairs = released.pair_ids(info["node_map"])
    penalty, increment = info["penalty"], info["increment"]
    if (not math.isfinite(penalty) or penalty <= 0 or not math.isfinite(increment)
            or not 0 < increment <= .25 or info["force_n"] != FORCE):
        raise ValueError("Invalid contact parameters or prescribed combined load")
    if (set(feet) != {n for n, p in nodes.items() if abs(p[2]) < 1e-5}
            or load not in nodes or load in feet or set(pairs) & (set(feet) | {load})):
        raise ValueError("Invalid floor, load or released-node ownership")
    for mapping in info["node_map"].values():
        for old, new in mapping.items():
            if nodes[int(old)] != nodes[int(new)]:
                raise ValueError("Released pair coordinates differ")
    if set(info["contact_faces"]) != {"left", "right"}:
        raise ValueError("Both panel contact pairs required")
    lines = ["** "+LIMITS, common.mesh_text(nodes, elements).rstrip()]
    for name, ids in (("TOP", [load]), ("FEET", feet), ("PAIRS", pairs)):
        lines += node_set(name, ids)
    lines += ["*MATERIAL,NAME=WOOD", "*ELASTIC", "7000,0.3", "*SOLID SECTION,ELSET=TIMBER,MATERIAL=WOOD"]
    for side in ("left", "right"):
        entries = info["contact_faces"][side]["pairs"]
        if not entries:
            raise ValueError("Empty panel contact pair")
        for label, member in (("SLAVE", "leg"), ("MASTER", "panel")):
            lines += [f"*SURFACE,NAME={label}_{side.upper()},TYPE=ELEMENT"]
            seen = set()
            for pair in entries:
                face = pair[member]
                e, f = face["element"], face["face"]
                if (e, f) in seen or f not in ("S1", "S2", "S3", "S4") or e not in elements:
                    raise ValueError("Invalid or duplicate contact face")
                actual = [elements[e][i] for i in FACES[int(f[1])-1]]
                if actual != face["nodes"]:
                    raise ValueError("Contact face connectivity differs")
                seen.add((e, f))
                lines += [f"{e},{f}"]
    lines += ["*SURFACE INTERACTION,NAME=PANEL_CONTACT", "*SURFACE BEHAVIOR,PRESSURE-OVERCLOSURE=LINEAR",
              f"{penalty:g}", "** No friction law: frictionless panel/leg contact"]
    for side in ("LEFT", "RIGHT"):
        lines += ["*CONTACT PAIR,INTERACTION=PANEL_CONTACT,TYPE=SURFACE TO SURFACE",
                  f"SLAVE_{side},MASTER_{side}"]
    lines += ["*BOUNDARY", "FEET,1,3,0", "*STEP,NLGEOM,INC=200", "*STATIC",
              f"{min(.025,increment):g},1,1e-7,{increment:g}", "*CLOAD,OP=NEW"]
    lines += [f"{load},{i},{v:.15g}" for i, v in enumerate(FORCE, 1) if v]
    for name, output in (("TOP", "U"), ("FEET", "U,RF"), ("PAIRS", "U")):
        lines += [f"*NODE PRINT,NSET={name},FREQUENCY=1", output]
    lines += ["*NODE FILE,FREQUENCY=1", "U,RF", "*CONTACT FILE,FREQUENCY=1", "CDIS,CSTR",
              "*CONTACT PRINT,FREQUENCY=1", "CDIS,CSTR,CNUM"]
    for side in ("LEFT", "RIGHT"):
        lines += [f"*CONTACT PRINT,SLAVE=SLAVE_{side},MASTER=MASTER_{side},FREQUENCY=1", "CF"]
    return "\n".join([*lines, "*END STEP", ""])


def prepare(penalty=10000., increment=.125, directory=None):
    directory = DIRECTORY if directory is None else Path(directory)
    if directory.exists():
        raise FileExistsError("Refusing to overwrite frame-contact preparation")
    accepted, original, _, sources = authenticated_inputs()
    summary_path = ARCHIVE/"summary.json"
    saved = json.loads(summary_path.read_text())
    if saved["candidate"] != accepted["candidate"] or saved["candidate"] != "timber-base-development":
        raise ValueError("Released geometry candidate differs")
    for p, sha in saved["source_sha256"].items():
        if p in sources and sources[p] != sha:
            raise ValueError("Conflicting release source")
        sources[p] = sha
    common.unchanged(sources)
    payloads = {}
    required = {n+".gz" for n in ("input.json", "K12.inp", "K12.dat", "K12.log", "K12.sta", "K12.launch.json", "K12.json")}
    if set(saved["replay_archives"]) != required:
        raise ValueError("Incomplete release archives")
    for name, hashes in saved["replay_archives"].items():
        path = ARCHIVE/name
        zipped = path.read_bytes()
        raw = gzip.decompress(zipped)
        if (hashlib.sha256(zipped).hexdigest() != hashes["gzip_sha256"] or
                hashlib.sha256(raw).hexdigest() != hashes["uncompressed_sha256"]):
            raise ValueError("Released archive differs")
        payloads[name.removesuffix(".gz")] = raw.decode()
        sources[str(path)] = common.digest(path)
    previous = json.loads(payloads["input.json"])
    if previous != saved["input"] or previous["accepted_mesh_deck_sha256"] != accepted["deck_sha256"]:
        raise ValueError("Released preparation differs")
    validate_replay(released.audit(payloads["K12.inp"], payloads["K12.dat"], previous), saved)
    joint = json.loads(released.REPORT.read_text())
    nodes, elements = mesh(original)
    legs = {s: released.recover(nodes, elements, leg) for s, leg in joint["legs"].items()}
    from mini_moonboard import box_frame as b

    faces = reconstruct(nodes, elements, legs, previous["node_map"],
        {"left": -b.HALF, "right": b.HALF}, b.point(0, 0, 0).toTuple(), b.normal().toTuple())
    revised_nodes, revised_elements, proof = released.release(nodes, elements, legs,
        {"left": -b.HALF, "right": b.HALF}, b.point(0, 0, 0).toTuple(), b.normal().toTuple(),
        floor_nodes=previous["floor_nodes"], load_nodes={previous["mapping"]["node"], *accepted["load_nodes"]})
    if (mesh(payloads["K12.inp"]) != (revised_nodes, revised_elements) or
            json.loads(json.dumps(proof)) != previous["release_proof"]):
        raise ValueError("Released mesh reconstruction differs")
    for path in (summary_path, released.REPORT, Path("fea/timber_panel_contact.py"), Path("fea/timber_contact_faces.py")):
        sources[str(path)] = common.digest(path)
    info = {"candidate": accepted["candidate"], "limits": LIMITS, "nodes": revised_nodes,
        "elements": revised_elements, "floor_nodes": previous["floor_nodes"], "load_node": previous["mapping"]["node"],
        "mapping": previous["mapping"], "force_n": FORCE, "node_map": previous["node_map"],
        "contact_faces": faces, "penalty": penalty, "increment": increment,
        "leg_floor_nodes": {s: joint["legs"][s]["floor_nodes"] for s in ("left", "right")},
        "leg_references_world_mm": {s: joint["legs"][s]["reference_world_mm"] for s in ("left", "right")},
        "pair_force_convention": "SLAVE is leg; MASTER is panel; CF acts on leg about deformed global origin",
        "source_sha256": sources, "maximum_runtime_seconds": TIMEOUT,
        "accepted_mesh_deck_sha256": accepted["deck_sha256"]}
    text = expected_deck(info)
    info["deck_sha256"] = hashlib.sha256(text.encode()).hexdigest()
    common.unchanged(sources)
    directory.mkdir(parents=True)
    with (directory/"contact.inp").open("x") as stream:
        stream.write(text)
    common.save(directory/"input.json", info)


def solve(directory=None):
    directory = DIRECTORY if directory is None else Path(directory)
    if {p.name for p in directory.iterdir()} != {"contact.inp", "input.json"}:
        raise FileExistsError("Refusing to overwrite frame-contact solver attempt")
    info = json.loads((directory/"input.json").read_text())
    common.unchanged(info["source_sha256"])
    if (info["candidate"] != "timber-base-development" or info["limits"] != LIMITS or
            (directory/"contact.inp").read_text() != expected_deck(info) or
            common.digest(directory/"contact.inp") != info["deck_sha256"]):
        raise ValueError("Prepared contact inputs differ")
    initial = common.digest(directory/"input.json")
    common.save(directory/"launch.json", {"input_sha256": initial, "deck_sha256": info["deck_sha256"],
        "source_sha256": info["source_sha256"], "timeout_seconds": TIMEOUT})
    try:
        with (directory/"contact.log").open("x") as stream:
            result = subprocess.run(["ccx", "-i", "contact"], cwd=directory,
                env={**os.environ, "OMP_NUM_THREADS": "2"}, stdout=stream, stderr=subprocess.STDOUT,
                check=False, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Frame contact timed out; attempt preserved") from error
    if result.returncode or "*ERROR" in (directory/"contact.log").read_text().upper():
        raise RuntimeError("Frame contact solver failed; attempt preserved")
    common.unchanged(info["source_sha256"])
    if common.digest(directory/"input.json") != initial or common.digest(directory/"contact.inp") != info["deck_sha256"]:
        raise ValueError("Frame contact input changed during solve")
    common.save(directory/"execution.json", {"status": "solver completed; contact audit pending", "limits": LIMITS,
        "artifacts": {p.name: common.digest(p) for p in directory.iterdir()}})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "solve"))
    parser.add_argument("--directory", type=Path, default=DIRECTORY)
    parser.add_argument("--penalty", type=float)
    parser.add_argument("--increment", type=float)
    args = parser.parse_args(argv)
    if args.command == "solve":
        if args.penalty is not None or args.increment is not None:
            parser.error("solve uses frozen preparation parameters")
        solve(args.directory)
    else:
        prepare(10000. if args.penalty is None else args.penalty,
                .125 if args.increment is None else args.increment, args.directory)


if __name__ == "__main__":
    main()
