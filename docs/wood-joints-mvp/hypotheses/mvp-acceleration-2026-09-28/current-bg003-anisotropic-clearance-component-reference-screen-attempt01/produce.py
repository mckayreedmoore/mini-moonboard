#!/usr/bin/env python3
"""Reproduce conditional BG003 local bearing and smooth-bolt stress references."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
ROOT = next(parent for parent in HERE.parents if (parent / "AGENTS.md").is_file())
BASE = Path("docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28")
FINITE = BASE / "current-bg003-anisotropic-clearance-finite-adapter-attempt01/finite-proxy-results.json"
DEMANDS = BASE / "current-corner-complete-resistance-register-attempt01/signed-demands.json"
STEEL_REFERENCE = BASE / "current-bg003-compatible-steel-normal-stress-screen-attempt01/steel-normal-stress.json"
MATERIALS = Path("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json")
FASTENERS = Path("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fastener-inputs.json")
PINS = HERE / "source-pins.json"
OUTPUT = HERE / "component-reference-screen.json"

PSI_TO_MPA = 0.006894757293168361
EXPECTED_SCENARIOS = {
    (350.0, 0.0, 16), (350.0, 0.0, 32),
    (350.0, 0.575, 16), (350.0, 0.575, 32),
    (550.0, 0.0, 16), (550.0, 0.0, 32),
    (550.0, 0.575, 16), (550.0, 0.575, 32),
}
EXPECTED_RECEIVERS = {
    "knee_outer_left_spine",
    "base_side_left",
    "knee_outer_left_inner_frame_block",
}


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


def close(a: float, b: float, *, atol: float = 1e-9, rtol: float = 1e-10) -> bool:
    return math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol)


def norm2(vector: list[float]) -> float:
    return math.hypot(float(vector[0]), float(vector[1]))


def verify_source_pins() -> dict[str, str]:
    manifest = read_json(PINS)
    require(manifest.get("schema") == "current_bg003_component_reference_source_pins/v1", "unexpected pin manifest schema")
    expected = manifest.get("files_sha256")
    require(isinstance(expected, dict) and expected, "empty source pin list")
    for relative, wanted in expected.items():
        path = ROOT / relative
        require(path.is_file(), f"pinned source missing: {relative}")
        actual = sha256(path)
        require(actual == wanted, f"source hash mismatch for {relative}: {actual} != {wanted}")

    finite = read_json(ROOT / FINITE)
    transitive = finite.get("source_sha256")
    require(isinstance(transitive, dict) and transitive, "finite result has no source hash chain")
    for relative, wanted in transitive.items():
        path = ROOT / relative
        require(path.is_file() and sha256(path) == wanted, f"finite proxy transitive source mismatch: {relative}")
    return expected


def acute_axis_angle_deg(force_yz: list[float], grain_angle_deg: float) -> float:
    force_norm = norm2(force_yz)
    require(force_norm > 0.0, "zero sampled bearing force cannot define a load angle")
    a = math.radians(grain_angle_deg)
    grain_yz = [math.sin(a), math.cos(a)]
    cosine = abs((float(force_yz[0]) * grain_yz[0] + float(force_yz[1]) * grain_yz[1]) / force_norm)
    cosine = max(0.0, min(1.0, cosine))
    return math.degrees(math.acos(cosine))


def build_result(source_hashes: dict[str, str]) -> dict[str, Any]:
    finite = read_json(ROOT / FINITE)
    demands = read_json(ROOT / DEMANDS)
    steel_basis = read_json(ROOT / STEEL_REFERENCE)
    materials = read_json(ROOT / MATERIALS)
    fasteners = read_json(ROOT / FASTENERS)

    require(finite.get("schema") == "bg003_anisotropic_clearance_finite_proxy_results/v1", "unexpected finite-proxy schema")
    require(finite.get("status") == "PASS_BOUNDED_PROXY_ONLY", "finite proxy status changed")
    require(finite.get("scenario_count") == 8 and len(finite.get("scenarios", [])) == 8, "expected the saved eight finite proxy scenarios")
    require(finite.get("joint_accepted") is False and finite.get("native_solve_executed") is False, "finite proxy scope flags changed")
    require(finite.get("adapter_sha256") == sha256(ROOT / (BASE / "current-bg003-anisotropic-clearance-finite-adapter-attempt01/run_adapter.py")), "finite adapter hash in result changed")
    require(all(row.get("status") == "CONVERGED" for row in finite["scenarios"]), "a saved finite proxy is not converged")
    require(all(row.get("source_lateral_wrenches_applied_once_at_receivers") is True for row in finite["scenarios"]), "source receiver actions are not applied once")
    require(all(row.get("physical_bolt_ends_free") is True for row in finite["scenarios"]), "physical bolt-end conditions changed")

    scenario_keys = {
        (float(row["density_kg_per_m3_non_adopted"]), float(row["gap_mm"]), int(row["mesh_divisions_per_receiver"]))
        for row in finite["scenarios"]
    }
    require(scenario_keys == EXPECTED_SCENARIOS, f"finite scenario grid changed: {sorted(scenario_keys)}")

    dowel = materials.get("dowel_bearing_scenario", {})
    require(dowel.get("scope", "").startswith("Solid-sawn wood members at current BG001/BG003/BG045"), "conditional dowel method scope changed")
    wood_hardware = dowel.get("conditional_hardware_scenario", {})
    d_in = float(wood_hardware.get("D_in", math.nan))
    diameter_mm = float(wood_hardware.get("D_mm", math.nan))
    g = float(dowel.get("G", math.nan))
    require(close(d_in, 0.25) and close(diameter_mm, 6.35) and close(g, 0.50), "conditional NDS wood/fastener scenario changed")
    formulas = dowel.get("formulas", {}).get("D_greater_equal_0_25_in", {})
    require(formulas.get("Fe_parallel_psi") == "11200 * G", "parallel Fe equation changed")
    require(formulas.get("Fe_perpendicular_psi") == "6100 * G^1.45 / sqrt(D_in)", "perpendicular Fe equation changed")
    require("Fe_theta_psi" in dowel.get("formulas", {}).get("angle_to_grain", {}), "NDS angle equation missing")
    fe_parallel_psi = 11200.0 * g
    fe_perpendicular_psi = 6100.0 * g**1.45 / math.sqrt(d_in)
    require(close(fe_parallel_psi, float(wood_hardware["Fe_parallel_psi"])), "parallel Fe calculation differs from pinned material input")
    require(close(fe_perpendicular_psi, float(wood_hardware["Fe_perpendicular_formula_unrounded_psi"]), atol=0.001), "perpendicular Fe calculation differs from pinned material input")

    members = {row["member_id"]: row for row in materials.get("primary_corner_members", {}).get("BG003", [])}
    require(set(members) == EXPECTED_RECEIVERS, "BG003 conditional member map changed")
    for name, member in members.items():
        grain_xyz = member["proposed_grain_global_xyz"]
        require(close(math.hypot(float(grain_xyz[1]), float(grain_xyz[2])), 1.0, atol=1e-8), f"grain direction is not unit length for {name}")

    require(demands.get("schema") == "three_case_corner_signed_component_register/v1", "signed demand register schema changed")
    axis = "knee_outer_left_side_1"
    case = "a12-rear"
    tie_rows = [row for row in demands["rows"] if row.get("group") == "BG003" and row.get("axis_id") == axis and row.get("case_id") == case and float(row.get("load_factor", -1.0)) == 1.0]
    require(len(tie_rows) == 2, "expected both simultaneous A12 BG003 plane rows")
    tie = tie_rows[0]["simultaneous_outer_tie"]
    require(all(row.get("simultaneous_outer_tie") == tie for row in tie_rows), "A12 lateral planes no longer share one exact tie record")
    require(tie.get("role") == "physical_bolt_outer_seat_tension", "same-state tie is not tension")
    tie_force = float(tie_rows[0]["simultaneous_tie_force_magnitude_N"])
    force_first = tie["force_on_first_xyz_n"]
    force_second = tie["force_on_second_xyz_n"]
    require(close(tie_force, 95.96739) and close(math.sqrt(sum(float(x) ** 2 for x in force_first)), tie_force), "A12 tie magnitude changed")
    require(all(close(float(a), -float(b)) for a, b in zip(force_first, force_second, strict=True)), "A12 tie actions are not equal and opposite")
    require(float(force_first[0]) > 0 and close(float(force_first[1]), 0.0) and close(float(force_first[2]), 0.0), "A12 tie source sign/direction changed")
    require(tie.get("source_connection_name") == f"{axis}/outer-seat-axial-tie", "unexpected source tie connection")

    steel_inputs = steel_basis.get("inputs", {})
    section_input = steel_inputs.get("smooth_shank_section", {})
    diameter_steel_mm = float(section_input.get("diameter_mm", math.nan))
    yield_data = steel_inputs.get("conditional_Grade5_direct_yield_reference", {})
    yield_mpa = float(yield_data.get("yield_mpa_exact_unit_conversion", math.nan))
    yield_ksi = float(yield_data.get("yield_ksi", math.nan))
    require(close(diameter_steel_mm, diameter_mm) and close(yield_ksi, 92.0), "selected steel smooth-section/reference scenario changed")
    expected_yield_mpa = yield_ksi * 1000.0 * PSI_TO_MPA
    require(close(yield_mpa, expected_yield_mpa, atol=1e-8), "Grade 5 reference conversion changed")
    fastener_record = fasteners.get("material_boundaries", {}).get("sae_j429_grade5_1_4_through_1_in", {})
    require(close(float(fastener_record.get("machine_test_yield_ksi_min", math.nan)), yield_ksi), "current fastener material source disagrees on yield reference")
    require("machine-test yield `Fy = 92 ksi`" in (ROOT / Path("docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fasteners.md")).read_text(encoding="utf-8"), "fastener source text no longer states the selected yield reference")
    require("no exact J429" in next(row for row in fasteners["catalog_candidates"] if row.get("group") == "BG003").get("fit_status", ""), "BG003 product-specific qualification gap changed")

    area_mm2 = math.pi * diameter_mm**2 / 4.0
    section_modulus_mm3 = math.pi * diameter_mm**3 / 32.0
    axial_stress_mpa = tie_force / area_mm2
    scenario_results: list[dict[str, Any]] = []
    for scenario in sorted(finite["scenarios"], key=lambda row: (float(row["density_kg_per_m3_non_adopted"]), float(row["gap_mm"]), int(row["mesh_divisions_per_receiver"]))):
        pressures = scenario.get("sampled_line_bearing_resultant_pressure_by_receiver", {})
        require(set(pressures) == EXPECTED_RECEIVERS, "sampled pressure receiver set changed")
        bearing_rows: list[dict[str, Any]] = []
        for receiver in sorted(EXPECTED_RECEIVERS):
            sample = pressures[receiver]
            force_yz = [float(x) for x in sample["line_resultant_YZ_N_per_mm"]]
            pressure_yz = [float(x) for x in sample["signed_p_over_d_YZ_MPa"]]
            pressure = norm2(force_yz) / diameter_mm
            require(close(pressure, float(sample["sampled_p_over_d_resultant_MPa"])), f"p/d resultant mismatch for {receiver}")
            expected_vector = [x / diameter_mm for x in force_yz]
            require(all(close(a, b) for a, b in zip(expected_vector, pressure_yz, strict=True)), f"signed p/d vector mismatch for {receiver}")

            grain_xyz = members[receiver]["proposed_grain_global_xyz"]
            grain_angle = math.degrees(math.atan2(float(grain_xyz[1]), float(grain_xyz[2])))
            require(close(grain_angle, float(sample["grain_angle_from_global_positive_Z_toward_positive_Y_deg"])), f"grain angle does not match material map for {receiver}")
            theta = acute_axis_angle_deg(force_yz, grain_angle)
            source_theta = abs((float(sample["signed_force_to_parallel_grain_angle_deg"]) + 90.0) % 180.0 - 90.0)
            require(close(theta, source_theta, atol=1e-7), f"force/grain angle mismatch for {receiver}")
            theta_rad = math.radians(theta)
            fe_theta_psi = (fe_parallel_psi * fe_perpendicular_psi) / (
                fe_parallel_psi * math.sin(theta_rad) ** 2
                + fe_perpendicular_psi * math.cos(theta_rad) ** 2
            )
            fe_theta_mpa = fe_theta_psi * PSI_TO_MPA
            bearing_rows.append({
                "receiver_member": receiver,
                "conditional_member_case": members[receiver].get("material_case", "conditional_DF-L_No.2"),
                "sample_location_x_mm_from_underhead": float(sample["x_mm_from_underhead"]),
                "signed_line_resultant_YZ_N_per_mm": force_yz,
                "signed_sampled_p_over_d_YZ_MPa": pressure_yz,
                "sampled_p_over_d_resultant_MPa": pressure,
                "proposed_grain_angle_from_global_positive_Z_toward_positive_Y_deg": grain_angle,
                "force_to_undirected_grain_axis_acute_angle_deg": theta,
                "conditional_NDS_2024_dowel_bearing_reference": {
                    "G": g,
                    "D_in": d_in,
                    "Fe_parallel_psi_unrounded": fe_parallel_psi,
                    "Fe_perpendicular_psi_unrounded": fe_perpendicular_psi,
                    "Fe_theta_psi_unrounded": fe_theta_psi,
                    "Fe_theta_MPa_unrounded": fe_theta_mpa,
                    "sampled_pressure_over_Fe_theta_reference": pressure / fe_theta_mpa,
                },
                "interpretation": "single saved maximum-sampled resultant p/d point compared with conditional unadjusted NDS Fe_theta; this is not an NDS design DCR or resistance check",
            })

        peak = scenario["sampled_peak_couple"]
        peak_pair = [float(x) for x in peak["signed_internal_couple_on_left_My_Mz_Nmm"]]
        peak_moment = math.hypot(*peak_pair)
        require(close(peak_moment, float(peak["magnitude_Nmm"])), "sampled peak signed couple does not match paired norm")
        middle_pair = [float(x) for x in scenario["middle_cut_internal_couple_on_left_My_Mz_Nmm"]]
        middle_moment = math.hypot(*middle_pair)

        def section_stress(pair: list[float], moment_norm: float) -> dict[str, Any]:
            bending = moment_norm / section_modulus_mm3
            sigma_plus = axial_stress_mpa + bending
            sigma_minus = axial_stress_mpa - bending
            return {
                "signed_My_Mz_on_left_Nmm": pair,
                "paired_moment_norm_Nmm": moment_norm,
                "axial_tension_stress_MPa": axial_stress_mpa,
                "bending_extreme_stress_magnitude_MPa": bending,
                "signed_outer_fiber_normal_stresses_MPa": {
                    "positive_bending_extreme_tension": sigma_plus,
                    "opposite_bending_extreme": sigma_minus,
                },
                "maximum_absolute_normal_stress_MPa": max(abs(sigma_plus), abs(sigma_minus)),
                "ratio_to_conditional_Grade5_92ksi_direct_yield_reference": max(abs(sigma_plus), abs(sigma_minus)) / yield_mpa,
            }

        scenario_results.append({
            "case_id": "a12-rear",
            "axis_id": "knee_outer_left_side_1",
            "load_factor": 1.0,
            "density_kg_per_m3_non_adopted_hypothesis": float(scenario["density_kg_per_m3_non_adopted"]),
            "modeled_radial_gap_mm_hypothesis": float(scenario["gap_mm"]),
            "mesh_divisions_per_receiver": int(scenario["mesh_divisions_per_receiver"]),
            "finite_proxy_status": scenario["status"],
            "wood_sampled_pressure_reference_comparisons": bearing_rows,
            "same_state_bolt_normal_stress_reference": {
                "physical_tie_tension_N_used_once": tie_force,
                "source_tie_connection": tie["source_connection_name"],
                "circular_smooth_diameter_mm_hypothesis": diameter_mm,
                "area_mm2": area_mm2,
                "elastic_section_modulus_mm3": section_modulus_mm3,
                "conditional_yield_reference_MPa": yield_mpa,
                "selected_material_interpretation": yield_data.get("conditionality"),
                "signed_middle_cut_stress": section_stress(middle_pair, middle_moment),
                "sampled_peak_stress": {
                    **section_stress(peak_pair, peak_moment),
                    "sample_x_mm_from_underhead": float(peak["x_mm_from_underhead"]),
                    "sampling_definition": peak.get("sampling"),
                },
                "interpretation": "signed outer-fiber normal stresses from one axial-tension action plus the paired signed bending moment, compared with hypothetical smooth-section Grade 5 direct-yield reference only",
            },
        })

    return {
        "schema": "current_bg003_anisotropic_clearance_component_reference_screen/v1",
        "status": "CONDITIONAL_COMPONENT_REFERENCE_COMPARISONS_ONLY",
        "source_sha256": source_hashes,
        "source_case": {
            "case_id": "a12-rear",
            "axis_id": "knee_outer_left_side_1",
            "load_factor": 1.0,
            "finite_proxy_scenario_count": 8,
            "finite_proxy_status": finite["status"],
            "same_state_plane_rows": sorted(row["source_connection_name"] for row in tie_rows),
            "same_state_physical_tie_tension_N": tie_force,
            "physical_tie_used_once": True,
        },
        "wood_reference_method": {
            "primary_source": "AWC NDS-2024 Chapter 12 §12.3.3, Table 12.3.3, and §12.3.4 Eq. 12.3-11; pinned source PDF",
            "conditional_material": "DF-L No. 2, G=0.50; the inner block is an explicit hypothetical final-section No. 2 / CFstudy=1.0 scenario; no delivered stock grade/species is asserted",
            "fastener": "smooth/full-body D=0.25 in.=6.35 mm scenario; actual thread/reduced-body bearing diameter is unverified",
            "demand_definition": "saved maximum-sampled receiver line-force resultant divided by modeled bolt diameter; N/mm divided by mm gives MPa over projected bore width",
            "angle_definition": "acute angle between the saved local signed force vector and proposed undirected longitudinal grain axis, computed from the returned force vector",
            "Fe_parallel_psi_unrounded": fe_parallel_psi,
            "Fe_perpendicular_psi_unrounded": fe_perpendicular_psi,
            "no_Fc_perpendicular_comparison": True,
        },
        "steel_reference_method": {
            "conditional_reference": "SAE J429 Grade 5 92 ksi machine-test minimum yield for nominal 1/4–1 in diameter band; 634.3176709714892 MPa",
            "section": "full smooth circular 6.35 mm section; A=pi*d^2/4 and Z=pi*d^3/32",
            "stress": "same-state tie tension/A plus or minus the magnitude of the saved paired signed bending couple/Z; both signed outer-fiber stresses are retained",
            "product_gap": "BG003 Ro-Brand HC5127 remains a catalog/length lead; exact J429 conformance is not established",
        },
        "limits": [
            "The directional foundations and radial clearance are uncalibrated constitutive hypotheses, not measured properties or physical bounds.",
            "Only the saved maximum-sampled p/d point per receiver is compared. It is a nominal projected-bore average from a line resultant, not a resolved circumferential contact-pressure field. Pressure samples are not continuous extrema; previous 16/32 pressure differences include 4.27% for the inner block and 1.05% for the side in the 550 kg/m3, 0.575 mm case.",
            "Fe_theta comparisons are local conditional stress/reference ratios, not NDS design DCRs, lateral-yield capacities, member capacities, or joint checks; no pressure distribution integration or shared-receiver/group method is supplied.",
            "The coupled Y/Z receiver action remains one vector; no independent plane capacities or resistances are combined.",
            "The smooth-shank stress excludes threads, reduced roots, runout, transitions, shear, torsion, preload, fatigue, fracture, and steel interaction. The 92 ksi reference is not a qualification of a delivered BG003 bolt.",
            "No splitting, net-section, row-tear-out, axial-tie/washer resistance, Fc-perpendicular gross-contact, friction, or complete-joint check is performed. No physical acceptance is claimed.",
        ],
        "results": scenario_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write only component-reference-screen.json")
    mode.add_argument("--verify", action="store_true", help="recompute and compare without writing")
    args = parser.parse_args()
    try:
        source_hashes = verify_source_pins()
        result = build_result(source_hashes)
        expected_bytes = (json.dumps(result, indent=2, sort_keys=True) + "\n").encode("utf-8")
        if args.write:
            OUTPUT.write_bytes(expected_bytes)
            print(f"wrote {OUTPUT.relative_to(ROOT)}")
            return 0
        require(OUTPUT.is_file(), f"saved output missing: {OUTPUT}")
        actual_bytes = OUTPUT.read_bytes()
        require(actual_bytes == expected_bytes, "saved component-reference-screen.json differs from pinned replay")
        print("PASS: 8 scenario records, 24 receiver sample/reference rows, 8 paired signed stress rows")
        return 0
    except (ScreenError, KeyError, TypeError, ValueError, OverflowError) as exc:
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
