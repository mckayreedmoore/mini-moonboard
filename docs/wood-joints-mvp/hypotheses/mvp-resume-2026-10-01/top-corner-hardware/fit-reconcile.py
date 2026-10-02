#!/usr/bin/env python3
"""Reconcile conditional top-corner fastener stacks and existing access envelopes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RUN = REPO / "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01"
INPUTS_PATH = HERE / "hardware-inputs.json"
PROPOSAL_PATH = RUN / "top-corner-correction/proposal.json"
COMPONENT_REPORT_PATH = RUN / "top-corner-component-checks.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mm(value: dict, bound: str) -> float:
    return float(value["mm"][bound])


def inches(value: dict, bound: str) -> float:
    return float(value["in"][bound])


def source_hash_check(inputs: dict) -> dict[str, str]:
    expected = {entry["path"]: entry["sha256"] for entry in inputs["source_inputs"]}
    paths = {
        "correction_note": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction.md",
        "correction_proposal": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/proposal.json",
        "contact_geometry": "docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-contact-geometry.json",
    }
    result = {}
    for name, relative in paths.items():
        actual = sha256(REPO / relative)
        recorded = expected[relative]
        if actual != recorded:
            raise SystemExit(f"Source hash changed for {relative}: {actual} != {recorded}")
        result[name] = actual
    return result


def family_fit(
    inputs: dict,
    family_name: str,
    bolt_id: str,
    nut_id: str,
    washer_id: str,
    proposal_approaches: list[dict],
) -> dict:
    family = inputs["axis_families"][family_name]
    bolt = inputs["catalog_parts"][bolt_id]
    nut = inputs["catalog_parts"][nut_id]
    washer = inputs["catalog_parts"][washer_id]
    nut_fit = family["nut_and_tip_fit"]

    grip = float(family["wood_grip_mm"])
    washer_min = mm(washer["thickness"], "minimum")
    washer_max = mm(washer["thickness"], "maximum")
    nut_min = mm(nut["height"], "minimum")
    nut_max = mm(nut["height"], "maximum")
    threads_per_inch = int(bolt["thread"]["tpi"])
    three_pitches = 3 * 25.4 / threads_per_inch
    maximum_stack = grip + 2 * washer_max + nut_max
    minimum_stack = grip + 2 * washer_min + nut_min

    approaches = []
    axis_ids = {axis["axis_id"] for axis in family["axes"]}
    for record in proposal_approaches:
        if record["axis_id"] not in axis_ids:
            continue
        approaches.append(
            {
                "axis_id": record["axis_id"],
                "end": record["end"],
                "tool_diameter_mm": record["tool_diameter_mm"],
                "tool_length_mm": record["tool_length_mm"],
                "outward_axis_xyz": record["outward_axis_xyz"],
                "proposed_wood_hits_mm3": sum(
                    record["proposed_wood_hits_mm3"].values()
                ),
                "other_candidate_shaft_hits_mm3": sum(
                    record["other_candidate_shaft_hits_mm3"].values()
                ),
            }
        )

    head_af = bolt.get("head", {}).get("across_flats")
    nut_af = nut.get("across_flats")
    length_min = bolt.get("length_under_head", {}).get("mm", {}).get("minimum")

    return {
        "bolt_part_id": bolt_id,
        "nut_part_id": nut_id,
        "washer_part_id": washer_id,
        "axis_ids": sorted(axis_ids),
        "bolts": family["bolt_quantity"],
        "nuts": family["nut_quantity"],
        "washers": family["washer_quantity"],
        "members_head_to_nut": family["wood_receiver_order_head_to_nut"],
        "member_bearing_lengths_mm": family["wood_bearing_lengths_head_to_nut_mm"],
        "wood_grip_mm": grip,
        "washer_thickness_range_each_mm": [washer_min, washer_max],
        "nut_height_range_mm": [nut_min, nut_max],
        "underhead_to_nut_outer_face_mm": [minimum_stack, maximum_stack],
        "threads_per_inch": threads_per_inch,
        "declared_three_pitch_allowance_mm": three_pitches,
        "underhead_length_needed_with_three_pitch_allowance_mm": maximum_stack
        + three_pitches,
        "catalog_underhead_length_minimum_mm": length_min,
        "conditional_b1821_minimum_tip_mm": nut_fit["conditional_minimum_tip_mm"],
        "conditional_margin_at_b1821_minimum_mm": nut_fit[
            "physical_tip_margin_at_length_minimum_mm"
        ],
        "full_form_thread_required_interval_from_underhead_mm": nut_fit[
            "full_form_thread_required_envelope_mm"
        ],
        "delivered_full_form_thread_interval_mm": nut_fit[
            "delivered_full_form_thread_interval_mm"
        ],
        "minimum_body_end_LB_for_full_body_scenario_mm": family[
            "minimum_LB_for_quarter_bearing_mm"
        ],
        "conditional_body_end_profiles": [
            {
                "scenario": item["scenario"],
                "LB_mm": item["LB_mm"],
                "threaded_bearing_by_member": [
                    {
                        "member_role": segment["member_role"],
                        "threaded_length_mm": segment["threaded_length_mm"],
                        "threaded_fraction": segment["threaded_fraction"],
                    }
                    for segment in item["threaded_bearing_at_maximum_head_washer"]
                ],
            }
            for item in family["conditional_profiles"]
        ],
        "bolt_head_across_flats_in": (
            [inches(head_af, "minimum"), inches(head_af, "maximum")]
            if head_af
            else None
        ),
        "nut_across_flats_in": [inches(nut_af, "minimum"), inches(nut_af, "maximum")],
        "washer_inside_diameter_mm": [
            mm(washer["inside_diameter"], "minimum"),
            mm(washer["inside_diameter"], "maximum"),
        ],
        "washer_outside_diameter_mm": [
            mm(washer["outside_diameter"], "minimum"),
            mm(washer["outside_diameter"], "maximum"),
        ],
        "washer_material": washer["catalog_material"],
        "washer_numeric_Fy_psi": washer["numeric_Fy_psi"],
        "approach_count": len(approaches),
        "straight_approaches": approaches,
    }


def procurement_summary(inputs: dict, option_id: str) -> dict:
    option = inputs["procurement"][option_id]
    total = round(sum(line["extended_USD"] for line in option["lines"]), 2)
    if total != option["subtotal_USD"]:
        raise SystemExit(f"Procurement subtotal mismatch for {option_id}: {total}")
    return {
        "description": option["description"],
        "observed_on": option["observed_on"],
        "status": option["status"],
        "lines": option["lines"],
        "reconciled_subtotal_USD": total,
        "shipping_tax_included": option["shipping_tax_included"],
        "hardware_fit_and_strength_accepted": option[
            "hardware_fit_and_strength_accepted"
        ],
    }


def component_report_summary() -> dict:
    report = COMPONENT_REPORT_PATH.read_text()

    def row_values(label: str) -> list[str]:
        prefix = f"| {label} |"
        line = next(line for line in report.splitlines() if line.startswith(prefix))
        return [cell.strip() for cell in line.split("|")[1:-1]]

    def row_pair(label: str, suffix: str = "") -> list[float]:
        return [
            float(value.removesuffix(suffix).strip())
            for value in row_values(label)[1:3]
        ]

    normalized = " ".join(report.split())
    clearance = re.search(
        r"The four side bolts have ([0-9.]+) mm relative clearance; "
        r"the four rail bolts have ([0-9.]+) mm",
        normalized,
    )
    washer = re.search(
        r"washer model requires up to ([0-9.]+) MPa bending stress at the "
        r"catalog minimum thickness, using declared ([0-9.]+) mm rail and "
        r"([0-9.]+) mm side head/nut bearing circles",
        normalized,
    )
    zero_gap = re.search(
        r"The preserved zero-gap right-corner individual reference is ([0-9.]+)",
        normalized,
    )
    if not (clearance and washer and zero_gap):
        raise SystemExit("Could not parse current top-corner component report")

    return {
        "source_path": str(COMPONENT_REPORT_PATH.relative_to(REPO)),
        "source_sha256": sha256(COMPONENT_REPORT_PATH),
        "conditional_material": "Grade 5 tensile-yield input Fyb = 92 ksi",
        "modeled_relative_clearance_mm": {
            "side_bolt": float(clearance.group(1)),
            "rail_bolt": float(clearance.group(2)),
        },
        "lateral_over_adjusted_conditional_reference_ratio": row_pair(
            "Lateral / adjusted conditional individual reference"
        ),
        "maximum_local_rail_side_movement_mm": row_pair(
            "Maximum local rail/side movement", "mm"
        ),
        "maximum_local_rail_side_rotation_degrees": row_pair(
            "Maximum local rail/side rotation", "°"
        ),
        "preserved_zero_gap_right_corner_individual_reference_ratio": float(
            zero_gap.group(1).rstrip(".")
        ),
        "washer_radial_strip_peak_stress_MPa": float(washer.group(1)),
        "washer_peak_location": "rail_1",
        "washer_catalog_minimum_thickness_basis": True,
        "assumed_head_nut_bearing_circle_diameters_mm": {
            "rail": float(washer.group(2)),
            "side": float(washer.group(3)),
        },
        "actual_head_nut_bearing_footprints_known": False,
        "washer_metal_resistance_basis_known": False,
        "bolt_grade_transferred_to_washer": False,
        "hardware_selected": False,
    }


def main(destination: Path) -> None:
    if destination.exists():
        raise SystemExit("Refusing to overwrite existing fit evidence")
    inputs = json.loads(INPUTS_PATH.read_text())
    proposal = json.loads(PROPOSAL_PATH.read_text())
    source_hashes = source_hash_check(inputs)

    side_grade5 = family_fit(
        inputs,
        "side",
        "side_bolt_grade5_kljack",
        "side_nut_grade5",
        "side_washer_uss",
        proposal["straight_tool_approach_scenarios"],
    )
    side_grade8 = family_fit(
        inputs,
        "side",
        "side_bolt_grade8",
        "side_nut_grade8",
        "side_washer_uss",
        proposal["straight_tool_approach_scenarios"],
    )
    rail = family_fit(
        inputs,
        "rail",
        "rail_bolt_grade5_motion",
        "rail_nut_grade5",
        "rail_washer_uss",
        proposal["straight_tool_approach_scenarios"],
    )

    approaches = side_grade8["straight_approaches"] + rail["straight_approaches"]
    output = {
        "schema": "top_corner_conditional_assembly_fit/v1",
        "generated_on": "2026-10-01",
        "status": "CONDITIONAL_FIT_RECONCILIATION_NO_HARDWARE_SELECTED",
        "input_hardware_file": "hardware-inputs.json",
        "parent_proposal_file": "../top-corner-correction/proposal.json",
        "source_sha256": source_hashes,
        "approach_geometry_source_scope": proposal["straight_tool_approach_scenarios"][
            0
        ]["scope"],
        "proposal_counts": proposal["counts"],
        "parent_both_corner_component_report": component_report_summary(),
        "side_grade5": side_grade5,
        "side_grade8": side_grade8,
        "rail_grade5_motion": rail,
        "all_eight_bolts_have_two_straight_approach_records": len(approaches) == 16,
        "all_approach_enclosures_clear_proposed_wood": all(
            item["proposed_wood_hits_mm3"] == 0 for item in approaches
        ),
        "all_approach_enclosures_clear_other_candidate_shafts": all(
            item["other_candidate_shaft_hits_mm3"] == 0 for item in approaches
        ),
        "catalog_contact_geometry_not_transferred": inputs[
            "contact_model_dimensions_not_transferred"
        ],
        "grade5_side_motion_rail_procurement": procurement_summary(
            inputs, "grade5_side_motion_rail"
        ),
        "grade8_side_motion_rail_procurement": procurement_summary(
            inputs, "grade8_side_motion_rail"
        ),
        "grade8_side_lawson_rail_procurement": inputs["procurement"][
            "grade8_side_lawson_rail"
        ],
        "limits": [
            "Catalog bounds and conditional B18.2.1 profiles do not establish delivered bolt LB or full-form thread interval.",
            "A 25.4 mm diameter by 50 mm straight approach is not a wrench turning sweep, tool-to-tool fit, or full bolt insertion/withdrawal path.",
            "Washer metal strength and actual supported wood contact are not accepted; bolt-grade properties do not apply to washers.",
            "Procurement subtotals are observed listing estimates, not live checkout quotes; no hardware is selected.",
        ],
    }
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(f"Wrote {destination}")
    print("Stack totals (max underhead to nut outer face):")
    print(f"  side: {side_grade8['underhead_to_nut_outer_face_mm'][1]:.4f} mm")
    print(f"  rail: {rail['underhead_to_nut_outer_face_mm'][1]:.4f} mm")
    print(f"Straight approaches: {len(approaches)}; all reported clear of proposal wood and candidate shafts.")
    print("Listing subtotals:")
    print(
        "  Grade 5 side + Grade 5 Motion rail: $"
        f"{output['grade5_side_motion_rail_procurement']['reconciled_subtotal_USD']:.2f}"
    )
    print(
        "  Grade 8 side + Grade 5 Motion rail: $"
        f"{output['grade8_side_motion_rail_procurement']['reconciled_subtotal_USD']:.2f}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "fit-reconciliation.json")
    main(parser.parse_args().output)
