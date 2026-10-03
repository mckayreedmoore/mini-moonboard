"""Prepare, then reconcile frozen knee states in a parent-authorized finite run.

Importing this module reads no evidence and imports no numerical library.
prepare(output) authenticates inputs and array headers only. build(output) adds
one small common-pose LP per saved nominal case, never a frame/contact solve.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-common-compatibility"
CONTINUOUS = HERE / "knee-bridge-continuous-shafts.py"
COMPLETED = HERE / "rawlocal/knee-bridge-continuous-shafts/attempt02"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02"
REPLAY = HERE / "rawlocal/knee-bridge-joint-replay/attempt01"
GEOMETRY = HERE / "rawlocal/knee-bridge-geometry/attempt01"
PROPOSAL = HERE / "rawlocal/knee-spine-reinforcement/attempt01/checks.json"
COUPON = HERE / "rawlocal/knee-compatible/coupon-attempt01"
ENTRY_COUPON = HERE / "rawlocal/knee-contact-entry/coupon-attempt01"
RUNTIME = {"python": "3.12.3", "numpy": "2.5.2", "scipy": "1.18.1"}
MOTION_TOL_MM = 1e-5  # Existing simple_frame motion resolution, not a joint criterion.
ROTATION_SCALE_MM = 1000.0
SLOPE_SCALE_MM = 215.9
LP_TOL = 1e-9
PINS = {
    CONTINUOUS: "c5e45ddc8c92094879fbfdaacb7ef66f3eb06b7843eb5728c25cbae32c259e27",
    COMPLETED / "receipt.json": "5496190db02ec1ed8fca6ced59f7538526503ab6735f946e651394ab225d1ffa",
    COMPLETED / "suite.json": "ec3b5bbc6d2c80c38bfcbe5877a4ea9ca6ac89f926f5f22fa799bfb9c76a701f",
    INTEGRATION / "manifest.json": "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    INTEGRATION / "receipt.json": "8a2813419289bee46e2e0985ab702a602a8ff3a0d3aacdd43d1aad841c92c8df",
    REPLAY / "checks.json": "71980f983dd3466d02eb6c5f838186de4b77dc2ebe04653f66cf3f3598fbe891",
    REPLAY / "receipt.json": "10503afef20c8fc69c0f5b4877f8deb2794646c258b05ca63616611443c6c22b",
    REPLAY / "allocations.jsonl": "5428cf793ba59c0ca1d75dbfedb62036518f29d31cefe63101df9b3d0a5bdb17",
    GEOMETRY / "manifest.json": "254dd58d2f311553b32637b01b85b8bacbc0b474acfee667597333c501afe147",
    PROPOSAL: "c9360e7ca4ab167a5cbc505373b2bd1342aa6a830f72a26113da9f7c4a8ad778",
    COUPON / "coupon.json": "c76aacdd80d42adc6ae7a080ea3ae3ab4b614cb1dcce2709a429e764a11fa1cd",
    COUPON / "receipt.json": "515f38a54c30b961f8c9edbd9de0f49f73b8e52f6bd5f4eee71de01778240482",
    ENTRY_COUPON / "coupon.json": "3301215eaef7b83ec4ac1d940615f44e2004e112029f1d3c64b99a6f8a84f3b1",
    ENTRY_COUPON / "receipt.json": "d2d4fc452e237e706a9e0eec5835e617000c157dda3d2608152c8d355a25b8bf",
    HERE.parent / "simple_frame.py": "3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34",
    ROOT / "uv.lock": "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
}
FLAGS = {
    "all_eight_axis_common_state_qualified": False,
    "elastic_receiver_field_qualified": False,
    "internal_passive_law_adopted": False,
    "actual_changed_hole_stiffness_qualified": False,
    "global_stability_qualified": False,
    "hardware_capacity_qualified": False,
    "complete_joint_acceptance": False,
    "proposal_adopted": False,
    "physical_release": False,
    "physical_failure_claimed": False,
    "loads_stiffness_or_gaps_tuned": False,
    "frame_native_or_CAD_run": False,
    "software_tests_or_review_run": False,
}
MISSING = [
    {
        "field": "internal_v_pairs.passive_axial_law_and_unloaded_seat_reference",
        "evidence": "The 24 allocations are static_allocation_only; all four global_operator_row fields are null.",
        "needed": "An explicit passive law with unloaded length, installation gap/preload policy and both seat contact laws.",
    },
    {
        "field": "modified_spines.common_elastic_displacement_and_rotation_field",
        "evidence": "rigid300 contains rigid components; q1612 contains relative connector motions, with no new v-seat coordinates.",
        "needed": "Same-state bore-line and v-seat elastic displacements under the combined unchanged shaft and internal tie tractions.",
    },
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


def retained():
    require(sha(CONTINUOUS) == PINS[CONTINUOUS], "retained adapter changed")
    spec = importlib.util.spec_from_file_location("retained_knee_shaft_adapter", CONTINUOUS)
    require(spec is not None and spec.loader is not None, "retained adapter API unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def header(stream):
    prefix = stream.read(8)
    require(prefix[:6] == b"\x93NUMPY" and prefix[6] in (1, 2, 3), "unsupported saved NPY header")
    size = 2 if prefix[6] == 1 else 4
    length = int.from_bytes(stream.read(size), "little")
    require(0 < length < 10000, "invalid saved NPY header length")
    return ast.literal_eval(stream.read(length).decode("utf-8"))


def sources(adapter, pins):
    """Reuse the completed shaft provenance API without any numerical calls."""
    adapter.authenticate(pins)
    original, _old_suite, _old_fit, comparison, selected, identities = adapter.sources(pins)
    model, rows = (read(adapter.GRAVITY / name) for name in ("model.json", "row-identities.json"))
    contract, states, _references, reuse = adapter.reuse_nominal(
        pins, adapter.REUSE, original, selected, identities, rows)
    completed, receipt = read(COMPLETED / "suite.json"), read(COMPLETED / "receipt.json")
    require(completed["status"] == receipt["status"] == "COMPLETE_FRESH_24_SHAFT_STATES_AND_96_PLACEMENTS"
            and completed["all24_nominal_completed"] and completed["postprocess_only"]
            and completed["reuse"] == reuse and completed["states"] == states
            and receipt["output_sha256"]["suite.json"] == PINS[COMPLETED / "suite.json"],
            "completed continuation does not bind the immutable attempt01 states")
    # Each consumed child must also be bound by its own completed receipt.
    integration, integration_receipt = read(INTEGRATION / "manifest.json"), read(INTEGRATION / "receipt.json")
    replay, replay_receipt = read(REPLAY / "checks.json"), read(REPLAY / "receipt.json")
    require(integration_receipt["output_sha256"]["manifest.json"] == PINS[INTEGRATION / "manifest.json"]
            and replay_receipt["output_sha256"]["checks.json"] == PINS[REPLAY / "checks.json"]
            and replay_receipt["output_sha256"]["allocations.jsonl"] == PINS[REPLAY / "allocations.jsonl"],
            "integration/static allocation receipt differs")
    require(integration["census"]["existing_receiver_bolt_axes"] == 104
            and integration["census"]["total_unique_proposal_bolt_axes"] == 108
            and integration["proposal_adopted"] is False
            and replay["local_elastic_compatibility_solved"] is False
            and replay["internal_allocation_count"] == 24
            and replay["geometry_overrides"] == integration["geometry"]["STEP_overrides"],
            "proposal, static census or modified geometry authority differs")
    modified = read(PROPOSAL)["geometry_proposals"]
    geometries = {body: value["hypothetical_geometry"] for body, value in modified.items()}
    geometry_manifest = read(GEOMETRY / "manifest.json")
    for override in integration["geometry"]["STEP_overrides"]:
        body, step = override["body"], override["proposal_step"]
        require(override["geometry_reference"]["sha256"] == PINS[GEOMETRY / "manifest.json"]
                and geometry_manifest["bodies"][body]["preserved_u_bore_count"] == 4
                and geometry_manifest["bodies"][body]["added_v_bore_count"] == 2,
                "modified spine does not preserve four u bores and two added v bores")
        adapter.bind(pins, ROOT / step["path"], step["sha256"])
    allocations = [json.loads(line) for line in (REPLAY / "allocations.jsonl").read_text().splitlines()]
    axes = integration["proposed_internal_bolt_axes"]
    require(len(axes) == 4 and all(a["same_body_end_pair"] and a["global_operator_row"] is None
            and a["receiver_interfaces"] == [] for a in axes), "internal axes became global receiver rows")
    expected = {(case, a["canonical_axis_id"]) for case in adapter.CASES for a in axes}
    require(len(allocations) == 24
            and {(r["case_id"], r["canonical_axis_id"]) for r in allocations} == expected,
            "static allocation case/axis join differs")
    for axis in axes:
        geom = geometries[axis["body"]]
        matches = [b for b in geom["bores"] if b["axis_id"] == axis["canonical_axis_id"]]
        require(len(matches) == 1 and matches[0]["radius_mm"] == 3.75
                and matches[0]["removed_interval_axis"] == 1
                and axis["nominal_shaft_record"]["diameter_mm"] == 6.35
                and axis["center_local_guv_mm"] == [matches[0]["station_mm"], 0.0, 0.0],
                "internal axis does not match the modified six-bore geometry")
        for row in [r for r in allocations if r["canonical_axis_id"] == axis["canonical_axis_id"]]:
            require(row["static_allocation_only"] and row["global_receiver_force_record"] is False
                    and row["block"] == axis["body"] and math.isfinite(row["axial_tension_n"])
                    and row["axial_tension_n"] >= 0
                    and [{k: e[k] for k in axis["end_seats"][0]} for e in row["end_seats"]] == axis["end_seats"],
                    "internal allocation lost its saved seats, sign or static scope")
    bodies = list(dict.fromkeys(b for axis in adapter.AXES for b in contract["geometry"][axis]["receiver_order"]))
    ports = [i for i, r in enumerate(rows) if
             {r["ownership"]["first_body"], r["ownership"]["second_body"]}.issubset(bodies)]
    retained_rows = [r for r in rows if r["ownership"]["second_body"] != "floor"]
    indices = {r["row"]: i for i, r in enumerate(retained_rows)}
    require(len(bodies) == 6 and len(model["body_names"]) == 50
            and len(retained_rows) == 1588 and len(ports) == 36
            and all(rows[i]["row"] == i for i in ports), "six-body/36-port or q prefix census differs")
    with zipfile.ZipFile(adapter.RESPONSE) as archive:
        for case in adapter.CASES:
            for suffix, shape in (("rigid_coordinates", (300,)), ("lumped_q_mm", (1612,)), ("raw_force_n", (1888,))):
                with archive.open(case + "_gap_" + suffix + ".npy") as stream:
                    description = header(stream)
                require(description == {"descr": "<f8", "fortran_order": False, "shape": shape},
                        "saved nominal array header differs: " + case + "/" + suffix)
    coupon, entry_coupon = read(COUPON / "coupon.json"), read(ENTRY_COUPON / "coupon.json")
    require(coupon["status"] == entry_coupon["status"] == "matched"
            and all(r["matched"] for r in coupon["arithmetic"])
            and all(r["matched"] for r in entry_coupon["records"])
            and coupon["input_contract_sha256"] == adapter.PINS[adapter.CONTRACT]
            and read(COUPON / "receipt.json")["output_sha256"]["coupon.json"] == PINS[COUPON / "coupon.json"]
            and read(ENTRY_COUPON / "receipt.json")["output_sha256"]["coupon.json"] == PINS[ENTRY_COUPON / "coupon.json"],
            "retained mechanics known answers are not authenticated matches")
    require(contract["model"]["bolt_E_mpa"] == 200000.0
            and contract["model"]["wood_bore_and_seat_stiffness_mpa_per_mm"] == 20.0
            and contract["model"]["head_contact_stiffness_mpa_per_mm"] == 10000.0,
            "original K20/K10000/E200000 model changed")
    adapter.authenticate(pins)
    return {"contract": contract, "states": states, "model": model, "rows": rows,
            "bodies": bodies, "ports": ports, "q_indices": indices,
            "axes": axes, "allocations": allocations, "comparison": comparison,
            "modified_geometry": geometries, "reuse": reuse}


def point_row(np, names, origins, body, point, direction):
    """direction dot [t + theta cross (point-origin)], using 1000*theta."""
    row = np.zeros(6 * len(names))
    offset = 6 * names.index(body)
    row[offset:offset + 3] = direction
    row[offset + 3:offset + 6] = np.cross(np.asarray(point) - origins[body], direction) / ROTATION_SCALE_MM
    return row


def minimax(np, linprog, matrix, target, bounds):
    """min t, |A*x-b| <= t; preserve every equation and both certificates."""
    matrix, target = np.asarray(matrix), np.asarray(target)
    count, size = matrix.shape
    problem = np.vstack((np.column_stack((matrix, -np.ones(count))),
                         np.column_stack((-matrix, -np.ones(count)))))
    rhs = np.r_[target, -target]
    result = linprog(np.r_[np.zeros(size), 1.0], A_ub=problem, b_ub=rhs,
                     bounds=[*bounds, (0, None)], method="highs",
                     options={"primal_feasibility_tolerance": LP_TOL,
                              "dual_feasibility_tolerance": LP_TOL, "maxiter": 1000, "time_limit": 5.0})
    require(result.success and result.status == 0, "common-pose LP incomplete: " + result.message)
    pose, slack = result.x[:-1], float(result.x[-1])
    residual = matrix @ pose - target
    dual = result.ineqlin.marginals
    free = [i for i, bound in enumerate(bounds) if bound == (None, None)]
    dual_error = float(np.max(abs((problem.T @ dual)[free]), initial=0))
    lower = float(rhs @ dual)
    gap = abs(slack - lower)
    require(np.isfinite(result.x).all() and np.isfinite(dual).all()
            and np.max(abs(residual), initial=0) <= slack + 1e-8
            and np.max(dual, initial=0) <= 1e-8 and -float(sum(dual)) <= 1 + 1e-8
            and dual_error <= 1e-8 and gap <= 1e-8 * max(1, slack),
            "common-pose LP primal/dual certificate failed")
    return {"pose": pose, "residual": residual, "minimum_maximum_residual_mm": slack,
            "dual_lower_bound_mm": lower, "dual_free_stationarity_error": dual_error,
            "duality_gap_mm": gap, "dual_weights": (dual[:count] - dual[count:]).tolist()}


def method_known_answer(np, linprog):
    """Two finite engineering references for the new adapter only; parent runs."""
    row = point_row(np, ["body"], {"body": np.zeros(3)}, "body", [3, 5, 7], [0, 1, 0])
    error = abs(float(row @ np.array([2, -1, 4, 10, -20, 30])) - (-0.98))
    result = minimax(np, linprog, [[1.0], [1.0]], [0.0, 2.0], [(None, None)])
    require(error <= 1e-12 and abs(result["pose"][0] - 1) <= 1e-8
            and abs(result["minimum_maximum_residual_mm"] - 1) <= 1e-8,
            "new common-pose datum/sign/scaling or duplicate-conflict known answer failed")
    return {"status": "MATCHED", "point_motion_expected_mm": -0.98, "point_motion_error_mm": error,
            "duplicate_rows_expected_minimax_mm": 1.0, "duplicate_rows_returned_minimax_mm": result["minimum_maximum_residual_mm"]}


def equations(np, adapter, packet, case, response, origins):
    matrix, target, labels = [], [], []
    names = packet["bodies"]

    def append(row, value, **label):
        matrix.append(row)
        target.append(value)
        labels.append(label)

    for state in [s for s in packet["states"] if s["case_id"] == case]:
        axis = state["axis_id"]
        result = read(ROOT / state["result_path"])
        geometry = packet["contract"]["geometry"][axis]
        normal, basis = np.asarray(geometry["bolt_axis_xyz"]), np.asarray(result["fresh_boundary"]["transverse_basis_xyz"])
        datum, length = geometry["datum_mm"], geometry["modeled_wood_grip_mm"]
        middle = geometry["receiver_order"][1]
        pose = np.asarray(result["accepted_iterate"])
        require(pose.shape == (112,) and np.isfinite(pose).all(), "saved mixed pose is invalid")
        for index in (0, 2):
            body = geometry["receiver_order"][index]
            offset = 100 + 4 * index
            for component, direction in enumerate(basis):
                row = (point_row(np, names, origins, body, datum, direction)
                       - point_row(np, names, origins, middle, datum, direction))
                append(row, float(pose[offset + component]), source="frozen_local_translation",
                       axis_id=axis, body=body, component=component, units="mm")
                row = np.zeros(6 * len(names))
                for member, sign in ((body, 1), (middle, -1)):
                    start = 6 * names.index(member) + 3
                    row[start:start + 3] = sign * SLOPE_SCALE_MM * np.cross(normal, direction) / ROTATION_SCALE_MM
                append(row, float(SLOPE_SCALE_MM * pose[offset + 2 + component] / length),
                       source="frozen_local_scaled_slope", axis_id=axis, body=body,
                       component=component, units="215.9_mm_times_rad")
        require(result["normal_transfer"]["single_physical_tie_n"] > 0,
                "zero-T local opening is not unique; a unilateral slack contract is required")
        spine, inner = geometry["receiver_order"][0], geometry["receiver_order"][2]
        opening = (point_row(np, names, origins, inner, geometry["nut_seat_point_mm"], normal)
                   - point_row(np, names, origins, spine, geometry["head_seat_point_mm"], normal))
        append(opening, result["normal_transfer"]["required_outer_opening_mm"],
               source="frozen_local_signed_outer_opening", axis_id=axis, units="mm")
    q = response[case + "_gap_lumped_q_mm"]
    require(q.shape == (1612,) and np.isfinite(q).all(), "saved q1612 is invalid")
    for index in packet["ports"]:
        owner = packet["rows"][index]["ownership"]
        row = (point_row(np, names, origins, owner["second_body"], owner["point_mm"], owner["direction_global_xyz"])
               - point_row(np, names, origins, owner["first_body"], owner["point_mm"], owner["direction_global_xyz"]))
        q_index = packet["q_indices"][index]
        append(row, float(q[q_index]), source="saved_total_connector_q", raw_row=index,
               lumped_q_index=q_index, row_id=packet["rows"][index]["row_id"], units="mm")
    require(len(matrix) == 72, "36 frozen-local/36 total-motion equation census differs")
    return np.asarray(matrix), np.asarray(target), labels


def duplicate_conflicts(matrix, target, labels):
    """Identical coefficient rows give an exact, interpretable lower bound."""
    groups, conflicts = {}, []
    for index, row in enumerate(matrix):
        key = tuple(float(x) for x in row)
        previous = groups.setdefault(key, index)
        lower = abs(float(target[index] - target[previous])) / 2
        if lower > MOTION_TOL_MM:
            conflicts.append({"first_equation": previous, "second_equation": index,
                              "first": labels[previous], "second": labels[index],
                              "minimum_maximum_residual_lower_bound_mm": lower,
                              "target_difference_mm": float(target[index] - target[previous]),
                              "coefficient_rows_identical": True})
    return conflicts


def finite(np, linprog, adapter, packet, report):
    report["phase"] = "new_method_known_answer"
    report["new_method_known_answer"] = method_known_answer(np, linprog)
    model, names = packet["model"], packet["bodies"]
    centers = {body: np.mean([model["physical_node_coordinates_mm"][str(node)]
               for node in sorted(set(model["body_nodes"][body]))], axis=0) for body in model["body_names"]}
    origins = {body: centers["base_side_left" if "left" in body else "base_side_right"] for body in names}
    bounds = [(0.0, 0.0) if body.startswith("base_side_") else (None, None)
              for body in names for _ in range(6)]
    with np.load(adapter.GRAVITY / "operators.npz", allow_pickle=False) as operators:
        D = operators["D"]
        for index in packet["ports"]:
            owner = packet["rows"][index]["ownership"]
            row = (point_row(np, model["body_names"], centers, owner["second_body"], owner["point_mm"], owner["direction_global_xyz"])
                   - point_row(np, model["body_names"], centers, owner["first_body"], owner["point_mm"], owner["direction_global_xyz"]))
            require(np.max(abs(row - D[index])) <= 1e-10, "saved D point-motion sign/datum differs")
    cases = report["cases"]
    with np.load(adapter.RESPONSE, allow_pickle=False) as response:
        for case in adapter.CASES:
            report.update(phase="common_pose_reconciliation", active_case=case)
            matrix, target, labels = equations(np, adapter, packet, case, response, origins)
            fit = minimax(np, linprog, matrix, target, bounds)
            rigid = response[case + "_gap_rigid_coordinates"]
            require(rigid.shape == (300,) and np.isfinite(rigid).all(), "saved rigid300 is invalid")
            rigid_pose = []
            for body in names:
                offset = 6 * model["body_names"].index(body)
                rotation = rigid[offset + 3:offset + 6] / ROTATION_SCALE_MM
                translation = rigid[offset:offset + 3] + np.cross(rotation, origins[body] - centers[body])
                rigid_pose.extend([*translation, *(ROTATION_SCALE_MM * rotation)])
            internal = []
            for axis in packet["axes"]:
                allocation = next(r for r in packet["allocations"] if r["case_id"] == case
                                  and r["canonical_axis_id"] == axis["canonical_axis_id"])
                tension = allocation["axial_tension_n"]
                length = axis["nominal_shaft_record"]["wood_span_mm"]
                profile = packet["contract"]["model"]["end_profile"]
                head_area = math.pi * (profile["hypothetical_concentric_head_and_nut_flat_radius_mm"]**2 - (profile["washer_ID_max_mm"] / 2)**2)
                wood_area = math.pi * ((profile["washer_OD_min_mm"] / 2)**2 - (profile["washer_ID_max_mm"] / 2)**2)
                opening = tension * (length / (200000 * math.pi * 6.35**2 / 4)
                                      + 2 / (10000 * head_area) + 2 / (20 * wood_area))
                internal.append({"axis_id": axis["canonical_axis_id"], "saved_static_tension_n": tension,
                                 "passive_compatibility": "MISSING_LAW_AND_COMMON_ELASTIC_SEAT_FIELD",
                                 "P0_hypothesis_adopted": False,
                                 "P0_required_opening_mm": opening,
                                 "single_rigid_body_first_order_seat_extension_mm": 0.0,
                                 "P0_consequence": "POSITIVE_T_REQUIRES_ELASTIC_SEAT_EXTENSION" if tension > 0 else "ZERO_T_DOES_NOT_QUALIFY_PASSIVE_RESPONSE"})
            conflict = fit["dual_lower_bound_mm"] > MOTION_TOL_MM + 1e-8
            cases.append({"case_id": case, "gap_scale": 1.0,
                          "status": "NO_COMMON_AFFINE_EMBEDDING_AT_RECORDED_RESOLUTION" if conflict else "KINEMATIC_RECONCILIATION_ONLY",
                          "finite_common_pose_conflict": conflict,
                          "fit": {key: value for key, value in fit.items() if key not in ("pose", "residual")},
                          "best_pose_is_diagnostic_not_contact_equilibrium": True,
                          "body_order": names, "origins_mm": {b: origins[b].tolist() for b in names},
                          "diagnostic_body_pose_t_1000theta": fit["pose"].reshape(-1, 6).tolist(),
                          "duplicate_conflicts": duplicate_conflicts(matrix, target, labels),
                          "equations": [{**label, "coefficients": row.tolist(), "saved_target": float(value),
                                         "best_fit_residual": float(residual)}
                                        for label, row, value, residual in zip(labels, matrix, target, fit["residual"], strict=True)],
                          "saved_rigid_component_diagnostic_maximum_mm": float(np.max(abs(matrix @ rigid_pose - target))),
                          "rigid_component_used_as_total_motion": False, "internal_v_pairs": internal})
    report.update(phase="finite_reconciliation_complete", active_case=None)


def execute(output, *, numerical):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    report = {"schema": "knee_bridge_common_compatibility/v1", "mode": "finite" if numerical else "prepare",
              "status": "STOP", "finite_run_executed": False, "cases": [], "missing_fields": MISSING,
              "runtime_pins": RUNTIME, "kinematic_resolution_mm": MOTION_TOL_MM,
              "slope_scale_mm": SLOPE_SCALE_MM, "rotation_coordinate_scale_mm": ROTATION_SCALE_MM,
              "finite_plan": {"nominal_cases": 6, "feasibility_LPs": 6, "equations_per_case": 72,
                              "pose_coordinates": 36, "coordinate_gauges": 12, "LP_variables_including_slack": 37,
                              "new_method_known_answers": 2, "new_contact_or_frame_solves": 0},
              **FLAGS}
    adapter = None
    try:
        adapter = retained()
        pins.update(adapter.PINS)
        report["observed_runtime"] = {"python": sys.version.split()[0],
                                      **{name: importlib.metadata.version(name) for name in ("numpy", "scipy")}}
        require(report["observed_runtime"] == RUNTIME, "use the frozen repository Python/NumPy/SciPy runtime")
        packet = sources(adapter, pins)
        report.update(case_ids=adapter.CASES, shaft_axes=adapter.AXES,
                      global_bolt_axis_count=104, proposal_bolt_axis_count=108,
                      Hillman_axes_unchanged=66, immutable_local_states=packet["states"],
                      internal_axis_ids=[a["canonical_axis_id"] for a in packet["axes"]],
                      pose_layout={"raw_rows": 1888, "connector_q_prefix": 1588,
                                   "floor_mean_q_suffix": 24, "q_size": 1612, "rigid_size": 300},
                      source_API_ready_for_bounded_run=True,
                      full_passive_common_state_ready=False,
                      frozen_local_states_changed=False,
                      finite_scope="Embed the specific saved local states and total port q in one affine pose per receiver; no alternate local equilibria or elastic field are searched.")
        if numerical:
            import numpy as np
            from scipy.optimize import linprog

            report["finite_run_executed"] = True
            finite(np, linprog, adapter, packet, report)
            report["status"] = ("COMPLETE_FINITE_RECONCILIATION_WITH_COMMON_POSE_CONFLICT_AND_MISSING_PASSIVE_FIELDS"
                                if any(c["finite_common_pose_conflict"] for c in report["cases"])
                                else "COMPLETE_FINITE_RECONCILIATION_WITH_MISSING_PASSIVE_FIELDS")
        else:
            report["status"] = "PREPARED_BOUNDED_RUN_WITH_EXPLICIT_PASSIVE_FIELD_GAPS"
    except (ValueError, KeyError, OSError, RuntimeError, ImportError, zipfile.BadZipFile) as error:
        report["failure"] = {"type": type(error).__name__, "detail": str(error)}
    try:
        if adapter is not None:
            adapter.authenticate(pins)
        else:
            require(all(sha(p) == digest for p, digest in pins.items()), "source changed")
        report["sources_unchanged_before_and_after"] = True
    except (OSError, ValueError) as error:
        report["status"] = "STOP"
        report["sources_unchanged_before_and_after"] = False
        report["source_failure"] = str(error)
    report["source_sha256"] = {str(p.relative_to(ROOT)): digest for p, digest in sorted(pins.items())}
    write(output / "report.json", report)
    write(output / "receipt.json", {"schema": "knee_bridge_common_compatibility_receipt/v1",
                                   "status": report["status"], "source_sha256": report["source_sha256"],
                                   "output_sha256": {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()},
                                   "sources_unchanged_before_and_after": report["sources_unchanged_before_and_after"], **FLAGS})
    return report


def prepare(output):
    """Lightweight provenance/API preparation; no numerical libraries or LPs."""
    return execute(output, numerical=False)


def build(output):
    """Parent-only finite engineering reconciliation after preparation/authorization."""
    return execute(output, numerical=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prepare", action="store_true", help="Authenticate and prepare only; never evaluate numerical states.")
    args = parser.parse_args()
    result = prepare(args.output) if args.prepare else build(args.output)
    print(result["status"])
    raise SystemExit(2 if result["status"] == "STOP" else 0)
