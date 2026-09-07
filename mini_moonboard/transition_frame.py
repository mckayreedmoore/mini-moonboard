"""Ten-junction perimeter inspection, not a selected joint or product.

Preserve the clip baseline separately; replace its twelve perimeter end screws.
Add material to each
existing splice profile, represented as two independent 19.05 mm plies, and
inspect custom angles with explicit generic hardware. No glue/friction credit.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import clip_frame as baseline
from . import shallow_frame
from .panel_grid import main_led_datums, main_tnut_datums

KEY = "lower-transition-development"
PLY = 19.05
STEEL = 6.
TANGENT = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()
BACK_Y = b.point(0, 0, shallow_frame.REAR).y
REMOVED_PREFIXES = ("analysis_batten_end_", "analysis_kicker_end_")


@dataclass(frozen=True)
class ProvisionalConnection(b.Connection):
    product_status: str = (
        "UNSELECTED replacement-route hardware envelope; custom 6 mm steel is not a rated A21. "
        "No thin-connector screw approval transfer. Material, head seating, threads, "
        "installation and resistance unresolved; no plywood-edge thread capacity credited."
    )


@cache
def connections():
    result = []
    for c in baseline.connections():
        if c.name.startswith(REMOVED_PREFIXES):
            continue
        members = tuple(ply for name in c.members for ply in
                        ((name+"_inner", name+"_outer") if name.startswith("cheek_splice_") else (name,)))
        result.append(replace(c, members=members) if members != c.members else c)
    for side, sign in (("left", -1), ("right", 1)):
        inner = sign*(b.HALF-b.THICKNESS)
        plies = (f"cheek_splice_{side}_inner", f"cheek_splice_{side}_outer")
        main, kicker = f"transition_main_angle_{side}", f"transition_kicker_angle_{side}"
        for index, s in enumerate((25., 70.), 1):
            result.append(ProvisionalConnection(f"transition_main_{side}_bolt_{index}",
                b.point(inner-sign*8, s, 110), cq.Vector(sign, 0, 0), 101.6, 9.525,
                (main, *plies, f"box_side_{side}"), "bolt", 82.2))
        for index, s in enumerate((30., 65.), 1):
            result.append(ProvisionalConnection(f"transition_main_{side}_screw_{index}",
                b.point(sign*(b.HALF-120), s, 44.1), -b.normal(), 38.1, 4.826,
                (main, "panel_edge_bottom")))
        for index, y in enumerate((-115., -145.), 1):
            result.append(ProvisionalConnection(f"transition_kicker_{side}_bolt_{index}",
                cq.Vector(inner-sign*8, y, 200), cq.Vector(sign, 0, 0), 101.6, 9.525,
                (kicker, *plies, f"kicker_cheek_{side}"), "bolt", 82.2))
        for index, inset in enumerate((95., 125.), 1):
            result.append(ProvisionalConnection(f"transition_kicker_{side}_screw_{index}",
                cq.Vector(sign*(b.HALF-inset), -80.1, 200), cq.Vector(0, 1, 0), 38.1, 4.826,
                (kicker, "kicker_batten_top")))
        for label, stations, n, rail in (
                ("seam", (1180., 1230.), 90., "panel_seam_horizontal"),
                ("top", (2375., 2415.), 63., "panel_edge_top")):
            angle = f"transition_{label}_angle_{side}"
            for index, s in enumerate(stations, 1):
                result.append(ProvisionalConnection(f"transition_{label}_{side}_bolt_{index}",
                    b.point(sign*(b.HALF-8), s, n), cq.Vector(sign, 0, 0), 63.5, 9.525,
                    (angle, f"box_side_{side}"), "bolt", 44.1))
                result.append(ProvisionalConnection(f"transition_{label}_{side}_screw_{index}",
                    b.point(sign*(b.HALF-110), s, 44.1), -b.normal(), 38.1, 4.826,
                    (angle, rail)))
        bottom = f"transition_kicker_bottom_angle_{side}"
        for index, y in enumerate((-100., -130.), 1):
            result.append(ProvisionalConnection(f"transition_kicker_bottom_{side}_bolt_{index}",
                cq.Vector(sign*(b.HALF-8), y, 25), cq.Vector(sign, 0, 0), 63.5, 9.525,
                (bottom, f"kicker_cheek_{side}"), "bolt", 44.1))
        for index, inset in enumerate((95., 125.), 1):
            result.append(ProvisionalConnection(f"transition_kicker_bottom_{side}_screw_{index}",
                cq.Vector(sign*(b.HALF-inset), -80.1, 25), cq.Vector(0, 1, 0), 38.1, 4.826,
                (bottom, "kicker_batten_bottom")))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: p for p in baseline.parts(drilled)}
    rebuilt = {member for c in baseline.connections() if c.name.startswith(REMOVED_PREFIXES)
               for member in c.members}
    if drilled:
        raw = {p.name: p for p in baseline.parts(False)}
        for name in rebuilt:
            part = raw[name]
            shape = part.shape
            if name.startswith("panel_"):
                for u, s in (*main_tnut_datums().values(), *main_led_datums().values()):
                    shape = shape.cut(cq.Solid.makeCylinder(20, b.THICKNESS+2,
                        b.point(u-b.HALF, s, -1), b.normal()))
            elif name.startswith("kicker_batten_"):
                for u, s in main_led_datums().values():
                    if s < 0:
                        shape = shape.cut(cq.Solid.makeCylinder(20, b.THICKNESS+2,
                            cq.Vector(u-b.HALF, -35, b.V1_KICKER_HEIGHT_MM+s), cq.Vector(0, -1, 0)))
            result[name] = replace(part, shape=shape.clean())
    for side, sign in (("left", -1), ("right", 1)):
        name = f"cheek_splice_{side}"
        old = result.pop(name)
        inner = sign*(b.HALF-b.THICKNESS)
        x0, x1 = sorted((sign*b.HALF, inner))
        main_pad = b.block(x0, x1, 0, 88.9, 38.1, 50)
        kicker_pad = cq.Solid.makeBox(x1-x0, -74.1-BACK_Y, 50, cq.Vector(x0, BACK_Y, 175))
        shape = old.shape.fuse(main_pad, kicker_pad).clean()
        s = [v.Center().dot(TANGENT) for v in shape.Vertices()]
        n = [v.Center().dot(b.normal()) for v in shape.Vertices()]
        bounds = shape.BoundingBox()
        for layer, start in (("inner", min(inner, inner+sign*PLY)),
                             ("outer", min(inner+sign*PLY, inner+sign*2*PLY))):
            clip = cq.Solid.makeBox(PLY, bounds.ylen+2, bounds.zlen+2,
                                   cq.Vector(start, bounds.ymin-1, bounds.zmin-1))
            result[name+"_"+layer] = b.Part(name+"_"+layer, shape.intersect(clip).clean(),
                (max(s)-min(s), max(n)-min(n), PLY),
                "PROVISIONAL additive transition profile; original stock profile and old bores retained, "
                "with supplemental through-bores; "
                "one independent 19.05 mm plywood ply, no glue/composite/friction credit; "
                "pads provide nominal bearing only, supplemental steel/bolts unqualified; STEP profile governs", 1)
        xx = sorted((inner, inner-sign*100))
        sx = sorted((inner, inner-sign*STEEL))
        main = b.block(*xx, 10, 85, 38.1, 44.1).fuse(b.block(*sx, 10, 85, 44.1, 138.1)).clean()
        # Keep the original upper splice screws accessible through the new
        # steel: generic Ø10 head/driver inside Ø12 openings, not rated holes.
        for c in baseline.connections():
            if c.name in (f"cheek_splice_{side}_3", f"cheek_splice_{side}_4"):
                main = main.cut(cq.Solid.makeCylinder(6, 8, c.start-c.direction*7, c.direction)).clean()
        kicker = cq.Solid.makeBox(xx[1]-xx[0], 6, 50, cq.Vector(xx[0], -80.1, 175)).fuse(
            cq.Solid.makeBox(sx[1]-sx[0], -80.1-BACK_Y, 50, cq.Vector(sx[0], BACK_Y, 175))).clean()
        for label, solid, blank in (("main", main, (100., 100., 75.)),
                                    ("kicker", kicker, (100., -74.1-BACK_Y, 50.))):
            name = f"transition_{label}_angle_{side}"
            result[name] = b.Part(name, solid, blank,
                "UNSELECTED custom 6 mm sharp-corner steel angle; not an A21 or a rated product; "
                "bend, steel, holes, head seating, fabrication and resistance unresolved; "
                "main-angle Ø12 access openings preserve old splice screw paths", 1)
        rim = sign*b.HALF
        xx, sx = sorted((rim, rim-sign*140)), sorted((rim, rim-sign*STEEL))
        for label, s0, s1, n1 in (("seam", 1159.35, 1250., 110.),
                                  ("top", 2359.5, 2428.4, 76.2)):
            shape = b.block(*xx, s0, s1, 38.1, 44.1).fuse(b.block(*sx, s0, s1, 44.1, n1)).clean()
            name = f"transition_{label}_angle_{side}"
            result[name] = b.Part(name, shape, (140., n1-38.1, s1-s0),
                "UNSELECTED custom 6 mm sharp-corner rear-face angle; rail side-grain screws "
                "and through-rim bolts; bend, steel, seating, edge distances and resistance unresolved", 1)
        shape = cq.Solid.makeBox(xx[1]-xx[0], 6, 40, cq.Vector(xx[0], -80.1, 5)).fuse(
            cq.Solid.makeBox(sx[1]-sx[0], 64.9, 40, cq.Vector(sx[0], -145., 5))).clean()
        name = f"transition_kicker_bottom_angle_{side}"
        result[name] = b.Part(name, shape, (140., 70.9, 40.),
            "UNSELECTED custom 6 mm rear-face angle, nominal 5 mm floor clearance; "
            "side-grain rail screws and through-cheek bolts; material, tools and resistance unresolved", 1)
    if drilled:
        for c in connections():
            for index, name in enumerate(c.members):
                if not c.name.startswith("transition_") and name not in rebuilt:
                    continue
                part = result[name]
                radius = 5 if c.kind == "bolt" else (2.6 if index == 0 else 1.6)
                shape = part.shape.cut(cq.Solid.makeCylinder(radius, c.length+2, c.start-c.direction, c.direction))
                if c.kind == "screw" and index == 0:
                    shape = shape.cut(c.components()[1])
                result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())
