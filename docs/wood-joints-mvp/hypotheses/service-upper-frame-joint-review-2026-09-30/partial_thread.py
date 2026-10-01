#!/usr/bin/env python3
"""Compare declared partial-thread scenarios with existing upper bolt actions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)
from mini_moonboard.wood_joint_bolt_resistance import nds_effective_bolt_diameter_in

LBF_N = 4.4482216152605
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def selector(lengths, threaded):
    return nds_effective_bolt_diameter_in(
        full_body_diameter_in=0.25,
        thread_root_diameter_in=0.189,
        threaded_full_body_fastener=True,
        main_bearing_length_in=lengths[0] / 25.4,
        side_bearing_length_in=lengths[1] / 25.4,
        main_thread_bearing_length_in=threaded[0] / 25.4,
        side_thread_bearing_length_in=threaded[1] / 25.4,
    )


def threshold_checks():
    fixtures = []
    for lengths in ([88.9, 38.1], [38.1, 88.9], [88.9, 88.9]):
        start = 2.032
        intervals = []
        for length in lengths:
            intervals.append((start, start + length))
            start += length
        boundary = max(end - length / 4 for (_, end), length in zip(intervals, lengths))
        outcomes = {}
        for name, delta in (("below", -1e-3), ("above", 1e-3)):
            s = boundary + delta
            threads = [max(0, end - max(begin, s)) for begin, end in intervals]
            outcomes[name] = selector(lengths, threads)["diameter_case"]
        assert outcomes == {"below": "thread_root_Dr", "above": "full_body_D"}
        fixtures.append(
            {
                "head_to_nut_lengths_mm": lengths,
                "required_thread_runout_start_mm": boundary,
                "one_micron_boundary_checks": outcomes,
            }
        )
    return fixtures


def produce():
    freeze = json.loads((HERE / "thread-scenario-freeze.json").read_text())
    assert freeze["full_body_diameter_in"] == 0.25
    assert freeze["thread_root_diameter_in_sensitivity"] == 0.189
    assert freeze["Fyb_psi_commentary_estimate"] == 106000
    assert freeze["head_washer_thickness_mm"] == 2.032
    for pin in freeze["sources"]:
        if sha(ROOT / pin["path"]) != pin["sha256"]:
            raise RuntimeError("Frozen source changed: " + pin["path"])
    output = {
        "schema": "upper-partial-thread-scenario/v1",
        "status": "DECLARED_THREAD_INTERVAL_COMPONENT_COMPARISON_ONLY",
        "producer_sha256": sha(Path(__file__)),
        "freeze_sha256": sha(HERE / "thread-scenario-freeze.json"),
        "declared_scenarios": freeze["declared_scenarios"],
        "thread_definition": "S is the earliest potentially bearing thread or runout. Entire body before S is declared smooth; every point after S through the far wood face is conservatively counted as threaded. This is not a first full-form coordinate or an Lb/Lg inference.",
        "declared_head_washer_thickness_mm": freeze["head_washer_thickness_mm"],
        "conditional_properties": {
            "nominal_NDS_D_in": 0.25,
            "typical_Dr_sensitivity_in": 0.189,
            "Fyb_psi": 106000,
            "Fyb_basis": "Unadopted Grade 5 Commentary estimate, not a test-derived or guaranteed bending property.",
        },
        "known_answer_threshold_checks": threshold_checks(),
        "axes": {},
        "rows": [],
        "sampled_maxima_by_block": {},
        "complete_joint_accepted": False,
        "six_case_envelope_established": False,
        "reviewed_geometry_changed": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
        "limits": [
            "Same three authenticated source response scenarios only; no physical bolt distribution bound.",
            "Hypothetical partial-thread interval and full-body fastener, not selected or delivered hardware.",
            "Hypothetical contacting, two-member, side-grain single shear; loaded contact applicability remains open.",
            "No end-use adjustments, geometry factor, group summation, splitting or axial/bending interaction applied.",
            "NDS effective diameter is separate from the steel tensile or shear area; direct steel checks are unchanged.",
            "Nut engagement, runout profile and washer transfer are separate checks.",
        ],
    }
    for relative in freeze["action_reports"]:
        report = json.loads((ROOT / relative).read_text())
        assert report["counts"]["physical_bolts"] == 16
        assert report["complete_joint_resistance_established"] is False
        assert report["six_case_envelope_established"] is False
        for axis_id, geometry in report["geometry_by_axis"].items():
            assert axis_id not in output["axes"]
            grip = geometry["hardware_axis_record"]["modeled_wood_grip_mm"]
            scenario_id = next(
                name
                for name, scenario in freeze["declared_scenarios"].items()
                if math.isclose(grip, scenario["wood_grip_mm"], abs_tol=1e-6)
            )
            s = freeze["declared_scenarios"][scenario_id][
                "earliest_potentially_bearing_thread_or_runout_start_underhead_mm"
            ]
            axis = geometry["head_to_nut_axis_xyz"]
            axis = [x / math.sqrt(dot(axis, axis)) for x in axis]
            head_wood_face = geometry["outer_seat_endpoints_xyz_mm"][0]
            members = {}
            for role, member in geometry["members"].items():
                length = member["bearing_length_mm"]
                midpoint = freeze["head_washer_thickness_mm"] + dot(
                    [
                        member["bolt_line_mid_bearing_xyz_mm"][i] - head_wood_face[i]
                        for i in range(3)
                    ],
                    axis,
                )
                begin, end = midpoint - length / 2, midpoint + length / 2
                threads = max(0, end - max(begin, s))
                assert abs(dot(axis, member["conditional_grain_xyz"])) < 1e-8
                members[role] = {
                    "member": member["member"],
                    "bearing_length_mm": length,
                    "underhead_wood_interval_mm": [begin, end],
                    "minimum_runout_start_for_quarter_rule_mm": end - length / 4,
                    "declared_thread_bearing_mm": threads,
                    "declared_thread_fraction": threads / length,
                }
            ordered = sorted(
                members.values(), key=lambda row: row["underhead_wood_interval_mm"][0]
            )
            assert abs(ordered[0]["underhead_wood_interval_mm"][0] - 2.032) < 1e-6
            assert (
                abs(
                    ordered[0]["underhead_wood_interval_mm"][1]
                    - ordered[1]["underhead_wood_interval_mm"][0]
                )
                < 1e-6
            )
            assert (
                abs(ordered[1]["underhead_wood_interval_mm"][1] - (2.032 + grip)) < 1e-6
            )
            lengths = [members[role]["bearing_length_mm"] for role in ("block", "host")]
            threads = [
                members[role]["declared_thread_bearing_mm"]
                for role in ("block", "host")
            ]
            selected = selector(lengths, threads)
            assert selected["diameter_case"] == "full_body_D"
            output["axes"][axis_id] = {
                "source_report": relative,
                "scenario_id": scenario_id,
                "members": members,
                "diameter_selector": selected,
                "thread_start_margin_over_required_mm": s
                - max(
                    m["minimum_runout_start_for_quarter_rule_mm"]
                    for m in members.values()
                ),
                "no_received_part_conformance_inferred": True,
            }
        for row in report["bolt_actions"]:
            axis_record = output["axes"][row["axis_id"]]
            members = axis_record["members"]
            angles = [
                row["member_directions"][role]["unsigned_load_to_grain_degrees"]
                for role in ("block", "host")
            ]
            factor = 1 + 0.25 * max(angles) / 90
            reduction = dict(
                zip(
                    MODES,
                    (
                        4 * factor,
                        4 * factor,
                        3.6 * factor,
                        3.2 * factor,
                        3.2 * factor,
                        3.2 * factor,
                    ),
                )
            )
            reference = wood_wood_single_shear_reference(
                main_bearing_length_in=members["block"]["bearing_length_mm"] / 25.4,
                side_bearing_length_in=members["host"]["bearing_length_mm"] / 25.4,
                main_load_to_grain_degrees=angles[0],
                side_load_to_grain_degrees=angles[1],
                main_bolt_axis_parallel_to_grain=False,
                side_bolt_axis_parallel_to_grain=False,
                bolt_full_body_diameter_in=0.25,
                bolt_thread_root_diameter_in=0.189,
                main_thread_bearing_length_in=members["block"][
                    "declared_thread_bearing_mm"
                ]
                / 25.4,
                side_thread_bearing_length_in=members["host"][
                    "declared_thread_bearing_mm"
                ]
                / 25.4,
                bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
                    bending_yield_strength_psi=106000, effective_diameter_in=0.25
                ),
                gap_in=0,
                reduction_terms=reduction,
            )
            assert reference["effective_bearing_diameter_in"] == 0.25
            reference_n = reference["reference_lateral_lbf"] * LBF_N
            output["rows"].append(
                {
                    "source_report": relative,
                    "case": row["case"],
                    "load_factor": row["load_factor"],
                    "block": row["block"],
                    "axis_id": row["axis_id"],
                    "lateral_demand_n": row["lateral_magnitude_n"],
                    "conditional_full_D_reference_n": reference_n,
                    "conditional_full_D_demand_to_unadjusted_reference": row[
                        "lateral_magnitude_n"
                    ]
                    / reference_n,
                    "full_D_governing_mode": reference["governing_mode"],
                    "full_D_six_reference_modes_n": {
                        k: v * LBF_N
                        for k, v in reference["reference_values_lbf"].items()
                    },
                    "nominal_Fe_root_yield_demand_to_unadjusted_reference": row[
                        "wood_lateral_references"
                    ]["nominal_D_bearing_root_yield"]["demand_to_unadjusted_reference"],
                    "root_Fe_root_yield_demand_to_unadjusted_reference": row[
                        "wood_lateral_references"
                    ]["root_D_bearing_root_yield_sensitivity"][
                        "demand_to_unadjusted_reference"
                    ],
                }
            )
    assert len(output["axes"]) == 32 and len(output["rows"]) == 672
    for block in sorted({r["block"] for r in output["rows"]}):
        peak = max(
            (r for r in output["rows"] if r["block"] == block),
            key=lambda r: r["conditional_full_D_demand_to_unadjusted_reference"],
        )
        output["sampled_maxima_by_block"][block] = {
            k: peak[k]
            for k in (
                "case",
                "load_factor",
                "axis_id",
                "lateral_demand_n",
                "conditional_full_D_reference_n",
                "conditional_full_D_demand_to_unadjusted_reference",
                "full_D_governing_mode",
                "nominal_Fe_root_yield_demand_to_unadjusted_reference",
                "root_Fe_root_yield_demand_to_unadjusted_reference",
            )
        }
    output["counts"] = {
        "upper_blocks": 8,
        "physical_bolt_axes": 32,
        "component_records": 672,
        "cases": 3,
        "increments_per_case": 7,
    }
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    report = produce()
    stream = io.StringIO(newline="")
    fields = [
        "case",
        "load_factor",
        "block",
        "axis_id",
        "lateral_demand_n",
        "conditional_full_D_reference_n",
        "conditional_full_D_demand_to_unadjusted_reference",
        "full_D_governing_mode",
        "nominal_Fe_root_yield_demand_to_unadjusted_reference",
        "root_Fe_root_yield_demand_to_unadjusted_reference",
    ]
    writer = csv.DictWriter(stream, fields, lineterminator="\n")
    writer.writeheader()
    for row in report["rows"]:
        writer.writerow({k: row[k] for k in fields})
    for name, text in {
        "partial-thread-comparison.json": json.dumps(report, indent=2, sort_keys=True)
        + "\n",
        "partial-thread-comparison.csv": stream.getvalue(),
    }.items():
        if args.verify:
            assert (HERE / name).read_text() == text
        else:
            (HERE / name).write_text(text)
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "sampled_maxima_by_block": report["sampled_maxima_by_block"],
            },
            indent=2,
        )
    )
