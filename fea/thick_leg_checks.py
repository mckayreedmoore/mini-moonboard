"""Supplied-geometry single-pivot screens, without CAD or construction approval.

The caller supplies actual material intervals, directional edge rays and hardware
assumptions. Recovered axial increments do not establish contact or prying bounds.
"""
import itertools
import math

from fea.current_response_resistance import VALIDITY
from fea.dowel_yield import single_shear
from fea.reinforced_fastener_checks import dot, norm


def positive(value):
    if not math.isfinite(value) or value <= 0:
        raise ValueError('Require positive finite dimensions and references')
    return value


def vector(value, *, unit=False):
    if len(value) != 3 or not all(math.isfinite(x) for x in value):
        raise ValueError('Require finite three-component vector')
    if unit and not math.isclose(norm(value),1.,abs_tol=1e-8):
        raise ValueError('Require unit vector')
    return value


def hardware_check(lateral_n, axial_n, hardware):
    """Direct steel stresses and one bearing washer per timber face.

    All reference dimensions and strengths are explicit provisional inputs.
    Loose washers receive no composite action. Clamp preload is not included.
    """
    tension = abs(axial_n)
    tensile_area = positive(hardware['tensile_area_mm2'])
    shear_area = positive(hardware['shear_area_mm2'])
    fy = positive(hardware['steel_yield_mpa'])
    omega = positive(hardware['steel_safety_factor'])
    sigma,tau = tension/tensile_area,lateral_n/shear_area
    washers = []
    for washer in hardware['washers']:
        outer,inner = positive(washer['outer_diameter_mm']),positive(washer['hole_diameter_mm'])
        seat = positive(washer['seat_diameter_mm'])
        thickness = positive(washer['thickness_mm'])
        if not inner < seat <= outer:
            raise ValueError('Require washer hole < seat <= outer diameter')
        area = math.pi*(outer*outer-inner*inner)/4
        pressure = tension/area
        a,c = seat/2,(outer-seat)/2
        moment = pressure*(c*c/2+c**3/(3*a))
        washers.append({'wood_bearing_ratio':pressure/positive(washer['wood_bearing_mpa']),
            'elastic_bending_ratio':6*moment*positive(washer['safety_factor'])/(thickness**2*positive(washer['yield_mpa'])),
            'net_bearing_area_mm2':area,'scope':'Uniform annular pressure and independent radial strips; local contact and preload unresolved.'})
    if len(washers) != 2:
        raise ValueError('Require one explicit bearing washer per timber face')
    return {'absolute_axial_increment_n':tension,'steel_direct_ratio':math.hypot(sigma,math.sqrt(3)*tau)/(fy/omega),
            'axial_stress_mpa':sigma,'remaining_bending_yield_mpa':fy-sigma,
            'washers':washers,'preload_or_prying_bound_established':False}


def bolt_check(row, geometry, hardware):
    """Actual single-shear thickness and all six TR12 dowel modes.

    geometry: diameter_mm, bending_yield_psi, members keyed by native member
    name. Each member: grain, bearing_length_mm, specific_gravity,
    parallel_bearing_psi and edge_distances_mm keyed grain_positive,
    grain_negative, depth_positive, depth_negative. Ray lengths are axis-center
    distances to actual CAD stock boundaries, not distance from the hole surface.
    """
    axis = vector(row['axis'],unit=True)
    force = vector(row['force_on_first_xyz_n'])
    reaction = vector(row['force_on_second_xyz_n'])
    if norm([a+b for a,b in zip(force,reaction,strict=True)]) > 1e-6:
        raise ValueError('Action/reaction mismatch')
    axial = dot(force,axis)
    lateral_vector = [f-axial*a for f,a in zip(force,axis,strict=True)]
    lateral = norm(lateral_vector)
    diameter_mm = positive(geometry['diameter_mm'])
    diameter = diameter_mm/25.4
    fyb = positive(geometry['bending_yield_psi'])
    bearings,lengths,placement = [],[],{}
    for side in ('first','second'):
        name = row[side]
        member = geometry['members'][name]
        grain = vector(member['grain'],unit=True)
        if abs(dot(axis,grain)) > 1e-8 or abs(grain[0]) > 1e-8:
            raise ValueError('Require through-thickness bolt and sagittal member grain')
        parallel = positive(member['parallel_bearing_psi'])
        perpendicular = 6100*positive(member['specific_gravity'])**1.45/math.sqrt(diameter)
        cosine2 = min(1.,(dot(lateral_vector,grain)/lateral)**2) if lateral else 0.
        bearings.append(parallel*perpendicular/(parallel*(1-cosine2)+perpendicular*cosine2))
        lengths.append(positive(member['bearing_length_mm'])/25.4)
        member_force = force if side == 'first' else reaction
        depth_force = dot(member_force,[0.,grain[2],-grain[1]])
        edges = member['edge_distances_mm']
        margins = {}
        for key in ('grain_positive','grain_negative','depth_positive','depth_negative'):
            distance = positive(edges[key])
            factor = 7. if key.startswith('grain') else 4. if ((key == 'depth_positive' and depth_force > 1e-8) or (key == 'depth_negative' and depth_force < -1e-8)) else 1.5
            margins[key] = distance-factor*diameter_mm
        placement[name] = {'depth_force_on_member_n':depth_force,'margins_mm':margins,
            'minimum_margin_mm':min(margins.values()),'passes_directional_screen':min(margins.values())>=0,
            'basis':'7D both ends; 4D force-directed loaded edge, 1.5D unloaded. Applying perpendicular edge rule to oblique force is a conservative screen.'}
    reference = single_shear(main_length_in=lengths[0],side_length_in=lengths[1],
        main_bearing_lb_in=bearings[0]*diameter,side_bearing_lb_in=bearings[1]*diameter,
        main_yield_moment_lb_in=fyb*diameter**3/6,side_yield_moment_lb_in=fyb*diameter**3/6,
        gap_in=0.,reduction_terms={'Im':5.,'Is':5.,'II':4.5,'IIIm':4.,'IIIs':4.,'IV':4.})
    capacity = reference['reference_lateral_lbf']*4.4482216152605
    steel = hardware_check(lateral,axial,hardware)
    return {'diameter_mm':diameter_mm,'bearing_lengths_mm':[v*25.4 for v in lengths],
            'bearing_psi':bearings,'lateral_demand_n':lateral,'lateral_reference_n':capacity,
            'lateral_ratio':lateral/capacity,'dowel_reference':reference,'placement':placement,
            'hardware':steel,'retained_bending_yield_under_axial_increment':steel['remaining_bending_yield_mpa']>=fyb*.006894757293168361,
            'qualified_for_design':False,
            'limits':['Single fastener; no group redistribution factor. Actual installation must establish smooth bearing through both supplied lengths.',
                      'Material, edge direction and axial force reflect only this solved case; load reversal may change the controlling edge.',
                      'Local splitting, net sections, free pivot travel, complete hardware fit and prying remain separate checks.']}


def assess(report, geometries, hardware):
    """Fail closed on native numerical validity and exact bolt inventory."""
    validity = {key:report.get(key) is True for key in VALIDITY}
    if not all(validity.values()):
        return {'status':'INVALID_RESPONSE_DIAGNOSTIC_ONLY','producer_validity':validity,'qualified_for_design':False}
    rows = {k:v for k,v in report['physical_connection_forces'].items() if k.startswith('lumber_leg_bolt_')}
    if not rows or set(rows) != set(geometries):
        raise ValueError('Actual bolt inventory must match supplied geometry')
    return {'candidate':report['candidate'],'producer_validity':validity,
            'bolts':{name:bolt_check(row,geometries[name],hardware) for name,row in rows.items()},
            'status':'CONDITIONAL_COMPARISONS_ONLY','qualified_for_design':False}


def bounded_section_properties(width, depth, rectangles):
    """Exact rectangle-union subtraction and unsymmetric section properties.

    Rectangles conservatively bound actual cuts in the section plane. Integrate
    retained rectilinear cells once, so overlapping cuts are never double-counted.
    Moduli bound linear stress over the entire stock bounding rectangle.
    """
    positive(width)
    positive(depth)
    cuts = []
    for u0,u1,v0,v1 in rectangles:
        if not all(math.isfinite(x) for x in (u0,u1,v0,v1)) or u0>u1 or v0>v1:
            raise ValueError('Require finite ordered rectangle bounds')
        u0,u1 = max(-width/2,u0),min(width/2,u1)
        v0,v1 = max(-depth/2,v0),min(depth/2,v1)
        if u1>u0 and v1>v0:
            cuts.append((u0,u1,v0,v1))
    us = sorted({-width/2,width/2,*(u for r in cuts for u in r[:2])})
    vs = sorted({-depth/2,depth/2,*(v for r in cuts for v in r[2:])})
    area=first_u=first_v=second_u=second_v=product=0.
    for u0,u1 in itertools.pairwise(us):
        for v0,v1 in itertools.pairwise(vs):
            cu,cv = (u0+u1)/2,(v0+v1)/2
            if any(a<=cu<=b and c<=cv<=d for a,b,c,d in cuts):
                continue
            a = (u1-u0)*(v1-v0)
            area += a
            first_u += a*cu
            first_v += a*cv
            second_u += (v1-v0)*(u1**3-u0**3)/3
            second_v += (u1-u0)*(v1**3-v0**3)/3
            product += (u1*u1-u0*u0)*(v1*v1-v0*v0)/4
    positive(area)
    cu,cv = first_u/area,first_v/area
    iu,iv,ip = second_u-area*cu*cu,second_v-area*cv*cv,product-area*cu*cv
    determinant = positive(iu*iv-ip*ip)
    corners = [(u-cu,v-cv) for u in (-width/2,width/2) for v in (-depth/2,depth/2)]
    strong = 1/max(abs((-ip*u+iu*v)/determinant) for u,v in corners)
    weak = 1/max(abs((iv*u-ip*v)/determinant) for u,v in corners)
    return {'area_mm2':area,'centroid_uv_mm':[cu,cv],
            'second_moments_u2_v2_uv_mm4':[iu,iv,ip],
            'strong_modulus_mm3':strong,'weak_modulus_mm3':weak,
            'scope':'Actual cut-box union, including product inertia; conservative linear stress over stock bounding corners.'}


def bounded_section_check(data, member, section, properties):
    """Actual station actions and cut-box section; gross stability sensitivity."""
    from fea.reinforced_timber_resistance import effective_beam_length, member_check

    b,d = member['width_mm'],member['depth_mm']
    axial = section['axial_n_tension_positive']
    cu,cv = properties['centroid_uv_mm']
    check = member_check(width_mm=b,depth_mm=d,
        axial_n=axial*b*d/properties['area_mm2'],
        moment_strong_nmm=(abs(section['moment_u_nmm'])+abs(axial*cv))*(b*d*d/6)/properties['strong_modulus_mm3'],
        moment_weak_nmm=(abs(section['moment_v_nmm'])+abs(axial*cu))*(d*b*b/6)/properties['weak_modulus_mm3'],
        shear_strong_n=section['shear_v_n']*b*d/properties['area_mm2'],
        shear_weak_n=section['shear_u_n']*b*d/properties['area_mm2'],
        torsion_nmm=section['torsion_nmm'],column_effective_strong_mm=data['length_mm'],
        column_effective_weak_mm=data['length_mm'],beam_effective_mm=effective_beam_length(data['length_mm'],d))
    check['local_opening_resistance_evaluated'] = False
    check['section_metadata_basis'] = 'Equivalent gross section with scaled actions; enclosing actual_cut_box_properties records net geometry.'
    check['conservative_net_section_envelope_ratio'] = max(check['necessary_compression_interaction_even_if_fully_braced'],check['tension_conservative_interaction'],check['shear_ratio'])
    return check


def assess_local(report, members, *, hole_diameter_mm):
    """Single-pivot local wood and station-matched net stress diagnostics.

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
        if len(rows) != 1:
            raise ValueError('Local thick-pivot check requires one bolt per joint member')
        row = rows[0]
        point = vector(row['point'])
        force = vector(row['force_on_first_xyz_n'] if name == row['first'] else row['force_on_second_xyz_n'])
        grain = vector(member['grain'],unit=True)
        centre = vector(member['centre_mm'])
        normal = [0.,grain[2],-grain[1]]
        offsets = [a-b for a,b in zip(point,centre,strict=True)]
        holes = [(dot(offsets,grain),dot(offsets,normal),hole_diameter_mm),*member['additional_section_boxes']]
        wood = joint_local_checks([point],[force],grain=grain,centre=centre,
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
        pivot_s,pivot_q,_ = holes[0]
        boxes.append([pivot_s-hole_diameter_mm/2,pivot_s+hole_diameter_mm/2,
                      -member['width_mm']/2,member['width_mm']/2,
                      pivot_q-hole_diameter_mm/2,pivot_q+hole_diameter_mm/2])
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
            'scope':'Local pivot timber and sampled net sections; header gross actions include modeled cantilever load transfer, not local header connection qualification.',
            'qualified_for_design':False}
