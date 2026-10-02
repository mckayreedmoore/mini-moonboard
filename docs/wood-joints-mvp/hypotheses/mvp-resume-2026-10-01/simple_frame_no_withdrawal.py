"""Six-case frame scenario giving Hillman withdrawal stiffness no credit."""

import fcntl
import json
import time
from pathlib import Path

import numpy as np
import simple_frame as frame
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
WITHDRAWAL_ROLE = "non_qualifying_parametric_screw_withdrawal"


def demand_change(original, scenario):
    return {
        "original": float(original),
        "zero_withdrawal": float(scenario),
        "change": float(scenario - original),
        "change_percent": None
        if original == 0
        else float(100 * (scenario - original) / original),
    }


def panel_normal_equilibrium(rows, body_names, source_D, source_W, original_forces):
    """Necessary panel force balance using the source connector directions.

    The upper panels have only face compression and in-plane lateral rows
    after withdrawal removal. Projection onto their outward normal requires
    a nonpositive load. Directional zeros are assessed at source-coordinate
    roundoff; this is a load-path screen, not a solver infeasibility status.
    """
    panels = []
    coefficient_tol = 1e-10
    retained = [r for r in rows if r["ownership"]["role"] != WITHDRAWAL_ROLE]
    for body in ("main_upper_left", "main_upper_right"):
        withdrawal = [
            r
            for r in rows
            if r["ownership"]["role"] == WITHDRAWAL_ROLE
            and r["ownership"]["second_body"] == body
        ]
        if len(withdrawal) != 12:
            raise ValueError("expected twelve upper-panel withdrawal axes")
        normal = np.array(withdrawal[0]["ownership"]["direction_global_xyz"])
        if any(
            frame.peak(np.array(r["ownership"]["direction_global_xyz"]) - normal)
            > coefficient_tol
            for r in withdrawal
        ):
            raise ValueError("mixed upper-panel normal directions")
        start = 6 * body_names.index(body)
        coefficients = source_D[:, start : start + 3] @ normal
        unilateral = [r["row"] for r in retained if r["family"] == "unilateral_springa"]
        bilateral = [r["row"] for r in retained if r["family"] != "unilateral_springa"]
        compression = coefficients[unilateral]
        bilateral_leakage = frame.peak(coefficients[bilateral])
        positive_coefficient = float(np.maximum(compression, 0).max())
        no_outward_path = (
            bilateral_leakage <= coefficient_tol
            and positive_coefficient <= coefficient_tol
            and float(compression.min()) < -coefficient_tol
        )
        required = normal @ (
            frame.DEAD_LOAD_FACTOR * source_W[start : start + 3, ::2]
            + source_W[start : start + 3, 1::2]
        )
        removed_ids = [r["row"] for r in withdrawal]
        contacts = [
            r["row"]
            for r in retained
            if r["ownership"]["role"] == "timber_or_panel_contact"
            and body in (r["ownership"]["first_body"], r["ownership"]["second_body"])
        ]
        panels.append(
            {
                "body": body,
                "outward_normal_xyz": normal.tolist(),
                "directional_zero_tolerance": coefficient_tol,
                "maximum_bilateral_normal_coefficient": bilateral_leakage,
                "maximum_positive_unilateral_normal_coefficient": positive_coefficient,
                "minimum_unilateral_normal_coefficient": float(compression.min()),
                "normal_contact_row_count": int(
                    np.count_nonzero(abs(compression) > coefficient_tol)
                ),
                "no_retained_outward_normal_load_path": no_outward_path,
                "required_normal_force_n_by_case": required.tolist(),
                "removed_source_rows": removed_ids,
                "original_withdrawal_normal_force_n_by_case": [
                    float(f[removed_ids] @ coefficients[removed_ids])
                    for f in original_forces.values()
                ],
                "original_contact_normal_force_n_by_case": [
                    float(f[contacts] @ coefficients[contacts])
                    for f in original_forces.values()
                ],
                "original_peak_removed_screw_force_n_by_case": [
                    float(f[removed_ids].max()) for f in original_forces.values()
                ],
            }
        )
    return panels


def necessary_static_feasibility(D, W, stiffness, unilateral, tangents):
    """Allow all floor tangents; omit elastic laws and bearing-set restrictions."""
    active = np.r_[np.flatnonzero(stiffness > 0), tangents.ravel()]
    bounds = [(0, None) if unilateral[i] else (None, None) for i in active]
    solved = linprog(
        np.zeros(len(active)),
        A_eq=frame.sparse.csc_matrix(D[active].T),
        b_eq=W,
        bounds=bounds,
        method="highs",
        options={
            "time_limit": 10.0,
            "primal_feasibility_tolerance": 1e-9,
            "dual_feasibility_tolerance": 1e-9,
            "threads": 1,
        },
    )
    return {
        "case_id": "a12-rear",
        "method": "scipy.optimize.linprog(method='highs')",
        "status_code": int(solved.status),
        "success": bool(solved.success),
        "message": solved.message,
        "iterations": int(solved.nit),
        "force_variables": len(active),
        "body_equilibrium_equalities": D.shape[1],
        "all_floor_tangents_retained": True,
        "elastic_laws_enforced": False,
        "withdrawal_force_constraint_n": 0.0,
        "primal_and_dual_feasibility_tolerance": 1e-9,
        "threads": 1,
        "time_limit_seconds": 10.0,
        "limits": "Necessary statics only; a feasible result would not establish elastic/contact-law acceptance.",
    }


def corner_demands(rows, body_names, source_D, original, scenario):
    """Compare same-case corner actions without assigning joint resistance."""
    comparisons = []
    for block in ("top_outer_left_cleat", "top_outer_right_cleat"):
        start = 6 * body_names.index(block)
        projection = source_D[:, start : start + 3]
        incident = [
            r
            for r in rows
            if block in (r["ownership"]["first_body"], r["ownership"]["second_body"])
        ]
        planes = {}
        ties = {}
        for row in incident:
            role = row["ownership"]["role"]
            if role == "candidate_bolt_lateral_plane":
                planes.setdefault(row["row_id"], []).append(row)
            elif role == "physical_bolt_outer_seat_tension":
                ties[row["row_id"].rsplit("/", 1)[0]] = row["row"]
        if len(planes) != 4 or len(ties) != 4:
            raise ValueError("incomplete top outer corner bolt identities")
        bolts = []
        for plane, components in sorted(planes.items()):
            if len(components) != 2:
                raise ValueError("expected two lateral components: " + plane)
            ids = [r["row"] for r in components]
            vectors = [-force[ids] @ projection[ids] for force in (original, scenario)]
            axis = plane.rsplit("/", 1)[0]
            bolts.append(
                {
                    "axis_id": axis,
                    "point_mm": components[0]["ownership"]["point_mm"],
                    "original_lateral_force_on_cleat_xyz_n": vectors[0].tolist(),
                    "zero_withdrawal_lateral_force_on_cleat_xyz_n": vectors[1].tolist(),
                    "lateral_resultant_n": demand_change(
                        np.linalg.norm(vectors[0]), np.linalg.norm(vectors[1])
                    ),
                    "outer_tie_n": demand_change(
                        original[ties[axis]], scenario[ties[axis]]
                    ),
                }
            )
        interfaces = []
        for host, pair in (
            ("base_rail_top", [b for b in bolts if "/rail_" in b["axis_id"]]),
            (
                "base_side_" + ("left" if block.endswith("left_cleat") else "right"),
                [b for b in bolts if "/side_" in b["axis_id"]],
            ),
        ):
            if len(pair) != 2:
                raise ValueError("incomplete corner bolt pair")
            points = np.array([b["point_mm"] for b in pair])
            center = points.mean(axis=0)
            couples = [
                np.linalg.norm(
                    np.cross(
                        points - center,
                        np.array([b[key] for b in pair]),
                    ).sum(axis=0)
                )
                for key in (
                    "original_lateral_force_on_cleat_xyz_n",
                    "zero_withdrawal_lateral_force_on_cleat_xyz_n",
                )
            ]
            contacts = [
                r["row"]
                for r in incident
                if r["ownership"]["role"] == "timber_or_panel_contact"
                and host
                in (r["ownership"]["first_body"], r["ownership"]["second_body"])
            ]
            if len(contacts) != 4:
                raise ValueError("expected four corner face-contact cells")
            interfaces.append(
                {
                    "host": host,
                    "lateral_pair_couple_nmm": demand_change(*couples),
                    "total_face_compression_n": demand_change(
                        original[contacts].sum(), scenario[contacts].sum()
                    ),
                    "peak_face_cell_force_n": demand_change(
                        original[contacts].max(), scenario[contacts].max()
                    ),
                }
            )
        comparisons.append({"cleat": block, "bolts": bolts, "interfaces": interfaces})
    return comparisons


def main():
    for name, expected in frame.PINS.items():
        if frame.sha(frame.COMP / name) != expected:
            raise ValueError("changed frame input: " + name)
    source_results = HERE / "simple-frame-results.json"
    baseline = json.loads(source_results.read_text())
    if baseline["producer_sha256"] != frame.sha(Path(frame.__file__)):
        raise ValueError("changed source scenario producer")
    source_response = HERE / "simple-frame-response.npz"
    if frame.sha(source_response) != baseline["response_sha256"]:
        raise ValueError("changed source scenario response")
    assessment = json.loads((frame.COMP / "assessment.json").read_text())
    case_ids = [r["case_id"] for r in assessment["load_columns"][::2]]
    if (
        baseline["source_sha256"] != frame.PINS
        or not baseline["source_unchanged"]
        or [c["case_id"] for c in baseline["cases"]] != case_ids
        or any(
            c["status"] != "PASS_STATIC_SCENARIO_BALANCE_AND_LAWS"
            for c in baseline["cases"]
        )
    ):
        raise ValueError("incompatible or incomplete original static scenario")
    with np.load(source_response, allow_pickle=False) as data:
        original_forces = {case: data[case + "_force_n"].copy() for case in case_ids}
    rows = json.loads((frame.COMP / "row-identities.json").read_text())
    unsupported = [r for r in rows if r["ownership"]["role"] == WITHDRAWAL_ROLE]
    if len(unsupported) != 66:
        roles = sorted({r["ownership"]["role"] for r in rows})
        raise ValueError(
            f"expected 66 parametric withdrawal rows; got {len(unsupported)}; roles {roles}"
        )
    with np.load(frame.COMP / "operators.npz", allow_pickle=False) as data:
        raw_H, D, e, W = [data[key].copy() for key in ["H", "D", "e", "W"]]
    source_D = D.copy()
    panel_balance = panel_normal_equilibrium(
        rows,
        assessment["body_names_in_rigid_column_order"],
        source_D,
        W,
        original_forces,
    )
    raw_H, D, e, W, stiffness, uni, normals, tangents, T, footprints = frame.lump_floor(
        raw_H, D, e, W, rows
    )
    indices = []
    for r in unsupported:
        matches = np.flatnonzero(T[:, r["row"]])
        if len(matches) != 1 or T[matches[0], r["row"]] != 1:
            raise ValueError("withdrawal row unexpectedly lumped")
        indices.append(int(matches[0]))
    stiffness[indices] = 0
    H = (raw_H + raw_H.T) / 2
    feasibility = necessary_static_feasibility(
        D, frame.DEAD_LOAD_FACTOR * W[:, 0] + W[:, 1], stiffness, uni, tangents
    )
    result = {
        "schema": "simple_frame_no_Hillman_withdrawal/v1",
        "candidate": baseline["candidate"],
        "revision_id": baseline["revision_id"],
        "source_results_sha256": frame.sha(source_results),
        "source_response_sha256": frame.sha(source_response),
        "source_sha256": frame.PINS,
        "producer_sha256": frame.sha(Path(__file__)),
        "solver_helper_sha256": frame.sha(Path(frame.__file__)),
        "disabled_source_rows": [r["row"] for r in unsupported],
        "disabled_role": WITHDRAWAL_ROLE,
        "disabled_axes": [r["row_id"].rsplit("/", 1)[0] for r in unsupported],
        "floor_footprints": footprints,
        "settings": frame.SETTINGS,
        "check_limits": {
            "body_force_and_spring_law_n": frame.FORCE_TOL_N,
            "body_moment_nmm": frame.MOMENT_TOL_NMM,
            "held_floor_motion_mm": frame.MOTION_TOL_MM,
            "maximum_unilateral_motion_mm": 10.0,
        },
        "dead_load_factor": frame.DEAD_LOAD_FACTOR,
        "panel_normal_equilibrium_screen": panel_balance,
        "representative_necessary_static_feasibility": feasibility,
        "disabled_withdrawal_force_constraint_n": 0.0,
        "assumptions": baseline["assumptions"]
        + [
            "All 66 unsupported Hillman withdrawal springs have zero stiffness and zero force; lateral springs and face contact are retained."
        ],
        "cases": [],
        "mechanical_acceptance": False,
        "engineering_mvp_complete": False,
        "physical_release": False,
        "reviewed_geometry_changed": False,
    }
    results_path = HERE / "no-withdrawal-frame-results.json"
    if results_path.exists():
        previous = json.loads(results_path.read_text())
        if previous.get("source_sha256") == frame.PINS:
            if "prior_numerical_attempt" in previous:
                result["prior_numerical_attempt"] = previous["prior_numerical_attempt"]
            elif all(
                c.get("reason") == "QP run time limit reached; no accepted response"
                for c in previous["cases"]
            ):
                result["prior_numerical_attempt"] = {
                    key: previous[key]
                    for key in (
                        "producer_sha256",
                        "response_sha256",
                        "settings",
                        "elapsed_seconds",
                        "cases",
                    )
                }
    outputs = {}
    started = time.monotonic()
    for column in range(0, 12, 2):
        case = baseline["cases"][column // 2]["case_id"]
        failed_panel_balance = [
            {
                "body": panel["body"],
                "required_outward_normal_force_n": panel[
                    "required_normal_force_n_by_case"
                ][column // 2],
                "available_outward_normal_force_n": 0.0,
            }
            for panel in panel_balance
            if panel["no_retained_outward_normal_load_path"]
            and panel["required_normal_force_n_by_case"][column // 2]
            > frame.FORCE_TOL_N
        ]
        if failed_panel_balance and feasibility["status_code"] == 2:
            result["cases"].append(
                {
                    "case_id": case,
                    "status": "STOP_PANEL_NORMAL_EQUILIBRIUM_SCREEN",
                    "reason": "Upper-panel normal load requires withdrawal; retained face compression and in-plane lateral rows cannot supply it.",
                    "failed_panel_normal_balances": failed_panel_balance,
                    "accepted_response_available": False,
                    "peak_body_translation_mm": None,
                    "disabled_withdrawal_force_n": None,
                    "equilibrium_and_law_checks": "No accepted response; necessary panel force balance fails.",
                    "top_outer_corner_demand_comparison": None,
                }
            )
            print(case, "STOP_PANEL_NORMAL_EQUILIBRIUM_SCREEN", flush=True)
            continue
        if "prior_numerical_attempt" in result:
            report = result["prior_numerical_attempt"]["cases"][column // 2]
            result["cases"].append(report)
            print(case, report["status"], flush=True)
            continue
        try:
            f, a, q, mask, report = frame.solve_case(
                H,
                D,
                frame.DEAD_LOAD_FACTOR * e[:, column] + e[:, column + 1],
                frame.DEAD_LOAD_FACTOR * W[:, column] + W[:, column + 1],
                stiffness,
                uni,
                normals,
                tangents,
            )
            source_f = T.T @ f
            withdrawal_force = frame.peak(source_f[[r["row"] for r in unsupported]])
            if withdrawal_force != 0:
                raise ValueError("nonzero unsupported withdrawal force")
            translations = np.linalg.norm(a.reshape(-1, 6)[:, :3], axis=1)
            report["peak_body_translation_mm"] = float(translations.max())
            report["peak_translation_body"] = assessment[
                "body_names_in_rigid_column_order"
            ][int(translations.argmax())]
            report["translation_comparison_mm"] = demand_change(
                baseline["cases"][column // 2]["peak_body_translation_mm"],
                translations.max(),
            )
            report["raw_vs_symmetric_motion_mm"] = frame.peak((raw_H - H) @ f)
            report["disabled_withdrawal_force_n"] = withdrawal_force
            report["disabled_withdrawal_nonzero_count"] = int(
                np.count_nonzero(source_f[[r["row"] for r in unsupported]])
            )
            report["top_outer_corner_demand_comparison"] = corner_demands(
                rows,
                assessment["body_names_in_rigid_column_order"],
                source_D,
                original_forces[case],
                source_f,
            )
            outputs.update(
                {
                    case + "_force_n": source_f,
                    case + "_lumped_force_n": f,
                    case + "_rigid_coordinates": a,
                    case + "_motion_mm": q,
                    case + "_bearing_mask": mask,
                }
            )
        except RuntimeError as error:
            report = {"status": "STOP_STATIC_SCENARIO", "reason": str(error)}
        result["cases"].append({"case_id": case, **report})
        print(case, report["status"], flush=True)
    result["elapsed_seconds"] = time.monotonic() - started
    result["accepted_response_case_count"] = sum(
        case + "_force_n" in outputs for case in case_ids
    )
    result["source_unchanged"] = all(
        frame.sha(frame.COMP / n) == h for n, h in frame.PINS.items()
    ) and all(
        frame.sha(path) == expected
        for path, expected in (
            (source_results, result["source_results_sha256"]),
            (source_response, result["source_response_sha256"]),
            (Path(frame.__file__), result["solver_helper_sha256"]),
        )
    )
    if not result["source_unchanged"]:
        raise ValueError("frame source changed during calculation")
    response = HERE / "no-withdrawal-frame-response.npz"
    np.savez_compressed(response, **outputs)
    result["response_sha256"] = frame.sha(response)
    results_path.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    lock = frame.ROOT / "docs/wood-joints-mvp/luna-max-native-run-ledger.lock"
    with lock.open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if json.loads(lock.with_suffix(".json").read_text())["slot"]["state"] != "idle":
            raise RuntimeError("shared analysis slot is occupied")
        main()
