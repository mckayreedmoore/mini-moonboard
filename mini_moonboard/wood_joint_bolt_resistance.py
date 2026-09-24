"""Bolt material and washer references for wood-to-wood joints.

All numeric results here are conditional component references. They are not
adjusted connection capacities, and they do not resolve combined bolt action.
NDS fastener bending yield strength (Fyb), loaded bolt sections, and material
properties must be supplied from evidence for the actual fastener.
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
    applies_to_delivered_fastener: bool | None,
) -> dict:
    """Gate supplied Fyb on the test routes NDS-2024 §12.3.6.2 recognizes.

    Fyb is never inferred here from a catalog grade, proof stress, Fu, or a
    generic 45-ksi value. For the F606 route, the evidence must identify the
    evaluator's tensile-yield-to-Fyb derivation; this function does not invent
    or apply an equation to tensile properties.
    """
    missing: list[str] = []
    if fyb_psi is None:
        missing.append("Fyb value")
    elif not _valid_positive_number(fyb_psi):
        raise ValueError("Fyb must be a positive finite value in psi")

    allowed_methods = {"ASTM F1575", "ASTM F606"}
    if not isinstance(test_method, str) or test_method not in allowed_methods:
        missing.append("recognized ASTM F1575 or F606 basis")
    if not isinstance(evidence_reference, str) or not evidence_reference.strip():
        missing.append("test report or evaluated evidence reference")
    if applies_to_delivered_fastener is not True:
        missing.append("evidence applicability to delivered fastener")

    if missing:
        return {
            "status": "unresolved",
            "fyb_psi": None,
            "basis": None,
            "missing": missing,
            "limits": "Catalog grade and generic NDS bolt values do not fill this gap.",
        }
    return {
        "status": "basis_recorded",
        "fyb_psi": fyb_psi,
        "basis": f"ANSI/AWC NDS-2024 12.3.6.2 via {test_method}",
        "evidence_reference": evidence_reference.strip(),
        "limits": (
            "Basis was recorded from caller input, not independently authenticated. "
            "F606 evidence must show the Fyb derivation."
        ),
    }


def bolt_first_yield_reference(
    *,
    axial_force_n: float,
    lateral_shear_vector_n: tuple[float, float],
    minimum_tensile_area_mm2: float | None,
    shear_plane_area_mm2: float | None,
    certified_min_yield_mpa: float | None,
    material_basis: str | None,
    tensile_area_basis: str | None,
    shear_area_basis: str | None,
) -> dict:
    """Return separate, unadjusted bolt first-yield component references.

    The force sign convention is tension positive; compression produces zero
    bolt-tension demand here. Pure shear first yield uses von Mises
    ``tau_y = Fy/sqrt(3)``. Areas and the product-property basis are mandatory.
    No combined tension/shear rule is established for these timber joints, so
    combined utilization is always unresolved.
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
    if certified_min_yield_mpa is None:
        missing.append("certified minimum tensile yield strength")
    elif not _valid_positive_number(certified_min_yield_mpa):
        raise ValueError("certified minimum yield strength must be positive finite MPa")
    if not _nonempty(material_basis):
        missing.append("fastener material/product standard and evidence reference")
    if not _nonempty(tensile_area_basis):
        missing.append("tensile-area basis and controlling section")
    if not _nonempty(shear_area_basis):
        missing.append("shear-area basis and loaded section (shank or thread root)")

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
        }

    assert minimum_tensile_area_mm2 is not None
    assert shear_plane_area_mm2 is not None
    assert certified_min_yield_mpa is not None
    tension_reference_n = minimum_tensile_area_mm2 * certified_min_yield_mpa
    shear_reference_n = shear_plane_area_mm2 * certified_min_yield_mpa / math.sqrt(3.0)
    if not math.isfinite(tension_reference_n) or not math.isfinite(shear_reference_n):
        raise ValueError("bolt first-yield reference is nonfinite")
    return {
        "status": "component_references_only",
        "axial_tension_demand_n": demand_t,
        "lateral_shear_demand_n": demand_v,
        "tension_first_yield_reference_n": tension_reference_n,
        "shear_first_yield_reference_n": shear_reference_n,
        "tension_first_yield_utilization": demand_t / tension_reference_n,
        "shear_first_yield_utilization": demand_v / shear_reference_n,
        "interaction_rule": "unresolved",
        "interaction_utilization": None,
        "material_basis": material_basis.strip(),
        "tensile_area_basis": tensile_area_basis.strip(),
        "shear_area_basis": shear_area_basis.strip(),
        "limits": (
            "Unadjusted material first-yield references only; not code design "
            "strengths or acceptance. Combined tension/shear, bolt fracture, "
            "fatigue, thread stripping, nut/head pull-through, and load-sharing "
            "effects are not checked."
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


def washer_steel_resistance_status() -> dict:
    """Expose unresolved washer-metal checks without inventing plate capacity."""
    return {
        "status": "unresolved",
        "resistance_n": None,
        "missing": [
            "delivered washer standard, material, and dimensions",
            "applicable washer bending/spreading resistance method for wood support",
            "actual washer-to-wood contact and load distribution",
        ],
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
