"""Same-material-cut timber recovery from an admitted finite CURRENT state.

The finite exported point forces and spatial couples are used at their own
current positions. Material membership is selected by reference station.
No old force field, current-point/reference-point alias, CAD or solve is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

from scripts import thin_bolted_timber_demand_checks as references
from scripts import thin_bolted_timber_resistance as unit
from scripts import thin_bolted_timber_section_properties as sections

ROOT, PACKET = unit.ROOT, unit.PACKET
GATE = "scripts/thin_bolted_finite_state_audit.py"
FINITE = "scripts/thin_bolted_finite_frame.py"
FINITE_SHA = "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588"
RECESS = PACKET / "timber-leg-recess-sections-v4.json"
RECESS_SHA = "94fd730a72bdb93efc5d654913a162bb9a9715af342e91ebb11e873006969574"
REFERENCES_SHA = "1be05e74563d2cc7a7ea5437aa4ff7217e62f8314f9fe011ff273d201f755e20"
SECTIONS_SHA = "398e883849dfd83a34aeb60b5ac0b5d50f57ffa9b01f3f2427e341725749a80a"


def current_cut_frame(mapping: dict, member: str, reference_point: list,
                      reference_grain: list, q: list, *, reference_centroid: list | None = None) -> dict:
    """Transport the cut datum and material directors through finite kinematics."""
    from scripts.thin_bolted_finite_frame import current_pose_from_map

    u, v, grain = sections.section_basis(reference_grain)
    basis = []
    current = None
    for director in (u, v, grain):
        pose = current_pose_from_map(mapping, member, reference_point, q, reference_director=director)
        current = np.asarray(pose["position_xyz_mm"], dtype=float)
        basis.append(np.asarray(pose["current_vector_xyz"], dtype=float))
    rotation = np.asarray(basis).T @ np.asarray((u, v, grain))
    unit.require(np.linalg.norm(rotation.T @ rotation - np.eye(3)) < 1e-8
                 and abs(np.linalg.det(rotation) - 1.) < 1e-8, "current material section frame is not a proper rotation")
    centroid = None
    if reference_centroid is not None:
        unit.require(abs(unit.dot(grain, reference_centroid) - unit.dot(grain, reference_point)) < 1e-5,
                     "reference net centroid does not belong to this material cut")
        centroid = current_pose_from_map(mapping, member, reference_centroid, q)["position_xyz_mm"].tolist()
    return {"reference_cut_point_xyz_mm": reference_point, "current_cut_point_xyz_mm": current.tolist(),
            "reference_basis_u_v_grain_xyz": [u, v, grain],
            "current_basis_u_v_grain_xyz": [vector.tolist() for vector in basis],
            "reference_to_current_rotation_columns_xyz": rotation.tolist(),
            "current_finished_section_centroid_xyz_mm": centroid,
            "cross_section_transport_model": "rigid material section under the saved geodesic director and linear centerline interpolation"}


def own_current_actions(demand: dict) -> dict:
    """Collect actual own-side points and physical free couples for each host."""
    identity = tuple(demand[key] for key in ("state_id", "case_id", "accessory_placement"))
    result = defaultdict(list)
    for row in demand["finite_interaction_actions"]:
        unit.require(tuple(row.get(key) for key in ("state_id", "case_id", "accessory_placement")) == identity,
                     "finite interaction mixes admitted state/case/accessory")
        first_force = unit.vector(row["force_on_first_xyz_n"], "finite first force")
        second_force = unit.vector(row["force_on_second_xyz_n"], "finite second force")
        unit.require(math.dist(first_force, [-x for x in second_force]) < 1e-7, "finite own force dual differs")
        for side in ("first", "second"):
            if row[side] == "floor":
                continue
            result[row[side]].append({"id": row["id"] + "/" + side,
                "kind": row["kind"], "reference_point_xyz_mm": row[f"reference_{side}_point_xyz_mm"],
                "current_point_xyz_mm": row[f"point_on_{side}_xyz_mm"],
                "force_xyz_n": row[f"force_on_{side}_xyz_n"],
                "free_spatial_moment_xyz_nmm": row[f"moment_on_{side}_at_current_point_xyz_nmm"],
                "source_action_id": row["id"], "source_action_side": side})
    for row in demand["finite_body_applied_loads"]:
        unit.require(tuple(row.get(key) for key in ("state_id", "case_id", "accessory_placement")) == identity,
                     "finite load mixes admitted state/case/accessory")
        result[row["body"]].append({"id": row["id"], "kind": "body_load",
            "reference_point_xyz_mm": row["reference_point_xyz_mm"],
            "current_point_xyz_mm": row["current_point_xyz_mm"], "force_xyz_n": row["force_xyz_n"],
            "free_spatial_moment_xyz_nmm": row["free_spatial_moment_xyz_nmm"],
            "gravity_model": row.get("gravity_model"), "source_station_mm": row.get("source_station_mm")})
    return result


def current_cut_wrench(actions: list[dict], reference_grain: list, reference_station: float,
                       frame: dict) -> dict:
    """Equilibrate the lower material portion using CURRENT force arms.

    The saved2Gauss gravity ports are discrete applied loads in this finite
    model. They are not replaced by a continuous old affine force integral.
    A load exactly on the cut belongs to the upper portion by explicit rule.
    """
    force, moment, selected = np.zeros(3), np.zeros(3), []
    cut = np.asarray(frame["current_cut_point_xyz_mm"])
    for row in actions:
        reference = unit.vector(row["reference_point_xyz_mm"], "material load point")
        if unit.dot(reference_grain, reference) >= reference_station:
            continue
        point = np.asarray(unit.vector(row["current_point_xyz_mm"], "current own load point"))
        action = np.asarray(unit.vector(row["force_xyz_n"], "current own force"))
        free = np.asarray(unit.vector(row["free_spatial_moment_xyz_nmm"], "current own free couple"))
        force += action
        moment += np.cross(point - cut, action) + free
        selected.append(row["id"])
    force, moment = -force, -moment
    basis = np.asarray(frame["current_basis_u_v_grain_xyz"])
    local_force, local_moment = basis @ force, basis @ moment
    return {"reference_material_station_global_grain_projection_mm": reference_station,
            **frame, "force_on_lower_material_portion_xyz_n": force.tolist(),
            "moment_on_lower_material_portion_about_current_cut_xyz_nmm": moment.tolist(),
            "local_Vu_Vv_N_TensionPositive_n": local_force.tolist(),
            "local_Mu_Mv_T_nmm": local_moment.tolist(), "own_lower_material_action_ids": selected,
            "current_point_projection_used_to_select_material_side": False,
            "old_affine_continuous_force_integral_substituted": False}


def centroid_components(wrench: dict, properties: dict) -> dict:
    """Use reused exact net centroid/cross inertia in the current material frame."""
    centroid = wrench["current_finished_section_centroid_xyz_mm"]
    unit.require(centroid is not None, "exact current finished centroid is required")
    force = np.asarray(wrench["force_on_lower_material_portion_xyz_n"])
    moment = np.asarray(wrench["moment_on_lower_material_portion_about_current_cut_xyz_nmm"])
    moment -= np.cross(np.asarray(centroid) - np.asarray(wrench["current_cut_point_xyz_mm"]), force)
    basis = np.asarray(wrench["current_basis_u_v_grain_xyz"])
    local = basis @ moment
    matrix = np.asarray(properties["centroidal_area_moment_matrix_uv_mm4"])
    unit.require(math.dist(np.asarray(properties["basis_u_v_grain_xyz"]).ravel(),
                           np.asarray(wrench["reference_basis_u_v_grain_xyz"]).ravel()) < 1e-8,
                 "net inertia basis differs from current transported material basis")
    unit.require(matrix.shape == (2, 2) and np.linalg.det(matrix) > 0., "positive net centroidal inertia required")
    beta = np.linalg.solve(matrix, [-local[1], local[0]])
    mean = wrench["local_Vu_Vv_N_TensionPositive_n"][2] / properties["finished_area_mm2"]
    return {"current_finished_section_centroid_xyz_mm": centroid,
            "moment_about_current_finished_centroid_xyz_nmm": moment.tolist(),
            "net_centroidal_area_moment_matrix_uv_mm4": matrix.tolist(),
            "mean_axial_normal_stress_n_mm2": mean, "linear_normal_stress_gradient_uv_n_mm3": beta.tolist(),
            "actual_trimmed_boundary_normal_stress_extrema": None,
            "complete_adjusted_NDS_member_resistance_or_utilization": None,
            "limits": "Reference material section properties are rigidly transported; exact directional material-boundary extrema, shear/torsion/fracture and stability are separate."}


def current_wood_bearing_wrenches(demand: dict, full: dict, layout: dict) -> list[dict]:
    """Own82 actual span resultants at current host datums/directors."""
    axes = {row["id"]: row for row in layout["installed_axes"]}
    interactions = demand["finite_interaction_actions"]
    mapping, q = demand["finite_kinematic_map"], demand["response"]["q"]
    from scripts.thin_bolted_finite_frame import current_pose_from_map

    output = []
    for receiver in full["receiver_boundary_geometry"]:
        member, axis_id = receiver["member"], receiver["axis_id"]
        axis, grain = axes[axis_id], receiver["grain_axis_xyz"]
        intervals = receiver["finished_full_wall_intervals_from_axis_point_mm"]
        unit.require(len(intervals) == 1, "current82span method requires one issued full-wall interval per wood host")
        reference_point = references.add(axis["point"], references.scale(unit.unit(axis["direction"]), .5 * sum(intervals[0])))
        pose = current_pose_from_map(mapping, member, reference_point, q, reference_director=grain)
        current_point, current_grain = pose["position_xyz_mm"], pose["current_vector_xyz"]
        current_bore = current_pose_from_map(mapping, member, reference_point, q,
            reference_director=axis["direction"])["current_vector_xyz"]
        own = [row for row in interactions if row["kind"] in ("common_shaft_bearing", "shaft_end_capture")
               and row["second"] == member and row["source_descriptor"]["axis_id"] == axis_id]
        bearing = [row for row in own if row["kind"] == "common_shaft_bearing"]
        unit.require(len(bearing) == 2, "all own two quadrature bearing ports required")
        force, moment = np.zeros(3), np.zeros(3)
        points = []
        for row in own:
            action = np.asarray(row["force_on_second_xyz_n"])
            point = np.asarray(row["point_on_second_xyz_mm"])
            free = np.asarray(row["moment_on_second_at_current_point_xyz_nmm"])
            force += action
            moment += np.cross(point - current_point, action) + free
            if row["kind"] == "common_shaft_bearing":
                source = row["source_descriptor"]
                reference = row["reference_second_point_xyz_mm"]
                local_grain = current_pose_from_map(mapping, member, reference, q, reference_director=grain)["current_vector_xyz"].tolist()
                local_bore = row["current_director_xyz"]
                resolved = unit.resolved_action(action.tolist(), local_grain, local_bore)
                parameters = []
                for fraction in (1., .8):
                    diameter = axis["diameter_mm"] * fraction
                    theta = resolved["load_to_grain_degrees"]
                    parameters.append({"diameter_fraction_scenario": fraction, "diameter_mm": diameter,
                        "actual_D_or_Dr_adopted": False,
                        "average_foundation_patch_pressure_n_mm2": resolved["lateral_n"] / (diameter * source["weight_length_mm"]),
                        "NDS_Fe_theta_psi": None if theta is None else unit.dfl_dowel_bearing_psi(diameter / 25.4, theta),
                        "adjusted_patch_or_connection_utilization": None})
                points.append({"id": row["id"], "current_point_xyz_mm": point.tolist(),
                    "force_on_wood_xyz_n": action.tolist(), "free_spatial_couple_on_wood_xyz_nmm": free.tolist(),
                    "current_material_grain_xyz": local_grain, "current_owned_bore_director_xyz": local_bore,
                    **resolved, "body_root_parameter_scenarios": parameters})
        resolved = unit.resolved_action(force.tolist(), current_grain.tolist(), current_bore.tolist())
        output.append({"state_id": demand["state_id"], "case_id": demand["case_id"],
            "accessory_placement": demand["accessory_placement"], "axis_id": axis_id, "member": member,
            "reference_finished_full_wall_interval_mm": intervals[0],
            "reference_host_midspan_point_xyz_mm": reference_point, "current_host_midspan_point_xyz_mm": current_point.tolist(),
            "current_material_grain_xyz": current_grain.tolist(), "current_owned_bore_director_xyz": current_bore.tolist(),
            "force_on_wood_xyz_n": force.tolist(), "moment_on_wood_about_current_datum_xyz_nmm": moment.tolist(),
            "own_current_bearing_points": points, "own_capture_ids": [row["id"] for row in own if row["kind"] == "shaft_end_capture"],
            "resolved_current_resultant": resolved,
            "reference_material_signed_boundary_diagnostics": references.signed_boundary_diagnostics(resolved, receiver, axis["diameter_mm"]),
            "reference_boundary_distances_are_exact_current_deformed_clearances": False,
            "general_distributed_NDS_yield_group_splitting_capacity": None})
    unit.require(len(output) == 82, "all82 current wood bearing hosts required")
    return output


def current_capture_annuli(demand: dict, packet: dict) -> list[dict]:
    """Retain each own finite capture force/couple; wood annulus is separate."""
    indexed = {(row["axis_id"], row["role"]): row for row in packet["washer_wood_interface_references"]}
    output = []
    for row in demand["finite_interaction_actions"]:
        if row["kind"] != "shaft_end_capture":
            continue
        source = row["source_descriptor"]
        axis_id, role = source["axis_id"], source["end"]["end"] + "_washer"
        reference = indexed[(axis_id, role)]
        value = reference["ideal_full_contact_wood_annulus_reference_n"]
        unit.require(row["axial_scalar_force_n"] >= 0., "own finite compression scalar must be nonnegative")
        output.append({"state_id": demand["state_id"], "case_id": demand["case_id"],
            "accessory_placement": demand["accessory_placement"], "axis_id": axis_id, "role": role,
            "own_capture_id": row["id"], "actual_support_host": row["second"],
            "current_shaft_pressure_point_xyz_mm": row["point_on_first_xyz_mm"],
            "current_host_support_point_xyz_mm": row["point_on_second_xyz_mm"],
            "model_own_capture_compression_n": row["axial_scalar_force_n"],
            "own_current_force_on_host_xyz_n": row["force_on_second_xyz_n"],
            "own_current_director_spatial_couple_on_host_xyz_nmm": row["moment_on_second_at_current_point_xyz_nmm"],
            "reference_support_material": reference["support_material"],
            "ideal_Fc_perp_wood_annulus_reference_n": value,
            "own_model_capture_over_ideal_annulus_component_ratio": None if value is None else row["axial_scalar_force_n"] / value,
            "duration_increase_applied_to_Fc_perp": False,
            "actual_pressure_prying_metal_spreading_or_head_nut_thread_capacity": None})
    return output


def recover_saved_cuts(demand: dict, full: dict, exact_properties: dict) -> list[dict]:
    """Recover complete current six-vectors at retained material stations."""
    mapping, q = demand["finite_kinematic_map"], demand["response"]["q"]
    actions = own_current_actions(demand)
    rows = []
    live = any(row["id"].startswith("climber/") for row in demand["finite_body_applied_loads"])
    for member in full["finished_member_sections"]:
        name, grain = member["member"], member["grain_axis_xyz"]
        body = mapping["mechanical_bodies"][name]
        unit.require(body["kind"] == "timber" and math.dist(body["reference_axis_xyz"], grain) < 1e-8,
                     "finite material member/grain differs from section inventory")
        source_start = body["reference_start_xyz_mm"]
        low = unit.dot(grain, source_start) + body["reference_stations_mm"][0]
        high = unit.dot(grain, source_start) + body["reference_stations_mm"][-1]
        witnesses = []
        for saved in member["sampled_sections"]:
            station = saved["station_global_grain_projection_mm"]
            if not low - 1e-5 <= station <= high + 1e-5:
                continue
            point = references.add(source_start, references.scale(grain, station - unit.dot(grain, source_start)))
            props = exact_properties.get((name, station))
            current = current_cut_frame(mapping, name, point, grain, q,
                reference_centroid=props["centroid_xyz_mm"] if props else None)
            wrench = current_cut_wrench(actions[name], grain, station, current)
            axial, area = wrench["local_Vu_Vv_N_TensionPositive_n"][2], saved["finished_area_mm2"]
            witness = {"state_id": demand["state_id"], "case_id": demand["case_id"],
                "accessory_placement": demand["accessory_placement"], "member": name, **wrench,
                "finished_reference_material_area_mm2": area,
                "average_tension_reference": references.duration_component_sensitivity(
                    area * 575. * unit.N_PER_LBF / 25.4**2, max(0., axial), case_id=demand["case_id"], live_load_present=live),
                "average_compression_reference": references.duration_component_sensitivity(
                    area * 1350. * unit.N_PER_LBF / 25.4**2, max(0., -axial), case_id=demand["case_id"], live_load_present=live),
                "current_net_centroid_and_inertia_components": centroid_components(wrench, props) if props else None,
                "complete_member_or_joint_acceptance": False}
            witnesses.append(witness)
        unit.require(witnesses, "no retained material cuts intersect current mapped member")
        selectors = {"maximum_average_tension_witness": lambda w: w["average_tension_reference"]["CD1_same_state_component_ratio"],
            "maximum_average_compression_witness": lambda w: w["average_compression_reference"]["CD1_same_state_component_ratio"],
            "maximum_cut_moment_witness": lambda w: math.hypot(*w["local_Mu_Mv_T_nmm"][:2]),
            "maximum_shear_witness": lambda w: math.hypot(*w["local_Vu_Vv_N_TensionPositive_n"][:2])}
        rows.append({"member": name, "saved_material_cut_count": len(witnesses),
            **{key: max(witnesses, key=selector) for key, selector in selectors.items()},
            "exact_net_property_cut_witnesses": [w for w in witnesses if w["current_net_centroid_and_inertia_components"] is not None],
            "separate_component_extrema_combined": False, "continuous_maximum_or_complete_member_resistance": False})
    return rows


def require_admission_receipt(admission: dict, demand: dict, field_sha256: str, admission_sha256: str) -> None:
    """Require a fresh finite receipt for the exact immutable bytes/state."""
    unit.require(admission.get("independent_finite_current_support_load_and_equilibrium_checks_pass") is True,
                 "new finite CURRENT admission gate fails")
    unit.require(admission.get("schema") == "thin_bolted_independent_finite_admission/v1"
                 and admission.get("field_sha256") == field_sha256
                 and admission.get("source_sha256", {}).get(GATE) == admission_sha256
                 and all(admission.get(key) == demand[key] for key in ("state_id", "case_id", "accessory_placement")),
                 "finite admission receipt does not bind the exact source/payload/state")


def consume(field_path: Path, expected_sha256: str, *, admission_sha256: str) -> dict:
    """Admission is exclusively through the NEW finite-current state gate."""
    unit.require(isinstance(admission_sha256, str) and len(admission_sha256) == 64
                 and all(char in "0123456789abcdef" for char in admission_sha256),
                 "mandatory explicit reviewed finite admission SHA256 is malformed")
    for path, expected in ((ROOT / GATE, admission_sha256), (ROOT / FINITE, FINITE_SHA),
                           (Path(references.__file__), REFERENCES_SHA), (Path(sections.__file__), SECTIONS_SHA)):
        unit.require(unit.sha(path) == expected, "frozen finite timber dependency differs")
    payload = field_path.read_bytes()
    unit.require(hashlib.sha256(payload).hexdigest() == expected_sha256, "released finite field differs")
    demand = json.loads(payload)
    from scripts.thin_bolted_finite_state_audit import audit_finite_state

    admission = audit_finite_state(payload)
    require_admission_receipt(admission, demand, expected_sha256, admission_sha256)
    packet, _, layout = references.read_unit()
    detail = packet["reproducible_detail_artifact"]
    unit.require(unit.sha(ROOT / detail["path"]) == detail["sha256"], "preserved material section inventory differs")
    full = json.loads((ROOT / detail["path"]).read_text())["finished_geometry_queries"]
    property_bytes = RECESS.read_bytes()
    unit.require(hashlib.sha256(property_bytes).hexdigest() == RECESS_SHA, "parent-queried exact net properties differ")
    properties = json.loads(property_bytes)
    unit.require(properties["state_id"] is None and properties["candidate"] == unit.CANDIDATE,
                 "net properties must be issued geometry only, without old force state")
    for relative, expected in properties["source_sha256"].items():
        unit.require(unit.sha(ROOT / relative) == expected, "reused exact section property source differs")
    indexed = {(row["member"], row["station_global_grain_projection_mm"]): row for row in properties["finished_sections"]}
    cuts = recover_saved_cuts(demand, full, indexed)
    wood = current_wood_bearing_wrenches(demand, full, layout)
    captures = current_capture_annuli(demand, packet)
    unit.require(len(captures) == 140, "all140 own finite captures required")
    receivers = {(row["axis_id"], row["member"]): row for row in full["receiver_boundary_geometry"]}
    windows = [references.standard_thread_window(axis, receivers) for axis in layout["installed_axes"]]
    duration = references.read_duration_sources()
    pins = {str(path.resolve().relative_to(ROOT)): unit.sha(path) for path in
        (field_path, Path(__file__), ROOT / GATE, ROOT / FINITE, Path(references.__file__), Path(sections.__file__),
         references.UNIT, ROOT / detail["path"], RECESS)}
    pins.update({row["path"]: row["sha256"] for row in duration["authenticated_primary_sources"]})
    pins[str((references.DURATION_CACHE / "source-bounds.json").relative_to(ROOT))] = unit.sha(references.DURATION_CACHE / "source-bounds.json")
    unit.require(unit.sha(RECESS) == RECESS_SHA, "reused exact section properties changed during finite consumption")
    unit.require(unit.sha(field_path) == expected_sha256, "released finite field changed during timber consumption")
    unit.require(unit.sha(ROOT / GATE) == admission_sha256, "reviewed finite admission source changed during consumption")
    return {"schema": "thin_bolted_finite_timber_components/v1", "candidate": unit.CANDIDATE,
        "state_id": demand["state_id"], "case_id": demand["case_id"], "accessory_placement": demand["accessory_placement"],
        "parameters": demand["parameters"], "source_sha256": pins,
        "finite_producer_source_sha256": demand["source_sha256"],
        "independent_finite_current_admission": admission, "complete_current_cut_witnesses": cuts,
        "exact_finite_schema_source_state_payload_receipt_authenticated": True,
        "current82own_wood_bearing_wrenches": wood, "current70reference_material_thread_windows": windows,
        "current140own_capture_and_annulus_references": captures,
        "duration_source": duration, "CAD_or_native_execution": False,
        "old_reference_state_forces_or_gate_relabelled": False, "all18_completion_gates_open": True,
        "general_distributed_yield_group_splitting_shear_stability_complete": False,
        "counts": {"current_wood_bearing_hosts": len(wood), "own_captures": len(captures),
            "physical_shaft_reference_thread_windows": len(windows),
            "retained_material_cuts_recovered": sum(row["saved_material_cut_count"] for row in cuts),
            "exact_centroid_inertia_current_cut_witnesses": sum(len(row["exact_net_property_cut_witnesses"]) for row in cuts)},
        "limits": ["Same-cut recovery equilibrates the exported finite discrete load model, including its material2Gauss gravity ports; it does not establish a continuous maximum or refinement bound.",
            "Finite current points and director-induced spatial couples are preserved; no equal/opposite classic yield pattern is inferred.",
            "Finished reference-material A/I is rigidly transported where available. Gross beam stiffness remains an unbounded scenario; no void/recess local stiffness, pressure or fracture acceptance follows.",
            "ActualDr/Fyb/body-runout/property conformity, formal oblique end/edge/group classification and connected fracture/splitting remain unadopted.",
            "Shear/torsion/local fracture/stability, actual washer pressure/prying/head/nut/thread resistance and complete case coverage remain open."],
        "complete_joint_acceptance": False, "release": unit.RELEASE}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--field-sha256", required=True)
    parser.add_argument("--admission-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    unit.require(not args.out.exists(), "preserve distinct finite timber evidence")
    result = consume(args.field, args.field_sha256, admission_sha256=args.admission_sha256)
    args.out.write_text(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
