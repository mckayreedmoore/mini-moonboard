"""Three targeted cached-solid contact queries; no rebuilt geometry or physics."""

import importlib.metadata
import json
from pathlib import Path

import cadquery as cq

from scripts import thin_bolted_timber_face_geometry as geometry

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve()
OUT = OWN.with_name("direct-timber-contact.json")
CACHE = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/native-geometry-v4.json"
CACHE_SHA = "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9"
PAIRS = [("base_header", "base_side_left", 277.),
         ("base_header", "base_principal_center_left", 277.),
         ("base_header", "base_post_center_left", 238.9)]


def query():
    sha = geometry.frame.sha
    geometry.require(sha(CACHE) == CACHE_SHA, "Frozen cache changed")
    cache = json.loads(CACHE.read_bytes())
    rows = {r["id"]: r for r in cache["parts"] if r["kind"] == "timber"}
    names = sorted({member for a, b, _ in PAIRS for member in (a, b)})
    paths = [OWN, CACHE, Path(geometry.__file__), Path(geometry.atlas.__file__),
             Path(geometry.partition.__file__)]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    shapes = {}
    for name in names:
        row = rows[name]
        path = ROOT / row["path"]
        geometry.require(sha(path) == row["sha256"], "Finished BREP changed")
        shape = cq.Shape.importBrep(str(path))
        geometry.require(shape.isValid() and len(shape.Solids()) == 1, "One valid finished timber required")
        shapes[name] = shape
        pins[row["path"]] = row["sha256"]
    faces = {name: geometry.atlas.source_face_records(name, shapes[name]) for name in names}
    pairs, patches = [], []
    for first, second, expected_z in PAIRS:
        own = geometry.find_patches(first, second, faces, shapes, cell_size_mm=25.)
        geometry.require(all(abs(r["centroid_xyz_mm"][2] - expected_z) < 1e-6 for r in own),
                         "Unexpected direct timber interface plane")
        pairs.append({"first": first, "second": second, "expected_plane_z_mm": expected_z,
                      "patch_ids": [r["id"] for r in own], "patch_count": len(own),
                      "trimmed_overlap_area_mm2": sum(r["area_mm2"] for r in own)})
        patches.extend(own)
    for path, expected in pins.items():
        geometry.require(sha(ROOT / path) == expected, "Query source changed while loaded")
    return {"schema": "thin_bolted_local_direct_timber_contact_geometry/v1", "source_sha256": pins,
            "source_cached_parts": [rows[name] for name in names], "pairs": pairs, "patches": patches,
            "method": {"functions": "unchanged atlas.source_face_records and timber_face_geometry.find_patches",
                       "enumeration": "all opposed coplanar positive-area finished face intersections for the three pairs",
                       "cell_size_mm": 25., "material_probe_depth_mm": .05,
                       "planar_tolerance_mm": geometry.PLANE_TOL_MM,
                       "occupancy_tolerance_mm": geometry.OCCUPANCY_TOL_MM,
                       "cadquery_version": cq.__version__,
                       "cadquery_ocp_version": importlib.metadata.version("cadquery-ocp")},
            "required_model_change_before_response": "Direct paired wood contacts are absent from the existing six-pair production contact atlas; any added compression law requires a distinct reviewed source-bound model/operator. Geometry only is issued here.",
            "limits": ["No continuous pressure, bedding stiffness, preload, friction, force, capacity or physical contact acceptance.",
                       "Fixed reference overlap does not establish current overlap after slip or finite rotation.",
                       "Area-resultant cells are geometric witnesses; their sampled second moments are not a stiffness bound.",
                       "No CAD reconstruction, inventory sweep, native/global solve or current/historical force consumption."],
            "release": {"structural_acceptance": False, "fabrication_release": False, "climbing_release": False}}


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit("Preserve issued targeted contact query")
    result = query()
    result["command"] = ["PYTHONPATH=.", "OPENBLAS_NUM_THREADS=1", ".venv/bin/python", str(OWN.relative_to(ROOT))]
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"path": str(OUT.relative_to(ROOT)), "sha256": geometry.frame.sha(OUT),
                      "producer_sha256": geometry.frame.sha(OWN), "pairs": result["pairs"],
                      "patches": len(result["patches"]), "cells": sum(len(r["cells"]) for r in result["patches"])}))
