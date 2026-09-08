"""Inset framing with a level, wood-bearing kicker base: geometry concept only.

No inherited screws, bolts, clips, pilots or joint capacity are transferred.
Panel hardware access, detachable retention and structural qualification remain
unresolved. Historical bearing-frame geometry and evidence are unchanged.
"""
import math
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import bearing_frame as baseline
from . import box_frame as b
from . import panel_grid_v2 as grid
from . import product_frame as product

KEY = "base-bearing-concept"
THICKNESS = 38.1
DEPTH = 139.7
SIDE_DEPTH = 177.8
HEADER_DEPTH = 285.75
HEADER_TOP = b.V1_KICKER_HEIGHT_MM
HEADER_BOTTOM = HEADER_TOP-THICKNESS
HEADER_FRONT_Y = product.KICKER_BACK_Y_MM
INNER_EDGE = b.HALF-THICKNESS
UPRIGHTS = {"left": (-76.2, -38.1), "right": (0., 38.1)}
LIMITS = "GEOMETRY CONCEPT ONLY; retention, service access and structural capacity unqualified; NOT build-ready"


def connections():
    """No stale predecessor hardware masquerades as this design's connections."""
    return ()


def _world_box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1-x0, y1-y0, z1-z0, cq.Vector(x0, y0, z0))


def _sloped_bearing_member(x0, x1, depth, top):
    """Extend nominal stock down to a horizontal bearing cut, never a corner seat."""
    origin = b.point(0, 0, 0)
    angle = math.radians(b.ANGLE_FROM_VERTICAL_DEG)
    start = (HEADER_TOP-origin.z-depth*math.sin(angle))/math.cos(angle)
    stock = b.block(x0, x1, start, top, 0., depth)
    floor_cut = _world_box(-2000., 2000., -2000., 4000., -1000., HEADER_TOP)
    return stock.cut(floor_cut).clean(), (top-start, depth, x1-x0)


@cache
def parts(drilled=True):
    result = {}

    def add(name, shape, blank, description, laminations=1):
        result[name] = b.Part(name, shape, blank, description+"; "+LIMITS, laminations)

    for row, band in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            x0, s0 = (col-1)*b.HALF, row*b.HALF
            shape = b.block(x0, x0+b.HALF, s0, s0+b.HALF,
                            -product.FACE_THICKNESS_MM, 0.)
            add(f"main_{band}_{side}", shape,
                (b.HALF, b.HALF, product.FACE_THICKNESS_MM),
            "Purchased 23/32 CAT face; unchanged main backplane; opt-in panel_grid_v2 datums")

    for col, side in enumerate(("left", "right")):
        x0 = (col-1)*b.HALF
        shape = _world_box(x0, x0+b.HALF, product.KICKER_BACK_Y_MM,
                           product.KICKER_BACK_Y_MM+product.FACE_THICKNESS_MM,
                           0., b.V1_KICKER_HEIGHT_MM)
        shape = shape.cut(result[f"main_lower_{side}"].shape).clean()
        add(f"kicker_{side}", shape,
            (b.HALF, b.V1_KICKER_HEIGHT_MM, product.FACE_THICKNESS_MM),
            "225mm kicker; ten total active-zone T-nut holes; no main-grid LEDs in kicker")

    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*INNER_EDGE))
        shape, blank = _sloped_bearing_member(x0, x1, SIDE_DEPTH, b.LENGTH)
        add(f"base_side_{side}", shape, blank,
            "Inset 38.1 mm laminated side rim behind face; grain S; level lower bearing cut; "
            "blank exceeds 8 ft plywood: longer stock or a redesigned joint required", 2)
    for side, (x0, x1) in UPRIGHTS.items():
        shape, blank = _sloped_bearing_member(x0, x1, DEPTH, b.LENGTH-THICKNESS)
        add(f"base_principal_{side}", shape, blank,
            "Continuous 2x6 grain S; horizontal lower bearing cut; square top below top rail; "
            "requires 10 ft lumber")

    add("base_rail_top", b.block(-INNER_EDGE, INNER_EDGE,
        b.LENGTH-THICKNESS, b.LENGTH, 0., DEPTH),
        (2*INNER_EDGE, DEPTH, THICKNESS), "Continuous square-cut 2x6 top crossmember; grain X")
    for level, s0, s1 in (("lower", b.HALF-THICKNESS, b.HALF),
                          ("upper", b.HALF, b.HALF+THICKNESS)):
        for side, x0, x1 in (("left", -INNER_EDGE, -76.2),
                            ("right", 38.1, INNER_EDGE)):
            add(f"base_rail_mid_{level}_{side}", b.block(x0, x1, s0, s1, 0., DEPTH),
                (x1-x0, DEPTH, THICKNESS), "Square-cut 2x6 seam rail; separate panel-edge bearing; grain X; "
                "row 7 LED exits obstructed: service pockets not yet designed")

    add("base_header", _world_box(-b.HALF, b.HALF,
        HEADER_FRONT_Y-HEADER_DEPTH, HEADER_FRONT_Y, HEADER_BOTTOM, HEADER_TOP),
        (2*b.HALF, HEADER_DEPTH, THICKNESS),
        "Horizontal nominal 2x12 flat header; grain X; direct sloped-member bearing, retention unresolved; "
        "does not back the main plywood bottom edge")
    posts = {"outer_left": (-b.HALF, -INNER_EDGE),
             **{f"center_{side}": extents for side, extents in UPRIGHTS.items()},
             "outer_right": (INNER_EDGE, b.HALF)}
    for name, (x0, x1) in posts.items():
        add(f"base_post_{name}", _world_box(x0, x1, HEADER_FRONT_Y-88.9,
            HEADER_FRONT_Y, 0., HEADER_BOTTOM), (HEADER_BOTTOM, 88.9, THICKNESS),
            "Short vertical 2x4 kicker support; grain Z; square floor/header bearing; retention unresolved")

    for p in baseline.parts(False):
        if p.name.startswith("leg_"):
            shift = THICKNESS if "left" in p.name else -THICKNESS
            result[p.name] = replace(p, shape=p.shape.translate((shift, 0., 0.)),
                description="Historical undrilled plywood leg ply moved inward 38.1 mm with side rim; "
                "no attachment/stitch hardware transferred; "+LIMITS)

    if drilled:
        for name, p in tuple(result.items()):
            shape = p.shape
            if name.startswith("main_"):
                row = 0 if "lower" in name else 1
                col = 0 if "left" in name else 1
                for datums, diameter in ((grid.main_tnut_datums(), 11.1125),
                                          (grid.main_led_datums(), 13.)):
                    for x, s in datums.values():
                        if col*b.HALF <= x < (col+1)*b.HALF and row*b.HALF <= s < (row+1)*b.HALF:
                            shape = shape.cut(cq.Solid.makeCylinder(diameter/2,
                                product.FACE_THICKNESS_MM+2,
                                b.point(x-b.HALF, s, -product.FACE_THICKNESS_MM-1), b.normal()))
            elif name.startswith("kicker_"):
                col = 0 if "left" in name else 1
                for x, z in grid.kicker_foothold_datums().values():
                    if col*b.HALF <= x < (col+1)*b.HALF:
                        shape = shape.cut(cq.Solid.makeCylinder(11.1125/2,
                            product.FACE_THICKNESS_MM+2,
                            cq.Vector(x-b.HALF, product.KICKER_BACK_Y_MM-1,
                                      b.V1_KICKER_HEIGHT_MM+z), cq.Vector(0, 1, 0)))
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
