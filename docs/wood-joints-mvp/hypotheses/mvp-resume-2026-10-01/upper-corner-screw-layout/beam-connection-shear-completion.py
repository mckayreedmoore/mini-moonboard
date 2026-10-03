"""Finite NDS 3.4.4.1 components on saved ce69/c3a8/62bd six-case actions.

Import is inert. prepare(output) authenticates sources and inventories joins
without importing NumPy or reading numerical arrays. Only the parent calls
build(output). No producer workflow, frame solve, CAD or software test is called.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
RAW = HERE / "rawlocal/beam-connection-shear-completion"
MEMBER_HELPER = HERE / "knee-bridge-members.py"
DEFINITION_HELPER = HERE / "contact-bearing-completion.py"
MEMBERS = HERE / "rawlocal/knee-bridge-members/attempt01"
N03 = HERE / "rawlocal/bolt-detailing-completion/attempt02"
N02 = HERE / "rawlocal/bolt-group-completion/attempt01"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
MAP = HERE / "beam-connection-shear-applicability.md"
PRIMARY = HERE / "rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf"
DOFS = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/model.dof"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SCENARIOS = {"cd1": 1.0, "cd1_25": 1.25}
# Existing source resolutions, not new physical acceptance thresholds.
ZERO_N = 1e-4
TOL_MM = 1e-5
CUT_TOL_MM = 1e-6
FORCE_TOL_N = 1e-7
MOMENT_TOL_NMM = 1e-5
PINS = {
    MAP: "b689b6f1a759ba0b86b6ace600f78e49b8e8c60f8f37bfbf46b6241094b7d9bb",
    MEMBER_HELPER: "bc0704d2c4f7cb6dc472a139b382e514ab69f0a8de02f05a19a3266de6addb0b",
    DEFINITION_HELPER: "4c1240a296f764d2565edf219e2a5aa1b0fae25958840f7cc64a610662bee1ee",
    PRIMARY: "205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644",
    DOFS: "532f732e5b2ed88d96c544b73bcc33168a65942ff6c5155f30c6d4ade9173f1d",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    N03 / "receipt.json": "28c00cefe1d95f86d75b837304a958ff5242690f88017e685a959ba7c1b15a59",
    N03 / "summary.json": "ed4ca499ec9e10ef8550f01071a42fec8797c34cb5ec24d1f95516d5c37ede94",
    N03 / "geometry-bindings.json": "c883691261a365125cedde76add0a3bf0406bd1c3c0b5fbfc1dc4b0aa25fa8ed",
    N03 / "host-states.jsonl": "07f086dff6a9691d06370888e43adf4bcd8c016b40c73c9dd5e614be6948a998",
    N02 / "checks.json": "4db21cc2d7fa76cebc021ef8574331d520f247b78de5acb4270ac90dc80713de",
    N02 / "receipt.json": "81f2e5dfbc0f30355b95c7b276d4ac437b9d8dfd344d7ef16bce2b91d15e7205",
    MEMBERS / "receipt.json": "fa4d5f5568d53c0e4e62a74d31a814738b39a78951a4c27ae6e4c141ef5be794",
    MEMBERS / "checks.json": "0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65",
    MEMBERS / "body-balances.json": "b7a99250f8828ad4dbb220e8bbfa4971de5cbc9331c679925fa7dd9b3a9c97e6",
}
FLAGS = dict.fromkeys((
    "complete_joint_acceptance", "complete_member_acceptance", "physical_release",
    "fabrication_release", "proposal_adopted", "formal_criteria_updated",
    "duration_adoption_complete", "permanent_load_check_included",
    "native_launch", "frame_solve", "CAD_rebuilt", "tests_run", "review_run",
    "geometry_load_stiffness_or_material_changed", "full_joint_NDS_capacity_assigned",
), False)
LIMITS = [
    "NDS 3.4.4.1 rectangular beam shear components only; no complete connection capacity.",
    "Opposing signs, zero direction, oblique force, axial washer direction, free couples and multiple interfaces remain named component limits.",
    "N03 physical-corner replay forces are retained as witnesses; full current member cuts use the original authenticated global point-action inventory.",
    "Eight mapped terminal/recess joins have null NDS capacities, with actual signed section demands retained.",
    "Saved point placement, no-slip support and conditional DF-L No.2 duration/material hypotheses remain unchanged.",
    "No EC5 comparison, cut-hull substitution, floor-friction test, torsional allowance or new perpendicular tensile property.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed source changed: " + str(path))


def source_map(pins):
    return {p.relative_to(ROOT).as_posix(): h for p, h in sorted(pins.items())}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def receipt(pins, directory, result_name, expand_sources=True):
    data = read(directory / "receipt.json")
    require(data["output_sha256"][result_name] == pins[directory / result_name],
            "receipt/result binding differs: " + str(directory))
    if expand_sources:
        for name, digest in data.get("source_sha256", {}).items():
            bind(pins, ROOT / name, digest)
        for name, digest in data.get("classifier_source_sha256", {}).items():
            bind(pins, ROOT / name, digest)
    # N02 is consumed only for identities; its force/resistance dependencies
    # are not substituted for the ce69 demand closure.
    for name, digest in data["output_sha256"].items():
        path = (directory / name).resolve()
        require(path.is_relative_to(directory), "receipt output leaves its packet")
        bind(pins, path, digest)
    return data


def guard(body, axis_ids):
    if body.startswith("lumber_leg_"):
        return ("UPPER_REAR_LEG_TRIMMED_REFERENCE" if axis_ids[0].startswith("lumber_leg_bolt_")
                else "RECESSED_REAR_LEG_FOOT")
    if body.startswith("base_principal_center_") and axis_ids[0].startswith("center_principal_"):
        return "TRUNCATED_PRINCIPAL_FOOT"
    if body.startswith("base_side_") and axis_ids[0].startswith("knee_outer_"):
        return "SIDE_TERMINAL_CORNER_CONTINUOUS_INTERFACES"
    return None


def sources(pins):
    authenticate(pins)
    helper = module(MEMBER_HELPER, "beam_saved_member_contract")
    for path, digest in {**helper.PINS, **helper.CLASSIFIER_PINS}.items():
        bind(pins, path, digest)
    report, comparison, model, rows, records, _materials, frame_ids, _selected = helper.load_sources(pins)
    member_receipt = receipt(pins, MEMBERS, "checks.json")
    detail_receipt = receipt(pins, N03, "summary.json")
    receipt(pins, N02, "checks.json", expand_sources=False)
    refs, detailing, pairs, integration = (read(p) for p in
        (MEMBERS / "checks.json", N03 / "summary.json", N02 / "checks.json", INTEGRATION))
    require(member_receipt["source_unchanged_before_and_after_write"] is True
            and detail_receipt["sources_authenticated_before_and_after"] is True,
            "completed source authentication missing")
    require(tuple(refs["case_ids"]) == tuple(pairs["case_ids"]) == CASES
            and refs["source_response_sha256"] == helper.PINS[helper.RESPONSE]
            and refs["source_comparison_sha256"] == helper.PINS[helper.COMPARISON]
            and refs["source_gravity_assessment_sha256"] == helper.PINS[helper.ASSESSMENT],
            "reference/demand authorities differ")
    require(detailing["census"]["geometry_host_records"] == 216
            and detailing["census"]["host_state_records"] == 1296
            and detailing["census"]["global_physical_axes"] == 104
            and detailing["census"]["internal_physical_axes"] == 4, "N03 census differs")
    require(len(model["body_names"]) == len(integration["geometry"]["effective_members"]) == 50
            and len(integration["existing_bolt_axes"]) == 104
            and len(integration["proposed_internal_bolt_axes"]) == 4, "104/108 body/axis inventory differs")
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "physical rows differ")
    bindings = {(r["body"], r["axis_id"]): r for r in read(N03 / "geometry-bindings.json")}
    require(len(bindings) == 216, "duplicate geometry binding")
    axes = {r["axis_id"]: r for r in integration["existing_bolt_axes"]}
    grouped = {}
    for row in pairs["groups"]:
        if row["case_id"] != CASES[0]:
            continue
        ids = tuple(sorted(row["axis_ids"]))
        require(len(ids) == len(set(ids)) == 2 and set(ids).issubset(axes), "invalid physical pair identity")
        for body in set(row["receivers"]) & frame_ids:
            record = grouped.setdefault((body, ids), {"body": body, "axis_ids": list(ids), "N02_group_ids": []})
            record["N02_group_ids"].append(row["group_id"])
    inventory = []
    for (body, ids), record in sorted(grouped.items()):
        record["join_id"] = body + " :: " + " | ".join(ids)
        record["geometry_guard"] = guard(body, ids)
        record["primary_transverse_index"] = 1 if body == "base_header" else 2
        record["interfaces"] = []
        for identity in ids:
            binding = bindings[body, identity]
            require(binding["effective_STEP"]["path"] == records[body]["current_finished_step"]
                    and binding["effective_STEP"]["sha256"] == records[body]["current_finished_step_sha256"],
                    "receiver geometry source differs: " + body)
            for interface in axes[identity]["interfaces"]:
                if body not in interface["receivers"]:
                    continue
                require(len(interface["receivers"]) == 2, "interface receiver census differs")
                record["interfaces"].append({"axis_id": identity, **interface})
        require(len(record["interfaces"]) == (4 if record["geometry_guard"] ==
                "SIDE_TERMINAL_CORNER_CONTINUOUS_INTERFACES" else 2), "pair interface count differs")
        inventory.append(record)
    require(len(inventory) == 58 and sum(r["geometry_guard"] is None for r in inventory) == 50
            and len({r["body"] for r in inventory if r["geometry_guard"] is None}) == 18
            and {r["body"] for r in inventory} == frame_ids, "frozen 50/8/58 map census differs")
    references = {r["member"]: r for r in refs["members"]}
    balances = {(r["case_id"], r["member"]): r for r in read(MEMBERS / "body-balances.json")}
    require(len(balances) == 252 and frame_ids.issubset(references), "saved member reference/closure missing")
    for body in frame_ids:
        ref = references[body]
        require(ref["kind"] == "frame" and ref["finished_step_sha256"] == records[body]["current_finished_step_sha256"],
                "member reference geometry differs")
        base = ref["references"]["cd1"]["Fv_mpa"]
        require(base == ref["material_strength_binding"]["CF_only_reference_mpa"]["Fv_parallel"]
                and ref["references"]["cd1_25"]["Fv_mpa"] == base * SCENARIOS["cd1_25"],
                "Fv/CD binding differs or duration applied twice")
    authenticate(pins)
    return SimpleNamespace(helper=helper, report=report, comparison=comparison, model=model, rows=rows,
        records=records, frame_ids=frame_ids, inventory=inventory, bindings=bindings,
        references=references, balances=balances, detailing=detailing)


def ray_side(np, ray, direction):
    dot = float(np.asarray(ray["ray_unit_xyz"]) @ direction)
    require(abs(abs(dot) - 1) < 1e-7, "reference ray is not in the chosen beam plane")
    return 1 if dot > 0 else -1


def group_geometry(np, group, states, data, basis):
    index = group["primary_transverse_index"]
    d = float(data.records[group["body"]]["geometry"]["width_mm" if index == 1 else "depth_mm"])
    b = float(data.records[group["body"]]["geometry"]["depth_mm" if index == 1 else "width_mm"])
    require(abs(d - 139.7) < TOL_MM and b > 0, "declared component dimensions differ")
    centers, ends, edges, normals, notes = [], [], [], [], []
    for identity in group["axis_ids"]:
        binding, detail = data.bindings[group["body"], identity], states[identity]["detail"]
        shaft = np.asarray(binding["axis_unit_xyz"])
        require(abs(float(shaft @ basis[0])) < 1e-7
                and abs(abs(float(shaft @ basis[3 - index])) - 1) < 1e-7,
                "fastener shaft does not establish the ordinary component plane")
        center = np.asarray(detail["mid_bearing_xyz_mm"])
        require(center.shape == (3,) and np.isfinite(center).all(), "invalid bore center")
        centers.append(center.tolist())
        rays = detail["reference_rays"]
        ends.append({name: rays[name]["distance_mm"] for name in ("grain_plus", "grain_minus")})
        own_edges, own_normals = {}, {}
        for name in ("cross_plus", "cross_minus"):
            ray = rays[name]
            side = ray_side(np, ray, basis[index])
            distance = float(ray["distance_mm"])
            require(math.isfinite(distance) and distance >= 0, "invalid exterior edge reference")
            own_edges[side] = distance
            own_normals[side] = ray.get("exterior_normals_xyz", [])
            if ray.get("reference_basis") != "EXACT_CONSTANT_PRISM_REFERENCE":
                notes.append("TRIMMED_MID_BEARING_REFERENCE_NOT_CONTINUOUS_DEPTH")
            if ray.get("first_exterior_exit") is None:
                notes.append("CORNER_OR_AFFINE_REFERENCE_REQUIRES_PROFILE_GUARD")
        require(set(own_edges) == {-1, 1}, "two physical edges not identified")
        edges.append(own_edges)
        normals.append(own_normals)
    if group["geometry_guard"] is None:
        require(all(abs(edge[-1] + edge[1] - d) < TOL_MM for edge in edges),
                "mapped candidate has a truncated depth")
        require(not notes, "mapped candidate lost its constant-prism witness")
        for normal_set in normals:
            for side in (-1, 1):
                require(any(abs(float(np.asarray(n) @ basis[index]) - side) < 1e-7
                            for n in normal_set[side]), "edge reference is not a parallel depth face")
    nearest = min(float(distance) for pair in ends for distance in pair.values())
    require(math.isfinite(nearest) and nearest >= 0, "invalid connection end reference")
    branch = "near" if nearest < 5 * d else "far"
    # The center nearest the unloaded edge gives the largest loaded-edge depth.
    depths = {side: d - min(edge[-side] for edge in edges) for side in (-1, 1)}
    guarded = group["geometry_guard"] is not None
    return {"b_mm": None if guarded else b, "d_mm": None if guarded else d,
        "source_rectangle_reference_b_d_mm": [b, d], "depth_axis_global_xyz": basis[index].tolist(),
        "breadth_axis_global_xyz": basis[3 - index].tolist(), "bore_centers_xyz_mm": centers,
        "center_to_physical_edges_mm": [{str(k): v for k, v in edge.items()} for edge in edges],
        "grain_end_distances_mm": ends, "closest_end_mm": nearest, "five_d_mm": 5 * d,
        "branch": branch, "de_by_loaded_edge_mm": {str(k): v for k, v in depths.items()},
        "reference_notes": sorted(set(notes)), "geometry_guard": group["geometry_guard"],
        "guarded_profile_planes": data.records[group["body"]]["profile_planes"] if guarded else None,
        "guarded_recess_source": data.records[group["body"]]["recess_source"] if guarded else None,
        "NDS_rectangle_component_established": not guarded}


def transfer(np, group, states, actions, data, basis, accounting):
    by_row = {a["row"]: a for a in actions if a["row"] >= 0}
    index, body = group["primary_transverse_index"], group["body"]
    planes, locations, limits = [], [], []
    force_rows = set()
    for interface in group["interfaces"]:
        identity = interface["axis_id"]
        candidates = [r for r in states[identity]["global_plane_actions"]
                      if r["plane_id"] == interface["plane_id"]]
        require(len(candidates) == 1, "N03 interface/axis join not unique")
        saved = candidates[0]
        require(saved["component_rows"] == interface["component_rows"]
                and saved["partner"] in interface["receivers"] and saved["partner"] != body,
                "N03 global plane ownership differs")
        selected = [by_row[row] for row in interface["component_rows"]]
        for action in selected:
            require(action["other_body"] == saved["partner"]
                    and action["source_id"] == saved["plane_id"]
                    and np.max(abs(np.asarray(action["point_mm"]) - saved["point_xyz_mm"])) < FORCE_TOL_N,
                    "saved interface point/row identity differs")
            require(action["row"] not in force_rows, "duplicated group force row")
            force_rows.add(action["row"])
        force = sum((np.asarray(a["force_n"]) for a in selected), np.zeros(3))
        require(np.max(abs(force - saved["force_xyz_n"])) < FORCE_TOL_N, "N03/global point force differs")
        components = basis @ force
        locations.extend(a["station_mm"] for a in selected)
        planes.append({"axis_id": identity, "plane_id": saved["plane_id"], "partner": saved["partner"],
            "component_rows": interface["component_rows"], "point_xyz_mm": saved["point_xyz_mm"],
            "force_xyz_n": force.tolist(), "force_grain_u_v_n": components.tolist()})
    signs = {1 if p["force_grain_u_v_n"][index] > 0 else -1 for p in planes
             if abs(p["force_grain_u_v_n"][index]) > ZERO_N}
    if len(signs) == 2:
        limits.append("OPPOSING_DEPTH_ACTIONS_NO_SINGLE_UNLOADED_EDGE")
    elif not signs:
        limits.append("ZERO_DEPTH_TRANSFER_UNLOADED_EDGE_UNDEFINED")
    if any(abs(p["force_grain_u_v_n"][0]) > ZERO_N for p in planes):
        limits.append("OBLIQUE_LOAD_TRANSVERSE_COMPONENT_ONLY")
    if any(abs(p["force_grain_u_v_n"][3 - index]) > ZERO_N for p in planes):
        limits.append("OUT_OF_PLANE_TRANSFER_NOT_COVERED")
    if len(group["interfaces"]) > 2:
        limits.append("MULTIPLE_INTERFACES_SHARED_MIDDLE_RECEIVER")
    replay_witnesses = []
    for identity in group["axis_ids"]:
        state = states[identity]
        global_force = sum((np.asarray(p["force_xyz_n"]) for p in planes if p["axis_id"] == identity), np.zeros(3))
        local = np.asarray(state["detail"]["direction"]["force_xyz_n"])
        delta = local - global_force
        replay_witnesses.append({"axis_id": identity, "N03_direction_basis": state["direction_basis"],
            "N03_local_force_xyz_n": local.tolist(), "current_global_bore_force_xyz_n": global_force.tolist(),
            "local_minus_global_force_xyz_n": delta.tolist()})
        if np.max(abs(delta)) > FORCE_TOL_N:
            require(state["direction_basis"] == "fresh_physical_corner_bore_resultant",
                    "unexplained N03/global force discrepancy")
            limits.append("PHYSICAL_CORNER_REPLAY_ALLOCATION_NOT_GLOBAL_CUT_ALLOCATION")
        station = float(basis[0] @ (np.asarray(state["detail"]["mid_bearing_xyz_mm"])
                                  - data.records[body]["geometry"]["start"]))
        own_stations = [a["station_mm"] for a in actions if a["row"] in
                        {r for p in planes if p["axis_id"] == identity for r in p["component_rows"]}]
        if any(abs(s - station) > TOL_MM for s in own_stations):
            limits.append("BORE_AND_GLOBAL_ACTION_GRAIN_STATIONS_DIFFER")
    partners = {p["partner"] for p in planes}
    associated = [a for a in actions if a["other_body"] in partners]
    free_couples = [a for a in associated if max(map(abs, a["free_moment_nmm"])) > MOMENT_TOL_NMM]
    if free_couples:
        limits.append("ASSOCIATED_CONNECTION_FREE_COUPLES_NOT_QUALIFIED")
    axial = [a for a in associated if a["role"] == "physical_bolt_outer_seat_tension"
             or "axial" in a["role"] or "tie" in a["role"]]
    if any(max(map(abs, a["force_n"])) > ZERO_N for a in axial):
        limits.append("ASSOCIATED_AXIAL_WASHER_OR_TIE_ACTION_SEPARATE")
    contact = [a for a in associated if "contact" in a["role"]]
    datum = np.asarray(data.records[body]["geometry"]["start"])
    wrench = accounting.wrench([by_row[r] for r in sorted(force_rows)], datum)
    return {"global_lateral_planes": planes, "N03_local_direction_witnesses": replay_witnesses,
        "loaded_edge_signs": sorted(signs), "unloaded_edge_established": len(signs) == 1,
        "group_force_row_ids": sorted(force_rows), "group_station_interval_mm": [min(locations), max(locations)],
        "bore_wrench_about_member_start_n_nmm": wrench.tolist(),
        "associated_connection_free_couples": free_couples,
        "associated_axial_actions": axial, "associated_contact_row_ids": [a["row"] for a in contact],
        "load_limits": sorted(set(limits))}


def cut_demands(np, group, loading, record, negative):
    stations = np.asarray(record["stations_mm"], dtype=float)
    lo, hi = loading["group_station_interval_mm"]
    points = [p["point_xyz_mm"] for p in loading["global_lateral_planes"]]
    grain = np.asarray(record["geometry"]["axis"])
    for point in points:
        station = float(grain @ (np.asarray(point) - record["geometry"]["start"]))
        require(float(np.min(abs(stations - station))) <= CUT_TOL_MM,
                "global group station absent from saved cuts")
    selected = [2 * i + side for i, station in enumerate(stations)
                if lo - CUT_TOL_MM <= station <= hi + CUT_TOL_MM for side in (0, 1)]
    require(selected, "no saved cuts bracket the actual group")
    witnesses = {}
    for index, name in ((1, "u"), (2, "v")):
        chosen = max(selected, key=lambda i: abs(float(negative[i, index])))
        witnesses[name] = {"V_abs_n": abs(float(negative[chosen, index])),
            "V_signed_n": float(negative[chosen, index]), "cut_array_index": chosen,
            "station_mm": float(stations[chosen // 2]), "trace": "before" if chosen % 2 == 0 else "after",
            "signed_N_Vu_Vv_T_Mu_Mv_n_nmm": negative[chosen].tolist(),
            "section_status": record["rectangle_at_station"][chosen // 2]["status"]}
    return {"scope": "all saved before/after traces across the complete global group station interval",
        "cut_trace_indices": selected, "cut_trace_count": len(selected), "u": witnesses["u"], "v": witnesses["v"]}


def comparisons(group, geometry, loading, demand, reference):
    index = group["primary_transverse_index"]
    component = "u" if index == 1 else "v"
    other = "v" if index == 1 else "u"
    limits = list(loading["load_limits"])
    if geometry["geometry_guard"]:
        limits.append(geometry["geometry_guard"])
    role = ("MATCHING_PLANAR_NDS_TRANSVERSE_COMPONENT" if not limits
            else "EXPLICIT_TRANSVERSE_COMPONENT_DIAGNOSTIC")
    actual_sides = loading["loaded_edge_signs"]
    # A zero or opposing transfer has no single physical unloaded edge. Both
    # hypothetical edge calculations stay visible and do not receive a pass.
    sides = actual_sides if len(actual_sides) == 1 else [-1, 1]
    result = []
    for side in sides:
        de = geometry["de_by_loaded_edge_mm"][str(side)]
        b, d, V = geometry["b_mm"], geometry["d_mm"], demand[component]["V_abs_n"]
        established = geometry["NDS_rectangle_component_established"] and 0 < de <= d + TOL_MM
        scenarios = {}
        for name, cd in SCENARIOS.items():
            fv = reference["references"][name]["Fv_mpa"]
            require(fv > 0 and math.isfinite(fv), "invalid saved adjusted Fv reference")
            capacity = (2 / 3) * fv * b * de * ((de / d) ** 2 if geometry["branch"] == "near" else 1) if established else None
            ratio = V / capacity if capacity is not None else None
            scenarios[name] = {"CD_already_in_saved_Fv": cd, "Fv_mpa": fv,
                "Vr_prime_n": capacity, "V_abs_n": V, "index": ratio,
                "comparison_exceeds_one": ratio > 1 if ratio is not None else None,
                "matching_component_pass": ratio <= 1 if ratio is not None and not limits else None,
                "complete_joint_pass": None}
        result.append({"component": component, "load_plane": "grain-" + component,
            "loaded_physical_depth_edge_sign": side, "unloaded_physical_depth_edge_sign": -side,
            "unloaded_edge_is_actual_unique_transfer": len(actual_sides) == 1,
            "de_mm": de if established else None, "geometry_depth_reference_mm": de,
            "b_mm": b, "d_mm": d, "branch": geometry["branch"],
            "equation": "3.4-6" if geometry["branch"] == "near" else "3.4-7",
            "role": role, "limits": sorted(set(limits)), "scenarios": scenarios,
            "demand_witness": demand[component], "complete_joint_capacity_n": None})
    return {"primary_component_comparisons": result,
        "other_component": {"component": other, "demand_witness": demand[other],
            "capacity_n": None, "limit": "SHAFT_AXIAL_OR_WASHER_DIRECTION_NOT_THIS_LATERAL_BEAM_ALLOWANCE"},
        "full_joint_qualified": False}


def assess(output, data, pins):
    import numpy as np

    definitions = module(DEFINITION_HELPER, "beam_pure_definition_loader")
    member = definitions.functions(BASE / "member_screen.py", ("basis", "cut_vectors"), {"np": np})
    bottom = definitions.functions(BASE / "bottom_corner_checks.py", ("saved_actions",), {})
    accounting = definitions.functions(BASE / "top_corner_actions.py", ("wrench",), {"np": np})
    method = SimpleNamespace(member=member, bottom=bottom, accounting=accounting)
    require(member is not None and bottom is not None, "pure helper import incomplete")
    require(DOFS.resolve() in pins, "physical DOF path not authenticated")
    labels = [tuple(map(int, line.split("."))) for line in DOFS.read_text().splitlines() if line.strip()]
    require(len(labels) == len(set(labels)) and all(dof in (1, 2, 3) for _, dof in labels), "invalid physical DOF labels")
    host_states = {}
    for line in (N03 / "host-states.jsonl").open():
        row = json.loads(line)
        require(row["gap_scale"] == 1.0 and row["case_id"] in CASES, "N03 nominal state scope differs")
        key = row["case_id"], row["body"], row["axis_id"]
        require(key not in host_states, "duplicate N03 case/axis/host")
        host_states[key] = row
    require(len(host_states) == 1296, "N03 host-state census differs")
    groups_by_body = {body: [g for g in data.inventory if g["body"] == body] for body in sorted(data.frame_ids)}
    report_cases = {(c["case_id"], r["member"]): r for c in data.report["cases"] for r in c["members"]}
    counters, limits, peaks, closures, branch_counts = Counter(), Counter(), {}, [], Counter()
    body_case_count = 0
    with np.load(data.helper.ARRAYS, allow_pickle=False) as arrays, \
            np.load(data.helper.RESPONSE, allow_pickle=False) as responses, \
            np.load(data.helper.GRAVITY / "operators.npz", allow_pickle=False) as operators, \
            (output / "group-case-states.jsonl").open("w") as stream:
        D, F, W = (operators[name] for name in ("D", "F", "W"))
        require(D.shape == (1888, 300) and F.shape == (len(labels), 12) and W.shape == (300, 12),
                "physical operator dimensions differ")
        for body in sorted(data.frame_ids):
            record, basis = data.records[body], member.basis(data.records[body]["geometry"])
            require(basis.shape == (3, 3) and np.max(abs(basis @ basis.T - np.eye(3))) < 1e-8,
                    "receiver grain/section frame differs")
            for case_index, case in enumerate(CASES):
                raw = responses[case + "_gap_raw_force_n"]
                require(raw.shape == (1888,) and np.isfinite(raw).all(), "invalid nominal raw force vector")
                negative, closure = data.helper.validate_actions(np, method, body, case, case_index, record,
                    arrays, data.model, data.rows, D, F, W, labels, raw, report_cases[case, body])
                preserved = data.balances[case, body]
                for field in ("whole_body_residual_n_nmm", "fresh_F_W_residual_n_nmm"):
                    data.helper.close(np, np.asarray(closure[field]) - preserved[field], FORCE_TOL_N,
                                      MOMENT_TOL_NMM, "preserved/current body closure")
                closures.append(closure)
                actions = bottom.saved_actions(body, case, record, arrays)
                require(len({a["row"] for a in actions if a["row"] >= 0}) ==
                        len([a for a in actions if a["row"] >= 0]), "duplicate member connector row")
                for group in groups_by_body[body]:
                    states = {identity: host_states[case, body, identity] for identity in group["axis_ids"]}
                    geometry = group_geometry(np, group, states, data, basis)
                    loading = transfer(np, group, states, actions, data, basis, accounting)
                    demand = cut_demands(np, group, loading, record, negative)
                    result = comparisons(group, geometry, loading, demand, data.references[body])
                    state = {"join_id": group["join_id"], "body": body, "axis_ids": group["axis_ids"],
                        "N02_identity_groups": group["N02_group_ids"], "case_id": case, "gap_scale": 1.0,
                        "geometry": geometry, "loading": loading, "section_demands": demand, **result,
                        "material_binding": data.references[body]["material_strength_binding"], **FLAGS}
                    stream.write(json.dumps(state, separators=(",", ":"), allow_nan=False) + "\n")
                    stream.flush()
                    counters["group_case_records"] += 1
                    counters["guarded_group_cases" if group["geometry_guard"] else "candidate_group_cases"] += 1
                    if case == CASES[0] and group["geometry_guard"] is None:
                        branch_counts[geometry["branch"]] += 1
                    for entry in result["primary_component_comparisons"]:
                        limits.update(entry["limits"])
                        counters[entry["role"]] += 1
                        for name, check in entry["scenarios"].items():
                            counters[name + "/finite_indices"] += check["index"] is not None
                            counters[name + "/exceedances"] += check["comparison_exceeds_one"] is True
                            counters[name + "/matching_passes"] += check["matching_component_pass"] is True
                            counters[name + "/matching_exceedances"] += (check["matching_component_pass"] is False)
                            key = name + "/" + entry["role"]
                            if check["index"] is not None and (key not in peaks or check["index"] > peaks[key]["index"]):
                                peaks[key] = {"index": check["index"], "join_id": group["join_id"], "case_id": case,
                                    "loaded_physical_depth_edge_sign": entry["loaded_physical_depth_edge_sign"],
                                    "Vr_prime_n": check["Vr_prime_n"], "de_mm": entry["de_mm"],
                                    "branch": entry["branch"], "demand_witness": entry["demand_witness"],
                                    "limits": entry["limits"]}
                body_case_count += 1
            print(json.dumps({"completed_frame_bodies": body_case_count // 6,
                              "completed_group_cases": counters["group_case_records"]}), flush=True)
    require(len(closures) == 120 and counters["group_case_records"] == 348
            and counters["candidate_group_cases"] == 300 and counters["guarded_group_cases"] == 48,
            "58 × 6 finite assessment census differs")
    require(dict(branch_counts) == {"near": 36, "far": 14}, "frozen near/far candidate map differs")
    write(output / "body-case-closure.json", closures)
    return {"status": "FINITE_NDS_REDUCED_DEPTH_COMPONENT_COMPARISONS_WITH_LIMITS",
        "counts": dict(counters), "candidate_branch_counts": dict(branch_counts),
        "named_limit_counts": dict(limits), "same_state_peaks": peaks,
        "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
        "source_case_force_keys": [case + "_gap_raw_force_n" for case in CASES],
        "body_case_closure_count": len(closures), "original_actions_and_full_wrenches_preserved": True}


def execute(output, numerical):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and output.name not in ("", ".", ".."), "output must be a fresh immediate child of owned raw directory")
    require(not output.exists(), "preserve existing attempt: " + str(output))
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins = dict(PINS)
    bind(pins, Path(__file__), sha(__file__))
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    result = {"schema": "beam-connection-shear-completion/v1", "status": "STARTED",
        "case_ids": list(CASES), "gap_scale": 1.0, "numerical_arithmetic_run": numerical,
        "API": {"prepare": "prepare(output): standard-library provenance and identity inventory only",
                "build": "build(output): parent-owned bounded six-case finite arithmetic",
                "output": "fresh immediate child of rawlocal/beam-connection-shear-completion"},
        "primary": {"source": PRIMARY.relative_to(ROOT).as_posix(), "sha256": PINS[PRIMARY],
                    "clause": "NDS 2024 3.4.4.1", "printed_page": 21, "PDF_page": 7,
                    "equations": ["3.4-6", "3.4-7"], "units": "mm, MPa, N"},
        "limits": LIMITS, **FLAGS}
    terminal = None
    try:
        data = sources(pins)
        census = {"transport_bodies": 50, "timber_bodies": 44, "frame_receivers": 20,
            "global_axes": 104, "internal_proposal_axes": 4, "proposal_axes": 108,
            "receiver_pair_joins": 58, "rectangular_geometry_candidates": 50, "guarded_joins": 8,
            "nominal_cases": 6, "expected_group_case_records": 348, "expected_body_case_closures": 120}
        write(output / "inventory.json", {"census": census, "joins": data.inventory})
        result.update(census=census, modeled_mass_kg=data.model["modeled_mass_kg"],
            same_state_dead_load_factor=data.model["dead_load_factor"],
            force_scope=data.report["source_force_state_scope"],
            source_response_sha256=data.helper.PINS[data.helper.RESPONSE],
            source_comparison_sha256=data.helper.PINS[data.helper.COMPARISON],
            source_gravity_assessment_sha256=data.helper.PINS[data.helper.ASSESSMENT],
            Fv_duration_application="Read each saved CD-specific Fv once; no additional CD multiplier.",
            source_resolutions={"zero_direction_n": ZERO_N, "geometry_mm": TOL_MM,
                                "cut_partition_mm": CUT_TOL_MM, "force_n": FORCE_TOL_N,
                                "moment_n_mm": MOMENT_TOL_NMM})
        if numerical:
            result.update(assess(output, data, pins))
        else:
            result.update(status="PREPARED_NOT_NUMERICALLY_RUN",
                          readiness="READY_FOR_PARENT_BUILD_WITH_NAMED_COMPONENT_LIMITS",
                          runtime={"python": sys.version.split()[0], "numerical_imports": False})
        authenticate(pins)
        result["sources_authenticated_before_and_after"] = True
    except Exception as exc:  # noqa: BLE001 -- Preserve the failed parent attempt, including partial states.
        terminal = f"{type(exc).__name__}: {exc}"
        result.update(status="STOP", terminal_exception=terminal)
    finally:
        sys.dont_write_bytecode = previous_bytecode
    result.update(source_count=len(pins), source_sha256=source_map(pins), producer_sha256=sha(__file__))
    write(output / "report.json", result)
    write(output / "receipt.json", {"schema": "beam-connection-shear-completion-receipt/v1",
        "status": result["status"], "terminal_exception": terminal,
        "source_count": len(pins), "source_sha256": source_map(pins), "producer_sha256": sha(__file__),
        "sources_authenticated_before_and_after": result.get("sources_authenticated_before_and_after", False),
        "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file() and p.name != "receipt.json"},
        "numerical_arithmetic_run": numerical, **FLAGS})
    require(terminal is None, terminal or "finite arithmetic failed")
    return result


def prepare(output):
    """Prepare provenance and pair inventory; no numerical arrays or NumPy."""
    return execute(output, numerical=False)


def build(output):
    """Parent-only finite reduced-depth arithmetic; no engineering solver."""
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": result["status"], "source_count": result["source_count"],
                      "receipt_sha256": sha(args.output / "receipt.json")}))
