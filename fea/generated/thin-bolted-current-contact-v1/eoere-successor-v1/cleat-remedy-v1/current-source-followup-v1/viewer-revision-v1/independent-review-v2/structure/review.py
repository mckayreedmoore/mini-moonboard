"""Bounded source/mock review of supported Z180 display entrypoints v2."""
from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
MANIFEST_SHA = "f2a2548a638f152306b9279b8498ac226ba3b4589b9ebd8725b09743bf69bd37"
V1_REVIEW = {
    "independent-review-v1/structure/review.py": "93016dfcfd4621de1e8eac11330d146c99025b4eb5fb3fde113c70a895f854a5",
    "independent-review-v1/structure/receipt.json": "05302415ccfaac229c1c115891d57d8c425466a89fd485444e0a5990fcf2a78c",
}


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_value_error(function, message):
    try:
        function()
    except ValueError as error:
        require(str(error) == message or str(error).startswith(message), "unexpected gate failure: " + str(error))
    else:
        raise AssertionError("gate accepted a synthetic invalid input")


def review():
    for name, digest in V1_REVIEW.items():
        require(sha(PACKET / name) == digest, "frozen v1 review changed")
    common = load(PACKET / "independent-review-v1/structure/review.py", "frozen_z180_v1_structure_helpers")
    require(not common.native_modules(), "native modules present")
    manifest_path = PACKET / "review-target-v2.json"
    require(sha(manifest_path) == MANIFEST_SHA, "v2 review manifest changed")
    manifest = common.read(manifest_path)
    prior = common.read(PACKET / "independent-review-v1/structure/receipt.json")
    inp = common.read(PACKET / "inputs.json")
    issued = common.read(PACKET / "source-verification-v2.json")
    export = common.read(PACKET / "runs-v1/export01/export-result.json")
    native = common.read(ROOT / inp["native_result"])
    mesh = common.read(PACKET / "mesh-check-v1.json")
    require(manifest["schema"] == "eoere_lower_cleat_z180_source_review_target/v2" and len(manifest["files"]) == 15, "target scope differs")
    pins = common.union(manifest["files"], prior["frozen_target_sha256"], inp["source_sha256"], issued["source_sha256"],
                        export["source_sha256"], native["source_sha256"], mesh["source_sha256"],
                        issued["saved_receiver_audit"]["export_sha256"],
                        {row["path"]: row["sha256"] for row in issued["original_outputs"].values()},
                        prior["provenance"]["current_numerical_records_retained_sha256"],
                        {str((PACKET / name).relative_to(ROOT)): digest for name, digest in V1_REVIEW.items()},
                        {str(manifest_path.relative_to(ROOT)): MANIFEST_SHA,
                         prior["target_manifest"]["path"]: prior["target_manifest"]["sha256"]})
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins, "target/source/output/retention hash mismatch")
    contexts = {name: sha(ROOT / name) for name in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")}
    wrapper = load(PACKET / "export-v2.py", "structure_z180_supported_export_v2")
    one, two = wrapper.guarded_original(), wrapper.guarded_original()
    require(one is not two and one.prepare is not two.prepare, "private adapter state shared")
    require(Path(one.main.__code__.co_filename) == PACKET / "export.py" and Path(one.verify.__code__.co_filename) == PACKET / "export.py", "original export/output code replaced")
    require(one.OWN == PACKET / "export.py" and wrapper.OWN == PACKET / "export-v2.py", "original/wrapper provenance relabeled")
    with patch.object(platform, "python_version", return_value=inp["runtime"]["python"]), patch.object(
        importlib.metadata, "version", side_effect=lambda name: inp["runtime"][name]
    ):
        observed = wrapper.verify_current()
    require(observed == issued and len(observed["source_sha256"]) == 17, "verify-only result differs from issued source verification")
    require(observed["original_export_sha256"] == sha(PACKET / "runs-v1/export01/export-result.json")
            and observed["original_outputs"] == export["output"], "issued export/outputs relabeled")
    require(observed["native_geometry_or_mechanics_executed"] is False and observed["parent_review_consumed_native_digest_joined"] is True, "supported verification claims differ")
    require(all(value is False for value in observed["release"].values()), "release differs")
    require(observed["saved_receiver_audit"] == export["saved_receiver_audit"], "saved observation audit changed")

    actual_read = wrapper.read
    guard_controls = []
    for filename, key, value, error_message in (
        ("parent-readiness.json", "reviewed_native_result_sha256", "0" * 64, "parent review and consumed native-result digest differ"),
        ("parent-readiness-v2.json", "reviewed_native_result_sha256", "0" * 64, "parent review and consumed native-result digest differ"),
        ("parent-readiness-v2.json", "exporter_sha256", "0" * 64, "source-bound v2 parent readiness required"),
        ("parent-readiness-v2.json", "only_four_saved_BREP_display_tessellations", False, "source-bound v2 parent readiness required"),
        ("parent-readiness-v2.json", "native_mechanics_or_full_frame_CAD_authorized", True, "source-bound v2 parent readiness required"),
        ("parent-readiness-v2.json", "geometry_adoption_authorized_by_this_file", True, "source-bound v2 parent readiness required"),
    ):
        def controlled_read(path, filename=filename, key=key, value=value):
            result = actual_read(path)
            if Path(path) == PACKET / filename:
                result = copy.deepcopy(result)
                result[key] = value
            return result
        with patch.object(wrapper, "read", controlled_read):
            expect_value_error(wrapper.guarded_original, error_message)
        guard_controls.append(filename + ":" + key)
    native_path = ROOT / inp["native_result"]
    with patch.object(wrapper, "sha", side_effect=lambda path: "0" * 64 if Path(path) == native_path else sha(Path(path))):
        expect_value_error(wrapper.guarded_original, "parent review and consumed native-result digest differ")
    guard_controls.append("consumed_native_result_bytes")

    # Exercise the added report/output gates without another native import.
    output_controls = []
    def native_free_original():
        original = wrapper.guarded_original()
        original.prepare = lambda: (inp, dict(issued["source_sha256"]), issued["runtime"],
                                    common.read(PACKET / "runs-v1/export01/layout.json"), {}, issued["saved_receiver_audit"])
        return original
    original_factory = native_free_original()
    for key, value, expected in (
        ("status", "ADOPTED", "original display scope differs"),
        ("saved_response_transferred", True, "original display scope differs"),
        ("scene_hash", "0" * 64, "original output binding differs"),
        ("scene_path", "../scene.json.gz", "original output binding differs"),
    ):
        def report_control(path, key=key, value=value):
            result = actual_read(path)
            if Path(path) == PACKET / "runs-v1/export01/export-result.json":
                result = copy.deepcopy(result)
                if key == "scene_hash":
                    result["output"]["scene.json.gz"]["sha256"] = value
                elif key == "scene_path":
                    result["output"]["scene.json.gz"]["path"] = value
                else:
                    result[key] = value
            return result
        with patch.object(wrapper, "guarded_original", return_value=original_factory), patch.object(wrapper, "read", report_control):
            expect_value_error(wrapper.verify_current, expected)
        output_controls.append(key)
    require(not common.native_modules(), "native module imported by source/mock checks")
    tree = ast.parse((PACKET / "export-v2.py").read_bytes())
    require(not any("cadquery" in ast.unparse(node) or "OCP" in ast.unparse(node) for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))), "wrapper native import")
    code = (PACKET / "export-v2.py").read_text()
    require('sys.argv[1:] == ["--verify-only"]' in code and 'elif not sys.argv[1:]' in code and '.open("x")' in code, "CLI support/exclusive verification issuance differs")
    browser = (ROOT / "scripts/check_eoere_lower_cleat_z180_browser_v2.cjs").read_text()
    require("getAttribute('disabled')" in browser and "eoere_lower_cleat_z180_browser_check/v2" in browser, "browser v2 disabled-fieldset/source identity differs")
    require("Current six-case results remain bound to Z200" in browser and "mechanics_or_physical_release: false" in browser and "page_context_code_evaluation: false" in browser, "browser claim boundaries differ")
    require("scripts/check_eoere_lower_cleat_z180_browser_v2.cjs" in browser and "{flag: 'wx'}" in browser, "browser source/output ownership differs")
    require({name: sha(ROOT / name) for name in pins} == before, "frozen evidence changed during review")
    require({name: sha(ROOT / name) for name in contexts} == contexts, "maintained context drifted during review")
    own_ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(own_ruff.returncode == 0, "own Ruff failed: " + own_ruff.stdout + own_ruff.stderr)
    target_ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--output-format", "json", str(PACKET / "export-v2.py")], cwd=ROOT, capture_output=True, text=True, check=False)
    lint = json.loads(target_ruff.stdout)
    require(target_ruff.returncode == 1 and len(lint) == 2 and all(row["code"] == "RUF059" and row["location"]["row"] == 71 for row in lint), "target Ruff differs from explicit frozen waiver")
    return {
        "schema": "eoere_z180_viewer_v2_architecture_review/v1", "review_helper_sha256": sha(OWN),
        "target_manifest": {"path": str(manifest_path.relative_to(ROOT)), "sha256": MANIFEST_SHA},
        "frozen_target_sha256": manifest["files"], "retained_v1_review_sha256": V1_REVIEW,
        "context_sha256": contexts, "findings": [],
        "source_integrity": {"frozen_targets": 15, "verified_source_output_retention_union": len(pins), "supported_verification_source_pins": 17, "unchanged_before_after": True, "all_original_geometry_mesh_layout_and_review_bytes_preserved": True},
        "supported_guard": {"frozen_v1_private_module_reused": True, "parent_v1_and_v2_digest_join_to_consumed_native_result": True, "rejected_synthetic_controls": guard_controls, "rejected_output_controls": output_controls, "verify_current_matches_issued_verification": True, "native_geometry_or_mechanics_executed": False},
        "ownership_and_scope": {"fixed_export01_exclusive_output_inherited_from_v1": True, "verification_receipt_exclusively_issued": True, "future_verification_function_is_read_only": True, "v1_runtime_and_native_display_methods_reused": True, "parent_owns_native_serialization_and_browser": True, "supported_browser_v2_uses_fieldset_disabled_attribute": True, "prior_browser_helper_and_failed_attempts_not_modified_or_pruned": True, "current_Z200_authority_and_saved_response_bindings_preserved": True, "no_panel_remedy_or_acceptance_transfer": True, "all_release_flags_false": True},
        "ruff": {"own_command": ".venv/bin/ruff check " + str(OWN.relative_to(ROOT)), "own_exit_code": own_ruff.returncode, "own_output": own_ruff.stdout.strip(), "frozen_target_waiver": {"explicit_parent_waiver": True, "code": "RUF059", "line": 71, "unused_tuple_locals": ["inp", "bodies"], "diagnostics": len(lint), "other_diagnostics": 0}},
        "limits": ["Source-only reads/hashes, saved-observation replay and inert mocks; no CAD/native/BREP/tessellation/mechanics/browser execution.", "Runtime metadata was mocked to pinned versions for the pure verification replay; no runtime qualification.", "Browser v2 is parent-owned and was inspected as source only. No browser pass is asserted by this receipt.", "Prior v1 review remains frozen and is reused within its original limits. Current numerical records were hashed only; no changed-case actions or joint resistance were evaluated.", "No source/shared/document/model changes, deletion, staging, commit or publication; reviewed unadopted geometry provides no physical release."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    receipt = review()
    path = OWN.with_name("receipt.json")
    if args.write:
        with path.open("x") as stream:
            stream.write(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n")
        print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": 0}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
