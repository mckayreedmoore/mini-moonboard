"""Evaluate one frozen washer end with a sparse polar Mindlin/contact approximation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import scipy
from scipy import sparse
from scipy.sparse.linalg import splu

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
FLEXURE = HERE / "upper-right-washer-flexure.py"
FLEXURE_SHA256 = "782ded96afd5e02e27873bd72b77073a643ed7c2a7946703a3240b1f51b21eac"
STATE_ID = "k12-right/top_outer/clip_single_top_right_2/rail_1/host"
RESOLUTIONS = {
    "coarse": {"inside_elements": 2, "outside_elements": 6, "fourier_order": 4, "angles": 64, "unknowns": 318},
    "fine": {"inside_elements": 4, "outside_elements": 12, "fourier_order": 8, "angles": 128, "unknowns": 1142},
}
GRADIENT_TOLERANCE, FORCE_TOLERANCE, MOMENT_TOLERANCE = 1e-4, 0.001, 0.02


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_source():
    require(sha(FLEXURE) == FLEXURE_SHA256, "frozen flexure source differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_washer_edge_source", FLEXURE)
    require(spec is not None and spec.loader is not None, "pure frozen force helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _contact_helper, records, pins = module.load_sources()
    require(pins[FLEXURE] == FLEXURE_SHA256, "force helper self-pin differs")
    selected = [record for record in records if record["state_id"] == STATE_ID]
    require(len(selected) == 1 and selected[0]["family"] == "rail", "frozen governing end is unavailable")
    pins[Path(__file__).resolve()] = sha(Path(__file__).resolve())
    module.authenticate(pins)
    return module, selected[0], pins


def radial_shapes(left, right, radii, outer):
    span = right - left
    s = (np.asarray(radii) - left)/span
    hermite = np.column_stack((1 - 3*s**2 + 2*s**3, span/outer*(s - 2*s**2 + s**3),
                               3*s**2 - 2*s**3, span/outer*(-s**2 + s**3)))
    hermite_r = np.column_stack(((-6*s + 6*s**2)/span, (1 - 4*s + 3*s**2)/outer,
                                 (6*s - 6*s**2)/span, (-2*s + 3*s**2)/outer))
    nodes = np.array([0.0, 1/3, 2/3, 1.0])
    lagrange, lagrange_r = np.ones((len(s), 4)), np.zeros((len(s), 4))
    for i in range(4):
        other = [j for j in range(4) if j != i]
        denominator = math.prod(nodes[i] - nodes[j] for j in other)
        lagrange[:, i] = np.prod([s - nodes[j] for j in other], axis=0)/denominator
        lagrange_r[:, i] = sum(np.prod([s - nodes[j] for j in other if j != k], axis=0)
                              for k in other)/(denominator*span)
    return hermite, hermite_r, lagrange, lagrange_r


def add_local(rows, columns, values, indices, matrix):
    active = np.flatnonzero(np.asarray(indices) >= 0)
    ids = np.asarray(indices)[active]
    rows.extend(np.repeat(ids, len(ids)).tolist())
    columns.extend(np.tile(ids, len(ids)).tolist())
    values.extend(matrix[np.ix_(active, active)].ravel().tolist())


def element_indices(model, element, mode):
    u = model["u_indices"][mode, element:element + 2].ravel()
    a = model["a_indices"][mode, 3*element:3*element + 4]
    b = model["b_indices"][mode - 1, 3*element:3*element + 4] if mode else np.array([], dtype=int)
    return u, a, b


def make_model(module, resolution):
    family, settings = module.FAMILIES["rail"], RESOLUTIONS[resolution]
    inner, outer, head = (family[key] for key in ("inner_radius_mm", "outer_radius_mm", "head_radius_mm"))
    edges = np.r_[np.linspace(inner, head, settings["inside_elements"] + 1),
                  np.linspace(head, outer, settings["outside_elements"] + 1)[1:]]
    elements, order = len(edges) - 1, settings["fourier_order"]
    u_indices = np.full((order + 1, elements + 1, 2), -1, dtype=int)
    next_index = 1  # w0 is the free axisymmetric deflection on the inner circle.
    for mode in range(order + 1):
        for node in range(elements + 1):
            for derivative in range(2):
                if mode == 0 and node == 0 and derivative == 0:
                    continue
                u_indices[mode, node, derivative] = next_index
                next_index += 1
    a_indices = np.arange(next_index, next_index + (order + 1)*(3*elements + 1)).reshape(order + 1, -1)
    next_index += a_indices.size
    b_indices = np.arange(next_index, next_index + order*(3*elements + 1)).reshape(order, -1)
    next_index += b_indices.size
    width = next_index + 3
    require(width == settings["unknowns"], "polar unknown census differs")
    thickness = family["thickness_mm"]
    rigidity = module.ESTEEL*thickness**3/(12*(1 - module.NU**2))
    constitutive = rigidity*np.array([[1.0, module.NU, 0.0], [module.NU, 1.0, 0.0], [0.0, 0.0, (1 - module.NU)/2]])
    shear_rigidity = (5/6)*module.ESTEEL/(2*(1 + module.NU))*thickness
    model = {"family": family, "settings": settings, "resolution": resolution, "edges": edges, "width": width,
             "u_indices": u_indices, "a_indices": a_indices, "b_indices": b_indices,
             "constitutive": constitutive, "shear_rigidity": shear_rigidity,
             "Kwood": module.KWOOD, "Khead": module.KHEAD, "Fy_hypothesis": module.FY_HYPOTHESIS}
    gauss, weights = np.polynomial.legendre.leggauss(6)
    bending_triplets, shear_triplets = ([], [], []), ([], [], [])
    wood_maps, areas, radial_points, angle_points, element_points = [], [], [], [], []
    angles = (np.arange(settings["angles"]) + 0.5)*(2*math.pi/settings["angles"])
    for element, (left, right) in enumerate(pairwise(edges)):
        radii = left + (gauss + 1)*(right - left)/2
        radial_weights = weights*(right - left)/2*radii
        h, hr, lagrange, lagrange_r = radial_shapes(left, right, radii, outer)
        contact_ids, contact_values = [0], [np.ones(len(radii)*len(angles))]
        for mode in range(order + 1):
            u, a, b = element_indices(model, element, mode)
            ids = np.r_[u, a, b]
            curvature = np.zeros((6, 3, len(ids)))
            gamma = np.zeros((6, 2, len(ids)))
            curvature[:, 0, 4:8] = lagrange_r/outer
            curvature[:, 1, 4:8] = lagrange/(outer*radii[:, None])
            gamma[:, 0, :4] = (h + radii[:, None]*hr)/outer
            gamma[:, 0, 4:8] = -lagrange/outer
            if mode:
                curvature[:, 1, 8:12] = mode*lagrange/(outer*radii[:, None])
                curvature[:, 2, 4:8] = -mode*lagrange/(outer*radii[:, None])
                curvature[:, 2, 8:12] = (lagrange_r - lagrange/radii[:, None])/outer
                gamma[:, 1, :4], gamma[:, 1, 8:12] = -mode*h/outer, -lagrange/outer
            cosine_area, sine_area = (2*math.pi, 0.0) if mode == 0 else (math.pi, math.pi)
            kb = cosine_area*np.einsum("n,nai,ab,nbj->ij", radial_weights, curvature[:, :2],
                                      constitutive[:2, :2], curvature[:, :2])
            kb += sine_area*constitutive[2, 2]*np.einsum("n,ni,nj->ij", radial_weights, curvature[:, 2], curvature[:, 2])
            ks = shear_rigidity*(cosine_area*np.einsum("n,ni,nj->ij", radial_weights, gamma[:, 0], gamma[:, 0])
                                + sine_area*np.einsum("n,ni,nj->ij", radial_weights, gamma[:, 1], gamma[:, 1]))
            add_local(*bending_triplets, ids, kb)
            add_local(*shear_triplets, ids, ks)
            values = ((radii/outer)[:, None, None]*h[:, None, :]*np.cos(mode*angles)[None, :, None]).reshape(-1, 4)
            for local, index in enumerate(u):
                if index >= 0:
                    contact_ids.append(int(index))
                    contact_values.append(values[:, local])
        contact_values = np.column_stack(contact_values)
        row_ids = np.repeat(np.arange(len(contact_values)), len(contact_ids))
        column_ids = np.tile(contact_ids, len(contact_values))
        wood_maps.append(sparse.coo_matrix((contact_values.ravel(), (row_ids, column_ids)),
                                          shape=(len(contact_values), width)).tocsr())
        areas.extend(np.repeat(radial_weights*(2*math.pi/len(angles)), len(angles)))
        radial_points.extend(np.repeat(radii, len(angles)))
        angle_points.extend(np.tile(angles, len(radii)))
        element_points.extend([element]*(len(radii)*len(angles)))
    for name, triplets in (("bending_stiffness", bending_triplets), ("shear_stiffness", shear_triplets)):
        values = sparse.coo_matrix((triplets[2], (triplets[0], triplets[1])), shape=(width, width)).tocsr()
        model[name] = (values + values.T)*0.5
    model["stiffness"] = model["bending_stiffness"] + model["shear_stiffness"]
    model["wood_map"] = sparse.vstack(wood_maps, format="csr")
    model["area"] = np.asarray(areas)
    model["r"] = np.asarray(radial_points)
    model["theta"] = np.asarray(angle_points)
    model["element"] = np.asarray(element_points)
    model["x"], model["y"] = model["r"]*np.cos(model["theta"]), model["r"]*np.sin(model["theta"])
    head_values = np.column_stack((np.ones(len(areas)), model["x"]/outer, model["y"]/outer))
    model["head_map"] = sparse.coo_matrix((head_values.ravel(),
        (np.repeat(np.arange(len(areas)), 3), np.tile(np.arange(width - 3, width), len(areas)))), shape=(len(areas), width)).tocsr()
    model["head_selection"] = model["element"] < settings["inside_elements"]
    require(math.isclose(float(np.sum(model["area"])), math.pi*(outer**2 - inner**2), abs_tol=1e-9), "wood quadrature area differs")
    require(math.isclose(float(np.sum(model["area"][model["head_selection"]])), math.pi*(head**2 - inner**2), abs_tol=1e-9),
            "head quadrature area differs")
    return model


def drive_vector(model, tension, moment):
    drive = np.zeros(model["width"])
    drive[-3:] = [tension, moment/model["family"]["outer_radius_mm"], 0.0]
    return drive


def contacts(model, full_head=False):
    selection = np.ones(len(model["area"]), dtype=bool) if full_head else model["head_selection"]
    return ((model["area"], model["wood_map"], model["Kwood"], model["x"], model["y"]),
            (model["area"][selection], (model["head_map"] - model["wood_map"])[selection],
             model["Khead"], model["x"][selection], model["y"][selection]))


def evaluate(model, pose, drive, contact_maps):
    energy = float(0.5*pose @ (model["stiffness"] @ pose) - drive @ pose)
    gradient, tangent, pressures, energies = model["stiffness"] @ pose - drive, model["stiffness"].copy(), [], []
    for area, mapping, stiffness, _x, _y in contact_maps:
        indentation = np.maximum(mapping @ pose, 0.0)
        pressure = stiffness*indentation
        value = float(0.5*stiffness*np.sum(area*indentation**2))
        energy += value
        gradient += mapping.T @ (area*pressure)
        tangent += mapping.T @ mapping.multiply((stiffness*area*(indentation > 0))[:, None])
        pressures.append(pressure)
        energies.append(value)
    return energy, gradient, tangent.tocsc(), pressures, energies


def contact_balance(contact_maps, pressures, tension, moment):
    records = []
    for role, (area, _mapping, _stiffness, x, y), pressure in zip(("wood", "head"), contact_maps, pressures):
        force = float(area @ pressure)
        first = [float((area*x) @ pressure), float((area*y) @ pressure)]
        records.append({"contact": role, "force_n": force, "first_moments_nmm": first,
                        "force_residual_n": force - tension, "first_moment_residuals_nmm": [first[0] - moment, first[1]],
                        "active_area_mm2": float(np.sum(area[pressure > 0])), "full_area_mm2": float(np.sum(area)),
                        "pressure_peak_mpa": float(np.max(pressure)), "mean_full_area_pressure_mpa": force/float(np.sum(area))})
    return records


def field_values(model, pose, element, radii, angles):
    outer = model["family"]["outer_radius_mm"]
    h, hr, lagrange, lagrange_r = radial_shapes(model["edges"][element], model["edges"][element + 1], radii, outer)
    shape = (len(radii), len(angles))
    w, beta, curvature, gamma = np.full(shape, pose[0]), np.zeros((*shape, 2)), np.zeros((*shape, 3)), np.zeros((*shape, 2))
    for mode in range(model["settings"]["fourier_order"] + 1):
        u_ids, a_ids, b_ids = element_indices(model, element, mode)
        u_coefficients = np.array([pose[index] if index >= 0 else 0.0 for index in u_ids])
        u, ur = h @ u_coefficients, hr @ u_coefficients
        a, ar = lagrange @ pose[a_ids], lagrange_r @ pose[a_ids]
        b, br = (lagrange @ pose[b_ids], lagrange_r @ pose[b_ids]) if mode else (np.zeros(len(radii)), np.zeros(len(radii)))
        cosine, sine = np.cos(mode*angles), np.sin(mode*angles)
        w += (radii*u/outer)[:, None]*cosine
        beta[:, :, 0] += (a/outer)[:, None]*cosine
        beta[:, :, 1] += (b/outer)[:, None]*sine
        curvature[:, :, 0] += (ar/outer)[:, None]*cosine
        curvature[:, :, 1] += ((a + mode*b)/(outer*radii))[:, None]*cosine
        curvature[:, :, 2] += ((br + (-mode*a - b)/radii)/outer)[:, None]*sine
        gamma[:, :, 0] += ((u + radii*ur - a)/outer)[:, None]*cosine
        gamma[:, :, 1] += ((-mode*u - b)/outer)[:, None]*sine
    return w, beta, curvature, gamma


def rigid_modes(model, debug):
    records = []
    outer = model["family"]["outer_radius_mm"]
    for role in ("normal_translation", "local_x_tilt"):
        pose = np.zeros(model["width"])
        if role == "normal_translation":
            pose[0] = 1.0
        else:
            pose[model["u_indices"][1, :, 0]] = outer
            pose[model["a_indices"][1]] = outer
            pose[model["b_indices"][0]] = -outer
        energy = float(0.5*pose @ (model["stiffness"] @ pose))
        action = float(np.max(np.abs(model["stiffness"] @ pose)))
        curvature_max, gamma_max = 0.0, 0.0
        for element in range(len(model["edges"]) - 1):
            selection = model["element"] == element
            radii, angles = np.unique(model["r"][selection]), np.unique(model["theta"][selection])
            _w, _beta, curvature, gamma = field_values(model, pose, element, radii, angles)
            curvature_max = max(curvature_max, float(np.max(np.abs(curvature))))
            gamma_max = max(gamma_max, float(np.max(np.abs(gamma))))
        record = {"mode": role, "matrix_energy_nmm": energy, "matrix_action_maximum_n": action,
                  "sampled_curvature_maximum_per_mm": curvature_max, "sampled_shear_strain_maximum": gamma_max}
        records.append(record)
        debug.update({"stage": "rigid-mode-diagnostics", "rigid_modes": records})
        require(abs(energy) <= 1e-5 and action <= GRADIENT_TOLERANCE and max(curvature_max, gamma_max) <= 1e-10,
                "polar plate has artificial stiffness in an in-subspace rigid mode")
    return records


def tangent_quality(tangent):
    require(np.isfinite(tangent.data).all(), "nonfinite sparse tangent")
    difference = tangent - tangent.T
    scale = max(1.0, float(np.max(np.abs(tangent.data))))
    symmetry = float(np.max(np.abs(difference.data))) if difference.nnz else 0.0
    require(symmetry/scale <= 1e-12, "sparse tangent symmetry residual exceeds 1e-12")
    return {"nnz": tangent.nnz, "relative_symmetry_residual": symmetry/scale,
            "minimum_diagonal_n_per_mm": float(np.min(tangent.diagonal())),
            "PSD_basis": "Positive isotropic curvature/shear Gram forms plus active compression-contact Gram forms.",
            "global_minimum_eigenvalue": None, "exact_nullity": None}


def coupon(model, modes, debug):
    area = float(np.sum(model["area"]))
    pose = np.zeros(model["width"])
    pose[0] = 100/(model["Kwood"]*area)
    pose[-3] = pose[0] + 100/(model["Khead"]*area)
    contact_maps = contacts(model, full_head=True)
    drive = drive_vector(model, 100.0, 0.0)
    energy, gradient, tangent, pressures, contact_energies = evaluate(model, pose, drive, contact_maps)
    balances = contact_balance(contact_maps, pressures, 100.0, 0.0)
    bending = float(0.5*pose @ (model["bending_stiffness"] @ pose))
    shear = float(0.5*pose @ (model["shear_stiffness"] @ pose))
    record = {"T_n": 100.0, "M_nmm": 0.0, "full_face_head_footprint": True, "area_mm2": area,
              "exact_w_mm": float(pose[0]), "exact_h_mm": float(pose[-3]), "uniform_pressure_mpa": 100/area,
              "scaled_gradient_maximum_n": float(np.max(np.abs(gradient))), "contact_balances": balances,
              "bending_energy_nmm": bending, "shear_energy_nmm": shear,
              "energy_identity_residual_nmm": float(drive @ pose - 2*(bending + shear + sum(contact_energies))),
              "energy_nmm": energy, "rigid_modes": modes, "tangent_quality": tangent_quality(tangent)}
    debug.update({"stage": "full-face-coupon", "scaled_variables_mm": pose.tolist(), **record})
    require(np.max(np.abs(gradient)) <= GRADIENT_TOLERANCE and abs(bending) <= 1e-10 and abs(shear) <= 1e-10,
            "full-face coupon energy or scaled gradient differs from its exact solution")
    require(all(np.max(np.abs(pressure - 100/area)) <= 1e-10 for pressure in pressures), "full-face coupon pressure is not uniform")
    check_balances(balances)
    record["coupon_satisfied"] = True
    return record


def check_balances(balances):
    require(all(abs(record["force_residual_n"]) <= FORCE_TOLERANCE
                and np.max(np.abs(record["first_moment_residuals_nmm"])) <= MOMENT_TOLERANCE for record in balances),
            "head/wood force or first-moment residual exceeds its declared tolerance")


def recover_fields(model, pose):
    outer, thickness = model["family"]["outer_radius_mm"], model["family"]["thickness_mm"]
    wood_w = model["wood_map"] @ pose
    affine = np.column_stack((np.ones(len(wood_w)), model["x"]/outer, model["y"]/outer))
    plane = np.linalg.lstsq(np.sqrt(model["area"])[:, None]*affine, np.sqrt(model["area"])*wood_w, rcond=None)[0]
    rows = []
    for element, (left, right) in enumerate(pairwise(model["edges"])):
        selection = model["element"] == element
        quadrature_radii = np.unique(model["r"][selection])
        quadrature_angles = np.unique(model["theta"][selection])
        evaluation_radii = np.r_[left, quadrature_radii, (left + right)/2, right]
        evaluation_angles = np.arange(model["settings"]["angles"])*(2*math.pi/model["settings"]["angles"])
        for sample_set, radii, angles in (("quadrature", quadrature_radii, quadrature_angles),
                                          ("edges_band_and_interiors", evaluation_radii, evaluation_angles)):
            w, beta, curvature, gamma = field_values(model, pose, element, radii, angles)
            moments = np.einsum("ab,rtb->rta", model["constitutive"], curvature)
            shears = model["shear_rigidity"]*gamma
            stresses = 6*moments/thickness**2
            face_vm = np.sqrt(stresses[:, :, 0]**2 - stresses[:, :, 0]*stresses[:, :, 1]
                              + stresses[:, :, 1]**2 + 3*stresses[:, :, 2]**2)
            mid_vm = math.sqrt(3)*3*np.linalg.norm(shears, axis=2)/(2*thickness)
            for radial, radius in enumerate(radii):
                for angular, angle in enumerate(angles):
                    x, y = radius*math.cos(angle), radius*math.sin(angle)
                    head_w = pose[-3] + pose[-2]*x/outer + pose[-1]*y/outer
                    edge = "inner" if math.isclose(radius, model["edges"][0], abs_tol=1e-12, rel_tol=0) else (
                        "outer" if math.isclose(radius, model["edges"][-1], abs_tol=1e-12, rel_tol=0) else None)
                    at_band = math.isclose(radius, model["family"]["head_radius_mm"], abs_tol=1e-12, rel_tol=0)
                    rows.append({"state_id": STATE_ID, "sample_set": sample_set, "element": element, "r_mm": float(radius),
                                 "theta_rad": float(angle), "x_mm": x, "y_mm": y, "radial_edge": edge,
                                 "head_band_boundary": at_band, "w_mm": float(w[radial, angular]),
                                 "beta_polar_components_rad": beta[radial, angular].tolist(),
                                 "non_affine_w_mm": float(w[radial, angular] - plane @ [1.0, x/outer, y/outer]),
                                 "Mrr_Mtt_Mrt_n": moments[radial, angular].tolist(), "Qr_Qt_n_per_mm": shears[radial, angular].tolist(),
                                 "face_stress_rr_tt_rt_mpa": stresses[radial, angular].tolist(), "face_von_mises_mpa": float(face_vm[radial, angular]),
                                 "midplane_parabolic_shear_von_mises_proxy_mpa": float(mid_vm[radial, angular]),
                                 "sampled_through_thickness_maximum_proxy_mpa": float(max(face_vm[radial, angular], mid_vm[radial, angular])),
                                 "wood_pressure_mpa": model["Kwood"]*max(float(w[radial, angular]), 0.0),
                                 "head_pressure_mpa": model["Khead"]*max(float(head_w - w[radial, angular]), 0.0)
                                 if radius <= model["family"]["head_radius_mm"] + 1e-12 else 0.0})
    edge_traces = {}
    for edge in ("inner", "outer"):
        selected = [row for row in rows if row["radial_edge"] == edge]
        edge_traces[edge] = {"sampled_max_abs_Mrr_n": max(abs(row["Mrr_Mtt_Mrt_n"][0]) for row in selected),
                             "sampled_max_abs_Mrt_n": max(abs(row["Mrr_Mtt_Mrt_n"][2]) for row in selected),
                             "sampled_max_abs_Qr_n_per_mm": max(abs(row["Qr_Qt_n_per_mm"][0]) for row in selected),
                             "sampled_stress_peak_witness": max(selected, key=lambda row: row["sampled_through_thickness_maximum_proxy_mpa"])}
    nonaffine = wood_w - affine @ plane
    return rows, {"weighted_best_fit_rigid_plane_mm": plane.tolist(),
                  "non_affine_w_weighted_rms_mm": float(np.sqrt(np.sum(model["area"]*nonaffine**2)/np.sum(model["area"]))),
                  "non_affine_peak_witness": max(rows, key=lambda row: abs(row["non_affine_w_mm"])),
                  "sampled_stress_peak_witness": max(rows, key=lambda row: row["sampled_through_thickness_maximum_proxy_mpa"]),
                  "sampled_deflection_peak_witness": max(rows, key=lambda row: abs(row["w_mm"])),
                  "head_band_stress_peak_witness": max((row for row in rows if row["head_band_boundary"]),
                                                       key=lambda row: row["sampled_through_thickness_maximum_proxy_mpa"]),
                  "free_radial_edge_residual_traces": edge_traces}


def solve_state(model, source, debug):
    pose = np.zeros(model["width"])
    rigid, outer = source["saved_rigid_contact"], model["family"]["outer_radius_mm"]
    tilt = rigid["wood_contact"]["tilt_rad"]
    pose[0] = rigid["wood_contact"]["closure_mm"]
    pose[model["u_indices"][1, :, 0]] = outer*tilt
    pose[model["a_indices"][1]] = outer*tilt
    pose[model["b_indices"][0]] = -outer*tilt
    pose[-3:] = [rigid["total_closure_mm"], outer*rigid["relative_tilt_rad"], 0.0]
    initial, drive, contact_maps = pose.copy(), drive_vector(model, source["T_n"], source["M_magnitude_nmm"]), contacts(model)
    linear_history = []
    for iteration in range(101):
        energy, gradient, tangent, pressures, contact_energies = evaluate(model, pose, drive, contact_maps)
        require(np.isfinite(energy) and np.isfinite(gradient).all(), "nonfinite edge-model energy or gradient")
        balances = contact_balance(contact_maps, pressures, source["T_n"], source["M_magnitude_nmm"])
        quality = tangent_quality(tangent)
        debug.update({"stage": "governing-state", "iteration": iteration, "scaled_variables_mm": pose.tolist(),
                      "energy_nmm": energy, "scaled_gradient_components_n": gradient.tolist(),
                      "scaled_gradient_maximum_n": float(np.max(np.abs(gradient))), "contact_balances": balances,
                      "tangent_quality": quality, "linear_solve_history": linear_history})
        if np.max(np.abs(gradient)) <= GRADIENT_TOLERANCE:
            break
        require(iteration < 100, "STOP: polar washer equilibrium did not converge within 100 Newton steps")
        diagonal = tangent.diagonal()
        require(np.min(diagonal) > 0, "sparse tangent has an unsupported zero diagonal; no stiffness is added")
        scale = 1/np.sqrt(diagonal)
        scaling = sparse.diags(scale)
        scaled = (scaling @ tangent @ scaling).tocsc()
        factor = splu(scaled)
        step = scale*factor.solve(-scale*gradient)
        require(np.isfinite(step).all(), "sparse Newton step is nonfinite")
        linear_residual = tangent @ step + gradient
        relative_residual = float(np.max(np.abs(linear_residual))/max(1.0, np.max(np.abs(gradient))))
        require(relative_residual <= 1e-7, "sparse Newton relative linear residual exceeds 1e-7")
        descent, curvature = float(gradient @ step), float(step @ (tangent @ step))
        require(descent < 0 and curvature >= 0, "sparse Newton direction lacks descent or nonnegative Gram curvature")
        linear_history.append({"iteration": iteration, "relative_linear_residual": relative_residual,
                               "absolute_linear_residual_maximum_n": float(np.max(np.abs(linear_residual))),
                               "directional_derivative_nmm": descent, "direction_curvature_nmm": curvature})
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose + fraction*step
            candidate_energy = evaluate(model, candidate, drive, contact_maps)[0]
            if np.isfinite(candidate_energy) and candidate_energy <= energy + 1e-4*fraction*descent + 1e-12*max(1.0, abs(energy)):
                pose = candidate
                linear_history[-1]["accepted_fraction"] = fraction
                break
        else:
            raise ValueError("STOP: polar washer Armijo search found no acceptable step")
    check_balances(balances)
    fields, witnesses = recover_fields(model, pose)
    bending = float(0.5*pose @ (model["bending_stiffness"] @ pose))
    shear = float(0.5*pose @ (model["shear_stiffness"] @ pose))
    head_tilt = pose[-2:]/outer
    for balance, role in zip(balances, ("wood_contact", "head_contact")):
        balance["active_area_minus_saved_rigid_mm2"] = balance["active_area_mm2"] - rigid[role]["active_area_mm2"]
        balance["pressure_peak_minus_saved_rigid_mpa"] = balance["pressure_peak_mpa"] - rigid[role]["pressure_peak_mpa"]
    return {**source, **witnesses, "iterations": iteration, "scaled_variables_mm": pose.tolist(),
            "initial_scaled_variables_mm": initial.tolist(), "scaled_gradient_components_n": gradient.tolist(),
            "scaled_gradient_maximum_n": float(np.max(np.abs(gradient))), "energy_nmm": energy,
            "bending_energy_nmm": bending, "shear_energy_nmm": shear,
            "wood_contact_energy_nmm": contact_energies[0], "head_contact_energy_nmm": contact_energies[1],
            "load_work_nmm": float(drive @ pose),
            "energy_identity_residual_nmm": float(drive @ pose - 2*(bending + shear + sum(contact_energies))),
            "head_closure_mm": float(pose[-3]), "head_tilt_components_rad": head_tilt.tolist(),
            "head_closure_minus_saved_rigid_mm": float(pose[-3] - rigid["total_closure_mm"]),
            "head_tilt_magnitude_minus_saved_rigid_rad": float(np.linalg.norm(head_tilt) - rigid["relative_tilt_rad"]),
            "contact_balances": balances, "tangent_quality": quality, "linear_solve_history": linear_history,
            "elastic_Fy_250MPa_hypothesis_exceeded": witnesses["sampled_stress_peak_witness"]["sampled_through_thickness_maximum_proxy_mpa"] > model["Fy_hypothesis"],
            "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
            "complete_joint_acceptance": False, "physical_release": False}, fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resolution", choices=tuple(RESOLUTIONS), required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(not output.exists(), f"output already exists: {output}")
    module, source, pins = load_source()
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    model, modes, coupon_record, state, fields, failure = None, None, None, None, None, None
    debug = {"stage": "matrix-preparation", "source_T_n": source["T_n"], "source_M_nmm": source["M_magnitude_nmm"]}
    try:
        model = make_model(module, args.resolution)
        modes = rigid_modes(model, debug)
        coupon_record = coupon(model, modes, debug)
        debug = {}
        state, fields = solve_state(model, source, debug)
        module.authenticate(pins)
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"error": str(error), "last_accepted_state": debug, "incompatibility_proved": False}
        if model is not None and debug.get("stage") == "governing-state" and "scaled_variables_mm" in debug:
            fields, partial_witnesses = recover_fields(model, np.array(debug["scaled_variables_mm"]))
            failure["partial_sampled_fields"] = partial_witnesses
    if fields:
        with (output / "fields.csv").open("w", newline="") as stream:
            module.csv_rows(stream, fields)
    if state:
        with (output / "states.csv").open("w", newline="") as stream:
            module.csv_rows(stream, [{key: state[key] for key in (
                "state_id", "T_n", "M_magnitude_nmm", "iterations", "scaled_gradient_maximum_n", "head_closure_mm",
                "head_tilt_components_rad", "non_affine_w_weighted_rms_mm", "sampled_stress_peak_witness",
                "free_radial_edge_residual_traces", "contact_balances", "elastic_Fy_250MPa_hypothesis_exceeded")}])
    settings = RESOLUTIONS[args.resolution]
    result = {"schema": "upper_right_polar_mindlin_washer_edge/v1",
              "status": "STOP" if failure else "FINITE_POLAR_WASHER_EDGE_HYPOTHESIS",
              "state_id": STATE_ID, "resolution": args.resolution, "source": source,
              "counts": {"authenticated_source_end_states": 48, "requested_end_states": 1,
                         "completed_end_states": int(state is not None), "completed_coupons": int(coupon_record is not None)},
              "state": state, "failure": failure, "engineering_coupon": coupon_record,
              "model": {"family": module.FAMILIES["rail"], "resolution": settings,
                        "radial_edges_mm": model["edges"].tolist() if model else None,
                        "scaled_unknowns": settings["unknowns"], "radial_gauss_points_per_element": 6,
                        "wood_contact_quadrature_points": (settings["inside_elements"] + settings["outside_elements"])*6*settings["angles"],
                        "head_contact_quadrature_points": settings["inside_elements"]*6*settings["angles"],
                        "stiffness_nnz": model["stiffness"].nnz if model else None, "rigid_mode_diagnostics": modes,
                        "E_mpa_hypothesis": module.ESTEEL, "nu_hypothesis": module.NU, "Fy_mpa_hypothesis": module.FY_HYPOTHESIS,
                        "Kwood_mpa_per_mm_hypothesis": module.KWOOD, "Khead_mpa_per_mm_hypothesis": module.KHEAD,
                        "shear_correction_factor": 5/6, "primary_energy_source": module.ENERGY_SOURCE,
                        "trial_space": "w=w0+(r/ro) sum u_m(r) cos(m theta), with C1 cubic Hermite u; beta_r=sum a_m(r)cos(m theta)/ro and beta_theta=sum b_m(r)sin(m theta)/ro use C0 piecewise cubic Lagrange functions.",
                        "axisymmetric_convention": "w0 is the free inner-circle axisymmetric value and u0(ri)=0 by representation. This drops one finite trial direction; it is not removal of an exact duplicate or a fixed physical deflection.",
                        "scaling": "Hermite derivative coefficients are ro*u_r; all u, a, b and head coefficients are in mm.",
                        "head_plane": "h=h0+hX*x/ro+hY*y/ro; hY remains an unknown diagnostic under the symmetric source drive.",
                        "polar_curvature": "[beta_r,r, (beta_theta,theta+beta_r)/r, beta_theta,r+(beta_r,theta-beta_theta)/r]",
                        "polar_shear": "[w,r-beta_r, w,theta/r-beta_theta]",
                        "radial_boundary_conditions": "Both radial edges are natural weak/Ritz free boundaries; no pointwise M/Q equation, deflection or rotation is imposed.",
                        "sparse_assembly": "Fourier orthogonality gives element-local plate Gram matrices. Unilateral contact is assembled with sparse point maps; sparse diagonally scaled LU supplies each Newton step without added stiffness.",
                        "scaled_gradient_tolerance_n": GRADIENT_TOLERANCE, "contact_force_tolerance_n": FORCE_TOLERANCE,
                        "contact_first_moment_tolerance_nmm": MOMENT_TOLERANCE, "relative_linear_solve_tolerance": 1e-7,
                        "maximum_newton_steps": 100, "maximum_armijo_backtracks_per_step": 50,
                        "stress_recovery": "Face VM from 6M/t^2 and midplane sqrt(3)*3|Q|/(2t) with parabolic recovery are compared at each point, preserving their different thickness positions."},
              "limits": ["Only the one exact same-state pair-derived end T and its own M are prescribed. Washer response is not fed back into pair/beam or full-frame equilibrium.",
                         "The symmetric angular subspace retains constant and local-x rigid tilt modes. Its piecewise cubic rotation space contains gradw; this does not establish stress convergence.",
                         "Free-edge traces are sampled residuals of a weak approximation. They may be nonzero and are never zeroed by an imposed boundary equation.",
                         "Stress is evaluated on radial quadrature interiors, both sides of element boundaries, both radial edges and the head-band boundary at midpoint and zero-origin angular grids.",
                         "E, nu, thickness, head/wood springs and 250 MPa yield remain the same hypotheses as the frozen flexure source. No delivered product, material strength or physical resistance is qualified.",
                         "The shell stress proxy excludes sigmaZZ, contact-edge three-dimensional stress, plasticity, membrane/geometric nonlinearity, preload and friction.",
                         "The full-face coupon and two rigid modes exercise signs and dimensional assembly. They do not validate the current unilateral contact/stress field.",
                         "A numerical STOP preserves its last accepted state and sampled residuals; it does not prove mechanical incompatibility. No regularization, relaxed retry, native/frame solve or CAD operation occurs."],
              "source_sha256": {str(path.relative_to(ROOT)): digest for path, digest in sorted(pins.items())},
              "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
              "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None, "actual_washer_yield_mpa": None,
              "coupled_joint_resistance_n": None, "complete_joint_acceptance": False, "physical_release": False}
    hashes = {path.name: sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    module.dump(output / "checks.json", result)
    hashes["checks.json"] = sha(output / "checks.json")
    module.dump(output / "source-pins.json", {"source_sha256": result["source_sha256"], "output_sha256": hashes,
                                            "complete_joint_acceptance": False, "physical_release": False})
    module.authenticate(pins)
    print(json.dumps({"status": result["status"], "resolution": args.resolution, "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
