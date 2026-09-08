"""Current-wide asymmetric replay and aggregate actions, not joint resistance."""
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea import wide_asymmetric as run
from fea.floor_contact_results import blocks, cross
from fea.leg_joint_demand import local_components
from fea.publish_timber_asymmetric import compliance
from fea.timber_joint_demand import resultant
from fea.wide_joint_ownership import recover

OUTPUT = Path("fea/results/wide-asymmetric")
SUFFIXES = (".inp", ".dat", ".log", ".sta", ".launch.json", ".json")


def normalized(value):
    return json.loads(json.dumps(value, allow_nan=False))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def group_actions(nodes, reactions, ownership):
    groups = {**ownership["legs"], "base": ownership["base"]}
    occupied, actions = set(), {}
    for name, group in groups.items():
        ids = set(group["floor_nodes"])
        if not ids or ids & occupied or not ids <= reactions.keys():
            raise ValueError("Invalid aggregate floor ownership")
        occupied.update(ids)
        world = resultant({n: nodes[n] for n in ids}, {n: reactions[n] for n in ids},
                          group["reference_world_mm"])
        actions[name] = {"on_board_world_n_nmm": world,
                        "on_board_local_xsn_n_nmm": local_components(world, ownership["local_axes_world"])}
    if occupied != reactions.keys():
        raise ValueError("Aggregate groups do not cover every floor reaction")
    return actions


def status_complete(text):
    rows = [line.split() for line in text.splitlines() if line.split() and line.split()[0].isdigit()]
    if len(rows) != 3:
        raise ValueError("Incomplete three-basis status")
    for step, row in enumerate(rows, 1):
        if (len(row) != 7 or int(row[0]) != step or int(row[1]) != 1
                or [float(v) for v in row[4:]] != [float(step), 1., 1.]):
            raise ValueError("Unexpected basis status history")


def replay(payload):
    expected_names = {"input.json"} | {h+s for h in run.HOLDS for s in SUFFIXES}
    if set(payload) != expected_names:
        raise ValueError("Incomplete wide asymmetric evidence")
    info = json.loads(payload["input.json"])
    expected, decks = run.preparation()
    if info != normalized(expected):
        raise ValueError("Wide preparation differs from reconstructed sources")
    ownership, nodes, _original, sources = recover([v["node"] for v in info["mapping"].values()])
    for path, digest in info["source_sha256"].items():
        if path in sources and sources[path] != digest:
            raise ValueError("Conflicting wide evidence sources")
        sources[path] = digest
    for path in ("fea/publish_wide_asymmetric.py", "fea/publish_timber_asymmetric.py",
                 "fea/leg_joint_demand.py", "fea/timber_joint_demand.py", "uv.lock"):
        sources[path] = run.digest(path)
    basis_results, cases, omitted = {}, [], {}
    for hold in run.HOLDS:
        deck, dat = payload[hold+".inp"].decode(), payload[hold+".dat"].decode()
        if deck != decks[hold] or sha(payload[hold+".inp"]) != info["deck_sha256"][hold]:
            raise ValueError("Wide deck differs from reconstructed geometry")
        record, launch = (json.loads(payload[hold+s]) for s in (".json", ".launch.json"))
        if (record["hold"] != hold or record["input_sha256"] != sha(payload["input.json"])
                or launch != {"input_sha256": sha(payload["input.json"]),
                    "deck_sha256": info["deck_sha256"][hold], "source_sha256": info["source_sha256"],
                    "timeout_seconds": run.TIMEOUT}):
            raise ValueError("Wide launch identity differs")
        required = {hold+s for s in SUFFIXES if s != ".json"}
        if (not required <= record["artifacts"].keys()
                or any(Path(n).name != n for n in record["artifacts"])
                or any(record["artifacts"][n] != sha(payload[n]) for n in required)
                or "*ERROR" in payload[hold+".log"].decode().upper()):
            raise ValueError("Wide solver artifact identity or status differs")
        omitted.update({n: h for n, h in record["artifacts"].items() if n not in required})
        status_complete(payload[hold+".sta"].decode())
        basis = run.audit(deck, dat, info["mapping"][hold]["node"])
        if normalized(basis) != record["basis"]:
            raise ValueError("Wide basis replay differs")
        parsed = blocks(dat)
        actions = [group_actions(nodes, parsed["forces", "FEET", float(i)], ownership) for i in (1, 2, 3)]
        basis_results[hold] = {"basis": basis, "compliance": compliance(basis), "aggregate_basis": actions,
                               "solver_version_banner": record["solver_version_banner"]}
        for scenario in run.scenarios(basis, nodes[info["mapping"][hold]["node"]]):
            aggregates = {}
            for name in ("left", "right", "base"):
                aggregates[name] = {key: [math.fsum(c*a[name][key][i] for c, a in
                    zip(scenario["basis_coefficients"], actions, strict=True)) for i in range(6)]
                    for key in ("on_board_world_n_nmm", "on_board_local_xsn_n_nmm")}
            # Aggregate free bodies must account for the complete floor wrench.
            origin_wrenches = []
            for name, action in aggregates.items():
                group = ownership["base"] if name == "base" else ownership["legs"][name]
                world = action["on_board_world_n_nmm"]
                offset = cross(group["reference_world_mm"], world[:3])
                origin_wrenches.append(world[:3]+[world[i+3]+offset[i] for i in range(3)])
            total = [math.fsum(w[i] for w in origin_wrenches) for i in range(6)]
            if any(abs(a-b) > (1e-6 if i < 3 else 1e-3) for i, (a, b) in
                   enumerate(zip(total, scenario["reaction_wrench_n_nmm"], strict=True))):
                raise ValueError("Aggregate wrench partition differs")
            cases.append({"hold": hold, **scenario, "aggregates": aggregates})
    if len(cases) != 216:
        raise ValueError("Wrong scenario inventory")
    run.unchanged(sources)
    return {"candidate": run.KEY, "limits": run.LIMITS, "source_sha256": sources,
        "input": info, "ownership": normalized(ownership), "basis_solve_count": 9,
        "scenario_count": len(cases), "basis_results": basis_results, "cases": cases,
        "maximum_loaded_displacement_by_weight": {str(w): max((c for c in cases if c["climber_lb"] == w),
            key=lambda c: c["loaded_displacement_magnitude_mm"]) for w in (150, 200, 250, 300)},
        "omitted_diagnostic_artifacts_sha256": omitted}


def publish():
    if OUTPUT.exists():
        raise FileExistsError("Refusing to overwrite wide asymmetric publication")
    names = {"input.json"} | {h+s for h in run.HOLDS for s in SUFFIXES}
    payload = {name: (run.DIRECTORY/name).read_bytes() for name in names}
    report = replay(payload)
    for hold in run.HOLDS:
        record = json.loads(payload[hold+".json"])
        run.unchanged({str(run.DIRECTORY/n): digest for n, digest in record["artifacts"].items()})
    archives = {name+".gz": gzip.compress(raw, mtime=0) for name, raw in payload.items()}
    report["replay_archives"] = {name+".gz": {"gzip_sha256": sha(archives[name+".gz"]),
        "uncompressed_sha256": sha(raw)} for name, raw in payload.items()}
    run.unchanged(report["source_sha256"])
    run.unchanged({str(run.DIRECTORY/n): sha(raw) for n, raw in payload.items()})
    OUTPUT.mkdir(parents=True, exist_ok=False)
    for name, raw in archives.items():
        with (OUTPUT/name).open("xb") as stream:
            stream.write(raw)
    run.save(OUTPUT/"summary.json", report)


if __name__ == "__main__":
    publish()
