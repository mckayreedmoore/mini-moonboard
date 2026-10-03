"""Prepare fresh same-state references for the sixteen original corner bolts.

Only the parent's explicit build(output) call reads evidence or calculates.
Retained pure functions supply component arithmetic; no historical producer,
local solve, native solver, CAD or frame entry point is called.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
RAW = HERE / "rawlocal/knee-bridge-corner-references"
SOURCE = HERE / "rawlocal/knee-bridge-corner-replay/attempt01/checks.json"
RECEIPT = SOURCE.with_name("receipt.json")
GRAVITY = HERE / "rawlocal/knee-bridge-gravity/attempt01"
ASSESSMENT = GRAVITY / "operator-assessment.json"
INPUTS = GRAVITY / "model-inputs.json"
COMPARISON = HERE / "rawlocal/knee-bridge-frame/attempt02/response/comparison.json"
RESPONSE = COMPARISON.with_name("response.npz")
TOP = HERE / "bolted-replay-results/corner-attempt01/component-results.json"
BOTTOM = HERE / "bolted-replay-results/bottom-attempt01/component-results.json"
TOP_MATH = HERE.parent / "corner_checks.py"
BOTTOM_MATH = HERE.parent / "lateral_reference.py"
TOP_REPLAY = HERE / "corner-first-order-components.py"
BOTTOM_REPLAY = HERE / "bottom-corner-components.py"
YIELD_MATH = ROOT / "fea/dowel_yield.py"
MATERIAL = HERE.parent.parent / "hardware-material-specification-2026-09-30/material-inputs.json"
FASTENERS = MATERIAL.with_name("fastener-inputs.json")
CASES = ["a12-rear", "a12-forward", "a12-left", "k12-right", "k12-rear", "a1-rear"]
MASS_KG = 225.19791414318078
DEAD_FACTOR = 1.1110134616260479
FYB_PSI = 92000.0
PSI_MPA = 0.006894757293168361
N_PER_LBF = 4.4482216152605
PINS = {
    SOURCE: "e699b5c662992abab1f646236cdd4037feb425c5476458d8629899bcb9948976",
    RECEIPT: "50898edc4d0d977c7522c3c30866504235f847ee6d3777345114afb4d86cd52d",
    ASSESSMENT: "ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95",
    COMPARISON: "c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729",
    RESPONSE: "62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90",
    INPUTS: "b260af3d53a199e66962caf6c7074086e1d433526e43d263a3f1247ba4c61b99",
    TOP: "401b8876dc3a96b553c847f1029a5a9200ba3f45af5493f64edd61fdc6bc42b6",
    BOTTOM: "ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a",
    TOP_MATH: "177e13712575b735dfb2cd4d1314d006e3f8fc77d3cbc9b3e117609fbe561bb0",
    BOTTOM_MATH: "845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94",
    TOP_REPLAY: "64927dce0058a2be67e3c55f82fc5a5649f91a908f6aa3ba6bdbc8dcfb39ec92",
    BOTTOM_REPLAY: "5239f1b4897e17ade2c4c4e73b8f9a42e9433f76357fbe0f355308c84fcbd3a7",
    YIELD_MATH: "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    MATERIAL: "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    FASTENERS: "ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2",
}
FLAGS = {
    "proposal_adopted": False,
    "historical_case_loads_used_as_authority": False,
    "historical_acceptance_transferred": False,
    "formal_criterion_acceptance": False,
    "complete_joint_acceptance": False,
    "physical_release": False,
    "fabrication_release": False,
    "reviewed_geometry_changed": False,
}
INDEX_KEYS = (
    "lateral_over_adjusted_92ksi_reference",
    "parallel_over_finished_path_reference",
    "mean_washer_wood_pressure_over_Fc_perp",
    "direct_combined_steel_over_92ksi",
    "smooth_bolt_VM_over_92ksi",
    "bottom_same_state_steel_reserve_ratio",
)


def require(condition, message):
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, record):
    Path(path).write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")


def bind(pins, path, digest):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT), "source leaves repository: " + str(path))
    require(path not in pins or pins[path] == digest, "conflicting pin: " + str(path))
    pins[path] = digest


def authenticate(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, "consumed source changed: " + str(path))


def source_map(pins):
    return {path.relative_to(ROOT).as_posix(): digest for path, digest in sorted(pins.items())}


def pure_functions(path, names, namespace):
    """Load only named retained functions, excluding imports and producer code."""
    tree = ast.parse(Path(path).read_text(), filename=str(path))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    require(len(functions) == len(names) and {node.name for node in functions} == set(names),
            "missing or duplicate retained pure function: " + str(path))
    require(all(not node.decorator_list for node in functions), "decorated reference function")
    # Pinned repository functions only; producer bodies and imports are excluded.
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(path), "exec"), namespace)  # noqa: S102
    return SimpleNamespace(**{name: namespace[name] for name in names})


def norm(vector):
    require(len(vector) == 3 and all(math.isfinite(v) for v in vector), "invalid finite vector")
    return math.sqrt(sum(v * v for v in vector))


def unit(vector):
    length = norm(vector)
    require(length > 0, "zero grain or axis")
    return [v / length for v in vector]


def dot(first, second):
    return sum(a * b for a, b in zip(first, second, strict=True))


def close(first, second, tolerance=1e-7):
    return len(first) == len(second) and all(
        math.isfinite(a) and math.isfinite(b) and abs(a - b) <= tolerance
        for a, b in zip(first, second, strict=True)
    )


def identity(row):
    return {key: row[key] for key in ("level", "side", "case_id", "host", "cleat", "axis_id")}


def component_summary(states):
    """Return finite indices, coverage and worksheet row witnesses for the parent."""
    components = {}
    for key in INDEX_KEYS:
        eligible = [(index, row) for index, row in enumerate(states) if row[key] is not None]
        require(all(math.isfinite(row[key]) and row[key] >= 0 for _, row in eligible),
                "nonfinite or negative component index: " + key)
        peak = max(eligible, key=lambda item: item[1][key]) if eligible else None
        components[key] = {
            "finite_states": len(eligible), "null_states": len(states) - len(eligible),
            "maximum": peak[1][key] if peak else None,
            "peak_witness": {"worksheet_row": peak[0], **identity(peak[1])} if peak else None,
            "above_one": [{"worksheet_row": index, "value": row[key], **identity(row)}
                          for index, row in eligible if row[key] > 1.0],
            "null_reasons": [{"worksheet_row": index, "reason": row["reference_limits"][key],
                              **identity(row)} for index, row in enumerate(states) if row[key] is None],
        }
    return {"bolt_states": len(states), "components": components,
            "exhausted_bottom_steel_reserve_states": [identity(row) for row in states
                if row["steel_reserve_status"] == "EXHAUSTED_CONDITIONAL_STEEL_RESERVE"],
            "maxima_are_independent_witnesses": True, **FLAGS}


def fresh_source(pins):
    source, receipt = read(SOURCE), read(RECEIPT)
    require(source["schema"] == "knee_bridge_original_corner_first_order_replay/v1"
            and source["status"] == "COMPLETE_FRESH_FIRST_ORDER_LOCAL_FORCES"
            and source["failure"] is None, "fresh corner replay incomplete")
    counts = {"completed_block_states": 24, "completed_host_states": 48,
              "top_bolt_states": 48, "bottom_bolt_states": 48, "completed_bolt_states": 96}
    require(source["counts"] == receipt["counts"] == counts and source["case_ids"] == CASES,
            "fresh source census or cases differ")
    require(len(source["source_sha256"]) == 94
            and receipt["source_sha256"] == source["source_sha256"]
            and receipt["output_sha256"]["checks.json"] == PINS[SOURCE]
            and receipt["status"] == source["status"]
            and receipt["source_unchanged_before_and_after_write"] is True,
            "94-pin closure or receipt differs")
    require(all(source[key] is False and receipt[key] is False for key in FLAGS),
            "source claims acceptance, release or changed geometry")
    require(source["geometric_shortening_and_preload_stiffness"] is False
            and source["balancing_free_couples_added"] == 0
            and source["material_or_contact_laws_changed"] is False
            and source["local_redistribution_feeds_back_to_frame"] is False
            and source["native_CAD_or_frame_execution"] is False
            and source["tests_run"] is False and source["review_loop_run"] is False,
            "preserved mechanics changed")
    require(source["physical_tolerances"] == {
        "host_force_n": 0.001, "host_moment_nmm": 0.2,
        "whole_cleat_force_n": 0.002, "whole_cleat_moment_nmm": 0.4},
        "source physical tolerances differ")
    require(source["modeled_mass_kg"] == MASS_KG and source["dead_load_factor"] == DEAD_FACTOR,
            "fresh gravity metadata differs")
    expected_loads = {path.relative_to(ROOT).as_posix(): PINS[path]
                      for path in (ASSESSMENT, COMPARISON, RESPONSE)}
    require(source["fresh_load_sources"] == expected_loads, "fresh load authority differs")
    for relative, digest in source["source_sha256"].items():
        bind(pins, ROOT / relative, digest)
    for relative, digest in receipt["output_sha256"].items():
        path = (SOURCE.parent / relative).resolve()
        require(path.parent == SOURCE.parent, "receipt output leaves replay directory")
        bind(pins, path, digest)
    require(all(source["source_sha256"][relative] == digest for relative, digest in expected_loads.items())
            and source["source_sha256"][INPUTS.relative_to(ROOT).as_posix()] == PINS[INPUTS],
            "fresh load/input pins absent from replay closure")
    authenticate(pins)
    return source


def build(output):
    """Parent-only arithmetic on the saved 96 states; write a fresh owned packet."""
    output = Path(output).resolve()
    require(output.parent == RAW.resolve() and not output.exists(), "use a fresh immediate owned output child")
    pins = {**PINS, Path(__file__).resolve(): sha(Path(__file__))}
    authenticate(pins)
    source = fresh_source(pins)
    top, bottom, inputs, material, fasteners = map(read, (TOP, BOTTOM, INPUTS, MATERIAL, FASTENERS))
    require(all(record["complete_joint_acceptance"] is False and record["physical_release"] is False
                for record in (top, bottom)), "retained geometry claims qualification")
    properties = material["conditional_DF_L_No2_base_row"]["base_properties"]
    require(properties["G_for_dowel_bearing"] == 0.5
            and properties["Fv_parallel"] == 180 and properties["Fc_perpendicular"] == 625,
            "retained wood hypothesis changed")
    fv, fc = (properties[key] * PSI_MPA for key in ("Fv_parallel", "Fc_perpendicular"))
    require(math.isclose(fv, top["component_references_mpa"]["Fv_parallel"], abs_tol=1e-12)
            and math.isclose(fc, top["component_references_mpa"]["Fc_perpendicular"], abs_tol=1e-12),
            "retained top wood references differ")
    yield_math = pure_functions(YIELD_MATH, ("single_shear",), {"math": math})
    lateral = pure_functions(BOTTOM_MATH, ("angle", "bearing", "reference"),
                             {"math": math, "single_shear": yield_math.single_shear})
    lateral.single_shear = yield_math.single_shear
    lateral.N_PER_LBF = N_PER_LBF
    top_math = pure_functions(TOP_MATH, ("lateral_reference",),
                             {"math": math, "correction": SimpleNamespace(lateral=lateral)})
    balance = pure_functions(BOTTOM_REPLAY, ("physical_balance",),
                             {"math": math, "require": require}).physical_balance
    grains = {row["member_id"]: unit(row["reduced_geometry_descriptor"]["axis"])
              for row in inputs["members"] if "axis" in row["reduced_geometry_descriptor"]}
    connections = {row["axis_id"]: row for row in inputs["connections"] if row["kind"] == "candidate_bolt"}
    paths = {level: {(row["axis_id"], row["grain_direction_sign"]): row
                     for row in packet["finished_paths"]} for level, packet in (("top", top), ("bottom", bottom))}
    seats = {"top": {(row["axis_id"], row["body"]): row for row in top["washer_seats"]},
             "bottom": {(row["axis_id"], row["member"]): row for row in bottom["washer_geometry"]}}
    bottom_factors = {}
    for row in bottom["states"]:
        axis, factors = row["axis_id"], row["component_factors"]
        require(axis not in bottom_factors or bottom_factors[axis] == factors,
                "retained geometry modifiers vary with historical case")
        bottom_factors[axis] = factors
    groups = {(row["level"], row["side"], row["host"]): row for row in source["preparation"]}
    require(len(groups) == len(source["preparation"]) == 8, "eight host geometry identities differ")
    axes = [axis for group in groups.values() for axis in group["axis_ids"]]
    require(len(axes) == len(set(axes)) == 16, "sixteen unique corner axes required")
    for group in groups.values():
        level, side, host, cleat = (group[key] for key in ("level", "side", "host", "cleat"))
        expected_host = "base_rail_top" if level == "top" else "base_rail_bottom_" + side
        require(level in {"top", "bottom"} and side in {"left", "right"}
                and cleat == level + "_outer_" + side + "_cleat"
                and host in {expected_host, "base_side_" + side}
                and len(group["axis_ids"]) == 2, "corner host ownership differs")
        family = group["geometry"]
        rail = host == expected_host
        expected = (38.1 if rail else 88.9, 139.7 if level == "top" and rail else 88.9,
                    7.9375 if level == "top" and not rail else 6.35,
                    9.0 if level == "top" and not rail else 7.5)
        require(tuple(family[key] for key in ("host_length_mm", "cleat_length_mm", "diameter_mm", "bore_mm"))
                == expected, "authenticated finished corner geometry differs")
        if level == "bottom":
            for member in (host, cleat):
                actual = unit(group["bottom_definition"]["finished_members"][member]["geometry"]["axis"])
                require(close(actual, grains[member], 1e-8), "finished bottom grain differs")
            require(group["bottom_definition"]["family"] == family, "bottom ordered receiver geometry differs")

    blocks, local_states, interfaces = {}, {}, []
    for block in source["states"]:
        level, side, case = block["level"], block["side"], block["case_id"]
        key = level, side, case
        require(key not in blocks, "duplicate fresh block/case")
        blocks[key] = block
        expected_hosts = {g["host"] for g in groups.values() if (g["level"], g["side"]) == (level, side)}
        require(set(block["hosts"]) == expected_hosts, "fresh block host census differs")
        balance(block["physical_whole_cleat_residual_n_nmm"], 0.002, 0.4)
        for host, record in block["hosts"].items():
            group, local = groups[level, side, host], record["state"]
            require(block["cleat"] == group["cleat"] and record["geometry"] == group["geometry"]
                    and local["case_id"] == case and local["gap_scale"] == 1.0
                    and len(local["face_cells"]) == (16 if level == "top" else 4)
                    and [b["axis_id"] for b in local["bolts"]] == group["axis_ids"],
                    "same-state case/geometry/contact identities differ")
            require(local["source_comparison_sha256"] == PINS[COMPARISON]
                    and local["source_response_sha256"] == PINS[RESPONSE]
                    and local["source_gravity_assessment_sha256"] == PINS[ASSESSMENT],
                    "local state contains a historical case-load authority")
            for field in ("physical_host_residual_n_nmm", "physical_cleat_interface_residual_n_nmm"):
                balance(record[field], 0.001, 0.2)
            require(all(math.isfinite(cell["pressure_mpa"]) and cell["pressure_mpa"] >= 0
                        for cell in local["face_cells"]), "invalid saved face pressure")
            interfaces.append({"level": level, "side": side, "case_id": case, "host": host,
                "cleat": block["cleat"], "face_cells": local["face_cells"],
                "maximum_face_pressure_over_Fc_perp_diagnostic": max(c["pressure_mpa"] for c in local["face_cells"]) / fc,
                "source_connector_wrench_on_host_n_nmm": local["source_connector_wrench_on_host_n_nmm"],
                "physical_host_residual_n_nmm": record["physical_host_residual_n_nmm"],
                "physical_cleat_interface_residual_n_nmm": record["physical_cleat_interface_residual_n_nmm"],
                "current_weight_once_n_nmm": block["current_weight_once_n_nmm"],
                "physical_whole_cleat_residual_n_nmm": block["physical_whole_cleat_residual_n_nmm"]})
            for bolt in local["bolts"]:
                axis_key = case, bolt["axis_id"]
                require(axis_key not in local_states, "duplicate local axis/case")
                local_states[axis_key] = (block, record, bolt)
    require(set(blocks) == {(level, side, case) for level in ("top", "bottom")
                            for side in ("left", "right") for case in CASES}
            and len(interfaces) == 48, "four-corner six-case block census differs")
    exported = source["same_state_bolt_actions"]
    keys = [(row["case_id"], row["axis_id"]) for row in exported]
    require(len(keys) == len(set(keys)) == len(local_states) == 96
            and set(keys) == {(case, axis) for case in CASES for axis in axes},
            "fresh 16-axis by six-case extractor census differs")

    states = []
    for row in exported:
        level, side, host, cleat, axis = (row[key] for key in ("level", "side", "host", "cleat", "axis_id"))
        block, record, bolt = local_states[row["case_id"], axis]
        group, family = groups[level, side, host], row["geometry"]
        fields = [field for field in block["beam_fields"] if field["axis_id"] == axis]
        require(row["local_bolt_state"] == bolt and row["beam_fields"] == fields and fields
                and row["cleat"] == block["cleat"] and row["level"] == block["level"]
                and row["side"] == block["side"] and family == group["geometry"]
                and axis in group["axis_ids"]
                and all(field["host"] == host for field in fields), "extractor lost same-state ownership or beam fields")
        for name in ("physical_host_residual_n_nmm", "physical_cleat_interface_residual_n_nmm"):
            require(row[name] == record[name], "extractor physical receipt differs")
        require(row["physical_whole_cleat_residual_n_nmm"] == block["physical_whole_cleat_residual_n_nmm"],
                "extractor whole-cleat receipt differs")
        tension = float(bolt["compatible_T_n"])
        force = [-value for value in bolt["bore_force_on_host_xyz_n"]]
        shear, diameter = norm(force), family["diameter_mm"]
        require(math.isfinite(tension) and tension >= 0 and bolt["projected_shortening_mm"] == 0
                and math.isclose(shear, bolt["bore_V_resultant_n"], abs_tol=1e-7, rel_tol=0)
                and len(bolt["end_contacts"]) == 2, "invalid simultaneous signed bolt state")
        require(all(bolt[key] is None for key in
                    ("actual_hardware_capacity_n", "actual_washer_capacity_n", "actual_washer_stress_mpa"))
                and all(end["actual_washer_capacity_n"] is None and end["actual_washer_stress_mpa"] is None
                        for end in bolt["end_contacts"]), "source contains an unqualified actual capacity")
        lengths = [family["host_length_mm"], family["cleat_length_mm"]]
        for receiver, length in zip(("host", "cleat"), lengths, strict=True):
            samples = [sample for sample in bolt["bore_fields"] if sample["receiver"] == receiver]
            start = 0.0 if receiver == "host" else lengths[0]
            require(samples and all(math.isfinite(s["quadrature_weight_mm"]) and s["quadrature_weight_mm"] > 0 for s in samples)
                    and all(math.isfinite(s["x_mm"]) and start <= s["x_mm"] <= start + length for s in samples)
                    and math.isclose(sum(s["quadrature_weight_mm"] for s in samples), length, abs_tol=1e-7, rel_tol=0),
                    "bore quadrature does not cover its actual ordered bearing length")
        require({s["receiver"] for s in bolt["bore_fields"]} == {"host", "cleat"}, "unsupported extra bore receiver")
        own_force = [sum(a["force_xyz_n"][i] for a in record["physical_cleat_interface_actions"]
                         if a["kind"] == "bore_station_resultant" and a["identity"] == axis) for i in range(3)]
        require(close(own_force, force, 0.001), "opposed same-state bore resultants do not close")
        own_grains = [grains[host], grains[cleat]] if level == "top" else [
            unit(group["bottom_definition"]["finished_members"][member]["geometry"]["axis"]) for member in (host, cleat)]
        bolt_axis = unit(bolt["bolt_axis_head_to_nut_xyz"] if level == "top" else bolt["actual_axis_head_to_nut_xyz"])
        receiver_ids = connections[axis]["receiver_member_ids"]
        supported = len(receiver_ids) == 2 and set(receiver_ids) == {host, cleat}
        status = "CONDITIONAL_SINGLE_SHEAR_92KSI" if supported else "MULTI_RECEIVER_NOT_SINGLE_SHEAR"
        if supported and any(abs(dot(bolt_axis, grain)) > 1e-8 for grain in own_grains):
            status = "END_GRAIN_METHOD_SEPARATE"
        angles = [lateral.angle(force, grain) for grain in own_grains]
        reference, reference_n = None, None
        if status == "CONDITIONAL_SINGLE_SHEAR_92KSI":
            if level == "top":
                reference = top_math.lateral_reference(force, diameter, lengths, own_grains, FYB_PSI)
                reference_n = reference["reference_n"]
            else:
                require(diameter == 6.35, "quarter-inch bottom reference used on another diameter")
                reference = lateral.reference(lengths, angles, FYB_PSI)
                reference_n = reference["reference_lateral_lbf"] * N_PER_LBF
        factor_record = ({"Cg_Cdelta": top["rail_component_Cg_Cdelta"]} if host == "base_rail_top"
                         else {"combined_multiplier": 1.0}) if level == "top" else bottom_factors[axis]
        factor = math.prod(factor_record["Cg_Cdelta"]) if "Cg_Cdelta" in factor_record else factor_record["combined_multiplier"]
        require(math.isfinite(factor) and 0 < factor <= 1, "invalid retained component modifier")
        if level == "bottom":
            require(math.isclose(factor, factor_record["Cg_component_scenario"] * factor_record["Cdelta_end_scenario"], abs_tol=1e-12),
                    "bottom modifier product differs")
        parallel = dot(force, own_grains[1])
        path = paths[level].get((axis, 1 if parallel >= 0 else -1))
        path_ok = (status == "CONDITIONAL_SINGLE_SHEAR_92KSI" and path is not None
                   and path["block"] == cleat and math.isfinite(path["minimum_finished_one_plane_area_mm2"])
                   and path["minimum_finished_one_plane_area_mm2"] > 0
                   and math.isclose(path["bearing_thickness_mm"], lengths[1], abs_tol=1e-6)
                   and math.isclose(path["bore_diameter_mm"], family["bore_mm"], abs_tol=1e-7))
        seat_records = []
        for end, member in enumerate((host, cleat)):
            recovered = [s for s in record["wood_seat_recovery"] if s["axis_id"] == axis
                         and s["end"].startswith("host_" if end == 0 else "cleat_")]
            require(len(recovered) == 1, "missing same-state own end seat")
            seat = seats[level].get((axis, member))
            area, seat_ok = None, False
            if seat is not None:
                if level == "top":
                    seat_ok = (seat["maximum_envelope_supported_fraction"] == 1.0
                               and close(recovered[0]["nominal_outer_wood_seat_xyz_mm"], seat["seat_point_mm"]))
                    area = seat["minimum_annulus_area_mm2"] if seat_ok else None
                else:
                    areas = [s["supported_area_mm2"] for s in seat["conditional_hole_only_areas"] if s["mode"] == "combined"]
                    seat_ok = (seat["geometry_screen_pass"] and areas
                               and all(s["hole_only_applicable"] for s in seat["conditional_hole_only_areas"])
                               and recovered[0]["member"] == member
                               and close(recovered[0]["nominal_outer_wood_seat_xyz_mm"], seat["point_xyz_mm"]))
                    area = min(areas) if seat_ok else None
            require(area is None or math.isfinite(area) and area > 0, "invalid retained supported washer area")
            seat_records.append({"member": member, "end": end, "applicable": bool(seat_ok),
                                 "minimum_supported_area_mm2": area, "retained_geometry": seat,
                                 "same_state_pressure_recovery": recovered[0], "end_contact": bolt["end_contacts"][end]})
        seat_area = min(s["minimum_supported_area_mm2"] for s in seat_records) if (
            status == "CONDITIONAL_SINGLE_SHEAR_92KSI" and all(s["applicable"] for s in seat_records)) else None
        pressure = tension / seat_area if seat_area is not None else None
        area_thread = (0.0524 if diameter == 7.9375 else 0.0318) * 25.4**2
        axial, shank_area = tension / area_thread, math.pi * diameter**2 / 4
        direct_vm = math.sqrt(axial**2 + 3 * (shear / shank_area)**2)
        stress = bolt["peak_stress_witness"]
        require(stress["axis_id"] == axis and any(all(field.get(key) == value for key, value in stress.items()) for field in fields)
                and all(math.isfinite(field["nominal_smooth_von_mises_proxy_mpa"]) and field["nominal_smooth_von_mises_proxy_mpa"] >= 0 for field in fields)
                and stress["nominal_smooth_von_mises_proxy_mpa"] == max(f["nominal_smooth_von_mises_proxy_mpa"] for f in fields)
                and math.isclose(stress["proxy_over_conditional_92ksi_Fyb"], stress["nominal_smooth_von_mises_proxy_mpa"] / (FYB_PSI * PSI_MPA), abs_tol=1e-12),
                "complete same-state beam stress witness differs")
        reserve, reserve_ratio, reserve_status = None, None, "NOT_AN_EXISTING_TOP_REFERENCE"
        if level == "bottom":
            reserve_status = status
            if reference_n is not None:
                tau = 4 * shear / (3 * shank_area)
                radicand = (FYB_PSI * PSI_MPA)**2 - 3 * tau**2
                remaining = math.sqrt(radicand) - axial if radicand > 0 else 0
                if remaining > 0:
                    reserve = lateral.reference(lengths, angles, remaining / PSI_MPA)
                    reserve_n = reserve["reference_lateral_lbf"] * N_PER_LBF
                    require(reserve_n <= reference_n + 1e-8, "steel reserve raises unchanged lateral reference")
                    reserve_ratio, reserve_status = shear / (factor * reserve_n), "CONDITIONAL_SAME_STATE_RESERVE"
                else:
                    reserve_status = "EXHAUSTED_CONDITIONAL_STEEL_RESERVE"
        strip = None
        if pressure is not None:
            outer = (0.905 if diameter == 7.9375 else max(fasteners["dimension_inputs"]["washer"]["od_in"])) * 25.4 / 2
            thickness = min(seats["top"][axis, member]["minimum_thickness_mm"] for member in (host, cleat)) if level == "top" else min(fasteners["dimension_inputs"]["washer"]["thickness_in"]) * 25.4
            radius = family["flat_radius_mm"]
            strip = 6 * pressure / radius * ((outer**3 - radius**3) / 3 - radius * (outer**2 - radius**2) / 2) / thickness**2
        reference_limits = {
            "lateral_over_adjusted_92ksi_reference": status,
            "parallel_over_finished_path_reference": "NO_APPLICABLE_SAME_GEOMETRY_FINISHED_PATH" if not path_ok else None,
            "mean_washer_wood_pressure_over_Fc_perp": (status if status != "CONDITIONAL_SINGLE_SHEAR_92KSI"
                else "NO_APPLICABLE_SUPPORTED_OWN_SEAT") if pressure is None else None,
            "bottom_same_state_steel_reserve_ratio": reserve_status,
        }
        states.append({**identity(row), "signed_T_n": tension, "V_n": shear,
            "signed_lateral_force_on_cleat_xyz_n": force, "recovered_cleat_bore_force_xyz_n": own_force,
            "opposed_bore_force_residual_xyz_n": [a - b for a, b in zip(own_force, force, strict=True)],
            "ordered_receivers_host_cleat": [host, cleat], "ordered_wood_lengths_mm": lengths,
            "diameter_mm": diameter, "bore_mm": family["bore_mm"], "grain_axes_host_cleat_xyz": own_grains,
            "bolt_axis_head_to_nut_xyz": bolt_axis, "load_to_grain_degrees": angles,
            "lateral_reference_status": status, "lateral_reference": reference,
            "reference_92ksi_n": reference_n, "component_factors": factor_record,
            "lateral_over_adjusted_92ksi_reference": shear / (factor * reference_n) if reference_n is not None else None,
            "parallel_force_n": parallel, "finished_path": path,
            "parallel_over_finished_path_reference": abs(parallel) / (fv * path["minimum_finished_one_plane_area_mm2"]) if path_ok else None,
            "own_end_seats": seat_records, "minimum_supported_washer_area_mm2": seat_area,
            "mean_washer_wood_pressure_mpa": pressure, "mean_washer_wood_pressure_over_Fc_perp": pressure / fc if pressure is not None else None,
            "nominal_thread_tensile_area_mm2": area_thread, "direct_combined_steel_vm_mpa": direct_vm,
            "direct_combined_steel_over_92ksi": direct_vm / (FYB_PSI * PSI_MPA),
            "smooth_bolt_stress_witness": stress, "smooth_bolt_VM_over_92ksi": stress["proxy_over_conditional_92ksi_Fyb"],
            "bottom_same_state_steel_reserve_reference": reserve, "bottom_same_state_steel_reserve_ratio": reserve_ratio,
            "steel_reserve_status": reserve_status, "washer_radial_strip_required_stress_mpa": strip,
            "sampled_end_wood_pressure_peak_mpa": max(end["wood_contact"]["pressure_peak_mpa"] for end in bolt["end_contacts"]),
            "reference_limits": reference_limits, "local_bolt_state": bolt, "beam_fields": fields,
            "actual_hardware_capacity_n": None, "actual_washer_capacity_n": None,
            "actual_washer_stress_mpa": None, "splitting_capacity_n": None, "group_capacity_n": None,
            "native_joint_capacity_n": None, **FLAGS})
    require(len(states) == 96 and all(sum(row["level"] == level for row in states) == 48 for level in ("top", "bottom")),
            "completed reference census differs")
    summary = component_summary(states)
    result = {"schema": "knee_bridge_original_corner_same_state_references/v1",
        "status": "COMPLETE_FRESH_SAME_STATE_COMPONENT_REFERENCES", "case_ids": CASES,
        "counts": {"corner_axes": 16, "block_states": 24, "host_states": 48, "bolt_states": 96,
                   "top_bolt_states": 48, "bottom_bolt_states": 48},
        "states": states, "interfaces": interfaces, "component_summary": summary,
        "conditional_Fyb_psi": FYB_PSI, "wood_references_mpa": {"Fv_parallel": fv, "Fc_perpendicular": fc},
        "modeled_mass_kg": MASS_KG, "dead_load_factor": DEAD_FACTOR,
        "fresh_load_sources": source["fresh_load_sources"], "source_sha256": source_map(pins),
        "source_corner_replay_sha256": PINS[SOURCE], "source_corner_receipt_sha256": PINS[RECEIPT],
        "source_closure_pin_count": 94, "mechanics_or_geometry_rerun": False,
        "native_CAD_or_frame_execution": False, "tests_run": False, "coupons_run": False,
        "review_loop_run": False, "helper_agents_created": False,
        "actual_hardware_capacity_n": None, "actual_washer_capacity_n": None,
        "splitting_capacity_n": None, "group_capacity_n": None, "native_joint_capacity_n": None,
        "limits": [
            "Only the authenticated fresh six nominal states supply loads: 250 lb with impact factor 2, signed 300 N directions and the fixed 100 mm lever; mass and dead factor are unchanged.",
            "Retained top diameter-dependent bearing and bottom 4450/5600 psi bearing are different conditional hypotheses. Only the 92 ksi smooth partially threaded bolt assumption is evaluated.",
            "Finished replay geometry governs diameter and bearing length. Raw source_record bolt envelopes in model-inputs retain older geometry and are not substituted for the finished local geometry.",
            "All comparisons use one axis/case's signed tension, bore force/couple, end contacts and complete saved beam fields. Independent peak component states are not combined.",
            "Top supported concentric annuli and bottom existing combined-offset supported areas remain their own retained mean-seat hypotheses; mean pressure does not qualify tilted contact or washer metal.",
            "Direct steel stress excludes beam bending; the separate complete smooth-beam stress witness retains bending. Bottom steel reserve is the existing simultaneous axial/shear reduction, not a new Fyb scenario or prescribed interaction rule.",
            "Finished tangent paths use their own signed parallel force and one-plane geometry. Oblique group and splitting capacity remain null; historical whole-host splitting demands are not replayed or adopted.",
            "End-grain and multi-receiver single-shear references remain null. Missing same-geometry paths or supported seats remain null with an explicit reason.",
            "Rigid timber, no-slip floor, hypothetical contact laws, reference geometry and smooth shank occupancy remain unverified assumptions. Delivered shank/thread exposure, washer capacity and native joint resistance remain unqualified.",
            "Completion is arithmetic coverage. A ratio above one or exhausted conditional reserve is visible to the parent; no formal criterion, complete joint or physical release is inferred.",
        ], **FLAGS}
    authenticate(pins)
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    write(output / "worksheet.json", result)
    write(output / "component-summary.json", summary)
    authenticate(pins)
    write(output / "receipt.json", {"source_sha256": source_map(pins),
        "output_sha256": {path.name: sha(path) for path in sorted(output.iterdir()) if path.is_file()},
        "source_unchanged_before_and_after_write": True, "source_closure_pin_count": 94,
        "counts": result["counts"], "status": result["status"], **FLAGS})
    authenticate(pins)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = build(arguments.output)
    print(json.dumps({"status": result["status"], "counts": result["counts"],
                      "component_summary": result["component_summary"]}, allow_nan=False))
