"""Supported Z180 display-v2 source/CLI testing; no native or browser work."""
from __future__ import annotations

import builtins
import copy
import importlib.util
import io
import json
import runpy
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
V1 = PACKET / "independent-review-v1/testing"
V1_HELPER_SHA = "cdc8a2f93337097adac147ea17c211daa7e6f0d8cce0dab70936e03cab2de290"
V1_RECEIPT_SHA = "3c09760dc8f920c5932e58e2ed543efe087c6bb2e712c093156401528adbce11"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReservedBeforeNative(Exception):
    """Mock boundary after exclusive output reservation and before native import."""


def review():
    helper = load(V1 / "review.py", "frozen_z180_v1_testing_utilities")
    sha, read, require, rejected = helper.sha, helper.read, helper.require, helper.rejected
    require(sha(V1 / "review.py") == V1_HELPER_SHA and sha(V1 / "receipt.json") == V1_RECEIPT_SHA, "frozen own v1 evidence differs")
    manifest_path = PACKET / "review-target-v2.json"
    manifest = read(manifest_path)
    before = {name: sha(ROOT / name) for name in manifest["files"]}
    require(before == manifest["files"] and len(before) == 15, "all fifteen frozen target hashes required")
    manifest_hash = sha(manifest_path)
    wrapper = load(PACKET / "export-v2.py", "supported_z180_display_v2_testing")
    actual = wrapper.verify_current()
    issued = read(PACKET / "source-verification-v2.json")
    require(actual == issued and actual["passed"] is True and actual["parent_review_consumed_native_digest_joined"] is True, "actual source verification differs")
    require(actual["native_geometry_or_mechanics_executed"] is False and all(value is False for value in actual["release"].values()), "verification scope")
    require(len(actual["source_sha256"]) == 17 and all(sha(ROOT / name) == digest for name, digest in actual["source_sha256"].items()), "seventeen source pins")
    old = read(V1 / "receipt.json")
    mesh = read(PACKET / "mesh-check-v1.json")
    require(sha(PACKET / "mesh-check-v1.json") == old["fresh_actual_Three_check"]["sha256"] == sha(V1 / "actual-mesh-check-v1.json"), "exact previous actual Three proof required")
    require(mesh["passed"] is True and all(sha(ROOT / name) == digest for name, digest in mesh["source_sha256"].items()), "reused Three inputs differ")
    unchanged_paths = ["site/index.html", "site/eoere-lower-cleat-z180-overlay.mjs", "site/eoere-lower-cleat-z180-scene.json.gz", "scripts/check_eoere_lower_cleat_z180.mjs"]
    require(all(before[name] == old["target_sha256_before_after"][name] for name in unchanged_paths), "old routing/mesh coverage no longer applicable")

    guard_path = PACKET / "parent-readiness-v2.json"
    parent_path = PACKET / "parent-readiness.json"
    input_path = PACKET / "inputs.json"
    guard, parent, inp = read(guard_path), read(parent_path), read(input_path)
    original_read = wrapper.read

    def virtual_guard(g, p, i):
        def overridden(path):
            values = {guard_path: g, parent_path: p, input_path: i}
            return copy.deepcopy(values[Path(path)]) if Path(path) in values else original_read(path)
        with patch.object(wrapper, "read", side_effect=overridden):
            return wrapper.guarded_original()

    gate_controls = []
    for key, value in (("schema", "other"), ("exporter_sha256", "0" * 64), ("only_four_saved_BREP_display_tessellations", False), ("native_mechanics_or_full_frame_CAD_authorized", True), ("geometry_adoption_authorized_by_this_file", True), ("reviewed_native_result_sha256", "0" * 64)):
        changed = copy.deepcopy(guard)
        changed[key] = value
        gate_controls.append({"name": "v2_" + key, "rejection": rejected(lambda changed=changed: virtual_guard(changed, parent, inp))})
    changed = copy.deepcopy(parent)
    changed["reviewed_native_result_sha256"] = "0" * 64
    gate_controls.append({"name": "v1_parent_reviewed_result_join", "rejection": rejected(lambda: virtual_guard(guard, changed, inp))})
    changed_input = copy.deepcopy(inp)
    changed_input["source_sha256"][inp["native_result"]] = "0" * 64
    gate_controls.append({"name": "consumed_input_digest_join", "rejection": rejected(lambda: virtual_guard(guard, parent, changed_input))})
    for source in list(guard["source_sha256"]):
        changed_guard = copy.deepcopy(guard)
        changed_guard["source_sha256"][source] = "0" * 64
        gate_controls.append({"name": "frozen_source_pin_" + Path(source).name, "rejection": rejected(lambda changed_guard=changed_guard: virtual_guard(changed_guard, parent, inp))})
    original_sha = wrapper.sha
    for name, path in (("frozen_exporter_bytes", PACKET / "export.py"), ("consumed_native_result_bytes", ROOT / inp["native_result"])):
        with patch.object(wrapper, "sha", side_effect=lambda candidate, path=path: "0" * 64 if Path(candidate) == path else original_sha(candidate)):
            gate_controls.append({"name": name, "rejection": rejected(wrapper.guarded_original)})

    report_path = PACKET / "runs-v1/export01/export-result.json"
    report = read(report_path)
    report_controls = []
    for key, value in (("schema", "other"), ("status", "other"), ("native_cuts_Boolean_or_mechanics", True), ("saved_response_transferred", True)):
        changed = copy.deepcopy(report)
        changed[key] = value
        with patch.object(wrapper, "read", side_effect=lambda path, changed=changed: copy.deepcopy(changed) if Path(path) == report_path else original_read(path)):
            report_controls.append({"name": "report_" + key, "rejection": rejected(wrapper.verify_current)})
    changed = copy.deepcopy(report)
    changed["release"]["geometry_adopted"] = True
    with patch.object(wrapper, "read", side_effect=lambda path: copy.deepcopy(changed) if Path(path) == report_path else original_read(path)):
        report_controls.append({"name": "report_release", "rejection": rejected(wrapper.verify_current)})
    for name in ("layout.json", "scene.json.gz"):
        for key, value in (("path", "other"), ("sha256", "0" * 64), ("bytes", -1)):
            changed = copy.deepcopy(report)
            changed["output"][name][key] = value
            with patch.object(wrapper, "read", side_effect=lambda path, changed=changed: copy.deepcopy(changed) if Path(path) == report_path else original_read(path)):
                report_controls.append({"name": name + "_" + key, "rejection": rejected(wrapper.verify_current)})
    changed = copy.deepcopy(report)
    changed["source_sha256"][inp["current_geometry"]] = "0" * 64
    with patch.object(wrapper, "read", side_effect=lambda path: copy.deepcopy(changed) if Path(path) == report_path else original_read(path)):
        report_controls.append({"name": "report_source_hash", "rejection": rejected(wrapper.verify_current)})
    layout_path = PACKET / "runs-v1/export01/layout.json"
    changed_layout = read(layout_path)
    changed_layout["proposed_axes"][0]["point_xyz_mm"][2] = 181
    with patch.object(wrapper, "read", side_effect=lambda path: copy.deepcopy(changed_layout) if Path(path) == layout_path else original_read(path)):
        report_controls.append({"name": "layout_descriptor_semantics", "rejection": rejected(wrapper.verify_current)})

    cli_controls = []
    with tempfile.TemporaryDirectory(prefix="review-scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        fresh_receipt = scratch / "fresh-verification.json"
        frozen_receipt_path = PACKET / "source-verification-v2.json"
        original_open = Path.open

        def redirect_output(path, *args, **kwargs):
            return original_open(fresh_receipt if path == frozen_receipt_path and args and args[0] == "x" else path, *args, **kwargs)

        def cli(arguments):
            with patch.object(sys, "argv", [str(PACKET / "export-v2.py"), *arguments]), redirect_stdout(io.StringIO()):
                return runpy.run_path(str(PACKET / "export-v2.py"), run_name="__main__")

        with patch.object(Path, "open", redirect_output):
            cli(["--verify-only"])
            require(fresh_receipt.read_bytes() == frozen_receipt_path.read_bytes(), "real verify-only CLI replay differs")
            cli_controls.append({"name": "actual_verify_only_cli_redirected_to_owned_fresh_output", "passed": True})
            digest = sha(fresh_receipt)
            cli_controls.append({"name": "exclusive_verify_only_output_reuse", "rejection": rejected(lambda: cli(["--verify-only"]))})
            require(sha(fresh_receipt) == digest, "existing review output changed")
        for args in (["--unsupported"], ["--verify-only", "extra"], ["--outdir", str(scratch / "outside")]):
            cli_controls.append({"name": "unsupported_cli_" + args[0], "rejection": rejected(lambda args=args: cli(args))})
        cli_controls.append({"name": "actual_fixed_destination_export_rejects_existing_frozen_run", "rejection": rejected(lambda: cli([]))})
        require(not (scratch / "outside").exists(), "unsupported output created")

        original = wrapper.guarded_original()
        values = original.prepare()
        with patch.object(original, "prepare", return_value=values), patch.object(original, "HERE", scratch):
            runs = scratch / "runs-v1"
            runs.mkdir()
            out = runs / "export01"
            out.symlink_to(runs / "absent")
            cli_controls.append({"name": "fixed_export_dangling_output", "rejection": rejected(original.main)})
            require(out.is_symlink() and not (runs / "absent").exists(), "dangling output followed")
            out.unlink()
            out.write_bytes(b"existing output")
            cli_controls.append({"name": "fixed_export_existing_file", "rejection": rejected(original.main)})
            require(out.read_bytes() == b"existing output", "existing file changed")
            out.unlink()

            def reserve(path, *args, **kwargs):
                original_mkdir(path, *args, **kwargs)
                if path == out:
                    raise ReservedBeforeNative

            original_mkdir = Path.mkdir
            with patch.object(Path, "mkdir", reserve):
                try:
                    original.main()
                except ReservedBeforeNative:
                    pass
                else:
                    raise AssertionError("reservation sentinel not reached")
            require(out.is_dir(), "exclusive fresh directory not reserved")
            cli_controls.append({"name": "fresh_export_reserved_before_native_sentinel", "passed": True})
            cli_controls.append({"name": "reserved_directory_cannot_be_reused", "rejection": rejected(original.main)})

        alias_root = scratch / "alias-root"
        alias_root.mkdir()
        target_root = scratch / "alias-target"
        target_root.mkdir()
        (alias_root / "runs-v1").symlink_to(target_root, target_is_directory=True)
        with patch.object(original, "prepare", return_value=values), patch.object(original, "HERE", alias_root):
            cli_controls.append({"name": "fixed_export_aliased_parent", "rejection": rejected(original.main)})
        require(not (target_root / "export01").exists(), "aliased output created")

    browser_text = (ROOT / manifest["supported_browser_checker"]).read_text()
    require("getAttribute('disabled')" in browser_text and "#part-visibility').isDisabled()" not in browser_text, "fieldset assertion fix")
    require("schema: 'eoere_lower_cleat_z180_browser_check/v2'" in browser_text, "browser v2 identity")
    require(before == {name: sha(ROOT / name) for name in before} and sha(manifest_path) == manifest_hash, "frozen fifteen targets changed")
    require(sha(V1 / "review.py") == V1_HELPER_SHA and sha(V1 / "receipt.json") == V1_RECEIPT_SHA, "own v1 evidence changed")
    require(all(sha(ROOT / name) == digest for name, digest in actual["source_sha256"].items()), "verification inputs changed")
    return {
        "schema": "eoere_lower_cleat_z180_supported_v2_independent_testing_review/v1",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "review_target_manifest": {"path": str(manifest_path.relative_to(ROOT)), "sha256": manifest_hash},
        "all15_target_sha256_before_after": before,
        "actual_source_verification_exact_replay": True,
        "verified_source_pins": len(actual["source_sha256"]),
        "readiness_and_consumed_result_controls": gate_controls,
        "saved_report_and_output_controls": report_controls,
        "cli_and_output_preservation_controls": cli_controls,
        "v1_finding_closed": "Both original and supported parent readiness digests must match the consumed input pin and actual result bytes before frozen prepare/audit or native display work.",
        "reused_v1_testing": {"helper_sha256": V1_HELPER_SHA, "receipt_sha256": V1_RECEIPT_SHA, "actual_Three_proof_sha256": sha(PACKET / "mesh-check-v1.json"), "actual_Three_rerun": False, "old_validator_controls": 42, "early_loader_controls": 5, "historical_dispatches": 14, "toggle_routes": 8},
        "browser_helper_review": {"source_sha256": sha(ROOT / manifest["supported_browser_checker"]), "fieldset_disabled_attribute_assertion": True, "actual_browser_execution": False, "status_at_review": manifest["browser_check_status"]},
        "findings": [],
        "sources_unchanged_before_after": True,
        "mechanics_or_physical_release": False,
        "scope": "Actual stdlib verify_current and owned redirected CLI byte replay; source hashes; in-memory readiness/result/output tampering; fixed-destination output guards and reservation sentinel. Existing saved receiver audit and unchanged v1 actual Three/routing proofs reused, not independently re-executed as native or mesh work.",
        "excluded": ["native/CAD imports", "BREP import/query/reconstruction/tessellation", "Three checker rerun", "browser launch/screenshots", "mechanics/FEA/frame/global solve", "field admission or strength acceptance", "target/shared edits"],
    }


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP"):
            native_attempts.append(name)
            raise AssertionError("forbidden native import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    if native_attempts:
        raise AssertionError("native import attempted")
    receipt["native_import_attempts"] = native_attempts
    output = OUT / "receipt.json"
    with output.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(output.relative_to(ROOT)), "sha256": load(V1 / "review.py", "v1_review_hash_utility").sha(output), "findings": len(receipt["findings"])}))
