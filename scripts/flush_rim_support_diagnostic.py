"""Map saved flush rim seats to actual header support; no resistance release."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def section_depth(profile, station):
    """Intersect convex CAD vertices with a grain-normal section.

    CAD vertex enumeration does not guarantee perimeter order.
    """
    polygon = list(dict.fromkeys(tuple(p) for p in profile))
    if len(polygon) < 3:
        raise ValueError('Require a convex profile with at least three vertices')
    centre = tuple(sum(p[i] for p in polygon)/len(polygon) for i in (0, 1))
    polygon.sort(key=lambda p: math.atan2(p[1]-centre[1], p[0]-centre[0]))
    values = []
    for (s0, q0), (s1, q1) in zip(polygon, polygon[1:]+polygon[:1], strict=True):
        if min(s0, s1)-1.e-7 <= station <= max(s0, s1)+1.e-7:
            if math.isclose(s0, s1, abs_tol=1.e-7):
                values.extend((q0, q1))
            else:
                fraction = min(1., max(0., (station-s0)/(s1-s0)))
                values.append(q0+fraction*(q1-q0))
    if len(values) < 2:
        raise ValueError('Section does not intersect the member profile')
    return max(values)-min(values)


def diagnose(geometry, report):
    candidate = 'compact-floor-flush-development'
    if geometry.get('candidate') != candidate or report.get('candidate') != candidate:
        raise ValueError('Require matching current flush candidate')
    if report.get('numerically_accepted') is not True:
        raise ValueError('Require a numerically accepted current response')
    for path, digest in geometry['source_sha256'].items():
        if path.startswith('mini_moonboard/') and report['source_sha256'].get(path) != digest:
            raise ValueError('Geometry and response model sources differ: '+path)
    header = report['member_section_demands']['base_header']['member']
    if header['axis'] != [1., 0., 0.] or header['section_u'] != [0., 1., 0.]:
        raise ValueError('Require current flat header orientation')
    header_y = [header['start'][1]+sign*header['width_mm']/2 for sign in (-1, 1)]
    header_top = header['start'][2]+header['depth_mm']/2
    result = {}
    for name in ('base_side_left', 'base_side_right'):
        member = geometry['members'][name]
        grain, centre = member['grain'], member['centre_mm']
        normal = [0., grain[2], -grain[1]]  # CAD profile q is opposite native v.
        profile = list(dict.fromkeys(tuple(p) for p in member['profile_sq_mm']))
        world = [[c+s*g+q*n for c, g, n in zip(centre, grain, normal, strict=True)]
                 for s, q in profile]
        seat = sorted(p[1] for p in world if abs(p[2]-header_top) < 1.e-6)
        if len(seat) != 2:
            raise ValueError('Require exactly two horizontal seat endpoints')
        contact_y = [max(seat[0], header_y[0]), min(seat[1], header_y[1])]
        if contact_y[1] <= contact_y[0]:
            raise ValueError('Rim seat has no positive header overlap')
        def station(y, centre=centre, grain=grain):
            return (y-centre[1])*grain[1]+(header_top-centre[2])*grain[2]
        depth = member['depth_mm']
        retained = (seat[1]-seat[0])*grain[2]
        required_seat = (.75*depth+3.)/grain[2]
        bearing = {key: row for key, row in report['physical_connection_forces'].items()
                   if row['first'] == name and row['second'] == 'base_header'}
        if len(bearing) != 4:
            raise ValueError('Require all four current rim/header bearing reactions')
        native = report['member_section_demands'][name]
        first = min(row['station_along_grain_mm'] for row in native['sections'])
        stresses = []
        b = member['width_mm']
        for row in native['sections']:
            if not math.isclose(row['station_along_grain_mm'], first, abs_tol=1.e-7):
                continue
            corners = [row['axial_n_tension_positive']/(b*depth)
                +row['moment_u_nmm']*(depth/2)/(b*depth**3/12)
                -row['moment_v_nmm']*u/(depth*b**3/12) for u in (-b/2, b/2)]
            stresses.append({'include_station_loads': row['include_station_loads'],
                'origin_xyz_mm': row['origin_xyz_mm'],
                'cut_side_nominal_longitudinal_stress_mpa': corners})
        result[name] = {
            'seat_y_mm': seat, 'contact_y_mm': contact_y,
            'seat_fully_supported_geometrically': all(abs(a-b) < 1.e-6 for a, b in zip(seat, contact_y, strict=True)),
            'contact_inner_edge_local_grain_station_mm': station(contact_y[1]),
            'depth_at_contact_inner_edge_mm': section_depth(profile, station(contact_y[1])),
            'depth_at_header_inner_edge_mm': section_depth(profile, station(header_y[1])),
            'terminal_seat_projected_depth_mm': retained,
            'existing_screen_margin_mm': retained-.75*depth-3.,
            'seat_length_needed_for_existing_screen_mm': required_seat,
            'forward_extension_needed_for_existing_screen_mm': required_seat-(seat[1]-seat[0]),
            'required_seat_excess_over_header_width_mm': required_seat-header['width_mm'],
            'full_header_width_projection_screen_margin_mm': header['width_mm']*grain[2]-.75*depth-3.,
            'bearing_points': {key: {'point_xyz_mm': row['point'],
                'compression_n': row['force_on_first_xyz_n'][2]} for key, row in bearing.items()},
            'total_native_header_compression_n': sum(row['force_on_first_xyz_n'][2] for row in bearing.values()),
            'adjacent_full_section_diagnostic': stresses,
        }
    return {'candidate': candidate, 'header_y_mm': header_y, 'header_top_z_mm': header_top,
        'rims': result, 'qualified_for_design': False,
        'scope': 'Saved geometry and current reactions only. Inner-edge depth does not establish compression-face classification. Adjacent nominal stresses exclude the partial heel region; no local cut resistance or redesigned support is qualified.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(json.loads(args.geometry.read_text()), json.loads(args.report.read_text()))
    result['input_sha256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                             for path in (args.geometry, args.report, Path(__file__))}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
