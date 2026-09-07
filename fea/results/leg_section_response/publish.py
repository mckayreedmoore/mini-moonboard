"""Retain and replay a terminal section experiment; never launch a solver."""
import io
import json
import re
import tarfile
from pathlib import Path

from fea import leg_section_response as response
from fea import leg_section_run as runner
from fea.publish_moving_fixture import checked_members

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def capture(directory):
    files = {}
    require(directory.is_dir() and not directory.is_symlink(), "Real runtime directory required")
    for path in sorted(directory.rglob("*")):
        require(not path.is_symlink(), "Runtime symlink rejected")
        if path.is_file():
            files[path.relative_to(directory).as_posix()] = path.read_bytes()
    return files


def replay(files):
    """Authenticate source/deck/configuration and recompute every signed result."""
    read = lambda name: json.loads(files[name])
    launch = read("prelaunch.json")
    require(launch["geometry_archive_sha256"] == runner.GEOMETRY_SHA, "Geometry identity differs")
    require(launch["gates"] == response.GATES, "Response gates differ")
    geometric = runner.geometry()
    require(read("geometry.json") == geometric, "Recorded geometry differs")
    require(set(launch["source_sha256"]) == {n+".py" for n in runner.SOURCES}, "Source inventory differs")
    for name, digest in launch["source_sha256"].items():
        data = files["sources/"+name]
        require(runner.sha(data) == digest and data == (ROOT/"fea"/name).read_bytes(), "Runtime source differs")
    require(runner.sha(files["protocol.md"]) == launch["protocol_sha256"], "Protocol digest differs")
    require(set(launch["commands"]) == set(launch["decks"]) == {"40", "25"}, "Mesh inventory differs")
    reports, directories, incomplete = {}, set(), {}
    for size in (40, 25):
        command = launch["commands"][str(size)]
        directory = Path(command[command.index("--cidfile")+1]).parent
        directories.add(str(directory))
        expected = runner.command(directory, size)
        user_index = expected.index("--user")+1
        require(re.fullmatch(r"[0-9]+:[0-9]+", command[user_index]), "Invalid recorded user")
        # Historical native identity, not the UID/GID of this portable reader.
        expected[user_index] = command[user_index]
        require(command == expected, "Bounded command differs")
        cid = files[f"mesh{size}.cid"].decode().strip()
        require(re.fullmatch(r"[0-9a-f]{64}", cid), "Invalid owned CID")
        terminal, inspected = read(f"mesh{size}-terminal.json"), read(f"mesh{size}-inspect.json")
        state = inspected["State"]
        require(terminal["container"] == inspected["Id"] == cid, "Container identity differs")
        require(inspected["Name"] == f"/moonboard-{directory.name}-{size}" and inspected["Image"] == runner.IMAGE,
                "Container name/image differs")
        require(terminal["state"] == state and state["Running"] is False
                and terminal["termination_verified"] is True and terminal["cleanup_exit"] == 0
                and terminal["cleanup_stdout"].strip() == cid and not any(k.endswith("error") for k in terminal),
                "Native execution or owned cleanup not proven")
        host, config = inspected["HostConfig"], inspected["Config"]
        require(host["Memory"] == host["MemorySwap"] == 2*1024**3 and host["NanoCpus"] == 2*10**9
                and host["PidsLimit"] == 256 and host["NetworkMode"] == "none" and host["ReadonlyRootfs"] is True,
                "Native resource bounds differ")
        require(config["User"] == command[command.index("--user")+1]
                and {"OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2"} <= set(config["Env"])
                and config["Cmd"] == command[-7:], "Native process configuration differs")
        mounts = [m for m in inspected["Mounts"] if m["Destination"] == "/job"]
        require(len(mounts) == 1 and mounts[0]["Source"] == str(directory/f"mesh{size}")
                and mounts[0]["RW"] is True, "Native job mount differs")
        text, context = response.prepare(size)
        require(files[f"mesh{size}/section.inp"] == text.encode()
                and launch["decks"][str(size)] == context["deck_sha256"], "Native input differs")
        completed = state["ExitCode"] == terminal["launch_exit"] == 0 and state["OOMKilled"] is False
        if not completed:
            require(f"mesh{size}-audit.json" not in files and "comparison.json" not in files,
                    "Failed execution must not have a completed audit/comparison")
            incomplete[str(size)] = {"launch_exit": terminal["launch_exit"], "native_exit": state["ExitCode"],
                                     "oom_killed": state["OOMKilled"]}
            continue
        require(b"*ERROR" not in files[f"mesh{size}/process.log"].upper(), "Native error reported")
        row = geometric["meshes"][str(size)]
        reports[size] = response.audit(files[f"mesh{size}/section.dat"].decode(), context,
            {"LOWER_CUT": row["cut_surface"]["area"], "UPPER_CUT": row["reverse_cut_surface"]["area"]})
        require(reports[size] == read(f"mesh{size}-audit.json"), "Signed native replay differs")
    require(len(directories) == 1, "Mixed runtime directories")
    if incomplete:
        return {"pass": False, "qualified_for_design": False, "incomplete_execution": incomplete}
    comparison = response.compare_meshes(reports[40], reports[25])
    require(comparison == read("comparison.json"), "Mesh comparison differs")
    require(comparison["qualified_for_design"] is False, "Design qualification is forbidden")
    return comparison


def publish(directory):
    directory = Path(directory).resolve()
    files = capture(directory)
    comparison = replay(files)  # Failed numerical gates are retained, not rejected.
    require(not (HERE/"evidence.tar.gz").exists() and not (HERE/"manifest.json").exists(), "No overwrite allowed")
    files["publisher.py.snapshot"] = Path(__file__).read_bytes()
    files["members.json"] = json.dumps({n: runner.sha(b) for n, b in files.items()}, sort_keys=True).encode()
    require(capture(directory) == {n: b for n, b in files.items() if n not in {"members.json", "publisher.py.snapshot"}},
            "Runtime changed during capture")
    target = HERE/"evidence.tar.gz"
    with tarfile.open(target, "x:gz") as archive:
        for name, data in sorted(files.items()):
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(data), 0o644
            archive.addfile(member, io.BytesIO(data))
    digest = runner.sha(target.read_bytes())
    checked_members(target, digest)
    manifest = {"archive": target.name, "archive_sha256": digest, "archive_bytes": target.stat().st_size,
                "member_count": len(files), "source_run": directory.name,
                "geometry_archive_sha256": runner.GEOMETRY_SHA, "comparison_pass": comparison["pass"],
                "qualified_for_design": False,
                "limits": "Replay authenticates retained native outputs and signed gates; no solver rerun, contact or strength approval."}
    with (HERE/"manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    import sys
    publish(sys.argv[1])
