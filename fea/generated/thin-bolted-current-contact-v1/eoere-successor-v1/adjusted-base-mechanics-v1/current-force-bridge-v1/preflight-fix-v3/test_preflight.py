"""Real all-bindings source regression and fresh-output/hash refusal controls."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
spec = importlib.util.spec_from_file_location("eoere_raw_input_pin_preflight_fixture", OWN.with_name("preflight.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
READINESS = s.BASE.parent / "current-readiness-v1"


def actual_argv(out):
    command = json.loads((READINESS / "process.json").read_bytes())["command"]
    argv = command[command.index("--mode"):]
    argv[argv.index("--out") + 1] = str(out)
    return argv


def prohibited(*_args, **_kwargs):
    raise AssertionError("source-only preflight reached candidate preparation or a panel/frame operator")


def test_real_exact_input_review_method_all_bindings_preflight(tmp_path):
    w, out = s.corrected(), tmp_path / "all-bindings.json"
    b = w.frozen()
    observed = []
    original_auth, original_load = b.authenticate_review, b.load
    def authenticate(ref, data, pins, **kwargs):
        raw = json.loads((s.ROOT / ref["path"]).read_bytes())["input"]
        assert raw["path"] not in data["source_sha256"]
        assert pins[raw["path"]] == raw["sha256"] == "f0c55ac1d67650eec2de0cedfe4ec383d5b2a04253fbf10c9db9df9251711baa"
        observed.append(raw)
        return original_auth(ref, data, pins, **kwargs)
    def load(path, sha, name):
        module = original_load(path, sha, name)
        if Path(path).resolve() == (s.ROOT / b.PANEL_BANK["path"]).resolve():
            module.load_panel_dependencies = prohibited
            module.prepare_panel_operators = prohibited
        return module
    with patch.object(b, "authenticate_review", side_effect=authenticate), patch.object(b, "load", side_effect=load), \
            patch.object(b.factory, "prepare", side_effect=prohibited), patch.object(b.frame, "ElasticAssembly", side_effect=prohibited), \
            patch.object(b, "run_case", side_effect=prohibited):
        assert s.main(actual_argv(out)) == 0
    result = json.loads(out.read_bytes())
    assert len(observed) == 1 and result["missing"] == []
    assert result["provided"]["input_review"]["sha256"] == "f7936b055d3a0ee9a475b09bff73d46fbbf25303c23c17c14e2d3e6c4c97eb2c"
    assert result["provided"]["method_input"]["sha256"] == "941ca92e8230de9d480d17f6e2a082d05a3fae267329ef0b33c81d06d0ad46f5"
    assert result["source_preflight_supplement"]["validated_read_inputs_returned_pins_retained_for_review_authentication"] is True
    assert result["production_readiness_claimed"] is False
    assert result["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
    assert not any(result["release"].values())


def test_negative_actual_input_raw_hash_retains_failed_attempt_before_authentication(tmp_path):
    w, out = s.corrected(), tmp_path / "bad-input-hash.json"
    b = w.frozen()
    argv = actual_argv(out)
    argv[argv.index("--inputs-sha256") + 1] = "0"*64
    with patch.object(b, "authenticate_review", side_effect=AssertionError("hash tamper reached review")), \
            patch.object(b.factory, "prepare", side_effect=prohibited), \
            pytest.raises(ValueError, match="provided current source bytes differ"):
        s.main(argv)
    failed = json.loads(out.read_bytes())
    assert failed["status"] == "FAILED" and failed["accepted_q"] is None and failed["accepted_actions"] is None
    with patch.object(w, "frozen", side_effect=AssertionError("repeated failed output reached frozen import")), pytest.raises(FileExistsError):
        s.main(argv)


@pytest.mark.parametrize("kind", ["file", "dangling_symlink"])
def test_output_reserved_before_original_frozen_work(tmp_path, kind):
    w, out = s.corrected(), tmp_path / "preserved.json"
    if kind == "file":
        out.write_text("preserved")
    else:
        out.symlink_to(tmp_path / "missing.json")
    with patch.object(w, "frozen", side_effect=AssertionError("existing output reached original work")), pytest.raises(FileExistsError):
        s.main(["--out", str(out)])
    assert out.read_text() == "preserved" if kind == "file" else out.is_symlink()


def test_supplement_refuses_producer_modes(tmp_path):
    out = tmp_path / "not-a-producer.json"
    with pytest.raises(ValueError, match="source-preflight-only"):
        s.main(["--mode", "build-inputs", "--out", str(out)])
    assert json.loads(out.read_bytes())["status"] == "FAILED"


def test_original_corrected_and_three_final_review_hashes_stay_exact():
    pins = s.frozen_pins(s.corrected())
    assert len(pins) == 12
    assert pins[str(s.CORRECTED.relative_to(s.ROOT))] == s.CORRECTED_SHA
