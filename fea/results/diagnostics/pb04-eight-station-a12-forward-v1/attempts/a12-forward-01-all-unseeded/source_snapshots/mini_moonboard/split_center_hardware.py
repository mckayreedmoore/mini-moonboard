"""Inspectable hex bolt ends for the new split-center candidate only."""
from dataclasses import fields
from math import cos, pi

import cadquery as cq

from .bolted_frame import WASHER, FrameBolt
from .selected_hardware import BoltSpec

BOLT_ROLES = ('shaft', 'near_washer', 'far_washer', 'head', 'nut')
HEX_LIMITS = ('Regular hex head/nut geometry within documented maximum flats/corners; '
              'no threads or chamfers modeled; hardware and joint resistance unqualified')


class HexFrameBolt(FrameBolt):
    def components(self):
        """Keep the historical five-component order and all axial placements."""
        shaft, near, far, _, _ = super().components()
        spec = BoltSpec('Selected dimensional family', self.length, self.grip, 0.)
        axis = self.direction.normalized()

        def hex_prism(start, direction, height, flats, corners):
            diameter = min(corners, flats/cos(pi/6))
            plane = cq.Plane(origin=start, normal=direction)
            return cq.Workplane(plane).polygon(6, diameter).extrude(height).val()

        head = hex_prism(self.start, -axis, spec.head_height_max_mm,
                         spec.head_across_flats_max_mm, spec.head_across_corners_max_mm)
        nut_start = self.start+axis*(2*WASHER+self.grip)
        nut = hex_prism(nut_start, axis, spec.nut_height_max_mm,
                       spec.nut_across_flats_max_mm, spec.nut_across_corners_max_mm)
        nut = nut.cut(cq.Solid.makeCylinder(spec.body_diameter_max_mm/2,
                                           spec.nut_height_max_mm, nut_start, axis))
        return shaft, near, far, head, nut


def with_hex_ends(connection):
    """Wrap only through-bolts; preserve screws and every placement parameter."""
    if isinstance(connection, FrameBolt):
        values = {field.name: getattr(connection, field.name) for field in fields(connection)}
        values['product_status'] += '; '+HEX_LIMITS
        return HexFrameBolt(**values)
    return connection
