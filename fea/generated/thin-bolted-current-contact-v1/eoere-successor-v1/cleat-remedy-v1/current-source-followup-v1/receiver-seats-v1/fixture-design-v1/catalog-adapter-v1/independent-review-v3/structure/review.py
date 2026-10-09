"""Source-only architecture/publication review of the frozen v3 verifier."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "verify-v3.py": "354bac725ebd23693bb835da073b8b503118df471cdded27e271dc3cd38f009e",
    "verification-v3.json": "2b484b62786d0c919aa21a0560cff078e2dfd2182ea5c070b5a32d9b920746da",
    "controls01/publication-file-inventory-v3.json": "df6b43be7214dd73b67284df0b45bdf6a7bd4dbeb9eb54a2f459c22447a73230",
}
PREVIOUS_HELPER = "f0329edc5e792dd11ad259889faa5b77744c3981bc5385c09bef8ab13fa87698"
PREVIOUS_RECEIPT = "ffacb1b5aef91be8cd71915b986691b20ad8a343f7444843b72d44b9010f83ab"
COMMON_SHA = "6d61bef99313cc7a6cd7af223e3c4b5adc2722294e51d8e57a58efce30d13158"


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review():
    prior_path = PACKET / "independent-review-v2/structure/review.py"
    prior_receipt_path = prior_path.with_name("receipt.json")
    common_path = PACKET.parent / "independent-review-v1/structure/review.py"
    require(sha(prior_path) == PREVIOUS_HELPER and sha(prior_receipt_path) == PREVIOUS_RECEIPT and sha(common_path) == COMMON_SHA, "prior review helpers/proofs changed")
    prior = load(prior_path, "catalog_v2_structure_utilities_only")
    common = load(common_path, "generic_structure_guard_utilities_only")
    require(not common.native_modules(), "source-only process required")
    inventory = read(PACKET / "controls01/publication-file-inventory-v3.json")
    saved, verified, proof = (read(path) for path in (PACKET / "result-v3.json", PACKET / "verification-v3.json", prior_receipt_path))
    pins = {str((PACKET / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    for mapping in (saved["source_sha256"], verified["preserved_available_review_sha256"],
                    {str((PACKET / n).relative_to(ROOT)): r["sha256"] for n, r in inventory["files"].items()},
                    proof["integrity"]["retained_current_numerical_sha256"]):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "contradictory source/output/review pins")
            pins[name] = digest
    pins[str(common_path.relative_to(ROOT))] = COMMON_SHA
    common_receipt = common_path.with_name("receipt.json")
    require(sha(common_receipt) == "8d7155ebc75fe9404758531ae73a899f37379d55a870e514eecaa904fafe416b", "generic proof changed")
    pins[str(common_receipt.relative_to(ROOT))] = sha(common_receipt)
    probe = inventory["active_ignored"]["positive_actual_main_probe"]
    pins[probe["path"]] = probe["sha256"]
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins and saved["source_pin_count"] == verified["source_pin_count"] == len(saved["source_sha256"]) == 30, "frozen source/target mismatch")
    require(len(inventory["files"]) == 21 and all((PACKET / n).stat().st_size == r["bytes"] for n, r in inventory["files"].items()), "permanent file census differs")
    require(sum(r["bytes"] for r in inventory["files"].values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"] == 214230, "permanent byte census differs")
    require(verified["verification_method_sha256"] == TARGETS["verify-v3.py"] and verified["passed"], "issued verifier identity differs")
    contexts = [ROOT / n for n in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md", "CONTRIBUTING.md", "pyproject.toml")]
    factory_path = PACKET.parent.parent / "hardware-followup-v1/factory-guide-sources-v1.json"
    contexts.append(factory_path)
    context_before = {str(p.relative_to(ROOT)): sha(p) for p in contexts}

    wrapper = load(PACKET / "adapter-v2.py", "catalog_structure_frozen_producer")
    verifier = load(PACKET / "verify-v3.py", "catalog_structure_verifier_v3")
    ambient_run_path, ambient_version = runpy.run_path, sys.version
    live, old = wrapper.calculate()
    untouched = copy.deepcopy(live)
    expected = {k: v for k, v in saved.items() if k != "drawing"}
    require(verifier.compare_replay(live, saved) == expected and live == untouched, "exact current-runtime comparison or immutability differs")
    with patch.object(sys, "version", sys.version + " (source-only v3 metadata control)"):
        alternate, _ = wrapper.calculate()
    require(verifier.compare_replay(alternate, saved) == expected, "corrected production comparison rejects runtime-only metadata")
    fields = ("generic_live_execution_python", "wrapper_live_execution_python")
    require(verifier.LIVE_RUNTIME_FIELDS == fields, "normalization scope expanded")
    require(verified["normalized_wrapper_comparison_paths_only"] == ["/runtime_reproduction/" + n for n in fields], "issued normalization scope differs")
    require(all(alternate["runtime_reproduction"][n] != saved["runtime_reproduction"][n] for n in fields)
            and alternate["runtime_reproduction"]["generic_recorded_execution_python"] == saved["runtime_reproduction"]["generic_recorded_execution_python"], "live/saved provenance not separated")
    controls = {
        "derived_relative_bound": ("derived_relative_bound_under_declared_unobserved_conditions_mm",),
        "source_pin": ("source_sha256", next(iter(live["source_sha256"]))),
        "recorded_generic_runtime": ("runtime_reproduction", "generic_recorded_execution_python"),
        "release_flag": ("release", "fabrication"),
        "execution_flag": ("execution", "new_CAD_BREP_native_mechanics_mesh_or_physical_run"),
        "nontext_generic_live_runtime": ("runtime_reproduction", fields[0]),
        "nontext_wrapper_live_runtime": ("runtime_reproduction", fields[1]),
        "extra_runtime_field": ("runtime_reproduction", "unexpected_review_field"),
        "extra_top_level_field": ("unexpected_review_field",),
    }
    rejected = []
    for label, path in controls.items():
        bad = copy.deepcopy(alternate)
        leaf = bad
        for key in path[:-1]:
            leaf = leaf[key]
        leaf[path[-1]] = None if label.startswith("nontext_") else (0.0 if label == "derived_relative_bound" else True)
        try:
            verifier.compare_replay(bad, saved)
        except ValueError:
            rejected.append(label)
        else:
            raise AssertionError("v3 comparison accepted nonruntime corruption: " + label)
    require(runpy.run_path is ambient_run_path and sys.version == ambient_version and wrapper.runpy is runpy, "ambient process state changed")
    require(old["load"].__globals__["runpy"] is not runpy, "producer's loader interception escaped its private namespace")
    require(old["drawing"](live) == (PACKET / "result-v3.svg").read_bytes(), "drawing/source replay changed")
    old_packet = common.PACKET
    common.PACKET = PACKET
    try:
        output_controls = common.output_controls(prior.load(PACKET / "adapter.py", "catalog_v3_frozen_output_guard"))
    finally:
        common.PACKET = old_packet

    # Authenticate the producer's retained real-main control; never rerun its
    # artifact-writing CLI or subprocess in this independently owned review.
    probe_receipt = read(ROOT / probe["path"])
    main_proof = verified["actual_main_controls"]
    require(main_proof["positive_probe_receipt_active_ignored"] == probe["path"] and main_proof["positive_probe_receipt_sha256"] == probe["sha256"], "actual-main probe binding differs")
    require(probe_receipt["passed"] and all(probe_receipt["live_runtime_provenance"][n].startswith("3.12.99 ") for n in fields), "retained main positive proof differs")
    require(probe_receipt["recorded_runtime_provenance"] == saved["runtime_reproduction"]
            and main_proof["recorded_generic_runtime_strict"] and not main_proof["second_interpreter_execution_claimed"], "retained runtime claims expanded")
    require(len(main_proof["nonruntime_actual_main_controls_rejected"]) == 8 and main_proof["parent_sys_version_and_shared_runpy_unchanged"], "retained actual-main rejection/isolation proof differs")
    require(verified["reused_independent_decimal_checks"]["independent_decimal_endpoint_corners"] == 256
            and proof["checks"]["saved256_Decimal_corners_reproduced"], "inherited same-source math proof differs")
    require(verified["runtime_reproduction_controls"] == proof["checks"]["reused_runtime_controls"], "unchanged producer runtime proof differs")
    history = read(PACKET / "development-v3/record.json")
    require(history["producer_sha256"] == inventory["files"]["development-v3/verify-v3.py"]["sha256"] and history["exit_code"] == 1, "preflight failure retention differs")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    coverage = {}
    for name, digest in saved["source_sha256"].items():
        if not name.endswith(".py"):
            continue
        committed, staged = prior.git_bytes(commit, name), prior.git_bytes("", name)
        owned = Path(name).is_relative_to(PACKET.relative_to(ROOT))
        coverage[name] = {"sha256": digest, "committed_exact": committed is not None and hashlib.sha256(committed).hexdigest() == digest,
                          "staged_exact": staged is not None and hashlib.sha256(staged).hexdigest() == digest, "owned_packet_publication_target": owned}
        require(owned or coverage[name]["committed_exact"] or coverage[name]["staged_exact"], "uncovered shared runtime code: " + name)
    require(coverage[prior.SHARED]["staged_exact"] and saved["source_sha256"][prior.SHARED] == prior.SHARED_SHA, "shared publication fix changed")
    facts = read(ROOT / read(PACKET / "inputs.json")["catalog_facts_path"])
    pdf = facts["sources"]["FISCH_pen_drill"]["raw_active_cache"]
    require(saved["source_sha256"][pdf["path"]] == pdf["sha256"] and (ROOT / pdf["path"]).stat().st_size == pdf["bytes"], "ignored PDF source binding differs")
    factory = read(factory_path)
    require(all(sha(ROOT / n) == h for n, h in factory["source_sha256"].items()), "factory source joins differ")
    require(all(v is False for v in factory["release"].values()) and all(v == "" for v in factory["actual_observations"].values()), "factory source facts promoted to acceptance")
    ledger = (ROOT / "docs/wood-joints-mvp/completion-ledger.md").read_text()
    require(prior.SHARED_SHA in ledger and pdf["sha256"] in ledger and facts["sources"]["FISCH_pen_drill"]["url"] in ledger
            and "raw_active_cache.path" in ledger and "differing downloaded bytes are not a substitute" in ledger, "maintained code/cache restoration boundary absent")
    require(saved["release"] == verified["release"] and all(v is False for v in saved["release"].values()) and all(v == "" for v in saved["actual_observations"].values()), "release/actual boundary changed")
    require(saved["preserved"]["current_Z200_and_four_HOLD_stations"] and not saved["preserved"]["current_forces_transferred_to_Z180"], "current/proposal authority transfer")
    require(all(not r.get("within_generic_allocation", r.get("within_generic_target")) for r in saved["generic_error_allowance_comparisons"].values()), "retained exceedances lost")
    require(not common.native_modules() and {name: sha(ROOT / name) for name in pins} == before, "native import or source/output/history drift")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_Z180_catalog_adapter_structure_review/v3", "review_helper_sha256": sha(OWN), "frozen_new_target_sha256": TARGETS, "findings": [],
        "integrity": {"direct_source_pins": 30, "verified_source_output_review_retention_union": len(pins), "unchanged_before_after": True,
                      "review_commit": commit, "small_runtime_code_publication_coverage": coverage, "previous_v2_structure_receipt_sha256": PREVIOUS_RECEIPT},
        "checks": {"current_runtime_comparison_exact": True, "production_runtime_metadata_only_comparison_passed": True,
                   "comparison_does_not_mutate_live_input": True, "independent_nonruntime_comparison_rejections": rejected,
                   "private_loader_and_ambient_runpy_sys_version_isolation": True, "inert_output_controls": output_controls,
                   "retained_actual_main_probe_sha256": probe["sha256"], "reused_same_source_Decimal_endpoint_corners": 256,
                   "existing_producer_7_runtime_and_8_output_control_proofs_authenticated": True},
        "ownership_scope_and_retention": {"producer_result_SVG_all_prior_packets_and_available_reviews_preserved": True,
                                         "new_verifier_normalizes_exactly_two_live_runtime_text_paths": True,
                                         "recorded_generic_runtime_source_guards_engineering_and_release_fields_remain_strict": True,
                                         "v3_preflight_failure_source_and_record_retained": True, "permanent_inventory_files": 21,
                                         "permanent_inventory_file_bytes_excluding_current_inventory_and_reviews": 214230,
                                         "shared_scalar_helper_staged_byte_identically": prior.SHARED_SHA,
                                         "shared_PDF_active_ignored_hash_bound_with_maintained_exact_restoration_boundary": pdf,
                                         "positive_main_probe_active_ignored_not_reexecuted": probe["path"],
                                         "factory_guide_is_source_comparison_with_actuals_blank_release_false": True,
                                         "Z180_unadopted_current_Z200_100_bolts_66_screws_HOLD_fields_retained_no_force_transfer": True,
                                         "generic_error_allocations_remain_unmet_actuals_blank_all_release_flags_false": True},
        "context": {"before_sha256": context_before, "after_sha256": {str(p.relative_to(ROOT)): sha(p) for p in contexts},
                    "maintained_prose_and_factory_facts_are_context_parent_may_update_prose": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Source/hash/scalar comparison APIs and inert mocks only; no target CLI, child process, CAD/native/BREP/FEA/global/browser/physical execution.",
                   "Actual-main positive/negative execution evidence is authenticated and reused; no new second-interpreter or clean-machine execution is claimed.",
                   "Same-source math and prior Decimal proofs are reused, not reissued. Native source closures, fields and manufacturer facts are not independently requalified.",
                   "All current and historical records remain active. No source/shared docs/model/site/index changes, staging, commit, copies, archives, pruning or engineering/physical acceptance."],
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
        print(json.dumps({"path": str(path.relative_to(ROOT)), "sha256": sha(path), "findings": len(receipt["findings"])}))
    else:
        print(json.dumps(receipt, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
