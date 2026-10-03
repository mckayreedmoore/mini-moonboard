#!/usr/bin/env python3
"""Source-bound nominal finished-boundary samples; no CAD or solver imports."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MANIFEST_SHA = "2d7050f533e315fb28a635b93546e1e5d2036011eddfb77e966dcd73c947f9c9"
LOAD_SHA = "f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1"
RAW_SHA = "c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9"
RESISTANCE_SHA = "c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1"
SURFACES_PATH = "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/surfaces.json"
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (.1, .2, .3, .45, .675, .925, 1.)
AXES = tuple(f"{kind}_bolt_{side}_{index}" for kind in
             ("lumber_leg", "rail_front", "rail_rear")
             for side in ("left", "right") for index in (1, 2))
FLAGS = ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
         "floor_capacity_established", "friction_qualified", "joint_accepted",
         "fabrication_release", "native_solve_executed")
SAMPLE_INSET_MM = .01


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path)
    return {"sha256": sha(path), "size_bytes": path.stat().st_size}


def refuse_output_alias(output, protected):
    """Protect source bytes even when another pathname shares their inode."""
    paths = {Path(path).resolve() for path in protected}
    require(output.resolve() not in paths, "output aliases an input")
    if output.exists():
        for path in paths:
            if path.exists():
                require(not output.samefile(path), "output aliases an input")


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def difference(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def vector(value, unit=False):
    require(len(value) == 3 and all(math.isfinite(x) for x in value), "invalid vector")
    if unit:
        require(abs(math.hypot(*value) - 1.) < 1e-9, "nonunit vector")
    return value


def checked_inputs(load_path, raw_path, resistance_path):
    require(sha(HERE / "source-pins.json") == MANIFEST_SHA, "changed source manifest")
    manifest = json.loads((HERE / "source-pins.json").read_text())
    for relative, expected in manifest["pins"].items():
        require(pin(ROOT / relative) == expected, f"changed source: {relative}")
    for path, expected in ((load_path, LOAD_SHA), (raw_path, RAW_SHA),
                           (resistance_path, RESISTANCE_SHA)):
        require(sha(path) == expected, f"changed frozen artifact: {path}")
    load = json.loads(Path(load_path).read_text())
    raw = json.loads(Path(raw_path).read_text())
    resistance = json.loads(Path(resistance_path).read_text())
    require(raw["report_sha256"] == LOAD_SHA and resistance["load_report_sha256"] == LOAD_SHA,
            "upstream report binding changed")
    require(all(load[k] is False and resistance[k] is False and raw[k] is False for k in FLAGS),
            "upstream acceptance changed")
    require(load["candidate"] == "compact-floor-flush-wood-joints-development"
            and load["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "candidate changed")
    require(set(load["axis_register"]) == set(AXES) and len(load["input_pins"]) == 143,
            "retained census changed")
    for relative, expected in load["input_pins"].items():
        require(pin(ROOT / relative) == expected, f"changed load source: {relative}")
    for relative, expected in resistance["source_pins"].items():
        require(pin(ROOT / relative) == expected, f"changed resistance source: {relative}")
    criteria = json.loads((ROOT / "docs/wood-joints-mvp/criteria.json").read_text())
    rows = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    require(len(rows) == 47 and all(row["status"] == "pending" for row in rows)
            and criteria["engineering_mvp_complete"] is False
            and all(value is False for value in criteria["release_flags"].values()),
            "criteria disposition changed")
    surfaces = json.loads((ROOT / SURFACES_PATH).read_text())
    require(surfaces["candidate"] == load["candidate"]
            and surfaces["geometry_revision_id"] == load["geometry_revision_id"]
            and not surfaces["unsupported_faces"]
            and not surfaces["ambiguous_cylinder_material_side_feature_ids"],
            "surface authority changed")
    axis_features = json.loads((ROOT / SURFACES_PATH).with_name("axis-features.json").read_text())
    bound_axes = {row["axis_id"]: row for row in
                  axis_features["source_axis_groups"]["retained_frame_bolt_axes"]["axes"]}
    require(set(bound_axes) == set(AXES), "axis feature census changed")
    for axis_id, axis in load["axis_register"].items():
        bound = bound_axes[axis_id]
        require(bound["source_axis_fields"] == axis["source_axis_fields"], "source axis binding changed")
        bound_receivers = {row["receiver_member_id"]: row for row in bound["receiver_memberships"]}
        require(set(bound_receivers) == {axis["first"], axis["second"]}, "feature receivers changed")
        for receiver in axis["receivers_head_to_nut"]:
            association = bound_receivers[receiver["member"]]
            require(association["match_status"] == "matched_bore_patch"
                    and association["matched_feature_ids"] == [receiver["feature_id"]]
                    and association["current_finished_step_binding"] == receiver["finished_step"]
                    and association["stock_frame"] == receiver["stock_frame"],
                    "matched own bore authority changed")
            candidates = [row for row in association["cylinder_surface_candidates"]
                          if row["feature_id"] == receiver["feature_id"]]
            require(len(candidates) == 1 and candidates[0]["patch_interval_projected_from_axis_datum_mm"]
                    == receiver["interval_from_axis_datum_mm"], "bearing interval binding changed")
    # Authenticate the pure method before loading it; never import CAD producers.
    spec = importlib.util.spec_from_file_location("retained_finished_ray_method", HERE / "method.py")
    method = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = method
    spec.loader.exec_module(method)
    return load, surfaces, manifest, method


def frame_checked(frame):
    basis = frame["basis_columns_global_xyz"]
    require(len(basis) == 3, "invalid frame")
    for axis in basis:
        vector(axis, unit=True)
    require(all(abs(dot(basis[i], basis[j])) < 1e-9 for i in range(3) for j in range(i)),
            "nonorthogonal frame")
    vector(frame["origin_global_xyz_mm"])
    require(len(frame["original_dimensions_gqr_mm"]) == 3
            and all(math.isfinite(x) and x > 0 for x in frame["original_dimensions_gqr_mm"]),
            "invalid stock dimensions")
    return basis


def make_geometry(load, surfaces, method):
    members = {row["member_id"]: row for row in surfaces["records"]}
    require(len(members) == 44, "duplicate or missing finished members")
    memberships, queries = {}, {}
    for axis_id in AXES:
        axis = load["axis_register"][axis_id]
        source = axis["source_axis_fields"]
        origin = vector(source["datum_global_xyz_mm"])
        axis_direction = vector(source["direction_global_xyz"], unit=True)
        require([row["member"] for row in axis["receivers_head_to_nut"]]
                == [axis["first"], axis["second"]], "receiver ordering changed")
        for side, receiver in zip(("first", "second"), axis["receivers_head_to_nut"], strict=True):
            member = members[receiver["member"]]
            require(member["step_binding"] == receiver["finished_step"]
                    and member["stock_frame"] == receiver["stock_frame"], "receiver binding changed")
            basis = frame_checked(receiver["stock_frame"])
            require(abs(dot(axis_direction, basis[0])) < 1e-9
                    and abs(dot(axis_direction, basis[1])) < 1e-9,
                    "axis is not transverse to modeled g/q")
            feature = [row for row in member["features"] if row["feature_id"] == receiver["feature_id"]]
            require(len(feature) == 1 and feature[0]["surface_kind"] == "CYLINDER"
                    and feature[0]["cylinder"]["material_side_geometry"] == "bore_like",
                    "own bore mapping changed")
            lo, hi = receiver["interval_from_axis_datum_mm"]
            require(0 <= lo < hi <= source["axis_length_mm"]
                    and hi - lo > 2 * SAMPLE_INSET_MM, "invalid bearing interval")
            membership_id = f"{axis_id}/{side}"
            stations = {"near_head": lo + SAMPLE_INSET_MM, "midpoint": (lo + hi) / 2,
                        "near_nut": hi - SAMPLE_INSET_MM}
            geometry_row = {"axis_id": axis_id, "receiver_side": side, **receiver,
                            "query_stations_from_axis_datum_mm": stations,
                            "physical_lateral_interface_point_xyz_mm": axis["lateral_interface_point_xyz_mm"],
                            "query_point_role": "interior bore-centerline sample, not the physical force application point",
                            "through_depth_minimum_mm": None, "queries_by_sample": {}}
            for label, station in stations.items():
                point = [a + station * b for a, b in zip(origin, axis_direction, strict=True)]
                local = [dot(difference(point, receiver["stock_frame"]["origin_global_xyz_mm"]), b)
                         for b in basis]
                require(all(-1e-5 <= value <= size + 1e-5 for value, size in
                            zip(local, receiver["stock_frame"]["original_dimensions_gqr_mm"], strict=True)),
                        "query outside stock locator")
                references = {}
                for dimension, label_axis in enumerate(("g", "q")):
                    for sign, suffix in ((1, "+"), (-1, "-")):
                        direction_name = label_axis + suffix
                        key = f"{membership_id}/{label}/{direction_name}"
                        direction = [sign * component for component in basis[dimension]]
                        query = method.query_member_direction(member, receiver["feature_id"], point, direction)
                        require(query["status"] in ("ok", "ambiguous", "unsupported"), "foreign method status")
                        stock_distance = (receiver["stock_frame"]["original_dimensions_gqr_mm"][dimension]
                                          - local[dimension]) if sign == 1 else local[dimension]
                        exterior = query["first_exterior_exit"]
                        grain_normal = None
                        if exterior is not None and exterior["surface_kind"] == "PLANE":
                            boundary = next(row for row in member["features"]
                                            if row["feature_id"] == exterior["feature_id"])
                            grain_normal = abs(dot(boundary["plane"]["normal_global_xyz"], basis[0])) > 1 - 1e-9
                        queries[key] = {"query_id": key, "axis_id": axis_id,
                                        "receiver_side": side, "sample": label,
                                        "station_from_axis_datum_mm": station,
                                        "depth_from_receiver_head_mm": station - lo,
                                        "modeled_bearing_length_mm": hi - lo,
                                        "direction_name": direction_name,
                                        "stock_box_distance_mm": stock_distance,
                                        "stock_box_role": "separate proposed envelope locator, never a finished-boundary fallback",
                                        "finished_geometry": query,
                                        "grain_normal_planar_boundary": grain_normal,
                                        "NDS_square_cut_end_applicability": None,
                                        "through_depth_minimum_mm": None}
                        references[direction_name] = key
                geometry_row["queries_by_sample"][label] = references
            memberships[membership_id] = geometry_row
    require(len(memberships) == 24 and len(queries) == 288, "geometry census changed")
    return memberships, queries


def signed_selection(force, radius, basis, label):
    component = dot(force, basis)
    uncertainty = dot(radius, [abs(x) for x in basis])
    lower, upper = component - uncertainty, component + uncertainty
    sign = 1 if lower > 0 else -1 if upper < 0 else None
    return {"signed_component_n": component, "rounding_radius_n": uncertainty,
            "interval_n": [lower, upper], "sign": sign,
            "selection_status": "resolved" if sign is not None else "sign_interval_contains_zero",
            "direction_name": label + ("+" if sign == 1 else "-") if sign is not None else None}


def make_states(load, memberships, queries):
    result, seen = [], set()
    for state in load["states"]:
        state_key = (state["case_id"], state["increment_index"])
        require(state_key not in seen and state_key[0] in CASES and state_key[1] in range(7),
                "foreign or duplicate state")
        seen.add(state_key)
        require(state["load_factor"] == FACTORS[state_key[1]]
                and set(state["bolt_states"]) == set(AXES), "state census changed")
        for axis_id in AXES:
            action = state["bolt_states"][axis_id]["lateral_interface_action"]
            first, second = vector(action["force_on_first_xyz_n"]), vector(action["force_on_second_xyz_n"])
            require(all(abs(a + b) < 1e-12 for a, b in zip(first, second, strict=True)),
                    "receiver force pair mismatch")
            radius = vector(action["force_rounding_radius_xyz_n"])
            require(all(x >= 0 for x in radius), "negative RF radius")
            for side, force in (("first", first), ("second", second)):
                membership_id = f"{axis_id}/{side}"
                receiver = memberships[membership_id]
                require(action[side] == receiver["member"]
                        and action["point"] == receiver["physical_lateral_interface_point_xyz_mm"],
                        "load point or receiver mismatch")
                basis = receiver["stock_frame"]["basis_columns_global_xyz"]
                candidates = {}
                for dimension, label in enumerate(("g", "q")):
                    selection = signed_selection(force, radius, basis[dimension], label)
                    selected = {}
                    for sample, refs in receiver["queries_by_sample"].items():
                        key = refs[selection["direction_name"]] if selection["direction_name"] else None
                        query = queries[key] if key else None
                        selected[sample] = {"query_id": key,
                                            "finished_exterior_distance_mm": query["finished_geometry"]["distance_mm"] if query else None,
                                            "first_material_exit_distance_mm": query["finished_geometry"]["first_material_exit"]["distance_mm"]
                                            if query and query["finished_geometry"]["first_material_exit"] else None}
                    candidates[label] = {**selection, "samples": selected}
                result.append({"case_id": state_key[0], "increment_index": state_key[1],
                               "load_factor": state["load_factor"], "axis_id": axis_id,
                               "membership_id": membership_id, "receiver_side": side,
                               "receiver_member_id": receiver["member"],
                               "physical_lateral_interface_point_xyz_mm": action["point"],
                               "force_on_receiver_xyz_n": force, "force_rounding_radius_xyz_n": radius,
                               "source_row_ids": action["source_row_ids"],
                               "loaded_direction_geometric_candidates": candidates,
                               "direction_basis": "separate signed modeled grain and stock-q components; not total-resultant ray",
                               "NDS_loaded_end_edge_classification": None, "Cdelta": None,
                               "Cg": None, "splitting_acceptance": None,
                               "through_depth_minimum_mm": None, "joint_accepted": False})
    require(len(seen) == 21 and len(result) == 504, "incomplete signed receiver census")
    return result


def produce(load_path, raw_path, resistance_path):
    load, surfaces, manifest, method = checked_inputs(load_path, raw_path, resistance_path)
    memberships, queries = make_geometry(load, surfaces, method)
    states = make_states(load, memberships, queries)
    statuses = {status: sum(q["finished_geometry"]["status"] == status for q in queries.values())
                for status in ("ok", "ambiguous", "unsupported")}
    unresolved_signs = sum(item["sign"] is None for row in states
                           for item in row["loaded_direction_geometric_candidates"].values())
    return {"schema": "retained_frame_bolt_finished_edges/v1",
            "status": "nominal_source_bound_geometry_with_explicit_applicability_gaps",
            "candidate": load["candidate"], "geometry_revision_id": load["geometry_revision_id"],
            "producer_sha256": sha(Path(__file__)), "method_sha256": sha(HERE / "method.py"),
            "source_manifest_sha256": MANIFEST_SHA, "source_pins": manifest["pins"],
            "load_report_sha256": LOAD_SHA, "accepted_raw_receipt_sha256": RAW_SHA,
            "resistance_report_sha256": RESISTANCE_SHA,
            "rechecked_load_input_pins": load["input_pins"],
            "counts": {"retained_axes": 12, "receiver_memberships": 24, "finished_members": 8,
                       "query_depths_per_receiver": 3, "directional_queries": 288,
                       "signed_bolt_states": 252, "signed_receiver_states": 504,
                       "signed_component_selections": 1008, "unresolved_component_signs": unresolved_signs,
                       "query_statuses": statuses},
            "memberships": memberships, "queries": queries, "receiver_state_rows": states,
            "criteria_status": "all_47_pending_unchanged", "engineering_mvp_complete": False,
            "criteria_pending_count": 47,
            "release_flags": {key: False for key in ("drilling_released", "fabrication_released",
                                                       "structural_released", "climbing_released")},
            **{flag: False for flag in FLAGS},
            "geometry_regenerated_or_changed": False, "CAD_executed": False,
            "limits": ["Nominal analytic saved-signature geometry, not kernel-tolerance or observed-hole validation.",
                       "Own bore filled only for centerline ray interpretation; every other cut remains.",
                       "First material-loss boundary and actual exterior boundary are distinct.",
                       "Three explicit query depths do not establish a through-depth minimum.",
                       "Signed component directions do not establish oblique-load NDS classification.",
                       "Stock envelopes are locators, never substituted for missing finished geometry.",
                       "No Cdelta, Cg, splitting, complete-joint resistance or release is adopted."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--load-report", type=Path, default=Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json"))
    parser.add_argument("--raw-receipt", type=Path, default=Path("/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json"))
    parser.add_argument("--resistance-report", type=Path, default=Path("/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = produce(args.load_report, args.raw_receipt, args.resistance_report)
    protected = [args.load_report, args.raw_receipt, args.resistance_report,
                 HERE / "source-pins.json", Path(__file__), *[ROOT / p for p in report["source_pins"]],
                 *[ROOT / p for p in report["rechecked_load_input_pins"]],
                 *[path for path in HERE.rglob("*") if path.is_file()]]
    refuse_output_alias(args.output, protected)
    args.output.write_text(json.dumps(report, sort_keys=True, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": sha(args.output), "counts": report["counts"]}))


if __name__ == "__main__":
    main()
