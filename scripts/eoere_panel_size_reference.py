"""Apply the missing APA size adjustment to saved current panel references.

This additive correction preserves the frozen component report and all actions.
It adjusts bending references only; it supplies no complete panel resistance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1'
COMPONENTS = PACKET / 'components.json'
COMPONENT_SHA = '20de966cb0c684c6d9ebed1cd380999386fa61b12106f9d7b5640e539439efaf'
APA = ROOT / 'docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/panel-local-net-completion/source-cache/apa-D510C-2012.pdf'
APA_SHA = '6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca'


def size_factor(width_mm: float) -> float:
    """APA D510C/D510F 4.5.5; dimension perpendicular to bending stress."""
    if not math.isfinite(width_mm) or width_mm <= 0:
        raise ValueError('Require a positive finite panel width')
    inches = width_mm / 25.4
    if width_mm >= 24*25.4:
        return 1.
    return .25 + .0313 * inches if width_mm >= 8*25.4 else .5


def adjusted_reference(peak: float, base_reference: float, width_bounds_mm) -> dict:
    """Bound the reference over the recorded front/full panel dimensions."""
    low, high = width_bounds_mm
    if not all(math.isfinite(v) for v in (peak, base_reference, low, high)):
        raise ValueError('Require finite reference inputs')
    if peak < 0 or base_reference <= 0 or not 0 < low <= high:
        raise ValueError('Invalid panel reference or width interval')
    # Include both rule junctions; the published rounded coefficient produces
    # small jumps there. Current widths are remote from both junctions.
    widths = [low, high]
    for junction in (8*25.4, 24*25.4):
        if low <= junction <= high:
            widths.append(junction)
            if low < junction:
                widths.append(math.nextafter(junction, -math.inf))
    factors = [size_factor(v) for v in widths]
    factors = [min(factors), max(factors)]
    references = [base_reference * v for v in factors]
    ratios = [peak / references[1], peak / references[0]]
    return {'width_bounds_mm': [low, high], 'Cs_bounds': factors,
            'base_reference_per_mm_width_CD1': base_reference,
            'adjusted_reference_bounds_per_mm_width_CD1': references,
            'peak_abs_resultant': peak, 'base_ratio_CD1': peak / base_reference,
            'adjusted_ratio_bounds_CD1': ratios,
            'definite_adjusted_reference_exceedance': ratios[0] > 1,
            'possible_adjusted_reference_exceedance': ratios[1] > 1}


def produce() -> dict:
    pins = {}

    def read(path, expected):
        raw = Path(path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError(f'Frozen reference changed: {path}')
        pins[str(Path(path).relative_to(ROOT))] = expected
        return raw

    source = Path(__file__).read_bytes()
    report = json.loads(read(COMPONENTS, COMPONENT_SHA))
    read(APA, APA_SHA)
    affected, newly_exceeded = [], []
    base_count = lower_count = upper_count = total = 0
    for case in report['cases']:
        field = json.loads(read(ROOT / case['field']['path'], case['field']['sha256']))
        if (field['case_id'], field['state_id']) != (case['case_id'], case['state_id']):
            raise ValueError('Exact own case/state required')
        if len(field['source_inputs']['shafts']) != 100 or len(field['source_inputs']['hillman_rows']) != 66:
            raise ValueError('Current 100-bolt/66-screw geometry required')
        for panel in case['coarse']['panels']['per_panel']:
            geometry = field['panel_generalized_coefficients'][panel['panel']]
            for name, row in panel['section_components'].items():
                total += 1
                peak, reference = row['peak_abs_resultant'], row['reference_per_mm_width_CD1']
                original = row['sampled_ratio_CD1']
                if not math.isclose(peak / reference, original, rel_tol=1e-12, abs_tol=1e-12):
                    raise ValueError('Original scalar does not reproduce')
                if name == 'bending_x':
                    widths = sorted([geometry['height_mm'], geometry['geometry']['front_height']])
                elif name == 'bending_y':
                    widths = [geometry['width_mm']] * 2
                else:
                    if name not in ('rolling_x', 'rolling_y'):
                        raise ValueError('Unknown panel comparison')
                    # APA 4.5.5 does not adjust rolling-shear reference values.
                    base_count += original > 1
                    lower_count += original > 1
                    upper_count += original > 1
                    continue
                corrected = adjusted_reference(peak, reference, widths)
                base_count += original > 1
                lower_count += corrected['definite_adjusted_reference_exceedance']
                upper_count += corrected['possible_adjusted_reference_exceedance']
                if corrected['Cs_bounds'] != [1., 1.]:
                    item = {'case_id': case['case_id'], 'state_id': case['state_id'],
                            'panel': panel['panel'], 'component': name, 'xy_mm': row['xy_mm'], **corrected}
                    affected.append(item)
                    if original <= 1 and corrected['definite_adjusted_reference_exceedance']:
                        newly_exceeded.append(item)
    if total != 144 or len(affected) != 12:
        raise ValueError('Expected all 144 panel comparisons and 12 affected kicker rows')
    for name, expected in pins.items():
        read(ROOT / name, expected)
    own_sha = hashlib.sha256(source).hexdigest()
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != own_sha:
        raise ValueError('Correction producer changed during calculation')
    return {'schema': 'eoere_current_panel_size_reference_correction/v1',
            'geometry_revision': report['geometry_revision'], 'hardware_revision': report['hardware_revision'],
            'extra_grid': False, 'components': {'path': str(COMPONENTS.relative_to(ROOT)), 'sha256': COMPONENT_SHA},
            'producer': {'path': str(Path(__file__).resolve().relative_to(ROOT)), 'sha256': own_sha},
            'source_sha256': pins, 'all_sources_unchanged': True,
            'rule': 'APA D510C (2012), 4.5.5, printed p25; D510F (2020), 4.5.5, printed p24. Cs adjusts bending/tension by the dimension perpendicular to stress.',
            'current_edition_crosscheck': 'https://wood.tcaup.umich.edu/lectures/2021/D510.pdf#page=28',
            'sampled_panel_comparisons': total, 'affected_bending_rows': affected,
            'original_base_reference_exceedance_count': base_count,
            'size_adjusted_definite_exceedance_count': lower_count,
            'size_adjusted_possible_exceedance_count': upper_count,
            'newly_exceeded_rows': newly_exceeded,
            'field_or_operator_changed': False, 'frozen_report_rewritten': False,
            'structural_acceptance': False, 'complete_panel_resistance': None,
            'limits': ['Existing fixed-action sampled plate reference only; no response solve, actual panel inspection or physical failure is established.',
                       'Recorded front/full dimensions bound the kicker size-reference scenarios. Hole/bevel/contact effects and complete local panel behavior remain unqualified.',
                       'The correction changes no stiffness, forces, Hillman policy, axes or physical operation. Other panel/screw remedies remain deferred.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = produce()
    with args.out.open('x') as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: report[k] for k in ('sampled_panel_comparisons',
          'original_base_reference_exceedance_count', 'size_adjusted_definite_exceedance_count')}))


if __name__ == '__main__':
    main()
