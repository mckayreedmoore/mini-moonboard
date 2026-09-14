"""First-stage actual bolt-force checks for the isolated low-rail trial.

Upper and low-rail connections use their own diameters, timber bearing lengths,
grain directions, actual boundary rays and hardware assumptions. No pivot
capacity is divided among bolts and no old frame acceptance transfers here.
"""
import math

from fea.compact_thick_checks import fully_threaded_sensitivity
from fea.current_response_resistance import VALIDITY
from fea.reinforced_fastener_checks import dot
from fea.thick_leg_checks import bolt_check, positive, vector

PSI_MPA=.006894757293168361


def hardware_assumptions(diameter_mm, *, washer_od_mm, hole_diameter_mm,
                         washer_thickness_mm):
    """Explicit provisional Grade 5 and independent round-washer references.

    Delivered thread/runout, washer dimensions and washer yield are not verified
    by these assumptions. The supplied washer geometry must match the CAD stack.
    """
    values={6.35:(.0318,.1887,.428),9.525:(.0775,.298,.551),12.7:(.1419,.4056,.736),19.05:(.334,.620,1.100)}
    diameter=next((d for d in values if math.isclose(diameter_mm,d,abs_tol=1e-8)),None)
    if diameter is None:
        raise ValueError('Supported provisional hardware is 1/4, 3/8, 1/2 or 3/4 inch')
    tensile,root,hex_min=values[diameter]
    washer={'outer_diameter_mm':positive(washer_od_mm),
        'hole_diameter_mm':positive(hole_diameter_mm),
        'seat_diameter_mm':.95*hex_min*25.4,
        'thickness_mm':positive(washer_thickness_mm),
        'wood_bearing_mpa':625*PSI_MPA,'yield_mpa':33000*PSI_MPA,
        'safety_factor':1.67}
    return {'tensile_area_mm2':tensile*25.4**2,
        'shear_area_mm2':math.pi*(root*25.4)**2/4,
        'steel_yield_mpa':92000*PSI_MPA,'steel_safety_factor':2.,
        'washers':[dict(washer),dict(washer)],
        'root_diameter_mm':root*25.4,'nominal_diameter_mm':diameter,
        **({'quarter_reference_basis':{
            'tensile_area_in2':.0318,'calculated_root_reference_in':.1887,
            'minimum_hex_across_flats_in':.428,
            'root_scope':'Calculated 1/4-20 UNC basic external root reference: 0.25 - 1.226869/20, rounded; not a delivered minor-diameter lower bound.',
            'seat_scope':'95% of the published minimum hex across-flats dimension is an assessment bearing-seat assumption.',
            'sources':{
                'tensile_area':'https://www.imageindustries.com/products/weld-stud/advanced-process-apa-inch-threaded-aluminum/part-number/APA25-75/mechanical-properties/FTA25/',
                'hex_dimensions_and_grade5':'https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf',
                'nut_dimensions':'https://boltdepot.com/Product-Details?product=2569'},
            'material_scope':'Thread area only is taken from the stud manufacturer; its aluminum properties are not used.'
            }} if diameter==6.35 else {}),
        **({'three_quarter_reference_basis':{
            'tensile_area_in2':.334,'calculated_root_reference_in':.620,
            'minimum_hex_across_flats_in':1.100,
            'root_scope':'Calculated 3/4-10 UNC reference, not a guaranteed delivered minor-diameter lower bound.',
            'seat_scope':'95% of the published minimum hex across-flats dimension is an assessment bearing-seat assumption.',
            'sources':{
                'tensile_area':'https://www.portlandbolt.com/technical/faqs/calculating-strength/',
                'calculated_thread_geometry':'https://www.imageindustries.com/products/weld-stud/reduced-base-rbc-inch-threaded-carbon-steel/part-number/RBC75-2/mechanical-properties/RBC75/',
                'hex_dimensions_and_grade5':'https://www.valuefastener.com/documents/products/capscrewgr5-8.pdf',
                'grade5':'https://www.portlandbolt.com/technical/specifications/sae-j429/'}
            }} if diameter==19.05 else {}),
        'scope':'Provisional Grade 5 and washer material assumptions; actual thread coverage, preload and local contact/prying remain unverified.'}


def _joint_resultants(rows):
    """Recover a diagnostic wrench for each joined member pair."""
    groups={}
    for name,row in rows.items():
        key=tuple(sorted((row['first'],row['second'])))
        groups.setdefault(key,[]).append((name,row))
    results={}
    for pair,items in groups.items():
        centre=[sum(row['point'][i] for _,row in items)/len(items) for i in range(3)]
        force=[0.,0.,0.]
        moment=[0.,0.,0.]
        for _,row in items:
            action=vector(row['force_on_first_xyz_n'] if row['first']==pair[0] else row['force_on_second_xyz_n'])
            offset=[a-b for a,b in zip(vector(row['point']),centre,strict=True)]
            cross=[offset[1]*action[2]-offset[2]*action[1],
                offset[2]*action[0]-offset[0]*action[2],offset[0]*action[1]-offset[1]*action[0]]
            for i in range(3):
                force[i]+=action[i]
                moment[i]+=cross[i]
        results[' / '.join(pair)]={'members':pair,'bolt_names':[n for n,_ in items],
            'centroid_xyz_mm':centre,'force_on_first_named_member_xyz_n':force,
            'moment_about_centroid_xyz_nmm':moment,
            'scope':'Actual same-case group wrench; capacity is checked per recovered bolt, never divided from this resultant.'}
    return results


def directed_end_distance_check(row, geometry):
    """Separate NDS Table 12.5.1A end-distance interpretation.

    For softwood, bearing toward the end uses 7D for Cdelta=1 and 3.5D
    absolute minimum. Bearing away or perpendicular uses 4D and 2D. Between
    those limits Cdelta=actual/full-reference end distance (NDS 12.5.1.2a).
    Applying the sign of the parallel force component to an oblique load is
    explicitly an assessment interpretation, not a new prescribed oblique rule.
    """
    diameter=positive(geometry['diameter_mm'])
    results={}
    for side in ('first','second'):
        name=row[side]
        member=geometry['members'][name]
        force=vector(row['force_on_'+side+'_xyz_n'])
        parallel=dot(force,vector(member['grain'],unit=True))
        ends={}
        for label,sign in (('grain_positive',1),('grain_negative',-1)):
            toward=sign*parallel>1e-8
            full=(7. if toward else 4.)*diameter
            minimum=full/2
            distance=positive(member['edge_distances_mm'][label])
            applicable=distance>=minimum-1e-8
            ends[label]={'parallel_force_toward_end_n':sign*parallel,
                'interpretation':'softwood tension toward end' if toward else 'compression away from end or perpendicular component',
                'actual_end_distance_mm':distance,'minimum_end_distance_mm':minimum,
                'full_reference_end_distance_mm':full,
                'minimum_margin_mm':distance-minimum,'full_reference_margin_mm':distance-full,
                'factor_before_applicability_check':min(1.,distance/full),
                'applicable':applicable,
                'end_distance_factor':min(1.,distance/full) if applicable else None}
        applicable=all(v['applicable'] for v in ends.values())
        results[name]={'parallel_force_on_member_n':parallel,'ends':ends,
            'applicable':applicable,
            'end_distance_factor':min(v['end_distance_factor'] for v in ends.values()) if applicable else None}
    applicable=all(v['applicable'] for v in results.values())
    return {'members':results,'applicable':applicable,
        'end_distance_factor':min(v['end_distance_factor'] for v in results.values()) if applicable else None,
        'basis':'NDS 12.5.1.2(a), Table12.5.1A; explicit force-component interpretation for oblique action.',
        'limits':'End-distance factor only. Other spacing/geometry factors, material assumptions and conservative oblique edge interpretation remain separate.'}


def end_distance_branch(rows, geometries, bolts):
    """Apply the smallest applicable end factor to all bolts in each joint.

    NDS 12.5.1.2 requires the smallest geometry factor in a group to apply to
    every fastener. No capacity is reported where any end is below its absolute
    minimum. Original strict 7D-both-ends checks remain untouched.
    """
    individual={n:directed_end_distance_check(row,geometries[n]) for n,row in rows.items()}
    groups={}
    for name,row in rows.items():
        pair=tuple(sorted((row['first'],row['second'])))
        groups.setdefault(pair,[]).append(name)
    checks={}
    for pair,names in groups.items():
        applicable=all(individual[n]['applicable'] for n in names)
        factor=min(individual[n]['end_distance_factor'] for n in names) if applicable else None
        checks[' / '.join(pair)]={'bolt_names':names,'applicable':applicable,
            'group_minimum_end_distance_factor':factor,
            'nominal_lateral_ratios':{n:bolts[n]['lateral_ratio']/factor if applicable else None for n in names},
            'full_root_lateral_ratios':{n:bolts[n]['fully_threaded_sensitivity']['lateral_ratio']/factor if applicable else None for n in names}}
    applicable=all(g['applicable'] for g in checks.values())
    ratios=[v for g in checks.values() for v in g['nominal_lateral_ratios'].values() if v is not None]
    peak=max(ratios) if ratios else None
    edge_margin=min(p['margins_mm'][edge] for b in bolts.values() for p in b['placement'].values() for edge in ('depth_positive','depth_negative'))
    failed=not applicable or edge_margin<0 or peak is None or peak>1
    return {'individual_end_checks':individual,'joint_groups':checks,
        'all_end_distances_above_absolute_minimum':applicable,
        'peak_nominal_lateral_ratio_after_end_factor':peak,
        'minimum_conservative_depth_edge_margin_mm':edge_margin,
        'status':'END_FACTOR_BRANCH_EXCEEDED_OR_INAPPLICABLE' if failed else 'END_FACTOR_BRANCH_MET_WITH_OTHER_LIMITS',
        'limits':['Original strict 7D-both-ends result is retained separately; this branch does not erase it.',
            'Factors apply to every bolt sharing a joined member pair, using the worst end-distance ratio in that group.',
            'No result below the tabulated absolute minimum receives a capacity factor or a pass.',
            'This branch checks end-adjusted lateral strength and the retained force-directed 4D/1.5D depth-edge screen; hardware, other group spacing and local wood checks remain separate.'],
        'qualified_for_design':False}


def assess(report, geometries_by_bolt_name, hardware_by_bolt_name, *, bolt_prefixes):
    """Check every upper and rail bolt after all native numerical gates pass.

    Explicit prefixes make omitted native bolt forces an error. Geometry uses
    the established per-bolt schema: diameter_mm, bending_yield_psi and members
    keyed by name, including actual bearing_length_mm and directional edge rays.
    No CAD generation or native solve occurs here.
    """
    validity={key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'candidate':report.get('candidate'),'producer_validity':validity,
            'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY','qualified_for_design':False}
    if not bolt_prefixes or any(not prefix for prefix in bolt_prefixes):
        raise ValueError('Require explicit nonempty upper and rail bolt prefixes')
    rows={name:row for name,row in report['physical_connection_forces'].items()
        if name.startswith(tuple(bolt_prefixes))}
    if not rows or set(rows)!=set(geometries_by_bolt_name) or set(rows)!=set(hardware_by_bolt_name):
        raise ValueError('Every selected native bolt needs exact matching geometry and hardware')
    bolts={}
    for name,row in rows.items():
        geometry=geometries_by_bolt_name[name]
        hardware=hardware_by_bolt_name[name]
        if not math.isclose(geometry['diameter_mm'],hardware['nominal_diameter_mm'],abs_tol=1e-8):
            raise ValueError('Hardware and geometry diameter mismatch: '+name)
        native_members=report.get('member_section_demands',{})
        for member_name,member in geometry['members'].items():
            if member_name not in (row['first'],row['second']):
                raise ValueError('Geometry includes an unrelated member')
            if member_name in native_members:
                native=native_members[member_name]['member']
                if abs(dot(vector(member['grain'],unit=True),vector(native['axis'],unit=True)))<1-1e-8:
                    raise ValueError('Native and supplied grain directions differ')
        check=bolt_check(row,geometry,hardware)
        check['fully_threaded_sensitivity']=fully_threaded_sensitivity(check,geometry,hardware['root_diameter_mm'])
        check['nominal_diameter_condition']='Delivered thread/runout must establish the NDS 12.3.7.2 nominal-diameter condition for each actual bearing length; no more than one quarter threaded bearing in either member.'
        check['limits'][0]='Individual native force in this actual assembled joint; local group/splitting resistance and row applicability require separate evidence.'
        check['limits'][-1]='This first-stage check does not qualify local wood/net sections, joint fit, low-rail member forces or prying.'
        bolts[name]=check
    metrics={'nominal_lateral':max(b['lateral_ratio'] for b in bolts.values()),
        'full_root_lateral_sensitivity':max(b['fully_threaded_sensitivity']['lateral_ratio'] for b in bolts.values()),
        'minimum_directional_edge_end_margin_mm':min(p['minimum_margin_mm'] for b in bolts.values() for p in b['placement'].values()),
        'steel_direct':max(b['hardware']['steel_direct_ratio'] for b in bolts.values()),
        'washer_bearing':max(w['wood_bearing_ratio'] for b in bolts.values() for w in b['hardware']['washers']),
        'washer_bending':max(w['elastic_bending_ratio'] for b in bolts.values() for w in b['hardware']['washers'])}
    failed=metrics['nominal_lateral']>1 or metrics['minimum_directional_edge_end_margin_mm']<0 or any(metrics[k]>1 for k in ('steel_direct','washer_bearing','washer_bending'))
    return {'candidate':report['candidate'],'producer_validity':validity,
        'status':'CONDITIONAL_FIRST_STAGE_EXCEEDED' if failed else 'LISTED_FIRST_STAGE_SCREENS_MET_WITH_OPEN_LIMITS',
        'metrics':metrics,'bolts':bolts,'joint_resultants':_joint_resultants(rows),
        'force_directed_end_branch':end_distance_branch(rows,geometries_by_bolt_name,bolts),
        'qualified_for_design':False,
        'limits':['No group reference capacity is divided among bolts; actual individual recovered forces govern.',
            'Force-directed 4D edge screening is conservative for oblique forces, not a universal oblique minimum.',
            'Nominal and full-root lateral branches are separate; neither verifies delivered hardware.',
            'Connection splitting/net sections, low-rail/header/post member resistance, end trims and all contact assumptions need matching checks before selecting this trial.']}
