"""Selected insert assembly envelopes; unknown thread engagement stays explicit.

Dottie FMDD14114's technical sheet specifies an 80–82 degree head. The CAD
uses the largest head and 80 degree limit as a clearance envelope, not a shop
countersink specification. E-Z LOK specifies below-surface seating but no depth.
"""
import math
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

from . import insert_frame as reference

REFERENCE_PATH = Path(__file__).resolve().parents[1]/'docs/panel-insert-reference.json'
INSERT, SCREW, PANEL = reference.INSERT, reference.SCREW, reference.PANEL
INSERT_RECESS_MM = .25
PANEL_CLEARANCE_MM = 7.
RESERVE_DEPTH_MM = 17.
LIMITS = ('E-Z LOK 801420-13 zinc insert and Dottie FMDD14114 machine screw; '
          'nominal insert and maximum head clearance envelopes; provisional 0.25 mm '
          'recess, 7 mm panel clearance and 17 mm receiver reserve; unknown thread '
          'runouts/drive recess, clamp force, head bearing and wood resistance; NOT build-ready')


def recess_sensitivity(recess_mm=INSERT_RECESS_MM):
    """Gross reach and ideal drill-point arithmetic, never effective engagement."""
    if not math.isfinite(recess_mm) or recess_mm < 0:
        raise ValueError('Insert recess must be finite and nonnegative')
    tip = INSERT['pilot_diameter_inch_recommendation']/(2*math.tan(math.radians(59)))
    maximum_length = INSERT['nominal_length']+INSERT['drawing_general_tolerance_plus_minus']
    return {'insert_recess_mm': recess_mm,
            'minimum_gross_reach_from_insert_front_mm': SCREW['minimum_overall_length']-PANEL-recess_mm,
            'nominal_gross_reach_from_insert_front_mm': SCREW['nominal_overall_length']-PANEL-recess_mm,
            'maximum_insert_back_from_receiver_face_mm': recess_mm+maximum_length,
            'ideal_118_degree_drill_point_mm': tip,
            'remaining_reserve_after_insert_and_point_mm': RESERVE_DEPTH_MM-recess_mm-maximum_length-tip,
            'effective_thread_engagement_mm': None, 'qualified_for_machining': False}


@dataclass(frozen=True)
class PanelMachineScrew(reference.PanelMachineScrew):
    product_status: str = LIMITS

    @property
    def insert_start(self):
        return self.start+self.direction*(PANEL+INSERT_RECESS_MM)

    def maximum_insert_envelope(self):
        tolerance = INSERT['drawing_general_tolerance_plus_minus']
        return cq.Solid.makeCylinder((INSERT['nominal_outer_diameter']+tolerance)/2,
            INSERT['nominal_length']+tolerance, self.insert_start, self.direction)

    def receiver_cut(self):
        """Occupied-body clearance plus blind reserve, not the installation pilot."""
        tolerance = INSERT['drawing_general_tolerance_plus_minus']
        entry = self.start+self.direction*PANEL
        envelope = cq.Solid.makeCylinder((INSERT['nominal_outer_diameter']+tolerance)/2,
            INSERT_RECESS_MM+INSERT['nominal_length']+tolerance, entry, self.direction)
        reserve = cq.Solid.makeCylinder(INSERT['pilot_diameter_inch_recommendation']/2,
                                       RESERVE_DEPTH_MM, entry, self.direction)
        return envelope.fuse(reserve).clean()

    def panel_cut(self):
        bore = cq.Solid.makeCylinder(PANEL_CLEARANCE_MM/2, PANEL+2,
                                     self.start-self.direction, self.direction)
        return bore.fuse(self.components()[1]).clean()
