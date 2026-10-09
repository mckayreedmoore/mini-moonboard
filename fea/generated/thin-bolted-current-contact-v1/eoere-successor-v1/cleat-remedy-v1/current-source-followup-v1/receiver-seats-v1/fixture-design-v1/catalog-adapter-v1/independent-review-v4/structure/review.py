"""Bounded v4 verifier architecture/publication review; inert preflight only."""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import importlib.util
import inspect
import io
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
OWN = Path(__file__).resolve()
ROOT = next(p for p in OWN.parents if (p / "AGENTS.md").is_file())
PACKET = OWN.parents[2]
TARGETS = {
    "verify-v4.py": "7d12b93a566807bdb6ea855f15339bfd11dbc11b7ff12c51e098b25d3d8288b3",
    "verification-v4.json": "d493675b10ed82518371ef23089850114a59025b96007b9f12e50ec207a6367f",
    "controls01/publication-file-inventory-v4.json": "6d35166082919605b1d61684c212e6ff0d5f07620a38b07538dfe4b5f5d438b5",
}
PREVIOUS_HELPER = "7d781b62430693e4ba1fab7454cc73a83556d6ec64fce48aba7ef88e2451968d"
PREVIOUS_RECEIPT = "4fa449b8650c882161c8a34a17f22ee7eac5225fd5045060db9ce3bf007c9e08"


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
    prior_path = PACKET / "independent-review-v3/structure/review.py"
    prior_receipt_path = prior_path.with_name("receipt.json")
    require(sha(prior_path) == PREVIOUS_HELPER and sha(prior_receipt_path) == PREVIOUS_RECEIPT, "prior structure proof changed")
    prior = load(prior_path, "catalog_v3_structure_utilities_only")
    proof = read(prior_receipt_path)
    inventory, verified, saved = (read(PACKET / n) for n in ("controls01/publication-file-inventory-v4.json", "verification-v4.json", "result-v3.json"))
    pins = {str((PACKET / n).relative_to(ROOT)): h for n, h in TARGETS.items()}
    for mapping in (saved["source_sha256"], verified["preserved_available_review_sha256"],
                    {str((PACKET / n).relative_to(ROOT)): r["sha256"] for n, r in inventory["files"].items()}):
        for name, digest in mapping.items():
            require(name not in pins or pins[name] == digest, "source/retention pin contradiction")
            pins[name] = digest
    common_path = PACKET.parent / "independent-review-v1/structure/review.py"
    require(sha(common_path) == prior.COMMON_SHA, "original common helpers changed")
    common = prior.load(common_path, "catalog_v4_source_only_import_detector")
    require(not common.native_modules(), "source-only process required")
    common_receipt = common_path.with_name("receipt.json")
    require(sha(common_receipt) == "8d7155ebc75fe9404758531ae73a899f37379d55a870e514eecaa904fafe416b", "generic proof changed")
    pins[str(common_path.relative_to(ROOT))] = sha(common_path)
    pins[str(common_receipt.relative_to(ROOT))] = sha(common_receipt)
    v2_receipt = PACKET / "independent-review-v2/structure/receipt.json"
    require(sha(v2_receipt) == prior.PREVIOUS_RECEIPT, "v2 source/math proof changed")
    pins.update(read(v2_receipt)["integrity"]["retained_current_numerical_sha256"])
    probes = [inventory["active_ignored"]["prior"]["positive_actual_main_probe"], inventory["active_ignored"]["positive_actual_main_probe"]]
    for probe in probes:
        pins[probe["path"]] = probe["sha256"]
    before = {name: sha(ROOT / name) for name in pins}
    require(before == pins and len(saved["source_sha256"]) == verified["source_pin_count"] == 30, "frozen sources/targets differ")
    require(len(inventory["files"]) == 24 and all((PACKET / n).stat().st_size == r["bytes"] for n, r in inventory["files"].items()), "publication census differs")
    require(sum(r["bytes"] for r in inventory["files"].values()) == inventory["total_bytes_excluding_this_inventory_and_parent_owned_reviews"] == 250361, "publication volume differs")
    require(verified["verification_method_sha256"] == TARGETS["verify-v4.py"] and verified["passed"], "issued v4 identity differs")
    contexts = [ROOT / n for n in ("AGENTS.md", "docs/wood-joints-mvp/README.md", "docs/wood-joints-mvp/completion-ledger.md")]
    contexts.append(PACKET.parent.parent / "hardware-followup-v1/factory-guide-sources-v1.json")
    context_before = {str(p.relative_to(ROOT)): sha(p) for p in contexts}

    verifier = prior.load(PACKET / "verify-v4.py", "catalog_v4_structure_target")
    old_tree, new_tree = (ast.parse((PACKET / n).read_bytes()) for n in ("verify-v3.py", "verify-v4.py"))
    def function(tree, name):
        return next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
    require(ast.dump(function(old_tree, "compare_replay")) == ast.dump(function(new_tree, "compare_replay")), "proven runtime comparison changed")
    require(verifier.LIVE_RUNTIME_FIELDS == ("generic_live_execution_python", "wrapper_live_execution_python"), "normalization expanded")
    require(inspect.signature(verifier.main).parameters["run_main_controls"].default is False, "nested main can recurse into controls by default")
    main_ast = function(new_tree, "main")
    control_call = next(node for node in ast.walk(main_ast) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "actual_main_controls")
    require(control_call.lineno > max(node.lineno for node in ast.walk(main_ast) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "compare_replay"), "controls precede normal comparison")
    entry = new_tree.body[-1]
    require(isinstance(entry, ast.If) and isinstance(entry.body[0], ast.Expr)
            and isinstance(entry.body[0].value, ast.Call)
            and entry.body[0].value.func.id == "main"
            and ast.literal_eval(entry.body[0].value.keywords[0].value) is True
            and entry.body[0].value.keywords[0].arg == "run_main_controls", "actual entrypoint does not enable guarded controls")
    cases = [
        ("help", ["--help"], SystemExit, "0"),
        ("invalid_parent", ["--out", str(PACKET / "controls01/_v4_structure_absent.json")], ValueError, "owned canonical JSON receipt required"),
        ("occupied_output", ["--out", str(PACKET / "verification-v3.json")], ValueError, "fresh receipt required"),
        ("changed_source", ["--out", str(PACKET / "_v4_structure_absent.json")], ValueError, "frozen v2/v3 packet or inventories differ"),
    ]
    inert = []
    for label, argv, error_type, message in cases:
        with contextlib.ExitStack() as stack:
            controls = stack.enter_context(patch.object(verifier, "actual_main_controls", side_effect=AssertionError("unexpected controls")))
            loader = stack.enter_context(patch.object(verifier.runpy, "run_path", side_effect=AssertionError("unexpected producer loading")))
            mkdir = stack.enter_context(patch.object(Path, "mkdir", side_effect=AssertionError("unexpected mkdir")))
            opened = stack.enter_context(patch.object(Path, "open", side_effect=AssertionError("unexpected open")))
            if label == "changed_source":
                stack.enter_context(patch.object(verifier, "sha", return_value="0"*64))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            stack.enter_context(contextlib.redirect_stderr(io.StringIO()))
            try:
                verifier.main(argv, run_main_controls=True)
            except error_type as error:
                require(str(error) == message, "unexpected early-guard outcome: " + label)
            else:
                raise AssertionError("early guard accepted: " + label)
            require(not any(mock.called for mock in (controls, loader, mkdir, opened)), "early guard attempted a side effect")
            inert.append(label)
    require(not common.native_modules(), "inert preflight imported native code")

    main_proof = verified["actual_main_controls"]
    require(main_proof["positive_probe_receipt_active_ignored"] == probes[1]["path"] and main_proof["positive_probe_receipt_sha256"] == probes[1]["sha256"], "v4 raw probe binding differs")
    require(main_proof["entrypoint_preflight_controls"]["actual_dunder_main_cases"] == [
        {"case": label, "expected_exit_code": code, "child_launch_attempts": 0, "file_mutation_attempts": 0}
        for label, code in (("help", 0), ("invalid_parent", 1), ("occupied_output", 1))], "retained entrypoint proof differs")
    publication = []
    for probe in probes:
        path = ROOT / probe["path"]
        raw = read(path)
        require(raw["passed"] and raw["recorded_runtime_provenance"] == saved["runtime_reproduction"], "retained probe provenance differs")
        staged = subprocess.run(["git", "show", ":" + probe["path"]], cwd=ROOT, capture_output=True, check=False)
        publication.append({"path": probe["path"], "sha256": probe["sha256"], "bytes": path.stat().st_size,
                            "parent_explicitly_plans_publication_at_original_path": True,
                            "staged_exact_at_review": staged.returncode == 0 and hashlib.sha256(staged.stdout).hexdigest() == probe["sha256"],
                            "historical_inventory_ignored_description_preserved": True})
    shared = "fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-corners-v1/lower_bolt_z_v2.py"
    staged_shared = subprocess.run(["git", "show", ":" + shared], cwd=ROOT, capture_output=True, check=True).stdout
    require(hashlib.sha256(staged_shared).hexdigest() == saved["source_sha256"][shared] == "a49bc35aeea241360af9df401bd48cc875ccdd34a6e118e109c06d122f45c095", "shared scalar dependency publication changed")
    require(proof["checks"]["reused_same_source_Decimal_endpoint_corners"] == 256 and proof["checks"]["private_loader_and_ambient_runpy_sys_version_isolation"], "prior unchanged math/isolation proof absent")
    require(verified["normalized_wrapper_comparison_paths_only"] == ["/runtime_reproduction/" + n for n in verifier.LIVE_RUNTIME_FIELDS]
            and verified["recorded_generic_runtime_and_every_other_field_exact"], "runtime/engineering provenance boundary differs")
    require(all(v is False for v in saved["release"].values()) and saved["release"] == verified["release"]
            and all(v == "" for v in saved["actual_observations"].values()), "acceptance/actuals changed")
    require(saved["preserved"]["current_Z200_and_four_HOLD_stations"] and not saved["preserved"]["current_forces_transferred_to_Z180"], "current authority/actions transferred")
    require({name: sha(ROOT / name) for name in pins} == before, "source/target/history changed")
    ruff = subprocess.run([str(ROOT / ".venv/bin/ruff"), "check", "--no-cache", str(OWN)], cwd=ROOT, capture_output=True, text=True, check=False)
    require(ruff.returncode == 0, "own Ruff failed: " + ruff.stdout + ruff.stderr)
    return {
        "schema": "eoere_Z180_catalog_adapter_structure_review/v4", "review_helper_sha256": sha(OWN), "frozen_new_target_sha256": TARGETS, "findings": [],
        "integrity": {"direct_producer_source_pins": 30, "verified_source_target_review_retention_union": len(pins), "unchanged_before_after": True,
                      "previous_v3_structure_receipt_sha256": PREVIOUS_RECEIPT},
        "checks": {"comparison_function_AST_identical_to_v3": True, "exact_two_live_text_fields_only": True,
                   "main_default_controls_false_actual_entrypoint_true": True, "controls_follow_argument_destination_source_and_normal_comparison": True,
                   "inert_main_early_guards_with_no_loader_controls_open_or_mkdir": inert,
                   "retained_actual_entrypoint_3_controls_real_main_8_rejections_and_positive_probe_authenticated": True,
                   "prior_256_Decimal_math_7_runtime_8_output_and_namespace_proofs_reused": True},
        "publication_contract": {"owned_inventory_files": 24, "owned_inventory_file_bytes_excluding_current_inventory_and_reviews": 250361,
                                 "required_small_bound_probe_additions": publication, "required_probe_total_bytes": sum(row["bytes"] for row in publication),
                                 "parent_owns_final_staging_and_exact_publication": True, "shared_14143_byte_capsule_helper_staged_exact": True,
                                 "other_probes_and_PDF_remain_active_ignored_with_existing_PDF_restore_instructions": True,
                                 "original_inventories_versions_reviews_failed_preflights_and_probe_paths_not_relabelled": True},
        "scope": {"engineering_math_producer_result_and_SVG_unchanged": True, "recorded_generic_runtime_and_all_nonlive_fields_strict": True,
                  "current_Z200_actions_HOLD_100_bolts_66_screws_and_unadopted_Z180_boundary_preserved": True,
                  "actuals_blank_release_false_no_force_or_physical_acceptance_transfer": True},
        "context": {"before_sha256": context_before, "after_sha256": {str(p.relative_to(ROOT)): sha(p) for p in contexts}, "parent_owned_prose_and_factory_facts_not_frozen_targets": True},
        "ruff": {"command": ".venv/bin/ruff check --no-cache " + str(OWN.relative_to(ROOT)), "exit_code": ruff.returncode, "output": ruff.stdout.strip()},
        "limits": ["New bounded source/AST and inert preflight checks only; no target artifact-writing CLI, target child subprocess, CAD/native/BREP/FEA/global/browser/physical execution.",
                   "Prior same-source scalar/Decimal, runtime, output and isolation proofs are reused, not reissued. Retained real-main/entrypoint probes are authenticated without rerunning them.",
                   "Small probe publication is the parent's explicit plan, with staged status recorded at review time; final publication remains parent-owned. No second-interpreter or clean-checkout execution is claimed.",
                   "No target/shared docs/site/index edits, staging, commit, cleanup, archive/prune, engineering input changes or acceptance."],
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
