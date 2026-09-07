"""Wood-first inspection MVP: housed timber, ordinary hardware, no custom steel.

Not a construction release. Housing deductions and provisional retention do not
establish joint strength, independent-ply load sharing or unanchored stability.
"""
from dataclasses import dataclass, replace
from functools import cache
from math import hypot

import cadquery as cq

from . import box_frame as b
from . import product_frame as product
from . import top_joint_frame as previous
from .model import _v1_kicker_holes, _v1_main_panel_holes
from .panel_grid import main_led_datums, main_tnut_datums

KEY = "wood-first-mvp"
THICKNESS = 38.1
HOUSING = 9.525
VERTICALS = {"center_left": (-88.9, 0.), "center_right": (0., 88.9),
             "edge_left": (-b.HALF, -b.HALF+88.9), "edge_right": (b.HALF-88.9, b.HALF)}
RAILS = {"lower": (0., 88.9), "mid": (b.HALF-69.85, b.HALF+69.85),
         "top": (b.LENGTH-88.9, b.LENGTH)}
PRINCIPALS = {"left": (-95.4, -57.3), "right": (18.9, 57.)}
BEAMS = {"lower": (100., 138.1), "mid": (b.HALF-19.05, b.HALF+19.05),
         "top": (b.LENGTH-38.1, b.LENGTH)}
LIMITS = "WOOD-FIRST MVP; nominal ordinary stock/hardware, unqualified joint, fit and stability; no glue/friction capacity credit"


@dataclass(frozen=True)
class MVPConnection(b.Connection):
    product_status: str = ("PROVISIONAL ordinary commercial wood-screw envelope; exact SKU, "
                           "pilot, head seat, engagement and resistance unqualified")


def _screw(name, start, direction, length, members, diameter=4.826):
    return MVPConnection(name, start, direction, length, diameter, tuple(members))


@cache
def connections():
    result = [c for c in product.connections() if c.name.startswith(
        ("leg_stitch_", "analysis_leg_wall_bolt_", "cheek_splice_", "kicker_"))]
    # Rebuild, rather than reuse, the short-margin lower splice screw bores.
    # Nominal center spacing is 33.541 mm; product spacing still needs review.
    for index, c in enumerate(result):
        if c.name.startswith("cheek_splice_") and c.name.endswith(("_1", "_2")):
            s, n = (-40., 80.) if c.name.endswith("_1") else (-25., 110.)
            sign = -1 if "_left_" in c.name else 1
            result[index] = replace(c, start=b.point(sign*(b.HALF-38.1), s, n))
    ticks = (50., 50.+(b.HALF-100)/3, 50.+2*(b.HALF-100)/3, b.HALF-50.)
    service = [(u-b.HALF, s) for u, s in
               (*main_tnut_datums().values(), *main_led_datums().values()) if s >= 0]
    for row, band in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            positions = [(x, s) for s in (50., b.HALF-50.) for x in ticks]
            positions += [(x, s) for x in (50., b.HALF-50.) for s in ticks[1:-1]]
            for index, (u, v) in enumerate(positions, 1):
                x, s = (col-1)*b.HALF+u, row*b.HALF+v
                # Shift only interior horizontal-edge stations around rear
                # service reliefs; shared corner columns stay aligned.
                offsets = (0,) if u in (50., b.HALF-50.) else (
                    0, *[d for step in range(1, 41) for d in (step, -step)])
                x = next(x+d for d in offsets
                         if all(hypot(x+d-hx, s-hs) >= 28. for hx, hs in service))
                rail = next((label for label, (a, z) in RAILS.items() if a <= s <= z), None)
                vertical = next((label for label, (a, z) in VERTICALS.items() if a <= x <= z), None)
                receivers = (["wood_rail_"+rail] if rail else [])
                if vertical:
                    receivers.append("wood_vertical_"+vertical)
                result.append(_screw(f"wood_panel_{band}_{side}_{index}", b.point(x, s, -product.FACE_THICKNESS_MM),
                                     b.normal(), 50.8, (f"main_{band}_{side}", *receivers), 4.3942))
    for vertical, (x0, x1) in VERTICALS.items():
        for rail, (s0, s1) in RAILS.items():
            for index, offset in enumerate((-20., 20.), 1):
                result.append(_screw(f"wood_lap_{vertical}_{rail}_{index}",
                    b.point((x0+x1)/2, (s0+s1)/2+offset, 0), b.normal(), 31.75,
                    ("wood_rail_"+rail, "wood_vertical_"+vertical)))
    for side, sign in (("left", -1), ("right", 1)):
        for index, s in enumerate((300., 900., 1500., 2100.), 1):
            result.append(_screw(f"wood_edge_{side}_{index}", b.point(sign*(b.HALF+38.1), s, 19.05),
                cq.Vector(-sign, 0, 0), 76.2, (f"box_side_{side}", f"wood_vertical_edge_{side}")))
        for label, (s0, s1) in BEAMS.items():
            x0, x1 = PRINCIPALS[side]
            result.append(_screw(f"wood_deep_lap_{side}_{label}",
                b.point((x0+x1)/2, (s0+s1)/2, 177.8), -b.normal(), 114.3,
                (f"wood_principal_{side}", f"wood_beam_{label}"), 6.35))
        for index, s in enumerate((300., 700., 1600., 2100.), 1):
            x0, x1 = PRINCIPALS[side]
            # Rear principal into the flat face ledge, across both members' grain.
            result.append(_screw(f"wood_principal_ledge_{side}_{index}",
                b.point((x0+x1)/2, s, 177.8), -b.normal(), 165.1,
                (f"wood_principal_{side}", f"wood_vertical_center_{side}"), 6.35))
        for level, z in (("bottom", 25.), ("top", 200.)):
            block = f"wood_kicker_block_{side}_{level}"
            inner = b.HALF-(76.2 if level == "top" else 38.1)
            result.append(_screw(f"wood_kicker_block_face_{side}_{level}",
                cq.Vector(sign*inner, -36, z), cq.Vector(0, -1, 0), 63.5,
                (f"kicker_batten_{level}", block)))
            members = [f"kicker_cheek_{side}"]
            if level == "top":
                members += [f"cheek_splice_{side}_outer", f"cheek_splice_{side}_inner"]
            members.append(block)
            result.append(_screw(f"wood_kicker_block_side_{side}_{level}",
                cq.Vector(sign*(b.HALF+38.1), -93.15, z), cq.Vector(-sign, 0, 0),
                101.6 if level == "top" else 63.5, members))
    return tuple(result)


def drill_parts(raw_parts, fasteners):
    """Recreate official face bores and only this variant's retention bores."""
    result = dict(raw_parts)
    for row, band in enumerate(("lower", "upper")):
        for col, side in enumerate(("left", "right")):
            name = f"main_{band}_{side}"
            shape = result[name].shape
            for x, s, diameter in _v1_main_panel_holes(col, row):
                shape = product._bore(shape, diameter, product.FACE_THICKNESS_MM+2,
                    b.point(x+(col-.5)*b.HALF, s+row*b.HALF, -product.FACE_THICKNESS_MM-1), b.normal())
            result[name] = replace(result[name], shape=shape.clean())
    for col, side in enumerate(("left", "right")):
        name = f"kicker_{side}"
        shape = result[name].shape
        for x, z, diameter in _v1_kicker_holes(col):
            shape = product._bore(shape, diameter, product.FACE_THICKNESS_MM+2,
                cq.Vector(x+(col-.5)*b.HALF, -37, z), cq.Vector(0, 1, 0))
        result[name] = replace(result[name], shape=shape.clean())
    for c in fasteners:
        for index, name in enumerate(c.members):
            if name.startswith("clip_mvp_"):
                continue  # Sibling commercial variant owns factory connector holes.
            part = result[name]
            diameter = (11.1125 if c.kind == "bolt" else
                        (7. if c.diameter >= 6.35 else 5.2) if index < len(c.members)-1 else
                        (4. if c.diameter >= 6.35 else 3.2))
            shape = product._bore(part.shape, diameter, c.length+2, c.start-c.direction, c.direction)
            if c.kind == "screw" and index == 0:
                shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())


@cache
def parts(drilled=True):
    result = {p.name: replace(p, description="Retained purchased face / plywood leg or splice / timber profile; "
                             "original datum, only this MVP's fastener bores; "+LIMITS)
              for p in previous.parts(False) if p.name.startswith(
                  ("main_", "leg_", "box_side_", "cheek_splice_", "kicker_"))}
    def add(name, shape, blank, note):
        result[name] = b.Part(name, shape.clean(), blank, note+"; "+LIMITS, 1)
    for label, (x0, x1) in VERTICALS.items():
        shape = b.block(x0, x1, 0, b.LENGTH, 0, 38.1)
        for s0, s1 in RAILS.values():
            shape = shape.cut(b.block(x0, x1, s0, s1, 0, 19.05))
        add("wood_vertical_"+label, shape, (b.LENGTH, 88.9, 38.1),
            "Flat 2x4 face-bearing ledge, grain S; front-half housing at horizontal ledges")
    for label, (s0, s1) in RAILS.items():
        shape = b.block(-b.HALF, b.HALF, s0, s1, 0, 38.1)
        for x0, x1 in VERTICALS.values():
            shape = shape.cut(b.block(x0, x1, s0, s1, 19.05, 38.1))
        add("wood_rail_"+label, shape, (b.LENGTH, s1-s0, 38.1),
            "Flat horizontal face-bearing ledge (2x6 at seam, 2x4 at ends), grain X; rear-half housing")
    for side, (x0, x1) in PRINCIPALS.items():
        shape = b.block(x0, x1, 0, b.LENGTH, 38.1, 177.8)
        for s0, s1 in BEAMS.values():
            shape = shape.cut(b.block(x0, x1, s0, s1, 38.1, 107.95))
        add("wood_principal_"+side, shape, (b.LENGTH, 139.7, 38.1),
            "Continuous on-edge 2x6 central support, grain S; actual 69.85 mm half-depth housings")
    for label, (s0, s1) in BEAMS.items():
        shape = b.block(-b.HALF-HOUSING, b.HALF+HOUSING, s0, s1, 38.1, 177.8)
        for x0, x1 in PRINCIPALS.values():
            shape = shape.cut(b.block(x0, x1, s0, s1, 107.95, 177.8))
        add("wood_beam_"+label, shape, (b.LENGTH+2*HOUSING, 139.7, 38.1),
            "On-edge 2x6 crossbeam/top cap, grain X; housed ends and complementary half-depth cuts")
        for side in ("left", "right"):
            name = f"box_side_{side}"
            result[name] = replace(result[name], shape=result[name].shape.cut(shape).clean(),
                description="Original 2x8 rim datum with 9.525 mm inner-face beam housings; "+LIMITS)
    for side, sign in (("left", -1), ("right", 1)):
        for level, z0 in (("bottom", 5.), ("top", 180.)):
            edge = b.HALF-(38.1 if level == "top" else 0.)
            x0, x1 = sorted((sign*edge, sign*(edge-76.2)))
            add(f"wood_kicker_block_{side}_{level}",
                cq.Solid.makeBox(x1-x0, 38.1, 40., cq.Vector(x0, -112.2, z0)),
                (76.2, 40., 38.1), "Sawn kicker retention block, grain vertical Z; side-grain X/Y fasteners")
    # Reuse service relief logic with a temporary panel prefix, not the old
    # frame fastener pattern. Deep supports keep the central hold/LED gap clear.
    for name, part in list(result.items()):
        if name.startswith(("wood_vertical_", "wood_rail_")):
            result[name] = replace(part, shape=product._backing_reliefs(replace(part, name="panel_"+name)).clean())
        elif name.startswith("kicker_batten_"):
            result[name] = replace(part, shape=product._backing_reliefs(part).clean())
    return drill_parts(result, connections()) if drilled else tuple(result.values())
