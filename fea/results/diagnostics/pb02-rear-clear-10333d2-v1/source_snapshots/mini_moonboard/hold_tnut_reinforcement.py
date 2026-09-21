"""Selectable owned Escape three-hole T-nuts at current panel-grid rear faces.

No holds, hold bolts or flange-retention screws are added. Barrel diameter,
thread representation, clocking and the measured body-depth datum remain
provisional; these display solids are not manufacturing or strength approval.
"""
import math
from functools import cache

import cadquery as cq

from . import model as measured
from . import panel_grid_v2 as grid

FLANGE_DIAMETER_MM = measured.V1_SELECTED_TNUT_FLANGE_DIAMETER_MM
FLANGE_THICKNESS_MM = measured.V1_SELECTED_TNUT_FLANGE_THICKNESS_MM
BARREL_PROJECTION_MM = measured.V1_SELECTED_TNUT_BODY_DEPTH_MM
RETENTION_HOLE_DIAMETER_MM = measured.V1_SELECTED_TNUT_FLANGE_SCREW_HOLE_DIAMETER_MM
RETENTION_TRIANGLE_PITCH_MM = 15.98
# Display assumptions; neither dimension was supplied as a measured thread/OD.
PROVISIONAL_BARREL_DIAMETER_MM = 11.0
PROVISIONAL_SMOOTH_THREAD_OPENING_MM = 8.0
LIMITS = ('Owned Escape three-hole 3/8-16 steel T-nut; measured flange 25.4 x 1.86 mm, '
          'body depth 12.7 mm and three 3.2 mm holes at 15.98 mm triangle pitch. '
          'Provisional barrel OD 11.0 mm and smooth 8.0 mm thread opening; no thread helices. '
          '12.7 mm modeled as barrel projection from seating face, 14.56 mm overall; '
          'measured depth datum and flange clocking unverified. No hold bolt or '
          'retention screws modeled; installation and resistance unqualified.')


def retention_hole_centers():
    """Equilateral pattern; arbitrary first-hole clocking along local +X."""
    radius = RETENTION_TRIANGLE_PITCH_MM/math.sqrt(3)
    return tuple((radius*math.cos(2*math.pi*i/3), radius*math.sin(2*math.pi*i/3))
                 for i in range(3))


@cache
def local_shape():
    """Z=0 seats against rear plywood; barrel enters +Z and flange extends -Z."""
    flange = cq.Solid.makeCylinder(FLANGE_DIAMETER_MM/2, FLANGE_THICKNESS_MM,
        cq.Vector(0, 0, -FLANGE_THICKNESS_MM), cq.Vector(0, 0, 1))
    barrel = cq.Solid.makeCylinder(PROVISIONAL_BARREL_DIAMETER_MM/2,
        BARREL_PROJECTION_MM, cq.Vector(0, 0, 0), cq.Vector(0, 0, 1))
    shape = flange.fuse(barrel)
    bore = cq.Solid.makeCylinder(PROVISIONAL_SMOOTH_THREAD_OPENING_MM/2,
        BARREL_PROJECTION_MM+FLANGE_THICKNESS_MM+2,
        cq.Vector(0, 0, -FLANGE_THICKNESS_MM-1), cq.Vector(0, 0, 1))
    shape = shape.cut(bore)
    for x, y in retention_hole_centers():
        hole = cq.Solid.makeCylinder(RETENTION_HOLE_DIAMETER_MM/2,
            FLANGE_THICKNESS_MM+2, cq.Vector(x, y, -FLANGE_THICKNESS_MM-1),
            cq.Vector(0, 0, 1))
        shape = shape.cut(hole)
    return shape.clean()


def datums(model):
    """Use grid_v2 coordinates and each candidate's actual rear-face transform."""
    if (not math.isclose(model.b.HALF, grid.PANEL_HEIGHT_MM, abs_tol=1.e-9)
            or model.wide.PANEL <= BARREL_PROJECTION_MM):
        raise ValueError('Require current 48-inch grid and a barrel shorter than the plywood')
    rows = []
    for label, (x, s) in grid.main_tnut_datums().items():
        side = 'left' if x < model.b.HALF else 'right'
        panel = f'main_{"lower" if s < model.b.HALF else "upper"}_{side}'
        point = model.b.point(x-model.b.HALF, s, 0.)
        axis = -model.b.normal()
        rows.append({'name': 'hold_tnut_main_'+label, 'label': label, 'panel': panel,
                     'rear_seating_xyz_mm': list(point.toTuple()),
                     'barrel_into_panel_direction': list(axis.toTuple())})
    for label, (x, z) in grid.kicker_foothold_datums().items():
        side = 'left' if x < model.b.HALF else 'right'
        point = cq.Vector(x-model.b.HALF, model.base.HEADER_FRONT_Y,
                          model.b.V1_KICKER_HEIGHT_MM+z)
        rows.append({'name': 'hold_tnut_kicker_'+label, 'label': label,
                     'panel': 'kicker_'+side, 'rear_seating_xyz_mm': list(point.toTuple()),
                     'barrel_into_panel_direction': [0., 1., 0.]})
    if len(rows) != 142 or len({row['name'] for row in rows}) != 142:
        raise ValueError('Require 132 main and 10 kicker T-nut datums')
    return tuple(rows)


def parts(model):
    """One independent steel display part per T-nut; no panel cuts or other hardware."""
    result = []
    for row in datums(model):
        plane = cq.Plane(origin=tuple(row['rear_seating_xyz_mm']), xDir=(1., 0., 0.),
                         normal=tuple(row['barrel_into_panel_direction']))
        result.append(model.b.Part(row['name'], local_shape().moved(plane.location),
            (FLANGE_DIAMETER_MM, FLANGE_DIAMETER_MM,
             BARREL_PROJECTION_MM+FLANGE_THICKNESS_MM),
            LIMITS+' Panel '+row['panel']+'; datum '+row['label']+'.', 1))
    return tuple(result)
