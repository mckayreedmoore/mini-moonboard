"""The review bundle retains original evidence and replays the selected case."""

import json
import zipfile

import pytest

from scripts.bolted_center_evidence_bundle import build, verify
from tests.test_bolted_center_candidate_extract import _fixture


def test_bundle_replays_without_raw_cycles(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    report_path = _fixture(source)
    archive = tmp_path / "evidence.zip"
    build(report_path.parent, archive)
    result = verify(archive)
    assert result["classification"] == "provisional_native_AB205_diagnostic"
    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
        assert "original-report.json" in names
        assert "report.json" in names
        assert "actions.json" in names
        assert "cycle-00/input.json" in names
        assert not any(name.endswith(".frd") for name in names)
        assert json.loads(bundle.read("original-report.json")) == json.loads(
            report_path.read_bytes()
        )
        assert json.loads(bundle.read("actions.json")) == result


def test_bundle_rejects_tampered_member(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    archive = tmp_path / "evidence.zip"
    build(_fixture(source).parent, archive)
    with zipfile.ZipFile(archive) as bundle:
        members = {name: bundle.read(name) for name in bundle.namelist()}
    members["actions.json"] = b"{}"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
    with pytest.raises(ValueError, match="digest"):
        verify(archive)
