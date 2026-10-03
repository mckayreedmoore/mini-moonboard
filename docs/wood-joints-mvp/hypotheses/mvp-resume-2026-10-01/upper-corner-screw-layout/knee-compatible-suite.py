"""Prepare the finite 24-state knee suite; parent runs 23 new states serially.

The accepted selected state is reused byte for byte. All mechanical assembly,
contact laws, gauge and physical recovery come from the frozen 8bfd4 producer.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-compatible-suite"
ORIGINAL_RAW = HERE / "rawlocal/knee-compatible"
CONTRACT = ORIGINAL_RAW / "prepare-attempt02/input-contract.json"
CACHED = ORIGINAL_RAW / "witness-attempt01/witness.json"
CORE = HERE / "knee-compatible.py"
SELECTED = ("a12-left", "knee_outer_left_side_1")
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"knee_outer_{side}_side_{number}" for side in ("left", "right") for number in (1, 2)]
FY_SENSITIVITIES_MPA = {"92ksi": 634.317671, "45ksi": 310.264078}
FROZEN = {
    "original_producer": (CORE, "8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413"),
    "input_contract": (CONTRACT, "f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f"),
    "preparation_receipt": (ORIGINAL_RAW / "prepare-attempt02/receipt.json", "25acba27d7e5586e4875121a04cd1b3f918f31acb92747101a37b4940b72ed7b"),
    "coupon": (ORIGINAL_RAW / "coupon-attempt01/coupon.json", "c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd"),
    "coupon_receipt": (ORIGINAL_RAW / "coupon-attempt01/receipt.json", "515f38a54c30b961f8c9edbd9de0f49f73b8e52f6bd5f4eee71de01778240482"),
    "selected_witness": (CACHED, "866817f4c62ab542b6c79e5912a01777c5322930aaf21a96ea4be7b9125ee246"),
    "selected_receipt": (ORIGINAL_RAW / "witness-attempt01/receipt.json", "7088673c7e3b1afa78e2a53438bff9e9f475444f1014a7fc018329156df2eb27"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label(path):
    return str(path.relative_to(ROOT))


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def constant(path, name):
    """Read an existing numeric reference without importing mechanical code."""
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return float(ast.literal_eval(node.value))
    raise ValueError(f"Missing frozen constant {name}: {path}")


def frozen_inputs():
    receipts = {}
    for name, (path, expected) in FROZEN.items():
        require(sha(path) == expected, f"Frozen original changed: {path}")
        receipts[name] = {"path": label(path), "sha256": expected, "bytes": path.stat().st_size}
    contract = read(CONTRACT)
    require(contract["schema"] == "knee_three_receiver_first_order_contract/v1", "Wrong original contract")
    require(contract["producer_sha256"] == FROZEN["original_producer"][1], "Wrong original producer binding")
    for name, receipt in contract["source_receipts"].items():
        path = ROOT / receipt["path"]
        require(sha(path) == receipt["sha256"], f"Frozen upstream source changed: {path}")
        receipts["upstream/" + name] = receipt
    for result_name, receipt_name in (("coupon", "coupon_receipt"), ("selected_witness", "selected_receipt")):
        result, receipt = read(FROZEN[result_name][0]), read(FROZEN[receipt_name][0])
        require(result["producer_sha256"] == receipt["producer_sha256"] == FROZEN["original_producer"][1], "Original result producer mismatch")
        require(result["input_contract_sha256"] == receipt["input_contract_sha256"] == FROZEN["input_contract"][1], "Original result contract mismatch")
        require(receipt["output_sha256"][FROZEN[result_name][0].name] == FROZEN[result_name][1], "Original result receipt mismatch")
    coupon, cached = read(FROZEN["coupon"][0]), read(CACHED)
    require(coupon["status"] == "matched", "Existing known-answer coupon did not match")
    require((cached["case_id"], cached["axis_id"]) == SELECTED and cached["coupon_sha256"] == FROZEN["coupon"][1], "Cached selected boundary mismatch")
    require(cached["status"] == "conditional_first_order_equilibrium" and cached["independent_reference_equilibrium_closed"], "Cached selected physical closure is not established")
    require(cached["scope"] == contract["model"], "Cached selected physics differs from the contract")
    state_ids = [(state["case_id"], state["axis_id"]) for state in contract["boundaries"]]
    require(state_ids == [(case, axis) for axis in AXES for case in CASES], "Expected exactly four shafts and six cases in frozen order")
    for state in contract["boundaries"]:
        geometry = contract["geometry"][state["axis_id"]]
        require(len(geometry["receivers"]) == len(state["operator_connector_wrenches_on_receivers"]) == 3, "Three-receiver boundary census changed")
        require(len(state["planes"]) == 2 and len(state["source_rows"]) == 5, "Two planes/one physical tie census changed")
    bearing = read(ROOT / contract["source_receipts"]["bearing"]["path"])
    references = {
        "smooth_beam_yield_sensitivities_mpa": FY_SENSITIVITIES_MPA,
        "nominal_minimum_bore_Fe_mpa": bearing["nominal_minimum_fe_mpa"],
        "wood_seat_Fc_perpendicular_mean_reference_mpa": constant(ROOT / contract["source_receipts"]["pure_helper"]["path"], "FC_PERP"),
        "scope": "Existing nominal/mean reference diagnostics and declared smooth-beam sensitivities. No adjusted joint resistance or actual hardware/wood acceptance.",
    }
    return contract, cached, receipts, references


def diagnostics(result, geometry, references):
    """Finite postprocessing of one state's recovered fields; never solve."""
    diameter = geometry["shaft_diameter_mm"]
    area, inertia = math.pi * diameter**2 / 4, math.pi * diameter**4 / 64
    tension = result["normal_transfer"]["single_physical_tie_n"]
    stress = []
    for field in result["beam_fields"]:
        bending = math.hypot(*field["EI_curvature_components_nmm"])
        shear = math.hypot(*field["EI_third_derivative_components_n"])
        normal = abs(tension / area) + bending * diameter / (2 * inertia)
        transverse = 4 * shear / (3 * area)
        proxy = math.hypot(normal, math.sqrt(3) * transverse)
        stress.append({
            "element": field["element"], "x_mm": field["x_mm"], "signed_single_tie_n": tension,
            "EI_curvature_components_nmm": field["EI_curvature_components_nmm"], "bending_resultant_nmm": bending,
            "EI_third_derivative_components_n": field["EI_third_derivative_components_n"], "shear_resultant_n": shear,
            "axial_plus_bending_envelope_mpa": normal, "round_section_shear_envelope_mpa": transverse,
            "nominal_smooth_von_mises_proxy_mpa": proxy,
            "over_declared_yield_sensitivity": {name: proxy / value for name, value in FY_SENSITIVITIES_MPA.items()},
        })
    bore, seats = [], []
    for receiver in geometry["receiver_order"]:
        fields = [field for field in result["bore_fields"] if field["receiver"] == receiver]
        peak = max(fields, key=lambda field: field["pressure_mpa"])
        bore.append({
            "receiver": receiver, "field_count": len(fields), "peak_pressure_mpa": peak["pressure_mpa"], "x_mm": peak["x_mm"],
            "nominal_Fe_reference_mpa": references["nominal_minimum_bore_Fe_mpa"],
            "peak_over_nominal_Fe_diagnostic": peak["pressure_mpa"] / references["nominal_minimum_bore_Fe_mpa"],
        })
    for end in result["outer_seat_fields"]:
        wood = end["series_contact"]["wood_contact"]
        mean, peak = wood["mean_pressure_full_annulus_mpa"], max(end["point_tractions"]["wood_contact"]["pressure_mpa"])
        reference = references["wood_seat_Fc_perpendicular_mean_reference_mpa"]
        seats.append({
            "end": end["end"], "receiver": end["receiver"], "positive_annular_peak_pressure_mpa": peak,
            "full_annulus_mean_pressure_mpa": mean, "Fc_perpendicular_mean_reference_mpa": reference,
            "peak_over_Fc_perpendicular_diagnostic": peak / reference, "mean_over_Fc_perpendicular_diagnostic": mean / reference,
            "peak_over_full_annulus_mean_diagnostic": peak / mean if mean else None,
            "head_center_closure_mm": end["series_contact"]["head_contact"]["closure_mm"],
            "wood_center_closure_mm": wood["closure_mm"], "total_center_closure_mm": end["series_contact"]["total_closure_mm"],
            "end_contact_moment_nmm": end["series_contact"]["moment_nmm"],
        })
    peak_stress = max(stress, key=lambda field: field["nominal_smooth_von_mises_proxy_mpa"])
    return {
        "case_id": result["case_id"], "axis_id": result["axis_id"], "beam_stress_fields": stress,
        "peak_same_state_same_position_smooth_proxy": peak_stress,
        "declared_sensitivity_exceeded": {name: peak_stress["nominal_smooth_von_mises_proxy_mpa"] > value for name, value in FY_SENSITIVITIES_MPA.items()},
        "bore_pressure_diagnostics": bore, "wood_seat_pressure_diagnostics": seats,
        "normal_transfer": result["normal_transfer"],
        "normal_center_position_note": "Negative reference outer opening is the rocking center position. Compression-only annular pressures remain nonnegative and the physical tie retains its prescribed positive tension. No center-pose bound is imposed.",
        "stress_scope": "The same source T and both bending/shear components at each reported beam position form the existing smooth-section envelope proxy. Peak bending and peak shear from different positions are not combined. Cross-section normal/shear envelopes are diagnostic, not an exact fiber-level VM field.",
        "static_endpoint_capacity_inherited": False, "pressure_ratios_are_joint_utilization": False,
        "actual_hardware_or_wood_acceptance": False,
    }


def prepare():
    contract, cached, receipts, references = frozen_inputs()
    states = []
    for index, state in enumerate(contract["boundaries"]):
        reused = (state["case_id"], state["axis_id"]) == SELECTED
        states.append({
            "index": index, "case_id": state["case_id"], "axis_id": state["axis_id"], "boundary_pointer": f"input_contract#/boundaries/{index}",
            "action": "reuse_accepted_witness" if reused else "one_frozen_API_call", "physical_axial_tie_n": state["physical_axial_tie_n"],
            "receiver_order": contract["geometry"][state["axis_id"]]["receiver_order"], "raw_source_rows": [row["raw_index"] for row in state["source_rows"]],
            "frozen_bearing_pointer": state["frozen_bearing_pointer"], "frozen_static_endpoint_pointers": state["frozen_static_endpoint_pointers"],
            "frozen_placement_witnesses": state["frozen_placement_witnesses"],
        })
    return {
        "schema": "knee_compatible_finite_suite_plan/v1", "status": "prepared_parent_execution_pending",
        "adapter_sha256": sha(Path(__file__)), "source_receipts": receipts, "states": states,
        "counts": {"physical_shafts": 4, "cases": 6, "total_states": 24, "cached_states_reused": 1, "new_mechanical_states": 23},
        "original_model": contract["model"], "diagnostic_references": references,
        "cached_selected_diagnostics": diagnostics(cached, contract["geometry"][SELECTED[1]], references),
        "cached_selected_physical_closure": cached["physical_recovery_max_residual"],
        "mechanics_executed_by_adapter": False, "physics_changed": False, "placement_recomputed": False,
        "scope": "Existing K requirement: all four shafts/six cases, with two signed lateral planes and one physical tie per shaft, recovered three-receiver bore/seat wrenches. Isolated force boundaries only; no shared-group/body-pose claim or new prerequisite.",
        "complete_joint_acceptance": False, "actual_hardware_or_wood_acceptance": False, "physical_release": False,
    }


def import_core():
    specification = importlib.util.spec_from_file_location("knee_compatible_frozen_8bfd4", CORE)
    core = importlib.util.module_from_spec(specification)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        specification.loader.exec_module(core)
    finally:
        sys.dont_write_bytecode = previous
    require((core.K_WOOD, core.E_BOLT, core.K_HEAD, core.ELEMENTS_PER_RECEIVER, core.GRADIENT_TOL) == (20.0, 200000.0, 10000.0, 8, 1e-6), "Frozen backend constants differ")
    return core


def summary_row(index, state, result, derived, source_path, source_sha, reused):
    return {
        "index": index, "case_id": state["case_id"], "axis_id": state["axis_id"], "reused_accepted_witness": reused,
        "result_path": label(source_path), "result_sha256": source_sha, "status": result["status"], "defect": result.get("defect"),
        "newton_converged": result.get("newton_converged", False), "independent_reference_equilibrium_closed": result.get("independent_reference_equilibrium_closed", False),
        "physical_recovery_max_residual": result.get("physical_recovery_max_residual"), "full_mixed_gradient_max_n": result.get("full_mixed_gradient_max_n"),
        "receivers": result.get("receivers", []), "single_physical_tie_n": state["physical_axial_tie_n"],
        "diagnostics": {key: value for key, value in derived.items() if key != "beam_stress_fields"} if derived else None,
    }


def run_suite(plan, plan_path, output):
    contract, cached, receipts, references = frozen_inputs()
    require(plan["schema"] == "knee_compatible_finite_suite_plan/v1" and plan["adapter_sha256"] == sha(Path(__file__)), "Wrong prepared adapter")
    require(plan["source_receipts"] == receipts and plan["original_model"] == contract["model"] and plan["diagnostic_references"] == references, "Prepared source/model references changed")
    expected_actions = [(state["case_id"], state["axis_id"]) for state in contract["boundaries"]]
    require([(item["case_id"], item["axis_id"]) for item in plan["states"]] == expected_actions, "Prepared state census changed")
    core = import_core()
    loaded, _, _ = core.load_contract(CONTRACT)
    require(loaded == contract, "Frozen API loaded a different contract")
    rows, outputs, attempted, completed = [], {}, 0, 0
    for index, state in enumerate(contract["boundaries"]):
        identity = (state["case_id"], state["axis_id"])
        geometry, reused = contract["geometry"][state["axis_id"]], identity == SELECTED
        if reused:
            result, source_path, source_sha = cached, CACHED, FROZEN["selected_witness"][1]
        else:
            attempted += 1
            try:
                # The backend accepts these full state/geometry arguments. Only its
                # return labels are fixed to SELECTED; correct those metadata here.
                result = core.run_witness(contract, state, geometry)
                result["backend_original_labels"] = {key: result[key] for key in ("case_id", "axis_id")}
                result["case_id"], result["axis_id"] = identity
                result["producer_sha256"] = FROZEN["original_producer"][1]
                result["input_contract_sha256"] = FROZEN["input_contract"][1]
                result["coupon_sha256"] = FROZEN["coupon"][1]
                result["suite_adapter_sha256"] = sha(Path(__file__))
                result["source_boundary_pointer"] = f"input_contract#/boundaries/{index}"
                require([receiver["receiver"] for receiver in result["receivers"]] == geometry["receiver_order"], "Backend receiver field ownership differs")
                require(result["normal_transfer"]["single_physical_tie_n"] == state["physical_axial_tie_n"], "Backend physical tie differs")
                completed += 1
            except (ValueError, ArithmeticError) as error:
                result = {"schema": "knee_suite_backend_defect/v1", "status": "STOP_backend_exception", "case_id": identity[0], "axis_id": identity[1], "defect": str(error), "source_boundary_pointer": f"input_contract#/boundaries/{index}", "mechanics_executed": True, "complete_joint_acceptance": False, "physical_release": False}
            source_path = output / f"state-{index:02d}.json"
            dump(source_path, result)
            source_sha = sha(source_path)
            outputs[source_path.name] = source_sha
        derived = diagnostics(result, geometry, references) if "beam_fields" in result else None
        diagnostic_path = output / f"diagnostics-{index:02d}.json"
        dump(diagnostic_path, {"source_result_path": label(source_path), "source_result_sha256": source_sha, "diagnostics": derived})
        outputs[diagnostic_path.name] = sha(diagnostic_path)
        rows.append(summary_row(index, state, result, derived, source_path, source_sha, reused))
        print(json.dumps({"index": index, "case_id": identity[0], "axis_id": identity[1], "reused": reused, "status": result["status"]}), flush=True)
    closed = sum(row["independent_reference_equilibrium_closed"] for row in rows)
    peak_rows = [row for row in rows if row["diagnostics"] is not None]
    peak = max(peak_rows, key=lambda row: row["diagnostics"]["peak_same_state_same_position_smooth_proxy"]["nominal_smooth_von_mises_proxy_mpa"])
    result = {
        "schema": "knee_compatible_finite_suite/v1", "status": "conditional_first_order_equilibrium_all24" if closed == 24 else "STOP_finite_suite_method_defects",
        "adapter_sha256": sha(Path(__file__)), "plan_sha256": sha(plan_path), "source_receipts": receipts, "states": rows,
        "counts": {"physical_shafts": 4, "cases": 6, "states_reported": len(rows), "cached_states_reused": 1, "new_states_attempted": attempted, "new_states_returned_fields": completed, "independent_reference_closure_states": closed},
        "peak_same_state_same_position_smooth_proxy": {"case_id": peak["case_id"], "axis_id": peak["axis_id"], **peak["diagnostics"]["peak_same_state_same_position_smooth_proxy"]},
        "diagnostic_references": references, "original_model": contract["model"], "output_sha256": outputs,
        "mechanics_executed_by_adapter": True, "physics_changed": False, "placement_recomputed": False,
        "scope": plan["scope"], "static_endpoint_capacity_inherited": False,
        "complete_joint_acceptance": False, "actual_hardware_or_wood_acceptance": False, "physical_release": False,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--out", type=Path, required=True, help="Fresh child below rawlocal/knee-compatible-suite")
    parser.add_argument("--input", type=Path, help="Prepared suite-plan.json for parent run mode")
    args = parser.parse_args()
    output = args.out.resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve(), "Output is outside assigned ownership")
    require(not output.exists(), "Output exists; preserve it and choose a fresh child")
    if args.mode == "prepare":
        result, name = prepare(), "suite-plan.json"
        output.mkdir(parents=True)
        (output / "executed-adapter.py").write_bytes(Path(__file__).read_bytes())
    else:
        require(args.input is not None and args.input.resolve().is_relative_to(RAW.resolve()), "Run requires the owned prepared plan")
        output.mkdir(parents=True)
        (output / "executed-adapter.py").write_bytes(Path(__file__).read_bytes())
        result, name = run_suite(read(args.input), args.input, output), "suite.json"
    dump(output / name, result)
    receipt = {
        "schema": "knee_compatible_suite_receipt/v1", "mode": args.mode, "status": result["status"],
        "adapter_sha256": sha(Path(__file__)), "original_producer_sha256": FROZEN["original_producer"][1],
        "source_receipts": result["source_receipts"], "argv": sys.argv, "python": sys.version.split()[0],
        "output_sha256": {name: sha(output / name), "executed-adapter.py": sha(output / "executed-adapter.py"), **result.get("output_sha256", {})},
        "mechanics_executed_by_adapter": args.mode == "run", "native_run": False, "frame_run": False, "CAD_run": False, "tests_run": False, "review_run": False,
    }
    if args.mode == "run":
        import numpy
        import scipy

        receipt.update(numpy=numpy.__version__, scipy=scipy.__version__, plan_sha256=sha(args.input))
    dump(output / "receipt.json", receipt)
    print(json.dumps({"status": result["status"], "result_path": label(output / name), "result_sha256": sha(output / name), "receipt_sha256": sha(output / "receipt.json"), "adapter_sha256": sha(Path(__file__)), "mechanics_executed_by_adapter": args.mode == "run"}, sort_keys=True))
    return 0 if not result["status"].startswith("STOP") else 2


if __name__ == "__main__":
    raise SystemExit(main())
