"""Resolve six header interfaces from frozen nominal-gap arrays, without solving.

Keep NDS placement applicability separate from component and first-face
sensitivities. Reuse saved physical actions, pair accounting and section tools.
The output is conditional engineering evidence, not fabrication qualification.
"""

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True

import bottom_corner_checks as bottom
import end_grain_route as route_method
import frame_state_contract as frame_contract
import member_screen as member
import numpy as np

screen = route_method.screen
HERE, ROOT, FRAME = screen.HERE, screen.ROOT, screen.FRAME
read, sha, require = screen.read, screen.sha, screen.require
write = screen.write_json
accounting, local = bottom.accounting, screen.local
DEFAULT_RESPONSE = HERE / "all-outer-corner-frame-attempt01"
DEFAULT_MEMBER = HERE / "member-screen-attempt02/all-outer-clearance01"
DEFAULT_LATERAL = HERE / "remaining-joint-screen-attempt03/grade5-92ksi"
DEFAULT_ROUTE = HERE / "end-grain-route-attempt02"
DEFAULT_OUTPUT = HERE / "header-joint-attempt01"
RESPONSE = DEFAULT_RESPONSE
MEMBER = DEFAULT_MEMBER
LATERAL = DEFAULT_LATERAL
ROUTE = DEFAULT_ROUTE
PRIMARY_SEATS = Path("/tmp/mini-moonboard-eccentric-parent-check-2026-10-01.json")
OUTPUT = DEFAULT_OUTPUT
CLEARANCE_PINS = {
    "all-outer-corner-frame-attempt01": {
        "comparison.json": "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
        "response.npz": "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
    },
    "two-receiver-frame-attempt03": {
        "comparison.json": "0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5",
        "response.npz": "774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52",
    },
}
EDGE_HELPER = HERE.parent / "mvp-acceleration-2026-09-28/current-bg045-edge-splitting-applicability-attempt02/produce.py"
SECTION_PLAN = HERE.parent / "right-corner-finished-sections-2026-10-01/source-plan.json"
D, CEG = route_method.D, route_method.CEG


def csv_records(path):
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def net_screen(section, geometry, old_frame, vector, references):
    """Rotate saved connected-area covariance; bound stress on its outer box.

    A connected section receives an elementary linear normal field only.
    No common strain or force split is assigned to disconnected ligaments.
    """
    props = section["properties"]
    current = member.basis(geometry)
    previous = np.array([old_frame[k] for k in
                         ("section_u_global_xyz", "section_v_global_xyz")])
    transform = current[1:] @ previous.T
    require(np.max(abs(transform @ transform.T - np.eye(2))) < 1e-8,
            "saved section frame is incompatible")
    q = props["area_covariance_integrals_mm4"]
    covariance = transform @ np.array([[q["uu"], q["uv"]],
                                      [q["uv"], q["vv"]]]) @ transform.T
    force, moment = vector[:3].copy(), vector[3:].copy()
    datum = np.array(geometry["start"]) + section["station_mm"] * current[0]
    offset = current @ (np.array(props["centroid_global_xyz_mm"]) - datum)
    moment -= np.cross(offset, force)
    slopes = np.linalg.solve(covariance, [-moment[2], moment[1]])
    corners = np.array([[u, v] for u in (-geometry["width_mm"] / 2,
                                        geometry["width_mm"] / 2)
                        for v in (-geometry["depth_mm"] / 2,
                                  geometry["depth_mm"] / 2)]) - offset[1:]
    bending = float(max(abs(corners @ slopes)))
    area = props["area_mm2"]
    ref = references["CF_only_reference_mpa"]
    axial = float(force[0] / area)
    return {
        "area_mm2": area,
        "centroid_YZ_offset_mm": offset[1:].tolist(),
        "covariance_YZ_mm4": covariance.tolist(),
        "centroid_N_VY_VZ_T_M_Y_M_Z": np.r_[force, moment].tolist(),
        "linear_normal_reference_sum": None if props["disconnected_ligaments"] else max(max(axial, 0) / ref["Ft_parallel"],
                                           max(-axial, 0) / ref["Fc_parallel"])
                                       + bending / ref["Fb"],
        "net_area_shear_reference": None if props["disconnected_ligaments"] else 1.5 * float(sum(abs(force[1:])))
                                    / area / ref["Fv_parallel"],
        "torque_nmm_no_resistance": float(moment[0]),
        "disconnected_ligaments": props["disconnected_ligaments"],
        "component_count": props["component_count"],
        "scope": "Connected-area linear normal field bounded by outer corners; net-area shear proxy. No hole concentration, torsion, or splitting capacity.",
    }


def run(*, frame_dir=FRAME, metadata_seed_dir=None):
    require(
        OUTPUT.is_relative_to(HERE)
        and OUTPUT.relative_to(HERE).parts
        and OUTPUT.relative_to(HERE).parts[0].startswith("header-joint-attempt"),
        "output must stay in a header-joint-attempt directory",
    )
    require(not any((OUTPUT / name).exists() for name in
                    ("checks.json", "joint-actions.json", "joint-states.json", "placement.json",
                     "header-sections.csv", "source-pins.json", "producer.py.snapshot")), "preserve existing header-joint evidence")
    source = screen.bind_frame_sources(frame_dir, RESPONSE, metadata_seed_dir)
    frame, response_dir = source["frame_dir"], source["clearance_dir"]
    comparison, route = source["comparison"], read(ROUTE / "route.json")
    report, geometry = read(MEMBER / "member-results.json"), read(MEMBER / "geometry.json")
    lateral = read(LATERAL / "screen.json")
    comparison_path = response_dir / "comparison.json"
    response_path = response_dir / "response.npz"
    comparison_sha = sha(comparison_path)
    response_sha = sha(response_path)
    expected_clearance = CLEARANCE_PINS.get(response_dir.name, {})
    force_scope = source["force_scope"]
    for name, expected in expected_clearance.items():
        actual = comparison_sha if name == "comparison.json" else response_sha
        require(actual == expected, "selected clearance source differs from its frozen pin: " + name)
    require(comparison["response_sha256"] == response_sha, "clearance comparison names another response")
    pins = {
        comparison_path: comparison_sha,
        response_path: response_sha,
        ROUTE / "route.json": sha(ROUTE / "route.json"),
        **local.PINS, **screen.lateral.PINS,
        accounting.MATERIALS: route_method.PINS[accounting.MATERIALS],
        route_method.FEATURES: route_method.PINS[route_method.FEATURES],
        screen.SUPPORT: screen.PINS[screen.SUPPORT],
        PRIMARY_SEATS: "0ae0af403cd99b323f0deb489e64bdf7cf94e0d32f0b84f0a9344efda2369354",
    }
    for path, digest in source["pins"].items():
        require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
        pins[path] = digest
    for directory, packet in ((ROUTE, route), (MEMBER, report), (LATERAL, lateral)):
        pins.update({directory / name: digest for name, digest in packet["output_sha256"].items()})
    for path in (frame / "model.json", frame / "row-identities.json", frame / "operators.npz"):
        pins[path] = comparison["source_sha256"][str(path.relative_to(ROOT))]
    comparison_key = str(comparison_path.relative_to(ROOT))
    response_key = str(response_path.relative_to(ROOT))
    require(
        report["clearance_input_directory"] == str(response_dir.relative_to(ROOT))
        and report["source_sha256"].get(comparison_key) == comparison_sha
        and report["source_sha256"].get(response_key) == response_sha
        and lateral["source_response_sha256"] == response_sha
        and lateral["source_comparison_sha256"] == comparison_sha
        and lateral["case_ids"] == list(frame_contract.CASES)
        and route["source_sha256"].get(comparison_key) == comparison_sha
        and route["source_sha256"].get(response_key) == response_sha
        and route["source_force_state_scope"] == force_scope
        and report["source_force_state_scope"] == force_scope
        and lateral["source_force_state_scope"] == force_scope
        and route["clearance_schema"] == comparison["schema"]
        and route["clearance_joint_hosts"] == comparison["clearance_joint_hosts"],
        "mixed force, seating-scope or clearance inputs",
    )
    for packet, frame_key in ((report, "frame_operator_directory"),
                              (lateral, "frame_operator_directory"),
                              (route, "frame_directory")):
        require(packet.get(frame_key, str(FRAME.relative_to(ROOT))) == str(frame.relative_to(ROOT))
                and packet.get("metadata_seed_directory", str(FRAME.relative_to(ROOT)))
                == str(source["metadata_seed_dir"].relative_to(ROOT)),
                "mixed physical operator or metadata seed inputs")
    require(tuple(route["case_ids"]) == frame_contract.CASES, "six-case census changed")
    require(route["force_source"] == str(response_path.relative_to(ROOT)), "route names another force source")
    require(route["axis_count"] == 12 and route["state_count"] == 72,
            "end-grain route census changed")
    require(report["producer_sha256"] == sha(Path(member.__file__))
            and lateral["producer_sha256"] == sha(HERE / "remaining_joint_screen.py"),
            "member or lateral producer differs from its saved current report")
    for path in (Path(__file__), Path(bottom.__file__), Path(member.__file__),
                 Path(route_method.__file__), Path(screen.__file__),
                 Path(accounting.__file__), Path(local.__file__),
                 Path(screen.lateral.__file__), Path(frame_contract.__file__),
                 MEMBER / "member-results.json",
                 LATERAL / "screen.json", SECTION_PLAN, EDGE_HELPER,
                 accounting.MODEL, accounting.CONTACTS):
        pins.setdefault(path, sha(path))
    require(sha(Path(route_method.__file__)) == route["producer_sha256"],
            "end-grain producer changed")
    edge = screen.load_module(EDGE_HELPER, "header_directed_edge_helper")
    model, rows = source["model"], source["rows"]
    inputs, materials = read(local.INPUTS), read(accounting.MATERIALS)
    require(inputs["revision_id"] == model["source_revision"] == route["source_revision"],
            "mixed geometry revision")
    require(inputs["candidate"] == model["candidate"] == route["candidate"], "mixed candidate")
    bolts = {b["axis_id"]: b for b in inputs["connections"] if b["kind"] == "candidate_bolt"}
    source_members = {m["member_id"]: m["reduced_geometry_descriptor"] for m in inputs["members"]}
    groups = defaultdict(list)
    for peak in route["peaks_at_92ksi"]:
        groups[peak["main_member"]].append(peak["axis_id"])
    require(len(groups) == 6 and all(len(a) == 2 for a in groups.values()), "header census changed")
    bodies = {*groups, "base_header"}
    for body in bodies:
        record = geometry["members"][body]
        pins[ROOT / record["current_finished_step"]] = record["current_finished_step_sha256"]
        require(record["current_finished_step_sha256"] == source_members[body]["step_sha256"],
                "header receiver geometry changed")
        grain = local.unit(record["geometry"]["axis"])
        require(np.max(abs(grain - ([1, 0, 0] if body == "base_header" else [0, 0, 1]))) < 1e-8,
                "grain scenario changed")
        frozen_grain = model["material_binding"]["orientation_overrides"][body]["material_axes_global_xyz"]["L"]
        require(np.max(abs(local.unit(frozen_grain) - grain)) < 1e-8, "frozen material differs")
    header = geometry["members"]["base_header"]["geometry"]
    require(np.max(abs(member.basis(header) - np.eye(3))) < 1e-8
            and abs(header["width_mm"] - 139.7) < 1e-8
            and abs(header["depth_mm"] - 38.1) < 1e-8, "header Y/Z sections changed")
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed source: " + str(path))

    route_states = {(r["case_id"], r["axis_id"]): r for r in csv_records(ROUTE / "six-case-signed-states.csv")}
    lateral_records = csv_records(LATERAL / "bolt-states.csv")
    lateral_states = {(r["case_id"], r["axis_id"]): r for r in lateral_records}
    lateral_counts = defaultdict(int)
    for record in lateral_records:
        lateral_counts[(record["case_id"], record["axis_id"])] += 1
    expected_states = {(case, axis) for case in frame_contract.CASES for axis in bolts
                       if axis in {a for axes in groups.values() for a in axes}}
    require(len(route_states) == 72 and set(route_states) == expected_states
            and expected_states <= lateral_counts.keys()
            and all(lateral_counts[state] == 1 for state in expected_states),
            "route and lateral records do not cover each of the same 12 axes once per case")
    support = read(screen.SUPPORT)
    seats = defaultdict(list)
    for seat in support["seats"]:
        if seat["axis_id"] in {a for axes in groups.values() for a in axes}:
            require(seat["geometry_screen_pass"] and seat["all_direction_hole_only_applicable"],
                    "header washer is not fully supported")
            require(support["finished_step_pins"][seat["member"]]["sha256"]
                    == geometry["members"][seat["member"]]["current_finished_step_sha256"],
                    "washer support has another STEP binding")
            seats[seat["axis_id"]].append(seat)
    # The remaining-seat packet excludes the two primary left-knee axes.
    # Reuse their separate frozen geometry evidence, never its old forces.
    primary = read(PRIMARY_SEATS)
    require(primary["verified_input_sha256"]["reduced model inputs"]["sha256"] == pins[local.INPUTS],
            "primary washer geometry has another raw model")
    require(primary["swept_step_envelope"]["all_direction_hole_only_support_proven_within_BREP_tolerance"],
            "primary washer sweep is unsupported")
    primary_areas = [{"mode": "combined", "supported_area_mm2": v["analytic_supported_area_mm2"]}
                     for s in primary["scenarios"] for v in s["offset_modes"]
                     if v["name"].startswith("combined")]
    for seat in primary["swept_step_envelope"]["per_seat"]:
        if seat["axis_id"] not in ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2"):
            continue
        require(seat["min_swept_support_fraction"] > 1 - 1e-7
                and max(seat["outward_overlap_fraction_by_depth"]) < 1e-7,
                "primary seat loses geometry support")
        clearance = next(r for r in bolts[seat["axis_id"]]["receiver_clearance_geometry"]
                         if r["receiver_id"] == seat["member"])
        require(abs(clearance["unique_bore_radius_mm"] - 3.75) < 1e-8,
                "primary displaced-area bore differs")
        seats[seat["axis_id"]].append({**seat, "role": seat["role"].removesuffix("_washer_seat"),
                                      "conditional_hole_only_areas": primary_areas})
    require(len(seats) == 12 and all(len(v) == 2 for v in seats.values()), "washer census changed")
    bounds = {r["member_id"]: np.array(r["bounds_xyz_mm"]) for r in route["stock_proposal"]}
    old_frame = next(f for f in read(SECTION_PLAN)["member_frames_and_step_bindings"]
                     if f["member_id"] == "base_header")
    sections = [s for s in geometry["saved_matching_finished_sections"] if s["member"] == "base_header"]
    require(sections and all(s["source_step_sha256"] == old_frame["step_sha256"]
                            == geometry["members"]["base_header"]["current_finished_step_sha256"]
                            for s in sections), "net sections have another source")
    contact_cells = {c["name"]: c for c in read(accounting.MODEL)["contact_cell_ownership"]
                     if c["kind"] == accounting.CONTACT}
    references = {b: member.reference_values(b, geometry["members"][b]["geometry"], materials) for b in bodies}
    fc_perp = materials["conditional_DF_L_No2_base_row"]["base_properties"]["Fc_perpendicular"] * local.PSI_MPA
    e_psi = materials["conditional_DF_L_No2_base_row"]["base_properties"]["E"]
    states, placements, joints, cuts, balances = [], [], [], [], []
    with (np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays,
          np.load(response_path, allow_pickle=False) as response,
          np.load(frame / "operators.npz", allow_pickle=False) as operators):
        require(operators["D"].shape == (1888, 300), "physical operator changed")
        for case in frame_contract.CASES:
            raw = response[case + "_gap_raw_force_n"]
            require(raw.shape == (1888,) and np.isfinite(raw).all(), "invalid raw force")
            actions = {b: bottom.saved_actions(b, case, geometry["members"][b], arrays) for b in bodies}
            for body in sorted(bodies):
                ids = model["body_nodes"][body]
                datum = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in ids], axis=0)
                value = accounting.wrench(actions[body], datum)
                require(max(abs(value[:3])) < 0.1 and max(abs(value[3:])) < 2, "whole-body imbalance")
                index = model["body_names"].index(body)
                for action in actions[body]:
                    if action["row"] < 0:
                        continue
                    expected = -operators["D"][action["row"], 6 * index:6 * index + 6] * raw[action["row"]]
                    restored = accounting.wrench([action], datum)
                    require(max(abs(restored[:3] - expected[:3])) < 1e-7
                            and max(abs(restored[3:] - expected[3:] * 1000)) < 1e-5,
                            "saved action/operator disagreement")
                balances.append({"case_id": case, "body": body, "residual_xyz_n_nmm": value.tolist()})
            for block, axes in sorted(groups.items()):
                axes.sort()
                group = {"block": block, "host": "base_header", "axis_ids": axes}
                target = [a for a in actions[block] if a["other_body"] == "base_header"]
                reciprocal = [a for a in actions["base_header"] if a["other_body"] == block]
                require(len(target) == len(reciprocal) == 10, "incomplete interface accounting")
                datum = np.mean([rows[json.loads(route_states[(case, a)]["component_rows"])[0]]
                                 ["ownership"]["point_mm"] for a in axes], axis=0)
                pair = bottom.pair_action(group, target, datum, geometry["members"][block]["geometry"])
                w = accounting.wrench(target, datum)
                residual = w + accounting.wrench(reciprocal, datum)
                require(max(abs(residual)) < 1e-5, "interface reciprocity failure")
                parts = {role: accounting.wrench([a for a in target if a["role"] == role], datum).tolist()
                         for role in sorted({a["role"] for a in target})}
                require(max(abs(np.sum(list(parts.values()), axis=0) - w)) < 1e-7, "lost couple")
                cells = [a for a in target if a["role"] == accounting.CONTACT]
                pressures = [max(0, float(raw[a["row"]])) / contact_cells[a["source_id"]]["area_mm2"] for a in cells]
                pitch = float(np.linalg.norm(np.diff(np.array([bolts[a]["source_point_xyz_mm"][:2] for a in axes]), axis=0)))
                length = json.loads(route_states[(case, axes[0])]["main_side_bearing_lengths_mm"])[0]
                # NDS equation used as a deliberately conservative two-fastener
                # row sensitivity; the actual oblique pair is not an equal-load row.
                cg = local.group_factor(2, pitch / 25.4, e_psi * length * (4 * D) / 25.4**2,
                                        e_psi * 38.1 * (4 * D) / 25.4**2)
                lower, upper = min(a["footprint_mm"][0] for a in reciprocal), max(a["footprint_mm"][1] for a in reciprocal)
                boundary_cuts = [accounting.host_cut(actions["base_header"], s, header, before)
                                 for s, before in ((lower - 1, True), (upper + 1, False))]
                header_stations = np.repeat(geometry["members"]["base_header"]["stations_mm"], 2)
                header_values = arrays[case + "__base_header__internal_negative_grain_u_v"]
                zone_indices = np.flatnonzero((header_stations >= lower - 1) & (header_stations <= upper + 1))
                require(len(zone_indices) > 0, "missing header connection-zone traces")
                zone_peaks = {
                    name: {"station_mm": float(header_stations[index]),
                           "trace": "before" if index % 2 == 0 else "after",
                           "signed_N_VY_VZ_T_MY_MZ": header_values[index].tolist()}
                    for component, name in enumerate(("N", "VY", "VZ", "T", "MY", "MZ"))
                    for index in [zone_indices[np.argmax(abs(header_values[zone_indices, component]))]]
                }
                # Header in-plane cross-grain dimension is Y=139.7; b=Z=38.1.
                y = [bolts[a]["source_point_xyz_mm"][1] for a in axes]
                he = {"+Y": -36.0 - min(y), "-Y": max(y) - (-175.7)}
                f90 = {face: 14 * 38.1 * math.sqrt(h / (1 - h / 139.7)) for face, h in he.items()}
                boundary_demand_y = max(abs(c[k]["force_grain_u_v_n"][1]) for c in boundary_cuts
                                        for k in ("internal_on_positive_half", "internal_on_negative_half"))
                demand_y = max(boundary_demand_y, abs(zone_peaks["VY"]["signed_N_VY_VZ_T_MY_MZ"][1]))
                joints.append({
                    "case_id": case, **group, "datum_xyz_mm": datum.tolist(),
                    "interface_wrench_on_block_xyz_n_nmm": w.tolist(), "role_wrenches_xyz_n_nmm": parts,
                    "reciprocity_residual_xyz_n_nmm": residual.tolist(), "pair": pair,
                    "actions_on_block": target, "complete_block_actions": actions[block],
                    "contact_cell_pressures_mpa": pressures,
                    "face_pressure_over_header_Fc_perp": max(pressures) / fc_perp,
                    "face_pressure_over_block_Fc_parallel": max(pressures) / references[block]["CF_only_reference_mpa"]["Fc_parallel"],
                    "pair_pitch_Y_mm": pitch, "Cg_two_fastener_row_sensitivity": cg,
                    "no_equal_sharing_credit": True, "no_face_friction_credit": True,
                    "header_footprint_bounds_mm": [lower, upper], "header_boundary_cuts": boundary_cuts,
                    "header_boundary_VY_demand_n": boundary_demand_y,
                    "header_connection_zone_signed_peaks": zone_peaks,
                    "header_VY_demand_n": demand_y, "header_He_for_both_Y_edges_mm": he,
                    "F90_characteristic_reference_n": f90,
                    "VY_over_minimum_F90_Rk_diagnostic": demand_y / min(f90.values()),
                    "splitting_design_resistance_established": False,
                })
                for axis, individual in zip(axes, pair["individual_bolts"], strict=True):
                    r, l = route_states[(case, axis)], lateral_states[(case, axis)]
                    components = json.loads(r["component_rows"])
                    force = raw[components] @ np.array([rows[i]["ownership"]["direction_global_xyz"] for i in components])
                    if rows[components[0]]["ownership"]["first_body"] != block:
                        force = -force
                    require(max(abs(force - individual["force_n"])) < 1e-7, "force convention differs")
                    tie_row = int(r["outer_tie_row"])
                    tension = float(raw[tie_row])
                    require(tension >= -1e-8 and abs(tension - float(l["outer_tie_signed_n"])) < 1e-8,
                            "mixed same-state axial demand")
                    shear = float(np.linalg.norm(force))
                    wasm = []
                    for seat in seats[axis]:
                        area = min(v["supported_area_mm2"] for v in seat["conditional_hole_only_areas"] if v["mode"] == "combined")
                        capacity = fc_perp if seat["member"] == "base_header" else references[block]["CF_only_reference_mpa"]["Fc_parallel"]
                        wasm.append({"member": seat["member"], "role": seat["role"], "supported_area_mm2": area,
                                     "pressure_mpa": tension / area, "wood_reference_mpa": capacity,
                                     "pressure_over_reference": tension / area / capacity,
                                     "grain_relative_to_bolt": "perpendicular" if seat["member"] == "base_header" else "parallel"})
                    axial = tension / (0.0318 * 25.4**2)
                    tau = 4 * shear / (3 * math.pi * D**2 / 4)
                    reserve = math.sqrt((92000 * local.PSI_MPA)**2 - 3 * tau**2) - axial
                    require(reserve > 0, "conditional steel yield exhausted")
                    lengths = json.loads(r["main_side_bearing_lengths_mm"])
                    angles = [90, screen.lateral.angle(force, [1, 0, 0])]
                    reduced = screen.lateral.reference(lengths, angles, reserve / local.PSI_MPA)
                    z = CEG * reduced["reference_lateral_lbf"] * screen.lateral.N_PER_LBF
                    states.append({"case_id": case, "block": block, "axis_id": axis,
                                   "force_on_block_xyz_n": force.tolist(), "shear_n": shear, "tension_n": tension,
                                   "component_rows": components, "tie_row": tie_row,
                                   "Ceg": CEG, "Cdelta_end_spacing_envelope": 1.0,
                                   "Cg_row_sensitivity": cg, "source_V_over_Ceg_Z_92ksi": float(r["V_over_Ceg_Z_92ksi"]),
                                   "same_state_steel_reserve_Ceg_Z_n": z,
                                   "same_state_V_over_Ceg_Z_Cg_sensitivity": shear / (z * cg),
                                   "washer_seats": wasm,
                                   "adopted_actual_detailing_failure": False})
                    point = bolts[axis]["source_point_xyz_mm"]
                    box = bounds[block]
                    hit = (
                        edge.directed_hit(point, force.tolist(),
                                          {"x": box[:, 0].tolist(), "y": box[:, 1].tolist()})
                        if max(abs(force[0]), abs(force[1])) >= 1e-10
                        else {
                            "first_intersected_source_envelope_face": None,
                            "first_intersection_travel_parameter_mm_per_n": None,
                            "first_intersection_normal_distance_mm": None,
                            "opposite_face": None,
                            "opposite_face_distance_mm": None,
                        }
                    )
                    signed_face, distance_y = edge.edge_distance(point, float(force[1]), box[:, 1].tolist())
                    header_face, header_edge = edge.edge_distance(point, -float(force[1]), [-175.7, -36.0])
                    end_x = [point[0] - header["start"][0], header["end"][0] - point[0]]
                    placements.append({"case_id": case, "axis_id": axis, "block": block,
                                       "source_axis_point_xyz_mm": point, "signed_force_on_block_xyz_n": force.tolist(),
                                       "block_finished_bounds_xyz_mm": box.tolist(), **hit,
                                       "block_Y_component_face": signed_face, "block_Y_component_edge_mm": distance_y,
                                       "block_Y_component_below_4D_sensitivity": bool(signed_face != "none" and distance_y < 4 * D - 1e-6),
                                       "first_face_normal_distance_below_4D_diagnostic":
                                           None if hit["first_intersection_normal_distance_mm"] is None
                                           else bool(hit["first_intersection_normal_distance_mm"] < 4 * D - 1e-6),
                                       "header_force_grain_angle_deg": angles[1], "header_grain_end_distances_mm": end_x,
                                       "header_Y_component_face": header_face, "header_Y_component_edge_mm": header_edge,
                                       "header_Y_component_below_4D_sensitivity": bool(header_face != "none" and header_edge < 4 * D - 1e-6),
                                       "adopted_actual_detailing_failure": False,
                                       "loaded_edge_rule": "NDS 12.1.2.1 / Table C; first-ray face and component face are diagnostics, not an invented NDS multi-face rule."})
            for section in sections:
                station = section["station_mm"]
                for trace, index in zip(("before", "after"), section["cut_indices_before_after"], strict=True):
                    vector = arrays[case + "__base_header__internal_negative_grain_u_v"][index]
                    own = net_screen(section, header, old_frame, vector, references["base_header"])
                    cuts.append({"case_id": case, "station_mm": station, "trace": trace,
                                 "plane_id": section["plane_id"], **own})
    for path, digest in pins.items():
        require(sha(path) == digest, "input changed during calculation: " + str(path))
    require(len(states) == 72 and len(joints) == 36 and len(balances) == 42, "incomplete six-case coverage")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / ".gitignore").write_text("*\n")
    write(OUTPUT / "joint-actions.json", {"interfaces": joints, "whole_body_balances": balances})
    write(OUTPUT / "joint-states.json", states)
    write(OUTPUT / "placement.json", placements)
    screen.write_csv(OUTPUT / "header-sections.csv", cuts)
    write(OUTPUT / "source-pins.json", {str(p): h for p, h in sorted(pins.items())})
    (OUTPUT / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    first_face_diagnostics = [
        p for p in placements if p["first_face_normal_distance_below_4D_diagnostic"]
    ]
    short_axes = sorted({p["axis_id"] for p in first_face_diagnostics})
    if first_face_diagnostics:
        status = "FINITE_CONDITIONAL_STRENGTH_AND_TRANSFER_RESULT_WITH_FIRST_FACE_SHORT_DIAGNOSTICS"
        remaining_detail = (
            f"{len(first_face_diagnostics)} first-ray normal-distance comparisons are below 4D across "
            f"{len(short_axes)} axes ({', '.join(short_axes)}). These are conditional placement diagnostics, "
            "not adopted NDS failures; the applicability of the multi-face loaded-edge construction remains "
            "unresolved. No Cdelta reduction is used to waive an edge minimum."
        )
    else:
        status = "FINITE_CONDITIONAL_STRENGTH_AND_TRANSFER_RESULT_WITH_NO_FIRST_FACE_SHORT_COMPARISON"
        null_ray_count = sum(p["first_intersected_source_envelope_face"] is None for p in placements)
        directional_count = len(placements) - null_ray_count
        remaining_detail = (
            "No saved first-ray normal distance is below 4D. "
            f"{null_ray_count} of {len(placements)} states have zero in-plane force and retain null first-ray "
            f"direction, face and travel fields; {directional_count} directional states have no short comparison. "
            "This does not establish local splitting/torque resistance, a universal loaded-edge rule or complete "
            "joint acceptance. No Cdelta reduction is used to waive an edge minimum."
        )
    summary = {
        "schema": "six_current_header_joint_conditional_checks/v1",
        "status": status,
        "candidate": model["candidate"], "source_revision": model["source_revision"],
        "development_revision": model["development_revision"], "case_ids": list(frame_contract.CASES),
        "force_source": str(response_path.relative_to(ROOT)),
        "force_key": "case_id + '_gap_raw_force_n'", "gap_scale": 1.0,
        "clearance_source_directory": str(response_dir.relative_to(ROOT)),
        "frame_operator_directory": str(frame.relative_to(ROOT)),
        "metadata_seed_directory": str(source["metadata_seed_dir"].relative_to(ROOT)),
        "metadata_seed_scope": "Case order and inherited seed provenance only; no old force vectors or acceptance transferred.",
        "clearance_comparison_sha256": comparison_sha,
        "response_sha256": response_sha,
        "source_force_state_scope": force_scope,
        "member_report_source": str((MEMBER / "member-results.json").relative_to(ROOT)),
        "lateral_report_source": str((LATERAL / "screen.json").relative_to(ROOT)),
        "end_grain_route_source": str((ROUTE / "route.json").relative_to(ROOT)),
        "counts": {"joints": 6, "axes": 12, "bolt_states": 72, "interfaces": 36,
                   "whole_body_balances": 42, "header_sections": len(sections), "header_section_states": len(cuts)},
        "conditional_material": {b: references[b] for b in sorted(bodies)},
        "peaks": {
            "individual_lateral": max(states, key=lambda s: s["source_V_over_Ceg_Z_92ksi"]),
            "same_state_lateral_with_Cg_sensitivity": max(states, key=lambda s: s["same_state_V_over_Ceg_Z_Cg_sensitivity"]),
            "washer": max(({"case_id": s["case_id"], "axis_id": s["axis_id"], **w}
                           for s in states for w in s["washer_seats"]), key=lambda w: w["pressure_over_reference"]),
            "header_net_normal": max((c for c in cuts if c["linear_normal_reference_sum"] is not None), key=lambda c: c["linear_normal_reference_sum"]),
            "header_net_shear": max((c for c in cuts if c["net_area_shear_reference"] is not None), key=lambda c: c["net_area_shear_reference"]),
            "header_torque": max(cuts, key=lambda c: abs(c["torque_nmm_no_resistance"])),
            "header_splitting_demand": max(joints, key=lambda j: j["header_VY_demand_n"])["header_VY_demand_n"],
            "F90_characteristic_comparison": max(j["VY_over_minimum_F90_Rk_diagnostic"] for j in joints),
            "face_pressure_over_header_Fc_perp": max(j["face_pressure_over_header_Fc_perp"] for j in joints),
            "whole_body_force_residual_n": max(max(abs(v) for v in b["residual_xyz_n_nmm"][:3]) for b in balances),
            "whole_body_moment_residual_nmm": max(max(abs(v) for v in b["residual_xyz_n_nmm"][3:]) for b in balances),
        },
        "first_face_below_4D_diagnostics": [p for p in placements if p["first_face_normal_distance_below_4D_diagnostic"]],
        "adopted_actual_detailing_failures": [],
        "exact_remaining_detailing_fact": remaining_detail,
        "limits": [
            "Existing Fe_perp and Ceg=.67 route is reused once, without re-investigating applicability.",
            "Cg is a two-fastener transverse row sensitivity using 4D equivalent widths, not uniform sharing or complete oblique-group acceptance. Actual signed forces and couples remain unchanged.",
            "Cdelta=1 is the conservative header end/spacing envelope; grainwise end distance is not assigned to a through end-grain block using a shaft midpoint.",
            "Washer wood pressures use same-state axial ties, displaced supported areas, Fc_perp on header and Fc_parallel on Z-grain blocks, with no bearing-area factor or friction/preload credit. Washer-metal, head/nut and delivered-shank qualification remain false.",
            "Net normal and shear references are finite section proxies. F90 is a characteristic EN reference, not an NDS resistance or cross-code design DCR. Required Y splitting, Z face/washer actions, moments and torque are retained together.",
            "Perpendicular splitting and torque interaction require an applicable local resistance; no invented wood tensile-perpendicular allowable or pure-force replacement of a couple is used.",
            "Parent owns integrated panel stiffness/contact sensitivity. No historical native force or acceptance is transferred.",
        ],
        "native_solve_run": False, "frame_solve_run": False, "CAD_rebuilt": False,
        "tests_run": False, "review_run": False,
        "reviewed_geometry_changed": bool(model.get("owner_authorized_screw_movements")),
        "owner_authorized_screw_movements": model.get("owner_authorized_screw_movements", []),
        "bolt_geometry_changed": False,
        "formal_qualification": False, "complete_joint_acceptance": False, "physical_release": False,
        "producer_sha256": sha(Path(__file__)),
        "output_sha256": {n: sha(OUTPUT / n) for n in
                          ("joint-actions.json", "joint-states.json", "placement.json", "header-sections.csv", "source-pins.json", "producer.py.snapshot")},
    }
    write(OUTPUT / "checks.json", summary)
    print(summary["status"])
    print(summary["counts"])
    print({k: (v if not isinstance(v, dict) else {a: v[a] for a in v
            if 'ratio' in a or 'reference_sum' in a or 'sensitivity' in a or a in
            ('case_id', 'axis_id', 'station_mm', 'net_area_shear_reference', 'pressure_over_reference')})
           for k, v in summary["peaks"].items()})
    print("First-face diagnostics:", [(p["case_id"], p["axis_id"], p["first_intersected_source_envelope_face"])
                                      for p in summary["first_face_below_4D_diagnostics"]])


def packet_path(value):
    path = Path(value)
    return (path if path.is_absolute() else HERE / path).resolve()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", default=str(FRAME.relative_to(HERE)),
                        help="Physical operator directory; defaults to the historical corrected frame.")
    parser.add_argument("--metadata-seed",
                        help="Case metadata directory; defaults to --frame. No seed force arrays are consumed.")
    parser.add_argument("--clearance", default=str(DEFAULT_RESPONSE.relative_to(HERE)))
    parser.add_argument("--members", default=str(DEFAULT_MEMBER.relative_to(HERE)))
    parser.add_argument("--lateral", default=str(DEFAULT_LATERAL.relative_to(HERE)))
    parser.add_argument("--route", default=str(DEFAULT_ROUTE.relative_to(HERE)))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT.relative_to(HERE)))
    args = parser.parse_args(argv)

    global RESPONSE, MEMBER, LATERAL, ROUTE, OUTPUT
    RESPONSE = packet_path(args.clearance)
    MEMBER = packet_path(args.members)
    LATERAL = packet_path(args.lateral)
    ROUTE = packet_path(args.route)
    OUTPUT = packet_path(args.output)
    run(frame_dir=packet_path(args.frame),
        metadata_seed_dir=packet_path(args.metadata_seed) if args.metadata_seed else None)


if __name__ == "__main__":
    main()
