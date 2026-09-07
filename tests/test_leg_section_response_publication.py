"""Portable retained-native replay only; never run CalculiX or Docker."""
import json

import pytest

from fea.publish_moving_fixture import checked_members
from fea.results.leg_section_response import publish

ARCHIVE_SHA = "a3ed8496a9a3e13303f69f931c184172d100c31bbfffb86a63d4cb8c7091d31a"


@pytest.fixture(scope="module")
def evidence():
    path = publish.HERE/"manifest.json"
    manifest = json.loads(path.read_bytes())
    assert manifest["archive_sha256"] == ARCHIVE_SHA
    assert manifest["archive"] == "evidence.tar.gz"
    archive = publish.HERE/manifest["archive"]
    assert archive.stat().st_size == manifest["archive_bytes"]
    files = checked_members(archive, manifest["archive_sha256"])
    assert len(files) == manifest["member_count"]
    # Historical publisher predates the live reader's host-UID portability fix.
    assert publish.runner.sha(files["publisher.py.snapshot"]) == "05ec14f81b0844bc4e608a47ea97fd4f691cdc05113c8a04f3bd53c3224dfe73"
    assert manifest["geometry_archive_sha256"] == publish.runner.GEOMETRY_SHA
    assert manifest["qualified_for_design"] is False
    return files, manifest


def test_retained_native_signed_replay_and_owned_cleanup(evidence, monkeypatch):
    files, manifest = evidence
    # CI/another workstation need not share the native run's UID or GID.
    monkeypatch.setattr(publish.runner.os, "getuid", lambda: 98765)
    monkeypatch.setattr(publish.runner.os, "getgid", lambda: 98766)
    result = publish.replay(files)
    assert result["pass"] == manifest["comparison_pass"]
    assert result["pass"] is False
    assert result["qualified_for_design"] is False
    assert sum(not row["pass"] for row in result["checks"]) == 12
    assert all(row["pass"] for row in result["fixture_compliance"])
    for size in (40, 25):
        audit = json.loads(files[f"mesh{size}-audit.json"])
        assert sum(not row["pass"] for row in audit["rows"]) == 6
        assert all(row["fixture"]["pass"] for row in audit["rows"])


@pytest.mark.parametrize("name", ["mesh40/section.inp", "sources/leg_section_response.py", "protocol.md"])
def test_mutated_runtime_identity_rejected(evidence, name):
    files = dict(evidence[0])
    files[name] += b"\nmutation\n"
    with pytest.raises(ValueError):
        publish.replay(files)


def test_uncertain_cleanup_rejected(evidence):
    files = dict(evidence[0])
    outcome = json.loads(files["mesh40-terminal.json"])
    outcome["cleanup_exit"] = 1
    files["mesh40-terminal.json"] = json.dumps(outcome).encode()
    with pytest.raises(ValueError, match="cleanup"):
        publish.replay(files)


def test_capture_rejects_symlink(tmp_path):
    (tmp_path/"file").write_text("evidence")
    (tmp_path/"link").symlink_to(tmp_path/"file")
    with pytest.raises(ValueError, match="symlink"):
        publish.capture(tmp_path)
