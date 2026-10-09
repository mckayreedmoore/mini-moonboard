"""Retained, source-bound arithmetic supplement; no CAD or mechanics execution.

The historical stdin source was recovered verbatim from its tool-call record.
This new checker authenticates that provenance without executing its fixed
output command. It reuses issued CAD proofs and checks their arithmetic.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import platform
from itertools import pairwise
from pathlib import Path

import run_fresh as guard


def interval_checks(model):
    rows = model["canonical_interval_checks"]
    guard.require(len(rows) == 12, "twelve canonical interval records")
    errors = [
        max(
            abs(a - b)
            for a, b in zip(
                row["canonical_interval_mm"], row["saved_receiver_x_bounds_mm"]
            )
        )
        for row in rows
    ]
    guard.require(
        max(errors) < 1e-6, "issued canonical intervals differ from saved bounds"
    )
    return {
        "count": len(rows),
        "maximum_interval_bbox_error_mm": max(errors),
        "proof_kind": "REUSED_SOURCE_BOUND_V3_SAVED_BREP_BOUND_RECEIPT",
        "new_independent_BREP_read": False,
    }


def washer_checks(details):
    rows = details["washer_seat_rows"]
    fresh = [r for r in rows if "current_host_support_point_xyz_mm" in r]
    guard.require(
        len(rows) == 112 and len(fresh) == 36, "112 seats / 36 issued fresh probes"
    )
    errors = []
    for row in fresh:
        outer, inner, depth = (
            row["OD_mm"],
            row["support_inner_diameter_mm"],
            row["probe_depth_mm"],
        )
        guard.require(outer > inner > 0 and depth == 0.1, "ring dimensions")
        expected = math.pi / 4 * (outer**2 - inner**2) * depth
        error = abs(row["expected_probe_volume_mm3"] - expected)
        errors.append(error)
        guard.require(
            error < 1e-8, "recorded ring volume differs from independent arithmetic"
        )
        guard.require(
            abs(row["intersected_current_wood_volume_mm3"] - expected) <= 1e-4,
            "issued intersection is not full within tolerance",
        )
        guard.require(
            abs(
                row["support_fraction"]
                - row["intersected_current_wood_volume_mm3"] / expected
            )
            < 1e-12,
            "issued support fraction differs",
        )
        guard.require(row["full_modeled_support"], "issued seat is not full")
    guard.require(all(r["full_modeled_support"] for r in rows), "non-full reused seat")
    return {
        "total_seats": len(rows),
        "issued_intersection_rows_reused": len(fresh),
        "independent_ring_volume_count": len(fresh),
        "maximum_ring_volume_arithmetic_error_mm3": max(errors),
        "maximum_recorded_probe_volume_deficit_mm3": max(
            abs(
                r["expected_probe_volume_mm3"]
                - r["intersected_current_wood_volume_mm3"]
            )
            for r in fresh
        ),
        "proof_kind": "INDEPENDENT_RING_ARITHMETIC_WITH_AUTHENTICATED_ISSUED_INTERSECTIONS",
        "new_independent_CAD_intersections": False,
    }


def station_checks(model, result, field):
    members = {r["name"]: r for r in field["source_inputs"]["timber_rows"]}
    rows = []
    for issued in result["candidate_member_restraint_paths"]:
        name = issued["member"]
        member = members[name]
        grain = (
            [1.0, 0.0, 0.0]
            if name in ("base_header", "base_rail_top")
            else [0.0, math.cos(math.radians(50)), math.sin(math.radians(50))]
        )
        shift = (
            model["principal_shift_xyz_mm"]
            if name == "base_principal_center_right"
            else [0, 0, 0]
        )
        start = [a + b for a, b in zip(member["start"], shift)]
        length = sum(
            (b - a) * g for a, b, g in zip(member["start"], member["end"], grain)
        )
        stations = sorted(
            sum((p - a) * g for p, a, g in zip(screw["origin_xyz_mm"], start, grain))
            for screw in model["screw_axes"]
            if screw["receiver"] == name
        )
        guard.require(
            stations and stations[0] >= -1e-6 and stations[-1] <= length + 1e-6,
            "stations within member",
        )
        cuts = [0.0, *stations, length]
        gap = max(b - a for a, b in pairwise(cuts))
        error = abs(gap - issued["largest_candidate_gap_mm"])
        guard.require(
            error < 1e-6 and abs(length - issued["gross_length_mm"]) < 1e-6,
            "station/gross-length arithmetic differs",
        )
        guard.require(
            len(stations) == len(issued["candidate_screw_axis_ids"]), "station count"
        )
        rows.append(
            {
                "member": name,
                "station_count": len(stations),
                "maximum_candidate_gap_mm": gap,
                "gap_difference_mm": error,
            }
        )
    guard.require(len(rows) == 4, "four member station records")
    return {
        "members": rows,
        "proof_kind": "INDEPENDENT_STDLIB_ARITHMETIC_FROM_FROZEN_GEOMETRY_AND_OLD_FIELD_DATUMS",
        "restraint_or_Cp_adopted": False,
    }


def historical_provenance(refs):
    recovery = guard.read_pinned(refs["historical_recovery"])
    checks = guard.read_pinned(refs["historical_checks"])
    for key in (
        "source",
        "historical_command",
        "historical_tool_records",
        "issued_verification",
        "existing_independent_checks",
    ):
        guard.verify({recovery[key]["path"]: recovery[key]["sha256"]})
    source = (guard.ROOT / recovery["source"]["path"]).read_text()
    command = (guard.ROOT / recovery["historical_command"]["path"]).read_text()
    guard.require(
        command == "uv run python - <<'PY'\n" + source + "PY",
        "recovered stdin differs from historical command",
    )
    records = [
        json.loads(line)["payload"]
        for line in (guard.ROOT / recovery["historical_tool_records"]["path"])
        .read_text()
        .splitlines()
    ]
    call = next(r for r in records if r["type"] == "custom_tool_call")
    output = next(r for r in records if r["type"] == "custom_tool_call_output")
    guard.require(
        call["call_id"] == output["call_id"] == recovery["original_tool_call_id"],
        "historical call/output identities differ",
    )
    marker = "tools.exec_command({cmd:"
    start = call["input"].index(marker) + len(marker)
    actual_command, _ = json.JSONDecoder().raw_decode(call["input"][start:])
    guard.require(actual_command == command, "retained command differs from tool call")
    observed = None
    for item in output["output"]:
        try:
            value = json.loads(item["text"])
        except (KeyError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and "exit_code" in value:
            guard.require(
                value["exit_code"] == 0, "historical checker did not exit successfully"
            )
            stdout = value["output"]
            try:
                observed = json.loads(stdout)
            except json.JSONDecodeError:
                # The captured tool transport preserves one JSON-string escape layer.
                observed = json.loads(json.loads('"' + stdout + '"'))
    guard.require(
        observed == checks == recovery["metrics"],
        "historical stdout and retained checks differ",
    )
    return {
        "source_retained_as_file_at_original_issue": False,
        "source_recovered_verbatim": True,
        "original_call_id": recovery["original_tool_call_id"],
        "original_call_timestamp_utc": recovery["original_call_timestamp_utc"],
        "original_source": recovery["source"],
        "recovery_record": refs["historical_recovery"],
        "command_source_output_bindings_verified": True,
        "historical_command_executed_by_supplement": False,
        "coupon_known_answers": "copied from producer in the historical checker; not independently queried there",
    }


def negative_controls(model, result, field, details):
    checks = []
    bad = copy.deepcopy(model)
    bad["canonical_interval_checks"][0]["saved_receiver_x_bounds_mm"][0] += 1
    checks.append(("altered_interval_bounds", lambda: interval_checks(bad)))
    bad_ring = copy.deepcopy(details)
    row = next(
        r
        for r in bad_ring["washer_seat_rows"]
        if "current_host_support_point_xyz_mm" in r
    )
    row["intersected_current_wood_volume_mm3"] *= 0.9
    checks.append(("partial_intersection", lambda: washer_checks(bad_ring)))
    bad_area = copy.deepcopy(details)
    row = next(
        r
        for r in bad_area["washer_seat_rows"]
        if "current_host_support_point_xyz_mm" in r
    )
    row["expected_probe_volume_mm3"] += 0.01
    checks.append(("altered_expected_area", lambda: washer_checks(bad_area)))
    bad_station = copy.deepcopy(model)
    row = next(
        r for r in bad_station["screw_axes"] if r["axis_id"] == "kicker_header_right_1"
    )
    row["origin_xyz_mm"][0] += 1
    checks.append(
        ("altered_header_station", lambda: station_checks(bad_station, result, field))
    )
    rejected = []
    for label, operation in checks:
        try:
            operation()
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError("negative control was accepted: " + label)
    return rejected


def run(inputs, digest):
    snapshot = guard.authenticate(inputs, digest, "audit")
    refs = inputs["evidence"]
    model, result, field, details = (
        guard.read_pinned(refs[key])
        for key in ("base_v3", "audit_result", "first_old_field", "audit_details")
    )
    guard.merge(snapshot["pins"], {r["path"]: r["sha256"] for r in refs.values()})
    reuse = guard.read_pinned(refs["v3_interval_reuse"])
    guard.merge(snapshot["pins"], reuse["source_sha256"])
    guard.require(
        reuse["reused_proof"]["exact_base_geometry_sha256"] == refs["base_v3"]["sha256"]
        and reuse["reused_proof"]["reusable_principal_and_kicker_post_interval_subset"]
        == 12,
        "prior interval proof does not cover this exact base/subset",
    )
    guard.verify(snapshot["pins"])
    record = {
        "schema": "revised_base_evidence_verification_supplement/v1",
        "status": "VERIFIED_REPRODUCIBLE_SUPPLEMENT_WITH_REUSED_CAD_PROOFS",
        "historical_provenance": historical_provenance(refs),
        "prior_interval_proof_reused": refs["v3_interval_reuse"],
        "intervals": interval_checks(model),
        "washers": washer_checks(details),
        "stations": station_checks(model, result, field),
        "negative_controls_rejected": negative_controls(model, result, field, details),
        "issued_audit_pin_count": snapshot["issued_pin_count"],
        "issued_closure_canonical_sha256": snapshot["issued_closure_canonical_sha256"],
        "new_checker": {
            "path": str(Path(__file__).relative_to(guard.ROOT)),
            "sha256": guard.sha(__file__),
        },
        "inputs_sha256": digest,
        "runtime": {"python": platform.python_version()},
        "native_solve": False,
        "CAD_rebuild": False,
        "new_response": False,
        "physical_observation_or_test": False,
    }
    guard.verify(snapshot["pins"])
    record["source_pins_before_after_unchanged"] = True
    record["supplement_pin_count"] = len(snapshot["pins"])
    record["supplement_closure_canonical_sha256"] = guard.canonical(snapshot["pins"])
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    try:
        guard.reserve_output(args.out)
        inputs, digest = guard.load_inputs()
        record = run(inputs, digest)
        guard.write_new(args.out / "verification-supplement.json", record)
    except (OSError, ValueError) as error:
        parser.exit(2, str(error) + "\n")
    print(
        json.dumps(
            {
                "status": record["status"],
                "issued_audit_pins": record["issued_audit_pin_count"],
            }
        )
    )


if __name__ == "__main__":
    main()
