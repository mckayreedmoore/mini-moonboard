#!/usr/bin/env python3
"""Replay conditional grain applicability over the frozen seven-pair screen."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
CONTACT_DIR = BASE / "current-corner-timber-contact-pressure-screen-attempt01"
MATERIAL_DIR = Path("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30")
PINS_PATH = HERE / "source-pins.json"
OUTPUT_PATH = HERE / "grain-applicability.json"

CONTACT_SCREEN = CONTACT_DIR / "screen.json"
CONTACT_PINS = CONTACT_DIR / "source-pins.json"
CONTACT_REPLAY = CONTACT_DIR / "replay.py"
MATERIAL_INPUTS = MATERIAL_DIR / "material-inputs.json"
MATERIAL_PINS = MATERIAL_DIR / "source-pins.json"
MATERIALS_MD = MATERIAL_DIR / "materials.md"
MATERIAL_README = MATERIAL_DIR / "README.md"
MATERIAL_PRODUCER = MATERIAL_DIR / "produce.py"

BASE_INPUT_PATHS = [
    CONTACT_SCREEN,
    CONTACT_PINS,
    CONTACT_REPLAY,
    MATERIAL_INPUTS,
    MATERIAL_PINS,
    MATERIALS_MD,
    MATERIAL_README,
    MATERIAL_PRODUCER,
]

PAIRS = [
    ("post-spine", "base_post_outer_left", "knee_outer_left_spine"),
    ("spine-side", "knee_outer_left_spine", "base_side_left"),
    ("side-innerblock", "base_side_left", "knee_outer_left_inner_frame_block"),
    ("block-header", "knee_outer_left_inner_frame_block", "base_header"),
    ("header-post", "base_header", "base_post_outer_left"),
    ("header-side", "base_header", "base_side_left"),
    ("header-spine", "base_header", "knee_outer_left_spine"),
]

PSI_TO_MPA = 0.006894757293168361
CLASSIFICATION_TOLERANCE = 1e-6


class ApplicabilityError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ApplicabilityError(f"cannot read JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ApplicabilityError(message)


def vnorm(vector: list[float]) -> float:
    return math.sqrt(sum(float(x) * float(x) for x in vector))


def normalized(vector: list[float], label: str) -> list[float]:
    require(len(vector) == 3, f"{label}: expected a 3-vector")
    norm = vnorm(vector)
    require(norm > 0.0, f"{label}: zero vector")
    return [float(x) / norm for x in vector]


def freeze_sources() -> None:
    if PINS_PATH.exists():
        raise ApplicabilityError(f"refusing to replace existing source freeze: {PINS_PATH}")
    material_inputs = read_json(ROOT / MATERIAL_INPUTS)
    files: dict[str, str] = {}
    for rel in BASE_INPUT_PATHS:
        path = ROOT / rel
        require(path.is_file(), f"source missing while freezing: {rel}")
        files[str(rel)] = sha256(path)
    for item in material_inputs.get("source_pins", []):
        rel = str(item["path"])
        expected = str(item["sha256"])
        path = ROOT / rel
        require(path.is_file(), f"material source missing while freezing: {rel}")
        actual = sha256(path)
        require(actual == expected, f"material packet source pin mismatch while freezing: {rel}")
        files[rel] = actual
    pins = {
        "schema": "current_corner_timber_contact_grain_applicability_source_pins/v1",
        "contact_screen_path": str(CONTACT_SCREEN),
        "contact_source_pins_path": str(CONTACT_PINS),
        "contact_replay_path": str(CONTACT_REPLAY),
        "material_input_path": str(MATERIAL_INPUTS),
        "material_packet_source_pins_path": str(MATERIAL_PINS),
        "material_packet_producer_path": str(MATERIAL_PRODUCER),
        "material_input_source_paths": [str(item["path"]) for item in material_inputs["source_pins"]],
        "files_sha256": dict(sorted(files.items())),
        "note": "The contact screen and hardware-material packet are each replay-verified from their own pinned sources before this result is built.",
    }
    PINS_PATH.write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(files)} source files in {PINS_PATH.relative_to(ROOT)}")


def verify_packet_replay(script: Path, label: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / script), "--verify"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        tail = (result.stdout + result.stderr).strip()
        raise ApplicabilityError(f"{label} replay failed: {tail}")


def load_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    pins = read_json(PINS_PATH)
    require(pins.get("schema") == "current_corner_timber_contact_grain_applicability_source_pins/v1", "unsupported source freeze schema")
    files: dict[str, str] = pins.get("files_sha256", {})
    for rel, expected in files.items():
        path = ROOT / rel
        require(path.is_file(), f"pinned source missing: {rel}")
        actual = sha256(path)
        require(actual == expected, f"source SHA mismatch: {rel} expected {expected}, got {actual}")

    verify_packet_replay(CONTACT_REPLAY, "saved seven-pair contact screen")
    verify_packet_replay(MATERIAL_PRODUCER, "hardware-material packet")

    screen = read_json(ROOT / CONTACT_SCREEN)
    material_inputs = read_json(ROOT / MATERIAL_INPUTS)
    require(screen.get("schema") == "current_corner_timber_contact_pressure_screen/v1", "unexpected contact-screen schema")
    require(screen.get("scope", {}).get("cell_state_count") == 588, "source contact screen does not contain 588 cells")
    require(screen.get("scope", {}).get("pair_resultant_count") == 147, "source contact screen does not contain 147 signed pair resultants")
    require(material_inputs.get("schema") == "wood_joint_material_inputs/2026-09-30/v1", "unexpected material-input schema")
    require(material_inputs.get("candidate") == screen.get("candidate"), "material/contact candidate mismatch")
    require(material_inputs.get("geometry_revision") == screen.get("geometry_revision_id"), "material/contact geometry revision mismatch")
    require(material_inputs.get("conditional_DF_L_No2_base_row", {}).get("base_properties", {}).get("Fc_perpendicular") == 625, "conditional DF-L No.2 Fc perpendicular input changed")
    require(material_inputs.get("conditional_DF_L_No2_base_row", {}).get("base_properties", {}).get("units", {}).get("stress") == "psi", "unexpected material stress unit")

    declared_input_pins = {row["path"]: row["sha256"] for row in material_inputs.get("source_pins", [])}
    require(set(declared_input_pins) == set(pins["material_input_source_paths"]), "material packet source list differs from the frozen source list")
    for rel, expected in declared_input_pins.items():
        require(files.get(rel) == expected, f"material source not bound by local source freeze: {rel}")

    by_member = {row["member_id"]: row for row in material_inputs.get("members", [])}
    required_members = {member for _, a, b in PAIRS for member in (a, b)}
    require(required_members <= set(by_member), "material packet lacks a member in the seven-pair corner")
    return pins, screen, {"inputs": material_inputs, "members": by_member}


def classify(normal: list[float], grain: list[float]) -> tuple[str, float, float]:
    n = normalized(normal, "source scalar contact normal")
    g = normalized(grain, "source proposed member grain")
    cosine = min(1.0, abs(sum(a * b for a, b in zip(n, g, strict=True))))
    if cosine >= 1.0 - CLASSIFICATION_TOLERANCE:
        classification = "parallel"
    elif cosine <= CLASSIFICATION_TOLERANCE:
        classification = "perpendicular"
    else:
        classification = "oblique"
    angle = math.degrees(math.acos(cosine))
    return classification, cosine, angle


def receiver_record(member_id: str, normal: list[float], material: dict[str, Any], pressure_mpa: float, pressure_interval_mpa: list[float]) -> dict[str, Any]:
    member = material["members"][member_id]
    grain = member.get("source_proposed_longitudinal_grain_global_xyz")
    require(isinstance(grain, list), f"material map has no proposed grain vector for {member_id}")
    grain_unit = normalized(grain, f"material grain {member_id}")
    classification, cosine, angle = classify(normal, grain_unit)
    out: dict[str, Any] = {
        "receiver_member_id": member_id,
        "source_proposed_longitudinal_grain_global_xyz": [float(x) for x in grain],
        "grain_vector_status": member.get("source_map_status"),
        "conditional_material_scenario": member.get("material_scenario"),
        "conditional_stock_class": member.get("conditional_nominal_stock_class") or member.get("conditional_final_nominal_stock_class"),
        "study_only_CF_for_arithmetic": member.get("study_only_CF_for_arithmetic"),
        "stock_conformance_or_delivered_grade_observed": bool(member.get("delivered_species_grade_observed", False) or member.get("post_rip_grade_observed", False)),
        "contact_normal_absolute_cosine_to_grain": cosine,
        "contact_force_normal_to_grain_angle_degrees": angle,
        "grain_applicability": classification,
        "source_cell_average_pressure_mpa": pressure_mpa,
        "source_cell_average_pressure_rounding_interval_mpa": [float(x) for x in pressure_interval_mpa],
    }
    if classification == "perpendicular":
        fc_psi = 625.0
        fc_mpa = fc_psi * PSI_TO_MPA
        out.update({
            "comparison_status": "CONDITIONAL_FC_PERP_REFERENCE_COMPARISON_ONLY",
            "reference_property": "conditional_DF-L_No.2 Fc perpendicular to grain",
            "reference_psi": fc_psi,
            "reference_mpa_exact_unit_conversion": fc_mpa,
            "pressure_to_reference_ratio": pressure_mpa / fc_mpa,
            "pressure_interval_to_reference_ratio": [float(pressure_interval_mpa[0]) / fc_mpa, float(pressure_interval_mpa[1]) / fc_mpa],
            "adjustment_scenario": {
                "duration": "NDS §§2.3.2 and 4.3.2 exclude Fc perpendicular to grain from CD; no load-duration factor is applied",
                "service_condition": "dry; CM=1.0",
                "temperature": "normal temperature assumed; Ct=1.0",
                "treatment_or_incising": "unincised assumed; Ci=1.0",
                "size_factor": "CF does not apply to Fc perpendicular to grain",
                "ripped_block_size_factor_note": "The inner-frame block's CFstudy=1.0 is a hypothetical final-section arithmetic input only; Fc perpendicular is outside CF scope and no grade transfer or stock conformance is inferred.",
                "bearing_area_factor_Cb": "none credited",
                "conditionality": "DF-L No.2 material and proposed grain are scenarios, not delivered-stock observations",
            },
            "interpretation": "Cell-average pressure/reference ratio only; not a code pass, allowable, local peak, or complete bearing check.",
        })
    else:
        out.update({
            "comparison_status": "REFERENCE_ONLY_NO_APPLICABLE_LOCAL_MEMBER_CONTACT_METHOD_ESTABLISHED",
            "reference_property": None,
            "pressure_to_reference_ratio": None,
            "interpretation": "No parallel or oblique member-contact resistance is assigned. Dowel-fastener embedment angle/Hankinson equations are not transferred to timber-member contact by analogy.",
        })
    return out


def build_result(pins: dict[str, Any], screen: dict[str, Any], material: dict[str, Any]) -> dict[str, Any]:
    material_inputs = material["inputs"]
    member_grain = {
        member_id: normalized(
            material["members"][member_id]["source_proposed_longitudinal_grain_global_xyz"],
            f"material grain {member_id}",
        )
        for _, member_a, member_b in PAIRS
        for member_id in (member_a, member_b)
    }
    expected_pairs = {pair_id: (member_a, member_b) for pair_id, member_a, member_b in PAIRS}
    require(set(screen["scope"]["target_pair_ids"]) == set(expected_pairs), "source pair list differs from the fixed seven-interface scope")

    cell_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    receiver_class_data: dict[tuple[str, str], list[tuple[str, float, float]]] = defaultdict(list)
    state_identity_counts: Counter[tuple[str, int, str]] = Counter()
    cell_records: list[dict[str, Any]] = []
    for source_cell in screen["cell_states"]:
        pair_id = source_cell["pair_id"]
        require(pair_id in expected_pairs, f"unexpected source pair {pair_id}")
        expected_a, expected_b = expected_pairs[pair_id]
        require((source_cell["member_a"], source_cell["member_b"]) == (expected_a, expected_b), f"member ordering changed for {pair_id}")
        require(source_cell["source_first_body"] in (expected_a, expected_b), f"source normal owner not in pair {pair_id}")
        normal = source_cell["source_scalar_normal_global_xyz"]
        pressure = float(source_cell["average_cell_pressure_mpa"])
        pressure_interval = [float(x) for x in source_cell["average_cell_pressure_rounding_interval_mpa"]]
        a_result = receiver_record(expected_a, normal, material, pressure, pressure_interval)
        b_result = receiver_record(expected_b, normal, material, pressure, pressure_interval)
        for result in (a_result, b_result):
            key = (pair_id, result["receiver_member_id"])
            cell_groups[key].append(source_cell)
            receiver_class_data[key].append((result["grain_applicability"], result["contact_normal_absolute_cosine_to_grain"], result["contact_force_normal_to_grain_angle_degrees"]))
        state_identity_counts[(pair_id, int(source_cell["increment_index_zero_based"]), str(source_cell["case_id"]))] += 1
        cell_records.append({
            "source_cell_record": copy.deepcopy(source_cell),
            "receiver_applicability": {expected_a: a_result, expected_b: b_result},
        })

    require(len(cell_records) == 588, f"expected 588 copied contact cells, got {len(cell_records)}")
    require(len(cell_groups) == 14, f"expected 14 pair/receiver combinations, got {len(cell_groups)}")
    require(all(count == 4 for count in state_identity_counts.values()), "one or more pair/increment groups no longer contain four source cells")

    receiver_summaries: list[dict[str, Any]] = []
    summary_by_pair_receiver: dict[tuple[str, str], dict[str, Any]] = {}
    for pair_id, member_a, member_b in PAIRS:
        for member_id in (member_a, member_b):
            key = (pair_id, member_id)
            classes = {row[0] for row in receiver_class_data[key]}
            cosines = [row[1] for row in receiver_class_data[key]]
            angles = [row[2] for row in receiver_class_data[key]]
            require(len(classes) == 1, f"grain orientation classification varies over cells for {pair_id}/{member_id}")
            require(max(cosines) - min(cosines) <= 1e-10, f"normal/grain angle varies over cells for {pair_id}/{member_id}")
            classification = next(iter(classes))
            source_states = cell_groups[key]
            active = [row for row in source_states if row["rounded_contact_state"] == "active_resolved"]
            active_peak = max(active, key=lambda row: row["average_cell_pressure_mpa"], default=None)
            summary: dict[str, Any] = {
                "pair_id": pair_id,
                "receiver_member_id": member_id,
                "grain_applicability": classification,
                "source_cell_state_count": len(source_states),
                "active_resolved_cell_state_count": len(active),
                "open_resolved_cell_state_count": sum(row["rounded_contact_state"] == "open_resolved" for row in source_states),
                "ambiguous_cell_state_count": sum(row["rounded_contact_state"] == "ambiguous_at_rounded_contact_boundary" for row in source_states),
                "absolute_cosine_to_grain": cosines[0],
                "contact_force_normal_to_grain_angle_degrees": angles[0],
                "active_cell_average_pressure_peak_mpa": None if active_peak is None else active_peak["average_cell_pressure_mpa"],
                "active_cell_average_pressure_peak_rounding_interval_mpa": None if active_peak is None else active_peak["average_cell_pressure_rounding_interval_mpa"],
                "peak_cell_source": None if active_peak is None else {
                    "case_id": active_peak["case_id"],
                    "increment_index_zero_based": active_peak["increment_index_zero_based"],
                    "load_factor": active_peak["load_factor"],
                    "source_connection_name": active_peak["source_connection_name"],
                    "source_row_id": active_peak["source_row_id"],
                },
            }
            if classification == "perpendicular":
                fc_mpa = 625.0 * PSI_TO_MPA
                interval = active_peak["average_cell_pressure_rounding_interval_mpa"] if active_peak else [0.0, 0.0]
                peak_pressure = active_peak["average_cell_pressure_mpa"] if active_peak else 0.0
                summary.update({
                    "conditional_Fc_perpendicular_psi": 625.0,
                    "conditional_Fc_perpendicular_mpa_exact_unit_conversion": fc_mpa,
                    "peak_cell_average_to_Fc_reference_ratio": peak_pressure / fc_mpa,
                    "peak_cell_average_ratio_rounding_interval": [float(interval[0]) / fc_mpa, float(interval[1]) / fc_mpa],
                    "result_scope": "conditional cell-average pressure/reference comparison only",
                })
            else:
                summary.update({
                    "conditional_Fc_perpendicular_psi": None,
                    "peak_cell_average_to_Fc_reference_ratio": None,
                    "result_scope": "reference-only grain classification; no applicable local member-contact resistance comparison",
                })
            summary_by_pair_receiver[key] = summary
            receiver_summaries.append(summary)

    resultants: list[dict[str, Any]] = []
    require(len(screen["pair_resultants"]) == 147, "source signed wrench count changed")
    for row in screen["pair_resultants"]:
        pair_id = row["pair_id"]
        member_a, member_b = expected_pairs[pair_id]
        require((row["member_a"], row["member_b"]) == (member_a, member_b), f"source pair wrench member order changed for {pair_id}")
        enriched = copy.deepcopy(row)
        enriched["receiver_grain_applicability"] = {
            member_a: summary_by_pair_receiver[(pair_id, member_a)]["grain_applicability"],
            member_b: summary_by_pair_receiver[(pair_id, member_b)]["grain_applicability"],
        }
        resultants.append(enriched)
    require(len(resultants) == 147, f"expected 147 copied signed wrenches, got {len(resultants)}")

    class_counts = Counter(row["grain_applicability"] for row in receiver_summaries)
    by_cells = Counter()
    for row in receiver_summaries:
        by_cells[row["grain_applicability"]] += row["source_cell_state_count"]
    transverse = [row for row in receiver_summaries if row["grain_applicability"] == "perpendicular"]
    maximum_reference_ratio = max(transverse, key=lambda row: row["peak_cell_average_to_Fc_reference_ratio"])
    fc_mpa = 625.0 * PSI_TO_MPA

    return {
        "schema": "current_corner_timber_contact_grain_applicability/v1",
        "status": "SOURCE_BOUND_CONDITIONAL_GRAIN_CLASSIFICATION_AND_CELL_AVERAGE_REFERENCE_COMPARISON",
        "candidate": screen["candidate"],
        "geometry_revision_id": screen["geometry_revision_id"],
        "scope": {
            "case_ids": screen["scope"]["case_ids"],
            "pair_ids": [pair_id for pair_id, _, _ in PAIRS],
            "pair_receiver_combinations": len(receiver_summaries),
            "source_contact_cell_states": len(cell_records),
            "source_signed_pair_wrenches": len(resultants),
            "source_increments": 21,
            "material_receiver_applicability_cell_records": sum(by_cells.values()),
            "receiver_applicability_counts_by_class": dict(sorted(class_counts.items())),
            "receiver_cell_applicability_counts_by_class": dict(sorted(by_cells.items())),
            "excluded": ["new contact solve", "new contact quadrature or cells", "dowel-embedment Hankinson transfer to member contact", "cell-peak pressure", "support-area or pressure-distribution proof", "stock conformance", "complete-joint acceptance"],
        },
        "source_authentication": {
            "source_pins_path": str(PINS_PATH.relative_to(ROOT)),
            "source_pins_sha256": sha256(PINS_PATH),
            "source_files_sha256": pins["files_sha256"],
            "source_contact_screen_path": str(CONTACT_SCREEN),
            "source_contact_screen_sha256": pins["files_sha256"][str(CONTACT_SCREEN)],
            "source_material_inputs_path": str(MATERIAL_INPUTS),
            "source_material_inputs_sha256": pins["files_sha256"][str(MATERIAL_INPUTS)],
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "source_contact_replay_verified": True,
            "source_material_packet_replay_verified": True,
            "native_solver_launched_by_this_packet": False,
        },
        "method": {
            "normal_source": "source_scalar_normal_global_xyz from the authenticated SPRINGA contact-cell model; used as the modeled contact force normal, with absolute dot product so its sign does not alter grain class",
            "grain_source": "source_proposed_longitudinal_grain_global_xyz for each receiving member from the declared hardware/material packet; proposed orientation only, not inspected stock",
            "classification": "normalize normal and grain; c=abs(dot(n,g)); parallel if c>=1-1e-6, perpendicular if c<=1e-6, otherwise oblique; angle=acos(c)",
            "transverse_reference": "Only perpendicular receiver classifications are compared to conditional DF-L No.2 Fc_perpendicular=625 psi. NDS §§2.3.2 and 4.3.2 exclude deformation-limit Fc_perpendicular from CD, so no load-duration factor is applied. MPa conversion uses 1 psi=0.006894757293168361 MPa; no Cb is credited. The contact source's existing cell-average pressure and rounding interval are divided by this reference.",
            "parallel_oblique": "Reference-only. No member-contact parallel/oblique resistance method is established here. NDS dowel-fastener embedment-angle/Hankinson equations are not applied by analogy.",
            "pressure_data": "Existing compression-only SPRINGA cell-average pressure, modeled source area, state and rounding intervals are copied unchanged; no new cells or pressure distribution are computed.",
            "datum": "Source signed pair wrenches are copied unchanged from the authenticated screen at its global XYZ datum [0,0,0] mm.",
        },
        "summary": {
            "receiver_applicability_class_counts": dict(sorted(class_counts.items())),
            "receiver_cell_state_counts": dict(sorted(by_cells.items())),
            "maximum_transverse_receiver_reference_ratio": {
                "pair_id": maximum_reference_ratio["pair_id"],
                "receiver_member_id": maximum_reference_ratio["receiver_member_id"],
                "case_id": maximum_reference_ratio["peak_cell_source"]["case_id"],
                "increment_index_zero_based": maximum_reference_ratio["peak_cell_source"]["increment_index_zero_based"],
                "source_connection_name": maximum_reference_ratio["peak_cell_source"]["source_connection_name"],
                "source_row_id": maximum_reference_ratio["peak_cell_source"]["source_row_id"],
                "cell_average_pressure_mpa": maximum_reference_ratio["active_cell_average_pressure_peak_mpa"],
                "cell_average_pressure_rounding_interval_mpa": maximum_reference_ratio["active_cell_average_pressure_peak_rounding_interval_mpa"],
                "conditional_Fc_perpendicular_psi": 625.0,
                "conditional_Fc_perpendicular_mpa_exact_unit_conversion": fc_mpa,
                "pressure_to_reference_ratio": maximum_reference_ratio["peak_cell_average_to_Fc_reference_ratio"],
                "ratio_rounding_interval": maximum_reference_ratio["peak_cell_average_ratio_rounding_interval"],
                "interpretation": "Conditional cell-average pressure/reference arithmetic only; not a code pass or actual wood-stress check.",
            },
            "unknown_local_peak_pressure": True,
            "unknown_actual_contact_support_area_and_distribution": True,
            "stock_conformance_or_delivered_grain_assignment_established": False,
            "complete_joint_acceptance": False,
        },
        "interface_receiver_summaries": receiver_summaries,
        "cell_states": cell_records,
        "pair_resultants": resultants,
        "limits": [
            "Material property and grain vectors are conditional declared scenarios; no physical stock species, grade, moisture, treatment, grain orientation or conformance was observed.",
            "The 625 psi Fc-perpendicular comparison assumes the named normal-duration, dry-service, normal-temperature, unincised conditional scenario (CD=CM=Ct=Ci=1.0); CF does not apply to Fc perpendicular to grain, and no bearing-area factor Cb is credited.",
            "Ripped inner-frame block grade is not inherited from its source 4x6; its DF-L No.2 final-section property row and CFstudy=1.0 remain hypothetical arithmetic only. This screen keeps that stock/grade gap distinct from the arithmetic.",
            "Cell-average pressures are discrete spring force divided by modeled cell area. They do not establish local peak pressure, actual support area, continuous contact, pressure distribution, or resistance.",
            "Parallel and oblique receiver orientations remain reference-only because no applicable local member-contact resistance method is established. Dowel-fastener embedment/Hankinson relationships are not transferred to timber member contact by analogy.",
            "The output preserves the source three-case conditional numerical demands only; it is not a full joint evaluation, complete-joint pass, physical failure finding, or candidate acceptance.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-sources", action="store_true", help="create the initial SHA freeze after source packets are valid")
    mode.add_argument("--write", action="store_true", help="write the result from frozen source packets")
    mode.add_argument("--verify", action="store_true", help="verify pins and exact deterministic output replay")
    args = parser.parse_args()
    try:
        if args.freeze_sources:
            freeze_sources()
            return 0
        pins, screen, material = load_sources()
        expected = build_result(pins, screen, material)
        expected_bytes = json.dumps(expected, indent=2, sort_keys=True) + "\n"
        if args.write:
            OUTPUT_PATH.write_text(expected_bytes, encoding="utf-8")
            print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}: {len(expected['cell_states'])} source cells, {len(expected['pair_resultants'])} signed wrenches, {len(expected['interface_receiver_summaries'])} receiver/interface combinations")
            return 0
        existing = OUTPUT_PATH.read_text(encoding="utf-8")
        require(existing == expected_bytes, "grain-applicability.json differs from a fresh source-bound replay")
        print(f"PASS: {len(expected['cell_states'])} source cells; {len(expected['pair_resultants'])} signed wrenches; receiver classes={expected['summary']['receiver_applicability_class_counts']}")
        print("maximum transverse receiver reference ratio: " + json.dumps(expected["summary"]["maximum_transverse_receiver_reference_ratio"], sort_keys=True))
        return 0
    except (ApplicabilityError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
