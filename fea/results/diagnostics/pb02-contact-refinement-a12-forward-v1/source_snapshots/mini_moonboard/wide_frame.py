"""Wider principals resolve a bolt-edge geometry defect, not joint capacity."""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from . import insert_frame as insert
from . import timber_connections as hardware
from . import timber_frame as timber
from .bolted_frame import WASHER

KEY = "wide-principal-development"
UPRIGHTS = {"left": (-127., -38.1), "right": (0., 88.9)}
CENTERS = {side: sum(bounds)/2 for side, bounds in UPRIGHTS.items()}
POST_Y = {"front": (-175.7, -36.), "rear": (-321.75, -182.05)}
LIMITS = "Wider-principal development; bearing and connections unqualified; NOT build-ready"
PanelMachineScrew = insert.PanelMachineScrew
INSERT, SCREW, ASSUMPTIONS, PANEL = insert.INSERT, insert.SCREW, insert.ASSUMPTIONS, insert.PANEL


def stations():
    for name, origin, u, v, beam, upright in hardware.stations(True):
        if "header_center_" in name:
            side = "left" if name.endswith("left") else "right"
            x = UPRIGHTS[side][0 if side == "left" else 1]
            for end, (y0, y1) in POST_Y.items():
                yield (name+"_"+end, cq.Vector(x, (y0+y1)/2, origin.z), u, v,
                       beam, upright+"_"+end)
        else:
            if upright.startswith("base_principal_"):
                origin = origin+cq.Vector(-50.8 if upright.endswith("left") else 50.8, 0, 0)
            yield name, origin, u, v, beam, upright


@cache
def connections():
    result = list(hardware.clip_connections(tuple(stations())))
    for c in insert.connections():
        if c.name.startswith("clip_"):
            continue
        side = "left" if "left" in c.name else "right"
        old_x = -57.15 if side == "left" else 19.05
        if abs(c.start.x-old_x) < 1e-6 and (
                isinstance(c, PanelMachineScrew) or c.name.startswith("timber_backing_bolt_")):
            members = tuple(n+"_front" if n == f"base_post_center_{side}" else n for n in c.members)
            c = replace(c, start=cq.Vector(CENTERS[side], c.start.y, c.start.z), members=members)
        result.append(c)
    return tuple(result)


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, PanelMachineScrew))


@cache
def wood_parts(drilled=True):
    result = {p.name: p for p in timber.wood_parts(drilled)}
    bottom = result["timber_bottom_backing"].shape
    # Use the uninterrupted housing tool, not a service-pocketed receiver.
    housing = b.block(-base.INNER_EDGE, base.INNER_EDGE, 0., 88.9, 0., 38.1)
    cutters = timber.service_envelopes() if drilled else ()
    for side, (x0, x1) in UPRIGHTS.items():
        name = f"base_principal_{side}"
        shape, blank = base._sloped_bearing_member(x0, x1, 139.7, b.LENGTH-38.1)
        shape = shape.cut(housing)
        for cutter in cutters:
            shape = shape.cut(cutter)
        result[name] = b.Part(name, shape.clean(), blank,
            "Nominal 4x6 kiln-dried No.2 fir/larch, actual 88.9 x139.7; housed front; "+LIMITS, 1)
        del result[f"base_post_center_{side}"]
        for end, (y0, y1) in POST_Y.items():
            name = f"base_post_center_{side}_{end}"
            result[name] = b.Part(name, base._world_box(x0, x1, y0, y1, 0., base.HEADER_BOTTOM),
                (base.HEADER_BOTTOM, 139.7, 88.9),
                "Vertical-grain 4x6 offcut; paired posts leave 6.35 mm gap beneath header; "+LIMITS, 1)
        for level in ("lower", "upper"):
            name = f"base_rail_mid_{level}_{side}"
            p = result[name]
            xa, xb = (-base.INNER_EDGE, x0) if side == "left" else (x1, base.INNER_EDGE)
            s0, s1 = (b.HALF-38.1, b.HALF) if level == "lower" else (b.HALF, b.HALF+38.1)
            result[name] = replace(p, shape=p.shape.intersect(b.block(xa, xb, s0, s1, 0., 139.7)).clean(),
                                   blank=(xb-xa, 139.7, 38.1))
    assert result["timber_bottom_backing"].shape is bottom
    return tuple(result.values())


@cache
def parts(drilled=True):
    result = {p.name: p for p in wood_parts(drilled)}
    result.update({p.name: p for p in hardware.clip_parts(tuple(stations()))})
    # Keep machining policy local: historical source closures remain unchanged.
    for c in connections():
        if isinstance(c, PanelMachineScrew):
            if drilled:
                panel, receiver = c.members
                shape = result[panel].shape.cut(cq.Solid.makeCylinder(
                    ASSUMPTIONS["panel_clearance_bore_diameter"]/2, PANEL+2,
                    c.start-c.direction, c.direction)).cut(c.components()[1])
                result[panel] = replace(result[panel], shape=shape.clean())
                tolerance = INSERT["drawing_general_tolerance_plus_minus"]
                envelope = cq.Solid.makeCylinder((INSERT["nominal_outer_diameter"]+tolerance)/2,
                    INSERT["nominal_length"]+tolerance, c.insert_start, c.direction)
                pilot = cq.Solid.makeCylinder(INSERT["pilot_diameter_inch_recommendation"]/2,
                    ASSUMPTIONS["pilot_tip_clearance_depth"], c.insert_start, c.direction)
                result[receiver] = replace(result[receiver],
                    shape=result[receiver].shape.cut(envelope).cut(pilot).clean())
            name = "insert_"+c.name
            result[name] = b.Part(name, c.insert_shape(),
                (INSERT["nominal_length"], INSERT["nominal_outer_diameter"], INSERT["nominal_outer_diameter"]),
                "E-Z LOK 801420-13 nominal insert envelope; "+LIMITS, 1)
            continue
        if not drilled:
            continue
        for index, name in enumerate(c.members):
            if name.startswith("clip_"):
                continue
            p = result[name]
            diameter = 11.1125 if c.kind == "bolt" else c.diameter
            shape = p.shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2,
                c.start-c.direction, c.direction))
            if index == 0 and c.kind == "screw":
                shape = shape.cut(c.components()[1])
            if name == "timber_bottom_backing" and c.name.startswith("timber_backing_bolt_"):
                shape = shape.cut(cq.Solid.makeCylinder(28.575/2, 10.+WASHER,
                    c.start-b.normal()*10., b.normal()))
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
