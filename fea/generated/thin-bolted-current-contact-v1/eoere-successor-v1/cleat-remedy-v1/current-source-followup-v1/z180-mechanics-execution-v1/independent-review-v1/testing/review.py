"""Inert Z180 adapter testing; no genuine descriptor/input/panel/solve execution."""
from __future__ import annotations

import ast
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
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "bridge.py": "fc95da9c8b81b8153813b6c98895401c4f4b5cf96e61d68973ba417c386917c6",
    "test_bridge.py": "d02c448019ac7bdc0b7b465337ce52a617d18c5e771c2e307d873bcc9e4b38be",
    "source-preflight.json": "4588317f7790a8982ecd89c66c6b47c4d15474567848ce72ac409f389d3ecc97",
    "verification.json": "0028e21509a60bcf8da1628f7839f37f24c7e0244a959949ad765f07ca200050",
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review():
    retained = PACKET.parent / "receiver-seats-v1/fixture-design-v1/catalog-adapter-v1/independent-review-v1/testing/review.py"
    assert sha(retained) == "9fddef5ba3f4c8148eab1ce2858671ef54aceda46b9bb6bae0434353893bd00e"
    utilities = runpy.run_path(str(retained))
    load, require, rejected = (utilities[key] for key in ("load", "require", "rejected"))
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "four target hashes")
    issued = json.loads((PACKET / "verification.json").read_bytes())
    preflight = json.loads((PACKET / "source-preflight.json").read_bytes())
    inherited = issued["inherited_sources_before_after"]
    require(all(sha(ROOT / name) == entry["sha256"] and (ROOT / name).stat().st_size == entry["bytes"] for name, entry in inherited.items()), "inherited method evidence hashes")
    closure = preflight["source_sha256"]
    require(len(closure) == 29 and all(sha(ROOT / name) == digest for name, digest in closure.items()), "twenty-nine source closure pins")
    tests = load(PACKET / "test_bridge.py", "frozen_z180_inert_test_fixture_reused")
    a = tests.a
    parent, exported, data, read = tests.fixture()
    with patch.object(a, "read_ref", side_effect=read):
        require(a.validate_descriptor(exported) is parent and a.require_sources(data)["cached_source_export"] is exported, "unchanged inert source fixture")
    omitted = exported["shafts"][0]["axis_id"]
    exported["shafts"][0] = copy.deepcopy(exported["shafts"][4])
    data["shafts"] = copy.deepcopy(exported["shafts"])
    with patch.object(a, "read_ref", side_effect=read):
        require(a.validate_descriptor(exported) is parent, "duplicate intake observation changed")
        require(a.require_sources(data)["cached_source_export"] is exported, "coherent duplicate source join observation changed")
    duplicate_observation = {"source": "retained test_bridge.fixture() synthetic in-memory structures only",
                             "list_length": len(exported["shafts"]), "unique_axis_ids": len({row["axis_id"] for row in exported["shafts"]}),
                             "omitted_declared_moved_axis": omitted,
                             "declared_moved_axis_count": exported["geometry_delta_proof"]["counts"]["shaft_axes_changed"],
                             "validate_descriptor_accepted": True, "coherent_require_sources_accepted": True}
    factory_path = next(ROOT / name for name in closure if name.endswith("/first_order_factory.py"))
    factory_tree = ast.parse(factory_path.read_bytes())
    validator = next(node for node in factory_tree.body if isinstance(node, ast.FunctionDef) and node.name == "validate_rows")
    uniqueness = next(node for node in validator.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                      and any(isinstance(arg, ast.Constant) and arg.value == "one continuous shaft per unique physical axis" for arg in node.value.args))
    downstream_guard = {"path": str(factory_path.relative_to(ROOT)), "sha256": sha(factory_path), "line": uniqueness.lineno,
                        "source_inspected_not_executed": True,
                        "condition": ast.unparse(uniqueness.value.args[0]),
                        "scope": "The frozen inherited factory separately rejects duplicate shaft axes; duplicate full rows also violate earlier physical-body uniqueness. No factory validation/preparation or genuine force/admission bypass is claimed."}
    require(len(exported["shafts"]) != len({row["axis_id"] for row in exported["shafts"]}), "independent unique-axis predicate")

    descriptor_controls = []
    for label in ("wrong_COM_translation", "changed_unmoved_shaft", "wrong_hardware_length", "historical_response", "missing_source_pin", "declared_count"):
        _parent, source, _data, fixture_read = tests.fixture()
        if label == "wrong_COM_translation":
            source["shafts"][0]["metal_roles"][0]["center_of_mass_xyz_mm"][0] += 1.
        elif label == "changed_unmoved_shaft":
            source["shafts"][4]["point"][2] -= 1.
        elif label == "wrong_hardware_length":
            source["shafts"][0]["source_axis"]["nominal_under_head_length_mm"] = 114.3
        elif label == "historical_response":
            source["q"] = [0.]
        elif label == "missing_source_pin":
            del source["source_sha256"][a.GEOMETRY["path"]]
        else:
            source["geometry_delta_proof"]["counts"]["hardware_role_locations_changed"] = 19
        with patch.object(a, "read_ref", side_effect=fixture_read):
            descriptor_controls.append({"case": label, "rejection": rejected(lambda source=source: a.validate_descriptor(source))})

    source_controls = []
    original_sha = a.sha
    for path in (a.OWN, a.PRODUCTION):
        boundary = Mock(side_effect=AssertionError("changed adapter entered frozen implementation"))
        with patch.object(a, "sha", side_effect=lambda candidate, path=path: "0" * 64 if Path(candidate) == path else original_sha(candidate)), patch.object(a.importlib.util, "spec_from_file_location", boundary):
            message = rejected(a.production)
        require(not boundary.called, "source drift reached import")
        source_controls.append({"path": str(path.relative_to(ROOT)), "rejection": message, "before_import": True})
    for ref in (a.GEOMETRY, a.SOURCE_MANIFEST, a.PARENT_DESCRIPTOR):
        with patch.object(a, "sha", side_effect=lambda candidate, ref=ref: "0" * 64 if Path(candidate) == ROOT / ref["path"] else original_sha(candidate)):
            source_controls.append({"path": ref["path"], "rejection": rejected(lambda ref=ref: a.read_ref(ref))})

    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        # Original tests are inert. Their real deferred-run test rejects an
        # injected missing review before any methods or preparation callbacks.
        with patch.dict(os.environ, {"PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}):
            import pytest
            result_text = io.StringIO()
            with redirect_stdout(result_text), redirect_stderr(result_text):
                test_code = pytest.main(["-q", "-p", "no:cacheprovider", "--confcutdir", str(PACKET),
                                         "--basetemp", str(scratch / "pytest"), str(PACKET / "test_bridge.py")])
        require(test_code == 0 and "15 passed" in result_text.getvalue(), "original fifteen inert tests: " + result_text.getvalue())
        w, b = a.production(), a.production().frozen()
        def prohibited(*_args, **_kwargs):
            raise AssertionError("review source preflight entered candidate work")
        output = scratch / "all-missing-preflight.json"
        with patch.object(b.factory, "prepare", side_effect=prohibited), patch.object(a, "methods", side_effect=prohibited), \
                patch.object(a, "build_inputs", side_effect=prohibited), patch.object(a, "validate_descriptor", side_effect=prohibited):
            require(a.main(["--out", str(output)]) == 0, "one fresh all-missing preflight")
        require(output.read_bytes() == (PACKET / "source-preflight.json").read_bytes(), "fresh source-only preflight byte replay")
        preflight_sha = sha(output)
        output_controls = []
        for kind in ("file", "directory", "dangling_symlink", "existing_symlink"):
            occupied = scratch / (kind + ".json")
            if kind == "file":
                occupied.write_bytes(b"preserved owned output")
            elif kind == "directory":
                occupied.mkdir()
            else:
                occupied.symlink_to(output if kind == "existing_symlink" else scratch / "absent.json")
            boundary = Mock(side_effect=AssertionError("occupied output entered frozen imports"))
            with patch.object(w, "frozen", boundary):
                message = rejected(lambda occupied=occupied: a.main(["--out", str(occupied)]))
            require(not boundary.called and output.read_bytes() == (PACKET / "source-preflight.json").read_bytes(), "occupied guard entered frozen code or overwrote")
            output_controls.append({"kind": kind, "rejection_type": "FileExistsError", "before_frozen_import": True, "rejection": message})
        ref_path = scratch / "inert-ref.json"
        ref_path.write_bytes(b'{"fixture": true}\n')
        good_ref = {"path": str(ref_path.relative_to(ROOT)), "sha256": sha(ref_path)}
        require(a.read_ref(good_ref) == {"fixture": True}, "owned inert source reference")
        ref_controls = []
        for label, ref in (("absolute", {**good_ref, "path": str(ref_path)}),
                           ("digest", {**good_ref, "sha256": "0"*64}),
                           ("extra_field", {**good_ref, "unexpected": True}),
                           ("outside", {**good_ref, "path": "../_testing_outside.json"})):
            ref_controls.append({"case": label, "rejection": rejected(lambda ref=ref: a.read_ref(ref))})
        names = ("OWN", "LOADED_SHA", "GEOMETRY", "SOURCE_MANIFEST", "INPUT_SCHEMA", "REVIEW_SCHEMA", "REVIEW_SUCCESS",
                 "METHOD_SCHEMA", "FIELD_SCHEMA", "STATE_PREFIX", "ADMISSION_SCHEMA", "SUCCESS", "read_ref",
                 "require_current_sources", "load", "read_method", "methods", "source_pins", "compile_function")
        hooks_before = {name: getattr(b, name) for name in names}
        try:
            with a.context(w, b):
                require(b.GEOMETRY == a.GEOMETRY and b.FIELD_SCHEMA == a.FIELD_SCHEMA, "scoped Z180 hooks absent")
                raise RuntimeError("owned inert restoration control")
        except RuntimeError as error:
            require(str(error) == "owned inert restoration control", "unexpected context failure")
        require(all(getattr(b, name) is value for name, value in hooks_before.items()) and not hasattr(b, "z180_original_read_method"), "scoped hooks not restored")

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "four target preservation")
    require(all(sha(ROOT / name) == digest for name, digest in closure.items()) and all(sha(ROOT / name) == entry["sha256"] for name, entry in inherited.items()), "inherited source preservation")
    require(preflight["production_readiness_claimed"] is False and preflight["complete_joint_resistance"] is None and not any(preflight["release"].values()) and len(preflight["missing"]) == 6, "unready claim boundary")
    return {"schema": "eoere_z180_execution_adapter_independent_testing_review/v1",
            "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
            "four_target_sha256_before_after": before, "twenty_nine_source_closure_sha256_before_after": closure,
            "inherited_method_evidence_hash_only_before_after": inherited,
            "original_inert_tests": {"count": 15, "exit_code": test_code, "stdout": result_text.getvalue().strip(), "qualification": "Normal existing dependency definitions imported, including transitive CAD library definitions as explicitly permitted; no candidate CAD/BREP operation or preparation."},
            "one_fresh_all_missing_main_preflight_byte_exact_sha256": preflight_sha,
            "duplicate_moved_axis_inert_intake_observation": duplicate_observation,
            "downstream_unique_axis_factory_guard_source_only_inspection": downstream_guard,
            "additional_descriptor_rejections": descriptor_controls,
            "source_drift_rejections": source_controls, "repository_reference_controls": ref_controls,
            "occupied_output_rejections_before_frozen_import": output_controls,
            "scoped_context_hooks_restored_after_exception": True,
            "findings": [{"severity": "medium", "file": str((PACKET / "bridge.py").relative_to(ROOT)), "line": 134,
                          "title": "Descriptor intake permits duplicate shafts and an omitted declared moved axis",
                          "impact": "validate_descriptor checks 100 rows but never requires 100 unique/exact axis IDs. Replacing one moved shaft by a duplicate unchanged shaft in the retained inert fixture passes descriptor validation and, with coherently joined inert data.shafts, require_sources. The source contract can therefore declare four moves while omitting a declared moved axis. No genuine descriptor/input trial, source preflight with supplied candidate evidence, readiness, preparation or force/admission bypass is claimed: the pinned inherited first_order_factory.validate_rows separately rejects duplicate axes downstream.",
                          "fix": "Before per-shaft validation, require unique axis IDs and exact equality with the parent axis-ID set, and require the declared four moved IDs to occur exactly once. Add descriptor and coherent input-join duplicate/missing-axis negative controls while retaining the downstream factory guard."}],
            "all_sources_and_targets_unchanged": True,
            "scope": "Frozen four-file source adapter only. Retained synthetic fixture, original fifteen inert tests and one fresh default all-missing source preflight, extra source/reference/descriptor/output/context controls. Existing dependencies are imported normally; no CAD/BREP operation occurs. The downstream factory guard is inspected, not executed. Original 491653 arithmetic and 014f panel identity reused within existing evidence; no genuine final descriptor/input/review/method exists or was constructed/consumed.",
            "review_harness_correction": "Reviewer restrictions initially stopped three dependency-loading tests (12 passed), first at NumPy and then before transitive cadquery import from mini_moonboard.__init__. Parent clarified that existing dependency definitions may be imported for the authorized inert replay; the final replay uses normal imports and no package shim. No target failure, candidate preparation or native solve is claimed by those initial harness stops.",
            "excluded": ["genuine descriptor/input construction or candidate source-field consumption", "current panel preparation/K, genuine frame operator/q/actions/admission or solve", "CAD/BREP/native/browser work", "broad mechanical arithmetic or historical acceptance re-audit", "current Z200/100 bolts/66 screws/forces/HOLD, 4in hardware or unadopted Z180 adoption", "spacer inclusion, panel remedies or resistance/physical release", "shared Git/docs/index edits, staging or commit"],
            "production_readiness_claimed": False, "complete_joint_resistance": None,
            "mechanics_or_physical_release": False}


if __name__ == "__main__":
    original_import = builtins.__import__
    dependency_imports = set()

    def tracked_import(name, *args, **kwargs):
        root = name.split(".")[0]
        if root in ("numpy", "scipy", "cadquery", "OCP"):
            dependency_imports.add(root)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=tracked_import):
        receipt = review()
    receipt["existing_dependency_definition_imports_observed"] = sorted(dependency_imports)
    receipt["actual_CAD_BREP_candidate_preparation_or_native_solve_operations_performed"] = False
    destination = OUT / "receipt.json"
    with destination.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "sha256": sha(destination), "findings": len(receipt["findings"])}))
