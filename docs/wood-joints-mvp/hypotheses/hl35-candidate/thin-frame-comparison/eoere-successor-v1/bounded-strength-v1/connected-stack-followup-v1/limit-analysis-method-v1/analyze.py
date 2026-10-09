"""Synthetic 1D bearing/bending limit benchmark, never a candidate capacity."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import scipy
import scipy.optimize._linprog_highs as highs_wrapper
from scipy.optimize import linprog
from scipy.optimize._highspy import _core

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "uv.lock").exists())
sys.path.insert(0, str(ROOT))
from fea.dowel_yield import single_shear

PACKET = Path(__file__).resolve().parent
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment():
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "highs": f"{_core.HIGHS_VERSION_MAJOR}.{_core.HIGHS_VERSION_MINOR}.{_core.HIGHS_VERSION_PATCH}",
        "scipy_highs_wrapper_sha256": sha(highs_wrapper.__file__),
    }


def check_pins(inputs):
    if environment() != inputs["environment"]:
        raise ValueError("Pinned Python/NumPy/SciPy/HiGHS environment mismatch")
    for pin in inputs["references"]:
        if sha(ROOT / pin["path"]) != pin["sha256"]:
            raise ValueError(f"Changed source: {pin['path']}")


def validate(case, cells):
    positive = (
        "main_length_in",
        "side_length_in",
        "main_bearing_lb_in",
        "side_bearing_lb_in",
        "yield_moment_lb_in",
    )
    if not all(math.isfinite(case[k]) and case[k] > 0 for k in positive):
        raise ValueError(
            "Lengths, bearing bounds and moment cap must be finite/positive"
        )
    if not math.isfinite(case["gap_in"]) or case["gap_in"] < 0:
        raise ValueError("Gap must be finite/nonnegative")
    if type(cells) is not int or not 2 <= cells <= 512:
        raise ValueError("Synthetic benchmark requires 2..512 cells per member")


def integrate(a, b, density):
    """Prefix integrate V'=q, M'=V, including gaps and all interior V=0 points.

    This recurrence is independent of the LP's convolution matrix. Coordinates,
    bearing, shear and moment use the same dimensionless scales as that matrix.
    """
    shear = moment = previous = 0.0
    points = []
    for lo, hi, q in zip(a, b, density):
        moment += shear * (lo - previous)
        points.append((float(lo), float(moment)))
        if q != 0:
            dx = -shear / q
            if 0 < dx < hi - lo:
                points.append(
                    (float(lo + dx), float(moment + shear * dx + q * dx**2 / 2))
                )
        dx = hi - lo
        moment += shear * dx + q * dx**2 / 2
        shear += q * dx
        points.append((float(hi), float(moment)))
        previous = hi
    return points, float(shear), float(moment)


def solve(case, cells, inputs):
    validate(case, cells)
    lm, ls = case["main_length_in"], case["side_length_in"]
    qm, qs = case["main_bearing_lb_in"], case["side_bearing_lb_in"]
    length = lm + ls + case["gap_in"]
    force = min(lm * qm, ls * qs)
    side = np.linspace(0, ls, cells + 1) / length
    main = np.linspace(ls + case["gap_in"], length, cells + 1) / length
    a = np.concatenate((side[:-1], main[:-1]))
    b = np.concatenate((side[1:], main[1:]))
    qcap = np.repeat([qs, qm], cells) * length / force
    weights = qcap * (b - a)
    eq = np.zeros((3, 2 * cells + 1))
    eq[0, :cells], eq[0, -1] = weights[:cells], -1
    eq[1, cells:-1], eq[1, -1] = weights[cells:], 1
    eq[2, :-1] = weights * (a + b) / 2
    # Last variable is nonnegative P/Fscale; every bearing variable is signed.
    bounds = [(-1, 1)] * (2 * cells) + [(0, None)]
    objective = np.zeros(2 * cells + 1)
    objective[-1] = -1
    cap = case["yield_moment_lb_in"] / (force * length)
    nodes = list(np.unique(np.concatenate((a, b))))
    limits = inputs["limits"]
    for round_index in range(limits["maximum_cut_rounds"]):
        matrix = np.column_stack(
            (
                np.array(
                    [
                        qcap
                        * (np.maximum(t - a, 0) ** 2 - np.maximum(t - b, 0) ** 2)
                        / 2
                        for t in nodes
                    ]
                ),
                np.zeros(len(nodes)),
            )
        )
        aub = np.concatenate((matrix, -matrix))
        bub = np.full(2 * len(nodes), cap)
        out = linprog(
            objective,
            A_ub=aub,
            b_ub=bub,
            A_eq=eq,
            b_eq=np.zeros(3),
            bounds=bounds,
            method=inputs["options"]["method"],
            options={k: v for k, v in inputs["options"].items() if k != "method"},
        )
        if not out.success or out.status != 0:
            raise RuntimeError(f"Synthetic LP failed: {out.status}: {out.message}")
        points, end_shear, end_moment = integrate(a, b, out.x[:-1] * qcap)
        maximum = max(abs(value) for _, value in points)
        cuts = [
            t
            for t, value in points
            if abs(value) > cap + limits["moment_cut_tolerance"]
        ]
        if not cuts:
            break
        nodes = sorted(set(nodes + cuts))
    else:
        raise RuntimeError("Exact interior moment cuts did not converge")

    dual = (
        bub @ out.ineqlin.marginals
        - sum(out.lower.marginals[:-1])
        + sum(out.upper.marginals[:-1])
    )
    stationarity = objective - (
        aub.T @ out.ineqlin.marginals
        + eq.T @ out.eqlin.marginals
        + out.lower.marginals
        + out.upper.marginals
    )
    certificate = {
        "equality_residual": float(max(abs(eq @ out.x))),
        "inequality_violation": float(max(0, max(aub @ out.x - bub))),
        "bearing_bound_violation": float(max(0, max(abs(out.x[:-1])) - 1)),
        "dual_stationarity_residual": float(max(abs(stationarity))),
        "primal_dual_objective_gap": float(abs(out.fun - dual)),
        "dual_sign_violation": float(
            max(
                0,
                max(out.ineqlin.marginals),
                max(-out.lower.marginals),
                max(out.upper.marginals),
            )
        ),
    }
    if max(certificate.values()) > limits["scaled_LP_residual_tolerance"]:
        raise RuntimeError(f"Synthetic LP certificate failed: {certificate}")
    # Shrink only to remove floating point/cut tolerance from statics bounds.
    # This is numerical feasibility repair, never a material/design factor.
    scale = min(1.0, 1 / max(abs(out.x[:-1])), cap / maximum)
    scale *= 1 - limits["numerical_feasible_scale_margin"]
    points, end_shear, end_moment = integrate(a, b, out.x[:-1] * qcap * scale)
    maximum = max(abs(value) for _, value in points)
    if maximum > cap * (1 + 1e-10):
        raise RuntimeError("Scaled statics field exceeds exact moment cap")
    return {
        "cells_per_member": cells,
        "raw_LP_load_lbf": float(out.x[-1] * force),
        "scaled_statics_load_lbf": float(out.x[-1] * force * scale),
        "numerical_feasibility_scale": float(scale),
        "moment_cut_rounds": round_index + 1,
        "moment_constraint_locations": len(nodes),
        "maximum_exact_moment_lb_in": maximum * force * length,
        "end_shear_lbf": end_shear * force,
        "end_moment_lb_in": end_moment * force * length,
        "scaled_LP_certificate": certificate,
    }, {
        "a_in": (a * length).tolist(),
        "b_in": (b * length).tolist(),
        "bearing_density_lb_in": (out.x[:-1] * qcap * force / length * scale).tolist(),
        "bearing_bounds_lb_in": np.repeat([qs, qm], cells).tolist(),
        "statics_load_lbf": float(out.x[-1] * force * scale),
        "moment_bound_lb_in": case["yield_moment_lb_in"],
    }


def controls(inputs):
    options = {k: v for k, v in inputs["options"].items() if k != "method"}
    signed = linprog([1.0], bounds=[(-2.0, 3.0)], method="highs-ds", options=options)
    infeasible = linprog(
        [1.0],
        A_ub=[[1.0], [-1.0]],
        b_ub=[0.0, -1.0],
        bounds=[(None, None)],
        method="highs-ds",
        options=options,
    )
    unbounded = linprog([-1.0], method="highs-ds", options=options)
    if (
        not signed.success
        or signed.x[0] != -2
        or infeasible.status != 2
        or unbounded.status != 3
    ):
        raise RuntimeError("Signed-bound/status known answers failed")
    # Default nonnegative bearing silently blocks opposing member force.
    unsigned = linprog(
        [0.0, 0.0, -1.0],
        A_eq=[[1.0, 0.0, -1.0], [0.0, 1.0, 1.0]],
        b_eq=[0.0, 0.0],
        bounds=[(0.0, 1.0)] * 2 + [(0.0, None)],
        method="highs-ds",
        options=options,
    )
    if not unsigned.success or unsigned.x[-1] != 0:
        raise RuntimeError("Wrong unsigned-bound negative control failed")
    rejected = []
    base = inputs["synthetic_cases"][0]
    for key, value in (
        ("main_length_in", 0.0),
        ("side_length_in", -1.0),
        ("main_bearing_lb_in", float("nan")),
        ("yield_moment_lb_in", float("inf")),
        ("gap_in", -1.0),
    ):
        try:
            validate({**base, key: value}, 32)
        except ValueError:
            rejected.append(key)
        else:
            raise RuntimeError(f"Invalid input accepted: {key}")
    iv = next(
        c for c in inputs["synthetic_cases"] if c["expected_raw_governing_mode"] == "IV"
    )
    capped, _ = solve(iv, 32, inputs)
    loose, _ = solve({**iv, "yield_moment_lb_in": 1e6}, 32, inputs)
    if loose["scaled_statics_load_lbf"] < 2 * capped["scaled_statics_load_lbf"]:
        raise RuntimeError("Bending-cap negative control did not expose extra load")
    symmetric, _ = solve(base, 32, inputs)
    exact_II = base["main_bearing_lb_in"] * base["main_length_in"] / (1 + math.sqrt(2))
    return {
        "signed_bound_known_answer": float(signed.x[0]),
        "infeasible_status": int(infeasible.status),
        "unbounded_status": int(unbounded.status),
        "wrong_unsigned_bounds_allow_zero_load_only": float(unsigned.x[-1]),
        "rejected_invalid_inputs": rejected,
        "loose_bending_cap_load_ratio": loose["scaled_statics_load_lbf"]
        / capped["scaled_statics_load_lbf"],
        "symmetric_rigid_dowel_exact_II_lbf": exact_II,
        "symmetric_32_cell_load_lbf": symmetric["scaled_statics_load_lbf"],
    }


def run(inputs):
    rows, details = [], {}
    for case in inputs["published_cases"] + inputs["synthetic_cases"]:
        k = case.get("k_theta", 1.0)
        rd = dict(zip(MODES, (4 * k, 4 * k, 3.6 * k, 3.2 * k, 3.2 * k, 3.2 * k)))
        analytic = single_shear(
            main_length_in=case["main_length_in"],
            side_length_in=case["side_length_in"],
            main_bearing_lb_in=case["main_bearing_lb_in"],
            side_bearing_lb_in=case["side_bearing_lb_in"],
            main_yield_moment_lb_in=case["yield_moment_lb_in"],
            side_yield_moment_lb_in=case["yield_moment_lb_in"],
            gap_in=case["gap_in"],
            reduction_terms=rd,
        )
        raw_mode = min(
            analytic["yield_values_lbf"], key=analytic["yield_values_lbf"].get
        )
        raw = analytic["yield_values_lbf"][raw_mode]
        if case.get("expected_raw_governing_mode", raw_mode) != raw_mode:
            raise RuntimeError("Synthetic case no longer selects its intended raw mode")
        published_error = None
        if "published_reference_values_lbf" in case:
            published_error = max(
                abs(value - expected)
                for value, expected in zip(
                    analytic["reference_values_lbf"].values(),
                    case["published_reference_values_lbf"],
                )
            )
            if published_error > 0.51:
                raise RuntimeError(
                    "Existing analytic helper differs from published rounding"
                )
        grids = []
        for cells in inputs["cells_per_member"]:
            result, field = solve(case, cells, inputs)
            result["relative_shortfall_from_raw_analytic"] = (
                1 - result["scaled_statics_load_lbf"] / raw
            )
            if result["relative_shortfall_from_raw_analytic"] < -1e-8:
                raise RuntimeError("Statics load exceeds analytic raw benchmark")
            if (
                grids
                and result["scaled_statics_load_lbf"]
                < grids[-1]["scaled_statics_load_lbf"] - 1e-6 * raw
            ):
                raise RuntimeError("Refined feasible field lost load unexpectedly")
            grids.append(result)
            details[f"{case['id']}/{cells}"] = field
        if (
            grids[-1]["relative_shortfall_from_raw_analytic"]
            > inputs["limits"]["maximum_final_relative_error"]
        ):
            raise RuntimeError(
                "Final synthetic grid misses required analytic agreement"
            )
        rows.append(
            {
                "id": case["id"],
                "raw_governing_mode": raw_mode,
                "analytic_raw_yield_lbf": raw,
                "published_reference_max_rounding_error_lbf": published_error,
                "analytic_all_raw_modes_lbf": analytic["yield_values_lbf"],
                "grids": grids,
            }
        )
    return {
        "schema": "synthetic_dowel_bearing_moment_limit_result/v1",
        "disposition": "verified_synthetic_known_answers_only",
        "candidate_inputs_used": False,
        "candidate_joint_capacity": None,
        "capacity_or_pass_claim": False,
        "source_pins": inputs["references"],
        "environment": environment(),
        "analyze_sha256": sha(__file__),
        "inputs_sha256": sha(PACKET / "inputs.json"),
        "solver_controls": controls(inputs),
        "cases": rows,
        "summary": {
            "case_count": len(rows),
            "LP_benchmark_count": len(details),
            "governing_modes_verified": sorted(
                {row["raw_governing_mode"] for row in rows}
            ),
            "maximum_128_cell_relative_shortfall": max(
                row["grids"][-1]["relative_shortfall_from_raw_analytic"] for row in rows
            ),
            "maximum_scaled_LP_certificate_residual": max(
                max(grid["scaled_LP_certificate"].values())
                for row in rows
                for grid in row["grids"]
            ),
        },
        "claim_limits": inputs["claim_limits"],
    }, details


def write(path, value):
    # Exclusive create also protects against accidentally reused result names.
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        parser.error(
            "--out must be a new directory; frozen output is never overwritten"
        )
    args.out.mkdir(parents=True, exist_ok=False)
    inputs = json.loads((PACKET / "inputs.json").read_text())
    check_pins(inputs)
    result, details = run(inputs)
    check_pins(inputs)
    write(args.out / "result.json", result)
    write(args.out / "details.json", details)
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
