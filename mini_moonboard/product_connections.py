"""Selected-product connection envelopes; not strength or machining approval.

Kept separate from frozen reference geometry. Head cylinders deliberately bound
all hex rotations; screw seats are labeled project allowances, not exact teeth
or taper geometry. Receiving-part holes are not changed by this module.
"""
from dataclasses import dataclass

import cadquery as cq

from .box_frame import Connection
from .selected_hardware import BoltSpec, spec_for


@dataclass(frozen=True)
class ProductConnection(Connection):
    @property
    def product_status(self):
        spec = spec_for(self)
        return (f"SELECTED {spec.product}; dimensional inspection envelope only; "
                "hex rotation bounded by cylinder; screw head/seat allowances are "
                "project assumptions; receiving holes and resistance require verification")

    def components(self):
        spec = spec_for(self)
        d = self.direction.normalized()
        if isinstance(spec, BoltSpec):
            # Nominal axial washer thickness, maximum radial collision envelope.
            t = spec.washer_thickness_nominal_mm
            shaft = cq.Solid.makeCylinder(spec.body_diameter_max_mm/2,
                                          self.length, self.start, d)

            def washer(start):
                return cq.Solid.makeCylinder(spec.washer_od_max_mm/2, t, start, d).cut(
                    cq.Solid.makeCylinder(spec.washer_id_min_mm/2, t, start, d))

            head = cq.Solid.makeCylinder(spec.head_across_corners_max_mm/2,
                                        spec.head_height_max_mm, self.start, -d)
            nut_start = self.start+d*(2*t+self.grip)
            nut = cq.Solid.makeCylinder(spec.nut_across_corners_max_mm/2,
                                       spec.nut_height_max_mm, nut_start, d).cut(
                cq.Solid.makeCylinder(spec.body_diameter_max_mm/2,
                                      spec.nut_height_max_mm, nut_start, d))
            return shaft, washer(self.start), washer(self.start+d*(t+self.grip)), head, nut
        shaft = cq.Solid.makeCylinder(spec.major_diameter_nominal_mm/2,
                                      self.length, self.start, d)
        head = cq.Solid.makeCylinder(spec.head_allowance_diameter_mm/2,
                                    spec.head_allowance_height_mm, self.start,
                                    d if spec.seating == "flush" else -d)
        return shaft, head


def selected_connection(connection):
    """Keep reference member bearing planes; update product size, not layout.

    Reference bolts place the first member 2 mm after their start. Selected
    washers use a different thickness, so moving the start preserves both ends
    of the physical grip. Face-stock thickness changes belong to the part/layout
    candidate, not to this conversion.
    """
    spec = spec_for(connection)
    if isinstance(connection, ProductConnection):
        return connection
    d = connection.direction.normalized()
    start = connection.start
    if isinstance(spec, BoltSpec):
        start = start+d*(2-spec.washer_thickness_nominal_mm)
        length, diameter = spec.length_mm, spec.diameter_nominal_mm
    else:
        length, diameter = spec.length_nominal_mm, spec.major_diameter_nominal_mm
    return ProductConnection(connection.name, start, d, length, diameter,
                             connection.members, connection.kind, connection.grip)
