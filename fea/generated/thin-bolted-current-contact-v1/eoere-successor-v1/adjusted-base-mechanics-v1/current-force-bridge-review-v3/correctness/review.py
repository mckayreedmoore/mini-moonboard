"""Independent preflight-only correctness review using metadata/tiny fixtures.

PYTHONDONTWRITEBYTECODE=1 uv run python PATH/TO/review.py [--out NEW_RECEIPT]
No preparation, candidate operator, case solve, native solver or CAD is run.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import copy
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
MECH = OWN.parents[2]
TARGET = MECH / "current-force-bridge-v1/preflight-fix-v3"
EXPECTED = {
    "preflight.py": "a557f8ee72a211f809220f5ac25621e2c7a6c0d9fdfdadd94b95cc8d31c0254c",
    "test_preflight.py": "ff06c0b5f2b8d951f72f6f071141633950f82c50c904388ceb3f1386ecfb4334",
    "all-bindings.json": "780b589d2381fa2d469ff075f500f744142207957de1d663b1f8c4c3f801624e",
    "verification.json": "c5348a6100dfb2bae65e52499044a3d41c60a4fe5d351a4d83f46e40bb1107fd",
}
HELPER = MECH / "current-force-bridge-review-v2/correctness/review.py"
HELPER_SHA = "fff076563691cd353bcbf935f5a5bab943985874e96028c90f144b588014c469"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authenticate():
    targets = {str((TARGET / name).relative_to(ROOT)): value for name, value in EXPECTED.items()}
    assert all(sha(ROOT / path) == value for path, value in targets.items())
    saved = json.loads((TARGET / "all-bindings.json").read_bytes())
    verification = json.loads((TARGET / "verification.json").read_bytes())
    pins = {**saved["source_sha256"], **verification["preserved_source_sha256"], **targets,
            str(HELPER.relative_to(ROOT)): HELPER_SHA}
    assert all(sha(ROOT / path) == value for path, value in pins.items()), "source closure changed"
    return pins, saved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OWN.with_name("receipt.json"))
    args = parser.parse_args()
    assert not os.path.lexists(args.out), "preserve existing review evidence"
    before, saved = authenticate()
    helper = load(HELPER, "preflight_correctness_reused_code_signature_helper")
    supplement = load(TARGET / "preflight.py", "preflight_correctness_reviewed_supplement")
    w = supplement.corrected()
    b = w.frozen()
    checks = []
    assert saved["missing"] == [] and set(saved["provided"]) == {
        "inputs", "input_review", "method_input", "source_export", "source_manifest", "panel_bank"}
    assert saved["production_readiness_claimed"] is False
    assert saved["candidate_CAD_panel_K_global_K_q_actions_or_solve_performed"] is False
    assert not any(saved["release"].values())
    for ref in saved["provided"].values():
        assert saved["source_sha256"][ref["path"]] == ref["sha256"] == sha(ROOT / ref["path"])
    assert saved["source_preflight_supplement"]["frozen_producer_and_admission"] == {
        "path": str(supplement.CORRECTED.relative_to(ROOT)), "sha256": supplement.CORRECTED_SHA}
    raw = json.loads((ROOT / saved["provided"]["inputs"]["path"]).read_bytes())
    review = json.loads((ROOT / saved["provided"]["input_review"]["path"]).read_bytes())
    method = json.loads((ROOT / saved["provided"]["method_input"]["path"]).read_bytes())
    assert saved["provided"]["inputs"]["path"] not in raw["source_sha256"]
    assert review["input"] == method["input"] == saved["provided"]["inputs"]
    assert method["input_review"] == saved["provided"]["input_review"]
    checks.append("Saved all-bindings output retains six exact source references, valid input/review/method joins and false readiness/release flags")
    with tempfile.TemporaryDirectory(prefix="fixtures-", dir=OWN.parent) as directory:
        directory = Path(directory)
        original = w.FROZEN.read_text()
        tree = ast.parse(original)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "preflight")
        source = ast.get_source_segment(original, node)
        changes = {
            "data, _ = read_inputs(args.inputs, args.inputs_sha256)":
                "data, input_pins = read_inputs(args.inputs, args.inputs_sha256)",
            'source_pins(data["source_sha256"])': "source_pins(input_pins)"}
        for old, new in changes.items():
            assert source.count(old) == 1
            source = source.replace(old, new)
        expected = directory / "expected.py"
        expected.write_text(source + "\n")
        with w.corrected_context(b):
            actual = supplement.compile_preflight(w, b)
            assert helper.signature(actual.__code__) == helper.signature(helper.source_code(expected, "preflight"))
        checks.append("Independent text-substitution oracle matches entire compiled preflight code after exactly the two declared pin changes")
        data = {"source_sha256": {"internal-only": "a" * 64}}
        input_path, review_path = directory / "input.json", directory / "review.json"
        input_path.write_text(json.dumps(data))
        review_path.write_text("{}")
        argv = ["--mode", "preflight", "--inputs", str(input_path), "--inputs-sha256", sha(input_path),
                "--input-review", str(review_path), "--input-review-sha256", sha(review_path),
                "--out", str(directory / "unused-output.json")]
        request = b.parse_args(argv)
        input_pins = {**data["source_sha256"], b.bundle.artifact_path(input_path): sha(input_path),
                      "extra-returned-validated-pin": "b" * 64}
        observed = []
        def authenticator(record, supplied, pins):
            assert supplied == data and pins == input_pins
            observed.append(copy.deepcopy(pins))
        with patch.object(b, "source_pins", side_effect=lambda extra=None, **kwargs: dict(extra or {})), \
                patch.object(b, "compile_execute", return_value=None), patch.object(b, "admission_functions", return_value={}), \
                patch.object(b, "factory_boundary", side_effect=lambda: contextlib.nullcontext()), \
                patch.object(b, "read_inputs", return_value=(data, input_pins)), \
                patch.object(b, "authenticate_review", side_effect=authenticator):
            result = supplement.compile_preflight(w, b)(request)
            assert len(observed) == 1 and result["missing"] == ["method_input", "source_export", "source_manifest", "panel_bank"]
            with patch.object(b, "authenticate_review", side_effect=ValueError("inert rejected review")):
                try:
                    supplement.compile_preflight(w, b)(request)
                except ValueError as error:
                    assert str(error) == "inert rejected review"
                else:
                    raise AssertionError("review authentication failure was suppressed")
        checks.append("Tiny source fixture forwards full read_inputs pin map, including raw self-reference and extra validated pins; authenticator errors propagate")
    assert b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA
    assert b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ
    assert b.factory.authenticate_source_review is b.ORIGINAL_AUTHENTICATE
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(TARGET / "test_preflight.py")]
    run = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1"))
    assert "6 passed" in run.stdout, run.stdout
    checks.append("Six guarded existing tests pass: real source-only six-bindings regression, bad raw SHA, repeat/existing/dangling output refusal and producer-mode refusal")
    after, _ = authenticate()
    assert after == before
    receipt = {"schema": "eoere_preflight_pin_supplement_independent_correctness_review/v3",
        "status": "NO_SUBSTANTIAL_FINDINGS_WITHIN_SOURCE_ONLY_SCOPE", "findings": [], "checks": checks,
        "source_sha256_before": before, "source_sha256_after": after, "sources_exact_before_after_unchanged": True,
        "reused_review_helper": {"path": str(HELPER.relative_to(ROOT)), "sha256": HELPER_SHA},
        "review_script": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "tests": {"command": command, "output": run.stdout.strip()}, "release": dict(b.core.RELEASE),
        "limits": ["Source-only preflight success does not establish production readiness, complete joint resistance or structural acceptance.",
                   "No actual K, candidate preparation, current-case response, native solve, CAD or browser was run.",
                   "Producer/admission491653, prior reviews, current inputs and failed original preflight remain byte-identical."],
        "retention": {"active": "Frozen preflight supplement, original producer/admission, input/review/method and this review", "archive_or_prune_performed": False}}
    with args.out.open("x") as output:
        json.dump(receipt, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    print(json.dumps({"status": receipt["status"], "authenticated_sources": len(before), "receipt_sha256": sha(args.out)}))


if __name__ == "__main__":
    main()
