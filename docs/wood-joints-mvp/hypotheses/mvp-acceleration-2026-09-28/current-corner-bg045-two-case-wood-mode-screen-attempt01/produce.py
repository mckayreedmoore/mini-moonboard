#!/usr/bin/env python3
"""Produce a source-bound BG045 two-case direction and wood-mode screen."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / ".git").exists())
BASE = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28"
EVAL = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24"
SOURCES = {
    "a12_demand_report": BASE / "current-corner-native-demand-export-attempt03/corner-demand-report.json",
    "a1_demand_report": BASE / "current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json",
    "a12_model": BASE / "current-springa-selected-floor-a12-rear-attempt03/model.json",
    "a1_model": BASE / "current-springa-selected-floor-a1-rear-attempt02/model.json",
    "a12_response_audit": BASE / "current-springa-selected-floor-a12-rear-attempt03/response.json",
    "a1_response_audit": BASE / "current-springa-selected-floor-a1-rear-attempt02/response-zero-u-token.json",
    "a12_resultant_direction_screen": BASE / "current-corner-resultant-direction-single-shear-attempt01/resultant-direction-screen.json",
    "a1_washer_screen": BASE / "current-corner-a1-rear-axial-seat-screen-attempt01/screen.json",
    "local_wood_geometry_screen": BASE / "current-corner-local-wood-screen-attempt01/section-screen.json",
    "appendix_e_precedent": BASE / "current-bg001-appendix-e-parallel-row-screen-attempt01/screen.json",
    "bg045_endgrain_scenario": BASE / "current-knee-header-endgrain-screen-attempt01/conditional-screen.json",
    "nds_scenario_table": BASE / "nds-screen/single-bolt-scenarios.json",
    "nds_single_bolt_producer": BASE / "nds-screen/produce.py",
    "dowel_yield_helper": ROOT / "fea/dowel_yield.py",
    "bearing_helper": ROOT / "mini_moonboard/bolted_timber_checks.py",
    "bolt_group_geometry": BASE / "bolt-groups/bolt-groups.json",
    "frame_grain_map": EVAL / "current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json",
    "block_grain_map": EVAL / "current-block-material-frame-map-attempt02/material-frame-map.json",
    "wood_limit_state_basis": ROOT / "docs/wood-joints-mvp/wood-limit-state-basis.md",
}
EXPECTED = {
    "a12_demand_report": "812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17",
    "a1_demand_report": "2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce",
    "a12_model": "8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8",
    "a1_model": "72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd",
    "a12_response_audit": "892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274",
    "a1_response_audit": "257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c",
    "a12_resultant_direction_screen": "d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10",
    "a1_washer_screen": "0f1160a62bdba6d5a8baf7607d4ecfc148bad44bbaee36d1971cecebf693eb19",
    "local_wood_geometry_screen": "22209a82b0bda6dfc5c140ccc4e481717e0e7c71d30a5827271c81ac71070564",
    "appendix_e_precedent": "3df6bf97fd4dfd07e81f17fa76bf4d7a841e055fa895f2d474984cfef030b488",
    "bg045_endgrain_scenario": "2c4e3cac2c1b951ccd99cff69c5678cc605651b752ff5f9f5cc5b2f7ee3eff28",
    "nds_scenario_table": "130041246af11fc8e3568a7091f585d0d75581b2e1fbb3a3f4b97b750d68a7ea",
    "nds_single_bolt_producer": "21d3b2b254b1ceb9a6cf777b98eb492b52f989cc019afa2209b92be3e4a3cdb0",
    "dowel_yield_helper": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "bearing_helper": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    "bolt_group_geometry": "4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4",
    "frame_grain_map": "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    "block_grain_map": "8705b8f100a2d3355c236fc19e6798bb7ad4862ba2d51826cf63a88db1285480",
    "wood_limit_state_basis": "1110e664a88f704773a463e83a2aeac3954b978048d811e4bff1effa55aa7c2e",
}
OUTPUT = HERE / "screen.json"
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
CASE_FILES = {
    "a12-rear": ("a12_demand_report", "a12_model", "a12_response_audit"),
    "a1-rear": ("a1_demand_report", "a1_model", "a1_response_audit"),
}
AXIS_IDS = ("knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2")
HEADER = "base_header"
BLOCK = "knee_outer_left_inner_frame_block"
N_PER_LBF = 4.4482216152605
MM_PER_IN = 25.4


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot import pinned helper {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def norm(v: list[float]) -> float:
    return math.sqrt(math.fsum(float(x) * float(x) for x in v))


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def vector_close(a: list[float], b: list[float], tol: float = 1.0e-8) -> bool:
    return len(a) == len(b) and all(abs(float(x) - float(y)) <= tol * max(1.0, abs(float(x)), abs(float(y))) for x, y in zip(a, b, strict=True))


def action_for(bolt: dict[str, Any], role: str) -> dict[str, Any]:
    rows = [row for row in bolt["actions"] if row.get("role") == role]
    if len(rows) != 1:
        raise ValueError(f"{bolt.get('axis_id')}: expected one {role} action")
    return rows[0]


def force_on(action: dict[str, Any], member: str) -> list[float]:
    if action["first"] == member:
        return [float(x) for x in action["force_on_first_xyz_n"]]
    if action["second"] == member:
        return [float(x) for x in action["force_on_second_xyz_n"]]
    raise ValueError(f"{member} is not attached to {action.get('source_connection_name')}")


def unit(v: list[float]) -> list[float]:
    n = norm(v)
    if not math.isfinite(n) or n <= 0.0:
        raise ValueError("finite nonzero direction required")
    return [float(x) / n for x in v]


def acute_angle_deg(force: list[float], grain: list[float]) -> float:
    cosine = min(1.0, max(0.0, abs(dot(unit(force), unit(grain)))))
    return math.degrees(math.acos(cosine))


def source_grain_vectors(frame_map: dict[str, Any], block_map: dict[str, Any], bolt_groups: dict[str, Any], models: dict[str, dict[str, Any]]) -> dict[str, list[float]]:
    frame_rows = {row["member_id"]: row for row in frame_map["members"]}
    block_rows = {row["part_id"]: row for row in block_map["members"]}
    grains = {
        HEADER: unit([float(x) for x in frame_rows[HEADER]["conditional_grain_assignment"]["proposed_global_xyz"]]),
        BLOCK: unit([float(x) for x in block_rows[BLOCK]["conditional_grain_assignment"]["grain_direction_global_xyz"]]),
    }
    if not vector_close(grains[HEADER], [1.0, 0.0, 0.0]) or not vector_close(grains[BLOCK], [0.0, 0.0, 1.0]):
        raise ValueError("pinned source-proposed BG045 grain directions changed")
    for model in models.values():
        for member in (HEADER, BLOCK):
            stated = model["body_geometry"][member]["geometry_record"]["source_descriptor"]["grain_global_xyz"]
            if not vector_close([float(x) for x in stated], grains[member]):
                raise ValueError(f"model grain binding differs from pinned map for {member}")
    axis_rows = [r for r in bolt_groups["candidate_axis_receiver_grain_angles"] if r.get("group_id") == "BG045"]
    if len(axis_rows) != 4:
        raise ValueError("expected four source grain-angle records for BG045")
    for row in axis_rows:
        if row.get("receiver_member_id") not in grains or not vector_close([float(x) for x in row["source_proposed_grain_unit_global_xyz"]], grains[row["receiver_member_id"]]):
            raise ValueError("BG045 axis/receiver grain-angle record differs from the pinned grain map")
    return grains


def geometry_bounds(model: dict[str, Any], grains: dict[str, list[float]]) -> dict[str, Any]:
    h = model["body_geometry"][HEADER]["geometry_record"]
    b = model["body_geometry"][BLOCK]["geometry_record"]
    if not vector_close(h["axis"], [1.0, 0.0, 0.0]) or not vector_close(h["section_u"], [0.0, 1.0, 0.0]) or not vector_close(h["section_v"], [0.0, 0.0, 1.0]):
        raise ValueError("base_header local axis/section frame changed")
    if not vector_close(b["axis"], [0.0, 0.0, 1.0]) or not vector_close(b["section_u"], [1.0, 0.0, 0.0]) or not vector_close(b["section_v"], [0.0, 1.0, 0.0]):
        raise ValueError("inner-block local axis/section frame changed")
    return {
        HEADER: {
            "grain_unit_global_xyz": grains[HEADER],
            "bolt_axis_global_xyz": [0.0, 0.0, 1.0],
            "x_end_bounds_mm": sorted([float(h["start"][0]), float(h["end"][0])]),
            "y_edge_bounds_mm": [float(h["start"][1]) - float(h["gross_width_mm"]) / 2.0,
                                 float(h["start"][1]) + float(h["gross_width_mm"]) / 2.0],
            "z_envelope_bounds_mm": [float(h["start"][2]) - float(h["gross_depth_mm"]) / 2.0,
                                     float(h["start"][2]) + float(h["gross_depth_mm"]) / 2.0],
        },
        BLOCK: {
            "grain_unit_global_xyz": grains[BLOCK],
            "bolt_axis_global_xyz": [0.0, 0.0, 1.0],
            "x_edge_bounds_mm": [float(b["start"][0]) - float(b["gross_width_mm"]) / 2.0,
                                 float(b["start"][0]) + float(b["gross_width_mm"]) / 2.0],
            "y_edge_bounds_mm": [float(b["start"][1]) - float(b["gross_depth_mm"]) / 2.0,
                                 float(b["start"][1]) + float(b["gross_depth_mm"]) / 2.0],
            "z_end_bounds_mm": sorted([float(b["start"][2]), float(b["end"][2])]),
        },
    }


def distances_for(force: list[float], point: list[float], bounds: dict[str, Any], member: str) -> dict[str, Any]:
    xlo, xhi = bounds["x_end_bounds_mm"] if member == HEADER else bounds["x_edge_bounds_mm"]
    ylo, yhi = bounds["y_edge_bounds_mm"]
    xdir = "+X" if force[0] > 0 else ("-X" if force[0] < 0 else None)
    ydir = "+Y" if force[1] > 0 else ("-Y" if force[1] < 0 else None)
    return {
        "source_model_envelope_distances_mm": {
            "x_minus": float(point[0]) - xlo,
            "x_plus": xhi - float(point[0]),
            "y_minus": float(point[1]) - ylo,
            "y_plus": yhi - float(point[1]),
        },
        "signed_component_directions": {"x": xdir, "y": ydir},
        "selected_component_boundary_distances_mm": {
            "x": (float(point[0]) - xlo if xdir == "-X" else (xhi - float(point[0]) if xdir == "+X" else None)),
            "y": (float(point[1]) - ylo if ydir == "-Y" else (yhi - float(point[1]) if ydir == "+Y" else None)),
        },
        "interpretation": "axis-aligned CAD envelope center-to-boundary distances only; not verified finished end/edge distances or an NDS Table 12.5.1 check",
    }


def ray_first_edge(point: list[float], direction: list[float], bounds: dict[str, Any]) -> dict[str, Any]:
    """Return first rectangular-envelope face met by a signed in-plane ray."""
    ux, uy = unit([float(direction[0]), float(direction[1])])
    xlo, xhi = bounds["x_edge_bounds_mm"]
    ylo, yhi = bounds["y_edge_bounds_mm"]
    options: list[tuple[float, str, float]] = []
    if ux > 0:
        options.append(((xhi - point[0]) / ux, "+X", xhi - point[0]))
    elif ux < 0:
        options.append(((xlo - point[0]) / ux, "-X", point[0] - xlo))
    if uy > 0:
        options.append(((yhi - point[1]) / uy, "+Y", yhi - point[1]))
    elif uy < 0:
        options.append(((ylo - point[1]) / uy, "-Y", point[1] - ylo))
    options = [row for row in options if row[0] >= 0.0]
    if not options:
        raise ValueError("ray does not meet a finite rectangular edge")
    travel, face, normal_distance = min(options, key=lambda row: row[0])
    return {"first_face_on_force_ray": face, "ray_travel_to_face_mm": travel,
            "center_to_face_distance_measured_normal_to_face_mm": normal_distance}


def edge_face_component(force: list[float], point: list[float], bounds: dict[str, Any], member: str, minimum_mm: float) -> list[dict[str, Any]]:
    """Emit directional face distances without turning oblique components into a full check."""
    xlo, xhi = bounds["x_edge_bounds_mm"]
    ylo, yhi = bounds["y_edge_bounds_mm"]
    options: list[tuple[str, float]] = []
    if force[0] > 0:
        options.append(("+X", xhi - point[0]))
    elif force[0] < 0:
        options.append(("-X", point[0] - xlo))
    if force[1] > 0:
        options.append(("+Y", yhi - point[1]))
    elif force[1] < 0:
        options.append(("-Y", point[1] - ylo))
    output = []
    for face, distance in options:
        output.append({"face_selected_by_signed_component": face,
                       "source_envelope_center_to_face_distance_mm": distance,
                       "ratio_to_conditional_4D_minimum": distance / minimum_mm,
                       "screen": "below_4D_conditional_envelope_threshold" if distance + 1.0e-9 < minimum_mm else "at_or_above_4D_conditional_envelope_threshold"})
    return output


def read_acceptance(case_id: str, report: dict[str, Any], model: dict[str, Any], response: dict[str, Any], expected_model_hash: str, expected_response_hash: str) -> dict[str, Any]:
    source = report["authenticated_source_case"]
    incs = report.get("increments", [])
    gates = report.get("response_audit_root_gates", {})
    checks = {
        "source_report_numerical_demand_only": report.get("schema") in ("current_corner_native_demand_report/v1", "current_corner_case_bound_demand_report/v1") and report.get("status") == "PASS_NUMERICAL_CORNER_DEMAND_REPORT_ONLY" and report.get("actual_case_demand_usable_for_conditional_joint_checks") is True,
        "authenticated_case_identity": report.get("case_id") == case_id and source.get("case_id") == case_id,
        "source_model_hash_bound": sha(SOURCES[f"{case_id.split('-')[0]}_model"]) == expected_model_hash and model.get("case_id") == case_id,
        "source_response_hash_bound": (source.get("response_audit_json_sha256", source.get("response_audit_sha256")) == expected_response_hash),
        "response_audit_status_nonacceptance": response.get("case_id") == case_id and response.get("status") == "PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY" and response.get("qualified_for_design") is False and response.get("mechanical_acceptance") is False,
        "all_root_response_gates_pass": bool(gates) and all(value is True for value in gates.values()),
        "full_factor_one_final_increment_and_corner_body_balance": bool(incs) and incs[-1].get("load_factor") == 1.0 and incs[-1].get("all_five_corner_bodies_raw_and_interval_balance_passed") is True and all(value is True for value in incs[-1].get("response_audit_gates", {}).values()),
        "no_complete_joint_acceptance_or_design_qualification": report.get("qualification_boundary", {}).get("complete_joint_accepted") is False and report.get("qualification_boundary", {}).get("qualified_for_design") is False,
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise ValueError(f"{case_id} accepted-demand gate failed: {', '.join(failed)}")
    return checks


def conditional_lateral_screen(bolt: dict[str, Any], case_id: str, nds: Any, fe: Any, geom: dict[str, Any]) -> dict[str, Any]:
    lateral = action_for(bolt, "candidate_bolt_lateral_plane")
    tie = action_for(bolt, "physical_bolt_outer_seat_tension")
    fh = force_on(lateral, HEADER)
    fb = force_on(lateral, BLOCK)
    if not vector_close(fh, [-x for x in fb]):
        raise ValueError("BG045 lateral action/reaction mismatch")
    th = force_on(tie, HEADER)
    tb = force_on(tie, BLOCK)
    if not vector_close(th, [-x for x in tb]):
        raise ValueError("BG045 tie action/reaction mismatch")
    if th[2] <= 0.0 or tb[2] >= 0.0:
        raise ValueError("BG045 washer-seat compression directions changed")

    m = norm(fh)
    angles = {
        HEADER: acute_angle_deg(fh, geom[HEADER]["grain_unit_global_xyz"]),
        BLOCK: acute_angle_deg(fb, geom[BLOCK]["grain_unit_global_xyz"]),
    }
    if abs(angles[BLOCK] - 90.0) > 1.0e-7:
        raise ValueError("block lateral load is expected to be fully cross-grain")
    d = 0.25
    fyb = 45000.0
    ce_g = 0.67
    fe_main = float(fe.dfl_dowel_bearing_psi(d, angles[BLOCK]))
    fe_side = float(fe.dfl_dowel_bearing_psi(d, angles[HEADER]))
    theta = max(angles.values())
    raw = nds.calculate(d, 139.0 / MM_PER_IN, 38.1 / MM_PER_IN, fe_main, fe_side, theta)
    refs = {name: float(raw["reference_values_lbf"][name]) * N_PER_LBF for name in MODES}
    if min(refs, key=refs.get) != "IV":
        raise ValueError("BG045 conditional direction screen no longer governs in mode IV")
    adjusted_refs = {name: value * ce_g for name, value in refs.items()}
    return {
        "axis_id": bolt["axis_id"],
        "physical_lateral_action_on_header_xyz_n": fh,
        "physical_lateral_action_on_block_xyz_n": fb,
        "lateral_resultant_n": m,
        "member_signed_grain_components_n": {
            HEADER: {"parallel_to_proposed_grain": dot(fh, geom[HEADER]["grain_unit_global_xyz"]), "cross_grain_resultant": math.sqrt(max(0.0, m*m-dot(fh, geom[HEADER]["grain_unit_global_xyz"])**2))},
            BLOCK: {"parallel_to_proposed_grain": dot(fb, geom[BLOCK]["grain_unit_global_xyz"]), "cross_grain_resultant": math.sqrt(max(0.0, m*m-dot(fb, geom[BLOCK]["grain_unit_global_xyz"])**2))},
        },
        "acute_force_to_grain_angle_degrees": angles,
        "model_envelope_geometry_only": {
            HEADER: distances_for(fh, bolt["axis_datum_global_xyz_mm"], geom[HEADER], HEADER),
            BLOCK: distances_for(fb, bolt["axis_datum_global_xyz_mm"], geom[BLOCK], BLOCK),
        },
        "outer_seat_tie_action": {
            "positive_bolt_tension_magnitude_n": norm(th),
            "force_on_header_xyz_n": th,
            "force_on_block_xyz_n": tb,
            "seat_load_relation": "compression at each washer seat; header is loaded transverse to proposed +X grain; block is loaded parallel to proposed +Z grain",
        },
        "conditional_single_bolt_lateral_yield_reference": {
            "method": "reviewed NDS/TR12 six-mode single-shear helper; reused angle-dependent Fe and the conditional BG045 main=block/side=header roles",
            "assumptions": {"material_scenario": "DF-L No. 2, SG 0.50, conditional only", "smooth_full_body_bolt_diameter_in": d, "main_block_bearing_length_mm": 139.0, "side_header_bearing_length_mm": 38.1, "interface_gap_mm": 0.0, "bolt_bending_yield_psi": fyb, "conditional_Ceg": ce_g, "Ceg_application": "once to each single-bolt lateral reference", "adjustment_factors_beyond_Ceg": []},
            "bearing_F_e_psi": {"block_main": fe_main, "header_side": fe_side},
            "unadjusted_six_mode_reference_n": refs,
            "six_mode_reference_after_Ceg_only_n": adjusted_refs,
            "governing_mode": "IV",
            "conditional_reference_after_Ceg_only_n": adjusted_refs["IV"],
            "resultant_over_reference_ratio": m / adjusted_refs["IV"],
            "ratio_scope": "one lateral resultant / one conditional single-bolt reference; not a design DCR, group capacity, combined-action check, or acceptance",
        },
    }


def produce() -> dict[str, Any]:
    actual_hashes = {name: sha(path) if path.is_file() else "MISSING" for name, path in SOURCES.items()}
    failed = [name for name, expected in EXPECTED.items() if actual_hashes.get(name) != expected]
    if failed:
        raise ValueError("source pin mismatch or missing: " + ", ".join(failed))
    docs = {name: read(path) for name, path in SOURCES.items() if path.suffix == ".json"}
    cases: dict[str, dict[str, Any]] = {}
    models: dict[str, dict[str, Any]] = {}
    for case_id, (report_key, model_key, response_key) in CASE_FILES.items():
        report, model, response = docs[report_key], docs[model_key], docs[response_key]
        expect_model = EXPECTED[model_key]
        expect_response = EXPECTED[response_key]
        gate_checks = read_acceptance(case_id, report, model, response, expect_model, expect_response)
        models[case_id] = model
        cases[case_id] = {"source_report_path": str(SOURCES[report_key].relative_to(ROOT)), "source_report_sha256": actual_hashes[report_key], "source_model_sha256": actual_hashes[model_key], "source_response_audit_sha256": actual_hashes[response_key], "accepted_response_checks": gate_checks, "final_increment": report["increments"][-1]}

    a12m, a1m = models["a12-rear"], models["a1-rear"]
    for member in (HEADER, BLOCK):
        if a12m["body_geometry"][member]["geometry_record"] != a1m["body_geometry"][member]["geometry_record"]:
            raise ValueError(f"A12/A1 source geometry differs for {member}")
    grains = source_grain_vectors(docs["frame_grain_map"], docs["block_grain_map"], docs["bolt_group_geometry"], models)
    bounds = geometry_bounds(a12m, grains)
    if a12m.get("geometry_revision_id") != a1m.get("geometry_revision_id"):
        raise ValueError("A12/A1 geometry revision differs")
    a12_ref = {row["axis_id"]: row for row in docs["a12_resultant_direction_screen"]["results"]["BG045"]}
    nds = load_module("bg045_nds_single_bolt_producer", SOURCES["nds_single_bolt_producer"])
    fe = load_module("bg045_bearing_helper", SOURCES["bearing_helper"])
    axis_rows: dict[str, Any] = {}
    case_sums: dict[str, Any] = {}
    for case_id, (report_key, _, _) in CASE_FILES.items():
        final = cases[case_id]["final_increment"]
        group = final["primary_physical_bolt_groups"]["BG045"]
        bolts = group["bolts"]
        if len(bolts) != 2 or {row["axis_id"] for row in bolts} != set(AXIS_IDS):
            raise ValueError(f"{case_id}: BG045 physical bolt inventory changed")
        rows = []
        for bolt in sorted(bolts, key=lambda row: row["axis_id"]):
            if abs(abs(dot(unit([float(x) for x in bolt["head_to_nut_unit_global_xyz"]]), grains[BLOCK])) - 1.0) > 1.0e-8:
                raise ValueError(f"{bolt['axis_id']}: bolt axis no longer parallels the block grain")
            row = conditional_lateral_screen(bolt, case_id, nds, fe, bounds)
            if case_id == "a12-rear":
                prior = a12_ref[bolt["axis_id"]]
                if abs(row["lateral_resultant_n"] - float(prior["lateral_resultant_demand_N"])) > 1e-7 or abs(row["conditional_single_bolt_lateral_yield_reference"]["conditional_reference_after_Ceg_only_n"] - float(prior["conditional_governing_reference_after_Ceg_only_N"])) > 1e-7:
                    raise ValueError("A12 reference reproduction mismatch")
            rows.append(row)
        header_sum = [math.fsum(r["physical_lateral_action_on_header_xyz_n"][k] for r in rows) for k in range(3)]
        block_sum = [math.fsum(r["physical_lateral_action_on_block_xyz_n"][k] for r in rows) for k in range(3)]
        if not vector_close(header_sum, [-x for x in block_sum]):
            raise ValueError("BG045 group lateral action/reaction does not close")
        case_sums[case_id] = {
            "header_lateral_group_force_xyz_n": header_sum,
            "block_lateral_group_force_xyz_n": block_sum,
            "header_lateral_resultant_n": norm(header_sum),
            "header_group_acute_angle_to_grain_degrees": acute_angle_deg(header_sum, bounds[HEADER]["grain_unit_global_xyz"]),
            "note": "Group sum is descriptive only; it is not a group capacity or complete member-section force.",
        }
        axis_rows[case_id] = rows

    # Cross-case washer-seat component screen uses the same candidate minimum
    # washer annulus and conditional header Fc-perp reference already in the
    # reviewed A1 seat packet. It is not a selected/delivered washer scenario.
    seat_rows = [r for r in docs["a1_washer_screen"]["seat_inventory"] if r["group_id"] == "BG045" and r["physical_member"] == HEADER]
    if len(seat_rows) != 2:
        raise ValueError("A1 washer source does not contain both BG045 header seats")
    area = float(seat_rows[0]["conditional_25nwus_min_annulus"]["area_mm2"])
    fc_ref = float(seat_rows[0]["conditional_base_timber_fc_perp_component"]["reference_n"])
    if any(abs(float(r["conditional_25nwus_min_annulus"]["area_mm2"]) - area) > 1e-8 for r in seat_rows):
        raise ValueError("BG045 washer area scenario differs by seat")
    washer_cases: dict[str, Any] = {}
    for case_id, report_key in (("a12-rear", "a12_demand_report"), ("a1-rear", "a1_demand_report")):
        seats = [r for r in cases[case_id]["final_increment"]["outer_washer_seats"] if r["physical_member"] == HEADER and r["axis_id"] in AXIS_IDS]
        by_axis = {r["axis_id"]: r for r in seats}
        if set(by_axis) != set(AXIS_IDS):
            raise ValueError(f"{case_id}: BG045 header washer seat actions missing")
        washer_cases[case_id] = [
            {"axis_id": axis, "bolt_tie_force_on_header_xyz_n": by_axis[axis]["seat_force_on_member_xyz_n"],
             "positive_bolt_tension_n": by_axis[axis]["signed_outer_seat_tie_action_n"],
             "uniform_pressure_over_candidate_min_annulus_mpa": by_axis[axis]["signed_outer_seat_tie_action_n"] / area,
             "conditional_header_Fc_perp_component_ratio": by_axis[axis]["signed_outer_seat_tie_action_n"] / fc_ref}
            for axis in AXIS_IDS
        ]

    # NDS detailing comparator for the named 1/4-in conditional bolt scenario.
    # The block lateral vector is wholly perpendicular to its proposed grain.
    diameter_mm = 0.25 * MM_PER_IN
    edge_4d = 4.0 * diameter_mm
    edge_1_5d = 1.5 * diameter_mm
    end_7d = 7.0 * diameter_mm
    end_4d = 4.0 * diameter_mm
    edge_detailing: dict[str, Any] = {
        "source_basis": "AWC NDS-2024 §§12.1.2.1, 12.5.1.3, Tables 12.5.1A and 12.5.1C; D=1/4 in is a conditional source scenario, not selected/delivered hardware",
        "conditional_thresholds_mm": {"assumed_bolt_diameter": diameter_mm, "Table_12_5_1C_perpendicular_loaded_edge_4D": edge_4d, "Table_12_5_1C_perpendicular_unloaded_edge_1_5D": edge_1_5d, "Table_12_5_1A_parallel_softwood_tension_7D": end_7d, "Table_12_5_1A_parallel_compression_4D": end_4d},
        "conditional_block_table_c_result": "Under the named 1/4-in scenario, the entire block lateral action is perpendicular to proposed grain, so Table 12.5.1C supplies the applicable directional edge categories. A1 axis 2 and the A1 group resultant both point toward the −Y face whose modeled distance is 20.0 mm, 5.4 mm below 4D=25.4 mm. This is a potential conditional detailing shortfall on the source envelope, not an adopted joint failure. A12 axis 1 also has a +Y component toward a 20.0 mm face, but its first rectangular ray face is +X at 44.45 mm; retain the +Y comparison as a conservative component-face sensitivity, not a normative second loaded-edge rule.",
        "conditional_geometry_difference_only": {"case_id": "a1-rear", "axis_id": "knee_outer_left_inner_header_2", "face": "block −Y", "source_envelope_distance_mm": 20.0, "conditional_4D_mm": edge_4d, "difference_to_conditional_4D_mm": round(edge_4d - 20.0, 6), "interpretation": "If this scenario were developed further, the 5.4 mm is only the normal-distance gap to the named conditional 4D comparator. It specifies neither an axis offset nor an edge increase and directs no geometry change."},
        "block_perpendicular_to_grain_loaded_edge_comparator": {},
        "header_parallel_component_end_comparator": {},
        "header_crossgrain_component_edge_sensitivity": {},
        "interpretation_limits": [
            "NDS §12.1.2.1 defines edge distance normal to grain and, for a member loaded perpendicular to grain, the loaded edge as the edge toward which the fastener acts. It does not establish a universal rectangular-corner/ray formula for selecting one face under an oblique in-plane action. The signed component-face distances are conservative conditional face comparisons; the force-ray face is a separately labeled geometric interpretation, not an NDS rule.",
            "For the block, the complete lateral vector is perpendicular to proposed +Z grain, so Table 12.5.1C supplies the relevant directional edge categories under the named 1/4-in scenario: 4D at the loaded edge and 1.5D at the unloaded edge. The Ceg lateral factor in §12.5.2.2 does not waive §12.5.1.3 detailing.",
            "For the header, each total lateral vector is oblique to +X grain. Its isolated signed Y component is shown against 4D only as a cross-grain-component sensitivity; this is not adopted as a full mixed-action Table 12.5.1C result.",
            "All comparisons use source-model external envelope dimensions. The 5.4 mm A1 axis-2 difference is a conditional comparison only; it is not a prescribed geometry modification or adopted failure. These are not verified delivered/as-built dimensions or complete connection acceptance.",
        ],
    }
    for case_id, rows in axis_rows.items():
        group_direction = case_sums[case_id]["block_lateral_group_force_xyz_n"]
        block_rows = []
        header_ends = []
        header_edges = []
        for row in rows:
            axis_id = row["axis_id"]
            fblock = row["physical_lateral_action_on_block_xyz_n"]
            fheader = row["physical_lateral_action_on_header_xyz_n"]
            point = next(b["axis_datum_global_xyz_mm"] for b in cases[case_id]["final_increment"]["primary_physical_bolt_groups"]["BG045"]["bolts"] if b["axis_id"] == axis_id)
            block_distances = row["model_envelope_geometry_only"][BLOCK]["source_model_envelope_distances_mm"]
            axis_ray = ray_first_edge(point, fblock, bounds[BLOCK])
            group_ray = ray_first_edge(point, group_direction, bounds[BLOCK])
            component_faces = edge_face_component(fblock, point, bounds[BLOCK], BLOCK, edge_4d)
            if case_id == "a1-rear" and axis_id == "knee_outer_left_inner_header_2":
                screen_limit = "Strongest potential conditional Table 12.5.1C loaded-edge issue: the signed axis action and the A1 group resultant both point toward the −Y face; the source-envelope distance is 20.0 mm versus 25.4 mm (4D), a 5.4 mm shortfall under the named 1/4-in scenario. The axis and group rectangular rays also first meet −Y. This is not an adopted joint FAIL, delivered-geometry finding, or geometry-change instruction."
            elif case_id == "a12-rear" and axis_id == "knee_outer_left_inner_header_1":
                screen_limit = "Conservative component-face sensitivity: the signed +Y component points toward a source-envelope face 20.0 mm from the axis, below conditional 4D=25.4 mm, but both the per-axis and group rectangular rays first meet +X at 44.45 mm. NDS does not supply the ray-selection rule used here; do not count this component comparison as a second normative Table 12.5.1C loaded edge or adopted joint FAIL."
            else:
                screen_limit = "The signed component-face comparisons are at or above conditional 4D=25.4 mm. The first-face ray is geometric context only, not an NDS selection rule for an oblique action; source-envelope dimensions and conditional bolt assumptions are not an adopted joint pass."
            block_rows.append({
                "axis_id": axis_id,
                "lateral_action_on_block_xyz_n": fblock,
                "grain_relation": "fully_perpendicular_to_proposed_grain",
                "all_four_center_to_face_distances_mm": block_distances,
                "component_face_comparators": component_faces,
                "component_comparator_scope": "Conservative conditional rectangular-face comparisons for the signed X/Y components; under an oblique action, the standard text reviewed here does not say that each component creates an independent Table 12.5.1C loaded edge.",
                "axis_force_ray_first_face": axis_ray,
                "case_group_resultant_ray_first_face": group_ray,
                "ray_and_group_select_same_first_face": axis_ray["first_face_on_force_ray"] == group_ray["first_face_on_force_ray"],
                "screen_limit": screen_limit,
            })
            xlo, xhi = bounds[HEADER]["x_end_bounds_mm"]
            if fheader[0] > 0:
                end_direction, end_distance = "+X", xhi - point[0]
            else:
                end_direction, end_distance = "-X", point[0] - xlo
            header_ends.append({
                "axis_id": axis_id,
                "signed_header_parallel_force_component_n": fheader[0],
                "direction_toward_source_envelope_end": end_direction,
                "source_envelope_end_distance_mm": end_distance,
                "distance_over_conditional_softwood_tension_7D": end_distance / end_7d,
                "distance_over_conditional_compression_4D": end_distance / end_4d,
                "screen": "above either Table 12.5.1A threshold on the source envelope; the force/action classification and finished geometry remain conditional",
            })
            header_edges.append({
                "axis_id": axis_id,
                "signed_header_crossgrain_force_component_n": fheader[1],
                "candidate_loaded_edge_from_crossgrain_component": "+Y" if fheader[1] > 0 else "-Y",
                "source_envelope_edge_distance_mm": (bounds[HEADER]["y_edge_bounds_mm"][1] - point[1] if fheader[1] > 0 else point[1] - bounds[HEADER]["y_edge_bounds_mm"][0]),
                "distance_over_conditional_4D": ((bounds[HEADER]["y_edge_bounds_mm"][1] - point[1] if fheader[1] > 0 else point[1] - bounds[HEADER]["y_edge_bounds_mm"][0]) / edge_4d),
                "screen": "conditional cross-grain-component sensitivity only; full lateral action is oblique and is not classified as perpendicular-to-grain Table C loading",
            })
        edge_detailing["block_perpendicular_to_grain_loaded_edge_comparator"][case_id] = block_rows
        edge_detailing["header_parallel_component_end_comparator"][case_id] = header_ends
        edge_detailing["header_crossgrain_component_edge_sensitivity"][case_id] = header_edges

    contact_results: dict[str, Any] = {}
    for case_id in CASE_FILES:
        final = cases[case_id]["final_increment"]
        contacts = [c for c in final["member_contact_bearing"]["contact_cells"] if {c["first"], c["second"]} == {HEADER, BLOCK}]
        if len(contacts) != 4:
            raise ValueError(f"{case_id}: expected four source-owned header/block contact cells")
        contact_results[case_id] = {
            "contact_cell_count": len(contacts),
            "cells": [{"source_connection_name": c["source_connection_name"], "modeled_area_mm2": c["contact"]["source_area_mm2"], "normal_action_on_header_n": c["contact"]["normal_action_on_first_n"], "force_on_header_xyz_n": c["force_on_first_xyz_n"], "modeled_average_pressure_mpa": c["contact"]["modeled_average_pressure_mpa"]} for c in contacts],
            "sum_compressive_normal_action_on_header_n": math.fsum(float(c["contact"]["normal_action_on_first_n"]) for c in contacts),
            "limits": "model-area average and recovered normal action only; not a stress distribution, wood resistance, or accepted contact state",
        }

    appendix = docs["appendix_e_precedent"]["standard_source"]
    return {
        "schema": "current_corner_bg045_two_case_wood_mode_screen/v1",
        "status": "PASS_SOURCE_BOUND_CONDITIONAL_DIRECTION_AND_COMPONENT_SCREEN_ONLY",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": "BG045 only: two actual bolt axes between the inner frame block and base header for the separately authenticated a12-rear and a1-rear conditional responses",
        "acceptance_boundary": {"numerical_case_demands_usable_for_conditional_checks": True, "mechanical_acceptance": False, "qualified_for_design": False, "complete_joint_accepted": False, "six_case_coverage_complete": False, "floor_slip_or_anchorage_qualified": False},
        "source_pins": {"files": {name: {"path": str(path.relative_to(ROOT)), "sha256": actual_hashes[name]} for name, path in SOURCES.items()}, "primary_nds_sources": {
            "chapter_12": {"edition": "ANSI/AWC NDS-2024, Chapter 12", "official_url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf", "sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a", "reviewed_sections": "§§12.1.2.1, 12.1.3.4, 12.5.1.3 (Tables 12.5.1A-D), 12.5.2.2; source digest inherited from reviewed local AWC Chapter 12 packet"},
            "appendix_e": {"edition": "ANSI/AWC NDS-2024, Appendix E", "official_url": appendix.get("appendix_pdf_url"), "sha256": appendix.get("appendix_pdf_sha256"), "reviewed_scope": "E.1-E.3 and E.6; inherited from source-pinned BG001 component screen"},
            "current_edition_page": "https://awc.org/resources/2024-nds/",
        }},
        "source_case_checks": {case_id: {"demand_report_sha256": data["source_report_sha256"], "model_sha256": data["source_model_sha256"], "response_audit_sha256": data["source_response_audit_sha256"], "gates": data["accepted_response_checks"]} for case_id, data in cases.items()},
        "member_frames_and_source_envelopes": {
            HEADER: {"proposed_grain": "+X", "bolt_axis": "+Z", "section_frame": "width +Y × depth +Z", "x_end_bounds_mm": bounds[HEADER]["x_end_bounds_mm"], "y_edge_bounds_mm": bounds[HEADER]["y_edge_bounds_mm"], "qualification": "source model rectangular envelope only; geometry record says not qualified for design"},
            BLOCK: {"proposed_grain": "+Z", "bolt_axis": "+Z", "end_section_frame": "width +X × depth +Y", "x_edge_bounds_mm": bounds[BLOCK]["x_edge_bounds_mm"], "y_edge_bounds_mm": bounds[BLOCK]["y_edge_bounds_mm"], "qualification": "source model rectangular envelope only; grade and as-built cuts/edges unobserved"},
            "BG045_axis_pitch_y_mm": abs(float(cases["a12-rear"]["final_increment"]["primary_physical_bolt_groups"]["BG045"]["bolts"][0]["axis_datum_global_xyz_mm"][1]) - float(cases["a12-rear"]["final_increment"]["primary_physical_bolt_groups"]["BG045"]["bolts"][1]["axis_datum_global_xyz_mm"][1])),
            "all_Bg045_bolt_axes_parallel_to_block_grain": True,
        },
        "per_axis_signed_actions_and_geometry": axis_rows,
        "per_case_lateral_group_resultants": case_sums,
        "nds_edge_and_end_distance_conditional_comparator": edge_detailing,
        "washer_seat_bearing_component": {
            "common_conditional_scenario": {"candidate_washer_lead": "Type A Wide 25NWUS dimensional lead; not selected or delivered", "minimum_annulus_area_mm2": area, "conditional_header_Fc_perp_reference_n": fc_ref, "material": "DF-L No. 2, Fc_perp=625 psi, conditional unadjusted reference", "support": "full annulus assumed; actual washer, support polygon, flatness, and load distribution unverified"},
            "case_seats": washer_cases,
            "block_seat_interpretation": "bolt-tie washer action on the block is parallel-to-grain compression; Fc_perp is inapplicable and no block Fc_parallel strength grade/reference is assigned",
        },
        "header_block_contact_bearing": contact_results,
        "net_section_row_and_splitting_applicability": {
            "A12_header": "Both bolt-plane actions have signed −X grain-parallel components, but also −Y cross-grain components; resultant is predominantly parallel. BG045 axes are spaced along Y across header grain. Appendix E.1 parallel-group and E.2/E.3 geometry/action conditions are not established for a complete mixed-action group, so no net-tension or row-tearout resistance is calculated. A candidate E.2 route would additionally need demonstrated member tension, actual complete net section and adjusted F't.",
            "A1_header": "The axis X components oppose and sum to only −32.624 N while Y components sum to +132.815 N; group resultant is cross-grain-dominant. Appendix E parallel-loaded group assumptions are not demonstrated; no E.2/E.3 value is calculated.",
            "block_both_cases": "Every BG045 lateral-plane action is 90° to proposed +Z grain; both outer washer ties compress the block parallel to +Z. BG045 does not furnish an Appendix E parallel-tension/row action on the block. The geometry-only block sections in the pinned local screen are not signed member demands.",
            "geometry_only_candidate_block_sections": docs["local_wood_geometry_screen"]["candidate_net_section_inputs"],
            "splitting": "Cross-grain actions make tension-perpendicular/splitting a required unresolved mode to assess on both receivers, especially the block (100% cross-grain lateral) and the A1 header (dominant transverse resultant). The action vectors are not a splitting tensile demand. NDS §§3.8.2 and 11.1.3 do not give a general splitting equation for this changed end-grain block/header topology; the pinned EC5 Figure 8.1 screen also does not establish applicability. No splitting capacity or pass/fail is reported.",
        },
        "limit_state_disposition": {
            "single_bolt_lateral_yield": "conditional individual-bolt component references reported per axis under the exact named assumptions; no sum across the two bolts, no mixed-axis/axial interaction, no group distribution adjustment, and no acceptance",
            "NDS_end_edge_detailing": "For the named conditional 1/4-in scenario, the block's all-cross-grain action puts Table 12.5.1C in scope; A1 axis 2/group points toward a 20.0 mm source-envelope −Y face versus 4D=25.4 mm, a potential 5.4 mm detailing deficit. A12 axis 1's +Y 20.0 mm component is retained as a conservative face sensitivity while its first geometric ray face is +X at 44.45 mm. The rectangular-ray/component-face convention is not claimed as a universal NDS rule. Header Y-component comparisons are sensitivity only because each full action is oblique to grain. No adopted joint fail/pass is assigned because bolt/hole and finished geometry remain conditional.",
            "washer_bearing": "conditional uniform-annulus Fc_perp component on header seats only; block tie bearing is parallel to grain, not Fc_perp",
            "net_tension_and_row_tearout": "not calculated; exact action/row applicability, critical cut/complete hole union, and adjusted strength basis are not established",
            "splitting": "unresolved; no generally applicable resistance equation established for this topology",
        },
        "not_calculated_or_accepted": ["full-member internal section force/moment resultants including simultaneous BG001/BG003/contact/other load paths", "header net-section plane with all intersecting bores/cuts", "block net-section tension demand", "Appendix E group tearout or mixed parallel/cross-grain/axial interaction", "block parallel compression reference/strength", "adjusted wood values, service factors, actual species/grade/moisture/condition", "actual bolt/washer selection, fit, threads and delivered dimensions", "washer contact-pressure distribution and steel bending/spreading", "wood splitting resistance", "whole-corner/joint acceptance or climbing/fabrication release"],
        "producer_source": {"path": str((HERE / "produce.py").relative_to(ROOT)), "sha256": sha(HERE / "produce.py")},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    result = produce()
    rendered = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.write:
        OUTPUT.write_text(rendered, encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")
        return
    if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != rendered:
        raise SystemExit("screen.json differs from source-bound producer output")
    print(f"verified {OUTPUT.relative_to(ROOT)} sha256={sha(OUTPUT)}")


if __name__ == "__main__":
    main()
