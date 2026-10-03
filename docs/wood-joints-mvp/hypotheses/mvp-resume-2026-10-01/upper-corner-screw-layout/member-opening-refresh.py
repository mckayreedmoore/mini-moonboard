"""Parent-run finite opening arithmetic; import and --prepare use stdlib only.

Historical packets provide exact section recipes, never historical demands.
No imported producer build, solve, coupon, CAD, or test entry point is called.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import sys
from collections import Counter
from functools import cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = HERE.parent
RAW = HERE / "rawlocal/member-opening-refresh"
FRESH = BASE / "member-screen-attempt02/knee-bridge-gravity01"
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
FRAME = HERE / "rawlocal/knee-bridge-frame/attempt02/response"
CORNER = HERE / "rawlocal/knee-bridge-corner-replay/attempt01"
GROUP = HERE / "rawlocal/corner-group-finish/attempt03"
HOST = HERE / "rawlocal/top-host-net-sections/attempt02"
COVERAGE = HERE / "rawlocal/member-opening-coverage/attempt03"
MATERIAL = BASE.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
CASES = ("a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear")
CLEATS = ("top_outer_left_cleat", "top_outer_right_cleat",
          "bottom_outer_left_cleat", "bottom_outer_right_cleat")
SIDES = ("base_side_left", "base_side_right")
METRICS = ("normal_reference_sum", "total_tension_over_Ft", "total_compression_over_Fc",
           "absolute_bending_over_Fb", "same_state_shear_bound_over_Fv",
           "transverse_shear_over_Fv", "torsional_shear_over_Fv")
FACE_METRICS = ("compatible_face_peak_over_Fv", "scalar_shear_bound_over_Fv",
                "sufficient_rectangle_bound_over_Fv")
PINS = {
    FRESH / "member-results.json": "5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0",
    FRESH / "action-section-arrays.npz": "3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596",
    FRESH / "geometry.json": "c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af",
    FRESH / "inputs.json": "34219c91e8b23588f76f4e2e2b6c564b25e1b979ccd4106dd0002c9f03cc0457",
    GRAVITY / "operator-assessment.json": "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    FRAME / "comparison.json": "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    FRAME / "response.npz": "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    CORNER / "checks.json": "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    CORNER / "receipt.json": "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    GROUP / "checks.json": "2ae3a84f273823dc6ca751e6fdddab8e0d70425ee7b34e1e38ebc79d5b672f23",
    GROUP / "receipt.json": "f1d8ad0f204be457f5b8eba2e8185828456251ae7fb67aa945bb7477bacd2f62",
    HOST / "checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    HOST / "receipt.json": "486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29",
    COVERAGE / "coverage.json": "a9dc39d5dbd153c7928923caf79dcf678e653c0b707a35514e1177c8bd4337b2",
    COVERAGE / "receipt.json": "5d9dba87ff93e0a218d5c74d7dc4830708bf2ac4b263bf229dde69b245737f02",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    BASE / "member_stability.py": "eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72",
    HERE / "knee-bridge-remaining-sections.py": "e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15",
    HERE / "corner-group-finish.py": "182523c1be28071f74097eed9f36e39978a519b8f6efd6d8447f86e922debd19",
    HERE / "corner-bore-wall.py": "0ad9c88be2496f1b2ae9b06cb31f0cb7d9d95a236ffb4b2dc586873b7cf4a185",
    HERE / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "header-net-section.py": "d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328",
    HERE / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    HERE / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    HERE / "knee-bridge-top-rail.py": "d8f4a84ab8c6fefcdce4ba65a6812de6a7e6199ea69f67c3fb4fde1252681fec",
}
FLAGS = {"native_CAD_or_frame_execution": False, "tests_run": False,
         "original_producer_pipelines_executed": False, "historical_demands_transferred": False,
         "physical_release": False, "complete_joint_acceptance": False,
         "formal_criterion_acceptance": False, "splitting_or_tangential_fracture_assessed": False,
         "geometry_material_duration_or_loads_changed": False,
         "local_redistribution_feeds_back_to_frame": False, "balancing_free_couples_added": 0}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def key(path):
    return str(Path(path).relative_to(ROOT))


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path)
    require(path not in pins or pins[path] == digest, "conflicting pin: " + key(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "changed frozen source: " + key(path))


def source_map(pins):
    return {key(p): h for p, h in sorted(pins.items())}


def prepare_sources():
    """Authenticate a finite saved-source join; do not import numerical helpers."""
    pins = dict(PINS)
    bind(pins, Path(__file__).resolve(), sha(__file__))
    authenticate(pins)
    fresh, corner, group, host, coverage, gravity = [read(p) for p in (
        FRESH / "member-results.json", CORNER / "checks.json", GROUP / "checks.json",
        HOST / "checks.json", COVERAGE / "coverage.json", GRAVITY / "operator-assessment.json")]
    for directory, name in ((CORNER, "checks.json"), (GROUP, "checks.json"),
                            (HOST, "checks.json"), (COVERAGE, "coverage.json")):
        receipt = read(directory / "receipt.json")
        require(receipt["output_sha256"][name] == pins[directory / name], "result/receipt mismatch")
    # Saved fresh extraction and replay supply the complete current provenance
    # closure. Historical demand pipelines are not imported or re-executed.
    for packet in (fresh, corner, read(CORNER / "receipt.json")):
        for relative, digest in packet["source_sha256"].items():
            bind(pins, ROOT / relative, digest)
    for relative, digest in gravity["output_sha256"].items():
        bind(pins, GRAVITY / relative, digest)
    for name in ("geometry.json", "inputs.json", "action-section-arrays.npz"):
        require(fresh["output_sha256"][name] == pins[FRESH / name], "fresh extraction output mismatch")
    require(corner["fresh_load_sources"] == {key(p): pins[p] for p in (
        GRAVITY / "operator-assessment.json", FRAME / "comparison.json", FRAME / "response.npz")},
        "physical replay does not use ce69/c3a8")
    require(corner["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES"
            and tuple(corner["case_ids"]) == tuple(fresh_case["case_id"] for fresh_case in fresh["cases"])
            == tuple(coverage["case_ids"]) == CASES, "fresh six-case replay incomplete")
    require(corner["dead_load_factor"] == fresh["same_state_dead_load_factor"]
            == gravity["dead_load_factor"] == 1.1110134616260479, "dead factor changed")
    require(len(corner["states"]) == 24 and {
        (s["cleat"], s["case_id"]) for s in corner["states"]
    } == {(body, case) for body in CLEATS for case in CASES}, "24 distinct physical states required")
    for state in corner["states"]:
        require(state["cleat"] == state["level"] + "_outer_" + state["side"] + "_cleat",
                "corner level/side identity differs")
        for host_record in state["hosts"].values():
            local = host_record["state"]
            require(local["case_id"] == state["case_id"] and local["gap_scale"] == 1.0
                    and local["source_comparison_sha256"] == pins[FRAME / "comparison.json"]
                    and local["source_response_sha256"] == pins[FRAME / "response.npz"]
                    and local["source_gravity_assessment_sha256"] == pins[GRAVITY / "operator-assessment.json"],
                    "physical host state does not use the fresh nominal case")
    members = read(FRESH / "geometry.json")["members"]
    ledger = coverage["uncalculated_fresh_opening_stations"]
    targets = {body: [s for s in ledger if s["body"] == body] for body in CLEATS}
    require([len(targets[b]) for b in CLEATS] == [26, 26, 16, 16], "84 corner station identities changed")
    for body in SIDES:
        targets[body] = []
        sections = host["opening_sections"][body]
        require(len(sections) == 13, "13 side-host sections required")
        for section in sections:
            own = [s for s in ledger if s["body"] == body and s["station_index"] == section["saved_station_index"]]
            require(len(own) == 1 and own[0]["station_mm"] == section["station_mm"], "side target absent from frozen gap")
            targets[body].append(own[0])
    for body, stations in targets.items():
        record = members[body]
        bind(pins, ROOT / record["current_finished_step"], record["current_finished_step_sha256"])
        if body in CLEATS:
            require(group["source_sha256"][record["current_finished_step"]]
                    == record["current_finished_step_sha256"], "source104 cleat geometry changed")
        else:
            geom = host["geometry"][body]
            require(geom["finished_step_path"] == record["current_finished_step"]
                    and geom["finished_step_sha256"] == record["current_finished_step_sha256"],
                    "source104 side-host geometry changed")
        for station in stations:
            i = station["station_index"]
            require(record["stations_mm"][i] == station["station_mm"]
                    and station["saved_trace_indices"] == [2 * i, 2 * i + 1]
                    and station["case_ids"] == list(CASES)
                    and station["opening_identity_kind"] == "finished_geometry_interval",
                    "current finished-opening identity changed")
    selected = {(b, s["station_index"]) for b, rows in targets.items() for s in rows}
    remaining = [s for s in ledger if (s["body"], s["station_index"]) not in selected]
    require(len(selected) == 110 and len(remaining) == 1074, "finite target census changed")
    remaining_counts = Counter(s["opening_identity_kind"] for s in remaining)
    authenticate(pins)
    prepared = {
        "schema": "member_opening_refresh_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
        "runtime": {"python": platform.python_version(), "numpy_installed": importlib.metadata.version("numpy")},
        "source_count": len(pins), "source_sha256": source_map(pins),
        "producer_sha256": pins[Path(__file__).resolve()], "case_ids": list(CASES),
        "target_stations": targets, "corner_grain_limit_count": 1008,
        "side_host_limit_count": 312, "side_host_duration_comparison_count": 624,
        "total_limit_count": 1320, "total_duration_comparison_count": 1632,
        "arithmetic_executed": False,
        "future_if_targets_finite": {
            "finished_opening_signed_traces": remaining_counts["finished_geometry_interval"] * 12,
            "unmachined_exclusion_signed_traces": remaining_counts["modeled_station_exclusion_only"] * 12,
            "inapplicable_terminal_signed_traces": 1176,
            "remaining_station_identities": remaining}, **FLAGS,
    }
    return pins, prepared, fresh, corner, group, host, members


def helper(filename):
    path = HERE / filename
    require(sha(path) == PINS[path], "changed arithmetic helper: " + filename)
    spec = importlib.util.spec_from_file_location("opening_refresh_" + path.stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, "missing helper loader")
    module = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    return module


def outcomes(summary, metrics):
    """An absent/nonfinite comparison is uncalculated, never a pass."""
    result = {}
    for metric in metrics:
        value = summary.get(metric)
        finite = isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)
        result[metric] = {"value": value if finite else None, "outcome": (
            "UNCALCULATED" if not finite else "SUPPORTED_REFERENCE_COMPARISON_AT_OR_BELOW_ONE"
            if value <= 1 else "EVALUATED_FACE_EXCEEDS_REFERENCE" if metric == "compatible_face_peak_over_Fv"
            else "SUFFICIENT_SHEAR_BOUND_ABOVE_ONE" if metric in (
                "same_state_shear_bound_over_Fv", "transverse_shear_over_Fv",
                "scalar_shear_bound_over_Fv", "sufficient_rectangle_bound_over_Fv")
            else "NOMINAL_TORSIONAL_SHEAR_EXCEEDS_REFERENCE" if metric == "torsional_shear_over_Fv"
            else "NOMINAL_REFERENCE_COMPARISON_ABOVE_ONE")}
    return result


def comparison_summary(rows, metrics, expected):
    require(len(rows) == expected, "comparison record count differs")
    result = {}
    for metric in metrics:
        values = [(row, row["comparison_outcomes"][metric]["value"]) for row in rows]
        finite = [(row, value) for row, value in values if value is not None]
        witness = max(finite, key=lambda item: item[1])[0] if finite else None
        result[metric] = {"expected": expected, "finite": len(finite), "uncalculated": expected - len(finite),
                          "above_one": sum(int(value > 1) for _, value in finite),
                          "at_or_below_one": sum(int(value <= 1) for _, value in finite), "maximum_witness": witness}
    return {"expected_comparison_count": expected,
            "complete_finite": all(r["finite"] == expected for r in result.values()),
            "all_computed_comparisons_at_or_below_one": all(
                r["finite"] == expected and r["above_one"] == 0 for r in result.values()), "metrics": result}


def start_output(output, pins):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "new owned immediate output child required")
    authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def finish(output, pins, status, arithmetic):
    authenticate(pins)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    dump(output / "receipt.json", {"schema": "member_opening_refresh_receipt/v1", "status": status,
         "source_count": len(pins), "source_sha256": source_map(pins), "output_sha256": outputs,
         "source_unchanged_before_and_after_arithmetic_and_write": True,
         "arithmetic_executed": arithmetic, **FLAGS})
    authenticate(pins)
    require(all(sha(output / name) == digest for name, digest in outputs.items()), "output changed after write")


def prepare(output):
    pins, prepared, *_ = prepare_sources()
    output = start_output(output, pins)
    dump(output / "preparation.json", prepared)
    finish(output, pins, prepared["status"], False)
    return prepared


def build(output):
    """Parent serializes this API. Read saved sources; run only finite arithmetic."""
    pins, prepared, _, corner, group_saved, host_saved, members = prepare_sources()
    import numpy as np

    replay, group, wall, timber, net, header, remaining, previous, rail = [helper(name) for name in (
        "knee-bridge-remaining-sections.py", "corner-group-finish.py", "corner-bore-wall.py",
        "corner-timber-sections.py", "corner-net-section.py", "header-net-section.py",
        "remaining-net-sections.py", "top-host-net-sections.py", "knee-bridge-top-rail.py")]
    fresh, model, rows, _ = replay.source_context(pins)
    require(source_map(pins) == prepared["source_sha256"], "numerical context expanded prepared closure")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    material = read(MATERIAL)
    bottom_preparation = {"groups": [{"side": p["side"], "host": p["host"],
                                      "n": p["normal_host_to_cleat_xyz"]}
                                     for p in corner["preparation"] if p["level"] == "bottom"]}
    output = start_output(output, pins)
    dump(output / "preparation.json", prepared)
    corner_summaries, side_summaries, audits = [], [], []
    certificates = {}
    with (np.load(FRESH / "action-section-arrays.npz", allow_pickle=False) as arrays,
          np.load(FRAME / "response.npz", allow_pickle=False) as response,
          np.load(GRAVITY / "operators.npz", allow_pickle=False) as operators,
          gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
        for body in CLEATS + SIDES:
            member = members[body]
            geom = group_saved["geometries"][body] if body in CLEATS else host_saved["geometry"][body]
            frame = np.array(geom["grain_frame_rows_xyz"])
            g = member["geometry"]
            require(np.max(abs(frame - np.array([g[k] for k in ("axis", "section_u", "section_v")]))) < 1e-6,
                    "retained grain identity differs")
            if body in CLEATS:
                certificates[body] = group.geometry_certificate(geom)
                require(np.max(abs(np.array(geom["start_xyz_mm"]) - g["start"])) < 1e-6
                        and np.max(abs(np.array(geom["width_depth_mm"]) - [g["width_mm"], g["depth_mm"]])) < 1e-6,
                        "retained stock/start identity differs")
            for case in fresh["cases"]:
                source, saved_actions, negative, audit = replay.actions_for(
                    case, body, member, arrays, response, operators["D"], operators["W"], model, rows, header)
                binding, refs = replay.material_for(source, material, net,
                    host_saved["conditional_material_by_host"][body] if body in SIDES else None)
                audit["conditional_material"] = binding
                if body in CLEATS:
                    state = next(s for s in corner["states"] if s["cleat"] == body and s["case_id"] == case["case_id"])
                    actions = state["physical_cleat_actions"] + state["own_weight_actions_once"]
                    require(len(state["own_weight_actions_once"]) == 20, "fresh cleat weight census differs")
                    for action in actions:
                        require(all(k not in action or max(abs(v) for v in action[k]) == 0
                                    for k in ("free_moment_nmm", "free_couple_xyz_nmm")), "unhandled physical free couple")
                    loads = {a["source_id"].removeprefix("body_load_node_"): a for a in saved_actions
                             if a["role"] == "discrete_body_load"}
                    weights = state["own_weight_actions_once"]
                    require(len(loads) == len(weights) and {a["identity"] for a in weights} == set(loads),
                            "fresh gravity node identity differs")
                    for weight in weights:
                        saved = loads[weight["identity"]]
                        require(np.max(abs(np.array(weight["point_xyz_mm"]) - saved["point_mm"])) < 1e-6
                                and np.max(abs(np.array(weight["force_xyz_n"]) - saved["force_n"])) < 1e-7,
                                "weight changed or counted twice")
                    points = (np.array([a["point_xyz_mm"] for a in actions]) - geom["start_xyz_mm"]) @ frame.T
                    forces = np.array([a["force_xyz_n"] for a in actions]) @ frame.T
                    require(np.isfinite(points).all() and np.isfinite(forces).all(), "nonfinite physical action")
                    full = np.r_[forces.sum(axis=0), np.cross(points, forces).sum(axis=0)]
                    datum_local = frame @ (np.array(state["common_datum_xyz_mm"]) - geom["start_xyz_mm"])
                    global_full = np.r_[frame.T @ full[:3], frame.T @ (full[3:] - np.cross(datum_local, full[:3]))]
                    replay.difference(global_full, state["physical_whole_cleat_residual_n_nmm"], "physical residual identity", 1e-7, 1e-7)
                    saved_full = header.wrench(saved_actions, state["common_datum_xyz_mm"])
                    audit["physical_minus_source_full_wrench_n_nmm"] = replay.difference(
                        global_full, saved_full, "physical/source full wrench", 0.002, 0.4)
                    require(max(abs(full[:3])) <= 0.002
                            and max(abs(frame @ global_full[3:])) <= 0.4, "physical whole-body balance failed")
                    profiles = group.pressure_profiles(state, geom, wall,
                        None if state["level"] == "top" else bottom_preparation)
                    mask = np.array([a["kind"] != "bore_station_resultant" for a in actions])
                    require(len(profiles) == 96 and int((~mask).sum()) == 96, "four-bore pressure census differs")
                    bore = np.r_[forces[~mask].sum(axis=0), np.cross(points[~mask], forces[~mask]).sum(axis=0)]
                    represented = sum((wall.pressure_arc_wrench(p, np.zeros(3)) for p in profiles), np.zeros(6))
                    audit["bore_pressure_full_wrench_delta_n_nmm"] = replay.difference(represented, bore, "bore pressure recovery", 1e-7, 1e-7)
                    audit["physical_actions"] = actions
                    audit["bore_pressure_profiles"] = profiles
                    point_q = np.c_[forces[mask], np.cross(points[mask], forces[mask])]
                    point_p = points[mask]
                audits.append(audit)
                for target in prepared["target_stations"][body]:
                    station, si = target["station_mm"], target["station_index"]
                    section = timber.section(geom, station) if body in CLEATS else next(
                        s for s in host_saved["opening_sections"][body] if s["saved_station_index"] == si)
                    require(section["net_area_mm2"] > 0 and section["regions"], "no positive retained section")
                    if body in CLEATS:
                        _, _, matrix, _ = group.cut_material(geom, 0, station)
                        require(abs(section["net_area_mm2"] - matrix[0, 0]) < 1e-7, "exact cut area differs")
                    for before in (True, False):
                        index, limit = 2 * si + int(not before), "before" if before else "after"
                        if body in CLEATS:
                            included = point_p[:, 0] < station - 1e-6 if before else point_p[:, 0] <= station + 1e-6
                            external = point_q[included].sum(axis=0)
                            datum_local = np.array([station, 0, 0])
                            external[3:] -= np.cross(datum_local, external[:3])
                            external += sum((group.partial_wall(p, 0, station, limit, wall) for p in profiles), np.zeros(6))
                            local = -external
                            opposite = full.copy()
                            opposite[3:] -= np.cross(datum_local, opposite[:3])
                            opposite -= external
                            replay.difference(local, opposite, "physical opposed halves", 0.002, 0.4)
                            nominal = net.nominal_section(local, section["regions"], refs)
                            nominal["references"] = refs
                            summary = remaining.cut_summary(case["case_id"], body, index, section, nominal)
                            summary.update(duration_scenario="original_CD1", CD=1.0)
                            summary["comparison_outcomes"] = outcomes(summary, METRICS)
                            corner_summaries.append(summary)
                            results = {"original_CD1": {"summary": summary, "nominal_section": nominal}}
                        else:
                            prefix = source["array_prefix"]
                            cut, datum = previous.global_cut(arrays[prefix + "__point_force_free_couple_xyz"],
                                arrays[body + "__point_xyz_mm"], arrays[body + "__point_stations_mm"], g, station, before)
                            local = np.r_[frame @ cut[:3], frame @ cut[3:]]
                            replay.difference(local, negative[index], "saved signed side-host cut replay")
                            results = rail.duration_results(local, section, datum, frame, case["case_id"], before,
                                                            net, previous, binding)
                            require(set(results) == {"original_CD1", "conditional_peak_CD1_25"}, "duration scenarios changed")
                            for result in results.values():
                                summary = remaining.cut_summary(case["case_id"], body, index, section, result["nominal_section"])
                                summary.update(result["summary"])
                                summary["comparison_outcomes"] = outcomes(summary, METRICS + FACE_METRICS)
                                result["summary"] = summary
                                side_summaries.append(summary)
                        for result in results.values():
                            replay.difference(result["nominal_section"]["reconstructed_signed_cut_n_nmm"],
                                              local, "regional signed-wrench recovery")
                        record = {"body": body, "case": case["case_id"], "saved_trace_index": index,
                                  "station_mm": station, "limit": limit, "opening_identity": target,
                                  "method": "physical_half_cosine_bore_pressure" if body in CLEATS else "original_signed_point_placement",
                                  "cut_grain_u_v_n_nmm": local.tolist(), "section": section, "duration_results": results}
                        stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
    authenticate(pins)
    corner_result = comparison_summary(corner_summaries, METRICS, 1008)
    side_result = comparison_summary(side_summaries, METRICS + FACE_METRICS, 624)
    complete = corner_result["complete_finite"] and side_result["complete_finite"]
    coverage_matrix = []
    for body in CLEATS + SIDES:
        own_rows = corner_summaries if body in CLEATS else side_summaries
        metrics = METRICS if body in CLEATS else METRICS + FACE_METRICS
        durations = ("original_CD1",) if body in CLEATS else ("original_CD1", "conditional_peak_CD1_25")
        expected = 12 * len(prepared["target_stations"][body])
        for duration in durations:
            selected = [s for s in own_rows if s["block"] == body and s["duration_scenario"] == duration]
            coverage_matrix.append({"body": body, "duration_scenario": duration,
                                    **comparison_summary(selected, metrics, expected)})
    result = {"schema": "member_opening_refresh/v1",
              "status": "COMPLETE_FINITE_COMPARISONS" if complete else "INCOMPLETE_UNCALCULATED_COMPARISONS",
              "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "source_count": len(pins), "source_sha256": source_map(pins),
              "case_ids": list(CASES), "corner_grain": corner_result, "side_hosts": side_result,
              "coverage_matrix": coverage_matrix,
              "unique_signed_limit_count": 1320, "duration_comparison_count": 1632,
              "geometry_certificates": certificates, "cut_summaries": corner_summaries + side_summaries,
              "future_if_targets_finite": prepared["future_if_targets_finite"],
              "finite_targets_removed_from_uncalculated_set": complete,
              "arithmetic_executed": True, **FLAGS}
    dump(output / "checks.json", result)
    dump(output / "action-audits.json", {"audits": audits})
    finish(output, pins, result["status"], True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="stdlib authentication/join only; no arithmetic")
    args = parser.parse_args()
    packet = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": packet["status"], "source_count": packet["source_count"],
                      "output": str(args.output)}, sort_keys=True))
