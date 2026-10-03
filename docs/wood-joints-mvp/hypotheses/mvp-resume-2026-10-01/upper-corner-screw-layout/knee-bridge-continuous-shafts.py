"""Parent-executed refresh of four retained continuous knee side shafts.

Importing this module reads no evidence and executes no mechanics. build(output)
binds fresh signed allocations to fresh D rows and evaluates the retained suite.
build(output, reuse_from=...) authenticates the completed same-input mechanics
in attempt01 and refreshes only the existing placement diagnostics.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import json
import math
import sys
from itertools import pairwise
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-continuous-shafts"
REUSE = RAW / "attempt01"
REUSE_RECEIPT_SHA256 = "1eba7e7047210366afe53e78d8dc6492281280ac0be6119a11e21383ea778e69"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = COMPARISON.with_name("response.npz")
EXPORT = HERE / "rawlocal/knee-bridge-response/attempt02"
SUMMARY = EXPORT / "summary.json"
EXPORT_RECEIPT = EXPORT / "receipt.json"
DEMANDS = EXPORT / "global-demands.jsonl"
REGISTER = HERE / "rawlocal/working-joint-register/attempt03/register.json"
CONTRACT = HERE / "rawlocal/knee-compatible/prepare-attempt02/input-contract.json"
OLD_SUITE = HERE / "rawlocal/knee-contact-entry/suite-attempt01/suite.json"
OLD_RECEIPT = OLD_SUITE.with_name("receipt.json")
CORE = HERE / "knee-compatible.py"
ENTRY = HERE / "knee-contact-entry.py"
ADAPTER = HERE / "knee-compatible-suite.py"
CONTACT = HERE / "upper-right-combined-transfer.py"
FIT = HERE.parent / "knee_bore_fit.py"
OLD_FIT = HERE.parent / "knee-bore-fit-attempt03/fit.json"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"knee_outer_{side}_side_{number}" for side in ("left", "right") for number in (1, 2)]
MASS_KG = 225.19791414318078
DEAD_FACTOR = 1.1110134616260479
PINS = {
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    SUMMARY: "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    EXPORT_RECEIPT: "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    DEMANDS: "f0d9bb8a8a25775a2571692183860b209708111b089f16538f7eab5d9adbe4c3",
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    CONTRACT: "f2876952e6b71d59acdbf20dacaef233444402e50bfcc6d3b9ec1967f2cad01f",
    OLD_SUITE: "b707952e5ad740ad2ebc0306bce17a37e4718e88c1164cba568d9a39a6e8b79a",
    OLD_RECEIPT: "63224d7d4e25bd8705123f75dc60663f6b4fcb8ab998d149ed2507ec79ee5e43",
    CORE: "8bfd4aab145e468f477a04a23073feebab9d9c3a0b4bb4cc1bc2407399fb3413",
    ENTRY: "dd20bb23b96e7e7e5f913a573108e1274b13179a7420c5fae01e3653fcae6bd8",
    ADAPTER: "9798402070802a1804f4c9797fea336cda66951179340c1255e7122315990304",
    CONTACT: "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0",
    FIT: "8993b3e5bc89d516841f644c34755ccc56642facd40e119a284d85b4fe30e252",
    OLD_FIT: "d4c8f42e2103082c2e11f29c21b99bd8d1f65e59a6570417b86401a5683af49e",
}
FLAGS = {
    "historical_case_loads_used_as_authority": False,
    "historical_force_or_acceptance_transferred": False,
    "proposal_adopted": False,
    "reviewed_geometry_changed": False,
    "formal_criterion_acceptance": False,
    "complete_joint_acceptance": False,
    "actual_hardware_or_wood_acceptance": False,
    "fabrication_release": False,
    "physical_release": False,
    "physical_failure_claimed": False,
    "whole_knee_group_compatibility_qualified": False,
    "frame_body_pose_compatibility_qualified": False,
    "actual_changed_hole_stiffness_qualified": False,
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


def debug_json(value):
    """Keep failed numerical evidence explicit without nonfinite JSON numbers."""
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite_float": repr(value)}
    if isinstance(value, dict):
        return {key: debug_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [debug_json(item) for item in value]
    return value


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and (path not in pins or pins[path] == digest),
            "conflicting or external source: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed source changed: " + str(path))


def source_map(pins):
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in sorted(pins.items())}


def pure_functions(path, names, namespace):
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(definitions) == len(names) and {node.name for node in definitions} == set(names)
            and all(not node.decorator_list for node in definitions), "retained pure function census differs")
    # Execute only the named definitions from an authenticated local source.
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**{name: namespace[name] for name in names})


def backend(np, brentq):
    def helper(length):
        return pure_functions(CONTACT, ("annulus", "compression", "series_contact", "hermite"),
                              {"np": np, "math": math, "require": require, "brentq": brentq,
                               "LENGTH": length, "K_HEAD": 10000.0})

    namespace = {"np": np, "math": math, "require": require, "pairwise": pairwise,
                 "K_WOOD": 20.0, "K_HEAD": 10000.0, "E_BOLT": 200000.0,
                 "ELEMENTS_PER_RECEIVER": 8, "GRADIENT_TOL": 1e-6}
    core = pure_functions(CORE, ("vector", "wrench", "assemble", "quads", "end_contact",
        "seat_tractions", "drive_for", "evaluate", "physical_recovery"), namespace)
    core.pure_helper, core.GRADIENT_TOL = helper, 1e-6
    entry = pure_functions(ENTRY, ("entry_step", "solve", "run_one"),
                           {"np": np, "math": math, "require": require})
    diagnostics = pure_functions(ADAPTER, ("diagnostics",),
        {"math": math, "FY_SENSITIVITIES_MPA": {"92ksi": 634.317671}}).diagnostics
    placement = pure_functions(FIT, ("witness",), {"np": np, "require": require}).witness
    return core, entry, diagnostics, placement


def sources(pins):
    assessment, comparison, summary, receipt = map(read, (ASSESSMENT, COMPARISON, SUMMARY, EXPORT_RECEIPT))
    require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] is True, "fresh gravity operators incomplete")
    require(comparison["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and comparison["response_sha256"] == PINS[RESPONSE]
            and comparison["complete_joint_acceptance"] is False
            and comparison["physical_release"] is False, "fresh frame binding differs")
    require([(s["gap_scale"], s["case_id"]) for s in comparison["states"]]
            == [(gap, case) for gap in (0.0, 1.0) for case in CASES]
            and all(s["status"].startswith("PASS_CONDITIONAL_") for s in comparison["states"]),
            "existing fresh frame state census incomplete")
    require(comparison["source_climber_weight_lb"] == 250
            and comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1
            and comparison["comparison_horizontal_force_n"] == 300, "fresh live load scales differ")
    for record in (assessment, comparison):
        require(record["modeled_mass_kg"] == MASS_KG and record["dead_load_factor"] == DEAD_FACTOR,
                "fresh mass or dead factor differs")
        for relative, digest in record["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for relative, digest in assessment["output_sha256"].items():
        path = (GRAVITY / relative).resolve()
        require(path.is_relative_to(GRAVITY), "gravity output path leaves source")
        bind(pins, path, digest)
    require(summary["schema"] == "knee-bridge-fresh-global-force-census/v1"
            and summary["status"] == "FRESH_GLOBAL_DEMANDS_EXPORTED"
            and summary["source_comparison_sha256"] == PINS[COMPARISON]
            and summary["census"]["global_structural_bolt_states"] == 624
            and summary["census"]["nominal_cases"] == 6
            and summary["fresh_modeled_mass_kg"] == MASS_KG and summary["dead_load_factor"] == DEAD_FACTOR,
            "fresh signed export authority differs")
    require(receipt["source_sha256"] == summary["source_sha256"]
            and receipt["output_sha256"]["summary.json"] == PINS[SUMMARY]
            and receipt["output_sha256"]["global-demands.jsonl"] == PINS[DEMANDS], "fresh export receipt differs")
    for relative, digest in summary["source_sha256"].items():
        bind(pins, ROOT / relative, digest)
    for name, digest in receipt["output_sha256"].items():
        path = (EXPORT / name).resolve()
        require(path.parent == EXPORT, "export receipt path leaves packet")
        bind(pins, path, digest)
    for path in (ASSESSMENT, GRAVITY / "model.json", GRAVITY / "operators.npz", GRAVITY / "row-identities.json"):
        require(comparison["source_sha256"][path.relative_to(ROOT).as_posix()] == pins[path],
                "frame consumed different fresh operators")
    authenticate(pins)
    original, old_suite, old_receipt, old_fit = map(read, (CONTRACT, OLD_SUITE, OLD_RECEIPT, OLD_FIT))
    require(original["schema"] == "knee_three_receiver_first_order_contract/v1"
            and original["producer_sha256"] == PINS[CORE]
            and old_suite["producer_sha256"] == PINS[ENTRY]
            and old_receipt["output_sha256"]["suite.json"] == PINS[OLD_SUITE]
            and old_suite["original_model"] == original["model"], "retained method/geometry binding differs")
    # Historical receipts remain named and byte-exact; none becomes a fresh load pin.
    for reference in original["source_receipts"].values():
        bind(pins, ROOT / reference["path"], reference["sha256"])
    authenticate(pins)
    require([(s["case_id"], s["axis_id"]) for s in original["boundaries"]]
            == [(case, axis) for axis in AXES for case in CASES]
            and len(old_suite["states"]) == 24
            and set(original["geometry"]) == set(old_fit["bore_geometry"]) == set(AXES)
            and old_fit["placement_count"] == 96, "retained finite census differs")
    model = original["model"]
    require((model["wood_bore_and_seat_stiffness_mpa_per_mm"], model["bolt_E_mpa"],
             model["head_contact_stiffness_mpa_per_mm"], model["elements_per_receiver"])
            == (20.0, 200000.0, 10000.0, 8)
            and model["numerical_tolerances"]["mixed_gradient_n"] == 1e-6
            and model["numerical_tolerances"]["force_n"] == 1e-6
            and math.isclose(model["numerical_tolerances"]["moment_nmm"], 215.9e-6, rel_tol=0, abs_tol=1e-15)
            and model["numerical_tolerances"]["max_newton_iterations"] == 150
            and (model["beam_nodes"], model["ungauged_transverse_variables"], model["gauged_transverse_variables"])
            == (25, 112, 108)
            and model["end_profile"]["washer_ID_max_mm"] == 8.3058
            and model["end_profile"]["washer_OD_min_mm"] == 18.4658
            and model["end_profile"]["hypothetical_concentric_head_and_nut_flat_radius_mm"] == 5.0,
            "retained contact laws, profile or iteration budget differ")
    demands = [json.loads(line) for line in DEMANDS.read_text().splitlines()]
    require(len(demands) == 1020 and sum(r["kind"] == "structural_bolt" for r in demands) == 624
            and summary["census"]["screw_states"] == 396
            and len({(r["case_id"], r["axis_id"]) for r in demands}) == 1020,
            "fresh signed global export census differs")
    selected = {(r["case_id"], r["axis_id"]): r for r in demands if r["axis_id"] in AXES}
    register = read(REGISTER)
    identities = {r["axis_id"]: {key: r[key] for key in ("axis_id", "receivers", "interfaces", "outer_tie")}
                  for r in register["axes"] if r["axis_id"] in AXES}
    # Keep only identity fields; per-state allocations and old joint status are unused.
    identities = {axis: {"receivers": row["receivers"],
        "interfaces": [{key: p[key] for key in ("plane_id", "component_rows", "component_directions_xyz")}
                       for p in row["interfaces"]], "tie_row": row["outer_tie"]["row"],
        "tie_row_id": row["outer_tie"]["row_id"]} for axis, row in identities.items()}
    require(set(identities) == set(AXES) and set(selected) == {(case, axis) for axis in AXES for case in CASES},
            "four nominal shaft identities missing")
    for axis in AXES:
        geometry, bore = original["geometry"][axis], old_fit["bore_geometry"][axis]
        require(geometry["bolt_axis_xyz"] == bore["axis_xyz"]
                and geometry["head_seat_point_mm"] == bore["head_seat_point_mm"]
                and geometry["shaft_diameter_mm"] == bore["shaft_diameter_mm"],
                "retained mechanics/placement shaft geometry differs")
        for receiver, field in zip(geometry["receivers"], bore["receivers"], strict=True):
            require(all(receiver[key] == field[key] for key in
                    ("member", "start_point_mm", "end_point_mm", "bore_diameter_mm", "radial_clearance_mm")),
                    "retained mechanics/placement bearing trace differs")
    return original, old_suite, old_fit, comparison, selected, identities


def boundaries(np, original, selected, identities, model, rows, operators, response):
    require(len(rows) == 1888 and [r["row"] for r in rows] == list(range(1888)), "fresh source row census differs")
    D = operators["D"]
    require(D.shape == (1888, 6 * len(model["body_names"])), "fresh D/body ordering differs")
    coordinates = model["physical_node_coordinates_mm"]
    datums = {body: np.mean([coordinates[str(node)] for node in sorted(set(nodes))], axis=0)
              for body, nodes in model["body_nodes"].items()}
    states = []
    for axis in AXES:
        geometry, ids = original["geometry"][axis], identities[axis]
        order = geometry["receiver_order"]
        side = "left" if "_left_" in axis else "right"
        require(order == [f"knee_outer_{side}_spine", f"base_side_{side}", f"knee_outer_{side}_inner_frame_block"]
                and len(geometry["receivers"]) == 3 and set(ids["receivers"]) == set(order)
                and geometry["shaft_diameter_mm"] == 6.35, "retained actual local shaft/order differs")
        n, head, datum = (np.asarray(geometry[key], dtype=float) for key in ("bolt_axis_xyz", "head_seat_point_mm", "datum_mm"))
        require(abs(float(n @ n) - 1) <= 1e-12, "invalid retained shaft axis")
        for index, receiver in enumerate(geometry["receivers"]):
            lo, hi = receiver["interval_from_head_wood_face_mm"]
            require(receiver["member"] == order[index] and hi > lo
                    and math.isclose(hi - lo, (38.1, 88.9, 88.9)[index], abs_tol=1e-8)
                    and (index != 0 or abs(lo) <= 1e-8)
                    and (index == 0 or abs(lo - geometry["receivers"][index - 1]["interval_from_head_wood_face_mm"][1]) <= 1e-8)
                    and receiver["bore_diameter_mm"] == 7.5
                    and abs(receiver["radial_clearance_mm"] - (7.5 - 6.35) / 2) <= 1e-12
                    and np.linalg.norm(head + lo * n - receiver["start_point_mm"]) <= 1e-8
                    and np.linalg.norm(head + hi * n - receiver["end_point_mm"]) <= 1e-8,
                    "retained three-receiver bearing trace differs")
            grain = np.asarray(geometry["grain_xyz"][index])
            require(abs(float(grain @ grain) - 1) <= 1e-8 and abs(float(n @ grain)) <= 1e-8,
                    "retained receiver has unsupported axial grain orientation")
        require(abs(geometry["modeled_wood_grip_mm"] - 215.9) <= 1e-8
                and np.linalg.norm(head + geometry["modeled_wood_grip_mm"] * n - geometry["nut_seat_point_mm"]) <= 1e-8,
                "retained complete grip or nut seat differs")
        selected_rows = [i for i, r in enumerate(rows) if r["row_id"].startswith(axis + "/")]
        require(len(ids["interfaces"]) == 2 and len(selected_rows) == 5
                and set(selected_rows) == {ids["tie_row"], *(i for p in ids["interfaces"] for i in p["component_rows"])},
                "four lateral rows/one tie census differs")
        basis = np.asarray(ids["interfaces"][0]["component_directions_xyz"], dtype=float).T
        require(np.max(abs(basis.T @ basis - np.eye(2))) <= 1e-12
                and np.linalg.norm(basis.T @ n) <= 1e-12, "retained lateral basis invalid")
        for case in CASES:
            raw, allocation = response[case + "_gap_raw_force_n"], selected[case, axis]
            require(raw.shape == (1888,) and np.isfinite(raw).all() and allocation["kind"] == "structural_bolt"
                    and set(allocation["receivers"]) == set(order), "fresh nominal allocation invalid")
            planes = []
            point_forces = {member: np.zeros(3) for member in order}
            point_moments = {member: np.zeros(3) for member in order}
            for plane_index, (plane, exported) in enumerate(zip(ids["interfaces"], allocation["interfaces"], strict=True)):
                indices = plane["component_rows"]
                require(len(indices) == 2 and all(exported[key] == plane[key] for key in
                        ("plane_id", "component_rows", "component_directions_xyz"))
                        and np.max(abs(raw[indices] - exported["components_n"])) <= 1e-9,
                        "fresh signed plane/export mismatch")
                for i, direction in zip(indices, plane["component_directions_xyz"], strict=True):
                    owner = rows[i]["ownership"]
                    require(rows[i]["row_id"] == plane["plane_id"]
                            and rows[i]["law"]["intended_law"] == "bilateral"
                            and [owner["first_body"], owner["second_body"]] == order[plane_index:plane_index + 2]
                            and owner["direction_global_xyz"] == direction
                            and np.linalg.norm(np.asarray(owner["point_mm"]) - geometry["interface_points_mm"][plane_index]) <= 1e-8,
                            "fresh signed plane row ownership differs")
                require(np.max(abs(np.asarray(plane["component_directions_xyz"]).T - basis)) <= 1e-12,
                        "two-plane transverse basis differs")
                planes.append({**plane, "first_body": order[plane_index], "second_body": order[plane_index + 1],
                    "point_mm": rows[indices[0]]["ownership"]["point_mm"],
                    "signed_components_n": raw[indices].tolist(),
                    "force_on_first_xyz_n": (basis @ raw[indices]).tolist()})
            tie = rows[ids["tie_row"]]
            tension = float(raw[ids["tie_row"]])
            require(tie["row_id"] == ids["tie_row_id"] == axis + "/outer-seat-axial-tie"
                    and tie["law"]["intended_law"] == "tension_only"
                    and [tie["ownership"]["first_body"], tie["ownership"]["second_body"]] == [order[0], order[2]]
                    and np.max(abs(np.asarray(tie["ownership"]["direction_global_xyz"]) - n)) <= 1e-12
                    and tension >= 0 and abs(tension - allocation["signed_axial_n"]) <= 1e-9,
                    "fresh single outer axial tie differs")
            for i in selected_rows:
                owner = rows[i]["ownership"]
                for member, sign in ((owner["first_body"], 1), (owner["second_body"], -1)):
                    force = sign * raw[i] * np.asarray(owner["direction_global_xyz"])
                    point_forces[member] += force
                    point_moments[member] += np.cross(np.asarray(owner["point_mm"]) - datum, force)
            recovered, errors = {}, {}
            for receiver_index, member in enumerate(order):
                body = model["body_names"].index(member)
                block = D[np.ix_(selected_rows, np.arange(6 * body, 6 * body + 6))]
                force = -block[:, :3].T @ raw[selected_rows]
                moment = -1000 * block[:, 3:].T @ raw[selected_rows] + np.cross(datums[member] - datum, force)
                error_force, error_moment = force - point_forces[member], moment - point_moments[member]
                require(np.max(abs(error_force)) < 1e-6 and np.max(abs(error_moment)) < 1e-5,
                        "fresh D contains an unsupported point transfer or unsaved receiver couple")
                expected_normal = tension * (1 if receiver_index == 0 else -1 if receiver_index == 2 else 0)
                require(abs(float(n @ force) - expected_normal) < 1e-6 and abs(float(n @ moment)) < 1e-5,
                        "fresh boundary needs unsupported middle axial force or shaft torsion")
                recovered[member] = {"force_xyz_n": force.tolist(), "moment_xyz_nmm": moment.tolist()}
                errors[member] = {"force_difference_xyz_n": error_force.tolist(),
                                  "retained_D_minus_point_couple_xyz_nmm": error_moment.tolist()}
            net_force = sum((np.asarray(r["force_xyz_n"]) for r in recovered.values()), np.zeros(3))
            net_moment = sum((np.asarray(r["moment_xyz_nmm"]) for r in recovered.values()), np.zeros(3))
            require(np.max(abs(net_force)) < 1e-6 and np.max(abs(net_moment)) < 1e-5,
                    "fresh full per-shaft receiver boundary does not balance")
            states.append({"case_id": case, "axis_id": axis, "gap_scale": 1.0,
                "transverse_basis_xyz": basis.T.tolist(), "physical_axial_tie_n": tension,
                "operator_connector_wrenches_on_receivers": recovered, "planes": planes,
                "source_rows": [{"raw_index": i, "signed_force_n": float(raw[i]), "identity": rows[i]} for i in selected_rows],
                "D_vs_signed_point_wrench_errors": errors,
                "net_connector_wrench": {"force_xyz_n": net_force.tolist(), "moment_xyz_nmm": net_moment.tolist()},
                "fresh_source_comparison_sha256": PINS[COMPARISON], "fresh_source_response_sha256": PINS[RESPONSE],
                "fresh_signed_export_summary_sha256": PINS[SUMMARY], "retained_geometry_contract_sha256": PINS[CONTRACT]})
    require(len(states) == 24, "fresh boundary census differs")
    return states


def reuse_nominal(pins, directory, original, selected, identities, rows):
    """Authenticate attempt01 without executing or copying its 24 local results."""
    directory = Path(directory).resolve()
    require(directory == REUSE.resolve(), "only the pinned same-input attempt01 may be reused")
    receipt_path = directory / "receipt.json"
    bind(pins, receipt_path, REUSE_RECEIPT_SHA256)
    authenticate(pins)
    receipt = read(receipt_path)
    producer = Path(__file__).resolve()
    producer_label = producer.relative_to(ROOT).as_posix()
    snapshot = directory / "producer.py.snapshot"
    require(receipt["schema"] == "knee_bridge_continuous_shaft_fresh_receipt/v1"
            and receipt["status"] == "STOP" and receipt["all24_nominal_completed"] is True
            and receipt["source_unchanged_before_and_after_execution"] is True
            and receipt["producer_sha256"] == receipt["source_sha256"][producer_label]
            == receipt["output_sha256"][snapshot.name], "same-input attempt01 receipt binding differs")
    for name, digest in receipt["output_sha256"].items():
        path = (directory / name).resolve()
        require(path.parent == directory, "reused output leaves attempt01")
        bind(pins, path, digest)
    for relative, digest in receipt["source_sha256"].items():
        if relative == producer_label:
            # The old live producer was revised; its immutable snapshot is its authority.
            bind(pins, snapshot, digest)
        else:
            bind(pins, ROOT / relative, digest)
    for path, digest in PINS.items():
        require(receipt["source_sha256"][path.relative_to(ROOT).as_posix()] == digest,
                "attempt01 used different retained or fresh inputs")
    authenticate(pins)
    previous, contract = read(directory / "suite.json"), read(directory / "fresh-inputs.json")
    expected = [(case, axis) for axis in AXES for case in CASES]
    require(previous["schema"] == "knee_bridge_continuous_shaft_fresh_suite/v1"
            and previous["status"] == "STOP" and previous["all24_nominal_completed"] is True
            and previous["failure"]["phase"] == "existing_placement_refresh"
            and previous["failure"]["error"] == "STOP: invalid fresh saved placement pose"
            and previous["source_sha256"] == receipt["source_sha256"]
            and previous["counts"] == receipt["counts"]
            and previous["case_ids"] == CASES and previous["axis_ids"] == AXES
            and [(r["case_id"], r["axis_id"]) for r in previous["states"]] == expected
            and all(previous["counts"][key] == 24 for key in
                    ("mechanics_calls", "states_returned", "independent_reference_closure_states"))
            and previous["counts"]["historical_states_reused"] == 0,
            "attempt01 does not contain all 24 fresh local closures before the placement API STOP")
    require(contract["schema"] == "knee_bridge_continuous_shaft_fresh_contract/v1"
            and contract["geometry"] == original["geometry"] and contract["model"] == original["model"]
            and contract["retained_geometry_contract_sha256"] == PINS[CONTRACT]
            and contract["legacy_source_receipts_geometry_and_method_only"] == original["source_receipts"]
            and contract["fresh_load_sources"] == {path.relative_to(ROOT).as_posix(): PINS[path]
                for path in (ASSESSMENT, COMPARISON, RESPONSE, SUMMARY, EXPORT_RECEIPT, DEMANDS)}
            and [(r["case_id"], r["axis_id"]) for r in contract["boundaries"]] == expected,
            "reused geometry, laws or fresh load contract differs")
    states = []
    tolerances = contract["model"]["numerical_tolerances"]
    for index, (row, boundary) in enumerate(zip(previous["states"], contract["boundaries"], strict=True)):
        case, axis = expected[index]
        path = directory / f"state-{index:02d}.json"
        result = read(path)
        geometry, exported, ids = contract["geometry"][axis], selected[case, axis], identities[axis]
        require(row["index"] == index and row["result_path"] == path.relative_to(ROOT).as_posix()
                and row["result_sha256"] == receipt["output_sha256"][path.name]
                and result["case_id"] == case and result["axis_id"] == axis
                and row["status"] == result["status"] == "conditional_first_order_equilibrium"
                and row["defect"] is result["defect"] is None
                and row["newton_converged"] is result["newton_converged"] is True
                and row["independent_reference_equilibrium_closed"]
                is result["independent_reference_equilibrium_closed"] is True
                and row["reused_historical_state"] is False
                and result["scope"] == contract["model"] and result["physics_changed"] is False
                and result["fresh_boundary"] == boundary and boundary["gap_scale"] == 1.0,
                "reused local result identity, closure or same-input boundary differs")
        residual = result["physical_recovery_max_residual"]
        require(math.isfinite(result["full_mixed_gradient_max_n"])
                and math.isfinite(residual["force_n"]) and math.isfinite(residual["moment_nmm"])
                and result["full_mixed_gradient_max_n"] <= tolerances["mixed_gradient_n"]
                and residual["force_n"] <= tolerances["force_n"]
                and residual["moment_nmm"] <= tolerances["moment_nmm"]
                and row["full_mixed_gradient_max_n"] == result["full_mixed_gradient_max_n"]
                and row["physical_recovery_max_residual"] == residual,
                "reused state fails the unchanged full-gradient/force/moment recovery gates")
        require(row["receiver_order"] == geometry["receiver_order"]
                == [r["receiver"] for r in result["receivers"]]
                and row["wrench_datum_mm"] == geometry["datum_mm"]
                and row["operator_connector_wrenches_on_receivers"]
                == boundary["operator_connector_wrenches_on_receivers"]
                and all(r["target_D_connector_wrench"] == boundary["operator_connector_wrenches_on_receivers"][r["receiver"]]
                        for r in result["receivers"])
                and row["physical_axial_tie_n"] == row["single_physical_tie_n"]
                == result["normal_transfer"]["single_physical_tie_n"]
                == boundary["physical_axial_tie_n"] == exported["signed_axial_n"]
                and row["diagnostics"] == {key: value for key, value in result["diagnostics"].items()
                                           if key != "beam_stress_fields"}
                and result["diagnostic_references"] == previous["diagnostic_references"],
                "reused receiver wrenches, same-state T or diagnostic fields differ")
        for record in (row, result, boundary, previous):
            require(record["fresh_source_comparison_sha256"] == PINS[COMPARISON]
                    and record["fresh_source_response_sha256"] == PINS[RESPONSE],
                    "reused result has a different fresh frame source")
        for plane, registered, allocation in zip(boundary["planes"], ids["interfaces"], exported["interfaces"], strict=True):
            require(all(plane[key] == registered[key] == allocation[key] for key in
                        ("plane_id", "component_rows", "component_directions_xyz"))
                    and plane["signed_components_n"] == allocation["components_n"],
                    "reused signed plane differs from the current export/identity register")
        signed_rows = {r["raw_index"]: r for r in boundary["source_rows"]}
        expected_rows = {ids["tie_row"]: exported["signed_axial_n"]}
        for plane in exported["interfaces"]:
            expected_rows.update(zip(plane["component_rows"], plane["components_n"], strict=True))
        require(set(signed_rows) == set(expected_rows) and len(signed_rows) == 5
                and all(signed_rows[i]["identity"] == rows[i]
                        and signed_rows[i]["signed_force_n"] == force for i, force in expected_rows.items())
                and all(result[key] is value for key, value in FLAGS.items())
                and all(result[key] is None for key in
                        ("actual_hardware_capacity_n", "actual_washer_capacity_n", "native_joint_capacity_n")),
                "reused row ownership, qualification boundary or null capacity differs")
        states.append({**row, "reused_same_fresh_input_state": True,
                       "same_fresh_input_receipt_sha256": REUSE_RECEIPT_SHA256})
    reuse = {"source_directory": directory.relative_to(ROOT).as_posix(),
        "source_receipt_sha256": REUSE_RECEIPT_SHA256,
        "source_suite_sha256": receipt["output_sha256"]["suite.json"],
        "source_producer_snapshot_sha256": receipt["producer_sha256"],
        "source_fresh_inputs_sha256": receipt["output_sha256"]["fresh-inputs.json"],
        "source_mechanics_calls": receipt["counts"]["mechanics_calls"],
        "same_fresh_input_states_reused": len(states), "state_files_copied": 0,
        "old_live_producer_authority_replaced_by": snapshot.relative_to(ROOT).as_posix(),
        "source_mechanics_runtime": previous["runtime"],
        "prior_status": previous["status"], "prior_failure": previous["failure"]}
    return contract, states, previous["diagnostic_references"], reuse


def placements(np, witness, geometries, model, rows, comparison, response, results, fits, debug):
    retained = [row for row in rows if row["ownership"]["second_body"] != "floor"]
    floor_members = sorted({row["ownership"]["first_body"] for row in rows
                            if row["ownership"]["second_body"] == "floor"})
    # simple_frame.lump_floor preserves retained-row order, then appends three
    # mean coordinates per floor footprint. q is not a raw-row displacement array.
    expected_q_size = len(retained) + 3 * len(floor_members)
    require(len(rows) == 1888 and len(retained) == 1588 and len(floor_members) == 8
            and [row["row"] for row in rows] == list(range(len(rows))), "saved floor transform census differs")
    layout = {"retained_connector_coordinates": len(retained), "floor_footprint_count": len(floor_members),
        "floor_mean_coordinates": 3 * len(floor_members), "lumped_q_size": expected_q_size,
        "rigid_coordinate_size": 6 * len(model["body_names"]),
        "connector_indexing": "Nonfloor rows in original row-list order; three means per floor footprint follow."}
    centers = {body: np.mean([model["physical_node_coordinates_mm"][str(node)] for node in nodes], axis=0)
               for body, nodes in model["body_nodes"].items()}
    for state in comparison["states"]:
        case, gap = state["case_id"], state["gap_scale"]
        tag = case + ("_gap" if gap else "_zero")
        rigid, q = response[tag + "_rigid_coordinates"], response[tag + "_lumped_q_mm"]
        debug.update(case_id=case, gap_scale=gap, saved_tag=tag, pose_layout=layout,
                     actual_rigid_shape=list(rigid.shape), actual_lumped_q_shape=list(q.shape))
        require(rigid.shape == (6 * len(model["body_names"]),) and q.shape == (expected_q_size,)
                and np.isfinite(rigid).all() and np.isfinite(q).all(), "invalid fresh saved placement pose")
        for axis in AXES:
            geometry = geometries[axis]
            datum, middle = np.asarray(geometry["head_seat_point_mm"]), geometry["receiver_order"][1]
            debug.update(case_id=case, axis_id=axis, gap_scale=gap, motion_mode=None)
            rigid_poses = {}
            for receiver in geometry["receivers"]:
                body = receiver["member"]
                offset = 6 * model["body_names"].index(body)
                rotation = rigid[offset + 3:offset + 6] / 1000
                translation = rigid[offset:offset + 3] + np.cross(rotation, datum - centers[body])
                rigid_poses[body] = translation, rotation
            middle_pose = rigid_poses[middle]
            rigid_poses = {body: (t - middle_pose[0], r - middle_pose[1]) for body, (t, r) in rigid_poses.items()}
            total, residuals = {middle: (np.zeros(3), np.zeros(3))}, []
            for receiver in (geometry["receivers"][0], geometry["receivers"][2]):
                body = receiver["member"]
                ports = [i for i, row in enumerate(retained) if
                         {row["ownership"]["first_body"], row["ownership"]["second_body"]} == {body, middle}]
                require(len(ports) == 8, "retained knee interface motion-port census differs")
                mapping = []
                for i in ports:
                    owner = retained[i]["ownership"]
                    direction = np.asarray(owner["direction_global_xyz"])
                    sign = 1 if owner["first_body"] == body else -1
                    mapping.append(sign * np.r_[direction, np.cross(np.asarray(owner["point_mm"]) - datum, direction)])
                mapping = np.asarray(mapping)
                pose, _, rank, _ = np.linalg.lstsq(mapping, q[ports], rcond=None)
                require(rank == 6, "incomplete fresh interface total-motion fit")
                residual = float(np.max(abs(mapping @ pose - q[ports])))
                total[body], residuals = (pose[:3], pose[3:]), [*residuals, residual]
                fits.append({"case_id": case, "axis_id": axis, "gap_scale": gap, "body": body,
                    "raw_rows": [retained[i]["row"] for i in ports], "lumped_q_indices": ports,
                    "translation_mm": pose[:3].tolist(),
                    "rotation_rad": pose[3:].tolist(), "maximum_projection_residual_mm": residual})
            bore = {"axis_xyz": geometry["bolt_axis_xyz"], "head_seat_point_mm": geometry["head_seat_point_mm"],
                    "shaft_diameter_mm": geometry["shaft_diameter_mm"], "receivers": geometry["receivers"]}
            for mode, poses in (("saved_rigid_components", rigid_poses), ("interface_total_motion_fit", total)):
                debug["motion_mode"] = mode
                results.append({"case_id": case, "axis_id": axis, "gap_scale": gap, "motion_mode": mode,
                    "local_fit_maximum_residual_mm": max(residuals) if mode == "interface_total_motion_fit" else None,
                    **witness(bore, poses, datum), "fresh_source_response_sha256": PINS[RESPONSE],
                    "body_pose_compatibility_qualified": False, "local_force_acceptance_transferred": False})
    require(len(results) == len(fits) == 96, "existing 96-placement/96-interface-fit census differs")
    return layout


def build(output, *, reuse_from=None):
    """Parent API; reuse_from=attempt01 performs only placement postprocessing."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    states, placed, fits, failure, debug = [], [], [], None, {}
    boundary_states, fresh_contract, references = [], None, None
    reuse, placement_layout = None, None
    mechanics_calls = 0
    phase, active = "source_authentication", None
    previous_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        import numpy as np

        runtime = {"python": sys.version.split()[0], "numpy": np.__version__}

        authenticate(pins)
        original, old_suite, _old_fit, comparison, selected, identities = sources(pins)
        frame_model, rows = (read(GRAVITY / name) for name in ("model.json", "row-identities.json"))
        if reuse_from is not None:
            phase = "same_fresh_mechanics_authentication"
            fresh_contract, states, references, reuse = reuse_nominal(
                pins, reuse_from, original, selected, identities, rows)
            boundary_states = fresh_contract["boundaries"]
            witness = pure_functions(FIT, ("witness",), {"np": np, "require": require}).witness
        else:
            import scipy
            from scipy.optimize import brentq

            runtime["scipy"] = scipy.__version__
            phase = "fresh_boundary_binding"
            with np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators, np.load(RESPONSE, allow_pickle=False) as response:
                boundary_states = boundaries(np, original, selected, identities, frame_model, rows, operators, response)
            fresh_contract = {"schema": "knee_bridge_continuous_shaft_fresh_contract/v1",
                "geometry": original["geometry"], "model": original["model"], "boundaries": boundary_states,
                "retained_geometry_contract_sha256": PINS[CONTRACT],
                "legacy_source_receipts_geometry_and_method_only": original["source_receipts"],
                "fresh_load_sources": {path.relative_to(ROOT).as_posix(): PINS[path]
                                       for path in (ASSESSMENT, COMPARISON, RESPONSE, SUMMARY, EXPORT_RECEIPT, DEMANDS)}}
            references = copy.deepcopy(old_suite["diagnostic_references"])
            references["smooth_beam_yield_sensitivities_mpa"] = {"92ksi": 634.317671}
            references["scope"] = "Retained nominal/mean diagnostics and only the existing conditional 92 ksi smooth-beam hypothesis."
            core, entry, diagnostic, witness = backend(np, brentq)
            original_evaluate = core.evaluate

            def traced_evaluate(pose, *args):
                debug["last_evaluated_pose"] = pose.tolist()
                debug["last_evaluation_may_be_rejected_trial"] = True
                value = original_evaluate(pose, *args)
                debug["last_energy_nmm"] = float(value[0])
                debug["last_full_mixed_gradient_max_n"] = float(np.max(abs(value[1])))
                return value

            core.evaluate = traced_evaluate
            write(output / "fresh-inputs.json", fresh_contract)
            phase = "nominal_local_mechanics"
            for index, boundary in enumerate(boundary_states):
                active, debug = {"index": index, "case_id": boundary["case_id"], "axis_id": boundary["axis_id"]}, {}
                geometry = fresh_contract["geometry"][boundary["axis_id"]]
                mechanics_calls += 1
                result = entry.run_one(core, fresh_contract, boundary, geometry)
                # Preserve a returned witness if subsequent postprocessing exposes an API gap.
                debug["returned_local_witness"] = result
                derived = diagnostic(result, geometry, references)
                result.update(fresh_boundary=boundary, fresh_source_comparison_sha256=PINS[COMPARISON],
                    fresh_source_response_sha256=PINS[RESPONSE], retained_geometry_contract_sha256=PINS[CONTRACT],
                    diagnostic_references=references, diagnostics=derived, actual_hardware_capacity_n=None,
                    actual_washer_capacity_n=None, native_joint_capacity_n=None, **FLAGS)
                require(result["case_id"] == boundary["case_id"] and result["axis_id"] == boundary["axis_id"]
                        and [r["receiver"] for r in result["receivers"]] == geometry["receiver_order"]
                        and result["normal_transfer"]["single_physical_tie_n"] == boundary["physical_axial_tie_n"],
                        "returned same-state receiver/tie ownership differs")
                path = output / f"state-{index:02d}.json"
                write(path, result)
                states.append({**active, "status": result["status"], "defect": result["defect"],
                    "receiver_order": geometry["receiver_order"], "wrench_datum_mm": geometry["datum_mm"],
                    "operator_connector_wrenches_on_receivers": boundary["operator_connector_wrenches_on_receivers"],
                    "physical_axial_tie_n": boundary["physical_axial_tie_n"],
                    "fresh_source_comparison_sha256": PINS[COMPARISON],
                    "fresh_source_response_sha256": PINS[RESPONSE],
                    "newton_converged": result["newton_converged"],
                    "independent_reference_equilibrium_closed": result["independent_reference_equilibrium_closed"],
                    "result_path": path.relative_to(ROOT).as_posix(), "result_sha256": sha(path),
                    "physical_recovery_max_residual": result["physical_recovery_max_residual"],
                    "full_mixed_gradient_max_n": result["full_mixed_gradient_max_n"],
                    "single_physical_tie_n": boundary["physical_axial_tie_n"],
                    "diagnostics": {key: value for key, value in derived.items() if key != "beam_stress_fields"},
                    "reused_historical_state": False, "reused_same_fresh_input_state": False})
                print(json.dumps({**active, "status": result["status"]}), flush=True)
                if not result["independent_reference_equilibrium_closed"]:
                    failure = {"phase": phase, **active, "error": result["defect"],
                        "iteration_history": result["iteration_history"], "last_accepted_iterate": result["accepted_iterate"],
                        "physical_recovery_max_residual": result["physical_recovery_max_residual"], **FLAGS}
                    break
        if failure is None:
            require(len(states) == 24, "24 same-fresh-input nominal states incomplete")
            phase, active, debug = "existing_placement_refresh", None, {}
            with np.load(RESPONSE, allow_pickle=False) as response:
                placement_layout = placements(np, witness, fresh_contract["geometry"], frame_model, rows,
                                              comparison, response, placed, fits, debug)
            write(output / "placements.json", {"records": placed, "interface_fits": fits,
                "existing_gap_scales": [0.0, 1.0], "existing_motion_modes": ["saved_rigid_components", "interface_total_motion_fit"],
                "fresh_source_response_sha256": PINS[RESPONSE], "pose_layout": placement_layout, **FLAGS})
            missed = [r for r in placed if not r["straight_shaft_placement_found"]]
            if missed:
                failure = {"phase": phase, "error": "Existing sufficient straight-shaft witness did not locate every fresh placement",
                           "unlocated_placements": missed, "incompatibility_proved": False, **FLAGS}
        authenticate(pins)
    except Exception as error:  # noqa: BLE001 -- persist STOP for a retained API/numerical failure.
        failure = {"phase": phase, "active_state": active, "error_type": type(error).__name__,
                   "error": str(error), "partial_debug": debug_json(debug),
                   "incompatibility_proved": False, **FLAGS}
        runtime = {"python": sys.version.split()[0]}
    finally:
        sys.dont_write_bytecode = previous_bytecode
    sources_unchanged = False
    try:
        authenticate(pins)
        sources_unchanged = True
    except (ValueError, OSError) as error:
        failure = {"phase": "final_source_authentication", "error": str(error), "prior_failure": failure, **FLAGS}
    closed = [row for row in states if row["independent_reference_equilibrium_closed"]]
    peak = max(closed, key=lambda row: row["diagnostics"]["peak_same_state_same_position_smooth_proxy"]["nominal_smooth_von_mises_proxy_mpa"]) if closed else None
    summary = {"schema": "knee_bridge_continuous_shaft_fresh_suite/v1",
        "status": "STOP" if failure else "COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS",
        "failure": failure, "states": states, "case_ids": CASES, "axis_ids": AXES,
        "postprocess_only": reuse_from is not None, "reuse": reuse,
        "fresh_inputs_source_path": ((REUSE if reuse is not None else output) / "fresh-inputs.json").relative_to(ROOT).as_posix(),
        "all24_nominal_completed": len(states) == 24 and len(closed) == 24,
        "placement_diagnostics": {"result_file": "placements.json" if (output / "placements.json").exists() else None,
            "expected_records": 96, "returned_records": len(placed), "pose_layout": placement_layout,
            "existing_gap_scales": [0.0, 1.0],
            "existing_motion_modes": ["saved_rigid_components", "interface_total_motion_fit"],
            "geometric_witnesses_are_local_mechanics_states": False},
        "counts": {"physical_shafts": 4, "nominal_cases": 6, "expected_nominal_states": 24,
            "mechanics_calls": mechanics_calls, "states_returned": len(states), "independent_reference_closure_states": len(closed),
            "same_fresh_input_states_reused": sum(row["reused_same_fresh_input_state"] for row in states),
            "source_mechanics_calls": reuse["source_mechanics_calls"] if reuse else 0,
            "historical_states_reused": 0, "placements_returned": len(placed),
            "placements_found": sum(r["straight_shaft_placement_found"] for r in placed), "interface_fits": len(fits)},
        "peak_same_state_same_position_smooth_proxy": {"case_id": peak["case_id"], "axis_id": peak["axis_id"],
            **peak["diagnostics"]["peak_same_state_same_position_smooth_proxy"]} if peak else None,
        "diagnostic_references": references, "fresh_source_comparison_sha256": PINS[COMPARISON],
        "fresh_source_response_sha256": PINS[RESPONSE], "fresh_signed_export_summary_sha256": PINS[SUMMARY],
        "retained_geometry_contract_sha256": PINS[CONTRACT], "retained_method_suite_sha256": PINS[OLD_SUITE],
        "modeled_mass_kg": MASS_KG, "dead_load_factor": DEAD_FACTOR, "source_sha256": source_map(pins),
        "runtime": runtime, "mechanics_executed": mechanics_calls > 0,
        "native_run": False, "CAD_run": False, "frame_run": False, "tests_run": False,
        "coupons_run": False, "review_run": False, "helper_agents_created": False,
        "contact_laws_or_iteration_budget_changed": False, "local_feedback_to_global_frame": False,
        "actual_hardware_capacity_n": None, "actual_washer_capacity_n": None, "native_joint_capacity_n": None,
        "limits": [
            "Every nominal local result uses the current signed global allocations and complete fresh D receiver wrenches at the retained common datum. Only authenticated attempt01 results with identical fresh inputs may be reused; earlier load acceptance is not transferred.",
            "Retained continuous knee side shafts are 6.35 mm in 7.5 mm circular bores, with ordered 38.1/88.9/88.9 mm bearing lengths and the original 215.9 mm grip. The separate top-corner side diameter is not substituted.",
            "The original K20 wood, K10000 head, E200000 smooth beam, gauge, contact-entry solver, 150 iterations and 1e-6 mixed-gradient/full-force gate remain. Middle axial load and shaft torsion are unsupported and stop boundary preparation.",
            "Only the existing 92 ksi smooth-steel diagnostic is reported. Complete beam fields and same-position tension/bending/shear witnesses remain; diagnostic pressure and steel ratios are not adjusted joint resistance.",
            "The existing 96 geometric witnesses use the already saved fresh gap-zero and nominal responses and both original motion fits. Postprocess continuation uses 24 unchanged same-fresh-input mechanical results and performs zero new mechanical calls.",
            "A sufficient line not located is not proof of physical interference. Projection fits and isolated receiver poses do not qualify full elastic bore deformation, shared knee-group/body-pose compatibility, or static endpoint resistance.",
            "New spine holes affect separately owned net timber cuts; this packet retains the unchanged local bearing trace. Global H remains a filled-bore approximation with unqualified changed-hole stiffness.",
            "No neighboring connector, face contact or separate gravity load is appended to the isolated per-shaft boundary. Current global gravity transfer is already included in the prescribed receiver wrenches.",
            "No delivered hardware, washer metal, native joint capacity or physical release is established. STOP retains partial outputs/debug and does not assert physical failure.",
        ], **FLAGS}
    summary["failure"] = debug_json(summary["failure"])
    write(output / "suite.json", summary)
    if failure is not None:
        write(output / "partial-debug.json", debug_json({"failure": failure, "last_debug": debug,
            "partial_placements": placed, "partial_interface_fits": fits, **FLAGS}))
    write(output / "receipt.json", {"schema": "knee_bridge_continuous_shaft_fresh_receipt/v1",
        "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_map(pins),
        "postprocess_only": summary["postprocess_only"], "reuse": reuse,
        "status": summary["status"], "all24_nominal_completed": summary["all24_nominal_completed"],
        "counts": summary["counts"], "source_unchanged_before_and_after_execution": sources_unchanged,
        "output_sha256": {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()}, **FLAGS})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse-from", type=Path, help="Pinned attempt01; refresh placements with zero new mechanics")
    arguments = parser.parse_args()
    result = build(arguments.output, reuse_from=arguments.reuse_from)
    print(json.dumps({"status": result["status"], "counts": result["counts"], "failure": result["failure"]}))
    if result["failure"] is not None:
        raise SystemExit(1)
