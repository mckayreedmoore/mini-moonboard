"""Evaluate six frozen rail-interface wrenches with one compatible rigid host."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HELPER = HERE / "upper-right-combined-transfer.py"
MODEL = HERE / "operators-attempt02/model.json"
ROWS = HERE / "operators-attempt02/row-identities.json"
OPERATORS = HERE / "operators-attempt02/operators.npz"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
RESPONSE = HERE / "frame-250-attempt02/response.npz"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
PINS = {
    HELPER: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    ROWS: "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS: "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
}
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"top_outer/clip_single_top_right_2/rail_{number}" for number in (1, 2)]
HOST, CLEAT = "base_rail_top", "top_outer_right_cleat"
DATUM = np.array([1082.675, 1449.9256507823475, 2178.633244417593])
LENGTH, DIAMETER, GAP = 177.8, 6.35, 0.575
KWOOD, KHEAD, EBOLT = 20.0, 10000.0, 200000.0
AREA = math.pi * DIAMETER**2 / 4
AXIAL_COMPLIANCE = LENGTH / (EBOLT * AREA)
GRADIENT_TOLERANCE, FORCE_TOLERANCE, MOMENT_TOLERANCE = 1e-4, 0.001, 0.2
FAMILY = {"host_length_mm": 38.1, "cleat_length_mm": 139.7, "diameter_mm": DIAMETER,
          "bore_mm": 7.5, "washer_ID_max_mm": 8.3058, "washer_OD_min_mm": 18.4658, "flat_radius_mm": 5.0}
FC_PERP, FYB_SCENARIO = 4.309223308230226, 92000 * 0.006894757293168


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def skew(vector):
    x, y, z = vector
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]])


def host_map(point):
    result = np.zeros((3, 142))
    result[:, 136:139] = np.eye(3)
    result[:, 139:142] = -skew(np.asarray(point) - DATUM) / LENGTH
    return result


def load_sources():
    pins = dict(PINS)
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_combined_transfer", HELPER)
    require(spec is not None and spec.loader is not None, "pure beam helper unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    require((helper.LENGTH, helper.E_BOLT, helper.K_HEAD) == (LENGTH, EBOLT, KHEAD), "frozen helper constants differ")
    model, identities, comparison, component = read(MODEL), read(ROWS), read(COMPARISON), read(COMPONENT)
    identities_by_row = {row["row"]: row for row in identities}
    require(comparison["response_sha256"] == PINS[RESPONSE], "response metadata binding differs")
    require([state["case_id"] for state in comparison["states"] if state["gap_scale"] == 1.0] == CASES, "nominal case order differs")
    require(not comparison["complete_joint_acceptance"] and not comparison["physical_release"], "source claims joint acceptance or release")
    require(component["source_comparison_sha256"] == PINS[COMPARISON] and component["source_response_sha256"] == PINS[RESPONSE], "component force binding differs")
    selected = sorted((row for row in identities if {row["ownership"]["first_body"], row["ownership"]["second_body"]} == {HOST, CLEAT}), key=lambda row: row["row"])
    require([row["row"] for row in selected] == list(range(1808, 1812)) + list(range(1870, 1888)), "rail-interface row census differs")
    require(all(row["ownership"]["first_body"] == HOST for row in selected), "current rail row ownership order differs")
    face = [row for row in selected if row["ownership"]["role"] == "timber_or_panel_contact"]
    require(len(face) == 16, "face-cell census differs")
    weighted_center = sum(row["contact_area_mm2"]*np.array(row["ownership"]["point_mm"]) for row in face) / sum(row["contact_area_mm2"] for row in face)
    geometry = next(record["axes"] for record in model["proposed_corner_axes"] if record["block"] == CLEAT)
    revised = {record["axis_id"]: record for record in geometry}
    ties = [row for row in selected if row["ownership"]["role"] == "physical_bolt_outer_seat_tension"]
    n = np.array(ties[0]["ownership"]["direction_global_xyz"])
    require(math.isclose(float(n @ n), 1.0, abs_tol=1e-12), "bolt axis is not unit length")
    require(abs(float(n @ (weighted_center - DATUM))) <= 1e-7, "contact area centroid leaves the declared interface plane")
    basis = np.column_stack((np.array([1.0, 0.0, 0.0]), np.cross(n, [1.0, 0.0, 0.0])))
    require(np.allclose(basis.T @ basis, np.eye(2), atol=1e-12), "transverse basis is not orthonormal")
    for row in face:
        require(np.allclose(row["ownership"]["direction_global_xyz"], -n, atol=1e-10), "face normal differs")
        require(math.isclose(row["law"]["stiffness_N_per_mm"] / row["contact_area_mm2"], 100.0, rel_tol=1e-10), "existing face stiffness differs")
    bolts = []
    for number, axis_id in enumerate(AXES):
        record = revised[axis_id]
        require(record["wood_grip_mm"] == LENGTH and record["nominal_bolt_diameter_mm"] == DIAMETER and record["proposed_CAD_bore_envelope_mm"] == 7.5, "corrected rail geometry differs")
        lateral = [row for row in selected if row["row_id"].rpartition("/")[0] == axis_id and row["ownership"]["role"] == "candidate_bolt_lateral_plane"]
        tie = next(row for row in ties if row["row_id"] == axis_id + "/outer-seat-axial-tie")
        require(len(lateral) == 2 and np.allclose(tie["ownership"]["direction_global_xyz"], n, atol=1e-12), "rail bolt rows differ")
        relative_gap = next(record["relative_radial_gap_mm"] for record in comparison["clearance_planes"] if record["plane_id"] == lateral[0]["row_id"])
        require(math.isclose(relative_gap, 2*GAP, abs_tol=1e-10), "source relative gap differs from the two receiver gaps")
        bolts.append({"axis_id": axis_id, "number": number, "interface_point_xyz_mm": lateral[0]["ownership"]["point_mm"],
                      "source_component_rows": [row["row"] for row in lateral], "source_tie_row": tie["row"]})
    body_index = model["body_names"].index(HOST)
    coordinates = model["physical_node_coordinates_mm"]
    body_datum = np.mean([coordinates[str(node)] for node in sorted(set(model["body_nodes"][HOST]))], axis=0)
    raw_rows = [row["row"] for row in selected]
    states = []
    with np.load(OPERATORS, allow_pickle=False) as operators, np.load(RESPONSE, allow_pickle=False) as response:
        dbody = operators["D"][raw_rows, 6*body_index:6*body_index + 6]
        for index, row in enumerate(selected):
            require(np.allclose(dbody[index, :3], -np.array(row["ownership"]["direction_global_xyz"]), atol=1e-12, rtol=0), "D translation sign differs from row ownership")
        for case_id in CASES:
            raw = response[case_id + "_gap_raw_force_n"]
            force = -dbody[:, :3].T @ raw[raw_rows]
            moment = -1000*dbody[:, 3:6].T @ raw[raw_rows] + np.cross(body_datum - DATUM, force)
            actions = [np.array(row["ownership"]["direction_global_xyz"])*raw[row["row"]] for row in selected]
            point_force = np.sum(actions, axis=0)
            point_moment = sum(np.cross(np.array(row["ownership"]["point_mm"]) - DATUM, action) for row, action in zip(selected, actions))
            require(np.max(np.abs(force - point_force)) <= 1e-7, "D and point-force sums differ")
            originals = []
            for bolt in bolts:
                witness = next(record for record in component["states"] if record["case_id"] == case_id and record["axis_id"] == bolt["axis_id"])
                host_lateral = sum(np.array(identities_by_row[row]["ownership"]["direction_global_xyz"])*raw[row] for row in bolt["source_component_rows"])
                tension = float(raw[bolt["source_tie_row"]])
                require(math.isclose(tension, witness["tension_n"], abs_tol=1e-8) and math.isclose(float(np.linalg.norm(host_lateral)), witness["lateral_n"], abs_tol=1e-8), "original bolt comparison differs")
                originals.append({"axis_id": bolt["axis_id"], "signed_T_n": tension, "V_n": witness["lateral_n"],
                                  "signed_plane_components_n": raw[bolt["source_component_rows"]].tolist(),
                                  "force_on_host_xyz_n": host_lateral.tolist()})
            states.append({"case_id": case_id, "source_connector_wrench_on_host_n_nmm": np.r_[force, moment].tolist(),
                           "external_drive_wrench_n_nmm": (-np.r_[force, moment]).tolist(),
                           "D_point_force_residual_n": (force - point_force).tolist(),
                           "retained_source_free_couple_nmm": (moment - point_moment).tolist(),
                           "source_face_compression_n": float(sum(raw[row["row"]] for row in face)),
                           "source_face_cells": [{"row": row["row"], "compression_n": float(raw[row["row"]]),
                                                  "stiffness_n_per_mm": row["law"]["stiffness_N_per_mm"]} for row in face],
                           "source_individual_bolts": originals})
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    return helper, bolts, face, n, basis, states, body_datum, weighted_center, pins


def model_matrices(helper, bolts, face, n, basis):
    elastic36, geometric36, samples, curvatures, inertia = helper.beam_model(FAMILY, 1.0)
    head_quad = helper.annulus(FAMILY["washer_ID_max_mm"]/2, FAMILY["flat_radius_mm"])
    wood_quad = helper.annulus(FAMILY["washer_ID_max_mm"]/2, FAMILY["washer_OD_min_mm"]/2)
    blocks = []
    for bolt in bolts:
        offsets = (bolt["number"]*68, bolt["number"]*68 + 34)
        elastic, geometric = np.zeros((142, 142)), np.zeros((142, 142))
        for offset in offsets:
            indices = np.arange(offset, offset + 34)
            elastic[np.ix_(indices, indices)] = elastic36[:34, :34]
            geometric[np.ix_(indices, indices)] = geometric36[:34, :34]
        bore = []
        for row, weight, location, receiver in samples:
            mapping = np.zeros((2, 142))
            for plane, offset in enumerate(offsets):
                mapping[plane, offset:offset + 34] = row[:34]
            point = np.array(bolt["interface_point_xyz_mm"]) + (location - FAMILY["host_length_mm"])*n
            if receiver == "host":
                mapping -= basis.T @ host_map(point)
            bore.append((mapping, KWOOD*DIAMETER*weight, location, receiver, weight))
        head_slope, nut_slope = np.zeros((2, 142)), np.zeros((2, 142))
        for plane, offset in enumerate(offsets):
            head_slope[plane, offset + 1], nut_slope[plane, offset + 33] = 1/LENGTH, 1/LENGTH
        head_slope[:, 139:142] -= basis.T @ (-skew(n)/LENGTH)
        blocks.append({**bolt, "offsets": offsets, "elastic": elastic, "geometric": geometric, "bore": bore,
                       "opening_row": -n @ host_map(bolt["interface_point_xyz_mm"]), "slope_rows": (head_slope, nut_slope),
                       "head_quad": head_quad, "wood_quad": wood_quad, "curvatures": curvatures, "inertia": inertia})
    cells = [{"source": row, "opening_row": -n @ host_map(row["ownership"]["point_mm"])} for row in face]
    return blocks, cells


def contact_derivatives(contact, head_quad, wood_quad):
    properties = []
    for key, quad in (("head_contact", head_quad), ("wood_contact", wood_quad)):
        record, (area, transverse, _radius) = contact[key], quad
        active = record["closure_mm"] + record["tilt_rad"]*transverse > 0
        active_area = float(np.sum(area[active]))
        require(active_area > 0, "positive-tension contact has no active area")
        rho = float(np.sum(area[active]*transverse[active])/active_area)
        if record["tilt_rad"] == 0:
            rho = 0.0
        properties.append((active_area, rho, record["tangent_nmm_per_rad"]))
    ah, rhoh, kh = properties[0]
    aw, rhow, kw = properties[1]
    require(kh + kw > 0, "both contact tangents vanish at positive tension")
    return (kw*rhoh + kh*rhow)/(kh + kw), 1/(KHEAD*ah) + 1/(KWOOD*aw) + (rhoh - rhow)**2/(kh + kw)


def axial_elimination(helper, block, pose, seed):
    opening = float(block["opening_row"] @ pose)
    shortening = float(0.5*pose @ block["geometric"] @ pose)
    slopes = [row @ pose for row in block["slope_rows"]]
    norms = [float(np.linalg.norm(slope)) for slope in slopes]
    target = opening + shortening
    zero_threshold = -sum(norm*float(np.max(block["head_quad"][1])) for norm in norms)

    def contacts(tension):
        return [helper.series_contact(tension, norm, KWOOD, block["head_quad"], block["wood_quad"]) for norm in norms]

    if target <= zero_threshold:
        tension, ends = 0.0, contacts(0.0)
        closure_residual = None
    else:
        def balance(tension):
            if tension == 0:
                return zero_threshold - target
            return AXIAL_COMPLIANCE*tension + sum(end["total_closure_mm"] for end in contacts(tension)) - target
        upper = max(1.0, seed)
        for _ in range(60):
            if balance(upper) >= 0:
                break
            upper *= 2
        else:
            raise ValueError("axial root could not be bracketed")
        tension = brentq(balance, 0.0, upper, xtol=1e-12, rtol=1e-13)
        ends = contacts(tension)
        closure_residual = AXIAL_COMPLIANCE*tension + sum(end["total_closure_mm"] for end in ends) - target
        require(abs(closure_residual) <= 1e-9, "axial compatibility residual exceeds 1e-9 mm")
    energy = tension*target - 0.5*AXIAL_COMPLIANCE*tension**2 + sum(end["energy_nmm"] for end in ends)
    gradient = tension*(block["opening_row"] + block["geometric"] @ pose)
    hessian = tension*block["geometric"]
    g_tension = block["opening_row"] + block["geometric"] @ pose
    compliance = AXIAL_COMPLIANCE
    moment_vectors = []
    for row, slope, norm, contact in zip(block["slope_rows"], slopes, norms, ends):
        contact["tilt_compatibility_residual_rad"] = contact["head_contact"]["tilt_rad"] + contact["wood_contact"]["tilt_rad"] - norm
        if norm == 0:
            unit, vector = np.zeros(2), np.zeros(2)
            tangent = contact["tangent_nmm_per_rad"]*np.eye(2)
        else:
            unit = slope/norm
            vector = contact["moment_nmm"]*unit
            projector = np.outer(unit, unit)
            tangent = contact["tangent_nmm_per_rad"]*projector + (contact["moment_nmm"]/norm)*(np.eye(2) - projector)
        gradient += row.T @ vector
        hessian += row.T @ tangent @ row
        if tension > 0:
            dm_dt, dc_dt = contact_derivatives(contact, block["head_quad"], block["wood_quad"])
            g_tension += row.T @ (dm_dt*unit)
            compliance += dc_dt
        moment_vectors.append(vector)
    if tension > 0:
        hessian += np.outer(g_tension, g_tension)/compliance
    return energy, gradient, hessian, {"normal_opening_mm": opening, "projected_shortening_mm": shortening,
                                      "compatible_T_n": tension, "zero_tension_opening_threshold_mm": zero_threshold,
                                      "zero_tension_complementarity_violation_mm": max(0.0, target - zero_threshold) if tension == 0 else None,
                                      "axial_compatibility_residual_mm": closure_residual, "axial_stretch_mm": AXIAL_COMPLIANCE*tension,
                                      "end_contacts": ends, "end_slope_vectors_rad": [slope.tolist() for slope in slopes],
                                      "end_moment_vectors_in_transverse_basis_nmm": [vector.tolist() for vector in moment_vectors]}


def evaluate(helper, blocks, cells, pose, source):
    external = np.zeros(142)
    external[136:142] = np.r_[source["external_drive_wrench_n_nmm"][:3], np.array(source["external_drive_wrench_n_nmm"][3:])/LENGTH]
    energy, gradient, hessian = float(-external @ pose), -external.copy(), np.zeros((142, 142))
    details = []
    for block, original in zip(blocks, source["source_individual_bolts"]):
        value, force, tangent, axial = axial_elimination(helper, block, pose, original["signed_T_n"])
        value += float(0.5*pose @ block["elastic"] @ pose)
        force += block["elastic"] @ pose
        tangent += block["elastic"]
        bore_fields = []
        for mapping, coefficient, location, receiver, weight in block["bore"]:
            relative = mapping @ pose
            radius = float(np.linalg.norm(relative))
            penetration = max(0.0, radius - GAP)
            if penetration:
                direction = relative/radius
                reaction = coefficient*penetration*direction
                bore_tangent = coefficient*((1 - GAP/radius)*np.eye(2) + (GAP/radius)*np.outer(direction, direction))
                value += 0.5*coefficient*penetration**2
                force += mapping.T @ reaction
                tangent += mapping.T @ bore_tangent @ mapping
            else:
                reaction = np.zeros(2)
            bore_fields.append({"x_mm": location, "receiver": receiver, "relative_vector_mm": relative.tolist(),
                                "radial_penetration_mm": penetration, "pressure_mpa": KWOOD*penetration,
                                "force_on_beam_in_basis_n": (-reaction).tolist(), "quadrature_weight_mm": weight})
        energy += value
        gradient += force
        hessian += tangent
        details.append({"axis_id": block["axis_id"], **axial, "host_gradient_scaled_n": force[136:142].tolist(), "bore_fields": bore_fields})
    face_fields = []
    for cell in cells:
        row, opening_row = cell["source"], cell["opening_row"]
        opening = float(opening_row @ pose)
        compression = min(0.0, opening)
        stiffness = row["law"]["stiffness_N_per_mm"]
        cell_gradient = stiffness*compression*opening_row
        energy += 0.5*stiffness*compression**2
        gradient += cell_gradient
        if compression < 0:
            hessian += stiffness*np.outer(opening_row, opening_row)
        face_fields.append({"row": row["row"], "row_id": row["row_id"], "point_xyz_mm": row["ownership"]["point_mm"],
                            "opening_mm": opening, "compression_n": -stiffness*compression,
                            "area_mm2": row["contact_area_mm2"], "pressure_mpa": -stiffness*compression/row["contact_area_mm2"],
                            "host_gradient_scaled_n": cell_gradient[136:142].tolist()})
    return energy, gradient, hessian, details, face_fields


def solve_case(helper, blocks, cells, n, basis, source, debug):
    pose = np.zeros(142)
    external_force = np.array(source["external_drive_wrench_n_nmm"][:3])
    transverse = basis.T @ external_force
    magnitude = float(np.linalg.norm(transverse))
    if magnitude > GRADIENT_TOLERANCE:
        direction = transverse/magnitude
        pose[136:139] = basis @ (direction*(2*GAP + magnitude/(2*KWOOD*DIAMETER*FAMILY["host_length_mm"])))
        for block in blocks:
            for plane, offset in enumerate(block["offsets"]):
                pose[offset:offset + 34:2] = GAP*direction[plane]
    zero_compliance = AXIAL_COMPLIANCE + 2/(KHEAD*np.sum(blocks[0]["head_quad"][0])) + 2/(KWOOD*np.sum(blocks[0]["wood_quad"][0]))
    strongest = max(source["source_face_cells"], key=lambda record: record["compression_n"])
    active_face = next(cell for cell in cells if cell["source"]["row"] == strongest["row"])
    normal_rows = np.vstack([block["opening_row"][136:142] for block in blocks] + [active_face["opening_row"][136:142]])
    normal_targets = np.array([original["signed_T_n"]*zero_compliance for original in source["source_individual_bolts"]]
                              + [-strongest["compression_n"]/strongest["stiffness_n_per_mm"]])
    normal_seed, _residuals, rank, _singular = np.linalg.lstsq(normal_rows, normal_targets, rcond=None)
    require(rank == 3 and np.max(np.abs(normal_rows @ normal_seed - normal_targets)) <= 1e-7, "normal source-demand seed is not determined")
    pose[136:142] += normal_seed
    initial = pose.copy()
    debug.update({"scaled_pose_variables_mm": pose.tolist(), "source_drive_wrench_n_nmm": source["external_drive_wrench_n_nmm"],
                  "normal_seed_targets_mm": normal_targets.tolist(), "normal_seed_face_row": strongest["row"]})
    converged = False
    for iteration in range(250):
        energy, gradient, hessian, details, face_details = evaluate(helper, blocks, cells, pose, source)
        debug.update({"iteration": iteration, "energy_nmm": energy, "scaled_pose_variables_mm": pose.tolist(),
                      "mixed_scaled_gradient_components_n": gradient.tolist(), "mixed_scaled_gradient_maximum_n": float(np.max(np.abs(gradient))),
                      "bolt_compatibility": [{key: bolt[key] for key in (
                          "axis_id", "compatible_T_n", "normal_opening_mm", "projected_shortening_mm", "axial_compatibility_residual_mm",
                          "zero_tension_complementarity_violation_mm", "end_contacts", "end_slope_vectors_rad")} for bolt in details],
                      "face_cells": face_details})
        require(np.isfinite(energy) and np.isfinite(gradient).all(), "nonfinite energy or gradient")
        if float(np.max(np.abs(gradient))) <= GRADIENT_TOLERANCE:
            converged = True
            break
        eigenvalues, eigenvectors = np.linalg.eigh(hessian)
        require(eigenvalues[0] >= -1e-9*max(1.0, eigenvalues[-1]), "eliminated tangent is not numerically positive semidefinite")
        active = eigenvalues > max(1.0, eigenvalues[-1])*1e-12
        inverse = np.full(142, 1/(KWOOD*DIAMETER*LENGTH))
        inverse[active] = 1/eigenvalues[active]
        step = -eigenvectors @ (inverse*(eigenvectors.T @ gradient))
        descent = float(gradient @ step)
        require(descent < 0, "Newton direction does not descend")
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose + fraction*step
            if evaluate(helper, blocks, cells, candidate, source)[0] <= energy + 1e-4*fraction*descent + 1e-12*max(1.0, abs(energy)):
                pose = candidate
                break
        else:
            raise ValueError("Armijo search stopped without a valid step")
    require(converged, "STOP: shared rail equilibrium did not converge within 250 iterations")
    energy, gradient, hessian, bolts, face = evaluate(helper, blocks, cells, pose, source)
    require(float(np.max(np.abs(gradient))) <= GRADIENT_TOLERANCE, "mixed scaled-gradient residual exceeds its declared tolerance")
    host_residual = np.r_[-gradient[136:139], -LENGTH*gradient[139:142]]
    require(np.max(np.abs(host_residual[:3])) <= FORCE_TOLERANCE and np.max(np.abs(host_residual[3:])) <= MOMENT_TOLERANCE,
            "whole-rail force or moment residual exceeds the declared tolerance")
    beam_fields = []
    for bolt, block, original in zip(bolts, blocks, source["source_individual_bolts"]):
        scaled_host = np.array(bolt.pop("host_gradient_scaled_n"))
        wrench = -np.r_[scaled_host[:3], LENGTH*scaled_host[3:]]
        for end, moment in zip(bolt["end_contacts"], bolt["end_moment_vectors_in_transverse_basis_nmm"]):
            end["moment_on_beam_xyz_nmm"] = (-np.cross(n, basis @ np.array(moment))).tolist()
            end["wood_contact"]["peak_pressure_over_Fc_perp_diagnostic"] = end["wood_contact"]["pressure_peak_mpa"]/FC_PERP
            end["wood_contact"]["mean_pressure_over_Fc_perp_diagnostic"] = end["wood_contact"]["mean_pressure_full_annulus_mpa"]/FC_PERP
            end["actual_washer_stress_mpa"], end["actual_washer_capacity_n"] = None, None
        host_bore_force, host_bore_moment = np.zeros(3), np.zeros(3)
        for field in bolt["bore_fields"]:
            beam_force = basis @ np.array(field["force_on_beam_in_basis_n"])
            field["force_on_beam_xyz_n"] = beam_force.tolist()
            if field["receiver"] == "host":
                host_force = -beam_force
                point = np.array(block["interface_point_xyz_mm"]) + (field["x_mm"] - FAMILY["host_length_mm"])*n
                host_bore_force += host_force
                host_bore_moment += np.cross(point - DATUM, host_force)
        beam_witnesses = []
        for element, location, indices, moment_row, shear_row in block["curvatures"]:
            moments = np.array([moment_row @ pose[offset + indices] for offset in block["offsets"]])
            shears = np.array([shear_row @ pose[offset + indices] for offset in block["offsets"]])
            normal = bolt["compatible_T_n"]/AREA + float(np.linalg.norm(moments))*DIAMETER/(2*block["inertia"])
            shear_stress = 4*float(np.linalg.norm(shears))/(3*AREA)
            proxy = math.sqrt(normal**2 + 3*shear_stress**2)
            beam_witnesses.append({"axis_id": block["axis_id"], "element": element, "x_mm": location,
                                   "EI_curvature_M_components_nmm": moments.tolist(), "EI_third_derivative_shear_components_n": shears.tolist(),
                                   "nominal_smooth_von_mises_proxy_mpa": proxy, "proxy_over_conditional_92ksi_Fyb": proxy/FYB_SCENARIO})
        bolt.update({"source_original_T_n": original["signed_T_n"], "source_original_V_n": original["V_n"],
                     "source_original_signed_plane_components_n": original["signed_plane_components_n"],
                     "compatible_T_minus_source_T_n": bolt["compatible_T_n"] - original["signed_T_n"],
                     "wrench_on_host_at_face_datum_n_nmm": wrench.tolist(), "bore_force_on_host_xyz_n": host_bore_force.tolist(),
                     "bore_moment_on_host_at_face_datum_nmm": host_bore_moment.tolist(), "bore_V_resultant_n": float(np.linalg.norm(host_bore_force)),
                     "interface_point_xyz_mm": block["interface_point_xyz_mm"], "bolt_axis_head_to_nut_xyz": n.tolist(),
                     "peak_stress_witness": max(beam_witnesses, key=lambda record: record["nominal_smooth_von_mises_proxy_mpa"]),
                     "peak_bore_pressure_witness": max(bolt["bore_fields"], key=lambda record: record["pressure_mpa"]),
                     "beam_node_displacements_in_basis_mm": [pose[offset:offset + 34:2].tolist() for offset in block["offsets"]],
                     "beam_node_slopes_in_basis_rad": [(pose[offset + 1:offset + 34:2]/LENGTH).tolist() for offset in block["offsets"]],
                     "actual_hardware_capacity_n": None, "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None})
        beam_fields.extend(beam_witnesses)
    face_scaled = np.sum([field.pop("host_gradient_scaled_n") for field in face], axis=0)
    face_wrench = -np.r_[face_scaled[:3], LENGTH*face_scaled[3:]]
    bolt_wrench = np.sum([bolt["wrench_on_host_at_face_datum_n_nmm"] for bolt in bolts], axis=0)
    balance = bolt_wrench + face_wrench + np.array(source["external_drive_wrench_n_nmm"])
    require(np.max(np.abs(balance[:3])) <= FORCE_TOLERANCE and np.max(np.abs(balance[3:])) <= MOMENT_TOLERANCE, "recovered interface wrench does not balance")
    eigenvalues = np.linalg.eigvalsh(hessian)
    nullity = int(np.sum(eigenvalues <= max(1.0, eigenvalues[-1])*1e-12))
    result = {**source, "iterations": iteration, "energy_nmm": energy, "host_translation_at_face_datum_xyz_mm": pose[136:139].tolist(),
              "host_rotation_xyz_rad": (pose[139:142]/LENGTH).tolist(), "scaled_pose_variables_mm": pose.tolist(),
              "initial_scaled_pose_variables_mm": initial.tolist(), "bolts": bolts, "face_cells": face,
              "normal_seed_targets_mm": normal_targets.tolist(), "normal_seed_face_row": strongest["row"],
              "face_wrench_on_host_at_face_datum_n_nmm": face_wrench.tolist(), "interface_wrench_balance_residual_n_nmm": balance.tolist(),
              "mixed_scaled_gradient_maximum_n": float(np.max(np.abs(gradient))), "mixed_scaled_gradient_components_n": gradient.tolist(),
              "tangent_nullity_at_relative_1e_12": nullity, "representative_nonunique_pose": nullity > 0,
              "elastic_bolt_hypothesis_exceeded": any(record["proxy_over_conditional_92ksi_Fyb"] > 1 for record in beam_fields),
              "complete_joint_acceptance": False, "physical_release": False}
    return result, beam_fields


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({key: json.dumps(value, separators=(",", ":")) if isinstance(value, (list, dict)) else value for key, value in row.items()} for row in rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    output = parser.parse_args().output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    helper, source_bolts, face, n, basis, sources, body_datum, face_centroid, pins = load_sources()
    blocks, cells = model_matrices(helper, source_bolts, face, n, basis)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, beam_rows, failure = [], [], None
    try:
        for source in sources:
            debug = {}
            state, fields = solve_case(helper, blocks, cells, n, basis, source, debug)
            states.append(state)
            beam_rows.extend({"case_id": source["case_id"], **field} for field in fields)
        for path, expected in pins.items():
            require(sha(path) == expected, f"source changed during rail-pair calculation: {path}")
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"case_id": source["case_id"], "source_wrench": source["external_drive_wrench_n_nmm"],
                   "last_accepted_state": debug, "error": str(error), "incompatibility_proved": False}
    if states:
        write_csv(output / "states.csv", [{"case_id": state["case_id"], "mixed_scaled_gradient_maximum_n": state["mixed_scaled_gradient_maximum_n"],
                                             "wrench_residual_n_nmm": state["interface_wrench_balance_residual_n_nmm"],
                                             "host_translation_xyz_mm": state["host_translation_at_face_datum_xyz_mm"],
                                             "host_rotation_xyz_rad": state["host_rotation_xyz_rad"], "elastic_bolt_hypothesis_exceeded": state["elastic_bolt_hypothesis_exceeded"]} for state in states])
        write_csv(output / "bolt-states.csv", [{"case_id": state["case_id"], **{key: bolt[key] for key in (
            "axis_id", "compatible_T_n", "source_original_T_n", "source_original_V_n", "bore_V_resultant_n",
            "normal_opening_mm", "projected_shortening_mm", "axial_compatibility_residual_mm", "wrench_on_host_at_face_datum_n_nmm")}}
            for state in states for bolt in state["bolts"]])
        write_csv(output / "beam-fields.csv", beam_rows)
        write_csv(output / "bore-fields.csv", [{"case_id": state["case_id"], "axis_id": bolt["axis_id"], **field} for state in states for bolt in state["bolts"] for field in bolt["bore_fields"]])
        write_csv(output / "face-cells.csv", [{"case_id": state["case_id"], **field} for state in states for field in state["face_cells"]])
    result = {"schema": "upper_right_common_host_rail_pair_sensitivity/v1", "status": "STOP" if failure else "FINITE_SHARED_HOST_RAIL_PAIR_HYPOTHESIS",
              "counts": {"source_cases": 6, "completed_cases": len(states), "bolts": 2, "face_cells": 16, "scaled_unknowns": 142},
              "case_ids": CASES, "axis_ids": AXES, "states": states, "failure": failure,
              "model": {"geometry": FAMILY, "host": HOST, "fixed_cleat": CLEAT, "face_datum_xyz_mm": DATUM.tolist(),
                        "finished_contact_area_centroid_xyz_mm": face_centroid.tolist(),
                        "source_body_datum_xyz_mm": body_datum.tolist(), "bolt_axis_head_to_nut_xyz": n.tolist(), "transverse_basis_xyz": basis.tolist(),
                        "Kwood_mpa_per_mm_hypothesis": KWOOD, "Khead_mpa_per_mm_hypothesis": KHEAD, "Ebolt_mpa_hypothesis": EBOLT,
                        "face_stiffness_mpa_per_mm": 100.0, "radial_gap_mm": GAP, "beam_elements_per_receiver": 8,
                        "bore_gauss_points_per_element": 3, "contact_gauss_radii": 8, "contact_uniform_azimuths": 32,
                        "mixed_scaled_gradient_tolerance_n": GRADIENT_TOLERANCE, "local_moment_tolerance_nmm": LENGTH*GRADIENT_TOLERANCE,
                        "whole_rail_force_component_tolerance_n": FORCE_TOLERANCE, "whole_rail_moment_component_tolerance_nmm": MOMENT_TOLERANCE,
                        "axial_compatibility_tolerance_mm": 1e-9, "conditional_Fyb_comparison_mpa": FYB_SCENARIO,
                        "contact_rotation_hypothesis": "The circular quadrature rotates with the two-component slope; fixed-T contact is explicitly isotropic.",
                        "axial_energy": "max_T>=0[T*(qnormal + .5 z.Kg_unit.z) - .5 T^2 L/(EA) + Whead + Wnut]",
                        "initialization_scope": "Transverse gap activation and a minimum-norm common-host fit to two source-T closure seeds and one existing face compression provide numerical seeds only."},
              "limits": ["This shared rigid rail and two bolts form one finite local model. The cleat is fixed; the side interface and full frame are not solved.",
                         "The exact current 22-row connector wrench supplies the external drive. Gravity is not added again; individual frozen bolt forces are allowed to redistribute compatibly.",
                         "Face-cell points, areas and unilateral stiffnesses are unchanged. The wood, head-seat and smooth-bolt elastic laws remain explicit hypotheses, without preload or friction.",
                         "Rigid washers supply contact moments without supplying washer bending stress, material resistance or an actual bearing-face profile.",
                         "The nominal smooth-section stress proxy is a diagnostic combining sectional envelopes at the same axial location; exceeding the conditional steel comparison invalidates that elasticity hypothesis, not an observed build.",
                         "Bore pressures and beam stresses are finite quadrature/element evaluations. No actual wood, threads, head/nut seats or delivered hardware is qualified.",
                         "The stated local numerical tolerances do not change or close the adopted 47-criterion authority. A converged pose is not a full-frame motion envelope or a complete joint pass.",
                         "Only frozen current forces are consumed; no frame solve, native solve, CAD operation or historical force/acceptance transfer occurs."],
              "source_sha256": {str(path.relative_to(ROOT)): expected for path, expected in sorted(pins.items())},
              "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
              "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None, "actual_hardware_capacity_n": None,
              "coupled_joint_resistance_n": None, "complete_joint_acceptance": False, "physical_release": False}
    hashes = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    dump(output / "checks.json", result)
    hashes["checks.json"] = sha(output / "checks.json")
    dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes,
                                       "complete_joint_acceptance": False, "physical_release": False})
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before final receipt: {path}")
    print(json.dumps({"status": result["status"], "completed_cases": len(states), "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
