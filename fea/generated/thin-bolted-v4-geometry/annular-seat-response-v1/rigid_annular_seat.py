"""Pure rigid frictionless annular-seat response under declared normal bedding.

Circular-cap integration supplies response, not washer bending, strength,
actual seat occupancy, preload, friction, or external rotational restraint.
"""
import argparse
import copy
import json
import math
import platform
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np
import scipy
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts import thin_bolted_steel_resistance as steel

PROFILE_PATH = ROOT / "fea/generated/thin-bolted-b104-local-hardware-inputs/inputs.json"
PROFILE_SHA = "8cebc830001ed86114bce7363f7fc3a0105c258885cdaa80a869245bea73d731"


def disk_cap(radius, cutoff):
    """[area, first X moment, second X moment, second Y moment] for X>cutoff."""
    if cutoff >= radius:
        return np.zeros(4)
    if cutoff <= -radius:
        return np.array([math.pi * radius**2, 0., math.pi * radius**4 / 4,
                         math.pi * radius**4 / 4])
    root = math.sqrt(max(0., radius**2 - cutoff**2))
    angle = math.acos(cutoff / radius)
    return np.array([radius**2 * angle - cutoff * root,
                     2 * root**3 / 3,
                     radius**4 * angle / 4 + cutoff * root * (radius**2 - 2 * cutoff**2) / 4,
                     radius**4 * angle / 4 - cutoff * root * (5 * radius**2 - 2 * cutoff**2) / 12])


def response(*, inner_radius_mm, outer_radius_mm, bedding_n_mm3,
             normal_approach_mm, closure_slopes):
    """Energy, resisting gradient and same-state tangent for d=delta+sx*x+sy*y.

    Positive delta is downward approach. Local +z points from receiving body
    toward washer. sx=theta_y and sy=-theta_x in the first-order rigid kinematics.
    """
    a = steel.number(inner_radius_mm, "inner radius", positive=True)
    b = steel.number(outer_radius_mm, "outer radius", positive=True)
    k = steel.number(bedding_n_mm3, "declared normal bedding", positive=True)
    delta = steel.number(normal_approach_mm, "normal approach")
    slope = np.asarray(closure_slopes, dtype=float)
    if b <= a or slope.shape != (2,) or not np.isfinite(slope).all():
        raise ValueError("ordered annulus radii and finite two-component closure slope required")
    tilt = float(np.linalg.norm(slope))
    full_area, full_inertia = math.pi * (b*b-a*a), math.pi * (b**4-a**4) / 4
    if tilt == 0.:
        area = full_area if delta > 0. else 0.
        first = np.zeros(2)
        second = np.eye(2) * (full_inertia if delta > 0. else 0.)
    else:
        area, q, j_parallel, j_perpendicular = disk_cap(b, -delta/tilt) - disk_cap(a, -delta/tilt)
        direction = slope/tilt
        first = q * direction
        projector = np.outer(direction, direction)
        second = j_parallel * projector + j_perpendicular * (np.eye(2)-projector)
    moment_matrix = np.empty((3, 3))
    moment_matrix[0, 0] = area
    moment_matrix[0, 1:] = moment_matrix[1:, 0] = first
    moment_matrix[1:, 1:] = second
    tangent = k * moment_matrix
    state = np.r_[delta, slope]
    gradient = tangent @ state
    energy = float(state @ gradient / 2)
    physical_moment = np.array([gradient[2], -gradient[1], 0.])
    physical_force = np.array([0., 0., gradient[0]])
    # Relative DOFs=[ux,uy,uz,theta_x,theta_y,theta_z] at annulus center.
    closure_map = np.array([[0., 0., -1., 0., 0., 0.],
                            [0., 0., 0., 0., 1., 0.],
                            [0., 0., 0., -1., 0., 0.]])
    six_tangent = closure_map.T @ tangent @ closure_map
    np.testing.assert_allclose(-closure_map.T @ gradient, np.r_[physical_force, physical_moment], atol=0, rtol=0)
    if area == 0.:
        state_kind = "zero-pressure-touching" if delta == 0. and tilt == 0. else "open-or-point-grazing"
    elif delta >= b * tilt:
        state_kind = "full-contact-nonnegative-pressure"
    else:
        state_kind = "partial-contact"
    return {"energy_nmm": energy, "resisting_gradient_N_Gx_Gy": gradient.tolist(),
            "tangent_delta_sx_sy": tangent.tolist(), "relative_six_dof_tangent": six_tangent.tolist(),
            "force_on_washer_local_xyz_n": physical_force.tolist(),
            "moment_on_washer_at_annulus_center_local_xyz_nmm": physical_moment.tolist(),
            "force_on_receiving_body_local_xyz_n": (-physical_force).tolist(),
            "moment_on_receiving_body_at_annulus_center_local_xyz_nmm": (-physical_moment).tolist(),
            "active_area_mm2": float(area), "contact_state": state_kind,
            "pressure_min_mpa": max(0., k*(delta-b*tilt)), "pressure_max_mpa": max(0., k*(delta+b*tilt)),
            "full_contact_kernel_radius_mm": full_inertia/(full_area*b)}


def cap_strip_oracle(a, b, cutoff):
    """Independent 1D integration across actual annular strips, no cap formula."""
    def terms(x):
        outside = math.sqrt(max(0., b*b-x*x))
        inside = math.sqrt(max(0., a*a-x*x))
        width = 2 * (outside-inside)
        return [width, x*width, x*x*width, 2*(outside**3-inside**3)/3]
    left = max(-b, cutoff)
    breaks = sorted(set([left, b] + [v for v in (-a, a) if left < v < b]))
    answer = []
    errors = []
    for component in range(4):
        value, error = 0., 0.
        for lo, hi in pairwise(breaks):
            integral, bound = quad(lambda x, j=component: terms(x)[j], lo, hi, epsabs=1e-8, epsrel=1e-12)
            value += integral
            error += bound
        answer.append(value)
        errors.append(error)
    return np.array(answer), errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    given = json.loads(args.input.read_bytes())
    assert steel.sha(ROOT / given["source_layout_path"]) == given["source_layout_sha256"]
    assert steel.sha(PROFILE_PATH) == PROFILE_SHA
    profile = json.loads(PROFILE_PATH.read_bytes())
    selected = {r["axis_id"] for r in given["selected_axis_profiles"]}
    assert selected == {r["axis_id"] for r in profile["stacks"]}
    for row in profile["stacks"]:
        h = row["frozen_occupancy"]["hardware_scenario"]
        assert [h["washer_od_mm"], h["washer_id_mm"], h["washer_thickness_mm"]] == [35.052, 14.2875, 3.3528]
    paths = [Path(__file__), args.input.resolve(), ROOT / given["source_layout_path"], PROFILE_PATH,
             ROOT / "scripts/thin_bolted_steel_resistance.py", ROOT / "tests/test_thin_bolted_steel_resistance.py",
             ROOT / "scripts/thin_bolted_numerical_step.py", ROOT / "fea/current_response_materials.py",
             ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/timber-face-contact-method-v4.json"]
    pins = {str(p.resolve().relative_to(ROOT)): steel.sha(p) for p in paths}
    assert all(steel.sha(ROOT / path) == digest for path, digest in pins.items())
    a, b, k = [given[name] for name in ("inner_radius_mm", "outer_radius_mm", "bedding_n_mm3")]
    assert [a, b, k] == [7.14375, 17.526, 1.]
    A, I = math.pi*(b*b-a*a), math.pi*(b**4-a**4)/4
    def evaluate(q):
        return response(inner_radius_mm=a, outer_radius_mm=b, bedding_n_mm3=k,
                        normal_approach_mm=float(q[0]), closure_slopes=q[1:])
    saved_input = copy.deepcopy(given)
    results = []
    by_id = {}
    for item in given["states"]:
        q = np.array(item["q"], dtype=float)
        out = evaluate(q)
        H, H6 = np.array(out["tangent_delta_sx_sy"]), np.array(out["relative_six_dof_tangent"])
        assert np.array_equal(H, H.T) and np.array_equal(H6, H6.T)
        assert np.linalg.eigvalsh(H).min() >= -1e-8
        expected_rank = 3 if out["active_area_mm2"] > 0 else 0
        assert np.linalg.matrix_rank(H) == np.linalg.matrix_rank(H6) == expected_rank
        for component in (0, 1, 5):
            assert np.count_nonzero(H6[:, component]) == 0
        pressure = steel.annulus_pressure(axial_n=out["resisting_gradient_N_Gx_Gy"][0],
                moment_xy_nmm=out["moment_on_washer_at_annulus_center_local_xyz_nmm"][:2],
                inner_radius_mm=a, outer_radius_mm=b)
        row = {"id": item["id"], "q_delta_sx_sy": q.tolist(), **out,
               "existing_full_annulus_resultant_check": pressure, "tangent_rank": expected_rank,
               "six_dof_horizontal_translation_and_yaw_columns_exact_zero": True,
               "reciprocity_exact": True}
        if item["id"] in ("full", "half-annulus", "general-cap", "reverse-cap"):
            steps = [1e-6, 1e-8, 1e-8]
            finite_H, finite_gradient = np.empty((3, 3)), np.empty(3)
            for component, step in enumerate(steps):
                plus, minus = q.copy(), q.copy()
                plus[component] += step; minus[component] -= step
                pp, pm = evaluate(plus), evaluate(minus)
                finite_H[:, component] = (np.array(pp["resisting_gradient_N_Gx_Gy"])-np.array(pm["resisting_gradient_N_Gx_Gy"]))/ (2*step)
                finite_gradient[component] = (pp["energy_nmm"]-pm["energy_nmm"])/(2*step)
            np.testing.assert_allclose(finite_H, H, atol=1e-5, rtol=2e-7)
            np.testing.assert_allclose(finite_gradient, out["resisting_gradient_N_Gx_Gy"], atol=1e-6, rtol=2e-7)
            row.update(finite_difference_tangent_max_abs_error=float(abs(finite_H-H).max()),
                       finite_difference_energy_gradient_max_abs_error=float(abs(finite_gradient-out["resisting_gradient_N_Gx_Gy"]).max()))
        results.append(row); by_id[item["id"]] = row
    full = by_id["full"]
    fullq = np.array(full["q_delta_sx_sy"])
    np.testing.assert_allclose(full["resisting_gradient_N_Gx_Gy"], k*np.array([A*fullq[0], I*fullq[1], I*fullq[2]]), rtol=2e-15, atol=1e-12)
    np.testing.assert_allclose(full["tangent_delta_sx_sy"], k*np.diag([A, I, I]), rtol=2e-15, atol=1e-10)
    half = by_id["half-annulus"]
    slope = np.array(half["q_delta_sx_sy"])[1:]; tilt = float(np.linalg.norm(slope)); e = slope/tilt
    Q = 2*(b**3-a**3)/3
    np.testing.assert_allclose(half["resisting_gradient_N_Gx_Gy"], np.r_[k*tilt*Q, k*tilt*I*e/2], rtol=2e-15)
    assert math.isclose(half["energy_nmm"], k*tilt*tilt*I/4, rel_tol=2e-15)
    assert math.isclose(half["active_area_mm2"], A/2, rel_tol=2e-15)
    assert half["existing_full_annulus_resultant_check"]["full_contact_admissible"] is False
    cap_q = np.array(by_id["general-cap"]["q_delta_sx_sy"])
    cutoff = -cap_q[0]/float(np.linalg.norm(cap_q[1:]))
    exact_moments = disk_cap(b, cutoff)-disk_cap(a, cutoff)
    oracle, errors = cap_strip_oracle(a, b, cutoff)
    np.testing.assert_allclose(exact_moments, oracle, rtol=2e-12, atol=1e-8)
    cap, reverse = by_id["general-cap"], by_id["reverse-cap"]
    assert cap["energy_nmm"] == reverse["energy_nmm"] and cap["active_area_mm2"] == reverse["active_area_mm2"]
    np.testing.assert_allclose(np.array(cap["resisting_gradient_N_Gx_Gy"])*[1., -1., -1.], reverse["resisting_gradient_N_Gx_Gy"], rtol=0, atol=0)
    for name in ("open", "point-grazing", "zero-pressure"):
        row = by_id[name]
        assert row["energy_nmm"] == 0. and row["resisting_gradient_N_Gx_Gy"] == [0., 0., 0.] and row["active_area_mm2"] == 0.
    assert given == saved_input
    original_full = evaluate(saved_input["states"][0]["q"])
    evaluate([-.1, 0., 0.])
    assert evaluate(saved_input["states"][0]["q"]) == original_full
    # Replay the existing fixture rather than transfer its pass as new physics.
    old_fixture = steel.annulus_pressure(axial_n=100., moment_xy_nmm=(1000., 0.), inner_radius_mm=5., outer_radius_mm=10.)
    assert old_fixture["full_contact_admissible"] is False and old_fixture["moment_full_contact_limit_nmm"] == 312.5
    report = {"schema": "thin_bolted_rigid_annular_seat_response_coupon/v1",
        "command": [sys.executable, str(Path(__file__).resolve()), "--input", str(args.input), "--output", str(args.output)],
        "source_sha256": pins, "geometry_and_bedding_inputs": given,
        "reuse_gap": "Existing full-annulus pressure and prescribed-pressure washer bending have no rigid compression-only partial-annulus response/tangent.",
        "law": "d(x,y)=delta+sx*x+sy*y; p=k*max(d,0); E=.5*k*integral(max(d,0)^2); R=integral(p*[1,x,y]); H=k*integral_active([1,x,y]^T*[1,x,y])",
        "slope_to_rotation": "sx=theta_y, sy=-theta_x; delta=-uz at local annulus center; horizontal translations and yaw are free",
        "physical_wrench": "Traction on washer is +z: N=int(p), Mx=int(p*y)=Gy, My=-int(p*x)=-Gx, Mz=0; receiving body receives exactly opposing force/moment",
        "full_contact_condition": "For uniform linear bedding, N>0 and ||Mxy||<=N*I/(A*b)=N*(a^2+b^2)/(4*b); strict inequality gives positive pressure everywhere. N=0,M=0 is zero pressure, not proof of bearing contact.",
        "full_contact_condition_is_moment_strength_or_capacity": False,
        "full_annulus_area_mm2": A, "full_annulus_second_moment_mm4": I, "full_contact_kernel_radius_mm": I/(A*b),
        "rows": results, "general_cap_strip_oracle": {"cutoff_mm": cutoff, "closed_form_A_Q_Jparallel_Jperp": exact_moments.tolist(),
            "independent_quadrature_A_Q_Jparallel_Jperp": oracle.tolist(), "quadrature_error_estimates": errors},
        "existing_full_annulus_fixture_replayed": old_fixture, "stateless_input_and_trial_replay_unchanged": True,
        "zero_closure_generalized_tangent": "Entire annulus at d=0 uses inactive zero generalized tangent, matching strict-positive normal activation; FD tests avoid that degenerate state and circle-edge tangencies.",
        "tool_versions": {"python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__},
        "limits": ["Uniform bedding1N/mm3 is a declared response scenario, not measured seat/wood/steel compliance or a strength bound.",
            "Rigid full nominal/max-envelope annulus is an analytical domain, not actual delivered contact area or minimum washer dimensions.",
            "Actual washer bending, head/nut pressure footprint, local wood strength/fracture and complete joint response remain separate.",
            "No friction, preload, tensile contact, free yaw couple or external tilt clamp is added.",
            "Closed-form double arithmetic near a vanishing cap or a numerically thin annulus is not independently bounded by these moderate-cap coupons."],
        "new_geometry_or_current_forces": False, "candidate_global_floor_native_or_CAD_solved": False,
        "actual_product_qualified": False, "capacity_established": False, "complete_joint_acceptance": False, "released": False}
    assert all(steel.sha(ROOT / path) == digest for path, digest in pins.items())
    with args.output.open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"output": str(args.output), "source_sha256": steel.sha(Path(__file__)),
                     "input_sha256": steel.sha(args.input), "result_sha256": steel.sha(args.output),
                     "response_states_passed": len(results), "full_contact_kernel_radius_mm": I/(A*b), "capacity_established": False}))


if __name__ == "__main__":
    main()
