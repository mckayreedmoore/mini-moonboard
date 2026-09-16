"""Conditional actual-taper section comparisons; not an EC5 certification.

EC5 notch reduction is applied to the project's unchanged US DF-L ASD shear
reference. This intentionally conservative hybrid is explicitly a comparison.
"""
import math

from fea.reinforced_timber_resistance import adjusted_reference
from fea.thick_leg_checks import bounded_section_check, bounded_section_properties
from scripts.compact_knee_results import cut_inventory, dot

CANDIDATE = 'compact-floor-taper-development'
NATIVE_BASIS = 'ACTUAL_GRAIN_TAPER_FOOT_RECESS_C3D20'
SOURCES = {
    'notch': 'https://www.swedishwood.com/siteassets/5-publikationer/pdfer/glulamhandbook2-240508.pdf',
    'torsion': 'https://www.fpl.fs.usda.gov/documnts/fplgtr/fplgtr190/chapter_09.pdf',
    'rectangular_elasticity': 'https://www.ae.msstate.edu/tupas/SA2/chA6.4_text.html',
}


def notch_factor(depth_mm, remaining_mm, taper_run_mm, support_distance_mm):
    """EC5 6.5.2 solid-timber kn=5, dimensions mm, notch inclination i=run/removed depth."""
    values = (depth_mm, remaining_mm, taper_run_mm, support_distance_mm)
    if not all(math.isfinite(v) for v in values) or not (0 < remaining_mm < depth_mm and taper_run_mm > 0 and support_distance_mm >= 0):
        raise ValueError('Require finite positive notch geometry and nonnegative support distance')
    alpha = remaining_mm/depth_mm
    slope = taper_run_mm/(depth_mm-remaining_mm)
    denominator = math.sqrt(depth_mm)*(math.sqrt(alpha*(1-alpha))
        + .8*support_distance_mm/depth_mm*math.sqrt(1/alpha-alpha**2))
    return min(1., 5.*(1+1.1*slope**1.5/math.sqrt(depth_mm))/denominator)


def rectangular_shear(width_mm, depth_mm, shear_u_n, shear_v_n, torsion_nmm, *, centroid_u_mm=0., centroid_v_mm=0., reduction=1.):
    """Sum maxima, with torsion coefficient 5 bounding the rectangle table.

    No torsional strength enhancement. Not a local hole stress calculation.
    Native section actions are translated conservatively to retained centroid.
    """
    values = (width_mm, depth_mm, shear_u_n, shear_v_n, torsion_nmm, centroid_u_mm, centroid_v_mm, reduction)
    if not all(math.isfinite(v) for v in values) or min(width_mm,depth_mm,reduction) <= 0 or reduction > 1:
        raise ValueError('Require finite actions, positive rectangle and reduction in (0,1]')
    short, long = sorted((width_mm,depth_mm))
    torque = abs(torsion_nmm)+abs(centroid_u_mm*shear_v_n)+abs(centroid_v_mm*shear_u_n)
    torsion = 5*torque/(long*short**2)
    transverse = 1.5*math.hypot(shear_u_n,shear_v_n)/(width_mm*depth_mm)
    reference = adjusted_reference(139.7)['Fv_mpa']
    return {'transverse_shear_mpa':transverse,'torsional_shear_bound_mpa':torsion,
        'retained_centroid_torque_bound_nmm':torque,'notch_reduction':reduction,
        'unreduced_asd_shear_reference_mpa':reference,
        'combined_shear_ratio':(transverse+torsion)/(reduction*reference),
        'scope':'Unbored rectangular section; sum of maximum transverse and torsional shear, no shape-factor strength increase.'}


def leg_floor_points(report, name):
    tangent_cells = report['parameters'].get('floor_tangent_cells')
    if tangent_cells is not None:
        floor = [c['point_xyz_mm'] for c in tangent_cells.values() if c['body'] == name]
    else:
        # The selected no-slip producer has normal cells and a separate
        # conditional centroid tangent spring, not finite-Coulomb cells.
        if report['parameters'].get('floor_friction_assumption') is not None:
            raise ValueError('Finite-friction support lacks tangent-cell geometry')
        floor = [c['point'] for c in report['physical_connection_forces'].values()
                 if c['first'] == name and c['second'] == 'floor'
                 and c.get('scalar_normal') == [0., 0., 1.]]
    if not floor:
        raise ValueError('Require actual floor support cells for each leg')
    return floor


def checks(report, geometry, sections=None):
    """Actual section stress and sampled taper geometry, retaining external gates."""
    if report.get('candidate') not in {CANDIDATE, 'compact-floor-flush-development'} or geometry.get('candidate') != report.get('candidate'):
        raise ValueError('Require matching isolated taper candidate')
    rows = {name: row for name, row in report['physical_connection_forces'].items()
            if name in geometry['hardware_by_name']}
    result = {}
    for name in ('lumber_leg_left','lumber_leg_right'):
        member = geometry['members'][name]
        data = report['member_section_demands'][name]
        native = data['member']
        taper = native.get('floor_recess_geometry', {})
        start,end = taper['taper_start_station_mm'],taper['taper_end_station_mm']
        run = end-start
        removed = taper['max_recess_depth_mm']
        b,d = member['width_mm'],member['depth_mm']
        grain = member['grain']
        retained_band = taper['retained_x_band_mm']
        sign = 1 if sum(retained_band)/2 > member['centre_mm'][0] else -1
        floor = leg_floor_points(report, name)
        support_distance = max(abs(start-dot(p,grain)) for p in floor)
        kv = notch_factor(b,b-removed,run,support_distance)
        cuts = cut_inventory(name,member,rows,geometry['hardware_by_name'])
        sampled = []
        for section in data['sections']:
            station = dot(section['origin_xyz_mm'],grain)
            local = dot([a-c for a,c in zip(section['origin_xyz_mm'],member['centre_mm'],strict=True)],grain)
            remove = removed*min(1.,max(0.,(end-station)/run))
            sidecut = [-b/2,-b/2+remove,-d/2,d/2] if sign > 0 else [b/2-remove,b/2,-d/2,d/2]
            active = [c for c in cuts if c['kind'] not in ('tab_notch','taper_recess') and c['box_sxq_mm'][0]-1.e-7 <= local <= c['box_sxq_mm'][1]+1.e-7]
            properties = bounded_section_properties(b,d,[sidecut,*(c['box_sxq_mm'][2:] for c in active)])
            normal = bounded_section_check(data,member,section,properties)
            shear = rectangular_shear(b-remove,d,section['shear_u_n'],section['shear_v_n'],section['torsion_nmm'],
                centroid_u_mm=sign*remove/2,reduction=kv if station <= end else 1.)
            sampled.append({'absolute_grain_station_mm':station,'retained_width_mm':b-remove,
                'normal_comparison':normal,'shear_comparison':shear,
                'other_openings':active,'torsion_rectangle_applicable':not active})
        if not sampled:
            raise ValueError('Require actual native section actions')
        criteria = {
            'native_actual_taper':native.get('native_section_geometry') == NATIVE_BASIS,
            'native_matches_cad_taper':all(taper.get(k) == member.get('floor_taper_geometry',{}).get(k) for k in
                ('taper_start_station_mm','taper_end_station_mm','max_recess_depth_mm','grain_axis_xyz','retained_x_band_mm')),
            'actual_mesh_volume':math.isfinite(native.get('retained_mesh_volume_mm3',math.nan)) and
                math.isclose(native['retained_mesh_volume_mm3'],taper.get('expected_retained_volume_mm3',math.nan),rel_tol=1.e-8,abs_tol=.02),
            'taper_at_least_one_in_ten':run >= 10*removed-1.e-6,
            'intended_stock_and_runout':math.isclose(b,88.9,abs_tol=1.e-5) and math.isclose(d,139.7,abs_tol=1.e-5)
                and math.isclose(removed,38.1,abs_tol=1.e-5) and run >= 457.2-1.e-5,
            'taper_bounds_sampled':all(any(abs(r['absolute_grain_station_mm']-v)<1.e-5 for r in sampled) for v in (start,end)),
            'actual_net_section_normal_resistance':max(r['normal_comparison']['conservative_net_section_envelope_ratio'] for r in sampled)<=1,
            'sampled_rectangular_shear_torsion':all(r['shear_comparison']['combined_shear_ratio']<=1 for r in sampled if r['torsion_rectangle_applicable']),
            'taper_region_unbored_torsion_applicable':all(r['torsion_rectangle_applicable'] for r in sampled if start-1.e-6 <= r['absolute_grain_station_mm'] <= end+1.e-6),
        }
        result[name] = {'notch_factor':kv,'support_distance_mm':support_distance,'separate_bolt_region_scope':'Nonrectangular bolt sections retain existing local joint and net-section comparisons; rectangular torsion does not qualify hole stress concentrations.','sampled_sections':sampled,'criteria':criteria}
    criteria = {k:all(v['criteria'][k] for v in result.values()) for k in next(iter(result.values()))['criteria']}
    return {'members':result,'criteria':criteria,'passes':all(criteria.values()),'qualified_for_design':False,
        'sources':SOURCES,'scope':__doc__}
