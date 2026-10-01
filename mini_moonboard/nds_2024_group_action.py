"""NDS-2024 Eq. 11.3-1 group-action-factor method boundary.

This module computes only Cg for an explicitly supplied, single uniform row of
same-diameter wood-to-wood dowel fasteners with one to three total members.
Four-or-more-member inputs fail closed until that scope has a source-bound
method. It does not calculate resistance, bolt-force distribution, or criterion
acceptance. Current inputs remain pending until an upstream coordinator
supplies independent source bindings.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

SCHEMA_VERSION = "awc_nds_2024_group_action_input/v1"
SOURCE_ROLES = ("geometry", "member_sections", "fastener_product", "load_cases")
GEOMETRY_TOLERANCE_IN = 1.0e-6
DIRECTION_COSINE_TOLERANCE = 1.0e-8
_SHA256_LENGTH = 64
DIGEST_ALGORITHM = "sha256:python-json-sortkeys-minified-utf8-allow_nan_false/v1"


def _pending(*reasons: str, missing_inputs: Sequence[str] = ()) -> dict[str, Any]:
    return {
        "status": "pending",
        "reason_codes": list(reasons),
        "missing_inputs": list(missing_inputs),
        "cg": None,
        "capacity": None,
        "criterion_disposition": "pending",
    }


def _finite(value: Any) -> bool:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, TypeError, ValueError):
        return False


def _positive(value: Any) -> bool:
    return _finite(value) and value > 0


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != _SHA256_LENGTH:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _is_strict_json_value(value: Any, active: set[int] | None = None) -> bool:
    """Reject Python-only values before applying the documented JSON digest."""
    if value is None or isinstance(value, (str, bool, int)):
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    if active is None:
        active = set()
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active or any(not isinstance(key, str) for key in value):
            return False
        active.add(identity)
        valid = all(_is_strict_json_value(item, active) for item in value.values())
        active.remove(identity)
        return valid
    if isinstance(value, list):
        identity = id(value)
        if identity in active:
            return False
        active.add(identity)
        valid = all(_is_strict_json_value(item, active) for item in value)
        active.remove(identity)
        return valid
    return False


def canonical_group_record_sha256(payload: Mapping[str, Any] | None) -> str | None:
    """Hash the complete strict-JSON group record using the canonical form.

    The digest includes every factor input and its ordered arrays, identities,
    and source bindings. It intentionally hashes the whole record rather than
    a producer-selected subset. The byte form is UTF-8 JSON with recursively
    sorted string object keys, compact `,` and `:` separators, unescaped
    Unicode, and no non-finite numbers. Arrays retain their input order.
    """
    return _canonical_json_sha256(payload)


def _canonical_json_bytes(value: Any) -> bytes | None:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        return None


def _canonical_json_sha256(value: Any) -> str | None:
    try:
        if not _is_strict_json_value(value):
            return None
    except RecursionError:
        return None
    canonical = _canonical_json_bytes(value)
    if canonical is None:
        return None
    return hashlib.sha256(canonical).hexdigest()


def canonical_sensitivity_contract_sha256(
    contract: Mapping[str, Any] | None,
) -> str | None:
    """Hash all sensitivity-contract fields except its declared ``sha256``.

    Excluding the digest field avoids a self-referential hash. All remaining
    fields, including review status, classification, scenario identities, and
    exact changed paths, are covered by the strict-JSON canonical byte rule.
    """
    if not isinstance(contract, Mapping) or "sha256" not in contract:
        return None
    content = {key: value for key, value in contract.items() if key != "sha256"}
    return _canonical_json_sha256(content)


def _vector(value: Any) -> tuple[float, float, float] | None:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
    ):
        return None
    if not all(_finite(component) for component in value):
        return None
    return (float(value[0]), float(value[1]), float(value[2]))


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _cross_norm(left: Sequence[float], right: Sequence[float]) -> float:
    return math.hypot(
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _norm(vector: Sequence[float]) -> float:
    return math.hypot(*vector)


def _unit(vector: Sequence[float]) -> tuple[float, float, float]:
    scale = max(abs(component) for component in vector)
    if scale == 0.0:
        return (0.0, 0.0, 0.0)
    scaled = tuple(component / scale for component in vector)
    length = _norm(scaled)
    return tuple(component / length for component in scaled)  # type: ignore[return-value]


def _binding_map_is_valid(value: Any) -> bool:
    if not isinstance(value, Mapping) or set(value) != set(SOURCE_ROLES):
        return False
    for role in SOURCE_ROLES:
        binding = value[role]
        if not isinstance(binding, Mapping):
            return False
        if (
            not isinstance(binding.get("source_id"), str)
            or not binding["source_id"].strip()
        ):
            return False
        if not _sha256(binding.get("sha256")):
            return False
    member_binding = value["member_sections"]
    side_ids = member_binding.get("side_member_ids")
    shear_planes = member_binding.get("shear_planes")
    return not (
        not isinstance(member_binding.get("main_member_id"), str)
        or not member_binding["main_member_id"].strip()
        or not isinstance(side_ids, list)
        or not side_ids
        or any(
            not isinstance(member_id, str) or not member_id.strip()
            for member_id in side_ids
        )
        or len(set(side_ids)) != len(side_ids)
        or isinstance(shear_planes, bool)
        or not isinstance(shear_planes, int)
        or shear_planes != len(side_ids)
    )


def _source_bindings_match(payload: Mapping[str, Any], expected: Any) -> bool:
    declared = payload.get("source_bindings")
    if not _binding_map_is_valid(declared) or not _binding_map_is_valid(expected):
        return False
    basic_match = all(
        declared[role]["source_id"] == expected[role]["source_id"]
        and declared[role]["sha256"].lower() == expected[role]["sha256"].lower()
        for role in SOURCE_ROLES
    )
    if not basic_match:
        return False
    member_record = payload.get("members")
    if (
        not isinstance(member_record, Mapping)
        or not isinstance(member_record.get("main"), Mapping)
        or not isinstance(member_record.get("side_members"), list)
    ):
        return False
    actual_main_id = member_record["main"].get("member_id")
    actual_side_ids = [
        side.get("member_id") if isinstance(side, Mapping) else None
        for side in member_record["side_members"]
    ]
    actual_planes = member_record.get("shear_planes")
    for binding in (declared["member_sections"], expected["member_sections"]):
        if (
            actual_main_id != binding["main_member_id"]
            or actual_side_ids != binding["side_member_ids"]
            or actual_planes != binding["shear_planes"]
        ):
            return False
    return True


def _group_geometry(
    payload: Mapping[str, Any],
) -> tuple[int, float, tuple[float, float, float]] | dict[str, Any]:
    geometry = payload.get("group_geometry")
    if not isinstance(geometry, Mapping):
        return _pending("missing_group_geometry", missing_inputs=("group_geometry",))

    axis = _vector(geometry.get("row_axis_xyz"))
    if axis is None or _norm(axis) == 0:
        return _pending("invalid_row_axis")
    axis = _unit(axis)

    fasteners = geometry.get("fasteners")
    if not isinstance(fasteners, list) or len(fasteners) < 2:
        return _pending("row_requires_at_least_two_fasteners")

    identities: set[str] = set()
    positions: list[tuple[str, tuple[float, float, float]]] = []
    diameters: list[float] = []
    for fastener in fasteners:
        if not isinstance(fastener, Mapping):
            return _pending("malformed_fastener_geometry")
        fastener_id = fastener.get("fastener_id")
        if (
            not isinstance(fastener_id, str)
            or not fastener_id.strip()
            or fastener_id in identities
        ):
            return _pending("duplicate_or_missing_fastener_id")
        identities.add(fastener_id)
        center = _vector(fastener.get("center_in"))
        diameter = fastener.get("nominal_diameter_in")
        if center is None or not _positive(diameter):
            return _pending("invalid_fastener_geometry_or_diameter")
        if fastener.get("type") != "dowel":
            return _pending("unsupported_fastener_type")
        positions.append((fastener_id, center))
        diameters.append(float(diameter))

    diameter = diameters[0]
    if any(value > 1.0 for value in diameters):
        return _pending("diameter_outside_nds_11_3_6_1_scope")
    if any(value != diameter for value in diameters[1:]):
        return _pending("mixed_fastener_diameters")

    origin = positions[0][1]
    projections: list[tuple[float, float]] = []
    for _, center in positions:
        relative = tuple(center[index] - origin[index] for index in range(3))
        if not all(_finite(value) for value in relative):
            return _pending("derived_group_geometry_outside_finite_range")
        along = _dot(relative, axis)
        transverse = tuple(relative[index] - along * axis[index] for index in range(3))
        transverse_norm = _norm(transverse)
        if (
            not _finite(along)
            or not all(_finite(value) for value in transverse)
            or not _finite(transverse_norm)
        ):
            return _pending("derived_group_geometry_outside_finite_range")
        if transverse_norm > GEOMETRY_TOLERANCE_IN:
            return _pending("not_a_single_straight_row")
        projections.append((along, transverse_norm))

    along_values = sorted(value[0] for value in projections)
    pitches = [
        along_values[index + 1] - along_values[index]
        for index in range(len(along_values) - 1)
    ]
    if any(not _finite(value) for value in pitches):
        return _pending("derived_group_geometry_outside_finite_range")
    if any(pitch <= GEOMETRY_TOLERANCE_IN for pitch in pitches):
        return _pending("duplicate_or_reversed_row_station")
    pitch = pitches[0]
    if any(abs(value - pitch) > GEOMETRY_TOLERANCE_IN for value in pitches[1:]):
        return _pending("nonuniform_pitch_outside_method_scope")

    return len(fasteners), pitch, axis


def _factor_area(
    member: Mapping[str, Any], load_axis: Sequence[float], pitch_in: float
) -> float | dict[str, Any]:
    if member.get("material") != "wood":
        return _pending("unsupported_nonwood_member")
    if not _positive(member.get("elastic_modulus_psi")):
        return _pending("missing_or_invalid_member_modulus")

    grain = _vector(member.get("grain_axis_xyz"))
    if grain is None or _norm(grain) == 0:
        return _pending("missing_or_invalid_member_grain_axis")
    grain = _unit(grain)
    cosine = abs(_dot(grain, load_axis))
    if _cross_norm(grain, load_axis) <= DIRECTION_COSINE_TOLERANCE:
        area = member.get("gross_section_area_in2")
        if not _positive(area):
            return _pending("missing_gross_section_area")
        return float(area)
    if cosine <= DIRECTION_COSINE_TOLERANCE:
        thickness = member.get("thickness_in")
        group_width = member.get("overall_fastener_group_width_in")
        if not _positive(thickness) or not _positive(group_width):
            return _pending("missing_nds_11_3_6_3_perpendicular_area_inputs")
        if not math.isclose(
            float(group_width), pitch_in, rel_tol=0.0, abs_tol=GEOMETRY_TOLERANCE_IN
        ):
            return _pending(
                "perpendicular_group_width_does_not_match_single_row_minimum_pitch"
            )
        equivalent_area = member.get("group_factor_area_in2")
        expected_area = float(thickness) * float(group_width)
        if not _positive(equivalent_area) or not math.isclose(
            float(equivalent_area), expected_area, rel_tol=1.0e-10, abs_tol=1.0e-12
        ):
            return _pending(
                "perpendicular_area_does_not_match_thickness_times_group_width"
            )
        return expected_area
    return _pending("oblique_member_grain_loading_outside_method_scope")


def evaluate_group_action_factor(
    payload: Mapping[str, Any] | None,
    *,
    expected_bindings: Mapping[str, Any] | None,
    expected_payload_sha256: str | None,
) -> dict[str, Any]:
    """Evaluate Eq. 11.3-1 for one completely bound row, or return pending.

    ``expected_bindings`` and ``expected_payload_sha256`` must come from the
    coordinator's independent input manifest. The digest is SHA-256 over the
    complete payload in :func:`canonical_group_record_sha256` format, which
    binds the exact numeric inputs and source references. This function checks
    equality and syntax; it does not establish that the external manifest is
    authoritative or independently reviewed. Missing/mismatched values never
    produce a factor.
    """
    if not isinstance(payload, Mapping):
        return _pending("missing_group_record", missing_inputs=("group_record",))
    if payload.get("schema") != SCHEMA_VERSION:
        return _pending("unsupported_or_missing_schema")

    for key in ("candidate_id", "revision_id", "group_id", "scenario_id"):
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            return _pending("missing_identity_fields", missing_inputs=(key,))

    if expected_bindings is None:
        return _pending(
            "independent_source_manifest_required",
            missing_inputs=("independent_expected_source_bindings",),
        )
    if not _source_bindings_match(payload, expected_bindings):
        return _pending("source_binding_mismatch_or_incomplete")
    observed_payload_sha256 = canonical_group_record_sha256(payload)
    if not _sha256(expected_payload_sha256) or observed_payload_sha256 is None:
        return _pending(
            "independent_canonical_payload_digest_required",
            missing_inputs=("independent_expected_payload_sha256",),
        )
    if observed_payload_sha256 != expected_payload_sha256.lower():
        return _pending("canonical_payload_digest_mismatch")

    geometry_result = _group_geometry(payload)
    if isinstance(geometry_result, dict):
        return geometry_result
    count, pitch, row_axis = geometry_result

    action = payload.get("load_case")
    if (
        not isinstance(action, Mapping)
        or not isinstance(action.get("case_id"), str)
        or not action["case_id"].strip()
    ):
        return _pending(
            "missing_case_bound_group_action", missing_inputs=("load_case",)
        )
    lateral = _vector(action.get("lateral_resultant_xyz_lbf"))
    if lateral is None or _norm(lateral) == 0:
        return _pending("missing_or_zero_lateral_resultant")
    lateral_axis = _unit(lateral)
    if _cross_norm(lateral_axis, row_axis) > DIRECTION_COSINE_TOLERANCE:
        return _pending("load_direction_not_aligned_with_fastener_row")

    members = payload.get("members")
    if not isinstance(members, Mapping):
        return _pending("missing_member_sections", missing_inputs=("members",))
    main = members.get("main")
    sides = members.get("side_members")
    shear_planes = members.get("shear_planes")
    if not isinstance(main, Mapping) or not isinstance(sides, list) or not sides:
        return _pending("incomplete_main_or_side_member_inventory")
    if (
        isinstance(shear_planes, bool)
        or not isinstance(shear_planes, int)
        or shear_planes != len(sides)
    ):
        return _pending("shear_plane_count_does_not_match_side_member_inventory")
    if len(sides) + 1 >= 4:
        return _pending(
            "four_or_more_member_plane_method_not_source_bound"
        )

    main_area = _factor_area(main, lateral_axis, pitch)
    if isinstance(main_area, dict):
        return main_area
    side_areas: list[float] = []
    side_moduli: list[float] = []
    side_ids: set[str] = set()
    for side in sides:
        if not isinstance(side, Mapping):
            return _pending("malformed_side_member_inventory")
        side_id = side.get("member_id")
        if (
            not isinstance(side_id, str)
            or not side_id.strip()
            or side_id == main.get("member_id")
            or side_id in side_ids
        ):
            return _pending("duplicate_or_missing_side_member_id")
        side_ids.add(side_id)
        side_area = _factor_area(side, lateral_axis, pitch)
        if isinstance(side_area, dict):
            return side_area
        side_areas.append(side_area)
        side_moduli.append(float(side["elastic_modulus_psi"]))

    if not isinstance(main.get("member_id"), str) or not main["member_id"].strip():
        return _pending("missing_main_member_id")
    if any(abs(value - side_moduli[0]) > 1.0e-9 for value in side_moduli[1:]):
        return _pending("different_side_member_moduli_outside_method_scope")

    main_ea = float(main["elastic_modulus_psi"]) * main_area
    side_ea = side_moduli[0] * sum(side_areas)
    if not _positive(main_ea) or not _positive(side_ea):
        return _pending("invalid_member_axial_stiffness_terms")

    diameter = float(payload["group_geometry"]["fasteners"][0]["nominal_diameter_in"])
    if diameter < 0.25:
        cg = 1.0
        gamma = None
    else:
        try:
            gamma = 180000.0 * diameter**1.5
            re = min(side_ea, main_ea) / max(side_ea, main_ea)
            u = 1.0 + gamma * pitch / 2.0 * (1.0 / main_ea + 1.0 / side_ea)
            if not math.isfinite(u) or u <= 1.0:
                return _pending("equation_intermediate_outside_finite_range")
            m = 1.0 / (u + math.sqrt(u * u - 1.0))
            numerator = m * (1.0 - m ** (2 * count))
            denominator = count * (
                (1.0 + re * m**count) * (1.0 + m) - 1.0 + m ** (2 * count)
            )
            cg = numerator / denominator * ((1.0 + re) / (1.0 - m))
        except (OverflowError, ZeroDivisionError, ValueError):
            return _pending("equation_arithmetic_failure")
        if not math.isfinite(cg) or cg <= 0.0 or cg > 1.0 + 1.0e-10:
            return _pending("equation_result_outside_physical_factor_range")

    return {
        "status": "calculated_method_only",
        "reason_codes": [],
        "missing_inputs": [],
        "candidate_id": payload["candidate_id"],
        "revision_id": payload["revision_id"],
        "group_id": payload["group_id"],
        "scenario_id": payload["scenario_id"],
        "case_id": action["case_id"],
        "row_fastener_count": count,
        "uniform_pitch_in": pitch,
        "diameter_in": diameter,
        "input_record_sha256": observed_payload_sha256,
        "input_record_digest_algorithm": DIGEST_ALGORITHM,
        "main_ea_lbf": main_ea,
        "side_ea_lbf": side_ea,
        "gamma_lbf_per_in": gamma,
        "cg": cg,
        "capacity": None,
        "criterion_disposition": "pending",
        "provenance_level": "matched_to_caller_supplied_independent_bindings; authority_not_verified_by_method",
        "scope": "NDS-2024 Eq. 11.3-1 group-action factor only; no resistance or demand/capacity comparison",
    }


def _changed_payload_paths(
    left: Any,
    right: Any,
    *,
    path: str = "",
    ignore_root_keys: frozenset[str] = frozenset(),
) -> list[str]:
    """Return exact changed paths using escaped object keys and array indexes.

    Object keys escape backslash, dot, and square brackets with a preceding
    backslash; the empty key is written as backslash plus ``e``. An all-
    whitespace key is encoded as one ``\\uXXXX`` escape per code point. An
    added or removed array item is represented by its indexed path (the whole
    item) and the array's ``.length`` path.
    """
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        keys = set(left) | set(right)
        changed: list[str] = []
        for key in sorted(keys):
            if not path and key in ignore_root_keys:
                continue
            escaped_key = str(key)
            if escaped_key == "":
                escaped_key = r"\e"
            elif not escaped_key.strip():
                escaped_key = "".join(
                    f"\\u{ord(char):04x}" for char in escaped_key
                )
            else:
                escaped_key = "".join(
                    f"\\{char}" if char in "\\.[]" else char
                    for char in escaped_key
                )
            child = f"{path}.{escaped_key}" if path else escaped_key
            if key not in left or key not in right:
                changed.append(child)
            else:
                changed.extend(
                    _changed_payload_paths(left[key], right[key], path=child)
                )
        return changed
    if isinstance(left, list) and isinstance(right, list):
        changed = []
        for index in range(min(len(left), len(right))):
            changed.extend(
                _changed_payload_paths(
                    left[index], right[index], path=f"{path}[{index}]"
                )
            )
        if len(left) != len(right):
            changed.extend(
                f"{path}[{index}]"
                for index in range(min(len(left), len(right)), len(left))
            )
            changed.extend(
                f"{path}[{index}]"
                for index in range(min(len(left), len(right)), len(right))
            )
            changed.append(f"{path}.length" if path else "length")
        return changed
    left_canonical = _canonical_json_bytes(left)
    right_canonical = _canonical_json_bytes(right)
    return (
        []
        if left_canonical is not None and left_canonical == right_canonical
        else [path]
    )


def evaluate_group_factor_sensitivity(
    baseline_payload: Mapping[str, Any] | None,
    sensitivity_payload: Mapping[str, Any] | None,
    *,
    baseline_expected_bindings: Mapping[str, Any] | None,
    baseline_expected_payload_sha256: str | None,
    sensitivity_expected_bindings: Mapping[str, Any] | None,
    sensitivity_expected_payload_sha256: str | None,
    expected_sensitivity_contract: Mapping[str, Any] | None,
    expected_sensitivity_binding: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Compare two predeclared Cg scenarios; never report criterion acceptance.

    The independent sensitivity contract and its expected binding belong to
    the coordinator. The contract must classify this as a composite scenario
    and enumerate exactly which input paths may change. The factor ratio is a
    dimensionless method sensitivity only, not the adopted criterion's
    demand/capacity ratio.
    """
    required_contract = (
        "contract_id",
        "source_id",
        "sha256",
        "review_status",
        "classification",
        "candidate_id",
        "revision_id",
        "group_id",
        "baseline_scenario_id",
        "sensitivity_scenario_id",
        "changed_input_paths",
    )
    if not isinstance(expected_sensitivity_contract, Mapping) or not isinstance(
        expected_sensitivity_binding, Mapping
    ):
        return _pending(
            "sensitivity_case_contract_and_independent_binding_required",
            missing_inputs=(
                "independent_sensitivity_case_contract",
                "independent_sensitivity_contract_binding",
            ),
        )
    if any(key not in expected_sensitivity_contract for key in required_contract):
        return _pending(
            "incomplete_sensitivity_case_contract",
            missing_inputs=("independent_sensitivity_case_contract",),
        )
    if not _sha256(expected_sensitivity_contract.get("sha256")):
        return _pending("invalid_sensitivity_contract_hash")
    observed_contract_sha256 = canonical_sensitivity_contract_sha256(
        expected_sensitivity_contract
    )
    if observed_contract_sha256 is None:
        return _pending("invalid_sensitivity_contract_content")
    if observed_contract_sha256 != expected_sensitivity_contract["sha256"].lower():
        return _pending("sensitivity_contract_content_digest_mismatch")
    if expected_sensitivity_contract.get("review_status") != "coordinator_reviewed":
        return _pending("sensitivity_case_contract_not_coordinator_reviewed")
    if expected_sensitivity_contract.get("classification") != "composite_scenario":
        return _pending("sensitivity_scenarios_must_be_classified_as_composite")
    changed_input_paths = expected_sensitivity_contract.get("changed_input_paths")
    if (
        not isinstance(changed_input_paths, list)
        or not changed_input_paths
        or any(
            not isinstance(path, str) or not path.strip()
            for path in changed_input_paths
        )
    ):
        return _pending("invalid_sensitivity_changed_input_paths")
    if any(
        not isinstance(expected_sensitivity_contract.get(key), str)
        or not expected_sensitivity_contract[key].strip()
        for key in required_contract
        if key not in ("sha256", "review_status", "changed_input_paths")
    ):
        return _pending("invalid_sensitivity_contract_identity")
    if (
        not isinstance(expected_sensitivity_binding.get("contract_id"), str)
        or not isinstance(expected_sensitivity_binding.get("source_id"), str)
        or not isinstance(expected_sensitivity_binding.get("sha256"), str)
        or not _sha256(expected_sensitivity_binding.get("sha256"))
    ):
        return _pending("invalid_independent_sensitivity_contract_binding")
    if (
        expected_sensitivity_binding.get("contract_id")
        != expected_sensitivity_contract.get("contract_id")
        or expected_sensitivity_binding.get("source_id")
        != expected_sensitivity_contract.get("source_id")
        or expected_sensitivity_binding["sha256"].lower()
        != expected_sensitivity_contract["sha256"].lower()
        or expected_sensitivity_binding.get("review_status") != "coordinator_reviewed"
    ):
        return _pending(
            "sensitivity_contract_does_not_match_independent_review_binding"
        )

    baseline = evaluate_group_action_factor(
        baseline_payload,
        expected_bindings=baseline_expected_bindings,
        expected_payload_sha256=baseline_expected_payload_sha256,
    )
    sensitivity = evaluate_group_action_factor(
        sensitivity_payload,
        expected_bindings=sensitivity_expected_bindings,
        expected_payload_sha256=sensitivity_expected_payload_sha256,
    )
    if (
        baseline["status"] != "calculated_method_only"
        or sensitivity["status"] != "calculated_method_only"
    ):
        return _pending(
            "baseline_or_sensitivity_case_not_calculated",
            missing_inputs=tuple(
                [f"baseline:{reason}" for reason in baseline["reason_codes"]]
                + [f"sensitivity:{reason}" for reason in sensitivity["reason_codes"]]
            ),
        )

    contract = expected_sensitivity_contract
    for key in ("candidate_id", "revision_id", "group_id"):
        if baseline[key] != contract[key] or sensitivity[key] != contract[key]:
            return _pending("sensitivity_contract_identity_mismatch")
    if baseline["scenario_id"] != contract["baseline_scenario_id"]:
        return _pending("baseline_scenario_id_mismatch")
    if sensitivity["scenario_id"] != contract["sensitivity_scenario_id"]:
        return _pending("sensitivity_scenario_id_mismatch")
    if baseline["case_id"] != sensitivity["case_id"]:
        return _pending("sensitivity_case_load_case_mismatch")

    if not isinstance(baseline_payload, Mapping) or not isinstance(
        sensitivity_payload, Mapping
    ):
        return _pending("sensitivity_payload_missing")
    actual_changed_paths = sorted(
        set(
            _changed_payload_paths(
                baseline_payload,
                sensitivity_payload,
                ignore_root_keys=frozenset(("scenario_id", "source_bindings")),
            )
        )
    )
    if actual_changed_paths != sorted(set(changed_input_paths)):
        return _pending("sensitivity_changed_input_paths_do_not_match_contract")

    try:
        ratio = sensitivity["cg"] / baseline["cg"]
    except (OverflowError, ZeroDivisionError):
        return _pending("sensitivity_ratio_arithmetic_failure")
    if not math.isfinite(ratio):
        return _pending("sensitivity_ratio_nonfinite")
    return {
        "status": "calculated_method_sensitivity_only",
        "reason_codes": [],
        "missing_inputs": [],
        "baseline_cg": baseline["cg"],
        "sensitivity_cg": sensitivity["cg"],
        "sensitivity_over_baseline_cg": ratio,
        "delta_cg": sensitivity["cg"] - baseline["cg"],
        "capacity": None,
        "criterion_disposition": "pending",
        "sensitivity_classification": "composite_scenario",
        "changed_input_paths": actual_changed_paths,
        "interpretation": "composite dimensionless change in Cg only; not the adopted criterion demand/capacity ratio",
        "sensitivity_contract_id": contract["contract_id"],
        "sensitivity_contract_sha256": contract["sha256"],
    }
