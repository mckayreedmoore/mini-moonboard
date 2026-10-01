#!/usr/bin/env python3
"""Reproduce the bounded BG045 conditional detailing arithmetic.

This reads already-produced source records only. It does not query CAD, rebuild
geometry, alter an axis, inspect hardware, or run a structural solver.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
HERE = Path(__file__).resolve().parent
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")

PINNED_SOURCE_SHA256 = {
    "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/README.md": "b9cfe28dfed2205da3f2375f7563e2d8839bd0588dba85bdf7e3777ab01c9250",
    "docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/diagnostics.json": "174f8f945e41a273318a41fc401f1ef484160b500d624d80f57cd3480a343c98",
    f"{BASE}/current-bg045-edge-applicability-dependency-attempt01/README.md": "84631f7eefbefe13a778914c87bb157bf66a7f53c07d2c942e26b5e71f902f88",
    f"{BASE}/current-bg045-edge-applicability-dependency-attempt01/dependency.json": "98916b15d05b3ed023e6d099b1643f7155693eb10b780ac12ca2dfa9fc57d772",
    f"{BASE}/current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md": "565f686f6d4d0bdca6eee747c9f682f4277847abd31db6f6aef178bcafb6685c",
    f"{BASE}/current-corner-bg045-two-case-wood-mode-screen-attempt01/screen.json": "6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b",
    f"{BASE}/current-corner-local-wood-screen-attempt01/README.md": "3e50086cea176a3dc282f3da4fcc9c2d3ddfee20d7867d4f6dec512e5dc56006",
    f"{BASE}/current-corner-local-wood-screen-attempt01/section-screen.json": "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    f"{BASE}/current-knee-three-member-profile-attempt01/README.md": "0809625dad5c960854c1a2657989ff121ab115888d9dedd6f12e0b4a2fd22321",
    f"{BASE}/current-knee-three-member-profile-attempt01/query.json": "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854",
    f"{BASE}/current-knee-three-member-profile-attempt01/source-pins.json": "629552eba2b3dd2639df245dde56afb46dae7c01d2b2b9b1d774f98ca4a846c7",
    f"{BASE}/bolt-groups/bolt-groups.json": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    f"{BASE}/current-corner-washer-seat-screen-attempt01/README.md": "6faede5b5473d30295b3a65047d44c30dcd91112b661cabd512e95e7ea94d645",
    f"{BASE}/current-corner-washer-seat-screen-attempt01/seat-screen.json": "67dda5964a9c2a864cdb5ee0e898bae3c9e6bea212e2eeb71d5b33f765481ef0",
    "docs/floor-flush-construction-kerf-right/connection-axes.csv": "174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58",
    "docs/wood-joints-mvp/wj24-fixed-screw-receiver-audit.md": "704b23bf5ed37a6ca0f136279d235c13b518da9f0ec8aeba6008f35ce0422529",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json": "c1e53e9a08599d13a992fc11a493853c1695f697f3fe99b45af20795c430240a",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(relative_path: str | Path) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text())


def close(a: float, b: float, tol: float = 1e-8) -> bool:
    return abs(a - b) <= tol


def point_segment_xy_distance(point: tuple[float, float], start: tuple[float, float], end: tuple[float, float]) -> tuple[float, float, tuple[float, float]]:
    dx, dy = end[0] - start[0], end[1] - start[1]
    den = dx * dx + dy * dy
    t = 0.0 if den == 0.0 else max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / den))
    nearest = (start[0] + t * dx, start[1] + t * dy)
    return math.hypot(point[0] - nearest[0], point[1] - nearest[1]), t, nearest


def main() -> None:
    observed_pins = {rel: sha256(ROOT / rel) for rel in PINNED_SOURCE_SHA256}
    mismatches = {
        rel: {"expected": PINNED_SOURCE_SHA256[rel], "observed": observed_pins[rel]}
        for rel in PINNED_SOURCE_SHA256
        if observed_pins[rel] != PINNED_SOURCE_SHA256[rel]
    }
    if mismatches:
        raise SystemExit(f"pinned inputs changed; stop and re-review: {json.dumps(mismatches, sort_keys=True)}")

    dep_path = BASE / "current-bg045-edge-applicability-dependency-attempt01/dependency.json"
    demand_path = BASE / "current-corner-bg045-two-case-wood-mode-screen-attempt01/screen.json"
    section_path = BASE / "current-corner-local-wood-screen-attempt01/section-screen.json"
    profile_path = BASE / "current-knee-three-member-profile-attempt01/query.json"
    groups_path = BASE / "bolt-groups/bolt-groups.json"
    seats_path = BASE / "current-corner-washer-seat-screen-attempt01/seat-screen.json"

    dep = read_json(dep_path)
    demand = read_json(demand_path)
    section = read_json(section_path)
    profile = read_json(profile_path)
    groups = read_json(groups_path)
    seats = read_json(seats_path)

    if dep["status"] != "CONDITIONAL_EDGE_RULE_APPLICABILITY_PENDING":
        raise SystemExit("edge-rule dependency status changed")
    if demand["geometry_revision_id"] != "led-clearance-2x6-runner-seated-blocks-v1":
        raise SystemExit("BG045 geometry revision changed")
    if groups["geometry_revision_id"] != demand["geometry_revision_id"]:
        raise SystemExit("axis group geometry revision differs")
    if len(groups["candidate_axes"]) != 92:
        raise SystemExit("reviewed candidate bolt-axis inventory is not 92")
    if profile["scope"]["physical_stack_group_id"] != "BG003" or profile["scope"]["ray_count"] != 72:
        raise SystemExit("pinned BG003 finished-profile query scope changed")

    diameter_mm = float(dep["recorded_quarter_inch_scenario_diameter_mm"])
    loaded_edge_4d_mm = float(dep["perpendicular_loaded_edge_reference_mm"])
    recorded_distance_mm = float(dep["modeled_envelope_distance_under_question_mm"])
    shortfall_mm = loaded_edge_4d_mm - recorded_distance_mm
    if not (close(diameter_mm, 6.35) and close(loaded_edge_4d_mm, 4.0 * diameter_mm)):
        raise SystemExit("conditional 1/4-in, 4D arithmetic changed")
    if not close(shortfall_mm, float(dep["nominal_shortfall_mm"])):
        raise SystemExit("source 5.4 mm conditional exception changed")

    edge_rows = demand["nds_edge_and_end_distance_conditional_comparator"]["block_perpendicular_to_grain_loaded_edge_comparator"]["a1-rear"]
    axis2_edge = next(row for row in edge_rows if row["axis_id"] == "knee_outer_left_inner_header_2")
    if axis2_edge["axis_force_ray_first_face"]["first_face_on_force_ray"] != "-Y":
        raise SystemExit("A1 axis 2 first ray face changed")
    if not close(axis2_edge["all_four_center_to_face_distances_mm"]["y_minus"], recorded_distance_mm):
        raise SystemExit("A1 axis 2 source-envelope face distance changed")

    axis_ids = ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
    group_axes = {row["axis_id"]: row for row in groups["candidate_axes"] if row["axis_id"] in axis_ids}
    if set(group_axes) != set(axis_ids):
        raise SystemExit("one or more BG045 source axes missing")
    axes = {
        axis_id: {
            "current_xyz_mm": [float(v) for v in group_axes[axis_id]["shaft_center_global_xyz_mm"]],
            "direction_xyz": [float(v) for v in group_axes[axis_id]["axis_head_to_nut_unit_global_xyz"]],
            "modeled_shaft_diameter_mm": float(group_axes[axis_id]["modeled_shaft_diameter_mm"]),
        }
        for axis_id in axis_ids
    }
    if not all(close(a["current_xyz_mm"][0], -1085.85) for a in axes.values()):
        raise SystemExit("BG045 X station changed")
    block = demand["member_frames_and_source_envelopes"]["knee_outer_left_inner_frame_block"]
    header = demand["member_frames_and_source_envelopes"]["base_header"]
    y_minus, y_plus = map(float, block["y_edge_bounds_mm"])
    if not (close(y_minus, -175.7) and close(y_plus, -42.35)):
        raise SystemExit("BG045 source block Y envelope changed")

    current_y = {axis_id: axes[axis_id]["current_xyz_mm"][1] for axis_id in axis_ids}
    target_y = {
        axis_ids[0]: y_plus - loaded_edge_4d_mm,
        axis_ids[1]: y_minus + loaded_edge_4d_mm,
    }
    movements = {axis_id: target_y[axis_id] - current_y[axis_id] for axis_id in axis_ids}
    if not (close(target_y[axis_ids[0]], -67.75) and close(target_y[axis_ids[1]], -150.3)):
        raise SystemExit("both-Y-face 4D envelope target changed")
    if not (close(movements[axis_ids[0]], -shortfall_mm) and close(movements[axis_ids[1]], shortfall_mm)):
        raise SystemExit("proposed sensitivity movement is not symmetric 5.4 mm")

    model_inputs = section["modeled_geometry_inputs"]
    bore_diameter_mm = float(model_inputs["modeled_bore_diameter_mm_from_profile_void_intervals"])
    bg003_centers = model_inputs["same_section_plane_void_reconciliation"]["bg003_x_bore_centers_xyz_mm"]
    if len(bg003_centers) != 2 or not close(bore_diameter_mm, 7.5):
        raise SystemExit("BG003 bore geometry input changed")
    bg003_ys = [float(center[1]) for center in bg003_centers]

    def bore_matrix(y_values: dict[str, float]) -> dict[str, dict[str, dict[str, float]]]:
        out: dict[str, dict[str, dict[str, float]]] = {}
        for axis_id in axis_ids:
            out[axis_id] = {}
            for index, bore_y in enumerate(bg003_ys, start=1):
                centerline = abs(y_values[axis_id] - bore_y)
                out[axis_id][f"BG003_x_bore_{index}"] = {
                    "BG003_bore_axis_y_mm": bore_y,
                    "centerline_distance_mm": centerline,
                    "modeled_bore_envelope_web_mm": centerline - bore_diameter_mm,
                }
        return out

    current_bores = bore_matrix(current_y)
    proposed_bores = bore_matrix(target_y)
    current_min = min(v["centerline_distance_mm"] for row in current_bores.values() for v in row.values())
    proposed_min = min(v["centerline_distance_mm"] for row in proposed_bores.values() for v in row.values())
    if not close(current_min, 14.952644215640262) or not close(proposed_min, 9.552644215640262):
        raise SystemExit("reproduced BG003/BG045 minimum centerline distance changed")

    def y_face_distances(y: float, bounds: list[float]) -> dict[str, float]:
        return {"minus_y": y - float(bounds[0]), "plus_y": float(bounds[1]) - y}

    header_bounds = [float(v) for v in header["y_edge_bounds_mm"]]
    block_bounds = [y_minus, y_plus]
    face_screens = {
        axis_id: {
            "current_block_center_to_face_mm": y_face_distances(current_y[axis_id], block_bounds),
            "proposed_block_center_to_face_mm": y_face_distances(target_y[axis_id], block_bounds),
            "current_header_envelope_center_to_face_mm": y_face_distances(current_y[axis_id], header_bounds),
            "proposed_header_envelope_center_to_face_mm": y_face_distances(target_y[axis_id], header_bounds),
        }
        for axis_id in axis_ids
    }

    screw_rows: list[dict[str, Any]] = []
    register_rows = read_json("docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-hardware-material-cost-closeout-attempt01/fastener-axis-register.json")["hillman_axis_rows"]
    register_by_id = {row["axis_id"]: row for row in register_rows}
    if "kicker_header_left_5" not in register_by_id or register_by_id["kicker_header_left_5"]["owner_moved_axis"]:
        raise SystemExit("nearest visible header screw is not confirmed as an unchanged Hillman station")
    screw_csv = ROOT / "docs/floor-flush-construction-kerf-right/connection-axes.csv"
    with screw_csv.open(newline="") as f:
        for row in csv.DictReader(f):
            if row["kind"] != "screw" or row["shop_opening_kind"] != "hillman_panel" or row["second_member"] != "base_header":
                continue
            start3 = tuple(float(row[f"start_{axis}_mm"]) for axis in "xyz")
            direction3 = tuple(float(row[f"direction_{axis}"]) for axis in "xyz")
            length = float(row["occupied_length_mm"])
            end3 = tuple(start3[i] + direction3[i] * length for i in range(3))
            screw_rows.append({
                "axis_id": row["name"],
                "receiver": row["second_member"],
                "start_xyz_mm": start3,
                "end_xyz_mm": end3,
                "occupied_envelope_diameter_mm": float(row["occupied_diameter_mm"]),
            })
    if len(screw_rows) != 10:
        raise SystemExit(f"expected 10 unchanged source Hillman axes entering base_header, found {len(screw_rows)}")
    screw_projection_minima = {}
    for axis_id in axis_ids:
        p = (axes[axis_id]["current_xyz_mm"][0], target_y[axis_id])
        candidates = []
        for screw in screw_rows:
            a = (screw["start_xyz_mm"][0], screw["start_xyz_mm"][1])
            b = (screw["end_xyz_mm"][0], screw["end_xyz_mm"][1])
            dist, t, q = point_segment_xy_distance(p, a, b)
            candidates.append((dist, screw, t, q))
        dist, screw, t, q = min(candidates, key=lambda item: item[0])
        screw_projection_minima[axis_id] = {
            "minimum_2d_xy_projected_centerline_distance_mm": dist,
            "nearest_axis_id": screw["axis_id"],
            "nearest_receiver": screw["receiver"],
            "nearest_axis_xy_projection_mm": list(q),
            "nearest_axis_segment_fraction": t,
            "nearest_source_occupied_envelope_diameter_mm": screw["occupied_envelope_diameter_mm"],
            "interpretation": "XY projection to the ten base-header screw envelopes is a lower-bound geometry screen; Z separation is omitted and the source diameter is not a delivered Hillman dimension.",
        }

    seat_by_axis = {row["axis_id"]: row for row in seats["axes"] if row["axis_id"] in axis_ids}
    if set(seat_by_axis) != set(axis_ids):
        raise SystemExit("BG045 washer seat source rows missing")
    washer_seat_status = {
        axis_id: {
            "selected_product": seat_by_axis[axis_id].get("selected_product"),
            "fit_status": seat_by_axis[axis_id]["fit_status"],
            "missing_limits": list(seat_by_axis[axis_id]["limits"]),
            "current_outer_seat_points_xyz_mm": [seat["seat_point_xyz_mm"] for seat in seat_by_axis[axis_id]["outer_seats"]],
            "only_y_translation_proposed": True,
        }
        for axis_id in axis_ids
    }

    pitch_current = abs(current_y[axis_ids[0]] - current_y[axis_ids[1]])
    pitch_proposed = abs(target_y[axis_ids[0]] - target_y[axis_ids[1]])
    a1_axis2_force = next(row for row in demand["per_axis_signed_actions_and_geometry"]["a1-rear"] if row["axis_id"] == axis_ids[1])["physical_lateral_action_on_block_xyz_n"]
    a1_axis1_force = next(row for row in demand["per_axis_signed_actions_and_geometry"]["a1-rear"] if row["axis_id"] == axis_ids[0])["physical_lateral_action_on_block_xyz_n"]

    result = {
        "schema": "current_bg045_conditional_detailing_exception/v1",
        "status": "CONDITIONAL_DETAILING_EXCEPTION_PRESERVED; BOTH_FACE_BAND_IS_UNAPPROVED_SENSITIVITY",
        "candidate": demand["candidate"],
        "geometry_revision_id": demand["geometry_revision_id"],
        "scope": "A1-rear BG045 axes 1/2 only; source-bound edge arithmetic and one geometry-only both-Y-face band sensitivity. No axis or production geometry changes.",
        "execution_boundary": {
            "native_solve_run": False,
            "cad_query_or_rebuild_run": False,
            "geometry_or_axis_files_modified": False,
            "hardware_inspection_required_for_this_arithmetic": False,
        },
        "conditional_exception": {
            "case": "A1-rear",
            "axis_id": axis_ids[1],
            "member": "knee_outer_left_inner_frame_block",
            "modeled_force_on_block_xyz_n": a1_axis2_force,
            "proposed_block_grain_xyz": [0.0, 0.0, 1.0],
            "force_is_perpendicular_to_proposed_grain": True,
            "signed_direction": "+X, -Y",
            "ray_first_face": axis2_edge["axis_force_ray_first_face"]["first_face_on_force_ray"],
            "current_source_envelope_minus_y_distance_mm": recorded_distance_mm,
            "conditional_bolt_diameter_mm": diameter_mm,
            "conditional_nds_perpendicular_loaded_edge_comparator_mm": loaded_edge_4d_mm,
            "conditional_shortfall_mm": shortfall_mm,
            "inspection_note": "The 20.0 mm minus-Y versus 25.4 mm 4D subtraction is reproducible from the current source envelope; delivered-stock inspection is not a prerequisite to record this explicitly conditional exception.",
            "disposition": "not an adopted NDS failure, complete-joint failure, or authority to move an axis",
        },
        "applicability_boundary": {
            "tabulated_scope": "NDS-2024 Chapter 12: §12.5.1.3 directs D >= 1/4 in dowels to Tables 12.5.1C/12.5.1D; Table 12.5.1C gives 4D loaded and 1.5D unloaded perpendicular-to-grain edge distances. The block's proposed +Z grain and XY lateral action place this block action in the perpendicular-to-grain category for the named conditional scenario.",
            "edge_definition": "The reviewed NDS §12.1.2.1 text defines edge distance normal to grain and describes the loaded edge for perpendicular-to-grain load. The source A1 axis-2 vector and A1 group resultant both point to -Y first in the rectangular-ray screen; that ray is geometric context, not a universal NDS rule for arbitrary oblique vectors.",
            "component_vs_ray": "The signed-component screen checks separate rectangular faces. For A1 axis 2, both ray and component identify -Y, so the reported 20 mm exposure is not the A12 axis-1-style case where a different first ray face and a short component-face sensitivity diverge. No blanket component-face criterion is inferred.",
            "end_grain_factor": "NDS §12.5.2.2 Ceg lateral adjustment does not waive §12.5.1.3 detailing.",
            "header": "The base header's proposed +X grain is oblique to the full lateral action; an isolated transverse component is not a complete mixed-direction Table 12.5.1C determination.",
            "unresolved": [
                "Applicability details for the finished end-grain block and any group-level versus individual-bolt load-direction convention.",
                "Finished dimensions/profile, tolerances, actual fastener diameter and hole, and full-joint detailing.",
                "NDS row/spacing checks; the source geometry groups are not established as NDS rows.",
            ],
            "primary_nds_source_pin": {
                "path_as_recorded_in_dependency": dep["primary_source_path"],
                "sha256": dep["primary_source_sha256"],
                "clauses": dep["clauses"],
            },
        },
        "unapproved_both_y_face_band_sensitivity": {
            "rule": "For arithmetic only, require both Y face distances >= 4D; this is deliberately more conservative than a loaded/unloaded-edge split and is not presented as an NDS rule or approved axis move.",
            "block_y_bounds_mm": [y_minus, y_plus],
            "target_y_interval_mm": [y_minus + loaded_edge_4d_mm, y_plus - loaded_edge_4d_mm],
            "axes": {
                axis_ids[0]: {"current_y_mm": current_y[axis_ids[0]], "proposed_y_mm": target_y[axis_ids[0]], "delta_y_mm": movements[axis_ids[0]], "A1_force_on_block_xyz_n": a1_axis1_force, "current_loaded_minus_y_edge_mm": face_screens[axis_ids[0]]["current_block_center_to_face_mm"]["minus_y"], "current_plus_y_edge_mm": face_screens[axis_ids[0]]["current_block_center_to_face_mm"]["plus_y"], "interpretation": "A1 force points toward -Y; on this named reading its -Y loaded edge is 113.35 mm. The 20 mm +Y side is the unloaded side and exceeds conditional 1.5D=9.525 mm; shifting axis 1 for a symmetric 4D band is not required by that loaded-edge comparison."},
                axis_ids[1]: {"current_y_mm": current_y[axis_ids[1]], "proposed_y_mm": target_y[axis_ids[1]], "delta_y_mm": movements[axis_ids[1]], "current_minus_y_loaded_edge_mm": recorded_distance_mm, "conditional_minus_y_loaded_edge_mm": loaded_edge_4d_mm},
            },
            "center_pitch_y_mm": {"current": pitch_current, "proposed": pitch_proposed, "change_mm": pitch_proposed - pitch_current},
            "approval_status": "not approved; no production axis/model changes",
        },
        "orthogonal_bg003_bore_consequence": {
            "source_basis": "Existing 72-ray BG003 finished-profile query and its same-section-plane reconciliation with BG045 bores; this packet reuses those outputs without querying or rebuilding CAD.",
            "modeled_bore_diameter_mm": bore_diameter_mm,
            "bg003_x_bore_center_y_z_mm": [[float(row[1]), float(row[2])] for row in bg003_centers],
            "bg045_axis_y_current_mm": current_y,
            "bg045_axis_y_sensitivity_mm": target_y,
            "pairwise_current": current_bores,
            "pairwise_sensitivity": proposed_bores,
            "minimum_centerline_distance_mm": {"current": current_min, "both_face_sensitivity": proposed_min},
            "minimum_modeled_bore_envelope_web_mm": {"current": current_min - bore_diameter_mm, "both_face_sensitivity": proposed_min - bore_diameter_mm},
            "geometry_consequence": "The band moves BG045 axis 1 5.4 mm toward the nearer BG003 orthogonal bore. Their minimum source centerline separation drops 5.4 mm, from 14.953 to 9.553 mm; subtracting the sum of equal bore radii (7.5 mm total for two 7.5 mm-diameter bores) gives a nominal 2.053 mm web. This is a geometry screen only, not a wood strength or splitting criterion.",
            "stop_condition": "Before implementing an axis relocation or altering reviewed geometry, separately review the changed BG003/BG045 bore union, remaining web, finished-profile tolerances, washer/affected receiver seats, and applicable member-strength/splitting path. This packet permits describing conditional coordinates; it does not authorize a model change.",
        },
        "header_washer_and_hillman_receiver_screen": {
            "header_y_envelope_bounds_mm": header_bounds,
            "header_center_to_face_distances_by_axis": {axis_id: {"current": face_screens[axis_id]["current_header_envelope_center_to_face_mm"], "sensitivity": face_screens[axis_id]["proposed_header_envelope_center_to_face_mm"]} for axis_id in axis_ids},
            "header_reading": "The envelope-only proposed distances are 31.75/107.95 mm for axis 1 and 25.4/114.3 mm for axis 2 (plus-Y/minus-Y order reversed as keyed). They show no new rectangular-envelope edge proximity under this arithmetic; they do not settle the header's oblique-action table applicability or finished receiver.",
            "washer_seat_records": washer_seat_status,
            "washer_reading": "Seat centers would translate with their matching bolt center while X and Z remain fixed, but the pinned seat screen says the washer is unselected and the exact finished support polygon/opening radius is missing. No positive washer-fit or bearing-support conclusion is possible from these coordinates.",
            "base_header_hillman_axis_projection_minima": screw_projection_minima,
            "hillman_reading": "A bounded XY projection of the ten unchanged Hillman axes entering base_header identifies no near crossing; the closest is kicker_header_left_5, 85.85 mm from BG045 axis 1 and 118.551 mm from axis 2. This is only a lower-bound coordinate screen; source occupied diameters are legacy CAD envelopes, not delivered Hillman dimensions or receiver-capacity checks. No claim is made about the other 56 screw receivers.",
        },
        "missing_checks_and_stop": [
            "Resolve the conditional NDS loaded-edge interpretation for the completed block detail and any group-versus-individual force convention before applying 4D as an adopted requirement.",
            "Confirm final stock section, finished surfaces, cut/tolerance state, actual bolt/hole and member grain; inspection is not needed for this arithmetic but these facts are needed for final detailing.",
            "Before implementing any axis move, recompute exact continuous finished-profile void unions and affected BG003/BG045 distances, receiver backing, washer support/access, and corner receiver/clearance/load-transfer dependencies. This packet's identified screw dependency is the ten base_header Hillman axes; preserve the 66-axis inventory and expand the receiver review only for another identified geometric consequence. Preserve the reviewed 92-axis geometry until required changes are reported and reviewed.",
            "Develop the applicable wood bearing, net-section/row, group interaction and splitting checks for the changed complete joint; no universal oblique ray/component rule or complete splitting criterion is established here.",
        ],
        "source_pins_sha256": observed_pins,
    }
    result["producer_sha256"] = sha256(Path(__file__).resolve())
    output_path = HERE / "detail-screen.json"
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {output_path.relative_to(ROOT)}")
    print(f"producer_sha256={result['producer_sha256']}")
    print(f"current_min_web_mm={current_min - bore_diameter_mm:.9f}")
    print(f"sensitivity_min_web_mm={proposed_min - bore_diameter_mm:.9f}")


if __name__ == "__main__":
    main()
