#!/usr/bin/env python3
"""Join current signed retained-bolt actions to conditional material references."""
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
sys.path.insert(0, str(ROOT))
LOAD_SHA = "f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1"
RAW_SHA = "c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9"
MANIFEST_SHA = "504728bb81018ad749544a12c967c240068d7ca2de0b6223c26a725958897d23"
EVIDENCE_SHA = "c58852dfc270f7bf1795ceb0cc8b6530b436f023bbf5a7c27ac9f4baa1e7f373"
CASES = ("a1-rear", "a12-rear", "k12-rear")
FACTORS = (.1, .2, .3, .45, .675, .925, 1.)
GROUPS = tuple(f"{kind}_bolt_{side}" for kind in
               ("lumber_leg", "rail_front", "rail_rear") for side in ("left", "right"))
AXES = tuple(f"{group}_{index}" for group in GROUPS for index in (1, 2))
FLAGS = ("qualified_for_design", "mechanical_acceptance", "joint_demand_accepted",
         "floor_capacity_established", "friction_qualified", "joint_accepted",
         "fabrication_release", "native_solve_executed")
N_PER_LBF = 4.4482216152605
PSI_TO_MPA = N_PER_LBF / 25.4**2
FINISHED_GAP = ("Existing directional helper uses the proposed outer stock box. "
                "Finished trim data exist, but no verified offline method is bound "
                "for a directional ray through trimmed multi-loop faces excluding "
                "the own bore. CAD methods were not executed. Finished-edge/end "
                "distances and Chapter12 applicability remain unresolved.")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pin(path: Path) -> dict:
    return {"sha256": sha(path), "size_bytes": path.stat().st_size}


def module(name: str, relative: str):
    """Load pure numerical files without importing the CAD package initializer."""
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def dot(a, b):
    return sum(x * y for x, y in zip(a, b, strict=True))


def sub(a, b):
    return [x - y for x, y in zip(a, b, strict=True)]


def add(a, b):
    return [x + y for x, y in zip(a, b, strict=True)]


def angle(force, axis) -> float | None:
    magnitude = math.hypot(*force)
    if magnitude == 0:
        return None
    return math.degrees(math.acos(min(1., abs(dot(force, axis)) / magnitude)))


def checked_load(path: Path, raw_path: Path) -> dict:
    require(sha(path) == LOAD_SHA, "changed frozen load report")
    require(sha(raw_path) == RAW_SHA, "changed accepted raw receipt")
    report = json.loads(path.read_text())
    raw = json.loads(raw_path.read_text())
    require(raw["report_sha256"] == LOAD_SHA, "raw receipt does not bind load report")
    require(report["candidate"] == "compact-floor-flush-wood-joints-development"
            and report["geometry_revision_id"] == "led-clearance-2x6-runner-seated-blocks-v1",
            "candidate or revision mismatch")
    require(all(report[k] is False and raw[k] is False for k in FLAGS),
            "upstream acceptance changed")
    require(set(report["axis_register"]) == set(AXES), "retained axis census changed")
    require(len(report["input_pins"]) == 143, "load input census changed")
    for name, expected in report["input_pins"].items():
        require(pin(ROOT / name) == expected, f"changed load input {name}")
    seen = set()
    for state in report["states"]:
        key = state["case_id"], state["increment_index"]
        require(key not in seen and key[0] in CASES and key[1] in range(7),
                "foreign or duplicate state")
        seen.add(key)
        require(state["load_factor"] == FACTORS[key[1]]
                and set(state["bolt_states"]) == set(AXES), "state census changed")
    require(len(seen) == 21, "incomplete state census")
    return report


def policy(axis: str) -> dict:
    if axis.startswith("lumber_leg"):
        sku, d, length, washer = "407", .5, 8., .132
    elif axis.startswith("rail_front"):
        sku, d, length, washer = "367", .375, 4., .104
    else:
        sku, d, length, washer = "368", .375, 4.5, .104
    return {"status": "inherited_hardware_policy_only", "catalog_sku_reference": sku,
            "nominal_diameter_in": d, "nominal_length_in": length,
            "catalog_max_head_washer_thickness_mm": washer * 25.4,
            "delivered_product": None, "delivered_full_body_to_transition_mm": None,
            "delivered_thread_root_diameter_in": None, "delivered_thread_class": None,
            "delivered_Fy_psi": None, "delivered_Fyb_psi": None,
            "actual_effective_NDS_diameter_in": None,
            "actual_steel_shear_area_mm2": None, "actual_minimum_tensile_area_mm2": None,
            "nut_thread_engagement": None, "washer_resistance_n": None}


def receiver(axis_row: dict, item: dict, force, geometry) -> dict:
    source = axis_row["source_axis_fields"]
    lo, hi = item["interval_from_axis_datum_mm"]
    require(0 <= lo < hi <= source["axis_length_mm"], "invalid bore interval")
    midpoint = [(lo + hi) / 2 * direction + origin for origin, direction in
                zip(source["datum_global_xyz_mm"], source["direction_global_xyz"], strict=True)]
    frame = item["stock_frame"]
    axes = frame["basis_columns_global_xyz"]
    require(abs(dot(axes[0], source["direction_global_xyz"])) < 1e-8,
            "bolt axis not perpendicular to modeled grain")
    classification = geometry.classify_member_fastener_load(
        force_on_member_global_n=force, grain_axis_global_unit=axes[0],
        bolt_axis_global_unit=source["direction_global_xyz"],
        bolt_center_global_mm=midpoint,
        member_frame_origin_global_mm=frame["origin_global_xyz_mm"],
        member_axes_global_unit=axes,
        member_bounds_local_mm=[[0., length] for length in frame["original_dimensions_gqr_mm"]],
    )
    return {"member": item["member"], "finished_feature_id": item["feature_id"],
            "finished_step_sha256": item["finished_step"]["file_sha256"],
            "bore_interval_mm": [lo, hi], "bearing_length_in": (hi - lo) / 25.4,
            "modeled_grain_axis_global_xyz": axes[0], "force_on_receiver_xyz_n": force,
            "load_to_grain_degrees": angle(force, axes[0]),
            "stock_box_direction_locator_only": classification,
            "finished_loaded_end_distance_mm": None,
            "finished_loaded_edge_distance_mm": None,
            "minimum_spacing_end_edge_verified": None, "finished_geometry_gap": FINISHED_GAP}


def lateral_references(receivers: list[dict], diameter: float, demand_n: float, nds) -> list:
    require(demand_n > 0 and all(r["load_to_grain_degrees"] is not None for r in receivers),
            "zero-demand orientation needs separate reference scenario")
    members = [dict(r, fe_theta_psi=nds._fe_theta_psi(
        specific_gravity=.5, diameter_in=diameter,
        angle_degrees=r["load_to_grain_degrees"])) for r in receivers]
    reductions = nds._reduction_terms(diameter_in=diameter,
                                    nominal_diameter_in=diameter,
                                    angle_max_degrees=max(r["load_to_grain_degrees"] for r in members))
    output = []
    for fyb in (45000., 106000.):
        values = nds._single_shear_modes(members[0], members[1], diameter, fyb, reductions)
        reverse = nds._single_shear_modes(members[1], members[0], diameter, fyb, reductions)
        require(math.isclose(min(values.values()), min(reverse.values()), rel_tol=1e-12),
                "main/side reversal changes minimum")
        z_n = min(values.values()) * N_PER_LBF
        output.append({"status": "idealized_full_D_zero_gap_single_fastener_reference_only",
                       "Fyb_scenario_psi": fyb, "Fyb_test_derived_or_adopted": False,
                       "specific_gravity_scenario": .5, "diameter_scenario_in": diameter,
                       "main_receiver": members[0]["member"], "side_receiver": members[1]["member"],
                       "main_Fe_psi": members[0]["fe_theta_psi"],
                       "side_Fe_psi": members[1]["fe_theta_psi"],
                       "reduction_terms": reductions, "mode_reference_lbf": values,
                       "reverse_assignment_mode_reference_lbf": reverse,
                       "governing_mode": min(values, key=values.get),
                       "single_fastener_unadjusted_reference_n": z_n,
                       "same_state_demand_divided_by_unadjusted_reference": demand_n / z_n,
                       "adjusted_resistance_n": None, "adjusted_joint_utilization": None,
                       "Cg": None, "Cdelta": None, "CD": None, "CM": None, "Ct": None,
                       "Ceg_scenario": 1., "actual_Ceg_verified": None,
                       "reference_qualified_for_this_finished_joint": False})
    return output


def steel_references(tie: float, lateral_vector, diameter: float, steel) -> dict:
    area_t = (.1419 if diameter == .5 else .0775) * 25.4**2
    area_v = math.pi * (diameter * 25.4)**2 / 4
    kwargs = {"axial_force_n": tie, "lateral_shear_vector_n": tuple(lateral_vector),
              "minimum_tensile_area_mm2": area_t, "shear_plane_area_mm2": area_v,
              "specified_min_yield_mpa": 92000 * PSI_TO_MPA,
              "property_scenario_id": "Grade5_nominal_UNC_At_and_full_D_shank",
              "material_basis": "ValueFastener Grade5 PDF page2, printed115; scenario only",
              "tensile_area_basis": "PortlandBolt nominal tensile stress area; not measured minimum root",
              "shear_area_basis": "Nominal full-D circular shank at the modeled lateral plane; conditional"}
    reference = steel.bolt_first_yield_reference(
        **kwargs, combined_action_area_mm2=area_v,
        combined_action_section_basis=("Hypothetical smooth full-D interface section carrying "
                                       "this same-state axial tie and average shear; no bolt bending"))
    actual = steel.bolt_first_yield_reference(
        axial_force_n=tie, lateral_shear_vector_n=tuple(lateral_vector),
        minimum_tensile_area_mm2=None, shear_plane_area_mm2=None,
        specified_min_yield_mpa=None, property_scenario_id=None,
        material_basis=None, tensile_area_basis=None, shear_area_basis=None)
    return {"conditional_nominal_material_reference": reference,
            "nominal_thread_tensile_stress_area_mm2": area_t,
            "hypothetical_full_D_interface_area_mm2": area_v,
            "actual_bolt_material_reference": actual,
            "actual_bolt_bending_demand_nmm": None, "actual_bolt_bending_resistance_nmm": None,
            "axial_complete_joint_resistance_n": None,
            "axial_missing": ["actual thread/shank and material evidence",
                              "nut/head/thread engagement and resistance",
                              "washer plate/spreading and actual contact/load sharing",
                              "wood bearing, splitting and net-section complete-joint applicability"],
            "wrench_offset_is_bolt_bending": False}


def produce(load_path: Path, raw_path: Path) -> dict:
    require(sha(HERE / "source-pins.json") == MANIFEST_SHA, "changed source manifest")
    require(sha(HERE / "source-evidence.json") == EVIDENCE_SHA, "changed source evidence")
    pins = json.loads((HERE / "source-pins.json").read_text())
    for name, expected in pins.items():
        require(pin(ROOT / name) == expected, f"changed method/source {name}")
    load = checked_load(load_path, raw_path)
    nds = module("retained_nds", "mini_moonboard/nds_2024_multi_member_bolt_yield.py")
    geometry = module("retained_direction", "mini_moonboard/wood_joint_directional_geometry.py")
    steel = module("retained_steel", "mini_moonboard/wood_joint_bolt_resistance.py")
    criteria = json.loads((ROOT / "docs/wood-joints-mvp/criteria.json").read_text())
    obligations = criteria["legacy_criteria"] + criteria["additional_candidate_obligations"]
    require(len(obligations) == 47 and all(r["status"] == "pending" for r in obligations),
            "criteria authority changed")
    register = {}
    for axis in AXES:
        item = load["axis_register"][axis]
        hardware = policy(axis)
        require(math.isclose(item["source_axis_fields"]["occupied_diameter_mm"] / 25.4,
                             hardware["nominal_diameter_in"], abs_tol=1e-12)
                and math.isclose(item["source_axis_fields"]["axis_length_mm"] / 25.4,
                                 hardware["nominal_length_in"], abs_tol=1e-12),
                "current modeled dimensions differ from inherited policy")
        lengths = [r["interval_from_axis_datum_mm"][1] - r["interval_from_axis_datum_mm"][0]
                   for r in item["receivers_head_to_nut"]]
        require(len(lengths) == 2 and math.isclose(
            item["receivers_head_to_nut"][0]["interval_from_axis_datum_mm"][1],
            item["receivers_head_to_nut"][1]["interval_from_axis_datum_mm"][0], abs_tol=1e-8),
            "not a contiguous modeled two-receiver stack")
        register[axis] = {"hardware_policy": hardware, "modeled_bearing_lengths_mm": lengths,
                          "modeled_wood_grip_mm": sum(lengths),
                          "conditional_full_body_transition_threshold_mm": (
                              sum(lengths) + hardware["catalog_max_head_washer_thickness_mm"]
                              - lengths[1] / 4),
                          "threshold_status": "conditional dimensions; measured transition and each member occupancy required",
                          "finished_receivers": item["receivers_head_to_nut"],
                          "adopted_reference_lateral_resistance_n": None,
                          "actual_adjusted_joint_resistance_n": None}
    rows, groups = [], []
    for state in load["states"]:
        key = {k: state[k] for k in ("case_id", "increment_index", "load_factor")}
        for axis in AXES:
            source = load["axis_register"][axis]
            actions = state["bolt_states"][axis]
            lateral = actions["lateral_interface_action"]
            force = lateral["force_on_first_xyz_n"]
            opposite = lateral["force_on_second_xyz_n"]
            require(all(math.isfinite(v) for v in force + opposite)
                    and math.hypot(*add(force, opposite)) < 1e-9
                    and abs(dot(force, source["source_axis_fields"]["direction_global_xyz"])) < 1e-8,
                    "lateral signed force scope changed")
            require((lateral["first"], lateral["second"]) == (source["first"], source["second"]),
                    "receiver ownership changed")
            receivers = [receiver(source, r, f, geometry) for r, f in
                         zip(source["receivers_head_to_nut"], (force, opposite), strict=True)]
            tie = actions["axial_interface_action"]["axial_along_installation_direction_n"]
            require(math.isfinite(tie) and tie >= 0, "unilateral tie not tension-positive")
            scalar_lateral = [r["scalar_force_on_first_N"] for r in actions["scalar_channels"]
                              if r["family"] == "bilateral_spring2"]
            require(len(scalar_lateral) == 2 and math.isclose(
                math.hypot(*scalar_lateral), math.hypot(*force), abs_tol=1e-8), "scalar/vector mismatch")
            d = register[axis]["hardware_policy"]["nominal_diameter_in"]
            rows.append(dict(key, axis_id=axis, lateral_force_on_first_xyz_n=force,
                             lateral_resultant_n=math.hypot(*force), same_state_axial_tie_n=tie,
                             source_row_ids=[r["source_row_id"] for r in actions["scalar_channels"]],
                             receivers=receivers,
                             lateral_references=lateral_references(receivers, d, math.hypot(*force), nds),
                             steel=steel_references(tie, scalar_lateral, d, steel), joint_accepted=False))
        for group in GROUPS:
            axis_ids = [f"{group}_{i}" for i in (1, 2)]
            action = [state["bolt_states"][a]["lateral_interface_action"] for a in axis_ids]
            delta = sub(action[1]["point"], action[0]["point"])
            spacing = math.hypot(*delta)
            row_axis = [v / spacing for v in delta]
            resultant = add(action[0]["force_on_first_xyz_n"], action[1]["force_on_first_xyz_n"])
            theta = angle(resultant, row_axis)
            require(theta is not None and theta > 1e-6, "group applicability must be revisited")
            groups.append(dict(key, group_id=group, axis_ids=axis_ids,
                               receiver_pair=[action[0]["first"], action[0]["second"]],
                               bolt_row_spacing_mm=spacing, bolt_row_unit_global_xyz=row_axis,
                               same_state_force_on_first_xyz_n=resultant,
                               resultant_to_bolt_row_degrees=theta, Cg=None,
                               group_adjusted_resistance_n=None,
                               method_gap="Existing Eq11.3-1 helper requires load-aligned row; current resultant is oblique. Per-fastener nonuniform actions preserved; no equal-sharing assumption.",
                               finished_group_edge_end_applicability=None))
    return {"schema": "retained_current_resistance_basis/v1", "status": "conditional_reference_only",
            "candidate": load["candidate"], "geometry_revision_id": load["geometry_revision_id"],
            "producer_sha256": sha(Path(__file__)), "source_pins": pins,
            "source_manifest_sha256": sha(HERE / "source-pins.json"),
            "source_evidence_sha256": sha(HERE / "source-evidence.json"),
            "load_report_sha256": LOAD_SHA, "accepted_raw_receipt_sha256": RAW_SHA,
            "rechecked_load_input_pins": load["input_pins"],
            "axis_register": register, "state_rows": rows, "group_state_rows": groups,
            "counts": {"axes": 12, "finished_receiver_memberships": 24, "states": 21,
                       "bolt_states": len(rows), "conditional_lateral_scenarios": len(rows) * 2,
                       "two_bolt_group_states": len(groups), "pending_criteria": 47, "closed_criteria": 0},
            "criteria_status": "all_47_pending_unchanged", "engineering_mvp_complete": False,
            **dict.fromkeys(FLAGS, False),
            "limits": ["Only the three frozen rear response sources; other load cases unresolved.",
                       "Full nominal D, zero gap, G=.5 and Fyb estimates are explicit scenarios; no finished-joint qualification.",
                       "No public NDS qualification gate bypassed: pure numeric helpers return component references only.",
                       "No old capacity, geometric wrench moment, bolt preload or friction credited.",
                       "Actual material, threads, steel areas, group/geometry adjustments and complete axial joint remain NULL.",
                       "No CAD/native execution, physical inspection, fabrication, candidate selection or release."]}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--load-report", type=Path, required=True)
    parser.add_argument("--raw-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args()
    data = (json.dumps(produce(args.load_report, args.raw_receipt), indent=2, sort_keys=True,
                       allow_nan=False) + "\n").encode()
    if args.check:
        require(data == args.check.read_bytes(), "resistance replay differs")
    args.output.write_bytes(data)
    print(json.dumps({"path": str(args.output), "sha256": sha(args.output), "size_bytes": len(data)}))


if __name__ == "__main__":
    main()
