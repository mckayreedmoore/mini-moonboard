"""Check frozen frame contact ports against existing finished timber BREP."""

import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np

from fea.current_response_model import level_face_points
from scripts import thin_bolted_frame_mechanics as mechanics


def main():
    out = mechanics.PACKET / "frame-contact-geometry-v4.json"
    if out.exists():
        raise FileExistsError("preserve contact geometry evidence")
    layout, evidence, pins = mechanics.inputs()
    geometry = mechanics.geometry(layout, evidence)
    cache = json.loads(mechanics.GEOMETRY_CACHE.read_text())
    shapes = {}
    for row in cache["parts"]:
        if row["kind"] == "timber":
            if mechanics.sha(mechanics.ROOT / row["path"]) != row["sha256"]:
                raise ValueError("finished timber differs from exact cache")
            shapes[row["id"]] = cq.Shape.importBrep(str(mechanics.ROOT / row["path"]))
            pins[row["path"]] = row["sha256"]
    contacts = [r for r in mechanics.action_edges(layout, geometry) if r["kind"] == "flange_contact"]
    unsupported_flange = []
    for row in contacts:
        probe = np.array(row["point_xyz_mm"]) - .05 * np.array(row["direction_xyz"])
        if not shapes[row["second"]].isInside(cq.Vector(*probe), 1e-6):
            unsupported_flange.append({"id": row["id"], "receiver": row["second"], "probe_xyz_mm": probe.tolist()})
    finished = {}
    unsupported_floor = []
    for name, old in geometry["floor_footprints"].items():
        finished[name] = [p.tolist() for p in level_face_points(shapes[name], True)]
        center = np.mean(old, axis=0)
        for corner, point in enumerate(old):
            point = np.array(point)
            direction = center - point
            direction[2] = 0.
            direction /= np.linalg.norm(direction)
            probe = point + .05 * direction + [0., 0., .05]
            if not shapes[name].isInside(cq.Vector(*probe), 1e-6):
                unsupported_floor.append({"body": name, "corner": corner, "point_xyz_mm": point.tolist(),
                                          "probe_xyz_mm": probe.tolist()})
    field = mechanics.PACKET / "compatible-frame-a12-rear-v4.json"
    field_report = json.loads(field.read_text())
    for row in unsupported_floor:
        action = next(a for a in field_report["floor_actions"] if a["kind"] == "floor_normal"
                      and a["first"] == row["body"] and a["point_xyz_mm"] == row["point_xyz_mm"])
        row["raw_floor_surrogate_normal_reaction_n"] = action["compression_n"]
    pins[str(mechanics.GEOMETRY_CACHE.relative_to(mechanics.ROOT))] = mechanics.GEOMETRY_CACHE_SHA
    pins[str(Path(__file__).resolve().relative_to(mechanics.ROOT))] = mechanics.sha(Path(__file__))
    pins[str(field.relative_to(mechanics.ROOT))] = mechanics.sha(field)
    pins["scripts/thin_bolted_frame_mechanics.py"] = mechanics.sha(Path(mechanics.__file__))
    pins["fea/current_response_model.py"] = mechanics.sha(mechanics.ROOT / "fea/current_response_model.py")
    report = {
        "schema": "thin_bolted_finished_contact_geometry/v1",
        "candidate": layout["candidate"], "layout_report_sha256": mechanics.LAYOUT_SHA,
        "geometry_cache_sha256": mechanics.GEOMETRY_CACHE_SHA, "source_sha256": pins,
        "command": "OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/frame-contact-audit-v4.py",
        "method": {"cadquery_version": cq.__version__, "recreated_geometry": False,
                   "inside_tolerance_mm": 1e-6, "flange_probe_depth_mm": .05,
                   "floor_probe_xy_inset_and_z_depth_mm": .05,
                   "floor_polygon_method": "level_face_points of exact finished timber BREP"},
        "flange_contact_points": len(contacts), "unsupported_flange_contacts": unsupported_flange,
        "raw_floor_points": sum(len(p) for p in geometry["floor_footprints"].values()),
        "unsupported_raw_floor_points": unsupported_floor,
        "finished_floor_footprints": finished,
        "disposition": "RAW_FLOOR_SURROGATE_REQUIRES_CORRECTION",
        "next_action": "Replace all eight raw floor rectangles with these authenticated finished footprints in the new numerical driver. Preserve the prior field as conditional raw-foot evidence.",
        "limits": ["Global support hull remains unchanged due adjacent runners; individual leg normal/tangential reaction routing changes.",
                   "Supported nominal flange points do not establish actual contact pressure, stiffness or capacity.",
                   "This cached geometry query supplies no material inspection, verified floor or physical release."],
        "release": mechanics.RELEASE,
    }
    out.write_text(json.dumps(report, separators=(",", ":")) + "\n")
    print(json.dumps({"path": str(out), "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
                      "unsupported_floor_points": len(unsupported_floor), "unsupported_flange_points": len(unsupported_flange)}))


if __name__ == "__main__":
    main()
