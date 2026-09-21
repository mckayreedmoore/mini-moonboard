"""Final spacing-screened bolt layout on the unchanged upper225 leg body."""
import cadquery as cq
import numpy as np

from . import compact_three_leg_options as original

KEY = 'compact-three-leg-upper225-refined-development'
LAYOUT_PARAMETERS = (76.,68.,3,10.,25.)
SCREEN_SOURCE = 'fea/results/compact-next-study/position-layouts-spacing.json'


class Candidate(original.Candidate):
    def __post_init__(self):
        super().__post_init__()
        if self.label != 'upper225':
            raise ValueError('Refinement requires the unchanged upper225 leg body')

    @property
    def KEY(self):
        return KEY

    @property
    def __file__(self):
        return __file__

    @property
    def parameters(self):
        return {**super().parameters, 'layout_parameters':list(LAYOUT_PARAMETERS), 'screen_source':SCREEN_SOURCE}

    def bolt_points(self):
        _,foot,leg,*_ = self.leg_datums()
        rim = original.previous.axes()[4]
        normal, rim_normal = cq.Vector(0.,leg.z,-leg.y), cq.Vector(0.,rim.z,-rim.y)
        rim_centre = self.b.point(0.,0.,self.DEPTH/2)
        y,z = np.linalg.solve([[normal.y,normal.z],[rim_normal.y,rim_normal.z]],
                             [foot.dot(normal),rim_centre.dot(rim_normal)])
        centre = cq.Vector(0.,float(y),float(z))
        return tuple(centre+p for p in original.layout_offsets(leg,rim,LAYOUT_PARAMETERS))


CANDIDATE = Candidate('upper225',225.,150.)


def __getattr__(name):
    return getattr(CANDIDATE,name)
