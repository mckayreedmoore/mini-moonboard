"""Independent v4 method-binding review; source metadata and inert fixtures.

Run: PYTHONDONTWRITEBYTECODE=1 uv run python PATH/TO/review.py [--out NEW_RECEIPT]
No current field, operator bundle, force slot, preparation or solver is used.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
MECH = OWN.parents[2]
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v4"
EXPECTED = {
    "preflight.py": "244f441114f3215d82e45d55403da5cfb2417d9b996779bcb5291188c2cd7ad2",
    "test_preflight.py": "ffb459d39cc7855ca4fb3f597bc025ab2f7553486666008e374c691cdf1ecbae",
    "all-bindings.json": "3f80b1185b88812d18219b1cea2ed2c1dee3cb8b323f2dafc72558f3e554f8d4",
    "verification.json": "afc71138a185b23eba2fa2d4d8947691446226814ea0c5f6223d1f08b735ab59",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def authenticate():
    pins = {str((TARGET / name).relative_to(ROOT)): value for name, value in EXPECTED.items()}
    assert all(sha(ROOT / path) == value for path, value in pins.items())
    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    pins.update(saved["source_sha256"])
    assert all(sha(ROOT / path) == value for path, value in pins.items()), "frozen source closure changed"
    return pins, saved


def require(ok, message):
    if not ok:
        raise ValueError(message)


def reject(callback, expected):
    try:
        callback()
    except ValueError as error:
        assert expected in str(error), str(error)
    else:
        raise AssertionError("negative binding fixture accepted")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OWN.with_name("receipt.json"))
    args = parser.parse_args()
    assert not os.path.lexists(args.out), "preserve prior review receipt"
    before, saved = authenticate()
    spec = importlib.util.spec_from_file_location("independent_v4_reference_correctness", TARGET / "preflight.py")
    supplement = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supplement)
    checks = []
    previous = json.loads(supplement.V3.with_name("all-bindings.json").read_bytes())
    for key, value in previous.items():
        if key not in {"source_sha256", "source_preflight_execution"}:
            assert saved[key] == value, key
    assert all(saved["source_sha256"].get(key) == value for key, value in previous["source_sha256"].items())
    bindings = saved["method_reference_bindings"]
    assert saved["missing"] == [] and bindings["complete"] is True and bindings["unchecked"] == []
    assert bindings["checked"] == {key: saved["provided"][key] for key in supplement.REFERENCE_KEYS}
    assert bindings["method"] == saved["provided"]["method_input"]
    method = json.loads((ROOT / bindings["method"]["path"]).read_bytes())
    inputs = json.loads((ROOT / method["input"]["path"]).read_bytes())
    expected_bound = {"inputs": method["input"], "input_review": method["input_review"],
        "source_manifest": method["source_manifest"], "panel_bank": method["panel_bank"],
        "source_export": inputs["geometry"]["cached_source_export"]}
    assert bindings["checked"] == expected_bound
    assert inputs["geometry"]["report"] == method["geometry"]
    assert inputs["geometry"]["source_manifest"] == method["source_manifest"]
    assert saved["production_readiness_claimed"] is False
    assert saved["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
    assert not any(saved["release"].values())
    checks.append("Saved v4 success independently matches all five method-bound references; prior mechanics/schema/release metadata and source pins remain unchanged")
    with tempfile.TemporaryDirectory(prefix="fixtures-", dir=OWN.parent) as directory:
        directory = Path(directory)
        refs = {key: {"path": str(directory / key), "sha256": "a" * 64} for key in supplement.REFERENCE_KEYS}
        geometry = {"report": {"path": "synthetic-geometry", "sha256": "b" * 64},
            "source_manifest": refs["source_manifest"], "cached_source_export": refs["source_export"]}
        method = {"input": refs["inputs"], "input_review": refs["input_review"],
            "source_manifest": refs["source_manifest"], "panel_bank": refs["panel_bank"],
            "geometry": geometry["report"], "input_record": {"path": "synthetic-method", "sha256": "c" * 64}}
        model = SimpleNamespace(bundle=SimpleNamespace(artifact_path=str), require=require,
            read_method=lambda *_: copy.deepcopy(method), read_ref=lambda _ref: {"geometry": copy.deepcopy(geometry)},
            source_pins=lambda pins: dict(pins))
        full = SimpleNamespace(mode="preflight", run=False, method_input=directory / "method", method_input_sha256="c" * 64,
            **{key: Path(ref["path"]) for key, ref in refs.items()},
            **{key + "_sha256": ref["sha256"] for key, ref in refs.items()})
        for mask in range(32):
            trial = copy.deepcopy(full)
            supplied = set()
            for i, key in enumerate(supplement.REFERENCE_KEYS):
                if mask & (1 << i):
                    supplied.add(key)
                else:
                    setattr(trial, key, None)
                    setattr(trial, key + "_sha256", None)
            result = supplement.method_reference_bindings(trial, model)
            assert result["checked"] == {key: refs[key] for key in supplement.REFERENCE_KEYS if key in supplied}
            assert result["unchecked"] == [key for key in supplement.REFERENCE_KEYS if key not in supplied]
            assert result["complete"] is (mask == 31) and result["method_provided"] is True
        for key in supplement.REFERENCE_KEYS:
            for missing in (key, key + "_sha256"):
                trial = copy.deepcopy(full)
                setattr(trial, missing, None)
                result = supplement.method_reference_bindings(trial, model)
                assert result["unchecked"] == [key] and result["complete"] is False
        for missing in ("method_input", "method_input_sha256"):
            trial = copy.deepcopy(full)
            setattr(trial, missing, None)
            result = supplement.method_reference_bindings(trial, model)
            assert result["method_provided"] is False and result["checked"] == {} and result["complete"] is False
            assert result["unchecked"] == list(supplement.REFERENCE_KEYS)
        checks.append("All 32 reference subsets, ten partial reference pairs and two partial method pairs report exact checked/unchecked/completeness state")
        calls = []
        def preserved(request, wrapper, data_model):
            assert request is full and data_model is model
            calls.append("v3-preflight")
            return {"source_sha256": {}, "mechanics": {"sentinel": "preserved"}, "release": {"released": False}}
        v3 = SimpleNamespace(preflight=preserved)
        wrapper = SimpleNamespace(require=require)
        with patch.object(supplement, "frozen_pins", return_value={}):
            result = supplement.preflight(full, v3, wrapper, model)
            assert calls == ["v3-preflight"] and result["mechanics"] == {"sentinel": "preserved"}
            for key in supplement.REFERENCE_KEYS:
                trial = copy.deepcopy(full)
                setattr(trial, key + "_sha256", "d" * 64)
                calls.clear()
                reject(lambda trial=trial: supplement.preflight(trial, v3, wrapper, model), "supplied " + key)
                assert calls == []
            for key in ("report", "source_manifest"):
                bad_geometry = copy.deepcopy(geometry)
                bad_geometry[key] = {"path": "foreign", "sha256": "e" * 64}
                with patch.object(model, "read_ref", return_value={"geometry": bad_geometry}):
                    reject(lambda: supplement.preflight(full, v3, wrapper, model), "input geometry/manifest")
            for mode in ("run", "admit", "build-inputs"):
                trial = copy.deepcopy(full)
                trial.mode = mode
                reject(lambda trial=trial: supplement.preflight(trial, v3, wrapper, model), "source-preflight-only")
            trial = copy.deepcopy(full)
            trial.run = True
            reject(lambda: supplement.preflight(trial, v3, wrapper, model), "source-preflight-only")
        checks.append("Five method-reference mismatches and two input geometry/manifest mismatches stop before v3; producer/admit/build-inputs/--run modes reject")
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--import-mode=importlib",
        str(TARGET / "test_preflight.py"), str(supplement.V3.with_name("test_preflight.py"))]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"))
    assert "20 passed" in run.stdout, run.stdout
    checks.append("All 14 v4 and six v3 guarded source-only tests pass, including genuine references, valid mismatched pair, failed/existing/dangling output guards")
    after, _ = authenticate()
    assert after == before
    receipt = {"schema": "eoere_v4_preflight_independent_correctness_review/v1",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_ONLY_SCOPE", "findings": [], "checks": checks,
        "source_sha256_before": before, "source_sha256_after": after, "sources_exact_before_after_unchanged": True,
        "review_script": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "tests": {"command": command, "output": run.stdout.strip()}, "release": saved["release"],
        "limits": ["This review addresses source-only preflight method-reference equality and reporting.",
                   "Genuine fields and operator bundles were not consumed; no K/preparation/solve/native/CAD/browser was run and no force slot was read or changed.",
                   "Producer/admission491653 and all prior frozen records remain unchanged; this does not establish structural acceptance."],
        "retention": {"active": "Current preflight supplement, frozen dependencies, prior reviews and this review", "archive_or_prune_performed": False}}
    with args.out.open("x") as output:
        json.dump(receipt, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    print(json.dumps({"status": receipt["status"], "authenticated_sources": len(before), "receipt_sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
