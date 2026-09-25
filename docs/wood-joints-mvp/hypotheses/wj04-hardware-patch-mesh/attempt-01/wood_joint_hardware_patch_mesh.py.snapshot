"""Prepare disjoint C3D10 meshes for one frozen WJ04 metal profile.

This is a geometry and mesh-evidence stage only. It does not assign material,
contact, ties, preload, loads, or solver cards, and it does not mesh the forty
legacy collision-role envelopes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from typing import Any

from fea import wood_joint_patch_mesh as wood_mesh
from fea.stitch_joint_mesh import (
    GMSH_TO_CCX,
    append_body,
    external_faces,
    surface_faces,
    validate_ownership,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "wood_joint_wj04_hardware_patch_mesh/v1"
HARDWARE_SCHEMA = "wood_joint_wj04_mechanics_hardware/v1"
HARDWARE_INVENTORY_SHA256 = "ea9b292466470898be61445242cabf83176dab4f4711eab83ed74aad15d3b883"
HARDWARE_HASH_INDEX_SHA256 = "c794a877cdb8ecd5338fcf52a6a8c179a3187a29aac6eb6d796f002adc6641af"
HARDWARE_BUILDER_PATH = "scripts/wood_joint_wj04_mechanics_hardware.py"
FROZEN_HARDWARE_BUILDER_SHA256 = "221e9222e74ad8ca83882b44e59edf9186339e0ba388f4f3b8327770775f0ad5"
FROZEN_WOOD_MESH_SHA256 = "915ab6d14efc6e81b4a95c4338ffb8b98cb7e4fac1478d23b592bc8bb377564b"
FROZEN_STITCH_MESH_SHA256 = "9e7bdd4467457cade47f1464e8a3b17cfde69ebb5729719787dd9218011b166e"
FROZEN_FLOOR_CONTACT_SHA256 = "f72c9de2f046f6f207974779de555bfa37f5964484ffae2293fc450c35025825"
SCENARIO_IDS = ("body_to_far_wood_face", "Lb_boundary_root_sensitivity")
STACK_IDS = (
    "lower_rail_1",
    "lower_rail_2",
    "lower_principal_1",
    "lower_principal_2",
    "upper_rail_1",
    "upper_rail_2",
    "upper_principal_1",
    "upper_principal_2",
)
COMPONENT_ROLES = ("bolt", "head_washer", "nut_washer", "nut")
COMPONENT_FILES = frozenset(f"{role}.step" for role in COMPONENT_ROLES)
EXPECTED_RECEIVERS = {
    "lower_rail_1": ("wj04_lower_full_stock_cleat", "base_rail_service_lower_right"),
    "lower_rail_2": ("wj04_lower_full_stock_cleat", "base_rail_service_lower_right"),
    "lower_principal_1": ("wj04_lower_full_stock_cleat", "base_principal_center_right"),
    "lower_principal_2": ("wj04_lower_full_stock_cleat", "base_principal_center_right"),
    "upper_rail_1": ("base_rail_service_upper_right", "wj04_upper_g7_crosscut_full_stock_cleat"),
    "upper_rail_2": ("base_rail_service_upper_right", "wj04_upper_g7_crosscut_full_stock_cleat"),
    "upper_principal_1": ("wj04_upper_g7_crosscut_full_stock_cleat", "base_principal_center_right"),
    "upper_principal_2": ("wj04_upper_g7_crosscut_full_stock_cleat", "base_principal_center_right"),
}
LIMITS = (
    "Independent physical-metal geometry meshes only; no material, active contact, "
    "tie, preload, load, native solve, strength result, or release claim."
)
WORKER_SOURCE_PATHS = (
    "fea/wood_joint_hardware_patch_mesh.py",
    "fea/wood_joint_patch_mesh.py",
    "fea/stitch_joint_mesh.py",
    "fea/floor_contact.py",
    HARDWARE_BUILDER_PATH,
)

CAD_IMPORT_RELATIVE_VOLUME_TOLERANCE = 1e-7
CAD_IMPORT_POSITION_TOLERANCE_MM = 1e-3
SURFACE_SAMPLE_GEOMETRY_TOLERANCE_MM = 2e-3
SURFACE_PLANE_TOLERANCE_MM = 1e-2
NORMAL_ALIGNMENT_TOLERANCE = 2e-3


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def write_json(path: str | Path, record: Any) -> None:
    Path(path).write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _finite_vector(value: Any, length: int, context: str) -> tuple[float, ...]:
    try:
        result = tuple(float(component) for component in value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected {length} finite coordinates") from error
    if len(result) != length or not all(math.isfinite(component) for component in result):
        raise ValueError(f"{context}: expected {length} finite coordinates")
    return result


def _finite_positive(value: Any, context: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{context}: expected a positive finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{context}: expected a positive finite number") from error
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{context}: expected a positive finite number")
    return number


def validate_mesh_configuration(
    global_max_size_mm: float,
    local_min_size_mm: float,
    surface_refinement_band_mm: float,
) -> dict[str, float]:
    global_size = _finite_positive(global_max_size_mm, "global metal mesh size")
    local_size = _finite_positive(local_min_size_mm, "local metal mesh size")
    band = _finite_positive(surface_refinement_band_mm, "surface refinement band")
    if local_size > global_size:
        raise ValueError("local metal mesh size must not exceed the global size")
    return {
        "global_max_size_mm": global_size,
        "local_min_size_mm": local_size,
        "surface_refinement_band_mm": band,
    }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _scenario_rows(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = inventory.get("scenarios")
    if not isinstance(rows, list):
        raise TypeError("hardware inventory has no scenario list")
    result = {row.get("scenario_id"): row for row in rows if isinstance(row, dict)}
    if len(result) != len(rows) or set(result) != set(SCENARIO_IDS):
        raise ValueError("hardware inventory must contain exactly both pinned profiles")
    return result


def _validate_inventory_contract(inventory: dict[str, Any]) -> None:
    if not isinstance(inventory, dict):
        raise TypeError("hardware inventory root must be an object")
    if inventory.get("schema") != HARDWARE_SCHEMA:
        raise ValueError("hardware inventory schema is not the frozen WJ04 profile export")
    if inventory.get("status") != "conditional_response_hardware_geometry_only":
        raise ValueError("hardware inventory status exceeds the frozen geometry-only scope")
    scope = inventory.get("scope")
    if not isinstance(scope, dict) or any(
        scope.get(key) != value
        for key, value in (
            ("finished_wood_bodies_consumed", 5),
            ("unique_physical_bolts", 8),
            ("physical_solids_per_scenario", 32),
            ("scenarios", 2),
            ("grip_each_bolt_mm", 127.0),
            ("native_solver_run", False),
            ("mesh_generated", False),
            ("capacity_or_release_claim", False),
        )
    ):
        raise ValueError("hardware inventory scope or claim boundary changed")
    geometry = inventory.get("selected_hardware_geometry")
    if not isinstance(geometry, dict):
        raise TypeError("hardware inventory selected geometry is missing")
    bolt_data = geometry.get("bolt", {})
    washer_data = geometry.get("each_of_two_washers_per_bolt", {})
    nut_data = geometry.get("nut", {})
    for label, part in (("bolt", bolt_data), ("washers", washer_data), ("nut", nut_data)):
        if not isinstance(part, dict):
            raise TypeError(f"selected {label} geometry is missing")
    if bolt_data.get("sku") != "25C600HCS5Z" or bolt_data.get("nominal_length_mm") != 152.4:
        raise ValueError("selected ordinary-joint bolt is not the pinned six-inch SKU")
    if nut_data.get("sku") != "25CNFH5Z":
        raise ValueError("selected nut is not the pinned physical nut scenario")
    for key in ("smooth_body_diameter_mm", "head_height_mm", "head_across_corners_mm"):
        _finite_positive(bolt_data.get(key), f"selected bolt {key}")
    for key in ("outside_diameter_mm", "inside_diameter_mm", "thickness_mm"):
        _finite_positive(washer_data.get(key), f"selected washer {key}")
    for key in ("modeled_thickness_mm", "across_corners_mm", "smooth_basic_reference_bore_mm"):
        _finite_positive(nut_data.get(key), f"selected nut {key}")

    source = inventory.get("source_inputs")
    if not isinstance(source, dict):
        raise TypeError("hardware source binding is missing")
    if tuple(source.get("frozen_physical_bolt_ids", ())) != tuple(
        f"wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{stack_id}"
        for stack_id in STACK_IDS
    ):
        raise ValueError("physical bolt ID inventory differs from the WJ04 eight-axis contract")
    if set(source.get("frozen_wood_ids", ())) != {
        "base_principal_center_right",
        "base_rail_service_lower_right",
        "base_rail_service_upper_right",
        "wj04_lower_full_stock_cleat",
        "wj04_upper_g7_crosscut_full_stock_cleat",
    }:
        raise ValueError("WJ04 five-body source inventory changed")
    if source.get("sha256", {}).get("patch_inventory.json") != (
        wood_mesh.FROZEN_PATCH_INVENTORY_SHA256
    ) or source.get("sha256", {}).get("mechanics_inputs.json") != (
        wood_mesh.FROZEN_MANIFEST_SHA256
    ):
        raise ValueError("hardware profile no longer binds the frozen WJ16 mechanics inputs")

    transition_expectations = {
        "body_to_far_wood_face": ("conditional body-through-wood profile", 129.032),
        "Lb_boundary_root_sensitivity": ("named sensitivity switch, not actual thread start", 127.0),
    }
    for scenario_id, scenario in _scenario_rows(inventory).items():
        expected_kind, expected_station = transition_expectations[scenario_id]
        if scenario.get("transition_kind") != expected_kind or not math.isclose(
            float(scenario.get("transition_station_mm", math.nan)),
            expected_station,
            rel_tol=0,
            abs_tol=1e-9,
        ):
            raise ValueError(f"{scenario_id}: profile transition datum changed")
        stacks = scenario.get("stacks")
        if not isinstance(stacks, list) or len(stacks) != len(STACK_IDS):
            raise ValueError(f"{scenario_id}: expected exactly eight physical bolt stacks")
        stack_rows = {row.get("stack_spec_id"): row for row in stacks if isinstance(row, dict)}
        if len(stack_rows) != len(stacks) or set(stack_rows) != set(STACK_IDS):
            raise ValueError(f"{scenario_id}: physical stack IDs are missing, duplicate, or unknown")
        if scenario.get("physical_bolt_count") != 8 or scenario.get("physical_solid_count") != 32:
            raise ValueError(f"{scenario_id}: physical part counts differ from 8 × 4")
        for stack_id in STACK_IDS:
            row = stack_rows[stack_id]
            expected_id = (
                "wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/" + stack_id
            )
            if row.get("physical_bolt_id") != expected_id or row.get("scenario_id") != scenario_id:
                raise ValueError(f"{scenario_id}/{stack_id}: physical bolt identity changed")
            receiver_ids = tuple(
                item.get("member_id") for item in row.get("receivers_head_to_nut", ())
            )
            if receiver_ids != EXPECTED_RECEIVERS[stack_id]:
                raise ValueError(f"{scenario_id}/{stack_id}: ordered receiver binding changed")
            if row.get("wood_grip_mm") != 127.0 or row.get("wood_or_washer_tie_assigned") is not False:
                raise ValueError(f"{scenario_id}/{stack_id}: grip or no-tie contract changed")
            axis = _finite_vector(
                row.get("world_axis_direction_head_to_nut"), 3, f"{scenario_id}/{stack_id} axis"
            )
            if not math.isclose(math.sqrt(math.fsum(value * value for value in axis)), 1.0, abs_tol=1e-8):
                raise ValueError(f"{scenario_id}/{stack_id}: axis direction is not unit length")
            _finite_vector(
                row.get("underhead_origin_global_xyz_mm"), 3, f"{scenario_id}/{stack_id} origin"
            )
            if row.get("component_role_names") != ["bolt", "head_washer", "nut", "nut_washer"]:
                raise ValueError(f"{scenario_id}/{stack_id}: physical component roles changed")
            component_solids = row.get("component_solids")
            if not isinstance(component_solids, dict) or set(component_solids) != set(COMPONENT_ROLES):
                raise ValueError(f"{scenario_id}/{stack_id}: expected four separate physical solids")
            for role in COMPONENT_ROLES:
                solid = component_solids[role]
                if not isinstance(solid, dict) or solid.get("solid_count") != 1:
                    raise ValueError(f"{scenario_id}/{stack_id}/{role}: expected one solid")
                _finite_positive(solid.get("volume_mm3"), f"{scenario_id}/{stack_id}/{role} volume")
                _finite_vector(solid.get("centroid_global_xyz_mm"), 3, f"{scenario_id}/{stack_id}/{role} centroid")
                _finite_vector(solid.get("bounds_xyz_mm"), 6, f"{scenario_id}/{stack_id}/{role} bounds")
                if not _is_sha256(solid.get("cad_shape_sha256")):
                    raise ValueError(f"{scenario_id}/{stack_id}/{role}: solid fingerprint is missing")

    legacy_roles = inventory.get("legacy_collision_role_metadata")
    if not isinstance(legacy_roles, list) or len(legacy_roles) != 40:
        raise ValueError("legacy collision-role metadata must remain forty nonphysical records")
    legacy_counts: dict[tuple[str, str], int] = {}
    for row in legacy_roles:
        if not isinstance(row, dict) or row.get("interpretation") != (
            "legacy collision envelope metadata only; not a mechanics solid"
        ):
            raise ValueError("legacy collision roles are not explicitly metadata-only")
        key = (str(row.get("physical_bolt_id")), str(row.get("role")))
        legacy_counts[key] = legacy_counts.get(key, 0) + 1
    expected_legacy = {
        (
            f"wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{stack_id}",
            role,
        )
        for stack_id in STACK_IDS
        for role in ("shaft", "head", "head_washer", "nut_washer", "nut")
    }
    if set(legacy_counts) != expected_legacy or any(count != 1 for count in legacy_counts.values()):
        raise ValueError("legacy collision roles must be the exact forty separate envelope records")
    if inventory.get("seat_and_stability_contract", {}).get("contact_law_assigned") is not False:
        raise ValueError("hardware inventory assigns a contact law outside mesh scope")


def _expected_bundle_files() -> set[str]:
    return {"inventory.json", "references/nbs-unified-thread-table2-excerpt.json"} | {
        f"hardware/{scenario_id}/{stack_id}/{role}.step"
        for scenario_id in SCENARIO_IDS
        for stack_id in STACK_IDS
        for role in COMPONENT_ROLES
    }


def load_hardware_bundle(directory: str | Path, scenario_id: str) -> dict[str, Any]:
    """Verify the immutable 64-file archive, returning one explicitly selected profile."""
    if scenario_id not in SCENARIO_IDS:
        raise ValueError(f"scenario_id must be one of {SCENARIO_IDS}")
    source = Path(directory).expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"hardware geometry bundle is unavailable: {source}")
    try:
        inventory_bytes = (source / "inventory.json").read_bytes()
        hash_index_bytes = (source / "sha256.json").read_bytes()
        inventory = json.loads(inventory_bytes)
        hashes = json.loads(hash_index_bytes)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("hardware inventory or hash index is missing or invalid") from error
    if sha256_bytes(inventory_bytes) != HARDWARE_INVENTORY_SHA256:
        raise ValueError("hardware inventory hash differs from the frozen two-profile export")
    if sha256_bytes(hash_index_bytes) != HARDWARE_HASH_INDEX_SHA256:
        raise ValueError("hardware hash index differs from the frozen archive")
    if not isinstance(hashes, dict) or set(hashes) != _expected_bundle_files():
        raise ValueError("hardware hash index differs from the exact 64-STEP archive")
    if hashes.get("inventory.json") != HARDWARE_INVENTORY_SHA256 or any(
        not _is_sha256(value) for value in hashes.values()
    ):
        raise ValueError("hardware hash index contains an invalid or mismatched digest")
    actual_files = {
        path.relative_to(source).as_posix() for path in source.rglob("*") if path.is_file()
    }
    if actual_files != set(hashes) | {"sha256.json"}:
        raise ValueError("hardware bundle has missing or undeclared files")
    _validate_inventory_contract(inventory)

    artifacts = inventory.get("step_artifacts")
    expected_step_files = _expected_bundle_files() - {
        "inventory.json",
        "references/nbs-unified-thread-table2-excerpt.json",
    }
    if not isinstance(artifacts, dict) or set(artifacts) != expected_step_files:
        raise ValueError("hardware STEP artifact map differs from exact two-profile solids")
    input_hashes = {
        "inventory.json": HARDWARE_INVENTORY_SHA256,
        "sha256.json": HARDWARE_HASH_INDEX_SHA256,
    }
    for relative in sorted(_expected_bundle_files()):
        expected_hash = hashes[relative]
        target = source / relative
        if not target.is_file() or sha256_file(target) != expected_hash:
            raise ValueError(f"frozen hardware artifact is missing or changed: {relative}")
        input_hashes[relative] = expected_hash
        if relative not in expected_step_files:
            continue
        artifact = artifacts[relative]
        if not isinstance(artifact, dict) or artifact.get("file_sha256") != expected_hash:
            raise ValueError(f"{relative}: inventory and archive hash disagree")
        checks = artifact.get("identity_checks", {})
        if any(checks.get(name) is not True for name in ("solid_count", "volume", "centroid", "bounds")):
            raise ValueError(f"{relative}: STEP source/readback identity evidence is incomplete")
        difference = checks.get("symmetric_difference", {})
        if difference.get("passed") is not True or difference.get("source_only_volume_mm3") != 0.0 or difference.get("step_only_volume_mm3") != 0.0:
            raise ValueError(f"{relative}: source/STEP solid identity evidence is incomplete")

    scenario = _scenario_rows(inventory)[scenario_id]
    stacks = {row["stack_spec_id"]: row for row in scenario["stacks"]}
    return {
        "path": source,
        "inventory": inventory,
        "inventory_sha256": HARDWARE_INVENTORY_SHA256,
        "hash_index_sha256": HARDWARE_HASH_INDEX_SHA256,
        "input_file_sha256": input_hashes,
        "scenario_id": scenario_id,
        "scenario": scenario,
        "stacks": stacks,
    }


def _source_paths() -> dict[str, Path]:
    return {relative: ROOT / relative for relative in WORKER_SOURCE_PATHS}


def snapshot_sources(output: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    expected = {
        "fea/wood_joint_patch_mesh.py": FROZEN_WOOD_MESH_SHA256,
        "fea/stitch_joint_mesh.py": FROZEN_STITCH_MESH_SHA256,
        "fea/floor_contact.py": FROZEN_FLOOR_CONTACT_SHA256,
        HARDWARE_BUILDER_PATH: FROZEN_HARDWARE_BUILDER_SHA256,
    }
    for relative, path in _source_paths().items():
        data = path.read_bytes()
        digest = sha256_bytes(data)
        hashes[relative] = digest
        target = output / "sources" / f"{relative}.snapshot"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if relative in expected and digest != expected[relative]:
            raise ValueError(f"pinned mesh source changed: {relative}")
    return hashes


def verify_sources(source_hashes: dict[str, str]) -> None:
    for relative, path in _source_paths().items():
        if not path.is_file() or sha256_file(path) != source_hashes[relative]:
            raise ValueError(f"mesh preparation source changed during run: {relative}")


def verify_input_bundle(bundle: dict[str, Any]) -> None:
    current = load_hardware_bundle(bundle["path"], bundle["scenario_id"])
    if current["input_file_sha256"] != bundle["input_file_sha256"]:
        raise ValueError("frozen hardware inventory, hash index, reference, or STEP changed during meshing")


def _dot(first: tuple[float, ...], second: tuple[float, ...]) -> float:
    return math.fsum(a * b for a, b in zip(first, second, strict=True))


def _norm(vector: tuple[float, ...]) -> float:
    return math.sqrt(_dot(vector, vector))


def _unit(vector: tuple[float, ...]) -> tuple[float, ...]:
    length = _norm(vector)
    if not math.isfinite(length) or length <= 0:
        raise ValueError("surface classification encountered a zero direction")
    return tuple(value / length for value in vector)


def _surface_probe_grid(gmsh: Any, tag: int) -> dict[str, Any]:
    low, high = gmsh.model.getParametrizationBounds(2, tag)
    lo = _finite_vector(low, 2, f"surface {tag} low UV")
    hi = _finite_vector(high, 2, f"surface {tag} high UV")
    u_values = (lo[0] + 0.17 * (hi[0] - lo[0]), (lo[0] + hi[0]) / 2, lo[0] + 0.83 * (hi[0] - lo[0]))
    v_values = (lo[1] + 0.17 * (hi[1] - lo[1]), (lo[1] + hi[1]) / 2, lo[1] + 0.83 * (hi[1] - lo[1]))
    probes = []
    for u in u_values:
        for v in v_values:
            xyz = _finite_vector(gmsh.model.getValue(2, tag, [u, v]), 3, f"surface {tag} XYZ sample")
            try:
                normal = _unit(_finite_vector(gmsh.model.getNormal(tag, [u, v]), 3, f"surface {tag} normal"))
            except (RuntimeError, TypeError, ValueError):
                normal = None
            probes.append({"uv": [u, v], "xyz_mm": list(xyz), "normal_global": list(normal) if normal else None})
    return {"parametric_bounds": [list(lo), list(hi)], "probes": probes}


def _surface_axis_metrics(
    probes: list[dict[str, Any]], axis_origin: tuple[float, ...], axis: tuple[float, ...]
) -> list[dict[str, Any]]:
    metrics = []
    for probe in probes:
        point = tuple(float(value) for value in probe["xyz_mm"])
        delta = tuple(value - start for value, start in zip(point, axis_origin, strict=True))
        station = _dot(delta, axis)
        radial = tuple(value - station * unit for value, unit in zip(delta, axis, strict=True))
        normal_values = probe.get("normal_global")
        normal_axis_cosine = None
        if normal_values is not None:
            normal_axis_cosine = _dot(tuple(float(value) for value in normal_values), axis)
        metrics.append(
            {
                "station_from_underhead_mm": station,
                "radius_from_bolt_axis_mm": _norm(radial),
                "normal_axis_cosine": normal_axis_cosine,
            }
        )
    return metrics


def classify_surface_datum(
    surface_type: str,
    probes: list[dict[str, Any]],
    stack: dict[str, Any],
    component_role: str,
    hardware_geometry: dict[str, Any],
) -> dict[str, Any]:
    """Classify a CAD face only from sampled analytic geometry and pinned datums."""
    origin = _finite_vector(stack["underhead_origin_global_xyz_mm"], 3, "underhead origin")
    axis = _unit(_finite_vector(stack["world_axis_direction_head_to_nut"], 3, "bolt axis"))
    metrics = _surface_axis_metrics(probes, origin, axis)
    if not metrics:
        return {
            "status": "unresolved",
            "role_candidates": [],
            "axis_probe_metrics": [],
            "complete_nine_point_normal_grid": False,
        }
    stations = [row["station_from_underhead_mm"] for row in metrics]
    radii = [row["radius_from_bolt_axis_mm"] for row in metrics]
    normal_cosines = [row["normal_axis_cosine"] for row in metrics if row["normal_axis_cosine"] is not None]
    complete_probe_grid = len(probes) == 9 and len(normal_cosines) == 9
    station_low, station_high = min(stations), max(stations)
    role_candidates: list[str] = []
    basis: list[str] = []

    def near_station(target: float) -> bool:
        return max(abs(value - target) for value in stations) <= SURFACE_PLANE_TOLERANCE_MM

    def normal_is_axial() -> bool:
        return complete_probe_grid and all(
            abs(abs(value) - 1.0) <= NORMAL_ALIGNMENT_TOLERANCE for value in normal_cosines
        )

    def normal_is_radial() -> bool:
        return complete_probe_grid and all(
            abs(value) <= NORMAL_ALIGNMENT_TOLERANCE for value in normal_cosines
        )

    def radius_matches(target: float) -> bool:
        return all(abs(value - target) <= SURFACE_SAMPLE_GEOMETRY_TOLERANCE_MM for value in radii)

    bolt = hardware_geometry["bolt"]
    washer = hardware_geometry["each_of_two_washers_per_bolt"]
    nut = hardware_geometry["nut"]
    transition = float(stack["smooth_body_transition_station_from_underhead_mm"])
    tip = float(stack["bolt_tip_station_from_underhead_mm"])
    head_top = -float(bolt["head_height_mm"])
    head_washer_end = float(washer["thickness_mm"])
    nut_washer_start = float(stack["nut_washer_start_station_from_underhead_mm"])
    nut_washer_end = nut_washer_start + float(washer["thickness_mm"])
    nut_start = float(stack["nut_start_station_from_underhead_mm"])
    nut_end = float(stack["nut_end_station_from_underhead_mm"])

    if surface_type == "Cylinder" and normal_is_radial():
        if component_role == "bolt":
            body_radius = float(bolt["smooth_body_diameter_mm"]) / 2
            root_radius = float(inventory_root_diameter(hardware_geometry)) / 2
            if radius_matches(body_radius) and station_low >= -SURFACE_PLANE_TOLERANCE_MM and station_high <= transition + SURFACE_PLANE_TOLERANCE_MM:
                role_candidates.append("bolt_smooth_shank_cylindrical_surface")
                basis.append("cylindrical radius and axis-station interval match the selected smooth-body profile")
            if radius_matches(root_radius) and station_low >= transition - SURFACE_PLANE_TOLERANCE_MM and station_high <= tip + SURFACE_PLANE_TOLERANCE_MM:
                role_candidates.append("bolt_root_sensitivity_cylindrical_surface")
                basis.append("cylindrical radius and axis-station interval match the named root profile")
        elif component_role in {"head_washer", "nut_washer"}:
            inner = float(washer["inside_diameter_mm"]) / 2
            outer = float(washer["outside_diameter_mm"]) / 2
            if radius_matches(inner):
                role_candidates.append("washer_bore_cylindrical_surface")
                basis.append("sampled cylindrical radius matches the pinned washer bore")
            if radius_matches(outer):
                role_candidates.append("washer_outer_cylindrical_surface")
                basis.append("sampled cylindrical radius matches the pinned washer outside diameter")
        elif component_role == "nut" and radius_matches(float(nut["smooth_basic_reference_bore_mm"]) / 2):
            if station_low >= nut_start - SURFACE_PLANE_TOLERANCE_MM and station_high <= nut_end + SURFACE_PLANE_TOLERANCE_MM:
                role_candidates.append("nut_basic_reference_bore_cylindrical_surface")
                basis.append("sampled cylindrical radius and interval match the basic-reference nut bore")

    if surface_type == "Plane" and normal_is_axial():
        if component_role == "bolt":
            if near_station(0.0):
                role_candidates.append("bolt_head_washer_bearing_face")
                basis.append("planar sample and normal match the underhead datum")
            if near_station(head_top):
                role_candidates.append("bolt_head_outer_face")
                basis.append("planar sample matches the catalog-derived head-top station")
            if near_station(tip):
                role_candidates.append("bolt_tip_end_face")
                basis.append("planar sample matches nominal bolt-tip station")
        elif component_role == "head_washer":
            if near_station(0.0):
                role_candidates.append("head_washer_bolt_bearing_face")
                basis.append("planar sample matches the bolt-underhead station")
            if near_station(head_washer_end):
                role_candidates.append("head_washer_wood_seat_face")
                basis.append("planar sample matches the first wood-face station")
        elif component_role == "nut_washer":
            if near_station(nut_washer_start):
                role_candidates.append("nut_washer_wood_seat_face")
                basis.append("planar sample matches the far wood-face station")
            if near_station(nut_washer_end):
                role_candidates.append("nut_washer_nut_bearing_face")
                basis.append("planar sample matches the nut-bearing station")
        elif component_role == "nut":
            if near_station(nut_start):
                role_candidates.append("nut_washer_bearing_face")
                basis.append("planar sample matches the nut start station")
            if near_station(nut_end):
                role_candidates.append("nut_outer_face")
                basis.append("planar sample matches the nut end station")

    if surface_type == "Plane" and normal_is_radial():
        if component_role == "bolt" and station_low >= head_top - SURFACE_PLANE_TOLERANCE_MM and station_high <= SURFACE_PLANE_TOLERANCE_MM:
            role_candidates.append("bolt_head_hex_flat")
            basis.append("planar normals are transverse to the bolt axis within the head station interval")
        if component_role == "nut" and station_low >= nut_start - SURFACE_PLANE_TOLERANCE_MM and station_high <= nut_end + SURFACE_PLANE_TOLERANCE_MM:
            role_candidates.append("nut_hex_flat")
            basis.append("planar normals are transverse to the bolt axis within the nut station interval")

    return {
        "status": "classified" if role_candidates else "unresolved",
        "role_candidates": sorted(set(role_candidates)),
        "classification_basis": sorted(set(basis)),
        "complete_nine_point_normal_grid": complete_probe_grid,
        "axis_probe_metrics": metrics,
        "station_interval_from_underhead_mm": [station_low, station_high],
        "radius_probe_range_mm": [min(radii), max(radii)],
    }


def inventory_root_diameter(hardware_geometry: dict[str, Any]) -> float:
    """Return the named sensitivity diameter (not a received thread boundary)."""
    value = hardware_geometry.get("thread_and_gage_mapping", {}).get("root_sensitivity_diameter_mm")
    if value is None:
        # The hardware exporter keeps thread mapping at report root; callers pass
        # that small metadata object in a geometry view below when available.
        value = hardware_geometry.get("root_sensitivity_diameter_mm")
    return _finite_positive(value, "root-sensitivity reference diameter")


def _mesh_body_id(stack_id: str, role: str) -> str:
    return f"{stack_id}__{role}"


def _surface_geometry(gmsh: Any, tag: int) -> dict[str, Any]:
    row = wood_mesh._surface_geometry(gmsh, tag)
    analytic = _surface_probe_grid(gmsh, tag)
    row["analytic_surface_data"].update(analytic)
    row["semantic_interface_binding"] = "datum classification only; not an active mesh contact assignment"
    return row


def _mesh_solid(
    gmsh: Any,
    bundle: dict[str, Any],
    stack_id: str,
    stack: dict[str, Any],
    role: str,
    settings: dict[str, float],
    all_nodes: dict[int, tuple[float, float, float]],
    all_elements: dict[int, tuple[int, ...]],
) -> dict[str, Any]:
    body_id = _mesh_body_id(stack_id, role)
    relative_step = f"hardware/{bundle['scenario_id']}/{stack_id}/{role}.step"
    step_path = bundle["path"] / relative_step
    solid_metadata = stack["component_solids"][role]
    gmsh.model.add(body_id)
    imported = gmsh.model.occ.importShapes(str(step_path))
    gmsh.model.occ.synchronize()
    if len(imported) != 1 or imported[0][0] != 3:
        raise ValueError(f"{body_id}: STEP must import as exactly one physical solid")
    volumes = gmsh.model.getEntities(3)
    if len(volumes) != 1 or volumes[0][1] != imported[0][1]:
        raise ValueError(f"{body_id}: independent model contains unexpected solids")
    volume_tag = int(imported[0][1])
    cad_volume = float(gmsh.model.occ.getMass(3, volume_tag))
    source_volume = _finite_positive(solid_metadata["volume_mm3"], f"{body_id} source volume")
    import_error = abs(cad_volume / source_volume - 1.0)
    if not math.isfinite(cad_volume) or cad_volume <= 0 or import_error > CAD_IMPORT_RELATIVE_VOLUME_TOLERANCE:
        raise ValueError(f"{body_id}: Gmsh STEP volume differs from the frozen export")
    imported_centroid = tuple(float(value) for value in gmsh.model.occ.getCenterOfMass(3, volume_tag))
    expected_centroid = _finite_vector(solid_metadata["centroid_global_xyz_mm"], 3, f"{body_id} source centroid")
    if any(abs(a - b) > CAD_IMPORT_POSITION_TOLERANCE_MM for a, b in zip(imported_centroid, expected_centroid, strict=True)):
        raise ValueError(f"{body_id}: Gmsh STEP centroid differs from the frozen export")
    imported_bounds = wood_mesh.normalize_gmsh_bounds_xyz(
        gmsh.model.getBoundingBox(3, volume_tag), f"{body_id} Gmsh bounds"
    )
    expected_bounds = _finite_vector(solid_metadata["bounds_xyz_mm"], 6, f"{body_id} source bounds")
    if any(abs(a - b) > CAD_IMPORT_POSITION_TOLERANCE_MM for a, b in zip(imported_bounds, expected_bounds, strict=True)):
        raise ValueError(f"{body_id}: Gmsh STEP bounds differ from the frozen export")

    boundary = gmsh.model.getBoundary(imported, combined=False, oriented=False)
    tags = [int(tag) for dimension, tag in boundary if dimension == 2]
    if not tags or len(tags) != len(set(tags)) or len(tags) != len(boundary):
        raise ValueError(f"{body_id}: expected a unique CAD surface boundary")
    geometry = bundle["inventory"]["selected_hardware_geometry"]
    if "thread_and_gage_mapping" not in geometry:
        geometry = {**geometry, "thread_and_gage_mapping": bundle["inventory"]["thread_and_gage_mapping"]}
    surface_rows: dict[str, dict[str, Any]] = {}
    for tag in tags:
        row = _surface_geometry(gmsh, tag)
        analytic = row["analytic_surface_data"]
        classification = classify_surface_datum(
            row["cad_type"], analytic["probes"], stack, role, geometry
        )
        row["datum_classification"] = classification
        row["tri6_exterior_face_refs"] = []
        row["tri6_node_ids"] = []
        surface_rows[str(tag)] = row

    for name, value in (
        ("Mesh.MeshSizeMax", settings["global_max_size_mm"]),
        ("Mesh.MeshSizeMin", settings["local_min_size_mm"]),
        ("Mesh.MeshSizeFromCurvature", 24),
        ("Mesh.MeshSizeExtendFromBoundary", 0),
        ("Mesh.MeshSizeFromPoints", 0),
        ("Mesh.ElementOrder", 2),
        ("Mesh.SecondOrderLinear", 0),
    ):
        gmsh.option.setNumber(name, value)
    distance_field = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(distance_field, "FacesList", tags)
    threshold_field = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(threshold_field, "InField", distance_field)
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMin", settings["local_min_size_mm"])
    gmsh.model.mesh.field.setNumber(threshold_field, "SizeMax", settings["global_max_size_mm"])
    gmsh.model.mesh.field.setNumber(threshold_field, "DistMin", 0.0)
    gmsh.model.mesh.field.setNumber(
        threshold_field, "DistMax", settings["surface_refinement_band_mm"]
    )
    gmsh.model.mesh.field.setAsBackgroundMesh(threshold_field)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")

    element_types, element_tags_by_type, connectivity_by_type = gmsh.model.mesh.getElements(3)
    if list(map(int, element_types)) != [11] or len(element_tags_by_type) != 1:
        raise ValueError(f"{body_id}: expected Gmsh quadratic tetrahedra only")
    local_elements = wood_mesh.c3d10_elements(element_tags_by_type[0], connectivity_by_type[0])
    used_nodes = {node for row in local_elements.values() for node in row}
    node_tags, coordinates, _parameters = gmsh.model.mesh.getNodes()
    all_local_nodes = {
        int(node): tuple(float(value) for value in coordinates[3 * index : 3 * index + 3])
        for index, node in enumerate(node_tags)
    }
    if not used_nodes <= set(all_local_nodes):
        raise ValueError(f"{body_id}: C3D10 connectivity references an absent node")
    local_nodes = {node: all_local_nodes[node] for node in used_nodes}
    if any(len(point) != 3 or not all(math.isfinite(value) for value in point) for point in local_nodes.values()):
        raise ValueError(f"{body_id}: mesh contains nonfinite coordinates")
    exterior = external_faces(local_elements)
    sampled = tuple(
        float(value)
        for value in gmsh.model.mesh.getElementQualities(element_tags_by_type[0], "minDetJac")
    )
    quadrature_points, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss5")
    _jacobians, determinants, _coordinates = gmsh.model.mesh.getJacobians(11, quadrature_points, volume_tag)
    audit = wood_mesh.audit_mesh_volume(
        cad_volume,
        tuple(float(value) for value in determinants),
        tuple(float(value) for value in weights),
        sampled,
        len(local_elements),
    )
    node_map, element_map = append_body(all_nodes, all_elements, local_nodes, local_elements)
    surface_faces_local: dict[str, list[list[int]]] = {}
    for tag in tags:
        kinds, _surface_element_tags, connectivity = gmsh.model.mesh.getElements(2, tag)
        if list(map(int, kinds)) != [9] or len(connectivity) != 1:
            raise ValueError(f"{body_id} surface {tag}: expected quadratic TRI6 surface mesh")
        flat = connectivity[0]
        if len(flat) % 6:
            raise ValueError(f"{body_id} surface {tag}: incomplete TRI6 connectivity")
        triangles = [tuple(int(value) for value in flat[index : index + 6]) for index in range(0, len(flat), 6)]
        selected = surface_faces(triangles, exterior)
        surface_faces_local[str(tag)] = selected["faces"]
        surface_rows[str(tag)]["tri6_node_ids"] = sorted(node_map[node] for node in selected["nodes"])
    surface_faces_global = wood_mesh.validate_and_remap_surface_coverage(
        exterior, surface_faces_local, element_map
    )
    for tag, refs in surface_faces_global.items():
        surface_rows[tag]["tri6_exterior_face_refs"] = refs

    origin = _finite_vector(stack["underhead_origin_global_xyz_mm"], 3, f"{body_id} underhead origin")
    axis = _unit(_finite_vector(stack["world_axis_direction_head_to_nut"], 3, f"{body_id} axis"))
    classified_surface_count = sum(
        row["datum_classification"]["status"] == "classified" for row in surface_rows.values()
    )
    return {
        "body_id": body_id,
        "physical_bolt_id": stack["physical_bolt_id"],
        "stack_spec_id": stack_id,
        "interface_id": stack["interface_id"],
        "ordered_receivers_head_to_nut": [row["member_id"] for row in stack["receivers_head_to_nut"]],
        "component_role": role,
        "solid_identity": {
            "inventory_sha256": bundle["inventory_sha256"],
            "step_relative_path": relative_step,
            "step_sha256": bundle["input_file_sha256"][relative_step],
            "source_shape_sha256": solid_metadata["cad_shape_sha256"],
            "expected_solid_count": 1,
            "imported_solid_count": len(volumes),
        },
        "axis_datum": {
            "origin_global_xyz_mm": list(origin),
            "origin_basis": "underhead origin from frozen hardware profile inventory",
            "direction_head_to_nut_global": list(axis),
            "station_reference": "axial projection from underhead origin; geometry datum only",
            "profile_transition_station_mm": float(stack["smooth_body_transition_station_from_underhead_mm"]),
            "profile_transition_basis": stack["smooth_body_transition_basis"],
            "nut_interval_mm": [float(stack["nut_start_station_from_underhead_mm"]), float(stack["nut_end_station_from_underhead_mm"])],
            "projected_thread_tie_interval_candidate_mm": [
                max(
                    float(stack["smooth_body_transition_station_from_underhead_mm"]),
                    float(stack["nut_start_station_from_underhead_mm"]),
                ),
                min(
                    float(stack["bolt_tip_station_from_underhead_mm"]),
                    float(stack["nut_end_station_from_underhead_mm"]),
                ),
            ],
            "projected_thread_interval_is_active_tie": False,
        },
        "target_configuration_mm": settings,
        "nodes": sorted(node_map.values()),
        "elements": sorted(element_map.values()),
        "surfaces": surface_rows,
        "surface_classification": {
            "classified_surface_count": classified_surface_count,
            "unresolved_surface_count": len(surface_rows) - classified_surface_count,
            "method": "analytic CAD type plus sampled points/normals projected to pinned fastener axis and station/radius datums; no face ordinal",
            "normal_convention": "sampled parametric normals are compared by unsigned alignment; CAD outward sign is not inferred here",
            "status": "geometry descriptors only; not active tie/contact set assignment",
        },
        "mesh_element_type": "C3D10",
        "gmsh_element_type": 11,
        "gmsh_to_calculix_quadratic_node_order": list(GMSH_TO_CCX),
        "node_count": len(node_map),
        "element_count": len(element_map),
        "exterior_tri6_face_count": len(exterior),
        "imported_cad": {
            "volume_mm3": cad_volume,
            "relative_volume_error_vs_export": import_error,
            "centroid_global_xyz_mm": list(imported_centroid),
            "bounds_xyz_mm": list(imported_bounds),
            "bounds_order": "xmin,xmax,ymin,ymax,zmin,zmax",
            "relative_volume_tolerance": CAD_IMPORT_RELATIVE_VOLUME_TOLERANCE,
            "position_tolerance_mm": CAD_IMPORT_POSITION_TOLERANCE_MM,
        },
        "integrated_mesh_audit": audit,
        "integration_rule": {
            "name": "Gmsh Gauss5 for element type 11",
            "weights_per_element": len(weights),
            "minimum_weight": min(float(value) for value in weights),
            "weight_positivity_basis": "explicit pinned Gmsh C3D10 Gauss5 rule",
        },
    }


def _write_input_deck(
    path: Path,
    nodes: dict[int, tuple[float, float, float]],
    elements: dict[int, tuple[int, ...]],
    bodies: dict[str, Any],
) -> None:
    lines = ["*HEADING", LIMITS, "*NODE"]
    lines.extend(
        f"{node}," + ",".join(repr(float(value)) for value in xyz)
        for node, xyz in sorted(nodes.items())
    )
    for body_id in sorted(bodies):
        elset = "METAL_" + body_id.upper()
        lines.append(f"*ELEMENT,TYPE=C3D10,ELSET={elset}")
        lines.extend(
            f"{element}," + ",".join(str(node) for node in elements[element])
            for element in bodies[body_id]["elements"]
        )
    path.write_text("\n".join(lines) + "\n")


def prepare_hardware_patch_mesh(
    bundle_directory: str | Path,
    output_directory: str | Path,
    *,
    scenario_id: str,
    global_max_size_mm: float,
    local_min_size_mm: float,
    surface_refinement_band_mm: float,
) -> Path:
    """Mesh one selected 32-solid hardware scenario in independent CAD models."""
    settings = validate_mesh_configuration(
        global_max_size_mm, local_min_size_mm, surface_refinement_band_mm
    )
    source_directory = Path(bundle_directory).expanduser().resolve()
    requested_output = Path(output_directory).expanduser().absolute()
    if requested_output.exists() or requested_output.is_symlink():
        raise FileExistsError(f"mesh output directory already exists: {requested_output}")
    output = requested_output.resolve(strict=False)
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"mesh output directory already exists: {output}")
    if output == source_directory or output.is_relative_to(source_directory) or source_directory.is_relative_to(output):
        raise ValueError("mesh output and frozen hardware input directories must be separate")
    output.mkdir(parents=True, exist_ok=False)
    nodes: dict[int, tuple[float, float, float]] = {}
    elements: dict[int, tuple[int, ...]] = {}
    bodies: dict[str, dict[str, Any]] = {}
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "PREPARING_PHYSICAL_HARDWARE_MESH_ONLY",
        "limits": LIMITS,
        "input_bundle_directory": str(source_directory),
        "scenario_id": scenario_id,
        "configuration": settings,
        "accepted": False,
        "solved": False,
        "legacy_collision_role_count_metadata_only": 40,
        "legacy_collision_roles_meshed": 0,
    }
    write_json(output / "mesh.json", record)
    gmsh = None
    initialized = False
    active_body_id: str | None = None
    try:
        source_hashes = snapshot_sources(output)
        bundle = load_hardware_bundle(source_directory, scenario_id)
        record.update(
            {
                "input_bundle_inventory_sha256": bundle["inventory_sha256"],
                "input_bundle_hash_index_sha256": bundle["hash_index_sha256"],
                "input_bundle_file_sha256_before": bundle["input_file_sha256"],
                "mesh_worker_source_sha256": source_hashes,
                "runtime": {"python": platform.python_version()},
                "physical_mesh_scope": {
                    "selected_profile": scenario_id,
                    "physical_bolts": 8,
                    "physical_solids": 32,
                    "component_roles_per_bolt": list(COMPONENT_ROLES),
                    "legacy_collision_roles_preserved_as_metadata": 40,
                    "legacy_collision_roles_meshed": 0,
                    "other_profile_included": False,
                },
                "legacy_collision_roles_metadata_only": bundle["inventory"][
                    "legacy_collision_role_metadata"
                ],
                "material_contact_tie_preload_load_or_solver_cards": False,
                "wood_mesh_bundle_sha256": wood_mesh.FROZEN_PATCH_INVENTORY_SHA256,
                "full24_final_mechanics_claim": False,
            }
        )
        write_json(output / "mesh.json", record)
        import gmsh as gmsh_module
        import numpy

        gmsh = gmsh_module
        if gmsh.isInitialized():
            raise ValueError("independent Gmsh session required for hardware mesh preparation")
        gmsh.initialize()
        initialized = True
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.option.setNumber("General.Verbosity", 2)
        for stack_id in STACK_IDS:
            stack = bundle["stacks"][stack_id]
            for role in COMPONENT_ROLES:
                active_body_id = _mesh_body_id(stack_id, role)
                row = _mesh_solid(
                    gmsh,
                    bundle,
                    stack_id,
                    stack,
                    role,
                    settings,
                    nodes,
                    elements,
                )
                bodies[active_body_id] = row
                record["completed_body_ids"] = list(bodies)
                record["completed_node_count"] = len(nodes)
                record["completed_element_count"] = len(elements)
                record["bodies"] = bodies
                write_json(output / "mesh.json", record)
                gmsh.model.remove()
                active_body_id = None
        if len(bodies) != 32:
            raise ValueError("selected profile mesh did not contain exactly 32 physical solids")
        record["runtime"].update(
            {"gmsh_version": str(gmsh.__version__), "numpy_version": str(numpy.__version__)}
        )
        gmsh.finalize()
        initialized = False
        validate_ownership(nodes, elements, bodies)
        verify_input_bundle(bundle)
        verify_sources(source_hashes)
        deck = output / "mesh.inp"
        _write_input_deck(deck, nodes, elements, bodies)
        record.update(
            {
                "status": "VERIFIED_C3D10_PHYSICAL_METAL_MESH_ONLY_NO_SOLVER",
                "body_count": len(bodies),
                "node_count": len(nodes),
                "element_count": len(elements),
                "bodies": bodies,
                "mesh_input_sha256": sha256_file(deck),
                "input_bundle_file_sha256_after": bundle["input_file_sha256"],
                "mesh_worker_source_sha256_after": source_hashes,
                "output_contains_material_contact_tie_preload_or_solver_cards": False,
                "active_contact_or_tie_set_assignment": False,
                "gmsh_to_calculix_quadratic_node_order": list(GMSH_TO_CCX),
                "open_clearances_preserved": True,
                "capacity_or_release_claim": False,
            }
        )
        write_json(output / "mesh.json", record)
        return output
    except Exception as error:
        failed_model = None
        if initialized and gmsh is not None and active_body_id is not None:
            try:
                failed_model = wood_mesh.preserve_failed_gmsh_model(gmsh, output, active_body_id)
            except Exception as capture_error:  # noqa: BLE001 - preserve original mesh failure
                failed_model = {
                    "body_id": active_body_id,
                    "status": "capture_failed",
                    "capture_error": f"{type(capture_error).__name__}: {capture_error}",
                    "file": None,
                    "sha256": None,
                }
        record.update(
            {
                "status": "FAILED_PHYSICAL_HARDWARE_MESH_PREPARATION_NO_SOLVER",
                "error": f"{type(error).__name__}: {error}",
                "completed_body_ids": list(bodies),
                "completed_node_count": len(nodes),
                "completed_element_count": len(elements),
                "bodies": bodies,
                "failed_gmsh_model": failed_model,
            }
        )
        try:
            write_json(output / "mesh.json", record)
        except Exception as report_error:  # noqa: BLE001 - do not mask original error
            error.add_note(f"Could not update mesh failure record: {type(report_error).__name__}: {report_error}")
        raise
    finally:
        if initialized and gmsh is not None:
            gmsh.finalize()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument("--scenario-id", choices=SCENARIO_IDS, required=True)
    parser.add_argument("--global-max-size-mm", type=float, required=True)
    parser.add_argument("--local-min-size-mm", type=float, required=True)
    parser.add_argument("--surface-refinement-band-mm", type=float, required=True)
    args = parser.parse_args()
    result = prepare_hardware_patch_mesh(
        args.bundle_directory,
        args.output_directory,
        scenario_id=args.scenario_id,
        global_max_size_mm=args.global_max_size_mm,
        local_min_size_mm=args.local_min_size_mm,
        surface_refinement_band_mm=args.surface_refinement_band_mm,
    )
    print(result, flush=True)


if __name__ == "__main__":
    main()
