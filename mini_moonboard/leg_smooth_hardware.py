"""Isolated smooth-shank leg hardware candidate; no released design change.

The original frame and its eight leg holes remain unchanged. Material grades
and acceptance dimensions below are purchase/fabrication requirements, not
claims about hardware already owned. No clamp friction is credited.
"""
import json
import math
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import cadquery as cq

from . import round_reinforcement_frame as base
from .bolted_frame import WASHER, FrameBolt
from .selected_hardware import BoltSpec

BOLT_LENGTH = 127.0
BOLT_LENGTH_SHORTFALL = 2.54
THREAD_PITCH = 25.4 / 16
THREAD_REFERENCE = 25.4
STOCK_MIN, STOCK_MAX = 37.5, 38.5
PLATE_OD, PLATE_ID, PLATE_THICKNESS = 38.1, 11.1125, 6.35
SPACER_OD, SPACER_ID, SPACER_LENGTH = 20.0, 11.1125, 19.05
STEEL_DENSITY_KG_MM3 = 7.85e-6
LIMITS = "Review candidate only; Grade 5 bolt/nut, A36 plate washers; no assembly strength qualification"
COMPONENT_LABELS = ("shaft", "head_plate", "nut_plate", "spacer", "head", "nut")


def dimensional_window(rim, leg):
    """Acceptance window with shortened bolt and conservative thread runout.

Plate and spacer dimensions are required finished dimensions. Supplier thread
length must be confirmed against the assumed 25.4 mm reference and five-pitch
runout; a generic bolt description does not establish that compliance.
"""
    if not all(math.isfinite(v) and STOCK_MIN <= v <= STOCK_MAX for v in (rim, leg)):
        raise ValueError("Stock must measure within 37.5–38.5 mm")
    spec = BoltSpec("Grade 5 dimensional acceptance envelope", BOLT_LENGTH, rim + leg, BOLT_LENGTH_SHORTFALL)
    body_min = BOLT_LENGTH - BOLT_LENGTH_SHORTFALL - THREAD_REFERENCE - 5 * THREAD_PITCH
    required_body = PLATE_THICKNESS + rim + leg
    gaging_max = BOLT_LENGTH - THREAD_REFERENCE
    nut_seat = 2 * PLATE_THICKNESS + rim + leg + SPACER_LENGTH
    projection = BOLT_LENGTH - BOLT_LENGTH_SHORTFALL - nut_seat - spec.nut_height_max_mm
    return {
        "minimum_smooth_body_mm": body_min,
        "required_smooth_body_mm": required_body,
        "smooth_body_margin_mm": body_min - required_body,
        "maximum_gaging_length_mm": gaging_max,
        "nut_seat_mm": nut_seat,
        "nut_seating_margin_mm": nut_seat - gaging_max,
        "minimum_tip_projection_mm": projection,
        "two_threads_mm": 2 * THREAD_PITCH,
        "two_thread_margin_mm": projection - 2 * THREAD_PITCH,
        "dimensional_acceptance_pass": body_min >= required_body and nut_seat >= gaging_max and projection >= 2 * THREAD_PITCH,
        "qualified_for_design": False,
    }


@dataclass(frozen=True)
class SmoothBolt(FrameBolt):
    """Individually selectable conservative envelopes; thread surface omitted."""

    def components(self):
        spec = BoltSpec("Grade 5 acceptance envelope", self.length, self.grip, BOLT_LENGTH_SHORTFALL)
        d = self.direction.normalized()

        def ring(outer, inner, thickness, station):
            start = self.start + d * station
            return cq.Solid.makeCylinder(outer / 2, thickness, start, d).cut(
                cq.Solid.makeCylinder(inner / 2, thickness, start, d))

        return (
            cq.Solid.makeCylinder(spec.body_diameter_max_mm / 2, self.length, self.start, d),
            ring(PLATE_OD, PLATE_ID, PLATE_THICKNESS, 0),
            ring(PLATE_OD, PLATE_ID, PLATE_THICKNESS, PLATE_THICKNESS + self.grip),
            ring(SPACER_OD, SPACER_ID, SPACER_LENGTH, 2 * PLATE_THICKNESS + self.grip),
            cq.Solid.makeCylinder(spec.head_across_corners_max_mm / 2, spec.head_height_max_mm, self.start, -d),
            ring(spec.nut_across_corners_max_mm, spec.body_diameter_max_mm,
                 spec.nut_height_max_mm, 2 * PLATE_THICKNESS + self.grip + SPACER_LENGTH),
        )


@cache
def connections():
    result = []
    for original in base.connections():
        if original.name.startswith("lumber_leg_bolt_"):
            original = SmoothBolt(
                original.name, original.start - original.direction.normalized() * (PLATE_THICKNESS - WASHER),
                original.direction, BOLT_LENGTH, original.diameter, original.members,
                original.kind, original.grip, product_status=LIMITS,
            )
        result.append(original)
    return tuple(result)


def parts():
    return base.parts()


def mass_summary():
    """Bounding cylindrical head/nut envelopes overestimate finished hex mass."""
    old = {c.name: c for c in base.connections()}
    changed = [c for c in connections() if isinstance(c, SmoothBolt)]
    new_mass = sum(s.Volume() for c in changed for s in c.components()) * STEEL_DENSITY_KG_MM3
    old_mass = sum(s.Volume() for c in changed for s in old[c.name].components()) * STEEL_DENSITY_KG_MM3
    return {"new_hardware_upper_bound_kg": new_mass, "old_hardware_envelope_kg": old_mass,
            "net_added_envelope_kg": new_mass - old_mass, "added_mass_allowance_kg": 2.0,
            "even_total_new_hardware_below_allowance": new_mass <= 2.0}


def export_review(directory):
    """Export candidate hardware only; original assembly stays unchanged."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    assembly = cq.Assembly(name="leg_smooth_hardware_review")
    for bolt in connections():
        if isinstance(bolt, SmoothBolt):
            for label, shape in zip(COMPONENT_LABELS, bolt.components(), strict=True):
                assembly.add(shape, name=f"{bolt.name}_{label}")
    assembly.save(str(target / "hardware.step"))
    report = {"status": LIMITS, "parent_variant": base.KEY, "changed_leg_bolts": 8,
              "dimensional_corners": [dimensional_window(r, l) for r in (STOCK_MIN, STOCK_MAX) for l in (STOCK_MIN, STOCK_MAX)],
              "mass": mass_summary(), "selected_variant_changed": False,
              "wood_geometry_changed": False}
    (target / "review.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def geometry_review():
    """Check nominal solids, adjacent hardware and complete washer support.

This is a geometry check only. Face support is checked by translating each
plate into its wood member and measuring unsupported ring volume.
"""
    wood = {p.name: p.shape for p in parts()}
    hardware = {c.name: c.components() for c in connections()}
    changed = [c for c in connections() if isinstance(c, SmoothBolt)]
    failures = []
    maximum_overlap = 0.0
    maximum_unsupported = 0.0

    def overlap(a, b):
        aa, bb = a.BoundingBox(), b.BoundingBox()
        if (min(aa.xmax, bb.xmax) - max(aa.xmin, bb.xmin) < 1e-7 or
                min(aa.ymax, bb.ymax) - max(aa.ymin, bb.ymin) < 1e-7 or
                min(aa.zmax, bb.zmax) - max(aa.zmin, bb.zmin) < 1e-7):
            return 0.0
        return a.intersect(b).Volume()

    for bolt in changed:
        components = hardware[bolt.name]
        for label, component in zip(COMPONENT_LABELS, components, strict=True):
            if not component.isValid() or component.Volume() <= 0:
                failures.append([bolt.name, label, "invalid solid"])
            for name, shape in wood.items():
                volume = overlap(component, shape)
                maximum_overlap = max(maximum_overlap, volume)
                if volume > 0.01:
                    failures.append([bolt.name, label, name, volume])
            for name, other_components in hardware.items():
                if name == bolt.name:
                    continue
                for other in other_components:
                    volume = overlap(component, other)
                    maximum_overlap = max(maximum_overlap, volume)
                    if volume > 0.01:
                        failures.append([bolt.name, label, name, volume])
        ordered_members = sorted(bolt.members, key=lambda name: (wood[name].Center() - bolt.start).dot(bolt.direction))
        for index, sign, member in ((1, 1, ordered_members[0]), (2, -1, ordered_members[1])):
            shifted = components[index].translate(bolt.direction.normalized() * (sign * PLATE_THICKNESS))
            unsupported = max(0.0, shifted.Volume() - shifted.intersect(wood[member]).Volume())
            maximum_unsupported = max(maximum_unsupported, unsupported)
            if unsupported > 0.01:
                failures.append([bolt.name, COMPONENT_LABELS[index], member, "unsupported", unsupported])
    return {"nominal_geometry_pass": not failures, "failures": failures,
            "maximum_overlap_mm3": maximum_overlap,
            "maximum_unsupported_plate_volume_mm3": maximum_unsupported,
            "strength_qualified": False}
