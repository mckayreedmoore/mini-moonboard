"""Preparation checks only; no compiler, Docker, native routine or solver run."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from fea import contact_energy_output_probe as probe


def test_original_source_driver_and_caps_are_frozen_without_execution(tmp_path):
    directory = probe.prepare(tmp_path)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    inventory = manifest["files_sha256"]
    assert set(inventory) == {p.name for p in directory.iterdir()} - {"manifest.json"}
    assert all(probe.digest((directory / n).read_bytes()) == h for n, h in inventory.items())
    original = probe.upstream_inputs(probe.ARCHIVE.read_bytes())
    assert all((directory / n).read_bytes() == original[n] for n in probe.FILES)
    assert manifest["upstream_evidence_archive_sha256"] == probe.ARCHIVE_SHA
    assert (directory / "driver.f90").read_text() == probe.DRIVER
    assert (directory / "stubs.f90").read_text() == probe.stub_source()
    assert "call printoutelem(" in probe.DRIVER and "lakon(nelem)='ESPRNGC6'" in probe.DRIVER
    assert "mortar=1" in probe.DRIVER and "prlab(1)='CELS  '" in probe.DRIVER
    assert [c["expected_CELS"] for c in manifest["cases"]] == [7.5, 0., 2.25]
    assert [(c["compact_slot"], c["writer_slot"]) for c in manifest["cases"]] == [(2, 2), (2, 8), (2, 8)]
    assert manifest["image"] == "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"
    assert (manifest["compiler_timeout_seconds"], manifest["driver_timeout_seconds"],
            manifest["inner_timeout_seconds"], manifest["outer_timeout_seconds"]) == (30, 5, 45, 65)
    assert manifest["memory_bytes"] == 2*1024**3 and manifest["cpus"] == 1
    assert manifest["compile_command"][0] == "gfortran"
    assert manifest["run_command"] == ["/result/energy-reader"]
    assert not any(p.name in ("energy-reader", "probe.dat", "report.json") for p in directory.iterdir())
    assert manifest["status"] == "PREPARED ONLY; NOT BUILT OR EXECUTED"


def test_every_unreachable_link_dependency_fails_fast():
    stubs = probe.stub_source()
    assert stubs.count("error stop 'UNREACHABLE ") == 16
    assert all(f"error stop 'UNREACHABLE {name}'" in stubs for name in probe.STUBS)


def test_wrong_upstream_bytes_cannot_prepare(tmp_path, monkeypatch):
    original = probe.upstream_inputs
    def changed(data):
        result = original(data)
        result["printoutelem.f"] += b"\n"
        return result
    monkeypatch.setattr(probe, "upstream_inputs", changed)
    with pytest.raises(ValueError, match="Original upstream source differs"):
        probe.prepare(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_wrong_archive_rejects_before_preparing(tmp_path, monkeypatch):
    path = tmp_path / "wrong.tar.gz"
    path.write_bytes(b"wrong pinned evidence")
    monkeypatch.setattr(probe, "ARCHIVE", path)
    with pytest.raises(ValueError, match="upstream evidence archive differs"):
        probe.prepare(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_standalone_frozen_module_needs_no_repo_or_external_source(tmp_path):
    directory = probe.prepare(tmp_path)
    script = ("import runpy,pathlib,sys; p=pathlib.Path(sys.argv[1]); "
              "m=runpy.run_path(str(p/'contact_energy_output_probe.py')); "
              "m['verify'](p); assert callable(m['execute'])")
    result = subprocess.run([sys.executable, "-I", "-c", script, str(directory)],
                            cwd=tmp_path, capture_output=True, text=True, timeout=10, check=False)
    assert result.returncode == 0, result.stderr


def test_changed_loaded_driver_cannot_prepare(tmp_path, monkeypatch):
    monkeypatch.setattr(probe, "DRIVER", probe.DRIVER + "\n")
    with pytest.raises(ValueError, match="source/configuration changed"):
        probe.prepare(tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_mid_copy_source_drift_leaves_no_ready_manifest(tmp_path, monkeypatch):
    original_read, original_write = Path.read_bytes, Path.write_bytes
    copied = False
    def write(path, data):
        nonlocal copied
        copied = True
        return original_write(path, data)
    def read(path):
        data = original_read(path)
        return data + b"\n" if copied and path == probe.ARCHIVE else data
    monkeypatch.setattr(Path, "write_bytes", write)
    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError, match="source drift"):
        probe.prepare(tmp_path)
    assert list(tmp_path.iterdir())
    assert not list(tmp_path.glob("*/manifest.json"))


@pytest.mark.parametrize("fault", ["command", "source", "driver"])
def test_resealed_manifest_cannot_select_other_execution(tmp_path, fault):
    directory = probe.prepare(tmp_path)
    manifest = json.loads((directory / "manifest.json").read_bytes())
    if fault == "command":
        manifest["run_command"] = ["ccx", "control"]
    else:
        name = "printoutelem.f" if fault == "source" else "driver.f90"
        (directory / name).write_bytes(b"changed")
        manifest["files_sha256"][name] = probe.digest(b"changed")
    (directory / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        probe.launch(directory)
    assert not (directory / "run").exists()


@pytest.mark.parametrize("failure", [None, "timeout", "running", "cleanup", "missing_cid"])
def test_runner_is_single_use_bounded_and_cleans_only_owned_cid(tmp_path, monkeypatch, failure):
    directory = probe.prepare(tmp_path)
    cid, calls = "a"*64, []
    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd[:2] == ["docker", "run"]:
            assert kwargs["timeout"] == 65
            assert all(x in cmd for x in ("--memory=2g", "--memory-swap=2g", "--cpus=1", "--network=none", "--read-only", probe.IMAGE))
            assert cmd[cmd.index("--kill-after=5")+1] == "45"
            if failure != "missing_cid":
                (directory / "run/container.id").write_text(cid)
            kwargs["stdout"].write(b"retained container output")
            probe.save(directory / "run/worker-exit.json", {"status": "NATIVE READER CASES OBSERVED"})
            if failure == "timeout":
                raise subprocess.TimeoutExpired(cmd, 65)
            return subprocess.CompletedProcess(cmd, 0)
        assert cmd[-1] == cid
        if cmd[1] == "inspect":
            data = [{"Id": cid, "Name": "/"+probe.command(directory)[3], "Config": {"Image": probe.IMAGE},
                     "State": {"Running": failure == "running", "OOMKilled": False, "ExitCode": 0}}]
            return subprocess.CompletedProcess(cmd, 0, json.dumps(data).encode(), b"")
        assert cmd == ["docker", "rm", "-f", cid]
        return subprocess.CompletedProcess(cmd, 1 if failure == "cleanup" else 0, cid.encode(), b"")
    monkeypatch.setattr(probe.subprocess, "run", run)
    if failure:
        with pytest.raises((RuntimeError, FileNotFoundError, subprocess.TimeoutExpired)):
            probe.launch(directory)
    else:
        probe.launch(directory)
    report = json.loads((directory / "run/exit.json").read_bytes())
    assert (report["status"] == "NATIVE READER PROBE COMPLETED") == (failure is None)
    assert report["output_sha256"]["container.log"] == probe.digest(b"retained container output")
    assert len(calls) == (1 if failure == "missing_cid" else 3)
    with pytest.raises(FileExistsError):
        probe.launch(directory)


@pytest.mark.parametrize("failure", [None, "compiler", "driver", "timeout", "sparse_cels", "face", "rowcount", "metadata", "total"])
def test_worker_binds_build_preserves_all_logs_and_never_retries(tmp_path, monkeypatch, failure):
    frozen = probe.prepare(tmp_path)
    result = tmp_path / "result"
    result.mkdir()
    read = Path.read_bytes
    def image_build(path):
        return read(frozen / "build_manifest.json") if path == Path("/opt/ccx-upstream-2.21/build_manifest.json") else read(path)
    monkeypatch.setattr(Path, "read_bytes", image_build)
    calls = []
    def run(cmd, **kwargs):
        calls.append(cmd)
        if cmd == ["gfortran", "--version"]:
            kwargs["stdout"].write(json.loads((frozen / "build_manifest.json").read_bytes())["compiler_versions"]["gfortran"].encode())
            assert kwargs["timeout"] == 5
        elif cmd == probe.COMPILE:
            assert kwargs["timeout"] == 30
            kwargs["stdout"].write(b"compiler retained output")
            (result / "energy-reader").write_bytes(b"test-only executable bytes")
            if failure == "compiler":
                return subprocess.CompletedProcess(cmd, 1)
            if failure == "timeout":
                raise subprocess.TimeoutExpired(cmd, 30)
        else:
            assert cmd == ["/result/energy-reader"] and kwargs["timeout"] == 5
            metadata = "1 2 1 2 7.5 7.5 7.5\n2 2 7 8 7.5 0 0\n3 2 7 8 7.5 2.25 2.25\n"
            dat = "101 2 7.5\n101 2 0\n101 2 2.25\n"
            if failure == "sparse_cels":
                dat = dat.replace("101 2 0\n", "101 2 7.5\n")
            elif failure == "face":
                dat = dat.replace("101 2 0\n", "101 3 0\n")
            elif failure == "rowcount":
                dat = dat.splitlines()[0] + "\n"
            elif failure == "metadata":
                metadata = metadata.replace("2 2 7 8", "2 2 6 8")
            elif failure == "total":
                metadata = metadata.replace("7.5 2.25 2.25", "7.5 2.25 7.5")
            kwargs["stdout"].write(metadata.encode())
            (result / "probe.dat").write_text(dat)
            if failure == "driver":
                return subprocess.CompletedProcess(cmd, 1)
        return subprocess.CompletedProcess(cmd, 0)
    monkeypatch.setattr(probe.subprocess, "run", run)
    if failure:
        with pytest.raises((RuntimeError, ValueError, subprocess.TimeoutExpired)):
            probe.execute(frozen, result)
    else:
        probe.execute(frozen, result)
    report = json.loads((result / "worker-exit.json").read_bytes())
    assert (report["status"] == "NATIVE READER CASES OBSERVED") == (failure is None)
    assert len(calls) == (2 if failure in ("compiler", "timeout") else 3)
    assert all(probe.digest((result / n).read_bytes()) == h for n, h in report["output_sha256"].items())
    if failure in ("sparse_cels", "face", "rowcount", "metadata", "total"):
        assert all(c["returncode"] == 0 for c in report["commands"])
        assert report["exception"]["type"] == "ValueError"
        assert "probe.dat" in report["output_sha256"] and "driver.log" in report["output_sha256"]
