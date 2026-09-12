"""Transparent planar axial-leg comparison; no panel or floor-friction assessment."""
import hashlib
import json
import math
import tarfile
from pathlib import Path

from fea.leg_member_capacity import compression_limit, leg_check
from fea.round_structural_global_envelope import locations

BUNDLE = Path('fea/results/reinforced-F10-k1000-v4.tar.gz')
MASS = Path('docs/round-reinforcement-review/review.json')


def axial_support_force(*, downward_n, horizontal_n, load_y, load_z,
                        dead_n, dead_y, front_y, rear_y, vertical_cosine):
    """Sagittal moment balance, two-force rear legs, front resultant at floor Z=0."""
    return (downward_n*(load_y-front_y)+horizontal_n*load_z+dead_n*(dead_y-front_y))/(
        (rear_y-front_y)*vertical_cosine)


def build(*, equipment_mass_kg=25.):
    from mini_moonboard import round_reinforcement_frame as model

    if not math.isfinite(equipment_mass_kg) or equipment_mass_kg < 0:
        raise ValueError('Equipment allowance must be finite and nonnegative')
    mass_record = json.loads(MASS.read_text())
    for path, expected in mass_record['source_sha256'].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError('Current geometry differs from mass evidence: '+path)
    with tarfile.open(BUNDLE, 'r:gz') as archive:
        native = json.load(archive.extractfile('report.json'))
    contacts = [r['point_xyz_mm'] for r in native['floor_contact_demands']
                if r['name'].startswith('floor_lumber_leg_left_')]
    foot = [sum(p[i] for p in contacts)/len(contacts) for i in range(3)]
    bolts = [r['point'] for name, r in native['physical_connection_forces'].items()
             if name.startswith('lumber_leg_bolt_left_')]
    top = [sum(p[i] for p in bolts)/len(bolts) for i in range(3)]
    span = math.hypot(top[1]-foot[1], top[2]-foot[2])
    cosine = (top[2]-foot[2])/span
    state = mass_record['state']
    cases = []
    points = list(locations(model))
    equipment_y = max(p[1]+offset*n[1] for _, p, n in points for offset in (0., 100.))
    combined_mass = state['mass_kg']+equipment_mass_kg
    combined_y = (state['mass_kg']*state['centre_xyz_mm'][1]
                  +equipment_mass_kg*equipment_y)/combined_mass
    for pounds in (150, 200, 250, 300):
        for factor in (1, 2):
            candidates = []
            for name, p, n in points:
                for front in (-270.95, -36.):
                    for offset in (0., 100.):
                        for horizontal in (0., 300.):
                            force = axial_support_force(downward_n=pounds*4.4482216152605*factor,
                                horizontal_n=horizontal, load_y=p[1]+offset*n[1],
                                load_z=p[2]+offset*n[2], dead_n=combined_mass*9.80665,
                                dead_y=combined_y, front_y=front,
                                rear_y=foot[1], vertical_cosine=cosine)
                            candidates.append((force, name, front, offset, horizontal))
            peak = max(candidates)
            cases.append({'climber_lb':pounds,'vertical_multiplier':factor,
                'entire_rear_compression_assigned_to_one_leg_n':peak[0],
                'governing_hold':peak[1], 'front_support_y_mm':peak[2],
                'standoff_mm':peak[3], 'horizontal_force_n':peak[4],
                'full_stock_length_check':leg_check(peak[0]),
                'actual_support_span_check':leg_check(peak[0],effective_length_mm=span)})
    source_paths = (Path(__file__).resolve(), Path('fea/leg_member_capacity.py'),
                    Path('fea/reinforced_timber_resistance.py'),
                    Path('fea/round_structural_global_envelope.py'), MASS, BUNDLE)
    return {'candidate':model.KEY,'source_sha256':{
        str(p.resolve().relative_to(Path.cwd())):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in source_paths}, 'support_span_mm':span,'vertical_cosine':cosine,
        'member_criterion_compression_full_stock_n':compression_limit()['compression_n'],
        'member_criterion_compression_support_span_n':compression_limit(effective_length_mm=span)['compression_n'],
        'equipment_allowance': {'mass_kg':equipment_mass_kg, 'y_mm':equipment_y,
            'basis':'Assumed maximum equipment mass, placed at rear-most hold projection; not measured kit mass'},
        'combined_dead_mass_kg':combined_mass,
        'cases':cases,'climber_rating_established':False,
        'limits':[
            'Panel construction accepted as owner-specified design basis; no comparison frame.',
            'Feet assumed prevented from sliding. No friction measurement, coefficient or qualification gate.',
            'Planar two-force rear-leg idealization; no extra imposed top-joint couples or transverse point loads.',
            'All rear axial compression assigned to one leg; no equal left/right sharing credit.',
            'Modeled assembly plus explicit equipment allowance; installed equipment must remain within assumed mass and rearward extent.',
            'Self-weight bending plus full half-width eccentricity and worst one-bore net section retained.',
            'Conditional member criterion only; four-bolt joint capacity and additional frame-imposed moments remain separate.',
            'Reference crossings are allowable-design comparisons, not physical breaking loads.']}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build()
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps([{k:c[k] for k in ('climber_lb','vertical_multiplier',
        'entire_rear_compression_assigned_to_one_leg_n')} for c in report['cases']]))
