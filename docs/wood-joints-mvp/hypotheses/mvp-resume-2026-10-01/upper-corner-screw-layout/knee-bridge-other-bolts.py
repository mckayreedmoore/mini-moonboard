"""Parent-only fresh-gravity lateral references for 84 existing physical bolts.

Import is inert. This binds saved forces and calls supplied-input reference
functions only; it invokes no old producer, frame solve, CAD or native pipeline.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
ROOT = HERE.parents[4]
HYPOTHESES = PACKET.parent
RAW = HERE / "rawlocal/knee-bridge-other-bolts"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
EXPORT = HERE / "rawlocal/knee-bridge-response/attempt02"
REGISTER = HERE / "rawlocal/working-joint-register/attempt03/register.json"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
GEOMETRY = HYPOTHESES / "mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
MATERIALS = HYPOTHESES / "hardware-material-specification-2026-09-30/material-inputs.json"
FASTENERS = MATERIALS.with_name("fastener-inputs.json")
RETAINED = Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json")
RETAINED_METHOD = HYPOTHESES / "retained-frame-bolt-current-resistance-basis-2026-10-01/produce.py"
NDS = ROOT / "mini_moonboard/nds_2024_multi_member_bolt_yield.py"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
FYB_PSI = 92000.0
CONTINUOUS = {f"knee_outer_{side}_side_{index}" for side in ("left", "right") for index in (1, 2)}
PINS = {
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    REGISTER: "c34745395481038e32c7474de1798882263de7e54a7cc494949948b4a5e3464c",
    EXPORT / "summary.json": "da8fcfde95eda2fb6967194c1060e5b55647eeb1ea98efa25e8a9e8260294c70",
    EXPORT / "receipt.json": "57163aa9f4e1ed7af338d29c4893f5614c21bd422e841532cf67feb67ac20933",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    GEOMETRY: "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9",
    MATERIALS: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
    RETAINED: "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1",
    RETAINED_METHOD: "24b3cb82ed6a785ab5dc0cf910f22a0cce915438f8d4b04d527d82a245b1205b",
    NDS: "575d7de88d5f138412fef633ef946bccba884c1953b67e8d9211fc028d74ab89",
    PACKET / "remaining_joint_screen.py": "4d9ea0e03ab98ba4bc8c9e4641a85d5e54603c59cf2ab1d17385de4c16dc964f",
    PACKET / "top_corner_local.py": "4b00bc312607be743ae73a7a34ee1ada0fe7a5d2ffd69d2d18902f3ea65dfd77",
    PACKET / "lateral_reference.py": "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    ROOT / "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
}
FLAGS = {
    "proposal_adopted": False, "formal_criteria_updated": False,
    "historical_stress_group_splitting_acceptance_transferred": False,
    "actual_changed_hole_stiffness_qualified": False,
    "hardware_capacity_qualified": False, "mechanical_acceptance": False,
    "complete_joint_acceptance": False, "physical_release": False,
    "native_or_CAD_or_frame_run": False, "tests_or_review_run": False,
}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def read(path):
    return json.loads(path.read_text())


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = path.resolve()
    require(path not in pins or pins[path] == digest, "conflicting source pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed source: " + str(path))


def pure_module(path, name):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def build(output):
    """Parent executes one fixed arithmetic comparison; no source results change."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate RAW child required")
    pins = dict(PINS)
    bind(pins, Path(__file__), sha(Path(__file__)))
    authenticate(pins)
    comparison, assessment, register, summary, receipt, integration, inputs, retained = [read(path) for path in
        (FRAME / "comparison.json", GRAVITY / "operator-assessment.json", REGISTER,
         EXPORT / "summary.json", EXPORT / "receipt.json", INTEGRATION, GEOMETRY, RETAINED)]
    require(comparison["response_sha256"] == pins[FRAME / "response.npz"], "fresh response binding differs")
    require(ROOT / comparison["frame_operator_directory"] == GRAVITY,
            "fresh comparison names another operator packet")
    require(comparison["source_sha256"][key(GRAVITY / "operator-assessment.json")]
            == pins[GRAVITY / "operator-assessment.json"], "gravity assessment not bound by response")
    require(assessment["operator_ready"] is True and assessment["case_ids"] == list(CASES),
            "gravity operators not ready or case order differs")
    require(summary["schema"] == "knee-bridge-fresh-global-force-census/v1"
            and summary["status"] == "FRESH_GLOBAL_DEMANDS_EXPORTED"
            and summary["source_comparison_sha256"] == pins[FRAME / "comparison.json"], "wrong demand export")
    require(summary["source_sha256"] == receipt["source_sha256"], "export source receipt differs")
    require(receipt["output_sha256"]["summary.json"] == pins[EXPORT / "summary.json"], "export summary receipt differs")
    for name, digest in receipt["source_sha256"].items():
        bind(pins, ROOT / name, digest)
    for name, digest in receipt["output_sha256"].items():
        bind(pins, EXPORT / name, digest)
    for name, digest in assessment["output_sha256"].items():
        bind(pins, GRAVITY / name, digest)
    for binding in integration["authority"]["files_unchanged"]:
        bind(pins, ROOT / binding["source"], binding["sha256"])
    authenticate(pins)
    require(comparison["modeled_mass_kg"] == assessment["modeled_mass_kg"] == summary["fresh_modeled_mass_kg"]
            and comparison["dead_load_factor"] == assessment["dead_load_factor"] == summary["dead_load_factor"],
            "fresh mass/deadfactor differs")
    state_ids = [(state["case_id"], state["gap_scale"]) for state in comparison["states"]]
    require(len(state_ids) == 12 and set(state_ids) == {(case, gap) for case in CASES for gap in (0.0, 1.0)},
            "fresh zero/nominal state census differs")
    require(register["case_ids"] == list(CASES) and register["candidate"] == inputs["candidate"] == retained["candidate"]
            and inputs["revision_id"] == retained["geometry_revision_id"], "geometry/register scope differs")
    candidate = read(ROOT / "wood-joints-candidate.json")
    criteria = read(ROOT / "docs/wood-joints-mvp/criteria.json")
    criteria_rows = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    release_flags = candidate["release_flags"]
    require(len(criteria_rows) == 47 and all(row["status"] == "pending" for row in criteria_rows)
            and len(release_flags) == 8 and all(value is False for value in release_flags.values())
            and candidate["release"] is False, "formal 47/8 authority differs")
    require(read(MATERIALS)["conditional_DF_L_No2_base_row"]["base_properties"]["G_for_dowel_bearing"] == 0.5
            and 1000 * read(FASTENERS)["material_boundaries"]["sae_j429_grade5_1_4_through_1_in"]["machine_test_yield_ksi_min"]
            == FYB_PSI, "frozen material/Fyb scenario differs")
    require(retained["producer_sha256"] == pins[RETAINED_METHOD]
            and retained["source_pins"][key(NDS)]["sha256"] == pins[NDS], "retained primary method differs")

    axes = {axis["axis_id"]: axis for axis in register["axes"]}
    bolts = {bolt["axis_id"]: bolt for bolt in inputs["connections"]
             if bolt["kind"] in ("candidate_bolt", "retained_bolt")}
    require(len(register["axes"]) == len(axes) == len(bolts) == 104 and set(axes) == set(bolts), "104-axis identity differs")
    corners = {axis for axis in axes if axis.startswith(("top_outer/", "bottom_outer/"))}
    continuous = {axis for axis, row in axes.items() if len(row["receivers"]) != 2}
    owned = set(axes) - corners - continuous
    service = {axis for axis, bolt in bolts.items() if "left_service_outer_lower_cleat" in bolt["receiver_member_ids"]}
    require(len(corners) == 16 and continuous == CONTINUOUS and len(owned) == 84
            and len(service) == 4 and service.issubset(owned), "84-axis ownership partition differs")
    require(sum(bolts[axis]["kind"] == "retained_bolt" for axis in owned) == 12, "retained census differs")
    members = {member["member_id"]: member["reduced_geometry_descriptor"]
               for member in inputs["members"] if member["member_kind"] != "panel"}
    rows = read(GRAVITY / "row-identities.json")
    require(len(rows) == 1888 and [row["row"] for row in rows] == list(range(1888)), "raw row order differs")
    exported = [json.loads(line) for line in (EXPORT / "global-demands.jsonl").read_text().splitlines()]
    demands = {(record["case_id"], record["axis_id"]): record for record in exported if record["kind"] == "structural_bolt"}
    require(len(demands) == sum(record["kind"] == "structural_bolt" for record in exported) == 624
            and set(demands) == {(case, axis) for case in CASES for axis in axes}, "exported bolt census differs")

    previous_path, previous_bytecode = list(sys.path), sys.dont_write_bytecode
    sys.path[:0] = [str(PACKET), str(ROOT)]
    sys.dont_write_bytecode = True
    try:
        import lateral_reference as lateral
        import numpy as np

        require(Path(lateral.__file__).resolve() == PACKET / "lateral_reference.py", "wrong lateral helper import")
        nds = pure_module(NDS, "knee_bridge_retained_primary")

        def unit(vector):
            value = np.asarray(vector, dtype=float)
            require(value.shape == (3,) and np.isfinite(value).all() and np.linalg.norm(value) > 0, "invalid direction")
            return value / np.linalg.norm(value)

        records = []
        with np.load(FRAME / "response.npz", allow_pickle=False) as response:
            for case in CASES:
                force = response[case + "_gap_raw_force_n"]
                require(force.shape == (1888,) and np.isfinite(force).all(), "invalid fresh nominal force array")
                for axis_id in sorted(owned):
                    axis, bolt, demand = axes[axis_id], bolts[axis_id], demands[(case, axis_id)]
                    require(axis["kind"] == bolt["kind"] and set(axis["receivers"]) == set(bolt["receiver_member_ids"])
                            == set(demand["receivers"]), "receiver identity differs: " + axis_id)
                    require(len(axis["interfaces"]) == len(demand["interfaces"]) == 1, "single-plane scope differs")
                    interface, exported_plane, tie = axis["interfaces"][0], demand["interfaces"][0], axis["outer_tie"]
                    indices = interface["component_rows"]
                    require(len(indices) == 2 and rows[tie["row"]]["row_id"] == tie["row_id"]
                            and rows[tie["row"]]["law"]["intended_law"] == "tension_only", "tie/plane row identity differs")
                    require(all(rows[tie["row"]]["ownership"][field] == tie[field]
                                for field in ("first_body", "second_body", "direction_global_xyz", "point_mm", "role")),
                            "signed tie ownership differs")
                    owners = [rows[index]["ownership"] for index in indices]
                    bodies = interface["receivers"]
                    require(all(rows[index]["row_id"] == interface["plane_id"] for index in indices)
                            and all(owner["first_body"] == bodies[0] and owner["second_body"] == bodies[1]
                                    and owner["point_mm"] == interface["point_xyz_mm"] for owner in owners), "mixed plane ownership")
                    directions = np.array(interface["component_directions_xyz"])
                    require(directions.tolist() == [owner["direction_global_xyz"] for owner in owners], "plane directions differ")
                    axis_unit = unit(bolt["axis_xyz"])
                    require(np.max(abs(directions @ directions.T - np.eye(2))) < 1e-8
                            and np.max(abs(directions @ axis_unit)) < 1e-8, "invalid lateral basis")
                    scalars, tension = force[indices], float(force[tie["row"]])
                    shear = scalars @ directions
                    magnitude = float(np.linalg.norm(shear))
                    require(tension >= -1e-8 and demand["signed_axial_n"] == tension, "fresh signed tie/export differs")
                    require(exported_plane["plane_id"] == interface["plane_id"]
                            and exported_plane["component_rows"] == indices
                            and exported_plane["component_directions_xyz"] == directions.tolist()
                            and exported_plane["components_n"] == scalars.tolist()
                            and math.isclose(exported_plane["lateral_n"], magnitude, rel_tol=1e-12, abs_tol=1e-8), "fresh same-plane export differs")
                    grains = [unit(members[body]["axis"]) for body in bodies]
                    angles = [lateral.angle(shear, grain) for grain in grains]
                    if bolt["kind"] == "retained_bolt":
                        geometry = retained["axis_register"][axis_id]
                        receivers = {receiver["member"]: receiver for receiver in geometry["finished_receivers"]}
                        require(set(receivers) == set(bodies), "retained finished receivers differ")
                        lengths = [receivers[body]["interval_from_axis_datum_mm"][1]
                                   - receivers[body]["interval_from_axis_datum_mm"][0] for body in bodies]
                        diameter = bolt["source_record"]["source_occupied_diameter_mm"] / 25.4
                        require(math.isclose(diameter, geometry["hardware_policy"]["nominal_diameter_in"], abs_tol=1e-10)
                                and math.isclose(sum(lengths), bolt["source_record"]["source_grip_mm"], abs_tol=1e-7), "retained D/grip differs")
                        require(np.linalg.norm(np.array(bolt["source_point_xyz_mm"]) + axis_unit
                                * receivers[bodies[0]]["interval_from_axis_datum_mm"][1]
                                - np.array(interface["point_xyz_mm"])) < 1e-6, "retained interface position differs")
                        for body, grain in zip(bodies, grains, strict=True):
                            receiver = receivers[body]
                            require(receiver["finished_step"]["file_sha256"] == members[body]["step_sha256"]
                                    and abs(grain @ unit(receiver["stock_frame"]["basis_columns_global_xyz"][0])) > 1 - 1e-8,
                                    "retained finished geometry/grain differs")
                            bind(pins, ROOT / receiver["finished_step"]["path"], receiver["finished_step"]["file_sha256"])
                    else:
                        geometry = bolt["source_record"]["geometry"]
                        require(math.isclose(geometry["modeled_shaft_diameter_mm"], 6.35, abs_tol=1e-8), "candidate D differs")
                        intervals = {receiver["receiver_id"]: receiver["current_shaft_intersection_solid_intervals_from_underhead_mm"]
                                     for receiver in geometry["wood_receiver_intervals"]}
                        require(set(intervals) == set(bodies) and all(len(spans) == 1 and spans[0][1] > spans[0][0]
                                for spans in intervals.values()), "ambiguous candidate bearing intervals")
                        lengths = [intervals[body][0][1] - intervals[body][0][0] for body in bodies]
                        diameter = 0.25
                    require(all(math.isfinite(length) and length > 0 for length in lengths), "invalid bearing lengths")
                    record = {"case_id": case, "gap_scale": 1.0, "axis_id": axis_id, "kind": bolt["kind"],
                        "plane_id": interface["plane_id"], "receivers": bodies, "point_xyz_mm": interface["point_xyz_mm"],
                        "component_rows": indices, "component_directions_xyz": directions.tolist(), "components_n": scalars.tolist(),
                        "force_on_first_body_xyz_n": shear.tolist(), "force_on_second_body_xyz_n": (-shear).tolist(),
                        "same_plane_lateral_n": magnitude, "tie_row": tie["row"], "signed_axial_n": tension,
                        "tie_first_body": tie["first_body"], "tie_second_body": tie["second_body"],
                        "tie_direction_xyz": tie["direction_global_xyz"],
                        "grain_axes_xyz": [grain.tolist() for grain in grains], "load_to_grain_degrees": angles,
                        "bearing_lengths_mm": lengths, "modeled_full_body_diameter_in": diameter,
                        "Fyb_scenario_psi": FYB_PSI, "reference_92ksi_n": None, "ratio_92ksi": None,
                        "mode_92ksi": None, "mode_references_92ksi_n": None,
                        "material_reference_method": "retained_primary_NDS" if bolt["kind"] == "retained_bolt" else "candidate_rounded_Fe",
                        "lateral_reference_status": "END_GRAIN_METHOD_SEPARATE", "joint_accepted": False}
                    if not any(abs(axis_unit @ grain) > 1e-8 for grain in grains):
                        if bolt["kind"] == "retained_bolt":
                            require(magnitude > 0, "retained zero-demand orientation needs a separate reference scenario")
                            receiving = [{"bearing_length_in": length / 25.4,
                                "fe_theta_psi": nds._fe_theta_psi(specific_gravity=0.5, diameter_in=diameter, angle_degrees=angle)}
                                for length, angle in zip(lengths, angles, strict=True)]
                            modes = nds._single_shear_modes(*receiving, diameter, FYB_PSI,
                                nds._reduction_terms(diameter_in=diameter, nominal_diameter_in=diameter, angle_max_degrees=max(angles)))
                            status = "CONDITIONAL_RETAINED_SINGLE_SHEAR"
                        else:
                            modes = lateral.reference(lengths, angles, FYB_PSI)["reference_values_lbf"]
                            status = "CONDITIONAL_CANDIDATE_SINGLE_SHEAR"
                        values = {mode: value * lateral.N_PER_LBF for mode, value in modes.items()}
                        governing = min(values, key=values.get)
                        reference = values[governing]
                        require(math.isfinite(reference) and reference > 0, "invalid conditional reference")
                        record.update(lateral_reference_status=status, mode_92ksi=governing,
                                      reference_92ksi_n=reference, ratio_92ksi=magnitude / reference, mode_references_92ksi_n=values)
                    records.append(record)
        authenticate(pins)
        require(len(records) == len({(row["case_id"], row["axis_id"]) for row in records}) == 504,
                "504-axis-state census differs")
        eligible = [row for row in records if row["ratio_92ksi"] is not None]
        counts = {"nominal_cases": 6, "old_physical_axes": 104, "excluded_corner_axes": 16,
            "excluded_continuous_knee_axes": 4, "owned_physical_axes": 84, "candidate_axes": 72, "retained_axes": 12,
            "lower_left_outer_service_axes_included": 4, "axis_states": 504, "plane_states": 504,
            "eligible_states": len(eligible), "status_states": dict(Counter(row["lateral_reference_status"] for row in records))}
        report = {"schema": "knee_bridge_other_bolts_fresh_lateral/v1", "status": "COMPLETE_FRESH_CONDITIONAL_LATERAL_REFERENCES",
            "census": counts, "owned_axis_ids": sorted(owned), "excluded_corner_axis_ids": sorted(corners),
            "excluded_continuous_axis_ids": sorted(continuous), "included_lower_service_axis_ids": sorted(service),
            "source_comparison_sha256": pins[FRAME / "comparison.json"], "fresh_modeled_mass_kg": comparison["modeled_mass_kg"],
            "dead_load_factor": comparison["dead_load_factor"], "Fyb_scenario_psi": FYB_PSI,
            "peak_92ksi_same_state": max(eligible, key=lambda row: row["ratio_92ksi"]) if eligible else None,
            "above_one_92ksi_axis_ids": sorted({row["axis_id"] for row in eligible if row["ratio_92ksi"] > 1}),
            "formal_pending_criteria_count": 47, "release_flags": release_flags,
            "assumptions": ["Existing DF-L G=0.50; candidate rounded Fe and retained diameter-dependent primary Fe remain distinct.",
                "Full smooth nominal-D bearing under the existing partially threaded delivered-profile assumption; no received shank/root profile is observed.",
                "Single-fastener zero-interface-gap references precede group/geometry/service adjustments; only the declared conditional 92 ksi Fyb scenario is used."],
            "limits": ["Signed T and signed same-plane V are fresh global allocations, not local joint resistance or redistributed force acceptance.",
                "End-grain method exclusions retain null reference ratios; sixteen corners and four continuous shafts belong to separate work.",
                "No old stress, group, splitting, washer, hardware qualification or release transfers. The center_principal_right_2 partial washer seat remains outside this lateral-only comparison.",
                "No geometry, material, lever, thread-root, load or hardware variant is introduced; original finished/member applicability gaps remain."], **FLAGS}
        output.mkdir(parents=True)
        (output / ".gitignore").write_text("*\n")
        (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
        with (output / "records.jsonl").open("w") as stream:
            for record in records:
                stream.write(json.dumps(record, allow_nan=False) + "\n")
        dump(output / "summary.json", report)
        source_hashes = {key(path): digest for path, digest in pins.items()}
        dump(output / "sources.json", {"source_sha256": source_hashes,
            "register_scope": "Axis receivers/component rows only; per_state historical forces and acceptance are not consumed.",
            "old_screen_binding_or_pipeline_called": False})
        authenticate(pins)
        names = (".gitignore", "producer.py.snapshot", "records.jsonl", "summary.json", "sources.json")
        output_hashes = {name: sha(output / name) for name in names}
        dump(output / "receipt.json", {"schema": "knee_bridge_other_bolts_receipt/v1", "status": report["status"],
            "producer_sha256": pins[Path(__file__).resolve()], "source_sha256": source_hashes, "output_sha256": output_hashes,
            "sources_authenticated_before_and_after": True, "census": counts, "formal_pending_criteria_count": 47,
            "release_flags": release_flags, **FLAGS})
        authenticate(pins)
        require(all(sha(output / name) == digest for name, digest in output_hashes.items()), "receipt-bound output changed")
        return {"status": report["status"], "output": str(output), "census": counts,
                "summary_sha256": output_hashes["summary.json"], "receipt_sha256": sha(output / "receipt.json"), **FLAGS}
    finally:
        sys.path[:] = previous_path
        sys.dont_write_bytecode = previous_bytecode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(build(arguments.output), allow_nan=False))
