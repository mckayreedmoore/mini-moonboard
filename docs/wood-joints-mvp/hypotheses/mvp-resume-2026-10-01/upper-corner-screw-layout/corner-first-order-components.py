"""Replay existing component references on both first-order corner responses."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = HERE / "rawlocal/corner-first-order/attempt01/checks.json"
COMPONENT = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
INPUTS = HERE / "operators-attempt02/model-inputs.json"
MATH_SOURCE = HERE / "upper-left-block-components.py"
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
SIDES = {
    "left": ("top_outer_left_cleat", "base_side_left", "clip_single_top_left_1"),
    "right": ("top_outer_right_cleat", "base_side_right", "clip_single_top_right_2"),
}
INDEX_KEYS = (
    "lateral_over_conditional_reference",
    "parallel_over_finished_path_reference",
    "mean_pressure_over_Fc_perp",
    "smooth_bolt_VM_over_92ksi_hypothesis",
)
PINS = {
    SOURCE: "b15b57d3879fdca2dac607d11a2ad127acd1008f6c2a6f546333a1b26c754cfe",
    COMPONENT: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    INPUTS: "e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc",
    MATH_SOURCE: "893a96221e13dab832d949271b7d9f0c022a1ec71e522a576f603458f93a25e3",
    HERE.parent / "corner_checks.py": "177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0",
    HERE.parent / "lateral_reference.py": "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    HERE.parent / "top_corner_correction.py": "6474cbe6aa8306a153b6cbe166c3162001954b41ea7e4da6c6b7fe60031472e9",
    ROOT / "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def physical_balance(values, label):
    require(len(values) == 6 and all(math.isfinite(value) for value in values), label + " invalid wrench")
    require(max(abs(value) for value in values[:3]) <= 0.001
            and max(abs(value) for value in values[3:]) <= 0.2,
            label + " exceeds existing local balance tolerances")


def build(output: Path):
    output = Path(output).resolve()
    require(not output.exists(), "preserve previous output")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    for path, expected in pins.items():
        require(sha(path) == expected, f"frozen source differs: {path}")
    source, component, inputs = map(read, (SOURCE, COMPONENT, INPUTS))
    require(source["schema"] == "first_order_corner_independent_traction/v1"
            and source["status"] == "COMPLETE_FIRST_ORDER_LOCAL_FORCES"
            and source["failure"] is None, "first-order corner source incomplete")
    require(source["geometric_shortening_and_preload_stiffness"] is False
            and source["balancing_free_couples_added"] == 0
            and source["frame_response_changed"] is False
            and source["material_or_contact_laws_changed"] is False,
            "first-order method/source flags differ")
    require(not source["complete_joint_acceptance"] and not source["physical_release"],
            "source claims joint acceptance or physical release")
    for relative, expected in source["source_sha256"].items():
        path = (ROOT / relative).resolve()
        require(path.is_relative_to(ROOT), "source closure path leaves repository")
        require(path not in pins or pins[path] == expected, "conflicting source pin")
        pins[path] = expected
    for path, expected in pins.items():
        require(sha(path) == expected, f"source closure differs: {path}")
    require(component["source_comparison_sha256"] == source["source_sha256"][
        (HERE / "frame-250-attempt02/comparison.json").relative_to(ROOT).as_posix()]
        and component["source_response_sha256"] == source["source_sha256"][
            (HERE / "frame-250-attempt02/response.npz").relative_to(ROOT).as_posix()],
        "geometry references and first-order source bind different frame forces")
    block_ids = [(case["side"], case["case_id"]) for case in source["states"]]
    require(len(block_ids) == len(set(block_ids)) == 12
            and set(block_ids) == {(side, case_id) for side in SIDES for case_id in CASES},
            "two-corner six-case census differs")

    # ponytail: reuse the pinned lateral function exported by the earlier replay;
    # neither its replay entry point nor any geometry/mechanics producer is called.
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("frozen_component_math", MATH_SOURCE)
    require(spec is not None and spec.loader is not None, "component arithmetic unavailable")
    math_source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(math_source)
    grains = {member["member_id"]: np.array(member["reduced_geometry_descriptor"]["axis"])
              for member in inputs["members"] if "axis" in member["reduced_geometry_descriptor"]}
    paths = {(path["axis_id"], path["grain_direction_sign"]): path for path in component["finished_paths"]}
    seats = {(seat["axis_id"], seat["body"]): seat for seat in component["washer_seats"]}
    fv, fc = (component["component_references_mpa"][key] for key in ("Fv_parallel", "Fc_perpendicular"))
    states, balances = [], []
    for case in source["states"]:
        side, case_id = case["side"], case["case_id"]
        cleat, side_host, station = SIDES[side]
        require(set(case["hosts"]) == {"base_rail_top", side_host}, "corner host identities differ")
        physical_balance(case["physical_whole_cleat_residual_n_nmm"], side + " " + case_id + " cleat")
        balances.append({"side": side, "case_id": case_id,
                         "current_weight_once_n_nmm": case["current_weight_once_n_nmm"],
                         "physical_cleat_residual_n_nmm": case["physical_whole_cleat_residual_n_nmm"],
                         "physical_host_residuals_n_nmm": {
                             host: record["physical_host_residual_n_nmm"]
                             for host, record in case["hosts"].items()}})
        for host, record in case["hosts"].items():
            local, geometry = record["state"], record["geometry"]
            require(local["case_id"] == case_id and len(local["bolts"]) == 2
                    and len(local["face_cells"]) == 16, "host state or contact census differs")
            physical_balance(record["physical_host_residual_n_nmm"], side + " " + case_id + " " + host)
            family = "rail" if host == "base_rail_top" else "side"
            require({bolt["axis_id"] for bolt in local["bolts"]}
                    == {f"top_outer/{station}/{family}_{number}" for number in (1, 2)},
                    "first-order bolt ownership differs")
            for bolt in local["bolts"]:
                force = -np.array(bolt["bore_force_on_host_xyz_n"], dtype=float)
                lateral = float(np.linalg.norm(force))
                tension = float(bolt["compatible_T_n"])
                require(tension >= 0 and np.all(np.isfinite(force)), "invalid first-order force")
                require(math.isclose(lateral, bolt["bore_V_resultant_n"], abs_tol=1e-7, rel_tol=0),
                        "signed bore force and resultant differ")
                reference = math_source.lateral_reference(
                    force, geometry["diameter_mm"],
                    [geometry["host_length_mm"], geometry["cleat_length_mm"]],
                    [grains[host], grains[cleat]], 92000.0,
                )
                factor = math.prod(component["rail_component_Cg_Cdelta"]) if family == "rail" else 1.0
                parallel = float(force @ grains[cleat])
                path = paths[(bolt["axis_id"], 1 if parallel >= 0 else -1)]
                seat = seats[(bolt["axis_id"], cleat)]
                states.append({
                    "side": side, "case_id": case_id, "axis_id": bolt["axis_id"],
                    "host": host, "cleat": cleat, "T_n": tension, "V_n": lateral,
                    "force_on_cleat_lateral_xyz_n": force.tolist(),
                    "diameter_mm": geometry["diameter_mm"],
                    "ordered_wood_lengths_mm": [geometry["host_length_mm"], geometry["cleat_length_mm"]],
                    "lateral_reference": reference, "Cg_Cdelta_multiplier": factor,
                    "lateral_over_conditional_reference": lateral / (factor * reference["reference_n"]),
                    "finished_path_sign": path["grain_direction_sign"], "parallel_force_n": parallel,
                    "minimum_finished_one_plane_area_mm2": path["minimum_finished_one_plane_area_mm2"],
                    "parallel_over_finished_path_reference": abs(parallel) / (fv * path["minimum_finished_one_plane_area_mm2"]),
                    "minimum_supported_annulus_area_mm2": seat["minimum_annulus_area_mm2"],
                    "mean_pressure_over_Fc_perp": tension / (fc * seat["minimum_annulus_area_mm2"]),
                    "sampled_end_wood_pressure_peak_mpa": max(
                        end["wood_contact"]["pressure_peak_mpa"] for end in bolt["end_contacts"]),
                    "smooth_bolt_VM_mpa": bolt["peak_stress_witness"]["nominal_smooth_von_mises_proxy_mpa"],
                    "smooth_bolt_VM_over_92ksi_hypothesis": bolt["peak_stress_witness"]["proxy_over_conditional_92ksi_Fyb"],
                })
    require(len(states) == 48 and all(sum(state["side"] == side for state in states) == 24 for side in SIDES),
            "eight-bolt six-case census differs")
    peaks = {key: max(states, key=lambda state, key=key: state[key]) for key in INDEX_KEYS}
    by_side = {side: {key: max((state for state in states if state["side"] == side),
                              key=lambda state, key=key: state[key]) for key in INDEX_KEYS} for side in SIDES}
    result = {
        "schema": "first_order_corner_same_state_component_replay/v1",
        "status": "COMPLETE_SAME_STATE_COMPONENT_REFERENCES",
        "counts": {"block_states": 12, "host_models": 24, "bolt_states": 48,
                   "left_bolt_states": 24, "right_bolt_states": 24},
        "states": states, "peak_witnesses": peaks, "peak_witnesses_by_side": by_side,
        "physical_balance_source_receipts": balances,
        "component_references_mpa": component["component_references_mpa"],
        "rail_component_Cg_Cdelta": component["rail_component_Cg_Cdelta"],
        "host_splitting_original_source_only": [
            record for record in component["host_splitting"] if record["block"] in {value[0] for value in SIDES.values()}],
        "source_first_order_limits": source["limits"],
        "limits": [
            "Each component uses one changed bolt's simultaneous first-order tension, signed bore force and beam stress. No original independent force maximum or left/right symmetry acceptance is transferred.",
            "Single-shear, finished bore-tangent and supported full-annulus mean references remain the frozen 401b component geometry and conditional DF-L No. 2/92 ksi basis.",
            "Signed lateral force selects its own grain angles and finished path. Rail Cg*Cdelta factors are unchanged conditional component modifiers.",
            "Mean-seat pressure is not a point-contact pressure limit. Smooth-bolt VM includes the source beam bending, without a delivered thread-root or washer-metal resistance claim.",
            "Original complete-host splitting records remain geometry/scope history, not redistributed first-order cut demands or an adopted design resistance.",
            "The frozen original 100 mm lever frame is not rerun or updated. Combined oblique-group, elastic timber/cleat, washer and delivered hardware resistance remain outside this replay.",
        ],
        "source_sha256": {path.relative_to(ROOT).as_posix(): expected for path, expected in sorted(pins.items())},
        "mechanics_or_geometry_rerun": False, "complete_joint_acceptance": False, "physical_release": False,
    }
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed during component arithmetic: {path}")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    dump(output / "checks.json", result)
    dump(output / "receipt.json", {
        "source_sha256": result["source_sha256"],
        "output_sha256": {name: sha(output / name) for name in ("checks.json", "producer.py.snapshot")},
        "complete_joint_acceptance": False, "physical_release": False,
    })
    for path, expected in pins.items():
        require(sha(path) == expected, f"source changed before final receipt: {path}")
    print(json.dumps({"checks_sha256": sha(output / "checks.json"), "counts": result["counts"],
                      "peak_indices": {key: state[key] for key, state in peaks.items()}}))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
