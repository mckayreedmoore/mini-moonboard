"""Method-bound preflight controls, with all current operators prohibited."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_method_bound_preflight_fixture", OWN.with_name("preflight.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
READINESS = s.BASE.parent / "current-readiness-v1"
PROBE = s.BASE.parent / "current-force-bridge-review-v3/testing/_probes/attempt-vi76g4cj/method-mismatch.json"


def actual_argv(out):
    command = json.loads((READINESS / "process.json").read_bytes())["command"]
    argv = command[command.index("--mode"):]
    argv[argv.index("--out") + 1] = str(out)
    return argv


def prohibited(*_args, **_kwargs):
    raise AssertionError("source-only preflight reached preparation or a panel/frame operator")


def test_genuine_exact_six_refs_pass_without_current_operators(tmp_path):
    w, out = s.previous().corrected(), tmp_path / "all-bindings.json"
    b = w.frozen()
    original_load = b.load
    def load(path, sha, name):
        module = original_load(path, sha, name)
        if Path(path).resolve() == (s.ROOT / b.PANEL_BANK["path"]).resolve():
            module.load_panel_dependencies = prohibited
            module.prepare_panel_operators = prohibited
        return module
    with patch.object(b, "load", side_effect=load), patch.object(b.factory, "prepare", side_effect=prohibited), \
            patch.object(b.frame, "ElasticAssembly", side_effect=prohibited), patch.object(b, "run_case", side_effect=prohibited):
        assert s.main(actual_argv(out)) == 0
    result = json.loads(out.read_bytes())
    bindings = result["method_reference_bindings"]
    assert result["missing"] == [] and bindings["complete"] is True and bindings["unchecked"] == []
    assert set(bindings["checked"]) == set(s.REFERENCE_KEYS)
    assert bindings["checked"] == {key: result["provided"][key] for key in s.REFERENCE_KEYS}
    assert bindings["method"] == result["provided"]["method_input"]
    method_path = s.ROOT / bindings["method"]["path"]
    assert hashlib.sha256(method_path.read_bytes()).hexdigest() == "941ca92e8230de9d480d17f6e2a082d05a3fae267329ef0b33c81d06d0ad46f5"
    assert len(json.loads(method_path.read_bytes())["source_sha256"]) == 1102
    assert result["production_readiness_claimed"] is False
    assert result["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
    assert not any(result["release"].values())


@pytest.mark.parametrize("changed", [("inputs", "input_review"), ("input_review",)])
def test_preserved_valid_pair_with_different_method_refs_rejected_before_v3(tmp_path, changed):
    previous, out = s.previous(), tmp_path / "mismatched-method.json"
    provided = json.loads(PROBE.read_bytes())["provided"]
    if changed == ("inputs", "input_review"):
        w = previous.corrected()
        b = w.frozen()
        with w.corrected_context(b), b.factory_boundary():
            data, pins = b.read_inputs(s.ROOT / provided["inputs"]["path"], provided["inputs"]["sha256"])
            b.authenticate_review(provided["input_review"], data, b.source_pins(pins))
    argv = actual_argv(out)
    for key in changed:
        flag = "--" + key.replace("_", "-")
        argv[argv.index(flag) + 1] = provided[key]["path"]
        argv[argv.index(flag + "-sha256") + 1] = provided[key]["sha256"]
    with patch.object(previous, "preflight", side_effect=AssertionError("mismatch reached preserved v3 preflight")), \
            pytest.raises(ValueError, match="supplied " + changed[0] + " reference differs from method binding"):
        s.main(argv)
    failed = json.loads(out.read_bytes())
    assert failed["status"] == "FAILED" and failed["accepted_q"] is None and failed["accepted_actions"] is None


@pytest.mark.parametrize("key", s.REFERENCE_KEYS)
def test_each_supplied_reference_requires_exact_method_bound_path_and_hash(tmp_path, key):
    refs = {name: {"path": str(tmp_path / name), "sha256": "a"*64} for name in s.REFERENCE_KEYS}
    geometry = {"report": {"path": "geometry", "sha256": "b"*64},
        "source_manifest": refs["source_manifest"], "cached_source_export": refs["source_export"]}
    method = {"input": refs["inputs"], "input_review": refs["input_review"], "geometry": geometry["report"],
        "source_manifest": refs["source_manifest"], "panel_bank": refs["panel_bank"], "input_record": {"path": "method"}}
    args = SimpleNamespace(method_input=tmp_path / "method", method_input_sha256="c"*64,
        **{name: Path(ref["path"]) for name, ref in refs.items()},
        **{name + "_sha256": ref["sha256"] for name, ref in refs.items()})
    b = SimpleNamespace(bundle=SimpleNamespace(artifact_path=str), read_method=lambda *_: method,
        read_ref=lambda ref: {"geometry": geometry}, require=s.previous().corrected().require)
    assert s.method_reference_bindings(args, b)["complete"] is True
    setattr(args, key + "_sha256", "d"*64)
    with pytest.raises(ValueError, match="supplied " + key + " reference differs from method binding"):
        s.method_reference_bindings(args, b)


def test_partial_no_method_reports_unchecked_bindings(tmp_path):
    out = tmp_path / "partial.json"
    assert s.main(["--out", str(out)]) == 0
    result = json.loads(out.read_bytes())
    assert set(result["missing"]) == {*s.REFERENCE_KEYS, "method_input"}
    assert result["method_reference_bindings"] == {"method_provided": False, "checked": {},
        "unchecked": list(s.REFERENCE_KEYS), "complete": False, "reason": "No complete method reference supplied."}
    assert result["production_readiness_claimed"] is False


def test_partial_exact_method_reports_missing_five_bindings(tmp_path):
    out = tmp_path / "method-only.json"
    argv = actual_argv(out)
    argv = ["--method-input", argv[argv.index("--method-input") + 1],
        "--method-input-sha256", argv[argv.index("--method-input-sha256") + 1], "--out", str(out)]
    assert s.main(argv) == 0
    result = json.loads(out.read_bytes())
    assert set(result["missing"]) == set(s.REFERENCE_KEYS)
    assert result["method_reference_bindings"]["method_provided"] is True
    assert result["method_reference_bindings"]["checked"] == {}
    assert result["method_reference_bindings"]["complete"] is False
    assert set(result["method_reference_bindings"]["unchecked"]) == set(s.REFERENCE_KEYS)


def test_input_hash_tamper_fails_before_preserved_preflight_and_retains_attempt(tmp_path):
    previous, out = s.previous(), tmp_path / "bad-input-hash.json"
    argv = actual_argv(out)
    argv[argv.index("--inputs-sha256") + 1] = "0"*64
    with patch.object(previous, "preflight", side_effect=AssertionError("tamper reached preserved preflight")), \
            pytest.raises(ValueError, match="supplied inputs reference differs from method binding"):
        s.main(argv)
    assert json.loads(out.read_bytes())["status"] == "FAILED"
    with patch.object(previous.corrected(), "frozen", side_effect=AssertionError("failed output reached frozen work")), \
            pytest.raises(FileExistsError):
        s.main(argv)


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_existing_output_refused_before_original_work(tmp_path, kind):
    w, out = s.previous().corrected(), tmp_path / "preserved.json"
    if kind == "file":
        out.write_text("preserved")
    else:
        out.symlink_to(tmp_path / "missing.json")
    with patch.object(w, "frozen", side_effect=AssertionError("existing output reached original work")), pytest.raises(FileExistsError):
        s.main(["--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()


def test_original_corrected_v3_and_all_review_sources_remain_exact():
    previous = s.previous()
    assert len(s.frozen_pins()) == 8
    assert len(previous.frozen_pins(previous.corrected())) == 12
