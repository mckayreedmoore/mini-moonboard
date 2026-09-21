"""Separate top-rim end-distance revision; fit and resistance remain unqualified.

Only four receiving bodies are rebuilt. The remaining selected-product geometry
and all hardware choices stay unchanged; no new FEA or capacity is implied.
"""
from dataclasses import replace
from functools import cache

from . import box_frame as b
from . import product_frame as baseline
from .selected_hardware import SD9112, SDS25112, BoltSpec, spec_for

KEY = "top-joint-development"
TOP_BOLT_STATIONS_MM = (2328., 2368.)
TOP_BOLT_NORMAL_MM = 63.
RIM_LEAF_START_MM = 2313.
ORIGINAL_LEAF_START_MM = 2359.5
LEAF_END_MM = 2428.4
REBUILT_NAMES = frozenset(
    f"{prefix}_{side}"
    for prefix in ("box_side", "transition_top_angle")
    for side in ("left", "right")
)


@cache
def connections():
    moved = {
        f"transition_top_{side}_bolt_{index}": station
        for side in ("left", "right")
        for index, station in enumerate(TOP_BOLT_STATIONS_MM, 1)
    }
    result = []
    for c in baseline.connections():
        if c.name in moved:
            station = (c.start-b.point(0, 0, 0)).dot(baseline.TANGENT)
            c = replace(c, start=c.start+baseline.TANGENT*(moved[c.name]-station))
        result.append(c)
    return tuple(result)


@cache
def parts(drilled=True):
    # Reuse all unaffected drilled bodies exactly, but never reuse old bores in
    # the four receivers: even unchanged incident connections are recut below.
    result = {p.name: p for p in baseline.parts(drilled)}
    raw = {p.name: p for p in baseline.parts(False)} if drilled else result.copy()
    for name in REBUILT_NAMES:
        result[name] = raw[name]
    for side, sign in (("left", -1), ("right", 1)):
        name = f"transition_top_angle_{side}"
        part = raw[name]
        rim = sign*b.HALF
        x0, x1 = sorted((rim, rim-sign*6.))
        extension = b.block(x0, x1, RIM_LEAF_START_MM, ORIGINAL_LEAF_START_MM, 44.1, 76.2)
        result[name] = replace(part, shape=part.shape.fuse(extension).clean(),
            blank=(140., 38.1, LEAF_END_MM-RIM_LEAF_START_MM),
            description="UNSELECTED custom 6 mm steel top angle; only rim-facing leaf extended "
            "downhill to S2313; rail-facing leaf and screw stations retained; "
            "STEP stepped profile governs. Nominal end-distance revision, unqualified; "
            "bend, fabrication, seating, installation and resistance unresolved; no capacity credit")
    if not drilled:
        return tuple(result.values())
    for c in connections():
        spec = spec_for(c)
        for index, name in enumerate(c.members):
            if name not in REBUILT_NAMES:
                continue
            if isinstance(spec, BoltSpec):
                diameter = baseline.BOLT_HOLE_DIAMETER_MM
            elif spec is SD9112:
                diameter = baseline.SD_PILOT_DIAMETER_MM
            elif spec is SDS25112:
                diameter = baseline.SDS_STEEL_HOLE_DIAMETER_MM if index == 0 else baseline.SDS_PILOT_DIAMETER_MM
            else:
                diameter = (baseline.R4_CLEARANCE_DIAMETER_MM if index < len(c.members)-1
                            else baseline.R4_PILOT_DIAMETER_MM)
            part = result[name]
            shape = baseline._bore(part.shape, diameter, c.length+2, c.start-c.direction, c.direction)
            if not isinstance(spec, BoltSpec) and spec.seating == "flush" and index == 0:
                shape = shape.cut(c.components()[1])
            result[name] = replace(part, shape=shape.clean())
    return tuple(result.values())
