"""Launcher preparation only; tests never start containers or a solver."""
import json
import signal
import subprocess
from pathlib import Path

import pytest

from fea import leg_section_run as launcher
from fea.leg_section_run import IMAGE, command, geometry


def test_geometry_gate_uses_authenticated_completed_evidence():
    report = geometry()
    assert set(report["meshes"]) == {"40", "25"}
    assert all(r["geometric_comparisons_within_gates"] for r in report["meshes"].values())
    assert report["qualified_for_design"] is False


def test_native_command_has_bounded_owned_job_and_no_network():
    root = Path("/tmp/leg-section-test")
    args = command(root, 40)
    assert args[:2] == ["docker", "run"]
    for key, value in (("--name", "moonboard-leg-section-test-40"),
                       ("--cidfile", "/tmp/leg-section-test/mesh40.cid"),
                       ("--network", "none"), ("--memory", "2g"),
                       ("--memory-swap", "2g"), ("--cpus", "2"),
                       ("--pids-limit", "256"), ("-v", "/tmp/leg-section-test/mesh40:/job:rw")):
        assert args[args.index(key)+1] == value
    assert "--read-only" in args
    assert args[-8:] == [IMAGE, "timeout", "--signal=TERM", "--kill-after=5", "120", "ccx", "-i", "section"]
    assert "OMP_NUM_THREADS=2" in args and "OPENBLAS_NUM_THREADS=2" in args


@pytest.mark.parametrize("fault", [None, "timeout", "interrupt", "inspect", "running", "identity",
                                    "wrong_id", "wrong_name", "missing", "invalid", "cleanup", "nonzero", "oom"])
def test_owned_cleanup_and_failure_evidence(tmp_path, monkeypatch, fault):
    (tmp_path/"mesh40").mkdir()
    cid = "a"*64
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        if args[:2] == ["docker", "run"]:
            if fault != "missing":
                (tmp_path/"mesh40.cid").write_text("bad" if fault == "invalid" else cid)
            assert kwargs["timeout"] == 140
            if fault == "timeout":
                raise subprocess.TimeoutExpired(args, 140)
            if fault == "interrupt":
                signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
            return subprocess.CompletedProcess(args, 1 if fault == "nonzero" else 0)
        assert args == ["docker", "rm", "-f", cid]
        # A second real signal remains blocked until terminal evidence is saved.
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, [])
        assert {signal.SIGINT, signal.SIGTERM} <= blocked
        if fault == "cleanup":
            raise subprocess.TimeoutExpired(args, 10)
        return subprocess.CompletedProcess(args, 0, cid+"\n", "")

    def inspect(args, **kwargs):
        assert args == ["docker", "inspect", cid] and kwargs["timeout"] == 10
        if fault == "inspect":
            raise OSError("inspection unavailable")
        return json.dumps([{"Id": "b"*64 if fault == "wrong_id" else cid,
            "Name": "wrong" if fault == "wrong_name" else "/moonboard-"+tmp_path.name+"-40",
            "Image": "wrong" if fault == "identity" else IMAGE,
            "State": {"Running": fault == "running", "ExitCode": 0, "OOMKilled": fault == "oom"}}]).encode()

    original_save = launcher.save

    def save(path, value):
        if path.name.endswith("-terminal.json"):
            assert {signal.SIGINT, signal.SIGTERM} <= signal.pthread_sigmask(signal.SIG_BLOCK, [])
        original_save(path, value)

    monkeypatch.setattr(launcher.subprocess, "run", run)
    monkeypatch.setattr(launcher.subprocess, "check_output", inspect)
    monkeypatch.setattr(launcher, "save", save)
    old_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    if fault is None:
        assert launcher.execute(tmp_path, 40)["termination_verified"]
    else:
        with pytest.raises(RuntimeError, match="failed or uncertain"):
            launcher.execute(tmp_path, 40)
    terminal = json.loads((tmp_path/"mesh40-terminal.json").read_text())
    assert len(calls) == (1 if fault in {"identity", "wrong_id", "wrong_name", "missing", "invalid"} else 2)
    assert old_handlers == {sig: signal.getsignal(sig) for sig in old_handlers}
    if fault in {"inspect", "running", "missing", "invalid"}:
        assert terminal["termination_verified"] is False


def test_existing_cid_prevents_launch(tmp_path, monkeypatch):
    (tmp_path/"mesh40.cid").write_text("a"*64)
    monkeypatch.setattr(launcher.subprocess, "run", lambda *a, **k: pytest.fail("must not launch"))
    with pytest.raises(ValueError, match="already exists"):
        launcher.execute(tmp_path, 40)


def test_source_drift_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "SOURCES", ("leg_section_run",))
    source = Path("fea/leg_section_run.py").read_bytes()
    (tmp_path/"leg_section_run.py").write_bytes(source)
    launcher.check_sources(tmp_path)
    (tmp_path/"leg_section_run.py").write_bytes(source+b"\n")
    with pytest.raises(ValueError, match="source changed"):
        launcher.check_sources(tmp_path)
