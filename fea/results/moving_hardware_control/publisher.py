"""Archive the first rejected hardware input without rerunning archived code."""
import argparse
import io
import json
import re
import tarfile
from pathlib import Path

from fea.results.stitch_joint_mesh.publisher import archive_files, mesh, sha

HERE = Path(__file__).parent
ROOT = HERE.parents[2]
SOLVE = ROOT / "fea/generated/quiescent-solves/quiescent-an9hdwot"
PREP = ROOT / "fea/generated/moving-hardware-controls/control-n9loh3l6"
GEOMETRY = ROOT / "fea/generated/stitch-joint-geometry-kag_x3_2"
MESH = GEOMETRY / "mesh-otcxe8mb"
BODIES = {"leg_right_inner", "leg_right_outer"} | {
    f"leg_stitch_right_{i}_{part}" for i in (1, 2, 3)
    for part in ("bolt_nut", "washer_inner", "washer_outer")}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def replay(files, *, timeout=False):
    """Check preserved hashes, ownership and rejection, not contact mechanics."""
    def record(name):
        return json.loads(files[name])

    def hashes(prefix, inventory):
        for name, expected in inventory.items():
            require(sha(files[prefix + name]) == expected, "Recorded hash differs: " + prefix + name)

    manifest = record("members.json")
    require(set(manifest) == set(files) - {"members.json"}, "Archive inventory differs")
    hashes("", manifest)
    geometry, mesh_record = record("geometry/geometry.json"), record("mesh/mesh.json")
    require(set(geometry["parts"]) == set(mesh_record["bodies"]) == BODIES, "Eleven-body inventory differs")
    require(geometry["locked_threads"] is True and mesh_record["locked_threads"] is True, "Wrong thread variant")
    require(set(geometry["step_sha256"]) == {n + ".step" for n in BODIES}, "STEP inventory differs")
    hashes("geometry/", geometry["step_sha256"])
    hashes("geometry/launch_sources/", geometry["source_sha256"])
    hashes("mesh/", {n + ".snapshot": h for n, h in mesh_record["source_sha256"].items()})
    require(mesh_record["geometry_sha256"] == sha(files["geometry/geometry.json"]), "Mesh geometry binding differs")
    require(mesh_record["step_sha256"] == geometry["step_sha256"], "Mesh STEP binding differs")
    require(mesh_record["mesh_sha256"] == sha(files["mesh/mesh.inp"]), "Mesh input binding differs")
    nodes, elements, sets = mesh(files["mesh/mesh.inp"].decode())
    require(set(sets) == BODIES, "Actual mesh body inventory differs")
    owned = set()
    for name, ids in sets.items():
        body = mesh_record["bodies"][name]
        used = {n for e in ids for n in elements[e]}
        require(set(ids) == set(body["elements"]) and set(body["nodes"]) == used and not owned & used,
                "Actual mesh body ownership differs")
        owned.update(used)
    require(owned == set(nodes), "Incomplete node ownership")
    require((mesh_record["body_count"], mesh_record["node_count"], mesh_record["element_count"])
            == (11, len(nodes), len(elements)), "Mesh counts differ")
    prepared = record("prepared/freeze.json")["files_sha256"]
    hashes("prepared/", prepared)
    context = record("prepared/context.json")
    hashes("prepared/frozen/", context["input_sha256"])
    hashes("prepared/frozen/", context["source_sha256"])
    for name in ("mesh.inp", "mesh.json"):
        require(files["prepared/frozen/" + name] == files["mesh/" + name], "Prepared mesh differs")
    require(files["prepared/frozen/geometry.json"] == files["geometry/geometry.json"], "Prepared geometry differs")
    for name, expected in context["deck_sha256"].items():
        require(sha(files["prepared/" + name + ".inp"]) == expected, "Prepared deck differs")
    freeze = record("solve/freeze.json")
    hashes("solve/frozen/", freeze["inputs_sha256"])
    require(files["solve/frozen/prepared-freeze.json"] == files["prepared/freeze.json"], "Prepared freeze differs")
    require(files["solve/frozen/context.json"] == files["prepared/context.json"], "Solve context differs")
    require(files["solve/frozen/control.inp"] == files["prepared/quiescent.inp"]
            == files["solve/result/control.inp"], "Launched deck differs")
    launch, outcome = record("solve/launch.json"), record("solve/result/exit.json")
    require(launch["freeze_sha256"] == sha(files["solve/freeze.json"]), "Launch freeze differs")
    hashes("solve/result/", outcome["output_sha256"])
    expected_exit = 124 if timeout else 201
    require(outcome["returncode"] == expected_exit and outcome["cleanup_returncode"] == 0
            and outcome["status"] == "SOLVER OR CLEANUP FAILED" and outcome["exceptions"] == [], "Original failure differs")
    cid = files["solve/result/container.id"].decode().strip()
    require(re.fullmatch(r"[0-9a-f]{64}", cid) and cid == outcome["owned_container_id"], "Captured container differs")
    probe = record("solve/result/container-probe.json")
    container, = json.loads(probe["stdout"])
    require(probe["returncode"] == 0 and container["Id"] == cid
            and container["Config"]["Image"] == freeze["image"]
            and container["Name"] == "/" + launch["command"][3]
            and container["State"]["Running"] is False and container["State"]["ExitCode"] == expected_exit
            and container["State"]["OOMKilled"] is False, "Captured terminal state differs")
    cleanup = record("solve/result/cleanup.json")
    require(cleanup["returncode"] == 0 and cleanup["container_id"] == cid
            and cleanup["stdout"].strip() == cid, "Owned cleanup differs")
    log = files["solve/result/solver.log"].decode()
    headers = [
        "SUMMARY OF JOB INFORMATION", "  STEP      INC     ATT  ITRS     TOT TIME     STEP TIME      INC TIME"]
    sta = files["solve/result/control.sta"].decode().splitlines()
    require(sta[:2] == headers, "Unexpected STA headers")
    if timeout:
        rows = [line.split() for line in sta[2:]]
        require(all(len(row) == 7 for row in rows), "Malformed partial STA")
        accepted = [row for row in rows if not row[2].endswith("U")]
        require(len(accepted) == 1 and accepted[0][:4] == ["1", "1", "1", "3"]
                and list(map(float, accepted[0][4:])) == [1e-8]*3, "Partial accepted state differs")
        rejected = [row for row in rows if row[2].endswith("U")]
        require(len(rejected) == 10 and all(row[:2] == ["1", "2"] for row in rejected)
                and float(rejected[-1][-1]) == 1e-11, "Cutback history differs")
        require(files["solve/result/control.dat"] and "*ERROR reading *NODE" not in log, "Expected partial numerical output")
        command = launch["command"]
        require(command[command.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=5", "120",
                "python3", "/frozen/moving_hardware_solve.py", "--execute"]
                and launch["outer_timeout_seconds"] == 140, "Recorded timeout bounds differ")
    else:
        require("*ERROR reading *NODE. Card image:" in log and "*ERROR in calinput: at least one fatal" in log,
                "Native input rejection absent")
        require(files["solve/result/control.dat"] == b"" and len(sta) == 2, "Unexpected numerical output")
    return {"classification": "BOUNDED TIMEOUT; PARTIAL UNQUALIFIED RESPONSE" if timeout else "NATIVE INPUT REJECTED; NO ACCEPTED STATES",
            "solver_exit_code": expected_exit,
            "cleanup_exit_code": 0, "accepted_states": 1 if timeout else 0, "body_count": 11,
            "mesh_nodes": len(nodes), "mesh_elements": len(elements), "shared_body_nodes": 0,
            "control_nodes": len(context["nodes"]), "control_elements": len(context["elements"])}


def publish():
    files = {}
    for prefix, directory in (("solve/", SOLVE), ("prepared/", PREP), ("mesh/", MESH)):
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                files[prefix + path.relative_to(directory).as_posix()] = path.read_bytes()
    for path in sorted(GEOMETRY.rglob("*")):
        if path.is_file() and (path.parent == GEOMETRY or "launch_sources" in path.relative_to(GEOMETRY).parts):
            files["geometry/" + path.relative_to(GEOMETRY).as_posix()] = path.read_bytes()
    files["publisher.py"] = Path(__file__).read_bytes()
    files["mesh_parser.py"] = (HERE.parent / "stitch_joint_mesh/publisher.py").read_bytes()
    files["members.json"] = (json.dumps({n: sha(b) for n, b in sorted(files.items())}, indent=2) + "\n").encode()
    summary = replay(files)
    archive = HERE / "first-input-rejection.tar.gz"
    with tarfile.open(archive, "x:gz") as output:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            output.addfile(info, io.BytesIO(data))
    require(replay(archive_files(archive)) == summary, "Written archive replay differs")
    report = {"archive": archive.name, "archive_sha256": sha(archive.read_bytes()), "summary": summary,
              "limits": "Rejected input only; no contact response, equilibrium, geometry recomputation, mesh quality recomputation or capacity qualification."}
    with (HERE / "first-input-rejection.json").open("x") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    return report


def replay_second(files, first_archive):
    """Resolve explicitly hashed shared evidence without extracting or executing it."""
    members = json.loads(files["members.json"])
    require(set(members) == set(files) - {"members.json"}
            and all(sha(files[n]) == h for n, h in members.items()), "Second archive inventory/hash differs")
    refs = json.loads(files["references.json"])
    require(sha(Path(first_archive).read_bytes()) == refs["archive_sha256"], "Referenced first archive differs")
    first = archive_files(first_archive)
    replay(first)
    resolved = {n: b for n, b in files.items() if n not in ("members.json", "references.json")}
    for name, expected in refs["members_sha256"].items():
        require(name not in resolved and sha(first[name]) == expected, "Referenced shared member differs")
        resolved[name] = first[name]
    resolved["members.json"] = json.dumps({n: sha(b) for n, b in resolved.items()}).encode()
    return replay(resolved, timeout=True)


def publish_second():
    first_archive = HERE / "first-input-rejection.tar.gz"
    first = archive_files(first_archive)
    files = {n: b for n, b in first.items() if n.startswith(("geometry/", "mesh/"))}
    solve = ROOT / "fea/generated/quiescent-solves/quiescent-mgxeu8y1"
    prep = ROOT / "fea/generated/moving-hardware-controls/control-qci96sn1"
    for prefix, directory in (("solve/", solve), ("prepared/", prep)):
        for path in sorted(directory.rglob("*")):
            if path.is_file():
                files[prefix + path.relative_to(directory).as_posix()] = path.read_bytes()
    files["publisher.py"] = Path(__file__).read_bytes()
    files["mesh_parser.py"] = (HERE.parent / "stitch_joint_mesh/publisher.py").read_bytes()
    shared = {n: sha(b) for n, b in files.items() if first.get(n) == b}
    files = {n: b for n, b in files.items() if n not in shared}
    files["references.json"] = json.dumps({"archive": first_archive.name,
        "archive_sha256": sha(first_archive.read_bytes()), "members_sha256": shared}, indent=2).encode()
    files["members.json"] = json.dumps({n: sha(b) for n, b in sorted(files.items())}, indent=2).encode()
    summary = replay_second(files, first_archive)
    archive = HERE / "second-quiescent-timeout.tar.gz"
    with tarfile.open(archive, "x:gz") as output:
        for name, data in sorted(files.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(data), 0o644
            output.addfile(info, io.BytesIO(data))
    require(replay_second(archive_files(archive), first_archive) == summary, "Written second archive differs")
    report = {"archive": archive.name, "archive_sha256": sha(archive.read_bytes()), "summary": summary,
              "shared_archive": first_archive.name, "shared_archive_sha256": sha(first_archive.read_bytes()),
              "limits": "Partial timed-out numerical diagnostic only; not complete contact output or a physical failure result."}
    with (HERE / "second-quiescent-timeout.json").open("x") as output:
        output.write(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--second", action="store_true")
    args = parser.parse_args()
    print(json.dumps(publish_second() if args.second else publish(), indent=2))
