"""Square-cut commercial-connector candidate; no construction/use approval.

Shallow face ledges butt together instead of using half-laps. Existing purchased
connector proxies, service reliefs and shaped leg/kicker/splice work remain
explicit complexities; this is not an entirely square-cut climbing board.
"""
from dataclasses import replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import bracket_mvp as baseline
from . import product_frame as product
from . import wood_mvp as wood

KEY = "square-cut-bracket"
LIMITS = "SQUARE-CUT FRAME candidate; nominal hardware and product proxies; NOT build-ready; fit and resistance unqualified"
INFILLS = {"lower": (wood.RAILS["lower"][1], wood.RAILS["mid"][0]),
           "upper": (wood.RAILS["mid"][1], wood.RAILS["top"][0])}


def ledger_layout():
    """Plain stock extents X/S; all shallow ledges occupy N=0..38.1."""
    for label, (s0, s1) in wood.RAILS.items():
        yield "wood_rail_"+label, -b.HALF, b.HALF, s0, s1
    for column, (x0, x1) in wood.VERTICALS.items():
        for band, (s0, s1) in INFILLS.items():
            yield f"wood_vertical_{column}_{band}", x0, x1, s0, s1


def _vertical_at(name, station):
    return name+"_"+next(band for band, (s0, s1) in INFILLS.items() if s0 <= station <= s1)


@cache
def connections():
    result = []
    for c in baseline.connections():
        if c.name.startswith(("wood_lap_", "wood_principal_ledge_")):
            continue
        station = (c.start-b.point(0, 0, 0)).dot(product.TANGENT)
        members = c.members
        if c.name.startswith("wood_panel_"):
            # At a horizontal edge there is now one full-depth rail, not two
            # overlapping half-depth members. Other screws enter butt infills.
            rails = [name for name in members if name.startswith("wood_rail_")]
            members = (members[0], rails[0]) if rails else (
                members[0], _vertical_at(members[-1], station))
        elif c.name.startswith("wood_edge_"):
            members = (members[0], _vertical_at(members[-1], station))
        result.append(replace(c, members=members) if members != c.members else c)
    for side, sign in (("left", -1), ("right", 1)):
        x0, x1 = wood.PRINCIPALS[side]
        for index, station in enumerate((300., 700., 1600., 2100.), 1):
            result.append(wood._screw(f"easy_principal_ledge_{side}_{index}",
                b.point((x0+x1)/2, station, 0), b.normal(), 63.5,
                (_vertical_at(f"wood_vertical_center_{side}", station), f"wood_principal_{side}")))
        # Full-width lower rail bears directly on both principal front faces.
        result.append(wood._screw(f"easy_lower_principal_{side}",
            b.point((x0+x1)/2, 44.45, 0), b.normal(), 63.5,
            ("wood_rail_lower", f"wood_principal_{side}")))
        for level, station in (("mid", b.HALF), ("top", b.LENGTH-19.05)):
            for index, x in enumerate((sign*400., sign*850.), 1):
                result.append(wood._screw(f"easy_rail_beam_{level}_{side}_{index}",
                    b.point(x, station, 0), b.normal(), 63.5,
                    (f"wood_rail_{level}", f"wood_beam_{level}_{side}")))
        block = f"easy_lower_corner_{side}"
        result.append(wood._screw(f"easy_lower_corner_front_{side}",
            b.point(sign*(b.HALF-63.5), 24.05, 0), b.normal(), 63.5,
            ("wood_rail_lower", block)))
        result.append(wood._screw(f"easy_lower_corner_side_{side}",
            b.point(sign*(b.HALF+38.1), 70.85, 57.15), cq.Vector(-sign, 0, 0), 101.6,
            (f"box_side_{side}", f"cheek_splice_{side}_outer", f"cheek_splice_{side}_inner", block)))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False)
              if not p.name.startswith(("wood_vertical_", "wood_rail_"))}
    for name, x0, x1, s0, s1 in ledger_layout():
        shape = b.block(x0, x1, s0, s1, 0, 38.1)
        vertical = name.startswith("wood_vertical_")
        blank = (s1-s0, x1-x0, 38.1) if vertical else (x1-x0, s1-s0, 38.1)
        part = b.Part(name, shape, blank,
            "Square-ended full-depth face-bearing ledge; grain "+("S" if vertical else "X")+
            "; butt contact, retention to deep frame, no end-grain screw credit; "
            "round hold/LED service reliefs still required; "+LIMITS, 1)
        shape = product._backing_reliefs(replace(part, name="panel_"+name))
        result[name] = replace(part, shape=shape.clean())
    for side, sign in (("left", -1), ("right", 1)):
        name = f"easy_lower_corner_{side}"
        x0, x1 = sorted((sign*(b.HALF-127.), sign*(b.HALF-38.1)))
        result[name] = b.Part(name, b.block(x0, x1, 5., 93.9, 38.1, 76.2),
            (88.9, 88.9, 38.1),
            "Square-cut 2x4 lower-rail block, 88.9 mm along grain S; section88.9X by38.1N; "
            "front N and through-splice X side-grain retention at staggered stations; "
            "kept below lower factory connector envelope, no glued/composite credit; "+LIMITS, 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
