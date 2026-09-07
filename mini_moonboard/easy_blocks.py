"""Square-cut, mechanically retained wood-block inspection alternative.

No joint capacity, clamp friction, end-grain withdrawal or glue credit. Ordinary
bolt envelopes are provisional products; actual stock, spacing and access need
verification before any construction release.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import bracket_mvp as bracket
from . import easy_frame as baseline
from . import wood_mvp as wood

KEY = "square-cut-wood-blocks"
BLOCK_X_MM = 88.9
BLOCK_S_MM = 38.1
BLOCK_N_MM = 139.7


@dataclass(frozen=True)
class BlockBolt(b.Connection):
    product_status: str = (
        "PROVISIONAL ordinary 3/8-16 hex through-bolt, nut and two flat washers; "
        "catalog SKU, grade, manufactured tolerances and threaded bearing unqualified. "
        "Nominal washerOD25.4 thickness2 headOD18 height6 nutOD18 height9; "
        "no clamp-friction, glue or end-grain withdrawal credit"
    )

    def components(self):
        d = self.direction
        shaft = cq.Solid.makeCylinder(self.diameter/2, self.length, self.start, d)

        def ring(radius, length, start):
            return cq.Solid.makeCylinder(radius, length, start, d).cut(
                cq.Solid.makeCylinder(5.6, length, start, d))

        return (shaft, ring(12.7, 2., self.start),
                ring(12.7, 2., self.start+d*(2+self.grip)),
                cq.Solid.makeCylinder(9., 6., self.start, -d),
                ring(9., 9., self.start+d*(4+self.grip)))


def block_layout():
    """Name, corner, side axes and actual receiving members for twelve blocks."""
    for name, origin, u, v, beam, upright in bracket.stations():
        yield name.replace("clip_mvp_", "wood_joint_block_"), origin, u, v, beam, upright


def block_shape(origin, u, v):
    # Standard 2x4 cross-section is X88.9 by S38.1. Grain follows N; each
    # offcut is 139.7 long along grain, so X/S bolts both cross side grain.
    w = b.normal()*BLOCK_N_MM/2
    wire = cq.Wire.makePolygon([origin-w, origin+u*BLOCK_X_MM-w,
                               origin+u*BLOCK_X_MM+w, origin+w], close=True)
    return cq.Solid.extrudeLinear(wire, [], v*BLOCK_S_MM)


@cache
def connections():
    result = [c for c in baseline.connections() if not c.name.startswith("clip_mvp_")]
    for name, origin, u, v, beam, upright in block_layout():
        for index, n in enumerate((-25., 25.), 1):
            result.append(BlockBolt(f"{name}_upright_{index}",
                origin+u*(BLOCK_X_MM+2)+v*(BLOCK_S_MM/2)+b.normal()*n, -u,
                152.4, 9.525, (name, upright), "bolt", 127.))
        # Enter from the beam's opposite face, crossing its 38.1 mm thickness
        # and the block's 38.1 mm width. The axis is 63.5 mm inward from the
        # upright: its 12.7 mm-radius washer clears the retained 38.1 mm-wide
        # lower splice, unlike an axis centered in the original narrow block.
        # Retains either opening direction;
        # the lower blocks are uphill stops, not claimed gravity seats.
        result.append(BlockBolt(f"{name}_beam", origin-v*40.1+u*63.5,
            v, 95.25, 9.525, (beam, name), "bolt", 76.2))
    return tuple(result)


@cache
def parts(drilled=True):
    result = {p.name: replace(p, description=p.description.replace(
                  "COMMERCIAL-BRACKET MVP", "SQUARE-CUT WOOD-BLOCK MVP"))
              for p in baseline.parts(False) if not p.name.startswith("clip_mvp_")}
    for name, origin, u, v, _, _ in block_layout():
        result[name] = b.Part(name, block_shape(origin, u, v),
            (BLOCK_N_MM, BLOCK_S_MM, BLOCK_X_MM),
            "Square-cut 2x4 offcut, 139.7 mm along grain N; section88.9X x38.1S. "
            "Two side-grain through-bolts to upright/rim and one side-grain through-bolt "
            "to rail; contact stop plus mechanical retention, not friction or end-grain withdrawal. "
            "Lower blocks above rails, other levels below; stock, bolt products, edge/spacing, "
            "tool access and resistance unqualified; no custom steel", 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
