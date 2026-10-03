"""Run exactly 48 fresh top-side washer states with the existing fine method.

Import is inert. Parent-only build(output) binds the actual supported side
profile and own-end loads; only make_model and solve_state are solver calls.
No coupon, retry, profile sweep, CAD, shaft, frame or native solve is run.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/washer-top-side-fine-reference"
HELPER = HERE / "washer-end-source-completion.py"
HELPER_SHA = "dbf242d54ae501c0bf8d4241447837dcf08e7e4d2d108703f43a2fc0e1c078c9"
SOURCE = HERE / "rawlocal/washer-land-reference-completion/attempt01"
SOURCE_SHA = "0218731514788a808ea8cb313945fe1000cbf63b51c181c9415b366ab374a46a"
PROFILE = {"inner_radius_mm": 4.953, "outer_radius_mm": 11.0236,
           "head_radius_mm": 6.0, "thickness_mm": 1.6256}
SETTINGS = {"inside_elements": 4, "outside_elements": 12, "fourier_order": 8,
            "angles": 128, "unknowns": 1142}
FLAGS = {"proposal_adopted": False, "complete_joint_acceptance": False,
         "physical_release": False, "fabrication_release": False,
         "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
         "actual_washer_yield_mpa": None, "global_frame_feedback": False,
         "loaded_shift_or_tilt_qualified": False, "actual_hardware_inspected": False,
         "formal_criteria_updated": False, "coupon_or_retry_or_sweep_run": False,
         "CAD_or_shaft_or_frame_or_native_solve_run": False}


def load_helper():
    import hashlib
    if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
        raise ValueError("STOP: frozen source consumer changed")
    spec = importlib.util.spec_from_file_location("side_fine_saved_source_helper", HELPER)
    if spec is None or spec.loader is None:
        raise ValueError("STOP: frozen source consumer loader unavailable")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    return helper


def input_rows(helper, api, pins):
    _, receipt = helper.packet(pins, SOURCE, SOURCE_SHA, "washer-land-reference-completion",
                               "washer_land_reference_completion_receipt/v1")
    helper.require(receipt["status"] == "COMPLETE_MATCHED_TOP_SIDE_NOMINAL_REFERENCES"
                   and receipt["sources_authenticated_before_and_after"] is True
                   and receipt["counts"]["full_actual_profile_lands"] == 8
                   and receipt["counts"]["finite_actual_ring_probes"] == 48,
                   "actual supported top-side source packet differs")
    rows = [json.loads(line) for line in (SOURCE / "own-end-references.jsonl").read_text().splitlines()]
    result = helper.read(SOURCE / "washer-land-reference-completion.json")
    helper.require(result["matching_existing_plate_method"]["profile"] == PROFILE
                   and len(rows) == len({tuple(row["join_key"]) for row in rows}) == 48
                   and len({tuple(row["physical_land_key"]) for row in rows}) == 8
                   and {row["case_id"] for row in rows} == set(api.CASES),
                   "actual side family or six-case end census differs")
    sources = []
    for row in sorted(rows, key=lambda item: tuple(item["join_key"])):
        helper.require(row["actual_side_profile"] == PROFILE and "/side_" in row["axis_id"]
                       and row["axis_id"].startswith("top_outer/")
                       and row["nominal_support_status"] == "BOUND_FULL_ACTUAL_SIDE_ANNULUS"
                       and row["source_sha256"] == api.PINS[api.CORNER],
                       "state profile, current nominal land or fresh response differs")
        normal = helper.vector(row["normal_into_receiver_xyz"], 3)
        moment = helper.vector(row["own_end_M_signed_xyz_nmm"], 3)
        force = helper.vector(row["force_on_receiver_xyz_n"], 3)
        tension, magnitude = float(row["T_n"]), float(row["own_end_M_magnitude_nmm"])
        helper.require(tension > 0 and math.isfinite(tension) and magnitude >= 0
                       and math.isclose(math.hypot(*normal), 1, rel_tol=0, abs_tol=1e-8)
                       and helper.close_vector(force, [tension * x for x in normal], 1e-6)
                       and math.isclose(math.hypot(*moment), magnitude, rel_tol=0, abs_tol=1e-6)
                       and abs(api.dot(normal, moment)) <= 1e-6,
                       "fresh simultaneous signed force/moment convention differs")
        if magnitude > 0:
            local_x = [x / magnitude for x in api.cross(normal, moment)]
        else:
            basis = min(([1., 0., 0.], [0., 1., 0.], [0., 0., 1.]), key=lambda axis: abs(api.dot(axis, normal)))
            direction = api.cross(normal, basis)
            local_x = [x / math.hypot(*direction) for x in direction]
        local_y = api.cross(normal, local_x)
        helper.require(math.isclose(math.hypot(*local_x), 1, rel_tol=0, abs_tol=1e-8)
                       and helper.close_vector([magnitude * x for x in api.cross(local_x, normal)], moment, 1e-6),
                       "circular plate drive would lose the physical own-moment direction")
        sources.append({"state_id": "/".join(row["join_key"]), "join_key": row["join_key"],
                        "case_id": row["case_id"], "axis_id": row["axis_id"],
                        "end_role": row["end_role"], "receiver_member": row["receiver_member"],
                        "family": "side", "T_n": tension, "M_magnitude_nmm": magnitude,
                        "source_signed_own_M_xyz_nmm": moment, "force_on_receiver_xyz_n": force,
                        "normal_into_receiver_xyz": normal, "own_seat_xyz_mm": row["own_seat_xyz_mm"],
                        "local_pressure_offset_x_xyz": local_x, "local_y_xyz": local_y,
                        "plate_pressure_first_moment_targets_nmm": [magnitude, 0.],
                        "saved_rigid_contact": row["saved_rigid_contact"],
                        "rigid_contact_used_as_initialization_only": True,
                        "conditional_Fc_perp_reference_mpa": row["conditional_Fc_perp_reference_mpa"],
                        "source": row["source"], "source_sha256": row["source_sha256"],
                        "source_pointer": row["source_pointer"], "nominal_land_receipt_sha256": SOURCE_SHA})
    return sources


def build(output):
    """Parent-only one-model fine48 execution, preserving every numerical stop."""
    output = Path(output).absolute()
    helper = load_helper()
    helper.require(output.resolve() == output and output.parent == RAW and not output.exists(),
                   "use a fresh unaliased child of rawlocal/washer-top-side-fine-reference")
    api = helper.load_n09()
    pins = {**api.PINS, HELPER: HELPER_SHA, helper.N09: helper.N09_SHA,
            Path(__file__).resolve(): helper.sha(__file__)}
    sources = input_rows(helper, api, pins)
    helper.authenticate(pins)
    before = {api.display(path): helper.sha(path) for path in sorted(pins)}
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    plan = {"schema": "top_side_fine_washer_plan/v1", "profile": PROFILE, "resolution": SETTINGS,
            "source_receipt_sha256": SOURCE_SHA, "source_rows": sources,
            "solver_calls_allowed": ["make_model", "solve_state"], "planned_state_calls": 48, **FLAGS}
    (output / "input-plan.json").write_text(json.dumps(plan, indent=2, sort_keys=True, allow_nan=False) + "\n")
    edge, flexure, model, setup_failure, model_calls = None, None, None, None, 0
    try:
        flexure = api.load_module(api.FLEXURE, "side_fine_pinned_material_source")
        edge = api.load_module(api.EDGE, "side_fine_pinned_edge_method")
        helper.require(flexure.FAMILIES["side"] == PROFILE and edge.RESOLUTIONS["fine"] == SETTINGS
                       and (flexure.ESTEEL, flexure.NU, flexure.KWOOD, flexure.KHEAD, flexure.FY_HYPOTHESIS)
                           == (200000., 0.3, 20., 10000., 250.),
                       "fine family, resolution or constitutive hypotheses differ")
        # Reuse the helper's rail slot for the existing side family; no source file changes.
        flexure.FAMILIES = {**flexure.FAMILIES, "rail": dict(PROFILE)}
        model_calls += 1
        model = edge.make_model(flexure, "fine")
    except (ValueError, RuntimeError, OSError, ArithmeticError, ImportError) as error:
        setup_failure = {"error": str(error), "physical_incompatibility_proved": False}
    states, failures, state_calls = [], [], 0
    with (output / "end-states.jsonl").open("x") as stream:
        for source in sources:
            debug, state, failure, metrics = {}, None, setup_failure, None
            if model is not None and setup_failure is None:
                try:
                    edge.STATE_ID = source["state_id"]
                    state_calls += 1
                    state, fields = edge.solve_state(model, source, debug)
                    wood = max(fields, key=lambda row: row["wood_pressure_mpa"])
                    stress = state["sampled_stress_peak_witness"]
                    metrics = {"sampled_stress_proxy_mpa": stress["sampled_through_thickness_maximum_proxy_mpa"],
                               "stress_proxy_over_Fy250": stress["sampled_through_thickness_maximum_proxy_mpa"] / 250.,
                               "sampled_wood_pressure_peak_mpa": wood["wood_pressure_mpa"],
                               "sampled_wood_peak_over_base_reference": wood["wood_pressure_mpa"] / source["conditional_Fc_perp_reference_mpa"],
                               "wood_pressure_peak_witness": wood,
                               "scaled_gradient_maximum_n": state["scaled_gradient_maximum_n"]}
                    del fields
                    helper.require(all(math.isfinite(metrics[key]) for key in (
                        "sampled_stress_proxy_mpa", "stress_proxy_over_Fy250", "sampled_wood_pressure_peak_mpa",
                        "sampled_wood_peak_over_base_reference", "scaled_gradient_maximum_n")),
                        "nonfinite returned fine comparison")
                except (ValueError, RuntimeError, OSError, ArithmeticError) as error:
                    metrics = None
                    failure = {"error": str(error), "last_accepted_state": api.json_value(debug),
                               "physical_incompatibility_proved": False, "retry_performed": False}
            record = {"join_key": source["join_key"], "source": source,
                      "status": "FINITE_SIDE_WASHER_HYPOTHESIS" if failure is None else "NUMERICAL_STOP",
                      "state": api.json_value(state), "metrics": metrics, "failure": failure, **FLAGS}
            if failure is not None:
                failures.append({"join_key": source["join_key"], **failure})
            states.append(record)
            stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
            stream.flush()
    finite = [row for row in states if row["status"] == "FINITE_SIDE_WASHER_HYPOTHESIS"]
    exceedances = [row["join_key"] for row in finite if row["metrics"]["stress_proxy_over_Fy250"] > 1.]
    witnesses = {}
    for column in ("sampled_stress_proxy_mpa", "stress_proxy_over_Fy250", "sampled_wood_peak_over_base_reference"):
        row = max(finite, key=lambda item: item["metrics"][column]) if finite else None
        witnesses[column] = None if row is None else {"join_key": row["join_key"], "value": row["metrics"][column],
            "same_state_T_n": row["source"]["T_n"], "same_state_M_nmm": row["source"]["M_magnitude_nmm"]}
    helper.authenticate(pins)
    after = {api.display(path): helper.sha(path) for path in sorted(pins)}
    helper.require(before == after, "source bytes changed during fine48 run")
    status = "FINITE_SIDE_WASHER_REFERENCES" if len(finite) == 48 else "PARTIAL_SIDE_WASHER_REFERENCES_WITH_NUMERICAL_STOPS"
    if len(finite) == 48 and exceedances:
        status = "FINITE_SIDE_WASHER_REFERENCES_WITH_HYPOTHETICAL_YIELD_EXCEEDANCES"
    result = {"schema": "top_side_fine_washer_reference/v1", "status": status,
              "counts": {"source_end_states": 48, "physical_nominal_lands": 8,
                         "completed_end_states": len(finite), "numerical_stops": len(failures),
                         "model_calls": model_calls, "state_calls": state_calls,
                         "sampled_Fy250_exceedances": len(exceedances)},
              "model": {"profile": PROFILE, "resolution": SETTINGS,
                        "E_mpa_hypothesis": 200000., "nu_hypothesis": 0.3, "Fy_mpa_comparator": 250.,
                        "Kwood_mpa_per_mm_hypothesis": 20., "Khead_mpa_per_mm_hypothesis": 10000.,
                        "profile_slot": "Existing side family supplied in the helper's rail slot.",
                        "maximum_Newton_steps": 100, "maximum_Armijo_backtracks": 50,
                        "primary_energy_source": flexure.ENERGY_SOURCE if flexure else None},
              "same_state_peak_witnesses": witnesses, "sampled_yield_exceedance_keys": exceedances,
              "setup_failure": setup_failure, "numerical_failures": failures,
              "source_receipt_sha256": SOURCE_SHA, "source_before_sha256": before,
              "source_after_sha256": after, "sources_authenticated_before_and_after": True,
              "runtime": {"python": sys.version, "numpy": edge.np.__version__ if edge else None,
                          "scipy": edge.scipy.__version__ if edge else None},
              "limits": ["Fresh same-state force and own moment are prescribed; flexure is not fed back into shaft/group/frame equilibrium.",
                         "The actual nominal ring is supported; loaded movement and changed contact support remain unqualified.",
                         "Circular head/nut profiles, thickness, steel properties and seat stiffness remain declared hypotheses.",
                         "Sampled face bending/midplane shear proxy excludes contact sigmaZZ, three-dimensional edges, plasticity, preload and friction.",
                         "The fine weak free-edge approximation is reused without a new convergence sweep or physical capacity qualification.",
                         "The wood comparator is the existing conditional base reference, not full adjusted timber/joint resistance.",
                         "Numerical stops remain method limits; no retries, added stiffness or physical failure inference.",
                         "All formal criteria and joint/release HOLD boundaries remain unchanged."], **FLAGS}
    (output / "washer-top-side-fine-reference.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    artifacts = {path.name: helper.sha(path) for path in sorted(output.iterdir()) if path.is_file()}
    (output / "receipt.json").write_text(json.dumps({"schema": "top_side_fine_washer_reference_receipt/v1",
        "status": status, "source_sha256": before, "source_before_sha256": before, "source_after_sha256": after,
        "sources_authenticated_before_and_after": True, "output_sha256": artifacts,
        "counts": result["counts"], **FLAGS}, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "same_state_peak_witnesses": result["same_state_peak_witnesses"]}, indent=2))
