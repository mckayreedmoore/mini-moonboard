import json

import pytest

from fea.results.moving_hardware_control import publisher


@pytest.fixture(scope="module")
def evidence():
    report = json.loads((publisher.HERE / "first-input-rejection.json").read_text())
    archive = publisher.HERE / report["archive"]
    assert publisher.sha(archive.read_bytes()) == report["archive_sha256"]
    return publisher.archive_files(archive), report


def test_preserved_first_rejection_replays_without_solver(evidence):
    files, report = evidence
    assert publisher.replay(files) == report["summary"]
    assert report["summary"]["accepted_states"] == 0
    assert report["summary"]["solver_exit_code"] == 201
    assert report["summary"]["mesh_nodes"] == 131695
    assert report["summary"]["control_nodes"] == 19769


@pytest.mark.parametrize("name,data", [
    ("solve/result/control.dat", b"invented output"),
    ("geometry/leg_right_inner.step", b"changed geometry"),
    ("prepared/frozen/moving_hardware_control.py", b"changed source"),
])
def test_changed_evidence_is_not_accepted(evidence, name, data):
    original, _ = evidence
    files = {**original, name: data}
    # Even a rewritten outer manifest must not bypass the original linked hashes.
    members = json.loads(files["members.json"])
    members[name] = publisher.sha(data)
    files["members.json"] = json.dumps(members).encode()
    with pytest.raises(ValueError, match="hash differs"):
        publisher.replay(files)


@pytest.fixture(scope="module")
def second_evidence():
    report = json.loads((publisher.HERE / "second-quiescent-timeout.json").read_text())
    archive = publisher.HERE / report["archive"]
    assert publisher.sha(archive.read_bytes()) == report["archive_sha256"]
    return publisher.archive_files(archive), report


def test_second_timeout_replays_with_original_shared_archive(second_evidence):
    files, report = second_evidence
    first = publisher.HERE / report["shared_archive"]
    assert publisher.replay_second(files, first) == report["summary"]
    assert report["summary"]["accepted_states"] == 1
    assert report["summary"]["solver_exit_code"] == 124
    refs = json.loads(files["references.json"])
    assert "mesh/mesh.inp" in refs["members_sha256"]
    assert not any(n.startswith("geometry/") for n in files)


@pytest.mark.parametrize("name", ["solve/result/control.sta", "solve/frozen/context.json", "references.json"])
def test_second_timeout_rejects_rewritten_evidence(second_evidence, name):
    original, report = second_evidence
    files = dict(original)
    if name == "references.json":
        refs = json.loads(files[name])
        refs["archive_sha256"] = "0"*64
        files[name] = json.dumps(refs).encode()
    else:
        files[name] += b"changed"
    members = json.loads(files["members.json"])
    members[name] = publisher.sha(files[name])
    files["members.json"] = json.dumps(members).encode()
    with pytest.raises(ValueError):
        publisher.replay_second(files, publisher.HERE / report["shared_archive"])


@pytest.fixture(scope="module")
def third_evidence():
    report = json.loads((publisher.HERE / "third-catalog-quiescent.json").read_text())
    archive = publisher.HERE / report["archive"]
    assert publisher.sha(archive.read_bytes()) == report["archive_sha256"]
    return publisher.archive_files(archive), report


def test_catalog_timeout_is_self_contained_partial_evidence(third_evidence):
    files, report = third_evidence
    assert publisher.replay(files, catalog=True) == report["summary"]
    assert report["summary"]["solver_exit_code"] == 124
    assert report["summary"]["accepted_states"] == 19
    assert "references.json" not in files
    assert len([name for name in files if name.startswith("geometry/") and name.endswith(".step")]) == 11
    assert "geometry/mesh-runtime.txt" in files
    assert json.loads(files["prepared/context.json"])["washer_bore_diameter_mm"] == 10.9982
    with pytest.raises(ValueError, match="Original failure differs"):
        publisher.replay(files)  # Cannot relabel this as the original input rejection.


@pytest.mark.parametrize("name", ["geometry/leg_stitch_right_1_washer_inner.step", "mesh/mesh.inp",
                                  "solve/result/control.sta", "solve/frozen/moving_hardware_solve.py"])
def test_catalog_archive_rejects_changed_linked_evidence(third_evidence, name):
    original, _ = third_evidence
    files = {**original, name: original[name] + b"changed"}
    members = json.loads(files["members.json"])
    members[name] = publisher.sha(files[name])
    files["members.json"] = json.dumps(members).encode()
    with pytest.raises(ValueError):
        publisher.replay(files, catalog=True)
