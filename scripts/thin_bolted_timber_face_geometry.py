"""Query six missing timber interfaces from eight authenticated finished BREPs.

Reuses the existing planar-face atlas and trimmed area-cell partition. This
exports reference contact geometry only, without rebuilding CAD or preparing
mechanics. Area/first moments are conserved; centroid quadrature error in
second moments is reported explicitly rather than called a stiffness bound.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps

from fea import wood_joint_reduced_contacts as partition
from scripts import thin_bolted_frame_mechanics as frame
from scripts import wood_joint_current_face_pair_atlas_attempt01 as atlas

SCHEMA = "thin_bolted_timber_face_contact_geometry/v1"
PAIRS = [(f"base_side_{side}", f"lumber_leg_{side}") for side in ("left", "right")]
PAIRS += [(f"base_post_outer_{side}", f"base_floor_{side}") for side in ("left", "right")]
PAIRS += [(f"base_floor_{side}", f"lumber_leg_{side}") for side in ("left", "right")]
PLANE_TOL_MM = 1e-5
OCCUPANCY_TOL_MM = 1e-7


def require(test, message):
    if not test:
        raise ValueError(message)


def centroidal_second_moments(face):
    """Return exact global centroidal integral (x-c)(x-c)^T dA."""
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face.wrapped, props, False, False)
    inertia = props.MatrixOfInertia()
    matrix = np.array([[inertia.Value(i + 1, j + 1) for j in range(3)] for i in range(3)])
    return .5 * np.trace(matrix) * np.eye(3) - matrix


def occupied_cells(face, first_shape, second_shape, normal, *, cell_size_mm):
    """Use the shared partition; refine only when a resultant lies in a void."""
    for level in range(7):
        effective = cell_size_mm / 2**level
        cells = partition.area_cells(face, normal, size_mm=effective, minimum_divisions=2)
        failures = []
        for row in cells:
            point = np.asarray(row["point_xyz_mm"])
            gap = face.distance(cq.Vertex.makeVertex(*point))
            occupied = (gap <= OCCUPANCY_TOL_MM
                        and first_shape.isInside(cq.Vector(*(point + .05 * normal)), 1e-7)
                        and second_shape.isInside(cq.Vector(*(point - .05 * normal)), 1e-7))
            if not occupied:
                failures.append(row)
            row["reference_centroid_on_trimmed_patch"] = gap <= OCCUPANCY_TOL_MM
            row["both_inward_material_probes_occupied"] = bool(occupied)
            row["reference_centroid_patch_distance_mm"] = float(gap)
        if not failures:
            return cells, effective, level
    raise ValueError("Trimmed contact centroid remains outside actual opposed timber material")


def find_patches(first, second, faces, shapes, *, cell_size_mm):
    patches = []
    for a in faces[first]:
        face_a = a["_shape"]
        normal_a = np.asarray(face_a.normalAt().toTuple())
        for b in faces[second]:
            face_b = b["_shape"]
            if not atlas._face_boxes_overlap(face_a, face_b, PLANE_TOL_MM):
                continue
            normal_b = np.asarray(face_b.normalAt().toTuple())
            dot = float(normal_a @ normal_b)
            offset = abs(float((np.asarray(face_b.Center().toTuple())
                                - np.asarray(face_a.Center().toTuple())) @ normal_a))
            if abs(abs(dot) - 1.) > 1e-8 or offset > PLANE_TOL_MM:
                continue
            regions = [r for r in face_a.intersect(face_b).Faces() if r.Area() > 1e-6]
            if not regions:
                continue
            require(dot < -1. + 1e-8, "Shared planar material faces must be opposed")
            regions.sort(key=lambda r: atlas._canonical_json(atlas._region_geometry_data(r)))
            for region_index, region in enumerate(regions):
                region_data = atlas._region_geometry_data(region)
                patch_id = (f"timber-face/{first}/{second}/"
                            f"{a['face_ordinal_1_based']}-{b['face_ordinal_1_based']}-{region_index}")
                cells, effective, level = occupied_cells(region, shapes[first], shapes[second], normal_b,
                                                        cell_size_mm=cell_size_mm)
                for index, cell in enumerate(cells):
                    cell["id"] = patch_id + f"/cell-{index}"
                area, center = float(region.Area()), np.asarray(region.Center().toTuple())
                weighted_center = sum((r["area_mm2"] * np.asarray(r["point_xyz_mm"]) for r in cells),
                                      np.zeros(3)) / area
                exact_second = centroidal_second_moments(region)
                sampled_second = sum((r["area_mm2"] * np.outer(np.asarray(r["point_xyz_mm"]) - center,
                                                               np.asarray(r["point_xyz_mm"]) - center)
                                      for r in cells), np.zeros((3, 3)))
                patches.append({"id": patch_id, "first": first, "second": second,
                    "source_first_face": {k: v for k, v in a.items() if k != "_shape"},
                    "source_second_face": {k: v for k, v in b.items() if k != "_shape"},
                    "first_outward_normal_xyz": normal_a.tolist(),
                    "normal_from_second_to_first_xyz": normal_b.tolist(),
                    "opposed_normal_dot": dot, "coplanar_offset_mm": offset,
                    "trimmed_region_geometry": region_data,
                    "trimmed_region_signature_sha256": atlas._canonical_sha256(region_data),
                    "area_mm2": area, "centroid_xyz_mm": center.tolist(), "cells": cells,
                    "effective_cell_size_mm": effective, "occupancy_refinement_levels": level,
                    "cell_area_error_mm2": float(sum(r["area_mm2"] for r in cells) - area),
                    "cell_centroid_error_mm": float(np.linalg.norm(weighted_center - center)),
                    "exact_centroidal_second_moment_matrix_xyz_mm4": exact_second.tolist(),
                    "sampled_centroidal_second_moment_matrix_xyz_mm4": sampled_second.tolist(),
                    "second_moment_relative_frobenius_error": float(np.linalg.norm(sampled_second - exact_second)
                                                                  / np.linalg.norm(exact_second)),
                    "cell_semantics": "area resultants; every centroid verified on trimmed patch and both inward material probes"})
    return patches


def query(*, cell_size_mm):
    require(np.isfinite(cell_size_mm) and cell_size_mm > 0., "Positive contact cell size required")
    require(frame.sha(frame.LAYOUT) == frame.LAYOUT_SHA, "Frozen layout changed")
    require(frame.sha(frame.GEOMETRY_CACHE) == frame.GEOMETRY_CACHE_SHA, "Frozen native geometry changed")
    layout = json.loads(frame.LAYOUT.read_text())
    cache = json.loads(frame.GEOMETRY_CACHE.read_text())
    rows = {r["id"]: r for r in cache["parts"] if r["kind"] == "timber"}
    names = sorted({n for pair in PAIRS for n in pair})
    sources = [{**rows[name], "member": name} for name in names]
    pins = {str(frame.LAYOUT.relative_to(frame.ROOT)): frame.LAYOUT_SHA,
            str(frame.GEOMETRY_CACHE.relative_to(frame.ROOT)): frame.GEOMETRY_CACHE_SHA,
            "scripts/wood_joint_current_face_pair_atlas_attempt01.py": frame.sha(Path(atlas.__file__)),
            "fea/wood_joint_reduced_contacts.py": frame.sha(Path(partition.__file__)),
            str(Path(__file__).relative_to(frame.ROOT)): frame.sha(Path(__file__))}
    shapes = {}
    for row in sources:
        require(frame.sha(frame.ROOT / row["path"]) == row["sha256"], "Finished timber BREP changed")
        shape = cq.Shape.importBrep(str(frame.ROOT / row["path"]))
        require(shape.isValid() and len(shape.Solids()) == 1, "One valid finished timber solid required")
        shapes[row["id"]] = shape
        pins[row["path"]] = row["sha256"]
    faces = {name: atlas.source_face_records(name, shape) for name, shape in shapes.items()}
    pairs, patches = [], []
    for first, second in PAIRS:
        own = find_patches(first, second, faces, shapes, cell_size_mm=cell_size_mm)
        axes = sorted(r["id"] for r in layout["installed_axes"]
                      if r["source"] == "original_starting_frame_axis"
                      and set(r["receivers"]) == {first, second})
        require(len(axes) == 2, "Each queried interface must belong to exactly two retained axes")
        pairs.append({"id": f"{first}|{second}", "first": first, "second": second,
                      "retained_axis_ids": axes, "patch_ids": [r["id"] for r in own],
                      "patch_count": len(own), "area_mm2": sum(r["area_mm2"] for r in own)})
        patches.extend(own)
    for path, expected in pins.items():
        require(frame.sha(frame.ROOT / path) == expected, "Query source changed during execution")
    return {"schema": SCHEMA, "candidate": layout["candidate"], "layout_report_sha256": frame.LAYOUT_SHA,
        "geometry_cache_sha256": frame.GEOMETRY_CACHE_SHA, "source_sha256": pins,
        "method": {"cell_size_mm": cell_size_mm, "minimum_divisions": 2,
                   "planar_face_tolerance_mm": PLANE_TOL_MM, "opposed_normal_tolerance": 1e-8,
                   "occupancy_tolerance_mm": OCCUPANCY_TOL_MM, "material_probe_depth_mm": .05,
                   "recreated_geometry": False, "cadquery_version": cq.__version__,
                   "cadquery_ocp_version": importlib.metadata.version("cadquery-ocp"),
                   "numpy_version": np.__version__,
                   "face_enumeration": "all opposed coplanar positive-area finished face intersections for each pair",
                   "cell_partition": "unchanged fea.wood_joint_reduced_contacts.area_cells; void-centroid refinement only",
                   "second_moment_method": "OCP surface inertia; centroid sampling reported separately"},
        "sources": sources, "pairs": pairs, "patches": patches,
        "counts": {"finished_timbers": len(sources), "member_pairs": len(pairs),
                   "retained_axes": sum(len(p["retained_axis_ids"]) for p in pairs),
                   "patches": len(patches), "cells": sum(len(p["cells"]) for p in patches)},
        "limits": ["Reference occupied contact geometry does not establish current overlap after finite slip.",
                   "Centroid cells conserve area and first moments, not exact rocking stiffness or local pressure peaks.",
                   "No bedding stiffness, preload, friction, resistance, inspected material or physical release is supplied."],
        "release": frame.RELEASE}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell-size", type=float, default=25.)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Preserve issued contact geometry")
    report = query(cell_size_mm=args.cell_size)
    report["command"] = ["OPENBLAS_NUM_THREADS=1", ".venv/bin/python", "-m",
                         "scripts.thin_bolted_timber_face_geometry", "--cell-size", str(args.cell_size),
                         "--out", str(args.out)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        stream.write(json.dumps(report, separators=(",", ":"), allow_nan=False) + "\n")
    print(json.dumps({"path": str(args.out), "sha256": frame.sha(args.out), "bytes": args.out.stat().st_size,
                      "counts": report["counts"], "maximum_second_moment_error":
                      max((r["second_moment_relative_frobenius_error"] for r in report["patches"]), default=None)}))


if __name__ == "__main__":
    main()
