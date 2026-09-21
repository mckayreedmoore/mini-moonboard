"""Exact extruded plywood outline clearances; no grain or resistance approval."""
import argparse
import hashlib
import json
import math
from pathlib import Path

import cadquery as cq

from . import top_joint_frame
from .profile_clearance import bore_ligament


def report():
    parts = [p for p in top_joint_frame.parts(False)
             if p.name.startswith(("leg_left_", "leg_right_", "cheek_splice_"))]
    rows = []
    for p in parts:
        bounds = p.shape.BoundingBox()
        faces = [f for f in p.shape.Faces() if f.geomType() == "PLANE"
                 and abs(abs(f.normalAt().x)-1) < 1e-8
                 and abs(f.Center().x-bounds.xmin) < 1e-6]
        if len(faces) != 1:
            raise ValueError(f"Expected one planar plywood profile: {p.name}")
        face = faces[0]
        # Reject stepped/nonprismatic stock rather than treating an end face
        # as a sufficient representation of its whole bore path.
        prism = cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), cq.Vector(bounds.xlen, 0, 0))
        difference = prism.Volume()+p.shape.Volume()-2*prism.intersect(p.shape).Volume()
        if abs(difference) > 1e-4:
            raise ValueError(f"Plywood profile does not represent the complete prism: {p.name}")
        holes = []
        for c in top_joint_frame.connections():
            if p.name not in c.members:
                continue
            if abs(abs(c.direction.x)-1) > 1e-8:
                raise ValueError(f"Oblique profile bore requires separate analysis: {c.name}")
            index = c.members.index(p.name)
            diameter = 11.1125 if c.kind == "bolt" else 5.2 if index < len(c.members)-1 else 3.2
            center = cq.Vector(face.Center().x, c.start.y, c.start.z)
            ligament = bore_ligament(face, center, diameter/2)
            holes.append({"connection": c.name, "center_yz_mm": [center.y, center.z],
                          "bore_diameter_mm": diameter,
                          "nearest_profile_boundary_center_distance_mm": ligament+diameter/2,
                          "profile_clear_ligament_mm": ligament})
        for hole in holes:
            neighbors = [(math.dist(hole["center_yz_mm"], other["center_yz_mm"])
                          -(hole["bore_diameter_mm"]+other["bore_diameter_mm"])/2,
                          other["connection"]) for other in holes if other is not hole]
            gap, neighbor = min(neighbors) if neighbors else (None, None)
            rows.append({"member": p.name, **hole, "nearest_other_bore": neighbor,
                         "bore_to_bore_clear_ligament_mm": gap,
                         "loaded_end_or_edge_classification": None})
    return {"variant": top_joint_frame.KEY, "qualified_for_design": False,
            "scope": "Eight independent leg/splice plywood profiles only. Exact prismatic outline and circular perpendicular project bores; does not include head seats, wood grain rules or resistance. Other members remain outside this report.",
            "members": [p.name for p in parts], "positions": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = json.loads(Path("exports/top-joint-development/manifest.json").read_text())["sources"]
    for name in ("profile_clearance", "ply_profile_audit"):
        path = Path("mini_moonboard")/(name+".py")
        sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    def verify():
        for path, digest in sources.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                raise RuntimeError(f"Source differs from exported candidate: {path}")
    verify()
    result = report()
    verify()
    result["sources"] = sources
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
