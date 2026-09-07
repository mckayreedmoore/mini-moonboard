"""Retained geometry arithmetic only; no Gmsh, integration or native solve."""
import hashlib
import json
import math
import shlex
from pathlib import Path

import pytest

from fea.leg_section_geometry import GATES, assess
from fea.publish_moving_fixture import checked_members

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / "fea/results/leg_section_geometry"
REFERENCE_SHA = "476283677930a59e8c0ed202f3455fa72b67880dbfcba3a8062dcb35522dfc5a"
IMAGE = "sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646"
ARCHIVE_SHA = "534c1c9ade2c06aface3a1a53f8014bba7ef4eff95ca88061ea8fb17f1407563"


@pytest.fixture(scope="module")
def evidence():
    manifest = json.loads((HERE/"manifest.json").read_bytes())
    assert manifest["archive_sha256"] == ARCHIVE_SHA
    archive = HERE/manifest["archive"]
    assert archive.stat().st_size == manifest["archive_bytes"]
    files = checked_members(archive, manifest["archive_sha256"])
    assert len(files) == manifest["member_count"]
    refs = json.loads(files["references.json"])
    assert refs["reference_sha256"] == manifest["reference_sha256"] == REFERENCE_SHA
    with (ROOT/refs["reference_archive"]).open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == REFERENCE_SHA
    assert files["publisher.py.snapshot"] == (HERE/"publish.py").read_bytes()
    return files


def test_both_terminal_attempts_caps_sources_and_owned_cleanup(evidence):
    files = evidence
    frozen = None
    for label, code, name in (("failed-import", 1, "leg-section-geometry-rMNuN4"),
                              ("completed", 0, "leg-section-geometry-2N0ZGp")):
        outcome = json.loads(files[label+"/exit.json"])
        inspected = json.loads(files[label+"/container-inspect.json"])
        metadata = json.loads(files[label+"/command.json"])
        command = shlex.split(metadata["command"])
        assert metadata["inner_timeout_seconds"] == 120 and metadata["outer_timeout_seconds"] == 140
        assert command[:6] == ["timeout", "--signal=TERM", "--kill-after=5", "140", "docker", "run"]
        assert command[-9:] == ["timeout", "--signal=TERM", "--kill-after=5", "120", "python3", "-m", "fea.leg_section_geometry", "--output", "/output"]
        assert outcome["state"] == inspected["State"]
        assert outcome["state"]["ExitCode"] == code and outcome["state"]["Running"] is False
        assert outcome["state"]["OOMKilled"] is False
        cid = outcome["container"]
        assert files[label+"/container.id"].decode().strip() == inspected["Id"] == cid
        assert inspected["Name"] == "/moonboard-"+name and inspected["Image"] == IMAGE
        assert outcome["cleanup"]["exit_code"] == 0 and outcome["cleanup"]["output"].strip() == cid
        config = inspected["HostConfig"]
        assert config["Memory"] == config["MemorySwap"] == 2*1024**3
        assert config["NanoCpus"] == 1000000000 and config["PidsLimit"] == 256
        assert config["NetworkMode"] == "none" and config["ReadonlyRootfs"] is True
        assert inspected["Config"]["User"] == "1000:1000"
        assert {"OMP_NUM_THREADS=2", "OPENBLAS_NUM_THREADS=2", "PYTHONDONTWRITEBYTECODE=1"} <= set(inspected["Config"]["Env"])
        mounts = {m["Destination"]: m for m in inspected["Mounts"]}
        assert mounts["/work"]["RW"] is False
        assert mounts["/work/fea/results/independent_leg_response"]["RW"] is False
        assert mounts["/output"]["RW"] is True
        current = {n.removeprefix(label+"/frozen/"): b for n, b in files.items() if n.startswith(label+"/frozen/")}
        assert len(current) == 10
        assert set(current) == {"fea/"+n+".py" for n in ("leg_section_geometry", "leg_section_preflight",
            "independent_leg_response", "independent_ply_control", "floor_contact", "floor_contact_results",
            "section_force_coupon", "section_force_tet_coupon")} | {"tests/test_leg_section_geometry.py", "tests/test_leg_section_preflight.py"}
        if frozen is not None:
            assert current == frozen
            assert mounts["/deps/numpy"]["RW"] is mounts["/deps/numpy.libs"]["RW"] is False
            assert "PYTHONPATH=/deps" in inspected["Config"]["Env"]
            assert metadata["environment"] == {"python": "3.12.3", "numpy": "2.5.2 read-only mounted existing locked environment", "gmsh": "4.12.1"}
            assert b'version = "2.5.2"' in files["completed/uv.lock.snapshot"]
        frozen = current
    assert files["failed-import/process.log"].decode().rstrip().endswith("ModuleNotFoundError: No module named 'numpy'")
    assert not any(n.startswith("failed-import/output/") for n in files)
    assert "completed/process.log" not in files


def test_reported_integrals_recompute_frozen_geometric_gates(evidence):
    report = json.loads(evidence["completed/output/report.json"])
    assert report["gates"] == GATES
    assert report["archive_sha256"] == REFERENCE_SHA
    assert report["gmsh_version"] == "4.12.1" and report["qualified_for_design"] is False
    assert "not an everywhere-positive or injective mapping proof" in report["limits"]
    assert report["status"] == "GEOMETRIC COMPARISONS WITHIN GATES"
    for size, counts in (("40", (1496, 1176, 22)), ("25", (3665, 2712, 26))):
        row = report["meshes"][size]
        assert row == json.loads(evidence[f"completed/output/mesh{size}.json"])
        assert tuple(row[k] for k in ("selected_elements", "boundary_faces", "cut_faces")) == counts
        cut, reverse = row["cut_surface"], row["reverse_cut_surface"]
        opposed = math.hypot(*(a+b for a, b in zip(cut["area_vector"], reverse["area_vector"], strict=True)))/cut["area"]
        actual = assess(row["surface"]["8"], row["surface"]["12"], row["volume_integral_mm3"],
                        row["volume_first_moment_local_mm4"], row["characteristic_length_mm"], opposed)
        assert {k: row[k] for k in actual} == actual
        assert actual["geometric_comparisons_within_gates"] and actual["failures"] == {}
        for surface in [*row["surface"].values(), cut, reverse]:
            assert surface["minimum_sampled_surface_jacobian"] > 0
            assert 0 < surface["minimum_sampled_orientation_cosine"] <= 1
        assert reverse["area"] == pytest.approx(cut["area"], rel=1e-12)
        assert reverse["volume"] == pytest.approx(-cut["volume"], rel=1e-12)
        assert reverse["first_moment"] == pytest.approx([-v for v in cut["first_moment"]], rel=1e-11)
