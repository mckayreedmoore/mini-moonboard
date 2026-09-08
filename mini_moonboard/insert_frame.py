"""Removable-panel insert candidate; no transferred connection qualification.

Threads are occupied-volume envelopes, not helical manufacturing geometry.
Receiver holes in display CAD reserve the insert envelope; the separate pilot
schedule must not be inferred from those displayed holes.
"""
import json
import math
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path

import cadquery as cq

from . import box_frame as b
from . import product_frame as product
from . import timber_connections as hardware
from . import timber_frame as timber
from .bolted_frame import WASHER

KEY = "panel-insert-development"
REFERENCE = json.loads((Path(__file__).resolve().parents[1]/"docs/panel-insert-reference.json").read_text())
INSERT, SCREW, ASSUMPTIONS = (REFERENCE[k] for k in ("insert", "screw", "project_geometry_assumptions"))
PANEL = product.FACE_THICKNESS_MM
LIMITS = "Insert geometry candidate; effective engagement and resistance unqualified; NOT build-ready"


@dataclass(frozen=True)
class PanelMachineScrew(b.Connection):
    product_status: str = "Dottie FMDD14114 1/4-20 x1.25in flat head, E-Z LOK 801420-13 receiver; "+LIMITS

    @property
    def insert_start(self):
        return self.start+self.direction*PANEL

    def components(self):
        # Envelope of the largest head and shallowest included angle. This is
        # a clearance proxy, not the selected machining countersink angle.
        depth = ((SCREW["head_diameter_max"]-self.diameter)/2 /
                 math.tan(math.radians(SCREW["head_angle_min_deg"]/2)))
        return (cq.Solid.makeCylinder(self.diameter/2, self.length-depth,
                                      self.start+self.direction*depth, self.direction),
                cq.Solid.makeCone(SCREW["head_diameter_max"]/2, self.diameter/2,
                                  depth, self.start, self.direction))

    def insert_shape(self):
        outer = cq.Solid.makeCylinder(INSERT["nominal_outer_diameter"]/2,
                                      INSERT["nominal_length"], self.insert_start, self.direction)
        # Nominal thread envelope removes overlap with the screw. The unknown
        # hex recess/runout means this is NOT an effective-engagement model.
        bore = cq.Solid.makeCylinder(self.diameter/2, INSERT["nominal_length"]+2,
                                     self.insert_start-self.direction, self.direction)
        return outer.cut(bore).clean()


@cache
def connections():
    return tuple(PanelMachineScrew(c.name, c.start, c.direction,
                    SCREW["nominal_overall_length"], SCREW["nominal_thread_diameter"], c.members)
                 if isinstance(c, timber.PanelScrew) else c for c in timber.connections())


def panel_connections():
    return tuple(c for c in connections() if isinstance(c, PanelMachineScrew))


@cache
def parts(drilled=True):
    result = {p.name: p for p in timber.wood_parts(drilled)}
    result.update({p.name: p for p in hardware.clip_parts(tuple(hardware.stations(True)))})
    for c in connections():
        if isinstance(c, PanelMachineScrew):
            if drilled:
                panel, receiver = c.members
                shape = result[panel].shape.cut(cq.Solid.makeCylinder(
                    ASSUMPTIONS["panel_clearance_bore_diameter"]/2, PANEL+2,
                    c.start-c.direction, c.direction)).cut(c.components()[1])
                result[panel] = replace(result[panel], shape=shape.clean())
                # Occupied-envelope display cut, NOT the smaller installation pilot.
                tolerance = INSERT["drawing_general_tolerance_plus_minus"]
                envelope = cq.Solid.makeCylinder((INSERT["nominal_outer_diameter"]+tolerance)/2,
                    INSERT["nominal_length"]+tolerance, c.insert_start, c.direction)
                pilot = cq.Solid.makeCylinder(INSERT["pilot_diameter_inch_recommendation"]/2,
                    ASSUMPTIONS["pilot_tip_clearance_depth"], c.insert_start, c.direction)
                shape = result[receiver].shape.cut(envelope).cut(pilot)
                result[receiver] = replace(result[receiver], shape=shape.clean())
            name = "insert_"+c.name
            result[name] = b.Part(name, c.insert_shape(),
                (INSERT["nominal_length"], INSERT["nominal_outer_diameter"], INSERT["nominal_outer_diameter"]),
                "E-Z LOK 801420-13 zinc insert; simplified unthreaded annulus; "+LIMITS, 1)
            continue
        if not drilled:
            continue
        for index, name in enumerate(c.members):
            if name.startswith("clip_"):
                continue
            p = result[name]
            diameter = 11.1125 if c.kind == "bolt" else c.diameter
            shape = p.shape.cut(cq.Solid.makeCylinder(diameter/2, c.length+2,
                c.start-c.direction, c.direction))
            if index == 0 and c.kind == "screw":
                shape = shape.cut(c.components()[1])
            if name == "timber_bottom_backing" and c.name.startswith("timber_backing_bolt_"):
                shape = shape.cut(cq.Solid.makeCylinder(28.575/2, 10.+WASHER,
                    c.start-b.normal()*10., b.normal()))
            result[name] = replace(p, shape=shape.clean())
    return tuple(result.values())
