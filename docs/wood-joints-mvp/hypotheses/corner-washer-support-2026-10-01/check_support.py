#!/usr/bin/env python3
"""Check source-BREP support of the six primary-corner outer washer seats."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import cadquery as cq
import OCP

from mini_moonboard.wood_joint_geometry import (
    BoltHardware,
    WasherSeat,
    washer_support_report,
)

SEAT_SCREEN = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    "/current-corner-washer-seat-screen-attempt01/seat-screen.json"
)
MODEL_INPUTS = Path(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
    "/reduced-static-attempt01/model-inputs.json"
)
MEMBER_BUNDLE = Path(
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
    "/current-full-frame-member-solids-attempt01/bundle"
    "/current-full-frame-member-solids.json"
)
FASTENER_INPUTS = Path(
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
    "/fastener-inputs.json"
)
WOOD_FRAME_SOURCE = Path("mini_moonboard/wood_joint_frame.py")

SOURCE_PINS: dict[str, tuple[Path, str]] = {
    "hardware specification": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
        )
        / "fasteners.md",
        "aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6",
    ),
    "hardware requirements": (
        Path(
            "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
        )
        / "requirements.json",
        "15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100",
    ),
    "washer support implementation": (
        Path("mini_moonboard/wood_joint_geometry.py"),
        "e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e",
    ),
    "CAD washer dimensions": (
        Path("mini_moonboard/wood_joint_frame.py"),
        "77b4a8b28b02088878f1f0e0483610a7918cb85f5694f0551f50cf8888886545",
    ),
}

EXPECTED_SEAT_SCREEN_SHA256 = (
    "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0"
)
EXPECTED_MODEL_INPUTS_SHA256 = (
    "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9"
)
EXPECTED_BUNDLE_SHA256 = (
    "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420"
)
EXPECTED_FASTENER_INPUTS_SHA256 = (
    "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2"
)

EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
AXIS_GROUPS = {
    "BG001": (
        "knee_outer_left_post_1",
        "knee_outer_left_post_2",
    ),
    "BG003": (
        "knee_outer_left_side_1",
        "knee_outer_left_side_2",
    ),
    "BG045": (
        "knee_outer_left_inner_header_1",
        "knee_outer_left_inner_header_2",
    ),
}
DEPTHS_MM = (0.01, 0.05, 0.1)
PLANE_TOLERANCE_MM = 1e-5
NORMAL_TOLERANCE = 1e-8
SUPPORT_TOLERANCE = 1e-8
INCH_MM = 25.4


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(relative: Path) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {relative}")
    return value


def verify_hash(relative: Path, expected: str, label: str) -> str:
    path = ROOT / relative
    require(path.is_file(), f"missing pinned input: {relative}")
    actual = sha256(path)
    require(actual == expected, f"{label} SHA-256 changed: {relative}")
    return actual


def source_number(source: str, variable: str) -> float:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == variable
            for target in node.targets
        ):
            return float(ast.literal_eval(node.value))
    raise ValueError(f"missing literal {variable} in pinned CAD source")


def hardware_for(od_mm: float, id_mm: float) -> BoltHardware:
    return BoltHardware(
        candidate_sku="geometry-only-annulus",
        under_head_length_mm=300.0,
        steel_diameter_mm=6.35,
        cad_occupied_diameter_mm=6.35,
        drill_diameter_mm=6.35,
        head_diameter_mm=12.827,
        head_height_mm=4.1656,
        washer_od_mm=od_mm,
        washer_id_mm=id_mm,
        washer_thickness_mm=1.651,
        nut_diameter_mm=12.827,
        nut_height_mm=5.7404,
        usable_thread_start_mm=1.0,
        usable_thread_end_mm=300.0,
    )


def matching_seat_planes(
    body: cq.Shape, point: cq.Vector, inward: cq.Vector
) -> list[dict[str, float | int]]:
    planes = []
    for index, face in enumerate(body.Faces()):
        if face.geomType() != "PLANE":
            continue
        plane = face._geomAdaptor().Pln()
        location = cq.Vector(*plane.Location().Coord())
        normal = cq.Vector(*plane.Axis().Direction().Coord()).normalized()
        offset = abs((point - location).dot(normal))
        alignment = abs(normal.dot(inward))
        if offset <= PLANE_TOLERANCE_MM and alignment >= 1.0 - NORMAL_TOLERANCE:
            planes.append(
                {
                    "face_index": index,
                    "plane_offset_mm": offset,
                    "normal_alignment": alignment,
                    "area_mm2": face.Area(),
                }
            )
    require(planes, "washer datum has no matching planar wood boundary face")
    return planes


def seat_support(
    body: cq.Shape,
    body_id: str,
    point_xyz: list[float] | tuple[float, float, float],
    axis_xyz: list[float] | tuple[float, float, float],
    role: str,
    od_mm: float,
    id_mm: float,
) -> dict[str, Any]:
    point = cq.Vector(*point_xyz)
    axis = cq.Vector(*axis_xyz).normalized()
    if role == "head_washer_seat":
        inward = axis
    elif role == "nut_washer_seat":
        inward = -axis
    else:
        raise ValueError(f"unknown washer seat role: {role}")
    planes = matching_seat_planes(body, point, inward)
    seat = WasherSeat(body_id, point, inward)
    hardware = hardware_for(od_mm, id_mm)
    inward_reports = [
        washer_support_report(seat, body, hardware, probe_depth_mm=depth)
        for depth in DEPTHS_MM
    ]
    outward_seat = WasherSeat(body_id, point, -inward)
    outward_reports = [
        washer_support_report(outward_seat, body, hardware, probe_depth_mm=depth)
        for depth in DEPTHS_MM
    ]
    fractions = [float(report.support_fraction) for report in inward_reports]
    outward_fractions = [float(report.support_fraction) for report in outward_reports]
    all_fractions = fractions + outward_fractions
    require(
        all(
            math.isfinite(value)
            and -SUPPORT_TOLERANCE <= value <= 1.0 + SUPPORT_TOLERANCE
            for value in all_fractions
        ),
        f"nonfinite or out-of-range support fraction at {body_id}",
    )
    require(
        min(fractions) >= 1.0 - SUPPORT_TOLERANCE,
        f"annulus is clipped by a bore or wood edge at {body_id}",
    )
    require(
        max(outward_fractions) <= SUPPORT_TOLERANCE,
        f"washer datum is embedded or outward normal is wrong at {body_id}",
    )
    area = math.pi * (od_mm**2 - id_mm**2) / 4.0
    return {
        "matching_planar_face_count": len(planes),
        "maximum_plane_offset_mm": max(float(row["plane_offset_mm"]) for row in planes),
        "minimum_normal_alignment": min(
            float(row["normal_alignment"]) for row in planes
        ),
        "inward_support_fraction_by_depth": {
            f"{depth:g}": fraction
            for depth, fraction in zip(DEPTHS_MM, fractions, strict=True)
        },
        "outward_support_fraction_by_depth": {
            f"{depth:g}": fraction
            for depth, fraction in zip(DEPTHS_MM, outward_fractions, strict=True)
        },
        "minimum_inward_support_fraction": min(fractions),
        "maximum_inward_support_fraction": max(fractions),
        "maximum_outward_support_fraction": max(outward_fractions),
        "annulus_area_mm2": area,
        "unsupported_area_max_mm2": max(
            float(report.unsupported_area_mm2) for report in inward_reports
        ),
    }


def checked_inputs() -> tuple[
    dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]
]:
    verified_hashes = {}
    for label, (relative, expected) in SOURCE_PINS.items():
        verified_hashes[label] = {
            "path": relative.as_posix(),
            "sha256": verify_hash(relative, expected, label),
        }
    frozen_inputs = (
        ("washer seat screen", SEAT_SCREEN, EXPECTED_SEAT_SCREEN_SHA256),
        ("reduced model inputs", MODEL_INPUTS, EXPECTED_MODEL_INPUTS_SHA256),
        ("finished member BREP manifest", MEMBER_BUNDLE, EXPECTED_BUNDLE_SHA256),
        ("local hardware raw inputs", FASTENER_INPUTS, EXPECTED_FASTENER_INPUTS_SHA256),
    )
    for label, path, expected in frozen_inputs:
        verified_hashes[label] = {
            "path": path.as_posix(),
            "sha256": verify_hash(path, expected, label),
        }
    return (
        read_json(SEAT_SCREEN),
        read_json(MODEL_INPUTS),
        read_json(MEMBER_BUNDLE),
        read_json(FASTENER_INPUTS),
        verified_hashes,
    )


def build_report() -> dict[str, Any]:
    screen, model, bundle, hardware_inputs, verified_hashes = checked_inputs()
    require(
        all(
            value.get("candidate") == EXPECTED_CANDIDATE
            for value in (screen, model, bundle)
        ),
        "source candidate identity changed",
    )
    require(
        model.get("revision_id") == EXPECTED_REVISION, "reduced model revision changed"
    )
    require(
        screen.get("geometry_revision_id") == EXPECTED_REVISION,
        "seat screen revision changed",
    )
    require(
        bundle.get("geometry_revision_id") == EXPECTED_REVISION,
        "member BREP revision changed",
    )
    require(
        screen.get("status") == "bounded_conditional_modeled_seat_geometry_only"
        and screen.get("mechanical_acceptance") is False
        and screen.get("native_solve_run") is False,
        "unexpected washer screen claim status",
    )

    inch = float(INCH_MM)
    washer_source = hardware_inputs["dimension_inputs"]["washer"]
    id_min_mm, id_max_mm = (float(value) * inch for value in washer_source["id_in"])
    od_min_mm, od_max_mm = (float(value) * inch for value in washer_source["od_in"])
    require(
        0 < id_min_mm <= id_max_mm < od_min_mm <= od_max_mm,
        "invalid catalog annulus bounds",
    )

    frame_text = (ROOT / WOOD_FRAME_SOURCE).read_text(encoding="utf-8")
    cad_od_mm = source_number(frame_text, "WASHER_OD_MM")
    cad_id_mm = source_number(frame_text, "WASHER_ID_MM")
    cad_area_mm2 = math.pi * (cad_od_mm**2 - cad_id_mm**2) / 4.0

    member_rows = {row["member_id"]: row for row in model["members"]}
    candidate_connections = [
        row for row in model["connections"] if row.get("kind") == "candidate_bolt"
    ]
    require(len(candidate_connections) == 92, "reviewed candidate-bolt count changed")
    connection_rows = {row["axis_id"]: row for row in candidate_connections}
    bundle_rows = {row["member_id"]: row for row in bundle["members"]}
    screen_axes = {row["axis_id"]: row for row in screen["axes"]}
    expected_axes = [axis for group in AXIS_GROUPS.values() for axis in group]
    require(
        set(screen_axes) == set(expected_axes), "washer screen axis coverage changed"
    )
    require(
        len(connection_rows) == len(candidate_connections),
        "candidate axis IDs are not unique",
    )

    shapes: dict[str, cq.Shape] = {}
    shape_summaries: dict[str, dict[str, Any]] = {}
    seat_results = []
    for group, axes in AXIS_GROUPS.items():
        for axis_id in axes:
            connection = connection_rows.get(axis_id)
            require(connection is not None, f"missing current connection: {axis_id}")
            geometry = connection["source_record"]["geometry"]
            axis = cq.Vector(*geometry["axis_head_to_nut_global"]).normalized()
            center = cq.Vector(*geometry["shaft_center_global_xyz_mm"])
            underhead = center - axis * (
                float(geometry["modeled_underhead_to_tip_mm"]) / 2.0
            )
            receivers = sorted(
                geometry["wood_receiver_intervals"],
                key=lambda row: row[
                    "current_shaft_intersection_solid_intervals_from_underhead_mm"
                ][0][0],
            )
            require(len(receivers) in (2, 3), f"unexpected receiver count: {axis_id}")
            require(
                all(
                    len(
                        row[
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ]
                    )
                    == 1
                    for row in (receivers[0], receivers[-1])
                ),
                f"ambiguous outer receiver interval: {axis_id}",
            )
            screen_axis = screen_axes[axis_id]
            require(
                abs(
                    float(screen_axis["modeled_outer_washer_annular_area_mm2"])
                    - cad_area_mm2
                )
                <= 1e-6,
                f"modeled CAD annulus area does not match source constants: {axis_id}",
            )
            require(
                abs(float(screen_axis["modeled_washer_thickness_mm"]) - 1.651) <= 1e-6,
                f"modeled washer thickness changed: {axis_id}",
            )
            expected_seats = (
                (
                    "head_washer_seat",
                    receivers[0],
                    float(
                        receivers[0][
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ][0][0]
                    ),
                ),
                (
                    "nut_washer_seat",
                    receivers[-1],
                    float(
                        receivers[-1][
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ][0][1]
                    ),
                ),
            )
            actual_seats = {row["seat_role"]: row for row in screen_axis["outer_seats"]}
            require(
                set(actual_seats) == {row[0] for row in expected_seats},
                f"seat roles changed: {axis_id}",
            )
            if group == "BG003":
                receiver_ids = [row["receiver_id"] for row in receivers]
                require(
                    len(receivers) == 3
                    and receiver_ids
                    == [
                        "knee_outer_left_spine",
                        "base_side_left",
                        "knee_outer_left_inner_frame_block",
                    ]
                    and screen_axis.get("no_middle_member_axial_washer_seat") is True,
                    f"BG003 continuous receiver/seat scope changed: {axis_id}",
                )

            for role, receiver, station in expected_seats:
                seat_record = actual_seats[role]
                body_id = receiver["receiver_id"]
                require(
                    seat_record["outer_receiver_member_id"] == body_id,
                    f"seat owner mismatch: {axis_id}/{role}",
                )
                point = underhead + axis * station
                point_xyz = tuple(
                    float(value) for value in seat_record["seat_point_xyz_mm"]
                )
                require(
                    (point - cq.Vector(*point_xyz)).Length <= PLANE_TOLERANCE_MM,
                    f"seat coordinate mismatch: {axis_id}/{role}",
                )
                member = member_rows[body_id]
                grain = tuple(
                    float(value)
                    for value in member["reduced_geometry_descriptor"][
                        "grain_global_xyz"
                    ]
                )
                require(
                    all(
                        abs(float(a) - float(b)) <= 1e-10
                        for a, b in zip(
                            seat_record["proposed_grain_global_xyz"], grain, strict=True
                        )
                    ),
                    f"grain owner mismatch: {axis_id}/{role}",
                )
                connection_bores = [
                    row
                    for row in connection["receiver_clearance_geometry"]
                    if row.get("receiver_id") == body_id
                ]
                require(
                    len(connection_bores) == 1,
                    f"ambiguous seat bore record: {axis_id}/{body_id}",
                )
                bore = float(connection_bores[0]["unique_bore_radius_mm"])
                require(
                    connection_bores[0]["result_status"]
                    == "unique_coaxial_bore_radius",
                    "seat bore status changed",
                )

                if body_id not in shapes:
                    binding = member["current_finished_step_binding"]
                    bundle_row = bundle_rows.get(body_id)
                    require(
                        bundle_row is not None,
                        f"member BREP absent from bundle manifest: {body_id}",
                    )
                    step_path = Path(binding["path"])
                    require(
                        binding.get("step_roundtrip_checked") is True,
                        f"STEP roundtrip not checked: {body_id}",
                    )
                    require(
                        bundle_row.get("step_file")
                        == step_path.relative_to(MEMBER_BUNDLE.parents[1]).as_posix()
                        and bundle_row.get("step_sha256") == binding.get("file_sha256"),
                        f"member BREP binding differs from source bundle: {body_id}",
                    )
                    step_hash = verify_hash(
                        step_path, str(binding["file_sha256"]), f"member BREP {body_id}"
                    )
                    shape = cq.importers.importStep(str(ROOT / step_path)).val()
                    solids = shape.Solids()
                    require(
                        len(solids) == 1 and solids[0].isValid(),
                        f"member BREP not one valid solid: {body_id}",
                    )
                    type_counts = Counter(face.geomType() for face in solids[0].Faces())
                    expected_summary = bundle_row["step_roundtrip_summary"]
                    require(
                        expected_summary.get("valid") is True
                        and expected_summary.get("solid_count") == 1
                        and len(solids[0].Faces()) == expected_summary["face_count"]
                        and type_counts["CYLINDER"] > 0
                        and type_counts["PLANE"] > 0
                        and abs(solids[0].Volume() - expected_summary["volume_mm3"])
                        < 0.001,
                        f"member BREP surface inventory is incomplete: {body_id}",
                    )
                    shapes[body_id] = solids[0]
                    shape_summaries[body_id] = {
                        "step_sha256": binding["file_sha256"],
                        "verified_step_sha256": step_hash,
                        "face_count": len(solids[0].Faces()),
                        "cylindrical_face_count": type_counts["CYLINDER"],
                        "plane_face_count": type_counts["PLANE"],
                        "bundle_roundtrip_valid": expected_summary["valid"],
                        "bundle_solid_count": expected_summary["solid_count"],
                    }
                body = shapes[body_id]
                cases = (
                    ("CAD modeled", cad_od_mm, cad_id_mm),
                    ("catalog minimum-area", od_min_mm, id_max_mm),
                    ("catalog maximum-envelope", od_max_mm, id_min_mm),
                )
                for scenario, od_mm, id_mm in cases:
                    require(
                        id_mm / 2.0 > bore,
                        f"washer opening does not clear modeled bore: {axis_id}/{scenario}",
                    )
                    result = seat_support(
                        body,
                        body_id,
                        point_xyz,
                        tuple(float(value) for value in axis.toTuple()),
                        role,
                        od_mm,
                        id_mm,
                    )
                    seat_results.append(
                        {
                            "group": group,
                            "axis_id": axis_id,
                            "seat_role": role,
                            "wood_member": body_id,
                            "member_kind": member["member_kind"],
                            "grain_global_xyz": list(grain),
                            "grain_relation": seat_record["load_grain_relation"],
                            "modeled_bore_radius_mm": bore,
                            "washer_scenario": scenario,
                            "washer_od_mm": od_mm,
                            "washer_id_mm": id_mm,
                            **result,
                        }
                    )

    require(len(seat_results) == 36, "expected 12 seats x 3 annulus scenarios")
    scenarios = ("CAD modeled", "catalog minimum-area", "catalog maximum-envelope")
    scenario_summary = {
        scenario: {
            "annulus_area_mm2": next(
                row["annulus_area_mm2"]
                for row in seat_results
                if row["washer_scenario"] == scenario
            ),
            "inward_support_fraction_min": min(
                row["minimum_inward_support_fraction"]
                for row in seat_results
                if row["washer_scenario"] == scenario
            ),
            "inward_support_fraction_max": max(
                row["maximum_inward_support_fraction"]
                for row in seat_results
                if row["washer_scenario"] == scenario
            ),
            "outward_overlap_fraction_max": max(
                row["maximum_outward_support_fraction"]
                for row in seat_results
                if row["washer_scenario"] == scenario
            ),
            "maximum_unsupported_area_mm2": max(
                row["unsupported_area_max_mm2"]
                for row in seat_results
                if row["washer_scenario"] == scenario
            ),
        }
        for scenario in scenarios
    }
    axis_ownership: dict[str, dict[str, dict[str, Any]]] = {}
    for row in seat_results:
        if row["washer_scenario"] == "CAD modeled":
            axis_ownership.setdefault(row["axis_id"], {})[row["seat_role"]] = {
                "wood_member": row["wood_member"],
                "grain_global_xyz": row["grain_global_xyz"],
                "grain_relation": row["grain_relation"],
            }
    ownership_patterns: dict[tuple[Any, ...], list[str]] = {}
    for axis_id, seats in axis_ownership.items():
        signature = tuple(
            (
                seats[role]["wood_member"],
                tuple(seats[role]["grain_global_xyz"]),
                seats[role]["grain_relation"],
            )
            for role in ("head_washer_seat", "nut_washer_seat")
        )
        ownership_patterns.setdefault(signature, []).append(axis_id)
    ownership_summary = [
        {
            "axis_ids": sorted(axis_ids),
            "head": {
                "wood_member": signature[0][0],
                "grain_global_xyz": list(signature[0][1]),
                "grain_relation": signature[0][2],
            },
            "nut": {
                "wood_member": signature[1][0],
                "grain_global_xyz": list(signature[1][1]),
                "grain_relation": signature[1][2],
            },
        }
        for signature, axis_ids in sorted(ownership_patterns.items())
    ]
    minimum = min(
        row["inward_support_fraction_min"] for row in scenario_summary.values()
    )
    maximum = max(
        row["inward_support_fraction_max"] for row in scenario_summary.values()
    )
    max_outward = max(
        row["outward_overlap_fraction_max"] for row in scenario_summary.values()
    )
    maximum_plane_offset = max(row["maximum_plane_offset_mm"] for row in seat_results)
    minimum_normal_alignment = min(
        row["minimum_normal_alignment"] for row in seat_results
    )
    return {
        "status": "PASS_SOURCE_BREP_WASHER_ANNULUS_GEOMETRY_ONLY",
        "candidate": EXPECTED_CANDIDATE,
        "candidate_revision": EXPECTED_REVISION,
        "geometry_kernel": {"cadquery": cq.__version__, "ocp": OCP.__version__},
        "verified_input_sha256": verified_hashes,
        "seat_count": 12,
        "physical_bolt_count": 6,
        "annulus_scenarios_per_seat": 3,
        "support_checks": len(seat_results),
        "inward_and_outward_probes_per_scenario": len(DEPTHS_MM),
        "probe_depths_mm": list(DEPTHS_MM),
        "inward_support_fraction_min": minimum,
        "inward_support_fraction_max": maximum,
        "outward_overlap_fraction_max": max_outward,
        "seat_plane_max_offset_mm": maximum_plane_offset,
        "seat_plane_minimum_normal_alignment": minimum_normal_alignment,
        "maximum_unsupported_area_mm2": max(
            row["maximum_unsupported_area_mm2"] for row in scenario_summary.values()
        ),
        "cad_annulus_mm": {"od": cad_od_mm, "id": cad_id_mm, "area": cad_area_mm2},
        "catalog_annulus_extremes_mm": {
            "minimum_area": {
                "od": od_min_mm,
                "id": id_max_mm,
                "area": math.pi * (od_min_mm**2 - id_max_mm**2) / 4.0,
            },
            "maximum_envelope": {
                "od": od_max_mm,
                "id": id_min_mm,
                "area": math.pi * (od_max_mm**2 - id_min_mm**2) / 4.0,
            },
        },
        "scenario_summary": scenario_summary,
        "seat_ownership_and_grain": ownership_summary,
        "source_member_breps": shape_summaries,
        "joint_accepted": False,
        "six_case_envelope_established": False,
        "native_solve_run": False,
        "physical_flatness_or_contact_proven": False,
    }


def self_test() -> dict[str, Any]:
    hardware = hardware_for(18.6436, 8.0)
    stock = cq.Workplane("XY").box(40.0, 40.0, 10.0).val()
    seat_point = (0.0, 0.0, -5.0)
    inward = (0.0, 0.0, 1.0)
    full = seat_support(
        stock,
        "fixture",
        seat_point,
        inward,
        "head_washer_seat",
        hardware.washer_od_mm,
        hardware.washer_id_mm,
    )
    require(
        full["minimum_inward_support_fraction"] == 1.0
        and full["maximum_outward_support_fraction"] == 0.0,
        "known full-support boundary fixture failed",
    )
    matching_seat_planes(stock, cq.Vector(*seat_point), cq.Vector(*inward))

    bore = cq.Solid.makeCylinder(2.4, 10.0, cq.Vector(6.5, 0, -5), cq.Vector(0, 0, 1))
    bored = stock.cut(bore)
    boss = cq.Workplane("XY").box(4.0, 20.0, 2.0).translate((6.0, 0.0, -6.0)).val()
    raised = stock.fuse(boss)
    inward_with_boss = washer_support_report(
        WasherSeat("fixture", seat_point, cq.Vector(*inward)),
        raised,
        hardware,
        probe_depth_mm=0.05,
    )
    outward_with_boss = washer_support_report(
        WasherSeat("fixture", seat_point, cq.Vector(*inward) * -1.0),
        raised,
        hardware,
        probe_depth_mm=0.05,
    )
    require(
        inward_with_boss.support_fraction >= 1.0 - SUPPORT_TOLERANCE
        and outward_with_boss.support_fraction > 0.0,
        "raised boundary obstruction fixture lacks its known inward/outward result",
    )
    edge_seat = (13.0, 0.0, -5.0)
    embedded = (0.0, 0.0, -4.0)
    rejected_inputs = (
        (bored, seat_point, inward, "head_washer_seat", "neighboring bore"),
        (
            raised,
            seat_point,
            inward,
            "head_washer_seat",
            "outward boundary obstruction",
        ),
        (stock, edge_seat, inward, "head_washer_seat", "wood edge"),
        (stock, embedded, inward, "head_washer_seat", "embedded datum"),
        (stock, seat_point, inward, "nut_washer_seat", "wrong inward normal"),
        (stock, seat_point, inward, "unknown_role", "unknown role"),
    )
    for body, point, axis, role, label in rejected_inputs:
        try:
            seat_support(
                body,
                "fixture",
                point,
                axis,
                role,
                hardware.washer_od_mm,
                hardware.washer_id_mm,
            )
        except ValueError:
            continue
        raise AssertionError(f"{label} fixture was accepted")
    try:
        seat_support(
            raised,
            "fixture",
            seat_point,
            inward,
            "head_washer_seat",
            hardware.washer_od_mm,
            hardware.washer_id_mm,
        )
    except ValueError as error:
        require(
            "embedded or outward normal is wrong" in str(error),
            "raised boundary obstruction did not exercise the outward-overlap guard",
        )
    else:
        raise AssertionError("outward boundary obstruction fixture was accepted")

    catalog_min = hardware_for(0.727 * INCH_MM, 0.327 * INCH_MM)
    catalog_max = hardware_for(0.749 * INCH_MM, 0.307 * INCH_MM)
    require(
        catalog_min.washer_od_mm < hardware.washer_od_mm < catalog_max.washer_od_mm
        and catalog_max.washer_id_mm < hardware.washer_id_mm < catalog_min.washer_id_mm,
        "CAD/catalog annulus ordering fixture failed",
    )
    return {
        "full_support_known_answer": True,
        "neighboring_bore_clipping_rejected": True,
        "outward_boundary_obstruction_rejected": True,
        "wood_edge_clipping_rejected": True,
        "embedded_datum_rejected": True,
        "wrong_inward_normal_and_role_rejected": True,
        "catalog_bounds_ordered_separately_from_cad": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--self-test", action="store_true")
    actions.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = self_test() if args.self_test else build_report()
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
