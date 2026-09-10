"""Lifecycle checks do not claim a mocked solver is a physical result."""
import json
import subprocess
import tarfile

import pytest

from fea import run_spread_floor_contact as runner


def test_invalid_runtime_and_existing_evidence_rejected(tmp_path):
    for value in (0, float("nan"), 3601):
        with pytest.raises(ValueError):
            runner.run(tmp_path/"trial.tar.gz", value)
    path = tmp_path/"existing.tar.gz"
    path.touch()
    with pytest.raises(FileExistsError):
        runner.run(path)


@pytest.mark.parametrize("exit_code,text", [(0, "Job finished"), (124, "bounded timeout"), (1, "*ERROR")])
def test_terminal_evidence_never_becomes_acceptance(tmp_path, monkeypatch, exit_code, text):
    def prepare(directory, **settings):
        assert settings == {"archive": runner.preparation.COMPACT_ARCHIVE,
                            "initial_increment": .25, "max_increment": .5}
        directory.mkdir()
        (directory/"input.json").write_text(json.dumps({"source_sha256": {}}))
        (directory/"contact.inp").write_text("mock test deck\n")
    monkeypatch.setattr(runner.preparation, "write", prepare)
    monkeypatch.setattr(runner.tempfile, "mkdtemp", lambda **kwargs: str(tmp_path))
    def native(command, **kwargs):
        assert "--network=none" in command and runner.IMAGE in command
        assert command[-7:] == ["timeout", "--signal=TERM", "--kill-after=10s", "5s", "ccx", "-i", "contact"]
        kwargs["stdout"].write(text)
        return subprocess.CompletedProcess(command, exit_code)
    monkeypatch.setattr(runner.subprocess, "run", native)
    output = tmp_path/"result.tar.gz"
    report = runner.run(output, 5, archive=runner.preparation.COMPACT_ARCHIVE,
                        initial_increment=.25, max_increment=.5)
    assert not report["qualified_for_design"]
    assert not report["local_contact_audited"] and not report["global_equilibrium_audited"]
    assert report["solver_terminated_normally"] == (exit_code == 0)
    with tarfile.open(output) as archive:
        saved = json.load(archive.extractfile("run.json"))
        assert saved == report
        assert archive.extractfile("contact.log").read().decode() == text


def test_preserved_compact_timeout_authenticates_without_acceptance():
    import hashlib

    from fea.floor_contact_results import blocks

    path = "fea/results/spread-floor-contact/compact-mu02-k1000-ramp05.tar.gz"
    with tarfile.open(path) as archive:
        files = {m.name: archive.extractfile(m).read() for m in archive if m.isfile()}
    report = json.loads(files["run.json"])
    for name, sha in report["artifact_sha256"].items():
        assert hashlib.sha256(files[name]).hexdigest() == sha
    for name, sha in report["source_sha256"].items():
        assert hashlib.sha256(files["launch_sources/"+name]).hexdigest() == sha
    assert report["exit_code"] == 124 and report["max_seconds"] == 1800
    assert not report["solver_terminated_normally"]
    assert not report["qualified_for_design"]
    assert not report["global_equilibrium_audited"] and not report["local_contact_audited"]
    record = json.loads(files["input.json"])
    assert record["parent_report"]["extension_mm"] == 0
    assert hashlib.sha256(files["contact.inp"]).hexdigest() == record["deck_sha256"]
    parsed = blocks(files["contact.dat"].decode())
    assert ("displacements", "WOODN", 1.) in parsed
    assert ("displacements", "WOODN", 2.) not in parsed
