"""Export CAD timber crops with primary bolt bores; secondary holes omitted."""
import json
import math
from pathlib import Path

import cadquery as cq

from mini_moonboard.box_frame import (
    BOLT_HOLE_RADIUS_MM,
    CROSS_STATIONS,
    DEPTH,
    HALF,
    LEG_NORMAL,
    LEG_STATIONS,
    THICKNESS,
    block,
    connections,
    frame_parts,
    point,
)
from mini_moonboard.model import ANGLE_FROM_VERTICAL_DEG


def main():
    directory = Path("fea/generated")
    directory.mkdir(parents=True, exist_ok=True)
    parts = {p.name: p.shape for p in frame_parts(drilled=False)}
    seat_s = CROSS_STATIONS[0]
    angle = math.radians(ANGLE_FROM_VERTICAL_DEG)
    origin = point(0,0,0)
    seat_bolts = [c for c in connections() if c.name.startswith("analysis_seat_bolt_right_1_")]
    seat_stations = sorted((c.start-origin).dot(cq.Vector(0,math.sin(angle),math.cos(angle))) for c in seat_bolts)
    definitions = [
        ("leg_wall", "box_side_right", 1480, 1880, LEG_STATIONS, LEG_NORMAL),
        ("leg_member", "leg_right", 1480, 1880, LEG_STATIONS, LEG_NORMAL),
        ("seat_wall", "box_side_right", seat_s-155, seat_s+155, seat_stations, DEPTH-100),
        ("seat_member", "cross_seat_right_1", seat_s-55, seat_s+55, seat_stations, DEPTH-100),
    ]
    records = []
    for name, member, low, high, stations, n in definitions:
        shape = parts[member].intersect(block(HALF-THICKNESS-1, HALF+2*THICKNESS+1, low, high, -18, DEPTH+1)).clean()
        for station in stations:
            shape = shape.cut(cq.Solid.makeCylinder(BOLT_HOLE_RADIUS_MM, 3*THICKNESS+2, point(HALF-THICKNESS-1,station,n), cq.Vector(1,0,0))).clean()
        if not shape.isValid() or len(shape.Solids()) != 1:
            raise ValueError(f"Invalid joint crop: {name}")
        cq.exporters.export(shape, str(directory/f"joint_{name}.step"))
        records.append({"name": name, "member": member, "clamp_s_mm": low, "stations_mm": list(stations), "normal_mm": n,
                            "hole_radius_mm": BOLT_HOLE_RADIUS_MM, "angle_deg": ANGLE_FROM_VERTICAL_DEG,
                            "thickness_mm": THICKNESS, "origin_mm": point(0, 0, 0).toTuple()})
    (directory/"joints.json").write_text(json.dumps(records, indent=2)+"\n")


if __name__ == "__main__":
    main()
