"""Continuous rails with lower end bearing and purchased-angle retention.

Development geometry only: actual factory fit and connection capacity unqualified.
The source-bound continuous predecessor remains unchanged.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import bracket_mvp as bracket
from . import continuous_frame as baseline
from . import wood_mvp as wood

KEY = "bearing-lean-frame"
RAIL_SHIFT_MM = 1.6
LOWER_STATION_MM = 101.6
LEDGE_CLIP_X_MM = (-919.2, -519.2, 480.8, 880.8)
TANGENT = bracket.TANGENT


def ledge_connector(x):
    """Rigidly rotate the existing ML24Z proxy; do not alter factory steel."""
    axis = cq.Vector(1, 0, 0)+b.normal()
    origin = b.point(x, LOWER_STATION_MM, 38.1)
    shape, holes = bracket._connector(cq.Vector(), cq.Vector(1, 0, 0), TANGENT)
    # 180 degrees exchanges X/N and reverses S: width X, legs rear/downhill.
    transform = lambda v: b.normal()*v.x-TANGENT*v.dot(TANGENT)+cq.Vector(1, 0, 0)*v.dot(b.normal())
    return (shape.rotate((0, 0, 0), axis.toTuple(), 180).translate(origin),
            [(suffix.replace("upright_", "ledge_"), origin+transform(start), transform(direction))
             for suffix, start, direction in holes])


@cache
def connections():
    result = []
    for c in baseline.connections():
        if c.name.startswith("lean_lower_ledge_"):
            continue
        if c.name.startswith("clip_mvp_lean_lower_"):
            c = replace(c, start=c.start+TANGENT*RAIL_SHIFT_MM)
        result.append(c)
    for index, x in enumerate(LEDGE_CLIP_X_MM, 1):
        name = f"clip_mvp_ledge_{index}"
        _, holes = ledge_connector(x)
        for suffix, start, direction in holes:
            receiver = "lean_beam_lower_full" if suffix.startswith("beam_") else "wood_rail_lower"
            result.append(bracket.ConnectorScrew(f"{name}_{suffix}", start, direction,
                38.1, 6.35, (name, receiver)))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False)}
    for name, p in tuple(result.items()):
        if name == "lean_beam_lower_full" or name.startswith("clip_mvp_lean_lower_"):
            result[name] = replace(p, shape=p.shape.translate(TANGENT*RAIL_SHIFT_MM))
        if name.startswith("lean_edge_") and name.endswith("_lower"):
            # Retain the original angle-to-infill butt clearance after the shift.
            result[name] = replace(p,
                shape=p.shape.cut(b.block(-b.HALF, b.HALF, 188.9, 190.5, -1., 90.)).clean(),
                blank=(p.blank[0]-RAIL_SHIFT_MM, *p.blank[1:]),
                description=p.description+"; lower end shortened 1.6mm to clear relocated angle")
    rail = result["lean_beam_lower_full"]
    result[rail.name] = replace(rail, description=rail.description+
        "; shifted uphill 1.6mm for central upright end bearing; added ledge angles unqualified")
    for index, x in enumerate(LEDGE_CLIP_X_MM, 1):
        name = f"clip_mvp_ledge_{index}"
        shape, _ = ledge_connector(x)
        result[name] = b.Part(name, shape, (101.6, 50.8, 50.8),
            "Purchased ML24Z lower-ledge angle, width across board; six separately purchased SDS25112 screws. "
            "Rigidly rotated PROVISIONAL factory geometry; not steel fabrication instructions; "
            "fit, tool access and mixed-direction resistance unqualified", 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
