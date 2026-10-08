"""Bounded twenty-timber reference contact atlas from frozen cached solids."""

import importlib.metadata
import itertools
import json
from collections import Counter
from pathlib import Path

import cadquery as cq
import numpy as np

from scripts import thin_bolted_timber_face_geometry as geometry

ROOT = Path(__file__).resolve().parents[3]
OWN = Path(__file__).resolve()
OUT = OWN.with_name("all-timber-pair-contact-atlas.json")
PACKET = ROOT / "docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison"
CACHE = PACKET / "native-geometry-v4.json"
OLD = PACKET / "timber-face-contact-geometry-v4.json"
LOCAL = OWN.with_name("direct-timber-contact.json")
EXPECTED = {CACHE: "cafdd983a41f2eee15647b28e60e5b2704354a4c5518d120e4c4342001994bb9",
            OLD: "be88aeb6754bc03e8afd523f5127f74b93b90bd00e8c3ceaa910e70aab3f125a",
            LOCAL: "ead9fee6a06d1233ac4cfd006fb2c681241d6ea2e81ddc410b1e47d9550e7dfa"}
AREA_TOL = 1e-6


def box_overlap(a, b):
    tol = geometry.PLANE_TOL_MM
    return all(max(x[0], y[0]) <= min(x[1], y[1]) + tol for x, y in zip(a, b, strict=True))


def planar_candidates(first, second):
    result = []
    for a in first:
        fa, na = a["_shape"], np.asarray(a["signature"]["oriented_normal_xyz"])
        for b in second:
            fb, nb = b["_shape"], np.asarray(b["signature"]["oriented_normal_xyz"])
            if not geometry.atlas._face_boxes_overlap(fa, fb, geometry.PLANE_TOL_MM):
                continue
            dot = float(na @ nb)
            offset = abs(float((np.asarray(fb.Center().toTuple()) - np.asarray(fa.Center().toTuple())) @ na))
            if abs(abs(dot) - 1.) <= 1e-8 and offset <= geometry.PLANE_TOL_MM:
                result.append({"first_face_id": a["face_id"], "second_face_id": b["face_id"],
                               "normal_dot": dot, "plane_offset_mm": offset})
    return result


def curved_candidates(first_shape, second_shape):
    result = []
    for i, fa in enumerate(first_shape.Faces(), 1):
        for j, fb in enumerate(second_shape.Faces(), 1):
            if fa.geomType() == fb.geomType() == "PLANE":
                continue
            if not geometry.atlas._face_boxes_overlap(fa, fb, geometry.PLANE_TOL_MM):
                continue
            row = {"first_face_ordinal_1_based": i, "second_face_ordinal_1_based": j,
                   "first_surface_type": fa.geomType(), "second_surface_type": fb.geomType()}
            try:
                common = fa.intersect(fb)
                own = [r for r in common.Faces() if r.Area() > AREA_TOL]
                row.update(status="positive-curved-area-unqualified" if own else "no-positive-trimmed-surface-area",
                           intersection_positive_area_mm2=sum(r.Area() for r in own),
                           positive_regions=[geometry.atlas._region_geometry_data(r) for r in own])
            except (ValueError, RuntimeError, TypeError) as error:
                row.update(status="curved-boolean-query-failed", error=repr(error))
            result.append(row)
    return result


def query():
    sha = geometry.frame.sha
    require = geometry.require
    require(all(sha(path) == expected for path, expected in EXPECTED.items()), "Frozen geometry evidence changed")
    cache = json.loads(CACHE.read_bytes())
    reused = {}
    for path in (OLD, LOCAL):
        report = json.loads(path.read_bytes())
        for pair in report["pairs"]:
            key = tuple(sorted((pair["first"], pair["second"])))
            require(key not in reused, "Duplicate reused pair")
            own = [p for p in report["patches"] if p["id"] in pair["patch_ids"]]
            require(own and len(own) == pair["patch_count"], "Exact reused positive patch set required")
            require(all(all(c["reference_centroid_on_trimmed_patch"] and c["both_inward_material_probes_occupied"]
                            for c in p["cells"]) for p in own), "Reused material occupancy proof required")
            reused[key] = {"path": str(path.relative_to(ROOT)), "sha256": EXPECTED[path],
                           "pair": pair, "patch_ids": pair["patch_ids"],
                           "area_mm2": sum(p["area_mm2"] for p in own),
                           "cell_count": sum(len(p["cells"]) for p in own)}
    require(len(reused) == 9, "Exactly nine proved pair queries reused")
    rows = {r["id"]: r for r in cache["parts"] if r["kind"] == "timber"}
    require(len(rows) == 20, "Frozen twenty-timber census required")
    pin_paths = [OWN, Path(geometry.__file__), Path(geometry.atlas.__file__), Path(geometry.partition.__file__)]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in pin_paths}
    pins.update({str(p.relative_to(ROOT)): expected for p, expected in EXPECTED.items()})
    shapes = {}
    surface_types = {}
    for name, row in sorted(rows.items()):
        path = ROOT / row["path"]
        require(sha(path) == row["sha256"], "Finished timber BREP changed")
        shape = cq.Shape.importBrep(str(path))
        require(shape.isValid() and len(shape.Solids()) == 1, "One valid finished timber solid required")
        shapes[name] = shape
        pins[row["path"]] = row["sha256"]
        surface_types[name] = dict(Counter(f.geomType() for f in shape.Faces()))
    faces = {name: geometry.atlas.source_face_records(name, shape) for name, shape in shapes.items()}
    pairs, patches = [], []
    for a, b in itertools.combinations(sorted(rows), 2):
        row = {"first": a, "second": b, "pair_id": f"{a}|{b}", "reference_bounds_overlap":
               box_overlap(rows[a]["bounds_xyz_mm"], rows[b]["bounds_xyz_mm"])}
        if not row["reference_bounds_overlap"]:
            require((a, b) not in reused, "Reused proved pair cannot have disjoint authenticated bounds")
            row.update(status="disjoint-source-bounds", patch_count=0, positive_area_mm2=0.,
                       planar_coplanar_candidate_count=0, curved_surface_candidate_queries=[])
        else:
            candidates = planar_candidates(faces[a], faces[b])
            row["planar_coplanar_candidates"] = candidates
            row["planar_coplanar_candidate_count"] = len(candidates)
            row["curved_surface_candidate_queries"] = curved_candidates(shapes[a], shapes[b])
            if (a, b) in reused:
                prior = reused[(a, b)]
                row.update(status="positive-planar-area-reused", reused_geometry=prior,
                           patch_count=len(prior["patch_ids"]), positive_area_mm2=prior["area_mm2"])
            elif not candidates:
                row.update(status="no-coplanar-planar-candidates", patch_count=0, positive_area_mm2=0.)
            else:
                try:
                    own = geometry.find_patches(a, b, faces, shapes, cell_size_mm=25.)
                    row.update(status="positive-planar-area-queried" if own else "empty-trimmed-planar-intersection",
                               patch_ids=[p["id"] for p in own], patch_count=len(own),
                               positive_area_mm2=sum(p["area_mm2"] for p in own))
                    patches.extend(own)
                except (ValueError, RuntimeError, TypeError) as error:
                    row.update(status="planar-query-failed", error=repr(error),
                               patch_count=None, positive_area_mm2=None)
        pairs.append(row)
        if row["reference_bounds_overlap"]:
            print(json.dumps({"pair": row["pair_id"], "status": row["status"],
                              "area_mm2": row["positive_area_mm2"],
                              "curved_queries": len(row["curved_surface_candidate_queries"])}), flush=True)
    for path, expected in pins.items():
        require(sha(ROOT / path) == expected, "Source changed during cached contact query")
    status = Counter(r["status"] for r in pairs)
    curved_status = Counter(c["status"] for r in pairs for c in r["curved_surface_candidate_queries"])
    require(len(pairs) == 190, "Complete unordered twenty-timber pair census required")
    geometric_complete = (not status["planar-query-failed"] and not curved_status["curved-boolean-query-failed"]
                          and not curved_status["positive-curved-area-unqualified"])
    return {"schema": "thin_bolted_all_timber_reference_contact_atlas/v1", "source_sha256": pins,
            "candidate": cache["candidate"], "cached_timbers": [{"member": name, "path": rows[name]["path"],
                "sha256": rows[name]["sha256"], "grain_axis_xyz": rows[name]["grain_axis_xyz"],
                "bounds_xyz_mm": rows[name]["bounds_xyz_mm"], "surface_type_counts": surface_types[name]}
                for name in sorted(rows)], "pairs": pairs, "new_positive_patches": patches,
            "counts": {"timbers": 20, "unordered_pairs": len(pairs), "reused_proved_pairs": 9,
                       "pair_status": dict(status), "curved_query_status": dict(curved_status),
                       "new_positive_patches": len(patches), "new_occupied_cells": sum(len(p["cells"]) for p in patches)},
            "reference_positive_area_contact_geometry_enumerated": geometric_complete,
            "complete_contact_response_operator": False,
            "method": {"source_face_records": "unchanged planar face ordinals/signatures",
                "find_patches": "unchanged opposed coplanar trimmed intersection + occupied centroid-cell proof",
                "pair_screen": "authenticated solid bounds and coplanar face candidates only; screens do not claim positive overlap",
                "curved_screen": "bounding overlapping non-planar face pairs use the same face.intersect Boolean; positive curved results are explicitly unqualified",
                "area_threshold_mm2": AREA_TOL, "plane_tolerance_mm": geometry.PLANE_TOL_MM,
                "cell_size_mm": 25., "probe_depth_mm": .05, "cadquery_version": cq.__version__,
                "cadquery_ocp_version": importlib.metadata.version("cadquery-ocp")},
            "required_response_correction": "Every newly proved touching timber pair needs an explicit distinct reviewed compression contact law/operator before current force analysis; this reference atlas does not adopt it.",
            "limits": ["Completeness is bounded to positive-area touching surfaces of the twenty source finished solids at declared kernel/area tolerances, not all future contact after motion.",
                "No solid-volume interpenetration audit, near-gap closure, line/point contact stiffness, pressure, preload, friction or resistance is supplied.",
                "Non-planar positive-area/Boolean failures remain explicit method gaps; no planar cell partition is assigned to them.",
                "Cell area/first-moment conservation and occupied centroids do not establish exact rocking stiffness or pressure maxima.",
                "No CAD rebuild, inventory export, global/native/K/response solve, priorforce/pass transfer or operator adoption."],
            "release": {"structural_acceptance": False, "fabrication_release": False, "climbing_release": False}}


if __name__ == "__main__":
    if OUT.exists():
        raise SystemExit("Preserve issued all-pair atlas")
    report = query()
    report["command"] = ["PYTHONPATH=.", "OPENBLAS_NUM_THREADS=1", ".venv/bin/python", str(OWN.relative_to(ROOT))]
    OUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "sha256": geometry.frame.sha(OUT),
                      "source_sha256": geometry.frame.sha(OWN), "counts": report["counts"],
                      "reference_geometry_enumerated": report["reference_positive_area_contact_geometry_enumerated"]}))
