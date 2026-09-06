"""Mocked quiescent orchestration only; never launch Docker or a solver."""

import json
import math
import signal
import subprocess
from pathlib import Path

import pytest

from fea import moving_hardware_solve as solve

CID = "a" * 64


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    source = tmp_path / "prepared"
    source.mkdir()
    (source / "quiescent.inp").write_text("quiescent fixture\n")
    (source / "moving.inp").write_text("must never launch\n")
    solve.save(source / "context.json", {
        "cases": {"quiescent": {"initial_velocity_mm_s": {"BOLT_NUT": [0., 0., 0.], "WASHER": [0., 0., 0.]}}},
        "diagnostic_reference_scales": {"status": "SOURCE-RECONSTRUCTED REFERENCE SCALES; no contact output qualification",
            "reference_mass_tonne": 1., "P_star_tonne_mm_s": math.sqrt(20000), "E_star_N_mm": 10000.,
            "H_star_tonne_mm2_s": 57.15 * math.sqrt(20000)},
        "deck_sha256": {"quiescent": solve.sha(source / "quiescent.inp")}, "input_sha256": {}, "source_sha256": {}})
    solve.save(source / "freeze.json", {"files_sha256": {p.name: solve.sha(p) for p in source.iterdir()}})
    build = tmp_path / "build.json"
    solve.save(build, {"binary_sha256": {solve.BINARY: "fixture"}})
    monkeypatch.setattr(solve, "BUILD", build)
    return source


def mock_docker(monkeypatch, directory, *, code=0, running=False, oom=False, cleanup_code=0,
                error=None, wrong_name=False, wrong_id=False, wrong_image=False, mutation=False):
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[1] == "run":
            assert kwargs["timeout"] == int(cmd[cmd.index("--kill-after=5") + 1]) + 20
            assert not Path(cmd[cmd.index("--cidfile") + 1]).exists()
            Path(cmd[cmd.index("--cidfile") + 1]).write_text(CID + "\n")
            kwargs["stdout"].write(b"retained solver output\n")
            (directory / "result/control.dat").write_bytes(b"partial native output\n")
            if mutation:
                (directory / "frozen/control.inp").write_text("changed")
            if error:
                raise error
            return subprocess.CompletedProcess(cmd, code)
        if cmd[1] == "inspect":
            assert cmd[-1] == CID
            data = [{"Id": "b" * 64 if wrong_id else CID,
                     "Name": "/foreign" if wrong_name else "/" + solve.command(directory)[3],
                     "Config": {"Image": "foreign" if wrong_image else solve.IMAGE},
                     "State": {"Running": running, "ExitCode": code, "OOMKilled": oom}}]
            return subprocess.CompletedProcess(cmd, 0, json.dumps(data).encode(), b"")
        assert cmd == ["docker", "rm", "-f", CID]
        return subprocess.CompletedProcess(cmd, cleanup_code, b"removed", b"")
    monkeypatch.setattr(solve.subprocess, "run", run)
    return calls


def test_prepare_only_freezes_quiescent_and_preserves_inputs(prepared, tmp_path, monkeypatch):
    original = {p.name: solve.sha(p) for p in prepared.iterdir()}
    monkeypatch.setattr(solve.subprocess, "run", lambda *a, **k: pytest.fail("prepare must not launch"))
    first = solve.prepare(prepared, tmp_path / "runs")
    second = solve.prepare(prepared, tmp_path / "runs")
    assert first != second
    assert solve.verify(first)["case"] == "quiescent"
    assert (first / "frozen/control.inp").read_bytes() == (prepared / "quiescent.inp").read_bytes()
    assert not (first / "frozen/moving.inp").exists()
    assert {p.name: solve.sha(p) for p in prepared.iterdir()} == original
    assert not (first / "launch.json").exists()


def test_resource_bounds_and_frozen_entrypoint(tmp_path):
    cmd = solve.command(tmp_path)
    for flag in ("--network=none", "--read-only", "--memory=4g", "--memory-swap=4g", "--cpus=2",
                 "OMP_NUM_THREADS=2", "/tmp:size=128m", solve.IMAGE):
        assert flag in cmd
    assert cmd[cmd.index("timeout"):] == ["timeout", "--signal=TERM", "--kill-after=5", "120",
                                          "python3", "/frozen/moving_hardware_solve.py", "--execute"]
    assert f"{tmp_path / 'frozen'}:/frozen:ro" in cmd
    assert f"{tmp_path / 'freeze.json'}:/freeze.json:ro" in cmd
    assert cmd[cmd.index("--cidfile") + 1] == str(tmp_path / "result/container.id")


def test_explicit_longer_cap_is_frozen_and_observed(prepared, tmp_path, monkeypatch):
    directory = solve.prepare(prepared, tmp_path / "runs", solver_timeout_seconds=180)
    assert solve.verify(directory)["solver_timeout_seconds"] == 180
    calls = mock_docker(monkeypatch, directory)
    solve.launch(directory)
    assert calls[0][calls[0].index("--kill-after=5") + 1] == "180"
    assert json.loads((directory / "launch.json").read_text())["outer_timeout_seconds"] == 200


@pytest.mark.parametrize("seconds", [True, 180., 0, 121, 10000])
def test_unbounded_or_undeclared_cap_rejected(prepared, tmp_path, seconds):
    with pytest.raises(ValueError, match="predeclared"):
        solve.prepare(prepared, tmp_path / "runs", solver_timeout_seconds=seconds)
    assert not (tmp_path / "runs").exists()


def test_success_is_only_solver_completion_and_cannot_repeat(prepared, tmp_path, monkeypatch):
    directory = solve.prepare(prepared, tmp_path / "runs")
    calls = mock_docker(monkeypatch, directory)
    result = solve.launch(directory)
    report = json.loads((result / "exit.json").read_text())
    assert report["status"] == "SOLVER COMPLETED; AUDIT PENDING"
    assert report["container_stopped_successfully_before_cleanup"] is True
    assert report["output_sha256"]["control.dat"] == solve.sha(result / "control.dat")
    launch_bytes = (directory / "launch.json").read_bytes()
    with pytest.raises(FileExistsError):
        solve.launch(directory)
    assert len(calls) == 3
    assert (directory / "launch.json").read_bytes() == launch_bytes


@pytest.mark.parametrize("failure", ["timeout", "interrupt", "nonzero", "running", "oom", "cleanup", "wrong_name", "wrong_id", "wrong_image", "mutation"])
def test_failures_retain_partial_evidence_and_clean_exact_container(prepared, tmp_path, monkeypatch, failure):
    directory = solve.prepare(prepared, tmp_path / "runs")
    kwargs = {"error": subprocess.TimeoutExpired("docker", 140)} if failure == "timeout" else (
        {"error": KeyboardInterrupt("test interrupt")} if failure == "interrupt" else
        {"code": 7} if failure == "nonzero" else
        {"cleanup_code": 1} if failure == "cleanup" else {failure: True})
    calls = mock_docker(monkeypatch, directory, **kwargs)
    with pytest.raises((RuntimeError, ValueError, KeyboardInterrupt, subprocess.TimeoutExpired)):
        solve.launch(directory)
    assert calls[-1] == ["docker", "rm", "-f", CID]
    report = json.loads((directory / "result/exit.json").read_text())
    assert report["status"] == "SOLVER OR CLEANUP FAILED"
    for name in ("solver.log", "control.dat", "container-probe.json", "cleanup.json"):
        assert report["output_sha256"][name] == solve.sha(directory / "result" / name)


@pytest.mark.parametrize("cid", [None, "", "existing-container", "b" * 12, "../foreign"])
def test_failed_creation_never_inspects_or_removes_a_container_name(prepared, tmp_path, monkeypatch, cid):
    directory = solve.prepare(prepared, tmp_path / "runs")
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        assert cmd[1] == "run", "name conflict must never inspect or remove the existing container"
        kwargs["stdout"].write(b"Conflict: container name already in use\n")
        if cid is not None:
            Path(cmd[cmd.index("--cidfile") + 1]).write_text(cid)
        return subprocess.CompletedProcess(cmd, 125)
    monkeypatch.setattr(solve.subprocess, "run", run)
    with pytest.raises((OSError, ValueError)):
        solve.launch(directory)
    assert len(calls) == 1
    report = json.loads((directory / "result/exit.json").read_text())
    assert report["owned_container_id"] is None
    assert report["cleanup_returncode"] is None
    assert report["status"] == "SOLVER OR CLEANUP FAILED"
    assert report["output_sha256"]["solver.log"] == solve.sha(directory / "result/solver.log")


def test_changed_prepared_input_or_frozen_source_never_launches(prepared, tmp_path, monkeypatch):
    monkeypatch.setattr(solve.subprocess, "run", lambda *a, **k: pytest.fail("must not launch"))
    directory = solve.prepare(prepared, tmp_path / "runs")
    (prepared / "quiescent.inp").write_text("changed")
    with pytest.raises(ValueError, match="provenance"):
        solve.prepare(prepared, tmp_path / "runs")
    (directory / "frozen/moving_hardware_solve.py").write_text("different source")
    with pytest.raises(ValueError, match="Frozen"):
        solve.launch(directory)
    record = json.loads((directory / "freeze.json").read_text())
    record["inputs_sha256"]["moving_hardware_solve.py"] = solve.sha(directory / "frozen/moving_hardware_solve.py")
    (directory / "freeze.json").write_text(json.dumps(record))
    with pytest.raises(ValueError, match="Executing"):
        solve.launch(directory)
    assert not (directory / "launch.json").exists()


@pytest.mark.parametrize("value", [None, "pending", False, 0., -1., math.nan, math.inf])
def test_pending_native_reference_rejected_before_preparing_or_launching(prepared, tmp_path, monkeypatch, value):
    directory = solve.prepare(prepared, tmp_path / "runs")
    monkeypatch.setattr(solve.subprocess, "run", lambda *a, **k: pytest.fail("pending reference must not launch"))
    context = json.loads((prepared / "context.json").read_text())
    context["diagnostic_reference_scales"]["reference_mass_tonne"] = value
    for root, context_path, inventory_path, key in (
        (prepared, prepared / "context.json", prepared / "freeze.json", "files_sha256"),
        (directory, directory / "frozen/context.json", directory / "freeze.json", "inputs_sha256")):
        context_path.write_text(json.dumps(context))
        record = json.loads(inventory_path.read_text())
        record[key]["context.json"] = solve.sha(context_path)
        inventory_path.write_text(json.dumps(record))
        with pytest.raises(ValueError, match="Native reference"):
            solve.prepare(root, tmp_path / "runs") if root == prepared else solve.launch(root)
    assert not (directory / "launch.json").exists()


def test_reference_status_and_formulas_must_match(prepared):
    context = json.loads((prepared / "context.json").read_text())
    context["diagnostic_reference_scales"]["E_star_N_mm"] *= 2
    with pytest.raises(ValueError, match="formula"):
        solve.check_reference(context)
    context["diagnostic_reference_scales"]["status"] = "FORMULAS ONLY"
    with pytest.raises(ValueError, match="pending"):
        solve.check_reference(context)


def test_second_real_signal_is_deferred_until_cleanup_and_exit_record(prepared, tmp_path, monkeypatch):
    directory = solve.prepare(prepared, tmp_path / "runs")
    events = []
    old_handler = signal.getsignal(signal.SIGTERM)

    def restored_handler(signum, frame):
        assert (directory / "result/exit.json").exists()
        events.append("pending_signal_delivered")

    def run(cmd, **kwargs):
        if cmd[1] == "run":
            Path(cmd[cmd.index("--cidfile") + 1]).write_text(CID)
            kwargs["stdout"].write(b"partial output")
            signal.raise_signal(signal.SIGTERM)
            pytest.fail("first signal must interrupt solver wait")
        assert {signal.SIGINT, signal.SIGTERM} <= signal.pthread_sigmask(signal.SIG_BLOCK, [])
        if cmd[1] == "inspect":
            signal.raise_signal(signal.SIGTERM)
            events.append("second_signal_pending")
            return subprocess.CompletedProcess(cmd, 1, b"[]", b"probe failed")
        assert cmd == ["docker", "rm", "-f", CID]
        events.append("container_removed")
        return subprocess.CompletedProcess(cmd, 0, b"removed", b"")

    monkeypatch.setattr(solve.subprocess, "run", run)
    signal.signal(signal.SIGTERM, restored_handler)
    try:
        with pytest.raises(KeyboardInterrupt, match="Received signal"):
            solve.launch(directory)
    finally:
        signal.signal(signal.SIGTERM, old_handler)
    assert events == ["second_signal_pending", "container_removed", "pending_signal_delivered"]
    report = json.loads((directory / "result/exit.json").read_text())
    assert report["status"] == "SOLVER OR CLEANUP FAILED"
    assert "cleanup.json" in report["output_sha256"]


@pytest.mark.parametrize("failure", ["build", "binary"])
def test_container_identity_failure_prevents_solver_exec(tmp_path, monkeypatch, failure):
    real_path = Path
    frozen = tmp_path / "frozen"
    frozen.mkdir()
    solve.save(frozen / "build_manifest.json", {"binary_sha256": {solve.BINARY: "bad"}})
    (tmp_path / "freeze.json").write_text("{}")
    installed = tmp_path / "installed.json"
    installed.write_text("{}" if failure == "build" else (frozen / "build_manifest.json").read_text())
    binary = tmp_path / "ccx"
    binary.write_bytes(b"native fixture")
    mapping = {"/frozen": frozen, "/freeze.json": tmp_path / "freeze.json",
               "/opt/ccx-upstream-2.21/build_manifest.json": installed, solve.BINARY: binary}
    monkeypatch.setattr(solve, "Path", lambda path: mapping.get(str(path), real_path(path)))
    monkeypatch.setattr(solve, "check_frozen", lambda *args: None)
    monkeypatch.setattr(solve.os, "execv", lambda *args: pytest.fail("identity failure must not execute"))
    with pytest.raises(ValueError, match="manifest" if failure == "build" else "executable"):
        solve.execute()
