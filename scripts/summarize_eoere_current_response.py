"""Authenticate six saved current cases and publish a compact force summary.

This reuses the saved-field admission consumer. It does not query CAD, prepare
operators, rerun equilibrium or establish physical resistance/applicability.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
from pathlib import Path

from scripts import eoere_current_response as current

OWN = Path(__file__).resolve()
LOADED_SHA = current.sha(OWN)
SEQUENCE = ["a12-forward", "a12-rear", "a12-left", "k12-right", "k12-rear", "a1-rear"]


def own_ref():
    current.require(current.sha(OWN) == LOADED_SHA, "loaded summary producer changed")
    return {"path": str(OWN.relative_to(current.ROOT)), "sha256": LOADED_SHA}


def canonical_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def process_record(directory, name):
    pointer = current.ref(directory / name)
    record = current.read(pointer)
    pins = current.join(record["pins_before"], {pointer["path"]: pointer["sha256"]},
                        {r["path"]: r["sha256"] for r in record["logs"].values()})
    current.verify(pins)
    return record, pins, pointer


def verify_process_pair(producer, admission, *, case_id, producer_command, refs,
                        execution_ref, field_ref, admission_ref, previous_end=None):
    expected_admission = [producer_command[0], "-B", refs["adapter"]["path"], "--mode", "admit",
                          "--field", str(current.ROOT / field_ref["path"]),
                          "--out", str(current.ROOT / admission_ref["path"])]
    required_pins = {r["path"]: r["sha256"] for r in [*refs.values(), execution_ref]}
    for mode, record, command in [("run", producer, producer_command), ("admit", admission, expected_admission)]:
        environment = {"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
        if mode == "run":
            environment["EOERE_PARENT_SERIALIZED_FORCE_RUN"] = "1"
        current.require(record["schema"] == "eoere_serial_current_"+mode+"_process_capture/v1"
                        and record["case_id"] == case_id and record["command"] == command
                        and record["cwd"] == str(current.ROOT) and record["controlled_environment"] == environment,
                        "own serial process command/schema/context differs")
        current.require(record["status"] == "FINISHED" and record["exit_code"] == 0
                        and record["pins_unchanged"] is True
                        and record["pins_before"] == record["pins_after"]
                        and all(record["pins_before"].get(p) == h for p, h in required_pins.items())
                        and record["historical_state_or_actions_used"] is False,
                        "successful unchanged serial process capture required")
    start = datetime.datetime.fromisoformat(producer["started_at_utc"])
    run_end = datetime.datetime.fromisoformat(producer["finished_at_utc"])
    audit_start = datetime.datetime.fromisoformat(admission["started_at_utc"])
    audit_end = datetime.datetime.fromisoformat(admission["finished_at_utc"])
    current.require(start <= run_end <= audit_start <= audit_end
                    and (previous_end is None or previous_end <= start), "parent cases must run and admit serially")
    return audit_end


def summarize(execution_ref):
    config = current.read(execution_ref)
    current.require(config["schema"] == "eoere_selected_hardware_parent_execution_inputs/v1"
                    and config["case_sequence"] == SEQUENCE
                    and config["release"] == current.manifest()["release"], "exact six-case execution contract required")
    refs = config["references"]
    current.require(refs["adapter"] == current.ref(current.OWN), "exact current force producer required")
    input_data = current.read(refs["inputs"])
    current.require_current_sources(input_data)
    input_review = current.read(refs["input_review"])
    checker_ref = current.ref(current.ROOT / "scripts/check_eoere_current_inputs.py")
    current.require(input_review["source_sha256"][checker_ref["path"]] == checker_ref["sha256"],
                    "exact loaded input checker source required")
    preflight_ref = current.ref(current.RAW / "preflight-v2.json")
    preflight = current.read(preflight_ref)
    current.require(preflight["missing"] == []
                    and preflight["provided"]["inputs"] == refs["inputs"]
                    and preflight["provided"]["input_review"] == refs["input_review"]
                    and preflight["provided"]["method_input"] == refs["method_input"], "complete matching preflight required")
    pins = current.join({r["path"]: r["sha256"] for r in [execution_ref, preflight_ref, own_ref()]},
                        {r["path"]: r["sha256"] for r in refs.values()})
    cases, previous_end = [], None
    with current.response_context() as (bridge, _):
        method = bridge.read_method(current.ROOT / refs["method_input"]["path"], refs["method_input"]["sha256"])
        current.require(method["input"] == refs["inputs"] and method["input_review"] == refs["input_review"],
                        "summary input/review differ from actual method")
        for case_id in SEQUENCE:
            directory = current.RAW / "cases-v1" / case_id / "attempt01"
            field_ref, admission_ref = current.ref(directory / "field.json"), current.ref(directory / "admission.json")
            receipt = current.read(admission_ref)
            field, admitted_pins = bridge.require_admitted_payload(
                (directory / "field.json").read_bytes(), receipt, admission_sha256=current.LOADED_SHA)
            current.require(field["case_id"] == receipt["case_id"] == case_id
                            and field["current_method_input"] == refs["method_input"]
                            and field["current_execution"]["geometry"] == current.manifest()["references"]["geometry"]
                            and receipt[current.SUCCESS] is True and field["response"]["converged"] is True
                            and field["release"] == receipt["release"] == config["release"],
                            "matching current admitted case with all releases false required")
            execution = field["current_execution"]
            current.require(execution["input_path"] == refs["inputs"]["path"]
                            and execution["input_sha256"] == refs["inputs"]["sha256"]
                            and execution["input_review_path"] == refs["input_review"]["path"]
                            and execution["input_review_sha256"] == refs["input_review"]["sha256"]
                            and execution["slot_at_start"]["sha256"] == refs["slot"]["sha256"]
                            and execution["historical_q_or_forces_used"] is False,
                            "exact execution input/review/slot and fresh state required")
            producer, producer_pins, producer_ref = process_record(directory, "process.json")
            admission, admission_pins, admission_process_ref = process_record(directory, "admission-process.json")
            previous_end = verify_process_pair(producer, admission, case_id=case_id,
                producer_command=execution["command"], refs=refs, execution_ref=execution_ref,
                field_ref=field_ref, admission_ref=admission_ref, previous_end=previous_end)
            current.require(receipt["declared_law_checks"]["gradient_inf_n"] <= 1e-5
                            and receipt["no_candidate_preparation_or_solve_in_admission"] is True,
                            "unchanged residual gate and saved-only audit required")
            peak = max(field["panel_screw_actions"], key=lambda row: row["withdrawal_n"])
            spacer_axes = {s["axis_id"] for s in field["source_inputs"]["shafts"]
                           if any(r["kind"] == "spacer" for r in s["metal_roles"])}
            spacer_actions = [{"axis_id": r["axis_id"], "compression_n": r["compression_n"]}
                              for r in field["shaft_end_capture_actions"]
                              if r["axis_id"] in spacer_axes and r["end"]["end"] == "nut"]
            current.require(len(spacer_axes) == len(spacer_actions) == 8, "eight own spacer nut captures required")
            row = {"case_id": case_id, "field": field_ref, "admission": admission_ref,
                   "operator_bundle": field["operator_bundle"],
                   "producer_process": producer_ref, "admission_process": admission_process_ref,
                   "producer_elapsed_seconds": producer["elapsed_seconds"],
                   "admission_elapsed_seconds": admission["elapsed_seconds"],
                   "state_id": field["state_id"], "counts": field["counts"],
                   "gradient_inf_n": receipt["declared_law_checks"]["gradient_inf_n"],
                   "applied_load_checks": receipt["applied_load_checks"],
                   "equilibrium_verification": field["equilibrium_verification"],
                   "global_residual_n_nmm": receipt["declared_law_checks"]["global_residual_n_nmm"],
                   "normal_force_n_by_host": receipt["normal_force_n_by_host"],
                   "horizontal_force_xyz_n_by_host": receipt["horizontal_force_xyz_n_by_host"],
                   "reaction_ratio_required_not_measured_friction": receipt["reaction_ratio_required_not_measured_friction"],
                   "floor_support_summary": field["floor_support_summary"],
                   "motion_diagnostics": receipt["motion_diagnostics"],
                   "peak_panel_screw_withdrawal": {"axis_id": peak["axis_id"], "withdrawal_n": peak["withdrawal_n"]},
                   "spacer_nut_capture_actions": spacer_actions,
                   "loaded_recovery_checks": receipt["loaded_recovery_checks"],
                   "owned_port_checks": receipt["owned_port_checks"],
                   "current_equilibrium_and_recovery_pass": True,
                   "physical_demand_bounds_established": receipt["physical_demand_bounds_established"],
                   "first_order_physical_applicability_established": receipt["first_order_physical_applicability_established"]}
            cases.append(row)
            pins = current.join(pins, admitted_pins, producer_pins, admission_pins,
                                {r["path"]: r["sha256"] for r in [field_ref, admission_ref]})
    current.require(len({r["state_id"] for r in cases}) == 6, "six own states required")
    current.verify(pins)
    own_ref()
    source_map = current.RAW / "summary-source-map-v1.json"
    current.write(source_map, pins)
    return {"schema": "eoere_selected_hardware_six_case_response/v1",
            "status": "CURRENT_CONDITIONAL_FIRST_ORDER_CASES_ADMITTED",
            "candidate": current.manifest()["candidate"],
            "geometry_revision": current.manifest()["geometry_revision"],
            "hardware_revision": current.manifest()["hardware_revision"],
            "geometry": current.manifest()["references"]["geometry"],
            "hardware_model": current.manifest()["references"]["hardware"],
            "source_manifest": current.ref(current.MANIFEST), "summary_producer": own_ref(),
            "force_producer": refs["adapter"], "input_checker": checker_ref,
            "execution_inputs": execution_ref, "input": refs["inputs"], "input_review": refs["input_review"],
            "method_input": refs["method_input"], "preflight": preflight_ref,
            "extra_grid": False, "case_sequence": SEQUENCE, "cases": cases,
            "maximum_full_gradient_residual_n": max(r["gradient_inf_n"] for r in cases),
            "maximum_owned_interaction_motion_mm": max(r["motion_diagnostics"]["maximum_owned_interaction_point_linear_displacement_norm_mm"] for r in cases),
            "maximum_relative_timber_or_fitting_rotation_rad": max(r["motion_diagnostics"]["maximum_relative_timber_or_fitting_strip_rotation_norm_rad"] for r in cases),
            "modeled_gravity": input_data["gravity"],
            "all_six_saved_field_admissions_pass": True,
            "source_union": {"count": len(pins), "canonical_sha256": canonical_sha(pins), "record": current.ref(source_map)},
            "conditional_first_order_solve_performed": True, "native_solve_performed": False,
            "historical_q_forces_or_passes_transferred": False, "remedies_attempted": False,
            "actual_build_fit_work_performed": False, "structural_acceptance": False,
            "physical_demand_bounds_established": False, "complete_joint_resistance": None,
            "finished_member_capacity": None, "release": current.manifest()["release"],
            "limits": ["Gross-stock timber stiffness; finished-section resistance and stability are not established.",
                       "Generic Hillman stiffness and nominal flat Eoere fitting priors; product/complete-joint resistance unknown.",
                       "Spacer axial capture/gravity included, without spacer compliance, seating or washer resistance qualification.",
                       "Unverified no-slip floor; fixed two rear-leg centroid XY penalties and 32 compression-only normal points.",
                       "First-order motions are diagnostics; physical demand bounds and support/panel applicability remain open.",
                       "Distributed panel RHS is authenticated producer capture, not an independently regenerated load distribution.",
                       "All earlier exceedances remain recorded for their exact prior inputs; no remedies are attempted."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execution-inputs", type=Path, required=True)
    parser.add_argument("--execution-inputs-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    source = {"path": str(args.execution_inputs.resolve().relative_to(current.ROOT)), "sha256": args.execution_inputs_sha256}
    current.require(args.out.parent.resolve().is_relative_to(current.ROOT), "repository summary output required")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fixed = current.load("bridge")
    with fixed.reserve(args.out) as output:
        output.write(summarize(source))
    print(json.dumps(current.ref(args.out)))


if __name__ == "__main__":
    main()
