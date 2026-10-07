"""Parent-owned finite frame preparation, execution and immutable export.

The first discretization reuses authenticated interval-eight panel operators
and their coarser contact quadrature. Historical displacement and force fields
are never selected as results. A failed common-shaft iterate may initialize
the unchanged coordinate blocks only; seventy finite shaft gauge coordinates
are added explicitly. Every expensive operation is serialized by the parent.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

from scripts import run_thin_bolted_common_shaft_incremental as initialization
from scripts import run_thin_bolted_finished_floor as finished
from scripts import run_thin_bolted_mechanics as serialization
from scripts import thin_bolted_common_shaft as common
from scripts import thin_bolted_finite_frame as finite
from scripts import thin_bolted_floor_contact as floor
from scripts import thin_bolted_frame_mechanics as frame
from scripts import thin_bolted_panel_coupled as datums
from scripts import thin_bolted_panel_load_diagnostics as mass_measure

ROOT, PACKET = frame.ROOT, frame.PACKET
OPERATORS = ROOT / "fea/generated/thin-bolted-panel/operators-intervals8.npz"
OPERATORS_SHA = "2b97d8c1741a0fbef119eb00b3f43bdf5f76e802b4851962a62fc555f1813468"
REFERENCE = PACKET / "compatible-frame-a12-rear-finished-floor-v4.json"
REFERENCE_SHA = "8d90941f9d1cb20d938ddc65992b2db7b0fe0c38420bf6bfc10fc0684281256d"
FIXED_HELPERS = {
    "scripts/thin_bolted_finite_newton.py": "039282fa1c06d90b5e899c1c69c2920c003b42db1a8600e390a7a2d9aca75afe",
    "scripts/thin_bolted_finite_frame.py": "68f711549da9e6b52c60db4e4df78235ba8105084ded0d81c9a3430cf5973588",
    "scripts/thin_bolted_floor_contact.py": "0852ced82484414621106314531e883f713f5943358541539e8750af243c2e1f",
    "scripts/thin_bolted_panel_coupled.py": "abd6da1911ec79ec25b57fc2a5cc20b9e687057a15b6df2f5e8fb292a42c6bd0",
    "scripts/thin_bolted_panel_load_diagnostics.py": "ff5e0e7b3944e64379181a6b3a1c442b921c197b87d25da3bd20a2d69ec63ebd",
    "scripts/run_thin_bolted_common_shaft_incremental.py": "342ca53532d08bab670bac13f923c00665bd4660722541ff936e4380131b1588",
    "scripts/run_thin_bolted_finished_floor.py": "626f7f1561b097ab3b73eaa5f7fe6c70e7f24b50c6db7ef76f0fe63c86be2140",
    "scripts/run_thin_bolted_mechanics.py": "b37ec3806852d84b51f1b2d6daa41b8608f175934e0806869b25a6c9e3f33413",
}
METHOD_RECEIPTS = {
    "finite-newton-method-v4.json": "c1fbebb86256f247aa14ee0bf63e0e7e6eb2af591f7fe53bf130e4a84e930f9b",
    "finite-frame-method-v4.json": "790b1925f042cc3f48fae596f5f8097ec64f8dc9605a00d9e200b4cd7bf28e9f",
    "floor-corner-stick-method-coupons-v4.json": "e7569ddc3ea2addb6171b3a3bcccadaa1b004b8c14da94b0eb61320b3982355e",
    "finite-panel-adapter-method-v1.json": "80c8f13fbdf9d352e10be44f9c4db500f904e8965d619c48fc3647c40026e7b9",
    "finite-mechanics-method-v4.json": "423eeb4eae42e096f9238df2bbcf65f090dd0b3b5a5288ec18d735cc335f9930",
    "finite-connector-method-v4.json": "2d53799c86bdeed9f9337cf87d2555f02c45732e025376bb24f2308b91b52fef",
    "isotropic-shaft-method-v4.json": "06943e846c80f506af080c8e5e029b9f6b6b928d23e36abb3539ea46b92e1c85",
}


def verify_pins(pins):
    for relative, expected in pins.items():
        if frame.sha(ROOT / relative) != expected:
            raise ValueError("finite driver frozen source differs: " + relative)


def reuse_panel_operators():
    """Rehydrate saved reference geometry, matrices and contact rows only."""
    pins = {str(path.relative_to(ROOT)): digest for path, digest in (
        (REFERENCE, REFERENCE_SHA), (OPERATORS, OPERATORS_SHA),
        (datums.DATUMS, datums.DATUMS_SHA), (datums.ASSESSMENT, datums.ASSESSMENT_SHA))}
    verify_pins({**pins, **FIXED_HELPERS})
    old = json.loads(REFERENCE.read_text())
    integrated = json.loads(frame.EVIDENCE.read_text())
    metadata = json.loads(datums.DATUMS.read_text())
    panels = datums.prepared_datums(old, json.loads(datums.ASSESSMENT.read_text()), metadata, integrated)
    layout = json.loads(frame.LAYOUT.read_text())
    with np.load(OPERATORS, allow_pickle=False) as operators:
        for name, panel in panels.items():
            panel.pop("q")
            panel["screws"] = [r for r in layout["screw_axes"] if r["panel"] == name]
            for key in ("K", "screw_u", "screw_v", "screw_w", "contact_w", "contact_xy", "contact_area"):
                panel[key] = operators[name + "/" + key].copy()
            panel["contact_owner"] = list(metadata[name]["contact_receivers"])
            if ([r["axis_id"] for r in panel["screws"]] != metadata[name]["screw_axes"]
                    or [r["receiver"] for r in panel["screws"]] != metadata[name]["screw_receivers"]
                    or len(panel["contact_owner"]) != len(panel["contact_area"])):
                raise ValueError("saved panel screw/contact ownership differs")
            geometry = panel["geometry"]
            positions = (geometry["origin"] + panel["contact_xy"] @ geometry["axes"][:, :2].T
                         - panel["thickness"] / 2 * geometry["axes"][:, 2])
            if not np.allclose(positions, operators[name + "/contact_points_xyz_mm"], atol=1e-7, rtol=0.):
                raise ValueError("saved contact point datum differs")
            mass_measure.mass_only_quadrature(panel)
    if sum(len(p["contact_area"]) for p in panels.values()) != 530:
        raise ValueError("initial saved coarser panel contact census differs")
    proof = {"schema": "thin_bolted_finite_panel_preparation/v1", "panel_intervals": 8,
        "contact_maximum_edge_mm": 70., "panel_contact_port_count": 530,
        "source_sha256": pins, "saved_reference_geometry_and_operators_reused": True,
        "historical_displacements_forces_or_acceptance_used": False,
        "panel_reference_K_reassembled": False, "CAD_rebuilt": False,
        "finite_energy_quadrature_reuses_frozen_reference_measure": True}
    return panels, pins, proof


def state_identity(case, parameters):
    identity = {"case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
                "parameters": parameters, "geometry_cache_sha256": frame.GEOMETRY_CACHE_SHA}
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return "thin-finite-v4-" + hashlib.sha256(payload).hexdigest()[:24]


def initial_vector(warm, provenance, ndof, reference_ndof, args):
    """Append only missing finite twist coordinates; transfer no load result."""
    if warm is None:
        return np.zeros(ndof), {"kind": "zero finite reference configuration"}
    expected = {"panel_intervals": 8, "beam_size_mm": args.beam_size, "shaft_max_segment_mm": args.shaft_segment}
    if provenance["reference_discretization"] != expected or len(warm) != reference_ndof or ndof != reference_ndof + 70:
        raise ValueError("failed warm iterate does not match unchanged reference coordinate blocks")
    q = np.zeros(ndof)
    q[:reference_ndof] = warm
    return q, {**provenance, "kind": "failed reference common-shaft iterate plus70 zero finite twist coordinates",
        "new_physical_contact_and_kinematic_laws_resolved_again": True,
        "source_contact_discretization_does_not_qualify_new_contact_discretization": True}


def export_state(case, parameters, pins, proof, preparation, solution, potential, gravity, command):
    """Keep failed initialization separate from accepted finite coefficients."""
    solved = bool(solution["converged"])
    response = {key: value for key, value in solution.items() if key != "physical_fields"}
    result = {"schema": "thin_bolted_finite_frame_response/v1", "candidate": potential.mechanics.assembly.layout["candidate"],
        "revision": potential.mechanics.assembly.layout["revision"], "state_id": case["state_id"],
        "case_id": case["case_id"], "accessory_placement": case["accessory_placement"],
        "layout_report_sha256": frame.LAYOUT_SHA, "geometry_cache_sha256": frame.GEOMETRY_CACHE_SHA,
        "disposition": "CONDITIONAL_FINITE_ELASTIC_SURROGATE" if solved else "FAILED_FINITE_NUMERICAL_EXPERIMENT",
        "parameters": copy.deepcopy(parameters), "source_sha256": dict(pins),
        "body_identities": [r["id"] for r in potential.mechanics.assembly.geo["bodies"]],
        "body_reference_applied_loads": copy.deepcopy(case["loads"]),
        "finished_floor_footprints": copy.deepcopy(proof), "gravity": gravity,
        "tool_versions": {"python": sys.version.split()[0], **{name: importlib.metadata.version(name)
                          for name in ("numpy", "scipy", "cadquery", "cadquery-ocp")}},
        "preparation_proof": preparation, "response": response,
        "usable_conditional_actions": solved, "independent_admission_required": True,
        "compatible_numerical_mvp_complete": False, "release": dict(frame.RELEASE),
        "execution": {"command": command, "environment": {"OPENBLAS_NUM_THREADS": os.environ.get("OPENBLAS_NUM_THREADS")},
            "native_solver_run": False, "geometry_rebuilt": False, "parent_serialized_execution": True,
            "historical_passes_transferred": False},
        "limits": [
            "This is a conditional finite elastic beam/plate/contact scenario, not a physical demand bound or climber rating.",
            "Uniform gross timber beams omit actual cut stiffness. Targeted leg-recess inertia is materially lower; net section, local fracture, shear and stability remain separate.",
            "APA diagonal Green/covariant plate proxies and local hole/contact quadrature require applicability and refinement evidence; Hillman stiffness/resistance is not qualified.",
            "Circular shaft and fitting methods require local curvature/mesh and actual hole/heel/washer/seating checks. No bolt-clamp friction or physical twist restraint is added.",
            "Corner-local rough elastic sticking uses an unverified no-slip floor assumption; lifted corners carry no shear. No friction capacity, anchor or no-separation law is claimed.",
            "Both generalized panel load correction potentials remain explicit and contribute current rigid wrenches separately from physical forces."]}
    if solved:
        fields = solution["physical_fields"]
        for key in ("finite_interaction_actions", "finite_body_applied_loads", "panel_generalized_load_corrections",
                    "finite_kinematic_map", "reference_interaction_descriptors", "wrench_reference_xyz_mm"):
            result[key] = fields[key]
        response["gradient_n"] = fields["gradient_n"]
        response["component_potential_energies_nmm"] = fields["component_potential_energies_nmm"]
        response["floor_normal_reactions_n"] = fields["floor_normal_reactions_n"]
        response["floor_xy_enabled_support_ids"] = fields["floor_xy_enabled_support_ids"]
    else:
        if "q" in response or "physical_fields" in solution:
            raise ValueError("failed finite state cannot export accepted coefficients/actions")
        result["failed_response_without_recovered_actions"] = True
    verify_pins(result["source_sha256"])
    return result


def main():
    from scripts import thin_bolted_finite_newton as newton

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", nargs="+", default=["a12-rear"])
    parser.add_argument("--out", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--warm-start", type=Path)
    parser.add_argument("--warm-start-sha256")
    parser.add_argument("--beam-size", type=float, default=150.)
    parser.add_argument("--shaft-segment", type=float, default=25.)
    parser.add_argument("--screw-stiffness", type=float, default=1000.)
    parser.add_argument("--wood-bearing-foundation", type=float, default=1000. / 38.1)
    parser.add_argument("--steel-bearing-foundation", type=float, default=10000. / 5.55625)
    parser.add_argument("--end-capture-stiffness", type=float, default=1000.)
    parser.add_argument("--max-iterations", type=int, default=300)
    parser.add_argument("--max-support-patterns", type=int, default=10)
    args = parser.parse_args()
    if (args.out is None) == (args.out_dir is None) or (args.out and len(args.cases) != 1):
        parser.error("use --out for one case or --out-dir for multiple cases")
    if len(set(args.cases)) != len(args.cases) or bool(args.warm_start) != bool(args.warm_start_sha256):
        parser.error("unique cases and paired warm source/hash required")
    paths = [args.out] if args.out else [args.out_dir / f"finite-frame-{case}-v4.json" for case in args.cases]
    if any(path.exists() for path in paths):
        raise FileExistsError("preserve issued finite states")
    options = newton.NewtonOptions(max_iterations=args.max_iterations, max_support_patterns=args.max_support_patterns)
    layout, integrated, pins = frame.inputs()
    verify_pins(FIXED_HELPERS)
    receipt_pins = {str((PACKET / path).relative_to(ROOT)): digest for path, digest in METHOD_RECEIPTS.items()}
    verify_pins(receipt_pins)
    pins.update(FIXED_HELPERS)
    pins.update(receipt_pins)
    pins.update(newton.source_pins())
    pins.update(floor.source_pins())
    pins.update(common.source_pins())
    pins[str(Path(__file__).relative_to(ROOT))] = frame.sha(Path(__file__))
    warm, warm_provenance = ((None, None) if args.warm_start is None
                             else initialization.read_warm(args.warm_start, args.warm_start_sha256))
    if warm_provenance:
        pins[warm_provenance["path"]] = warm_provenance["sha256"]
    print("Preparing one finite assembly from shared geometry and saved panel operators", flush=True)
    footprints, proof, floor_pins = finished.read_finished_footprints()
    pins.update(floor_pins)
    geo = frame.geometry(layout, integrated)
    geo["floor_footprints"] = footprints
    cases, gravity = frame.load_cases(integrated, geo)
    selected = [next(c for c in cases if c["case_id"] == name and c["primary_load_basis"]) for name in args.cases]
    panels, panel_pins, preparation = reuse_panel_operators()
    pins.update(panel_pins)
    assembly = frame.ElasticAssembly(layout, geo, panels, beam_size=args.beam_size)
    system = common.CommonShaftSystem(assembly, common.read_inputs(),
        wood_foundation_n_mm2=args.wood_bearing_foundation, plate_foundation_n_mm2=args.steel_bearing_foundation,
        end_capture_n_mm=args.end_capture_stiffness, max_segment_mm=args.shaft_segment)
    reference_ndof = assembly.ndof
    groups, contacts, _ = frame.elastic_connections(assembly, 1000., 1.5875, args.screw_stiffness)
    groups = [r for r in groups if r["kind"] == "panel_screw"] + system.bearing_groups
    contacts += system.end_captures
    tangents = floor.corner_rows(assembly, contacts)
    base_operator_pin = hashlib.sha256(assembly.K.data.tobytes()).hexdigest()
    parameters = {"panel_intervals": 8, "foundation_port_cell_mm": 70., "beam_size_mm": args.beam_size,
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
        "finite_numerical_producer_sha256": FIXED_HELPERS["scripts/thin_bolted_finite_newton.py"],
        "saved_panel_operator_sha256": OPERATORS_SHA,
        "saved_panel_datum_sha256": datums.DATUMS_SHA,
        "method_receipts_sha256": METHOD_RECEIPTS, **system.parameters}
    command = [sys.executable, "-m", "scripts.run_thin_bolted_finite_frame", *sys.argv[1:]]
    previous_q = None
    previous_initialization = None
    for case, path in zip(selected, paths, strict=True):
        case = system.remap_bolt_gravity(copy.deepcopy(case))
        case_parameters = copy.deepcopy(parameters)
        case_parameters["finite_initialization_source"] = (previous_initialization or warm_provenance
                                                           or {"kind": "zero finite reference configuration"})
        case["state_id"] = state_identity(case, case_parameters)
        potential = finite.FiniteFramePotential.from_prepared(assembly, system, case, integrated, groups, contacts, tangents,
                                                              source_sha256=pins)
        pins.update(potential.source_sha256)
        q0, init = initial_vector(warm, warm_provenance, potential.ndof, reference_ndof, args)
        if previous_q is not None:
            q0, init = previous_q.copy(), previous_initialization
        per_case_preparation = {**preparation, "reference_dofs": reference_ndof, "finite_dofs": potential.ndof,
            "physical_body_count": 132, "initialization": init, "prepared_reference_operator_sha256": base_operator_pin,
            "geometry_preparations": 1, "panel_reference_preparations": 1, "assembly_preparations": 1}
        last_progress = [0.]

        def progress(event, case_id=case["case_id"], last_progress=last_progress):
            now = time.monotonic()
            if event["event"] == "newton-iteration" or now - last_progress[0] >= 30.:
                display = {key: event[key] for key in ("event", "support_pattern_iteration", "iteration", "gradient_inf_n",
                           "physical_potential_energy_nmm", "step_damping") if key in event}
                print(json.dumps({"case": case_id, **display}), flush=True)
                last_progress[0] = now

        print(json.dumps({"case": case["case_id"], "state_id": case["state_id"], "dofs": potential.ndof,
                          "physical_bodies": 132, "panel_contacts": 530, "phase": "finite Newton"}), flush=True)
        solution = newton.solve_finite_potential(potential.response, q0,
            quotient=newton.CircularShaftQuotient(potential.shaft_replacement),
            support_feedback=newton.CornerSupportFeedback.from_finite_frame(potential), options=options, progress=progress)
        if hashlib.sha256(assembly.K.data.tobytes()).hexdigest() != base_operator_pin:
            raise ValueError("shared reference material operator changed")
        report = export_state(case, case_parameters, pins, proof, per_case_preparation, solution, potential, gravity, command)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x") as stream:
            stream.write(serialization.dump(report))
        print(json.dumps({"case": case["case_id"], "path": str(path), "sha256": frame.sha(path),
            "converged": solution["converged"], "termination": solution["termination"],
            "gradient_inf_n": solution["gradient_inf_n"], "independent_admission_required": True}), flush=True)
        if not solution["converged"]:
            break
        previous_q = np.asarray(solution["q"])
        previous_initialization = {"kind": "preceding finite case as initialization only", "forces_transferred": False,
            "source_state_id": case["state_id"], "path": str(path.resolve().relative_to(ROOT)), "sha256": frame.sha(path)}
        pins[previous_initialization["path"]] = previous_initialization["sha256"]


if __name__ == "__main__":
    main()
