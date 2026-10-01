#!/usr/bin/env python3
"""Reconstruct six right-corner bolts from existing authenticated responses."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHARED = HERE.parent / "remaining-candidate-washer-demands-2026-10-01/produce.py"
SHARED_SHA = "0c58a7dc6c82ccc2624ee9d3355e2840f738be01961ddaf3f64486700e89e6c9"
AXES = {
    "knee_outer_right_inner_header_1": (41,),
    "knee_outer_right_inner_header_2": (42,),
    "knee_outer_right_post_1": (43,),
    "knee_outer_right_post_2": (44,),
    "knee_outer_right_side_1": (45, 46),
    "knee_outer_right_side_2": (47, 48),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vector(values):
    require(len(values) == 3 and all(math.isfinite(float(v)) for v in values),
            "invalid three-vector")
    return [float(v) for v in values]


def close(actual, expected, message):
    require(all(math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-8)
                for a, b in zip(vector(actual), vector(expected), strict=True)), message)


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def moment(point, force, reference):
    return cross([p-r for p, r in zip(point, reference, strict=True)], force)


def norm(v):
    return math.sqrt(sum(x*x for x in v))


def load_shared():
    require(sha(SHARED) == SHARED_SHA, "shared source checker changed")
    spec = importlib.util.spec_from_file_location("right_corner_shared", SHARED)
    require(spec is not None and spec.loader is not None, "shared checker unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def checked_plane(action, springs, components, inventory, expected_owner):
    require(action["role"] == "candidate_bolt_lateral_plane", "wrong plane role")
    require(len(action["source_row_ids"]) == 2
            and len(set(action["source_row_ids"])) == 2, "wrong scalar plane inventory")
    records = action["source_inventory_rows"]
    require([r["source_row_id"] for r in records] == action["source_row_ids"],
            "plane inventory order differs")
    reconstructed, radius = [0., 0., 0.], [0., 0., 0.]
    dofs = []
    for source, record in zip(action["source_row_ids"], records, strict=True):
        spring, component = springs[source], components[source]
        index = spring["source_inventory_row_index"]
        original = inventory[index]
        require(record["source_inventory_row_index"] == index
                and record["source_connection_name"] == spring["name"]
                and record["intended_law"] == spring["intended_law"] == original["intended_law"]
                == "bilateral" and spring["group"] == original["group"] == source,
                "plane source inventory/law differs")
        require(spring["physical_owner"] == original["physical_owner"] == expected_owner
                and original["element"] == spring["element"] == component["element"]
                and component["source_row_id"] == component["source_group"] == source,
                "plane source ownership/element differs")
        require(component["rf_action_reaction_passed"] is True
                and component["rf_kdu_intervals_intersect"] is True,
                "native bilateral gate failed")
        scalar = float(component["force_on_first_local_N"])
        error = float(component["force_rounding_radius_local_N"])
        require(math.isfinite(scalar) and math.isfinite(error) and error >= 0,
                "invalid native force/radius")
        require(math.isclose(scalar, -float(component["endpoint_rf_N"][0]),
                             rel_tol=1e-10, abs_tol=1e-8), "native endpoint RF sign differs")
        require(math.isclose(scalar, float(component["endpoint_rf_N"][1]),
                             rel_tol=1e-10, abs_tol=1e-8), "native second RF sign differs")
        dof = spring["connector_local_dof"]
        require(dof == spring["dof"] == original["dof"] and dof in (2, 3),
                "wrong lateral scalar DOF")
        dofs.append(dof)
        direction = vector(expected_owner["force_basis"][dof-1])
        for j in range(3):
            reconstructed[j] += scalar*direction[j]
            radius[j] += error*abs(direction[j])
    require(sorted(dofs) == [2, 3], "duplicate/missing lateral force direction")
    for key in ("axis", "axis_id", "first", "second", "role", "force_basis", "point"):
        require(action[key] == expected_owner[key], "export plane identity differs")
    close(action["force_on_first_xyz_n"], reconstructed, "plane/native vector differs")
    close(action["force_on_second_xyz_n"], [-v for v in reconstructed], "plane reaction differs")
    close(action["force_rounding_radius_xyz_n"], radius, "plane force interval differs")
    require(abs(sum(a*f for a, f in zip(action["axis"], reconstructed, strict=True))) < 1e-8,
            "plane has axial force")
    require(math.isclose(float(action["transverse_shear_n"]), norm(reconstructed),
                         rel_tol=1e-10, abs_tol=1e-8), "plane resultant differs")
    return reconstructed, radius


def self_checks():
    require(moment([3., 4., 5.], [7., -2., 9.], [1., 1., 1.]) == [35., 10., -25.],
            "independent force/couple oracle failed")
    f, p, d1, d2 = [7., -2., 9.], [3., 4., 5.], [1., 1., 1.], [-2., 3., 0.]
    transported = [m-c for m, c in zip(moment(p, f, d1),
                   cross([b-a for a, b in zip(d1, d2, strict=True)], f), strict=True)]
    close(moment(p, f, d2), transported, "wrench transport oracle failed")
    close(moment(p, f, d1), [-x for x in moment(p, [-x for x in f], d1)],
          "equal/opposite moment oracle failed")


def produce():
    self_checks()
    shared = load_shared()
    acceptance = shared.load_method("acceptance")
    _, register, _ = acceptance.verify_source_pins()
    geometry = shared.load_method("geometry")
    base, _ = geometry.methods()
    _, model, _, _, geometry_pins = base.checked_inputs()
    remaining, primary, upper = geometry.partition(base, model)
    selected = {c["axis_id"]: c for c in remaining if c["axis_id"] in AXES}
    require(set(selected) == set(AXES) and not set(AXES).intersection(primary+upper),
            "right-corner cohort overlaps another owned cohort")
    seats = {axis: {s["role"]: s for s in geometry.source_seats(c)}
             for axis, c in selected.items()}
    require(sha(shared.FREEZE) == shared.FREEZE_SHA, "three-case freeze changed")
    freeze = json.loads(shared.FREEZE.read_text())
    bolts, plane_rows, receiver_rows = [], [], []
    max_force_closure, max_moment_closure = 0., 0.
    for case, files in freeze["cases"].items():
        acceptance.report_register_row(register, case, acceptance.CASE_SPECS[case])
        for pin in files.values():
            require(sha(ROOT/pin["path"]) == pin["sha256"], "frozen source changed")
        native = json.loads((ROOT/files["model"]["path"]).read_text())
        response = json.loads((ROOT/files["response"]["path"]).read_text())
        audit = json.loads((ROOT/files["all_body_audit"]["path"]).read_text())
        terminal = json.loads((ROOT/files["terminal"]["path"]).read_text())
        require(audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS"
                and audit["source_model_sha256"] == files["model"]["sha256"]
                and audit["source_response_sha256"] == files["response"]["sha256"],
                "all-body source audit differs")
        require(terminal.get("conditional_case_forces_usable",
                             terminal.get("response_usable_for_conditional_joint_checks")) is True,
                "terminal response unusable")
        for key, expected in (("candidate", model["candidate"]),
                              ("geometry_revision_id", model["revision_id"]), ("case_id", case)):
            require(native[key] == response[key] == expected, "source case/revision differs")
        require(freeze["candidate"] == model["candidate"]
                and freeze["geometry_revision_id"] == model["revision_id"], "freeze revision differs")
        for key in ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
                    "floor_capacity_established", "friction_qualified"):
            require(response[key] is False, "source acceptance boundary changed")
        for name, key in (("model", "source_input_model_json_sha256"),
                          ("deck", "source_input_deck_sha256"), ("native_data", "native_data_sha256")):
            require(response[key] == files[name]["sha256"], "native provenance differs")
        require(tuple(i["load_factor"] for i in response["increments"]) == shared.FACTORS
                and tuple(i["load_factor"] for i in audit["increments"]) == shared.FACTORS,
                "wrong increment coverage")
        springs = {r["source_row_id"]: r for r in native["springs"]}
        bindings = {r["name"]: r for r in native["unilateral_springa_bindings"]}
        require(len(springs) == len(native["springs"])
                and len(bindings) == len(native["unilateral_springa_bindings"]), "duplicate source identities")
        inventory = native["raw_source_carrier_law_inventory_rows"]
        for index, inc in enumerate(response["increments"]):
            require(all(inc[g] is True for g in shared.GATES), "source increment gate failed")
            require(all(b["printed_resultants_passed"] is True
                        and b["interval_resultants_passed"] is True
                        for b in audit["increments"][index]["body_equilibrium"].values()),
                    "source body-equilibrium gate failed")
            components = {r["source_row_id"]: r for r in inc["retained_bilateral_spring2_components"]}
            ties = {r["source_row_id"]: r for r in inc["springa_components"]}
            require(len(components) == len(inc["retained_bilateral_spring2_components"])
                    and len(ties) == len(inc["springa_components"]), "duplicate component identity")
            for axis, plane_numbers in sorted(AXES.items()):
                identity = {"case_id": case, "increment_index": index,
                            "load_factor": inc["load_factor"], "axis_id": axis}
                outer = seats[axis]
                reference = list(outer["head"]["point"].toTuple())
                tie_name = axis+"/outer-seat-axial-tie"
                tie, binding = inc["physical_connection_forces"][tie_name], bindings[tie_name]
                signed_tie = shared.checked_tie(tie, binding, ties[binding["source_row_id"]], outer)
                receivers = selected[axis]["source_record"]["geometry"]["wood_receiver_intervals"]
                require(len(receivers) == len(plane_numbers)+1, "receiver/plane topology differs")
                actions, endpoints = [], []
                for j, number in enumerate(plane_numbers):
                    name = f"{axis}/plane-{number}"
                    action = inc["physical_connection_forces"][name]
                    source = springs[action["source_row_ids"][0]]["physical_owner"]
                    force, radius = checked_plane(action, springs, components, inventory, source)
                    require(source["first"] == receivers[j]["receiver_id"]
                            and source["second"] == receivers[j+1]["receiver_id"], "receiver order differs")
                    edge = receivers[j]["intersection_solid_intervals_from_underhead_mm"][0][1]
                    start = receivers[0]["intersection_solid_intervals_from_underhead_mm"][0][0]
                    next_start = receivers[j+1]["intersection_solid_intervals_from_underhead_mm"][0][0]
                    require(math.isclose(edge, next_start, abs_tol=1e-7), "inter-receiver gap changed")
                    close(source["point"], [p+(edge-start)*a for p, a in
                          zip(reference, tie["axis"], strict=True)], "plane/wood interface datum differs")
                    close(source["axis"], tie["axis"], "plane/bolt axis differs")
                    actions.append({"name": name, "source_action": action})
                    plane_rows.append({**identity, "connection_name": name,
                                       "lateral_resultant_N": norm(force), "signed_tie_N": signed_tie,
                                       "source_action": action})
                    endpoints.extend([(source["first"], source["point"], force, radius, name),
                                      (source["second"], source["point"], [-f for f in force], radius, name)])
                for side in ("first", "second"):
                    endpoints.append((tie[side], tie[side+"_point"], tie["force_on_"+side+"_xyz_n"],
                                      tie["force_rounding_radius_xyz_n"], tie_name))
                sums = defaultdict(lambda: {"force_N": [0., 0., 0.], "moment_Nmm": [0., 0., 0.],
                                           "force_radius_N": [0., 0., 0.], "moment_radius_Nmm": [0., 0., 0.],
                                           "endpoint_actions": []})
                for receiver, point, force, radius, name in endpoints:
                    wrench = sums[receiver]
                    lever = [p-r for p, r in zip(point, reference, strict=True)]
                    m = moment(point, force, reference)
                    mr = [abs(lever[1])*radius[2]+abs(lever[2])*radius[1],
                          abs(lever[2])*radius[0]+abs(lever[0])*radius[2],
                          abs(lever[0])*radius[1]+abs(lever[1])*radius[0]]
                    for field, value in (("force_N", force), ("moment_Nmm", m),
                                         ("force_radius_N", radius), ("moment_radius_Nmm", mr)):
                        for k in range(3):
                            wrench[field][k] += value[k]
                    wrench["endpoint_actions"].append({"connection_name": name, "point_xyz_mm": point,
                                                      "force_N": force, "force_radius_N": radius})
                require(set(sums) == {r["receiver_id"] for r in receivers}, "missing receiver wrench")
                fc = max(abs(sum(w["force_N"][k] for w in sums.values())) for k in range(3))
                mc = max(abs(sum(w["moment_Nmm"][k] for w in sums.values())) for k in range(3))
                require(fc <= 1e-8 and mc <= 1e-7, "internal action cancellation failed")
                max_force_closure, max_moment_closure = max(max_force_closure, fc), max(max_moment_closure, mc)
                record = {**identity, "reference_head_seat_xyz_mm": reference, "signed_tie_N": signed_tie,
                          "source_tie": tie, "same_state_planes": actions, "receivers": dict(sums)}
                bolts.append(record)
                receiver_rows.extend({**identity, "receiver": receiver, "reference_head_seat_xyz_mm": reference,
                                      "force_resultant_N": norm(w["force_N"]),
                                      "couple_resultant_Nmm": norm(w["moment_Nmm"]),
                                      "signed_tie_N": signed_tie, **w} for receiver, w in sums.items())
    require(len(bolts) == len({(r["case_id"], r["increment_index"], r["axis_id"]) for r in bolts}) == 126,
            "incomplete physical-bolt coverage")
    require(len(plane_rows) == 168 and len(receiver_rows) == 294, "incomplete plane/receiver coverage")
    peaks = [max((r for r in plane_rows if r["connection_name"] == f"{axis}/plane-{number}"),
                 key=lambda r: r["lateral_resultant_N"]) for axis, nums in sorted(AXES.items()) for number in nums]
    return {"status": "PASS_RIGHT_CORNER_SOURCE_JOIN_AND_INTERNAL_BOOKKEEPING_ONLY",
            "candidate": model["candidate"], "revision": model["revision_id"],
            "producer_sha256": sha(Path(__file__)), "shared_checker_sha256": SHARED_SHA,
            "freeze_sha256": shared.FREEZE_SHA, "case_sources": freeze["cases"],
            "geometry_input_pins": geometry_pins,
            "counts": {"axes": 6, "lateral_planes": 8, "cases": 3, "states_per_case": 7,
                       "bolt_states": 126, "plane_states": 168, "receiver_wrenches": 294},
            "max_internal_force_closure_N": max_force_closure,
            "max_internal_moment_closure_Nmm": max_moment_closure,
            "peak_plane_states": peaks, "maximum_tie_state": max(bolts, key=lambda r: r["signed_tie_N"]),
            "bolt_states": bolts, "receiver_wrenches": receiver_rows,
            "claim_limits": {"existing_three_case_source_join": True, "native_RF_tokens_independently_parsed": False,
                             "native_solve": False, "geometry_changed": False, "left_pass_transferred": False,
                             "complete_body_boundary_or_section": False, "bolt_internal_bending": False,
                             "resistance_or_combined_interaction": False, "six_case_envelope": False,
                             "joint_accepted": False, "criterion_pass": False}}


def rejection_checks():
    shared = load_shared()
    freeze = json.loads(shared.FREEZE.read_text())
    files = freeze["cases"]["a12-rear"]
    model = json.loads((ROOT/files["model"]["path"]).read_text())
    inc = json.loads((ROOT/files["response"]["path"]).read_text())["increments"][0]
    action = inc["physical_connection_forces"]["knee_outer_right_post_1/plane-43"]
    springs = {r["source_row_id"]: r for r in model["springs"]}
    components = {r["source_row_id"]: r for r in inc["retained_bilateral_spring2_components"]}
    owner = springs[action["source_row_ids"][0]]["physical_owner"]
    for mutation in ("first_force_sign", "reaction_sign", "nonfinite_force", "inventory_row", "interval_radius"):
        bad = copy.deepcopy(action)
        if mutation == "first_force_sign":
            bad["force_on_first_xyz_n"] = [-x for x in bad["force_on_first_xyz_n"]]
        elif mutation == "reaction_sign":
            bad["force_on_second_xyz_n"] = bad["force_on_first_xyz_n"][:]
        elif mutation == "nonfinite_force":
            bad["force_on_first_xyz_n"][0] = float("nan")
        elif mutation == "inventory_row":
            bad["source_inventory_rows"][0]["source_inventory_row_index"] += 1
        else:
            bad["force_rounding_radius_xyz_n"][1] += 1
        try:
            checked_plane(bad, springs, components, model["raw_source_carrier_law_inventory_rows"], owner)
        except ValueError:
            continue
        raise ValueError(f"corrupted source was accepted: {mutation}")
    return 5


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--rejection-checks", action="store_true")
    args = parser.parse_args()
    if args.rejection_checks:
        self_checks()
        print(f"PASS_RIGHT_CORNER_ORACLES_AND_{rejection_checks()}_CORRUPT_SOURCE_REJECTIONS")
    else:
        print(json.dumps(produce(), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
