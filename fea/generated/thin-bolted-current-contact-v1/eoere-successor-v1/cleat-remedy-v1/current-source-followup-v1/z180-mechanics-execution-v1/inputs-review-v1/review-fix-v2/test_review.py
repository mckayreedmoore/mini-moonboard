"""Two exact absolute pins; all ordinary source and inert math controls reused."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("z180_input_review_absolute_fix_fixture", OWN.with_name("review.py"))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def test_two_authentic_absolute_pins_and_ordinary_relative_pin():
    frozen = w.original()
    ordinary = str(frozen.PRIOR_REVIEW.relative_to(frozen.ROOT))
    sources = {**w.INHERITED_ABSOLUTE, ordinary: frozen.PRIOR_SHA}
    before = {path: frozen.sha(Path(path) if Path(path).is_absolute() else frozen.ROOT / path) for path in sources}
    with w.corrected_context(frozen):
        checked = frozen.verify_pins(dict(sources))
        assert checked.items() >= sources.items()
        assert checked[str(w.FROZEN.relative_to(frozen.ROOT))] == w.FROZEN_SHA
        assert checked[str(w.OWN.relative_to(frozen.ROOT))] == w.LOADED_SHA
    assert before == {path: frozen.sha(Path(path) if Path(path).is_absolute() else frozen.ROOT / path) for path in sources}


@pytest.mark.parametrize("kind", ["altered_digest", "altered_path", "third_absolute"])
def test_every_other_absolute_pair_rejects(kind):
    frozen = w.original()
    path, digest = next(iter(w.INHERITED_ABSOLUTE.items()))
    if kind == "altered_digest":
        digest = "0" * 64
    elif kind == "altered_path":
        path = str(Path(path).parent / "." / Path(path).name).replace("/eoere-", "/./eoere-")
    else:
        path, digest = str(frozen.PRIOR_REVIEW), frozen.PRIOR_SHA
    with w.corrected_context(frozen), pytest.raises(ValueError, match="exact inherited absolute"):
        frozen.verify_pins({path: digest})


def test_changed_exact_absolute_source_bytes_reject_without_mutating_source():
    frozen = w.original()
    path, digest = next(iter(w.INHERITED_ABSOLUTE.items()))
    original_sha = frozen.sha
    with w.corrected_context(frozen), patch.object(frozen, "sha", side_effect=lambda value:
            "0" * 64 if str(value) == path else original_sha(value)), pytest.raises(ValueError, match="exact inherited absolute"):
        frozen.verify_pins({path: digest})


def test_relative_alias_and_wrong_relative_digest_stay_rejected():
    frozen = w.original()
    relative = str(frozen.PRIOR_REVIEW.relative_to(frozen.ROOT))
    for path, digest in ((relative, "0" * 64), ("./" + relative, frozen.PRIOR_SHA)):
        with w.corrected_context(frozen), pytest.raises(ValueError):
            frozen.verify_pins({path: digest})


def test_own_identity_conflict_rejects_and_context_restores():
    frozen = w.original()
    prior = frozen.verify_pins
    with pytest.raises(ValueError, match="identity pin conflict"), w.corrected_context(frozen):
        frozen.verify_pins({str(w.OWN.relative_to(frozen.ROOT)): "0" * 64})
    assert frozen.verify_pins is prior and frozen.OWN == w.FROZEN and frozen.LOADED_SHA == w.FROZEN_SHA


def test_default_preflight_retains_false_readiness_and_pins_old_and_self(tmp_path):
    out = tmp_path / "preflight.json"
    frozen = w.original()
    with patch.object(frozen, "load_gate", side_effect=AssertionError("preflight reached dependent imports")):
        assert w.main(["--out", str(out)]) == 0
    result = json.loads(out.read_bytes())
    assert result["review_readiness"] is False and result["reviewed_input"] is None
    assert result["actual_saved_input_review_performed"] is False and result["complete_reference_contact_inventory"] is False
    assert result["source_sha256"].items() >= w.INHERITED_ABSOLUTE.items()
    assert result["source_sha256"].items() >= w.frozen_pins(frozen.ROOT).items()
    assert not any(result["release"].values())


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_output_guard_precedes_any_dependent_gate_import(tmp_path, kind):
    frozen, out = w.original(), tmp_path / "preserved.json"
    out.write_text("preserved") if kind == "file" else out.symlink_to(tmp_path / "missing")
    with patch.object(frozen, "load_gate", side_effect=AssertionError("occupied output reached gate imports")), pytest.raises(FileExistsError):
        w.main(["--mode", "review", "--run", "--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()
