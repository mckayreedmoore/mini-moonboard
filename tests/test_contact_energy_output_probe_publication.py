"""Replay retained native-reader bytes only; never compile or execute a probe."""
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from fea.publish_moving_fixture import checked_members

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "fea/results/contact_energy_output_probe/native-reader.tar.gz"
ARCHIVE_SHA = "f226dda9d3370b449b98c66166cbf7a7c45b2597b1385856dde3e96a7db87cad"
UPSTREAM_SHA = "62eb6870736d979993b5e8c0096f8426a90f8db41e5a621fc2398e806460ce79"
BUILD_SHA = "04b8da67a5edf12c763e03c9a4c3da241375c8d7a37c07eec06e2b31a4622988"
IMAGE = "sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


@pytest.fixture(scope="module")
def files():
    return checked_members(ARCHIVE, ARCHIVE_SHA)


def test_complete_frozen_inputs_match_original_native_source(files):
    assert len(files) == 29
    refs = json.loads(files["references.json"])
    assert refs["source_directory"] == "fea/generated/contact-energy-output-probes/energy-reader-zwetxm3x"
    assert refs["upstream_evidence_archive_sha256"] == UPSTREAM_SHA
    upstream = (ROOT / refs["upstream_evidence_archive"]).read_bytes()
    assert sha(upstream) == UPSTREAM_SHA
    manifest = json.loads(files["probe/manifest.json"])
    assert manifest["status"] == "PREPARED ONLY; NOT BUILT OR EXECUTED"
    assert manifest["upstream_evidence_archive_sha256"] == UPSTREAM_SHA
    assert manifest["source_build_manifest_sha256"] == BUILD_SHA
    assert manifest["image"] == IMAGE
    assert sha(files["probe/build_manifest.json"]) == BUILD_SHA
    prepared = {n.removeprefix("probe/") for n in files if n.startswith("probe/") and not n.startswith("probe/run/")}
    assert prepared == set(manifest["files_sha256"]) | {"manifest.json"}
    assert all(sha(files["probe/"+n]) == h for n, h in manifest["files_sha256"].items())
    build = json.loads(files["probe/build_manifest.json"])
    with tarfile.open(fileobj=io.BytesIO(upstream), mode="r:gz") as archive:
        assert files["probe/build_manifest.json"] == archive.extractfile("frozen/build_manifest.json").read()
        for name in ("printoutelem.f", "gauss.f", "nonlingeo.c", "gencontelem_f2f.f", "resultsmech.f", "results.c", "resultsprint.f", "printout.f"):
            assert files["probe/"+name] == archive.extractfile("frozen/native-source/"+name).read()
            assert sha(files["probe/"+name]) == build["upstream_files_sha256"]["./CalculiX/ccx_2.21/src/"+name]
    assert b"GNU GENERAL PUBLIC LICENSE" in files["probe/COPYING"]
    driver = files["probe/driver.f90"].decode()
    assert "call printoutelem(" in driver and "lakon(nelem)='ESPRNGC6'" in driver
    assert "mortar=1" in driver and "prlab(1)='CELS  '" in driver
    assert files["probe/stubs.f90"].count(b"error stop 'UNREACHABLE ") == 16


def test_actual_three_native_rows_and_slot_metadata(files):
    manifest = json.loads(files["probe/manifest.json"])
    assert [c["expected_CELS"] for c in manifest["cases"]] == [7.5, 0., 2.25]
    rows = [tuple(map(float, row.split())) for row in files["probe/run/probe.dat"].decode().splitlines()]
    assert rows == [(101., 2., 7.5), (101., 2., 0.), (101., 2., 2.25)]
    metadata = [tuple(map(float, row.split())) for row in files["probe/run/driver.log"].decode().splitlines()]
    assert metadata == [(1, 2, 1, 2, 7.5, 7.5, 7.5), (2, 2, 7, 8, 7.5, 0, 0), (3, 2, 7, 8, 7.5, 2.25, 2.25)]
    worker = json.loads(files["probe/run/worker-exit.json"])
    assert worker["status"] == "NATIVE READER CASES OBSERVED" and worker["exception"] is None
    assert "not calculated spring energies" in worker["limits"]
    assert {n for n in worker["output_sha256"]} == {"compiler-version.log", "compiler.log", "driver.log", "probe.dat", "energy-reader"}
    assert all(sha(files["probe/run/"+n]) == h for n, h in worker["output_sha256"].items())
    assert worker["commands"] == [
        {"label": "compiler-version", "command": ["gfortran", "--version"], "timeout_seconds": 5, "returncode": 0},
        {"label": "compiler", "command": manifest["compile_command"], "timeout_seconds": 30, "returncode": 0},
        {"label": "driver", "command": ["/result/energy-reader"], "timeout_seconds": 5, "returncode": 0}]
    assert manifest["compile_command"] == ["gfortran", "-O0", "-g", "-fcheck=all", "-fallow-argument-mismatch",
        "-I/frozen", "/frozen/printoutelem.f", "/frozen/driver.f90", "/frozen/stubs.f90", "-o", "/result/energy-reader"]
    assert files["probe/run/compiler-version.log"].decode() == json.loads(files["probe/build_manifest.json"])["compiler_versions"]["gfortran"]
    assert files["probe/run/energy-reader"].startswith(b"\x7fELF")


def test_terminal_owned_cleanup_caps_and_complete_output_inventory(files):
    manifest = json.loads(files["probe/manifest.json"])
    launch = json.loads(files["probe/run/launch.json"])
    outcome = json.loads(files["probe/run/exit.json"])
    assert launch["manifest_sha256"] == sha(files["probe/manifest.json"])
    assert launch["outer_timeout_seconds"] == manifest["outer_timeout_seconds"] == 65
    assert manifest["inner_timeout_seconds"] == 45
    assert manifest["memory_bytes"] == 2*1024**3 and manifest["cpus"] == 1
    cmd = launch["command"]
    directory = Path(cmd[5]).parent.parent
    assert str(directory).endswith("/fea/generated/contact-energy-output-probes/energy-reader-zwetxm3x")
    assert cmd == ["docker", "run", "--name", "energy-reader-"+directory.name, "--cidfile", str(directory/"run/container.id"),
        "--network=none", "--read-only", "--memory=2g", "--memory-swap=2g", "--cpus=1", "--pids-limit=128",
        "--tmpfs", "/tmp:size=128m", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{directory}:/frozen:ro",
        "-v", f"{directory/'run'}:/result", "-w", "/result", IMAGE, "timeout", "--signal=TERM", "--kill-after=5",
        "45", "python3", "/frozen/contact_energy_output_probe.py", "--execute"]
    native = {n.removeprefix("probe/run/") for n in files if n.startswith("probe/run/")}
    assert native == set(outcome["output_sha256"]) | {"exit.json"}
    assert all(sha(files["probe/run/"+n]) == h for n, h in outcome["output_sha256"].items())
    assert outcome["status"] == "NATIVE READER PROBE COMPLETED" and outcome["returncode"] == 0
    assert outcome["stopped_successfully"] is True and outcome["cleanup_success"] is True and outcome["exceptions"] == []
    cid = outcome["owned_container_id"]
    assert cid == "40ec30bc32ff5f392dc9f8600971040b1898f7ab5a2fb34221ce0728f3543a6e"
    assert files["probe/run/container.id"].decode() == cid
    probe = json.loads(files["probe/run/container-inspect.json"])
    inspected = json.loads(probe["stdout"])
    assert probe["returncode"] == 0 and len(inspected) == 1
    item = inspected[0]
    assert item["Id"] == cid and item["Name"] == "/"+cmd[3] and item["Config"]["Image"] == IMAGE
    assert item["State"]["Running"] is False and item["State"]["ExitCode"] == 0 and item["State"]["OOMKilled"] is False
    cleanup = json.loads(files["probe/run/cleanup.json"])
    assert cleanup["returncode"] == 0 and cleanup["container_id"] == cid and cleanup["stdout"].strip() == cid
