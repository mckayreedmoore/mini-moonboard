"""Parent-only critical-case run with authenticated direct timber compression.

The frozen driver provides operator reuse, initialization, state identity and
export. This bounded orchestration adds the missing six interfaces through the
new descriptor adapter; every mechanics law and numerical method is reused.
It does not rebuild CAD, select a candidate or grant physical release.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

from scripts import run_thin_bolted_finite_frame as previous
from scripts import thin_bolted_finite_newton as newton
from scripts import thin_bolted_timber_face_contact as contact_method

frame, finite, common = previous.frame, previous.finite, previous.common
floor, finished = previous.floor, previous.finished
ROOT, PACKET = frame.ROOT, frame.PACKET
PROOF = PACKET / "timber-face-contact-geometry-v4.json"
PROOF_SHA = "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a"
PREVIOUS_DRIVER_SHA = "5cf423d80e57b6f4386eb6c7aae39961ba083a7b4a457c7d37694cb80101361e"
GEOMETRY_METHOD = PACKET / "timber-face-geometry-method-v4.json"
GEOMETRY_METHOD_SHA = "5a42cffcb02092e9eaca25ad604cf5877c4cb8fa5ac39690e21b478cf98d3655"


def scenario_parameters(args, options, system, contact_parameters, warm_provenance):
    """Retain each frozen scenario choice and bind the newly restored path."""
    return {"panel_intervals": 8, "foundation_port_cell_mm": 70., "beam_size_mm": args.beam_size,
        "wood_E_mpa": 11031.612, "wood_G_over_E_clear_DF_analogy": .064,
        "Hillman_axial_lateral_stiffness_n_mm": args.screw_stiffness, "fitting_section": "gross",
        "panel_foundation_n_mm3": 2., "flange_corner_contact_n_mm": 10000., "floor_corner_contact_n_mm": 25000.,
        "floor_no_slip_xy_penalty_n_mm_per_foot": 100000., "floor_xy_penalty_n_mm_per_corner": 25000.,
        "floor_support_basis": floor.SUPPORT_BASIS, "floor_normal_activation_threshold_n": 1e-7,
        "floor_contact_geometry_sha256": finished.CONTACT_SHA,
        "finite_kinematics_basis": "objective finite beam/plate/ports with potential-derived transported directors",
        "finite_shaft_basis": "isotropic reference-Timoshenko director energy and exact common-right-roll quotient",
        "mechanical_hessian_difference_step_mm": 1e-3,
        "finite_numerical_method": "scaled step-only Levenberg Newton with original-potential gradient-work cancellation control",
        "finite_numerical_options": asdict(options),
        "finite_numerical_producer_sha256": previous.FIXED_HELPERS["scripts/thin_bolted_finite_newton.py"],
        "saved_panel_operator_sha256": previous.OPERATORS_SHA,
        "saved_panel_datum_sha256": previous.datums.DATUMS_SHA,
        "method_receipts_sha256": previous.METHOD_RECEIPTS,
        "finite_initialization_source": warm_provenance or {"kind": "zero finite reference configuration"},
        **system.parameters, **contact_parameters}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["a12-rear"], default="a12-rear")
    parser.add_argument("--beam-size", type=float, default=150.)
    parser.add_argument("--shaft-segment", type=float, default=25.)
    parser.add_argument("--wood-bearing-foundation", type=float, default=26.2467191601)
    parser.add_argument("--steel-bearing-foundation", type=float, default=1799.77502812)
    parser.add_argument("--end-capture-stiffness", type=float, default=1000.)
    parser.add_argument("--screw-stiffness", type=float, default=1000.)
    parser.add_argument("--wood-bedding", type=float, default=1.)
    parser.add_argument("--contact-method-receipt-sha256", required=True)
    parser.add_argument("--warm-start", type=Path)
    parser.add_argument("--warm-start-sha256")
    parser.add_argument("--max-iterations", type=int, default=300)
    parser.add_argument("--max-support-patterns", type=int, default=10)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Preserve issued finite experiments")
    if bool(args.warm_start) != bool(args.warm_start_sha256):
        parser.error("paired warm-start path and digest required")
    options = newton.NewtonOptions(max_iterations=args.max_iterations, max_support_patterns=args.max_support_patterns)
    layout, integrated, pins = frame.inputs()
    receipt_pins = {str((PACKET / path).relative_to(ROOT)): digest for path, digest in previous.METHOD_RECEIPTS.items()}
    pins = contact_method.merge_pins(pins, previous.FIXED_HELPERS, receipt_pins, newton.source_pins(),
        floor.source_pins(), common.source_pins(),
        {"scripts/run_thin_bolted_finite_frame.py": PREVIOUS_DRIVER_SHA,
         str(GEOMETRY_METHOD.relative_to(ROOT)): GEOMETRY_METHOD_SHA,
         str(Path(__file__).resolve().relative_to(ROOT)): frame.sha(Path(__file__))})
    previous.verify_pins(pins)
    warm, warm_provenance = ((None, None) if args.warm_start is None else
                            previous.initialization.read_warm(args.warm_start, args.warm_start_sha256))
    if warm_provenance:
        pins = contact_method.merge_pins(pins, {warm_provenance["path"]: warm_provenance["sha256"]})
    print("Reusing cached frame geometry, interval-eight operators and frozen finite methods", flush=True)
    footprints, floor_proof, floor_pins = finished.read_finished_footprints()
    pins = contact_method.merge_pins(pins, floor_pins)
    geo = frame.geometry(layout, integrated)
    geo["floor_footprints"] = footprints
    cases, gravity = frame.load_cases(integrated, geo)
    case = next(c for c in cases if c["case_id"] == args.case and c["primary_load_basis"])
    panels, panel_pins, preparation = previous.reuse_panel_operators()
    pins = contact_method.merge_pins(pins, panel_pins)
    assembly = frame.ElasticAssembly(layout, geo, panels, beam_size=args.beam_size)
    system = common.CommonShaftSystem(assembly, common.read_inputs(),
        wood_foundation_n_mm2=args.wood_bearing_foundation, plate_foundation_n_mm2=args.steel_bearing_foundation,
        end_capture_n_mm=args.end_capture_stiffness, max_segment_mm=args.shaft_segment)
    reference_ndof = assembly.ndof
    groups, contacts, _ = frame.elastic_connections(assembly, 1000., 1.5875, args.screw_stiffness)
    groups = [r for r in groups if r["kind"] == "panel_screw"] + system.bearing_groups
    contacts += system.end_captures
    tangents = floor.corner_rows(assembly, contacts)
    reference_operator_sha = hashlib.sha256(assembly.K.data.tobytes()).hexdigest()
    case = system.remap_bolt_gravity(copy.deepcopy(case))
    potential = finite.FiniteFramePotential.from_prepared(assembly, system, case, integrated, groups, contacts,
                                                         tangents, source_sha256=pins)
    potential = contact_method.attach_prepared(potential, PROOF, PROOF_SHA,
        bedding_n_mm3=args.wood_bedding, scenario_id=contact_method.DEFAULT_SCENARIO_ID,
        method_receipt_sha256=args.contact_method_receipt_sha256)
    pins = contact_method.merge_pins(pins, potential.source_sha256)
    contact_parameters = potential.timber_face_contact_parameters
    contact_ids = [row["id"] for row in potential.interactions if row["kind"] == "timber_face_contact"]
    parameters = scenario_parameters(args, options, system, contact_parameters, warm_provenance)
    case["state_id"] = previous.state_identity(case, parameters)
    potential.case["state_id"] = case["state_id"]
    q0, initialization = previous.initial_vector(warm, warm_provenance, potential.ndof, reference_ndof, args)
    preparation = {**preparation, "reference_dofs": reference_ndof, "finite_dofs": potential.ndof,
        "physical_body_count": 132, "initialization": initialization,
        "prepared_reference_operator_sha256": reference_operator_sha,
        "geometry_preparations": 1, "panel_reference_preparations": 1, "assembly_preparations": 1,
        "timber_contact_preparation": {"parameters": contact_parameters, "contact_ids": contact_ids,
                                       "new_mechanics_or_geometry_preparation": False}}
    print(json.dumps({"case": args.case, "state_id": case["state_id"], "dofs": potential.ndof,
        "physical_bodies": 132, "panel_contacts": 530, "timber_contacts": len(contact_ids),
        "phase": "corrected finite Newton"}), flush=True)

    def progress(event):
        if event["event"] == "newton-iteration":
            print(json.dumps({"case": args.case, **{key: event[key] for key in ("event", "support_pattern_iteration",
                "iteration", "gradient_inf_n", "physical_potential_energy_nmm", "step_damping") if key in event}}), flush=True)

    start = time.monotonic()
    solution = newton.solve_finite_potential(potential.response, q0,
        quotient=newton.CircularShaftQuotient(potential.shaft_replacement),
        support_feedback=newton.CornerSupportFeedback.from_finite_frame(potential), options=options, progress=progress)
    if hashlib.sha256(assembly.K.data.tobytes()).hexdigest() != reference_operator_sha:
        raise ValueError("Reused reference operator changed")
    previous.verify_pins(pins)
    report = previous.export_state(case, parameters, pins, floor_proof, preparation, solution, potential, gravity,
                                  [sys.executable, "-m", "scripts.run_thin_bolted_timber_contact_frame", *sys.argv[1:]])
    report["execution"]["elapsed_seconds"] = time.monotonic() - start
    report["limits"].extend(contact_method.LIMITS)
    report["timber_contact_geometry_sha256"] = PROOF_SHA
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(previous.serialization.dump(report))
    print(json.dumps({"path": str(args.out), "sha256": frame.sha(args.out), "bytes": args.out.stat().st_size,
        "state_id": case["state_id"], "converged": solution["converged"], "termination": solution["termination"],
        "gradient_inf_n": solution["gradient_inf_n"], "independent_extended_admission_required": True}), flush=True)


if __name__ == "__main__":
    main()
