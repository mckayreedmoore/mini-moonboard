"""Verify and emit a source-only R75/H1 mesh preparation record.

This module deliberately has no CAD, Gmsh, solver, Docker, or network imports.
It does not create geometry, mesh inputs, solver decks, or a parent freeze.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PINS = HERE / "source-pins.json"
SCHEMA = "conditional_washer_crop_mesh_source_preparation/v1"
EXPECTED_ORACLE = {
    "H1_nut_volume_mm3": 415.50205345278425,
    "H2_nut_volume_mm3": 404.7247322297162,
    "nut_outward_face_area_mm2": 75.51784511932227,
    "H1_initial_land_area_mm2": 57.48292325873653,
    "washer_volume_mm3": 355.5139185846077,
    "washer_annular_face_area_mm2": 223.9457754863671,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def _close(a: float, b: float, *, atol: float = 1e-9) -> bool:
    return math.isfinite(a) and math.isfinite(b) and abs(a - b) <= atol


def hex_disk_area(radius: float, apothem: float, clip_radius: float) -> float:
    """Area of a regular hexagon intersected by a centered limiting disk."""
    values = (radius, apothem, clip_radius)
    if not all(math.isfinite(value) and value > 0 for value in values):
        raise ValueError("hex/disk radii must be finite and positive")
    radius = min(radius, clip_radius)
    if radius <= apothem:
        return math.pi * radius * radius
    half_sector = math.pi / 6
    switch = math.acos(min(1.0, apothem / radius))
    if switch >= half_sector:
        return 6 * apothem * apothem * math.tan(half_sector)
    return 6 * (
        apothem * apothem * math.tan(switch)
        + radius * radius * (half_sector - switch)
    )


def _simpson(function: Any, low: float, high: float) -> float:
    middle = (low + high) / 2
    return (high - low) * (
        function(low) + 4 * function(middle) + function(high)
    ) / 6


def _adaptive_simpson(
    function: Any,
    low: float,
    high: float,
    *,
    tolerance: float = 1e-11,
    depth: int = 24,
) -> float:
    whole = _simpson(function, low, high)

    def split(a: float, b: float, estimate: float, tol: float, left: int) -> float:
        middle = (a + b) / 2
        first = _simpson(function, a, middle)
        second = _simpson(function, middle, b)
        correction = first + second - estimate
        if left <= 0 or abs(correction) <= 15 * tol:
            return first + second + correction / 15
        return split(a, middle, first, tol / 2, left - 1) + split(
            middle, b, second, tol / 2, left - 1
        )

    return split(low, high, whole, tolerance, depth)


def nut_profile_metrics(profile: dict[str, Any], land: str) -> dict[str, float]:
    """Independent source-only section integration of the parent H1/H2 laws."""
    if land not in {"H1", "H2"}:
        raise ValueError("the profile branch must be H1 or H2")
    height = float(profile["nut_height"])
    apothem = float(profile["silhouette"]["regular_hex_across_flats"]) / 2
    clip_radius = float(profile["silhouette"]["coaxial_corner_clip_diameter"]) / 2
    land_radius = float(profile["bearing_side_outer_relief"][f"{land}_land_outer_radius"])
    inner_land = float(profile["bearing_side_inner_relief"]["land_inner_radius"])
    bore_radius = float(profile["bearing_side_inner_relief"]["smooth_through_bore_radius"])
    diameter_clip = float(profile["silhouette"]["coaxial_corner_clip_diameter"])
    if not _close(diameter_clip, 2 * clip_radius):
        raise ValueError("invalid corner clip definition")

    def cross_section(depth: float) -> float:
        outer = min(clip_radius, land_radius + depth)
        inner = max(bore_radius, inner_land - depth)
        return hex_disk_area(outer, apothem, clip_radius) - math.pi * inner * inner

    cut_points = sorted(
        {
            0.0,
            height,
            min(height, max(0.0, apothem - land_radius)),
            min(height, max(0.0, clip_radius - land_radius)),
            min(height, inner_land - bore_radius),
        }
    )
    volume = math.fsum(
        _adaptive_simpson(cross_section, a, b)
        for a, b in zip(cut_points, cut_points[1:])
        if b > a
    )
    face_area = hex_disk_area(clip_radius, apothem, clip_radius) - math.pi * bore_radius**2
    land_area = math.pi * (land_radius**2 - inner_land**2)
    outer_relief_depth = clip_radius - land_radius
    return {
        "volume_mm3": volume,
        "outward_face_area_mm2": face_area,
        "initial_land_area_mm2": land_area,
        "outer_relief_to_full_silhouette_depth_mm": outer_relief_depth,
    }


def washer_metrics(od: float, inner: float, thickness: float) -> dict[str, float]:
    if not all(math.isfinite(value) and value > 0 for value in (od, inner, thickness)):
        raise ValueError("washer dimensions must be finite and positive")
    if inner >= od:
        raise ValueError("washer inner diameter must be below its outer diameter")
    face_area = math.pi / 4 * (od * od - inner * inner)
    return {"face_area_mm2": face_area, "volume_mm3": face_area * thickness}


def source_to_local(
    point_global: list[float], transform: list[list[float]]
) -> tuple[float, float, float]:
    if len(point_global) != 3 or len(transform) != 4 or any(len(row) != 4 for row in transform):
        raise ValueError("expected a 3D point and 4x4 source transform")
    delta = [point_global[i] - transform[i][3] for i in range(3)]
    # The first three columns are the authenticated local X/T/N unit axes.
    return tuple(
        math.fsum(transform[i][j] * delta[i] for i in range(3))
        for j in range(3)
    )


def _validate_frame(frame: dict[str, Any]) -> None:
    transform = frame["local_to_global_transform"]
    axes = frame["axes_global_xyz"]
    columns = {
        name: tuple(transform[row][column] for row in range(3))
        for column, name in enumerate(("X", "T", "N"))
    }
    for name, vector in columns.items():
        if not all(_close(columns[name][i], axes[name][i], atol=1e-12) for i in range(3)):
            raise ValueError(f"{name} basis differs between transform and frame map")
        if not _close(math.sqrt(math.fsum(value * value for value in vector)), 1.0, atol=1e-12):
            raise ValueError(f"{name} basis is not unit length")
    for left, right in (("X", "T"), ("T", "N"), ("N", "X")):
        if abs(math.fsum(columns[left][i] * columns[right][i] for i in range(3))) > 1e-12:
            raise ValueError(f"{left}/{right} axes are not orthogonal")
    x, t, n = columns["X"], columns["T"], columns["N"]
    cross = (
        x[1] * t[2] - x[2] * t[1],
        x[2] * t[0] - x[0] * t[2],
        x[0] * t[1] - x[1] * t[0],
    )
    if math.fsum(cross[i] * n[i] for i in range(3)) < 1 - 1e-12:
        raise ValueError("source receiver basis is not right-handed")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def verify_source_pins(root: Path = ROOT) -> dict[str, str]:
    pins = _read_json(PINS)
    if pins.get("schema") != "conditional_washer_crop_mesh_source_pins/v1":
        raise ValueError("unsupported source pin schema")
    result: dict[str, str] = {}
    for relative, expected in pins["sources"].items():
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"pinned source is missing: {relative}")
        actual = sha256_file(path)
        if actual != expected:
            raise ValueError(f"pinned source drift: {relative} ({actual})")
        result[relative] = actual
    return result


def build_record(root: Path = ROOT) -> dict[str, Any]:
    sources = verify_source_pins(root)
    pins = _read_json(PINS)
    profile_path = root / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional-nut-profile.json"
    contract_path = root / "docs/wood-joints-mvp/hypotheses/current-washer-conditional-3d-contract-2026-10-01/README.md"
    crosscheck_path = root / "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/washer-contract-parent-source-crosscheck.json"
    frame_path = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
    solids_path = root / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json"
    profile = _read_json(profile_path)
    crosscheck = _read_json(crosscheck_path)
    frame_map = _read_json(frame_path)
    solids = _read_json(solids_path)
    contract = contract_path.read_text()
    external_oracle = pins["external_oracle_receipt"]
    oracle_path = Path(external_oracle["path"])
    if not oracle_path.is_file() or sha256_file(oracle_path) != external_oracle["sha256"]:
        raise ValueError("pinned independent hardware geometry-oracle receipt is missing or changed")
    oracle_record = _read_json(oracle_path)
    if oracle_record.get("profile_sha256") != sources[
        "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional-nut-profile.json"
    ] or oracle_record.get("source_sha256") != sources[
        "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional_hardware_geometry_oracle.py"
    ]:
        raise ValueError("external numerical oracle does not bind the pinned profile/producer")

    if profile.get("schema") != "parent_conditional_washer_nut_profile/v1":
        raise ValueError("unsupported conditional nut profile")
    for key in ("reviewed_frame_geometry_changed", "physical_work_authorized", "native_execution_authorized", "actual_product_profile_established", "material_resistance_established"):
        if profile.get(key) is not False:
            raise ValueError(f"nut profile exceeds its conditional scope: {key}")
    if crosscheck.get("candidate_capacity_or_acceptance") is not False or crosscheck.get("CAD_runs") != 0 or crosscheck.get("native_runs") != 0:
        raise ValueError("source crosscheck exceeds its source-only scope")
    if crosscheck.get("scope") != "parent source-only washer-contract demand/frame crosscheck":
        raise ValueError("unexpected source crosscheck scope")

    member = next(row for row in frame_map["members"] if row.get("member_id") == "base_principal_center_right")
    if member["current_geometry_lineage"]["step_sha256"] != sources[
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_right.step"
    ]:
        raise ValueError("receiver map and exact STEP bytes differ")
    if member["current_geometry_lineage"]["step_file"] not in sources:
        raise ValueError("receiver STEP path is not pinned")
    if member["current_geometry_lineage"]["step_file"] != "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle/members/base_principal_center_right.step":
        raise ValueError("receiver STEP path changed")
    if member["current_geometry_lineage"]["step_roundtrip_summary"]["solid_count"] != 1 or member["current_geometry_lineage"]["step_roundtrip_summary"]["valid"] is not True:
        raise ValueError("receiver source STEP is not one valid solid")

    frame = crosscheck["receiver_frame"]
    _validate_frame(frame)
    if frame["local_to_global_transform"] != member["source_frame"]["local_to_global_transform"]:
        raise ValueError("source crosscheck and member frame map differ")
    if crosscheck["receiver_map_sha256"] != sources[
        "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json"
    ]:
        raise ValueError("source crosscheck does not bind the pinned receiver map")

    rows = crosscheck["full_load_cases"]["k12-rear"]["source_rows"]
    by_axis = {row["axis_id"]: row for row in rows}
    axis_ids = ("center_principal_right_2", "center_principal_right_1")
    if set(by_axis) != set(axis_ids):
        raise ValueError("K12 crosscheck does not contain exactly the target and companion nut seats")
    local_seats: dict[str, tuple[float, float, float]] = {}
    for axis_id in axis_ids:
        row = by_axis[axis_id]
        if row["receiver"] != "base_principal_center_right" or row["seat_role"] != "nut" or row["case_id"] != "k12-rear" or row["increment_index"] != 6 or row["load_factor"] != 1.0:
            raise ValueError(f"{axis_id}: unexpected signed source row")
        vector = row["physical_action_xyz_N"]
        force = row["signed_inward_action_N"]
        if not _close(vector[0], force, atol=1e-9) or max(abs(vector[1]), abs(vector[2])) > 1e-9 or force <= 0:
            raise ValueError(f"{axis_id}: signed action is not inward receiver-local +X")
        local_seats[axis_id] = source_to_local(row["point_xyz_mm"], frame["local_to_global_transform"])
        if not _close(local_seats[axis_id][0], 0.0, atol=1e-9):
            raise ValueError(f"{axis_id}: seat is not on the X=0 receiver face")
    target = local_seats["center_principal_right_2"]
    neighbor = local_seats["center_principal_right_1"]
    separation = math.dist(target[1:], neighbor[1:])
    if not _close(separation, 53.0, atol=1e-8):
        raise ValueError("authenticated nut seats are not 53 mm apart")
    if not (_close(target[1], 37.57576013, atol=2e-8) and _close(target[2], 95.25, atol=2e-8)):
        raise ValueError("target source seat differs from the conditional contract")
    if not (_close(neighbor[1], -15.42423987, atol=2e-8) and _close(neighbor[2], 95.25, atol=2e-8)):
        raise ValueError("companion source seat differs from the source crosscheck")

    washer = profile["washer"] if "washer" in profile else None
    # Washer dimensions are pinned by the draft contract and catalog record;
    # this profile file intentionally owns nut geometry only.
    dimensions = (18.653125, 7.9248, 1.5875)
    contract_needles = ("47/64 in", "18.653125 mm", "18.6436 mm", "K12 rear")
    if any(needle not in contract for needle in contract_needles):
        raise ValueError("draft contract no longer carries its exact washer/scenario distinction")
    washer_result = washer_metrics(*dimensions)
    if washer is not None:
        raise ValueError("nut profile unexpectedly overrides washer geometry")
    metrics = {name: nut_profile_metrics(profile, name) for name in ("H1", "H2")}
    comparisons = {
        "H1_nut_volume_mm3": metrics["H1"]["volume_mm3"],
        "H2_nut_volume_mm3": metrics["H2"]["volume_mm3"],
        "nut_outward_face_area_mm2": metrics["H1"]["outward_face_area_mm2"],
        "H1_initial_land_area_mm2": metrics["H1"]["initial_land_area_mm2"],
        "washer_volume_mm3": washer_result["volume_mm3"],
        "washer_annular_face_area_mm2": washer_result["face_area_mm2"],
    }
    if any(not _close(comparisons[key], value, atol=1e-9) for key, value in EXPECTED_ORACLE.items()):
        raise ValueError("independent conditional hardware arithmetic differs from pinned external receipt")

    radius = float(profile["silhouette"]["coaxial_corner_clip_diameter"]) / 2
    washer_radius = dimensions[0] / 2
    if math.dist(target[1:], neighbor[1:]) + washer_radius > 75 or radius > 75:
        raise ValueError("one of the two washer/nut footprints falls outside the R75 crop")
    if not all(needle in contract for needle in ("38.1 mm X thickness", "source `X/T/N` frame", "radius 75 mm")):
        raise ValueError("draft contract no longer binds the declared crop/source frame")

    body_names = [
        "receiver_base_principal_center_right_R75_crop",
        "washer_center_principal_right_2",
        "nut_H1_center_principal_right_2",
        "washer_center_principal_right_1",
        "nut_H1_center_principal_right_1",
    ]
    tool_paths = (HERE / "prepare.py", HERE / "mesh_oracles.py", HERE / "produce_mesh.py")
    if any(not path.is_file() for path in tool_paths):
        raise FileNotFoundError("source-only producer and independent mesh-oracle modules must be present")
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "SOURCE_PREPARATION_COMPLETE_NO_FREEZE_NO_GEOMETRY_NO_MESH_NO_SOLVER",
        "candidate": "compact-floor-flush-wood-joints-development",
        "geometry_revision_id": "led-clearance-2x6-runner-seated-blocks-v1",
        "branch": "R75_H1_R_T_A_K12_catalog_nominal_frictionless_mesh_only",
        "source_pins_sha256": sha256_file(PINS),
        "sources": sources,
        "source_preparation_code_sha256": {
            path.name: sha256_file(path) for path in tool_paths
        },
        "runtime_receipt": pins["historical_runtime"],
        "external_geometry_oracle_receipt": pins["external_oracle_receipt"],
        "receiver": {
            "member_id": "base_principal_center_right",
            "step_sha256": sources[member["current_geometry_lineage"]["step_file"]],
            "source_solid_summary": {
                "finished_volume_mm3": member["current_geometry_lineage"]["finished_volume_mm3"],
                "roundtrip_volume_mm3": member["current_geometry_lineage"]["step_roundtrip_summary"]["volume_mm3"],
                "centroid_global_xyz_mm": member["current_geometry_lineage"]["step_roundtrip_summary"]["center_xyz_mm"],
                "bounds_global_xyz_mm": member["current_geometry_lineage"]["step_roundtrip_summary"]["bounds_xyz_mm"],
                "source_face_count": member["current_geometry_lineage"]["step_roundtrip_summary"]["face_count"],
                "surface_area_by_type_mm2": member["current_geometry_lineage"]["step_roundtrip_summary"]["surface_area_by_type_mm2"],
                "step_roundtrip_valid_one_solid": True,
            },
            "source_frame": frame,
            "local_seat_centers_X_T_N_mm": {key: list(value) for key, value in local_seats.items()},
            "washer_nut_seat_separation_mm": separation,
            "crop": {
                "shape": "exact source BREP common with finite X-directed cylinder",
                "source_X_interval_mm": [0.0, 38.1],
                "center_axis": "center_principal_right_2 receiver-local T/N center; axis source +X",
                "radius_mm": 75.0,
                "natural_cuts": "preserve all exact source cuts intersecting the crop",
            },
        },
        "stack_loads": {
            key: {
                "load_case": "k12-rear",
                "signed_inward_resultant_N": by_axis[key]["signed_inward_action_N"],
                "direction_receiver_local": [1.0, 0.0, 0.0],
                "source_global_point_xyz_mm": by_axis[key]["point_xyz_mm"],
            }
            for key in axis_ids
        },
        "hardware": {
            "washer": {
                "od_id_thickness_mm": list(dimensions),
                "prior_cad_envelope_od_reference_mm": 18.6436,
                "volume_mm3_each": washer_result["volume_mm3"],
                "annular_face_area_mm2_each": washer_result["face_area_mm2"],
                "reintersect_with_exact_brep": True,
                "old_support_fraction_transfer": False,
            },
            "nut_profile": {key: value for key, value in metrics.items()},
            "nut_geometry_source_sha256": sources[
                "docs/wood-joints-mvp/hypotheses/mvp-integration-2026-10-01/conditional-nut-profile.json"
            ],
        },
        "mesh_plan": {
            "exact_independent_body_ids": body_names,
            "body_count": 5,
            "element": "quadratic C3D10; Gmsh order 2 with audited node reorder",
            "nominal_elements_through_washer_thickness": 2,
            "maximum_local_edge_mm": 0.8,
            "local_refinement_regions": ["both washer contact rims", "both receiver bolt bores", "F1/G1 service passage edge"],
            "global_max_size_mm": 40.0,
            "local_refinement_band_mm": 12.0,
            "one_launch_limit": 1,
            "retry_budget": 0,
            "timeout_seconds": 300,
            "cpus": 2,
            "memory_bytes": 4294967296,
            "scratch_bytes": 536870912,
            "network": "none",
            "input_mount_read_only": True,
            "output": "new isolated directory; refuse if existing, symlinked, or within input tree",
            "cards_prohibited": ["material", "contact", "tie", "load", "restraint", "preload", "solver"],
        },
        "required_oracles": [
            "exact source/hash/receiver-frame binding and source-face analytic signatures",
            "OCC crop ancestry: natural source faces versus R75-generated faces",
            "one valid connected solid per exact body identity; disjoint node/element ownership",
            "source BREP and crop volume/centroid/bounds; analytic washer/nut volumes and load-face area",
            "all C3D10 faces reconciled exactly once with TRI6 exterior faces",
            "positive sampled and Gmsh Gauss5 C3D10 Jacobians; mesh volume error <=0.1%",
            "actual nut outward-face TRI6 force/moment integration: <=0.02 N and <=0.05 N mm",
            "achieved two-layer washer thickness resolution and local edge bounds",
            "mesh-only deck contains no material/contact/tie/load/restraint/preload/solver cards",
        ],
        "limits": [
            "No actual CAD or geometry was built by this preparation script.",
            "No mesh, solver input freeze, mechanics result, acceptance, or physical claim was created.",
            "The historical runtime receipt is not current runtime verification.",
            "A future parent freeze and preflight are required before one mesh launch.",
        ],
    }
    record["record_sha256"] = sha256_bytes(
        json.dumps(record, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="optional new JSON record inside this owned directory")
    args = parser.parse_args()
    record = build_record()
    payload = json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output is None:
        print(payload, end="")
        return
    requested = args.output if args.output.is_absolute() else HERE / args.output
    requested = Path(os.path.abspath(requested))
    if not requested.is_relative_to(HERE) or requested == HERE or requested.exists() or requested.is_symlink():
        raise FileExistsError("source-preparation output must be a new file inside this owned directory")
    target = requested.resolve(strict=False)
    if not target.is_relative_to(HERE) or target.exists() or target.is_symlink():
        raise FileExistsError("resolved source-preparation output is not a new owned file")
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(payload)


if __name__ == "__main__":
    main()
