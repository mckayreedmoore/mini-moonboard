"""V4 CLI sequencing and fixture reproducibility; reuse frozen arithmetic proof."""
from __future__ import annotations

import ast
import builtins
import copy
import hashlib
import io
import json
import os
import runpy
import subprocess
import sys
import tempfile
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from types import FunctionType, SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
OUT = OWN.parent
PACKET = OUT.parent.parent
FIXTURE = PACKET.parent
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
EXPECTED = {
    "verify-v4.py": "7d12b93a566807bdb6ea855f15339bfd11dbc11b7ff12c51e098b25d3d8288b3",
    "verification-v4.json": "d493675b10ed82518371ef23089850114a59025b96007b9f12e50ec207a6367f",
    "controls01/publication-file-inventory-v4.json": "6d35166082919605b1d61684c212e6ff0d5f07620a38b07538dfe4b5f5d438b5",
}
PRIOR_HELPER_SHA = "5c9d70484e4a69a1f5e5390bc62aff31804229addb69f210226f8a71efbf0489"
PRIOR_RECEIPT_SHA = "54ed621a699e73361be8557f4d58fab0442b9700b73cd692452e376bc82ad9e8"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review():
    prior_path = PACKET / "independent-review-v3/testing/review.py"
    prior_receipt = PACKET / "independent-review-v3/testing/receipt.json"
    assert sha(prior_path) == PRIOR_HELPER_SHA and sha(prior_receipt) == PRIOR_RECEIPT_SHA
    utilities = runpy.run_path(str(PACKET / "independent-review-v2/testing/review.py"))
    load = utilities["load"]
    v1 = load(PACKET / "independent-review-v1/testing/review.py", "retained_v1_testing_utilities_v4")
    require, rejected = v1.require, v1.rejected
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "v4 target hashes")
    issued = json.loads((PACKET / "verification-v4.json").read_bytes())
    prior_evidence = json.loads(prior_receipt.read_bytes())
    inventory = json.loads((PACKET / "controls01/publication-file-inventory-v4.json").read_bytes())
    inventory_before = {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size} for name in inventory["files"]}
    require(inventory_before == inventory["files"] and sum(row["bytes"] for row in inventory_before.values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "inventory hash/bytes")
    reviews = issued["preserved_available_review_sha256"]
    require(len(reviews) == 18 and all(sha(ROOT / name) == digest for name, digest in reviews.items()), "eighteen prior review hashes")
    # Authenticate peer bytes without reading peer review conclusions.
    trees = {version: ast.parse((PACKET / ("verify-" + version + ".py")).read_text()) for version in ("v3", "v4")}
    comparison = {version: ast.dump(next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compare_replay"), include_attributes=False) for version, tree in trees.items()}
    require(comparison["v3"] == comparison["v4"], "runtime comparator changed beyond reviewed v3 proof")
    require(prior_evidence["recorded_generic_runtime_and_all_other_scalar_leaf_mutations_rejected"] == 312 and prior_evidence["prior_v2_runtime_equality_finding_closed_by_v3_compare_replay"], "retained strict-comparison proof")
    verifier = load(PACKET / "verify-v4.py", "frozen_v4_verifier_actual")
    wrapper = load(PACKET / "adapter-v2.py", "frozen_catalog_wrapper_reused_v4")
    generic_verifier = load(FIXTURE / "verify.py", "frozen_generic_guards_reused_v4")
    saved = json.loads((PACKET / "result-v3.json").read_bytes())
    current, old = wrapper.calculate()
    require(verifier.compare_replay(current, saved) == current and old["drawing"](current) == (PACKET / "result-v3.svg").read_bytes(), "current fixture scalar/SVG replay")
    pins = saved["source_sha256"]
    require(len(pins) == 30 and all(sha(ROOT / name) == digest for name, digest in pins.items()), "thirty source pins")
    control_record = issued["actual_main_controls"]
    positive_path = ROOT / control_record["positive_probe_receipt_active_ignored"]
    require(sha(positive_path) == control_record["positive_probe_receipt_sha256"], "frozen v4 CLI child bytes")
    positive = json.loads(positive_path.read_bytes())
    require(positive["passed"] is True and positive["verification_method_sha256"] == EXPECTED["verify-v4.py"] and positive["actual_main_controls"] is None, "child controls disabled and method bound")
    require(positive["recorded_runtime_provenance"] == saved["runtime_reproduction"] and all(positive["live_runtime_provenance"][key] != saved["runtime_reproduction"][key] for key in verifier.LIVE_RUNTIME_FIELDS), "live/recorded runtime distinction")
    require(positive["reused_independent_decimal_checks"] == issued["reused_independent_decimal_checks"] and positive["release"] == saved["release"], "child fixture scope")

    original_loader, original_version = runpy.run_path, sys.version
    entry_cases = [("help", ["--help"], 0), ("missing_out", [], 2),
                   ("occupied_output", ["--out", str(PACKET / "verification-v4.json")], "fresh receipt required"),
                   ("outside_parent", ["--out", str(OUT / "unwritten.json")], "owned canonical JSON receipt required"),
                   ("wrong_suffix", ["--out", str(PACKET / "_testing_unwritten.txt")], "owned canonical JSON receipt required")]
    entry_controls = []
    original_read_bytes = Path.read_bytes
    for name in verifier.FROZEN_V3:
        entry_cases.append(("changed_" + name, ["--out", str(PACKET / "_testing_unwritten.json")], "frozen v2/v3 packet or inventories differ"))
    for label, args, expected in entry_cases:
        child_boundary = Mock(side_effect=AssertionError("child launcher entered before CLI preflight"))
        mutations = []

        def no_mutation(*_args, mutations=mutations, **_kwargs):
            mutations.append("filesystem mutation")
            raise AssertionError("filesystem mutation before CLI preflight")

        def read_source(path, label=label):
            return b"in-memory changed frozen source" if label.startswith("changed_") and path == PACKET / label.removeprefix("changed_") else original_read_bytes(path)

        with ExitStack() as stack:
            stack.enter_context(patch.object(subprocess, "run", child_boundary))
            stack.enter_context(patch.object(sys, "argv", [str(PACKET / "verify-v4.py"), *args]))
            stack.enter_context(patch.object(Path, "read_bytes", read_source))
            for method in ("mkdir", "unlink", "rmdir", "rename", "replace", "symlink_to", "hardlink_to", "write_bytes", "write_text"):
                stack.enter_context(patch.object(Path, method, no_mutation))
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(redirect_stderr(io.StringIO()))
            try:
                original_loader(str(PACKET / "verify-v4.py"), run_name="__main__")
            except SystemExit as error:
                require(isinstance(expected, int) and error.code == expected, "entrypoint argparse outcome")
            except ValueError as error:
                require(str(error) == expected, "entrypoint preflight outcome")
            else:
                raise AssertionError("expected guarded CLI termination")
        require(not child_boundary.called and not mutations, "entrypoint did work before preflight")
        entry_controls.append({"case": label, "expected_outcome": expected, "child_launch_attempts": 0, "filesystem_mutation_attempts": 0})

    main_corruption_controls = []
    virtual = PACKET / ("_testing_v4_unwritten_" + str(os.getpid()) + ".json")
    require(not os.path.lexists(virtual), "virtual output occupied")
    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        (scratch / "controls01").mkdir()
        (scratch / "result.json").write_bytes(b"owned inherited output-guard fixture")
        events = []
        actual_guards = generic_verifier.guard_checks

        def owned_guards(function):
            events.append("output_guards")
            with patch.object(generic_verifier, "HERE", scratch), patch.dict(function.__globals__, {"HERE": scratch}):
                return actual_guards(function)

        def guard_proxy(function):
            return owned_guards(function)

        isolated_proxy = FunctionType(guard_proxy.__code__, {}, closure=guard_proxy.__closure__)

        def redirected_loader(path, *args, **kwargs):
            if Path(path).resolve() == FIXTURE / "verify.py":
                return {"guard_checks": isolated_proxy}
            module = original_loader(path, *args, **kwargs)
            if Path(path).resolve() == PACKET / "verify.py":
                decimal = module["decimal_corners"]

                def counted_decimal(value):
                    events.append("Decimal")
                    return decimal(value)

                module["decimal_corners"] = counted_decimal
            if Path(path).resolve() == PACKET / "verify-v2.py":
                runtime = module["runtime_controls"]

                def counted_runtime(method, live):
                    events.append("runtime_controls")
                    return runtime(method, live)

                module["runtime_controls"] = counted_runtime
            return module

        original_open, original_stat, original_mkdir = Path.open, Path.stat, Path.mkdir

        def run_owned(destination, **kwargs):
            def redirect_open(path, *args, **options):
                return original_open(destination if path == virtual else path, *args, **options)

            def redirect_stat(path, *args, **options):
                return original_stat(destination if path == virtual else path, *args, **options)

            def redirect_mkdir(path, *args, **options):
                return original_mkdir(scratch / "controls01" if path == PACKET / "controls01" else path, *args, **options)

            with patch.object(verifier, "runpy", SimpleNamespace(run_path=redirected_loader)), patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(Path, "mkdir", redirect_mkdir), redirect_stdout(io.StringIO()):
                return verifier.main(["--out", str(virtual)], **kwargs)

        disabled_boundary = Mock(side_effect=AssertionError("default main invoked controls"))
        with patch.object(verifier, "actual_main_controls", disabled_boundary):
            default_result = run_owned(scratch / "default.json")
        require(not disabled_boundary.called and default_result["actual_main_controls"] is None, "child/default controls enabled")
        enabled_path = scratch / "enabled.json"
        events.clear()

        def reused_main_controls():
            require(events == ["Decimal", "runtime_controls", "output_guards"] and not enabled_path.exists(), "controls ran before normal verification or after receipt write")
            events.append("actual_main_controls_reused")
            return control_record

        with patch.object(verifier, "actual_main_controls", side_effect=reused_main_controls) as enabled:
            run_owned(enabled_path, run_main_controls=True)
        require(enabled.call_count == 1 and enabled_path.read_bytes() == (PACKET / "verification-v4.json").read_bytes(), "enabled main exact replay using authenticated control record")
        main_replay_sha = sha(enabled_path)
        sequence = list(events)
        alternate = copy.deepcopy(current)
        for key in verifier.LIVE_RUNTIME_FIELDS:
            alternate["runtime_reproduction"][key] = "3.12.99 (synthetic v4 review runtime)"
        with patch.object(verifier, "actual_main_controls", disabled_boundary):
            alt_receipt = run_owned(scratch / "alternate.json", calculate=lambda: (alternate, old))
        require(alt_receipt["passed"] is True and alt_receipt["live_runtime_provenance"] == alternate["runtime_reproduction"] and alt_receipt["recorded_runtime_provenance"] == saved["runtime_reproduction"], "runtime-only regression")
        for path, replacement in [(("derived_relative_bound_under_declared_unobserved_conditions_mm",), 1.6),
                                  (("runtime_reproduction", "generic_recorded_execution_python"), "changed recorded runtime"),
                                  (("release", "fabrication"), True)]:
            bad = copy.deepcopy(current)
            v1.change(bad, path, replacement)
            boundary = Mock(side_effect=AssertionError("controls before corrupt-result rejection"))
            rejected_path = scratch / "rejected-unwritten.json"
            with patch.object(verifier, "actual_main_controls", boundary):
                message = rejected(lambda bad=bad, rejected_path=rejected_path: run_owned(rejected_path, calculate=lambda: (bad, old), run_main_controls=True))
            require(message == "non-runtime wrapper scalar/source/structure replay difference" and not boundary.called and not rejected_path.exists(), "corruption controls did work or wrote")
            main_corruption_controls.append({"path": list(path), "rejection": message, "before_controls_and_output": True})

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "v4 target preservation")
    require(inventory_before == {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size} for name in inventory_before}, "all packet/history preservation")
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()) and all(sha(ROOT / name) == digest for name, digest in reviews.items()) and sha(positive_path) == control_record["positive_probe_receipt_sha256"], "pins/reviews/saved child preservation")
    require(runpy.run_path is original_loader and sys.version == original_version and not os.path.lexists(virtual), "ambient state or shared leaf changed")
    require(len(saved["release"]) == 13 and all(value is False for value in saved["release"].values()) and len(saved["actual_observations"]) == 9 and all(value == "" for value in saved["actual_observations"].values()), "release/blank boundary")
    return {
        "schema": "eoere_Z180_catalog_adapter_independent_testing_review/v4",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "three_v4_target_sha256_before_after": before,
        "reused_own_v3_helper_sha256": PRIOR_HELPER_SHA, "reused_own_v3_receipt_sha256": PRIOR_RECEIPT_SHA,
        "inventory_file_count": len(inventory_before), "inventory_file_bytes": sum(row["bytes"] for row in inventory_before.values()),
        "inventory_files_hash_and_bytes_before_after": inventory_before,
        "thirty_source_pins_authenticated_before_after": pins, "eighteen_prior_review_files_hash_only_before_after": reviews,
        "runtime_comparator_AST_unchanged_from_reviewed_v3": True,
        "reused_v3_strict_scalar_leaf_rejection_count": 312,
        "actual_dunder_main_preflight_controls": entry_controls,
        "main_default_and_child_controls_disabled": True,
        "main_enabled_controls_called_once_after_actual_normal_checks_before_receipt": sequence,
        "actual_main_byte_exact_replay_with_authenticated_control_record_sha256": main_replay_sha,
        "actual_main_alternate_live_runtime_regression_passed": True,
        "actual_main_corruption_rejections_before_controls_and_output": main_corruption_controls,
        "saved_parent_actual_CLI_positive_authenticated_not_reexecuted": {"path": str(positive_path.relative_to(ROOT)), "sha256": sha(positive_path)},
        "reused_evidence": "Frozen producer actual scalar/SVG/CLI proof, v3 strict runtime comparator and 312 leaf controls; current v4 normal main APIs actually rerun retained seven runtime, eight output and 256 Decimal controls. Parent-run positive child and entrypoint audit evidence authenticated; review invokes actual __main__ preflight with child and filesystem mutation boundaries blocked and actual main with owned final receipt/guard IO. The expensive/control child launcher is replaced only by its authenticated issued report for exact final receipt replay, not claimed as own execution.",
        "prior_v3_CLI_controls_before_preflight_finding_closed": True,
        "findings": [], "all_sources_targets_reviews_and_history_unchanged": True,
        "shared_runpy_and_sys_version_unchanged": True,
        "scope": "Bounded v4 CLI/output sequencing, regression controls and current source-only fixture reproducibility. No broad historical arithmetic re-audit, second-interpreter qualification or actual fixture/hardware/physical proof. Current Z200/100 bolts/66 screws/forces/HOLD and unadopted Z180 remain unchanged; reference exceedances and blank actuals/false releases retained.",
        "excluded": ["reviewer child/control launcher execution", "native/CAD/BREP/FEA/global/browser/physical work", "manufacturer/PDF or actual bit/fixture fit qualification", "model/current forces/held operations/panel remedies or acceptance changes", "shared files, docs/site/index edits, staging or commit"],
        "mechanics_or_physical_release": False,
    }


if __name__ == "__main__":
    original_import = builtins.__import__
    native_attempts = []

    def no_native(name, *args, **kwargs):
        if name.split(".")[0] in ("cadquery", "OCP", "numpy", "scipy"):
            native_attempts.append(name)
            raise AssertionError("forbidden import: " + name)
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", side_effect=no_native):
        receipt = review()
    assert not native_attempts
    receipt["native_or_numeric_library_import_attempts"] = native_attempts
    destination = OUT / "receipt.json"
    with destination.open("xb") as stream:
        stream.write((json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False) + "\n").encode())
    print(json.dumps({"receipt": str(destination.relative_to(ROOT)), "sha256": sha(destination), "findings": len(receipt["findings"])}))
