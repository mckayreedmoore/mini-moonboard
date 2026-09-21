"""Lumber-rim development with panel-edge backing and explicit service pockets.

Not construction approval. The preserved base concept is never modified.
"""
from dataclasses import dataclass, replace
from functools import cache
from math import hypot

import cadquery as cq

from . import base_frame as base
from . import box_frame as b
from . import panel_grid_v2 as grid
from . import product_frame as product
from . import timber_connections as hardware
from .bolted_frame import WASHER, FrameBolt

KEY = "timber-base-development"
SIDE_DEPTH = 184.15  # Actual 1.5 x 7.25 in nominal 2x8; no width ripping.
SERVICE_DIAMETER = 40.
SERVICE_DEPTH = 45.
LIMITS = "Development geometry; connections and structural resistance unqualified; NOT build-ready"


def service_envelopes():
    """Reserved straight access volumes; flexible-wire bend routing is separate."""
    return tuple(cq.Solid.makeCylinder(SERVICE_DIAMETER/2, SERVICE_DEPTH,
        b.point(x-b.HALF, s, 0), b.normal())
        for x, s in (*grid.main_tnut_datums().values(), *grid.main_led_datums().values()))


@cache
def wood_parts(drilled=True):
    result = {p.name: p for p in base.parts(drilled)}
    bottom = b.block(-base.INNER_EDGE, base.INNER_EDGE, 0., 88.9, 0., 38.1)
    # Continuous front rail receives the entire lower panel edge. Its 38.1 mm
    # deep housings leave the principal rear section continuous to the header.
    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*base.INNER_EDGE))
        shape, blank = base._sloped_bearing_member(x0, x1, SIDE_DEPTH, b.LENGTH)
        name = f"base_side_{side}"
        result[name] = b.Part(name, shape, blank,
            "One-piece nominal 2x8 x10 ft Douglas Fir-Larch No.2 candidate; "
            "actual section 38.1 x184.15 mm; level lower bearing cut; "+LIMITS, 1)
        name = f"base_principal_{side}"
        p = result[name]
        result[name] = replace(p, shape=p.shape.cut(bottom).clean(),
            description="Nominal 2x6 x10 ft; front housing 88.9 mm along board x38.1 mm deep "
            "for continuous lower rail; 101.6 mm rear depth remains; "+LIMITS)
    result["timber_bottom_backing"] = b.Part("timber_bottom_backing", bottom,
        (2*base.INNER_EDGE, 88.9, 38.1),
        "Continuous flat nominal 2x4 lower panel-edge receiver; housed into principals; "+LIMITS, 1)
    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*(b.HALF+19.05)))
        name = f"timber_base_gusset_{side}"
        result[name] = b.Part(name, base._world_box(x0, x1,
            base.HEADER_FRONT_Y-base.HEADER_DEPTH, base.HEADER_FRONT_Y, 20., 480.),
            (460., base.HEADER_DEPTH, 19.05),
            "Removable 3/4 in plywood side gusset; face grain vertical; four through-bolts; "
            "plywood thickness assumed, not purchased-face measurement; "+LIMITS, 1)
    for name, p in tuple(result.items()):
        if name.startswith("leg_"):
            result[name] = replace(p, description="Independent 3/4 in plywood leg ply; "
                "three ply stitch bolts and four removable rim bolts per leg; "+LIMITS)
        elif name.startswith("base_post_"):
            bounds = p.shape.BoundingBox()
            shape = base._world_box(bounds.xmin, bounds.xmax,
                base.HEADER_FRONT_Y-base.HEADER_DEPTH, base.HEADER_FRONT_Y, 0., base.HEADER_BOTTOM)
            result[name] = replace(p, shape=shape,
                blank=(base.HEADER_BOTTOM, base.HEADER_DEPTH, 38.1),
                description="Short upright nominal 2x12 block; grain vertical; supports full header depth; "+LIMITS)
        elif name.startswith("base_rail_mid_"):
            result[name] = replace(p, description="Nominal 2x6 midpoint rail; front LED service pockets; "+LIMITS)
        elif name == "base_header":
            result[name] = replace(p, description="Flat nominal 2x12 header; full-depth posts beneath "
                "sloped-member bearing lines; bottom face backing supplied separately; "+LIMITS)
    if drilled:
        cutters = service_envelopes()
        for name, p in tuple(result.items()):
            if name.startswith(("base_side_", "base_principal_", "base_rail_", "timber_bottom_")):
                shape = p.shape
                bounds = shape.BoundingBox()
                for cutter in cutters:
                    cb = cutter.BoundingBox()
                    if all(getattr(bounds, a+"max") >= getattr(cb, a+"min") and
                           getattr(cb, a+"max") >= getattr(bounds, a+"min") for a in "xyz"):
                        shape = shape.cut(cutter)
                result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())


@dataclass(frozen=True)
class PanelScrew(b.Connection):
    product_status: str = "SPAX XFT08P-2000 #8 x2 in; nominal geometry; head profile and capacity unqualified"

    def components(self):
        return (cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, self.direction),
                cq.Solid.makeCone(8.128/2, self.diameter/2, 3., self.start, self.direction))


def panel_connections():
    """Twelve per panel; corner screws move away from timber ends."""
    service = [(x-b.HALF, s) for x, s in
               (*grid.main_tnut_datums().values(), *grid.main_led_datums().values())]
    for row, band in enumerate(("lower", "upper")):
        for side, x0, x1 in (("left", -1200.15, -57.15), ("right", 19.05, 1200.15)):
            low, high = row*b.HALF, (row+1)*b.HALF
            points = [(x, s) for x in (x0, x1) for s in (low+60., high-(100. if row else 60.))]
            points += [(x, low+b.HALF*f) for x in (x0, x1) for f in (1/3, 2/3)]
            for s in (low+19.05, high-19.05):
                for f in (1/3, 2/3):
                    target = x0+(x1-x0)*f
                    x = next(target+d for d in (0., *[v for k in range(1, 41) for v in (k, -k)])
                             if all(hypot(target+d-hx, s-hs) >= 28. for hx, hs in service))
                    points.append((x, s))
            for index, (x, s) in enumerate(points, 1):
                if abs(x) > base.INNER_EDGE:
                    receiver = f"base_side_{side}"
                elif x in (-57.15, 19.05):
                    receiver = "timber_bottom_backing" if s < 88.9 else f"base_principal_{side}"
                elif s < 88.9:
                    receiver = "timber_bottom_backing"
                elif s > b.LENGTH-38.1:
                    receiver = "base_rail_top"
                else:
                    receiver = f"base_rail_mid_{'lower' if s < b.HALF else 'upper'}_{side}"
                yield PanelScrew(f"timber_panel_{band}_{side}_{index}",
                    b.point(x, s, -product.FACE_THICKNESS_MM), b.normal(), 50.8, 4.1402,
                    (f"main_{band}_{side}", receiver))


@cache
def connections():
    result = [*hardware.leg_connections(), *hardware.clip_connections(tuple(hardware.stations(True))),
              *panel_connections()]
    for side, sign in (("left", -1), ("right", 1)):
        for index, (y, z, receiver) in enumerate((
                (-80., 300., f"base_side_{side}"), (-80., 380., f"base_side_{side}"),
                (-100., 100., f"base_post_outer_{side}"), (-240., 100., f"base_post_outer_{side}")), 1):
            result.append(FrameBolt(f"timber_base_{side}_{index}",
                cq.Vector(sign*(base.INNER_EDGE-WASHER), y, z), cq.Vector(sign, 0, 0),
                76.2, 9.525, (receiver, f"timber_base_gusset_{side}"), "bolt", 57.15,
                product_status="Conquest-family 3/8-16 x3 in candidate; removable base gusset; joint unqualified"))
        x = -57.15 if side == "left" else 19.05
        result.append(FrameBolt(f"timber_backing_bolt_{side}", b.point(x, 40., 10.), b.normal(),
            152.4, 9.525, ("timber_bottom_backing", f"base_principal_{side}"), "bolt", 139.7-10.-WASHER,
            product_status="Conquest-family 3/8-16 x6 in candidate; recessed front head beneath panel; joint unqualified"))
    # Kicker attachment stays on the front: two screws per outer/central post.
    for side, xs in (("left", (-1200.15, -57.15)), ("right", (19.05, 1200.15))):
        for column, x in enumerate(xs):
            post = f"base_post_{'outer' if abs(x)>1000 else 'center'}_{side}"
            for index, z in enumerate((60., 140.), 1):
                result.append(PanelScrew(f"timber_kicker_{side}_{column}_{index}",
                    cq.Vector(x, base.HEADER_FRONT_Y+product.FACE_THICKNESS_MM, z), cq.Vector(0, -1, 0),
                    50.8, 4.1402, (f"kicker_{side}", post)))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in wood_parts(drilled)}
    result.update({p.name: p for p in hardware.clip_parts(tuple(hardware.stations(True)))})
    if drilled:
        for c in connections():
            for index, name in enumerate(c.members):
                if name.startswith("clip_"):
                    continue
                p = result[name]
                # Cylinders represent occupied/clearance geometry only. They
                # are not pilot-drilling instructions for the selected screws.
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
