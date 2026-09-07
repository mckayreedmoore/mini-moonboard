"""Separate selected-product fit model; not machining or structural approval.

Freeze the predecessor's backing datums. Category face thickness and product
envelopes are explicit, while pilots, head seats and the US clip proxy remain
unqualified. No old fastener bores are reused.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import transition_frame as baseline
from .model import _v1_kicker_holes, _v1_main_panel_holes
from .panel_grid import main_led_datums, main_tnut_datums
from .product_connections import selected_connection
from .selected_hardware import SD9112, SDS25112, BoltSpec, spec_for

KEY = "selected-hardware-development"
FACE_THICKNESS_MM = 23 / 32 * 25.4  # Category dimension, not measured stock.
REFERENCE_FACE_THICKNESS_MM = 18.
KICKER_BACK_Y_MM = -36.
BOLT_HOLE_DIAMETER_MM = 11.1125  # Project 7/16 in hole, not a supplier instruction.
R4_CLEARANCE_DIAMETER_MM = 5.2
R4_PILOT_DIAMETER_MM = 3.2
SD_PILOT_DIAMETER_MM = 3.2
SDS_STEEL_HOLE_DIAMETER_MM = 7.
SDS_PILOT_DIAMETER_MM = 4.
TANGENT = (b.point(0, 1, 0) - b.point(0, 0, 0)).normalized()
LIMITS = ("Selected-product fit candidate, unqualified; project bores/pilots and head-seat envelopes "
          "are NOT machining instructions or structural approval; no capacity credit")


@cache
def connections():
    result = []
    for old in baseline.connections():
        c = selected_connection(old)
        if old.members[0].startswith("main_") or old.members[0] in ("kicker_left", "kicker_right"):
            c = replace(c, start=c.start-c.direction*(FACE_THICKNESS_MM-REFERENCE_FACE_THICKNESS_MM))
        result.append(c)
    return tuple(result)


def _bore(shape, diameter, length, start, direction):
    return shape.cut(cq.Solid.makeCylinder(diameter/2, length, start, direction))


def _backing_reliefs(part):
    shape = part.shape
    if part.name.startswith(("panel_", "mid_")):
        points = [v.Center() for v in shape.Vertices()]
        xs = [p.x for p in points]
        ss = [(p-b.point(0, 0, 0)).dot(TANGENT) for p in points]
        for u, s in (*main_tnut_datums().values(), *main_led_datums().values()):
            x = u-b.HALF
            if min(xs)-20 < x < max(xs)+20 and min(ss)-20 < s < max(ss)+20:
                shape = _bore(shape, 40., b.THICKNESS+2, b.point(x, s, -1), b.normal())
    elif part.name.startswith("kicker_batten_"):
        for u, s in main_led_datums().values():
            if s < 0:
                shape = _bore(shape, 40., b.THICKNESS+2,
                    cq.Vector(u-b.HALF, -35, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, -1, 0))
    return shape


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False)}
    for row, band in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            name = f"main_{band}_{side}"
            x0, s0 = (col-1)*b.HALF, row*b.HALF
            shape = b.block(x0, x0+b.HALF, s0, s0+b.HALF, -FACE_THICKNESS_MM, 0)
            result[name] = replace(result[name], shape=shape,
                blank=(b.HALF, b.HALF, FACE_THICKNESS_MM),
                description="23/32 CAT face plywood; fixed backplane N=0; category not measured thickness; "+LIMITS)
    for col, side in enumerate(("left", "right")):
        name = f"kicker_{side}"
        shape = cq.Solid.makeBox(b.HALF, FACE_THICKNESS_MM, b.V1_KICKER_HEIGHT_MM,
            cq.Vector((col-1)*b.HALF, KICKER_BACK_Y_MM, 0))
        # Explicit local seam trim: thicker faces at fixed backing planes would
        # overlap at the old square seam. Preserve the main panel/grid and floor.
        shape = shape.cut(result[f"main_lower_{side}"].shape).clean()
        result[name] = replace(result[name], shape=shape,
            blank=(b.HALF, b.V1_KICKER_HEIGHT_MM, FACE_THICKNESS_MM),
            description="23/32 CAT kicker; fixed Y=-36 backplane; top locally trimmed against main face, "
            "STEP seam profile governs; category not measured thickness; "+LIMITS)
    for name, part in list(result.items()):
        if name.startswith("clip_"):
            result[name] = replace(part, description="US A21 selected with SD9112; UNVERIFIED UK hole/bend "
                "geometry proxy retained unaltered; not US production geometry or rated installation; "+LIMITS)
    if not drilled:
        return tuple(result.values())

    for row, band in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            name = f"main_{band}_{side}"
            shape = result[name].shape
            for x, s, diameter in _v1_main_panel_holes(col, row):
                shape = _bore(shape, diameter, FACE_THICKNESS_MM+2,
                    b.point(x+(col-.5)*b.HALF, s+row*b.HALF, -FACE_THICKNESS_MM-1), b.normal())
            result[name] = replace(result[name], shape=shape.clean())
    for col, side in enumerate(("left", "right")):
        name = f"kicker_{side}"
        shape = result[name].shape
        for x, z, diameter in _v1_kicker_holes(col):
            shape = _bore(shape, diameter, FACE_THICKNESS_MM+2,
                cq.Vector(x+(col-.5)*b.HALF, KICKER_BACK_Y_MM-1, z), cq.Vector(0, 1, 0))
        result[name] = replace(result[name], shape=shape.clean())
    for name, part in list(result.items()):
        result[name] = replace(part, shape=_backing_reliefs(part).clean())

    for c in connections():
        spec = spec_for(c)
        for index, name in enumerate(c.members):
            if name.startswith("clip_"):
                continue  # Never modify the purchased-connector hole proxy.
            if isinstance(spec, BoltSpec):
                diameter = BOLT_HOLE_DIAMETER_MM
            elif spec is SD9112:
                diameter = SD_PILOT_DIAMETER_MM
            elif spec is SDS25112:
                diameter = SDS_STEEL_HOLE_DIAMETER_MM if index == 0 else SDS_PILOT_DIAMETER_MM
            else:
                # Splice has two independent side plies; only its final member
                # is the receiving wood. Clearance through both side plies.
                diameter = R4_CLEARANCE_DIAMETER_MM if index < len(c.members)-1 else R4_PILOT_DIAMETER_MM
            part = result[name]
            shape = _bore(part.shape, diameter, c.length+2, c.start-c.direction, c.direction)
            if not isinstance(spec, BoltSpec) and spec.seating == "flush" and index == 0:
                shape = shape.cut(c.components()[1])  # Assumed reserved seat volume, not a real countersink.
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())
