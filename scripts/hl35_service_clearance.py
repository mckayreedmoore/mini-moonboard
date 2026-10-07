"""Inspect retained service bodies against a new HL35 candidate's occupied pose.

Native service solids are authenticated against the preserved display bounds
and asset hashes. Positive intersections are geometric findings, not forces.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from mini_moonboard import hold_tnut_reinforcement as tnuts
from mini_moonboard import no_shoes_frame, round_structural_wiring
from mini_moonboard.floor_flush_width import KERF_RIGHT, variant
from scripts import hl35_candidate as base


def mesh_bounds(mesh: dict) -> tuple[np.ndarray, np.ndarray]:
    dtype = {"int16": "<i2", "int32": "<i4"}[mesh["vertex_component_type"]]
    points = np.frombuffer(base64.b64decode(mesh["vertices_base64"]), dtype).reshape(-1, 3)
    points = points * mesh["vertex_quantization_mm"]
    return points.min(axis=0), points.max(axis=0)


def service_parts() -> tuple[list[tuple[str, str, cq.Shape]], dict]:
    _, _, parent = base.load_sources()
    changes = parent["revision_report"]
    parts = []
    for part in variant(KERF_RIGHT).electrical_parts():
        shape = part.shape
        if part.name == "light_G2":
            shape = shape.translate(cq.Vector(*changes["led_move"]["translation_xyz_mm"]))
        elif part.name in changes["wire_endpoint_revisions"]:
            change = changes["wire_endpoint_revisions"][part.name]
            record = {"route_local_mm": change["route_local_mm"]}
            path = round_structural_wiring.wire_path(record)
            if abs(path.Length() - change["routed_length_mm"]) > 1e-8:
                raise ValueError("reviewed wire length differs")
            first, second = [round_structural_wiring.b.point(*p) for p in record["route_local_mm"][:2]]
            plane = cq.Plane(origin=first, normal=(second - first).normalized())
            shape = cq.Workplane(plane).circle(round_structural_wiring.CABLE_DIAMETER_MM / 2).sweep(
                cq.Workplane(obj=path), isFrenet=True).val().translate(cq.Vector(*change["source_placement_xyz_mm"]))
        parts.append((part.name, part.kind, shape))
    parts.extend((part.name, "tnut", part.shape) for part in tnuts.parts(no_shoes_frame))
    if len(parts) != 405 or len({p[0] for p in parts}) != 405:
        raise ValueError("expected 132 lights, 131 wires and 142 T-nuts")
    baseline = json.loads((base.ROOT / "site/hybrid/compact-floor-flush-kerf-right/parts.json").read_text())
    by_name = {r["name"]: r for r in baseline["parts"]}
    replacements = {r["name"]: r for r in parent["solids"] if r["display_class"] == "electrical_replacement"}
    aliases = json.loads((base.ROOT / "site/mesh-aliases.json").read_text())["aliases"]
    dtype = np.dtype([("normal", "<f4", (3,)), ("points", "<f4", (3, 3)), ("attribute", "<u2")])
    checked = []
    for name, kind, shape in parts:
        if name in replacements:
            low, high = mesh_bounds(replacements[name]["mesh"])
            source = "source-bound reviewed replacement"
        else:
            path = by_name[name]["path"]
            raw = (base.ROOT / "site" / aliases.get(path, path)).read_bytes()
            if hashlib.sha256(raw).hexdigest() != parent["baseline_asset_sha256"][path]:
                raise ValueError(f"preserved service asset differs: {path}")
            points = np.frombuffer(raw, dtype, offset=84)["points"].reshape(-1, 3)
            low, high = points.min(axis=0), points.max(axis=0)
            source = path
        b = shape.BoundingBox()
        actual = np.array([[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]])
        error = float(np.max(np.abs(actual - np.stack((low, high)))))
        if error > .2:
            raise ValueError(f"service source bounds differ: {name}: {error}")
        checked.append({"name": name, "kind": kind, "asset": source, "maximum_bounds_difference_mm": round(error, 6)})
    return parts, {"source_authentication": checked, "source_binding_sha256": base.SOURCE_PINS,
                   "counts": {"lights": 132, "wires": 131, "tnuts": 142}}


def inspect(wood: dict, metal: list[tuple[str, str, cq.Shape]], angles: list) -> dict:
    parts, result = service_parts()
    timber_hits, steel_hits = [], []
    bodies = [({"member": name}, shape, shape.BoundingBox()) for name, shape in wood.items()
              if not name.startswith(("main_", "kicker_"))]
    bodies.extend(({"axis": axis, "role": role}, shape, shape.BoundingBox()) for axis, role, shape in metal)
    bodies.extend(({"angle": angle.id}, angle.shape, angle.shape.BoundingBox()) for angle in angles)
    for name, kind, shape in parts:
        a = shape.BoundingBox()
        for identity, body, b in bodies:
            if any(min(getattr(a, x + "max"), getattr(b, x + "max")) -
                   max(getattr(a, x + "min"), getattr(b, x + "min")) < 1e-6 for x in "xyz"):
                continue
            volume = max(0.0, shape.intersect(body).Volume())
            if volume > .01:
                hits = timber_hits if "member" in identity else steel_hits
                hits.append({"service": name, "kind": kind, **identity, "intersection_mm3": round(volume, 4)})
    result.update({"timber_intersections": timber_hits, "metal_intersections": steel_hits,
                   "physical_service_access_qualified": False,
                   "limits": "Native provisional service-body intersections only. Nominal display clearance does not prove bulb extraction, cable feeding, tolerances, hold-bolt access or whole-harness transport."})
    result["counts"].update({"timber_intersections": len(timber_hits), "metal_intersections": len(steel_hits)})
    result["producer_sha256"] = {str(Path(__file__).relative_to(base.ROOT)): base.sha(Path(__file__))}
    return result
