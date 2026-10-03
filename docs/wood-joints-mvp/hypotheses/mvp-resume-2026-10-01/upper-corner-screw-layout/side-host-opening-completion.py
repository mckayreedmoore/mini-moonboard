"""Parent-run N08 side-host opening comparisons from authenticated saved data.

Import is inert. prepare(output) authenticates and joins metadata using stdlib
only. build(output) reuses the existing exact-slot and signed regional methods;
it calls no producer pipeline, mechanics solve, CAD, coupon, test or review.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
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
RAW = HERE / "rawlocal/side-host-opening-completion"
REMAINDER = HERE / "member-opening-remainder.py"
REMAINDER_RESULT = HERE / "rawlocal/member-opening-remainder/attempt02"
REFRESH_RESULT = HERE / "rawlocal/member-opening-refresh/attempt02"
HOST_RESULT = HERE / "rawlocal/top-host-net-sections/attempt02"
PROPOSAL = BASE / "top-corner-correction/proposal.json"
SIDES = ("base_side_left", "base_side_right")
TOL = 1e-5
SUPPORTED = "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE"
PINS = {
    REMAINDER: "5db858b30a69f393f46b493bc06c46ca2b786e85ed4ac520475d29cf51b25e62",
    REMAINDER_RESULT / "checks.json": "b328e9c19bd001bf542e79399f5b15f7b67c595e37d18ff035a9e13d177ae163",
    REMAINDER_RESULT / "receipt.json": "db5a48bc43ab7d953da9fa57df99ddac507dfe0b389f0d1907c5c946a93e6931",
    REFRESH_RESULT / "checks.json": "40beca5a3a5863612a0fadcee4b259f1edacf55f9c58035bc058918c1d64f7e8",
    REFRESH_RESULT / "receipt.json": "1b31e5582c67c5374bbabcfbbd179957aea976701fbb991f41a0268084d3d694",
    HOST_RESULT / "checks.json": "7e0977645a79d11b3456ff82cc987f2466becd135f192e6aca3c4c53875487a9",
    HOST_RESULT / "receipt.json": "486b7d5f5da12e78e94b0deb0c2ab8631f27c1992ee9b49f32c0554249eeff29",
    PROPOSAL: "5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2",
}
FLAGS = {
    "proposal_adopted": False, "reviewed_104_pass_transferred": False,
    "historical_demands_transferred": False, "prior_strength_pass_transferred": False,
    "native_CAD_or_frame_execution": False, "tests_run": False, "review_run": False,
    "original_producer_pipelines_executed": False,
    "geometry_material_duration_or_loads_changed": False,
    "gross_rectangle_fallback_used": False, "blind_bore_extended_to_through_slot": False,
    "new_resistance_established": False, "exact_finished_H_claimed": False,
    "local_pressure_interpretation_claimed": False,
    "splitting_or_tangential_fracture_assessed": False,
    "complete_joint_acceptance": False, "formal_criterion_acceptance": False,
    "physical_release": False, "fabrication_release": False,
}
LIMITS = [
    "Finite exact-slot geometry supplies nominal regional references, not concentration, splitting, anchorage or complete joint resistance.",
    "Common longitudinal strain, grain-end continuity, area-proportional transverse sharing, equal longitudinal shear moduli, common twist and free warping remain the existing hypotheses.",
    "The sufficient rectangle shear bound is conservative for the recorded nominal rectangular fields; it is not a bound on every physical perforated or blind-section stress field.",
    "Blind or partial cylinders retain connected pocket/bridge shapes outside the existing exact-slot method. Geometric inclusion alone does not establish conservative simultaneous N/V/M/T resistance.",
    "Clipped ends retain the existing lumped-point-load traction-distribution gap. Oblique cylinders, incomplete walls and unsupported overlapping openings remain explicit method limits.",
    "Fresh ce69/c3a8/62bd signed actions retain filled-bore gross compliance and point placement. Exact finished-hole H, distributed local bearing and continuous section maxima are not supplied.",
    "The separate 1320 refresh limits and 3336 remainder exceptions keep their own identities and methods; neither is recomputed or silently subtracted twice.",
]


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, record):
    with Path(path).open("x") as stream:
        json.dump(record, stream, indent=2, allow_nan=False)
        stream.write("\n")


def output_guard(output):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "fresh owned immediate output child required")
    return output


def module(path, expected):
    require(sha(path) == expected, "changed helper: " + str(path))
    spec = importlib.util.spec_from_file_location("side_host_" + Path(path).stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    result = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = old
    return result


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def metadata_gate(target, member, surface):
    """Join saved wall/face metadata; compute no regional section or stress."""
    station, g = target["station_mm"], member["geometry"]
    frame = [g[k] for k in ("axis", "section_u", "section_v")]
    features = {f["feature_id"]: f for f in surface["features"]}
    active = [b for b in member["bore_or_passage_intervals"] if b["lo"] - 1e-6 <= station <= b["hi"] + 1e-6]
    require({b["id"] for b in active} == set(target["feature_ids"]), "active interval/target binding differs")
    caps = {fid for fid, f in features.items() if f["surface_kind"] == "PLANE"
            and len(f["trim"]["wires"]) == 1 and f["trim"]["wires"][0]["edge_count"] == 1
            and f["trim"]["wires"][0]["edges"][0]["curve_kind"] == "CIRCLE"}
    longitudinal_sides = set()
    for plane in member["profile_planes"]:
        if plane["id"] in caps or not plane["lo"] - TOL <= station <= plane["hi"] + TOL:
            continue
        normal = [dot(row, plane["normal"]) for row in frame]
        if abs(normal[0]) < 1e-7:
            for axis in (1, 2):
                if abs(abs(normal[axis]) - 1) < 1e-7 and abs(normal[3 - axis]) < 1e-7:
                    longitudinal_sides.add((axis, 1 if normal[axis] > 0 else -1))
    if len(longitudinal_sides) != 4:
        return {"eligible_for_parent_exact_slot_method": False,
                "predicted_reason": "OUTER_PROFILE_OR_TERMINAL_POINT_LOAD_MODEL_INAPPLICABLE"}
    certificates = []
    for interval in active:
        feature = features.get(interval["id"])
        require(feature is not None and interval["id"] not in member["replaced_original_bore_features"],
                "active original feature identity lost or superseded")
        if feature["surface_kind"] != "CYLINDER":
            return {"eligible_for_parent_exact_slot_method": False,
                    "predicted_reason": "OPENING_SURFACE_HAS_NO_EXACT_CYLINDER_SLOT_RECIPE"}
        cylinder = feature["cylinder"]
        delta = [a - b for a, b in zip(cylinder["axis_origin_global_xyz_mm"], g["start"], strict=True)]
        point = [dot(row, delta) for row in frame]
        direction = [dot(row, cylinder["axis_unit_global_xyz"]) for row in frame]
        shaft = max(range(3), key=lambda i: abs(direction[i]))
        angular, axial = feature["trim"]["surface_parameter_bounds"]["u"], cylinder["axis_parameter_interval_mm"]
        radius = cylinder["radius_mm"]
        require(radius > 0 and abs(radius - interval["radius_mm"]) < TOL, "saved radius binding differs")
        if (cylinder["material_side_geometry"] != "bore_like" or shaft not in (1, 2)
                or abs(abs(direction[shaft]) - 1) >= 1e-7
                or max(abs(direction[i]) for i in range(3) if i != shaft) >= 1e-7):
            return {"eligible_for_parent_exact_slot_method": False,
                    "predicted_reason": "NONTRANSVERSE_OR_OBLIQUE_OPENING_REQUIRES_ANOTHER_SECTION_MODEL"}
        if (abs(angular[1] - angular[0] - 2 * math.pi) >= TOL
                or abs(feature["area_mm2"] - 2 * math.pi * radius * (axial[1] - axial[0])) >= 0.001):
            return {"eligible_for_parent_exact_slot_method": False,
                    "predicted_reason": "TRIMMED_WALL_HAS_NO_WHOLE_CYLINDER_CERTIFICATE"}
        ends = sorted(point[shaft] + direction[shaft] * x for x in axial)
        dimension = g["width_mm"] if shaft == 1 else g["depth_mm"]
        bounds = [-dimension / 2, dimension / 2]
        certificate = {"feature_id": interval["id"], "shaft_axis": shaft,
                       "saved_shaft_ends_mm": ends, "nominal_profile_shaft_bounds_mm": bounds,
                       "radius_mm": radius, "whole_cylinder_wall": True}
        if max(abs(a - b) for a, b in zip(ends, bounds, strict=True)) >= TOL:
            return {"eligible_for_parent_exact_slot_method": False,
                    "predicted_reason": "BLIND_OR_PARTIAL_SHAFT_NOT_A_COMPLETE_TRANSVERSE_SLOT",
                    "shaft_certificate": certificate}
        require(abs(interval["lo"] - (point[0] - radius)) < TOL
                and abs(interval["hi"] - (point[0] + radius)) < TOL, "saved grain interval/cylinder binding differs")
        certificates.append(certificate)
    return {"eligible_for_parent_exact_slot_method": True, "predicted_reason": None,
            "shaft_certificates": certificates, "section_and_resistance_arithmetic_executed": False}


def sources():
    """Reuse the frozen stdlib closure, then join the exact disjoint side gap."""
    for path, digest in PINS.items():
        require(sha(path) == digest, "changed frozen seed: " + str(path))
    method = module(REMAINDER, PINS[REMAINDER])
    api, pins, original_plan, members, surfaces = method.sources()
    old_result, refresh, host, proposal = [read(p) for p in (
        REMAINDER_RESULT / "checks.json", REFRESH_RESULT / "checks.json",
        HOST_RESULT / "checks.json", PROPOSAL)]
    require(old_result["source_sha256"] == api.source_map(pins), "accepted remainder source closure differs")
    for path, digest in PINS.items():
        api.bind(pins, path, digest)
    api.bind(pins, Path(__file__).resolve(), sha(__file__))
    for packet in (REFRESH_RESULT, REMAINDER_RESULT, HOST_RESULT):
        receipt = read(packet / "receipt.json")
        require(receipt["output_sha256"]["checks.json"] == pins[packet / "checks.json"], "result/receipt binding differs")
    for name, digest in refresh["source_sha256"].items():
        api.bind(pins, ROOT / name, digest)
    require(refresh["status"] == "COMPLETE_FINITE_COMPARISONS"
            and refresh["unique_signed_limit_count"] == 1320
            and refresh["duration_comparison_count"] == 1632
            and refresh["finite_targets_removed_from_uncalculated_set"] is True
            and refresh["side_hosts"]["complete_finite"] is True, "accepted refresh target coverage differs")
    require(old_result["finite_supported_arithmetic_complete"] is True
            and old_result["target_signed_limit_count"] == 10320
            and old_result["supported_signed_limit_count"] == 6984
            and old_result["method_inapplicable_signed_limit_count"] == 3336
            and old_result["side_host_signed_limits_still_outside_assignment"] == 2304,
            "accepted remainder/side gap partition differs")
    ledger = api.read(method.COVERAGE / "coverage.json")["uncalculated_fresh_opening_stations"]
    require(tuple(refresh["case_ids"]) == tuple(original_plan["case_ids"]) == api.CASES, "six cases differ")
    accepted, targets, bindings = [], [], []
    for body in SIDES:
        member, original_surface, saved_geometry = members[body], surfaces[body], host["geometry"][body]
        original = original_surface["step_binding"]
        current = ROOT / member["current_finished_step"]
        require(member["recess_source"] is None
                and set(member["replaced_original_bore_features"]) == {body + "/facet002", body + "/facet004"}
                and original["file_sha256"] == member["original_finished_step_sha256"]
                and saved_geometry["finished_step_path"] == member["current_finished_step"]
                and saved_geometry["finished_step_sha256"] == member["current_finished_step_sha256"]
                == proposal["proposal_step_sha256"][member["current_finished_step"]],
                "original/corrected side STEP binding differs: " + body)
        api.bind(pins, ROOT / original["path"], original["file_sha256"])
        api.bind(pins, current, member["current_finished_step_sha256"])
        accepted_indices = {s["saved_station_index"] for s in host["opening_sections"][body]}
        actual_indices = {s["saved_trace_index"] // 2 for s in refresh["cut_summaries"] if s["block"] == body}
        require(len(accepted_indices) == 13 and accepted_indices == actual_indices, "13 refreshed side indices differ")
        actual_limits = {(s["case"], s["saved_trace_index"]) for s in refresh["cut_summaries"] if s["block"] == body}
        require(actual_limits == {(case, 2 * i + side) for case in api.CASES for i in accepted_indices for side in (0, 1)},
                "accepted side six-case signed-limit identities differ")
        finished = [s for s in ledger if s["body"] == body and s["opening_identity_kind"] == "finished_geometry_interval"]
        own = [s for s in finished if s["station_index"] not in accepted_indices]
        require(len(finished) == 109 and len(own) == 96, "109/96 side station census differs")
        accepted.extend(s for s in finished if s["station_index"] in accepted_indices)
        for target in own:
            si = target["station_index"]
            require(target["station_mm"] == member["stations_mm"][si]
                    and target["saved_trace_indices"] == [2 * si, 2 * si + 1]
                    and target["case_ids"] == list(api.CASES) and target["limits"] == ["before", "after"]
                    and len(target["feature_ids"]) == 1, "exact side opening/station identity differs")
            targets.append({**target, "metadata_method_gate": metadata_gate(target, member, original_surface)})
        bindings.append({"body": body, "original_step": original,
            "current_finished_step": member["current_finished_step"],
            "current_finished_step_sha256": member["current_finished_step_sha256"],
            "replaced_original_feature_ids": member["replaced_original_bore_features"],
            "accepted_corrected_bore_ids": [b["opening_id"] for b in saved_geometry["bores"]],
            "scope": "Two correction-bound replacement bores and unchanged saved outer/other opening features; no new CAD or geometry."})
    require(len(targets) == 192 and len(accepted) == 26
            and not ({(s["body"], s["station_index"]) for s in targets}
                     & {(s["body"], s["station_index"]) for s in accepted}), "side target disjointness differs")
    candidate = sum(int(s["metadata_method_gate"]["eligible_for_parent_exact_slot_method"]) for s in targets)
    reasons = Counter(s["metadata_method_gate"]["predicted_reason"] for s in targets
                      if not s["metadata_method_gate"]["eligible_for_parent_exact_slot_method"])
    require(candidate == 108 and reasons == {
        "BLIND_OR_PARTIAL_SHAFT_NOT_A_COMPLETE_TRANSVERSE_SLOT": 78,
        "OUTER_PROFILE_OR_TERMINAL_POINT_LOAD_MODEL_INAPPLICABLE": 6}, "saved side method candidate census differs")
    api.authenticate(pins)
    plan = {"schema": "side_host_opening_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
        "source_count": len(pins), "source_sha256": api.source_map(pins),
        "producer_sha256": pins[Path(__file__).resolve()], "runtime": {"python": platform.python_version()},
        "force_basis": "unadopted108_ce69_c3a8_62bd", "case_ids": list(api.CASES),
        "dead_load_factor": original_plan.get("dead_load_factor", read(api.ASSESSMENT)["dead_load_factor"]),
        "source_load_identity": {"climber_weight_lb": 250, "dynamic_factor": 2, "signed_horizontal_force_n": 300,
                                 "hold_lever_mm": 100, "proportional_equipment_allowance_kg": 25},
        "body_ids": list(SIDES), "target_stations": targets, "target_station_count": len(targets),
        "target_signed_limit_count": 2304, "target_duration_record_count": 4608,
        "body_target_counts": dict(Counter(s["body"] for s in targets)),
        "expected_exact_slot_candidate_stations": candidate, "expected_supported_signed_limits": candidate * 12,
        "expected_supported_duration_records": candidate * 24,
        "expected_method_inapplicable_station_reasons": dict(reasons),
        "expected_method_inapplicable_signed_limits": (len(targets) - candidate) * 12,
        "actual_supported_comparisons_executed": False, "comparison_maxima": None,
        "duration_scenarios": method.DURATIONS, "finished_STEP_bindings": bindings,
        "separate_accepted_refresh_signed_limits": 1320, "excluded_accepted_side_stations": accepted,
        "separate_remainder_supported_signed_limits": 6984, "separate_remainder_method_inapplicable_signed_limits": 3336,
        "finished_opening_gap_before_this_arithmetic": 5640,
        "unmachined_exclusion_signed_limits_outside_assignment": 264,
        "original_terminal_inapplicable_signed_limits_outside_assignment": 1176,
        "floor_direction_adapter": original_plan["floor_direction_adapter"],
        "arithmetic_executed": False, "limits": LIMITS, **FLAGS}
    return api, method, pins, plan, members, surfaces, host


def start(output, pins):
    output_guard(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    require(sha(output / "producer.py.snapshot") == pins[Path(__file__).resolve()], "producer snapshot differs")


def finish(output, api, pins, status, arithmetic):
    api.authenticate(pins)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    dump(output / "receipt.json", {"schema": "side_host_opening_receipt/v1", "status": status,
        "source_count": len(pins), "source_sha256": api.source_map(pins), "output_sha256": outputs,
        "source_unchanged_before_and_after_write": True, "arithmetic_executed": arithmetic, **FLAGS})
    api.authenticate(pins)
    require(all(sha(output / name) == digest for name, digest in outputs.items()), "output changed after publication")


def prepare(output):
    output = output_guard(output)
    api, _, pins, plan, *_ = sources()
    start(output, pins)
    dump(output / "preparation.json", plan)
    finish(output, api, pins, plan["status"], False)
    return plan


def build(output):
    """Parent evaluates every exact signed cut and the supported regional method."""
    output = output_guard(output)
    api, method, pins, plan, members, surfaces, host = sources()
    import numpy as np

    replay, timber, net, header, remaining, previous, rail = [module(HERE / name, pins[HERE / name]) for name in (
        "knee-bridge-remaining-sections.py", "corner-timber-sections.py", "corner-net-section.py",
        "header-net-section.py", "remaining-net-sections.py", "top-host-net-sections.py", "knee-bridge-top-rail.py")]
    fresh, model, rows, _ = replay.source_context(pins)
    require(api.source_map(pins) == plan["source_sha256"] and rail.DURATIONS == plan["duration_scenarios"],
            "numerical context or duration assumptions differ")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    outer_at = previous.outer_rectangle_function()
    recipes = {}
    for target in plan["target_stations"]:
        body, gate = target["body"], target["metadata_method_gate"]
        recipe = method.recipe(target, members[body], surfaces[body], outer_at, timber, np)
        require((recipe["status"] == SUPPORTED) == gate["eligible_for_parent_exact_slot_method"]
                and (recipe["status"] == SUPPORTED or recipe["reason"] == gate["predicted_reason"]),
                "actual recipe/prepared saved metadata applicability differs")
        recipes[body, target["station_index"]] = recipe
    api.authenticate(pins)
    start(output, pins)
    dump(output / "preparation.json", plan)
    dump(output / "section-recipes.json", {"recipes": list(recipes.values()), "limits": LIMITS})
    material = read(api.MATERIALS)
    summaries, audits, exclusions, count = [], [], [], 0
    with (np.load(api.ARRAYS, allow_pickle=False) as arrays,
          np.load(api.RESPONSE, allow_pickle=False) as response,
          np.load(api.GRAVITY / "operators.npz", allow_pickle=False) as operators,
          gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
        action_rows = method.private_action_rows(rows, model, operators["D"], plan["floor_direction_adapter"], np)
        direction_audit = {**plan["floor_direction_adapter"], "full_D_join_executed": True,
                           "original_actions_for_guard_retained": True, "source_metadata_mutated": False}
        dump(output / "ownership-direction-map.json", direction_audit)
        for body in SIDES:
            member, g = members[body], members[body]["geometry"]
            frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
            targets = [s for s in plan["target_stations"] if s["body"] == body]
            for case in fresh["cases"]:
                source, _, negative, audit = replay.actions_for(case, body, member, arrays, response,
                    operators["D"], operators["W"], model, action_rows, header)
                binding, _ = replay.material_for(source, material, net, host["conditional_material_by_host"][body])
                audit.update(private_floor_direction_adapter_used=True, conditional_material=binding)
                audits.append(audit)
                prefix = source["array_prefix"]
                for target in targets:
                    si, station = target["station_index"], target["station_mm"]
                    recipe = recipes[body, si]
                    for before in (True, False):
                        index = 2 * si + int(not before)
                        cut, datum = previous.global_cut(arrays[prefix + "__point_force_free_couple_xyz"],
                            arrays[body + "__point_xyz_mm"], arrays[body + "__point_stations_mm"], g, station, before)
                        local = np.r_[frame @ cut[:3], frame @ cut[3:]]
                        replay.difference(local, negative[index], "complete fresh signed side-host cut")
                        record = {"body": body, "case": case["case_id"], "station_mm": station,
                            "saved_station_index": si, "saved_trace_index": index,
                            "limit": "before" if before else "after", "opening_feature_ids": target["feature_ids"],
                            "recipe_status": recipe["status"], "method": "original_signed_point_placement",
                            "cut_global_xyz_n_nmm": cut.tolist(), "cut_grain_u_v_n_nmm": local.tolist(),
                            "cut_datum_global_xyz_mm": datum.tolist()}
                        if recipe["status"] == SUPPORTED:
                            section = {**recipe["section"], "saved_station_index": si}
                            results = rail.duration_results(local, section, datum, frame, case["case_id"], before, net, previous, binding)
                            require(set(results) == set(method.DURATIONS), "two duration records required")
                            for result in results.values():
                                nominal = result["nominal_section"]
                                replay.difference(nominal["reconstructed_signed_cut_n_nmm"], local,
                                                  "regional centroid/full signed-wrench recovery")
                                summary = remaining.cut_summary(case["case_id"], body, index, section, nominal)
                                summary.update(result["summary"])
                                summary["comparison_outcomes"] = method.outcomes(summary)
                                result["summary"] = summary
                                summaries.append(summary)
                            record["duration_results"] = results
                        else:
                            record.update(reason=recipe["reason"], duration_results={name: {
                                "CD": duration, "outcome": "METHOD_INAPPLICABLE_NOT_A_PASS",
                                "comparison_outcomes": method.outcomes({})} for name, duration in method.DURATIONS.items()})
                            exclusions.append({"body": body, "station_index": si, "station_mm": station,
                                "case": case["case_id"], "limit": record["limit"], "saved_trace_index": index,
                                "feature_ids": target["feature_ids"], "reason": recipe["reason"]})
                        stream.write(json.dumps(record, separators=(",", ":"), allow_nan=False) + "\n")
                        count += 1
    supported = sum(int(recipe["status"] == SUPPORTED) for recipe in recipes.values())
    require(count == 2304 and len(audits) == 12 and supported == 108
            and len(summaries) == 2592 and len(exclusions) == 1008, "actual side arithmetic/exception census differs")
    comparisons = method.summarize(summaries)
    require(comparisons["complete_finite"], "supported comparisons include absent/nonfinite metrics")
    matrix = []
    for body in SIDES:
        for duration in method.DURATIONS:
            selected = [s for s in summaries if s["block"] == body and s["duration_scenario"] == duration]
            require(len(selected) == 648, "body/duration finite coverage differs")
            matrix.append({"body": body, "duration_scenario": duration, "target_signed_limits": 1152,
                "supported_signed_limits": 648, "method_inapplicable_signed_limits": 504, **method.summarize(selected)})
    result = {"schema": "side_host_opening_completion/v1",
        "status": "COMPLETE_SUPPORTED_ARITHMETIC_WITH_EXPLICIT_INAPPLICABLE_TARGETS",
        "source_count": len(pins), "source_sha256": api.source_map(pins),
        "producer_sha256": pins[Path(__file__).resolve()], "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "case_ids": plan["case_ids"], "force_basis": plan["force_basis"], "dead_load_factor": plan["dead_load_factor"],
        "target_station_count": 192, "target_signed_limit_count": count, "supported_station_count": supported,
        "supported_signed_limit_count": supported * 12, "finite_duration_record_count": len(summaries),
        "method_inapplicable_station_count": len(recipes) - supported, "method_inapplicable_signed_limit_count": len(exclusions),
        "method_inapplicable_signed_limit_reasons": dict(Counter(s["reason"] for s in exclusions)),
        "inapplicable_cut_identities": exclusions, "comparisons": comparisons, "coverage_matrix": matrix,
        "finite_supported_arithmetic_complete": True, "all_assigned_opening_strength_comparisons_finite": False,
        "all_N08_finished_opening_comparisons_complete": False,
        "separate_accepted_refresh_signed_limits": 1320, "separate_remainder_supported_signed_limits": 6984,
        "separate_remainder_method_inapplicable_signed_limits": 3336,
        "finished_opening_gap_after_this_finite_arithmetic": 3336 + len(exclusions),
        "unmachined_exclusion_signed_limits_outside_assignment": 264,
        "original_terminal_inapplicable_signed_limits_outside_assignment": 1176,
        "finished_STEP_bindings": plan["finished_STEP_bindings"],
        "floor_direction_adapter": {k: v for k, v in direction_audit.items() if k != "mappings"},
        "arithmetic_executed": True, "limits": LIMITS, **FLAGS}
    api.authenticate(pins)
    dump(output / "action-audits.json", {"audits": audits})
    dump(output / "checks.json", result)
    finish(output, api, pins, result["status"], True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="stdlib source/metadata joins only")
    args = parser.parse_args()
    packet = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": packet["status"], "source_count": packet["source_count"]}))
