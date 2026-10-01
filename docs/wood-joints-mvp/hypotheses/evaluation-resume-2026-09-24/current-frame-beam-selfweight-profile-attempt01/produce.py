#!/usr/bin/env python3
"""Build a finite-bin, wrench-preserving self-weight profile from pinned STEP solids.

This is a geometry/mass accounting artifact. It performs no meshing, solver
work, structural support modeling, or section-force recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "beam-selfweight-profile.json"

GEOMETRY_PATH = (
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "reduced-static-attempt01/member-geometry.json"
)
MATERIAL_MAP_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-frame-timber-material-frame-map-attempt01/"
    "current-frame-timber-material-frame-map.json"
)
MASS_CENTROIDS_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-mass-centroids-attempt01/mass-centroids.json"
)
MANIFEST_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-input-manifest-attempt04/"
    "current-full-frame-input-manifest.json"
)
SOLID_BUNDLE_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-full-frame-member-solids-attempt01/bundle/"
    "current-full-frame-member-solids.json"
)
BOARD_WEIGHT_PATH = "docs/wood-joints-mvp/board-weight-2026-09-24.json"
LOAD_CASES_PATH = (
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
    "current-load-cases.json"
)
PYPROJECT_PATH = "pyproject.toml"
UV_LOCK_PATH = "uv.lock"

EXPECTED_INPUT_SHA256 = {
    GEOMETRY_PATH: "121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187",
    MATERIAL_MAP_PATH: "f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409",
    MASS_CENTROIDS_PATH: "4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a",
    MANIFEST_PATH: "9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11",
    SOLID_BUNDLE_PATH: "8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420",
    BOARD_WEIGHT_PATH: "7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e",
    LOAD_CASES_PATH: "9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a",
    PYPROJECT_PATH: "84e007ad5c9cfffa853f21627fecbaec0a85c602560d5d5e0b507326e9b02452",
    UV_LOCK_PATH: "5ea7a77ddb3072bfe1c2ba131e34b293a0103f931eb9b911e9eb248ccb6d84d3",
}

EXPECTED_REVISION = "led-clearance-2x6-runner-seated-blocks-v1"
EXPECTED_CANDIDATE = "compact-floor-flush-wood-joints-development"
EXPECTED_MANIFEST_ID = "current-full-frame-input-manifest-attempt04"
EXPECTED_MANIFEST_DIGEST = "8db026d0764ee3f4f9f83656133e18ea11ebe250acd0c431567e85fa4d4d23bc"
EXPECTED_SOLID_ARTIFACT_DIGEST = "d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc"
EXPECTED_GEOMETRY_CONTENT_DIGEST = "1bb5fc145327e2ea2a51ead0f813c6fbc06d053f755112b49215ee1326106ec6"
EXPECTED_MATERIAL_GEOMETRY_DIGEST = "d9d8feefea4df6ad2895a25292e164851c4d776ae6606c12956b639fb161e3fc"
EXPECTED_MATERIAL_MAP_RECORD_DIGEST = "69a99e91583a4a2e9064edf24335a921cc48395ba3699fd96bec1a2272a30bb5"

GEOMETRY_TOLERANCE_MM = 1e-6
SOURCE_VOLUME_TOLERANCE_MM3 = 1e-3
SOURCE_CENTROID_TOLERANCE_MM = 1e-5
PROFILE_VOLUME_REL_TOLERANCE = 1e-8
PROFILE_CENTROID_TOLERANCE_MM = 1e-5
FORCE_CLOSURE_TOLERANCE_N = 1e-8
MOMENT_CLOSURE_TOLERANCE_NMM = 1e-4
KNOWN_VOLUME_TOLERANCE_MM3 = 1e-5
KNOWN_CENTROID_TOLERANCE_MM = 1e-7
BIN_LENGTH_MM = 50.0
END_CAP_CLIP_SLACK_MM = 0.01
GRAVITY_M_S2 = 9.80665
MODELED_WOOD_DENSITY_KG_M3 = 600.0
KNOWN_FIXTURE_DENSITY_KG_M3 = 600.0


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Pinned source is missing: {relative_path}")
    return sha256_bytes(path.read_bytes())


def read_json(relative_path: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative_path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative_path}: expected a JSON object")
    return value


def dot(a: list[float], b: list[float]) -> float:
    return math.fsum(float(x) * float(y) for x, y in zip(a, b, strict=True))


def cross(a: list[float], b: list[float]) -> list[float]:
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def unit(a: list[float], name: str) -> list[float]:
    length = math.sqrt(dot(a, a))
    if not math.isfinite(length) or length <= 0.0:
        raise ValueError(f"{name}: expected a finite nonzero vector")
    return [float(x) / length for x in a]


def add_scaled(origin: list[float], direction: list[float], distance: float) -> list[float]:
    return [float(origin[i]) + float(direction[i]) * distance for i in range(3)]


def subtract(a: list[float], b: list[float]) -> list[float]:
    return [float(a[i]) - float(b[i]) for i in range(3)]


def max_abs(a: list[float], b: list[float]) -> float:
    return max(abs(float(x) - float(y)) for x, y in zip(a, b, strict=True))


def magnitude(a: list[float]) -> float:
    return math.sqrt(dot(a, a))


def verify_pinned_inputs() -> dict[str, str]:
    actual = {path: file_sha256(path) for path in EXPECTED_INPUT_SHA256}
    mismatches = {
        path: {"expected": EXPECTED_INPUT_SHA256[path], "actual": actual[path]}
        for path in EXPECTED_INPUT_SHA256
        if actual[path] != EXPECTED_INPUT_SHA256[path]
    }
    if mismatches:
        raise ValueError(f"Pinned source hashes changed: {mismatches}")
    return actual


def finite_bins(length_mm: float, target_bin_mm: float) -> list[tuple[float, float]]:
    if length_mm <= 0.0 or target_bin_mm <= 0.0:
        raise ValueError("Member length and bin width must be positive")
    result: list[tuple[float, float]] = []
    start = 0.0
    while start < length_mm - 1e-12:
        end = min(start + target_bin_mm, length_mm)
        result.append((start, end))
        start = end
    if not result or abs(result[0][0]) > 1e-12 or abs(result[-1][1] - length_mm) > 1e-9:
        raise AssertionError("Longitudinal bins do not partition the descriptor span")
    return result


def slice_shape(
    shape: Any,
    start_xyz: list[float],
    axis_xyz: list[float],
    section_u_xyz: list[float],
    length_mm: float,
    bin_length_mm: float,
    transverse_half_width_mm: float,
    end_slack_mm: float = END_CAP_CLIP_SLACK_MM,
) -> list[dict[str, Any]]:
    """Intersect an exact BRep with oriented longitudinal slabs and report mass properties."""
    import cadquery as cq

    bins: list[dict[str, Any]] = []
    intervals = finite_bins(length_mm, bin_length_mm)
    for index, (station_start, station_end) in enumerate(intervals):
        clip_start = station_start - (end_slack_mm if index == 0 else 0.0)
        clip_end = station_end + (end_slack_mm if index == len(intervals) - 1 else 0.0)
        clip_length = clip_end - clip_start
        clip_mid = (clip_start + clip_end) * 0.5
        plane_origin = add_scaled(start_xyz, axis_xyz, clip_mid)
        plane = cq.Plane(
            origin=tuple(plane_origin),
            xDir=tuple(section_u_xyz),
            normal=tuple(axis_xyz),
        )
        cutter = (
            cq.Workplane(plane)
            .box(
                2.0 * transverse_half_width_mm,
                2.0 * transverse_half_width_mm,
                clip_length,
                centered=(True, True, True),
            )
            .val()
        )
        part = shape.intersect(cutter)
        if not part.isValid():
            raise ValueError(f"Invalid BRep intersection in bin {index}")
        volume = float(part.Volume())
        if not math.isfinite(volume) or volume < -1e-9:
            raise ValueError(f"Invalid bin volume in bin {index}: {volume}")
        if volume <= 1e-12:
            centroid = None
            volume = 0.0
        else:
            centroid = [float(value) for value in part.Center().toTuple()]
        bins.append(
            {
                "bin_index": index,
                "descriptor_station_start_mm": station_start,
                "descriptor_station_end_mm": station_end,
                "descriptor_station_length_mm": station_end - station_start,
                "boolean_clip_start_mm": clip_start,
                "boolean_clip_end_mm": clip_end,
                "volume_mm3": volume,
                "centroid_global_xyz_mm": centroid,
                "intersection_solid_count": len(part.Solids()),
            }
        )
    return bins


def profile_wrench(
    bins: list[dict[str, Any]],
    density_kg_m3: float,
    gravity_m_s2: float,
    start_xyz: list[float],
    axis_xyz: list[float],
) -> tuple[list[dict[str, Any]], float, list[float], list[float]]:
    total_mass = 0.0
    total_force = [0.0, 0.0, 0.0]
    total_moment = [0.0, 0.0, 0.0]
    enriched: list[dict[str, Any]] = []
    for row in bins:
        volume = float(row["volume_mm3"])
        mass = volume * density_kg_m3 / 1e9
        weight = mass * gravity_m_s2
        force = [0.0, 0.0, -weight]
        centroid = row["centroid_global_xyz_mm"]
        if centroid is None:
            moment = [0.0, 0.0, 0.0]
            station_mid = (
                float(row["descriptor_station_start_mm"])
                + float(row["descriptor_station_end_mm"])
            ) * 0.5
            axis_point = add_scaled(start_xyz, axis_xyz, station_mid)
            offset = [0.0, 0.0, 0.0]
            equivalent_couple = [0.0, 0.0, 0.0]
        else:
            moment = cross(centroid, force)
            station_mid = (
                float(row["descriptor_station_start_mm"])
                + float(row["descriptor_station_end_mm"])
            ) * 0.5
            axis_point = add_scaled(start_xyz, axis_xyz, station_mid)
            offset = subtract(centroid, axis_point)
            equivalent_couple = cross(offset, force)
        length_m = float(row["descriptor_station_length_mm"]) / 1000.0
        enriched.append(
            {
                **row,
                "conditional_density_kg_m3": density_kg_m3,
                "mass_kg": mass,
                "weight_n": weight,
                "mean_uniform_equivalent_line_load_n_per_m": weight / length_m,
                "descriptor_axis_point_global_xyz_mm": axis_point,
                "centroid_offset_from_descriptor_axis_mm": offset,
                "gravity_force_global_xyz_n": force,
                "gravity_moment_about_global_origin_nmm": moment,
                "equivalent_axis_couple_about_bin_station_nmm": equivalent_couple,
            }
        )
        total_mass += mass
        for component in range(3):
            total_force[component] += force[component]
            total_moment[component] += moment[component]
    return enriched, total_mass, total_force, total_moment


def run_known_answer_fixture(cadquery_version: str) -> dict[str, Any]:
    import cadquery as cq

    axis = unit([2.0, -1.0, 2.0], "known-answer axis")
    section_u = unit([1.0, 2.0, 0.0], "known-answer section_u")
    section_v = unit(cross(axis, section_u), "known-answer section_v")
    if abs(dot(axis, section_u)) > 1e-12 or dot(cross(axis, section_u), section_v) < 1.0 - 1e-12:
        raise AssertionError("Known-answer frame is not right-handed orthonormal")

    width_u_mm = 40.0
    width_v_mm = 80.0
    length_mm = 137.0
    start = [321.0, -456.0, 789.0]
    middle = add_scaled(start, axis, length_mm * 0.5)
    fixture_plane = cq.Plane(
        origin=tuple(middle), xDir=tuple(section_u), normal=tuple(axis)
    )
    fixture = (
        cq.Workplane(fixture_plane)
        .box(width_u_mm, width_v_mm, length_mm, centered=(True, True, True))
        .val()
    )
    bbox = fixture.BoundingBox()
    diagonal = math.sqrt(bbox.xlen**2 + bbox.ylen**2 + bbox.zlen**2)
    bins = slice_shape(
        fixture,
        start,
        axis,
        section_u,
        length_mm,
        BIN_LENGTH_MM,
        diagonal + 1.0,
    )

    max_volume_error = 0.0
    max_centroid_error = 0.0
    max_first_moment_error = 0.0
    expected_total_volume = width_u_mm * width_v_mm * length_mm
    expected_first_moment = [0.0, 0.0, 0.0]
    actual_first_moment = [0.0, 0.0, 0.0]
    for row in bins:
        low = float(row["descriptor_station_start_mm"])
        high = float(row["descriptor_station_end_mm"])
        expected_length = high - low
        expected_volume = width_u_mm * width_v_mm * expected_length
        expected_center = add_scaled(start, axis, (low + high) * 0.5)
        actual_center = row["centroid_global_xyz_mm"]
        if actual_center is None:
            raise AssertionError("Known-answer box produced an empty bin")
        max_volume_error = max(max_volume_error, abs(float(row["volume_mm3"]) - expected_volume))
        max_centroid_error = max(max_centroid_error, max_abs(actual_center, expected_center))
        for component in range(3):
            expected_first_moment[component] += expected_volume * expected_center[component]
            actual_first_moment[component] += float(row["volume_mm3"]) * actual_center[component]
    max_first_moment_error = max_abs(actual_first_moment, expected_first_moment)
    volume_sum = math.fsum(float(row["volume_mm3"]) for row in bins)
    if abs(volume_sum - expected_total_volume) > KNOWN_VOLUME_TOLERANCE_MM3:
        raise AssertionError(f"Known-answer volume closure failed: {volume_sum} != {expected_total_volume}")
    if max_volume_error > KNOWN_VOLUME_TOLERANCE_MM3:
        raise AssertionError(f"Known-answer bin volume error too large: {max_volume_error}")
    if max_centroid_error > KNOWN_CENTROID_TOLERANCE_MM:
        raise AssertionError(f"Known-answer centroid error too large: {max_centroid_error}")
    if max_first_moment_error > 1e-5:
        raise AssertionError(f"Known-answer first moment error too large: {max_first_moment_error}")

    fixture_density = KNOWN_FIXTURE_DENSITY_KG_M3
    fixture_mass = expected_total_volume * fixture_density / 1e9
    fixture_weight = fixture_mass * GRAVITY_M_S2
    expected_total_centroid = [float(value) for value in fixture.Center().toTuple()]
    expected_force = [0.0, 0.0, -fixture_weight]
    expected_moment = cross(expected_total_centroid, expected_force)
    actual_mass = volume_sum * fixture_density / 1e9
    actual_force = [0.0, 0.0, -actual_mass * GRAVITY_M_S2]
    actual_center = [value / volume_sum for value in actual_first_moment]
    actual_moment = cross(actual_center, actual_force)
    force_error = max_abs(actual_force, expected_force)
    moment_error = max_abs(actual_moment, expected_moment)
    if force_error > FORCE_CLOSURE_TOLERANCE_N or moment_error > MOMENT_CLOSURE_TOLERANCE_NMM:
        raise AssertionError("Known-answer gravity force or first-moment closure failed")

    return {
        "status": "PASS",
        "cadquery_version": cadquery_version,
        "geometry": "rotated prismatic box; exact BRep generated in a non-cardinal right-handed frame",
        "axis_global_xyz": axis,
        "section_u_global_xyz": section_u,
        "section_v_global_xyz": section_v,
        "width_u_mm": width_u_mm,
        "width_v_mm": width_v_mm,
        "length_mm": length_mm,
        "target_bin_length_mm": BIN_LENGTH_MM,
        "bin_count": len(bins),
        "expected_total_volume_mm3": expected_total_volume,
        "actual_total_volume_mm3": volume_sum,
        "max_bin_volume_error_mm3": max_volume_error,
        "max_bin_centroid_error_mm": max_centroid_error,
        "max_total_first_moment_error_mm4": max_first_moment_error,
        "conditional_density_kg_m3": fixture_density,
        "expected_gravity_force_global_xyz_n": expected_force,
        "actual_gravity_force_global_xyz_n": actual_force,
        "max_gravity_force_error_n": force_error,
        "expected_gravity_moment_about_origin_nmm": expected_moment,
        "actual_gravity_moment_about_origin_nmm": actual_moment,
        "max_gravity_moment_error_nmm": moment_error,
    }


def build_record() -> dict[str, Any]:
    import cadquery as cq
    from cadquery import importers

    if cq.__version__ != "2.8.0":
        raise ValueError(f"Expected CadQuery 2.8.0, found {cq.__version__}")
    pins = verify_pinned_inputs()
    geometry = read_json(GEOMETRY_PATH)
    material_map = read_json(MATERIAL_MAP_PATH)
    mass_export = read_json(MASS_CENTROIDS_PATH)
    manifest = read_json(MANIFEST_PATH)
    bundle = read_json(SOLID_BUNDLE_PATH)
    board_weight = read_json(BOARD_WEIGHT_PATH)
    load_cases = read_json(LOAD_CASES_PATH)

    canonical_geometry = dict(geometry)
    claimed_geometry_digest = canonical_geometry.pop("content_sha256", None)
    actual_geometry_digest = sha256_bytes(canonical_json(canonical_geometry))
    if claimed_geometry_digest != EXPECTED_GEOMETRY_CONTENT_DIGEST or actual_geometry_digest != claimed_geometry_digest:
        raise ValueError("member-geometry.json canonical content digest mismatch")
    if (
        geometry.get("candidate") != EXPECTED_CANDIDATE
        or geometry.get("geometry_revision_id") != EXPECTED_REVISION
        or geometry.get("candidate_accepted") is not False
    ):
        raise ValueError("member geometry candidate/revision/acceptance identity changed")
    if (
        material_map.get("geometry_revision_id") != EXPECTED_REVISION
        or material_map.get("current_geometry_artifact_sha256") != EXPECTED_MATERIAL_GEOMETRY_DIGEST
        or material_map.get("record_sha256") != EXPECTED_MATERIAL_MAP_RECORD_DIGEST
    ):
        raise ValueError("Conditional material-frame map identity/digest changed")
    if (
        manifest.get("manifest_id") != EXPECTED_MANIFEST_ID
        or manifest.get("manifest_sha256") != EXPECTED_MANIFEST_DIGEST
        or manifest.get("geometry_revision_id") != EXPECTED_REVISION
        or manifest.get("candidate") != EXPECTED_CANDIDATE
    ):
        raise ValueError("Attempt04 manifest identity/digest changed")
    if (
        bundle.get("artifact_sha256") != EXPECTED_SOLID_ARTIFACT_DIGEST
        or bundle.get("geometry_revision_id") != EXPECTED_REVISION
        or bundle.get("candidate") != EXPECTED_CANDIDATE
    ):
        raise ValueError("Exact STEP bundle identity/digest changed")
    if mass_export.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Mass-centroid source revision changed")
    if board_weight.get("revision_id") != EXPECTED_REVISION:
        raise ValueError("Density scenario revision changed")
    if mass_export.get("source_sha256", {}).get(BOARD_WEIGHT_PATH) != pins[BOARD_WEIGHT_PATH]:
        raise ValueError("Mass-centroid export no longer pins the selected density source")
    if load_cases.get("gravity_m_s2") not in (None, GRAVITY_M_S2):
        raise ValueError("Current load contract gravity value changed")

    material_rows = material_map.get("members")
    descriptors = geometry.get("members")
    mass_rows = mass_export.get("rows")
    weight_rows = board_weight.get("rows")
    if not all(isinstance(rows, list) for rows in (material_rows, descriptors, mass_rows, weight_rows)):
        raise TypeError("Pinned source member rows are missing")
    if len(material_rows) != 20:
        raise ValueError(f"Expected 20 frame timber grain rows, found {len(material_rows)}")
    descriptor_by_id = {row.get("member_id"): row for row in descriptors}
    source_mass_by_name = {row.get("name"): row for row in mass_rows}
    scenario_by_name = {row.get("name"): row for row in weight_rows}
    if len(descriptor_by_id) != len(descriptors) or len(source_mass_by_name) != len(mass_rows):
        raise ValueError("Duplicate source member identifiers")

    expected_ids = sorted(str(row["member_id"]) for row in material_rows)
    if len(set(expected_ids)) != 20:
        raise ValueError("Conditional grain map does not contain 20 unique frame timber IDs")
    if any(member_id not in descriptor_by_id for member_id in expected_ids):
        raise ValueError("One or more grain-mapped frame timbers lack a member geometry descriptor")
    if any(member_id not in source_mass_by_name or member_id not in scenario_by_name for member_id in expected_ids):
        raise ValueError("One or more frame timber IDs lack a pinned mass/density inventory row")

    frame_rows: list[dict[str, Any]] = []
    for material_row in sorted(material_rows, key=lambda row: row["member_id"]):
        member_id = str(material_row["member_id"])
        descriptor = descriptor_by_id[member_id]
        source_mass = source_mass_by_name[member_id]
        scenario_row = scenario_by_name[member_id]
        lineage = material_row.get("current_geometry_lineage", {})
        grain = material_row.get("conditional_grain_assignment", {})
        step_path = str(descriptor["step_path"])
        step_digest = str(descriptor["step_sha256"])
        if (
            lineage.get("step_file") != step_path
            or lineage.get("step_sha256") != step_digest
            or scenario_row.get("group") != "frame timber"
            or source_mass.get("group") != "frame timber"
        ):
            raise ValueError(f"{member_id}: geometry/mass/material IDs do not reconcile")
        if not step_path.startswith(
            "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/"
            "current-full-frame-member-solids-attempt01/bundle/members/"
        ):
            raise ValueError(f"{member_id}: STEP path is outside the pinned current member bundle")
        if file_sha256(step_path) != step_digest:
            raise ValueError(f"{member_id}: current STEP file hash changed")
        density = float(source_mass["density_kg_m3"])
        if density != float(scenario_row["density_kg_m3"]) or density != MODELED_WOOD_DENSITY_KG_M3:
            raise ValueError(f"{member_id}: timber density scenario mismatch")
        if abs(density - MODELED_WOOD_DENSITY_KG_M3) > 1e-12:
            raise ValueError(f"{member_id}: unexpected modeled density")

        axis = unit([float(value) for value in descriptor["axis"]], f"{member_id} axis")
        section_u = unit(
            [float(value) for value in descriptor["section_u"]], f"{member_id} section_u"
        )
        section_v = unit(
            [float(value) for value in descriptor["section_v"]], f"{member_id} section_v"
        )
        grain_axis = unit(
            [float(value) for value in grain["proposed_global_xyz"]], f"{member_id} grain"
        )
        start = [float(value) for value in descriptor["start"]]
        end = [float(value) for value in descriptor["end"]]
        length = float(descriptor["length_mm"])
        end_vector = subtract(end, start)
        if abs(magnitude(end_vector) - length) > GEOMETRY_TOLERANCE_MM:
            raise ValueError(f"{member_id}: start/end distance differs from descriptor length")
        if dot(unit(end_vector, f"{member_id} start/end"), axis) < 1.0 - 1e-10:
            raise ValueError(f"{member_id}: descriptor axis does not point from start to end")
        if dot(axis, grain_axis) < 1.0 - 1e-8:
            raise ValueError(f"{member_id}: descriptor axis is not sign-aligned with conditional grain")
        if abs(dot(axis, section_u)) > 1e-8 or abs(dot(axis, section_v)) > 1e-8:
            raise ValueError(f"{member_id}: descriptor section axes are not transverse")
        expected_section_v = unit(cross(axis, section_u), f"{member_id} expected section_v")
        if dot(expected_section_v, section_v) < 1.0 - 1e-8:
            raise ValueError(f"{member_id}: descriptor section frame is not right-handed")

        shape = importers.importStep(str(ROOT / step_path)).val()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"{member_id}: exact STEP must be one valid solid")
        actual_volume = float(shape.Volume())
        actual_center = [float(value) for value in shape.Center().toTuple()]
        source_volume = float(source_mass["volume_mm3"])
        source_center = [float(value) for value in source_mass["mass_center_global_xyz_mm"]]
        if abs(actual_volume - source_volume) > SOURCE_VOLUME_TOLERANCE_MM3:
            raise ValueError(f"{member_id}: exact STEP volume differs from source mass inventory")
        if max_abs(actual_center, source_center) > SOURCE_CENTROID_TOLERANCE_MM:
            raise ValueError(f"{member_id}: exact STEP centroid differs from source mass inventory")

        bounds = shape.BoundingBox()
        bbox_corners = [
            [x, y, z]
            for x in (bounds.xmin, bounds.xmax)
            for y in (bounds.ymin, bounds.ymax)
            for z in (bounds.zmin, bounds.zmax)
        ]
        transverse_half_width = max(
            max(abs(dot(subtract(corner, start), section_u)), abs(dot(subtract(corner, start), section_v)))
            for corner in bbox_corners
        ) + 1.0
        projected_vertices = [
            dot(subtract([float(value) for value in vertex.Center().toTuple()], start), axis)
            for vertex in shape.Vertices()
        ]
        projection_min = min(projected_vertices)
        projection_max = max(projected_vertices)
        if projection_min < -END_CAP_CLIP_SLACK_MM or projection_max > length + END_CAP_CLIP_SLACK_MM:
            raise ValueError(f"{member_id}: descriptor span does not cover exact STEP longitudinal vertices")

        raw_bins = slice_shape(
            shape,
            start,
            axis,
            section_u,
            length,
            BIN_LENGTH_MM,
            transverse_half_width,
        )
        profiled_bins, profile_mass, profile_force, profile_moment = profile_wrench(
            raw_bins,
            density,
            GRAVITY_M_S2,
            start,
            axis,
        )
        profile_volume = math.fsum(float(row["volume_mm3"]) for row in raw_bins)
        profile_first_moment = [
            math.fsum(
                float(row["volume_mm3"]) * float(row["centroid_global_xyz_mm"][component])
                for row in raw_bins
                if row["centroid_global_xyz_mm"] is not None
            )
            for component in range(3)
        ]
        profile_center = [value / profile_volume for value in profile_first_moment]
        profile_volume_error = profile_volume - actual_volume
        profile_center_error = max_abs(profile_center, actual_center)
        source_mass_kg = float(source_mass["mass_kg"])
        source_force = [float(value) for value in source_mass["gravity_force_global_xyz_n"]]
        source_moment = [
            float(value) for value in source_mass["gravity_moment_about_global_origin_nmm"]
        ]
        force_error = max_abs(profile_force, source_force)
        moment_error = max_abs(profile_moment, source_moment)
        source_centroid_error = max_abs(profile_center, source_center)
        if abs(profile_volume_error) > max(SOURCE_VOLUME_TOLERANCE_MM3, actual_volume * PROFILE_VOLUME_REL_TOLERANCE):
            raise ValueError(f"{member_id}: binned volume does not close to exact STEP volume")
        if profile_center_error > PROFILE_CENTROID_TOLERANCE_MM:
            raise ValueError(f"{member_id}: binned first moment does not close to exact STEP centroid")
        if abs(profile_mass - source_mass_kg) > 1e-9:
            raise ValueError(f"{member_id}: binned mass does not close to source inventory")
        if force_error > FORCE_CLOSURE_TOLERANCE_N or moment_error > MOMENT_CLOSURE_TOLERANCE_NMM:
            raise ValueError(f"{member_id}: binned gravity wrench does not close to source inventory")

        frame_rows.append(
            {
                "member_id": member_id,
                "member_kind": "frame_timber",
                "step_path": step_path,
                "step_sha256": step_digest,
                "source_inventory_density_kg_m3": density,
                "density_status": "conditional modeled scenario; not measured received stock",
                "descriptor_axis_global_xyz_unit": axis,
                "conditional_grain_axis_global_xyz_unit": grain_axis,
                "section_u_global_xyz_unit": section_u,
                "section_v_global_xyz_unit": section_v,
                "descriptor_start_global_xyz_mm": start,
                "descriptor_end_global_xyz_mm": end,
                "descriptor_length_mm": length,
                "exact_step_volume_mm3": actual_volume,
                "exact_step_centroid_global_xyz_mm": actual_center,
                "source_inventory_volume_mm3": source_volume,
                "source_inventory_mass_kg": source_mass_kg,
                "source_inventory_centroid_global_xyz_mm": source_center,
                "vertex_projection_min_from_start_mm": projection_min,
                "vertex_projection_max_from_start_mm": projection_max,
                "transverse_clipping_half_width_mm": transverse_half_width,
                "bin_count": len(profiled_bins),
                "profile_volume_mm3": profile_volume,
                "profile_mass_kg": profile_mass,
                "profile_centroid_global_xyz_mm": profile_center,
                "profile_gravity_force_global_xyz_n": profile_force,
                "profile_gravity_moment_about_global_origin_nmm": profile_moment,
                "closure": {
                    "profile_minus_exact_volume_mm3": profile_volume_error,
                    "profile_minus_exact_centroid_max_abs_mm": profile_center_error,
                    "profile_minus_source_centroid_max_abs_mm": source_centroid_error,
                    "profile_minus_source_mass_kg": profile_mass - source_mass_kg,
                    "profile_minus_source_force_max_abs_n": force_error,
                    "profile_minus_source_moment_max_abs_nmm": moment_error,
                    "passed": True,
                },
                "bins": profiled_bins,
            }
        )

    source_total_mass = math.fsum(float(row["source_inventory_mass_kg"]) for row in frame_rows)
    profile_total_mass = math.fsum(float(row["profile_mass_kg"]) for row in frame_rows)
    source_total_force = [
        math.fsum(float(row["source_inventory_mass_kg"]) * 0.0 for row in frame_rows),
        math.fsum(float(row["source_inventory_mass_kg"]) * 0.0 for row in frame_rows),
        -source_total_mass * GRAVITY_M_S2,
    ]
    profile_total_force = [
        math.fsum(float(row["profile_gravity_force_global_xyz_n"][component]) for row in frame_rows)
        for component in range(3)
    ]
    source_total_moment = [
        math.fsum(
            -float(row["source_inventory_mass_kg"])
            * GRAVITY_M_S2
            * float(row["source_inventory_centroid_global_xyz_mm"][1])
            for row in frame_rows
        ),
        math.fsum(
            float(row["source_inventory_mass_kg"])
            * GRAVITY_M_S2
            * float(row["source_inventory_centroid_global_xyz_mm"][0])
            for row in frame_rows
        ),
        0.0,
    ]
    profile_total_moment = [
        math.fsum(float(row["profile_gravity_moment_about_global_origin_nmm"][component]) for row in frame_rows)
        for component in range(3)
    ]
    global_force_error = max_abs(profile_total_force, source_total_force)
    global_moment_error = max_abs(profile_total_moment, source_total_moment)
    if global_force_error > FORCE_CLOSURE_TOLERANCE_N or global_moment_error > MOMENT_CLOSURE_TOLERANCE_NMM:
        raise ValueError("Combined 20-member binned gravity wrench does not close")

    record = {
        "attempt_id": "current-frame-beam-selfweight-profile-attempt01",
        "candidate": EXPECTED_CANDIDATE,
        "geometry_revision_id": EXPECTED_REVISION,
        "status": "EXPLORATORY_CONDITIONAL_FINITE_BIN_MASS_AND_CENTROID_PROFILE",
        "cadquery_version": cq.__version__,
        "producer_path": str((HERE / "produce.py").relative_to(ROOT)),
        "producer_sha256": file_sha256(str((HERE / "produce.py").relative_to(ROOT))),
        "source_pins": pins,
        "method": {
            "geometry_source": "The exact pinned STEP BReps are clipped by oriented rectangular slabs normal to each source-bound member-geometry axis.",
            "longitudinal_axis_source": "member-geometry.json axis/start/end descriptors; verified sign-aligned with the conditional grain vector in the pinned material-frame map.",
            "obb_used": False,
            "principal_inertia_axis_used": False,
            "cross_section_frame_source": "member-geometry.json section_u and section_v; checked orthonormal, transverse, and right-handed with axis.",
            "bin_length_mm": BIN_LENGTH_MM,
            "end_cap_clip_slack_mm": END_CAP_CLIP_SLACK_MM,
            "density_kg_m3": MODELED_WOOD_DENSITY_KG_M3,
            "density_basis": "Per-member mass-centroid/board-weight modeled scenario; uniform within each exact STEP solid, not measured received stock.",
            "gravity_m_s2": GRAVITY_M_S2,
            "transverse_cutter_half_width": "Maximum absolute section_u/section_v projection of the exact STEP global AABB corners from descriptor start plus 1 mm; this bounds the imported BRep crosswise even where the descriptor centerline endpoint lies beyond one global AABB face.",
            "bin_representative": "Each bin reports its BRep volume centroid; bin gravity force at that centroid preserves that bin's force and first moment under the uniform-density scenario.",
            "line_load_interpretation": "mean_uniform_equivalent_line_load_n_per_m is bin weight divided by descriptor station length; the accompanying equivalent_axis_couple preserves that bin's resultant wrench if reduced to the descriptor axis.",
        },
        "known_answer_fixture": run_known_answer_fixture(cq.__version__),
        "source_body_count": 20,
        "profiled_body_count": len(frame_rows),
        "total_conditional_mass_kg": profile_total_mass,
        "total_conditional_weight_n": profile_total_mass * GRAVITY_M_S2,
        "source_inventory_total_mass_kg": source_total_mass,
        "combined_profile_gravity_force_global_xyz_n": profile_total_force,
        "combined_source_gravity_force_global_xyz_n": source_total_force,
        "combined_profile_gravity_moment_about_global_origin_nmm": profile_total_moment,
        "combined_source_gravity_moment_about_global_origin_nmm": source_total_moment,
        "combined_force_closure_max_abs_n": global_force_error,
        "combined_moment_closure_max_abs_nmm": global_moment_error,
        "closure_tolerances": {
            "source_volume_abs_mm3": SOURCE_VOLUME_TOLERANCE_MM3,
            "source_centroid_abs_mm": SOURCE_CENTROID_TOLERANCE_MM,
            "profile_volume_rel": PROFILE_VOLUME_REL_TOLERANCE,
            "profile_centroid_abs_mm": PROFILE_CENTROID_TOLERANCE_MM,
            "force_abs_n": FORCE_CLOSURE_TOLERANCE_N,
            "moment_abs_nmm": MOMENT_CLOSURE_TOLERANCE_NMM,
        },
        "claim_limits": [
            "This is a finite-bin mass/centroid and whole-wrench accounting profile, not an exact continuous q(s) or continuous eccentric-moment distribution.",
            "The grain direction, member axis, start/end stations, cross-section frame, density, and uniform-within-body density are conditional source scenarios, not observations of delivered lumber.",
            "The 50 mm bins do not define structural supports, effective spans, releases, joint stiffness, or beam end conditions.",
            "No mesh, solver, beam section-force recovery, member/joint demand, capacity, or design acceptance is included.",
            "Only 20 frame timbers are profiled; panels, blocks, hardware, equipment allowance, climber loads, and support reactions are outside this record.",
        ],
        "members": frame_rows,
    }
    record["content_sha256"] = sha256_bytes(canonical_json(record))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preview", action="store_true", help="compute and print summary without writing")
    group.add_argument("--write", action="store_true", help="write the new record; refuses overwrite")
    group.add_argument("--verify", action="store_true", help="recompute and verify the existing record")
    args = parser.parse_args()

    record = build_record()
    if args.preview:
        preview = {
            "status": record["status"],
            "producer_sha256": record["producer_sha256"],
            "content_sha256": record["content_sha256"],
            "member_count": record["profiled_body_count"],
            "total_conditional_mass_kg": record["total_conditional_mass_kg"],
            "total_conditional_weight_n": record["total_conditional_weight_n"],
            "combined_force_closure_max_abs_n": record["combined_force_closure_max_abs_n"],
            "combined_moment_closure_max_abs_nmm": record["combined_moment_closure_max_abs_nmm"],
            "known_answer_fixture": record["known_answer_fixture"],
        }
        print(json.dumps(preview, indent=2, sort_keys=True))
        return 0
    if args.write:
        if OUTPUT.exists():
            raise FileExistsError(f"Refusing to overwrite append-only record: {OUTPUT}")
        OUTPUT.write_text(json.dumps(record, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        print(f"wrote {OUTPUT.relative_to(ROOT)}")
        print(f"content_sha256 {record['content_sha256']}")
        return 0

    if not OUTPUT.is_file():
        raise FileNotFoundError(f"Expected existing append-only record: {OUTPUT}")
    existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
    digest_payload = dict(existing)
    claimed_digest = digest_payload.pop("content_sha256", None)
    if claimed_digest != sha256_bytes(canonical_json(digest_payload)):
        raise ValueError("Stored profile content digest is invalid")
    if existing != record:
        raise ValueError("Recomputed profile differs from the stored append-only record")
    print(f"verified {OUTPUT.relative_to(ROOT)}")
    print(f"content_sha256 {record['content_sha256']}")
    print(f"producer_sha256 {record['producer_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
