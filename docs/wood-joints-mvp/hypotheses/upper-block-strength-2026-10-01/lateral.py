#!/usr/bin/env python3
"""Replay conditional single-bolt lateral references for the reviewed blocks.

This calculation preserves the source action records and uses the existing
wood-to-wood single-shear helper. It does not establish adjusted or joint
resistance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SERVICE = ROOT / "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30"
MATERIALS = ROOT / "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30"
OUTPUT = HERE / "lateral.json"
sys.path.insert(0, str(ROOT))

from mini_moonboard.bolted_wood_wood_yield import (
    dowel_bending_yield_moment_lb_in,
    wood_wood_single_shear_reference,
)

LBF_N = 4.4482216152605
MODES = ("Im", "Is", "II", "IIIm", "IIIs", "IV")
THREAD_FREEZE = SERVICE / "thread-scenario-freeze.json"
PARTIAL_REPORT = SERVICE / "partial-thread-comparison.json"
PARTIAL_PRODUCER = SERVICE / "partial_thread.py"
MATERIAL_INPUTS = MATERIALS / "material-inputs.json"
MATERIALS_NOTE = MATERIALS / "materials.md"
FASTENERS_NOTE = MATERIALS / "fasteners.md"
CHAPTER_12 = MATERIALS / "materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf"

# Immutable pins for the two reviewed action packets and every method/data
# implementation consumed directly by this producer. The Chapter 12 pin also
# binds the source-table F_yb sensitivity called out in the accompanying note.
PINNED_SHA256 = {
    "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json": "0fc5f9ce9c92effcb01d3213c38b33282c281539dab9d48cb06f33e15c1994a6",
    "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/upper-joints.json": "f4c92d874dcb0f40e5e900971deaff9580e99063b453e1984e9b1ba660a2be9f",
    "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/thread-scenario-freeze.json": "2ac51798bb5814edfe73c315279cfcc0c4ad4100038f6a15c7c1c2c1f04c321b",
    "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/partial_thread.py": "75bc4aae954b8fe33ebb1e9b6c7ab1c51716290bee9d8392b5aaed6aae65ce3f",
    "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/partial-thread-comparison.json": "df7b5af3665ff937cb940e822165d64d43bcb7384a6cd8c7aeb00d870984676b",
    "mini_moonboard/bolted_wood_wood_yield.py": "efefbe55279776bc42844cb0aa260bfdd2604f2599dbf9278f6b1754a33c7379",
    "mini_moonboard/bolted_timber_checks.py": "a1414547d9eaa3d60e81482b4a2cac2d49e88f31aafa341dca5be9ec8ef4aa13",
    "fea/dowel_yield.py": "d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/material-inputs.json": "0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials.md": "943e5ecb26a5bb9e49e55e4c510bbbf697b08a6b9415c26bbcb41c48db70a2d6",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/fasteners.md": "aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6",
    "docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/materials-source/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-Dowel-type-fasteners.pdf": "5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a",
}

ACTION_PATHS = (
    "docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/upper-joints.json",
    "docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/upper-joints.json",
)
EXPECTED_COUNTS = {
    "upper_blocks": 8,
    "physical_bolt_axes": 32,
    "component_records": 672,
    "six_mode_records": 4032,
    "cases": 3,
    "increments_per_case": 7,
}
DECLARED_CD_SENSITIVITIES = (1.0, 1.25, 1.6)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def require_hash(path: Path, expected: str) -> str:
    actual = sha256(path)
    if actual != expected:
        raise RuntimeError(f"Pinned source changed: {path.relative_to(ROOT)} ({actual})")
    return actual


def check_pinned_sources() -> dict[str, str]:
    return {
        relative: require_hash(ROOT / relative, expected)
        for relative, expected in PINNED_SHA256.items()
    }


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"Expected a JSON object: {path}")
    return value


def assert_close(actual: float, expected: float, *, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=2e-11, abs_tol=2e-8):
        raise RuntimeError(f"{label} did not replay: {actual!r} != {expected!r}")


def verify_reused_partial_thread_packet() -> None:
    """Require the existing packet's own deterministic replay to pass."""
    result = subprocess.run(
        [sys.executable, str(PARTIAL_PRODUCER), "--verify"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise RuntimeError(
            "Existing partial-thread packet did not verify:\n"
            + result.stdout[-3000:]
            + result.stderr[-3000:]
        )


def reduction_terms(
    main_angle: float, side_angle: float, effective_diameter_in: float
) -> dict[str, float]:
    angle_factor = 1 + 0.25 * max(main_angle, side_angle) / 90
    if effective_diameter_in < 0.25:
        kd = 2.2 if effective_diameter_in <= 0.17 else 10 * effective_diameter_in + 0.5
        return dict.fromkeys(MODES, kd * angle_factor)
    return dict(
        zip(
            MODES,
            (
                4 * angle_factor,
                4 * angle_factor,
                3.6 * angle_factor,
                3.2 * angle_factor,
                3.2 * angle_factor,
                3.2 * angle_factor,
            ),
            strict=True,
        )
    )


def single_bolt_reference(
    *,
    lengths_mm: dict[str, float],
    threads_mm: dict[str, float],
    angles_degrees: dict[str, float],
    effective_diameter_in: float,
    fyb_psi: float,
) -> dict:
    """Use the pinned method with explicit block/main and host/side inputs."""
    full_diameter_in = 0.25
    root_diameter_in = 0.189
    if effective_diameter_in == full_diameter_in:
        thread_lengths = threads_mm
    elif effective_diameter_in == root_diameter_in:
        # Explicit alternate sensitivity: treat all wood-bearing length as
        # threaded, selecting Dr in both members. This is not the frozen
        # partial-thread scenario or a claim about a delivered bolt.
        thread_lengths = dict(lengths_mm)
    else:
        raise ValueError("Only the declared nominal-D and Dr sensitivity are supported")

    result = wood_wood_single_shear_reference(
        main_bearing_length_in=lengths_mm["block"] / 25.4,
        side_bearing_length_in=lengths_mm["host"] / 25.4,
        main_load_to_grain_degrees=angles_degrees["block"],
        side_load_to_grain_degrees=angles_degrees["host"],
        main_bolt_axis_parallel_to_grain=False,
        side_bolt_axis_parallel_to_grain=False,
        bolt_full_body_diameter_in=full_diameter_in,
        bolt_thread_root_diameter_in=root_diameter_in,
        main_thread_bearing_length_in=thread_lengths["block"] / 25.4,
        side_thread_bearing_length_in=thread_lengths["host"] / 25.4,
        bolt_bending_yield_moment_lb_in=dowel_bending_yield_moment_lb_in(
            bending_yield_strength_psi=fyb_psi,
            effective_diameter_in=effective_diameter_in,
        ),
        gap_in=0,
        reduction_terms=reduction_terms(
            angles_degrees["block"],
            angles_degrees["host"],
            effective_diameter_in,
        ),
        bolt_bending_yield_strength_psi=(
            fyb_psi if effective_diameter_in < full_diameter_in else None
        ),
    )
    assert_close(
        result["effective_bearing_diameter_in"],
        effective_diameter_in,
        label="effective lateral diameter",
    )
    return result


def as_mode_record(reference: dict, demand_n: float, fyb_psi: float, basis: str) -> dict:
    modes_n = {
        mode: reference["reference_values_lbf"][mode] * LBF_N for mode in MODES
    }
    governing_mode = min(modes_n, key=modes_n.get)
    capacity_n = modes_n[governing_mode]
    return {
        "Fyb_psi": fyb_psi,
        "Fyb_basis": basis,
        "six_unadjusted_mode_references_n": modes_n,
        "governing_mode": governing_mode,
        "governing_unadjusted_reference_n": capacity_n,
        "demand_to_governing_reference": demand_n / capacity_n,
        "required_common_scalar_multiplier_for_unity": demand_n / capacity_n,
        "member_bearing_inputs_psi_block_host": [
            reference["main_bearing_psi"],
            reference["side_bearing_psi"],
        ],
        "effective_bearing_diameter_in": reference["effective_bearing_diameter_in"],
    }


def minimum_fyb_for_unity(
    *,
    demand_n: float,
    cd: float,
    lengths_mm: dict[str, float],
    threads_mm: dict[str, float],
    angles_degrees: dict[str, float],
) -> dict:
    """Solve the Fyb threshold for CD × min(six unadjusted modes) = demand."""

    def margin(fyb: float) -> float:
        reference = single_bolt_reference(
            lengths_mm=lengths_mm,
            threads_mm=threads_mm,
            angles_degrees=angles_degrees,
            effective_diameter_in=0.25,
            fyb_psi=fyb,
        )
        return (
            min(reference["reference_values_lbf"].values()) * LBF_N * cd
            - demand_n
        )

    low = 1e-9
    high = 45_000.0
    while margin(high) < 0 and high < 1e9:
        high *= 2
    if margin(high) < 0:
        return {
            "status": "no_finite_Fyb_threshold_found_within_1e9_psi",
            "minimum_Fyb_psi": None,
            "governing_mode_at_threshold": None,
        }
    for _ in range(100):
        middle = (low + high) / 2
        if margin(middle) >= 0:
            high = middle
        else:
            low = middle
    at_threshold = single_bolt_reference(
        lengths_mm=lengths_mm,
        threads_mm=threads_mm,
        angles_degrees=angles_degrees,
        effective_diameter_in=0.25,
        fyb_psi=high,
    )
    return {
        "status": "conditional_single_bolt_reference_threshold_only",
        "minimum_Fyb_psi": high,
        "declared_CD_sensitivity": cd,
        "governing_mode_at_threshold": at_threshold["governing_mode"],
        "adjusted_conditional_reference_n": (
            at_threshold["reference_lateral_lbf"] * LBF_N * cd
        ),
        "demand_n": demand_n,
        "uses_group_or_other_adjustments": False,
    }


def _load_and_validate_inputs() -> tuple[dict, dict, dict, list[tuple[str, dict]]]:
    check_pinned_sources()
    freeze = load_json(THREAD_FREEZE)
    partial = load_json(PARTIAL_REPORT)
    if freeze.get("full_body_diameter_in") != 0.25:
        raise RuntimeError("Thread freeze no longer declares D = 0.25 in")
    if freeze.get("thread_root_diameter_in_sensitivity") != 0.189:
        raise RuntimeError("Thread freeze no longer declares Dr = 0.189 in")
    if freeze.get("Fyb_psi_commentary_estimate") != 106000:
        raise RuntimeError("Thread freeze commentary Fyb changed")
    if not freeze.get("conditional_only"):
        raise RuntimeError("Partial-thread input no longer declares conditional scope")
    if tuple(freeze.get("action_reports", ())) != ACTION_PATHS:
        raise RuntimeError("Thread freeze action report set changed")
    if partial.get("schema") != "upper-partial-thread-scenario/v1":
        raise RuntimeError("Unexpected partial-thread report schema")
    if partial.get("producer_sha256") != sha256(PARTIAL_PRODUCER):
        raise RuntimeError("Partial-thread report was not produced by the pinned producer")
    if partial.get("freeze_sha256") != sha256(THREAD_FREEZE):
        raise RuntimeError("Partial-thread report does not match the pinned freeze")
    if partial.get("counts") != {
        "upper_blocks": 8,
        "physical_bolt_axes": 32,
        "component_records": 672,
        "cases": 3,
        "increments_per_case": 7,
    }:
        raise RuntimeError("Partial-thread report counts changed")
    for flag in (
        "complete_joint_accepted",
        "six_case_envelope_established",
        "reviewed_geometry_changed",
        "drilling_released",
        "fabrication_released",
        "structural_released",
    ):
        if partial.get(flag) is not False:
            raise RuntimeError(f"Partial-thread report has unexpected {flag} state")

    material_inputs = load_json(MATERIAL_INPUTS)
    if material_inputs.get("schema") is None:
        raise RuntimeError("Pinned material input lacks its schema")
    if "0.50" not in MATERIALS_NOTE.read_text() or "5,600" not in MATERIALS_NOTE.read_text():
        raise RuntimeError("Pinned material note no longer records DF-L / G=0.50 inputs")
    fastener_note = FASTENERS_NOTE.read_text()
    if "restricted to `D ≥ 3/8 in`" not in fastener_note or "does not establish quarter-inch `Fyb`" not in fastener_note:
        raise RuntimeError("Pinned fastener note no longer bounds the 45 ksi example")

    partial_rows: dict[tuple[str, str, str, float], dict] = {}
    for row in partial["rows"]:
        key = (row["source_report"], row["axis_id"], row["case"], row["load_factor"])
        if key in partial_rows:
            raise RuntimeError(f"Duplicate partial-thread state: {key}")
        partial_rows[key] = row
    if len(partial_rows) != 672 or len(partial["axes"]) != 32:
        raise RuntimeError("Partial-thread rows/axes do not match the frozen counts")

    reports: list[tuple[str, dict]] = []
    combined_blocks: set[str] = set()
    combined_axes: set[str] = set()
    for relative in ACTION_PATHS:
        report = load_json(ROOT / relative)
        if report.get("geometry_revision_id") != "led-clearance-2x6-runner-seated-blocks-v1":
            raise RuntimeError(f"Unexpected reviewed geometry revision: {relative}")
        for flag in (
            "complete_joint_resistance_established",
            "six_case_envelope_established",
            "reviewed_geometry_changed",
            "drilling_released",
            "fabrication_released",
            "structural_released",
        ):
            if report.get(flag) is not False:
                raise RuntimeError(f"Action packet has unexpected {flag} state: {relative}")
        if len(report.get("bolt_actions", ())) != 336:
            raise RuntimeError(f"Unexpected action row count: {relative}")
        axis_ids = set(report["geometry_by_axis"])
        blocks = {row["block"] for row in report["bolt_actions"]}
        if len(axis_ids) != 16 or len(blocks) != 4:
            raise RuntimeError(f"Unexpected block/axis count: {relative}")
        if combined_axes.intersection(axis_ids) or combined_blocks.intersection(blocks):
            raise RuntimeError("Action packets overlap their block or axis identities")
        combined_axes.update(axis_ids)
        combined_blocks.update(blocks)
        seen_rows: set[tuple[str, str, str, float]] = set()
        for action in report["bolt_actions"]:
            key = (relative, action["axis_id"], action["case"], action["load_factor"])
            if key in seen_rows:
                raise RuntimeError(f"Duplicate source action state: {key}")
            seen_rows.add(key)
            partial_row = partial_rows.get(key)
            if partial_row is None:
                raise RuntimeError(f"Partial-thread packet is missing state: {key}")
            if partial_row["block"] != action["block"]:
                raise RuntimeError(f"Block identity differs across packets: {key}")
            assert_close(
                partial_row["lateral_demand_n"],
                action["lateral_magnitude_n"],
                label=f"partial-thread/source demand {key}",
            )
        if len(seen_rows) != 336:
            raise RuntimeError(f"Action packet state count changed: {relative}")
        reports.append((relative, report))
    if len(combined_axes) != 32 or len(combined_blocks) != 8:
        raise RuntimeError("Combined source packets do not contain 8 blocks / 32 axes")
    return freeze, partial, partial_rows, reports


def _row_result(
    *,
    relative: str,
    report: dict,
    action: dict,
    partial_rows: dict[tuple[str, str, str, float], dict],
) -> dict:
    axis_id = action["axis_id"]
    geometry = report["geometry_by_axis"].get(axis_id)
    if not geometry or set(geometry.get("members", {})) != {"block", "host"}:
        raise RuntimeError(f"Missing two-member geometry for axis {axis_id}")
    thread_axis = load_partial_axis(partial_rows, relative, action)
    selector = thread_axis.get("diameter_selector", {})
    if selector.get("diameter_case") != "full_body_D" or selector.get("effective_lateral_diameter_in") != 0.25:
        raise RuntimeError(f"Declared partial-thread input did not select full D: {axis_id}")
    lengths_mm = {
        role: geometry["members"][role]["bearing_length_mm"]
        for role in ("block", "host")
    }
    threads_mm = {
        role: thread_axis["members"][role]["declared_thread_bearing_mm"]
        for role in ("block", "host")
    }
    angles = {
        role: action["member_directions"][role]["unsigned_load_to_grain_degrees"]
        for role in ("block", "host")
    }
    if any(not math.isfinite(x) or x <= 0 for x in lengths_mm.values()):
        raise RuntimeError(f"Invalid bearing length on {axis_id}")
    if any(not math.isfinite(x) or not 0 <= x <= 90 for x in angles.values()):
        raise RuntimeError(f"Invalid load/grain angle on {axis_id}")

    demand = action["lateral_magnitude_n"]
    if not math.isfinite(demand) or demand <= 0:
        raise RuntimeError(f"Invalid lateral demand on {axis_id}")
    commentary = single_bolt_reference(
        lengths_mm=lengths_mm,
        threads_mm=threads_mm,
        angles_degrees=angles,
        effective_diameter_in=0.25,
        fyb_psi=106000,
    )
    if commentary["effective_bearing_diameter_in"] != 0.25:
        raise RuntimeError(f"Nominal full-D sensitivity failed on {axis_id}")
    partial_row = partial_rows[(relative, axis_id, action["case"], action["load_factor"])]
    modes_from_prior = partial_row["full_D_six_reference_modes_n"]
    our_record = as_mode_record(
        commentary,
        demand,
        106000,
        "Unadopted 106 ksi commentary estimate; not guaranteed or observed Fyb.",
    )
    for mode in MODES:
        assert_close(
            our_record["six_unadjusted_mode_references_n"][mode],
            modes_from_prior[mode],
            label=f"six-mode replay {axis_id} {action['case']} {action['load_factor']} {mode}",
        )
    assert_close(
        our_record["governing_unadjusted_reference_n"],
        partial_row["conditional_full_D_reference_n"],
        label=f"governing reference replay {axis_id}",
    )

    table_45k = single_bolt_reference(
        lengths_mm=lengths_mm,
        threads_mm=threads_mm,
        angles_degrees=angles,
        effective_diameter_in=0.25,
        fyb_psi=45000,
    )
    table_record = as_mode_record(
        table_45k,
        demand,
        45000,
        "Hypothetical 45 ksi source-table sensitivity only; the cited Table I1/TR12 example is limited to D >= 3/8 in and does not qualify a 1/4-in Fyb or any product.",
    )
    root_sensitivity = single_bolt_reference(
        lengths_mm=lengths_mm,
        threads_mm=threads_mm,
        angles_degrees=angles,
        effective_diameter_in=0.189,
        fyb_psi=106000,
    )
    root_record = as_mode_record(
        root_sensitivity,
        demand,
        106000,
        "Unadopted 106 ksi estimate with all wood-bearing length set to Dr=0.189 in; alternate sensitivity only.",
    )
    direct_steel = action.get("direct_steel_reference")
    if not isinstance(direct_steel, dict):
        raise TypeError(f"Missing same-state direct-steel source record: {axis_id}")
    if direct_steel.get("status") != "material_first_yield_reference_only":
        raise RuntimeError(f"Unexpected direct-steel source basis: {axis_id}")
    if direct_steel.get("interaction_rule") != "unresolved":
        raise RuntimeError(f"Unexpected direct-steel interaction status: {axis_id}")

    return {
        "source_report": relative,
        "case": action["case"],
        "load_factor": action["load_factor"],
        "increment_index": action["increment_index"],
        "block": action["block"],
        "axis_id": axis_id,
        "lateral_demand_n": demand,
        "source_lateral_force_on_block_n": action["lateral_force_on_block_n"],
        "source_lateral_force_rounding_radius_n": action["lateral_force_rounding_radius_n"],
        "source_lateral_magnitude_n": action["lateral_magnitude_n"],
        "source_lateral_action_name": action["lateral_source_name"],
        "source_lateral_row_ids": action["lateral_source_row_ids"],
        "source_axial_force_on_block_n_same_state": action["axial_force_on_block_n"],
        "source_axial_force_rounding_radius_n_same_state": action["axial_force_rounding_radius_n"],
        "source_axial_tension_n_same_state": action["axial_tension_n"],
        "block_member": geometry["members"]["block"]["member"],
        "host_member": geometry["members"]["host"]["member"],
        "bearing_lengths_mm_block_host": lengths_mm,
        "load_to_grain_angles_degrees_block_host": angles,
        "declared_partial_thread_scenario_id": thread_axis["scenario_id"],
        "declared_thread_bearing_mm_block_host": threads_mm,
        "thread_quarter_rule_full_D_condition": selector,
        "full_D_Fyb106ksi_commentary_estimate": our_record,
        "full_D_Fyb45000_source_table_scope_limited_sensitivity": table_record,
        "all_thread_Dr0189in_sensitivity_Fyb106ksi": root_record,
        "same_state_source_component_references": {
            "direct_steel_reference": direct_steel,
            "washer_tension_to_ideal_annulus_reference": action.get(
                "washer_tension_to_ideal_annulus_reference"
            ),
            "nut_capacity_comparison": "not_performed; no matched nut material/section capacity input in this action packet",
        },
        "complete_joint_accepted": False,
    }


def load_partial_axis(
    partial_rows: dict[tuple[str, str, str, float], dict],
    relative: str,
    action: dict,
) -> dict:
    key = (relative, action["axis_id"], action["case"], action["load_factor"])
    row = partial_rows.get(key)
    if row is None:
        raise RuntimeError(f"Partial-thread state is missing: {key}")
    # Axes are keyed by axis_id, and each axis belongs to exactly one report.
    # The sibling state row carries its axis member/thread interval result.
    return partial_rows_axis(row, action["axis_id"])


def partial_rows_axis(row: dict, axis_id: str) -> dict:
    # The caller's row is joined against the current partial report in produce;
    # this helper is replaced through the axis registry attached to that row.
    axis = row.get("_axis")
    if not isinstance(axis, dict) or axis.get("axis_id") != axis_id:
        raise RuntimeError(f"Internal axis registry missing or mismatched: {axis_id}")
    return axis


def _build_partial_row_index(partial: dict) -> dict[tuple[str, str, str, float], dict]:
    axes = partial["axes"]
    index = {}
    for row in partial["rows"]:
        key = (row["source_report"], row["axis_id"], row["case"], row["load_factor"])
        axis = axes.get(row["axis_id"])
        if not isinstance(axis, dict):
            raise TypeError(f"Missing axis geometry in partial-thread packet: {row['axis_id']}")
        # A private in-memory join avoids writing a mutated copy back to disk.
        index[key] = {**row, "_axis": {**axis, "axis_id": row["axis_id"]}}
    return index


def produce() -> dict:
    """Recompute every frozen lateral mode and requested sensitivity."""
    source_hashes = check_pinned_sources()
    _freeze, partial, _, reports = _load_and_validate_inputs()
    partial_rows = _build_partial_row_index(partial)
    rows = []
    source_case_names: set[str] = set()
    source_load_factors: set[float] = set()
    for relative, report in reports:
        for action in report["bolt_actions"]:
            source_case_names.add(action["case"])
            source_load_factors.add(action["load_factor"])
            rows.append(
                _row_result(
                    relative=relative,
                    report=report,
                    action=action,
                    partial_rows=partial_rows,
                )
            )
    if len(rows) != EXPECTED_COUNTS["component_records"]:
        raise RuntimeError(f"Expected 672 same-state action records; got {len(rows)}")
    axes = {row["axis_id"] for row in rows}
    blocks = {row["block"] for row in rows}
    if len(axes) != EXPECTED_COUNTS["physical_bolt_axes"] or len(blocks) != EXPECTED_COUNTS["upper_blocks"]:
        raise RuntimeError("Output axis/block identity counts changed")
    if len(source_case_names) != EXPECTED_COUNTS["cases"] or len(source_load_factors) != EXPECTED_COUNTS["increments_per_case"]:
        raise RuntimeError("Source case/increment counts changed")

    maxima = {}
    for block in sorted(blocks):
        sampled = [row for row in rows if row["block"] == block]
        peak = max(
            sampled,
            key=lambda row: row["full_D_Fyb106ksi_commentary_estimate"][
                "demand_to_governing_reference"
            ],
        )
        mode_result = peak["full_D_Fyb106ksi_commentary_estimate"]
        maxima[block] = {
            "state_count": len(sampled),
            "case": peak["case"],
            "load_factor": peak["load_factor"],
            "axis_id": peak["axis_id"],
            "lateral_demand_n": peak["lateral_demand_n"],
            "governing_mode": mode_result["governing_mode"],
            "unadjusted_reference_n": mode_result["governing_unadjusted_reference_n"],
            "demand_to_unadjusted_reference": mode_result["demand_to_governing_reference"],
            "minimum_common_scalar_multiplier_for_unity": mode_result[
                "required_common_scalar_multiplier_for_unity"
            ],
            "minimum_resistance_increase_percent_for_unity": (
                mode_result["required_common_scalar_multiplier_for_unity"] - 1
            )
            * 100,
            "max_over_21_sampled_states_only": True,
        }

    outer = {}
    for block in ("top_outer_left_cleat", "top_outer_right_cleat"):
        peak = max(
            (row for row in rows if row["block"] == block),
            key=lambda row: row["full_D_Fyb106ksi_commentary_estimate"][
                "demand_to_governing_reference"
            ],
        )
        lengths_mm = peak["bearing_lengths_mm_block_host"]
        threads_mm = peak["declared_thread_bearing_mm_block_host"]
        angles = peak["load_to_grain_angles_degrees_block_host"]
        cd_rows = []
        for cd in DECLARED_CD_SENSITIVITIES:
            threshold = minimum_fyb_for_unity(
                demand_n=peak["lateral_demand_n"],
                cd=cd,
                lengths_mm=lengths_mm,
                threads_mm=threads_mm,
                angles_degrees=angles,
            )
            table_cap = (
                peak["full_D_Fyb45000_source_table_scope_limited_sensitivity"][
                    "governing_unadjusted_reference_n"
                ]
                * cd
            )
            commentary_cap = (
                peak["full_D_Fyb106ksi_commentary_estimate"][
                    "governing_unadjusted_reference_n"
                ]
                * cd
            )
            cd_rows.append(
                {
                    **threshold,
                    "Fyb45000_reference_times_declared_CD_n": table_cap,
                    "Fyb45000_demand_to_that_conditional_value": peak["lateral_demand_n"] / table_cap,
                    "Fyb106000_reference_times_declared_CD_n": commentary_cap,
                    "Fyb106000_demand_to_that_conditional_value": peak["lateral_demand_n"] / commentary_cap,
                    "CD_is_adopted": False,
                }
            )
        outer[block] = {
            "governing_state": {
                "source_report": peak["source_report"],
                "case": peak["case"],
                "load_factor": peak["load_factor"],
                "axis_id": peak["axis_id"],
            },
            "lateral_demand_n": peak["lateral_demand_n"],
            "same_state_lateral_force_on_block_n": peak["source_lateral_force_on_block_n"],
            "same_state_axial_tension_n": peak["source_axial_tension_n_same_state"],
            "Fyb106000_conditional_unadjusted_reference_n": peak[
                "full_D_Fyb106ksi_commentary_estimate"
            ]["governing_unadjusted_reference_n"],
            "Fyb106000_demand_to_unadjusted_reference": peak[
                "full_D_Fyb106ksi_commentary_estimate"
            ]["demand_to_governing_reference"],
            "Fyb45000_hypothetical_scope_limited_sensitivity_reference_n": peak[
                "full_D_Fyb45000_source_table_scope_limited_sensitivity"
            ]["governing_unadjusted_reference_n"],
            "Fyb45000_demand_to_unadjusted_reference": peak[
                "full_D_Fyb45000_source_table_scope_limited_sensitivity"
            ]["demand_to_governing_reference"],
            "Dr0189_all_thread_Fyb106000_sensitivity_reference_n": peak[
                "all_thread_Dr0189in_sensitivity_Fyb106ksi"
            ]["governing_unadjusted_reference_n"],
            "Dr0189_all_thread_Fyb106000_demand_to_reference": peak[
                "all_thread_Dr0189in_sensitivity_Fyb106ksi"
            ]["demand_to_governing_reference"],
            "minimum_total_uniform_multiplier_for_unity_before_any_end_use_adjustments": peak[
                "full_D_Fyb106ksi_commentary_estimate"
            ]["required_common_scalar_multiplier_for_unity"],
            "minimum_Fyb_by_conditional_CD_sensitivity": cd_rows,
            "same_state_direct_component_context": peak[
                "same_state_source_component_references"
            ],
            "nut_capacity_comparison": "not available in the pinned action packet; no nut material/section capacity is inferred",
        }

    return {
        "schema": "upper-block-conditional-lateral-components/v1",
        "status": "CONDITIONAL_SINGLE_BOLT_LATERAL_COMPONENTS_ONLY",
        "candidate_geometry_revision": "led-clearance-2x6-runner-seated-blocks-v1",
        "counts": {
            **EXPECTED_COUNTS,
            "source_action_packets": len(reports),
            "states_per_axis": 21,
        },
        "source_hashes": source_hashes,
        "producer_sha256": sha256(Path(__file__)),
        "thread_freeze_sha256": sha256(THREAD_FREEZE),
        "partial_thread_report_sha256": sha256(PARTIAL_REPORT),
        "source_case_names": sorted(source_case_names),
        "source_load_factors": sorted(source_load_factors),
        "conditional_input_basis": {
            "wood_scenario": "DF-L No. 2 conditional arithmetic; G=0.50 per pinned NDS material note, not observed stock",
            "nominal_lateral_diameter_in": 0.25,
            "partial_thread_scenario": "Frozen thread intervals and member lengths from service packet; the full-body quarter-member selector must return D for each axis.",
            "Fyb106000_psi": "Unadopted commentary estimate; not test-derived, guaranteed, or received bolt property.",
            "Fyb45000_psi": "Hypothetical source-table sensitivity only. The cited Table I1/TR12 45 ksi example is limited to D >= 3/8 in; Table 12A does not qualify quarter-inch Fyb. Not a product property or adoption.",
            "end_use_adjustments": "None applied in the 672 rows. CD values appear only in requested algebraic threshold sensitivities.",
            "source_member_roles": "Block is supplied as the main member and host as the side member, matching the existing partial-thread producer inputs.",
        },
        "method_limits": [
            "Six unadjusted two-member single-shear modes only; no group, duration, wet-service, temperature, treatment, or other adjustment is adopted.",
            "No splitting, net-section, row tear-out, bearing distribution, continuous three-receiver transfer, slip, or complete-joint resistance is established.",
            "The 0.189-in all-thread sensitivity is a separate hypothetical Dr case and does not replace the declared partial-thread condition.",
            "Fyb=106 ksi is an unadopted commentary estimate. Fyb=45 ksi is shown only as a hypothetical source-table sensitivity; the cited example is limited to D >= 3/8 in and does not qualify a quarter-inch bolt or its Fyb.",
            "CD=1, 1.25, and 1.6 are illustrative multipliers used only for minimum-Fyb threshold calculations; none is selected or applied to the action rows.",
            "Same-state source axial force and direct component references are copied separately. No axial/lateral interaction is formed, no nut capacity is inferred, and no bolt bending is inferred from a resultant.",
            "No complete joint, drilling, fabrication, structural, or climbing release is made.",
        ],
        "sampled_maxima_by_block": maxima,
        "top_outer_conditional_sensitivities": outer,
        "rows": rows,
        "complete_joint_accepted": False,
        "six_case_envelope_established": False,
        "reviewed_geometry_changed": False,
        "drilling_released": False,
        "fabrication_released": False,
        "structural_released": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true", help="replay and compare ignored lateral.json")
    mode.add_argument("--write", action="store_true", help="replay and write ignored lateral.json")
    args = parser.parse_args()
    verify_reused_partial_thread_packet()
    report = produce()
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.verify:
        if not OUTPUT.exists():
            raise RuntimeError(f"Missing ignored replay output: {OUTPUT}")
        if OUTPUT.read_text() != serialized:
            raise RuntimeError(f"Replay differs from {OUTPUT}")
    else:
        OUTPUT.write_text(serialized)
    print(
        json.dumps(
            {
                "counts": report["counts"],
                "top_outer_conditional_sensitivities": report[
                    "top_outer_conditional_sensitivities"
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
