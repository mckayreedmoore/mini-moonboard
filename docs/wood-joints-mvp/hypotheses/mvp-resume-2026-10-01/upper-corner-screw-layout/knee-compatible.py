"""Prepare a frozen knee boundary; parent runs the coupon and one K20 witness.

No native solver, CAD, frame replay, placement search, or resistance calculation
is called. Mechanical modes are explicit and write only below rawlocal/knee-compatible.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from itertools import pairwise
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-compatible"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
AXES = [f"knee_outer_{side}_side_{number}" for side in ("left", "right") for number in (1, 2)]
SELECTED = ("a12-left", "knee_outer_left_side_1")
K_WOOD, E_BOLT, K_HEAD = 20.0, 200000.0, 10000.0
ELEMENTS_PER_RECEIVER = 8
GRADIENT_TOL = 1e-6
FROZEN = {
    "assessment": (HERE / "operators-attempt02/operator-assessment.json", "1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a"),
    "model": (HERE / "operators-attempt02/model.json", "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626"),
    "rows": (HERE / "operators-attempt02/row-identities.json", "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27"),
    "operators": (HERE / "operators-attempt02/operators.npz", "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3"),
    "comparison": (HERE / "frame-250-attempt02/comparison.json", "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca"),
    "response": (HERE / "frame-250-attempt02/response.npz", "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7"),
    "screen": (PACKET / "three-member-screen-attempt02/four-screw250/screen.json", "ccd5b3bef3ff48a2468b47cc73da984f2a9ec7421e624bce3929032107ca17ba"),
    "screen_pins": (PACKET / "three-member-screen-attempt02/four-screw250/source-pins.json", "16a8f1972b99f18d57940af70b4aebd1505020d138fc598f294f1c4ea1edaa4b"),
    "bearing": (PACKET / "knee-bearing-attempt02/checks.json", "b56cc77e8a088f5cf7c1b6a84d8b8844cdfe335ecd2d2da68d6da138f0f2facb"),
    "placement": (PACKET / "knee-bore-fit-attempt03/fit.json", "d4c8f42e2103082c2e11f29c21b99bd8d1f65e59a6570417b86401a5683af49e"),
    "pure_helper": (HERE / "upper-right-combined-transfer.py", "fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0"),
    "engagement": (PACKET / "assembly-package/rawlocal/hardware-engagement/hardware-engagement.json", "93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a"),
    "hardware_inputs": (ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fastener-inputs.json", "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def read(path):
    return json.loads(path.read_text())


def label(path):
    return str(path.relative_to(ROOT))


def pins():
    receipts = {}
    for key, (path, expected) in FROZEN.items():
        require(sha(path) == expected, f"Frozen source changed: {path}")
        receipts[key] = {"path": label(path), "sha256": expected, "bytes": path.stat().st_size}
    return receipts


def vector(value):
    return np.asarray(value, dtype=float)


def wrench(force, moment):
    return {"force_xyz_n": force.tolist(), "moment_xyz_nmm": moment.tolist()}


def prepare():
    receipts = pins()
    screen, bearing, placement, model, rows = [read(FROZEN[key][0]) for key in ("screen", "bearing", "placement", "model", "rows")]
    require(screen["case_ids"] == bearing["case_ids"] == CASES, "Six-case source census changed")
    require(set(screen["geometry"]) == set(AXES), "Four-shaft geometry census changed")
    require(len(screen["bolt_cases"]) == len(bearing["states"]) == 24, "Frozen bearing census changed")
    require(len(bearing["endpoint_fields"]) == placement["placement_count"] == placement["placement_found_count"] == 96, "Frozen endpoints/placements changed")
    require((screen["peaks"]["92ksi"]["case_id"], screen["peaks"]["92ksi"]["axis_id"]) == SELECTED, "Same-state governing witness changed")
    for report in (screen, bearing):
        require(report["source_comparison_sha256"] == FROZEN["comparison"][1], "Different comparison source")
        require(report["source_response_sha256"] == FROZEN["response"][1], "Different force source")
    require(bearing["source_screen_sha256"] == FROZEN["screen"][1], "Bearing source changed")
    coordinates = model["physical_node_coordinates_mm"]
    body_datums = {
        body: np.mean([coordinates[str(node)] for node in sorted(set(model["body_nodes"][body]))], axis=0)
        for body in model["body_names"]
    }
    geometries, boundaries, max_force_error, max_moment_error = {}, [], 0.0, 0.0
    with np.load(FROZEN["operators"][0], allow_pickle=False) as operators, np.load(FROZEN["response"][0], allow_pickle=False) as response:
        operator = operators["D"]
        require(operator.shape == (len(rows), 6 * len(model["body_names"])), "D/body ordering changed")
        for axis in AXES:
            geometry, bore = screen["geometry"][axis], placement["bore_geometry"][axis]
            order = geometry["receiver_order"]
            require(order == [receiver["member"] for receiver in bore["receivers"]], "Receiver order mismatch")
            normal, head, datum = [vector(geometry[key]) for key in ("bolt_axis_xyz", "head_seat_point_mm", "datum_mm")]
            require(np.allclose(normal, bore["axis_xyz"], atol=1e-12, rtol=0), "Bore/shaft direction mismatch")
            datum_x = float(normal @ (datum - head))
            wood_start = geometry["receiver_intervals_from_underhead_mm"][order[0]][0]
            intervals, receiver_geometry = [], []
            for member, field in zip(order, bore["receivers"], strict=True):
                underhead = geometry["receiver_intervals_from_underhead_mm"][member]
                interval = [coordinate - wood_start for coordinate in underhead]
                require(interval[1] > interval[0], "Nonpositive receiver grip")
                for coordinate, point in zip(interval, (field["start_point_mm"], field["end_point_mm"]), strict=True):
                    require(np.linalg.norm(head + coordinate * normal - vector(point)) < 1e-8, "Grip/bore point mismatch")
                require(not intervals or abs(interval[0] - intervals[-1][1]) < 1e-8, "Noncontiguous three-receiver grip")
                require(abs(field["radial_clearance_mm"] - (field["bore_diameter_mm"] - bore["shaft_diameter_mm"]) / 2) < 1e-12, "Bore gap mismatch")
                intervals.append(interval)
                receiver_geometry.append({**field, "interval_from_head_wood_face_mm": interval, "interval_from_underhead_mm": underhead})
            length = intervals[-1][1]
            require(abs(length - geometry["modeled_wood_grip_mm"]) < 1e-8, "Grip length mismatch")
            require(np.linalg.norm(head + length * normal - vector(geometry["nut_seat_point_mm"])) < 1e-8, "Nut seat mismatch")
            geometries[axis] = {**geometry, "datum_x_from_head_wood_face_mm": datum_x, "shaft_diameter_mm": bore["shaft_diameter_mm"], "receivers": receiver_geometry}
            selected_rows = [i for i, row in enumerate(rows) if row["row_id"].startswith(axis + "/")]
            require(len(selected_rows) == 5, "Expected four lateral rows and one physical axial tie")
            for case in CASES:
                state_index, state = next((i, state) for i, state in enumerate(screen["bolt_cases"]) if (state["case_id"], state["axis_id"]) == (case, axis))
                require(len(state["planes"]) == 2, "Expected two lateral interfaces")
                expected_rows = [row for plane in state["planes"] for row in plane["raw_rows"]] + [state["tie_raw_row"]]
                require(sorted(selected_rows) == sorted(expected_rows), "Per-bolt row ownership mismatch")
                raw = response[case + "_gap_raw_force_n"]
                basis = vector(state["planes"][0]["directions_xyz"]).T
                require(np.allclose(basis.T @ basis, np.eye(2), atol=1e-12, rtol=0) and np.linalg.norm(basis.T @ normal) < 1e-12, "Lateral basis invalid")
                for plane_index, plane in enumerate(state["planes"]):
                    require(np.allclose(vector(plane["directions_xyz"]).T, basis, atol=1e-12, rtol=0), "Two-plane basis mismatch")
                    require([plane["first_body"], plane["second_body"]] == order[plane_index:plane_index + 2], "Plane receiver ownership mismatch")
                    require(np.linalg.norm(vector(plane["point_mm"]) - head - intervals[plane_index][1] * normal) < 1e-8, "Plane/interface point mismatch")
                    require(all(rows[i]["law"]["intended_law"] == "bilateral" for i in plane["raw_rows"]), "Source lateral law changed")
                    require(np.allclose(raw[plane["raw_rows"]], plane["signed_components_n"], atol=1e-9, rtol=0), "Saved plane forces mismatch")
                tie_index = state["tie_raw_row"]
                require(rows[tie_index]["law"]["intended_law"] == "tension_only", "Source physical tie law changed")
                require([rows[tie_index]["ownership"][key] for key in ("first_body", "second_body")] == [order[0], order[2]], "Physical tie end ownership mismatch")
                tension = float(raw[tie_index])
                require(abs(tension - state["outer_tie_signed_n"]) < 1e-9 and tension >= 0, "Positive source axial tie mismatch")
                recovered, errors = {}, {}
                for member_index, body in enumerate(order):
                    body_index = model["body_names"].index(body)
                    block = operator[np.ix_(selected_rows, np.arange(6 * body_index, 6 * body_index + 6))]
                    force = -block[:, :3].T @ raw[selected_rows]
                    moment = -1000 * block[:, 3:].T @ raw[selected_rows] + np.cross(body_datums[body] - datum, force)
                    saved = state["receiver_wrenches"][body]["total"]
                    force_error = float(np.max(np.abs(force - vector(saved["force_xyz_n"]))))
                    moment_error = float(np.max(np.abs(moment - vector(saved["moment_xyz_nmm"]))))
                    require(force_error < 1e-6 and moment_error < 1e-5, "D contains an unsaved per-receiver transfer couple")
                    expected_normal = tension * (1 if member_index == 0 else -1 if member_index == 2 else 0)
                    require(abs(normal @ force - expected_normal) < 1e-6 and abs(normal @ moment) < 1e-5, "Boundary needs unsupported middle axial force or shaft torsion")
                    recovered[body] = wrench(force, moment)
                    errors[body] = {"force_max_abs_n": force_error, "moment_max_abs_nmm": moment_error}
                    max_force_error, max_moment_error = max(max_force_error, force_error), max(max_moment_error, moment_error)
                net_force = sum((vector(value["force_xyz_n"]) for value in recovered.values()), np.zeros(3))
                net_moment = sum((vector(value["moment_xyz_nmm"]) for value in recovered.values()), np.zeros(3))
                require(np.max(np.abs(net_force)) < 1e-6 and np.max(np.abs(net_moment)) < 1e-5, "Per-bolt boundary fails reference equilibrium")
                bearing_index, bearing_state = next((i, item) for i, item in enumerate(bearing["states"]) if (item["case_id"], item["axis_id"]) == (case, axis))
                endpoint_indices = [i for i, item in enumerate(bearing["endpoint_fields"]) if (item["case_id"], item["axis_id"]) == (case, axis)]
                placement_indices = [i for i, item in enumerate(placement["records"]) if (item["case_id"], item["axis_id"]) == (case, axis)]
                require(len(endpoint_indices) == len(placement_indices) == 4, "Frozen witness join differs")
                boundaries.append({
                    "case_id": case, "axis_id": axis, "transverse_basis_xyz": basis.T.tolist(),
                    "physical_axial_tie_n": tension, "operator_connector_wrenches_on_receivers": recovered,
                    "saved_point_connector_wrenches_on_receivers": state["receiver_wrenches"],
                    "D_vs_saved_point_wrench_errors": errors, "net_connector_wrench": wrench(net_force, net_moment),
                    "source_rows": [{"raw_index": i, "signed_force_n": float(raw[i]), "identity": rows[i]} for i in selected_rows],
                    "planes": state["planes"], "screen_pointer": f"screen#/bolt_cases/{state_index}",
                    "frozen_bearing_pointer": f"bearing#/states/{bearing_index}", "frozen_affine_fields": bearing_state["members"],
                    "frozen_static_endpoint_pointers": [f"bearing#/endpoint_fields/{i}" for i in endpoint_indices],
                    "frozen_placement_witnesses": [{"pointer": f"placement#/records/{i}", **{key: placement["records"][i][key] for key in ("gap_scale", "motion_mode", "straight_shaft_placement_found", "minimum_conservative_margin_mm")}} for i in placement_indices],
                })
    return {
        "schema": "knee_three_receiver_first_order_contract/v1", "status": "prepared_not_mechanically_executed",
        "producer_sha256": sha(Path(__file__)), "source_receipts": receipts,
        "source_pin_scope": "Directly consumed frozen outputs and operators. Inherited STEP/source maps are retained provenance; geometry is not reconstructed.",
        "counts": {"physical_shafts": 4, "source_states": 24, "bearing_fields": 24, "static_endpoint_fields": 96, "placement_witnesses": 96},
        "geometry": geometries, "boundaries": boundaries, "selected": {"case_id": SELECTED[0], "axis_id": SELECTED[1], "selection_basis": "Existing same-state 92ksi convex screen peak; no new envelope or capacity."},
        "D_vs_saved_max_errors": {"force_n": max_force_error, "moment_nmm": max_moment_error},
        "model": {
            "wood_bore_and_seat_stiffness_mpa_per_mm": K_WOOD, "bolt_E_mpa": E_BOLT, "head_contact_stiffness_mpa_per_mm": K_HEAD,
            "elements_per_receiver": ELEMENTS_PER_RECEIVER, "beam_nodes": 25, "ungauged_transverse_variables": 112, "gauged_transverse_variables": 108,
            "bore_law": "Circular radial clearance, compression-only K20 projected-diameter line foundation; the two transverse components share each contact norm.",
            "axial_law": "One prescribed source tension. Both outer series contacts carry full T; middle receiver has no axial bore/contact load. Opening equals direct compression plus T*L/(E*A).",
            "end_profile": {"washer_ID_max_mm": 8.3058, "washer_OD_min_mm": 18.4658, "hypothetical_concentric_head_and_nut_flat_radius_mm": 5.0, "washer": "rigid, symmetric profile at both ends"},
            "omitted": ["T-dependent geometric stiffness", "geometric shortening", "preload", "friction", "washer bending", "thread/root and head-fillet mechanics", "shaft torsion", "whole-knee-group compatibility", "complete elastic timber qualification"],
            "gauge": "Middle receiver transverse translation and two tilts at the common shaft datum are zero. Common axial translation and middle axial pose are unconstrained by the isolated bolt.",
            "source_boundary": "External receiver drives are the negatives of current D per-bolt full wrenches at the common datum. No face contact, neighboring bolt, gravity, or whole-body wrench is added.",
            "numerical_tolerances": {"mixed_gradient_n": GRADIENT_TOL, "force_n": GRADIENT_TOL, "moment_nmm": geometries[SELECTED[1]]["modeled_wood_grip_mm"] * GRADIENT_TOL, "max_newton_iterations": 150},
        },
        "frame_law_changed": False, "placement_recomputed": False, "mechanics_executed": False,
        "complete_joint_acceptance": False, "actual_hardware_or_wood_acceptance": False, "physical_release": False,
    }


def load_contract(path):
    path = path.resolve()
    require(path.is_relative_to(RAW.resolve()), "Contract must remain in the owned raw directory")
    contract = read(path)
    require(contract["schema"] == "knee_three_receiver_first_order_contract/v1", "Wrong contract schema")
    require(contract["producer_sha256"] == sha(Path(__file__)), "Producer changed; prepare a fresh contract")
    require(contract["source_receipts"] == pins(), "Contract source receipts changed")
    selected = contract["selected"]
    require((selected["case_id"], selected["axis_id"]) == SELECTED, "Only the governing witness is executable")
    state = next(item for item in contract["boundaries"] if (item["case_id"], item["axis_id"]) == SELECTED)
    return contract, state, contract["geometry"][SELECTED[1]]


def pure_helper(length):
    # Reuse only the pinned definitions. Its pair assembly and main/sweeps are never called.
    specification = importlib.util.spec_from_file_location("knee_frozen_pure_contact", FROZEN["pure_helper"][0])
    module = importlib.util.module_from_spec(specification)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        specification.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    module.LENGTH = length  # Hermite slope variables use this model's grip scale.
    require(module.E_BOLT == E_BOLT and module.K_HEAD == K_HEAD, "Pure helper constants changed")
    return module


def assemble(geometry, helper):
    receivers = geometry["receivers"]
    intervals = [receiver["interval_from_head_wood_face_mm"] for receiver in receivers]
    length, diameter = intervals[-1][1], geometry["shaft_diameter_mm"]
    nodes = np.r_[np.linspace(*intervals[0], ELEMENTS_PER_RECEIVER + 1), *[np.linspace(*interval, ELEMENTS_PER_RECEIVER + 1)[1:] for interval in intervals[1:]]]
    scalar_size = 2 * len(nodes)
    size, rigidity = 2 * scalar_size + 12, E_BOLT * math.pi * diameter**4 / 64
    stiffness, samples, fields = np.zeros((size, size)), [], []
    gauss, weights = np.polynomial.legendre.leggauss(3)
    scale = np.diag([1, 1 / length, 1, 1 / length])
    for element, (left, right) in enumerate(pairwise(nodes)):
        span, receiver_index = right - left, element // ELEMENTS_PER_RECEIVER
        local = rigidity / span**3 * np.array([
            [12, 6 * span, -12, 6 * span], [6 * span, 4 * span**2, -6 * span, 2 * span**2],
            [-12, -6 * span, 12, -6 * span], [6 * span, 2 * span**2, -6 * span, 4 * span**2],
        ])
        indices = [np.arange(2 * element, 2 * element + 4) + component * scalar_size for component in range(2)]
        for index in indices:
            stiffness[np.ix_(index, index)] += scale @ local @ scale
        for coordinate, weight in zip((gauss + 1) / 2, weights * span / 2, strict=True):
            location = left + coordinate * span
            mapping = np.zeros((2, size))
            for component in range(2):
                mapping[component, indices[component]] = helper.hermite(coordinate, span)
                mapping[component, 2 * scalar_size + 4 * receiver_index + component] = -1
                mapping[component, 2 * scalar_size + 4 * receiver_index + 2 + component] = -(location - geometry["datum_x_from_head_wood_face_mm"]) / length
            samples.append({"map": mapping, "weight_mm": float(weight), "x_mm": float(location), "receiver_index": receiver_index, "gap_mm": receivers[receiver_index]["radial_clearance_mm"]})
        for coordinate in np.r_[0, (gauss + 1) / 2, 1]:
            fields.append((element, float(left + coordinate * span), indices, rigidity * helper.hermite(coordinate, span, 2), rigidity * helper.hermite(coordinate, span, 3)))
    ends = []
    for receiver_index, node_index in ((0, 0), (2, len(nodes) - 1)):
        mapping = np.zeros((2, size))
        for component in range(2):
            mapping[component, component * scalar_size + 2 * node_index + 1] = 1 / length
            mapping[component, 2 * scalar_size + 4 * receiver_index + 2 + component] = -1 / length
        ends.append(mapping)
    fixed = np.arange(2 * scalar_size + 4, 2 * scalar_size + 8)
    return {"K": stiffness, "samples": samples, "fields": fields, "ends": ends, "nodes": nodes, "scalar_size": scalar_size, "size": size, "free": np.setdiff1d(np.arange(size), fixed), "EI": rigidity, "length": length, "diameter": diameter}


def quads(helper, contract):
    profile = contract["model"]["end_profile"]
    inner = profile["washer_ID_max_mm"] / 2
    return [helper.annulus(inner, outer) for outer in (profile["hypothetical_concentric_head_and_nut_flat_radius_mm"], profile["washer_OD_min_mm"] / 2)]


def end_contact(helper, tension, relative, quadratures):
    tilt = float(np.linalg.norm(relative))
    unit = relative / tilt if tilt else np.array([1.0, 0.0])
    contact = helper.series_contact(tension, tilt, K_WOOD, *quadratures)
    moment, tangent = contact["moment_nmm"], contact["tangent_nmm_per_rad"]
    hessian = tangent * np.outer(unit, unit)
    if tilt:
        hessian += moment / tilt * (np.eye(2) - np.outer(unit, unit))
    else:
        hessian = tangent * np.eye(2)
    return contact, moment * unit, hessian, unit


def seat_tractions(contact, unit, end_index, quadratures, geometry, basis):
    """Integrate pressure at reference annulus points, independently of dual rows."""
    normal = vector(geometry["bolt_axis_xyz"])
    seat = vector(geometry["head_seat_point_mm"] if end_index == 0 else geometry["nut_seat_point_mm"])
    sign = 1 if end_index == 0 else -1
    angle = (np.arange(32) + 0.5) * 2 * math.pi / 32
    inner = 8.3058 / 2
    orientation = np.column_stack((unit, [-unit[1], unit[0]]))
    fields = {}
    for name, quadrature, stiffness in zip(("head_contact", "wood_contact"), quadratures, (K_HEAD, K_WOOD), strict=True):
        area, transverse, outer = quadrature
        radii = inner + (np.polynomial.legendre.leggauss(8)[0] + 1) * (outer - inner) / 2
        second = (radii[:, None] * np.sin(angle)).ravel()
        # Opposite normal directions require opposite pressure eccentricities.
        offsets = -sign * (basis @ orientation @ np.vstack((transverse, second))).T
        pressure = stiffness * np.maximum(contact[name]["closure_mm"] + contact[name]["tilt_rad"] * transverse, 0)
        force_on_wood = sign * (area * pressure)[:, None] * normal
        points = seat + offsets
        forces = force_on_wood if name == "wood_contact" else -force_on_wood
        total_force = np.sum(forces, axis=0)
        total_moment = np.sum(np.cross(points - vector(geometry["datum_mm"]), forces), axis=0)
        fields[name] = {
            "on": "receiver" if name == "wood_contact" else "bolt", "reference_points_mm": points.tolist(),
            "quadrature_area_mm2": area.tolist(), "pressure_mpa": pressure.tolist(), "point_forces_xyz_n": forces.tolist(),
            "integrated_wrench_about_common_datum": wrench(total_force, total_moment),
        }
    return fields


def drive_for(state, geometry, model):
    drive = np.zeros(model["size"])
    basis, normal = vector(state["transverse_basis_xyz"]).T, vector(geometry["bolt_axis_xyz"])
    for receiver_index, member in enumerate(geometry["receiver_order"]):
        source = state["operator_connector_wrenches_on_receivers"][member]
        offset = 2 * model["scalar_size"] + 4 * receiver_index
        drive[offset:offset + 2] = -basis.T @ vector(source["force_xyz_n"])
        drive[offset + 2:offset + 4] = -basis.T @ np.cross(vector(source["moment_xyz_nmm"]), normal) / model["length"]
    return drive


def evaluate(pose, model, helper, tension, quadratures, drive):
    energy = float(0.5 * pose @ model["K"] @ pose - drive @ pose)
    gradient, hessian = model["K"] @ pose - drive, model["K"].copy()
    bore, ends = [], []
    for sample in model["samples"]:
        mapping = sample["map"]
        relative = mapping @ pose
        radius = float(np.linalg.norm(relative))
        penetration = max(radius - sample["gap_mm"], 0)
        unit = relative / radius if radius else np.zeros(2)
        coefficient = K_WOOD * model["diameter"] * sample["weight_mm"]
        force_on_wood = coefficient * penetration * unit
        energy += 0.5 * coefficient * penetration**2
        gradient += mapping.T @ force_on_wood
        if penetration:
            tangent = coefficient * ((1 - sample["gap_mm"] / radius) * np.eye(2) + sample["gap_mm"] / radius * np.outer(unit, unit))
            hessian += mapping.T @ tangent @ mapping
        bore.append((relative, penetration, force_on_wood))
    baseline = helper.series_contact(tension, 0, K_WOOD, *quadratures)["energy_nmm"]
    for mapping in model["ends"]:
        contact, moment, tangent, unit = end_contact(helper, tension, mapping @ pose, quadratures)
        energy += contact["energy_nmm"] - baseline
        gradient += mapping.T @ moment
        hessian += mapping.T @ tangent @ mapping
        ends.append((contact, moment, unit))
    return energy, gradient, hessian, bore, ends


def coupon(contract, state, geometry):
    helper = pure_helper(geometry["modeled_wood_grip_mm"])
    model, records = assemble(geometry, helper), []
    length, scalar_size, nodes = model["length"], model["scalar_size"], model["nodes"]

    def compare(name, actual, expected, tolerance=1e-7):
        actual, expected = vector(actual), vector(expected)
        error = float(np.max(np.abs(actual - expected)))
        limit = tolerance * max(1, float(np.max(np.abs(expected))))
        records.append({"name": name, "actual": actual.tolist(), "expected": expected.tolist(), "max_abs_error": error, "tolerance": limit, "matched": error <= limit})

    curvature = 1e-5
    pose = np.zeros(model["size"])
    pose[:scalar_size:2] = curvature * nodes * (nodes - length) / 2
    pose[1:scalar_size:2] = length * curvature * (nodes - length / 2)
    compare("constant_curvature_elastic_energy_nmm", 0.5 * pose @ model["K"] @ pose, 0.5 * model["EI"] * curvature**2 * length)
    expected = np.zeros(model["size"])
    expected[1], expected[scalar_size - 1] = -model["EI"] * curvature / length, model["EI"] * curvature / length
    compare("constant_curvature_endpoint_scaled_moments", model["K"] @ pose, expected)
    recovered = [[moment_row @ pose[indices[0]], shear_row @ pose[indices[0]]] for _, _, indices, moment_row, shear_row in model["fields"]]
    compare("constant_curvature_EI_fields", recovered, [[model["EI"] * curvature, 0]] * len(recovered))
    normal, basis = vector(geometry["bolt_axis_xyz"]), vector(state["transverse_basis_xyz"]).T
    tension, quadratures = state["physical_axial_tie_n"], quads(helper, contract)
    indentation_pose = np.zeros(model["size"])
    indentation_pose[:scalar_size:2] = geometry["receivers"][0]["radial_clearance_mm"] + 0.01
    indentation = evaluate(indentation_pose, model, helper, tension, quadratures, np.zeros(model["size"]))
    q_line = K_WOOD * model["diameter"] * 0.01
    for receiver_index, member in enumerate(geometry["receiver_order"]):
        indices = [i for i, sample in enumerate(model["samples"]) if sample["receiver_index"] == receiver_index]
        samples = [model["samples"][i] for i in indices]
        start, end = geometry["receivers"][receiver_index]["interval_from_head_wood_face_mm"]
        forces = [basis @ indentation[3][i][2] for i in indices]
        points = [vector(geometry["head_seat_point_mm"]) + sample["x_mm"] * normal for sample in samples]
        compare(member + "/uniform_bore_force_n", np.sum(forces, axis=0), q_line * (end - start) * basis[:, 0])
        compare(member + "/uniform_bore_moment_nmm", np.sum([np.cross(point - vector(geometry["datum_mm"]), force) for point, force in zip(points, forces, strict=True)], axis=0), q_line * (end - start) * ((start + end) / 2 - geometry["datum_x_from_head_wood_face_mm"]) * np.cross(normal, basis[:, 0]))
    # A shared rigid line must have no bending, relative bore motion or end tilt.
    rigid = np.zeros(model["size"])
    translation, slope = np.array([0.13, -0.17]), np.array([0.001, -0.0007])
    for component in range(2):
        rigid[component * scalar_size:(component + 1) * scalar_size:2] = translation[component] + slope[component] * (nodes - geometry["datum_x_from_head_wood_face_mm"])
        rigid[component * scalar_size + 1:(component + 1) * scalar_size:2] = length * slope[component]
    for receiver_index in range(3):
        offset = 2 * scalar_size + 4 * receiver_index
        rigid[offset:offset + 2], rigid[offset + 2:offset + 4] = translation, length * slope
    compare("shared_rigid_line_beam_gradient", model["K"] @ rigid, np.zeros(model["size"]))
    compare("shared_rigid_line_bore_and_end_motion", [mapping @ rigid for mapping in [*[sample["map"] for sample in model["samples"]], *model["ends"]]], np.zeros((len(model["samples"]) + 2, 2)))
    end = helper.series_contact(tension, 0, K_WOOD, *quadratures)
    analytic_closure = tension / (K_HEAD * sum(quadratures[0][0])) + tension / (K_WOOD * sum(quadratures[1][0]))
    compare("zero_tilt_direct_compression_mm", end["total_closure_mm"], analytic_closure)
    compare("one_tie_two_full_T_ends_opening_mm", 2 * end["total_closure_mm"] + tension * length / (E_BOLT * math.pi * model["diameter"]**2 / 4), 2 * analytic_closure + tension * length / (E_BOLT * math.pi * model["diameter"]**2 / 4))
    relative = np.array([0.002, -0.001])
    contact, moment, _, unit = end_contact(helper, tension, relative, quadratures)
    for end_index, sign in ((0, 1), (1, -1)):
        fields = seat_tractions(contact, unit, end_index, quadratures, geometry, basis)
        for name, target_sign in (("wood_contact", 1), ("head_contact", -1)):
            integrated = fields[name]["integrated_wrench_about_common_datum"]
            compare(f"end{end_index}/{name}/normal_force_n", integrated["force_xyz_n"], target_sign * sign * tension * normal)
            compare(f"end{end_index}/{name}/reference_point_moment_nmm", integrated["moment_xyz_nmm"], target_sign * np.cross(normal, basis @ moment))
    force, moment = np.array([0, -11, 13]), np.array([0, 17, -19])
    translation, rotation = np.array([0, -0.2, 0.3]), np.array([0, -0.02, 0.03])
    compare("global_wrench_virtual_work_nmm", force @ translation + moment @ rotation, 5.19)
    compare("D_1000theta_virtual_work_nmm", force @ translation + (moment / 1000) @ (1000 * rotation), 5.19)
    scaled_tilt = length * basis.T @ np.cross(rotation, normal)
    compare("local_scaled_slope_virtual_work_nmm", (basis.T @ force) @ (basis.T @ translation) + (basis.T @ np.cross(moment, normal) / length) @ scaled_tilt, 5.19)
    return {"schema": "knee_first_order_engineering_coupon/v1", "status": "matched" if all(record["matched"] for record in records) else "STOP_coupon_mismatch", "arithmetic": records, "mechanics_executed": True, "software_tests_run": False, "complete_joint_acceptance": False, "physical_release": False}


def physical_recovery(pose, evaluation, model, helper, contract, state, geometry):
    """Recover each full wrench from bore and annular point tractions, not gradients."""
    normal, basis = vector(geometry["bolt_axis_xyz"]), vector(state["transverse_basis_xyz"]).T
    datum, head = vector(geometry["datum_mm"]), vector(geometry["head_seat_point_mm"])
    forces, moments, bore_fields = np.zeros((3, 3)), np.zeros((3, 3)), []
    for sample, (relative, penetration, components) in zip(model["samples"], evaluation[3], strict=True):
        receiver_index = sample["receiver_index"]
        force, point = basis @ components, head + sample["x_mm"] * normal
        forces[receiver_index] += force
        moments[receiver_index] += np.cross(point - datum, force)
        bore_fields.append({
            "receiver": geometry["receiver_order"][receiver_index], "x_mm": sample["x_mm"], "reference_point_mm": point.tolist(),
            "quadrature_weight_mm": sample["weight_mm"], "relative_transverse_motion_mm": relative.tolist(),
            "radial_penetration_mm": penetration, "pressure_mpa": K_WOOD * penetration,
            "force_on_wood_xyz_n": force.tolist(), "force_on_beam_xyz_n": (-force).tolist(),
        })
    end_fields, quadratures = [], quads(helper, contract)
    for end_index, (contact, _, unit) in enumerate(evaluation[4]):
        field = seat_tractions(contact, unit, end_index, quadratures, geometry, basis)
        receiver_index = 0 if end_index == 0 else 2
        recovered = field["wood_contact"]["integrated_wrench_about_common_datum"]
        forces[receiver_index] += vector(recovered["force_xyz_n"])
        moments[receiver_index] += vector(recovered["moment_xyz_nmm"])
        end_fields.append({"end": "head" if end_index == 0 else "nut", "receiver": geometry["receiver_order"][receiver_index], "series_contact": contact, "point_tractions": field})
    residuals, receiver_fields = [], []
    for receiver_index, member in enumerate(geometry["receiver_order"]):
        target = state["operator_connector_wrenches_on_receivers"][member]
        force_error, moment_error = forces[receiver_index] - vector(target["force_xyz_n"]), moments[receiver_index] - vector(target["moment_xyz_nmm"])
        offset = 2 * model["scalar_size"] + 4 * receiver_index
        local = pose[offset:offset + 4]
        receiver_fields.append({"receiver": member, "transverse_translation_at_datum_xyz_mm": (basis @ local[:2]).tolist(), "rotation_xyz_rad": np.cross(normal, basis @ (local[2:] / model["length"])).tolist(), "independently_recovered_connector_wrench": wrench(forces[receiver_index], moments[receiver_index]), "target_D_connector_wrench": target, "reference_equilibrium_residual": wrench(force_error, moment_error)})
        residuals.append((float(np.max(np.abs(force_error))), float(np.max(np.abs(moment_error)))))
    beam_fields = []
    for element, location, indices, moment_row, shear_row in model["fields"]:
        curvature = np.array([moment_row @ pose[index] for index in indices])
        third = np.array([shear_row @ pose[index] for index in indices])
        beam_fields.append({"element": element, "x_mm": location, "EI_curvature_components_nmm": curvature.tolist(), "EI_third_derivative_components_n": third.tolist(), "physical_bending_vector_xyz_nmm": np.cross(normal, basis @ curvature).tolist()})
    area = math.pi * model["diameter"]**2 / 4
    stretch = state["physical_axial_tie_n"] * model["length"] / (E_BOLT * area)
    opening = stretch + sum(end[0]["total_closure_mm"] for end in evaluation[4])
    return {
        "receivers": receiver_fields, "bore_fields": bore_fields, "outer_seat_fields": end_fields, "beam_fields": beam_fields,
        "beam_nodes": [{"x_mm": float(location), "transverse_displacement_mm": [float(pose[component * model["scalar_size"] + 2 * node]) for component in range(2)], "transverse_slope_rad": [float(pose[component * model["scalar_size"] + 2 * node + 1] / model["length"]) for component in range(2)]} for node, location in enumerate(model["nodes"])],
        "physical_recovery_max_residual": {"force_n": max(value[0] for value in residuals), "moment_nmm": max(value[1] for value in residuals)},
        "normal_transfer": {"single_physical_tie_n": state["physical_axial_tie_n"], "each_outer_stack_tension_n": state["physical_axial_tie_n"], "middle_axial_load_n": 0, "direct_bolt_stretch_mm": stretch, "required_outer_opening_mm": opening, "geometric_shortening_mm": 0, "outer_common_normal_translation": "undetermined", "middle_normal_pose": "undetermined", "frame_source_normal_pose_imposed": False},
    }


def run_witness(contract, state, geometry):
    helper = pure_helper(geometry["modeled_wood_grip_mm"])
    model, tension = assemble(geometry, helper), state["physical_axial_tie_n"]
    quadratures, drive = quads(helper, contract), drive_for(state, geometry, model)
    pose, free = np.zeros(model["size"]), model["free"]
    history, defect, converged = [], None, False
    for iteration in range(150):
        evaluation = evaluate(pose, model, helper, tension, quadratures, drive)
        energy, gradient, hessian = evaluation[:3]
        mixed = float(np.max(np.abs(gradient[free])))
        history.append({"iteration": iteration, "energy_nmm": energy, "max_free_mixed_gradient_n": mixed})
        if mixed <= GRADIENT_TOL:
            converged = True
            break
        values, vectors = np.linalg.eigh(hessian[np.ix_(free, free)])
        if values[0] < -1e-9 * max(1, values[-1]):
            defect = "Newton tangent is not numerically positive semidefinite"
            break
        positive = values > max(1, values[-1]) * 1e-12
        inverse = np.full(len(free), 1 / (K_WOOD * model["diameter"] * model["length"]))
        inverse[positive] = 1 / values[positive]
        step = -vectors @ (inverse * (vectors.T @ gradient[free]))
        slope = float(gradient[free] @ step)
        if slope >= 0:
            defect = "Newton step does not descend"
            break
        for backtrack in range(50):
            fraction = 0.5**backtrack
            candidate = pose.copy()
            candidate[free] += fraction * step
            if evaluate(candidate, model, helper, tension, quadratures, drive)[0] <= energy + 1e-4 * fraction * slope + 1e-12 * max(1, abs(energy)):
                pose = candidate
                break
        else:
            defect = "Armijo search stopped without a valid step"
            break
    evaluation = evaluate(pose, model, helper, tension, quadratures, drive)
    recovered = physical_recovery(pose, evaluation, model, helper, contract, state, geometry)
    residual = recovered["physical_recovery_max_residual"]
    all_gradient = float(np.max(np.abs(evaluation[1])))
    closed = converged and residual["force_n"] <= GRADIENT_TOL and residual["moment_nmm"] <= model["length"] * GRADIENT_TOL and all_gradient <= GRADIENT_TOL
    if not converged and defect is None:
        defect = "Local iteration budget exhausted; compatibility has not been established"
    if converged and not closed:
        defect = "Independent reference-geometry bore/seat traction recovery does not close all three receiver wrenches"
    return {
        "schema": "knee_three_receiver_first_order_witness/v1", "status": "conditional_first_order_equilibrium" if closed else "STOP_method_or_boundary_defect",
        "case_id": SELECTED[0], "axis_id": SELECTED[1], "wood_stiffness_mpa_per_mm": K_WOOD,
        "defect": defect, "newton_converged": converged, "independent_reference_equilibrium_closed": closed,
        "full_mixed_gradient_max_n": all_gradient, "accepted_iterate": pose.tolist(), "iteration_history": history,
        **recovered, "scope": contract["model"], "mechanics_executed": True, "mechanical_state_count": 1,
        "force_ready_for_whole_knee_group": False, "complete_joint_acceptance": False, "actual_hardware_or_wood_acceptance": False, "physical_release": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "coupon", "run"))
    parser.add_argument("--out", type=Path, required=True, help="Fresh child directory below rawlocal/knee-compatible")
    parser.add_argument("--input", type=Path, help="Prepared input-contract.json")
    parser.add_argument("--coupon", type=Path, help="Matching parent-executed coupon.json for run mode")
    args = parser.parse_args()
    output = args.out.resolve()
    require(output.is_relative_to(RAW.resolve()) and output != RAW.resolve(), "Output is outside assigned ownership")
    require(not output.exists(), "Output already exists; preserve it and use a fresh child directory")
    require(args.mode == "prepare" or args.input is not None, "Mechanical modes require --input")
    require(args.mode != "run" or args.coupon is not None, "Run requires the stipulated engineering coupon receipt")
    # Preparation performs hash/metadata joins and signed wrench arithmetic only.
    input_sha = None
    if args.mode == "prepare":
        result, name = prepare(), "input-contract.json"
    else:
        contract, state, geometry = load_contract(args.input)
        input_sha = sha(args.input)
        if args.mode == "coupon":
            result, name = coupon(contract, state, geometry), "coupon.json"
        else:
            require(args.coupon.resolve().is_relative_to(RAW.resolve()), "Coupon is outside assigned ownership")
            saved_coupon = read(args.coupon)
            require(saved_coupon["schema"] == "knee_first_order_engineering_coupon/v1" and saved_coupon["status"] == "matched", "Coupon arithmetic did not match")
            require(saved_coupon["input_contract_sha256"] == input_sha and saved_coupon["producer_sha256"] == sha(Path(__file__)), "Coupon belongs to different inputs or source")
            result, name = run_witness(contract, state, geometry), "witness.json"
            result["coupon_sha256"] = sha(args.coupon)
        result["input_contract_sha256"] = input_sha
        result["producer_sha256"] = sha(Path(__file__))
    output.mkdir(parents=True)
    (output / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    dump(output / name, result)
    receipt = {
        "schema": "knee_compatible_execution_receipt/v1", "mode": args.mode, "status": result["status"],
        "producer_sha256": sha(Path(__file__)), "source_receipts": result.get("source_receipts", contract["source_receipts"] if args.mode != "prepare" else {}),
        "input_contract_sha256": input_sha, "argv": sys.argv, "python": sys.version.split()[0], "numpy": np.__version__,
        "output_sha256": {name: sha(output / name), "executed-producer.py": sha(output / "executed-producer.py")},
        "mechanics_executed": args.mode != "prepare", "native_run": False, "frame_run": False, "CAD_run": False, "tests_run": False,
    }
    if args.mode != "prepare":
        import scipy

        receipt["scipy"] = scipy.__version__
    dump(output / "receipt.json", receipt)
    print(json.dumps({"status": result["status"], "result_path": label(output / name), "result_sha256": sha(output / name), "receipt_sha256": sha(output / "receipt.json"), "producer_sha256": sha(Path(__file__)), "mechanics_executed": args.mode != "prepare"}, sort_keys=True))
    return 0 if not result["status"].startswith("STOP") else 2


if __name__ == "__main__":
    raise SystemExit(main())
