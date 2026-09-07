"""Bounded contact-free native section experiment; not a strength assessment."""
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
from pathlib import Path

from fea import leg_section_response as response
from fea.leg_section_geometry import assess
from fea.publish_moving_fixture import checked_members

IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
GEOMETRY_SHA = "534c1c9ade2c06aface3a1a53f8014bba7ef4eff95ca88061ea8fb17f1407563"
SOURCES = ("leg_section_run", "leg_section_response", "leg_section_geometry",
           "leg_section_preflight", "independent_leg_response", "independent_ply_control",
           "floor_contact", "floor_contact_results", "section_force_coupon", "section_force_tet_coupon")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+"\n")


def geometry():
    files = checked_members(Path("fea/results/leg_section_geometry/evidence.tar.gz"), GEOMETRY_SHA)
    report = json.loads(files["completed/output/report.json"])
    for name in SOURCES:
        key = f"completed/frozen/fea/{name}.py"
        if key in files and files[key] != Path(f"fea/{name}.py").read_bytes():
            raise ValueError("Geometry runtime source changed")
    for row in report["meshes"].values():
        import math
        cut, reverse = row["cut_surface"], row["reverse_cut_surface"]
        opposed = math.hypot(*(a+b for a, b in zip(cut["area_vector"], reverse["area_vector"], strict=True)))/cut["area"]
        result = assess(row["surface"]["8"], row["surface"]["12"], row["volume_integral_mm3"],
                        row["volume_first_moment_local_mm4"], row["characteristic_length_mm"], opposed)
        if not result["geometric_comparisons_within_gates"]:
            raise ValueError("Geometry gates not satisfied")
    return report


def command(directory, size):
    job = directory/f"mesh{size}"
    return ["docker", "run", "--name", f"moonboard-{directory.name}-{size}",
            "--cidfile", str(directory/f"mesh{size}.cid"), "--network", "none", "--read-only",
            "--memory", "2g", "--memory-swap", "2g", "--cpus", "2", "--pids-limit", "256",
            "--user", f"{os.getuid()}:{os.getgid()}", "--tmpfs", "/tmp:rw,size=128m",
            "-e", "OMP_NUM_THREADS=2", "-e", "OPENBLAS_NUM_THREADS=2",
            "-v", f"{job}:/job:rw", "-w", "/job", IMAGE,
            "timeout", "--signal=TERM", "--kill-after=5", "120", "ccx", "-i", "section"]


def execute(directory, size):
    """One launch; only a fresh Docker-written CID authorizes cleanup."""
    cidfile = directory/f"mesh{size}.cid"
    if cidfile.exists():
        raise ValueError("Owned CID path already exists; no launch")
    terminal = {"launch_exit": None, "termination_verified": False}
    previous = {}

    def interrupted(signum, frame):
        raise InterruptedError(f"Launcher interrupted by signal {signum}")

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.signal(sig, interrupted)
        with (directory/f"mesh{size}/process.log").open("w") as log:
            try:
                terminal["launch_exit"] = subprocess.run(command(directory, size), stdout=log,
                    stderr=subprocess.STDOUT, timeout=140, check=False).returncode
            except (Exception, KeyboardInterrupt) as error:  # noqa: BLE001 -- preserve any launch failure before cleanup
                terminal["launch_error"] = f"{type(error).__name__}: {error}"
    finally:
        mask = signal.pthread_sigmask(signal.SIG_BLOCK, previous)
        try:
            cid = cidfile.read_text().strip() if cidfile.exists() else ""
            if not re.fullmatch(r"[0-9a-f]{64}", cid):
                terminal["error"] = "No valid owned container ID; no cleanup attempted"
            else:
                terminal["container"] = cid
                identity_matches = True
                try:
                    inspected = json.loads(subprocess.check_output(["docker", "inspect", cid], timeout=10))[0]
                    save(directory/f"mesh{size}-inspect.json", inspected)
                    identity_matches = (inspected["Id"] == cid and
                        inspected["Name"] == f"/moonboard-{directory.name}-{size}" and inspected["Image"] == IMAGE)
                    if not identity_matches:
                        raise ValueError("Container identity differs; no cleanup attempted")
                    terminal["state"] = inspected["State"]
                    terminal["termination_verified"] = not inspected["State"]["Running"]
                except Exception as error:  # noqa: BLE001 -- inspect failure must not skip owned-CID cleanup
                    terminal["inspect_error"] = f"{type(error).__name__}: {error}"
                if identity_matches:
                    # A fresh CID still identifies our creation if inspection fails.
                    try:
                        cleanup = subprocess.run(["docker", "rm", "-f", cid], capture_output=True,
                                                 text=True, timeout=10, check=False)
                        terminal.update(cleanup_exit=cleanup.returncode, cleanup_stdout=cleanup.stdout,
                                        cleanup_stderr=cleanup.stderr)
                    except Exception as error:  # noqa: BLE001 -- retain uncertain cleanup
                        terminal["cleanup_error"] = f"{type(error).__name__}: {error}"
        except Exception as error:  # noqa: BLE001 -- always persist terminal evidence
            terminal["cleanup_error"] = f"{type(error).__name__}: {error}"
        finally:
            try:
                save(directory/f"mesh{size}-terminal.json", terminal)
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
                signal.pthread_sigmask(signal.SIG_SETMASK, mask)
    state = terminal.get("state", {})
    if (terminal["launch_exit"] != 0 or not terminal["termination_verified"] or
            terminal.get("cleanup_exit") != 0 or terminal.get("cleanup_stdout", "").strip() != terminal.get("container") or
            state.get("ExitCode") != 0 or state.get("OOMKilled") is not False or
            any(k.endswith("error") for k in terminal)):
        raise RuntimeError("Native execution/cleanup failed or uncertain; evidence retained")
    return terminal


def check_sources(frozen):
    if any((frozen/f"{name}.py").read_bytes() != Path(f"fea/{name}.py").read_bytes() for name in SOURCES):
        raise ValueError("Runtime source changed from prelaunch snapshot")


def main():
    geometric = geometry()
    directory = Path(tempfile.mkdtemp(prefix="leg-section-response-", dir="fea/generated")).resolve()
    frozen = directory/"sources"
    frozen.mkdir()
    for name in SOURCES:
        (frozen/f"{name}.py").write_bytes(Path(f"fea/{name}.py").read_bytes())
    (directory/"protocol.md").write_bytes(Path("docs/leg-section-protocol.md").read_bytes())
    save(directory/"geometry.json", geometric)
    contexts = {}
    for size in (40, 25):
        job = directory/f"mesh{size}"
        job.mkdir()
        text, contexts[size] = response.prepare(size)
        (job/"section.inp").write_text(text)
    save(directory/"prelaunch.json", {"geometry_archive_sha256": GEOMETRY_SHA,
         "source_sha256": {p.name: sha(p.read_bytes()) for p in frozen.iterdir()},
         "protocol_sha256": sha((directory/"protocol.md").read_bytes()),
         "decks": {str(s): contexts[s]["deck_sha256"] for s in contexts},
         "commands": {str(s): command(directory, s) for s in contexts}, "gates": response.GATES})
    print(directory, flush=True)
    reports = {}
    for size in (40, 25):
        job = directory/f"mesh{size}"
        check_sources(frozen)
        if sha((job/"section.inp").read_bytes()) != contexts[size]["deck_sha256"]:
            raise ValueError("Native input changed before launch")
        execute(directory, size)
        check_sources(frozen)
        if sha((job/"section.inp").read_bytes()) != contexts[size]["deck_sha256"]:
            raise ValueError("Native input changed")
        if "*ERROR" in (job/"process.log").read_text().upper():
            raise ValueError("Native solver reported an error")
        row = geometric["meshes"][str(size)]
        reports[size] = response.audit((job/"section.dat").read_text(), contexts[size],
                       {"LOWER_CUT": row["cut_surface"]["area"], "UPPER_CUT": row["reverse_cut_surface"]["area"]})
        save(directory/f"mesh{size}-audit.json", reports[size])
        print(size, "section gates", reports[size]["pass"], flush=True)
    save(directory/"comparison.json", response.compare_meshes(reports[40], reports[25]))


if __name__ == "__main__":
    main()
