#!/usr/bin/env python3
"""Check conditional washer eccentricity on frozen primary-corner STEP solids."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import cadquery as cq
import OCP

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from mini_moonboard.wood_joint_geometry import WasherSeat, washer_support_report

PACKET = Path("docs/wood-joints-mvp/hypotheses/corner-washer-support-2026-10-01")
CHECKER = PACKET / "check_support.py"
BASE_README = PACKET / "README.md"
FASTENERS = Path(
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fasteners.md"
)
SHA = {
    "prior_checker": "9b3b773c2f7f1a51d5b5f9902ff288644133f67f63575a7c3a37168028e0dc57",
    "prior_readme": "fc6e1c62fc712866554f85d8e90a8779e84e2ef635581e97e8130383218d7db6",
    "fasteners": "aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6",
}
INCH_MM = 25.4
BOLT_D_MM = 6.35  # Recorded nominal smooth-body geometry scenario, not a delivered bound.
BORE_D_MM = 7.5
DEPTHS_MM = (0.01, 0.05, 0.1)
ANGLES_DEG = (0, 45, 90)  # Diagnostic samples only; continuum proof is the swept BREP test.
TOL = 1e-7
PLANE_TOLERANCE_MM = 1e-5
AREA_TOLERANCE_MM2 = 2e-5


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def near(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(b))


def disk_intersection(r1: float, r2: float, d: float) -> float:
    """Exact area of two disk intersections, including disjoint/tangent cases."""
    a, b, d = float(r1), float(r2), float(d)
    require(all(math.isfinite(x) for x in (a, b, d)) and a > 0 and b > 0 and d >= 0,
            "circle radii must be positive and distance nonnegative")
    if d >= a + b:
        return 0.0
    if d <= abs(a - b):
        return math.pi * min(a, b) ** 2
    ca = max(-1.0, min(1.0, (d*d + a*a - b*b) / (2*d*a)))
    cb = max(-1.0, min(1.0, (d*d + b*b - a*a) / (2*d*b)))
    root = math.sqrt(max(0.0, (-d+a+b)*(d+a-b)*(d-a+b)*(d+a+b)))
    return a*a*math.acos(ca) + b*b*math.acos(cb) - root/2


def annulus_area(od: float, ident: float) -> float:
    require(math.isfinite(od) and math.isfinite(ident) and 0 < ident < od,
            "invalid washer annulus dimensions")
    return math.pi * (od*od - ident*ident) / 4


def hole_only_area(od: float, ident: float, bore: float, offset: float) -> float:
    """Supported area if the only missing wood is the circular receiver bore."""
    ro, ri, rb = od/2, ident/2, bore/2
    require(0 < rb < ro and 0 < ri < ro and math.isfinite(offset) and offset >= 0,
            "invalid annulus, bore, or offset")
    area = annulus_area(od, ident)
    missing = disk_intersection(rb, ro, offset) - disk_intersection(rb, ri, offset)
    return min(area, max(0.0, area - max(0.0, missing)))


def prior_checker() -> Any:
    for label, path in (("prior_checker", CHECKER), ("prior_readme", BASE_README)):
        require(digest(ROOT / path) == SHA[label], f"pinned {label} changed")
    spec = importlib.util.spec_from_file_location("pinned_corner_washer_check", ROOT / CHECKER)
    require(spec is not None and spec.loader is not None, "cannot load prior checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def measurement(checker: Any, body: cq.Shape, body_id: str, point: cq.Vector,
                inward: cq.Vector, od: float, ident: float) -> list[dict[str, float]]:
    """Run the pinned production annulus/STEP Boolean at each depth."""
    hardware = checker.hardware_for(od, ident)
    seat = WasherSeat(body_id, point, inward)
    area = annulus_area(od, ident)
    result = []
    for depth in DEPTHS_MM:
        report = washer_support_report(seat, body, hardware, probe_depth_mm=depth)
        fraction = float(report.support_fraction)
        require(math.isfinite(fraction) and -TOL <= fraction <= 1 + TOL,
                f"out-of-range BREP support at {body_id}")
        fraction = min(1.0, max(0.0, fraction))
        result.append({
            "depth_mm": depth,
            "support_fraction": fraction,
            "supported_area_mm2": area * fraction,
        })
    return result


def inward_envelope(body: cq.Shape, seat: dict[str, Any], outer_radius: float,
                    depth: float) -> dict[str, float]:
    axis = seat["inward"].normalized()
    outer = cq.Solid.makeCylinder(outer_radius, depth, seat["point"], axis)
    bore = cq.Solid.makeCylinder(seat["bore_radius_mm"], depth, seat["point"], axis)
    swept_annulus = outer.cut(bore)
    expected = math.pi * (outer_radius**2 - seat["bore_radius_mm"]**2) * depth
    actual = swept_annulus.intersect(body).Volume()
    fraction = actual / expected
    require(math.isfinite(fraction) and -TOL <= fraction <= 1 + TOL,
            "out-of-range inward swept-envelope fraction")
    fraction = min(1.0, max(0.0, fraction))
    return {"depth_mm": depth, "support_fraction": fraction,
            "unsupported_volume_mm3": max(0.0, expected-actual)}


def outward_envelope(body: cq.Shape, seat: dict[str, Any], radius: float,
                     depth: float) -> dict[str, float]:
    volume = math.pi * radius**2 * depth
    probe = cq.Solid.makeCylinder(radius, depth, seat["point"], seat["inward"].normalized() * -1)
    overlap = probe.intersect(body).Volume()
    fraction = overlap / volume
    require(math.isfinite(fraction) and -TOL <= fraction <= 1 + TOL,
            "out-of-range outward swept-envelope fraction")
    return {"depth_mm": depth, "overlap_fraction": min(1.0, max(0.0, fraction)),
            "overlap_volume_mm3": overlap}


def step_bore_faces(body: cq.Shape, point: cq.Vector, axis: cq.Vector,
                    radius: float) -> int:
    matches = 0
    for face in body.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = face._geomAdaptor().Cylinder()
        direction = cq.Vector(*cylinder.Axis().Direction().Coord()).normalized()
        origin = cq.Vector(*cylinder.Axis().Location().Coord())
        alignment = abs(direction.dot(axis.normalized()))
        offset = (point-origin).cross(direction).Length
        if (alignment >= 1-1e-8 and offset <= 1e-5
                and abs(float(cylinder.Radius())-radius) <= 1e-5):
            matches += 1
    return matches


def load_seats(checker: Any, model: dict[str, Any], screen: dict[str, Any],
               bundle: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, cq.Shape]]:
    members = {row["member_id"]: row for row in model["members"]}
    bundle_members = {row["member_id"]: row for row in bundle["members"]}
    screen_axes = {row["axis_id"]: row for row in screen["axes"]}
    connections = {row["axis_id"]: row for row in model["connections"]
                   if row.get("kind") == "candidate_bolt"}
    require(len(connections) == 92, "reviewed candidate-axis count changed")
    shapes: dict[str, cq.Shape] = {}
    seats: list[dict[str, Any]] = []

    for group, axes in checker.AXIS_GROUPS.items():
        for axis_id in axes:
            connection = connections[axis_id]
            geometry = connection["source_record"]["geometry"]
            axis = cq.Vector(*geometry["axis_head_to_nut_global"]).normalized()
            center = cq.Vector(*geometry["shaft_center_global_xyz_mm"])
            shaft_d = float(geometry["modeled_shaft_diameter_mm"])
            require(near(shaft_d, BOLT_D_MM), f"recorded shaft diameter changed: {axis_id}")
            underhead = center - axis * float(geometry["modeled_underhead_to_tip_mm"]) / 2
            receivers = sorted(geometry["wood_receiver_intervals"], key=lambda row:
                row["current_shaft_intersection_solid_intervals_from_underhead_mm"][0][0])
            require(len(receivers) in (2, 3), f"unexpected receiver count: {axis_id}")
            seats_by_role = {row["seat_role"]: row for row in screen_axes[axis_id]["outer_seats"]}
            ends = (
                ("head_washer_seat", receivers[0],
                 float(receivers[0]["current_shaft_intersection_solid_intervals_from_underhead_mm"][0][0])),
                ("nut_washer_seat", receivers[-1],
                 float(receivers[-1]["current_shaft_intersection_solid_intervals_from_underhead_mm"][0][1])),
            )
            for role, receiver, station in ends:
                record = seats_by_role[role]
                body_id = str(receiver["receiver_id"])
                point = cq.Vector(*record["seat_point_xyz_mm"])
                require((underhead + axis*station-point).Length <= PLANE_TOLERANCE_MM,
                        f"seat coordinate changed: {axis_id}/{role}")
                bore_rows = [row for row in connection["receiver_clearance_geometry"]
                             if row.get("receiver_id") == body_id]
                require(len(bore_rows) == 1 and bore_rows[0].get("result_status") == "unique_coaxial_bore_radius",
                        f"ambiguous recorded bore: {axis_id}/{role}")
                bore_r = float(bore_rows[0]["unique_bore_radius_mm"])
                require(near(2*bore_r, BORE_D_MM) and near(float(bore_rows[0]["modeled_shaft_diameter_mm"]), shaft_d)
                        and near(float(record["modeled_finished_wood_bore_radius_mm"]), bore_r),
                        f"6.35 mm modeled body/7.5 mm bore source distinction changed: {axis_id}/{role}")
                if body_id not in shapes:
                    member = members[body_id]
                    binding = member["current_finished_step_binding"]
                    manifest = bundle_members[body_id]
                    step_path = Path(binding["path"])
                    require(manifest["step_file"] == step_path.relative_to(checker.MEMBER_BUNDLE.parents[1]).as_posix()
                            and manifest["step_sha256"] == binding["file_sha256"],
                            f"STEP bundle binding changed: {body_id}")
                    require(digest(ROOT / step_path) == binding["file_sha256"], f"STEP hash changed: {body_id}")
                    imported = cq.importers.importStep(str(ROOT / step_path)).val().Solids()
                    summary = manifest["step_roundtrip_summary"]
                    require(len(imported) == 1 and imported[0].isValid()
                            and len(imported[0].Faces()) == summary["face_count"]
                            and abs(imported[0].Volume()-float(summary["volume_mm3"])) < .001,
                            f"STEP import differs from pinned round trip: {body_id}")
                    shapes[body_id] = imported[0]
                body = shapes[body_id]
                require(step_bore_faces(body, point, axis, bore_r) > 0,
                        f"recorded 7.5 mm bore not found in STEP: {axis_id}/{role}")
                inward = axis if role == "head_washer_seat" else -axis
                planes = checker.matching_seat_planes(body, point, inward)
                seats.append({"group": group, "axis_id": axis_id, "role": role,
                              "member": body_id, "point": point, "axis": axis,
                              "inward": inward, "bore_radius_mm": bore_r,
                              "shaft_diameter_mm": shaft_d,
                              "bolt_bore_radial_clearance_mm": bore_r-shaft_d/2,
                              "seat_plane_offset_mm": max(float(row["plane_offset_mm"]) for row in planes)})
    require(len(seats) == 12, "expected twelve primary-corner outer washer seats")
    return seats, shapes


def scenarios(hardware: dict[str, Any], fastener_text: str) -> list[dict[str, Any]]:
    washer = hardware["dimension_inputs"]["washer"]
    id_range = tuple(float(value) for value in washer["id_in"])
    od_sources = [
        ("K.L. Jack 25NWUS plain Type A Wide", tuple(float(x) for x in washer["od_in"]),
         "directly recorded catalog dimensions"),
        ("K.L. Jack 25NWUS8Z F436 Type A Wide", (.729, .749),
         "mixed-source sensitivity: F436 OD with 25NWUS ID range, not a matched product envelope"),
    ]
    require("25NWUS8Z" in fastener_text and "listed OD range is 0.729–0.749 in" in fastener_text,
            "pinned F436 OD source changed")
    result = []
    for od_name, ods, relation in od_sources:
        for od_bound, od in zip(("OD minimum", "OD maximum"), ods, strict=True):
            for id_bound, ident in zip(("ID minimum", "ID maximum"), id_range, strict=True):
                result.append({"name": f"{od_name} / {od_bound} / {id_bound}",
                               "od_source": od_name, "id_source": washer["source"],
                               "source_relationship": relation, "od_in": od, "id_in": ident,
                               "od_mm": od*INCH_MM, "id_mm": ident*INCH_MM})
    return result


def offset_modes(ident: float, bore: float) -> list[dict[str, Any]]:
    washer_play = (ident-BOLT_D_MM)/2
    bore_play = (bore-BOLT_D_MM)/2
    require(washer_play >= 0 and bore_play >= 0, "negative radial clearance scenario")
    return [
        {"name": "bolt held on modeled bore axis; washer at body/hole contact",
         "bolt_axis_offset_mm": 0.0, "offset_mm": washer_play},
        {"name": "combined bolt/bore clearance plus washer play, aligned radially",
         "bolt_axis_offset_mm": bore_play, "offset_mm": bore_play+washer_play},
    ]


def tangent_basis(axis: cq.Vector) -> tuple[cq.Vector, cq.Vector]:
    refs = (cq.Vector(1, 0, 0), cq.Vector(0, 1, 0), cq.Vector(0, 0, 1))
    ref = min(refs, key=lambda item: abs(item.dot(axis.normalized())))
    u = axis.normalized().cross(ref).normalized()
    return u, axis.normalized().cross(u).normalized()


def enforce_geometry_gate(containment: bool, outward_clearance: bool,
                          area_errors: list[float]) -> None:
    """Fail a check when its swept geometry or direct area oracle disagrees."""
    require(containment, "inward swept region lacks full BREP support")
    require(outward_clearance, "outward swept region intersects the BREP")
    require(bool(area_errors), "no direct STEP/formula area comparisons")
    require(all(math.isfinite(error) and 0 <= error <= AREA_TOLERANCE_MM2
                for error in area_errors), "direct STEP/formula area comparison failed")


def self_test(checker: Any) -> dict[str, Any]:
    pi = math.pi
    require(near(disk_intersection(2, 3, 5), 0), "disjoint-circle case failed")
    require(near(disk_intersection(2, 3, 1), 4*pi), "contained-circle case failed")
    require(near(disk_intersection(2, 2, 0), 4*pi), "concentric-circle case failed")
    partial = 50*math.acos(.6)-24
    require(near(disk_intersection(5, 5, 6), partial), "known partial-circle case failed")
    require(near(disk_intersection(2, 2, 4), 0), "external tangency failed")
    require(near(disk_intersection(5, 3, 2), 9*pi), "internal tangency failed")
    ann = annulus_area(40, 10)
    require(near(hole_only_area(40, 10, 8, 0), ann), "concentric area case failed")
    require(near(hole_only_area(40, 10, 8, 1), ann), "contained-hole edge case failed")
    require(near(hole_only_area(40, 10, 8, 9), ann-16*pi), "disjoint-hole edge case failed")
    area = annulus_area(24, 10)
    known = area-(25*pi-partial)
    require(near(hole_only_area(24, 10, 10, 6), known), "partial washer/bore case failed")

    body = cq.Workplane("XY").box(40, 40, 10).val()
    point, inward = cq.Vector(0, 0, -5), cq.Vector(0, 0, 1)
    bore = cq.Solid.makeCylinder(3.75, 10, point, inward)
    bored = body.cut(bore)
    od, ident, e = 18.0, 8.0, .724
    expected = hole_only_area(od, ident, 7.5, e)
    measured = measurement(checker, bored, "fixture", point+cq.Vector(e, 0, 0), inward, od, ident)
    require(max(abs(row["supported_area_mm2"]-expected) for row in measured) < AREA_TOLERANCE_MM2,
            "production STEP measurement disagrees with formula fixture")
    sweep_seat = {"point": point, "inward": inward, "bore_radius_mm": 3.75}
    supported = inward_envelope(bored, sweep_seat, 11, .1)
    require(supported["support_fraction"] >= 1-TOL, "known inward swept annulus failed")
    require(outward_envelope(bored, sweep_seat, 11, .1)["overlap_fraction"] <= TOL,
            "known outward clearance failed")
    adjacent = cq.Solid.makeCylinder(.75, 10, cq.Vector(8, 0, -5), inward)
    require(inward_envelope(bored.cut(adjacent), sweep_seat, 11, .1)["support_fraction"] < 1-TOL,
            "neighbor-bore envelope case escaped")
    boss = cq.Workplane("XY").box(2, 2, 1).translate((8, 0, -5.5)).val()
    require(outward_envelope(bored.fuse(boss), sweep_seat, 11, .1)["overlap_fraction"] > TOL,
            "outward boss case escaped")
    enforce_geometry_gate(True, True, [0.0, AREA_TOLERANCE_MM2])
    for containment, clearance, errors in (
        (False, True, [0.0]),
        (True, False, [0.0]),
        (True, True, [2 * AREA_TOLERANCE_MM2]),
        (True, True, [math.nan]),
        (True, True, []),
    ):
        try:
            enforce_geometry_gate(containment, clearance, errors)
        except ValueError:
            continue
        raise AssertionError("failed geometry/oracle fixture escaped the check gate")
    return {"circle_edge_and_known_overlap_cases_pass": True,
            "production_brep_measurement_matches_formula": True,
            "production_swept_envelopes_detect_neighbor_bore_and_outward_boss": True,
            "geometry_gate_rejects_failed_envelopes_and_area_oracles": True}


def build_report() -> dict[str, Any]:
    checker = prior_checker()
    prior = checker.build_report()  # Reuses all prior pins, seat checks, and STEP validation.
    require(prior["candidate"] == "compact-floor-flush-wood-joints-development"
            and prior["candidate_revision"] == "led-clearance-2x6-runner-seated-blocks-v1"
            and prior["joint_accepted"] is False and prior["six_case_envelope_established"] is False
            and prior["native_solve_run"] is False, "prior packet identity/claim boundary changed")
    screen, model, bundle, hardware, input_hashes = checker.checked_inputs()
    fastener_text = (ROOT/FASTENERS).read_text(encoding="utf-8")
    require(digest(ROOT/FASTENERS) == SHA["fasteners"], "pinned fastener source changed")
    seats, shapes = load_seats(checker, model, screen, bundle)
    cases = scenarios(hardware, fastener_text)

    # Maximum OD/offset swept annulus covers every declared washer position in every direction.
    all_dims = [{"od_mm": checker.source_number((ROOT/checker.WOOD_FRAME_SOURCE).read_text(), "WASHER_OD_MM"),
                 "id_mm": checker.source_number((ROOT/checker.WOOD_FRAME_SOURCE).read_text(), "WASHER_ID_MM")}]
    all_dims.extend(cases)
    max_od = max(row["od_mm"] for row in all_dims)
    max_id = max(row["id_mm"] for row in all_dims)
    max_offset = (BORE_D_MM-BOLT_D_MM)/2 + (max_id-BOLT_D_MM)/2
    sweep_radius = max_od/2 + max_offset
    envelope_rows = []
    for seat in seats:
        body = shapes[seat["member"]]
        inward = [inward_envelope(body, seat, sweep_radius, d) for d in DEPTHS_MM]
        outward = [outward_envelope(body, seat, sweep_radius, d) for d in DEPTHS_MM]
        envelope_rows.append({"axis_id": seat["axis_id"], "seat_role": seat["role"],
                              "member": seat["member"], "inward": inward, "outward": outward})
    global_containment = all(min(row["support_fraction"] for row in seat["inward"]) >= 1-TOL
                             for seat in envelope_rows)
    global_outward_clearance = all(max(row["overlap_fraction"] for row in seat["outward"]) <= TOL
                                   for seat in envelope_rows)

    cad_source = (ROOT/checker.WOOD_FRAME_SOURCE).read_text(encoding="utf-8")
    cad_od = checker.source_number(cad_source, "WASHER_OD_MM")
    cad_id = checker.source_number(cad_source, "WASHER_ID_MM")
    dimension_cases = [{"name": "CAD modeled annulus; not catalog hardware", "od_mm": cad_od,
                        "id_mm": cad_id, "source_relationship": "CAD baseline"}, *cases]
    # Direct STEP checks: CAD and catalog plain-washer maximum OD with each ID extreme.
    sample_keys = {(round(cad_od, 8), round(cad_id, 8))}
    sample_keys.update((round(max(row["od_mm"] for row in cases if row["od_source"].endswith("25NWUS plain Type A Wide")), 8),
                        round(row["id_mm"], 8)) for row in cases if row["id_in"] in (0.307, 0.327))
    seen: set[tuple[float, float]] = set()
    sample_cache: dict[tuple[float, float], list[list[dict[str, float]]]] = {}
    scenario_rows = []
    for case in dimension_cases:
        od, ident = float(case["od_mm"]), float(case["id_mm"])
        key = (round(od, 8), round(ident, 8))
        direct = key in sample_keys
        run_sample = direct and key not in seen
        if run_sample:
            seen.add(key)
        mode_rows = []
        for mode in offset_modes(ident, BORE_D_MM):
            expected_area = hole_only_area(od, ident, BORE_D_MM, mode["offset_mm"])
            ann_area = annulus_area(od, ident)
            result = {"name": mode["name"], "bolt_axis_offset_mm": mode["bolt_axis_offset_mm"],
                      "washer_center_offset_mm": mode["offset_mm"],
                      "analytic_supported_area_mm2": expected_area,
                      "analytic_support_fraction": expected_area/ann_area,
                      "analytic_unsupported_area_mm2": ann_area-expected_area,
                      "direct_step_sampled": direct}
            if run_sample:
                fractions = [[] for _ in DEPTHS_MM]
                areas = [[] for _ in DEPTHS_MM]
                for seat in seats:
                    u, v = tangent_basis(seat["axis"])
                    for angle in ANGLES_DEG:
                        theta = math.radians(angle)
                        direction = u*math.cos(theta)+v*math.sin(theta)
                        sample = measurement(checker, shapes[seat["member"]], seat["member"],
                                             seat["point"]+direction*mode["offset_mm"],
                                             seat["inward"], od, ident)
                        for i, item in enumerate(sample):
                            fractions[i].append(item["support_fraction"])
                            areas[i].append(item["supported_area_mm2"])
                result["step_sample_by_depth"] = [
                    {"depth_mm": depth, "support_fraction_min": min(fractions[i]),
                     "support_fraction_max": max(fractions[i]), "supported_area_min_mm2": min(areas[i]),
                     "supported_area_max_mm2": max(areas[i]),
                     "max_area_difference_from_formula_mm2": max(abs(x-expected_area) for x in areas[i])}
                    for i, depth in enumerate(DEPTHS_MM)
                ]
            elif direct:
                result["step_sample_by_depth"] = sample_cache[key][len(mode_rows)]
            mode_rows.append(result)
        if run_sample:
            sample_cache[key] = [row["step_sample_by_depth"] for row in mode_rows]
        scenario_rows.append({"scenario": case["name"],
                              "source_relationship": case.get("source_relationship", "CAD baseline"),
                              "washer_od_mm": od, "washer_id_mm": ident,
                              "annulus_area_mm2": annulus_area(od, ident),
                              "direct_step_samples_cover_all_12_seats": direct,
                              "offset_modes": mode_rows})

    area_errors = [sample["max_area_difference_from_formula_mm2"]
                   for case in scenario_rows for mode in case["offset_modes"]
                   for sample in mode.get("step_sample_by_depth", [])]
    enforce_geometry_gate(global_containment, global_outward_clearance, area_errors)

    return {
        "status": "CONDITIONAL_WASHER_GEOMETRY_ONLY",
        "candidate": prior["candidate"], "revision": prior["candidate_revision"],
        "kernel": {"CadQuery": cq.__version__, "OCP": OCP.__version__},
        "prior_checker_sha256": digest(ROOT/CHECKER), "prior_readme_sha256": digest(ROOT/BASE_README),
        "verified_input_sha256": input_hashes,
        "seat_count": len(seats), "bolt_count": 6,
        "declared_dimensions": {"conditional_nominal_smooth_body_mm": BOLT_D_MM,
                                "modeled_wood_bore_mm": BORE_D_MM,
                                "radial_body_to_bore_play_mm": (BORE_D_MM-BOLT_D_MM)/2,
                                "catalog_ID_range_mm": [x*INCH_MM for x in hardware["dimension_inputs"]["washer"]["id_in"]],
                                "catalog_OD_sources_in": {
                                    source: sorted({row["od_in"] for row in cases if row["od_source"] == source})
                                    for source in sorted({row["od_source"] for row in cases})
                                },
                                "bolt_body_limit": "6.35 mm is a recorded nominal smooth-body scenario, not a minimum delivered shank; no bolt tilt, seat drift, or fabrication tolerance is included."},
        "offset_definitions": {"washer_play_mm": "(washer_ID - conditional body diameter)/2",
                               "bolt_bore_play_mm": "(modeled bore diameter - conditional body diameter)/2",
                               "combined_case": "same-direction sum of those two circular clearances; geometric scenario only, not installed-position/equilibrium prediction"},
        "area_formula": {"disk_intersection": "0 if d >= r1+r2; pi*min(r1,r2)^2 if d <= abs(r1-r2); otherwise r1^2*acos((d^2+r1^2-r2^2)/(2*d*r1)) + r2^2*acos((d^2+r2^2-r1^2)/(2*d*r2)) - 0.5*sqrt((-d+r1+r2)(d+r1-r2)(d-r1+r2)(d+r1+r2))",
                         "unsupported_hole_area": "I(wood_bore, washer_OD/2, offset) - I(wood_bore, washer_ID/2, offset)",
                         "supported_area": "pi*(OD^2-ID^2)/4 - unsupported_hole_area"},
        "swept_step_envelope": {"tested_radial_region_mm": [BORE_D_MM/2, sweep_radius],
                                 "depths_mm": list(DEPTHS_MM),
                                 "all_direction_hole_only_support_proven_within_BREP_tolerance": global_containment,
                                 "outward_clearance_to_0_1mm_proven": global_outward_clearance,
                                 "per_seat": [{"axis_id": row["axis_id"], "role": row["seat_role"],
                                               "member": row["member"],
                                               "min_swept_support_fraction": min(x["support_fraction"] for x in row["inward"]),
                                               "max_unsupported_volume_mm3": max(x["unsupported_volume_mm3"] for x in row["inward"]),
                                               "outward_overlap_fraction_by_depth": [x["overlap_fraction"] for x in row["outward"]]}
                                              for row in envelope_rows]},
        "direction_samples_deg": list(ANGLES_DEG), "direction_samples_are_global_bound": False,
        "check_gate": {"swept_fraction_tolerance": TOL,
                       "direct_area_absolute_tolerance_mm2": AREA_TOLERANCE_MM2,
                       "failed_geometry_or_oracle_exits_nonzero": True},
        "depths_mm": list(DEPTHS_MM), "scenarios": scenario_rows,
        "claim_limits": {"geometry_only": True, "selected_or_delivered_hardware": False,
                         "actual_wood_or_hardware_inspected": False, "contact_pressure_or_resistance_established": False,
                         "joint_accepted": False, "six_case_envelope_established": False,
                         "native_solve_run": False, "physical_work_authorized": False},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--self-test", action="store_true")
    actions.add_argument("--check", action="store_true")
    args = parser.parse_args()
    checker = prior_checker()
    result = self_test(checker) if args.self_test else build_report()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
