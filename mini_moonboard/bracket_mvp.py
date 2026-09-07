"""Commercial ML24Z inspection alternative; no custom-metal fabrication.

Factory hole centers, thickness and bend are explicit provisional envelopes,
not instructions to drill, trim or bend a purchased connector. No capacity claim.
"""
from dataclasses import dataclass, replace
from functools import cache

import cadquery as cq

from . import box_frame as b
from . import top_joint_frame as previous
from . import wood_mvp as wood

KEY = "commercial-bracket-mvp"
ML_LEG_MM = 50.8
ML_WIDTH_MM = 101.6
ML_THICKNESS_MM = 2.7  # Project envelope for 12-gauge product, not a tolerance.
TANGENT = (b.point(0, 1, 0)-b.point(0, 0, 0)).normalized()


@dataclass(frozen=True)
class ConnectorScrew(b.Connection):
    product_status: str = (
        "SELECTED Simpson SDS25112 1/4 x 1-1/2 in; nominal shaft and assumed "
        "head envelope; ML24Z factory hole positions are PROVISIONAL, not a "
        "steel drilling instruction; fit and resistance unqualified"
    )
    pilot_diameter_mm: float = 4.

    def components(self):
        return (cq.Solid.makeCylinder(3.175, self.length, self.start, self.direction),
                cq.Solid.makeCylinder(7., 7., self.start, -self.direction))


def _prism(points, vector):
    return cq.Solid.extrudeLinear(cq.Wire.makePolygon(points, close=True), [], vector)


def _connector(origin, u, v):
    """Two external bearing planes; width follows the board's rear normal."""
    w = b.normal()
    t, length, half = ML_THICKNESS_MM, ML_LEG_MM, ML_WIDTH_MM/2
    shape = _prism([origin+w*(-half), origin+u*length-w*half,
                    origin+u*length+w*half, origin+w*half], v*t)
    shape = shape.fuse(_prism([origin-w*half, origin+v*length-w*half,
                               origin+v*length+w*half, origin+w*half], u*t)).clean()
    # Six factory holes required by US catalog. Coordinates below are only
    # an inspection proxy until the actual US drawing/product is identified.
    holes = []
    for index, (offset, along) in enumerate(((-34., 18.), (0., 34.), (34., 18.)), 1):
        holes.append((f"beam_{index}", origin+u*along+w*offset+v*t, -v))
    for index, (offset, along) in enumerate(((-34., 34.), (0., 18.), (34., 34.)), 1):
        holes.append((f"upright_{index}", origin+v*along+w*offset+u*t, -u))
    for _, start, direction in holes:
        shape = shape.cut(cq.Solid.makeCylinder(3.5, t+2, start-direction, direction))
    return shape.clean(), holes


def stations():
    """Two side spans per level; the central service gap remains open."""
    for level, (s0, s1) in wood.BEAMS.items():
        # Lower splice stock reaches S100: place these clips above the beam,
        # S138.1..188.9, rather than in the retained splice's rear volume.
        station, direction = (s1, TANGENT) if level == "lower" else (s0, -TANGENT)
        for side in ("left", "right"):
            x0, x1 = wood.PRINCIPALS[side]
            endpoints = ((-b.HALF, 1., "box_side_left"),
                         (x0, -1., "wood_principal_left")) if side == "left" else (
                         (x1, 1., "wood_principal_right"),
                         (b.HALF, -1., "box_side_right"))
            for index, (x, sign, upright) in enumerate(endpoints, 1):
                yield (f"clip_mvp_{level}_{side}_{index}", b.point(x, station, 107.95),
                       cq.Vector(sign, 0, 0), direction,
                       f"wood_beam_{level}_{side}", upright)


@cache
def connections():
    result = [c for c in wood.connections() if not c.name.startswith("wood_deep_lap_")]
    for name, origin, u, v, beam, upright in stations():
        _, holes = _connector(origin, u, v)
        for suffix, start, direction in holes:
            member = beam if suffix.startswith("beam_") else upright
            result.append(ConnectorScrew(f"{name}_{suffix}", start, direction,
                                         38.1, 6.35, (name, member)))
    return tuple(result)


@cache
def parts(drilled=True):
    # Reuse face ledges, plywood profiles and service provisions. Replace only
    # the deep housed intersections with continuous supports and butt spans.
    result = {p.name: replace(p, description=p.description.replace(
                  "WOOD-FIRST MVP", "COMMERCIAL-BRACKET MVP")) for p in wood.parts(False)
              if not p.name.startswith(("wood_principal_", "wood_beam_"))}
    for part in previous.parts(False):
        if part.name.startswith("box_side_"):
            result[part.name] = replace(part, description=
                "Original rim datum restored without deep beam housings; commercial-bracket MVP; unqualified")
    for side, (x0, x1) in wood.PRINCIPALS.items():
        name = f"wood_principal_{side}"
        result[name] = b.Part(name, b.block(x0, x1, 0, b.LENGTH, 38.1, 177.8),
            (b.LENGTH, 139.7, 38.1), "Continuous on-edge 2x6 central support; no deep half-lap; grain S; unqualified", 1)
    for level, (s0, s1) in wood.BEAMS.items():
        for side, (x0, x1) in {
            "left": (-b.HALF, wood.PRINCIPALS["left"][0]),
            "right": (wood.PRINCIPALS["right"][1], b.HALF),
        }.items():
            name = f"wood_beam_{level}_{side}"
            result[name] = b.Part(name, b.block(x0, x1, s0, s1, 38.1, 177.8),
                (x1-x0, 139.7, s1-s0),
                "On-edge 2x6 butt-ended side span, grain X; central service gap open; commercial clips, unqualified", 1)
    for name, origin, u, v, _, _ in stations():
        shape, _ = _connector(origin, u, v)
        result[name] = b.Part(name, shape, (101.6, 50.8, 50.8),
            "SELECTED commercial Simpson ML24Z, 12 gauge, 2x2x4 in; six SDS25112 screws separately supplied. "
            "PROVISIONAL factory-hole coordinates, 2.7 mm thickness and sharp bend proxy; "
            "not a steel drilling, cutting or bending instruction. Actual purchased geometry, tool access "
            "and resistance require verification; no custom metal fabrication", 1)
    return wood.drill_parts(result, connections()) if drilled else tuple(result.values())
