"""Mocked quiescent orchestration only; never launch Docker or a solver."""

import copy
import gzip
import json
import math
import shutil
import signal
import subprocess
from pathlib import Path

import pytest

from fea import moving_hardware_solve as solve

CID = "a" * 64


@pytest.fixture(scope="module")
def moving_prepared(tmp_path_factory):
    """Replay real quiet proof; reuse its unchanged-coordinate matrices, not a solve."""
    from fea import hardware_mass_cache as mass
    from fea import moving_hardware_event as event

    parent = tmp_path_factory.mktemp("moving-launch-fixture")
    prepared = event.prepare(parent)
    evidence = event.archived_files(event.ARCHIVE.read_bytes())
    data = (prepared / "context.json").read_bytes()
    context = json.loads(data)
    old = json.loads(evidence["mass/context.json"])
    assert mass.context_mesh(context) == mass.context_mesh(old)
    # Changing initial velocity and selected time window cannot change M(X,rho).
    cache = json.loads(gzip.decompress(evidence["mass/blocks.json.gz"]))
    cache["context_sha256"] = mass.sha(data)
    payload = gzip.compress(json.dumps(cache, separators=(",", ":")).encode(), mtime=0)
    report = json.loads(evidence["mass/report.json"])
    report.update(case="moving", context_sha256=mass.sha(data), blocks_sha256=mass.sha(payload),
                  deck_sha256=solve.sha(prepared / "moving.inp"),
                  prepared_freeze_sha256=solve.sha(prepared / "freeze.json"),
                  source_sha256={n: mass.sha(b) for n, b in mass.sources().items()})
    assert mass.validate_cache(cache, data) == report["body_mass_tonne"]
    directory = parent / "rebound-identical-mesh-mass"
    directory.mkdir()
    for name, contents in {"context.json": data, "blocks.json.gz": payload,
            "prepared-freeze.json": (prepared / "freeze.json").read_bytes(),
            "moving.inp": (prepared / "moving.inp").read_bytes(),
            **{n + ".snapshot": b for n, b in mass.sources().items()}}.items():
        (directory / name).write_bytes(contents)
    solve.save(directory / "report.json", report)
    return prepared, directory


@pytest.fixture
def moving_run(moving_prepared, tmp_path, monkeypatch):
    prepared, mass = moving_prepared
    with monkeypatch.context() as guard:
        guard.setattr(solve.subprocess, "run", lambda *a, **k: pytest.fail("prepare must not launch"))
        return solve.prepare(prepared, tmp_path / "runs", case="moving", mass_directory=mass,
                             solver_timeout_seconds=1800)


def test_explicit_moving_freezes_full_approved_closure(moving_run, moving_prepared):
    prepared, mass = moving_prepared
    record = solve.verify(moving_run)
    frozen = moving_run / "frozen"
    approval = json.loads((frozen / "moving-preflight.json").read_text())
    assert record["case"] == "moving" and record["solver_timeout_seconds"] == 1800
    assert approval["passed_quiet_archive_sha256"] == solve.QUIET_ARCHIVE_SHA
    assert approval["inputs_sha256"] == {n: h for n, h in record["inputs_sha256"].items() if n != "moving-preflight.json"}
    assert {p.name for p in (frozen / "mass").iterdir()} == solve.MASS_FILES
    assert all((frozen / "mass" / n).read_bytes() == (mass / n).read_bytes() for n in solve.MASS_FILES)
    assert (frozen / "control.inp").read_bytes() == (prepared / "moving.inp").read_bytes()
    assert not (moving_run / "launch.json").exists()
    command = solve.command(moving_run, case="moving", solver_timeout_seconds=1800)
    assert command[3] == "moving-" + moving_run.name
    assert command[command.index("--kill-after=5") + 1] == "1800"


def test_moving_mock_completion_is_not_acceptance_and_is_single_use(moving_run, monkeypatch):
    calls = mock_docker(monkeypatch, moving_run)
    result = solve.launch(moving_run)
    launch = json.loads((moving_run / "launch.json").read_text())
    report = json.loads((result / "exit.json").read_text())
    assert launch["outer_timeout_seconds"] == 1820
    assert report["status"] == "SOLVER COMPLETED; AUDIT PENDING"
    assert report["container_stopped_successfully_before_cleanup"] is True
    assert "refinement pending" in report["limits"]
    with pytest.raises(FileExistsError):
        solve.launch(moving_run)
    assert calls[-1] == ["docker", "rm", "-f", CID] and len(calls) == 3


@pytest.mark.parametrize("failure", ["timeout", "running"])
def test_moving_timeout_or_running_container_retains_failure(moving_run, monkeypatch, failure):
    kwargs = {"error": subprocess.TimeoutExpired("docker", 1820)} if failure == "timeout" else {"running": True}
    calls = mock_docker(monkeypatch, moving_run, **kwargs)
    with pytest.raises((RuntimeError, subprocess.TimeoutExpired)):
        solve.launch(moving_run)
    assert calls[-1] == ["docker", "rm", "-f", CID]
    report = json.loads((moving_run / "result/exit.json").read_text())
    assert report["status"] != "SOLVER COMPLETED; AUDIT PENDING"
    assert report["output_sha256"]["control.dat"] == solve.sha(moving_run / "result/control.dat")


@pytest.mark.parametrize("name", ["mass/blocks.json.gz", "evaluators/moving_hardware_balance.py.snapshot", "moving-preflight.json"])
def test_changed_moving_frozen_evidence_rejects_before_sentinel(moving_run, name):
    path = moving_run / "frozen" / name
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Frozen input changed"):
        solve.launch(moving_run)
    assert not (moving_run / "launch.json").exists()


@pytest.mark.parametrize("case,seconds", [("quiescent", 1800), ("moving", 120), ("moving", 180),
    ("moving", 3600), ("moving", 1800.), ("moving", True), ("refinement", 1800)])
def test_moving_authority_is_explicit_and_coarse_only(tmp_path, case, seconds):
    with pytest.raises(ValueError):
        solve.prepare(tmp_path / "absent", case=case, solver_timeout_seconds=seconds)


def test_moving_missing_selected_cache_rejects(moving_prepared, tmp_path):
    prepared, _ = moving_prepared
    with pytest.raises(ValueError, match="explicit mass_directory"):
        solve.prepare(prepared, tmp_path / "runs", case="moving", solver_timeout_seconds=1800)
    assert not (tmp_path / "runs").exists()


def test_moving_child_guard_needs_only_standard_library(moving_run):
    # -I removes the repository import path: runtime approval must need no FEA/Gmsh imports.
    import sys
    program = ("import json,runpy,pathlib; p=pathlib.Path(__import__('sys').argv[1]); "
               "m=runpy.run_path(str(p/'frozen/moving_hardware_solve.py')); "
               "m['check_frozen'](p/'frozen',json.loads((p/'freeze.json').read_text()))")
    completed = subprocess.run([sys.executable, "-I", "-c", program, str(moving_run)],
                               capture_output=True, text=True, timeout=20, check=False)
    assert completed.returncode == 0, completed.stderr


@pytest.mark.parametrize("fault", ["context", "blocks", "source", "extra"])
def test_moving_wrong_cache_is_rejected(moving_prepared, tmp_path, fault):
    prepared, mass = moving_prepared
    changed = tmp_path / "mass"
    shutil.copytree(mass, changed)
    name = {"context": "context.json", "blocks": "blocks.json.gz", "source": "dynamic_momentum.py.snapshot", "extra": "foreign"}[fault]
    (changed / name).write_bytes(b"changed")
    with pytest.raises(ValueError):
        solve.prepare(prepared, tmp_path / "runs", case="moving", solver_timeout_seconds=1800, mass_directory=changed)
    assert not (tmp_path / "runs").exists()


def test_moving_extra_frozen_file_rejects(moving_run):
    (moving_run / "frozen/unapproved").write_bytes(b"extra")
    with pytest.raises(ValueError, match="inventory"):
        solve.verify(moving_run)


def test_selected_native_mass_must_match_frozen_reference(moving_prepared, tmp_path):
    from fea import hardware_mass_cache as mass

    prepared, original = moving_prepared
    changed = tmp_path / "mass"
    shutil.copytree(original, changed)
    cache = json.loads(gzip.decompress((changed / "blocks.json.gz").read_bytes()))
    for _, block in cache["operators"]["native_four_point"]["WASHER"].values():
        for row in block:
            for i in range(len(row)):
                row[i] *= 2
    payload = gzip.compress(json.dumps(cache).encode(), mtime=0)
    (changed / "blocks.json.gz").write_bytes(payload)
    report = json.loads((changed / "report.json").read_bytes())
    report["blocks_sha256"] = mass.sha(payload)
    report["body_mass_tonne"] = mass.validate_cache(cache, (prepared / "context.json").read_bytes())
    (changed / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="native washer mass differs"):
        solve.prepare(prepared, tmp_path / "runs", case="moving", solver_timeout_seconds=1800, mass_directory=changed)
    assert not (tmp_path / "runs").exists()


def test_failed_freeze_validation_leaves_no_launchable_record(prepared, tmp_path, monkeypatch):
    def reject(*args):
        raise ValueError("final frozen validation failed")
    monkeypatch.setattr(solve, "check_frozen", reject)
    with pytest.raises(ValueError, match="final frozen validation"):
        solve.prepare(prepared, tmp_path / "runs")
    assert list((tmp_path / "runs").iterdir())
    assert not list((tmp_path / "runs").glob("*/freeze.json"))


@pytest.mark.parametrize("fault", ["velocity", "time", "gate", "quiet", "source", "reference"])
def test_moving_host_replay_rejects_changed_contract(moving_prepared, fault):
    prepared, mass = moving_prepared
    context = copy.deepcopy(json.loads((prepared / "context.json").read_text()))
    if fault == "velocity":
        context["cases"]["moving"]["initial_velocity_mm_s"]["BOLT_NUT"][0] = 1
    elif fault == "time":
        context["cases"]["moving"]["total_time_s"] = 4e-5
    elif fault == "gate":
        context["moving_protocol"]["native_ke_rtol"] = 1
    elif fault == "quiet":
        context["passed_quiet_evidence"]["archive_sha256"] = "0" * 64
    elif fault == "source":
        context["source_sha256"]["moving_hardware_balance.py"] = "0" * 64
    else:
        context["diagnostic_reference_scales"]["reference_mass_tonne"] *= 2
    with pytest.raises(ValueError):
        solve.moving_preflight(prepared, context, mass)


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
                     "Name": "/foreign" if wrong_name else "/" + json.loads((directory / "freeze.json").read_text())["case"] + "-" + directory.name,
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
