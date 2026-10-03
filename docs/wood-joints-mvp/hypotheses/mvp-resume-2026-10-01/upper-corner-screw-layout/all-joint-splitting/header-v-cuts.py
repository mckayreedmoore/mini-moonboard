"""Compare source-point and mapped-field signed v cuts for header cleats.

Parent runs this frozen consumer after pinning header-boundary output. It
integrates only saved washer, trimmed-contact, and bore-pressure fields. Every
source residual stays at its exact source point/free couple. No resistance or
joint acceptance is calculated.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
UPPER = HERE.parent
RAW = UPPER / "rawlocal/header-v-cuts"
ROOT = next(path for path in HERE.parents if (path / "current-candidate.json").is_file())
FLAGS = {
    "new_splitting_capacity": False,
    "splitting_qualified": False,
    "complete_joint_acceptance": False,
    "formal_criterion_acceptance": False,
    "fabrication_release": False,
    "physical_release": False,
    "proposal_108_adopted": False,
}
FORCE_TOL_N = 1e-7
MOMENT_TOL_NMM = 1e-5
GRAVITY_TOL = 1e-6
POINT_TOL_MM = 1e-6
GEOMETRY_TOL_MM = 1e-7
ALIGN_TOL = 1e-8
BOUNDARY_SOURCE_SHA256 = "e7c2a0be9577a9946a61736cb06c913874337549d2934ba0af1a9852cc6788ea"
BOUNDARY_DOC_SHA256 = "5e9e68f8135b94862d9ab61d64d78d6f91522dce33d1970cb1052a561d24f41e"


class UnsupportedField(ValueError):
    """One saved field cannot be integrated by the existing exact helpers."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("STOP: " + message)


def sha(path: Path) -> str:
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path: Path) -> Any:
    return json.loads(Path(path).read_text())


def write(path: Path, value: Any) -> None:
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def path_key(path: Path) -> str:
    path = Path(path)
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def authenticate(pins: dict[Path, str]) -> None:
    for path, expected in pins.items():
        require(path.is_file(), f"missing frozen source: {path}")
        observed = sha(path)
        require(observed == expected, f"changed frozen source: {path}; got {observed}")


def module(path: Path, name: str) -> Any:
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"helper unavailable: {path}")
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def vec(value: Any, shape: tuple[int, ...] = (3,)) -> np.ndarray:
    result = np.asarray(value, dtype=float)
    require(result.shape == shape and np.isfinite(result).all(), "invalid saved vector")
    return result


def frame_axis(frame: np.ndarray, axis: int) -> np.ndarray:
    return np.asarray(frame[axis], dtype=float)


def aligned_coordinate(direction: np.ndarray, axes: list[np.ndarray], label: str) -> tuple[int, float]:
    dots = np.asarray([float(direction @ axis) for axis in axes])
    index = int(np.argmax(np.abs(dots)))
    require(
        abs(abs(dots[index]) - 1.0) < ALIGN_TOL
        and all(abs(dots[j]) < ALIGN_TOL for j in range(len(dots)) if j != index),
        f"{label} is not aligned with a saved pressure-domain coordinate",
    )
    return index, float(dots[index])


def wrench_global(actions: list[dict[str, Any]], datum: np.ndarray) -> np.ndarray:
    result = np.zeros(6)
    for action in actions:
        force = vec(action["force_n"])
        point = vec(action["point_mm"])
        result[:3] += force
        result[3:] += np.cross(point - datum, force)
        result[3:] += vec(action.get("free_moment_nmm", [0.0, 0.0, 0.0]))
    return result


def local_wrench(global_wrench: np.ndarray, frame: np.ndarray) -> np.ndarray:
    return np.r_[global_wrench[:3] @ frame.T, global_wrench[3:] @ frame.T]


def local_point_wrench(
    action: dict[str, Any], own: dict[str, Any], station: float | None = None, limit: str | None = None
) -> np.ndarray:
    point = (vec(action["point_mm"]) - own["start"]) @ own["frame"].T
    force = vec(action["force_n"]) @ own["frame"].T
    couple = vec(action.get("free_moment_nmm", [0.0, 0.0, 0.0])) @ own["frame"].T
    if station is None:
        origin = np.zeros(3)
    else:
        require(limit in ("before", "after"), "invalid cut limit")
        included = (
            point[2] < station - POINT_TOL_MM
            if limit == "before"
            else point[2] <= station + POINT_TOL_MM
        )
        if not included:
            return np.zeros(6)
        origin = np.array([0.0, 0.0, station])
    return np.r_[force, np.cross(point - origin, force) + couple]


def disk_integrals(
    disk_helper: Any, radius: float, sign: float, delta: float | None
) -> np.ndarray:
    if delta is None:
        low, high = -radius, radius
    elif sign > 0:
        low, high = -radius, delta
    else:
        low, high = -delta, radius
    return disk_helper.disk_strip(low, high, 0.0, 0.0, radius)


def annulus_field_wrench(
    field: dict[str, Any], own: dict[str, Any], station: float | None, datum: np.ndarray, disk_helper: Any
) -> np.ndarray:
    domain = field["domain"]
    center = vec(domain["plane_point_xyz_mm"])
    axes = [vec(domain["basis_u_xyz"]), vec(domain["basis_v_xyz"])]
    selected, sign = aligned_coordinate(frame_axis(own["frame"], 2), axes, "cleat v axis")
    delta = None
    if station is not None:
        center_v = float(((center - own["start"]) @ own["frame"].T)[2])
        delta = station - center_v
    inner = float(domain["inner_radius_mm"])
    outer = float(domain["outer_radius_mm"])
    integrals = disk_integrals(disk_helper, outer, sign, delta)
    integrals -= disk_integrals(disk_helper, inner, sign, delta)
    area = float(integrals[0])
    first_global = area * center + integrals[1] * axes[selected] + integrals[2] * axes[1 - selected]
    pressure_vector = float(domain["pressure_mpa"]) * vec(domain["normal_into_body_xyz"])
    force = area * pressure_vector
    moment = np.cross(first_global - area * datum, pressure_vector)
    if station is None:
        require(
            abs(area - float(domain["area_mm2"])) < 1e-8,
            "annulus full-area integral differs from saved domain",
        )
        require(
            np.max(abs(force - vec(field["integrated_force_xyz_n"]))) < FORCE_TOL_N,
            "annulus full-force integral differs from saved field",
        )
    return np.r_[force, moment]


def contact_integrals(
    field: dict[str, Any], own: dict[str, Any], station: float | None, tile_helper: Any
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    domain = field["domain"]
    trimmed = domain["trimmed_domain"]
    body_v = frame_axis(own["frame"], 2)
    cell_bounds_uv = domain["sampler"]["cell_rectangle_patch_uv_mm"]
    corners = [
        vec(point) for point in trimmed["cell_rectangle_global_corners_xyz_mm"]
    ]
    require(len(corners) == 4, "saved contact cell needs four global corners")
    u_bounds, v_bounds = cell_bounds_uv
    axes = [
        (corners[2] - corners[0]) / (u_bounds[1] - u_bounds[0]),
        (corners[1] - corners[0]) / (v_bounds[1] - v_bounds[0]),
    ]
    axes = [axis / np.linalg.norm(axis) for axis in axes]
    origin = corners[0] - u_bounds[0] * axes[0] - v_bounds[0] * axes[1]
    selected, sign = aligned_coordinate(body_v, axes, "cleat v axis")
    other = 1 - selected
    bounds = [cell_bounds_uv[selected], cell_bounds_uv[other]]
    bores = []
    for index, circle in enumerate(trimmed["excluded_circles_patch_uv"]):
        center_uv = vec(circle["center_patch_uv_mm"])
        bores.append(
            {
                "axis_id": f"saved-contact-bore-{index}",
                "station_mm": float(center_uv[selected]),
                "transverse_center_mm": float(center_uv[other]),
                "radius_mm": float(circle["radius_mm"]),
            }
        )

    def integral(cut: float | None) -> np.ndarray:
        raw = tile_helper.supported_tile_integrals(bounds, bores, cut=cut)
        return np.asarray(raw, dtype=float)

    total = integral(None)
    if station is None:
        value = total
    else:
        base = float((origin - own["start"]) @ body_v)
        cut_coordinate = (station - base) / sign
        prefix = integral(cut_coordinate)
        value = prefix if sign > 0 else total - prefix
    first_global = (
        value[0] * origin + value[1] * axes[selected] + value[2] * axes[other]
    )
    return value, first_global, total


def contact_field_wrench(
    field: dict[str, Any], own: dict[str, Any], station: float | None, datum: np.ndarray, tile_helper: Any
) -> np.ndarray:
    integral, first_global, total = contact_integrals(field, own, station, tile_helper)
    area = float(integral[0])
    pressure_vector = float(field["pressure_mpa"]) * vec(field["domain"]["normal_into_body_xyz"])
    force = area * pressure_vector
    moment = np.cross(first_global - area * datum, pressure_vector)
    if station is None:
        expected = float(field["domain"]["source_cell_area_mm2"])
        require(abs(float(total[0]) - expected) < 1e-3, "trimmed contact full-area integral differs from saved cell")
        require(
            np.max(abs(force - vec(field["integrated_force_xyz_n"]))) < FORCE_TOL_N,
            "trimmed contact full-force integral differs from saved field",
        )
    return np.r_[force, moment]


def bore_field_wrench(
    field: dict[str, Any], own: dict[str, Any], station: float | None, datum: np.ndarray, bore_helper: Any
) -> np.ndarray:
    profile = field["profile"]
    low_active, high_active = map(float, profile["active_angle_interval_rad"])
    if station is None:
        return bore_helper.pressure_arc_wrench(profile, datum, low_active, high_active)

    e, h = np.asarray(profile["pressure_basis_e_h_xyz"], dtype=float)
    radius = float(profile["radius_mm"])
    axis_point = vec(profile["axis_point_xyz_mm"])
    body_v = frame_axis(own["frame"], 2)
    a = radius * float(e @ body_v)
    b = radius * float(h @ body_v)
    target = station - float((axis_point - own["start"]) @ body_v)
    roots = bore_helper.coordinate_roots(a, b, target)
    bounds = [low_active, *sorted(roots), high_active]
    total = np.zeros(6)
    cut_datum = own["start"] + station * body_v
    for index in range(len(bounds) - 1):
        low, high = bounds[index], bounds[index + 1]
        if high - low <= 1e-13:
            continue
        middle = (low + high) / 2
        coordinate = a * math.cos(middle) + b * math.sin(middle)
        if coordinate <= target + GEOMETRY_TOL_MM:
            total += bore_helper.pressure_arc_wrench(profile, cut_datum, low, high)
    return total


def field_global_wrench(
    field: dict[str, Any],
    own: dict[str, Any],
    station: float | None,
    datum: np.ndarray,
    disk_helper: Any,
    tile_helper: Any,
    bore_helper: Any,
) -> np.ndarray:
    kind = field["field_kind"]
    if kind == "uniform_compressive_pressure_on_supported_annulus":
        return annulus_field_wrench(field, own, station, datum, disk_helper)
    if kind == "uniform_frictionless_normal_pressure_on_saved_trimmed_cell":
        return contact_field_wrench(field, own, station, datum, tile_helper)
    if kind == "nonnegative_half_cosine_radial_bore_pressure":
        return bore_field_wrench(field, own, station, datum, bore_helper)
    raise UnsupportedField(f"unsupported saved header field kind: {kind}")


def action_recovery(
    item: dict[str, Any],
    own: dict[str, Any],
    interface_datum: np.ndarray,
    disk_helper: Any,
    tile_helper: Any,
    bore_helper: Any,
) -> dict[str, Any]:
    source = item["source_action"]
    status = item.get("field_status", "UNSUPPORTED_FIELD_STATUS_MISSING")
    fields = item.get("boundary_fields", [])
    field_full_global = np.zeros(6)
    failure = None
    if status == "MAPPED_WITH_EXPLICIT_SOURCE_RESIDUALS":
        try:
            for field in fields:
                field_full_global += field_global_wrench(
                    field, own, None, own["start"], disk_helper, tile_helper, bore_helper
                )
        except (UnsupportedField, ValueError, AssertionError, KeyError, IndexError) as exc:
            failure = f"{type(exc).__name__}: {exc}"
            fields = []
            field_full_global = np.zeros(6)
    elif status != "ZERO_SOURCE_FORCE_NO_PRESSURE_FIELD":
        failure = f"saved field status remains explicit: {status}"
        fields = []

    field_full_local = local_wrench(field_full_global, own["frame"])
    if failure is not None:
        residual = {
            "point_mm": source["point_mm"],
            "force_n": source["force_n"],
            "free_moment_nmm": source["free_moment_nmm"],
            "source_row": int(source["row"]),
            "source_id": source["source_id"],
            "role": source["role"],
        }
        field_full_local[:] = 0.0
        status_out = "SOURCE_POINT_RETAINED_FIELD_UNSUPPORTED"
    else:
        point_local = (vec(source["point_mm"]) - own["start"]) @ own["frame"].T
        source_force_local = vec(source["force_n"]) @ own["frame"].T
        source_couple_local = vec(source["free_moment_nmm"]) @ own["frame"].T
        residual_force_local = source_force_local - field_full_local[:3]
        field_moment_at_source = field_full_local[3:] - np.cross(
            point_local, field_full_local[:3]
        )
        residual_couple_local = source_couple_local - field_moment_at_source
        residual = {
            "point_mm": source["point_mm"],
            "force_n": (residual_force_local @ own["frame"]).tolist(),
            "free_moment_nmm": (residual_couple_local @ own["frame"]).tolist(),
            "source_row": int(source["row"]),
            "source_id": source["source_id"],
            "role": source["role"],
        }
        status_out = "FIELD_PLUS_EXACT_SOURCE_POINT_RESIDUAL"

    residual_local = local_point_wrench(residual, own)
    mixed_full_local = field_full_local + residual_local
    source_about_interface = wrench_global([source], interface_datum)
    field_about_interface = np.r_[
        field_full_global[:3],
        field_full_global[3:] + np.cross(own["start"] - interface_datum, field_full_global[:3]),
    ]
    residual_about_interface = source_about_interface - field_about_interface
    mixed_about_interface = field_about_interface + residual_about_interface
    require(
        max(abs(mixed_about_interface[:3] - source_about_interface[:3])) < FORCE_TOL_N
        and max(abs(mixed_about_interface[3:] - source_about_interface[3:])) < MOMENT_TOL_NMM,
        f"header source-row wrench balance failed: {source['source_id']}",
    )
    saved_residual = item.get("source_to_field_wrench_residual_xyz_n_nmm")
    saved_residual_error = None
    if saved_residual is not None and failure is None:
        saved_residual_error = residual_about_interface - vec(saved_residual, (6,))
        require(
            max(abs(saved_residual_error[:3])) < FORCE_TOL_N
            and max(abs(saved_residual_error[3:])) < MOMENT_TOL_NMM,
            f"integrated field differs from saved boundary residual: {source['source_id']}",
        )
    return {
        "source": source,
        "fields": fields,
        "field_full_wrench_local_about_body_start_n_nmm": field_full_local.tolist(),
        "residual_point": residual,
        "mixed_full_wrench_local_about_body_start_n_nmm": mixed_full_local.tolist(),
        "field_recovery_status": status_out,
        "unsupported_field_reason": failure,
        "unmapped_source_force_xyz_n": item.get("unmapped_source_force_xyz_n", source["force_n"]),
        "unmapped_source_free_moment_nmm": item.get(
            "unmapped_source_free_moment_nmm", source["free_moment_nmm"]
        ),
        "computed_source_to_field_residual_xyz_n_nmm_about_interface": residual_about_interface.tolist(),
        "saved_source_to_field_residual_difference_xyz_n_nmm": (
            None if saved_residual_error is None else saved_residual_error.tolist()
        ),
    }


def field_cut_local(
    recovery: dict[str, Any],
    own: dict[str, Any],
    station: float,
    disk_helper: Any,
    tile_helper: Any,
    bore_helper: Any,
) -> np.ndarray:
    cut_datum = own["start"] + station * frame_axis(own["frame"], 2)
    field_global = np.zeros(6)
    for field in recovery["fields"]:
        field_global += field_global_wrench(
            field, own, station, cut_datum, disk_helper, tile_helper, bore_helper
        )
    return local_wrench(field_global, own["frame"])


def physical_gravity_cut(
    own: dict[str, Any], physical_math: Any, station: float, limit: str
) -> np.ndarray:
    volume, first = own["volume_function"](own["geom"], 2, station)
    first = np.asarray(first, dtype=float)
    timber = np.r_[
        volume * own["body_force"],
        np.cross(first - np.array([0.0, 0.0, station]) * volume, own["body_force"]),
    ]
    return timber + physical_math.point_gravity(own["hardware"], 2, station, limit)


def signed_q(internal_local: np.ndarray) -> np.ndarray:
    order = [2, 0, 1]
    return np.r_[internal_local[:3][order], internal_local[3:][order]]


def cut_row(
    body: str,
    case_id: str,
    station: float,
    limit: str,
    own: dict[str, Any],
    recoveries: list[dict[str, Any]],
    retained: list[dict[str, Any]],
    gravity_points: list[dict[str, Any]],
    physical_math: Any,
    normal_math: Any,
    remaining: Any,
    disk_helper: Any,
    tile_helper: Any,
    bore_helper: Any,
) -> dict[str, Any]:
    original_external = np.zeros(6)
    mapped_external = np.zeros(6)
    for recovery in recoveries:
        original_external += local_point_wrench(recovery["source"], own, station, limit)
        mapped_external += field_cut_local(
            recovery, own, station, disk_helper, tile_helper, bore_helper
        )
        mapped_external += local_point_wrench(
            recovery["residual_point"], own, station, limit
        )
    for action in retained:
        if action["role"] != "discrete_body_load":
            original_external += local_point_wrench(action, own, station, limit)
            mapped_external += local_point_wrench(action, own, station, limit)
    for action in gravity_points:
        original_external += local_point_wrench(action, own, station, limit)
    old_physical_gravity = physical_math.point_gravity(
        # The archive's exact mapped gravity point rows, prepared by caller.
        own["source_gravity_prepared"],
        2,
        station,
        limit,
    )
    source_gravity_cut = sum(
        (local_point_wrench(action, own, station, limit) for action in gravity_points),
        np.zeros(6),
    )
    require(
        np.max(abs(source_gravity_cut - old_physical_gravity)) < GRAVITY_TOL,
        "saved discrete gravity point cut differs from reused point-gravity helper",
    )
    mapped_physical_gravity = physical_gravity_cut(own, physical_math, station, limit)
    mapped_external += mapped_physical_gravity

    old_internal = -original_external
    mapped_internal = -mapped_external
    old_q, mapped_q = signed_q(old_internal), signed_q(mapped_internal)
    hull = [
        [0.0, float(own["geom"]["grain_length_mm"])],
        [-float(own["geom"]["width_depth_mm"][0]) / 2, float(own["geom"]["width_depth_mm"][0]) / 2],
    ]
    old_normal = normal_math.normal_bound(old_q.tolist(), hull)
    mapped_normal = normal_math.normal_bound(mapped_q.tolist(), hull)
    try:
        old_pressure = remaining.finite_pressure(old_q.tolist(), own["geom"], 2, station, normal_math)
    except (ValueError, AssertionError, KeyError, IndexError) as exc:
        old_pressure = {"status": "UNSUPPORTED_EXISTING_FINITE_PRESSURE_WITNESS", "reason": f"{type(exc).__name__}: {exc}"}
    try:
        mapped_pressure = remaining.finite_pressure(mapped_q.tolist(), own["geom"], 2, station, normal_math)
    except (ValueError, AssertionError, KeyError, IndexError) as exc:
        mapped_pressure = {"status": "UNSUPPORTED_EXISTING_FINITE_PRESSURE_WITNESS", "reason": f"{type(exc).__name__}: {exc}"}
    old_t = float(old_normal["minimum_tensile_normal_resultant_n"])
    mapped_t = float(mapped_normal["minimum_tensile_normal_resultant_n"])
    return {
        "body": body,
        "case_id": case_id,
        "axis": 2,
        "station_mm": station,
        "limit": limit,
        "original_source_point_signed_internal_n_nmm": old_q.tolist(),
        "mapped_full_cut_signed_internal_n_nmm": mapped_q.tolist(),
        "original_normal_hull_minimum_tensile_resultant_n": old_t,
        "mapped_normal_hull_minimum_tensile_resultant_n": mapped_t,
        "mapped_minus_original_normal_hull_tensile_resultant_n": mapped_t - old_t,
        "original_normal_hull_diagnostic": old_normal,
        "mapped_normal_hull_diagnostic": mapped_normal,
        "original_existing_finite_pressure_witness": old_pressure,
        "mapped_existing_finite_pressure_witness": mapped_pressure,
        "original_mapped_gravity_negative_half_n_nmm": old_physical_gravity.tolist(),
        "physical_gravity_negative_half_n_nmm": mapped_physical_gravity.tolist(),
        "free_couples_and_force_residuals_retained_at_saved_points": True,
    }


def coupon(disk_helper: Any, tile_helper: Any, bore_helper: Any) -> dict[str, Any]:
    annulus = disk_helper.disk_strip(-5.0, 0.0, 0.0, 0.0, 5.0) - disk_helper.disk_strip(
        -2.0, 0.0, 0.0, 0.0, 2.0
    )
    require(abs(float(annulus[0]) - 10.5 * math.pi) < 1e-12, "annulus half-area known answer differs")
    require(abs(float(annulus[1]) + 78.0) < 1e-12, "annulus half-first-moment known answer differs")
    require(abs(float(annulus[2])) < 1e-12, "annulus cross first moment should vanish")

    tile = tile_helper.supported_tile_integrals(
        [[0.0, 10.0], [-5.0, 5.0]],
        [{"axis_id": "coupon-hole", "station_mm": 4.0, "transverse_center_mm": 0.0, "radius_mm": 1.0}],
        cut=5.0,
    )
    require(
        np.max(abs(tile - np.array([50.0 - math.pi, 125.0 - 4.0 * math.pi, 0.0]))) < 1e-12,
        "trimmed tile known answer differs",
    )

    profile = bore_helper.pressure_profile(
        [0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [0.0, 0.0, 1.0], 2.0, 1.0, identity="v-cut-coupon"
    )
    roots = bore_helper.coordinate_roots(0.0, 2.0, 0.0)
    require(len(roots) == 1 and abs(roots[0]) < 1e-12, "bore v-cut root known answer differs")
    arc = bore_helper.pressure_arc_wrench(profile, [0.0, 0.0, 0.0], -math.pi / 2, 0.0)
    require(
        np.max(abs(arc[:3] - np.array([5.0, -10.0 / math.pi, 0.0]))) < 1e-12,
        "bore half-arc force known answer differs",
    )
    return {
        "known_answers_satisfied": True,
        "annulus_negative_half_area_mm2": float(annulus[0]),
        "annulus_negative_half_first_moment_mm3": float(annulus[1]),
        "trimmed_cell_cut_area_first_moments": np.asarray(tile).tolist(),
        "bore_negative_half_arc_force_n": arc[:3].tolist(),
        "scope": "Exact-helper algebra only; no engineering case or joint is evaluated.",
    }


def source_header_result(
    path: Path,
    expected_result_sha: str,
    receipt_path: Path | None,
    expected_receipt_sha: str | None,
    expected_source_pins: dict[Path, str],
    boundary: Any,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, str]]:
    require(re.fullmatch(r"[0-9a-f]{64}", expected_result_sha) is not None, "expected boundary result SHA must be 64 lowercase hex digits")
    observed_result_sha = sha(path)
    require(observed_result_sha == expected_result_sha, f"boundary result SHA differs: {observed_result_sha}")
    result = read(path)
    require(
        result.get("schema") == "six_header_cleat_boundary_fields/v1"
        and result.get("source_authority", {}).get("candidate")
        == "compact-floor-flush-wood-joints-development"
        and result.get("source_authority", {}).get("development_revision")
        == "upper-corner-screw-row-2026-10-02-v1"
        and result.get("source_authority", {}).get("selected_axis_count") == 104
        and result.get("source_authority", {}).get("proposal_adopted") is False
        and result.get("source_authority", {}).get("available_108_axis_proposal") is not None
        and result.get("source_authority", {}).get("case_ids") == list(boundary.CASES)
        and result.get("source_authority", {}).get("six_target_bodies") == list(boundary.BODIES),
        "boundary result authority/schema differs",
    )
    require(
        result.get("counts", {}).get("interfaces") == 36
        and result.get("counts", {}).get("source_actions") == 360
        and result.get("counts", {}).get("u_v_cut_states") == 72,
        "boundary result interface/action/cut coverage differs",
    )
    require(
        not any(result.get(flag, False) for flag in FLAGS),
        "boundary result carries forbidden acceptance or proposal flag",
    )
    require(
        result.get("new_resistance_established") is False
        and result.get("complete_joint_acceptance") is False
        and result.get("proposal_108_adopted") is False,
        "boundary result acceptance/adoption flags differ",
    )
    receipt = None
    source_pins = {path_key(path): digest for path, digest in expected_source_pins.items()}
    source_pins[path_key(path)] = observed_result_sha
    if receipt_path is not None:
        require(expected_receipt_sha is not None, "boundary receipt needs its expected SHA")
        require(re.fullmatch(r"[0-9a-f]{64}", expected_receipt_sha) is not None, "expected boundary receipt SHA must be 64 lowercase hex digits")
        observed_receipt_sha = sha(receipt_path)
        require(observed_receipt_sha == expected_receipt_sha, f"boundary receipt SHA differs: {observed_receipt_sha}")
        receipt = read(receipt_path)
        require(
            receipt.get("schema") == "six_header_cleat_boundary_fields_receipt/v1"
            and receipt.get("status") == result.get("status")
            and receipt.get("output_sha256", {}).get("result.json") == observed_result_sha
            and receipt.get("output_sha256", {}).get("producer.py.snapshot") == BOUNDARY_SOURCE_SHA256,
            "boundary receipt does not bind result",
        )
        require(
            not any(
                receipt.get(flag, False)
                for flag in (
                    "new_resistance_established",
                    "complete_joint_acceptance",
                    "formal_criterion_acceptance",
                    "fabrication_release",
                    "physical_release",
                    "proposal_108_adopted",
                )
            ),
            "boundary receipt carries a forbidden acceptance/adoption flag",
        )
        for source, digest in receipt.get("source_sha256", {}).items():
            local = expected_source_pins.get(ROOT / source)
            if local is not None:
                require(local == digest, f"boundary receipt source pin differs: {source}")
        source_pins[path_key(receipt_path)] = observed_receipt_sha
    return result, receipt, source_pins


def build(
    boundary_result_path: Path,
    expected_result_sha: str,
    boundary_receipt_path: Path | None,
    expected_receipt_sha: str | None,
    output: Path,
) -> dict[str, Any]:
    boundary = module(HERE / "header-boundary.py", "header_boundary_for_v_cuts")
    remaining = module(UPPER / "remaining-block-transverse.py", "remaining_for_header_v_cuts")
    pins = dict(boundary.PINS)
    require(
        sha(HERE / "header-boundary.py") == BOUNDARY_SOURCE_SHA256
        and sha(HERE / "header-boundary.md") == BOUNDARY_DOC_SHA256,
        "frozen header-boundary producer/document changed",
    )
    pins[HERE / "header-boundary.py"] = BOUNDARY_SOURCE_SHA256
    pins[HERE / "header-boundary.md"] = BOUNDARY_DOC_SHA256
    source = boundary.source_context(dict(pins))
    for body_record in source["body_records"].values():
        member_geometry = body_record["member_geometry"]
        pins[ROOT / member_geometry["current_finished_step"]] = member_geometry[
            "current_finished_step_sha256"
        ]

    for path, digest in remaining.PINS.items():
        require(path not in pins or pins[path] == digest, f"conflicting frozen source pin: {path}")
        pins[path] = digest
    packet_geometries: dict[str, dict[str, Any]] = {}
    for packet_path in remaining.PACKETS:
        packet = read(packet_path)
        for relative, digest in packet["source_sha256"].items():
            path = ROOT / relative
            require(path not in pins or pins[path] == digest, f"conflicting frozen source pin: {relative}")
            pins[path] = digest
        require(not (set(packet_geometries) & set(packet["geometry"])), "duplicate body in saved geometry packets")
        packet_geometries.update(packet["geometry"])
    authenticate(pins)

    result, _boundary_receipt, boundary_pins = source_header_result(
        boundary_result_path,
        expected_result_sha,
        boundary_receipt_path,
        expected_receipt_sha,
        pins,
        boundary,
    )
    physical_math, normal_math, long_math = [
        remaining.module(path)
        for path in (remaining.PHYSICAL, remaining.NORMAL, remaining.LONG)
    ]
    disk_helper = module(UPPER / "top-host-physical-actions.py", "top_host_integrals_for_header_v_cuts")
    bore_helper = module(UPPER / "corner-bore-wall.py", "corner_bore_for_header_v_cuts")
    require(
        sha(UPPER / "top-host-physical-actions.py") == boundary.PINS[boundary.TOP_HOST]
        and sha(UPPER / "corner-bore-wall.py") == boundary.PINS[boundary.BORE_MAP],
        "reused integration helper differs from header boundary pins",
    )

    member_geometry = read(remaining.MEMBERS / "geometry.json")
    member_results = read(remaining.MEMBERS / "member-results.json")
    adapter, masses, current, contacts = [
        read(path) for path in (remaining.ADAPTER, remaining.MASS, remaining.CURRENT, remaining.CONTACTS)
    ]
    factor = float(source["remaining"]["source_gravity_multiplier"])
    require(
        abs(factor - float(member_results["same_state_dead_load_factor"])) < 1e-12,
        "saved gravity factor differs from member archive",
    )

    inputs = source["inputs"]
    require([case["case_id"] for case in inputs["cases"]] == list(boundary.CASES), "six-case source order differs")
    body_geometries = {
        body: packet_geometries[body]
        for body in boundary.BODIES
        if body in packet_geometries
    }
    require(set(body_geometries) == set(boundary.BODIES), "saved net-section packets do not cover six cleats")
    expected_cuts = boundary.cut_catalog(boundary.ALL_JOINT_DIR / "receiver-cuts.jsonl", source["all_joint"])
    remaining_states = {
        (state["block"], state["case_id"], int(state["axis"])): state
        for state in source["remaining"]["states"]
        if state["block"] in boundary.BODIES and int(state["axis"]) == 2
    }

    by_body_case = {(row["body"], row["case_id"]): row for row in result["bodies"]}
    require(len(by_body_case) == len(boundary.BODIES) * len(boundary.CASES), "boundary body/case record census differs")
    output = Path(output).resolve()
    require(output.is_relative_to(RAW) and output != RAW and not output.exists(), "fresh owned output child required")
    output.mkdir(parents=True, exist_ok=False)
    (output / ".gitignore").write_text("*\n")
    (output / "producer.py.snapshot").write_bytes(Path(__file__).read_bytes())
    own_script_sha = sha(Path(__file__))
    pins[Path(__file__).resolve()] = own_script_sha
    authenticate(pins)

    body_prepared: dict[str, dict[str, Any]] = {}
    body_stops = []
    for body in boundary.BODIES:
        try:
            own = remaining.prepare_body(
                body,
                body_geometries[body],
                member_geometry["members"][body],
                adapter,
                masses,
                current,
                contacts,
                physical_math,
                long_math,
                factor,
            )
            body_prepared[body] = own
        except (remaining.UnsupportedBody, ValueError, AssertionError, KeyError) as exc:
            body_stops.append({"body": body, "status": "AFFECTED_BODY_SCOPE_STOPPED", "reason": f"{type(exc).__name__}: {exc}"})

    case_summaries = []
    body_case_balance = []
    all_cut_count = 0
    unsupported_fields = []
    t_peaks = {"original": None, "mapped": None}
    with gzip.open(output / "v-cuts.jsonl.gz", "wt") as stream:
        for body in boundary.BODIES:
            if body not in body_prepared:
                continue
            own = body_prepared[body]
            for case_id in boundary.CASES:
                record = by_body_case[(body, case_id)]
                require(
                    record["header_interface"]["source_action_count"] == 10,
                    f"header action count differs: {body}/{case_id}",
                )
                require(
                    np.max(abs(vec(record["source_body_datum_xyz_mm"]) - own["start"])) < POINT_TOL_MM,
                    f"body datum differs from retained-mass helper: {body}/{case_id}",
                )
                interface_datum = vec(record["source_interface_datum_xyz_mm"])
                recoveries = [
                    action_recovery(
                        item,
                        own,
                        interface_datum,
                        disk_helper,
                        disk_helper,
                        bore_helper,
                    )
                    for item in record["header_interface"]["actions"]
                ]
                unsupported_fields.extend(
                    {
                        "body": body,
                        "case_id": case_id,
                        "source_row": recovery["source"]["row"],
                        "source_id": recovery["source"]["source_id"],
                        "status": recovery["field_recovery_status"],
                        "reason": recovery["unsupported_field_reason"],
                        "unmapped_source_force_xyz_n": recovery["unmapped_source_force_xyz_n"],
                        "unmapped_source_free_moment_nmm": recovery["unmapped_source_free_moment_nmm"],
                    }
                    for recovery in recoveries
                    if recovery["unsupported_field_reason"] is not None
                )
                retained = [
                    {
                        "point_mm": item["point_xyz_mm"],
                        "force_n": item["force_xyz_n"],
                        "free_moment_nmm": item["free_moment_nmm"],
                        "source_row": item["source_row"],
                        "source_id": item["source_id"],
                        "role": item["role"],
                    }
                    for item in record["whole_body_accounting"]["retained_nonheader_source_point_actions"]
                ]
                gravity_points = [item for item in retained if item["role"] == "discrete_body_load"]
                gravity_prepared = physical_math.prepare_points(
                    [
                        {
                            "point_xyz_mm": item["point_mm"],
                            "force_xyz_n": item["force_n"],
                            "free_couple_xyz_nmm": item["free_moment_nmm"],
                        }
                        for item in gravity_points
                    ],
                    own["frame"],
                    own["start"],
                )
                own["source_gravity_prepared"] = gravity_prepared

                original_interface = sum(
                    (local_point_wrench(recovery["source"], own) for recovery in recoveries),
                    np.zeros(6),
                )
                original_interface_global = sum(
                    (wrench_global([recovery["source"]], interface_datum) for recovery in recoveries),
                    np.zeros(6),
                )
                saved_interface = vec(
                    record["header_interface"]["source_wrench_xyz_n_nmm"], (6,)
                )
                require(
                    max(abs(original_interface_global[:3] - saved_interface[:3])) < FORCE_TOL_N
                    and max(abs(original_interface_global[3:] - saved_interface[3:])) < MOMENT_TOL_NMM,
                    f"header interface full source wrench differs: {body}/{case_id}",
                )
                mapped_interface = sum(
                    (np.asarray(recovery["mixed_full_wrench_local_about_body_start_n_nmm"]) for recovery in recoveries),
                    np.zeros(6),
                )
                source_body = local_wrench(
                    vec(record["whole_body_accounting"]["source_wrench_xyz_n_nmm"], (6,)),
                    own["frame"],
                )
                original_body = original_interface + sum(
                    (local_point_wrench(action, own) for action in retained), np.zeros(6)
                )
                physical_full_gravity = np.asarray(own["full_gravity"], dtype=float)
                source_gravity_full = sum(
                    (local_point_wrench(action, own) for action in gravity_points), np.zeros(6)
                )
                gravity_error = source_gravity_full - physical_full_gravity
                require(
                    max(abs(gravity_error[:3])) < GRAVITY_TOL
                    and max(abs(gravity_error[3:])) < GRAVITY_TOL,
                    f"physical gravity full-wrench replacement differs: {body}/{case_id}",
                )
                mapped_body = mapped_interface + sum(
                    (local_point_wrench(action, own) for action in retained if action["role"] != "discrete_body_load"),
                    np.zeros(6),
                ) + physical_full_gravity
                old_body_error = original_body - source_body
                mapped_body_error = mapped_body - source_body
                require(
                    max(abs(old_body_error[:3])) < FORCE_TOL_N
                    and max(abs(old_body_error[3:])) < MOMENT_TOL_NMM,
                    f"source whole-body points fail six-wrench balance: {body}/{case_id}",
                )
                require(
                    max(abs(mapped_body_error[:3])) < FORCE_TOL_N
                    and max(abs(mapped_body_error[3:])) < MOMENT_TOL_NMM,
                    f"mapped whole-body field/residual/gravity balance fails: {body}/{case_id}",
                )

                states = record["u_v_cut_catalog"]["v"]["source_states"]
                identity = (body, case_id, 2)
                require(
                    states == expected_cuts[identity],
                    f"boundary v-cut catalog differs from pinned source cuts: {body}/{case_id}",
                )
                state = remaining_states[identity]
                require(len(states) * 2 == int(state["cut_count"]), f"v-cut count differs from remaining archive: {body}/{case_id}")
                max_old = None
                max_new = None
                old_t_positive = new_t_positive = old_pressure_count = new_pressure_count = 0
                for cut in states:
                    station = float(cut["station_mm"])
                    for limit in cut["limits"]:
                        row = cut_row(
                            body,
                            case_id,
                            station,
                            limit,
                            own,
                            recoveries,
                            retained,
                            gravity_points,
                            physical_math,
                            normal_math,
                            remaining,
                            disk_helper,
                            disk_helper,
                            bore_helper,
                        )
                        stream.write(json.dumps(row, allow_nan=False, separators=(",", ":")) + "\n")
                        all_cut_count += 1
                        old_t = row["original_normal_hull_minimum_tensile_resultant_n"]
                        new_t = row["mapped_normal_hull_minimum_tensile_resultant_n"]
                        old_t_positive += old_t > 0.0
                        new_t_positive += new_t > 0.0
                        old_pressure_count += "pressure_peak_mpa" in row["original_existing_finite_pressure_witness"]
                        new_pressure_count += "pressure_peak_mpa" in row["mapped_existing_finite_pressure_witness"]
                        for tag, value, witness in (
                            ("original", old_t, row),
                            ("mapped", new_t, row),
                        ):
                            if t_peaks[tag] is None or value > t_peaks[tag]["value"]:
                                t_peaks[tag] = {"value": value, "body": body, "case_id": case_id, "station_mm": station, "limit": limit}
                        if max_old is None or old_t > max_old:
                            max_old = old_t
                        if max_new is None or new_t > max_new:
                            max_new = new_t
                body_case_balance.append(
                    {
                        "body": body,
                        "case_id": case_id,
                        "source_body_wrench_local_n_nmm": source_body.tolist(),
                        "original_source_point_balance_residual_local_n_nmm": old_body_error.tolist(),
                        "mapped_field_residual_and_physical_gravity_balance_residual_local_n_nmm": mapped_body_error.tolist(),
                        "physical_minus_saved_discrete_gravity_local_n_nmm": gravity_error.tolist(),
                        "integrated_header_actions": len(recoveries),
                        "retained_nonheader_points": len(retained),
                        "physical_gravity_replaces_discrete_body_load_rows": len(gravity_points),
                        "v_cut_station_count": len(states),
                    }
                )
                case_summaries.append(
                    {
                        "body": body,
                        "case_id": case_id,
                        "cut_limit_count": len(states) * 2,
                        "original_positive_normal_hull_tension_count": old_t_positive,
                        "mapped_positive_normal_hull_tension_count": new_t_positive,
                        "original_finite_pressure_witness_count": old_pressure_count,
                        "mapped_finite_pressure_witness_count": new_pressure_count,
                        "maximum_original_normal_hull_tension_n": max_old,
                        "maximum_mapped_normal_hull_tension_n": max_new,
                        "maximum_tension_change_n": max_new - max_old,
                        "header_action_recovery": [
                            {
                                "source_row": item["source"]["row"],
                                "source_id": item["source"]["source_id"],
                                "field_recovery_status": item["field_recovery_status"],
                                "unsupported_field_reason": item["unsupported_field_reason"],
                                "residual_force_xyz_n": item["residual_point"]["force_n"],
                                "residual_free_moment_nmm": item["residual_point"]["free_moment_nmm"],
                                "saved_unmapped_source_force_xyz_n": item["unmapped_source_force_xyz_n"],
                                "saved_unmapped_source_free_moment_nmm": item["unmapped_source_free_moment_nmm"],
                                "source_to_field_residual_difference_xyz_n_nmm": item["saved_source_to_field_residual_difference_xyz_n_nmm"],
                            }
                            for item in recoveries
                        ],
                    }
                )

    require(sha(Path(__file__)) == own_script_sha, "consumer source changed during run")
    authenticate(pins)
    require(
        all_cut_count == sum(summary["cut_limit_count"] for summary in case_summaries),
        "v-cut result count differs from body/case catalogs",
    )
    result_output = {
        "schema": "six_header_cleat_v_cut_comparison/v1",
        "status": "PREPARED_V_CUT_COMPARISON_WITH_EXPLICIT_SOURCE_RESIDUALS"
        if not body_stops and not unsupported_fields
        else "V_CUT_COMPARISON_WITH_EXPLICIT_SCOPE_STOPS_OR_UNSUPPORTED_FIELDS",
        "source_authority": {
            "candidate": "compact-floor-flush-wood-joints-development",
            "development_revision": "upper-corner-screw-row-2026-10-02-v1",
            "reviewed_axis_count": 104,
            "header_axis_count": 12,
            "case_ids": list(boundary.CASES),
            "target_bodies": list(boundary.BODIES),
            "available_108_axis_proposal_present": True,
            "available_108_axis_proposal_adopted": False,
        },
        "boundary_result": {
            "path": path_key(boundary_result_path),
            "sha256": expected_result_sha,
            "receipt_path": None if boundary_receipt_path is None else path_key(boundary_receipt_path),
            "receipt_sha256": expected_receipt_sha,
        },
        "counts": {
            "body_case_pairs_evaluated": len(case_summaries),
            "v_cut_limits_evaluated": all_cut_count,
            "unsupported_fields_retained_as_exact_source_points": len(unsupported_fields),
            "body_scope_stops": len(body_stops),
        },
        "whole_body_field_balance": body_case_balance,
        "body_case_summaries": case_summaries,
        "maximum_normal_hull_tension_witnesses": t_peaks,
        "unsupported_fields": unsupported_fields,
        "body_scope_stops": body_stops,
        "method": {
            "washer": "Exact disk-strip integrals over saved uniform annuli, subtracting inner disk.",
            "contact": "Existing supported trimmed-tile integrals on saved patch-cell coordinates and bore circles.",
            "lateral_bore": "Existing angular roots and analytic pressure-arc wrench over each saved half-cosine profile.",
            "residuals": "Saved source row force/free couple minus integrated full field, retained at exact source point; unsupported field stays as full original source point.",
            "gravity": "Existing retained-timber volume/first-moment field plus original allocated hardware points replaces discrete body-load points once.",
            "diagnostics": "Full signed six-component v-cut wrench; existing normal-hull lower-bound diagnostic and finite compression witness only.",
        },
        "limits": [
            "Numerical source and whole-body wrench balance is accounting, not pressure compatibility or timber stress.",
            "Every unsupported frictionless force/free couple stays explicit at its original source point; roundoff couples remain in the inventory.",
            "The normal-hull tensile resultant is a necessary lower bound, not splitting capacity or a bolt allocation.",
            "Finite pressure results reuse the existing sufficient compression-only construction; no new material value or acceptance check is added.",
            "The v-cut inventory samples only saved source stations and both saved limits; no continuous maximum is claimed.",
        ],
        "v_cuts_path": "v-cuts.jsonl.gz",
        **FLAGS,
    }
    write(output / "result.json", result_output)
    source_hashes = {key: value for key, value in sorted(boundary_pins.items())}
    for path, digest in sorted(pins.items()):
        source_hashes[path_key(path)] = digest
    artifacts = {path.name: sha(path) for path in output.iterdir() if path.is_file()}
    write(
        output / "receipt.json",
        {
            "schema": "six_header_cleat_v_cut_comparison_receipt/v1",
            "status": result_output["status"],
            "source_sha256": source_hashes,
            "output_sha256": artifacts,
            "runtime": {"python": sys.version.split()[0], "numpy": np.__version__},
            **FLAGS,
        },
    )
    return {
        "status": result_output["status"],
        "body_case_pairs_evaluated": len(case_summaries),
        "v_cut_limits_evaluated": all_cut_count,
        "result_sha256": sha(output / "result.json"),
        "receipt_sha256": sha(output / "receipt.json"),
        "unsupported_fields": unsupported_fields,
        "body_scope_stops": body_stops,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coupon-only", action="store_true")
    parser.add_argument("--boundary-result", type=Path)
    parser.add_argument("--expected-boundary-result-sha256")
    parser.add_argument("--boundary-receipt", type=Path)
    parser.add_argument("--expected-boundary-receipt-sha256")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.coupon_only:
        boundary = module(HERE / "header-boundary.py", "header_boundary_for_v_cut_coupon")
        require(
            sha(HERE / "header-boundary.py") == BOUNDARY_SOURCE_SHA256
            and sha(HERE / "header-boundary.md") == BOUNDARY_DOC_SHA256
            and sha(UPPER / "top-host-physical-actions.py") == boundary.PINS[boundary.TOP_HOST]
            and sha(UPPER / "corner-bore-wall.py") == boundary.PINS[boundary.BORE_MAP],
            "frozen boundary pair or reused integral helper changed",
        )
        disk_helper = module(UPPER / "top-host-physical-actions.py", "header_v_cut_coupon_tiles")
        bore_helper = module(UPPER / "corner-bore-wall.py", "header_v_cut_coupon_bore")
        print(json.dumps(coupon(disk_helper, disk_helper, bore_helper), sort_keys=True))
        return
    require(args.boundary_result is not None, "--boundary-result is required")
    require(args.expected_boundary_result_sha256 is not None, "--expected-boundary-result-sha256 is required")
    require(args.output is not None, "--output is required")
    require(
        (args.boundary_receipt is None) == (args.expected_boundary_receipt_sha256 is None),
        "provide both --boundary-receipt and --expected-boundary-receipt-sha256, or neither",
    )
    print(
        json.dumps(
            build(
                args.boundary_result,
                args.expected_boundary_result_sha256,
                args.boundary_receipt,
                args.expected_boundary_receipt_sha256,
                args.output,
            ),
            allow_nan=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
