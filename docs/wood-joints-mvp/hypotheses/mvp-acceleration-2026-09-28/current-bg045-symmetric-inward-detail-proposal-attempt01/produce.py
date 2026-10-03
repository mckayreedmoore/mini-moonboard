#!/usr/bin/env python3
"""Source-guarded conditional BG045 detailing comparison; never edits CAD."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
PINS_PATH = HERE / "source-pins.json"
OUTPUT_PATH = HERE / "proposal.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def close(a: float, b: float, tol: float = 1e-7) -> bool:
    return abs(a - b) <= tol


def assert_close(a: float, b: float, label: str, tol: float = 1e-7) -> None:
    if not close(a, b, tol):
        raise AssertionError(f"{label}: {a!r} != {b!r}")


def verify_pin_file(pin_file: Path) -> int:
    """Validate every path/hash pair recursively declared by a source pin file."""
    data = read_json(pin_file)
    found: set[tuple[str, str]] = set()

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            path = value.get("path")
            digest = value.get("sha256")
            if isinstance(path, str) and isinstance(digest, str) and len(digest) == 64:
                found.add((path, digest))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    failures = []
    for rel, expected in sorted(found):
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"missing pinned source {rel}")
        elif sha256(path) != expected:
            failures.append(f"hash mismatch for pinned source {rel}")
    if failures:
        raise AssertionError("; ".join(failures))
    return len(found)


def load_sources() -> tuple[dict[str, Any], dict[str, Any]]:
    pins = read_json(PINS_PATH)
    producer_pin = pins["producer"]
    if producer_pin["path"] != str(Path(__file__).resolve().relative_to(ROOT)):
        raise AssertionError("producer path in source pins does not match this helper")
    if sha256(Path(__file__)) != producer_pin["sha256"]:
        raise AssertionError("producer source hash does not match source pins")
    direct = pins["files"]
    for item in direct:
        path = ROOT / item["path"]
        if not path.is_file() or sha256(path) != item["sha256"]:
            raise AssertionError(f"direct source pin failed: {item['path']}")
    recursive_counts = {}
    for rel in pins["source_pin_documents"]:
        recursive_counts[rel] = verify_pin_file(ROOT / rel)

    sources = {item["role"]: read_json(ROOT / item["path"])
               for item in direct if item["path"].endswith(".json")}
    embedded_counts = {}
    for rel in pins["embedded_source_pin_maps"]:
        embedded = read_json(ROOT / rel)
        source_map = embedded["source_pins"]
        checked = 0
        for source_rel, record in source_map.items():
            path = ROOT / source_rel
            if not path.is_file() or sha256(path) != record["sha256"]:
                raise AssertionError(f"embedded source pin failed: {source_rel}")
            checked += 1
        embedded_counts[rel] = checked
    recursive_counts["embedded_source_pin_maps"] = embedded_counts
    return pins, {**sources, "recursive_pin_counts": recursive_counts}


def get_member_face(surfaces: dict[str, Any], member_id: str, feature_id: str) -> dict[str, Any]:
    rec = next(row for row in surfaces["records"] if row["member_id"] == member_id)
    return next(feature for feature in rec["features"] if feature["feature_id"] == feature_id)


def circles(feature: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for wire in feature["trim"]["wires"]:
        for edge in wire["edges"]:
            if edge.get("curve_kind") == "CIRCLE":
                out.append(edge["circle"])
    return out


def verify_rectangular_circle_face(face: dict[str, Any], expected_circle_count: int) -> dict[str, Any]:
    """Check the published trimmed-loop inventory used by the margin arithmetic."""
    wires = face["trim"]["wires"]
    if len(wires) != expected_circle_count + 1:
        raise AssertionError(f"unexpected wire count on {face['feature_id']}")
    if wires[0]["edge_count"] != 4 or any(
        edge["curve_kind"] != "LINE" for edge in wires[0]["edges"]
    ):
        raise AssertionError(f"outer loop is not the four-line rectangle: {face['feature_id']}")
    for wire in wires[1:]:
        if wire["edge_count"] != 1 or wire["edges"][0]["curve_kind"] != "CIRCLE":
            raise AssertionError(f"non-circular interior loop: {face['feature_id']}")
    if len(circles(face)) != expected_circle_count:
        raise AssertionError(f"circular loop inventory mismatch: {face['feature_id']}")
    bounds = face["trim"]["bounds_global_xyz_mm"]
    outer_vertices = {
        tuple(vertex)
        for edge in wires[0]["edges"]
        for vertex in edge["topological_vertices_global_xyz_mm"]
    }
    expected_xy_corners = {
        (bounds[0], bounds[2]), (bounds[0], bounds[3]),
        (bounds[1], bounds[2]), (bounds[1], bounds[3]),
    }
    observed_xy_corners = {(point[0], point[1]) for point in outer_vertices}
    if len(observed_xy_corners) != 4 or any(
        not any(close(x, ex) and close(y, ey) for ex, ey in expected_xy_corners)
        for x, y in observed_xy_corners
    ):
        raise AssertionError(f"outer rectangle vertices do not close to bounds: {face['feature_id']}")
    return {
        "outer_loop": "four straight edges with vertices at the registered XY bounding rectangle corners",
        "interior_loops": "single-edge circles only",
        "interior_circle_count": expected_circle_count,
        "all_face_loops_classified_for_arithmetic": True,
    }


def candidate_axis(axis_features: dict[str, Any], axis_id: str) -> dict[str, Any]:
    axes = axis_features["source_axis_groups"]["candidate_bolt_axes"]["axes"]
    return next(axis for axis in axes if axis["axis_id"] == axis_id)


def receiver_match(axis: dict[str, Any], member_id: str) -> dict[str, Any]:
    match = next(row for row in axis["receiver_memberships"]
                 if row["receiver_member_id"] == member_id)
    if match["match_status"] != "matched_bore_patch":
        raise AssertionError(f"{axis['axis_id']} is not matched in {member_id}")
    return match


def produce() -> dict[str, Any]:
    pins, loaded = load_sources()
    old = loaded["prior_axis2_only_detail_screen"]
    profile = loaded["finished_profile_edge_query"]
    washer = loaded["current_washer_support_screen"]
    axis_features = loaded["finished_axis_feature_register"]
    surfaces = loaded["finished_surface_register"]
    edge = loaded["edge_and_splitting_applicability_results"]

    axis1 = "knee_outer_left_inner_header_1"
    axis2 = "knee_outer_left_inner_header_2"
    member_header = "base_header"
    member_block = "knee_outer_left_inner_frame_block"
    both = old["geometry_scenarios"]["edge_distances_and_pitch"][
        "prior_both_face_4d_band_unapproved"]
    current = old["geometry_scenarios"]["edge_distances_and_pitch"]["current_reviewed"]
    y1_current = current["axes"][axis1]["center_xyz_mm"][1]
    y2_current = current["axes"][axis2]["center_xyz_mm"][1]
    y1_proposed = both["axes"][axis1]["center_xyz_mm"][1]
    y2_proposed = both["axes"][axis2]["center_xyz_mm"][1]
    dy1 = y1_proposed - y1_current
    dy2 = y2_proposed - y2_current

    profile_edge_rows = []
    for item in profile["profile_distance_summary"]:
        if (item["axis_id"] in (axis1, axis2)
                and item["receiver_member_id"] in (member_header, member_block)
                and item["direction"] in ("+Y", "-Y")):
            profile_edge_rows.append({
                "axis_id": item["axis_id"],
                "receiver_member_id": item["receiver_member_id"],
                "direction": item["direction"],
                "source_planar_face_indices": item["profile_face_indices_across_five_stations"],
                "sampled_finished_profile_distance_mm":
                    item["finished_profile_perpendicular_distance_range_mm"],
                "old_rectangle_distance_mm": item["old_rectangular_envelope_distance_mm"],
                "finished_minus_rectangle_range_mm": item["finished_minus_rectangle_range_mm"],
                "same_trimmed_face_at_all_five_stations": item["same_trimmed_face_at_all_five_stations"],
            })
    if len(profile_edge_rows) != 8 or any(
        any(not close(value, 0.0) for value in row["finished_minus_rectangle_range_mm"])
        for row in profile_edge_rows
    ):
        raise AssertionError("expected eight BG045 current finished-profile Y-face rows")

    # The two source-matched receivers have the same existing bore centers.
    matched = {}
    for axis_id in (axis1, axis2):
        axis = candidate_axis(axis_features, axis_id)
        matched[axis_id] = {}
        for member_id in (member_header, member_block):
            member_match = receiver_match(axis, member_id)
            matched[axis_id][member_id] = {
                "feature_ids": member_match["matched_feature_ids"],
                "binding_status": member_match["binding_status"],
                "modeled_bore_radius_mm": member_match["cylinder_surface_candidates"][0]["cylinder_radius_mm"],
            }

    expected_feature = {
        axis1: {member_header: "base_header/facet006",
                member_block: "knee_outer_left_inner_frame_block/facet010"},
        axis2: {member_header: "base_header/facet014",
                member_block: "knee_outer_left_inner_frame_block/facet009"},
    }
    for axis_id in (axis1, axis2):
        ycur = current["axes"][axis_id]["center_xyz_mm"][1]
        for member_id in (member_header, member_block):
            fid = expected_feature[axis_id][member_id]
            if matched[axis_id][member_id]["feature_ids"] != [fid]:
                raise AssertionError(f"unexpected bore mapping {axis_id} / {member_id}")
            face = get_member_face(surfaces, member_id,
                                   "base_header/facet002" if member_id == member_header
                                   else "knee_outer_left_inner_frame_block/facet003")
            matching_circles = [c for c in circles(face)
                                if close(c["center_global_xyz_mm"][0], -1085.85)
                                and close(c["center_global_xyz_mm"][1], ycur)
                                and close(c["radius_mm"], 3.75)]
            if len(matching_circles) != 1:
                raise AssertionError(f"planar bore loop mismatch {axis_id} / {member_id}")

    assert_close(dy1, -5.4, "axis1 signed shift")
    assert_close(dy2, 5.4, "axis2 signed shift")
    assert_close(y1_proposed, -67.75, "axis1 candidate coordinate")
    assert_close(y2_proposed, -150.3, "axis2 candidate coordinate")

    block_face = get_member_face(surfaces, member_block,
                                 "knee_outer_left_inner_frame_block/facet003")
    header_face = get_member_face(surfaces, member_header, "base_header/facet002")
    face_loop_inventory = {
        member_header: verify_rectangular_circle_face(header_face, 12),
        member_block: verify_rectangular_circle_face(block_face, 2),
    }
    block_bounds = block_face["trim"]["bounds_global_xyz_mm"]
    header_bounds = header_face["trim"]["bounds_global_xyz_mm"]
    block_ymin, block_ymax = block_bounds[2], block_bounds[3]
    header_ymin, header_ymax = header_bounds[2], header_bounds[3]

    def to_y_faces(y: float, ymin: float, ymax: float) -> dict[str, float]:
        return {"minus_y": y - ymin, "plus_y": ymax - y}

    block_distances = {
        axis1: to_y_faces(y1_proposed, block_ymin, block_ymax),
        axis2: to_y_faces(y2_proposed, block_ymin, block_ymax),
    }
    header_distances = {
        axis1: to_y_faces(y1_proposed, header_ymin, header_ymax),
        axis2: to_y_faces(y2_proposed, header_ymin, header_ymax),
    }
    pitch_current = abs(y2_current - y1_current)
    pitch_proposed = abs(y2_proposed - y1_proposed)
    assert_close(pitch_current, 93.35, "current y pitch")
    assert_close(pitch_proposed, 82.55, "proposed y pitch")
    for axis_id in (axis1, axis2):
        for recv in (member_header, member_block):
            assert_close(matched[axis_id][recv]["modeled_bore_radius_mm"], 3.75,
                         f"{axis_id} {recv} bore radius")

    # Current OCC washer intersections are exact at original centers. The margins
    # below are analytic translation scenarios over the registered planar loops;
    # they are not a moved-BRep/OCC query.
    id_min = washer["catalog_washer_dimensional_scenario"]["id_bounds_mm"][0]
    od_max = washer["catalog_washer_dimensional_scenario"]["od_bounds_mm"][1]
    washer_r_inner_min = id_min / 2.0
    washer_r_outer_max = od_max / 2.0
    bore_r = 3.75
    support_rows = [s for s in washer["seats"] if s["group_id"] == "BG045"]
    if len(support_rows) != 4 or not all(
        s["full_dimensional_envelope_annulus_supported_in_cad"] for s in support_rows
    ):
        raise AssertionError("current four-seat OCC washer support input changed")
    current_seat_rows = []
    for row in support_rows:
        face = row["finished_wood_support_face"]
        tilt = face["normal_tilt_from_modeled_washer_plane_deg"]
        if not close(tilt, 0.0):
            raise AssertionError("current BG045 seat face has modeled tilt")
        current_seat_rows.append({
            "axis_id": row["axis_id"],
            "receiver_member_id": row["receiver_member_id"],
            "seat_role": row["seat_role"],
            "full_dimensional_envelope_annulus_supported_in_cad":
                row["full_dimensional_envelope_annulus_supported_in_cad"],
            "supported_fraction_by_catalog_extreme": {
                case["dimensional_case"]: case["supported_fraction"]
                for case in row["catalog_annulus_support_cases"]
            },
            "unsupported_area_mm2_by_catalog_extreme": {
                case["dimensional_case"]: case["unsupported_annulus_area_mm2"]
                for case in row["catalog_annulus_support_cases"]
            },
            "modeled_face_tilt_deg": tilt,
            "method": "exact OCC planar trimmed-face common and annulus-minus-face cut on current CAD only",
        })

    washer_scenarios = []
    for axis_id, y_proposed, other_y_proposed in (
        (axis1, y1_proposed, y2_proposed),
        (axis2, y2_proposed, y1_proposed),
    ):
        for role_member, fid in ((member_header, "base_header/facet002"),
                                 (member_block, "knee_outer_left_inner_frame_block/facet003")):
            face = get_member_face(surfaces, role_member, fid)
            b = face["trim"]["bounds_global_xyz_mm"]
            center = (-1085.85, y_proposed)
            center_to_edges = {
                "x_minus": center[0] - b[0],
                "x_plus": b[1] - center[0],
                "y_minus": center[1] - b[2],
                "y_plus": b[3] - center[1],
            }
            nearest_edge_name, nearest_edge = min(center_to_edges.items(), key=lambda kv: kv[1])
            face_circles = circles(face)
            target_current_ys = (y1_current, y2_current)
            target_bores = [c for c in face_circles
                            if close(c["center_global_xyz_mm"][0], center[0])
                            and any(close(c["center_global_xyz_mm"][1], y) for y in target_current_ys)
                            and close(c["radius_mm"], bore_r)]
            if len(target_bores) != 2:
                raise AssertionError(f"expected two BG045 opening loops on {role_member}")
            other_circles = [c for c in face_circles if c not in target_bores]
            other_clearances = []
            for circle in other_circles:
                cx, cy, _ = circle["center_global_xyz_mm"]
                d = math.hypot(center[0] - cx, center[1] - cy)
                other_clearances.append({
                    "wire_center_xy_mm": [cx, cy],
                    "wire_radius_mm": circle["radius_mm"],
                    "washer_outer_to_other_wire_clearance_mm":
                        d - washer_r_outer_max - circle["radius_mm"],
                })
            nearest_other = (min(
                other_clearances,
                key=lambda r: r["washer_outer_to_other_wire_clearance_mm"],
            ) if other_clearances else None)
            washer_scenarios.append({
                "axis_id": axis_id,
                "receiver_member_id": role_member,
                "support_face_feature_id": fid,
                "proposed_center_xy_mm": list(center),
                "registered_support_face_wire_count": face["trim"]["wire_count"],
                "registered_non_target_circle_count": len(other_circles),
                "registered_face_loop_inventory": face_loop_inventory[role_member],
                "nearest_rectangular_face_edge": nearest_edge_name,
                "center_to_nearest_face_edge_mm": nearest_edge,
                "max_catalog_outer_radius_mm": washer_r_outer_max,
                "conditional_ring_to_nearest_face_edge_margin_mm":
                    nearest_edge - washer_r_outer_max,
                "minimum_catalog_inner_radius_mm": washer_r_inner_min,
                "translated_target_bore_radius_mm": bore_r,
                "conditional_opening_to_bore_radial_margin_mm":
                    washer_r_inner_min - bore_r,
                "other_shifted_target_bore_centerline_pitch_mm":
                    abs(y_proposed - other_y_proposed),
                "conditional_washer_outer_to_other_shifted_target_bore_margin_mm":
                    abs(y_proposed - other_y_proposed) - washer_r_outer_max - bore_r,
                "nearest_unmoved_registered_cut": nearest_other,
                "support_interpretation":
                    "rectangle-boundary and registered circular-loop separation arithmetic only; assumes this target bore moves with its mating bore, translates both BG045 target loops, keeps unrelated registered circles fixed, and uses catalog envelope dimensions; not a moved-BRep OCC/common or complete support proof",
            })

    # Reuse, do not re-run, the old orthogonal-bore ray screen and ten-receiver
    # screw projection. These are envelope/projection results only.
    web = old["bg003_orthogonal_bore_web"]
    web_current = web["scenario_results"]["current_reviewed"]
    web_both = web["scenario_results"]["prior_both_face_4d_band_unapproved"]
    assert_close(web_current["minimum_pairwise_modeled_envelope_web_mm"],
                 7.452644216, "current BG003 web")
    assert_close(web_both["minimum_pairwise_modeled_envelope_web_mm"],
                 2.052644216, "both-face BG003 web")
    screw_groups = axis_features["source_axis_groups"]
    if len(screw_groups["panel_kicker_screw_axes"]["axes"]) != 66:
        raise AssertionError("panel/kicker screw inventory is not 66")
    screw_projection = old["ten_base_header_hillman_receiver_projection_screen"]
    screw_screen = screw_projection["scenario_minima_by_BG045_axis"][
        "prior_both_face_4d_band_unapproved"]

    edge_disposition = edge["status"]
    if "UNRESOLVED" not in edge_disposition and "CONDITIONAL" not in edge_disposition:
        raise AssertionError(f"edge/splitting disposition changed: {edge_disposition}")

    return {
        "schema": "current_bg045_symmetric_inward_detailing_proposal/v1",
        "status": "CONDITIONAL_GEOMETRY_PROPOSAL_NOT_READY_FOR_AXIS_CHANGE",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "BG045 two-bolt 6.35 mm conditional edge-detailing proposal; source geometry and published scenario arithmetic only",
        "proposal": {
            "condition": "Only consider the symmetric inward proposal if later source-backed code interpretation establishes that the block's +Y edge for axis 1 and -Y edge for axis 2 are the relevant loaded-edge checks and the 25.4 mm comparator applies to this receiver/detail.",
            "axes": {
                axis1: {"current_y_mm": y1_current, "proposed_y_mm": y1_proposed,
                        "signed_move_y_mm": dy1},
                axis2: {"current_y_mm": y2_current, "proposed_y_mm": y2_proposed,
                        "signed_move_y_mm": dy2},
            },
            "block_y_envelope_mm": [block_ymin, block_ymax],
            "header_y_envelope_mm": [header_ymin, header_ymax],
            "conditional_block_edge_comparators_mm": block_distances,
            "header_edge_distances_mm": header_distances,
            "y_center_pitch_current_mm": pitch_current,
            "y_center_pitch_proposed_mm": pitch_proposed,
            "pitch_reduction_mm": pitch_current - pitch_proposed,
            "conditional_4d_mm": 25.4,
            "arithmetic_only": True,
            "current_finished_profile_y_face_comparison": profile_edge_rows,
            "same_pitch_block_width_growth_sensitivity": {
                "current_block_width_mm": block_ymax - block_ymin,
                "current_y_pitch_preserved_mm": pitch_current,
                "unchanged_axis_y_mm": {axis1: y1_current, axis2: y2_current},
                "growth_each_y_face_mm": 5.4,
                "hypothetical_block_y_envelope_mm": [block_ymin - 5.4, block_ymax + 5.4],
                "hypothetical_width_mm": (block_ymax - block_ymin) + 10.8,
                "resulting_conditional_block_distances_mm": {
                    axis1: to_y_faces(y1_current, block_ymin - 5.4, block_ymax + 5.4),
                    axis2: to_y_faces(y2_current, block_ymin - 5.4, block_ymax + 5.4),
                },
                "status": "arithmetic_sensitivity_only_not_a_member_design_or_CAD_change",
                "unverified_consequences": "changed block stock/envelope, mating fit, washer/support, access, finished profile, receiver contacts, and all adjoining features require review",
            },
        },
        "mating_bore_consequence": {
            "current_axis_register_matches": matched,
            "required_if_proposed": "Translate each existing axis's base_header and inner-block bore together by that axis's signed Y shift; their present 3.75 mm-radius cylinders and top-face circles are matched at the current positions only.",
            "both_receiver_bores_regenerated_or_verified_at_proposed_centers": False,
            "proposal_does_not_move_any_axis_or_model": True,
        },
        "washer_support": {
            "dimensional_basis": washer["catalog_washer_dimensional_scenario"],
            "current_bg045_outer_wood_seats_exact_occ": {
                "seat_count": 4,
                "all_full_dimensional_annuli_supported": True,
                "max_modeled_face_tilt_deg": max(
                    row["modeled_face_tilt_deg"] for row in current_seat_rows
                ),
                "seat_rows": current_seat_rows,
                "scope": "exact current CAD face/annulus OCC result only; head/nut-to-washer metal footprint and actual contact/resistance are separate and unresolved",
            },
            "conditional_translated_planar_face_scenarios": washer_scenarios,
            "moved_brep_washer_query_performed": False,
        },
        "known_feature_and_axis_consequences": {
            "bg003_orthogonal_bore_web": {
                "current_minimum_modeled_web_mm": web_current["minimum_pairwise_modeled_envelope_web_mm"],
                "proposal_minimum_modeled_web_mm": web_both["minimum_pairwise_modeled_envelope_web_mm"],
                "change_mm": (web_both["minimum_pairwise_modeled_envelope_web_mm"]
                              - web_current["minimum_pairwise_modeled_envelope_web_mm"]),
                "governing_pair": web["axis2_only_avoids_axis1_both_face_web_consequence"][
                    "governing_both_face_pair"],
                "interpretation": "modeled envelope geometry only; not a strength, splitting, net-section, or cutting acceptance check",
            },
            "panel_kicker_screw_axes": {
                "source_inventory_count": 66,
                "proposal_axis_changes": 0,
                "existing_affected_base_header_projection_subset_count":
                    screw_projection["source_axis_count"],
                "existing_projection_minima_under_scenario_mm": {
                    axis1: screw_screen[axis1]["minimum_xy_projected_centerline_distance_mm"],
                    axis2: screw_screen[axis2]["minimum_xy_projected_centerline_distance_mm"],
                },
                "screen_limit": screw_projection["interpretation"],
            },
        },
        "code_and_strength_boundary": {
            "source_disposition": edge_disposition,
            "loaded_edge_and_splitting_method_resolved": False,
            "resultant_or_component_selects_4d_face": False,
            "web_is_a_splitting_criterion": False,
            "current_load_actions_transfer_to_moved_geometry": False,
            "no_adjusted_or_group_capacity_or_joint_acceptance": True,
        },
        "not_ready_dependencies": [
            "Resolve by source-backed NDS interpretation whether either block Y face is the required loaded edge for the actual signed, grain-relative group actions; do not infer from coordinate band alone.",
            "If retained, regenerate and independently review the header and block geometry together, including both matched through-bores, exact finished face loops, tolerances, and every intersecting feature; current register describes the unmoved model only.",
            "Requery all four BG045 washer wood seats on the regenerated model. The margins here assume translated target circles and fixed unrelated loops; no new OCC result, delivered washer fit, physical flatness, or metal bearing footprint is established.",
            "Recompute signed actions/load sharing on the relocated reviewed geometry; existing actions and orthogonal-web screen describe the current source geometry.",
            "Establish the applicable complete-joint lateral/axial interaction and a supported group splitting/net-section/shear-out method; the 2.053 mm modeled web is not a capacity criterion.",
            "Recheck all affected receiving features and 66 unchanged panel/kicker axes on the regenerated model. The existing screw projection is only ten base_header axes in XY and does not prove clearance, backing, or installation.",
        ],
        "source_guard": {
            "source_pins_sha256": sha256(PINS_PATH),
            "producer_sha256": sha256(Path(__file__)),
            "pinned_direct_input_count": len(pins["files"]),
            "recursively_checked_pin_documents": loaded["recursive_pin_counts"],
            "old_axis2_only_producer_executed": False,
            "native_geometry_or_load_solve_executed": False,
        },
    }


def dump_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write this packet's proposal.json only")
    mode.add_argument("--verify", action="store_true", help="read-only source and replay verification")
    args = parser.parse_args()
    expected = dump_bytes(produce())
    if args.write:
        OUTPUT_PATH.write_bytes(expected)
        print(f"wrote {OUTPUT_PATH.relative_to(ROOT)} sha256={hashlib.sha256(expected).hexdigest()}")
    else:
        actual = OUTPUT_PATH.read_bytes()
        if actual != expected:
            raise SystemExit("proposal.json does not replay byte-for-byte")
        print(f"read-only replay passed: sha256={hashlib.sha256(actual).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
