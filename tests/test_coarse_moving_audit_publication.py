"""Replay the failed first audit and two native rows, not a balance evaluation."""
import gzip
import hashlib
import json
import math
import re
from pathlib import Path

import pytest

from fea.publish_moving_fixture import checked_members
from fea.results.stitch_joint_mesh.publisher import sha

HERE = Path(__file__).resolve().parents[1] / "fea/results/coarse_moving_control"
ARCHIVE_SHA = "3c1ca9a3a281a928cf2194e0e15d9102ba657b8f1af693e4f62e745f2b8b4e66"
PREPARATION_SHA = "053d6c06995cb76c666ec8eae85178be299747db96cadd220cabc8355bb5c9d1"
DAT_SHA = "1d106908563f4a8014c892d58cf31f7a95fac1d205679cfcd1016540b3def65a"


@pytest.fixture(scope="module")
def evidence():
    return checked_members(HERE / "first-audit.tar.gz", ARCHIVE_SHA)


def test_failed_audit_process_and_owned_cleanup_are_retained(evidence):
    files = evidence
    refs, outcome, runtime, command, cleanup = [json.loads(files[n]) for n in
        ("references.json", "audit/exit.json", "audit/runtime.json", "audit/command.json", "audit/cleanup.json")]
    assert refs["preparation_sha256"] == PREPARATION_SHA
    with (HERE / "preparation.tar.gz").open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == PREPARATION_SHA
    assert refs["DAT_sha256"] == DAT_SHA
    assert sha((HERE / "native-output.json").read_bytes()) == refs["native_output_manifest_sha256"]
    assert outcome["status"] == "AUDIT PROCESS OR CLEANUP FAILED"
    assert outcome["returncode"] == 1 and outcome["cleanup_returncode"] == 0
    assert outcome["exceptions"] == [] and outcome["numerical_status"] is None
    assert outcome["container_stopped_successfully_before_cleanup"] is False
    assert 0 < outcome["elapsed_seconds"] < 900
    assert set(outcome["files_sha256"]) == {n.removeprefix("audit/") for n in files if n.startswith("audit/")} - {"exit.json"}
    assert all(sha(files["audit/" + n]) == h for n, h in outcome["files_sha256"].items())
    assert not any(n.startswith("audit/reports/") for n in files)
    assert runtime["inner_timeout_seconds"] == 900 and runtime["outer_timeout_seconds"] == 920
    assert runtime["memory_bytes"] == runtime["memory_plus_swap_bytes"] == 8 * 1024**3
    assert runtime["cpus"] == 2
    assert sha(files["audit/supervisor.py.snapshot"]) == runtime["supervisor_sha256"]
    assert sha(files["audit/solver-exit.json.snapshot"]) == runtime["solver_exit_sha256"]
    assert sha(files["audit/command.json"]) == runtime["command_sha256"]
    assert command[command.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=5", "900",
        "python3", "-m", "fea.moving_hardware_audit", "/input", "--output", "/output"]
    assert all(option in command for option in ("--network=none", "--read-only", "--memory=8g", "--memory-swap=8g",
                                                 "--cpus=2", "--pids-limit=256"))
    assert command[command.index("--user") + 1] == "1000:1000"
    assert runtime["image"] == "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
    assert runtime["image"] in command
    cid = files["audit/container.id"].decode().strip()
    assert re.fullmatch(r"[0-9a-f]{64}", cid) and cid == outcome["owned_container_id"]
    probe = json.loads(files["audit/container-probe.json"])
    assert probe["returncode"] == 0 and probe["command"] == ["docker", "inspect", cid]
    container, = json.loads(probe["stdout"])
    assert container["Id"] == cid and container["Name"] == "/" + command[3]
    assert container["Config"]["Image"] == runtime["image"]
    assert container["State"]["ExitCode"] == 1 and container["State"]["Running"] is False
    assert container["State"]["OOMKilled"] is False
    assert cleanup["returncode"] == 0 and cleanup["container_id"] == cleanup["stdout"].strip() == cid
    assert cleanup["command"] == ["docker", "rm", "-f", cid]
    solver = json.loads(files["audit/solver-exit.json.snapshot"])
    assert solver["returncode"] == solver["cleanup_returncode"] == 0
    assert solver["output_sha256"]["control.dat"] == DAT_SHA
    log = files["audit/audit.log"].decode()
    assert "quiet.outputs(dat_text, times, context)" in log
    assert log.rstrip().endswith("ValueError: Contact pressure/penetration differs")


def test_two_diagnostic_rows_recover_from_streamed_native_dat(evidence):
    files = evidence
    report = json.loads(files["diagnostic/report.json"])
    assert sha(files["diagnostic/scan.py.snapshot"]) == report["script_sha256"]
    assert report["DAT_sha256"] == DAT_SHA
    prepared = checked_members(HERE / "preparation.tar.gz", PREPARATION_SHA)
    assert sha(prepared["prepared/context.json"]) == report["context_sha256"]
    context = json.loads(prepared["prepared/context.json"])
    del prepared
    targets = {row["time_s"]: row for row in (report["first"], report["worst"])}
    assert set(targets) == {1.07e-5, 1.61e-5}
    assert report["counts"] == {"states": 200, "rows": 582445, "failed_rows": 2, "negative_pressure_positive_gap": 2}
    assert report["alignment_and_ownership"] == "all rows passed"
    prefixes = {"relative contact displacement (": "CDIS", "contact stress (": "CSTR", "contact spring energy (": "CELS"}
    header = re.compile(rb"^\s*([^\n]+?(?:and time|for time))\s+(\S+)\s*$")
    found, digest = {}, hashlib.sha256()
    target = kind = None
    row_index = 0
    with gzip.open(HERE / "control.dat.gz", "rb") as stream:
        for line in stream:
            digest.update(line)
            match = header.match(line)
            if match:
                target = targets.get(float(match[2]))
                name = match[1].decode().strip()
                kind = next((k for prefix, k in prefixes.items() if name.startswith(prefix)), None)
                row_index = 0
            elif target is not None and kind is not None:
                row = line.strip()
                if not row or row.startswith(b"INCREMENT"):
                    continue
                if row_index == target["row_index"]:
                    found[target["time_s"], kind] = list(map(float, row.split()))
                row_index += 1
    assert digest.hexdigest() == DAT_SHA
    assert len(found) == 6
    for t, target in targets.items():
        for kind in prefixes.values():
            assert found[t, kind] == target[kind]
        dis, stress, energy = [found[t, kind] for kind in ("CDIS", "CSTR", "CELS")]
        assert dis[:2] == stress[:2] == energy[:2]
        assert dis[:2] in context["surfaces"][target["pair"]]["faces"]
        assert dis[2] > 0 and stress[2] < 0
        assert math.isclose(stress[2], -1e5*dis[2], rel_tol=5e-6, abs_tol=1e-10)
        assert target["expected_pressure"] == 0 and target["residual_over_tolerance"] > 199999
        assert energy[2] == 0  # Recorded zero only; not validated by a spring-energy formula.
