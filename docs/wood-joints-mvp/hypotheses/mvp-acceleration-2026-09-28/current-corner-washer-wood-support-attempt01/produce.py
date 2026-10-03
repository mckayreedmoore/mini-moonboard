#!/usr/bin/env python3
"""Source-check outer washer annulus support on the six left-corner bolts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cadquery as cq


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PINS = HERE / "source-pins.json"
OUTPUT = HERE / "support-screen.json"

REL = {
    "seat_screen": Path(
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
        "/current-corner-washer-seat-screen-attempt01/seat-screen.json"
    ),
    "axial_register": Path(
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
        "/current-corner-three-case-axial-seat-register-attempt01/axial-seat-register.json"
    ),
    "manifest": Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
        "/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json"
    ),
    "bundle": Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
        "/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
    ),
    "centroids": Path(
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
        "/current-mass-centroids-attempt01/mass-centroids.json"
    ),
    "member_geometry": Path(
        "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
        "/reduced-static-attempt01/member-geometry.json"
    ),
}

EXPECTED_GROUP = {
    "knee_outer_left_post_1": "BG001",
    "knee_outer_left_post_2": "BG001",
    "knee_outer_left_side_1": "BG003",
    "knee_outer_left_side_2": "BG003",
    "knee_outer_left_inner_header_1": "BG045",
    "knee_outer_left_inner_header_2": "BG045",
}
TARGET_MEMBERS = {
    "base_post_outer_left",
    "knee_outer_left_spine",
    "knee_outer_left_inner_frame_block",
    "base_header",
}

# K.L. Jack 25NWUS Type A Wide catalog dimensional-envelope inputs, converted
# exactly from the source-backed inch endpoints in fasteners.md.
WASHER_ID_BOUNDS_MM = (7.7978, 8.3058)
WASHER_OD_BOUNDS_MM = (18.4658, 19.0246)
WASHER_T_MM = (1.2954, 2.0320)  # 0.051–0.080 in; not used as wood area.
WOOD_BORE_RADIUS_MM = 3.75

PLANE_TOL_MM = 1.0e-6
NORMAL_DOT_TOL = 1.0e-9
CENTER_TOL_MM = 1.0e-5
AREA_TOL_MM2 = 1.0e-6
TIE_TOL_N = 1.0e-9


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def dot(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def norm(v: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(dot(v, v))


def unit(v: list[float] | tuple[float, ...]) -> tuple[float, float, float]:
    length = norm(v)
    require(length > 0.0, "zero-length vector")
    return tuple(float(x) / length for x in v)


def sub(a: list[float] | tuple[float, ...], b: list[float] | tuple[float, ...]) -> tuple[float, float, float]:
    return tuple(float(x) - float(y) for x, y in zip(a, b, strict=True))


def scale(v: list[float] | tuple[float, ...], factor: float) -> tuple[float, float, float]:
    return tuple(float(x) * factor for x in v)


def annulus_area_mm2(inner_d_mm: float, outer_d_mm: float) -> float:
    return math.pi / 4.0 * (outer_d_mm**2 - inner_d_mm**2)


def lower_upper_area_bounds() -> tuple[float, float]:
    # The least annulus area uses minimum OD and maximum ID; the greatest uses
    # maximum OD and minimum ID. This is a dimensional-envelope scenario.
    return (
        annulus_area_mm2(WASHER_ID_BOUNDS_MM[1], WASHER_OD_BOUNDS_MM[0]),
        annulus_area_mm2(WASHER_ID_BOUNDS_MM[0], WASHER_OD_BOUNDS_MM[1]),
    )


def round_f(value: float, digits: int = 12) -> float:
    result = round(float(value), digits)
    return 0.0 if result == 0.0 else result


def clean(value: Any) -> Any:
    if isinstance(value, float):
        return round_f(value)
    if isinstance(value, tuple):
        return [clean(item) for item in value]
    if isinstance(value, list):
        return [clean(item) for item in value]
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return value


def support_face_for_seat(shape: cq.Shape, point: tuple[float, float, float], expected_normal: tuple[float, float, float]) -> tuple[int, cq.Face, float, float]:
    """Bind the unique planar trimmed face at a seat plane and its normal."""
    candidates: list[tuple[int, cq.Face, float, float]] = []
    coplanar: list[tuple[int, cq.Face, tuple[float, float, float], float]] = []
    for index, face in enumerate(shape.Faces(), start=1):
        if face.geomType() != "PLANE":
            continue
        normal = unit(face.normalAt().toTuple())
        center = face.Center().toTuple()
        plane_offset = dot(sub(point, center), normal)
        if abs(plane_offset) <= PLANE_TOL_MM:
            alignment = dot(normal, expected_normal)
            coplanar.append((index, face, normal, plane_offset))
            if alignment >= 1.0 - NORMAL_DOT_TOL:
                candidates.append((index, face, plane_offset, alignment))
    require(len(candidates) == 1,
            f"seat plane must have exactly one trimmed support face: {len(candidates)}")
    index, face, plane_offset, alignment = candidates[0]
    require(len(coplanar) == 1,
            f"seat plane must be represented by exactly one coplanar planar face: {len(coplanar)}")
    return index, face, plane_offset, alignment


def planar_annulus(point: tuple[float, float, float], normal: tuple[float, float, float], inner_d: float, outer_d: float) -> cq.Face:
    normal_vec = cq.Vector(*normal)
    # Choose a stable global seed not parallel to the surface normal.
    seed = cq.Vector(0.0, 0.0, 1.0)
    if abs(dot(seed.toTuple(), normal)) > 0.9:
        seed = cq.Vector(0.0, 1.0, 0.0)
    x_dir = seed.cross(normal_vec).normalized()
    plane = cq.Plane(origin=cq.Vector(*point), xDir=x_dir, normal=normal_vec)
    outer = cq.Workplane(plane).circle(outer_d / 2.0).val()
    inner = cq.Workplane(plane).circle(inner_d / 2.0).val()
    return cq.Face.makeFromWires(outer, [inner])


def build() -> dict[str, Any]:
    pins_record = read_json(PINS)
    require(pins_record.get("schema") == "current_corner_washer_wood_support_source_pins/v1",
            "source pin schema")
    observed: dict[str, str] = {}
    for pin in pins_record["files"]:
        path = ROOT / pin["path"]
        require(path.is_file(), f"pinned source missing: {pin['path']}")
        actual = sha256(path)
        require(actual == pin["sha256"], f"pinned source hash mismatch: {pin['path']}")
        observed[pin["path"]] = actual

    seat = read_json(ROOT / REL["seat_screen"])
    register = read_json(ROOT / REL["axial_register"])
    manifest = read_json(ROOT / REL["manifest"])
    bundle = read_json(ROOT / REL["bundle"])
    centroids = read_json(ROOT / REL["centroids"])
    member_geometry = read_json(ROOT / REL["member_geometry"])

    require(seat["geometry_revision_id"] == member_geometry["geometry_revision_id"],
            "seat screen/member geometry revision mismatch")
    require(seat["geometry_revision_id"] == manifest["geometry_revision_id"],
            "seat screen/full-frame manifest revision mismatch")
    require(register["status"] == "PASS_AUTHENTICATED_AXIAL_TIE_AND_OUTER_SEAT_DEMAND_COVERAGE_ONLY",
            "three-case register status/scope mismatch")
    require(register["scope"]["joint_or_product_accepted"] is False,
            "source register acceptance boundary changed")
    require(len(register["states"]) == 21 and
            {row["case_id"] for row in register["states"]} == {"a12-rear", "a1-rear", "k12-rear"},
            "register does not contain the three accepted seven-increment cases")
    for case_id in ("a12-rear", "a1-rear", "k12-rear"):
        require(
            {row["increment_ordinal"] for row in register["states"] if row["case_id"] == case_id}
            == set(range(1, 8)),
            f"register increment inventory mismatch: {case_id}",
        )
    require(member_geometry["inputs"]["manifest"]["sha256"] == sha256(ROOT / REL["manifest"]),
            "reduced member-geometry manifest hash mismatch")
    require(bundle["geometry_revision_id"] == manifest["geometry_revision_id"],
            "STEP bundle/manifest geometry revision mismatch")
    require(bundle["artifact_sha256"] == manifest["existing_step_export_evidence"]["artifact_sha256"],
            "STEP bundle artifact digest disagrees with current manifest")

    seat_axes = {row["axis_id"]: row for row in seat["axes"]}
    require(set(seat_axes) == set(EXPECTED_GROUP), "exact six primary-corner washer axes")
    geometry_members = {row["member_id"]: row for row in member_geometry["members"]}
    manifest_members = {row["member_id"]: row for row in manifest["finished_member_step_bindings"]}
    bundle_members = {row["member_id"]: row for row in bundle["members"]}
    centroid_rows = {row["name"]: row for row in centroids["rows"]}
    require(TARGET_MEMBERS.issubset(geometry_members), "all outer washer seat receiver rows exist")
    require(TARGET_MEMBERS.issubset(manifest_members), "all outer washer seat STEP bindings exist")
    require(TARGET_MEMBERS.issubset(bundle_members), "all outer washer seat bundle rows exist")

    shapes: dict[str, cq.Shape] = {}
    for member_id in sorted(TARGET_MEMBERS):
        geometry = geometry_members[member_id]
        binding = manifest_members[member_id]
        bundle_row = bundle_members[member_id]
        step_path = ROOT / binding["path"]
        step_sha = sha256(step_path)
        require(geometry["step_path"] == binding["path"], f"member geometry/manifest STEP path mismatch: {member_id}")
        require(geometry["step_sha256"] == binding["file_sha256"] == step_sha,
                f"member geometry/manifest/STEP hash mismatch: {member_id}")
        require(member_geometry["inputs"]["member_step_file_sha256"].get(binding["path"]) == step_sha,
                f"reduced geometry STEP pin mismatch: {member_id}")
        require(bundle_row["step_sha256"] == step_sha, f"bundle/manifest STEP hash mismatch: {member_id}")
        require(bundle_row["bounds_and_volume_match_current_manifest"] is True,
                f"finished STEP bounds/volume source check missing: {member_id}")
        require(binding["one_solid_valid_roundtrip"] is True and binding["source_bounds_and_volume_match"] is True,
                f"finished STEP roundtrip status missing: {member_id}")
        imported = cq.importers.importStep(str(step_path)).val()
        require(imported.isValid() and len(imported.Solids()) == 1,
                f"finished STEP is not one valid solid: {member_id}")
        shapes[member_id] = imported

    # Seat rows are bound from the reviewed reduced-property screen, then tied
    # to exact full-frame STEP member IDs and same-state register seats.
    seats: dict[tuple[str, str], dict[str, Any]] = {}
    for axis_id, axis_row in seat_axes.items():
        require(axis_id in EXPECTED_GROUP, f"unexpected axis {axis_id}")
        require(axis_row["one_physical_outer_seat_tie"] is True,
                f"physical outer-seat tie basis absent: {axis_id}")
        axis = unit(axis_row["modeled_axis_head_to_nut_global_xyz"])
        for source_seat in axis_row["outer_seats"]:
            role = source_seat["seat_role"]
            require(role in {"head_washer_seat", "nut_washer_seat"},
                    f"unexpected outer seat role: {axis_id}/{role}")
            member_id = source_seat["outer_receiver_member_id"]
            require(member_id in TARGET_MEMBERS, f"seat receiver missing target STEP: {axis_id}/{member_id}")
            centroid_role = "head" if role == "head_washer_seat" else "nut"
            centroid = centroid_rows[f"{axis_id}/{centroid_role}_washer"]
            washer_center = tuple(float(x) for x in centroid["mass_center_global_xyz_mm"])
            point = tuple(float(x) for x in source_seat["seat_point_xyz_mm"])
            delta = sub(point, washer_center)
            axial_delta = dot(delta, axis)
            tangent = sub(delta, scale(axis, axial_delta))
            thickness = float(axis_row["modeled_washer_thickness_mm"])
            expected_delta = thickness / 2.0 if centroid_role == "head" else -thickness / 2.0
            gap = axial_delta - expected_delta
            expected_outward = unit(scale(axis, -1.0 if centroid_role == "head" else 1.0))
            require(abs(norm(tangent)) <= CENTER_TOL_MM,
                    f"CAD washer centroid is not coaxial with seat: {axis_id}/{role}")
            require(abs(gap) <= CENTER_TOL_MM,
                    f"wood plane does not coincide with modeled CAD washer contact plane: {axis_id}/{role}")
            require(abs(thickness - 1.651) <= 1e-6,
                    f"CAD washer thickness differs from reviewed seat screen: {axis_id}/{role}")
            require(source_seat["modeled_finished_wood_bore_radius_mm"] == WOOD_BORE_RADIUS_MM,
                    f"modeled wood bore radius changed: {axis_id}/{role}")
            face_index, face, plane_offset, normal_alignment = support_face_for_seat(
                shapes[member_id], point, expected_outward
            )
            face_normal = unit(face.normalAt().toTuple())
            angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, normal_alignment))))
            require(abs(plane_offset) <= PLANE_TOL_MM,
                    f"finished wood face plane differs from source seat station: {axis_id}/{role}")
            require(angle_deg <= 0.001, f"wood seat plane is not aligned to CAD washer plane: {axis_id}/{role}")

            area_low, area_high = lower_upper_area_bounds()
            intersection_rows = []
            for label, inner_d, outer_d, expected_area in (
                ("minimum_area_dimensional_envelope", WASHER_ID_BOUNDS_MM[1], WASHER_OD_BOUNDS_MM[0], area_low),
                ("maximum_area_dimensional_envelope", WASHER_ID_BOUNDS_MM[0], WASHER_OD_BOUNDS_MM[1], area_high),
            ):
                ring = planar_annulus(point, face_normal, inner_d, outer_d)
                common = face.intersect(ring)
                unsupported = ring.cut(face)
                ring_area = float(ring.Area())
                supported_area = float(common.Area())
                unsupported_area = float(unsupported.Area())
                require(abs(ring_area - expected_area) <= AREA_TOL_MM2,
                        f"OCC annulus area disagrees with exact circle arithmetic: {axis_id}/{role}/{label}")
                require(abs(ring_area - supported_area) <= AREA_TOL_MM2 and unsupported_area <= AREA_TOL_MM2,
                        f"catalog annulus is clipped by finished wood support: {axis_id}/{role}/{label}")
                require(len(common.Faces()) == 1,
                        f"supported annulus is not one connected planar region: {axis_id}/{role}/{label}")
                intersection_rows.append(
                    {
                        "dimensional_case": label,
                        "washer_inner_diameter_mm": inner_d,
                        "washer_outer_diameter_mm": outer_d,
                        "full_annulus_area_mm2": ring_area,
                        "wood_face_intersection_area_mm2": supported_area,
                        "unsupported_annulus_area_mm2": unsupported_area,
                        "supported_fraction": supported_area / ring_area,
                        "supported_planar_region_count": len(common.Faces()),
                    }
                )

            bore_clearance = WASHER_ID_BOUNDS_MM[0] / 2.0 - WOOD_BORE_RADIUS_MM
            require(bore_clearance > 0.0, f"minimum washer opening does not clear modeled bore: {axis_id}/{role}")
            identity = (axis_id, role)
            require(identity not in seats, f"duplicate seat identity {identity}")
            face_box = face.BoundingBox()
            seats[identity] = {
                "axis_id": axis_id,
                "group_id": EXPECTED_GROUP[axis_id],
                "seat_role": role,
                "receiver_member_id": member_id,
                "receiver_member_kind": geometry_members[member_id].get("member_kind"),
                "receiver_step_path": manifest_members[member_id]["path"],
                "receiver_step_sha256": manifest_members[member_id]["file_sha256"],
                "seat_center_global_xyz_mm": point,
                "modeled_bolt_axis_head_to_nut_global": axis,
                "expected_outward_wood_normal_global": expected_outward,
                "finished_wood_support_face": {
                    "one_based_step_face_index": face_index,
                    "surface_type": face.geomType(),
                    "face_area_mm2": float(face.Area()),
                    "wire_count": len(face.Wires()),
                    "edge_count": len(face.Edges()),
                    "bounds_xyz_mm": [face_box.xmin, face_box.xmax, face_box.ymin, face_box.ymax, face_box.zmin, face_box.zmax],
                    "plane_offset_at_seat_mm": plane_offset,
                    "outward_normal_global": face_normal,
                    "normal_tilt_from_modeled_washer_plane_deg": angle_deg,
                    "annular_support_geometry_method": "exact OCC planar trimmed-face common and annulus-minus-face cut; complete CAD face topology includes its modeled openings/cuts",
                },
                "modeled_cad_washer_pose": {
                    "mass_centroid_global_xyz_mm": washer_center,
                    "modeled_thickness_mm": thickness,
                    "seat_point_minus_centroid_along_head_to_nut_axis_mm": axial_delta,
                    "expected_contact_plane_offset_from_centroid_mm": expected_delta,
                    "wood_to_ideal_modeled_contact_plane_gap_mm": gap,
                    "tangential_centroid_to_seat_offset_mm": norm(tangent),
                },
                "modeled_wood_bore_radius_mm": WOOD_BORE_RADIUS_MM,
                "minimum_25nwus_opening_to_modeled_bore_radial_clearance_mm": bore_clearance,
                "catalog_annulus_support_cases": intersection_rows,
                "full_dimensional_envelope_annulus_supported_in_cad": True,
            }

    require(len(seats) == 12, f"expected 12 unique outer washer seats, found {len(seats)}")

    tie_states: list[dict[str, Any]] = []
    tied_axis_counts: dict[str, int] = {axis_id: 0 for axis_id in EXPECTED_GROUP}
    for state in register["states"]:
        require(state.get("source_response_audit_gates", {}).get("raw_balance_passed") is True,
                "accepted tie state lacks source raw-balance gate")
        for tie in state["ties"]:
            axis_id = tie["axis_id"]
            require(axis_id in EXPECTED_GROUP, f"unexpected tie axis in register: {axis_id}")
            require(tie["group_id"] == EXPECTED_GROUP[axis_id], f"tie group mismatch: {axis_id}")
            action = float(tie["signed_tie_action_n"])
            require(action > TIE_TOL_N, f"three-case source tie is not positive tension: {axis_id}")
            require(tie["signed_tie_state"] == "tension", f"source tie sign class changed: {axis_id}")
            axis_vec = unit(tie["head_to_nut_unit_global_xyz"])
            require(norm(sub(axis_vec, seats[(axis_id, "head_washer_seat")]["modeled_bolt_axis_head_to_nut_global"])) <= CENTER_TOL_MM,
                    f"signed register/seat geometry bolt axis mismatch: {axis_id}")
            source_by_role = {seat["seat_role"]: seat for seat in tie["seats"]}
            require(set(source_by_role) == {"head_washer_seat", "nut_washer_seat"},
                    f"tie does not have two outer seats: {axis_id}")
            per_seat = []
            area_min, area_max = lower_upper_area_bounds()
            for role in ("head_washer_seat", "nut_washer_seat"):
                source_seat = source_by_role[role]
                geometry_seat = seats[(axis_id, role)]
                require(source_seat["physical_member"] == geometry_seat["receiver_member_id"],
                        f"source tie/finished STEP receiver mismatch: {axis_id}/{role}")
                require(norm(sub(source_seat["seat_point_global_xyz_mm"], geometry_seat["seat_center_global_xyz_mm"])) <= CENTER_TOL_MM,
                        f"source tie/finished STEP seat center mismatch: {axis_id}/{role}")
                require(abs(float(source_seat["signed_tie_action_n"]) - action) <= TIE_TOL_N,
                        f"same-state outer-seat tie scalar mismatch: {axis_id}/{role}")
                low_p = action / area_max
                high_p = action / area_min
                per_seat.append(
                    {
                        "seat_role": role,
                        "receiver_member_id": geometry_seat["receiver_member_id"],
                        "conditional_uniform_average_wood_pressure_mpa_range": [low_p, high_p],
                        "pressure_area_basis": "25NWUS catalog dimensional-envelope annulus fully intersected by finished CAD wood face; actual washer/product and physical contact are unverified",
                    }
                )
            tie_states.append(
                {
                    "source_register_state": {
                        "case_id": state["case_id"],
                        "increment_ordinal": state["increment_ordinal"],
                        "load_factor": state["load_factor"],
                        "source_demand_report_path": state["source_demand_report_path"],
                        "source_demand_report_sha256": state["source_demand_report_sha256"],
                    },
                    "axis_id": axis_id,
                    "group_id": tie["group_id"],
                    "signed_tie_action_n": action,
                    "signed_tie_state": tie["signed_tie_state"],
                    "outer_seat_pressure_rows": per_seat,
                }
            )
            tied_axis_counts[axis_id] += 1
    require(len(tie_states) == 126, f"expected 126 same-state physical ties, found {len(tie_states)}")
    require(all(count == 21 for count in tied_axis_counts.values()), "each of six bolts must have 21 same-state actions")

    all_pressure = [
        p
        for tie in tie_states
        for seat in tie["outer_seat_pressure_rows"]
        for p in seat["conditional_uniform_average_wood_pressure_mpa_range"]
    ]
    area_low, area_high = lower_upper_area_bounds()
    min_action = min(tie["signed_tie_action_n"] for tie in tie_states)
    max_action = max(tie["signed_tie_action_n"] for tie in tie_states)
    max_tie = max(tie_states, key=lambda item: item["signed_tie_action_n"])
    min_tie = min(tie_states, key=lambda item: item["signed_tie_action_n"])
    observed = {pin["path"]: pin["sha256"] for pin in pins_record["files"]}
    observed[str(PINS.relative_to(ROOT))] = sha256(PINS)
    observed[str(Path(__file__).resolve().relative_to(ROOT))] = sha256(Path(__file__).resolve())

    result = {
        "schema": "current_corner_washer_wood_support_screen/v1",
        "status": "PASS_SOURCE_BOUND_CAD_WOOD_ANNULUS_SUPPORT_GEOMETRY_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": seat["geometry_revision_id"],
        "runtime": {"cadquery_version": cq.__version__, "units": "mm, mm^2, N, MPa"},
        "source_pins_sha256": sha256(PINS),
        "source_sha256_observed": dict(sorted(observed.items())),
        "scope": {
            "axis_ids": sorted(EXPECTED_GROUP),
            "outer_wood_seat_count": len(seats),
            "same_state_signed_tie_count": len(tie_states),
            "same_state_outer_seat_tension_rows": len(tie_states) * 2,
            "wood_member_cut_topology_used": True,
            "washer_to_wood_annulus_only": True,
            "head_or_nut_to_washer_metal_footprint_analyzed": False,
            "physical_wood_or_delivered_hardware_inspection": False,
            "native_or_mesh_work": False,
            "geometry_modified": False,
        },
        "catalog_washer_dimensional_scenario": {
            "source_product_lead": "K.L. Jack 25NWUS, Type A Wide, 1/4 in, plain/light oil",
            "source_status": "catalog geometry envelope only; not selected, purchased, received, or fit-qualified",
            "id_bounds_mm": list(WASHER_ID_BOUNDS_MM),
            "od_bounds_mm": list(WASHER_OD_BOUNDS_MM),
            "thickness_bounds_mm": list(WASHER_T_MM),
            "minimum_annulus_area_mm2": area_low,
            "maximum_annulus_area_mm2": area_high,
            "area_bound_combinations": {
                "minimum": "minimum OD with maximum ID",
                "maximum": "maximum OD with minimum ID",
            },
            "modeled_cad_wood_bore_diameter_mm": 2.0 * WOOD_BORE_RADIUS_MM,
            "minimum_opening_to_bore_radial_clearance_mm": WASHER_ID_BOUNDS_MM[0] / 2.0 - WOOD_BORE_RADIUS_MM,
        },
        "method": {
            "geometry_binding": "attempt04 finished-member STEP bindings cross-checked to reduced member geometry, current full-frame STEP bundle, and the original attempt04 manifest",
            "profile_method_precedent": "attempt01 current-knee-finished-profile finite trimmed-face query and CadQuery/OCC source-bound STEP loading; direct planar-face query extended to the four exact receiver solids at all 12 washer stations",
            "seat_plane_lookup": "unique source-point-coplanar planar BRep face with outward normal toward modeled washer centroid",
            "support_operation": "exact OCC common of each coplanar trimmed wood face with both catalog annulus dimensional extremes, plus annulus-minus-face cut area",
            "area_tolerance_mm2": AREA_TOL_MM2,
            "plane_tolerance_mm": PLANE_TOL_MM,
            "important_interpretation": "modeled flat, coaxial catalog-annulus scenario on the finished STEP plane; not received washer profile, physical flatness, actual wood contact, local pressure, or resistance",
        },
        "summary": {
            "seat_count_with_unique_plane_and_full_support": len(seats),
            "seat_count_with_coincident_modeled_wood_and_washer_planes": sum(
                abs(row["modeled_cad_washer_pose"]["wood_to_ideal_modeled_contact_plane_gap_mm"]) <= CENTER_TOL_MM
                and row["finished_wood_support_face"]["normal_tilt_from_modeled_washer_plane_deg"] <= 0.001
                for row in seats.values()
            ),
            "min_annulus_intersection_fraction": min(
                bound["supported_fraction"]
                for row in seats.values()
                for bound in row["catalog_annulus_support_cases"]
            ),
            "max_unsupported_annulus_area_mm2": max(
                bound["unsupported_annulus_area_mm2"]
                for row in seats.values()
                for bound in row["catalog_annulus_support_cases"]
            ),
            "max_abs_cad_plane_gap_mm": max(
                abs(row["modeled_cad_washer_pose"]["wood_to_ideal_modeled_contact_plane_gap_mm"])
                for row in seats.values()
            ),
            "max_wood_plane_tilt_deg": max(
                row["finished_wood_support_face"]["normal_tilt_from_modeled_washer_plane_deg"]
                for row in seats.values()
            ),
            "minimum_positive_tie_across_three_cases_n": min_action,
            "minimum_tie_source_state": {
                "case_id": min_tie["source_register_state"]["case_id"],
                "increment_ordinal": min_tie["source_register_state"]["increment_ordinal"],
                "axis_id": min_tie["axis_id"],
            },
            "maximum_positive_tie_across_three_cases_n": max_action,
            "maximum_tie_source_state": {
                "case_id": max_tie["source_register_state"]["case_id"],
                "increment_ordinal": max_tie["source_register_state"]["increment_ordinal"],
                "axis_id": max_tie["axis_id"],
            },
            "conditional_uniform_average_pressure_range_mpa_across_126_ties_and_both_seats": [min(all_pressure), max(all_pressure)],
            "pressure_bound_basis": "each of the 126 registered same-state positive tension scalars is applied separately at each of its two outer seats and divided by the 25NWUS catalog annular area envelope, after exact CAD wood-face support was verified",
        },
        "seats": [seats[key] for key in sorted(seats)],
        "same_state_tie_pressures": tie_states,
        "limits": [
            "The 25NWUS dimensions are a conditional catalog envelope applied as a geometric scenario to all twelve seats; BG003 has no 25NWUS washer lead in the existing axis register.",
            "This checks only the washer annulus against the finished CAD wood support face; it does not analyze head-to-washer or nut-to-washer metal footprints.",
            "Coincident modeled planes and zero modeled gap/tilt do not verify physical wood flatness, cut quality, washer flatness, delivered-part conformance, assembly seating, or actual contact area.",
            "T/A is a conditional uniform average over the catalog annulus, not a local contact-pressure solution. No wood bearing resistance, adjustment factor, washer steel resistance, or joint capacity is calculated.",
            "The tie data cover only 126 same-state rows from A12-rear, A1-rear, and K12-rear, not the six-case envelope or final joint acceptance.",
        ],
    }
    return clean(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    payload = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.write:
        OUTPUT.write_text(payload, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        return
    actual = OUTPUT.read_text(encoding="utf-8")
    if actual != payload:
        raise SystemExit("support-screen.json differs from source-bound reconstruction")
    result = json.loads(actual)
    summary = result["summary"]
    print(
        "verified 12 CAD wood seats; full support and modeled plane coincidence; "
        f"126 ties, pressure {summary['conditional_uniform_average_pressure_range_mpa_across_126_ties_and_both_seats'][0]:.9f}–"
        f"{summary['conditional_uniform_average_pressure_range_mpa_across_126_ties_and_both_seats'][1]:.9f} MPa"
    )


if __name__ == "__main__":
    main()
