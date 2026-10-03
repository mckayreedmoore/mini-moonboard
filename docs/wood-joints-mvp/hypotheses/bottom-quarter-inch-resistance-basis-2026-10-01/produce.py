#!/usr/bin/env python3
"""Recompute conditional bottom-bolt lateral references; accept no joint."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
from fea.dowel_yield import single_shear

PACKETS = ROOT / "docs/wood-joints-mvp/hypotheses"
PREFIX = "bottom_outer/clip_horizontal_bottom_left_1/"
AXES = tuple(PREFIX + suffix for suffix in ("side_1", "side_2", "rail_1", "rail_2"))
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
N_PER_LBF = 4.4482216152605
REPORT_PINS = {
    "reference": "6551861db1112c91b87c5705bbceb3bb26f55f0d7e70029a74d828519425145e",
    "placement": "21c2eba56b80efa174cdb5ecdb206468a6b15882732c6edd548d2027063f58c3",
    "joint": "fcf393be26c433daf760a6afcf9fd6260d88f04f43a6234def960bbba4789029",
}
FILE_PINS = {
    "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/requirements.json":
        "15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100",
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf":
        "45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33",
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf":
        "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
    "docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf":
        "1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(vector: list[float]) -> float:
    return math.hypot(*vector)


def modes(lm: float, ls: float, fm: float, fs: float, theta: float, fyb: float) -> dict:
    """Six zero-gap modes for explicit smooth D=0.25 in, supplied Fyb in psi."""
    require(math.isfinite(theta) and 0 <= theta <= 90, "invalid grain angle")
    d = 0.25
    moment = fyb * d**3 / 6
    ktheta = 1 + 0.25 * theta / 90
    return single_shear(
        main_length_in=lm, side_length_in=ls,
        main_bearing_lb_in=fm * d, side_bearing_lb_in=fs * d,
        main_yield_moment_lb_in=moment, side_yield_moment_lb_in=moment,
        gap_in=0,
        reduction_terms={key: factor * ktheta for key, factor in
                         {"Im": 4, "Is": 4, "II": 3.6, "IIIm": 3.2,
                          "IIIs": 3.2, "IV": 3.2}.items()},
    )


def geometry_triggers(diameter_in: float) -> dict:
    require(math.isfinite(diameter_in) and diameter_in > 0, "invalid diameter")
    return {
        "sub_quarter_Cg_exception_applies": diameter_in < 0.25,
        "sub_quarter_Cdelta_exception_applies": diameter_in < 0.25,
        "Chapter_12_edge_row_rules_triggered": diameter_in >= 0.25,
    }


def checked_report(path: Path, kind: str) -> dict:
    require(sha(path) == REPORT_PINS[kind], f"changed frozen {kind} report")
    report = json.loads(path.read_text())
    require(report["candidate"] == "compact-floor-flush-wood-joints-development"
            and report["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "candidate/revision mismatch")
    return report


def state_key(row: dict) -> tuple:
    return row["case_id"], row["increment_index"], row["axis_id"]


def validate_rows(rows: list[dict]) -> None:
    expected = {(case, i, axis) for case in CASES for i in range(7) for axis in AXES}
    observed = set()
    for row in rows:
        key = state_key(row)
        require(key in expected and key not in observed, "foreign/duplicate bolt state")
        observed.add(key)
        require(row["load_factor"] == FACTORS[key[1]] and row["joint_accepted"] is False,
                "state amplitude or acceptance changed")
        f0, f1 = (row[f"actual_lateral_force_on_receiver_{i}_N"] for i in (0, 1))
        require(len(f0) == len(f1) == 3 and all(math.isfinite(x) for x in (*f0, *f1)),
                "invalid lateral vector")
        require(all(abs(a + b) < 1e-8 for a, b in zip(f0, f1, strict=True)),
                "signed receiver forces do not close")
        require(math.isclose(norm(f0), row["actual_lateral_resultant_N"], abs_tol=1e-8),
                "changed lateral resultant")
        require(math.isfinite(row["same_state_signed_outer_tie_N_once"]), "invalid tie")
        require(row["single_shear_reference_exclusion"] is None, "excluded source method")
    require(observed == expected, "incomplete 84-state census")


def produce(reference_path: Path, placement_path: Path, joint_path: Path) -> dict:
    for path, expected in FILE_PINS.items():
        require(sha(ROOT / path) == expected, f"changed pinned source: {path}")
    reference = checked_report(reference_path, "reference")
    placement = checked_report(placement_path, "placement")
    joint = checked_report(joint_path, "joint")
    require(placement["joint_source_sha256"] == REPORT_PINS["joint"]
            and joint["source_report_sha256"] == REPORT_PINS["reference"],
            "upstream join does not bind the frozen reports")
    expected_basis = {
        "diameter_in": 0.25, "bolt_bending_yield_psi": 45000.0,
        "wood_specific_gravity": 0.5, "Fe_parallel_psi": 5600.0,
        "Fe_perpendicular_psi": 4450.0, "interface_gap_in": 0.0,
        "shank": "smooth full-diameter quarter-inch scenario through each bearing interval",
    }
    require(all(reference["reference_basis"].get(k) == v for k, v in expected_basis.items()),
            "changed reference scenario")
    rows = [r for r in reference["state_rows"] if r["axis_id"] in AXES]
    validate_rows(rows)
    output_rows = []
    for row in rows:
        metadata = reference["axis_geometry_and_grain"][row["axis_id"]]
        require(metadata["single_shear_applicability_exclusion"] is None
                and all(abs(x) < 1e-8 for x in metadata["absolute_bolt_axis_grain_dots"]),
                "transverse-grain Ceg/reference scope changed")
        lengths = {r["receiver_id"]: r["modeled_bearing_length_in"] for r in metadata["receivers"]}
        results = []
        for assignment in row["single_shear_reference_assignments"]["scenarios"]:
            lm, ls = (lengths[assignment[k]] for k in ("main_receiver", "side_receiver"))
            fm, fs = assignment["main_Fe_psi"], assignment["side_Fe_psi"]
            theta = assignment["max_angle_theta_deg"]
            for fyb in (45000.0, 106000.0):
                result = modes(lm, ls, fm, fs, theta, fyb)
                if fyb == 45000:
                    require(all(math.isclose(result["reference_values_lbf"][mode],
                            assignment["unadjusted_reference_modes_lbf"][mode], rel_tol=1e-10)
                            for mode in MODES), "45-ksi source replay mismatch")
                ref_n = result["reference_lateral_lbf"] * N_PER_LBF
                results.append({
                    "assignment": assignment["assignment"], "Fyb_scenario_psi": fyb,
                    "Fyb_adopted": False, **result,
                    "reference_lateral_N": ref_n,
                    "lateral_demand_to_unadjusted_reference": row["actual_lateral_resultant_N"] / ref_n,
                    "required_Cg_times_Cdelta_under_declared_unity_service_scenario":
                        row["actual_lateral_resultant_N"] / ref_n,
                    "Cg": None, "Cdelta": None, "adjusted_reference_N": None,
                })
        output_rows.append({"unchanged_source_bolt_state": row, "conditional_references": results})
    critical = next(row for row in output_rows if state_key(row["unchanged_source_bolt_state"])
                    == ("a1-rear", 6, PREFIX + "side_1"))
    source = critical["unchanged_source_bolt_state"]
    a = source["single_shear_reference_assignments"]["scenarios"][0]
    # An inverse mode-IV budget is valid only after all six modes are checked there.
    ratio45 = source["actual_lateral_resultant_N"] / critical["conditional_references"][0]["reference_lateral_N"]
    fyb_needed = 45000 * ratio45**2
    geometry = reference["axis_geometry_and_grain"][source["axis_id"]]
    lengths = [r["modeled_bearing_length_in"] for r in geometry["receivers"]]
    threshold = modes(*lengths, a["main_Fe_psi"], a["side_Fe_psi"], a["max_angle_theta_deg"], fyb_needed)
    require(threshold["governing_mode"] == "IV" and math.isclose(
        threshold["reference_lateral_lbf"] * N_PER_LBF, source["actual_lateral_resultant_N"], rel_tol=1e-10),
        "inverse mode-IV threshold is outside its valid mode regime")
    requirements = json.loads((PACKETS / "hardware-material-specification-2026-09-30/requirements.json").read_text())
    hardware = [r for r in requirements["axis_requirements"] if r["axis_id"] in AXES]
    require({r["axis_id"] for r in hardware} == set(AXES), "hardware axis census mismatch")
    return {
        "schema": "bottom-quarter-inch-resistance-basis/v1",
        "status": "CONDITIONAL_ARITHMETIC_AND_APPLICABILITY_ONLY",
        "producer_sha256": sha(HERE / "produce.py"),
        "candidate": reference["candidate"], "geometry_revision_id": reference["geometry_revision_id"],
        "source_report_sha256": REPORT_PINS, "method_and_material_pins": FILE_PINS,
        "service_scenario": {"ASD_duration": "normal", "CD": 1.0,
            "fabrication_and_service_moisture": "seasoned dry, both <=19%", "CM": 1.0,
            "sustained_temperature": "<=100 F", "Ct": 1.0,
            "wood_treatment": "untreated; no fire-retardant treatment",
            "Ceg": 1.0, "Ceg_basis": "modeled bolt axes transverse to both proposed grains",
            "observed_or_adopted": False},
        "geometry_triggers": geometry_triggers(0.25),
        "critical_unity_factor_mode_IV_Fyb_budget_psi": fyb_needed,
        "critical_Fyb_budget_is_material_requirement_or_acceptance": False,
        "bolt_state_rows": output_rows,
        "unchanged_axis_geometry_and_grain": {axis: reference["axis_geometry_and_grain"][axis] for axis in AXES},
        "unchanged_member_bolt_states": placement["member_bolt_states"],
        "unchanged_interface_wrenches": placement["member_interface_states"],
        "unchanged_cleat_complete_joint_states": joint["joint_states"],
        "unchanged_contact_cell_states": joint["contact_cell_states"],
        "unchanged_placements": placement["placements"],
        "unchanged_pair_geometry": placement["pair_geometry"],
        "unchanged_hardware_requirements": hardware,
        "joint_accepted": False, "adopted_capacity": False,
        "limits": ["No source actions reduced or allocated from a favorable group resultant",
            "45 ksi hypothesis and 106 ksi nonmandatory Appendix estimate are both unadopted",
            "No numeric group/geometry adjustment or adjusted joint resistance",
            "Axial bearing, washer metal/contact, bolt bending/combined, splitting and local stresses stay open",
            "Three rear cases only; no native/CAD or physical operation performed"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--placement-report", type=Path, required=True)
    parser.add_argument("--joint-report", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(produce(args.reference_report, args.placement_report, args.joint_report),
                     indent=2, allow_nan=False))
