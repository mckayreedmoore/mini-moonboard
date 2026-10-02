"""Join the four continuous knee bolts in six saved nominal-gap frame states.

The asymmetric utilization sum is a declared convex-superposition screen,
not an NDS three-member resistance or a complete-joint qualification.
Only saved-array arithmetic is performed; existing evidence is never replaced.
"""

import argparse
import json
import math
import platform
import sys
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True

import numpy as np
import remaining_joint_screen as remaining

from mini_moonboard import bolted_wood_wood_double_shear as double
from mini_moonboard import nds_2024_multi_member_bolt_yield as nds

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = remaining.lateral.BASE
FRAME = HERE / "corner-frame-attempt01"
GAP = HERE / "top-and-service-frame-attempt02"
OUTPUT = HERE / "three-member-screen-attempt01"
ORDER = (
    BASE / "bolt-groups/three-member-stack-order-attempt01/receiver-stack-order.json"
)
PROFILE = BASE / "current-knee-three-member-profile-attempt01/query.json"
PROFILE_PINS = PROFILE.parent / "source-pins.json"
OLD_NOTE = BASE / "current-knee-three-member-transfer-attempt01/README.md"
AXES = tuple(
    f"knee_outer_{side}_side_{i}" for side in ("left", "right") for i in (1, 2)
)
SCENARIOS = {"45ksi": 45000.0, "92ksi": 92000.0}
read, require, sha = remaining.read, remaining.require, remaining.sha
unit, lateral = remaining.local.unit, remaining.lateral
wrench = remaining.local.actions_method.wrench
PINS = {
    ORDER: "e6a6d242ae2a62ecefafc4acbe8f3ea78a916aac4f48f53bdff84ec3c773055e",
    PROFILE: "5c820231ac4434e896ee708c72128672424ff158b3ee4458197cdadc1a4b0854",
    PROFILE_PINS: "629552eba2b3dd2639df245dde56afb46dae7c01d2b2b9b1d774f98ca4a846c7",
    OLD_NOTE: "97d671c5bec0832ddae71f496249d0b1cfc4aef0e63b9b75d3b9912f133e3e03",
    HERE
    / "remaining_joint_screen.py": "4e2704590dc009194953425c594a38f288c9b47de4385dd3542b18ad76b217c1",
    ROOT
    / "mini_moonboard/nds_2024_multi_member_bolt_yield.py": "575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89",
    ROOT
    / "mini_moonboard/bolted_wood_wood_double_shear.py": "46a7be4202f32bdcb4631c6137574204f64aa44365b582ebe2369319052afcbd",
    ROOT
    / "mini_moonboard/bolted_timber_checks.py": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    **lateral.PINS,
    remaining.local.FASTENERS: remaining.local.PINS[remaining.local.FASTENERS],
    remaining.local.actions_method.MATERIALS: remaining.local.actions_method.PINS[
        remaining.local.actions_method.MATERIALS
    ],
}
CLEARANCE_PINS = {
    "top-and-service-frame-attempt02": {
        "comparison.json": "4aa32390c80f803faee4fceeb6460c05b665dd8e970beaef89b40985b0b9555b",
        "response.npz": "227b9381a6ff19286ba4b46c81bc5852bb3b536735ac5c74f727f6869a5f40d6",
    },
    "all-outer-corner-frame-attempt01": {
        "comparison.json": "ec69b49c821a56fdde76d94148405f9f743e4f72add17c89d35af512be76f6a3",
        "response.npz": "aa70480aa18c33bb1cbd7d3a53ff582a0c7a90c93487f92721619474ec251901",
    },
}
GAPS = {
    "CONVEX_ENDPOINTS": "Establish that each complete two-member endpoint load/wrench state is admissible in this same three-member assembly and that its lateral admissible set is convex. The utilization sum is conditional on both propositions; they are not validated here.",
    "SHARED_BOLT": "Bind compatible bearing distributions, rotations and bending along the continuous 215.9 mm grip, including the middle receiver and both planes. Interface transfer moments are not recovered steel bending moments.",
    "AXIAL_LATERAL": "Resolve simultaneous outer-seat tie tension, bolt bending/lateral interaction, supported washer pressure and washer/head/nut metal transfer. Face-contact forces are kept separately and are not assigned to individual bolts.",
    "ADJUSTMENTS_GROUP": "Determine applicable Z-prime adjustments including Cdelta and Cg for two obliquely spaced bolts with unequal, sometimes opposing vectors; no bolt-count capacity multiplier is used.",
    "FINISHED_WOOD": "Bind signed finished end/edge/spacing, splitting, net sections and tear-out for each receiver. BG003 reuses only the recorded 72 sampled profile rays, with internal bores and an oblique middle-member end; BG004 has no consumed corresponding finished-profile query.",
    "DELIVERED_INPUTS": "Confirm the conditional species/grade/grain, face contact, bolt product/Fyb basis, actual diameter, thread-bearing intervals and nut engagement. The 92 ksi and smooth-body scenarios are not delivered-part findings; 45 ksi is an unadopted quarter-inch sensitivity.",
    "CORNER_FRAME": "Parent must reconcile these local receiver wrenches with the post/spine and inner-block/header chains and the frame's floor, panel/screw, stiffness and clearance assumptions. Accounting closure here does not qualify those paths.",
}


def bind(path, digest):
    require(
        path not in PINS or PINS[path] == digest, "conflicting source: " + str(path)
    )
    PINS[path] = digest


def unchanged():
    for path, digest in PINS.items():
        require(sha(path) == digest, "changed source: " + str(path))


def vector_columns(prefix, vector):
    return {f"{prefix}_{a}": float(v) for a, v in zip("xyz", vector, strict=True)}


def packed_wrench(actions, datum):
    value = wrench(actions, datum)
    return {
        "force_xyz_n": value[:3].tolist(),
        "moment_xyz_nmm": value[3:].tolist(),
        "force_resultant_n": float(np.linalg.norm(value[:3])),
        "moment_resultant_nmm": float(np.linalg.norm(value[3:])),
    }


def action(body, point, force, kind, row_ids):
    return {
        "body": body,
        "point_mm": np.asarray(point).tolist(),
        "force_n": np.asarray(force).tolist(),
        "free_moment_nmm": [0.0, 0.0, 0.0],
        "kind": kind,
        "row_ids": row_ids,
    }


def plane_actions(components, force, kind):
    own = components[0]["ownership"]
    require(
        all(
            all(
                r["ownership"][k] == own[k]
                for k in ("first_body", "second_body", "point_mm", "role")
            )
            for r in components
        ),
        "mixed plane ownership",
    )
    directions = np.array([r["ownership"]["direction_global_xyz"] for r in components])
    scalars = force[[r["row"] for r in components]]
    vector = scalars @ directions
    points = own["point_mm"]
    ids = [r["row_id"] for r in components]
    return vector, [
        action(own["first_body"], points, vector, kind, ids),
        action(own["second_body"], points, -vector, kind, ids),
    ]


def geometry(bolt, ordered, planes, tie, members):
    g = bolt["source_record"]["geometry"]
    intervals = {}
    for receiver in g["wood_receiver_intervals"]:
        spans = receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
        require(
            len(spans) == 1 and spans[0][1] > spans[0][0], "ambiguous bearing interval"
        )
        intervals[receiver["receiver_id"]] = spans[0]
    ids = [r["receiver_id"] for r in ordered["head_to_nut_geometric_receiver_order"]]
    require(
        set(ids) == set(intervals) == set(bolt["receiver_member_ids"]),
        "receiver census differs",
    )
    require(len(ids) == 3 and len(planes) == 2, "not one three-member/two-plane bolt")
    axis = unit(bolt["axis_xyz"])
    underhead = (
        np.array(g["shaft_center_global_xyz_mm"])
        - axis * g["modeled_underhead_to_tip_mm"] / 2
    )
    lengths = [intervals[b][1] - intervals[b][0] for b in ids]
    require(
        np.allclose(lengths, [38.1, 88.9, 88.9], atol=1e-7, rtol=0), "knee grip changed"
    )
    require(
        math.isclose(g["wood_grip_material_length_mm"], sum(lengths), abs_tol=1e-7),
        "grip differs",
    )
    require(
        math.isclose(g["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8),
        "diameter differs",
    )
    require(
        np.linalg.norm(axis - ordered["head_to_nut_unit_global_xyz"]) < 1e-8,
        "axis/order differs",
    )
    for i, receiver in enumerate(ordered["head_to_nut_geometric_receiver_order"]):
        require(
            np.allclose(
                intervals[ids[i]], [receiver["start_mm"], receiver["end_mm"]], atol=1e-8
            ),
            "stack interval differs",
        )
        require(abs(axis @ unit(members[ids[i]]["axis"])) < 1e-8, "end-grain axis")
        if i < 2:
            require(
                abs(intervals[ids[i]][1] - intervals[ids[i + 1]][0]) < 1e-7,
                "intermember gap",
            )
            own = planes[i][0]["ownership"]
            require(
                (own["first_body"], own["second_body"]) == tuple(ids[i : i + 2]),
                "wrong plane order",
            )
            require(
                np.linalg.norm(
                    underhead + axis * intervals[ids[i]][1] - own["point_mm"]
                )
                < 1e-6,
                "interface point differs",
            )
            directions = np.array(
                [r["ownership"]["direction_global_xyz"] for r in planes[i]]
            )
            require(
                len(planes[i]) == 2
                and np.max(abs(directions @ directions.T - np.eye(2))) < 1e-8
                and np.max(abs(directions @ axis)) < 1e-8,
                "invalid lateral basis",
            )
    own = tie["ownership"]
    require(
        (own["first_body"], own["second_body"]) == (ids[0], ids[2]),
        "outer tie receivers differ",
    )
    require(
        tie["law"]["intended_law"] == "tension_only"
        and np.linalg.norm(axis - own["direction_global_xyz"]) < 1e-8,
        "outer tie law/direction differs",
    )
    head = underhead + axis * intervals[ids[0]][0]
    nut = underhead + axis * intervals[ids[2]][1]
    require(np.linalg.norm(head - own["point_mm"]) < 1e-6, "head seat differs")
    return {
        "receiver_order": ids,
        "bearing_lengths_mm": lengths,
        "receiver_intervals_from_underhead_mm": intervals,
        "grain_xyz": [unit(members[b]["axis"]).tolist() for b in ids],
        "bolt_axis_xyz": axis.tolist(),
        "modeled_wood_grip_mm": sum(lengths),
        "modeled_shaft_occupancy_mm": g["modeled_underhead_to_tip_mm"],
        "head_seat_point_mm": head.tolist(),
        "nut_seat_point_mm": nut.tolist(),
        "interface_points_mm": [p[0]["ownership"]["point_mm"] for p in planes],
        "datum_mm": np.mean(
            [p[0]["ownership"]["point_mm"] for p in planes], axis=0
        ).tolist(),
        "actual_thread_bearing_lengths_mm": None,
        "physical_head_to_nut_order_verified": False,
    }


def bolt_state(case_id, axis_id, g, planes, tie, force):
    actions, plane_records = [], []
    for i, components in enumerate(planes):
        vector, paired = plane_actions(components, force, "bolt_lateral")
        actions.extend(paired)
        angles = [lateral.angle(vector, grain) for grain in g["grain_xyz"][i : i + 2]]
        refs = {}
        for label, fyb in SCENARIOS.items():
            result = lateral.reference(g["bearing_lengths_mm"][i : i + 2], angles, fyb)
            # Reuse the maintained NDS input/mode helpers at these same inputs.
            receiving = [
                {
                    "bearing_length_in": length / 25.4,
                    "fe_theta_psi": nds._fe_theta_psi(
                        specific_gravity=0.5, diameter_in=0.25, angle_degrees=theta
                    ),
                }
                for length, theta in zip(
                    g["bearing_lengths_mm"][i : i + 2], angles, strict=True
                )
            ]
            modes = nds._single_shear_modes(
                *receiving,
                0.25,
                fyb,
                nds._reduction_terms(
                    diameter_in=0.25,
                    nominal_diameter_in=0.25,
                    angle_max_degrees=max(angles),
                ),
            )
            require(
                all(
                    math.isclose(modes[k], v, rel_tol=1e-12)
                    for k, v in result["reference_values_lbf"].items()
                ),
                "maintained reference helpers disagree",
            )
            reference = result["reference_lateral_lbf"] * lateral.N_PER_LBF
            refs[label] = {
                "reference_n": reference,
                "utilization": float(np.linalg.norm(vector)) / reference,
                "governing_mode": result["governing_mode"],
                "mode_references_n": {
                    k: v * lateral.N_PER_LBF for k, v in modes.items()
                },
            }
        plane_records.append(
            {
                "plane_id": components[0]["row_id"],
                "raw_rows": [r["row"] for r in components],
                "directions_xyz": [
                    r["ownership"]["direction_global_xyz"] for r in components
                ],
                "signed_components_n": force[[r["row"] for r in components]].tolist(),
                "first_body": paired[0]["body"],
                "second_body": paired[1]["body"],
                "point_mm": paired[0]["point_mm"],
                "force_on_first_xyz_n": vector.tolist(),
                "force_resultant_n": float(np.linalg.norm(vector)),
                "load_to_grain_deg": angles,
                "bearing_strengths_psi": [lateral.bearing(a) for a in angles],
                "single_shear_endpoint_references": refs,
            }
        )
    outer = [
        np.array(plane_records[0]["force_on_first_xyz_n"]),
        -np.array(plane_records[1]["force_on_first_xyz_n"]),
    ]
    magnitudes = [float(np.linalg.norm(v)) for v in outer]
    require(
        min(magnitudes) > 1e-10,
        "zero outer action needs a separate symmetry convention",
    )
    difference = float(np.linalg.norm(outer[0] - outer[1]))
    tolerance = 1e-8 + 1e-10 * max(magnitudes)
    symmetric = difference <= tolerance and math.isclose(
        plane_records[0]["load_to_grain_deg"][0],
        plane_records[1]["load_to_grain_deg"][1],
        abs_tol=1e-8,
    )
    direct_double = {}
    # Do not equalize actual actions. The double-shear helper is called only
    # when complete signed vectors establish its symmetric action pattern.
    if symmetric:
        direction = outer[0] + outer[1]
        angles = [lateral.angle(direction, grain) for grain in g["grain_xyz"]]
        for label, fyb in SCENARIOS.items():
            direct_double[label] = double.wood_wood_double_shear_reference(
                main_bearing_length_in=g["bearing_lengths_mm"][1] / 25.4,
                side_a_bearing_length_in=g["bearing_lengths_mm"][0] / 25.4,
                side_b_bearing_length_in=g["bearing_lengths_mm"][2] / 25.4,
                main_load_to_grain_degrees=angles[1],
                side_a_load_to_grain_degrees=angles[0],
                side_b_load_to_grain_degrees=angles[2],
                main_bolt_axis_parallel_to_grain=False,
                side_a_bolt_axis_parallel_to_grain=False,
                side_b_bolt_axis_parallel_to_grain=False,
                bolt_full_body_diameter_in=0.25,
                bolt_thread_root_diameter_in=0.25,
                main_thread_bearing_length_in=0,
                side_a_thread_bearing_length_in=0,
                side_b_thread_bearing_length_in=0,
                bolt_bending_yield_strength_psi=fyb,
                side_a_gap_in=0,
                side_b_gap_in=0,
                symmetric_side_actions_established=True,
            )
    tension = float(force[tie["row"]])
    require(tension >= -1e-8, "compressive outer tie")
    axial = tension * np.array(g["bolt_axis_xyz"])
    for body, point, vector in zip(
        (g["receiver_order"][0], g["receiver_order"][2]),
        (g["head_seat_point_mm"], g["nut_seat_point_mm"]),
        (axial, -axial),
        strict=True,
    ):
        actions.append(action(body, point, vector, "outer_tie", [tie["row_id"]]))
    receivers = {}
    for body in g["receiver_order"]:
        local_actions = [a for a in actions if a["body"] == body]
        receivers[body] = {
            kind: packed_wrench(
                [a for a in local_actions if kind == "total" or a["kind"] == kind],
                g["datum_mm"],
            )
            for kind in ("bolt_lateral", "outer_tie", "total")
        }
    total = sum(
        (
            wrench([a for a in actions if a["body"] == b], g["datum_mm"])
            for b in g["receiver_order"]
        ),
        np.zeros(6),
    )
    require(
        np.linalg.norm(total[:3]) < 1e-8 and np.linalg.norm(total[3:]) < 1e-7,
        "bolt accounting does not close",
    )
    record = {
        "case_id": case_id,
        "axis_id": axis_id,
        "datum_mm": g["datum_mm"],
        "planes": plane_records,
        "receiver_wrenches": receivers,
        "outer_tie_signed_n": tension,
        "tie_raw_row": tie["row"],
        "outer_vector_difference_n": difference,
        "outer_vector_difference_over_larger_outer": difference / max(magnitudes),
        "outer_magnitude_ratio": min(magnitudes) / max(magnitudes),
        "outer_vector_angle_deg": math.degrees(
            math.acos(
                float(np.clip(outer[0] @ outer[1] / math.prod(magnitudes), -1, 1))
            )
        ),
        "symmetry_tolerance_n": tolerance,
        "symmetric_double_shear_action_applicable": symmetric,
        "direct_double_shear_references": direct_double or None,
        "conditional_convex_utilization_sum": {
            label: sum(
                p["single_shear_endpoint_references"][label]["utilization"]
                for p in plane_records
            )
            for label in SCENARIOS
        },
        "accounting_force_residual_n": float(np.linalg.norm(total[:3])),
        "accounting_moment_residual_nmm": float(np.linalg.norm(total[3:])),
        "normative_asymmetric_reference_n": None,
        "complete_joint_acceptance": False,
    }
    return record, actions


def group_state(
    case_id,
    stack,
    geometry_by_axis,
    bolt_records,
    actions,
    contact_rows,
    force,
    members,
):
    axes, bodies = stack["axis_ids"], stack["head_to_nut_geometric_receiver_order"]
    datum = np.mean([geometry_by_axis[a]["datum_mm"] for a in axes], axis=0)
    pitch = (
        np.array(geometry_by_axis[axes[1]]["datum_mm"])
        - geometry_by_axis[axes[0]]["datum_mm"]
    )
    contact_records = []
    for row in contact_rows:
        own = row["ownership"]
        require(row["law"]["intended_law"] == "compression_only", "wrong contact law")
        require(float(force[row["row"]]) >= -1e-8, "negative contact force")
        vector, paired = plane_actions([row], force, "face_contact")
        actions.extend(paired)
        contact_records.append(
            {
                "raw_row": row["row"],
                "row_id": row["row_id"],
                "first_body": own["first_body"],
                "second_body": own["second_body"],
                "point_mm": own["point_mm"],
                "compression_n": float(force[row["row"]]),
                "force_on_first_xyz_n": vector.tolist(),
            }
        )
    receivers = {
        b: {
            kind: packed_wrench(
                [
                    a
                    for a in actions
                    if a["body"] == b and (kind == "total" or a["kind"] == kind)
                ],
                datum,
            )
            for kind in ("bolt_lateral", "outer_tie", "face_contact", "total")
        }
        for b in bodies
    }
    interfaces = []
    for i in range(2):
        point = np.mean(
            [geometry_by_axis[a]["interface_points_mm"][i] for a in axes], axis=0
        )
        interface_actions = [
            a
            for a in actions
            if a["kind"] == "bolt_lateral"
            and a["body"] == bodies[i]
            and abs(
                (np.array(a["point_mm"]) - point)
                @ np.array(geometry_by_axis[axes[0]]["bolt_axis_xyz"])
            )
            < 1e-6
        ]
        interfaces.append(
            {
                "headward_body": bodies[i],
                "nutward_body": bodies[i + 1],
                "interface_pair_center_mm": point.tolist(),
                "lateral_wrench_on_headward_about_pair_center": packed_wrench(
                    interface_actions, point
                ),
            }
        )
    total = sum(
        (wrench([a for a in actions if a["body"] == b], datum) for b in bodies),
        np.zeros(6),
    )
    require(
        np.linalg.norm(total[:3]) < 1e-8 and np.linalg.norm(total[3:]) < 1e-7,
        "group accounting does not close",
    )
    return {
        "case_id": case_id,
        "group_id": stack["group_id"],
        "axis_ids": axes,
        "receiver_order": bodies,
        "datum_mm": datum.tolist(),
        "bolt_pitch_xyz_mm": pitch.tolist(),
        "bolt_pitch_mm": float(np.linalg.norm(pitch)),
        "receiver_pitch_grain_crossgrain_mm": {
            b: [
                float(pitch @ unit(members[b]["axis"])),
                float(
                    pitch
                    @ unit(
                        np.cross(
                            unit(members[b]["axis"]),
                            geometry_by_axis[axes[0]]["bolt_axis_xyz"],
                        )
                    )
                ),
            ]
            for b in bodies
        },
        "receiver_wrenches": receivers,
        "interfaces": interfaces,
        "contact_states": contact_records,
        "maximum_individual_bolt_utilization_sum": {
            label: max(
                r["conditional_convex_utilization_sum"][label] for r in bolt_records
            )
            for label in SCENARIOS
        },
        "sum_outer_ties_n": sum(r["outer_tie_signed_n"] for r in bolt_records),
        "interface_contact_compression_n": [
            sum(
                c["compression_n"]
                for c in contact_records
                if {c["first_body"], c["second_body"]} == set(bodies[i : i + 2])
            )
            for i in range(2)
        ],
        "accounting_force_residual_n": float(np.linalg.norm(total[:3])),
        "accounting_moment_residual_nmm": float(np.linalg.norm(total[3:])),
        "complete_group_qualification": False,
    }


def profile_states(records, geometry_by_axis, query):
    result = []
    for record in records:
        axis_id = record["axis_id"]
        if "_right_" in axis_id:
            continue  # The consumed query covers BG003 only; do not mirror it.
        g = geometry_by_axis[axis_id]
        for body, grain in zip(g["receiver_order"], g["grain_xyz"], strict=True):
            vector = np.array(
                record["receiver_wrenches"][body]["bolt_lateral"]["force_xyz_n"]
            )
            e = unit(np.cross(grain, g["bolt_axis_xyz"]))
            row = {
                "case_id": record["case_id"],
                "axis_id": axis_id,
                "receiver": body,
                "signed_grain_action_n": float(vector @ grain),
                "signed_crossgrain_action_n": float(vector @ e),
            }
            for component, value in (
                ("g", row["signed_grain_action_n"]),
                ("e", row["signed_crossgrain_action_n"]),
            ):
                label = component + ("+" if value >= 0 else "-")
                rays = [
                    r
                    for r in query["rays"]
                    if r["bolt_id"] == axis_id
                    and r["member_id"] == body
                    and r["ray_label"] == label
                ]
                require(len(rays) == 3, "missing profile stations")
                distance = min(r["center_to_last_material_exit_mm"] for r in rays)
                row[component + "_selected_ray"] = label
                row[component + "_minimum_sampled_terminal_distance_mm"] = distance
                row[component + "_distance_over_nominal_d"] = distance / 6.35
                row[component + "_all_terminal_faces_square"] = all(
                    math.isclose(f["abs_normal_dot_ray"], 1, abs_tol=1e-8)
                    for r in rays
                    for f in r["terminal_face_candidates"]
                )
                row[component + "_internal_void_intervals_by_station_mm"] = json.dumps(
                    [r["initial_and_intermediate_void_intervals_mm"] for r in rays]
                )
            result.append(row)
    return result


def main(clearance, output):
    global GAP
    GAP = clearance.resolve()
    if GAP.name == "comparison.json":
        GAP = GAP.parent
    output = output.resolve()
    require(
        output == OUTPUT or output.is_relative_to(OUTPUT),
        "output must be inside three-member-screen-attempt01",
    )
    require(
        not output.exists(), "preserve existing output; choose a fresh child directory"
    )
    unchanged()
    comparison = read(GAP / "comparison.json")
    require(
        comparison["schema"]
        in (
            "coupled_top_and_service_frame_clearance/v1",
            "coupled_outer_corner_frame_clearance/v1",
        ),
        "wrong clearance source",
    )
    known = CLEARANCE_PINS.get(GAP.name)
    if known is not None:
        require(
            GAP == (HERE / GAP.name).resolve(), "known source in unexpected directory"
        )
    bind(
        GAP / "comparison.json",
        known["comparison.json"] if known else sha(GAP / "comparison.json"),
    )
    bind(
        GAP / "response.npz",
        known["response.npz"] if known else comparison["response_sha256"],
    )
    require(
        comparison["response_sha256"] == PINS[GAP / "response.npz"],
        "response binding differs",
    )
    require(
        len(comparison["states"]) == 12
        and {(s["case_id"], s["gap_scale"]) for s in comparison["states"]}
        == {(c, g) for c in remaining.CASES for g in (0.0, 1.0)}
        and all(
            s["status"] == "PASS_CONDITIONAL_COUPLED_FRAME_LAWS"
            for s in comparison["states"]
        ),
        "incomplete source census",
    )
    for relative, digest in comparison["source_sha256"].items():
        bind(ROOT / relative, digest)
    bind(GAP / "producer.py.snapshot", comparison["producer_sha256"])
    assessment, frame_inputs = (
        read(FRAME / "operator-assessment.json"),
        read(FRAME / "inputs.json"),
    )
    require(
        assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
        and assessment["source_sha256"] == frame_inputs["source_sha256"],
        "frame assessment differs",
    )
    for name, digest in assessment["output_sha256"].items():
        require(PINS[FRAME / name] == digest, "frame/gap binding differs")
    bind(
        FRAME / "inputs.json",
        "27b6431f88d86bb1f6b877e19177ae01c785b851a7edf80c6176674338b68510",
    )
    bind(FRAME / "corner_frame.py.snapshot", assessment["producer_sha256"])
    material = read(remaining.local.actions_method.MATERIALS)
    for source in material["source_pins"]:
        if (
            "materials-source" in source["path"]
            or "material-frame-map" in source["path"]
        ):
            bind(ROOT / source["path"], source["sha256"])
    query_pins, query, order = read(PROFILE_PINS), read(PROFILE), read(ORDER)
    require(query_pins["query_sha256"] == PINS[PROFILE], "profile receipt differs")
    for source in (order["source_sha256"], query_pins["source_sha256_verified"]):
        for relative, digest in source.items():
            if relative != "manifest_embedded_manifest_sha256":
                bind(ROOT / relative, digest)
    for filename in (
        "bolt_demands.py",
        "lateral_reference.py",
        "top_corner_local.py",
        "top_corner_actions.py",
    ):
        path = HERE / filename
        require(
            path in PINS or filename in ("bolt_demands.py", "lateral_reference.py"),
            "unbound imported method",
        )
        bind(path, PINS.get(path, sha(path)))
    bind(Path(__file__).resolve(), sha(Path(__file__)))
    unchanged()
    model, inputs = read(FRAME / "model.json"), read(lateral.INPUTS)
    require(
        model["candidate"]
        == inputs["candidate"]
        == order["candidate"]
        == query["candidate"],
        "mixed candidate",
    )
    require(
        model["source_revision"]
        == inputs["revision_id"]
        == order["geometry_revision_id"]
        == query["geometry_revision_id"],
        "mixed geometry revision",
    )
    require(
        material["dowel_bearing_scenario"]["G"] == 0.5
        and material["dowel_bearing_scenario"]["conditional_hardware_scenario"]["D_mm"]
        == 6.35,
        "wood scenario differs",
    )
    fasteners = read(remaining.local.FASTENERS)
    require(
        1000
        * fasteners["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"][
            "machine_test_yield_ksi_min"
        ]
        == SCENARIOS["92ksi"],
        "conditional Grade 5 scenario differs",
    )
    read_members = {
        m["member_id"]: m["reduced_geometry_descriptor"]
        for m in inputs["members"]
        if m["member_kind"] != "panel"
    }
    bolts = {
        b["axis_id"]: b
        for b in inputs["connections"]
        if b["kind"] == "candidate_bolt" and len(b["receiver_member_ids"]) == 3
    }
    require(set(bolts) == set(AXES), "four-bolt census changed")
    for bolt in bolts.values():
        for body in bolt["receiver_member_ids"]:
            bind(
                ROOT / read_members[body]["step_path"],
                read_members[body]["step_sha256"],
            )
    ordered = {a["axis_id"]: a for s in order["stacks"] for a in s["axes"]}
    require(
        set(ordered) == set(AXES) and len(order["stacks"]) == 2, "stack census differs"
    )
    for axis_id, receivers in query_pins[
        "attempt04_receiver_order_from_modeled_underhead"
    ].items():
        for r in receivers:
            require(
                np.linalg.norm(
                    unit(r["source_proposed_grain_global_xyz"])
                    - unit(read_members[r["member_id"]]["axis"])
                )
                < 1e-8,
                "profile grain differs",
            )
    rows = read(FRAME / "row-identities.json")
    require(
        len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)),
        "raw row order differs",
    )
    planes, ties = defaultdict(lambda: defaultdict(list)), {}
    for row in rows:
        axis_id = row["row_id"].rsplit("/", 1)[0]
        if axis_id in bolts:
            if row["ownership"]["role"] == "candidate_bolt_lateral_plane":
                planes[axis_id][row["row_id"]].append(row)
            elif row["ownership"]["role"] == "physical_bolt_outer_seat_tension":
                require(axis_id not in ties, "duplicate tie")
                ties[axis_id] = row
            else:
                raise ValueError("unexpected owned bolt row")
    require(set(ties) == set(planes) == set(AXES), "incomplete knee rows")
    plane_sets = {
        a: sorted(p.values(), key=lambda rr: rr[0]["row"]) for a, p in planes.items()
    }
    geometry_by_axis = {
        a: geometry(bolts[a], ordered[a], plane_sets[a], ties[a], read_members)
        for a in AXES
    }
    contacts = {}
    for stack in order["stacks"]:
        bodies = stack["head_to_nut_geometric_receiver_order"]
        pairs = [set(bodies[i : i + 2]) for i in range(2)]
        rr = [
            r
            for r in rows
            if r["ownership"]["role"] == "timber_or_panel_contact"
            and {r["ownership"]["first_body"], r["ownership"]["second_body"]} in pairs
        ]
        require(len(rr) == 8, "knee face-contact census changed")
        contacts[stack["group_id"]] = rr
    unchanged()
    records, groups = [], []
    with np.load(GAP / "response.npz", allow_pickle=False) as response:
        for case_id in remaining.CASES:
            force = response[case_id + "_gap_raw_force_n"]
            require(
                force.shape == (1888,) and np.isfinite(force).all(),
                "invalid force array",
            )
            by_axis, action_by_axis = {}, {}
            for axis_id in AXES:
                r, aa = bolt_state(
                    case_id,
                    axis_id,
                    geometry_by_axis[axis_id],
                    plane_sets[axis_id],
                    ties[axis_id],
                    force,
                )
                records.append(r)
                by_axis[axis_id], action_by_axis[axis_id] = r, aa
            for stack in order["stacks"]:
                axes = stack["axis_ids"]
                groups.append(
                    group_state(
                        case_id,
                        stack,
                        geometry_by_axis,
                        [by_axis[a] for a in axes],
                        [act for a in axes for act in action_by_axis[a]],
                        contacts[stack["group_id"]],
                        force,
                        read_members,
                    )
                )
    profiles = profile_states(records, geometry_by_axis, query)
    require(
        len(records) == 24 and len(groups) == 12 and len(profiles) == 36,
        "incomplete result census",
    )
    unchanged()
    output.mkdir(parents=True)
    remaining.write_json(
        output / "source-pins.json",
        {str(p.relative_to(ROOT)): v for p, v in PINS.items()},
    )
    (output / "three_member_screen.py.snapshot").write_bytes(
        Path(__file__).read_bytes()
    )
    bolt_csv, plane_csv, receiver_csv, group_csv, contact_csv = [], [], [], [], []
    for r in records:
        g = geometry_by_axis[r["axis_id"]]
        body = g["receiver_order"][1]
        bolt_csv.append(
            {
                "case_id": r["case_id"],
                "axis_id": r["axis_id"],
                **{
                    k: r[k]
                    for k in (
                        "outer_tie_signed_n",
                        "outer_vector_difference_n",
                        "outer_vector_difference_over_larger_outer",
                        "outer_magnitude_ratio",
                        "outer_vector_angle_deg",
                        "symmetric_double_shear_action_applicable",
                    )
                },
                **{
                    f"utilization_sum_{label}": u
                    for label, u in r["conditional_convex_utilization_sum"].items()
                },
                **vector_columns("datum_mm", r["datum_mm"]),
                **vector_columns(
                    "headward_outer_force_n", r["planes"][0]["force_on_first_xyz_n"]
                ),
                **vector_columns(
                    "nutward_outer_force_n",
                    -np.array(r["planes"][1]["force_on_first_xyz_n"]),
                ),
                **vector_columns(
                    "middle_force_n",
                    r["receiver_wrenches"][body]["bolt_lateral"]["force_xyz_n"],
                ),
                **vector_columns(
                    "middle_moment_nmm",
                    r["receiver_wrenches"][body]["bolt_lateral"]["moment_xyz_nmm"],
                ),
            }
        )
        for p in r["planes"]:
            plane_csv.append(
                {
                    "case_id": r["case_id"],
                    "axis_id": r["axis_id"],
                    **{
                        k: json.dumps(v) if isinstance(v, (list, dict)) else v
                        for k, v in p.items()
                    },
                }
            )
        for b, ww in r["receiver_wrenches"].items():
            receiver_csv.append(
                {
                    "case_id": r["case_id"],
                    "axis_id": r["axis_id"],
                    "receiver": b,
                    **vector_columns("datum_mm", r["datum_mm"]),
                    **{
                        f"{kind}_{k}_{a}": float(v)
                        for kind, w in ww.items()
                        for k in ("force_xyz_n", "moment_xyz_nmm")
                        for a, v in zip("xyz", w[k], strict=True)
                    },
                }
            )
    for r in groups:
        middle = r["receiver_wrenches"][r["receiver_order"][1]]
        group_csv.append(
            {
                "case_id": r["case_id"],
                "group_id": r["group_id"],
                "sum_outer_ties_n": r["sum_outer_ties_n"],
                "headward_contact_compression_n": r["interface_contact_compression_n"][
                    0
                ],
                "nutward_contact_compression_n": r["interface_contact_compression_n"][
                    1
                ],
                **vector_columns("datum_mm", r["datum_mm"]),
                **{
                    f"middle_{kind}_{k}_{a}": float(v)
                    for kind, w in middle.items()
                    for k in ("force_xyz_n", "moment_xyz_nmm")
                    for a, v in zip("xyz", w[k], strict=True)
                },
            }
        )
        for c in r["contact_states"]:
            contact_csv.append(
                {
                    "case_id": r["case_id"],
                    "group_id": r["group_id"],
                    **{
                        k: json.dumps(v) if isinstance(v, list) else v
                        for k, v in c.items()
                    },
                }
            )
    for name, rr in (
        ("bolt-cases.csv", bolt_csv),
        ("plane-states.csv", plane_csv),
        ("receiver-wrenches.csv", receiver_csv),
        ("group-states.csv", group_csv),
        ("contact-states.csv", contact_csv),
        ("profile-states.csv", profiles),
    ):
        remaining.write_csv(output / name, rr)
    remaining.write_json(
        output / "screen.json",
        {
            "schema": "saved_knee_three_member_conditional_screen/v1",
            "status": "CONDITIONAL_ASYMMETRIC_SCREEN_FORMAL_GAPS_OPEN",
            "candidate": model["candidate"],
            "geometry_revision_id": model["source_revision"],
            "clearance_source": str(GAP.relative_to(ROOT)),
            "clearance_joint_hosts": comparison["clearance_joint_hosts"],
            "gap_scale": 1.0,
            "case_ids": list(remaining.CASES),
            "bolt_case_count": len(records),
            "group_case_count": len(groups),
            "symmetric_action_case_count": sum(
                r["symmetric_double_shear_action_applicable"] for r in records
            ),
            "scenario_fyb_psi": SCENARIOS,
            "screen_rule": "U_lat = norm(V_headward_outer)/Z_single_plane1 + norm(V_nutward_outer)/Z_single_plane2. One shared bolt; no summed capacities, plane count or bolt count multiplier. Conditional on convex complete-assembly lateral admissibility and inclusion of each full lifted two-member endpoint wrench; neither is established here.",
            "reference_basis": "Unadjusted individual endpoint Z, conditional DF-L G=0.50, 6.35 mm smooth body, zero thread bearing and face gap; actual signed plane directions. The larger middle bearing interval is reused in different endpoint hypotheses, not counted twice as an available resistance.",
            "normative_superposition_rule": False,
            "convex_endpoint_embedding_validated": False,
            "geometry": geometry_by_axis,
            "bolt_cases": records,
            "group_states": groups,
            "peaks": {
                label: max(
                    records,
                    key=lambda r: r["conditional_convex_utilization_sum"][label],
                )
                for label in SCENARIOS
            },
            "above_one": {
                label: [
                    {
                        "case_id": r["case_id"],
                        "axis_id": r["axis_id"],
                        "utilization_sum": r["conditional_convex_utilization_sum"][
                            label
                        ],
                    }
                    for r in records
                    if r["conditional_convex_utilization_sum"][label] > 1
                ]
                for label in SCENARIOS
            },
            "formal_gaps": GAPS,
            "moment_scope": "Moments are signed r cross F about recorded datums, with zero row free moments. They preserve receiver/interface transfer couples; no continuous-dowel stress recovery or wood/contact capacity is inferred. Action-reaction accounting closure is not a new frame-equilibrium audit.",
            "source_pin_count": len(PINS),
            "producer_sha256": sha(Path(__file__)),
            "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir())},
            "versions": {"python": platform.python_version(), "numpy": np.__version__},
            "complete_joint_acceptance": False,
            "reviewed_geometry_changed": False,
            "physical_release": False,
        },
    )
    for label in SCENARIOS:
        peak = max(
            records, key=lambda r: r["conditional_convex_utilization_sum"][label]
        )
        print(
            f"{label}: {peak['case_id']} / {peak['axis_id']} U={peak['conditional_convex_utilization_sum'][label]:.9f}; {sum(r['conditional_convex_utilization_sum'][label] > 1 for r in records)} states above one"
        )
    print(
        f"24 bolt cases, 48 plane states, 12 group states; {len(PINS)} source pins unchanged. {output}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clearance", type=Path, default=GAP)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    arguments = parser.parse_args()
    main(arguments.clearance, arguments.output)
