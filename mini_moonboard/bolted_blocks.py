"""Wider, square-cut wood-block alternative with provisional quarter-inch bolts.

Improved geometric margins are not a joint capacity qualification. In particular,
smaller bolts need independent steel, wood bearing, splitting and group checks.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import bolted_frame as baseline
from . import box_frame as b

KEY = "bolted-block-frame"
BLOCK_X_MM = 88.9
BLOCK_S_MM = 88.9
BLOCK_N_MM = 139.7
BOLT_DIAMETER_MM = 6.35
BOLT_LENGTH_MM = 190.5
BOLT_GRIP_MM = 177.8
BOLT_CLEARANCE_MM = 7.14375
WASHER_THICKNESS_MM = 1.6


@dataclass(frozen=True)
class BlockBolt(b.Connection):
    product_status: str = (
        "Commercial 1/4-20 x 7-1/2 or 9 in through-bolt, nut and two SAE-size "
        "flat washers; final grade, thread length and manufactured tolerances unqualified. "
        "Inspection washer OD15.875 thickness1.6, head OD13.5 height5, nut OD13.5 height5.56; "
        "head cylinders are all-rotation allowances, not exact hexes; no clamp-friction or glue credit. "
        "Geometric edge screening does not qualify bolt or wood resistance"
    )

    def components(self):
        direction = self.direction

        def ring(radius, length, start):
            return cq.Solid.makeCylinder(radius, length, start, direction).cut(
                cq.Solid.makeCylinder(3.6, length, start, direction))

        return (
            cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, direction),
            ring(7.9375, WASHER_THICKNESS_MM, self.start),
            ring(7.9375, WASHER_THICKNESS_MM,
                 self.start+direction*(WASHER_THICKNESS_MM+self.grip)),
            cq.Solid.makeCylinder(6.75, 5., self.start, -direction),
            ring(6.75, 5.56, self.start+direction*(2*WASHER_THICKNESS_MM+self.grip)),
        )


def block_layout():
    """Keep A's beam endpoints, including lower uphill stops, not gravity seats."""
    for name, origin, u, v, beam, upright in baseline.stations():
        yield name.replace("clip_mvp_", "wood_joint_block_"), origin, u, v, beam, upright


def block_shape(origin, u, v):
    half_depth = b.normal()*BLOCK_N_MM/2
    wire = cq.Wire.makePolygon([
        origin-half_depth, origin+u*BLOCK_X_MM-half_depth,
        origin+u*BLOCK_X_MM+half_depth, origin+half_depth,
    ], close=True)
    return cq.Solid.extrudeLinear(wire, [], v*BLOCK_S_MM)


@cache
def connections():
    result = [c for c in baseline.connections() if not c.name.startswith("clip_mvp_")]
    for name, origin, u, v, beam, upright in block_layout():
        for index, offset in enumerate((-20., 20.), 1):
            outer = "edge" in upright
            side = upright.rsplit("_", 1)[1]
            members = (name, upright, f"box_side_{side}") if outer else (name, upright)
            result.append(BlockBolt(
                f"{name}_upright_{index}",
                origin+u*(BLOCK_X_MM+WASHER_THICKNESS_MM)
                +v*(BLOCK_S_MM/2)+b.normal()*offset,
                -u, 228.6 if outer else BOLT_LENGTH_MM, BOLT_DIAMETER_MM,
                members, "bolt", 215.9 if outer else BOLT_GRIP_MM,
            ))
        result.append(BlockBolt(
            f"{name}_beam", origin-v*(88.9+WASHER_THICKNESS_MM)+u*57.15,
            v, BOLT_LENGTH_MM, BOLT_DIAMETER_MM, (beam, name), "bolt", BOLT_GRIP_MM,
        ))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {
        p.name: replace(p, description=p.description.replace(
            "BOLTED CONNECTOR FRAME", "BOLTED WOOD-BLOCK FRAME"))
        for p in baseline.parts(False) if not p.name.startswith("clip_mvp_")
    }
    for name, origin, u, v, _, _ in block_layout():
        result[name] = b.Part(
            name, block_shape(origin, u, v), (BLOCK_N_MM, BLOCK_S_MM, BLOCK_X_MM),
            "Square-cut nominal 4x4 offcut, actual88.9X x88.9S with139.7mm grain N. "
            "Two quarter-inch side-grain through-bolts to upright/rim and one to beam. "
            "Lower blocks are uphill stops; other levels have downhill bearing seats. "
            "No glue, clamp-friction or end-grain withdrawal credit. Stock grade, "
            "bolt resistance, directional joint loads and group behavior unqualified", 1,
        )
    return baseline.drill_parts(result, connections()) if drilled else tuple(result.values())
