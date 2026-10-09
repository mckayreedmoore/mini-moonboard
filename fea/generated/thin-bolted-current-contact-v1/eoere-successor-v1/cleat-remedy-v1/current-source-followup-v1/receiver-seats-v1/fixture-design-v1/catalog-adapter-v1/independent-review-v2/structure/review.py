"""Frozen v2 catalog adapter structure/publication review; source-only IO."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import runpy
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
FACTORY = PACKET.parent.parent / "hardware-followup-v1/factory-guide-sources-v1.json"
TARGETS = {
    "adapter-v2.py": "dae93a7011242ad3878f47040cbf3af9cd224d7077eb503621a8816d55cd4014",
    "result-v3.json": "1060bc7a57fb90b6dc8b3dd1aeb18bb863eb3e0fbe7dd2043c524a15c5d48fbf",
    "result-v3.svg": "4b52eaba8f98d5457b606061f5d51eace14bc222d38dc6bc0f873d91ff2e1b6b",
    "verify-v2.py": "2f01212e390c5ea53a23821ecb6042e82fe0c9b64fd1fc54341c0944b3c0757f",
    "verification-v2.json": "286c4df35620d46d4a3276904ffb6f4997c5a0cf57f8c49b6e113a0f9231410e",
    "controls01/publication-file-inventory-v2.json": "e0f7e412e4f8a64385dc564d7793c8b3b9cdf6fbe256c561c7c8eb9f1497f514",
}
FACTORY_SHA = "3e0d553d76fa076764c06a393554c98e297b597fee8d339fd493053ea057e429"
PREVIOUS_REVIEW_SHA = "3d9d09f8cc4983efaff294362a886c337ab001126037ebe020cb930d5ea9d210"
COMMON_SHA = "6d61bef99313cc7a6cd7af223e3c4b5adc2722294e51d8e57a58efce30d13158"
SHARED = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-corners-v1/lower_bolt_z_v2.py"
SHARED_SHA = "a49bc35aeea241360af9df401bd48cc875ccdd34a6e118e109c06d122f45c095"


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


def git_bytes(ref, path):
    result = subprocess.run(["git", "show", ref + ":" + path], cwd=ROOT, capture_output=True, check=False)
    return None if result.returncode else result.stdout


def review():
    inventory = read(PACKET / "controls01/publication-file-inventory-v2.json")
    saved, verified = (read(PACKET / name) for name in ("result-v3.json", "verification-v2.json"))
    prior_path = PACKET / "independent-review-v1/structure/review.py"
    common_path = PACKET.parent / "independent-review-v1/structure/review.py"
    require(sha(prior_path) == PREVIOUS_REVIEW_SHA and sha(common_path) == COMMON_SHA, "reused helpers changed")
    prior = load(prior_path, "catalog_structure_v1_utilities_only")
    common = load(common_path, "generic_structure_inert_helpers_only")
    require(not common.native_modules(), "source-only process required")
    pins = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in TARGETS.items()}
    pins[str(FACTORY.relative_to(ROOT))] = FACTORY_SHA
    for mapping in (saved["source_sha256"], verified["preserved_v1_review_sha256"],
                    {str((PACKET / n).relative_to(ROOT)): r["sha256"] for n, r in inventory["files"].items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "source/output pin contradiction")
            pins[name] = digest
    pins[str(prior_path.relative_to(ROOT))] = PREVIOUS_REVIEW_SHA
    pins[str(common_path.relative_to(ROOT))] = COMMON_SHA
    common_receipt = common_path.with_name("receipt.json")
    require(sha(common_receipt) == "8d7155ebc75fe9404758531ae73a899f37379d55a870e514eecaa904fafe416b", "generic receipt changed")
    pins[str(common_receipt.relative_to(ROOT))] = sha(common_receipt)
    numerical = read(common_receipt)["integrity"]["retained_current_numerical_sha256"]
    pins.update(numerical)
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins and saved["source_pin_count"] == len(saved["source_sha256"]) == 30, "frozen sources differ")
    require(all((PACKET / n).stat().st_size == row["bytes"] for n, row in inventory["files"].items()), "inventory size differs")
    require(sum(row["bytes"] for row in inventory["files"].values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"] == 174648, "permanent volume differs")
    require(sum(inventory["files"][n]["bytes"] for n in inventory["corrected_final_files"]) == inventory["new_corrected_final_file_bytes"] == 50963, "v2 volume differs")
    contexts = ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md", "CONTRIBUTING.md", "pyproject.toml")
    context_before = {name: sha(ROOT / name) for name in contexts}

    wrapper = load(PACKET / "adapter-v2.py", "catalog_structure_adapter_v2")
    verifier = load(PACKET / "verify-v2.py", "catalog_structure_verifier_v2")
    original_run_path = runpy.run_path
    live, method = wrapper.calculate()
    reference = {k: v for k, v in saved.items() if k != "drawing"}
    require(live == reference, "issued current-runtime replay differs")
    require(method["drawing"](live) == (PACKET / "result-v3.svg").read_bytes() == (PACKET / "result-v2.svg").read_bytes(), "frozen SVG changed")
    require(runpy.run_path is original_run_path and wrapper.runpy is runpy, "shared runpy mutated")
    require(method["load"].__globals__["runpy"] is not runpy, "private loader not isolated")
    runtime_checks = verifier.runtime_controls(vars(wrapper), live)
    require(runtime_checks == verified["runtime_reproduction_controls"], "saved runtime controls differ")
    decimal = prior.load(PACKET / "verify.py", "catalog_structure_decimal_v1").decimal_corners(saved)
    require(decimal == verified["reused_independent_decimal_checks"], "saved Decimal replay differs")
    old_packet = common.PACKET
    common.PACKET = PACKET
    try:
        output_controls = common.output_controls(prior.load(PACKET / "adapter.py", "catalog_structure_guard_v1"))
    finally:
        common.PACKET = old_packet

    # Reproduce the verifier's exact line-128 condition without its output CLI.
    # This changes only process-local text; it is not a second interpreter run.
    with patch.object(sys, "version", sys.version + " (structure metadata-only portability control)"):
        alternate, _ = wrapper.calculate()
    changed_top = [name for name in alternate if alternate[name] != reference[name]]
    changed_runtime = [name for name in alternate["runtime_reproduction"] if alternate["runtime_reproduction"][name] != reference["runtime_reproduction"][name]]
    require(changed_top == ["runtime_reproduction"] and set(changed_runtime) == {"generic_live_execution_python", "wrapper_live_execution_python"}, "metadata control changed another field")
    normalized = copy.deepcopy(alternate)
    for name in changed_runtime:
        normalized["runtime_reproduction"][name] = reference["runtime_reproduction"][name]
    require(normalized == reference, "nonruntime result/source differences")
    try:
        verifier.require(alternate == reference, "v2 wrapper exact scalar/source replay")
    except ValueError as error:
        require(str(error) == "v2 wrapper exact scalar/source replay", "unexpected metadata rejection")
    else:
        raise AssertionError("frozen verifier no longer rejects changed runtime metadata")
    require(runpy.run_path is original_run_path and wrapper.runpy is runpy, "runtime test leaked loader override")

    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    code = {}
    for name, digest in saved["source_sha256"].items():
        if not name.endswith(".py"):
            continue
        committed, staged = git_bytes(commit, name), git_bytes("", name)
        packet_file = Path(name).is_relative_to(PACKET.relative_to(ROOT))
        code[name] = {"sha256": digest, "bytes": (ROOT / name).stat().st_size,
                      "committed_exact": committed is not None and hashlib.sha256(committed).hexdigest() == digest,
                      "staged_exact": staged is not None and hashlib.sha256(staged).hexdigest() == digest,
                      "owned_packet_publication_target": packet_file}
        require(packet_file or code[name]["committed_exact"] or code[name]["staged_exact"], "small shared code lacks publication coverage: " + name)
    require(code[SHARED]["staged_exact"] and code[SHARED]["sha256"] == SHARED_SHA and code[SHARED]["bytes"] == 14143, "shared helper publication fix differs")
    factory = read(FACTORY)
    require(all(sha(ROOT / n) == h for n, h in factory["source_sha256"].items()), "factory facts source join differs")
    require(factory["sources"]["Milescraft_1307"]["facts"]["explicit_13p32_guide_listed"] and all(v is None for v in factory["sources"]["Milescraft_1307"]["not_established_by_read_page"].values()), "factory identity/unknown dimensions boundary differs")
    require(not factory["sources"]["Big_Gator_STD1000DGNP"]["facts"]["includes_13p32"], "excluded model promoted")
    require(all(v is False for v in factory["release"].values()) and all(v == "" for v in factory["actual_observations"].values()), "factory selection/actual/release changed")
    require(all(v is False for v in saved["release"].values()) and all(v == "" for v in saved["actual_observations"].values()), "catalog actual/release changed")
    require(saved["release"] == verified["release"] and saved["preserved"]["current_Z200_and_four_HOLD_stations"] and not saved["preserved"]["current_forces_transferred_to_Z180"], "authority/force boundary differs")
    require(all(not r.get("within_generic_allocation", r.get("within_generic_target")) for r in saved["generic_error_allowance_comparisons"].values()), "unmet allocations lost")
    facts = read(ROOT / read(PACKET / "inputs.json")["catalog_facts_path"])
    pdf = facts["sources"]["FISCH_pen_drill"]["raw_active_cache"]
    require(saved["source_sha256"][pdf["path"]] == pdf["sha256"] and (ROOT / pdf["path"]).stat().st_size == pdf["bytes"], "active ignored cache binding differs")
    picture_text = " ".join(ET.fromstring((PACKET / "result-v3.svg").read_bytes()).itertext())
    require("error budget is exceeded" in picture_text and "Current Z200 remains HOLD" in picture_text, "drawing scope lost")
    require(not common.native_modules() and {name: sha(ROOT / name) for name in pins} == before, "native import or source/history drift")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_Z180_catalog_adapter_structure_review/v2", "review_helper_sha256": sha(OWN),
        "frozen_target_sha256": {**TARGETS, str(FACTORY.relative_to(ROOT)): FACTORY_SHA},
        "findings": [{"severity": "P2", "location": str((PACKET / "verify-v2.py").relative_to(ROOT)) + ":128",
                      "issue": "The corrected verifier still requires identical live Python build strings in the entire result comparison.",
                      "impact": "On another supported Python build, adapter-v2 can reproduce every scalar/source/guard field but verify-v2 rejects before its Decimal/runtime/output checks and receipt creation.",
                      "evidence": {"metadata_only_control": True, "changed_fields_only": ["/runtime_reproduction/" + n for n in changed_runtime], "all_other_fields_exact": True, "rejection": "v2 wrapper exact scalar/source replay", "actual_second_interpreter_run": False},
                      "fix": "Preserve frozen v2 files. In a separate forward verifier, compare saved scalar/source/guard fields exactly while validating and recording the two live runtime strings as provenance; keep the recorded runtime and other runtime_reproduction fields bound."}],
        "integrity": {"direct_source_pins": 30, "verified_source_output_retention_union": len(pins), "unchanged_before_after": True,
                      "retained_current_numerical_sha256": numerical, "review_commit": commit, "small_runtime_code_publication_coverage": code},
        "checks": {"issued_current_runtime_scalar_replay_exact": True, "v1_and_v2_SVG_bytes_identical": True, "saved256_Decimal_corners_reproduced": True,
                   "reused_runtime_controls": runtime_checks, "inert_output_controls": output_controls, "private_loader_and_shared_runpy_isolation": True},
        "scope_and_retention": {"v1_and_first_run_files_and_six_v1_review_files_preserved": True, "wrapper_reuses_v1_math_source_guards_and_drawing": True,
                                "adapter_normalizes_only_generic_execution_python": True, "small_shared_helper_staged_byte_identically": SHARED_SHA,
                                "catalog_packet_bytes_excluding_current_inventory_and_reviews": 174648, "new_v2_five_file_bytes": 50963,
                                "shared_raw_PDF": {**pdf, "primary_URL": facts["sources"]["FISCH_pen_drill"]["url"], "active_ignored_not_copied_archived_or_pruned": True},
                                "factory_comparison_does_not_dimension_select_or_qualify_product": True, "all_three_catalog_error_allocations_remain_unmet": True,
                                "current_Z200_100_bolts_66_screws_HOLD_and_fields_retained": True, "Z180_unadopted_no_force_transfer": True, "actuals_blank_release_false": True},
        "maintained_context": {"before_sha256": context_before, "after_sha256": {name: sha(ROOT / name) for name in contexts}, "parent_may_update_README_and_ledger_during_review": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library source/hash/scalar replay and inert mocks only; no CAD/native/BREP/FEA/global/browser/physical execution or output CLI.",
                   "Metadata-only controls are not execution on another interpreter or a clean-checkout run. Publication coverage records committed/staged/planned owned files at review time.",
                   "Manufacturer facts were reviewed as frozen source records, without new product verification, selection, fit or qualification. The active ignored PDF was hashed only.",
                   "Existing complete native source closures and current numerical fields were not independently re-audited or consumed. Current numerical records were hashed only.",
                   "Original v1 findings/receipts remain immutable; this v2 receipt distinguishes their adapter/publication fixes from the remaining verifier issue. No source/shared docs/model/site changes, staging, commit, cleanup or release."],
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
