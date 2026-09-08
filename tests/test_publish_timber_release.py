"""Early publication guards do not run CAD or a solver."""
import json
import math
from copy import deepcopy

import pytest

from fea import publish_timber_release as publisher


def replay_fixture():
    return {"basis": [{"residual_wrench": [0.]*6}], "comparison": {
        name: {"matrix_mm_per_n": [[.001, 0., 0.], [0., .002, 0.], [0., 0., .003]],
               "symmetric_eigenvalues_mm_per_n": [.001, .002, .003]}
        for name in ("bonded_compliance", "released_compliance")}}


def test_only_tiny_compliance_eigensolver_roundoff_is_accepted():
    replay = replay_fixture()
    saved = deepcopy(replay)
    saved["comparison"]["released_compliance"]["symmetric_eigenvalues_mm_per_n"][0] = math.nextafter(.001, math.inf)
    publisher.validate_replay(replay, saved)
    assert replay == replay_fixture(), "Validation must not mutate replay evidence"


@pytest.mark.parametrize("mutation", ["spectrum", "nan", "matrix", "reaction"])
def test_material_spectrum_changes_and_any_other_replay_change_reject(mutation):
    replay = replay_fixture()
    saved = deepcopy(replay)
    if mutation in ("spectrum", "nan"):
        saved["comparison"]["released_compliance"]["symmetric_eigenvalues_mm_per_n"][0] = .00101 if mutation == "spectrum" else math.nan
    elif mutation == "matrix":
        saved["comparison"]["released_compliance"]["matrix_mm_per_n"][0][0] = math.nextafter(.001, math.inf)
    else:
        saved["basis"][0]["residual_wrench"][0] = 1e-20
    with pytest.raises(ValueError, match="replay differs"):
        publisher.validate_replay(replay, saved)


def test_existing_publication_is_untouched(tmp_path, monkeypatch):
    output = tmp_path/"published"
    output.mkdir()
    (output/"prior").write_text("keep")
    monkeypatch.setattr(publisher, "OUTPUT", output)
    with pytest.raises(FileExistsError, match="overwrite"):
        publisher.publish()
    assert (output/"prior").read_text() == "keep"


@pytest.mark.parametrize("wrong", ["candidate", "scope"])
def test_foreign_candidate_or_scope_rejected(tmp_path, monkeypatch, wrong):
    generated, output = tmp_path/"generated", tmp_path/"published"
    generated.mkdir()
    monkeypatch.setattr(publisher.run, "DIRECTORY", generated)
    monkeypatch.setattr(publisher, "OUTPUT", output)
    info = {"candidate": "timber-base-development", "limits": publisher.run.LIMITS}
    if wrong == "candidate":
        info["candidate"] = "wide-principal-development"
    else:
        info["limits"] = "qualified"
    for name in publisher.NAMES:
        (generated/name).write_text(json.dumps(info if name != "K12.launch.json" else {}))
    with pytest.raises(ValueError, match="candidate or scope"):
        publisher.publish()
    assert not output.exists()
