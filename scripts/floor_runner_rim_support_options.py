"""Compare exact rim support geometries without assigning resistance capacity."""
import argparse
import json
from pathlib import Path


def options(geometry):
    rim = geometry['members']['base_side_left']
    if geometry['candidate'] != 'compact-floor-flush-development':
        raise ValueError('Require the preserved flush geometry')
    _, gy, gz = rim['grain']
    _, cy, cz = rim['centre_mm']
    depth, width = rim['depth_mm'], rim['width_mm']
    station = rim['end_stations_mm'][0]
    endpoints = [[cy + station*gy + q*gz, cz + station*gz - q*gy]
                 for q in (-depth/2, depth/2)]
    high, low = endpoints
    base = [high[0], low[1]]
    seat_end = low[0]
    return {
        'source_candidate': geometry['candidate'],
        'square_end_local_grain_station_mm': station,
        'square_end_yz_mm': endpoints,
        'separate_wedge_profile_yz_mm': [base, low, high],
        'wedge_width_x_mm': width,
        'wedge_run_y_mm': low[0]-high[0],
        'wedge_rise_z_mm': high[1]-low[1],
        'current_header_y_mm': [-175.7, -36.0],
        'wedge_header_end_margins_mm': [high[0]+175.7, -36.0-low[0]],
        'full_horizontal_end_y_mm': [seat_end-depth/gz, seat_end],
        'full_horizontal_end_length_mm': depth/gz,
        'header_width_shortfall_for_full_horizontal_end_mm': depth/gz-139.7,
        'restored_10mm_heel_projection_margin_mm': (seat_end+185.7)*gz-.75*depth-3.,
        'resistance_qualified': False,
        'scope': 'Geometry only. Square-end option requires a new fitted timber wedge, '
                 'positive thrust and uplift restraints, material checks and fresh assembly forces. '
                 'Historical projected-depth margin does not establish NDS method applicability.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry', type=Path, default=Path('docs/floor-flush-geometry.json'))
    args = parser.parse_args()
    print(json.dumps(options(json.loads(args.geometry.read_text())), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
