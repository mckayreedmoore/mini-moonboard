"""Round-variant SPAX #8 nominal 90-degree countersunk head and shank envelope.

The US CP-XF_08 drawing supplies the head/shank diameters and included angle.
The selected XFT08P-2000 Table 2 nominal thread region includes the tapered tip.
Sharp transitions, solid thread envelope and omitted ribs/tip are idealizations.
"""
from dataclasses import fields

import cadquery as cq

from .timber_frame import PanelScrew

HEAD_DIAMETER_MM = 8.128
SHANK_DIAMETER_MM = 2.921
HEAD_INCLUDED_ANGLE_DEG = 90.
HEAD_HEIGHT_MM = (HEAD_DIAMETER_MM-SHANK_DIAMETER_MM)/2
NOMINAL_THREAD_LENGTH_MM = 31.496
LIMITS = ('US CP-XF_08 nominal 90-degree flat head and 0.115-inch shank; sharp head/neck '
          'and shank/thread transitions idealized; ribs, thread helices and tapered tip '
          'omitted; occupied geometry is not a pilot-drilling specification')


class CountersunkPanelScrew(PanelScrew):
    def components(self):
        neck_length = self.length-NOMINAL_THREAD_LENGTH_MM
        if neck_length < HEAD_HEIGHT_MM:
            raise ValueError('Selected screw length cannot contain the modeled head and unthreaded shank')
        shank = cq.Solid.makeCylinder(SHANK_DIAMETER_MM/2, neck_length, self.start, self.direction)
        thread = cq.Solid.makeCylinder(self.diameter/2, NOMINAL_THREAD_LENGTH_MM,
                                       self.start+self.direction*neck_length, self.direction)
        return shank.fuse(thread).clean(), self.head_recess()

    def head_recess(self):
        """Exact nominal head envelope; no extra countersink depth or pilot rule."""
        return cq.Solid.makeCone(HEAD_DIAMETER_MM/2, SHANK_DIAMETER_MM/2,
                                 HEAD_HEIGHT_MM, self.start, self.direction)


def with_countersunk_head(connection):
    if not isinstance(connection, PanelScrew):
        return connection
    values = {field.name: getattr(connection, field.name) for field in fields(connection)}
    values['product_status'] += '; '+LIMITS
    return CountersunkPanelScrew(**values)
