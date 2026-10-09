"""Frozen catalog adapter architecture/provenance/retention review; no native IO."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
PUBLICATION_SHA = "9f8241920281107edf8edcf77d96b54ec049a0025a0fb2d053a9b54c4d740f0c"
COMMIT = "df0a3a9d8dbf4f89dea3e1ec54b7c3a56aab2392"
COMMON_SHA = "6d61bef99313cc7a6cd7af223e3c4b5adc2722294e51d8e57a58efce30d13158"
MISSING_CODE = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-corners-v1/lower_bolt_z_v2.py"
MISSING_SHA = "a49bc35aeea241360af9df401bd48cc875ccdd34a6e118e109c06d122f45c095"
RECOVERY_ROOT = Path("/home/mckay-linux/repos/mini-moonboard-cleanup-backups-navigation-v1")
RECOVERY = {"recovery-plan.json": "bcc2e8622fc4be3fe06fb5623e6f18085c657c9509eec027f123b78758a7b0af",
            "required-inputs.json": "7a2fc1e21801263ef3062350469c290cc562f1cb9e35aae352c39eec9fd689da"}


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


def git_contains(path):
    return subprocess.run(["git", "cat-file", "-e", COMMIT + ":" + path], cwd=ROOT, capture_output=True, check=False).returncode == 0


def review():
    inventory_path = PACKET / "controls01/publication-file-inventory.json"
    require(sha(inventory_path) == PUBLICATION_SHA, "frozen publication inventory changed")
    inventory = read(inventory_path)
    require(len(inventory["final_files"]) == 6 and len(inventory["retained_first_run_files"]) == 4, "publication/retention scope differs")
    common_path = PACKET.parent / "independent-review-v1/structure/review.py"
    require(sha(common_path) == COMMON_SHA, "review's reused inert checks changed")
    common = load(common_path, "frozen_generic_fixture_structure_helpers")
    require(not common.native_modules(), "review must start source-only")
    inp, saved, verification = (read(PACKET / name) for name in ("inputs.json", "result-v2.json", "verification-v1.json"))
    files = {str((PACKET / name).relative_to(ROOT)): row["sha256"] for name, row in inventory["files"].items()}
    require(all((PACKET / name).stat().st_size == row["bytes"] for name, row in inventory["files"].items()), "publication byte census differs")
    require(sum(row["bytes"] for row in inventory["files"].values()) == inventory["total_bytes"] == 121444, "permanent volume differs")
    require(saved["source_pin_count"] == len(saved["source_sha256"]) == 25, "25 runtime source pins required")
    require(all(saved["source_sha256"][name] == digest for name, digest in inp["source_sha256"].items()), "input/source binding differs")
    pins = {**saved["source_sha256"], **files, str(inventory_path.relative_to(ROOT)): PUBLICATION_SHA,
            str(common_path.relative_to(ROOT)): COMMON_SHA}
    prior_receipt_path = common_path.with_name("receipt.json")
    require(sha(prior_receipt_path) == "8d7155ebc75fe9404758531ae73a899f37379d55a870e514eecaa904fafe416b", "generic review receipt changed")
    prior = read(prior_receipt_path)
    pins[str(prior_receipt_path.relative_to(ROOT))] = sha(prior_receipt_path)
    pins.update(prior["integrity"]["retained_current_numerical_sha256"])
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins, "frozen source/output/history bytes differ")
    contexts = {name: sha(ROOT / name) for name in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md", "CONTRIBUTING.md", "pyproject.toml")}
    adapter = load(PACKET / "adapter.py", "structure_catalog_adapter_v1")
    verifier = load(PACKET / "verify.py", "structure_catalog_verifier_v1")
    observed = adapter.calculate()
    require(observed == {key: value for key, value in saved.items() if key != "drawing"}, "exact scalar replay differs")
    require(adapter.drawing(saved) == (PACKET / "result-v2.svg").read_bytes(), "SVG byte replay differs")
    require(verifier.decimal_corners(saved) == verification["independent_decimal_checks"], "saved 256-corner replay differs")
    require(verification["passed"] is True and len(verification["output_guard_controls"]) == 8 and verification["verification_method_sha256"] == files[str((PACKET / "verify.py").relative_to(ROOT))], "verification identity/scope differs")
    original_packet = common.PACKET
    common.PACKET = PACKET
    try:
        output_controls = common.output_controls(adapter)
    finally:
        common.PACKET = original_packet

    code_audit = {}
    for name, digest in saved["source_sha256"].items():
        if name.endswith(".py"):
            code_audit[name] = {"sha256": digest, "bytes": (ROOT / name).stat().st_size,
                                "in_review_commit": git_contains(name), "new_packet_target": name == str((PACKET / "adapter.py").relative_to(ROOT))}
    absent_shared = [name for name, row in code_audit.items() if not row["in_review_commit"] and not row["new_packet_target"]]
    require(absent_shared == [MISSING_CODE] and saved["source_sha256"][MISSING_CODE] == MISSING_SHA, "shared code coverage differs from frozen observation")
    require((ROOT / MISSING_CODE).stat().st_size == 14143, "missing code byte count differs")
    recovery = {}
    for name, digest in RECOVERY.items():
        path = RECOVERY_ROOT / name
        require(sha(path) == digest and MISSING_CODE.encode() not in path.read_bytes(), "documented recovery coverage differs")
        recovery[str(path)] = digest
    actual_read_bytes = Path.read_bytes
    def omit_code(path):
        if path == ROOT / MISSING_CODE:
            raise FileNotFoundError(str(path))
        return actual_read_bytes(path)
    with patch.object(Path, "read_bytes", omit_code):
        try:
            adapter.calculate()
        except FileNotFoundError as error:
            require(str(error) == str(ROOT / MISSING_CODE), "unexpected absent-file rejection")
        else:
            raise AssertionError("adapter did not require missing shared code")

    # Only environment provenance changes; independently verify every arithmetic
    # and source field stays identical before exercising the adapter's equality.
    _, _, _, _, _, generic_method, _ = adapter.load()
    _, generic_before, _ = generic_method["evaluate"]()
    with patch.object(sys, "version", sys.version + " (metadata-only portability control)"):
        _, generic_after, _ = generic_method["evaluate"]()
        try:
            adapter.load()
        except ValueError as error:
            require(str(error) == "generic result arithmetic differs", "unexpected metadata-only rejection")
        else:
            raise AssertionError("frozen metadata gate no longer reproduced")
    normalized = copy.deepcopy(generic_after)
    normalized["execution"]["python"] = generic_before["execution"]["python"]
    require(normalized == generic_before, "portability control changed arithmetic/source values")
    require(generic_before["execution"]["python"] == "3.12.3 (main, Aug 31 2026, 10:18:26) [GCC 13.3.0]", "frozen Python build differs")
    facts = read(ROOT / inp["catalog_facts_path"])
    pdf = facts["sources"]["FISCH_pen_drill"]["raw_active_cache"]
    require(saved["source_sha256"][pdf["path"]] == pdf["sha256"] and (ROOT / pdf["path"]).stat().st_size == pdf["bytes"] == 87148, "shared raw-cache binding differs")
    history = read(PACKET / "development-v1/record.json")
    require(history["producer_sha256"] == inventory["files"]["development-v1/adapter.py"]["sha256"] and history["outputs"] == {name: inventory["files"][name]["sha256"] for name in ("result.json", "result.svg")}, "first-run recovery ownership differs")
    first = read(PACKET / "result.json")
    require(first["source_sha256"][str((PACKET / "adapter.py").relative_to(ROOT))] == history["producer_sha256"], "first-run producer history relabeled")

    require(all(value is False for value in saved["release"].values()) and saved["release"] == inp["release"] == verification["release"], "release boundary differs")
    require(all(value == "" for value in saved["actual_observations"].values()), "actual observations populated")
    require(saved["preserved"]["current_forces_transferred_to_Z180"] is False and saved["preserved"]["current_Z200_and_four_HOLD_stations"] is True, "force/current authority transfer differs")
    require(all(not row.get("within_generic_allocation", row.get("within_generic_target")) for row in saved["generic_error_allowance_comparisons"].values()), "generic exceedances lost")
    require(saved["FISCH_nominal_comparison"]["guided_handheld_use_or_actual_fit_qualified"] is False and all(row["actual_bit_fit_established"] is False for row in saved["configured_ID_cases"]), "nominal catalog dimensions promoted to actual fit")
    require(saved["clamps"]["actual_clamp_geometry_and_force_qualified"] is False and saved["cap_and_mounting"]["mount_hole_material_fit_retention_and_stiffness_qualified"] is False and saved["reach_and_guidance"]["effective_guidance_observed_or_catalog_guaranteed"] is False, "fixture qualification transferred")
    svg = ET.fromstring((PACKET / "result-v2.svg").read_bytes())
    text = " ".join(svg.itertext())
    require("error budget is exceeded" in text and "Current Z200 remains HOLD" in text and "No frame change, tool selection" in text, "drawing claims differ")
    require(not common.native_modules(), "source/scalar review imported native modules")
    require({name: sha(ROOT / name) for name in pins} == before, "source/output/history changed during review")
    require({name: sha(ROOT / name) for name in contexts} == contexts, "maintained context drifted")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    staged = subprocess.run(["git", "show", ":" + MISSING_CODE], cwd=ROOT, capture_output=True, check=True).stdout
    require(hashlib.sha256(staged).hexdigest() == MISSING_SHA, "parent-staged publication helper differs")
    path = str((PACKET / "adapter.py").relative_to(ROOT))
    return {
        "schema": "eoere_Z180_catalog_fixture_architecture_review/v1", "review_helper_sha256": sha(OWN),
        "publication_inventory": {"path": str(inventory_path.relative_to(ROOT)), "sha256": PUBLICATION_SHA},
        "frozen_six_target_sha256": {name: inventory["files"][name]["sha256"] for name in inventory["final_files"]},
        "retained_first_run_sha256": {name: inventory["files"][name]["sha256"] for name in inventory["retained_first_run_files"]},
        "context_sha256": contexts,
        "findings": [
            {"severity": "P2", "location": path + ":54", "issue": "The required shared capsule helper is absent from the reviewed Git commit and documented recovery map.",
             "impact": "Publishing the listed catalog files cannot make the recorded reproduction command run on a clean checkout, even after restoring the intentionally ignored PDF.",
             "call_path": "adapter.load -> generic design.evaluate -> prepare -> verify/pure capsule helper; generic design.py:81-83",
             "required_path": MISSING_CODE, "required_sha256": MISSING_SHA, "required_bytes": 14143,
             "evidence": "Absent-file mock reproduces FileNotFoundError; no other pre-existing .py source pin lacks committed coverage.",
             "fix": "Publish the existing shared helper unchanged at its current path, or add an exact bound restoration path; preserve catalog/generic/history bytes. Keep the shared PDF cache separate and document its recovery boundary."},
            {"severity": "P2", "location": path + ":57", "issue": "Generic arithmetic comparison also requires an identical live sys.version build string.",
             "impact": "Another supported Python 3.12 patch/build rejects the adapter despite identical source pins and scalar outputs; the reproduction command does not bind that exact interpreter build.",
             "evidence": {"only_changed_field": "execution.python", "error": "generic result arithmetic differs", "frozen_build": generic_before["execution"]["python"], "all_other_result_fields_identical": True},
             "fix": "Preserve originals; compare arithmetic/source fields independently of environment provenance and record live runtime separately, or explicitly provide and bind the exact required interpreter build."}],
        "integrity": {"direct_source_pins": 25, "verified_source_output_retention_union": len(pins), "unchanged_before_after": True, "review_commit": COMMIT, "small_runtime_code_audit": code_audit, "documented_recovery_maps_checked": recovery},
        "later_parent_publication_fix": {"shared_helper_staged_byte_identically": True, "sha256": MISSING_SHA, "original_pre_fix_assessment_commit_and_packet_not_relabelled": True, "interpreter_comparison_correction_not_reviewed_here": True},
        "checks": {"result_and_SVG_replay_exact": True, "saved256_Decimal_corners_reproduced": True, "inert_output_controls": output_controls, "native_or_browser_execution": False},
        "scope_and_retention": {"generic_scalar_helpers_reused_without_whole_CAD_import": True, "generic_six_files_preserved": True, "original_first_run_and_lint_failure_preserved": True, "permanent_packet_bytes": inventory["total_bytes"], "shared_raw_PDF": {**pdf, "tracked_in_review_commit": git_contains(pdf["path"]), "primary_recovery_URL": facts["sources"]["FISCH_pen_drill"]["url"], "active_ignored_and_not_copied": True}, "generic_error_allocations_remain_unmet": True, "catalog_values_are_not_actual_product_fit": True, "current_Z200_geometry_100_bolts_66_screws_HOLD_and_fields_preserved": True, "current_forces_not_transferred": True, "actuals_blank_and_release_flags_false": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["Standard-library source/hash/scalar replay and inert controls only; no native/CAD/BREP/FEA/global/browser/physical execution.", "The interpreter portability control changes only metadata; no second interpreter or clean-machine run is claimed.", "No independent manufacturer requalification or new catalog selection. Ignored raw PDF bytes were authenticated without rendering/copying; current numerical records were hashed only.", "Original frozen catalog/generic/history records and reviews remain active and unchanged. Parent owns any later publication fix; this receipt describes the reviewed commit and target.", "No source/shared docs/site/model edits, cleanup, staging or commit; no current force transfer or fixture/strength/physical acceptance."],
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
