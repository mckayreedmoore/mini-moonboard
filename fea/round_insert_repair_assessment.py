"""Nominal insert fit and repair rejection arithmetic; never repair authorization."""
import argparse
import hashlib
import json
import math
from pathlib import Path

REFERENCE = Path('docs/panel-insert-reference.json')


def damage_screen(diameter_mm, eccentricity_mm, uncertainty_mm, *, split=False, verified=False):
    """Necessary radial cleanup only, over the entire proposed insert depth."""
    values = (diameter_mm, eccentricity_mm, uncertainty_mm)
    if any(not math.isfinite(v) or v < 0 for v in values):
        raise ValueError('Damage dimensions must be finite and nonnegative')
    pilot = json.loads(REFERENCE.read_text())['insert']['pilot_diameter_inch_recommendation']
    margin = pilot/2-diameter_mm/2-eccentricity_mm-uncertainty_mm
    return {'radial_cleanup_margin_mm': margin,
            'necessary_cleanup_condition_passed': verified and not split and margin > 0.,
            'qualified_repair': False,
            'limits': 'A measured enclosing damage envelope is required through the insert depth; '
                      'positive cleanup margin does not establish sound wood or repair capacity.'}


def dimensional_screen():
    ref = json.loads(REFERENCE.read_text())
    insert, screw, assumptions = ref['insert'], ref['screw'], ref['project_geometry_assumptions']
    pilot = insert['pilot_diameter_inch_recommendation']
    maximum_length = insert['nominal_length']+insert['drawing_general_tolerance_plus_minus']
    tip = pilot/(2*math.tan(math.radians(118./2)))
    reserve = assumptions['pilot_tip_clearance_depth']
    thickness = assumptions['face_and_kicker_thickness']
    return {'pilot_diameter_mm': pilot, 'assumed_drill_point_angle_deg': 118.,
            'idealized_drill_tip_length_mm': tip,
            'maximum_insert_length_mm': maximum_length,
            'minimum_total_depth_at_zero_recess_mm': maximum_length+tip,
            'remaining_depth_for_recess_and_extra_clearance_mm': reserve-maximum_length-tip,
            'reserved_depth_mm': reserve,
            'minimum_gross_receiver_reach_before_recess_mm': screw['minimum_overall_length']-thickness,
            'nominal_gross_receiver_reach_before_recess_mm': screw['nominal_overall_length']-thickness,
            'centered_38_1mm_face_side_ligament_mm': (38.1-insert['nominal_outer_diameter']
                -insert['drawing_general_tolerance_plus_minus'])/2,
            'effective_thread_engagement_mm': None, 'qualified_for_drilling': False,
            'limits': 'Idealized 118-degree twist drill only; no selected recess, extra bottom '
                      'clearance, drill geometry, usable thread interval or actual damage measurement. '
                      'Centered face ligament is illustrative, not an actual-location edge rating.'}


def build():
    # Parent serializes this actual CAD assessment; pure math above imports no CAD.
    from fea.horizontal_insert_fit import build as fit

    paths = [Path(__file__), REFERENCE, Path('docs/round-service-wiring-reference.json'),
             Path('docs/round-panel-countersink-reference.json')]
    def hashes():
        return {str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths}
    before = hashes()
    report = fit('mini_moonboard.round_service_frame')
    dimensions = dimensional_screen()
    if before != hashes():
        raise ValueError('Repair assessment sources changed during evaluation')
    report['source_sha256'].update(before)
    report.update(dimensional_screen=dimensions, physical_tests_performed=False,
                  damaged_wood_assessed=False, authorized_for_climbing=False)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    from fea.screw_insert_repair_reserve import write

    write(build(), args.output)
