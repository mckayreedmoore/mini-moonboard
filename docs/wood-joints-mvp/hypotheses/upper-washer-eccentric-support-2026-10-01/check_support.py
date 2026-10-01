#!/usr/bin/env python3
"""Extend the existing conditional eccentric seat method to 32 upper bolts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
HELPER = PACKETS / "remaining-candidate-washer-seats-2026-10-01/check_support.py"
HELPER_SHA = "a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967"
AREA_TOLERANCE_MM2 = 2e-5
SAMPLE_ANGLES_DEG = (0, 90, 180, 270)


def helper():
    import hashlib

    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("pinned remaining-seat helper changed")
    spec = importlib.util.spec_from_file_location("pinned_upper_seat_extension", HELPER)
    if spec is None or spec.loader is None:
        raise ValueError("cannot import pinned seat helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def area_oracle_pass(samples):
    return bool(samples) and all(math.isfinite(r["error_mm2"])
                                 and 0 <= r["error_mm2"] <= AREA_TOLERANCE_MM2
                                 for r in samples)


def report():
    shared = helper()
    base, eccentric = shared.methods()
    _, model, bundle, hardware, pins = base.checked_inputs()
    shared.require(model["candidate"] == bundle["candidate"] == base.EXPECTED_CANDIDATE
                   and model["revision_id"] == bundle["geometry_revision_id"] == base.EXPECTED_REVISION,
                   "candidate/revision identity changed")
    remaining, primary, upper = shared.partition(base, model)
    selected = sorted((r for r in model["connections"]
                       if r.get("kind") == "candidate_bolt" and r["axis_id"] in upper),
                      key=lambda r: r["axis_id"])
    shared.require(len(selected) == len(upper) == 32, "upper cohort is incomplete")
    members = {r["member_id"]: r for r in model["members"]}
    manifests = {r["member_id"]: r for r in bundle["members"]}
    washer = hardware["dimension_inputs"]["washer"]
    imin, imax = [float(v) * 25.4 for v in washer["id_in"]]
    omin, omax = [float(v) * 25.4 for v in washer["od_in"]]
    shared.require(shared.BODY_DIAMETER < imin <= imax < omin <= omax,
                   "washer bounds changed")
    frame_text = (ROOT / base.WOOD_FRAME_SOURCE).read_text()
    cad_od = base.source_number(frame_text, "WASHER_OD_MM")
    cad_id = base.source_number(frame_text, "WASHER_ID_MM")
    scenarios = [("CAD", cad_od, cad_id)] + [
        (f"plain_OD_{od:g}_ID_{ident:g}", od, ident)
        for od in (omin, omax) for ident in (imin, imax)]
    shapes, step_pins, rows = {}, {}, []
    for connection in selected:
        for seat in shared.source_seats(connection):
            body = shared.import_body(base, seat["member"], members, manifests,
                                      shapes, step_pins)
            planes = base.matching_seat_planes(body, seat["point"], seat["inward"])
            shared.require(eccentric.step_bore_faces(body, seat["point"], seat["axis"],
                                                    seat["bore_radius_mm"]) > 0,
                           "source bore absent from STEP")
            bore_play = seat["bore_radius_mm"] - shared.BODY_DIAMETER / 2
            max_offset = bore_play + (max(imax, cad_id) - shared.BODY_DIAMETER) / 2
            sweep_radius = max(omax, cad_od) / 2 + max_offset
            inside = [eccentric.inward_envelope(body, seat, sweep_radius, depth)
                      for depth in shared.DEPTHS]
            outside = [eccentric.outward_envelope(body, seat, sweep_radius, depth)
                       for depth in shared.DEPTHS]
            contained = min(r["support_fraction"] for r in inside) >= 1 - shared.TOL
            clear = max(r["overlap_fraction"] for r in outside) <= shared.TOL
            areas = []
            for name, od, ident in scenarios:
                for mode, offset in (("bolt_held", (ident - shared.BODY_DIAMETER) / 2),
                                     ("combined", bore_play + (ident - shared.BODY_DIAMETER) / 2)):
                    areas.append({"scenario": name, "mode": mode, "offset_mm": offset,
                                  "area_mm2": eccentric.hole_only_area(
                                      od, ident, 2 * seat["bore_radius_mm"], offset),
                                  "applicable": contained})
            # These samples check the area oracle, not the continuum enclosure.
            samples = []
            if contained:
                u, v = eccentric.tangent_basis(seat["axis"])
                sample_offset = bore_play + (imax - shared.BODY_DIAMETER) / 2
                expected = eccentric.hole_only_area(omax, imax,
                                                   2 * seat["bore_radius_mm"], sample_offset)
                for angle in SAMPLE_ANGLES_DEG:
                    radians = math.radians(angle)
                    direction = u * math.cos(radians) + v * math.sin(radians)
                    measured = eccentric.measurement(base, body, seat["member"],
                                                      seat["point"] + direction * sample_offset,
                                                      seat["inward"], omax, imax)
                    for row in measured:
                        error = abs(row["supported_area_mm2"] - expected)
                        samples.append({"angle_deg": angle, "depth_mm": row["depth_mm"],
                                        "area_mm2": row["supported_area_mm2"], "error_mm2": error})
            oracle_ok = area_oracle_pass(samples) if contained else False
            rows.append({"axis_id": seat["axis_id"], "role": seat["role"],
                         "member": seat["member"], "point_xyz_mm": list(seat["point"].toTuple()),
                         "bore_radius_mm": seat["bore_radius_mm"],
                         "receiver_count": seat["receiver_count"],
                         "plane_offset_mm": max(r["plane_offset_mm"] for r in planes),
                         "combined_offset_bound_mm": max_offset,
                         "sweep_radius_mm": sweep_radius, "inward": inside, "outward": outside,
                         "hole_only_applicable": contained, "outward_clearance": clear,
                         "conditional_hole_only_areas": areas, "direct_area_samples": samples,
                         "sample_area_oracle_pass": oracle_ok,
                         "geometry_screen_pass": contained and clear and oracle_ok})
    shared.require(len(rows) == len({(r["axis_id"], r["role"]) for r in rows}) == 64,
                   "incomplete upper outer-seat coverage")
    failures = [{k: r[k] for k in ("axis_id", "role", "member", "hole_only_applicable",
                                 "outward_clearance", "sample_area_oracle_pass")}
                for r in rows if not r["geometry_screen_pass"]]
    return {"status": "GEOMETRY_EXCEPTIONS" if failures else "PASS_CONDITIONAL_GEOMETRY_ONLY",
            "candidate": model["candidate"], "revision": model["revision_id"],
            "input_pins": pins, "helper_sha256": HELPER_SHA,
            "method_pins": shared.PINNED_METHODS, "cohort_pins": shared.UPPER_PINS,
            "finished_step_pins": step_pins,
            "excluded_primary_axes": primary,
            "excluded_remaining_axes": [r["axis_id"] for r in remaining],
            "counts": {"axes": len(selected), "seats": len(rows), "members": len(shapes)},
            "bore_radius_counts": dict(Counter(r["bore_radius_mm"] for r in rows)),
            "probe_depths_mm": shared.DEPTHS, "fraction_tolerance": shared.TOL,
            "sample_area_tolerance_mm2": AREA_TOLERANCE_MM2,
            "conditional_body_diameter_mm": shared.BODY_DIAMETER,
            "washer_id_bounds_mm": [imin, imax], "washer_od_bounds_mm": [omin, omax],
            "samples_are_continuum_proof": False, "failures": failures, "seats": rows,
            "claim_limits": {"geometry_only": True, "delivered_or_minimum_shank_bound": False,
                             "seat_tolerance_or_tilt": False, "pressure_or_strength": False,
                             "actual_inspection": False, "joint_accepted": False,
                             "six_case_envelope": False, "native_solve": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--oracle-fixture", action="store_true")
    args = parser.parse_args()
    if args.oracle_fixture:
        shared = helper()
        base, eccentric = shared.methods()
        # Run the actual BREP measurement on a known bored rectangular seat.
        body = shared.cq.Workplane("XY").box(40, 40, 10).val()
        point, inward = shared.cq.Vector(0, 0, -5), shared.cq.Vector(0, 0, 1)
        body = body.cut(shared.cq.Solid.makeCylinder(3.75, 10, point, inward))
        expected = eccentric.hole_only_area(19.0246, 8.3058, 7.5, 1.5529)
        measured = eccentric.measurement(base, body, "fixture", point + shared.cq.Vector(1.5529, 0, 0),
                                         inward, 19.0246, 8.3058)
        samples = [{"error_mm2": abs(r["supported_area_mm2"] - expected)} for r in measured]
        shared.require(area_oracle_pass(samples), "known area fixture failed")
        corrupted = [dict(r) for r in samples]
        corrupted[1]["error_mm2"] += 2 * AREA_TOLERANCE_MM2
        shared.require(not area_oracle_pass(corrupted), "corrupted area escaped gate")
        shared.require(not area_oracle_pass([])
                       and not area_oracle_pass([{"error_mm2": math.nan}]),
                       "empty/nonfinite oracle escaped gate")
        result = {"status": "PASS_KNOWN_AREA_AND_CORRUPTED_ORACLE_REJECTION",
                  "max_area_error_mm2": max(r["error_mm2"] for r in samples)}
    else:
        result = report()
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(bool(result.get("failures")))


if __name__ == "__main__":
    raise SystemExit(main())
