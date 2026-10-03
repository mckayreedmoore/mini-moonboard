"""Enter unloaded bore clearance explicitly in the frozen first-order knee model.

Only the numerical step changes. Accepted suite states remain byte-exact;
the 14 states stopped by the original iteration limit get one new evaluation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-contact-entry"
SUITE = HERE / "rawlocal/knee-compatible-suite/suite-attempt01/suite.json"
ADAPTER = HERE / "knee-compatible-suite.py"
PINS = {
    SUITE: "0d7dff18b38d82130be212b1fc53fbb18a97c0e6f0c3a8c4a13e58fa3375910f",
    ADAPTER: "9798402070802a1804f4c9797fea336cda66951179340c1255e7122315990304",
    HERE / "rawlocal/knee-compatible-suite/suite-attempt01/receipt.json":
        "3180d95e9b7f146da7bc2dce40ec3d88c10b6152e3da9f06b70e11a9226187f1",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def adapter():
    for path, expected in PINS.items():
        require(sha(path) == expected, f"Frozen source changed: {path}")
    specification = importlib.util.spec_from_file_location("frozen_knee_suite", ADAPTER)
    value = importlib.util.module_from_spec(specification)
    sys.dont_write_bytecode = True
    specification.loader.exec_module(value)
    return value


def entry_step(pose, direction, samples):
    """First forward intersection with an inactive circular bore, then cross it.

    This is an exact ray/sphere intersection in the original kinematics.
    Crossing by at least 1e-6 mm is a step-selection scale, not a law or gap.
    Armijo still checks the unchanged full potential before accepting it.
    """
    events = []
    for sample in samples:
        relative, velocity = sample["map"] @ pose, sample["map"] @ direction
        radius, gap = float(np.linalg.norm(relative)), sample["gap_mm"]
        speed_squared = float(velocity @ velocity)
        if radius > gap or speed_squared <= 1e-28:
            continue
        linear = float(relative @ velocity)
        constant = float(relative @ relative) - gap**2
        discriminant = max(0.0, linear**2 - speed_squared * constant)
        distance = (-linear + math.sqrt(discriminant)) / speed_squared
        if distance >= 0 and math.isfinite(distance):
            crossing = distance + max(1e-4 * distance, 1e-6 / math.sqrt(speed_squared))
            events.append((crossing, distance))
    require(events, "Loaded neutral direction has no forward unused bore support")
    return min(events)


def solve(evaluate, model, tolerance):
    pose, free = np.zeros(model["size"]), model["free"]
    history, defect, converged = [], None, False
    for iteration in range(150):
        energy, gradient, hessian = evaluate(pose)[:3]
        mixed = float(np.max(np.abs(gradient[free])))
        row = {"iteration": iteration, "energy_nmm": energy,
               "max_free_mixed_gradient_n": mixed}
        history.append(row)
        if mixed <= tolerance:
            converged = True
            break
        values, vectors = np.linalg.eigh(hessian[np.ix_(free, free)])
        if values[0] < -1e-9 * max(1, values[-1]):
            defect = "Newton tangent is not numerically positive semidefinite"
            break
        positive = values > max(1, values[-1]) * 1e-12
        projected = vectors.T @ gradient[free]
        null_gradient = vectors[:, ~positive] @ projected[~positive]
        row["loaded_neutral_gradient_max_n"] = float(np.max(np.abs(null_gradient)))
        direction = np.zeros(model["size"])
        if row["loaded_neutral_gradient_max_n"] > max(1e-8, mixed * 1e-9):
            direction[free] = -null_gradient
            try:
                fraction, first_contact = entry_step(pose, direction, model["samples"])
            except ValueError as error:
                defect = str(error)
                break
            direction *= fraction
            row.update(step_kind="forward_bore_contact_entry",
                       forward_ray_first_contact=first_contact,
                       forward_ray_crossing=fraction)
        else:
            direction[free] = -vectors[:, positive] @ (projected[positive] / values[positive])
            row["step_kind"] = "positive_tangent_Newton"
        slope = float(gradient @ direction)
        if slope >= 0:
            defect = "Numerical step does not descend"
            break
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose + fraction * direction
            if evaluate(candidate)[0] <= energy + 1e-4 * fraction * slope + 1e-12 * max(1, abs(energy)):
                pose = candidate
                row["accepted_fraction"] = fraction
                break
        else:
            defect = "Armijo search stopped without a valid step"
            break
    if not converged and defect is None:
        defect = "Local iteration budget exhausted; compatibility has not been established"
    return pose, history, defect, converged


def coupon():
    """Two-component known answer for a loaded circular clearance foundation."""
    records = []
    stiffness, gap = 13.0, 0.575
    model = {"size": 2, "free": np.arange(2),
             "samples": [{"map": np.eye(2), "gap_mm": gap}]}
    for force in (np.array([2.0, -3.0]), np.array([-0.2, 0.1]), np.zeros(2)):
        def evaluate(pose, force=force):
            radius = float(np.linalg.norm(pose))
            excess = max(radius - gap, 0)
            unit = pose / radius if radius else np.zeros(2)
            hessian = np.zeros((2, 2))
            if excess:
                hessian = stiffness * ((1 - gap / radius) * np.eye(2)
                                       + gap / radius * np.outer(unit, unit))
            return (float(0.5 * stiffness * excess**2 - force @ pose),
                    stiffness * excess * unit - force, hessian)
        pose, history, defect, converged = solve(evaluate, model, 1e-10)
        norm = float(np.linalg.norm(force))
        exact = (gap + norm / stiffness) * force / norm if norm else np.zeros(2)
        error = float(np.max(np.abs(pose - exact)))
        records.append({"force_n": force.tolist(), "expected_pose_mm": exact.tolist(),
                        "returned_pose_mm": pose.tolist(), "max_abs_error_mm": error,
                        "history": history, "defect": defect,
                        "matched": converged and error <= 1e-9})
    return {"schema": "knee_contact_entry_known_answer/v1",
            "status": "matched" if all(r["matched"] for r in records) else "STOP_coupon_mismatch",
            "circular_gap_mm": gap, "stiffness_n_per_mm": stiffness,
            "records": records, "software_tests_run": False,
            "physical_release": False, "producer_sha256": sha(Path(__file__))}


def run_one(core, contract, state, geometry):
    helper = core.pure_helper(geometry["modeled_wood_grip_mm"])
    model = core.assemble(geometry, helper)
    tension = state["physical_axial_tie_n"]
    quadratures, drive = core.quads(helper, contract), core.drive_for(state, geometry, model)

    def evaluate(pose):
        return core.evaluate(pose, model, helper, tension, quadratures, drive)

    pose, history, defect, converged = solve(evaluate, model, core.GRADIENT_TOL)
    evaluation = evaluate(pose)
    recovered = core.physical_recovery(pose, evaluation, model, helper, contract, state, geometry)
    residual = recovered["physical_recovery_max_residual"]
    all_gradient = float(np.max(np.abs(evaluation[1])))
    closed = (converged and residual["force_n"] <= core.GRADIENT_TOL
              and residual["moment_nmm"] <= model["length"] * core.GRADIENT_TOL
              and all_gradient <= core.GRADIENT_TOL)
    if converged and not closed:
        defect = "Independent reference-geometry recovery does not close all three receiver wrenches"
    return {"schema": "knee_three_receiver_first_order_witness/v1",
            "status": "conditional_first_order_equilibrium" if closed else "STOP_method_or_boundary_defect",
            "case_id": state["case_id"], "axis_id": state["axis_id"], "defect": defect,
            "newton_converged": converged, "independent_reference_equilibrium_closed": closed,
            "full_mixed_gradient_max_n": all_gradient, "accepted_iterate": pose.tolist(),
            "iteration_history": history, **recovered, "scope": contract["model"],
            "physics_changed": False, "mechanics_executed": True,
            "force_ready_for_whole_knee_group": False, "complete_joint_acceptance": False,
            "actual_hardware_or_wood_acceptance": False, "physical_release": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("coupon", "run"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--coupon", type=Path)
    args = parser.parse_args()
    output = args.out.resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve(), "Outside owned output folder")
    require(not output.exists(), "Preserve previous output; choose a fresh child")
    owner = adapter()
    contract, _, sources, references = owner.frozen_inputs()
    output.mkdir(parents=True)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    generated = {}
    if args.mode == "coupon":
        result, name = coupon(), "coupon.json"
    else:
        require(args.coupon is not None and args.coupon.resolve().is_relative_to(RAW.resolve()), "Owned matched coupon required")
        checked = read(args.coupon)
        require(checked["status"] == "matched" and checked["producer_sha256"] == sha(Path(__file__)), "Unmatched coupon/producer")
        previous = read(SUITE)
        core, rows = owner.import_core(), []
        for old, boundary in zip(previous["states"], contract["boundaries"], strict=True):
            index = old["index"]
            geometry = contract["geometry"][boundary["axis_id"]]
            reuse = old["independent_reference_equilibrium_closed"]
            if reuse:
                path, digest = ROOT / old["result_path"], old["result_sha256"]
                require(sha(path) == digest, "Accepted result changed")
                state_result = read(path)
            else:
                state_result = run_one(core, contract, boundary, geometry)
                path = output / f"state-{index:02d}.json"
                dump(path, state_result)
                digest = sha(path)
                generated[path.name] = digest
            derived = owner.diagnostics(state_result, geometry, references)
            row = owner.summary_row(index, boundary, state_result, derived, path, digest, reuse)
            rows.append(row)
            print(json.dumps({"index": index, "case_id": row["case_id"],
                              "axis_id": row["axis_id"], "reused": reuse,
                              "status": row["status"]}), flush=True)
        accepted = [r for r in rows if r["independent_reference_equilibrium_closed"]]
        peak = max(accepted, key=lambda r: r["diagnostics"]["peak_same_state_same_position_smooth_proxy"]["nominal_smooth_von_mises_proxy_mpa"])
        result, name = {
            "schema": "knee_contact_entry_finite_suite/v1",
            "status": "conditional_first_order_equilibrium_all24" if len(accepted) == 24 else "STOP_finite_suite_method_defects",
            "states": rows,
            "counts": {"physical_shafts": 4, "cases": 6, "states_reported": 24,
                       "accepted_old_states_reused": sum(r["reused_accepted_witness"] for r in rows),
                       "new_contact_entry_states": 14, "independent_reference_closure_states": len(accepted)},
            "peak_accepted_same_state_same_position_smooth_proxy": {
                "case_id": peak["case_id"], "axis_id": peak["axis_id"],
                **peak["diagnostics"]["peak_same_state_same_position_smooth_proxy"]},
            "original_model": contract["model"], "diagnostic_references": references,
            "producer_sha256": sha(Path(__file__)), "coupon_sha256": sha(args.coupon),
            "physics_changed": False, "complete_joint_acceptance": False,
            "actual_hardware_or_wood_acceptance": False, "physical_release": False,
        }, "suite.json"
    dump(output / name, result)
    generated.update({name: sha(output / name), "producer.py.snapshot": sha(output / "producer.py.snapshot")})
    receipt = {"mode": args.mode, "status": result["status"],
               "producer_sha256": sha(Path(__file__)), "source_receipts": sources,
               "source_sha256": {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
               "output_sha256": generated, "argv": sys.argv,
               "mechanics_executed": args.mode == "run", "tests_run": False,
               "native_run": False, "CAD_run": False, "frame_run": False}
    dump(output / "receipt.json", receipt)
    print(json.dumps({"status": result["status"], "result_sha256": sha(output / name),
                      "receipt_sha256": sha(output / "receipt.json")}))
    return 0 if not result["status"].startswith("STOP") else 2


if __name__ == "__main__":
    raise SystemExit(main())
