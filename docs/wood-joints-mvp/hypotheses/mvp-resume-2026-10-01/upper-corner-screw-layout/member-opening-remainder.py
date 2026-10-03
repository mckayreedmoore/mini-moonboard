"""Parent-run N08 arithmetic for the 18 remaining frame members.

Import and --prepare are stdlib-only. build(output) evaluates authenticated
finished opening cuts with existing rectangle/through-slot resistance helpers.
Unsupported geometry is explicit and never replaced by a gross rectangle.
"""

from __future__ import annotations

import argparse
import copy
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
BASE = HERE.parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/member-opening-remainder"
COVERAGE = HERE / "rawlocal/member-opening-coverage/attempt03"
SURFACES = BASE.parent / "current-finished-feature-register-2026-10-01/surfaces.json"
PIN_HELPER = HERE / "knee-bridge-members.py"
PIN_HELPER_SHA = "bc0704d2c4f7cb6dc472a139b382e514ab69f0a8de02f05a19a3266de6addb0b"
PROJECTION_BASE = BASE.parent / "mvp-acceleration-2026-09-28"
PROJECTION_CONTRACT = PROJECTION_BASE / "current-frame-physical-connector-projection-contract-attempt01/projection-contract.json"
PROJECTION_INPUTS = PROJECTION_BASE / "current-frame-connector-compliance-attempt04/inputs.json"
SIDES = {"base_side_left", "base_side_right"}
METRICS = ("normal_reference_sum", "total_tension_over_Ft", "total_compression_over_Fc",
           "absolute_bending_over_Fb", "same_state_shear_bound_over_Fv",
           "transverse_shear_over_Fv", "torsional_shear_over_Fv",
           "compatible_face_peak_over_Fv", "scalar_shear_bound_over_Fv",
           "sufficient_rectangle_bound_over_Fv")
DURATIONS = {"original_CD1": 1.0, "conditional_peak_CD1_25": 1.25}
EXTRA_PINS = {
    PROJECTION_CONTRACT: "4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3",
    PROJECTION_INPUTS: "3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208",
    COVERAGE / "coverage.json": "a9dc39d5dbd153c7928923caf79dcf678e653c0b707a35514e1177c8bd4337b2",
    COVERAGE / "receipt.json": "5d9dba87ff93e0a218d5c74d7dc4830708bf2ac4b263bf229dde69b245737f02",
    HERE / "knee-bridge-remaining-sections.py": "e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15",
    HERE / "corner-timber-sections.py": "d0e2c5cb94b056cab71072fcab52cc7be8760fb7d32368c097a45050b3493633",
    HERE / "corner-net-section.py": "8a60447291161300ec4ee4f4f89c783cdcb565ee771e972c524ffd10f006d0e5",
    HERE / "header-net-section.py": "d413a2ae912df6bf56086ad6ddda59526db32cc6325f1b4bf2b71f984d86a328",
    HERE / "remaining-net-sections.py": "acd60cee627331fdfeb06eb02321221f09a666bcea7e3997a9e51e616c98c129",
    HERE / "top-host-net-sections.py": "bfa6a1716908efdb83b3ebf07b0def1bd9114d448dbdf294057b832749d8b3e8",
    HERE / "knee-bridge-top-rail.py": "d8f4a84ab8c6fefcdce4ba65a6812de6a7e6199ea69f67c3fb4fde1252681fec",
}
FLAGS = {"native_CAD_or_frame_execution": False, "tests_run": False, "review_run": False,
         "historical_demands_transferred": False, "refresh_result_consumed": False,
         "geometry_material_duration_or_loads_changed": False,
         "gross_rectangle_fallback_used": False, "new_resistance_established": False,
         "local_pressure_interpretation_claimed": False, "physical_release": False,
         "complete_joint_acceptance": False, "formal_criterion_acceptance": False,
         "splitting_or_tangential_fracture_assessed": False}


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def module(path, expected):
    require(sha(path) == expected, "changed helper: " + str(path))
    spec = importlib.util.spec_from_file_location("opening_remainder_" + Path(path).stem.replace("-", "_"), path)
    require(spec is not None and spec.loader is not None, "helper import unavailable")
    result = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(result)
    finally:
        sys.dont_write_bytecode = old
    return result


def sources():
    """Finite stdlib source/identity join, with no geometry or strength execution."""
    pins_api = module(PIN_HELPER, PIN_HELPER_SHA)
    selected = (pins_api.REPORT, pins_api.ARRAYS, pins_api.GEOMETRY, pins_api.INPUTS,
                pins_api.ASSESSMENT, pins_api.COMPARISON, pins_api.RESPONSE,
                pins_api.MATERIALS, pins_api.METHOD, BASE / "member_screen.py")
    pins = {p: pins_api.PINS[p] for p in selected}
    pins.update(EXTRA_PINS)
    pins.update(pins_api.CLASSIFIER_PINS)
    pins[PIN_HELPER] = PIN_HELPER_SHA
    pins[Path(__file__).resolve()] = sha(__file__)
    pins_api.authenticate(pins)
    fresh, inputs, gravity, coverage, receipt, geometry, frame_map = [pins_api.read(p) for p in (
        pins_api.REPORT, pins_api.INPUTS, pins_api.ASSESSMENT, COVERAGE / "coverage.json",
        COVERAGE / "receipt.json", pins_api.GEOMETRY, pins_api.FRAME_MAP)]
    require(receipt["output_sha256"]["coverage.json"] == pins[COVERAGE / "coverage.json"], "coverage receipt differs")
    require(fresh["source_sha256"] == inputs["source_sha256"], "action source closure differs")
    for name, digest in fresh["source_sha256"].items():
        pins_api.bind(pins, ROOT / name, digest)
    for name, digest in gravity["output_sha256"].items():
        pins_api.bind(pins, pins_api.GRAVITY / name, digest)
    for name in ("geometry.json", "inputs.json", "action-section-arrays.npz"):
        require(fresh["output_sha256"][name] == pins[pins_api.MEMBERS / name], "saved extraction differs")
    require(SURFACES in pins, "saved surface register missing from frozen closure")
    pins_api.authenticate(pins)
    members = geometry["members"]
    surface_records = {r["member_id"]: r for r in pins_api.read(SURFACES)["records"]}
    frame_ids = {r["member_id"] for r in frame_map["members"]}
    body_ids = frame_ids - SIDES
    require(len(frame_ids) == 20 and len(body_ids) == 18 and len(members) == 44, "20/18/44 body census differs")
    require(tuple(coverage["case_ids"]) == tuple(c["case_id"] for c in fresh["cases"]) == pins_api.CASES,
            "six source cases differ")
    finished = [s for s in coverage["uncalculated_fresh_opening_stations"]
                if s["opening_identity_kind"] == "finished_geometry_interval"]
    targets = [s for s in finished if s["body"] in body_ids]
    require(len(finished) == 1162 and len(targets) == 860
            and len({(s["body"], s["station_index"]) for s in targets}) == 860, "1162/860 target station census differs")
    require(13944 - 1320 == 12624 and 12624 - 12 * len(targets) == 2304, "refresh/remainder partition differs")
    for body in sorted(body_ids):
        record, surface = members[body], surface_records[body]
        require(not record["replaced_original_bore_features"]
                and surface["step_binding"]["path"] == record["current_finished_step"]
                and surface["step_binding"]["file_sha256"] == record["current_finished_step_sha256"],
                "unchanged finished frame identity differs: " + body)
        pins_api.bind(pins, ROOT / record["current_finished_step"], record["current_finished_step_sha256"])
        feature_ids = {f["feature_id"] for f in surface["features"]}
        for target in (s for s in targets if s["body"] == body):
            si = target["station_index"]
            require(target["station_mm"] == record["stations_mm"][si]
                    and target["saved_trace_indices"] == [2 * si, 2 * si + 1]
                    and target["case_ids"] == list(pins_api.CASES)
                    and target["limits"] == ["before", "after"], "station/case/limit identity differs")
            actual_ids = [fid for fid in target["feature_ids"] if not fid.endswith("/owner_authorized_station_exclusion")]
            require(actual_ids and all(fid in feature_ids for fid in actual_ids), "actual opening feature identity missing")
    pins_api.authenticate(pins)
    direction_map = floor_direction_metadata(pins_api, pins)
    plan = {"schema": "member_opening_remainder_preparation/v1", "status": "PREPARED_NOT_EXECUTED",
            "source_count": len(pins), "source_sha256": pins_api.source_map(pins),
            "producer_sha256": pins[Path(__file__).resolve()],
            "runtime": {"python": platform.python_version(), "numpy_installed": importlib.metadata.version("numpy")},
            "case_ids": list(pins_api.CASES), "body_ids": sorted(body_ids), "target_stations": targets,
            "target_station_count": 860, "target_signed_limit_count": 10320,
            "target_duration_record_count": 20640, "duration_scenarios": DURATIONS,
            "body_target_counts": dict(Counter(s["body"] for s in targets)),
            "finished_gap_signed_limits": 13944, "separate_first_refresh_signed_limits": 1320,
            "side_host_signed_limits_outside_assignment_after_first_refresh": 2304,
            "unmachined_exclusion_signed_limits_outside_assignment": 264,
            "original_terminal_inapplicable_signed_limits": 1176,
            "floor_direction_adapter": direction_map,
            "arithmetic_executed": False, **FLAGS}
    return pins_api, pins, plan, members, surface_records


def floor_direction_metadata(api, pins):
    """Recover recorded constraint orientation; do not infer it from observed D."""
    inputs = api.read(PROJECTION_INPUTS)
    require(inputs["source_sha256"][str(PROJECTION_CONTRACT.relative_to(ROOT))]
            == pins[PROJECTION_CONTRACT], "original compliance/projection contract binding differs")
    contract = api.read(PROJECTION_CONTRACT)
    floor = [r for r in contract["rows"] if r["family"] == "conditional_floor_tangent_constraint"]
    require(len(floor) == 200, "source floor orientation inventory differs")

    def identity(row):
        return row["row_id"], row["source_group"], row["source_element"]

    original = {identity(r): r for r in floor}
    require(len(original) == 200, "duplicate source floor orientation identity")
    raw_rows = api.read(api.GRAVITY / "row-identities.json")
    current = [r for r in raw_rows if r["family"] == "conditional_floor_tangent_constraint"]
    require(len(raw_rows) == 1888 and len(current) == 200
            and {identity(r) for r in current} == set(original), "current/source floor row join differs")
    mappings = []
    for raw in current:
        saved = original[identity(raw)]
        own = raw["ownership"]
        require(raw["law"] == saved["law"] and own == saved["ownership"]
                and own["role"] == "assumed_no_slip_floor" and own["second_body"] == "floor"
                and raw["law"]["intended_law"] == "floor_tangent_all_bearing_hypothesis"
                and saved["owner_point_rigid_row_sign"] == -1
                and saved["owner_point_rigid_row_max_abs_residual"] < 1e-8,
                "floor source orientation/schema differs: " + raw["row_id"])
        sign = saved["owner_point_rigid_row_sign"]
        mappings.append({"row": raw["row"], "row_id": raw["row_id"],
                         "source_group": raw["source_group"], "source_element": raw["source_element"],
                         "first_body": own["first_body"], "second_body": own["second_body"],
                         "role": own["role"], "point_mm": own["point_mm"],
                         "source_constraint_axis_global_xyz": own["direction_global_xyz"],
                         "source_owner_point_rigid_row_sign": sign,
                         "helper_force_axis_on_first_per_unit_scalar_xyz": [sign * x for x in own["direction_global_xyz"]]})
    return {"schema": "floor_constraint_direction_adapter/v1", "row_count": 200,
            "projection_contract_sha256": pins[PROJECTION_CONTRACT], "mappings": mappings,
            "scope": "Private expected physical-force direction for the unchanged -D.T scalar reaction; original source axis, point, law, role, D and scalar forces remain unchanged."}


def private_action_rows(rows, model, D, direction_map, np):
    """Translate metadata semantics after independently checking full D rows."""
    require(D.shape == (1888, 6 * len(model["body_names"])), "current D/body ordering shape differs")
    private = copy.deepcopy(rows)
    for mapping in direction_map["mappings"]:
        i, body = mapping["row"], mapping["first_body"]
        raw = rows[i]
        require(raw["row"] == i and raw["row_id"] == mapping["row_id"]
                and raw["source_group"] == mapping["source_group"]
                and raw["source_element"] == mapping["source_element"]
                and raw["ownership"]["direction_global_xyz"] == mapping["source_constraint_axis_global_xyz"],
                "private floor row identity differs")
        nodes = model["body_nodes"][body]
        center = np.mean([model["physical_node_coordinates_mm"][str(n)] for n in nodes], axis=0)
        point = np.array(mapping["point_mm"])
        axis = np.array(mapping["source_constraint_axis_global_xyz"])
        sign = mapping["source_owner_point_rigid_row_sign"]
        # owner_rigid_row is (-axis on first, +axis on second).
        # The source contract supplies its arbitrary constraint-row sign.
        expected = sign * np.r_[-axis, -np.cross(point - center, axis) / 1000]
        first = 6 * model["body_names"].index(body)
        require(np.isfinite(D[i]).all() and np.max(abs(D[i, first:first + 6] - expected)) < 1e-8,
                "source floor orientation/full D force-moment binding differs: " + raw["row_id"])
        require(np.max(abs(np.r_[D[i, :first], D[i, first + 6:]])) < 1e-12,
                "floor D row contains another body's action")
        private[i]["ownership"]["direction_global_xyz"] = mapping["helper_force_axis_on_first_per_unit_scalar_xyz"].copy()
        private[i]["source_constraint_direction_binding"] = copy.deepcopy(mapping)
    require(rows != private and len(private) == len(rows), "private floor context was not constructed")
    return private


def unsupported(reason, detail, target):
    return {"status": "INAPPLICABLE_EXISTING_RECTANGULAR_LIGAMENT_RESISTANCE_MODEL",
            "reason": reason, "detail": detail, "opening_identity": target, "regions": None}


def recipe(target, record, surface, outer_at, timber, np):
    """Join finite planes and whole cylindrical walls, then reuse exact slot cuts."""
    station = target["station_mm"]
    geometry = record["geometry"]
    frame = np.array([geometry[k] for k in ("axis", "section_u", "section_v")])
    features = {f["feature_id"]: f for f in surface["features"]}
    # A one-circle planar cap is an interior boundary of a blind recess,
    # never an outward plane bounding the complete timber cross section.
    caps = {fid for fid, f in features.items() if f["surface_kind"] == "PLANE"
            and len(f["trim"]["wires"]) == 1 and f["trim"]["wires"][0]["edge_count"] == 1
            and f["trim"]["wires"][0]["edges"][0]["curve_kind"] == "CIRCLE"}
    planes = [p for p in record["profile_planes"] if p["id"] not in caps]
    outer = outer_at(station, geometry, planes, [])
    if not outer["status"].startswith("BORE_FREE_"):
        return unsupported("OUTER_PROFILE_OR_TERMINAL_POINT_LOAD_MODEL_INAPPLICABLE", outer, target)
    low, high = np.array(outer["bounds_uv_mm"])
    center = (low + high) / 2
    active = [b for b in record["bore_or_passage_intervals"] if b["lo"] - 1e-6 <= station <= b["hi"] + 1e-6]
    require({b["id"] for b in active} == set(target["feature_ids"]), "active feature/station join differs")
    if any(b["id"].endswith("/owner_authorized_station_exclusion") for b in active):
        return unsupported("OVERLAPPING_UNMACHINED_STATION_EXCLUSION", active, target)
    bores, certificates = [], []
    for interval in active:
        feature = features[interval["id"]]
        if feature["surface_kind"] != "CYLINDER":
            return unsupported("OPENING_SURFACE_HAS_NO_EXACT_CYLINDER_SLOT_RECIPE", interval, target)
        cylinder = feature["cylinder"]
        point = frame @ (np.array(cylinder["axis_origin_global_xyz_mm"]) - geometry["start"])
        direction = frame @ np.array(cylinder["axis_unit_global_xyz"])
        shaft = int(np.argmax(abs(direction)))
        angular = feature["trim"]["surface_parameter_bounds"]["u"]
        axial = cylinder["axis_parameter_interval_mm"]
        radius = cylinder["radius_mm"]
        require(radius > 0 and abs(radius - interval["radius_mm"]) < 1e-5, "saved radius binding differs")
        if (cylinder["material_side_geometry"] != "bore_like" or shaft not in (1, 2)
                or abs(abs(direction[shaft]) - 1) >= 1e-7 or max(abs(np.delete(direction, shaft))) >= 1e-7):
            return unsupported("NONTRANSVERSE_OR_OBLIQUE_OPENING_REQUIRES_ANOTHER_SECTION_MODEL", interval, target)
        if (abs(angular[1] - angular[0] - 2 * math.pi) >= 1e-5
                or abs(feature["area_mm2"] - 2 * math.pi * radius * (axial[1] - axial[0])) >= 0.001):
            return unsupported("TRIMMED_WALL_HAS_NO_WHOLE_CYLINDER_CERTIFICATE", interval, target)
        ends = np.sort(point[shaft] + direction[shaft] * np.array(axial))
        bounds = np.array([low[shaft - 1], high[shaft - 1]])
        if np.max(abs(ends - bounds)) >= 1e-5:
            return unsupported("BLIND_OR_PARTIAL_SHAFT_NOT_A_COMPLETE_TRANSVERSE_SLOT",
                               {"feature_id": interval["id"], "saved_shaft_ends_mm": ends.tolist(),
                                "finished_profile_shaft_bounds_mm": bounds.tolist()}, target)
        other = 3 - shaft
        distance = abs(station - point[0])
        if distance < radius:
            chord = math.sqrt(radius**2 - distance**2)
            if point[other] - chord < low[other - 1] - 1e-5 or point[other] + chord > high[other - 1] + 1e-5:
                return unsupported("SLOT_LEAVES_AUTHENTICATED_OUTER_PROFILE", interval, target)
        require(abs(interval["lo"] - (point[0] - radius)) < 1e-5
                and abs(interval["hi"] - (point[0] + radius)) < 1e-5, "saved grain interval differs from actual cylinder")
        bores.append({"axis_id": interval["id"], "station_mm": float(point[0]),
                      "radius_mm": radius, "removed_interval_axis": other,
                      "transverse_center_mm": float(point[other] - center[other - 1])})
        certificates.append({"feature_id": interval["id"], "source_feature": feature["feature_id"],
                             "radius_mm": radius, "grain_center_mm": float(point[0]), "shaft_axis": shaft,
                             "whole_cylindrical_wall": True, "shaft_ends_mm": ends.tolist(),
                             "finished_profile_shaft_bounds_mm": bounds.tolist(),
                             "zero_chord_at_station": bool(distance >= radius)})
    section = timber.section({"width_depth_mm": (high - low).tolist(), "bores": bores}, station)
    require(set(section["bore_or_tangency_ids"]) == {b["id"] for b in active}, "exact bore/tangency coverage differs")
    if section["net_area_mm2"] <= 0 or not section["regions"]:
        return unsupported("NO_POSITIVE_RETAINED_RECTANGULAR_LIGAMENT", section, target)
    for region in section["regions"]:
        region["bounds_uv_mm"] = (np.array(region["bounds_uv_mm"]) + center[:, None]).tolist()
        region["centroid_uv_mm"] = (np.array(region["centroid_uv_mm"]) + center).tolist()
    return {"status": "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE", "opening_identity": target,
            "outer_profile": outer, "excluded_interior_cap_plane_ids": sorted(caps),
            "bore_certificates": certificates, "section": section,
            "scope": "Exact rectangle minus union of whole transverse bore chords at this finite station; no gross fallback or artificial subdivision of connected material."}


def outcomes(summary):
    result = {}
    for metric in METRICS:
        raw = summary.get(metric)
        finite = raw is not None and not isinstance(raw, bool) and math.isfinite(float(raw))
        value = float(raw) if finite else None
        status = "UNCALCULATED"
        if finite:
            status = "SUPPORTED_REFERENCE_COMPARISON_AT_OR_BELOW_ONE" if value <= 1 else (
                "EVALUATED_FACE_EXCEEDS_REFERENCE" if metric == "compatible_face_peak_over_Fv"
                else "SUFFICIENT_SHEAR_BOUND_ABOVE_ONE" if metric in (
                    "same_state_shear_bound_over_Fv", "transverse_shear_over_Fv",
                    "scalar_shear_bound_over_Fv", "sufficient_rectangle_bound_over_Fv")
                else "NOMINAL_REFERENCE_COMPARISON_ABOVE_ONE")
        result[metric] = {"value": value, "outcome": status}
    return result


def summarize(rows):
    """Keep counts as Python ints, including comparisons of NumPy scalars."""
    metrics = {}
    for name in METRICS:
        finite = [row for row in rows if row["comparison_outcomes"][name]["value"] is not None]
        metrics[name] = {"expected": len(rows), "finite": len(finite), "uncalculated": len(rows) - len(finite),
                         "above_one": sum(int(r["comparison_outcomes"][name]["value"] > 1) for r in finite),
                         "at_or_below_one": sum(int(r["comparison_outcomes"][name]["value"] <= 1) for r in finite),
                         "maximum_witness": max(finite, key=lambda r: r["comparison_outcomes"][name]["value"]) if finite else None}
    return {"record_count": len(rows), "complete_finite": bool(rows) and all(m["uncalculated"] == 0 for m in metrics.values()),
            "all_comparisons_at_or_below_one": bool(rows) and all(
                m["uncalculated"] == 0 and m["above_one"] == 0 for m in metrics.values()), "metrics": metrics}


def start(output, api, pins):
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "new owned immediate output child required")
    api.authenticate(pins)
    output.mkdir(parents=True)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    return output


def finish(output, api, pins, status, arithmetic):
    api.authenticate(pins)
    outputs = {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}
    api.write(output / "receipt.json", {"schema": "member_opening_remainder_receipt/v1", "status": status,
              "source_count": len(pins), "source_sha256": api.source_map(pins), "output_sha256": outputs,
              "source_unchanged_before_and_after_write": True, "arithmetic_executed": arithmetic, **FLAGS})
    api.authenticate(pins)
    require(all(sha(output / name) == digest for name, digest in outputs.items()), "output changed after write")


def prepare(output):
    api, pins, plan, *_ = sources()
    output = start(output, api, pins)
    api.write(output / "preparation.json", plan)
    finish(output, api, pins, plan["status"], False)
    return plan


def build(output):
    """Parent serializes finite geometry joins and real nominal cut arithmetic."""
    api, pins, plan, members, surfaces = sources()
    import numpy as np

    replay, timber, net, header, remaining, previous, rail = [module(HERE / name, pins[HERE / name]) for name in (
        "knee-bridge-remaining-sections.py", "corner-timber-sections.py", "corner-net-section.py",
        "header-net-section.py", "remaining-net-sections.py", "top-host-net-sections.py", "knee-bridge-top-rail.py")]
    fresh, model, rows, _ = replay.source_context(pins)
    require(api.source_map(pins) == plan["source_sha256"], "numerical context expanded prepared closure")
    require(rail.DURATIONS == DURATIONS, "existing duration hypotheses differ")
    net.rectangle_torsion = cache(net.rectangle_torsion)
    outer_at = previous.outer_rectangle_function()
    recipes = {(s["body"], s["station_index"]): recipe(s, members[s["body"]], surfaces[s["body"]], outer_at, timber, np)
               for s in plan["target_stations"]}
    api.authenticate(pins)
    output = start(output, api, pins)
    api.write(output / "preparation.json", plan)
    api.write(output / "section-recipes.json", {"recipes": list(recipes.values())})
    material = api.read(api.MATERIALS)
    summaries, audits, count = [], [], 0
    with (np.load(api.ARRAYS, allow_pickle=False) as arrays,
          np.load(api.RESPONSE, allow_pickle=False) as response,
          np.load(api.GRAVITY / "operators.npz", allow_pickle=False) as operators,
          gzip.open(output / "cuts.jsonl.gz", "wt") as stream):
        action_rows = private_action_rows(rows, model, operators["D"], plan["floor_direction_adapter"], np)
        api.write(output / "ownership-direction-map.json", plan["floor_direction_adapter"])
        for body in plan["body_ids"]:
            record = members[body]
            g = record["geometry"]
            frame = np.array([g[k] for k in ("axis", "section_u", "section_v")])
            selected = [s for s in plan["target_stations"] if s["body"] == body]
            for case in fresh["cases"]:
                source, _, negative, audit = replay.actions_for(case, body, record, arrays, response,
                    operators["D"], operators["W"], model, action_rows, header)
                audit["floor_direction_adapter_used"] = True
                binding, _ = replay.material_for(source, material, net)
                audit["conditional_material"] = binding
                audits.append(audit)
                prefix = source["array_prefix"]
                for target in selected:
                    si, station = target["station_index"], target["station_mm"]
                    layout = recipes[body, si]
                    for before in (True, False):
                        index = 2 * si + int(not before)
                        cut, datum = previous.global_cut(arrays[prefix + "__point_force_free_couple_xyz"],
                            arrays[body + "__point_xyz_mm"], arrays[body + "__point_stations_mm"], g, station, before)
                        local = np.r_[frame @ cut[:3], frame @ cut[3:]]
                        replay.difference(local, negative[index], "complete saved signed cut replay")
                        record_out = {"body": body, "case": case["case_id"], "station_mm": station,
                                      "saved_station_index": si, "saved_trace_index": index,
                                      "limit": "before" if before else "after", "recipe_status": layout["status"],
                                      "opening_feature_ids": target["feature_ids"],
                                      "cut_global_xyz_n_nmm": cut.tolist(), "cut_grain_u_v_n_nmm": local.tolist(),
                                      "cut_datum_global_xyz_mm": datum.tolist()}
                        if layout["status"] == "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE":
                            section = {**layout["section"], "saved_station_index": si}
                            results = rail.duration_results(local, section, datum, frame, case["case_id"], before, net, previous, binding)
                            require(set(results) == set(DURATIONS), "duration record census differs")
                            for result in results.values():
                                nominal = result["nominal_section"]
                                replay.difference(nominal["reconstructed_signed_cut_n_nmm"], local, "regional signed-wrench recovery")
                                summary = remaining.cut_summary(case["case_id"], body, index, section, nominal)
                                summary.update(result["summary"])
                                summary["comparison_outcomes"] = outcomes(summary)
                                result["summary"] = summary
                                summaries.append(summary)
                            record_out["duration_results"] = results
                        else:
                            record_out.update(reason=layout["reason"], duration_results={name: {
                                "CD": duration, "outcome": "INAPPLICABLE_EXISTING_RECTANGULAR_LIGAMENT_RESISTANCE_MODEL",
                                "comparison_outcomes": outcomes({})} for name, duration in DURATIONS.items()})
                        stream.write(json.dumps(record_out, separators=(",", ":"), allow_nan=False) + "\n")
                        count += 1
    require(count == 10320 and len(audits) == 108, "18-body six-case cut/action census differs")
    supported = sum(int(r["status"] == "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE") for r in recipes.values())
    require(len(summaries) == supported * 24 and supported > 0, "supported strength arithmetic incomplete")
    comparisons = summarize(summaries)
    coverage_matrix = []
    for body in plan["body_ids"]:
        own_recipes = [r for (b, _), r in recipes.items() if b == body]
        own_supported = sum(int(r["status"] == "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE") for r in own_recipes)
        for duration in DURATIONS:
            own = [s for s in summaries if s["block"] == body and s["duration_scenario"] == duration]
            require(len(own) == own_supported * 12, "body/duration finite record census differs")
            coverage_matrix.append({"body": body, "duration_scenario": duration,
                                    "target_signed_limits": len(own_recipes) * 12,
                                    "supported_signed_limits": own_supported * 12,
                                    "method_inapplicable_signed_limits": (len(own_recipes) - own_supported) * 12,
                                    **summarize(own)})
    inapplicable = [r for r in recipes.values() if r["status"] != "SUPPORTED_EXACT_TRANSVERSE_SLOT_RECIPE"]
    finite = comparisons["complete_finite"]
    result = {"schema": "member_opening_remainder/v1", "status": (
                "COMPLETE_SUPPORTED_ARITHMETIC_WITH_EXPLICIT_INAPPLICABLE_TARGETS" if finite
                else "INCOMPLETE_UNCALCULATED_SUPPORTED_COMPARISONS"),
              "runtime": {"python": platform.python_version(), "numpy": np.__version__},
              "source_count": len(pins), "source_sha256": api.source_map(pins),
              "floor_direction_adapter": {k: v for k, v in plan["floor_direction_adapter"].items() if k != "mappings"},
              "target_station_count": 860, "target_signed_limit_count": count,
              "supported_station_count": supported, "supported_signed_limit_count": supported * 12,
              "method_inapplicable_station_count": len(inapplicable),
              "method_inapplicable_signed_limit_count": len(inapplicable) * 12,
              "method_inapplicable_reasons": dict(Counter(r["reason"] for r in inapplicable)),
              "inapplicable_opening_identities": [r["opening_identity"] for r in inapplicable],
              "comparisons": comparisons, "coverage_matrix": coverage_matrix,
              "finite_supported_arithmetic_complete": finite,
              "all_assigned_opening_strength_comparisons_finite": finite and not inapplicable,
              "finished_gap_after_separate_first_refresh_and_this_finite_arithmetic": (
                  12624 - supported * 12 if finite else None),
              "side_host_signed_limits_still_outside_assignment": 2304,
              "unmachined_exclusion_signed_limits_outside_assignment": 264,
              "original_terminal_inapplicable_signed_limits": 1176,
              "arithmetic_executed": True, **FLAGS}
    api.authenticate(pins)
    api.write(output / "action-audits.json", {"audits": audits})
    api.write(output / "checks.json", result)
    finish(output, api, pins, result["status"], True)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true", help="stdlib authentication/identity join only")
    args = parser.parse_args()
    packet = prepare(args.output) if args.prepare else build(args.output)
    print(json.dumps({"status": packet["status"], "source_count": packet["source_count"]}))
