"""Authenticate and join finite timber coverage; perform no strength calculation.

Import is inert. build(output) reads saved receipts, section identities and results.
The station ledger distinguishes the fresh proposal actions from source-104 results.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/member-opening-coverage"
METHOD_SHA = "bc0704d2c4f7cb6dc472a139b382e514ab69f0a8de02f05a19a3266de6addb0b"
FIXED = {
    "knee-bridge-working-package/attempt02/manifest.json": "4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0",
    "knee-bridge-members/attempt01/checks.json": "0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65",
    "knee-bridge-remaining-sections/attempt01/checks.json": "f519ecc04af7622ec5637162b7a86d6a88e6478e2b15332bf566e6d0e5a3d4c3",
    "knee-bridge-top-rail/attempt02/checks.json": "9af1574d785466cdb8de36d3f0cd13dd92cd554ca6e374999f59d20adee5a744",
    "knee-bridge-joint-replay/attempt01/checks.json": "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    "top-host-net-sections/attempt02/checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    "corner-group-finish/attempt03/checks.json": "2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23",
}


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def build(output):
    """Write a finite identity/coverage ledger into a new owned immediate child."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh owned child required")
    method_path = HERE / "knee-bridge-members.py"
    require(sha(method_path) == METHOD_SHA, "source-pin helper changed")
    spec = importlib.util.spec_from_file_location("coverage_source_pins", method_path)
    require(spec is not None and spec.loader is not None, "source-pin helper unavailable")
    method = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(method)
    finally:
        sys.dont_write_bytecode = previous
    # Reuse the existing pin dictionary and authentication function. Never call
    # load_sources, a mechanics helper, or a producer build/run/main entry point.
    pins = {method_path: METHOD_SHA, **method.CLASSIFIER_PINS}
    for path in (method.GEOMETRY, method.GEOMETRY_REFERENCE, method.REPORT,
                 method.INPUTS, method.ASSESSMENT, method.COMPARISON, method.RESPONSE):
        pins[path] = method.PINS[path]
    pins.update({HERE / "rawlocal" / name: digest for name, digest in FIXED.items()})
    method.authenticate(pins)
    reports = {name: read(HERE / "rawlocal" / name) for name in FIXED}
    package = reports["knee-bridge-working-package/attempt02/manifest.json"]
    members = reports["knee-bridge-members/attempt01/checks.json"]
    remaining = reports["knee-bridge-remaining-sections/attempt01/checks.json"]
    top = reports["knee-bridge-top-rail/attempt02/checks.json"]
    knee = reports["knee-bridge-joint-replay/attempt01/checks.json"]
    old_hosts = reports["top-host-net-sections/attempt02/checks.json"]
    old_corners = reports["corner-group-finish/attempt03/checks.json"]
    geometry = read(method.GEOMETRY)["members"]
    case_ids = tuple(method.CASES)
    require(len(geometry) == 44 and len(members["members"]) == 42, "44/42 census differs")
    for report in (members, remaining, top, knee):
        require(tuple(report["case_ids"]) == case_ids, "fresh case order differs")
        factor = report.get("dead_load_factor", report.get("same_state_dead_load_factor"))
        require(factor == 1.1110134616260479, "fresh gravity scope differs")
    # Bind each consumed saved result through its existing receipt. Only read
    # output hashes here; unconsumed historical source closures are not re-run.
    for name, digest in FIXED.items():
        if name.endswith("manifest.json"):
            continue
        path = HERE / "rawlocal" / name
        receipt_path = path.with_name("receipt.json")
        if name.startswith("corner-group-finish/"):
            receipt_digest = "f1d8ad0f204be457f5b8eba2e8185828456251ae7fb67aa945bb7477bacd2f62"
        else:
            receipt_digest = package["source_sha256"].get(str(receipt_path.relative_to(ROOT)))
        require(receipt_digest is not None, "receipt binding absent: " + name)
        method.bind(pins, receipt_path, receipt_digest)
        method.authenticate({receipt_path: receipt_digest})
        receipt = read(receipt_path)
        require(receipt["output_sha256"][path.name] == digest, "receipt result binding differs")
    effective = {r["body"]: r["effective_proposal_step"]
                 for r in package["geometry"]["effective_members"] if r["body"] in geometry}
    require(set(effective) == set(geometry), "effective timber identity differs")
    for body, record in geometry.items():
        current_path = ROOT / record["current_finished_step"]
        method.bind(pins, current_path, record["current_finished_step_sha256"])
        proposed = effective[body]
        method.bind(pins, ROOT / proposed["path"], proposed["sha256"])
        if body not in method.EXCLUDED:
            require(proposed["sha256"] == record["current_finished_step_sha256"], "unrecorded geometry change")
    for body in old_corners["geometries"]:
        record = geometry[body]
        require(old_corners["source_sha256"].get(record["current_finished_step"])
                == record["current_finished_step_sha256"], "corner geometry carryforward differs")
    method.authenticate(pins)
    # A key denotes one simultaneous signed cut, not a maximum or load variant.
    fresh, historical = {}, set()
    for family, result in remaining["families"].items():
        require(result["evaluated_limit_count"] == result["expected_limit_count"], "incomplete family")
        for cut in result["cut_summaries"]:
            key = (cut["block"], cut["case"], cut["saved_trace_index"])
            require(key not in fresh, "duplicate fresh family trace")
            fresh[key] = family
    for cut in top["cuts"]:
        fresh[("base_rail_top", cut["case"], cut["saved_trace_index"])] = "physical_top_rail"
    for cut in old_hosts["cuts"]:
        historical.add((cut["body"], cut["case"], cut["saved_trace_index"]))
    frame_ids = {r["member_id"] for r in read(method.FRAME_MAP)["members"]}
    rows, missing, excluded, features = [], [], [], []
    consumed_fresh = set()
    for body, record in geometry.items():
        counts = Counter()
        body_missing = []
        modified = body in method.EXCLUDED
        for index, (station, section) in enumerate(zip(
            record["stations_mm"], record["rectangle_at_station"], strict=True
        )):
            status = section["status"]
            for case in case_ids:
                for offset, limit in enumerate(("before", "after")):
                    key = (body, case, 2 * index + offset)
                    if modified:
                        disposition = "separate_modified_spine_replay"
                    elif status.startswith("BORE_FREE_"):
                        disposition = "fresh_bore_free_reference"
                    elif key in fresh:
                        disposition = "fresh_opening_reference"
                    elif status == "NON_APPLICABLE_BORE_OR_PASSAGE":
                        disposition = "uncalculated_fresh_opening_reference"
                    else:
                        disposition = "inapplicable_terminal_point_load_section"
                    counts[disposition] += 1
                    if key in fresh:
                        consumed_fresh.add(key)
            if modified or status.startswith("BORE_FREE_"):
                continue
            identities = {fresh.get((body, case, 2 * index + offset))
                          for case in case_ids for offset in (0, 1)}
            require(len(identities) == 1, "partial case/limit coverage must be reported explicitly")
            if None not in identities:
                continue
            feature_ids = section.get("feature_ids", [])
            guards_only = bool(feature_ids) and all(
                identity.endswith("/owner_authorized_station_exclusion") for identity in feature_ids)
            row = {"body": body, "station_index": index, "station_mm": station,
                   "section_status": status, "case_ids": list(case_ids),
                   "limits": ["before", "after"], "saved_trace_indices": [2 * index, 2 * index + 1],
                   "feature_ids": feature_ids,
                   "opening_identity_kind": "modeled_station_exclusion_only" if guards_only else "finished_geometry_interval",
                   "source104_host_comparison_available": all(
                       (body, c, 2 * index + k) in historical for c in case_ids for k in (0, 1)),
                   "source104_corner_method_available": body in old_corners["geometries"]}
            if status == "NON_APPLICABLE_BORE_OR_PASSAGE":
                missing.append(row)
                body_missing.append(row)
            else:
                excluded.append(row)
        for feature in record["bore_or_passage_intervals"]:
            stations = [(i, s) for i, s in enumerate(record["stations_mm"])
                        if feature["lo"] - 1e-6 <= s <= feature["hi"] + 1e-6]
            features.append({"body": body, **feature,
                             "finished_void_claimed": not feature["id"].endswith("/owner_authorized_station_exclusion"),
                             "section_identity_scope": "original_four_bore_descriptor" if modified else "effective_finished_geometry",
                             "fresh_finite_replay_family": "modified_spine" if modified else None,
                             "intersecting_saved_station_indices": [i for i, _ in stations],
                             "uncalculated_saved_station_indices": [r["station_index"] for r in body_missing
                                  if feature["id"] in r["feature_ids"]]})
        rows.append({"body": body, "kind": "frame" if body in frame_ids else "block",
                     "effective_step": effective[body], "original_geometry_station_count": len(record["stations_mm"]),
                     "saved_finished_profile_planes": record["profile_planes"],
                     "original_geometry_opening_feature_count": len(record["bore_or_passage_intervals"]),
                     "trace_counts": dict(counts), "source104_corner_nominal_method": body in old_corners["geometries"],
                     "recess_geometry": record.get("recess_source"),
                     "uncalculated_station_count": len(body_missing)})
    require(consumed_fresh == set(fresh), "fresh family refers to an unknown trace")
    totals = Counter()
    for row in rows:
        if row["body"] not in method.EXCLUDED:
            totals.update(row["trace_counts"])
    require(sum(totals.values()) == 53784 and totals["fresh_bore_free_reference"] == 33912,
            "unchanged-body signed trace census differs")
    require(totals["fresh_opening_reference"] == 4488
            and totals["uncalculated_fresh_opening_reference"] == 14208
            and totals["inapplicable_terminal_point_load_section"] == 1176, "finite residual partition differs")
    missing_kinds = Counter(r["opening_identity_kind"] for r in missing)
    require(missing_kinds == {"finished_geometry_interval": 1162, "modeled_station_exclusion_only": 22},
            "finished void / modeled screw exclusion partition differs")
    result = {"schema": "member-opening-coverage/v1", "status": "COMPLETE_FINITE_SOURCE_JOIN_WITH_EXACT_GAPS",
              "case_ids": list(case_ids), "body_count": 44, "frame_count": 20, "block_count": 24,
              "original_geometry_opening_feature_count": len(features),
              "original_geometry_finished_void_feature_count": sum(f["finished_void_claimed"] for f in features),
              "unmachined_station_exclusion_feature_count": sum(not f["finished_void_claimed"] for f in features),
              "added_spine_bores": [{"body": b, "grain_station_mm": s, "diameter_mm": 7.5,
                  "axis": "v", "fresh_strength_source": "knee-bridge-joint-replay/attempt01"}
                  for b in sorted(method.EXCLUDED) for s in (100, 250)],
              "unchanged_body_trace_partition": dict(totals), "bodies": rows,
              "uncalculated_opening_identity_partition": {k: {"stations": v, "signed_traces": 12*v}
                  for k, v in missing_kinds.items()},
              "opening_feature_inventory": features, "uncalculated_fresh_opening_stations": missing,
              "inapplicable_terminal_stations": excluded,
              "source104_corner_strength_scope": {"finite_cut_limit_count": old_corners["finite_cut_limit_count"],
                  "bodies": sorted(old_corners["geometries"]), "geometry_identity_confirmed": True,
                  "fresh_strength_pass_transferred": False},
              "fresh_modified_spine_scope": {"grain_cut_count": knee["grain_cut_count"],
                  "normal_cut_count": knee["normal_cut_count"],
                  "all_named_reference_screens_satisfied": knee["all_named_reference_screens_satisfied"]},
              "fresh_bore_free_peaks": members["global_peaks"],
              "fresh_top_rail_duration_comparison": top["duration_comparison"],
              "fresh_remaining_family_peaks": {name: r["same_state_peaks"] for name, r in remaining["families"].items()},
              "strength_arithmetic_executed": False, "native_CAD_frame_or_tests_executed": False,
              "splitting_or_fracture_assessed": False, "source104_pass_transferred": False,
              "physical_release": False}
    method.authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "coverage.json", result)
    method.authenticate(pins)
    receipt = {"schema": "member-opening-coverage-receipt/v1", "status": result["status"],
               "source_sha256": method.source_map(pins), "source_closure_scope": "Consumed saved results, their receipts, frame identities and effective timber bytes only; no unconsumed closure rerun.",
               "source_authentication_before_and_after": True,
               "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir())}}
    dump(output / "receipt.json", receipt)
    require(all(sha(output / name) == digest for name, digest in receipt["output_sha256"].items()), "output changed")
    return {"status": result["status"], "counts": dict(totals),
            "missing_station_count": len(missing), "terminal_station_count": len(excluded),
            "source_pin_count": len(pins), "coverage_sha256": sha(output / "coverage.json"),
            "receipt_sha256": sha(output / "receipt.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output), indent=2))
