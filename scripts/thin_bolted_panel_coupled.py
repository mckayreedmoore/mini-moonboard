"""Read-only panel diagnostics from one authenticated coupled field.

No geometry reconstruction, stiffness assembly or equilibrium solve occurs.
Saved Ritz coefficients supply membrane/bending/shear/displacement fields;
saved compatible connector actions supply simultaneous screw demands.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from itertools import pairwise
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss

from scripts import thin_bolted_panel_mechanics as panel_method

ROOT = panel_method.ROOT
PACKET = panel_method.PACKET
METHOD_SHA = "472eef63a8af59367533028008c68e4f7e32780e49891499154ba2950559a3aa"
ASSESSMENT = PACKET / "panel-mechanics-v4.json"
ASSESSMENT_SHA = "a61cadf7b120b58c00326e83c68999f7a726fba77ec5e12882cf843355951dec"
VALIDATION = PACKET / "panel-mechanics-validation-v4.json"
VALIDATION_SHA = "0b9af40f1d9b5969d99d6401df04336701e94899f20a9bc1bc7c00a7c1914691"
DATUMS = ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.json"
DATUMS_SHA = "aeeb9b6ccd2c521896b32012ccbf9712fd67cdb7d0744e06d88afa4fd3f441d4"
FLOOR_BASIS = "authenticated-finished-timber-horizontal-faces"
FLOOR_SHA = "e6c7ac4548b943bef4580b7c58efd67c11e29ed3335ae4036998a70c346986fc"
SUPPORT_AUDIT_SHA = "0a37e67ed20e3fd1eed8b8b4d0d12889df6fd9a6fb33d6f8f68a0c6768f5ada0"
COEFFICIENT_ORDER = "u,v,outward_w; x-major tensor cubic B-spline coefficients in mm"
RELEASE = {key: False for key in ("candidate_accepted", "complete_joint_acceptance",
                               "capacity_established", "fabrication_released",
                               "structural_released", "climbing_released")}


def verify_pins(pins: dict) -> None:
    for path, expected in pins.items():
        panel_method.require(panel_method.sha(ROOT / path) == expected,
                             f"saved-field source differs: {path}")


def validate_state(state: dict) -> None:
    parameters = state["parameters"]
    panel_method.require(parameters.get("floor_support_basis") == FLOOR_BASIS
                         and parameters.get("floor_contact_geometry_sha256") == FLOOR_SHA,
                         "finished timber floor support is required; raw-floor state is unsupported")
    panel_method.require(state["response"]["converged"] and state["usable_conditional_actions"]
                         and state["equilibrium_verification"]["all_body_and_global_checks_pass"],
                         "converged compatible equilibrium field required")
    panel_method.require(not any(state["release"].values()), "analysis cannot authorize release")
    identity = {"case_id": state["case_id"], "accessory_placement": state["accessory_placement"],
                "parameters": parameters, "geometry_cache_sha256": state["geometry_cache_sha256"]}
    expected = "thin-v4-" + hashlib.sha256(json.dumps(identity, sort_keys=True,
                                                     separators=(",", ":")).encode()).hexdigest()[:24]
    panel_method.require(state["state_id"] == expected, "coupled state identity differs")
    for table in ("panel_screw_actions", "contact_actions"):
        for row in state[table]:
            panel_method.require(row["state_id"] == expected and row["case_id"] == state["case_id"]
                                 and row["accessory_placement"] == state["accessory_placement"],
                                 "mixed case, accessory or state actions")


def coefficient_slice(state: dict, name: str) -> tuple[panel_method.SheetBasis, np.ndarray]:
    row = state["panel_generalized_coefficients"][name]
    basis = panel_method.SheetBasis(row["width_mm"], row["height_mm"],
                                    state["parameters"]["panel_intervals"])
    panel_method.require(row["basis_order_per_direction"] == basis.order
                         and row["coefficient_order"] == COEFFICIENT_ORDER
                         and np.array_equal(row["knots_normalized"], basis.knots),
                         "saved coefficient basis or ordering differs")
    q = np.asarray(row["coefficients_mm"], dtype=float)
    start = row["global_dof_start"]
    whole = np.asarray(state["response"]["q"], dtype=float)
    panel_method.require(isinstance(start, int) and start >= 0 and q.shape == (3 * basis.size,)
                         and np.isfinite(q).all() and np.array_equal(q, whole[start:start + len(q)]),
                         "panel coefficients differ from their global field slice")
    return basis, q


def prepared_datums(state: dict, assessment: dict, datums: dict, integrated: dict) -> dict:
    """Rehydrate JSON geometry and basis only; never import BREP or assemble K."""
    geometry_rows = {r["panel"]: r for r in assessment["panel_geometry"]}
    panel_method.require(set(state["panel_generalized_coefficients"]) == set(panel_method.PANELS),
                         "six coefficient blocks required")
    panels = {}
    slices = []
    for name in panel_method.PANELS:
        basis, q = coefficient_slice(state, name)
        source, datum = geometry_rows[name], datums[name]
        panel_method.require(abs(source["width_mm"] - basis.width) < 1e-8
                             and abs(source["height_mm"] - basis.height) < 1e-8,
                             "saved dimensions differ from frozen panel geometry")
        axes = np.asarray(datum["local_axes_columns_xyz"], dtype=float)
        origin = np.asarray(datum["origin_xyz_mm"], dtype=float)
        panel_method.require(np.max(abs(axes.T @ axes - np.eye(3))) < 1e-8
                             and np.array_equal(axes[:, 0], [1., 0., 0.]),
                             "horizontal owner strength-axis datum differs")
        geometry = {"name": name, "origin": origin, "axes": axes, "inward": -axes[:, 2],
                    "front_height": source["front_height_mm"]}
        holes = [{**r, "xy_mm": panel_method.local_xy(r["start_xyz_mm"], geometry).tolist()}
                 for r in integrated["panel_machining"]["features"] if r["panel"] == name]
        panels[name] = {"geometry": geometry, "basis": basis, "holes": holes,
                        "support_bounds": source["support_footprints"],
                        "thickness": panel_method.CAT, "twist_scale": 1., "q": q}
        start = state["panel_generalized_coefficients"][name]["global_dof_start"]
        slices.append(set(range(start, start + len(q))))
    panel_method.require(all(not a.intersection(b) for i, a in enumerate(slices) for b in slices[i + 1:]),
                         "overlapping panel global field slices")
    return panels


def plate_fields(panel: dict, points: np.ndarray, q: np.ndarray) -> dict[str, np.ndarray]:
    """Signed simultaneous fields, using the frozen zero-Poisson proxy."""
    basis, n = panel["basis"], panel["basis"].size
    u, v, w = q[:n], q[n:2 * n], q[2 * n:]
    dx, dy = basis.values(points, 1), basis.values(points, 0, 1)
    ex, ey = panel_method.material.APA_EA[::-1]
    bx, by = panel_method.material.APA_EI[::-1]
    ga = panel_method.material.APA_GA
    twist = ga * panel["thickness"]**2 / 12 * panel["twist_scale"]
    return {"u_mm": basis.values(points) @ u, "v_mm": basis.values(points) @ v,
            "outward_w_mm": basis.values(points) @ w,
            "slope_x": dx @ w, "slope_upslope": dy @ w,
            "membrane_x_n_per_mm": ex * (dx @ u),
            "membrane_upslope_n_per_mm": ey * (dy @ v),
            "membrane_xy_n_per_mm": ga * (dy @ u + dx @ v),
            "bending_x_nmm_per_mm": -bx * (basis.values(points, 2) @ w),
            "bending_upslope_nmm_per_mm": -by * (basis.values(points, 0, 2) @ w),
            "twisting_xy_nmm_per_mm": -2 * twist * (basis.values(points, 1, 1) @ w),
            "rolling_x_n_per_mm": -bx * (basis.values(points, 3) @ w)
                                      - 2 * twist * (basis.values(points, 1, 2) @ w),
            "rolling_upslope_n_per_mm": -by * (basis.values(points, 0, 3) @ w)
                                            - 2 * twist * (basis.values(points, 2, 1) @ w)}


def deformation_diagnostics(panel: dict, q: np.ndarray, samples: int = 41) -> dict:
    basis = panel["basis"]
    x, y = np.meshgrid(np.linspace(0, basis.width, samples),
                        np.linspace(0, basis.height, samples), indexing="ij")
    points = np.c_[x.ravel(), y.ravel()]
    fields = plate_fields(panel, points, q)
    w = fields["outward_w_mm"]
    slope = np.hypot(fields["slope_x"], fields["slope_upslope"])
    design = np.c_[np.ones(len(points)), points]
    affine = np.linalg.lstsq(design, w, rcond=None)[0]
    warp = w - design @ affine
    jw, js, jb = int(abs(w).argmax()), int(slope.argmax()), int(abs(warp).argmax())
    # Positive partition of unity makes each cubic field lie within its
    # coefficient convex hull. These are safe field bounds, not sample peaks.
    coefficients = q[2 * basis.size:].reshape(basis.order, basis.order)
    knot = basis.knots
    denominator = knot[np.arange(basis.order - 1) + 4] - knot[np.arange(basis.order - 1) + 1]
    cx = np.diff(coefficients, axis=0) * (3 / denominator / basis.width)[:, None]
    cy = np.diff(coefficients, axis=1) * (3 / denominator / basis.height)[None, :]
    return {"sample_count_per_axis": samples,
            "maximum_sampled_abs_outward_w_mm": float(abs(w[jw])), "outward_w_witness_xy_mm": points[jw].tolist(),
            "minimum_sampled_outward_w_mm": float(w.min()), "maximum_sampled_outward_w_mm": float(w.max()),
            "maximum_sampled_abs_w_over_panel_height": float(abs(w[jw]) / basis.height),
            "maximum_sampled_slope_norm": float(slope[js]), "slope_witness_xy_mm": points[js].tolist(),
            "slope_angle_marker_rad": float(np.arctan(slope[js])),
            "sampled_best_affine_outward_field_coefficients_mm_mm_per_mm": affine.tolist(),
            "maximum_sampled_affine_removed_warp_mm": float(abs(warp[jb])),
            "warp_witness_xy_mm": points[jb].tolist(),
            "absolute_outward_w_coefficient_convex_hull_bound_mm": float(abs(coefficients).max()),
            "absolute_slope_x_derivative_coefficient_bound": float(abs(cx).max()),
            "absolute_slope_upslope_derivative_coefficient_bound": float(abs(cy).max()),
            "linear_plate_applicability_established": False,
            "limit": "Absolute displacement and slope include assembly motion. Affine removal is a sampled diagnostic, not a geometrically nonlinear solution or an adopted drift criterion."}


def integrated_net_diagnostics(panel: dict, q: np.ndarray, samples: int = 41) -> dict:
    """Integrate saved continuum resultants over actual full-bore net cuts.

    The source applied-vector rigid-wrench correction has no unique physical
    distributed force field. Do not invent one to claim exact local cut
    equilibrium; these integrations remain resolution diagnostics.
    """
    basis = panel["basis"]
    z, weights = leggauss(4)
    cuts = []
    convert = panel_method.N_PER_LBF / 304.8
    for direction in (0, 1):
        length, transverse = (basis.width, basis.height) if direction == 0 else (basis.height, basis.width)
        locations = np.unique(np.r_[np.linspace(.001, length - .001, samples),
                                   [r["xy_mm"][direction] for r in panel["holes"]]])
        knots = np.unique(basis.knots) * transverse
        for location in locations:
            spans = panel_method.net_intervals(panel, direction, location)
            points, areas = [], []
            for lo, hi in spans:
                subdivisions = np.r_[lo, knots[(knots > lo) & (knots < hi)], hi]
                for a, b in pairwise(subdivisions):
                    p = np.zeros((4, 2)); p[:, direction] = location
                    p[:, 1 - direction] = (a + b) / 2 + (b - a) / 2 * z
                    points.extend(p); areas.extend(weights * (b - a) / 2)
            fields = plate_fields(panel, np.asarray(points), q)
            areas = np.asarray(areas)
            axis = "x" if direction == 0 else "upslope"
            bending = float(areas @ fields[f"bending_{axis}_nmm_per_mm"])
            rolling = float(areas @ fields[f"rolling_{axis}_n_per_mm"])
            axial = float(areas @ fields[f"membrane_{axis}_n_per_mm"])
            width = float(areas.sum())
            cuts.append({"cut_axis": axis, "cut_coordinate_mm": float(location),
                         "net_full_bore_width_mm": width, "signed_bending_nmm": bending,
                         "signed_rolling_shear_n": rolling, "signed_membrane_axial_n": axial,
                         "mean_net_bending_ratio_CD1": abs(bending) / ((775 if direction == 0 else 455) * 25.4 * convert * width),
                         "mean_net_rolling_shear_ratio_CD1": abs(rolling) / (350 * convert * width),
                         "mean_net_axial_ratio_CD1": abs(axial) / (([5100, 3400] if axial >= 0 else [4800, 2900])[direction] * convert * width)})
    return {"cut_count": len(cuts), "simultaneous_signed_cut_witnesses": {
        key: max(cuts, key=lambda row: row[key]) for key in
        ("mean_net_bending_ratio_CD1", "mean_net_rolling_shear_ratio_CD1", "mean_net_axial_ratio_CD1")},
        "status": "INTEGRATED_GLOBAL_PLATE_RESOLUTION_DIAGNOSTIC",
        "local_hole_seat_edge_or_hold_capacity_accepted": False}


def screw_references(row: dict, thickness: float) -> dict:
    tension, lateral = float(row["withdrawal_n"]), float(row["lateral_n"])
    local = np.asarray(row["local_force_n"], dtype=float)
    panel_method.require(tension >= -1e-9 and local.shape == (3,)
                         and abs(tension - local[0]) < 1e-7
                         and abs(lateral - np.linalg.norm(local[1:])) < 1e-7,
                         "screw scalar demands differ from simultaneous signed local force")
    head = panel_method.scalar_head_reference(thickness)
    capacity_per_thread_mm = 2850 * .50**2 * .190 * panel_method.N_PER_LBF / 25.4
    annulus = math.pi * (9**2 - 5**2) / 4
    return {**row, "generic_head_reference_n_CD1": head, "generic_head_ratio_CD1": tension / head,
            "generic_head_ratio_conditional_CD1p6": tension / (1.6 * head),
            "generic_withdrawal_required_effective_thread_mm_CD1": tension / capacity_per_thread_mm,
            "generic_withdrawal_required_effective_thread_mm_conditional_CD1p6": tension / (1.6 * capacity_per_thread_mm),
            "gross_nominal_length_after_panel_mm": 63.5 - thickness,
            "projected_annulus_mean_pressure_mpa": tension / annulus,
            "same_axis_simultaneous_lateral_n": lateral,
            "Hillman_product_capacity_or_stiffness_established": False,
            "local_conical_indentation_punching_edge_capacity_established": False}


def evaluate(field_path: Path, samples: int = 41) -> dict:
    from scripts import thin_bolted_finished_support_audit as support_audit

    method_path = Path(panel_method.__file__)
    pins = {str(method_path.relative_to(ROOT)): METHOD_SHA, str(ASSESSMENT.relative_to(ROOT)): ASSESSMENT_SHA,
            str(VALIDATION.relative_to(ROOT)): VALIDATION_SHA, str(DATUMS.relative_to(ROOT)): DATUMS_SHA,
            str(Path(support_audit.__file__).relative_to(ROOT)): SUPPORT_AUDIT_SHA}
    verify_pins(pins)
    field_sha = panel_method.sha(field_path)
    state = json.loads(field_path.read_text())
    validate_state(state)
    audit = support_audit.audit_finished_state(state)
    panel_method.require(audit["independent_finished_support_and_equilibrium_checks_pass"],
                         "independent finished support and arithmetic gate failed")
    verify_pins(state["source_sha256"])
    panel_method.require(state["source_sha256"].get("scripts/thin_bolted_panel_mechanics.py") == METHOD_SHA,
                         "coupled state used another panel method")
    assessment = json.loads(ASSESSMENT.read_text())
    integrated = json.loads(panel_method.INTEGRATED.read_text())
    layout = json.loads(panel_method.LAYOUT.read_text())
    panels = prepared_datums(state, assessment, json.loads(DATUMS.read_text()), integrated)
    expected = {row["axis_id"]: row for row in layout["screw_axes"]}
    actions = state["panel_screw_actions"]
    panel_method.require(len(actions) == 66 and {r["axis_id"] for r in actions} == set(expected),
                         "sixty-six unique retained screw actions required")
    screws = []
    for row in actions:
        source = expected[row["axis_id"]]
        panel = panels[row["panel"]]
        g = panel["geometry"]
        force = np.asarray(row["force_on_receiver_xyz_n"])
        projected = force @ g["axes"][:, [2, 0, 1]]
        point = np.asarray(source["origin_xyz_mm"]) + g["inward"] * panel["thickness"] / 2
        panel_method.require(row["panel"] == source["panel"] and row["receiver"] == source["receiver"]
                             and np.max(abs(point - row["point_xyz_mm"])) < 1e-6
                             and np.max(abs(projected - row["local_force_n"])) < 1e-6,
                             "same-axis ownership, point or signed world force differs")
        screws.append(screw_references(row, panel["thickness"]))
    rows = []
    for name, panel in panels.items():
        q = panel["q"]
        resolved = panel_method.resolved_section_references(panel, q, samples)
        points = np.asarray([r["xy_mm"] for r in resolved["components"].values()])
        simultaneous = plate_fields(panel, points, q)
        owned = [r for r in screws if r["panel"] == name]
        peak = max(owned, key=lambda r: r["withdrawal_n"])
        rows.append({"panel": name, "state_id": state["state_id"], "case_id": state["case_id"],
                     "accessory_placement": state["accessory_placement"],
                     "head_witness": peak, "resolved_section_diagnostics": resolved,
                     "simultaneous_fields_at_section_witnesses": [
                         {"governing_component": key, "xy_mm": points[i].tolist(),
                          **{k: float(v[i]) for k, v in simultaneous.items()}}
                         for i, key in enumerate(resolved["components"])],
                     "integrated_net_section_diagnostics": integrated_net_diagnostics(panel, q, samples),
                     "edge_transfer_diagnostics": panel_method.edge_transfer_diagnostics(panel, q, samples),
                     "deformation_diagnostics": deformation_diagnostics(panel, q, samples)})
    pins.update(state["source_sha256"])
    pins[str(field_path.resolve().relative_to(ROOT))] = field_sha
    pins[str(Path(__file__).resolve().relative_to(ROOT))] = panel_method.sha(Path(__file__))
    result = {"schema": "thin_bolted_coupled_panel_diagnostics/v1", "candidate": state["candidate"],
              "revision": state["revision"], "state_id": state["state_id"], "case_id": state["case_id"],
              "accessory_placement": state["accessory_placement"], "parameters": state["parameters"],
              "source_sha256": pins, "field_sha256": field_sha,
              "source_equilibrium_verification": state["equilibrium_verification"],
              "independent_finished_support_and_equilibrium_audit": audit,
              "disposition": "SAME_STATE_CONDITIONAL_COUPLED_PANEL_DIAGNOSTICS",
              "panel_diagnostics": rows, "screw_actions_and_generic_references": screws,
              "maximum_head_witness": max(screws, key=lambda r: r["withdrawal_n"]),
              "method": {"saved_coefficients_used_directly": True, "global_slice_identity_checked": True,
                         "geometry_recreated": False, "stiffness_assembled": False, "new_solve": False,
                         "panel_method_SHA256": METHOD_SHA, "reference_tests_reused": str(VALIDATION.relative_to(ROOT))},
              "limits": ["Conditional Hillman/fitting/contact stiffness scenarios are not measured or physical demand bounds.",
                         "Global cubic plate fields do not resolve free opening boundaries, actual hold/T-nut footprints, conical seats, punching or screw edge-out.",
                         "Generic NDS head/wood-screw references are not a Hillman 42605 product rating. Effective threaded embedment and screw steel/lateral resistance are unavailable.",
                         "CAT23/32 thickness and owner horizontal original 8 ft plywood direction are used. Nominal 3/4 thickness requires a fresh compatible field.",
                         "CD1 is the reported generic reference; CD1.6 is conditional wind/earthquake comparison only. Permanent-load CD0.9/creep acceptance is not supplied.",
                         "Pressure is projected annulus mean demand, not a conical indentation or rupture capacity. No capacity is invented for local punching/edge action.",
                         "Sampled bending/rolling/net/edge peaks require mesh and loading-footprint convergence; small-displacement applicability remains unresolved.",
                         "Independent finished-support/arithmetic gate verifies geometry and arithmetic only. Solver convergence does not establish structural acceptance."],
              "release": RELEASE, "complete_panel_resistance_established": False}
    verify_pins(pins)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--field", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=41)
    args = parser.parse_args()
    panel_method.require(args.samples >= 4, "at least four samples per axis required")
    result = evaluate(args.field, args.samples)
    with args.out.open("x") as stream:
        stream.write(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "state_id": result["state_id"],
                      "sha256": panel_method.sha(args.out),
                      "peak_head_n": result["maximum_head_witness"]["withdrawal_n"]}))


if __name__ == "__main__":
    main()
