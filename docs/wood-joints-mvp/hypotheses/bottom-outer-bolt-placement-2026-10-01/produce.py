#!/usr/bin/env python3
"""Bound bottom bolt placement and complete interface actions to frozen sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = HERE.parent
FEATURES = PACKETS / "current-finished-feature-register-2026-10-01/axis-features.json"
FEATURE_SHA = "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19"
JOINT_SHA = "fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029"
HELPER = ROOT / "mini_moonboard/connection_geometry.py"
HELPER_SHA = "f729bc64e7ea7fb9df9308411df07e02f98fc309efcf26038809a9e7bd4bc4a4"
METHOD_PINS = {
    "joint_producer": (PACKETS / "bottom-outer-joint-disposition-2026-10-01/produce.py",
                       "a941dceee5c002068e9920cfe41f62270e11ff399367fdf9494c445a06d8a86d"),
    "feature_producer": (FEATURES.with_name("axis_features.py"),
                         "e9787320589db65f1443b2c40607ed347cd5c4e8d5c8a2b9be73a5619275104f"),
    "chapter12": (PACKETS / "hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf",
                  "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"),
    "interval_helper": (HELPER, HELPER_SHA),
}
PREFIX = "bottom_outer/clip_horizontal_bottom_left_1/"
AXES = {f"{PREFIX}{role}_{i}" for role in ("rail", "side") for i in (1, 2)}
CLEAT, RAIL, SIDE = "bottom_outer_left_cleat", "base_rail_bottom_left", "base_side_left"
INTERFACES = {"rail": {CLEAT, RAIL}, "side": {CLEAT, SIDE}}
PATCHES = {"rail": 58, "side": 88}
D = 6.35
TOL = 2e-4


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    require(len(a) == 3 and all(math.isfinite(x) for x in a) and norm(a) > 0, "invalid vector")
    return scale(a, 1/norm(a))


def project(force, basis):
    return [dot(force, direction) for direction in basis]


def radius_project(radius, basis):
    require(len(radius) == 3 and all(math.isfinite(x) and x >= 0 for x in radius), "invalid rounding radii")
    return [dot(radius, [abs(x) for x in direction]) for direction in basis]


def resolved_sign(center, radius):
    return "positive" if center-radius > 0 else "negative" if center+radius < 0 else "unresolved"


def angle(a, b):
    return math.degrees(math.acos(max(0.0, min(1.0, abs(dot(a, b))/(norm(a)*norm(b)))))) if norm(a) else None


def checked_membership(axis, membership):
    frame = membership["stock_frame"]
    basis = frame["basis_columns_global_xyz"]
    require(len(basis) == 3 and all(abs(norm(v)-1) < 1e-8 for v in basis)
            and all(abs(dot(basis[i], basis[j])) < 1e-8 for i in range(3) for j in range(i)),
            "stock frame not orthonormal")
    require(dot(cross(basis[0], basis[1]), basis[2]) > 1-1e-8, "stock frame not right handed")
    field = axis["source_axis_fields"]
    direction = unit(field["direction_global_xyz"])
    datum = field["datum_global_xyz_mm"]
    local = membership["axis_in_stock_frame"]
    for actual, wanted in zip(project(sub(datum, frame["origin_global_xyz_mm"]), basis),
                              local["datum_stock_gqr_mm"], strict=True):
        require(abs(actual-wanted) < 1e-6, "source/global stock datum differs")
    require(all(abs(x-y) < 1e-8 for x, y in zip(project(direction, basis),
            local["direction_stock_gqr"], strict=True)), "source/global stock axis differs")
    require(abs(dot(direction, basis[0])) < 1e-6, "bottom axis not transverse to grain")
    require(membership["binding_status"] == "bound_to_current_finished_stock_frame"
            and membership["match_status"] == "matched_bore_patch"
            and len(membership["matched_feature_ids"]) == 1, "ambiguous finished bore")
    patches = [p for p in membership["cylinder_surface_candidates"]
               if p["feature_id"] in membership["matched_feature_ids"]]
    require(len(patches) == 1 and patches[0]["association_status"] == "eligible_bore_patch"
            and patches[0]["material_side_geometry"] == "bore_like", "wrong finished feature")
    patch = patches[0]
    require(abs(field["occupied_diameter_mm"]-D) < 1e-6
            and abs(patch["cylinder_radius_mm"]-3.75) < 1e-6, "diameter scenario differs")
    lo, hi = patch["patch_interval_projected_from_axis_datum_mm"]
    require(hi-lo > .02, "no interior bore interval")
    e = unit(cross(basis[0], direction))
    e_local = project(e, basis)
    e_index = max(range(1, 3), key=lambda i: abs(e_local[i]))
    require(abs(abs(e_local[e_index])-1) < 1e-6, "edge direction not stock aligned")
    dims = frame["original_dimensions_gqr_mm"]
    require(len(dims) == 3 and all(math.isfinite(x) and x > 0 for x in dims), "invalid stock dimensions")
    g_station, e_station = local["datum_stock_gqr_mm"][0], local["datum_stock_gqr_mm"][e_index]
    require(0 < g_station < dims[0] and 0 < e_station < dims[e_index], "bolt center outside face profile")
    e_minus, e_plus = (e_station, dims[e_index]-e_station) if e_local[e_index] > 0 else (dims[e_index]-e_station, e_station)
    return {"axis_id": axis["axis_id"], "member_id": membership["receiver_member_id"],
            "stock_frame": frame, "datum_stock_gqr_mm": local["datum_stock_gqr_mm"],
            "axis_datum_xyz_mm": datum, "axis_direction_xyz": direction,
            "grain_direction_xyz": basis[0], "edge_direction_xyz": e,
            "matched_bore_feature_id": patch["feature_id"], "bore_radius_mm": patch["cylinder_radius_mm"],
            "bore_axis_interval_from_datum_mm": [lo, hi],
            "finished_step_binding": membership["current_finished_step_binding"],
            "stock_center_to_boundary_mm": {"g-": g_station, "g+": dims[0]-g_station,
                                            "e-": e_minus, "e+": e_plus}}


def finished_rays(record, shape, material_intervals):
    import cadquery as cq

    lo, hi = record["bore_axis_interval_from_datum_mm"]
    result = []
    for station_name, t in (("near_first", lo+.01), ("mid_depth", (lo+hi)/2), ("near_second", hi-.01)):
        origin = add(record["axis_datum_xyz_mm"], scale(record["axis_direction_xyz"], t))
        for label, basis in (("g", record["grain_direction_xyz"]), ("e", record["edge_direction_xyz"])):
            for sign, suffix in ((-1, "-"), (1, "+")):
                expected = record["stock_center_to_boundary_mm"][label+suffix]
                intervals = material_intervals(shape, origin, scale(basis, sign), 0, expected+5)
                last = intervals[-1][1] if intervals else None
                gaps, end = [], 0
                for a, b in intervals:
                    if a-end > TOL:
                        gaps.append([end, a])
                    end = b
                require(intervals and intervals[0][0] >= record["bore_radius_mm"]-TOL,
                        "own bore not preserved by finished query")
                terminal_point = add(origin, scale(basis, sign*last))
                vertex = cq.Vertex.makeVertex(*terminal_point)
                terminal_faces = []
                for index, face in enumerate(shape.Faces(), 1):
                    if vertex.distance(face) <= TOL:
                        terminal_faces.append({"feature_id": f"{record['member_id']}/facet{index:03d}",
                                               "surface_kind": face.geomType(),
                                               "face_center_xyz_mm": list(face.Center().toTuple()),
                                               "face_area_mm2": face.Area()})
                require(terminal_faces and all(f["surface_kind"] == "PLANE" for f in terminal_faces),
                        "terminal ray boundary is not an identified planar exterior profile")
                result.append({"station": station_name, "axis_station_mm": t, "ray": label+suffix,
                               "origin_xyz_mm": origin, "direction_xyz": scale(basis, sign),
                               "material_intervals_mm": intervals, "void_intervals_mm": gaps,
                               "center_to_last_material_exit_mm": last,
                               "center_to_stock_boundary_mm": expected,
                               "terminal_matches_stock_boundary": last is not None and abs(last-expected) <= TOL,
                               "terminal_finite_face_candidates": terminal_faces,
                               "continuous_depth_extrema_proved": False})
    return result


def action_on_member(action, member):
    require(member in (action["first"], action["second"]), "action/member boundary differs")
    first = member == action["first"]
    force = action["force_on_first_xyz_n" if first else "force_on_second_xyz_n"]
    other = action["force_on_second_xyz_n" if first else "force_on_first_xyz_n"]
    require(all(abs(x+y) < 1e-9 for x, y in zip(force, other, strict=True)), "source action is not reciprocal")
    point = action.get("first_point" if first else "second_point", action["point"])
    radius = action["force_rounding_radius_xyz_n"]
    radius_project(radius, [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    return force, radius, point


def produce(joint_path):
    require(sha(joint_path) == JOINT_SHA and sha(FEATURES) == FEATURE_SHA, "frozen input changed")
    for name, (path, expected) in METHOD_PINS.items():
        require(sha(path) == expected, f"pinned method changed: {name}")
    joint, features = json.loads(joint_path.read_text()), json.loads(FEATURES.read_text())
    candidate, revision = "compact-floor-flush-wood-joints-development", "led-clearance-2x6-runner-seated-blocks-v1"
    require(joint["candidate"] == features["candidate"] == candidate
            and joint["geometry_revision_id"] == features["geometry_revision_id"] == revision,
            "candidate or revision differs")
    for pins in (joint["source_pins"], *joint["case_sources"].values()):
        for pin in pins.values():
            require(sha(ROOT / pin["path"]) == pin["sha256"], "upstream source changed")
    group = features["source_axis_groups"]["candidate_bolt_axes"]
    require(group["axis_count"] == len(group["axes"]) == 92, "candidate axis count differs")
    axes = {a["axis_id"]: a for a in group["axes"] if a["axis_id"] in AXES}
    require(set(axes) == AXES, "four-bolt scope differs")
    sys.path.insert(0, str(ROOT))
    import cadquery as cq

    from mini_moonboard.connection_geometry import material_intervals
    placements, shapes = {}, {}
    for axis_id, axis in sorted(axes.items()):
        role = axis_id.removeprefix(PREFIX).split("_")[0]
        require({r["receiver_member_id"] for r in axis["receiver_memberships"]} == INTERFACES[role]
                and len(axis["receiver_memberships"]) == 2, "receiver set differs")
        for membership in axis["receiver_memberships"]:
            row = checked_membership(axis, membership)
            member = row["member_id"]
            binding = row["finished_step_binding"]
            path = ROOT / binding["path"]
            require(sha(path) == binding["file_sha256"], "finished STEP changed")
            if member not in shapes:
                shape = cq.importers.importStep(str(path)).val()
                require(shape.isValid() and len(shape.Solids()) == 1 and len(shape.Faces()) == binding["face_count"],
                        "finished shape invalid or changed")
                shapes[member] = shape
            row["finished_rays"] = finished_rays(row, shapes[member], material_intervals)
            distances = row["stock_center_to_boundary_mm"]
            row["edge_category_envelope"] = {
                "D_mm": D, "edge_threshold_4D_mm": 4*D,
                "interface_scope_condition": "two axes on this interface only; no adopted NDS group",
                "every_stock_cross_grain_edge_exceeds_4D": min(distances["e-"], distances["e+"]) >= 4*D,
                "smallest_stock_edge_margin_mm": min(distances["e-"], distances["e+"])-4*D,
                "edge_terminal_matches_at_three_depth_stations": all(r["terminal_matches_stock_boundary"] for r in row["finished_rays"] if r["ray"].startswith("e")),
                "minimum_sampled_finished_edge_mm": min(r["center_to_last_material_exit_mm"] for r in row["finished_rays"] if r["ray"].startswith("e")),
                "adopted_Table_12_5_1C_pass": False}
            row["softwood_tension_end_sensitivity"] = {
                "full_value_7D_mm": 7*D, "minimum_3_5D_mm": 3.5*D,
                "shortest_end_mm": min(distances["g-"], distances["g+"]),
                "every_stock_end_exceeds_7D": min(distances["g-"], distances["g+"]) >= 7*D,
                "end_ratio_to_7D": min(distances["g-"], distances["g+"])/(7*D),
                "minimum_sampled_finished_end_mm": min(r["center_to_last_material_exit_mm"] for r in row["finished_rays"] if r["ray"].startswith("g")),
                "stock_end_matches_at_three_depth_stations": all(r["terminal_matches_stock_boundary"] for r in row["finished_rays"] if r["ray"].startswith("g")),
                "adopted_Cdelta": None}
            placements[(axis_id, member)] = row
    pair_geometry = {}
    for role, members in INTERFACES.items():
        first, second = [axes[f"{PREFIX}{role}_{i}"]["source_axis_fields"]["datum_global_xyz_mm"] for i in (1, 2)]
        line = sub(second, first)
        require(abs(norm(line)-33) < 1e-5, "pair center spacing differs")
        pair_geometry[role] = {"axis_ids": [f"{PREFIX}{role}_{i}" for i in (1, 2)],
                              "center_spacing_mm": norm(line), "pair_line_xyz": unit(line),
                              "possible_between_row_S_over_2_upper_bound_mm": norm(line)/2,
                              "four_D_dominates_this_interface_S_over_2_bound": 4*D >= norm(line)/2,
                              "adopted_NDS_row_or_group": False,
                              "member_pair_line_stock_gqr": {member: project(unit(line), placements[(f"{PREFIX}{role}_1", member)]["stock_frame"]["basis_columns_global_xyz"]) for member in sorted(members)}}
    member_states, interface_states = [], []
    require(len(joint["joint_states"]) == 21, "state count differs")
    identities = set()
    for state in joint["joint_states"]:
        identity = {k: state[k] for k in ("case_id", "increment_index", "load_factor")}
        identity_key = (identity["case_id"], identity["increment_index"])
        require(identity_key not in identities, "duplicate state")
        identities.add(identity_key)
        rows = {r["axis_id"]: r for r in state["bolt_reference_rows"]}
        require(len(state["bolt_reference_rows"]) == 4 and set(rows) == AXES, "state bolt coverage differs")
        boundary = state["cleat_complete_boundary_actions"]
        for axis_id, row in sorted(rows.items()):
            plane, tie = boundary[row["lateral_plane_source_name"]], boundary[axis_id+"/outer-seat-axial-tie"]
            require(plane["source_row_ids"] == row["lateral_plane_source_row_ids"]
                    and tie["source_row_ids"] == row["same_state_tie_source_row_ids"], "bolt/native source mapping differs")
            for member in sorted({plane["first"], plane["second"]}):
                placement = placements[(axis_id, member)]
                basis = placement["stock_frame"]["basis_columns_global_xyz"]
                lateral, r_lateral, _ = action_on_member(plane, member)
                axial, r_axial, _ = action_on_member(tie, member)
                require(abs(dot(lateral, placement["axis_direction_xyz"])) < 1e-5
                        and norm(cross(axial, placement["axis_direction_xyz"])) < 1e-5, "lateral/axial action decomposition differs")
                require(abs(norm(lateral)-row["actual_lateral_resultant_N"]) < 1e-8
                        and abs(norm(axial)-abs(row["same_state_signed_outer_tie_N_once"])) < 1e-8, "source force differs")
                local, radii = project(lateral, basis), radius_project(r_lateral, basis)
                edge_center = dot(lateral, placement["edge_direction_xyz"])
                edge_radius = dot(r_lateral, [abs(x) for x in placement["edge_direction_xyz"]])
                member_states.append({**identity, "axis_id": axis_id, "member_id": member,
                    "plane_source_row_ids": plane["source_row_ids"], "tie_source_row_ids": tie["source_row_ids"],
                    "lateral_force_stock_gqr_N": local, "lateral_radius_stock_gqr_N": radii,
                    "grain_component_sign": resolved_sign(local[0], radii[0]),
                    "cross_grain_e_component_N": edge_center, "cross_grain_e_radius_N": edge_radius,
                    "cross_grain_e_component_sign": resolved_sign(edge_center, edge_radius),
                    "candidate_loaded_edge_from_lateral_component": "e+" if edge_center-edge_radius > 0 else "e-" if edge_center+edge_radius < 0 else None,
                    "full_bolt_force_on_member_xyz_N": add(lateral, axial),
                    "axial_tie_on_member_xyz_N": axial, "axial_radius_xyz_N": r_axial,
                    "full_force_angle_to_bolt_axis_deg": angle(add(lateral, axial), placement["axis_direction_xyz"]),
                    "source_role": "component direction diagnostic, not an adopted NDS loaded edge"})
        for role, members in INTERFACES.items():
            names = sorted([rows[f"{PREFIX}{role}_{i}"]["lateral_plane_source_name"] for i in (1, 2)]
                           + [f"{PREFIX}{role}_{i}/outer-seat-axial-tie" for i in (1, 2)]
                           + [f"contact_{PATCHES[role]}_{i}" for i in range(4)])
            require(len(names) == 8 and all({boundary[n]["first"], boundary[n]["second"]} == members for n in names),
                    "complete interface boundary differs")
            midpoint = scale(add(axes[f"{PREFIX}{role}_1"]["source_axis_fields"]["datum_global_xyz_mm"],
                                 axes[f"{PREFIX}{role}_2"]["source_axis_fields"]["datum_global_xyz_mm"]), .5)
            for member in sorted(members):
                force, radius, moment = [0., 0., 0.], [0., 0., 0.], [0., 0., 0.]
                for name in names:
                    f, r, point = action_on_member(boundary[name], member)
                    force, radius = add(force, f), add(radius, r)
                    moment = add(moment, cross(sub(point, midpoint), f))
                line = pair_geometry[role]["pair_line_xyz"]
                interface_states.append({**identity, "interface": role, "member_id": member,
                    "source_action_names": names, "datum_pair_axis_midpoint_xyz_mm": midpoint,
                    "complete_interface_force_xyz_N": force, "force_radius_xyz_N": radius,
                    "complete_interface_moment_about_datum_Nmm": moment,
                    "force_angle_to_pair_line_deg": angle(force, line),
                    "force_not_aligned_with_pair_line_beyond_source_rounding": norm(cross(force, line)) > 2*norm(radius),
                    "adopted_NDS_row_or_group": False,
                    "other_joint_interfaces_and_body_loads_included": False})
    return {"schema": "bottom_outer_bolt_placement/v1", "status": "PASS_FROZEN_SOURCE_JOIN_AND_BOUNDED_GEOMETRY_ONLY",
            "producer_sha256": sha(HERE / "produce.py"), "candidate": candidate, "geometry_revision_id": revision,
            "joint_source_sha256": JOINT_SHA, "feature_source_sha256": FEATURE_SHA,
            "method_pins": {name: {"path": str(path.relative_to(ROOT)), "sha256": value} for name, (path, value) in METHOD_PINS.items()},
            "counts": {"axes": 4, "receiver_memberships": len(placements),
                       "finished_rays": sum(len(p["finished_rays"]) for p in placements.values()),
                       "member_bolt_states": len(member_states), "member_interface_states": len(interface_states)},
            "placements": list(placements.values()), "pair_geometry": pair_geometry,
            "member_bolt_states": member_states, "member_interface_states": interface_states,
            "claim_limits": {"adopted_geometry_factor": False, "adopted_group_factor": False,
                             "continuous_through_depth_profile_extrema": False, "complete_host_sections_or_resistance": False,
                             "joint_accepted": False, "criterion_pass": False, "geometry_changed": False, "native_solve": False}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--joint-report", type=Path, required=True)
    print(json.dumps(produce(parser.parse_args().joint_report), indent=2, allow_nan=False))
