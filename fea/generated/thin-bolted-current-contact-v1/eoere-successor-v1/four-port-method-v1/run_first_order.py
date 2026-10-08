"""Parent-only fresh A12 execution entrypoint; no implicit run or old q reader.

Method readiness, final reviewed source inputs and a distinct independent field
gate are required outside this driver. Convergence exports a pending candidate,
never a structural or fabrication PASS. All writes preserve existing outputs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import signal
import sys
import time
from pathlib import Path

import numpy as np

from scripts import thin_bolted_support_state_search as search

OWN = Path(__file__).resolve()
FACTORY = OWN.with_name("first_order_factory.py")
SPEC = importlib.util.spec_from_file_location("eoere_first_order_execution_factory", FACTORY)
factory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory)
frame = factory.frame
LOADED_SHA = frame.sha(OWN)
LOADED_FACTORY_SHA = frame.sha(FACTORY)
SEARCH_SHA = "c162d296306a263be4e6769c4249abf6491512e8f7d9af323ab2e9b10b1018e8"
SAVED_PANEL_PATH = "scripts/run_thin_bolted_finite_frame.py"
SAVED_PANEL_SHA = "5cf423d80e57b6f4386eb6c7aae39961ba083a7b4a457c7d37694cb80101361e"
RELEASE = {"candidate_accepted": False, "complete_joint_acceptance": False, "capacity_established": False,
           "fabrication_released": False, "structural_released": False, "climbing_released": False}


class CaseWallTimeLimit(Exception):
    pass


def serial(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: serial(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serial(item) for item in value]
    return value


def descriptor(row):
    return serial({key: value for key, value in row.items() if key != "B"})


def operator_fingerprint(prepared):
    def sparse(matrix):
        matrix = matrix.tocsr()
        return {"shape": matrix.shape, "data": hashlib.sha256(matrix.data.tobytes()).hexdigest(),
                "indices": hashlib.sha256(matrix.indices.tobytes()).hexdigest(),
                "indptr": hashlib.sha256(matrix.indptr.tobytes()).hexdigest()}

    return factory.canonical({"K": sparse(prepared.assembly.K),
        "applied": hashlib.sha256(prepared.applied.tobytes()).hexdigest(),
        "rows": [{"descriptor": descriptor(row), "B": sparse(row["B"])}
                 for row in [*prepared.groups, *prepared.contacts, *prepared.tangents]],
        "case": prepared.case, "body_descriptors": prepared.assembly.geo["bodies"],
        "fitting_descriptors": [el.descriptor() for el in prepared.fittings.values()]})


def runtime_pins(extra=None):
    pins = factory.source_pins(search.source_pins())
    for path, digest in (extra or {}).items():
        factory.require(path not in pins or pins[path] == digest, "runner source join conflict")
        pins[path] = digest
    pins = factory.source_pins(pins)
    for path, digest in ((OWN, LOADED_SHA), (FACTORY, LOADED_FACTORY_SHA),
                         (frame.ROOT/"scripts/thin_bolted_support_state_search.py", SEARCH_SHA),
                         (frame.ROOT/SAVED_PANEL_PATH, SAVED_PANEL_SHA)):
        factory.require(frame.sha(path) == digest, "loaded runner/factory/search source changed")
        pins[str(path.relative_to(frame.ROOT))] = digest
    return pins


def write_exclusive(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(serial(payload), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def recover(prepared, response):
    """Reuse common-shaft recovery, keep disabled floor rows and loaded roots."""
    factory.require(response.get("converged") is True and "q" in response,
                    "failed branches supply no accepted actions")
    recovered = prepared.system.compatible_actions(prepared.case, response,
        prepared.groups, prepared.contacts, prepared.tangents)
    floor = {row["id"]: row for row in recovered["floor_actions"]}
    disabled = set(response["nonbearing_no_slip_removed"])
    for row in prepared.tangents:
        enabled = row["first"] not in disabled
        if not enabled:
            floor[row["id"]] = {**descriptor(row), "second": "floor", "force_on_first_xyz_n": [0., 0., 0.],
                "tangent_displacement_mm": float((row["B"] @ response["q"])[0]), "energy_nmm": 0.,
                "case_id": prepared.case["case_id"], "accessory_placement": prepared.case["accessory_placement"]}
        floor[row["id"]]["interaction_enabled"] = enabled
        floor[row["id"]]["force_on_second_xyz_n"] = (-np.asarray(floor[row["id"]]["force_on_first_xyz_n"])).tolist()
    recovered["floor_actions"] = list(floor.values())
    recovered["four_port_fitting_actions"] = [element.response(np.asarray(response["q"])[element.indices],
        loads=[row for row in prepared.case["loads"] if row["body"] == body], declared_route=factory.guarded.ROUTE)
        for body, element in prepared.fittings.items()]
    return recovered


def execute(prepared, *, pins, command, mask_budget=64, max_iterations=300, branch_observer=None):
    """One solve on one instance; independent admission remains a separate gate."""
    factory.require(not prepared.synthetic_only, "synthetic assembly cannot enter production execution")
    expected = runtime_pins(pins)
    original_operators = operator_fingerprint(prepared)
    state = "eoere-a12-"+factory.canonical({"source_sha256": expected, "inputs": prepared.source_inputs,
        "case": prepared.case, "counts": prepared.counts, "mask_budget": mask_budget,
        "max_iterations": max_iterations})[:24]
    response = search.compatible_contact_solve(prepared.assembly.K, prepared.applied, prepared.groups,
        prepared.contacts, prepared.tangents, mask_budget=mask_budget, max_iterations=max_iterations,
        branch_observer=branch_observer)
    field = {"schema": "eoere_first_order_common_shaft_four_port_candidate/v1", "state_id": state,
        "case_id": prepared.case["case_id"], "accessory_placement": prepared.case["accessory_placement"],
        "source_sha256": expected, "source_inputs": prepared.source_inputs, "counts": prepared.counts,
        "source_input_review": prepared.source_review,
        "floor_reference_plane_numerical_tolerance_mm": prepared.source_inputs["scenario"].get(
            "floor_reference_plane_numerical_tolerance_mm", 1e-6),
        "physical_body_descriptors": prepared.assembly.geo["bodies"], "response": response,
        "body_applied_loads": prepared.case["loads"], "applied_wrench_work_error_n_nmm": prepared.applied_wrench_work_error_n_nmm,
        "fitting_operator_descriptors": [el.descriptor() for el in prepared.fittings.values()],
        "reference_interaction_descriptors": [descriptor(row) for row in [*prepared.groups, *prepared.contacts, *prepared.tangents]],
        "execution": {"command": command, "loaded_driver_sha256": LOADED_SHA, "loaded_factory_sha256": LOADED_FACTORY_SHA,
                      "one_preparation": True, "one_case": True, "automatic_retry": False, "historical_q_used": False},
        "independent_admission_required": True, "release": RELEASE,
        "original_operator_fingerprint_sha256": original_operators,
        "limits": ["First-order gross-stock beam/four-strip/reference-point spring scenario; finite objectivity/current contact applicability unresolved.",
                   "Area-weighted flange40,000 scale, timber1 and panel2 priors are unmeasured, not pressure or demand bounds.",
                   "Whole-foot centroid no-slip is an unverified analytical assumption; no friction capacity, anchor or no-separation clamp.",
                   "Steel grade/heel/hole/warping/prying and complete joint resistance remain unresolved."]}
    if response.get("converged") is True and "q" in response:
        enabled = response["support_state_search_v1"]["accepted_enabled_centroid_xy_hosts"]
        full = search._fresh_fields(prepared.assembly.K, prepared.applied, prepared.groups,
                                    prepared.contacts, prepared.tangents, enabled, np.asarray(response["q"]))
        gradient = np.asarray(full[0])
        factory.require(gradient.shape == (prepared.assembly.ndof,) and np.isfinite(gradient).all(),
                        "fresh full original-law gradient must be a finite full-coordinate vector")
        factory.require(np.max(abs(gradient)) <= frame.GENERALIZED_RESIDUAL_TOLERANCE_N,
                        "fresh full original-law gradient exceeds original tolerance")
        field["response"].update(gradient_n=gradient.tolist(), gradient_inf_n=float(np.max(abs(gradient))),
            q_canonical_sha256=factory.canonical(serial(response["q"])), gradient_canonical_sha256=factory.canonical(gradient.tolist()))
        recovered = recover(prepared, response)
        factory.require(recovered["equilibrium_verification"]["all_body_and_global_checks_pass"] is True,
                        "fresh body/global closure failed; coefficient field cannot advance")
        field.update(recovered)
        for table in ("panel_screw_actions", "contact_actions", "floor_actions", "common_shaft_bearing_actions",
                      "shaft_end_capture_actions", "common_shaft_wood_bearing_actions", "common_shaft_steel_port_actions"):
            for row in field.get(table, []):
                row.update(state_id=state, case_id=field["case_id"], accessory_placement=field["accessory_placement"])
        field["disposition"] = "CONVERGED_CANDIDATE_PENDING_INDEPENDENT_ADMISSION"
    else:
        factory.require("q" not in response, "failed search must not export accepted coefficients")
        field["disposition"] = "FAILED_NO_ACCEPTED_COEFFICIENTS_OR_ACTIONS"
    factory.require(runtime_pins(pins) == expected, "source bytes changed during execution")
    factory.require(operator_fingerprint(prepared) == original_operators, "source operators changed during execution/recovery")
    return field


def load_panel_dependencies(data):
    """Source-equivalent saved six panel operators, one read; no candidate CAD."""
    from scripts import run_thin_bolted_finite_frame as saved

    factory.require(frame.sha(frame.ROOT/SAVED_PANEL_PATH) == SAVED_PANEL_SHA, "saved panel loader source differs")
    # Frozen extraction already binds these unchanged source files. Do not
    # demand new convenience metadata or mutate its preserved output.
    record = {"path": str(frame.EVIDENCE.relative_to(frame.ROOT)), "sha256": frame.EVIDENCE_SHA}
    factory.require(data["source_sha256"].get(record["path"]) == record["sha256"]
                    and frame.sha(frame.ROOT/record["path"]) == record["sha256"], "panel load source join differs")
    panels, panel_pins, proof = saved.reuse_panel_operators()
    cache = str(frame.GEOMETRY_CACHE.relative_to(frame.ROOT))
    factory.require(data["source_sha256"].get(cache) == frame.GEOMETRY_CACHE_SHA
                    and frame.sha(frame.GEOMETRY_CACHE) == frame.GEOMETRY_CACHE_SHA,
                    "unchanged panel cached-geometry source missing")
    manifest = json.loads(frame.GEOMETRY_CACHE.read_bytes())
    records = [row for row in manifest["parts"] if row["kind"] == "panel"]
    factory.require({row["id"] for row in records} == set(data["panel_ids"]) == set(panels),
                    "six source-identical panel owners required")
    for row in records:
        factory.require(data["source_sha256"].get(row["path"]) == row["sha256"]
                        and frame.sha(frame.ROOT/row["path"]) == row["sha256"],
                        "source panel geometry is not byte-identical to reused operator geometry")
    panel_pins = factory.source_pins({**panel_pins, **saved.FIXED_HELPERS, SAVED_PANEL_PATH: SAVED_PANEL_SHA})
    proof = {**proof, "old_contact_rows_or_owners_used": False, "fresh_contact_source": "reviewed successor direct_contacts",
             "only_unchanged_panel_geometry_K_and_load_measure_reused": True}
    return panels, json.loads((frame.ROOT/record["path"]).read_bytes()), panel_pins, proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--inputs-sha256", required=True)
    parser.add_argument("--input-review", type=Path, required=True)
    parser.add_argument("--input-review-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--mask-budget", type=int, default=64)
    parser.add_argument("--max-iterations", type=int, default=300)
    parser.add_argument("--wall-seconds", type=float, default=1770.)
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    factory.require(args.run, "actual preparation/run requires explicit parent --run invocation")
    factory.require(not args.out.exists() and not args.out.with_suffix(args.out.suffix+".interrupted.json").exists()
                    and not args.out.with_suffix(args.out.suffix+".failed.json").exists(),
                    "preserve every existing candidate/failure output")
    factory.require(0. < args.wall_seconds <= 1800., "bounded positive case wall cap required")
    command, events = list(sys.orig_argv), []
    last = {"phase": "before-source-read", "gradient_available": False}
    pins = runtime_pins()

    def alarm(_signum, _frame):
        raise CaseWallTimeLimit("case wall limit")

    def observer(event):
        events.append(copy.deepcopy(event))
        last.update(phase="support-search", branch_event=copy.deepcopy(event))
        print(json.dumps({"support_branch": event}, sort_keys=True), flush=True)

    prior = signal.signal(signal.SIGALRM, alarm)
    start = time.monotonic()
    signal.setitimer(signal.ITIMER_REAL, args.wall_seconds)
    try:
        data, input_pins = factory.read_inputs(args.inputs, args.inputs_sha256)
        pins = runtime_pins(input_pins)
        factory.require(data["case"]["case_id"] == "a12-rear"
                        and data["case"]["accessory_placement"] == "retained-original-top-hold", "one original-envelope A12 case required")
        last["phase"] = "saved-panel-operators"
        panels, integrated, panel_pins, proof = load_panel_dependencies(data)
        pins = runtime_pins({**pins, **panel_pins})
        last["phase"] = "fresh-preparation"
        prepared = factory.prepare(data, panels, integrated, source_sha256=pins,
            source_review={"path": str(args.input_review.resolve().relative_to(frame.ROOT)), "sha256": args.input_review_sha256})
        pins = runtime_pins(prepared.source_sha256)
        last["phase"] = "fresh-support-search"
        field = execute(prepared, pins=pins, command=command, mask_budget=args.mask_budget,
                        max_iterations=args.max_iterations, branch_observer=observer)
        field["saved_panel_operator_preparation"] = proof
        field["execution"].update(elapsed_seconds=time.monotonic()-start, wall_seconds=args.wall_seconds,
                                  branch_events=events)
        write_exclusive(args.out, field)
        return 0 if field["disposition"].startswith("CONVERGED") else 1
    except CaseWallTimeLimit:
        write_exclusive(args.out.with_suffix(args.out.suffix+".interrupted.json"), {
            "schema": "eoere_first_order_execution_interruption/v1", "command": command, "source_sha256": pins,
            "last_observation": last, "branch_events": events, "elapsed_seconds": time.monotonic()-start,
            "accepted_q": None, "accepted_actions": None, "release": RELEASE,
            "preserved_output_sha256": frame.sha(args.out) if args.out.exists() else None})
        return 1
    # Any unaccepted guard failure must preserve a diagnostic, never a field.
    except Exception as error:  # noqa: BLE001
        write_exclusive(args.out.with_suffix(args.out.suffix+".failed.json"), {
            "schema": "eoere_first_order_execution_guard_failure/v1", "command": command, "source_sha256": pins,
            "last_observation": last, "branch_events": events, "elapsed_seconds": time.monotonic()-start,
            "error_type": type(error).__name__, "error": str(error),
            "accepted_q": None, "accepted_actions": None, "release": RELEASE,
            "preserved_output_sha256": frame.sha(args.out) if args.out.exists() else None})
        return 1
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.)
        signal.signal(signal.SIGALRM, prior)


if __name__ == "__main__":
    raise SystemExit(main())
