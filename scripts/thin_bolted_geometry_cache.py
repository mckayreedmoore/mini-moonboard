"""Share exact frozen thin-v4 solids without repeating occupied CAD rebuilds.

The BREP files are ignored analysis inputs. This manifest authenticates them;
it is not a machining packet or a mechanics/strength acceptance result.
"""

from __future__ import annotations

import argparse
import json
import platform
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import cadquery as cq

from mini_moonboard import compact_floor_flush_frame
from scripts import hl35_candidate as shared
from scripts import thin_bolted_model as model
from scripts import thin_bolted_occupied as occupied

CACHE = shared.ROOT / "fea/generated/thin-bolted-v4-geometry"
MANIFEST = model.LAYOUT.parent / "native-geometry-v4.json"
INTEGRATED_SHA = "28bbd2d2fb6f1a93acb441af124c453f04f81e03be551906c633d5acad1d407e"


def bounds(shape: cq.Shape) -> list[list[float]]:
    box = shape.BoundingBox()
    return [[box.xmin, box.xmax], [box.ymin, box.ymax], [box.zmin, box.zmax]]


def grain_axes(names: list[str]) -> dict:
    """Nominal member grain directions, not inspection of actual lumber."""
    recess = compact_floor_flush_frame.floor_recess_geometry()
    result = {}
    for name in names:
        if name in recess:
            grain = cq.Vector(*recess[name]["grain_axis_xyz"])
        elif name.startswith("base_floor_"):
            grain = cq.Vector(0, 1, 0)
        elif name.startswith("base_post_"):
            grain = cq.Vector(0, 0, 1)
        elif name.startswith("base_rail_") or name == "base_header":
            grain = cq.Vector(1, 0, 0)
        elif name.startswith(("base_side_", "base_principal_")):
            grain = model.revision.thin.T
        else:
            raise ValueError(f"unclassified nominal grain: {name}")
        result[name] = shared.xyz(grain.normalized())
    return result


def build(cache: Path = CACHE) -> dict:
    integrated_path = model.EVIDENCE
    if shared.sha(integrated_path) != INTEGRATED_SHA:
        raise ValueError("preserve the reviewed integrated model evidence")
    frozen = model.source_layout()
    source_paths = set(frozen["source_sha256"]) | {
        str(model.LAYOUT.relative_to(shared.ROOT)),
        str(integrated_path.relative_to(shared.ROOT)),
        str(Path(__file__).relative_to(shared.ROOT)),
        "scripts/thin_bolted_model.py", "scripts/thin_bolted_layout_revision.py",
        "scripts/thin_bolted_occupied.py", "scripts/thin_bolted_candidate.py",
        "scripts/thin_bolted_fitting_screen.py", "uv.lock",
    }
    source_pins = {name: shared.sha(shared.ROOT / name) for name in sorted(source_paths)}
    cache.mkdir(parents=True, exist_ok=False)
    captured = {}
    original = model.revision.row_layout

    def capture(*args, **kwargs):
        answer = original(*args, **kwargs)
        captured["raw"] = dict(answer[0])
        return answer

    print("Reconstructing reviewed frozen geometry once", flush=True)
    with patch.object(model.revision, "row_layout", capture):
        source, wood, fitted, _axes, metal, services, _evidence = model.recreate()
    grains = grain_axes([name for name in wood if name.startswith(("base_", "lumber_leg_"))])
    expected = {r["name"]: r for r in json.loads(integrated_path.read_text())["finished_stock"]}
    for name, shape in wood.items():
        old = expected[name]
        if abs(shape.Volume() - old["volume_mm3"]) > max(.01, old["volume_mm3"] * 1e-9):
            raise ValueError(f"finished volume differs: {name}")
        if (shape.Center() - cq.Vector(*old["center_of_mass_xyz_mm"])).Length > 1e-5:
            raise ValueError(f"finished center differs: {name}")
    parts, raw_parts, outlines = [], [], []

    def add(target: list, identity: str, kind: str, shape: cq.Shape, **metadata) -> None:
        if not shape.isValid():
            raise ValueError(f"invalid source shape: {identity}")
        path = cache / (identity + ".brep")
        if path.exists() or not shape.exportBrep(str(path)):
            raise ValueError(f"cannot create untouched BREP: {identity}")
        restored = cq.Shape.importBrep(str(path))
        volume_error = abs(restored.Volume() - shape.Volume())
        bound_error = max(abs(a - b) for pair_a, pair_b in zip(bounds(shape), bounds(restored), strict=True)
                          for a, b in zip(pair_a, pair_b, strict=True))
        if (not restored.isValid() or volume_error > max(.01, shape.Volume() * 1e-9)
                or bound_error > 1e-5 or len(restored.Solids()) != len(shape.Solids())):
            raise ValueError(f"BREP roundtrip differs: {identity}")
        target.append({"id": identity, "kind": kind, "path": str(path.relative_to(shared.ROOT)),
                       "sha256": shared.sha(path), "bytes": path.stat().st_size,
                       "volume_mm3": shape.Volume(), "center_of_mass_xyz_mm": shared.xyz(shape.Center()),
                       "bounds_xyz_mm": bounds(shape), "solid_count": len(shape.Solids()),
                       "roundtrip_volume_error_mm3": volume_error, "roundtrip_bounds_error_mm": bound_error,
                       **metadata})

    print("Exporting and reimporting exact solids", flush=True)
    for name, shape in sorted(wood.items()):
        timber = name in grains
        add(parts, name, "timber" if timber else "panel", shape,
            **({"grain_axis_xyz": grains[name]} if timber else {}))
    for angle, fitting in fitted:
        add(parts, angle.id, "bracket", angle.shape, duty_id=angle.duty, catalog_model=fitting.model)
    for axis_id, role, shape in metal:
        add(parts, axis_id + "_" + role, role, shape, axis_id=axis_id, hardware_role=role)
    for row in source["screw_axes"]:
        shapes = [body for _, body in occupied.screw_shapes(row)]
        add(parts, "fastener_" + row["axis_id"], "screw", shapes[0].fuse(shapes[1]).clean(),
            axis_id=row["axis_id"], panel_member=row["panel"], receiver_member=row["receiver"])
    for name, kind, shape in services:
        add(parts, name, kind, shape)
    for name, shape in sorted(captured["raw"].items()):
        if name in grains:
            add(raw_parts, "raw_" + name, "timber", shape, member=name, grain_axis_xyz=grains[name])
    recovered, _ = model.panel_outlines(captured["raw"])
    for name, shape in sorted(recovered.items()):
        add(outlines, "outline_" + name, "panel", shape, member=name)
    counts = Counter(row["kind"] for row in parts)
    if len(parts) != 883 or len(raw_parts) != 20 or len(outlines) != 6:
        raise ValueError(f"cache census differs: {dict(counts)}")
    for name, expected_sha in source_pins.items():
        if shared.sha(shared.ROOT / name) != expected_sha:
            raise ValueError(f"source changed during reconstruction: {name}")
    return {"schema": "thin_bolted_exact_geometry_cache/v1", "candidate": model.CANDIDATE,
            "revision": model.REVISION, "source_sha256": source_pins,
            "method": {"format": "OpenCascade text BREP", "world_units": "mm",
                       "one_occupied_reconstruction": True, "reviewed_finished_volumes_centers_reproduced": True,
                       "every_export_reimported_and_checked": True, "python_version": platform.python_version(),
                       "cadquery_version": cq.__version__, "native_mechanics_solve": False},
            "counts": {**dict(counts), "finished_parts": len(parts), "raw_timbers": len(raw_parts),
                       "unperforated_panel_outlines": len(outlines)},
            "cache_bytes": sum(r["bytes"] for r in parts + raw_parts + outlines),
            "parts": parts, "raw_parts": raw_parts, "panel_outline_parts": outlines,
            "release": shared.RELEASE,
            "reproduce": ".venv/bin/python -m scripts.thin_bolted_geometry_cache",
            "retention": "Active shared analysis geometry in ignored fea/generated; do not prune while workers consume it.",
            "limits": ["Source shapes reproduce conditional catalog/material/clearance scenarios, not delivered parts.",
                       "Nominal grain vectors do not verify grain, grade or moisture of actual wood.",
                       "Raw members precede recesses, service channels and candidate bolt bores; finished members omit receiver screw pilots.",
                       "No stiffness, resistance, fabrication instruction, installed inspection or climbing release is established."]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=CACHE)
    parser.add_argument("--out", type=Path, default=MANIFEST)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("preserve immutable exact-geometry evidence")
    report = build(args.cache)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"counts": report["counts"], "cache_bytes": report["cache_bytes"]}, indent=2))


if __name__ == "__main__":
    main()
