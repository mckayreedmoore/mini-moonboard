"""Isolate/replay only the frozen top rail; consume saved forces, never solve.

Future replay is limited to a parent-produced load-lever response with unchanged
geometry, connector laws/operators, gravity, and top-rail nodal loads.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = PACKET.parents[3]
MEMBERS = PACKET / "member-screen-attempt02/four-screw-layout01"
CHECKS = PACKET / "member-stability-attempt01/four-screw-layout01/checks.json"
FRAME = HERE / "operators-attempt02"
RESPONSE = HERE / "frame-250-attempt02"
RAW = HERE / "rawlocal/top-rail-limit"
BODY = "base_rail_top"
MATERIALS = PACKET.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
PINS = {
    RESPONSE / "comparison.json": "bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca",
    RESPONSE / "response.npz": "0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7",
    FRAME / "operators.npz": "c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3",
    FRAME / "model.json": "b5f9b87b70c4a9920372a3443a55e37dfe34351fb9ac8210b299c1360fb93626",
    FRAME / "row-identities.json": "cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27",
    MEMBERS / "member-results.json": "54f3888581717d2579b0dd6ea7dcd754501ec2890a9f4869059f476f2d0965c5",
    MEMBERS / "action-section-arrays.npz": "ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf",
    MEMBERS / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    CHECKS: "aceebc0beaee1cc178450b52b2a16a32924803c3210dc0c115c0fee7a3a7c574",
    PACKET / "member_screen.py": "5ecbfcebc8ea45bba83961305735f919d5e6caa3862625befec875655dd0b5d9",
    PACKET / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    PACKET / "top_corner_actions.py": "bfe51728521b620e54fa23822f4e3b3cee320457503580cf95ab439863327bd5",
    PACKET / "bottom_corner_checks.py": "5df7a264354e1488c2a68332820fe927e8dcb1fa9721111ec8fac5c00ad19e26",
    PACKET / "frame_state_contract.py": "22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5",
    ROOT / "scripts/floor_taper_checks.py": "bf15d8983b42d95dda0d0329bc2d8c2664f9c146813f21e1a0cc8f0f6a3bf1c3",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args):
    pins = dict(PINS)
    pins[Path(__file__).resolve()] = sha(Path(__file__))
    require(RAW.resolve() in args.output.resolve().parents, "output must be a fresh child of rawlocal/top-rail-limit")
    require(not args.output.exists(), "preserve existing output; choose a fresh child")
    supplied = (args.frame, args.clearance, args.operators_sha256, args.comparison_sha256, args.response_sha256)
    future = any(x is not None for x in supplied)
    require(not future or all(x is not None for x in supplied), "replay requires both directories and all three parent hashes")
    frame, clearance = (args.frame.resolve(), args.clearance.resolve()) if future else (FRAME, RESPONSE)
    if future:
        require(sha(clearance / "comparison.json") == args.comparison_sha256, "changed parent comparison")
        comparison = read(clearance / "comparison.json")
        assessment_path = frame / "operator-assessment.json"
        assessment_hash = comparison["source_sha256"][str(assessment_path.relative_to(ROOT))]
        require(sha(assessment_path) == assessment_hash, "changed parent operator assessment")
        assessment = read(assessment_path)
        require(assessment["schema"] == "declared_front_face_force_lever/v1", "unsupported preparation schema")
        require(assessment["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS"
                and assessment["geometry_changed"] is False, "load-lever preparation is not applicable")
        require(assessment["output_sha256"]["operators.npz"] == args.operators_sha256,
                "preparation/operator hash mismatch")
        pins.update({frame / "operators.npz": args.operators_sha256,
                     frame / "model.json": assessment["output_sha256"]["model.json"],
                     frame / "row-identities.json": PINS[FRAME / "row-identities.json"],
                     assessment_path: assessment_hash,
                     clearance / "comparison.json": args.comparison_sha256,
                     clearance / "response.npz": args.response_sha256})
    for path, digest in pins.items():
        require(sha(path) == digest, "changed consumed input: " + str(path))
    if future:
        model_payload = read(frame / "model.json")
        scenario = model_payload.pop("diagnostic_load_scenario")
        require(model_payload == read(FRAME / "model.json"), "physical model payload changed")
        require(scenario == assessment["diagnostic_load_scenario"], "load-scenario metadata mismatch")

    # Reuse the maintained cut partition, action restoration, and stress field.
    sys.path.insert(0, str(PACKET))
    import member_stability as method
    import numpy as np

    member, accounting = method.member, method.accounting
    source, comparison = read(RESPONSE / "comparison.json"), read(clearance / "comparison.json")
    scope = method.frame_contract.force_state_scope(comparison)
    require(comparison["frame_operator_directory"] == str(frame.relative_to(ROOT)), "response/operator directory mismatch")
    require(comparison["response_sha256"] == pins[clearance / "response.npz"], "response hash mismatch")
    for name in ("operators.npz", "model.json", "row-identities.json"):
        require(comparison["source_sha256"][str((frame / name).relative_to(ROOT))] == pins[frame / name], "response source mismatch: " + name)
    for key in ("dead_load_factor", "climber_load_scale", "source_climber_weight_lb", "comparison_climber_weight_lb"):
        require(comparison[key] == source[key], "load-lever-only replay changed " + key)
    require(comparison.get("horizontal_load_scale", 1.0) == source.get("horizontal_load_scale", 1.0), "horizontal force scale changed")
    for key in ("clearance_planes", "clearance_joint_hosts", "floor_footprints", "panel_screw_stiffness_n_per_mm"):
        require(comparison[key] == source[key], "connection/load-lever contract changed: " + key)

    report, saved_checks = read(MEMBERS / "member-results.json"), read(CHECKS)
    require(report["source_sha256"][str((RESPONSE / "comparison.json").relative_to(ROOT))] == PINS[RESPONSE / "comparison.json"], "mixed saved member source")
    for name in ("geometry.json", "action-section-arrays.npz"):
        require(report["output_sha256"][name] == PINS[MEMBERS / name], "member artifact binding changed")
    require(saved_checks["source_member_results_sha256"] == PINS[MEMBERS / "member-results.json"], "mixed stability source")
    record = read(MEMBERS / "geometry.json")["members"][BODY]
    geometry, model = record["geometry"], read(frame / "model.json")
    step = ROOT / record["current_finished_step"]
    pins[step] = record["current_finished_step_sha256"]
    require(sha(step) == pins[step], "finished STEP changed")
    reference = member.reference_values(BODY, geometry, read(MATERIALS))
    fv = reference["CF_only_reference_mpa"]["Fv_parallel"]
    basis = member.basis(geometry)
    radial = np.array(model["material_binding"]["orientation_overrides"][BODY]["material_axes_global_xyz"]["R"])
    require(abs(radial @ basis[1]) > 1 - 1e-7, "frozen R/u assignment changed")
    ratio = .064 / .078
    datum = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in model["body_nodes"][BODY]], axis=0)
    body_index = model["body_names"].index(BODY)
    body_slice = slice(6 * body_index, 6 * body_index + 6)
    positions = np.repeat(record["stations_mm"], 2)
    rectangles = record["rectangle_at_station"]
    states, case_peaks, balances, action_sets = [], [], [], {}
    with (np.load(MEMBERS / "action-section-arrays.npz", allow_pickle=False) as arrays,
          np.load(RESPONSE / "response.npz", allow_pickle=False) as source_response,
          np.load(clearance / "response.npz", allow_pickle=False) as responses,
          np.load(FRAME / "operators.npz", allow_pickle=False) as original,
          np.load(frame / "operators.npz", allow_pickle=False) as operators):
        D = operators["D"]
        require(D.shape == (1888, 300), "connector operator dimensions changed")
        for key in ("H", "D"):
            require(np.array_equal(operators[key], original[key]), "mechanical operator changed: " + key)
        for key in ("F", "e", "W"):
            require(np.array_equal(operators[key][:, ::2], original[key][:, ::2]), "gravity columns changed: " + key)
        # The top rail has no direct hold load. Preserve every rail nodal load,
        # including zero and signed consistent-load rows, rather than rescale it.
        labels = [tuple(map(int, x.split("."))) for x in member.DOFS.read_text().splitlines() if x.strip()]
        pins[member.DOFS] = report["source_sha256"][str(member.DOFS.relative_to(ROOT))]
        require(sha(member.DOFS) == pins[member.DOFS], "physical DOF map changed")
        load_indices = [i for i, (node, _dof) in enumerate(labels) if node in set(model["body_nodes"][BODY])]
        require(np.array_equal(operators["F"][load_indices], original["F"][load_indices]), "top-rail nodal load changed")
        require(np.array_equal(operators["W"][body_slice], original["W"][body_slice]), "top-rail load wrench changed")
        for case in method.CASES:
            key = case + "_gap_raw_force_n"
            raw = responses[key]
            require(raw.shape == (1888,) and np.isfinite(raw).all(), "invalid simultaneous force vector: " + case)
            actions = method.bottom.saved_actions(BODY, case, record, arrays)
            for action in actions:
                row = action["row"]
                if row < 0:
                    continue
                point = np.array(action["point_mm"])
                # Original point/free-couple decomposition and D must agree.
                expected = -original["D"][row, body_slice] * source_response[key][row]
                saved = accounting.wrench([action], datum)
                require(np.max(abs(saved[:3] - expected[:3])) < 1e-7 and np.max(abs(saved[3:] - 1000 * expected[3:])) < 1e-5, "saved point action/operator mismatch")
                if future:
                    value = -D[row, body_slice] * raw[row]
                    action["force_n"] = value[:3].tolist()
                    action["free_moment_nmm"] = (1000 * value[3:] - np.cross(point - datum, value[:3])).tolist()
            closure = accounting.wrench(actions, datum)
            require(np.max(abs(closure[:3])) < .1 and np.max(abs(closure[3:])) < 2, "top-rail balance failed: " + case)
            balances.append({"case_id": case, "residual_xyz_n_nmm": closure.tolist()})
            action_sets[case] = actions
            if future:
                minus, plus, replay_positions, _before = member.cut_vectors(actions, geometry, np.array(record["stations_mm"]))
                require(np.array_equal(replay_positions, positions), "station census changed")
                negative = np.c_[minus[:, :3] @ basis.T, minus[:, 3:] @ basis.T]
                positive = np.c_[plus[:, :3] @ basis.T, plus[:, 3:] @ basis.T]
            else:
                negative = arrays[case + "__" + BODY + "__internal_negative_grain_u_v"]
                positive = arrays[case + "__" + BODY + "__internal_positive_grain_u_v"]
            require(negative.shape == (len(positions), 6) and np.max(abs(negative + positive)) < 1e-6, "cut-side balance failed")
            own = []
            for index, value in enumerate(negative):
                rectangle = rectangles[index // 2]
                if not rectangle["status"].startswith("BORE_FREE_"):
                    continue
                value = value.copy()
                origin = np.array(geometry["start"]) + positions[index] * basis[0]
                offset = basis @ (np.array(rectangle["centroid_xyz_mm"]) - origin)
                value[3:] -= np.cross(offset, value[:3])
                shear = method.shear_check(value, *rectangle["width_depth_mm"], fv, True, ratio)
                state = {"case_id": case, "cut_array_index": index, "station_mm": float(positions[index]),
                         "trace": "before" if index % 2 == 0 else "after",
                         "section_status": rectangle["status"],
                         "N_Vu_Vv_n_T_Mu_Mv_nmm": value.tolist(), **shear}
                states.append(state)
                own.append(state)
            case_peaks.append(max(own, key=lambda x: x["face_lower_bound_ratio"]))
    peak = max(case_peaks, key=lambda x: x["face_lower_bound_ratio"])
    saved_peak = saved_checks["global_bore_free_peaks"]["shear_face_ratio"]
    if not future:
        require(peak["case_id"] == saved_peak["case_id"] and peak["cut_array_index"] == saved_peak["cut_array_index"] and abs(peak["face_lower_bound_ratio"] - saved_peak["shear_face_ratio"]) < 1e-12, "saved governing reference not reproduced")
    actions = action_sets[peak["case_id"]]
    cut = accounting.host_cut(actions, peak["station_mm"], geometry, peak["trace"] == "before")
    w, d = rectangles[peak["cut_array_index"] // 2]["width_depth_mm"]
    _n, vu, vv, torque, _mu, _mv = peak["N_Vu_Vv_n_T_Mu_Mv_nmm"]
    cu, cv = peak["torsion_coefficient_u_v_per_mm3"]
    su, sv = 1.5 * vu / (w * d), 1.5 * vv / (w * d)
    faces = [{"u_v_mm": [0, -d / 2], "tau_Lu_Lv_mpa": [su + torque * cu, 0]},
             {"u_v_mm": [0, d / 2], "tau_Lu_Lv_mpa": [su - torque * cu, 0]},
             {"u_v_mm": [-w / 2, 0], "tau_Lu_Lv_mpa": [0, sv - torque * cv]},
             {"u_v_mm": [w / 2, 0], "tau_Lu_Lv_mpa": [0, sv + torque * cv]}]
    receivers = []
    for other in sorted({a["other_body"] for a in actions if a["other_body"]}):
        selected = [a for a in actions if a["other_body"] == other]
        receivers.append({"other_body": other, "role_counts": dict(Counter(a["role"] for a in selected)),
                          "point_station_range_mm": [min(a["station_mm"] for a in selected), max(a["station_mm"] for a in selected)],
                          "footprint_station_range_mm": [min(a["footprint_mm"][0] for a in selected), max(a["footprint_mm"][1] for a in selected)],
                          "rows_by_role": {role: [a["row"] for a in selected if a["role"] == role] for role in sorted({a["role"] for a in selected})},
                          "source_ids": [a["source_id"] for a in selected],
                          "wrench_about_rail_node_mean_xyz_n_nmm": accounting.wrench(selected, datum).tolist()})
    require(all(sha(path) == digest for path, digest in pins.items()), "consumed input changed during arithmetic")
    args.output.mkdir(parents=True)
    with (args.output / "cuts.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "cut_array_index", "station_mm", "trace", "N_Vu_Vv_n_T_Mu_Mv_nmm", "face_lower_bound_ratio", "component_rectangle_upper_bound_ratio"])
        writer.writeheader()
        writer.writerows({k: row[k] for k in writer.fieldnames} for row in states)
    result = {"schema": "top_rail_saved_force_isolation/v1", "member": BODY,
              "mode": "parent_load_lever_replay" if future else "frozen_source_isolation",
              "source_sha256": {str(p.relative_to(ROOT)): h for p, h in pins.items()},
              "source_force_scope": scope, "same_state_dead_load_factor": comparison["dead_load_factor"],
              "counts": {"cases": 6, "members": 1, "stations": len(rectangles), "signed_cut_traces": len(positions) * 6, "bore_free_screened_traces": len(states), "point_actions_per_case": len(actions)},
              "material_reference": reference, "G_Lu_over_G_Lv": ratio,
              "peak": peak, "same_cut_face_midpoint_stresses": faces, "complete_signed_cut": cut,
              "case_peaks": case_peaks, "body_balances": balances, "receiver_roles": receivers,
              "bore_or_passage_exclusions": record["bore_or_passage_intervals"],
              "section_status_station_counts": dict(Counter(r["status"] for r in rectangles)),
              "baseline_governing_reference": saved_peak,
              "limits": ["Only the frozen sampled top-rail stations, both one-sided traces, and the six saved nominal-gap force states are evaluated.",
                         "Compatible face exceedance applies to the declared free-warping intact prism. Joint/contact/bolt/washer disturbed-region stresses, splitting, and bore/ligament resistance remain outside this screen.",
                         "Fv=180 psi, CD=1; the longitudinal shear allowance is explicitly applied to both components. No separate NDS torsion resistance or capacity credit is inferred.",
                         "A lower face ratio alone does not bound every interior point; the same-cut component bound and original local exclusions remain visible.",
                         "No stock observation, geometry modification, frame/native/mechanical solve, climber rating, or physical acceptance is made."],
              "native_launch": False, "frame_solve": False, "CAD_rebuilt": False,
              "tests_run": False, "complete_joint_acceptance": False, "physical_release": False,
              "output_sha256": {"cuts.csv": sha(args.output / "cuts.csv")}}
    (args.output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "result_sha256": sha(args.output / "result.json"),
                      "case_id": peak["case_id"], "station_mm": peak["station_mm"], "trace": peak["trace"],
                      "face_ratio": peak["face_lower_bound_ratio"], "counts": result["counts"]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame", type=Path)
    parser.add_argument("--clearance", type=Path)
    parser.add_argument("--operators-sha256")
    parser.add_argument("--comparison-sha256")
    parser.add_argument("--response-sha256")
    run(parser.parse_args())
