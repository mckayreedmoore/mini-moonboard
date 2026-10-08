"""Publish compact witnesses from the fixed admitted A12 assessment inputs."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

from scripts import thin_bolted_joint_post_admission as pure

OWN = Path(__file__).resolve()
LOADED_SHA = hashlib.sha256(OWN.read_bytes()).hexdigest()
ROOT = pure.ROOT
PACKET = OWN.parent
GATE = PACKET / "admission.py"
GATE_SHA = "4b78722ab407a39d6e00fc9e16be0d370d0c837dea5880e45e7a2e277dd6efb6"
INPUTS = {
    "a12-rear.json": "29b25f11794a171a1364268ed676a24cee2882e47c3018b3648267d2707a0ddf",
    "admission.json": "e5bbf8c0ad2947f42f71819d61b03fcd260a0926b5f5429481e5523ff8e122a5",
    "component-reductions.json": "650c0cf1225326506c91ff74b97205832f1ba73e3b67cfe8d73450d42237285e",
    "pose-applicability.json": "9918d4b93c8201f71d0621aff2b3fa2d2391b2eb148da8d4fbe389f712f3d077",
    "pose-applicability-review.json": "deddc0dd5f392220858c0f8aa85ad72f6af1c5229dc629b851fac942996be46e",
    "fitting-gravity-v1/gravity-diagnostic.json": "4d0b9b9615a8b7574fecf2d42834ef2567dade841f8f61d578f638d5041a84f4",
    "section-box-v1/normal-stress.json": "e810ab40d10ffbb9e4488b8f13e7f9bd3710a2a03fb365e538869e3b8d622a46",
    "section-box-v1/independent-normal-stress-validation.json": "c5d33e39d12e5b64911751503d14a506fda55e08e8e0b717c19dd47bbed854db",
}


def read_bound(name):
    payload = (PACKET / name).read_bytes()
    pure.unit.require(hashlib.sha256(payload).hexdigest() == INPUTS[name], "fixed assessment input changed: " + name)
    return json.loads(payload)


def compose():
    pure.verify_pins({str(GATE.relative_to(ROOT)): GATE_SHA})
    field_bytes = (PACKET / "a12-rear.json").read_bytes()
    pure.unit.require(hashlib.sha256(field_bytes).hexdigest() == INPUTS["a12-rear.json"], "fixed raw assessment bytes differ")
    admission = read_bound("admission.json")
    spec = importlib.util.spec_from_file_location("actual_gate_for_compact_assessment", GATE)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    field, pins = gate.require_admitted_payload(field_bytes, admission, admission_sha256=GATE_SHA)
    reports = [read_bound(name) for name in (
        "component-reductions.json", "pose-applicability.json", "fitting-gravity-v1/gravity-diagnostic.json",
        "section-box-v1/normal-stress.json")]
    components, pose, gravity, sections = reports
    for report in reports:
        pure.unit.require(all(report[k] == field[k] for k in pure.IDENTITIES)
            and report["field_sha256"] == INPUTS["a12-rear.json"]
            and report["release"] == field["release"] and not any(report["release"].values()),
            "same admitted field identity and unqualified release required")
        pins = gate.linear.merge_pins(pins, report["source_sha256"])
    review = read_bound("pose-applicability-review.json")
    pure.unit.require(review["numeric_review_pass"] is True and review["state_id"] == field["state_id"]
        and review["q_canonical_sha256"] == admission["original_gradient_checks"]["final_q_canonical_sha256"],
        "current numerical pose review differs")
    section_review = read_bound("section-box-v1/independent-normal-stress-validation.json")
    layout = json.loads(pure.unit.LAYOUT.read_bytes())
    fitting_rows = {r["angle_id"]: r for r in layout["raw_fittings"]}
    nominal = {(r["angle_id"], r["flange"]): r for r in gravity["nominal_flange_diagnostics"]}
    torsion = {(r["angle_id"], r["flange"]): r for r in gravity["flange_torsion_diagnostics"]}
    pure.unit.require(len(fitting_rows) == 36 and len(nominal) == len(torsion) == 72,
                      "all36 fittings/all72 current flange references required")
    duties = []
    for duty in sorted({r["duty_id"] for r in fitting_rows.values()}):
        names = sorted(name for name, row in fitting_rows.items() if row["duty_id"] == duty)
        own = [nominal[(name, flange)] for name in names for flange in ("beam", "post")]
        witness = max(own, key=lambda r: r["sampled_maximum_nominal_first_yield_index"])
        scenarios = {}
        for scenario in ("gross_rectangle", "two_ligament_equal_twist_proxy"):
            choices = [{"angle_id": name, "flange": flange, **torsion[(name, flange)]["sampled_scenario_witnesses"][scenario]}
                for name in names for flange in ("beam", "post")
                if torsion[(name, flange)]["sampled_scenario_witnesses"][scenario] is not None]
            scenarios[scenario] = max(choices, key=lambda r: r["simultaneous_nominal_first_yield_bound_index"], default=None)
        duties.append({"duty_id": duty, "fitting_ids": names,
            "axis_ids": sorted(a["id"] for a in layout["installed_axes"]
                if any(r["duty_id"] == duty for r in a["attachments"])),
            "nominal_flange_witness_including_operator_gravity": {k: witness[k] for k in (
                "angle_id", "flange", "sampled_maximum_nominal_first_yield_index", "sampled_stress_witness")},
            "same_cut_torsion_scenario_witnesses_including_operator_gravity": scenarios,
            "complete_joint_strength_disposition": "UNQUALIFIED", "complete_joint_resistance": None})
    pure.unit.require(len(duties) == 24, "all24 original angle duties required")
    panels = [{"panel": row["panel"],
        "spatial_section_diagnostics": row["resolved_section_diagnostics"],
        "separate_mean_net_section_diagnostics": row["integrated_net_section_diagnostics"],
        "deformation_diagnostics": row["deformation_diagnostics"], "complete_panel_resistance": None}
        for row in components["panels"]["panel_diagnostics"]]
    source_records = {str((PACKET / name).relative_to(ROOT)): digest for name, digest in INPUTS.items()}
    source_records[str(OWN.relative_to(ROOT))] = LOADED_SHA
    pins = gate.linear.merge_pins(pins, source_records)
    pure.verify_pins(pins)
    for name in INPUTS:
        read_bound(name)
    return {"schema": "thin_bolted_current_a12_compact_conditional_assessment/v1",
        **{key: field[key] for key in pure.IDENTITIES}, "field_sha256": INPUTS["a12-rear.json"],
        "counts": field["counts"], "source_sha256": pins, "input_records": source_records,
        "original_gradient_and_same_q_floor_gate": admission["original_gradient_checks"],
        "independent_body_global_equilibrium": admission["independent_common_shaft_audit"]["equilibrium"],
        "current24_joint_duty_diagnostics": duties,
        "other_component_witnesses_original_declared_scope": {k: v for k, v in
            components["governing_conditional_diagnostic_witnesses"].items() if not k.startswith("flange_")},
        "six_panel_spatial_mean_and_deformation_diagnostics": panels,
        "all66_same_axis_generic_screw_diagnostic_values": [{k: row[k] for k in (
            "axis_id", "panel", "receiver", "withdrawal_n", "same_axis_simultaneous_lateral_n",
            "generic_head_ratio_CD1", "generic_head_ratio_conditional_CD1p6",
            "generic_withdrawal_required_effective_thread_mm_CD1",
            "generic_withdrawal_required_effective_thread_mm_conditional_CD1p6",
            "gross_nominal_length_after_panel_mm", "Hillman_product_capacity_or_stiffness_established")}
            for row in components["panels"]["screw_actions_and_generic_references"]],
        "all20_existing_timber_cut_diagnostic_witnesses": components["timber"]["simultaneous_existing_member_cut_witnesses"],
        "five_exact_net_section_containing_box_stress_bounds": sections["five_same_cut_section_box_bounds"],
        "independent_five_section_numeric_review": section_review,
        "admitted_current_pose_markers": pose["markers"], "independent_pose_review": review,
        "fitting_gravity_operator_projection": gravity["source_gravity_port_projection_checks"],
        "limits": [
            "One admitted first-order A12 scenario; unmeasured stiffness and current contact applicability do not establish physical demand bounds.",
            "Every24 duty's current nominal/torsion witness includes the original operator's own gravity interpolation; physical formed-leg weight distribution and product heel/hole/warping/prying strength remain unqualified.",
            "The original full component artifact preserves its earlier flange-cut scope; the current24 duty rows use the gravity-complete operator scenario.",
            "Generic Hillman head/withdrawal comparisons and spatial spline panel findings remain separate from mean net-cut diagnostics and actual local capacity.",
            "All14 unequal shared-shaft ASD resistances, actual roots/threads/Fyb, own washer pressures/moments and complete group/splitting/shear/stability resistance remain unavailable.",
            "The1046 cut replay excludes four terminal planes; five containing-box stress bounds do not qualify other sections, occupied corner extrema or complete NDS resistance.",
            "Fixed-q finite pose markers, including zero-roll shaft lifts, do not recompute contact forces, current overlap or physical motion.",
            "The recorded no-slip floor assumption remains unverified; arithmetic activation consistency supplies no floor friction or anchor capacity.",
        ], "complete_joint_resistance": None, "complete_joint_acceptance": False,
        "structural_or_fabrication_release": False, "release": dict(field["release"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve existing compact assessment")
    result = compose()
    with args.out.open("x") as output:
        json.dump(result, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")


if __name__ == "__main__":
    main()
