"""Read-only v5 certificate checks and exact cone/aggregation qualifications."""

import importlib.util
import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


h = module("local_v5", OUT / "local-contract-v5.py")


def main():
    target = OUT / "verification-v5.json"
    if target.exists():
        raise FileExistsError("preserve issued evidence")
    config = json.loads((OUT / "input-v5.json").read_text())
    result = json.loads((OUT / "result-v5.json").read_text())
    pins = result["source_sha256"] | {str((OUT / "result-v5.json").relative_to(h.ROOT)): h.sha(OUT / "result-v5.json"),
        str((OUT / "review-v2.py").relative_to(h.ROOT)): h.sha(OUT / "review-v2.py")}
    h.verify(pins)
    read = lambda key: json.loads((h.ROOT / config[key]).read_text())
    layout, unit, cache, direct = (read(k) for k in ("layout", "timber_unit_geometry", "geometry_cache", "direct_timber_geometry"))
    shafts = h.shaft_inputs(layout, unit, cache)
    checks = []
    for patch, saved in zip(config["patches"], result["results"], strict=True):
        bodies, reference, E, N, T, D, _ = h.operators(patch, layout, shafts, 100., direct)
        rods = [s for s in shafts if s["axis_id"] in patch["axes"]]
        rolls, global_modes = h.rod_rolls(bodies, rods, reference, 100.), h.global_modes(bodies)
        matrices = {"nominal_touch_normals_only": N, "touch_normals_plus_annular_tilt_potential": np.vstack((N, T)),
            "all_radial_bilateral_plus_touch_normal_envelope": np.vstack((E, N)), "all_radial_normal_plus_annular_envelope": np.vstack((E, N, T)),
            "conditional_direct_timber_plus_touch_normals": np.vstack((N, D)),
            "conditional_direct_timber_plus_radial_normal_envelope": np.vstack((E, N, D))}
        stored = next(r for r in saved["scale_checks"] if r["scale_mm"] == 100.)["diagnostics"]
        row_checks = {}
        for name, A in matrices.items():
            Z = np.asarray(stored[name]["full_null_basis_q_columns"])
            errors = {"null_residual": float(np.max(abs(A @ Z))), "orthonormal_error": float(np.max(abs(Z.T @ Z - np.eye(Z.shape[1])))),
                "six_global_mode_residual": float(np.max(abs(A @ global_modes))), "shaft_roll_residual": float(np.max(abs(A @ rolls)))}
            assert max(errors.values()) < 1e-9
            row_checks[name] = errors
        base_cert = saved["nominal_touch_cone_certificate"]["reviewed_bracket_contact_only"]
        weights = np.asarray(base_cert["positive_coefficients"])
        assert min(weights) > 0 and np.max(abs(N.T @ weights)) < 1e-9
        opened = saved["nominal_touch_cone_certificate"]["conditional_added_direct_timber"]
        values = np.vstack((N, D)) @ np.asarray(opened["feasible_opening_direction_q"])
        assert min(values) > -1e-9 and max(values) > 1e-6
        dual_checks, incompatible_witnesses = [], []
        for name, units in saved["signed_balanced_unit_loads"].items():
            radial = E if "radial" in name else np.zeros((0, len(bodies)*6))
            normal = np.vstack((N, D)) if "direct" in name else N
            matrix = np.column_stack((radial.T, normal.T))
            for row in units:
                load = np.asarray(row["generalized_body_load_vector"])
                for direction, sign in (("positive", 1.), ("negative", -1.)):
                    certificate = row["conditional_rigid_reaction_cone_checks"][direction]
                    if certificate["compression_reaction_cone_feasible"]:
                        coeff = np.r_[certificate["radial_bilateral_multipliers"], certificate["normal_nonnegative_multipliers"]]
                        residual = float(np.max(abs(matrix @ coeff + sign*load)))
                        assert min(certificate["normal_nonnegative_multipliers"]) >= -1e-10 and residual < 1e-9
                        dual_checks.append({"id": row["id"], "family": name, "sign": sign, "residual": residual})
                    else:
                        if "direct_touch" not in name:
                            raise ValueError("unexpected incompatible unit family")
                        timber = row["id"].split("/")[0]
                        index = 6*bodies.index(timber)
                        opening_axis = np.array([0., 0., -1. if timber == "base_post_center_left" else 1.])
                        q = np.zeros(len(bodies)*6)
                        if row["id"].endswith("/unit_Fz"):
                            q[index:index+3] = opening_axis
                        else:
                            axis = sign*np.asarray(row["timber_vs_header_wrench_at_reference"])[3:]
                            rod = next(s for s in rods if any(r["host"] == timber for r in s["surfaces"]))
                            q[index:index+3] = np.cross(axis, reference-rod["point"])
                            q[index+3:index+6] = 100.*axis
                            slope = normal @ q
                            translation = np.zeros_like(q); translation[index:index+3] = opening_axis
                            derivative = normal @ translation
                            lift = max((-slope[i]/derivative[i] for i in range(len(slope)) if derivative[i] > .5), default=0.) + 1.
                            q += lift*translation
                        openings = normal @ q
                        work = float(sign*load @ q)
                        assert min(openings) > -1e-9 and work > .9
                        incompatible_witnesses.append({"id": row["id"], "family": name, "sign": sign,
                            "feasible_opening_direction_q": q.tolist(), "normal_opening_derivatives": openings.tolist(),
                            "positive_external_virtual_work_nmm": work,
                            "proof": "If load=-N.T*lambda with lambda>=0, its work on Nq>=0 cannot be positive; this opening ray disproves that load sign."})
        checks.append({"patch": patch["id"], "row_checks": row_checks, "positive_self_stress_residual": float(np.max(abs(N.T @ weights))),
            "conditional_direct_opening_witness_minimum_derivative": float(min(values)), "maximum_derivative": float(max(values)),
            "feasible_dual_certificate_checks": dual_checks, "independent_incompatible_load_opening_witnesses": incompatible_witnesses})
    known = module("old_work_fixture", OUT / "review-v2.py").fixture_checks()
    h.verify(pins)
    pins[str(Path(__file__).relative_to(h.ROOT))] = h.sha(Path(__file__))
    target.write_text(json.dumps({"status": "PURE_CERTIFICATE_VERIFICATION_AND_SCOPE_QUALIFICATION", "source_sha256": pins,
        "known_answer_checks": known, "checks": checks,
        "qualifications_superseding_v5_labels": {
            "touch_cone_lineality_equals_all_normal_nullspace": "The intended tested proposition is ENTIRE touch cone=kerN. Its lineality is ALWAYS kerN, since q and -q are feasible iff Nq=0. The positive self-stress proves entire cone=kerN; the direct opening witness disproves entire equality.",
            "admissible_wrench_basis_and_work_dimension": "These SVD keys mean annihilators of kernel/lineality. They are not signed compression-cone admissibility, active response, stiffness or capacity. Signed unit feasibility has separate primal/dual certificates.",
            "hardware_aggregation": "Five/eight rigid aggregate bodies optimistically contract 11/17 native hardware bodies. Six/nine extra independent nut/washer axial roll gauges are omitted only as unobserved frictionless coordinates, never credited as torsional restraint. Native profiles must retain them; no axis-spin friction law is supplied.",
            "smallest_bidirectional_centered_gap_load_family": "Only one/two paired transverse couples are verified in both signs under the nominal touch-normal reduced contract. Conditional direct end bearing permits one-sided compression loads, not pure post-axis couples without accompanying compression.",
            "response_and_reciprocity": "No operator/compliance is computed. Cij=fi.T*qj reciprocity requires the same qualified reciprocal elastic response and fixed admitted contact branch; geometry/work feasibility does not establish it."},
        "LP_K_CAD_native_or_global_solve_used_in_verification": False}, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"helper_sha256": h.sha(Path(__file__)), "result_sha256": h.sha(target), "bytes": target.stat().st_size}))


if __name__ == "__main__":
    main()
