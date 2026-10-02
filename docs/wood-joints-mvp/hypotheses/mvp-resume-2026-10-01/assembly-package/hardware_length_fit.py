#!/usr/bin/env python3
"""Prepare and run the bounded 12-bolt nominal-length fit screen.

Importing this module and ``--prepare`` use only the Python standard library.
The parent-only ``run`` imports CadQuery only for overlapping saved boxes with
matching STEP geometry. It never composes or rebuilds the source scene.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import struct
import time
from pathlib import Path
from typing import Any


def _repository_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / "mini_moonboard").is_dir():
            return parent
    raise RuntimeError("cannot locate mini-moonboard repository root")


ROOT = _repository_root()
PACKAGE = Path(__file__).resolve().parent
RESUME = PACKAGE.parent
RAW_DEFAULT = PACKAGE / "rawlocal" / "hardware-length-fit"
GEOMETRY_SNAPSHOT = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json"
MEMBER_BUNDLE = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/bundle"
MEMBER_MANIFEST = MEMBER_BUNDLE / "current-full-frame-member-solids.json"

MODEL_PATH = RESUME / "corner-frame-attempt01/model.json"
PROPOSAL_PATH = RESUME / "top-corner-correction/proposal.json"
BODY_CSV = PACKAGE / "rawlocal/bodies.csv"
AXIS_CSV = PACKAGE / "rawlocal/hardware-axes.csv"
FAMILY_CSV = PACKAGE / "rawlocal/hardware-families.csv"
ENGAGEMENT_CSV = PACKAGE / "rawlocal/hardware-engagement/hardware-engagement-axes.csv"
RECONCILED_JSON = PACKAGE / "rawlocal/reconciled-assembly.json"
TOP_HARDWARE_INPUTS = RESUME / "top-corner-hardware/hardware-inputs.json"

TARGET_IDS = tuple(
    [f"center_post_{side}_{index}" for side in ("left", "right") for index in (1, 2)]
    + [f"center_principal_header_{side}_{index}" for side in ("left", "right") for index in (1, 2)]
    + [f"knee_outer_{side}_inner_header_{index}" for side in ("left", "right") for index in (1, 2)]
)
EXPECTED_BODY_COUNT = 50
EXPECTED_TOP_OVERRIDES = {
    "top_outer_left_cleat",
    "top_outer_right_cleat",
    "base_side_left",
    "base_side_right",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"expected a JSON object: {path}")
    return data


def _read_csv(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        value = row.get(key, "")
        if not value or value in result:
            raise ValueError(f"{path}: {key} values must be unique and nonempty")
        result[value] = row
    return result


def _vec3(values: Any, label: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{label} must be a finite 3-vector")
    length = math.sqrt(sum(value * value for value in result))
    if length <= 1e-12:
        raise ValueError(f"{label} must be nonzero")
    return tuple(value / length for value in result)


def _add_scaled(
    point: tuple[float, float, float], direction: tuple[float, float, float], amount: float
) -> list[float]:
    return [point[i] + direction[i] * amount for i in range(3)]


def build_setup() -> dict[str, Any]:
    """Read source metadata and prepare source-pinned axes/member paths only."""
    model = _load_json(MODEL_PATH)
    proposal = _load_json(PROPOSAL_PATH)
    snapshot = _load_json(GEOMETRY_SNAPSHOT)
    member_manifest = _load_json(MEMBER_MANIFEST)
    assembly = _load_json(RECONCILED_JSON)
    bodies = _read_csv(BODY_CSV, "body_id")
    axes = _read_csv(AXIS_CSV, "axis_id")
    families = _read_csv(FAMILY_CSV, "reconciled_family_id")
    engagement = _read_csv(ENGAGEMENT_CSV, "axis_id")

    if model.get("source_revision") != snapshot.get("revision_id"):
        raise ValueError("corner model and saved geometry snapshot revisions differ")
    if model.get("physical_release") is not False or proposal.get("physical_release") is not False:
        raise ValueError("this producer requires unreleased source geometry")
    if len(model.get("body_names", ())) != EXPECTED_BODY_COUNT:
        raise ValueError("corner model does not bind exactly 50 bodies")
    if len(bodies) != EXPECTED_BODY_COUNT or len(member_manifest.get("members", ())) != EXPECTED_BODY_COUNT:
        raise ValueError("the frozen assembly/member bundle must contain exactly 50 bodies")
    expected_bodies = set(model["body_names"])
    if set(bodies) != expected_bodies:
        raise ValueError("assembly body census differs from corner-frame model")
    member_rows = {row["member_id"]: row for row in member_manifest["members"]}
    if set(member_rows) != expected_bodies:
        raise ValueError("STEP member manifest differs from the 50-body census")
    assembly_body_ids = {row["body_id"] for row in assembly.get("bodies", ())}
    if assembly_body_ids != expected_bodies:
        raise ValueError("reconciled assembly JSON differs from the 50-body census")

    declared_overrides = proposal.get("proposal_step_sha256")
    if not isinstance(declared_overrides, dict):
        raise TypeError("top-corner proposal lacks its STEP override map")
    override_ids: dict[str, str] = {}
    for relative, digest in declared_overrides.items():
        body_id = Path(relative).stem
        if body_id in override_ids or body_id not in expected_bodies:
            raise ValueError("top-corner override IDs must be unique current bodies")
        override_ids[body_id] = relative
        if _sha256(ROOT / relative) != digest:
            raise ValueError(f"top-corner STEP override hash changed: {relative}")
    if set(override_ids) != EXPECTED_TOP_OVERRIDES:
        raise ValueError("current proposal must replace both cleats and both side hosts")

    member_inputs: list[dict[str, Any]] = []
    input_hashes: dict[str, str] = {}
    for relative in (
        MODEL_PATH.relative_to(ROOT).as_posix(),
        PROPOSAL_PATH.relative_to(ROOT).as_posix(),
        GEOMETRY_SNAPSHOT.relative_to(ROOT).as_posix(),
        MEMBER_MANIFEST.relative_to(ROOT).as_posix(),
        BODY_CSV.relative_to(ROOT).as_posix(),
        AXIS_CSV.relative_to(ROOT).as_posix(),
        FAMILY_CSV.relative_to(ROOT).as_posix(),
        ENGAGEMENT_CSV.relative_to(ROOT).as_posix(),
        RECONCILED_JSON.relative_to(ROOT).as_posix(),
        TOP_HARDWARE_INPUTS.relative_to(ROOT).as_posix(),
        "scripts/wood_joint_current_access_screen.py",
        "scripts/wood_joint_current_retained_access.py",
        "scripts/wood_joint_wj24_tool_operation_probe.py",
        "scripts/wood_joint_wj12_diagnostic.py",
        "scripts/wood_joint_wj04_tool_access.py",
        "scripts/wood_joint_current_geometry.py",
    ):
        path = ROOT / relative
        input_hashes[relative] = _sha256(path)

    for body_id in sorted(expected_bodies):
        member = member_rows[body_id]
        source_relative = member["step_file"]
        if source_relative.startswith("bundle/"):
            source_relative = f"docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-member-solids-attempt01/{source_relative}"
        source_path = ROOT / source_relative
        if _sha256(source_path) != member["step_sha256"]:
            raise ValueError(f"frozen member STEP hash changed: {source_relative}")
        final_relative = override_ids.get(body_id, source_relative)
        final_path = ROOT / final_relative
        final_hash = _sha256(final_path)
        body_shape_scope = bodies[body_id]["shape_source_scope"]
        if "uncut source shape/extents" not in body_shape_scope and final_hash != bodies[body_id]["shape_source_sha256"]:
            raise ValueError(f"assembly STEP binding changed for {body_id}")
        if body_id not in override_ids and final_hash != member["step_sha256"]:
            raise ValueError(f"unmodified member STEP differs from bundle manifest: {body_id}")
        if body_id in override_ids and proposal["proposal_step_sha256"][final_relative] != final_hash:
            raise ValueError(f"proposal STEP binding changed for {body_id}")
        input_hashes[final_relative] = final_hash
        member_inputs.append(
            {
                "body_id": body_id,
                "step_path": final_relative,
                "step_sha256": final_hash,
                "replaces_bundle_step": body_id in override_ids,
                "bundle_step_sha256": member["step_sha256"],
                "assembly_shape_source_sha256": bodies[body_id]["shape_source_sha256"],
                "assembly_shape_source_scope": body_shape_scope,
                "expected_bounds_xyz_mm": member["step_roundtrip_summary"]["bounds_xyz_mm"],
                "expected_volume_mm3": member["step_roundtrip_summary"]["volume_mm3"] if body_id not in override_ids else None,
                "replacement_summary_source": "top-corner proposal STEP; validate exact imported solid at run time" if body_id in override_ids else "frozen full-frame member bundle",
            }
        )

    target_rows: list[dict[str, Any]] = []
    snapshot_axes = snapshot.get("axes", {})
    for axis_id in TARGET_IDS:
        if axis_id not in axes or axis_id not in engagement or axis_id not in snapshot_axes:
            raise ValueError(f"required saved target axis is missing: {axis_id}")
        engagement_row = engagement[axis_id]
        saved_axis = snapshot_axes[axis_id]
        model_length = float(engagement_row["model_underhead_length_mm"])
        nominal_length = float(engagement_row["proposed_nominal_order_length_mm"])
        diameter = float(engagement_row["diameter_mm"])
        head_to_nut = _vec3(saved_axis["axis_head_to_nut_global"], f"{axis_id} direction")
        center = tuple(float(value) for value in saved_axis["shaft_center_xyz_mm"])
        bounds = saved_axis["hardware"]["shaft"]
        low_xyz = tuple(float(value) for value in bounds["min_xyz_mm"])
        high_xyz = tuple(float(value) for value in bounds["max_xyz_mm"])
        projections = [
            sum((corner[i] - center[i]) * head_to_nut[i] for i in range(3))
            for corner in (
                (x, y, z)
                for x in (low_xyz[0], high_xyz[0])
                for y in (low_xyz[1], high_xyz[1])
                for z in (low_xyz[2], high_xyz[2])
            )
        ]
        shaft_low, shaft_high = min(projections), max(projections)
        saved_length = shaft_high - shaft_low
        if abs(round(model_length, 3) - model_length) > 1e-9 or abs(saved_length - model_length) > 0.00051:
            raise ValueError(f"{axis_id}: saved shaft extent does not bind rounded model length")
        if abs(diameter - float(saved_axis["shaft_diameter_mm"])) > 1e-6:
            raise ValueError(f"{axis_id}: saved shaft diameter differs from engagement census")
        expected = 203.2 if "header" in axis_id else (152.4 if axis_id.startswith("center_post_") else 203.2)
        if abs(nominal_length - expected) > 1e-9 or nominal_length <= saved_length:
            raise ValueError(f"{axis_id}: proposed nominal length is outside the authorized set")
        receivers = json.loads(engagement_row["ordered_members_head_to_nut"])
        if tuple(receivers) != tuple(saved_axis["receiver_ids"]):
            raise ValueError(f"{axis_id}: saved receiver order differs between inventories")
        start = _add_scaled(center, head_to_nut, shaft_low)
        old_end = _add_scaled(center, head_to_nut, shaft_high)
        proposed_end = _add_scaled(center, head_to_nut, shaft_low + nominal_length)
        target_rows.append(
            {
                "axis_id": axis_id,
                "family_id": engagement_row["family_id"],
                "members_head_to_nut": receivers,
                "shaft_diameter_mm": diameter,
                "head_to_nut_axis_xyz": list(head_to_nut),
                "headward_axis_xyz": [-value for value in head_to_nut],
                "saved_shaft_center_xyz_mm": list(center),
                "recorded_model_underhead_length_mm": model_length,
                "saved_shaft_envelope_length_mm": round(saved_length, 9),
                "proposed_nominal_length_mm": nominal_length,
                "extension_from_saved_shaft_envelope_mm": round(nominal_length - saved_length, 9),
                "extension_from_recorded_model_length_mm": round(nominal_length - model_length, 9),
                "saved_headward_endpoint_xyz_mm": start,
                "saved_nutward_endpoint_xyz_mm": old_end,
                "proposed_nutward_endpoint_xyz_mm": proposed_end,
                "endpoint_basis": "saved shaft BBox projected on source head-to-nut axis; proposed cylinder keeps the saved headward endpoint",
                "raw_family_census": {
                    "family_name": engagement_row["family_name"],
                    "family_model_length_mm": float(families[engagement_row["family_id"]]["model_length_mm"]),
                    "wood_grip_mm": float(engagement_row["wood_grip_mm"]),
                },
            }
        )

    if len(target_rows) != 12 or len({row["axis_id"] for row in target_rows}) != 12:
        raise ValueError("exactly 12 unique target axes are required")
    for row in target_rows:
        family_length = row["raw_family_census"]["family_model_length_mm"]
        if abs(family_length - row["recorded_model_underhead_length_mm"]) > 1e-9:
            raise ValueError(f"{row['axis_id']}: family model length disagrees with axis input")

    top_axes: dict[str, Any] = {}
    for proposal_row in proposal.get("proposals", ()):
        for axis in proposal_row.get("axes", ()):
            axis_id = axis["axis_id"]
            if axis_id in top_axes:
                raise ValueError(f"top proposal axis repeated: {axis_id}")
            census = axes.get(axis_id)
            if census is None:
                raise ValueError(f"top proposal axis missing from assembly census: {axis_id}")
            family = families[census["family_id"]]
            top_axes[axis_id] = {
                "old_axis_point_mm": axis["old_axis_point_mm"],
                "proposed_axis_point_mm": axis["proposed_axis_point_mm"],
                "nominal_bolt_diameter_mm": axis["nominal_bolt_diameter_mm"],
                "family_id": census["family_id"],
                "proposed_underhead_length_mm": float(family["model_length_mm"]),
                "proposed_wood_grip_mm": axis["wood_grip_mm"],
            }
    if len(top_axes) != 8:
        raise ValueError("top-corner proposal must bind its eight updated axes")

    return {
        "schema": "hardware_length_fit_setup/v1",
        "status": "prepared_only_waiting_for_parent_geometry_slot",
        "candidate": model["candidate"],
        "source_revision": model["source_revision"],
        "corner_model_development_revision": model["development_revision"],
        "geometry_snapshot_revision": snapshot["revision_id"],
        "method": "prepare saved axis lengths/endpoints and exact STEP source map; no CAD/OCP imported or run",
        "source_sha256": dict(sorted(input_hashes.items())),
        "source_files": {
            "corner_model": MODEL_PATH.relative_to(ROOT).as_posix(),
            "top_corner_proposal": PROPOSAL_PATH.relative_to(ROOT).as_posix(),
            "geometry_snapshot": GEOMETRY_SNAPSHOT.relative_to(ROOT).as_posix(),
            "assembly_raw": [path.relative_to(ROOT).as_posix() for path in (BODY_CSV, AXIS_CSV, FAMILY_CSV, ENGAGEMENT_CSV, RECONCILED_JSON)],
            "member_bundle_manifest": MEMBER_MANIFEST.relative_to(ROOT).as_posix(),
            "corrected_step_override_ids": sorted(EXPECTED_TOP_OVERRIDES),
        },
        "target_axes": target_rows,
        "top_corner_axes_for_separation_certificate": dict(sorted(top_axes.items())),
        "current_member_step_map": member_inputs,
        "expected_counts": {"current_member_bodies": 50, "target_extended_axes": 12, "top_corner_changed_axes": 8},
        "run_command": "uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/hardware_length_fit.py --run --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-length-fit",
        "cad_run_executed": False,
        "geometry_fit_or_physical_access_established": False,
    }


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == encoded:
            return
        raise FileExistsError(f"refusing to replace existing raw output: {path}")
    path.write_text(encoded, encoding="utf-8")


def _resolved_output_dir(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _box_gap(first: list[float], second: list[float]) -> float:
    gaps = [
        max(0.0, first[2 * index] - second[2 * index + 1],
            second[2 * index] - first[2 * index + 1])
        for index in range(3)
    ]
    return math.sqrt(sum(gap * gap for gap in gaps))


def _inflate(bounds: list[float], allowance: float = 0.001) -> list[float]:
    return [value + (-allowance if index % 2 == 0 else allowance)
            for index, value in enumerate(bounds)]


def _cylinder_bounds(start: list[float], end: list[float], direction: list[float], radius: float) -> list[float]:
    return [value for index in range(3)
            for value in (min(start[index], end[index]) - radius * math.sqrt(max(0.0, 1 - direction[index]**2)),
                          max(start[index], end[index]) + radius * math.sqrt(max(0.0, 1 - direction[index]**2)))]


def _source_box(record: dict[str, Any]) -> list[float]:
    return [value for index in range(3)
            for value in (record["min_xyz_mm"][index], record["max_xyz_mm"][index])]


def _mesh_box(path: Path, dimensions: list[float], translation: list[float]) -> list[float]:
    """Enclose source CAD using saved global extents and STL surface vertices.

    For each axis, CAD min >= mesh max - CAD extent and CAD max <= mesh min
    + CAD extent. Union with mesh bounds and 0.001 mm coordinate allowance
    accounts for exported float32 rounding. This is a conservative box, not a
    mesh-to-CAD qualification or a new reconstructed solid.
    """
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    if len(data) != 84 + 50 * count or count == 0:
        raise ValueError(f"expected nonempty binary STL: {path}")
    low, high = [math.inf] * 3, [-math.inf] * 3
    for triangle in struct.iter_unpack("<12fH", data[84:]):
        for offset in (3, 6, 9):
            for index in range(3):
                coordinate = triangle[offset + index]
                low[index] = min(low[index], coordinate)
                high[index] = max(high[index], coordinate)
    return _inflate([value + translation[index] for index in range(3)
                     for value in (min(low[index], high[index] - dimensions[index]),
                                   max(high[index], low[index] + dimensions[index]))])


def saved_inventory(setup: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read saved bounds/STEP/mesh references only; do not import CAD."""
    scene_path = ROOT / "site/owner-wood-joints-wj24-scene.json"
    snapshot = _load_json(GEOMETRY_SNAPSHOT)
    access_path = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/access-screen-attempt03-exact-components.json"
    access = _load_json(access_path)
    operations = {row["axis_id"]: row for row in access["axis_operations"]}
    scene = _load_json(scene_path)
    inventory_path = ROOT / "docs/wood-joints-mvp/source-inventory.json"
    inventory = _load_json(inventory_path)
    d6_dir = ROOT / "docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export"
    d6_manifest = _load_json(d6_dir / "manifest.json")
    manifest_path = ROOT / "site" / scene["baseline_manifest_path"].removeprefix("site/")
    baseline = _load_json(manifest_path)
    for path in (scene_path, access_path, inventory_path, d6_dir / "manifest.json", manifest_path):
        setup["source_sha256"][path.relative_to(ROOT).as_posix()] = _sha256(path)
    bodies = {row["member_id"]: row for row in _load_json(MEMBER_MANIFEST)["members"]}
    obstacles = []
    for member in setup["current_member_step_map"]:
        body_id = member["body_id"]
        bounds = list(bodies[body_id]["step_roundtrip_summary"]["bounds_xyz_mm"])
        if body_id.startswith("top_outer_"):
            # The frozen correction adds 50.8 mm to the section with 25.4 mm
            # center shift. Uniform +/-50.8 mm encloses either global projection.
            bounds = _inflate(bounds, 50.8)
        obstacles.append({"id": f"wood/{body_id}", "category": "wood", "bounds_xyz_mm": _inflate(bounds),
                          "step_path": member["step_path"], "axis_id": None})
    targets = {row["axis_id"]: row for row in setup["target_axes"]}
    top_ids = set(setup["top_corner_axes_for_separation_certificate"])
    for axis_id, axis in snapshot["axes"].items():
        if axis_id in top_ids:
            continue
        for role, shape in axis["hardware"].items():
            bounds = _source_box(shape)
            if role == "shaft" and axis_id in targets:
                row = targets[axis_id]
                bounds = _cylinder_bounds(row["saved_headward_endpoint_xyz_mm"], row["proposed_nutward_endpoint_xyz_mm"],
                                          row["head_to_nut_axis_xyz"], row["shaft_diameter_mm"] / 2)
            obstacles.append({"id": f"candidate_stack/{axis_id}/{role}", "category": "candidate_hardware",
                              "bounds_xyz_mm": _inflate(bounds), "axis_id": axis_id,
                              "geometry_limit": "saved role bounds; no exact STEP supplied for this component"})
    for axis_id, row in setup["top_corner_axes_for_separation_certificate"].items():
        # The point is a frozen bore datum in the 177.8 mm grip. This remote box
        # allows twice the complete nominal length in either direction, plus
        # 25.4 mm for recorded head/nut/washer envelopes; not delivered parts.
        extent = 2 * row["proposed_underhead_length_mm"] + 25.4
        bounds = [value for point in row["proposed_axis_point_mm"] for value in (point - extent, point + extent)]
        obstacles.append({"id": f"corrected_top_stack/{axis_id}", "category": "corrected_top_stack",
                          "axis_id": axis_id, "bounds_xyz_mm": _inflate(bounds),
                          "geometry_limit": "conservative nominal corrected stack enclosure; exact product geometry unavailable"})
    for row in d6_manifest["files"]:
        if row["category"] not in {"retained_frame_bolt_roles", "modeled_wires"}:
            continue
        path = d6_dir / row["path"]
        if _sha256(path) != row["sha256"]:
            raise ValueError(f"retained/wire STEP changed: {path}")
        setup["source_sha256"][path.relative_to(ROOT).as_posix()] = row["sha256"]
        obstacles.append({"id": f"{row['category']}/{row['shape_id']}", "category": row["category"],
                          "bounds_xyz_mm": _inflate(row["bounds_xyz_mm"]),
                          "step_path": path.relative_to(ROOT).as_posix(), "axis_id": None})
    moved = {row["axis_id"]: row for row in snapshot["panel_screws"]}
    for row in inventory["fixed_panel_kicker_screws"]:
        axis_id = row["axis_id"]
        start = moved.get(axis_id, {}).get("new_start_global_xyz_mm", row["origin_global_xyz_mm"])
        direction = list(_vec3(row["axis_global_xyz"], axis_id))
        end = _add_scaled(tuple(start), tuple(direction), 63.5)
        obstacles.append({"id": f"panel_screw/{axis_id}", "category": "panel_screw_envelope",
                          "axis_id": None, "bounds_xyz_mm": _inflate(_cylinder_bounds(start, end, direction, 4.1402 / 2)),
                          "geometry_limit": "recorded 63.5 mm occupied screw cylinder; no exact STEP supplied"})
    hidden = set(scene["hidden_baseline_visual_names"])
    for row in baseline["parts"]:
        name = row["name"]
        if name in hidden or not name.startswith(("hold_tnut_", "light_")):
            continue
        path = ROOT / "site" / row["path"]
        expected = scene["baseline_asset_sha256"][row["path"]]
        if _sha256(path) != expected:
            raise ValueError(f"baseline physical mesh changed: {path}")
        setup["source_sha256"][path.relative_to(ROOT).as_posix()] = expected
        obstacles.append({"id": name, "category": "tnuts" if name.startswith("hold_tnut_") else "lights",
                          "axis_id": None, "mesh_path": path.relative_to(ROOT).as_posix(),
                          "bounds_xyz_mm": _mesh_box(path, row["viewer_aabb_mm"], scene["baseline_display_translations_mm"].get(name, [0, 0, 0])),
                          "geometry_limit": "saved STL/global CAD extent enclosure; no exact STEP supplied"})
    for row in scene["solids"]:
        if row.get("display_class") == "electrical_replacement" and row["id"].startswith("light_"):
            obstacles.append({"id": row["id"], "category": "lights", "axis_id": None,
                              "bounds_xyz_mm": _inflate(row["mesh"]["bounds_xyz_mm"], row["mesh"].get("vertex_max_euclidean_error_mm", 0.1)),
                              "geometry_limit": "saved electrical replacement mesh/source bounds; no exact STEP supplied"})
    if len({row["id"] for row in obstacles}) != len(obstacles):
        raise ValueError("saved obstacle IDs are not unique")
    counts = {category: sum(row["category"] == category for row in obstacles)
              for category in {row["category"] for row in obstacles}}
    expected = {"wood": 50, "candidate_hardware": 420, "corrected_top_stack": 8,
                "retained_frame_bolt_roles": 60, "modeled_wires": 131,
                "panel_screw_envelope": 66, "tnuts": 142, "lights": 132}
    if counts != expected:
        raise ValueError(f"saved installed scene census differs: {counts}")
    queries = []
    for row in setup["target_axes"]:
        axis_id = row["axis_id"]
        direction = row["head_to_nut_axis_xyz"]
        extra = row["extension_from_saved_shaft_envelope_mm"]
        old_travel = operations[axis_id]["operations"]["head_side_bolt"]["derived_travel_mm"]
        row["source_headward_travel_mm"] = old_travel
        row["proposed_headward_travel_mm"] = old_travel + extra
        row["headward_travel_increment_mm"] = extra
        old_head = _add_scaled(tuple(row["saved_headward_endpoint_xyz_mm"]), tuple(direction), -old_travel)
        new_head = _add_scaled(tuple(old_head), tuple(direction), -extra)
        for part, start, end in (("tip_extension", row["saved_nutward_endpoint_xyz_mm"], row["proposed_nutward_endpoint_xyz_mm"]),
                                 ("shaft_headward_increment", new_head, old_head)):
            queries.append({"id": f"{axis_id}/{part}", "axis_id": axis_id, "component": part,
                            "bounds_xyz_mm": _inflate(_cylinder_bounds(start, end, direction, row["shaft_diameter_mm"] / 2)),
                            "cylinder": {"start_xyz_mm": start, "direction_xyz": direction,
                                         "length_mm": extra, "radius_mm": row["shaft_diameter_mm"] / 2}})
        for role in ("head", "head_washer"):
            bounds = _source_box(snapshot["axes"][axis_id]["hardware"][role])
            translated = [[bounds[2 * index + edge] - direction[index] * travel
                           for index in range(3) for edge in (0, 1)]
                          for travel in (old_travel, old_travel + extra)]
            union = [min(box[index] for box in translated) if index % 2 == 0 else max(box[index] for box in translated)
                     for index in range(6)]
            queries.append({"id": f"{axis_id}/{role}_headward_increment", "axis_id": axis_id,
                            "component": f"{role}_headward_increment", "bounds_xyz_mm": _inflate(union),
                            "geometry_limit": "source role AABB translated through only the additional headward increment; exact moving role STEP unavailable"})
    setup["source_sha256"] = dict(sorted(setup["source_sha256"].items()))
    setup["obstacle_counts"] = counts
    return obstacles, queries


def prepare(output_dir: str | Path = RAW_DEFAULT) -> Path:
    setup = build_setup()
    obstacles, queries = saved_inventory(setup)
    setup["status"] = "prepared_saved_sources_only_waiting_for_parent_run"
    setup["method"] = "saved AABB inventory and 12 tip/headward increments; no live scene replay or CAD import"
    setup["run_command"] = "uv run --no-sync python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/hardware_length_fit.py --run --output-dir docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/hardware-length-fit/saved-source-attempt01"
    setup["obstacles"] = obstacles
    setup["queries"] = queries
    setup["overlapping_box_pairs"] = [{"query_id": query["id"], "obstacle_id": other["id"]}
                                      for query in queries for other in obstacles
                                      if other["axis_id"] != query["axis_id"] and _box_gap(query["bounds_xyz_mm"], other["bounds_xyz_mm"]) <= 0]
    target = _resolved_output_dir(output_dir) / "setup.json"
    _write_json(target, setup)
    return target


def run(*, output_dir: str | Path = RAW_DEFAULT) -> Path:
    """Parent run: certify separate boxes; use saved STEP only for overlaps."""
    started = time.monotonic()
    setup_path = prepare(output_dir)
    setup = _load_json(setup_path)
    obstacles = setup["obstacles"]
    loaded_steps = {}
    cylinders = {}
    pairs = []
    for query in setup["queries"]:
        for other in obstacles:
            if other["axis_id"] == query["axis_id"]:
                continue
            gap = _box_gap(query["bounds_xyz_mm"], other["bounds_xyz_mm"])
            pair = {"query_id": query["id"], "obstacle_id": other["id"],
                    "AABB_distance_lower_bound_mm": round(gap, 9)}
            if gap > 0:
                pair["status"] = "clear_by_conservative_AABB_separation"
            elif "step_path" in other and "cylinder" in query:
                import cadquery as cq

                if other["id"] not in loaded_steps:
                    loaded_steps[other["id"]] = cq.importers.importStep(str(ROOT / other["step_path"])).val()
                if query["id"] not in cylinders:
                    cylinder = query["cylinder"]
                    cylinders[query["id"]] = cq.Solid.makeCylinder(cylinder["radius_mm"], cylinder["length_mm"],
                                                                  cq.Vector(cylinder["start_xyz_mm"]), cq.Vector(cylinder["direction_xyz"]))
                moving = cylinders[query["id"]]
                fixed = loaded_steps[other["id"]]
                volume = float(moving.intersect(fixed).Volume())
                distance = float(moving.distance(fixed))
                pair.update({"status": "modeled_overlap" if volume > 1e-6 else "clear_by_saved_STEP_intersection",
                             "overlap_volume_mm3": volume, "minimum_distance_mm": distance,
                             "step_path": other["step_path"]})
            else:
                pair.update({"status": "undecided_specific_pair", "reason": query.get("geometry_limit", other.get("geometry_limit")),
                             "existing_mesh_path": other.get("mesh_path")})
            pairs.append(pair)
    changed = [path for path, expected in setup["source_sha256"].items() if _sha256(ROOT / path) != expected]
    if changed:
        raise ValueError(f"source inputs changed during saved-source screen: {changed}")
    result_path = _resolved_output_dir(output_dir) / "result.json"
    _write_json(result_path, {
        "schema": "hardware_length_fit_saved_source_result/v1", "status": "completed_saved_source_pair_screen",
        "producer_sha256": _sha256(Path(__file__)), "setup_sha256": _sha256(setup_path),
        "source_sha256": setup["source_sha256"], "source_unchanged_after_run": True,
        "runtime_seconds": round(time.monotonic() - started, 6),
        "geometry_rebuilt": False, "STEP_obstacles_loaded": len(loaded_steps),
        "obstacle_counts": setup["obstacle_counts"], "target_axes": setup["target_axes"],
        "pair_count": len(pairs), "pairs": pairs,
        "overlap_pairs": [row for row in pairs if row["status"] == "modeled_overlap"],
        "undecided_pairs": [row for row in pairs if row["status"] == "undecided_specific_pair"],
        "limits": ["Only proposed tips and extra headward shaft/head/washer occupancy are screened; source travels are reused.",
                   "Clear boxes certify separation within the recorded nominal geometry, not delivered hardware or physical access.",
                   "Overlapping boxes without matching exact saved STEP geometry remain named undecided pairs.",
                   "Source captured-nut sequences and intact harness stay unchanged; nut/thread turning and full assembly are outside this screen."],
    })
    print(f"completed {result_path}", flush=True)
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="write source-pinned 12-axis setup; stdlib only")
    mode.add_argument("--run", action="store_true", help="run exact CAD intersection screen after parent authorization")
    parser.add_argument("--output-dir", required=True, help="explicit ignored rawlocal output directory")
    args = parser.parse_args(argv)
    if args.prepare:
        path = prepare(args.output_dir)
        print(f"prepared {path}")
        return 0
    run(output_dir=args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
