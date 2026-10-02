"""Screen remaining bolts using the saved six nominal-gap frame states.

This is saved-array arithmetic, not a frame solve or complete-joint acceptance.
The top outer corner connectors and lower-left outer service cleat are excluded.
"""

import argparse
import csv
import importlib.util
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True

import bolt_demands as demands
import frame_state_contract as frame_contract
import lateral_reference as lateral
import numpy as np
import top_corner_local as local

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FRAME = HERE / "corner-frame-attempt01"
GAP = HERE / "both-corner-frame-attempt01"
OUTPUT = HERE / "remaining-joint-screen-attempt01/partial-support-corrected"
HYPOTHESES = HERE.parent
RETAINED_PACKET = HYPOTHESES / "retained-frame-bolt-current-resistance-basis-2026-10-01"
RETAINED = Path(
    "/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json"
)
SUPPORT = Path("/tmp/mini-moonboard-remaining-seats-parent-2026-10-01.json")
EXCLUDED_PREFIXES = (
    "top_outer/clip_single_top_left_1/rail_",
    "top_outer/clip_single_top_left_1/side_",
    "top_outer/clip_single_top_right_2/rail_",
    "top_outer/clip_single_top_right_2/side_",
)
WORKER_BLOCK = "left_service_outer_lower_cleat"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
DEFAULT_CLEARANCE_PINS = {
    "comparison.json": "044d914af001b9d0e9f2895b4ddc95498b8f3cdf70d96a035bb7d274467a256d",
    "response.npz": "af5567aeef00df674bd8cfa1400e093174c0427bd9629f8afd9b15657df8451e",
}
PINS = {
    HERE
    / "bolt_demands.py": "b3b5d2676bfd7efc908e9411c1aeddd58b5483fc33dd206d263d99d8fb6ca479",
    RETAINED: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    SUPPORT: "64853898bccf71df62119f0977f29aa612b323d436790b370b5616f7b3cb9fe3",
    **lateral.PINS,
    local.SEATS: local.PINS[local.SEATS],
    local.FASTENERS: local.PINS[local.FASTENERS],
}
GAPS = {
    "GROUP_GEOMETRY": "Bind finished loaded edges/ends, spacing and Cdelta; resolve the oblique nonuniform bolt group/Cg, splitting, tear-out, member sections and complete contact/couple transfer at these same states.",
    "HARDWARE_AXIAL": "Specify applicable Fyb/product basis and body/thread transition through each receiver, nut engagement, bolt bending and coupled axial/lateral resistance; no hardware is selected by this screen.",
    "WASHER_TRANSFER": "Resolve actual supported footprint, eccentric contact/wood pressure and washer/head/nut metal spreading or bending; ideal annulus pressure is not a complete axial-transfer check.",
    "END_GRAIN": "The bolt axis is parallel to one receiver's grain. The reused transverse single-shear helper does not establish an applicable end-grain lateral resistance or splitting/detailing treatment.",
    "MULTI_RECEIVER": "A continuous three-receiver bolt has two distinct lateral planes. Resolve compatible bolt bending, receiver bearing and axial/lateral interaction; do not sum plane magnitudes or apply a two-member reference.",
    "PARTIAL_SEAT": "center_principal_right_2 nut seat on base_principal_center_right overlaps the retained 38.1mm F1-G1 service passage. Centered outer-envelope support is 90.0597697729%, centered minimum-area support is 90.6001120577%, and swept containment is 86.7210768952%. Full-annulus pressure/ratios are inapplicable and omitted at this seat and in this bolt's plane rows. Keep signed demand for the parent's separate bearing-footprint work; supported contact/metal/wood transfer remains open.",
    "RETAINED_WASHER": "The consumed retained register has no bound OD/ID/support treatment for its 1/2- and 3/8-inch washer families. The quarter-inch annulus is inapplicable; pressures and ratios stay null.",
}
sha, read, require = demands.sha, local.read, local.require


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def write_csv(path, records):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def state_ref(record):
    """Keep one simultaneous state; never compose independent maxima."""
    keys = (
        "case_id",
        "axis_id",
        "plane_id",
        "first_body",
        "second_body",
        "shear_component_1_n",
        "shear_component_2_n",
        "shear_x_n",
        "shear_y_n",
        "shear_z_n",
        "shear_resultant_n",
        "outer_tie_signed_n",
        "reference_45ksi_n",
        "ratio_45ksi",
        "mode_45ksi",
        "reference_92ksi_n",
        "ratio_92ksi",
        "mode_92ksi",
        "reference_106ksi_n",
        "ratio_106ksi",
        "mode_106ksi",
        "ideal_annulus_pressure_mpa",
        "ideal_pressure_over_wood_reference",
        "washer_reference_status",
        "lateral_reference_status",
    )
    return {key: record[key] for key in keys}


def main(clearance, output):
    global GAP, OUTPUT
    GAP = clearance.resolve()
    if GAP.name == "comparison.json":
        GAP = GAP.parent
    OUTPUT = output.resolve()
    require(
        OUTPUT.is_relative_to(HERE)
        and OUTPUT.relative_to(HERE)
        .parts[0]
        .startswith("remaining-joint-screen-attempt"),
        "output must be inside an owned remaining-joint-screen-attempt directory",
    )
    require(not OUTPUT.exists(), "preserve the recorded attempt; output already exists")
    PINS[GAP / "comparison.json"] = sha(GAP / "comparison.json")
    comparison = read(GAP / "comparison.json")
    PINS[GAP / "response.npz"] = comparison["response_sha256"]
    if GAP == (HERE / "both-corner-frame-attempt01").resolve():
        require(
            all(
                PINS[GAP / name] == digest
                for name, digest in DEFAULT_CLEARANCE_PINS.items()
            ),
            "default clearance source changed",
        )
    clearance_scopes = {
        "both_top_corner_corrected_frame_clearance/v1": "both top outer corners",
        "coupled_top_and_service_frame_clearance/v1": "both top outer corners and both upper/lower left outer service cleats",
        "coupled_outer_corner_frame_clearance/v1": "both top and bottom outer corners and both upper/lower left outer service cleats",
        "coupled_two_receiver_frame_clearance/v1": "all 88 independent two-receiver candidate bolts; four continuous candidate bolts and twelve retained bolts remain at zero clearance",
    }
    require(
        comparison["schema"] in clearance_scopes, "unknown clearance source contract"
    )
    clearance_scope = clearance_scopes[comparison["schema"]]
    force_scope = frame_contract.force_state_scope(comparison)
    PINS[Path(frame_contract.__file__)] = sha(Path(frame_contract.__file__))
    assessment, baseline = (
        read(FRAME / "operator-assessment.json"),
        read(FRAME / "frame-results.json"),
    )
    frame_inputs = read(FRAME / "inputs.json")
    require(
        frame_inputs["source_sha256"] == assessment["source_sha256"],
        "frame input pins differ",
    )
    require(
        baseline["operator_assessment_sha256"]
        == sha(FRAME / "operator-assessment.json"),
        "wrong baseline assessment",
    )
    require(
        assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
        "frame operator status changed",
    )
    for relative, digest in comparison["source_sha256"].items():
        path = ROOT / relative
        require(path not in PINS or PINS[path] == digest, "conflicting source pin")
        PINS[path] = digest
    for name, digest in assessment["output_sha256"].items():
        require(PINS[FRAME / name] == digest, "gap/baseline frame binding differs")
    require(
        PINS[FRAME / "frame-response.npz"] == baseline["response_sha256"],
        "baseline response differs",
    )
    require(
        sha(FRAME / "corner_frame.py.snapshot")
        == assessment["producer_sha256"]
        == frame_inputs["producer_sha256"],
        "frame producer snapshot differs",
    )
    require(
        sha(GAP / "producer.py.snapshot") == comparison["producer_sha256"],
        "gap producer snapshot differs",
    )
    PINS[FRAME / "inputs.json"] = sha(FRAME / "inputs.json")
    PINS[FRAME / "corner_frame.py.snapshot"] = assessment["producer_sha256"]
    PINS[GAP / "producer.py.snapshot"] = comparison["producer_sha256"]
    retained = read(RETAINED)
    retained_method = RETAINED_PACKET / "produce.py"
    PINS[retained_method] = retained["producer_sha256"]
    nds_path = ROOT / "mini_moonboard/nds_2024_multi_member_bolt_yield.py"
    PINS[nds_path] = retained["source_pins"][str(nds_path.relative_to(ROOT))]["sha256"]
    PINS[Path(__file__)] = sha(Path(__file__))
    for path, digest in PINS.items():
        require(sha(path) == digest, "changed source: " + str(path))
    require(len(comparison["states"]) == 12, "incomplete zero/gap source census")
    require(
        {(s["case_id"], s["gap_scale"]) for s in comparison["states"]}
        == {(c, g) for c in CASES for g in (0.0, 1.0)},
        "missing/duplicate/failed source frame state",
    )
    model, inputs = read(FRAME / "model.json"), read(lateral.INPUTS)
    require(
        model["source_revision"]
        == inputs["revision_id"]
        == retained["geometry_revision_id"],
        "mixed source revisions",
    )
    require(
        model["candidate"] == inputs["candidate"] == retained["candidate"],
        "mixed candidates",
    )
    members = {
        m["member_id"]: m["reduced_geometry_descriptor"]
        for m in inputs["members"]
        if m["member_kind"] != "panel"
    }
    bolts = {
        b["axis_id"]: b
        for b in inputs["connections"]
        if b["kind"] in ("candidate_bolt", "retained_bolt")
    }
    excluded_top = {a for a in bolts if a.startswith(EXCLUDED_PREFIXES)}
    excluded_worker = {
        a for a, b in bolts.items() if WORKER_BLOCK in b["receiver_member_ids"]
    }
    proposed = {a["axis_id"] for p in model["proposed_corner_axes"] for a in p["axes"]}
    require(
        len(bolts) == 104
        and excluded_top == proposed
        and len(excluded_top) == 8
        and len(excluded_worker) == 4,
        "ownership partition changed",
    )
    included = set(bolts) - excluded_top - excluded_worker
    rows = read(FRAME / "row-identities.json")
    require(
        len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)),
        "raw row order changed",
    )
    planes, ties = defaultdict(list), {}
    for row in rows:
        axis = row["row_id"].rsplit("/", 1)[0]
        if axis not in included:
            continue
        role = row["ownership"]["role"]
        if role in ("candidate_bolt_lateral_plane", "retained_bolt_lateral_plane"):
            planes[row["row_id"]].append(row)
        elif role == "physical_bolt_outer_seat_tension":
            require(axis not in ties, "duplicate axial tie")
            require(row["law"]["intended_law"] == "tension_only", "wrong axial law")
            ties[axis] = row
    require(
        set(ties) == included and len(planes) == 96, "incomplete owned connector census"
    )
    nds, retained_helper = (
        load_module(nds_path, "remaining_nds"),
        load_module(retained_method, "remaining_retained"),
    )
    material = read(local.actions_method.MATERIALS)["conditional_DF_L_No2_base_row"][
        "base_properties"
    ]
    fc_perp, fc_parallel = [
        material[k] * local.PSI_MPA for k in ("Fc_perpendicular", "Fc_parallel")
    ]
    annulus = next(
        a
        for a in read(local.SEATS)["washer_annulus_scenarios"]
        if a["scenario_id"] == "catalog_minimum_area"
    )
    fasteners = read(local.FASTENERS)
    washer = fasteners["dimension_inputs"]["washer"]
    grade5_yield_psi = (
        1000
        * fasteners["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"][
            "machine_test_yield_ksi_min"
        ]
    )
    require(grade5_yield_psi == 92000, "conditional Grade 5 minimum scenario changed")
    area = math.pi / 4 * 25.4**2 * (washer["od_in"][0] ** 2 - washer["id_in"][1] ** 2)
    require(
        math.isclose(area, annulus["annulus_area_mm2"], rel_tol=1e-12),
        "annulus inputs differ",
    )
    support = read(SUPPORT)
    require(
        support["input_pins"]["reduced model inputs"]["sha256"] == PINS[lateral.INPUTS],
        "seat/model source differs",
    )
    partial = next(
        s
        for s in support["seats"]
        if s["axis_id"] == "center_principal_right_2" and s["role"] == "nut"
    )
    require(
        not partial["geometry_screen_pass"]
        and partial["member"] == "base_principal_center_right",
        "partial-seat evidence changed",
    )
    require(
        support["finished_step_pins"][partial["member"]]["sha256"]
        == members[partial["member"]]["step_sha256"],
        "partial seat receiver differs",
    )
    records, seat_records = [], []
    with np.load(GAP / "response.npz", allow_pickle=False) as data:
        for case_id in CASES:
            force = data[case_id + "_gap_raw_force_n"]
            require(
                force.shape == (1888,) and np.isfinite(force).all(),
                "invalid raw force array",
            )
            for plane_id, components in sorted(planes.items()):
                axis = plane_id.rsplit("/", 1)[0]
                bolt, tie = bolts[axis], ties[axis]
                own = components[0]["ownership"]
                require(
                    len(components) == 2
                    and all(
                        all(
                            r["ownership"][k] == own[k]
                            for k in ("first_body", "second_body", "point_mm", "role")
                        )
                        for r in components
                    ),
                    "mixed plane identities",
                )
                bodies = [own["first_body"], own["second_body"]]
                require(
                    set(bodies).issubset(bolt["receiver_member_ids"]),
                    "foreign receiver",
                )
                directions = np.array(
                    [r["ownership"]["direction_global_xyz"] for r in components]
                )
                axis_unit = local.unit(bolt["axis_xyz"])
                require(
                    np.max(abs(directions @ directions.T - np.eye(2))) < 1e-8
                    and np.max(abs(directions @ axis_unit)) < 1e-8,
                    "invalid lateral basis",
                )
                scalars = force[[r["row"] for r in components]]
                shear = (
                    scalars @ directions
                )  # Physical force on first body; second gets its negative.
                tension = float(force[tie["row"]])
                require(tension >= -1e-8, "compressive tensile-tie force")
                grains = [local.unit(members[b]["axis"]) for b in bodies]
                angles = [lateral.angle(shear, g) for g in grains]
                record = {
                    "case_id": case_id,
                    "axis_id": axis,
                    "plane_id": plane_id,
                    "duty_id": axis.rsplit("_", 1)[0],
                    "kind": bolt["kind"],
                    "first_body": bodies[0],
                    "second_body": bodies[1],
                    "point_x_mm": own["point_mm"][0],
                    "point_y_mm": own["point_mm"][1],
                    "point_z_mm": own["point_mm"][2],
                    "component_1_row": components[0]["row"],
                    "component_2_row": components[1]["row"],
                    "direction_1_xyz": json.dumps(directions[0].tolist()),
                    "direction_2_xyz": json.dumps(directions[1].tolist()),
                    "shear_component_1_n": float(scalars[0]),
                    "shear_component_2_n": float(scalars[1]),
                    "shear_x_n": float(shear[0]),
                    "shear_y_n": float(shear[1]),
                    "shear_z_n": float(shear[2]),
                    "shear_resultant_n": float(np.linalg.norm(shear)),
                    "tie_row": tie["row"],
                    "outer_tie_signed_n": tension,
                    "tie_first_body": tie["ownership"]["first_body"],
                    "tie_second_body": tie["ownership"]["second_body"],
                    "tie_direction_xyz": json.dumps(
                        tie["ownership"]["direction_global_xyz"]
                    ),
                    "first_load_to_grain_deg": angles[0],
                    "second_load_to_grain_deg": angles[1],
                    "first_bearing_length_mm": None,
                    "second_bearing_length_mm": None,
                    "reference_45ksi_n": None,
                    "ratio_45ksi": None,
                    "mode_45ksi": None,
                    "reference_92ksi_n": None,
                    "ratio_92ksi": None,
                    "mode_92ksi": None,
                    "reference_106ksi_n": None,
                    "ratio_106ksi": None,
                    "mode_106ksi": None,
                    "ideal_annulus_pressure_mpa": None,
                    "ideal_pressure_over_wood_reference": None,
                    "washer_reference_status": "RETAINED_DIMENSIONS_AND_SUPPORT_UNBOUND",
                }
                gap_ids = ["GROUP_GEOMETRY", "HARDWARE_AXIAL", "WASHER_TRANSFER"]
                if bolt["kind"] == "retained_bolt":
                    register = retained["axis_register"][axis]
                    receivers = {r["member"]: r for r in register["finished_receivers"]}
                    require(set(receivers) == set(bodies), "retained receivers differ")
                    lengths = [
                        receivers[b]["interval_from_axis_datum_mm"][1]
                        - receivers[b]["interval_from_axis_datum_mm"][0]
                        for b in bodies
                    ]
                    diameter = (
                        bolt["source_record"]["source_occupied_diameter_mm"] / 25.4
                    )
                    require(
                        math.isclose(
                            diameter,
                            register["hardware_policy"]["nominal_diameter_in"],
                            abs_tol=1e-10,
                        ),
                        "retained diameter differs",
                    )
                    require(
                        math.isclose(
                            sum(lengths),
                            bolt["source_record"]["source_grip_mm"],
                            abs_tol=1e-7,
                        ),
                        "retained grip differs",
                    )
                    require(
                        np.linalg.norm(
                            np.array(bolt["source_point_xyz_mm"])
                            + axis_unit
                            * receivers[bodies[0]]["interval_from_axis_datum_mm"][1]
                            - np.array(own["point_mm"])
                        )
                        < 1e-6,
                        "retained interface point differs",
                    )
                    for body, grain in zip(bodies, grains, strict=True):
                        require(
                            receivers[body]["finished_step"]["file_sha256"]
                            == members[body]["step_sha256"]
                            and abs(
                                grain
                                @ local.unit(
                                    receivers[body]["stock_frame"][
                                        "basis_columns_global_xyz"
                                    ][0]
                                )
                            )
                            > 1 - 1e-8,
                            "retained geometry/grain binding differs",
                        )
                    refs = retained_helper.lateral_references(
                        [
                            {
                                "member": b,
                                "bearing_length_in": length / 25.4,
                                "load_to_grain_degrees": angle,
                            }
                            for b, length, angle in zip(
                                bodies, lengths, angles, strict=True
                            )
                        ],
                        diameter,
                        record["shear_resultant_n"],
                        nds,
                    )
                    record["lateral_reference_status"] = (
                        "CONDITIONAL_RETAINED_SINGLE_SHEAR"
                    )
                    gap_ids.append("RETAINED_WASHER")
                    for name, ref in zip(("45ksi", "106ksi"), refs, strict=True):
                        record["reference_" + name + "_n"] = ref[
                            "single_fastener_unadjusted_reference_n"
                        ]
                        record["ratio_" + name] = ref[
                            "same_state_demand_divided_by_unadjusted_reference"
                        ]
                        record["mode_" + name] = ref["governing_mode"]
                    # Reuse the retained numerical helper's supplied-input modes;
                    # its public scenario wrapper fixes the other two Fyb values.
                    receiving = [
                        {
                            "bearing_length_in": length / 25.4,
                            "fe_theta_psi": nds._fe_theta_psi(
                                specific_gravity=0.5,
                                diameter_in=diameter,
                                angle_degrees=angle,
                            ),
                        }
                        for length, angle in zip(lengths, angles, strict=True)
                    ]
                    values = nds._single_shear_modes(
                        *receiving,
                        diameter,
                        grade5_yield_psi,
                        nds._reduction_terms(
                            diameter_in=diameter,
                            nominal_diameter_in=diameter,
                            angle_max_degrees=max(angles),
                        ),
                    )
                    record["reference_92ksi_n"] = (
                        min(values.values()) * lateral.N_PER_LBF
                    )
                    record["ratio_92ksi"] = (
                        record["shear_resultant_n"] / record["reference_92ksi_n"]
                    )
                    record["mode_92ksi"] = min(values, key=values.get)
                else:
                    geometry = bolt["source_record"]["geometry"]
                    require(
                        math.isclose(
                            geometry["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8
                        ),
                        "candidate diameter changed",
                    )
                    intervals = {
                        r["receiver_id"]: r[
                            "current_shaft_intersection_solid_intervals_from_underhead_mm"
                        ]
                        for r in geometry["wood_receiver_intervals"]
                    }
                    require(
                        all(
                            len(v) == 1 and v[0][1] > v[0][0]
                            for v in intervals.values()
                        ),
                        "ambiguous receiver intervals",
                    )
                    lengths = [intervals[b][0][1] - intervals[b][0][0] for b in bodies]
                    record["ideal_annulus_pressure_mpa"] = max(0.0, tension) / area
                    record["washer_reference_status"] = "IDEAL_FULL_ANNULUS_ONLY"
                    if axis == partial["axis_id"]:
                        gap_ids.append("PARTIAL_SEAT")
                        record["ideal_annulus_pressure_mpa"] = None
                        record["washer_reference_status"] = (
                            "PARTIAL_SUPPORT_EXCEPTION_NO_FULL_ANNULUS_REFERENCE"
                        )
                    if len(intervals) != 2:
                        record["lateral_reference_status"] = (
                            "MULTI_RECEIVER_NOT_SINGLE_SHEAR"
                        )
                        gap_ids.append("MULTI_RECEIVER")
                    elif any(abs(axis_unit @ g) > 1e-8 for g in grains):
                        record["lateral_reference_status"] = "END_GRAIN_METHOD_SEPARATE"
                        gap_ids.append("END_GRAIN")
                    else:
                        record["lateral_reference_status"] = (
                            "CONDITIONAL_CANDIDATE_SINGLE_SHEAR"
                        )
                        for fyb, name in (
                            (45000, "45ksi"),
                            (grade5_yield_psi, "92ksi"),
                            (106000, "106ksi"),
                        ):
                            ref = lateral.reference(lengths, angles, fyb)
                            value = ref["reference_lateral_lbf"] * lateral.N_PER_LBF
                            record["reference_" + name + "_n"] = value
                            record["ratio_" + name] = (
                                record["shear_resultant_n"] / value
                            )
                            record["mode_" + name] = ref["governing_mode"]
                (
                    record["first_bearing_length_mm"],
                    record["second_bearing_length_mm"],
                ) = lengths
                record["gap_ids"] = ";".join(gap_ids)
                records.append(record)
            # One outer-tie/washer record per physical bolt; never duplicate a three-receiver tie.
            for axis in sorted(included):
                bolt = bolts[axis]
                tie = ties[axis]
                tension = float(force[tie["row"]])
                for body in (
                    tie["ownership"]["first_body"],
                    tie["ownership"]["second_body"],
                ):
                    alignment = abs(
                        local.unit(bolt["axis_xyz"]) @ local.unit(members[body]["axis"])
                    )
                    route, fc = (
                        ("PERPENDICULAR_BASE_REFERENCE", fc_perp)
                        if alignment < 1e-8
                        else ("PARALLEL_BASE_REFERENCE_ONLY", fc_parallel)
                        if alignment > 1 - 1e-8
                        else ("OBLIQUE_METHOD_UNBOUND", None)
                    )
                    pressure = (
                        max(0.0, tension) / area
                        if bolt["kind"] == "candidate_bolt"
                        else None
                    )
                    partial_seat = (
                        axis == partial["axis_id"] and body == partial["member"]
                    )
                    if partial_seat:
                        pressure = None
                    seat_records.append(
                        {
                            "case_id": case_id,
                            "axis_id": axis,
                            "member": body,
                            "outer_tie_signed_n": tension,
                            "axis_grain_absolute_dot": float(alignment),
                            "wood_reference_route": route,
                            "wood_reference_mpa": fc,
                            "ideal_full_annulus_area_mm2": area
                            if pressure is not None
                            else None,
                            "ideal_annulus_pressure_mpa": pressure,
                            "ideal_pressure_over_wood_reference": pressure / fc
                            if pressure is not None and fc is not None
                            else None,
                            "known_partial_support": partial_seat,
                            "full_annulus_reference_applicable": pressure is not None,
                            "actual_supported_pressure_mpa": None,
                            "washer_metal_resistance_n": None,
                        }
                    )
    seat_for = defaultdict(list)
    for seat in seat_records:
        seat_for[(seat["case_id"], seat["axis_id"])].append(seat)
    for record in records:
        ratios = [
            s["ideal_pressure_over_wood_reference"]
            for s in seat_for[(record["case_id"], record["axis_id"])]
            if s["ideal_pressure_over_wood_reference"] is not None
        ]
        record["ideal_pressure_over_wood_reference"] = (
            max(ratios) if ratios and record["axis_id"] != partial["axis_id"] else None
        )
    duties = defaultdict(list)
    for record in records:
        duties[record["duty_id"]].append(record)
    priorities = []
    for duty_id, states in sorted(duties.items()):
        eligible = [s for s in states if s["ratio_106ksi"] is not None]
        pressure_states = [
            s for s in states if s["ideal_pressure_over_wood_reference"] is not None
        ]
        priorities.append(
            {
                "duty_id": duty_id,
                "kind": states[0]["kind"],
                "axis_ids": sorted({s["axis_id"] for s in states}),
                "receivers": sorted(
                    {b for s in states for b in (s["first_body"], s["second_body"])}
                ),
                "plane_state_count": len(states),
                "peak_shear": state_ref(
                    max(states, key=lambda s: s["shear_resultant_n"])
                ),
                "peak_tension": state_ref(
                    max(states, key=lambda s: s["outer_tie_signed_n"])
                ),
                "governing_45ksi": state_ref(
                    max(eligible, key=lambda s: s["ratio_45ksi"])
                )
                if eligible
                else None,
                "governing_106ksi": state_ref(
                    max(eligible, key=lambda s: s["ratio_106ksi"])
                )
                if eligible
                else None,
                "governing_92ksi": state_ref(
                    max(eligible, key=lambda s: s["ratio_92ksi"])
                )
                if eligible
                else None,
                "peak_ideal_wood_pressure": state_ref(
                    max(
                        pressure_states,
                        key=lambda s: s["ideal_pressure_over_wood_reference"],
                    )
                )
                if pressure_states
                else None,
                "gap_ids": sorted({g for s in states for g in s["gap_ids"].split(";")}),
            }
        )
    counts = {
        "cases": len(CASES),
        "candidate_axes": 80,
        "retained_axes": 12,
        "physical_axes": len(included),
        "lateral_interfaces": len(planes),
        "plane_states": len(records),
        "outer_seat_states": len(seat_records),
        "partial_support_exception_seat_states": sum(
            s["known_partial_support"] for s in seat_records
        ),
        "duties": len(priorities),
        "lateral_status_states": dict(
            Counter(r["lateral_reference_status"] for r in records)
        ),
    }
    require(
        counts["plane_states"] == 576
        and counts["outer_seat_states"] == 1104
        and counts["duties"] == 46,
        "incomplete screen census",
    )
    for path, digest in PINS.items():
        require(sha(path) == digest, "source changed during arithmetic: " + str(path))
    OUTPUT.mkdir(parents=True)
    (OUTPUT / ".gitignore").write_text("*\n")
    (OUTPUT / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write_csv(OUTPUT / "bolt-states.csv", records)
    write_csv(OUTPUT / "washer-reference-states.csv", seat_records)
    write_json(
        OUTPUT / "source-pins.json",
        {
            "rechecked_sha256": {str(p): d for p, d in sorted(PINS.items())},
            "frame_source_pins": comparison["source_sha256"],
            "retained_geometry_inherited_pins": retained["rechecked_load_input_pins"],
            "retained_geometry_pin_recheck": "Frozen geometry register reused; only consumed same-state helpers and frame source bindings are rechecked here, not its earlier native-response/acceptance pipeline.",
        },
    )
    eligible = [r for r in records if r["ratio_106ksi"] is not None]
    report = {
        "schema": "remaining_nominal_gap_joint_screen/v1",
        "candidate": model["candidate"],
        "source_revision": model["source_revision"],
        "development_revision": model["development_revision"],
        "source_comparison_sha256": PINS[GAP / "comparison.json"],
        "source_response_sha256": PINS[GAP / "response.npz"],
        "source_comparison_path": str((GAP / "comparison.json").relative_to(ROOT)),
        "source_response_path": str((GAP / "response.npz").relative_to(ROOT)),
        "source_clearance_schema": comparison["schema"],
        "source_force_state_scope": force_scope,
        "source_clearance_scope": clearance_scope,
        "source_force_key": "case_id + '_gap_raw_force_n'",
        "gap_scale": 1.0,
        "producer_sha256": PINS[Path(__file__)],
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "counts": counts,
        "case_ids": list(CASES),
        "excluded_top_prefixes": EXCLUDED_PREFIXES,
        "excluded_top_axes": sorted(excluded_top),
        "excluded_worker_block": WORKER_BLOCK,
        "excluded_worker_axes": sorted(excluded_worker),
        "wood_reference_mpa": {"Fc_perpendicular": fc_perp, "Fc_parallel": fc_parallel},
        "quarter_inch_minimum_annulus": annulus,
        "conditional_grade5_92ksi_basis": {
            "Fyb_scenario_psi": grade5_yield_psi,
            "source": str(local.FASTENERS.relative_to(ROOT)),
            "basis": "Declared SAE J429 Grade 5 1/4-through-1-inch minimum tensile-yield scenario used as conditional Fyb; the applicable ASTM F606/product/test basis remains unverified. No exact product or guaranteed Fyb is established.",
            "adopted_or_product_qualified": False,
        },
        "partial_seat_geometry": partial,
        "partial_support_axial_ties_n": {
            r["case_id"]: r["outer_tie_signed_n"]
            for r in records
            if r["axis_id"] == partial["axis_id"]
        },
        "partial_support_tie_row": ties[partial["axis_id"]]["row"],
        "duties": priorities,
        "gap_definitions": GAPS,
        "peak_45ksi": state_ref(max(eligible, key=lambda r: r["ratio_45ksi"])),
        "peak_106ksi": state_ref(max(eligible, key=lambda r: r["ratio_106ksi"])),
        "peak_92ksi": state_ref(max(eligible, key=lambda r: r["ratio_92ksi"])),
        "above_one_45ksi_axes": sorted(
            {r["axis_id"] for r in eligible if r["ratio_45ksi"] > 1}
        ),
        "above_one_106ksi_axes": sorted(
            {r["axis_id"] for r in eligible if r["ratio_106ksi"] > 1}
        ),
        "above_one_92ksi_axes": sorted(
            {r["axis_id"] for r in eligible if r["ratio_92ksi"] > 1}
        ),
        "source_frame_limits": comparison["limits"],
        "sign_convention": "q = direction dot (u_second - u_first); positive scalar gives +f*direction on first body and its negative on second. Outer tie is positive tension; signed raw values are preserved. max(0,T) is used only for ideal washer pressure.",
        "assumptions": [
            f"The six saved nominal-gap same-state frame forces are reused without solving. Explicit circular clearance applies to {clearance_scope}; other lateral rows retain the source zero-gap stiffness assumption.",
            "Candidate lateral references reuse D=6.35mm, SG=0.50, Fe parallel/perpendicular 5600/4450psi, raw receiver lengths, zero intermember gap and full smooth bearing diameter. Retained references reuse their bound finished bore intervals and diameter-dependent NDS bearing helper.",
            "Fyb=45ksi and 106ksi are unadopted hypotheses; 45ksi is not a quarter-inch table entitlement, and 106ksi is an estimate, not an exact-product minimum. References precede group, geometry and service adjustments; no preload/friction is credited.",
            "Fyb=92ksi uses the declared Grade 5 minimum tensile-yield scenario under the same conditional ASTM F606 basis as the parent's top-corner work. Product conformity and applicable Fyb test/evaluation remain unverified; this is not a guaranteed exact-product capacity or complete joint acceptance.",
            "Wood pressure uses dry normal-duration DF-L No.2 base Fc perpendicular=625psi or parallel=1350psi, with no factor increase. The parallel comparison is a base-property reference, not an adopted local bearing resistance.",
            "Quarter-inch pressure assumes the entire centered 0.727in OD/0.327in ID annulus is uniformly supported. The known partial nut seat and its bolt plane rows have no full-annulus pressure/ratio; its opposite outer seat retains only its own ideal reference. Actual supported pressures and all washer metal capacities remain null. The parent's supported-bearing option is not developed here.",
            "Outer tension is not a local bolt-section interaction demand. Separate multi-receiver plane magnitudes are never added, and component maxima from different cases are never combined.",
            "The 66 Hillman axes retain unsupported parametric properties in the saved frame; no screw resistance, stiffness qualification or physical inspection is supplied here.",
        ],
        "output_sha256": {
            n: sha(OUTPUT / n)
            for n in (
                "bolt-states.csv",
                "washer-reference-states.csv",
                "source-pins.json",
                "producer.py.snapshot",
            )
        },
        "native_solve_run": False,
        "frame_solve_run": False,
        "hardware_selected": False,
        "reviewed_geometry_changed": False,
        "complete_joint_acceptance": False,
        "physical_release": False,
    }
    write_json(OUTPUT / "screen.json", report)
    print(
        json.dumps(
            {
                "counts": counts,
                "peak_45ksi": report["peak_45ksi"],
                "peak_106ksi": report["peak_106ksi"],
                "peak_92ksi": report["peak_92ksi"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clearance",
        type=Path,
        default=GAP,
        help="Saved clearance directory or its comparison.json; no solve is run.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Fresh directory under an owned remaining-joint-screen-attempt path.",
    )
    args = parser.parse_args()
    main(args.clearance, args.output)
