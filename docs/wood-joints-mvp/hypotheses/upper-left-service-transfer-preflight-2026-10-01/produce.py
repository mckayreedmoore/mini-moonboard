#!/usr/bin/env python3
"""Extract signed interface inputs and identify couples missing from two bolt points.

This reuses the authenticated source packet. It is a statics preflight, not a
contact, compliance, resistance, or joint acceptance calculation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BASE = "docs/wood-joints-mvp/hypotheses/"
REPORT = Path("/tmp/mini-moonboard-parent-upper-left-service-joint-final-replay-2026-10-01.json")
REPORT_SHA = "35f11b92a35604c8d924d20d9cb5f9a5221b415ef40cc9fb94e8de8f5fcc346d"
GEOMETRY = BASE + "upper-block-strength-2026-10-01/geometry.json"
GEOMETRY_SHA = "2ba66f4242b59e73a7dfc14a0b21d20d1f2710b9f835d60fce569eb73353fe91"
FREEZE = BASE + "service-upper-frame-joint-review-2026-09-30/freeze.json"
FREEZE_SHA = "c7669530756bcdb24662c879b86545e23934fa9ea810c00b66fa08d91d051f4f"
BLOCK = "left_service_outer_upper_cleat"
RECEIVERS = {"base_rail_service_upper_left", "base_side_left"}
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_pinned(path, expected):
    require(digest(path) == expected, f"Source changed: {path}")
    return json.loads(path.read_text())


def vector(value):
    require(isinstance(value, list) and len(value) == 3, "Expected three-vector")
    require(all(type(x) in (int, float) and math.isfinite(x) for x in value),
            "Nonfinite vector")
    return value


def dot(a, b):
    return math.fsum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def unit(a):
    length = math.hypot(*vector(a))
    require(length > 0, "Zero direction")
    return [x / length for x in a]


def summed(rows):
    return [math.fsum(row[i] for row in rows) for i in range(3)]


def shifted_moment(force, moment, old_datum, new_datum):
    """M_new = M_old - (new - old) x F; all coordinates remain global."""
    return sub(moment, cross(sub(new_datum, old_datum), force))


def shifted_radius(force_radius, moment_radius, old_datum, new_datum):
    arm = sub(new_datum, old_datum)
    return [moment_radius[i] + abs(arm[j]) * force_radius[k]
            + abs(arm[k]) * force_radius[j]
            for i, j, k in ((0, 1, 2), (1, 2, 0), (2, 0, 1))]


def close(actual, expected, tolerance, message):
    require(max(abs(x) for x in sub(actual, expected)) <= tolerance, message)


def group_frame(group, axes):
    points = group["axis_midplane_coordinates_xyz_mm"]
    require(len(points) == 2, "Expected two bolt points")
    datum = [(x + y) / 2 for x, y in zip(*points, strict=True)]
    pair = unit(sub(points[1], points[0]))
    normal = unit(axes[group["axis_ids"][0]]["bolt_axis_head_to_nut_global_xyz"])
    other_normal = unit(axes[group["axis_ids"][1]]["bolt_axis_head_to_nut_global_xyz"])
    close(normal, other_normal, 1e-8, "Nonparallel bolt pair")
    require(abs(dot(pair, normal)) < 1e-8, "Pair is not in interface plane")
    transverse = unit(cross(normal, pair))
    return {"datum_xyz_mm": datum,
            "basis_global_xyz": [pair, transverse, normal],
            "basis_order": ["bolt_pair_line", "in_face_transverse", "head_to_nut"],
            "axis_ids": group["axis_ids"],
            "bolt_point_xyz_mm": points,
            "pitch_mm": group["center_to_center_spacing_mm"]}


def source_port_audit(names, ports, block, frame):
    forces, moments = [], []
    pair = frame["basis_global_xyz"][0]
    contributions = {"contact": [], "lateral": [], "axial": []}
    for name in names:
        port = ports[name]
        side = "first" if port["first"] == block else "second"
        require(port[side] == block, "Wrong port body")
        point = vector(port.get(side + "_point", port["point"]))
        force = vector(port["force_on_" + side + "_xyz_n"])
        moment = cross(sub(point, frame["datum_xyz_mm"]), force)
        kind = ("contact" if name.startswith("contact_") else
                "axial" if name.endswith("outer-seat-axial-tie") else "lateral")
        contributions[kind].append({"source_name": name,
                                    "couple_on_pair_line_nmm": dot(pair, moment)})
        forces.append(force)
        moments.append(moment)
    require({k: len(v) for k, v in contributions.items()}
            == {"contact": 4, "lateral": 2, "axial": 2}, "Wrong port groups")
    return summed(forces), summed(moments), {
        kind: {"sum_nmm": math.fsum(r["couple_on_pair_line_nmm"] for r in rows),
               "ports": rows}
        for kind, rows in contributions.items()
    }


def produce(source=REPORT):
    report = read_pinned(source, REPORT_SHA)
    geometry = read_pinned(ROOT / GEOMETRY, GEOMETRY_SHA)
    freeze = read_pinned(ROOT / FREEZE, FREEZE_SHA)
    require(report["block"] == BLOCK and
            report["status"] == "HOLD_COMPLETE_JOINT_EVIDENCE_MISSING", "Wrong packet")
    require(report["local_joint_mvp_complete"] is False and
            report["complete_joint_accepted"] is False, "Unexpected acceptance")
    require(report["counts"] == {"bolt_states": 84, "whole_boundary_states": 21,
                                 "incident_ports_per_state": 16,
                                 "nominal_washer_seats": 8}, "Wrong source counts")
    for value in (geometry, freeze):
        require(value["candidate"] == report["candidate"] and
                value["geometry_revision_id"] == report["geometry_revision_id"],
                "Wrong candidate or revision")
    axes = {r["axis_id"]: r for r in geometry["physical_bolt_axes"]
            if r["block"] == BLOCK}
    groups = {r["host"]: group_frame(r, axes) for r in geometry["two_bolt_groups"]
              if r["block"] == BLOCK}
    require(set(groups) == RECEIVERS and len(axes) == 4, "Wrong joint groups")
    source_pins = {str(source): REPORT_SHA, GEOMETRY: GEOMETRY_SHA, FREEZE: FREEZE_SHA}
    models, responses, baseline_loads = {}, {}, {}
    for case in CASES:
        files = freeze["cases"][case]
        for key, destination in (("model", models), ("response", responses)):
            pin = files[key]
            require(report["source_pins"][pin["path"]] == pin["sha256"],
                    "Input is not pinned by the authenticated source packet")
            destination[case] = read_pinned(ROOT / pin["path"], pin["sha256"])
            source_pins[pin["path"]] = pin["sha256"]
            require(destination[case]["case_id"] == case and
                    destination[case]["candidate"] == report["candidate"] and
                    destination[case]["geometry_revision_id"] == report["geometry_revision_id"],
                    "Wrong case input identity")
        model = models[case]
        baseline_loads[case] = [
            {"source_node": int(node), "point_xyz_mm": vector(model["nodes"][str(node)]),
             "full_factor_force_n": vector(force)}
            for node, force in sorted(model["physical_body_loads"][BLOCK].items(),
                                      key=lambda item: int(item[0]))
        ]
        require(len(baseline_loads[case]) == 20, "Wrong body-load count")

    states = []
    boundaries = report["complete_same_state_receiver_wrenches"]
    keys = [(r["case"], r["increment_index"]) for r in boundaries]
    require(len(keys) == len(set(keys)) == 21 and
            set(keys) == {(case, i) for case in CASES for i in range(7)},
            "Wrong simultaneous state set")
    for row in boundaries:
        case, index, factor = row["case"], row["increment_index"], row["load_factor"]
        require(factor == FACTORS[index] and row["source_balance_reproduced"] is True,
                "Wrong load factor or unauthenticated balance")
        increment = responses[case]["increments"][index]
        require(increment["load_factor"] == factor, "Response factor mismatch")
        require(set(row["receiver_actions_on_block"]) == RECEIVERS, "Wrong receivers")
        receiver_rows = {}
        for receiver, frame in groups.items():
            action = row["receiver_actions_on_block"][receiver]
            force = vector(action["force_n"])
            old_moment = vector(action["moment_at_block_datum_nmm"])
            moment = shifted_moment(force, old_moment, row["datum_xyz_mm"],
                                    frame["datum_xyz_mm"])
            # The whole-boundary interval is a conservative upper bound on each
            # receiver's interval. It is not a newly derived native RF interval.
            radius = shifted_radius(row["force_rounding_radius_n"],
                                    row["moment_rounding_radius_nmm"],
                                    row["datum_xyz_mm"], frame["datum_xyz_mm"])
            pair = frame["basis_global_xyz"][0]
            tau, tau_radius = dot(pair, moment), dot([abs(x) for x in pair], radius)
            port_force, port_moment, contributions = source_port_audit(
                action["source_names"], increment["physical_connection_forces"], BLOCK, frame)
            close(port_force, force, 1e-8, "Port force rejoin failed")
            close(port_moment, moment, 1e-6, "Port moment rejoin failed")
            receiver_rows[receiver] = {
                "force_global_n": force, "moment_at_common_block_datum_global_nmm": old_moment,
                "moment_at_pair_datum_global_nmm": moment,
                "force_in_group_basis_n": [dot(e, force) for e in frame["basis_global_xyz"]],
                "moment_in_group_basis_nmm": [dot(e, moment) for e in frame["basis_global_xyz"]],
                "pair_line_couple_nmm": tau,
                "pair_line_couple_rounding_upper_bound_nmm": tau_radius,
                "two_point_force_only_representation_excluded": abs(tau) > tau_radius + 1e-8,
                "source_port_couple_contributions": contributions,
            }
        loads = [[factor * x for x in r["full_factor_force_n"]] for r in baseline_loads[case]]
        load_moment = summed([cross(sub(r["point_xyz_mm"], row["datum_xyz_mm"]), force)
                              for r, force in zip(baseline_loads[case], loads, strict=True)])
        total_force = summed([r["force_global_n"] for r in receiver_rows.values()] + loads)
        total_moment = summed([r["moment_at_common_block_datum_global_nmm"]
                               for r in receiver_rows.values()] + [load_moment])
        close(total_force, row["force_residual_n"], 1e-8, "Body force rejoin failed")
        close(total_moment, row["moment_residual_nmm"], 1e-6, "Body moment rejoin failed")
        states.append({"case": case, "increment_index": index, "load_factor": factor,
                       "common_block_datum_xyz_mm": row["datum_xyz_mm"],
                       "receiver_actions_on_block": receiver_rows,
                       "source_body_load_force_n": summed(loads),
                       "source_body_load_moment_at_common_datum_nmm": load_moment,
                       "source_force_residual_n": total_force,
                       "source_moment_residual_nmm": total_moment})
    summary = {}
    for receiver in sorted(RECEIVERS):
        peak = max(states, key=lambda r: abs(r["receiver_actions_on_block"][receiver]
                                            ["pair_line_couple_nmm"]))
        value = peak["receiver_actions_on_block"][receiver]
        summary[receiver] = {"case": peak["case"], "increment_index": peak["increment_index"],
                             "load_factor": peak["load_factor"],
                             "pair_line_couple_nmm": value["pair_line_couple_nmm"],
                             "rounding_upper_bound_nmm": value["pair_line_couple_rounding_upper_bound_nmm"]}
    return {
        "schema": "upper-left-service-signed-transfer-preflight/v1",
        "status": "PASS_SIGNED_INPUT_REJOIN_CONTACT_COUPLES_REQUIRED_JOINT_HOLD",
        "candidate": report["candidate"], "geometry_revision_id": report["geometry_revision_id"],
        "block": BLOCK, "source_pins": source_pins, "producer_sha256": digest(Path(__file__)),
        "source_cases": list(CASES), "missing_frame_cases": report["missing_frame_cases"],
        "force_sign": "Each receiver action acts on the cleat; body loads act on the same cleat.",
        "group_frames": groups, "source_full_factor_body_loads": baseline_loads,
        "states": states, "peak_pair_line_couples": summary,
        "counts": {"simultaneous_states": 21, "receiver_states": 42,
                   "source_ports_rejoined": 336, "body_load_instances_rejoined": 420},
        "all_receiver_states_require_more_than_two_point_forces": all(
            r["two_point_force_only_representation_excluded"]
            for state in states for r in state["receiver_actions_on_block"].values()),
        "allowable_slip_mm": None, "allowable_rotation_rad": None,
        "local_wrench_envelope_adopted": False, "frame_compatibility_established": False,
        "contact_compliance_or_resistance_established": False,
        "complete_joint_model_ready": False, "local_joint_mvp_complete": False,
        "complete_joint_accepted": False, "six_case_envelope_established": False,
        "geometry_changed": False, "native_solve_executed": False,
        "fabrication_released": False, "drilling_released": False,
        "structural_released": False, "climbing_released": False,
        "limits": "The transformed wrenches retain simultaneous source states. The pair-line couple "
                  "is a receiver demand about the pair datum, not local bolt bending. The rejoined "
                  "source contact ports carry this couple in the diagnostic model. No finite contact "
                  "pressure, physical force sharing, compliance, material resistance or operation is qualified."
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=REPORT)
    args = parser.parse_args()
    print(json.dumps(produce(args.source), indent=2, sort_keys=True))
