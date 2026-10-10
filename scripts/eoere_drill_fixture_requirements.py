"""Bound nominal guide reach, alignment and raw-stock clamp footprints.

This checks proposed dimensions, not actual clamp retention or drilling skill.
Finished recess/channel lands and actual tool dimensions still need observation.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from scripts.eoere_nominal_access import BASE, DOC, ROOT, SHOP
from scripts.eoere_selected_hardware import encoded, require, sha


def alignment_budget(wood, guide, bore, shaft, guide_clearance, entry_error):
    radial = (bore - shaft) / 2
    require(min(wood, guide, radial) > 0 and min(guide_clearance, entry_error) >= 0,
            "positive path, guide and hole clearance required")
    drift = wood * guide_clearance / guide
    return {"nominal_radial_fit_budget_mm": radial,
            "proposed_entry_alignment_error_mm": entry_error,
            "guide_diametral_clearance_mm": guide_clearance,
            "guide_play_angle_deg": math.degrees(math.atan(guide_clearance / guide)),
            "worst_nominal_guide_play_drift_mm": drift,
            "remaining_nominal_radial_budget_mm": radial - entry_error - drift}


def raw_contains(point, profile):
    vertices = profile["vertices_luv_mm"]
    for i in (1, 2):
        if not min(v[i] for v in vertices) - 1e-5 <= point[i] <= max(v[i] for v in vertices) + 1e-5:
            return False
    for plane in profile["end_planes"]:
        normal = [float(plane["outward_normal_" + axis + "_unitless"]) for axis in "luv"]
        if sum(a * b for a, b in zip(point, normal, strict=True)) > float(plane["plane_offset_from_datum_mm"]) + 1e-5:
            return False
    return True


def receiver_support(profile, axis, row, body):
    """Probe the finished entry face and choose two separate supported pads."""
    import cadquery as cq

    entry = [float(row["entry_in_receiver_" + name + "_mm"]) for name in "luv"]
    local_direction = [sum(a * b for a, b in zip(axis["direction_xyz"], basis, strict=True))
                       for basis in profile["basis_grain_u_v_xyz"]]
    face_axis = max(range(3), key=lambda i: abs(local_direction[i]))
    square_to_face = face_axis != 0 and abs(abs(local_direction[face_axis]) - 1) < 1e-6
    spans = [i for i in range(3) if i != face_axis]

    def footprint(center, half):
        return all(raw_contains([center[i] + (s * half if i == spans[0] else t * half if i == spans[1] else 0)
                                 for i in range(3)], profile)
                   for s in (-1, 1) for t in (-1, 1))

    pads = [[entry[0] + sign * 50.8, *entry[1:]] for sign in (-1, 1)]
    direction = cq.Vector(*axis["direction_xyz"])
    origin = cq.Vector(*axis["point_xyz_mm"]) + direction * float(row["entry_from_axis_point_mm"])
    plane = cq.Plane(origin=origin, xDir=profile["basis_grain_u_v_xyz"][0], normal=direction)
    guide_ring = cq.Workplane(plane).rect(38.1, 38.1).circle(axis["bore_diameter_mm"] / 2).extrude(.2).val()
    guide_missing = guide_ring.cut(body).Volume()
    candidate_pads = []
    for a in (-76.2, -50.8, -38.1, 0, 38.1, 50.8, 76.2):
        for b in (-50.8, -38.1, 0, 38.1, 50.8):
            if math.hypot(max(abs(a) - 12.7, 0), max(abs(b) - 12.7, 0)) < 25.4 - 1e-8:
                continue
            local_center = list(entry)
            local_center[spans[0]] += a
            local_center[spans[1]] += b
            if not footprint(local_center, 12.7):
                continue
            world = cq.Vector(*profile["datum_xyz_mm"])
            for coordinate, basis in zip(local_center, profile["basis_grain_u_v_xyz"], strict=True):
                world += cq.Vector(*basis) * coordinate
            pad_plane = cq.Plane(origin=world, xDir=plane.xDir, normal=direction)
            pad = cq.Workplane(pad_plane).rect(25.4, 25.4).extrude(.2).val()
            if pad.cut(body).Volume() < 1e-4:
                candidate_pads.append((a, b))
    pair = next(([a, b] for i, a in enumerate(candidate_pads) for b in candidate_pads[i + 1:]
                 if max(abs(a[0] - b[0]), abs(a[1] - b[1])) >= 25.4 - 1e-8), None)
    return {"axis_id": axis["id"], "receiver": row["receiver"],
        "normal_to_nominal_stock_face": square_to_face, "entry_luv_mm": entry,
        "38p1_mm_square_guide_inside_raw_face": square_to_face and footprint(entry, 19.05),
        "25p4_mm_square_pads_at_plus_minus50p8_grain_inside_raw_face":
            [square_to_face and footprint(pad, 12.7) for pad in pads],
        "guide_ring_missing_nominal_wood_mm3_at_0p2_depth": guide_missing,
        "guide_ring_fully_supported_nominally": guide_missing < 1e-4,
        "two_nominal_finished_pad_candidates": pair,
        "pad_offsets_basis_local_indices": spans,
        "actual_land_and_clamp_retention_verified": False, "Actual": "", "Disposition": ""}


def build(out):
    require(out.resolve().is_relative_to(ROOT / BASE / "selected-hardware-v1") and not out.exists(),
            "fresh ignored fixture output required")
    paths = [DOC / "occupied-kicker-clearance-v1.json", SHOP / "drilling-requirements.csv",
             SHOP / "current_profiles.json", SHOP.parent / "receiver-holes.csv", Path(__file__).relative_to(ROOT),
             SHOP / "README.md", Path("scripts/eoere_selected_hardware.py"),
             Path("scripts/eoere_nominal_access.py")]
    pins = {str(p): sha(p) for p in paths}
    geometry = json.loads(paths[0].read_bytes())
    profiles = json.loads(paths[2].read_bytes())
    axes = {r["id"]: r for r in geometry["axes"]}
    guide, backer, clearance = 19.05, 6.35, .02
    requirements = []
    for axis in axes.values():
        bit = 10.31875 if axis["diameter_mm"] == 9.525 else 13.49375
        budget = (bit - axis["diameter_mm"]) / 4
        requirements.append({"axis_id": axis["id"], "wood_path_mm": axis["grip_mm"],
            "specified_nominal_bit_diameter_mm": bit,
            "modeled_bore_envelope_mm": axis["bore_diameter_mm"],
            "guide_depth_mm": guide, "backer_mm": backer,
            "minimum_usable_bit_projection_mm": axis["grip_mm"] + guide + backer,
            "minimum_clamp_opening_without_extra_pads_mm": axis["grip_mm"] + guide + backer,
            **alignment_budget(axis["grip_mm"], guide, bit, axis["diameter_mm"], clearance, budget),
            "Actual_bit_projection_mm": "", "Actual_clamp_opening_and_pad_pose": "",
            "Actual_guide_clearance_and_runout": "", "Actual": "", "Disposition": ""})
    footprints = []
    import cadquery as cq

    solid_cache = {}
    coupon = cq.Workplane("XY").box(2, 2, 2).val()
    require(abs(coupon.intersect(coupon.translate((1, 0, 0))).Volume() - 4) < 1e-8,
            "finished-land overlap known answer")
    for row in csv.DictReader(paths[3].open()):
        profile, axis = profiles[row["receiver"]], axes[row["axis_id"]]
        record = profile["finished"]
        if row["receiver"] not in solid_cache:
            require(sha(record["path"]) == record["sha256"], "finished receiver source differs")
            pins[record["path"]] = record["sha256"]
            solid_cache[row["receiver"]] = cq.Shape.importBrep(record["path"])
        footprints.append(receiver_support(profile, axis, row, solid_cache[row["receiver"]]))
    require(len(requirements) == 100 and len(footprints) == 120, "complete axis and receiver census required")
    require(all(sha(p) == digest for p, digest in pins.items()), "fixture source drift")
    out.mkdir(parents=True)
    result = {"schema": "eoere_selected_hardware_drill_fixture_requirements/v1", "revision": geometry["revision"],
        "source_sha256": pins, "source_bytes_unchanged": True, "axis_requirements": requirements,
        "raw_face_footprints": footprints, "counts": {"axes": 100, "receivers": 120,
            "square_stock_face_axes": sum(r["normal_to_nominal_stock_face"] for r in footprints),
            "guide_inside_raw_face": sum(r["38p1_mm_square_guide_inside_raw_face"] for r in footprints),
            "both_pad_candidates_inside_raw_face": sum(all(r["25p4_mm_square_pads_at_plus_minus50p8_grain_inside_raw_face"]) for r in footprints),
            "guide_rings_fully_supported_on_nominal_finished_face": sum(r["guide_ring_fully_supported_nominally"] for r in footprints),
            "two_pads_on_nominal_finished_face": sum(r["two_nominal_finished_pad_candidates"] is not None for r in footprints)},
        "finished_land_volume_known_answers": 1,
        "maximum_minimum_usable_projection_mm": max(r["minimum_usable_bit_projection_mm"] for r in requirements),
        "minimum_candidate_radial_budget_mm": min(r["remaining_nominal_radial_budget_mm"] for r in requirements),
        "limits": ["0.02-mm guide diametral play and half the nominal radial fit budget for entry alignment are explicit proposed assumptions, not observed tolerances.",
            "Bit runout, wood movement, guide tilt/compliance and actual shaft/bore limits consume the remaining budget.",
            "Finished-face probes are 0.2 mm deep. Full nominal support does not establish actual flatness, clamp strength, drill/chuck approach or practical tool conformance.",
            "Use bridge/outboard fixtures where proposed footprints overhang; independent stops and clamps must retain both receivers and backer.",
            "No physical work, actual inspection, load capacity or fabrication/climbing release."],
        "Actual": "", "Disposition": "", "physical_release": False}
    (out / "result.json").write_bytes(encoded(result))
    print(json.dumps({k: result[k] for k in ["counts", "maximum_minimum_usable_projection_mm", "minimum_candidate_radial_budget_mm"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    build(parser.parse_args().out)
