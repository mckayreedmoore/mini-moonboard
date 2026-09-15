"""Analytic nominal longitudinal stress extrema; no local taper resistance claim.

Actions are exact free-body resultants of the supplied connector-load model.
Between adjacent recorded load stations, N is constant and Mu/Mv are affine.
For a linearly tapered rectangle, each corner stress is p(t)/w(t)^2 with
quadratic p and affine positive w. Its derivative numerator is affine, so
endpoints plus its one possible interior root give exact nominal extrema.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path


def corner_extrema(width_start, width_end, depth, axial, moment_u,
                   moment_v_centroid, corner_u, corner_v):
    """Signed corner stresses in a right-handed (u,v,grain) frame, MPa.

    moment tuples contain endpoint values about the retained section centroid.
    sigma = N/A - Mv*u/Iv + Mu*v/Iu. Corner signs select u=sign*w/2,
    v=sign*d/2. Return all analytic extrema candidates, including endpoints.
    """
    values = (width_start,width_end,depth,axial,*moment_u,*moment_v_centroid)
    if not all(math.isfinite(x) for x in values) or min(width_start,width_end,depth)<=0:
        raise ValueError('Require finite actions and positive section dimensions')
    if corner_u not in (-1,1) or corner_v not in (-1,1):
        raise ValueError('Corner signs must be -1 or +1')
    w,k = width_start,width_end-width_start
    mu,du = moment_u[0],moment_u[1]-moment_u[0]
    mv,dv = moment_v_centroid[0],moment_v_centroid[1]-moment_v_centroid[0]
    p0 = axial*w/depth-6*corner_u*mv/depth+6*corner_v*mu*w/depth**2
    p1 = axial*k/depth-6*corner_u*dv/depth+6*corner_v*(mu*k+du*w)/depth**2
    p2 = 6*corner_v*du*k/depth**2
    # (p' w - 2 p w') = intercept + slope*t; quadratic terms cancel.
    intercept,slope = p1*w-2*p0*k,2*p2*w-p1*k
    ts = [0.,1.]
    if slope != 0:
        root = -intercept/slope
        if 0<root<1:
            ts.append(root)
    return [{'fraction':t,'longitudinal_stress_mpa':(p0+p1*t+p2*t*t)/(w+k*t)**2}
            for t in sorted(ts)]


def _close(a,b,abs_tol=1.e-5):
    if not math.isclose(a,b,rel_tol=1.e-8,abs_tol=abs_tol):
        raise ValueError(f'Inconsistent native action/geometry: {a} != {b}')


def member_diagnostic(data):
    member = data['member']
    taper = member['floor_recess_geometry']
    grain = taper['grain_axis_xyz']
    for a,b in zip(member['section_u'],(1.,0.,0.),strict=True):
        _close(a,b)
    for a,b in zip(member['section_v'],taper['normal_axis_xyz'],strict=True):
        _close(a,b)
    start,end = taper['taper_start_station_mm'],taper['taper_end_station_mm']
    removed,sign = taper['max_recess_depth_mm'],taper['outward_sign']
    width,depth = member['width_mm'],member['depth_mm']
    if not start<end or not 0<removed<width or sign not in (-1,1):
        raise ValueError('Require supported linear side taper')
    sections = {}
    for row in data['sections']:
        station = sum(a*b for a,b in zip(row['origin_xyz_mm'],grain,strict=True))
        if start-1e-6<=station<=end+1e-6:
            key = next((s for s in sections if abs(s-station)<1e-6),station)
            sections.setdefault(key,{})[row['include_station_loads']] = row
    stations = sorted(sections)
    if len(stations)<2:
        raise ValueError('Both taper boundaries must be recorded')
    _close(stations[0],start)
    _close(stations[-1],end)
    rows = []
    for s0,s1 in itertools.pairwise(stations):
        # Free body above the cut: exclude a left-end load; include a right-end load.
        left,right = sections[s0][False],sections[s1][True]
        for key in ('axial_n_tension_positive','shear_u_n','shear_v_n','torsion_nmm'):
            _close(left[key],right[key])
        _close(right['moment_u_nmm']-left['moment_u_nmm'],(s1-s0)*left['shear_v_n'],.001)
        _close(right['moment_v_nmm']-left['moment_v_nmm'],-(s1-s0)*left['shear_u_n'],.001)
        cuts = [removed*max(0.,min(1.,(end-s)/(end-start))) for s in (s0,s1)]
        n = left['axial_n_tension_positive']
        widths = [width-c for c in cuts]
        mus = [r['moment_u_nmm'] for r in (left,right)]
        mvs = [r['moment_v_nmm']+sign*c*n/2 for r,c in zip((left,right),cuts,strict=True)]
        for u in (-1,1):
            for v in (-1,1):
                for row in corner_extrema(*widths,depth,n,mus,mvs,u,v):
                    rows.append({**row,'grain_station_mm':s0+row['fraction']*(s1-s0),
                        'interval_mm':[s0,s1],'corner_u_sign':u,'corner_v_sign':v,
                        'on_cut_face':u==-sign})
    face = [r for r in rows if r['on_cut_face']]
    maximum = max(face,key=lambda r:r['longitudinal_stress_mpa'])
    return {'method':'ANALYTIC_NOMINAL_PLANE_SECTION_EXTREMA',
        'taper_interval_mm':[start,end],'load_interval_count':len(stations)-1,
        'extrema_candidates':rows,
        'maximum_nominal_longitudinal_stress':max(rows,key=lambda r:r['longitudinal_stress_mpa']),
        'minimum_nominal_longitudinal_stress':min(rows,key=lambda r:r['longitudinal_stress_mpa']),
        'maximum_nominal_cut_face_longitudinal_stress':maximum,
        'minimum_nominal_cut_face_longitudinal_stress':min(face,key=lambda r:r['longitudinal_stress_mpa']),
        'cut_face_compression_only_in_nominal_model':maximum['longitudinal_stress_mpa']<=0,
        'nominal_face_stress_times_slope_squared_mpa':maximum['longitudinal_stress_mpa']*(removed/(end-start))**2,
        'slope_identity_scope':'For an ideal smooth traction-free face only. Multiplying nominal longitudinal stress by slope squared is a diagnostic, not a recovered local transverse stress or resistance check.'}


def analyze(path):
    raw = Path(path).read_bytes()
    report = json.loads(raw)
    if report['candidate'] != 'compact-floor-flush-development':
        raise ValueError('Require the flush candidate report')
    return {'candidate':report['candidate'],'report_path':str(path),
        'report_sha256':hashlib.sha256(raw).hexdigest(),
        'status':'DIAGNOSTIC_ONLY_NO_LOCAL_RESISTANCE_QUALIFICATION',
        'members':{name:member_diagnostic(report['member_section_demands'][name])
                   for name in ('lumber_leg_left','lumber_leg_right')},
        'limits':['Plane sections and the actual lumped connector/gravity load model; no local stress recovery.',
                  'No perpendicular-grain tensile allowable, fracture acceptance or taper-transition qualification.',
                  'No torsional/local shear interaction acceptance or construction release.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    parser.add_argument('output',type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(analyze(args.report),indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
