"""Final AST/contract probes using source JSON and inert callbacks only."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import pytest

OWN = Path(__file__).resolve()
ROOT = OWN.parents[10]
CONSUMER = OWN.parents[2]
TARGET = CONSUMER / "review-fix-v2"
REVIEW = ROOT / "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-inputs-v1/independent-review-v2/correctness/receipt.json"
PINS = {
    TARGET / "consume.py": "791e39cbdfbf80e6a207ca568898c0347e7f400ac428efa84dc65906a8a8cf92",
    TARGET / "test_consume.py": "6828f723f53d1e3d411ce114d352000bd0156c17713c548003a139ac3cc2524c",
    TARGET / "verification.json": "0ceea1da4d9c7c4a7b09f896d2fa2b9787c491756d11c95c531f3e7901ce7832",
    CONSUMER / "consume.py": "673498ce0cb1cb95bf6f263e2710b357f9792eaf8d12020c25a0812dc12a1d80",
    CONSUMER / "test_consume.py": "1024873b79c965172ddd7d4324063863c4d41561570f30c24d9cd895b6bd7d44",
    CONSUMER / "verification.json": "fe7cdb509058d116049fef87bf91266378d4dc252b68c9e80b64d9a439ce2286",
    CONSUMER / "independent-review-v1/correctness/receipt.json": "d3d0bfd9e2206c657583daf1dad8940ceec4f99f5ef4571ebddf43a1f69bbf1d",
    REVIEW: "acecce87e8b737374f75b896a7875fcdf287649923b641d431edb8a301e49a38",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_sources():
    for path, expected in PINS.items():
        assert sha(path) == expected, str(path)


def load(path, label):
    spec = importlib.util.spec_from_file_location(label, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reject(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("expected fail-closed ValueError")


def ast_and_authentic_contract_probe(tests):
    w, a = tests.m, tests.a
    frozen_tree = ast.parse(w.FROZEN.read_bytes())
    function = next(n for n in frozen_tree.body if isinstance(n, ast.FunctionDef) and n.name == "authenticate")
    expected = copy.deepcopy(function)
    matches = [n for n in ast.walk(expected) if isinstance(n, ast.Compare)
               and ast.dump(n) == ast.dump(ast.parse("review['release'] == RELEASE", mode="eval").body)]
    assert len(matches) == 1
    matches[0].comparators[0] = ast.Name(id="DESCRIPTOR_RELEASE", ctx=ast.Load())
    captured = []
    original_compile = builtins.compile
    def capture(tree, *args, **kwargs):
        if isinstance(tree, ast.Module):
            captured.append(copy.deepcopy(tree))
        return original_compile(tree, *args, **kwargs)
    with patch.object(w, "compile", capture, create=True):
        callback = w.corrected_authenticate(a)
    assert len(captured) == 1 and len(captured[0].body) == 1
    assert ast.dump(captured[0].body[0]) == ast.dump(expected)
    corrected = inspect.getclosurevars(callback).nonlocals["corrected"]
    assert corrected.__globals__["RELEASE"] is a.RELEASE
    assert corrected.__globals__["DESCRIPTOR_RELEASE"] == w.DESCRIPTOR_RELEASE
    assert corrected.__globals__["DESCRIPTOR_RELEASE"] is not a.RELEASE
    for key in ("checked", "verify", "load", "decode", "merge"):
        assert corrected.__globals__[key] is getattr(a, key)
    before = REVIEW.read_bytes()
    authentic = json.loads(before)
    original_guard = next(n.args[0] for n in ast.walk(function) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "require" and len(n.args) > 1
        and isinstance(n.args[1], ast.Constant) and n.args[1].value == "exact own descriptor review required")
    corrected_guard = next(n.args[0] for n in ast.walk(expected) if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name) and n.func.id == "require" and len(n.args) > 1
        and isinstance(n.args[1], ast.Constant) and n.args[1].value == "exact own descriptor review required")
    # Evaluate only the source-JSON review predicate, not authenticate or a gate.
    scope = {"review": authentic, "refs": {"descriptor": authentic["descriptor"]},
             "RELEASE": a.RELEASE, "DESCRIPTOR_RELEASE": w.DESCRIPTOR_RELEASE}
    assert eval(compile(ast.Expression(original_guard), str(w.FROZEN), "eval"), scope) is False
    assert eval(compile(ast.fix_missing_locations(ast.Expression(corrected_guard)), str(w.FROZEN), "eval"), scope) is True
    assert REVIEW.read_bytes() == before
    return {"compiled_AST_matches_exact_original_plus_one_review_release_comparator": True,
            "mechanics_RELEASE_object_preserved": True, "authentication_helpers_keep_original_function_identities": True,
            "authentic_selected_review_predicate_accepts_unmodified_record": True,
            "original_guard_rejects_same_unmodified_record": True,
            "authentic_descriptor_reference": authentic["descriptor"],
            "authentic_release": authentic["release"], "authentic_receipt_bytes_unchanged": True}


def with_coupon(tests, callback):
    with tempfile.TemporaryDirectory(prefix="inert-z180-release-review-") as root, pytest.MonkeyPatch.context() as patches:
        coupon = tests.tiny.__wrapped__(Path(root), patches)
        callback(coupon, patches)


def pin_order_and_restore_probe(tests):
    w, a = tests.m, tests.a
    checked = []
    for kind in ("success", "fake_reducer_failure", "fake_reducer_mutation", "wrapper_drift_during_fake_gate"):
        def check(coupon, patches, kind=kind):
            original_auth = a.authenticate
            original_release = dict(a.RELEASE)
            before_review = (coupon.root / "review.json").read_bytes()
            fake_reduce = a.reduce_admitted
            reached = []
            def guarded_fake(config, records, field, pins, gate, **kwargs):
                assert pins["consume.py"] == w.FROZEN_SHA
                assert pins["review-fix-v2/consume.py"] == w.LOADED_SHA
                assert a.RELEASE == original_release and field["release"] == original_release
                assert (coupon.root / "review.json").read_bytes() == before_review
                reached.append("both_self_pins_present_before_fake_reducer")
                result = fake_reduce(config, records, field, pins, gate, **kwargs)
                if kind == "fake_reducer_failure":
                    raise ValueError("inert reducer failure")
                if kind == "fake_reducer_mutation":
                    field["case_id"] = "foreign"
                return result
            patches.setattr(a, "reduce_admitted", guarded_fake)
            if kind == "wrapper_drift_during_fake_gate":
                coupon.during_gate = lambda: w.OWN.write_bytes(w.OWN.read_bytes() + b"\n")
            if kind == "success":
                result = tests.call(coupon)
                assert result["release"] == original_release and result["complete_joint_resistance"] is None
                assert reached == ["both_self_pins_present_before_fake_reducer"]
            else:
                reject(lambda: tests.call(coupon))
                assert bool(reached) == (kind != "wrapper_drift_during_fake_gate")
            assert a.authenticate is original_auth and a.RELEASE == original_release
            assert (coupon.root / "review.json").read_bytes() == before_review
        with_coupon(tests, check)
        checked.append(kind)
    return {"inert_paths": checked, "original_and_wrapper_source_pins_verified_before_fake_reducer": True,
            "wrapper_source_drift_during_fake_admission_rejected_before_fake_reducer": True,
            "authenticate_and_mechanics_release_restored_on_success_and_failure": True,
            "inert_descriptor_review_bytes_preserved": True}


def check():
    verify_sources()
    prohibited = []
    original_import = builtins.__import__
    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"numpy", "scipy", "cadquery", "OCP", "mini_moonboard"}:
            prohibited.append(name)
            raise AssertionError("inert review attempted numerical/geometry import: " + name)
        return original_import(name, *args, **kwargs)
    with patch.object(builtins, "__import__", guarded_import):
        tests = load(TARGET / "test_consume.py", "independent_final_z180_release_fixtures")
        ast_contract = ast_and_authentic_contract_probe(tests)
        pins_and_restore = pin_order_and_restore_probe(tests)
        assert not prohibited
    verify_sources()
    return {"schema": "independent_final_z180_component_correctness_review/v2", "passed": True,
            "review_program_sha256": sha(OWN), "source_sha256": {str(p.relative_to(ROOT)): h for p, h in PINS.items()},
            "AST_and_contract": ast_contract, "pins_and_restoration": pins_and_restore,
            "actual_admission_or_reducer_callbacks_or_calculations": 0, "genuine_config_pair_consumed": False,
            "prohibited_import_attempts": prohibited,
            "CAD_BREP_panel_K_q_native_frame_solve_browser_executed": False,
            "substantial_confirmed_findings": [],
            "limits": ["Source predicate evaluation and inert fake callbacks only; no genuine readiness supplied.",
                       "Unchanged39-test boundary and arithmetic reviews remain frozen references, not new force results."]}


if __name__ == "__main__":
    print(json.dumps(check(), indent=2, sort_keys=True, allow_nan=False))
