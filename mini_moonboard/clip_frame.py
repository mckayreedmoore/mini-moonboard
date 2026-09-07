"""Separate +5 mm mid-batten clip inspection; no product or capacity approval.

Official A21 CAD dimensions are reconstructed, not imported manufacturer files.
Screws, heads and tools are provisional envelopes, not regional substitutions.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import hybrid_frame as h
from . import spacing_frame as baseline
from .panel_grid import main_led_datums, main_tnut_datums

KEY = "mid-batten-clip-development"
SHIFT = 5.
THICKNESS = 1.1684
WIDTH = 34.925
LONG = 51.9684
SHORT = 39.2684
HOLE_RADIUS = 2.1717
TANGENT = (b.point(0, 1, 0) - b.point(0, 0, 0)).normalized()


def stations():
    for side, sign in h.SIDES:
        for band, end, s, direction, rail in (
            ("lower", "bottom", 88.9, 1, "panel_edge_bottom"),
            ("lower", "top", 1149.35, -1, "panel_seam_horizontal"),
            ("upper", "bottom", 1289.05, 1, "panel_seam_horizontal"),
            ("upper", "top", 2349.5, -1, "panel_edge_top"),
        ):
            yield f"clip_{band}_{side}_{end}", h.mid_x(sign) + SHIFT - h.EDGE/2, s, direction, f"mid_{band}_{side}", rail


def placed(x, s, direction, u, v, w):
    """Proper rotation of IFC axes; outside faces contact timber, N centred."""
    return b.point(x - w, s - direction*v, 19.05 - direction*u)


def clip_shape(x, s, direction):
    def point(u, v, w):
        return placed(x, s, direction, u, v, w)
    def prism(points, vector):
        wire = cq.Wire.makePolygon([point(*p) for p in points], close=True)
        return cq.Solid.extrudeLinear(wire, [], vector)
    half, tip = WIDTH/2, WIDTH/2 - 6.35
    long = prism([(half, 0, 0), (half, -LONG+6.35, 0), (tip, -LONG, 0),
                  (-tip, -LONG, 0), (-half, -LONG+6.35, 0), (-half, 0, 0)], cq.Vector(-THICKNESS, 0, 0))
    short = prism([(half, 0, 0), (half, 0, SHORT-6.35), (tip, 0, SHORT),
                   (-tip, 0, SHORT), (-half, 0, SHORT-6.35), (-half, 0, 0)], TANGENT * (direction*THICKNESS))
    shape = long.fuse(short).clean()
    for u, v in ((-7.9375, -42.4434), (7.9375, -29.7434)):
        shape = shape.cut(cq.Solid.makeCylinder(HOLE_RADIUS, THICKNESS+2, point(u, v, -1), cq.Vector(-1, 0, 0)))
    for u, w in ((-7.9375, 17.0434), (7.9375, 29.7434)):
        shape = shape.cut(cq.Solid.makeCylinder(HOLE_RADIUS, THICKNESS+2, point(u, 1, w), TANGENT*direction))
    return shape.clean()


@dataclass(frozen=True)
class ClipScrew(b.Connection):
    """Provisional Ø3.75×30 shaft, Ø10×3 pan head; NOT a selected screw."""

    product_status: str = (
        "UNSELECTED SCREW-ENVELOPE EXPLORATION: diameter/length are not a catalog screw selection; "
        "UK A21 N3.75x30 specifies nails, not these screws. No US screw equivalence. "
        "Provisional diameter3.75 length30 headOD10 headheight3; driverOD10 approach25 mm."
    )

    def components(self):
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, self.direction),
                cq.Solid.makeCylinder(5, 3, self.start, -self.direction))


@cache
def connections():
    result = []
    for c in baseline.connections():
        if c.name.startswith("mid_end_"):
            continue
        moved = c.name.startswith(("rib_", "angle_rib_")) and "_mid_" in c.name
        result.append(replace(c, start=c.start+cq.Vector(SHIFT, 0, 0)) if moved else c)
    for name, x, s, direction, batten, rail in stations():
        for i, (u, v) in enumerate(((-7.9375, -42.4434), (7.9375, -29.7434)), 1):
            result.append(ClipScrew(f"{name}_batten_{i}", placed(x, s, direction, u, v, THICKNESS),
                cq.Vector(1, 0, 0), 30., 3.75, (name, batten)))
        for i, (u, w) in enumerate(((-7.9375, 17.0434), (7.9375, 29.7434)), 1):
            result.append(ClipScrew(f"{name}_rail_{i}", placed(x, s, direction, u, -THICKNESS, w),
                -TANGENT*direction, 30., 3.75, (name, rail)))
    return tuple(result)


@cache
def parts(drilled=True):
    raw = {p.name: p for p in baseline.parts(False)}
    moved = {n for n in raw if n.startswith("mid_") or (n.startswith(("rib_", "angle_rib_")) and "_mid_" in n)}
    for name in moved:
        raw[name] = replace(raw[name], shape=raw[name].shape.translate((SHIFT, 0, 0)))
    for name, x, s, direction, _, _ in stations():
        raw[name] = b.Part(name, clip_shape(x, s, direction), (LONG, SHORT, WIDTH),
            "PROVISIONAL official A21 CAD outline; sharp bend, no manufacturing tolerances; "
            "not regional product equivalence or capacity; four provisional pan-head screw envelopes", 1)
    if not drilled:
        return tuple(raw.values())
    old = {c.name: c for c in baseline.connections()}
    rebuilt = moved | {member for c in baseline.connections() if c.name.startswith("mid_end_") for member in c.members}
    rebuilt |= {member for c in connections() if c.name not in old or c is not old[c.name] for member in c.members}
    result = {p.name: p for p in baseline.parts()}
    for name in rebuilt:
        part = raw[name]
        shape = part.shape
        if name.startswith(("mid_", "panel_")):
            for u, s in (*main_tnut_datums().values(), *main_led_datums().values()):
                shape = shape.cut(cq.Solid.makeCylinder(20, b.THICKNESS+2, b.point(u-b.HALF, s, -1), b.normal()))
        result[name] = replace(part, shape=shape)
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in rebuilt or name.startswith("clip_"):
                continue
            part = result[name]
            radius = 5 if c.kind == "bolt" else (2.6 if index == 0 else 1.6)
            shape = part.shape.cut(cq.Solid.makeCylinder(radius, c.length+2, c.start-c.direction, c.direction))
            if c.kind == "screw" and index == 0:
                shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape)
    return tuple(result.values())
