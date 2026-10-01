"""Source-bounded individual-bolt lateral-yield component for NDS-2024.

The maintained API implements the individual-bolt wood/wood lateral-yield
route in NDS-2024 §12.3.1A and §12.3.8 for a single bolt through solid-sawn
lumber. Two-member joints use all six single-shear modes, three-member joints
use all four symmetric double-shear modes, and stacks of four or more use the
NDS pair/triple procedure. This is a reference Z calculation only. It never
returns a connection pass or an adjusted/current capacity.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any, Mapping

from fea.dowel_yield import single_shear


NDS_EDITION = "ANSI/AWC NDS-2024"
METHOD_ID = "awc_nds2024_12_3_individual_bolt_solid_sawn_lumber"
CURRENT_GEOMETRY_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
CURRENT_MANIFEST_ID = "current-full-frame-input-manifest-attempt04"
CURRENT_MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/"
    "current-full-frame-input-manifest.json"
)
CURRENT_MANIFEST_FILE_SHA256 = (
    "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11"
)
CURRENT_MANIFEST_DECLARED_SHA256 = (
    "8db026d0764ee3f4f9f83656133e18ea11ebe250acd0c431567e85fa4d4d23bc"
)

NDS_SOURCE_PINS = {
    "standard_page": "https://awc.org/resources/2024-nds/",
    "standard_title": "2024 National Design Specification for Wood Construction",
    "standard_status": "ANSI-approved 2024 edition; AWC free view-only source",
    "errata_and_addenda": (
        "https://awc.org/wp-content/uploads/2026/03/"
        "2024-NDS-Errata-and-Addenda-03.23.26.pdf"
    ),
    "errata_and_addenda_sha256": (
        "b3f4f8b3b2e2ffa5eb618de9e1182614c329d9e4a135096667364dc9a8e473c0"
    ),
    "january_2025_table_12_3_1b_erratum": (
        "https://web-media.awc.org/wp-content/uploads/2025/03/31134949/"
        "2024-NDS-Errata-and-Addenda-03.28.25.pdf"
    ),
    "january_2025_erratum_sha256": (
        "2ecba75d6603994cafca68fbb049d0b9ff00f5e9df8dd0783e5150c3ca6460d8"
    ),
    "clauses": [
        "12.3.1 and Table 12.3.1A: applicable yield modes and reference Z",
        "Table 12.3.1B and January 2025 erratum: Rd terms",
        "12.3.3 and Table 12.3.3: solid-wood Fe from G and selected D",
        "12.3.4 / Eq. 12.3-11: angle-to-grain Fe",
        "12.3.6.2: Fyb test basis",
        "12.3.7.1-12.3.7.2: D versus Dr and one-quarter thread-bearing limit",
        "12.3.8.1-12.3.8.2: four-or-more-member pair/triple procedure",
        "12.5: minimum end, edge, and spacing requirements",
        "12.5.2.2: end-grain factor (excluded here)",
        "Table 11.3.1: applicable adjustment factors (not calculated here)",
    ],
}

_SINGLE_MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
_DOUBLE_MODES = ("Im", "Is", "IIIs", "IV")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _finite(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def _source_ref_ok(value: Any) -> bool:
    return (
        isinstance(value, Mapping)
        and isinstance(value.get("path"), str)
        and bool(value["path"].strip())
        and isinstance(value.get("locator"), str)
        and bool(value["locator"].strip())
        and isinstance(value.get("sha256"), str)
        and bool(_SHA256_RE.fullmatch(value["sha256"]))
    )


def _field_missing(mapping: Any, field: str) -> bool:
    return not isinstance(mapping, Mapping) or field not in mapping or mapping[field] is None


def _pending(missing: list[str], *, reason: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "method_id": METHOD_ID,
        "standard_edition": NDS_EDITION,
        "status": "pending",
        "reference_lateral_lbf": None,
        "reference_values_by_analysis_lbf": None,
        "missing_inputs": sorted(set(missing)),
        "adjusted_capacity_lbf": None,
        "adjustment_status": "pending_not_calculated",
        "current_demand_status": "pending_not_bound",
        "criterion_disposition": "pending",
        "capacity_or_pass_claim": False,
        "source_pins": NDS_SOURCE_PINS,
    }
    if reason:
        payload["reason"] = reason
    return payload


def _round_50(psi: float) -> float:
    # NDS Table 12.3.3: tabulated Fe is rounded to the nearest 50 psi.
    # The half-up form avoids Python's ties-to-even round behavior.
    return 50.0 * math.floor(psi / 50.0 + 0.5)


def _fe_theta_psi(*, specific_gravity: float, diameter_in: float,
                  angle_degrees: float) -> float:
    """NDS-2024 Table 12.3.3 plus Eq. 12.3-11 for solid-sawn wood."""
    if diameter_in < 0.25:
        return _round_50(16600.0 * specific_gravity**1.84)
    fe_parallel = _round_50(11200.0 * specific_gravity)
    fe_perpendicular = _round_50(
        6100.0 * specific_gravity**1.45 / math.sqrt(diameter_in)
    )
    radians = math.radians(angle_degrees)
    sin2 = math.sin(radians) ** 2
    cos2 = math.cos(radians) ** 2
    result = (fe_parallel * fe_perpendicular) / (
        fe_parallel * sin2 + fe_perpendicular * cos2
    )
    if not math.isfinite(result) or result <= 0:
        raise ValueError("NDS dowel-bearing strength is nonfinite or nonpositive")
    return result


def _reduction_terms(*, diameter_in: float, nominal_diameter_in: float,
                     angle_max_degrees: float) -> dict[str, float]:
    """NDS-2024 Table 12.3.1B with the January 2025 correction."""
    k_theta = 1.0 + 0.25 * angle_max_degrees / 90.0
    if diameter_in >= 0.25:
        return {
            "Im": 4.0 * k_theta,
            "Is": 4.0 * k_theta,
            "II": 3.6 * k_theta,
            "IIIm": 3.2 * k_theta,
            "IIIs": 3.2 * k_theta,
            "IV": 3.2 * k_theta,
        }
    # January 2025 erratum: KD = 10D - 0.5 in this interval. For a
    # threaded, nominal full-body bolt with Dr < 1/4 in, NDS Table 12.3.1B
    # footnote 1 additionally applies Ktheta.
    k_d = 2.2 if diameter_in <= 0.17 else 10.0 * diameter_in - 0.5
    reduction = k_d * k_theta if nominal_diameter_in >= 0.25 else k_d
    return dict.fromkeys(_SINGLE_MODES, reduction)


def _validate_source_ref(source: Any, name: str, missing: list[str]) -> None:
    if source is None:
        missing.append(name)
    elif not _source_ref_ok(source):
        raise ValueError(f"{name} must include path, locator, and lowercase SHA-256")


def _collect_missing(case: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in (
        "standard_edition",
        "geometry_revision_id",
        "axis_id",
        "geometry_axis_source",
        "members",
        "adjacent_face_gaps_in",
        "action_source",
        "bolt",
        "load_normal_to_bolt_axis",
        "minimum_spacing_end_edge_verified",
        "spacing_end_edge_source",
        "stack_order_source",
    ):
        if _field_missing(case, field):
            missing.append(field)
    if case.get("standard_edition") not in (None, NDS_EDITION):
        missing.append("standard_edition_mismatch_requires_method_rebind")
    if case.get("standard_edition") is not None and case.get("standard_edition") != NDS_EDITION:
        return missing
    members = case.get("members")
    if not isinstance(members, list):
        missing.append("members:ordered_member_records")
        members = []
    if len(members) < 2:
        missing.append("members:at_least_two_required_for_bolt_shear_plane")
    for index, member in enumerate(members):
        prefix = f"members[{index}]"
        if not isinstance(member, Mapping):
            missing.append(prefix)
            continue
        for field in (
            "member_id", "material_class", "bearing_length_in",
            "specific_gravity", "specific_gravity_source",
            "load_to_grain_degrees", "bolt_axis_perpendicular_to_grain",
            "thread_bearing_length_in", "lateral_force_lbf",
            "bearing_length_source", "grain_orientation_source",
        ):
            if _field_missing(member, field):
                missing.append(f"{prefix}.{field}")
        _validate_source_ref(
            member.get("specific_gravity_source"),
            f"{prefix}.specific_gravity_source", missing,
        )
        _validate_source_ref(
            member.get("bearing_length_source"),
            f"{prefix}.bearing_length_source", missing,
        )
        _validate_source_ref(
            member.get("grain_orientation_source"),
            f"{prefix}.grain_orientation_source", missing,
        )
    gaps = case.get("adjacent_face_gaps_in")
    if isinstance(gaps, list) and len(gaps) != max(0, len(members) - 1):
        missing.append("adjacent_face_gaps_in:one_gap_per_adjacent_interface")
    elif gaps is not None and not isinstance(gaps, list):
        missing.append("adjacent_face_gaps_in:array_required")
    bolt = case.get("bolt")
    if not isinstance(bolt, Mapping):
        bolt = {}
    for field in (
        "kind", "nominal_diameter_in", "root_diameter_in", "threaded",
        "bending_yield_strength_psi", "product_source", "fyb_basis",
    ):
        if _field_missing(bolt, field):
            missing.append(f"bolt.{field}")
    _validate_source_ref(bolt.get("product_source"), "bolt.product_source", missing)
    _validate_source_ref(bolt.get("fyb_basis"), "bolt.fyb_basis", missing)
    for field in ("geometry_axis_source", "stack_order_source", "spacing_end_edge_source"):
        _validate_source_ref(case.get(field), field, missing)
    if bolt.get("threaded") is True:
        for index, member in enumerate(members):
            if isinstance(member, Mapping) and member.get("thread_bearing_length_in") is None:
                missing.append(f"members[{index}].thread_bearing_length_in")
    action = case.get("action_source")
    if action is None:
        missing.append("action_source")
    elif not _source_ref_ok(action):
        raise ValueError("action_source must include path, locator, and lowercase SHA-256")
    return sorted(set(missing))


def _validate_inputs(case: Mapping[str, Any]) -> tuple[float, dict[str, float], list[dict[str, Any]]]:
    if case.get("standard_edition") != NDS_EDITION:
        raise ValueError(f"standard_edition must be exactly {NDS_EDITION}")
    if not isinstance(case.get("geometry_revision_id"), str) or not case["geometry_revision_id"].strip():
        raise ValueError("geometry_revision_id is required")
    if not isinstance(case.get("axis_id"), str) or not case["axis_id"].strip():
        raise ValueError("axis_id is required")
    if case.get("load_normal_to_bolt_axis") is not True:
        raise ValueError("NDS 12.3.1 yield equations require lateral load perpendicular to bolt axis")
    if case.get("minimum_spacing_end_edge_verified") is not True:
        raise ValueError("NDS 12.3.1 requires §12.5 minimum end, edge, and spacing conditions")
    for source_field in ("geometry_axis_source", "stack_order_source", "spacing_end_edge_source"):
        if not _source_ref_ok(case.get(source_field)):
            raise ValueError(f"{source_field} must bind its independent geometry/stack/detail source")

    members = case["members"]
    if not isinstance(members, list) or len(members) < 2:
        raise ValueError("NDS lateral-yield method requires at least two ordered solid-wood members")
    ids = []
    for i, member in enumerate(members):
        if not isinstance(member, Mapping):
            raise ValueError(f"members[{i}] must be an object")
        member_id = member.get("member_id")
        if not isinstance(member_id, str) or not member_id.strip() or member_id in ids:
            raise ValueError("member IDs must be unique nonempty strings")
        ids.append(member_id)
        if member.get("material_class") != "solid_sawn_lumber":
            raise ValueError("this method supports solid-sawn lumber only")
        for field in ("bearing_length_in", "specific_gravity", "load_to_grain_degrees",
                      "thread_bearing_length_in", "lateral_force_lbf"):
            value = member.get(field)
            if not _finite(value):
                raise ValueError(f"members[{i}].{field} must be finite")
        if member["bearing_length_in"] <= 0:
            raise ValueError("bearing lengths must be positive")
        if not 0 < member["specific_gravity"] <= 1.0:
            raise ValueError("specific gravity must be greater than 0 and no more than 1")
        if not 0 <= member["load_to_grain_degrees"] <= 90:
            raise ValueError("load-to-grain angle must be in [0, 90] degrees")
        if type(member.get("bolt_axis_perpendicular_to_grain")) is not bool:
            raise ValueError("bolt-axis/grain perpendicular orientation must be explicit")
        if not member["bolt_axis_perpendicular_to_grain"]:
            raise ValueError("this method requires a bolt axis perpendicular to each member's grain")
        if not _source_ref_ok(member.get("grain_orientation_source")):
            raise ValueError(f"members[{i}].grain_orientation_source is not source-bound")
        if not 0 <= member["thread_bearing_length_in"] <= member["bearing_length_in"]:
            raise ValueError("thread bearing length must fit within that member")
        if member["lateral_force_lbf"] == 0:
            raise ValueError("member lateral action must be nonzero to establish NDS load direction")
        for source_field in ("specific_gravity_source", "bearing_length_source"):
            if not _source_ref_ok(member.get(source_field)):
                raise ValueError(f"members[{i}].{source_field} is not source-bound")

    gaps = case.get("adjacent_face_gaps_in")
    if not isinstance(gaps, list) or len(gaps) != len(members) - 1:
        raise ValueError("one explicit gap is required at every adjacent member interface")
    for gap in gaps:
        if not _finite(gap) or gap != 0:
            raise ValueError("NDS 12.3.1 applies to contacting faces; gaps must be zero")

    bolt = case["bolt"]
    if not isinstance(bolt, Mapping) or bolt.get("kind") != "bolt":
        raise ValueError("only an explicitly identified bolt is supported")
    for field in ("nominal_diameter_in", "root_diameter_in", "bending_yield_strength_psi"):
        if not _finite(bolt.get(field)) or bolt[field] <= 0:
            raise ValueError(f"bolt.{field} must be positive and finite")
    nominal = float(bolt["nominal_diameter_in"])
    root = float(bolt["root_diameter_in"])
    fyb = float(bolt["bending_yield_strength_psi"])
    if not 0.25 <= nominal <= 1.0:
        raise ValueError("this bolt method is bounded to NDS Table 12.3.1B nominal D of 1/4–1 in")
    if root > nominal:
        raise ValueError("bolt root diameter cannot exceed nominal full-body diameter")
    if type(bolt.get("threaded")) is not bool:
        raise ValueError("bolt.threaded must be explicit")
    if not bolt["threaded"] and root != nominal:
        raise ValueError("unthreaded full-body bolts must have root diameter equal to D")
    if not _source_ref_ok(bolt.get("product_source")):
        raise ValueError("bolt.product_source is not source-bound")
    basis = bolt.get("fyb_basis")
    if not _source_ref_ok(basis):
        raise ValueError("bolt.fyb_basis is not source-bound")
    test_basis = basis.get("test_basis")
    if test_basis not in ("ASTM_F1575", "ASTM_F606_with_Fyb_evaluation"):
        raise ValueError("Fyb basis must be ASTM F1575 or ASTM F606 with an explicit Fyb evaluation")

    effective_diameter = nominal
    if bolt["threaded"]:
        full_body_exception = all(
            member["thread_bearing_length_in"] <= member["bearing_length_in"] / 4.0
            for member in members
        )
        if not full_body_exception:
            effective_diameter = root
    if effective_diameter <= 0 or effective_diameter > 1.0:
        raise ValueError("selected NDS bearing/yield diameter is outside the supported range")
    angle_max = max(float(member["load_to_grain_degrees"]) for member in members)
    reductions = _reduction_terms(
        diameter_in=effective_diameter,
        nominal_diameter_in=nominal,
        angle_max_degrees=angle_max,
    )
    prepared = []
    for member in members:
        fe = _fe_theta_psi(
            specific_gravity=float(member["specific_gravity"]),
            diameter_in=effective_diameter,
            angle_degrees=float(member["load_to_grain_degrees"]),
        )
        prepared.append({**member, "fe_theta_psi": fe})
    return effective_diameter, reductions, prepared


def _single_shear_modes(main: Mapping[str, Any], side: Mapping[str, Any],
                        diameter_in: float, fyb_psi: float,
                        reductions: Mapping[str, float]) -> dict[str, float]:
    moment = fyb_psi * diameter_in**3 / 6.0
    result = single_shear(
        main_length_in=float(main["bearing_length_in"]),
        side_length_in=float(side["bearing_length_in"]),
        main_bearing_lb_in=float(main["fe_theta_psi"]) * diameter_in,
        side_bearing_lb_in=float(side["fe_theta_psi"]) * diameter_in,
        main_yield_moment_lb_in=moment,
        side_yield_moment_lb_in=moment,
        gap_in=0.0,
        reduction_terms=dict(reductions),
    )
    values = result["reference_values_lbf"]
    if set(values) != set(_SINGLE_MODES) or any(not _finite(v) or v <= 0 for v in values.values()):
        raise ValueError("single-shear result is incomplete, nonfinite, or nonpositive")
    return {mode: float(values[mode]) for mode in _SINGLE_MODES}


def _double_shear_modes(main: Mapping[str, Any], side_a: Mapping[str, Any],
                        side_b: Mapping[str, Any], diameter_in: float,
                        fyb_psi: float, reductions: Mapping[str, float]) -> dict[str, float]:
    # NDS 12.3.1 symmetric double shear: the member in the middle is main;
    # the two outer members are side members. This implementation fails closed
    # unless both sides are identical in properties and bearing length.
    comparable = (
        "bearing_length_in", "specific_gravity", "load_to_grain_degrees",
        "fe_theta_psi", "thread_bearing_length_in",
    )
    if any(side_a[key] != side_b[key] for key in comparable):
        raise ValueError("each three-member set must have geometrically/materially symmetric side members")
    if not math.isclose(abs(float(side_a["lateral_force_lbf"])),
                        abs(float(side_b["lateral_force_lbf"])), rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("symmetric double shear requires equal side-member lateral actions")
    if math.copysign(1.0, float(main["lateral_force_lbf"])) == math.copysign(
        1.0, float(side_a["lateral_force_lbf"])
    ):
        raise ValueError("main and side actions in double shear must oppose")

    lm = float(main["bearing_length_in"])
    ls = float(side_a["bearing_length_in"])
    fem = float(main["fe_theta_psi"])
    fes = float(side_a["fe_theta_psi"])
    re = fem / fes
    if not math.isfinite(re) or re <= 0:
        raise ValueError("double-shear bearing ratio is invalid")
    try:
        k3 = -1.0 + math.sqrt(
            2.0 * (1.0 + re) / re
            + 2.0 * fyb_psi * (2.0 + re) * diameter_in**2
            / (3.0 * fem * ls**2)
        )
        values = {
            "Im": diameter_in * lm * fem / reductions["Im"],
            "Is": 2.0 * diameter_in * ls * fes / reductions["Is"],
            "IIIs": 2.0 * k3 * diameter_in * ls * fem
            / ((2.0 + re) * reductions["IIIs"]),
            "IV": 2.0 * diameter_in**2 / reductions["IV"]
            * math.sqrt(2.0 * fem * fyb_psi / (3.0 * (1.0 + re))),
        }
    except (OverflowError, ZeroDivisionError, ValueError) as exc:
        raise ValueError("double-shear yield calculation failed") from exc
    if not math.isfinite(k3) or k3 <= 0 or any(not _finite(v) or v <= 0 for v in values.values()):
        raise ValueError("double-shear result is incomplete, nonfinite, or nonpositive")
    return {mode: float(values[mode]) for mode in _DOUBLE_MODES}


def calculate_multi_member_bolt_reference(case: Mapping[str, Any]) -> dict[str, Any]:
    """Calculate NDS-2024 reference Z for one bolt in an ordered timber stack.

    Required case fields are documented in the attempt README. Missing actual
    inputs return ``status='pending'``; malformed or out-of-scope inputs raise
    ``ValueError``. A complete input returns only a conditional reference Z:
    adjustments, demand comparison, group/wood limit states, and criterion
    disposition remain pending.
    """
    if not isinstance(case, Mapping):
        raise TypeError("case must be a mapping")
    missing = _collect_missing(case)
    if missing:
        return _pending(missing)
    diameter, reductions, members = _validate_inputs(case)
    bolt = case["bolt"]
    n = len(members)
    analyses: list[dict[str, Any]] = []

    if n % 2 == 0:
        roles = case.get("adjacent_pair_roles")
        if not isinstance(roles, list) or len(roles) != n - 1:
            return _pending(["adjacent_pair_roles:one_main_and_side_binding_per_shear_plane"])
        for index in range(n - 1):
            left, right = members[index], members[index + 1]
            if math.copysign(1.0, float(left["lateral_force_lbf"])) == math.copysign(
                1.0, float(right["lateral_force_lbf"])
            ):
                raise ValueError("adjacent members in NDS 12.3.8 even-member procedure must oppose")
            role = roles[index]
            if not isinstance(role, Mapping):
                raise ValueError(f"adjacent_pair_roles[{index}] must identify main and side member IDs")
            main_id, side_id = role.get("main_member_id"), role.get("side_member_id")
            if not isinstance(main_id, str) or not isinstance(side_id, str):
                raise ValueError(f"adjacent_pair_roles[{index}] member IDs must be strings")
            if {main_id, side_id} != {left["member_id"], right["member_id"]} or main_id == side_id:
                raise ValueError(f"adjacent_pair_roles[{index}] must match that adjacent pair")
            by_id = {left["member_id"]: left, right["member_id"]: right}
            modes = _single_shear_modes(
                by_id[main_id], by_id[side_id], diameter,
                float(bolt["bending_yield_strength_psi"]), reductions,
            )
            z = min(modes.values())
            analyses.append({
                "analysis_id": f"single-shear-pair-{index + 1}",
                "type": "single_shear",
                "shear_plane_ids": [f"{left['member_id']}|{right['member_id']}"],
                "main_member_id": main_id,
                "side_member_id": side_id,
                "yield_values_lbf": modes,
                "reference_z_lbf": z,
                "governing_mode": min(modes, key=modes.get),
            })
        if n == 2:
            multiplier = 1.0
            procedure = "NDS-2024-12.3.1A-two-member-single-shear-all-six-modes"
        else:
            multiplier = n / 2.0
            procedure = "NDS-2024-12.3.8.1-even-member-min-pair-times-n-over-2"
    else:
        for index in range(n - 2):
            side_a, main, side_b = members[index:index + 3]
            if math.copysign(1.0, float(side_a["lateral_force_lbf"])) != math.copysign(
                1.0, float(side_b["lateral_force_lbf"])
            ):
                raise ValueError("each NDS 12.3.8 odd-member triple needs same-direction side actions")
            modes = _double_shear_modes(
                main, side_a, side_b, diameter,
                float(bolt["bending_yield_strength_psi"]), reductions,
            )
            z = min(modes.values())
            analyses.append({
                "analysis_id": f"double-shear-triple-{index + 1}",
                "type": "symmetric_double_shear",
                "shear_plane_ids": [
                    f"{side_a['member_id']}|{main['member_id']}",
                    f"{main['member_id']}|{side_b['member_id']}",
                ],
                "main_member_id": main["member_id"],
                "side_member_ids": [side_a["member_id"], side_b["member_id"]],
                "yield_values_lbf": modes,
                "reference_z_lbf": z,
                "governing_mode": min(modes, key=modes.get),
            })
        if n == 3:
            multiplier = 1.0
            procedure = "NDS-2024-12.3.1A-three-member-symmetric-double-shear-all-four-modes"
        else:
            multiplier = (n - 1.0) / 2.0
            procedure = "NDS-2024-12.3.8.2-odd-member-min-triple-times-n-minus-1-over-2"

    z_min = min(analysis["reference_z_lbf"] for analysis in analyses)
    z_connection = z_min * multiplier
    if not math.isfinite(z_connection) or z_connection <= 0:
        raise ValueError("multi-member reference value is nonfinite or nonpositive")
    return {
        "method_id": METHOD_ID,
        "standard_edition": NDS_EDITION,
        "status": "conditional_reference_calculated",
        "procedure": procedure,
        "axis_id": case["axis_id"],
        "geometry_revision_id": case["geometry_revision_id"],
        "member_count": n,
        "ordered_member_ids": [member["member_id"] for member in members],
        "selected_bearing_and_yield_diameter_in": diameter,
        "reduction_terms": reductions,
        "analysis_count": len(analyses),
        "analysis_results": analyses,
        "minimum_adjacent_analysis_z_lbf": z_min,
        "nds_member_count_multiplier": multiplier,
        "reference_lateral_lbf": z_connection,
        "reference_basis": "unadjusted NDS reference Z for one bolt only",
        "adjusted_capacity_lbf": None,
        "adjustment_status": "pending_all_applicable_NDS_Table_11_3_1_and_Table_12_footnotes",
        "current_demand_status": "pending_not_compared",
        "criterion_disposition": "pending",
        "capacity_or_pass_claim": False,
        "excluded_scope": [
            "bolt-group/effective-number effects, including Cg and multiple-fastener distribution",
            "splitting, net section, row tear-out, group tear-out, and member shear/bearing limits",
            "axial/lateral shear interaction and bolt tension or withdrawal",
            "washer bending, load spreading, and wood washer bearing",
            "steel connector, block, plate, cleat, angle, or panel resistance",
            "plywood, wood structural panels, SCL, CLT, end-grain/axis-parallel, and gapped joints",
            "current same-case demand, governing-case selection, pass/fail, and release",
        ],
        "source_pins": NDS_SOURCE_PINS,
    }


def inspect_current_candidate_axis(manifest_path: str | Path, axis_id: str) -> dict[str, Any]:
    """Read-only, hash-pinned inventory of one modeled axis; never a capacity.

    The current manifest only establishes model receiver intervals. These are
    not physical bearing-length/product/grain/action evidence. The function
    intentionally returns pending because the reviewed current records do not
    establish the physical stack/order, product, wood properties, or current
    same-case bolt demand. The returned receiver intervals are model geometry,
    not physical bearing lengths or proof of every load-transfer shear plane.
    """
    path = Path(manifest_path)
    try:
        data = path.read_bytes()
    except OSError as exc:
        return _pending(["current_full_frame_manifest_file"], reason=str(exc))
    actual_sha = hashlib.sha256(data).hexdigest()
    if actual_sha != CURRENT_MANIFEST_FILE_SHA256:
        return _pending(
            ["current_full_frame_manifest_hash_rebind_and_review"],
            reason=(f"manifest bytes SHA-256 {actual_sha} does not match pinned "
                    f"{CURRENT_MANIFEST_FILE_SHA256}"),
        )
    try:
        manifest = json.loads(data)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return _pending(["current_full_frame_manifest_parse"], reason=str(exc))
    if manifest.get("manifest_id") != CURRENT_MANIFEST_ID:
        return _pending(["current_full_frame_manifest_id_rebind"], reason="manifest ID mismatch")
    if manifest.get("geometry_revision_id") != CURRENT_GEOMETRY_REVISION:
        return _pending(["current_geometry_revision_rebind"], reason="geometry revision mismatch")
    axes = manifest.get("candidate_bolt_axes")
    if not isinstance(axes, list):
        return _pending(["candidate_bolt_axes_manifest_inventory"])
    found = [axis for axis in axes if isinstance(axis, Mapping) and axis.get("axis_id") == axis_id]
    if len(found) != 1:
        return _pending([f"axis_id:{axis_id}:unique_manifest_binding"])
    axis = found[0]
    member_ids = axis.get("receiver_member_ids")
    intervals = axis.get("geometry", {}).get("wood_receiver_intervals")
    if not isinstance(member_ids, list) or not isinstance(intervals, list):
        return _pending(["manifest_axis_receiver_geometry"])
    interval_by_id = {item.get("receiver_id"): item for item in intervals if isinstance(item, Mapping)}
    if len(interval_by_id) != len(intervals) or set(interval_by_id) != set(member_ids):
        return _pending(["manifest_axis_receiver_interval_reconciliation"])
    model_geometry = []
    for member_id in member_ids:
        item = interval_by_id[member_id]
        segments = item.get("intersection_solid_intervals_from_underhead_mm")
        if not isinstance(segments, list) or len(segments) != 1:
            return _pending([f"manifest_axis_member:{member_id}:simple_interval_binding"])
        interval = segments[0]
        if (not isinstance(interval, list) or len(interval) != 2
                or not all(_finite(v) for v in interval) or interval[1] <= interval[0]):
            return _pending([f"manifest_axis_member:{member_id}:valid_interval"])
        model_geometry.append({
            "member_id": member_id,
            "modeled_receiver_interval_from_underhead_mm": interval,
            "modeled_interval_length_mm": interval[1] - interval[0],
            "modeled_interval_length_in": (interval[1] - interval[0]) / 25.4,
            "physical_bearing_length_established": False,
        })
    missing = [
        "physical_head_to_nut_stack_order_and_all_member_layers",
        "per_interface_actual_face_contact_gap_and_actual_bearing_lengths",
        "selected_delivered_bolt_product_and_nominal/root/thread-bearing geometry",
        "bolt_Fyb_with_NDS_12_3_6_2_test_source",
        "per-member solid-sawn species/grade/specific-gravity evidence",
        "per-member load-to-grain angle and bolt-axis orientation",
        "per-case signed lateral actions at every member/shear plane",
        "NDS_12_5_minimum_spacing_end_and_edge_evidence",
        "all_applicable_NDS_adjustment_factors_and_group_effects",
        "fresh_current_same-case_demand_and_governing_case",
        "physical_head_to_nut_stack_and_all_load_transfer_shear_planes_required",
    ]
    return {
        "method_id": METHOD_ID,
        "status": "pending",
        "candidate": manifest.get("candidate"),
        "manifest_id": manifest.get("manifest_id"),
        "manifest_file_sha256": actual_sha,
        "manifest_declared_sha256": manifest.get("manifest_sha256"),
        "geometry_revision_id": manifest.get("geometry_revision_id"),
        "axis_id": axis_id,
        "receiver_member_ids": member_ids,
        "modeled_receiver_geometry_only": model_geometry,
        "member_order_established": False,
        "physical_product_selected_or_received": False,
        "current_full_frame_demands_available": False,
        "missing_inputs": missing,
        "reference_lateral_lbf": None,
        "adjusted_capacity_lbf": None,
        "criterion_disposition": "pending",
        "capacity_or_pass_claim": False,
    }
