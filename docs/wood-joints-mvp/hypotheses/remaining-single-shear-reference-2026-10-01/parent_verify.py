#!/usr/bin/env python3
"""Cross-check a local census with the independent NDS single-shear equations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PDF = ROOT / (
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/"
    "materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-"
    "Dowel-type-fasteners.pdf"
)
PDF_SHA = "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a"
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
CASES = ("a1-rear", "a12-rear", "k12-rear")
N_PER_LBF = 4.4482216152605
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def norm(vector: list[float]) -> float:
    return math.sqrt(math.fsum(x * x for x in vector))


def angle(force: list[float], grain: list[float]) -> float:
    cosine = abs(math.fsum(f * g for f, g in zip(force, grain, strict=True)))
    cosine /= norm(force) * norm(grain)
    return math.degrees(math.acos(min(1.0, max(0.0, cosine))))


def bearing(theta: float) -> float:
    radians = math.radians(theta)
    return 5600.0 * 4450.0 / (
        5600.0 * math.sin(radians) ** 2 + 4450.0 * math.cos(radians) ** 2
    )


def nds_modes(lm: float, ls: float, fm: float, fs: float, theta: float) -> dict[str, float]:
    """NDS-2024 Table 12.3.1A single-shear column and Table 12.3.1B.

    Independent closed forms for the packet's zero-gap, smooth 0.25-inch,
    45,000-psi Fyb scenario. No imports from either production helper.
    """
    d, fyb = 0.25, 45000.0
    re, rt = fm / fs, lm / ls
    k_theta = 1.0 + 0.25 * theta / 90.0
    k1 = (
        math.sqrt(re + 2 * re**2 * (1 + rt + rt**2) + rt**2 * re**3)
        - re * (1 + rt)
    ) / (1 + re)
    k2 = -1 + math.sqrt(
        2 * (1 + re) + 2 * fyb * (1 + 2 * re) * d**2 / (3 * fm * lm**2)
    )
    k3 = -1 + math.sqrt(
        2 * (1 + re) / re + 2 * fyb * (2 + re) * d**2 / (3 * fm * ls**2)
    )
    return {
        "Im": d * lm * fm / (4 * k_theta),
        "Is": d * ls * fs / (4 * k_theta),
        "II": k1 * d * ls * fs / (3.6 * k_theta),
        "IIIm": k2 * d * lm * fm / ((1 + 2 * re) * 3.2 * k_theta),
        "IIIs": k3 * d * ls * fm / ((2 + re) * 3.2 * k_theta),
        "IV": d**2 * math.sqrt(2 * fm * fyb / (3 * (1 + re))) / (3.2 * k_theta),
    }


def verify(path: Path) -> dict:
    report = json.loads(path.read_text())
    require(sha(PDF) == PDF_SHA, "NDS oracle source changed")
    require(report["producer_sha256"] == sha(HERE / "produce.py"), "producer changed")
    require(report["status"] == "PASS_SOURCE_BOUND_UNADJUSTED_REFERENCE_ARITHMETIC_ONLY",
            "wrong packet status")
    require(report["claim_limits"]["joint_accepted"] is False
            and report["claim_limits"]["adopted_capacity"] is False,
            "acceptance boundary changed")
    basis = report["reference_basis"]
    require(basis["diameter_in"] == 0.25 and basis["bolt_bending_yield_psi"] == 45000
            and basis["wood_specific_gravity"] == 0.5 and basis["interface_gap_in"] == 0,
            "oracle scenario changed")
    for pin in report["source_sha256"].values():
        require(sha(ROOT / pin["path"]) == pin["sha256"], "method or grain pin changed")
    for files in report["source_acceptance"]["source_cases"].values():
        for pin in files.values():
            require(sha(ROOT / pin["path"]) == pin["sha256"], "frozen case file changed")

    axes = report["axis_geometry_and_grain"]
    require(len(axes) == 52, "wrong axis census")
    expected = {(case, i, axis_id) for case in CASES for i in range(7) for axis_id in axes}
    observed = set()
    maximum_relative_error = 0.0
    eligible, excluded, comparisons = 0, 0, 0
    peaks = {}
    for row in report["state_rows"]:
        identity = (row["case_id"], row["increment_index"], row["axis_id"])
        require(identity in expected and identity not in observed, "duplicate or foreign state")
        observed.add(identity)
        require(row["load_factor"] == FACTORS[identity[1]] and row["joint_accepted"] is False,
                "load factor or state acceptance changed")
        metadata = axes[identity[2]]
        forces = [row["actual_lateral_force_on_receiver_0_N"],
                  row["actual_lateral_force_on_receiver_1_N"]]
        require(all(abs(a + b) < 1e-8 for a, b in zip(*forces, strict=True)),
                "receiver action pair does not close")
        demand = norm(forces[0])
        require(math.isclose(demand, row["actual_lateral_resultant_N"], abs_tol=1e-8),
                "resultant changed")
        if metadata["single_shear_applicability_exclusion"]:
            excluded += 1
            require(row["single_shear_reference_exclusion"]
                    == metadata["single_shear_applicability_exclusion"]
                    and row["single_shear_reference_assignments"] is None
                    and row["demand_to_reference_ratios_unadjusted_only"] is None,
                    "excluded method emitted a reference or ratio")
            continue
        eligible += 1
        receivers = metadata["receivers"]
        grains = [r["source_descriptor_grain_axis_unit_global_xyz"] for r in receivers]
        require(all(abs(math.fsum(a * g for a, g in zip(
            metadata["modeled_bolt_axis_unit_global_xyz"], grain, strict=True
        ))) <= 1e-8 for grain in grains), "reference applied to non-transverse axis")
        theta = [angle(force, grain) for force, grain in zip(forces, grains, strict=True)]
        lengths = [(r["modeled_interval_from_underhead_mm"][1]
                    - r["modeled_interval_from_underhead_mm"][0]) / 25.4 for r in receivers]
        scenarios = row["single_shear_reference_assignments"]["scenarios"]
        require(len(scenarios) == 2, "missing receiver-role assignment")
        for scenario, (m, s) in zip(scenarios, ((0, 1), (1, 0)), strict=True):
            require(scenario["main_receiver"] == receivers[m]["receiver_id"]
                    and scenario["side_receiver"] == receivers[s]["receiver_id"],
                    "receiver roles changed")
            values = nds_modes(lengths[m], lengths[s], bearing(theta[m]), bearing(theta[s]), max(theta))
            for mode in MODES:
                value = scenario["unadjusted_reference_modes_lbf"][mode]
                error = abs(value - values[mode]) / values[mode]
                maximum_relative_error = max(maximum_relative_error, error)
                require(error < 1e-10, f"NDS closed-form mismatch: {identity}/{mode}")
                comparisons += 1
            reference = min(values.values()) * N_PER_LBF
            require(scenario["governing_mode"] in MODES
                    and math.isclose(values[scenario["governing_mode"]] * N_PER_LBF,
                                     reference, rel_tol=1e-10), "governing mode changed")
            ratio = demand / reference
            stored_ratio = row["demand_to_reference_ratios_unadjusted_only"][scenario["assignment"]]
            require(math.isclose(reference, scenario["governing_unadjusted_reference_N"], rel_tol=1e-10)
                    and math.isclose(ratio, stored_ratio, rel_tol=1e-10),
                    "governing value or raw ratio changed")
            if identity[2] not in peaks or ratio > peaks[identity[2]]["ratio"]:
                peaks[identity[2]] = {"axis_id": identity[2], "case_id": identity[0],
                                      "load_factor": row["load_factor"], "ratio": ratio,
                                      "lateral_N": demand, "reference_N": reference,
                                      "mode": scenario["governing_mode"]}
    require(observed == expected and eligible == 882 and excluded == 210,
            "source-state or applicability census changed")
    return {
        "status": "PASS_INDEPENDENT_NDS_CLOSED_FORM_REFERENCE_CROSSCHECK_ONLY",
        "report_sha256": sha(path), "producer_sha256": report["producer_sha256"],
        "NDS_source_sha256": PDF_SHA, "states": len(observed),
        "eligible_states": eligible, "excluded_null_states": excluded,
        "independent_mode_comparisons": comparisons,
        "maximum_relative_mode_difference": maximum_relative_error,
        "axes_with_raw_scenario_ratio_above_one": sum(p["ratio"] > 1 for p in peaks.values()),
        "largest_raw_scenario_comparisons": sorted(peaks.values(), key=lambda p: p["ratio"], reverse=True)[:8],
        "joint_accepted": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    print(json.dumps(verify(parser.parse_args().report), indent=2, allow_nan=False))
