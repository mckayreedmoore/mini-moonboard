"""One saved A12-rear upper-left panel attachment route; parent executes.

Preserve all signed source forces, moments, contacts and twelve screw ties.
Reference requirements are conditional arithmetic, not a new force allocation,
hardware selection, frame/CAD/native run or physical release.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
RAW = HERE / "rawlocal/panel-path-reconciliation"
FRAME = HERE / "frame-250-attempt02"
OPERATORS = HERE / "operators-attempt02"
HEAD = HERE / "rawlocal/head-check/attempt01"
REFERENCE = BASE / "panel-attachment/results/attempt08-all-two-receiver/comparison.json"
SOURCE = (
    ROOT
    / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-input-adapter-attempt01/a12-rear/model.json"
)
CONTACTS = SOURCE.parents[2] / "reduced-static-attempt01/contact-geometry.json"
PDF = (
    BASE.parent
    / "upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf"
)
BODY, CASE, AXIS = "main_upper_left", "a12-rear", "round_panel_upper_left_edge_2"
AXIAL, LATERAL, CONTACT = (
    "non_qualifying_parametric_screw_withdrawal",
    "panel_screw_lateral_plane",
    "timber_or_panel_contact",
)
PINS = {
    FRAME
    / "comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    FRAME
    / "response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    OPERATORS
    / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    OPERATORS
    / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    OPERATORS
    / "model-inputs.json": "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    OPERATORS
    / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    HERE
    / "panel-contact-sharing.py": "8fd353bb515ef4b453bb2dbf820e087c506a46f5356b5fbcf0ffb28053c3e62f",
    HERE
    / "head-reference-basis.md": "577f75fa32889fdb5ee53f1076ebec924132b5251d6e92e571ab0b49e96588d3",
    HEAD
    / "receipt.json": "be53a3e7cfbb674b00a5571df228b318908ead3726dfbb2fa26e49689df659af",
    HEAD
    / "screw-states.csv": "30b34cdf7400afa909e35efc36ea308da4089987d61eb6f8e2419ab096572989",
    REFERENCE: "7146069ad3ecf913cbb354f3a37d1e6af6768fc3b577f574feb5a10bd483eb2f",
    BASE
    / "panel-attachment/attachment_screen.py": "c2acb48370cecb3964172e8ab82d3c8999e2836e97025e1bde778bc03cf6b9dc",
    BASE
    / "frame_state_contract.py": "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
    SOURCE: "61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8",
    CONTACTS: "034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151",
    PDF: "53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def module(path, name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "saved helper unavailable")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def reference_requirements(tension, lateral, helper, saved):
    """Existing equations and bounded inverse requirements, with no capacity adoption."""
    resultant = math.hypot(tension, lateral)
    head_rows = []
    for thickness in (17.25625, 18.25625):
        unadjusted = float(helper.head_reference(0.50, 9.017, thickness))
        adjusted = 1.6 * unadjusted
        head_rows.append(
            {
                "plywood_G_hypothesis": 0.50,
                "retailer_nominal_head_diameter_mm": 9.017,
                "net_plywood_thickness_mm_hypothesis": thickness,
                "CD_hypothesis": 1.6,
                "CM_Ct_hypothesis": 1.0,
                "unadjusted_head_reference_n": unadjusted,
                "adjusted_head_reference_n": adjusted,
                "demand_reference_ratio": tension / adjusted,
                "required_head_diameter_mm_algebraic_thin_branch": 9.017
                * tension
                / adjusted,
                "inverse_head_diameter_within_Table12_2F_range": 5.9436
                <= 9.017 * tension / adjusted
                <= 12.7,
                "head_reference_at_maximum_tabulated_diameter_n": 1.6
                * float(helper.head_reference(0.50, 12.7, thickness)),
            }
        )
    withdrawal_rows = []
    for source in saved["withdrawal_sensitivities"]:
        g, penetration = (
            source["timber_G_hypothesis"],
            source["effective_thread_penetration_mm_hypothesis"],
        )
        unadjusted = float(helper.withdrawal_reference(g, penetration))
        require(
            abs(unadjusted - source["unadjusted_generic_withdrawal_n"]) < 1e-9,
            "saved withdrawal equation differs",
        )
        adjusted = 1.6 * unadjusted
        term = tension**2 / (resultant * adjusted)
        withdrawal_rows.append(
            {
                "timber_G_hypothesis": g,
                "effective_thread_penetration_mm_hypothesis": penetration,
                "unadjusted_withdrawal_reference_n": unadjusted,
                "CD_hypothesis": 1.6,
                "adjusted_withdrawal_reference_n": adjusted,
                "axial_demand_reference_ratio": tension / adjusted,
                "same_state_NDS12_4_withdrawal_term": term,
                "required_adjusted_lateral_reference_n": lateral**2
                / (resultant * (1 - term))
                if term < 1
                else None,
            }
        )
    per_mm = 1.6 * float(helper.withdrawal_reference(0.50, 1.0))
    proposed_gross_penetration = 76.2 - 18.25625
    proposed_w = per_mm * proposed_gross_penetration
    proposed_term = tension**2 / (resultant * proposed_w)
    return {
        "head": head_rows,
        "withdrawal": withdrawal_rows,
        "lateral": {
            "same_state_demand_n": lateral,
            "Hillman_adjusted_lateral_resistance_n": None,
            "source": "NDS12.4 same-state requirement only; no Hillman lateral rating supplied.",
            "combined_requirement": "R = hypot(T,V); T^2/(R*Wprime) + V^2/(R*Zprime) <= 1. Head pull-through remains a separate check.",
        },
        "current_screw_length_mm": 63.5,
        "panel_thickness_mm": 18.25625,
        "current_gross_possible_timber_embedment_mm": 63.5 - 18.25625,
        "current_9mm_head_thickness_independent_reference_ceiling_n": 1.6
        * float(helper.head_reference(0.50, 9.017, 38.1)),
        "head_diameter_applicability_mm": [5.9436, 12.7],
        "net_side_thickness_applicability_mm": [7.9375, 38.1],
        "G050_CD16_minimum_effective_penetration_for_axial_only_mm": tension / per_mm,
        "G050_CD16_effective_penetration_necessary_for_any_finite_lateral_reference_mm_strictly_greater_than": tension
        ** 2
        / (resultant * per_mm),
        "proposed_hardware_requirement_diagnostic": {
            "nominal_length_mm": 76.2,
            "gross_embedment_ceiling_mm": proposed_gross_penetration,
            "G_hypothesis": 0.50,
            "CD_hypothesis": 1.6,
            "Wprime_if_entire_gross_embedment_is_effective_thread_n": proposed_w,
            "required_Zprime_under_that_optimistic_thread_hypothesis_n": lateral**2
            / (resultant * (1 - proposed_term))
            if proposed_term < 1
            else None,
            "independently_supported_head_pullthrough_reference_required_n": tension,
            "selected_or_qualified": False,
            "limit": "A 3-in length is a purchasing requirement example, not a Hillman rating or delivered thread length. A compatible larger head/load spreader needs its own supported resistance; the inverse head diameter is outside the NDS equation's range.",
        },
    }


def run(output):
    output = output.resolve()
    require(
        output.is_relative_to(RAW.resolve())
        and output != RAW.resolve()
        and not output.exists(),
        "fresh owned rawlocal child required",
    )
    pins = dict(PINS)
    for path, expected in pins.items():
        require(sha(path) == expected, f"changed input: {path}")
    extractor = module(
        HERE / "panel-contact-sharing.py", "upper_left_panel_path_extractor"
    )
    # A private imported module supplies the existing pure panel accounting API.
    # Its original comparison run is never called, and no shared source is edited.
    extractor.BODY, extractor.CASE = BODY, CASE
    extractor.FRAMES = {
        12: (str(FRAME), PINS[FRAME / "comparison.json"], PINS[FRAME / "response.npz"])
    }
    cells = {c["name"]: c for c in read(SOURCE)["contact_cell_ownership"]}
    patches = read(CONTACTS)["contact_patches"]
    state, _h, rows = extractor.analyze(12, pins, cells, patches)
    require(state["peak"]["row_id"].split("/")[0] == AXIS, "governing axis differs")
    with (HEAD / "screw-states.csv").open(newline="") as stream:
        saved_ties = [
            r
            for r in csv.DictReader(stream)
            if r["source"] == str(FRAME.relative_to(ROOT))
            and r["case_id"] == CASE
            and float(r["gap_scale"]) == 1
            and r["panel"] == BODY
        ]
    require(len(saved_ties) == 12, "saved twelve-tie census differs")
    model = read(OPERATORS / "model.json")
    actions, grouped = state["actions"], defaultdict(list)
    for action in actions:
        grouped[action["other_body"]].append(action)
    screw_records = []
    reference_module = module(
        BASE / "panel-attachment/attachment_screen.py", "panel_path_references"
    )
    for tie in saved_ties:
        axis = tie["axis_id"]
        own = [a for a in actions if a["row_id"].startswith(axis + "/")]
        require(
            len(own) == 3 and {a["role"] for a in own} == {AXIAL, LATERAL},
            "incomplete screw action",
        )
        axial = next(a for a in own if a["role"] == AXIAL)
        lateral_rows = [a for a in own if a["role"] == LATERAL]
        t, v = (
            float(tie["head_pullthrough_demand_n"]),
            float(tie["lateral_resultant_n"]),
        )
        require(
            abs(t - axial["scalar_force_n"]) < 1e-7
            and abs(v - math.hypot(*(a["scalar_force_n"] for a in lateral_rows)))
            < 1e-7,
            "saved screw demands differ",
        )
        point = np.array(axial["point_xyz_mm"])
        delta = point - state["peak"]["point_xyz_mm"]
        tangent = np.cross(state["panel_normal_xyz"], [1.0, 0.0, 0.0])
        row = next(r for r in rows if r["row_id"] == axial["row_id"])
        grain = model["material_binding"]["orientation_overrides"][tie["receiver"]][
            "material_axes_global_xyz"
        ]["L"]
        sidegrain_dot = float(
            abs(np.array(grain) @ row["ownership"]["direction_global_xyz"])
        )
        require(sidegrain_dot < 1e-7, "withdrawal sidegrain hypothesis is inapplicable")
        screw_records.append(
            {
                "axis_id": axis,
                "receiver": tie["receiver"],
                "point_xyz_mm": point.tolist(),
                "offset_from_peak_X_T_mm": [float(delta[0]), float(delta @ tangent)],
                "in_plane_distance_from_peak_mm": float(
                    math.hypot(delta[0], delta @ tangent)
                ),
                "head_and_withdrawal_demand_n": t,
                "lateral_demand_n": v,
                "source_opening_mm": float(tie["relative_opening_mm"]),
                "source_axis_grain_dot_abs": sidegrain_dot,
                "signed_wrench_on_panel_about_saved_datum_n_nmm": np.sum(
                    [
                        np.r_[a["force_xyz_n"], a["moment_about_panel_datum_xyz_nmm"]]
                        for a in own
                    ],
                    axis=0,
                ).tolist(),
                "head_reference_930222_ratio": t
                / (1.6 * reference_module.head_reference(0.50, 9.017, 17.25625)),
                "head_reference_984128_ratio": t
                / (1.6 * reference_module.head_reference(0.50, 9.017, 18.25625)),
            }
        )
    peak = next(r for r in screw_records if r["axis_id"] == AXIS)
    requirements = reference_requirements(
        peak["head_and_withdrawal_demand_n"],
        peak["lateral_demand_n"],
        reference_module,
        read(REFERENCE),
    )
    receiver_records = []
    for receiver, own in sorted(grouped.items()):
        ties = [s for s in screw_records if s["receiver"] == receiver]
        receiver_records.append(
            {
                "receiver": receiver,
                "panel_action_count": len(own),
                "contact_count": sum(a["role"] == CONTACT for a in own),
                "active_contact_count": sum(
                    a["role"] == CONTACT and a["scalar_force_n"] > 0.01 for a in own
                ),
                "screw_tie_count": len(ties),
                "screw_tension_sum_n": sum(
                    s["head_and_withdrawal_demand_n"] for s in ties
                ),
                "signed_wrench_on_panel_about_saved_datum_n_nmm": np.sum(
                    [
                        np.r_[a["force_xyz_n"], a["moment_about_panel_datum_xyz_nmm"]]
                        for a in own
                    ],
                    axis=0,
                ).tolist(),
                "signed_normal_contact_sum_n": sum(
                    a["panel_normal_force_n"] for a in own if a["role"] == CONTACT
                ),
            }
        )
    head_exceptions = [
        s["axis_id"] for s in screw_records if s["head_reference_930222_ratio"] > 1
    ]
    payload = {
        "schema": "one_upper_left_panel_hotspot_route/v1",
        "status": "SAVED_ROUTE_BALANCED_DECLARED_HEAD_REFERENCE_EXCEEDED",
        "source_hold_lever_mm": 100,
        "case": CASE,
        "gap_scale": 1,
        "panel": BODY,
        "peak_axis": AXIS,
        "producer_sha256": sha(Path(__file__).resolve()),
        "source_sha256": {
            str(p.relative_to(ROOT)): digest for p, digest in pins.items()
        },
        "complete_saved_panel_accounting": state,
        "all_twelve_same_state_screw_records": screw_records,
        "nearest_four_adjacent_ties": sorted(
            (s for s in screw_records if s["axis_id"] != AXIS),
            key=lambda s: s["in_plane_distance_from_peak_mm"],
        )[:4],
        "per_receiver_panel_actions": receiver_records,
        "hotspot_reference_requirements": requirements,
        "axes_exceeding_reduced_net_head_reference": head_exceptions,
        "complete_joint_acceptance": False,
        "hardware_selected": False,
        "geometry_changed": False,
        "physical_release": False,
        "practical_disposition": "The frozen route cannot meet the declared head references. Keeping the same forces requires a changed fastening assembly with independently supported head, timber withdrawal and simultaneous lateral resistance. A larger head/washer alone does not establish that route. Preserving all purchased screws instead requires a changed backing/tie load path and a new compatible force response; no redistribution is supplied here.",
        "limits": [
            "One saved simultaneous A12-rear nominal state; no new force allocation, contact law, stiffness or count study.",
            "All twelve ties and all incident contacts/lateral actions are retained; nearby contacts are not isolated balancing partners.",
            "G, duration, effective thread length, head/countersink geometry and Hillman force-slip law remain conditional. Parent owns duration adoption.",
            "NDS table head bounds are read from the pinned Chapter12/Table12.2F. Inverse diameters outside those bounds are algebraic diagnostics only, not resistance for a washer or larger head.",
            "A longer-screw requirement example changes the purchased policy if selected. It is not authorized installation, delivered thread engagement, occupancy, steel strength, product selection or a new candidate.",
        ],
    }
    for path, expected in pins.items():
        require(sha(path) == expected, f"input changed during accounting: {path}")
    output.mkdir(parents=True)
    (RAW / ".gitignore").write_text("*\n")
    dump(output / "result.json", payload)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                "result_sha256": sha(output / "result.json"),
                "head_reference_exceeding_axes": head_exceptions,
                "peak": peak,
                "hotspot_reference_requirements": requirements,
                "signed_panel_balance": state["balance_residual_xyz_n_and_nmm"],
            },
            indent=2,
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    run(parser.parse_args().output)


if __name__ == "__main__":
    main()
