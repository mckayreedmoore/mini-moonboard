"""Parent-owned finite top-rail refresh from saved fresh-gravity actions.

Import is inert. Only build(output) loads arithmetic helpers. Historical
section evidence supplies geometry and twelve sections, never loads or passes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-top-rail"
CORNER = HERE / "rawlocal/knee-bridge-corner-replay/attempt01"
MEMBER = BASE / "member-screen-attempt02/knee-bridge-gravity01"
SECTION = HERE / "rawlocal/top-host-net-sections/attempt02"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
INTEGRATION = HERE / "rawlocal/knee-bridge-integration/attempt02/manifest.json"
FACE = BASE / "top-corner-contact-geometry.json"
HOST = "base_rail_top"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
SIDES = ("left", "right")
DURATIONS = {"original_CD1": 1.0, "conditional_peak_CD1_25": 1.25}
GEOM_TOL, PARTITION_TOL = 1e-5, 1e-6
FORCE_TOL, MOMENT_TOL = 0.001, 0.2
PINS = {
    CORNER / "checks.json": "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    CORNER / "receipt.json": "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    MEMBER / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    MEMBER / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    MEMBER / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    SECTION / "checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    SECTION / "receipt.json": "486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29",
    SECTION / "producer.py.snapshot": "c8c6e3c23bfe5e7d6999160546bc8f6ad106c178219307aa1d984367fcd80364",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    INTEGRATION: "1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c",
    FACE: "987af6908d6677165b6a712537ecca0c02827d558ca386ced96f4c1f6436008f",
    HERE / "top-host-physical-actions.py": "0f005656656d26d1003c3ff4317c696172f2399de438c287ff9a8ea12e926b49",
    HERE / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "corner-bore-wall.py": "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    BASE / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    BASE / "top_corner_contact.py": "a077c8636f504a2d4a7437f0f68722411c16911dbddc2734a96e444bf2b4655a",
}
FLAGS = dict.fromkeys((
    "proposal_adopted", "formal_criterion_acceptance", "complete_joint_acceptance",
    "complete_member_acceptance", "physical_release", "fabrication_release",
    "historical_acceptance_transferred", "historical_case_loads_used_as_authority",
    "reviewed_geometry_changed", "material_or_contact_laws_changed",
    "actual_changed_hole_elastic_stiffness_qualified", "local_bridge_compatibility_qualified",
    "stability_qualified", "hardware_qualified", "local_redistribution_feeds_back_to_frame",
    "native_CAD_or_frame_execution", "known_answers_executed", "tests_run", "review_run",
), False)


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
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = path.resolve()
    require(path not in pins or pins[path] == digest, "conflicting source: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + str(path))


def bind_outputs(pins, directory, outputs):
    for name, digest in outputs.items():
        require(Path(name).name == name, "output receipt path is not a filename")
        bind(pins, directory / name, digest)


def helper(filename):
    path = HERE / filename
    spec = importlib.util.spec_from_file_location("knee_bridge_top_" + path.stem, path)
    require(spec is not None and spec.loader is not None, "helper unavailable: " + filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare(pins):
    """Authenticate fresh load packets and the saved geometry provenance closure."""
    corner, receipt, member, member_geometry, saved, old_receipt, face, gravity, comparison, integration = (
        read(path) for path in (
            CORNER / "checks.json", CORNER / "receipt.json", MEMBER / "member-results.json",
            MEMBER / "geometry.json", SECTION / "checks.json", SECTION / "receipt.json",
            FACE, GRAVITY / "operator-assessment.json", FRAME / "comparison.json", INTEGRATION,
        )
    )
    require(corner["schema"] == "knee_bridge_original_corner_first_order_replay/v1"
            and corner["status"] == receipt["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES",
            "fresh corner replay is incomplete")
    require(corner["source_sha256"] == receipt["source_sha256"]
            and len(receipt["source_sha256"]) == 94, "corner source receipt differs")
    require(receipt["output_sha256"]["checks.json"] == pins[CORNER / "checks.json"]
            and receipt["source_unchanged_before_and_after_write"] is True,
            "corner output receipt differs")
    require(corner["counts"] == {
        "completed_block_states": 24, "completed_host_states": 48,
        "top_bolt_states": 48, "bottom_bolt_states": 48, "completed_bolt_states": 96,
    } and len(corner["states"]) == 24, "full fresh corner census differs")
    require(member["schema"] == "same_state_six_case_timber_member_screen/v1"
            and member["status"] == "COMPLETE_CONDITIONAL_ELEMENTARY_MEMBER_SCREENS_NOT_QUALIFICATION",
            "fresh member packet differs")
    require(member["clearance_input_directory"] == key(FRAME)
            and member["frame_operator_directory"] == key(GRAVITY),
            "member actions name another frame or gravity directory")
    require(tuple(case["case_id"] for case in member["cases"]) == CASES
            and corner["case_ids"] == gravity["case_ids"] == list(CASES), "six case IDs differ")
    require(gravity["operator_ready"] is True
            and gravity["status"] == "PASS_UPDATED_ELASTIC_FRAME_OPERATORS",
            "gravity operator packet is not ready")
    fresh_sources = {key(path): pins[path] for path in (
        GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz",
    )}
    require(corner["fresh_load_sources"] == fresh_sources, "corner fresh force bindings differ")
    for relative, digest in fresh_sources.items():
        require(member["source_sha256"][relative] == digest, "member fresh force binding differs")
    require(comparison["schema"] == "coupled_two_receiver_frame_clearance/v1"
            and comparison["response_sha256"] == pins[FRAME / "response.npz"]
            and comparison["frame_operator_directory"] == key(GRAVITY)
            and comparison["source_sha256"][key(GRAVITY / "operator-assessment.json")]
            == pins[GRAVITY / "operator-assessment.json"], "fresh frame binding differs")
    require(corner["modeled_mass_kg"] == comparison["modeled_mass_kg"] == gravity["modeled_mass_kg"]
            and corner["dead_load_factor"] == comparison["dead_load_factor"]
            == gravity["dead_load_factor"] == member["same_state_dead_load_factor"],
            "fresh mass or gravity factor differs")
    require(comparison["climber_load_scale"] == comparison["horizontal_load_scale"] == 1
            and comparison["source_climber_weight_lb"] == comparison["comparison_climber_weight_lb"] == 250
            and comparison["comparison_horizontal_force_n"] == 300, "live load scope differs")
    require(old_receipt["source_sha256"] == saved["source_sha256"]
            and old_receipt["output_sha256"] == {
                name: pins[SECTION / name] for name in ("checks.json", "producer.py.snapshot")
            }, "historical geometry receipt differs")
    require(face["producer_sha256"] == pins[BASE / "top_corner_contact.py"],
            "finite face geometry recipe differs")
    # Historical closure is provenance only; its point forces/results are never consumed.
    for relative, digest in saved["source_sha256"].items():
        if relative == key(HERE / "top-host-net-sections.py"):
            require(digest == pins[SECTION / "producer.py.snapshot"], "section snapshot binding differs")
            continue
        bind(pins, ROOT / relative, digest)
    for packet in (receipt, member, face, gravity, comparison):
        for relative, digest in packet["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for directory, packet in ((CORNER, receipt), (MEMBER, member), (GRAVITY, gravity)):
        bind_outputs(pins, directory, packet["output_sha256"])
    for binding in integration["authority"]["files_unchanged"]:
        bind(pins, ROOT / binding["source"], binding["sha256"])
    authenticate(pins)
    candidate = read(ROOT / "wood-joints-candidate.json")
    criteria = read(ROOT / "docs/wood-joints-mvp/criteria.json")
    criteria_rows = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    release_flags = candidate["release_flags"]
    require(len(criteria_rows) == 47 and all(row["status"] == "pending" for row in criteria_rows)
            and len(release_flags) == 8 and all(value is False for value in release_flags.values())
            and candidate["release"] is False, "formal 47 pending / eight false flags differ")
    require(all(corner[name] is False for name in (
        "proposal_adopted", "historical_acceptance_transferred", "historical_case_loads_used_as_authority",
        "reviewed_geometry_changed", "material_or_contact_laws_changed", "physical_release",
    )), "fresh corner claim boundary differs")
    record = member_geometry["members"][HOST]
    rail = saved["geometry"][HOST]
    sections = saved["opening_sections"][HOST]
    require(len(sections) == 12 and len({section["station_mm"] for section in sections}) == 12
            and len({section["saved_station_index"] for section in sections}) == 12,
            "twelve unchanged section stations required")
    require(record["current_finished_step"] == rail["finished_step_path"]
            and record["current_finished_step_sha256"] == rail["finished_step_sha256"],
            "fresh member and historical rail geometry differ")
    for section in sections:
        require(record["stations_mm"][section["saved_station_index"]] == section["station_mm"],
                "saved section index no longer names the same station")
    material = next(row for row in member["cases"][0]["members"] if row["member"] == HOST)["conditional_material"]
    require(material["scenario"] == "conditional_DF-L_No2_standard_section_CF_only"
            and material["CF"] == {"Fb": 1.3, "Ft_parallel": 1.3, "Fc_parallel": 1.1}
            and material["design_resistance_established"] is False, "retained material scenario differs")
    states = {}
    for side in SIDES:
        selected = [state for state in corner["states"] if state["level"] == "top" and state["side"] == side]
        require(tuple(state["case_id"] for state in selected) == CASES,
                "six top states per side required: " + side)
        for state in selected:
            require(state["cleat"] == "top_outer_" + side + "_cleat" and HOST in state["hosts"],
                    "top rail host ownership differs")
            local = state["hosts"][HOST]["state"]
            require(local["case_id"] == state["case_id"] and local["gap_scale"] == 1
                    and local["source_comparison_sha256"] == pins[FRAME / "comparison.json"]
                    and local["source_response_sha256"] == pins[FRAME / "response.npz"]
                    and local["source_gravity_assessment_sha256"] == pins[GRAVITY / "operator-assessment.json"],
                    "top host is not the fresh nominal state")
        states[side] = selected
    return member, record, rail, sections, face, states, material, gravity, release_flags


def duration_results(local, section, datum, frame, case_id, before, nominal, previous, material):
    """The unchanged regional stress and signed face-vector comparisons."""
    results = {}
    for scenario, duration in DURATIONS.items():
        refs = {name: value * duration for name, value in material["CF_only_reference_mpa"].items()}
        result = nominal.nominal_section(local, section["regions"], refs)
        result["references"] = refs
        faces = [previous.region_faces(region, refs, {"cut_datum_global_xyz_mm": datum.tolist()}, frame)
                 for region in result["regions"]]
        deciding = max(faces, key=lambda region: region["face_peak"]["combined_shear_over_Fv"])
        summary = {
            "case": case_id, "station_mm": section["station_mm"],
            "limit": "before" if before else "after",
            "saved_trace_index": 2 * section["saved_station_index"] + int(not before),
            "duration_scenario": scenario, "CD": duration,
            "normal_reference_sum": max(corner["comparisons"]["axial_plus_bending_reference_sum"]
                                        for region in result["regions"] for corner in region["longitudinal_corners"]),
            "compatible_face_peak_over_Fv": deciding["face_peak"]["combined_shear_over_Fv"],
            "scalar_shear_bound_over_Fv": max(region["same_state_shear_bound_over_Fv"] for region in result["regions"]),
            "sufficient_rectangle_bound_over_Fv": max(region["sufficient_all_section_bound_over_Fv"] for region in faces),
            "deciding_region_id": deciding["region_id"], "deciding_face": deciding["face_peak"],
        }
        results[scenario] = {"summary": summary, "nominal_section": result, "regional_faces": faces}
    return results


def comparison_summary(summaries):
    metrics = ("normal_reference_sum", "compatible_face_peak_over_Fv",
               "scalar_shear_bound_over_Fv", "sufficient_rectangle_bound_over_Fv")
    comparison = {}
    for scenario, duration in DURATIONS.items():
        own = [row for row in summaries if row["duration_scenario"] == scenario]
        require(len(own) == 144, "144 comparisons per duration required")
        comparison[scenario] = {
            "CD": duration, "global_peaks": {metric: max(own, key=lambda row: row[metric]) for metric in metrics},
            "exceeding_trace_count_by_metric": {metric: int(sum(row[metric] > 1 for row in own)) for metric in metrics},
            "face_exceeding_trace_count": int(sum(row["compatible_face_peak_over_Fv"] > 1 for row in own)),
            "all_sufficient_rectangle_bounds_below_one": all(row["sufficient_rectangle_bound_over_Fv"] <= 1 for row in own),
            "per_case": [{"case": case, "face_peak": max(
                (row for row in own if row["case"] == case), key=lambda row: row["compatible_face_peak_over_Fv"]
            )} for case in CASES],
        }
    return comparison


def record_error(accounting, label, error):
    for suffix, values in (("force_error_n", error[:3]), ("moment_error_nmm", error[3:])):
        name = "maximum_" + label + "_" + suffix
        accounting[name] = max(accounting.get(name, 0.0), max(abs(float(value)) for value in values))


def build(output):
    """Parent-only arithmetic; write one fresh immediate child of the owned RAW directory."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh immediate RAW child required")
    producer = Path(__file__).resolve()
    pins = dict(PINS)
    bind(pins, producer, sha(producer))
    authenticate(pins)
    member, record, rail, sections, face, states, material, gravity, release_flags = prepare(pins)
    # Load definitions only; no old build/main, coupons, response or pipeline calls.
    old_bytecode = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        import numpy as np
        physical, previous, nominal, wall = (helper(name) for name in (
            "top-host-physical-actions.py", "top-host-net-sections.py", "corner-net-section.py", "corner-bore-wall.py",
        ))
    finally:
        sys.dont_write_bytecode = old_bytecode
    require((physical.GEOM_TOL, physical.PARTITION_TOL, physical.FORCE_TOL, physical.MOMENT_TOL)
            == (GEOM_TOL, PARTITION_TOL, FORCE_TOL, MOMENT_TOL)
            and (previous.GEOM_TOL, previous.PARTITION_TOL) == (GEOM_TOL, PARTITION_TOL)
            and physical.DURATIONS == previous.SCENARIOS == DURATIONS, "original method tolerances or durations differ")
    geometry = record["geometry"]
    frame = np.array(rail["grain_frame_rows_xyz"])
    require(np.max(abs(frame - [geometry["axis"], geometry["section_u"], geometry["section_v"]])) < GEOM_TOL
            and np.max(abs(np.array(rail["width_depth_mm"]) - [geometry["width_mm"], geometry["depth_mm"]])) < GEOM_TOL,
            "unchanged grain frame or section dimensions differ")
    geom = {**rail, "start_xyz_mm": geometry["start"],
            "grain_length_mm": float(np.dot(np.array(geometry["end"]) - geometry["start"], frame[0]))}
    identities = read(GRAVITY / "row-identities.json")
    row_map = {row["row"]: row for row in identities}
    require(len(row_map) == len(identities), "operator row identities are not unique")
    by_side = {side: {state["case_id"]: state["hosts"][HOST] for state in states[side]} for side in SIDES}
    tiles_by_side = {}
    original_member = physical.MEMBER
    try:
        # face_tiles reads this global for unchanged bore geometry; use the fresh packet explicitly.
        physical.MEMBER = MEMBER
        for side in SIDES:
            block = "top_outer_" + side + "_cleat"
            own_face = [cleat for cleat in face["cleats"] if cleat["block"] == block]
            require(len(own_face) == 1, "one unchanged face record per top cleat required")
            tiles_by_side[side] = physical.face_tiles(block, own_face[0], geometry, frame, rail, states[side], row_map)
    finally:
        physical.MEMBER = original_member
    cuts, point_cuts, summaries, point_summaries, groups, accounting = [], [], [], [], [], {}
    with np.load(MEMBER / "action-section-arrays.npz", allow_pickle=False) as arrays:
        points, stations, point_rows = (arrays[HOST + suffix] for suffix in (
            "__point_xyz_mm", "__point_stations_mm", "__point_rows",
        ))
        count = len(record["point_action_ids"])
        require(points.shape == (count, 3) and stations.shape == point_rows.shape == (count,)
                and np.isfinite(points).all() and np.isfinite(stations).all(), "fresh point geometry arrays differ")
        for case in member["cases"]:
            case_id = case["case_id"]
            own_member = [row for row in case["members"] if row["member"] == HOST]
            require(len(own_member) == 1, "one fresh top rail member record per case required")
            row = own_member[0]
            require(row["conditional_material"] == material and row["point_action_count"] == count
                    and row["array_prefix"] == case_id + "__" + HOST, "fresh member material or array binding differs")
            values = arrays[row["array_prefix"] + "__point_force_free_couple_xyz"]
            saved_negative = arrays[row["array_prefix"] + "__internal_negative_grain_u_v"]
            require(values.shape == (count, 6) and np.isfinite(values).all()
                    and saved_negative.shape == (2 * len(record["stations_mm"]), 6)
                    and np.isfinite(saved_negative).all(), "fresh signed force/cut arrays differ")
            removed, profiles, washers = {}, {}, {}
            for side in SIDES:
                host, block = by_side[side][case_id], "top_outer_" + side + "_cleat"
                own = np.array([other == block for other in record["point_action_other_bodies"]])
                expected_rows = (set(range(1800, 1804)) | set(range(1834, 1852)) if side == "left"
                                 else set(range(1808, 1812)) | set(range(1870, 1888)))
                require(int(sum(own)) == 22 and {int(value) for value in point_rows[own]} == expected_rows,
                        "exact 22 incident source rows differ: " + block)
                source_actions = host["state"]["source_point_actions"]
                action_rows = {action["row"]: action for action in source_actions}
                require(len(source_actions) == len(action_rows) == 22 and set(action_rows) == expected_rows,
                        "fresh local source-row census differs: " + block)
                for index in np.flatnonzero(own):
                    identity = row_map[int(point_rows[index])]
                    action = action_rows[int(point_rows[index])]
                    require(identity["row_id"] == record["point_action_ids"][index] == action["identity"]
                            and action["ownership"] == identity["ownership"]
                            and {identity["ownership"]["first_body"], identity["ownership"]["second_body"]} == {HOST, block}
                            and np.max(abs(points[index] - action["point_xyz_mm"])) < GEOM_TOL,
                            "fresh source row ownership or point differs")
                    require(np.max(abs(values[index, :3] - action["force_xyz_n"])) < FORCE_TOL,
                            "fresh member/local individual source-row force differs")
                    # Retain the actual member free couples in both the full wrench and cut.
                removed[side] = own
                original = np.sum(np.column_stack([
                    values[own, :3], np.cross(points[own] - geometry["start"], values[own, :3]) + values[own, 3:],
                ]), axis=0)
                actions = host["physical_host_actions"]
                require(len(actions) == 576 and len(host["state"]["face_cells"]) == 16
                        and len(host["state"]["bolts"]) == 2, "top host physical action census differs")
                replacement = sum((physical.point_wrench(action["point_xyz_mm"], action["force_xyz_n"],
                                                         np.array(geometry["start"])) for action in actions), start=np.zeros(6))
                error = physical.compare_wrench(replacement, original, "whole-host fresh target: " + block + "/" + case_id)
                record_error(accounting, "group_replacement", error)
                profiles[side] = physical.bore_profiles(host, geom, wall)
                washers[side] = physical.washer_actions(host, geom, frame)
                require(len(profiles[side]) == 48 and len(washers[side]) == 512,
                        "48 axial bore measures / 512 washer measures per host required")
                datum = np.array(geometry["start"])
                full_face, _ = physical.face_negative(tiles_by_side[side], host, geometry, frame,
                                                     geom["grain_length_mm"] + 1, datum)
                full_by_kind = {
                    "supported_uniform_face": full_face,
                    "bore_wall": sum((wall.pressure_arc_wrench(profile, datum) for profile in profiles[side]), start=np.zeros(6)),
                    "washer_quadrature": sum((physical.point_wrench(action["point_xyz_mm"], action["force_xyz_n"], datum)
                                              for action in washers[side]), start=np.zeros(6)),
                }
                represented = sum(full_by_kind.values(), start=np.zeros(6))
                representation_error = physical.compare_wrench(represented, replacement, "supported full pressure recovery")
                record_error(accounting, "pressure_representation", representation_error)
                groups.append({
                    "case": case_id, "side": side, "removed_rows": sorted(expected_rows),
                    "removed_row_ids": [record["point_action_ids"][index] for index in np.flatnonzero(own)],
                    "fresh_point_full_external_wrench_at_start_global_n_nmm": original.tolist(),
                    "fresh_member_source_free_couple_sum_global_nmm": np.sum(values[own, 3:], axis=0).tolist(),
                    "current_full_external_wrench_at_start_global_n_nmm": replacement.tolist(),
                    "replacement_minus_fresh_point_global_n_nmm": error.tolist(),
                    "represented_full_pressure_wrench_at_start_global_n_nmm": represented.tolist(),
                    "pressure_representation_minus_saved_global_n_nmm": representation_error.tolist(),
                    "represented_full_external_by_kind_global_n_nmm": {name: value.tolist() for name, value in full_by_kind.items()},
                    "physical_host_actions": actions, "host_bore_pressure_profiles": profiles[side],
                })
            for section in sections:
                for before in (True, False):
                    index = 2 * section["saved_station_index"] + int(not before)
                    original_cut, datum = previous.global_cut(values, points, stations, geometry, section["station_mm"], before)
                    original_local = np.r_[frame @ original_cut[:3], frame @ original_cut[3:]]
                    replay_error = physical.compare_wrench(original_local, saved_negative[index], "fresh full signed point-cut replay", 1e-7, 1e-5)
                    record_error(accounting, "point_cut_replay", replay_error)
                    revised, replacements = original_cut.copy(), []
                    for side in SIDES:
                        own = removed[side]
                        old_internal, _ = previous.global_cut(values[own], points[own], stations[own], geometry, section["station_mm"], before)
                        new_negative, by_kind, face_records = physical.replacement_negative(
                            by_side[side][case_id], profiles[side], washers[side], tiles_by_side[side],
                            geometry, geom, frame, section, before, wall,
                        )
                        revised -= old_internal + new_negative
                        replacements.append({
                            "side": side, "fresh_point_negative_external_wrench_global_n_nmm": (-old_internal).tolist(),
                            "current_negative_external_wrench_global_n_nmm": new_negative.tolist(),
                            "current_negative_external_by_kind_global_n_nmm": by_kind, "finite_face_negative_records": face_records,
                        })
                    local = np.r_[frame @ revised[:3], frame @ revised[3:]]
                    results = duration_results(local, section, datum, frame, case_id, before, nominal, previous, material)
                    diagnostic = duration_results(original_local, section, datum, frame, case_id, before, nominal, previous, material)
                    summaries.extend(result["summary"] for result in results.values())
                    point_summaries.extend(result["summary"] for result in diagnostic.values())
                    for result in results.values():
                        record_error(accounting, "regional_recovery", result["nominal_section"]["reconstructed_minus_source_n_nmm"])
                    base_cut = {"case": case_id, "station_mm": section["station_mm"], "limit": "before" if before else "after",
                                "saved_trace_index": index, "cut_datum_global_xyz_mm": datum.tolist()}
                    cuts.append({**base_cut, "fresh_integrated_point_cut_global_n_nmm": original_cut.tolist(),
                                 "current_pressure_cut_global_n_nmm": revised.tolist(), "current_pressure_cut_grain_u_v_n_nmm": local.tolist(),
                                 "replacement_negative_records": replacements, "duration_results": results})
                    point_cuts.append({**base_cut, "fresh_integrated_point_cut_global_n_nmm": original_cut.tolist(),
                                       "fresh_integrated_point_cut_grain_u_v_n_nmm": original_local.tolist(), "duration_results": diagnostic})
    require(len(cuts) == len(point_cuts) == 144 and len(summaries) == len(point_summaries) == 288
            and len(groups) == 12, "finite fresh top-rail comparison census differs")
    comparison = comparison_summary(summaries)
    source_map = {key(path): digest for path, digest in sorted(pins.items())}
    common = {
        **previous.FLAGS, **FLAGS, "source_sha256": source_map,
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "case_ids": list(CASES), "host": HOST, "recorded_section_count": 12,
        "evaluated_trace_count": 144, "duration_comparison_count": 288,
        "source_force_state_scope": member["source_force_state_scope"],
        "source_hold_lever_mm": 100, "modeled_mass_kg": gravity["modeled_mass_kg"], "dead_load_factor": gravity["dead_load_factor"],
        "formal_authority": {"pending_criteria_count": 47, "release_flags_unchanged": release_flags},
        "geometry": {HOST: rail}, "opening_sections": {HOST: sections}, "conditional_material": material,
    }
    point_report = {
        **common, "schema": "knee-bridge-top-rail-fresh-point-diagnostic/v1",
        "status": "COMPLETE_FRESH_POINT_DIAGNOSTIC_NOT_ACCEPTANCE",
        "scope": "Original integrated-point placement method, recomputed only from the fresh member arrays; separate from finite physical pressure cuts.",
        "duration_comparison": comparison_summary(point_summaries), "cuts": point_cuts,
    }
    report = {
        **common, "schema": "knee-bridge-top-rail-local-pressure-cuts/v1",
        "status": "COMPLETE_FINITE_FRESH_TOP_RAIL_LOCAL_PRESSURE_COMPARISONS",
        "selected_top_block_state_count": 12, "excluded_bottom_block_state_count": 12,
        "replaced_rows_per_top_cleat": 22, "whole_interface_replacement_count": 12,
        "historical_section_evidence_usage": "Geometry, twelve sections and provenance only; no historical force, stress or pass is transferred.",
        "working_hypotheses": [
            "Uniform supported 4x4 face-tile pressure retains the original circular-mouth subtraction and saved clipped area/centroid checks; no pressure crosses a void.",
            "Host bore forces keep all 24 axial Gauss measures per bolt and the unchanged nonunique half-cosine radial wall pressure shape.",
            "Host washers keep the saved 8-radial/32-angular finite quadrature per bolt; no continuously integrated annulus or cut-error envelope is invented.",
            "Common longitudinal strain, area-proportional transverse force sharing, end-bridge compatibility and common rectangular twist retain the existing nominal ligament hypothesis.",
            "Original CD=1 is diagnostic; CD=1.25 is the existing conditional peak-load hypothesis. Every ratio and exceeding trace remains reported.",
        ],
        "limits": [
            "Same 250 lb times two / 300 N / 100 mm source loads and fresh gravity. Global FILLED-BORE gross compliance remains the declared MVP assumption.",
            "Only the two top cleats' original 22 rows each are replaced by saved local physical actions; all other member actions, including gravity, remain once and unchanged.",
            "Finite twelve bore/tangency sections only; no continuous maximum, concentration, splitting, free-warping or actual timber qualification is established.",
            "No added rocking couple, tie, load tuning, geometry tuning, stiffness tuning or displacement feedback. Actual changed-hole elastic stiffness, local bridge compatibility, stability and hardware remain unqualified.",
            "Proposal is unadopted. Global connector inventory remains 104; four proposed internal bolts stay separate static allocations, with proposal census 108/108/216/66.",
            "All 47 formal criteria stay pending and eight release flags stay false. Arithmetic comparisons authorize no drilling, fabrication or climbing.",
        ],
        "tolerances": {"geometry_mm": GEOM_TOL, "partition_mm": PARTITION_TOL,
                       "interface_force_n": FORCE_TOL, "interface_moment_nmm": MOMENT_TOL,
                       "point_cut_replay_force_n": 1e-7, "point_cut_replay_moment_nmm": 1e-5,
                       "radial_force_recovery_n": 1e-7, "radial_moment_recovery_nmm": 1e-6},
        "face_tiles": tiles_by_side, "whole_interface_accounting": groups, "accounting": accounting,
        "duration_comparison": comparison, "cuts": cuts, "point_diagnostic_file": "point-diagnostic.json",
    }
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(producer.read_bytes())
    dump(output / "point-diagnostic.json", point_report)
    dump(output / "checks.json", report)
    outputs = {name: sha(output / name) for name in (
        ".gitignore", "producer.py.snapshot", "point-diagnostic.json", "checks.json",
    )}
    authenticate(pins)
    dump(output / "receipt.json", {
        **previous.FLAGS, **FLAGS, "status": report["status"], "source_sha256": source_map, "output_sha256": outputs,
        "source_unchanged_before_and_after_arithmetic": True, "source_unchanged_before_and_after_write": True,
        "counts": {"top_block_states": 12, "rail_sections": 12, "signed_pressure_traces": 144,
                   "duration_comparisons": 288, "separate_point_diagnostic_traces": 144},
        "formal_authority": common["formal_authority"],
    })
    authenticate(pins)
    authenticate({output / name: digest for name, digest in outputs.items()})
    return {"status": report["status"], "output": key(output), "checks_sha256": sha(output / "checks.json"),
            "point_diagnostic_sha256": sha(output / "point-diagnostic.json"), "receipt_sha256": sha(output / "receipt.json"),
            "accounting": accounting, "duration_comparison": comparison}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    print(json.dumps(build(parser.parse_args().output), indent=2, sort_keys=True, allow_nan=False))
