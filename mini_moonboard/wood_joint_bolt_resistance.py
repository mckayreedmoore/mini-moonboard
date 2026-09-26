"""Conditional bolt/washer references for wood-to-wood joint development.

The optional same-section von Mises result is only a nominal material
first-yield comparison. None of these results is an adjusted connection
capacity or acceptance check. Specified material scenarios and delivered-part
conformance are separate records; washer plate/spreading resistance remains a
named method gap.
"""

from __future__ import annotations

import math


def nds_effective_bolt_diameter_in(
    *,
    full_body_diameter_in: float,
    thread_root_diameter_in: float,
    threaded_full_body_fastener: bool,
    main_bearing_length_in: float,
    side_bearing_length_in: float,
    main_thread_bearing_length_in: float,
    side_thread_bearing_length_in: float,
) -> dict:
    """Select NDS D or Dr from measured thread occupancy in both wood members.

    ANSI/AWC NDS-2024 §12.3.7 uses Dr for threaded or reduced-body fasteners,
    except that full-body D is allowed when thread bearing is no more than 1/4
    of the full bearing length in each member holding threads. This helper
    selects the wood lateral-yield diameter only. Steel tension and shear areas
    at the actual sections are separate inputs to ``bolt_first_yield_reference``.
    """
    _positive_finite(full_body_diameter_in, "full-body diameter")
    _positive_finite(thread_root_diameter_in, "thread-root diameter")
    if thread_root_diameter_in > full_body_diameter_in:
        raise ValueError("thread-root diameter cannot exceed full-body diameter")
    if type(threaded_full_body_fastener) is not bool:
        raise ValueError("threaded_full_body_fastener must be an explicit boolean")

    _positive_finite(main_bearing_length_in, "main bearing length")
    _positive_finite(side_bearing_length_in, "side bearing length")
    _nonnegative_finite(main_thread_bearing_length_in, "main thread-bearing length")
    _nonnegative_finite(side_thread_bearing_length_in, "side thread-bearing length")
    if main_thread_bearing_length_in > main_bearing_length_in:
        raise ValueError("main thread-bearing length exceeds main bearing length")
    if side_thread_bearing_length_in > side_bearing_length_in:
        raise ValueError("side thread-bearing length exceeds side bearing length")

    main_fraction = main_thread_bearing_length_in / main_bearing_length_in
    side_fraction = side_thread_bearing_length_in / side_bearing_length_in
    use_full_body = (
        threaded_full_body_fastener and main_fraction <= 0.25 and side_fraction <= 0.25
    )
    diameter = full_body_diameter_in if use_full_body else thread_root_diameter_in
    return {
        "status": "conditional_input_screen",
        "basis": "ANSI/AWC NDS-2024 12.3.7.1-12.3.7.2",
        "diameter_case": "full_body_D" if use_full_body else "thread_root_Dr",
        "effective_lateral_diameter_in": diameter,
        "main_thread_bearing_fraction": main_fraction,
        "side_thread_bearing_fraction": side_fraction,
        "full_body_rule_applied": use_full_body,
        "sub_quarter_inch_reduction_required": diameter < 0.25,
        "limits": (
            "Requires measured bearing and thread-bearing lengths in each wood "
            "member. Does not determine steel shear/tension area or prove the "
            "delivered bolt matches these inputs."
        ),
    }


def nds_fyb_basis_status(
    *,
    fyb_psi: float | None,
    test_method: str | None,
    evidence_reference: str | None,
    scenario_id: str | None,
    fyb_derivation_reference: str | None = None,
    delivered_conformance_status: str = "not_assessed",
    delivered_evidence_reference: str | None = None,
) -> dict:
    """Separate a specified Fyb scenario from test-method and delivery gates.

    Fyb is never inferred here from a catalog grade, proof stress, Fu, or a
    generic 45-ksi value. For the F606 route, the evidence must identify the
    evaluator's tensile-yield-to-Fyb derivation; this function does not invent
    or apply an equation to tensile properties. A caller may record an
    explicitly sourced conditional scenario before delivered hardware is
    selected. Recording that scenario does not make it an NDS test-derived
    value or establish delivered-part conformance.
    """
    scenario_missing: list[str] = []
    if fyb_psi is None:
        scenario_missing.append("specified Fyb scenario value")
    elif not _valid_positive_number(fyb_psi):
        raise ValueError("Fyb must be a positive finite value in psi")
    if not _nonempty(scenario_id):
        scenario_missing.append("specified scenario ID")
    if not _nonempty(evidence_reference):
        scenario_missing.append("specified scenario source reference")

    allowed_methods = {"ASTM F1575", "ASTM F606"}
    method_missing: list[str] = []
    if not isinstance(test_method, str) or test_method not in allowed_methods:
        method_missing.append("recognized ASTM F1575 or F606 test method")
    if test_method == "ASTM F606" and not _nonempty(fyb_derivation_reference):
        method_missing.append("supported F606 tensile-yield-to-Fyb derivation")

    delivery = _delivery_conformance_record(
        delivered_conformance_status, delivered_evidence_reference
    )
    scenario_recorded = not scenario_missing
    test_basis_recorded = not method_missing and not scenario_missing
    return {
        "status": "specified_scenario_recorded" if scenario_recorded else "unresolved",
        "specified_scenario": {
            "status": "recorded" if scenario_recorded else "unresolved",
            "scenario_id": scenario_id.strip() if _nonempty(scenario_id) else None,
            "fyb_psi": fyb_psi if scenario_recorded else None,
            "evidence_reference": (
                evidence_reference.strip() if _nonempty(evidence_reference) else None
            ),
            "missing": scenario_missing,
        },
        "nds_test_basis": {
            "status": "recorded" if test_basis_recorded else "unresolved",
            "basis": (
                f"ANSI/AWC NDS-2024 12.3.6.2 via {test_method}"
                if test_basis_recorded
                else None
            ),
            "test_method": test_method if test_basis_recorded else None,
            "fyb_derivation_reference": (
                fyb_derivation_reference.strip()
                if test_basis_recorded and _nonempty(fyb_derivation_reference)
                else None
            ),
            "missing": method_missing + scenario_missing,
        },
        "delivered_fastener_conformance": delivery,
        "limits": (
            "Caller-supplied scenario and references are not independently "
            "authenticated. A specified estimate without the recognized test "
            "basis remains scenario-only; it is not test-derived NDS Fyb. "
            "Delivered conformance is a separate receiving record."
        ),
    }


def bolt_first_yield_reference(
    *,
    axial_force_n: float,
    lateral_shear_vector_n: tuple[float, float],
    minimum_tensile_area_mm2: float | None,
    shear_plane_area_mm2: float | None,
    specified_min_yield_mpa: float | None,
    property_scenario_id: str | None,
    material_basis: str | None,
    tensile_area_basis: str | None,
    shear_area_basis: str | None,
    combined_action_area_mm2: float | None = None,
    combined_action_section_basis: str | None = None,
    delivered_conformance_status: str = "not_assessed",
    delivered_evidence_reference: str | None = None,
) -> dict:
    """Return conditional bolt first-yield references from explicit inputs.

    The force sign convention is tension positive; compression produces zero
    bolt-tension demand here. Pure shear first yield uses von Mises
    ``tau_y = Fy/sqrt(3)``. Areas and the product-property basis are mandatory.
    A nominal von Mises axial/shear interaction is reported only when the
    caller identifies one common cross-section for both stresses. This is a
    material first-yield reference, not a connection design rule or acceptance
    check. Delivered-product conformance remains a separate receiving status.
    """
    _finite_number(axial_force_n, "axial force")
    if (
        not isinstance(lateral_shear_vector_n, tuple)
        or len(lateral_shear_vector_n) != 2
        or any(not _valid_number(value) for value in lateral_shear_vector_n)
    ):
        raise ValueError("lateral shear vector must be a finite 2-vector in N")

    demand_t = max(0.0, axial_force_n)
    demand_v = math.hypot(*lateral_shear_vector_n)
    if not math.isfinite(demand_v):
        raise ValueError("lateral shear resultant is nonfinite")
    missing: list[str] = []
    if minimum_tensile_area_mm2 is None:
        missing.append("minimum tensile area at controlling bolt section")
    elif not _valid_positive_number(minimum_tensile_area_mm2):
        raise ValueError("minimum tensile area must be positive finite mm^2")
    if shear_plane_area_mm2 is None:
        missing.append("actual shear-plane area")
    elif not _valid_positive_number(shear_plane_area_mm2):
        raise ValueError("shear-plane area must be positive finite mm^2")
    if specified_min_yield_mpa is None:
        missing.append("specified scenario minimum tensile yield strength")
    elif not _valid_positive_number(specified_min_yield_mpa):
        raise ValueError("specified minimum yield strength must be positive finite MPa")
    if not _nonempty(property_scenario_id):
        missing.append("specified material-property scenario ID")
    if not _nonempty(material_basis):
        missing.append("fastener material/product standard and evidence reference")
    if not _nonempty(tensile_area_basis):
        missing.append("tensile-area basis and controlling section")
    if not _nonempty(shear_area_basis):
        missing.append("shear-area basis and loaded section (shank or thread root)")

    delivery = _delivery_conformance_record(
        delivered_conformance_status, delivered_evidence_reference
    )
    if combined_action_area_mm2 is not None and not _valid_positive_number(
        combined_action_area_mm2
    ):
        raise ValueError("combined-action section area must be positive finite mm^2")
    if combined_action_area_mm2 is not None and not _nonempty(
        combined_action_section_basis
    ):
        raise ValueError("combined-action section basis is required with its area")

    interaction_utilization = None
    interaction_missing = []
    interaction_stress_mpa = None
    if combined_action_area_mm2 is None:
        interaction_missing.append(
            "one co-located section area and basis for the axial and shear stresses"
        )
    if missing:
        return {
            "status": "unresolved",
            "axial_tension_demand_n": demand_t,
            "lateral_shear_demand_n": demand_v,
            "tension_first_yield_reference_n": None,
            "shear_first_yield_reference_n": None,
            "tension_first_yield_utilization": None,
            "shear_first_yield_utilization": None,
            "interaction_rule": "unresolved",
            "interaction_utilization": None,
            "missing": missing,
            "interaction_missing": interaction_missing,
            "delivered_fastener_conformance": delivery,
        }

    assert minimum_tensile_area_mm2 is not None
    assert shear_plane_area_mm2 is not None
    assert specified_min_yield_mpa is not None
    tension_reference_n = minimum_tensile_area_mm2 * specified_min_yield_mpa
    shear_reference_n = shear_plane_area_mm2 * specified_min_yield_mpa / math.sqrt(3.0)
    if not math.isfinite(tension_reference_n) or not math.isfinite(shear_reference_n):
        raise ValueError("bolt first-yield reference is nonfinite")
    if combined_action_area_mm2 is not None:
        normal_stress_mpa = abs(axial_force_n) / combined_action_area_mm2
        average_shear_stress_mpa = demand_v / combined_action_area_mm2
        interaction_stress_mpa = math.hypot(
            normal_stress_mpa, math.sqrt(3.0) * average_shear_stress_mpa
        )
        if not math.isfinite(interaction_stress_mpa):
            raise ValueError("combined bolt first-yield reference is nonfinite")
        interaction_utilization = interaction_stress_mpa / specified_min_yield_mpa
    return {
        "status": "material_first_yield_reference_only",
        "axial_tension_demand_n": demand_t,
        "lateral_shear_demand_n": demand_v,
        "tension_first_yield_reference_n": tension_reference_n,
        "shear_first_yield_reference_n": shear_reference_n,
        "tension_first_yield_utilization": demand_t / tension_reference_n,
        "shear_first_yield_utilization": demand_v / shear_reference_n,
        "specified_material_scenario": {
            "scenario_id": property_scenario_id.strip(),
            "minimum_yield_strength_mpa": specified_min_yield_mpa,
            "basis": material_basis.strip(),
        },
        "interaction_rule": (
            "nominal_von_mises_same_section_average_shear"
            if combined_action_area_mm2 is not None
            else "unresolved"
        ),
        "interaction_utilization": interaction_utilization,
        "interaction_equivalent_stress_mpa": interaction_stress_mpa,
        "interaction_section": (
            {
                "area_mm2": combined_action_area_mm2,
                "basis": combined_action_section_basis.strip(),
                "normal_stress_mpa": abs(axial_force_n) / combined_action_area_mm2,
                "average_shear_stress_mpa": demand_v / combined_action_area_mm2,
            }
            if combined_action_area_mm2 is not None
            else None
        ),
        "interaction_missing": interaction_missing,
        "bending_first_yield_status": "unresolved_not_evaluated",
        "delivered_fastener_conformance": delivery,
        "material_basis": material_basis.strip(),
        "tensile_area_basis": tensile_area_basis.strip(),
        "shear_area_basis": shear_area_basis.strip(),
        "limits": (
            "Unadjusted material references only; not code design strengths or "
            "acceptance. The optional von Mises result assumes average shear "
            "stress over one caller-identified common section and omits bending, "
            "stress concentrations, fracture, fatigue, thread stripping, "
            "nut/head pull-through, and load-sharing effects."
        ),
    }


def wood_washer_annulus_reference_lbf(
    *,
    washer_outer_diameter_in: float,
    washer_inner_diameter_in: float,
    wood_bore_diameter_in: float,
) -> dict:
    """Return ideal DF-L No. 2 Fc-perp bearing on a fully supported washer annulus.

    Reuses the project's NDS-2024-based 625-psi helper. This is wood bearing
    only. It does not calculate washer steel bending/spreading, establish actual
    flat contact, or credit preload or bearing-area increases.
    """
    from mini_moonboard.bolted_timber_checks import (
        dfl_axial_wood_bearing_reference_lbf,
    )

    reference = dfl_axial_wood_bearing_reference_lbf(
        washer_outer_diameter_in=washer_outer_diameter_in,
        wood_bore_diameter_in=wood_bore_diameter_in,
        washer_inner_diameter_in=washer_inner_diameter_in,
    )
    return {
        "status": "conditional_wood_reference_only",
        "wood_fc_perp_psi": 625.0,
        "wood_bearing_reference_lbf": reference,
        "basis": "2024 NDS Supplement Table 4A; DF-L No. 2 Fc-perp",
        "assumptions": [
            "uniform compression over full circular washer/wood annulus",
            "washer footprint fits sound wood",
            "no preload or bearing-area-factor increase",
        ],
        "washer_steel_bending_spreading": "unresolved",
        "limits": "Not actual contact evidence, bolt tension capacity, or joint capacity.",
    }


def washer_steel_resistance_status(
    *,
    scenario_id: str | None = None,
    washer_standard: str | None = None,
    material_basis: str | None = None,
    outer_diameter_in: float | None = None,
    inner_diameter_in: float | None = None,
    thickness_in: float | None = None,
    specified_yield_strength_psi: float | None = None,
    evidence_reference: str | None = None,
    delivered_conformance_status: str = "not_assessed",
    delivered_evidence_reference: str | None = None,
) -> dict:
    """Record washer scenario and receiving inputs, with the real method gap.

    Sourcing and dimensions can complete the input manifest, but no applicable
    washer plate-bending/load-spreading method for this washer-on-timber support
    condition is adopted here. The function therefore reports that precise
    blocker instead of implying that additional catalog data can yield a
    resistance value.
    """
    dimensions = {
        "outer_diameter_in": outer_diameter_in,
        "inner_diameter_in": inner_diameter_in,
        "thickness_in": thickness_in,
        "specified_yield_strength_psi": specified_yield_strength_psi,
    }
    for name, value in dimensions.items():
        if value is not None and not _valid_positive_number(value):
            raise ValueError(f"{name} must be positive and finite")
    if (
        outer_diameter_in is not None
        and inner_diameter_in is not None
        and inner_diameter_in >= outer_diameter_in
    ):
        raise ValueError("washer inner diameter must be less than outer diameter")

    missing: list[str] = []
    for value, label in (
        (scenario_id, "specified washer scenario ID"),
        (washer_standard, "washer standard or explicit product definition"),
        (material_basis, "specified washer material basis"),
        (evidence_reference, "specified washer source reference"),
    ):
        if not _nonempty(value):
            missing.append(label)
    for name, value in dimensions.items():
        if value is None:
            missing.append(name.replace("_", " "))
    delivery = _delivery_conformance_record(
        delivered_conformance_status, delivered_evidence_reference
    )
    return {
        "status": "method_gap",
        "specified_scenario_status": "recorded" if not missing else "incomplete",
        "specified_scenario": {
            "scenario_id": scenario_id.strip() if _nonempty(scenario_id) else None,
            "washer_standard": washer_standard.strip()
            if _nonempty(washer_standard)
            else None,
            "material_basis": material_basis.strip() if _nonempty(material_basis) else None,
            **dimensions,
            "evidence_reference": evidence_reference.strip()
            if _nonempty(evidence_reference)
            else None,
        },
        "scenario_missing": missing,
        "delivered_washer_conformance": delivery,
        "resistance_n": None,
        "method_gap": {
            "id": "washer_steel_bending_and_load_spreading_on_timber",
            "required_method": (
                "An applicable, reviewed washer-plate bending/spreading method "
                "for the specified washer geometry, steel, and timber support "
                "contact; catalog dimensions alone are insufficient."
            ),
            "consequence": (
                "The steel-side washer limit cannot bound bolt tension transfer. "
                "The wood annulus reference cannot close washer failure or the "
                "complete-joint tension criterion."
            ),
        },
    }


def _delivery_conformance_record(status: str, evidence_reference: str | None) -> dict:
    allowed = {"not_assessed", "conforming", "nonconforming"}
    if not isinstance(status, str) or status not in allowed:
        raise ValueError(f"delivery conformance status must be one of {sorted(allowed)}")
    if status == "not_assessed":
        if evidence_reference is not None and _nonempty(evidence_reference):
            raise ValueError("delivery evidence cannot be recorded before assessment")
        return {"status": "not_assessed", "evidence_reference": None}
    if not _nonempty(evidence_reference):
        raise ValueError("an assessed delivery status requires an evidence reference")
    return {
        "status": "recorded_by_caller",
        "recorded_conformance": status,
        "evidence_reference": evidence_reference.strip(),
        "limits": "Caller record only; this helper does not authenticate receiving evidence.",
    }


def _valid_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _valid_positive_number(value: object) -> bool:
    return _valid_number(value) and value > 0


def _finite_number(value: object, label: str) -> None:
    if not _valid_number(value):
        raise ValueError(f"{label} must be a finite number")


def _positive_finite(value: object, label: str) -> None:
    if not _valid_positive_number(value):
        raise ValueError(f"{label} must be a positive finite number")


def _nonnegative_finite(value: object, label: str) -> None:
    if not _valid_number(value) or value < 0:
        raise ValueError(f"{label} must be a finite nonnegative number")


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
