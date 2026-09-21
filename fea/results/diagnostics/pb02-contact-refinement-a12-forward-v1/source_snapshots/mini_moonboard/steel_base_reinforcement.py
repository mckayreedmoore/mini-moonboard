"""Provisional fabricated steel shoes for the outer rim/header connections.

This separate development candidate replaces two ML24Z angles and twelve SDS
screws with two welded A36 shoes and sixteen complete A307 bolt stacks. It
explicitly raises each rim's bearing cut by the shoe plate thickness. Welds,
steel/wood resistance and actual hardware procurement are not qualified.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import round_structural_frame as previous
from .bolted_frame import WASHER
from .split_center_hardware import HexFrameBolt

KEY = 'steel-base-development'
LIMITS = ('Provisional fabricated A36 steel shoes, 3/8-inch plates and 6 mm external '
          'fillet weld; new A307 3/8-inch bolt groups; geometry only, not released fabrication '
          'or connection resistance; original structural-screw candidate preserved')
THICKNESS = 9.525
BEARING_PLATE_THICKNESS = 6.35
BEARING_PLATE_WIDTH = 32.
STEEL_HOLE_DIAMETER = 11.1125
WOOD_HOLE_DIAMETER = 11.1125
WELD_LEG = 6.
RIM_STATIONS = (170., 230.)
RIM_NORMAL_OFFSETS = (45., 100.)
HEADER_X_MAGNITUDES = (1060., 1110.)
HEADER_Y = (-210., -80.)
FOOT_INBOARD_X = 1035.
FOOT_OUTBOARD_X = 1240.
FOOT_Y = (-245., -32.)
WEB_NORMAL_RANGE = (20., 125.)
WEB_TOP_STATION = 280.
GRIP = THICKNESS+38.1+BEARING_PLATE_THICKNESS
BOLT_LENGTH = 76.2


def __getattr__(name):
    return getattr(previous, name)


def stations():
    return tuple(s for s in previous.stations() if not s[0].startswith('clip_angle_base_'))


@cache
def added_connections():
    result = []
    for side, sign in (('left', -1.), ('right', 1.)):
        shoe = 'clip_steel_shoe_'+side
        for index, (s, n) in enumerate(((s, n) for s in RIM_STATIONS
                                       for n in RIM_NORMAL_OFFSETS), 1):
            name = f'steel_shoe_rim_{side}_{index}'
            start = previous.b.point(sign*(previous.b.HALF+THICKNESS+WASHER), s, n)
            result.append(HexFrameBolt(name, start, cq.Vector(-sign, 0, 0),
                BOLT_LENGTH, 9.525, (shoe, 'base_side_'+side, 'clip_plate_'+name),
                'bolt', GRIP, product_status=LIMITS+'; provisional A307 Grade A 3/8-16 x3in, '
                'A563 Grade A nut, two existing maximum-envelope SAE washers, 32mm square bearing plate'))
        for index, (x, y) in enumerate(((x, y) for x in HEADER_X_MAGNITUDES
                                       for y in HEADER_Y), 1):
            name = f'steel_shoe_header_{side}_{index}'
            start = cq.Vector(sign*x, y, previous.base.HEADER_TOP+THICKNESS+WASHER)
            result.append(HexFrameBolt(name, start, cq.Vector(0, 0, -1),
                BOLT_LENGTH, 9.525, (shoe, 'base_header', 'clip_plate_'+name),
                'bolt', GRIP, product_status=LIMITS+'; provisional A307 Grade A 3/8-16 x3in, '
                'A563 Grade A nut, two existing maximum-envelope SAE washers, 32mm square bearing plate'))
    return tuple(result)


def connections():
    return tuple(c for c in previous.connections()
                 if not c.name.startswith('clip_angle_base_'))+added_connections()


def trim_bearing_ends(parts):
    result = []
    cut_top = previous.base.HEADER_TOP+THICKNESS
    cutter = cq.Solid.makeBox(3000., 3000., cut_top+100., cq.Vector(-1500., -500., -100.))
    for p in parts:
        if p.name in ('base_side_left', 'base_side_right'):
            p = replace(p, shape=p.shape.cut(cutter).clean(),
                        description=p.description+'; bearing end trimmed upward 9.525mm for steel shoe; '+LIMITS)
        result.append(p)
    return tuple(result)


@cache
def uncut_wood_parts():
    return trim_bearing_ends(previous.uncut_wood_parts())


@cache
def wood_parts():
    return trim_bearing_ends(previous.wood_parts())


@cache
def steel_parts():
    result = []
    z = previous.base.HEADER_TOP
    for side, sign in (('left', -1.), ('right', 1.)):
        a, b = sorted((sign*FOOT_INBOARD_X, sign*FOOT_OUTBOARD_X))
        foot = cq.Solid.makeBox(b-a, FOOT_Y[1]-FOOT_Y[0], THICKNESS,
                               cq.Vector(a, FOOT_Y[0], z))
        a, b = sorted((sign*previous.b.HALF, sign*(previous.b.HALF+THICKNESS)))
        web = previous.b.block(a, b, -250., WEB_TOP_STATION, *WEB_NORMAL_RANGE)
        web = web.cut(cq.Solid.makeBox(3000., 3000., z+THICKNESS+100.,
                                      cq.Vector(-1500., -500., -100.))).clean()
        # One continuous EXTERNAL fillet avoids intruding into the timber seat.
        # Its resistance and welding procedure remain a separate calculation.
        vertices = [v for v in web.Vertices() if abs(v.Z-z-THICKNESS) < 1.e-6]
        y0, y1 = min(v.Y for v in vertices), max(v.Y for v in vertices)
        x = sign*(previous.b.HALF+THICKNESS)
        wire = cq.Wire.makePolygon([cq.Vector(x, y0, z+THICKNESS),
            cq.Vector(x+sign*WELD_LEG, y0, z+THICKNESS),
            cq.Vector(x, y0, z+THICKNESS+WELD_LEG)], close=True)
        weld = cq.Solid.extrudeLinear(wire, [], cq.Vector(0, y1-y0, 0))
        shoe = foot.fuse(web, weld).clean()
        # Keep the rim's existing enclosed strand passage open through the web.
        for row in previous.bore_records():
            if row['member'] != 'base_side_'+side:
                continue
            center = previous.b.point(sign*previous.b.HALF,
                                      row['center_s_mm'], row['center_n_mm'])
            opening = cq.Solid.makeCylinder((row['diameter_mm']+4.)/2, 100.,
                                            center-cq.Vector(50., 0, 0), cq.Vector(1, 0, 0))
            shoe = shoe.cut(opening).clean()
        result.append(previous.b.Part('clip_steel_shoe_'+side, shoe,
            (FOOT_Y[1]-FOOT_Y[0], FOOT_OUTBOARD_X-FOOT_INBOARD_X, THICKNESS), LIMITS, 1))
    for c in added_connections():
        # Opposite the shoe: rim-inner or header-underside load-spreading plate.
        near = c.start+c.direction*(WASHER+THICKNESS+38.1)
        if 'rim_' in c.name:
            sign = -c.direction.x
            index = int(c.name.rsplit('_', 1)[1])-1
            s = RIM_STATIONS[index//2]
            n = RIM_NORMAL_OFFSETS[index%2]
            lo, hi = sorted((sign*(previous.base.INNER_EDGE-BEARING_PLATE_THICKNESS),
                             sign*previous.base.INNER_EDGE))
            shape = previous.b.block(lo, hi, s-16., s+16., n-16., n+16.)
        else:
            shape = cq.Solid.makeBox(BEARING_PLATE_WIDTH, BEARING_PLATE_WIDTH,
                BEARING_PLATE_THICKNESS, cq.Vector(near.x-16., near.y-16., near.z-BEARING_PLATE_THICKNESS))
        result.append(previous.b.Part('clip_plate_'+c.name, shape,
            (32., 32., BEARING_PLATE_THICKNESS), 'Provisional A36 square bearing plate; '+LIMITS, 1))
    return tuple(result)


@cache
def parts():
    result = {p.name: p for p in wood_parts()}
    result.update({p.name: p for p in previous.hardware.clip_parts(stations())})
    result.update({p.name: p for p in steel_parts()})
    new_names = {c.name for c in added_connections()}
    for c in connections():
        for index, name in enumerate(c.members):
            if name.startswith('clip_') and c.name not in new_names:
                continue
            p = result[name]
            if index == 0 and isinstance(c, previous.CountersunkPanelScrew):
                shaft, head = c.components()
                shape = p.shape.cut(shaft).cut(head)
            else:
                diameter = WOOD_HOLE_DIAMETER if c.kind == 'bolt' else c.diameter
                shape = p.shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2.,
                                    c.start-c.direction, c.direction))
                if index == 0 and c.kind == 'screw':
                    shape = shape.cut(c.components()[1])
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
