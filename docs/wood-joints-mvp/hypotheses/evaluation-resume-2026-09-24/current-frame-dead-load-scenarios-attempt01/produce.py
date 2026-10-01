"""Build source-bound gravity and accessory-placement scenario inputs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import math
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import cadquery as cq

from mini_moonboard import (
    hold_tnut_reinforcement,
    no_shoes_frame,
    panel_grid,
    panel_grid_v2,
    product_frame,
    round_structural_wiring,
)

OUTPUT_PATH = Path(__file__).resolve().parent / "dead-load-scenarios.json"
REVISION_ID = "led-clearance-2x6-runner-seated-blocks-v1"
GRAVITY_M_S2 = 9.80665
ACCESSORY_ALLOWANCE_KG = 25.0
ELECTRICAL_SPLITS_KG = (0.0, 12.5, 25.0)
ENDPOINT_SPLIT_KG = 12.5
ENDPOINT_NAMES = (
    "hold_tnut_main_A1",
    "hold_tnut_main_K1",
    "hold_tnut_main_A12",
    "hold_tnut_main_K12",
    "hold_tnut_kicker_1",
    "hold_tnut_kicker_10",
)

INPUT_PATHS = {
    "candidate_contract": "wood-joints-candidate.json",
    "selected_candidate": "current-candidate.json",
    "geometry_snapshot": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json",
    "full_frame_manifest": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/current-full-frame-input-manifest.json",
    "load_cases": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-cases.json",
    "load_datums": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-load-datums.json",
    "mass_centroids": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json",
    "mass_topology": "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json",
    "review_scene": "site/owner-wood-joints-wj24-scene.json",
    "review_report": "site/owner-wood-joints-review-report.json",
    "baseline_parts": "site/hybrid/compact-floor-flush-kerf-right/parts.json",
}

DOCUMENT_PATHS = (
    "docs/wood-joints-mvp/current-frame-dead-load-map.md",
    "docs/wood-joints-mvp/current-frame-mass-source-topology-map.md",
    "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/README.md",
)

RUNTIME_DATA_PATHS = (
    "docs/ml24z-reference.json",
    "docs/panel-insert-reference.json",
    "docs/round-service-wiring-reference.json",
    "docs/led-wiring-reference.json",
)

SOURCE_PATHS = (
    "pyproject.toml",
    "uv.lock",
    "mini_moonboard/box_frame.py",
    "mini_moonboard/compact_floor_flush_frame.py",
    "mini_moonboard/floor_flush_width.py",
    "mini_moonboard/hold_tnut_reinforcement.py",
    "mini_moonboard/model.py",
    "mini_moonboard/no_shoes_frame.py",
    "mini_moonboard/panel_grid.py",
    "mini_moonboard/panel_grid_v2.py",
    "mini_moonboard/product_frame.py",
    "mini_moonboard/round_insert_frame.py",
    "mini_moonboard/round_service_frame.py",
    "mini_moonboard/round_service_wiring.py",
    "mini_moonboard/round_structural_frame.py",
    "mini_moonboard/round_structural_wiring.py",
    "mini_moonboard/timber_frame.py",
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _loaded_geometry_source_paths() -> tuple[str, ...]:
    """Pin every project geometry module loaded while building the shapes."""
    module_root = ROOT / "mini_moonboard"
    paths = set()
    for module in tuple(sys.modules.values()):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        path = Path(module_file).resolve()
        if path.suffix != ".py":
            continue
        try:
            relative_path = path.relative_to(module_root)
        except ValueError:
            continue
        paths.add((module_root / relative_path).relative_to(ROOT).as_posix())
    return tuple(sorted(paths))


def _canonical_sha256(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _sha256_bytes(payload)


def _read_json(relative: str) -> dict[str, Any]:
    value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{relative} must contain a JSON object")
    return value


def _vector3(value: Any, label: str) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{label} must be a 3-vector")
    vector = tuple(float(component) for component in value)
    if not all(math.isfinite(component) for component in vector):
        raise ValueError(f"{label} contains a non-finite value")
    return vector


def _cross(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _add(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a + b for a, b in zip(first, second, strict=True))


def _subtract(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    return tuple(a - b for a, b in zip(first, second, strict=True))


def _mean(points: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    if not points:
        raise ValueError("cannot average an empty point set")
    return tuple(math.fsum(point[index] for point in points) / len(points)
                 for index in range(3))


def _close_vector(
    first: tuple[float, float, float],
    second: tuple[float, float, float],
    *,
    tolerance: float = 1e-8,
) -> bool:
    return math.dist(first, second) <= tolerance


def _validate_mass_sources(
    mass_export: dict[str, Any], topology: dict[str, Any]
) -> dict[str, Any]:
    rows = mass_export.get("rows")
    topology_rows = topology.get("physical_mass_rows")
    if not isinstance(rows, list) or not isinstance(topology_rows, list):
        raise TypeError("mass rows are missing from the pinned source artifacts")
    if len(rows) != 778 or len(topology_rows) != 778:
        raise ValueError("the current modeled-mass inventory must contain 778 rows")

    by_name = {row["name"]: row for row in rows}
    topology_by_name = {row["inventory_name"]: row for row in topology_rows}
    if len(by_name) != 778 or set(by_name) != set(topology_by_name):
        raise ValueError("mass-centroid and topology row identities differ")

    for name, row in by_name.items():
        mapped = topology_by_name[name]
        for field, topology_field in (
            ("mass_kg", "mass_kg"),
            ("mass_center_global_xyz_mm", "mass_center_global_xyz_mm"),
            ("gravity_force_global_xyz_n", "gravity_force_global_xyz_n"),
            ("gravity_moment_about_global_origin_nmm", "gravity_moment_about_global_origin_nmm"),
        ):
            first, second = row[field], mapped[topology_field]
            if isinstance(first, list):
                if not _close_vector(_vector3(first, f"{name}.{field}"),
                                     _vector3(second, f"{name}.{topology_field}"),
                                     tolerance=1e-10):
                    raise ValueError(f"mass source rows differ for {name}.{field}")
            elif not math.isclose(float(first), float(second), rel_tol=1e-12, abs_tol=1e-12):
                raise ValueError(f"mass source rows differ for {name}.{field}")

    total_mass = math.fsum(float(row["mass_kg"]) for row in rows)
    total_force = tuple(
        math.fsum(float(row["gravity_force_global_xyz_n"][axis]) for row in rows)
        for axis in range(3)
    )
    total_moment = tuple(
        math.fsum(
            float(row["gravity_moment_about_global_origin_nmm"][axis])
            for row in rows
        )
        for axis in range(3)
    )
    center = tuple(
        math.fsum(
            float(row["mass_kg"]) * float(row["mass_center_global_xyz_mm"][axis])
            for row in rows
        ) / total_mass
        for axis in range(3)
    )
    if not math.isclose(total_mass, float(mass_export["modeled_mass_kg"]),
                        rel_tol=1e-12, abs_tol=1e-12):
        raise ValueError("mass row sum differs from the exported mass total")
    if not _close_vector(total_force,
                         _vector3(mass_export["gravity_force_global_xyz_n"], "mass gravity force"),
                         tolerance=1e-8):
        raise ValueError("gravity force row sum differs from the exported total")
    if not _close_vector(total_moment,
                         _vector3(mass_export["gravity_moment_about_global_origin_nmm"], "mass gravity moment"),
                         tolerance=1e-6):
        raise ValueError("gravity moment row sum differs from the exported total")
    if not _close_vector(center,
                         _vector3(mass_export["modeled_mass_center_global_xyz_mm"], "mass center"),
                         tolerance=1e-8):
        raise ValueError("mass row centroid differs from the exported total")
    if float(mass_export["equipment_allowance_kg_excluded_from_centroid"]) != ACCESSORY_ALLOWANCE_KG:
        raise ValueError("the separate 25 kg allowance must remain excluded")
    if topology.get("equipment_allowance", {}).get("included_in_mass_rows") is not False:
        raise ValueError("the topology map must keep the allowance outside mass rows")

    group_counts = dict(sorted(Counter(row["group"] for row in rows).items()))
    return {
        "row_count": len(rows),
        "group_counts": group_counts,
        "modeled_mass_kg": total_mass,
        "mass_center_global_xyz_mm": center,
        "gravity_force_global_xyz_n": total_force,
        "gravity_moment_about_global_origin_nmm": total_moment,
    }


def _project_main_mass_center(
    point: tuple[float, float, float],
    anchor: tuple[float, float, float],
    normal: tuple[float, float, float],
) -> tuple[float, float, float]:
    distance = math.fsum((point[index] - anchor[index]) * normal[index]
                         for index in range(3))
    return tuple(point[index] - distance * normal[index] for index in range(3))


def _hold_axis_records(
    mass_export: dict[str, Any],
    load_datums: dict[str, Any],
    scene: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_rows = hold_tnut_reinforcement.datums(no_shoes_frame)
    if len(source_rows) != 142 or len({row["name"] for row in source_rows}) != 142:
        raise ValueError("expected 132 main and 10 kicker hold axes")
    mass_centers = {
        row["name"]: _vector3(row["mass_center_global_xyz_mm"], row["name"])
        for row in mass_export["rows"]
        if row["group"] == "hold T-nuts"
    }
    if len(mass_centers) != 142:
        raise ValueError("the source mass export must contain 142 T-nut centers")

    current_datums = load_datums.get("holds", {})
    main_anchor = _vector3(current_datums["A1"]["face_datum_global_mm"], "A1 face")
    main_outward = _vector3(current_datums["A1"]["outward_normal_global"], "A1 normal")
    face_thickness = float(product_frame.FACE_THICKNESS_MM)
    if not math.isclose(face_thickness, 18.25625, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError("current panel face thickness differs from its pinned datum")

    main_grid = panel_grid_v2.main_tnut_datums()
    kicker_grid = panel_grid.kicker_foothold_datums()
    scene_solids = {row["id"]: row for row in scene["solids"]}
    kicker_faces = [
        float(scene_solids[f"kicker_{side}"]["mesh"]["bounds_xyz_mm"][3])
        for side in ("left", "right")
    ]
    if max(kicker_faces) - min(kicker_faces) > 1e-8:
        raise ValueError("the two current kicker panel face planes differ")
    kicker_face_y = math.fsum(kicker_faces) / 2
    expected_kicker_face_y = (
        float(no_shoes_frame.base.HEADER_FRONT_Y) + face_thickness
    )
    if not math.isclose(kicker_face_y, expected_kicker_face_y,
                        rel_tol=0.0, abs_tol=1e-8):
        raise ValueError("the current kicker face bound differs from its source transform")

    records = []
    projected_mass_centers = []
    face_points = []
    for source in source_rows:
        name = source["name"]
        rear = _vector3(source["rear_seating_xyz_mm"], f"{name} rear axis")
        tnut_center = mass_centers[name]
        if name.startswith("hold_tnut_main_"):
            label = source["label"]
            x_grid, station = main_grid[label]
            face = tuple(no_shoes_frame.b.point(
                x_grid - no_shoes_frame.b.HALF,
                station,
                -face_thickness,
            ).toTuple())
            outward = tuple(-value for value in no_shoes_frame.b.normal().normalized().toTuple())
            projected_mass = _project_main_mass_center(
                tnut_center, main_anchor, main_outward
            )
        else:
            x_grid, z_offset = kicker_grid[source["label"]]
            face = (float(x_grid - no_shoes_frame.b.HALF),
                    kicker_face_y,
                    float(no_shoes_frame.b.V1_KICKER_HEIGHT_MM + z_offset))
            outward = (0.0, 1.0, 0.0)
            projected_mass = (tnut_center[0], kicker_face_y, tnut_center[2])

        if not _close_vector(face, projected_mass, tolerance=1e-8):
            raise ValueError(f"grid face point and projected T-nut center differ: {name}")
        record = {
            "axis_id": name,
            "label": source["label"],
            "panel_id": source["panel"],
            "rear_axis_point_global_xyz_mm": rear,
            "climbing_face_axis_point_global_xyz_mm": face,
            "outward_normal_global": outward,
            "source_tnut_mass_center_global_xyz_mm": tnut_center,
        }
        records.append(record)
        face_points.append(face)
        projected_mass_centers.append(projected_mass)

    by_name = {row["axis_id"]: row for row in records}
    if not set(ENDPOINT_NAMES) <= set(by_name):
        raise ValueError("one or more named hold-axis endpoint scenarios are missing")
    for label in ("A1", "A12", "K12"):
        actual = _vector3(current_datums[label]["face_datum_global_mm"], f"{label} datum")
        if not _close_vector(
            actual,
            by_name[f"hold_tnut_main_{label}"]["climbing_face_axis_point_global_xyz_mm"],
            tolerance=1e-8,
        ):
            raise ValueError(f"current load datum does not match the face transform: {label}")

    rear_centroid = _mean([row["rear_axis_point_global_xyz_mm"] for row in records])
    face_centroid = _mean(face_points)
    max_projection_error = max(math.dist(first, second)
                               for first, second in zip(face_points, projected_mass_centers, strict=True))
    return records, {
        "axis_count": len(records),
        "main_axis_count": sum(row["axis_id"].startswith("hold_tnut_main_") for row in records),
        "kicker_axis_count": sum(row["axis_id"].startswith("hold_tnut_kicker_") for row in records),
        "rear_axis_equal_weight_centroid_global_xyz_mm": rear_centroid,
        "climbing_face_equal_weight_centroid_global_xyz_mm": face_centroid,
        "mass_center_projection_cross_check_max_error_mm": max_projection_error,
        "face_thickness_mm": face_thickness,
        "kicker_face_y_mm": kicker_face_y,
        "endpoint_axis_ids": list(ENDPOINT_NAMES),
        "projection_basis": "Main axes use current panel-grid transforms; kicker axes use the current face bound. Projected source T-nut mass centers cross-check every axis point.",
        "cross_check_limit": "T-nut mass centers come from the parent CAD reader; no serialized-BRep replay is performed here.",
    }


def _current_electrical_shapes(
    report: dict[str, Any],
    scene: dict[str, Any],
    baseline_parts: dict[str, Any],
) -> tuple[list[tuple[str, str, float, tuple[float, float, float]]], dict[str, Any]]:
    replacements = report.get("electrical_replacements", {})
    expected_replacements = {
        "light_G2": "lights",
        "wire_073_G1_G2": "wires",
        "wire_074_G2_G3": "wires",
    }
    if replacements != expected_replacements:
        raise ValueError("the reviewed electrical replacement identities changed")
    if scene["model_inventory"].get("electrical_replacements") != expected_replacements:
        raise ValueError("the scene does not bind the reviewed electrical replacements")

    manifest_rows = baseline_parts.get("parts")
    if not isinstance(manifest_rows, list):
        raise TypeError("baseline parts manifest is malformed")
    baseline_electrical_names = {
        row["name"] for row in manifest_rows
        if row["name"].startswith(("light_", "wire_"))
    }
    if len(baseline_electrical_names) != 263:
        raise ValueError("baseline must enumerate all 132 lights and 131 wires")

    expected_asset_hashes = scene["baseline_asset_sha256"]
    electrical_asset_count = 0
    for row in manifest_rows:
        if row["name"] not in baseline_electrical_names:
            continue
        relative_asset = row["path"]
        expected_hash = expected_asset_hashes.get(relative_asset)
        if not isinstance(expected_hash, str):
            raise ValueError(f"baseline scene does not pin {relative_asset}")
        asset_path = ROOT / "site" / relative_asset
        if _sha256_file(asset_path) != expected_hash:
            raise ValueError(f"baseline electrical asset hash differs: {relative_asset}")
        electrical_asset_count += 1
    if electrical_asset_count != 263:
        raise ValueError("not all baseline electrical assets were source-checked")

    changed_scene_solids = {row["id"]: row for row in scene["solids"]}
    source_parts = no_shoes_frame.electrical_parts()
    source_names = {part.name for part in source_parts}
    if source_names != baseline_electrical_names or len(source_parts) != 263:
        raise ValueError("current CAD source and baseline electrical identities differ")

    light_move = _vector3(report["led_move"]["translation_xyz_mm"], "G2 translation")
    wire_revisions = report.get("wire_endpoint_revisions", {})
    if set(wire_revisions) != {"wire_073_G1_G2", "wire_074_G2_G3"}:
        raise ValueError("the reviewed G2 wire revisions changed")

    revised_wire_shapes: dict[str, cq.Shape] = {}
    revised_wire_checks = {}
    for name, revision in wire_revisions.items():
        route = copy.deepcopy(revision["route_local_mm"])
        record = {"route_local_mm": route}
        path = round_structural_wiring.wire_path(record)
        actual_length = float(path.Length())
        if not math.isclose(
            actual_length,
            float(revision["routed_length_mm"]),
            rel_tol=1e-11,
            abs_tol=1e-8,
        ):
            raise ValueError(f"reviewed route length differs from its source path: {name}")
        first, second = [round_structural_wiring.b.point(*point) for point in route[:2]]
        plane = cq.Plane(origin=first, normal=(second - first).normalized())
        shape = cq.Workplane(plane).circle(
            round_structural_wiring.CABLE_DIAMETER_MM / 2
        ).sweep(cq.Workplane(obj=path), isFrenet=True).val()
        shape = shape.translate(cq.Vector(*revision["source_placement_xyz_mm"]))
        revised_wire_shapes[name] = shape
        revised_wire_checks[name] = {
            "source_path_length_mm": actual_length,
            "reviewed_path_length_mm": float(revision["routed_length_mm"]),
        }

    rows = []
    changed_shape_checks = {}
    for part in source_parts:
        shape = part.shape
        if part.name == "light_G2":
            shape = shape.translate(cq.Vector(*light_move))
        elif part.name in revised_wire_shapes:
            shape = revised_wire_shapes[part.name]
        volume = float(shape.Volume())
        center = tuple(float(value) for value in shape.Center().toTuple())
        if volume <= 0.0 or not math.isfinite(volume):
            raise ValueError(f"electrical body has an invalid volume: {part.name}")
        rows.append((part.name, part.kind, volume, center))

        if part.name in expected_replacements:
            bounds = shape.BoundingBox()
            calculated_bounds = (
                bounds.xmin, bounds.xmax,
                bounds.ymin, bounds.ymax,
                bounds.zmin, bounds.zmax,
            )
            scene_bounds = tuple(
                float(value)
                for value in changed_scene_solids[part.name]["mesh"]["bounds_xyz_mm"]
            )
            bound_error = max(abs(a - b) for a, b in zip(
                calculated_bounds, scene_bounds, strict=True
            ))
            if bound_error > 1e-6:
                raise ValueError(f"current replacement bounds differ from the reviewed scene: {part.name}")
            changed_shape_checks[part.name] = {
                "volume_mm3": volume,
                "centroid_global_xyz_mm": center,
                "scene_brep_bound_max_error_mm": bound_error,
            }

    kinds = Counter(row[1] for row in rows)
    total_volume = math.fsum(row[2] for row in rows)
    centroid = tuple(
        math.fsum(row[2] * row[3][axis] for row in rows) / total_volume
        for axis in range(3)
    )
    if len(rows) != 263 or kinds != {"light": 132, "wire": 131}:
        raise ValueError("current electrical body counts differ from the reviewed baseline")
    return rows, {
        "separate_body_count": len(rows),
        "body_counts": dict(sorted(kinds.items())),
        "baseline_electrical_asset_hashes_checked": electrical_asset_count,
        "sum_of_separate_body_volumes_mm3": total_volume,
        "sum_body_volume_weighted_centroid_global_xyz_mm": centroid,
        "changed_replacement_body_checks": changed_shape_checks,
        "revised_wire_path_checks": revised_wire_checks,
        "centroid_basis": "Volume-weighted sum of all separate current CAD bodies; overlapping bodies are counted once per body and no Boolean union is taken.",
        "centroid_limit": "Nominal model envelope under provisional light/cable geometry, not actual installed electrical equipment mass CG.",
    }


def _gravity_at_point(
    mass_kg: float, point: tuple[float, float, float]
) -> dict[str, Any]:
    force = (0.0, 0.0, -mass_kg * GRAVITY_M_S2)
    return {
        "mass_kg": mass_kg,
        "point_global_xyz_mm": point,
        "gravity_force_global_xyz_n": force,
        "gravity_moment_about_global_origin_nmm": _cross(point, force),
    }


def _scenario_rows(
    hold_centroid: tuple[float, float, float],
    electrical_centroid: tuple[float, float, float],
    endpoint_points: dict[str, tuple[float, float, float]],
) -> list[dict[str, Any]]:
    specs = []
    for electrical_mass in ELECTRICAL_SPLITS_KG:
        specs.append((
            f"split_{str(electrical_mass).replace('.', '_')}_kg_hold_mean",
            electrical_mass,
            "equal_axis_weighted_face_centroid",
            hold_centroid,
        ))
    for axis_name in ENDPOINT_NAMES:
        if axis_name.startswith("hold_tnut_main_"):
            label = axis_name.removeprefix("hold_tnut_main_")
        else:
            label = f"kicker_{axis_name.removeprefix('hold_tnut_kicker_')}"
        specs.append((
            f"split_12_5_kg_hold_at_{label}",
            ENDPOINT_SPLIT_KG,
            f"single_face_axis_endpoint:{axis_name}",
            endpoint_points[axis_name],
        ))

    scenarios = []
    for scenario_id, electrical_mass, hold_distribution, hold_point in specs:
        hold_mass = ACCESSORY_ALLOWANCE_KG - electrical_mass
        hold_load = _gravity_at_point(hold_mass, hold_point)
        electrical_load = _gravity_at_point(electrical_mass, electrical_centroid)
        total_force = _add(
            hold_load["gravity_force_global_xyz_n"],
            electrical_load["gravity_force_global_xyz_n"],
        )
        total_moment = _add(
            hold_load["gravity_moment_about_global_origin_nmm"],
            electrical_load["gravity_moment_about_global_origin_nmm"],
        )
        if not math.isclose(hold_mass + electrical_mass, ACCESSORY_ALLOWANCE_KG,
                            rel_tol=0.0, abs_tol=1e-12):
            raise ValueError(f"accessory budget does not reconcile: {scenario_id}")
        scenarios.append({
            "scenario_id": scenario_id,
            "status": "ANALYTICAL_PLACEMENT_SCENARIO_NOT_OBSERVED_INSTALLATION",
            "accessory_budget_kg": ACCESSORY_ALLOWANCE_KG,
            "hold_and_hold_bolt_mass_kg": hold_mass,
            "electrical_mass_kg": electrical_mass,
            "hold_distribution": hold_distribution,
            "hold_outward_cg_offset_mm": 0.0,
            "hold_outward_offset_basis": "Baseline face projection only; actual outward CG offset is unknown and the climber 100 mm standoff is not reused.",
            "hold_gravity": hold_load,
            "electrical_location_basis": "Current 263-body sum-volume centroid; electrical mass amount remains a scenario parameter.",
            "electrical_gravity": electrical_load,
            "accessory_gravity_force_global_xyz_n": total_force,
            "accessory_gravity_moment_about_global_origin_nmm": total_moment,
        })
    if len(scenarios) != 9:
        raise ValueError("expected three split and six hold-axis endpoint scenarios")
    return scenarios


def _combined_case_resultants(
    scenarios: list[dict[str, Any]],
    cases: list[dict[str, Any]],
    modeled_force: tuple[float, float, float],
    modeled_moment: tuple[float, float, float],
) -> list[dict[str, Any]]:
    results = []
    for scenario in scenarios:
        accessory_force = _vector3(
            scenario["accessory_gravity_force_global_xyz_n"], "accessory force"
        )
        accessory_moment = _vector3(
            scenario["accessory_gravity_moment_about_global_origin_nmm"],
            "accessory moment",
        )
        dead_force = _add(modeled_force, accessory_force)
        dead_moment = _add(modeled_moment, accessory_moment)
        for case in cases:
            wrench = case["applied_wrench"]
            reference = _vector3(
                wrench["reference_point_global_xyz_mm"], "case reference point"
            )
            climber_force = _vector3(wrench["force_global_xyz_n"], "case force")
            climber_moment_at_reference = _vector3(
                wrench["moment_global_xyz_nmm"], "case moment"
            )
            climber_moment_at_origin = _add(
                climber_moment_at_reference,
                _cross(reference, climber_force),
            )
            combined_force = _add(climber_force, dead_force)
            combined_moment_at_origin = _add(climber_moment_at_origin, dead_moment)
            combined_moment_at_reference = _subtract(
                combined_moment_at_origin,
                _cross(reference, combined_force),
            )
            results.append({
                "scenario_id": scenario["scenario_id"],
                "case_id": case["case_id"],
                "dead_load_resultant_force_global_xyz_n": dead_force,
                "dead_load_resultant_moment_about_global_origin_nmm": dead_moment,
                "combined_external_force_global_xyz_n": combined_force,
                "combined_external_moment_about_global_origin_nmm": combined_moment_at_origin,
                "combined_external_wrench_at_case_reference": {
                    "reference_point_global_xyz_mm": reference,
                    "force_global_xyz_n": combined_force,
                    "moment_global_xyz_nmm": combined_moment_at_reference,
                },
                "interpretation": "Resultant reconciliation only; preserve 778 body-level gravity inputs and do not replace their distributed application with this wrench.",
            })
    return results


def build_contract() -> dict[str, Any]:
    inputs = {name: _read_json(path) for name, path in INPUT_PATHS.items()}
    input_hashes = {
        path: _sha256_file(ROOT / path) for path in INPUT_PATHS.values()
    }
    producer_path = Path(__file__).resolve()
    producer_hash = _sha256_file(producer_path)

    candidate = inputs["candidate_contract"]
    selected = inputs["selected_candidate"]
    geometry = inputs["geometry_snapshot"]
    manifest = inputs["full_frame_manifest"]
    scene = inputs["review_scene"]
    report = inputs["review_report"]
    baseline_parts = inputs["baseline_parts"]
    load_cases = inputs["load_cases"]
    load_datums = inputs["load_datums"]
    mass_export = inputs["mass_centroids"]
    topology = inputs["mass_topology"]

    if candidate.get("candidate") != "compact-floor-flush-wood-joints-development":
        raise ValueError("the reviewed wood-joints development candidate changed")
    if selected.get("candidate") != "compact-floor-flush-development":
        raise ValueError("the selected candidate authority changed")
    if geometry.get("revision_id") != REVISION_ID or scene.get("revision_id") != REVISION_ID:
        raise ValueError("current geometry revision differs from the reviewed candidate")
    if report.get("revision_id") != REVISION_ID:
        raise ValueError("review report revision differs from the current candidate")
    if scene.get("source_binding", {}).get("revision_report_sha256") != input_hashes[
        INPUT_PATHS["review_report"]
    ]:
        raise ValueError("review scene does not bind the current review report")
    if scene.get("baseline_manifest_sha256") != input_hashes[INPUT_PATHS["baseline_parts"]]:
        raise ValueError("review scene does not bind the baseline parts manifest")
    if manifest.get("manifest_id") != "current-full-frame-input-manifest-attempt02":
        raise ValueError("the full-frame source manifest is not attempt02")
    if (
        manifest.get("candidate") != candidate["candidate"]
        or manifest.get("geometry_revision_id") != REVISION_ID
        or manifest.get("selected_candidate_authority_preserved") != selected["candidate"]
    ):
        raise ValueError("the full-frame manifest is bound to a different candidate authority")
    manifest_readiness = manifest.get("readiness", {})
    if (
        manifest_readiness.get("inventory_complete") is not True
        or manifest_readiness.get("inputs_ready") is not False
        or manifest_readiness.get("native_solve_executed") is not False
    ):
        raise ValueError("full-frame manifest readiness flags changed")
    if load_cases.get("geometry_revision_id") != REVISION_ID:
        raise ValueError("six-case applied loads target a different geometry revision")
    if mass_export.get("revision_id") != REVISION_ID or topology.get("revision_id") != REVISION_ID:
        raise ValueError("mass source artifacts target a different geometry revision")

    mass_summary = _validate_mass_sources(mass_export, topology)
    hold_axes, hold_summary = _hold_axis_records(mass_export, load_datums, scene)
    electrical_rows, electrical_summary = _current_electrical_shapes(
        report, scene, baseline_parts
    )
    source_paths = (
        *INPUT_PATHS.values(),
        *DOCUMENT_PATHS,
        *RUNTIME_DATA_PATHS,
        *SOURCE_PATHS,
        *_loaded_geometry_source_paths(),
    )
    source_hashes = {
        path: _sha256_file(ROOT / path) for path in dict.fromkeys(source_paths)
    }
    hold_centroid = _vector3(
        hold_summary["climbing_face_equal_weight_centroid_global_xyz_mm"],
        "hold-axis centroid",
    )
    electrical_centroid = _vector3(
        electrical_summary["sum_body_volume_weighted_centroid_global_xyz_mm"],
        "electrical centroid",
    )
    endpoint_points = {
        row["axis_id"]: _vector3(
            row["climbing_face_axis_point_global_xyz_mm"], row["axis_id"]
        )
        for row in hold_axes
        if row["axis_id"] in ENDPOINT_NAMES
    }
    scenarios = _scenario_rows(hold_centroid, electrical_centroid, endpoint_points)

    body_force = _vector3(mass_summary["gravity_force_global_xyz_n"], "body gravity")
    body_moment = _vector3(
        mass_summary["gravity_moment_about_global_origin_nmm"], "body gravity moment"
    )
    combined = _combined_case_resultants(
        scenarios,
        load_cases["cases"],
        body_force,
        body_moment,
    )

    payload = {
        "schema": "wood_joint_current_frame_dead_load_scenarios/v1",
        "status": "SOURCE_BOUND_LOAD_INPUTS_ONLY_NOT_SOLVER_READY",
        "candidate": candidate["candidate"],
        "selected_candidate_preserved": selected["candidate"],
        "revision_id": REVISION_ID,
        "source_sha256": dict(sorted(source_hashes.items())),
        "producer_sha256": producer_hash,
        "environment": {
            "python_version": sys.version.split()[0],
            "cadquery_version": importlib.metadata.version("cadquery"),
        },
        "modeled_body_gravity": {
            **mass_summary,
            "source_centroid_artifact": INPUT_PATHS["mass_centroids"],
            "source_topology_artifact": INPUT_PATHS["mass_topology"],
            "application_policy": "Preserve all 778 source rows. Use direct density on matching meshed bodies or distributed member gravity for reduced physical members; represent omitted component masses at mapped carriers. Solver DOFs and mass carriers are not implemented.",
            "not_a_single_point_load": True,
        },
        "accessory_allowance": {
            "budget_kg": ACCESSORY_ALLOWANCE_KG,
            "gravity_magnitude_n": ACCESSORY_ALLOWANCE_KG * GRAVITY_M_S2,
            "mass_groups": {
                "holds_and_hold_bolts": "25 kg minus m_electrical; no actual split is known",
                "electrical": "m_electrical in the explicit [0, 25] kg scenario sweep",
            },
            "already_modeled_and_excluded_from_budget": [
                "142 hold T-nuts",
                "92 candidate bolt/washer/nut stacks",
                "12 retained frame-bolt/washer/nut stacks",
                "66 panel/kicker screw-axis mass proxies",
            ],
            "hold_axis_projection": hold_summary,
            "hold_axes": hold_axes,
            "electrical_location": electrical_summary,
            "electrical_body_rows": [
                {
                    "body_id": name,
                    "kind": kind,
                    "volume_mm3": volume,
                    "centroid_global_xyz_mm": center,
                }
                for name, kind, volume, center in electrical_rows
            ],
            "scenarios": scenarios,
            "outward_hold_cg_offset_policy": "Every scenario explicitly uses 0 mm additional outward offset as the face-projected reference case. Actual hold CG may be outward; no physical offset or sensitivity range is established.",
            "limits": [
                "The 25 kg budget and component split are estimates, not measured masses or an observed installation.",
                "Equal axis weighting and endpoint placements bound location scenarios; they are not the actual hold distribution.",
                "The electrical point is a sum-of-separate-BRep-body-volume proxy, not the mass center of the installed electrical system.",
                "The T-nut and screw masses already in the 778 rows are not counted again in this allowance.",
            ],
        },
        "gravity_and_six_case_resultants": {
            "gravity_m_s2": GRAVITY_M_S2,
            "gravity_multiplier_per_case": 1.0,
            "source_applied_load_cases": INPUT_PATHS["load_cases"],
            "scenario_case_resultants": combined,
            "limit": "Combined wrenches are arithmetic checks only. Do not use them in place of body-level distributed gravity or infer support/connection force sharing.",
        },
        "planning_totals": {
            "modeled_mass_kg": mass_summary["modeled_mass_kg"],
            "additional_accessory_allowance_kg": ACCESSORY_ALLOWANCE_KG,
            "total_planning_mass_kg": mass_summary["modeled_mass_kg"] + ACCESSORY_ALLOWANCE_KG,
            "total_gravity_force_global_xyz_n": _add(
                body_force, (0.0, 0.0, -ACCESSORY_ALLOWANCE_KG * GRAVITY_M_S2)
            ),
        },
        "readiness": {
            "inventory_complete": manifest_readiness["inventory_complete"],
            "inputs_ready": False,
            "native_solve_run": False,
            "solver_dof_mapping_implemented": False,
            "mechanical_acceptance": False,
            "candidate_accepted": False,
            "fabrication_released": False,
            "climbing_released": False,
        },
        "limits": [
            "This artifact supplies source-bound dead-load accounting and location scenarios only.",
            "It does not build or map the full-frame solver model, connections, material laws, constraints, or boundary conditions.",
            "The full-frame manifest remains inventory-complete and inputs-not-ready; do not launch full-frame cases from this artifact.",
            "No support reactions, joint demands, stability response, capacity, acceptance, or release is established.",
            "Electrical CAD bodies are constructed in memory from pinned source for centroid calculation; no STEP/STL is exported or source geometry modified.",
        ],
    }
    payload = json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False))
    payload["contract_sha256"] = _canonical_sha256(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="create the frozen scenario artifact")
    mode.add_argument("--verify", action="store_true", help="recompute and compare without writing")
    args = parser.parse_args()

    payload = build_contract()
    if args.write:
        with OUTPUT_PATH.open("x", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
        print(json.dumps({
            "status": "written",
            "path": str(OUTPUT_PATH.relative_to(ROOT)),
            "contract_sha256": payload["contract_sha256"],
            "hold_face_centroid_mm": payload["accessory_allowance"]["hold_axis_projection"]["climbing_face_equal_weight_centroid_global_xyz_mm"],
            "electrical_centroid_mm": payload["accessory_allowance"]["electrical_location"]["sum_body_volume_weighted_centroid_global_xyz_mm"],
            "scenario_count": len(payload["accessory_allowance"]["scenarios"]),
        }, indent=2))
        return 0

    if not OUTPUT_PATH.is_file():
        raise FileNotFoundError(f"scenario artifact is missing: {OUTPUT_PATH}")
    actual = json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    if actual != payload:
        raise ValueError("current source-derived scenario payload differs from the frozen artifact")
    print(json.dumps({
        "status": "verified",
        "path": str(OUTPUT_PATH.relative_to(ROOT)),
        "contract_sha256": actual["contract_sha256"],
        "scenario_count": len(actual["accessory_allowance"]["scenarios"]),
        "inputs_ready": actual["readiness"]["inputs_ready"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
