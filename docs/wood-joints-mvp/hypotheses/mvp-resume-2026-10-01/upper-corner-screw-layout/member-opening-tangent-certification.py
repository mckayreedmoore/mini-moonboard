# ruff: noqa: RUF007
# Retain frozen certification function bytes; source SHA records this lint-only header.
"""Pure saved-geometry certification of sub-tolerance tangent cut coordinates."""
import math


def certificates(recipe, member, surface, station, np, tolerance=1e-6):
    if recipe['regions'] is None:
        return []
    axes = [sorted({x for r in recipe['regions'] for x in r['bounds_uv_mm'][i]}) for i in (0, 1)]
    tiny = {(i, a, b) for i, v in enumerate(axes) for a, b in zip(v[:-1], v[1:])
            if (b-a)/2 < tolerance and a != v[0] and b != v[-1]}
    if not tiny:
        return []
    if station is None:
        raise ValueError('tangent certification needs its exact source station')
    geometry = member['geometry']
    frame = np.array([geometry[k] for k in ('axis', 'section_u', 'section_v')])
    features = {f['feature_id']: f for f in surface['features']}
    results = []
    for bore in recipe.get('saved_geometry', {}).get('bores', []):
        radius = bore['radius_mm']
        distance = abs(station-bore['station_mm'])
        discriminant = radius*radius-distance*distance
        halfwidth = math.sqrt(max(0., discriminant))
        if not 0 < halfwidth < tolerance or abs(distance-radius) >= tolerance:
            continue
        axis = bore['removed_interval_axis']-1
        expected = (bore['transverse_center_mm']-halfwidth, bore['transverse_center_mm']+halfwidth)
        for i, left, right in tiny:
            if i != axis or max(abs(left-expected[0]), abs(right-expected[1])) >= tolerance/100:
                continue
            results.append({'feature_id':bore['axis_id'], 'source':'recipe.saved_geometry.bores',
                            'station_mm':station, 'grain_center_mm':bore['station_mm'],
                            'radius_mm':radius, 'grain_distance_mm':distance,
                            'distance_minus_radius_mm':distance-radius,
                            'circle_discriminant_mm2':discriminant, 'source_chord_halfwidth_mm':halfwidth,
                            'section_axis':i, 'original_interval_mm':[left,right],
                            'idealized_coordinate_mm':(left+right)/2,
                            'maximum_coordinate_delta_mm':(right-left)/2,
                            'eligibility_rule':'Each edge displacement is below existing coordinate tolerance.',
                            'geometry_basis':recipe.get('geometry_basis'),
                            'scope':'Source-bound saved-geometry transverse cylinder tangent idealization for shear only.'})
    for interval in member['bore_or_passage_intervals']:
        if interval['id'].endswith('/owner_authorized_station_exclusion'):
            continue
        if not interval['lo']-tolerance <= station <= interval['hi']+tolerance:
            continue
        feature = features.get(interval['id'])
        if feature is None:
            continue  # Corrected bore recipes must authenticate through saved_geometry.
        if feature['surface_kind'] != 'CYLINDER':
            continue
        cylinder = feature['cylinder']
        origin = frame @ (np.array(cylinder['axis_origin_global_xyz_mm'])-geometry['start'])
        direction = frame @ np.array(cylinder['axis_unit_global_xyz'])
        shaft = int(np.argmax(abs(direction)))
        if shaft not in (1, 2) or abs(abs(direction[shaft])-1) >= 1e-7:
            continue
        if max(abs(np.delete(direction, shaft))) >= 1e-7:
            continue
        angular = feature['trim']['surface_parameter_bounds']['u']
        if cylinder['material_side_geometry'] != 'bore_like' or abs(angular[1]-angular[0]-2*math.pi) >= 1e-5:
            continue
        radius = cylinder['radius_mm']
        distance = abs(station-origin[0])
        discriminant = radius*radius-distance*distance
        halfwidth = math.sqrt(max(0., discriminant))
        if not 0 < halfwidth < tolerance or abs(distance-radius) >= tolerance:
            continue
        axis = 2-shaft
        expected = (origin[3-shaft]-halfwidth, origin[3-shaft]+halfwidth)
        for i, left, right in tiny:
            if i != axis or max(abs(left-expected[0]), abs(right-expected[1])) >= tolerance/100:
                continue
            results.append({'feature_id': interval['id'], 'station_mm': station,
                            'grain_center_mm': float(origin[0]), 'radius_mm': radius,
                            'grain_distance_mm': float(distance),
                            'distance_minus_radius_mm': float(distance-radius),
                            'circle_discriminant_mm2': float(discriminant),
                            'source_chord_halfwidth_mm': halfwidth,
                            'section_axis': i, 'original_interval_mm': [left, right],
                            'idealized_coordinate_mm': (left+right)/2,
                            'maximum_coordinate_delta_mm': (right-left)/2,
                            'eligibility_rule': 'Each chord edge moves less than the existing coordinate tolerance; the full interval may approach twice that tolerance.',
                            'geometry_basis': recipe.get('geometry_basis'),
                            'scope': 'Certified transverse-cylinder tangent-coordinate idealization for shear only; exact original normal regions are unchanged.'})
    certified = {(r['section_axis'], *r['original_interval_mm']) for r in results}
    if certified != tiny:
        raise ValueError('sub-tolerance internal interval lacks a transverse-cylinder tangency certificate: '+str(tiny-certified))
    return results


def apply(regions, certificates):
    mappings = [{}, {}]
    for certificate in certificates:
        axis = certificate['section_axis']
        for value in certificate['original_interval_mm']:
            adjusted = certificate['idealized_coordinate_mm']
            if value in mappings[axis] and mappings[axis][value] != adjusted:
                raise ValueError('overlapping tangent-coordinate certifications conflict')
            mappings[axis][value] = adjusted
    result = []
    for region in regions:
        bounds = [[mappings[i].get(x, x) for x in region['bounds_uv_mm'][i]] for i in (0, 1)]
        if all(b-a > 1e-12 for a, b in bounds):
            result.append({'bounds_uv_mm': bounds})
    if not result:
        raise ValueError('tangent-coordinate idealization removed the complete section')
    return result
