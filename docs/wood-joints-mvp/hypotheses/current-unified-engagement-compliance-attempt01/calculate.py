"""Reproduce a conditional Unified 1/4-20 engagement compliance/slack screen.

This standalone calculation reads only immutable, source-pinned local inputs.
It does not emit or modify any finite-element input.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

SOURCE_PINS = {
    "docs/wood-joints-mvp/current-engagement-evidence-routes.md": "76438bd59d07105a4dbd4553ca0cb95fa1de828552adc9815e71fad9233f50bb",
    "docs/wood-joints-mvp/current-engagement-analytical-proposal.md": "ed71af102b1e8987d71597f72c9a8f7f756e45335e21a9e23d2ee234253b0d9b",
    "docs/wood-joints-mvp/current-thread-fit-travel.md": "4046318d1fac274bc3a2bb654921d3eaa4bce9c33e2cc2c391b8b83f4ac8d50d",
    "docs/wood-joints-mvp/current-ordinary-hardware-basis.md": "72ffabef1e449234622f4682eaefcde787abc1b56fbe8814b1e843d1581d1ecc",
    "docs/wood-joints-mvp/steel-elastic-material-scenario.md": "e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3",
    "docs/wood-joints-mvp/thread-engagement-method.md": "66e899d5e090d11124b011ba150e559f1addebdb55a4aae90e7ece89d4c53503",
    "docs/wood-joints-mvp/hypotheses/current-engagement-analytical-attempt01/calculation.json": "80f73199d77e7d6147d6e4d8a74018c151a45a89070882c6c888a5440d0b44eb",
    "docs/wood-joints-mvp/hypotheses/thread-fit-travel-attempt01/calculation.json": "206ff1dae7d83b739d5af909e27309b2d8e2f1dda399c190f07a4def9898c43b",
}

MM_PER_IN = 25.4


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _read_pinned_json(root: Path, relative_path: str) -> dict[str, Any]:
    path = root / relative_path
    expected = SOURCE_PINS[relative_path]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(
            f"source drift for {relative_path}: expected {expected}, got {actual}"
        )
    return json.loads(path.read_text())


def _verify_document_pins(root: Path) -> list[dict[str, str]]:
    pins: list[dict[str, str]] = []
    for relative_path, expected in SOURCE_PINS.items():
        path = root / relative_path
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(
                f"source drift for {relative_path}: expected {expected}, got {actual}"
            )
        pins.append({"path": relative_path, "sha256": actual})
    return pins


def build_calculation(root: Path | None = None) -> dict[str, Any]:
    """Calculate the pinned nominal tangent and ideal fixed-rotation slack."""
    source_root = root or _repo_root()
    pins = _verify_document_pins(source_root)
    tangent = _read_pinned_json(
        source_root,
        "docs/wood-joints-mvp/hypotheses/current-engagement-analytical-attempt01/calculation.json",
    )
    fit = _read_pinned_json(
        source_root,
        "docs/wood-joints-mvp/hypotheses/thread-fit-travel-attempt01/calculation.json",
    )

    model = tangent["model"]
    inputs = tangent["inputs"]
    if model["equation"] != "K_th = A_s * E_b / L_th":
        raise ValueError("unexpected source tangent equation")
    if model["area_equation_inch_units"] != ("A_s = 0.7854 * (D - 0.9743/n)^2 in^2"):
        raise ValueError("unexpected source stress-area equation")
    if fit["hypothetical_pair"]["designation"] != "1/4-20 UNC":
        raise ValueError("unexpected thread-fit source designation")
    if (
        fit["hypothetical_pair"]["external_class"],
        fit["hypothetical_pair"]["internal_class"],
    ) != ("2A", "2B"):
        raise ValueError("unexpected thread-fit class pair")

    diameter_in = float(inputs["D_in"])
    threads_per_in = float(inputs["n_per_in"])
    elastic_modulus_mpa = float(inputs["reference_E_MPa"])
    equivalent_length_ratio = float(model["equivalent_length_ratio"])
    area_in2 = 0.7854 * (diameter_in - 0.9743 / threads_per_in) ** 2
    area_mm2 = area_in2 * MM_PER_IN**2
    diameter_mm = diameter_in * MM_PER_IN
    equivalent_length_mm = equivalent_length_ratio * diameter_mm
    stiffness_n_per_mm = area_mm2 * elastic_modulus_mpa / equivalent_length_mm
    compliance_mm_per_n = 1.0 / stiffness_n_per_mm

    # Reconcile the independent calculation to the frozen predecessor record.
    if not math.isclose(area_mm2, inputs["area_mm2"], rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("recomputed Unified tensile stress area does not match source")
    if not math.isclose(
        equivalent_length_mm, inputs["L_th_mm"], rel_tol=0.0, abs_tol=1e-10
    ):
        raise ValueError("recomputed equivalent thread length does not match source")
    expected_reference = next(
        row for row in tangent["outputs"] if row["E_MPa"] == elastic_modulus_mpa
    )
    if not math.isclose(
        stiffness_n_per_mm,
        expected_reference["K_N_per_mm"],
        rel_tol=1e-12,
        abs_tol=1e-7,
    ):
        raise ValueError("recomputed tangent does not match source reference result")

    limits = fit["reference_limits_in"]
    external_min = float(limits["external_2a_pitch_diameter_min"])
    external_max = float(limits["external_2a_pitch_diameter_max"])
    internal_min = float(limits["internal_2b_pitch_diameter_min"])
    internal_max = float(limits["internal_2b_pitch_diameter_max"])
    functional_factor = float(
        fit["conversion"]["unified_60deg_functional_diameter_factor"]
    )
    clearance_min_in = internal_min - external_max
    clearance_max_in = internal_max - external_min
    if clearance_min_in < 0.0 or clearance_max_in < clearance_min_in:
        raise ValueError("invalid source pitch-diameter clearance limits")
    reversal_min_mm = clearance_min_in / functional_factor * MM_PER_IN
    reversal_max_mm = clearance_max_in / functional_factor * MM_PER_IN

    return {
        "artifact_id": "current_unified_engagement_compliance_attempt01",
        "prepared_date": "2026-09-25",
        "status": "conditional_nominal_tangent_plus_historical_class_fit_comparator",
        "scope": {
            "thread_hypothesis": "1/4-20 UNC, external 2A / internal 2B",
            "applies_to_delivered_hardware": False,
            "transfers_to_wj24_provisional_axes": False,
            "physical_axial_engagement_resolved": False,
            "capacity_or_resistance_calculated": False,
            "preload_assumed": False,
        },
        "source_pins": pins,
        "post_seating_tangent": {
            "model": "K_th = A_s * E_b / L_th; L_th = 0.85*d",
            "basis": "Matsubara and Teranishi (2022), Eqs. (5) and (9), with the nominal Unified tensile-stress-area equation from NBS Handbook 28 Supplement (1963) substituted for their JIS B1082 area input.",
            "nominal_diameter_mm": diameter_mm,
            "threads_per_in": threads_per_in,
            "pitch_mm": MM_PER_IN / threads_per_in,
            "tensile_stress_area_in2": area_in2,
            "tensile_stress_area_mm2": area_mm2,
            "equivalent_thread_length_ratio": equivalent_length_ratio,
            "equivalent_thread_length_mm": equivalent_length_mm,
            "generic_reference_E_MPa": elastic_modulus_mpa,
            "stiffness_N_per_mm": stiffness_n_per_mm,
            "stiffness_kN_per_mm": stiffness_n_per_mm / 1000.0,
            "compliance_mm_per_N": compliance_mm_per_n,
            "compliance_mm_per_kN": compliance_mm_per_n * 1000.0,
            "extension_at_1kN_mm": compliance_mm_per_n * 1000.0,
            "meaning": "One post-seating equivalent thread-engagement tangent component only. L_th is an elastic equivalent length, not physical overlap or nut height.",
            "applicability_limit": "The source's M12 timber tests compare composite joint tightening stiffness; they do not isolate this thread component or validate a 1/4-20 Unified pair. This is a conditional model scenario, not an evidence-derived physical law or bound.",
        },
        "fit_slack_comparator": {
            "source": "NBS Handbook H28 (1969), Part I, ideal 60-degree Unified profile relation and 1/4-20 class limits; current ASME B1.1-2024 numerical table confirmation remains open.",
            "external_2a_pitch_diameter_limits_in": [external_min, external_max],
            "internal_2b_pitch_diameter_limits_in": [internal_min, internal_max],
            "diametral_pitch_clearance_in": [clearance_min_in, clearance_max_in],
            "functional_diameter_factor": functional_factor,
            "total_reversal_travel_mm": [reversal_min_mm, reversal_max_mm],
            "one_way_initial_free_travel_mm_if_phase_unknown": [0.0, reversal_max_mm],
            "opposing_direction_slack_relation": "For one ideal fixed-rotation matched pair, g_positive + g_negative equals its total flank-to-flank reversal travel within the listed comparator interval; initial phase is unmeasured.",
            "assumptions": [
                "ideal full-form 60-degree Unified flanks",
                "zero pitch/lead, flank-angle, helix-form, taper, and roundness error",
                "relative nut/bolt rotation fixed",
                "at least one mutually engaged full-form thread turn",
                "no preload and no known initial flank phase",
            ],
            "meaning": "Historical dimensional fit comparator only; not delivered WJ04 fit, current-edition ASME acceptance limits, or WJ24 hardware evidence.",
        },
        "conditional_piecewise_law": {
            "coordinate": "delta is bolt-to-nut relative axial displacement, positive in the chosen tensile direction.",
            "equations": [
                "F=0 when -g_negative < delta < g_positive",
                "F=K_th*(delta-g_positive) when delta >= g_positive",
                "F=K_th*(delta+g_negative) when delta <= -g_negative",
                "g_positive >= 0; g_negative >= 0; g_positive + g_negative = b_reversal",
            ],
            "interpretation": "This combines a separately conditional post-seating tangent with an idealized fixed-rotation fit gap. It is not a physical 1/4-20 constitutive law until model applicability, class limits, full-form overlap, and assembled fit are supported.",
        },
        "compliance_partition": {
            "included": "Post-seating equivalent thread-engagement component K_th only.",
            "bolt_body": "Bolt shank/threaded-segment/body extension remains in the explicit deformable bolt model as applicable; do not add its EA/L compliance to this engagement connector again.",
            "nut_body": "A rigid nut contributes no nut-body compliance in the response model. This calculation does not assert that real nut-body compliance is zero; include it only through an explicit deformable nut or a separately justified term.",
            "other_excluded_compliance": "Washer-seat and timber compression/bearing remain separate explicit components; neither is included in K_th.",
            "fit_is_not_compliance": "The H28 slack comparator is an initial flank-travel interval, not a spring compliance. Matsubara's K_s term is free threaded-bolt length in a series model, not flank backlash.",
        },
        "full_height_fit": {
            "established": False,
            "catalog_nut_thickness_mm": [5.3848, 5.7404],
            "nut_thickness_proves_active_thread_height": False,
            "missing_exact_parameter": "Axial overlap length of mutually complete external and internal full-form threads after bolt runout and nut entry/exit chamfers, measured from the seated nut-bearing plane.",
            "why_missing": "The current hardware basis gives nominal/standard length screens and nut thickness but no first-full-thread coordinate, female-thread chamfer/active-height coordinate, or delivered matched-pair overlap. Catalog LG/LB or overall length does not supply that intersection.",
        },
        "applicability_blockers": [
            "The finite tangent is a literature-based engineering scenario; M&T did not isolate thread-pair stiffness in a 1/4-20 Unified test. The Zhang-Gao-Xu M36 validation is not used or extrapolated.",
            "The class slack values are from NBS H28 (1969), not verified against numeric ASME B1.1-2024 endpoints; current numeric 2A/2B pitch-diameter limits and delivered effective thread geometry remain unbound.",
            "No exact active full-form overlap, installed initial flank phase, or rotational-restraint/end-stop condition is established for delivered hardware.",
        ],
        "evidence_route": "A source-applicable validated analytical/numerical model or directly applicable published test can support a conditional finite law without a brand-specific coupon. This scenario alone does not meet that validation gate and does not create a coupon prerequisite for unrelated sensitivity calculations.",
    }


def main() -> None:
    result = build_calculation()
    output = Path(__file__).with_name("calculation.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
