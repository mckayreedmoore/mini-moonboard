"""Conditional aggregate base-on-board actions; no individual joint demand."""
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea import timber_asymmetric as asymmetric
from fea.floor_contact import mesh
from fea.floor_contact_results import blocks
from fea.leg_joint_demand import local_components
from fea.timber_joint_demand import authenticated_inputs, resultant

OUTPUT = Path("fea/results/timber-base-demand.json")
JOINTS = Path("fea/results/timber-joint-demand.json")
ASYMMETRIC = Path("fea/results/timber-asymmetric")
LIMITS = (
    "Conditional aggregate base-on-board wrench only: header, posts, kicker and "
    "gussets form one free body. Fixed XYZ floor includes kicker-bottom contact, "
    "not just posts. No base gravity or applied load; ideal bonded isotropic "
    "timber. Not isolated gusset/backing/bolt demand, actual unanchored demand, "
    "joint resistance or approval. Original coordinates; forces N, moments Nmm. "
    "216 asymmetric scenarios are linear superpositions of nine solved bases."
)


def merge_sources(target, incoming):
    if not incoming or any(p in target and target[p] != sha for p, sha in incoming.items()):
        raise ValueError("Missing or conflicting source identity")
    asymmetric.unchanged(incoming)
    target.update(incoming)


def partition_floor(nodes, feet, leg_feet, contact_contains):
    """Exhaustive disjoint base/leg floor partition, allowing contact-boundary overlap."""
    feet = set(feet)
    if not feet or feet != {n for n, p in nodes.items() if abs(p[2]) < 1e-5}:
        raise ValueError("Floor inventory differs from complete mesh floor")
    left, right = (set(leg_feet[side]) for side in ("left", "right"))
    if not left or not right or left & right or not (left | right) <= feet:
        raise ValueError("Invalid or overlapping leg floor patches")
    by_body = {name: sorted(n for n in feet if contains(nodes[n]))
               for name, contains in contact_contains.items()}
    if any(not ids for ids in by_body.values()):
        raise ValueError("Missing expected base floor contact")
    base = set().union(*map(set, by_body.values()))
    if base & (left | right) or base | left | right != feet:
        raise ValueError("Unowned or overlapping base/leg floor nodes")
    return base, by_body


def actions(nodes, reaction, base, reference, axes):
    world = resultant({n: nodes[n] for n in base}, {n: reaction[n] for n in base}, reference)
    return {"base_on_board_world_n_nmm": world,
            "board_on_base_world_n_nmm": [-v for v in world],
            "base_on_board_local_xsn_n_nmm": local_components(world, axes)}


def asymmetric_cases(accepted, original, nodes, feet, base, reference, axes, sources, in_base):
    summary_path = ASYMMETRIC/"summary.json"
    report = json.loads(summary_path.read_text())
    if report["candidate"] != accepted["candidate"] or report["basis_solve_count"] != 9:
        raise ValueError("Asymmetric candidate differs")
    merge_sources(sources, report["source_sha256"])
    decoded = {}
    expected = {"input.json"} | {h+s for h in asymmetric.HOLDS for s in
        (".inp", ".dat", ".log", ".sta", ".launch.json", ".json")}
    if set(report["replay_archives"]) != {n+".gz" for n in expected}:
        raise ValueError("Incomplete asymmetric archives")
    for name, hashes in report["replay_archives"].items():
        path = ASYMMETRIC/name
        payload = path.read_bytes()
        raw = gzip.decompress(payload)
        if (hashlib.sha256(payload).hexdigest() != hashes["gzip_sha256"] or
                hashlib.sha256(raw).hexdigest() != hashes["uncompressed_sha256"]):
            raise ValueError("Asymmetric archive differs")
        sources[str(path)] = asymmetric.digest(path)
        decoded[name.removesuffix(".gz")] = raw.decode()
    info = json.loads(decoded["input.json"])
    if info != report["input"] or info["accepted_mesh_deck_sha256"] != accepted["deck_sha256"]:
        raise ValueError("Asymmetric input identity differs")
    result, recorded = [], iter(report["cases"])
    for hold in asymmetric.HOLDS:
        deck, dat = decoded[hold+".inp"], decoded[hold+".dat"]
        node = info["mapping"][hold]["node"]
        if node in feet or in_base(nodes[node]) or mesh(deck) != mesh(original):
            raise ValueError("Asymmetric mesh or base load differs")
        record, launch = (json.loads(decoded[hold+s]) for s in (".json", ".launch.json"))
        input_sha = hashlib.sha256(decoded["input.json"].encode()).hexdigest()
        deck_sha = hashlib.sha256(deck.encode()).hexdigest()
        if (record["input_sha256"] != input_sha or launch["input_sha256"] != input_sha or
                launch["source_sha256"] != info["source_sha256"] or
                deck_sha != info["deck_sha256"][hold] or launch["deck_sha256"] != deck_sha):
            raise ValueError("Asymmetric launch differs")
        for suffix in (".inp", ".dat", ".log", ".sta", ".launch.json"):
            if hashlib.sha256(decoded[hold+suffix].encode()).hexdigest() != record["artifacts"][hold+suffix]:
                raise ValueError("Asymmetric record artifact differs")
        if "*ERROR" in decoded[hold+".log"].upper():
            raise ValueError("Asymmetric solver error")
        basis = asymmetric.audit(deck, dat, node)
        if json.loads(json.dumps(basis)) != record["basis"] or record["basis"] != report["basis_results"][hold]["basis"]:
            raise ValueError("Asymmetric basis replay differs")
        parsed = blocks(dat)
        reactions = [parsed["forces", "FEET", float(i)] for i in (1, 2, 3)]
        if any(set(r) != feet for r in reactions):
            raise ValueError("Asymmetric floor inventory differs")
        for scenario in asymmetric.scenarios(basis, nodes[node]):
            old = next(recorded)
            if old["hold"] != hold or any(old[k] != json.loads(json.dumps(v)) for k, v in scenario.items()):
                raise ValueError("Asymmetric scenario replay differs")
            reaction = {n: [math.fsum(c*r[n][i] for c, r in zip(scenario["basis_coefficients"], reactions, strict=True))
                            for i in range(3)] for n in feet}
            result.append({"hold": hold, **scenario, **actions(nodes, reaction, base, reference, axes)})
    if next(recorded, None) is not None or len(result) != 216 or report["scenario_count"] != 216:
        raise ValueError("Wrong asymmetric scenario count")
    sources[str(summary_path)] = asymmetric.digest(summary_path)
    return result


def main():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite base-demand evidence")
    accepted, deck, dat, sources = authenticated_inputs()
    joint = json.loads(JOINTS.read_text())
    if joint["candidate"] != accepted["candidate"]:
        raise ValueError("Joint report candidate differs")
    merge_sources(sources, joint["source_sha256"])
    for path in (JOINTS, Path("fea/timber_base_demand.py"), Path("fea/timber_asymmetric.py")):
        sources[str(path)] = asymmetric.digest(path)
    import cadquery as cq

    from mini_moonboard import timber_frame as frame

    raw = {p.name: p.shape for p in frame.wood_parts(False)}
    group = {n: s for n, s in raw.items() if n == "base_header" or
             n.startswith(("base_post_", "kicker_", "timber_base_gusset_"))}
    if len(group) != 9:
        raise ValueError("Unexpected explicit base-group inventory")
    contacts = {n: s for n, s in group.items() if n.startswith(("base_post_", "kicker_"))}
    nodes, _ = mesh(deck)
    parsed = blocks(dat)
    feet = set(parsed["forces", "FEET", 1.])
    contains = lambda shape: lambda p: shape.isInside(cq.Vector(*p), 1e-5)
    base, by_body = partition_floor(nodes, feet,
        {s: joint["legs"][s]["floor_nodes"] for s in ("left", "right")},
        {n: contains(s) for n, s in contacts.items()})
    in_base = lambda p: any(contains(s)(p) for s in group.values())
    if any(in_base(nodes[n]) for n in accepted["load_nodes"]):
        raise ValueError("External load acts on base free body")
    reference = raw["base_header"].Center().toTuple()
    axes, cases = joint["local_axes_world"], []
    for step, case in enumerate(accepted["frozen_geometry"]["audited_cases"], 1):
        reaction = parsed["forces", "FEET", float(step)]
        if set(reaction) != feet:
            raise ValueError("Original floor inventory differs")
        cases.append({"case": case["name"], **actions(nodes, reaction, base, reference, axes)})
    extra = asymmetric_cases(accepted, deck, nodes, feet, base, reference, axes, sources, in_base)
    asymmetric.unchanged(sources)
    report = {"candidate": accepted["candidate"], "limits": LIMITS, "source_sha256": sources,
        "members": sorted(group), "reference_world_mm": reference, "local_axes_world": axes,
        "floor_nodes": sorted(base), "floor_nodes_by_member": by_body,
        "floor_note": "Member inventories overlap at common boundaries; resultant uses unique union. Kicker floor restraint is included, not post-only support.",
        "cases": cases, "asymmetric_cases": extra}
    with OUTPUT.open("x") as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(OUTPUT)


if __name__ == "__main__":
    main()
