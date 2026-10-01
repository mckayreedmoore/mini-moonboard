#!/usr/bin/env python3
"""Offline integrity and synthetic fail-closed checks for the capture proposal."""

from __future__ import annotations

import hashlib
import json
import math
import sys
import tarfile
from pathlib import Path


class Reject(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Reject(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").is_file())
PACKET = Path(__file__).resolve().parent
CONTRACT_PATH = PACKET / "capture-contract.json"
PINS_PATH = PACKET / "source-pins.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify_pins(contract: dict, pins: dict) -> dict:
    require(pins.get("schema") == "ccx223_bounded_contact_capture_source_pins/v1", "source-pins schema mismatch")
    archive = pins["source_archive"]
    archive_path = ROOT / archive["path"]
    require(sha256_file(archive_path) == archive["sha256"], "pinned source archive hash mismatch")

    checked_members = 0
    with tarfile.open(archive_path, mode="r:bz2") as source_tar:
        for member in pins["source_members"]:
            file_obj = source_tar.extractfile(member["member"])
            require(file_obj is not None, f"missing pinned source member: {member['member']}")
            require(hashlib.sha256(file_obj.read()).hexdigest() == member["sha256"], f"source member hash mismatch: {member['member']}")
            checked_members += 1

    checked_artifacts = 0
    for artifact in pins["artifacts"]:
        path = ROOT / artifact["path"]
        require(path.is_file(), f"missing pinned artifact: {artifact['path']}")
        require(sha256_file(path) == artifact["sha256"], f"pinned artifact hash mismatch: {artifact['path']}")
        checked_artifacts += 1

    motion_dir = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-port-motion-attempt09-common-map"
    pair_manifest = load_json(motion_dir / "contact-manifest.json")
    mesh_manifest = load_json(motion_dir / "mesh.json")
    require(len(pair_manifest["pairs"]) == contract["mesh_and_pair_census"]["ordered_pair_count"], "pair manifest count mismatch")
    require(sum(row["slave_face_count"] for row in pair_manifest["pairs"]) == contract["mesh_and_pair_census"]["slave_face_count"], "slave face census mismatch")
    require(sum(row["master_face_count"] for row in pair_manifest["pairs"]) == contract["mesh_and_pair_census"]["master_face_count"], "master face census mismatch")
    require(mesh_manifest["node_count"] == contract["mesh_and_pair_census"]["mesh_geometry_counts"]["nodes"], "mesh node count mismatch")
    require(mesh_manifest["element_count"] == contract["mesh_and_pair_census"]["mesh_geometry_counts"]["c3d10_elements"], "mesh element count mismatch")
    require(mesh_manifest["body_count"] == contract["mesh_and_pair_census"]["mesh_geometry_counts"]["bodies"], "mesh body count mismatch")
    bore_indices = contract["mesh_and_pair_census"]["wood_bore_pair_indices_one_based"]
    require(all(pair_manifest["pairs"][index - 1]["category"] == "open_bolt_shank_to_wood_bore" for index in bore_indices), "wood-bore pair crosswalk mismatch")
    require(pair_manifest["contact_law"]["calculix_version"] == "2.21", "historical manifest version note changed; re-review contract scope")

    trace_path = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-contact-point-trace-attempt01/trace-format.json"
    trace_format = load_json(trace_path)
    require(trace_format["schema"] == "ccx223_contact_point_trace_format/v1", "prototype trace schema mismatch")
    require("native_isol" in trace_format["tags"]["CCXPT_MAP"]["integer_fields"], "MAP native_isol field absent")
    require("energy_enabled" in trace_format["tags"]["CCXPT_TRIAL"]["integer_fields"], "TRIAL energy flag absent")
    return {"source_members_checked": checked_members, "artifacts_checked": checked_artifacts}


def audit_sweep(roster: list[dict], face_rows: list[dict], offset_base: int, offset_end: int,
                nintpoint: int, outcomes: list[dict], max_candidates: int | None = None) -> dict:
    """Check roster, contiguous runtime spans, and exactly one category per slot."""
    require(len(face_rows) == len(roster), "face visit count differs from frozen roster")
    cursor = offset_base
    slot_to_face: dict[int, tuple[dict, int]] = {}
    zero_span = 0
    for expected, actual in zip(roster, face_rows, strict=True):
        for field in ("pair_index", "tie_index", "face_ordinal", "slave_face_encoded"):
            require(expected[field] == actual[field], f"face order/key mismatch at {field}")
        start = actual["offset_start"]
        end = actual["offset_end"]
        require(start == cursor, "face offsets contain a hole or overlap")
        require(isinstance(start, int) and isinstance(end, int) and end >= start, "invalid face offset range")
        span = end - start
        if span == 0:
            zero_span += 1
        for local_ordinal, slot in enumerate(range(start + 1, end + 1), start=1):
            slot_to_face[slot] = (actual, local_ordinal)
        cursor = end

    require(cursor == offset_end, "final face end differs from recorded sweep end")
    require(offset_end - offset_base == nintpoint, "runtime spans do not conserve nintpoint")
    require(len(slot_to_face) == nintpoint, "runtime slot enumeration mismatch")
    require(len(outcomes) == nintpoint, "candidate outcome count does not equal runtime point count")

    seen_slots: set[int] = set()
    seen_keys: set[tuple[int, int, int, int, int]] = set()
    counts = {"mapped_generated": 0, "mapped_excluded": 0, "unmapped": 0}
    allowed_categories = set(counts)
    for outcome in outcomes:
        slot = outcome["slot"]
        require(slot in slot_to_face, "outcome slot lies outside the live face spans")
        require(slot not in seen_slots, "duplicate outcome slot")
        seen_slots.add(slot)
        face, expected_local = slot_to_face[slot]
        for field in ("pair_index", "tie_index", "face_ordinal", "slave_face_encoded"):
            require(outcome[field] == face[field], f"outcome face identity mismatch at {field}")
        require(outcome["face_local_ordinal"] == expected_local, "outcome local ordinal does not match source point loop")
        category = outcome["category"]
        require(category in allowed_categories, "unrecognized candidate outcome")
        if category == "mapped_generated":
            require(outcome.get("reason") == "GENERATED", "generated point has wrong source outcome")
        elif category == "mapped_excluded":
            require(outcome.get("reason") in {
                "DYNAMIC_POSITIVE_CLEARANCE_UNILATERAL_FILTER",
                "STATIC_POSITIVE_CLEARANCE_FILTER",
                "ALEATORIC_CONTACT_FILTER",
                "STATIC_PREVIOUS_STATE_FILTER",
                "SOURCE_STATE_ZERO_FILTER",
            }, "mapped exclusion lacks an allowed source-observed reason")
            require(outcome.get("reason") != "ALEATORIC_CONTACT_FILTER", "aleatoric exclusion invalidates deterministic capture")
        else:
            require(outcome.get("reason") == "NO_MASTER_PROJECTION", "unmapped point lacks no-master reason")
        key = (outcome["pair_index"], outcome["tie_index"], outcome["face_ordinal"],
               outcome["slave_face_encoded"], outcome["face_local_ordinal"])
        require(key not in seen_keys, "duplicate within-sweep point key")
        seen_keys.add(key)
        counts[category] += 1

    require(seen_slots == set(slot_to_face), "one or more live points have no unique category")
    candidate_count = sum(counts.values())
    if max_candidates is not None:
        require(candidate_count <= max_candidates, "exact point-key memory cap exceeded")
    mapped_count = counts["mapped_generated"] + counts["mapped_excluded"]
    require(candidate_count == mapped_count + counts["unmapped"], "candidate partition mismatch")
    return {
        "face_count": len(face_rows),
        "zero_span_face_count": zero_span,
        "nintpoint": nintpoint,
        "candidate_count": candidate_count,
        "mapped_count": mapped_count,
        "generated_count": counts["mapped_generated"],
        "excluded_count": counts["mapped_excluded"],
        "unmapped_count": counts["unmapped"],
    }


def audit_trial_coverage(generated_keys: list[tuple], trial_keys: list[tuple]) -> None:
    require(len(generated_keys) == len(set(generated_keys)), "duplicate generated point key")
    require(len(trial_keys) == len(set(trial_keys)), "duplicate trial point key")
    require(set(generated_keys) == set(trial_keys), "generated/trial point key coverage mismatch")


def classify_transition(old: dict, new: dict) -> str:
    """Separate displacement-state equality from point-mapping equality."""
    if old.get("accepted") or old.get("cutback") or new.get("cutback"):
        return "NO_JOIN_ACCEPTED_OR_CUTBACK_BOUNDARY"
    if (old.get("step"), old.get("increment"), old.get("attempt")) != (
            new.get("step"), new.get("increment"), new.get("attempt")):
        return "NO_JOIN_STEP_INCREMENT_OR_ATTEMPT_BOUNDARY"
    if old.get("corrected_coordinates") != new.get("generation_coordinates"):
        return "NO_JOIN_DIFFERENT_DISPLACEMENT_STATE"
    if old.get("mapping_fingerprint") == new.get("mapping_fingerprint"):
        return "EQUAL_STATE_POINTWISE_MAPPING_MATCH"
    return "EQUAL_STATE_REMAPPED_EXCLUDE_POINTWISE_COMPARISON"


def inactive_force_bound(outcome: dict, constitutive_gap: float | None, law: str) -> float | None:
    """Return zero only for the proven positive-gap unilateral exclusion case."""
    if outcome.get("category") == "unmapped":
        return None
    if (outcome.get("category") == "mapped_excluded"
            and outcome.get("reason") == "DYNAMIC_POSITIVE_CLEARANCE_UNILATERAL_FILTER"
            and law == "LINEAR_UNILATERAL"
            and constitutive_gap is not None
            and math.isfinite(constitutive_gap)
            and constitutive_gap > 0.0):
        return 0.0
    return None


def require_finite(values: list[float], label: str) -> None:
    require(all(math.isfinite(value) for value in values), f"nonfinite required numeric value in {label}")


def audit_completion(sweeps: list[dict], run_end: dict | None, actual_bytes: int,
                     max_bytes: int, max_details: int, max_sweeps: int) -> None:
    require(run_end is not None, "missing RUN_END marker")
    require(actual_bytes <= max_bytes, "capture byte cap exceeded")
    require(len(sweeps) <= max_sweeps, "generation sweep cap exceeded")
    require(run_end.get("complete") is True, "RUN_END marks capture incomplete")
    require(run_end.get("overflow") is False, "capture overflow reported")
    require(run_end.get("writer_error") is False, "capture writer error reported")
    require(run_end.get("bytes_written") == actual_bytes, "RUN_END byte count mismatch")
    require(len(sweeps) == run_end.get("sweeps_seen"), "RUN_END sweep count mismatch")
    require(len({row.get("sweep_id") for row in sweeps}) == len(sweeps), "duplicate sweep marker")
    detail_count = sum(row.get("detail_rows", 0) for row in sweeps)
    face_count = sum(row.get("face_rows_seen", 0) for row in sweeps)
    require(detail_count <= max_details, "detail row cap exceeded")
    require(run_end.get("detail_rows") == detail_count, "RUN_END detail count mismatch")
    require(run_end.get("face_rows_seen") == face_count, "RUN_END face count mismatch")
    for row in sweeps:
        require(row.get("begin") is True and row.get("end") is True, "missing sweep begin/end marker")
        require(row.get("complete") is True and row.get("overflow") is False, "incomplete or overflowing sweep")
        require(row.get("face_rows_seen") == row.get("expected_face_rows"), "sweep face-row count mismatch")
        require(row.get("span_sum") == row.get("nintpoint"), "sweep end span conservation mismatch")


def synthetic_controls(contract: dict) -> list[str]:
    passed: list[str] = []

    roster = [
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 1, "slave_face_encoded": 101},
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 2, "slave_face_encoded": 102},
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 3, "slave_face_encoded": 103},
        {"pair_index": 2, "tie_index": 5, "face_ordinal": 1, "slave_face_encoded": 201},
    ]
    faces = [
        {**roster[0], "offset_start": 0, "offset_end": 0},
        {**roster[1], "offset_start": 0, "offset_end": 2},
        {**roster[2], "offset_start": 2, "offset_end": 3},
        {**roster[3], "offset_start": 3, "offset_end": 3},
    ]
    outcomes = [
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 2, "slave_face_encoded": 102,
         "face_local_ordinal": 1, "slot": 1, "category": "mapped_generated", "reason": "GENERATED"},
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 2, "slave_face_encoded": 102,
         "face_local_ordinal": 2, "slot": 2, "category": "mapped_excluded",
         "reason": "DYNAMIC_POSITIVE_CLEARANCE_UNILATERAL_FILTER"},
        {"pair_index": 1, "tie_index": 4, "face_ordinal": 3, "slave_face_encoded": 103,
         "face_local_ordinal": 1, "slot": 3, "category": "unmapped", "reason": "NO_MASTER_PROJECTION"},
    ]
    result = audit_sweep(roster, faces, 0, 3, 3, outcomes)
    require(result["zero_span_face_count"] == 2 and result["candidate_count"] == 3, "zero/variable-span positive control failed")
    passed.append("variable_and_zero_span_conservation")

    def rejected(name, thunk):
        try:
            thunk()
        except (Reject, KeyError, TypeError):
            passed.append(name)
            return
        raise Reject(f"negative control unexpectedly passed: {name}")

    rejected("missing_face_rejected", lambda: audit_sweep(roster, faces[:-1], 0, 3, 3, outcomes))
    broken_offsets = [dict(row) for row in faces]
    broken_offsets[2]["offset_start"] = 1
    rejected("offset_hole_or_overlap_rejected", lambda: audit_sweep(roster, broken_offsets, 0, 3, 3, outcomes))
    duplicated_outcome = outcomes + [dict(outcomes[0])]
    rejected("duplicate_or_extra_outcome_rejected", lambda: audit_sweep(roster, faces, 0, 3, 3, duplicated_outcome))
    rejected("missing_outcome_rejected", lambda: audit_sweep(roster, faces, 0, 3, 3, outcomes[:-1]))
    rejected("exact_key_memory_cap_rejected", lambda: audit_sweep(roster, faces, 0, 3, 3, outcomes, max_candidates=2))

    generated_keys = [(1, 4, 2, 102, 1)]
    audit_trial_coverage(generated_keys, list(generated_keys))
    rejected("missing_trial_key_rejected", lambda: audit_trial_coverage(generated_keys, []))
    rejected("duplicate_trial_key_rejected", lambda: audit_trial_coverage(generated_keys, generated_keys * 2))
    passed.append("generated_trial_key_coverage")

    same_state_remap = {
        "step": 1, "increment": 7, "attempt": 1, "accepted": False, "cutback": False,
        "corrected_coordinates": (0.0, 1.0), "mapping_fingerprint": (22, 0.25, 0.75),
    }
    next_sweep_remap = {
        "step": 1, "increment": 7, "attempt": 1, "accepted": False, "cutback": False,
        "generation_coordinates": (0.0, 1.0), "mapping_fingerprint": (23, 0.25, 0.75),
    }
    require(classify_transition(same_state_remap, next_sweep_remap) == "EQUAL_STATE_REMAPPED_EXCLUDE_POINTWISE_COMPARISON", "remap classification failed")
    passed.append("equal_state_remap_not_conflated_with_state_change")
    wrong_increment = dict(next_sweep_remap, increment=8)
    require(classify_transition(same_state_remap, wrong_increment).startswith("NO_JOIN"), "increment boundary joined")
    passed.append("increment_boundary_join_rejected")
    wrong_cutback = dict(next_sweep_remap, cutback=True)
    require(classify_transition(same_state_remap, wrong_cutback).startswith("NO_JOIN"), "cutback boundary joined")
    passed.append("cutback_join_rejected")

    mapped_excluded = {"category": "mapped_excluded", "reason": "DYNAMIC_POSITIVE_CLEARANCE_UNILATERAL_FILTER"}
    require(inactive_force_bound(mapped_excluded, 1.0e-4, "LINEAR_UNILATERAL") == 0.0, "positive-gap unilateral bound control failed")
    require(inactive_force_bound({"category": "unmapped", "reason": "NO_MASTER_PROJECTION"}, None, "LINEAR_UNILATERAL") is None, "unmapped point was assigned a zero force")
    require(inactive_force_bound(mapped_excluded, -1.0e-4, "LINEAR_UNILATERAL") is None, "penetrating exclusion was assigned a zero bound")
    passed.append("inactive_force_bound_requires_mapped_positive_gap_reason")

    require_finite([0.0, 1.0], "synthetic finite fields")
    rejected("nonfinite_required_value_rejected", lambda: require_finite([0.0, float("nan")], "negative control"))
    passed.append("finite_field_gate")

    caps = contract["sampling_caps_and_completion"]
    good_sweeps = [{"sweep_id": 1, "begin": True, "end": True, "complete": True, "overflow": False,
                    "face_rows_seen": 2, "expected_face_rows": 2, "span_sum": 1, "nintpoint": 1, "detail_rows": 1}]
    good_end = {"complete": True, "overflow": False, "writer_error": False, "bytes_written": 128,
                "sweeps_seen": 1, "detail_rows": 1, "face_rows_seen": 2}
    audit_completion(good_sweeps, good_end, 128, caps["max_capture_bytes"], caps["max_detail_rows_total"], caps["max_generation_sweeps"])
    passed.append("matching_terminal_markers_positive_control")
    rejected("missing_run_end_rejected", lambda: audit_completion(good_sweeps, None, 128, caps["max_capture_bytes"], caps["max_detail_rows_total"], caps["max_generation_sweeps"]))
    rejected("byte_overflow_rejected", lambda: audit_completion(good_sweeps, good_end, caps["max_capture_bytes"] + 1, caps["max_capture_bytes"], caps["max_detail_rows_total"], caps["max_generation_sweeps"]))
    too_many_details = [dict(good_sweeps[0], detail_rows=caps["max_detail_rows_total"])]
    detail_end = dict(good_end, detail_rows=caps["max_detail_rows_total"])
    rejected("detail_overflow_rejected", lambda: audit_completion(too_many_details, detail_end, 128, caps["max_capture_bytes"], caps["max_detail_rows_total"] - 1, caps["max_generation_sweeps"]))
    rejected("sweep_overflow_rejected", lambda: audit_completion(good_sweeps * (caps["max_generation_sweeps"] + 1),
             dict(good_end, sweeps_seen=caps["max_generation_sweeps"] + 1,
                  detail_rows=caps["max_generation_sweeps"] + 1,
                  face_rows_seen=2 * (caps["max_generation_sweeps"] + 1)),
             128, caps["max_capture_bytes"], caps["max_detail_rows_total"], caps["max_generation_sweeps"]))
    return passed


def main() -> int:
    try:
        contract = load_json(CONTRACT_PATH)
        pins = load_json(PINS_PATH)
        require(contract.get("schema") == "ccx223_bounded_contact_capture_contract/v1", "capture contract schema mismatch")
        pin_result = verify_pins(contract, pins)
        cap = contract["sampling_caps_and_completion"]
        require(cap["max_face_rows"] == cap["max_generation_sweeps"] * cap["max_frozen_slave_faces_per_sweep"], "face row cap arithmetic mismatch")
        require(cap["max_pair_summary_rows"] == 2 * contract["mesh_and_pair_census"]["ordered_pair_count"] * cap["max_generation_sweeps"], "pair-summary row cap arithmetic mismatch")
        require(cap["max_pair_state_link_rows"] == contract["mesh_and_pair_census"]["ordered_pair_count"] * cap["max_generation_sweeps"], "pair-state link row cap arithmetic mismatch")
        require(cap["max_unique_snapshot_nodes"] == contract["mesh_and_pair_census"]["mesh_geometry_counts"]["nodes"], "snapshot node cap differs from frozen mesh cap")
        require(cap["max_exact_snapshot_bytes_each"] == cap["max_unique_snapshot_nodes"] * 3 * 8, "snapshot byte cap arithmetic mismatch")
        require(cap["max_concurrent_snapshot_bytes"] >= 2 * cap["max_exact_snapshot_bytes_each"], "two-state snapshot memory cap is too small")
        require(cap["max_concurrent_point_key_table_bytes"] >= 2 * cap["max_point_key_table_bytes"], "two-state point-key memory cap is too small")
        require(cap["max_all_run_output_bytes"] == (cap["max_native_output_files_total_bytes"]
                + cap["max_capture_bytes"] + 2 * cap["max_solver_stdout_stderr_bytes_each"]), "aggregate run-output cap arithmetic mismatch")
        worst_case_bytes = (
            cap["max_face_rows"] * cap["max_face_record_bytes_including_lf"]
            + cap["max_pair_summary_rows"] * cap["max_pair_summary_record_bytes_including_lf"]
            + cap["max_detail_rows_total"] * cap["max_detail_record_bytes_including_lf"]
            + 2 * cap["max_generation_sweeps"] * cap["max_sweep_control_record_bytes_including_lf"]
            + 2 * cap["max_run_control_record_bytes_including_lf"]
            + (cap["max_iteration_link_rows"] + cap["max_pair_state_link_rows"])
            * cap["max_other_record_bytes_including_lf"]
        )
        require(worst_case_bytes < cap["max_capture_bytes"], "declared worst-case record caps exceed capture byte cap")
        control_names = synthetic_controls(contract)
        print(json.dumps({
            "schema": "ccx223_bounded_contact_capture_contract_validation/v1",
            "status": "PASS_CONTRACT_AND_SYNTHETIC_CONTROLS",
            "native_run_performed": False,
            "solver_build_performed": False,
            "canonical_files_modified": False,
            "source_pin_counts": pin_result,
            "synthetic_controls_passed": control_names,
            "synthetic_control_count": len(control_names),
            "declared_worst_case_capture_bytes": worst_case_bytes,
            "declared_capture_byte_cap": cap["max_capture_bytes"]
        }, sort_keys=True, indent=2))
        return 0
    except (Reject, OSError, KeyError, TypeError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(json.dumps({
            "schema": "ccx223_bounded_contact_capture_contract_validation/v1",
            "status": "FAIL_CLOSED",
            "native_run_performed": False,
            "solver_build_performed": False,
            "error": str(exc)
        }, sort_keys=True, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
