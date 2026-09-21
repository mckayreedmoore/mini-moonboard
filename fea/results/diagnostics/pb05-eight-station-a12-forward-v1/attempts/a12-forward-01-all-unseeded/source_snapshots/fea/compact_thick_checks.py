"""Conditional compact 4x6 moment-group checks using individual native forces.

Historical pivot evidence is not transferred to a multiple-bolt rotationally
restrained joint. Every comparison requires current assembled response forces.
"""
import itertools
import math

from fea.current_response_resistance import VALIDITY
from fea.dowel_yield import single_shear
from fea.reinforced_fastener_checks import dot, norm
from fea.thick_leg_checks import (
    bolt_check,
    bounded_section_check,
    bounded_section_properties,
    positive,
    vector,
)


def hardware_assumptions():
    """Explicit provisional 1/2-inch Grade 5 / round-washer inputs.

    Catalog availability does not verify delivered thread length, runout or
    washer yield. Nominal 8-inch bolt seating is distinct from those conditions.
    """
    psi=.006894757293168361
    washer={'outer_diameter_mm':34.925,'hole_diameter_mm':14.2875,
        'seat_diameter_mm':.95*.736*25.4,'thickness_mm':3.175,
        'wood_bearing_mpa':625*psi,'yield_mpa':33000*psi,'safety_factor':1.67}
    return {'tensile_area_mm2':.1419*25.4**2,
        'shear_area_mm2':math.pi*(.4056*25.4)**2/4,
        'steel_yield_mpa':92000*psi,'steel_safety_factor':2.,
        'washers':[dict(washer),dict(washer)],
        'scope':'Provisional Grade 5 and independent washer assumptions; no catalog-qualified smooth shank, preload or prying bound.'}


def fully_threaded_sensitivity(nominal, geometry, root_diameter_mm=.4056*25.4):
    """Entire bearing length at minimum thread root; original edge rules remain.

    Nominal-diameter perpendicular wood bearing is retained conservatively while
    root diameter reduces bearing width and bolt yield moment in every mode.
    This is a sensitivity, not an assertion that the entire bolt is threaded.
    """
    root=positive(root_diameter_mm)/25.4
    if root_diameter_mm>geometry['diameter_mm']:
        raise ValueError('Thread root must not exceed nominal bolt diameter')
    lengths=[v/25.4 for v in nominal['bearing_lengths_mm']]
    fe=nominal['bearing_psi'];fy=geometry['bending_yield_psi']
    reference=single_shear(main_length_in=lengths[0],side_length_in=lengths[1],
        main_bearing_lb_in=fe[0]*root,side_bearing_lb_in=fe[1]*root,
        main_yield_moment_lb_in=fy*root**3/6,side_yield_moment_lb_in=fy*root**3/6,
        gap_in=0.,reduction_terms={'Im':5.,'Is':5.,'II':4.5,'IIIm':4.,'IIIs':4.,'IV':4.})
    capacity=reference['reference_lateral_lbf']*4.4482216152605
    return {'root_diameter_mm':root_diameter_mm,'reference_lateral_n':capacity,
        'lateral_ratio':nominal['lateral_demand_n']/capacity,'dowel_reference':reference,
        'scope':'Full-root bearing sensitivity; nominal geometry remains unchanged.'}


def conservative_group_factor(count, diameter_mm, pitch_mm, area_mm2, modulus_mpa=11031.611669069377):
    """Equal-member EA, total-fastener row bound; separate conservative sensitivity.

    NDS group action compares uniform reference capacity with unequal row sharing.
    Native individual spring forces already resolve some unequal distribution;
    this extra reduction is retained as an explicitly conservative sensitivity.
    """
    if not isinstance(count,int) or not 2 <= count <= 4:
        raise ValueError('Require two to four fasteners')
    diameter = positive(diameter_mm)/25.4
    pitch = positive(pitch_mm)/25.4
    ea = positive(area_mm2)/25.4**2*positive(modulus_mpa)/.006894757293168361
    u = 1+180000*diameter**1.5*pitch/ea
    m = 1/(u+math.sqrt(u*u-1))
    n = count
    return m*(1-m**(2*n))/(n*((1+m**n)*(1+m)-1+m**(2*n)))*2/(1-m)


def layout_check(points, member, diameter_mm):
    """Component-axis spacing and shrinkage screens; no invented grain-row rule.

    NDS 12.1.2.4 defines a row along load. Perpendicular-load between-row
    separation runs along grain; the old generic 5D cross-grain interpretation
    is not used here. Oblique, unequal bolt-force row applicability remains an
    explicit interpretation limit rather than a fabricated universal rule.
    """
    diameter = positive(diameter_mm)
    grain = vector(member['grain'],unit=True)
    normal = [0.,grain[2],-grain[1]]
    local = [(dot(vector(p),grain),dot(p,normal)) for p in points]
    if not 2<=len(local)<=4:
        raise ValueError('Require two to four bolt points')
    thickness = positive(member['width_mm'])
    ratio = thickness/diameter
    perpendicular_rows = 2.5*diameter if ratio<=2 else 5*diameter if ratio>=6 else (5*thickness+10*diameter)/8
    margins = []
    for (s1,q1),(s2,q2) in itertools.combinations(local,2):
        ds,dq = abs(s1-s2),abs(q1-q2)
        margins.append(math.hypot(ds,dq)-4*diameter)
        # Aligned component rows are directly checkable. Arbitrarily oblique
        # pairs are not silently treated as grain-parallel rows.
        if dq<1e-5:
            margins.append(ds-max(4*diameter,perpendicular_rows))
        if ds<1e-5:
            margins.append(dq-4*diameter)
    spread = max(q for _,q in local)-min(q for _,q in local)
    centre = [sum(p[i] for p in points)/len(points) for i in range(3)]
    offsets = [[p[i]-centre[i] for i in range(3)] for p in points]
    yy=sum(p[1]**2 for p in offsets);zz=sum(p[2]**2 for p in offsets);yz=sum(p[1]*p[2] for p in offsets)
    return {'minimum_component_spacing_margin_mm':min(margins),
            'cross_grain_spread_mm':spread,'cross_grain_limit_mm':127.,
            'component_spacing_screen_passed':min(margins)>=0 and spread<=127.,
            'noncollinear':yy*zz-yz*yz>1e-6,
            'scope':'4D pair spacing; aligned component rows checked with load-relative Table12.5.1D direction. General oblique group row applicability remains conditional.'}


def assess(report, geometries, hardware, *, hole_diameter_mm):
    """Actual per-bolt forces, group geometry, local wood and net-section checks."""
    validity={key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY','producer_validity':validity,'qualified_for_design':False}
    rows={n:r for n,r in report['physical_connection_forces'].items() if n.startswith('lumber_leg_bolt_')}
    if not rows or set(rows)!=set(geometries):
        raise ValueError('Actual bolt inventory must match supplied geometry')
    members={name:m for geometry in geometries.values() for name,m in geometry['members'].items()}
    bolts={name:bolt_check(row,geometries[name],hardware) for name,row in rows.items()}
    for name,bolt in bolts.items():
        bolt['fully_threaded_sensitivity']=fully_threaded_sensitivity(bolt,geometries[name])
        bolt['nominal_diameter_condition']='Actual threaded bearing must satisfy NDS 12.3.7.2 (no more than one quarter of either bearing length); nominal 8-inch hardware alone does not verify delivered thread/runout tolerances.'
    groups={}
    for name,member in members.items():
        names=[n for n,r in rows.items() if name in (r['first'],r['second'])]
        points=[rows[n]['point'] for n in names]
        layout=layout_check(points,member,geometries[names[0]]['diameter_mm'])
        span=max(norm([a-b for a,b in zip(p,q,strict=True)]) for p,q in itertools.combinations(points,2))
        cg=conservative_group_factor(len(names),geometries[names[0]]['diameter_mm'],span,member['width_mm']*member['depth_mm'])
        groups[name]={'layout':layout,'conservative_total_count_row_factor':cg,
            'peak_individual_lateral_ratio':max(bolts[n]['lateral_ratio'] for n in names),
            'peak_with_additional_group_reduction':max(bolts[n]['lateral_ratio']/cg for n in names)}
    for bolt in bolts.values():
        bolt['limits'][0]='Actual individual solved force in a moment group; separate conservative total-count row sensitivity is reported.'
    return {'candidate':report['candidate'],'producer_validity':validity,'bolts':bolts,
            'groups':groups,'local':assess_local(report,members,hole_diameter_mm=hole_diameter_mm),
            'status':'CONDITIONAL_COMPARISONS_ONLY','qualified_for_design':False}


def assess_local(report, members, *, hole_diameter_mm):
    """Moment-group local wood and station-matched net stress diagnostics.

    members is actual CAD geometry keyed by the four joined timber names:
    grain, centre_mm, end_stations_mm, width_mm, depth_mm,
    additional_section_boxes, section_cut_boxes and openings_complete. Extra opening boxes use the
    same grain/depth coordinates as centre_mm. This consumes sampled native
    sections; it does not claim to have recovered actions at every opening.
    """
    from fea.current_response_resistance import member_comparisons
    from fea.wider_leg_wood_checks import joint_local_checks

    positive(hole_diameter_mm)
    validity = {key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY','producer_validity':validity,'qualified_for_design':False}
    forces = {k:r for k,r in report['physical_connection_forces'].items() if k.startswith('lumber_leg_bolt_')}
    expected = {r[side] for r in forces.values() for side in ('first','second')}
    if not forces or set(members) != expected:
        raise ValueError('Require geometry for every joined pivot member')
    local = {}
    for name,member in members.items():
        rows = [r for r in forces.values() if name in (r['first'],r['second'])]
        if not 2 <= len(rows) <= 4:
            raise ValueError('Require two to four bolts per joined member')
        points = [vector(r['point']) for r in rows]
        actions = [vector(r['force_on_first_xyz_n'] if name == r['first'] else r['force_on_second_xyz_n']) for r in rows]
        grain = vector(member['grain'],unit=True)
        centre = vector(member['centre_mm'])
        normal = [0.,grain[2],-grain[1]]
        holes = []
        for point in points:
            offsets = [a-b for a,b in zip(point,centre,strict=True)]
            holes.append((dot(offsets,grain),dot(offsets,normal),hole_diameter_mm))
        bolt_holes = list(holes)
        holes.extend(member['additional_section_boxes'])
        wood = joint_local_checks(points,actions,grain=grain,centre=centre,
            end_stations_mm=member['end_stations_mm'],depth_mm=member['depth_mm'],
            width_mm=member['width_mm'],hole_mm=hole_diameter_mm,
            additional_section_boxes=member['additional_section_boxes'])
        data = report['member_section_demands'][name]
        native = data['member']
        if any(not math.isclose(a,b,abs_tol=1e-5) for a,b in zip((native['width_mm'],native['depth_mm']),(member['width_mm'],member['depth_mm']),strict=True)):
            raise ValueError('Native and CAD member dimensions differ')
        if 'axis' in native and dot(vector(native['axis'],unit=True),grain)<1-1e-8:
            raise ValueError('Native and CAD grain directions differ')
        if 'section_u' in native:
            orientation = dot(vector(native['section_u'],unit=True),[1.,0.,0.])
            if abs(orientation)<1-1e-8:
                raise ValueError('Cut-box width requires native section_u parallel to global X')
            if 'section_v' in native and dot(vector(native['section_v'],unit=True),normal)*orientation<1-1e-8:
                raise ValueError('Native section axes must flip together relative to cut-box axes')
            # Native -X,-q flips both signed moments and both centroid offsets.
            # The independent absolute-action stress bound is invariant to that
            # simultaneous reversal; cut-box coordinates remain global X,q.
        boxes = list(member['section_cut_boxes']) if 'section_cut_boxes' in member else [r['section_box_sxq_mm'] for r in member['opening_records']]
        for bolt_s,bolt_q,_ in bolt_holes:
            boxes.append([bolt_s-hole_diameter_mm/2,bolt_s+hole_diameter_mm/2,
                          -member['width_mm']/2,member['width_mm']/2,
                          bolt_q-hole_diameter_mm/2,bolt_q+hole_diameter_mm/2])
        checks, sampled_stations = [],[]
        for section in data['sections']:
            station = dot([a-b for a,b in zip(vector(section['origin_xyz_mm']),centre,strict=True)],grain)
            sampled_stations.append(station)
            active = [(u0,u1,q0,q1) for s0,s1,u0,u1,q0,q1 in boxes if s0-1e-7<=station<=s1+1e-7]
            properties = bounded_section_properties(member['width_mm'],member['depth_mm'],active)
            comparison = bounded_section_check(data,member,section,properties)
            checks.append({'station_mm_from_cad_centre':station,'active_hole_count':len(active),
                'actual_area_mm2':properties['area_mm2'],
                'actual_moduli_mm3':[properties['strong_modulus_mm3'],properties['weak_modulus_mm3']],
                'actual_cut_box_properties':properties,'comparison':comparison})
        if not checks:
            raise ValueError('Require sampled member sections')
        peak = max(checks,key=lambda c:c['comparison']['conservative_net_section_envelope_ratio'])
        local[name] = {'joint_wood':wood,'sampled_net_peak':peak,
            'all_opening_centres_sampled':all(any(abs(s-p)<1e-5 for p in sampled_stations) for s,_,_ in holes),
            'all_openings_represented':member.get('openings_complete',member.get('all_openings_represented')) is True,
            'sampled_full_length_unbraced_sensitivity_failed':any(c['comparison']['conditional_checked_failure'] for c in checks),
            'qualified_for_design':False,
            'limits':['Net sections use only cut boxes intersecting each sampled native section; actual partial-width extents and product inertia are retained conservatively.',
                      'Raw end cuts, local opening stress concentrations, torsion and unsampled opening stations are not qualified.',
                      'NDS Appendix E parallel checks and supplemental EC5 splitting retain their separate reference conventions.']}
    header_source = dict(report,member_section_demands={k:v for k,v in report['member_section_demands'].items() if k=='base_header'})
    header = member_comparisons(header_source)
    for result in header.values():
        result.pop('checks',None)
    return {'candidate':report['candidate'],'producer_validity':validity,
            'local_members':local,'header_gross':header,
            'scope':'Local bolt-group timber and sampled net sections; header gross actions include modeled cantilever load transfer, not local header connection qualification.',
            'qualified_for_design':False}
