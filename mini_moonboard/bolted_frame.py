"""Wide-stock, through-bolted ledge/clip development candidate, not build approval."""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import bracket_mvp as bracket
from . import easy_frame as baseline
from . import product_frame as product
from . import wood_mvp as wood
from .selected_hardware import BoltSpec

KEY = "bolted-clip-frame"
LIMITS = "Development geometry only; joint capacity, stability and product fit unqualified; NOT build-ready"
RAILS = {**wood.RAILS, "lower": (0., 234.95)}
INFILLS = {"lower": (234.95, 1149.35), "upper": (1289.05, 2349.5)}
VERTICALS = {**wood.VERTICALS, "center_left": (-184.15, 0.), "center_right": (0., 184.15)}
UPRIGHTS = {"wood_principal_left": (-146.2, -57.3),
            "wood_principal_right": (57.3, 146.2),
            "wood_edge_principal_left": (-1219.2, -1130.3),
            "wood_edge_principal_right": (1130.3, 1219.2)}
BEAMS = {"lower": (100., 188.9), "mid": (1174.75, 1263.65), "top": (2349.5, 2438.4)}
SPANS = {"left": (-1130.3, -146.2), "right": (146.2, 1130.3)}
WASHER = 2.032
RECESS = 9.3392
FRONT_START = 7.3072
COUNTERBORE_DIAMETER = 28.575  # 1-1/8 in Forstner; actual socket fit unqualified.
EDGE_START = 114.3  # Square end clears the retained kicker-splice profiles.


@dataclass(frozen=True)
class FrameBolt(b.Connection):
    product_status: str = (
        "Selected Conquest A307 plain 3/8-16, 7.5-inch front and leg / 6-inch rim; "
        "dimensional family from selected_hardware.BoltSpec, maximum head/nut/washer envelopes; "
        "no assigned bearing, net-section, joint or clamp-friction resistance"
    )

    def components(self):
        spec = BoltSpec("Conquest A307 plain, selected dimensional family", self.length, self.grip, 0.)
        d = self.direction.normalized()
        radius = spec.body_diameter_max_mm/2

        def ring(outer, inner, length, start):
            return cq.Solid.makeCylinder(outer, length, start, d).cut(
                cq.Solid.makeCylinder(inner, length, start, d))

        return (cq.Solid.makeCylinder(radius, self.length, self.start, d),
                ring(spec.washer_od_max_mm/2, spec.washer_id_min_mm/2, WASHER, self.start),
                ring(spec.washer_od_max_mm/2, spec.washer_id_min_mm/2, WASHER,
                     self.start+d*(WASHER+self.grip)),
                cq.Solid.makeCylinder(spec.head_across_corners_max_mm/2,
                                      spec.head_height_max_mm, self.start, -d),
                ring(spec.nut_across_corners_max_mm/2, radius, spec.nut_height_max_mm,
                     self.start+d*(2*WASHER+self.grip)))


def ledger_layout():
    for label, (s0, s1) in RAILS.items():
        yield "wood_rail_"+label, -b.HALF, b.HALF, s0, s1
    for column, (x0, x1) in VERTICALS.items():
        for band, (s0, s1) in INFILLS.items():
            yield f"wood_vertical_{column}_{band}", x0, x1, s0, s1


def stations():
    for level, (s0, s1) in BEAMS.items():
        station, v = (s1, bracket.TANGENT) if level == "lower" else (s0, -bracket.TANGENT)
        for side, (x0, x1) in SPANS.items():
            endpoints = ((x0, 1., f"wood_edge_principal_{side}"),
                         (x1, -1., f"wood_principal_{side}")) if side == "left" else (
                         (x0, 1., f"wood_principal_{side}"),
                         (x1, -1., f"wood_edge_principal_{side}"))
            for index, (x, sign, upright) in enumerate(endpoints, 1):
                yield (f"clip_mvp_{level}_{side}_{index}", b.point(x, station, 107.95),
                       cq.Vector(sign, 0, 0), v, f"wood_beam_{level}_{side}", upright)


@cache
def connections():
    result = []
    for c in baseline.connections():
        if c.name.startswith(("easy_", "wood_edge_", "clip_mvp_")):
            continue
        if c.name.startswith("wood_panel_"):
            s = (c.start-b.point(0, 0, 0)).dot(product.TANGENT)
            x = c.start.x
            receiver = next(name for name, x0, x1, s0, s1 in ledger_layout()
                            if x0-1e-6 <= x <= x1+1e-6 and s0-1e-6 <= s <= s1+1e-6)
            c = replace(c, members=(c.members[0], receiver))
        if c.name.startswith("analysis_leg_wall_bolt_"):
            side = "left" if "_left_" in c.name else "right"
            sign = -1 if side == "left" else 1
            station = (c.start-b.point(0, 0, 0)).dot(product.TANGENT)
            # Move the existing four-axis pattern 4 mm rear-normal for the
            # added upright's loaded-edge margin. No extra hole is retained.
            c = FrameBolt(c.name, b.point(sign*(1130.3-WASHER), station, 78.075),
                          c.direction, 190.5, 9.525,
                          (f"wood_edge_principal_{side}", *c.members), "bolt", 165.1)
        result.append(c)

    def front(name, x, s, members):
        result.append(FrameBolt(name, b.point(x, s, FRONT_START), b.normal(),
                                190.5, 9.525, members, "bolt", 177.8-RECESS))

    for upright, (x0, x1) in UPRIGHTS.items():
        column = ("edge_" if "edge" in upright else "center_")+upright.rsplit("_", 1)[1]
        for index, s in enumerate((320., 700., 1600., 2100.), 1):
            band = "lower" if s < 1149.35 else "upper"
            front(f"bolted_ledge_{column}_{index}", (x0+x1)/2, s,
                  (f"wood_vertical_{column}_{band}", upright))
        if "edge" not in upright:
            front(f"bolted_lower_{column}", (x0+x1)/2, 117.475,
                  ("wood_rail_lower", upright))
    for side, sign in (("left", -1), ("right", 1)):
        front(f"bolted_lower_span_{side}", sign*850., 144.45,
              ("wood_rail_lower", f"wood_beam_lower_{side}"))
        for level, s in (("mid", 1219.2), ("top", 2393.95)):
            for index, x in enumerate((sign*400., sign*850.), 1):
                front(f"bolted_rail_{level}_{side}_{index}", x, s,
                      (f"wood_rail_{level}", f"wood_beam_{level}_{side}"))
        for index, s in enumerate((350., 750., 1000., 2200.), 1):
            result.append(FrameBolt(f"bolted_rim_{side}_{index}",
                b.point(sign*(1257.3+WASHER), s, 107.95), cq.Vector(-sign, 0, 0),
                152.4, 9.525, (f"box_side_{side}", f"wood_edge_principal_{side}"), "bolt", 127.))
    for name, origin, u, v, beam, upright in stations():
        _, holes = bracket._connector(origin, u, v)
        for suffix, start, direction in holes:
            member = beam if suffix.startswith("beam_") else upright
            result.append(bracket.ConnectorScrew(f"{name}_{suffix}", start, direction,
                                                 38.1, 6.35, (name, member)))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(False) if not p.name.startswith(
        ("wood_vertical_", "wood_rail_", "wood_principal_", "wood_beam_", "easy_", "clip_mvp_"))}
    for name, x0, x1, s0, s1 in ledger_layout():
        vertical = name.startswith("wood_vertical_")
        blank = (s1-s0, x1-x0, 38.1) if vertical else (x1-x0, s1-s0, 38.1)
        p = b.Part(name, b.block(x0, x1, s0, s1, 0, 38.1), blank,
            "Square-ended flat ledge, grain "+("S" if vertical else "X")+
            "; round service reliefs and front bolt counterbores; "+LIMITS, 1)
        result[name] = replace(p, shape=product._backing_reliefs(replace(p, name="panel_"+name)).clean())
    for name, (x0, x1) in UPRIGHTS.items():
        s0 = EDGE_START if "edge" in name else 0.
        result[name] = b.Part(name, b.block(x0, x1, s0, b.LENGTH, 38.1, 177.8),
            (b.LENGTH-s0, 139.7, 88.9), "Square-ended 4x6 upright, grain S; "+LIMITS, 1)
    for level, (s0, s1) in BEAMS.items():
        for side, (x0, x1) in SPANS.items():
            name = f"wood_beam_{level}_{side}"
            result[name] = b.Part(name, b.block(x0, x1, s0, s1, 38.1, 177.8),
                (x1-x0, 139.7, s1-s0), "Repeated square-ended 4x6 beam span, grain X; "+LIMITS, 1)
    for name, origin, u, v, _, _ in stations():
        shape, _ = bracket._connector(origin, u, v)
        result[name] = b.Part(name, shape, (101.6, 50.8, 50.8),
            "Purchased ML24Z proxy; six SDS25112 screws separately supplied; factory holes/bend "
            "unverified, no custom steel work; "+LIMITS, 1)
    if not drilled:
        return tuple(result.values())
    return drill_parts(result, connections())


def drill_parts(raw_parts, fasteners):
    """Official face bores, retained holes and size-specific development bolt holes."""
    fasteners = tuple(fasteners)
    # Avoid drilling quarter-inch development bolts with the historical 3/8 clearance.
    retained = [c for c in fasteners if c.kind != "bolt"]
    result = {p.name: p for p in wood.drill_parts(raw_parts, retained)}
    for c in fasteners:
        if c.kind == "bolt":
            diameter = 7.14375 if c.diameter <= 6.35 else 11.1125
            for name in c.members:
                p = result[name]
                shape = product._bore(p.shape, diameter, c.length+2, c.start-c.direction, c.direction)
                result[name] = replace(p, shape=shape.clean())
        if c.name.startswith(("bolted_ledge_", "bolted_lower_", "bolted_rail_")):
            p = result[c.members[0]]
            start = c.start-c.direction*(FRONT_START+1)
            shape = p.shape.cut(cq.Solid.makeCylinder(COUNTERBORE_DIAMETER/2, RECESS+1, start, c.direction)).clean()
            result[p.name] = replace(p, shape=shape)
    return tuple(result.values())
