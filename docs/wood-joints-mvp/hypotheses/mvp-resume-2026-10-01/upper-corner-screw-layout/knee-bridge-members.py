"""Parent-owned fresh references for exactly 42 unchanged timber bodies.

build(output) consumes authenticated new-gravity nominal actions and saved cuts.
It calls preserved pure arithmetic only. Importing this file reads no sources
and runs no arithmetic. Modified outer spines and plywood are outside this screen.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from itertools import pairwise
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-members"
MEMBERS = PACKET / "member-screen-attempt02/knee-bridge-gravity01"
REPORT = MEMBERS / "member-results.json"
ARRAYS = MEMBERS / "action-section-arrays.npz"
GEOMETRY = MEMBERS / "geometry.json"
INPUTS = MEMBERS / "inputs.json"
GEOMETRY_REFERENCE = PACKET / "member-screen-attempt02/four-screw-layout01/geometry.json"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ASSESSMENT = GRAVITY / "operator-assessment.json"
COMPARISON = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = COMPARISON.with_name("response.npz")
METHOD = PACKET / "member_stability.py"
DURATION = HERE / "member-duration.py"
FRAME_MAP = (PACKET.parent / "evaluation-resume-2026-09-24"
             / "current-frame-timber-material-frame-map-attempt01"
             / "current-frame-timber-material-frame-map.json")
MATERIALS = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
EXCLUDED = {"knee_outer_left_spine", "knee_outer_right_spine"}
SCENARIOS = {"cd1": 1.0, "cd1_25": 1.25}
STRENGTH_KEYS = {"Fb_star_mpa", "Ft_mpa", "Fc_star_mpa", "Fv_mpa"}
PINS = {
    REPORT: "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    ARRAYS: "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    GEOMETRY: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    GEOMETRY_REFERENCE: "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    INPUTS: "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    METHOD: "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    DURATION: "4407e780ade7a5f4f08eb586b6aea15130a6dd81ef747f535562a812f4a10c6d",
    PACKET / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    PACKET / "bottom_corner_checks.py": "5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26",
    PACKET / "top_corner_actions.py": "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    PACKET / "frame_state_contract.py": "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
    ROOT / "fea/reinforced_timber_resistance.py": "d4e8302d39beb9f53c70fa264762c59c231f6e6b086cb866906ca39eeab9cfbc",
    ROOT / "scripts/floor_taper_checks.py": "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    ROOT / "fea/current_response_materials.py": "72af0456272d91282928014d8fde557d347e36df6b7bdf23bcc41ef923d0d135",
    ROOT / "fea/wood_joint_patch_materials.py": "ecbbd11a8a0e99ece69aeb5cb4159e7cf17e0aa18c509c78b5c8f5a2e573ae78",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    PACKET.parent / "upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf":
        "6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100",
}
# This classifier is an independently consumed input to this producer. Its pin
# must never be inserted into, or required from, member_screen's source report.
CLASSIFIER_PINS = {FRAME_MAP: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409"}
FLAGS = {
    "source_acceptance_transferred": False,
    "duration_adoption_complete": False,
    "permanent_load_check_included": False,
    "actual_pressure_placement_refreshed": False,
    "complete_member_acceptance": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "geometry_changed": False,
    "native_launch": False,
    "frame_solve": False,
    "CAD_rebuilt": False,
    "tests_run": False,
    "review_run": False,
}
NORMAL_METRICS = {
    "end_only_normal_ratio": ("end_supported_only", "interaction_ratio"),
    "timber_braced_normal_ratio": ("existing_timber_weak_restraints", "interaction_ratio"),
    "end_only_stability_3_9_4_ratio": ("end_supported_only", "stability_3_9_4_ratio"),
    "timber_braced_stability_3_9_4_ratio": ("existing_timber_weak_restraints", "stability_3_9_4_ratio"),
}
SHEAR_METRICS = {
    "shear_face_ratio": "face_lower_bound_ratio",
    "shear_component_bound_ratio": "component_rectangle_upper_bound_ratio",
    "coefficient5_sensitivity_ratio": "coefficient5_isotropic_sensitivity_ratio",
    "RT_swap_fixed_action_face_ratio": "RT_swap_fixed_action_face_ratio",
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


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed source changed: " + str(path))


def source_map(pins):
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in sorted(pins.items())}


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "preserved arithmetic import unavailable")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def finite_wrench(np, value, label):
    value = np.asarray(value, dtype=float)
    require(value.shape == (6,) and np.isfinite(value).all(), label + " is not a finite wrench")
    return value


def close(np, value, force_tol, moment_tol, label):
    value = finite_wrench(np, value, label)
    require(np.max(abs(value[:3])) <= force_tol and np.max(abs(value[3:])) <= moment_tol,
            label + " exceeds the preserved tolerance")


def load_sources(pins):
    report, inputs, assessment, comparison = (read(path) for path in (REPORT, INPUTS, ASSESSMENT, COMPARISON))
    require(report["schema"] == "same_state_six_case_timber_member_screen/v1"
            and report["status"] == "COMPLETE_CONDITIONAL_ELEMENTARY_MEMBER_SCREENS_NOT_QUALIFICATION"
            and report["complete_member_acceptance"] is False and report["physical_release"] is False,
            "fresh member action extraction incomplete")
    require(assessment["schema"] == "knee-bridge-gravity-operators/v1"
            and assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
            and assessment["operator_ready"] is True and assessment["gravity_delta_in_proposal_operators"] is True,
            "completed new gravity operators required")
    require(report["producer_sha256"] == inputs["producer_sha256"] == PINS[PACKET / "member_screen.py"]
            == report["output_sha256"]["producer.py.snapshot"], "member producer binding differs")
    require(tuple(case["case_id"] for case in report["cases"]) == tuple(assessment["case_ids"]) == CASES
            and inputs["selected_force_keys"] == [case + "_gap_raw_force_n" for case in CASES]
            and all(case["source_force_key"] == case["case_id"] + "_gap_raw_force_n" for case in report["cases"]),
            "six nominal force keys differ")
    require(report["clearance_input_directory"] == COMPARISON.parent.relative_to(ROOT).as_posix()
            and report["frame_operator_directory"] == comparison["frame_operator_directory"]
            == GRAVITY.relative_to(ROOT).as_posix(), "member/response/operator directories differ")
    require(report["same_state_dead_load_factor"] == inputs["same_state_dead_load_factor"]
            == assessment["dead_load_factor"] == comparison["dead_load_factor"] == 1.1110134616260479
            and assessment["modeled_mass_kg"] == comparison["modeled_mass_kg"] == 225.19791414318078,
            "fresh mass/dead factor differs")
    require(comparison["response_sha256"] == PINS[RESPONSE]
            and comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1.0
            and comparison["source_climber_weight_lb"] == 250.0, "fresh nominal response binding differs")
    for record in (report, inputs, assessment, comparison):
        for relative, digest in record["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for directory, record in ((MEMBERS, report), (GRAVITY, assessment)):
        for relative, digest in record["output_sha256"].items():
            path = (directory / relative).resolve()
            require(path.is_relative_to(directory), "reported output leaves its source packet")
            bind(pins, path, digest)
    # Only sources actually consumed by member_screen are required in its closure.
    for path in (COMPARISON, RESPONSE, ASSESSMENT, MATERIALS,
                 *(GRAVITY / name for name in ("model.json", "row-identities.json", "operators.npz"))):
        require(report["source_sha256"].get(path.relative_to(ROOT).as_posix()) == pins[path],
                "member actions have another consumed source: " + str(path))
    for name in ("model.json", "row-identities.json", "operators.npz"):
        path = GRAVITY / name
        require(comparison["source_sha256"].get(path.relative_to(ROOT).as_posix()) == pins[path]
                == assessment["output_sha256"][name], "frame/gravity operator binding differs")
    require(comparison["source_sha256"].get(ASSESSMENT.relative_to(ROOT).as_posix()) == PINS[ASSESSMENT],
            "frame has another gravity assessment")
    authenticate(pins)
    authenticate(CLASSIFIER_PINS)
    model, rows, packet, materials = (read(path) for path in
                                    (GRAVITY / "model.json", GRAVITY / "row-identities.json", GEOMETRY, MATERIALS))
    records = packet["members"]
    frame_ids = [entry["member_id"] for entry in read(FRAME_MAP)["members"]]
    require(len(frame_ids) == len(set(frame_ids)) == 20 and set(frame_ids).issubset(records),
            "independent 20-frame classifier differs")
    require(len(records) == 44 and EXCLUDED.issubset(records)
            and all(record["member_kind"] == "timber" for record in records.values()),
            "44-source timber census differs")
    selected = set(records) - EXCLUDED
    require(len(selected) == 42 and len(selected & set(frame_ids)) == 20
            and len(selected - set(frame_ids)) == 22, "42 unchanged bodies must be 20 frame + 22 blocks")
    require(set(model["body_names"]) - set(records) ==
            {"kicker_left", "kicker_right", "main_lower_left", "main_lower_right", "main_upper_left", "main_upper_right"},
            "plywood/timber body partition differs")
    require(inputs["source_model_revision"] == model["development_revision"]
            and model["dead_load_factor"] == comparison["dead_load_factor"]
            and model["modeled_mass_kg"] == comparison["modeled_mass_kg"], "member/model metadata differ")
    for body in selected:
        record = records[body]
        path = (ROOT / record["current_finished_step"]).resolve()
        digest = record["current_finished_step_sha256"]
        require(report["source_sha256"].get(path.relative_to(ROOT).as_posix()) == digest,
                "unchanged finished geometry source not bound: " + body)
        bind(pins, path, digest)
    for case in report["cases"]:
        ids = [entry["member"] for entry in case["members"]]
        require(len(ids) == len(set(ids)) == 44 and set(ids) == set(records), "fresh case timber census differs")
    authenticate(pins)
    return report, comparison, model, rows, records, materials, set(frame_ids), sorted(selected)


def duration_shear(base, cd):
    """Reuse member-duration's fixed-action ratio scaling, including diagnostics."""
    result = {key: value / cd if key.endswith("_ratio") else value for key, value in base.items()}
    result["strength_allowance_mpa"] = base["strength_allowance_mpa"] * cd
    face, bound = result["face_lower_bound_ratio"], result["component_rectangle_upper_bound_ratio"]
    result["disposition"] = ("FACE_EXCEEDS_DECLARED_ALLOWANCE" if face > 1
                             else "RECTANGLE_BOUND_BELOW_ALLOWANCE" if bound <= 1
                             else "CONSERVATIVE_COMPONENT_BOUND_EXCEEDS_ONLY")
    return result


def body_parameters(np, method, body, record, arrays, rows, timber_ids, materials, model, frame_ids):
    geometry = record["geometry"]
    basis = method.member.basis(geometry)
    require(basis.shape == (3, 3) and np.isfinite(basis).all()
            and np.max(abs(basis @ basis.T - np.eye(3))) < 1e-8, "invalid section frame: " + body)
    orientation = model["material_binding"]["orientation_overrides"][body]
    axes = orientation["material_axes_global_xyz"]
    require(np.max(abs(np.asarray(axes["L"]) - basis[0])) < 1e-8, "frozen grain/section frame differs: " + body)
    ru, rv = (abs(float(np.asarray(axes["R"]) @ basis[i])) for i in (1, 2))
    aligned = max(ru, rv) > 1 - 1e-7
    ratio = .064 / .078 if ru > rv else .078 / .064
    length = float(np.linalg.norm(np.asarray(geometry["end"]) - geometry["start"]))
    rectangles, stations = record["rectangle_at_station"], record["stations_mm"]
    require(length > 0 and len(rectangles) == len(stations) > 0
            and np.isfinite(stations).all() and all(a <= b for a, b in pairwise(stations)),
            "invalid saved section census: " + body)
    intact = [rectangle for rectangle in rectangles if rectangle["status"].startswith("BORE_FREE_")]
    short, long = (map(float, np.min([sorted(r["width_depth_mm"]) for r in intact], axis=0))
                   if intact else sorted((geometry["width_mm"], geometry["depth_mm"])))
    candidates = method.brace_candidates(body, record, arrays, rows, timber_ids)
    restraint_stations = sorted({0.0, length, *(candidate["station_mm"] for candidate in candidates)})
    weak_bay = max(b - a for a, b in pairwise(restraint_stations))
    binding, base = method.references(body, geometry, materials)
    references = {name: {key: value * cd if key in STRENGTH_KEYS else value for key, value in base.items()}
                  for name, cd in SCENARIOS.items()}
    require(all(ref["Emin_mpa"] == base["Emin_mpa"] and ref["Fc_perp_mpa"] == base["Fc_perp_mpa"]
                for ref in references.values()), "duration changed excluded references")
    kernels = {name: {restraint: method.stability_kernel(short, long, length, weak, ref)
                      for restraint, weak in (("end_supported_only", length),
                                              ("existing_timber_weak_restraints", weak_bay))}
               for name, ref in references.items()}
    for restraint in kernels["cd1"]:
        one, peak = kernels["cd1"][restraint], kernels["cd1_25"][restraint]
        require(all(one[key] == peak[key] for key in
                    ("FcE_strong_weak_mpa", "FbE_mpa", "beam_slenderness", "column_slenderness_strong_weak")),
                "duration changed Euler or slenderness references")
    return {"member": body, "kind": "frame" if body in frame_ids else "block",
            "source_geometry": geometry, "finished_step": record["current_finished_step"],
            "finished_step_sha256": record["current_finished_step_sha256"],
            "material_strength_binding": binding, "references": references, "stability_kernels": kernels,
            "frozen_elastic_orientation": orientation,
            "torsion_orientation": {"aligned": aligned, "radial_abs_projection_on_u_v": [ru, rv],
                                    "source_GLR_over_EL": .064, "source_GLT_over_EL": .078,
                                    "Gu_over_Gv": ratio,
                                    "stress_distribution": "aligned_source_longitudinal_orthotropy" if aligned
                                    else "equal_longitudinal_shear_moduli_rectangle_approximation"},
            "length_mm": length, "minimum_intact_rectangle_short_long_mm": [short, long],
            "source_bolt_weak_restraint_candidates": candidates, "maximum_candidate_weak_bay_mm": weak_bay,
            "section_status_trace_counts": {}, "scenario_exception_counts": {}, "peaks": {},
            "whole_member_or_local_opening_qualification": False}


def validate_actions(np, method, body, case, index, record, arrays, model, rows, D, F, W, labels, raw, source):
    actions = method.bottom.saved_actions(body, case, record, arrays)
    geometry, basis = record["geometry"], method.member.basis(record["geometry"])
    nodes = sorted(set(model["body_nodes"][body]))
    datum = np.mean([model["physical_node_coordinates_mm"][str(node)] for node in nodes], axis=0)
    body_index = model["body_names"].index(body)
    projection = D[:, 6 * body_index:6 * body_index + 6]
    incident = [row["row"] for row in rows if body in
                (row["ownership"]["first_body"], row["ownership"]["second_body"])]
    connectors = [action for action in actions if action["row"] >= 0]
    require(len(connectors) == len(incident) and {action["row"] for action in connectors} == set(incident),
            "saved incident-row inventory differs: " + body)
    unowned = np.ones(len(rows), dtype=bool)
    unowned[incident] = False
    require(np.max(abs(projection[unowned])) < 1e-12, "hidden body connector action")
    for action in connectors:
        row, ownership = rows[action["row"]], rows[action["row"]]["ownership"]
        other = ownership["second_body"] if ownership["first_body"] == body else ownership["first_body"]
        require(action["source_id"] == row["row_id"] and action["role"] == ownership["role"]
                and action["other_body"] == other
                and np.max(abs(np.asarray(action["point_mm"]) - ownership["point_mm"])) < 1e-7,
                "saved physical row placement/ownership differs")
        expected = -projection[action["row"]] * raw[action["row"]]
        expected = expected * [1, 1, 1, 1000, 1000, 1000]
        close(np, method.accounting.wrench([action], datum) - expected, 1e-7, 1e-5,
              "saved action/new full-D force and moment")
    loads = [action for action in actions if action["row"] < 0]
    require(len(loads) == len(nodes) and {action["source_id"] for action in loads}
            == {"body_load_node_" + str(node) for node in nodes}
            and all(action["role"] == "discrete_body_load" for action in loads), "saved nodal load census differs")
    nodal = {node: np.zeros(3) for node in nodes}
    selected = [(i, node, dof - 1) for i, (node, dof) in enumerate(labels) if node in nodal]
    require(len(selected) == 3 * len(nodes)
            and {(node, dof) for _, node, dof in selected} == {(node, dof) for node in nodes for dof in range(3)},
            "fresh physical load DOF census differs")
    for row, node, dof in selected:
        nodal[node][dof] = model["dead_load_factor"] * F[row, 2 * index] + F[row, 2 * index + 1]
    for action in loads:
        node = int(action["source_id"].removeprefix("body_load_node_"))
        require(np.max(abs(np.asarray(action["point_mm"]) - model["physical_node_coordinates_mm"][str(node)])) < 1e-7
                and np.max(abs(np.asarray(action["force_n"]) - nodal[node])) < 1e-7
                and np.max(abs(np.asarray(action["free_moment_nmm"]))) == 0.0, "saved nodal action/fresh F differs")
    for action in actions:
        station = float(basis[0] @ (np.asarray(action["point_mm"]) - geometry["start"]))
        require(abs(station - action["station_mm"]) < 1e-7
                and np.isfinite(action["footprint_mm"]).all(), "saved signed-action station/footprint differs")
    load_wrench = method.accounting.wrench(loads, datum)
    expected_load = (model["dead_load_factor"] * W[6 * body_index:6 * body_index + 6, 2 * index]
                     + W[6 * body_index:6 * body_index + 6, 2 * index + 1]) * [1, 1, 1, 1000, 1000, 1000]
    close(np, load_wrench - expected_load, 1e-6, 1e-6, "fresh F/W load wrench")
    closure = method.accounting.wrench(actions, datum)
    close(np, closure, .1, 2.0, "fresh whole-body balance")
    saved = source["whole_member_balance"]
    close(np, closure - np.r_[saved["force_xyz_n"], saved["moment_xyz_nmm"]], 1e-7, 1e-5,
          "saved report/reconstructed whole-body balance")
    negative = arrays[case + "__" + body + "__internal_negative_grain_u_v"]
    positive = arrays[case + "__" + body + "__internal_positive_grain_u_v"]
    count = 2 * len(record["rectangle_at_station"])
    require(negative.shape == positive.shape == (count, 6) and np.isfinite(negative).all()
            and np.isfinite(positive).all() and source["cut_trace_count"] == count
            and source["point_action_count"] == len(actions), "saved signed-cut/action dimensions differ")
    require(np.max(abs(negative + positive)) < 1e-6, "opposite signed cut halves disagree")
    minus, plus, _positions, _before = method.member.cut_vectors(actions, geometry, record["stations_mm"])
    for actual, recovered in ((negative, minus), (positive, plus)):
        local = np.column_stack((recovered[:, :3] @ basis.T, recovered[:, 3:] @ basis.T))
        require(np.max(abs(actual[:, :3] - local[:, :3])) <= 1e-7
                and np.max(abs(actual[:, 3:] - local[:, 3:])) <= 1e-5, "saved cut/new signed-action reconstruction differs")
    return negative, {"case_id": case, "member": body, "datum_xyz_mm": datum.tolist(),
                      "whole_body_residual_n_nmm": closure.tolist(),
                      "fresh_F_W_residual_n_nmm": (load_wrench - expected_load).tolist(),
                      "cut_trace_count": count, "point_action_count": len(actions)}


def metric_values(scenario):
    if scenario["normal"] is None:
        return {key: None for key in (*NORMAL_METRICS, *SHEAR_METRICS)}
    values = {key: scenario["normal"][restraint][field] for key, (restraint, field) in NORMAL_METRICS.items()}
    values.update({key: scenario["shear"].get(field) for key, field in SHEAR_METRICS.items()})
    return values


def collect(record, peaks, exceptions):
    witness = {key: record[key] for key in ("member", "case_id", "cut_array_index", "station_mm", "trace",
                                           "section_status", "signed_action_at_rectangle_centroid_n_nmm")}
    for name, scenario in record["scenarios"].items():
        maxima = peaks.setdefault(name, {})
        counts = exceptions.setdefault(name, Counter())
        if scenario["normal"] is None:
            counts["unsupported_local_section_traces"] += 1
            continue
        for restraint, check in scenario["normal"].items():
            counts[restraint + "/null_interaction"] += check["interaction_ratio"] is None
            counts[restraint + "/outside_slenderness_domain"] += not check["within_slenderness_limits"]
            counts[restraint + "/nonpositive_Euler_denominator"] += not check["Euler_denominators_positive"]
            counts[restraint + "/checked_exceedance"] += check["ratio_exceeds_one"]
        counts["shear_face_exceedance"] += scenario["shear"]["face_lower_bound_ratio"] > 1
        counts["shear_component_bound_exceedance"] += scenario["shear"]["component_rectangle_upper_bound_ratio"] > 1
        for key, value in metric_values(scenario).items():
            if value is not None and (key not in maxima or value > maxima[key]["value"]):
                maxima[key] = {**witness, "value": value}


def build(output):
    """Replay saved signed cuts once; only the parent executes this API."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    authenticate(pins)
    authenticate(CLASSIFIER_PINS)
    previous_path, previous_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(PACKET), str(ROOT)]
    sys.dont_write_bytecode = True
    try:
        import numpy as np

        report, comparison, model, rows, records, materials, frame_ids, selected = load_sources(pins)
        method = module(METHOD, "fresh_unchanged_member_stability")
        duration = module(DURATION, "fresh_member_duration_basis")
        for helper, path in ((method.member, PACKET / "member_screen.py"),
                             (method.bottom, PACKET / "bottom_corner_checks.py"),
                             (method.accounting, PACKET / "top_corner_actions.py"),
                             (method.frame_contract, PACKET / "frame_state_contract.py")):
            require(Path(helper.__file__).resolve() == path, "arithmetic import resolved to another helper")
        require(duration.CD == SCENARIOS["cd1_25"], "existing conditional duration hypothesis changed")
        force_scope = method.frame_contract.force_state_scope(comparison)
        require(report["source_force_state_scope"] == force_scope, "member/frame force-state scopes differ")
        require(method.member.DOFS.resolve() in pins, "physical DOF labels missing from consumed source closure")
        labels = [tuple(map(int, line.split("."))) for line in method.member.DOFS.read_text().splitlines() if line.strip()]
        require(len(labels) == len(set(labels)) and all(dof in (1, 2, 3) for _, dof in labels), "invalid physical DOF labels")
        authenticate(pins)
        output.mkdir(parents=True, exist_ok=False)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        summaries, balances, global_peaks, global_exceptions, status_counts = [], [], {}, {}, Counter()
        trace_count = intact_count = 0
        with np.load(ARRAYS, allow_pickle=False) as arrays, \
                np.load(RESPONSE, allow_pickle=False) as responses, \
                np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators, \
                (output / "same-cut-states.jsonl").open("w") as stream:
            D, F, W = (operators[name] for name in ("D", "F", "W"))
            require([row["row"] for row in rows] == list(range(len(rows)))
                    and D.shape == (len(rows), 6 * len(model["body_names"]))
                    and F.shape == (len(labels), 12) and W.shape == (6 * len(model["body_names"]), 12),
                    "fresh physical operator dimensions differ")
            raw_cases = {case: responses[case + "_gap_raw_force_n"] for case in CASES}
            require(all(raw.shape == (len(rows),) and np.isfinite(raw).all() for raw in raw_cases.values()),
                    "invalid new nominal raw-force vector")
            witnesses = {(case["case_id"], entry["member"]): entry
                         for case in report["cases"] for entry in case["members"]}
            for body in sorted(selected, key=lambda name: (name not in frame_ids, name)):
                record = records[body]
                summary = body_parameters(np, method, body, record, arrays, rows, set(records), materials, model, frame_ids)
                basis = method.member.basis(record["geometry"])
                own_status, own_peaks, own_exceptions = Counter(), {}, {}
                for index, case in enumerate(CASES):
                    negative, receipt = validate_actions(np, method, body, case, index, record, arrays, model,
                                                        rows, D, F, W, labels, raw_cases[case], witnesses[case, body])
                    balances.append(receipt)
                    for cut_index, original in enumerate(negative):
                        rectangle = record["rectangle_at_station"][cut_index // 2]
                        station = float(record["stations_mm"][cut_index // 2])
                        intact = rectangle["status"].startswith("BORE_FREE_")
                        value = original.copy()
                        offset, dimensions = None, None
                        if intact:
                            dimensions = rectangle["width_depth_mm"]
                            require(len(dimensions) == 2 and min(dimensions) > 0 and np.isfinite(dimensions).all(),
                                    "invalid saved intact rectangle")
                            datum = np.asarray(record["geometry"]["start"]) + station * basis[0]
                            offset = basis @ (np.asarray(rectangle["centroid_xyz_mm"]) - datum)
                            require(np.isfinite(offset).all(), "invalid saved rectangle centroid")
                            value[3:] -= np.cross(offset, value[:3])
                            shear = method.shear_check(value.tolist(), *dimensions, summary["references"]["cd1"]["Fv_mpa"],
                                                       summary["torsion_orientation"]["aligned"],
                                                       summary["torsion_orientation"]["Gu_over_Gv"])
                            scenarios = {name: {"normal": {restraint: method.normal_check(value.tolist(), *dimensions, kernel,
                                                         summary["references"][name])
                                                   for restraint, kernel in summary["stability_kernels"][name].items()},
                                                "shear": duration_shear(shear, cd)} for name, cd in SCENARIOS.items()}
                            for restraint in scenarios["cd1"]["normal"]:
                                base, peak = (scenarios[name]["normal"][restraint] for name in SCENARIOS)
                                require(all(base[key] == peak[key] for key in
                                            ("within_slenderness_limits", "Euler_denominators_positive", "stability_3_9_4_ratio")),
                                        "duration changed fixed-action stability/domain")
                        else:
                            scenarios = {name: {"normal": None, "shear": None} for name in SCENARIOS}
                        state = {"member": body, "kind": summary["kind"], "case_id": case,
                                 "cut_array_index": cut_index, "station_mm": station,
                                 "trace": "before" if cut_index % 2 == 0 else "after",
                                 "cut_side": "negative_grain_half_N_tension_positive",
                                 "section_status": rectangle["status"], "rectangle_width_depth_mm": dimensions,
                                 "rectangle_centroid_xyz_mm": rectangle.get("centroid_xyz_mm"),
                                 "centroid_offset_grain_u_v_mm": None if offset is None else offset.tolist(),
                                 "centroid_shift_applied": intact,
                                 "signed_action_at_source_cut_n_nmm": original.tolist(),
                                 "signed_action_at_rectangle_centroid_n_nmm": value.tolist(),
                                 "scenarios": scenarios, "physical_release": False}
                        stream.write(json.dumps(state, separators=(",", ":"), allow_nan=False) + "\n")
                        trace_count += 1
                        intact_count += intact
                        own_status[rectangle["status"]] += 1
                        status_counts[rectangle["status"]] += 1
                        collect(state, own_peaks, own_exceptions)
                        collect(state, global_peaks, global_exceptions)
                summary.update({"section_status_trace_counts": dict(own_status), "peaks": own_peaks,
                                "scenario_exception_counts": {name: dict(count) for name, count in own_exceptions.items()}})
                summaries.append(summary)
                print(json.dumps({"member": body, "completed_members": len(summaries),
                                  "completed_body_case_balances": len(balances)}), flush=True)
        require(len(summaries) == 42 and {summary["member"] for summary in summaries} == set(selected)
                and len(balances) == len({(row["member"], row["case_id"]) for row in balances}) == 42 * 6,
                "42 × 6 whole-body completion census differs")
        expected_traces = sum(2 * len(records[body]["stations_mm"]) * len(CASES) for body in selected)
        require(trace_count == expected_traces and sum(status_counts.values()) == trace_count,
                "complete signed-cut/status census differs")
        authenticate(pins)
        authenticate(CLASSIFIER_PINS)
        write(output / "body-balances.json", balances)
        top = next(summary for summary in summaries if summary["member"] == "base_rail_top")
        result = {
            "schema": "knee_bridge_unchanged_timber_references/v1",
            "status": "COMPLETE_FRESH_CONDITIONAL_REFERENCES_NOT_ACCEPTANCE",
            "candidate": model["candidate"], "producer_sha256": pins[Path(__file__).resolve()],
            "case_ids": CASES, "excluded_modified_bodies": sorted(EXCLUDED), "plywood_screened": False,
            "selected_body_ids": selected, "members": summaries,
            "artifacts": {"signed_cut_states": "same-cut-states.jsonl", "whole_body_balances": "body-balances.json"},
            "counts": {"members": 42, "frame_members": 20, "blocks": 22, "cases": 6,
                       "whole_body_balances": len(balances), "signed_cut_traces": trace_count,
                       "bore_free_signed_cut_traces": intact_count,
                       "unsupported_local_section_traces": trace_count - intact_count},
            "section_status_trace_counts": dict(status_counts), "global_peaks": global_peaks,
            "scenario_exception_counts": {name: dict(count) for name, count in global_exceptions.items()},
            "top_rail_point_action_diagnostic": {"member": "base_rail_top", "point_action_reference_only": True,
                "actual_pressure_placement_refreshed": False, "peaks": top["peaks"],
                "scenario_exception_counts": top["scenario_exception_counts"],
                "parent_next_action": "Refresh actual pressure placement separately; retain this point-action diagnostic."},
            "source_member_report_sha256": PINS[REPORT], "source_member_report_closure": report["source_sha256"],
            "source_sha256": source_map(pins), "classifier_source_sha256": source_map(CLASSIFIER_PINS),
            "classifier_role": "Independent 20-frame/24-block identifier partition only; no member-report provenance or material orientation is inferred from the classifier.",
            "source_force_scope": force_scope, "source_comparison_sha256": PINS[COMPARISON],
            "source_response_sha256": PINS[RESPONSE], "source_gravity_assessment_sha256": PINS[ASSESSMENT],
            "modeled_mass_kg": model["modeled_mass_kg"], "same_state_dead_load_factor": model["dead_load_factor"],
            "load_hypothesis": {"wood_strength_CD_scenarios": SCENARIOS, "cumulative_full_peak_load_days_max": 7,
                                "original_250_lb_times_2_signed_300_N_100_mm_lever": True,
                                "duration_changes_only": sorted(STRENGTH_KEYS), "Emin_and_Fcperp_unchanged": True,
                                "permanent_load_CD": .9, "permanent_load_check_included": False,
                                "duration_adoption_complete": False, "force_or_elastic_or_hardware_multiplier": 1.0},
            "primary_sources": {"stability": method.PRIMARY, "duration": duration.PRIMARY},
            "restraint_assumptions": {
                "end_supported_only": "Both ends laterally restrained in both section directions; no sway, K=1, grain-axis end rotation prevented; full member span; no panel restraint credit.",
                "existing_timber_weak_restraints": "Same end conditions; original bilateral timber stations or tension ties with their compression counterface shorten weak column bays only, conditional on braced receivers and opening slack taken up. Strong column and beam spans remain full length.",
                "brace_receiver_inventory": "All 44 source timber receiver identifiers are retained for the original conditional brace candidates; only the 42 unchanged bodies are screened.",
                "reduced_profile": "Uniform minimum intact bore-free rectangle over the full span; recess, holes and terminal profiles keep their local-section limits.",
            },
            "limits": [
                "Fresh raw forces, current full-D point wrenches/free couples, fresh nodal F/W loads and saved signed cuts are independently joined for each of 252 body cases.",
                "The source geometry is byte-identical to the frozen four-screw packet; the modified six-bore outer spines remain Fermat's separate scope.",
                "Every before/after signed cut and centroid offset is retained. Nonrectangular/local opening sections keep null references; domain nulls, checked exceedances and component-bound sensitivities are not suppressed.",
                "C_D=1.25 scales only Fb/Ft/Fc/Fv. The seven-day cumulative full-peak hypothesis is conditional and unobserved; the separate permanent-load comparison remains pending.",
                "Aligned longitudinal orthotropy, the nonaligned equal-shear-modulus approximation and the existing fixed-action R/T diagnostic remain the preserved member_stability hypotheses.",
                "No brace stiffness/capacity, plywood sharing, local opening, actual pressure distribution, formal torsion resistance or complete member/joint acceptance is established.",
            ], "runtime": {"python": sys.version.split()[0], "numpy": np.__version__}, **FLAGS,
        }
        write(output / "checks.json", result)
        authenticate(pins)
        authenticate(CLASSIFIER_PINS)
        write(output / "receipt.json", {"producer_sha256": result["producer_sha256"],
              "source_sha256": source_map(pins), "classifier_source_sha256": source_map(CLASSIFIER_PINS),
              "output_sha256": {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()},
              "source_unchanged_before_and_after_write": True, "counts": result["counts"], **FLAGS})
        authenticate(pins)
        authenticate(CLASSIFIER_PINS)
        return result
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "checks_sha256": sha(args.output / "checks.json")}))
