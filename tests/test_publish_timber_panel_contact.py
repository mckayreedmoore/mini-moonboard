"""Publication boundaries without a solver or full mesh reconstruction."""
import json

import pytest

from fea import publish_timber_panel_contact as publish


def test_existing_publication_refuses_before_read(monkeypatch, tmp_path):
    monkeypatch.setattr(publish, "OUTPUT", tmp_path)
    monkeypatch.setattr(publish.run, "DIRECTORY", tmp_path/"missing")
    with pytest.raises(FileExistsError):
        publish.main()


@pytest.fixture
def prepared(monkeypatch):
    info = {"candidate": "timber-base-development", "limits": publish.run.LIMITS,
            "source_sha256": {"source": "hash"}, "penalty": 10000., "increment": .125,
            "deck_sha256": publish.sha(b"deck"), "leg_references_world_mm": {"left": [1., 2., 3.]}}
    raw = {n: b"" for n in publish.FILES}
    raw["input.json"] = json.dumps(info).encode()
    raw["contact.inp"] = b"deck"
    raw["launch.json"] = json.dumps({"input_sha256": publish.sha(raw["input.json"]),
        "deck_sha256": info["deck_sha256"], "source_sha256": info["source_sha256"],
        "timeout_seconds": publish.run.TIMEOUT}).encode()
    raw["execution.json"] = json.dumps({"status": "solver completed; contact audit pending",
        "limits": publish.run.LIMITS, "artifacts": {n: publish.sha(v) for n, v in raw.items()
                                                    if n != "execution.json"}}).encode()
    def prepare(penalty, increment, path):
        assert (penalty, increment) == (10000., .125)
        path.mkdir()
        (path/"input.json").write_text(json.dumps(info))
        (path/"contact.inp").write_bytes(b"deck")
    monkeypatch.setattr(publish.run, "prepare", prepare)
    monkeypatch.setattr(publish.run.common, "unchanged", lambda sources: None)
    monkeypatch.setattr(publish, "audit_with_history", lambda *args: [{"time": 1.}])
    return raw


def test_validated_input_reconstruction_reaches_audit(prepared):
    assert publish.validate(prepared)["endpoints"] == [{"time": 1.}]


@pytest.mark.parametrize("defect", ["candidate", "reference", "deck", "launch", "execution", "missing"])
def test_changed_source_derived_metadata_or_artifacts_reject(prepared, defect):
    raw = dict(prepared)
    if defect in ("candidate", "reference"):
        info = json.loads(raw["input.json"])
        if defect == "candidate":
            info["candidate"] = "wide-principal-development"
        else:
            info["leg_references_world_mm"]["left"][0] = 999.
        raw["input.json"] = json.dumps(info).encode()
    elif defect == "deck":
        raw["contact.inp"] += b" changed"
    elif defect == "launch":
        raw["launch.json"] = b"{}"
    elif defect == "execution":
        execution = json.loads(raw["execution.json"])
        execution["artifacts"]["contact.dat"] = "wrong"
        raw["execution.json"] = json.dumps(execution).encode()
    else:
        del raw["contact.sta"]
    with pytest.raises(ValueError):
        publish.validate(raw)


def test_unacceptable_contact_is_not_published(prepared, monkeypatch):
    def fail(*args):
        raise ValueError("Unacceptable contact")
    monkeypatch.setattr(publish, "audit_with_history", fail)
    with pytest.raises(ValueError, match="Unacceptable"):
        publish.validate(prepared)
