#!/usr/bin/env python3
"""Prepare and parent-run saved-geometry checks for four upper panel screws."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any


def _root() -> Path:
    for path in Path(__file__).resolve().parents:
        if (path / "pyproject.toml").is_file() and (path / "mini_moonboard").is_dir():
            return path
    raise RuntimeError("cannot locate mini-moonboard repository root")


ROOT = _root()
HERE = Path(__file__).resolve().parent
RESUME = HERE.parent
INPUTS = ROOT / "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-attempt01/model-inputs.json"
CORNER_MODEL = RESUME / "corner-frame-attempt01/model.json"
SOURCE_INVENTORY = ROOT / "docs/wood-joints-mvp/source-inventory.json"
FEATURES = ROOT / "docs/wood-joints-mvp/hypotheses/current-finished-feature-register-2026-10-01/axis-features.json"
TRANSFER_INVENTORY = ROOT / "docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/inventory.py"
HARDWARE_HELPER = RESUME / "assembly-package/hardware_length_fit.py"
EXPECTED_INPUTS_SHA256 = "178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9"
EXPECTED_CORNER_SHA256 = "d17dadd7c999e4a1634f53226cf63e131f547cd9cf5d46d87d75c935f2dc807e"
TARGETS = {
    "round_panel_upper_left_rim_4": "base_side_left",
    "round_panel_upper_right_rim_4": "base_side_right",
    "round_panel_upper_left_center_4": "base_rail_top",
    "round_panel_upper_right_center_4": "base_rail_top",
}
MOVE_MM = 65.95
TOP_ROW_T_MM = 2619.974134
T_AXIS = (0.0, math.cos(math.radians(50.0)), math.sin(math.radians(50.0)))
RAW_DEFAULT = HERE / "rawlocal/attempt01"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def _vec(value: Any, label: str) -> tuple[float, float, float]:
    result = tuple(float(x) for x in value)
    if len(result) != 3 or not all(math.isfinite(x) for x in result):
        raise ValueError(f"{label} must be a finite 3-vector")
    length = math.sqrt(sum(x * x for x in result))
    if length < 1e-12:
        raise ValueError(f"{label} must be nonzero")
    return tuple(x / length for x in result)


def _point(value: Any, label: str) -> tuple[float, float, float]:
    result = tuple(float(x) for x in value)
    if len(result) != 3 or not all(math.isfinite(x) for x in result):
        raise ValueError(f"{label} must be a finite 3-point")
    return result


def _dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def _add_scaled(point: tuple[float, ...], direction: tuple[float, ...], amount: float) -> list[float]:
    return [point[i] + amount * direction[i] for i in range(3)]


def _module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load source helper: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _axis_rows(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {row["axis_id"]: row for row in model.get("connections", []) if row.get("kind") == "panel_screw"}
    if len(rows) != 66:
        raise ValueError(f"frozen model must contain 66 panel screws, found {len(rows)}")
    return rows


def _feature_membership(feature: dict[str, Any], group: str, axis_id: str, member: str) -> dict[str, Any]:
    rows = feature.get("source_axis_groups", {}).get(group, {}).get("axes", [])
    row = next((item for item in rows if item.get("axis_id") == axis_id), None)
    if row is None:
        raise ValueError(f"finished-feature axis missing: {axis_id}")
    matches = [m for m in row.get("receiver_memberships", []) if m.get("receiver_member_id") == member]
    if len(matches) != 1:
        raise ValueError(f"{axis_id} has no unique saved stock frame for {member}")
    return matches[0]


def _stock_projection(point: list[float], axis: list[float], length: float, membership: dict[str, Any]) -> dict[str, Any]:
    frame = membership["stock_frame"]
    origin = _point(frame["origin_global_xyz_mm"], "stock-frame origin")
    basis = [_vec(column, "stock-frame basis") for column in frame["basis_columns_global_xyz"]]
    dims = [float(x) for x in frame["original_dimensions_gqr_mm"]]
    delta = tuple(float(point[i]) - origin[i] for i in range(3))
    coords = [_dot(delta, column) for column in basis]
    direction = _vec(axis, "screw axis")
    local_axis = [_dot(direction, column) for column in basis]
    low, high = 0.0, length
    for coordinate, component, dimension in zip(coords, local_axis, dims, strict=True):
        if abs(component) < 1e-10:
            if coordinate < -1e-6 or coordinate > dimension + 1e-6:
                low, high = 1.0, 0.0
                break
        else:
            a, b = sorted((-coordinate / component, (dimension - coordinate) / component))
            low, high = max(low, a), min(high, b)
    overlap = max(0.0, high - low)
    transverse_edges = []
    for index in (1, 2):
        if abs(local_axis[index]) < 1e-8:
            transverse_edges.append({
                "stock_axis": "gqr"[index],
                "signed_clearances_to_faces_mm": [coords[index], dims[index] - coords[index]],
            })
    return {
        "basis_status": "saved_stock_frame_projection_only",
        "receiver_stock_dimensions_gqr_mm": dims,
        "screw_datum_gqr_mm": coords,
        "screw_direction_gqr": local_axis,
        "grain_end_clearances_mm": [coords[0], dims[0] - coords[0]],
        "transverse_edge_clearances": transverse_edges,
        "axis_interval_inside_receiver_stock_envelope_mm": [low, high] if overlap else None,
        "axis_length_inside_receiver_stock_envelope_mm": overlap,
        "limit": "Stock envelope only; no finished-solid support, installation, or capacity claim.",
    }


def _line(row: dict[str, Any], point: list[float], receiver: str, feature: dict[str, Any], length: float) -> dict[str, Any]:
    axis = list(_vec(row["axis_xyz"], row["axis_id"]))
    group = "panel_kicker_screw_axes"
    membership = _feature_membership(feature, group, row["axis_id"], receiver)
    return {
        "axis_id": row["axis_id"],
        "panel_member": row["source_record"]["panel_member"],
        "receiver_member": receiver,
        "axis_origin_xyz_mm": point,
        "axis_direction_xyz": axis,
        "nominal_length_mm": length,
        "nominal_diameter_mm": 4.1402,
        "receiver_stock_projection": _stock_projection(point, axis, length, membership),
    }


def _obstacle_box(helper: Any, axis: dict[str, Any]) -> list[float]:
    direction = tuple(axis["direction_xyz"])
    start = tuple(axis["start_xyz_mm"])
    end = tuple(axis["end_xyz_mm"])
    return helper._inflate(helper._cylinder_bounds(list(start), list(end), list(direction), axis["diameter_mm"] / 2))


def _fastener_rows(connections: list[dict[str, Any]], source_screws: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in connections:
        kind, record = row["kind"], row["source_record"]
        if kind == "panel_screw":
            source = source_screws[row["axis_id"]]
            start = list(_point(row["source_point_xyz_mm"], row["axis_id"]))
            direction = list(_vec(row["axis_xyz"], row["axis_id"]))
            length, diameter, semantics = 63.5, float(source["source_occupied_diameter_mm"]), "reported panel-screw datum to nominal tip"
        elif kind == "candidate_bolt":
            geometry = record["geometry"]
            direction = list(_vec(geometry["axis_head_to_nut_global"], row["axis_id"]))
            length = float(geometry["modeled_shaft_occupied_length_mm"])
            diameter = float(geometry["modeled_shaft_diameter_mm"])
            center = _point(geometry["shaft_center_global_xyz_mm"], row["axis_id"])
            start = _add_scaled(center, tuple(direction), -length / 2)
            semantics = "saved shaft-center segment"
        elif kind == "retained_bolt":
            direction = list(_vec(record["axis_global_xyz"], row["axis_id"]))
            length, diameter = float(record["source_occupied_length_mm"]), float(record["source_occupied_diameter_mm"])
            start = list(_point(record["origin_global_xyz_mm"], row["axis_id"]))
            semantics = "saved origin to recorded occupied length"
        else:
            continue
        result.append({
            "axis_id": row["axis_id"], "kind": kind,
            "start_xyz_mm": start, "end_xyz_mm": _add_scaled(tuple(start), tuple(direction), length),
            "direction_xyz": direction, "length_mm": length, "diameter_mm": diameter,
            "extent_semantics": semantics,
        })
    if sum(row["kind"] == "panel_screw" for row in result) != 66 or sum(row["kind"] == "candidate_bolt" for row in result) != 92 or sum(row["kind"] == "retained_bolt" for row in result) != 12:
        raise ValueError("frozen screw/bolt census must be 66/92/12")
    return result


def prepare(output_dir: str | Path) -> Path:
    if _sha(INPUTS) != EXPECTED_INPUTS_SHA256:
        raise ValueError("frozen model-inputs.json SHA-256 changed")
    if _sha(CORNER_MODEL) != EXPECTED_CORNER_SHA256:
        raise ValueError("reviewed corner-frame model SHA-256 changed")
    model, corner = _json(INPUTS), _json(CORNER_MODEL)
    if model.get("candidate") != corner.get("candidate") or model.get("revision_id") != corner.get("source_revision"):
        raise ValueError("reduced-static inputs and reviewed corner model do not match")
    for path, expected in model.get("source_sha256", {}).items():
        if _sha(ROOT / path) != expected:
            raise ValueError(f"frozen model-input source changed: {path}")

    helper = _module(HARDWARE_HELPER, "upper_corner_hardware_length_fit")
    helper_setup = helper.build_setup()
    if helper_setup["corner_model_development_revision"] != corner["development_revision"]:
        raise ValueError("saved STEP overrides belong to a different corner model")
    member_steps = {row["body_id"]: row for row in helper_setup["current_member_step_map"]}
    override_ids = set(helper_setup["source_files"]["corrected_step_override_ids"])
    if override_ids != {"top_outer_left_cleat", "top_outer_right_cleat", "base_side_left", "base_side_right"}:
        raise ValueError("corrected top STEP override set changed")

    transfer = _module(TRANSFER_INVENTORY, "upper_corner_panel_inventory")
    inventory, transfer_pins = transfer.build_report(root=ROOT)
    current_axes = {row["axis_id"]: row for row in inventory["axes"]}
    model_axes = _axis_rows(model)
    if set(current_axes) != set(model_axes):
        raise ValueError("current receiver inventory differs from frozen 66-axis model")
    source_screws = {row["axis_id"]: row for row in _json(SOURCE_INVENTORY)["fixed_panel_kicker_screws"]}
    if len(source_screws) != 66 or set(source_screws) != set(model_axes):
        raise ValueError("source inventory does not bind exactly 66 panel screws")
    feature = _json(FEATURES)

    panel_rows = []
    for axis_id, current in sorted(current_axes.items()):
        row = model_axes[axis_id]
        point = [float(x) for x in row["source_point_xyz_mm"]]
        direction = list(_vec(row["axis_xyz"], axis_id))
        if any(abs(point[i] - current["origin_global_xyz_mm"][i]) > 1e-6 for i in range(3)):
            raise ValueError(f"{axis_id}: frozen model and current inventory origins differ")
        if current["receiver_member"] != row["source_record"]["receiver_member"]:
            raise ValueError(f"{axis_id}: frozen model and current receiver inventory differ")
        panel_rows.append({
            "axis_id": axis_id, "panel_member": current["panel_member"],
            "receiver_member": current["receiver_member"], "origin_xyz_mm": point,
            "axis_direction_xyz": direction, "nominal_length_mm": 63.5,
            "diameter_mm": float(source_screws[axis_id]["source_occupied_diameter_mm"]),
            "location_status": current["current_location_status"],
        })
    by_axis = {row["axis_id"]: row for row in panel_rows}
    before_after = []
    moved_rows = {}
    for axis_id, receiver in TARGETS.items():
        current = by_axis[axis_id]
        if current["receiver_member"] != ("base_side_left" if "left_rim" in axis_id else "base_side_right" if "right_rim" in axis_id else "base_principal_center_left" if "left_center" in axis_id else "base_principal_center_right"):
            raise ValueError(f"{axis_id}: expected starting receiver changed")
        old = _line(model_axes[axis_id], current["origin_xyz_mm"], current["receiver_member"], feature, 63.5)
        new_point = _add_scaled(tuple(current["origin_xyz_mm"]), T_AXIS, MOVE_MM)
        t = _dot(tuple(new_point), T_AXIS)
        if abs(t - TOP_ROW_T_MM) > 1e-6:
            raise ValueError(f"{axis_id}: moved axis misses frozen top row T={TOP_ROW_T_MM}")
        new = dict(old)
        new.update({
            "receiver_member": receiver,
            "axis_origin_xyz_mm": new_point,
            "receiver_stock_projection": _stock_projection(
                new_point, old["axis_direction_xyz"], 63.5,
                _feature_membership(feature, "candidate_bolt_axes", "top_center/clip_split_top_center_left/rail_1", receiver)
                if receiver == "base_rail_top" else _feature_membership(feature, "panel_kicker_screw_axes", axis_id, receiver),
            ),
        })
        before_after.append({
            "axis_id": axis_id, "move_mm": MOVE_MM, "translation_xyz_mm": [MOVE_MM * x for x in T_AXIS],
            "target_T_mm": t, "before": old, "after": new,
        })
        moved_rows[axis_id] = new

    # Keep comparison to bounded, saved screw and bolt axes only.
    fasteners = _fastener_rows(model["connections"], source_screws)
    scenario_data = {}
    for scenario in ("before", "after"):
        axis_positions = {row["axis_id"]: row for row in panel_rows}
        if scenario == "after":
            for axis_id, row in moved_rows.items():
                axis_positions[axis_id] = {
                    **axis_positions[axis_id], "receiver_member": row["receiver_member"],
                    "origin_xyz_mm": row["axis_origin_xyz_mm"],
                }
        screws = []
        for axis_id, row in sorted(axis_positions.items()):
            direction = row["axis_direction_xyz"]
            start = row["origin_xyz_mm"]
            screws.append({"axis_id": axis_id, "kind": "panel_screw", "start_xyz_mm": start,
                           "end_xyz_mm": _add_scaled(tuple(start), tuple(direction), 63.5),
                           "direction_xyz": direction, "length_mm": 63.5, "diameter_mm": row["diameter_mm"],
                           "extent_semantics": "reported panel-screw datum to nominal tip"})
        axes = {row["axis_id"]: row for row in screws + [r for r in fasteners if r["kind"] != "panel_screw"]}
        boxes = {axis_id: _obstacle_box(helper, row) for axis_id, row in axes.items()}
        pairs = []
        for target_id in TARGETS:
            for other_id, other in axes.items():
                if other_id == target_id:
                    continue
                gap = helper._box_gap(boxes[target_id], boxes[other_id])
                if gap <= 0:
                    pairs.append({"axis_id": target_id, "other_axis_id": other_id,
                                  "other_kind": other["kind"], "AABB_gap_lower_bound_mm": 0.0,
                                  "refinement": "parent --run compares saved-axis cylinders"})
        scenario_data[scenario] = {"fastener_axis_count": len(axes), "AABB_overlap_pairs": pairs}

    member_ids = {"main_upper_left", "main_upper_right", "base_side_left", "base_side_right",
                  "base_principal_center_left", "base_principal_center_right", "base_rail_top"}
    selected_members = {name: member_steps[name] for name in sorted(member_ids)}
    if len(selected_members) != 7:
        raise ValueError("saved member STEP map does not contain all seven required solids")
    source_hashes = dict(helper_setup["source_sha256"])
    source_hashes.update({row["path"]: row["sha256"] for row in transfer_pins["sources"]})
    source_hashes[INPUTS.relative_to(ROOT).as_posix()] = EXPECTED_INPUTS_SHA256
    source_hashes[CORNER_MODEL.relative_to(ROOT).as_posix()] = EXPECTED_CORNER_SHA256
    source_hashes[SOURCE_INVENTORY.relative_to(ROOT).as_posix()] = _sha(SOURCE_INVENTORY)
    source_hashes[FEATURES.relative_to(ROOT).as_posix()] = _sha(FEATURES)
    for path in (HARDWARE_HELPER, TRANSFER_INVENTORY, Path(__file__)):
        source_hashes[path.relative_to(ROOT).as_posix()] = _sha(path)

    target = Path(output_dir)
    if not target.is_absolute():
        target = ROOT / target
    setup_path = target / "setup.json"
    setup = {
        "schema": "upper_corner_screw_geometry_setup/v1",
        "status": "prepared_saved_sources_only_waiting_for_parent_CAD_slot",
        "candidate": model["candidate"], "geometry_revision_id": model["revision_id"],
        "model_inputs_sha256": EXPECTED_INPUTS_SHA256, "corner_model_sha256": EXPECTED_CORNER_SHA256,
        "move_basis_T_xyz": list(T_AXIS), "move_mm": MOVE_MM, "target_T_mm": TOP_ROW_T_MM,
        "panel_screw_inventory_count": len(panel_rows), "receiver_inventory_counts": inventory["counts"],
        "changed_axis_ids": list(TARGETS), "before_after": before_after,
        "all_66_panel_screw_axes_before": panel_rows,
        "saved_fastener_axis_counts": {"panel_screw": 66, "candidate_bolt": 92, "retained_bolt": 12},
        "saved_member_steps": selected_members,
        "corrected_top_step_override_ids": sorted(override_ids),
        "scenarios": scenario_data,
        "source_sha256": dict(sorted(source_hashes.items())),
        "limits": [
            "Stock-frame distances use saved proposed stock envelopes; no support, installation, or capacity is established.",
            "Fastener axes are nominal saved cylinders; source lengths do not establish delivered hardware geometry.",
            "Only four axes, their panel/receiver solids, panel outer edges, and screw/bolt-axis occupancy are in scope.",
            "Saved STEP geometry is imported without scene replay or rebuilding.",
        ],
        "run_command": f"uv run --no-sync python {Path(__file__).resolve().relative_to(ROOT).as_posix()} --run --output-dir {Path(output_dir)}",
        "cad_run_executed": False,
    }
    _write_json(setup_path, setup)
    return setup_path


def _write_json(path: Path, value: dict[str, Any]) -> None:
    encoded = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") == encoded:
            return
        raise FileExistsError(f"refusing to replace existing raw output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(encoded, encoding="utf-8")


def _cylinder(cq: Any, row: dict[str, Any]):
    return cq.Solid.makeCylinder(
        float(row["diameter_mm"]) / 2, float(row["length_mm"]),
        cq.Vector(*row["start_xyz_mm"]), cq.Vector(*row["direction_xyz"]),
    )


def run(output_dir: str | Path) -> Path:
    setup_path = prepare(output_dir)
    setup = _json(setup_path)
    import cadquery as cq

    member_shapes: dict[str, Any] = {}
    fastener_shapes: dict[str, Any] = {}
    for member_id, row in setup["saved_member_steps"].items():
        member_shapes[member_id] = cq.importers.importStep(str(ROOT / row["step_path"])).val()

    model = _json(INPUTS)
    source_screws = {row["axis_id"]: row for row in _json(SOURCE_INVENTORY)["fixed_panel_kicker_screws"]}
    fasteners = _fastener_rows(model["connections"], source_screws)
    screw_rows = {row["axis_id"]: row for row in setup["all_66_panel_screw_axes_before"]}
    results = []
    for scenario in ("before", "after"):
        candidate_pairs = {
            (row["axis_id"], row["other_axis_id"])
            for row in setup["scenarios"][scenario]["AABB_overlap_pairs"]
        }
        axes = {row["axis_id"]: dict(row) for row in screw_rows.values()}
        if scenario == "after":
            for row in setup["before_after"]:
                axes[row["axis_id"]]["origin_xyz_mm"] = row["after"]["axis_origin_xyz_mm"]
                axes[row["axis_id"]]["receiver_member"] = row["after"]["receiver_member"]
        cylinders = {}
        for axis_id, row in axes.items():
            cylinders[axis_id] = cq.Solid.makeCylinder(
                row["diameter_mm"] / 2, row["nominal_length_mm"], cq.Vector(*row["origin_xyz_mm"]),
                cq.Vector(*row["axis_direction_xyz"]),
            )
        for row in fasteners:
            if row["kind"] != "panel_screw":
                fastener_shapes[row["axis_id"]] = _cylinder(cq, row)

        for change in setup["before_after"]:
            axis_id = change["axis_id"]
            item = change[scenario]
            moving = cylinders[axis_id]
            panel_id, receiver_id = item["panel_member"], item["receiver_member"]
            host_checks = []
            for role, member_id in (("panel", panel_id), ("receiver", receiver_id)):
                fixed = member_shapes[member_id]
                overlap = float(moving.intersect(fixed).Volume())
                distance = float(moving.distance(fixed))
                host_checks.append({
                    "role": role, "member_id": member_id,
                    "STEP_path": setup["saved_member_steps"][member_id]["step_path"],
                    "cylinder_intersection_volume_mm3": overlap,
                    "minimum_distance_mm": distance,
                    "interpretation": "saved-solid geometry only; intersection is not support adequacy or a new cut",
                })
            panel = member_shapes[panel_id]
            planar = [face for face in panel.Faces() if face.geomType() == "PLANE"]
            if not planar:
                raise ValueError(f"{panel_id}: saved panel STEP has no planar face for edge check")
            face = max(planar, key=lambda value: value.Area())
            vertex = cq.Vertex.makeVertex(*item["axis_origin_xyz_mm"])
            edge_distance = min(float(edge.distance(vertex)) for edge in face.outerWire().Edges())

            screw_bolts = []
            for other_id, other_shape in {**cylinders, **fastener_shapes}.items():
                if other_id == axis_id or (axis_id, other_id) not in candidate_pairs:
                    continue
                distance = float(moving.distance(other_shape))
                if distance <= 1e-6:
                    screw_bolts.append({"other_axis_id": other_id, "minimum_distance_mm": distance,
                                        "intersection_volume_mm3": float(moving.intersect(other_shape).Volume())})
            results.append({
                "scenario": scenario, "axis_id": axis_id, "receiver_member": receiver_id,
                "host_geometry": host_checks,
                "panel_outer_perimeter_edge_distance_mm": edge_distance,
                "panel_edge_method": "minimum 3D distance from saved axis datum to outer wire of largest planar panel face",
                "screw_bolt_axis_conflicts": screw_bolts,
            })

    changed = [path for path, digest in setup["source_sha256"].items() if _sha(ROOT / path) != digest]
    if changed:
        raise ValueError(f"source bytes changed during saved-geometry run: {changed}")
    result_path = Path(output_dir)
    if not result_path.is_absolute():
        result_path = ROOT / result_path
    result_path = result_path / "result.json"
    _write_json(result_path, {
        "schema": "upper_corner_screw_geometry_result/v1",
        "status": "saved_STEP_and_axis_geometry_checked",
        "setup_sha256": _sha(setup_path), "producer_sha256": _sha(Path(__file__)),
        "source_sha256": setup["source_sha256"], "source_unchanged_after_run": True,
        "geometry_rebuilt": False, "saved_STEP_solids_imported": len(member_shapes),
        "checks": results,
        "limits": setup["limits"],
    })
    return result_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="write pinned stdlib setup and AABB axis conflicts")
    mode.add_argument("--run", action="store_true", help="parent-only saved STEP check; use serialized CAD slot")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        if args.prepare:
            print(f"prepared {prepare(args.output_dir)}")
        else:
            print(f"completed {run(args.output_dir)}")
    except (OSError, ValueError, KeyError, TypeError, ImportError) as error:
        print(f"upper-corner geometry preparation refused: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
