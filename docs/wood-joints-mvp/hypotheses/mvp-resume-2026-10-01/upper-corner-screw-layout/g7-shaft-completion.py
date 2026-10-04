"""Complete only the authenticated T=0 upper-G7 shaft numerical null.

Import is inert. A rank-aware initializer changes only the initial pose;
the pinned original shaft helper owns residual acceptance and field recovery.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/g7-shaft-completion"
BASE = HERE / "rawlocal/bolt-reference-completion/two-recovery-attempt01"
PRODUCER = HERE / "bolt-reference-completion.py"
PRODUCER_SHA = "b0d45007a15e4de08f7c6a3d69194e7e434f43c96a221d02cf1382e1c17eb56f"
RECEIPT_SHA = "353f5890dd8cccc8db5cbf29bd7f2daa1de8877e3031825343a807a47421aa22"
TARGET = ("a12-left", "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1")


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


def initializer(K, C, weights, gaps, linear, rigid, initial, np):
    """Same convex hinge energy, exact breakpoint line search, at most 32 steps.

    Nullspace directions preserve bending and existing bore penetrations. Range
    Newton directions use the positive tangent eigenmodes. No artificial spring
    is added to a zero-curvature mode. The unchanged helper remains the gate.
    """
    pose, events = initial.copy(), []

    def evaluate(z):
        relative = C @ z
        penetration = np.sign(relative) * np.maximum(abs(relative) - gaps, 0.)
        active = abs(relative) > gaps
        gradient = K @ z + linear + C.T @ (weights * penetration)
        tangent = K + C.T @ (weights[:, None] * active[:, None] * C)
        energy = float(.5 * z @ K @ z + linear @ z + .5 * np.sum(weights * penetration**2))
        return energy, gradient, tangent, relative, active

    for iteration in range(33):
        energy, gradient, tangent, relative, active = evaluate(pose)
        event = {"iteration": iteration, "energy_nmm": energy,
                 "scaled_gradient_inf_n": float(max(abs(gradient))),
                 "active_bore_sample_indices": np.flatnonzero(active).tolist(),
                 "pose_scaled_mm": pose.tolist()}
        events.append(event)
        if max(abs(gradient)) <= 1e-6:
            return pose, {"status": "STATIONARY_INITIAL_POSE", "events": events,
                          "max_steps": 32, "force_gate_n": 1e-6,
                          "material_law_or_geometry_changed": False}
        require(iteration < 32, "rank-aware initializer reached its 32-step bound")
        _, singular, vh = np.linalg.svd(C[active] @ rigid, full_matrices=True)
        rank = int(np.sum(singular > (max(1., singular[0]) if len(singular) else 1.) * 1e-12))
        null = rigid @ vh[rank:].T
        if null.shape[1]:
            null, _ = np.linalg.qr(null)
        projected = null @ (null.T @ gradient)
        event["analytical_tangent_nullity"] = null.shape[1]
        event["null_gradient_inf_n"] = float(max(abs(projected)))
        if max(abs(projected)) > 1e-8:
            direction = -projected / max(abs(projected))
            event["direction"] = "ANALYTICAL_NULL_DESCENT"
            event["active_contact_direction_error"] = float(max(abs(C[active] @ direction), default=0.))
            require(event["active_contact_direction_error"] < 1e-9,
                    "null direction changes an existing contact")
        else:
            values, vectors = np.linalg.eigh(tangent)
            positive = values > max(1., values[-1]) * 1e-12
            require(values[0] >= -1e-9 * max(1., values[-1]), "initializer tangent is indefinite")
            direction = -vectors[:, positive] @ ((vectors[:, positive].T @ gradient) / values[positive])
            event["direction"] = "RANGE_NEWTON"
        slope = float(gradient @ direction)
        require(slope < 0 and np.isfinite(direction).all(), "initializer direction does not descend")
        rates = C @ direction
        bending_rate = float(direction @ K @ direction)
        require(bending_rate >= -1e-8 * max(1., abs(slope)), "line curvature is negative")
        bending_rate = max(0., bending_rate)

        def derivative(t, relative=relative, rates=rates, direction=direction,
                       pose=pose, bending_rate=bending_rate):
            rel = relative + t * rates
            pen = np.sign(rel) * np.maximum(abs(rel) - gaps, 0.)
            return float(direction @ (K @ pose + linear) + t * bending_rate
                         + np.sum(weights * pen * rates))

        breaks = sorted({float((side * gaps[i] - relative[i]) / rates[i])
                         for i in range(len(rates)) if abs(rates[i]) > 1e-14
                         for side in (-1., 1.)
                         if (side * gaps[i] - relative[i]) / rates[i] > 1e-14})
        left = 0.
        for right in [*breaks, math.inf]:
            middle = (left + right) / 2 if math.isfinite(right) else left + max(1., abs(left))
            branch_active = abs(relative + middle * rates) > gaps
            curvature = bending_rate + float(np.sum(weights[branch_active] * rates[branch_active]**2))
            at_left = derivative(left)
            if curvature > 0:
                candidate = left - at_left / curvature
                if candidate <= right and candidate >= left - 1e-10 * max(1., abs(left)):
                    step = max(left, candidate)
                    break
            require(math.isfinite(right), "convex energy is unbounded on the chosen ray")
            left = right
        else:
            raise ValueError("STOP: no exact line minimizer")
        require(step > 0 and math.isfinite(step), "line search produced a nonpositive step")
        candidate = pose + step * direction
        require(evaluate(candidate)[0] <= energy + 1e-9 * max(1., abs(energy)), "exact line did not reduce energy")
        event.update({"step_fraction": step, "line_breakpoints": len(breaks),
                      "line_derivative_at_minimum_n": derivative(step)})
        pose = candidate
    raise AssertionError("unreachable")


def oracle(np):
    K = np.diag([0., 0., 10000.])
    C = np.array([[1., 0., 0.], [0., 1., 0.]])
    weights, gaps, linear = np.array([1000., 20.]), np.array([1.15, .75]), np.array([-5., 4., -4.])
    answer, report = initializer(K, C, weights, gaps, linear, np.eye(3)[:, :2], np.zeros(3), np)
    expected = np.array([1.155, -.95, .0004])
    error = float(max(abs(answer - expected)))
    require(error <= 1e-10 and any(row.get("direction") == "ANALYTICAL_NULL_DESCENT" for row in report["events"]),
            "gap/elastic/nullspace known answer differs")
    return {"answer": answer.tolist(), "expected": expected.tolist(), "pose_error_mm": error, **report}


def context():
    require(sha(PRODUCER) == PRODUCER_SHA and sha(BASE / "receipt.json") == RECEIPT_SHA,
            "consumed two-state producer or receipt changed")
    producer = module(PRODUCER, "g7_original_producer")
    api = producer.load_module(producer.EXTRACTOR, "g7_saved_extractor")
    receipt = api.read(BASE / "receipt.json")
    require(receipt["sources_authenticated_before_and_after"] is True
            and receipt["producer_sha256"] == PRODUCER_SHA
            and len(receipt["source_sha256"]) == 159 and len(receipt["output_sha256"]) == 10
            and receipt["counts"]["completed_shaft_states"] == 503
            and receipt["counts"]["recovered_washer_end_states"] == 1006, "base completion scope differs")
    pins = {PRODUCER: PRODUCER_SHA, BASE / "receipt.json": RECEIPT_SHA,
            Path(__file__).resolve(): sha(__file__), Path(__file__).with_suffix(".md"): sha(Path(__file__).with_suffix(".md"))}
    for path, expected in receipt["source_sha256"].items():
        api.bind(pins, ROOT / path, expected)
    for name, expected in receipt["output_sha256"].items():
        require((BASE / name).resolve().parent == BASE, "base output path escapes")
        api.bind(pins, BASE / name, expected)
    api.authenticate(pins)
    return producer, api, pins, receipt


def build(output):
    output = Path(output).absolute()
    require(output.parent == RAW and output.resolve() == output and not output.exists(), "fresh immediate owned RAW child required")
    saved_bytecode, saved_path = sys.dont_write_bytecode, list(sys.path)
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(ROOT), str(HERE.parent)]
    try:
        p, api, pins, _base_receipt = context()
        import numpy as np
        require(np.__version__ == "2.5.2", "pinned NumPy runtime differs")
        known_answer = oracle(np)
        helper = p.load_module(p.SHAFT, "g7_original_shaft")
        original_beam = helper.beam_model

        def first_order(family, tension):
            elastic, geometric, samples, curvatures, inertia = original_beam(family, tension)
            return elastic, np.zeros_like(geometric), samples, curvatures, inertia

        helper.beam_model = first_order
        solve, contract = p.seeded_shaft_solver(helper)
        original = {name: (BASE / name).read_bytes().splitlines(keepends=True)
                    for name in ("steel.jsonl", "washer-ends.jsonl", "shaft-fields.jsonl", "end-grain.jsonl")}
        identity = lambda row: (row["case_id"], row["axis_id"])
        steel = [json.loads(row) for row in original["steel.jsonl"]]
        targets = [i for i, row in enumerate(steel) if row["shaft"] is None]
        require(len(steel) == 504 and len(targets) == 1 and identity(steel[targets[0]]) == TARGET, "sole target differs")
        index = targets[0]
        row = dict(steel[index])
        family, order = row["geometry"], row["receivers_head_to_nut"]
        require(row["signed_axial_n"] == 0. and row["same_plane_lateral_n"] == 1.9755775926692833, "target loading differs")
        saved = [json.loads(line) for line in (p.SAVED / "records.jsonl").read_bytes().splitlines()]
        record = saved[row["source_record_index"]]
        require(identity(record) == TARGET and row["source_component_rows"] == record["component_rows"]
                and row["source_tie_row"] == record["tie_row"], "target action join differs")
        old_end = json.loads(original["washer-ends.jsonl"][2 * index])
        direction = old_end["shaft_axis_head_to_nut_xyz"]
        force = np.asarray(record["force_on_first_body_xyz_n"] if order[0] == record["receivers"][0] else record["force_on_second_body_xyz_n"])
        drive = -force / row["same_plane_lateral_n"]
        require(abs(float(drive @ direction)) < 1e-8 and math.isclose(float(np.linalg.norm(drive)), 1., abs_tol=1e-8), "drive differs")
        references = p.load_module(p.REFERENCE_LOADER, "g7_reference_loader")
        lateral = api.pure_module(p.PACKET / "lateral_reference.py", "g7_lateral")
        members = {r["member_id"]: r["reduced_geometry_descriptor"] for r in api.read(api.GEOMETRY)["members"] if r["member_kind"] != "panel"}
        source = {**{key: record[key] for key in ("case_id", "axis_id", "gap_scale", "kind")},
                  "signed_T_n": 0., "V_n": row["same_plane_lateral_n"], "drive_unit_xyz": drive.tolist(),
                  "rotation_axis_xyz": np.cross(direction, drive).tolist(), "lateral_direction_arbitrary": False,
                  "physical_interface_point_xyz_mm": record["point_xyz_mm"], "shaft_axis_head_to_nut_xyz": direction,
                  "receivers_head_to_nut": order,
                  "Fe_mpa": {role: lateral.bearing(lateral.angle(force, references.unit(members[body]["axis"]))) * p.PSI_MPA
                             for role, body in zip(("host", "cleat"), order, strict=True)}}
        previous = next(r for r in api.read(BASE / "recovery-trace.json")["states"] if identity(r) == TARGET)
        initial = np.asarray(previous["events"][-1]["pose_scaled_mm"])
        helper.LENGTH = family["host_length_mm"] + family["cleat_length_mm"]
        K, geometric, samples, _, _ = helper.beam_model(family, 0.)
        require(np.count_nonzero(geometric) == 0 and len(samples) == 48, "first-order shaft convention differs")
        C, weights = np.vstack([sample[0] for sample in samples]), p.KWOOD * family["diameter_mm"] * np.asarray([sample[1] for sample in samples])
        gaps = np.full(48, (family["bore_mm"] - family["diameter_mm"]) / 2)
        linear = np.zeros(36)
        linear[34] = -source["V_n"]
        nodes = np.r_[np.linspace(0., family["host_length_mm"], 9), np.linspace(family["host_length_mm"], helper.LENGTH, 9)[1:]]
        rigid = np.zeros((36, 4))
        rigid[:34:2, 0], rigid[:34:2, 1], rigid[1:34:2, 1] = 1., nodes / helper.LENGTH, 1.
        rigid[34, 2], rigid[35, 3] = 1., 1.
        require(max(abs(K @ rigid).ravel()) < 1e-6, "analytical rigid modes fail elastic annihilation")
        api.authenticate(pins)
        seed, initialization = initializer(K, C, weights, gaps, linear, rigid, initial, np)
        helper_trace = []

        def log(event, iteration, pose, evaluation, **details):
            entry = {"event": event, "iteration": iteration, "pose_scaled_mm": pose.tolist()}
            if evaluation is not None:
                entry.update({"scaled_gradient_inf_n": float(max(abs(evaluation[1]))),
                              "active_bore_sample_indices": np.flatnonzero(evaluation[4]).tolist()})
            helper_trace.append(entry)

        state, fields, bore = solve(source, family, p.KWOOD, seed, log)
        require(len(fields) == 80 and len(bore) == 48 and state["small_angle_projected_axial_shortening_mm"] == 0.
                and abs(state["host_force_balance_residual_n"]) <= 1e-6
                and abs(state["host_moment_balance_residual_nmm"]) <= helper.LENGTH * 1e-6, "unchanged shaft/wrench gates differ")
        row.update({"shaft": state, "shaft_ratio": state["peak_beam_stress_witness"]["proxy_over_conditional_92ksi_Fyb"], "shaft_null_reason": None,
                    "g7_completion_provenance": {"base_receipt_sha256": RECEIPT_SHA, "steel_record_index": index,
                                                "initial_pose_only_changed": True, "method": "analytical null descent / exact breakpoint line search"}})
        row["same_state_steel_ratio"] = max(row["thread_tension_ratio"], row["average_T_V_ratio"], row["shaft_ratio"])
        row["status"] = p.reference_status(row["same_state_steel_ratio"])
        combined = {name: list(lines) for name, lines in original.items()}
        combined["steel.jsonl"][index] = p.serialize(row).encode()
        hardware = p.load_module(p.HARDWARE, "g7_hardware")
        with p.HARDWARE_AXES.open(newline="", encoding="utf-8") as stream:
            family_ids = {r["axis_id"]: r["family_id"] for r in csv.DictReader(stream)}
        catalog = hardware.STACKS[hardware.ROUTES[family_ids[row["axis_id"]]][0]]
        traction = references.pure_functions(p.TRACTION, ["action", "wrench", "wood_seat", "shifted"], {"np": np, "require": require})
        source_join = {**old_end["source_join"], "producer_sha256": pins[Path(__file__).resolve()], "g7_base_receipt_sha256": RECEIPT_SHA}
        for end_index in (0, 1):
            end = p.washer_end_source(record, state, family, order, direction, row["partial_supported_ring_route"],
                                      catalog, end_index, source_join, helper, traction, np, None, row["geometry_applicability"])
            require(end["status"] == "COMPLETE_ISOLATED_END_SOURCE", "own-end source remains incomplete")
            combined["washer-ends.jsonl"][2 * index + end_index] = p.serialize(end).encode()
        combined["shaft-fields.jsonl"].extend(p.serialize({**{key: record[key] for key in ("case_id", "axis_id", "gap_scale", "kind")}, **field}).encode() for field in fields)
        reuse = {}
        for name, lines in original.items():
            keep = [i for i in range(len(lines)) if not (name == "steel.jsonl" and i == index)
                    and not (name == "washer-ends.jsonl" and i // 2 == index)]
            before, after = b"".join(lines[i] for i in keep), b"".join(combined[name][i] for i in keep)
            require(before == after, "accepted base bytes changed: " + name)
            reuse[name] = {"rows": len(keep), "sha256": hashlib.sha256(before).hexdigest(), "byte_identical": True}
        steel[index] = row
        summary = {"status": "COMPLETE_CONDITIONAL_COMPARISONS", "scope": "ONLY_ONE_T0_G7_SHAFT_NULL",
                   "base_receipt_sha256": RECEIPT_SHA, "target": list(TARGET), "counts": {"completed_shaft_states": 504, "null_shaft_states": 0,
                   "recovered_washer_end_states": 1008, "null_washer_end_states": 0, "shaft_field_samples": 40320, "new_shaft_calls": 1},
                   "N10": {key: p.component_summary(steel, key) for key in ("thread_tension_ratio", "average_T_V_ratio", "shaft_ratio", "same_state_steel_ratio")},
                   "target_steel": row, "initializer": initialization, "known_answer": known_answer, "solver_contract": contract,
                   "helper_trace": helper_trace, "preserved_base_rows": reuse, "N10_comparisons_complete": True,
                   "N09_end_sources_complete": True, "N09_complete": False, **p.FLAGS}
        api.authenticate(pins)
        output.mkdir(parents=True, exist_ok=False)
        for name, lines in combined.items():
            (output / name).write_bytes(b"".join(lines))
        for name, value in (("summary.json", summary), ("bore-fields.json", bore), ("sources.json", {api.key(k): v for k, v in pins.items()})):
            (output / name).write_text(p.serialize(value))
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        (output / "documentation.md.snapshot").write_bytes(Path(__file__).with_suffix(".md").read_bytes())
        outputs = {path.name: sha(path) for path in sorted(output.iterdir())}
        receipt = {"schema": "g7_shaft_completion_receipt/v1", "producer_sha256": sha(__file__), "base_receipt_sha256": RECEIPT_SHA,
                   "source_sha256": {api.key(k): v for k, v in pins.items()}, "output_sha256": outputs, "counts": summary["counts"],
                   "sources_authenticated_before_and_after": True, "N10_comparisons_complete": True, "N09_end_sources_complete": True,
                   "N09_complete": False, **p.FLAGS}
        api.authenticate(pins)
        (output / "receipt.json").write_text(p.serialize(receipt))
        return receipt
    finally:
        sys.dont_write_bytecode, sys.path[:] = saved_bytecode, saved_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.oracle:
        import numpy as np
        print(json.dumps(oracle(np), sort_keys=True, allow_nan=False))
    else:
        require(args.output is not None, "--output is required")
        print(json.dumps(build(args.output), sort_keys=True, allow_nan=False))
