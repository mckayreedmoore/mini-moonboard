"""Single-layer 1.5-inch-stock framing study; no assigned connection capacity."""
from dataclasses import replace
from functools import cache
from math import hypot

import cadquery as cq

from . import box_frame as b
from . import bracket_mvp as bracket
from . import easy_frame as baseline
from . import product_frame as product
from . import wood_mvp as wood
from .bolted_frame import WASHER, FrameBolt
from .panel_grid import main_led_datums, main_tnut_datums

KEY = "lean-38mm-frame"
DEPTH = 139.7
THICKNESS = 38.1
LIMITS = "Single-layer nominal 2x6 development; joints, net sections and stability unqualified; NOT build-ready"
UPRIGHTS = {"left": (-76.2, -38.1), "right": (0., 38.1)}
SPANS = {"left": (-b.HALF, -76.2), "right": (38.1, b.HALF)}
RAILS = {"lower": (100., 138.1), "mid_lower": (1181.1, 1219.2),
         "mid_upper": (1219.2, 1257.3), "top": (2400.3, 2438.4)}
# Square-ended edge infills stop outside the purchased angle bodies.
EDGE_BANDS = {"lower": (188.9, 1130.3), "upper": (1308.1, 2349.5)}


def timber_layout():
    for side, (x0, x1) in UPRIGHTS.items():
        yield f"lean_principal_{side}", x0, x1, 139.7, b.LENGTH, "S"
    for level, (s0, s1) in RAILS.items():
        for side, (x0, x1) in SPANS.items():
            yield f"lean_beam_{level}_{side}", x0, x1, s0, s1, "X"
    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign*b.HALF, sign*(b.HALF-THICKNESS)))
        for band, (s0, s1) in EDGE_BANDS.items():
            yield f"lean_edge_{side}_{band}", x0, x1, s0, s1, "S"


def stations():
    for level, (s0, s1) in RAILS.items():
        station, v = (s1, bracket.TANGENT) if level in ("lower", "mid_upper") else (s0, -bracket.TANGENT)
        for side, (x0, x1) in SPANS.items():
            endpoints = ((x0, 1., f"box_side_{side}", True),
                         (x1, -1., f"lean_principal_{side}", False)) if side == "left" else (
                         (x0, 1., f"lean_principal_{side}", False),
                         (x1, -1., f"box_side_{side}", True))
            for index, (x, sign, upright, outer) in enumerate(endpoints, 1):
                yield (f"clip_mvp_lean_{level}_{side}_{index}", b.point(x, station, 88.9 if level == "lower" else DEPTH/2),
                       cq.Vector(sign, 0, 0), v, f"lean_beam_{level}_{side}", upright)


def panel_positions():
    service = [(u-b.HALF, s) for u, s in (*main_tnut_datums().values(), *main_led_datums().values()) if s >= 0]
    for band, s0, s1 in (("lower", 19.05, 1200.15), ("upper", 1238.25, 2419.35)):
        for side, x0, x1 in (("left", -1200.15, -57.15), ("right", 19.05, 1200.15)):
            xs = [x0+i*(x1-x0)/3 for i in range(4)]
            ss = [s0+i*(s1-s0)/3 for i in range(4)]
            points = [(x, s, i in (0, 3)) for s in (s0, s1) for i, x in enumerate(xs)]
            points += [(x, s, True) for x in (x0, x1) for s in ss[1:-1]]
            for index, (x, s, fixed) in enumerate(points, 1):
                offsets = (0,) if fixed else (0, *[v for step in range(1, 41) for v in (step, -step)])
                x = next(x+d for d in offsets if all(hypot(x+d-hx, s-hs) >= 28. for hx, hs in service))
                yield f"lean_panel_{band}_{side}_{index}", f"main_{band}_{side}", x, s


@cache
def connections():
    result = []
    for c in baseline.connections():
        if not c.name.startswith(("leg_stitch_", "analysis_leg_wall_bolt_", "cheek_splice_", "kicker_", "wood_kicker_")):
            continue
        if c.name.startswith("analysis_leg_wall_bolt_"):
            side = "left" if "_left_" in c.name else "right"
            sign = -1 if side == "left" else 1
            s = (c.start-b.point(0, 0, 0)).dot(product.TANGENT)
            band = next(band for band, (s0, s1) in EDGE_BANDS.items() if s0 <= s <= s1)
            c = FrameBolt(c.name, b.point(sign*(1181.1-WASHER), s, 74.075),
                          c.direction, 139.7, 9.525,
                          (f"lean_edge_{side}_{band}", *c.members), "bolt", 114.3)
            c = replace(c, product_status="Provisional Conquest-family 3/8-16 x5.5in leg bolt; fit/strength unqualified")
        result.append(c)
    result.extend(c for c in baseline.connections() if c.name.startswith("easy_lower_corner_"))
    for name, panel, x, s in panel_positions():
        receiver = "wood_rail_lower" if s < 139.7 else next(
            name for name, x0, x1, s0, s1, _ in timber_layout()
            if x0-1e-6 <= x <= x1+1e-6 and s0-1e-6 <= s <= s1+1e-6)
        result.append(wood._screw(name, b.point(x, s, -product.FACE_THICKNESS_MM),
                                 b.normal(), 50.8, (panel, receiver), 4.3942))
    for side, sign in (("left", -1), ("right", 1)):
        for index, x in enumerate((sign*400., sign*850.), 1):
            screw = wood._screw(f"lean_lower_ledge_{side}_{index}",
                b.point(x, 119.05, 0.), b.normal(), 79.248,
                ("wood_rail_lower", f"lean_beam_lower_{side}"), 4.3942)
            result.append(replace(screw, product_status=
                "Selected GRK R4 #9 x3-1/8, 103105; drawing L79.248mm, thread40.894mm; "
                "generic head/pilot proxy; tolerances, thread engagement and withdrawal resistance unqualified"))
    for side, sign in (("left", -1), ("right", 1)):
        for index, s in enumerate((320., 700., 1000., 1500., 2100., 2300.), 1):
            band = next(band for band, (s0, s1) in EDGE_BANDS.items() if s0 <= s <= s1)
            result.append(wood._screw(f"lean_edge_side_{side}_{index}",
                b.point(sign*(b.HALF+38.1), s, 44.45 if band == "lower" else 110.), cq.Vector(-sign, 0, 0), 63.5,
                (f"box_side_{side}", f"lean_edge_{side}_{band}")))
    for name, origin, u, v, beam, upright in stations():
        _, holes = bracket._connector(origin, u, v)
        for suffix, start, direction in holes:
            result.append(bracket.ConnectorScrew(f"{name}_{suffix}", start, direction,
                38.1, 6.35, (name, beam if suffix.startswith("beam_") else upright)))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False) if p.name.startswith(
        ("main_", "leg_", "box_side_", "cheek_splice_", "kicker_", "wood_kicker_", "easy_lower_corner_"))}
    lower = b.Part("wood_rail_lower", b.block(-b.HALF, b.HALF, 0., 139.7, 0., 38.1),
        (b.LENGTH, 139.7, 38.1), "Localized lower transition flat 2x6 ledge; paired deep spans and retained corners; "+LIMITS, 1)
    result[lower.name] = replace(lower, shape=product._backing_reliefs(replace(lower, name="panel_"+lower.name)).clean())
    for name, x0, x1, s0, s1, grain in timber_layout():
        # Lower edge infills carry panel edges, not leg attachment bolts.
        depth = 88.9 if name.startswith("lean_edge_") and name.endswith("_lower") else DEPTH
        blank = (s1-s0, depth, x1-x0) if grain == "S" else (x1-x0, depth, s1-s0)
        n0, n1 = (38.1, 177.8) if name.startswith("lean_beam_lower_") else (0., depth)
        p = b.Part(name, b.block(x0, x1, s0, s1, n0, n1), blank,
            f"Square-cut {'2x4 panel-edge infill' if depth == 88.9 else '2x6 framing'}, grain {grain}; "
            + ("localized lower two-layer transition; " if n0 else "single depth; ")
            + "round front service pockets only; "+LIMITS, 1)
        result[name] = replace(p, shape=product._backing_reliefs(replace(p, name="panel_"+name)).clean())
    for name, origin, u, v, _, _ in stations():
        shape, _ = bracket._connector(origin, u, v)
        result[name] = b.Part(name, shape, (101.6, 50.8, 50.8),
            "Purchased ML24Z proxy; six separate SDS25112 screws; actual geometry and resistance unqualified", 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
