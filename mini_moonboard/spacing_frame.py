"""Separate screw-spacing geometry experiment; no selected products or capacity.

Preserve the independent leg plies/stitches and rebuild moved joint receivers
from undrilled stock. Published predecessor candidates remain unchanged.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import independent_leg_frame as baseline
from . import joint_frame as joint
from .panel_grid import main_led_datums, main_tnut_datums

KEY = "screw-spacing-development"


def seam_stations():
    """Row, side, X, centre S, rib length, front offset, rear bolt offset."""
    for row, s in enumerate(b.CROSS_STATIONS, 1):
        for side, sign in (("left", -1), ("right", 1)):
            if row == 2:
                yield row, side, sign * 76., s, 300., 0., 70. if side == "left" else 35.
            else:
                yield (row, side, sign * 54., s,
                       350. if side == "left" else 420.,
                       -70. if side == "left" else 105.,
                       35. if side == "left" else 70.)


@cache
def connections():
    result = {c.name: c for c in baseline.connections()}
    for row, side, x, s, _, front_offset, bolt_offset in seam_stations():
        rib = f"rib_{row}_seam_{side}"
        sign = -1 if side == "left" else 1
        dx = x - sign * joint.SEAM_CENTER
        front = result[rib + "_front"]
        result[front.name] = replace(front, start=b.point(x, s + front_offset, 0))
        for index, offset in enumerate((-bolt_offset, bolt_offset), 1):
            name = f"angle_{rib}_rib_{index}"
            old = result[name]
            result[name] = replace(old, start=b.point(old.start.x + dx, s + offset,
                (joint.RIB_FRONT + joint.RIB_REAR) / 2))
        if dx:
            for index in (1, 2):
                name = f"angle_{rib}_beam_{index}"
                old = result[name]
                result[name] = replace(old, start=old.start + cq.Vector(dx, 0, 0))
    return tuple(result.values())


@cache
def parts(drilled=True):
    if not drilled:
        result = {p.name: p for p in baseline.parts(False)}
        for row, side, x, s, length, _, _ in seam_stations():
            rib = f"rib_{row}_seam_{side}"
            shape = b.block(x - joint.RIB_WIDTH / 2, x + joint.RIB_WIDTH / 2,
                            s - length / 2, s + length / 2, joint.RIB_FRONT, joint.RIB_REAR)
            for wire_x in {u - b.HALF for u, _ in main_led_datums().values()}:
                if x - joint.RIB_WIDTH / 2 < wire_x + 7.5 and wire_x - 7.5 < x + joint.RIB_WIDTH / 2:
                    shape = shape.cut(b.block(wire_x - 7.5, wire_x + 7.5,
                        s - length / 2 - 1, s + length / 2 + 1, joint.RIB_FRONT - 1, 56)).clean()
            result[rib] = b.Part(rib, shape, (length, joint.RIB_REAR - joint.RIB_FRONT, joint.RIB_WIDTH),
                f"PROVISIONAL solid rib, grain along S; 63.5 x 89.95 x {length:g} mm blank; "
                "net wire chase where required; no glue credit; material, products and capacity unresolved", 1)
            if row == 2:
                name = "angle_" + rib
                angle = result[name]
                dx = x - (-joint.SEAM_CENTER if side == "left" else joint.SEAM_CENTER)
                result[name] = replace(angle, shape=angle.shape.translate((dx, 0, 0)))
        return tuple(result.values())

    old = {c.name: c for c in baseline.connections()}
    rebuilt = {name for c in connections() if c is not old[c.name] for name in c.members}
    result = {p.name: p for p in baseline.parts()}
    undrilled = {p.name: p for p in parts(False)}
    for name in rebuilt:
        part = undrilled[name]
        shape = part.shape
        if name.startswith("panel_seam_"):
            for x, s in (*main_tnut_datums().values(), *main_led_datums().values()):
                shape = shape.cut(cq.Solid.makeCylinder(20, b.THICKNESS + 2,
                    b.point(x - b.HALF, s, -1), b.normal()))
        result[name] = replace(part, shape=shape)
    for c in connections():
        for index, name in enumerate(c.members):
            if name not in rebuilt:
                continue
            part = result[name]
            radius = 5 if c.kind == "bolt" else (2.6 if index == 0 else 1.6)
            shape = part.shape.cut(cq.Solid.makeCylinder(radius, c.length + 2,
                c.start - c.direction, c.direction))
            if c.kind == "screw" and index == 0:
                shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape)
    return tuple(result.values())
