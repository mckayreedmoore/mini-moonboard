"""Revise only the four cleat/post axes in the frozen eoere geometry method.

The first occupied build crosses two retained kicker screws. Keep that build
and its producer unchanged; reuse the producer with an explicit axis adapter.
No panel screw, main fitting pose, existing stock section or force is changed.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from unittest.mock import patch

import cadquery as cq

from scripts import eoere_bolted_model as model

ROOT = model.ROOT
FIRST = model.CACHE / "geometry.json"
FIRST_SHA = "552870d3ff7c7f2c678ef917b7cee037614c11cef180126d9cf06ab8d2cab3ec"
ORIGINAL_PREPARE_AXES = model.prepare_axes


def retarget_cleat_axes(axes: list[dict], wood: dict, z_mm: float) -> tuple[list[dict], list[dict]]:
    """Move the four independent cleat axes, rechecking finite wood ownership."""
    if not math.isfinite(z_mm):
        raise ValueError("finite cleat/post bolt height required")
    result, changes = [], []
    for axis in axes:
        if axis["source"] != "cleat_post_through_bolt":
            result.append(axis)
            continue
        old = axis["point"]
        point = cq.Vector(old.x, old.y, z_mm)
        names, near, far = model.connected_receivers(wood, point, axis["direction"], axis["receivers"][0])
        if set(names) != set(axis["receivers"]) or abs((far - near) - axis["grip_mm"]) > 1e-5:
            raise ValueError("revised cleat axis changes its receiver or grip")
        revised = dict(axis, point=point + axis["direction"] * near, receivers=names)
        result.append(revised)
        changes.append({"axis_id": axis["id"], "point_before_xyz_mm": model.shared.xyz(old),
                        "point_after_xyz_mm": model.shared.xyz(revised["point"]),
                        "reason": "clear retained kicker screws without moving their axes"})
    if len(changes) != 4:
        raise ValueError("exactly four independent cleat/post axes required")
    return result, changes


def build(output: Path, z_mm: float) -> tuple[dict, dict]:
    if model.shared.sha(FIRST) != FIRST_SHA:
        raise ValueError("first failed occupied-geometry input differs")
    changes = []

    def prepare(wood, angles, scenario, old_axes):
        axes, ports = ORIGINAL_PREPARE_AXES(wood, angles, scenario, old_axes)
        axes, revised = retarget_cleat_axes(axes, wood, z_mm)
        changes.extend(revised)
        return axes, ports

    # The unchanged producer performs the complete occupied queries and export.
    # Its source-closure collector also pins this adapter before and after use.
    with patch.object(model, "prepare_axes", prepare):
        report, scene = model.build(output)
    if model.shared.sha(FIRST) != FIRST_SHA:
        raise ValueError("first failed geometry changed during revision")
    report["source_sha256"][str(FIRST.relative_to(ROOT))] = FIRST_SHA
    report["inputs"]["cleat_post_axis_z_mm"] = z_mm
    report["changes"]["cleat_post_axis_moves"] = changes
    report["changes"]["preserved_first_geometry_sha256"] = FIRST_SHA
    scene["layout_report"]["path"] = str((model.PACKET / "occupied-geometry-v2.json").relative_to(ROOT))
    return report, scene


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cleat-post-z", type=float, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior geometry attempts; choose a distinct output")
    args.output.mkdir(parents=True)
    report, scene = build(args.output, args.cleat_post_z)
    report_path = args.output / "geometry.json"
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    scene["layout_report"]["sha256"] = model.shared.sha(report_path)
    scene_path = args.output / "scene.json"
    scene_path.write_text(json.dumps(scene, separators=(",", ":"), allow_nan=False) + "\n")
    (args.output / "scene.json.gz").write_bytes(gzip.compress(scene_path.read_bytes(), compresslevel=9, mtime=0))
    print(json.dumps({"output": str(args.output), "counts": report["counts"],
                      "collision_counts": {key: len(rows) for key, rows in report["collisions"].items()},
                      "layout_sha256": model.shared.sha(report_path),
                      "scene_sha256": model.shared.sha(scene_path)}, indent=2))


if __name__ == "__main__":
    main()
