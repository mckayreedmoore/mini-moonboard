#!/usr/bin/env python3
"""Replay four saved BG003 radial-proxy smooth-section stress comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
DIAG_DIR = BASE / "current-bg003-radial-clearance-diagnostic-attempt01"
DEMAND_DIR = BASE / "current-corner-complete-resistance-register-attempt01"
HARDWARE_DIR = Path("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30")

DIAGNOSTICS = DIAG_DIR / "diagnostics.json"
DIAGNOSTIC_PRODUCER = DIAG_DIR / "run_diagnostic.py"
DIAGNOSTIC_README = DIAG_DIR / "README.md"
DIAGNOSTIC_SUMS = DIAG_DIR / "SHA256SUMS"
SIGNED_DEMANDS = DEMAND_DIR / "signed-demands.json"
DEMAND_PRODUCER = DEMAND_DIR / "produce.py"
FASTENERS_MD = HARDWARE_DIR / "fasteners.md"
FASTENER_INPUTS = HARDWARE_DIR / "fastener-inputs.json"
HARDWARE_PINS = HARDWARE_DIR / "source-pins.json"
HARDWARE_PRODUCER = HARDWARE_DIR / "produce.py"
HARDWARE_README = HARDWARE_DIR / "README.md"
PINS_PATH = HERE / "source-pins.json"
OUTPUT_PATH = HERE / "steel-normal-stress.json"

AXIS_ID = "knee_outer_left_side_1"
CASE_ID = "a12-rear"
LOAD_FACTOR = 1.0
DIAMETER_MM = 6.35
TIE_FORCE_N = 95.96739
GRADE5_FY_KSI = 92.0
PSI_TO_MPA = 0.006894757293168361
EXPECTED_K_GAP = {(100.0, 0.0), (100.0, 0.575), (1000.0, 0.0), (1000.0, 0.575)}

BASE_SOURCE_PATHS = [
    DIAGNOSTICS,
    DIAGNOSTIC_PRODUCER,
    DIAGNOSTIC_README,
    DIAGNOSTIC_SUMS,
    SIGNED_DEMANDS,
    DEMAND_PRODUCER,
    FASTENERS_MD,
    FASTENER_INPUTS,
    HARDWARE_PINS,
    HARDWARE_PRODUCER,
    HARDWARE_README,
]


class ScreenError(RuntimeError):
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
        raise ScreenError(f"cannot read JSON {path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ScreenError(message)


def close(a: float, b: float, *, atol: float = 1e-10, rtol: float = 1e-12) -> bool:
    return math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol)


def norm(vector: list[float]) -> float:
    return math.sqrt(sum(float(value) * float(value) for value in vector))


def verify_subpacket(script: Path, label: str) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / script), "--verify"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ScreenError(f"{label} source replay failed: {(result.stdout + result.stderr).strip()}")


def diagnostic_checks(diag: dict[str, Any]) -> dict[str, str]:
    require(diag.get("schema") is None or isinstance(diag.get("schema"), str), "malformed saved diagnostic")
    require(diag.get("status") == "PASS_BOUNDED_RADIAL_GAP_DIAGNOSTIC_ONLY", "radial diagnostic status changed")
    require(diag.get("producer_sha256") == sha256(ROOT / DIAGNOSTIC_PRODUCER), "radial diagnostic producer SHA mismatch")
    require(diag.get("native_solve_run") is False, "radial diagnostic unexpectedly reports a native solve")
    require(diag.get("capacity_calculated") is False and diag.get("joint_accepted") is False, "radial diagnostic limits changed")
    source_case = diag.get("source_case", {})
    require(source_case.get("case_id") == CASE_ID and source_case.get("axis_id") == AXIS_ID, "radial diagnostic source case/axis changed")
    require(source_case.get("selected_increment_load_factor") == LOAD_FACTOR, "radial diagnostic is not full load")
    require(source_case.get("only_this_case_and_bolt_used") is True, "radial diagnostic no longer identifies one case and bolt")
    physical = diag.get("physical_and_conditional_parameters", {})
    require(close(physical.get("bolt_diameter_mm", math.nan), DIAMETER_MM), "radial proxy bolt diameter changed")
    require(physical.get("foundation_inputs_are_physical_calibrations_or_bounds") is False, "proxy stiffness scope changed")
    source_hashes = diag.get("source_sha256", {})
    require(isinstance(source_hashes, dict) and source_hashes, "radial diagnostic source hash map missing")
    for rel, expected in source_hashes.items():
        path = ROOT / rel
        require(path.is_file(), f"radial diagnostic pinned source missing: {rel}")
        require(sha256(path) == expected, f"radial diagnostic source SHA mismatch: {rel}")
    sum_lines = (ROOT / DIAGNOSTIC_SUMS).read_text(encoding="utf-8").splitlines()
    expected_sums: dict[str, str] = {}
    for line in sum_lines:
        digest, rel = line.split(maxsplit=1)
        expected_sums[rel.strip()] = digest
    for rel in (str(DIAGNOSTICS), str(DIAGNOSTIC_PRODUCER), str(DIAGNOSTIC_README)):
        require(expected_sums.get(rel) == sha256(ROOT / rel), f"radial diagnostic SHA256SUMS mismatch: {rel}")
    scenarios = diag.get("scenario_results", [])
    selected = [row for row in scenarios if row.get("mesh_divisions_per_receiver") == 32]
    require(len(selected) == 4, f"expected four 32-division diagnostic scenarios, got {len(selected)}")
    found = set()
    for row in selected:
        key = (float(row["k_line_N_per_mm2"]), round(float(row["gap_mm"]), 3))
        require(row.get("status") == "CONVERGED" and row.get("physical_bolt_ends_free") is True, "a selected radial proxy did not converge with free ends")
        found.add(key)
    require(found == EXPECTED_K_GAP, f"saved 32-division k/gap scenarios changed: {sorted(found)}")
    return dict(source_hashes)


def demand_checks(demands: dict[str, Any]) -> dict[str, str]:
    require(demands.get("schema") == "three_case_corner_signed_component_register/v1", "unexpected signed-demand schema")
    require(demands.get("plane_count") == 8 and demands.get("plane_state_count") == 168, "signed-demand register coverage changed")
    require(demands.get("producer_sha256") == sha256(ROOT / DEMAND_PRODUCER), "signed-demand producer SHA mismatch")
    pins = demands.get("source_pins", {})
    require(isinstance(pins, dict) and len(pins) == 3, "signed-demand source register pins changed")
    for rel, expected in pins.items():
        path = ROOT / rel
        require(path.is_file() and sha256(path) == expected, f"signed-demand source pin mismatch: {rel}")
    matches = [
        row for row in demands["rows"]
        if row.get("group") == "BG003"
        and row.get("axis_id") == AXIS_ID
        and row.get("case_id") == CASE_ID
        and close(row.get("load_factor", math.nan), LOAD_FACTOR)
    ]
    require(len(matches) == 2, f"expected both simultaneous BG003 planes at full load, got {len(matches)}")
    require({row["source_connection_name"] for row in matches} == {f"{AXIS_ID}/plane-37", f"{AXIS_ID}/plane-38"}, "expected source planes 37 and 38")
    first_tie = matches[0]["simultaneous_outer_tie"]
    require(all(row["simultaneous_outer_tie"] == first_tie for row in matches), "the two source planes do not bind the same exact outer-seat tie")
    require(all(row.get("simultaneous_tie_force_magnitude_N") == TIE_FORCE_N for row in matches), "same-state outer-seat tie magnitude changed")
    require(first_tie.get("role") == "physical_bolt_outer_seat_tension", "same-state tie is not identified as tension")
    require(first_tie.get("source_connection_name") == f"{AXIS_ID}/outer-seat-axial-tie", "physical tie source name changed")
    require(first_tie.get("first") == "knee_outer_left_spine" and first_tie.get("second") == "knee_outer_left_inner_frame_block", "physical tie receivers changed")
    force_first = [float(x) for x in first_tie["force_on_first_xyz_n"]]
    force_second = [float(x) for x in first_tie["force_on_second_xyz_n"]]
    require(close(norm(force_first), TIE_FORCE_N) and close(norm(force_second), TIE_FORCE_N), "tie vectors do not reproduce exact tension magnitude")
    require(all(close(a, -b) for a, b in zip(force_first, force_second, strict=True)), "physical tie endpoint vectors are not action/reaction")
    require(close(force_first[1], 0.0) and close(force_first[2], 0.0), "physical tie is not aligned with source bolt X axis")
    return pins


def material_checks(fastener_inputs: dict[str, Any]) -> dict[str, Any]:
    marker = "machine-test yield `Fy = 92 ksi`"
    require(marker in (ROOT / FASTENERS_MD).read_text(encoding="utf-8"), "current fasteners.md no longer states the 92 ksi machine-test yield reference")
    material = fastener_inputs.get("material_boundaries", {}).get("sae_j429_grade5_1_4_through_1_in", {})
    require(material.get("machine_test_yield_ksi_min") == GRADE5_FY_KSI, "current Grade 5 diameter-band yield input changed")
    require(material.get("source_url") == "https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j429-technical-data", "Grade 5 yield source URL changed")
    require("conditional material scenario" in material.get("interpretation", ""), "Grade 5 yield conditionality changed")
    group = next((row for row in fastener_inputs.get("catalog_candidates", []) if row.get("group") == "BG003"), None)
    require(group is not None, "current hardware packet lacks BG003 catalog disposition")
    require(group.get("bolt_lead", {}).get("part") == "HC5127", "current BG003 catalog lead changed")
    require("no exact J429" in group.get("fit_status", ""), "BG003 exact-product material gap changed")
    axis = next((row for row in fastener_inputs.get("axis_snapshots", []) if row.get("axis_id") == AXIS_ID), None)
    require(axis is not None and close(axis.get("modeled_shaft_diameter_mm", math.nan), DIAMETER_MM), "current BG003 model diameter changed")
    return {
        "property": "SAE J429 Grade 5 machine-test minimum yield stress for nominal 1/4–1 in diameters",
        "yield_ksi": GRADE5_FY_KSI,
        "source_url": material["source_url"],
        "conditional_interpretation": material["interpretation"],
        "BG003_part_specific_gap": "Ro-Brand HC5127 is a length/catalog lead; the current packet says exact J429 conformance is unestablished.",
    }


def circle_section(diameter_mm: float) -> dict[str, float]:
    radius = diameter_mm / 2.0
    area = math.pi * radius**2
    inertia = math.pi * radius**4 / 4.0
    modulus_from_inertia = inertia / radius
    modulus_formula = math.pi * diameter_mm**3 / 32.0
    require(close(modulus_from_inertia, modulus_formula, atol=1e-13), "circular section-modulus identities disagree")

    # Hand analytic biaxial flexure oracle: for a circle, sigma_b(y,z) =
    # (My*z - Mz*y)/I. A signed (3,4) Nmm pair reaches (3,4)R/5 on the
    # tensile extreme fiber, so its maximum is 5R/I = 5/Z.
    my, mz = 3.0, 4.0
    moment_norm = math.hypot(my, mz)
    y = -radius * mz / moment_norm
    z = radius * my / moment_norm
    stress_from_field = (my * z - mz * y) / inertia
    stress_from_section_modulus = moment_norm / modulus_formula
    require(close(stress_from_field, stress_from_section_modulus, atol=1e-13), "hand analytic biaxial circular flexure check failed")
    return {
        "diameter_mm": diameter_mm,
        "radius_mm": radius,
        "area_mm2": area,
        "second_moment_of_area_mm4": inertia,
        "elastic_section_modulus_mm3": modulus_formula,
        "hand_check": {
            "signed_My_Mz_Nmm": [my, mz],
            "resultant_bending_moment_Nmm": moment_norm,
            "tensile_extreme_fiber_yz_mm": [y, z],
            "stress_from_linear_field_MPa": stress_from_field,
            "stress_from_M_over_Z_MPa": stress_from_section_modulus,
            "identity_passed": True,
        },
    }


def build_result(
    pins: dict[str, Any],
    diag: dict[str, Any],
    demands: dict[str, Any],
    material_basis: dict[str, Any],
) -> dict[str, Any]:
    tie_rows = [
        row for row in demands["rows"]
        if row.get("group") == "BG003"
        and row.get("axis_id") == AXIS_ID
        and row.get("case_id") == CASE_ID
        and close(row.get("load_factor", math.nan), LOAD_FACTOR)
    ]
    tie_record = tie_rows[0]["simultaneous_outer_tie"]
    tension_n = float(tie_rows[0]["simultaneous_tie_force_magnitude_N"])
    require(tension_n == TIE_FORCE_N, "selected tension no longer matches exact source tie")
    section = circle_section(DIAMETER_MM)
    fy_mpa = GRADE5_FY_KSI * 1000.0 * PSI_TO_MPA
    axial_stress_mpa = tension_n / section["area_mm2"]
    selected = [
        row for row in diag["scenario_results"]
        if row.get("mesh_divisions_per_receiver") == 32
        and row.get("status") == "CONVERGED"
        and (float(row["k_line_N_per_mm2"]), round(float(row["gap_mm"]), 3)) in EXPECTED_K_GAP
    ]
    require(len(selected) == 4, f"expected four existing 32-division proxies, got {len(selected)}")
    selected.sort(key=lambda row: (float(row["k_line_N_per_mm2"]), float(row["gap_mm"])))
    results: list[dict[str, Any]] = []
    for scenario in selected:
        middle_pair = [float(x) for x in scenario["middle_cut_internal_couple_on_left_My_Mz_Nmm"]]
        middle_moment_norm = math.hypot(*middle_pair)
        require(close(middle_moment_norm, scenario["middle_cut_couple_magnitude_Nmm"], atol=1e-8), "signed middle-cut moment does not match its paired norm")
        peak_moment_norm = float(scenario["sampled_peak_couple_magnitude_Nmm"])
        require(peak_moment_norm >= middle_moment_norm - 1e-9, "sampled peak paired moment is below the middle-cut norm")
        middle_bending_stress_mpa = middle_moment_norm / section["elastic_section_modulus_mm3"]
        peak_bending_stress_mpa = peak_moment_norm / section["elastic_section_modulus_mm3"]
        middle_total_mpa = axial_stress_mpa + middle_bending_stress_mpa
        peak_total_mpa = axial_stress_mpa + peak_bending_stress_mpa
        results.append({
            "case_id": CASE_ID,
            "axis_id": AXIS_ID,
            "load_factor": LOAD_FACTOR,
            "diagnostic_line_foundation_k_N_per_mm2": float(scenario["k_line_N_per_mm2"]),
            "diagnostic_radial_gap_mm": float(scenario["gap_mm"]),
            "diagnostic_mesh_divisions_per_receiver": int(scenario["mesh_divisions_per_receiver"]),
            "diagnostic_source_status": scenario["status"],
            "tension_input": {
                "used_once_for_physical_bolt": True,
                "sign": "tension",
                "magnitude_n": tension_n,
                "source_tie_connection_name": tie_record["source_connection_name"],
                "source_plane_rows_confirming_same_tie": sorted(row["source_connection_name"] for row in tie_rows),
                "source_tie_role": tie_record["role"],
                "tie_force_on_first_xyz_n": tie_record["force_on_first_xyz_n"],
                "tie_force_on_second_xyz_n": tie_record["force_on_second_xyz_n"],
                "axial_tension_normal_stress_mpa": axial_stress_mpa,
            },
            "signed_middle_cut": {
                "source_signed_My_Mz_Nmm": middle_pair,
                "paired_bending_moment_norm_Nmm": middle_moment_norm,
                "bending_normal_stress_MPa": middle_bending_stress_mpa,
                "tension_plus_middle_cut_bending_stress_MPa": middle_total_mpa,
                "yield_reference_ratio": middle_total_mpa / fy_mpa,
            },
            "sampled_peak_bending": {
                "source_definition": "maximum norm of the paired signed section-couple vector sampled at radial-diagnostic mesh nodes; no plane capacities or independent plane peaks are summed",
                "paired_sampled_peak_moment_norm_Nmm": peak_moment_norm,
                "bending_normal_stress_mpa": peak_bending_stress_mpa,
                "T_over_A_plus_sampled_peak_M_over_Z_mpa": peak_total_mpa,
                "conditional_yield_reference_mpa": fy_mpa,
                "conditional_yield_reference_ratio": peak_total_mpa / fy_mpa,
                "below_conditional_smooth_shank_first_yield_reference": peak_total_mpa < fy_mpa,
            },
            "interpretation": "Conditional smooth circular-section normal stress from an elastic proxy compared with a hypothetical Grade 5 direct-yield reference only; not steel capacity or adopted mechanics.",
        })

    require({(row["diagnostic_line_foundation_k_N_per_mm2"], round(row["diagnostic_radial_gap_mm"], 3)) for row in results} == EXPECTED_K_GAP, "result set does not cover exactly the four requested scenarios")
    maximum = max(results, key=lambda row: row["sampled_peak_bending"]["conditional_yield_reference_ratio"])
    source_hashes = dict(pins["files_sha256"])
    return {
        "schema": "current_bg003_compatible_steel_normal_stress_screen/v1",
        "status": "CONDITIONAL_PROXY_NORMAL_STRESS_BELOW_ASSUMED_GRADE5_DIRECT_YIELD_REFERENCE",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "scope": {
            "case_id": CASE_ID,
            "axis_id": AXIS_ID,
            "load_factor": LOAD_FACTOR,
            "physical_bolt_tie_actions": 1,
            "source_plane_rows_checking_that_same_tie": 2,
            "radial_proxy_scenarios": 4,
            "diagnostic_mesh_divisions_per_receiver": 32,
            "excluded": ["new solves", "plane capacity sums", "shear", "torsion", "preload", "thread section", "notch or transition", "steel design capacity", "physical contact bounds", "joint acceptance"],
        },
        "source_authentication": {
            "source_pins_path": str(PINS_PATH.relative_to(ROOT)),
            "source_pins_sha256": sha256(PINS_PATH),
            "source_files_sha256": source_hashes,
            "radial_diagnostic_output_path": str(DIAGNOSTICS),
            "radial_diagnostic_output_sha256": source_hashes[str(DIAGNOSTICS)],
            "signed_demand_register_path": str(SIGNED_DEMANDS),
            "signed_demand_register_sha256": source_hashes[str(SIGNED_DEMANDS)],
            "current_hardware_fasteners_path": str(FASTENERS_MD),
            "current_hardware_fasteners_sha256": source_hashes[str(FASTENERS_MD)],
            "current_fastener_inputs_sha256": source_hashes[str(FASTENER_INPUTS)],
            "grade5_yield_source_url": material_basis["source_url"],
            "producer_path": str(Path(__file__).resolve().relative_to(ROOT)),
            "producer_sha256": sha256(Path(__file__).resolve()),
            "signed_demand_register_replay_verified": True,
            "current_hardware_material_packet_replay_verified": True,
            "radial_diagnostic_replayed_or_resolved_here": False,
            "native_solver_launched_by_this_packet": False,
        },
        "inputs": {
            "load_case_and_axis": {"case_id": CASE_ID, "axis_id": AXIS_ID, "load_factor": LOAD_FACTOR},
            "same_state_axial_tie": {
                "force_magnitude_N": tension_n,
                "tension_or_compression": "tension",
                "physical_bolt_tie_action_used_once": True,
                "source_rows": [row["source_connection_name"] for row in tie_rows],
                "both_plane_rows_contain_identical_tie_record": True,
            },
            "smooth_shank_section": section,
            "conditional_Grade5_direct_yield_reference": {
                "yield_ksi": GRADE5_FY_KSI,
                "yield_mpa_exact_unit_conversion": fy_mpa,
                "source_basis": "Current hardware/material packet: SAE J429 Grade 5 machine-test minimum yield stress for 1/4 through 1 in diameter band.",
                "conditionality": material_basis["conditional_interpretation"],
                "specific_BG003_product_gap": material_basis["BG003_part_specific_gap"],
            },
        },
        "calculation": {
            "area": "A=pi*d^2/4 for a full, smooth 6.35 mm circular section",
            "section_modulus": "Z=I/(d/2)=pi*d^3/32, with I=pi*d^4/64",
            "axial_stress": "T/A using the one positive-tension outer-seat tie; identical copies attached to two signed plane rows are deduplicated by axis/case/load factor",
            "bending_stress": "paired signed middle cut uses hypot(My,Mz); diagnostic sampled peak uses its own saved maximum norm of the paired section-couple vector; sigma_b=M/Z for isotropic circular section",
            "combined_sampled_normal_stress": "T/A + sampled_peak_pair_moment_norm/Z, the tensile extreme-fiber normal stress for this smooth circular elastic proxy under the supplied positive tie tension",
            "plane_handling": "The radial diagnostic already solves a single coupled biaxial law and returns paired signed cut moments and a paired sampled peak norm. No separate Y/Z capacity or peak stresses are summed.",
            "units": {"force": "N", "moment": "N mm", "diameter": "mm", "area": "mm^2", "section_modulus": "mm^3", "stress": "MPa"},
        },
        "summary": {
            "all_four_saved_proxies_below_conditional_smooth_shank_first_yield_reference": all(row["sampled_peak_bending"]["below_conditional_smooth_shank_first_yield_reference"] for row in results),
            "maximum_proxy_yield_reference_ratio": maximum["sampled_peak_bending"]["conditional_yield_reference_ratio"],
            "maximum_proxy_case": {key: maximum[key] for key in ("case_id", "axis_id", "load_factor", "diagnostic_line_foundation_k_N_per_mm2", "diagnostic_radial_gap_mm")},
            "maximum_proxy_sampled_peak_normal_stress_mpa": maximum["sampled_peak_bending"]["T_over_A_plus_sampled_peak_M_over_Z_mpa"],
            "maximum_yield_reference_mpa": fy_mpa,
            "interpretation": "All four saved sample-derived proxy stresses are below the explicitly conditional smooth-shank Grade 5 machine-test yield reference. This does not demonstrate actual steel stress, yield margin/capacity, delivered material conformance, or a joint pass.",
        },
        "results": results,
        "limits": [
            "The radial-clearance output is one nonlinear idealized proxy for A12 rear, BG003 bolt 1, with hypothetical line-foundation stiffness and modeled radial gap. Its mesh-sampled moment peak is not a physical bound or demonstrated continuous-section maximum.",
            "The 95.96739 N outer-seat tie is the same-state A12-rear, full-load physical bolt tie. Its repeated presence on plane 37 and plane 38 is checked and used once, with its source role explicitly identifying tension.",
            "The conditional 92 ksi Grade 5 machine-test yield reference is a material scenario, not an exact BG003 product qualification. The current packet records Ro-Brand HC5127 without exact J429 conformance evidence.",
            "The smooth circular section omits threads, runout, transitions, notches and section loss. Shear, torsion, preload, fatigue, fracture, stability, steel design resistance, interaction, and actual contact/support bounds are not evaluated.",
            "No spring stiffness or clearance scenario is selected as physical, no independent plane capacities are summed, and no joint or candidate acceptance is made.",
        ],
    }


def source_paths() -> set[str]:
    diag = read_json(ROOT / DIAGNOSTICS)
    demands = read_json(ROOT / SIGNED_DEMANDS)
    fastener_inputs = read_json(ROOT / FASTENER_INPUTS)
    hardware_pins = read_json(ROOT / HARDWARE_PINS)
    paths = {str(path) for path in BASE_SOURCE_PATHS}
    paths.update(diag.get("source_sha256", {}).keys())
    paths.update(demands.get("source_pins", {}).keys())
    paths.update(row["path"] for row in hardware_pins.get("inputs", []))
    paths.update(
        str(HARDWARE_DIR / row["file"])
        for row in fastener_inputs.get("local_source_cache", [])
    )
    return paths


def verify_source_packets() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    diag = read_json(ROOT / DIAGNOSTICS)
    demands = read_json(ROOT / SIGNED_DEMANDS)
    fastener_inputs = read_json(ROOT / FASTENER_INPUTS)
    diagnostic_checks(diag)
    demand_checks(demands)
    material_basis = material_checks(fastener_inputs)
    # This producer is read-only with respect to all upstream packets. The
    # signed demand and material specification replays do not launch solvers.
    verify_subpacket(DEMAND_PRODUCER, "signed-demand register")
    verify_subpacket(HARDWARE_PRODUCER, "current hardware/material packet")
    return diag, demands, {"inputs": fastener_inputs, "basis": material_basis}


def freeze_sources() -> None:
    if PINS_PATH.exists():
        raise ScreenError(f"refusing to replace existing source freeze: {PINS_PATH}")
    diag, demands, material = verify_source_packets()
    paths = source_paths()
    files: dict[str, str] = {}
    for rel in sorted(paths):
        path = ROOT / rel
        require(path.is_file(), f"source missing while freezing: {rel}")
        files[rel] = sha256(path)
    pins = {
        "schema": "current_bg003_compatible_steel_normal_stress_source_pins/v1",
        "radial_diagnostic_path": str(DIAGNOSTICS),
        "signed_demands_path": str(SIGNED_DEMANDS),
        "current_hardware_fasteners_path": str(FASTENERS_MD),
        "transitive_hardware_and_case_source_count": len(files),
        "files_sha256": files,
        "note": "The saved radial diagnostic is hash/source-chain checked but not re-solved here. Signed-demand and current hardware/material packets are exact-replay verified read-only.",
    }
    PINS_PATH.write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"froze {len(files)} upstream source files in {PINS_PATH.relative_to(ROOT)}")


def load_pinned_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    pins = read_json(PINS_PATH)
    require(pins.get("schema") == "current_bg003_compatible_steel_normal_stress_source_pins/v1", "unsupported source-pin schema")
    files: dict[str, str] = pins.get("files_sha256", {})
    require(pins.get("transitive_hardware_and_case_source_count") == len(files), "source file count differs from manifest")
    for rel, expected in files.items():
        path = ROOT / rel
        require(path.is_file(), f"pinned source missing: {rel}")
        actual = sha256(path)
        require(actual == expected, f"source SHA mismatch: {rel} expected {expected}, got {actual}")
    require(set(source_paths()) == set(files), "the transitive source file set changed")
    diag, demands, material = verify_source_packets()
    require(diag["source_case"]["axis_id"] == AXIS_ID, "radial diagnostic axis changed")
    return pins, diag, demands, material


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--freeze-sources", action="store_true", help="create source SHA freeze after upstream validation")
    mode.add_argument("--write", action="store_true", help="write steel-normal-stress.json from frozen sources")
    mode.add_argument("--verify", action="store_true", help="verify frozen sources and exact replay without writing")
    args = parser.parse_args()
    try:
        if args.freeze_sources:
            freeze_sources()
            return 0
        pins, diag, demands, material = load_pinned_sources()
        result = build_result(pins, diag, demands, material["basis"])
        encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
        if args.write:
            OUTPUT_PATH.write_text(encoded, encoding="utf-8")
            print(f"wrote {OUTPUT_PATH.relative_to(ROOT)}: {len(result['results'])} source-bound scenarios")
            return 0
        existing = OUTPUT_PATH.read_text(encoding="utf-8")
        require(existing == encoded, "steel-normal-stress.json differs from exact source replay")
        print(f"PASS: {len(result['results'])} saved scenarios; maximum conditional yield-reference ratio={result['summary']['maximum_proxy_yield_reference_ratio']:.12f}")
        return 0
    except (ScreenError, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
