"""Reproduce an explicitly conditional two-member NDS bolt screen.

This is a small, non-native mechanics calculation. It does not bind a
candidate axis, actual wood, a product, action, or acceptance criterion.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fea.dowel_yield import single_shear  # noqa: E402
from mini_moonboard.bolted_wood_wood_yield import (  # noqa: E402
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)


SCENARIO = {
    "main_length_in": 3.5,
    "side_length_in": 1.5,
    "specific_gravity": 0.50,
    "full_body_diameter_in": 0.25,
    "thread_root_diameter_in": 0.189,
    "thread_bearing_length_main_in": 0.0,
    "thread_bearing_length_side_in": 0.0,
    "bolt_bending_yield_strength_psi": 45000.0,
    "gap_in": 0.0,
}
LB_TO_N = 4.4482216152605
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reductions(main_angle: float, side_angle: float) -> dict[str, float]:
    k_theta = 1.0 + 0.25 * max(main_angle, side_angle) / 90.0
    return {
        "Im": 4.0 * k_theta,
        "Is": 4.0 * k_theta,
        "II": 3.6 * k_theta,
        "IIIm": 3.2 * k_theta,
        "IIIs": 3.2 * k_theta,
        "IV": 3.2 * k_theta,
    }


def rounded_force_values(values: dict[str, float]) -> dict[str, dict[str, float]]:
    return {
        mode: {
            "lbf": round(value, 6),
            "N": round(value * LB_TO_N, 6),
        }
        for mode, value in values.items()
    }


def tr12_example_3_1_check() -> dict:
    """Reproduce the repository's published TR12 Example 3.1 benchmark."""
    moment = 45000.0 * 0.5**3 / 6.0
    case = single_shear(
        main_length_in=1.5,
        side_length_in=1.5,
        main_bearing_lb_in=4800.0 * 0.5,
        side_bearing_lb_in=4800.0 * 0.5,
        main_yield_moment_lb_in=moment,
        side_yield_moment_lb_in=moment,
        gap_in=0.0,
        reduction_terms={
            "Im": 4.0,
            "Is": 4.0,
            "II": 3.6,
            "IIIm": 3.2,
            "IIIs": 3.2,
            "IV": 3.2,
        },
    )
    expected = {
        "Im": 900.0,
        "Is": 900.0,
        "II": 414.0,
        "IIIm": 550.0,
        "IIIs": 550.0,
        "IV": 663.0,
    }
    matches = all(
        abs(case["reference_values_lbf"][mode] - expected[mode]) <= 0.51
        for mode in MODES
    )
    if not matches or case["governing_mode"] != "II":
        raise AssertionError("TR12 Example 3.1 known-answer check failed")
    return {
        "benchmark": "AWC TR12 Example 3.1, zero-gap single shear",
        "expected_rounded_reference_values_lbf": expected,
        "calculated_reference_values_lbf": {
            mode: round(case["reference_values_lbf"][mode], 6)
            for mode in MODES
        },
        "governing_mode": case["governing_mode"],
        "matches_within_0_51_lbf": matches,
    }


def calculate_case(name: str, main_angle: float, side_angle: float) -> dict:
    d = SCENARIO["full_body_diameter_in"]
    fyb = SCENARIO["bolt_bending_yield_strength_psi"]
    moment = dowel_bending_yield_moment_lb_in(
        bending_yield_strength_psi=fyb,
        effective_diameter_in=d,
    )
    reduction = reductions(main_angle, side_angle)
    result = wood_wood_single_shear_reference(
        main_bearing_length_in=SCENARIO["main_length_in"],
        side_bearing_length_in=SCENARIO["side_length_in"],
        main_load_to_grain_degrees=main_angle,
        side_load_to_grain_degrees=side_angle,
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=d,
        bolt_thread_root_diameter_in=SCENARIO["thread_root_diameter_in"],
        main_thread_bearing_length_in=SCENARIO["thread_bearing_length_main_in"],
        side_thread_bearing_length_in=SCENARIO["thread_bearing_length_side_in"],
        bolt_bending_yield_moment_lb_in=moment,
        gap_in=SCENARIO["gap_in"],
        reduction_terms=reduction,
        bolt_bending_yield_strength_psi=fyb,
    )

    # For zero gap, Mode IV reduces to this closed form. This checks the
    # reported governing reference value against the explicit mechanics form.
    q_main = result["main_bearing_psi"] * d
    q_side = result["side_bearing_psi"] * d
    mode_iv_yield = math.sqrt(
        (2.0 * moment) / (1.0 / (2.0 * q_side) + 1.0 / (2.0 * q_main))
    )
    mode_iv_reference = mode_iv_yield / reduction["IV"]
    if not math.isclose(
        mode_iv_reference,
        result["reference_values_lbf"]["IV"],
        rel_tol=1e-12,
        abs_tol=1e-12,
    ):
        raise AssertionError(f"direct Mode IV equation mismatch for {name}")

    return {
        "case": name,
        "lateral_load_to_grain_degrees": {
            "main": main_angle,
            "side": side_angle,
        },
        "bolt_axis_perpendicular_to_grain_in_both_members": True,
        "bearing_strength_psi": {
            "main": result["main_bearing_psi"],
            "side": result["side_bearing_psi"],
        },
        "reduction_terms": reduction,
        "yield_modes": rounded_force_values(result["yield_values_lbf"]),
        "reference_modes_before_end_use_adjustments": rounded_force_values(
            result["reference_values_lbf"]
        ),
        "governing_mode": result["governing_mode"],
        "conditional_single_bolt_reference": {
            "lbf": round(result["reference_lateral_lbf"], 6),
            "N": round(result["reference_lateral_lbf"] * LB_TO_N, 6),
        },
        "direct_zero_gap_mode_iv_reference_lbf": round(mode_iv_reference, 6),
        "direct_mode_iv_matches_solver": True,
    }


def main() -> None:
    cases = [
        calculate_case("parallel_parallel", 0.0, 0.0),
        calculate_case("perpendicular_perpendicular", 90.0, 90.0),
        calculate_case("main_parallel_side_perpendicular", 0.0, 90.0),
        calculate_case("main_perpendicular_side_parallel", 90.0, 0.0),
    ]
    output = {
        "record_kind": "conditional_component_scenario",
        "scenario_id": "ordinary-two-member-1-4in-bolt-45ksi-fyb",
        "status": "illustrative_design_scenario_only",
        "scenario_inputs": {
            "geometry": {
                "main_member_bearing_length_in": SCENARIO["main_length_in"],
                "side_member_bearing_length_in": SCENARIO["side_length_in"],
                "basis": "explicit screening dimensions, 3.5 in + 1.5 in; not bound to a candidate axis",
            },
            "wood": {
                "species_group_assumption": "Douglas Fir-Larch",
                "specific_gravity_G": SCENARIO["specific_gravity"],
                "basis": "explicit dry solid-sawn scenario; not received-stock evidence",
            },
            "bolt": {
                "full_body_diameter_in": SCENARIO["full_body_diameter_in"],
                "thread_root_diameter_helper_input_in": SCENARIO["thread_root_diameter_in"],
                "thread_root_input_role": "inert helper input only; with zero thread bearing lengths, the selected effective diameter stays .25 in; this is not a product or thread-class claim",
                "thread_bearing_length_in": {
                    "main": SCENARIO["thread_bearing_length_main_in"],
                    "side": SCENARIO["thread_bearing_length_side_in"],
                },
                "effective_diameter_in": SCENARIO["full_body_diameter_in"],
                "thread_assumption": "zero thread bearing in both wood members; D=.25 in is used throughout this conditional calculation; actual thread placement is unverified",
                "Fyb_psi": SCENARIO["bolt_bending_yield_strength_psi"],
                "Fyb_basis": "explicit 45 ksi design scenario, matching the full-body-bolt Fyb stated by NDS-2024 Table 12A footnote 2; no actual SKU or delivered-part conformance inferred",
            },
            "contact_and_loading": {
                "gap_in": SCENARIO["gap_in"],
                "bolt_axis_perpendicular_to_both_member_grains": True,
                "lateral_force_perpendicular_to_bolt_axis": True,
                "angle_definition": "NDS lateral load-to-grain angle in each member, distinct from bolt-axis-to-grain orientation",
            },
        },
        "results": cases,
        "method_checks": {
            "tr12_example_3_1": tr12_example_3_1_check(),
            "mode_iv_direct_equation_checked_for_each_case": all(
                case["direct_mode_iv_matches_solver"] for case in cases
            ),
        },
        "not_included": [
            "end-grain factor Ceg and any axis-parallel-to-grain case",
            "NDS geometry factor Cdelta and end, edge, row, or spacing checks",
            "group action or load sharing; do not sum this reference across bolts",
            "same-case demand or utilization",
            "bolt tension, shear, interaction, thread stripping, nut engagement, or head/nut pull-through",
            "washer steel bending/spreading or washer-seat demand distribution",
            "member net section, splitting, row tear-out, block shear, or complete joint behavior",
            "the distinct rail-to-principal compression butt-seat path",
            "product selection, actual thread position, grip fit, or delivered material conformance",
        ],
        "method_sources": {
            "nds_2024_chapter_12": {
                "url": "https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf",
                "sha256": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
                "locators": [
                    "Table 12A footnote 2, PDF page 23: tabulated two-member bolt values use full-body bolts and Fyb=45,000 psi",
                    "§12.3.3.4, PDF page 14: qualifying end-grain main-member bearing uses Fe-perpendicular",
                    "§12.5.2.2, PDF page 22: qualifying end-grain main-member lateral Z is multiplied by Ceg=0.67",
                    "§12.3.6.2, PDF page 17: Fyb basis; §12.3.7.2, PDF page 17: limited full-body-D thread-bearing exception",
                ],
            },
            "awc_tr12_2026": {
                "url": "https://awc.org/wp-content/uploads/2026/06/TR-12_2026_formatted.V3.pdf",
                "locators": ["Table 1-1 equations; Example 3.1 known-answer benchmark"],
            },
            "awc_2024_appendix_commentary": {
                "url": "https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf",
                "sha256": "99b0a54e7133b3cf6dd156d8fe864c1717c951487bf5baa99c34da9a68a6bbb7",
                "locator": "Appendix I.4, PDF page 20; Table I1, PDF page 21; Table I1/Appendix I scope is distinct from Table 12A footnote 2",
            },
        },
        "implementation_sources": {
            "wood_wood_method": {
                "path": "mini_moonboard/bolted_wood_wood_yield.py",
                "sha256": sha256(ROOT / "mini_moonboard/bolted_wood_wood_yield.py"),
            },
            "tr12_equations": {
                "path": "fea/dowel_yield.py",
                "sha256": sha256(ROOT / "fea/dowel_yield.py"),
            },
            "dfl_bearing_strength": {
                "path": "mini_moonboard/bolted_timber_checks.py",
                "sha256": sha256(ROOT / "mini_moonboard/bolted_timber_checks.py"),
            },
        },
    }
    (HERE / "screen.json").write_text(json.dumps(output, indent=2) + "\n")
    print(HERE / "screen.json")


if __name__ == "__main__":
    main()
