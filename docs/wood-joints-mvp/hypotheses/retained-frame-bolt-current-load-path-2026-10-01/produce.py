#!/usr/bin/env python3
"""Bind twelve current retained bolts to frozen signed forces; accept no joint."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PACKETS = "docs/wood-joints-mvp/hypotheses/"
ACCEL = PACKETS + "mvp-acceleration-2026-09-28/"
FEATURE = PACKETS + "current-finished-feature-register-2026-10-01/"
PROJECTION = ACCEL + "current-frame-physical-connector-projection-contract-attempt01/"
FIXED = {
    PACKETS + "upper-frame-joint-review-2026-09-30/freeze.json":
        "d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73",
    FEATURE + "axis-features.json":
        "bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19",
    FEATURE + "axis-source-pins.json":
        "7a501047c003174c15461ae12e3cd47af4e4bf59b1d40d3c8e5b76d8e1904d34",
    FEATURE + "source-pins.json":
        "0e8cb56407f14e93d7ab95741115d4355a954eb845ae503365ba1da1149bd9cd",
    PROJECTION + "projection-contract.json":
        "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    PROJECTION + "physical-index-map.json":
        "08cecf37bd798e82f55f117dc0d03693c956c6f370950bd1634549645c202a19",
    PROJECTION + "source-pins.json":
        "0f56602a25eedf9424a448b635b354768379f18649b6ec13e93ba054160c76ae",
    ACCEL + "current-corner-native-demand-export-attempt03/produce.py":
        "0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8",
}
EXPORT = ACCEL + "current-corner-native-demand-export-attempt03/produce.py"
FREEZE = PACKETS + "upper-frame-joint-review-2026-09-30/freeze.json"
CANDIDATE = "compact-floor-flush-wood-joints-development"
REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
FACTORS = (0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0)
ACCEPTANCE = ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
              "floor_capacity_established", "friction_qualified")
GATES = ("mpc_interval_checks_passed", "retained_bilateral_checks_passed",
         "springa_law_checks_passed", "selected_floor_complementarity_passed",
         "inactive_floor_tangent_no_restraint_or_reaction_passed",
         "raw_balance_passed", "rounding_interval_balance_passed")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin_file(relative, expected, pins):
    path = ROOT / relative
    require(path.is_file() and sha(path) == expected, f"source byte changed or missing: {relative}")
    require(relative not in pins or pins[relative]["sha256"] == expected,
            f"contradictory pin: {relative}")
    pins[relative] = {"sha256": expected, "size_bytes": path.stat().st_size}


def nested_pins(value, pins):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            pin_file(value["path"], value["sha256"], pins)
        for key, child in value.items():
            if isinstance(child, dict) and "sha256" in child and "/" in key:
                pin_file(key, child["sha256"], pins)
            nested_pins(child, pins)
    elif isinstance(value, list):
        for child in value:
            nested_pins(child, pins)


def read(relative):
    return json.loads((ROOT / relative).read_text())


def close(actual, expected, message, tolerance=1e-8):
    require(len(actual) == len(expected) and all(
        math.isfinite(float(a)) and math.isfinite(float(b))
        and abs(a-b) <= tolerance for a, b in zip(actual, expected, strict=True)), message)


def indexed(rows, key, message):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), message)
    return result


def plus(a, b):
    return [x+y for x, y in zip(a, b, strict=True)]


def scaled(a, scale):
    return [scale*x for x in a]


def geometry_register(features, pins):
    require(features["candidate"] == CANDIDATE
            and features["geometry_revision_id"] == REVISION, "wrong current geometry")
    group = features["source_axis_groups"]["retained_frame_bolt_axes"]
    axes = indexed(group["axes"], "axis_id", "duplicate retained axis")
    expected = {f"{family}_bolt_{side}_{number}" for family in
                ("lumber_leg", "rail_front", "rail_rear")
                for side in ("left", "right") for number in (1, 2)}
    require(set(axes) == set(group["axis_ids"]) == expected
            and group["axis_count"] == 12, "missing/extra retained axes")
    candidate_group = features["source_axis_groups"]["candidate_bolt_axes"]
    candidate_ids = candidate_group["axis_ids"]
    require(len(set(candidate_ids)) == len(candidate_ids) == candidate_group["axis_count"] == 92
            and not set(candidate_ids).intersection(axes), "candidate/retained census mixed")
    result, members = {}, set()
    for axis_id, row in sorted(axes.items()):
        require(row["axis_group"] == "retained_frame_bolt_axes", "wrong axis group")
        source = row["source_axis_fields"]
        datum, direction = source["datum_global_xyz_mm"], source["direction_global_xyz"]
        close([sum(v*v for v in direction)], [1.], "nonunit geometry direction")
        receivers = []
        memberships = row["receiver_memberships"]
        require(len(memberships) == 2 and len({r["receiver_member_id"] for r in memberships}) == 2,
                f"missing/duplicate receivers: {axis_id}")
        for membership in memberships:
            require(membership["match_status"] == "matched_bore_patch"
                    and membership["binding_status"] == "bound_to_current_finished_stock_frame",
                    f"unresolved receiver: {axis_id}")
            eligible = [patch for patch in membership["cylinder_surface_candidates"]
                        if patch["association_status"] == "eligible_bore_patch"]
            require(len(eligible) == 1 and membership["matched_feature_ids"] == [eligible[0]["feature_id"]],
                    f"ambiguous bore: {axis_id}")
            patch = eligible[0]
            interval = patch["patch_interval_projected_from_axis_datum_mm"]
            require(patch["material_side_geometry"] == "bore_like"
                    and patch["finite_interval_status"] == "contained_in_source_finite_interval"
                    and len(interval) == 2 and 0 <= interval[0] < interval[1] <= source["axis_length_mm"],
                    f"invalid finite bore: {axis_id}")
            step = membership["current_finished_step_binding"]
            require(step["valid"] and step["manifest_roundtrip_valid"] and step["solid_count"] == 1,
                    "invalid current finished STEP")
            pin_file(step["path"], step["file_sha256"], pins)
            require(pins[step["path"]]["size_bytes"] == step["size_bytes"], "STEP size differs")
            members.add(membership["receiver_member_id"])
            receivers.append({"member": membership["receiver_member_id"], "interval_from_axis_datum_mm": interval,
                              "feature_id": patch["feature_id"], "finished_step": step,
                              "stock_frame": membership["stock_frame"]})
        receivers.sort(key=lambda r: r["interval_from_axis_datum_mm"][0])
        first, second = receivers
        close([first["interval_from_axis_datum_mm"][1]], [second["interval_from_axis_datum_mm"][0]],
              "noncontiguous retained receivers", 1e-6)
        def point_at(station, axis_datum=datum, axis_direction=direction):
            return plus(axis_datum, scaled(axis_direction, station))
        result[axis_id] = {"source_axis_fields": source, "receivers_head_to_nut": receivers,
                           "first": first["member"], "second": second["member"],
                           "lateral_interface_point_xyz_mm": point_at(first["interval_from_axis_datum_mm"][1]),
                           "first_outer_seat_point_xyz_mm": point_at(first["interval_from_axis_datum_mm"][0]),
                           "second_outer_seat_point_xyz_mm": point_at(second["interval_from_axis_datum_mm"][1]),
                           "source_hardware_policy_record_only": row["source_hardware_policy"]}
    require(len(members) == 8, "wrong retained receiver body count")
    return result, sorted(members), candidate_ids


def bind_axis_model(axis_id, geometry, model, projection_rows):
    raw_rows = model["raw_source_carrier_law_inventory_rows"]
    lateral_name, axial_name = axis_id+"/wood-interface", axis_id+"/outer-seat-axial-tie"
    lateral = [r for r in raw_rows if r["name"] == lateral_name]
    axial = [r for r in raw_rows if r["name"] == axial_name]
    require(len(lateral) == 2 and len(axial) == 1
            and {r["dof"] for r in lateral} == {2, 3}, "missing/duplicate retained scalar rows")
    native_springs = indexed(model["springs"], "source_row_id", "duplicate native springs")
    ties = indexed(model["unilateral_springa_bindings"], "name", "duplicate native ties")
    tie = ties[axial_name]
    require(tie["force_law"] == "k * max(q_mm, 0)"
            and tie["ground_endpoint_is_numerical_only"] is True, "incorrect retained tie law")
    result = []
    for raw in sorted(lateral, key=lambda r: r["dof"])+axial:
        owner = raw["physical_owner"]
        require(owner["axis_id"] == axis_id and owner["first"] == raw["first_body"] == geometry["first"]
                and owner["second"] == raw["second_body"] == geometry["second"], "current owner/receiver differs")
        close(owner["axis"], geometry["source_axis_fields"]["direction_global_xyz"], "current axis direction differs")
        is_lateral = raw["name"] == lateral_name
        require(raw["role"] == owner["role"] == ("retained_bolt_lateral_plane" if is_lateral
                else "physical_bolt_outer_seat_tension")
                and raw["intended_law"] == ("bilateral" if is_lateral else "tension_only"), "wrong retained role/law")
        if is_lateral:
            close(owner["point"], geometry["lateral_interface_point_xyz_mm"], "lateral current bore point differs", 1e-6)
            spring = native_springs[raw["group"]]
            require(spring["nodes"] == raw["nodes"] and spring["element"] == raw["element"]
                    and spring["physical_owner"] == owner and spring["dof"] == raw["dof"], "SPRING2 source map differs")
            direction = owner["force_basis"][raw["dof"]-1]
        else:
            for side in ("first", "second"):
                close(owner[side+"_point"], geometry[side+"_outer_seat_point_xyz_mm"], "axial current outer seat differs", 1e-6)
            require(tie["physical_owner"] == owner and tie["source_row_id"] == raw["group"]
                    and tie["source_element"] == raw["element"], "SPRINGA source map differs")
            direction = owner["scalar_normal"]
            close(direction, owner["axis"], "tie scalar direction differs")
        matches = [r for r in projection_rows if r["source_group"] == raw["group"]]
        require(len(matches) == 1, "missing/duplicate physical projection row")
        projection = matches[0]
        ownership = projection["ownership"]
        require(projection["row_id"] == raw["name"]
                and projection["source_inventory_row_index"] == raw_rows.index(raw)
                and projection["source_element"] == raw["element"]
                and ownership["first_body"] == owner["first"] and ownership["second_body"] == owner["second"]
                and ownership["role"] == owner["role"] and projection["law"]["intended_law"] == raw["intended_law"],
                "physical projection identity differs")
        close(ownership["direction_global_xyz"], direction, "physical projection direction differs")
        close(ownership["point_mm"], owner["point"], "physical projection point differs")
        require(projection["law"]["stiffness_N_per_mm"] == raw["stiffness_n_per_mm"], "projection stiffness differs")
        if is_lateral:
            require(projection["source_connector"]["nodes"] == raw["nodes"]
                    and projection["source_connector"]["dof"] == raw["dof"], "projection SPRING2 map differs")
        else:
            require(projection["source_projection"]["springa_nodes"] == tie["springa_nodes"]
                    and projection["source_projection"]["nodes"] == tie["source_projection_nodes"]
                    and projection["grounding"]["ground_is_physical"] is False, "projection tie/ground map differs")
        result.append({"source_row_id": raw["group"], "source_inventory_row_index": raw_rows.index(raw),
                       "family": projection["family"], "connection_name": raw["name"],
                       "source_nodes": raw["nodes"] if is_lateral else tie["springa_nodes"],
                       "local_dof": raw["dof"] if is_lateral else None,
                       "direction_global_xyz": direction, "physical_owner": owner,
                       "element": raw["element"]})
    return result


def scalar_actions(binding, increment):
    bilateral = indexed(increment["retained_bilateral_spring2_components"], "source_row_id", "duplicate SPRING2 components")
    ties = indexed(increment["springa_components"], "source_row_id", "duplicate SPRINGA components")
    result = []
    for row in binding:
        is_lateral = row["family"] == "bilateral_spring2"
        component = (bilateral if is_lateral else ties)[row["source_row_id"]]
        require(component["element"] == row["element"], "component/source element differs")
        if is_lateral:
            require(component["rf_action_reaction_passed"] is True
                    and component["rf_kdu_intervals_intersect"] is True, "SPRING2 gate failed")
            force, radius = component["force_on_first_local_N"], component["force_rounding_radius_local_N"]
            close([force], [-component["endpoint_rf_N"][0]], "SPRING2 endpoint sign differs")
        else:
            require(component["source_inventory_row_index"] == row["source_inventory_row_index"]
                    and component["intended_source_law"] == "tension_only", "SPRINGA component source differs")
            for gate in ("inside_table_domain_including_rounding", "table_force_interval_intersects_native_rf",
                         "native_endpoint_action_reaction_passed", "numerical_ground_rf_excluded_from_physical_balance"):
                require(component[gate] is True, "SPRINGA gate failed: "+gate)
            force, radius = component["native_endpoint_internal_force_N"], component["native_endpoint_internal_radius_N"]
            require(force >= -1e-9, "negative tension-only action")
        require(math.isfinite(force) and math.isfinite(radius) and radius >= 0, "invalid scalar force/radius")
        result.append({**row, "scalar_force_on_first_N": force, "scalar_radius_N": radius,
                       "force_on_first_xyz_n": scaled(row["direction_global_xyz"], force),
                       "force_rounding_radius_xyz_n": scaled([abs(x) for x in row["direction_global_xyz"]], radius)})
    return result


def check_interface(row, binding, scalar_rows, method):
    owner = binding[0]["physical_owner"]
    method.validate_response_owner(row, {"owner": owner}, binding[0]["connection_name"])
    require(row["axis_id"] == owner["axis_id"] and row["role"] == owner["role"], "physical row axis/role differs")
    require(row["source_row_ids"] == [r["source_row_id"] for r in binding], "physical scalar coverage differs")
    refs = row["source_inventory_rows"]
    require(len(refs) == len(binding) and all(
        ref["source_row_id"] == source["source_row_id"]
        and ref["source_inventory_row_index"] == source["source_inventory_row_index"]
        and ref["source_connection_name"] == source["connection_name"]
        for ref, source in zip(refs, binding, strict=True)), "physical source inventory differs")
    close(row["force_on_first_xyz_n"], method.sum_vectors([r["force_on_first_xyz_n"] for r in scalar_rows]),
          "physical force differs from signed scalars")
    close(row["force_rounding_radius_xyz_n"], method.sum_vectors([r["force_rounding_radius_xyz_n"] for r in scalar_rows]),
          "physical force radius differs from signed scalars")


def endpoint_wrenches(lateral, axial, datums, method):
    result = {}
    for side in ("first", "second"):
        body = lateral[side]
        require(axial[side] == body, "combined receiver owner differs")
        datum = datums[body]
        force, moment, origin, radius, moment_radius, origin_radius = ([0.]*3 for _ in range(6))
        individual = []
        for row in (lateral, axial):
            point = row.get(side+"_point", row["point"])
            action = row["force_on_"+side+"_xyz_n"]
            bound = row["force_rounding_radius_xyz_n"]
            force = plus(force, action)
            moment = plus(moment, method.cross(method.sub(point, datum), action))
            origin = plus(origin, method.cross(point, action))
            radius = plus(radius, bound)
            moment_radius = plus(moment_radius, method.cross_interval_radius(method.sub(point, datum), bound))
            origin_radius = plus(origin_radius, method.cross_interval_radius(point, bound))
            individual.append({"role": row["role"], "point_xyz_mm": point, "force_xyz_n": action,
                               "moment_about_reporting_datum_xyz_nmm": method.cross(method.sub(point, datum), action),
                               "moment_about_origin_xyz_nmm": method.cross(point, action)})
        close(origin, plus(moment, method.cross(datum, force)), "endpoint wrench transport differs", 1e-6)
        result[side] = {"receiver_member_id": body, "reporting_datum_xyz_mm": datum,
                        "force_xyz_n": force, "moment_about_reporting_datum_xyz_nmm": moment,
                        "individual_interface_wrenches": individual,
                        "moment_about_origin_xyz_nmm": origin, "force_radius_xyz_n": radius,
                        "moment_radius_about_reporting_datum_xyz_nmm": moment_radius,
                        "moment_radius_about_origin_xyz_nmm": origin_radius}
    close(plus(result["first"]["force_xyz_n"], result["second"]["force_xyz_n"]), [0.]*3,
          "retained pair force cancellation differs")
    close(plus(result["first"]["moment_about_origin_xyz_nmm"], result["second"]["moment_about_origin_xyz_nmm"]),
          [0.]*3, "retained pair origin couple cancellation differs", 1e-6)
    return result


def body_boundary(model, members):
    grouped = {}
    for index, row in enumerate(model["raw_source_carrier_law_inventory_rows"]):
        owner = row["physical_owner"]
        require(owner["first"] == row["first_body"] and owner["second"] == row["second_body"], "raw owner/body differs")
        if owner["first"] not in members and owner["second"] not in members:
            continue
        record = grouped.setdefault(row["name"], {"source_connection_name": row["name"],
                                                  "owner": owner, "source_indices": []})
        require(record["owner"] == owner, "duplicate interface owners differ")
        record["source_indices"].append(index)
    return [grouped[name] for name in sorted(grouped)]


def validate_case(case, files, freeze, pins):
    nested_pins(files, pins)
    model, response, audit, terminal = (read(files[k]["path"]) for k in
                                       ("model", "response", "all_body_audit", "terminal"))
    for key, expected in (("candidate", CANDIDATE), ("geometry_revision_id", REVISION)):
        require(model[key] == response[key] == freeze[key] == expected, "case candidate/revision differs")
    require(model["case_id"] == response["case_id"] == case, "case identity differs")
    for key in ACCEPTANCE:
        require(response[key] is False, "source acceptance changed")
    require(response["historical_c11_forces_or_active_states_used"] is False, "historical response transfer")
    require(audit["status"] == "PASS_PARENT_ALL_BODY_RESPONSE_SUMS" and audit["joint_accepted"] is False
            and audit["physical_tolerances_N_Nmm"] == [0.1, 2.0]
            and audit["source_model_sha256"] == files["model"]["sha256"]
            and audit["source_response_sha256"] == files["response"]["sha256"], "all-body audit binding differs")
    require(terminal.get("conditional_case_forces_usable", terminal.get("response_usable_for_conditional_joint_checks")) is True,
            "terminal conditional response unusable")
    for label, key in (("model", "source_input_model_json_sha256"), ("deck", "source_input_deck_sha256"),
                       ("native_data", "native_data_sha256")):
        require(response[key] == files[label]["sha256"], "response source pin differs")
    require(tuple(i["load_factor"] for i in response["increments"]) == FACTORS
            and tuple(i["load_factor"] for i in audit["increments"]) == FACTORS, "incomplete state coverage")
    for relative, digest in model["source_geometry_hashes"].items():
        pin_file(relative, digest, pins)
    return model, response, audit


def build():
    pins = {}
    for relative, digest in FIXED.items():
        pin_file(relative, digest, pins)
    for relative in (FEATURE+"axis-source-pins.json", FEATURE+"source-pins.json", PROJECTION+"source-pins.json"):
        nested_pins(read(relative), pins)
    spec = importlib.util.spec_from_file_location("retained_endpoint_export", ROOT/EXPORT)
    require(spec is not None and spec.loader is not None, "pinned endpoint helper unavailable")
    method = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(method)
    require((method.BALANCE_FORCE_TOL_N, method.BALANCE_MOMENT_TOL_NMM) == (0.1, 2.0), "body limits changed")
    close(method.cross([10., 20., 30.], [2., 3., 4.]), [-10., 20., -10.], "known-answer wrench transport failed")
    geometry, members, candidate_ids = geometry_register(read(FEATURE+"axis-features.json"), pins)
    freeze, projection = read(FREEZE), read(PROJECTION+"projection-contract.json")
    require(set(freeze["cases"]) == {"a1-rear", "a12-rear", "k12-rear"}, "wrong case set")
    require(projection["candidate"] == CANDIDATE and projection["geometry_revision_id"] == REVISION
            and projection["native_solve_executed"] is False, "wrong physical projection")
    states, cases, fingerprints = [], {}, []
    for case, files in freeze["cases"].items():
        model, response, audit = validate_case(case, files, freeze, pins)
        bindings = {axis_id: bind_axis_model(axis_id, entry, model, projection["rows"])
                    for axis_id, entry in geometry.items()}
        retained_raw = [r for r in model["raw_source_carrier_law_inventory_rows"]
                        if r["physical_owner"].get("axis_id") in geometry]
        require(len(retained_raw) == 36, "unaccounted retained raw source channels")
        boundary = body_boundary(model, members)
        descriptor_datums = {body: [(a+b)/2 for a, b in zip(model["body_geometry"][body]["geometry_record"]["start"],
                   model["body_geometry"][body]["geometry_record"]["end"], strict=True)] for body in members}
        datums = {body: audit["increments"][0]["body_equilibrium"][body]["reference_xyz_mm"] for body in members}
        fingerprints.append({"bindings": bindings, "boundary": boundary, "datums": datums})
        cases[case] = {"source_files": files, "retained_scalar_bindings": bindings,
                       "boundary_inventory": boundary, "boundary_interface_count": len(boundary),
                       "boundary_scalar_count": sum(len(r["source_indices"]) for r in boundary),
                       "reporting_datums_xyz_mm": datums, "descriptor_midpoints_xyz_mm": descriptor_datums,
                       "reporting_datum_source": "authenticated all-body audit reference; no centroid interpretation",
                       "load_map": "physical_body_loads before support elimination"}
        for index, saved in enumerate(response["increments"]):
            require(all(saved[g] is True for g in GATES), "source increment gate failed")
            audited = audit["increments"][index]
            require(audited["passed"] is True and audited["numerical_grounds_counted"] == 0
                    and audited["time"] == saved["time"], "source audit state/ground treatment differs")
            inc = copy.deepcopy(saved)
            # The pinned floor adapter iterates a set of tangent names. Restore
            # a stable port order before all force/moment sums and serialization.
            interfaces = dict(sorted(method.response_interfaces(inc, boundary).items()))
            require(set(interfaces) == {r["source_connection_name"] for r in boundary}, "incomplete body boundary")
            for record in boundary:
                method.validate_response_owner(interfaces[record["source_connection_name"]], record, record["source_connection_name"])
            bolts = {}
            for axis_id, binding in bindings.items():
                channels = scalar_actions(binding, inc)
                lateral, axial = interfaces[axis_id+"/wood-interface"], interfaces[axis_id+"/outer-seat-axial-tie"]
                check_interface(lateral, binding[:2], channels[:2], method)
                check_interface(axial, binding[2:], channels[2:], method)
                bolts[axis_id] = {"scalar_channels": channels, "lateral_interface_action": lateral,
                                  "axial_interface_action": axial,
                                  "combined_receiver_actions": endpoint_wrenches(lateral, axial, datums, method)}
            balances = method.member_balance(model, {"corner_body_names": members},
                                             {"descriptor_midpoint_datums_mm": datums}, interfaces, inc["load_factor"])
            for body, balance in balances.items():
                original = audit["increments"][index]["body_equilibrium"][body]
                require(original["printed_resultants_passed"] is True and original["interval_resultants_passed"] is True
                        and balance["raw_balance_passed"] and balance["rounding_interval_balance_passed"], "body gate failed")
                close(datums[body], original["reference_xyz_mm"], "body reporting reference differs")
                for kind, units, tolerance in (("force", "n", 1e-8), ("moment", "nmm", 1e-6)):
                    close(balance["combined_residual_wrench"][kind+"_xyz_"+units],
                          original[kind+"_residual_xyz_"+units], "all-body residual differs", tolerance)
                radius, moment_radius, origin_radius = [0.]*3, [0.]*3, [0.]*3
                for row in interfaces.values():
                    for side in ("first", "second"):
                        if row[side] != body:
                            continue
                        bound = row["force_rounding_radius_xyz_n"]
                        point = row.get(side+"_point", row["point"])
                        radius = plus(radius, bound)
                        moment_radius = plus(moment_radius, method.cross_interval_radius(method.sub(point, datums[body]), bound))
                        origin_radius = plus(origin_radius, method.cross_interval_radius(point, bound))
                close(radius, original["force_rounding_radius_xyz_n"], "all-body force interval differs")
                close(moment_radius, original["moment_rounding_radius_xyz_nmm"], "all-body moment interval differs", 1e-6)
                balance["force_radius_xyz_n"] = radius
                balance["moment_radius_xyz_nmm"] = moment_radius
                balance["moment_radius_about_origin_xyz_nmm"] = origin_radius
                balance["origin_balance_gate_applied"] = False
                balance["datum_status"] = "authenticated all-body audit reference; no physical centroid/cut/support interpretation"
                for label in ("external_load_wrench", "interface_action_wrench", "combined_residual_wrench"):
                    wrench = balance[label]
                    balance[label+"_about_origin"] = {"force_xyz_n": wrench["force_xyz_n"],
                        "moment_xyz_nmm": plus(wrench["moment_xyz_nmm"], method.cross(datums[body], wrench["force_xyz_n"]))}
            states.append({"case_id": case, "increment_index": index, "load_factor": inc["load_factor"],
                           "bolt_states": bolts, "body_balances": balances, "interface_actions": interfaces,
                           "floor_tangent_state_counts": dict(Counter(r.get("floor_tangent_state") for r in interfaces.values()
                                                                       if "floor_tangent_state" in r))})
    require(len(states) == 21 and all(f == fingerprints[0] for f in fingerprints), "case topology/state coverage differs")
    return {"schema": "current_retained_frame_bolt_load_path/v1", "status": "PASS_CURRENT_RETAINED_FORCE_AND_BODY_JOIN_ONLY",
            "candidate": CANDIDATE, "geometry_revision_id": REVISION, "producer_sha256": sha(Path(__file__)),
            "input_pins": dict(sorted(pins.items())), "case_sources": freeze["cases"], "axis_register": geometry,
            "candidate_bolt_axis_ids_separate": candidate_ids, "receiver_bodies": members, "cases": cases,
            "counts": {"retained_axes": 12, "receiver_memberships": 24, "candidate_axes_separate": 92,
                       "states": 21, "bolt_states": 252, "combined_receiver_wrenches": 504,
                       "physical_interface_actions_retained": 504, "complete_body_states": 168,
                       "scalar_retained_channel_states": 756}, "states": states,
            "unmapped_axes": [], "unmapped_receivers": [], "native_solve_executed": False,
            **{key: False for key in ACCEPTANCE}, "joint_accepted": False, "fabrication_release": False,
            "limits": ["Only three conditional rear cases at seven simultaneous factors; no six-case or sensitivity envelope.",
                       "Twelve retained starting bolt arrangements are rechecked; historical demands and capacities do not transfer.",
                       "Physical endpoint forces and transported couples do not establish bolt internal bending or combined resistance.",
                       "All ports touching the eight receiver bodies are retained, including candidate bolts, panel screws, contacts and floor.",
                       "Physical nodal loads precede support elimination; floor reactions stay explicit and numerical ground is not a physical anchor.",
                       "Source body gates remain 0.1 N and 2 Nmm. Arithmetic comparisons use 1e-8 N and 1e-6 Nmm.",
                       "Reporting datum is the authenticated all-body audit reference; descriptor midpoint retained separately. No physical centroid/cut/support interpretation.",
                       "No actual wood, floor or hardware inspected.",
                       "No local stress, complete joint resistance, hardware capacity, acceptance, geometry change or fabrication release."]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(build(), indent=2, allow_nan=False))
