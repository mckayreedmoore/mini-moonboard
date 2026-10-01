#!/usr/bin/env python3
"""Compare conditional nut projections with the partial washer's timber seat."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
METHOD = PACKETS / "remaining-candidate-washer-seats-2026-10-01/check_support.py"
METHOD_SHA = "a3cedb8e6fddf9d4080afd82cf12cf3e5a39658868baa478ad1f14eee7d07967"
FOOTPRINT_SOURCE = PACKETS / "washer-bearing-footprint-inputs-2026-10-01/parent-review.md"
FOOTPRINT_SHA = "952b5753823048135822985659e8c0150602dd534f005564233fe957e2b291be"
PASSAGES = ROOT / "docs/floor-flush-construction-kerf-right/timber-passages.json"
PASSAGES_SHA = "5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f"
AXIS_ID = "center_principal_right_2"
MEMBER_ID = "base_principal_center_right"
CUT_ID = "bore_base_principal_center_right_072"
AF_MAX_IN = 0.438
AC_MAX_IN = 0.505  # Separate full-hex silhouette, not a flat bearing circle.
NUT_AXIS_ZONE_FRACTION = 0.04


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_method():
    for path, expected in ((METHOD, METHOD_SHA), (FOOTPRINT_SOURCE, FOOTPRINT_SHA),
                           (PASSAGES, PASSAGES_SHA)):
        require(sha(path) == expected, f"source changed: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location("partial_seat_pinned_method", METHOD)
    require(spec is not None and spec.loader is not None, "cannot load pinned method")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def report():
    shared = load_method()
    base, eccentric = shared.methods()
    _, model, bundle, _, input_pins = base.checked_inputs()
    require(model["candidate"] == base.EXPECTED_CANDIDATE
            and model["revision_id"] == base.EXPECTED_REVISION, "candidate/revision changed")
    shared.partition(base, model)  # Preserve the complete 92-axis source partition.
    connections = [r for r in model["connections"] if r.get("axis_id") == AXIS_ID]
    require(len(connections) == 1, "missing/ambiguous affected axis")
    seat = next(s for s in shared.source_seats(connections[0]) if s["role"] == "nut")
    require(seat["member"] == MEMBER_ID and abs(seat["bore_radius_mm"] - 3.65) < 1e-8,
            "affected outer seat/bore changed")
    members = {r["member_id"]: r for r in model["members"]}
    manifests = {r["member_id"]: r for r in bundle["members"]}
    step_pins = {}
    body = shared.import_body(base, MEMBER_ID, members, manifests, {}, step_pins)
    base.matching_seat_planes(body, seat["point"], seat["inward"])
    require(eccentric.step_bore_faces(body, seat["point"], seat["axis"], 3.65) > 0,
            "own bore missing from STEP")
    cuts = [r for r in json.loads(PASSAGES.read_text()) if r["name"] == CUT_ID]
    require(len(cuts) == 1 and cuts[0]["member"] == MEMBER_ID
            and cuts[0]["datums"] == ["F1", "G1"], "service-cut source identity changed")
    cut = cuts[0]
    cut_origin = shared.cq.Vector(*cut["start_mm"])
    cut_axis = shared.cq.Vector(*cut["direction"])
    cut_radius = float(cut["diameter_mm"]) / 2
    require(abs(cut_axis.Length - 1) < 1e-8 and cut_axis.dot(seat["inward"]) >= 1 - 1e-8
            and (cut_axis - shared.cq.Vector(1, 0, 0)).Length < 1e-8
            and abs(cut_radius - 19.05) < 1e-8
            and abs(float(cut["member_entry_mm"]) - seat["point"].x) < 1e-8,
            "service-cut datum/direction/radius changed")
    require((seat["point"] - cut_origin).dot(cut_axis) >= 0
            and (seat["point"] - cut_origin).dot(cut_axis) + max(shared.DEPTHS)
            < float(cut["length_mm"]), "source cut does not cover the inward probes")
    cut_faces = []
    for face in body.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        direction = shared.cq.Vector(*cylinder.Axis().Direction().Coord()).normalized()
        origin = shared.cq.Vector(*cylinder.Axis().Location().Coord())
        if (abs(direction.dot(cut_axis)) >= 1 - 1e-8
                and (cut_origin - origin).cross(direction).Length <= 1e-5
                and abs(float(cylinder.Radius()) - cut_radius) <= 1e-5):
            bounds = face.BoundingBox()
            if (abs(bounds.xmin - float(cut["member_entry_mm"])) <= 1e-5
                    and abs(bounds.xmax - float(cut["member_exit_mm"])) <= 1e-5):
                cut_faces.append([bounds.xmin, bounds.xmax])
    require(bool(cut_faces), "STEP service cylinder axial extent differs from source")
    distance = (seat["point"] - cut_origin).cross(cut_axis).Length
    near_cut_edge = distance - cut_radius
    body_play = seat["bore_radius_mm"] - shared.BODY_DIAMETER / 2
    nut_body_to_thread_offset = AF_MAX_IN * 25.4 * NUT_AXIS_ZONE_FRACTION / 2
    projections = []
    for name, radius, limit in (
        ("declared_circular_end_face", AF_MAX_IN * 25.4 / 2,
         "Explicit flat circular end-face idealization; not an established complete contact patch."),
        ("complete_hex_silhouette_enclosure", AC_MAX_IN * 25.4 / 2,
         "Circumscribed disk covering all hex orientations; not the occupied or loaded nut face."),
    ):
        enclosure_radius = radius + body_play + nut_body_to_thread_offset
        inside = [eccentric.inward_envelope(body, seat, enclosure_radius, d)
                  for d in shared.DEPTHS]
        outside = [eccentric.outward_envelope(body, seat, enclosure_radius, d)
                   for d in shared.DEPTHS]
        contained = min(r["support_fraction"] for r in inside) >= 1 - shared.TOL
        clear = max(r["overlap_fraction"] for r in outside) <= shared.TOL
        projections.append({"scenario": name, "shape_radius_mm": radius,
                            "enclosure_radius_mm": enclosure_radius,
                            "service_cut_clearance_budget_mm": near_cut_edge - enclosure_radius,
                            "inward": inside, "outward": outside,
                            "outside_own_bore_contained": contained,
                            "near_face_outward_clear": clear, "limit": limit})
    passed = sum(s["outside_own_bore_contained"] and s["near_face_outward_clear"]
                 for s in projections)
    return {"status": "ALL_PROJECTION_ENCLOSURES_CONTAINED" if passed == len(projections)
            else "PROJECTION_ENCLOSURE_EXCEPTIONS", "passed_projection_count": passed,
            "candidate": model["candidate"], "revision": model["revision_id"],
            "axis_id": AXIS_ID, "role": "nut", "member": MEMBER_ID,
            "point_xyz_mm": list(seat["point"].toTuple()),
            "input_pins": input_pins, "method_sha256": METHOD_SHA,
            "footprint_source_sha256": FOOTPRINT_SHA, "passages_sha256": PASSAGES_SHA,
            "finished_step_pins": step_pins,
            "service_cut": {"id": CUT_ID, "origin_xyz_mm": list(cut_origin.toTuple()),
                            "radius_mm": cut_radius, "center_distance_mm": distance,
                            "nearest_edge_mm": near_cut_edge,
                            "source_length_mm": cut["length_mm"],
                            "step_face_axial_bounds_x_mm": cut_faces},
            "conditional_nominal_body_mm": shared.BODY_DIAMETER,
            "body_to_bore_play_mm": body_play,
            "nut_body_to_thread_offset_mm": nut_body_to_thread_offset,
            "projections": projections,
            "claim_limits": {"nut_thread_coaxial_with_bolt_assumed": True,
                             "actual_minimum_shank_or_thread_play_bound": False,
                             "tilt_or_seat_tolerance_bound": False,
                             "own_bore_supported": False,
                             "washer_outer_annulus_supported": False,
                             "contact_patch_or_pressure_established": False,
                             "metal_or_wood_strength": False, "joint_accepted": False,
                             "model_changed": False, "native_solve": False}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", required=True, action="store_true")
    parser.parse_args()
    result = report()
    print(json.dumps(result, indent=2, allow_nan=False))
    return int(any(not s["outside_own_bore_contained"] or not s["near_face_outward_clear"]
                   for s in result["projections"]))


if __name__ == "__main__":
    raise SystemExit(main())
