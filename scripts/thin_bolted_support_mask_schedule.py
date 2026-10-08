"""Deprioritize authenticated earlier masks; reuse the frozen support search.

An earlier failed field supplies scheduling information only. Its q, reactions
and acceptance never transfer. The fresh all-host initial branch is retained;
globally new masks are preferred before earlier masks are reconsidered.
"""

from __future__ import annotations

import copy
import hashlib
import json
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from scripts import thin_bolted_support_state_search as core

frame = core.frame
CORE_SHA256 = "c162d296306a263be4e6769c4249abf6491512e8f7d9af323ab2e9b10b1018e8"
LOADED_PRODUCER_SHA256 = frame.sha(Path(__file__))
FROZEN_NEXT_MASK = core._next_mask
FROZEN_CORE_SOLVE = core.compatible_contact_solve
METHOD = "authenticated-prior-mask-deprioritization"
NUMERICAL_PARAMETER_KEYS = frozenset({"numerical_continuation_method",
    "numerical_newton_iteration_limit_per_floor_pattern", "lean_case_wall_time_limit_seconds"})
NUMERICAL_PARAMETER_PREFIXES = ("support_state_search_", "support_priority_", "support_mask_schedule_")
PHYSICAL_INPUT_KEYS = ("schema", "candidate", "revision", "case_id", "accessory_placement",
    "layout_report_sha256", "geometry_cache_sha256", "counts", "gravity", "applied_force_xyz_n",
    "applied_moment_about_global_origin_xyz_nmm", "body_applied_loads", "body_identities",
    "finished_floor_footprints")


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def physical_input_signature_sha256(report):
    inputs = {key: report[key] for key in PHYSICAL_INPUT_KEYS}
    inputs["parameters"] = {key: value for key, value in report["parameters"].items()
                            if key not in NUMERICAL_PARAMETER_KEYS
                            and not key.startswith(NUMERICAL_PARAMETER_PREFIXES)}
    return canonical_sha256(inputs)


def _artifact_name(path):
    path = Path(path).resolve()
    return str(path.relative_to(frame.ROOT)) if path.is_relative_to(frame.ROOT) else str(path)


def _number(hosts, mask_id):
    prefix = "centroid-mask-"
    if (not isinstance(mask_id, str) or not mask_id.startswith(prefix)
            or len(mask_id) != len(prefix) + len(hosts) or set(mask_id[len(prefix):]) - {"0", "1"}):
        raise ValueError("canonical mask ID in the original host order required")
    return sum(1 << i for i, bit in enumerate(mask_id[len(prefix):]) if bit == "1")


def _join_pins(*maps):
    pins = {}
    for mapping in maps:
        for path, digest in mapping.items():
            if path in pins and pins[path] != digest:
                raise ValueError("conflicting scheduling source pin: " + path)
            pins[path] = digest
    return pins


def source_pins(previous_schedule=None):
    pins = core.source_pins()
    if pins["scripts/thin_bolted_support_state_search.py"] != CORE_SHA256:
        raise ValueError("preserve the frozen support-search core")
    pins = _join_pins(pins, {_artifact_name(__file__): LOADED_PRODUCER_SHA256},
                      {} if previous_schedule is None else previous_schedule["source_sha256"])
    if any(frame.sha(frame.ROOT / path) != digest for path, digest in pins.items()):
        raise ValueError("scheduling source or previous failed payload changed")
    return pins


def load_previous_schedule(path, expected_sha256):
    """Read an authenticated complete failure, discarding old q and reactions."""
    path = Path(path).resolve()
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("previous failed payload raw SHA differs")
    report = json.loads(raw)
    response = report.get("response", {})
    if (report.get("schema") != "thin_bolted_common_shaft_frame/v1"
            or response.get("converged") is not False
            or report.get("usable_conditional_actions") is not False
            or report.get("failed_response_without_recovered_actions") is not True
            or report.get("compatible_numerical_mvp_complete") is not False
            or report.get("release") != frame.RELEASE
            or any(key in response for key in ("q", "connector_local_force_n", "normal_contact_force_n"))):
        raise ValueError("complete failed field without accepted q or recovered actions required")
    diagnostics = response.get("support_state_search_v1", {})
    hosts, rows = diagnostics.get("host_order"), diagnostics.get("tested_masks")
    if (diagnostics.get("schema") != "thin_bolted_support_state_search/v1"
            or diagnostics.get("method") != core.METHOD
            or diagnostics.get("floor_activation_threshold_n") != core.FLOOR_ACTIVATION_THRESHOLD_N
            or diagnostics.get("physical_laws_changed") is not False
            or diagnostics.get("old_field_initialization_used") is not False
            or diagnostics.get("no_fixed_point_proven") is not False
            or not isinstance(hosts, list) or not 1 <= len(hosts) <= 8
            or hosts != sorted(set(hosts)) or not isinstance(rows, list) or not rows
            or any(diagnostics.get(key) is not None for key in (
                "accepted_pattern_index", "accepted_enabled_centroid_xy_hosts",
                "accepted_disabled_centroid_xy_hosts", "final_mask_id", "final_q_canonical_sha256"))):
        raise ValueError("unaccepted original-law support-mask diagnostics required")
    if sorted(item["member"] for item in report["finished_floor_footprints"]) != hosts:
        raise ValueError("previous masks must name the authenticated physical floor hosts")
    mask_ids = []
    for index, row in enumerate(rows):
        number = _number(hosts, row.get("mask_id"))
        enabled = core._enabled(hosts, number)
        disabled = sorted(set(hosts) - set(enabled))
        if (row.get("pattern_index") != index or row.get("enabled_centroid_xy_hosts") != enabled
                or row.get("disabled_centroid_xy_hosts") != disabled or row.get("self_consistent") is not False
                or type(row.get("fixed_branch_converged")) is not bool):
            raise ValueError("previous mask partition or failure diagnostics differ")
        mask_ids.append(row["mask_id"])
    if len(set(mask_ids)) != len(mask_ids) or mask_ids[0] != "centroid-mask-" + "1" * len(hosts):
        raise ValueError("unique previous masks with a fresh all-host initial branch required")
    identity = {key: report[key] for key in ("case_id", "accessory_placement", "parameters", "geometry_cache_sha256")}
    if report.get("state_id") != "thin-v4-" + canonical_sha256(identity)[:24]:
        raise ValueError("previous case/parameter state identity differs")
    required_pins = core.source_pins()
    previous_pins = report.get("source_sha256", {})
    if any(previous_pins.get(key) != digest for key, digest in required_pins.items()):
        raise ValueError("previous field must bind the frozen original search methods")
    pins = _join_pins(previous_pins, source_pins(), {_artifact_name(path): expected_sha256})
    if any(frame.sha(frame.ROOT / name) != digest for name, digest in pins.items()):
        raise ValueError("previous failed field source bytes differ")
    return {"schema": "thin_bolted_support_mask_schedule/v1", "method": METHOD,
            "previous_field_path": _artifact_name(path), "previous_field_sha256": expected_sha256,
            "previous_field_canonical_sha256": canonical_sha256(report),
            "previous_state_id": report["state_id"], "previous_case_id": report["case_id"],
            "previous_accessory_placement": report["accessory_placement"],
            "previous_host_order": hosts.copy(), "previous_mask_ids": mask_ids,
            "physical_input_signature_sha256": physical_input_signature_sha256(report),
            "scheduling_only": True, "old_q_or_forces_used": False,
            "previous_results_are_nonexistence_proof": False, "physical_laws_changed": False,
            "first_all_host_branch_remains_fresh": True, "source_sha256": pins}


def schedule_metadata(previous_schedule):
    return copy.deepcopy({key: value for key, value in previous_schedule.items() if key != "source_sha256"})


def validate_current_report(report, previous_schedule):
    """Compare complete physical inputs after the finished-state binding."""
    source_pins(previous_schedule)
    if physical_input_signature_sha256(report) != previous_schedule["physical_input_signature_sha256"]:
        raise ValueError("previous-mask scheduling requires unchanged complete physical inputs")
    if sorted(item["member"] for item in report["finished_floor_footprints"]) != previous_schedule["previous_host_order"]:
        raise ValueError("current physical floor host order differs")


@contextmanager
def preferred_unvisited_masks(previous_schedule):
    """Patch only numerical ordering, then restore it even on interruption."""
    hosts = previous_schedule["previous_host_order"]
    prior_masks = {_number(hosts, mask_id) for mask_id in previous_schedule["previous_mask_ids"]}

    def next_mask(current, demanded, visited, total):
        if total != 1 << len(hosts):
            raise ValueError("previous masks require the unchanged original floor-host census")
        number, reason = FROZEN_NEXT_MASK(current, demanded, visited | prior_masks, total)
        if number is not None:
            return number, "globally new mask scheduling: " + reason
        number, reason = FROZEN_NEXT_MASK(current, demanded, visited, total)
        return number, "earlier mask reconsideration after globally new pool: " + reason

    with patch.object(core, "_next_mask", next_mask):
        yield


def compatible_contact_solve(*args, previous_schedule, **kwargs):
    """Reuse every fresh core branch; old masks influence scheduling only."""
    source_pins(previous_schedule)
    contacts = args[3] if len(args) > 3 else kwargs["contacts"]
    tangents = args[4] if len(args) > 4 else kwargs["tangents"]
    if core._hosts(contacts, tangents) != previous_schedule["previous_host_order"]:
        raise ValueError("scheduling host order differs from the fresh physical floor rows")
    with preferred_unvisited_masks(previous_schedule):
        result = FROZEN_CORE_SOLVE(*args, **kwargs)
    result["support_mask_schedule_v1"] = schedule_metadata(previous_schedule)
    source_pins(previous_schedule)
    return result
