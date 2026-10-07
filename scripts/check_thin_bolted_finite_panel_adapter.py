"""Six saved-panel reference and finite constant-load method coupons.

Reads authenticated JSON/NPZ only. Builds local finite plate matrices, with
no geometry reconstruction, frame assembly or response solve.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from scripts import thin_bolted_finite_panel_adapter as adapter
from scripts import thin_bolted_panel_coupled as datums
from scripts import thin_bolted_panel_mechanics as method

FIELD = method.PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
FIELD_SHA = "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d"
OPERATORS = method.ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.npz"
OPERATORS_SHA = "2b97d8c1741a0fbef119eb00b3f43bdf5f76e802b4851962a62fc555f1813468"


def inputs():
    pins = {**adapter.BASE_PINS, str(datums.ASSESSMENT.relative_to(method.ROOT)): datums.ASSESSMENT_SHA,
            str(datums.DATUMS.relative_to(method.ROOT)): datums.DATUMS_SHA,
            str(FIELD.relative_to(method.ROOT)): FIELD_SHA,
            str(OPERATORS.relative_to(method.ROOT)): OPERATORS_SHA,
            str(method.LAYOUT.relative_to(method.ROOT)): method.LAYOUT_SHA,
            "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0"}
    adapter.verify_pins(pins)
    state = json.loads(FIELD.read_text())
    integrated = json.loads(method.INTEGRATED.read_text())
    panels = datums.prepared_datums(state, json.loads(datums.ASSESSMENT.read_text()),
                                     json.loads(datums.DATUMS.read_text()), integrated)
    layout = json.loads(method.LAYOUT.read_text())
    for name, panel in panels.items():
        panel["screws"] = [r for r in layout["screw_axes"] if r["panel"] == name]
    return panels, state, integrated, pins


def rigid_coefficients(a, rotation, translation):
    b = a.basis
    greville = np.array([np.mean(b.knots[i + 1:i + 4]) for i in range(b.order)])
    x, y = np.meshgrid(greville * b.width, greville * b.height, indexing="ij")
    original = a.origin + np.c_[x.ravel(), y.ravel()] @ a.axes[:, :2].T
    return ((original @ rotation.T + translation - original) @ a.axes).T.ravel()


def check() -> dict:
    panels, state, integrated, pins = inputs()
    case = next(c for c in method.load_cases(integrated) if c["id"] == state["case_id"])
    rotation = Rotation.from_rotvec(np.array([2., -1., 3.]) / np.sqrt(14.) * np.deg2rad(20.)).as_matrix()
    translation = np.array([19., -21., 34.])
    records = []
    with np.load(OPERATORS, allow_pickle=False) as operators:
        for name, panel in panels.items():
            start = time.perf_counter()
            a = adapter.FinitePanelAdapter(panel, source_sha256=pins)
            zero = np.zeros(a.local_size)
            reference = a.response(zero)
            retained = operators[f"{name}/K"]
            relative = np.linalg.norm(reference["local_hessian_csr"].toarray() - retained) / np.linalg.norm(retained)
            method.require(relative < 2e-11, f"reference finite panel H differs from saved K: {name}")
            screw_max = 0.
            for i, screw in enumerate(panel["screws"]):
                port = a.screw_port(zero, screw, False)
                expected = a.axes @ np.vstack([operators[f"{name}/screw_{component}"][i] for component in ("u", "v", "w")])
                screw_max = max(screw_max, float(abs(port["J_csr"].toarray() - expected).max()))
            method.require(screw_max < 2e-9, f"reference annular screw J differs: {name}")
            loads = a.prepare_case_load(case, integrated, "original_top", state["body_applied_loads"])
            at_zero = loads.external(zero)
            rhs_error = float(abs(-at_zero["local_gradient_n"] - loads.corrected_reference_force_n).max())
            method.require(rhs_error < 1e-8, f"reference corrected RHS differs: {name}")
            old_uncorrected = operators[f"{name}/load/{case['id']}"]
            current_without_metal = method.panel_case_load(a.panel, case, integrated, "original_top")[0]
            mass_error = float(abs(current_without_metal - old_uncorrected).max())
            method.require(mass_error < 1e-8, f"saved mass/load basis differs: {name}")
            q = rigid_coefficients(a, rotation, translation)
            rigid_response = a.response(q, False)
            rigid_energy = rigid_response["energy_nmm"]
            method.require(abs(rigid_energy) < 1e-9, f"common rigid motion acquires energy: {name}")
            finite_loads = loads.external(q)
            mean_xy = a.measure["mass_weights"] @ a.measure["xy_mm"]
            mean_reference = a.origin + a.axes[:, :2] @ mean_xy
            expected = -loads.uniform_force @ (rotation @ mean_reference + translation - mean_reference)
            for load in loads.point_loads:
                p, f = np.asarray(load["point_xyz_mm"]), np.asarray(load["force_xyz_n"])
                expected -= f @ (rotation @ p + translation - p)
            expected += -loads.correction_n @ q
            gravity_error = float(abs(finite_loads["energy_nmm"] - expected))
            metric_defect = float(np.linalg.norm(a.axes.T @ a.axes - np.eye(3)))
            port_radius = max(np.linalg.norm(np.asarray(r["point_xyz_mm"]) - a.origin) for r in loads.loads)
            force_sum = sum(np.linalg.norm(r["force_xyz_n"]) for r in loads.loads)
            precision_allowance = 1e-8 + metric_defect * force_sum * (4 * port_radius + 2 * np.linalg.norm(translation))
            method.require(gravity_error < precision_allowance,
                           f"constant world gravity rigid-motion work exceeds recorded-axis precision: {name}")
            rng = np.random.default_rng(350)
            perturbation = rng.normal(size=a.local_size); perturbation /= np.linalg.norm(perturbation)
            h = 1e-3
            plus, minus = loads.external(q+h*perturbation, False), loads.external(q-h*perturbation, False)
            numerical_gradient = (plus["energy_nmm"] - minus["energy_nmm"])/(2*h)
            expected_gradient = finite_loads["local_gradient_n"] @ perturbation
            numerical_hessian = (plus["local_gradient_n"]-minus["local_gradient_n"])/(2*h)
            expected_hessian = finite_loads["local_hessian_csr"] @ perturbation
            gradient_error = float(abs(numerical_gradient - expected_gradient))
            hessian_error = float(np.linalg.norm(numerical_hessian - expected_hessian))
            method.require(gradient_error < 2e-5 and hessian_error < 2e-6,
                           f"finite external gradient/tangent coupon differs: {name}")
            records.append({"panel": name, "reference_H_vs_saved_K_relative_frobenius": float(relative),
                "reference_screw_J_max_abs_difference": screw_max, "screw_count": len(panel["screws"]),
                "reference_corrected_RHS_max_abs_difference_n": rhs_error,
                "mass_load_vs_saved_NPZ_max_abs_difference_n": mass_error,
                "twenty_degree_rigid_motion_energy_nmm": rigid_energy,
                "constant_world_gravity_rigid_motion_potential_difference_nmm": gravity_error,
                "recorded_axis_metric_defect_frobenius": metric_defect,
                "constant_world_work_coordinate_precision_allowance_nmm": precision_allowance,
                "external_gradient_directional_central_difference_abs_n": gradient_error,
                "external_H_directional_central_difference_l2_n_per_mm": hessian_error,
                "finite_correction_wrench_n_nmm": finite_loads["generalized_correction_wrench_n_nmm"].tolist(),
                "finite_external_force_wrench_residual_norm_n": float(np.linalg.norm(finite_loads["wrench_residual_n_nmm"][:3])),
                "finite_external_moment_wrench_residual_norm_nmm": float(np.linalg.norm(finite_loads["wrench_residual_n_nmm"][3:])),
                "reference_area_quadrature_points": len(a.measure["xy_mm"]), "compact_support_groups": len(a.groups),
                "reference_H_sparse_entries": reference["local_hessian_csr"].nnz,
                "retained_owned_point_load_count": len(loads.point_loads),
                "reference_generalized_correction_norm_n": float(np.linalg.norm(loads.correction_n)),
                "reference_port_alignment_correction_norm_n": float(np.linalg.norm(loads.reference_port_alignment_correction_n)),
                "reference_port_alignment_correction_inf_n": float(abs(loads.reference_port_alignment_correction_n).max()),
                "retained_rigid_correction_norm_n": float(np.linalg.norm(loads.retained_rigid_correction_n)),
                "elapsed_local_coupon_seconds": time.perf_counter()-start})
    pins.update({str(Path(adapter.__file__).resolve().relative_to(method.ROOT)): method.sha(Path(adapter.__file__)),
                 str(Path(__file__).resolve().relative_to(method.ROOT)): method.sha(Path(__file__)),
                 "tests/test_thin_bolted_finite_panel_adapter.py": method.sha(method.ROOT / "tests/test_thin_bolted_finite_panel_adapter.py")})
    adapter.verify_pins(pins)
    return {"schema": "thin_bolted_finite_panel_adapter_method/v1", "source_sha256": pins,
            "six_panel_method_coupons": records, "all_method_coupons_pass": True,
            "reference_case_id": state["case_id"], "reference_accessory_placement": state["accessory_placement"],
            "reference_field_state_id": state["state_id"],
            "reference_field_used_as_load_metadata_only": True,
            "method": {"CAD_rebuilt": False, "global_assembly_built": False, "response_solved": False,
                       "energy_measure_subtraction_retained": True, "existing_helpers_changed": False,
                       "screw_axial_projected_annulus_reference_rows_retained": True,
                       "generalized_RHS_correction_explicitly_carried": True},
            "unit_tests": {"command": "UV_CACHE_DIR=/tmp/mini-moonboard-uv-cache OPENBLAS_NUM_THREADS=1 uv run --offline pytest -q tests/test_thin_bolted_finite_panel_adapter.py",
                           "passed": 12},
            "limits": ["Signed bore/head-seat/bevel quadrature is the retained energy proxy, not locally traction-free hole or seating-pressure qualification.",
                       "Projected-ring screw kinematics and nearest-edge accessory tangent extension are explicit objective scenarios matching the reference rows; no manufacturer stiffness/capacity follows.",
                       "The fixed generalized correction has no assigned physical forces; its current rigid-generator wrench must be included separately in an assembly audit.",
                       "Tiny common-motion differences reflect the retained CAD axes' orthogonality tolerance; no finite assembly/contact solution or applicability pass is issued."],
            "release": datums.RELEASE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": method.sha(args.out),
                      "six_panel_coupons_pass": True, "screws": sum(r["screw_count"] for r in result["six_panel_method_coupons"])}))


if __name__ == "__main__":
    main()
