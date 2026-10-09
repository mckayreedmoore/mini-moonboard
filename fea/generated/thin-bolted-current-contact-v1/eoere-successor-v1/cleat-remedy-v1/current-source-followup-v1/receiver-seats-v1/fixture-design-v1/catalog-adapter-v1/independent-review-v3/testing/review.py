"""Bounded v3 verifier review; reuse frozen scalar evidence and own scratch IO."""
from __future__ import annotations

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
from contextlib import redirect_stdout
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
    "verify-v3.py": "354bac725ebd23693bb835da073b8b503118df471cdded27e271dc3cd38f009e",
    "verification-v3.json": "2b484b62786d0c919aa21a0560cff078e2dfd2182ea5c070b5a32d9b920746da",
    "controls01/publication-file-inventory-v3.json": "df6b43be7214dd73b67284df0b45bdf6a7bd4dbeb9eb54a2f459c22447a73230",
}
PRIOR_HELPER_SHA = "df7f8d29b6fa958dac210a0f70404fb42536752b80267f0699399af08b5074d5"
PRIOR_RECEIPT_SHA = "8fabd992267e8d7f924ad0c1b7c8723198904a3f50b248d46538ac7637e3d31a"
ALTERNATE = "3.12.99 (synthetic v3 testing runtime, not another interpreter)"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review():
    old_helper = PACKET / "independent-review-v2/testing/review.py"
    old_receipt = PACKET / "independent-review-v2/testing/receipt.json"
    assert sha(old_helper) == PRIOR_HELPER_SHA and sha(old_receipt) == PRIOR_RECEIPT_SHA
    prior = runpy.run_path(str(old_helper))
    load, leaves, different = prior["load"], prior["leaves"], prior["different"]
    v1_utilities = load(PACKET / "independent-review-v1/testing/review.py", "retained_review_utilities_v3")
    require, rejected, change = v1_utilities.require, v1_utilities.rejected, v1_utilities.change
    before = {name: sha(PACKET / name) for name in EXPECTED}
    require(before == EXPECTED, "three frozen v3 files differ")
    issued = json.loads((PACKET / "verification-v3.json").read_bytes())
    inventory = json.loads((PACKET / "controls01/publication-file-inventory-v3.json").read_bytes())
    inventory_before = {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size} for name in inventory["files"]}
    require(inventory_before == inventory["files"] and sum(row["bytes"] for row in inventory_before.values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"], "inventory hash/bytes")
    prior_reviews = issued["preserved_available_review_sha256"]
    require(len(prior_reviews) == 12 and all(sha(ROOT / name) == digest for name, digest in prior_reviews.items()), "twelve frozen prior review hashes")
    # Peer review contents are not read. Only hashes required by the producer's
    # receipt are authenticated; own prior testing evidence supplies reuse.
    old_proof = json.loads(old_receipt.read_bytes())
    require(old_proof["actual_current_scalar_and_SVG_replay_exact"] and old_proof["reused_independent_Decimal_API"]["independent_decimal_endpoint_corners"] == 256, "retained actual arithmetic proof")
    verifier = load(PACKET / "verify-v3.py", "frozen_v3_verifier_actual")
    wrapper = load(PACKET / "adapter-v2.py", "frozen_v2_wrapper_reused")
    generic_verifier = load(FIXTURE / "verify.py", "frozen_generic_guards_reused_v3")
    saved = json.loads((PACKET / "result-v3.json").read_bytes())
    current, old = wrapper.calculate()
    require(verifier.compare_replay(current, saved) == current, "actual current replay comparison")
    require(old["drawing"](current) == (PACKET / "result-v3.svg").read_bytes(), "unchanged current SVG")
    pins = saved["source_sha256"]
    require(len(pins) == 30 and all(sha(ROOT / name) == digest for name, digest in pins.items()), "thirty pins")
    live_fields = verifier.LIVE_RUNTIME_FIELDS
    require(live_fields == ("generic_live_execution_python", "wrapper_live_execution_python"), "exact two permitted leaves")
    positive_comparisons = []
    for selected in ((live_fields[0],), (live_fields[1],), live_fields):
        live = copy.deepcopy(current)
        for key in selected:
            live["runtime_reproduction"][key] = ALTERNATE
        untouched = copy.deepcopy(live)
        require(verifier.compare_replay(live, saved) == current and live == untouched, "runtime-only join or input immutability")
        positive_comparisons.append(list(selected))
    rejected_paths = []
    for path, value in leaves(current):
        if path in (("runtime_reproduction", live_fields[0]), ("runtime_reproduction", live_fields[1])):
            continue
        bad = copy.deepcopy(current)
        change(bad, path, different(value))
        rejected(lambda bad=bad: verifier.compare_replay(bad, saved))
        rejected_paths.append(list(path))
    structure_controls = []
    for field in live_fields:
        for value in (None, False, 3.12, [], {}):
            bad = copy.deepcopy(current)
            bad["runtime_reproduction"][field] = value
            structure_controls.append({"field": field, "type": type(value).__name__, "rejection": rejected(lambda bad=bad: verifier.compare_replay(bad, saved))})
    extra = copy.deepcopy(current)
    extra["runtime_reproduction"]["unexpected"] = True
    structure_controls.append({"field": "extra_runtime_field", "rejection": rejected(lambda: verifier.compare_replay(extra, saved))})

    # Authenticate the parent-run same-executable CLI positive, rather than
    # rerun the unconditional shared-output control launcher.
    positive_record = issued["actual_main_controls"]
    positive_path = ROOT / positive_record["positive_probe_receipt_active_ignored"]
    require(sha(positive_path) == positive_record["positive_probe_receipt_sha256"], "saved actual-main positive bytes")
    positive = json.loads(positive_path.read_bytes())
    require(positive["passed"] is True and positive["verification_method_sha256"] == EXPECTED["verify-v3.py"] and positive["actual_main_controls"] is None, "genuine child main receipt binding")
    require(positive["recorded_runtime_provenance"] == saved["runtime_reproduction"] and all(positive["live_runtime_provenance"][field] != saved["runtime_reproduction"][field] for field in live_fields), "saved alternate live/recorded provenance")
    require(positive["live_runtime_provenance"][live_fields[0]] == positive["live_runtime_provenance"][live_fields[1]] and positive["live_runtime_provenance"]["generic_recorded_execution_python"] == saved["runtime_reproduction"]["generic_recorded_execution_python"], "recorded generic runtime stays exact")
    require(positive["reused_independent_decimal_checks"] == issued["reused_independent_decimal_checks"] and positive["release"] == saved["release"], "saved positive retains numerical/release scope")
    original_loader = runpy.run_path
    original_version = sys.version
    entrypoint_controls = []

    class ControlLauncherEntered(Exception):
        pass

    def blocked_child(*_args, **_kwargs):
        raise ControlLauncherEntered

    for args in (("--help",), ("--out", str(PACKET / "verification-v3.json")), ("--out", str(OUT / "outside-unwritten.json"))):
        with patch.object(subprocess, "run", side_effect=blocked_child), patch.object(sys, "argv", [str(PACKET / "verify-v3.py"), *args]):
            try:
                original_loader(str(PACKET / "verify-v3.py"), run_name="__main__")
            except ControlLauncherEntered:
                entrypoint_controls.append({"argv": list(args), "subprocess_entered_before_argument_or_destination_guard": True, "child_blocked_without_execution_or_output": True})
            else:
                raise AssertionError("entrypoint did not enter controls before CLI guards")

    source_controls = []
    original_sha = verifier.sha
    virtual = PACKET / ("_testing_v3_unwritten_" + str(os.getpid()) + ".json")
    require(not os.path.lexists(virtual), "virtual destination occupied")
    for name in (*verifier.FROZEN_V2, "inputs.json", "adapter.py", "result-v2.json"):
        boundary = Mock(side_effect=AssertionError("loader before source rejection"))
        with patch.object(verifier, "sha", side_effect=lambda path, name=name: "0" * 64 if Path(path) == PACKET / name else original_sha(path)), patch.object(verifier, "runpy", SimpleNamespace(run_path=boundary)):
            message = rejected(lambda: verifier.main(["--out", str(virtual)]))
        require(not boundary.called and not os.path.lexists(virtual), "source rejection did work")
        source_controls.append({"source": name, "rejection": message, "before_loader": True})

    main_negative_controls = []
    with tempfile.TemporaryDirectory(prefix="scratch-", dir=OUT) as raw:
        scratch = Path(raw)
        (scratch / "controls01").mkdir()
        (scratch / "result.json").write_bytes(b"owned output guard fixture")
        original_guards = generic_verifier.guard_checks

        def own_guards(function):
            with patch.object(generic_verifier, "HERE", scratch), patch.dict(function.__globals__, {"HERE": scratch}):
                return original_guards(function)

        def guard_proxy(function):
            return own_guards(function)

        isolated_proxy = FunctionType(guard_proxy.__code__, {}, closure=guard_proxy.__closure__)

        def redirected_loader(path, *args, **kwargs):
            return {"guard_checks": isolated_proxy} if Path(path).resolve() == FIXTURE / "verify.py" else original_loader(path, *args, **kwargs)

        original_open, original_stat, original_mkdir = Path.open, Path.stat, Path.mkdir

        def run_owned_main(destination, **kwargs):
            def redirect_open(path, *args, **options):
                return original_open(destination if path == virtual else path, *args, **options)

            def redirect_stat(path, *args, **options):
                return original_stat(destination if path == virtual else path, *args, **options)

            def redirect_mkdir(path, *args, **options):
                return original_mkdir(scratch / "controls01" if path == PACKET / "controls01" else path, *args, **options)

            with patch.object(verifier, "runpy", SimpleNamespace(run_path=redirected_loader)), patch.object(Path, "open", redirect_open), patch.object(Path, "stat", redirect_stat), patch.object(Path, "mkdir", redirect_mkdir), redirect_stdout(io.StringIO()):
                return verifier.main(["--out", str(virtual)], **kwargs)

        current_receipt = scratch / "current.json"
        run_owned_main(current_receipt, main_control_report=issued["actual_main_controls"])
        require(current_receipt.read_bytes() == (PACKET / "verification-v3.json").read_bytes(), "current actual main exact replay")
        current_sha = sha(current_receipt)
        for selected in ((live_fields[0],), (live_fields[1],), live_fields):
            changed = copy.deepcopy(current)
            for field in selected:
                changed["runtime_reproduction"][field] = ALTERNATE
            owned_path = scratch / ("alternate-" + str(len(selected)) + "-" + selected[0] + ".json")
            result = run_owned_main(owned_path, calculate=lambda changed=changed: (changed, old))
            require(result["passed"] is True and result["recorded_runtime_provenance"] == saved["runtime_reproduction"] and result["live_runtime_provenance"] == changed["runtime_reproduction"], "actual main runtime-only positive or provenance")
        corruptions = [(("derived_relative_bound_under_declared_unobserved_conditions_mm",), 1.6),
                       (("runtime_reproduction", "generic_recorded_execution_python"), ALTERNATE),
                       (("release", "fabrication"), True),
                       (("preserved", "current_forces_transferred_to_Z180"), True),
                       (("preserved", "current_Z200_and_four_HOLD_stations"), False),
                       (("execution", "new_CAD_BREP_native_mechanics_mesh_or_physical_run"), True),
                       (("actual_observations", "Actual"), "unobserved control must reject"),
                       (("runtime_reproduction", live_fields[0]), None)]
        for path, replacement in corruptions:
            bad = copy.deepcopy(current)
            change(bad, path, replacement)
            rejected_path = scratch / "rejected-unwritten.json"
            message = rejected(lambda bad=bad, rejected_path=rejected_path: run_owned_main(rejected_path, calculate=lambda: (bad, old)))
            require("non-runtime wrapper" in message or "live runtime text required" in message, "unrelated main rejection")
            require(not os.path.lexists(rejected_path) and not os.path.lexists(virtual), "rejected main wrote output")
            main_negative_controls.append({"path": list(path), "rejection": message, "no_receipt_created": True})
        api_output_controls = []
        for requested in (PACKET / "verification-v3.json", OUT / "unwritten.json", PACKET / "_testing_unwritten.txt"):
            boundary = Mock(side_effect=AssertionError("loader before API output rejection"))
            with patch.object(verifier, "runpy", SimpleNamespace(run_path=boundary)):
                message = rejected(lambda requested=requested: verifier.main(["--out", str(requested)]))
            require(not boundary.called, "API output guard did work")
            api_output_controls.append({"requested": str(requested.relative_to(ROOT)), "rejection": message, "before_loader": True})

    require(before == {name: sha(PACKET / name) for name in EXPECTED}, "v3 target preservation")
    require(inventory_before == {name: {"sha256": sha(PACKET / name), "bytes": (PACKET / name).stat().st_size} for name in inventory_before}, "inventory/history preservation")
    require(all(sha(ROOT / name) == digest for name, digest in pins.items()) and all(sha(ROOT / name) == digest for name, digest in prior_reviews.items()) and sha(positive_path) == positive_record["positive_probe_receipt_sha256"], "pins/reviews/positive receipt preservation")
    require(runpy.run_path is original_loader and sys.version == original_version, "ambient loader or runtime mutation")
    require(len(saved["release"]) == 13 and all(value is False for value in saved["release"].values()) and len(saved["actual_observations"]) == 9 and all(value == "" for value in saved["actual_observations"].values()), "physical/observation boundary")
    return {
        "schema": "eoere_Z180_catalog_adapter_independent_testing_review/v3",
        "review_helper": {"path": str(OWN.relative_to(ROOT)), "sha256": sha(OWN)},
        "three_v3_targets_sha256_before_after": before,
        "reused_own_v2_helper_sha256": PRIOR_HELPER_SHA, "reused_own_v2_receipt_sha256": PRIOR_RECEIPT_SHA,
        "inventory_file_count": len(inventory_before), "inventory_file_bytes": sum(row["bytes"] for row in inventory_before.values()),
        "inventory_files_hash_and_bytes_before_after": inventory_before,
        "thirty_source_pins_authenticated_before_after": pins,
        "twelve_prior_review_files_hash_only_before_after": prior_reviews,
        "saved_actual_CLI_positive_receipt_authenticated_not_reexecuted": {"path": str(positive_path.relative_to(ROOT)), "sha256": sha(positive_path)},
        "actual_current_main_byte_exact_replay_sha256": current_sha,
        "three_actual_main_runtime_only_positive_cases": positive_comparisons,
        "recorded_generic_runtime_and_all_other_scalar_leaf_mutations_rejected": len(rejected_paths),
        "protected_mutated_paths_sha256": hashlib.sha256(json.dumps(rejected_paths, sort_keys=True).encode()).hexdigest(),
        "additional_comparison_structure_controls": structure_controls,
        "actual_main_nonruntime_rejections_without_receipt": main_negative_controls,
        "actual_main_API_source_rejections_before_loader": source_controls,
        "actual_main_API_output_rejections_before_loader": api_output_controls,
        "actual_script_entrypoint_controls_child_blocked": entrypoint_controls,
        "reused_evidence": "Frozen v2 testing actual producer main/SVG replay, 568 generic nonruntime leaf controls, seven runtime-control API checks, eight output guards and 256 Decimal corners remain applicable. Current v3 main independently reruns those retained verifier APIs under owned guard/receipt IO; no second interpreter, native or browser execution.",
        "prior_v2_runtime_equality_finding_closed_by_v3_compare_replay": True,
        "findings": [{"severity": "medium", "file": str((PACKET / "verify-v3.py").relative_to(ROOT)), "line": 194,
                      "title": "CLI starts output-producing controls before validating arguments or destination",
                      "impact": "Python evaluates actual_main_controls() before entering main(), so --help, an occupied requested receipt and an outside output all enter the subprocess launcher first. On valid frozen sources that launcher creates a new main-v3-runtime-controlNN.json before the requested output is rejected. This bypasses main's rejection-before-work boundary and causes unexpected packet writes for read-only/help or invalid invocations. Three real __main__ entrypoint probes confirm ordering with the child blocked; no child or shared write was executed by this review. Issued numerical/SVG and runtime-normalization observations remain correct.",
                      "fix": "Parse and validate the requested CLI destination before launching controls, then run the control suite and main against that validated destination, or expose controls as a separate explicit operation. Add __main__ tests for --help, existing output and outside output asserting no child launch or files."}],
        "all_sources_targets_reviews_and_history_unchanged": True, "shared_runpy_and_sys_version_unchanged": True,
        "scope": "Source-only review of the three frozen v3 files. Actual compare_replay API and scalar leaf mutations, actual main API current/alternate-runtime positives and nonruntime negatives, preflight/output guards, saved same-executable CLI child receipt authentication and actual __main__ ordering probes with subprocess execution blocked. Current main receipt/guard scratch IO redirected only to exclusive own temporary paths. Frozen v1/v2 manufacturer/scalar/Decimal evidence reused, not re-qualified.",
        "excluded": ["subprocess control child or second interpreter execution by reviewer", "native/CAD/BREP/FEA/global/browser/physical work", "manufacturer/PDF or actual bit/fixture fit qualification", "current Z200/100 bolt/66 screw/force/HOLD or unadopted Z180 changes", "panel remedies, reference relaxation or strength/physical release", "shared file/index/document edits, staging or commit"],
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
