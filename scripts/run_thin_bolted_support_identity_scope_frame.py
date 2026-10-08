"""Keep immutable scheduling ancestors outside current action-ID binding."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

from scripts import run_thin_bolted_support_chain_frame as chain
from scripts.thin_bolted_timber_face_contact import merge_pins

frame = chain.frame
OWN = str(Path(__file__).resolve().relative_to(frame.ROOT))
LOADED_DRIVER_SHA256 = frame.sha(Path(__file__))
METHOD_RECEIPT = frame.PACKET / "support-identity-scope-method-v4.json"
METHOD_SCHEMA = "thin_bolted_support_identity_scope_method/v1"
CHAIN_RECEIPT_SHA256 = "6bed41e7248ac0f3e72275614236a51acad871c8f0a5f21a7d69b928b850b90a"
HISTORY_KEY = "support_mask_chain_schedule_v1"
HISTORY_PATH = "response." + HISTORY_KEY
ORIGINAL_FINISHED_BINDING = chain.core.lean.common.finished.bind_finished_state


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify_current_identities(report):
    """Exempt exactly one authenticated history subtree, no current actions."""
    identity = {key: report[key] for key in ("state_id", "case_id", "accessory_placement")}

    def walk(value, path=()):
        if path == ("response", HISTORY_KEY):
            return
        if isinstance(value, dict):
            for key, expected in identity.items():
                if key in value and value[key] != expected:
                    raise ValueError("mixed current identity outside historical schedule: " + ".".join(path + (key,)))
            for key, child in value.items():
                walk(child, path + (key,))
        elif isinstance(value, list):
            for i, child in enumerate(value):
                walk(child, path + (str(i),))

    walk(report)


def bind_scoped_finished_state(report, *args, binder=None):
    """Relabel all current aliases while restoring the same historical object."""
    history = report["response"][HISTORY_KEY]
    digest = canonical_sha(history)
    del report["response"][HISTORY_KEY]
    try:
        result = (ORIGINAL_FINISHED_BINDING if binder is None else binder)(report, *args)
    finally:
        report["response"][HISTORY_KEY] = history
    result["response"][HISTORY_KEY] = history
    if canonical_sha(history) != digest:
        raise ValueError("immutable scheduling history changed during finished binding")
    verify_current_identities(result)
    result["support_identity_scope_execution"].update({
        "historical_metadata_path": HISTORY_PATH,
        "historical_metadata_before_canonical_sha256": digest,
        "historical_metadata_after_canonical_sha256": digest,
        "historical_metadata_restored_unchanged": True,
        "current_action_identities_verified": True,
    })
    return result


def main():
    from scripts import thin_bolted_support_identity_scope_admission as admission

    arguments = sys.argv[1:]
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("--support-identity-method-receipt", type=Path, required=True)
    parser.add_argument("--support-identity-method-sha256", required=True)
    custom, remainder = parser.parse_known_args(arguments)
    scope = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    scope.add_argument("--support-chain-prior-failure", type=Path, required=True)
    scope.add_argument("--support-chain-prior-sha256", required=True)
    scope.add_argument("--support-chain-method-receipt", type=Path, required=True)
    scope.add_argument("--support-chain-method-sha256", required=True)
    selected, _ = scope.parse_known_args(remainder)
    if (custom.support_identity_method_receipt.resolve() != METHOD_RECEIPT.resolve()
            or selected.support_chain_method_receipt.resolve() != chain.METHOD_RECEIPT.resolve()
            or selected.support_chain_method_sha256 != CHAIN_RECEIPT_SHA256):
        parser.error("use the fixed fresh identity-scope and frozen chain method receipts")
    previous = chain.scheduling.load_failed_chain(
        selected.support_chain_prior_failure, selected.support_chain_prior_sha256,
        chain_driver_sha256=chain.LOADED_DRIVER_SHA256,
        method_receipt_path=selected.support_chain_method_receipt,
        method_receipt_sha256=selected.support_chain_method_sha256)
    admission.verify_recorded_ancestor_scopes(previous, driver_sha256=LOADED_DRIVER_SHA256,
        method_receipt_path=custom.support_identity_method_receipt,
        method_receipt_sha256=custom.support_identity_method_sha256)

    def source_pins():
        return merge_pins(chain.source_pins(chain.METHOD_RECEIPT, CHAIN_RECEIPT_SHA256, previous),
            admission.source_pins(LOADED_DRIVER_SHA256, custom.support_identity_method_receipt,
                                  custom.support_identity_method_sha256))

    pins = source_pins()
    execution = {
        "command": [sys.executable, "-m", "scripts.run_thin_bolted_support_identity_scope_frame", *arguments],
        "loaded_driver_sha256": LOADED_DRIVER_SHA256,
        "method_receipt_path": str(custom.support_identity_method_receipt.resolve().relative_to(frame.ROOT)),
        "method_receipt_sha256": custom.support_identity_method_sha256,
        "nested_support_mask_chain_execution_is_reused_internal_call": True,
        "historical_metadata_path": HISTORY_PATH,
    }
    original_metadata = chain.core.lean.common.bind_common_metadata

    def metadata(report, *args):
        report = original_metadata(report, *args)
        if source_pins() != pins:
            raise ValueError("identity-scope frozen inputs changed during the case")
        report["source_sha256"] = merge_pins(report["source_sha256"], pins)
        report["parameters"].update({
            "support_mask_schedule_identity_scope_driver_sha256": LOADED_DRIVER_SHA256,
            "support_mask_schedule_identity_scope_method_receipt_sha256": custom.support_identity_method_sha256,
        })
        report["support_identity_scope_execution"] = copy.deepcopy(execution)
        return report

    old_argv = sys.argv
    try:
        sys.argv = [old_argv[0], *remainder]
        with (patch.object(chain.core.lean.common, "bind_common_metadata", metadata),
              patch.object(chain.core.lean.common.finished, "bind_finished_state", bind_scoped_finished_state)):
            chain.main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
