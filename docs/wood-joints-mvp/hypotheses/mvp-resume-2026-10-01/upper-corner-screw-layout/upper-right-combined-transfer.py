"""Solve finite independent upper-right bolt sensitivities from frozen forces."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import scipy
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
REGISTER = HERE / "rawlocal/joint-register/attempt01/register.json"
MODEL = HERE / "operators-attempt02/model.json"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
COMPARISON = HERE / "frame-250-attempt02/comparison.json"
RESPONSE = HERE / "frame-250-attempt02/response.npz"
FROZEN = {
    REGISTER: "79db8c6830dee42e47dcdcd75c331ce22a67cd3d27e38f9a8b616e820c37d3ca",
    MODEL: "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    COMPARISON: "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE: "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
}
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = ["top_outer/clip_single_top_right_2/" + name for name in ("rail_1", "rail_2", "side_1", "side_2")]
LENGTH, E_BOLT, K_HEAD = 177.8, 200000.0, 10000.0
K_BRANCHES = (5.0, 20.0, 80.0)
PSI_TO_MPA = 0.006894757293168
FYB_SCENARIO = 92000.0 * PSI_TO_MPA
FC_PERP = 4.309223308230226
FAMILIES = {
    "rail": {"host_length_mm": 38.1, "cleat_length_mm": 139.7, "diameter_mm": 6.35, "bore_mm": 7.5,
             "washer_ID_max_mm": 8.3058, "washer_OD_min_mm": 18.4658, "flat_radius_mm": 5.0},
    "side": {"host_length_mm": 88.9, "cleat_length_mm": 88.9, "diameter_mm": 7.9375, "bore_mm": 9.0,
             "washer_ID_max_mm": 9.9060, "washer_OD_min_mm": 22.0472, "flat_radius_mm": 6.0},
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def annulus(inner, outer):
    abscissa, weights = np.polynomial.legendre.leggauss(8)
    radii = inner + (abscissa + 1) * (outer - inner) / 2
    radial_area = radii * weights * (outer - inner) / 2 * (2 * math.pi / 32)
    angles = (np.arange(32) + 0.5) * (2 * math.pi / 32)
    return np.repeat(radial_area, 32), (radii[:, None] * np.cos(angles)).ravel(), outer


def compression(tension, tilt, stiffness, quadrature):
    area, transverse, radius = quadrature
    if tension == 0:
        return {"energy_nmm": 0.0, "moment_nmm": 0.0, "tangent_nmm_per_rad": 0.0,
                "closure_mm": 0.0, "active_area_mm2": 0.0, "pressure_peak_mpa": 0.0,
                "mean_pressure_full_annulus_mpa": 0.0, "force_residual_n": 0.0,
                "moment_over_T_radius": None, "tilt_rad": tilt}
    offsets = tilt * transverse
    order = np.argsort(-offsets)
    cumulative_area = np.cumsum(area[order])
    cumulative_offset = np.cumsum(area[order] * offsets[order])
    closures = (tension / stiffness - cumulative_offset) / cumulative_area
    last_positive = closures + offsets[order] > 0
    next_nonpositive = np.r_[closures[:-1] + offsets[order][1:] <= 0, True]
    eligible = np.flatnonzero(last_positive & next_nonpositive)
    require(len(eligible) == 1, "compression active prefix is not uniquely identified")
    closure = float(closures[eligible[0]])
    indentation = np.maximum(closure + offsets, 0.0)
    pressure = stiffness * indentation
    active = indentation > 0
    active_area = float(np.sum(area[active]))
    first_moment = float(np.sum(area[active] * transverse[active]))
    second_moment = float(np.sum(area[active] * transverse[active] ** 2))
    moment = float(np.sum(area * pressure * transverse))
    tangent = stiffness * (second_moment - first_moment**2 / active_area)
    return {"energy_nmm": float(0.5 * stiffness * np.sum(area * indentation**2) - tension * closure),
            "moment_nmm": moment, "tangent_nmm_per_rad": max(0.0, tangent),
            "closure_mm": closure, "active_area_mm2": active_area,
            "pressure_peak_mpa": float(np.max(pressure)),
            "mean_pressure_full_annulus_mpa": tension / float(np.sum(area)),
            "force_residual_n": float(np.sum(area * pressure) - tension),
            "moment_over_T_radius": abs(moment) / (tension * radius), "tilt_rad": tilt}


def series_contact(tension, relative_tilt, kwood, head_quad, wood_quad):
    if tension == 0 or relative_tilt == 0:
        washer_tilt = 0.0
    elif abs(relative_tilt) < 1e-12:
        kh = compression(tension, 0.0, K_HEAD, head_quad)["tangent_nmm_per_rad"]
        kw = compression(tension, 0.0, kwood, wood_quad)["tangent_nmm_per_rad"]
        washer_tilt = relative_tilt * kh / (kh + kw)
    else:
        def balance(angle):
            return (compression(tension, relative_tilt - angle, K_HEAD, head_quad)["moment_nmm"]
                    - compression(tension, angle, kwood, wood_quad)["moment_nmm"])
        washer_tilt = brentq(balance, min(0.0, relative_tilt), max(0.0, relative_tilt), xtol=1e-14, rtol=1e-14)
    head = compression(tension, relative_tilt - washer_tilt, K_HEAD, head_quad)
    wood = compression(tension, washer_tilt, kwood, wood_quad)
    kh, kw = head["tangent_nmm_per_rad"], wood["tangent_nmm_per_rad"]
    return {"energy_nmm": head["energy_nmm"] + wood["energy_nmm"],
            "moment_nmm": head["moment_nmm"], "tangent_nmm_per_rad": kh * kw / (kh + kw) if kh + kw else 0.0,
            "moment_balance_residual_nmm": head["moment_nmm"] - wood["moment_nmm"],
            "relative_tilt_rad": relative_tilt, "washer_tilt_rad": washer_tilt,
            "total_closure_mm": head["closure_mm"] + wood["closure_mm"], "head_contact": head, "wood_contact": wood}


def hermite(s, length, derivative=0):
    if derivative == 0:
        values = [1 - 3*s*s + 2*s**3, length*(s - 2*s*s + s**3), 3*s*s - 2*s**3, length*(-s*s + s**3)]
    elif derivative == 2:
        values = [(-6 + 12*s)/length**2, (-4 + 6*s)/length, (6 - 12*s)/length**2, (-2 + 6*s)/length]
    else:
        values = [12/length**3, 6/length**2, -12/length**3, 6/length**2]
    return np.array(values) * np.array([1.0, 1/LENGTH, 1.0, 1/LENGTH])


def beam_model(family, tension):
    host_length, diameter = family["host_length_mm"], family["diameter_mm"]
    nodes = np.r_[np.linspace(0, host_length, 9), np.linspace(host_length, LENGTH, 9)[1:]]
    inertia = math.pi * diameter**4 / 64
    rigidity = E_BOLT * inertia
    elastic, geometric = np.zeros((36, 36)), np.zeros((36, 36))
    samples, curvatures = [], []
    gauss, weights = np.polynomial.legendre.leggauss(3)
    scale = np.diag([1.0, 1/LENGTH, 1.0, 1/LENGTH])
    for element, (left, right) in enumerate(pairwise(nodes)):
        span = right - left
        indices = np.arange(2*element, 2*element + 4)
        stiffness = rigidity / span**3 * np.array([
            [12, 6*span, -12, 6*span], [6*span, 4*span**2, -6*span, 2*span**2],
            [-12, -6*span, 12, -6*span], [6*span, 2*span**2, -6*span, 4*span**2]])
        initial_stress = tension / (30*span) * np.array([
            [36, 3*span, -36, 3*span], [3*span, 4*span**2, -3*span, -span**2],
            [-36, -3*span, 36, -3*span], [3*span, -span**2, -3*span, 4*span**2]])
        elastic[np.ix_(indices, indices)] += scale @ stiffness @ scale
        geometric[np.ix_(indices, indices)] += scale @ initial_stress @ scale
        for coordinate, weight in zip((gauss + 1)/2, weights*span/2):
            location = left + coordinate*span
            row = np.zeros(36)
            row[indices] = hermite(coordinate, span)
            host = element < 8
            if host:
                row[34], row[35] = -1.0, -(location - host_length)/LENGTH
            samples.append((row, float(weight), float(location), "host" if host else "cleat"))
        for coordinate in np.r_[0.0, (gauss + 1)/2, 1.0]:
            curvatures.append((element, float(left + coordinate*span), indices,
                               rigidity*hermite(coordinate, span, 2), rigidity*hermite(coordinate, span, 3)))
    return elastic, geometric, samples, curvatures, inertia


def solve_state(source, family, kwood):
    tension, lateral = source["signed_T_n"], source["V_n"]
    require(tension >= 0, "negative source tension is outside the prescribed positive-T model")
    diameter, gap = family["diameter_mm"], (family["bore_mm"] - family["diameter_mm"])/2
    elastic, geometric, samples, curvatures, inertia = beam_model(family, tension)
    stiffness = elastic + geometric
    sample_rows = np.vstack([sample[0] for sample in samples])
    coefficients = kwood * diameter * np.array([sample[1] for sample in samples])
    inner = family["washer_ID_max_mm"] / 2
    head_quad, wood_quad = annulus(inner, family["flat_radius_mm"]), annulus(inner, family["washer_OD_min_mm"]/2)
    head_row, nut_row = np.zeros(36), np.zeros(36)
    head_row[1], head_row[35], nut_row[33] = 1/LENGTH, -1/LENGTH, 1/LENGTH
    baseline = 2 * series_contact(tension, 0.0, kwood, head_quad, wood_quad)["energy_nmm"]

    def evaluate(pose):
        relative = sample_rows @ pose
        penetration = np.sign(relative) * np.maximum(np.abs(relative) - gap, 0.0)
        active = np.abs(relative) > gap
        contact_forces = coefficients * penetration
        gradient = stiffness @ pose + sample_rows.T @ contact_forces
        gradient[34] -= lateral
        hessian = stiffness + sample_rows.T @ (coefficients[:, None] * active[:, None] * sample_rows)
        energy = float(0.5*pose @ stiffness @ pose + 0.5*np.sum(coefficients*penetration**2) - lateral*pose[34] - baseline)
        ends = []
        for row in (head_row, nut_row):
            contact = series_contact(tension, float(row @ pose), kwood, head_quad, wood_quad)
            energy += contact["energy_nmm"]
            gradient += contact["moment_nmm"] * row
            hessian += contact["tangent_nmm_per_rad"] * np.outer(row, row)
            ends.append(contact)
        return energy, gradient, hessian, relative, penetration, contact_forces, ends

    pose = np.zeros(36)
    if lateral > 1e-9:
        pose[:34:2] = gap
        pose[34] = 2*gap + lateral/(kwood*diameter*min(family["host_length_mm"], family["cleat_length_mm"]))
    converged = False
    for iteration in range(150):
        evaluation = evaluate(pose)
        energy, gradient, hessian = evaluation[:3]
        if float(np.max(np.abs(gradient))) <= 1e-6:
            converged = True
            break
        eigenvalues, eigenvectors = np.linalg.eigh(hessian)
        require(eigenvalues[0] >= -1e-9*max(1.0, eigenvalues[-1]), "Newton tangent is not numerically positive semidefinite")
        positive = eigenvalues > max(1.0, eigenvalues[-1])*1e-12
        projected = eigenvectors.T @ gradient
        inverse = np.full(36, 1/(kwood*diameter*LENGTH))
        inverse[positive] = 1/eigenvalues[positive]
        step = -eigenvectors @ (inverse * projected)
        slope = float(gradient @ step)
        require(slope < 0, "Newton step does not descend")
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose + fraction*step
            if evaluate(candidate)[0] <= energy + 1e-4*fraction*slope + 1e-12*max(1.0, abs(energy)):
                pose = candidate
                break
        else:
            raise ValueError("Armijo search stopped without a valid step")
    require(converged, "STOP: local equilibrium did not converge within 150 iterations")
    energy, gradient, hessian, relative, penetration, forces, ends = evaluate(pose)
    require(np.isfinite(pose).all(), "nonfinite local pose")
    residual_force = float(np.max(np.abs(gradient[np.r_[np.arange(0, 34, 2), 34]])))
    residual_moment = float(LENGTH*np.max(np.abs(gradient[np.r_[np.arange(1, 34, 2), 35]])))
    require(residual_force <= 1e-6 and residual_moment <= LENGTH*1e-6, "STOP: local force or moment residual exceeds the declared tolerance")
    area = math.pi * diameter**2 / 4
    beam_fields = []
    for element, location, indices, moment_row, shear_row in curvatures:
        moment, shear = float(moment_row @ pose[indices]), float(shear_row @ pose[indices])
        normal = abs(tension/area) + abs(moment)*diameter/(2*inertia)
        shear_stress = 4*abs(shear)/(3*area)
        proxy = math.sqrt(normal**2 + 3*shear_stress**2)
        beam_fields.append({"element": element, "x_mm": location, "EI_curvature_M_nmm": moment,
                            "EI_third_derivative_shear_n": shear, "axial_plus_bending_envelope_mpa": normal,
                            "round_section_shear_envelope_mpa": shear_stress, "nominal_smooth_von_mises_proxy_mpa": proxy,
                            "proxy_over_conditional_92ksi_Fyb": proxy/FYB_SCENARIO})
    bore_fields = [{"x_mm": sample[2], "receiver": sample[3], "relative_motion_mm": float(relative[index]),
                    "signed_penetration_mm": float(penetration[index]), "pressure_mpa": float(kwood*abs(penetration[index])),
                    "force_on_beam_n": float(-forces[index]), "quadrature_weight_mm": sample[1],
                    "pressure_over_conditional_Fe": float(kwood*abs(penetration[index])/source["Fe_mpa"][sample[3]])}
                   for index, sample in enumerate(samples)]
    host_indices = [index for index, sample in enumerate(samples) if sample[3] == "host"]
    host_reaction = float(np.sum(forces[host_indices]))
    host_bore_moment = float(sum(forces[index]*(samples[index][2] - family["host_length_mm"]) for index in host_indices))
    axial_stretch = tension*LENGTH/(E_BOLT*area)
    unit_geometric = geometric/tension if tension else beam_model(family, 1.0)[1]
    projected_shortening = float(0.5*pose @ unit_geometric @ pose)
    direction, rotation_axis = np.array(source["drive_unit_xyz"]), np.array(source["rotation_axis_xyz"])
    eigenvalues = np.linalg.eigvalsh(hessian)
    nullity = int(np.sum(eigenvalues <= max(1.0, eigenvalues[-1])*1e-12))
    for end in ends:
        end["wood_contact"]["peak_pressure_over_Fc_perp_diagnostic"] = end["wood_contact"]["pressure_peak_mpa"]/FC_PERP
        end["wood_contact"]["mean_pressure_over_Fc_perp_diagnostic"] = end["wood_contact"]["mean_pressure_full_annulus_mpa"]/FC_PERP
        end["moment_over_T_flat_radius"] = abs(end["moment_nmm"])/(tension*family["flat_radius_mm"]) if tension else None
    result = {**source, "Kwood_mpa_per_mm": kwood, "geometry": family, "radial_gap_mm": gap,
              "iterations": iteration, "energy_relative_to_zero_tilt_nmm": energy,
              "host_u_mm": float(pose[34]), "host_phi_rad": float(pose[35]/LENGTH),
              "host_translation_at_interface_xyz_mm": (pose[34]*direction).tolist(),
              "host_rotation_xyz_rad": (pose[35]/LENGTH*rotation_axis).tolist(),
              "beam_node_displacements_mm": pose[:34:2].tolist(), "beam_node_rotations_rad": (pose[1:34:2]/LENGTH).tolist(),
              "end_head": ends[0], "end_nut": ends[1], "axial_stretch_mm": axial_stretch,
              "small_angle_projected_axial_shortening_mm": projected_shortening,
              "linear_axial_separation_component_mm": axial_stretch + sum(end["total_closure_mm"] for end in ends),
              "required_axial_separation_mm": axial_stretch + sum(end["total_closure_mm"] for end in ends) - projected_shortening,
              "host_bore_reaction_n": host_reaction, "host_bore_reaction_xyz_n": (host_reaction*direction).tolist(),
              "host_force_balance_residual_n": host_reaction + lateral,
              "host_bore_moment_nmm": host_bore_moment, "host_moment_balance_residual_nmm": host_bore_moment + ends[0]["moment_nmm"],
              "maximum_nodal_force_residual_n": residual_force, "maximum_nodal_moment_residual_nmm": residual_moment,
              "scaled_gradient_residuals_n": gradient.tolist(), "tangent_nullity_at_tolerance": nullity,
              "representative_nonunique_pose": nullity > 0 or source["lateral_direction_arbitrary"],
              "peak_beam_stress_witness": max(beam_fields, key=lambda row: row["nominal_smooth_von_mises_proxy_mpa"]),
              "maximum_abs_EI_curvature_M_nmm": max(abs(row["EI_curvature_M_nmm"]) for row in beam_fields),
              "maximum_abs_EI_third_derivative_shear_n": max(abs(row["EI_third_derivative_shear_n"]) for row in beam_fields),
              "elastic_bolt_hypothesis_exceeded": any(row["proxy_over_conditional_92ksi_Fyb"] > 1 for row in beam_fields),
              "peak_bore_pressure_witness": max(bore_fields, key=lambda row: row["pressure_mpa"]),
              "actual_hardware_capacity_n": None, "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
              "coupled_joint_resistance_n": None, "common_host_compatibility_established": False,
              "complete_joint_acceptance": False, "physical_release": False}
    return result, beam_fields, bore_fields


def inputs():
    pins = dict(FROZEN)
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen input differs: {path}")
    receipt_path = REGISTER.parent / "source-pins.json"
    receipt = read(receipt_path)
    pins[receipt_path] = sha(receipt_path)
    for name, expected in receipt["output_sha256"].items():
        path = REGISTER.parent / name
        require(sha(path) == expected, f"register output pin differs: {path}")
        pins[path] = expected
    register, model, component, comparison = read(REGISTER), read(MODEL), read(COMPONENT), read(COMPARISON)
    require(register["case_ids"] == CASES and not register["complete_joint_acceptance"] and not register["physical_release"], "register scope differs")
    require(component["source_response_sha256"] == FROZEN[RESPONSE] and component["source_comparison_sha256"] == FROZEN[COMPARISON], "component force binding differs")
    require(comparison["response_sha256"] == FROZEN[RESPONSE], "current response binding differs")
    proposed = next(record["axes"] for record in model["proposed_corner_axes"] if record["block"] == "top_outer_right_cleat")
    geometry = {record["axis_id"]: record for record in proposed}
    require(set(geometry) == set(AXES), "corrected upper-right geometry census differs")
    all_axes = {record["axis_id"]: record for record in register["axes"]}
    components = {(record["case_id"], record["axis_id"]): record for record in component["states"]}
    states = []
    with np.load(RESPONSE, allow_pickle=False) as response:
        for axis_id in AXES:
            axis, revised = all_axes[axis_id], geometry[axis_id]
            family_name = "rail" if "/rail_" in axis_id else "side"
            family = FAMILIES[family_name]
            require(revised["wood_grip_mm"] == LENGTH and revised["nominal_bolt_diameter_mm"] == family["diameter_mm"] and revised["proposed_CAD_bore_envelope_mm"] == family["bore_mm"], "corrected bolt geometry differs")
            require(len(axis["interfaces"]) == 1, "upper-right axis is not a single-interface bolt")
            interface = axis["interfaces"][0]
            host = "base_rail_top" if family_name == "rail" else "base_side_right"
            require(set(interface["receivers"]) == {host, "top_outer_right_cleat"}, "current receiver pair differs")
            seats = {record["body"]: np.array(record["seat_point_mm"]) for record in component["washer_seats"] if record["axis_id"] == axis_id}
            bolt_axis = (seats["top_outer_right_cleat"] - seats[host])/LENGTH
            require(math.isclose(float(np.linalg.norm(bolt_axis)), 1.0, abs_tol=1e-8), "corrected seat grip is not 177.8 mm")
            require(np.allclose(seats[host] + family["host_length_mm"]*bolt_axis, interface["point_xyz_mm"], atol=1e-7, rtol=0),
                    "corrected receiver interface does not match the frozen force station")
            for state in axis["per_state"]:
                require(state["case_id"] in CASES and state["gap_scale"] == 1.0, "non-nominal input state")
                plane, case_id = state["interfaces"][0], state["case_id"]
                raw = response[case_id + "_gap_raw_force_n"]
                require(np.array_equal(raw[plane["component_rows"]], plane["components_n"]) and float(raw[state["outer_tie_row"]]) == state["outer_tie_signed_n"], "register raw forces differ")
                witness = components[case_id, axis_id]
                require(math.isclose(witness["tension_n"], state["outer_tie_signed_n"], abs_tol=1e-8) and math.isclose(witness["lateral_n"], plane["V_resultant_n"], abs_tol=1e-8), "component simultaneous demand differs")
                host_force = np.array(plane["force_on_first_xyz_n"] if interface["receivers"][0] == host else plane["force_on_second_xyz_n"])
                lateral = plane["V_resultant_n"]
                arbitrary = lateral <= 1e-9
                direction = -host_force/lateral if not arbitrary else np.array(interface["component_directions_xyz"][0])
                require(abs(float(direction @ bolt_axis)) < 1e-8, "lateral direction is not perpendicular to corrected bolt axis")
                states.append({"axis_id": axis_id, "case_id": case_id, "family": family_name,
                               "signed_T_n": state["outer_tie_signed_n"], "V_n": lateral,
                               "signed_plane_components_n": plane["components_n"], "plane_id": plane["plane_id"],
                               "component_rows": plane["component_rows"], "tie_row": state["outer_tie_row"],
                               "saved_connector_force_on_host_xyz_n": host_force.tolist(), "drive_unit_xyz": direction.tolist(),
                               "lateral_direction_arbitrary": arbitrary, "bolt_axis_head_to_nut_xyz": bolt_axis.tolist(),
                               "rotation_axis_xyz": np.cross(bolt_axis, direction).tolist(), "interface_point_xyz_mm": interface["point_xyz_mm"],
                               "corrected_proposed_axis_point_xyz_mm": revised["proposed_axis_point_mm"],
                               "Fe_mpa": dict(zip(("host", "cleat"), [value*PSI_TO_MPA for value in witness["reference"]["bearing_strengths_psi"]]))})
    require(len(states) == 24 and all(sum(state["axis_id"] == axis_id for state in states) == 6 for axis_id in AXES), "upper-right state census differs")
    states.sort(key=lambda state: (CASES.index(state["case_id"]), AXES.index(state["axis_id"])))
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    return states, pins


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    output = parser.parse_args().output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    sources, pins = inputs()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, beam_rows, bore_rows, failure = [], [], [], None
    try:
        for source in sources:
            for branch in K_BRANCHES:
                record, beam, bore = solve_state(source, FAMILIES[source["family"]], branch)
                states.append(record)
                identity = {"case_id": source["case_id"], "axis_id": source["axis_id"], "Kwood_mpa_per_mm": branch}
                beam_rows.extend({**identity, **row} for row in beam)
                bore_rows.extend({**identity, **row} for row in bore)
        for path, expected in pins.items():
            require(sha(path) == expected, f"source changed during local calculation: {path}")
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"case_id": source["case_id"], "axis_id": source["axis_id"], "Kwood_mpa_per_mm": branch,
                   "source_state": source, "error": str(error)}
    if beam_rows:
        write_csv(output / "beam-fields.csv", beam_rows)
        write_csv(output / "bore-fields.csv", bore_rows)
        write_csv(output / "states.csv", [{key: state[key] for key in (
            "case_id", "axis_id", "Kwood_mpa_per_mm", "signed_T_n", "V_n", "host_u_mm", "host_phi_rad",
            "required_axial_separation_mm", "maximum_abs_EI_curvature_M_nmm", "maximum_abs_EI_third_derivative_shear_n",
            "host_force_balance_residual_n", "host_moment_balance_residual_nmm", "elastic_bolt_hypothesis_exceeded")}
            | {"peak_nominal_smooth_von_mises_proxy_mpa": state["peak_beam_stress_witness"]["nominal_smooth_von_mises_proxy_mpa"],
               "peak_pressure_over_conditional_Fe": max(row["pressure_over_conditional_Fe"] for row in bore_rows
                                                         if row["case_id"] == state["case_id"] and row["axis_id"] == state["axis_id"] and row["Kwood_mpa_per_mm"] == state["Kwood_mpa_per_mm"])}
            for state in states])
    result = {"schema": "upper_right_independent_combined_transfer_sensitivity/v1", "status": "STOP" if failure else "FINITE_HYPOTHETICAL_LOCAL_RESULTS",
              "counts": {"source_states": 24, "stiffness_branches": 3, "completed_local_states": len(states), "expected_local_states": 72},
              "case_ids": CASES, "axis_ids": AXES, "states": states, "failure": failure,
              "model": {"beam": "Euler-Bernoulli, 8 elements per receiver, 17 nodes; rotations scaled by 177.8 mm",
                        "E_bolt_mpa_hypothesis": E_BOLT, "K_head_contact_mpa_per_mm_hypothesis": K_HEAD,
                        "Kwood_mpa_per_mm_hypotheses": K_BRANCHES, "bore_quadrature": "3 Gauss points per element",
                        "annulus_quadrature": "8 Gauss radii and 32 uniform azimuths", "washer_rigid_hypothesis": True,
                        "positive_tension_geometric_stiffness": True, "force_tolerance_n": 1e-6, "moment_tolerance_nmm": LENGTH*1e-6,
                        "no_preload": True, "conditional_Fyb_comparison_mpa": FYB_SCENARIO, "wood_reference_Fc_perp_mpa": FC_PERP},
              "limits": ["All four stacks are independent. Returned relative host poses do not establish a common-host or complete-joint displacement solution.",
                         "External local host drive is the negative of the saved connector force on that host; the cleat receiver is rigid and fixed.",
                         "Wood and head contact stiffnesses and smooth bolt elasticity are hypothetical. Bore pressure peaks are quadrature samples, not a continuum bound.",
                         "Bore pressure/Fe and washer wood pressure/Fc-perpendicular values are diagnostic comparisons with the frozen component references, not design demand/capacity ratios.",
                         "The nominal smooth-section stress proxy combines axial/bending and round-section shear envelopes at the same axial location; it is not a qualified coupled NDS capacity.",
                         "A proxy above the conditional steel comparison invalidates that elastic material hypothesis; it is not an observed physical failure.",
                         "Rigid washers transmit moment without supplying washer stress or resistance. Actual head/nut bearing profiles, steel resistance, thread-bearing intervals and installed support remain unqualified.",
                         "Signed seat closures plus elastic bolt stretch minus small-angle projected shortening define this model's required axial separation; no installed frame fit or seating motion envelope is established.",
                         "Frozen simultaneous forces are reused without a frame solve, native solve, CAD operation, historical force transfer or changed geometry."],
              "source_sha256": {str(path.relative_to(ROOT)): expected for path, expected in sorted(pins.items())},
              "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
              "actual_hardware_capacity_n": None, "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
              "complete_joint_acceptance": False, "physical_release": False}
    generated = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = generated.copy()
    dump(output / "checks.json", result)
    generated["checks.json"] = sha(output / "checks.json")
    dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": generated,
                                       "complete_joint_acceptance": False, "physical_release": False})
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before receipt completion: {path}")
    print(json.dumps({"status": result["status"], "completed": len(states), "checks_sha256": generated["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
