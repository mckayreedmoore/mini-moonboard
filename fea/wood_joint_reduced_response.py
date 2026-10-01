"""Physical response and active-branch checks for the reduced current candidate.

No native execution is hidden here. Each trial is frozen and reviewed before
the coordinator launches it. Numerical checks never confer joint acceptance.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from fea import horizontal_panel_frame as frame
from fea import wood_joint_reduced_force_output
from fea.current_response_run import (
    axial_tension_state,
    configure_radial_clearance,
    next_axial_tension_names,
    next_radial_clearance_states,
    radial_clearance_inventory,
    radial_clearance_state,
)
from fea.wood_joint_reduced_model import normalize_active_groups, oriented_deck
from fea.wood_joint_reduced_native import digest, freeze, verify, write_json


def _balance(entries, reference):
    force, moment, force_radius, moment_radius = (np.zeros(3) for _ in range(4))
    for point, value, radius in entries:
        arm = np.asarray(point)-reference
        value, radius = np.asarray(value), np.asarray(radius)
        force += value
        moment += np.cross(arm, value)
        force_radius += radius
        x, y, z = abs(arm)
        moment_radius += np.array([[0, z, y], [z, 0, x], [y, x, 0]]) @ radius
    force_distance = np.maximum(0., abs(force)-force_radius)
    moment_distance = np.maximum(0., abs(moment)-moment_radius)
    return {"reference_xyz_mm": np.asarray(reference).tolist(),
        "force_residual_xyz_n": force.tolist(), "moment_residual_xyz_nmm": moment.tolist(),
        "force_rounding_radius_xyz_n": force_radius.tolist(),
        "moment_rounding_radius_xyz_nmm": moment_radius.tolist(),
        "force_interval_distance_from_zero_n": force_distance.tolist(),
        "moment_interval_distance_from_zero_nmm": moment_distance.tolist(),
        "printed_resultants_passed": bool(max(abs(force)) <= .1 and max(abs(moment)) <= 2.),
        "interval_resultants_passed": bool(max(force_distance) <= .1 and max(moment_distance) <= 2.),
        "criterion": "0.1 N / 2 Nmm, raw and independently propagated DAT rounding intervals reported separately"}


def assess_record(record, data):
    """Check actual external loads, physical interfaces and every body's balance."""
    ordinary = {**record, "springs": [dict(row, bearing_closed_assumption=False)
        if (row["name"].endswith("_friction") or row.get("tension_only_assumption")
            or row.get("radial_clearance_assumption")) else row for row in record["springs"]]}
    raw = frame.assess(ordinary, data)
    output = frame.panel_kernel.read_blocks(data)
    physical, force_recovery = wood_joint_reduced_force_output.recover(record, raw, data)
    nodes = {int(n): np.asarray(point) for n, point in record["nodes"].items()}
    body_nodes = {name: set(map(int, tags)) for name, tags in record["physical_body_nodes"].items()}
    if not body_nodes or any(not tags for tags in body_nodes.values()):
        raise ValueError("Every physical body must own solid nodes")
    if sum(map(len, body_nodes.values())) != len(set().union(*body_nodes.values())):
        raise ValueError("Physical solid nodes belong to multiple bodies")
    solid_nodes = {int(n) for kind, ids, _ in record["elements"].values() if kind == "C3D20" for n in ids}
    if not solid_nodes and record.get("scope") != "Three disconnected known-answer static method fixtures only; no candidate joint":
        raise ValueError("Candidate response lacks its physical solid mesh")
    if solid_nodes:
        from fea.wood_joint_reduced_geometry import MODEL_INPUTS

        if digest(MODEL_INPUTS) != record["source_model_inputs_sha256"]:
            raise ValueError("Current source body inventory changed")
        source = json.loads(Path(MODEL_INPUTS).read_text())
        if set(body_nodes) != {row["member_id"] for row in source["members"]}:
            raise ValueError("Physical body inventory omits or adds source bodies")
        if set().union(*body_nodes.values()) != solid_nodes:
            raise ValueError("Physical body node inventory does not cover the solid mesh exactly")
    body_loads = record["physical_body_loads"]
    if set(body_loads) != set(body_nodes):
        raise ValueError("Physical body load inventory changed")
    body_entries, all_loads = {}, {}
    for name, loads in body_loads.items():
        if set(map(int, loads))-body_nodes[name]:
            raise ValueError("Physical load lies outside its recorded body")
        body_entries[name] = [(nodes[int(n)], value, np.zeros(3)) for n, value in loads.items()]
        for n, value in loads.items():
            if int(n) in all_loads:
                raise ValueError("Physical load was counted on two bodies")
            all_loads[int(n)] = np.asarray(value)
    declared = {int(n): np.asarray(f) for n, f in record["physical_external_loads"].items()}
    if set(declared) != set(all_loads) or any(not np.allclose(declared[n], f, rtol=0, atol=1e-10)
                                             for n, f in all_loads.items()):
        raise ValueError("Body and global physical load inventories differ")
    global_entries = [(nodes[n], f, np.zeros(3)) for n, f in all_loads.items()]
    for row in physical.values():
        for which in ("first", "second"):
            body = row[which]
            if body == "floor":
                continue
            if body not in body_entries:
                raise ValueError("Unowned physical interface: " + body)
            point = row.get(which+"_point", row["point"])
            entry = (point, row["force_on_"+which+"_xyz_n"], row["force_rounding_radius_xyz_n"])
            body_entries[body].append(entry)
            if row["second" if which == "first" else "first"] == "floor":
                global_entries.append(entry)
    balances = {name: _balance(entries, np.mean([nodes[n] for n in body_nodes[name]], axis=0))
                for name, entries in body_entries.items()}
    global_balance = _balance(global_entries, np.zeros(3))
    tension = axial_tension_state(record, output["displacements"])
    radial = radial_clearance_state(record, output["displacements"])
    contact_pass = raw["closed_bearing_assumption_passed"]
    tension_pass = all(row["tension_only_assumption_satisfied"] for row in tension)
    radial_pass = all(row["radial_clearance_assumption_satisfied"] for row in radial)
    raw_balance_pass = global_balance["printed_resultants_passed"] and all(
        row["printed_resultants_passed"] for row in balances.values())
    interval_balance_pass = global_balance["interval_resultants_passed"] and all(
        row["interval_resultants_passed"] for row in balances.values())
    return {"physical_connection_forces": physical,
        "force_output_recovery_audit": force_recovery,
        "force_output_helper_sha256": digest(wood_joint_reduced_force_output.__file__),
        "body_equilibrium": balances,
        "global_equilibrium": global_balance, "bearings": raw["bearings"],
        "axial_tension": tension, "radial_clearance": radial,
        "mpc_audit": raw["mpc_printed_precision_audit"], "mpc_check_passed": raw["mpc_check_passed"],
        "contact_complementarity_passed": contact_pass,
        "axial_complementarity_passed": tension_pass, "radial_complementarity_passed": radial_pass,
        "all_complementarity_passed": contact_pass and tension_pass and radial_pass,
        "all_raw_equilibrium_passed": raw_balance_pass,
        "all_interval_equilibrium_passed": interval_balance_pass,
        "numerical_checks_passed": raw_balance_pass and raw["mpc_check_passed"]
            and contact_pass and tension_pass and radial_pass,
        "maximum_node_displacement_mm": raw["maximum_node_displacement_mm"],
        "mechanical_acceptance": False, "qualified_for_design": False,
        "limits": ["Raw and interval equilibrium gates are distinct; wide rounding intervals are not precise forces",
                   "RF-derived force intervals are output-rounding bounds for isolated linear SPRING2 endpoint DOFs, cross-checked against printed U intervals; they do not qualify the connector law",
                   "Conditional stiffness/contact response does not establish product capacity or actual floor support",
                   "All physical loads exclude auxiliary local gap-reference CLOADs"]}


def next_state(structure, report):
    active = frame.next_bearing_set(report["bearings"])
    active |= next_axial_tension_names(report["axial_tension"])
    radial = next_radial_clearance_states(report["radial_clearance"])
    active |= {name for name, normal in radial.items() if normal is not None}
    return normalize_active_groups(structure, active), radial


def freeze_trial(directory, structure, metadata, *, active_groups, radial_states, extra_sources=()):
    """Freeze one explicit active branch; does not authorize or launch it."""
    active = normalize_active_groups(structure, active_groups)
    if set(radial_states) != set(radial_clearance_inventory(structure.springs)):
        raise ValueError("Radial state inventory differs from current model")
    if any((normal is not None) != (name in active) for name, normal in radial_states.items()):
        raise ValueError("Radial active groups and normals disagree")
    base_loads = {int(n): np.asarray(f) for n, f in metadata["physical_external_loads"].items()}
    corrections = configure_radial_clearance(structure, radial_states, base_loads)
    structure.loads = {n: f.tolist() for n, f in structure.loads.items()}
    frozen_metadata = {**metadata, "radial_clearance_reference_loads": corrections,
        "trial_active_groups": sorted(active), "trial_radial_states": radial_states}
    deck = oriented_deck(structure, metadata["material_binding"], active_bearings=active)
    return freeze(directory, structure, frozen_metadata, [__file__, *extra_sources],
                  deck_text=deck, active_bearings=active)


def assess_directory(directory):
    from fea.wood_joint_reduced_native import LEDGER, ROOT

    directory = Path(directory)
    verify(directory, check_live=False)
    execution = json.loads((directory/"execution.json").read_text())
    ledger = json.loads(LEDGER.read_text())
    matches = [row for row in ledger["runs"] if row["run_id"] == execution["run_id"]]
    if len(matches) != 1:
        raise ValueError("Native execution is not uniquely registered")
    registered = matches[0]
    if (registered["execution_record_sha256"] != digest(directory/"execution.json")
            or registered["input_freeze_sha256"] != digest(directory/"freeze.json")
            or (ROOT/registered["attempt_directory"]).resolve() != directory.resolve()
            or registered["state"] != "consumed_terminal" or registered["launches_consumed"] != 1):
        raise ValueError("Native execution does not match the consumed ledger entry")
    if execution.get("returncode") != 0 or not execution.get("container_confirmed_terminal"):
        raise ValueError("Native execution did not complete successfully")
    for name, expected in execution["outputs_sha256"].items():
        if digest(directory/name) != expected:
            raise ValueError("Native output changed: " + name)
    log = (directory/"native.stdout").read_text()+(directory/"native.stderr").read_text()
    if "*ERROR" in log.upper():
        raise ValueError("Native log reports an error")
    record = json.loads((directory/"model.json").read_text())
    report = assess_record(record, (directory/"model.dat").read_text())
    report.update(native_execution_verified=True, native_solve_executed=True,
                  input_freeze_sha256=digest(directory/"freeze.json"),
                  postprocessor_sha256=digest(__file__),
                  force_output_helper_path="fea/wood_joint_reduced_force_output.py",
                  native_warnings=[line for line in log.splitlines() if "WARNING" in line.upper()])
    if report["native_warnings"]:
        report["numerical_checks_passed"] = False
    write_json(directory/"response.json", report)
    return report


def self_check():
    """Replay the completed known-answer fixture; do not run a solver."""
    from copy import deepcopy

    root = Path(__file__).resolve().parents[1]
    directory = root/"docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-methods-attempt02"
    verify(directory, check_live=False)
    record = json.loads((directory/"model.json").read_text())
    record.update(physical_body_nodes={}, physical_body_loads={}, physical_external_loads={})
    for check in record["checks"]:
        owner = record["connection_ownership"][check["name"]]
        first_ground = owner["first"] == "ground"
        body = owner["second"] if first_ground else owner["first"]
        owner["first" if first_ground else "second"] = "floor"
        force = np.asarray(check["expected_force_on_first_n"])*(1 if first_ground else -1)
        record["physical_body_nodes"][body] = [check["node"]]
        record["physical_body_loads"][body] = {check["node"]: force.tolist()}
        record["physical_external_loads"][check["node"]] = force.tolist()
    data = (directory/"model.dat").read_text()
    result = assess_record(record, data)
    if not result["numerical_checks_passed"]:
        raise AssertionError("Known-answer physical-body response audit failed")
    if result["force_output_recovery_audit"]["status"] != "PASS_ISOLATED_SPRING_RF_ACTION_REACTION_AND_KDU_INTERVALS":
        raise AssertionError("Known-answer RF force-output recovery failed")
    perturbed = deepcopy(record)
    body = next(iter(perturbed["physical_body_loads"]))
    node = next(iter(perturbed["physical_body_loads"][body]))
    perturbed["physical_body_loads"][body][node][0] += 1.
    perturbed["physical_external_loads"][node][0] += 1.
    negative = assess_record(perturbed, data)
    if negative["all_interval_equilibrium_passed"] or negative["numerical_checks_passed"]:
        raise AssertionError("Missing reaction to injected 1 N load was not detected")
    perturbed = deepcopy(record)
    bodies = list(record["physical_body_loads"])[:2]
    tags = [next(iter(record["physical_body_loads"][body])) for body in bodies]
    direction = np.asarray(record["nodes"][str(tags[1])])-record["nodes"][str(tags[0])]
    direction /= np.linalg.norm(direction)
    for body, node, sign in zip(bodies, tags, (1., -1.), strict=True):
        value = (np.asarray(perturbed["physical_body_loads"][body][node])+sign*direction).tolist()
        perturbed["physical_body_loads"][body][node] = value
        perturbed["physical_external_loads"][node] = value
    local_negative = assess_record(perturbed, data)
    if not local_negative["global_equilibrium"]["printed_resultants_passed"]:
        raise AssertionError("Collinear opposite perturbations should preserve global equilibrium")
    if local_negative["all_interval_equilibrium_passed"] or local_negative["numerical_checks_passed"]:
        raise AssertionError("Individual-body imbalance hidden by global cancellation was not detected")
    return {"known_native_fixture_replay_passed": True, "unbalanced_load_detected": True,
            "body_imbalance_with_global_balance_detected": True,
            "rf_force_output_recovery_passed": True,
            "force_output_helper_sha256": digest(wood_joint_reduced_force_output.__file__),
            "native_solve_executed": False, "mechanical_acceptance": False}


if __name__ == "__main__":
    print(json.dumps(self_check()))
