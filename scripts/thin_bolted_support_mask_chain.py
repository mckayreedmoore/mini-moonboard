"""Reuse failed-mask cohorts for ordering, with no transferred force field.

The shared pure lineage reader authenticates immutable source, command and
physical-input records. The frozen controller supplies numerical ordering and
the frozen core supplies every fresh branch. Admission remains a separate
replay of the new coefficients, actions and complete body balances.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from scripts import thin_bolted_support_chain_admission as lineage
from scripts import thin_bolted_support_mask_schedule as scheduling

frame = scheduling.frame
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FROZEN_CORE_SOLVE = scheduling.FROZEN_CORE_SOLVE
SCHEMA = "thin_bolted_support_mask_chain/v1"
METHOD = "authenticated-failed-chain-mask-deprioritization"


def _validate_union(chain):
    if (chain.get("schema") != SCHEMA or chain.get("method") != METHOD
            or chain.get("scheduling_only") is not True or chain.get("old_q_or_forces_used") is not False
            or chain.get("previous_results_are_nonexistence_proof") is not False
            or chain.get("physical_laws_changed") is not False
            or chain.get("first_all_host_branch_remains_fresh") is not True):
        raise ValueError("explicit authenticated scheduling-only chain required")
    hosts, cohorts = chain["host_order"], chain["cohorts"]
    if hosts != sorted(set(hosts)) or not 1 <= len(hosts) <= 8 or not cohorts:
        raise ValueError("original ordered floor hosts and immutable cohorts required")
    union = []
    for cohort in cohorts:
        if cohort["policy"] not in ("original-core", "priority", "chain"):
            raise ValueError("authenticated recorded scheduling policy required")
        for mask in cohort["local_mask_ids"]:
            scheduling._number(hosts, mask)
            if mask not in union:
                union.append(mask)
    if chain["union_mask_ids"] != union:
        raise ValueError("mask union must preserve first occurrence oldest to newest")
    leaf = cohorts[-1]
    for top, local in (("previous_field_path", "field_path"), ("previous_field_sha256", "field_sha256"),
                       ("previous_field_canonical_sha256", "field_canonical_sha256"),
                       ("previous_state_id", "state_id"), ("previous_case_id", "case_id"),
                       ("previous_accessory_placement", "accessory_placement")):
        if chain[top] != leaf[local]:
            raise ValueError("latest immutable cohort and chain provenance differ")


def source_pins(chain=None):
    pins = scheduling._join_pins(scheduling.source_pins(), {
        scheduling._artifact_name(__file__): LOADED_PRODUCER_SHA256,
        lineage.OWN: lineage.LOADED_PRODUCER_SHA256})
    if chain is not None:
        _validate_union(chain)
        pins = scheduling._join_pins(pins, chain["source_sha256"])
        if any(pins.get(row["field_path"]) != row["field_sha256"] for row in chain["cohorts"]):
            raise ValueError("every immutable ancestor must remain source-pinned")
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("chain source or immutable failed ancestor changed")
    return pins


def load_failed_chain(path, expected_sha256, *, chain_driver_sha256,
                      method_receipt_path, method_receipt_sha256):
    """Authenticate each predecessor and actual policy without importing q."""
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("latest failed payload raw SHA differs")
    reference = json.loads(raw)
    chain = lineage.read_failed_chain(path, expected_sha256, reference,
        chain_driver_sha256=chain_driver_sha256, chain_method_sha256=LOADED_PRODUCER_SHA256,
        method_receipt_path=method_receipt_path, method_receipt_sha256=method_receipt_sha256)
    chain["source_sha256"] = source_pins(chain)
    return chain


def chain_metadata(chain):
    _validate_union(chain)
    return copy.deepcopy({key: value for key, value in chain.items() if key != "source_sha256"})


def validate_current_report(report, chain):
    """Compare complete physical inputs after finished-state identity binding."""
    source_pins(chain)
    if scheduling.physical_input_signature_sha256(report) != chain["physical_input_signature_sha256"]:
        raise ValueError("failed-chain ordering requires unchanged complete physical inputs")
    if sorted(row["member"] for row in report["finished_floor_footprints"]) != chain["host_order"]:
        raise ValueError("fresh physical floor host order differs from the chain")


def compatible_contact_solve(*args, previous_chain, **kwargs):
    """Supply only union mask IDs to the frozen context; solve every fresh law."""
    source_pins(previous_chain)
    contacts = args[3] if len(args) > 3 else kwargs["contacts"]
    tangents = args[4] if len(args) > 4 else kwargs["tangents"]
    if scheduling.core._hosts(contacts, tangents) != previous_chain["host_order"]:
        raise ValueError("fresh floor rows must retain the chain's ordered physical hosts")
    internal = {"previous_host_order": previous_chain["host_order"],
                "previous_mask_ids": previous_chain["union_mask_ids"]}
    with scheduling.preferred_unvisited_masks(internal):
        result = FROZEN_CORE_SOLVE(*args, **kwargs)
    result["support_mask_chain_schedule_v1"] = chain_metadata(previous_chain)
    source_pins(previous_chain)
    return result
