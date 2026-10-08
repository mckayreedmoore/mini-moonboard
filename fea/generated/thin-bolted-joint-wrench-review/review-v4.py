"""Unaccepted cold-q local applicability: geometry/kinematics only, no K."""

from __future__ import annotations

import copy
import hashlib
import json
from itertools import pairwise
from pathlib import Path

import numpy as np

from scripts import thin_bolted_finite_frame as finite
from scripts import thin_bolted_finite_mechanics as mechanical
from scripts import thin_bolted_panel_mechanics as panels
from scripts.thin_bolted_common_shaft import shaft_inputs
from scripts.thin_bolted_linear_timber_admission import point_displacement

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def verify(pins):
    for relative, expected in pins.items():
        if sha(ROOT / relative) != expected:
            raise ValueError("frozen source changed: " + relative)


def make_map(field, layout, shafts, metadata, assessment, integrated):
    """Reconstruct frozen coordinate ordering, without reading or forming K."""
    bodies = {r["member"]: {**copy.deepcopy(r), "kind": "timber"}
              for r in field["linear_timber_coordinate_map"]["members"]}
    offset = max(i for r in bodies.values() for row in r["node_dof_indices"] for i in row) + 1
    for fitting in layout["raw_fittings"]:
        ports = {r["flange"]: r["entry_xyz_mm"] for r in fitting["holes"]}
        bodies[fitting["angle_id"]] = {"kind": "fitting", "node_dof_indices": np.arange(offset, offset+12).reshape(2, 6).tolist(),
            "node_reference_centers_xyz_mm": [ports[f] for f in ("beam", "post")],
            "storage_basis_columns_xyz": np.eye(3).tolist(), "flange_node_map": {"beam": 0, "post": 1}}
        offset += 12
    geometry = {r["panel"]: r for r in assessment["panel_geometry"]}
    thickness = {r["panel"]: r["panel_thickness_mm"] for r in integrated["panel_machining"]["outlines"]}
    panel_map = {}
    for name in panels.PANELS:
        datum, size = metadata[name], metadata[name]["basis_size"]
        basis = panels.SheetBasis(geometry[name]["width_mm"], geometry[name]["height_mm"], field["parameters"]["panel_intervals"])
        if basis.size != size:
            raise ValueError("source panel basis size mismatch")
        panel_map[name] = {"kind": "panel", "global_dof_indices": list(range(offset, offset+3*size)),
            "origin_xyz_mm": datum["origin_xyz_mm"], "axes_columns_xyz": datum["local_axes_columns_xyz"],
            "thickness_mm": thickness[name], "basis_width_mm": basis.width, "basis_height_mm": basis.height,
            "basis_order": basis.order, "basis_knots_normalized": basis.knots.tolist()}
        offset += 3*size
    shaft_offset = offset
    gauge_index = len(field["response"]["diagnostic_last_q"])
    for shaft_number, shaft in enumerate(shafts):
        events = set(shaft["shaft_interval_mm"])
        for surface in shaft["surfaces"]:
            a, b = surface["interval_mm"]
            events.update((a, .5*(a+b), b))
        for end in shaft["ends"]:
            events.update((end["support_s_mm"], end["pressure_face_s_mm"]))
        coarse = []
        for event in sorted(events):
            if not coarse or event - coarse[-1] > 1e-6:
                coarse.append(event)
        stations = []
        for a, b in pairwise(coarse):
            stations.extend(np.linspace(a, b, max(1, int(np.ceil((b-a)/field["parameters"]["shaft_max_segment_mm"])))+1)[:-1])
        stations.append(coarse[-1])
        indices = np.arange(6*len(stations)).reshape(-1, 6)
        indices[0, 3] = -1
        keep = indices >= 0
        indices[keep] = np.arange(int(keep.sum()))+offset
        indices[0, 3] = gauge_index+shaft_number
        bodies[shaft["body"]] = {"kind": "shaft", "node_dof_indices": indices.tolist(),
            "node_reference_centers_xyz_mm": (shaft["point"]+np.asarray(stations)[:, None]*shaft["basis"][0]).tolist(),
            "storage_basis_columns_xyz": shaft["basis"].T.tolist(), "reference_start_xyz_mm": shaft["point"].tolist(),
            "reference_axis_xyz": shaft["basis"][0].tolist(), "reference_stations_mm": stations}
        offset += int(keep.sum())
    if offset != field["counts"]["dofs"] or {*bodies, *panel_map} != set(field["body_identities"]):
        raise ValueError("complete reconstructed coordinate/body census mismatch")
    q = np.r_[field["response"]["diagnostic_last_q"], np.zeros(len(shafts))]
    return {"ndof": len(q), "mechanical_bodies": bodies, "panels": panel_map}, q, shaft_offset


def pose(mapping, q, body, point, flange=None):
    point = np.asarray(point)
    if body in mapping["panels"]:
        row = mapping["panels"][body]
        basis = panels.SheetBasis(row["basis_width_mm"], row["basis_height_mm"], row["basis_order"]-3)
        axes, origin = np.asarray(row["axes_columns_xyz"]), np.asarray(row["origin_xyz_mm"])
        panel = {"basis": basis, "geometry": {"origin": origin, "axes": axes}}
        coef = q[np.asarray(row["global_dof_indices"])]
        linear = point + panels.point_matrix(panel, point) @ coef
        exact = finite.current_pose_from_map(mapping, body, point, q, allow_edge_extension=True)
        return {"linear_point": linear, "exact_point": exact["position_xyz_mm"],
                "rotation": None, "surface_normal": exact["current_vector_xyz"], "panel_normal_only": True}
    row = mapping["mechanical_bodies"][body]
    indices, centers, storage = np.asarray(row["node_dof_indices"]), np.asarray(row["node_reference_centers_xyz_mm"]), np.asarray(row["storage_basis_columns_xyz"])
    if row["kind"] == "fitting":
        i = row["flange_node_map"][flange]
        state = q[indices[i]]
        linear = point + state[:3] + np.cross(state[3:]/1000., point-centers[i])
        R = mechanical.so3_exp(state[3:]/1000.)
    else:
        stations, axis = np.asarray(row["reference_stations_mm"]), np.asarray(row["reference_axis_xyz"])
        s = float((point-np.asarray(row["reference_start_xyz_mm"])) @ axis)
        i = int(np.clip(np.searchsorted(stations, s)-1, 0, len(stations)-2))
        t = float(np.clip((s-stations[i])/(stations[i+1]-stations[i]), 0., 1.))
        state = q[indices[i:i+2].ravel()]
        nodal = (1-t)*state[:6]+t*state[6:]
        center = (1-t)*centers[i]+t*centers[i+1]
        linear = point+storage@nodal[:3]+np.cross(storage@nodal[3:]/1000., point-center)
        R = mechanical.interpolated_rotation(state, t, storage)[0]
        if row["kind"] == "timber":
            original = point_displacement({"members": [row]}, body, point, q)
            if np.max(abs(linear-point-original)) > 1e-8:
                raise ValueError("linear timber point replay differs from reviewed helper")
    exact = finite.current_pose_from_map(mapping, body, point, q, flange=flange)
    return {"linear_point": linear, "exact_point": exact["position_xyz_mm"], "rotation": R,
            "panel_normal_only": False}


def angle(a, b):
    return float(np.arccos(np.clip(np.dot(a, b)/(np.linalg.norm(a)*np.linalg.norm(b)), -1., 1.)))


def relative(identifier, mapping, q, first, second, p1, p2, normal, *, flange1=None, flange2=None, **meta):
    a, b = pose(mapping, q, first, p1, flange1), pose(mapping, q, second, p2, flange2)
    normal = np.asarray(normal); normal /= np.linalg.norm(normal)
    reference_delta = np.asarray(p1)-np.asarray(p2)
    linear_delta = a["linear_point"]-b["linear_point"]-reference_delta
    exact_delta = a["exact_point"]-b["exact_point"]
    n1 = a["surface_normal"] if a["panel_normal_only"] else a["rotation"]@normal
    n2 = b["surface_normal"] if b["panel_normal_only"] else b["rotation"]@normal
    # At all call sites panel is first and its own source normal matches normal.
    linear_projection = float(normal@linear_delta)
    exact_fixed_projection = float(normal@(exact_delta-reference_delta))
    exact_projection = float(n2@exact_delta-normal@reference_delta)
    exact_tangent = exact_delta-(n2@exact_delta)*n2
    linear_tangent = linear_delta-linear_projection*normal
    result = {"id": identifier, "first": first, "second": second, "first_reference_point_xyz_mm": np.asarray(p1).tolist(),
        "second_reference_point_xyz_mm": np.asarray(p2).tolist(), "first_flange": flange1, "second_flange": flange2,
        "linear_signed_projection_opening_positive_mm": linear_projection,
        "finite_arm_fixed_reference_normal_projection_mm": exact_fixed_projection,
        "finite_arm_updated_second_normal_projection_opening_positive_mm": exact_projection,
        "linear_tangent_motion_xyz_mm": linear_tangent.tolist(), "linear_tangent_motion_norm_mm": float(np.linalg.norm(linear_tangent)),
        "finite_arm_tangent_motion_xyz_mm": exact_tangent.tolist(), "finite_arm_tangent_motion_norm_mm": float(np.linalg.norm(exact_tangent)),
        "exact_minus_linear_relative_point_shift_norm_mm": float(np.linalg.norm(exact_delta-reference_delta-linear_delta)),
        "fixed_reference_normal_exact_minus_linear_projection_mm": exact_fixed_projection-linear_projection,
        "own_director_relative_angle_rad": angle(n1, n2),
        "fixed_q_normal_side_changes_in_updated_normal_diagnostic": bool((linear_projection > 0.) != (exact_projection > 0.)),
        "finite_arm_is_new_equilibrated_or_physical_response": False, **meta}
    if a["rotation"] is not None and b["rotation"] is not None:
        result["relative_material_rotation_vector_rad"] = mechanical.so3_log(b["rotation"].T@a["rotation"]).tolist()
        result["relative_material_rotation_norm_rad"] = float(np.linalg.norm(result["relative_material_rotation_vector_rad"]))
        result["shaft_full_material_roll_is_recorded_gauge_dependent"] = first.startswith("shaft/") or second.startswith("shaft/")
    else:
        result["relative_material_rotation_norm_rad"] = None
        result["panel_rotation_scope"] = "own surface-normal tilt; no finite rigid panel/material-frame rotation assigned"
    return result


def max_summary(rows):
    metrics = ("linear_tangent_motion_norm_mm", "finite_arm_tangent_motion_norm_mm", "exact_minus_linear_relative_point_shift_norm_mm",
               "own_director_relative_angle_rad")
    return {k: max(rows, key=lambda r: r[k]) for k in metrics}


def fixtures():
    center, point = np.zeros(3), np.array([10., 0., 0.])
    q = np.array([0., 0., 0., 0., 0., np.pi/2*1000.])
    expected = np.array([0., 10., 0.])
    actual = mechanical.rigid_port(point, center, q)[0]
    assert np.linalg.norm(actual-expected) < 1e-12
    # Geodesic equal-node rotation reproduces that exact rigid rotation.
    ends = np.array([[0., 0., 0.], [0., 0., 20.]])
    actual2 = mechanical.interpolated_point(point, ends, np.tile(q, 2), 0., np.eye(3))[0]
    assert np.linalg.norm(actual2-expected) < 1e-12
    assert abs(np.linalg.norm(mechanical.so3_log(mechanical.so3_exp([0., 0., .3])))-.3) < 1e-12
    return {"90_degree_rigid_arm_known_answer": True, "equal_node_geodesic_matches_rigid_arm": True,
            "relative_rotation_SO3_known_answer": True}


def evaluate(field, config, layout, shafts, metadata, assessment, integrated, proof, cache):
    mapping, q, shaft_offset = make_map(field, layout, shafts, metadata, assessment, integrated)
    fitting_by_id = {r["angle_id"]: r for r in layout["raw_fittings"]}
    selected = {r["angle_id"] for r in layout["raw_fittings"] if r["duty_id"] in config["duties"]}
    selected_axes = {a["id"] for a in layout["installed_axes"] if any(r["angle_id"] in selected for r in a["attachments"])}
    flange_rows, attachment_rows, fitting_internal = [], [], []
    for name in sorted(selected):
        fitting = fitting_by_id[name]
        o, u, v, w = (np.asarray(fitting[k]) for k in ("origin_xyz_mm", "u_xyz", "v_xyz", "w_xyz"))
        ports = {r["flange"]: r for r in fitting["holes"]}
        for flange, receiver, normal, along, length in (
            ("beam", fitting["beam"], v, u, 104.775),
            ("post", fitting["post"], u, v, 41.275 if name.startswith("B103ZN") else 88.9)):
            for corner, (s, t) in enumerate((s, t) for s in (5.55625, length) for t in (-20.6375, 20.6375)):
                point = o+along*s+w*t
                flange_rows.append(relative(name+"/"+flange+f"/contact-{corner}", mapping, q, name, receiver, point, point, normal,
                    flange1=flange, duty_id=fitting["duty_id"], kind="flange_contact"))
            point = ports[flange]["entry_xyz_mm"]
            attachment_rows.append(relative(name+"/"+flange+"/hole", mapping, q, name, receiver, point, point, ports[flange]["axis_xyz"],
                flange1=flange, duty_id=fitting["duty_id"], kind="fitting_receiver_hole_correspondence"))
        p1, p2 = ports["beam"]["entry_xyz_mm"], ports["post"]["entry_xyz_mm"]
        first_pose, second_pose = pose(mapping, q, name, p1, "beam"), pose(mapping, q, name, p2, "post")
        R1, R2 = first_pose["rotation"], second_pose["rotation"]
        current_chord = second_pose["exact_point"]-first_pose["exact_point"]
        objective_translation = R1.T@current_chord-(np.asarray(p2)-np.asarray(p1))
        rotation_vector = mechanical.so3_log(R1.T@R2)
        fitting_internal.append({"id": name+"/two-flange-port-pose", "duty_id": fitting["duty_id"],
            "kind": "internal_fitting_relative_pose", "beam_to_post_relative_rotation_vector_rad": rotation_vector.tolist(),
            "beam_to_post_relative_rotation_norm_rad": float(np.linalg.norm(rotation_vector)),
            "objective_relative_port_translation_in_beam_pose_mm": objective_translation.tolist(),
            "objective_relative_port_translation_norm_mm": float(np.linalg.norm(objective_translation)),
            "individual_flat_leg_heel_curvature_or_actual_bend_radius_recovered": False})
    bearings, captures = [], []
    cache_roles = {r["id"]: r for r in cache["parts"]}
    for shaft in shafts:
        if shaft["axis_id"] not in selected_axes:
            continue
        origin, direction = shaft["point"], shaft["basis"][0]
        for i, surface in enumerate(shaft["surfaces"]):
            a, b = surface["interval_mm"]
            for quad, xi in enumerate((-1/np.sqrt(3.), 1/np.sqrt(3.))):
                point = origin+direction*(.5*(a+b)+.5*(b-a)*xi)
                bearings.append(relative(shaft["axis_id"]+f"/bearing-{i}-{quad}", mapping, q, shaft["body"], surface["host"],
                    point, point, direction, flange2=surface.get("flange"), axis_id=shaft["axis_id"],
                    kind="common_shaft_bearing", radial_gap_mm=.5*(shaft["bore_diameter_mm"]-shaft["diameter_mm"]),
                    gauge_independent_rotation_metric="own_director_relative_angle_rad is shaft-axis tilt"))
        for end in shaft["ends"]:
            p1, p2 = origin+direction*end["pressure_face_s_mm"], origin+direction*end["support_s_mm"]
            washer = cache_roles[end["washer_id"]]
            widths = np.diff(np.asarray(washer["bounds_xyz_mm"]), axis=1).ravel()
            component = int(np.argmin(abs(direction)))
            od = float((widths[component]-end["own_washer_thickness_mm"]*abs(direction[component])) / np.sqrt(1-direction[component]**2))
            row = relative(shaft["axis_id"]+"/"+end["end"]+"-capture", mapping, q, shaft["body"], end["host"], p1, p2,
                end["direction_on_shaft_xyz"], flange2=end.get("flange"), axis_id=shaft["axis_id"], kind="own_washer_capture",
                occupied_washer_outer_diameter_mm=od, occupied_washer_thickness_mm=end["own_washer_thickness_mm"],
                actual_washer_rotation_contact_pressure_or_seating_resolved=False,
                gauge_independent_rotation_metric="own_director_relative_angle_rad is shaft/host normal tilt")
            row["occupied_diameter_times_sin_relative_axis_tilt_mm"] = od*np.sin(row["own_director_relative_angle_rad"])
            captures.append(row)
    panel_rows = []
    selected_receivers = {fitting_by_id[name][key] for name in selected for key in ("beam", "post")}
    thickness = {r["panel"]: r["panel_thickness_mm"] for r in integrated["panel_machining"]["outlines"]}
    for screw in layout["screw_axes"]:
        if screw["receiver"] not in selected_receivers:
            continue
        outward = np.asarray(metadata[screw["panel"]]["local_axes_columns_xyz"])[:, 2]
        point = np.asarray(screw["origin_xyz_mm"])-outward*thickness[screw["panel"]]/2
        panel_rows.append(relative(screw["axis_id"], mapping, q, screw["panel"], screw["receiver"], point, point, outward,
            kind="Hillman_panel_point", current_actions_or_actual_Hillman_response_inferred=False))
    timber_rows, pair_summaries = [], []
    for patch in proof["patches"]:
        own = []
        bounds = np.asarray(patch["trimmed_region_geometry"]["bounds_xyz_mm"]).reshape(3, 2)
        normal = np.asarray(patch["normal_from_second_to_first_xyz"])
        tangential_axes = np.flatnonzero(abs(normal) < .5)
        extents = (bounds[:, 1]-bounds[:, 0])[tangential_axes]
        for cell in patch["cells"]:
            row = relative(cell["id"], mapping, q, patch["first"], patch["second"], cell["point_xyz_mm"], cell["point_xyz_mm"], normal,
                kind="timber_face_contact", patch_id=patch["id"], cell_area_mm2=cell["area_mm2"])
            row["linear_tangent_motion_in_25mm_cells"] = row["linear_tangent_motion_norm_mm"]/25.
            row["finite_tangent_motion_in_25mm_cells"] = row["finite_arm_tangent_motion_norm_mm"]/25.
            own.append(row)
        timber_rows.extend(own)
        witnesses = max_summary(own)
        pair_summaries.append({"patch_id": patch["id"], "first": patch["first"], "second": patch["second"],
            "reference_overlap_area_mm2": patch["area_mm2"], "reference_tangential_world_axis_indices": tangential_axes.tolist(),
            "reference_overlap_bounding_extents_mm": extents.tolist(), "cell_size_mm": proof["method"]["cell_size_mm"],
            "cell_count": len(own), "witnesses": witnesses,
            "worst_linear_slide_over_minimum_overlap_bounding_extent": witnesses["linear_tangent_motion_norm_mm"]["linear_tangent_motion_norm_mm"]/float(min(extents)),
            "finite_current_trimmed_footprint_overlap_established": False,
            "footprint_limit": "same-cell point/director diagnostics and source overlap extents; current curved/trimmed face projection, holes and area overlap not recovered"})
    return {"state_id": field["state_id"], "counts": field["counts"], "diagnostic_q_sha256": canonical(field["response"]["diagnostic_last_q"]),
        "diagnostic_current_coordinate_map_sha256": canonical(field["linear_timber_coordinate_map"]),
        "pure_reconstructed_map_sha256": canonical(mapping), "recorded_base_shaft_dof_start": shaft_offset,
        "added_zero_gauge_coordinates_are_only_pose_facade_not_response": 70,
        "representative_flange_contacts": flange_rows, "representative_fitting_receiver_ports": attachment_rows,
        "representative_internal_fitting_pose": fitting_internal, "representative_shaft_bearing_ports": bearings,
        "representative_own_washer_captures": captures, "representative_panel_receiver_points": panel_rows,
        "all_six_timber_pair_summaries": pair_summaries, "all272_timber_cell_motions": timber_rows,
        "representative_worst": {"flanges": max_summary(flange_rows), "bearings": max_summary(bearings),
            "captures": max_summary(captures), "panels": max_summary(panel_rows)},
        "relative_rotations_are_local_while_global_q_remains_unaccepted": True}


def main():
    target = OUT/"result-v4.json"
    if target.exists():
        raise FileExistsError("preserve existing applicability evidence")
    config = json.loads((OUT/"input-v4.json").read_text())
    verify(config["source_sha256"])
    read = lambda key: json.loads((ROOT/config[key]).read_text())
    layout, unit, cache, metadata, assessment, integrated, proof = (read(key) for key in
        ("layout", "timber_unit_geometry", "geometry_cache", "panel_metadata", "panel_assessment", "integrated_geometry", "timber_face_proof"))
    shafts = shaft_inputs(layout, unit, cache)
    results = []
    for source in config["cold_diagnostic_sources"]:
        field = json.loads((ROOT/source["path"]).read_text())
        verify(field["source_sha256"])
        q = field["response"]["diagnostic_last_q"]
        if (field["state_id"] != source["state_id"] or canonical(q) != source["q_sha256"]
                or canonical(field) != source["canonical_field_sha256"] or sha(ROOT/source["path"]) != source["raw_sha256"]):
            raise ValueError("cold source/q/state differs from the recorded ledger identity")
        if (field["response"]["converged"] is not False or field["usable_conditional_actions"] is not False
                or "q" in field["response"] or any(field["release"].values())
                or field["counts"]["structural_bodies"] != 132):
            raise ValueError("diagnostic must retain its complete unaccepted cold scope")
        results.append(evaluate(field, config, layout, shafts, metadata, assessment, integrated, proof, cache))
        verify(field["source_sha256"])
    verify(config["source_sha256"])
    result = {"schema": "thin_bolted_unaccepted_cold_q_local_applicability/v1",
        "status": "DIAGNOSTIC_POSE_APPLICABILITY_ONLY_NO_ACCEPTED_ACTIONS", "source_sha256": config["source_sha256"] | {
            str((OUT/"input-v4.json").relative_to(ROOT)): sha(OUT/"input-v4.json"), str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
        "source_bytes_and_q_identity_checked_before_and_after": True, "known_answer_checks": fixtures(),
        "results": results, "method": config["method"], "limits": config["limits"],
        "K_CAD_native_global_solve_force_strength_or_stability_operation": False,
        "release": {k: False for k in ("candidate_accepted", "complete_joint_acceptance", "capacity_established", "fabrication_released", "structural_released", "climbing_released")}}
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"input_sha256": sha(OUT/"input-v4.json"), "script_sha256": sha(Path(__file__)), "result_sha256": sha(target),
        "state_ids": [r["state_id"] for r in results], "bytes": target.stat().st_size}, indent=2))


if __name__ == "__main__":
    main()
