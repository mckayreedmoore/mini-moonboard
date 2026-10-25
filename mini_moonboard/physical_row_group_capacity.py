"""Source-bound, aggregate lateral capacity references for one dowel row.

This adapter is intentionally narrower than a connection solver.  It combines
the maintained NDS-2024 Cg evaluator with externally supplied, independently
bound single-fastener lateral Z references.  It retains every fastener force
and free couple, and always leaves complete group/connection acceptance
unresolved.  A caller must supply an explicit qualification record and an
independent digest; this module does not decide that the record is authoritative.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from typing import Any

from mini_moonboard.nds_2024_group_action import (
    evaluate_group_action_factor,
)

SCHEMA_VERSION = "physical_dowel_row_capacity_input/v1"
GROUP_FACTOR_SCHEMA_VERSION = "awc_nds_2024_group_factor_equation_input/v1"
N_TO_LBF = 0.22480894387096
MM_TO_IN = 1.0 / 25.4
NMM_TO_LBFIN = N_TO_LBF * MM_TO_IN
VECTOR_TOLERANCE = 1.0e-8
BALANCE_REL_TOLERANCE = 1.0e-8


def canonical_record_sha256(record: Mapping[str, Any] | None) -> str | None:
    """Return the strict canonical JSON digest used for coordinator pins."""
    if not isinstance(record, Mapping):
        return None
    try:
        encoded = json.dumps(
            record,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError, UnicodeError, RecursionError):
        return None
    return hashlib.sha256(encoded).hexdigest()


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _vec3(value: Any, *, label: str) -> tuple[float, float, float]:
    if (
        not isinstance(value, Sequence)
        or isinstance(value, (str, bytes))
        or len(value) != 3
        or any(not _finite(component) for component in value)
    ):
        raise ValueError(f"{label} must be a finite three-vector")
    return tuple(float(component) for component in value)  # type: ignore[return-value]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return math.fsum(a * b for a, b in zip(left, right, strict=True))


def _cross(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _add(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _sub(left: Sequence[float], right: Sequence[float]) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def _scale(vector: Sequence[float], scalar: float) -> tuple[float, float, float]:
    return tuple(component * scalar for component in vector)  # type: ignore[return-value]


def _norm(vector: Sequence[float]) -> float:
    return math.hypot(*vector)


def _unit(vector: Sequence[float], *, label: str) -> tuple[float, float, float]:
    length = _norm(vector)
    if not math.isfinite(length) or length <= 0:
        raise ValueError(f"{label} must be nonzero")
    return _scale(vector, 1.0 / length)


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _source_refs_are_pinned(value: Any) -> bool:
    if not isinstance(value, Mapping) or not value:
        return False
    for role, item in value.items():
        if (
            not isinstance(role, str)
            or not role.strip()
            or not isinstance(item, Mapping)
            or not isinstance(item.get("source_id"), str)
            or not item["source_id"].strip()
            or not _sha256(item.get("sha256"))
        ):
            return False
    return True


def _same_sources(observed: Any, expected: Any) -> bool:
    if not _source_refs_are_pinned(observed) or not _source_refs_are_pinned(expected):
        return False
    return observed == expected


def _pending(reason: str, *, missing: Sequence[str] = ()) -> dict[str, Any]:
    return {
        "status": "pending",
        "reason_codes": [reason],
        "missing_inputs": list(missing),
        "cg": None,
        "group_lateral_capacity_lbf": None,
        "row_lateral_utilization": None,
        "row_lateral_subcheck": "pending",
        "complete_group_capacity": None,
        "complete_group_pass": None,
    }


def evaluate_nds_group_factor_equation(
    record: Mapping[str, Any] | None,
    *,
    expected_record_sha256: str | None,
    expected_sources: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Evaluate the NDS Eq. 11.3-1 scalar from pinned EA/row inputs.

    This is a separate equation engine from the maintained wood-to-wood
    record validator below. It supports the documented wood-to-wood and
    wood-to-metal gamma constants, but only calculates the scalar equation;
    it does not establish that the caller's effective EA, physical row,
    material assignment, force alignment, or capacity mapping is applicable.
    Inputs use inches and lbf throughout.
    """
    if not isinstance(record, Mapping):
        return _pending("missing_group_factor_record")
    if record.get("schema") != GROUP_FACTOR_SCHEMA_VERSION:
        return _pending("unsupported_group_factor_schema")
    if not _same_sources(record.get("source_bindings"), expected_sources):
        return _pending("group_factor_source_binding_mismatch_or_incomplete")
    observed_sha = canonical_record_sha256(record)
    if (
        not _sha256(expected_record_sha256)
        or observed_sha is None
        or observed_sha != expected_record_sha256.lower()
    ):
        return _pending("group_factor_record_digest_mismatch_or_missing")

    n = record.get("fastener_count")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        return _pending("invalid_fastener_count")
    values = {
        key: record.get(key)
        for key in (
            "pitch_in",
            "diameter_in",
            "EA_main_lbf",
            "EA_side_lbf",
        )
    }
    if any(not _finite(value) or value <= 0 for value in values.values()):
        return _pending("invalid_or_missing_positive_equation_input")
    kind = record.get("connection_kind")
    gamma_coefficients = {"wood_wood": 180_000.0, "wood_metal": 270_000.0}
    if kind not in gamma_coefficients:
        return _pending("unsupported_connection_kind")

    pitch = float(values["pitch_in"])
    diameter = float(values["diameter_in"])
    ea_main = float(values["EA_main_lbf"])
    ea_side = float(values["EA_side_lbf"])
    if diameter > 1.0:
        return _pending("diameter_outside_NDS_11_3_6_1_scope")

    if diameter < 0.25:
        gamma = None
        cg = 1.0
        u = None
        m = None
        re = min(ea_main, ea_side) / max(ea_main, ea_side)
        method_note = "NDS sub-1/4-inch Cg=1.0 exception"
    else:
        try:
            gamma = gamma_coefficients[kind] * diameter**1.5
            re = min(ea_main, ea_side) / max(ea_main, ea_side)
            u = 1.0 + gamma * pitch / 2.0 * (1.0 / ea_main + 1.0 / ea_side)
            if not math.isfinite(u) or u <= 1.0:
                return _pending("group_factor_equation_intermediate_out_of_range")
            m = 1.0 / (u + math.sqrt(u * u - 1.0))
            numerator = m * (1.0 - m ** (2 * n))
            denominator = n * ((1.0 + re * m**n) * (1.0 + m) - 1.0 + m ** (2 * n))
            cg = numerator / denominator * ((1.0 + re) / (1.0 - m))
        except (OverflowError, ZeroDivisionError, ValueError):
            return _pending("group_factor_equation_arithmetic_failure")
        if not math.isfinite(cg) or not 0.0 < cg <= 1.0 + 1.0e-10:
            return _pending("group_factor_equation_result_outside_range")
        rounding_clamped = cg > 1.0
        if rounding_clamped:
            cg = 1.0
        method_note = "NDS-2024 Eq. 11.3-1 scalar equation only"

    return {
        "status": "calculated_method_only",
        "reason_codes": [],
        "input_record_sha256": observed_sha,
        "candidate_id": record.get("candidate_id"),
        "revision_id": record.get("revision_id"),
        "group_id": record.get("group_id"),
        "scenario_id": record.get("scenario_id"),
        "case_id": record.get("case_id"),
        "fastener_count": n,
        "pitch_in": pitch,
        "diameter_in": diameter,
        "EA_main_lbf": ea_main,
        "EA_side_lbf": ea_side,
        "RE": re,
        "gamma_lbf_per_in": gamma,
        "u": u,
        "m": m,
        "cg": cg,
        "cg_rounding_clamped_to_unit_limit": (
            False if diameter < 0.25 else rounding_clamped
        ),
        "connection_kind": kind,
        "method_note": method_note,
        "physical_applicability": "caller must establish separately; not evaluated",
        "capacity": None,
        "criterion_disposition": "pending",
    }


def _parse_fasteners(
    row_record: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], tuple[float, float, float]]:
    axis = _unit(
        _vec3(row_record.get("row_axis_xyz"), label="row_axis_xyz"),
        label="row_axis_xyz",
    )
    entries = row_record.get("fasteners")
    if not isinstance(entries, list) or len(entries) < 2:
        raise ValueError("row requires at least two fastener wrench records")
    ids: set[str] = set()
    parsed: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise TypeError("malformed fastener wrench record")
        fastener_id = entry.get("fastener_id")
        if (
            not isinstance(fastener_id, str)
            or not fastener_id.strip()
            or fastener_id in ids
        ):
            raise ValueError("duplicate or missing fastener_id")
        ids.add(fastener_id)
        point = _vec3(entry.get("point_xyz_mm"), label="point_xyz_mm")
        bolt_axis = _unit(
            _vec3(entry.get("bolt_axis_xyz"), label="bolt_axis_xyz"),
            label="bolt_axis_xyz",
        )
        force = _vec3(entry.get("force_xyz_n"), label="force_xyz_n")
        moment = _vec3(
            entry.get("moment_xyz_nmm_at_point"),
            label="moment_xyz_nmm_at_point",
        )
        moment_point = _vec3(
            entry.get("moment_point_xyz_mm"), label="moment_point_xyz_mm"
        )
        z_ref = entry.get("single_bolt_Z_lbf")
        if not _finite(z_ref) or z_ref <= 0:
            raise ValueError("each fastener needs a positive single-bolt Z reference")
        z_source = entry.get("single_bolt_source_id")
        if not isinstance(z_source, str) or not z_source.strip():
            raise ValueError("each single-bolt Z needs a source identifier")
        lateral = _sub(force, _scale(bolt_axis, _dot(force, bolt_axis)))
        axial = _dot(force, bolt_axis)
        parsed.append(
            {
                "fastener_id": fastener_id,
                "point_mm": point,
                "bolt_axis": bolt_axis,
                "force_n": force,
                "lateral_force_n": lateral,
                "axial_force_n": axial,
                "moment_at_point_nmm": moment,
                "moment_point_mm": moment_point,
                "single_bolt_Z_lbf": float(z_ref),
                "single_bolt_source_id": z_source,
            }
        )
    return parsed, axis


def evaluate_physical_row_group_capacity(
    row_record: Mapping[str, Any] | None,
    *,
    expected_row_record_sha256: str | None,
    expected_row_sources: Mapping[str, Any] | None,
    nds_group_record: Mapping[str, Any] | None,
    expected_nds_bindings: Mapping[str, Any] | None,
    expected_nds_record_sha256: str | None,
) -> dict[str, Any]:
    """Evaluate one source-pinned lateral row subcheck and retain its full wrench.

    ``row_record`` uses N/mm/mm units and carries per-fastener 6D actions and
    single-fastener Z values.  The NDS payload uses its documented lbf/in
    input contract.  Positions, row axes, fastener IDs, and total lateral force
    must join exactly within documented numeric tolerances.  Cg is applied
    once to ``n * min(Z)``; it is never multiplied into per-fastener actions.

    The function reports a lateral-row result only.  Non-row force, axial
    capture, point moments, splitting, end/edge and other joint criteria remain
    separately visible; complete group/connection acceptance is always null.
    The coordinator must supply a canonical digest and source bindings for
    the row record.  Their presence proves byte identity only, not source
    authority or the truth of a caller's explicit qualification statement.
    """
    if not isinstance(row_record, Mapping):
        return _pending("missing_source_bound_row_record", missing=("row_record",))
    if row_record.get("schema") != SCHEMA_VERSION:
        return _pending("unsupported_row_record_schema")
    if not _same_sources(row_record.get("source_bindings"), expected_row_sources):
        return _pending("row_source_binding_mismatch_or_incomplete")
    observed_row_sha = canonical_record_sha256(row_record)
    if (
        not _sha256(expected_row_record_sha256)
        or observed_row_sha is None
        or observed_row_sha != expected_row_record_sha256.lower()
    ):
        return _pending("row_record_digest_mismatch_or_missing")

    qualification = row_record.get("qualification")
    if not isinstance(qualification, Mapping):
        return _pending("explicit_row_qualification_required")
    qualification_status = qualification.get("status")
    if qualification_status not in {
        "independently_source_bound",
        "conditional_scenario",
    }:
        return _pending("row_qualification_not_explicitly_supported")
    for key in ("basis", "row_ownership", "load_path_basis"):
        if (
            not isinstance(qualification.get(key), str)
            or not qualification[key].strip()
        ):
            return _pending("row_qualification_record_incomplete", missing=(key,))

    identity_keys = ("candidate_id", "revision_id", "group_id")
    if any(
        not isinstance(row_record.get(key), str) or not row_record[key].strip()
        for key in identity_keys
    ):
        return _pending("row_identity_fields_missing")
    if (
        not isinstance(row_record.get("case_id"), str)
        or not row_record["case_id"].strip()
        or not isinstance(row_record.get("scenario_id"), str)
        or not row_record["scenario_id"].strip()
    ):
        return _pending("row_case_or_scenario_identity_missing")

    try:
        fasteners, row_axis = _parse_fasteners(row_record)
        reference_mm = _vec3(
            row_record.get("reference_point_xyz_mm"), label="reference_point_xyz_mm"
        )
    except (TypeError, ValueError) as exc:
        return _pending(f"invalid_row_record:{exc}")

    if not isinstance(nds_group_record, Mapping):
        return _pending("missing_NDS_group_record")
    nds_result = evaluate_group_action_factor(
        nds_group_record,
        expected_bindings=expected_nds_bindings,
        expected_payload_sha256=expected_nds_record_sha256,
    )
    if any(row_record[key] != nds_group_record.get(key) for key in identity_keys):
        return _pending("NDS_and_wrench_candidate_revision_or_group_identity_mismatch")
    if row_record["scenario_id"] != nds_group_record.get("scenario_id"):
        return _pending("NDS_and_wrench_scenario_identity_mismatch")

    # Source-bound force and couple reduction, retaining all six wrench terms.
    lateral_sum_n = (0.0, 0.0, 0.0)
    axial_sum_n = 0.0
    row_forces_lbf: list[float] = []
    transverse_forces_lbf: list[tuple[float, float, float]] = []
    total_moment_about_reference_nmm = (0.0, 0.0, 0.0)
    per_fastener: list[dict[str, Any]] = []
    for fastener in fasteners:
        lateral = fastener["lateral_force_n"]
        axial = fastener["axial_force_n"]
        row_component_n = _dot(lateral, row_axis)
        row_component = row_component_n * N_TO_LBF
        transverse_n = _sub(lateral, _scale(row_axis, row_component_n))
        r_moment = _sub(fastener["moment_point_mm"], reference_mm)
        moment = _add(
            fastener["moment_at_point_nmm"],
            _cross(r_moment, _add(lateral, _scale(fastener["bolt_axis"], axial))),
        )
        total_moment_about_reference_nmm = _add(
            total_moment_about_reference_nmm, moment
        )
        # Keep the full resultant force and the axial separation explicit.
        lateral_sum_n = _add(lateral_sum_n, lateral)
        axial_sum_n += axial
        row_forces_lbf.append(row_component)
        transverse_forces_lbf.append(_scale(transverse_n, N_TO_LBF))
        per_fastener.append(
            {
                "fastener_id": fastener["fastener_id"],
                "lateral_force_xyz_N": list(lateral),
                "row_force_signed_lbf": row_component,
                "transverse_force_xyz_lbf": list(_scale(transverse_n, N_TO_LBF)),
                "axial_force_signed_N": axial,
                "moment_xyz_Nmm_at_source_point": list(fastener["moment_at_point_nmm"]),
                "moment_point_xyz_mm": list(fastener["moment_point_mm"]),
                "transported_total_moment_xyz_Nmm": list(moment),
                "single_bolt_Z_lbf": fastener["single_bolt_Z_lbf"],
                "single_bolt_source_id": fastener["single_bolt_source_id"],
            }
        )

    numeric_sums = (
        *lateral_sum_n,
        axial_sum_n,
        *total_moment_about_reference_nmm,
        *row_forces_lbf,
        *(component for vector in transverse_forces_lbf for component in vector),
    )
    if not all(math.isfinite(value) for value in numeric_sums):
        return _pending("derived_group_wrench_overflowed_finite_range")

    nds_geometry = (
        nds_group_record.get("group_geometry")
        if isinstance(nds_group_record, Mapping)
        else None
    )
    if not isinstance(nds_geometry, Mapping):
        return _pending("NDS_group_geometry_missing_or_malformed")
    nds_fasteners = nds_geometry.get("fasteners", [])
    if not isinstance(nds_fasteners, list) or len(nds_fasteners) != len(fasteners):
        return _pending("NDS_and_wrench_fastener_count_mismatch")
    expected_ids = [item["fastener_id"] for item in fasteners]
    nds_by_id = {
        item.get("fastener_id"): item
        for item in nds_fasteners
        if isinstance(item, Mapping)
    }
    if set(nds_by_id) != set(expected_ids):
        return _pending("NDS_and_wrench_fastener_ids_mismatch")
    for item in fasteners:
        try:
            nds_point = _vec3(
                nds_by_id[item["fastener_id"]].get("center_in"),
                label="NDS fastener center_in",
            )
        except ValueError:
            return _pending("NDS_fastener_center_missing_or_malformed")
        expected_point = _scale(item["point_mm"], MM_TO_IN)
        if _norm(_sub(nds_point, expected_point)) > 1.0e-6:
            return _pending("NDS_and_wrench_fastener_positions_mismatch")
    try:
        nds_axis = _vec3(nds_geometry.get("row_axis_xyz"), label="NDS row axis")
    except ValueError:
        return _pending("NDS_row_axis_missing_or_malformed")
    try:
        nds_axis_unit = _unit(nds_axis, label="NDS row axis")
    except ValueError:
        return _pending("NDS_row_axis_missing_or_invalid")
    if _norm(_cross(row_axis, nds_axis_unit)) > VECTOR_TOLERANCE:
        return _pending("NDS_and_wrench_row_axis_mismatch")

    resultant_lbf = _scale(lateral_sum_n, N_TO_LBF)
    nds_load = (
        nds_group_record.get("load_case")
        if isinstance(nds_group_record, Mapping)
        else None
    )
    if not isinstance(nds_load, Mapping):
        return _pending("NDS_lateral_resultant_missing")
    if nds_load.get("case_id") != row_record.get("case_id"):
        return _pending("NDS_and_wrench_case_identity_mismatch")
    try:
        nds_resultant = _vec3(
            nds_load.get("lateral_resultant_xyz_lbf"),
            label="NDS lateral resultant",
        )
    except ValueError:
        return _pending("NDS_lateral_resultant_missing_or_malformed")
    balance_scale = max(1.0, _norm(resultant_lbf), _norm(nds_resultant))
    lateral_balance_error = _norm(_sub(resultant_lbf, nds_resultant))

    if nds_result.get("status") != "calculated_method_only":
        nds_pending = dict(nds_result)
        return {
            "status": "pending",
            "reason_codes": ["NDS_group_factor_not_applicable_or_not_source_bound"],
            "cg": nds_result.get("cg"),
            "nds_group_factor": nds_pending,
            "row_record_sha256": observed_row_sha,
            "row_qualification_status": qualification_status,
            "row_axis_xyz": list(row_axis),
            "reference_point_xyz_mm": list(reference_mm),
            "fasteners": per_fastener,
            "signed_group_lateral_resultant_xyz_lbf": list(resultant_lbf),
            "lateral_resultant_balance_error_lbf": lateral_balance_error,
            "group_lateral_row_demand_sum_abs_lbf": math.fsum(
                abs(value) for value in row_forces_lbf
            ),
            "group_lateral_row_signed_sum_lbf": math.fsum(row_forces_lbf),
            "group_transverse_lateral_resultant_xyz_lbf": list(
                _sub(resultant_lbf, _scale(row_axis, _dot(resultant_lbf, row_axis)))
            ),
            "sum_axial_capture_N": axial_sum_n,
            "transported_total_moment_about_reference_xyz_Nmm": list(
                total_moment_about_reference_nmm
            ),
            "group_lateral_capacity_lbf": None,
            "row_lateral_utilization": None,
            "row_lateral_subcheck": "pending_NDS_Cg",
            "unresolved_conditions": [
                "NDS Cg eligibility/source binding",
                "transverse lateral force",
                "axial capture",
                "free couples and eccentric group action",
                "wood splitting/net section and end/edge conditions",
                "full simultaneous six-wrench group/connection interaction",
            ],
            "complete_group_capacity": None,
            "complete_group_pass": None,
        }

    if lateral_balance_error > BALANCE_REL_TOLERANCE * balance_scale:
        return _pending("NDS_and_wrench_lateral_resultant_mismatch")

    total_row_force = math.fsum(row_forces_lbf)
    row_force_demand = math.fsum(abs(value) for value in row_forces_lbf)
    if abs(total_row_force) == 0:
        return _pending("zero_lateral_row_demand")
    if not all(
        value * total_row_force >= -BALANCE_REL_TOLERANCE for value in row_forces_lbf
    ):
        return _pending(
            "opposing_fastener_row_force_signs_outside_unidirectional_row_scope"
        )

    # NDS Eq. 11.3-1 and the aggregate n*Cg*Z row check are aligned-row
    # criteria. A net resultant parallel to the row is insufficient: two
    # fasteners can carry equal and opposite transverse components whose sum
    # vanishes while each fastener still has a non-row lateral action. Keep
    # that complete wrench visible and fail the scalar row route closed.
    transverse_magnitudes = [_norm(vector) for vector in transverse_forces_lbf]
    individual_lateral_magnitudes = [
        _norm(_scale(item["lateral_force_n"], N_TO_LBF)) for item in fasteners
    ]
    transverse_tolerance_by_fastener = [
        BALANCE_REL_TOLERANCE * max(1.0, magnitude)
        for magnitude in individual_lateral_magnitudes
    ]
    misaligned_fastener_ids = [
        fastener["fastener_id"]
        for fastener, transverse, tolerance in zip(
            fasteners,
            transverse_magnitudes,
            transverse_tolerance_by_fastener,
            strict=True,
        )
        if transverse > tolerance
    ]
    if misaligned_fastener_ids:
        transverse_sum = _sub(
            resultant_lbf, _scale(row_axis, _dot(resultant_lbf, row_axis))
        )
        return {
            "status": "pending",
            "reason_codes": [
                "individual_fastener_lateral_force_not_parallel_to_NDS_row"
            ],
            "cg": None,
            "nds_group_factor": nds_result,
            "row_record_sha256": observed_row_sha,
            "row_qualification_status": qualification_status,
            "row_qualification_basis": qualification.get("basis"),
            "row_axis_xyz": list(row_axis),
            "reference_point_xyz_mm": list(reference_mm),
            "fastener_count": len(fasteners),
            "fasteners": per_fastener,
            "misaligned_fastener_ids": misaligned_fastener_ids,
            "signed_group_lateral_resultant_xyz_lbf": list(resultant_lbf),
            "lateral_resultant_balance_error_lbf": lateral_balance_error,
            "group_lateral_row_demand_sum_abs_lbf": row_force_demand,
            "group_lateral_row_signed_sum_lbf": total_row_force,
            "group_transverse_lateral_resultant_xyz_lbf": list(transverse_sum),
            "max_individual_transverse_lateral_force_lbf": max(
                transverse_magnitudes, default=0.0
            ),
            "sum_axial_capture_N": axial_sum_n,
            "transported_total_moment_about_reference_xyz_Nmm": list(
                total_moment_about_reference_nmm
            ),
            "group_lateral_capacity_lbf": None,
            "row_lateral_utilization": None,
            "row_lateral_subcheck": "pending_individual_force_projection",
            "unresolved_conditions": [
                "individual fastener lateral actions are not parallel to the NDS row axis",
                "a source-supported coupled decomposition for simultaneous row and transverse bolt forces",
                "axial capture",
                "free couples and eccentric group action",
                "wood splitting/net section and end/edge conditions",
                "full simultaneous six-wrench group/connection interaction",
            ],
            "complete_group_capacity": None,
            "complete_group_pass": None,
        }

    qualification_basis = qualification.get("basis")
    # An explicit conditional qualification can produce a labeled scenario
    # ratio; it is never reported as an adopted/current connection pass.
    z_min = min(item["single_bolt_Z_lbf"] for item in fasteners)
    cg = float(nds_result["cg"])
    group_capacity = len(fasteners) * cg * z_min
    utilization = row_force_demand / group_capacity
    if not math.isfinite(utilization) or group_capacity <= 0:
        return _pending("invalid_aggregate_row_capacity_or_demand")

    transverse_sum = _sub(
        resultant_lbf, _scale(row_axis, _dot(resultant_lbf, row_axis))
    )
    moment_norm_lbfin = _norm(_scale(total_moment_about_reference_nmm, NMM_TO_LBFIN))
    axial_norm_lbf = abs(axial_sum_n) * N_TO_LBF
    return {
        "status": "calculated_method_only",
        "reason_codes": [],
        "row_record_sha256": observed_row_sha,
        "row_qualification_status": qualification_status,
        "row_qualification_basis": qualification_basis,
        "qualification_authority": "caller-supplied and coordinator-pinned; not verified by this helper",
        "nds_group_factor": nds_result,
        "row_axis_xyz": list(row_axis),
        "reference_point_xyz_mm": list(reference_mm),
        "fastener_count": len(fasteners),
        "fasteners": per_fastener,
        "signed_group_lateral_resultant_xyz_lbf": list(resultant_lbf),
        "lateral_resultant_balance_error_lbf": lateral_balance_error,
        "group_lateral_row_demand_sum_abs_lbf": row_force_demand,
        "group_lateral_row_signed_sum_lbf": total_row_force,
        "group_transverse_lateral_resultant_xyz_lbf": list(transverse_sum),
        "max_individual_transverse_lateral_force_lbf": max(
            transverse_magnitudes, default=0.0
        ),
        "sum_axial_capture_N": axial_sum_n,
        "transported_total_moment_about_reference_xyz_Nmm": list(
            total_moment_about_reference_nmm
        ),
        "transported_total_moment_norm_lbfin": moment_norm_lbfin,
        "sum_axial_capture_lbf": axial_norm_lbf,
        "minimum_single_bolt_Z_lbf": z_min,
        "group_lateral_capacity_lbf": group_capacity,
        "group_capacity_formula": "n * Cg * min(single-bolt Z); Cg applied once at row level",
        "row_lateral_utilization": utilization,
        "row_lateral_subcheck": (
            "conditional_scenario_only"
            if qualification_status == "conditional_scenario"
            else "source_bound_lateral_row_only"
        ),
        "unresolved_conditions": [
            "non-row/transverse lateral force",
            "axial capture",
            "free couples and eccentric group action",
            "wood splitting/net section and end/edge conditions",
            "other member and fitting limit states",
            "complete simultaneous six-wrench group/connection interaction",
        ],
        "complete_group_capacity": None,
        "complete_group_pass": None,
    }
