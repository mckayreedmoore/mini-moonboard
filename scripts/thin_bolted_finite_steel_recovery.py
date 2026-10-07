"""Pure current-state steel/shaft recovery from finite physical JSON actions.

No global assembly, stiffness, CAD or solve is used. Reference material
stations choose the side of a cut; current points/bases transport all wrenches.
"""

from __future__ import annotations

import copy
import hashlib
import math
from pathlib import Path

import numpy as np

from scripts import thin_bolted_common_shaft_steel as common
from scripts import thin_bolted_flange_torsion as torsion
from scripts import thin_bolted_steel_resistance as steel

ROOT, PACKET = steel.ROOT, steel.PACKET
LOADED_RECOVERY_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
FINITE_SHA = "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588"
REUSED_SOURCES = {
    "scripts/thin_bolted_common_shaft_steel.py": "4b28f7a055c50dc127569b7df387f8e8d973f74080d2937ceb5db356a89d9952",
    "scripts/thin_bolted_flange_torsion.py": "48e3181f65772cb2d21be6687a011eaeba6a35491b6299cd179759f66ffc6871",
    "scripts/thin_bolted_steel_resistance.py": "5a41c7d4a46bf1857e4c756fb35c12cc4253d2fd74f49de01a95c275a8c80602",
}


def source_pins():
    """Public writer binding for frozen reuse and this loaded recovery source."""
    from scripts.thin_bolted_finite_frame import source_pins as finite_source_pins

    pins = finite_source_pins()
    if pins["scripts/thin_bolted_finite_frame.py"] != FINITE_SHA:
        raise ValueError("current finite map reader differs from its frozen source")
    pins.update(REUSED_SOURCES)
    pins["scripts/thin_bolted_finite_steel_recovery.py"] = LOADED_RECOVERY_SHA256
    if any(hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != digest for path, digest in pins.items()):
        raise ValueError("current recovery or frozen reused source changed")
    return pins


def state_fields(export):
    return {key: export[key] for key in ("state_id", "case_id", "accessory_placement")}


def current_pose(mapping, body, point, q, *, flange=None, reference_director=None):
    from scripts.thin_bolted_finite_frame import current_pose_from_map

    return current_pose_from_map(mapping, body, point, q, flange=flange, reference_director=reference_director)


def validate_labels(export):
    expected = state_fields(export)
    for table in ("finite_interaction_actions", "finite_body_applied_loads"):
        rows = export[table]
        if len({row["id"] for row in rows}) != len(rows):
            raise ValueError("duplicate finite physical action/load identity")
        for row in rows:
            if any(row.get(key) != value for key, value in expected.items()):
                raise ValueError("finite physical actions mix or omit state/load identity")


def mapped_state(export, q):
    """Use exactly the admitted coordinate vector when the writer supplies it."""
    q = common.vector(q, export["finite_kinematic_map"]["ndof"])
    if "q" in export.get("response", {}):
        saved = common.vector(export["response"]["q"], len(q))
        if not np.array_equal(saved, q):
            raise ValueError("recovery coordinates differ from the supplied finite response")
    return q


def current_metal_gravity(export, q, shaft_specs, *, pose=current_pose):
    """Authenticate every exact role and replay its own current point/force."""
    expected = {"physical-bolt-metal/"+role["id"]: (shaft, role)
                for shaft in shaft_specs for role in shaft["metal_roles"]}
    rows = [r for r in export["finite_body_applied_loads"] if r["id"].startswith("physical-bolt-metal/")]
    saved = {row["id"]: row for row in rows}
    if len(saved) != len(rows) or set(saved) != set(expected):
        raise ValueError("complete exact own metal-role gravity census required")
    mapping = export["finite_kinematic_map"]
    for identity, (shaft, role) in expected.items():
        row = saved[identity]
        reference = common.vector(role["center_of_mass_xyz_mm"])
        current = pose(mapping, shaft["body"], reference, q)["position_xyz_mm"]
        force = np.array([0., 0., -role["volume_mm3"]*7850e-9*9.80665])
        if (row["body"] != shaft["body"] or row.get("source_load_id") != identity
                or np.linalg.norm(common.vector(row["reference_point_xyz_mm"])-reference) > 1e-5
                or np.linalg.norm(common.vector(row["current_point_xyz_mm"])-current) > 1e-5
                or np.linalg.norm(common.vector(row["force_xyz_n"])-force) > 1e-7
                or np.linalg.norm(common.vector(row["free_spatial_moment_xyz_nmm"])) > 1e-10):
            raise ValueError("own metal gravity role, current arm or force differs from exact source")
    return rows


def current_shaft_cuts(export, q, shaft_specs, *, pose=current_pose):
    """Lower material-part equilibrium in each current local director basis."""
    mapping, state = export["finite_kinematic_map"], state_fields(export)
    scale = export["parameters"]["shaft_diameter_scale"]
    if not isinstance(scale, (int, float)) or not math.isfinite(scale) or scale <= 0:
        raise ValueError("positive finite unadopted elastic circle scale required")
    gravity = current_metal_gravity(export, q, shaft_specs, pose=pose)
    actions = [r for r in export["finite_interaction_actions"] if r["kind"] in ("common_shaft_bearing", "shaft_end_capture")]
    result = []
    for shaft in shaft_specs:
        origin, axis = common.vector(shaft["point"]), common.vector(shaft["basis"][0])
        loads = [{"id": row["id"], "reference": row["reference_point_xyz_mm"],
                  "point": row["current_point_xyz_mm"], "force": row["force_xyz_n"],
                  "moment": row["free_spatial_moment_xyz_nmm"]} for row in gravity if row["body"] == shaft["body"]]
        loads += [{"id": row["id"], "reference": row["reference_first_point_xyz_mm"],
                   "point": row["point_on_first_xyz_mm"], "force": row["force_on_first_xyz_n"],
                   "moment": row["moment_on_first_at_current_point_xyz_nmm"]}
                  for row in actions if row["first"] == shaft["body"]]
        mesh = common.vector(mapping["mechanical_bodies"][shaft["body"]]["reference_stations_mm"],
                             len(mapping["mechanical_bodies"][shaft["body"]]["reference_stations_mm"]))
        low, high = shaft["shaft_interval_mm"]
        if len(mesh) < 2 or np.min(np.diff(mesh)) <= 0 or abs(mesh[0]-low) > 1e-5 or abs(mesh[-1]-high) > 1e-5:
            raise ValueError("current shaft map must cover the exact reference material interval")
        stations = list(mesh)+list(np.linspace(low, high, 33))
        for row in loads:
            row["material_station"] = float((common.vector(row["reference"])-origin) @ axis)
            stations.extend((float(np.clip(row["material_station"]-1e-7, low, high)),
                             float(np.clip(row["material_station"]+1e-7, low, high))))
        cuts = []
        for station in sorted(set(stations)):
            reference = origin + axis*station
            cut_point = common.vector(pose(mapping, shaft["body"], reference, q)["position_xyz_mm"])
            basis = np.array([pose(mapping, shaft["body"], reference, q, reference_director=director)["current_vector_xyz"]
                              for director in shaft["basis"]])
            if np.linalg.norm(basis @ basis.T-np.eye(3)) > 1e-8 or np.linalg.det(basis) < .99999999:
                raise ValueError("current shaft material director basis must be proper orthonormal")
            force, moment = np.zeros(3), np.zeros(3)
            own = []
            for row in loads:
                if row["material_station"] < station:
                    f, m = common.transport_wrench(row["force"], row["moment"], row["point"], cut_point)
                    force -= f; moment -= m; own.append(row["id"])
            cuts.append({**state, "station_from_axis_point_mm": station,
                "reference_material_point_xyz_mm": reference.tolist(), "point_xyz_mm": cut_point.tolist(),
                "current_basis_axis_tangent1_tangent2_xyz": basis.tolist(),
                "local_N_V1_V2_T_M1_M2_n_nmm": np.r_[basis @ force, basis @ moment].tolist(),
                "lower_material_part_physical_load_ids": own})
        result.append({**state, "axis_id": shaft["axis_id"], "body": shaft["body"], "cuts": cuts,
            "reference_material_interval_mm": [low, high], "reference_mesh_stations_mm": mesh.tolist(),
            "elastic_section_diameter_mm": shaft["diameter_mm"]*scale,
            "load_order_is_reference_material_station_not_current_global_projection": True,
            "all_current_force_arms_and_free_spatial_couples_retained": True,
            "physical_end_prying_root_or_delivered_material_verified": False})
    return result


def current_steel_ports(export, q, layout, *, pose=current_pose):
    """Reuse signed aggregation with a distinct current entry for each flange."""
    current_layout = copy.deepcopy(layout)
    mapping = export["finite_kinematic_map"]
    for shaft in current_layout["installed_axes"]:
        for port in shaft["attachments"]:
            port["entry_xyz_mm"] = np.asarray(pose(mapping, port["angle_id"], port["entry_xyz_mm"], q,
                flange=port["flange"])["position_xyz_mm"]).tolist()
    bearings, captures = [], []
    for row in export["finite_interaction_actions"]:
        if row["kind"] not in ("common_shaft_bearing", "shaft_end_capture"):
            continue
        source = row["source_descriptor"]
        normalized = {**state_fields(export), "id": row["id"], "axis_id": source["axis_id"],
            "second": row["second"], "force_on_second_xyz_n": row["force_on_second_xyz_n"],
            "moment_on_second_at_point_xyz_nmm": row["moment_on_second_at_current_point_xyz_nmm"]}
        if row["kind"] == "common_shaft_bearing":
            bearings.append({**normalized, "surface_material": source["surface"]["kind"],
                "flange": source["surface"].get("flange"), "point_xyz_mm": row["point_on_second_xyz_mm"]})
        else:
            captures.append({**normalized, "end": source["end"], "host_support_point_xyz_mm": row["point_on_second_xyz_mm"]})
    ports = common.aggregate_steel_ports(current_layout, bearings, captures)
    return [{**state_fields(export), **port, "entry_is_current_own_flange_pose": True} for port in ports]


def fitting_source_leg_loads(export, q, angle, flange, *, pose=current_pose):
    """Exact derivative of the source mean-two-flange rigid-arm load port."""
    mapping, result = export["finite_kinematic_map"], []
    rows = [row for row in export.get("finite_body_applied_loads", []) if row["body"] == angle]
    if rows and mapping["mechanical_bodies"][angle]["gravity_port"] != "mean of two exact flange rigid-arm ports":
        raise ValueError("fitting leg load recovery requires the exact source mean-port definition")
    for row in rows:
        if np.linalg.norm(common.vector(row["free_spatial_moment_xyz_nmm"])) > 1e-10:
            raise ValueError("a source fitting free couple has no authenticated leg derivative")
        reference = common.vector(row["reference_point_xyz_mm"])
        positions = {part: common.vector(pose(mapping, angle, reference, q, flange=part)["position_xyz_mm"])
                     for part in ("beam", "post")}
        if np.linalg.norm(.5*(positions["beam"]+positions["post"])-common.vector(row["current_point_xyz_mm"])) > 1e-5:
            raise ValueError("source fitting current load point differs from its exact mean port")
        result.append({"id": row["id"]+"/"+flange+"-port-derivative", "source_load_id": row["source_load_id"],
            "point_xyz_mm": positions[flange].tolist(), "force_on_steel_xyz_n": (.5*common.vector(row["force_xyz_n"])).tolist(),
            "moment_on_steel_at_point_xyz_nmm": [0., 0., 0.],
            "model_leg_force_basis": "exact derivative of the mean of the two current flange rigid-arm source load ports",
            "assumed_physical_gravity_equal_sharing": False})
    return result


def current_flange_sections(export, q, layout, ports, *, pose=current_pose):
    """Nominal per-flange material cuts with full current-point spatial wrenches."""
    fittings = {row["angle_id"]: row for row in layout["raw_fittings"]}
    mapping, state, result = export["finite_kinematic_map"], state_fields(export), []
    for port in ports:
        angle, flange = port["angle_id"], port["flange"]
        reference = fittings[angle]
        current = {**reference, "origin_xyz_mm": np.asarray(pose(mapping, angle, reference["origin_xyz_mm"], q,
                                                            flange=flange)["position_xyz_mm"]).tolist()}
        for key in ("u_xyz", "v_xyz", "w_xyz"):
            current[key] = np.asarray(pose(mapping, angle, reference["origin_xyz_mm"], q, flange=flange,
                reference_director=reference[key])["current_vector_xyz"]).tolist()
        loads = [{"point_xyz_mm": port["point_xyz_mm"], "force_on_steel_xyz_n": port["force_on_steel_xyz_n"],
                  "moment_on_steel_at_point_xyz_nmm": port["moment_on_steel_at_point_xyz_nmm"]}]
        loads += [{"point_xyz_mm": row["point_on_first_xyz_mm"], "force_on_steel_xyz_n": row["force_on_first_xyz_n"],
                   "moment_on_steel_at_point_xyz_nmm": row["moment_on_first_at_current_point_xyz_nmm"]}
                  for row in export["finite_interaction_actions"] if row["kind"] == "flange_contact"
                  and row["first"] == angle and row["source_descriptor"]["flange"] == flange]
        loads += fitting_source_leg_loads(export, q, angle, flange, pose=pose)
        sections = steel.flange_reference(current, flange, loads)["sections"]
        along = common.vector(current["u_xyz"] if flange == "beam" else current["v_xyz"])
        across = common.vector(current["w_xyz"])
        basis = np.array([along, across, np.cross(along, across)])
        for cut in sections:
            cut.update(state)
            cut["current_point_xyz_mm"] = (common.vector(current["origin_xyz_mm"])+along*cut["station_from_assumed_corner_mm"]).tolist()
            cut["current_material_basis_rows_xyz"] = basis.tolist()
            chord = max(0., steel.WIDTH-cut["area_mm2"]/steel.THICKNESS)
            kwargs = {"width_mm": steel.WIDTH, "thickness_mm": steel.THICKNESS, "removed_center_width_mm": chord,
                "force_local_n": cut["force_local_n"], "moment_local_nmm": cut["moment_local_nmm"], "fy_mpa": steel.FY_CATALOG}
            cut["gross_rectangle_torsion_bound"] = torsion.simultaneous_section_bound(**kwargs, scenario="gross_rectangle")
            cut["holed_equal_twist_proxy_bound"] = torsion.simultaneous_section_bound(**kwargs,
                scenario="two_ligament_equal_twist_proxy") if chord > 1e-8 else None
        result.append({**state, "angle_id": angle, "flange": flange, "current_own_flange_pose": current,
            "sections": sections, "external_current_point_actions_on_steel": loads,
            "opposed_flange_same_rigid_pose_assumed": False, "actual_heel_hole_warping_or_capacity_verified": False})
    return result


def current_own_washer_captures(export):
    result = []
    for row in export["finite_interaction_actions"]:
        if row["kind"] != "shaft_end_capture":
            continue
        end = row["source_descriptor"]["end"]
        direction = common.vector(row["current_director_xyz"])
        scalar = row["axial_scalar_force_n"]
        if (not isinstance(scalar, (int, float)) or not math.isfinite(scalar) or scalar < 0
                or abs(np.linalg.norm(direction)-1.) > 1e-8
                or np.linalg.norm(common.vector(row["force_on_first_xyz_n"])-scalar*direction) > 1e-7):
            raise ValueError("own current washer capture must retain its unilateral scalar and director")
        result.append({**state_fields(export), "id": row["id"], "axis_id": row["source_descriptor"]["axis_id"],
            "role": {"head": "head_washer", "nut": "nut_washer"}[end["end"]], "washer_id": end["washer_id"],
            "own_capture_model_axial_force_n": scalar, "current_shaft_pressure_point_xyz_mm": row["point_on_first_xyz_mm"],
            "current_host_support_point_xyz_mm": row["point_on_second_xyz_mm"],
            "model_spatial_couple_on_shaft_at_pressure_point_nmm": row["moment_on_first_at_current_point_xyz_nmm"],
            "model_spatial_couple_on_host_at_support_point_nmm": row["moment_on_second_at_current_point_xyz_nmm"],
            "director_model_couple_is_actual_washer_pressure_prying_or_capacity": False,
            "actual_washer_material_seating_pressure_or_same_end_strength_verified": False})
    return result


def recover_current_actions(finite_export, q, layout, shaft_specs, *, caller_sections=None, pose=current_pose):
    """Public writer API. Recovery is separate from independent admission."""
    pins = source_pins()
    validate_labels(finite_export)
    q = mapped_state(finite_export, q)
    cuts = current_shaft_cuts(finite_export, q, shaft_specs, pose=pose)
    ports = current_steel_ports(finite_export, q, layout, pose=pose)
    flanges = current_flange_sections(finite_export, q, layout, ports, pose=pose)
    if source_pins() != pins:
        raise ValueError("current recovery source binding changed during evaluation")
    return {"schema": "thin_bolted_finite_steel_recovery/v1", **state_fields(finite_export), "source_sha256": pins,
        "current_shaft_section_cut_actions": cuts, "current_steel_port_actions": ports,
        "current_flange_section_actions": flanges,
        "current_shaft_circle_references": common.shaft_section_references(cuts, caller_sections),
        "current_own_washer_capture_actions": current_own_washer_captures(finite_export),
        "own_metal_role_gravity_count": sum(len(row["metal_roles"]) for row in shaft_specs),
        "independent_finite_current_gate_pass_inferred_by_recovery": False,
        "native_CAD_global_assembly_or_solve_execution": False,
        "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}
