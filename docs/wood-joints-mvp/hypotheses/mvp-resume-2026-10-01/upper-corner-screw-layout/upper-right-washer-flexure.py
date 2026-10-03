"""Evaluate prescribed current washer end T/M with a free-edge Mindlin Ritz plate."""

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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
HELPER = HERE / "upper-right-combined-transfer.py"
RAIL = HERE / "rawlocal/upper-right-rail-pair/attempt01/checks.json"
SIDE = HERE / "rawlocal/upper-right-side-pair/attempt01/checks.json"
PINS = {
    HELPER: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    RAIL: "e0cccb56abb94ed16c322da888cd64a9904c4e49d1e34f573a6903c8b8b98d3d",
    SIDE: "b507a5a501737c89814a471eee6a12749a3c54224f5444b2c5d583020e875ba7",
    HERE / "upper-right-rail-pair.py": "4243b53bbb7377753f0b1fdd73fa1aa6c80e1a96c99d428def88e82a899e6f96",
    HERE / "upper-right-side-pair.py": "ce07e9489d96fb251ee780ecb96cdbb38539b5d204922a74c39066095d9ac0cc",
}
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
FAMILIES = {
    "rail": {"inner_radius_mm": 8.3058/2, "outer_radius_mm": 18.4658/2,
             "head_radius_mm": 5.0, "thickness_mm": 1.2954},
    "side": {"inner_radius_mm": 9.906/2, "outer_radius_mm": 22.0472/2,
             "head_radius_mm": 6.0, "thickness_mm": 1.6256},
}
ESTEEL, NU, KWOOD, KHEAD, FY_HYPOTHESIS = 200000.0, 0.3, 20.0, 10000.0, 250.0
GRADIENT_TOLERANCE, FORCE_TOLERANCE, MOMENT_TOLERANCE = 1e-4, 0.001, 0.02
ENERGY_SOURCE = "https://docu.ngsolve.org/ngs24/SaS/plates_derivation.html"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")


def load_sources():
    pins = dict(PINS)
    authenticate(pins)
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_washer_contact", HELPER)
    require(spec is not None and spec.loader is not None, "pure annulus helper unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    documents = {name: json.loads(path.read_text()) for name, path in (("rail", RAIL), ("side", SIDE))}
    for name, document in documents.items():
        require(document["schema"] == f"upper_right_common_host_{name}_pair_sensitivity/v1"
                and document["counts"]["completed_cases"] == 6 and document["failure"] is None,
                "source pair packet is incomplete")
        require(document["case_ids"] == CASES and not document["complete_joint_acceptance"]
                and not document["physical_release"], "source case order or claim boundary differs")
        producer = HERE / f"upper-right-{name}-pair.py"
        require(document["output_sha256"]["producer.py.snapshot"] == pins[producer], "pair producer binding differs")
        geometry, family = document["model"]["geometry"], FAMILIES[name]
        require(geometry["washer_ID_max_mm"]/2 == family["inner_radius_mm"]
                and geometry["washer_OD_min_mm"]/2 == family["outer_radius_mm"]
                and geometry["flat_radius_mm"] == family["head_radius_mm"], "source washer radii differ")
        for relative, digest in document["source_sha256"].items():
            path = ROOT / relative
            require(path not in pins or pins[path] == digest, "source pair pins conflict")
            pins[path] = digest
    authenticate(pins)
    records = []
    for case_id in CASES:
        for name, document in documents.items():
            state = next(state for state in document["states"] if state["case_id"] == case_id)
            basis = np.array(document["model"]["transverse_basis_xyz"])
            for bolt in state["bolts"]:
                require(bolt["compatible_T_n"] >= 0 and len(bolt["end_contacts"]) == 2, "source axial or end census differs")
                for end_index, role in enumerate(("host", "cleat")):
                    contact = bolt["end_contacts"][end_index]
                    moment_vector = np.array(bolt["end_moment_vectors_in_transverse_basis_nmm"][end_index])
                    slope_vector = np.array(bolt["end_slope_vectors_rad"][end_index])
                    moment = float(np.linalg.norm(moment_vector))
                    require(math.isclose(moment, contact["moment_nmm"], abs_tol=1e-7), "source end moment differs")
                    direction = moment_vector/moment if moment > 0 else (
                        slope_vector/np.linalg.norm(slope_vector) if np.linalg.norm(slope_vector) > 0 else np.array([1.0, 0.0]))
                    records.append({"state_id": f"{case_id}/{bolt['axis_id']}/{role}", "case_id": case_id,
                                    "axis_id": bolt["axis_id"], "end_role": role, "family": name,
                                    "source_pair_checks_sha256": pins[RAIL if name == "rail" else SIDE],
                                    "T_n": bolt["compatible_T_n"], "M_magnitude_nmm": moment,
                                    "source_signed_M_vector_in_pair_basis_nmm": moment_vector.tolist(),
                                    "source_signed_slope_vector_in_pair_basis_rad": slope_vector.tolist(),
                                    "source_moment_on_beam_xyz_nmm": contact["moment_on_beam_xyz_nmm"],
                                    "local_positive_x_global_xyz": (basis @ direction).tolist(),
                                    "source_bolt_axis_head_to_nut_xyz": bolt["bolt_axis_head_to_nut_xyz"],
                                    "saved_rigid_contact": contact})
    require(len(records) == 48 and len({record["state_id"] for record in records}) == 48, "washer end-state census differs")
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    return helper, records, pins


def quadrature(helper, inner, outer):
    area, x, radius = helper.annulus(inner, outer)
    abscissa, weights = np.polynomial.legendre.leggauss(8)
    radii = inner + (abscissa + 1)*(outer - inner)/2
    angles = (np.arange(32) + 0.5)*(2*math.pi/32)
    expected_area = np.repeat(radii*weights*(outer - inner)/2*(2*math.pi/32), 32)
    expected_x = (radii[:, None]*np.cos(angles)).ravel()
    y = (radii[:, None]*np.sin(angles)).ravel()
    require(radius == outer and np.allclose(area, expected_area, atol=1e-13, rtol=0)
            and np.allclose(x, expected_x, atol=1e-13, rtol=0), "frozen annulus quadrature mapping differs")
    require(math.isclose(float(np.sum(area)), math.pi*(outer**2 - inner**2), abs_tol=1e-10), "annulus quadrature area differs")
    return area, x, y


def field_maps(x, y, outer, monomials):
    normalized_x, normalized_y = np.asarray(x)/outer, np.asarray(y)/outer
    phi = np.column_stack([normalized_x**i*normalized_y**j for i, j in monomials])
    dx = np.column_stack([i*normalized_x**(i - 1)*normalized_y**j/outer if i else np.zeros_like(normalized_x)
                          for i, j in monomials])
    dy = np.column_stack([j*normalized_x**i*normalized_y**(j - 1)/outer if j else np.zeros_like(normalized_y)
                          for i, j in monomials])
    count, width = len(monomials), 3*len(monomials) + 3
    w, beta = np.zeros((len(x), width)), np.zeros((len(x), 2, width))
    w[:, :count] = phi
    beta[:, 0, count:2*count], beta[:, 1, 2*count:3*count] = phi/outer, phi/outer
    curvature, shear = np.zeros((len(x), 3, width)), np.zeros((len(x), 2, width))
    curvature[:, 0, count:2*count], curvature[:, 1, 2*count:3*count] = dx/outer, dy/outer
    curvature[:, 2, count:2*count], curvature[:, 2, 2*count:3*count] = dy/outer, dx/outer
    shear[:, 0, :count], shear[:, 1, :count] = dx, dy
    shear -= beta
    head = np.zeros((len(x), width))
    head[:, -3:] = np.column_stack((np.ones(len(x)), normalized_x, normalized_y))
    return {"w": w, "beta": beta, "curvature": curvature, "shear": shear, "head": head}


def make_model(helper, family, degree, full_head=False):
    inner, outer, thickness = (family[key] for key in ("inner_radius_mm", "outer_radius_mm", "thickness_mm"))
    monomials = [(i, total - i) for total in range(degree + 1) for i in range(total + 1)]
    wood = quadrature(helper, inner, outer)
    head = quadrature(helper, inner, outer if full_head else family["head_radius_mm"])
    wood_maps, head_maps = (field_maps(q[1], q[2], outer, monomials) for q in (wood, head))
    rigidity = ESTEEL*thickness**3/(12*(1 - NU**2))
    constitutive = rigidity*np.array([[1.0, NU, 0.0], [NU, 1.0, 0.0], [0.0, 0.0, (1 - NU)/2]])
    shear_rigidity = (5/6)*ESTEEL/(2*(1 + NU))*thickness
    bending = np.einsum("n,nai,ab,nbj->ij", wood[0], wood_maps["curvature"], constitutive, wood_maps["curvature"])
    shear = shear_rigidity*np.einsum("n,nai,naj->ij", wood[0], wood_maps["shear"], wood_maps["shear"])
    stiffness = bending + shear
    width, count = len(stiffness), len(monomials)
    rigid_modes = []
    for role in ("constant", "global_x", "global_y"):
        mode = np.zeros(width)
        if role == "constant":
            mode[monomials.index((0, 0))] = 1.0
        else:
            direction = (1, 0) if role == "global_x" else (0, 1)
            mode[monomials.index(direction)] = outer
            mode[(count if role == "global_x" else 2*count) + monomials.index((0, 0))] = outer
        energy = float(0.5*mode @ stiffness @ mode)
        residual = float(np.max(np.abs(stiffness @ mode)))
        require(abs(energy) <= 1e-7 and residual <= 1e-7, "plate matrix supplies artificial rigid-mode stiffness")
        rigid_modes.append({"mode": role, "matrix_energy_nmm": energy, "matrix_action_maximum_n": residual})
    return {"family": family, "degree": degree, "monomials": monomials, "width": width,
            "wood_quad": wood, "head_quad": head, "wood_maps": wood_maps, "head_maps": head_maps,
            "head_relative": head_maps["head"] - head_maps["w"], "stiffness": stiffness,
            "bending_stiffness": bending, "shear_stiffness": shear, "constitutive": constitutive,
            "shear_rigidity": shear_rigidity, "rigid_mode_diagnostics": rigid_modes}


def evaluate(model, pose, drive):
    energy = float(0.5*pose @ model["stiffness"] @ pose - drive @ pose)
    gradient, tangent = model["stiffness"] @ pose - drive, model["stiffness"].copy()
    pressures = []
    for area, mapping, stiffness in ((model["wood_quad"][0], model["wood_maps"]["w"], KWOOD),
                                     (model["head_quad"][0], model["head_relative"], KHEAD)):
        indentation = np.maximum(mapping @ pose, 0.0)
        pressure = stiffness*indentation
        energy += float(0.5*stiffness*np.sum(area*indentation**2))
        gradient += mapping.T @ (area*pressure)
        active = indentation > 0
        tangent += mapping[active].T @ ((stiffness*area[active])[:, None]*mapping[active])
        pressures.append(pressure)
    return energy, gradient, (tangent + tangent.T)/2, pressures


def drive_vector(model, tension, moment):
    drive = np.zeros(model["width"])
    drive[-3:] = [tension, moment/model["family"]["outer_radius_mm"], 0.0]
    return drive


def contact_balance(model, pressures, tension, moment):
    records = []
    for name, quad, pressure in zip(("wood", "head"), (model["wood_quad"], model["head_quad"]), pressures):
        area, x, y = quad
        force = float(area @ pressure)
        moments = [float((area*x) @ pressure), float((area*y) @ pressure)]
        records.append({"contact": name, "force_n": force, "first_moments_nmm": moments,
                        "force_residual_n": force - tension, "moment_residuals_nmm": [moments[0] - moment, moments[1]],
                        "active_area_mm2": float(np.sum(area[pressure > 0])), "full_area_mm2": float(np.sum(area)),
                        "pressure_peak_mpa": float(np.max(pressure)), "mean_full_area_pressure_mpa": force/float(np.sum(area))})
    return records


def energy_record(model, pose, drive, pressures):
    bending = float(0.5*pose @ model["bending_stiffness"] @ pose)
    shear = float(0.5*pose @ model["shear_stiffness"] @ pose)
    wood = float(0.5*np.sum(model["wood_quad"][0]*pressures[0]**2)/KWOOD)
    head = float(0.5*np.sum(model["head_quad"][0]*pressures[1]**2)/KHEAD)
    work = float(drive @ pose)
    return {"bending_energy_nmm": bending, "shear_energy_nmm": shear,
            "wood_contact_energy_nmm": wood, "head_contact_energy_nmm": head,
            "load_work_nmm": work, "energy_identity_residual_nmm": work - 2*(bending + shear + wood + head)}


def coupon(helper, degree, debug):
    model = make_model(helper, FAMILIES["rail"], degree, full_head=True)
    pose, count = np.zeros(model["width"]), len(model["monomials"])
    area = float(np.sum(model["wood_quad"][0]))
    wood_closure, head_closure = 100/(KWOOD*area), 100/(KHEAD*area)
    pose[model["monomials"].index((0, 0))], pose[3*count] = wood_closure, wood_closure + head_closure
    energy, gradient, tangent, pressures = evaluate(model, pose, drive_vector(model, 100.0, 0.0))
    balances = contact_balance(model, pressures, 100.0, 0.0)
    energies = energy_record(model, pose, drive_vector(model, 100.0, 0.0), pressures)
    bending = float(0.5*pose @ model["bending_stiffness"] @ pose)
    shear = float(0.5*pose @ model["shear_stiffness"] @ pose)
    debug.update({"stage": "full-face-coupon", "scaled_variables_mm": pose.tolist(), "energy_nmm": energy,
                  "scaled_gradient_components_n": gradient.tolist(), "contact_balances": balances,
                  "bending_energy_nmm": bending, "shear_energy_nmm": shear,
                  "rigid_mode_diagnostics": model["rigid_mode_diagnostics"]})
    require(np.max(np.abs(gradient)) <= GRADIENT_TOLERANCE and abs(bending) <= 1e-10 and abs(shear) <= 1e-10,
            "full-face pressure coupon energy or gradient differs from its exact solution")
    require(all(np.max(np.abs(pressure - 100/area)) <= 1e-10 for pressure in pressures), "coupon pressure is not uniform")
    require(all(abs(contact["force_residual_n"]) <= FORCE_TOLERANCE
                and np.max(np.abs(contact["moment_residuals_nmm"])) <= MOMENT_TOLERANCE for contact in balances),
            "coupon force or first-moment balance differs from its exact solution")
    eigenvalues = np.linalg.eigvalsh(tangent)
    require(eigenvalues[0] >= -1e-10*max(1.0, eigenvalues[-1]), "coupon contact tangent is not positive semidefinite")
    return {"method_question": "Confirm contact signs, dimensional energy and preservation of the plate's three rigid modes.",
            "T_n": 100.0, "M_nmm": 0.0, "full_face_head_footprint": True, "area_mm2": area,
            "exact_w_mm": wood_closure, "exact_head_closure_mm": wood_closure + head_closure,
            "exact_uniform_pressure_mpa": 100/area, **energies,
            "total_potential_energy_nmm": energy, "mixed_scaled_gradient_maximum_n": float(np.max(np.abs(gradient))),
            "contact_balances": balances, "rigid_mode_diagnostics": model["rigid_mode_diagnostics"],
            "tangent_minimum_eigenvalue_n_per_mm": float(eigenvalues[0]), "coupon_satisfied": True}


def recover_fields(model, pose, source):
    inner, outer, thickness = (model["family"][key] for key in ("inner_radius_mm", "outer_radius_mm", "thickness_mm"))
    area, x, y = model["wood_quad"]
    affine = np.column_stack((np.ones(len(x)), x/outer, y/outer))
    wood_w = model["wood_maps"]["w"] @ pose
    rigid_plane = np.linalg.lstsq(np.sqrt(area)[:, None]*affine, np.sqrt(area)*wood_w, rcond=None)[0]
    angles = np.arange(64)*(2*math.pi/64)
    radii = np.linspace(inner, outer, 33)
    dense = ((radii[:, None]*np.cos(angles)).ravel(), (radii[:, None]*np.sin(angles)).ravel())
    rows = []
    for sample_set, sample_x, sample_y in (("wood_quadrature", x, y),
                                          ("head_quadrature", model["head_quad"][1], model["head_quad"][2]),
                                          ("dense_radial_edges_included", *dense)):
        maps = field_maps(sample_x, sample_y, outer, model["monomials"])
        w, beta = maps["w"] @ pose, np.einsum("nai,i->na", maps["beta"], pose)
        moments = np.einsum("ab,nbi,i->na", model["constitutive"], maps["curvature"], pose)
        shears = model["shear_rigidity"]*np.einsum("nai,i->na", maps["shear"], pose)
        stresses = 6*moments/thickness**2
        face_vm = np.sqrt(stresses[:, 0]**2 - stresses[:, 0]*stresses[:, 1] + stresses[:, 1]**2 + 3*stresses[:, 2]**2)
        midplane_vm = math.sqrt(3)*3*np.linalg.norm(shears, axis=1)/(2*thickness)
        nonaffine = w - np.column_stack((np.ones(len(sample_x)), sample_x/outer, sample_y/outer)) @ rigid_plane
        wood_pressure = KWOOD*np.maximum(w, 0.0)
        head_pressure = KHEAD*np.maximum((maps["head"] - maps["w"]) @ pose, 0.0)
        head_pressure[np.hypot(sample_x, sample_y) > model["family"]["head_radius_mm"] + 1e-12] = 0.0
        for index in range(len(sample_x)):
            rows.append({"state_id": source["state_id"], "sample_set": sample_set,
                         "x_mm": float(sample_x[index]), "y_mm": float(sample_y[index]), "w_mm": float(w[index]),
                         "beta_components_rad": beta[index].tolist(), "non_affine_w_mm": float(nonaffine[index]),
                         "bending_resultants_n": moments[index].tolist(), "shear_resultants_n_per_mm": shears[index].tolist(),
                         "face_stress_components_mpa": stresses[index].tolist(), "face_von_mises_mpa": float(face_vm[index]),
                         "midplane_parabolic_shear_von_mises_proxy_mpa": float(midplane_vm[index]),
                         "sampled_through_thickness_maximum_proxy_mpa": float(max(face_vm[index], midplane_vm[index])),
                         "wood_pressure_mpa": float(wood_pressure[index]), "head_pressure_mpa": float(head_pressure[index])})
    wood_nonaffine = wood_w - affine @ rigid_plane
    return rows, {"weighted_best_fit_rigid_plane_mm": rigid_plane.tolist(),
                  "non_affine_w_weighted_rms_mm": float(np.sqrt(np.sum(area*wood_nonaffine**2)/np.sum(area))),
                  "non_affine_w_peak_witness": max(rows, key=lambda row: abs(row["non_affine_w_mm"])),
                  "sampled_stress_peak_witness": max(rows, key=lambda row: row["sampled_through_thickness_maximum_proxy_mpa"]),
                  "sampled_deflection_peak_witness": max(rows, key=lambda row: abs(row["w_mm"])),
                  "sampled_deflection_minimum_mm": min(row["w_mm"] for row in rows),
                  "sampled_deflection_maximum_mm": max(row["w_mm"] for row in rows)}


def solve_state(model, source, debug):
    pose, count = np.zeros(model["width"]), len(model["monomials"])
    outer, rigid = model["family"]["outer_radius_mm"], source["saved_rigid_contact"]
    constant, linear_x = model["monomials"].index((0, 0)), model["monomials"].index((1, 0))
    pose[constant], pose[linear_x] = rigid["wood_contact"]["closure_mm"], outer*rigid["wood_contact"]["tilt_rad"]
    pose[count + constant] = outer*rigid["wood_contact"]["tilt_rad"]
    pose[-3:] = [rigid["total_closure_mm"], outer*rigid["relative_tilt_rad"], 0.0]
    initial, drive = pose.copy(), drive_vector(model, source["T_n"], source["M_magnitude_nmm"])
    for iteration in range(101):
        energy, gradient, tangent, pressures = evaluate(model, pose, drive)
        debug.update({"iteration": iteration, "scaled_variables_mm": pose.tolist(), "energy_nmm": energy,
                      "scaled_gradient_components_n": gradient.tolist(), "scaled_gradient_maximum_n": float(np.max(np.abs(gradient))),
                      "contact_balances": contact_balance(model, pressures, source["T_n"], source["M_magnitude_nmm"])})
        require(np.isfinite(energy) and np.isfinite(gradient).all(), "nonfinite washer energy or gradient")
        eigenvalues, eigenvectors = np.linalg.eigh(tangent)
        require(eigenvalues[0] >= -1e-10*max(1.0, eigenvalues[-1]), "washer tangent is not numerically positive semidefinite")
        if np.max(np.abs(gradient)) <= GRADIENT_TOLERANCE:
            break
        require(iteration < 100, "STOP: washer equilibrium did not converge within 100 Newton steps")
        active = eigenvalues > max(1.0, eigenvalues[-1])*1e-12
        inverse = np.full(model["width"], 1/(KWOOD*np.sum(model["wood_quad"][0])))
        inverse[active] = 1/eigenvalues[active]
        step = -eigenvectors @ (inverse*(eigenvectors.T @ gradient))
        descent = float(gradient @ step)
        require(descent < 0, "washer Newton direction does not descend")
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose + fraction*step
            if evaluate(model, candidate, drive)[0] <= energy + 1e-4*fraction*descent + 1e-12*max(1.0, abs(energy)):
                pose = candidate
                break
        else:
            raise ValueError("STOP: washer Armijo search found no acceptable step")
    balances = contact_balance(model, pressures, source["T_n"], source["M_magnitude_nmm"])
    require(all(abs(contact["force_residual_n"]) <= FORCE_TOLERANCE
                and np.max(np.abs(contact["moment_residuals_nmm"])) <= MOMENT_TOLERANCE for contact in balances),
            "washer contact force or first-moment residual exceeds its declared tolerance")
    fields, witnesses = recover_fields(model, pose, source)
    energies = energy_record(model, pose, drive, pressures)
    for contact, key in zip(balances, ("wood_contact", "head_contact")):
        contact["active_area_minus_saved_rigid_mm2"] = contact["active_area_mm2"] - rigid[key]["active_area_mm2"]
        contact["peak_pressure_minus_saved_rigid_mpa"] = contact["pressure_peak_mpa"] - rigid[key]["pressure_peak_mpa"]
    head_tilt = pose[-2:]/outer
    return {**source, **witnesses, "degree": model["degree"], "iterations": iteration,
            "scaled_unknowns": model["width"], "scaled_variables_mm": pose.tolist(), "initial_scaled_variables_mm": initial.tolist(),
            "energy_nmm": energy, **energies,
            "scaled_gradient_maximum_n": float(np.max(np.abs(gradient))), "scaled_gradient_components_n": gradient.tolist(),
            "contact_balances": balances, "head_closure_mm": float(pose[-3]), "head_tilt_components_rad": head_tilt.tolist(),
            "head_tilt_magnitude_rad": float(np.linalg.norm(head_tilt)),
            "head_closure_minus_saved_rigid_mm": float(pose[-3] - rigid["total_closure_mm"]),
            "head_tilt_minus_saved_rigid_rad": float(np.linalg.norm(head_tilt) - rigid["relative_tilt_rad"]),
            "tangent_minimum_eigenvalue_n_per_mm": float(eigenvalues[0]),
            "tangent_nullity_at_relative_1e_12": int(np.sum(eigenvalues <= max(1.0, eigenvalues[-1])*1e-12)),
            "elastic_Fy_250MPa_hypothesis_exceeded": witnesses["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"] > FY_HYPOTHESIS,
            "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
            "complete_joint_acceptance": False, "physical_release": False}, fields


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def csv_rows(stream, rows, writer=None):
    if writer is None:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
    writer.writerows({key: json.dumps(value, separators=(",", ":")) if isinstance(value, (list, dict)) else value
                     for key, value in row.items()} for row in rows)
    return writer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--degree", type=int, choices=(4, 6), default=4)
    parser.add_argument("--state-id", help="Exact saved end-state ID; required for the single degree-6 refinement.")
    parser.add_argument("--coupon-only", action="store_true", help="Write the one full-face engineering coupon and matrix diagnostics only.")
    args = parser.parse_args()
    require((args.degree == 4 and args.state_id is None) or (args.degree == 6 and args.state_id is not None),
            "use degree 4 for the finite batch or degree 6 for one identified governing state")
    require(not args.coupon_only or args.degree == 4, "the single production coupon uses degree 4")
    output = args.output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    helper, all_sources, pins = load_sources()
    sources = [source for source in all_sources if args.state_id is None or source["state_id"] == args.state_id]
    require(len(sources) == (48 if args.state_id is None else 1), "requested saved state ID is unavailable")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    models, states, coupon_record, failure, source, debug = {}, [], None, None, None, {"stage": "matrix-preparation"}
    with (output / "fields.csv").open("w", newline="") as field_stream:
        writer = None
        try:
            for name, family in FAMILIES.items():
                debug["family"] = name
                models[name] = make_model(helper, family, args.degree)
            coupon_record = coupon(helper, 4, debug)
            if not args.coupon_only:
                for source in sources:
                    debug = {}
                    state, fields = solve_state(models[source["family"]], source, debug)
                    states.append(state)
                    writer = csv_rows(field_stream, fields, writer)
            authenticate(pins)
        except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
            failure = {"state_id": source["state_id"] if source else "full-face-coupon",
                       "source_T_M_n_nmm": [source["T_n"], source["M_magnitude_nmm"]] if source else [100.0, 0.0],
                       "last_accepted_state": debug, "error": str(error), "incompatibility_proved": False}
    if states:
        with (output / "states.csv").open("w", newline="") as stream:
            csv_rows(stream, [{key: state[key] for key in (
                "state_id", "family", "T_n", "M_magnitude_nmm", "degree", "iterations", "scaled_gradient_maximum_n",
                "head_closure_mm", "head_tilt_magnitude_rad", "head_closure_minus_saved_rigid_mm", "head_tilt_minus_saved_rigid_rad",
                "non_affine_w_weighted_rms_mm", "sampled_stress_peak_witness", "contact_balances",
                "elastic_Fy_250MPa_hypothesis_exceeded")} for state in states])
    result = {"schema": "upper_right_free_edge_mindlin_washer_flexure/v1",
              "status": "STOP" if failure else ("ENGINEERING_COUPON_ONLY" if args.coupon_only else "FINITE_WASHER_FLEXURE_HYPOTHESIS"),
              "counts": {"frozen_source_end_states": 48, "requested_end_states": 0 if args.coupon_only else len(sources),
                         "completed_end_states": len(states)}, "case_ids": CASES, "states": states,
              "engineering_coupon": coupon_record, "failure": failure,
              "model": {"families": FAMILIES, "degree": args.degree,
                        "normalized_monomials": [(i, total - i) for total in range(args.degree + 1) for i in range(total + 1)],
                        "scaled_unknowns": 3*((args.degree + 1)*(args.degree + 2)//2) + 3,
                        "E_mpa_hypothesis": ESTEEL, "nu_hypothesis": NU, "Fy_mpa_hypothesis": FY_HYPOTHESIS,
                        "Kwood_mpa_per_mm_hypothesis": KWOOD, "Khead_mpa_per_mm_hypothesis": KHEAD,
                        "shear_correction_factor": 5/6, "energy_primary_source": ENERGY_SOURCE,
                        "energy_source_locator": "Sections 8.1.1, dimensional thickness-integrated energy and 5/6 shear correction; free boundary conditions.",
                        "energy": ".5 integral[kappa.C.kappa + (5/6)Gt |gradw-beta|^2] + .5 Kwood sumA max(w,0)^2 + .5 Khead sumA max(h-w,0)^2 - [T,M/ro,0].h",
                        "scaling": "w=phi.cw; betaX/Y=phi.cbX/Y/ro; h=h0+hX*(x/ro)+hY*(y/ro); all coefficients are in mm.",
                        "radial_edge_conditions": "Both radial edges are free natural boundaries; no w or beta constraint is imposed.",
                        "end_role_definition": "Host and cleat identify the two source receiver ends. Each has the same hypothetical circular pressing profile; delivered head/nut placement is not inferred.",
                        "contact_quadrature": "Frozen 8 Gauss radii by 32 midpoint azimuths, separately on the wood and head annuli.",
                        "dense_evaluation_grid": {"radial_stations": 33, "azimuths": 64, "both_radial_edges_included": True},
                        "stress_recovery": "Face VM from 6M/t^2; midplane shear VM proxy sqrt(3)*3|Q|/(2t), with explicitly parabolic shear recovery. The sampled proxy is their maximum at each location.",
                        "rigid_mode_diagnostics": {name: model["rigid_mode_diagnostics"] for name, model in models.items()},
                        "scaled_gradient_tolerance_n": GRADIENT_TOLERANCE, "contact_force_tolerance_n": FORCE_TOLERANCE,
                        "contact_first_moment_tolerance_nmm": MOMENT_TOLERANCE,
                        "maximum_newton_steps": 100, "maximum_armijo_backtracks_per_step": 50,
                        "initialization": "Saved same-state rigid wood closure/tilt and total head closure/tilt supply a numerical seed only."},
              "limits": ["Prescribed T and each end's own M come from the exact frozen shared-host pair state. Washer flexure is not fed back into the beam/pair equilibrium.",
                         "The isotropic annulus is rotated to align local +x with the saved end moment/slope direction. Full signed pair-basis vectors and the source global beam moment remain recorded.",
                         "Free-edge and unilateral contact equilibrium are Ritz approximations; sampled stress and contact areas have no continuum convergence guarantee.",
                         "The polynomial beta space contains gradw. This avoids imposing an incompatible Kirchhoff slope constraint; finite-degree stress convergence remains conditional.",
                         "The shell model excludes sigmaZZ, local three-dimensional head/contact-edge stress, plasticity, membrane/geometric nonlinearity, preload and friction.",
                         "Face bending and midplane shear peaks occur at different thickness positions and are compared separately rather than added together.",
                         "E, nu and 250 MPa yield are explicit hypotheses. Exceeding this comparison invalidates the linear-elastic material hypothesis; it is not an observed hardware failure or catalog resistance.",
                         "The one full-face coupon checks signs and the three matrix rigid modes. It does not validate the candidate's unilateral flexure/stress field.",
                         "A numerical STOP preserves the last accepted iterate and does not prove mechanical incompatibility. No relaxed retry, native/frame solve, CAD operation or geometry change is performed."],
              "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())},
              "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
              "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None, "actual_washer_yield_mpa": None,
              "coupled_joint_resistance_n": None, "complete_joint_acceptance": False, "physical_release": False}
    hashes = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    dump(output / "checks.json", result)
    hashes["checks.json"] = sha(output / "checks.json")
    dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes,
                                       "complete_joint_acceptance": False, "physical_release": False})
    authenticate(pins)
    print(json.dumps({"status": result["status"], "completed_end_states": len(states), "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
