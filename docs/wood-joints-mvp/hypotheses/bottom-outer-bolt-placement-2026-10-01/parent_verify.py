#!/usr/bin/env python3
"""Independent source-coordinate and force/moment oracle for bottom bolt placement."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = HERE.parent
PRODUCER = HERE / "produce.py"
PRODUCER_SHA = "75e7eed05e9f24c1a04b35a8faeb03e4f284259ae2af54abd45c611bb2e0684f"
REPORT_DEFAULT = Path("/tmp/mini-moonboard-bottom-outer-placement-2026-10-01.json")
REPORT_SHA = "21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3"
JOINT_REPORT = Path("/tmp/mini-moonboard-bottom-outer-joint-2026-10-01.json")
JOINT_SHA = "fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029"
JOINT_PRODUCER_SHA = "a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d"
FEATURES = PACKETS / "current-finished-feature-register-2026-10-01/axis-features.json"
FEATURE_SHA = "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19"
FEATURE_PRODUCER = FEATURES.with_name("axis_features.py")
FEATURE_PRODUCER_SHA = "e9787320589db65f1443b2c40607ed347cd5c4e8d5c8a2b9be73a5619275104f"
GEOMETRY_HELPER = ROOT / "mini_moonboard/connection_geometry.py"
GEOMETRY_HELPER_SHA = "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4"
CHAPTER12 = PACKETS / "hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf"
CHAPTER12_SHA = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
FREEZE = PACKETS / "upper-frame-joint-review-2026-09-30/freeze.json"
FREEZE_SHA = "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73"
METHOD_PINS = {
    "joint_producer": (PACKETS / "bottom-outer-joint-disposition-2026-10-01/produce.py", JOINT_PRODUCER_SHA),
    "feature_producer": (FEATURE_PRODUCER, FEATURE_PRODUCER_SHA),
    "chapter12": (CHAPTER12, CHAPTER12_SHA),
    "interval_helper": (GEOMETRY_HELPER, GEOMETRY_HELPER_SHA),
}
PREFIX = "bottom_outer/clip_horizontal_bottom_left_1/"
AXES = {f"{PREFIX}{role}_{i}" for role in ("rail", "side") for i in (1, 2)}
CLEAT, RAIL, SIDE = "bottom_outer_left_cleat", "base_rail_bottom_left", "base_side_left"
INTERFACES = {"rail": {CLEAT, RAIL}, "side": {CLEAT, SIDE}}
PATCHES = {"rail": 58, "side": 88}
D = 6.35
RAY_TOL = 2e-4
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def dot(a, b):
    return math.fsum(x*y for x, y in zip(a, b, strict=True))


def add(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def sub(a, b):
    return [x-y for x, y in zip(a, b, strict=True)]


def scale(a, s):
    return [x*s for x in a]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def norm(a):
    return math.sqrt(dot(a, a))


def unit(a):
    require(len(a) == 3 and all(math.isfinite(float(x)) for x in a) and norm(a) > 0,
            "invalid direction")
    return scale(a, 1/norm(a))


def project(v, basis):
    return [dot(v, direction) for direction in basis]


def radius_project(radius, basis):
    require(len(radius) == 3 and all(math.isfinite(x) and x >= 0 for x in radius),
            "invalid Cartesian force radius")
    return [dot(radius, [abs(x) for x in direction]) for direction in basis]


def resolved_sign(center, radius):
    return "positive" if center-radius > 0 else "negative" if center+radius < 0 else "unresolved"


def angle(a, b):
    return math.degrees(math.acos(max(0.0, min(1.0, abs(dot(a, b))/(norm(a)*norm(b)))))) if norm(a) else None


def close(a, b, tol=1e-8):
    return math.isfinite(float(a)) and math.isfinite(float(b)) and abs(float(a)-float(b)) <= tol


def expect(actual, expected, label, tol=1e-8):
    if isinstance(expected, dict):
        require(isinstance(actual, dict) and set(actual) == set(expected), f"{label}: keys differ")
        for key in expected:
            expect(actual[key], expected[key], f"{label}/{key}", tol)
    elif isinstance(expected, list):
        require(isinstance(actual, list) and len(actual) == len(expected), f"{label}: list length differs")
        for index, (a, b) in enumerate(zip(actual, expected, strict=True)):
            expect(a, b, f"{label}[{index}]", tol)
    elif isinstance(expected, float):
        require(close(actual, expected, tol), f"{label}: {actual!r} != {expected!r}")
    else:
        require(actual == expected, f"{label}: {actual!r} != {expected!r}")


def self_test():
    require(cross([2, 3, 4], [5, 7, 11]) == [5, -2, -1], "known-answer cross product failed")
    require(project([3, 4, 5], [[1, 0, 0], [0, 1, 0], [0, 0, 1]]) == [3, 4, 5],
            "known-answer stock projection failed")
    require(radius_project([2, 3, 5], [[1, 0, 0], [0, 0.6, 0.8], [0, -0.8, 0.6]])
            == [2, 5.8, 5.4], "known-answer radius projection failed")
    require(resolved_sign(-3, 0.5) == "negative" and resolved_sign(0.2, 0.3) == "unresolved",
            "known-answer interval-sign fixture failed")


def derive_placement(axis, membership):
    frame = membership["stock_frame"]
    basis = frame["basis_columns_global_xyz"]
    require(len(basis) == 3 and all(close(norm(v), 1, 1e-8) for v in basis)
            and all(abs(dot(basis[i], basis[j])) < 1e-8 for i in range(3) for j in range(i)),
            "finished-feature stock basis is not orthonormal")
    require(dot(cross(basis[0], basis[1]), basis[2]) > 1-1e-8, "stock basis is not right handed")
    fields = axis["source_axis_fields"]
    axis_direction = unit(fields["direction_global_xyz"])
    datum = fields["datum_global_xyz_mm"]
    local = project(sub(datum, frame["origin_global_xyz_mm"]), basis)
    local_axis_direction = project(axis_direction, basis)
    given_local = membership["axis_in_stock_frame"]
    expect(given_local["datum_stock_gqr_mm"], local, "feature/global bolt datum", 1e-6)
    expect(given_local["direction_stock_gqr"], local_axis_direction, "feature/global axis direction", 1e-8)
    require(abs(dot(axis_direction, basis[0])) < 1e-6, "modeled bolt is not transverse to proposed grain")
    require(close(fields["occupied_diameter_mm"],
                  membership["cylinder_surface_candidates"][0]["source_occupied_diameter_mm"], 1e-6)
            and close(fields["occupied_diameter_mm"], D, 1e-6), "nominal modeled shaft diameter differs")
    require(membership["binding_status"] == "bound_to_current_finished_stock_frame"
            and membership["match_status"] == "matched_bore_patch"
            and len(membership["matched_feature_ids"]) == 1, "finished bore-feature association is ambiguous")
    candidates = [r for r in membership["cylinder_surface_candidates"]
                  if r["feature_id"] in membership["matched_feature_ids"]]
    require(len(candidates) == 1 and candidates[0]["association_status"] == "eligible_bore_patch"
            and candidates[0]["material_side_geometry"] == "bore_like", "wrong matched bore patch")
    patch = candidates[0]
    require(abs(patch["cylinder_radius_mm"]-3.75) < 1e-6
            and patch["source_occupied_diameter_mm"] == fields["occupied_diameter_mm"], "bore/source diameter differs")
    lo, hi = patch["patch_interval_projected_from_axis_datum_mm"]
    require(hi > lo and close(hi-lo, patch["axial_overlap_length_mm"], 1e-6), "bore interval differs")
    grain = unit(basis[0])
    edge = unit(cross(grain, axis_direction))
    edge_local = project(edge, basis)
    edge_index = max(range(1, 3), key=lambda i: abs(edge_local[i]))
    require(abs(abs(edge_local[edge_index])-1) < 1e-6, "cross-grain edge direction is not stock aligned")
    dims = frame["original_dimensions_gqr_mm"]
    require(len(dims) == 3 and all(math.isfinite(x) and x > 0 for x in dims), "invalid proposed stock dimensions")
    g_station = local[0]
    e_station = local[edge_index]
    require(0 < g_station < dims[0] and 0 < e_station < dims[edge_index], "bolt center outside stock face")
    e_minus, e_plus = ((e_station, dims[edge_index]-e_station) if edge_local[edge_index] > 0
                       else (dims[edge_index]-e_station, e_station))
    return {
        "axis_id": axis["axis_id"], "member_id": membership["receiver_member_id"],
        "stock_frame": frame, "datum_stock_gqr_mm": local, "axis_datum_xyz_mm": datum,
        "axis_direction_xyz": axis_direction, "grain_direction_xyz": grain,
        "edge_direction_xyz": edge, "matched_bore_feature_id": patch["feature_id"],
        "bore_radius_mm": patch["cylinder_radius_mm"],
        "bore_axis_interval_from_datum_mm": [lo, hi],
        "finished_step_binding": membership["current_finished_step_binding"],
        "stock_center_to_boundary_mm": {
            "g-": g_station, "g+": dims[0]-g_station, "e-": e_minus, "e+": e_plus,
        },
        "edge_index": edge_index, "edge_local_sign": 1 if edge_local[edge_index] > 0 else -1,
    }


def verify_placement_record(output, derived):
    for key in ("axis_id", "member_id", "stock_frame", "matched_bore_feature_id", "finished_step_binding"):
        expect(output[key], derived[key], f"placement/{key}")
    for key in ("datum_stock_gqr_mm", "axis_datum_xyz_mm", "axis_direction_xyz", "grain_direction_xyz",
                "edge_direction_xyz", "bore_axis_interval_from_datum_mm", "stock_center_to_boundary_mm"):
        expect(output[key], derived[key], f"placement/{key}", 1e-6)
    expect(output["bore_radius_mm"], derived["bore_radius_mm"], "placement/bore radius", 1e-6)
    return output


def verify_rays(placement, derived):
    lo, hi = derived["bore_axis_interval_from_datum_mm"]
    stations = {"near_first": lo+0.01, "mid_depth": (lo+hi)/2, "near_second": hi-0.01}
    expected_rays = {f"{label}{sign}": scale(direction, 1 if sign == "+" else -1)
                     for label, direction in (("g", derived["grain_direction_xyz"]),
                                              ("e", derived["edge_direction_xyz"]))
                     for sign in ("-", "+")}
    rays = placement["finished_rays"]
    require(len(rays) == 12, "expected 12 sampled depth/ray records per placement")
    seen = set()
    by_direction = {"g": [], "e": []}
    for ray in rays:
        key = (ray["station"], ray["ray"])
        require(key not in seen and ray["station"] in stations and ray["ray"] in expected_rays,
                "duplicate/unexpected finished ray")
        seen.add(key)
        t = stations[ray["station"]]
        origin = add(derived["axis_datum_xyz_mm"], scale(derived["axis_direction_xyz"], t))
        expect(ray["axis_station_mm"], t, f"ray {key} depth", 1e-8)
        expect(ray["origin_xyz_mm"], origin, f"ray {key} source-plane point", 1e-6)
        expect(ray["direction_xyz"], expected_rays[ray["ray"]], f"ray {key} direction", 1e-8)
        expected_boundary = derived["stock_center_to_boundary_mm"][ray["ray"]]
        expect(ray["center_to_stock_boundary_mm"], expected_boundary, f"ray {key} analytic stock edge", 1e-6)
        intervals = ray["material_intervals_mm"]
        require(intervals and all(len(i) == 2 and 0 <= i[0] <= i[1] for i in intervals),
                f"invalid material intervals on ray {key}")
        require(all(intervals[i][1] <= intervals[i+1][0]+1e-8 for i in range(len(intervals)-1)),
                f"overlapping/unsorted material intervals on ray {key}")
        require(abs(intervals[0][0]-derived["bore_radius_mm"]) <= RAY_TOL,
                f"ray {key} does not leave material at the matched own bore")
        require(intervals[-1][1] <= expected_boundary+RAY_TOL,
                f"ray {key} exceeds the stock boundary projection")
        gaps, end = [], 0.0
        for start, stop in intervals:
            if start-end > RAY_TOL:
                gaps.append([end, start])
            end = stop
        expect(ray["void_intervals_mm"], gaps, f"ray {key} void complement", 1e-8)
        expect(ray["center_to_last_material_exit_mm"], intervals[-1][1], f"ray {key} last material exit", 1e-8)
        matched = abs(intervals[-1][1]-expected_boundary) <= RAY_TOL
        require(ray["terminal_matches_stock_boundary"] is matched,
                f"ray {key} stock-boundary flag differs")
        require(ray["terminal_finite_face_candidates"]
                and all(row["surface_kind"] == "PLANE" for row in ray["terminal_finite_face_candidates"]),
                f"ray {key} terminal face candidates are not planar")
        require(ray["continuous_depth_extrema_proved"] is False, "sampled ray was promoted to a continuous-depth bound")
        by_direction[ray["ray"][0]].append(ray)
    require(len(seen) == 12, "incomplete station/ray product")
    # All e rays should meet the source stock side plane at each sampled depth;
    # g rays may terminate at an intervening finished cut (notably the side host).
    require(len(by_direction["e"]) == 6 and all(r["terminal_matches_stock_boundary"] for r in by_direction["e"]),
            "sampled cross-grain rays do not terminate at the analytic stock sides")
    return by_direction


def verify_edge_sensitivities(placement, derived, rays):
    distances = derived["stock_center_to_boundary_mm"]
    min_edge = min(distances["e-"], distances["e+"])
    edge_rows = [r for r in rays["e"]]
    edge_sensitivity = placement["edge_category_envelope"]
    expect(edge_sensitivity["D_mm"], D, "edge scenario D")
    expect(edge_sensitivity["edge_threshold_4D_mm"], 4*D, "edge scenario 4D")
    require(edge_sensitivity["interface_scope_condition"] == "two axes on this interface only; no adopted NDS group",
            "edge sensitivity scope changed")
    require(edge_sensitivity["every_stock_cross_grain_edge_exceeds_4D"] is (min_edge >= 4*D)
            and edge_sensitivity["smallest_stock_edge_margin_mm"] == min_edge-4*D,
            "analytic stock-edge distance/4D sensitivity differs")
    expect(edge_sensitivity["edge_terminal_matches_at_three_depth_stations"],
           all(r["terminal_matches_stock_boundary"] for r in edge_rows), "sampled e-ray terminal summary")
    expect(edge_sensitivity["minimum_sampled_finished_edge_mm"],
           min(r["center_to_last_material_exit_mm"] for r in edge_rows), "sampled finished e-ray minimum")
    require(edge_sensitivity["adopted_Table_12_5_1C_pass"] is False,
            "stock geometry sensitivity claimed an adopted edge-distance pass")
    shortest_end = min(distances["g-"], distances["g+"])
    end_rows = [r for r in rays["g"]]
    sensitivity = placement["softwood_tension_end_sensitivity"]
    expect(sensitivity["full_value_7D_mm"], 7*D, "end sensitivity 7D")
    expect(sensitivity["minimum_3_5D_mm"], 3.5*D, "end sensitivity 3.5D")
    expect(sensitivity["shortest_end_mm"], shortest_end, "analytic proposed-stock end")
    require(sensitivity["every_stock_end_exceeds_7D"] is (shortest_end >= 7*D),
            "analytic proposed-stock end/7D flag differs")
    expect(sensitivity["end_ratio_to_7D"], shortest_end/(7*D), "proposed-stock end/7D ratio")
    expect(sensitivity["minimum_sampled_finished_end_mm"],
           min(r["center_to_last_material_exit_mm"] for r in end_rows), "sampled finished g-ray minimum")
    expect(sensitivity["stock_end_matches_at_three_depth_stations"],
           all(r["terminal_matches_stock_boundary"] for r in end_rows), "sampled g-ray terminal summary")
    require(sensitivity["adopted_Cdelta"] is None, "sensitivity assigned adopted Cdelta")


def check_source_pins(report, joint):
    require(sha(PRODUCER) == PRODUCER_SHA and sha(JOINT_REPORT) == JOINT_SHA
            and sha(FEATURES) == FEATURE_SHA and sha(FEATURE_PRODUCER) == FEATURE_PRODUCER_SHA
            and sha(FREEZE) == FREEZE_SHA, "producer/report/feature/freeze pin changed")
    require(report["producer_sha256"] == PRODUCER_SHA
            and report["joint_source_sha256"] == JOINT_SHA
            and report["feature_source_sha256"] == FEATURE_SHA,
            "output source digests differ")
    require(set(report["method_pins"]) == set(METHOD_PINS), "method pin names differ")
    for name, (path, digest) in METHOD_PINS.items():
        require(report["method_pins"][name] == {"path": path.relative_to(ROOT).as_posix(), "sha256": digest}
                and sha(path) == digest, f"method pin differs: {name}")
    require(joint["producer_sha256"] == JOINT_PRODUCER_SHA
            and joint["schema"] == "bottom_outer_joint_disposition/v1"
            and joint["claim_limits"]["joint_accepted"] is False,
            "bottom-outer joint source identity/claim boundary differs")
    for pin in joint["source_pins"].values():
        require(sha(ROOT / pin["path"]) == pin["sha256"], "bottom-joint upstream source pin changed")
    for pin in joint["material_source_pins"]:
        require(sha(ROOT / pin["path"]) == pin["sha256"], "bottom-joint material source pin changed")
    freeze = load(FREEZE)
    require(joint["case_sources"] == freeze["cases"], "joint source case set differs from frozen cases")
    for case, files in freeze["cases"].items():
        for kind, pin in files.items():
            require(sha(ROOT / pin["path"]) == pin["sha256"], f"frozen {case}/{kind} file changed")
    return freeze


def verify_response_actions(joint, freeze):
    responses, models = {}, {}
    joint_states = {(s["case_id"], s["increment_index"]): s for s in joint["joint_states"]}
    require(len(joint_states) == 21, "joint source does not contain 21 unique states")
    for case, files in freeze["cases"].items():
        model = load(ROOT / files["model"]["path"])
        response = load(ROOT / files["response"]["path"])
        audit = load(ROOT / files["all_body_audit"]["path"])
        require(model["candidate"] == response["candidate"] == joint["candidate"]
                and model["geometry_revision_id"] == response["geometry_revision_id"] == joint["geometry_revision_id"]
                and model["case_id"] == response["case_id"] == case,
                f"frozen case identity differs: {case}")
        require(response["source_input_model_json_sha256"] == files["model"]["sha256"]
                and response["source_input_deck_sha256"] == files["deck"]["sha256"]
                and response["native_data_sha256"] == files["native_data"]["sha256"]
                and audit["source_model_sha256"] == files["model"]["sha256"]
                and audit["source_response_sha256"] == files["response"]["sha256"],
                f"native response/audit provenance differs: {case}")
        require(tuple(i["load_factor"] for i in response["increments"]) == FACTORS
                and tuple(i["load_factor"] for i in audit["increments"]) == FACTORS,
                f"increment coverage differs: {case}")
        for index, inc in enumerate(response["increments"]):
            state = joint_states[(case, index)]
            require(state["load_factor"] == inc["load_factor"], "joint/native increment differs")
            boundary = state["cleat_complete_boundary_actions"]
            require(len(boundary) == 16, "joint source cleat boundary action count differs")
            response_actions = inc["physical_connection_forces"]
            for name, action in boundary.items():
                require(name in response_actions and action == response_actions[name],
                        f"joint action differs from frozen response: {case}/{index}/{name}")
                require(all(math.isfinite(float(x)) for x in action["force_on_first_xyz_n"]
                            + action["force_on_second_xyz_n"] + action["force_rounding_radius_xyz_n"]),
                        "nonfinite force/action-radius source")
                require(all(x >= 0 for x in action["force_rounding_radius_xyz_n"]), "negative action radius")
                require(all(abs(a+b) <= 1e-9 for a, b in zip(action["force_on_first_xyz_n"],
                                                              action["force_on_second_xyz_n"], strict=True)),
                        "native action/reaction mismatch")
            responses[(case, index)], models[case] = (inc, audit["increments"][index]), model
    require(set(responses) == set(joint_states), "joint/native state key sets differ")
    return joint_states, responses, models


def verify_feature_placements(report, features):
    group = features["source_axis_groups"]["candidate_bolt_axes"]
    require(group["axis_count"] == len(group["axes"]) == 92, "feature group axis count differs")
    axes = {r["axis_id"]: r for r in group["axes"] if r["axis_id"] in AXES}
    require(set(axes) == AXES, "finished-feature register does not contain exact four axes")
    saved = {(r["axis_id"], r["member_id"]): r for r in report["placements"]}
    require(len(saved) == 8 and len(report["placements"]) == 8, "placement output is not the 8 memberships")
    derived = {}
    ray_counts = {"g": 0, "e": 0, "g_terminal_matches": 0, "e_terminal_matches": 0}
    for axis_id, axis in axes.items():
        role = axis_id.removeprefix(PREFIX).split("_")[0]
        memberships = axis["receiver_memberships"]
        require(len(memberships) == 2
                and {m["receiver_member_id"] for m in memberships} == INTERFACES[role],
                f"finished membership receiver set differs: {axis_id}")
        for membership in memberships:
            placement = derive_placement(axis, membership)
            row = saved[(axis_id, placement["member_id"])]
            verify_placement_record(row, placement)
            binding = placement["finished_step_binding"]
            require(sha(ROOT / binding["path"]) == binding["file_sha256"],
                    f"finished STEP hash differs: {placement['member_id']}")
            rays = verify_rays(row, placement)
            verify_edge_sensitivities(row, placement, rays)
            derived[(axis_id, placement["member_id"])] = placement
            for ray in row["finished_rays"]:
                ray_counts[ray["ray"][0]] += 1
                ray_counts[ray["ray"][0] + "_terminal_matches"] += int(ray["terminal_matches_stock_boundary"])
    return axes, saved, derived, ray_counts


def action_on_member(action, member):
    require(member in (action["first"], action["second"]), "action not incident on requested member")
    is_first = member == action["first"]
    force = action["force_on_first_xyz_n" if is_first else "force_on_second_xyz_n"]
    opposite = action["force_on_second_xyz_n" if is_first else "force_on_first_xyz_n"]
    require(all(abs(x+y) <= 1e-9 for x, y in zip(force, opposite, strict=True)), "source action is not reciprocal")
    point_key = "first_point" if is_first else "second_point"
    point = action[point_key] if point_key in action else action["point"]
    radius = action["force_rounding_radius_xyz_n"]
    require(len(force) == len(radius) == len(point) == 3
            and all(math.isfinite(float(x)) for x in force+radius+point)
            and all(x >= 0 for x in radius), "invalid action point/force/radius")
    return force, radius, point


def check_bolt_reference_row(bolt, plane, tie):
    require(plane["source_row_ids"] == bolt["lateral_plane_source_row_ids"]
            and tie["source_row_ids"] == bolt["same_state_tie_source_row_ids"],
            "bolt native source row mapping differs")
    expect(bolt["actual_lateral_force_on_receiver_0_N"], plane["force_on_first_xyz_n"],
           "signed receiver-0 force", 1e-10)
    expect(bolt["actual_lateral_force_on_receiver_1_N"], plane["force_on_second_xyz_n"],
           "signed receiver-1 force", 1e-10)
    expect(bolt["actual_lateral_force_rounding_radius_N"], plane["force_rounding_radius_xyz_n"],
           "lateral source force radius", 1e-10)
    expect(bolt["actual_lateral_resultant_N"], norm(plane["force_on_first_xyz_n"]),
           "lateral resultant", 1e-8)
    require(abs(dot(plane["force_on_first_xyz_n"], plane["axis"])) < 1e-8,
            "lateral plane action has material axial component")
    require(tie["role"] == "physical_bolt_outer_seat_tension"
            and tie["axis_id"] == bolt["axis_id"], "outer-seat tie identity differs")
    expect(bolt["same_state_signed_outer_tie_N_once"], tie["axial_along_installation_direction_n"],
           "separate signed outer tie", 1e-8)
    expect(norm(tie["force_on_first_xyz_n"]), abs(bolt["same_state_signed_outer_tie_N_once"]),
           "outer-tie axial magnitude", 1e-8)
    for row in bolt["single_shear_reference_assignments"]["scenarios"]:
        expect(row["actual_resultant_to_governing_reference"],
               bolt["actual_lateral_resultant_N"]/row["governing_unadjusted_reference_N"],
               "unadjusted lateral quotient")


def compare_member_states(report, joint_states, placements):
    source_rows, state_rows = {}, {}
    for (case, index), source_state in joint_states.items():
        bolts = {r["axis_id"]: r for r in source_state["bolt_reference_rows"]}
        require(set(bolts) == AXES, "source state bolt axis set differs")
        boundary = source_state["cleat_complete_boundary_actions"]
        for axis_id, bolt in bolts.items():
            plane = boundary[bolt["lateral_plane_source_name"]]
            tie = boundary[axis_id + "/outer-seat-axial-tie"]
            check_bolt_reference_row(bolt, plane, tie)
        for field in report["member_bolt_states"]:
            if field["case_id"] == case and field["increment_index"] == index:
                key = (case, index, field["axis_id"], field["member_id"])
                require(key not in state_rows, "duplicate member-bolt state")
                state_rows[key] = field
        for axis_id, bolt in bolts.items():
            plane = boundary[bolt["lateral_plane_source_name"]]
            tie = boundary[axis_id + "/outer-seat-axial-tie"]
            for member in (plane["first"], plane["second"]):
                placement = placements[(axis_id, member)]
                basis = placement["stock_frame"]["basis_columns_global_xyz"]
                lateral, lateral_radius, _point = action_on_member(plane, member)
                axial, axial_radius, _tie_point = action_on_member(tie, member)
                axis = placement["axis_direction_xyz"]
                require(abs(dot(lateral, axis)) < 1e-5
                        and norm(cross(axial, axis)) < 1e-5, "bolt plane/tie vector decomposition differs")
                expect(norm(lateral), bolt["actual_lateral_resultant_N"], "member lateral resultant")
                expect(norm(axial), abs(bolt["same_state_signed_outer_tie_N_once"]), "member tie resultant")
                local = project(lateral, basis)
                projected_radius = radius_project(lateral_radius, basis)
                e_center = dot(lateral, placement["edge_direction_xyz"])
                e_radius = dot(lateral_radius, [abs(v) for v in placement["edge_direction_xyz"]])
                total = add(lateral, axial)
                expected = {
                    "case_id": case, "increment_index": index, "load_factor": bolt["load_factor"],
                    "axis_id": axis_id, "member_id": member,
                    "plane_source_row_ids": plane["source_row_ids"], "tie_source_row_ids": tie["source_row_ids"],
                    "lateral_force_stock_gqr_N": local, "lateral_radius_stock_gqr_N": projected_radius,
                    "grain_component_sign": resolved_sign(local[0], projected_radius[0]),
                    "cross_grain_e_component_N": e_center, "cross_grain_e_radius_N": e_radius,
                    "cross_grain_e_component_sign": resolved_sign(e_center, e_radius),
                    "candidate_loaded_edge_from_lateral_component":
                        "e+" if e_center-e_radius > 0 else "e-" if e_center+e_radius < 0 else None,
                    "full_bolt_force_on_member_xyz_N": total,
                    "axial_tie_on_member_xyz_N": axial, "axial_radius_xyz_N": axial_radius,
                    "full_force_angle_to_bolt_axis_deg": angle(total, axis),
                    "source_role": "component direction diagnostic, not an adopted NDS loaded edge",
                }
                key = (case, index, axis_id, member)
                require(key in state_rows, f"member-state row missing: {key}")
                expect(state_rows[key], expected, f"independent member state {key}", 2e-8)
                source_rows[key] = expected
    require(len(state_rows) == len(source_rows) == 168, "member-bolt coverage is not 168")
    require(set(state_rows) == set(source_rows), "member-bolt keys differ")
    return source_rows


def derive_pair_geometry(report, axes, placements):
    result = {}
    for role, members in INTERFACES.items():
        id1, id2 = f"{PREFIX}{role}_1", f"{PREFIX}{role}_2"
        p1 = axes[id1]["source_axis_fields"]["datum_global_xyz_mm"]
        p2 = axes[id2]["source_axis_fields"]["datum_global_xyz_mm"]
        delta = sub(p2, p1)
        spacing = norm(delta)
        line = unit(delta)
        require(close(spacing, 33.0, 1e-5), f"{role} bolt center spacing differs")
        local_line = {member: project(line, placements[(id1, member)]["stock_frame"]["basis_columns_global_xyz"])
                      for member in sorted(members)}
        expected = {
            "axis_ids": [id1, id2], "center_spacing_mm": spacing, "pair_line_xyz": line,
            "possible_between_row_S_over_2_upper_bound_mm": spacing/2,
            "four_D_dominates_this_interface_S_over_2_bound": 4*D >= spacing/2,
            "adopted_NDS_row_or_group": False, "member_pair_line_stock_gqr": local_line,
        }
        got = report["pair_geometry"][role]
        expect(got, expected, f"pair geometry {role}", 2e-8)
        result[role] = expected
    require(set(report["pair_geometry"]) == set(INTERFACES), "pair geometry interfaces differ")
    return result


def compare_interfaces(report, joint_states, responses, axes, placements, pair_geometry):
    report_rows = {(r["case_id"], r["increment_index"], r["interface"], r["member_id"]): r
                   for r in report["member_interface_states"]}
    require(len(report_rows) == len(report["member_interface_states"]) == 84,
            "member interface state count/uniqueness differs")
    reconstructed = {}
    for (case, index), state in joint_states.items():
        inc, _audit = responses[(case, index)]
        boundary = state["cleat_complete_boundary_actions"]
        bolt_rows = {r["axis_id"]: r for r in state["bolt_reference_rows"]}
        for role, members in INTERFACES.items():
            axes_for_role = [f"{PREFIX}{role}_{i}" for i in (1, 2)]
            names = sorted([bolt_rows[axis]["lateral_plane_source_name"] for axis in axes_for_role]
                           + [axis + "/outer-seat-axial-tie" for axis in axes_for_role]
                           + [f"contact_{PATCHES[role]}_{i}" for i in range(4)])
            require(len(names) == 8 and all(name in boundary for name in names),
                    f"{role} complete interface action set differs")
            for name in names:
                action = boundary[name]
                require(action == inc["physical_connection_forces"][name]
                        and {action["first"], action["second"]} == members,
                        f"{role} interface action is not the original native pair: {name}")
            p1 = axes[axes_for_role[0]]["source_axis_fields"]["datum_global_xyz_mm"]
            p2 = axes[axes_for_role[1]]["source_axis_fields"]["datum_global_xyz_mm"]
            midpoint = scale(add(p1, p2), 0.5)
            line = pair_geometry[role]["pair_line_xyz"]
            for member in sorted(members):
                force, radius, moment = [0.0]*3, [0.0]*3, [0.0]*3
                for name in names:
                    f, r, point = action_on_member(boundary[name], member)
                    force = add(force, f)
                    radius = add(radius, r)
                    moment = add(moment, cross(sub(point, midpoint), f))
                not_aligned = norm(cross(force, line)) > 2*norm(radius)
                key = (case, index, role, member)
                expected = {
                    "case_id": case, "increment_index": index, "load_factor": state["load_factor"],
                    "interface": role, "member_id": member, "source_action_names": names,
                    "datum_pair_axis_midpoint_xyz_mm": midpoint,
                    "complete_interface_force_xyz_N": force, "force_radius_xyz_N": radius,
                    "complete_interface_moment_about_datum_Nmm": moment,
                    "force_angle_to_pair_line_deg": angle(force, line),
                    "force_not_aligned_with_pair_line_beyond_source_rounding": not_aligned,
                    "adopted_NDS_row_or_group": False,
                    "other_joint_interfaces_and_body_loads_included": False,
                }
                require(key in report_rows, f"member-interface row missing: {key}")
                expect(report_rows[key], expected, f"independent interface wrench {key}", 2e-8)
                reconstructed[key] = expected
    require(set(report_rows) == set(reconstructed), "member-interface state keys differ")
    return reconstructed


def verify(report_path: Path):
    self_test()
    require(sha(report_path) == REPORT_SHA, "raw placement report SHA differs")
    report, joint, features = load(report_path), load(JOINT_REPORT), load(FEATURES)
    require(report["schema"] == "bottom_outer_bolt_placement/v1"
            and report["status"] == "PASS_FROZEN_SOURCE_JOIN_AND_BOUNDED_GEOMETRY_ONLY"
            and report["claim_limits"] == {
                "adopted_geometry_factor": False, "adopted_group_factor": False,
                "continuous_through_depth_profile_extrema": False,
                "complete_host_sections_or_resistance": False, "joint_accepted": False,
                "criterion_pass": False, "geometry_changed": False, "native_solve": False,
            }, "placement report identity or claim limits changed")
    require(report["candidate"] == joint["candidate"] == features["candidate"]
            == "compact-floor-flush-wood-joints-development"
            and report["geometry_revision_id"] == joint["geometry_revision_id"]
            == features["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "candidate/revision source binding differs")
    freeze = check_source_pins(report, joint)
    axes, _saved_placements, derived_placements, ray_counts = verify_feature_placements(report, features)
    expected_counts = {"axes": 4, "receiver_memberships": 8, "finished_rays": 96,
                       "member_bolt_states": 168, "member_interface_states": 84}
    require(report["counts"] == expected_counts, "output coverage counts differ")
    require(ray_counts["g"] == 48 and ray_counts["e"] == 48
            and ray_counts["e_terminal_matches"] == 48,
            "96 ray direction/depth coverage or cross-grain analytic check differs")
    joint_states, responses, _models = verify_response_actions(joint, freeze)
    member_states = compare_member_states(report, joint_states, derived_placements)
    pair_geometry = derive_pair_geometry(report, axes, derived_placements)
    interface_states = compare_interfaces(report, joint_states, responses, axes, derived_placements, pair_geometry)
    force_magnitudes = [norm(row["complete_interface_force_xyz_N"]) for row in interface_states.values()]
    moment_magnitudes = [norm(row["complete_interface_moment_about_datum_Nmm"]) for row in interface_states.values()]
    return {
        "result": "PASS_INDEPENDENT_SOURCE_COORDINATE_AND_INTERFACE_WRENCH_ORACLE",
        "producer_sha256": sha(PRODUCER), "report_sha256": sha(report_path),
        "joint_report_sha256": sha(JOINT_REPORT), "feature_register_sha256": sha(FEATURES),
        "freeze_sha256": sha(FREEZE), "counts": expected_counts,
        "finished_ray_counts": ray_counts,
        "member_bolt_states_independently_reconstructed": len(member_states),
        "member_interface_wrenches_independently_reconstructed": len(interface_states),
        "maximum_complete_interface_force_resultant_N": max(force_magnitudes),
        "maximum_complete_interface_moment_resultant_Nmm": max(moment_magnitudes),
        "claim_boundary": "proposed-stock and source-action geometry only; no adopted NDS factor/group or joint acceptance",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=REPORT_DEFAULT)
    args = parser.parse_args()
    print(json.dumps(verify(args.report), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
