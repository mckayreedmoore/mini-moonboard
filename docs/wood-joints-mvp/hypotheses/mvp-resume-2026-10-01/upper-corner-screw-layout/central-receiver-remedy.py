"""Recover central receiver component demands from authenticated saved fields.

This reader reuses unchanged physical group geometry and finite cut stations.
It performs no frame/native solve and does not infer whole-joint resistance.
"""
from __future__ import annotations

import argparse
import copy
import gzip
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BODIES = ("base_header", "base_post_center_left", "base_post_center_right",
          "center_post_cleat_left", "center_post_cleat_right")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def build(source, loads, output):
    helper = __import__("importlib.util", fromlist=["util"])
    spec = helper.spec_from_file_location("central_current", HERE / "current-method-corrections.py")
    shared = helper.module_from_spec(spec)
    spec.loader.exec_module(shared)
    consumer = shared.module(HERE / "member-connection-method-correction.py", "central_components")
    exporter = shared.module(HERE / "joint-frame-action-reconciliation.py", "central_actions")
    reader = shared.module(HERE / "hardware-clearance-remedy.py", "central_frame_reader")
    source, loads = Path(source).resolve(), Path(loads).resolve()
    _follow, mechanics, frame, pins, _orientation = reader.load_frame(shared)
    recovery, _context, load_binding = reader.apply_case_loads(shared, mechanics, frame, loads, pins)
    receipt = read(source / "receipt.json")
    for name, digest in receipt["output_sha256"].items():
        path = (source / name).resolve()
        require(path.is_relative_to(source) and shared.sha(path) == digest,
                "Saved response output binding changed: " + name)
        pins[path] = digest
    comparison = read(source / "comparison.json")
    require(comparison["case_load_comparison"]["receipt_sha256"] == load_binding["receipt_sha256"],
            "Saved response has another load comparison")
    require(len(comparison["states"]) == 12 and all(
        s["solver"]["status"] == "Solved" and s["audit"]["all_passed"] for s in comparison["states"]),
        "Twelve actually solved/audited source states required")
    pins[source / "receipt.json"] = shared.sha(source / "receipt.json")
    mapping_path = HERE / "rawlocal/joint-frame-action-reconciliation/profile-attempt01/source-row-map.json"
    request_path = mechanics.PREPARATION / "wood-port-request.json"
    labels_path = mechanics.PREPARATION / "port-labels.json"
    local_paths = (Path(__file__), HERE / "current-method-corrections.py",
                   HERE / "member-connection-method-correction.py", HERE / "joint-frame-action-reconciliation.py",
                   HERE / "hardware-clearance-remedy.py", exporter.MODEL, exporter.DOFS,
                   exporter.BASELINE / "geometry.json", exporter.OPERATORS / "model.json",
                   exporter.OPERATORS / "operators.npz", exporter.OPERATORS / "row-identities.json",
                   mapping_path, request_path, labels_path, consumer.OLD, consumer.CUTS,
                   consumer.ACTIONS, consumer.GEOMETRY, consumer.CHAPTER,
                   exporter.RESUME / "member_screen.py", exporter.RESUME / "top_corner_actions.py")
    for path in local_paths:
        pins[path] = shared.sha(path)
    loader = shared.module(HERE / "panel-reference-completion.py", "central_pure_definitions")
    namespace = {"np": np, "require": require, "TOL": 1e-5}
    actions_api = loader.definitions(exporter.RESUME / "top_corner_actions.py", ("wrench", "physical_actions"), namespace)
    sections = loader.definitions(exporter.RESUME / "member_screen.py", ("basis", "cut_vectors"), namespace)
    revised, model = read(exporter.OPERATORS / "model.json"), read(exporter.MODEL)
    model = copy.deepcopy(model)
    model["nodes"] = revised["physical_node_coordinates_mm"]
    geometry = read(exporter.BASELINE / "geometry.json")["members"]
    for body in BODIES:
        model["body_geometry"][body]["geometry_record"] = geometry[body]["geometry"]
    names, rows = revised["body_names"], read(exporter.OPERATORS / "row-identities.json")
    mapping, request = read(mapping_path), read(request_path)
    labels = read(labels_path)["new_ports"]
    require(len(mapping["kept_map"]) == 1592 and len(request["new_wood_port_terms"]) == 1600,
            "Current coupled row inventory differs")
    with np.load(exporter.OPERATORS / "operators.npz", allow_pickle=False) as data:
        raw_D = data["D"].copy()
    dofs = [tuple(map(int, line.split("."))) for line in exporter.DOFS.read_text().splitlines() if line.strip()]
    require(len(dofs) == recovery["F"].shape[0], "Physical load DOF labels differ")
    templates = {}
    formula_error = 0.
    for item in consumer.read_lines(consumer.OLD):
        if item["body"] not in BODIES:
            continue
        if item["join_id"] in templates:
            require(consumer.same_geometry(item["geometry"], templates[item["join_id"]]["geometry"]),
                    "Source group geometry varies across cases")
        templates[item["join_id"]] = item
        for component in item["primary_component_comparisons"]:
            for scenario in component["scenarios"].values():
                if scenario["Vr_prime_n"] is not None:
                    calculated = consumer.capacity(scenario["Fv_mpa"], component["b_mm"], component["d_mm"],
                                                   component["de_mm"], component["branch"])
                    formula_error = max(formula_error, abs(calculated - scenario["Vr_prime_n"]) / calculated)
    require(len(templates) == 8 and formula_error < 1e-12, "Source central group/formula reproduction failed")
    finite = {}
    for item in consumer.read_lines(consumer.CUTS):
        if item["body"] in BODIES and "normal" in item:
            # Only geometry, finite stations and fixed strength-reference inputs
            # are reused. Saved old demands never enter the fresh comparison.
            finite.setdefault((item["body"], item["state_tag"]), []).append({
                k: item[k] for k in ("station_mm", "limit", "duration_CD", "references_mpa", "full_signed_wrench_n_nmm")})
    old_actions = {(r["body"], r["state_tag"]): r for r in consumer.read_lines(consumer.ACTIONS)
                   if r["body"] in BODIES}
    old_cut_error = 0.
    for key, cuts in finite.items():
        old = old_actions[key]
        stations = np.unique([r["station_mm"] for r in cuts])
        negative, _, positions, before = sections.cut_vectors(old["actions"], geometry[key[0]]["geometry"], stations)
        basis = sections.basis(geometry[key[0]]["geometry"])
        values = np.column_stack((negative[:, :3] @ basis.T, negative[:, 3:] @ basis.T))
        lookup = {(float(x), "before" if b else "after"): v for x, b, v in zip(positions, before, values, strict=True)}
        for cut in cuts:
            old_cut_error = max(old_cut_error, float(np.max(abs(
                lookup[cut["station_mm"], cut["limit"]] - cut["full_signed_wrench_n_nmm"]))))
    require(old_cut_error < 1e-5, "Known-answer signed physical cut reconstruction failed")
    output = shared.output_directory(output)
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    fields, balances = [], []
    with np.load(source / "response.npz", allow_pickle=False) as saved, gzip.open(output / "body-actions.jsonl.gz", "wt") as stream:
        for state_index, state in enumerate(comparison["states"]):
            tag, case = state["state_tag"], state["case_id"]
            force = saved[tag + "_force"]
            require(force.shape == (3192,) and np.isfinite(force).all(), "Saved force shape/values differ")
            raw = np.zeros(len(rows))
            available = np.zeros(len(rows), dtype=bool)
            for item in mapping["kept_map"]:
                raw[item["raw_rows"]] = np.asarray(item["weights"]) * force[item["kept_position"]]
                available[item["raw_rows"]] = True
            column = 0 if case == "dead-only" else 2 * exporter.CASES.index(case)
            maps = []
            for c in (column, column + 1):
                mapped = {}
                for (node, dof), value in zip(dofs, recovery["F"][:, c], strict=True):
                    if value:
                        mapped.setdefault(str(node), [0., 0., 0.])[dof - 1] = float(value)
                maps.append(mapped)
            case_map = {"gravity_nodal_map": maps[0], "climber_nodal_map": {} if case == "dead-only" else maps[1],
                        "dead_load_factor": frame["dead_load_factor"]}
            body_load = frame["W"] @ mechanics.load_coefficients(case, frame["dead_load_factor"])
            for body in BODIES:
                actions, center, chart = actions_api.physical_actions(body, case_map, raw, model, rows, raw_D, names, {})
                for action in actions:
                    action["source_force_available"] = action["row"] is None or bool(available[action["row"]])
                for port, terms in enumerate(request["new_wood_port_terms"]):
                    for index, term in enumerate(terms):
                        if term["member_id"] == body:
                            point = np.asarray(term["point_mm"])
                            station = float(np.asarray(chart["axis"]) @ (point - chart["start"]))
                            actions.append({"row": None, "coupled_port_row": 1592 + port,
                                "source_id": f"coupled/{labels[port]['axis_id']}/{port}/{index}",
                                "role": labels[port]["role"], "other_body": None,
                                "point_mm": point.tolist(), "station_mm": station,
                                "footprint_mm": [station, station], "source_force_available": True,
                                "force_n": (-force[1592 + port] * np.asarray(term["direction_global_xyz"])).tolist(),
                                "free_moment_nmm": [0., 0., 0.]})
                b = names.index(body)
                loads_only = [a for a in actions if a["role"] == "discrete_body_load"]
                connectors = [a for a in actions if a["role"] != "discrete_body_load"]
                closure = actions_api.wrench(actions, center)
                load_error = float(np.max(abs(actions_api.wrench(loads_only, center) -
                    body_load[6*b:6*b+6] * [1, 1, 1, 1000, 1000, 1000])))
                connector_error = float(np.max(abs(actions_api.wrench(connectors, center) +
                    (frame["Dwood"][:, 6*b:6*b+6].T @ force) * [1, 1, 1, 1000, 1000, 1000])))
                require(np.max(abs(closure[:3])) < .1 and np.max(abs(closure[3:])) < 2.
                        and load_error < 1e-6 and connector_error < 1e-5,
                        "Fresh physical body-action recovery failed: " + tag + "/" + body)
                balances.append({"state_tag": tag, "body": body, "closure_n_nmm": closure.tolist(),
                                 "load_wrench_error_n_nmm": load_error, "connector_wrench_error_n_nmm": connector_error})
                stream.write(json.dumps({"state_tag": tag, "body": body, "center_mm": center.tolist(),
                    "source_state_record": {"path": str(source / "comparison.json"), "sha256": shared.sha(source / "comparison.json"),
                        "pointer": "/states/" + str(state_index)}, "actions": actions}, allow_nan=False) + "\n")
                cuts = finite[body, tag]
                stations = np.unique([r["station_mm"] for r in cuts])
                negative, _, positions, before = sections.cut_vectors(actions, chart, stations)
                basis = sections.basis(chart)
                values = np.column_stack((negative[:, :3] @ basis.T, negative[:, 3:] @ basis.T))
                lookup = {(float(x), "before" if b else "after"): v for x, b, v in zip(positions, before, values, strict=True)}
                by_row = {a["row"]: a for a in actions if isinstance(a["row"], int)}
                for template in templates.values():
                    if template["body"] != body:
                        continue
                    g = template["geometry"]
                    component = template["primary_component_comparisons"][0]["component"]
                    index = 1 if component == "u" else 2
                    depth_axis = np.asarray(g["depth_axis_global_xyz"])
                    require(np.max(abs(depth_axis - basis[index])) < 1e-7, "Group depth axis changed")
                    row_ids = template["loading"]["group_force_row_ids"]
                    require(all(r in by_row and by_row[r]["source_force_available"] for r in row_ids),
                            "Central group has unavailable source rows")
                    plane_forces = [float(np.sum([by_row[r]["force_n"] for r in p["component_rows"]], axis=0) @ depth_axis)
                                    for p in template["loading"]["global_lateral_planes"]]
                    signs = sorted({1 if v > 0 else -1 for v in plane_forces if abs(v) > 1e-8})
                    lo, hi = min(by_row[r]["station_mm"] for r in row_ids), max(by_row[r]["station_mm"] for r in row_ids)
                    selected = [r for r in cuts if lo - 1e-5 <= r["station_mm"] <= hi + 1e-5]
                    require(selected and g["NDS_rectangle_component_established"], "Finite rectangular group cuts required")
                    witness = max(selected, key=lambda r: abs(lookup[r["station_mm"], r["limit"]][index]))
                    demand = abs(float(lookup[witness["station_mm"], witness["limit"]][index]))
                    for sign in signs if len(signs) == 1 else (-1, 1):
                        effective = g["de_by_loaded_edge_mm"][str(sign)]
                        reference = consumer.capacity(witness["references_mpa"]["Fv_parallel"], g["b_mm"], g["d_mm"], effective, g["branch"])
                        fields.append({"join_id": template["join_id"], "body": body, "state_tag": tag,
                            "index": demand / reference, "demand_n": demand, "reference_n": reference,
                            "component": component, "loaded_edge_sign": sign,
                            "unique_loaded_edge_established": len(signs) == 1, "de_mm": effective,
                            "b_mm": g["b_mm"], "d_mm": g["d_mm"], "branch": g["branch"],
                            "Fv_mpa": witness["references_mpa"]["Fv_parallel"], "duration_CD": witness["duration_CD"],
                            "finite_cut_count": len(selected), "same_state_plane_depth_forces_n": plane_forces,
                            "cut_witness": {"station_mm": witness["station_mm"], "limit": witness["limit"],
                                "signed_N_Vu_Vv_T_Mu_Mv": lookup[witness["station_mm"], witness["limit"]].tolist()},
                            "complete_joint_acceptance": False})
    require(all(shared.sha(p) == h for p, h in pins.items()), "Source changed during recovery")
    unique = [r for r in fields if r["unique_loaded_edge_established"]]
    result = {"schema": "fresh_central_receiver_component_comparison/v1", "states": 12, "bodies": list(BODIES),
        "physical_groups": len(templates), "finite_comparisons": len(fields), "unique_loaded_edge_comparisons": len(unique),
        "unique_loaded_edge_exceedances": sum(r["index"] > 1. for r in unique),
        "unique_loaded_edge_peak": max(unique, key=lambda r: r["index"]),
        "both_edge_sensitivity_peak": max(fields, key=lambda r: r["index"]), "fields": fields,
        "known_answer": {"old_capacity_relative_error": formula_error, "old_signed_cut_error_n_nmm": old_cut_error},
        "native_or_frame_solve": False, "reviewed_geometry_changed": False, "whole_member_stress_census_updated": False,
        "complete_joint_acceptance": False, "physical_release": False,
        "limits": ["Eight central/header NDS transverse components only, not the whole frame or complete joints.",
                   "Unchanged finite geometry/stations; every demand and loaded-edge sign uses fresh compatible 145 lb fields.",
                   "No old shear/normal stress ratio is scaled and no saw-cut, bore, contact or splitting resistance is established."]}
    shared.write(output / "result.json", result)
    shared.write(output / "body-balances.json", {"balances": balances})
    shared.write(output / "receipt.json", {"schema": "fresh_central_receiver_comparison_receipt/v1",
        "source_sha256": {mechanics.source_key(p): h for p, h in pins.items()},
        "output_sha256": {p.name: shared.sha(p) for p in output.iterdir() if p.is_file() and p.name != ".gitignore"},
        "status": "PASS_FRESH_CENTRAL_COMPONENT_RECOVERY_NOT_JOINT_ACCEPTANCE", "physical_release": False})
    print(json.dumps({k: v for k, v in result.items() if k not in ("fields", "limits")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--case-loads", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.case_loads, args.output)
