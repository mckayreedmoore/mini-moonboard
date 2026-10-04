"""Source-bound prescribed-force recovery of the 100 retained scalar shafts.

Import is inert. Preparation reads saved forces and finished geometry only.
Project field calls are parent-owned; an isolated field does not replace the
coupled frame's scalar laws or establish compatible global curvature.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/joint-frame-shaft-recovery"
API = HERE / "all-joint-splitting/closure.py"
DIRECT = HERE / "joint-frame-bolt-reference.py"
RECOVERY = HERE / "bolt-reference-completion.py"
G7 = HERE / "g7-shaft-completion.py"
PROFILE = HERE / "washer-working-profile-completion.py"
PROFILE_PACKET = HERE / "rawlocal/washer-working-profile-completion/preparation01"
PROFILE_RECEIPT = "8f64eabfd382d51b2cf5cf0aa67c2149bc13cb7ea825ebe076572c80418a89c1"
PROFILE_CONTRACT = "793848a80900c4fc8f13472f148680b96cf588b58ab5c455ae5aea7a408e9f93"
PINS = {
    API: "095cc122b4f0292fecd108446c24744a2671a703d156527afcd243eb8de9035d",
    DIRECT: "b543630283f495d6ee31b9cd8a711e65a95b911d7adc74c7ad4610511ecc9805",
    RECOVERY: "b0d45007a15e4de08f7c6a3d69194e7e434f43c96a221d02cf1382e1c17eb56f",
    G7: "cd711362d1e9bba7977692f4e4f130945dfade1f98e4b8b652dfa7e52fc9cd44",
    PROFILE: "6dd34bc0bd0d92da590cfedff8cdbfc6305843161e2cd95102b397e8eb9525f4",
}
FLAGS = {"common_host_compatibility_established": False,
         "globally_compatible_scalar_shaft_curvature_established": False,
         "isolated_fields_used_to_refresh_global_forces": False,
         "historical_force_or_acceptance_transferred": False,
         "actual_washer_metal_stress_complete": False,
         "complete_joint_acceptance": False, "physical_release": False,
         "reviewed_geometry_changed": False, "native_or_CAD_or_frame_run": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open("x") as stream:
        rows = value if str(path).endswith(".jsonl") else [value]
        stream.writelines(json.dumps(row, sort_keys=True, allow_nan=False) + "\n" for row in rows)


def context():
    for path, digest in PINS.items():
        require(sha(path) == digest, "maintained helper differs: " + str(path))
    api = module(API, "prescribed_shaft_bindings")
    p = module(RECOVERY, "prescribed_shaft_recovery_helpers")
    direct = module(DIRECT, "prescribed_shaft_direct_helpers")
    pins = dict(PINS)
    for path in (p.SHAFT, p.TRACTION, p.REFERENCE_LOADER, p.HARDWARE, p.HARDWARE_AXES,
                 p.FEATURES, p.FEATURE_METHOD, p.GEOMETRY_METHOD, p.CONTACT, p.STEEL,
                 ROOT / "pyproject.toml", ROOT / "uv.lock"):
        api.bind(pins, path, p.PINS[path])
    for path in (direct.RETAINED, direct.LATERAL, direct.OPERATORS / "model-inputs.json",
                 direct.OPERATORS / "row-identities.json", ROOT / "fea/dowel_yield.py"):
        api.bind(pins, path, direct.PINS[path])
    api.bind(pins, Path(__file__).resolve(), sha(__file__))
    api.authenticate(pins)
    return api, p, direct, pins


def category(axis, bolt):
    if axis == "center_principal_right_2":
        return "restricted_center_ring"
    if axis.startswith("wj04_g7/"):
        return "upper_G7"
    if axis.startswith("top_outer/"):
        return "top_rail_wider" if "/rail_" in axis else "top_side_source_quarter_mismatch"
    if axis.startswith("bottom_outer/"):
        return "bottom_outer"
    if bolt["kind"] == "retained_bolt":
        return "retained_frame"
    if "base_header" in bolt["receiver_member_ids"]:
        return "header_endgrain"
    return "ordinary_two_host"


def pilot_inventory(records):
    selected = {}
    for name in sorted({r["pilot_family"] for r in records}):
        group = [r for r in records if r["pilot_family"] == name]
        choices = [("maximum_V", max(group, key=lambda r: r["V_n"])),
                   ("maximum_T", max(group, key=lambda r: r["signed_T_n"]))]
        positive = [r for r in group if r["signed_T_n"] > 0]
        if positive:
            choices.append(("minimum_positive_T", min(positive, key=lambda r: r["signed_T_n"])))
        zero_gap = [r for r in group if r["gap_scale"] == 0]
        if zero_gap:
            choices.append(("maximum_V_zero_effective_gap", max(zero_gap, key=lambda r: r["V_n"])))
        for reason, row in choices:
            selected.setdefault((row["state_tag"], row["axis_id"]), []).append(name + ":" + reason)
    return [{"state_tag": tag, "axis_id": axis, "selection_reasons": reasons}
            for (tag, axis), reasons in sorted(selected.items())]


def prepare_sources(actions, expected_receipt, force_branch):
    import numpy as np

    require(np.__version__ == "2.5.2", "NumPy runtime differs")
    api, p, direct, pins = context()
    actions = Path(actions).resolve()
    require(actions.is_relative_to(HERE / "rawlocal") and sha(actions / "receipt.json") == expected_receipt,
            "action packet receipt differs")
    api.bind(pins, actions / "receipt.json", expected_receipt)
    api.receipt_sources(pins, actions / "receipt.json")
    summary, inputs = read(actions / "summary.json"), read(actions / "inputs.json")
    require(summary["action_exports_complete_for_accepted_states"] is True,
            "action export is incomplete for its actual accepted states")
    response = ROOT / inputs["response"]
    require(response / "comparison.json" in pins and response / "response.npz" in pins,
            "saved compatible response is outside action closure")
    frame = read(response / "comparison.json")
    scope = direct.accepted_scope(api, pins, response, summary, frame)
    require(frame["reviewed_geometry_changed"] is False, "reviewed geometry changed")
    api.bind(pins, PROFILE_PACKET / "receipt.json", PROFILE_RECEIPT)
    api.receipt_sources(pins, PROFILE_PACKET / "receipt.json")
    require(sha(PROFILE_PACKET / "profile-contract.json") == PROFILE_CONTRACT, "working profile contract changed")
    contract = read(PROFILE_PACKET / "profile-contract.json")
    profile_api = module(PROFILE, "prescribed_shaft_profiles")
    api.authenticate(pins)
    geometry = read(direct.OPERATORS / "model-inputs.json")
    identities = read(direct.OPERATORS / "row-identities.json")
    bolts = {b["axis_id"]: b for b in geometry["connections"]
             if b["kind"] in ("candidate_bolt", "retained_bolt") and b["axis_id"] not in direct.CONTINUOUS}
    require(len(bolts) == 100 and len(identities) == 1888, "canonical scalar axis/row census differs")
    members = {m["member_id"]: m["reduced_geometry_descriptor"] for m in geometry["members"]
               if m["member_kind"] != "panel"}
    references = p.load_module(p.REFERENCE_LOADER, "prescribed_shaft_pure_references")
    hardware = p.load_module(p.HARDWARE, "prescribed_shaft_hardware")
    for path, digest in hardware.PINS.items():
        api.bind(pins, ROOT / path, digest)
    retained = read(direct.RETAINED)
    with p.HARDWARE_AXES.open(newline="") as stream:
        family_ids = {r["axis_id"]: r["family_id"] for r in csv.DictReader(stream)}
    feature_records = read(p.FEATURES)["records"]
    features = {f["feature_id"]: f for m in feature_records for f in m["features"]}
    proof = p.geometry_precision_proof(api, geometry, feature_records)
    families, records = {}, []
    source_join = {"force_branch": force_branch, "action_packet": api.key(actions),
                   "action_receipt_sha256": expected_receipt,
                   "action_raw_force_path": api.key(actions / "source-row-response.npz"),
                   "action_raw_force_sha256": pins[actions / "source-row-response.npz"],
                   "profile_contract_path": api.key(PROFILE_PACKET / "profile-contract.json"),
                   "profile_contract_sha256": PROFILE_CONTRACT, "profile_receipt_sha256": PROFILE_RECEIPT,
                   "profile_api_sha256": PINS[PROFILE], "response": inputs["response"],
                   "source_force_basis": inputs["source_force_basis"]}
    with np.load(actions / "source-row-response.npz", allow_pickle=False) as saved:
        expected = {"canonical_raw_row_available", "canonical_raw_row_to_kept_lumped_position", "old_kept_lumped_rows"}
        expected |= {s["state_tag"] + suffix for s in summary["states"] for suffix in
                     ("_raw_force_n", "_kept_lumped_relative_motion_mm", "_coupled_force_n")}
        require(set(saved.files) == expected, "missing or rejected state force fields exported")
        available = saved["canonical_raw_row_available"]
        require(available.shape == (1888,) and np.count_nonzero(~available) == 20, "replaced row mask differs")
        for state in summary["states"]:
            force = saved[state["state_tag"] + "_raw_force_n"]
            require(force.shape == (1888,) and np.isfinite(force).all(), "nonfinite raw source forces")
            for axis, bolt in sorted(bolts.items()):
                owned = [r for r in identities if r["row_id"].startswith(axis + "/")]
                planes = [r for r in owned if "bolt_lateral_plane" in r["ownership"]["role"]]
                ties = [r for r in owned if r["ownership"]["role"] == "physical_bolt_outer_seat_tension"]
                require(len(planes) == 2 and len(ties) == 1 and planes[0]["row_id"] == planes[1]["row_id"],
                        "scalar plane/tie ownership differs: " + axis)
                indices = [r["row"] for r in planes]
                tie = ties[0]
                require(available[indices].all() and available[tie["row"]], "unavailable placeholder used as demand")
                bodies = [planes[0]["ownership"][k] for k in ("first_body", "second_body")]
                require(set(bodies) == set(bolt["receiver_member_ids"]) and all(
                    [r["ownership"][k] for k in ("first_body", "second_body")] == bodies for r in planes),
                    "physical lateral receiver join differs")
                basis = np.asarray([r["ownership"]["direction_global_xyz"] for r in planes])
                direction = np.asarray(references.unit(bolt["axis_xyz"]))
                require(np.max(abs(basis @ basis.T - np.eye(2))) < 1e-8 and np.max(abs(basis @ direction)) < 1e-8,
                        "physical transverse basis differs")
                components = force[indices]
                vector = components @ basis
                tension = float(force[tie["row"]])
                require(tension >= 0, "negative tension outside prescribed compression-contact method")
                if bolt["kind"] == "retained_bolt":
                    spans = {r["member"]: [r["interval_from_axis_datum_mm"]]
                             for r in retained["axis_register"][axis]["finished_receivers"]}
                    diameter = retained["axis_register"][axis]["hardware_policy"]["nominal_diameter_in"] * 25.4
                else:
                    geom = bolt["source_record"]["geometry"]
                    spans = {r["receiver_id"]: r["current_shaft_intersection_solid_intervals_from_underhead_mm"]
                             for r in geom["wood_receiver_intervals"]}
                    diameter = geom["modeled_shaft_diameter_mm"]
                require(set(spans) == set(bodies) and all(len(v) == 1 for v in spans.values()), "bearing spans differ")
                lengths = [spans[b][0][1] - spans[b][0][0] for b in bodies]
                row = {"state_tag": state["state_tag"], "case_id": state["case_id"], "gap_scale": state["gap_scale"],
                       "axis_id": axis, "kind": bolt["kind"], "receivers": bodies, "bearing_lengths_mm": lengths,
                       "modeled_full_body_diameter_in": diameter / 25.4, "source_diameter_mm": diameter,
                       "point_xyz_mm": planes[0]["ownership"]["point_mm"], "signed_T_n": tension,
                       "signed_axial_n": tension, "components_n": components.tolist(),
                       "component_directions_xyz": basis.tolist(), "force_on_first_body_xyz_n": vector.tolist(),
                       "force_on_second_body_xyz_n": (-vector).tolist(), "V_n": float(np.linalg.norm(vector)),
                       "component_rows": indices, "tie_row": tie["row"],
                       "source_state_record": scope["accepted_source_records"][(state["case_id"], state["gap_scale"])],
                       "source_force_array": state["state_tag"] + "_raw_force_n",
                       "duration_factor": state["duration_factor_for_downstream_strength"],
                       "pilot_family": category(axis, bolt)}
                require(all(r["ownership"]["point_mm"] == row["point_xyz_mm"] for r in planes), "mixed force planes")
                if axis not in families:
                    catalog = hardware.STACKS[hardware.ROUTES[family_ids[axis]][0]]
                    if not math.isclose(catalog["diameter_mm"], diameter, abs_tol=1e-6):
                        catalog = hardware.STACKS["qtr_kl"]
                    evidence = {"original_bearing_lengths_mm": lengths, "original_source_interface_xyz_mm": row["point_xyz_mm"]}
                    geometry_limit = None
                    try:
                        family, order, shaft_direction, partial = p.geometry_for(
                            row, bolt, retained, features, catalog, references.unit, references.dot, api, pins, proof, evidence)
                    except p.UnsupportedGeometry as error:
                        require(axis.startswith("top_outer/") and "/side_" in axis
                                and str(error) == "source lateral plane is not the physical two-host interface; an imposed couple would be needed",
                                "unexpected geometry limit on " + axis + ": " + str(error))
                        geometry_limit = str(error)
                        direction_data = bolt["source_record"]["geometry"]
                        shaft_direction = references.unit(direction_data["axis_head_to_nut_global"])
                        ordered = sorted((b, v[0]) for b, v in spans.items())
                        ordered.sort(key=lambda item: item[1][0])
                        order = [b for b, _interval in ordered]
                        datum = np.asarray(direction_data["shaft_center_global_xyz_mm"]) - np.asarray(shaft_direction) * direction_data["modeled_shaft_occupied_length_mm"] / 2
                        physical = datum + np.asarray(shaft_direction) * ordered[0][1][1]
                        evidence.update({"physical_interface_point_xyz_mm": physical.tolist(),
                                         "source_to_physical_interface_offset_xyz_mm": (np.asarray(row["point_xyz_mm"]) - physical).tolist(),
                                         "source_to_physical_interface_offset_mm": float(np.linalg.norm(np.asarray(row["point_xyz_mm"]) - physical)),
                                         "unsupported_source_couple_is_not_dropped": True})
                        family, partial = None, False
                    profile = profile_api.profile_for_axis(contract, axis, diameter, mode="source")
                    require(partial is profile["partial_supported_ring_route"], "restricted ring profile differs")
                    if family is not None:
                        family.update(profile["shaft_contact"])
                        require(family["washer_ID_max_mm"] / 2 < family["flat_radius_mm"] <= family["washer_OD_min_mm"] / 2,
                                "working source contact ring is empty")
                        lever = np.asarray(tie["ownership"]["point_mm"]) - np.asarray(row["point_xyz_mm"])
                        require(np.linalg.norm(np.cross(lever, shaft_direction)) < 1e-5, "eccentric axial tie needs unsupported couple")
                    families[axis] = {"family": family, "receivers_head_to_nut": order, "direction": shaft_direction,
                                      "partial": partial, "profile": profile, "catalog": catalog,
                                      "geometry_applicability": evidence, "geometry_limit": geometry_limit,
                                      "grain_axes_xyz": {b: members[b]["axis"] for b in bodies}}
                if families[axis]["geometry_limit"] is not None:
                    physical = np.asarray(families[axis]["geometry_applicability"]["physical_interface_point_xyz_mm"])
                    lateral_couple = np.cross(np.asarray(row["point_xyz_mm"]) - physical, vector)
                    axial_direction = np.asarray(tie["ownership"]["direction_global_xyz"])
                    axial_first_body = tension * axial_direction
                    axial_couple = np.cross(np.asarray(tie["ownership"]["point_mm"]) - physical, axial_first_body)
                    row["unrepresented_source_couples_at_physical_interface"] = {
                        "lateral_source_force_on_first_body_xyz_n": vector.tolist(),
                        "lateral_force_equivalent_couple_on_first_body_xyz_nmm": lateral_couple.tolist(),
                        "signed_lateral_torsion_about_shaft_axis_nmm": float(lateral_couple @ np.asarray(families[axis]["direction"])),
                        "source_tie_point_xyz_mm": tie["ownership"]["point_mm"],
                        "source_tie_outer_seat_points_mm": tie["outer_seat_points_mm"],
                        "axial_source_force_on_first_body_xyz_n": axial_first_body.tolist(),
                        "axial_force_equivalent_couple_on_first_body_xyz_nmm": axial_couple.tolist(),
                        "second_body_couples_opposite": True, "couples_omitted_from_any_accepted_field": False}
                row["source_join"] = {**source_join, "source_state_record": row["source_state_record"],
                                      "source_rows": indices + [tie["row"]], "source_force_array": row["source_force_array"]}
                records.append(row)
    limited = {(r["state_tag"], r["axis_id"]): r for r in records
               if "unrepresented_source_couples_at_physical_interface" in r}
    by_body = {}
    for key, row in limited.items():
        by_body.setdefault((row["state_tag"], row["receivers"][0]), []).append(key)
    with gzip.open(actions / "body-actions.jsonl.gz", "rt") as stream:
        for line in stream:
            body = json.loads(line)
            for key in by_body.get((body["state_tag"], body["body"]), []):
                row = limited[key]
                selected = [a for a in body["actions"] if a.get("row") in row["component_rows"] + [row["tie_row"]]]
                require(len(selected) == 3 and all(a["source_force_available"] is True
                        and a["replaced_source_row_placeholder"] is False for a in selected),
                        "source couple body-action join differs")
                lateral_actions = [a for a in selected if a["row"] in row["component_rows"]]
                axial_action = next(a for a in selected if a["row"] == row["tie_row"])
                require(np.max(abs(sum((np.asarray(a["force_n"]) for a in lateral_actions), np.zeros(3))
                                   - row["force_on_first_body_xyz_n"])) < 1e-8,
                        "sourceD signed lateral/body export differs")
                require(np.max(abs(np.asarray(axial_action["force_n"]) - row[
                        "unrepresented_source_couples_at_physical_interface"]["axial_source_force_on_first_body_xyz_n"])) < 1e-8,
                        "sourceD signed axial/body export differs")
                physical = np.asarray(families[row["axis_id"]]["geometry_applicability"]["physical_interface_point_xyz_mm"])
                def couple(action, physical=physical):
                    return np.cross(np.asarray(action["point_mm"]) - physical, action["force_n"]) + action["free_moment_nmm"]
                row["unrepresented_source_couples_at_physical_interface"].update({
                    "exact_source_body_actions_on_first_body": selected,
                    "exported_lateral_full_force_equivalent_couple_xyz_nmm": sum(
                        (couple(a) for a in lateral_actions), np.zeros(3)).tolist(),
                    "exported_axial_full_force_equivalent_couple_xyz_nmm": couple(axial_action).tolist(),
                    "body_action_path": api.key(actions / "body-actions.jsonl.gz"),
                    "body_action_sha256": pins[actions / "body-actions.jsonl.gz"]})
    require(all("exact_source_body_actions_on_first_body" in r["unrepresented_source_couples_at_physical_interface"]
                for r in limited.values()), "missing source physical action for a limited axis state")
    require(len(records) == 100 * scope["accepted_states"] and len(families) == 100, "current source recovery census differs")
    api.authenticate(pins)
    public_scope = {k: v for k, v in scope.items() if k != "accepted_source_records"}
    return api, pins, {"schema": "joint_frame_prescribed_shaft_inputs/v1", "source_join": source_join,
                       "force_branch": force_branch, "families": families, "records": records,
                       "pilot_inventory": pilot_inventory(records), "accepted_scope": public_scope, **FLAGS}


def known_answer(p, np):
    helper = p.load_module(p.SHAFT, "prescribed_shaft_oracle_kernel")
    family = {"host_length_mm": 38.1, "cleat_length_mm": 88.9, "diameter_mm": 6.35,
              "bore_mm": 7.5, "washer_ID_max_mm": 8.3058, "washer_OD_min_mm": 25.4, "flat_radius_mm": 5.}
    helper.LENGTH = 127.
    first_order = p.load_module(HERE / "corner-first-order.py", "prescribed_shaft_cantilever")
    beam = first_order.cantilever_coupon(helper, family)
    annulus = helper.annulus(family["washer_ID_max_mm"] / 2, family["washer_OD_min_mm"] / 2)
    contact = []
    area = math.pi * ((family["washer_OD_min_mm"] / 2)**2 - (family["washer_ID_max_mm"] / 2)**2)
    for tension in (0., 1e-18, 1e-12, 10., 1000.):
        result = helper.compression(tension, 0., p.KWOOD, annulus)
        expected = tension / (p.KWOOD * area)
        require(abs(result["closure_mm"] - expected) <= 1e-13 * max(1., expected), "concentric closure known answer differs")
        require(abs(result["force_residual_n"]) <= 1e-12 * max(1., tension), "concentric force known answer differs")
        require(tension == 0 or result["active_area_mm2"] > 0, "tiny positive tension changed to inactive contact")
        contact.append({"T_n": tension, "expected_closure_mm": expected, "returned": result})
    g7 = module(G7, "prescribed_shaft_zero_T_oracle")
    return {"cantilever": beam, "prescribed_concentric_contact": contact, "zero_T_gap_null_oracle": g7.oracle(np),
            "geometry_or_project_forces_used": False, "project_shaft_calls": 0}


def zero_T_seed(p, helper, family, source, initial, np):
    elastic, _, samples, _, _ = helper.beam_model(family, 0.)
    length = helper.LENGTH
    nodes = np.r_[np.linspace(0., family["host_length_mm"], 9),
                  np.linspace(family["host_length_mm"], length, 9)[1:]]
    rigid = np.zeros((36, 4))
    rigid[:34:2, 0] = 1.
    rigid[:34:2, 1] = nodes / length
    rigid[1:34:2, 1] = 1.
    rigid[34, 2] = rigid[35, 3] = 1.
    require(np.max(abs(elastic @ rigid)) < 1e-6, "analytical zero-curvature vectors differ")
    rows = np.vstack([s[0] for s in samples])
    weights = p.KWOOD * family["diameter_mm"] * np.asarray([s[1] for s in samples])
    gaps = np.full(48, (family["bore_mm"] - family["diameter_mm"]) / 2)
    linear = np.zeros(36)
    linear[34] = -source["V_n"]
    g7 = module(G7, "prescribed_shaft_zero_T_initializer")
    return g7.initializer(elastic, rows, weights, gaps, linear, rigid, initial, np)


def recover(preparation, expected_receipt, all_states):
    import clarabel
    import numpy as np
    import scipy
    from scipy import sparse

    require(np.__version__ == "2.5.2" and scipy.__version__ == "1.18.1" and clarabel.__version__ == "0.11.1",
            "recorded numerical runtimes differ")
    api, p, direct, pins = context()
    preparation = Path(preparation).resolve()
    require(preparation.parent == RAW and sha(preparation / "receipt.json") == expected_receipt,
            "prepared current source packet differs")
    api.bind(pins, preparation / "receipt.json", expected_receipt)
    api.receipt_sources(pins, preparation / "receipt.json")
    inputs = read(preparation / "input-plan.json")
    require(not all_states or inputs["force_branch"] == "washer_updated_compatible_frame",
            "all100 final recovery requires new washer-updated compatible action forces")
    api.authenticate(pins)
    helper = p.load_module(p.SHAFT, "prescribed_shaft_current_kernel")
    beam_model = helper.beam_model

    def first_order(family, tension):
        elastic, geometric, samples, curvatures, inertia = beam_model(family, tension)
        return elastic, np.zeros_like(geometric), samples, curvatures, inertia

    helper.beam_model = first_order
    solve, contract = p.seeded_shaft_solver(helper)
    references = p.load_module(p.REFERENCE_LOADER, "prescribed_shaft_pressure_references")
    traction = references.pure_functions(p.TRACTION, ["action", "wrench", "wood_seat", "shifted"],
                                        {"np": np, "require": require})
    lateral = module(direct.LATERAL, "prescribed_shaft_lateral_reference")
    steel = module(p.STEEL, "prescribed_shaft_direct_reference")
    selected = {(r["state_tag"], r["axis_id"]) for r in inputs["pilot_inventory"]}
    records = [r for r in inputs["records"] if all_states or (r["state_tag"], r["axis_id"]) in selected]
    states, fields, ends, traces = [], [], [], []
    for record in records:
        started = time.monotonic()
        geom = inputs["families"][record["axis_id"]]
        family = dict(geom["family"]) if geom["family"] is not None else None
        original_bore = family["bore_mm"] if family is not None else None
        if family is not None:
            family["bore_mm"] = family["diameter_mm"] + record["gap_scale"] * (original_bore - family["diameter_mm"])
            helper.LENGTH = family["host_length_mm"] + family["cleat_length_mm"]
        order, axis = geom["receivers_head_to_nut"], np.asarray(geom["direction"])
        host_force = np.asarray(record["force_on_first_body_xyz_n"] if order[0] == record["receivers"][0]
                                else record["force_on_second_body_xyz_n"])
        arbitrary = record["V_n"] == 0
        drive = np.asarray(record["component_directions_xyz"][0]) if arbitrary else -host_force / record["V_n"]
        rotation = np.cross(axis, drive)
        source = {k: record[k] for k in ("case_id", "gap_scale", "state_tag", "axis_id", "signed_T_n", "V_n")}
        source.update({"drive_unit_xyz": drive.tolist(), "rotation_axis_xyz": rotation.tolist(),
                       "lateral_direction_arbitrary": arbitrary, "physical_interface_point_xyz_mm": record["point_xyz_mm"],
                       "shaft_axis_head_to_nut_xyz": axis.tolist(), "receivers_head_to_nut": order,
                       "Fe_mpa": {role: lateral.bearing(lateral.angle(host_force, references.unit(geom["grain_axes_xyz"][body])))
                                  * p.PSI_MPA for role, body in zip(("host", "cleat"), order, strict=True)}})
        trace = []

        def log(event, iteration, pose, evaluation, trace=trace, **extra):
            entry = {"event": event, "iteration": iteration, "pose_scaled_mm": pose.tolist()}
            if evaluation is not None:
                entry["energy_nmm"] = float(evaluation[0])
                entry["scaled_gradient_inf_n"] = float(np.max(abs(evaluation[1])))
            for key in ("fraction", "backtrack", "slope", "converged"):
                if key in extra:
                    entry[key] = extra[key]
            trace.append(entry)

        state, beam_fields, bore_fields, seed_info, error = None, [], [], None, None
        try:
            require(family is not None, geom["geometry_limit"])
            require(np.max(abs(np.column_stack((axis, drive, rotation)).T @ np.column_stack((axis, drive, rotation)) - np.eye(3))) < 1e-8,
                    "current signed drive basis is not orthonormal")
            initial, seed_info = p.shaft_convex_seed(source, family, helper, np, sparse, clarabel)
            if record["signed_T_n"] == 0:
                initial, null_info = zero_T_seed(p, helper, family, source, initial, np)
                seed_info["zero_T_rank_initializer"] = null_info
            state, beam_fields, bore_fields = solve(source, family, p.KWOOD, initial, log)
            require(len(beam_fields) == 80 and len(bore_fields) == 48, "unchanged field recovery census differs")
            require(max(abs(np.asarray(state["scaled_gradient_residuals_n"]))) <= 1e-6,
                    "original scaled stationary gate differs")
            require(abs(state["host_force_balance_residual_n"]) <= 1e-6
                    and abs(state["host_moment_balance_residual_nmm"]) <= helper.LENGTH * 1e-6,
                    "physical host force/moment equilibrium gates differ")
        except (ValueError, ArithmeticError, np.linalg.LinAlgError) as caught:
            error = str(caught)
            state, beam_fields, bore_fields = None, [], []
        identity = {k: record[k] for k in ("state_tag", "case_id", "gap_scale", "axis_id", "kind")}
        dref = direct.direct(steel, record["signed_T_n"], record["components_n"], round(record["source_diameter_mm"] / 25.4, 8) * 25.4)
        shaft_index = state["peak_beam_stress_witness"]["proxy_over_conditional_92ksi_Fyb"] if state else None
        steel_index = max(shaft_index, dref["interaction_utilization"], dref["tension_first_yield_utilization"]) if state else None
        row = {**identity, "source_join": record["source_join"], "source_record": record,
               "working_profile": geom["profile"], "original_bore_mm": original_bore,
               "effective_family": family, "state": state, "direct_T_V_reference": dref,
               "shaft_same_state_same_position_index": shaft_index, "same_state_steel_index": steel_index,
               "shaft_null_reason": error, "status": "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" if family is None else
               "STOP_NUMERICAL_FIELD_UNAVAILABLE" if state is None else
               "REFERENCE_EXCEEDANCE" if steel_index > 1. else "SUPPORTED_ISOLATED_CURRENT_FORCE_FIELD",
               "isolated_prescribed_current_force_field": True, **FLAGS}
        for end_index in (0, 1):
            end = p.washer_end_source(record, state, family, order, geom["direction"], geom["partial"], geom["catalog"],
                                      end_index, record["source_join"], helper, traction, np, error, geom["geometry_applicability"])
            end.update({"schema": "joint_frame_prescribed_shaft_own_end/v1", "scope": "isolated_prescribed_current_force",
                        "force_branch": inputs["force_branch"], "state_tag": record["state_tag"],
                        "working_profile": geom["profile"], "saved_contact_initialization_only_for_actual_plate": True,
                        "join_key": [inputs["force_branch"], record["state_tag"], record["axis_id"],
                                     end["end_role"], end["receiver_member"]], **FLAGS})
            if family is not None:
                end["contact_hypotheses"].update({
                    "physical_original_bore_radius_mm": original_bore / 2,
                    "wood_contact_ring_overlaps_bore_void": family["washer_ID_max_mm"] < original_bore,
                    "source_ring_actual_bore_trim_qualified": False,
                    "support_limit": "Hypothetical concentric source ring; actual bore-trimmed plate contact remains separate"})
            ends.append(end)
        states.append(row)
        if state is not None:
            fields.append({**identity, "beam_fields": beam_fields, "bore_fields": bore_fields})
        traces.append({**identity, "seed": seed_info, "original_solver_trace": trace,
                       "error": error, "elapsed_seconds": time.monotonic() - started})
        print(json.dumps({**identity, "status": row["status"], "steel_index": steel_index,
                          "error": error, "elapsed_seconds": traces[-1]["elapsed_seconds"]}), flush=True)
    api.authenticate(pins)
    completed = sum(r["state"] is not None for r in states)
    complete_ends = sum(e["status"] == "COMPLETE_ISOLATED_END_SOURCE" for e in ends)
    finite = [r for r in states if r["same_state_steel_index"] is not None]
    peak = max(finite, key=lambda r: r["same_state_steel_index"]) if finite else None
    summary = {"status": "COMPLETE_ISOLATED_CURRENT_FORCE_FIELDS_AND_END_SOURCES" if completed == len(states)
               and complete_ends == 2 * len(states) else "ASSESSED_ISOLATED_CURRENT_FORCE_FIELDS_WITH_DECLARED_STOPS",
               "source_join": inputs["source_join"], "accepted_scope": inputs["accepted_scope"],
               "all100_final_current_force_sweep": all_states, "counts": {"attempted_shaft_states": len(states),
               "completed_shaft_states": completed,
               "shaft_numerical_stops": sum(r["status"] == "STOP_NUMERICAL_FIELD_UNAVAILABLE" for r in states),
               "source_geometry_couple_method_limits": sum(r["status"] == "SOURCE_GEOMETRY_COUPLE_METHOD_LIMIT" for r in states),
               "complete_own_end_sources": complete_ends, "own_end_source_limits": len(ends) - complete_ends,
               "field_positions": completed * 80, "bore_samples": completed * 48,
               "steel_reference_exceedances": sum(r["same_state_steel_index"] > 1 for r in finite)},
               "maximum_same_state_steel_index": peak["same_state_steel_index"] if peak else None,
               "peak": {k: peak[k] for k in ("case_id", "gap_scale", "axis_id")} if peak else None,
               "unchanged_seeded_solver_contract": contract,
               "pressure_initializations_are_not_actual_plate_stress_or_support_qualification": True, **FLAGS}
    return api, pins, {"summary.json": summary, "shaft-states.jsonl": states, "shaft-fields.jsonl": fields,
                       "washer-ends.jsonl": ends, "recovery-trace.jsonl": traces}


def build(args):
    output = Path(args.output).absolute()
    require(output.resolve() == output and output.parent == RAW and not output.exists(), "fresh immediate owned output child required")
    old_path, old_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(ROOT), str(HERE.parent)]
    sys.dont_write_bytecode = True
    started = time.monotonic()
    try:
        if args.mode in ("pilot", "all"):
            api, pins, payloads = recover(args.preparation, args.expected_preparation_receipt, args.mode == "all")
        else:
            import numpy as np

            if args.mode == "prepare":
                api, pins, inputs = prepare_sources(args.actions, args.expected_action_receipt, args.force_branch)
                payloads = {"input-plan.json": inputs, "summary.json": {"status": "PREPARED_CURRENT_FORCES_AND_GEOMETRY_ONLY",
                            "source_join": inputs["source_join"], "accepted_scope": inputs["accepted_scope"],
                            "scalar_axis_states": len(inputs["records"]), "scalar_axes": len(inputs["families"]),
                            "geometry_couple_limited_axes": [a for a, g in inputs["families"].items() if g["geometry_limit"]],
                            "pilot_states": len(inputs["pilot_inventory"]), "project_shaft_calls": 0, **FLAGS}}
            else:
                api, p, _direct, pins = context()
                api.bind(pins, HERE / "corner-first-order.py", p.PINS[HERE / "corner-first-order.py"])
                payloads = {"known-answer.json": known_answer(p, np),
                            "summary.json": {"status": "PASS_TINY_ANALYTIC_SHAFT_AND_CONTACT_KNOWN_ANSWERS",
                                             "project_shaft_calls": 0, **FLAGS}}
        api.authenticate(pins)
        output.mkdir(parents=True, exist_ok=False)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        (output / "documentation.md.snapshot").write_bytes(Path(__file__).with_suffix(".md").read_bytes())
        for name, value in payloads.items():
            write(output / name, value)
        write(output / "sources.json", {api.key(path): digest for path, digest in pins.items()})
        outputs = {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()}
        receipt = {"schema": "joint_frame_prescribed_shaft_receipt/v1", "status": payloads["summary.json"]["status"],
                   "source_sha256": {api.key(path): digest for path, digest in pins.items()}, "output_sha256": outputs,
                   "source_authenticated_before_and_after": True, "elapsed_seconds": time.monotonic() - started, **FLAGS}
        write(output / "receipt.json", receipt)
        api.authenticate(pins)
        return {"output": api.key(output), "status": receipt["status"], "receipt_sha256": sha(output / "receipt.json")}
    finally:
        sys.path[:], sys.dont_write_bytecode = old_path, old_bytecode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("prepare", "known", "pilot", "all"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--actions")
    parser.add_argument("--expected-action-receipt")
    parser.add_argument("--force-branch", choices=("original_frame08_method_pilot", "washer_updated_compatible_frame"),
                        default="original_frame08_method_pilot")
    parser.add_argument("--preparation")
    parser.add_argument("--expected-preparation-receipt")
    print(json.dumps(build(parser.parse_args()), sort_keys=True, allow_nan=False))
