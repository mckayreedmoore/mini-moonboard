"""Same-state steel allowance scenario for the corrected top-corner bolts.

Reserve nominal yield stress for direct axial load and an assumed parabolic
circular-shank shear field before recomputing the existing lateral reference.
This is an explicit mechanics scenario, not a prescribed NDS interaction rule
or qualification of the actual three-dimensional bolt stress field.
"""

import argparse
import json
import math
from pathlib import Path

import corner_checks as checks
import numpy as np


def run(source, output):
    source, output = source.resolve(), output.resolve()
    checks.require(not output.exists(), "preserve existing interaction output")
    original = checks.read(source)
    pins = {
        checks.ROOT / name: digest
        for name, digest in original["source_sha256"].items()
    }
    for path in (source, Path(__file__), Path(checks.__file__)):
        pins[path] = checks.sha(path)
    for path, digest in pins.items():
        checks.require(checks.sha(path) == digest, "changed input: " + str(path))
    materials = {
        r["member_id"]: r["reduced_geometry_descriptor"]
        for r in checks.read(checks.local.INPUTS)["members"]
    }
    states = []
    for state in original["states"]:
        diameter = state["diameter_mm"]
        side = "/side_" in state["axis_id"]
        gross_area = math.pi * diameter**2 / 4
        axial_area = (0.0524 if side else 0.0318) * 25.4**2
        axial = state["tension_n"] / axial_area
        shear = 4 * state["lateral_n"] / (3 * gross_area)
        yield_mpa = state["conditional_Fyb_psi"] * checks.local.PSI_MPA
        available_squared = yield_mpa**2 - 3 * shear**2
        checks.require(available_squared > 0, "direct shear exhausts steel yield")
        remaining = math.sqrt(available_squared) - axial
        checks.require(remaining > 0, "direct axial/shear exhausts steel yield")
        reference = checks.lateral_reference(
            np.array(state["force_on_cleat_xyz_n"]),
            diameter,
            [88.9, 88.9] if side else [38.1, 139.7],
            [materials[state["host"]]["axis"], materials[state["block"]]["axis"]],
            remaining / checks.local.PSI_MPA,
        )
        ratio = state["lateral_n"] / (
            reference["reference_n"] * state["declared_Cg_Cdelta_multiplier"]
        )
        states.append(
            {
                "case_id": state["case_id"],
                "axis_id": state["axis_id"],
                "block": state["block"],
                "tension_n": state["tension_n"],
                "lateral_n": state["lateral_n"],
                "reserved_axial_stress_mpa": axial,
                "assumed_maximum_shank_shear_stress_mpa": shear,
                "remaining_nominal_bending_yield_stress_mpa": remaining,
                "reduced_Fyb_psi": remaining / checks.local.PSI_MPA,
                "reduced_lateral_reference": reference,
                "same_state_lateral_over_adjusted_reduced_reference": ratio,
            }
        )
    checks.require(len(states) == 48, "incomplete same-state interaction coverage")
    for path, digest in pins.items():
        checks.require(checks.sha(path) == digest, "input changed during calculation")
    report = {
        "schema": "top_corner_same_state_steel_allowance/v1",
        "source_sha256": {
            str(path.relative_to(checks.ROOT)): digest for path, digest in pins.items()
        },
        "states": states,
        "assumed_yield_allowance": "sqrt(Fy^2 - 3*(4*V/(3*A_shank))^2) - T/A_thread",
        "limits": [
            "All forces are simultaneous nominal-gap frame values, not separate envelope peaks.",
            "Axial stress uses nominal thread tensile area; bending uses the conditional smooth-shank diameter.",
            "The assumed parabolic shank shear maximum and uniform axial stress reserve yield before the existing dowel bending reference is calculated.",
            "This stress-field scenario is not a prescribed NDS combined-load equation or a validated root, thread transition, bearing-zone or head/nut interaction result.",
            "Conditional material and component group/geometry adjustments remain those of the source worksheet.",
        ],
        "complete_joint_acceptance": False,
        "hardware_selected": False,
        "physical_release": False,
    }
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    for block in checks.accounting.BLOCK_HOSTS:
        maximum = max(
            s["same_state_lateral_over_adjusted_reduced_reference"]
            for s in states
            if s["block"] == block
        )
        print(block, "same-state reduced steel reference ratio", maximum, flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.input, arguments.output)
