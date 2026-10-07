"""Finished-floor steel diagnostics reusing the frozen component consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
SUPPORT_AUDIT = ROOT / "scripts/thin_bolted_finished_support_audit.py"
SUPPORT_AUDIT_SHA = "0a37e67ed20e3fd1eed8b8b4d0d12889df6fd9a6fb33d6f8f68a0c6768f5ada0"
HEAD_REFERENCE = PACKET / "cap-head-face-reference-v4.json"
HEAD_REFERENCE_SHA = "0cba6f3c9e36506807fe4d353eb970534f92a52c3ed35d91a8076d83c73cc7d4"
SCHEMA = "thin_bolted_finished_floor_steel_demands/v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_finished_support(demand: dict) -> dict:
    if sha(SUPPORT_AUDIT) != SUPPORT_AUDIT_SHA:
        raise ValueError("frozen finished-support audit changed")
    from scripts.thin_bolted_finished_support_audit import audit_finished_state

    receipt = audit_finished_state(demand)
    if receipt.get("independent_finished_support_and_equilibrium_checks_pass") is not True:
        raise ValueError("independent finished-support and equilibrium gate failed")
    if sha(SUPPORT_AUDIT) != SUPPORT_AUDIT_SHA:
        raise ValueError("finished-support audit changed during consumption")
    return receipt


def cap_head_same_state_references(washer_rows: list[dict], reference: dict) -> list[dict]:
    """Multiply only the changed head-input coefficient by the fresh signed action."""
    by_end = {(r["axis_id"], r["role"]): r for r in washer_rows}
    result = []
    for end in reference["ends"]:
        row = by_end[(end["axis_id"], end["role"])]
        profile = reference["profiles"][end["profile_id"]]
        unit = profile["unit_axial_two_face_bending"]
        if row["support_material"] != "steel" or row["role"] != "head_washer" or unit["axial_n"] != 1.:
            raise ValueError("minimum cap-face reference is restricted to one-newton steel-supported head scenarios")
        coefficient = unit["required_fy_mpa_at_sampled_bending_first_yield"]
        result.append({"state_id": row["state_id"], "axis_id": row["axis_id"], "role": row["role"],
                       "frozen_head_profile_id": end["profile_id"], "assumed_circular_head_bearing_diameter_mm": 17.145,
                       "signed_force_on_receiver_along_flange_inward_axis_n": row["signed_force_on_receiver_along_flange_inward_axis_n"],
                       "opening_restraint_component_n": row["opening_restraint_component_n"],
                       "closing_component_n": row["closing_component_n"],
                       "required_fy_mpa_opening_component_reference": coefficient * row["opening_restraint_component_n"],
                       "required_fy_mpa_absolute_projection_diagnostic": coefficient * row["absolute_axial_projection_diagnostic_n"],
                       "actual_head_footprint_and_fillet_seating_verified": False,
                       "physical_bolt_tension_or_own_end_moments_verified": False,
                       "combined_washer_index": None, "complete_joint_acceptance": False})
    return result


def consume_finished_state(demand_path: Path) -> dict:
    demand = json.loads(demand_path.read_text())
    support = require_finished_support(demand)
    # This is the issued consumer, not evaluate(): it does not rerun unit methods.
    from scripts.thin_bolted_steel_demands import consume

    report = consume(demand_path)
    if sha(HEAD_REFERENCE) != HEAD_REFERENCE_SHA:
        raise ValueError("issued cap-head coefficient evidence changed")
    head = json.loads(HEAD_REFERENCE.read_text())
    for relative, expected in head["source_sha256"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"cap-head reference dependency changed: {relative}")
    head_rows = cap_head_same_state_references(report["small_washer_same_state_axial_component_references"], head)
    if len(head_rows) != 12:
        raise ValueError("expected all twelve small steel-supported cap-head scenarios")
    report["schema"] = SCHEMA
    report["status"] = "CONDITIONAL_FINISHED_FLOOR_FRESH_COMPONENT_DIAGNOSTICS"
    report["independent_finished_support_and_equilibrium_audit"] = support
    report["cap_head_17_145mm_same_state_references"] = head_rows
    report["source_sha256"].update({str(SUPPORT_AUDIT.relative_to(ROOT)): SUPPORT_AUDIT_SHA,
                                    str(HEAD_REFERENCE.relative_to(ROOT)): HEAD_REFERENCE_SHA,
                                    str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))})
    report["first_order_geometric_applicability_verified"] = False
    report["physical_common_shaft_and_prying_verified"] = False
    report["limits"].extend(["Finished CAD floor regions and numerical closure are authenticated; actual floor/no-slip and first-order geometric applicability remain unverified.",
                             "The17.145mm head circle is an additional prescribed-pressure scenario. ASME gaging geometry does not qualify delivered contact or small-washer/fillet seating.",
                             "The two small nut washers retain unverified nut bearing footprints. Washer own-end moments/prying and combined resistance are unresolved."])
    return report


def summarize(report: dict) -> dict:
    comparison = report["fresh_demand_comparison"]
    rows = comparison["flange_comparisons"]
    nominal = max(rows, key=lambda r: r["sampled_maximum_nominal_first_yield_index"])
    bearing_rows = [r for r in rows if r["required_fu_mpa_for_asd_bearing_tearout_component"] is not None]
    bearing = max(bearing_rows, key=lambda r: r["required_fu_mpa_for_asd_bearing_tearout_component"]) if bearing_rows else None
    washer = report["small_washer_same_state_axial_component_references"]
    circle_maxima = {}
    for row in washer:
        for scenario in row["reused_frozen_plate_sensitivities"]:
            diameter = str(scenario["assumed_circular_bearing_diameter_mm"])
            circle_maxima[diameter] = max(circle_maxima.get(diameter, 0.), scenario["required_fy_mpa_absolute_projection_diagnostic"])
    return {"state_id": report["state"]["state_id"], "case_id": report["state"]["case_id"],
            "accessory_placement": report["state"]["accessory_placement"],
            "parameters": report["state"]["parameters"],
            "nominal_sampled_flange_yield_index_max": nominal["sampled_maximum_nominal_first_yield_index"],
            "nominal_flange_witness": {k: nominal[k] for k in ("angle_id", "flange")},
            "nominal_sampled_flange_yield_exceedances": comparison["cases"][0]["nominal_sampled_first_yield_exceedances"],
            "required_fu_mpa_bearing_tearout_max": bearing["required_fu_mpa_for_asd_bearing_tearout_component"] if bearing else None,
            "bearing_tearout_witness": {k: bearing[k] for k in ("angle_id", "flange")} if bearing else None,
            "small_washer_max_opening_component_n": max(r["opening_restraint_component_n"] for r in washer),
            "small_washer_max_closing_component_n": max(r["closing_component_n"] for r in washer),
            "small_washer_required_fy_mpa_absolute_projection_by_assumed_circle": circle_maxima,
            "steel_head_17_145mm_required_fy_mpa_absolute_projection_max": max(
                r["required_fy_mpa_absolute_projection_diagnostic"] for r in report["cap_head_17_145mm_same_state_references"]),
            "two_wood_side_small_washer_annulus_opening_reference_index_max": max(
                r["nominal_wood_full_annulus_opening_component_reference_index"] for r in washer if r["support_material"] == "wood"),
            "complete_joint_acceptance": False}


def aggregate(paths: list[Path]) -> dict:
    """Collect governing independent states without mixing or superposing actions."""
    summaries, pins, used = [], {}, set()
    for path in paths:
        report = json.loads(path.read_text())
        if report.get("schema") != SCHEMA or report.get("independent_finished_support_and_equilibrium_audit", {}).get(
                "independent_finished_support_and_equilibrium_checks_pass") is not True:
            raise ValueError("aggregate requires issued finished-support-gated steel reports")
        if report["state"]["state_id"] in used:
            raise ValueError("duplicate parameter state in aggregate")
        used.add(report["state"]["state_id"])
        for relative, expected in report["source_sha256"].items():
            if sha(ROOT / relative) != expected:
                raise ValueError(f"aggregate input source changed: {relative}")
        summaries.append(summarize(report))
        pins[str(path.resolve().relative_to(ROOT))] = sha(path)
    if not summaries:
        raise ValueError("at least one issued state is required")
    worst = max(summaries, key=lambda r: r["nominal_sampled_flange_yield_index_max"])
    return {"schema": "thin_bolted_finished_floor_steel_summary/v1", "state_summaries": summaries,
            "source_sha256": pins | {str(Path(__file__).relative_to(ROOT)): sha(Path(__file__))},
            "governing_sampled_flange_state_id": worst["state_id"],
            "governing_sampled_flange_yield_index": worst["nominal_sampled_flange_yield_index_max"],
            "actions_from_distinct_states_combined_or_superposed": False,
            "complete_joint_acceptance": False, "fabrication_release": False, "climbing_release": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demands", type=Path)
    mode.add_argument("--aggregate", nargs="+", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve issued finished-floor component evidence")
    report = consume_finished_state(args.demands) if args.demands else aggregate(args.aggregate)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "summary": summarize(report) if args.demands else
                      {"states": len(report["state_summaries"]), "governing_index": report["governing_sampled_flange_yield_index"]}}, indent=2))


if __name__ == "__main__":
    main()
