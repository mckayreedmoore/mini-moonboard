#!/usr/bin/env python3
"""Calculate conditional end-grain references from ten frozen bolt axes."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = HERE.parent / "remaining-single-shear-reference-2026-10-01/produce.py"
OLD_SHA = "5f2a7fdca2ef0c56c661fa10e4122189f8a7a1ae0725062cb8c56d95dd911edf"
CENSUS = HERE / "role_census.py"
CENSUS_SHA = "a8bd7797b1f46c11f0a9603c5a2fa87742bf9d39e99e0db33942546216ec664c"
PDF = HERE.parent / (
    "hardware-material-specification-2026-09-30/materials-source/"
    "AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf"
)
PDF_SHA = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
REGISTER_SHA = "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e"
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605
CEG = 0.67
AXIS_TOL = 1e-8


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_pinned(name: str, path: Path, expected: str):
    require(path.is_file() and sha(path) == expected, f"pinned source changed: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def methods():
    final = load_pinned("end_grain_source_reference", OLD, OLD_SHA)
    final.pin_sources()
    require(sha(PDF) == PDF_SHA, "NDS end-grain method source changed")
    _, nds, bearing = final.basis_sources()
    return final, nds, bearing


def conditional_reference(
    final: Any, nds: Any, bearing: Any, axis: dict, state: dict,
) -> dict:
    """One parallel-grain receiver is main, independent of endpoint convention.

    This role interpretation is conditional, supported by AWC's bolted-role
    FAQ and symmetric yield equations. Extending it to the main-member-only
    end-grain clauses is an engineering inference, not an adopted capacity.
    """
    receivers = axis["receivers"]
    require(len(receivers) == 2, "only two-receiver single shear is supported")
    receiver_ids = [row["receiver_id"] for row in receivers]
    require(len(set(receiver_ids)) == 2
            and receiver_ids == axis["receiver_ids_underhead_to_tip"],
            "receiver order or identity differs")
    bolt_axis = final.unit(axis["modeled_bolt_axis_unit_global_xyz"])
    alignment = [abs(final.dot(bolt_axis, final.unit(
        row["source_descriptor_grain_axis_unit_global_xyz"]
    ))) for row in receivers]
    main_indices = [i for i, value in enumerate(alignment) if value >= 1 - AXIS_TOL]
    side_indices = [i for i, value in enumerate(alignment) if value <= AXIS_TOL]
    require(len(main_indices) == len(side_indices) == 1,
            "requires one parallel and one perpendicular bolt/grain receiver")
    main_index, side_index = main_indices[0], side_indices[0]
    main, side = receivers[main_index], receivers[side_index]
    require(axis["parallel_grain_receiver_id"] == main["receiver_id"],
            "census parallel-grain identity changed")
    forces = [state["actual_lateral_force_on_receiver_0_N"],
              state["actual_lateral_force_on_receiver_1_N"]]
    force_units = [final.unit(force) for force in forces]
    final.close_vector(forces[0], [-value for value in forces[1]],
                       "signed lateral receiver forces do not close")
    require(all(abs(final.dot(bolt_axis, vector)) <= AXIS_TOL for vector in force_units),
            "lateral force has a bolt-axis component")
    demand = final.norm(forces[0])
    require(final.close(demand, state["actual_lateral_resultant_N"]),
            "source lateral resultant differs")
    angles = [final.angle_to_grain_degrees(force, receiver[
        "source_descriptor_grain_axis_unit_global_xyz"
    ]) for force, receiver in zip(forces, receivers, strict=True)]
    require(abs(angles[main_index] - 90.0) < 1e-7,
            "end-grain main lateral load must be perpendicular to grain")
    for receiver, angle in zip(receivers, angles, strict=True):
        require(final.close(angle, state["actual_lateral_angle_to_grain_deg_by_receiver"][
            receiver["receiver_id"]], absolute=1e-7), "source load/grain angle differs")
    lengths = []
    for receiver in receivers:
        start, end = receiver["modeled_interval_from_underhead_mm"]
        length_in = (end - start) / 25.4
        require(math.isfinite(length_in) and length_in > 0
                and final.close(length_in, receiver["modeled_bearing_length_in"]),
                "modeled bearing interval length differs")
        lengths.append(length_in)
    main_fe = 4450.0  # NDS 12.3.3.4: use Fe perpendicular for end-grain main.
    side_fe = bearing.dfl_dowel_bearing_psi(0.25, angles[side_index])
    raw = final.single_shear_reference(
        nds, main_length_in=lengths[main_index], side_length_in=lengths[side_index],
        main_fe_psi=main_fe, side_fe_psi=side_fe, theta_degrees=90.0,
    )
    ceg_modes = {mode: value * CEG
                 for mode, value in raw["unadjusted_reference_modes_lbf"].items()}
    governing = raw["governing_mode"]
    reference_N = ceg_modes[governing] * N_PER_LBF
    return {
        "main_receiver": main["receiver_id"],
        "side_receiver": side["receiver_id"],
        "main_receiver_underhead_to_tip_index": main_index,
        "role_basis": "conditional end-grain-main interpretation independent of modeled head/nut order",
        "end_grain_role_extension_is_engineering_inference": True,
        "main_bearing_length_in": lengths[main_index],
        "side_bearing_length_in": lengths[side_index],
        "main_Fe_perpendicular_psi": main_fe,
        "side_Fe_actual_angle_psi": side_fe,
        "actual_angle_degrees_by_receiver": dict(zip(receiver_ids, angles, strict=True)),
        "reduction_theta_degrees": 90.0,
        "Ktheta": 1.25,
        **raw,
        "Ceg": CEG,
        "Ceg_application_count": 1,
        "Ceg_only_reference_modes_lbf": ceg_modes,
        "governing_Ceg_only_reference_N": reference_N,
        "lateral_demand_to_Ceg_only_reference_ratio": demand / reference_N,
        "joint_accepted": False,
    }


def produce(source_report: Path) -> dict:
    final, nds, bearing = methods()
    census_method = load_pinned("end_grain_source_census", CENSUS, CENSUS_SHA)
    require(sha(source_report) == REGISTER_SHA, "frozen 52-axis output changed")
    census = census_method.build_census(source_report)
    axes, sources = census["axes"], census["states"]
    require(set(axes) == census_method.EXPECTED_AXES and len(sources) == 210,
            "ten-axis/210-state census differs")
    rows = []
    for source in sources:
        reference = conditional_reference(final, nds, bearing, axes[source["axis_id"]], source)
        require(reference["side_receiver"] == "base_header",
                "current transverse header receiver changed")
        require(source["joint_accepted"] is False,
                "source acceptance boundary changed")
        rows.append({**source, "conditional_end_grain_reference": reference})
    pins = final.pin_sources()
    for name, path, expected in (
        ("remaining_single_shear_producer", OLD, OLD_SHA),
        ("role_census", CENSUS, CENSUS_SHA), ("NDS_2024_chapter_12", PDF, PDF_SHA),
    ):
        pins[name] = {"path": path.relative_to(ROOT).as_posix(), "sha256": expected}
    return {
        "schema": "end_grain_single_shear_reference/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_CEG_ONLY_ARITHMETIC",
        "producer_sha256": sha(HERE / "produce.py"),
        "candidate": final.CANDIDATE,
        "geometry_revision_id": final.REVISION,
        "source_report_sha256": REGISTER_SHA,
        "source_sha256": pins,
        "source_census_pins": census["source_pins"],
        "reference_basis": {**final.REFERENCE_BASIS, "Ceg": CEG,
                            "quarter_inch_Fyb_qualified": False},
        "counts": {"axes": len(axes), "source_cases": 3, "increments_per_case": 7,
                   "reference_state_rows": len(rows)},
        "axis_geometry_and_grain": axes,
        "state_rows": rows,
        "claim_limits": {
            "joint_accepted": False, "mechanical_acceptance": False,
            "adopted_capacity": False, "fully_adjusted_design_ratio": False,
            "Ceg_applied_once": True, "other_adjustments_applied": False,
            "same_state_tie_added_to_lateral_demand": False,
            "source_null_reference_fields_changed": False,
            "six_case_envelope_established": False, "physical_work_released": False,
        },
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-report", type=Path, required=True)
    print(json.dumps(produce(parser.parse_args().source_report), indent=2, allow_nan=False))
