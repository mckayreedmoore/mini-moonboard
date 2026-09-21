"""Normal timber bearing at unnotched exterior leg feet; no floor qualification."""
import math

from fea.reinforced_timber_resistance import PSI_MPA, bearing_check

CANDIDATE = 'compact-exterior-brace-development'
SOURCES = [
    'https://plib.org/wp-content/uploads/2020/09/AWC-NDS2018.pdf',
    'https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210113_AWCWebsite_Appendix.pdf',
]


def leg_foot_bearing_check(report, geometry):
    """Validate equal-area midpoint cells against the actual horizontal foot profile.

    NDS 3.10.3 and Appendix J.3 use the surface-normal force component and its
    angle to grain. Tangential traction is not added to normal bearing pressure;
    existing member shear/combined-action checks remain independently necessary.
    """
    n = report['parameters'].get('leg_floor_grid')
    if report.get('candidate') != CANDIDATE or type(n) is not int or n < 2:
        raise ValueError('Require exterior candidate with explicit square foot grid')
    physical = report['physical_connection_forces']
    bearing_rows = report['bearings']
    bearings = {row['name']: row for row in bearing_rows}
    if len(bearings) != len(bearing_rows):
        raise ValueError('Duplicate bearing inventory')
    cells, feet = {}, {}
    for name in ('lumber_leg_left', 'lumber_leg_right'):
        member = geometry['members'][name]
        grain = member['grain']
        width, depth = member['width_mm'], member['depth_mm']
        centre = member['centre_mm']
        values = [*grain, *centre, width, depth, *[v for p in member['profile_sq_mm'] for v in p]]
        if (not all(math.isfinite(v) for v in values) or width <= 0
                or not math.isclose(width, 88.9, abs_tol=1.e-3)
                or not math.isclose(depth, 139.7, abs_tol=1.e-3)
                or not math.isclose(sum(v*v for v in grain), 1., abs_tol=1.e-9)
                or abs(grain[0]) > 1.e-9 or grain[2] <= 0
                or any(r.get('kind') == 'tab_notch' for r in member.get('opening_records', []))):
            raise ValueError('Require actual unnotched 4x6 leg geometry and unit grain')
        profile = [(centre[1]+grain[1]*s+grain[2]*q,
                    centre[2]+grain[2]*s-grain[1]*q)
                   for s,q in member['profile_sq_mm']]
        bottom = sorted({round(y, 7) for y,z in profile if abs(z) < 1.e-5})
        if len(bottom) != 2 or min(z for y,z in profile) < -1.e-5:
            raise ValueError('Require full horizontal foot at floor zero')
        ymin, ymax = bottom
        length = ymax-ymin
        if not math.isclose(length, depth/grain[2], abs_tol=1.e-5):
            raise ValueError('Foot profile differs from full unnotched stock section')
        area = width*length/n**2
        theta = math.degrees(math.acos(min(1., grain[2])))
        expected = {f'floor_{name}_{i}' for i in range(n*n)}
        actual = {k for k,r in physical.items()
                  if r['first'] == name and r['second'] == 'floor' and 'scalar_normal' in r}
        if actual != expected or not expected <= bearings.keys():
            raise ValueError('Leg normal contact inventory differs from square grid')
        positions = set()
        for key in sorted(expected):
            row, bearing = physical[key], bearings[key]
            x,y,z = row['point']
            fraction = row['normal_stiffness_fraction']
            force = row['force_on_first_xyz_n']
            if (not all(math.isfinite(v) for v in (x,y,z,fraction,*force))
                    or row['scalar_normal'] != [0.,0.,1.]
                    or abs(z) > 1.e-5 or max(abs(force[0]),abs(force[1])) > 1.e-8
                    or not math.isclose(fraction, 1/n**2, rel_tol=1.e-9)):
                raise ValueError('Invalid normal cell direction, force or area fraction')
            ix = (x-(centre[0]-width/2))/(width/n)-.5
            iy = (y-ymin)/(length/n)-.5
            index = (round(ix), round(iy))
            if (abs(ix-index[0]) > 1.e-6 or abs(iy-index[1]) > 1.e-6
                    or any(i < 0 or i >= n for i in index) or index in positions):
                raise ValueError('Normal cells must occupy each actual foot midpoint once')
            positions.add(index)
            compression = bearing['compression_force_n']
            if (not math.isfinite(compression) or compression < 0 or force[2] < -1.e-8
                    or not math.isclose(compression, force[2], abs_tol=1.e-6)
                    or (not bearing['active'] and compression > 1.e-8)):
                raise ValueError('Normal force disagrees with compression-only bearing record')
            result = bearing_check(compression, area, theta, depth)
            cells[key] = {'active':bearing['active'], 'tributary_area_mm2':area,
                'compression_n':compression, 'pressure_mpa':compression/area,
                'angle_to_grain_deg':theta, **result,
                'perpendicular_625psi_screen_ratio':compression/area/(625*PSI_MPA),
                'passed':result['bearing_ratio'] <= 1.}
        feet[name] = {'horizontal_foot_area_mm2':width*length,
                      'grid_n':n, 'cell_count':len(positions), 'angle_to_grain_deg':theta}
    peak = max(row['bearing_ratio'] for row in cells.values())
    return {'cells':cells, 'feet':feet, 'peak_ratio':peak, 'passed':peak <= 1.,
        'basis':'NDS 3.10.3/Appendix J.3; DF-L No.2 dry unincised, CD=1, Fc*=1485 psi (no Cp), Fc-perp=625 psi, Cb=1.',
        'scope':'Normal timber bearing on modeled equal-area cells only. Tangential traction remains in independent member shear/combined-action checks; not measured floor pressure, floor qualification or physical contact convergence.',
        'sources':SOURCES}
