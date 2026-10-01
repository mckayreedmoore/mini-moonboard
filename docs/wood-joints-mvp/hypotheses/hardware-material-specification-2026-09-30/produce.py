#!/usr/bin/env python3
"""Produce a pinned, geometry-derived hardware requirement screen.

The producer reads frozen JSON and local source records only. It does not
import CAD/FEA modules, select products, infer actual thread locations, or
assign resistance. Use --write to refresh the three owned outputs and
--verify for an exact deterministic replay check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections.abc import Iterable
from itertools import pairwise
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ARTIFACT_ID = "hardware-material-specification-2026-09-30"
GRIP_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json"
COVERAGE_PATH = "docs/wood-joints-mvp/current-hardware-coverage.json"
CATALOG_PATH = "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-bolt-catalog-screen-attempt01/catalog-screen.json"

# These content hashes are deliberately fixed here. --write refuses changed
# inputs; a source update needs a reviewed pin change in this producer.
PINNED_INPUTS: tuple[dict[str, str], ...] = (
    {
        "id": "grip_screen_attempt02",
        "path": GRIP_PATH,
        "sha256": "9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a",
        "role": "Frozen 92-axis geometry, receiver intervals, role occupancy, and underhead datum.",
    },
    {
        "id": "current_hardware_coverage",
        "path": COVERAGE_PATH,
        "sha256": "011dcf33c8a99d5072623db06388ffc0e409c8824be15015e68b454c31e7305d",
        "role": "Candidate family partition and separate 12 retained starting-stack IDs.",
    },
    {
        "id": "current_bolt_catalog_screen",
        "path": CATALOG_PATH,
        "sha256": "0184e45a3991c3dfbd236696a5d6a50417299177e23e287b9279240b53adc3a8",
        "role": "Screened length-class comparisons and catalog-lead IDs; no selection.",
    },
    {
        "id": "bolt_thread_boundary_screen",
        "path": "docs/wood-joints-mvp/current-bolt-thread-boundary-screen-2026-09-27.md",
        "sha256": "27397d18eb1f6d3039295210b72ab04ed5b16a30f3625303212c519c60a6afd5",
        "role": "Current standard/product thread-boundary limits and unresolved matched fit.",
    },
    {
        "id": "bolt_dimension_source_correction",
        "path": "docs/wood-joints-mvp/bolt-dimension-source-correction.md",
        "sha256": "3933bf5bf9d2491b4618691a77d75f929dfc838da7dbd4fff02de9e986846555",
        "role": "Correct ASME LG/LB attribution and underhead datum interpretation.",
    },
    {
        "id": "thread_alternative_spec_research",
        "path": "docs/wood-joints-mvp/current-bolt-thread-alternative-spec-research-2026-09-27.md",
        "sha256": "658b1e141b5548b94631ff8f399f45d5796aa03c1e4bea36c8e3ef5b093b786a",
        "role": "Nut finished-height standard range and active-thread/chamfer evidence gap.",
    },
    {
        "id": "hardware_schedule",
        "path": "docs/wood-joints-mvp/current-hardware-schedule.md",
        "sha256": "47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa",
        "role": "Current candidate and retained-stack piece roles/counts.",
    },
    {
        "id": "ordinary_hardware_basis",
        "path": "docs/wood-joints-mvp/current-ordinary-hardware-basis.md",
        "sha256": "72ffabef1e449234622f4682eaefcde787abc1b56fbe8814b1e843d1581d1ecc",
        "role": "ASME B18.2.1 Table 12/13 class-boundary values and distinct LG/LB meanings.",
    },
    {
        "id": "ordinary_spacer_and_tip_screen",
        "path": "docs/wood-joints-mvp/current-ordinary-hardware-spacer-option.md",
        "sha256": "6dbbc841e8122061cb23d65595d78419880897218aa9fb99afa2eaa62c578c4d",
        "role": "Current WJ24 physical 3.175 mm tip projection and no-tail-thread requirement.",
    },
    {
        "id": "center_sandwich_quarter_thread_basis",
        "path": "docs/wood-joints-mvp/current-center-sandwich-hardware-options.md",
        "sha256": "644ddb4c42b3c14513739f96e44dc4d860de42ab4f4431af1d963ec1c6ef4a1c",
        "role": "NDS 2024 §12.3.7.2 quarter-member thread-bearing screen and limits.",
    },
    {
        "id": "nds_bolt_resistance_basis",
        "path": "docs/wood-joints-mvp/bolt-resistance-basis.md",
        "sha256": "1b5e1a261735f7630c0c45fe505a4755227dd88d52091f112141f0c1332f0d80",
        "role": "NDS full-body versus thread-root diameter method boundary.",
    },
    {
        "id": "wj03_dimensional_range_example",
        "path": "docs/wood-joints-mvp/wj03-hardware-procurement.md",
        "sha256": "dba2e10295358859d7bae5a9a9b1c71382aa212441186022be3fbdc3579db3fc",
        "role": "Documented 1/4 in washer ranges; cross-check for dimensional arithmetic only.",
    },
)

OUT_REQUIREMENTS = HERE / "requirements.json"
OUT_PINS = HERE / "source-pins.json"
OUT_MARKDOWN = HERE / "requirements.md"

# Published dimensional inputs; recorded as source-bounded comparisons, not
# selected or inspected products. Exact conversions are 25.4 mm per inch.
WASHER_THICKNESS_IN = (0.051, 0.080)
NUT_FINISHED_HEIGHT_IN = (0.212, 0.226)
MM_PER_INCH = 25.4
THREAD_PITCH_IN = 0.050
PHYSICAL_PROTRUSION_THREADS = 3
PHYSICAL_TIP_PROJECTION_MM = THREAD_PITCH_IN * PHYSICAL_PROTRUSION_THREADS * MM_PER_INCH
INHERITED_WJ24_GEOMETRY_TIP_ALLOWANCE_MM = 3.175
HEAD_WASHER_ROLE = "head_washer"
NUT_WASHER_ROLE = "nut_washer"
GEOMETRY_TOLERANCE_MM = 1.0e-6
DATUM_CONTACT_TOLERANCE_MM = 1.0e-4
EXPECTED_CANDIDATE_AXES = 92
EXPECTED_RETAINED_AXES = 12
EXPECTED_RETAINED_FAMILIES = 3


class RequirementError(ValueError):
    """Raised when a pinned source or expected inventory fails closed."""


def round_mm(value: float) -> float:
    """Serialize derived millimetres to a stable six-decimal representation."""
    result = round(float(value), 6)
    return 0.0 if result == 0 else result


def mm_range(values_in: Iterable[float]) -> list[float]:
    return [round_mm(float(value) * MM_PER_INCH) for value in values_in]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_source_hashes(root: Path, pins: Iterable[dict[str, str]] = PINNED_INPUTS) -> None:
    for pin in pins:
        path = root / pin["path"]
        if not path.is_file():
            raise RequirementError(f"Pinned source is missing: {pin['path']}")
        observed = sha256_file(path)
        if observed != pin["sha256"]:
            raise RequirementError(
                f"Pinned source changed: {pin['path']} expected {pin['sha256']}, found {observed}"
            )


def normalize_interval_to_underhead(
    interval: Iterable[float],
    *,
    coordinate_origin: str,
    underhead_global_axis_mm: float | None = None,
) -> tuple[float, float]:
    """Convert an axial interval only when its coordinate origin is explicit."""
    values = tuple(float(value) for value in interval)
    if len(values) != 2 or not all(math.isfinite(value) for value in values) or values[1] <= values[0]:
        raise RequirementError(f"Invalid axial interval: {values!r}")
    if coordinate_origin == "underhead_relative":
        return values[0], values[1]
    if coordinate_origin == "global_axis":
        if underhead_global_axis_mm is None or not math.isfinite(float(underhead_global_axis_mm)):
            raise RequirementError("A finite underhead global-axis datum is required for global intervals")
        datum = float(underhead_global_axis_mm)
        return values[0] - datum, values[1] - datum
    raise RequirementError(f"Unsupported interval coordinate origin: {coordinate_origin!r}")


def quarter_thread_lb_requirement(a_mm: float, b_mm: float) -> dict[str, float]:
    """Return the NDS nominal-D geometric bound for one contiguous member interval."""
    a = float(a_mm)
    b = float(b_mm)
    if not math.isfinite(a) or not math.isfinite(b) or b <= a:
        raise RequirementError(f"Invalid member interval [{a_mm}, {b_mm}]")
    thickness = b - a
    maximum_thread_bearing = thickness / 4.0
    return {
        "member_interval_thickness_mm": round_mm(thickness),
        "maximum_thread_bearing_in_member_mm": round_mm(maximum_thread_bearing),
        "minimum_LB_underhead_to_last_thread_scratch_mm": round_mm(b - maximum_thread_bearing),
    }


def evaluate_full_thread_profile(
    first_full_thread_start_mm: float,
    last_full_thread_end_mm: float,
    *,
    earliest_nut_bearing_plane_mm: float,
    latest_nut_far_face_mm: float,
) -> bool:
    """Test a declared sufficient profile envelope; this is not functional fit."""
    values = tuple(float(value) for value in (
        first_full_thread_start_mm,
        last_full_thread_end_mm,
        earliest_nut_bearing_plane_mm,
        latest_nut_far_face_mm,
    ))
    if not all(math.isfinite(value) for value in values):
        raise RequirementError("Thread-profile and nut-envelope coordinates must be finite")
    start, end, near, far = values
    if end <= start or far <= near:
        raise RequirementError("Thread profile and nut envelope must have positive length")
    return start <= near and end >= far


def nut_stack_envelope(
    far_wood_face_underhead_mm: float,
    *,
    modeled_head_washer_thickness_mm: float,
    head_washer_range_mm: Iterable[float],
    nut_washer_range_mm: Iterable[float],
    nut_finished_height_range_mm: Iterable[float],
    physical_tip_projection_mm: float,
) -> dict[str, float]:
    """Project published washer/nut dimensions from the frozen wood endpoint."""
    far_wood = float(far_wood_face_underhead_mm)
    modeled_head = float(modeled_head_washer_thickness_mm)
    projection = float(physical_tip_projection_mm)
    head_range = tuple(float(value) for value in head_washer_range_mm)
    washer_range = tuple(float(value) for value in nut_washer_range_mm)
    nut_range = tuple(float(value) for value in nut_finished_height_range_mm)
    if (
        len(head_range) != 2 or len(washer_range) != 2 or len(nut_range) != 2
        or not all(math.isfinite(value) for value in (far_wood, modeled_head, projection, *head_range, *washer_range, *nut_range))
        or modeled_head <= 0 or projection < 0
        or head_range[0] <= 0 or washer_range[0] <= 0 or nut_range[0] <= 0
        or head_range[1] < head_range[0] or washer_range[1] < washer_range[0] or nut_range[1] < nut_range[0]
    ):
        raise RequirementError("Invalid washer/nut stack envelope inputs")
    earliest_bearing = far_wood + head_range[0] - modeled_head + washer_range[0]
    latest_bearing = far_wood + head_range[1] - modeled_head + washer_range[1]
    earliest_far_face = earliest_bearing + nut_range[0]
    latest_far_face = latest_bearing + nut_range[1]
    return {
        "earliest_nut_bearing_plane_mm": round_mm(earliest_bearing),
        "latest_nut_bearing_plane_mm": round_mm(latest_bearing),
        "earliest_nut_far_face_mm": round_mm(earliest_far_face),
        "latest_nut_far_face_mm": round_mm(latest_far_face),
        "minimum_physical_tip_target_mm": round_mm(latest_far_face + projection),
    }


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def read_json(root: Path, relative_path: str) -> dict[str, Any]:
    try:
        return json.loads((root / relative_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RequirementError(f"Cannot read {relative_path}: {exc}") from exc


def interval_role(axis: dict[str, Any], role_name: str) -> list[list[float]]:
    try:
        intervals = axis["hardware_roles"][role_name]["union_intervals_from_underhead_mm"]
    except (KeyError, TypeError) as exc:
        raise RequirementError(f"{axis.get('axis_id', '<axis>')}: missing modeled {role_name} role") from exc
    normalized = []
    for interval in intervals:
        a, b = normalize_interval_to_underhead(interval, coordinate_origin="underhead_relative")
        normalized.append([a, b])
    if not normalized:
        raise RequirementError(f"{axis['axis_id']}: empty modeled {role_name} interval")
    return normalized


def validate_inventory(
    grip: dict[str, Any], coverage: dict[str, Any], catalog: dict[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
    if grip.get("schema") != "wood_joint_current_grip_screen/v1":
        raise RequirementError("Unexpected frozen grip-screen schema")
    if grip.get("revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
        raise RequirementError("Unexpected geometry revision")
    axes = grip.get("axes")
    if not isinstance(axes, list) or len(axes) != EXPECTED_CANDIDATE_AXES:
        raise RequirementError(f"Expected {EXPECTED_CANDIDATE_AXES} current candidate axes")
    axis_by_id: dict[str, dict[str, Any]] = {}
    for axis in axes:
        axis_id = axis.get("axis_id")
        if not isinstance(axis_id, str) or not axis_id or axis_id in axis_by_id:
            raise RequirementError(f"Missing or duplicate candidate axis ID: {axis_id!r}")
        axis_by_id[axis_id] = axis

    coverage_source = coverage.get("axis_source", {})
    grip_pin = next(pin for pin in PINNED_INPUTS if pin["id"] == "grip_screen_attempt02")
    if coverage_source.get("path") != GRIP_PATH or coverage_source.get("sha256") != grip_pin["sha256"]:
        raise RequirementError("Coverage index does not pin the frozen 92-axis grip screen")
    if coverage_source.get("candidate_axis_count") != EXPECTED_CANDIDATE_AXES:
        raise RequirementError("Coverage index candidate-axis count does not match")
    if catalog.get("grip_screen_pin", {}).get("sha256") != grip_pin["sha256"]:
        raise RequirementError("Catalog screen does not pin the frozen grip-screen hash")

    candidate_families = coverage.get("candidate_family_coverage")
    if not isinstance(candidate_families, list):
        raise RequirementError("Coverage index has no candidate family partition")
    family_by_axis: dict[str, str] = {}
    for family in candidate_families:
        family_id = family.get("family_id")
        family_ids = family.get("axis_ids")
        if not isinstance(family_id, str) or not isinstance(family_ids, list):
            raise RequirementError("Malformed candidate family record")
        if family.get("count") != len(family_ids):
            raise RequirementError(f"{family_id}: count does not equal its axis ID list")
        for axis_id in family_ids:
            if axis_id in family_by_axis:
                raise RequirementError(f"Candidate axis assigned to more than one family: {axis_id}")
            family_by_axis[axis_id] = family_id
    if set(family_by_axis) != set(axis_by_id):
        raise RequirementError("Candidate family IDs do not exactly cover the 92 geometry axes")
    quantity = coverage.get("quantity_reconciliation", {}).get("candidate", {})
    if quantity.get("axes") != EXPECTED_CANDIDATE_AXES:
        raise RequirementError("Coverage candidate quantity is not 92 axes")

    catalog_rows = catalog.get("axis_rows")
    if not isinstance(catalog_rows, list):
        raise RequirementError("Catalog screen has no axis rows")
    catalog_by_axis: dict[str, dict[str, Any]] = {}
    for row in catalog_rows:
        for axis_id in row.get("axis_ids", []):
            if axis_id in catalog_by_axis:
                raise RequirementError(f"Catalog assigns an axis more than once: {axis_id}")
            catalog_by_axis[axis_id] = row
    if set(catalog_by_axis) != set(axis_by_id):
        raise RequirementError("Catalog row IDs do not exactly cover the 92 geometry axes")
    return axis_by_id, family_by_axis, catalog_by_axis


def maximum_role_thickness(intervals: list[list[float]]) -> float:
    return max(b - a for a, b in intervals)


def asme_class_options(row: dict[str, Any]) -> list[dict[str, Any]]:
    screen = row.get("length_screen", {})
    options: list[dict[str, Any]] = []
    primary_fields = ("minimum_overall_mm", "LB_min_mm", "LG_max_mm")
    if all(field in screen for field in primary_fields):
        options.append({
            "option_id": "screened_nominal_class",
            "nominal_class_in": screen.get("nominal_class_in"),
            "minimum_overall_mm": screen["minimum_overall_mm"],
            "LB_min_mm": screen["LB_min_mm"],
            "LG_max_mm": screen["LG_max_mm"],
            "source_scope": "conditional ASME B18.2.1 length-class arithmetic from the pinned catalog screen",
        })
    for key, value in screen.items():
        if not isinstance(value, dict) or not all(field in value for field in primary_fields):
            continue
        options.append({
            "option_id": key,
            "nominal_class_in": value.get("nominal_class_in"),
            "minimum_overall_mm": value["minimum_overall_mm"],
            "LB_min_mm": value["LB_min_mm"],
            "LG_max_mm": value["LG_max_mm"],
            "source_scope": "conditional alternative length-class arithmetic from the pinned catalog screen",
        })
    return options


def profile_signature(axis_requirement: dict[str, Any]) -> tuple[tuple[int, float, float], ...]:
    return tuple(
        (
            member["receiver_ordinal_head_to_nut"],
            member["member_interval_relative_to_wood_start_mm"][0],
            member["member_interval_thickness_mm"],
        )
        for member in axis_requirement["member_requirements"]
    )


def build_axis_requirement(
    axis: dict[str, Any], family_id: str, catalog_row: dict[str, Any]
) -> dict[str, Any]:
    axis_id = axis["axis_id"]
    datum = axis.get("underhead_datum", {})
    contact = datum.get("head_underface_contact_check", {})
    signed_gap = float(contact.get("signed_gap_mm", math.inf))
    head_face_global = float(contact.get("head_toward_nut_face_global_axis_mm", math.nan))
    washer_face_global = float(contact.get("head_washer_toward_head_face_global_axis_mm", math.nan))
    if not all(math.isfinite(value) for value in (signed_gap, head_face_global, washer_face_global)):
        raise RequirementError(f"{axis_id}: non-finite underhead datum evidence")
    if abs(signed_gap) > DATUM_CONTACT_TOLERANCE_MM or abs(head_face_global - washer_face_global) > DATUM_CONTACT_TOLERANCE_MM:
        raise RequirementError(f"{axis_id}: head/head-washer underhead datum does not close")
    definition = datum.get("definition", "")
    if "adjacent head bearing face / head-washer headward face" not in definition:
        raise RequirementError(f"{axis_id}: unexpected underhead datum definition")

    head_washer_intervals = interval_role(axis, HEAD_WASHER_ROLE)
    nut_washer_intervals = interval_role(axis, NUT_WASHER_ROLE)
    head_washer_model_thickness = maximum_role_thickness(head_washer_intervals)
    nut_washer_model_thickness = maximum_role_thickness(nut_washer_intervals)
    head_washer_min_mm, head_washer_max_mm = mm_range(WASHER_THICKNESS_IN)
    nut_washer_min_mm, nut_washer_max_mm = mm_range(WASHER_THICKNESS_IN)
    nut_min_mm, nut_max_mm = mm_range(NUT_FINISHED_HEIGHT_IN)
    head_shift_max = head_washer_max_mm - head_washer_model_thickness

    receivers = axis.get("wood_receiver_intervals")
    if not isinstance(receivers, list) or not receivers:
        raise RequirementError(f"{axis_id}: no receiver intervals")
    declared_order = axis.get("ordered_receiver_ids_head_to_nut", [])
    if [receiver.get("receiver_id") for receiver in receivers] != declared_order:
        raise RequirementError(f"{axis_id}: receiver records do not match declared head-to-nut order")

    raw_members: list[dict[str, Any]] = []
    all_ends: list[float] = []
    for receiver_ordinal, receiver in enumerate(receivers, start=1):
        receiver_id = receiver.get("receiver_id")
        intervals = receiver.get("intersection_solid_intervals_from_underhead_mm")
        if not isinstance(receiver_id, str) or not isinstance(intervals, list) or not intervals:
            raise RequirementError(f"{axis_id}: malformed raw receiver record")
        if len(intervals) != 1:
            raise RequirementError(
                f"{axis_id}/{receiver_id}: split bearing intervals need a member-level gap analysis; refusing a per-piece quarter-thread bound"
            )
        intervals_underhead = [
            normalize_interval_to_underhead(interval, coordinate_origin="underhead_relative")
            for interval in intervals
        ]
        interval_length = sum(b - a for a, b in intervals_underhead)
        reported_length = float(receiver.get("receiver_wood_axis_length_mm", interval_length))
        if not math.isfinite(reported_length) or reported_length <= 0:
            raise RequirementError(f"{axis_id}/{receiver_id}: receiver wood axis length must be finite and positive")
        if abs(reported_length - interval_length) > GEOMETRY_TOLERANCE_MM:
            raise RequirementError(f"{axis_id}/{receiver_id}: receiver interval length mismatch")
        for interval_ordinal, (a, b) in enumerate(intervals_underhead, start=1):
            if a < 0.0:
                raise RequirementError(f"{axis_id}/{receiver_id}: wood receiver begins headward of the underhead datum")
            bound = quarter_thread_lb_requirement(a, b)
            max_washer_bound = quarter_thread_lb_requirement(a + head_shift_max, b + head_shift_max)
            all_ends.append(b)
            raw_members.append({
                "receiver_id": receiver_id,
                "receiver_ordinal_head_to_nut": receiver_ordinal,
                "interval_ordinal": interval_ordinal,
                "interval_source_field": "intersection_solid_intervals_from_underhead_mm",
                "interval_coordinate_origin": "already normalized from the adjacent head/head-washer bearing plane",
                "modeled_interval_underhead_mm": [round_mm(a), round_mm(b)],
                "conservative_interval_underhead_mm_at_max_published_head_washer": [
                    round_mm(a + head_shift_max), round_mm(b + head_shift_max)
                ],
                "member_interval_relative_to_wood_start_mm": [round_mm(a - min(
                    x[0] for item in receivers for x in item["intersection_solid_intervals_from_underhead_mm"]
                )), round_mm(b - min(
                    x[0] for item in receivers for x in item["intersection_solid_intervals_from_underhead_mm"]
                ))],
                **bound,
                "minimum_LB_if_head_washer_at_published_max_mm": max_washer_bound["minimum_LB_underhead_to_last_thread_scratch_mm"],
                "head_washer_range_adjustment_to_LB_mm": round_mm(
                    max_washer_bound["minimum_LB_underhead_to_last_thread_scratch_mm"]
                    - bound["minimum_LB_underhead_to_last_thread_scratch_mm"]
                ),
                "profile_basis": "each contiguous raw receiver intersection is treated as one wood bearing interval; no gap is filled",
            })

    sorted_member_intervals = sorted(
        (member["modeled_interval_underhead_mm"][0], member["modeled_interval_underhead_mm"][1], member["receiver_id"])
        for member in raw_members
    )
    for previous, current in pairwise(sorted_member_intervals):
        if current[0] < previous[1] - GEOMETRY_TOLERANCE_MM:
            raise RequirementError(f"{axis_id}: overlapping receiver intervals need a member identity review")
    computed_wood_material_length = sum(b - a for a, b, _ in sorted_member_intervals)
    source_wood_material_length = float(axis.get("wood_grip_material_length_mm", math.nan))
    if not math.isfinite(source_wood_material_length) or source_wood_material_length <= 0:
        raise RequirementError(f"{axis_id}: wood_grip_material_length_mm must be finite and positive")
    if abs(source_wood_material_length - computed_wood_material_length) > GEOMETRY_TOLERANCE_MM:
        raise RequirementError(f"{axis_id}: source wood-grip material length does not equal its member intervals")

    wood_start = min(
        float(interval[0])
        for receiver in receivers
        for interval in receiver["intersection_solid_intervals_from_underhead_mm"]
    )
    wood_far_face = max(all_ends)
    max_lb_requirement = max(member["minimum_LB_underhead_to_last_thread_scratch_mm"] for member in raw_members)
    max_lb_with_headwasher_shift = max(member["minimum_LB_if_head_washer_at_published_max_mm"] for member in raw_members)

    stack = nut_stack_envelope(
        wood_far_face,
        modeled_head_washer_thickness_mm=head_washer_model_thickness,
        head_washer_range_mm=(head_washer_min_mm, head_washer_max_mm),
        nut_washer_range_mm=(nut_washer_min_mm, nut_washer_max_mm),
        nut_finished_height_range_mm=(nut_min_mm, nut_max_mm),
        physical_tip_projection_mm=PHYSICAL_TIP_PROJECTION_MM,
    )
    earliest_nut_bearing = stack["earliest_nut_bearing_plane_mm"]
    latest_nut_bearing = stack["latest_nut_bearing_plane_mm"]
    earliest_nut_far_face = stack["earliest_nut_far_face_mm"]
    latest_nut_far_face = stack["latest_nut_far_face_mm"]
    physical_tip_target = stack["minimum_physical_tip_target_mm"]

    modeled_roles = {
        role: interval_role(axis, role)
        for role in ("head", "head_washer", "shaft", "nut_washer", "nut")
    }
    shaft_end = max(b for _, b in modeled_roles["shaft"])
    source_shaft_end = float(axis.get("modeled_underhead_to_tip_mm", math.nan))
    if not math.isfinite(source_shaft_end) or source_shaft_end <= 0 or abs(source_shaft_end - shaft_end) > GEOMETRY_TOLERANCE_MM:
        raise RequirementError(f"{axis_id}: modeled underhead-to-tip length disagrees with shaft role occupancy")
    modeled_shaft_diameter = float(axis.get("modeled_shaft_diameter_mm", math.nan))
    if not math.isfinite(modeled_shaft_diameter) or modeled_shaft_diameter <= 0:
        raise RequirementError(f"{axis_id}: invalid modeled shaft diameter")
    length_options = []
    for option in asme_class_options(catalog_row):
        min_length = float(option["minimum_overall_mm"])
        lb_min = float(option["LB_min_mm"])
        lg_max = float(option["LG_max_mm"])
        if not all(math.isfinite(value) and value > 0 for value in (min_length, lb_min, lg_max)):
            raise RequirementError(f"{axis_id}: source-backed length-class dimensions must be finite and positive")
        length_options.append({
            **option,
            "minimum_overall_mm": round_mm(min_length),
            "minimum_length_minus_physical_tip_target_mm": round_mm(min_length - physical_tip_target),
            "minimum_length_minus_modeled_CAD_shaft_endpoint_mm": round_mm(min_length - shaft_end),
            "LB_min_mm": round_mm(lb_min),
            "LB_min_minus_NDS_nominal_D_requirement_mm": round_mm(lb_min - max_lb_requirement),
            "LB_min_minus_max_head_washer_sensitivity_mm": round_mm(lb_min - max_lb_with_headwasher_shift),
            "LG_max_mm": round_mm(lg_max),
            "earliest_nut_bearing_minus_LG_max_mm": round_mm(earliest_nut_bearing - lg_max),
            "physical_tip_length_status": (
                "class_minimum_reaches_tip_projection_target" if min_length + GEOMETRY_TOLERANCE_MM >= physical_tip_target
                else "class_minimum_is_short_of_tip_projection_target"
            ),
            "CAD_endpoint_status": (
                "class_minimum_reaches_modeled_CAD_endpoint" if min_length + GEOMETRY_TOLERANCE_MM >= shaft_end
                else "class_minimum_can_be_shorter_than_modeled_CAD_endpoint"
            ),
            "NDS_body_boundary_status": (
                "class_LB_min_at_or_above_geometric_requirement_if_class_applies" if lb_min + GEOMETRY_TOLERANCE_MM >= max_lb_requirement
                else "class_LB_min_does_not_demonstrate_geometric_requirement; actual_LB_may_be_longer"
            ),
            "max_head_washer_sensitivity_status": (
                "class_LB_min_at_or_above_washer_shifted_sensitivity_if_class_applies" if lb_min + GEOMETRY_TOLERANCE_MM >= max_lb_with_headwasher_shift
                else "class_LB_min_does_not_demonstrate_washer_shifted_sensitivity; actual_LB_may_be_longer"
            ),
            "LG_interpretation": "gage-coordinate arithmetic only; LG_max is not first-full-thread start and does not establish nut engagement",
            "applicability": "hypothetical ASME class bound only; no selected or inspected bolt is asserted to conform",
        })

    if not length_options:
        raise RequirementError(f"{axis_id}: catalog row has no source-backed class comparison")

    return {
        "axis_id": axis_id,
        "priority_group": axis.get("priority_group"),
        "family_id": family_id,
        "catalog_row_id": catalog_row.get("row_id"),
        "raw_receiver_ids_head_to_nut": declared_order,
        "underhead_datum": {
            "definition": definition,
            "receiver_intervals_input": "already underhead-relative; producer does not rebase them a second time",
            "head_to_head_washer_contact_gap_mm": round_mm(signed_gap),
            "head_underface_global_axis_mm": round_mm(float(contact["head_toward_nut_face_global_axis_mm"])),
        },
        "modeled_geometry_occupancy": {
            "nominal_diameter_assumption_mm": round_mm(modeled_shaft_diameter),
            "modeled_shaft_unthreaded_envelope_underhead_mm": [
                [round_mm(a), round_mm(b)] for a, b in modeled_roles["shaft"]
            ],
            "modeled_shaft_underhead_to_tip_mm": round_mm(shaft_end),
            "modeled_roles_underhead_mm": {
                name: [[round_mm(a), round_mm(b)] for a, b in intervals]
                for name, intervals in modeled_roles.items()
            },
            "receiver_wood_envelope_underhead_mm": [round_mm(wood_start), round_mm(wood_far_face)],
            "receiver_wood_union_length_mm": round_mm(float(axis["wood_grip_material_length_mm"])),
            "modeled_shaft_covers_all_raw_receiver_intervals": bool(axis.get("modeled_shaft_covers_all_raw_receiver_intervals")),
            "thread_geometry_in_CAD": False,
            "role_policy": "integral head, shaft, head washer, nut washer, and nut remain distinct modeled roles",
        },
        "source_range_comparison": {
            "head_washer_role": {
                "published_thickness_range_mm": [head_washer_min_mm, head_washer_max_mm],
                "modeled_thickness_mm": round_mm(head_washer_model_thickness),
                "modeled_thickness_within_published_range": head_washer_min_mm - GEOMETRY_TOLERANCE_MM <= head_washer_model_thickness <= head_washer_max_mm + GEOMETRY_TOLERANCE_MM,
                "meaning": "dimensional comparison to a catalog lead; product not selected or received",
            },
            "nut_washer_role": {
                "published_thickness_range_mm": [nut_washer_min_mm, nut_washer_max_mm],
                "modeled_thickness_mm": round_mm(nut_washer_model_thickness),
                "modeled_thickness_within_published_range": nut_washer_min_mm - GEOMETRY_TOLERANCE_MM <= nut_washer_model_thickness <= nut_washer_max_mm + GEOMETRY_TOLERANCE_MM,
                "meaning": "dimensional comparison to a catalog lead; product not selected or received",
            },
            "nut_role": {
                "published_finished_height_range_mm": [nut_min_mm, nut_max_mm],
                "modeled_thickness_mm": round_mm(maximum_role_thickness(modeled_roles["nut"])),
                "modeled_thickness_within_published_range": nut_min_mm - GEOMETRY_TOLERANCE_MM <= maximum_role_thickness(modeled_roles["nut"]) <= nut_max_mm + GEOMETRY_TOLERANCE_MM,
                "meaning": "B18.2.2 finished-nut outer height range; does not locate active internal thread or establish a matched nut lot",
            },
        },
        "member_requirements": raw_members,
        "NDS_nominal_D_quarter_thread_screen": {
            "nominal_D_assumption_mm": round_mm(modeled_shaft_diameter),
            "maximum_thread_bearing_fraction_per_contiguous_member_interval": 0.25,
            "minimum_LB_underhead_to_last_thread_scratch_mm_for_all_members": round_mm(max_lb_requirement),
            "minimum_LB_if_head_washer_at_published_max_mm": round_mm(max_lb_with_headwasher_shift),
            "max_head_washer_shift_sensitivity_mm": round_mm(head_shift_max),
            "condition": "For each frozen modeled interval [a,b], LB >= b - (b-a)/4. The direct result uses the exact pinned underhead-relative [a,b] values; a separate sensitivity shifts those values by published maximum head-washer thickness minus modeled thickness.",
            "status": "geometric criterion only; NDS resistance and joint acceptance are not evaluated",
        },
        "nut_and_tip_requirements": {
            "nut_bearing_plane_range_underhead_mm": [round_mm(earliest_nut_bearing), round_mm(latest_nut_bearing)],
            "nut_far_face_range_underhead_mm": [round_mm(earliest_nut_far_face), round_mm(latest_nut_far_face)],
            "minimum_physical_tip_target_underhead_mm": round_mm(physical_tip_target),
            "minimum_physical_projection_past_worst_case_nut_far_face_mm": round_mm(PHYSICAL_TIP_PROJECTION_MM),
            "inherited_WJ24_unthreaded_CAD_tip_allowance_mm": INHERITED_WJ24_GEOMETRY_TIP_ALLOWANCE_MM,
            "projection_comparison_scope": "3 full 1/4-20 pitches is a source-documented length-only projection scenario; the inherited WJ24 3.175 mm CAD allowance is separately identified and neither requires full-form thread through the projection.",
            "full_thread_sufficient_profile_condition": {
                "first_full_form_thread_start_must_be_at_or_headward_of_mm": round_mm(earliest_nut_bearing),
                "last_full_form_thread_end_must_be_at_or_nutward_of_mm": round_mm(latest_nut_far_face),
                "continuous_full_form_interval_must_cover_mm": [round_mm(earliest_nut_bearing), round_mm(latest_nut_far_face)],
                "status": "unproven; no item-specific first/last full-form thread coordinates or matched nut active-thread interval are sourced",
                "interpretation": "sufficient external-profile coverage across the full finished nut envelope, not an exact functional fit, chamfer-capacity, or strength criterion",
            },
            "physical_tail_thread_requirement": "none beyond the nut from this screen; the 3.81 mm three-pitch projection is physical length only and does not require full-form thread through the tail",
        },
        "source_backed_length_comparisons": length_options,
        "evidence_gaps": [
            "No selected bolt SKU or delivered length/shank has been identified or inspected.",
            "No item/lot-specific first full-form thread, last thread scratch, continuous usable-thread interval, or point/runout envelope is available.",
            "The matched nut's functional active-thread height and end chamfers are not located by nominal or finished outer thickness.",
            "No product/lot evidence establishes that catalog or ASME class dimensions describe a delivered axis part.",
            "The full-thread sufficient profile condition does not establish class compatibility, rotational fit, seat contact, capacity, or joint acceptance.",
        ],
    }


def build_source_pins() -> dict[str, Any]:
    return {
        "schema": "wood_joint_hardware_material_specification_source_pins/v1",
        "artifact_id": ARTIFACT_ID,
        "pin_policy": "immutable reviewed SHA-256 values are embedded in produce.py; both --write and --verify fail if any source differs",
        "inputs": [dict(pin) for pin in PINNED_INPUTS],
        "derived_source_ranges": {
            "washer_thickness": {
                "source_lead": "K.L. Jack 25NWUS 1/4-in Type A Wide washer",
                "published_range_in": list(WASHER_THICKNESS_IN),
                "published_range_mm": mm_range(WASHER_THICKNESS_IN),
                "range_scope": "public catalog dimensional lead only; no selection, receiving check, material/capacity or washer support acceptance",
            },
            "nut_finished_outer_height": {
                "standard": "ASME B18.2.2-2022, 1/4-in finished hex nut envelope",
                "published_range_in": list(NUT_FINISHED_HEIGHT_IN),
                "published_range_mm": mm_range(NUT_FINISHED_HEIGHT_IN),
                "range_scope": "standard outer-height range; does not give the selected nut lot's active-thread height or chamfer depth",
            },
            "physical_tip_projection": {
                "range_mm": round_mm(PHYSICAL_TIP_PROJECTION_MM),
                "source_basis": "three 1/4-20 pitches (3 x 0.050 in) as a length-only stack scenario documented in wj03-hardware-procurement.md",
                "scope": "physical tip past the worst-case nut far face only; no full-form thread is required through this projection",
            },
            "inherited_WJ24_geometry_tip_allowance": {
                "range_mm": INHERITED_WJ24_GEOMETRY_TIP_ALLOWANCE_MM,
                "source_basis": "unthreaded shaft endpoint allowance in current-ordinary-hardware-spacer-option.md",
                "scope": "reported for comparison only; it is not a thread-engagement requirement",
            },
            "nominal_D": {
                "range_mm": 6.35,
                "source_basis": "modeled 6.35 mm shaft envelope in each pinned grip-screen axis",
                "scope": "nominal-D geometry assumption for a conditional NDS screen; no selected delivered bolt is asserted to have this diameter",
            },
        },
    }


def build_requirements(root: Path) -> dict[str, Any]:
    verify_source_hashes(root)
    grip = read_json(root, GRIP_PATH)
    coverage = read_json(root, COVERAGE_PATH)
    catalog = read_json(root, CATALOG_PATH)
    axis_by_id, family_by_axis, catalog_by_axis = validate_inventory(grip, coverage, catalog)

    if coverage.get("schema") != "wood-joints-current-hardware-coverage/v1":
        raise RequirementError("Unexpected current hardware coverage schema")
    family_sources = {family["family_id"]: family for family in coverage["candidate_family_coverage"]}
    axis_requirements = {
        axis_id: build_axis_requirement(axis, family_by_axis[axis_id], catalog_by_axis[axis_id])
        for axis_id, axis in axis_by_id.items()
    }

    family_results: list[dict[str, Any]] = []
    for family_id, family in family_sources.items():
        family_axes = [axis_requirements[axis_id] for axis_id in family["axis_ids"]]
        max_lb = max(axis["NDS_nominal_D_quarter_thread_screen"]["minimum_LB_underhead_to_last_thread_scratch_mm_for_all_members"] for axis in family_axes)
        max_lb_headwasher = max(axis["NDS_nominal_D_quarter_thread_screen"]["minimum_LB_if_head_washer_at_published_max_mm"] for axis in family_axes)
        max_tip_target = max(axis["nut_and_tip_requirements"]["minimum_physical_tip_target_underhead_mm"] for axis in family_axes)
        max_modeled_endpoint = max(axis["modeled_geometry_occupancy"]["modeled_shaft_underhead_to_tip_mm"] for axis in family_axes)

        variant_buckets: dict[tuple[tuple[int, float, float], ...], list[dict[str, Any]]] = {}
        for axis in family_axes:
            variant_buckets.setdefault(profile_signature(axis), []).append(axis)
        variants = []
        for variant_axes in variant_buckets.values():
            members = variant_axes[0]["member_requirements"]
            variants.append({
                "axis_ids": [axis["axis_id"] for axis in variant_axes],
                "member_profiles_head_to_nut": [
                    {
                        "receiver_ids_across_variant_axes": sorted({
                            axis["member_requirements"][i]["receiver_id"]
                            for axis in variant_axes
                        }),
                        "receiver_ordinal_head_to_nut": member["receiver_ordinal_head_to_nut"],
                        "member_interval_relative_to_wood_start_mm": member["member_interval_relative_to_wood_start_mm"],
                        "member_interval_thickness_mm": member["member_interval_thickness_mm"],
                        "maximum_thread_bearing_in_member_mm": member["maximum_thread_bearing_in_member_mm"],
                        "minimum_LB_underhead_to_last_thread_scratch_mm": member["minimum_LB_underhead_to_last_thread_scratch_mm"],
                    }
                    for i, member in enumerate(members)
                ],
                "minimum_LB_for_all_members_in_variant_mm": max(
                    member["minimum_LB_underhead_to_last_thread_scratch_mm"] for member in members
                ),
            })

        option_ids = [option["option_id"] for option in family_axes[0]["source_backed_length_comparisons"]]
        class_comparisons = []
        for option_id in option_ids:
            options = [
                next(item for item in axis["source_backed_length_comparisons"] if item["option_id"] == option_id)
                for axis in family_axes
            ]
            source_option = options[0]
            min_len = source_option["minimum_overall_mm"]
            lb_min = source_option["LB_min_mm"]
            lg_max = source_option["LG_max_mm"]
            earliest = min(axis["nut_and_tip_requirements"]["nut_bearing_plane_range_underhead_mm"][0] for axis in family_axes)
            washer_adjusted_lb = max(axis["NDS_nominal_D_quarter_thread_screen"]["minimum_LB_if_head_washer_at_published_max_mm"] for axis in family_axes)
            class_comparisons.append({
                "option_id": option_id,
                "nominal_class_in": source_option.get("nominal_class_in"),
                "minimum_overall_mm": min_len,
                "physical_tip_target_max_mm": round_mm(max_tip_target),
                "minimum_length_minus_tip_target_mm": round_mm(min_len - max_tip_target),
                "physical_tip_status": "class_minimum_reaches_tip_projection_target" if min_len + GEOMETRY_TOLERANCE_MM >= max_tip_target else "class_minimum_is_short_of_tip_projection_target",
                "modeled_CAD_endpoint_max_mm": round_mm(max_modeled_endpoint),
                "minimum_length_minus_CAD_endpoint_mm": round_mm(min_len - max_modeled_endpoint),
                "CAD_endpoint_status": "class_minimum_reaches_modeled_endpoint" if min_len + GEOMETRY_TOLERANCE_MM >= max_modeled_endpoint else "class_minimum_can_be_shorter_than_modeled_endpoint",
                "LB_min_mm": lb_min,
                "minimum_LB_requirement_max_mm": round_mm(max_lb),
                "LB_min_minus_requirement_mm": round_mm(lb_min - max_lb),
                "NDS_boundary_status": "class_LB_min_at_or_above_geometric_requirement_if_class_applies" if lb_min + GEOMETRY_TOLERANCE_MM >= max_lb else "class_LB_min_does_not_demonstrate_geometric_requirement; actual_LB_may_be_longer",
                "maximum_head_washer_sensitivity_LB_requirement_mm": round_mm(washer_adjusted_lb),
                "LB_min_minus_max_head_washer_sensitivity_mm": round_mm(lb_min - washer_adjusted_lb),
                "maximum_head_washer_sensitivity_status": "class_LB_min_at_or_above_washer_shifted_sensitivity_if_class_applies" if lb_min + GEOMETRY_TOLERANCE_MM >= washer_adjusted_lb else "class_LB_min_does_not_demonstrate_washer_shifted_sensitivity; actual_LB_may_be_longer",
                "LG_max_mm": lg_max,
                "earliest_nut_bearing_min_mm": round_mm(earliest),
                "earliest_nut_bearing_minus_LG_max_mm": round_mm(earliest - lg_max),
                "LG_status": "gage-coordinate comparison only; it is not a first-full-thread coordinate",
                "listed_product_ids": family_axes[0]["source_backed_length_comparisons"] and catalog_by_axis[family["axis_ids"][0]].get("product_ids", []),
                "conditional_scope": "standard class bound only if the compared delivered item conforms; no SKU selected and nominal length is not delivered shank length",
            })

        all_roles_in_range = all(
            axis["source_range_comparison"][role]["modeled_thickness_within_published_range"]
            for axis in family_axes
            for role in ("head_washer_role", "nut_washer_role", "nut_role")
        )
        family_results.append({
            "family_id": family_id,
            "family_name": family["family"],
            "axis_count": family["count"],
            "axis_ids": family["axis_ids"],
            "member_profiles": variants,
            "family_minimum_LB_underhead_to_last_thread_scratch_mm": round_mm(max_lb),
            "family_minimum_LB_if_head_washer_at_published_max_mm": round_mm(max_lb_headwasher),
            "largest_member_quarter_thread_allowance_mm": max(
                member["maximum_thread_bearing_in_member_mm"]
                for axis in family_axes for member in axis["member_requirements"]
            ),
            "smallest_member_quarter_thread_allowance_mm": min(
                member["maximum_thread_bearing_in_member_mm"]
                for axis in family_axes for member in axis["member_requirements"]
            ),
            "physical_tip_target_underhead_max_mm": round_mm(max_tip_target),
            "modeled_CAD_shaft_endpoint_max_mm": round_mm(max_modeled_endpoint),
            "published_washer_and_nut_outer_ranges_match_modeled_role_sizes": all_roles_in_range,
            "nut_full_thread_profile_condition": "external full-form thread must span the family's earliest nut bearing plane through its latest far face; source evidence does not prove this condition for any delivered axis",
            "class_comparisons": class_comparisons,
            "unresolved_family_evidence": [
                "No exact part-specific axial thread profile is available to demonstrate both the NDS LB threshold and the nut full-thread envelope.",
                "No selected/delivered washer or nut lot is available; source ranges remain conditional dimensions.",
            ],
        })

    retained_families = coverage.get("retained_family_coverage", [])
    retained_ids: list[str] = []
    retained_reference = []
    for retained in retained_families:
        retained_ids.extend(retained.get("axis_ids", []))
        retained_reference.append({
            "family_id": retained.get("family_id"),
            "family": retained.get("family"),
            "count": retained.get("count"),
            "axis_ids": retained.get("axis_ids", []),
            "modeled_reference": retained.get("modeled", {}),
            "treatment": "separate retained starting-stack identity reference only; no requalification, resistance transfer, or delivered-part inspection",
        })
    if len(retained_families) != EXPECTED_RETAINED_FAMILIES or len(retained_ids) != EXPECTED_RETAINED_AXES or len(set(retained_ids)) != EXPECTED_RETAINED_AXES:
        raise RequirementError("Retained starting-stack reference must remain exactly three families and 12 unique axes")
    if coverage.get("quantity_reconciliation", {}).get("retained", {}).get("axes") != EXPECTED_RETAINED_AXES:
        raise RequirementError("Coverage retained-axis quantity is not 12")

    primary_ids = [
        "knee_outer_left_post_1", "knee_outer_left_post_2",
        "knee_outer_left_side_1", "knee_outer_left_side_2",
        "knee_outer_left_inner_header_1", "knee_outer_left_inner_header_2",
    ]
    if any(axis_id not in axis_requirements for axis_id in primary_ids):
        raise RequirementError("Required left-corner priority axes are missing")

    data = {
        "schema": "wood_joint_hardware_material_requirements/v1",
        "artifact_id": ARTIFACT_ID,
        "status": "conditional source-bound dimensional requirements; not product selection, acceptance, resistance, or joint pass",
        "scope": {
            "candidate_revision_id": grip["revision_id"],
            "frozen_geometry_screen": GRIP_PATH,
            "candidate_axis_count": EXPECTED_CANDIDATE_AXES,
            "retained_starting_axes_referenced_separately": EXPECTED_RETAINED_AXES,
            "selected_or_inspected_parts": False,
            "joint_pass_or_capacity_claim": False,
        },
        "input_pins": [
            {"id": pin["id"], "path": pin["path"], "sha256": pin["sha256"]}
            for pin in PINNED_INPUTS
        ],
        "coordinate_and_method_assumptions": {
            "source_receiver_interval_field": "intersection_solid_intervals_from_underhead_mm",
            "source_receiver_intervals_already_underhead_relative": True,
            "underhead_datum": "adjacent head bearing face / head-washer headward face projected on the head-to-nut axis; source verifies coincident contact",
            "why_no_rebase_is_applied": "The pinned receiver and hardware role interval keys explicitly state from_underhead_mm; the datum is retained as evidence and is not subtracted a second time.",
            "alternate_datum_conversion_rule_tested": "global-axis interval [u0,u1] becomes [u0-underhead_axis, u1-underhead_axis]; global-to-underhead conversion is rejected without an explicit datum.",
            "modeled_receiver_interval_assumption": "Each contiguous raw axis-probe intersection interval represents one wood bearing interval; interval endpoints and stock are CAD geometry, not measured cuts or tolerance bounds.",
            "head_washer_stack_adjustment": "The required NDS bound uses the frozen modeled receiver interval exactly. A separate sensitivity shifts the interval by (published maximum head-washer thickness minus modeled head-washer thickness); the nut-plane range separately uses published head-washer min/max.",
            "split_receiver_policy": "Current source has one contiguous intersection interval per raw receiver. A receiver with multiple intervals is rejected; the code does not incorrectly apply a per-piece quarter-thread rule as a member-level rule.",
            "NDS_nominal_D_condition": "For each member interval [a,b], nominal-D threaded bearing is screened to no more than (b-a)/4, hence LB >= b-(b-a)/4. Apply per receiver interval and take the maximum LB requirement; no resistance is calculated.",
            "LB_definition": "ASME B18.2.1 body-length datum to last thread scratch / applicable transition datum; not a measured first-full-thread coordinate.",
            "nominal_D_assumption_mm": 6.35,
            "thread_profile_unknown": True,
        },
        "source_range_assumptions": {
            "washer_thickness_mm": mm_range(WASHER_THICKNESS_IN),
            "washer_source": "K.L. Jack 25NWUS 1/4-in Type A Wide catalog lead; same published range used separately for the CAD head-washer and nut-washer roles",
            "nut_finished_outer_height_mm": mm_range(NUT_FINISHED_HEIGHT_IN),
            "nut_source": "ASME B18.2.2-2022 1/4-in finished hex-nut outer envelope, 0.212–0.226 in; the listed K.L. Jack nut is only a nominal 7/32-in catalog lead",
            "physical_tip_projection_past_worst_case_nut_far_face_mm": round_mm(PHYSICAL_TIP_PROJECTION_MM),
            "physical_tip_projection_source": "three full 1/4-20 pitches (0.150 in) in the documented WJ-03 length-only arithmetic scenario; no full-form thread beyond the nut is required by this screen",
            "inherited_WJ24_geometry_tip_allowance_mm": INHERITED_WJ24_GEOMETRY_TIP_ALLOWANCE_MM,
            "class_minimum_overall_and_LB_source": "conditional ASME B18.2.1 Tables 12–13 comparisons captured in the pinned catalog screen and corrected by bolt-dimension-source-correction.md",
            "actual_product_scope": "Published dimensions are conditional source ranges / class boundaries; no named part has a receiving record or product-specific complete-thread interval here.",
        },
        "candidate_summary": {
            "candidate_axes": len(axis_requirements),
            "unique_axis_ids": len(set(axis_requirements)),
            "candidate_family_count": len(family_results),
            "modeled_bolts": len(axis_requirements),
            "modeled_nuts": len(axis_requirements),
            "modeled_head_washer_roles": len(axis_requirements),
            "modeled_nut_washer_roles": len(axis_requirements),
            "modeled_separate_washer_roles": 2 * len(axis_requirements),
            "threaded_profile_rows": sum(len(axis["member_requirements"]) for axis in axis_requirements.values()),
            "axis_coverage_status": "all 92 current candidate axes appear exactly once in the pinned coverage families and exactly once in catalog comparison rows",
        },
        "retained_starting_stack_reference": {
            "source": COVERAGE_PATH,
            "family_count": EXPECTED_RETAINED_FAMILIES,
            "axis_count": EXPECTED_RETAINED_AXES,
            "families": retained_reference,
            "boundary": "These 12 starting arrangements remain distinct from the 92 current candidate axes. This artifact only references their identities and modeled quantities; it does not rerun fit/resistance checks or transfer any prior result.",
        },
        "family_requirements": family_results,
        "axis_requirements": list(axis_requirements.values()),
        "required_corner_priority_axis_ids": primary_ids,
        "global_missing_evidence": [
            "No item-specific first-full-thread start, last full-form thread end, last scratch, runout or point envelope is available for any candidate bolt.",
            "No matched nut lot's active internal-thread interval/chamfers or functional gauge evidence is available.",
            "No exact delivered bolt length, shank, washers, nut, wood cuts, seats, or floor has been inspected.",
            "The dimension screens establish no material resistance, bolt/nut capacity, load path, full-joint mechanics, or joint acceptance.",
        ],
        "disposition": {
            "selected_SKU": None,
            "purchase_authorized": False,
            "delivered_part_inspection_claimed": False,
            "NDS_capacity_result": None,
            "joint_pass": False,
            "fabrication_or_drilling_release": False,
        },
    }
    return data


def build_markdown(data: dict[str, Any], pins: dict[str, Any]) -> str:
    lines = [
        "# WJ24 hardware and material requirements",
        "",
        "**Status:** conditional, source-bound dimensional requirements for the 92-axis `led-clearance-2x6-runner-seated-blocks-v1` geometry. This is not a product selection, delivered-part acceptance, capacity result, joint pass, or fabrication release.",
        "",
        "The producer reads the pinned geometry and local source records only. The complete per-axis receiver intervals, stack envelopes, and class comparisons are in [`requirements.json`](requirements.json). [`source-pins.json`](source-pins.json) records the fixed SHA-256 inputs; both replay modes fail if any source bytes change.",
        "",
        "## Geometry and calculation basis",
        "",
        "The grip-screen receiver intervals are already measured from the adjacent head bearing face/head-washer headward face. Their field name is `intersection_solid_intervals_from_underhead_mm`, and the source records coincident head/head-washer contact. The producer does not subtract the global datum again. A separate tested conversion rule rebases global-axis intervals only when an explicit underhead scalar is supplied.",
        "",
        "For each raw receiver interval `[a,b]`, with `t=b-a`, the nominal-diameter NDS screen requires `LB >= b - t/4`; it therefore caps thread bearing in that member at `t/4`. This direct requirement uses the frozen underhead-relative interval exactly. A separately reported sensitivity shifts the interval by the difference between the published maximum head-washer thickness and the modeled thickness. If a receiver ever contains multiple disjoint intervals, the producer stops and requires member-level gap analysis rather than treating each piece as an independent member. `D = 6.35 mm` is a modeled nominal-diameter assumption. No NDS resistance or joint pass is calculated.",
        "",
        "The dimensional ranges used for each washer role are 0.051–0.080 in (1.2954–2.032 mm), from the K.L. Jack 25NWUS catalog lead. The nut's finished outer-height comparison is 0.212–0.226 in (5.3848–5.7404 mm), from the ASME B18.2.2 1/4-in nut envelope. Those are source ranges, not evidence that a selected or delivered washer/nut matches them. The model keeps head washer, shaft, nut washer, and nut as separate roles.",
        "",
        "The physical tip target is the worst-case far nut face plus three 1/4-20 pitches (3.81 mm), a documented length-only projection scenario. The existing WJ24 unthreaded CAD allowance is 3.175 mm and is reported separately. Neither projection requires full-form thread through the tail. For sufficient nut-profile coverage, a continuous full-form external-thread interval would span from the earliest possible nut bearing plane through the latest possible nut far face. This envelope uses the published washer/nut dimensions and is deliberately stronger than a claim about the nut's unknown active-thread height. It is not exact thread fit, chamfer capacity, or strength evidence.",
        "",
        "ASME `LB,min` and minimum overall length are reported as conditional class boundaries. A class `LB,min` below a geometric bound means the class minimum does not demonstrate the needed body length; an actual part could have a longer body. `LG,max` is kept as a gage-coordinate comparison. It is not the first-full-thread coordinate and does not establish nut engagement. A nominal class length is not a purchase length or delivered shank measurement.",
        "",
        "## Family summary",
        "",
        "| Family | Axes | Member variants | Minimum `LB` (frozen intervals) (mm) | `LB` with max-head-washer sensitivity (mm) | Largest per-member quarter allowance (mm) | Maximum physical tip target (mm) | Missing profile evidence |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for family in data["family_requirements"]:
        variant_ids = "; ".join(
            f"{len(variant['axis_ids'])} axes: "
            + " → ".join(f"{member['member_interval_thickness_mm']:.1f}" for member in variant["member_profiles_head_to_nut"])
            + " mm head to nut"
            for variant in family["member_profiles"]
        )
        lines.append(
            f"| `{family['family_id']}` | {family['axis_count']} | {variant_ids} | "
            f"{family['family_minimum_LB_underhead_to_last_thread_scratch_mm']:.3f} | "
            f"{family['family_minimum_LB_if_head_washer_at_published_max_mm']:.3f} | "
            f"{family['largest_member_quarter_thread_allowance_mm']:.3f} | "
            f"{family['physical_tip_target_underhead_max_mm']:.3f} | unresolved for every axis |"
        )
    lines.extend([
        "",
        "Family variants retain each member's relative interval, maximum threaded-bearing length, exact receiver IDs, and `LB` requirement in `requirements.json`. This is important for the four knee inner-header axes: the `_1` and `_2` receivers have different far-member lengths even though their total grip and hardware class screen match.",
        "",
        "## Left outer-corner priority axes",
        "",
        "These six exact IDs are the requested corner priorities. Values are geometry-derived from their frozen receiver records; mirrored/right-side peers are also present in the JSON.",
        "",
        "| Axis | Receiver IDs head to nut | Per-member `[a,b]` underhead intervals (mm) | Required `LB` (mm) | Tip target (mm) |",
        "| --- | --- | --- | ---: | ---: |",
    ])
    for axis_id in data["required_corner_priority_axis_ids"]:
        axis = next(item for item in data["axis_requirements"] if item["axis_id"] == axis_id)
        member_text = "; ".join(
            f"{member['receiver_id']} [{member['modeled_interval_underhead_mm'][0]:.3f}, {member['modeled_interval_underhead_mm'][1]:.3f}]"
            for member in axis["member_requirements"]
        )
        lines.append(
            f"| `{axis_id}` | {', '.join(axis['raw_receiver_ids_head_to_nut'])} | {member_text} | "
            f"{axis['NDS_nominal_D_quarter_thread_screen']['minimum_LB_underhead_to_last_thread_scratch_mm_for_all_members']:.3f} | "
            f"{axis['nut_and_tip_requirements']['minimum_physical_tip_target_underhead_mm']:.3f} |"
        )
    lines.extend([
        "",
        "## Length-class comparisons and open conditions",
        "",
        "`requirements.json` reports, by family and length option, the source-class minimum overall length versus the physical tip target and modeled CAD endpoint, `LB,min` versus the per-member screen, and `LG,max` versus the earliest nut bearing plane. A negative comparison records a permissive class boundary that does not meet the screen. It is not a product failure finding, because the actual SKU and delivered dimensions are unknown.",
        "",
        "No listed source pins a candidate bolt's first full-form thread, last full-form thread, last scratch, transition/runout, or point at an actual axis. The matched nut's active internal-thread interval and chamfers are also unknown. Thus the sufficient profile envelope remains unproven for all 92 axes, regardless of length-class arithmetic.",
        "",
        "The 12 retained starting stacks are referenced separately from the 92 current axes by identity and modeled quantity in `requirements.json`. This packet does not requalify those stacks or transfer their prior resistance results.",
        "",
        "Source documents include the [current grip screen](../../current-grip-screen.md), [hardware schedule](../../current-hardware-schedule.md), [bolt thread-boundary screen](../../current-bolt-thread-boundary-screen-2026-09-27.md), [ASME dimension correction](../../bolt-dimension-source-correction.md), [thread source research](../../current-bolt-thread-alternative-spec-research-2026-09-27.md), [quarter-thread discussion](../../current-center-sandwich-hardware-options.md), and [physical tip screen](../../current-ordinary-hardware-spacer-option.md).",
        "",
    ])
    return "\n".join(lines)


def expected_outputs(root: Path) -> dict[Path, bytes]:
    pins = build_source_pins()
    requirements = build_requirements(root)
    return {
        root / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/source-pins.json": json_bytes(pins),
        root / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/requirements.json": json_bytes(requirements),
        root / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/requirements.md": build_markdown(requirements, pins).encode("utf-8"),
    }


def write_outputs(root: Path) -> None:
    outputs = expected_outputs(root)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    print(f"Wrote {len(outputs)} owned outputs for {EXPECTED_CANDIDATE_AXES} candidate axes")


def verify_outputs(root: Path) -> None:
    outputs = expected_outputs(root)
    mismatches = []
    for path, expected in outputs.items():
        if not path.is_file():
            mismatches.append(f"missing {path.relative_to(root)}")
        elif path.read_bytes() != expected:
            mismatches.append(f"byte mismatch {path.relative_to(root)}")
    if mismatches:
        raise RequirementError("Generated outputs differ: " + "; ".join(mismatches))
    print(f"Verified exact replay of {len(outputs)} owned outputs for {EXPECTED_CANDIDATE_AXES} candidate axes")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write requirements.json, source-pins.json, and requirements.md")
    mode.add_argument("--verify", action="store_true", help="verify source pins and exact deterministic output replay")
    args = parser.parse_args(argv)
    try:
        if args.write:
            write_outputs(ROOT)
        else:
            verify_outputs(ROOT)
    except RequirementError as exc:
        print(f"FAIL CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
