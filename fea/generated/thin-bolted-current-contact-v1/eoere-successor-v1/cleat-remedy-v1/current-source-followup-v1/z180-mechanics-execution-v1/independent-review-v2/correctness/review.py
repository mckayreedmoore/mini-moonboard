"""Independent inert review of final Z180 roster wrapper; reuse frozen v1 proof."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[1]
TARGET = PACKET / "review-fix-v2"
ROOT = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
TARGETS = {
    "bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
    "test_bridge.py": "7139f66d4218510d1eefc7e9d6f2b4827ff673d01c3cdb073c1a2dd9ee3b65a2",
    "source-preflight.json": "2b76796f808dce7805aaf338729571c078f4676f7e589dc626f1ceeeb483c092",
    "verification.json": "97845159bf1c8e59df46ac09ab072df2af2fcc8069b5ed57ff2eaa4e2195aaf5",
}
PRIOR = PACKET / "independent-review-v1/correctness"
PRIOR_HASHES = {"review.py": "6c7dd0e335d4c003fa66a1ca0811285fa028d0910f9743ac5069ad44e836bfb6",
                "receipt.json": "941b9114d1516ded9bfc92ba605c80f0f8eb4b1840fe87468952a7aaf520c605"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok):
    if not ok:
        raise AssertionError("independent wrapper review failed")


def evaluate():
    pins = {str((TARGET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    pins.update({str((PRIOR / name).relative_to(ROOT)): digest for name, digest in PRIOR_HASHES.items()})
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()))
    prior = json.loads((PRIOR / "receipt.json").read_bytes())
    require(prior["findings"] == [])
    pins.update(prior["reviewed_sha256"])
    saved = json.loads((TARGET / "source-preflight.json").read_bytes())
    for name, digest in saved["source_sha256"].items():
        require(name not in pins or pins[name] == digest)
        pins[name] = digest
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins)
    spec = importlib.util.spec_from_file_location("independent_z180_v2_inert_tests", TARGET / "test_bridge.py")
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    c, count = tests.c, 0
    for name in ("test_import_has_no_original_adapter_or_candidate_callback",
                 "test_exact_roster_delegates_original_all_source_checks_once",
                 "test_authenticated_parent_and_declared_moved_rosters_are_exact",
                 "test_source_drift_and_nested_context_fail_closed_and_restore"):
        getattr(tests, name)()
        count += 1
    for kind in ("duplicate_moved", "omitted_moved", "unknown_axis"):
        tests.test_bad_roster_rejects_descriptor_and_coherently_joined_inputs_before_delegate(kind)
        tests.test_bad_roster_stops_original_builder_before_any_panel_callback(kind)
        count += 2
    for source in ("original", "correction"):
        tests.test_conflicting_adapter_source_pin_rejected(source)
        count += 1

    a = c.original()
    originals = {name: getattr(a, name) for name in ("OWN", "LOADED_SHA", "validate_descriptor", "source_pins")}
    extra_roster_rejects = 0
    for kind in ("duplicate_unmoved", "missing_unmoved", "duplicate_declared", "unknown_declared"):
        _, exported, _, read = tests.mutated("valid")
        authority = copy.deepcopy(a.manifest())
        if kind == "duplicate_unmoved":
            exported["shafts"][50] = copy.deepcopy(exported["shafts"][51])
        elif kind == "missing_unmoved":
            exported["shafts"].pop()
        elif kind == "duplicate_declared":
            authority["declared_changes"]["axis_ids"][0] = authority["declared_changes"]["axis_ids"][1]
        else:
            authority["declared_changes"]["axis_ids"][0] = "unknown_declared"
        delegate = Mock(side_effect=AssertionError("invalid roster reached original validator"))
        with patch.object(a, "read_ref", side_effect=read), patch.object(a, "manifest", return_value=authority), \
                patch.object(a, "validate_descriptor", delegate), c.corrected_context(a):
            try:
                a.validate_descriptor(exported)
            except ValueError as error:
                require("exact unique 100" in str(error))
                extra_roster_rejects += 1
            else:
                raise AssertionError("invalid extra roster admitted")
        delegate.assert_not_called()
    require(extra_roster_rejects == 4)

    # Every public wrapper delegates with final own identity and restores state.
    delegated = []
    for name, args, kwargs in (
        ("main", (["--out", "inert-never-used"],), {}),
        ("run_case", (SimpleNamespace(synthetic=True),), {}),
        ("audit", (Path("inert-never-used-field"),), {}),
        ("require_admitted_payload", (b"synthetic-not-a-field", {}), {"admission_sha256": c.LOADED_SHA}),
    ):
        def delegate(*actual, _name=name, _args=args, _kwargs=kwargs, **actual_kwargs):
            require(actual == _args and actual_kwargs == _kwargs)
            require(a.OWN == c.OWN and a.LOADED_SHA == c.LOADED_SHA)
            require(a.validate_descriptor is not originals["validate_descriptor"])
            delegated.append(_name)
            return "inert-delegated"
        with patch.object(a, name, delegate):
            require(getattr(c, name)(*args, **kwargs) == "inert-delegated")
        require(all(getattr(a, key) is value for key, value in originals.items()))
    with patch.object(a, "audit", side_effect=ValueError("inert-delegate-failure")):
        try:
            c.audit(Path("inert-never-used-field"))
        except ValueError as error:
            require(str(error) == "inert-delegate-failure")
        else:
            raise AssertionError("delegate failure suppressed")
    require(all(getattr(a, key) is value for key, value in originals.items()))

    w, written = a.production(), []
    b = w.frozen()
    with c.corrected_context(a), a.context(w, b):
        require(b.OWN == c.OWN and b.LOADED_SHA == c.LOADED_SHA)
        runtime_pins = b.source_pins()
        method_pins = b.source_pins(method={"source_sha256": runtime_pins,
            "input_record": {"path": str(c.OWN.relative_to(ROOT)), "sha256": c.LOADED_SHA}})
        require(runtime_pins == method_pins == saved["source_sha256"] and len(runtime_pins) == 30)
    require(b.OWN == w.FROZEN and b.LOADED_SHA == w.FROZEN_SHA)

    @contextmanager
    def reservation(path):
        yield SimpleNamespace(path=path, owned=lambda: None, write=written.append)

    def prohibited(*_args, **_kwargs):
        raise AssertionError("source-only preflight reached candidate work")

    output = HERE / "inert-never-created-preflight.json"
    require(not output.exists())
    with patch.object(w, "reserve", reservation), patch.object(b.factory, "prepare", prohibited), \
            patch.object(a, "build_inputs", prohibited), patch.object(a, "validate_descriptor", prohibited):
        require(c.main(["--out", str(output)]) == 0)
    require(written == [saved] and not output.exists())
    require(saved["provided"] == {} and len(saved["missing"]) == 6)
    require(saved["complete_joint_resistance"] is None and saved["production_readiness_claimed"] is False)
    require(saved["generalized_residual_tolerance_n_inclusive"] == 1e-5 and not any(saved["release"].values()))
    require(saved["nut_spacer_proposal_included"] is False)
    require(all(getattr(a, key) is value for key, value in originals.items()))
    require(b.OWN == w.FROZEN and b.factory.SCHEMA == b.ORIGINAL_SCHEMA and b.factory.read_inputs is b.ORIGINAL_READ)
    require({name: sha(ROOT / name) for name in pins} == before)
    return {
        "schema": "independent_z180_final_wrapper_correctness_review/v2", "findings": [],
        "reviewer_source_sha256": sha(Path(__file__)), "reviewed_sha256": pins,
        "reused_v1_receipt_sha256": PRIOR_HASHES["receipt.json"],
        "checks": {"source_and_target_pins_before_after": len(pins),
                   "selected_existing_v2_inert_controls_passed": count,
                   "additional_parent_or_unmoved_roster_rejects_before_delegate": extra_roster_rejects,
                   "public_entrypoint_scoped_identity_delegations": delegated,
                   "delegate_failure_propagates_and_restores_hooks": True,
                   "default_preflight_exact_replay_in_memory_without_outputs": True,
                   "runtime_and_method_source_union_exact_saved_30pins": True},
        "limits": ["Frozen v1 numerical/context/guard review reused within unchanged source hashes; no broad old-method rerun.",
                   "Only source definitions, synthetic roster rows, mocked entrypoints, source-pin joins and a no-reference in-memory preflight executed.",
                   "No genuine descriptor/input construction, panel preparation/K/frame/q/field/solve/CAD/BREP/native/browser or actual admission consumption.",
                   "Own final descriptor/input/review/method and parent serial slot remain required; no readiness, resistance, hardware/geometry adoption or physical acceptance follows."],
    }


if __name__ == "__main__":
    receipt = evaluate()
    with (HERE / "receipt.json").open("x") as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"findings": receipt["findings"], "review_sha256": receipt["reviewer_source_sha256"],
                      "receipt_sha256": sha(HERE / "receipt.json"), "checks": receipt["checks"]}))
