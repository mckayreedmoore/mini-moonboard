"""Isolated standard-hardware leg trial; no strength or purchase approval.

Four MCX washers per bolt (two at each end), not a bonded thick plate.
Wood geometry and all non-leg connections remain the frozen spread candidate.
"""
import math
from dataclasses import dataclass
from functools import cache

import cadquery as cq

from . import lumber_leg_spread_frame as base
from .bolted_frame import WASHER, FrameBolt
from .selected_hardware import BoltSpec

BOLT_LENGTH = 107.95
BOLT_LENGTH_SHORTFALL = 2.54  # 4.25in is in the >4–6in length-tolerance band.
THREAD_PITCH = 25.4/16
THREAD_REFERENCE = 25.4
WASHER_MIN, WASHER_MAX = .110*25.4, .126*25.4
WASHER_NOMINAL = (WASHER_MIN+WASHER_MAX)/2
WASHER_OD_MAX, WASHER_ID_MIN = 1.015*25.4, .433*25.4
STOCK_MIN, STOCK_MAX = 37.5, 38.5  # Project acceptance window, not lumber tolerances.
LIMITS = "Development hardware trial; stock window and product compliance unverified; NOT build-ready"
SOURCES = {
    "bolt": "https://boltsandnuts.com/products/3-8-16x4-1-4-hex-cap-screws-grade-5-bolts-zinc-clear",
    "washers": "https://www.wroughtwasher.com/standard-washers/extra-thick-mil-carb-mcx/",
    "nut": "https://boltsandnuts.com/products/3-8-16-grade-5-finished-hex-nuts-zinc-clear",
    "body_length": "https://www.nickel-systems.com/blog/what-are-max-grip-gaging-min-body-lengths",
}


def dimensional_window(rim, leg):
    """Worst washer dimensions; generic body/gaging limits, not supplier proof."""
    if not all(math.isfinite(v) and STOCK_MIN <= v <= STOCK_MAX for v in (rim, leg)):
        raise ValueError("Stock must be measured within the project 37.5–38.5 mm window")
    body_min = BOLT_LENGTH-THREAD_REFERENCE-5*THREAD_PITCH
    gaging_max = BOLT_LENGTH-THREAD_REFERENCE
    required_body = 2*WASHER_MAX+rim+.75*leg
    nut_seat_min = 4*WASHER_MIN+rim+leg
    # Matches the 37CFHN5Z drawing's .337in maximum nut height.
    nut_max = BoltSpec("Envelope only", BOLT_LENGTH, rim+leg, BOLT_LENGTH_SHORTFALL).nut_height_max_mm
    projection_min = BOLT_LENGTH-BOLT_LENGTH_SHORTFALL-4*WASHER_MAX-rim-leg-nut_max
    return {"required_body_mm": required_body, "generic_body_min_mm": body_min,
        "body_margin_mm": body_min-required_body, "generic_gaging_max_mm": gaging_max,
        "nut_seat_min_mm": nut_seat_min, "seating_margin_mm": nut_seat_min-gaging_max,
        "tip_projection_min_mm": projection_min,
        "complete_thread_projection_verified": False, "qualified_for_design": False}


@dataclass(frozen=True)
class TrialBolt(FrameBolt):
    washer_thickness: float = WASHER_NOMINAL

    def components(self):
        # Keep the predecessor's conservative shaft/head/nut envelopes. These
        # bound the new catalog dimensions; no strength assigned by these bounds.
        spec = BoltSpec("Conservative catalog envelope", self.length, self.grip, BOLT_LENGTH_SHORTFALL)
        d, t = self.direction.normalized(), self.washer_thickness
        radius = spec.body_diameter_max_mm/2
        def ring(outer, inner, thick, start):
            return cq.Solid.makeCylinder(outer/2, thick, start, d).cut(
                cq.Solid.makeCylinder(inner/2, thick, start, d))
        washers = tuple(ring(WASHER_OD_MAX, WASHER_ID_MIN, t, self.start+d*s)
                        for s in (0., t, 2*t+self.grip, 3*t+self.grip))
        return (cq.Solid.makeCylinder(radius, self.length, self.start, d), *washers,
            cq.Solid.makeCylinder(spec.head_across_corners_max_mm/2,
                                 spec.head_height_max_mm, self.start, -d),
            ring(spec.nut_across_corners_max_mm, spec.body_diameter_max_mm,
                 spec.nut_height_max_mm, self.start+d*(4*t+self.grip)))


@cache
def connections(washer_thickness=WASHER_NOMINAL):
    if not math.isfinite(washer_thickness) or not WASHER_MIN <= washer_thickness <= WASHER_MAX:
        raise ValueError("Require the published MCX thickness interval")
    result = []
    for c in base.connections("2x6", 300.):
        if c.name.startswith("lumber_leg_bolt_"):
            c = TrialBolt(c.name, c.start-c.direction*(2*washer_thickness-WASHER),
                c.direction, BOLT_LENGTH, c.diameter, c.members, c.kind, c.grip,
                product_status=LIMITS+"; 3/8-16 x4.25in; four Wrought 014423 washers",
                washer_thickness=washer_thickness)
        result.append(c)
    return tuple(result)


def parts():
    return base.parts("2x6", 300.)
