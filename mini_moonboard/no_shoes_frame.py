"""Separate shoe-free 2x6-leg candidate with a 277 mm floor-to-face kicker.

Translate the existing upper frame by 52 mm, extend ground-bearing stock,
and preserve every occupied bore. Historical modules and caches stay untouched.
"""
from dataclasses import replace
from functools import cache
from types import SimpleNamespace

import cadquery as cq

from . import hold_tnut_reinforcement as tnuts
from . import kicker_header_reinforcement as kicker
from . import lumber_leg_spread_frame as leg_source
from . import round_structural_frame as previous

KEY = 'no-shoes-development'
PAD_HEIGHT_MM = 127.
EXPOSED_KICKER_MM = 150.
KICKER_HEIGHT_MM = PAD_HEIGHT_MM+EXPOSED_KICKER_MM
HEIGHT_CHANGE_MM = KICKER_HEIGHT_MM-previous.b.V1_KICKER_HEIGHT_MM
SHIFT = cq.Vector(0., 0., HEIGHT_CHANGE_MM)
LIMITS = ('Single 2x6 support legs with four existing bolts per leg; original two '
          'ML24Z base angles and twelve SDS screws restored; no custom steel shoes '
          'or shoe holes. Kicker top 277 mm above floor: 150 mm above an assumed '
          '127 mm pad. Upper frame raised 52 mm, posts/kicker extended to floor, '
          'legs extended along grain to level feet. 66 panel/kicker screws and '
          '142 T-nuts retained. Whole-frame response and connection resistance '
          'not assessed; NOT build-ready.')
# These API datums describe this candidate; historic factories are deliberately
# not forwarded, since their cached transforms use the old 225 mm kicker.
b = SimpleNamespace(HALF=previous.b.HALF, LENGTH=previous.b.LENGTH,
    V1_KICKER_HEIGHT_MM=KICKER_HEIGHT_MM, Part=previous.b.Part,
    point=lambda *args: previous.b.point(*args)+SHIFT,
    block=lambda *args: previous.b.block(*args).translate(SHIFT),
    normal=previous.b.normal)
base = SimpleNamespace(HEADER_TOP=previous.base.HEADER_TOP+HEIGHT_CHANGE_MM,
    HEADER_BOTTOM=previous.base.HEADER_BOTTOM+HEIGHT_CHANGE_MM,
    HEADER_FRONT_Y=previous.base.HEADER_FRONT_Y, INNER_EDGE=previous.base.INNER_EDGE)
wide = previous.wide


def changed_mesh(name):
    return name.startswith(('base_post_', 'kicker_', 'lumber_leg_')) or name == 'base_header'


@cache
def connections():
    return tuple(replace(c, start=c.start+SHIFT)
                 for c in previous.connections()+kicker.added_connections())


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, previous.CountersunkPanelScrew))


def attachment_datums():
    return tuple({**row, 's': row['s']+HEIGHT_CHANGE_MM}
                 if row['panel'].startswith('kicker_') else dict(row)
                 for row in kicker.attachment_datums())


def stations():
    return tuple((name, origin+SHIFT, u, v, beam, upright)
                 for name, origin, u, v, beam, upright in previous.stations())


def bolt_points():
    return tuple(point+SHIFT for point in previous.bolt_points())


def extend_ground_part(part):
    """Extend stock along its grain without stretching any occupied holes."""
    shape = part.shape.translate(SHIFT)
    blank = part.blank
    if part.name.startswith(('base_post_', 'kicker_')):
        bounds = shape.BoundingBox()
        extension = cq.Solid.makeBox(bounds.xlen, bounds.ylen, HEIGHT_CHANGE_MM,
                                    cq.Vector(bounds.xmin, bounds.ymin, 0.))
        shape = shape.fuse(extension).clean()
        index = 1 if part.name.startswith('kicker_') else 0
        blank = tuple(value+HEIGHT_CHANGE_MM if i == index else value
                      for i, value in enumerate(blank))
    elif part.name.startswith('lumber_leg_'):
        _, _, along, _ = leg_source.geometry('2x6', 0.)
        # The existing level foot is a parallelogram. Sweep that face down
        # along the original grain to preserve the exact 38.1 x 139.7 section.
        faces = [face for face in shape.Faces()
                 if all(abs(v.Z-HEIGHT_CHANGE_MM) < 1.e-6 for v in face.Vertices())]
        if len(faces) != 1:
            raise ValueError('Require one planar level foot: '+part.name)
        face = faces[0]
        extension_length = HEIGHT_CHANGE_MM/along.z
        extension = cq.Solid.extrudeLinear(face.outerWire(), face.innerWires(), -along*extension_length)
        shape = shape.fuse(extension).clean()
        blank = (blank[0]+extension_length, *blank[1:])
    return replace(part, shape=shape, blank=blank,
                   description=part.description+'; '+LIMITS)


@cache
def parts():
    return tuple(extend_ground_part(p) for p in
                 kicker.cut_added_connections(previous.parts())+tnuts.parts(previous))


@cache
def uncut_wood_parts():
    return tuple(extend_ground_part(p) for p in previous.uncut_wood_parts())


@cache
def electrical_parts():
    return tuple(replace(p, shape=p.shape.translate(SHIFT)) for p in previous.electrical_parts())
