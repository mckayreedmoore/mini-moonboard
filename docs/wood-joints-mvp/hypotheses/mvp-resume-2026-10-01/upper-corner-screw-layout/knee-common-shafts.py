"""Prepare shared receiver wrenches; parent-only build of two knee shafts per side.

Import is inert and uses only the standard library. prepare(output) authenticates
frozen sources and joins their signed rows without numerical execution. build(output)
runs a symmetric engineering reference first, then twelve bounded local equilibria.
It does not update the frame, qualify the four internal v ties, or adopt a proposal.
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import struct
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-common-shafts"
ADAPTER = HERE / "knee-bridge-continuous-shafts.py"
FRESH = HERE / "rawlocal/knee-bridge-continuous-shafts/attempt01/fresh-inputs.json"
COMMON = HERE / "rawlocal/knee-bridge-common-compatibility/attempt01/report.json"
RUNTIME = {"python": "3.12.3", "numpy": "2.5.2", "scipy": "1.18.1"}
ROTATION_SCALE = 1000.0
PINS = {
    ADAPTER: "c5e45ddc8c92094879fbfdaacb7ef66f3eb06b7843eb5728c25cbae32c259e27",
    FRESH: "19f292683521bbc4f4def787fffcaaf686a266631f87fc54a14d888b6920a28b",
    COMMON: "05741edf258ad5608d8db7414e7b2e52426ac01d6aa6e17c2bf1f06e79f28f7f",
    COMMON.with_name("receipt.json"): "500091d3e6d2054be4603e0a75293d072b289e12d6468189ef577f2409790833",
    HERE / "rawlocal/knee-compatible/coupon-attempt01/coupon.json":
        "c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd",
    HERE / "rawlocal/knee-compatible/coupon-attempt01/receipt.json":
        "515f38a54c30b961f8c9edbd9de0f49f73b8e52f6bd5f4eee71de01778240482",
    HERE / "rawlocal/knee-contact-entry/coupon-attempt01/coupon.json":
        "3301215eaef7b83ec4ac1d940615f44e2004e112029f1d3c64b99a6f8a84f3b1",
    HERE / "rawlocal/knee-contact-entry/coupon-attempt01/receipt.json":
        "d2d4fc452e237e706a9e0eec5835e617000c157dda3d2608152c8d355a25b8bf",
    ROOT / "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
}
FLAGS = {
    "global_frame_feedback": False,
    "saved_global_pose_or_port_motion_replaced": False,
    "isolated_states_fitted_or_used_as_initial_iterates": False,
    "internal_v_ties_passive_field_qualified": False,
    "elastic_timber_field_qualified": False,
    "hardware_capacity_qualified": False,
    "complete_joint_acceptance": False,
    "proposal_adopted": False,
    "physical_release": False,
    "physical_failure_claimed": False,
    "stiffness_load_or_geometry_tuned": False,
    "native_or_CAD_execution": False,
    "software_tests_or_reviews_run": False,
}


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


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def subtract(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def scale(a, factor):
    return [factor * x for x in a]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def cross(a, b):
    return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]


def header(stream):
    prefix = stream.read(8)
    require(prefix[:6] == b"\x93NUMPY" and prefix[6] in (1, 2, 3), "unsupported NPY header")
    length = int.from_bytes(stream.read(2 if prefix[6] == 1 else 4), "little")
    require(0 < length < 10000, "invalid NPY header size")
    value = ast.literal_eval(stream.read(length).decode("utf-8"))
    require(value["descr"] == "<f8" and value["fortran_order"] is False, "array representation changed")
    return value["shape"]


def f64_rows(path, key, shape, indices=None):
    """Read only the required frozen rows using ZIP/struct, without NumPy."""
    with zipfile.ZipFile(path) as archive, archive.open(key + ".npy") as stream:
        require(header(stream) == shape, "array shape changed: " + key)
        if indices is None:
            count = math.prod(shape)
            payload = stream.read(8 * count)
            require(len(payload) == 8 * count and stream.read(1) == b"", "array payload changed")
            return list(struct.unpack("<" + str(count) + "d", payload))
        data_start, width, result = stream.tell(), shape[1], {}
        for index in sorted(indices):
            stream.seek(data_start + 8 * width * index)
            payload = stream.read(8 * width)
            require(len(payload) == 8 * width, "truncated operator row")
            result[index] = list(struct.unpack("<" + str(width) + "d", payload))
        return result


def retained():
    require(sha(ADAPTER) == PINS[ADAPTER], "retained adapter changed")
    spec = importlib.util.spec_from_file_location("knee_common_retained", ADAPTER)
    require(spec is not None and spec.loader is not None, "retained API unavailable")
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def sources(adapter, pins):
    """Authenticate receipts and rejoin point/D wrenches from the fresh response."""
    adapter.authenticate(pins)
    original, _, _, _, selected, identities = adapter.sources(pins)
    adapter.bind(pins, adapter.REUSE / "receipt.json", adapter.REUSE_RECEIPT_SHA256)
    adapter.authenticate(pins)
    receipt = read(adapter.REUSE / "receipt.json")
    require(receipt["all24_nominal_completed"] is True
            and receipt["source_unchanged_before_and_after_execution"] is True
            and receipt["output_sha256"][FRESH.name] == PINS[FRESH], "fresh input receipt differs")
    for name, digest in receipt["output_sha256"].items():
        path = (adapter.REUSE / name).resolve()
        require(path.parent == adapter.REUSE, "receipt output leaves frozen attempt")
        adapter.bind(pins, path, digest)
    for relative, digest in receipt["source_sha256"].items():
        path = adapter.REUSE / "producer.py.snapshot" if relative == ADAPTER.relative_to(ROOT).as_posix() else ROOT / relative
        adapter.bind(pins, path, digest)
    adapter.authenticate(pins)
    contract = read(FRESH)
    require(contract["geometry"] == original["geometry"] and contract["model"] == original["model"]
            and contract["fresh_load_sources"] == {p.relative_to(ROOT).as_posix(): adapter.PINS[p]
                for p in (adapter.ASSESSMENT, adapter.COMPARISON, adapter.RESPONSE,
                          adapter.SUMMARY, adapter.EXPORT_RECEIPT, adapter.DEMANDS)}
            and [(s["case_id"], s["axis_id"]) for s in contract["boundaries"]]
            == [(case, axis) for axis in adapter.AXES for case in adapter.CASES], "fresh contract join differs")
    common, common_receipt = read(COMMON), read(COMMON.with_name("receipt.json"))
    require(common_receipt["output_sha256"][COMMON.name] == PINS[COMMON]
            and common["sources_unchanged_before_and_after"]
            and len(common["cases"]) == 6 and all(c["finite_common_pose_conflict"] for c in common["cases"]),
            "recorded common-pose conflict differs")
    for folder in ("knee-compatible", "knee-contact-entry"):
        directory = HERE / "rawlocal" / folder / "coupon-attempt01"
        coupon, proof = read(directory / "coupon.json"), read(directory / "receipt.json")
        require(coupon["status"] == "matched"
                and proof["output_sha256"]["coupon.json"] == pins[directory / "coupon.json"],
                "retained engineering reference does not match")
    model, rows = (read(adapter.GRAVITY / name) for name in ("model.json", "row-identities.json"))
    require(len(model["body_names"]) == 50 and len(rows) == 1888
            and [r["row"] for r in rows] == list(range(1888)), "fresh body/row layout differs")
    datums = {body: [sum(model["physical_node_coordinates_mm"][str(n)][c] for n in set(nodes)) / len(set(nodes))
                     for c in range(3)] for body, nodes in model["body_nodes"].items()}
    selected_indices = {i for axis in adapter.AXES for i in
                        [identities[axis]["tie_row"], *(r for p in identities[axis]["interfaces"] for r in p["component_rows"])]}
    require(len(selected_indices) == 20, "four shaft rows differ")
    D = f64_rows(adapter.GRAVITY / "operators.npz", "D", (1888, 300), selected_indices)
    raw = {case: f64_rows(adapter.RESPONSE, case + "_gap_raw_force_n", (1888,)) for case in adapter.CASES}
    require(all(math.isfinite(v) for values in raw.values() for v in values)
            and all(math.isfinite(v) for values in D.values() for v in values), "nonfinite frozen source")
    maximum_force_error, maximum_moment_error = 0.0, 0.0
    for state in contract["boundaries"]:
        case, axis = state["case_id"], state["axis_id"]
        geometry, ids, exported = contract["geometry"][axis], identities[axis], selected[case, axis]
        require(geometry["shaft_diameter_mm"] == 6.35 and abs(geometry["modeled_wood_grip_mm"] - 215.9) < 1e-8
                and all(r["bore_diameter_mm"] == 7.5 and abs(r["radial_clearance_mm"] - 0.575) < 1e-12
                        for r in geometry["receivers"]), "retained shaft geometry changed")
        indices = {ids["tie_row"], *(i for plane in ids["interfaces"] for i in plane["component_rows"])}
        require(indices == {r["raw_index"] for r in state["source_rows"]}
                and all(r["identity"] == rows[r["raw_index"]] and r["signed_force_n"] == raw[case][r["raw_index"]]
                        for r in state["source_rows"])
                and state["physical_axial_tie_n"] == exported["signed_axial_n"] == raw[case][ids["tie_row"]],
                "fresh signed raw force/identity join differs")
        for plane, allocation in zip(ids["interfaces"], exported["interfaces"], strict=True):
            require(all(plane[k] == allocation[k] for k in ("plane_id", "component_rows", "component_directions_xyz"))
                    and allocation["components_n"] == [raw[case][i] for i in plane["component_rows"]],
                    "signed exported plane differs")
        for member in geometry["receiver_order"]:
            force, moment = [0.0]*3, [0.0]*3
            for index in indices:
                owner = rows[index]["ownership"]
                sign = 1 if owner["first_body"] == member else -1 if owner["second_body"] == member else 0
                point_force = scale(owner["direction_global_xyz"], sign * raw[case][index])
                force = add(force, point_force)
                moment = add(moment, cross(subtract(owner["point_mm"], geometry["datum_mm"]), point_force))
            offset = 6 * model["body_names"].index(member)
            operator_force = [-sum(D[i][offset+c] * raw[case][i] for i in indices) for c in range(3)]
            operator_moment = add([-1000 * sum(D[i][offset+3+c] * raw[case][i] for i in indices) for c in range(3)],
                                  cross(subtract(datums[member], geometry["datum_mm"]), operator_force))
            target = state["operator_connector_wrenches_on_receivers"][member]
            fe = max(abs(v) for v in [*subtract(force, target["force_xyz_n"]), *subtract(operator_force, target["force_xyz_n"])])
            me = max(abs(v) for v in [*subtract(moment, target["moment_xyz_nmm"]), *subtract(operator_moment, target["moment_xyz_nmm"])])
            require(fe <= 1e-6 and me <= 1e-5, "fresh full signed D/point wrench does not close")
            maximum_force_error, maximum_moment_error = max(maximum_force_error, fe), max(maximum_moment_error, me)
    packets = []
    for side in ("left", "right"):
        axes = [axis for axis in adapter.AXES if "_" + side + "_" in axis]
        geometries = [contract["geometry"][axis] for axis in axes]
        origin = scale(add(*(g["datum_mm"] for g in geometries)), 0.5)
        require(geometries[0]["receiver_order"] == geometries[1]["receiver_order"], "shaft receivers differ")
        for case in adapter.CASES:
            states = [next(s for s in contract["boundaries"] if s["case_id"] == case and s["axis_id"] == axis) for axis in axes]
            targets = {}
            for member in geometries[0]["receiver_order"]:
                force, moment = [0.0]*3, [0.0]*3
                for geometry, state in zip(geometries, states, strict=True):
                    value = state["operator_connector_wrenches_on_receivers"][member]
                    force = add(force, value["force_xyz_n"])
                    moment = add(moment, add(value["moment_xyz_nmm"], cross(subtract(geometry["datum_mm"], origin), value["force_xyz_n"])))
                targets[member] = {"force_xyz_n": force, "moment_xyz_nmm": moment}
            require(max(abs(sum(t[k][i] for t in targets.values())) for k in ("force_xyz_n", "moment_xyz_nmm") for i in range(3)) < 1e-5,
                    "combined receiver wrenches do not balance")
            packets.append({"case_id": case, "side": side, "axes": axes, "origin_mm": origin,
                            "states": states, "target_combined_receiver_wrenches": targets})
    adapter.authenticate(pins)
    return {"contract": contract, "packets": packets, "fresh_D_point_join_max_errors":
            {"force_n": maximum_force_error, "moment_nmm": maximum_moment_error},
            "preceding_fit_residuals_scaled_mm": [c["fit"]["minimum_maximum_residual_mm"] for c in common["cases"]]}


def point_row(np, size, offset, origin, point, direction):
    row = np.zeros(size)
    row[offset:offset+3] = direction
    row[offset+3:offset+6] = np.cross(np.asarray(point) - origin, direction) / ROTATION_SCALE
    return row


def assemble(np, core, contract, packet):
    geometries = [contract["geometry"][axis] for axis in packet["axes"]]
    models = [core.assemble(g, core.pure_helper(g["modeled_wood_grip_mm"])) for g in geometries]
    beam_size = 2 * models[0]["scalar_size"]
    size, receiver_start = 2 * beam_size + 18, 2 * beam_size
    require(beam_size == 100 and size == 218, "retained beam layout differs")
    names, origin = geometries[0]["receiver_order"], np.asarray(packet["origin_mm"])
    shafts, samples = [], []
    for index, (geometry, local, state) in enumerate(zip(geometries, models, packet["states"], strict=True)):
        basis, normal = np.asarray(state["transverse_basis_xyz"]), np.asarray(geometry["bolt_axis_xyz"])
        require(np.max(abs(basis @ basis.T - np.eye(2))) <= 1e-12 and np.max(abs(basis @ normal)) <= 1e-12
                and abs(abs(normal[0]) - 1) <= 1e-12 and np.max(abs(normal[1:])) <= 1e-12,
                "parallel transverse shaft basis differs")
        mapping = np.zeros((local["size"], size))
        mapping[:beam_size, index*beam_size:(index+1)*beam_size] = np.eye(beam_size)
        for receiver in range(3):
            offset = receiver_start + 6 * receiver
            for component, direction in enumerate(basis):
                mapping[beam_size+4*receiver+component] = point_row(np, size, offset, origin, geometry["datum_mm"], direction)
                mapping[beam_size+4*receiver+2+component, offset+3:offset+6] = local["length"] * np.cross(normal, direction) / ROTATION_SCALE
        opening = (point_row(np, size, receiver_start+12, origin, geometry["nut_seat_point_mm"], normal)
                   - point_row(np, size, receiver_start, origin, geometry["head_seat_point_mm"], normal))
        helper = core.pure_helper(local["length"])
        quadratures = core.quads(helper, contract)
        # These are the retained rotating annulus quadrature supports, not OD reserves.
        edge_radius = float(np.max(abs(quadratures[0][1])))
        require(edge_radius < float(np.max(abs(quadratures[1][1]))), "unloaded series seat support order differs")
        shaft = {"geometry": geometry, "state": state, "model": local, "map": mapping,
                 "opening": opening, "helper": helper, "quadratures": quadratures,
                 "end_maps": [end @ mapping for end in local["ends"]], "edge_radius": edge_radius,
                 "steel_compliance": local["length"] / (200000 * math.pi * local["diameter"]**2 / 4)}
        shafts.append(shaft)
        samples.extend({**sample, "map": sample["map"] @ mapping} for sample in local["samples"])
    drive = np.zeros(size)
    for receiver, member in enumerate(names):
        target = packet["target_combined_receiver_wrenches"][member]
        drive[receiver_start+6*receiver:receiver_start+6*receiver+6] = -np.r_[target["force_xyz_n"], np.asarray(target["moment_xyz_nmm"]) / ROTATION_SCALE]
    # Six common rigid modes use the base as reference. The additional mode moves
    # both outer receivers together along the shafts relative to the base.
    unloaded = np.zeros(size)
    unloaded[receiver_start] = unloaded[receiver_start+12] = 1
    require(all(np.max(abs(s["map"] @ unloaded)) <= 1e-12 and abs(s["opening"] @ unloaded) <= 1e-12 for s in shafts)
            and abs(drive @ unloaded) <= 1e-6, "purported axial float is loaded or kinematically supported")
    fixed = [*range(receiver_start+6, receiver_start+12), receiver_start]
    tolerance = min(1e-6, 215.9e-6 / ROTATION_SCALE)
    return {"size": size, "free": np.setdiff1d(np.arange(size), fixed), "shafts": shafts,
            "samples": samples, "drive": drive, "names": names, "origin": origin,
            "receiver_start": receiver_start, "tolerance": tolerance,
            "gauge": {"base_pose_coordinates": 6, "outer_axial_float_coordinates": 1,
                      "axial_float_virtual_work_n": float(drive @ unloaded),
                      "axial_float_vector": unloaded.tolist(), "fixed_indices": fixed}}


def compliance(np, contact, quadratures):
    """Exact active-set derivatives of the retained series-contact dual potential."""
    parts = []
    for name, stiffness, (area, transverse, _) in zip(("head_contact", "wood_contact"), (10000.0, 20.0), quadratures, strict=True):
        field = contact[name]
        active = field["closure_mm"] + field["tilt_rad"] * transverse > 0
        s0 = float(np.sum(area[active]))
        require(s0 > 0, "positive tension has no annular contact area")
        mean = float(np.sum(area[active] * transverse[active])) / s0
        tangent = stiffness * float(np.sum(area[active] * (transverse[active] - mean)**2))
        parts.append((1 / (stiffness*s0), mean, tangent))
    ch, mh, dh = parts[0]
    cw, mw, dw = parts[1]
    require(dh + dw > 0, "series tilt balance has no unique positive-tension tangent")
    return ch + cw + (mh-mw)**2 / (dh+dw), (mh*dw + mw*dh) / (dh+dw)


def seat_envelope(np, shaft, pose):
    return float(shaft["opening"] @ pose) + shaft["edge_radius"] * sum(float(np.linalg.norm(m @ pose)) for m in shaft["end_maps"])


def transfer(np, brentq, core, shaft, pose):
    """Eliminate T >= 0 by the common-opening stationarity/complementarity law."""
    opening = float(shaft["opening"] @ pose)
    tilts = [float(np.linalg.norm(m @ pose)) for m in shaft["end_maps"]]
    envelope = opening + shaft["edge_radius"] * sum(tilts)
    helper, quads = shaft["helper"], shaft["quadratures"]
    if envelope <= 0:
        tension = 0.0
    else:
        def residual(tension):
            if tension == 0:
                return -envelope
            return (shaft["steel_compliance"] * tension - opening
                    + sum(helper.series_contact(tension, tilt, 20.0, *quads)["total_closure_mm"] for tilt in tilts))
        upper = 1.0
        for _ in range(60):
            if residual(upper) >= 0:
                break
            upper *= 2
        else:
            raise ValueError("STOP: monotone axial contact root was not bracketed")
        tension = float(brentq(residual, 0, upper, xtol=1e-12, rtol=1e-14))
        require(tension > 0, "positive seat envelope returned an unloaded root")
    local_pose = shaft["map"] @ pose
    evaluation = core.evaluate(local_pose, shaft["model"], helper, tension, quads, np.zeros(shaft["model"]["size"]))
    if tension == 0:
        # The retained T=0 shortcut gives closure=0 even at nonzero tilt. That
        # dual-energy placeholder must not be integrated as positive pressure.
        # Choose an admissible zero-pressure witness; its slack partition is
        # arbitrary and supplies neither stiffness nor a physical constraint.
        ends = copy.deepcopy(evaluation[4])
        for contact, _, _ in ends:
            contact["head_contact"]["closure_mm"] = -shaft["edge_radius"] * contact["head_contact"]["tilt_rad"] - max(-envelope, 0)/2
            contact["total_closure_mm"] = contact["head_contact"]["closure_mm"]
            contact["unloaded_closure_witness_is_unique"] = False
        evaluation = (*evaluation[:4], ends)
    energy = (evaluation[0] + 2 * helper.series_contact(tension, 0, 20.0, *quads)["energy_nmm"]
              + tension * opening - 0.5 * shaft["steel_compliance"] * tension**2)
    gradient = shaft["map"].T @ evaluation[1] + tension * shaft["opening"]
    hessian = shaft["map"].T @ evaluation[2] @ shaft["map"]
    if tension > 0:
        denominator, mixed = shaft["steel_compliance"], shaft["opening"].copy()
        for (contact, _, unit), mapping in zip(evaluation[4], shaft["end_maps"], strict=True):
            ct, mt = compliance(np, contact, quads)
            denominator += ct
            mixed += mt * (unit @ mapping)
        hessian += np.outer(mixed, mixed) / denominator
        axial_residual = opening - shaft["steel_compliance"] * tension - sum(end[0]["total_closure_mm"] for end in evaluation[4])
        require(abs(axial_residual) <= 1e-8, "positive-tension opening stationarity did not close")
    elif opening == 0 and all(tilt == 0 for tilt in tilts):
        # At the exact zero-load origin choose the active-side generalized tangent
        # of max(opening, 0)^2/(2*C). This adds no force, energy or constraint.
        denominator = shaft["steel_compliance"] + 2 * sum(1 / (k*float(np.sum(q[0]))) for k, q in zip((10000.0, 20.0), quads, strict=True))
        hessian += np.outer(shaft["opening"], shaft["opening"]) / denominator
        axial_residual = None
    else:
        axial_residual = None
    return energy, gradient, hessian, {"tension_n": tension, "local_pose": local_pose,
        "evaluation": evaluation, "opening_mm": opening, "axial_stationarity_residual_mm": axial_residual,
        "unloaded_slack_mm": max(-envelope, 0), "unloaded_seat_closures_unique": tension > 0}


def solve_one(np, brentq, adapter, core, entry, contract, packet):
    model = assemble(np, core, contract, packet)

    def evaluate(pose):
        energy, gradient, hessian = -float(model["drive"] @ pose), -model["drive"].copy(), np.zeros((model["size"], model["size"]))
        fields = []
        for shaft in model["shafts"]:
            e, g, h, field = transfer(np, brentq, core, shaft, pose)
            energy, gradient, hessian = energy+e, gradient+g, hessian+h
            fields.append(field)
        return energy, gradient, hessian, fields

    def forward(pose, direction, samples):
        events = []
        try:
            events.append(entry.entry_step(pose, direction, samples))
        except ValueError as error:
            require("no forward unused bore support" in str(error), str(error))
            # Annular entry may support this loaded neutral direction.
        for shaft in model["shafts"]:
            speed = abs(float(shaft["opening"] @ direction)) + shaft["edge_radius"] * sum(float(np.linalg.norm(m @ direction)) for m in shaft["end_maps"])
            asymptotic = float(shaft["opening"] @ direction) + shaft["edge_radius"] * sum(float(np.linalg.norm(m @ direction)) for m in shaft["end_maps"])
            if seat_envelope(np, shaft, pose) > 0 or asymptotic <= 0 or speed <= 1e-28:
                continue
            def boundary(distance, shaft=shaft):
                return seat_envelope(np, shaft, pose + distance*direction)
            lower = 0.0
            if boundary(0) == 0 and boundary(1e-6/speed) < 0:
                lower = 1e-6/speed  # A boundary ray can first move into the slack set.
            upper = max(1.0, 2*lower)
            for _ in range(60):
                if boundary(upper) > 0:
                    break
                upper *= 2
            else:
                raise ValueError("STOP: annular contact-entry ray could not be bracketed")
            distance = float(brentq(boundary, lower, upper, xtol=1e-12, rtol=1e-14))
            events.append((distance + max(1e-4*distance, 1e-6/speed), distance))
        require(events, "loaded neutral direction has no bore or annular support; no reserve is supplied")
        return min(events)

    solver = adapter.pure_functions(adapter.ENTRY, ("solve",),
        {"np": np, "math": math, "require": require, "entry_step": forward}).solve
    pose, history, defect, converged = solver(evaluate, model, model["tolerance"])
    evaluation = evaluate(pose)
    combined = {member: {"force_xyz_n": np.zeros(3), "moment_xyz_nmm": np.zeros(3)} for member in model["names"]}
    shaft_results = []
    for shaft, field in zip(model["shafts"], evaluation[3], strict=True):
        state = {**shaft["state"], "physical_axial_tie_n": field["tension_n"]}
        recovered = core.physical_recovery(field["local_pose"], field["evaluation"], shaft["model"], shaft["helper"], contract, state, shaft["geometry"])
        for receiver in recovered["receivers"]:
            value = receiver["independently_recovered_connector_wrench"]
            force, moment = np.asarray(value["force_xyz_n"]), np.asarray(value["moment_xyz_nmm"])
            combined[receiver["receiver"]]["force_xyz_n"] += force
            combined[receiver["receiver"]]["moment_xyz_nmm"] += moment + np.cross(np.asarray(shaft["geometry"]["datum_mm"]) - model["origin"], force)
            receiver["original_isolated_source_wrench"] = receiver.pop("target_D_connector_wrench")
            receiver["redistribution_from_original_source"] = receiver.pop("reference_equilibrium_residual")
        recovered.pop("physical_recovery_max_residual")
        normal = recovered["normal_transfer"]
        normal["common_pose_outer_opening_mm"] = field["opening_mm"]
        normal["axial_stationarity_residual_mm"] = field["axial_stationarity_residual_mm"]
        normal["unloaded_slack_mm"] = field["unloaded_slack_mm"]
        normal["unloaded_seat_closures_unique"] = field["unloaded_seat_closures_unique"]
        normal["outer_common_normal_translation"] = "Unloaded axial float; spine x=0 is its coordinate representative."
        normal["middle_normal_pose"] = "Base pose is the common rigid reference; no axial bore stiffness is supplied."
        if field["tension_n"] == 0:
            normal["required_outer_opening_mm"] = None
            normal["unloaded_closure_limit"] = "Opening + r_edge*(|tilt_head|+|tilt_nut|) <= 0; separate closures are undetermined."
        shaft_results.append({"axis_id": state["axis_id"], "source_tension_n": shaft["state"]["physical_axial_tie_n"],
                              "redistributed_tension_n": field["tension_n"], **recovered})
    records, maximum_force, maximum_moment = [], 0.0, 0.0
    for member, value in combined.items():
        target = packet["target_combined_receiver_wrenches"][member]
        residual = {key: (vector - np.asarray(target[key])).tolist() for key, vector in value.items()}
        maximum_force = max(maximum_force, max(abs(v) for v in residual["force_xyz_n"]))
        maximum_moment = max(maximum_moment, max(abs(v) for v in residual["moment_xyz_nmm"]))
        records.append({"receiver": member, "datum_mm": model["origin"].tolist(),
                        "target": target, "recovered": {k: v.tolist() for k, v in value.items()}, "residual": residual})
    full_gradient = float(np.max(abs(evaluation[1])))
    closed = (converged and full_gradient <= model["tolerance"]
              and maximum_force <= 1e-6 and maximum_moment <= 215.9e-6)
    if converged and not closed:
        defect = "common receiver full traction wrenches or removed-mode reactions do not close"
    receiver_pose = pose[model["receiver_start"]:].reshape(3, 6)
    return {"schema": "knee_common_two_shafts_state/v1", "case_id": packet["case_id"], "side": packet["side"],
            "status": "CONDITIONAL_COMMON_RECEIVER_EQUILIBRIUM" if closed else "STOP_COUPLED_EQUILIBRIUM",
            "defect": defect, "newton_converged": converged, "combined_full_wrenches_closed": closed,
            "reference_origin_mm": model["origin"].tolist(), "receiver_order": model["names"],
            "receiver_poses_t_1000theta": receiver_pose.tolist(), "accepted_iterate": pose.tolist(),
            "coordinate_count": model["size"], "free_coordinate_count": len(model["free"]), "gauges": model["gauge"],
            "iteration_history": history, "full_mixed_gradient_max_n": full_gradient,
            "mixed_gradient_tolerance_n": model["tolerance"],
            "combined_traction_recovery_max_residual": {"force_n": maximum_force, "moment_nmm": maximum_moment},
            "combined_receiver_wrenches": records, "shafts": shaft_results, **FLAGS}


def known_answer(np, brentq, adapter, core, entry, packet):
    """Two translated identical shafts under centered pure axial demand, first."""
    contract = copy.deepcopy(packet["contract"])
    source = packet["packets"][0]
    original = contract["geometry"][source["axes"][0]]
    basis = np.asarray(source["states"][0]["transverse_basis_xyz"])
    normal, origin = np.asarray(original["bolt_axis_xyz"]), np.asarray(original["datum_mm"])
    geometries, states, axes = {}, [], []
    for index, sign in enumerate((-1, 1)):
        geometry = copy.deepcopy(original)
        shift = sign * 30 * basis[0]
        for key in ("datum_mm", "head_seat_point_mm", "nut_seat_point_mm"):
            geometry[key] = (np.asarray(geometry[key]) + shift).tolist()
        for receiver in geometry["receivers"]:
            for key in ("start_point_mm", "end_point_mm"):
                receiver[key] = (np.asarray(receiver[key]) + shift).tolist()
        axis = "reference_identical_" + str(index+1)
        axes.append(axis)
        geometries[axis] = geometry
        states.append({**copy.deepcopy(source["states"][0]), "axis_id": axis, "physical_axial_tie_n": 100.0,
                       "operator_connector_wrenches_on_receivers": {
                           member: {"force_xyz_n": ((1 if i == 0 else -1 if i == 2 else 0)*100*normal).tolist(),
                                    "moment_xyz_nmm": [0.0]*3}
                           for i, member in enumerate(original["receiver_order"])}})
    contract["geometry"] = geometries
    names = original["receiver_order"]
    targets = {member: {"force_xyz_n": ((1 if i == 0 else -1 if i == 2 else 0)*200*normal).tolist(),
                        "moment_xyz_nmm": [0.0]*3} for i, member in enumerate(names)}
    reference = {"case_id": "symmetric_known_answer", "side": "reference", "axes": axes,
                 "origin_mm": origin.tolist(), "states": states, "target_combined_receiver_wrenches": targets}
    result = solve_one(np, brentq, adapter, core, entry, contract, reference)
    helper, local = core.pure_helper(215.9), core.assemble(original, core.pure_helper(215.9))
    quadratures = core.quads(helper, contract)
    expected_opening = 100*(215.9/(200000*math.pi*6.35**2/4)
                            + 2*sum(1/(k*float(np.sum(q[0]))) for k, q in zip((10000.0, 20.0), quadratures, strict=True)))
    report_datum = origin + 20*basis[1]
    references, shaft_references = [], []
    for record in result["combined_receiver_wrenches"]:
        expected_force = np.asarray(targets[record["receiver"]]["force_xyz_n"])
        expected_moment = np.cross(origin-report_datum, expected_force)
        force, moment = np.asarray(record["recovered"]["force_xyz_n"]), np.asarray(record["recovered"]["moment_xyz_nmm"])
        returned_moment = moment + np.cross(origin-report_datum, force)
        references.append({"receiver": record["receiver"], "datum_mm": report_datum.tolist(),
                           "expected_force_xyz_n": expected_force.tolist(), "expected_moment_xyz_nmm": expected_moment.tolist(),
                           "force_error_n": float(np.max(abs(force-expected_force))),
                           "moment_error_nmm": float(np.max(abs(returned_moment-expected_moment)))})
    for shaft in result["shafts"]:
        datum = np.asarray(geometries[shaft["axis_id"]]["datum_mm"])
        for index, record in enumerate(shaft["receivers"]):
            expected_force = (1 if index == 0 else -1 if index == 2 else 0)*100*normal
            expected_moment = np.cross(datum-report_datum, expected_force)
            value = record["independently_recovered_connector_wrench"]
            force, moment = np.asarray(value["force_xyz_n"]), np.asarray(value["moment_xyz_nmm"])
            shaft_references.append({"axis_id": shaft["axis_id"], "receiver": record["receiver"],
                "datum_mm": report_datum.tolist(), "expected_force_xyz_n": expected_force.tolist(),
                "expected_moment_xyz_nmm": expected_moment.tolist(),
                "force_error_n": float(np.max(abs(force-expected_force))),
                "moment_error_nmm": float(np.max(abs(moment+np.cross(datum-report_datum, force)-expected_moment)))})
    matched = (result["combined_full_wrenches_closed"] and local["size"] == 112
               and all(abs(s["redistributed_tension_n"]-100) <= 1e-6
                       and abs(s["normal_transfer"]["common_pose_outer_opening_mm"]-expected_opening) <= 1e-8 for s in result["shafts"])
               and all(r["force_error_n"] <= 1e-6 and r["moment_error_nmm"] <= 215.9e-6 for r in [*references, *shaft_references]))
    return {"schema": "knee_common_two_shafts_engineering_reference/v1", "status": "MATCHED" if matched else "STOP_REFERENCE_MISMATCH",
            "expected_each_shaft_tension_n": 100.0, "expected_common_opening_mm": expected_opening,
            "symmetric_station_offsets_mm": [-30, 30], "nonzero_moment_datum_offset_mm": (20*basis[1]).tolist(),
            "full_wrench_references": references, "per_shaft_full_wrench_references": shaft_references,
            "state": result, **FLAGS}


def execute(output, *, numerical):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    report = {"schema": "knee_common_shafts/v1", "mode": "build" if numerical else "prepare", "status": "STOP",
              "engineering_execution_started": False, "engineering_reference_executed": False,
              "coupled_equilibria_attempted": 0, "states": [], "runtime_pins": RUNTIME,
              "scope": "Four existing side shafts only; combined signed full wrench of each of three receivers per side is prescribed.",
              "other_interfaces": "Fresh source forces remain frozen; saved global q and rigid coordinates are not imposed or updated.",
              "internal_v_ties": "Four new ties require a separate common elastic seat field and passive law; no qualification transfers.",
              "finite_plan": {"symmetric_known_answers_first": 1, "sides": 2, "cases_per_side": 6,
                              "shafts_per_side": 2, "coordinates_per_side": 218, "free_coordinates_per_side": 211,
                              "maximum_Newton_iterations_per_state": 150}, **FLAGS}
    try:
        adapter = retained()
        pins.update(adapter.PINS)
        packet = sources(adapter, pins)
        report["source_closure_ready"] = True
        report["fresh_D_point_join_max_errors"] = packet["fresh_D_point_join_max_errors"]
        report["preceding_fit_residuals_scaled_mm"] = packet["preceding_fit_residuals_scaled_mm"]
        write(output / "input-contract.json", {"schema": "knee_common_shafts_contract/v1", **packet,
                                              "source_sha256": adapter.source_map(pins), **FLAGS})
        if numerical:
            observed = {"python": sys.version.split()[0], **{name: importlib.metadata.version(name) for name in ("numpy", "scipy")}}
            report["observed_runtime"] = observed
            require(observed == RUNTIME, "parent must use frozen Python/NumPy/SciPy runtime")
            import numpy as np
            from scipy.optimize import brentq

            core, entry, _, _ = adapter.backend(np, brentq)
            report["engineering_execution_started"] = True
            report["engineering_reference_executed"] = True
            reference = known_answer(np, brentq, adapter, core, entry, packet)
            write(output / "engineering-reference.json", reference)
            require(reference["status"] == "MATCHED", "symmetric sharing/opening/full-wrench engineering reference did not match")
            for index, state in enumerate(packet["packets"]):
                report["active_state"] = {"side": state["side"], "case_id": state["case_id"]}
                report["coupled_equilibria_attempted"] += 1
                result = solve_one(np, brentq, adapter, core, entry, packet["contract"], state)
                name = f"state-{index:02d}.json"
                write(output / name, result)
                report["states"].append({"side": state["side"], "case_id": state["case_id"], "status": result["status"],
                                         "combined_full_wrenches_closed": result["combined_full_wrenches_closed"],
                                         "path": name, "sha256": sha(output / name)})
                print(json.dumps(report["states"][-1]), flush=True)
            report["active_state"] = None
            report["status"] = ("COMPLETE_12_CONDITIONAL_COMMON_RECEIVER_EQUILIBRIA"
                                if all(s["combined_full_wrenches_closed"] for s in report["states"])
                                else "STOP_ONE_OR_MORE_COUPLED_EQUILIBRIA")
        else:
            report["status"] = "PREPARED_COMMON_RECEIVER_EQUILIBRIUM_API"
    except (ValueError, KeyError, OSError, RuntimeError, ImportError, zipfile.BadZipFile, struct.error) as error:
        report["failure"] = {"type": type(error).__name__, "detail": str(error)}
    try:
        require(all(sha(path) == digest for path, digest in pins.items()), "consumed source changed")
        report["sources_unchanged_before_and_after"] = True
    except (OSError, ValueError) as error:
        report["status"] = "STOP"
        report["sources_unchanged_before_and_after"] = False
        report["source_failure"] = str(error)
    report["source_sha256"] = {p.relative_to(ROOT).as_posix(): digest for p, digest in sorted(pins.items())}
    write(output / "report.json", report)
    write(output / "receipt.json", {"schema": "knee_common_shafts_receipt/v1", "status": report["status"],
                                   "source_sha256": report["source_sha256"],
                                   "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                                   "sources_unchanged_before_and_after": report["sources_unchanged_before_and_after"], **FLAGS})
    return report


def prepare(output):
    """Standard-library-only provenance and signed full-wrench source joins."""
    return execute(output, numerical=False)


def build(output):
    """Parent-only engineering execution; symmetric known answer precedes cases."""
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--build", action="store_true", help="Parent-only numerical execution; default is stdlib preparation.")
    args = parser.parse_args()
    result = build(args.output) if args.build else prepare(args.output)
    print(result["status"])
    raise SystemExit(0 if result["status"].startswith(("PREPARED_", "COMPLETE_")) else 2)
