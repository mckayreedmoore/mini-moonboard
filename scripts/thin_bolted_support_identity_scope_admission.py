"""Authenticate a distinct outer identity scope around frozen chain mechanics.

Historical schedule metadata retains its own immutable ancestor identities.
Every other nested state label must identify the current field. The unchanged
chain gate receives the exact original bytes as a subordinate mechanics check;
its receipt is preserved under its real schema, never projected or relabelled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts import thin_bolted_support_chain_admission as chain

ROOT = chain.ROOT
OWN = str(Path(__file__).resolve().relative_to(ROOT))
OWN_TEST = "tests/test_thin_bolted_support_identity_scope_admission.py"
DRIVER = "scripts/run_thin_bolted_support_identity_scope_frame.py"
LOADED_PRODUCER_SHA256 = chain.core.support.digest(Path(__file__))
SCHEMA = "thin_bolted_independent_support_identity_scope_admission/v1"
SUCCESS = "independent_support_identity_scope_face_source_map_law_and_equilibrium_checks_pass"
METHOD_RECEIPT = chain.PACKET / "support-identity-scope-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_identity_scope_method/v1"
HISTORICAL_PATH = "response.support_mask_chain_schedule_v1"
CHAIN_GATE_SHA256 = "660ef5fc88458ce2586ecc4cfb9cec257aa971a7e35dbddf3871ea9701d1ec32"
CHAIN_ARGS = {
    "chain_driver_sha256": "c84470fbcc7f0611aee22df0f1c12985103d7a7d99b02c7172810aad33126bbf",
    "chain_method_sha256": "10e5589d4159d9cd4238c1766d2d5538787179f28c50ffb532c4e2c5aed27b4a",
    "method_receipt_path": chain.METHOD_RECEIPT,
    "method_receipt_sha256": "6bed41e7248ac0f3e72275614236a51acad871c8f0a5f21a7d69b928b850b90a",
}
require, canonical_sha = chain.require, chain.canonical_sha


def source_pins(driver_sha256, method_receipt_path, method_receipt_sha256):
    """Pin the fresh outer method and its unchanged frozen mechanics graph."""
    path = Path(method_receipt_path).resolve()
    require(path == METHOD_RECEIPT.resolve(), "fixed identity-scope method receipt path required")
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == method_receipt_sha256, "identity-scope receipt raw bytes differ")
    receipt = json.loads(raw)
    require(receipt.get("schema") == METHOD_SCHEMA and receipt.get("method_checks_pass") is True
            and receipt.get("released") is False, "checked unreleased identity-scope method receipt required")
    chain.core.require_unreleased(receipt.get("release"))
    required = {DRIVER: driver_sha256, OWN: LOADED_PRODUCER_SHA256, chain.OWN: CHAIN_GATE_SHA256,
                chain.DRIVER: CHAIN_ARGS["chain_driver_sha256"], chain.METHOD: CHAIN_ARGS["chain_method_sha256"],
                chain.relative(CHAIN_ARGS["method_receipt_path"]): CHAIN_ARGS["method_receipt_sha256"]}
    sources = receipt.get("source_sha256", {})
    require(all(sources.get(key) == value for key, value in required.items()) and OWN_TEST in sources,
            "identity-scope receipt must bind its actual fresh and frozen sources")
    pins = chain.merge_pins(chain.source_pins(**CHAIN_ARGS), sources, required,
                            {chain.relative(path): method_receipt_sha256})
    chain.verify_pins(pins)
    return pins


def verify_current_state_labels(field):
    """Exclude exactly one historical subtree; inspect every other state label."""
    require(isinstance(field.get("response", {}).get("support_mask_chain_schedule_v1"), dict),
            "the one explicit historical scheduling subtree is required")
    checked = 0

    def visit(value, path=()):
        nonlocal checked
        if path == ("response", "support_mask_chain_schedule_v1"):
            return
        if isinstance(value, dict):
            if "state_id" in value:
                require(value["state_id"] == field["state_id"], "mixed current state identity outside historical scope")
                checked += 1
            require(all(key not in value or value[key] == field[key] for key in ("case_id", "accessory_placement")),
                    "mixed current load identity outside historical scope")
            for key, item in value.items():
                visit(item, (*path, key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, (*path, index))

    visit(field)
    return {"all_nonhistorical_nested_state_labels_verified": True, "state_label_count": checked,
            "only_exempt_path": HISTORICAL_PATH}


def verify_scope_execution(field, *, driver_sha256, method_receipt_path, method_receipt_sha256):
    execution = field.get("support_identity_scope_execution", {})
    command = execution.get("command")
    internal = field.get("support_mask_chain_execution", {}).get("command")
    require(isinstance(command, list) and len(command) >= 3 and all(isinstance(v, str) and v for v in command)
            and command[1:3] == ["-m", "scripts.run_thin_bolted_support_identity_scope_frame"]
            and isinstance(internal, list) and len(internal) >= 3,
            "actual outer identity-scope command and truthful reused chain call required")
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False, exit_on_error=False)
    parser.add_argument("--support-identity-method-receipt", type=Path)
    parser.add_argument("--support-identity-method-sha256")
    try:
        args, remainder = parser.parse_known_args(command[3:])
    except (argparse.ArgumentError, SystemExit) as exc:
        raise ValueError("invalid identity-scope command arguments") from exc
    require(args.support_identity_method_receipt is not None
            and chain.relative(ROOT / args.support_identity_method_receipt) == chain.relative(method_receipt_path)
            and args.support_identity_method_sha256 == method_receipt_sha256
            and command[0] == internal[0] and remainder == internal[3:],
            "outer identity-scope arguments must preserve the exact internal chain invocation")
    metadata_sha = canonical_sha(field["response"]["support_mask_chain_schedule_v1"])
    expected = {"loaded_driver_sha256": driver_sha256, "method_receipt_path": chain.relative(method_receipt_path),
                "method_receipt_sha256": method_receipt_sha256,
                "nested_support_mask_chain_execution_is_reused_internal_call": True,
                "historical_metadata_path": HISTORICAL_PATH,
                "historical_metadata_before_canonical_sha256": metadata_sha,
                "historical_metadata_after_canonical_sha256": metadata_sha,
                "historical_metadata_restored_unchanged": True, "current_action_identities_verified": True}
    require(all(execution.get(key) == value and (not isinstance(value, bool) or execution.get(key) is value)
                for key, value in expected.items()), "actual narrow historical-scope provenance required")
    params = {"support_mask_schedule_identity_scope_driver_sha256": driver_sha256,
              "support_mask_schedule_identity_scope_method_receipt_sha256": method_receipt_sha256}
    require(all(field["parameters"].get(key) == value for key, value in params.items()),
            "current identity must bind the actual outer source and method")
    labels = verify_current_state_labels(field)
    return {"actual_outer_execution": execution, "current_identity_scope_checks": labels,
            "historical_metadata_canonical_sha256": metadata_sha}


def verify_recorded_ancestor_scopes(failed_chain, *, driver_sha256, method_receipt_path, method_receipt_sha256):
    """Verify preserved outer wrappers without changing recorded search policies."""
    args = {"driver_sha256": driver_sha256, "method_receipt_path": method_receipt_path,
            "method_receipt_sha256": method_receipt_sha256}
    pins = source_pins(**args)
    checked = []
    for cohort in failed_chain["cohorts"]:
        path = ROOT / cohort["field_path"]
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == cohort["field_sha256"], "ancestor outer-scope raw bytes differ")
        ancestor = json.loads(raw)
        require(canonical_sha(ancestor) == cohort["field_canonical_sha256"], "ancestor outer-scope canonical bytes differ")
        scoped = "support_identity_scope_execution" in ancestor
        require(scoped or not any(key.startswith("support_mask_schedule_identity_scope_")
                                 for key in ancestor["parameters"]), "ancestor outer-scope sources lack actual invocation")
        if scoped:
            verify_scope_execution(ancestor, **args)
            require(all(ancestor["source_sha256"].get(key) == value for key, value in pins.items()),
                    "scoped ancestor omits actual wrapper sources")
            checked.append(cohort["field_path"])
        require(chain.core.support.digest(path) == cohort["field_sha256"], "ancestor changed during outer-scope replay")
    chain.verify_pins(pins)
    return {"all_recorded_ancestor_outer_scopes_verified": True, "scoped_ancestor_paths": checked,
            "recorded_search_policies_unchanged": True}


def audit_support_identity_scope_state(path_or_bytes, *, driver_sha256, method_receipt_path,
                                       method_receipt_sha256, prior_failure_path, prior_failure_sha256):
    require(isinstance(path_or_bytes, (bytes, str, Path)), "immutable identity-scope bytes or path required")
    args = {"driver_sha256": driver_sha256, "method_receipt_path": method_receipt_path,
            "method_receipt_sha256": method_receipt_sha256}
    pins = source_pins(**args)
    path = None if isinstance(path_or_bytes, bytes) else Path(path_or_bytes)
    payload = path_or_bytes if path is None else path.read_bytes()
    raw_sha = hashlib.sha256(payload).hexdigest()
    field = json.loads(payload)
    before = canonical_sha(field)
    current_scope = verify_scope_execution(field, **args)
    require(all(field["source_sha256"].get(key) == value for key, value in pins.items()),
            "fresh field omits actual outer wrapper sources")
    # The child checks exact current state/raw/canonical/q and all frozen laws.
    # No projected field, renamed command or relabelled receipt is supplied.
    mechanics = chain.audit_support_chain_state(payload, **CHAIN_ARGS,
        prior_failure_path=prior_failure_path, prior_failure_sha256=prior_failure_sha256)
    require(mechanics.get("schema") == chain.SCHEMA and mechanics.get(chain.SUCCESS) is True
            and mechanics["field_sha256"] == raw_sha and mechanics["field_canonical_sha256"] == before
            and all(mechanics.get(key) == field[key] for key in chain.core.IDENTITIES),
            "unchanged same-byte frozen chain mechanics receipt required")
    ancestors = verify_recorded_ancestor_scopes(mechanics["failed_chain_source"], **args)
    pins = chain.merge_pins(pins, mechanics["source_sha256"], field["source_sha256"])
    chain.verify_pins(pins)
    require(canonical_sha(field) == before and source_pins(**args).items() <= pins.items(),
            "outer scope field or source changed during admission")
    if path is not None:
        require(chain.core.support.digest(path) == raw_sha, "raw identity-scope field changed during admission")
    return {"schema": SCHEMA, SUCCESS: True, **{key: field[key] for key in chain.core.IDENTITIES},
            "field_sha256": raw_sha, "field_canonical_sha256": before, "source_sha256": pins,
            **current_scope, "ancestor_outer_scope_checks": ancestors,
            "support_search_checks": mechanics["support_search_checks"],
            "frozen_chain_mechanics_admission": mechanics,
            "same_original_bytes_delegated_without_field_or_receipt_relabelling": True,
            "native_CAD_K_or_response_execution": False,
            "small_motion_applicability_physical_bounds_complete_capacity_or_release_established": False,
            "release": {key: False for key in field["release"]}}
