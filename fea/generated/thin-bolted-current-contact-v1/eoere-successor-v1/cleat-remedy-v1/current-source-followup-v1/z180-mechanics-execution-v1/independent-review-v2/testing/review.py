"""Bounded exact-roster wrapper review; inert interfaces and default preflight."""
from __future__ import annotations

import builtins
import copy
import hashlib
import io
import json
import os
import runpy
import sys
import tempfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
TARGET = PACKET / "review-fix-v2"
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "bridge.py": "dc224c51a46f78433df614ce53b76e2a8f4b1a7ac4c436b7d0d212f784388f55",
    "test_bridge.py": "7139f66d4218510d1eefc7e9d6f2b4827ff673d01c3cdb073c1a2dd9ee3b65a2",
    "source-preflight.json": "2b76796f808dce7805aaf338729571c078f4676f7e589dc626f1ceeeb483c092",
    "verification.json": "97845159bf1c8e59df46ac09ab072df2af2fcc8069b5ed57ff2eaa4e2195aaf5",
}
PRIOR_RECEIPT_SHA = "a4a1f0636cd1931a90f0cd4c83e32afbc7682ac4504e2a0c1ead9f13be80f32e"
PRIOR_HELPER_SHA = "e5558e68391075ceaeb03b0c011d082a01ac6c9f85eb5753b712058a69420ddd"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review():
    utilities_path = PACKET.parent / "receiver-seats-v1/fixture-design-v1/catalog-adapter-v1/independent-review-v1/testing/review.py"
    utilities = runpy.run_path(str(utilities_path))
    load, require, rejected = (utilities[key] for key in ("load", "require", "rejected"))
    own_prior = PACKET / "independent-review-v1/testing"
    require(sha(own_prior / "review.py") == PRIOR_HELPER_SHA and sha(own_prior / "receipt.json") == PRIOR_RECEIPT_SHA, "own frozen v1 review")
    prior = json.loads((own_prior / "receipt.json").read_bytes())
    require(prior["original_inert_tests"]["count"] == 15 and prior["original_inert_tests"]["exit_code"] == 0, "reused original fifteen tests")
    before = {name: sha(TARGET / name) for name in EXPECTED}
    require(before == EXPECTED, "four corrected target hashes")
    issued = json.loads((TARGET / "verification.json").read_bytes())
    preflight = json.loads((TARGET / "source-preflight.json").read_bytes())
    preserved = issued["inherited_source_sha256_before_after"]
    require(all(sha(ROOT / name) == entry["sha256"] and (ROOT / name).stat().st_size == entry["bytes"] for name, entry in preserved.items()), "inherited and prior-review bytes")
    # Hash peer files only as required by issued preservation proof; do not
    # inspect their source or conclusions.
    closure = preflight["source_sha256"]
    require(len(closure) == 30 and all(sha(ROOT / name) == digest for name, digest in closure.items()), "thirty source pins")
    c = load(TARGET / "bridge.py", "corrected_z180_testing_actual")
    fixture_module = load(PACKET / "test_bridge.py", "frozen_z180_fixture_reused_v2")
    a = c.original()
    controls = []
    for kind in ("duplicate_unchanged", "unknown_unchanged", "parent_missing", "moved_duplicate", "moved_unknown", "moved_short"):
        parent, exported, data, fixture_read = fixture_module.fixture()
        authority = a.manifest()
        if kind == "duplicate_unchanged":
            exported["shafts"][5] = copy.deepcopy(exported["shafts"][4])
        elif kind == "unknown_unchanged":
            exported["shafts"][4]["axis_id"] = "unknown_unchanged_axis"
        elif kind == "parent_missing":
            parent["shafts"].pop()
        elif kind == "moved_duplicate":
            authority["declared_changes"]["axis_ids"][1] = authority["declared_changes"]["axis_ids"][0]
        elif kind == "moved_unknown":
            authority["declared_changes"]["axis_ids"][0] = "unknown_declared_move"
        else:
            authority["declared_changes"]["axis_ids"].pop()
        data["shafts"] = copy.deepcopy(exported["shafts"])
        delegate = Mock(side_effect=AssertionError("invalid roster entered original descriptor validator"))
        with patch.object(a, "read_ref", side_effect=fixture_read), patch.object(a, "manifest", return_value=authority), \
                patch.object(a, "validate_descriptor", delegate), c.corrected_context(a):
            descriptor_error = rejected(lambda exported=exported: a.validate_descriptor(exported))
            source_error = rejected(lambda data=data: a.require_sources(data))
        require(not delegate.called and descriptor_error == source_error == "exact unique 100 authenticated parent axes including all four moved axes required", "roster rejection ordering")
        controls.append({"case": kind, "descriptor_and_coherent_source_join_rejected_before_delegate": True})
    parent, exported, data, fixture_read = fixture_module.fixture()
    exported["shafts"] = list(reversed(exported["shafts"]))
    data["shafts"] = copy.deepcopy(exported["shafts"])
    with patch.object(a, "read_ref", side_effect=fixture_read), c.corrected_context(a):
        require(a.validate_descriptor(exported) is parent and a.require_sources(data)["cached_source_export"] is exported, "complete reordered roster positive")

    hooks = ("OWN", "LOADED_SHA", "validate_descriptor", "source_pins")
    hooks_before = {name: getattr(a, name) for name in hooks}
    entered = []

    def interrupted_main(_argv):
        require(a.OWN == c.OWN and a.LOADED_SHA == c.LOADED_SHA, "corrected entrypoint identity absent")
        entered.append("corrected_scoped_main")
        raise RuntimeError("inert interrupted main")

    with patch.object(a, "main", side_effect=interrupted_main):
        try:
            c.main([])
        except RuntimeError as error:
            require(str(error) == "inert interrupted main", "wrong delegation failure")
        else:
            raise AssertionError("interrupted delegation did not reject")
    require(entered == ["corrected_scoped_main"] and all(getattr(a, name) is value for name, value in hooks_before.items()), "entrypoint context restoration")
    drift_controls = []
    original_read = Path.read_bytes
    for path in (c.OWN, c.FROZEN):
        boundary = Mock(side_effect=AssertionError("changed source entered main"))
        with patch.object(Path, "read_bytes", lambda candidate, path=path: b"in-memory changed bytes" if candidate == path else original_read(candidate)), patch.object(a, "main", boundary):
            message = rejected(lambda: c.main([]))
        require(not boundary.called, "source drift reached delegated main")
        drift_controls.append({"source": str(path.relative_to(ROOT)), "rejection": message, "before_main": True})

    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        with patch.dict(os.environ, {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}):
            import pytest
            test_stdout = io.StringIO()
            with redirect_stdout(test_stdout), redirect_stderr(test_stdout):
                code = pytest.main(["-q", "-p", "no:cacheprovider", "--import-mode=importlib", "--confcutdir", str(TARGET),
                                    "--basetemp", str(scratch / "pytest"), str(TARGET / "test_bridge.py")])
        require(code == 0 and "15 passed" in test_stdout.getvalue(), "new fifteen inert tests: " + test_stdout.getvalue())
        w, b = a.production(), a.production().frozen()
        runtime_pins = w.runtime_source_pins
        expected = {str(c.OWN.relative_to(ROOT)): c.LOADED_SHA, str(c.FROZEN.relative_to(ROOT)): c.FROZEN_SHA}
        pin_events = []

        def observed_runtime(bridge, additions=None, *, method=None):
            require(all(additions[name] == digest for name, digest in expected.items()), "own and original pins missing before genuine runtime verification")
            pin_events.append({"both_identities_present_before_runtime_verification": True, "synthetic_method_source_pin_shape": method is not None})
            return runtime_pins(bridge, additions, method=method)

        with c.corrected_context(a), a.context(w, b), patch.object(w, "runtime_source_pins", side_effect=observed_runtime):
            pins = b.source_pins()
            synthetic = {"source_sha256": pins, "input_record": {"path": str(c.OWN.relative_to(ROOT)), "sha256": c.LOADED_SHA}}
            method_pins = b.source_pins(method=synthetic)
            require(all(pins[name] == method_pins[name] == digest for name, digest in expected.items()), "runtime identity pin preservation")
        require(len(pin_events) == 2 and all(getattr(a, name) is value for name, value in hooks_before.items()), "source-pin context restoration")
        output = scratch / "default-source-preflight.json"
        def prohibited(*_args, **_kwargs):
            raise AssertionError("default preflight entered candidate work")
        with patch.object(b.factory, "prepare", side_effect=prohibited), patch.object(a, "build_inputs", side_effect=prohibited), \
                patch.object(a, "methods", side_effect=prohibited), patch.object(a, "validate_descriptor", side_effect=prohibited):
            require(c.main(["--out", str(output)]) == 0, "one fresh corrected default preflight")
        require(output.read_bytes() == (TARGET / "source-preflight.json").read_bytes(), "default preflight exact byte replay")
        preflight_sha = sha(output)

    require(before == {name: sha(TARGET / name) for name in EXPECTED}, "four corrected target preservation")
    require(all(sha(ROOT / name) == entry["sha256"] for name, entry in preserved.items()) and all(sha(ROOT / name) == digest for name, digest in closure.items()), "inherited/closure preservation")
    require(preflight["provided"] == {} and len(preflight["missing"]) == 6 and preflight["production_readiness_claimed"] is False and preflight["complete_joint_resistance"] is None and not any(preflight["release"].values()), "production unready boundary")
    return {"schema": "eoere_z180_roster_wrapper_independent_testing_review/v2",
            "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
            "four_corrected_target_sha256_before_after": before,
            "reused_v1_testing_helper_sha256": PRIOR_HELPER_SHA, "reused_v1_testing_receipt_sha256": PRIOR_RECEIPT_SHA,
            "thirty_source_closure_sha256_before_after": closure,
            "preserved_source_and_prior_review_hash_only_before_after": preserved,
            "new_inert_tests": {"count": 15, "exit_code": code, "stdout": test_stdout.getvalue().strip()},
            "original_fifteen_inert_tests_and_unaffected_v1_controls_reused_not_rerun": True,
            "added_invalid_parent_move_and_unchanged_roster_controls": controls,
            "reordered_complete_roster_positive_passed": True,
            "real_main_delegation_context_restored_after_exception": True,
            "original_and_corrected_self_source_drift_rejected_before_main": drift_controls,
            "self_pin_ordering_at_genuine_runtime_source_interface": pin_events,
            "one_fresh_default_preflight_byte_exact_sha256": preflight_sha,
            "v1_duplicate_roster_intake_finding_closed": True,
            "all_sources_and_targets_unchanged": True, "findings": [],
            "scope": "Final 3508-byte source wrapper and four issued targets. Existing dependency definitions may import normally. New fifteen inert tests, six additional roster/declaration fixtures through actual corrected descriptor/source interfaces, exact complete-roster positive, delegation restoration, cached self-source drift, original/corrected pins before genuine runtime-source verification, and one fresh default all-missing preflight. The synthetic method dictionary is only a source-pin API shape, not a genuine method/input trial. V1 source/output/review/authentication/numerical tolerance controls reused unchanged; no candidate descriptor, input, panel, operator, response or admission consumed.",
            "excluded": ["genuine candidate descriptor/input/review/method construction or trial", "CAD/BREP geometry queries/construction/Booleans/tessellation", "panel preparation/K, frame K/q/actions/solve or genuine field/admission consumption", "numerical law or tolerance changes, force transfer or resistance acceptance", "current Z200/100 bolts/66 screws/4in hardware/HOLD or unadopted Z180 adoption", "spacer inclusion or panel remedies", "docs/Git/shared/frozen-file edits"],
            "production_readiness_claimed": False, "complete_joint_resistance": None, "mechanics_or_physical_release": False}


if __name__ == "__main__":
    original_import = builtins.__import__
    dependencies = set()

    def tracked_import(name, *args, **kwargs):
        root = name.split(".")[0]
        if root in ("numpy", "scipy", "cadquery", "OCP"):
            dependencies.add(root)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=tracked_import):
        receipt = review()
    receipt["existing_dependency_definition_imports_observed"] = sorted(dependencies)
    receipt["actual_CAD_BREP_candidate_preparation_or_native_solve_operations_performed"] = False
    destination = OUT / "receipt.json"
    with destination.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "sha256": sha(destination), "findings": len(receipt["findings"])}))
