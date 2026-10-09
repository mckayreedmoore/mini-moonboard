"""Final descriptor-release seam review; fake boundaries and exact AST only."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
TARGET = OWN.parents[2]
FIX = TARGET / "review-fix-v2"
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "review-fix-v2/consume.py": "791e39cbdfbf80e6a207ca568898c0347e7f400ac428efa84dc65906a8a8cf92",
    "review-fix-v2/test_consume.py": "6828f723f53d1e3d411ce114d352000bd0156c17713c548003a139ac3cc2524c",
    "review-fix-v2/verification.json": "0ceea1da4d9c7c4a7b09f896d2fa2b9787c491756d11c95c531f3e7901ce7832",
    "independent-review-v1/testing/review.py": "f64873a6a3b5b4fb6b488768a19178b403820ced62ebb654c666de1c60e3b178",
    "independent-review-v1/testing/receipt.json": "2523158dea74f63f8b3faa45b85f22114794fa24d19a8e3c39948f4b0dc14001",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load_tests():
    spec = importlib.util.spec_from_file_location("independent_final_release_fixtures", FIX / "test_consume.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flatten(node, prefix=""):
    result = {}
    if isinstance(node, ast.AST):
        result[prefix + ".type"] = type(node).__name__
        for key, value in ast.iter_fields(node):
            result.update(flatten(value, prefix + "." + key))
    elif isinstance(node, list):
        result[prefix + ".length"] = len(node)
        for index, value in enumerate(node):
            result.update(flatten(value, prefix + f"[{index}]"))
    else:
        result[prefix] = node
    return result


def exact_ast_scope(wrapper):
    original = wrapper.original()
    captured = []
    def compile_ast(tree, *args, **kwargs):
        captured.append(copy.deepcopy(tree))
        return builtins.compile(tree, *args, **kwargs)
    before_authenticate, before_release = original.authenticate, dict(original.RELEASE)
    with patch.object(wrapper, "compile", compile_ast, create=True):
        authenticate = wrapper.corrected_authenticate(original)
    assert original.authenticate is before_authenticate and original.RELEASE == before_release
    assert len(captured) == 1 and isinstance(captured[0], ast.Module) and len(captured[0].body) == 1
    original_function = next(node for node in ast.parse(wrapper.FROZEN.read_bytes()).body
                             if isinstance(node, ast.FunctionDef) and node.name == "authenticate")
    prior, current = flatten(original_function), flatten(captured[0].body[0])
    assert prior.keys() == current.keys()
    changes = {key: [prior[key], current[key]] for key in prior if prior[key] != current[key]}
    assert len(changes) == 1 and list(changes.values()) == [["RELEASE", "DESCRIPTOR_RELEASE"]]
    assert next(iter(changes)).endswith(".comparators[0].id")
    closure = dict(zip(authenticate.__code__.co_freevars, (cell.cell_contents for cell in authenticate.__closure__), strict=True))
    corrected = closure["corrected"]
    assert corrected.__globals__["RELEASE"] is original.RELEASE
    assert corrected.__globals__["DESCRIPTOR_RELEASE"] == wrapper.DESCRIPTOR_RELEASE
    assert corrected.__globals__["DESCRIPTOR_RELEASE"] is not wrapper.DESCRIPTOR_RELEASE
    return {"AST_leaf_changes": changes, "only_authenticate_compiled": True,
            "mechanics_RELEASE_identity_preserved": True, "descriptor_contract_copied_into_scoped_namespace": True}


def controls(tests, scratch):
    observed = {}
    modes = ("positive", "foreign_descriptor", "false_review_success", "raw_review_bytes", "wrong_admission_pair",
             "wrong_admission_state", "descriptor_style_config", "reducer_exception")
    for mode in modes:
        root = scratch / mode
        root.mkdir()
        with pytest.MonkeyPatch.context() as monkey:
            t = tests.tiny.__wrapped__(root, monkey)
            wrapper, original = tests.m, tests.a
            old_authenticate, old_release = original.authenticate, dict(original.RELEASE)
            review_bytes = (root / "review.json").read_bytes()
            if mode == "foreign_descriptor":
                t.review["descriptor"] = {**t.review["descriptor"], "sha256": "0" * 64}
                ref = t.controls.write(root, "review.json", t.review)
                t.config["sources"]["descriptor_review"] = ref
            elif mode == "false_review_success":
                t.review["independent_z180_descriptor_source_checks_pass"] = False
                t.freeze_review()
            elif mode == "raw_review_bytes":
                (root / "review.json").write_bytes(review_bytes + b"\n")
            elif mode in {"wrong_admission_pair", "wrong_admission_state"}:
                t.receipt_extra["field_sha256" if mode == "wrong_admission_pair" else "state_id"] = "0" * 64
                t.freeze()
                t.freeze_review()
            elif mode == "descriptor_style_config":
                t.config["release"] = dict(wrapper.DESCRIPTOR_RELEASE)
            callback = original.reduce_admitted
            calls = []
            def reduce(*args, callback=callback, calls=calls, wrapper=wrapper, original=original, control_mode=mode, **kwargs):
                pins = args[3]
                assert pins[str(wrapper.OWN.relative_to(original.ROOT))] == wrapper.LOADED_SHA
                assert pins[str(original.OWN.relative_to(original.ROOT))] == wrapper.FROZEN_SHA
                calls.append("source_pins_present_before_inert_reducer")
                if control_mode == "reducer_exception":
                    raise ValueError("inert reducer stop")
                return callback(*args, **kwargs)
            monkey.setattr(original, "reduce_admitted", reduce)
            t.config_ref = t.controls.write(root, "config.json", t.config)
            try:
                result = tests.call(t)
            except ValueError as error:
                assert mode != "positive"
                observed[mode] = str(error)
            else:
                assert mode == "positive", "negative contract accepted: " + mode
                assert calls == ["source_pins_present_before_inert_reducer"]
                assert (root / "review.json").read_bytes() == review_bytes
                assert result["release"] == old_release and result["complete_joint_resistance"] is None
                assert result["nominal_seat_geometry"]["nominal_wood_seats"] is None
                observed[mode] = "authentic contract shape accepts unchanged bytes; exact consumer pins precede inert reducer"
            assert original.authenticate is old_authenticate and original.RELEASE == old_release
            if mode not in {"positive", "reducer_exception"}:
                assert not calls and "inert_reducer_callback" not in t.events
            if mode == "reducer_exception":
                assert calls == ["source_pins_present_before_inert_reducer"]
    return observed


def main():
    prior_receipt = read(TARGET / "independent-review-v1/testing/receipt.json")
    frozen = dict(prior_receipt["source_sha256"])
    frozen.update({str((TARGET / name).relative_to(ROOT)): digest for name, digest in EXPECTED.items()})
    verification = read(FIX / "verification.json")
    ref = verification["authentic_review_metadata_fixture_basis"]
    frozen[ref["path"]] = ref["sha256"]
    old_reviews = {str(path.relative_to(ROOT)): sha(path) for path in (TARGET / "independent-review-v1").rglob("*")
                   if path.is_file() and path.suffix in {".py", ".json"}}

    def unchanged():
        assert all(sha(ROOT / path) == digest for path, digest in frozen.items())
        assert all(sha(ROOT / path) == digest for path, digest in old_reviews.items())

    unchanged()
    tests = load_tests()
    scope = exact_ast_scope(tests.m)
    with tempfile.TemporaryDirectory(prefix="z180-final-consumer-testing-") as directory:
        checks = controls(tests, Path(directory))
        command = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", str(FIX / "test_consume.py")]
        run = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
        assert run.returncode == 0 and "15 passed" in run.stdout, run.stderr + run.stdout
    unchanged()
    assert not any(name in sys.modules for name in ("cadquery", "OCP", "numpy", "scipy"))
    report = {"schema": "eoere_z180_component_corrected_consumer_independent_testing_review/v2",
              "status": "PASS_WITHIN_INERT_SOURCE_SCOPE", "confirmed_substantial_findings": [],
              "source_sha256": frozen, "review_source_sha256": {str(OWN.relative_to(ROOT)): sha(OWN)},
              "all_frozen_sources_and_v1_reviews_unchanged_before_after": True, "preserved_v1_reviews": old_reviews,
              "single_source_bound_AST_seam": scope, "independent_inert_contract_controls": checks,
              "new_inert_suite": {"passed": 15, "command": command, "stdout": run.stdout},
              "reused_evidence": {"original_inert_tests": 39, "original_boundary_review_sha256": EXPECTED["independent-review-v1/testing/receipt.json"],
                                  "frozen_math_rerun": False, "retained_100_axes_16_own_96_inherited_seats_and_22_fittings": True},
              "readiness": verification["readiness"], "release": verification["release"],
              "execution": {"only_source_metadata_AST_and_fake_callbacks": True,
                            "actual_configs_fields_admissions_reducers_numbers_CAD_BREP_K_q_solve_or_browser": False,
                            "shared_docs_Git_index_staging_or_commit_changes": False},
              "retention": "Keep final compact review alongside frozen v1 evidence. Temporary fake configs/outputs removed; selected authentic review JSON used for metadata shape only. Genuine consumption remains deferred and parent-owned."}
    output = OWN.with_name("receipt.json")
    output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"path": str(output.relative_to(ROOT)), "sha256": sha(output), "bytes": output.stat().st_size,
                      "confirmed_substantial_findings": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
