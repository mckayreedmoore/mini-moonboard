"""Nine source-bound wide-frame linear bases; no connection qualification."""
import argparse
import gzip
import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

from fea.floor_contact import mesh
from fea.floor_contact_results import blocks, cross
from fea.publish_bearing_structural import validate_metadata
from fea.solve_easy_frame import audit as global_audit
from fea.solve_easy_frame import digest, make_deck
from fea.timber_asymmetric import (
    BASIS,
    HOLDS,
    map_target,
    mesh_text,
    save,
    scenarios,  # noqa: F401 -- shared publisher API
    unchanged,
)
from fea.wide_structural import locations

KEY = "wide-principal-development"
ARCHIVE = Path("fea/results/wide-principal")
SOURCE = ARCHIVE/"mesh40.json"
DIRECTORY = Path("fea/generated/wide-asymmetric")
TIMEOUT = 600
LIMITS = ("Current wide-principal-development accepted 40mm mesh. Linear isotropic "
          "ideally bonded wood, including leg plies and leg-to-rim AND upper-panel "
          "edge interfaces; fixed XYZ floor including kicker bottom. No gravity, "
          "standoff moment, separation, actual insert/bolt compliance or strength "
          "approval. Three single-hold jobs contain nine solved bases; 216 derived "
          "scenarios are linear superpositions, not independent solves. Point stress "
          "and individual joint forces are not qualified.")


def authenticated_inputs():
    row = json.loads(SOURCE.read_text())
    if row.get("candidate") != KEY or row.get("mesh_size_mm") != 40 or not row.get("source_sha256"):
        raise ValueError("Require source-bound wide 40mm evidence")
    sources = dict(row["source_sha256"])
    for name, value in row["publisher_source_sha256"].items():
        if name in sources and sources[name] != value:
            raise ValueError("Conflicting publisher source identity")
        sources[name] = value
    unchanged(sources)
    required = {"mesh40"+suffix+".gz" for suffix in (".inp", ".dat", ".context.json", ".log", ".sta")}
    if set(row["replay_archives"]) != required:
        raise ValueError("Incomplete wide mesh archives")
    decoded = {}
    for name, hashes in row["replay_archives"].items():
        path = ARCHIVE/name
        zipped = path.read_bytes()
        raw = gzip.decompress(zipped)
        if (hashlib.sha256(zipped).hexdigest() != hashes["gzip_sha256"]
                or hashlib.sha256(raw).hexdigest() != hashes["uncompressed_sha256"]
                or hashes["uncompressed_sha256"] != row["evidence_sha256"][hashes["original_name"]]):
            raise ValueError("Wide archived evidence differs")
        decoded[name.removesuffix(".gz")] = raw.decode()
        sources[str(path)] = hashlib.sha256(zipped).hexdigest()
    deck, dat = decoded["mesh40.inp"], decoded["mesh40.dat"]
    if "*ERROR" in decoded["mesh40.log"].upper():
        raise ValueError("Archived wide solver error")
    validate_metadata(row, deck, json.loads(decoded["mesh40.context.json"]))
    replay = global_audit(deck, dat, row["frozen_geometry"])
    if any(json.loads(json.dumps(value)) != row[key] for key, value in replay.items()):
        raise ValueError("Wide global result replay differs")
    for name in (str(SOURCE), "fea/wide_asymmetric.py", "fea/timber_asymmetric.py",
                 "fea/wide_structural.py", "fea/publish_bearing_structural.py"):
        sources[name] = digest(name)
    unchanged(sources)
    return row, deck, dat, sources


def expected_deck(nodes, elements, feet, node):
    return "** "+LIMITS+"\n"+make_deck(mesh_text(nodes, elements), feet, [node], BASIS, 7000.)


def preparation():
    """Reconstruct source-derived metadata/decks without writing or solving."""
    accepted, original, _, sources = authenticated_inputs()
    nodes, elements = mesh(original)
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    targets = {label: (p, normal) for label, p, normal in locations()}
    mappings = {hold: map_target(nodes, *targets[hold], set(feet)) for hold in HOLDS}
    if len({v["node"] for v in mappings.values()}) != 3:
        raise ValueError("Distinct wide holds map to one node")
    decks = {hold: expected_deck(nodes, elements, feet, value["node"]) for hold, value in mappings.items()}
    if any(mesh(text) != (nodes, elements) for text in decks.values()):
        raise ValueError("Wide basis changes accepted mesh")
    info = {"candidate": KEY, "limits": LIMITS, "mapping": mappings, "basis": BASIS,
            "source_sha256": sources, "accepted_mesh_deck_sha256": accepted["deck_sha256"],
            "maximum_runtime_seconds": TIMEOUT,
            "deck_sha256": {h: hashlib.sha256(text.encode()).hexdigest() for h, text in decks.items()}}
    unchanged(sources)
    return info, decks


def prepare():
    if DIRECTORY.exists():
        raise FileExistsError("Refusing to overwrite wide basis preparation")
    info, decks = preparation()
    DIRECTORY.mkdir(parents=True)
    for hold, text in decks.items():
        with (DIRECTORY/f"{hold}.inp").open("x") as stream:
            stream.write(text)
    save(DIRECTORY/"input.json", info)


def audit(deck, data, node):
    nodes, elements = mesh(deck)
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    if node not in nodes or node in feet or not feet:
        raise ValueError("Invalid wide load or floor")
    if deck != expected_deck(nodes, elements, feet, node):
        raise ValueError("Wide basis deck differs")
    parsed = blocks(data)
    if set(parsed) != {(kind, name, float(i)) for i in (1, 2, 3)
                       for kind, name in (("displacements", "TOP"), ("forces", "FEET"))}:
        raise ValueError("Incomplete wide basis endpoints")
    result = []
    for i, case in enumerate(BASIS, 1):
        u, reactions = parsed["displacements", "TOP", float(i)], parsed["forces", "FEET", float(i)]
        if set(u) != {node} or set(reactions) != set(feet):
            raise ValueError("Incomplete wide reaction inventory")
        force = [math.fsum(v[j] for v in reactions.values()) for j in range(3)]
        moments = [cross(nodes[n], v) for n, v in reactions.items()]
        world = force+[math.fsum(v[j] for v in moments) for j in range(3)]
        applied = case["force_n"]+cross(nodes[node], case["force_n"])
        residual = [a+b for a, b in zip(world, applied, strict=True)]
        if max(map(abs, residual[:3])) > .1 or max(map(abs, residual[3:])) > 1.:
            raise ValueError("Wide basis force/moment imbalance")
        result.append({"name": case["name"], "force_n": case["force_n"],
            "loaded_displacement_mm": u[node], "reaction_wrench_n_nmm": world, "residual_wrench": residual})
    return result


def solve(hold):
    if hold not in HOLDS:
        raise ValueError("Unknown wide hold")
    info_path = DIRECTORY/"input.json"
    info = json.loads(info_path.read_text())
    prefix = DIRECTORY/hold
    if {p.name for p in DIRECTORY.glob(hold+".*")} != {hold+".inp"}:
        raise FileExistsError("Refusing to overwrite wide solver attempt")
    unchanged(info["source_sha256"])
    text = prefix.with_suffix(".inp").read_text()
    nodes, elements = mesh(text)
    feet = sorted(n for n, p in nodes.items() if abs(p[2]) < 1e-5)
    if (info["candidate"] != KEY or info["limits"] != LIMITS or info["basis"] != list(BASIS)
            or text != expected_deck(nodes, elements, feet, info["mapping"][hold]["node"])
            or digest(prefix.with_suffix(".inp")) != info["deck_sha256"][hold]):
        raise ValueError("Prepared wide inputs differ")
    initial = digest(info_path)
    save(prefix.with_suffix(".launch.json"), {"input_sha256": initial,
        "deck_sha256": info["deck_sha256"][hold], "source_sha256": info["source_sha256"],
        "timeout_seconds": TIMEOUT})
    try:
        with prefix.with_suffix(".log").open("x") as stream:
            completed = subprocess.run(["ccx", "-i", hold], cwd=DIRECTORY,
                env={**os.environ, "OMP_NUM_THREADS": "2"}, stdout=stream,
                stderr=subprocess.STDOUT, check=False, timeout=TIMEOUT)
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("Wide basis timed out; attempt preserved") from error
    log = prefix.with_suffix(".log").read_text()
    if completed.returncode or "*ERROR" in log.upper():
        raise RuntimeError("Wide basis solver failed; attempt preserved")
    unchanged(info["source_sha256"])
    if digest(info_path) != initial or digest(prefix.with_suffix(".inp")) != info["deck_sha256"][hold]:
        raise ValueError("Wide inputs changed during solve")
    basis = audit(text, prefix.with_suffix(".dat").read_text(), info["mapping"][hold]["node"])
    save(prefix.with_suffix(".json"), {"hold": hold, "basis": basis, "input_sha256": initial,
        "solver_version_banner": [line.strip() for line in log.splitlines() if "version" in line.lower()],
        "artifacts": {p.name: digest(p) for p in DIRECTORY.glob(hold+".*")}})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "solve"))
    parser.add_argument("--hold", choices=HOLDS)
    args = parser.parse_args(argv)
    if args.command == "solve":
        if args.hold is None:
            parser.error("solve requires --hold")
        solve(args.hold)
    else:
        if args.hold is not None:
            parser.error("--hold belongs to solve")
        prepare()


if __name__ == "__main__":
    main()
