"""Parent-owned first-order transfers for the four original outer corner cleats.

Importing this module does not read sources or run calculations. build(output)
authenticates the new gravity/frame packet, replaces every historical case load,
and calls only the preserved local matrix kernel and physical recovery functions.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-corner-replay"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = COMPARISON.with_name("response.npz")
FIRST = HERE / "corner-first-order.py"
BOTTOM = HERE / "bottom-corner-transfer.py"
TRACTION = HERE / "cleat-traction.py"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
MASS_KG = 225.19791414318078
DEAD_FACTOR = 1.1110134616260479
PINS = {
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    FIRST: "6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563",
    BOTTOM: "2b05f8a789ed1098d66a0b482c3c4531379a3b5c5bb538ef80f46adfc5356d77",
    TRACTION: "2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764",
}
FLAGS = {
    "proposal_adopted": False,
    "historical_case_loads_used_as_authority": False,
    "historical_acceptance_transferred": False,
    "formal_criterion_acceptance": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "reviewed_geometry_changed": False,
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, record):
    Path(path).write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, "consumed source changed: " + str(path))


def source_map(pins):
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in sorted(pins.items())}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "missing preserved helper")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def array_sha(value):
    digest = hashlib.sha256(f"{value.dtype.str}:{value.shape}".encode())
    digest.update(value.tobytes(order="C"))
    return digest.hexdigest()


def balance(np, wrench, force_tolerance, moment_tolerance, label):
    wrench = np.asarray(wrench, dtype=float)
    require(wrench.shape == (6,) and np.isfinite(wrench).all(), label + " is not a finite wrench")
    require(np.max(abs(wrench[:3])) <= force_tolerance
            and np.max(abs(wrench[3:])) <= moment_tolerance, label + " does not balance")


def fresh_inputs(pins):
    assessment, comparison = read(ASSESSMENT), read(COMPARISON)
    require(assessment["schema"] == "knee-bridge-gravity-operators/v1"
            and assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] is True
            and assessment["gravity_delta_in_proposal_operators"] is True,
            "completed new gravity operators required")
    require(comparison["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and comparison["response_sha256"] == PINS[RESPONSE], "new response binding differs")
    nominal = [state for state in comparison["states"] if state["gap_scale"] == 1.0]
    require(assessment["case_ids"] == [state["case_id"] for state in nominal] == CASES,
            "six nominal case identities/order differ")
    require(all(state["status"] in {"PASS_CONDITIONAL_COUPLED_FRAME_LAWS",
                                   "PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING"}
                for state in nominal), "new nominal frame case incomplete")
    require(comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1.0
            and comparison["source_climber_weight_lb"] == 250.0,
            "nominal live load scales differ")
    require(comparison["complete_joint_acceptance"] is False
            and comparison["physical_release"] is False, "frame source claims release")
    for record in (assessment, comparison):
        require(record["modeled_mass_kg"] == MASS_KG and record["dead_load_factor"] == DEAD_FACTOR,
                "new mass/dead factor differs")
        for relative, digest in record["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for relative, digest in assessment["output_sha256"].items():
        path = (GRAVITY / relative).resolve()
        require(path.is_relative_to(GRAVITY), "gravity output leaves source packet")
        bind(pins, path, digest)
    for path in (ASSESSMENT, *(GRAVITY / name for name in
                  ("model.json", "model-inputs.json", "operators.npz", "row-identities.json"))):
        require(comparison["source_sha256"][path.relative_to(ROOT).as_posix()] == pins[path],
                "frame did not consume this gravity source: " + str(path))
    authenticate(pins)
    model, inputs, rows = (read(GRAVITY / name) for name in
                          ("model.json", "model-inputs.json", "row-identities.json"))
    old_model, old_inputs = (read(HERE / "operators-attempt02" / name)
                             for name in ("model.json", "model-inputs.json"))
    require(model["modeled_mass_kg"] == inputs["modeled_mass_kg"] == MASS_KG
            and model["dead_load_factor"] == inputs["dead_load_factor"] == DEAD_FACTOR,
            "gravity model/input metadata differ")
    require([case["case_id"] for case in inputs["cases"]] == CASES,
            "fresh load columns differ")
    require(all(case["source_applied_load"] == old["source_applied_load"]
                and case["loaded_panel"] == old["loaded_panel"]
                for case, old in zip(inputs["cases"], old_inputs["cases"], strict=True)),
            "250 lb × 2 / 300 N / 100 mm cases changed")
    require(inputs["connections"] == old_inputs["connections"], "receiver order or global axes changed")
    require(all(model[key] == old_model[key] for key in
                ("body_names", "body_nodes", "physical_node_coordinates_mm", "proposed_corner_axes")),
            "original corner placement/geometry changed")
    return assessment, comparison, model, rows


def prepare_groups(first, bottom, pins):
    """Historical preparations supply geometry and matrices, never replay loads."""
    for path, digest in first.PINS.items():
        bind(pins, path, digest)
    authenticate(pins)
    groups, common = [], {}
    for side, mechanics, helper, blocks, cells, n, basis, _old_sources, geometry in first.prepare(pins):
        groups.append({"level": "top", "side": side, "host": mechanics.HOST,
                       "cleat": mechanics.CLEAT, "family": geometry,
                       "kernel": (mechanics, helper, blocks, cells, n, basis)})
    for side in ("left", "right"):
        old = read(HERE / f"rawlocal/upper-{side}-block/attempt01/checks.json")
        common["top", side] = (old["common_datum_xyz_mm"] if side == "right"
                               else old["model"]["common_cleat_datum_xyz_mm"])
    prepared, old_pins = bottom.prepare()
    for path, digest in old_pins.items():
        bind(pins, path, digest)
    for definition in prepared["groups"]:
        # Discard historical case loads before binding the preserved matrix kernel.
        definition = {key: value for key, value in definition.items() if key != "sources"}
        mechanics, helper, blocks, cells = bottom.configure(definition)
        groups.append({"level": "bottom", "side": definition["side"],
                       "host": definition["host"], "cleat": definition["cleat"],
                       "family": definition["family"], "bottom_definition": definition,
                       "kernel": (mechanics, helper, blocks, cells,
                                  bottom.np.asarray(definition["n"]), bottom.np.asarray(definition["basis"]))})
    for side, block in prepared["blocks"].items():
        common["bottom", side] = block["common_datum_xyz_mm"]
    require(len(groups) == 8 and len(common) == 4, "four-cleat/eight-host census differs")
    authenticate(pins)
    return groups, common


def fresh_boundaries(np, traction, bottom, groups, common, model, rows, operators, response, labels):
    D, F, W = (operators[name] for name in ("D", "F", "W"))
    require(D.shape == (len(rows), 6 * len(model["body_names"]))
            and F.shape == (len(labels), 12) and W.shape == (6 * len(model["body_names"]), 12),
            "current row/load dimensions differ")
    require([row["row"] for row in rows] == list(range(len(rows))), "row indexing differs")
    raw = {case: response[case + "_gap_raw_force_n"] for case in CASES}
    require(all(value.shape == (len(rows),) and np.isfinite(value).all() for value in raw.values()),
            "new nominal raw force vector invalid")
    weights = {}
    for level, side in common:
        cleat = next(g["cleat"] for g in groups if (g["level"], g["side"]) == (level, side))
        nodes = set(model["body_nodes"][cleat])
        selected = [(index, node, dof - 1) for index, (node, dof) in enumerate(labels) if node in nodes]
        require(len(selected) == 3 * len(nodes)
                and {(node, dof) for _, node, dof in selected} == {(node, dof) for node in nodes for dof in range(3)},
                "cleat nodal load census differs")
        require(np.max(abs(F[[i for i, _, _ in selected], 1::2])) == 0.0,
                "cleat has a live nodal load; own-weight interpretation invalid")
        body = model["body_names"].index(cleat)
        origin = bottom.body_datum(model, cleat)
        for index, case in enumerate(CASES):
            nodal = {node: np.zeros(3) for node in sorted(nodes)}
            for row, node, dof in selected:
                nodal[node][dof] = DEAD_FACTOR * F[row, 2 * index]
            actions = [traction.action("new_gravity_cleat_node", str(node),
                       model["physical_node_coordinates_mm"][str(node)], force, node_id=node)
                       for node, force in nodal.items()]
            mapped = traction.wrench(actions, common[level, side])
            whole = DEAD_FACTOR * W[6 * body:6 * body + 6, 2 * index]
            require(np.max(abs(W[6 * body:6 * body + 6, 2 * index + 1])) == 0.0,
                    "cleat W contains a live load")
            whole = whole.copy()
            whole[3:] *= 1000.0
            whole = traction.shifted(whole, origin, np.asarray(common[level, side]))
            balance(np, mapped - whole, 1e-6, 1e-6, "fresh cleat F/W recovery")
            weights[level, side, case] = {"actions": actions, "wrench_n_nmm": mapped.tolist(),
                                         "mapped_F_minus_W_n_nmm": (mapped - whole).tolist()}
    for group in groups:
        mechanics, _helper, blocks, cells, _n, _basis = group["kernel"]
        host, cleat = group["host"], group["cleat"]
        selected = sorted((row for row in rows if {row["ownership"]["first_body"], row["ownership"]["second_body"]}
                           == {host, cleat}), key=lambda row: row["row"])
        indices = [row["row"] for row in selected]
        expected = {row for bolt in blocks for row in (*bolt["source_component_rows"], bolt["source_tie_row"])}
        expected.update(cell["source"]["row"] for cell in cells)
        require(set(indices) == expected and len(indices) == len(expected) == (22 if group["level"] == "top" else 10),
                "current host connector row census differs")
        by_row = {row["row"]: row for row in selected}
        for cell in cells:
            require(all(cell["source"][key] == by_row[cell["source"]["row"]][key]
                        for key in ("row_id", "ownership", "law")), "face geometry/law changed")
        body = model["body_names"].index(host)
        dhost = D[indices, 6 * body:6 * body + 6]
        directions = [np.asarray(row["ownership"]["direction_global_xyz"]) *
                      (1 if row["ownership"]["first_body"] == host else -1) for row in selected]
        require(np.max(abs(-dhost[:, :3] - directions)) <= 1e-12, "D/physical host force signs differ")
        origin = bottom.body_datum(model, host)
        group["source_rows"], group["sources"] = indices, []
        for case in CASES:
            values = raw[case][indices]
            wrench = np.r_[-dhost[:, :3].T @ values, -1000.0 * dhost[:, 3:].T @ values]
            wrench = traction.shifted(wrench, origin, mechanics.DATUM)
            actions = [traction.action("new_frame_source_row", row["row_id"], row["ownership"]["point_mm"],
                       value * direction, row=row["row"], ownership=row["ownership"])
                       for row, direction, value in zip(selected, directions, values, strict=True)]
            point = traction.wrench(actions, mechanics.DATUM)
            require(np.max(abs(wrench[:3] - point[:3])) <= 1e-7, "D/physical point force sums differ")
            # Retain D's entire rotational boundary, including any source row couple.
            # No free couple is appended to independently recovered wood actions.
            originals = []
            for bolt in blocks:
                force = sum(np.asarray(actions[indices.index(row)]["force_xyz_n"])
                            for row in bolt["source_component_rows"])
                tension = float(raw[case][bolt["source_tie_row"]])
                require(tension >= 0, "new source bolt tension is negative")
                originals.append({"axis_id": bolt["axis_id"], "signed_T_n": tension,
                                  "V_n": float(np.linalg.norm(force)),
                                  "signed_plane_components_n": raw[case][bolt["source_component_rows"]].tolist(),
                                  "force_on_host_xyz_n": force.tolist()})
            source = {"case_id": case, "gap_scale": 1.0,
                      "source_comparison_sha256": PINS[COMPARISON], "source_response_sha256": PINS[RESPONSE],
                      "source_gravity_assessment_sha256": PINS[ASSESSMENT],
                      "source_connector_wrench_on_host_n_nmm": wrench.tolist(),
                      "external_drive_wrench_n_nmm": (-wrench).tolist(),
                      "source_point_actions": actions, "D_point_force_residual_n": (wrench[:3] - point[:3]).tolist(),
                      "retained_source_free_couple_nmm": (wrench - point)[3:].tolist(),
                      "source_individual_bolts": originals,
                      "source_original_fields_meaning": "Authenticated new nominal raw-force components; historical field names only.",
                      "source_face_cells": [{"row": cell["source"]["row"],
                         "compression_n": float(raw[case][cell["source"]["row"]]),
                         "stiffness_n_per_mm": cell["source"]["law"]["stiffness_N_per_mm"]} for cell in cells]}
            require(all(cell["compression_n"] >= 0 for cell in source["source_face_cells"]),
                    "new source face compression is negative")
            source["source_face_compression_n"] = sum(cell["compression_n"] for cell in source["source_face_cells"])
            group["sources"].append(source)
    for key, datum in common.items():
        for case_index, case in enumerate(CASES):
            residual = np.asarray(weights[key[0], key[1], case]["wrench_n_nmm"]).copy()
            for group in (g for g in groups if (g["level"], g["side"]) == key):
                residual -= traction.shifted(group["sources"][case_index]["source_connector_wrench_on_host_n_nmm"],
                                             group["kernel"][0].DATUM, np.asarray(datum))
            balance(np, residual, 1e-6, 1e-6, "fresh source whole-cleat weight-once closure")
            weights[key[0], key[1], case]["source_whole_cleat_residual_n_nmm"] = residual.tolist()
    return weights


def build(output):
    """Calculate local transfers once; the parent serializes this explicit call."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    authenticate(pins)
    previous_path, previous_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        import numpy as np
        import scipy

        assessment, _comparison, model, rows = fresh_inputs(pins)
        first, bottom, traction = (module(path, name) for path, name in
                                  ((FIRST, "fresh_corner_first_order"), (BOTTOM, "fresh_corner_bottom"),
                                   (TRACTION, "fresh_corner_physical_traction")))
        groups, common = prepare_groups(first, bottom, pins)
        require(len({(g["cleat"], g["host"]) for g in groups}) == 8
                and len({b["axis_id"] for g in groups for b in g["kernel"][2]}) == 16,
                "original eight-host/sixteen-axis identities differ")
        for group in groups:
            mechanics, _helper, blocks, _cells, _n, _basis = group["kernel"]
            require((mechanics.KWOOD, mechanics.KHEAD, mechanics.EBOLT,
                     mechanics.GRADIENT_TOLERANCE, mechanics.FORCE_TOLERANCE, mechanics.MOMENT_TOLERANCE)
                    == (20.0, 10000.0, 200000.0, 1e-4, 0.001, 0.2)
                    and all(np.count_nonzero(block["geometric"]) == 0 for block in blocks),
                    "preserved first-order laws/tolerances differ")
        parser = module(bottom.PARSER, "fresh_corner_dof_parser")
        labels = parser.parse_dof_file(bottom.DOF)
        with np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators, \
                np.load(bottom.OPERATORS, allow_pickle=False) as old_operators, \
                np.load(RESPONSE, allow_pickle=False) as response:
            for name, expected in assessment["unchanged_array_sha256"].items():
                key = name.split("/")[0]
                fresh, old = operators[key], old_operators[key]
                if "/" in name:
                    fresh, old = fresh[:, 1::2], old[:, 1::2]
                require(array_sha(fresh) == array_sha(old) == expected,
                        "gross stiffness/rows/live columns changed: " + name)
            for group in groups:
                nodes = set(model["body_nodes"][group["cleat"]])
                dofs = [index for index, (node, _dof) in enumerate(labels) if node in nodes]
                require(np.array_equal(operators["F"][dofs], old_operators["F"][dofs]),
                        "original cleat own nodal mass changed")
            weights = fresh_boundaries(np, traction, bottom, groups, common, model, rows, operators, response, labels)
        authenticate(pins)
        preparation = [{"level": g["level"], "side": g["side"], "host": g["host"], "cleat": g["cleat"],
                        "geometry": g["family"], "host_interface_datum_xyz_mm": g["kernel"][0].DATUM.tolist(),
                        "normal_host_to_cleat_xyz": g["kernel"][4].tolist(),
                        "transverse_basis_xyz": g["kernel"][5].tolist(), "source_rows": g["source_rows"],
                        "axis_ids": [b["axis_id"] for b in g["kernel"][2]], "sources": g["sources"],
                        "bottom_definition": g.get("bottom_definition")} for g in groups]
        output.mkdir(parents=True, exist_ok=False)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        write(output / "fresh-transfer-inputs.json", {"case_ids": CASES, "groups": preparation,
              "own_weight_by_cleat_case": [{"level": level, "side": side, "case_id": case,
                 "common_datum_xyz_mm": common[level, side], **value}
                 for (level, side, case), value in weights.items()],
              "source_sha256": source_map(pins), **FLAGS})
        states, failure, debug, hosts = [], None, {}, {}
        case = level = side = host = None
        try:
            for index, case in enumerate(CASES):
                for (level, side), datum in common.items():
                    hosts, actions, fields = {}, [], []
                    for group in (g for g in groups if (g["level"], g["side"]) == (level, side)):
                        host = group["host"]
                        mechanics, helper, blocks, cells, n, basis = group["kernel"]
                        debug = {}
                        state, beam_fields = mechanics.solve_case(helper, blocks, cells, n, basis,
                                                                 group["sources"][index], debug)
                        require(state["source_response_sha256"] == PINS[RESPONSE]
                                and state["case_id"] == case
                                and [b["axis_id"] for b in state["bolts"]] == [b["axis_id"] for b in blocks]
                                and len(state["face_cells"]) == (16 if level == "top" else 4),
                                "returned state source/geometry census differs")
                        if level == "top":
                            recovered, physical_host, seats, residual = first.physical_actions(
                                traction, helper, mechanics, group["family"], n, basis, state)
                            record = {"state": state, "physical_host_actions": physical_host,
                                      "wood_seat_recovery": seats, "physical_host_residual_n_nmm": residual.tolist()}
                        else:
                            recovered, record = bottom.recover(group["bottom_definition"], mechanics, helper, state)
                        balance(np, record["physical_host_residual_n_nmm"], 0.001, 0.2, "independent returned host")
                        cleat_residual = traction.wrench(recovered, mechanics.DATUM) + np.asarray(
                            state["source_connector_wrench_on_host_n_nmm"])
                        balance(np, cleat_residual, 0.001, 0.2, "independent returned cleat interface")
                        hosts[host] = {**record, "geometry": group["family"],
                                       "physical_cleat_interface_actions": recovered,
                                       "physical_cleat_interface_residual_n_nmm": cleat_residual.tolist(),
                                       "host_interface_datum_xyz_mm": mechanics.DATUM.tolist()}
                        actions.extend(recovered)
                        fields.extend({"host": host, **field} for field in beam_fields)
                    weight = weights[level, side, case]
                    residual = traction.wrench(actions + weight["actions"], np.asarray(datum))
                    balance(np, residual, 0.002, 0.4, "independent returned whole cleat")
                    states.append({"level": level, "side": side, "case_id": case, "cleat": group["cleat"],
                                   "common_datum_xyz_mm": datum, "hosts": hosts, "beam_fields": fields,
                                   "physical_cleat_actions": actions, "own_weight_actions_once": weight["actions"],
                                   "current_weight_once_n_nmm": weight["wrench_n_nmm"],
                                   "physical_whole_cleat_residual_n_nmm": residual.tolist(), **FLAGS})
                    print(json.dumps({"level": level, "side": side, "case_id": case,
                                      "completed_block_states": len(states)}), flush=True)
            require(len(states) == 24 and len({(s["level"], s["side"], s["case_id"]) for s in states}) == 24,
                    "four-cleat six-case completion census differs")
        except (ValueError, RuntimeError, OSError, np.linalg.LinAlgError) as error:
            failure = {"case_id": case, "level": level, "side": side, "host": host, "error": str(error),
                       "last_accepted_iteration": debug, "partial_block_host_states": hosts,
                       "incompatibility_proved": False, "physical_failure_claimed": False,
                       "retry_or_law_sweep_performed": False}
        # Stable extractor API: one native same-state bolt record and all beam fields
        # per axis/case, with host/cleat geometry and independent physical receipts.
        bolts = [{"level": block["level"], "side": block["side"], "case_id": block["case_id"],
                  "host": host, "cleat": block["cleat"], "geometry": record["geometry"],
                  "axis_id": bolt["axis_id"], "local_bolt_state": bolt,
                  "beam_fields": [field for field in block["beam_fields"] if field["axis_id"] == bolt["axis_id"]],
                  "physical_host_residual_n_nmm": record["physical_host_residual_n_nmm"],
                  "physical_cleat_interface_residual_n_nmm": record["physical_cleat_interface_residual_n_nmm"],
                  "physical_whole_cleat_residual_n_nmm": block["physical_whole_cleat_residual_n_nmm"]}
                 for block in states for host, record in block["hosts"].items() for bolt in record["state"]["bolts"]]
        counts = {"completed_block_states": len(states), "completed_host_states": sum(len(s["hosts"]) for s in states),
                  "top_bolt_states": sum(b["level"] == "top" for b in bolts),
                  "bottom_bolt_states": sum(b["level"] == "bottom" for b in bolts), "completed_bolt_states": len(bolts)}
        if failure is None:
            require(counts == {"completed_block_states": 24, "completed_host_states": 48,
                               "top_bolt_states": 48, "bottom_bolt_states": 48, "completed_bolt_states": 96},
                    "48 top + 48 bottom bolt census differs")
        authenticate(pins)
        result = {"schema": "knee_bridge_original_corner_first_order_replay/v1",
                  "status": "STOP" if failure else "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES",
                  "failure": failure, "case_ids": CASES, "counts": counts, "states": states,
                  "same_state_bolt_actions": bolts, "preparation": preparation,
                  "modeled_mass_kg": MASS_KG, "dead_load_factor": DEAD_FACTOR,
                  "fresh_load_sources": {path.relative_to(ROOT).as_posix(): PINS[path]
                                         for path in (ASSESSMENT, COMPARISON, RESPONSE)},
                  "source_sha256": source_map(pins),
                  "physical_tolerances": {"host_force_n": 0.001, "host_moment_nmm": 0.2,
                                          "whole_cleat_force_n": 0.002, "whole_cleat_moment_nmm": 0.4},
                  "geometric_shortening_and_preload_stiffness": False, "balancing_free_couples_added": 0,
                  "material_or_contact_laws_changed": False, "local_redistribution_feeds_back_to_frame": False,
                  "native_CAD_or_frame_execution": False, "known_answers_executed": False,
                  "tests_run": False, "review_loop_run": False, "component_references_replayed": False,
                  "runtime": {"python": sys.version.split()[0], "numpy": np.__version__, "scipy": scipy.__version__},
                  "limits": [
                      "The new completed nominal frame is the only case-load authority; historical preparations supply unchanged geometry, matrices and provenance only.",
                      "Each original cleat receives its unchanged nodal self-weight once at the new dead factor; source host wrenches already include frame gravity transfer.",
                      "The preserved first-order reference-geometry kernel omits geometric shortening and preload stiffness together and adds no compensating wood moment.",
                      "Rigid timber, circular bore clearance, hypothetical K20 wood/K10000 head contacts, rigid concentric washers and smooth elastic bolts remain conditional assumptions.",
                      "Full boundary moments, signed bore forces, beam shears/moments, seat pressure moments and independent host/cleat receipts are retained for fresh component extraction.",
                      "Component references, redistributed timber cuts, group/splitting resistance, delivered hardware, washer-metal resistance and complete-joint acceptance are outside this transfer packet.",
                      "Neutral modes return representative poses; no stability, motion envelope or physical shop/climber release follows from convergence.",
                  ], **FLAGS}
        write(output / "checks.json", result)
        authenticate(pins)
        write(output / "receipt.json", {"source_sha256": source_map(pins),
              "output_sha256": {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()},
              "source_unchanged_before_and_after_write": True, "counts": counts,
              "status": result["status"], **FLAGS})
        authenticate(pins)
        return result
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = build(arguments.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "checks_sha256": sha(arguments.output / "checks.json")}))
    if result["failure"] is not None:
        raise SystemExit(1)
