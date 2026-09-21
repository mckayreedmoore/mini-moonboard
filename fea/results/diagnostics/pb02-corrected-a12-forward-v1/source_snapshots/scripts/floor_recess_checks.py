"""Conservative continuous-band diagnostics and explicit recess-local gates.

Removing the shoulder load does not remove stress redistribution at the cut.
Net-section comparisons do not qualify notch-corner tension or splitting.
"""
import math

from fea.thick_leg_checks import bounded_section_check, bounded_section_properties
from scripts.compact_knee_results import cut_inventory, dot

CANDIDATE = 'compact-floor-recess-development'
LEGS = ('lumber_leg_left', 'lumber_leg_right')
NATIVE_BASIS = 'ACTUAL_HORIZONTAL_FOOT_RECESS_C3D20'
NOTCH_REINFORCEMENT_REFERENCE = 'https://www.rothoblaas.com/attachments/271031-product-271/ETA_11_0030_RB_screws_2025.pdf'


def continuous_band_sections(data, member, rows, hardware):
    """Ignore the removed side band at EVERY station, including above shoulder.

    Current signed native actions enter the existing conservative net-section
    comparison, which includes eccentricity to the retained centroid. This is
    a strength diagnostic only; it does not replace native stiffness or resolve
    local corner stresses. Bolt and other machining remain subtracted.
    """
    notches = [r for r in member['opening_records'] if r['kind'] == 'tab_notch']
    if len(notches) != 1:
        raise ValueError('Require one open side recess per leg')
    box = notches[0]['section_box_sxq_mm']
    if len(box) != 6 or not all(math.isfinite(v) for v in box):
        raise ValueError('Require finite three-dimensional recess bounds')
    width, depth = member['width_mm'], member['depth_mm']
    if not (math.isclose(width, 88.9, abs_tol=1.e-5)
            and math.isclose(box[3]-box[2], 38.1, abs_tol=1.e-5)
            and (math.isclose(box[2], -width/2, abs_tol=1.e-5)
                 or math.isclose(box[3], width/2, abs_tol=1.e-5))):
        raise ValueError('Require the actual 38.1 mm open-side cut in 88.9 mm stock')
    band_cut = [box[2], box[3], -depth/2, depth/2]
    base = bounded_section_properties(width, depth, [band_cut])
    cuts = cut_inventory(data['member']['name'], member, rows, hardware)
    result = []
    for section in data['sections']:
        station = dot([a-b for a, b in zip(section['origin_xyz_mm'], member['centre_mm'], strict=True)], member['grain'])
        active = [c for c in cuts if c['kind'] != 'tab_notch'
                  and c['box_sxq_mm'][0]-1.e-7 <= station <= c['box_sxq_mm'][1]+1.e-7]
        properties = bounded_section_properties(width, depth, [band_cut, *(c['box_sxq_mm'][2:] for c in active)])
        result.append({'station_mm_from_cad_centre': station,
            'actual_cut_box_properties': properties,
            'comparison': bounded_section_check(data, member, section, properties)})
    if not result:
        raise ValueError('Require signed native section actions')
    return {'remaining_width_mm': 50.8, 'unbored_band_properties': base,
        'sampled_sections': result,
        'peak_ratio': max(r['comparison']['conservative_net_section_envelope_ratio'] for r in result),
        'local_notch_resistance_qualified': False,
        'scope': 'All actions assigned to the continuous outer 50.8 mm band; no composite credit or local stress-concentration bound.'}


def checks(report, geometry, sections):
    """Additional recess gates; caller retains all existing numerical/joint gates."""
    if report.get('candidate') != CANDIDATE or geometry.get('candidate') != CANDIDATE:
        raise ValueError('Require matching isolated floor-recess candidate')
    rows = {n:r for n,r in report['physical_connection_forces'].items()
            if n.startswith(('lumber_leg_bolt_', 'rail_front_bolt_', 'rail_rear_bolt_'))}
    result = {}
    for name in LEGS:
        member = geometry['members'][name]
        data = report['member_section_demands'][name]
        native = data['member']
        band = continuous_band_sections(data, member, rows, geometry['hardware_by_name'])
        cuts = [c for c in sections[name]['cut_coverage'] if c['kind'] == 'tab_notch']
        bolts = [c for c in sections[name]['cut_coverage'] if c['kind'] == 'bolt_bore']
        bearings = [r for r in geometry['receiver_fit']
                    if r['member'] == name and r['bolt'].startswith('rail_rear_bolt_')]
        mesh_geometry = native.get('floor_recess_geometry', {})
        retained = mesh_geometry.get('retained_x_band_mm', ())
        cut_band = mesh_geometry.get('cut_inner_x_band_mm', ())
        openings = [r for r in member['opening_records'] if r['kind'] == 'tab_notch']
        volume = native.get('retained_mesh_volume_mm3', math.nan)
        expected_volume = mesh_geometry.get('expected_retained_volume_mm3', math.nan)
        native_pass = (native.get('native_section_geometry') == NATIVE_BASIS
            and math.isclose(mesh_geometry.get('notch_top_z_mm', math.nan), 141.7, abs_tol=1.e-5)
            and len(retained) == 2 and math.isclose(retained[1]-retained[0], 50.8, abs_tol=1.e-5)
            and len(cut_band) == 2 and math.isclose(cut_band[1]-cut_band[0], 38.1, abs_tol=1.e-5)
            and len(openings) == 1 and all(math.isclose(x-member['centre_mm'][0], q, abs_tol=1.e-5)
                for x,q in zip(cut_band, openings[0]['section_box_sxq_mm'][2:4], strict=True))
            and math.isfinite(volume) and volume > 0 and math.isclose(volume, expected_volume, abs_tol=.02, rel_tol=1.e-9)
            and math.isclose(mesh_geometry.get('expected_removed_volume_mm3', math.nan),
                openings[0].get('actual_removed_volume_mm3', math.nan), abs_tol=.02, rel_tol=1.e-9)
            and mesh_geometry.get('shoulder_bearing_credited') is False)
        recovery = native.get('additional_recovery_stations_mm', ())
        origin_shift = dot([a-b for a,b in zip(native.get('start', member['centre_mm']), member['centre_mm'], strict=True)], member['grain'])
        sampled = [r['station_mm_from_cad_centre'] for r in sections[name]['sampled_sections']]
        shoulders_sampled = (len(recovery) == 2 and all(math.isfinite(v) for v in recovery)
            and recovery[1] > recovery[0] and all(any(abs(v+origin_shift-t) < 1.e-5 for t in sampled) for v in recovery))
        result[name] = {'continuous_band': band, 'native_recess_record': native,
            'criteria': {
                'native_actual_recess': native_pass,
                'three_dimensional_recess_represented': sections[name]['all_openings_represented'] is True and len(cuts) == 1,
                'shoulder_bounds_sampled': shoulders_sampled,
                'all_bolt_centres_sampled': bool(bolts) and all(not c['unsampled_stations_mm'] for c in bolts),
                'actual_rear_receiver_band': len(bearings) == 2 and all(r['passes'] is True
                    and math.isclose(r['bearing_length_mm'], 50.8, abs_tol=1.e-5) for r in bearings),
                'continuous_band_nominal_resistance': band['peak_ratio'] <= 1,
                'local_notch_corner_resistance': False}}
    criteria = {key: all(r['criteria'][key] for r in result.values()) for key in result[LEGS[0]]['criteria']}
    return {'members': result, 'criteria': criteria, 'passes': all(criteria.values()),
        'qualified_for_design': False,
        'local_notch_disposition': 'No shoulder bearing credited. Continuous-band checks do not bound corner splitting/stress concentration. Reinforcement or an applicable local-notch assessment remains required.',
        'reinforcement_reference': {'url': NOTCH_REINFORCEMENT_REFERENCE, 'location': 'Annex F, page 79',
            'scope': 'Primary notched-support reinforcement method; applicability, actual screw anchorage and combined-action demands are not yet established for this side-face recess.'}}
