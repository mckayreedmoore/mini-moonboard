"""Compare two identical, frictionless flat washers at one frozen local T/M."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EDGE = HERE / "upper-right-washer-edge.py"
EDGE_SHA256 = "ffe3db3e8c707851d44f0c60c43e6e6ef4aa4845f753dc6880c64186e3c75e61"


def interface_witness(edge, model, single_stiffness, state):
    """Recover the hard-contact multiplier and each individual plate residual."""
    pose = np.array(state["scaled_variables_mm"])
    drive = edge.drive_vector(model, state["T_n"], state["M_magnitude_nmm"])
    _, _, _, pressures, _ = edge.evaluate(model, pose, drive, edge.contacts(model))
    wood = pressures[0]
    head = np.zeros_like(wood)
    head[model["head_selection"]] = pressures[1]
    interface = (wood + head) / 2
    area, mapping = model["area"], model["wood_map"]
    top = single_stiffness @ pose + mapping.T @ (area * (interface - head))
    bottom = single_stiffness @ pose + mapping.T @ (area * (wood - interface))
    force = float(area @ interface)
    moments = [float((area * model[key]) @ interface) for key in ("x", "y")]
    residuals = [moments[0] - state["M_magnitude_nmm"], moments[1]]
    # The last three coordinates belong to the rigid head, not either plate.
    plate_residuals = [float(np.max(np.abs(value[:-3]))) for value in (top, bottom)]
    edge.require(np.min(interface) >= 0, "interface requires tensile normal traction")
    edge.require(max(plate_residuals) <= edge.GRADIENT_TOLERANCE,
                 "individual washer weak equilibrium residual exceeds tolerance")
    edge.require(abs(force - state["T_n"]) <= edge.FORCE_TOLERANCE,
                 "interface force does not recover source T")
    edge.require(max(map(abs, residuals)) <= edge.MOMENT_TOLERANCE,
                 "interface first moment does not recover source M")
    return {
        "pressure_law": "p_interface=(p_head+p_wood)/2; p_head=0 outside pressing band",
        "minimum_pressure_mpa": float(np.min(interface)),
        "maximum_pressure_mpa": float(np.max(interface)),
        "positive_pressure_area_mm2": float(np.sum(area[interface > 0])),
        "zero_pressure_area_mm2": float(np.sum(area[interface == 0])),
        "normal_gap_mm": 0.0,
        "pressure_gap_complementarity_nmm": 0.0,
        "top_plate_scaled_gradient_maximum_n": plate_residuals[0],
        "bottom_plate_scaled_gradient_maximum_n": plate_residuals[1],
        "interface_force_n": force,
        "interface_force_residual_n": force - state["T_n"],
        "interface_first_moments_nmm": moments,
        "interface_first_moment_residuals_nmm": residuals,
        "tangential_traction": "zero; relative tangential sliding is free",
        "contact_conclusion": "coincident transverse fields satisfy both plate equations and unilateral hard-contact KKT conditions within this discrete linear model",
    }, interface, wood, head


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resolution", choices=("coarse", "fine"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_stacked_washer_edge", EDGE)
    if spec is None or spec.loader is None:
        raise ValueError("frozen edge helper unavailable")
    edge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(edge)
    edge.require(edge.sha(EDGE) == EDGE_SHA256, "frozen edge helper differs")
    module, source, pins = edge.load_source()
    pins[Path(__file__).resolve()] = edge.sha(Path(__file__).resolve())
    module.authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    model, state, coupon, rigid, interface = None, None, None, None, None
    fields, failure, debug = None, None, {"stage": "matrix-preparation"}
    try:
        model = edge.make_model(module, args.resolution)
        single_stiffness = model["stiffness"].copy()
        # ponytail: identical plates admit an exact common-w hard-contact witness.
        # Sum their energy, retaining each original constitutive law for stress.
        for key in ("bending_stiffness", "shear_stiffness", "stiffness"):
            model[key] = 2 * model[key]
        rigid = edge.rigid_modes(model, debug)
        coupon = edge.coupon(model, rigid, debug)
        debug = {}
        state, fields = edge.solve_state(model, source, debug)
        interface, pressure, wood, head = interface_witness(edge, model, single_stiffness, state)
        for row in fields:
            row["interface_pressure_mpa"] = (row["head_pressure_mpa"] + row["wood_pressure_mpa"]) / 2
        np.savez(output / "interface.npz", pressure_mpa=pressure,
                 wood_pressure_mpa=wood, head_pressure_mpa=head,
                 area_mm2=model["area"], x_mm=model["x"], y_mm=model["y"])
        module.authenticate(pins)
    except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
        failure = {"error": str(error), "last_accepted_state": debug,
                   "physical_incompatibility_proved": False}
    if fields:
        with (output / "fields.csv").open("w", newline="") as stream:
            module.csv_rows(stream, fields)
    result = {
        "schema": "two_identical_frictionless_flat_washers/v1",
        "status": "STOP" if failure else "FINITE_TWO_WASHER_CONTACT_HYPOTHESIS",
        "resolution": args.resolution, "source": source, "state": state,
        "interface_witness": interface, "failure": failure,
        "engineering_coupon": coupon, "rigid_mode_diagnostics": rigid,
        "model": {
            "number_of_washers": 2, "individual_family": module.FAMILIES["rail"],
            "assembled_bending_and_shear_stiffness_multiplier": 2,
            "individual_stress_constitutive_multiplier": 1,
            "resolution": edge.RESOLUTIONS[args.resolution],
            "E_mpa_hypothesis": module.ESTEEL, "nu_hypothesis": module.NU,
            "Fy_mpa_hypothesis": module.FY_HYPOTHESIS,
            "Kwood_mpa_per_mm_hypothesis": module.KWOOD,
            "Khead_mpa_per_mm_hypothesis": module.KHEAD,
            "primary_energy_source": module.ENERGY_SOURCE,
            "interface": "flat concentric identical plates; hard unilateral normal contact; zero friction and no adhesion",
            "reduction": "2K for equal transverse fields; original K for each washer's stress and equilibrium; positive interface multiplier verifies admissibility rather than imposing bonded composite action",
        },
        "limits": [
            "This is the old fixed 709.052842 N / 2292.108528 Nmm witness, not the current corner-first-order source or an installed load.",
            "Full geometric coincidence is the recovered hard-contact solution only for identical, flat, concentric linear plates with zero initial gap. No opening is forbidden by tensile traction.",
            "Zero-pressure regions may have zero gap without positive contact pressure. Normal complementarity does not require positive pressure everywhere.",
            "Different thicknesses, misalignment, washer dish/burrs and finite through-thickness compression are not modeled.",
            "Each washer has its own original thickness/material law. A bonded 2t plate would have eight times original bending stiffness and is not used.",
            "The fine/coarse comparison is numerical evidence for this approximation, not a guaranteed physical error bound.",
            "The inherited shell stress proxy excludes normal/contact-edge 3D stress, plasticity, membrane effects, preload and friction.",
            "Wood/head contact laws and head footprint remain hypothetical; product yield and actual contact faces remain unknown.",
            "Changed end compliance and added axial thickness are not fed back into bolt-pair or frame mechanics, hardware engagement or CAD.",
            "No hardware adoption, purchased-quantity change, complete-joint acceptance or physical release follows from this local comparison.",
        ],
        "source_sha256": {str(path.relative_to(edge.ROOT)): digest for path, digest in sorted(pins.items())},
        "actual_washer_stress_mpa": None, "actual_washer_capacity_n": None,
        "actual_washer_yield_mpa": None, "complete_joint_acceptance": False,
        "physical_release": False,
    }
    hashes = {path.name: edge.sha(path) for path in output.iterdir()}
    result["output_sha256"] = hashes.copy()
    module.dump(output / "checks.json", result)
    hashes["checks.json"] = edge.sha(output / "checks.json")
    module.dump(output / "source-pins.json", {"source_sha256": result["source_sha256"],
                                             "output_sha256": hashes})
    module.authenticate(pins)
    print(json.dumps({"status": result["status"], "resolution": args.resolution,
                      "checks_sha256": hashes["checks.json"]}))
    if failure:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
