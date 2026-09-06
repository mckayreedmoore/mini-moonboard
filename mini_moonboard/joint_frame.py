"""Separate backing-joint development geometry; NOT a rated connection design.

Stock, steel fabrication, fastener products and resistance remain open. Reuse
the foot100 baseline without mutating its shapes, connections or publications.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import footprint_frame as baseline
from . import hybrid_frame as h
from . import shallow_frame as shallow
from .panel_grid import main_led_datums, main_tnut_datums

RIB_WIDTH = 63.5
RIB_LENGTH = 300.0
ANGLE_LENGTH = 180.0
SEAM_CENTER = 54.0
SEAM_WIDTH = 165.1
RIB_FRONT = b.THICKNESS
RIB_REAR = shallow.REAR - shallow.BEAM_DEPTH


def stations():
    for row, s in enumerate(b.CROSS_STATIONS, 1):
        for label, x in (("seam_left", -SEAM_CENTER), ("seam_right", SEAM_CENTER),
                         ("mid_left", h.mid_x(-1)), ("mid_right", h.mid_x(1))):
            yield row, label, x, s


@cache
def connections():
    old = {c.name: c for c in baseline.connections()}
    result = {name: c for name, c in old.items()
              if not name.startswith(("rib_", "angle_rib_"))}
    for row, label, x, s in stations():
        rib = f"rib_{row}_{label}"
        angle = "angle_" + rib
        sign = -1 if x < 0 else 1
        edge = x + sign * RIB_WIDTH / 2
        front = old[rib + "_front"]
        offset = 30.0 if label == "seam_left" and row != 2 else 0.0
        result[front.name] = replace(front, start=b.point(x, s+offset, 0))
        # Stagger the opposing seam nuts: their access envelopes must not be
        # treated as empty space simply because the timber bodies are separate.
        spacing = 70.0 if label == "seam_left" else 35.0
        for j, offset in enumerate((-spacing, spacing), 1):
            name = f"{angle}_rib_{j}"
            result[name] = replace(old[name],
                start=b.point(edge + sign * (h.STEEL + 2), s + offset,
                              (RIB_FRONT + RIB_REAR) / 2),
                length=88.9, grip=RIB_WIDTH + h.STEEL)
        for j, dx in enumerate((38.0, 66.0), 1):
            name = f"{angle}_beam_{j}"
            result[name] = replace(old[name],
                start=b.point(edge + sign * dx, s, shallow.REAR + 2))
    return tuple(result.values())


@cache
def parts(drilled=True):
    # Start from undrilled bodies so relocated holes do not leave phantom bores.
    result = {p.name: p for p in baseline.parts(100, False)}
    for band, s0, s1 in (("lower", h.EDGE, b.HALF-h.SEAM/2),
                         ("upper", b.HALF+h.SEAM/2, b.LENGTH-h.EDGE)):
        name = "panel_seam_vertical_" + band
        result[name] = b.Part(name,
            b.block(-SEAM_WIDTH/2, SEAM_WIDTH/2, s0, s1, 0, b.THICKNESS),
            (s1-s0, SEAM_WIDTH, b.THICKNESS),
            "DEVELOPMENT: graded 2x8 ripped to 165.1 mm; wider seam batten "
            "permits separated rib nuts and nominal socket access", 1)
    for row, label, x, s in stations():
        rib = f"rib_{row}_{label}"
        shape = b.block(x - RIB_WIDTH / 2, x + RIB_WIDTH / 2,
                        s - RIB_LENGTH / 2, s + RIB_LENGTH / 2, RIB_FRONT, RIB_REAR)
        # Open front-edge chases preserve the existing 11 x 2 mm wire corridors
        # with 2 mm lateral and 4 mm rear allowance. They reduce bearing area;
        # the resulting net section, not the rectangular blank, governs analysis.
        for wire_x in {u-b.HALF for u, _ in main_led_datums().values()}:
            if x-RIB_WIDTH/2 < wire_x+7.5 and wire_x-7.5 < x+RIB_WIDTH/2:
                shape = shape.cut(b.block(wire_x-7.5, wire_x+7.5,
                    s-RIB_LENGTH/2-1, s+RIB_LENGTH/2+1, RIB_FRONT-1, 56)).clean()
        result[rib] = b.Part(rib, shape, (RIB_LENGTH, RIB_REAR-RIB_FRONT, RIB_WIDTH),
            "DEVELOPMENT: solid graded stock, grain along board slope; "
            "63.5 x 89.95 x 300 mm blank with wire chase where required; "
            "no glue credit; material/product unresolved", 1)
        sign = -1 if x < 0 else 1
        edge = x + sign * RIB_WIDTH / 2
        x0, x1 = sorted((edge, edge + sign * 80))
        sx0, sx1 = sorted((edge, edge + sign * h.STEEL))
        angle = b.block(x0, x1, s-ANGLE_LENGTH/2, s+ANGLE_LENGTH/2,
                        RIB_REAR-h.STEEL, RIB_REAR).fuse(
            b.block(sx0, sx1, s-ANGLE_LENGTH/2, s+ANGLE_LENGTH/2,
                    RIB_REAR-80, RIB_REAR-h.STEEL)).clean()
        name = "angle_" + rib
        result[name] = b.Part(name, angle, (180., 80., 80.),
            "DEVELOPMENT: custom 80 x 80 x 6 mm angle, 180 mm long; "
            "sharp-corner envelope, fabrication and resistance unresolved", 1)
    if drilled:
        # Unchanged bodies keep their original hardware reliefs. Only the front
        # battens need rebuilding, because their rib screw locations moved.
        bored = {p.name: p for p in baseline.parts(100, True)}
        changed_battens = {c.members[0] for c in connections()
                           if c.name.startswith("rib_")}
        changed_timber = changed_battens | {f"rear_cross_{row}" for row in range(1, 4)}
        for name in result:
            if not name.startswith(("rib_", "angle_rib_")) and name not in changed_timber:
                result[name] = bored[name]
        for name in changed_battens:
            p = result[name]
            shape = p.shape
            for x, s in (*main_tnut_datums().values(), *main_led_datums().values()):
                shape = shape.cut(cq.Solid.makeCylinder(20, b.THICKNESS+2,
                    b.point(x-b.HALF, s, -1), b.normal()))
            result[name] = replace(p, shape=shape)
        rebuilt = changed_timber | {name for name in result
                                   if name.startswith(("rib_", "angle_rib_"))}
        for c in connections():
            for i, name in enumerate(c.members):
                if name not in rebuilt:
                    continue
                p = result[name]
                radius = 5 if c.kind == "bolt" else (2.6 if i == 0 else 1.6)
                shape = p.shape.cut(cq.Solid.makeCylinder(radius, c.length+2,
                                                         c.start-c.direction, c.direction))
                if c.kind == "screw" and i == 0:
                    shape = shape.cut(c.components()[1])
                result[name] = replace(p, shape=shape)
    return tuple(result.values())
