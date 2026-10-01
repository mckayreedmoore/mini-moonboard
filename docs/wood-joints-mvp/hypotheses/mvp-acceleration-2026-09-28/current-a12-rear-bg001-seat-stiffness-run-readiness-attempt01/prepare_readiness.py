#!/usr/bin/env python3
"""Verify and snapshot the read-only inputs for one parent-owned sensitivity run."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
PACKET = Path(__file__).resolve().parent
SERIES = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
VARIANT = SERIES / "current-a12-rear-bg001-seat-stiffness-variant-attempt01"
BASELINE = SERIES / "current-springa-selected-floor-a12-rear-attempt03"
PARENT_REVIEW = SERIES / "current-sensitivity-response-core-parent-review-attempt01/final-method-review.json"
PARENT_CHECK = SERIES / "current-springa-selected-floor-parent-response-audit-attempt01/check.py"

INPUT_PINS = {
    "variant_model_json": (VARIANT / "model.json", "ddb65e7630eb0f6f5f44ae762eb00c61a53642122a62376f46959ccc7b1eccbb"),
    "variant_deck": (VARIANT / "model.inp", "dd38c90d0aef23e109449992061e885cc79278b26bc42ab1dd1e63d58cf5383c"),
    "variant_manifest": (VARIANT / "variant.json", "ba9d632f61ed218dca8d8ad503270ad516d6881a458f06925566b635856e57b2"),
    "variant_preparer": (VARIANT / "prepare.py", "6ba100b0b8afdb360eb125883053c732071239c1747a198959523761d68af724"),
    "validator": (VARIANT / "validate_sensitivity_input.py", "5add545272a777bf239beec91aeb1f9f2347118fa5040419f374e6528c7a03d3"),
    "response_core_fork": (VARIANT / "sensitivity_response_core.py", "44e2fa9cda9d286ae991a022f894e5ea2dea8693e0be3042cd46a3fdf868566b"),
    "input_verifier": (VARIANT / "verify_sensitivity_input.py", "361bfed2bf2b9f5e43c098b7a1a2b78223685a27a9d12b4ec334c18d525cf34c"),
    "input_verifier_report": (VARIANT / "sensitivity_input_contract_check.json", "244b1ba04ad19eb9d2b771c9a4ec409de373537208b495ab6ea88741c9a73bc3"),
    "parent_method_review": (PARENT_REVIEW, "50d2cdda20d3fe6d96059f59bc54dfbb5e9617bf360aca192d26cd87a661f81a"),
    "baseline_model_json": (BASELINE / "model.json", "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8"),
    "baseline_deck": (BASELINE / "model.inp", "e8f7376817daa1e3ac0b7d5f85c52b16115c2cef39291486d1800e0e847e0aff"),
    "baseline_response": (BASELINE / "response.json", "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274"),
    "baseline_freeze": (BASELINE / "freeze.json", "a362e551a39afcaed06ecbf0a0f1f18858fbc8677bdf2a927652b543ac67eb03"),
    "floor_screen": (SERIES / "current-springa-selected-floor-branch-screen-attempt02/screen.json", "231b4fa22128bb01ae08f9bf21e6fec9ccb9c7578724781fae01a6f79856ed93"),
    "six_case_register": (SERIES / "current-six-case-source-load-register-attempt01/register.json", "7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508"),
    "source_compliance_sensitivity": (SERIES / "current-post-spine-compliance-sensitivity-attempt01/sensitivity.json", "0994ae3f5a54c6eb985141c54eb3d38d455678482ed2ac5a6205e2a84096a9c0"),
    "source_compliance_sensitivity_producer": (SERIES / "current-post-spine-compliance-sensitivity-attempt01/produce.py", "7f00f6e5679e36eb5233dc5247a2dcf3aeb0ea0d5078f82dae4722ba7f5718d5"),
    "effective_stiffness_property_source": (ROOT / "fea/wood_joint_reduced_properties.py", "26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1"),
    "solver_profile": (ROOT / "fea/calculix_223/solver-profile.json", "f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c"),
    "solver_manual": (ROOT / "fea/generated/ccx_2.23.pdf", "a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330"),
    "serialized_native_runner": (ROOT / "fea/wood_joint_reduced_native.py", "ff7a81bc604090a4791eb584f9998bc76a35be2ac3ebaed15be970291583ff61"),
    "pinned_711_response": (SERIES / "current-springa-zero-u-token-response-audit-attempt01/response_audit.py", "711fa96e8faff12dc4b21fa939ae28822be8abba65bc12a896b558f0a54bfff0"),
    "pinned_711_recovery": (SERIES / "current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py", "bdcfa2dd85e152503b740a2f49bb1de6b67462565eb610ff5ee451990335a77d"),
    "baseline_response_audit": (SERIES / "current-springa-selected-floor-response-audit-attempt03/response_audit.py", "41536568057101155290880e1d6228ea9eda8fc283678cd06ee3acb5945797ed"),
    "baseline_stable_recovery": (SERIES / "current-springa-frame-response-audit-attempt01/response_audit.py", "b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c"),
    "independent_all_body_check": (PARENT_CHECK, "7ff46055915e01d945cefe728cc4a4b146b05836976620c7f54100f586130b80"),
}

SNAPSHOT_RELS = [
    "AGENTS.md",
    "fea/wood_joint_reduced_native.py",
    "fea/calculix_223/solver-profile.json",
    "fea/generated/ccx_2.23.pdf",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/prepare.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-compliance-sensitivity-attempt01/produce.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-compliance-sensitivity-attempt01/sensitivity.json",
    "fea/wood_joint_reduced_properties.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/variant.json",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/validate_sensitivity_input.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/sensitivity_response_core.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/verify_sensitivity_input.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-variant-attempt01/sensitivity_input_contract_check.json",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-sensitivity-response-core-parent-review-attempt01/final-method-review.json",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-parent-response-audit-attempt01/check.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt03/response_audit.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-response-audit-attempt01/response_audit.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-zero-u-token-response-audit-attempt01/response_audit.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-zero-u-token-response-audit-attempt01/stable_response_audit.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-branch-screen-attempt02/screen.json",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/README.md",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/prepare_readiness.py",
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/audit_variant_run.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    for label, (path, expected) in INPUT_PINS.items():
        require(path.is_file(), f"missing {label}: {path}")
        actual = sha(path)
        require(actual == expected, f"{label} hash mismatch: {actual} != {expected}")

    variant = json.loads((VARIANT / "model.json").read_text())
    manifest = json.loads((VARIANT / "variant.json").read_text())
    input_check = json.loads((VARIANT / "sensitivity_input_contract_check.json").read_text())
    method_review = json.loads(PARENT_REVIEW.read_text())
    profile = json.loads((ROOT / "fea/calculix_223/solver-profile.json").read_text())
    require(variant.get("schema") == "current_springa_selected_floor_input_model/v1", "variant schema changed")
    require(variant.get("case_id") == "a12-rear", "prepared input is not A12-rear")
    require(variant.get("candidate") == "compact-floor-flush-wood-joints-development", "candidate changed")
    require(variant.get("geometry_revision_id") == "led-clearance-2x6-runner-seated-blocks-v1", "revision changed")
    branch = variant.get("floor_branch_metadata", {})
    require(branch.get("selected_cell_count") == 25 and branch.get("inactive_cell_count") == 75, "expected copied 25/75 floor mask")
    require(branch.get("status") == "proposed_diagnostic_mask_only", "floor mask must remain diagnostic-only")
    require(branch.get("selected_branch_screen_status") == "REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH", "floor screen status changed")
    require(branch.get("screen_packet_sha256") == INPUT_PINS["floor_screen"][1], "floor screen pin differs")
    require(branch.get("selected_branch_screen_outputs_adopted") is False, "floor screen output was adopted")
    require(branch.get("automatic_mask_iteration_authorized") is False, "automatic mask iteration unexpectedly authorized")
    require(manifest.get("native_solve_executed") is False and manifest.get("mechanical_acceptance") is False, "variant manifest overclaims")
    require(input_check.get("status") == "PASS_EXACT_TWO_TIE_SENSITIVITY_INPUT_CONTRACT", "input validation report is not passing")
    require(input_check.get("new_native_output_generated") is False and input_check.get("corner_demands_usable") is False, "input report overclaims a response")
    require(method_review.get("status") == "PASS_PARENT_FINAL_SENSITIVITY_METHOD_REVIEW", "parent method review status changed")
    require(method_review.get("unchanged_existing_functions_except_entrypoint_and_added_loader_pin") is True, "parent method review details changed")
    require(method_review.get("physical_audit_statements_unchanged_before_final_provenance") == 27, "parent-reviewed mechanical gate body changed")
    require(method_review.get("parent_replayed_verifier") is True and method_review.get("native_readiness") is False, "parent review scope changed")
    require(profile.get("version") == "2.23" and profile.get("image_id") == "sha256:31336f517557f5dd5f97d85b1e6e15947fd1c10b44edc1364dbba4c1a5ab6c38", "pinned native profile changed")
    require(profile.get("binary_sha256") == "c6882d262b44525a563250673420dff1506c41b95e6d82d50392f9af26111863", "pinned solver binary changed")

    snapshot_hashes = {}
    for relative in SNAPSHOT_RELS:
        source = ROOT / relative
        require(source.is_file(), f"missing snapshot source: {relative}")
        destination = PACKET / "sources" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        snapshot_hashes[relative] = sha(destination)
        require(snapshot_hashes[relative] == sha(source), f"snapshot copy mismatch: {relative}")

    contract = {
        "schema": "a12_rear_bg001_stiffness_sensitivity_parent_readiness_inputs/v1",
        "status": "PREPARED_FOR_PARENT_REVIEW_ONLY",
        "parent_native_readiness": False,
        "native_freeze_created": False,
        "native_solve_executed": False,
        "mechanical_acceptance": False,
        "qualified_for_design": False,
        "campaign_scope": "The six authenticated no-slip case program remains the project scope. This single A12-rear response sensitivity neither replaces nor satisfies the other cases.",
        "run_scope": {
            "case_id": "a12-rear",
            "candidate": variant["candidate"],
            "geometry_revision_id": variant["geometry_revision_id"],
            "purpose": "One conditional response sensitivity for the two BG001 left-post outer-seat axial ties at the source-derived 2401.714359616974 N/mm effective stiffness.",
            "max_launches": 1,
            "timeout_seconds": 240,
            "memory": "4g",
            "no_automatic_retry": True,
        },
        "prepared_inputs": {
            "model_json_path": str((VARIANT / "model.json").relative_to(ROOT)),
            "model_json_sha256": INPUT_PINS["variant_model_json"][1],
            "deck_path": str((VARIANT / "model.inp").relative_to(ROOT)),
            "deck_sha256": INPUT_PINS["variant_deck"][1],
            "variant_manifest_path": str((VARIANT / "variant.json").relative_to(ROOT)),
            "variant_manifest_sha256": INPUT_PINS["variant_manifest"][1],
        },
        "two_tie_override": {
            "source_scenario": "Current source-derived local nominal-ring case A, scenario index 4; 190000 MPa steel; wood influence depth 2.0 times equivalent washer-area diameter. Uncalibrated response sensitivity only, not a physical bound.",
            "stiffness_n_per_mm": 2401.714359616974,
            "baseline_stiffness_n_per_mm": 4670.054188242363,
            "ratio_to_baseline": 0.5142797626767777,
            "groups": ["SPR1771", "SPR1772"],
            "force_law": "k * max(q_mm, 0), q = u(second projection) - u(first projection)",
            "geometry_load_support_other_springs_and_all_348_bilateral_rows": "unchanged exact source inputs",
        },
        "floor_mask": {
            "status": "PROVISIONAL_COPIED_MASK_NOT_ADOPTED",
            "selected_cell_count": 25,
            "inactive_separated_cell_count": 75,
            "screen_path": branch["screen_packet_path"],
            "screen_sha256": INPUT_PINS["floor_screen"][1],
            "screen_status": branch["selected_branch_screen_status"],
            "native_output_must_recheck_strict_complementarity_each_increment": True,
            "mask_must_not_be_auto_iterated_or_treated_as_physical_acceptance": True,
        },
        "method_review": {
            "path": str(PARENT_REVIEW.relative_to(ROOT)),
            "sha256": INPUT_PINS["parent_method_review"][1],
            "status": method_review["status"],
            "physical_audit_statements_unchanged": 27,
        },
        "no_standard_711_context_claim": {
            "standard_711_case_context_validation_passed": False,
            "reason": "The exact A12-rear sensitivity path uses the sealed input-validator contract. It does not synthesize the missing all-bearing controls context required by the standard 711 case-context path.",
        },
        "source_hashes": {label: expected for label, (_, expected) in INPUT_PINS.items()},
        "frozen_source_snapshot_sha256": snapshot_hashes,
        "freeze_spec": {
            "schema": "wood_joint_reduced_native_freeze/v1",
            "must_preserve_exact_model_and_deck_bytes": True,
            "required_fields": ["scope", "candidate", "geometry_revision_id", "case_id", "solver_profile", "source_sha256", "files_sha256", "native_solve_executed", "mechanical_acceptance"],
            "files_sha256": {"model.json": INPUT_PINS["variant_model_json"][1], "model.inp": INPUT_PINS["variant_deck"][1]},
            "additional_run_root_file_sha256_required": ["readiness-source-snapshot-manifest.json"],
            "source_sha256_required": "Every source_snapshots entry plus readiness_contract_snapshot from source-snapshot-manifest.json.",
            "solver_profile_path": "fea/calculix_223/solver-profile.json",
            "solver_profile_sha256": INPUT_PINS["solver_profile"][1],
            "source_snapshot_root": "run-directory/sources/<repository-relative-path>",
            "must_not_change_model_metadata_or_serialize_a_different_record": True,
            "native_solve_executed": False,
            "mechanical_acceptance": False,
        },
        "runner": {
            "path": "fea/wood_joint_reduced_native.py",
            "sha256": INPUT_PINS["serialized_native_runner"][1],
            "api": "fea.wood_joint_reduced_native.launch(run_dir, run_id, parent_readiness_review, timeout_seconds=240, memory='4g')",
            "locks_and_ledger": "The runner checks the pinned solver image/binary and takes the repository's existing serialized native-run lock/ledger. Parent must recheck the live slot at launch.",
        },
        "postrun": {
            "fork_audit_script": "audit_variant_run.py",
            "fork_audit_script_sha256": None,
            "command": "OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 <this-packet>/audit_variant_run.py <frozen-run-directory>",
            "independent_all_50_body_check_source": str(PARENT_CHECK.relative_to(ROOT)),
            "independent_all_50_body_check_sha256": INPUT_PINS["independent_all_body_check"][1],
            "independent_all_50_body_check_command": "OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 <frozen-run-directory>/sources/" + str(PARENT_CHECK.relative_to(ROOT)) + " <frozen-run-directory>/model.json <frozen-run-directory>/response.json",
            "expected_response_output": "<frozen-run-directory>/response.json",
            "expected_independent_balance_report": "<frozen-run-directory>/sources/" + str(PARENT_CHECK.parent.relative_to(ROOT)) + "/audit.json",
        },
        "limits": [
            "The sensitivity is one declared conditional parameter point, not a statistical, calibrated, or physical stiffness lower bound.",
            "The selected 25-cell floor mask remains a copied proposal; only strict native complementarity rechecked in every increment permits this conditional response audit to pass.",
            "No force is usable unless all unchanged source-law, MPC, retained SPRING2, floor, and every-body/global balance gates pass.",
            "This single A12-rear run does not establish six-case sensitivity robustness, contact uniqueness/recontact, connection resistance, build readiness, or acceptance.",
        ],
    }
    contract["postrun"]["fork_audit_script_sha256"] = sha(PACKET / "audit_variant_run.py")
    contract_path = PACKET / "readiness-contract.json"
    contract_path.write_text(json.dumps(contract, indent=2, allow_nan=False) + "\n")
    contract_rel = str(contract_path.relative_to(ROOT))
    contract_snapshot = PACKET / "sources" / contract_rel
    contract_snapshot.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(contract_path, contract_snapshot)
    snapshot_manifest = {
        "schema": "a12_rear_bg001_sensitivity_readiness_source_snapshots/v1",
        "status": "INPUT_SNAPSHOTS_ONLY_NO_FREEZE_OR_RUN",
        "source_snapshots": snapshot_hashes,
        "readiness_contract_snapshot": {
            "repository_relative_path": contract_rel,
            "sha256": sha(contract_snapshot),
        },
    }
    (PACKET / "source-snapshot-manifest.json").write_text(json.dumps(snapshot_manifest, indent=2) + "\n")
    print(json.dumps({
        "status": contract["status"],
        "parent_native_readiness": False,
        "variant_model_sha256": contract["prepared_inputs"]["model_json_sha256"],
        "variant_deck_sha256": contract["prepared_inputs"]["deck_sha256"],
        "source_snapshot_count": len(snapshot_hashes),
        "readiness_contract_sha256": sha(contract_path),
        "source_snapshot_manifest_sha256": sha(PACKET / "source-snapshot-manifest.json"),
        "readiness_contract": str((PACKET / "readiness-contract.json").relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
