"""Read-only load-angle and duration sensitivities for accepted compact trials.

Original fixed-Ktheta comparisons remain separate. Directional Ktheta follows
NDS Table 12.3.1B; the 1.6 duration branch is hypothetical, not adopted design
resistance. Neither branch changes solved loads or qualifies the joint.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from fea.current_response_resistance import VALIDITY
from fea.dowel_yield import single_shear
from fea.thick_leg_checks import positive, vector

LBF_N=4.4482216152605
SOURCE='https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf'


def dot(a,b):
    return sum(x*y for x,y in zip(a,b,strict=True))


def compare_bolt(row, geometry, original_ratio=None):
    """Recompute all six yield modes for fixed and actual directional Ktheta."""
    axis=vector(row['axis'],unit=True)
    force=vector(row['force_on_first_xyz_n'])
    reaction=vector(row['force_on_second_xyz_n'])
    if math.sqrt(sum((a+b)**2 for a,b in zip(force,reaction,strict=True)))>1e-6:
        raise ValueError('Require bolt action/reaction balance')
    axial=dot(force,axis)
    lateral=[f-axial*a for f,a in zip(force,axis,strict=True)]
    demand=math.sqrt(dot(lateral,lateral))
    diameter=positive(geometry['diameter_mm'])/25.4
    if not .25<=diameter<=1.:
        raise ValueError('This comparison uses the NDS 1/4 through 1 inch reduction table')
    angles,bearings,lengths={},[],[]
    for key in ('first','second'):
        name=row[key]
        member=geometry['members'][name]
        grain=vector(member['grain'],unit=True)
        if abs(dot(axis,grain))>1e-8:
            raise ValueError('Require installation axis perpendicular to timber grain')
        cosine=min(1.,abs(dot(lateral,grain))/demand) if demand else 0.
        angles[name]=math.degrees(math.acos(cosine))
        parallel=positive(member['parallel_bearing_psi'])
        perpendicular=6100*positive(member['specific_gravity'])**1.45/math.sqrt(diameter)
        bearings.append(parallel*perpendicular/(parallel*(1-cosine*cosine)+perpendicular*cosine*cosine))
        lengths.append(positive(member['bearing_length_mm'])/25.4)
    ktheta=1+.25*max(angles.values())/90
    fy=positive(geometry['bending_yield_psi'])
    modes={}
    for label,k in (('original_fixed_1_25',1.25),('actual_angle',ktheta)):
        rd={mode:factor*k for mode,factor in {'Im':4.,'Is':4.,'II':3.6,'IIIm':3.2,'IIIs':3.2,'IV':3.2}.items()}
        result=single_shear(main_length_in=lengths[0],side_length_in=lengths[1],
            main_bearing_lb_in=bearings[0]*diameter,side_bearing_lb_in=bearings[1]*diameter,
            main_yield_moment_lb_in=fy*diameter**3/6,side_yield_moment_lb_in=fy*diameter**3/6,
            gap_in=0.,reduction_terms=rd)
        reference=result['reference_lateral_lbf']*LBF_N
        modes[label]={'Ktheta':k,'reduction_terms':rd,'all_modes':result,
            'reference_lateral_n_CD_1':reference,'ratio_CD_1':demand/reference,
            'hypothetical_reference_lateral_n_CD_1_6':reference*1.6,
            'hypothetical_ratio_CD_1_6':demand/(reference*1.6)}
    if original_ratio is not None and (not math.isfinite(original_ratio) or not math.isclose(original_ratio,modes['original_fixed_1_25']['ratio_CD_1'],rel_tol=1e-8,abs_tol=1e-9)):
        raise ValueError('Supplied historical ratio does not match this force and geometry')
    return {'angles_to_grain_deg':angles,'maximum_angle_deg':max(angles.values()),
        'lateral_demand_n':demand,'signed_axial_increment_n':axial,
        'original_reported_ratio':original_ratio,'comparisons':modes,
        'duration_factor_adopted':1.,'hypothetical_duration_factor':1.6,
        'hypothetical_duration_applicability_established':False,
        'qualified_for_design':False}


def assess(report, geometry, original_checks=None, *, expected_candidate=None):
    """Compare matching archived two-/three-bolt candidates after numerical gates."""
    allowed=(expected_candidate,) if expected_candidate is not None else ('compact-two-development','compact-thick-development')
    if report.get('candidate') not in allowed or geometry.get('candidate')!=report['candidate']:
        raise ValueError('Require matching explicitly supported candidate report and geometry')
    validity={key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'candidate':report['candidate'],'producer_validity':validity,
            'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY','qualified_for_design':False}
    identity={}
    for path,digest in geometry.get('source_sha256',{}).items():
        if path.startswith('mini_moonboard/'):
            if report.get('source_sha256',{}).get(path)!=digest:
                raise ValueError('Native/geometry direct model source mismatch: '+path)
            identity[path]=digest
    rows={name:row for name,row in report['physical_connection_forces'].items() if name.startswith('lumber_leg_bolt_')}
    geometries=geometry['geometries_by_bolt_name']
    if not rows or set(rows)!=set(geometries):
        raise ValueError('Require exact native/geometry bolt inventory')
    original={} if original_checks is None else original_checks['bolts']
    if original_checks is not None and set(original)!=set(rows):
        raise ValueError('Original comparisons must cover the same bolts')
    bolts={name:compare_bolt(row,geometries[name],None if original_checks is None else original[name]['lateral_ratio']) for name,row in rows.items()}
    governing={}
    for mode in ('original_fixed_1_25','actual_angle'):
        for duration,label in ((1.,'CD_1'),(1.6,'hypothetical_CD_1_6')):
            key='ratio_CD_1' if duration==1. else 'hypothetical_ratio_CD_1_6'
            name=max(bolts,key=lambda n:bolts[n]['comparisons'][mode][key])
            governing[mode+'_'+label]={'bolt':name,'ratio':bolts[name]['comparisons'][mode][key]}
    return {'candidate':report['candidate'],'producer_validity':validity,
        'status':'ASSUMPTION_SENSITIVITY_ONLY','bolts':bolts,'governing':governing,
        'matched_direct_model_source_sha256':identity,
        'reference_source':SOURCE,'duration_factor_adopted':1.,
        'limits':['Ktheta uses the greatest acute angle of this recovered bolt force to either joined timber grain, per NDS Table12.3.1B.',
            'Bearing strength, thickness, nominal diameter and all six yield modes are recomputed. Existing ratios remain preserved and checked separately.',
            'Cd1.6 is arithmetic sensitivity only; the project retains Cd1. Doubling applied downward load does not establish duration-factor eligibility.',
            'No source load, native solution, thread condition, spacing, local wood resistance or construction selection is changed.'],
        'qualified_for_design':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--geometry',type=Path,required=True)
    parser.add_argument('--checks',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-candidate')
    args=parser.parse_args()
    raw=args.report.read_bytes()
    report=json.loads(gzip.decompress(raw) if args.report.suffix=='.gz' else raw)
    geometry=json.loads(args.geometry.read_text())
    original=json.loads(args.checks.read_text()) if args.checks else None
    result=assess(report,geometry,original,expected_candidate=args.expected_candidate)
    paths=[args.report,args.geometry,Path(__file__)]
    if args.checks:
        paths.append(args.checks)
    result['source_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(result.get('governing',result['status']))


if __name__=='__main__':
    main()
