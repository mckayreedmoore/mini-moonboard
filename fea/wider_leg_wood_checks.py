"""Geometry-driven local wood checks for the single-stock six-bolt candidate.

NDS 2024 ASD values and supplemental EC5 splitting are separate comparisons.
Inputs must describe current geometry and actions; this module supplies neither.
"""
import itertools
import math

from fea.reinforced_timber_resistance import adjusted_reference, stability_factor


def dot(a, b):
    return sum(x*y for x, y in zip(a, b, strict=True))


def section_envelope(holes_sq_d, *, depth_mm=184.15, width_mm=38.1):
    """Bound all grain-normal sections by full-diameter rectangular hole strips.

    Each (grain station, depth coordinate, diameter) hole is conservatively a
    square in the member plane. Overlapping strips are unioned, not subtracted
    twice. This captures simultaneous staggered holes without a sampling grid.
    Coordinates are relative to the stock depth centerline.
    """
    if depth_mm <= 0 or width_mm <= 0:
        raise ValueError('Positive stock dimensions required')
    for s, q, d in holes_sq_d:
        if not all(math.isfinite(v) for v in (s, q, d)) or d <= 0 or abs(q)+d/2 > depth_mm/2+1e-9:
            raise ValueError('Require finite holes contained in stock')
    events = sorted({s+sign*d/2 for s, _, d in holes_sq_d for sign in (-1, 1)})
    samples = events+[(a+b)/2 for a,b in itertools.pairwise(events)]
    samples = samples or [0.]
    sections = []
    for station in samples:
        strips = sorted((q-d/2,q+d/2) for s,q,d in holes_sq_d if abs(s-station) <= d/2+1e-9)
        merged = []
        for lo,hi in strips:
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(hi,merged[-1][1])
            else:
                merged.append([lo,hi])
        remaining = depth_mm-sum(hi-lo for lo,hi in merged)
        centroid = -sum((hi*hi-lo*lo)/2 for lo,hi in merged)/remaining
        area = width_mm*remaining
        inertia = width_mm*(depth_mm**3/12-sum((hi**3-lo**3)/3 for lo,hi in merged))-area*centroid**2
        sections.append({'station_mm':station,'removed_intervals_mm':merged,
                         'area_mm2':area,'centroid_mm':centroid,
                         'strong_modulus_mm3':inertia/(depth_mm/2+abs(centroid)),
                         'weak_modulus_mm3':remaining*width_mm**2/6})
    return sections


def member_net_check(compression_n, moment_strong_nmm, *, holes_sq_d,
                     effective_length_mm, mass_kg, axis_vertical_cosine,
                     depth_mm=184.15, width_mm=38.1, face_eccentricity_mm=19.05, duration_factor=1.):
    """Carry entire joint moment and worst net section through supported length."""
    if min(compression_n,mass_kg,face_eccentricity_mm) < 0 or effective_length_mm <= 0:
        raise ValueError('Require nonnegative loads and positive length')
    ref = adjusted_reference(depth_mm)
    if not math.isfinite(duration_factor) or duration_factor <= 0:
        raise ValueError('Positive finite duration factor required')
    for key in ('Fb_star_mpa','Ft_mpa','Fc_star_mpa','Fv_mpa'):
        ref[key] *= duration_factor
    fce1 = .822*ref['Emin_mpa']/(effective_length_mm/depth_mm)**2
    fce2 = .822*ref['Emin_mpa']/(effective_length_mm/width_mm)**2
    cp = stability_factor(min(fce1,fce2)/ref['Fc_star_mpa'],.8)
    rb = math.sqrt(2*effective_length_mm*depth_mm/width_mm**2)
    fbe = 1.2*ref['Emin_mpa']/rb**2
    cl = stability_factor(fbe/ref['Fb_star_mpa'],.95)
    gravity_moment = mass_kg*9.80665*math.sqrt(1-axis_vertical_cosine**2)*effective_length_mm/4
    rows = []
    for section in section_envelope(holes_sq_d,depth_mm=depth_mm,width_mm=width_mm):
        fc = compression_n/section['area_mm2']
        fb1 = (abs(moment_strong_nmm)+gravity_moment+compression_n*abs(section['centroid_mm']))/section['strong_modulus_mm3']
        fb2 = compression_n*face_eccentricity_mm/section['weak_modulus_mm3']
        den1,den2 = 1-fc/fce1,1-fc/fce2-(fb1/fbe)**2
        interaction = ((fc/(cp*ref['Fc_star_mpa']))**2+fb1/(cl*ref['Fb_star_mpa']*den1)+fb2/(ref['Fb_star_mpa']*den2)) if min(den1,den2)>0 else None
        rows.append({**section,'interaction':interaction,'stability':fc/fce2+(fb1/fbe)**2})
    passed = all(r['interaction'] is not None and max(r['interaction'],r['stability']) <= 1 for r in rows)
    return {'sections':rows,'peak_interaction':max((r['interaction'] or 1e100) for r in rows),
            'Cp':cp,'CL':cl,'self_weight_moment_nmm':gravity_moment,
            'effective_length_mm':effective_length_mm,'meets_member_criteria':passed and effective_length_mm/width_mm<=50 and rb<=50,
            'scope':'Conditional NDS 3.9-3/4 leg check; full supplied moment, no joint release'}


def joint_local_checks(points, forces, *, grain, centre, end_stations_mm,
                       depth_mm=184.15, width_mm=38.1, hole_mm=14.2875, kmod=.8, additional_section_boxes=(), duration_factor=1.):
    """Actual-row Appendix E and directional supplemental EC5 splitting.

    Forces are ON the member being checked. No cancellation across bolts is
    credited. For splitting each force sign uses its own loaded-edge distance.
    All rows remain in he: they form one connected through-bolt group.
    """
    if len(points)!=len(forces) or not points:
        raise ValueError('Matching nonempty points and forces required')
    normal = (0.,grain[2],-grain[1])
    local = [(dot([p[i]-centre[i] for i in range(3)],grain),dot([p[i]-centre[i] for i in range(3)],normal)) for p in points]
    sections = section_envelope([(s,q,hole_mm) for s,q in local]+list(additional_section_boxes),depth_mm=depth_mm,width_mm=width_mm)
    ref = adjusted_reference(depth_mm)
    if not math.isfinite(duration_factor) or duration_factor <= 0:
        raise ValueError('Positive finite duration factor required')
    for key in ('Fb_star_mpa','Ft_mpa','Fc_star_mpa','Fv_mpa'):
        ref[key] *= duration_factor
    rows = []
    for i,(s,q) in sorted(enumerate(local),key=lambda v:v[1][1]):
        existing = next((r for r in rows if abs(r['q_mm']-q)<1e-5),None)
        if existing is None:
            existing={'q_mm':q,'indices':[]}
            rows.append(existing)
        existing['indices'].append(i)
    for row in rows:
        stations=sorted(local[i][0] for i in row['indices'])
        critical=min(stations[0]-end_stations_mm[0],end_stations_mm[1]-stations[-1],*(b-a for a,b in itertools.pairwise(stations)))
        if critical<=0:
            raise ValueError('Invalid member ends or coincident row fasteners')
        capacity=len(stations)*ref['Fv_mpa']*width_mm*critical
        demand=sum(abs(dot(forces[i],grain)) for i in row['indices'])
        row.update(critical_spacing_mm=critical,resistance_n=capacity,demand_n=demand,ratio=demand/capacity)
    groups=[]
    for i in range(len(rows)):
        for j in range(i+1,len(rows)):
            selected=rows[i:j+1]
            # Subtract a complete hole for every interior row and half a hole
            # at each bounding row, even where stagger prevents simultaneous cuts.
            net_height=rows[j]['q_mm']-rows[i]['q_mm']-(j-i)*hole_mm
            capacity=(rows[i]['resistance_n']+rows[j]['resistance_n'])/2+ref['Ft_mpa']*width_mm*max(0.,net_height)
            demand=sum(r['demand_n'] for r in selected)
            groups.append({'rows':[i,j],'resistance_n':capacity,'demand_n':demand,'ratio':demand/capacity})
    net_capacity=min(s['area_mm2'] for s in sections)*ref['Ft_mpa']
    parallel=sum(abs(dot(f,grain)) for f in forces)
    splitting=[]
    for sign in (-1,1):
        he=depth_mm/2-min(sign*q for _,q in local)
        characteristic=14*width_mm*math.sqrt(he/(1-he/depth_mm))
        demand=1.5*sum(max(0.,sign*dot(f,normal)) for f in forces)
        resistance=kmod*characteristic/1.3
        splitting.append({'force_sign':sign,'he_mm':he,'demand_n':demand,'resistance_n':resistance,'ratio':demand/resistance})
    return {'rows':rows,'group_tear_out':groups,'net_tension_ratio':parallel/net_capacity,
            'parallel_peak_ratio':max([parallel/net_capacity]+[r['ratio'] for r in rows+groups]),
            'splitting':splitting,'splitting_peak_ratio':max(r['ratio'] for r in splitting),
            'splitting_basis':{'kmod':kmod,'gammaM':1.3,'additional_load_factor':1.5},
            'scope':'NDS Appendix E parallel stresses plus separate supplemental EC5 splitting; no global rim qualification'}
