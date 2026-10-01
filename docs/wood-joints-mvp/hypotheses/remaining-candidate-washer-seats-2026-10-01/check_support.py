#!/usr/bin/env python3
"""Check the 54 candidate bolts outside the primary and upper washer packets."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from itertools import pairwise
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
PINNED_METHODS = {
    "base": ("corner-washer-support-2026-10-01/check_support.py",
             "9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57"),
    "eccentric": ("corner-washer-eccentric-support-2026-10-01/check_eccentric_support.py",
                  "97b6426cdc84364bfe8967d491906189b153d8805bbd53290f08dc5f730ce035"),
}
UPPER_PINS = {
    "upper-frame-joint-review-2026-09-30/upper-joints.json":
        "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    "service-upper-frame-joint-review-2026-09-30/upper-joints.json":
        "f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f",
}
DEPTHS = (0.01, 0.05, 0.1)
TOL = 1e-7
BODY_DIAMETER = 6.35  # Nominal scenario, not a delivered-shank minimum.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def methods():
    loaded = {}
    for name, (relative, expected) in PINNED_METHODS.items():
        path = PACKETS / relative
        require(sha(path) == expected, f"pinned {name} method changed")
        spec = importlib.util.spec_from_file_location(f"remaining_seats_{name}", path)
        require(spec is not None and spec.loader is not None, "method import unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded["base"], loaded["eccentric"]


def partition(base, model):
    connections = [r for r in model["connections"] if r.get("kind") == "candidate_bolt"]
    ids = {r["axis_id"] for r in connections}
    require(len(connections) == len(ids) == 92, "candidate-axis inventory changed")
    upper = set()
    for relative, expected in UPPER_PINS.items():
        path = PACKETS / relative
        require(sha(path) == expected, f"upper exclusion source changed: {relative}")
        cohort = {r["axis_id"] for r in json.loads(path.read_text())["bolt_actions"]}
        require(len(cohort) == 16 and not upper.intersection(cohort), "upper cohorts overlap")
        upper.update(cohort)
    primary = {axis for group in base.AXIS_GROUPS.values() for axis in group}
    require(len(primary) == 6 and len(upper) == 32 and not primary.intersection(upper),
            "primary/upper ownership partition changed")
    require(primary.union(upper).issubset(ids), "excluded axis missing from current model")
    remaining = ids - primary - upper
    require(len(remaining) == 54, "expected 54 remaining candidate bolts")
    return sorted((r for r in connections if r["axis_id"] in remaining),
                  key=lambda r: r["axis_id"]), sorted(primary), sorted(upper)


def import_body(base, body_id, members, bundle_members, cache, step_pins):
    if body_id in cache:
        return cache[body_id]
    binding = members[body_id]["current_finished_step_binding"]
    manifest = bundle_members[body_id]
    relative = Path(binding["path"])
    require(manifest["step_file"] == relative.relative_to(base.MEMBER_BUNDLE.parents[1]).as_posix()
            and manifest["step_sha256"] == binding["file_sha256"],
            f"STEP manifest/model binding differs: {body_id}")
    path = ROOT / relative
    require(sha(path) == binding["file_sha256"], f"finished STEP changed: {body_id}")
    solids = cq.importers.importStep(str(path)).val().Solids()
    summary = manifest["step_roundtrip_summary"]
    require(len(solids) == 1 and solids[0].isValid()
            and len(solids[0].Faces()) == summary["face_count"]
            and abs(solids[0].Volume() - float(summary["volume_mm3"])) < 0.001,
            f"finished STEP round trip differs: {body_id}")
    cache[body_id] = solids[0]
    step_pins[body_id] = {"path": relative.as_posix(), "sha256": binding["file_sha256"]}
    return solids[0]


def source_seats(connection):
    geometry = connection["source_record"]["geometry"]
    axis = cq.Vector(*geometry["axis_head_to_nut_global"])
    require(abs(axis.Length - 1) < 1e-8, "nonunit source bolt direction")
    diameter = float(geometry["modeled_shaft_diameter_mm"])
    require(abs(diameter - BODY_DIAMETER) < 1e-8, "nominal body scenario changed")
    origin = (cq.Vector(*geometry["shaft_center_global_xyz_mm"])
              - axis * float(geometry["modeled_underhead_to_tip_mm"]) / 2)
    receivers = geometry["wood_receiver_intervals"]
    require(len(receivers) in (2, 3), "unexpected wood receiver count")
    require(len({r["receiver_id"] for r in receivers}) == len(receivers),
            "duplicate wood receiver")
    intervals = []
    for receiver in receivers:
        values = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
        require(len(values) == 1 and len(values[0]) == 2, "ambiguous receiver interval")
        start, end = map(float, values[0])
        require(math.isfinite(start) and math.isfinite(end) and 0 <= start < end,
                "invalid receiver interval")
        intervals.append((start, end, receiver["receiver_id"]))
    intervals.sort()
    require(all(a[1] <= b[0] + 1e-6 for a, b in pairwise(intervals)),
            "overlapping receiver intervals")
    # There is no middle washer on a continuous three-receiver bolt.
    for role, interval, station, inward in (
        ("head", intervals[0], intervals[0][0], axis),
        ("nut", intervals[-1], intervals[-1][1], -axis),
    ):
        body_id = interval[2]
        bores = [r for r in connection["receiver_clearance_geometry"]
                 if r["receiver_id"] == body_id]
        require(len(bores) == 1 and bores[0]["result_status"] == "unique_coaxial_bore_radius",
                "ambiguous source bore")
        radius = float(bores[0]["unique_bore_radius_mm"])
        require(math.isfinite(radius) and radius > diameter / 2
                and abs(float(bores[0]["modeled_shaft_diameter_mm"]) - diameter) < 1e-8,
                "invalid source body/bore distinction")
        yield {"axis_id": connection["axis_id"], "role": role, "member": body_id,
               "point": origin + axis * station, "axis": axis, "inward": inward,
               "bore_radius_mm": radius, "receiver_count": len(receivers)}


def report():
    base, eccentric = methods()
    _, model, bundle, hardware, input_pins = base.checked_inputs()
    require(model["candidate"] == bundle["candidate"] == base.EXPECTED_CANDIDATE
            and model["revision_id"] == bundle["geometry_revision_id"] == base.EXPECTED_REVISION,
            "candidate/revision identity differs")
    connections, primary, upper = partition(base, model)
    members = {r["member_id"]: r for r in model["members"]}
    bundle_members = {r["member_id"]: r for r in bundle["members"]}
    source = hardware["dimension_inputs"]["washer"]
    imin, imax = [float(x) * 25.4 for x in source["id_in"]]
    omin, omax = [float(x) * 25.4 for x in source["od_in"]]
    require(BODY_DIAMETER < imin <= imax < omin <= omax, "invalid catalog ring bounds")
    text = (ROOT / base.WOOD_FRAME_SOURCE).read_text()
    cad = (base.source_number(text, "WASHER_OD_MM"), base.source_number(text, "WASHER_ID_MM"))
    nominal = [("CAD", *cad), ("plain_minimum_area", omin, imax),
               ("plain_outer_envelope", omax, imin)]
    analytic = [("CAD", *cad)] + [(f"plain_OD_{od:g}_ID_{ident:g}", od, ident)
                                         for od in (omin, omax) for ident in (imin, imax)]
    shapes, step_pins, rows = {}, {}, []
    for connection in connections:
        for seat in source_seats(connection):
            body = import_body(base, seat["member"], members, bundle_members, shapes, step_pins)
            planes = base.matching_seat_planes(body, seat["point"], seat["inward"])
            require(eccentric.step_bore_faces(body, seat["point"], seat["axis"],
                                            seat["bore_radius_mm"]) > 0,
                    f"recorded bore absent from STEP: {seat['axis_id']}/{seat['role']}")
            nominal_results = []
            for name, od, ident in nominal:
                inside = eccentric.measurement(base, body, seat["member"], seat["point"],
                                               seat["inward"], od, ident)
                outside = eccentric.measurement(base, body, seat["member"], seat["point"],
                                                -seat["inward"], od, ident)
                low = min(r["support_fraction"] for r in inside)
                high = max(r["support_fraction"] for r in outside)
                nominal_results.append({"scenario": name, "inward_min": low,
                                        "outward_max": high,
                                        "inward_measurements": inside,
                                        "outward_measurements": outside,
                                        "supported": low >= 1 - TOL and high <= TOL})
            max_offset = (seat["bore_radius_mm"] - BODY_DIAMETER / 2
                          + (max(imax, cad[1]) - BODY_DIAMETER) / 2)
            sweep = max(omax, cad[0]) / 2 + max_offset
            inside = [eccentric.inward_envelope(body, seat, sweep, d) for d in DEPTHS]
            outside = [eccentric.outward_envelope(body, seat, sweep, d) for d in DEPTHS]
            contained = min(r["support_fraction"] for r in inside) >= 1 - TOL
            clear = max(r["overlap_fraction"] for r in outside) <= TOL
            areas = []
            for name, od, ident in analytic:
                for mode, offset in (("bolt_held", (ident - BODY_DIAMETER) / 2),
                                     ("combined", seat["bore_radius_mm"] - BODY_DIAMETER / 2
                                      + (ident - BODY_DIAMETER) / 2)):
                    areas.append({"scenario": name, "mode": mode, "offset_mm": offset,
                                  "supported_area_mm2": eccentric.hole_only_area(
                                      od, ident, 2 * seat["bore_radius_mm"], offset),
                                  "hole_only_applicable": contained})
            rows.append({"axis_id": seat["axis_id"], "role": seat["role"],
                         "member": seat["member"], "bore_radius_mm": seat["bore_radius_mm"],
                         "receiver_count": seat["receiver_count"],
                         "point_xyz_mm": list(seat["point"].toTuple()),
                         "max_plane_offset_mm": max(r["plane_offset_mm"] for r in planes),
                         "nominal": nominal_results, "sweep_radius_mm": sweep,
                         "swept_inward": inside, "swept_outward": outside,
                         "all_direction_hole_only_applicable": contained,
                         "outward_clearance": clear, "conditional_hole_only_areas": areas,
                         "geometry_screen_pass": all(r["supported"] for r in nominal_results)
                         and contained and clear})
    require(len(rows) == 108 and len({(r["axis_id"], r["role"]) for r in rows}) == 108,
            "incomplete outer-seat coverage")
    failures = [{k: r[k] for k in ("axis_id", "role", "member")}
                for r in rows if not r["geometry_screen_pass"]]
    return {"status": "PASS_GEOMETRY_ONLY" if not failures else "GEOMETRY_EXCEPTIONS",
            "candidate": model["candidate"], "revision": model["revision_id"],
            "counts": {"axes": len(connections), "seats": len(rows), "members": len(shapes)},
            "excluded_primary_axes": primary, "excluded_upper_axes": upper,
            "input_pins": input_pins, "method_pins": PINNED_METHODS,
            "upper_exclusion_pins": UPPER_PINS, "finished_step_pins": step_pins,
            "bore_radius_counts": dict(Counter(r["bore_radius_mm"] for r in rows)),
            "probe_depths_mm": DEPTHS, "fraction_tolerance": TOL,
            "conditional_body_diameter_mm": BODY_DIAMETER, "failures": failures, "seats": rows,
            "claim_limits": {"geometry_only": True, "actual_inspection": False,
                             "delivered_shank_bound": False, "tilt_or_seat_tolerance": False,
                             "pressure_or_strength": False, "joint_accepted": False,
                             "six_case_envelope": False, "native_solve": False,
                             "semantic_cut_inventory": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--check", action="store_true")
    options.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        base, eccentric = methods()
        result = {"base_production_fixtures": base.self_test(),
                  "eccentric_production_fixtures": eccentric.self_test(base)}
        # Invalid interval input must fail before producing a seat.
        bad = {"source_record": {"geometry": {"axis_head_to_nut_global": [0, 1, 0],
               "modeled_shaft_diameter_mm": 6.35, "shaft_center_global_xyz_mm": [0, 0, 0],
               "modeled_underhead_to_tip_mm": 100, "wood_receiver_intervals": [
                   {"receiver_id": "a", "current_shaft_intersection_solid_intervals_from_underhead_mm": [[1, 3], [4, 5]]},
                   {"receiver_id": "b", "current_shaft_intersection_solid_intervals_from_underhead_mm": [[6, 10]]}]}}}
        try:
            list(source_seats(bad))
        except ValueError:
            result["ambiguous_source_interval_rejected"] = True
        else:
            raise AssertionError("ambiguous interval fixture was accepted")
    else:
        result = report()
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(result.get("status") == "GEOMETRY_EXCEPTIONS")


if __name__ == "__main__":
    raise SystemExit(main())
